from sqlalchemy.orm import Session
from app.models.target import Target
from app.models.finding import Finding
from app.tasks.recon import start_recon_pipeline
from app.schemas import ScopeTargetCreate # Need to adapt schemas next
import json

def ensure_storage() -> None:
    pass # Managed by S3/MinIO in future or volume mounts now

def create_scope_target(db: Session, payload: dict) -> Target:
    target = Target(
        name=payload.get("program_name", "Unknown"),
        in_scope=json.dumps(payload.get("domains", [])),
        out_of_scope="[]"
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target

def run_recon(db: Session, target_id: int) -> str | None:
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        return None
    
    domains = json.loads(target.in_scope)
    job_id = start_recon_pipeline(target.id, domains)
    return job_id

def create_finding(db: Session, payload: dict) -> Finding:
    finding = Finding(
        target_id=payload["target_id"],
        title=payload["title"],
        vulnerability_class=payload.get("vulnerability_class", ""),
        severity=payload["severity"],
        description=payload["description"],
        evidence=json.dumps(payload.get("evidence", []))
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding

def get_learning_modules() -> dict:
    return {} # Placeholder for old functionality

def generate_report(db: Session, finding_id: int) -> dict | None:
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        return None
    return {"title": finding.title, "pdf_path": f"report_{finding.id}.pdf"}

def build_report_data(finding: Finding) -> dict:
    return {"title": finding.title}

def render_pdf_report(report_data: dict) -> bytes:
    return b"PDF CONTENT"