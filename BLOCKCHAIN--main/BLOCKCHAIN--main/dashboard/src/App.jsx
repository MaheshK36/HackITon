import { useState, useEffect, useCallback } from "react";
import { Shield, Activity, Lock, RefreshCw, Server, AlertTriangle, CheckCircle2 } from "lucide-react";
import { PulseDot, EXPLORER_BASE } from "./components/Shared.jsx";
import { AuditTab } from "./components/AuditTab.jsx";
import { AnalyticsTab } from "./components/AnalyticsTab.jsx";
import { APITab } from "./components/APITab.jsx";

const SUMMARY_URL = "/api/analytics/summary";
const AUDIT_URL = "/api/audit-logs";
const ANOMALIES_URL = "/api/anomalies";
const FALLBACK_URL = "/dashboard.json";
const REFRESH_MS = 10_000;

export default function App() {
  const [data, setData] = useState({
    summary: {},
    events: [],
    anomalies: [],
    auditTrail: [],
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("audit");
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
        setLoading(false);
        return;
      }
      throw new Error("API unavailable");
    } catch {
      // Fallback to /dashboard.json static asset if API server is offline
      try {
        const fb = await fetch(FALLBACK_URL);
        if (fb.ok) {
          const json = await fb.json();
          setData({
            summary: json.summary || {},
            events: json.events || [],
            anomalies: json.anomalies || [],
            auditTrail: json.audit_trail || [],
          });
          setLastRefresh(new Date());
        }
      } catch (e2) {
        console.warn("Fallback fetch failed:", e2);
      } finally {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Background Decor */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 -right-40 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Navigation Topbar */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-2xl">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl text-white shadow-lg">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Access Audit & Anomaly Detection
                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  v2.0 System
                </span>
              </h1>
              <p className="text-xs text-slate-400 font-mono">
                Software Platform Login/Logout Blockchain Audit Trail
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300">
              <PulseDot />
              <span>Real-Time Monitor</span>
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

        {/* Tab Selector */}
        <nav className="flex items-center gap-2 p-1.5 bg-slate-900/60 rounded-xl border border-slate-800 backdrop-blur-md font-mono text-xs">
          <button
            onClick={() => setActiveTab("audit")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all font-semibold ${
              activeTab === "audit"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-white hover:bg-slate-800/50"
            }`}
          >
            <Lock className="w-4 h-4" /> Audit Log View
          </button>

          <button
            onClick={() => setActiveTab("analytics")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all font-semibold ${
              activeTab === "analytics"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-white hover:bg-slate-800/50"
            }`}
          >
            <Activity className="w-4 h-4" /> Anomaly & Analytics View
          </button>

          <button
            onClick={() => setActiveTab("api")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all font-semibold ${
              activeTab === "api"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-white hover:bg-slate-800/50"
            }`}
          >
            <Server className="w-4 h-4" /> REST API
          </button>
        </nav>

        {/* Main Tab Content */}
        <main>
          {activeTab === "audit" && (
            <AuditTab events={data.events} auditTrail={data.auditTrail} />
          )}

          {activeTab === "analytics" && (
            <AnalyticsTab summary={data.summary} anomalies={data.anomalies} />
          )}

          {activeTab === "api" && <APITab />}
        </main>
      </div>
    </div>
  );
}
