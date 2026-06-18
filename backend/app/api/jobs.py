import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.tasks.tool_runner import run_tool
from app.database import SessionLocal
from app.models.job import Job
from celery.result import AsyncResult
from app.core.celery_app import celery_app

router = APIRouter()

ALLOWED_TOOLS = {"subfinder", "httpx", "nuclei", "nmap", "ffuf", "gau", "waybackurls", "katana"}


@router.post("/start", response_model=Dict[str, Any])
async def start_job(target_id: int, tool: str, args: list[str] = None):
    """
    Trigger a new scan job for a target.
    - tool: one of subfinder, httpx, nuclei, nmap, ffuf, gau, katana
    - args: list of CLI arguments passed to the tool
    """
    if tool not in ALLOWED_TOOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool}' is not allowed. Allowed tools: {sorted(ALLOWED_TOOLS)}"
        )

    args = args or []
    task = run_tool.delay(tool, args, target_id)

    # Persist job record
    db = SessionLocal()
    try:
        job = Job(
            target_id=target_id,
            task_id=task.id,
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return {
        "job_id": task.id,
        "tool": tool,
        "target_id": target_id,
        "status": "pending",
        "ws_url": f"ws://localhost:8000/ws/logs/{target_id}",
    }


@router.get("", response_model=list[Dict[str, Any]])
async def list_jobs(target_id: int = None):
    """List all scan jobs, optionally filtered by target."""
    db = SessionLocal()
    try:
        q = db.query(Job).order_by(Job.started_at.desc())
        if target_id:
            q = q.filter(Job.target_id == target_id)
        jobs = q.limit(50).all()
        result = []
        for job in jobs:
            # Sync Celery status
            task_result = AsyncResult(job.task_id, app=celery_app)
            status = task_result.status.lower() if task_result.status else job.status
            result.append({
                "job_id": job.task_id,
                "db_id": job.id,
                "target_id": job.target_id,
                "status": status,
                "started_at": job.started_at.isoformat() if job.started_at else "",
                "completed_at": job.completed_at.isoformat() if job.completed_at else "",
            })
        return result
    finally:
        db.close()


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_status(job_id: str):
    """Poll the status and result of a specific scan job."""
    task_result = AsyncResult(job_id, app=celery_app)

    response: Dict[str, Any] = {
        "job_id": job_id,
        "status": task_result.status,
    }

    if task_result.status == "SUCCESS":
        result = task_result.result
        response["result"] = result
        # Auto-update DB record
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.task_id == job_id).first()
            if job:
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                job.result = json.dumps(result) if isinstance(result, dict) else str(result)
                db.commit()
        finally:
            db.close()
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)

    return response
