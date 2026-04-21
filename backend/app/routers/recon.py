from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ScopeTarget
from ..schemas import ChecklistItem, ReconRunRead
from ..services import endpoint_checklist, run_recon

router = APIRouter(prefix="/api", tags=["recon"])


@router.post("/recon/{target_id}", response_model=ReconRunRead)
def execute_recon(target_id: int, db: Session = Depends(get_db)):
    recon = run_recon(db, target_id)
    if not recon:
        raise HTTPException(status_code=404, detail="Target not found")
    return recon


@router.get("/recon/{target_id}", response_model=list[ReconRunRead])
def list_recon_runs(target_id: int, db: Session = Depends(get_db)):
    target = db.get(ScopeTarget, target_id)
    return target.recon_runs if target else []


@router.get("/checklists")
def checklists(target_id: int, db: Session = Depends(get_db)):
    target = db.get(ScopeTarget, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    endpoints = target.api_endpoints or ["/api/users/update", "/api/admin/users", "/upload"]
    return [
        ChecklistItem(
            endpoint=ep,
            method="GET" if "api" in ep else "POST",
            checklist=endpoint_checklist(ep),
        )
        for ep in endpoints
    ]
