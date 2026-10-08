import React, { useState } from "react";
import { Database, Send } from "lucide-react";

const initial = { source_ip: "198.51.100.10", destination_ip: "10.0.0.20", destination_port: 22, protocol: "tcp", packets: 2, bytes: 160, duration: 0.1 };

export function LiveIngestTab() {
  const [event, setEvent] = useState(initial);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      const payload = { ...event, destination_port: Number(event.destination_port), packets: Number(event.packets), bytes: Number(event.bytes), duration: Number(event.duration), metadata: { syn_flag_count: 1, port_scan: true } };
      const response = await fetch("/api/v1/flows/ingest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      setResult(await response.json());
    } catch (error) { setResult({ detail: error.message }); } finally { setLoading(false); }
  };
  return <div className="space-y-6">
    <div className="p-5 rounded-2xl bg-amber-950/30 border border-amber-500/30 text-sm"><strong>DEMO INPUT.</strong> This submits canonical synthetic telemetry through the same validation and decision pipeline as future adapters. Current inference is a transparent heuristic fallback, not a trained model.</div>
    <div className="grid lg:grid-cols-2 gap-6">
      <form onSubmit={submit} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="font-bold flex gap-2"><Database className="text-indigo-400"/> Canonical telemetry event</h2>
        {Object.entries(event).map(([key, value]) => <label className="block text-xs text-slate-400" key={key}>{key}<input value={value} onChange={(e) => setEvent({ ...event, [key]: e.target.value })} className="mt-1 w-full p-2 rounded bg-slate-950 border border-slate-700 text-white" /></label>)}
        <button disabled={loading} className="w-full p-3 rounded bg-indigo-600 font-bold"><Send className="inline w-4 mr-2"/>{loading ? "Processing" : "Validate and ingest"}</button>
      </form>
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800"><h2 className="font-bold mb-3">Decision record</h2><pre className="text-xs overflow-auto text-indigo-200">{result ? JSON.stringify(result, null, 2) : "No event submitted."}</pre></div>
    </div>
  </div>;
}
