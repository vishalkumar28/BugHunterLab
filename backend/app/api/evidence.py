"""
Evidence upload/download/list/delete endpoints.
POST   /api/evidence/{finding_id}          — upload file
GET    /api/evidence/{finding_id}          — list files
GET    /api/evidence/{finding_id}/{file}   — download file
DELETE /api/evidence/{finding_id}/{file}   — delete file
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.database import SessionLocal
from app.models.finding import Finding
from app.services.storage import save_evidence, list_evidence, delete_evidence, get_evidence_path

router = APIRouter()

MAX_UPLOAD_MB = 20


def _verify_finding(finding_id: int):
    db = SessionLocal()
    try:
        f = db.query(Finding).filter(Finding.id == finding_id).first()
        if not f:
            raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")
    finally:
        db.close()


@router.post("/{finding_id}")
async def upload_evidence(finding_id: int, file: UploadFile = File(...)):
    """Upload an evidence file (screenshot, log, request/response dump) for a finding."""
    _verify_finding(finding_id)

    # Reject suspiciously large uploads
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_MB} MB limit")

    # Rewind the file so save_evidence can read it
    import io
    file.file = io.BytesIO(contents)

    meta = save_evidence(file, finding_id)
    return {"status": "uploaded", **meta}


@router.get("/{finding_id}")
def list_finding_evidence(finding_id: int):
    """List all evidence files attached to a finding."""
    _verify_finding(finding_id)
    return list_evidence(finding_id)


@router.get("/{finding_id}/{filename}")
def download_evidence(finding_id: int, filename: str):
    """Stream/download a specific evidence file."""
    _verify_finding(finding_id)
    # Sanitise — no path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = get_evidence_path(finding_id, filename)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(path), filename=filename)


@router.delete("/{finding_id}/{filename}")
def remove_evidence(finding_id: int, filename: str):
    """Delete a specific evidence file."""
    _verify_finding(finding_id)
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    deleted = delete_evidence(finding_id, filename)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "filename": filename}
