from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .intelligence import VULNERABILITY_DB
from .routers import findings, recon, reports, scope, tools
from .services import ensure_storage, get_learning_modules

ensure_storage()
Base.metadata.create_all(bind=engine)


app = FastAPI(title="BugHunterLab API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit OPTIONS handlers for CORS preflight
from fastapi.responses import JSONResponse

@app.options("/api/dashboard")
def options_dashboard():
    return JSONResponse(content={}, status_code=200)

@app.options("/api/learning")
def options_learning():
    return JSONResponse(content={}, status_code=200)

# ── Register routers ──
app.include_router(scope.router)
app.include_router(recon.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(tools.router)


@app.get("/")
def root():
    return {"name": "BugHunterLab API", "status": "ok"}


@app.get("/api/dashboard")
def dashboard():
    from sqlalchemy.orm import Session

    from .database import SessionLocal
    from .models import Finding, ScopeTarget

    db: Session = SessionLocal()
    try:
        recent_targets = db.query(ScopeTarget).order_by(ScopeTarget.created_at.desc()).limit(5).all()
        recent_findings = db.query(Finding).order_by(Finding.created_at.desc()).limit(5).all()
        phases = [
            {"id": 1, "name": "Fundamentals", "description": "Understand web layers and attack surfaces."},
            {"id": 2, "name": "Programming Knowledge", "description": "Study vuln patterns in code."},
            {"id": 3, "name": "Architecture Mapping", "description": "Fingerprint frameworks and services."},
            {"id": 4, "name": "HTTP Inspection", "description": "Review methods, headers, cookies, and CORS."},
            {"id": 5, "name": "Recon", "description": "Discover subdomains, hosts, ports, and endpoints."},
            {"id": 6, "name": "Testing", "description": "Apply endpoint-specific checklists and payloads."},
            {"id": 7, "name": "Proof", "description": "Store evidence and generate PoCs."},
            {"id": 8, "name": "Reporting", "description": "Export structured bug bounty reports."},
        ]
        return {
            "phases": phases,
            "target_count": db.query(ScopeTarget).count(),
            "finding_count": db.query(Finding).count(),
            "recent_targets": recent_targets,
            "recent_findings": recent_findings,
        }
    finally:
        db.close()


@app.get("/api/learning")
def learning():
    return get_learning_modules()


@app.get("/api/vulnerabilities")
def vulnerabilities():
    return VULNERABILITY_DB