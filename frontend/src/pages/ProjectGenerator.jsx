import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { 
    FaPlay, FaSpinner, FaCheckCircle, FaDownload, 
    FaChevronRight, FaChevronLeft, FaTasks, FaFolderOpen, FaCopy, FaCheck 
} from "react-icons/fa";

import { generateProjectStream, fetchProjectFileContent } from "../services/projectApi";
import FileExplorer from "../components/FileExplorer";

const TABS = [
    { key: "plan", label: "Plan" },
    { key: "architecture", label: "Architecture" },
    { key: "frontend", label: "Frontend" },
    { key: "backend", label: "Backend" },
    { key: "database", label: "Database" },
    { key: "documentation", label: "Documentation" },
    { key: "tests", label: "Tests" },
    { key: "review", label: "Review" },
];

const STAGE_LABELS = {
    planner: "Planner",
    architect: "Architect",
    frontend: "Frontend",
    backend: "Backend",
    database: "Database",
    documentation: "Documentation",
    testing: "Testing",
    reviewer: "Reviewer",
    completed: "Completed",
};

const STAGE_TO_TAB = {
    planner: "plan",
    architect: "architecture",
    frontend: "frontend",
    backend: "backend",
    database: "database",
    documentation: "documentation",
    testing: "tests",
    reviewer: "review",
};

const STAGES_ORDER = [
    { key: "planner", label: "Planner", desc: "Formulating build specifications" },
    { key: "architect", label: "Architect", desc: "Designing layout & schemas" },
    { key: "frontend", label: "Frontend", desc: "Writing UI pages & components" },
    { key: "backend", label: "Backend", desc: "Generating server APIs & logic" },
    { key: "database", label: "Database", desc: "Drafting schema scripts" },
    { key: "reviewer", label: "Reviewer", desc: "Checking safety & errors" },
    { key: "testing", label: "Testing", desc: "Running unit assertions" },
    { key: "documentation", label: "Documentation", desc: "Structuring README & guides" },
];

