"use client";

import { useEffect, useState } from "react";

import { api, API_BASE_URL } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { Finding, ReportResponse } from "./types";

export function ReportBuilderView() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<number | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<{ status: string; platform: string; external_id: string } | null>(null);

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

  async function buildReport() {
    if (!selectedFinding) return;
    setBuilding(true);
    setError(null);
    setSubmissionResult(null);
    try {
      const response = await api.report(selectedFinding);
      setReport(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report generation failed");
    } finally {
      setBuilding(false);
    }
  }

  async function submitReport() {
    if (!selectedFinding) return;
    setSubmitting(true);
    setError(null);
    setSubmissionResult(null);
    try {
      const response = await api.submitReport(selectedFinding, "hackerone");
      setSubmissionResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell title="Report Builder" description="Compile bug bounty reports with summary, impact, reproduction steps, proof, and remediation advice.">
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      {submissionResult && (
        <p className="text-sm text-green-700 bg-green-50 p-4 rounded-xl border border-green-200" role="alert">
          Successfully submitted to {submissionResult.platform}. External ID: {submissionResult.external_id}
        </p>
      )}

      <SectionCard title="Build Disclosure" eyebrow="Report Generation">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading findings…</p>
        ) : (
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
            <label className="sr-only" htmlFor="report-finding">Select finding</label>
            <select id="report-finding" className="rounded-2xl border border-black/10 bg-white px-4 py-3" onChange={(e) => setSelectedFinding(Number(e.target.value))} value={selectedFinding ?? ""}>
              <option value="" disabled>Select finding</option>
              {findings.map((finding) => (
                <option key={finding.id} value={finding.id}>{finding.title}</option>
              ))}
            </select>
            <button className="rounded-full bg-moss px-5 py-3 text-white disabled:opacity-50" onClick={buildReport} type="button" disabled={building || !selectedFinding}>
              {building ? "Generating…" : "Generate Report"}
            </button>
            {selectedFinding ? (
              <a className="rounded-full border border-black/10 bg-white px-5 py-3 text-sm transition hover:bg-sand" href={`${API_BASE_URL}/report/${selectedFinding}/pdf`} target="_blank" rel="noopener noreferrer">
                Open PDF
              </a>
            ) : null}
            <button className="rounded-full bg-[#3e3c38] px-5 py-3 text-white text-sm transition hover:bg-black disabled:opacity-50" onClick={submitReport} type="button" disabled={submitting || !selectedFinding}>
              {submitting ? "Submitting..." : "Submit to HackerOne"}
            </button>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Markdown" eyebrow="Export">
          <pre className="overflow-x-auto rounded-2xl bg-ink p-4 text-xs text-white">{report?.markdown ?? "Generate a report to preview Markdown output."}</pre>
        </SectionCard>
        <SectionCard title="Plain Text" eyebrow="Export">
          <pre className="overflow-x-auto rounded-2xl bg-ink p-4 text-xs text-white">{report?.plain_text ?? "Plain text export will appear here."}</pre>
          {report?.pdf_path ? <p className="mt-4 text-xs text-ink/70">Saved PDF path: {report.pdf_path}</p> : null}
        </SectionCard>
      </div>
    </PageShell>
  );
}