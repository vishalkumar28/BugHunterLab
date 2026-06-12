from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.tasks.tool_runner import run_tool
from celery.result import AsyncResult
from app.core.celery_app import celery_app

router = APIRouter()

@router.post("/start", response_model=Dict[str, Any])
async def start_job(target_id: int, tool: str, args: list[str]):
    """
    Trigger a new scan job.
    """
    task = run_tool.delay(tool, args, target_id)
    return {"job_id": task.id, "status": "pending"}

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_status(job_id: str):
    """
    Poll the status of a specific job.
    """
    task_result = AsyncResult(job_id, app=celery_app)
    
    response = {
        "job_id": job_id,
        "status": task_result.status,
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
        
    return response
