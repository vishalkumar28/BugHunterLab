"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import { AutoScanner } from "./auto-scanner";
import type { DashboardData } from "./types";

export function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    api
      .dashboard()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Prevent hydration mismatch by avoiding conditional server/client mismatches
  if (!mounted) {
    return (
      <PageShell title="From Scope to Submission" description="Guide bug bounty work through reconnaissance, vulnerability research, evidence capture, and report generation in one local platform.">
        <p className="text-sm text-ink/60 animate-pulse">Loading dashboard…</p>
      </PageShell>
    );
  }

  return (
    <PageShell title="From Scope to Submission" description="Guide bug bounty work through reconnaissance, vulnerability research, evidence capture, and report generation in one local platform.">
      {error && <p className="text-sm text-red-600" role="alert">Failed to load dashboard: {error}</p>}

      {data && (
        <>
          <div className="grid gap-6 lg:grid-cols-3">
            <SectionCard title={String(data.target_count)} eyebrow="Tracked Targets">
              Scope analyzer records target breadth, API presence, and workflow difficulty.
            </SectionCard>
            <SectionCard title={String(data.finding_count)} eyebrow="Recorded Findings">
              Proof, reproduction steps, and severity stay attached to each issue.
            </SectionCard>
            <SectionCard title="Local-First" eyebrow="Tooling">
              Tool wrappers execute real binaries when present and degrade safely when not installed.
            </SectionCard>
          </div>

          <SectionCard title="Workflow Phases" eyebrow="Methodology Engine">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {data.phases.map((phase) => (
                <div className="rounded-2xl border border-black/10 bg-sand/70 p-4" key={phase.id}>
                  <p className="text-sm font-semibold text-rust">Phase {phase.id}</p>
                  <h3 className="mt-2 font-display text-xl">{phase.name}</h3>
                  <p className="mt-2 text-sm text-ink/75">{phase.description}</p>
                </div>
              ))}
            </div>
          </SectionCard>

          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard title="Recent Targets" eyebrow="Scope">
              <div className="space-y-3">
                {data.recent_targets.length ? data.recent_targets.map((target) => (
                  <div className="rounded-2xl border border-black/10 bg-white/60 p-4" key={target.id}>
                    <div className="flex items-center justify-between gap-4">
                      <strong>{target.program_name}</strong>
                      <span className="rounded-full bg-moss px-3 py-1 text-xs text-white">{target.target_level}</span>
                    </div>
                    <p className="mt-2 text-sm text-ink/75">{target.summary}</p>
                  </div>
                )) : <p className="text-sm text-ink/70">No targets yet. Start in Scope Analyzer.</p>}
              </div>
            </SectionCard>

            <AutoScanner targetId={data.recent_targets?.[0]?.id || 1} />

            <SectionCard title="Recent Findings" eyebrow="Validation">
              <div className="space-y-3">
                {data.recent_findings.length ? data.recent_findings.map((finding) => (
                  <div className="rounded-2xl border border-black/10 bg-white/60 p-4" key={finding.id}>
                    <div className="flex items-center justify-between gap-4">
                      <strong>{finding.title}</strong>
                      <span className="rounded-full bg-rust px-3 py-1 text-xs text-white">{finding.severity}</span>
                    </div>
                    <p className="mt-2 text-sm text-ink/75">{finding.vulnerability_class}</p>
                  </div>
                )) : <p className="text-sm text-ink/70">No findings recorded yet.</p>}
              </div>
            </SectionCard>
          </div>
        </>
      )}
    </PageShell>
  );
}