"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { SectionCard } from "./section-card";
import type { LearningPhase } from "./types";

export function LearningStrip() {
  const [learning, setLearning] = useState<Record<string, LearningPhase>>({});
  const [loading, setLoading] = useState(true);

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    api
      .learning()
      .then(setLearning)
      .catch(() => setLearning({}))
      .finally(() => setLoading(false));
  }, []);

  if (!mounted) {
    return (
      <SectionCard title="Methodology Primer" eyebrow="Phases 1-4">
        <p className="text-sm text-ink/60 animate-pulse">Loading learning modules…</p>
      </SectionCard>
    );
  }

  return (
    <SectionCard title="Methodology Primer" eyebrow="Phases 1-4">
      <div className="grid gap-4 lg:grid-cols-4">
        {Object.entries(learning).map(([key, phase]) => (
          <div className="rounded-2xl border border-black/10 bg-white/70 p-4" key={key}>
            <h3 className="text-sm font-semibold text-rust">{phase.title}</h3>
            {phase.topics && (
              <ul className="mt-2 space-y-1 text-xs text-ink/75">
                {phase.topics.map((topic, i) => <li key={i}>• {topic}</li>)}
              </ul>
            )}
            {phase.tools && (
              <ul className="mt-2 space-y-1 text-xs text-ink/75">
                {phase.tools.map((tool, i) => <li key={i}>• {tool}</li>)}
              </ul>
            )}
            {phase.focus && (
              <ul className="mt-2 space-y-1 text-xs text-ink/75">
                {phase.focus.map((item, i) => <li key={i}>• {item}</li>)}
              </ul>
            )}
          </div>
        ))}
      </div>
    </SectionCard>
  );
}