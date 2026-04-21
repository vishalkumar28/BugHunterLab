from __future__ import annotations

import json
import re
import subprocess
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from .config import settings
from .intelligence import LANGUAGE_EXAMPLES, VULNERABILITY_DB
from .models import Finding, ReconRun, ScopeTarget
from .schemas import FindingCreate, ScopeTargetCreate

# Allowed characters in tool args — alphanumerics, dots, hyphens, slashes, colons
_SAFE_ARG_PATTERN = re.compile(r"^[\w.\-/:=@,]+$")


def ensure_storage() -> None:
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.database_url.replace("sqlite:///", "")).parent.mkdir(parents=True, exist_ok=True)


def score_target(domains: list[str], api_endpoints: list[str], scope_text: str) -> tuple[int, str, str]:
    score = min(
        100,
        len(domains) * 8
        + len(api_endpoints) * 6
        + (20 if "api" in scope_text.lower() else 0)
        + (15 if "auth" in scope_text.lower() or "login" in scope_text.lower() else 0)
        + (15 if len(scope_text.splitlines()) > 4 else 0),
    )
    if score < 35:
        level = "beginner-friendly"
    elif score < 70:
        level = "intermediate"
    else:
        level = "expert-level"
    summary = (
        f"Attack surface includes {len(domains)} domains and {len(api_endpoints)} known APIs. "
        f"The scope is classified as {level} with a quality score of {score}/100 based on breadth, "
        "API presence, and likely authenticated complexity."
    )
    return score, level, summary


def synthesize_recon(target: ScopeTarget) -> tuple[dict, dict, str]:
    domains = target.domains or []
    api_endpoints = target.api_endpoints or []
    subdomains = [f"app.{d}" for d in domains] + [f"api.{d}" for d in domains]
    live_hosts = [f"https://{host}" for host in domains + subdomains]
    assets = {
        "domains": domains,
        "subdomains": sorted(set(subdomains)),
        "live_hosts": live_hosts,
        "open_ports": [{"host": d, "ports": [80, 443, 8080]} for d in domains],
        "technologies": [
            {"host": domains[0], "frontend": "Next.js", "backend": "FastAPI", "database": "SQLite"}
        ]
        if domains
        else [],
        "hidden_endpoints": api_endpoints
        + ["/admin", "/dashboard", "/api/internal/health", "/graphql", "/.well-known/openid-configuration"],
    }
    attack_surface = {
        "nodes": [{"id": host, "type": "host"} for host in domains]
        + [{"id": ep, "type": "endpoint"} for ep in assets["hidden_endpoints"]],
        "edges": [
            {"source": domains[0], "target": ep, "label": "serves"}
            for ep in assets["hidden_endpoints"]
        ]
        if domains
        else [],
    }
    notes = (
        "Local recon synthesis completed. Tool wrappers can replace this synthesized result with "
        "real outputs from subfinder, amass, httpx, nuclei, nmap, ffuf, and sqlmap."
    )
    return assets, attack_surface, notes


def endpoint_checklist(endpoint: str) -> list[str]:
    lowered = endpoint.lower()
    checks = ["Test authentication bypass", "Test IDOR", "Test rate limiting"]
    if "update" in lowered or "admin" in lowered or "profile" in lowered:
        checks.extend(["Test CSRF", "Test mass assignment"])
    if "search" in lowered or "query" in lowered:
        checks.append("Test SQL injection")
    if "upload" in lowered:
        checks.append("Test file upload vulnerabilities")
    if "callback" in lowered or "url" in lowered or "webhook" in lowered:
        checks.append("Test SSRF")
    if "/api/" in lowered or lowered.startswith("/graphql"):
        checks.append("Test API authorization drift")
    checks.append("Test reflected and stored XSS")
    return checks


