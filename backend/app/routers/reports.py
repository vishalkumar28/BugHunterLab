from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ReportResponse
from ..services import generate_report, render_pdf_report

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/report/{finding_id}", response_model=ReportResponse)
def report(finding_id: int, db: Session = Depends(get_db)):
    report_data = generate_report(db, finding_id)
    if not report_data:
        raise HTTPException(status_code=404, detail="Finding not found")
    return ReportResponse(**report_data)


@router.get("/report/{finding_id}/pdf")
def report_pdf(finding_id: int, db: Session = Depends(get_db)):
    report_data = generate_report(db, finding_id)
    if not report_data:
        raise HTTPException(status_code=404, detail="Finding not found")
    pdf_bytes = render_pdf_report(report_data)
    pdf_path = Path(report_data["pdf_path"])
    pdf_path.write_bytes(pdf_bytes)
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)
