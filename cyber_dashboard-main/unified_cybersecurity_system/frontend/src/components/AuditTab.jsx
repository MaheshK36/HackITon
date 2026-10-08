import React, { useState } from "react";
import { Shield, Search, Lock, ExternalLink, CheckCircle2, AlertOctagon } from "lucide-react";
import { EventRow, EXPLORER_BASE } from "./Shared.jsx";

export function AuditTab({ events = [], auditTrail = [], onVerifyHash }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [verifyId, setVerifyId] = useState("");
  const [verifyHashVal, setVerifyHashVal] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);

  const filteredEvents = events.filter((evt) => {
    const matchesSearch =
      (evt.user_id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (evt.event_id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (evt.ip_address || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === "all" || evt.event_type === filterType;
    return matchesSearch && matchesFilter;
  });

  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    if (!verifyHashVal) return;
    try {
      const res = await fetch("/api/verify-hash", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: verifyId, hash: verifyHashVal }),
      });
      const json = await res.json();
      setVerifyResult(json);
    } catch (err) {
      setVerifyResult({ verified: false, error: err.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-heading">
            <Lock className="w-5 h-5 text-indigo-400" /> Platform Access Audit Stream
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Every login/logout access event is hashed (SHA-256) and verified against on-chain smart contract ledger.
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
              className="bg-slate-950 border border-slate-800 text-xs text-white pl-9 pr-4 py-2 rounded-xl focus:outline-none focus:border-indigo-500 w-48 sm:w-64 font-mono"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-white px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="all">All Events</option>
            <option value="login">Logins</option>
            <option value="logout">Logouts</option>
            <option value="failed_login">Failed Logins</option>
          </select>
        </div>
      </div>

      {/* Verification Tool */}
      <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 font-heading">
          <Shield className="w-4 h-4 text-indigo-400" /> Verify SHA-256 On-Chain Record Integrity
        </h3>

        <form onSubmit={handleVerifySubmit} className="flex flex-col sm:flex-row items-center gap-3 font-mono text-xs">
          <input
            type="text"
            placeholder="Event ID (e.g. EVT-1001)"
            value={verifyId}
            onChange={(e) => setVerifyId(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-white px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500 w-full sm:w-48"
          />
          <input
            type="text"
            placeholder="SHA-256 Hash value to verify..."
            value={verifyHashVal}
            onChange={(e) => setVerifyHashVal(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-white px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500 flex-1 w-full"
          />
          <button
            type="submit"
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shrink-0 w-full sm:w-auto"
          >
            Verify Integrity
          </button>
        </form>

        {verifyResult && (
          <div
            className={`p-3 rounded-xl border text-xs font-mono flex items-center justify-between ${
              verifyResult.verified
                ? "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"
                : "bg-rose-950/40 border-rose-500/30 text-rose-300"
            }`}
          >
            <div className="flex items-center gap-2">
              {verifyResult.verified ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertOctagon className="w-4 h-4 text-rose-400" />}
              <span>{verifyResult.status || verifyResult.error}</span>
            </div>
            {verifyResult.user_id && <span>User: <strong>{verifyResult.user_id}</strong></span>}
          </div>
        )}
      </div>

      {/* Access Log Table */}
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden backdrop-blur-md shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 text-xs font-semibold uppercase tracking-wider font-mono">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">User ID</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">IP & Subnet</th>
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
    </div>
  );
}
