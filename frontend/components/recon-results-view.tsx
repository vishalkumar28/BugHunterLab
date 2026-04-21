"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { ReconRun, ScopeTarget } from "./types";

export function ReconResultsView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
  const [recon, setRecon] = useState<ReconRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .scopes()
      .then((scopes) => {
        setTargets(scopes);
        setSelectedTarget(scopes[0]?.id ?? null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function runRecon() {
    if (!selectedTarget) return;
    setRunning(true);
    setError(null);
    try {
      const data = await api.runRecon(selectedTarget);
      setRecon(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recon failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <PageShell title="Recon Results" description="Enumerate subdomains, services, technologies, and hidden endpoints, then turn discovery data into testing momentum.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <SectionCard title="Execute Recon" eyebrow="Asset Discovery">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading targets…</p>
        ) : (
          <div className="flex flex-col gap-4 md:flex-row">
            <label className="sr-only" htmlFor="recon-target">Select target</label>
            <select id="recon-target" className="rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setSelectedTarget(Number(e.target.value))} value={selectedTarget ?? ""}>
              <option value="" disabled>Select target</option>
              {targets.map((target) => (
                <option key={target.id} value={target.id}>{target.program_name}</option>
              ))}
            </select>
            <button className="rounded-full bg-moss px-5 py-3 text-white disabled:opacity-50" onClick={runRecon} type="button" disabled={running || !selectedTarget}>
              {running ? "Running…" : "Run Recon Pass"}
            </button>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Assets" eyebrow="Normalized Output">
          <pre className="overflow-x-auto rounded-2xl bg-ink p-4 text-xs text-white">{JSON.stringify(recon?.assets ?? {}, null, 2)}</pre>
        </SectionCard>
        <SectionCard title="Notes" eyebrow="Recon Intelligence">
          <p className="text-sm text-ink/80">{recon?.notes ?? "Run a recon pass to populate data."}</p>
        </SectionCard>
      </div>
    </PageShell>
  );
}