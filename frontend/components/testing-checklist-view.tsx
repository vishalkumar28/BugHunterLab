"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { ChecklistItem, ScopeTarget } from "./types";

export function TestingChecklistView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
  const [items, setItems] = useState<ChecklistItem[]>([]);
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

  async function loadChecklist() {
    if (!selectedTarget) return;
    setFetching(true);
    setError(null);
    try {
      const data = await api.checklists(selectedTarget);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load checklist");
    } finally {
      setFetching(false);
    }
  }

  return (
    <PageShell title="Testing Checklist" description="Generate endpoint-specific test plans so each route gets the bug classes that actually fit its behavior and risk profile.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <SectionCard title="Generate Checklist" eyebrow="Checklist Engine">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading targets…</p>
        ) : (
          <div className="flex flex-col gap-4 md:flex-row">
            <label className="sr-only" htmlFor="checklist-target">Select target</label>
            <select id="checklist-target" className="rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setSelectedTarget(Number(e.target.value))} value={selectedTarget ?? ""}>
              <option value="" disabled>Select target</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>{t.program_name}</option>
              ))}
            </select>
            <button className="rounded-full bg-moss px-5 py-3 text-white disabled:opacity-50" onClick={loadChecklist} type="button" disabled={fetching || !selectedTarget}>
              {fetching ? "Loading…" : "Generate Checklist"}
            </button>
          </div>
        )}
      </SectionCard>

      {items.length > 0 && (
        <SectionCard title={targets.find((t) => t.id === selectedTarget)?.program_name ?? "Checklist"} eyebrow="Results">
          <div className="space-y-4">
            {items.map((item, index) => (
              <div className="rounded-2xl border border-black/10 bg-white/70 p-5" key={`${item.method}-${item.endpoint}-${index}`}>
                <div className="flex items-center justify-between gap-4">
                  <strong className="font-mono text-sm">{item.endpoint}</strong>
                  <span className="rounded-full bg-ink px-3 py-1 text-xs text-white">{item.method}</span>
                </div>
                <ul className="mt-4 space-y-2 text-sm text-ink/80">
                  {item.checklist.map((check, i) => (
                    <li key={i}>- {check}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
    </PageShell>
  );
}