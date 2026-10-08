import React, { useState, useEffect, useCallback } from "react";
import { Shield, Activity, Lock, RefreshCw, Zap, Database, Cpu, Link2 } from "lucide-react";

import { PulseDot } from "./components/Shared.jsx";
import { AuditTab } from "./components/AuditTab.jsx";
import { AnalyticsTab } from "./components/AnalyticsTab.jsx";
import { DigitalTwinTab } from "./components/DigitalTwinTab.jsx";
import { CyberSeerTab } from "./components/CyberSeerTab.jsx";
import { LiveIngestTab } from "./components/LiveIngestTab.jsx";

const SUMMARY_URL = "/api/analytics/summary";
const AUDIT_URL = "/api/audit-logs";
const ANOMALIES_URL = "/api/anomalies";
const REFRESH_MS = 10_000;

/* ── Reusable Iframe Embed Component ── */
function EmbeddedView({ src, title }) {
  return (
    <div className="w-full bg-slate-900/50 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 bg-slate-900/80 border-b border-slate-800">
        <Link2 className="w-3.5 h-3.5 text-indigo-400" />
        <span className="text-xs font-mono text-slate-400">{title}</span>
        <span className="text-[10px] font-mono text-slate-600 ml-auto">{src}</span>
        <a href={src} target="_blank" rel="noopener noreferrer"
          className="text-[10px] font-mono text-indigo-400 hover:text-indigo-300 transition-colors px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
          Open ↗
        </a>
      </div>
      <iframe
        src={src}
        title={title}
        className="w-full border-0"
        style={{ height: "calc(100vh - 220px)", minHeight: "600px" }}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  );
}

/* ── Tab Configuration ── */
const TABS = [
  { id: "twin", label: "Digital Twin Simulator", icon: Cpu },
  { id: "cyberseer", label: "GNN Attack Forecast", icon: Zap },
  { id: "audit", label: "Blockchain Audit Log", icon: Lock },
  { id: "analytics", label: "Anomaly Gate & Analytics", icon: Activity },
  { id: "ingest", label: "Live Flow Ingestion", icon: Database },
];

export default function App() {
  const [data, setData] = useState({
    summary: {},
    events: [],
    anomalies: [],
    auditTrail: [],
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("twin");
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const summaryRes = await fetch(SUMMARY_URL);
      const auditRes = await fetch(AUDIT_URL);
      const anomaliesRes = await fetch(ANOMALIES_URL);

      if (summaryRes.ok && auditRes.ok && anomaliesRes.ok) {
        const summary = await summaryRes.json();
        const auditData = await auditRes.json();
        const anomaliesData = await anomaliesRes.json();

        setData({
          summary: summary,
          events: auditData.audit_logs || [],
          anomalies: anomaliesData.anomalies || [],
          auditTrail: auditData.audit_logs || [],
        });
        setLastRefresh(new Date());
      }
    } catch (err) {
      console.warn("API fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Dynamic Background Glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 -right-40 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Navigation Topbar */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-2xl">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl text-white shadow-lg shadow-indigo-500/20">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2 font-heading">
                AI Cyber Defense Command Center
                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                  v2.0 Unified Architecture
                </span>
              </h1>
              <p className="text-xs text-slate-400 font-mono">
                Telemetry-derived graph • labelled prediction methods • local hash evidence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300">
              <PulseDot />
              <span>{data.summary.mode || "DEMO"} MODE — simulation/replay only unless a live adapter is configured</span>
            </div>

            <button
              onClick={fetchDashboardData}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
              title="Refresh Dashboard"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </header>

        {/* Navigation Tab Bar */}
        <nav className="flex items-center gap-2 p-1.5 bg-slate-900/60 rounded-xl border border-slate-800 backdrop-blur-md font-mono text-xs overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all font-semibold shrink-0 ${
                  activeTab === tab.id
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                <Icon className="w-4 h-4" /> {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Main Tab Content Viewport */}
        <main>
          {activeTab === "twin" && <DigitalTwinTab />}
          {activeTab === "cyberseer" && <CyberSeerTab />}
          {activeTab === "audit" && <AuditTab events={data.events} auditTrail={data.auditTrail} />}
          {activeTab === "analytics" && <AnalyticsTab summary={data.summary} anomalies={data.anomalies} />}
          {activeTab === "ingest" && <LiveIngestTab />}
        </main>
      </div>
    </div>
  );
}
