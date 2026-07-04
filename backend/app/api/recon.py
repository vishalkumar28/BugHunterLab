import json
import logging
from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.target import Target
from app.models.asset import Asset, AssetTechnology, AssetPort
from app.models.finding import Finding

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{target_id}")
def run_recon(target_id: int):
    """Trigger a full recon pipeline (subfinder → dnsx → naabu → httpx → katana+gau → nuclei → normalize) for a target."""
    import re
    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        # Parse domains from in_scope field — handles JSON list OR plain text
        raw = target.in_scope or ""
        domains = []

        # Try JSON list first (["example.com", "api.example.com"])
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                domains = [str(d).strip() for d in parsed if str(d).strip()]
        except (json.JSONDecodeError, ValueError):
            pass

        # If not a valid JSON list, extract domain patterns from raw text
        if not domains:
            # Match *.example.com, example.com, sub.example.com patterns
            domain_pattern = re.compile(
                r'\*?\.?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}',
                re.IGNORECASE
            )
            found = domain_pattern.findall(raw)
            # findall returns list of tuples due to groups — extract full matches
            full_matches = re.findall(
                r'(\*?\.?[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,})',
                raw
            )
            # Filter out email-like matches, keep only domain-like strings
            domains = list({
                m.lower().lstrip("*.") for m in full_matches
                if "." in m and "@" not in m and len(m) < 100
            })

        if not domains:
            raise HTTPException(
                status_code=400,
                detail=f"No domains found in scope for target '{target.name}'. "
                       "Please edit this scope target and add domains (e.g. example.com) in the domains field."
            )

        # Try to dispatch to Celery worker; fall back to in-process if unavailable
        try:
            from app.tasks.recon import start_recon_pipeline
            job_id = start_recon_pipeline(target_id, domains)
            mode = "async"
        except Exception as celery_err:
            log.warning(f"Celery unavailable ({celery_err}), running recon in-process")
            try:
                from app.tasks.recon import _run_recon_sync
                job_id = _run_recon_sync(target_id, domains)
                mode = "sync"
            except Exception as sync_err:
                log.error(f"Sync recon also failed: {sync_err}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Recon pipeline unavailable. Celery error: {celery_err}. Sync error: {sync_err}. Is the worker container running?"
                )

        return {
            "job_id": str(job_id),
            "target_id": target_id,
            "domains": domains,
            "status": "started",
            "mode": mode,
            "pipeline": "subfinder → dnsx → naabu → httpx → katana+gau → nuclei → normalize",
            "message": f"Enterprise recon pipeline started ({mode}) for {len(domains)} domain(s).",
        }
    finally:
        db.close()


@router.get("/{target_id}")
def get_recon_results(target_id: int):
    """Return all discovered assets (subdomains, live hosts, ports, endpoints, technologies, findings) for a target."""
    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        assets = db.query(Asset).filter(Asset.target_id == target_id).all()
        findings = db.query(Finding).filter(Finding.target_id == target_id).all()

        subdomains = []
        live_hosts = []
        endpoints = []
        technologies_seen = set()
        ports_data = []

        for a in assets:
            if a.type == "subdomain":
                subdomains.append(a.value)
                # Include port data for subdomains
                for p in a.ports:
                    ports_data.append({
                        "host": a.value,
                        "port": p.port,
                        "protocol": p.protocol,
                        "service": p.service,
                    })
            elif a.type == "url":
                techs = [
                    {"name": t.tech_name, "version": t.version, "category": t.category}
                    for t in a.technologies
                ]
                for t in a.technologies:
                    if t.tech_name:
                        technologies_seen.add(t.tech_name)
                live_hosts.append({
                    "id": a.id,
                    "url": a.value,
                    "is_alive": a.is_alive,
                    "technologies": techs,
                    "discovered_at": a.created_at.isoformat() if a.created_at else "",
                })
            elif a.type == "endpoint":
                endpoints.append(a.value)

        # Serialize findings from nuclei
        findings_data = [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "vulnerability_class": f.vulnerability_class,
                "description": f.description,
                "evidence": f.evidence,
                "created_at": f.created_at.isoformat() if f.created_at else "",
            }
            for f in findings
        ]

        # Build attack surface graph nodes and edges
        nodes = [{"id": f"asset_{a.id}", "label": a.value, "type": a.type} for a in assets]
        edges = [{"from": f"target_{target_id}", "to": f"asset_{a.id}"} for a in assets]

        return {
            "target_id": target_id,
            "target_name": target.name,
            "status": "completed" if assets else "pending",
            "assets": {
                "subdomains": subdomains,
                "live_hosts": live_hosts,
                "technologies": sorted(list(technologies_seen)),
                "ports": ports_data,
                "endpoints": endpoints,
            },
            "findings": findings_data,
            "attack_surface": {"nodes": nodes, "edges": edges},
            "total_assets": len(assets),
        }
    finally:
        db.close()


@router.delete("/{target_id}/assets")
def clear_recon_results(target_id: int):
    """Clear all discovered assets and findings for a target (allows fresh rescan)."""
    db = SessionLocal()
    try:
        deleted_assets = db.query(Asset).filter(Asset.target_id == target_id).delete()
        deleted_findings = db.query(Finding).filter(Finding.target_id == target_id).delete()
        db.commit()
        return {"deleted_assets": deleted_assets, "deleted_findings": deleted_findings, "target_id": target_id}
    finally:
        db.close()
