import React, { useState } from "react";
import {
  Zap,
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Layers,
  ShieldAlert,
  Sliders,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Cpu,
  BarChart3
} from "lucide-react";

export function CyberSeerTab() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [steps, setSteps] = useState(5);
  const [selectedStep, setSelectedStep] = useState(1);
  const [showRaw, setShowRaw] = useState(false);

  const runForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/v1/forecast/propagation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ steps: steps }),
      });
      if (!r.ok) {
        throw new Error(`Server returned HTTP ${r.status}`);
      }
      const data = await r.json();
      if (data.status === "INSUFFICIENT_EVIDENCE") {
        setError(data.reason || "No telemetry-derived graph exists yet. Ingest telemetry or run a demo scenario first.");
        setResult(null);
      } else {
        setResult(data);
        setSelectedStep(1);
      }
    } catch (err) {
      setError(err.message || "Failed to execute propagation forecast");
    } finally {
      setLoading(false);
    }
  };

  const forecastSteps = result?.forecast_steps || [];
  const currentStepData = forecastSteps.find((s) => s.step === selectedStep) || forecastSteps[0];
  const previousStepData = selectedStep > 1 ? forecastSteps.find((s) => s.step === selectedStep - 1) : null;

  // Compute trend arrow
  const getTrend = (currentRisk, hostIp) => {
    if (!previousStepData) return <Minus className="w-3.5 h-3.5 text-slate-500 inline" />;
    const prevHost = previousStepData.hosts.find((h) => h.ip_address === hostIp);
    if (!prevHost) return <Minus className="w-3.5 h-3.5 text-slate-500 inline" />;
    const diff = currentRisk - prevHost.risk_score;
    if (diff > 0.01) return <TrendingUp className="w-3.5 h-3.5 text-red-400 inline" />;
    if (diff < -0.01) return <TrendingDown className="w-3.5 h-3.5 text-emerald-400 inline" />;
    return <Minus className="w-3.5 h-3.5 text-slate-400 inline" />;
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Method Provenance */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl backdrop-blur-md">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white">GNN Multi-Step Attack Propagation Forecast</h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Simulates dynamic threat momentum, future attack surface expansion, and host compromise trajectories across network topology.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Steps:</span>
            <select
              value={steps}
              onChange={(e) => setSteps(Number(e.target.value))}
              className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer"
            >
              <option value={3} className="bg-slate-900">3 Steps</option>
              <option value={5} className="bg-slate-900">5 Steps</option>
              <option value={10} className="bg-slate-900">10 Steps</option>
            </select>
          </div>

          <button
            onClick={runForecast}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 font-bold text-xs font-mono text-white shadow-lg shadow-indigo-600/30 transition-all"
          >
            <Zap className={`w-4 h-4 fill-current ${loading ? "animate-pulse" : ""}`} />
            {loading ? "Computing Forecast..." : "Run GNN Forecast"}
          </button>
        </div>
      </div>

      {/* Honest Method & Provenance Badge */}
      {result && (
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
              Method: {result.method || "GNN Forecaster"}
            </span>
            <span className="text-slate-400">
              Version: <strong className="text-slate-200">{result.model_version || "gnn-cyberseer-v1.0"}</strong>
            </span>
          </div>
          {result.evaluation_metrics && (
            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span>Test Acc: <strong className="text-emerald-400">{((result.evaluation_metrics.accuracy || 1) * 100).toFixed(1)}%</strong></span>
              <span>Macro F1: <strong className="text-emerald-400">{((result.evaluation_metrics.macro_f1 || 1) * 100).toFixed(1)}%</strong></span>
            </div>
          )}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-5 rounded-2xl bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs font-mono flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="block text-sm text-amber-300">Telemetry Required Before Forecasting</strong>
            <p>{error}</p>
            <p className="text-slate-400 pt-1">
              Switch to the <strong>Digital Twin Simulator</strong> tab and click <em>Run demo scenario</em>, or ingest flow events in <strong>Live Flow Ingestion</strong>.
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!result && !error && !loading && (
        <div className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-3 font-mono">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <Activity className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">No Forecast Requested Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click <strong>"Run GNN Forecast"</strong> above to compute multi-step risk diffusion and predicted host compromise states across the active digital twin.
          </p>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400">Blast Radius</span>
              <div className="text-xl font-bold font-mono text-red-400">
                {result.blast_radius_percent || 0}%
              </div>
              <span className="text-[10px] font-mono text-slate-500">Compromised / target hosts</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400">High Risk Nodes</span>
              <div className="text-xl font-bold font-mono text-amber-400">
                {result.high_risk_nodes || 0}
              </div>
              <span className="text-[10px] font-mono text-slate-500">Risk score ≥ 0.50</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400">Attack Momentum</span>
              <div className="text-xl font-bold font-mono text-indigo-400">
                +{result.attack_momentum || 0}
              </div>
              <span className="text-[10px] font-mono text-slate-500">Maximum risk delta</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400">Network Forecast Nodes</span>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {result.num_nodes || 0}
              </div>
              <span className="text-[10px] font-mono text-slate-500">Evaluated in topology</span>
            </div>
          </div>

          {/* Average Network Risk Line Chart (SVG) */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                Network Average Risk Across Forecast Steps (Line Chart)
              </span>
              <span className="text-slate-400">
                Horizon: {forecastSteps.length} Steps
              </span>
            </div>

            <div className="relative h-44 w-full pt-4">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 600 120" preserveAspectRatio="none">
                {/* Horizontal reference lines */}
                {[0.25, 0.5, 0.75, 1.0].map((level) => (
                  <line
                    key={level}
                    x1="40"
                    y1={110 - level * 100}
                    x2="590"
                    y2={110 - level * 100}
                    stroke="#1e293b"
                    strokeDasharray="4 4"
                    strokeWidth="1"
                  />
                ))}

                {/* Plot line */}
                {forecastSteps.length > 1 && (
                  <path
                    d={forecastSteps.reduce((acc, step, i) => {
                      const x = 50 + (i / (forecastSteps.length - 1)) * 530;
                      const y = 110 - (step.avg_network_risk || 0) * 100;
                      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
                    }, "")}
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="3"
                  />
                )}

                {/* Plot Dots */}
                {forecastSteps.map((step, i) => {
                  const x = 50 + (i / (Math.max(forecastSteps.length - 1, 1))) * 530;
                  const y = 110 - (step.avg_network_risk || 0) * 100;
                  const isCurrent = step.step === selectedStep;
                  return (
                    <g key={step.step} onClick={() => setSelectedStep(step.step)} className="cursor-pointer">
                      <circle
                        cx={x}
                        cy={y}
                        r={isCurrent ? "6" : "4"}
                        fill={isCurrent ? "#ef4444" : "#818cf8"}
                        stroke="#0f172a"
                        strokeWidth="2"
                      />
                      <text
                        x={x}
                        y={y - 10}
                        textAnchor="middle"
                        fill="#cbd5e1"
                        fontSize="10"
                        fontFamily="monospace"
                      >
                        {Math.round((step.avg_network_risk || 0) * 100)}%
                      </text>
                      <text
                        x={x}
                        y={125}
                        textAnchor="middle"
                        fill="#64748b"
                        fontSize="9"
                        fontFamily="monospace"
                      >
                        t+{step.step}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Step Selector Slider / Tabs */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-300">Select Forecast Step:</span>
              <span className="text-indigo-400 font-bold">Step {selectedStep} of {forecastSteps.length}</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {forecastSteps.map((s) => (
                <button
                  key={s.step}
                  onClick={() => setSelectedStep(s.step)}
                  className={`flex-1 min-w-[90px] py-2 rounded-lg font-bold transition-all text-center ${
                    selectedStep === s.step
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                      : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                  }`}
                >
                  Step {s.step} ({Math.round(s.avg_network_risk * 100)}%)
                </button>
              ))}
            </div>
          </div>

          {/* Host Risk Heatmap / Bar Visualizer & Table */}
          <div className="rounded-2xl bg-slate-900 border border-slate-800 shadow-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center font-mono text-xs">
              <span className="font-bold text-slate-200">
                Hosts Risk Progression at Step {selectedStep} ({currentStepData?.hosts?.length || 0} Nodes)
              </span>
              <span className="text-slate-400">
                Avg Network Risk: <strong className="text-indigo-400">{Math.round((currentStepData?.avg_network_risk || 0) * 100)}%</strong>
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Host</th>
                    <th className="py-3 px-4">IP Address</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Risk Bar / Heatmap</th>
                    <th className="py-3 px-4 text-right">Risk Score</th>
                    <th className="py-3 px-4 text-center">Trend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {currentStepData?.hosts?.map((host) => (
                    <tr key={host.ip_address} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-200">{host.hostname}</td>
                      <td className="py-3 px-4 text-slate-400">{host.ip_address}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            host.status === "compromised"
                              ? "bg-red-500/20 text-red-400 border border-red-500/30"
                              : host.status === "target"
                              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          }`}
                        >
                          {host.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 min-w-[160px]">
                        <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
                          <div
                            className={`h-full transition-all duration-300 ${
                              host.risk_score >= 0.5
                                ? "bg-red-500"
                                : host.risk_score >= 0.25
                                ? "bg-amber-500"
                                : "bg-emerald-500"
                            }`}
                            style={{ width: `${Math.round(host.risk_score * 100)}%` }}
                          />
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-200">
                        {Math.round(host.risk_score * 100)}%
                      </td>
                      <td className="py-3 px-4 text-center">
                        {getTrend(host.risk_score, host.ip_address)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* View Raw Response Toggle */}
          <div className="pt-2">
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="text-xs font-mono text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <ChevronRight className={`w-3.5 h-3.5 transition-transform ${showRaw ? "rotate-90" : ""}`} />
              {showRaw ? "Hide raw response" : "View raw response"}
            </button>
            {showRaw && (
              <pre className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 overflow-auto text-[11px] font-mono text-indigo-200">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
