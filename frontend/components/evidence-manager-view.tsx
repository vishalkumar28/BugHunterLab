"use client";

import { FormEvent, useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { Finding, ScopeTarget } from "./types";

export function EvidenceManagerView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    target_id: 0,
    title: "",
    vulnerability_class: "",
    severity: "Medium",
    endpoint: "",
    description: "",
    reproduction_steps: "",
  });

  async function loadData() {
    try {
      const [scopeData, findingData] = await Promise.all([api.scopes(), api.findings()]);
      setTargets(scopeData);
      setFindings(findingData);
      if (!form.target_id && scopeData[0]) {
        setForm((current) => ({ ...current, target_id: scopeData[0].id }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createFinding({
        ...form,
        evidence: "Captured during local reproduction",
        reproduction_steps: form.reproduction_steps,
      });
      setForm((prev) => ({
        ...prev,
        title: "",
        vulnerability_class: "",
        severity: "Medium",
        endpoint: "",
        description: "",
        reproduction_steps: "",
      }));
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save finding");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell title="Evidence Manager" description="Preserve proof, request data, response data, and analyst notes in a finding record that is ready for validation and reporting.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <div className="grid gap-6 xl:grid-cols-[1fr,1fr]">
        <SectionCard title="Record Finding" eyebrow="Proof Collection">
          {loading ? (
            <p className="text-sm text-ink/60 animate-pulse">Loading…</p>
          ) : (
            <form className="space-y-4" onSubmit={onSubmit}>
              <div>
                <label htmlFor="ev-target" className="mb-1 block text-xs font-medium text-ink/60">Target Program</label>
                <select id="ev-target" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setForm({ ...form, target_id: Number(e.target.value) })} value={form.target_id}>
                  {targets.map((target) => (
                    <option key={target.id} value={target.id}>{target.program_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="ev-title" className="mb-1 block text-xs font-medium text-ink/60">Finding Title</label>
                <input id="ev-title" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. IDOR on /api/users/update" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
              </div>
              <div>
                <label htmlFor="ev-vulnclass" className="mb-1 block text-xs font-medium text-ink/60">Vulnerability Class</label>
                <input id="ev-vulnclass" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. IDOR, XSS, SQLi" value={form.vulnerability_class} onChange={(e) => setForm({ ...form, vulnerability_class: e.target.value })} required />
              </div>
              <div>
                <label htmlFor="ev-severity" className="mb-1 block text-xs font-medium text-ink/60">Severity</label>
                <select id="ev-severity" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                  <option>Critical</option>
                  <option>High</option>
                  <option>Medium</option>
                  <option>Low</option>
                  <option>Informational</option>
                </select>
              </div>
              <div>
                <label htmlFor="ev-endpoint" className="mb-1 block text-xs font-medium text-ink/60">Endpoint</label>
                <input id="ev-endpoint" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. /api/users/update" value={form.endpoint} onChange={(e) => setForm({ ...form, endpoint: e.target.value })} />
              </div>
              <div>
                <label htmlFor="ev-desc" className="mb-1 block text-xs font-medium text-ink/60">Description</label>
                <textarea id="ev-desc" className="min-h-24 w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="Describe the vulnerability and its impact…" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
              </div>
              <div>
                <label htmlFor="ev-steps" className="mb-1 block text-xs font-medium text-ink/60">Reproduction Steps (one per line)</label>
                <textarea id="ev-steps" className="min-h-32 w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="Step 1&#10;Step 2&#10;Step 3" value={form.reproduction_steps} onChange={(e) => setForm({ ...form, reproduction_steps: e.target.value })} />
              </div>
              <button className="rounded-full bg-rust px-5 py-3 text-white disabled:opacity-50" type="submit" disabled={submitting}>
                {submitting ? "Saving…" : "Save Evidence"}
              </button>
            </form>
          )}
        </SectionCard>

        <SectionCard title="Finding Records" eyebrow="Stored Proof">
          <div className="space-y-4">
            {findings.map((finding) => (
              <div className="rounded-2xl border border-black/10 bg-white/70 p-5" key={finding.id}>
                <div className="flex items-center justify-between gap-3">
                  <strong>{finding.title}</strong>
                  <span className="rounded-full bg-rust px-3 py-1 text-xs text-white">{finding.severity}</span>
                </div>
                <p className="mt-2 text-sm text-ink/75">{finding.description}</p>
              </div>
            ))}
            {!loading && !findings.length ? <p className="text-sm text-ink/70">No stored findings yet.</p> : null}
          </div>
        </SectionCard>
      </div>
    </PageShell>
  );
}