def create_scope_target(db: Session, payload: ScopeTargetCreate) -> ScopeTarget:
    score, level, summary = score_target(payload.domains, payload.api_endpoints, payload.scope_text)
    target = ScopeTarget(
        program_name=payload.program_name,
        program_url=payload.program_url,
        scope_text=payload.scope_text,
        domains=payload.domains,
        api_endpoints=payload.api_endpoints,
        target_score=score,
        target_level=level,
        summary=summary,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def run_recon(db: Session, target_id: int) -> ReconRun | None:
    target = db.get(ScopeTarget, target_id)
    if not target:
        return None
    assets, attack_surface, notes = synthesize_recon(target)
    recon = ReconRun(target_id=target_id, assets=assets, attack_surface=attack_surface, notes=notes)
    db.add(recon)
    db.commit()
    db.refresh(recon)
    return recon


def create_finding(db: Session, payload: FindingCreate) -> Finding:
    finding = Finding(
        target_id=payload.target_id,
        title=payload.title,
        vulnerability_class=payload.vulnerability_class,
        severity=payload.severity,
        endpoint=payload.endpoint,
        description=payload.description,
        evidence=payload.evidence,
        reproduction_steps=payload.reproduction_steps,
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def generate_poc(finding: Finding, poc_type: str) -> str:
    endpoint = finding.endpoint or "https://target.example/api/test"
    if poc_type == "python":
        return (
            "import requests\n\n"
            f"url = '{endpoint}'\n"
            "headers = {'Authorization': 'Bearer <token>'}\n"
            "payload = {'id': 'replace-me'}\n"
            "response = requests.get(url, headers=headers, params=payload, timeout=10)\n"
            "print(response.status_code)\nprint(response.text)\n"
        )
    if poc_type == "browser":
        return (
            "<script>\n"
            f"fetch('{endpoint}', {{ credentials: 'include' }})\n"
            "  .then(r => r.text())\n"
            "  .then(console.log);\n"
            "</script>\n"
        )
    return (
        f"curl -i '{endpoint}' \\\n"
        "  -H 'Authorization: Bearer <token>' \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  --data '{\"id\":\"replace-me\"}'\n"
    )


def build_report_data(finding: Finding) -> dict:
    vuln = VULNERABILITY_DB.get(finding.vulnerability_class, {})
    markdown = f"""# {finding.title}

## Summary
{finding.description}

## Impact
Severity: {finding.severity}

{vuln.get("impact", "Impact analysis pending.")}

## Steps to Reproduce
""" + "\n".join([f"{idx + 1}. {step}" for idx, step in enumerate(finding.reproduction_steps or ["Document the exact request and replay it."])]) + f"""

## Proof of Concept
```bash
{generate_poc(finding, "curl").strip()}
```

## Screenshots / Evidence
{json.dumps(finding.evidence, indent=2)}

## Remediation Advice
{vuln.get("description", "Harden authorization, input validation, and defensive monitoring.")}
"""
    plain_text = markdown.replace("# ", "").replace("## ", "")
    pdf_path = str(settings.evidence_dir / f"finding-{finding.id}-report.pdf")
    return {"title": finding.title, "markdown": markdown, "plain_text": plain_text, "pdf_path": pdf_path}


def generate_report(db: Session, finding_id: int) -> dict | None:
    finding = db.get(Finding, finding_id)
    if not finding:
        return None
    return build_report_data(finding)


def render_pdf_report(report_data: dict) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    text = pdf.beginText(40, 750)
    text.setLeading(16)
    for line in report_data["plain_text"].splitlines():
        if text.getY() < 50:
            pdf.drawText(text)
            pdf.showPage()
            text = pdf.beginText(40, 750)
            text.setLeading(16)
        text.textLine(line[:110])
    pdf.drawText(text)
    pdf.save()
    return buffer.getvalue()


def _sanitize_args(args: list[str]) -> list[str]:
    """Reject args with shell metacharacters to prevent injection."""
    sanitized = []
    for arg in args:
        if not _SAFE_ARG_PATTERN.match(arg):
            raise ValueError(f"Unsafe argument rejected: {arg!r}")
        sanitized.append(arg)
    return sanitized


def run_tool_wrapper(tool_name: str, args: list[str]) -> dict:
    script = settings.tools_dir / "run_tool.py"
    try:
        safe_args = _sanitize_args(args)
    except ValueError as exc:
        return {"tool": tool_name, "status": "error", "message": str(exc)}
    command = ["python", str(script), tool_name, *safe_args]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    except OSError as exc:
        return {"tool": tool_name, "status": "error", "message": str(exc)}
    return {
        "tool": tool_name,
        "status": "completed" if completed.returncode == 0 else "failed",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def get_learning_modules() -> dict:
    return {
        "phase_1": {
            "title": "Internet and Web Fundamentals",
            "topics": ["DNS resolution", "HTTP request structure", "Sessions and cookies", "TLS handshake", "Client/server architecture"],
            "visualizations": ["Request line", "Headers", "Response headers", "Cookies", "Authentication tokens"],
        },
        "phase_2": {
            "title": "Programming Knowledge for Security Testing",
            "languages": LANGUAGE_EXAMPLES,
        },
        "phase_3": {
            "title": "Application Architecture Mapping",
            "tools": ["Wappalyzer", "WhatWeb", "BuiltWith", "Custom fingerprinting"],
        },
        "phase_4": {
            "title": "HTTP Deep Inspection",
            "focus": ["Methods", "Headers", "Cookies", "CORS"],
            "highlight_issues": ["Missing security headers", "CORS misconfiguration", "Insecure cookies"],
        },
    }