function ProjectGenerator() {
    const [prompt, setPrompt] = useState("");
    const [project, setProject] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState(TABS[0].key);
    const [progress, setProgress] = useState({ percent: 0, stage: "" });
    const [currentStageKey, setCurrentStageKey] = useState("");

    // Right Sidebar controls
    const [rightPanelOpen, setRightPanelOpen] = useState(true);
    const [rightPanelTab, setRightPanelTab] = useState("progress"); // "progress" | "explorer"

    // Explorer file viewer states
    const [selectedFile, setSelectedFile] = useState(null); // { path: string, content: string }
    const [fileLoading, setFileLoading] = useState(false);
    const [fileCopied, setFileCopied] = useState(false);

    // Track active project name generated
    const [generatedProjectName, setGeneratedProjectName] = useState("");

    const handleGenerate = async () => {
        if (!prompt.trim() || loading) return;

        setLoading(true);
        setError("");
        setProgress({ percent: 0, stage: "" });
        setCurrentStageKey("");
        setProject({});
        setSelectedFile(null);

        // Normalize folder name estimate
        const safeName = prompt.trim();
        setGeneratedProjectName(safeName);

        try {
            const result = await generateProjectStream(prompt, (event) => {
                setProgress({
                    percent: event.percent,
                    stage: STAGE_LABELS[event.stage] || event.stage,
                });
                
                if (event.stage) {
                    setCurrentStageKey(event.stage);
                }

                // 1. Auto-switch active tab to match the currently generating/updating stage
                if (event.stage && event.stage !== "completed" && event.stage !== "error") {
                    const correspondingTab = STAGE_TO_TAB[event.stage];
                    if (correspondingTab) {
                        setActiveTab(correspondingTab);
                    }
                }

                // 2. Append incoming chunks to project state for live typing effect
                if (event.chunk !== undefined) {
                    const tabKey = STAGE_TO_TAB[event.stage];
                    if (tabKey) {
                        setProject((prev) => {
                            const currentVal = prev?.[tabKey] || "";
                            return {
                                ...prev,
                                [tabKey]: currentVal + event.chunk,
                            };
                        });
                    }
                }

                // 3. Fallback/override with final stage output when it completes
                if (event.output) {
                    setProject((prev) => ({
                        ...prev,
                        ...event.output,
                    }));
                    if (event.output.project_name) {
                        setGeneratedProjectName(event.output.project_name);
                    }
                }
            });

            if (result) {
                setProject(result);
                if (result.project_name) {
                    setGeneratedProjectName(result.project_name);
                }
                // Switch to explorer tab on success
                setRightPanelTab("explorer");
            }
        } catch (err) {
            setError(err.message || "Something went wrong while generating the project.");
        } finally {
            setLoading(false);
        }
    };

    // Handle explorer file select click
    const handleFileSelect = async (projectName, filePath) => {
        setFileLoading(true);
        try {
            const content = await fetchProjectFileContent(projectName, filePath);
            setSelectedFile({ path: filePath, content: content });
            setActiveTab("file_viewer");
        } catch (err) {
            console.error("Failed to load file content", err);
        } finally {
            setFileLoading(false);
        }
    };

    const copyFileCode = () => {
        if (!selectedFile?.content) return;
        navigator.clipboard.writeText(selectedFile.content);
        setFileCopied(true);
        setTimeout(() => setFileCopied(false), 2000);
    };

    const activeContent = project?.[activeTab] || "";

    // Determine status of checklist item
    const getStageStatus = (stageKey) => {
        if (project?.success) return "completed";
        if (!loading && !currentStageKey) return "pending";

        const currentIndex = STAGES_ORDER.findIndex(s => s.key === currentStageKey);
        const stageIndex = STAGES_ORDER.findIndex(s => s.key === stageKey);

        if (currentStageKey === stageKey) return "active";
        if (stageIndex < currentIndex && currentIndex !== -1) return "completed";
        return "pending";
    };

    return (
        <div className="flex-1 flex overflow-hidden bg-[#0B0F19] text-white relative">
            {/* Center Area: Generator & Tabs */}
            <div className="flex-1 flex flex-col min-w-0 overflow-y-auto p-6 space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">🏗️ Project Builder</h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Formulate full applications end-to-end using autonomous agents.
                    </p>
                </div>

                {/* Main Action Form Card */}
                <div className="bg-[#1e293b] border border-gray-800 rounded-2xl p-6 shadow-lg space-y-4">
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder='Describe your software idea (e.g., "Build an E-Commerce API with FastAPI and SQLite")...'
                        rows={3}
                        className="w-full p-4 rounded-xl bg-[#0B0F19] border border-gray-800 text-sm text-white placeholder-gray-500 outline-none focus:border-[#6366F1] transition"
                        disabled={loading}
                    />

                    <div className="flex items-center justify-between">
                        <button
                            onClick={handleGenerate}
                            disabled={loading || !prompt.trim()}
                            className="flex items-center gap-2 bg-[#6366F1] hover:bg-[#5053e1] disabled:bg-gray-800 disabled:cursor-not-allowed text-white font-semibold py-2.5 px-6 rounded-xl transition text-sm cursor-pointer shadow-md shadow-indigo-500/20 active:scale-95"
                        >
                            {loading ? (
                                <>
                                    <FaSpinner className="animate-spin" /> Compiling...
                                </>
                            ) : (
                                <>
                                    <FaPlay size={10} /> Generate Project
                                </>
                            )}
                        </button>

                        {/* Right sidebar toggle */}
                        <button
                            onClick={() => setRightPanelOpen(!rightPanelOpen)}
                            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white px-3 py-2 rounded-lg bg-[#0B0F19] border border-gray-800 transition"
                        >
                            {rightPanelOpen ? <FaChevronRight size={10} /> : <FaChevronLeft size={10} />}
                            <span>{rightPanelOpen ? "Hide Panel" : "Show Panel"}</span>
                        </button>
                    </div>
                </div>

                {/* Progress feedback under main actions if loading */}
                {loading && (
                    <div className="bg-[#1e293b] border border-gray-800 rounded-xl p-4 shadow space-y-3">
                        <div className="flex justify-between items-center text-xs">
                            <span className="text-gray-400">Current Phase: <strong className="text-indigo-400">{progress.stage || "Starting..."}</strong></span>
                            <span className="font-semibold">{progress.percent}%</span>
                        </div>
                        <div className="w-full h-2 bg-[#0B0F19] rounded-full overflow-hidden border border-gray-800">
                            <div
                                className="h-full bg-gradient-to-r from-[#6366F1] to-indigo-400 transition-all duration-500 ease-out"
                                style={{ width: `${progress.percent}%` }}
                            />
                        </div>
                    </div>
                )}

                {error && (
                    <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-xl p-4 text-sm">
                        {error}
                    </div>
                )}

                {project?.success && (
                    <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-[#1e293b] border border-indigo-500/20 p-5 rounded-2xl shadow-lg">
                        <div>
                            <h3 className="text-sm font-bold text-[#6366F1]">🎉 Generation Complete!</h3>
                            <p className="text-xs text-gray-400 mt-0.5">
                                Download the full ZIP archive or browse directories on the right panel.
                            </p>
                        </div>
                        <a
                            href={`http://127.0.0.1:8000/download-project/${encodeURIComponent(generatedProjectName)}`}
                            download
                            className="flex items-center gap-2 bg-[#10B981] hover:bg-emerald-600 text-white font-semibold py-2 px-4 rounded-xl text-xs transition active:scale-95 shadow-md shadow-emerald-500/10"
                        >
                            <FaDownload size={11} /> Download ZIP
                        </a>
                    </div>
                )}

                {/* Main Center Viewer Panel */}
                {project && Object.keys(project).length > 0 && (
                    <div className="bg-[#1e293b] border border-gray-800 rounded-2xl overflow-hidden shadow-xl flex flex-col flex-1 min-h-[400px]">
                        <div className="flex flex-wrap gap-1 p-2 bg-[#0F172A] border-b border-gray-800/80">
                            {/* Dynamically append file viewer tab if active */}
                            {selectedFile && (
                                <button
                                    onClick={() => setActiveTab("file_viewer")}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                                        activeTab === "file_viewer"
                                            ? "bg-[#6366F1] text-white shadow"
                                            : "text-gray-400 hover:text-white"
                                    }`}
                                >
                                    📄 {selectedFile.path.split("/").pop()}
                                </button>
                            )}

                            {TABS.map((tab) => (
                                <button
                                    key={tab.key}
                                    onClick={() => setActiveTab(tab.key)}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                                        activeTab === tab.key
                                            ? "bg-[#6366F1] text-white shadow"
                                            : "text-gray-400 hover:text-white"
                                    }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content Display */}
                        <div className="p-6 overflow-y-auto flex-1 text-sm leading-relaxed max-h-[60vh]">
                            {activeTab === "file_viewer" && selectedFile ? (
                                <div className="space-y-4 h-full flex flex-col">
                                    <div className="flex justify-between items-center pb-2 border-b border-gray-800 text-xs text-gray-400">
                                        <span className="font-mono">{selectedFile.path}</span>
                                        <button
                                            onClick={copyFileCode}
                                            className="flex items-center gap-1.5 hover:text-white transition-colors"
                                        >
                                            {fileCopied ? <FaCheck className="text-emerald-400" /> : <FaCopy />}
                                            <span>{fileCopied ? "Copied" : "Copy Code"}</span>
                                        </button>
                                    </div>
                                    {fileLoading ? (
                                        <div className="flex-1 flex items-center justify-center italic text-gray-500 py-20">
                                            Loading file content...
                                        </div>
                                    ) : (
                                        <div className="rounded-xl overflow-hidden border border-gray-800/80 text-xs">
                                            <SyntaxHighlighter
                                                style={oneDark}
                                                language={selectedFile.path.split(".").pop()}
                                                PreTag="div"
                                                customStyle={{
                                                    margin: 0,
                                                    background: "#0F172A",
                                                    padding: "16px",
                                                }}
                                            >
                                                {selectedFile.content}
                                            </SyntaxHighlighter>
                                        </div>
                                    )}
                                </div>
                            ) : activeContent ? (
                                <div className="prose prose-invert max-w-none text-gray-300">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {activeContent}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                <div className="text-center text-gray-500 italic py-20">
                                    Heuristic generation metrics for this stage are empty or loading...
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Right Collapsible Panel */}
            {rightPanelOpen && (
                <>
                    {/* Backdrop: only shown below the lg breakpoint, tap-to-close */}
                    <div
                        onClick={() => setRightPanelOpen(false)}
                        className="lg:hidden fixed inset-0 bg-black/50 z-10 animate-fade-in"
                    />
                    <div className="w-80 max-w-[85vw] bg-[#111827] border-l border-gray-800 flex flex-col h-full animate-fade-in absolute right-0 top-0 bottom-0 z-20 shadow-2xl lg:static lg:shadow-none">
                    {/* Header Tabs */}
                    <div className="flex border-b border-gray-800 bg-[#0F172A]">
                        <button
                            onClick={() => setRightPanelTab("progress")}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-semibold border-b-2 transition ${
                                rightPanelTab === "progress"
                                    ? "border-[#6366F1] text-white"
                                    : "border-transparent text-gray-400 hover:text-white"
                            }`}
                        >
                            <FaTasks size={11} /> Agent Progress
                        </button>
                        <button
                            onClick={() => setRightPanelTab("explorer")}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-semibold border-b-2 transition ${
                                rightPanelTab === "explorer"
                                    ? "border-[#6366F1] text-white"
                                    : "border-transparent text-gray-400 hover:text-white"
                            }`}
                        >
                            <FaFolderOpen size={11} /> File Explorer
                        </button>
                    </div>

                    {/* Content view switching */}
                    <div className="flex-1 overflow-y-auto min-h-0">
                        {rightPanelTab === "progress" ? (
                            <div className="p-4 space-y-4">
                                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-2">
                                    Workflow Steps
                                </span>

                                <div className="space-y-3">
                                    {STAGES_ORDER.map((stage) => {
                                        const status = getStageStatus(stage.key);
                                        return (
                                            <div
                                                key={stage.key}
                                                className={`flex items-start gap-3 p-3 rounded-xl border transition-all duration-200 ${
                                                    status === "active"
                                                        ? "bg-indigo-500/5 border-[#6366F1]/30 text-indigo-50"
                                                        : status === "completed"
                                                        ? "bg-[#1E293B]/20 border-gray-800/60 text-gray-400"
                                                        : "bg-transparent border-transparent text-gray-600"
                                                }`}
                                            >
                                                <div className="mt-0.5">
                                                    {status === "completed" && (
                                                        <FaCheckCircle className="text-emerald-500" size={14} />
                                                    )}
                                                    {status === "active" && (
                                                        <FaSpinner className="text-[#6366F1] animate-spin" size={14} />
                                                    )}
                                                    {status === "pending" && (
                                                        <div className="h-3.5 w-3.5 rounded-full border-2 border-gray-800 flex items-center justify-center text-[8px]" />
                                                    )}
                                                </div>
                                                <div>
                                                    <h4 className={`text-xs font-bold ${
                                                        status === "active" ? "text-[#6366F1]" : status === "completed" ? "text-gray-300" : "text-gray-500"
                                                    }`}>
                                                        {stage.label}
                                                    </h4>
                                                    <p className="text-[10px] text-gray-500 mt-0.5">
                                                        {stage.desc}
                                                    </p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <FileExplorer
                                activeProjectName={generatedProjectName}
                                onFileSelect={handleFileSelect}
                                onProjectChange={(proj) => {
                                    setGeneratedProjectName(proj);
                                    setSelectedFile(null);
                                }}
                            />
                        )}
                    </div>
                    </div>
                </>
            )}
        </div>
    );
}

export default ProjectGenerator;
