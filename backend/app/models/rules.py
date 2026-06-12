from sqlalchemy import Column, Integer, String, Text
from .base import Base

class VulnerabilityRule(Base):
    __tablename__ = "vulnerability_rules"

    id = Column(Integer, primary_key=True, index=True)
    tech_name = Column(String(100), nullable=False, index=True)
    condition = Column(Text, nullable=True) # e.g. "version < 2.0"
    tool = Column(String(50), nullable=False) # e.g. "nuclei"
    tool_args = Column(Text, nullable=False) # e.g. "-t cves/ -tags {tech_name}"
