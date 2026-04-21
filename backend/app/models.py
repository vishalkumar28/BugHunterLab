from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScopeTarget(Base):
    __tablename__ = "scope_targets"

    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String(255), nullable=False)
    program_url = Column(String(512), nullable=True)
    scope_text = Column(Text, nullable=False)
    domains = Column(JSON, nullable=False, default=list)
    api_endpoints = Column(JSON, nullable=False, default=list)
    target_score = Column(Integer, nullable=False, default=0)
    target_level = Column(String(50), nullable=False, default="beginner-friendly")
    summary = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    recon_runs = relationship("ReconRun", back_populates="target", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="target", cascade="all, delete-orphan")


class ReconRun(Base):
    __tablename__ = "recon_runs"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("scope_targets.id"), nullable=False)
    status = Column(String(50), nullable=False, default="completed")
    assets = Column(JSON, nullable=False, default=dict)
    attack_surface = Column(JSON, nullable=False, default=dict)
    notes = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    target = relationship("ScopeTarget", back_populates="recon_runs")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("scope_targets.id"), nullable=False)
    title = Column(String(255), nullable=False)
    vulnerability_class = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    endpoint = Column(String(512), nullable=False, default="")
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False, default=list)
    reproduction_steps = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    target = relationship("ScopeTarget", back_populates="findings")