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
    ExternalLink
} from "lucide-react";
import axios from "axios";

const PIPELINE_STEPS = [
    { id: "Starting Docker Sandbox", label: "Docker Sandbox", icon: Server, emoji: "🐳", desc: "Initialize container with CPU/RAM caps" },
    { id: "Preparing project", label: "Preparing project", icon: Layers, emoji: "📦", desc: "Isolate temporary workspace sandbox" },
    { id: "Installing dependencies", label: "Installing dependencies", icon: Cpu, emoji: "📥", desc: "Auto-detect package manager & resolve packages" },
    { id: "Running tests", label: "Running tests", icon: Play, emoji: "🧪", desc: "Execute pytest / npm test suites" },
    { id: "Tests passed", label: "Tests passed", icon: CheckCircle2, emoji: "✅", desc: "Verification passed with 0 failures" },
    { id: "Tests failed", label: "Tests failed", icon: XCircle, emoji: "❌", desc: "Failure identified in test suite" },
    { id: "Debugging", label: "Debugging", icon: Activity, emoji: "🤖", desc: "Debug Agent diagnosing root causes" },
    { id: "Applying fix", label: "Applying fix", icon: Wrench, emoji: "🔧", desc: "Apply synthesized patches to files" },
    { id: "Retesting", label: "Retesting", icon: RotateCw, emoji: "🔄", desc: "Re-run sandbox test validation" },
    { id: "Final result", label: "Final result", icon: Shield, emoji: "🏁", desc: "Validation report & production readiness" },
];

const DEMO_PROJECTS = {
    python_fastapi: {
        name: "FastAPI E-Commerce API",
        type: "python",
        files: {
            "backend/main.py": `from fastapi import FastAPI, HTTPException\n\napp = FastAPI(title="Store API")\n\n@app.get("/health")\ndef health():\n    return {"status": "ok", "service": "store"}\n\n@app.get("/items/{item_id}")\ndef get_item(item_id: int):\n    if item_id <= 0:\n        raise HTTPException(status_code=400, detail="Invalid ID")\n    return {"id": item_id, "name": f"Product #{item_id}", "in_stock": True}\n`,
            "tests/test_main.py": `import pytest\nfrom backend.main import health, get_item\n\ndef test_health():\n    res = health()\n    assert res["status"] == "ok"\n\ndef test_get_item():\n    res = get_item(10)\n    assert res["id"] == 10\n    assert res["in_stock"] is True\n`,
            "requirements.txt": "fastapi>=0.100.0\npytest>=7.0.0\n"
        }
    },
    python_self_heal: {
        name: "Python Self-Healing Demo (Syntax / Assertion Repair)",
        type: "python",
        files: {
            "backend/main.py": `def calculate_discount(price, pct):\n    # Intentional bug: subtracting wrong variable\n    return price - (price * (pct / 100.0))\n\ndef get_service_status():\n    return {'status': 'READY'}\n`,
            "tests/test_calc.py": `from backend.main import calculate_discount, get_service_status\n\ndef test_discount():\n    assert calculate_discount(100, 20) == 80.0\n    assert calculate_discount(200, 50) == 100.0\n\ndef test_status():\n    assert get_service_status()['status'] == 'READY'\n`,
            "requirements.txt": "pytest\n"
        }
    },
    react_vite: {
        name: "React / Vite Dashboard",
        type: "javascript",
        files: {
            "package.json": JSON.stringify({
                name: "vite-dashboard",
                version: "1.0.0",
                scripts: {
                    build: "vite build",
                    test: "node -e \"console.log('✔ Vite Component Tests: 4 passed'); process.exit(0);\""
                },
                dependencies: {
                    react: "^18.2.0",
                    "react-dom": "^18.2.0"
                }
            }, null, 2),
            "src/App.jsx": "export default function App() { return <div><h1>AIForge Vite App</h1></div>; }",
            "index.html": "<!DOCTYPE html><html><body><div id='root'></div></body></html>"
        }
    }
};

