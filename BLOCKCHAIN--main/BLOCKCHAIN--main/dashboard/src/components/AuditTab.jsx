import React, { useState } from "react";
import { Shield, Key, Search, CheckCircle2, Lock, ExternalLink, RefreshCw } from "lucide-react";
import { EventRow, EXPLORER_BASE } from "./Shared.jsx";

export function AuditTab({ events = [], auditTrail = [] }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");

  const filteredEvents = events.filter((evt) => {
    const matchesSearch =
      (evt.user_id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (evt.event_id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (evt.ip_address || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === "all" || evt.event_type === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-indigo-400" /> Software Platform Access Audit Log
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time capture of user login & logout events. Every event is hashed (SHA-256) and submitted on-chain to AccessAuditLog.sol.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search user, IP, ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-white pl-9 pr-4 py-2 rounded-xl focus:outline-none focus:border-indigo-500 w-48 sm:w-64"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-white px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Events</option>
            <option value="login">Logins</option>
            <option value="logout">Logouts</option>
            <option value="failed_login">Failed Logins</option>
          </select>
        </div>
      </div>

      {/* Access Events Table */}
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden backdrop-blur-md shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">User ID</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">IP & Location</th>
                <th className="py-3 px-4">Device Info</th>
                <th className="py-3 px-4 text-right">Audit Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.length > 0 ? (
                filteredEvents.map((evt, idx) => <EventRow key={evt.event_id || idx} event={evt} />)
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 text-xs font-mono">
                    No access audit events matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* On-Chain Cryptographic SHA-256 Audit Trail Stream */}
      <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" /> Tamper-Evident SHA-256 On-Chain Audit Records
          </h3>
          <a
            href={EXPLORER_BASE}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-mono"
          >
            AccessAuditLog.sol <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        <div className="space-y-2 font-mono text-xs max-h-60 overflow-y-auto pr-2">
          {auditTrail && auditTrail.length > 0 ? (
            auditTrail.map((rec, i) => (
              <div
                key={i}
                className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-slate-300"
              >
                <div className="flex items-center gap-2 truncate">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="text-slate-400">Hash:</span>
                  <span className="text-emerald-300 font-semibold truncate max-w-[280px]">{rec.log_hash}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0 text-slate-400">
                  <span>User: <strong className="text-white">{rec.user_id}</strong></span>
                  <span>Type: <strong className="text-indigo-400">{rec.event_type}</strong></span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold uppercase border border-emerald-500/20">
                    {rec.audit_status || "Recorded"}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-xs py-4 text-center">
              No on-chain audit records captured yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
