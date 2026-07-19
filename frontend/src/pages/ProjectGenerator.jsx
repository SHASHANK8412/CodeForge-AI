import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { generateProjectStream } from "../services/projectApi";

const TABS = [
    { key: "plan", label: "Plan" },
    { key: "architecture", label: "Architecture" },
    { key: "frontend", label: "Frontend" },
    { key: "backend", label: "Backend" },
    { key: "database", label: "Database" },
    { key: "documentation", label: "Documentation" },
    { key: "tests", label: "Tests" },
    { key: "review", label: "Review" },
    { key: "github", label: "GitHub" },
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
    github: "GitHub",
    completed: "Completed",
};

// Map SSE event stage to tab keys to support auto-switching
const STAGE_TO_TAB = {
    planner: "plan",
    architect: "architecture",
    frontend: "frontend",
    backend: "backend",
    database: "database",
    documentation: "documentation",
    testing: "tests",
    reviewer: "review",
    github: "github",
};

function ProjectGenerator() {
    const [prompt, setPrompt] = useState("");
    const [project, setProject] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState(TABS[0].key);
    const [progress, setProgress] = useState({ percent: 0, stage: "" });

    async function handleGenerate() {
        if (!prompt.trim() || loading) return;

        setLoading(true);
        setError("");
        setProgress({ percent: 0, stage: "" });
        setProject({}); // Clear previous generation results and init empty object

        try {
            const result = await generateProjectStream(prompt, (event) => {
                setProgress({
                    percent: event.percent,
                    stage: STAGE_LABELS[event.stage] || event.stage,
                });

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
                }
            });

            if (result) {
                setProject(result);
            }
        } catch (err) {
            setError(err.message || "Something went wrong while generating the project.");
        } finally {
            setLoading(false);
        }
    }

    const activeContent = project?.[activeTab] || "";

    return (
        <div className="max-w-6xl mx-auto p-8 text-white">
            <h1 className="text-4xl font-bold mb-2">🏗️ AIForge Project Generator</h1>
            <p className="text-gray-400 mb-6">
                Describe a full application and let the multi-agent pipeline plan,
                design, build, document, test and review it end-to-end.
            </p>

            <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder='e.g. "Build an E-Commerce Website"'
                rows={4}
                className="w-full p-4 rounded-xl bg-[#40414F] text-white outline-none"
            />

            <button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="mt-4 bg-green-600 disabled:bg-green-900 disabled:cursor-not-allowed px-6 py-3 rounded-xl font-semibold"
            >
                {loading ? "Generating Project..." : "Generate Project"}
            </button>

            {loading && (
                <div className="mt-6">
                    <div className="flex justify-between text-sm text-gray-300 mb-2">
                        <span>{progress.stage ? `${progress.stage}...` : "Starting..."}</span>
                        <span>{progress.percent}%</span>
                    </div>
                    <div className="w-full h-3 bg-[#40414F] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-green-600 transition-all duration-500 ease-out"
                            style={{ width: `${progress.percent}%` }}
                        />
                    </div>
                </div>
            )}

            {error && (
                <div className="mt-6 bg-red-900/50 border border-red-700 text-red-200 rounded-xl p-4">
                    {error}
                </div>
            )}

            {project?.error && (
                <div className="mt-6 bg-yellow-900/40 border border-yellow-700 text-yellow-200 rounded-xl p-4 whitespace-pre-wrap">
                    ⚠️ Partial failure during generation:
                    {"\n"}
                    {project.error}
                </div>
            )}

            {project?.success && (
                <div className="mt-6 flex flex-col md:flex-row gap-4 items-center justify-between bg-[#343541] border border-green-600/30 p-6 rounded-xl shadow-lg">
                    <div>
                        <h3 className="text-lg font-bold text-green-400">🎉 Project Assembly Complete!</h3>
                        <p className="text-gray-400 text-sm mt-1">
                            Download your project folders structured with configs and ready for local development.
                        </p>
                    </div>
                    <a
                        href={`http://127.0.0.1:8000/download-project/${encodeURIComponent(project.project_name || prompt)}`}
                        download
                        className="bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-xl font-bold transition-all text-center flex items-center gap-2 w-full md:w-auto justify-center"
                    >
                        📥 Download Project ZIP
                    </a>
                </div>
            )}

            {project && Object.keys(project).length > 0 && (
                <div className="mt-8 bg-[#444654] rounded-xl overflow-hidden">
                    <div className="flex flex-wrap gap-1 p-2 bg-[#343541] border-b border-gray-700">
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    activeTab === tab.key
                                        ? "bg-green-600 text-white"
                                        : "text-gray-300 hover:bg-[#40414F]"
                                }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    <div className="p-6 max-h-[70vh] overflow-y-auto">
                        {activeContent ? (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {activeContent}
                            </ReactMarkdown>
                        ) : (
                            <p className="text-gray-400">No output for this stage.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default ProjectGenerator;
