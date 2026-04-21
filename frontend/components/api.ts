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

export const API_BASE_URL = API_BASE;

export const api = {
  dashboard: () => request<DashboardData>("/dashboard"),
  learning: () => request<Record<string, LearningPhase>>("/learning"),
  vulnerabilities: () => request<Record<string, VulnerabilityEntry>>("/vulnerabilities"),
  scopes: () => request<ScopeTarget[]>("/scope"),
  createScope: (body: Omit<ScopeTarget, "id" | "target_score" | "target_level" | "summary" | "created_at">) =>
    request<ScopeTarget>("/scope", { method: "POST", body: JSON.stringify(body) }),
  runRecon: (targetId: number) => request<ReconRun>(`/recon/${targetId}`, { method: "POST" }),
  reconRuns: (targetId: number) => request<ReconRun[]>(`/recon/${targetId}`),
  findings: () => request<Finding[]>("/findings"),
  createFinding: (body: Omit<Finding, "id" | "status" | "created_at">) =>
    request<Finding>("/findings", { method: "POST", body: JSON.stringify(body) }),
  checklists: (targetId: number) => request<ChecklistItem[]>(`/checklists?target_id=${targetId}`),
  poc: (findingId: number, pocType: string) =>
    request<PocResponse>("/poc", { method: "POST", body: JSON.stringify({ finding_id: findingId, poc_type: pocType }) }),
  report: (findingId: number) => request<ReportResponse>(`/report/${findingId}`),
};