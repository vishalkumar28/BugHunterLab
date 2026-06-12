"use client";

import { useState, useEffect } from "react";
import { io, Socket } from "socket.io-client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Play, Activity, CheckCircle2, AlertCircle } from "lucide-react";
import { SectionCard } from "./section-card";

export function AutoScanner({ targetId }: { targetId: number }) {
  const [logs, setLogs] = useState<any[]>([]);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    // We connect to the FastAPI WebSocket endpoint
    // In a real app we would get the host dynamically
    const ws = new WebSocket(`ws://localhost:8000/ws/logs/${targetId}`);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [...prev, data]);
      } catch (e) {
        console.error("Failed to parse log", event.data);
      }
    };

    return () => {
      ws.close();
    };
  }, [targetId]);

  const startScan = async () => {
    // We would use an actual fetch or axios call here
    // POST /api/jobs/start
    const res = await fetch(`http://localhost:8000/api/jobs/start?target_id=${targetId}&tool=subfinder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(["-d", "example.com"])
    });
    if (res.ok) {
      console.log("Scan started");
    }
  };

  return (
    <SectionCard title="Auto Scanner" eyebrow="Pipeline">
      <div className="space-y-4">
        <button
          onClick={startScan}
          className="flex items-center gap-2 rounded-full bg-rust px-4 py-2 text-sm font-semibold text-white hover:bg-rust/90"
        >
          <Play className="h-4 w-4" />
          Full Auto Scan
        </button>

        <div className="mt-4 rounded-xl bg-ink text-sand p-4 max-h-64 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <p className="text-sand/50">Waiting for scan to start...</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex gap-2 mb-1">
                {log.status === "running" && <Activity className="h-4 w-4 text-blue-400" />}
                {log.status === "completed" && <CheckCircle2 className="h-4 w-4 text-moss" />}
                {log.status === "error" && <AlertCircle className="h-4 w-4 text-rust" />}
                <span>[{log.tool}]</span>
                <span className="opacity-80">{log.status}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </SectionCard>
  );
}
