from fastapi import APIRouter
from app.api.jobs import router as jobs_router
from app.api.submissions import router as submissions_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(submissions_router, prefix="/submissions", tags=["submissions"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
