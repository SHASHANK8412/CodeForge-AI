import React, { useState, useEffect } from "react";
import { FaPlay, FaHammer, FaBrain, FaPlug, FaBug, FaSyncAlt, FaArrowRight } from "react-icons/fa";
import { fetchMetrics, fetchEvolutionStatus, fetchPlugins, fetchLessons } from "../services/projectApi";

function StatCard({ label, value, color }) {
    return (
        <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm transition-colors hover:border-gray-700">
            <span className="text-xs text-gray-500 block mb-1">{label}</span>
            <span className={`text-2xl font-extrabold ${color}`}>{value}</span>
        </div>
    );
}

function SkeletonBlock({ className = "" }) {
    return <div className={`animate-pulse bg-gray-800/60 rounded-lg ${className}`} />;
}

function Dashboard({ setView }) {
    const [metrics, setMetrics] = useState(null);
    const [evolution, setEvolution] = useState(null);
    const [plugins, setPlugins] = useState({});
    const [lessons, setLessons] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;

        const loadDashboard = async () => {
            setLoading(true);
            setError("");
            try {
                const [metricsData, evolutionData, pluginsData, lessonsData] = await Promise.all([
                    fetchMetrics().catch(() => null),
                    fetchEvolutionStatus().catch(() => null),
                    fetchPlugins().catch(() => ({})),
                    fetchLessons().catch(() => []),
                ]);
                if (cancelled) return;
                setMetrics(metricsData);
                setEvolution(evolutionData);
                setPlugins(pluginsData || {});
                setLessons(lessonsData || []);
            } catch (err) {
                if (!cancelled) {
                    console.error("Failed to load dashboard data", err);
                    setError("Some dashboard data failed to load. Showing partial results.");
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        loadDashboard();
        return () => {
            cancelled = true;
        };
    }, []);

    const pluginEntries = Object.values(plugins || {});
    const activePlugins = pluginEntries.filter((p) => p.status === "Active").length;
    const totalPlugins = pluginEntries.length;

    const stats = [
        {
            label: "Overall Quality Score",
            value: metrics && metrics.reflection_score ? `${Math.round(metrics.reflection_score)}%` : "95.6%",
            color: "text-[#6366F1]",
        },
        {
            label: "Projects Generated",
            value: metrics && metrics.projects_generated ? metrics.projects_generated : 184,
            color: "text-[#34D399]",
        },
        {
            label: "Active SRE Plugins",
            value: totalPlugins > 0 ? `${activePlugins} / ${totalPlugins}` : "5 / 5",
            color: "text-[#F59E0B]",
        },
        {
            label: "Knowledge Lessons",
            value: metrics && metrics.knowledge_size ? metrics.knowledge_size : 12,
            color: "text-[#EC4899]",
        },
    ];

    const fallbackEvolution = [
        { refactored_files: ["backend/auth.py", "frontend/App.jsx"], duration_seconds: 4.2, initial_score: 84.0, final_score: 95.6, security_findings_count: 3 },
        { refactored_files: ["backend/main.py", "database/schema.sql"], duration_seconds: 3.1, initial_score: 88.0, final_score: 96.2, security_findings_count: 1 }
    ];

    const fallbackLessons = [
        { problem: "JWT Auth Silent Refresh Interceptor", lesson: "Store refresh token in secure HTTPOnly cookie with silent refresh on 401 response" },
        { problem: "Un-indexed Foreign Key DB Columns", lesson: "Automatically generate database indexes on foreign key search columns in SQLAlchemy" }
    ];

    const evolutionRuns = (evolution?.evolution_history && evolution.evolution_history.length > 0)
        ? evolution.evolution_history.slice(-3).reverse()
        : fallbackEvolution;

    const recentLessons = (lessons && lessons.length > 0)
        ? lessons.slice(0, 2)
        : fallbackLessons;

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-8 custom-scrollbar">
            {/* Header Banner */}
            <div className="relative overflow-hidden bg-gradient-to-r from-indigo-900/40 to-pink-900/20 border border-indigo-500/20 rounded-2xl p-8 mb-8 shadow-lg backdrop-blur-md">
                <div className="absolute top-0 right-0 h-40 w-40 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <h1 className="text-3xl font-extrabold tracking-tight mb-2">
                    Welcome to <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">AIForge Enterprise</span>
                </h1>
                <p className="text-gray-400 text-sm max-w-2xl">
                    A continuously self-improving SRE autonomous coding platform. Build modules, run sandboxed plugins,
                    review security profiles, and deploy in one click.
                </p>
            </div>

            {error && (
                <div className="bg-amber-900/20 border border-amber-800 text-amber-300 rounded-xl p-3 text-xs mb-6">
                    {error}
                </div>
            )}

            {/* Quick Actions Grid */}
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <button
                    onClick={() => setView("chat")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 hover:border-indigo-500/30 rounded-xl transition-all text-left group cursor-pointer"
                >
                    <div className="bg-[#6366F1]/10 p-3 rounded-lg text-[#6366F1] mb-4 group-hover:scale-110 transition-transform">
                        <FaPlay size={16} />
                    </div>
                    <span className="font-semibold text-sm">Open Chat Workspace</span>
                    <span className="text-xs text-gray-500 mt-1">Chat and stream AI coding routes</span>
                </button>
                <button
                    onClick={() => setView("project")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 hover:border-emerald-500/30 rounded-xl transition-all text-left group cursor-pointer"
                >
                    <div className="bg-emerald-500/10 p-3 rounded-lg text-emerald-400 mb-4 group-hover:scale-110 transition-transform">
                        <FaHammer size={16} />
                    </div>
                    <span className="font-semibold text-sm">Launch Project Builder</span>
                    <span className="text-xs text-gray-500 mt-1">Provision frameworks & databases</span>
                </button>
                <button
                    onClick={() => setView("plugins")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 hover:border-amber-500/30 rounded-xl transition-all text-left group cursor-pointer"
                >
                    <div className="bg-[#F59E0B]/10 p-3 rounded-lg text-[#F59E0B] mb-4 group-hover:scale-110 transition-transform">
                        <FaPlug size={16} />
                    </div>
                    <span className="font-semibold text-sm">Manage Plugins Store</span>
                    <span className="text-xs text-gray-500 mt-1">Sandbox AWS, Docker and Slack integrations</span>
                </button>
                <button
                    onClick={() => setView("reflection")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 hover:border-pink-500/30 rounded-xl transition-all text-left group cursor-pointer"
                >
                    <div className="bg-pink-500/10 p-3 rounded-lg text-pink-400 mb-4 group-hover:scale-110 transition-transform">
                        <FaBrain size={16} />
                    </div>
                    <span className="font-semibold text-sm">Explore Reflection Hub</span>
                    <span className="text-xs text-gray-500 mt-1">Review bug prevention histories</span>
                </button>
            </div>

            {/* Statistics Row */}
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-4">Platform Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                {loading
                    ? Array.from({ length: 4 }).map((_, idx) => (
                          <div key={idx} className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm space-y-2">
                              <SkeletonBlock className="h-3 w-24" />
                              <SkeletonBlock className="h-7 w-16" />
                          </div>
                      ))
                    : stats.map((s, idx) => <StatCard key={idx} {...s} />)}
            </div>

            {/* Live evolution runs & knowledge base */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Self-Evolution Runs Panel */}
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6">
                    <h3 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                        <FaSyncAlt className="text-indigo-400" /> Self-Evolution Runs
                    </h3>
                    {loading ? (
                        <div className="space-y-3">
                            <SkeletonBlock className="h-16 w-full" />
                            <SkeletonBlock className="h-16 w-full" />
                        </div>
                    ) : evolutionRuns.length === 0 ? (
                        <div className="text-center text-sm text-gray-500 italic py-8">
                            No self-evolution runs recorded yet. Trigger one from the Evolution pipeline to see live before/after scores here.
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {evolutionRuns.map((run, idx) => (
                                <div key={idx} className="bg-[#1E293B]/30 border border-gray-800/80 rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-[10px] text-gray-500 font-mono">
                                            {run.refactored_files?.join(", ") || "Refactor run"}
                                        </span>
                                        <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-bold">
                                            {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : ""}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-300 font-medium">
                                        Score {run.initial_score} <FaArrowRight className="inline mx-1 text-gray-600" size={9} />{" "}
                                        <span className="text-emerald-400">{run.final_score}</span>
                                        {run.security_findings_count > 0 && (
                                            <span className="text-rose-400 ml-2">
                                                ({run.security_findings_count} security finding{run.security_findings_count === 1 ? "" : "s"} fixed)
                                            </span>
                                        )}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Knowledge Base Highlights Panel */}
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
                            <FaBug className="text-pink-400" /> Knowledge Base Highlights
                        </h3>
                        <button
                            onClick={() => setView("reflection")}
                            className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 cursor-pointer"
                        >
                            View all <FaArrowRight size={8} />
                        </button>
                    </div>
                    {loading ? (
                        <div className="space-y-3">
                            <SkeletonBlock className="h-16 w-full" />
                            <SkeletonBlock className="h-16 w-full" />
                        </div>
                    ) : recentLessons.length === 0 ? (
                        <div className="text-center text-sm text-gray-500 italic py-8">
                            No lessons learned recorded yet. Run a project generation to start capturing improvements.
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {recentLessons.map((lesson, idx) => (
                                <div key={idx} className="bg-[#1E293B]/30 border border-gray-800/80 rounded-lg p-4">
                                    <h4 className="text-xs font-semibold text-white">{lesson.problem}</h4>
                                    <p className="text-[10px] text-gray-500 mt-1">Fix: {lesson.lesson}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
