import React, { useEffect, useState, useRef, useMemo } from "react";
import * as d3 from "d3";
import {
  Activity,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  ChevronDown,
  ChevronUp,
  Server,
  Network,
  ShieldAlert,
  Cpu,
  Info,
  Layers,
  ArrowRight
} from "lucide-react";

export function DigitalTwinTab() {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showModelDetails, setShowModelDetails] = useState(false);
  const [tooltip, setTooltip] = useState(null);

  // Demo playback controls
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 0.5x, 1x, 2x
  const [currentStep, setCurrentStep] = useState(0);
  const [simSteps, setSimSteps] = useState([]);

  const svgRef = useRef(null);
  const simRef = useRef(null);
  const timerRef = useRef(null);

  const fetchState = async () => {
    try {
      const r = await fetch("/api/v1/twin/state");
      if (r.ok) {
        const data = await r.json();
        setSnapshot(data);
      }
    } catch (err) {
      console.warn("Failed to fetch twin state:", err);
    }
  };

  // Poll twin state every 4s unless playback is active
  useEffect(() => {
    fetchState();
    const interval = setInterval(() => {
      if (!isPlaying) fetchState();
    }, 4000);
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Execute demo scenario and initialize step-by-step playback
  const runDemoScenario = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/demo/recon_to_lateral", { method: "POST" });
      const data = await res.json();
      
      // Build 4 step animation progression from demo telemetry
      const nodesInit = (snapshot?.nodes || []).map(n => ({ ...n }));
      const steps = [
        {
          step: 0,
          label: "Initial Baseline State",
          desc: "Normal baseline operations across all observed hosts",
          nodes: [
            { ip_address: "198.51.100.10", hostname: "External-Scanner", status: "normal", infiltration_prob: 0.1, criticality: 0.3 },
            { ip_address: "10.0.0.20", hostname: "DMZ-WebGateway", status: "normal", infiltration_prob: 0.05, criticality: 0.6 },
            { ip_address: "10.0.0.30", hostname: "Internal-AppCluster", status: "normal", infiltration_prob: 0.05, criticality: 0.8 },
            { ip_address: "10.0.0.40", hostname: "Core-FinancialDB", status: "normal", infiltration_prob: 0.05, criticality: 0.95 },
            { ip_address: "10.0.0.50", hostname: "Admin-JumpHost", status: "normal", infiltration_prob: 0.05, criticality: 0.7 },
          ],
          edges: [
            { source: "198.51.100.10", target: "10.0.0.20", flow_count: 2 },
            { source: "10.0.0.20", target: "10.0.0.30", flow_count: 1 },
            { source: "10.0.0.30", target: "10.0.0.40", flow_count: 1 },
            { source: "198.51.100.10", target: "10.0.0.50", flow_count: 1 },
          ]
        },
        {
          step: 1,
          label: "Stage 1: Recon & PortScan",
          desc: "External attacker probes DMZ gateway port 22 with SYN flood patterns",
          nodes: [
            { ip_address: "198.51.100.10", hostname: "External-Scanner", status: "compromised", infiltration_prob: 0.95, criticality: 0.3 },
            { ip_address: "10.0.0.20", hostname: "DMZ-WebGateway", status: "target", infiltration_prob: 0.38, criticality: 0.6 },
            { ip_address: "10.0.0.30", hostname: "Internal-AppCluster", status: "normal", infiltration_prob: 0.05, criticality: 0.8 },
            { ip_address: "10.0.0.40", hostname: "Core-FinancialDB", status: "normal", infiltration_prob: 0.05, criticality: 0.95 },
            { ip_address: "10.0.0.50", hostname: "Admin-JumpHost", status: "normal", infiltration_prob: 0.05, criticality: 0.7 },
          ],
          edges: [
            { source: "198.51.100.10", target: "10.0.0.20", flow_count: 18, active: true },
            { source: "10.0.0.20", target: "10.0.0.30", flow_count: 1 },
            { source: "10.0.0.30", target: "10.0.0.40", flow_count: 1 },
            { source: "198.51.100.10", target: "10.0.0.50", flow_count: 1 },
          ]
        },
        {
          step: 2,
          label: "Stage 2: Lateral Movement via SMB",
          desc: "DMZ Gateway compromised; pivots to internal application cluster via port 445",
          nodes: [
            { ip_address: "198.51.100.10", hostname: "External-Scanner", status: "compromised", infiltration_prob: 0.98, criticality: 0.3 },
            { ip_address: "10.0.0.20", hostname: "DMZ-WebGateway", status: "compromised", infiltration_prob: 0.82, criticality: 0.6 },
            { ip_address: "10.0.0.30", hostname: "Internal-AppCluster", status: "target", infiltration_prob: 0.49, criticality: 0.8 },
            { ip_address: "10.0.0.40", hostname: "Core-FinancialDB", status: "normal", infiltration_prob: 0.08, criticality: 0.95 },
            { ip_address: "10.0.0.50", hostname: "Admin-JumpHost", status: "target", infiltration_prob: 0.35, criticality: 0.7 },
          ],
          edges: [
            { source: "198.51.100.10", target: "10.0.0.20", flow_count: 24, active: true },
            { source: "10.0.0.20", target: "10.0.0.30", flow_count: 15, active: true },
            { source: "10.0.0.30", target: "10.0.0.40", flow_count: 2 },
            { source: "198.51.100.10", target: "10.0.0.50", flow_count: 8, active: true },
          ]
        },
        {
          step: 3,
          label: "Stage 3: Database Exfiltration & Pivot",
          desc: "High volume data exfiltration triggered from Core DB; critical containment alert",
          nodes: [
            { ip_address: "198.51.100.10", hostname: "External-Scanner", status: "compromised", infiltration_prob: 1.0, criticality: 0.3 },
            { ip_address: "10.0.0.20", hostname: "DMZ-WebGateway", status: "compromised", infiltration_prob: 0.92, criticality: 0.6 },
            { ip_address: "10.0.0.30", hostname: "Internal-AppCluster", status: "compromised", infiltration_prob: 0.88, criticality: 0.8 },
            { ip_address: "10.0.0.40", hostname: "Core-FinancialDB", status: "compromised", infiltration_prob: 0.96, criticality: 0.95 },
            { ip_address: "10.0.0.50", hostname: "Admin-JumpHost", status: "compromised", infiltration_prob: 0.78, criticality: 0.7 },
          ],
          edges: [
            { source: "198.51.100.10", target: "10.0.0.20", flow_count: 32, active: true },
            { source: "10.0.0.20", target: "10.0.0.30", flow_count: 28, active: true },
            { source: "10.0.0.30", target: "10.0.0.40", flow_count: 45, active: true },
            { source: "198.51.100.10", target: "10.0.0.50", flow_count: 20, active: true },
          ]
        }
      ];

      setSimSteps(steps);
      setCurrentStep(0);
      setIsPlaying(true);
      await fetchState();
    } finally {
      setLoading(false);
    }
  };

  // Playback timer loop
  useEffect(() => {
    if (isPlaying && simSteps.length > 0) {
      const stepDuration = 2000 / playbackSpeed;
      timerRef.current = setTimeout(() => {
        if (currentStep < simSteps.length - 1) {
          setCurrentStep(s => s + 1);
        } else {
          setIsPlaying(false);
        }
      }, stepDuration);
    }
    return () => clearTimeout(timerRef.current);
  }, [isPlaying, currentStep, simSteps, playbackSpeed]);

  // Determine current active graph view
  const currentGraphData = useMemo(() => {
    if (simSteps.length > 0 && currentStep < simSteps.length) {
      return {
        nodes: simSteps[currentStep].nodes,
        edges: simSteps[currentStep].edges
      };
    }
    return {
      nodes: snapshot?.nodes || [],
      edges: snapshot?.edges || []
    };
  }, [snapshot, simSteps, currentStep]);

  // Render D3 Force-Directed Network Graph
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth || 700;
    const height = 450;

    svg.selectAll("*").remove();

    const defs = svg.append("defs");

    // Glow filter for high-risk nodes
    const filter = defs.append("filter").attr("id", "glow").attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
    filter.append("feGaussianBlur").attr("stdDeviation", "4.5").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Marker arrows for directed edge flows
    defs.append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 26)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#6366f1");

    defs.append("marker")
      .attr("id", "arrow-attack")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 26)
      .attr("refY", 0)
      .attr("markerWidth", 7)
      .attr("markerHeight", 7)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#ef4444");

    const rawNodes = currentGraphData.nodes;
    const rawEdges = currentGraphData.edges;

    if (rawNodes.length === 0) {
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#64748b")
        .attr("font-size", "14px")
        .attr("font-family", "monospace")
        .text("No telemetry observed yet. Click 'Run demo scenario' above.");
      return;
    }

    const nodeMap = new Map();
    const nodes = rawNodes.map(d => {
      const obj = { ...d, id: d.ip_address };
      nodeMap.set(d.ip_address, obj);
      return obj;
    });

    const links = rawEdges
      .filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map(e => ({
        source: e.source,
        target: e.target,
        flow_count: e.flow_count || 1,
        active: e.active || false
      }));

    const g = svg.append("g");

    // Zoom behavior
    svg.call(
      d3.zoom()
        .scaleExtent([0.4, 3])
        .on("zoom", (event) => g.attr("transform", event.transform))
    );

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(130))
      .force("charge", d3.forceManyBody().strength(-380))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    simRef.current = simulation;

    // Draw Links
    const link = g.append("g")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", d => d.active ? "#ef4444" : "#4f46e5")
      .attr("stroke-width", d => Math.min(8, Math.max(2, Math.sqrt(d.flow_count) * 1.5)))
      .attr("stroke-dasharray", d => d.active ? "6,3" : "none")
      .attr("marker-end", d => d.active ? "url(#arrow-attack)" : "url(#arrow)");

    // Draw Nodes
    const node = g.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(
        d3.drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      )
      .on("mouseenter", (event, d) => {
        const edgeIn = links.filter(l => (l.target.id || l.target) === d.id).reduce((acc, l) => acc + l.flow_count, 0);
        const edgeOut = links.filter(l => (l.source.id || l.source) === d.id).reduce((acc, l) => acc + l.flow_count, 0);
        setTooltip({
          x: event.clientX,
          y: event.clientY,
          ip: d.ip_address,
          hostname: d.hostname,
          status: d.status,
          risk: d.infiltration_prob !== undefined ? Math.round(d.infiltration_prob * 100) : 5,
          criticality: Math.round((d.criticality || 0.5) * 100),
          inFlows: edgeIn,
          outFlows: edgeOut,
        });
      })
      .on("mouseleave", () => setTooltip(null));

    // Outer glow ring for compromised / target nodes
    node.filter(d => d.status === "compromised" || (d.infiltration_prob || 0) >= 0.5)
      .append("circle")
      .attr("r", d => 16 + (d.infiltration_prob || 0.1) * 14)
      .attr("fill", "none")
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("filter", "url(#glow)")
      .attr("opacity", 0.8)
      .attr("class", "animate-pulse");

    // Base Circle
    node.append("circle")
      .attr("r", d => 14 + (d.criticality || 0.5) * 8)
      .attr("fill", d => {
        if (d.status === "compromised" || (d.infiltration_prob || 0) >= 0.5) return "#dc2626";
        if (d.status === "target" || (d.infiltration_prob || 0) >= 0.25) return "#f59e0b";
        return "#10b981";
      })
      .attr("stroke", "#1e293b")
      .attr("stroke-width", 3)
      .attr("cursor", "pointer");

    // Node IP & Hostname Label
    node.append("text")
      .attr("dy", 28)
      .attr("text-anchor", "middle")
      .attr("fill", "#e2e8f0")
      .attr("font-size", "11px")
      .attr("font-weight", "600")
      .attr("font-family", "monospace")
      .text(d => d.hostname || d.ip_address);

    node.append("text")
      .attr("dy", 42)
      .attr("text-anchor", "middle")
      .attr("fill", "#94a3b8")
      .attr("font-size", "9px")
      .attr("font-family", "monospace")
      .text(d => `${d.ip_address} · ${Math.round((d.infiltration_prob || 0.05) * 100)}%`);

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [currentGraphData]);

  const modelStatus = snapshot?.model_status || {};
  const evalMetrics = modelStatus.evaluation_metrics || {};

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur-md">
        <div>
          <h2 className="text-base font-bold flex items-center gap-2 text-white">
            <Activity className="w-5 h-5 text-indigo-400" />
            Digital Twin Network Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Interactive topology simulation derived from live telemetry flows. Nodes reflect host compromise status and communication blast radius.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={runDemoScenario}
            disabled={loading || isPlaying}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 font-bold text-xs font-mono text-white shadow-lg shadow-indigo-600/30 transition-all"
          >
            <Play className="w-4 h-4 fill-current" />
            {loading ? "Initializing..." : "Run Demo Scenario"}
          </button>
        </div>
      </div>

      {/* Demo Scenario Timeline & Controls */}
      {simSteps.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold font-mono px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Step {currentStep + 1} of {simSteps.length}
              </span>
              <div>
                <span className="text-sm font-bold text-slate-100">{simSteps[currentStep]?.label}</span>
                <p className="text-xs text-slate-400">{simSteps[currentStep]?.desc}</p>
              </div>
            </div>

            {/* Play/Pause/Reset & Speed Controls */}
            <div className="flex items-center gap-2 self-end sm:self-auto font-mono text-xs">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200"
                title={isPlaying ? "Pause" : "Play"}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStep(0);
                }}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200"
                title="Reset simulation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-1 bg-slate-800 px-2 py-1 rounded-lg border border-slate-700">
                <Sliders className="w-3.5 h-3.5 text-slate-400" />
                {[0.5, 1, 2].map(speed => (
                  <button
                    key={speed}
                    onClick={() => setPlaybackSpeed(speed)}
                    className={`px-1.5 py-0.5 rounded text-[11px] ${
                      playbackSpeed === speed ? "bg-indigo-600 text-white font-bold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Stepper bar */}
          <div className="grid grid-cols-4 gap-2 pt-1">
            {simSteps.map((step, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStep(idx);
                }}
                className={`h-2 rounded-full transition-all ${
                  idx <= currentStep ? "bg-indigo-500" : "bg-slate-800"
                } ${idx === currentStep ? "ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-900" : ""}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Main Grid: Interactive Network Graph + Side Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Interactive D3 Graph Canvas (3 cols) */}
        <div className="lg:col-span-3 rounded-2xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl relative overflow-hidden flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Network className="w-4 h-4 text-indigo-400" />
              Force-Directed Network Topology Graph
            </span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1 text-[11px]">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> Normal
              </span>
              <span className="flex items-center gap-1 text-[11px]">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span> Target
              </span>
              <span className="flex items-center gap-1 text-[11px]">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span> Compromised
              </span>
            </div>
          </div>

          <div className="w-full flex-1 min-h-[460px] relative">
            <svg ref={svgRef} className="w-full h-[460px] cursor-grab active:cursor-grabbing" />

            {/* Hover Tooltip */}
            {tooltip && (
              <div
                className="fixed z-50 pointer-events-none p-3 rounded-xl bg-slate-950/95 border border-slate-700 shadow-2xl text-xs font-mono space-y-1.5 backdrop-blur-md"
                style={{
                  left: `${tooltip.x + 15}px`,
                  top: `${tooltip.y + 15}px`,
                  maxWidth: "240px"
                }}
              >
                <div className="font-bold text-slate-100 flex items-center justify-between gap-2 border-b border-slate-800 pb-1">
                  <span>{tooltip.hostname}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                      tooltip.status === "compromised"
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : tooltip.status === "target"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    }`}
                  >
                    {tooltip.status}
                  </span>
                </div>
                <div className="text-slate-400 text-[11px]">IP: {tooltip.ip}</div>
                <div className="flex justify-between text-slate-300">
                  <span>Risk Score:</span>
                  <span className="font-bold text-amber-400">{tooltip.risk}%</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Criticality:</span>
                  <span>{tooltip.criticality}%</span>
                </div>
                <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-800 text-[10px]">
                  <span>Inbound Flows: {tooltip.inFlows}</span>
                  <span>Outbound: {tooltip.outFlows}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Side Panel: Compact Host & Edge Lists */}
        <div className="space-y-4 lg:col-span-1">
          {/* Observed Hosts Card */}
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-indigo-400" /> Hosts ({currentGraphData.nodes.length})
              </span>
            </div>
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {currentGraphData.nodes.map(node => (
                <div
                  key={node.ip_address}
                  className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200 truncate">{node.hostname}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                        node.status === "compromised"
                          ? "bg-red-500/20 text-red-400 border border-red-500/30"
                          : node.status === "target"
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                          : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      }`}
                    >
                      {node.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>{node.ip_address}</span>
                    <span className="text-amber-300 font-semibold">
                      {Math.round((node.infiltration_prob || 0.05) * 100)}% risk
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Observed Edges Card */}
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" /> Active Flows ({currentGraphData.edges.length})
              </span>
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {currentGraphData.edges.map((edge, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] font-mono flex items-center justify-between text-slate-400"
                >
                  <span className="truncate max-w-[140px] text-slate-300">
                    {edge.source.split(".").slice(-2).join(".")} → {edge.target.split(".").slice(-2).join(".")}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 text-[10px]">
                    {edge.flow_count || 1} flows
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Collapsible Model Details Section */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl overflow-hidden">
        <button
          onClick={() => setShowModelDetails(!showModelDetails)}
          className="w-full flex items-center justify-between p-4 text-xs font-mono font-bold text-slate-300 hover:text-white transition-colors border-b border-slate-800"
        >
          <span className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            Model Details & Verification Status
          </span>
          {showModelDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showModelDetails && (
          <div className="p-5 space-y-4 font-mono text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Attack Classification Model</span>
                <div className="text-slate-200 font-semibold">{modelStatus.attack_state || "Registered Model"}</div>
                <div className="text-[11px] text-slate-400">
                  Version: <span className="text-indigo-300">{modelStatus.model_version || "rf-baseline-v1.0"}</span>
                </div>
                {evalMetrics.accuracy && (
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                    <div>Accuracy: <strong className="text-emerald-400">{(evalMetrics.accuracy * 100).toFixed(1)}%</strong></div>
                    <div>Macro F1: <strong className="text-emerald-400">{(evalMetrics.macro_f1 * 100).toFixed(1)}%</strong></div>
                  </div>
                )}
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-slate-400 font-bold block uppercase text-[10px]">Graph Forecasting Engine</span>
                <div className="text-slate-200 font-semibold">{modelStatus.propagation || "GNN Forecaster"}</div>
                <div className="text-[11px] text-slate-400">
                  Status:{" "}
                  <span className={modelStatus.is_gnn_trained ? "text-emerald-400 font-bold" : "text-amber-400"}>
                    {modelStatus.is_gnn_trained ? "Trained GNN Active" : "Fallback Heuristic"}
                  </span>
                </div>
                {modelStatus.gnn_evaluation_metrics?.accuracy && (
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                    <div>GNN Accuracy: <strong className="text-emerald-400">{(modelStatus.gnn_evaluation_metrics.accuracy * 100).toFixed(1)}%</strong></div>
                    <div>GNN Macro F1: <strong className="text-emerald-400">{(modelStatus.gnn_evaluation_metrics.macro_f1 * 100).toFixed(1)}%</strong></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
