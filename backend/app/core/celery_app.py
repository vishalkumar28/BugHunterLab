import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("bughunter", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=3600, # 1 hour max per task
    worker_concurrency=4,
    broker_connection_retry_on_startup=True
)

celery_app.autodiscover_tasks(['app.tasks'])
