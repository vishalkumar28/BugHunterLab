"""
Recon Pipeline
================================
subfinder → naabu → httpx → normalize

Each stage is a Celery shared_task that can be chained, grouped, or run
independently.  All tasks publish real-time progress via Redis pub/sub
so the frontend can show live pipeline logs.
"""

import json
import logging
import subprocess
import os

# ── Ensure Go-installed tools are always in PATH ────────────────────────
# This is critical inside the worker container where Go binaries live
# under /root/go/bin but Celery's subprocess may not inherit the full PATH.
os.environ["PATH"] = "/root/go/bin:/usr/local/go/bin:" + os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")

from celery import shared_task, chain
from app.core.celery_app import celery_app
import redis

log = logging.getLogger(__name__)

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
    """Run a CLI tool safely, returning CompletedProcess.
    Logs stderr for debugging when a tool writes warnings/errors."""
    log.info(f"Running: {' '.join(cmd[:3])}... (timeout={timeout}s)")
    result = subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        log.warning(f"{cmd[0]} returned code {result.returncode}: {result.stderr[:500]}")
    elif result.stderr:
        log.debug(f"{cmd[0]} stderr: {result.stderr[:300]}")
    return result


# ── Stage 1: Subdomain Enumeration ─────────────────────────────────────

@shared_task(bind=True)
def run_subfinder(self, target_id: int, domain: str):
    """Run subfinder to passively discover subdomains."""
    _publish(target_id, {"tool": "subfinder", "status": "running", "target_id": target_id})
    try:
        result = _safe_run(["subfinder", "-d", domain, "-silent", "-all"], timeout=600)
        subdomains = list({line.strip() for line in result.stdout.splitlines() if line.strip()})
        _publish(target_id, {"tool": "subfinder", "status": "completed", "count": len(subdomains)})
        log.info(f"subfinder found {len(subdomains)} subdomains for {domain}")
        return {"domain": domain, "subdomains": subdomains}
    except FileNotFoundError:
        _publish(target_id, {"tool": "subfinder", "status": "skipped", "reason": "not installed"})
        log.error("subfinder binary not found in PATH")
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
        # Use -a for A record lookup and -json for structured output.
        # Do NOT combine -resp with -json — they produce conflicting formats.
        result = _safe_run(
            ["dnsx", "-silent", "-a", "-json"],
            input_data=input_data,
            timeout=300,
        )
        resolved = []
        resolved_hosts = set()
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                host = entry.get("host", "").strip()
                ips = entry.get("a", [])
                if host:
                    resolved_hosts.add(host)
                    resolved.append({"host": host, "ips": ips})
            except json.JSONDecodeError:
                # dnsx plain text fallback: "sub.domain.com [1.2.3.4]"
                # Extract just the hostname (first token before any space/bracket)
                host = line.split()[0].strip()
                if host and "." in host:
                    resolved_hosts.add(host)
                    resolved.append({"host": host, "ips": []})

        # Keep only resolved subdomains (valid DNS)
        valid_subs = [s for s in subdomains if s in resolved_hosts]

        # If dnsx resolved nothing (maybe it's not working), pass all subs through
        # so the pipeline doesn't die with empty data
        if not valid_subs and subdomains:
            log.warning(f"dnsx resolved 0 of {len(subdomains)} subs — passing all through as fallback")
            valid_subs = subdomains

        _publish(target_id, {
            "tool": "dnsx", "status": "completed",
            "resolved": len(resolved), "filtered_out": len(subdomains) - len(valid_subs),
        })
        log.info(f"dnsx: {len(resolved)} resolved, {len(valid_subs)} valid subs kept")
        return {"domain": domain, "subdomains": valid_subs, "resolved": resolved}

    except FileNotFoundError:
        _publish(target_id, {"tool": "dnsx", "status": "skipped", "reason": "not installed"})
        log.error("dnsx binary not found in PATH")
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
        import tempfile
        import os

        # Write subdomains to a temporary file to use with -list
        fd, temp_path = tempfile.mkstemp(prefix="naabu_targets_", text=True)
        with open(fd, 'w') as f:
            f.write("\n".join(subdomains))

        try:
            # Scan top 1000 ports with JSON output using -list
            result = _safe_run(
                ["naabu", "-silent", "-list", temp_path, "-top-ports", "1000", "-json"],
                timeout=3600,
            )
        finally:
            os.remove(temp_path)
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
        log.info(f"naabu: {len(ports_map)} hosts with {total_ports} total ports")
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": ports_map,
        }

    except FileNotFoundError:
        _publish(target_id, {"tool": "naabu", "status": "skipped", "reason": "not installed"})
        log.error("naabu binary not found in PATH")
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
        import tempfile
        import os
        
        fd, temp_path = tempfile.mkstemp(prefix="httpx_targets_", text=True)
        with open(fd, 'w') as f:
            f.write("\n".join(targets))
            
        try:
            result = _safe_run(
                ["httpx", "-silent", "-l", temp_path, "-status-code", "-title", "-tech-detect",
                 "-follow-redirects", "-json"],
                timeout=3600, # Increased timeout to 1 hour
            )
        finally:
            os.remove(temp_path)
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
        log.info(f"httpx: {len(live)} live hosts detected")
        return {
            "domain": domain, "subdomains": subdomains,
            "resolved": resolved, "ports": ports_map, "live": live,
        }

    except FileNotFoundError:
        _publish(target_id, {"tool": "httpx", "status": "skipped", "reason": "not installed"})
        log.error("httpx binary not found in PATH")
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
        log.info(f"katana: {len(endpoints)} endpoints crawled")
    except FileNotFoundError:
        _publish(target_id, {"tool": "katana", "status": "skipped", "reason": "not installed"})
        log.error("katana binary not found in PATH")
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
        log.info(f"gau: {gau_count} historical URLs found")
    except FileNotFoundError:
        _publish(target_id, {"tool": "gau", "status": "skipped", "reason": "not installed"})
        log.error("gau binary not found in PATH")
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
        log.info(f"nuclei: {len(findings)} vulnerabilities found")
        enriched_result["nuclei_findings"] = findings
        return enriched_result

    except FileNotFoundError:
        _publish(target_id, {"tool": "nuclei", "status": "skipped", "reason": "not installed"})
        log.error("nuclei binary not found in PATH")
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

        db.commit()
        log.info(f"normalize: persisted {stats} for target {target_id}")
        _publish(target_id, {
            "tool": "normalize", "status": "completed",
            "target_id": target_id, **stats,
        })
        return {"status": "success", **stats}
    except Exception as e:
        db.rollback()
        log.error(f"normalize error: {e}")
        _publish(target_id, {"tool": "normalize", "status": "error", "error": str(e)})
        return {"error": str(e)}
    finally:
        db.close()


