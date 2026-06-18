"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "./api";
import { api } from "./api";
import { PageShell } from "./page-shell";
import { SectionCard } from "./section-card";
import type { ScopeTarget } from "./types";

interface Node { id: string; label: string; type: string; }
interface Edge { from: string; to: string; }
interface AttackSurface {
  target_id: number;
  target_name: string;
  status: string;
  total_assets: number;
  assets: {
    subdomains: string[];
    live_hosts: Array<{ id: number; url: string; is_alive: boolean; technologies: Array<{ name: string }> }>;
    technologies: string[];
  };
  attack_surface: { nodes: Node[]; edges: Edge[] };
}

export function AttackSurfaceMapView() {
  const [targets, setTargets] = useState<ScopeTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
  const [surface, setSurface] = useState<AttackSurface | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "subdomain" | "url">("all");

  // Load targets
  useEffect(() => {
    api
      .scopes()
      .then((scopes) => {
        setTargets(scopes);
        if (scopes[0]) {
          setSelectedTarget(scopes[0].id);
          loadSurface(scopes[0].id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function loadSurface(targetId: number) {
    setFetching(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/recon/${targetId}`);
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        setError(d.detail || `API error ${res.status}`);
        return;
      }
      const data: AttackSurface = await res.json();
      setSurface(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cannot reach API — is the backend running?");
    } finally {
      setFetching(false);
    }
  }

  const filteredNodes = surface?.attack_surface?.nodes?.filter(
    (n) => filter === "all" || n.type === filter
  ) ?? [];

  const nodeTypeColor = (type: string) => {
    switch (type) {
      case "url": return "bg-blue-100 text-blue-700 border-blue-200";
      case "subdomain": return "bg-green-100 text-green-700 border-green-200";
      default: return "bg-gray-100 text-gray-600 border-gray-200";
    }
  };

  return (
    <PageShell
      title="Attack Surface Map"
      description="Visualize how domains, hosts, and endpoints relate so you can move from wide recon to targeted testing paths."
    >
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

      <SectionCard title="Select Target" eyebrow="Surface Graph">
        {loading ? (
          <p className="text-sm text-ink/60 animate-pulse">Loading targets…</p>
        ) : targets.length === 0 ? (
          <p className="text-sm text-ink/60">
            No targets found. Add a target in <strong>Scope Analyzer</strong>, then run recon.
          </p>
        ) : (
          <div className="flex flex-col gap-4 md:flex-row md:items-center flex-wrap">
            <label className="sr-only" htmlFor="surface-target">Select target</label>
            <select
              id="surface-target"
              className="rounded-2xl border border-black/10 bg-white px-4 py-3"
              onChange={(e) => {
                const id = Number(e.target.value);
                setSelectedTarget(id);
                setSurface(null);
                loadSurface(id);
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
              onClick={() => selectedTarget && loadSurface(selectedTarget)}
              type="button"
              disabled={fetching || !selectedTarget}
            >
              {fetching ? "Loading…" : "Refresh Surface"}
            </button>
            {/* Filter buttons */}
            <div className="flex gap-2 ml-auto">
              {(["all", "subdomain", "url"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`rounded-full px-3 py-1.5 text-xs font-semibold border ${filter === f ? "bg-rust text-white border-rust" : "bg-white border-gray-200 text-gray-600"}`}
                >
                  {f === "all" ? "All" : f === "subdomain" ? "Subdomains" : "Live Hosts"}
                </button>
              ))}
            </div>
          </div>
        )}
      </SectionCard>

      {/* Stats bar */}
      {surface && (
        <div className="grid gap-4 sm:grid-cols-3">
          <SectionCard title={String(surface.assets.subdomains.length)} eyebrow="Subdomains">
            Discovered via subfinder
          </SectionCard>
          <SectionCard title={String(surface.assets.live_hosts.length)} eyebrow="Live Hosts">
            Confirmed alive via httpx
          </SectionCard>
          <SectionCard title={String(surface.assets.technologies.length)} eyebrow="Technologies">
            Fingerprinted by httpx
          </SectionCard>
        </div>
      )}

      {/* Node grid */}
      <SectionCard
        title={surface ? `${surface.target_name} — ${filteredNodes.length} node(s)` : "No target selected"}
        eyebrow="Nodes"
      >
        {!surface ? (
          <p className="text-sm text-ink/70">
            {fetching ? "Loading attack surface…" : 'Select a target and click "Refresh Surface". Run recon first if no assets appear.'}
          </p>
        ) : filteredNodes.length === 0 ? (
          <p className="text-sm text-ink/70">
            No assets found for this filter. Go to <strong>Recon Results</strong> and run a recon pass first.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 max-h-96 overflow-y-auto pr-1">
            {filteredNodes.map((node) => (
              <div
                key={node.id}
                className={`rounded-2xl border p-3 ${nodeTypeColor(node.type)}`}
              >
                <p className="text-xs uppercase tracking-[0.15em] opacity-60 mb-1">{node.type}</p>
                <p className="font-mono text-xs break-all">{node.label}</p>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Technologies */}
      {surface && surface.assets.technologies.length > 0 && (
        <SectionCard title="Detected Technologies" eyebrow="Stack Fingerprint">
          <div className="flex flex-wrap gap-2">
            {surface.assets.technologies.map((t, i) => (
              <span key={i} className="rounded-full bg-rust/10 px-3 py-1 text-xs font-semibold text-rust border border-rust/20">
                {t}
              </span>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Edges */}
      {surface && surface.attack_surface.edges.length > 0 && (
        <SectionCard title={`Relationships (${surface.attack_surface.edges.length})`} eyebrow="Edges">
          <pre className="overflow-x-auto rounded-2xl bg-ink p-4 text-xs text-white max-h-48">
            {JSON.stringify(surface.attack_surface.edges.slice(0, 20), null, 2)}
            {surface.attack_surface.edges.length > 20 && "\n… and more"}
          </pre>
        </SectionCard>
      )}
    </PageShell>
  );
}