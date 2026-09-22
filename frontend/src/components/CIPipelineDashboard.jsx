import { useState, useEffect, useRef } from "react";
import {
    Play,
    CheckCircle2,
    XCircle,
    RotateCw,
    Terminal,
    AlertTriangle,
    Shield,
    Cpu,
    Wrench,
    FileCode,
    RefreshCw,
    Activity,
    Layers,
    Server,
    Clock,
    GitBranch,
    Copy,
    Check,
    History
} from "lucide-react";
import axios from "axios";

const CI_STAGES = [
    { id: "dependencies", label: "Dependencies", icon: Cpu, desc: "Package manager resolution & installation" },
    { id: "build", label: "Build", icon: Layers, desc: "Syntax compilation & asset packaging" },
    { id: "tests", label: "Tests", icon: Play, desc: "Automated test suite execution" },
    { id: "lint", label: "Lint", icon: Activity, desc: "Static analysis & style conventions" },
    { id: "security", label: "Security", icon: Shield, desc: "OWASP patterns & secret leak detection" },
];

const DEMO_PROJECTS = {
    python_fastapi: {
        name: "FastAPI E-Commerce Service",
        type: "python",
        files: {
            "backend/main.py": `from fastapi import FastAPI, HTTPException\n\napp = FastAPI(title="Store API")\n\n@app.get("/health")\ndef health():\n    return {"status": "ok", "service": "store"}\n\n@app.get("/items/{item_id}")\ndef get_item(item_id: int):\n    if item_id <= 0:\n        raise HTTPException(status_code=400, detail="Invalid ID")\n    return {"id": item_id, "name": f"Product #{item_id}", "in_stock": True}\n`,
            "tests/test_main.py": `import pytest\nfrom backend.main import health, get_item\n\ndef test_health():\n    res = health()\n    assert res["status"] == "ok"\n\ndef test_get_item():\n    res = get_item(10)\n    assert res["id"] == 10\n    assert res["in_stock"] is True\n`,
            "requirements.txt": "fastapi>=0.100.0\npytest>=7.0.0\n"
        }
    },
    python_ci_repair: {
        name: "Python Self-Healing CI Demo",
        type: "python",
        files: {
            "backend/main.py": `def calculate_discount(price, pct):\n    # Intentional bug for CI repair loop demo\n    return price - (price * (pct / 100.0))\n\ndef get_service_status():\n    return {'status': 'READY'}\n`,
            "tests/test_calc.py": `from backend.main import calculate_discount, get_service_status\n\ndef test_discount():\n    assert calculate_discount(100, 20) == 80.0\n    assert calculate_discount(200, 50) == 100.0\n\ndef test_status():\n    assert get_service_status()['status'] == 'READY'\n`,
            "requirements.txt": "pytest\n"
        }
    },
    react_vite: {
        name: "React / Vite Frontend Dashboard",
        type: "javascript",
        files: {
            "package.json": JSON.stringify({
                name: "vite-dashboard",
                version: "1.0.0",
                scripts: {
                    build: "vite build",
                    test: "node -e \"console.log('✔ Component tests: 5 passed'); process.exit(0);\""
                },
                dependencies: {
                    react: "^18.2.0",
                    "react-dom": "^18.2.0"
                }
            }, null, 2),
            "src/App.jsx": "export default function App() { return <div><h1>AIForge CI Dashboard</h1></div>; }",
            "index.html": "<!DOCTYPE html><html><body><div id='root'></div></body></html>"
        }
    }
};

