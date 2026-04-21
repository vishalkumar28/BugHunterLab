"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { ReconRun, ScopeTarget } from "./types";

export function AttackSurfaceMapView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
  const [recon, setRecon] = useState<ReconRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .scopes()
      .then((scopes) => {
        setTargets(scopes);
        if (scopes[0]) setSelectedTarget(scopes[0].id);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function loadSurface() {
    if (!selectedTarget) return;
    setFetching(true);
    setError(null);
    try {
      const data = await api.runRecon(selectedTarget);
      setRecon(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load attack surface");
    } finally {
      setFetching(false);
    }
  }

  return (
    <PageShell title="Attack Surface Map" description="Visualize how domains, hosts, and endpoints relate so you can move from wide recon to targeted testing paths.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <SectionCard title="Select Target" eyebrow="Surface Graph">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading targets…</p>
        ) : (
          <div className="flex flex-col gap-4 md:flex-row">
            <label className="sr-only" htmlFor="surface-target">Select target</label>
            <select id="surface-target" className="rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setSelectedTarget(Number(e.target.value))} value={selectedTarget ?? ""}>
              <option value="" disabled>Select target</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>{t.program_name}</option>
              ))}
            </select>
            <button className="rounded-full bg-moss px-5 py-3 text-white disabled:opacity-50" onClick={loadSurface} type="button" disabled={fetching || !selectedTarget}>
              {fetching ? "Loading…" : "Map Attack Surface"}
            </button>
          </div>
        )}
      </SectionCard>

      <SectionCard title={targets.find((t) => t.id === selectedTarget)?.program_name ?? "No target selected"} eyebrow="Nodes">
        <div className="grid gap-4 md:grid-cols-2">
          {recon?.attack_surface?.nodes?.map((node) => (
            <div className="rounded-2xl border border-black/10 bg-white/70 p-4" key={node.id}>
              <p className="text-xs uppercase tracking-[0.2em] text-rust">{node.type}</p>
              <p className="mt-2 font-mono text-sm">{node.id}</p>
            </div>
          )) ?? <p className="text-sm text-ink/70">Click &quot;Map Attack Surface&quot; to render the map.</p>}
        </div>
      </SectionCard>

      <SectionCard title="Relationships" eyebrow="Edges">
        <pre className="overflow-x-auto rounded-2xl bg-ink p-4 text-xs text-white">{JSON.stringify(recon?.attack_surface?.edges ?? [], null, 2)}</pre>
      </SectionCard>
    </PageShell>
  );
}