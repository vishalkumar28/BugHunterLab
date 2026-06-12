from celery.schedules import crontab
from app.core.celery_app import celery_app
from app.tasks.recon import start_recon_pipeline
from app.database import SessionLocal
from app.models.target import Target
import json

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Runs every day at midnight
    sender.add_periodic_task(
        crontab(minute=0, hour=0),
        run_daily_scans.s(),
        name='run daily recon'
    )

@celery_app.task
def run_daily_scans():
    """
    Fetch all in-scope targets and schedule recon for them.
    """
    db = SessionLocal()
    try:
        targets = db.query(Target).all()
        for target in targets:
            try:
                domains = json.loads(target.in_scope)
                if domains:
                    start_recon_pipeline(target.id, domains)
            except:
                continue
    finally:
        db.close()
