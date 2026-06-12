from fastapi import APIRouter
from app.api.jobs import router as jobs_router
from app.api.submissions import router as submissions_router
from app.api.dashboard import router as dashboard_router
from app.api.learning import router as learning_router
from app.api.scope import router as scope_router
from app.api.findings import router as findings_router
from app.api.recon import router as recon_router
from app.api.vulnerabilities import router as vulnerabilities_router
from app.api.checklists import router as checklists_router
from app.api.poc import router as poc_router
from app.api.report import router as report_router

api_router = APIRouter()
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(submissions_router, prefix="/submissions", tags=["submissions"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(learning_router, prefix="/learning", tags=["learning"])
api_router.include_router(scope_router, prefix="/scope", tags=["scope"])
api_router.include_router(findings_router, prefix="/findings", tags=["findings"])
api_router.include_router(recon_router, prefix="/recon", tags=["recon"])
api_router.include_router(vulnerabilities_router, prefix="/vulnerabilities", tags=["vulnerabilities"])
api_router.include_router(checklists_router, prefix="/checklists", tags=["checklists"])
api_router.include_router(poc_router, prefix="/poc", tags=["poc"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
