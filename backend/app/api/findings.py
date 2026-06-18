from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.finding import Finding
from app.models.target import Target
from app.services.storage import list_evidence
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class FindingCreate(BaseModel):
    target_id: int
    title: str
    vulnerability_class: Optional[str] = None
    severity: str  # low, medium, high, critical
    description: str
    endpoint: Optional[str] = None
    evidence: Optional[str] = None
    reproduction_steps: Optional[str] = None


class FindingUpdate(BaseModel):
    title: Optional[str] = None
    vulnerability_class: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    evidence: Optional[str] = None
    reproduction_steps: Optional[str] = None


def _serialize(f: Finding) -> dict:
    return {
        "id": f.id,
        "target_id": f.target_id,
        "title": f.title,
        "vulnerability_class": getattr(f, "vulnerability_class", None) or "Unknown",
        "severity": f.severity,
        "status": "open",
        "endpoint": getattr(f, "endpoint", "") or "",
        "description": f.description,
        "evidence": f.evidence or "",
        "evidence_files": list_evidence(f.id),
        "reproduction_steps": getattr(f, "reproduction_steps", "") or "",
        "oob_validated": getattr(f, "oob_validated", False),
        "created_at": f.created_at.isoformat() if f.created_at else "",
    }


@router.get("")
def list_findings(target_id: Optional[int] = None):
    """List all findings, optionally filtered by target."""
    db = SessionLocal()
    try:
        q = db.query(Finding).order_by(Finding.created_at.desc())
        if target_id:
            q = q.filter(Finding.target_id == target_id)
        return [_serialize(f) for f in q.all()]
    finally:
        db.close()


@router.post("")
def create_finding(body: FindingCreate):
    """Create a new finding."""
    db = SessionLocal()
    try:
        # Validate target exists
        target = db.query(Target).filter(Target.id == body.target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail=f"Target {body.target_id} not found")

        finding = Finding(
            target_id=body.target_id,
            title=body.title,
            vulnerability_class=body.vulnerability_class,
            severity=body.severity,
            description=body.description,
            evidence=body.evidence,
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)
        return _serialize(finding)
    finally:
        db.close()


@router.get("/{finding_id}")
def get_finding(finding_id: int):
    """Get a single finding by ID."""
    db = SessionLocal()
    try:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return _serialize(finding)
    finally:
        db.close()


@router.put("/{finding_id}")
def update_finding(finding_id: int, body: FindingUpdate):
    """Update an existing finding."""
    db = SessionLocal()
    try:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(finding, field, value)
        db.commit()
        db.refresh(finding)
        return _serialize(finding)
    finally:
        db.close()


@router.delete("/{finding_id}")
def delete_finding(finding_id: int):
    """Delete a finding and its evidence files."""
    db = SessionLocal()
    try:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        db.delete(finding)
        db.commit()
        return {"status": "deleted", "id": finding_id}
    finally:
        db.close()
