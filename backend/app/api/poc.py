from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.finding import Finding

router = APIRouter()


class PocRequest(BaseModel):
    finding_id: int
    poc_type: str  # curl, python, burp


POC_TEMPLATES = {
    "curl": """\
# cURL Proof of Concept
# Finding: {title}
# Severity: {severity}
curl -v \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  "https://TARGET_HOST{endpoint}"
""",
    "python": """\
# Python Proof of Concept
# Finding: {title}
# Severity: {severity}
import requests

session = requests.Session()
session.headers.update({{"Authorization": "Bearer YOUR_TOKEN"}})

resp = session.get("https://TARGET_HOST{endpoint}")
print(resp.status_code, resp.text[:500])
""",
    "burp": """\
# Burp Suite Repeater Request
# Finding: {title}
# Severity: {severity}
GET {endpoint} HTTP/1.1
Host: TARGET_HOST
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

""",
}


@router.post("")
def generate_poc(body: PocRequest):
    db = SessionLocal()
    try:
        finding = db.query(Finding).filter(Finding.id == body.finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")

        template = POC_TEMPLATES.get(body.poc_type, POC_TEMPLATES["curl"])
        content = template.format(
            title=finding.title,
            severity=finding.severity,
            endpoint=f"/api/resource/{finding.target_id}",
        )
        return {
            "finding_id": body.finding_id,
            "poc_type": body.poc_type,
            "content": content,
        }
    finally:
        db.close()
