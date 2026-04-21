"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { VulnerabilityEntry } from "./types";

export function BugTestingGuideView() {
  const [entries, setEntries] = useState<Record<string, VulnerabilityEntry>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .vulnerabilities()
      .then(setEntries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageShell title="Bug Testing Guide" description="Study each vulnerability class with attack conditions, payload examples, manual steps, and signs of a real issue.">
      {loading && <p className="text-sm text-ink/60 animate-pulse">Loading vulnerability database…</p>}
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <div className="grid gap-6 xl:grid-cols-2">
        {Object.entries(entries).map(([name, entry]) => (
          <SectionCard key={name} title={name} eyebrow="Vulnerability Intelligence">
            <p className="text-sm text-ink/80">{entry.description}</p>
            <p className="mt-3 text-sm"><strong>Attack scenario:</strong> {entry.exploitation_method}</p>
            <p className="mt-3 text-sm"><strong>Impact:</strong> {entry.impact}</p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-rust">Manual testing steps</p>
                <ul className="mt-2 space-y-2 text-sm text-ink/80">
                  {entry.testing_checklist.map((step, i) => (
                    <li key={i}>- {step}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-rust">Example payloads</p>
                <ul className="mt-2 space-y-2 font-mono text-xs text-ink/80">
                  {entry.poc_examples.map((payload, i) => (
                    <li key={i}>{payload}</li>
                  ))}
                </ul>
              </div>
            </div>
          </SectionCard>
        ))}
      </div>
    </PageShell>
  );
}