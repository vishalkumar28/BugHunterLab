from celery import shared_task, chain
from app.tasks.tool_runner import run_tool
import json
import asyncio
from app.database import SessionLocal
from app.models.target import Target
from app.models.asset import Asset
from sqlalchemy.orm import Session

@shared_task(bind=True)
def normalize_assets_task(self, previous_results: list, target_id: int):
    """
    Parses outputs from previous tasks and normalizes them into the database.
    """
    # Simplified mock logic for parsing tool outputs
    db = SessionLocal()
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            return {"error": "Target not found"}
        
        # In a real scenario, we would parse JSON files from shared volume or result dict
        # For this prototype, we'll just create a dummy asset
        
        asset = Asset(
            target_id=target_id,
            type="subdomain",
            value="api.example.com",
            is_alive=True
        )
        db.add(asset)
        db.commit()
        
        return {"status": "success", "assets_added": 1}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

def start_recon_pipeline(target_id: int, domains: list[str]):
    """
    Builds and dispatches the Celery chain for full recon.
    """
    if not domains:
        return None
    
    # Example chain: subfinder -> httpx -> normalize
    # In production, pass appropriate args like out-files
    
    recon_chain = chain(
        run_tool.s("subfinder", ["-d", domains[0], "-silent"], target_id),
        run_tool.s("httpx", ["-silent"], target_id), # Ideally takes input from subfinder
        normalize_assets_task.s(target_id)
    )
    
    result = recon_chain.apply_async()
    return result.id
