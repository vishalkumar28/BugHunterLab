// ── Shared types mirroring backend schemas ──

export type ScopeTarget = {
  id: number;
  program_name: string;
  program_url?: string | null;
  scope_text: string;
  domains: string[];
  api_endpoints: string[];
  target_score: number;
  target_level: string;
  summary: string;
  created_at: string;
};

export type Finding = {
  id: number;
  target_id: number;
  title: string;
  vulnerability_class: string;
  severity: string;
  status: string;
  endpoint: string;
  description: string;
  evidence: Array<Record<string, string>>;
  reproduction_steps: string[];
  created_at: string;
};

export type ReconRun = {
  id: number;
  target_id: number;
  status: string;
  assets: {
    domains?: string[];
    subdomains?: string[];
    live_hosts?: string[];
    open_ports?: Array<{ host: string; ports: number[] }>;
    technologies?: Array<Record<string, string>>;
    hidden_endpoints?: string[];
  };
  attack_surface: {
    nodes: Array<{ id: string; type: string }>;
    edges: Array<{ source: string; target: string; label: string }>;
  };
  notes: string;
  created_at: string;
};

export type ChecklistItem = {
  endpoint: string;
  method: string;
  checklist: string[];
};

export type ReportResponse = {
  title: string;
  markdown: string;
  plain_text: string;
  pdf_path: string;
};

export type DashboardData = {
  phases: Array<{ id: number; name: string; description: string }>;
  target_count: number;
  finding_count: number;
  recent_targets: ScopeTarget[];
  recent_findings: Finding[];
};

export type VulnerabilityEntry = {
  description: string;
  attack_conditions: string[];
  exploitation_method: string;
  impact: string;
  testing_checklist: string[];
  poc_examples: string[];
};

export type PocResponse = {
  finding_id: number;
  poc_type: string;
  content: string;
};

export type LearningPhase = {
  title: string;
  topics?: string[];
  visualizations?: string[];
  languages?: Record<string, unknown>;
  tools?: string[];
  focus?: string[];
  highlight_issues?: string[];
};