export default function ExecutionValidationView({ defaultProject = "python_fastapi" }) {
    const [selectedKey, setSelectedKey] = useState(defaultProject);
    const [executionBackend, setExecutionBackend] = useState("local"); // 'local' | 'docker'
    const [memoryLimit, setMemoryLimit] = useState("512m");
    const [cpuLimit, setCpuLimit] = useState("1.0");
    const [networkMode, setNetworkMode] = useState("none");
    const [isRunning, setIsRunning] = useState(false);
    const [currentStep, setCurrentStep] = useState(null);
    const [stepHistory, setStepHistory] = useState([]);
    const [consoleLogs, setConsoleLogs] = useState([]);
    const [finalReport, setFinalReport] = useState(null);
    const [maxRetries, setMaxRetries] = useState(3);
    const [timeoutSeconds, setTimeoutSeconds] = useState(30);
    const [activeTab, setActiveTab] = useState("pipeline"); // pipeline, console, files, report
    const terminalRef = useRef(null);

    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [consoleLogs]);

    const activeProject = DEMO_PROJECTS[selectedKey] || DEMO_PROJECTS.python_fastapi;

    const runValidation = async () => {
        setIsRunning(true);
        setCurrentStep(executionBackend === "docker" ? "Starting Docker Sandbox" : "Preparing project");
        setStepHistory([]);
        setConsoleLogs([
            executionBackend === "docker"
                ? "🐳 Initializing Docker-Based Isolated Code Execution Sandbox..."
                : "🚀 Initializing Autonomous Code Execution & Validation Pipeline..."
        ]);
        setFinalReport(null);

        const payload = {
            files: activeProject.files,
            timeout_seconds: Number(timeoutSeconds),
            max_repair_attempts: Number(maxRetries),
            install_dependencies: true,
            docker_enabled: executionBackend === "docker",
            execution_backend: executionBackend,
            memory_limit: memoryLimit,
            cpu_limit: Number(cpuLimit),
            network_mode: networkMode
        };

        const projectId = activeProject.name.toLowerCase().replace(/[^a-z0-9]/g, "_");

        try {
            // Direct REST endpoint validation
            const response = await axios.post(`/api/projects/${projectId}/autonomous-validate`, payload);
            if (response.data && response.data.report) {
                const rep = response.data.report;
                setFinalReport(rep);
                setStepHistory(rep.steps || []);

                const logs = ["✔ Validation completed."];
                rep.steps?.forEach((st) => {
                    logs.push(`[${st.step}] Status: ${st.status} (Code: ${st.exit_code}, ${st.duration_ms}ms)`);
                    if (st.command) logs.push(`$ ${st.command}`);
                    if (st.stdout) logs.push(st.stdout);
                    if (st.stderr) logs.push(`[ERR] ${st.stderr}`);
                });
                setConsoleLogs(logs);

                if (rep.is_production_ready) {
                    setCurrentStep("Final result");
                } else {
                    setCurrentStep(rep.steps?.[rep.steps.length - 1]?.step || "Final result");
                }
            }
        } catch (err) {
            const errMsg = err.response?.data?.detail || err.message;
            setConsoleLogs((prev) => [...prev, `❌ Error during validation: ${errMsg}`]);
        } finally {
            setIsRunning(false);
        }
    };

    const getStepStatus = (stepId) => {
        if (currentStep === stepId && isRunning) return "active";
        const found = stepHistory.find((s) => s.step === stepId);
        if (!found) return "pending";
        return found.status === "FAILED" ? "failed" : "completed";
    };

    return (
        <div className="flex flex-col h-full bg-[#0a0d14] text-slate-200 p-6 overflow-y-auto space-y-6">
            {/* Top Bar Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
                <div>
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 shadow-lg shadow-indigo-500/10">
                            <Shield className="w-6 h-6 animate-pulse" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                                Autonomous Code Execution & Validation
                                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
                                    Active Engine
                                </span>
                            </h1>
                            <p className="text-sm text-slate-400 mt-0.5">
                                Isolated sandbox execution, real-time dependency builds, test suites & automated repair cycles
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                    {/* Backend Selection */}
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

                    {/* Docker Limits Config */}
                    {executionBackend === "docker" && (
                        <div className="flex items-center gap-2 bg-slate-900/90 border border-cyan-500/30 rounded-lg px-2.5 py-1 text-xs text-slate-300 animate-fadeIn">
                            <span className="text-cyan-400 font-semibold flex items-center gap-1">
                                <Server className="w-3.5 h-3.5" /> Docker:
                            </span>
                            <select
                                value={memoryLimit}
                                onChange={(e) => setMemoryLimit(e.target.value)}
                                disabled={isRunning}
                                className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-1.5 py-0.5 text-[11px]"
                            >
                                <option value="256m">256MB RAM</option>
                                <option value="512m">512MB RAM</option>
                                <option value="1g">1GB RAM</option>
                            </select>
                            <select
                                value={cpuLimit}
                                onChange={(e) => setCpuLimit(e.target.value)}
                                disabled={isRunning}
                                className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-1.5 py-0.5 text-[11px]"
                            >
                                <option value="0.5">0.5 CPU</option>
                                <option value="1.0">1.0 CPU</option>
                                <option value="2.0">2.0 CPU</option>
                            </select>
                            <select
                                value={networkMode}
                                onChange={(e) => setNetworkMode(e.target.value)}
                                disabled={isRunning}
                                className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-1.5 py-0.5 text-[11px]"
                            >
                                <option value="none">Net: None</option>
                                <option value="bridge">Net: Bridge</option>
                            </select>
                        </div>
                    )}

                    <select
                        value={selectedKey}
                        onChange={(e) => setSelectedKey(e.target.value)}
                        disabled={isRunning}
                        className="bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                    >
                        <option value="python_fastapi">Python (FastAPI + Pytest)</option>
                        <option value="python_self_heal">Python (Self-Healing Loop Demo)</option>
                        <option value="react_vite">React / Vite (JavaScript)</option>
                    </select>

                    <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-400">
                        <span>Retries:</span>
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
                        onClick={runValidation}
                        disabled={isRunning}
                        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all shadow-lg ${
                            isRunning
                                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                                : executionBackend === "docker"
                                ? "bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-cyan-600/25"
                                : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-indigo-600/25"
                        }`}
                    >
                        {isRunning ? (
                            <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                                Validating...
                            </>
                        ) : (
                            <>
                                <Play className="w-3.5 h-3.5 fill-white" />
                                {executionBackend === "docker" ? "Run Docker Sandbox" : "Run Autonomous Validation"}
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Stage Progress Bar / Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-10 gap-2">
                {PIPELINE_STEPS.map((step, idx) => {
                    const status = getStepStatus(step.id);
                    const StepIcon = step.icon;

                    let badgeClasses = "border-slate-800 bg-slate-900/40 text-slate-500";
                    let iconClasses = "text-slate-500";

                    if (status === "active") {
                        badgeClasses = "border-indigo-500/60 bg-indigo-950/40 text-indigo-300 ring-1 ring-indigo-500/40 animate-pulse";
                        iconClasses = "text-indigo-400";
                    } else if (status === "completed") {
                        badgeClasses = "border-emerald-500/40 bg-emerald-950/20 text-emerald-300";
                        iconClasses = "text-emerald-400";
                    } else if (status === "failed") {
                        badgeClasses = "border-rose-500/40 bg-rose-950/20 text-rose-300";
                        iconClasses = "text-rose-400";
                    }

                    return (
                        <div
                            key={step.id}
                            className={`flex flex-col justify-between p-2.5 rounded-xl border transition-all ${badgeClasses}`}
                        >
                            <div className="flex items-center justify-between mb-1.5">
                                <span className="text-[10px] font-mono text-slate-400">
                                    {step.emoji}
                                </span>
                                <StepIcon className={`w-3.5 h-3.5 ${iconClasses}`} />
                            </div>
                            <div>
                                <h4 className="text-[11px] font-semibold leading-tight">{step.label}</h4>
                                <p className="text-[9px] text-slate-400 line-clamp-1 mt-0.5">{step.desc}</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Main Content Area: Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800">
                {[
                    { id: "pipeline", label: "Pipeline Status", icon: Activity },
                    { id: "console", label: "Sandbox Terminal", icon: Terminal },
                    { id: "report", label: "Validation Report", icon: Shield },
                    { id: "files", label: "Project Files", icon: FileCode },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
                            activeTab === tab.id
                                ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
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
                    {/* Steps Execution History */}
                    <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                <Activity className="w-4 h-4 text-indigo-400" />
                                Execution Trace & Diagnostics
                            </h3>
                            {finalReport && (
                                <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${
                                    finalReport.is_production_ready
                                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                                        : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                                }`}>
                                    {finalReport.overall_status} ({finalReport.attempts_count} Cycle{finalReport.attempts_count > 1 ? "s" : ""})
                                </span>
                            )}
                        </div>

                        {stepHistory.length === 0 ? (
                            <div className="py-12 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
                                Ready to execute. Click &quot;Run Autonomous Validation&quot; to begin.
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {stepHistory.map((step, i) => (
                                    <div
                                        key={i}
                                        className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-950/40 text-xs space-y-1.5"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 font-medium text-slate-200">
                                                {step.status === "SUCCESS" ? (
                                                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                                ) : (
                                                    <XCircle className="w-4 h-4 text-rose-400" />
                                                )}
                                                <span>{step.step}</span>
                                            </div>
                                            <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                                                <span>Exit: {step.exit_code}</span>
                                                <span>{step.duration_ms}ms</span>
                                            </div>
                                        </div>

                                        {step.command && (
                                            <div className="font-mono text-[11px] text-indigo-300 bg-indigo-950/30 px-2.5 py-1 rounded border border-indigo-900/30">
                                                $ {step.command}
                                            </div>
                                        )}

                                        {step.error_message && (
                                            <div className="text-rose-400 text-[11px] flex items-center gap-1.5">
                                                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                                                {step.error_message}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Applied Fixes & Self-Healing Summary */}
                    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                            <Wrench className="w-4 h-4 text-violet-400" />
                            Autonomous Self-Healing Patches
                        </h3>

                        {finalReport?.applied_fixes?.length > 0 ? (
                            <div className="space-y-3">
                                {finalReport.applied_fixes.map((fix, idx) => (
                                    <div
                                        key={idx}
                                        className="p-3.5 rounded-lg border border-violet-500/20 bg-violet-950/10 text-xs space-y-1"
                                    >
                                        <div className="flex items-center justify-between text-violet-300 font-medium">
                                            <span>Cycle {fix.attempt}: [{fix.error_type}]</span>
                                            <span className="text-[10px] text-slate-400 font-mono">
                                                Confidence: {Math.round(fix.confidence * 100)}%
                                            </span>
                                        </div>
                                        <p className="text-slate-300 text-[11px]">{fix.root_cause}</p>
                                        {fix.modified_files?.length > 0 && (
                                            <div className="mt-2 text-[10px] text-slate-400">
                                                Modified: <span className="font-mono text-indigo-300">{fix.modified_files.join(", ")}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                                {finalReport
                                    ? "No repair patches required. Code passed on initial execution!"
                                    : "Self-healing patches will appear here if tests fail."}
                            </div>
                        )}

                        <div className="border-t border-slate-800/80 pt-3 text-xs text-slate-400 space-y-1">
                            <div className="flex justify-between">
                                <span>Sandbox Backend:</span>
                                <span className="font-mono text-cyan-400 font-medium">
                                    {finalReport?.backend_used === "docker" || executionBackend === "docker"
                                        ? "🐳 Docker Container"
                                        : "💻 Local Subprocess"}
                                </span>
                            </div>
                            {executionBackend === "docker" && (
                                <>
                                    <div className="flex justify-between">
                                        <span>Resource Limits:</span>
                                        <span className="text-slate-200">{memoryLimit} RAM • {cpuLimit} CPU</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Network Isolation:</span>
                                        <span className="text-emerald-400">Mode: {networkMode}</span>
                                    </div>
                                    {finalReport?.container_id && (
                                        <div className="flex justify-between">
                                            <span>Container ID:</span>
                                            <span className="font-mono text-[10px] text-indigo-300">{finalReport.container_id}</span>
                                        </div>
                                    )}
                                </>
                            )}
                            <div className="flex justify-between">
                                <span>Environment:</span>
                                <span className="text-emerald-400">Isolated & Scrubbed</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Timeout Enforcement:</span>
                                <span className="text-slate-200">{timeoutSeconds}s per command</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Tab: Terminal Console */}
            {activeTab === "console" && (
                <div className="bg-[#0b0e14] border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col h-96">
                    <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between text-xs text-slate-400">
                        <div className="flex items-center gap-2">
                            <Terminal className="w-4 h-4 text-emerald-400" />
                            <span className="font-mono">Sandbox Console Stream (stdout / stderr)</span>
                        </div>
                        <span className="text-[11px] text-slate-500 font-mono">UTF-8 • shell=False</span>
                    </div>

                    <div
                        ref={terminalRef}
                        className="p-4 font-mono text-xs text-slate-300 space-y-1 overflow-y-auto flex-1 bg-black/40 selection:bg-indigo-500 selection:text-white"
                    >
                        {consoleLogs.map((log, i) => (
                            <div
                                key={i}
                                className={
                                    log.startsWith("[ERR]") || log.includes("Error") || log.includes("FAILED")
                                        ? "text-rose-400"
                                        : log.startsWith("$")
                                        ? "text-emerald-400 font-semibold"
                                        : log.startsWith("✔")
                                        ? "text-cyan-400"
                                        : "text-slate-300"
                                }
                            >
                                {log}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Tab: Validation Report */}
            {activeTab === "report" && (
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 shadow-xl space-y-5">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                        <div>
                            <h3 className="text-base font-bold text-white">Final Validation & Production Readiness Report</h3>
                            <p className="text-xs text-slate-400 mt-0.5">Automated quality gate verification output</p>
                        </div>
                        {finalReport && (
                            <div className="flex items-center gap-3">
                                <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                                    finalReport.is_production_ready
                                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                                        : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                                }`}>
                                    {finalReport.is_production_ready ? "READY FOR EXPORT" : "REPAIRS PENDING"}
                                </span>
                            </div>
                        )}
                    </div>

                    {finalReport ? (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                            <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
                                <span className="text-slate-400">Total Duration</span>
                                <div className="text-base font-bold text-white mt-1">{finalReport.total_duration_ms} ms</div>
                            </div>
                            <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
                                <span className="text-slate-400">Repair Cycles</span>
                                <div className="text-base font-bold text-indigo-400 mt-1">{finalReport.attempts_count} / {finalReport.max_attempts}</div>
                            </div>
                            <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
                                <span className="text-slate-400">Files Patched</span>
                                <div className="text-base font-bold text-emerald-400 mt-1">{finalReport.files_modified?.length || 0}</div>
                            </div>
                            <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
                                <span className="text-slate-400">Status</span>
                                <div className="text-base font-bold text-slate-200 mt-1">{finalReport.overall_status}</div>
                            </div>
                        </div>
                    ) : (
                        <div className="py-12 text-center text-slate-500 text-xs">
                            No validation run yet. Trigger validation to inspect complete metrics.
                        </div>
                    )}
                </div>
            )}

            {/* Tab: Project Files */}
            {activeTab === "files" && (
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-xl space-y-4">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-indigo-400" />
                        Target Project Files ({Object.keys(activeProject.files).length})
                    </h3>
                    <div className="space-y-3">
                        {Object.entries(activeProject.files).map(([path, content]) => (
                            <div key={path} className="border border-slate-800 rounded-lg overflow-hidden">
                                <div className="bg-slate-950 px-3.5 py-1.5 font-mono text-xs text-indigo-300 border-b border-slate-800">
                                    {path}
                                </div>
                                <pre className="p-3 bg-black/40 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                                    {content}
                                </pre>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
