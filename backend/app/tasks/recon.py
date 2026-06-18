import json
import subprocess
import os
from celery import shared_task, chain
from app.core.celery_app import celery_app
import redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


def _publish(target_id: int, msg: dict):
    try:
        redis_client.publish(f"target_{target_id}_updates", json.dumps(msg))
    except Exception:
        pass  # Redis optional — don't crash task


@shared_task(bind=True)
def run_subfinder(self, target_id: int, domain: str):
    """Run subfinder on domain, return list of discovered subdomains."""
    _publish(target_id, {"tool": "subfinder", "status": "running", "target_id": target_id})
    try:
        result = subprocess.run(
            ["subfinder", "-d", domain, "-silent"],
            capture_output=True, text=True, timeout=300, check=False
        )
        subdomains = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        _publish(target_id, {"tool": "subfinder", "status": "completed", "count": len(subdomains)})
        return {"domain": domain, "subdomains": subdomains}
    except FileNotFoundError:
        # subfinder not installed — return just the base domain
        _publish(target_id, {"tool": "subfinder", "status": "skipped", "reason": "not installed"})
        return {"domain": domain, "subdomains": [domain]}
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "subfinder", "status": "timeout"})
        return {"domain": domain, "subdomains": [domain]}


@shared_task(bind=True)
def run_httpx(self, subfinder_result: dict, target_id: int):
    """Probe discovered subdomains with httpx to find live hosts."""
    subdomains = subfinder_result.get("subdomains", [])
    _publish(target_id, {"tool": "httpx", "status": "running", "targets": len(subdomains)})
    live = []
    try:
        input_data = "\n".join(subdomains)
        result = subprocess.run(
            ["httpx", "-silent", "-status-code", "-title", "-tech-detect", "-json"],
            input=input_data, capture_output=True, text=True, timeout=300, check=False
        )
        for line in result.stdout.splitlines():
            try:
                entry = json.loads(line)
                live.append({
                    "url": entry.get("url", ""),
                    "status_code": entry.get("status_code", 0),
                    "title": entry.get("title", ""),
                    "technologies": entry.get("technologies", []),
                })
            except json.JSONDecodeError:
                if line.strip():
                    live.append({"url": line.strip(), "status_code": 200, "title": "", "technologies": []})
        _publish(target_id, {"tool": "httpx", "status": "completed", "live_hosts": len(live)})
        return {"subdomains": subdomains, "live": live}
    except FileNotFoundError:
        _publish(target_id, {"tool": "httpx", "status": "skipped", "reason": "not installed"})
        # Fallback: treat all subdomains as live
        live = [{"url": f"https://{s}", "status_code": 0, "title": "", "technologies": []} for s in subdomains]
        return {"subdomains": subdomains, "live": live}
    except subprocess.TimeoutExpired:
        _publish(target_id, {"tool": "httpx", "status": "timeout"})
        return {"subdomains": subdomains, "live": []}


@shared_task(bind=True)
def normalize_assets_task(self, httpx_result: dict, target_id: int):
    """Parse httpx output and persist assets + technologies into the database."""
    from app.database import SessionLocal
    from app.models.asset import Asset, AssetTechnology
    from app.models.target import Target

    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            return {"error": "Target not found"}

        live_hosts = httpx_result.get("live", [])
        subdomains = httpx_result.get("subdomains", [])
        assets_added = 0

        # Store subdomains that are not live
        for subdomain in subdomains:
            exists = db.query(Asset).filter(
                Asset.target_id == target_id, Asset.value == subdomain
            ).first()
            if not exists:
                asset = Asset(target_id=target_id, type="subdomain", value=subdomain, is_alive=False)
                db.add(asset)

        # Store live hosts with tech detection
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
                assets_added += 1

        db.commit()
        _publish(target_id, {
            "tool": "normalize", "status": "completed",
            "assets_added": assets_added, "target_id": target_id
        })
        return {"status": "success", "assets_added": assets_added, "live_hosts": len(live_hosts)}
    except Exception as e:
        db.rollback()
        _publish(target_id, {"tool": "normalize", "status": "error", "error": str(e)})
        return {"error": str(e)}
    finally:
        db.close()


def start_recon_pipeline(target_id: int, domains: list):
    """Builds and dispatches subfinder → httpx → normalize chain for each domain.
    Raises an exception if Celery/Redis is unreachable — caller handles fallback."""
    if not domains:
        return None

    domain = domains[0]  # Primary domain for now
    recon_chain = chain(
        run_subfinder.s(target_id, domain),
        run_httpx.s(target_id),
        normalize_assets_task.s(target_id),
    )
    result = recon_chain.apply_async()
    return result.id


def _run_recon_sync(target_id: int, domains: list) -> str:
    """Synchronous in-process fallback recon when Celery is unavailable.
    Runs subfinder → httpx → normalize directly (blocking). Returns a fake job id."""
    import uuid
    job_id = f"sync-{uuid.uuid4().hex[:8]}"

    for domain in domains:
        # Step 1: subfinder
        sf_result = run_subfinder.run(target_id, domain)   # .run() bypasses Celery

        # Step 2: httpx
        httpx_result = run_httpx.run(sf_result, target_id)

        # Step 3: normalize + persist to DB
        normalize_assets_task.run(httpx_result, target_id)

    return job_id
