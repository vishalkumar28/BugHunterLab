from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ScopeTarget
from ..schemas import ScopeTargetCreate, ScopeTargetRead
from ..services import create_scope_target

router = APIRouter(prefix="/api", tags=["scope"])


@router.post("/scope", response_model=ScopeTargetRead)
def create_scope(payload: ScopeTargetCreate, db: Session = Depends(get_db)):
    return create_scope_target(db, payload)


@router.get("/scope", response_model=list[ScopeTargetRead])
def list_scope(db: Session = Depends(get_db)):
    return db.query(ScopeTarget).order_by(ScopeTarget.created_at.desc()).all()
