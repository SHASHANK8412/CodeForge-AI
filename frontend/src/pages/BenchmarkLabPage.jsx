import React, { useState, useEffect, useRef } from "react";
import {
  FaFlask,
  FaPlay,
  FaCheckCircle,
  FaTimesCircle,
  FaChartLine,
  FaHistory,
  FaLightbulb,
  FaCode,
  FaSlidersH,
  FaSyncAlt,
  FaSpinner,
  FaMicrochip,
  FaStop,
  FaTrophy,
  FaExclamationTriangle,
  FaClock,
  FaCogs,
  FaLayerGroup,
  FaCopy,
  FaCheck,
  FaFileAlt
} from "react-icons/fa";
import {
  fetchBenchmarkTasks,
  fetchBenchmarkModels,
  fetchBenchmarkConfigurations,
  startBenchmarkRun,
  fetchBenchmarkRuns,
  fetchBenchmarkRun,
  cancelBenchmarkRun,
  fetchMarkdownReport,
  fetchArtifactContent,
  fetchBenchmarkRecommendations,
} from "../services/benchmarkLabApi";

export default function BenchmarkLabPage() {
  const [activeTab, setActiveTab] = useState("setup"); // setup, monitor, results, artifacts, history
  const [tasks, setTasks] = useState([]);
  const [models, setModels] = useState([]);
  const [configurations, setConfigurations] = useState([]);
  const [historicalRuns, setHistoricalRuns] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Setup form states
  const [selectedTaskIds, setSelectedTaskIds] = useState([]);
  const [selectedConfigIds, setSelectedConfigIds] = useState([]);
  const [priority, setPriority] = useState("BEST_OVERALL");
  const [repeatedRuns, setRepeatedRuns] = useState(1);
  const [launching, setLaunching] = useState(false);

  // Active run monitoring
  const [activeRunId, setActiveRunId] = useState(null);
  const [activeRun, setActiveRun] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollTimerRef = useRef(null);

  // Inspection & Artifacts
  const [selectedResult, setSelectedResult] = useState(null);
  const [artifactContent, setArtifactContent] = useState("");
  const [loadingArtifact, setLoadingArtifact] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [markdownReport, setMarkdownReport] = useState("");

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [tList, mList, cList, rList, recs] = await Promise.all([
        fetchBenchmarkTasks(),
        fetchBenchmarkModels(false),
        fetchBenchmarkConfigurations(),
        fetchBenchmarkRuns(),
        fetchBenchmarkRecommendations(),
      ]);

      setTasks(tList || []);
      setModels(mList || []);
      setConfigurations(cList || []);
      setHistoricalRuns(rList || []);
      setRecommendations(recs || []);

      // Default selections: select top 3 tasks and top 2 available configs
      if (tList && tList.length > 0) {
        setSelectedTaskIds([tList[0].id, tList[1].id]);
      }
      if (cList && cList.length > 0) {
        const avail = cList.filter((c) => c.is_available);
        const toSelect = avail.length > 0 ? avail.slice(0, 2) : cList.slice(0, 2);
        setSelectedConfigIds(toSelect.map((c) => c.id));
      }

      // If historical runs exist, set latest as active run
      if (rList && rList.length > 0) {
        const latest = rList[0];
        setActiveRunId(latest.id);
        setActiveRun(latest);
      }
    } catch (err) {
      console.error("Failed to load Benchmark Lab data:", err);
    } finally {
      setLoading(false);
    }
  };

  // Polling for active run
  useEffect(() => {
    if (!activeRunId || !isPolling) return;

    pollTimerRef.current = setInterval(async () => {
      try {
        const updated = await fetchBenchmarkRun(activeRunId);
        setActiveRun(updated);
        if (updated.status === "COMPLETED" || updated.status === "FAILED" || updated.status === "CANCELLED") {
          setIsPolling(false);
          // Refresh historical runs and recommendations
          const [rList, recs] = await Promise.all([
            fetchBenchmarkRuns(),
            fetchBenchmarkRecommendations(),
          ]);
          setHistoricalRuns(rList || []);
          setRecommendations(recs || []);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [activeRunId, isPolling]);

  const handleLaunchBenchmark = async () => {
    if (selectedTaskIds.length === 0) {
      alert("Please select at least one benchmark task.");
      return;
    }
    if (selectedConfigIds.length === 0) {
      alert("Please select at least one configuration to evaluate.");
      return;
    }

    setLaunching(true);
    try {
      const payload = {
        name: `Suite Benchmark (${selectedConfigIds.length} configs, ${selectedTaskIds.length} tasks)`,
        task_ids: selectedTaskIds,
        configuration_ids: selectedConfigIds,
        repeated_runs: parseInt(repeatedRuns, 10) || 1,
        priority: priority,
      };

      const started = await startBenchmarkRun(payload);
      setActiveRunId(started.id);
      setActiveRun(started);
      setIsPolling(true);
      setActiveTab("monitor");
    } catch (err) {
      alert(`Failed to launch benchmark: ${err.message}`);
    } finally {
      setLaunching(false);
    }
  };

  const handleCancelRun = async () => {
    if (!activeRunId) return;
    try {
      await cancelBenchmarkRun(activeRunId);
      setIsPolling(false);
      const updated = await fetchBenchmarkRun(activeRunId);
      setActiveRun(updated);
    } catch (err) {
      console.error("Failed to cancel run:", err);
    }
  };

  const handleSelectRun = async (runId) => {
    setActiveRunId(runId);
    try {
      const run = await fetchBenchmarkRun(runId);
      setActiveRun(run);
      setActiveTab("results");
    } catch (err) {
      console.error("Failed to load run:", err);
    }
  };

  const handleInspectArtifact = async (result) => {
    setSelectedResult(result);
    setActiveTab("artifacts");
    if (!result.generated_files || Object.keys(result.generated_files).length === 0) {
      setArtifactContent("// No generated code recorded for this execution.");
      return;
    }

    const firstFile = Object.keys(result.generated_files)[0];
    setLoadingArtifact(true);
    try {
      const art = await fetchArtifactContent(activeRunId, result.task_id, result.config_id, firstFile);
      setArtifactContent(art.content || result.generated_files[firstFile] || "");
    } catch {
      // Fallback to local stored generated_files
      setArtifactContent(result.generated_files[firstFile] || "// Artifact loading error.");
    } finally {
      setLoadingArtifact(false);
    }
  };

  const handleLoadMarkdownReport = async () => {
    if (!activeRunId) return;
    try {
      const rep = await fetchMarkdownReport(activeRunId);
      setMarkdownReport(rep.report_markdown || "");
    } catch (err) {
      console.error("Failed to load markdown report:", err);
    }
  };

  const toggleTaskSelection = (taskId) => {
    setSelectedTaskIds((prev) =>
      prev.includes(taskId) ? prev.filter((id) => id !== taskId) : [...prev, taskId]
    );
  };

  const toggleConfigSelection = (configId) => {
    setSelectedConfigIds((prev) =>
      prev.includes(configId) ? prev.filter((id) => id !== configId) : [...prev, configId]
    );
  };

  const selectAllTasks = () => {
    setSelectedTaskIds(tasks.map((t) => t.id));
  };

  const deselectAllTasks = () => {
    setSelectedTaskIds([]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0D14] flex flex-col items-center justify-center text-slate-300 gap-4">
        <FaSpinner className="w-10 h-10 text-cyan-400 animate-spin" />
        <p className="text-sm font-semibold tracking-wide">Initializing AIForge Benchmark Laboratory...</p>
      </div>
    );
  }

  const rankedConfigs = activeRun?.comparison?.ranked_configurations || [];
  const tradeOffs = activeRun?.comparison?.trade_offs || [];

  return (
    <div className="min-h-screen bg-[#08090D] text-[#E2E8F0] font-sans p-6 overflow-y-auto selection:bg-cyan-500 selection:text-black">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto border-b border-[#1E2433] pb-6 mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 text-cyan-400">
              <FaFlask size={22} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                AIForge Benchmark Lab
                <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  v2.0 Autonomous
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates, compares, and optimizes AI software engineers with deterministic tasks & empirical metrics.
              </p>
            </div>
          </div>
        </div>

        {/* Global Action / Status pills */}
        <div className="flex items-center gap-3">
          {activeRun && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#121622] border border-[#242C3D] text-xs">
              <span className="text-slate-400">Active Run:</span>
              <span className="font-mono font-bold text-white">{activeRun.name.slice(0, 24)}</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                  activeRun.status === "COMPLETED"
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : activeRun.status === "RUNNING"
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse"
                    : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                }`}
              >
                {activeRun.status}
              </span>
            </div>
          )}

          <button
            onClick={loadInitialData}
            title="Refresh Data"
            className="p-2.5 rounded-xl bg-[#121622] border border-[#242C3D] text-slate-300 hover:text-white hover:border-cyan-500/50 transition cursor-pointer"
          >
            <FaSyncAlt size={14} />
          </button>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex flex-wrap items-center gap-2 border-b border-[#1E2433] pb-3">
          {[
            { id: "setup", label: "Suite Setup", icon: <FaSlidersH /> },
            {
              id: "monitor",
              label: "Live Monitor",
              icon: <FaChartLine />,
              badge: isPolling ? "RUNNING" : null,
            },
            { id: "results", label: "Rankings & Trade-offs", icon: <FaTrophy /> },
            { id: "artifacts", label: "Artifacts & Inspection", icon: <FaFileAlt /> },
            { id: "history", label: "Recommendations & Archive", icon: <FaHistory /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                activeTab === tab.id
                  ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white border border-cyan-500/40 shadow-lg"
                  : "text-slate-400 hover:text-white hover:bg-[#121622]"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-cyan-400/20 text-cyan-300 border border-cyan-400/40 animate-pulse">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* ========================================================================= */}
        {/* TAB 1: SUITE SETUP                                                        */}
        {/* ========================================================================= */}
        {activeTab === "setup" && (
          <div className="space-y-6">
            {/* Top Config Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-5 space-y-2">
                <span className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-2">
                  <FaSlidersH className="text-cyan-400" /> Evaluation Priority
                </span>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-[#181F2E] border border-[#293247] rounded-xl px-3 py-2 text-xs font-medium text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="BEST_OVERALL">Best Overall (Balanced)</option>
                  <option value="MAX_CORRECTNESS">Maximum Correctness (Test Pass First)</option>
                  <option value="FASTEST_EXECUTION">Fastest Execution (Minimum Latency)</option>
                  <option value="BEST_QUALITY">Best Quality (Strict Clean AST & Types)</option>
                  <option value="LOWEST_RESOURCES">Lowest Resource Consumption</option>
                </select>
                <p className="text-[11px] text-slate-400">
                  Weighting profile applied when ranking configurations across tasks.
                </p>
              </div>

              <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-5 space-y-2">
                <span className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-2">
                  <FaClock className="text-purple-400" /> Repeatability & Iterations
                </span>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={repeatedRuns}
                    onChange={(e) => setRepeatedRuns(e.target.value)}
                    className="flex-1 accent-cyan-400"
                  />
                  <span className="font-mono text-sm font-bold text-white px-2.5 py-1 bg-[#181F2E] rounded-lg border border-[#293247]">
                    {repeatedRuns}x
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Runs each task multiple times to measure statistical run-to-run variation.
                </p>
              </div>

              <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-5 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-2">
                    <FaMicrochip className="text-emerald-400" /> Local Ollama Status
                  </span>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                    <span className="text-xs font-bold text-emerald-400">Daemon Reachable</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {models.filter((m) => m.provider === "Ollama").length} installed local models detected.
                  </p>
                </div>

                <button
                  onClick={handleLaunchBenchmark}
                  disabled={launching}
                  className="w-full mt-3 py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-black font-extrabold text-xs rounded-xl shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-50"
                >
                  {launching ? <FaSpinner className="animate-spin" /> : <FaPlay />}
                  <span>Launch Benchmark Matrix</span>
                </button>
              </div>
            </div>

            {/* Task Library Selector */}
            <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1E2433] pb-3">
                <div className="flex items-center gap-2">
                  <FaLayerGroup className="text-cyan-400" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Benchmark Task Library ({tasks.length} Deterministic Tasks)
                  </h3>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <button
                    onClick={selectAllTasks}
                    className="px-2.5 py-1 rounded-lg bg-[#181F2E] border border-[#293247] text-slate-300 hover:text-white"
                  >
                    Select All
                  </button>
                  <button
                    onClick={deselectAllTasks}
                    className="px-2.5 py-1 rounded-lg bg-[#181F2E] border border-[#293247] text-slate-300 hover:text-white"
                  >
                    Clear
                  </button>
                  <span className="text-slate-400 ml-2">Selected: {selectedTaskIds.length}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {tasks.map((task) => {
                  const isSelected = selectedTaskIds.includes(task.id);
                  return (
                    <div
                      key={task.id}
                      onClick={() => toggleTaskSelection(task.id)}
                      className={`p-4 rounded-xl border transition cursor-pointer select-none ${
                        isSelected
                          ? "bg-gradient-to-br from-cyan-950/30 to-[#121622] border-cyan-500/50 shadow-md shadow-cyan-500/10"
                          : "bg-[#141926] border-[#222A3B] opacity-75 hover:opacity-100"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs font-extrabold text-white">{task.name}</span>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="mt-1 accent-cyan-400"
                        />
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{task.description}</p>
                      <div className="flex flex-wrap items-center gap-1.5 mt-3">
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold ${
                            task.difficulty === "EASY"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : task.difficulty === "HARD"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}
                        >
                          {task.difficulty}
                        </span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-bold">
                          {task.category}
                        </span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {task.framework}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Configurations Selector */}
            <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1E2433] pb-3">
                <div className="flex items-center gap-2">
                  <FaCogs className="text-purple-400" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Model & Agent Workflow Configurations
                  </h3>
                </div>
                <span className="text-xs text-slate-400">Selected: {selectedConfigIds.length}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {configurations.map((cfg) => {
                  const isSelected = selectedConfigIds.includes(cfg.id);
                  return (
                    <div
                      key={cfg.id}
                      onClick={() => cfg.is_available && toggleConfigSelection(cfg.id)}
                      className={`p-4 rounded-xl border transition ${
                        !cfg.is_available
                          ? "bg-[#121622] border-rose-900/30 opacity-50 cursor-not-allowed"
                          : isSelected
                          ? "bg-gradient-to-br from-purple-950/30 to-[#121622] border-purple-500/50 shadow-md shadow-purple-500/10 cursor-pointer"
                          : "bg-[#141926] border-[#222A3B] opacity-80 hover:opacity-100 cursor-pointer"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs font-bold text-white">{cfg.name}</span>
                        {cfg.is_available ? (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}}
                            className="mt-1 accent-purple-400"
                          />
                        ) : (
                          <span className="text-[9px] text-rose-400 font-bold">OFFLINE</span>
                        )}
                      </div>

                      <div className="text-[11px] text-slate-400 mt-1 font-mono">
                        Model: <span className="text-cyan-400">{cfg.model_name}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Workflow: <span className="text-purple-400">{cfg.workflow}</span>
                      </div>

                      <div className="flex items-center justify-between mt-3 text-[10px] text-slate-400 border-t border-[#1E2433] pt-2">
                        <span>Max Repairs: {cfg.max_repair_attempts}</span>
                        <span>Timeout: {cfg.timeout_seconds}s</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: LIVE EXECUTION MONITOR                                             */}
        {/* ========================================================================= */}
        {activeTab === "monitor" && (
          <div className="space-y-6">
            {!activeRun ? (
              <div className="p-12 text-center text-slate-400 bg-[#10141E] border border-[#1E2433] rounded-2xl">
                No active benchmark run found. Launch one from Suite Setup.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Run Overview Banner */}
                <div className="bg-gradient-to-r from-slate-950 via-[#10141E] to-slate-950 border border-cyan-500/30 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h2 className="text-base font-bold text-white">{activeRun.name}</h2>
                      <span
                        className={`px-2.5 py-0.5 rounded text-xs font-bold font-mono ${
                          activeRun.status === "RUNNING"
                            ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse"
                            : activeRun.status === "COMPLETED"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        }`}
                      >
                        {activeRun.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 font-mono">ID: {activeRun.id} | Priority: {activeRun.priority}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    {activeRun.status === "RUNNING" && (
                      <button
                        onClick={handleCancelRun}
                        className="px-4 py-2 bg-rose-500/10 border border-rose-500/30 hover:bg-rose-500/20 text-rose-400 font-bold text-xs rounded-xl flex items-center gap-2 transition cursor-pointer"
                      >
                        <FaStop /> Cancel Execution
                      </button>
                    )}
                    <button
                      onClick={() => handleSelectRun(activeRun.id)}
                      className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 hover:bg-cyan-500/20 text-cyan-400 font-bold text-xs rounded-xl flex items-center gap-2 transition cursor-pointer"
                    >
                      <FaTrophy /> View Rankings
                    </button>
                  </div>
                </div>

                {/* Progress Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
                  <div className="p-4 bg-[#10141E] border border-[#1E2433] rounded-xl space-y-1">
                    <span className="text-slate-400 block font-sans">Total Evaluated</span>
                    <span className="text-lg font-bold text-white">{activeRun.results.length}</span>
                  </div>
                  <div className="p-4 bg-[#10141E] border border-[#1E2433] rounded-xl space-y-1">
                    <span className="text-slate-400 block font-sans">Passed</span>
                    <span className="text-lg font-bold text-emerald-400">
                      {activeRun.results.filter((r) => r.status === "COMPLETED").length}
                    </span>
                  </div>
                  <div className="p-4 bg-[#10141E] border border-[#1E2433] rounded-xl space-y-1">
                    <span className="text-slate-400 block font-sans">Failed</span>
                    <span className="text-lg font-bold text-rose-400">
                      {activeRun.results.filter((r) => r.status === "FAILED").length}
                    </span>
                  </div>
                  <div className="p-4 bg-[#10141E] border border-[#1E2433] rounded-xl space-y-1">
                    <span className="text-slate-400 block font-sans">Configurations</span>
                    <span className="text-lg font-bold text-purple-400">{activeRun.configurations.length}</span>
                  </div>
                </div>

                {/* Real-time Task Execution Table */}
                <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-4">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-[#1E2433] pb-3 flex items-center gap-2">
                    <FaChartLine className="text-cyan-400" /> Task Execution Stream
                  </h3>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-sans">
                      <thead>
                        <tr className="border-b border-[#1E2433] text-[11px] font-mono text-slate-400 uppercase">
                          <th className="pb-3">Task Name</th>
                          <th className="pb-3">Configuration</th>
                          <th className="pb-3">Status</th>
                          <th className="pb-3">Tests Passed</th>
                          <th className="pb-3">Duration</th>
                          <th className="pb-3">Score</th>
                          <th className="pb-3 text-right">Inspect</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1E2433]/60 font-mono">
                        {activeRun.results.map((r, i) => (
                          <tr key={i} className="hover:bg-[#141926]/50 transition">
                            <td className="py-3 font-bold text-white font-sans">{r.task_name}</td>
                            <td className="py-3 text-slate-300 font-mono text-[11px]">{r.config_id}</td>
                            <td className="py-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  r.status === "COMPLETED"
                                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                    : r.status === "RUNNING"
                                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse"
                                    : r.status === "NOT_RUN"
                                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                }`}
                              >
                                {r.status}
                              </span>
                            </td>
                            <td className="py-3 text-emerald-400 font-bold">
                              {r.metrics.tests_total > 0
                                ? `${r.metrics.tests_passed}/${r.metrics.tests_total}`
                                : r.metrics.build_success
                                ? "BUILD PASS"
                                : "0/0"}
                            </td>
                            <td className="py-3 text-slate-300">{r.metrics.duration_seconds}s</td>
                            <td className="py-3 font-bold text-cyan-400">{r.metrics.overall_score}</td>
                            <td className="py-3 text-right">
                              <button
                                onClick={() => handleInspectArtifact(r)}
                                className="px-2.5 py-1 rounded bg-[#181F2E] border border-[#293247] hover:border-cyan-500/40 text-cyan-400 text-[11px] font-bold"
                              >
                                View Code
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: RESULTS & COMPARATIVE RANKINGS                                     */}
        {/* ========================================================================= */}
        {activeTab === "results" && (
          <div className="space-y-6">
            {!activeRun ? (
              <div className="p-12 text-center text-slate-400 bg-[#10141E] border border-[#1E2433] rounded-2xl">
                No active run selected.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Ranking Summary */}
                <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-[#1E2433] pb-3">
                    <div className="flex items-center gap-2">
                      <FaTrophy className="text-amber-400" />
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                        Ranked Configurations for Priority: {activeRun.comparison?.priority || activeRun.priority}
                      </h3>
                    </div>
                    <button
                      onClick={handleLoadMarkdownReport}
                      className="px-3 py-1.5 rounded-xl bg-[#181F2E] border border-[#293247] text-xs font-bold text-slate-300 hover:text-white flex items-center gap-1.5"
                    >
                      <FaFileAlt /> View Markdown Report
                    </button>
                  </div>

                  {rankedConfigs.length === 0 ? (
                    <p className="text-xs text-slate-400">
                      No comparative ranking available. Run or complete benchmark tasks first.
                    </p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-sans">
                        <thead>
                          <tr className="border-b border-[#1E2433] text-[11px] font-mono text-slate-400 uppercase">
                            <th className="pb-3">Rank</th>
                            <th className="pb-3">Configuration</th>
                            <th className="pb-3">Model</th>
                            <th className="pb-3">Test Pass Rate</th>
                            <th className="pb-3">Build Rate</th>
                            <th className="pb-3">Quality</th>
                            <th className="pb-3">Avg Latency</th>
                            <th className="pb-3 text-right">Composite Score</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#1E2433]/60 font-mono">
                          {rankedConfigs.map((cfg) => (
                            <tr
                              key={cfg.config_id}
                              className={`transition ${
                                cfg.rank === 1 ? "bg-amber-500/5 hover:bg-amber-500/10 font-bold" : "hover:bg-[#141926]/50"
                              }`}
                            >
                              <td className="py-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                    cfg.rank === 1
                                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                                      : "bg-slate-800 text-slate-300"
                                  }`}
                                >
                                  #{cfg.rank}
                                </span>
                              </td>
                              <td className="py-3 font-sans text-white font-bold">{cfg.config_name}</td>
                              <td className="py-3 text-cyan-400 font-mono">{cfg.model_name}</td>
                              <td className="py-3 text-emerald-400 font-bold">{cfg.test_pass_rate}%</td>
                              <td className="py-3 text-slate-300">{cfg.build_success_rate}%</td>
                              <td className="py-3 text-purple-400">{cfg.mean_quality}%</td>
                              <td className="py-3 text-slate-300">
                                {cfg.mean_duration_seconds}s (±{cfg.std_duration}s)
                              </td>
                              <td className="py-3 text-right">
                                <span className="text-base font-extrabold text-cyan-400">{cfg.composite_score}</span>
                                <span className="text-slate-500 text-[10px]"> / 100</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Trade-off Insights */}
                {tradeOffs.length > 0 && (
                  <div className="bg-gradient-to-br from-indigo-950/20 via-[#10141E] to-[#10141E] border border-indigo-500/30 rounded-2xl p-6 space-y-3">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <FaLightbulb className="text-amber-400" /> Empirical Trade-Off Analysis
                    </h3>
                    {tradeOffs.map((to, i) => (
                      <div key={i} className="p-3.5 bg-[#141926] border border-[#222A3B] rounded-xl space-y-1">
                        <span className="text-xs font-bold text-cyan-400 block">{to.comparison}</span>
                        <p className="text-xs text-slate-300">{to.analysis}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Markdown Report Modal / Drawer */}
                {markdownReport && (
                  <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-3 font-mono">
                    <div className="flex items-center justify-between border-b border-[#1E2433] pb-3">
                      <span className="text-xs font-bold text-white uppercase font-sans">Generated Markdown Report</span>
                      <button
                        onClick={() => setMarkdownReport("")}
                        className="text-xs text-slate-400 hover:text-white"
                      >
                        Close
                      </button>
                    </div>
                    <pre className="p-4 bg-[#090D14] rounded-xl border border-[#1E2433] text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-96">
                      {markdownReport}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: ARTIFACTS & INSPECTION                                             */}
        {/* ========================================================================= */}
        {activeTab === "artifacts" && (
          <div className="space-y-6">
            {!selectedResult ? (
              <div className="p-12 text-center text-slate-400 bg-[#10141E] border border-[#1E2433] rounded-2xl">
                Select a task result from the Live Monitor to inspect generated code and validation output.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Header for selected task */}
                <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <FaCode className="text-cyan-400" /> {selectedResult.task_name}
                    </h3>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">
                      Config: {selectedResult.config_id} | Status: {selectedResult.status} | Duration: {selectedResult.metrics.duration_seconds}s
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-lg text-xs font-mono font-bold">
                      Score: {selectedResult.metrics.overall_score} / 100
                    </span>
                  </div>
                </div>

                {/* Code Viewer & Test Output split */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Generated Code */}
                  <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-3 flex flex-col">
                    <div className="flex items-center justify-between border-b border-[#1E2433] pb-3">
                      <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Generated Artifact Code
                      </span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(artifactContent);
                          setCopiedCode(true);
                          setTimeout(() => setCopiedCode(false), 2000);
                        }}
                        className="text-xs text-cyan-400 hover:text-white flex items-center gap-1.5"
                      >
                        {copiedCode ? <FaCheck /> : <FaCopy />}
                        <span>{copiedCode ? "Copied" : "Copy Code"}</span>
                      </button>
                    </div>

                    <pre className="p-4 bg-[#090D14] rounded-xl border border-[#1E2433] text-xs font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap max-h-[500px] flex-1">
                      {loadingArtifact ? "Loading artifact source..." : artifactContent}
                    </pre>
                  </div>

                  {/* Validation Stderr / Stdout */}
                  <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-3 flex flex-col">
                    <div className="flex items-center justify-between border-b border-[#1E2433] pb-3">
                      <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Out-of-Band Validation Logs (Pytest)
                      </span>
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded ${
                          selectedResult.metrics.build_success
                            ? "text-emerald-400 bg-emerald-500/10"
                            : "text-rose-400 bg-rose-500/10"
                        }`}
                      >
                        {selectedResult.metrics.build_success ? "PASSED" : "FAILED"}
                      </span>
                    </div>

                    <pre className="p-4 bg-[#090D14] rounded-xl border border-[#1E2433] text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-[500px] flex-1">
                      {selectedResult.validation_stdout ||
                        selectedResult.validation_stderr ||
                        selectedResult.error_message ||
                        "No validation output logs recorded."}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 5: RECOMMENDATIONS & ARCHIVE                                          */}
        {/* ========================================================================= */}
        {activeTab === "history" && (
          <div className="space-y-6">
            {/* Recommendations Section */}
            <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-[#1E2433] pb-3 flex items-center gap-2">
                <FaLightbulb className="text-amber-400" /> Evidence-Backed Engineering Recommendations
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="p-5 rounded-xl bg-gradient-to-br from-[#121622] to-[#141926] border border-[#242C3D] space-y-3 shadow-lg"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{rec.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-bold">
                        {rec.confidence}
                      </span>
                    </div>

                    <div className="text-xs text-slate-300 space-y-1">
                      <div>
                        <span className="text-slate-400">Target Scenario: </span>
                        <span className="text-white font-semibold">{rec.target_scenario}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Recommended: </span>
                        <span className="text-cyan-400 font-mono font-bold">{rec.recommended_configuration}</span>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-400 border-t border-[#1E2433] pt-2">
                      <span className="font-semibold text-slate-300">Observed Evidence: </span>
                      {rec.evidence}
                    </p>

                    <p className="text-[11px] text-slate-400">
                      <span className="font-semibold text-slate-300">Trade-offs: </span>
                      {rec.trade_offs}
                    </p>

                    <div className="pt-2 flex items-center justify-between text-[10px] text-slate-500 border-t border-[#1E2433]">
                      <span>Approval required before changing active workflows</span>
                      <span>Runs cited: {rec.cited_runs?.length || 0}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Historical Runs Archive */}
            <div className="bg-[#10141E] border border-[#1E2433] rounded-2xl p-6 space-y-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-[#1E2433] pb-3 flex items-center gap-2">
                <FaHistory className="text-purple-400" /> Historical Benchmark Run Archive
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-sans">
                  <thead>
                    <tr className="border-b border-[#1E2433] text-[11px] font-mono text-slate-400 uppercase">
                      <th className="pb-3">Run Name</th>
                      <th className="pb-3">Timestamp</th>
                      <th className="pb-3">Tasks Evaluated</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3">Winning Config</th>
                      <th className="pb-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1E2433]/60 font-mono">
                    {historicalRuns.map((r) => (
                      <tr key={r.id} className="hover:bg-[#141926]/50 transition">
                        <td className="py-3 font-bold text-white font-sans">{r.name}</td>
                        <td className="py-3 text-slate-400 text-[11px]">{r.created_at.slice(0, 19).replace("T", " ")}</td>
                        <td className="py-3 text-slate-300">{r.results.length}</td>
                        <td className="py-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              r.status === "COMPLETED"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : r.status === "NOT_RUN"
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {r.status}
                          </span>
                        </td>
                        <td className="py-3 text-cyan-400 font-bold">
                          {r.comparison?.best_configuration_id || "N/A"}
                        </td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => handleSelectRun(r.id)}
                            className="px-2.5 py-1 rounded bg-[#181F2E] border border-[#293247] hover:border-cyan-500/40 text-cyan-400 text-[11px] font-bold"
                          >
                            View Results
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
