from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.target import Target
from app.models.finding import Finding

router = APIRouter()

@router.get("")
def get_dashboard_data():
    db = SessionLocal()
    try:
        # We order by created_at desc
        recent_targets_db = db.query(Target).order_by(Target.created_at.desc()).limit(5).all()
        recent_findings_db = db.query(Finding).order_by(Finding.created_at.desc()).limit(5).all()
        
        phases = [
            {"id": 1, "name": "Fundamentals", "description": "Understand web layers and attack surfaces."},
            {"id": 2, "name": "Programming Knowledge", "description": "Study vuln patterns in code."},
            {"id": 3, "name": "Architecture Mapping", "description": "Fingerprint frameworks and services."},
            {"id": 4, "name": "HTTP Inspection", "description": "Review methods, headers, cookies, and CORS."},
            {"id": 5, "name": "Recon", "description": "Discover subdomains, hosts, ports, and endpoints."},
            {"id": 6, "name": "Testing", "description": "Apply endpoint-specific checklists and payloads."},
            {"id": 7, "name": "Proof", "description": "Store evidence and generate PoCs."},
            {"id": 8, "name": "Reporting", "description": "Export structured bug bounty reports."},
        ]

        recent_targets = []
        for t in recent_targets_db:
            recent_targets.append({
                "id": t.id,
                "program_name": t.name,
                "target_level": "intermediate", # Mock since level was removed in new model
                "summary": f"Scope: {t.in_scope[:50]}..." if t.in_scope else "No scope defined"
            })

        recent_findings = []
        for f in recent_findings_db:
            recent_findings.append({
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "vulnerability_class": getattr(f, 'vulnerability_class', 'Unknown')
            })

        return {
            "phases": phases,
            "target_count": db.query(Target).count(),
            "finding_count": db.query(Finding).count(),
            "recent_targets": recent_targets,
            "recent_findings": recent_findings,
        }
    finally:
        db.close()
