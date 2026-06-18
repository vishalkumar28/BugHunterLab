"""
Local-filesystem evidence storage.
Files are stored under ./evidence/<finding_id>/<uuid>_<filename>
In production, swap save/get_url for S3 calls.
"""
import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile

EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", "/app/evidence"))


def ensure_dirs(finding_id: int) -> Path:
    dest = EVIDENCE_DIR / str(finding_id)
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def save_evidence(file: UploadFile, finding_id: int) -> dict:
    """Save an uploaded file and return metadata."""
    dest = ensure_dirs(finding_id)
    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'upload')}"
    file_path = dest / safe_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = file_path.stat().st_size
    return {
        "filename": safe_name,
        "original_name": file.filename,
        "path": str(file_path),
        "size_bytes": size,
        "url": f"/api/evidence/{finding_id}/{safe_name}",
    }


def list_evidence(finding_id: int) -> list[dict]:
    """List all evidence files for a finding."""
    dest = EVIDENCE_DIR / str(finding_id)
    if not dest.exists():
        return []
    files = []
    for f in sorted(dest.iterdir()):
        if f.is_file():
            files.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "url": f"/api/evidence/{finding_id}/{f.name}",
            })
    return files


def delete_evidence(finding_id: int, filename: str) -> bool:
    """Delete a specific evidence file."""
    file_path = EVIDENCE_DIR / str(finding_id) / filename
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        return True
    return False


def get_evidence_path(finding_id: int, filename: str) -> Path | None:
    """Return the full path to an evidence file (for streaming)."""
    file_path = EVIDENCE_DIR / str(finding_id) / filename
    return file_path if file_path.exists() else None
