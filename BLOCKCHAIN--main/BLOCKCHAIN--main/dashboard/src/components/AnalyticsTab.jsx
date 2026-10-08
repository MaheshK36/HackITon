import React from "react";
import { AlertTriangle, ShieldAlert, Cpu, Activity, CheckCircle2, User, Zap } from "lucide-react";
import { StatTile } from "./Shared.jsx";

export function AnalyticsTab({ summary = {}, anomalies = [] }) {
  return (
    <div className="space-y-6">
      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile
          icon={Activity}
          label="Total Access Events"
          value={summary.total_events || 0}
          sub="Logged & hashed"
          color="emerald"
        />
        <StatTile
          icon={ShieldAlert}
          label="Flagged Access Anomalies"
          value={summary.total_anomalies || anomalies.length || 0}
          sub="Multi-confirm gate (≥2 agreed)"
          color="rose"
        />
        <StatTile
          icon={User}
          label="Active Open Sessions"
          value={summary.active_sessions || 0}
          sub="Monitored real-time"
          color="amber"
        />
        <StatTile
          icon={Cpu}
          label="On-Chain Audit Records"
          value={summary.audit_records_onchain || 0}
          sub="AccessAuditLog.sol"
          color="indigo"
        />
      </div>

      {/* Detection Engine Status Banner */}
      <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Multi-Confirm Anomaly Detection Engine</h3>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Enforces Z-Score Frequency Spikes + Isolation Forest Outliers + Behavioral Rule Heuristics. Requires ≥2 algorithms to agree before flagging an access anomaly.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-3.5 py-2 rounded-xl shrink-0">
          <CheckCircle2 className="w-4 h-4" /> Multi-Confirm Gate: ACTIVE (≥ 80% Threshold)
        </div>
      </div>

      {/* Detected Access Anomalies Table */}
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 backdrop-blur-md overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" /> Flagged User Session Access Incidents
          </h3>
          <span className="text-xs font-mono text-slate-400">
            Showing {anomalies.length} incident cluster(s)
          </span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {anomalies && anomalies.length > 0 ? (
            anomalies.map((inc, i) => (
              <div key={inc.id || i} className="p-5 hover:bg-slate-800/30 transition-colors space-y-3 font-mono text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold text-[11px]">
                      {inc.id}
                    </span>
                    <span className="text-white font-bold text-sm">User: {inc.user_id}</span>
                  </div>

                  <div className="flex items-center gap-3 text-slate-400">
                    <span className="text-xs font-semibold text-amber-400">{inc.state}</span>
                    <span className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[10px] font-bold">
                      Confidence: {Math.round((inc.peak_confidence || 0.8) * 100)}%
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 font-sans text-sm">
                  {inc.description || `Access anomaly detected for user '${inc.user_id}'.`}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-slate-400 text-[11px] pt-1">
                  <span>Category: <strong className="text-slate-200">{inc.anomaly_type}</strong></span>
                  <span>Occurrences: <strong className="text-slate-200">{inc.occurrences || 1}</strong></span>
                  <span>Started: <strong className="text-slate-300">{inc.start_time}</strong></span>
                </div>
              </div>
            ))
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs font-mono">
              No software platform access anomalies detected. All logins operating within normal baseline.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
