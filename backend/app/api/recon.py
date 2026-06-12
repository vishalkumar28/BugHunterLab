from fastapi import APIRouter
from app.database import SessionLocal
from app.models.target import Target
from app.models.asset import Asset
from datetime import datetime, timezone

router = APIRouter()


@router.post("/{target_id}")
def run_recon(target_id: int):
    """Trigger a recon pass (mock response — real tools run via jobs API)."""
    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Target not found")
        return {
            "id": 1,
            "target_id": target_id,
            "status": "completed",
            "assets": {
                "domains": [target.in_scope.split()[0]] if target.in_scope else [],
                "subdomains": [],
                "live_hosts": [],
                "open_ports": [],
                "technologies": [],
                "hidden_endpoints": [],
            },
            "attack_surface": {"nodes": [], "edges": []},
            "notes": "Run subfinder and httpx via the Auto Scanner for real recon results.",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


@router.get("/{target_id}")
def get_recon_runs(target_id: int):
    """Return past recon runs for a target."""
    return []
