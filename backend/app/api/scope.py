import json
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
    out_of_scope: list[str] = []


class ScopeUpdate(BaseModel):
    program_name: Optional[str] = None
    program_url: Optional[str] = None
    scope_text: Optional[str] = None
    domains: Optional[list[str]] = None
    api_endpoints: Optional[list[str]] = None
    out_of_scope: Optional[list[str]] = None


def _score_target(domains: list, api_endpoints: list, scope_text: str) -> tuple[int, str, str]:
    """Heuristic scorer: returns (score 0-100, level, summary)."""
    score = 0
    score += min(len(domains) * 5, 30)
    score += min(len(api_endpoints) * 5, 20)
    low = scope_text.lower()
    if "graphql" in low:
        score += 10
    if any(w in low for w in ["oauth", "jwt", "saml", "sso"]):
        score += 10
    if any(w in low for w in ["admin", "internal", "corp"]):
        score += 10
    if any(w in low for w in ["upload", "file", "import", "export"]):
        score += 10
    if any(w in low for w in ["idor", "bola", "ssrf", "rce", "sqli"]):
        score += 10
    score = min(score, 100)
    level = "expert" if score >= 65 else ("intermediate" if score >= 35 else "beginner")
    summary = (
        f"Surface: {len(domains)} domain(s), {len(api_endpoints)} API endpoint(s). "
        f"Difficulty: {level.capitalize()}."
    )
    return score, level, summary


def _serialize(t: Target) -> dict:
    try:
        domains = json.loads(t.in_scope) if t.in_scope else []
        if not isinstance(domains, list):
            domains = [t.in_scope] if t.in_scope else []
    except (json.JSONDecodeError, ValueError):
        domains = [d.strip() for d in (t.in_scope or "").replace(",", "\n").splitlines() if d.strip()]

    try:
        oos = json.loads(t.out_of_scope) if t.out_of_scope else []
    except (json.JSONDecodeError, ValueError):
        oos = []

    score, level, summary = _score_target(domains, [], t.in_scope or "")
    return {
        "id": t.id,
        "program_name": t.name,
        "program_url": None,
        "scope_text": t.in_scope or "",
        "domains": domains,
        "api_endpoints": [],
        "out_of_scope": oos,
        "target_score": score,
        "target_level": level,
        "summary": summary,
        "created_at": t.created_at.isoformat() if t.created_at else "",
    }


@router.get("")
def list_scopes():
    """List all scope targets."""
    db = SessionLocal()
    try:
        targets = db.query(Target).order_by(Target.created_at.desc()).all()
        return [_serialize(t) for t in targets]
    finally:
        db.close()


@router.post("")
def create_scope(body: ScopeCreate):
    """Create a new scope target."""
    db = SessionLocal()
    try:
        score, level, summary = _score_target(body.domains, body.api_endpoints, body.scope_text)
        # Store domains as JSON array for reliable parsing later
        stored_scope = json.dumps(body.domains) if body.domains else body.scope_text
        target = Target(
            name=body.program_name,
            in_scope=stored_scope,
            out_of_scope=json.dumps(body.out_of_scope),
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        return {
            "id": target.id,
            "program_name": target.name,
            "program_url": body.program_url,
            "scope_text": stored_scope,
            "domains": body.domains,
            "api_endpoints": body.api_endpoints,
            "out_of_scope": body.out_of_scope,
            "target_score": score,
            "target_level": level,
            "summary": summary,
            "created_at": target.created_at.isoformat() if target.created_at else "",
        }
    finally:
        db.close()


@router.get("/{target_id}")
def get_scope(target_id: int):
    """Get a single scope target by ID."""
    db = SessionLocal()
    try:
        t = db.query(Target).filter(Target.id == target_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Target not found")
        return _serialize(t)
    finally:
        db.close()


@router.put("/{target_id}")
def update_scope(target_id: int, body: ScopeUpdate):
    """Update an existing scope target."""
    db = SessionLocal()
    try:
        t = db.query(Target).filter(Target.id == target_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Target not found")
        if body.program_name is not None:
            t.name = body.program_name
        if body.domains is not None:
            t.in_scope = json.dumps(body.domains)
        elif body.scope_text is not None:
            t.in_scope = body.scope_text
        if body.out_of_scope is not None:
            t.out_of_scope = json.dumps(body.out_of_scope)
        db.commit()
        db.refresh(t)
        return _serialize(t)
    finally:
        db.close()


@router.delete("/{target_id}")
def delete_scope(target_id: int):
    """Delete a scope target and all its findings/assets."""
    db = SessionLocal()
    try:
        t = db.query(Target).filter(Target.id == target_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Target not found")
        db.delete(t)
        db.commit()
        return {"status": "deleted", "id": target_id}
    finally:
        db.close()
