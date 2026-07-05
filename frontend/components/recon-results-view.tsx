"use client";

import { useEffect, useState, useRef } from "react";

import { api, API_BASE_URL } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { ScopeTarget } from "./types";

interface PortData {
  host: string;
  port: number;
  protocol: string;
  service: string | null;
}

interface FindingData {
  id: number;
  title: string;
  severity: string;
  vulnerability_class: string;
  description: string;
  evidence: string | null;
  created_at: string;
}

interface AssetData {
  target_id: number;
  target_name: string;
  status: string;
  assets: {
    subdomains: string[];
    live_hosts: Array<{
      id: number;
      url: string;
      is_alive: boolean;
      technologies: Array<{ name: string; version?: string; category?: string }>;
    }>;
    technologies: string[];
    ports: PortData[];
    endpoints: string[];
  };
  findings: FindingData[];
  attack_surface: {
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: Array<{ from: string; to: string }>;
  };
  total_assets: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-yellow-500 text-black",
  low: "bg-blue-500 text-white",
  info: "bg-gray-400 text-white",
};

export function ReconResultsView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
  const [recon, setRecon] = useState<AssetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Load scope targets
  useEffect(() => {
    api
      .scopes()
      .then((scopes) => {
        setTargets(scopes);
        if (scopes[0]) {
          setSelectedTarget(scopes[0].id);
          // Load existing recon results for first target
          loadResults(scopes[0].id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Connect WebSocket for live logs only when a scan is running
  useEffect(() => {
    if (!selectedTarget || !running) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    let mounted = true;
    let retryTimeout: ReturnType<typeof setTimeout>;
    let retryCount = 0;
    const MAX_RETRIES = 3;

    function connect() {
      if (!mounted) return;
      try {
        const wsBase = API_BASE_URL.replace(/^https?/, "ws").replace("/api", "");
        const ws = new WebSocket(`${wsBase}/ws/logs/${selectedTarget}`);
        wsRef.current = ws;

        ws.onclose = () => {
          if (mounted && running && retryCount < MAX_RETRIES) {
            retryCount++;
            retryTimeout = setTimeout(connect, Math.min(1000 * Math.pow(2, retryCount), 8000));
          }
        };

        ws.onerror = () => {
          // onerror is always followed by onclose
        };

        ws.onmessage = (event) => {
          if (!mounted) return;
          try {
            const data = JSON.parse(event.data);
            const parts = [`[${data.tool}] ${data.status}`];
            if (data.count) parts.push(`${data.count} subdomains`);
            if (data.resolved !== undefined) parts.push(`${data.resolved} resolved`);
            if (data.filtered_out !== undefined) parts.push(`${data.filtered_out} filtered out`);
            if (data.hosts_with_ports !== undefined) parts.push(`${data.hosts_with_ports} hosts, ${data.total_ports} ports`);
            if (data.live_hosts !== undefined) parts.push(`${data.live_hosts} live hosts`);
            if (data.endpoints !== undefined) parts.push(`${data.endpoints} endpoints`);
            if (data.historical_urls !== undefined) parts.push(`${data.historical_urls} historical URLs`);
            if (data.findings !== undefined) parts.push(`${data.findings} vulnerabilities found`);
            if (data.assets_added !== undefined) parts.push(`${data.assets_added} assets saved`);
            if (data.error) parts.push(data.error);

            const msg = parts.join(" — ");
            setLogs((prev) => [...prev, msg]);
            // When normalize completes, refresh results from DB
            if (data.tool === "normalize" && data.status === "completed") {
              setRunning(false);
              if (selectedTarget) loadResults(selectedTarget);
            }
          } catch {
            // ignore
          }
        };
      } catch {
        // WebSocket constructor can throw
      }
    }

    connect();

    return () => {
      mounted = false;
      clearTimeout(retryTimeout);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [selectedTarget, running]);

  async function loadResults(targetId: number) {
    try {
      const data = await fetch(`${API_BASE_URL}/recon/${targetId}`).then((r) => r.json());
      setRecon(data);
    } catch {
      // No results yet — that's fine
    }
  }

  async function runRecon() {
    if (!selectedTarget) return;
    setRunning(true);
    setError(null);
    setLogs([]);
    setRecon(null);

    try {
      const res = await fetch(`${API_BASE_URL}/recon/${selectedTarget}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Recon failed to start");
        setRunning(false);
        return;
      }
      setJobId(data.job_id);
      setLogs([
        `Recon pipeline started — job ${data.job_id?.slice(0, 8)}…`,
        `Pipeline: ${data.pipeline || "subfinder → naabu → httpx → normalize"}`,
        `Scanning: ${data.domains?.join(", ") || "domains"}`,
      ]);
      // Results will auto-refresh when WebSocket receives "normalize completed"
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cannot reach API");
      setRunning(false);
    }
  }

  async function clearRecon() {
    if (!selectedTarget) return;
    try {
      await api.clearRecon(selectedTarget);
      setRecon(null);
      setLogs([]);
      setJobId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear results");
    }
  }

  return (
    <PageShell
      title="Recon Results"
      description="Recon pipeline: subdomain enumeration, port scanning, and HTTP probing."
    >
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <SectionCard title="Execute Recon" eyebrow="Recon Pipeline">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading targets…</p>
        ) : targets.length === 0 ? (
          <p className="text-sm text-ink/60">No targets yet — go to Scope Analyzer and add a program first.</p>
        ) : (
          <div className="flex flex-col gap-4 md:flex-row md:items-center flex-wrap">
            <label className="sr-only" htmlFor="recon-target">Select target</label>
            <select
              id="recon-target"
              className="rounded-2xl border border-black/10 bg-white px-4 py-3"
              onChange={(e) => {
                const id = Number(e.target.value);
                setSelectedTarget(id);
                setRecon(null);
                setLogs([]);
                loadResults(id);
              }}
              value={selectedTarget ?? ""}
            >
              <option value="" disabled>Select target</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>{t.program_name}</option>
              ))}
            </select>

            <button
              className="rounded-full bg-moss px-5 py-3 text-white disabled:opacity-50"
              onClick={runRecon}
              type="button"
              disabled={running || !selectedTarget}
            >
              {running ? "Running recon pipeline…" : "Run Recon"}
            </button>

            {recon && recon.total_assets > 0 && (
              <button
                className="rounded-full border border-red-300 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
                onClick={clearRecon}
                type="button"
              >
                Clear & Rescan
              </button>
            )}
          </div>
        )}
      </SectionCard>

      {/* Live log output */}
      {logs.length > 0 && (
        <SectionCard title="Live Pipeline Logs" eyebrow="Stream">
          <div className="rounded-xl bg-gray-900 p-4 font-mono text-xs text-gray-100 max-h-64 overflow-y-auto space-y-1">
            {logs.map((log, i) => (
              <div key={i} className="text-green-300"> {log}</div>
            ))}
            {running && <div className="animate-pulse text-yellow-300"> Pipeline running… this may take several minutes.</div>}
          </div>
        </SectionCard>
      )}



      {/* Results grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Subdomains */}
        <SectionCard title={`Subdomains (${recon?.assets?.subdomains?.length ?? 0})`} eyebrow="Normalized Output">
          {!recon || recon.assets.subdomains.length === 0 ? (
            <p className="text-sm text-ink/60">Run a recon pass to discover subdomains.</p>
          ) : (
            <ul className="space-y-1 max-h-64 overflow-y-auto font-mono text-xs">
              {recon.assets.subdomains.map((s, i) => (
                <li key={i} className="text-ink/80">· {s}</li>
              ))}
            </ul>
          )}
        </SectionCard>

        {/* Technologies */}
        <SectionCard title={`Technologies (${recon?.assets?.technologies?.length ?? 0})`} eyebrow="Tech Stack">
          {!recon || recon.assets.technologies.length === 0 ? (
            <p className="text-sm text-ink/60">Technologies detected by httpx will appear here.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {recon.assets.technologies.map((t, i) => (
                <span key={i} className="rounded-full bg-rust/10 px-3 py-1 text-xs font-semibold text-rust">{t}</span>
              ))}
            </div>
          )}
        </SectionCard>

        {/* Open Ports */}
        <SectionCard title={`Open Ports (${recon?.assets?.ports?.length ?? 0})`} eyebrow="Naabu Scan">
          {!recon || !recon.assets.ports || recon.assets.ports.length === 0 ? (
            <p className="text-sm text-ink/60">Ports discovered by naabu will appear here.</p>
          ) : (
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-ink/50 border-b border-black/10">
                    <th className="pb-2 pr-4">Host</th>
                    <th className="pb-2 pr-4">Port</th>
                    <th className="pb-2">Protocol</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {recon.assets.ports.map((p, i) => (
                    <tr key={i} className="border-b border-black/5">
                      <td className="py-1.5 pr-4 text-ink/80">{p.host}</td>
                      <td className="py-1.5 pr-4 font-bold text-rust">{p.port}</td>
                      <td className="py-1.5 text-ink/60">{p.protocol}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>



        {/* Live hosts */}
        <SectionCard
          title={`Live Hosts (${recon?.assets?.live_hosts?.length ?? 0})`}
          eyebrow="HTTP Alive"
        >
          {!recon || recon.assets.live_hosts.length === 0 ? (
            <p className="text-sm text-ink/60">Live hosts probed by httpx will appear here.</p>
          ) : (
            <ul className="space-y-2 max-h-64 overflow-y-auto">
              {recon.assets.live_hosts.map((h) => (
                <li key={h.id} className="rounded-xl border border-black/10 bg-white/60 px-4 py-2">
                  <a href={h.url} target="_blank" rel="noreferrer" className="font-mono text-xs text-blue-600 hover:underline">
                    {h.url}
                  </a>
                  {h.technologies.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {h.technologies.map((t, i) => (
                        <span key={i} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{t.name}</span>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        {/* Stats */}
        <SectionCard title="Summary" eyebrow="Recon Intelligence">
          {!recon ? (
            <p className="text-sm text-ink/80">Run a recon pass to populate data.</p>
          ) : (
            <div className="space-y-2 text-sm">
              <p><strong>Target:</strong> {recon.target_name}</p>
              <p><strong>Status:</strong> {recon.status}</p>
              <p><strong>Total Assets:</strong> {recon.total_assets}</p>
              <p><strong>Subdomains:</strong> {recon.assets.subdomains.length}</p>
              <p><strong>Live Hosts:</strong> {recon.assets.live_hosts.length}</p>
              <p><strong>Open Ports:</strong> {recon.assets.ports?.length ?? 0}</p>
              <p><strong>Technologies:</strong> {recon.assets.technologies.length}</p>
              {jobId && <p className="text-xs text-gray-400"><strong>Job ID:</strong> {jobId}</p>}
            </div>
          )}
        </SectionCard>
      </div>
    </PageShell>
  );
}