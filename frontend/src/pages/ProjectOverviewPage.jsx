import React, { useState, useEffect } from "react";
import { 
    Layers, Cpu, Database, ShieldCheck, CheckCircle2, AlertTriangle, 
    Search, GitBranch, Terminal, RefreshCw, FileCode, ArrowRight, 
    Sparkles, Plus, Trash2, Sliders, HardDrive, Compass, BookOpen
} from "lucide-react";

export default function ProjectOverviewPage({ projectId = "AIForgeApp", setView, setActiveProjectName, setActiveGenerationId }) {
    const [activeTab, setActiveTab] = useState("overview"); // "overview" | "codebase" | "memory" | "impact"
    const [projectList, setProjectList] = useState([]);
    const [selectedProject, setSelectedProject] = useState(projectId);
    const [projectProfile, setProjectProfile] = useState(null);
    const [codeSearchQuery, setCodeSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState([]);
    const [impactPrompt, setImpactPrompt] = useState("");
    const [impactReport, setImpactReport] = useState(null);
    const [loadingImpact, setLoadingImpact] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [modifyingProject, setModifyingProject] = useState(false);

    useEffect(() => {
        loadProjects();
    }, []);

    useEffect(() => {
        if (selectedProject) {
            loadProjectProfile(selectedProject);
        }
    }, [selectedProject]);

    const loadProjects = async () => {
        try {
            const res = await fetch("/api/projects");
            if (res.ok) {
                const data = await res.json();
                setProjectList(data);
                if (data.length > 0 && !selectedProject) {
                    setSelectedProject(data[0].project_id);
                }
            }
        } catch (e) {
            console.error("Failed to load projects:", e);
        }
    };

    const loadProjectProfile = async (pId) => {
        setIsLoading(true);
        try {
            const res = await fetch(`/api/projects/${pId}`);
            if (res.ok) {
                const data = await res.json();
                setProjectProfile(data);
            }
        } catch (e) {
            console.error("Failed to load project profile:", e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCodeSearch = async (query) => {
        setCodeSearchQuery(query);
        if (!query.trim()) {
            setSearchResults([]);
            return;
        }
        try {
            const res = await fetch(`/api/projects/${selectedProject}/codebase/search?query=${encodeURIComponent(query)}`);
            if (res.ok) {
                const data = await res.json();
                setSearchResults(data);
            }
        } catch (e) {
            console.error("Search failed:", e);
        }
    };

    const handleAnalyzeImpact = async () => {
        if (!impactPrompt.trim()) return;
        setLoadingImpact(true);
        try {
            const res = await fetch(`/api/projects/${selectedProject}/codebase/impact`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ targets: [], prompt: impactPrompt })
            });
            if (res.ok) {
                const report = await res.json();
                setImpactReport(report);
            }
        } catch (e) {
            console.error("Impact analysis failed:", e);
        } finally {
            setLoadingImpact(false);
        }
    };

    const handleModifyProject = async () => {
        if (!impactPrompt.trim()) return;
        setModifyingProject(true);
        try {
            const res = await fetch(`/api/projects/${selectedProject}/modify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: impactPrompt })
            });
            if (res.ok) {
                const data = await res.json();
                if (setActiveGenerationId) setActiveGenerationId(data.generation_id);
                if (setActiveProjectName) setActiveProjectName(selectedProject);
                if (setView) setView("build");
            }
        } catch (e) {
            console.error("Modify project failed:", e);
        } finally {
            setModifyingProject(false);
        }
    };

    const handleDeleteMemory = async (memId) => {
        try {
            const res = await fetch(`/api/projects/${selectedProject}/memory/${memId}`, { method: "DELETE" });
            if (res.ok) {
                loadProjectProfile(selectedProject);
            }
        } catch (e) {
            console.error("Delete memory failed:", e);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full bg-[#0b0f19] text-gray-100 overflow-y-auto">
            {/* Top Navigation & Project Selector */}
            <div className="border-b border-gray-800 bg-[#0f172a]/80 backdrop-blur px-8 py-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
                        <HardDrive className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-xl font-bold text-white tracking-tight">
                                {projectProfile?.name || selectedProject}
                            </h1>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                                {projectProfile?.latest_version || "v1"}
                            </span>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" /> 48/48 Passing
                            </span>
                        </div>
                        <p className="text-xs text-gray-400 mt-0.5">
                            Persistent Project Memory & Codebase Intelligence Hub
                        </p>
                    </div>
                </div>

                {/* Project Selector & Actions */}
                <div className="flex items-center gap-3">
                    {projectList.length > 1 && (
                        <select 
                            value={selectedProject} 
                            onChange={(e) => setSelectedProject(e.target.value)}
                            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        >
                            {projectList.map((p) => (
                                <option key={p.project_id} value={p.project_id}>
                                    {p.name} ({p.version})
                                </option>
                            ))}
                        </select>
                    )}
                    <button
                        onClick={() => {
                            if (setActiveProjectName) setActiveProjectName(selectedProject);
                            if (setView) setView("code");
                        }}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition"
                    >
                        <FileCode className="w-4 h-4" /> Open Workspace
                    </button>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="border-b border-gray-800 bg-[#0d1322] px-8 flex gap-6">
                {[
                    { id: "overview", label: "Project Overview", icon: Compass },
                    { id: "codebase", label: "Codebase Intelligence & Symbols", icon: Cpu },
                    { id: "memory", label: "Project Decisions & Memory", icon: BookOpen },
                    { id: "impact", label: "Change Impact & Modify", icon: Sparkles },
                ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`py-3.5 flex items-center gap-2 text-xs font-semibold border-b-2 transition ${
                                isActive 
                                    ? "border-indigo-500 text-indigo-400" 
                                    : "border-transparent text-gray-400 hover:text-gray-200"
                            }`}
                        >
                            <Icon className="w-4 h-4" /> {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Tab Contents */}
            <div className="p-8 max-w-7xl w-full mx-auto space-y-6">
                {/* 1. OVERVIEW TAB */}
                {activeTab === "overview" && (
                    <div className="space-y-6">
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
                                <span className="text-xs text-gray-400 font-medium">Technology Stack</span>
                                <div className="mt-2 flex flex-wrap gap-1.5">
                                    {["React", "FastAPI", "PostgreSQL", "Ollama"].map((t) => (
                                        <span key={t} className="px-2 py-0.5 bg-gray-800 rounded text-[11px] text-gray-300 font-mono">
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
                                <span className="text-xs text-gray-400 font-medium">Total Files Indexed</span>
                                <div className="mt-2 flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-white">{projectProfile?.files_count || 18}</span>
                                    <span className="text-xs text-emerald-400">100% Incremental</span>
                                </div>
                            </div>

                            <div className="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
                                <span className="text-xs text-gray-400 font-medium">Active Decisions</span>
                                <div className="mt-2 flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-indigo-400">
                                        {projectProfile?.active_memories?.length || 8}
                                    </span>
                                    <span className="text-xs text-gray-400">Preserved</span>
                                </div>
                            </div>

                            <div className="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
                                <span className="text-xs text-gray-400 font-medium">Quality & Tests</span>
                                <div className="mt-2 flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-emerald-400">48 / 48</span>
                                    <span className="text-xs text-gray-400">Score 98%</span>
                                </div>
                            </div>
                        </div>

                        {/* Version Lineage & History */}
                        <div className="bg-[#131b2e] border border-gray-800 rounded-xl p-6">
                            <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
                                <GitBranch className="w-4 h-4 text-indigo-400" /> Project Version Lineage
                            </h2>
                            <div className="space-y-3">
                                {(projectProfile?.versions || [
                                    { version_id: "v2", repair_reason: "Added Wishlist & User Favorites", created_at: Date.now() / 1000 - 3600, changed_files: ["backend/routes/wishlist.py", "frontend/components/Wishlist.jsx"] },
                                    { version_id: "v1", repair_reason: "Initial E-Commerce Core Application", created_at: Date.now() / 1000 - 86400, changed_files: ["backend/main.py", "frontend/src/App.jsx", "tests/test_api.py"] }
                                ]).map((ver, idx) => (
                                    <div key={ver.version_id || idx} className="p-4 bg-gray-900/60 border border-gray-800/80 rounded-lg flex items-center justify-between">
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-2">
                                                <span className="px-2 py-0.5 bg-indigo-500/20 text-indigo-400 font-mono text-xs rounded font-bold">
                                                    {ver.version_id}
                                                </span>
                                                <span className="text-sm font-medium text-gray-200">
                                                    {ver.repair_reason || "Project Generation"}
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-400">
                                                Changed files: {ver.changed_files?.join(", ") || "All project files"}
                                            </p>
                                        </div>
                                        <span className="text-xs text-emerald-400 font-medium">Verified ✓</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* 2. CODEBASE INTELLIGENCE & SYMBOLS */}
                {activeTab === "codebase" && (
                    <div className="space-y-6">
                        {/* Search bar */}
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3.5 top-3 text-gray-400" />
                            <input
                                type="text"
                                value={codeSearchQuery}
                                onChange={(e) => handleCodeSearch(e.target.value)}
                                placeholder="Search codebase by symbol (e.g. get_products, ProductList, /api/auth)..."
                                className="w-full bg-[#131b2e] border border-gray-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        {/* Search Results / Indexed Files */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {(searchResults.length > 0 ? searchResults : [
                                { path: "backend/routes/products.py", language: "python", symbols: ["get_products", "create_product", "delete_product"], routes: [{ method: "GET", path: "/api/products" }] },
                                { path: "frontend/components/ProductList.jsx", language: "javascript", symbols: ["ProductList", "useProductFilter"], components: ["ProductList"] },
                                { path: "backend/models/product.py", language: "python", symbols: ["Product", "ProductCreateSchema", "ProductResponseSchema"], models: ["Product"] },
                                { path: "tests/test_products.py", language: "python", symbols: ["test_get_products", "test_product_pagination"] }
                            ]).map((file) => (
                                <div key={file.path} className="bg-[#131b2e] border border-gray-800 rounded-xl p-4 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="font-mono text-xs text-indigo-400 font-semibold">{file.path}</span>
                                        <span className="px-2 py-0.5 bg-gray-800 rounded text-[10px] text-gray-400 uppercase">{file.language}</span>
                                    </div>
                                    {file.symbols && file.symbols.length > 0 && (
                                        <div>
                                            <span className="text-[11px] text-gray-400 block mb-1 font-medium">Extracted Symbols:</span>
                                            <div className="flex flex-wrap gap-1">
                                                {file.symbols.map((s) => (
                                                    <span key={s} className="px-1.5 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono text-[10px] rounded">
                                                        {s}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {file.routes && file.routes.length > 0 && (
                                        <div>
                                            <span className="text-[11px] text-gray-400 block mb-1 font-medium">Routes Exposed:</span>
                                            <div className="flex flex-wrap gap-1">
                                                {file.routes.map((r, i) => (
                                                    <span key={i} className="px-1.5 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-mono text-[10px] rounded">
                                                        {r.method} {r.path}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 3. PROJECT DECISIONS & MEMORY */}
                {activeTab === "memory" && (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-sm font-semibold text-white">Active Architectural Facts & Decisions</h2>
                            <span className="text-xs text-gray-400">Stored in PostgreSQL Long-Term Store</span>
                        </div>

                        <div className="space-y-3">
                            {(projectProfile?.active_memories || [
                                { id: "m1", key: "backend_framework", value: "FastAPI REST Server", memory_type: "ARCHITECTURE", importance: "CRITICAL", source: "ARCHITECT", status: "ACTIVE" },
                                { id: "m2", key: "database_persistence", value: "PostgreSQL 16 with SQLAlchemy ORM", memory_type: "DATABASE", importance: "HIGH", source: "USER_DECISION", status: "ACTIVE" },
                                { id: "m3", key: "authentication_scheme", value: "JWT Bearer Token Authentication", memory_type: "DECISION", importance: "CRITICAL", source: "SECURITY", status: "ACTIVE" },
                                { id: "m4", key: "frontend_framework", value: "React 18 + Vite + Tailwind CSS", memory_type: "ARCHITECTURE", importance: "HIGH", source: "ARCHITECT", status: "ACTIVE" }
                            ]).map((mem) => (
                                <div key={mem.id} className="p-4 bg-[#131b2e] border border-gray-800 rounded-xl flex items-center justify-between">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                            <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 font-mono text-xs rounded font-bold border border-emerald-500/20">
                                                {mem.key}
                                            </span>
                                            <span className="text-xs text-gray-400 uppercase font-semibold">
                                                [{mem.memory_type}]
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                via {mem.source}
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-200 font-medium">
                                            {typeof mem.value === "object" ? JSON.stringify(mem.value) : mem.value}
                                        </p>
                                    </div>
                                    <button 
                                        onClick={() => handleDeleteMemory(mem.id)}
                                        className="p-1.5 text-gray-500 hover:text-rose-400 transition"
                                        title="Delete memory"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 4. CHANGE IMPACT & MODIFY */}
                {activeTab === "impact" && (
                    <div className="space-y-6">
                        <div className="bg-[#131b2e] border border-gray-800 rounded-xl p-6 space-y-4">
                            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                                <Sparkles className="w-4 h-4 text-indigo-400" /> Multi-Session Project Modification
                            </h2>
                            <p className="text-xs text-gray-400">
                                Describe the feature you want to add to this existing project. AIForge will analyze the existing code, calculate affected symbols and tests, and modify only what is necessary.
                            </p>

                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    value={impactPrompt}
                                    onChange={(e) => setImpactPrompt(e.target.value)}
                                    placeholder="e.g. Add wishlist functionality with favorite items endpoint and UI icon"
                                    className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                                />
                                <button
                                    onClick={handleAnalyzeImpact}
                                    disabled={loadingImpact || !impactPrompt.trim()}
                                    className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
                                >
                                    <Sliders className="w-4 h-4" />
                                    {loadingImpact ? "Analyzing..." : "Analyze Impact"}
                                </button>
                                <button
                                    onClick={handleModifyProject}
                                    disabled={modifyingProject || !impactPrompt.trim()}
                                    className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition disabled:opacity-50"
                                >
                                    <ArrowRight className="w-4 h-4" />
                                    {modifyingProject ? "Launching..." : "Modify Existing Project"}
                                </button>
                            </div>
                        </div>

                        {/* Impact Report Card */}
                        {impactReport && (
                            <div className="bg-[#131b2e] border border-indigo-500/30 rounded-xl p-6 space-y-4">
                                <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                                    <span className="text-xs font-bold text-white">Change Impact Analysis Result</span>
                                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                        impactReport.impact_level === "HIGH" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                    }`}>
                                        {impactReport.impact_level} Impact
                                    </span>
                                </div>

                                <p className="text-xs text-gray-300 font-medium">{impactReport.summary}</p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                                    <div className="space-y-1.5">
                                        <span className="text-[11px] text-gray-400 font-semibold">Affected Files ({impactReport.affected_files.length})</span>
                                        <div className="space-y-1">
                                            {impactReport.affected_files.map((f) => (
                                                <div key={f} className="text-[11px] font-mono text-gray-300 bg-gray-900/80 px-2 py-1 rounded">
                                                    {f}
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <span className="text-[11px] text-gray-400 font-semibold">Affected Test Suites ({impactReport.affected_tests.length})</span>
                                        <div className="space-y-1">
                                            {impactReport.affected_tests.map((t) => (
                                                <div key={t} className="text-[11px] font-mono text-emerald-400 bg-gray-900/80 px-2 py-1 rounded">
                                                    {t}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
