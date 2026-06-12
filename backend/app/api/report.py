from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.finding import Finding

router = APIRouter()


def _build_markdown(finding: Finding) -> str:
    return f"""# Bug Bounty Report: {finding.title}

**Severity:** {finding.severity.upper()}  
**Vulnerability Class:** {getattr(finding, 'vulnerability_class', 'Unknown') or 'Unknown'}  
**Status:** Open  

---

## Description

{finding.description}

## Reproduction Steps

1. Authenticate as a normal user
2. Navigate to the affected endpoint
3. Observe the vulnerability

## Evidence

{finding.evidence or 'No evidence attached.'}

## Impact

This vulnerability could allow attackers to compromise user data or application integrity.

## Remediation

- Implement proper authorization checks
- Validate and sanitize all user input
- Apply the principle of least privilege
"""


def _build_plain(finding: Finding) -> str:
    return (
        f"TITLE: {finding.title}\n"
        f"SEVERITY: {finding.severity.upper()}\n"
        f"CLASS: {getattr(finding, 'vulnerability_class', 'Unknown') or 'Unknown'}\n\n"
        f"DESCRIPTION:\n{finding.description}\n\n"
        f"EVIDENCE:\n{finding.evidence or 'None'}\n"
    )


@router.get("/{finding_id}")
def get_report(finding_id: int):
    db = SessionLocal()
    try:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        md = _build_markdown(finding)
        plain = _build_plain(finding)
        return {
            "title": finding.title,
            "markdown": md,
            "plain_text": plain,
            "pdf_path": f"/api/report/{finding_id}/pdf",
        }
    finally:
        db.close()
