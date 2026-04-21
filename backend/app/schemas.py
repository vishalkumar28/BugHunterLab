from datetime import datetime

from pydantic import BaseModel, Field


class ScopeTargetCreate(BaseModel):
    program_name: str
    program_url: str | None = None
    scope_text: str
    domains: list[str] = Field(default_factory=list)
    api_endpoints: list[str] = Field(default_factory=list)


class ScopeTargetRead(BaseModel):
    id: int
    program_name: str
    program_url: str | None
    scope_text: str
    domains: list[str]
    api_endpoints: list[str]
    target_score: int
    target_level: str
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReconRunRead(BaseModel):
    id: int
    target_id: int
    status: str
    assets: dict
    attack_surface: dict
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingCreate(BaseModel):
    target_id: int
    title: str
    vulnerability_class: str
    severity: str
    endpoint: str = ""
    description: str
    evidence: list[dict] = Field(default_factory=list)
    reproduction_steps: list[str] = Field(default_factory=list)


class FindingRead(BaseModel):
    id: int
    target_id: int
    title: str
    vulnerability_class: str
    severity: str
    status: str
    endpoint: str
    description: str
    evidence: list[dict]
    reproduction_steps: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChecklistItem(BaseModel):
    endpoint: str
    method: str
    checklist: list[str]


class PocRequest(BaseModel):
    finding_id: int
    poc_type: str = "curl"


class ReportResponse(BaseModel):
    title: str
    markdown: str
    plain_text: str
    pdf_path: str


class DashboardResponse(BaseModel):
    phases: list[dict]
    target_count: int
    finding_count: int
    recent_targets: list[ScopeTargetRead]
    recent_findings: list[FindingRead]