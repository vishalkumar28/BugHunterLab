from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Finding
from ..schemas import FindingCreate, FindingRead, PocRequest
from ..services import create_finding, generate_poc

router = APIRouter(prefix="/api", tags=["findings"])


@router.post("/findings", response_model=FindingRead)
def add_finding(payload: FindingCreate, db: Session = Depends(get_db)):
    return create_finding(db, payload)


@router.get("/findings", response_model=list[FindingRead])
def list_findings(db: Session = Depends(get_db)):
    return db.query(Finding).order_by(Finding.created_at.desc()).all()


@router.post("/poc")
def poc(payload: PocRequest, db: Session = Depends(get_db)):
    finding = db.get(Finding, payload.finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {
        "finding_id": finding.id,
        "poc_type": payload.poc_type,
        "content": generate_poc(finding, payload.poc_type),
    }
