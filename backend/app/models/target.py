from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    in_scope = Column(Text, nullable=False)
    out_of_scope = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assets = relationship("Asset", back_populates="target", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="target", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="target", cascade="all, delete-orphan")
