from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import SessionLocal
from app.models.target import Target

router = APIRouter()


class ScopeCreate(BaseModel):
    program_name: str
    program_url: Optional[str] = None
    scope_text: str
    domains: list[str] = []
    api_endpoints: list[str] = []


def _score_target(domains: list, api_endpoints: list, scope_text: str) -> tuple[int, str, str]:
    """Simple heuristic scorer: returns (score, level, summary)."""
    score = 0
    score += min(len(domains) * 5, 30)
    score += min(len(api_endpoints) * 5, 20)
    if "graphql" in scope_text.lower():
        score += 10
    if any(w in scope_text.lower() for w in ["oauth", "jwt", "saml", "sso"]):
        score += 10
    if any(w in scope_text.lower() for w in ["admin", "internal", "corp"]):
        score += 10
    if any(w in scope_text.lower() for w in ["upload", "file", "import", "export"]):
        score += 10
    if any(w in scope_text.lower() for w in ["idor", "bola", "idor", "ssrf", "rce", "sqli"]):
        score += 10
    score = min(score, 100)
    if score >= 65:
        level = "expert"
    elif score >= 35:
        level = "intermediate"
    else:
        level = "beginner"
    summary = (
        f"Surface: {len(domains)} domain(s), {len(api_endpoints)} API endpoint(s). "
        f"Difficulty: {level.capitalize()}."
    )
    return score, level, summary


@router.get("")
def list_scopes():
    db = SessionLocal()
    try:
        targets = db.query(Target).order_by(Target.created_at.desc()).all()
        return [
            {
                "id": t.id,
                "program_name": t.name,
                "program_url": None,
                "scope_text": t.in_scope or "",
                "domains": [],
                "api_endpoints": [],
                "target_score": 0,
                "target_level": "intermediate",
                "summary": f"Scope: {(t.in_scope or '')[:60]}",
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
            for t in targets
        ]
    finally:
        db.close()


@router.post("")
def create_scope(body: ScopeCreate):
    db = SessionLocal()
    try:
        score, level, summary = _score_target(body.domains, body.api_endpoints, body.scope_text)
        target = Target(
            name=body.program_name,
            in_scope=body.scope_text,
            out_of_scope=None,
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        return {
            "id": target.id,
            "program_name": target.name,
            "program_url": body.program_url,
            "scope_text": target.in_scope,
            "domains": body.domains,
            "api_endpoints": body.api_endpoints,
            "target_score": score,
            "target_level": level,
            "summary": summary,
            "created_at": target.created_at.isoformat() if target.created_at else "",
        }
    finally:
        db.close()
