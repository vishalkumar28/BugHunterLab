"use client";

import { useState, useEffect, useRef } from "react";
import { Play, StopCircle, Activity, CheckCircle2, AlertCircle, Wifi, WifiOff } from "lucide-react";
import { SectionCard } from "./section-card";
import { API_BASE_URL } from "./api";

interface LogEntry {
  tool: string;
  status: "running" | "completed" | "error" | "timeout" | "skipped";
  count?: number;
  live_hosts?: number;
  assets_added?: number;
  reason?: string;
  error?: string;
  target_id?: number;
}

const ALLOWED_TOOLS = ["subfinder", "httpx", "nuclei", "nmap", "ffuf", "gau", "katana"] as const;

export function AutoScanner({ targetId }: { targetId: number }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [selectedTool, setSelectedTool] = useState("subfinder");
  const [customArgs, setCustomArgs] = useState("");
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Build WebSocket URL from the same host as the API
  const wsBase = API_BASE_URL.replace(/^https?/, "ws").replace("/api", "");

  useEffect(() => {
    if (!targetId) return;

    const ws = new WebSocket(`${wsBase}/ws/logs/${targetId}`);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as LogEntry;
        setLogs((prev) => [...prev, data]);
        if (data.status === "completed" || data.status === "error" || data.status === "timeout") {
          setIsScanning(false);
        }
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
      } catch {
        // Ignore unparseable messages
      }
    };

    return () => ws.close();
  }, [targetId, wsBase]);

  const startScan = async () => {
    if (!targetId) return;
    setIsScanning(true);
    setLogs([]);

    const argsArray = customArgs
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    try {
      const params = new URLSearchParams({
        target_id: String(targetId),
        tool: selectedTool,
      });
      const res = await fetch(`${API_BASE_URL}/jobs/start?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(argsArray),
      });

      if (res.ok) {
        const data = await res.json();
        setLastJobId(data.job_id);
        setLogs([{ tool: selectedTool, status: "running" }]);
      } else {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        setLogs([{ tool: selectedTool, status: "error", error: err.detail || "Failed to start scan" }]);
        setIsScanning(false);
      }
    } catch (e) {
      setLogs([{ tool: selectedTool, status: "error", error: "Cannot reach API — is the backend running?" }]);
      setIsScanning(false);
    }
  };

  const startFullRecon = async () => {
    if (!targetId) return;
    setIsScanning(true);
    setLogs([{ tool: "recon-pipeline", status: "running" }]);

    try {
      const res = await fetch(`${API_BASE_URL}/recon/${targetId}`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setLastJobId(data.job_id);
      } else {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        setLogs([{ tool: "recon-pipeline", status: "error", error: err.detail }]);
        setIsScanning(false);
      }
    } catch {
      setLogs([{ tool: "recon-pipeline", status: "error", error: "Cannot reach API" }]);
      setIsScanning(false);
    }
  };

  const stopScan = () => {
    setIsScanning(false);
    setLogs((prev) => [...prev, { tool: "system", status: "error", error: "Scan stopped by user" }]);
  };

  return (
    <SectionCard title="Auto Scanner" eyebrow="Pipeline">
      <div className="space-y-4">
        {/* Connection status */}
        <div className="flex items-center gap-2 text-xs">
          {isConnected ? (
            <><Wifi className="h-3 w-3 text-green-500" /><span className="text-green-600">Live log stream connected</span></>
          ) : (
            <><WifiOff className="h-3 w-3 text-gray-400" /><span className="text-gray-500">WebSocket not connected</span></>
          )}
          {lastJobId && (
            <span className="ml-auto text-gray-400">Job: {lastJobId.slice(0, 8)}…</span>
          )}
        </div>

        {/* Full recon pipeline */}
        <button
          onClick={isScanning ? stopScan : startFullRecon}
          disabled={!targetId}
          className="flex items-center gap-2 rounded-full bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
        >
          {isScanning ? <StopCircle className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          {isScanning ? "Stop" : "Full Recon (subfinder → httpx → save)"}
        </button>

        {/* Single tool runner */}
        <div className="flex gap-2 flex-wrap">
          <select
            value={selectedTool}
            onChange={(e) => setSelectedTool(e.target.value)}
            className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm"
          >
            {ALLOWED_TOOLS.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Extra args (e.g. -silent -o output.txt)"
            value={customArgs}
            onChange={(e) => setCustomArgs(e.target.value)}
            className="flex-1 min-w-0 rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-mono"
          />
          <button
            onClick={startScan}
            disabled={isScanning || !targetId}
            className="flex items-center gap-2 rounded-full border border-gray-300 px-4 py-1.5 text-sm font-semibold hover:bg-gray-50 disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5" />
            Run tool
          </button>
        </div>

        {/* Live log terminal */}
        <div className="rounded-xl bg-gray-900 text-gray-100 p-4 max-h-72 overflow-y-auto font-mono text-xs leading-relaxed">
          {logs.length === 0 ? (
            <p className="text-gray-500">Waiting for scan to start… select a target first.</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex gap-2 mb-1 items-start">
                {log.status === "running" && <Activity className="h-3.5 w-3.5 text-blue-400 mt-0.5 shrink-0" />}
                {log.status === "completed" && <CheckCircle2 className="h-3.5 w-3.5 text-green-400 mt-0.5 shrink-0" />}
                {(log.status === "error" || log.status === "timeout") && <AlertCircle className="h-3.5 w-3.5 text-red-400 mt-0.5 shrink-0" />}
                {log.status === "skipped" && <AlertCircle className="h-3.5 w-3.5 text-yellow-400 mt-0.5 shrink-0" />}
                <span className="text-blue-300">[{log.tool}]</span>
                <span className="opacity-80">{log.status}</span>
                {log.count !== undefined && <span className="text-green-300">· {log.count} subdomains</span>}
                {log.live_hosts !== undefined && <span className="text-green-300">· {log.live_hosts} live</span>}
                {log.assets_added !== undefined && <span className="text-green-300">· {log.assets_added} saved to DB</span>}
                {log.reason && <span className="text-yellow-300">· {log.reason}</span>}
                {log.error && <span className="text-red-300">· {log.error}</span>}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </SectionCard>
  );
}
