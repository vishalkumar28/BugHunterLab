import subprocess
import json
import os
from celery import shared_task
from app.core.celery_app import celery_app
import redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

@shared_task(bind=True)
def run_tool(self, tool_name: str, args: list, target_id: int):
    """
    Generic task to run CLI tools safely within the container.
    """
    command = [tool_name] + args
    
    # Notify start
    job_msg = {
        "job_id": self.request.id,
        "target_id": target_id,
        "status": "running",
        "tool": tool_name
    }
    redis_client.publish(f"target_{target_id}_updates", json.dumps(job_msg))
    
    try:
        # Run subprocess
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=3600 # 1 hour max
        )
        
        status = "completed" if result.returncode == 0 else "failed"
        
        job_msg["status"] = status
        redis_client.publish(f"target_{target_id}_updates", json.dumps(job_msg))
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        job_msg["status"] = "timeout"
        redis_client.publish(f"target_{target_id}_updates", json.dumps(job_msg))
        return {"error": "Timeout expired after 3600 seconds"}
    except Exception as e:
        job_msg["status"] = "error"
        job_msg["error"] = str(e)
        redis_client.publish(f"target_{target_id}_updates", json.dumps(job_msg))
        return {"error": str(e)}
