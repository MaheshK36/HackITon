import React from "react";
import { Server, Code, Send, CheckCircle2 } from "lucide-react";

export function APITab() {
  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md">
        <h2 className="text-xl font-bold text-white flex items-center gap-2 font-sans">
          <Server className="w-5 h-5 text-indigo-400" /> Software Access Audit REST API Reference
        </h2>
        <p className="text-xs text-slate-400 mt-1 font-sans">
          Integrate your software platform authentication services to automatically record login/logout access events, query audit records, and fetch anomaly metrics.
        </p>
      </div>

      {/* Endpoint 1: POST /api/events */}
      <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">
            POST
          </span>
          <span className="text-white text-sm font-bold">/api/events</span>
          <span className="text-slate-400 text-xs">Ingest Login / Logout Event</span>
        </div>
        <p className="text-slate-300 font-sans">
          Submits a software access event to the pipeline. Automatically runs anomaly detection and records the SHA-256 hash on-chain.
        </p>
        <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-indigo-300 overflow-x-auto">
{`curl -X POST "http://localhost:8000/api/events" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "usr_alice",
    "event_type": "login",
    "ip_address": "192.168.1.105",
    "location": "US-East",
    "device_info": "Chrome/MacOS"
  }'`}
        </pre>
      </div>

      {/* Endpoint 2: GET /api/audit-logs */}
      <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-400 font-bold border border-indigo-500/30">
            GET
          </span>
          <span className="text-white text-sm font-bold">/api/audit-logs</span>
          <span className="text-slate-400 text-xs">Fetch Audit Event Stream</span>
        </div>
        <p className="text-slate-300 font-sans">
          Retrieves the immutable audit trail of captured login/logout access events with SHA-256 hashes.
        </p>
      </div>

      {/* Endpoint 3: GET /api/anomalies */}
      <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30">
            GET
          </span>
          <span className="text-white text-sm font-bold">/api/anomalies</span>
          <span className="text-slate-400 text-xs">Fetch Flagged Access Anomalies</span>
        </div>
        <p className="text-slate-300 font-sans">
          Returns access security anomalies flagged by the Multi-Confirm Gate (Z-Score + Isolation Forest + Rules).
        </p>
      </div>
    </div>
  );
}
