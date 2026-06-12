from fastapi import APIRouter, HTTPException
import requests
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class SubmissionRequest(BaseModel):
    finding_id: int
    platform: str # hackerone or bugcrowd

@router.post("/submit")
def submit_report(req: SubmissionRequest):
    """
    Submit a generated report to an external bug bounty platform.
    """
    if req.platform == "hackerone":
        if not settings.HACKERONE_API_TOKEN:
            raise HTTPException(status_code=400, detail="HackerOne token not configured")
            
        # Mock submission logic
        # requests.post("https://api.hackerone.com/v1/reports", headers={"Authorization": f"Bearer {settings.HACKERONE_API_TOKEN}"})
        
        return {"status": "success", "platform": "hackerone", "external_id": "12345"}
        
    raise HTTPException(status_code=400, detail="Unsupported platform")