export default function CIPipelineDashboard() {
    const [selectedProjectKey, setSelectedProjectKey] = useState("python_fastapi");
    const [executionBackend, setExecutionBackend] = useState("local");
    const [maxRetries, setMaxRetries] = useState(3);
    const [isRunning, setIsRunning] = useState(false);
    const [activeTab, setActiveTab] = useState("pipeline"); // pipeline, console, history, workflow
    const [currentStage, setCurrentStage] = useState(null);
    const [ciResult, setCiResult] = useState(null);
    const [consoleLogs, setConsoleLogs] = useState([]);
    const [runHistory, setRunHistory] = useState([]);
    const [copiedYaml, setCopiedYaml] = useState(false);
    const terminalRef = useRef(null);

    const activeProject = DEMO_PROJECTS[selectedProjectKey] || DEMO_PROJECTS.python_fastapi;
    const projectId = activeProject.name.toLowerCase().replace(/[^a-z0-9]/g, "_");

    useEffect(() => {
        fetchHistory();
    }, [selectedProjectKey]);

    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [consoleLogs]);

    const fetchHistory = async () => {
        try {
            const res = await axios.get(`/api/projects/${projectId}/ci/history`);
            if (res.data?.history) {
                setRunHistory(res.data.history);
            }
        } catch {
            // Ignore if empty
        }
    };

    const runCIPipeline = async () => {
        setIsRunning(true);
        setCurrentStage("dependencies");
        setCiResult(null);
        setConsoleLogs([
            `🚀 Initiating AIForge Autonomous CI/CD Pipeline for '${activeProject.name}'...`,
            `⚙ Backend Sandbox: ${executionBackend === "docker" ? "🐳 Docker Container" : "💻 Local Subprocess"}`
        ]);

        const payload = {
            files: activeProject.files,
            commit_version: "v1.2.0",
            max_repair_attempts: Number(maxRetries),
            timeout_seconds: 30.0,
            execution_backend: executionBackend,
            docker_enabled: executionBackend === "docker",
            memory_limit: "512m",
            cpu_limit: 1.0,
            network_mode: "none",
            generate_github_workflow: true
        };

        try {
            const res = await axios.post(`/api/projects/${projectId}/ci/run`, payload);
            if (res.data && res.data.result) {
                const report = res.data.result;
                setCiResult(report);
                setCurrentStage(null);

                const logs = [`🏁 CI Pipeline Completed with status: ${report.status}`];
                report.stages?.forEach((st) => {
                    const icon = st.status === "passed" ? "✔" : st.status === "warning" ? "⚠️" : "❌";
                    logs.push(`[${st.stage.toUpperCase()}] ${icon} Status: ${st.status} (Duration: ${st.duration}s, Code: ${st.exit_code})`);
                    if (st.command) logs.push(`$ ${st.command}`);
                    if (st.stdout) logs.push(st.stdout);
                    if (st.stderr) logs.push(`[ERR] ${st.stderr}`);
                });

                if (report.applied_repairs?.length > 0) {
                    logs.push(`🤖 Autonomous Self-Healing Repaired ${report.applied_repairs.length} Failure(s)`);
                    report.applied_repairs.forEach((rep) => {
                        logs.push(`   Cycle ${rep.attempt}: Fixed ${rep.failed_stage} -> ${rep.root_cause}`);
                    });
                }

                setConsoleLogs((prev) => [...prev, ...logs]);
                fetchHistory();
            }
        } catch (err) {
            const msg = err.response?.data?.detail || err.message;
            setConsoleLogs((prev) => [...prev, `❌ CI Pipeline execution failed: ${msg}`]);
        } finally {
            setIsRunning(false);
        }
    };

    const copyWorkflowYaml = () => {
        if (ciResult?.workflow_yaml) {
            navigator.clipboard.writeText(ciResult.workflow_yaml);
            setCopiedYaml(true);
            setTimeout(() => setCopiedYaml(false), 2000);
        }
    };

    const getStageState = (stageId) => {
        if (!ciResult) {
            return isRunning && currentStage === stageId ? "active" : "pending";
        }
        const stageObj = ciResult.stages?.find((s) => s.stage === stageId);
        if (!stageObj) return "pending";
        return stageObj.status; // passed, failed, warning, skipped
    };

    return (
        <div className="flex flex-col h-full bg-[#090d16] text-slate-200 p-6 overflow-y-auto space-y-6">
            {/* Top Bar Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
                <div>
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-500/10">
                            <GitBranch className="w-6 h-6 animate-pulse" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                                Autonomous CI/CD Pipeline
                                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-medium">
                                    Quality Gate Engine
                                </span>
                            </h1>
                            <p className="text-sm text-slate-400 mt-0.5">
                                Automated multi-stage validation: Dependency • Build • Test • Lint • Security with AI Debug Repair
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                    {/* Sandbox Backend Switcher */}
                    <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg p-1 text-xs">
                        <button
                            type="button"
                            onClick={() => setExecutionBackend("local")}
                            disabled={isRunning}
                            className={`px-2.5 py-1 rounded font-medium transition-all ${
                                executionBackend === "local"
                                    ? "bg-indigo-600 text-white shadow"
                                    : "text-slate-400 hover:text-slate-200"
                            }`}
                        >
                            💻 Local Sandbox
                        </button>
                        <button
                            type="button"
                            onClick={() => setExecutionBackend("docker")}
                            disabled={isRunning}
                            className={`px-2.5 py-1 rounded font-medium transition-all ${
                                executionBackend === "docker"
                                    ? "bg-cyan-600 text-white shadow shadow-cyan-500/20"
                                    : "text-slate-400 hover:text-slate-200"
                            }`}
                        >
                            🐳 Docker Sandbox
                        </button>
                    </div>

                    <select
                        value={selectedProjectKey}
                        onChange={(e) => setSelectedProjectKey(e.target.value)}
                        disabled={isRunning}
                        className="bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                        <option value="python_fastapi">Python (FastAPI + Pytest)</option>
                        <option value="python_ci_repair">Python (CI Self-Healing Repair Demo)</option>
                        <option value="react_vite">React / Vite (JavaScript)</option>
                    </select>

                    <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-400">
                        <span>Max Repairs:</span>
                        <input
                            type="number"
                            min="1"
                            max="5"
                            value={maxRetries}
                            onChange={(e) => setMaxRetries(e.target.value)}
                            className="w-8 bg-slate-800 border border-slate-700 rounded px-1 py-0.5 text-white text-center text-xs"
                        />
                    </div>

                    <button
                        onClick={runCIPipeline}
                        disabled={isRunning}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-xs transition-all shadow-lg ${
                            isRunning
                                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                                : "bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-cyan-600/25"
                        }`}
                    >
                        {isRunning ? (
                            <>
                                <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                                Running CI Pipeline...
                            </>
                        ) : (
                            <>
                                <Play className="w-4 h-4 fill-white" />
                                Execute CI Pipeline
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Stages Visual Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {CI_STAGES.map((stage, idx) => {
                    const status = getStageState(stage.id);
                    const StageIcon = stage.icon;

                    let badgeClasses = "border-slate-800 bg-slate-900/40 text-slate-500";
                    let iconClasses = "text-slate-500";
                    let statusLabel = "Pending";

                    if (status === "active") {
                        badgeClasses = "border-cyan-500/60 bg-cyan-950/40 text-cyan-300 ring-1 ring-cyan-500/40 animate-pulse";
                        iconClasses = "text-cyan-400";
                        statusLabel = "Running...";
                    } else if (status === "passed") {
                        badgeClasses = "border-emerald-500/40 bg-emerald-950/20 text-emerald-300";
                        iconClasses = "text-emerald-400";
                        statusLabel = "Passed ✅";
                    } else if (status === "warning") {
                        badgeClasses = "border-amber-500/40 bg-amber-950/20 text-amber-300";
                        iconClasses = "text-amber-400";
                        statusLabel = "Warning ⚠️";
                    } else if (status === "failed") {
                        badgeClasses = "border-rose-500/40 bg-rose-950/20 text-rose-300";
                        iconClasses = "text-rose-400";
                        statusLabel = "Failed ❌";
                    }

                    return (
                        <div
                            key={stage.id}
                            className={`flex flex-col justify-between p-4 rounded-xl border transition-all ${badgeClasses}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                                    Stage 0{idx + 1}
                                </span>
                                <StageIcon className={`w-4 h-4 ${iconClasses}`} />
                            </div>
                            <div>
                                <h4 className="text-sm font-semibold leading-tight">{stage.label}</h4>
                                <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{stage.desc}</p>
                            </div>
                            <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                                <span className="font-mono text-[11px] font-medium">{statusLabel}</span>
                                {ciResult?.stages?.find((s) => s.stage === stage.id)?.duration && (
                                    <span className="text-slate-400 font-mono text-[10px]">
                                        {ciResult.stages.find((s) => s.stage === stage.id).duration}s
                                    </span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800">
                {[
                    { id: "pipeline", label: "Pipeline Status", icon: Activity },
                    { id: "console", label: "Execution Console", icon: Terminal },
                    { id: "history", label: "Run History", icon: History },
                    { id: "workflow", label: "GitHub Actions Workflow", icon: GitBranch },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
                            activeTab === tab.id
                                ? "border-cyan-500 text-cyan-400 bg-cyan-500/5"
                                : "border-transparent text-slate-400 hover:text-slate-200"
                        }`}
                    >
                        <tab.icon className="w-3.5 h-3.5" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab: Pipeline Status */}
            {activeTab === "pipeline" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Stage Results Trace */}
                    <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                <Activity className="w-4 h-4 text-cyan-400" />
                                CI Stage Execution Summary
                            </h3>
                            {ciResult && (
                                <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${
                                    ciResult.status === "PASSED"
                                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                                        : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                                }`}>
                                    {ciResult.status} ({ciResult.duration}s)
                                </span>
                            )}
                        </div>

                        {!ciResult ? (
                            <div className="py-12 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
                                Ready to execute. Click &quot;Execute CI Pipeline&quot; to run quality checks.
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {ciResult.stages?.map((stage, i) => (
                                    <div
                                        key={i}
                                        className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-950/40 text-xs space-y-1.5"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 font-medium text-slate-200 uppercase tracking-wide text-[11px]">
                                                {stage.status === "passed" ? (
                                                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                                ) : stage.status === "warning" ? (
                                                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                                                ) : (
                                                    <XCircle className="w-4 h-4 text-rose-400" />
                                                )}
                                                <span>{stage.stage}</span>
                                            </div>
                                            <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                                                <span>Exit: {stage.exit_code}</span>
                                                <span>{stage.duration}s</span>
                                            </div>
                                        </div>

                                        {stage.command && stage.command !== "skip" && (
                                            <div className="font-mono text-[11px] text-cyan-300 bg-cyan-950/30 px-2.5 py-1 rounded border border-cyan-900/30">
                                                $ {stage.command}
                                            </div>
                                        )}

                                        {stage.stderr && (
                                            <div className="text-rose-400 text-[11px] font-mono bg-rose-950/20 p-2 rounded border border-rose-900/30">
                                                {stage.stderr}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Self-Healing & Telemetry Summary Card */}
                    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                            <Wrench className="w-4 h-4 text-violet-400" />
                            Autonomous Debug & Repair Loop
                        </h3>

                        {ciResult?.applied_repairs?.length > 0 ? (
                            <div className="space-y-3">
                                {ciResult.applied_repairs.map((fix, idx) => (
                                    <div
                                        key={idx}
                                        className="p-3.5 rounded-lg border border-violet-500/20 bg-violet-950/10 text-xs space-y-1"
                                    >
                                        <div className="flex items-center justify-between text-violet-300 font-medium">
                                            <span>Cycle {fix.attempt}: [{fix.failed_stage}]</span>
                                            <span className="text-[10px] text-slate-400 font-mono">
                                                {Math.round(fix.confidence * 100)}% Confidence
                                            </span>
                                        </div>
                                        <p className="text-slate-300 text-[11px]">{fix.root_cause}</p>
                                        {fix.modified_files?.length > 0 && (
                                            <div className="mt-2 text-[10px] text-slate-400">
                                                Patched: <span className="font-mono text-cyan-300">{fix.modified_files.join(", ")}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                                {ciResult
                                    ? "All stages passed on initial run. Zero repairs needed!"
                                    : "Failure repair cycles will be recorded here when errors occur."}
                            </div>
                        )}

                        <div className="border-t border-slate-800/80 pt-3 text-xs text-slate-400 space-y-1.5">
                            <div className="flex justify-between">
                                <span>CI Overall Status:</span>
                                <span className={`font-bold ${ciResult?.status === "PASSED" ? "text-emerald-400" : "text-slate-200"}`}>
                                    {ciResult?.status || "READY"}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>Repair Cycles:</span>
                                <span className="text-slate-200">{ciResult?.repair_attempts || 0} / {maxRetries}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Sandbox Isolation:</span>
                                <span className="text-cyan-400 font-mono">
                                    {executionBackend === "docker" ? "🐳 Docker Container" : "💻 Local Subprocess"}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>Total Duration:</span>
                                <span className="text-slate-200">{ciResult?.duration || 0}s</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Tab: Console Stream */}
            {activeTab === "console" && (
                <div className="bg-[#0b0e14] border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col h-96">
                    <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between text-xs text-slate-400">
                        <div className="flex items-center gap-2">
                            <Terminal className="w-4 h-4 text-cyan-400" />
                            <span className="font-mono">CI Pipeline Console Stream</span>
                        </div>
                        <span className="text-[11px] text-slate-500 font-mono">Real-time telemetry</span>
                    </div>

                    <div
                        ref={terminalRef}
                        className="p-4 font-mono text-xs text-slate-300 space-y-1 overflow-y-auto flex-1 bg-black/40 selection:bg-cyan-500 selection:text-white"
                    >
                        {consoleLogs.map((log, i) => (
                            <div
                                key={i}
                                className={
                                    log.startsWith("[ERR]") || log.includes("failed") || log.includes("FAILED")
                                        ? "text-rose-400"
                                        : log.startsWith("$")
                                        ? "text-cyan-400 font-semibold"
                                        : log.startsWith("✔") || log.includes("PASSED")
                                        ? "text-emerald-400"
                                        : "text-slate-300"
                                }
                            >
                                {log}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Tab: Run History */}
            {activeTab === "history" && (
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                            <History className="w-4 h-4 text-cyan-400" />
                            Historical Pipeline Executions ({runHistory.length})
                        </h3>
                        <button
                            onClick={fetchHistory}
                            className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
                        >
                            <RefreshCw className="w-3.5 h-3.5" /> Refresh
                        </button>
                    </div>

                    {runHistory.length === 0 ? (
                        <div className="py-12 text-center text-slate-500 text-xs">
                            No recorded CI runs yet for this project.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs text-left">
                                <thead className="text-[11px] text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
                                    <tr>
                                        <th className="px-4 py-2.5">Run ID</th>
                                        <th className="px-4 py-2.5">Status</th>
                                        <th className="px-4 py-2.5">Duration</th>
                                        <th className="px-4 py-2.5">Repairs</th>
                                        <th className="px-4 py-2.5">Backend</th>
                                        <th className="px-4 py-2.5">Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/60 font-mono">
                                    {runHistory.map((run) => (
                                        <tr key={run.run_id} className="hover:bg-slate-800/20">
                                            <td className="px-4 py-3 font-semibold text-cyan-300">{run.run_id}</td>
                                            <td className="px-4 py-3">
                                                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                                    run.overall_status === "PASSED"
                                                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                                        : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                                                }`}>
                                                    {run.overall_status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-slate-300">{run.duration}s</td>
                                            <td className="px-4 py-3 text-violet-300">{run.repair_attempts}</td>
                                            <td className="px-4 py-3 text-slate-400">{run.backend_used}</td>
                                            <td className="px-4 py-3 text-slate-400 text-[11px]">{new Date(run.timestamp).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Tab: GitHub Actions Workflow */}
            {activeTab === "workflow" && (
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div>
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                <GitBranch className="w-4 h-4 text-cyan-400" />
                                Generated GitHub Actions Workflow (.github/workflows/aiforge-ci.yml)
                            </h3>
                            <p className="text-xs text-slate-400 mt-0.5">Automated CI workflow tailored to detected project type</p>
                        </div>
                        <button
                            onClick={copyWorkflowYaml}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-all"
                        >
                            {copiedYaml ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            {copiedYaml ? "Copied!" : "Copy YAML"}
                        </button>
                    </div>

                    <pre className="p-4 bg-black/60 rounded-lg border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto max-h-96">
                        {ciResult?.workflow_yaml || `# Execute CI Pipeline to generate .github/workflows/aiforge-ci.yml`}
                    </pre>
                </div>
            )}
        </div>
    );
}
