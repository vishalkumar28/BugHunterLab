"use client";

import { FormEvent, useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { ScopeTarget } from "./types";

export function ScopeAnalyzerView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    program_name: "",
    program_url: "",
    scope_text: "",
    domains: "",
    api_endpoints: "",
  });

  const loadTargets = () =>
    api
      .scopes()
      .then(setTargets)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

  useEffect(() => {
    loadTargets();
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createScope({
        ...form,
        domains: form.domains.split(",").map((v) => v.trim()).filter(Boolean),
        api_endpoints: form.api_endpoints.split(",").map((v) => v.trim()).filter(Boolean),
      });
      setForm({ program_name: "", program_url: "", scope_text: "", domains: "", api_endpoints: "" });
      await loadTargets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create scope target");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell title="Scope Analyzer" description="Capture program scope, classify target quality, and decide whether the target fits your current research depth.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
        <SectionCard title="Analyze Target" eyebrow="Program Intake">
          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label htmlFor="program_name" className="mb-1 block text-xs font-medium text-ink/60">Program Name</label>
              <input id="program_name" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. Acme Public Program" value={form.program_name} onChange={(e) => setForm({ ...form, program_name: e.target.value })} required />
            </div>
            <div>
              <label htmlFor="program_url" className="mb-1 block text-xs font-medium text-ink/60">Program URL</label>
              <input id="program_url" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. https://hackerone.com/acme" value={form.program_url} onChange={(e) => setForm({ ...form, program_url: e.target.value })} />
            </div>
            <div>
              <label htmlFor="scope_text" className="mb-1 block text-xs font-medium text-ink/60">Scope Description</label>
              <textarea id="scope_text" className="min-h-32 w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="Paste scope details, one per line…" value={form.scope_text} onChange={(e) => setForm({ ...form, scope_text: e.target.value })} required />
            </div>
            <div>
              <label htmlFor="domains" className="mb-1 block text-xs font-medium text-ink/60">Domains (comma-separated)</label>
              <input id="domains" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. acme.test, app.acme.test" value={form.domains} onChange={(e) => setForm({ ...form, domains: e.target.value })} />
            </div>
            <div>
              <label htmlFor="api_endpoints" className="mb-1 block text-xs font-medium text-ink/60">API Endpoints (comma-separated)</label>
              <input id="api_endpoints" className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3" placeholder="e.g. /api/users, /graphql" value={form.api_endpoints} onChange={(e) => setForm({ ...form, api_endpoints: e.target.value })} />
            </div>
            <button className="rounded-full bg-ink px-5 py-3 text-white transition hover:bg-rust disabled:opacity-50" type="submit" disabled={submitting}>
              {submitting ? "Scoring…" : "Score Target"}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Scoring Factors" eyebrow="What Matters">
          <ul className="space-y-3 text-sm text-ink/80">
            <li>Attack surface size across domains and applications.</li>
            <li>API presence, auth boundaries, and privileged features.</li>
            <li>Complexity signals that usually correlate with rich bug classes.</li>
            <li>Classification into beginner-friendly, intermediate, or expert-level.</li>
          </ul>
        </SectionCard>
      </div>

      <SectionCard title="Tracked Programs" eyebrow="Output">
        {loading && <p className="text-sm text-ink/60 animate-pulse">Loading targets…</p>}
        <div className="grid gap-4 lg:grid-cols-2">
          {targets.map((target) => (
            <div className="rounded-2xl border border-black/10 bg-white/60 p-5" key={target.id}>
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-display text-xl">{target.program_name}</h3>
                <span className="rounded-full bg-brass px-3 py-1 text-xs text-white">{target.target_score}/100</span>
              </div>
              <p className="mt-3 text-sm text-ink/75">{target.summary}</p>
            </div>
          ))}
          {!loading && !targets.length ? <p className="text-sm text-ink/70">No scope targets recorded yet.</p> : null}
        </div>
      </SectionCard>
    </PageShell>
  );
}