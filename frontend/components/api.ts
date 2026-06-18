import type {
  ChecklistItem,
  DashboardData,
  Finding,
  LearningPhase,
  PocResponse,
  ReconRun,
  ReportResponse,
  ScopeTarget,
  VulnerabilityEntry,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "Unknown error");
    throw new Error(`API ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

async function upload(path: string, file: File): Promise<unknown> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "Unknown error");
    throw new Error(`Upload ${response.status}: ${detail}`);
  }
  return response.json();
}

export const API_BASE_URL = API_BASE;

export const api = {
  // Dashboard
  dashboard: () => request<DashboardData>("/dashboard"),

  // Learning / knowledge base
  learning: () => request<Record<string, LearningPhase>>("/learning"),
  vulnerabilities: () => request<Record<string, VulnerabilityEntry>>("/vulnerabilities"),

  // Scope targets
  scopes: () => request<ScopeTarget[]>("/scope"),
  getScope: (id: number) => request<ScopeTarget>(`/scope/${id}`),
  createScope: (body: Omit<ScopeTarget, "id" | "target_score" | "target_level" | "summary" | "created_at">) =>
    request<ScopeTarget>("/scope", { method: "POST", body: JSON.stringify(body) }),
  updateScope: (id: number, body: Partial<ScopeTarget>) =>
    request<ScopeTarget>(`/scope/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteScope: (id: number) => request<{ status: string }>(`/scope/${id}`, { method: "DELETE" }),

  // Recon  
  runRecon: (targetId: number) => request<unknown>(`/recon/${targetId}`, { method: "POST" }),
  getReconResults: (targetId: number) => request<unknown>(`/recon/${targetId}`),
  reconRuns: (targetId: number) => request<unknown>(`/recon/${targetId}`), // backward-compat alias
  clearRecon: (targetId: number) =>
    request<{ deleted: number }>(`/recon/${targetId}/assets`, { method: "DELETE" }),

  // Findings
  findings: (targetId?: number) =>
    request<Finding[]>(targetId ? `/findings?target_id=${targetId}` : "/findings"),
  getFinding: (id: number) => request<Finding>(`/findings/${id}`),
  createFinding: (body: Omit<Finding, "id" | "status" | "created_at" | "evidence_files">) =>
    request<Finding>("/findings", { method: "POST", body: JSON.stringify(body) }),
  updateFinding: (id: number, body: Partial<Finding>) =>
    request<Finding>(`/findings/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteFinding: (id: number) => request<{ status: string }>(`/findings/${id}`, { method: "DELETE" }),

  // Checklists
  checklists: (targetId: number) => request<ChecklistItem[]>(`/checklists?target_id=${targetId}`),

  // PoC
  poc: (findingId: number, pocType: string) =>
    request<PocResponse>("/poc", { method: "POST", body: JSON.stringify({ finding_id: findingId, poc_type: pocType }) }),

  // Report
  report: (findingId: number) => request<ReportResponse>(`/report/${findingId}`),
  downloadReportPdf: (findingId: number) => `${API_BASE}/report/${findingId}/pdf`,

  // Evidence
  listEvidence: (findingId: number) => request<unknown[]>(`/evidence/${findingId}`),
  uploadEvidence: (findingId: number, file: File) => upload(`/evidence/${findingId}`, file),
  downloadEvidenceUrl: (findingId: number, filename: string) =>
    `${API_BASE}/evidence/${findingId}/${filename}`,
  deleteEvidence: (findingId: number, filename: string) =>
    request<{ status: string }>(`/evidence/${findingId}/${filename}`, { method: "DELETE" }),

  // Jobs
  listJobs: (targetId?: number) =>
    request<unknown[]>(targetId ? `/jobs?target_id=${targetId}` : "/jobs"),
  startJob: (targetId: number, tool: string, args: string[]) =>
    request<{ job_id: string; status: string }>(`/jobs/start?target_id=${targetId}&tool=${tool}`, {
      method: "POST",
      body: JSON.stringify(args),
    }),
  getJob: (jobId: string) => request<unknown>(`/jobs/${jobId}`),
};