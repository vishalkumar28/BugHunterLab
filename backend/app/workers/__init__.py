# Register all Celery tasks so the worker picks them up on autodiscovery
from app.tasks.tool_runner import run_tool  # noqa: F401
from app.tasks.recon import normalize_assets_task  # noqa: F401
from app.tasks.scanner import run_targeted_scans  # noqa: F401