# ── Pipeline Orchestrators ──────────────────────────────────────────────

def start_recon_pipeline(target_id: int, domains: list):
    """Build and dispatch the full recon chain for the primary domain.

    Pipeline: subfinder → naabu → httpx → normalize

    Verifies Celery broker connectivity first, then dispatches the chain.
    Raises an exception if Celery/Redis is unreachable — caller handles fallback.
    """
    if not domains:
        return None

    # ── Pre-flight: verify broker is reachable ──
    # This prevents silent failures where apply_async() returns a task ID
    # but no worker ever picks up the task.
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=5)
        conn.close()
    except Exception as e:
        raise ConnectionError(f"Cannot reach Celery broker: {e}") from e

    # ── Also verify at least one worker is alive ──
    try:
        inspector = celery_app.control.inspect(timeout=5)
        active = inspector.active_queues()
        if not active:
            raise ConnectionError("No Celery workers are online — is the worker container running?")
    except Exception as e:
        raise ConnectionError(f"Worker health check failed: {e}") from e

    domain = domains[0]  # Primary domain
    recon_chain = chain(
        run_subfinder.s(target_id, domain),
        run_naabu.s(target_id),
        run_httpx.s(target_id),
        normalize_assets_task.s(target_id),
    )
    result = recon_chain.apply_async()
    log.info(f"Pipeline dispatched: job={result.id} target={target_id} domain={domain}")
    return result.id


def _run_recon_sync(target_id: int, domains: list) -> str:
    """Synchronous in-process fallback recon when Celery is unavailable.
    Runs the full pipeline directly (blocking). Returns a fake job id."""
    import uuid
    job_id = f"sync-{uuid.uuid4().hex[:8]}"

    for domain in domains:
        # Step 1: subfinder
        sf_result = run_subfinder.run(target_id, domain)

        # Step 2: naabu
        naabu_result = run_naabu.run(sf_result, target_id)

        # Step 3: httpx
        httpx_result = run_httpx.run(naabu_result, target_id)

        # Step 4: normalize + persist to DB
        normalize_assets_task.run(httpx_result, target_id)

    return job_id
