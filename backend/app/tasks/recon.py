"""
Enterprise-Grade Recon Pipeline
================================
subfinder → dnsx → naabu → httpx → katana → gau → nuclei → normalize

Each stage is a Celery shared_task that can be chained, grouped, or run
independently.  All tasks publish real-time progress via Redis pub/sub
so the frontend can show live pipeline logs.
"""

import json
import subprocess
import os

os.environ["PATH"] += os.pathsep + "/root/go/bin:/usr/local/go/bin"

from celery import shared_task, chain
from app.core.celery_app import celery_app
import redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "/app/evidence")


# ── Helpers ─────────────────────────────────────────────────────────────

def _publish(target_id: int, msg: dict):
    """Push real-time update to the frontend via Redis pub/sub."""
    try:
        redis_client.publish(f"target_{target_id}_updates", json.dumps(msg))
    except Exception:
        pass  # Redis optional — don't crash task


def _safe_run(cmd: list, input_data: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a CLI tool safely, returning CompletedProcess."""
    return subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


# ── Stage 1: Subdomain Enumeration ─────────────────────────────────────

@shared_task(bind=True)
def run_subfinder(self, target_id: int, domain: str):
    """Run subfinder to passively discover subdomains."""
    _publish(target_id, {"tool": "subfinder", "status": "running", "target_id": target_id})
    try:
        result = _safe_run(["subfinder", "-d", domain, "-silent", "-all"], timeout=600)
        subdomains = list({line.strip() for line in result.stdout.splitlines() if line.strip()})
        _publish(target_id, {"tool": "subfinder", "status": "completed", "count": len(subdomains)})
        return {"domain": domain, "subdomains": subdomains}
    except FileNotFoundError:
        _publish(target_id, {"tool": "subfinder", "status": "skipped", "reason": "not installed"})
        return {"domain": domain, "subdomains": [domain]}
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "subfinder", "status": "timeout"})
        return {"domain": domain, "subdomains": [domain]}


# ── Stage 2: DNS Resolution ────────────────────────────────────────────

@shared_task(bind=True)
def run_dnsx(self, subfinder_result: dict, target_id: int):
    """Resolve subdomains via dnsx — filters out dead/parked DNS entries."""
    subdomains = subfinder_result.get("subdomains", [])
    domain = subfinder_result.get("domain", "")
    _publish(target_id, {"tool": "dnsx", "status": "running", "targets": len(subdomains)})

    if not subdomains:
        return {"domain": domain, "subdomains": [], "resolved": []}

    try:
        input_data = "\n".join(subdomains)
        result = _safe_run(
            ["dnsx", "-silent", "-a", "-json"],
            input_data=input_data,
            timeout=300,
        )
        resolved = []
        resolved_hosts = set()
        for line in result.stdout.splitlines():
            try:
                entry = json.loads(line)
                host = entry.get("host", "").strip()
                ips = entry.get("a", [])
                if host:
                    resolved_hosts.add(host)
                    resolved.append({"host": host, "ips": ips})
            except json.JSONDecodeError:
                line_str = line.strip()
                if not line_str: continue
                # if dnsx outputs standard text format e.g. "sub.domain.com [1.2.3.4]"
                host = line_str.split()[0]
                if host:
                    resolved_hosts.add(host)
                    resolved.append({"host": host, "ips": []})

        # Keep only resolved subdomains (valid DNS)
        valid_subs = [s for s in subdomains if s in resolved_hosts]
        _publish(target_id, {
            "tool": "dnsx", "status": "completed",
            "resolved": len(resolved), "filtered_out": len(subdomains) - len(valid_subs),
        })
        return {"domain": domain, "subdomains": valid_subs, "resolved": resolved}

    except FileNotFoundError:
        _publish(target_id, {"tool": "dnsx", "status": "skipped", "reason": "not installed"})
        return {"domain": domain, "subdomains": subdomains, "resolved": []}
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "dnsx", "status": "timeout"})
        return {"domain": domain, "subdomains": subdomains, "resolved": []}


# ── Stage 3: Port Scanning ─────────────────────────────────────────────

@shared_task(bind=True)
def run_naabu(self, dnsx_result: dict, target_id: int):
    """Fast port scan with naabu on resolved subdomains."""
    subdomains = dnsx_result.get("subdomains", [])
    domain = dnsx_result.get("domain", "")
    resolved = dnsx_result.get("resolved", [])
    _publish(target_id, {"tool": "naabu", "status": "running", "targets": len(subdomains)})

    if not subdomains:
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": {},
        }

    try:
        input_data = "\n".join(subdomains)
        # Scan top 1000 ports with JSON output
        result = _safe_run(
            ["naabu", "-silent", "-top-ports", "1000", "-json"],
            input_data=input_data,
            timeout=600,
        )
        ports_map = {}  # host -> [port, port, ...]
        for line in result.stdout.splitlines():
            try:
                entry = json.loads(line)
                host = entry.get("host", "").strip()
                port = entry.get("port", 0)
                if host and port:
                    ports_map.setdefault(host, []).append(port)
            except json.JSONDecodeError:
                # naabu plain output: host:port
                if ":" in line:
                    parts = line.strip().rsplit(":", 1)
                    host = parts[0]
                    try:
                        port = int(parts[1])
                        ports_map.setdefault(host, []).append(port)
                    except ValueError:
                        pass

        total_ports = sum(len(v) for v in ports_map.values())
        _publish(target_id, {
            "tool": "naabu", "status": "completed",
            "hosts_with_ports": len(ports_map), "total_ports": total_ports,
        })
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": ports_map,
        }

    except FileNotFoundError:
        _publish(target_id, {"tool": "naabu", "status": "skipped", "reason": "not installed"})
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": {},
        }
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "naabu", "status": "timeout"})
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": {},
        }


# ── Stage 4: HTTP Probing + Tech Detection ─────────────────────────────

@shared_task(bind=True)
def run_httpx(self, naabu_result: dict, target_id: int):
    """Probe subdomains with httpx including tech detection and status codes.
    
    If naabu found specific ports, we construct host:port pairs so httpx
    checks the exact ports instead of just 80/443.
    """
    subdomains = naabu_result.get("subdomains", [])
    ports_map = naabu_result.get("ports", {})
    domain = naabu_result.get("domain", "")
    resolved = naabu_result.get("resolved", [])

    # Build input: if we have port data, include host:port combos
    targets = set()
    for sub in subdomains:
        if sub in ports_map:
            for port in ports_map[sub]:
                targets.add(f"{sub}:{port}")
        else:
            targets.add(sub)

    _publish(target_id, {"tool": "httpx", "status": "running", "targets": len(targets)})
    live = []
    try:
        input_data = "\n".join(targets)
        result = _safe_run(
            ["httpx", "-silent", "-status-code", "-title", "-tech-detect",
             "-follow-redirects", "-json"],
            input_data=input_data,
            timeout=600,
        )
        for line in result.stdout.splitlines():
            try:
                entry = json.loads(line)
                live.append({
                    "url": entry.get("url", ""),
                    "status_code": entry.get("status_code", 0),
                    "title": entry.get("title", ""),
                    "technologies": entry.get("technologies", []),
                    "content_length": entry.get("content_length", 0),
                    "webserver": entry.get("webserver", ""),
                })
            except json.JSONDecodeError:
                if line.strip():
                    live.append({
                        "url": line.strip(), "status_code": 200,
                        "title": "", "technologies": [],
                        "content_length": 0, "webserver": "",
                    })
        _publish(target_id, {"tool": "httpx", "status": "completed", "live_hosts": len(live)})
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": ports_map, "live": live,
        }

    except FileNotFoundError:
        _publish(target_id, {"tool": "httpx", "status": "skipped", "reason": "not installed"})
        live = [{"url": f"https://{s}", "status_code": 0, "title": "",
                 "technologies": [], "content_length": 0, "webserver": ""} for s in subdomains]
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": ports_map, "live": live,
        }
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "httpx", "status": "timeout"})
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": ports_map, "live": [],
        }


# ── Stage 5: Endpoint Discovery (Katana + GAU) ─────────────────────────

@shared_task(bind=True)
def run_endpoint_discovery(self, httpx_result: dict, target_id: int):
    """Crawl live hosts with katana and enrich with historical URLs via gau."""
    live = httpx_result.get("live", [])
    domain = httpx_result.get("domain", "")
    endpoints = set()

    # ── katana: active crawling ──
    _publish(target_id, {"tool": "katana", "status": "running", "targets": len(live)})
    try:
        urls_input = "\n".join(h["url"] for h in live if h.get("url"))
        if urls_input:
            result = _safe_run(
                ["katana", "-silent", "-depth", "3", "-js-crawl",
                 "-known-files", "all", "-form-extraction"],
                input_data=urls_input,
                timeout=600,
            )
            for line in result.stdout.splitlines():
                ep = line.strip()
                if ep:
                    endpoints.add(ep)
        _publish(target_id, {"tool": "katana", "status": "completed", "endpoints": len(endpoints)})
    except FileNotFoundError:
        _publish(target_id, {"tool": "katana", "status": "skipped", "reason": "not installed"})
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "katana", "status": "timeout"})

    # ── gau: historical URL discovery ──
    _publish(target_id, {"tool": "gau", "status": "running"})
    gau_count = 0
    try:
        result = _safe_run(
            ["gau", "--threads", "5", "--subs", domain],
            timeout=300,
        )
        for line in result.stdout.splitlines():
            ep = line.strip()
            if ep:
                endpoints.add(ep)
                gau_count += 1
        _publish(target_id, {"tool": "gau", "status": "completed", "historical_urls": gau_count})
    except FileNotFoundError:
        _publish(target_id, {"tool": "gau", "status": "skipped", "reason": "not installed"})
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "gau", "status": "timeout"})

    # Merge endpoint list back into the result
    httpx_result["endpoints"] = list(endpoints)
    _publish(target_id, {
        "tool": "endpoint_discovery", "status": "completed",
        "total_endpoints": len(endpoints),
    })
    return httpx_result


# ── Stage 6: Vulnerability Scanning (Nuclei) ───────────────────────────

@shared_task(bind=True)
def run_nuclei(self, enriched_result: dict, target_id: int):
    """Run nuclei against all live hosts to find CVEs and misconfigurations."""
    live = enriched_result.get("live", [])
    _publish(target_id, {"tool": "nuclei", "status": "running", "targets": len(live)})

    findings = []
    try:
        urls_input = "\n".join(h["url"] for h in live if h.get("url"))
        if not urls_input:
            _publish(target_id, {"tool": "nuclei", "status": "completed", "findings": 0})
            enriched_result["nuclei_findings"] = []
            return enriched_result

        result = _safe_run(
            ["nuclei", "-silent", "-json",
             "-severity", "low,medium,high,critical",
             "-rate-limit", "100",
             "-bulk-size", "50",
             "-concurrency", "25"],
            input_data=urls_input,
            timeout=1800,  # 30 minutes max for nuclei
        )
        for line in result.stdout.splitlines():
            try:
                entry = json.loads(line)
                findings.append({
                    "template_id": entry.get("template-id", ""),
                    "name": entry.get("info", {}).get("name", ""),
                    "severity": entry.get("info", {}).get("severity", "info"),
                    "description": entry.get("info", {}).get("description", ""),
                    "matched_url": entry.get("matched-at", entry.get("host", "")),
                    "matcher_name": entry.get("matcher-name", ""),
                    "extracted_results": entry.get("extracted-results", []),
                    "curl_command": entry.get("curl-command", ""),
                    "tags": entry.get("info", {}).get("tags", []),
                    "reference": entry.get("info", {}).get("reference", []),
                })
            except json.JSONDecodeError:
                pass

        _publish(target_id, {"tool": "nuclei", "status": "completed", "findings": len(findings)})
        enriched_result["nuclei_findings"] = findings
        return enriched_result

    except FileNotFoundError:
        _publish(target_id, {"tool": "nuclei", "status": "skipped", "reason": "not installed"})
        enriched_result["nuclei_findings"] = []
        return enriched_result
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "nuclei", "status": "timeout"})
        enriched_result["nuclei_findings"] = findings
        return enriched_result


# ── Stage 7: Normalize + Persist Everything to DB ───────────────────────

@shared_task(bind=True)
def normalize_assets_task(self, pipeline_result: dict, target_id: int):
    """Parse the full pipeline output and persist assets, ports, technologies,
    endpoints, and nuclei findings into the database."""
    from app.database import SessionLocal
    from app.models.asset import Asset, AssetTechnology, AssetPort
    from app.models.target import Target
    from app.models.finding import Finding

    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            return {"error": "Target not found"}

        live_hosts = pipeline_result.get("live", [])
        subdomains = pipeline_result.get("subdomains", [])
        ports_map = pipeline_result.get("ports", {})
        endpoints = pipeline_result.get("endpoints", [])
        nuclei_findings = pipeline_result.get("nuclei_findings", [])
        resolved = pipeline_result.get("resolved", [])

        stats = {"subdomains": 0, "live_hosts": 0, "ports": 0, "endpoints": 0, "findings": 0}

        # ── Persist subdomains ──
        for subdomain in subdomains:
            exists = db.query(Asset).filter(
                Asset.target_id == target_id, Asset.value == subdomain
            ).first()
            if not exists:
                # Lookup resolved IPs for this subdomain
                asset = Asset(target_id=target_id, type="subdomain", value=subdomain, is_alive=False)
                db.add(asset)
                db.flush()

                # Attach discovered ports from naabu
                if subdomain in ports_map:
                    for port in ports_map[subdomain]:
                        port_entry = AssetPort(asset_id=asset.id, port=port, protocol="tcp")
                        db.add(port_entry)
                        stats["ports"] += 1

                stats["subdomains"] += 1

        # ── Persist live hosts with technologies ──
        for host in live_hosts:
            url = host.get("url", "")
            if not url:
                continue
            exists = db.query(Asset).filter(
                Asset.target_id == target_id, Asset.value == url
            ).first()
            if not exists:
                asset = Asset(target_id=target_id, type="url", value=url, is_alive=True)
                db.add(asset)
                db.flush()
                for tech in host.get("technologies", []):
                    if isinstance(tech, str) and tech:
                        tech_entry = AssetTechnology(
                            asset_id=asset.id,
                            tech_name=tech,
                        )
                        db.add(tech_entry)
                # Also store webserver as a technology if detected
                webserver = host.get("webserver", "")
                if webserver:
                    tech_entry = AssetTechnology(
                        asset_id=asset.id,
                        tech_name=webserver,
                        category="Web Server",
                    )
                    db.add(tech_entry)
                stats["live_hosts"] += 1

        # ── Persist discovered endpoints from katana/gau ──
        for ep in endpoints:
            if not ep:
                continue
            exists = db.query(Asset).filter(
                Asset.target_id == target_id, Asset.value == ep
            ).first()
            if not exists:
                asset = Asset(target_id=target_id, type="endpoint", value=ep, is_alive=True)
                db.add(asset)
                stats["endpoints"] += 1

        # ── Persist nuclei findings ──
        for finding in nuclei_findings:
            title = finding.get("name") or finding.get("template_id", "Unknown")
            severity = finding.get("severity", "info").lower()
            if severity not in ("low", "medium", "high", "critical"):
                severity = "low"

            # Avoid duplicate findings for same template + URL
            existing = db.query(Finding).filter(
                Finding.target_id == target_id,
                Finding.title == title,
                Finding.vulnerability_class == finding.get("template_id", ""),
            ).first()
            if not existing:
                desc_parts = [finding.get("description", "")]
                if finding.get("matched_url"):
                    desc_parts.append(f"Matched URL: {finding['matched_url']}")
                if finding.get("reference"):
                    refs = finding["reference"]
                    if isinstance(refs, list):
                        desc_parts.append("References: " + ", ".join(refs))
                if finding.get("tags"):
                    tags = finding["tags"]
                    if isinstance(tags, list):
                        desc_parts.append("Tags: " + ", ".join(tags))

                evidence_parts = []
                if finding.get("curl_command"):
                    evidence_parts.append(f"curl command:\n{finding['curl_command']}")
                if finding.get("extracted_results"):
                    evidence_parts.append(f"Extracted: {json.dumps(finding['extracted_results'])}")

                f = Finding(
                    target_id=target_id,
                    title=title,
                    severity=severity,
                    vulnerability_class=finding.get("template_id", ""),
                    description="\n\n".join(desc_parts),
                    evidence="\n\n".join(evidence_parts) if evidence_parts else None,
                )
                db.add(f)
                stats["findings"] += 1

        db.commit()
        _publish(target_id, {
            "tool": "normalize", "status": "completed",
            "target_id": target_id, **stats,
        })
        return {"status": "success", **stats}
    except Exception as e:
        db.rollback()
        _publish(target_id, {"tool": "normalize", "status": "error", "error": str(e)})
        return {"error": str(e)}
    finally:
        db.close()


# ── Pipeline Orchestrators ──────────────────────────────────────────────

def start_recon_pipeline(target_id: int, domains: list):
    """Build and dispatch the full enterprise recon chain for the primary domain.

    Pipeline: subfinder → dnsx → naabu → httpx → katana+gau → nuclei → normalize

    Raises an exception if Celery/Redis is unreachable — caller handles fallback.
    """
    if not domains:
        return None

    domain = domains[0]  # Primary domain
    recon_chain = chain(
        run_subfinder.s(target_id, domain),
        run_dnsx.s(target_id),
        run_naabu.s(target_id),
        run_httpx.s(target_id),
        run_endpoint_discovery.s(target_id),
        run_nuclei.s(target_id),
        normalize_assets_task.s(target_id),
    )
    result = recon_chain.apply_async()
    return result.id


def _run_recon_sync(target_id: int, domains: list) -> str:
    """Synchronous in-process fallback recon when Celery is unavailable.
    Runs the full pipeline directly (blocking). Returns a fake job id."""
    import uuid
    job_id = f"sync-{uuid.uuid4().hex[:8]}"

    for domain in domains:
        # Step 1: subfinder
        sf_result = run_subfinder.run(target_id, domain)

        # Step 2: dnsx
        dnsx_result = run_dnsx.run(sf_result, target_id)

        # Step 3: naabu
        naabu_result = run_naabu.run(dnsx_result, target_id)

        # Step 4: httpx
        httpx_result = run_httpx.run(naabu_result, target_id)

        # Step 5: endpoint discovery (katana + gau)
        enriched_result = run_endpoint_discovery.run(httpx_result, target_id)

        # Step 6: nuclei
        nuclei_result = run_nuclei.run(enriched_result, target_id)

        # Step 7: normalize + persist to DB
        normalize_assets_task.run(nuclei_result, target_id)

    return job_id
