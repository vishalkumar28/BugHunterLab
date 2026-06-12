from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    type = Column(String(50), nullable=False) # subdomain, ip, url
    value = Column(String(512), nullable=False, index=True)
    is_alive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    target = relationship("Target", back_populates="assets")
    technologies = relationship("AssetTechnology", back_populates="asset", cascade="all, delete-orphan")

class AssetTechnology(Base):
    __tablename__ = "asset_technologies"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    tech_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)

    asset = relationship("Asset", back_populates="technologies")
