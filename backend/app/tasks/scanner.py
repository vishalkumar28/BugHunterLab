from celery import shared_task, group
from app.tasks.tool_runner import run_tool
from app.services.rule_engine import generate_scan_plan

@shared_task(bind=True)
def run_targeted_scans(self, asset_id: int, target_id: int):
    """
    Generates a scan plan for a specific asset and launches the required tools in parallel.
    """
    plan = generate_scan_plan(asset_id)
    
    if not plan:
        return {"status": "no_plan", "message": "No specific rules matched technologies."}
    
    tasks = []
    for item in plan:
        tasks.append(run_tool.s(item["tool"], item["args"], target_id))
        
    # Group tasks to run them in parallel
    job = group(tasks)
    result = job.apply_async()
    return {"job_id": result.id, "tasks_launched": len(tasks)}
