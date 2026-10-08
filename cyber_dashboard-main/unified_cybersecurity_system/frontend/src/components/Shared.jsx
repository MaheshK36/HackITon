import React from "react";
import { CheckCircle2, ShieldAlert } from "lucide-react";

export const EXPLORER_BASE = "https://sepolia.etherscan.io/address/0x742d35Cc6634C0532925a3b844Bc454e4438f44e";

export function PulseDot() {
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
    </span>
  );
}

export function StatTile({ icon: Icon, label, value, sub, color = "indigo" }) {
  const colorMap = {
    indigo: "border-indigo-500/30 text-indigo-400 bg-indigo-500/10",
    emerald: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
    rose: "border-rose-500/30 text-rose-400 bg-rose-500/10",
    amber: "border-amber-500/30 text-amber-400 bg-amber-500/10",
  };

  return (
    <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md flex items-center justify-between shadow-lg">
      <div className="space-y-1">
        <p className="text-xs text-slate-400 font-mono">{label}</p>
        <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
        {sub && <p className="text-[10px] text-slate-500 font-mono">{sub}</p>}
      </div>
      <div className={`p-3 rounded-xl border ${colorMap[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}

export function EventRow({ event }) {
  const isFailed = event.event_type === "failed_login";

  return (
    <tr className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors text-xs font-mono">
      <td className="py-3 px-4 text-indigo-300 font-semibold">{event.event_id || "EVT-1000"}</td>
      <td className="py-3 px-4 text-white font-bold">{event.user_id}</td>
      <td className="py-3 px-4">
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
            isFailed
              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
          }`}
        >
          {event.event_type}
        </span>
      </td>
      <td className="py-3 px-4 text-slate-400">{event.timestamp}</td>
      <td className="py-3 px-4 text-slate-300">{event.ip_address}</td>
      <td className="py-3 px-4 text-slate-400 truncate max-w-[150px]">{event.device_info || "Browser Session"}</td>
      <td className="py-3 px-4 text-right">
        <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5" /> SHA-256 Verified
        </span>
      </td>
    </tr>
  );
}
