import React from "react";
import { Shield, Activity, Lock, AlertTriangle, CheckCircle2, User, Key, Server } from "lucide-react";

export const EXPLORER_BASE = "https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b";

export function PulseDot({ status = "active" }) {
  return (
    <span className="relative flex h-3 w-3 inline-flex mr-2">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
    </span>
  );
}

export function StatTile({ icon: Icon, label, value, sub, color = "emerald" }) {
  const colorMap = {
    emerald: "border-emerald-500/30 text-emerald-400 bg-emerald-950/20",
    amber: "border-amber-500/30 text-amber-400 bg-amber-950/20",
    rose: "border-rose-500/30 text-rose-400 bg-rose-950/20",
    indigo: "border-indigo-500/30 text-indigo-400 bg-indigo-950/20",
  };

  return (
    <div className={`p-4 rounded-xl border ${colorMap[color] || colorMap.emerald} backdrop-blur-md shadow-lg transition-all duration-200 hover:scale-[1.02]`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</span>
        {Icon && <Icon className="w-5 h-5 opacity-80" />}
      </div>
      <div className="text-2xl font-bold tracking-tight text-white">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1 font-mono">{sub}</div>}
    </div>
  );
}

export function EventRow({ event }) {
  const isAnomaly = event.is_anomaly || event.status === "failed";
  const eventTypeColors = {
    login: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    logout: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    failed_login: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  };

  return (
    <tr className={`border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors font-mono text-xs ${isAnomaly ? 'bg-rose-950/10' : ''}`}>
      <td className="py-3 px-4 text-slate-300 font-semibold">{event.event_id || "EVT-SYS"}</td>
      <td className="py-3 px-4 text-white font-medium flex items-center gap-2">
        <User className="w-3.5 h-3.5 text-slate-400" />
        {event.user_id}
      </td>
      <td className="py-3 px-4">
        <span className={`px-2.5 py-1 rounded-md text-[11px] font-semibold border ${eventTypeColors[event.event_type] || eventTypeColors.login}`}>
          {event.event_type}
        </span>
      </td>
      <td className="py-3 px-4 text-slate-400">{event.timestamp}</td>
      <td className="py-3 px-4 text-slate-300">{event.ip_address} ({event.location})</td>
      <td className="py-3 px-4 text-slate-400 truncate max-w-[140px]">{event.device_info}</td>
      <td className="py-3 px-4 text-right">
        {isAnomaly ? (
          <span className="inline-flex items-center text-rose-400 font-semibold gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> Flagged Anomaly
          </span>
        ) : (
          <span className="inline-flex items-center text-emerald-400 font-semibold gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Verified Normal
          </span>
        )}
      </td>
    </tr>
  );
}
