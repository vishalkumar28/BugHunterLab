from fastapi import APIRouter
from app.database import SessionLocal
from app.models.finding import Finding
from app.models.target import Target
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


@router.get("")
def list_findings():
    db = SessionLocal()
    try:
        findings = db.query(Finding).order_by(Finding.created_at.desc()).all()
        return [
            {
                "id": f.id,
                "target_id": f.target_id,
                "title": f.title,
                "vulnerability_class": getattr(f, "vulnerability_class", None) or "Unknown",
                "severity": f.severity,
                "status": "open",
                "endpoint": "",
                "description": f.description,
                "evidence": [],
                "reproduction_steps": [],
                "created_at": f.created_at.isoformat() if f.created_at else "",
            }
            for f in findings
        ]
    finally:
        db.close()


@router.post("")
def create_finding(body: FindingCreate):
    db = SessionLocal()
    try:
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
        return {
            "id": finding.id,
            "target_id": finding.target_id,
            "title": finding.title,
            "vulnerability_class": finding.vulnerability_class or "Unknown",
            "severity": finding.severity,
            "status": "open",
            "endpoint": body.endpoint or "",
            "description": finding.description,
            "evidence": [],
            "reproduction_steps": [],
            "created_at": finding.created_at.isoformat() if finding.created_at else "",
        }
    finally:
        db.close()
