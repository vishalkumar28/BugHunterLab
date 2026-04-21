"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { Finding, PocResponse } from "./types";

export function PocGeneratorView() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<number | null>(null);
  const [pocType, setPocType] = useState("curl");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .findings()
      .then((data) => {
        setFindings(data);
        setSelectedFinding(data[0]?.id ?? null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function generate() {
    if (!selectedFinding) return;
    setGenerating(true);
    setError(null);
    try {
      const response = await api.poc(selectedFinding, pocType);
      setContent(response.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <PageShell title="PoC Generator" description="Generate curl, browser, or Python proof-of-concept snippets directly from validated findings.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <SectionCard title="Generate Exploit Proof" eyebrow="PoC Output">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading findings…</p>
        ) : (
          <div className="flex flex-col gap-4 lg:flex-row">
            <div>
              <label className="sr-only" htmlFor="poc-finding">Select finding</label>
              <select id="poc-finding" className="rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setSelectedFinding(Number(e.target.value))} value={selectedFinding ?? ""}>
                <option value="" disabled>Select finding</option>
                {findings.map((finding) => (
                  <option key={finding.id} value={finding.id}>{finding.title}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="sr-only" htmlFor="poc-type">PoC type</label>
              <select id="poc-type" className="rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setPocType(e.target.value)} value={pocType}>
                <option value="curl">curl</option>
                <option value="browser">browser</option>
                <option value="python">python</option>
              </select>
            </div>
            <button className="rounded-full bg-ink px-5 py-3 text-white disabled:opacity-50" onClick={generate} type="button" disabled={generating || !selectedFinding}>
              {generating ? "Generating…" : "Generate"}
            </button>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Generated Snippet" eyebrow="Ready to Reproduce">
        <pre className="overflow-x-auto rounded-2xl bg-ink p-4 text-xs text-white">{content || "Generate a PoC from a stored finding."}</pre>
      </SectionCard>
    </PageShell>
  );
}