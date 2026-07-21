import React from "react";
import { FaPlay, FaHammer, FaBrain, FaPlug, FaTrophy, FaBug, FaSyncAlt } from "react-icons/fa";

function Dashboard({ setView }) {
    // Mock dashboard metrics matches Level 9 requirements
    const stats = [
        { label: "Overall Quality Score", value: "96%", color: "text-[#6366F1]" },
        { label: "Projects Completed", value: "20", color: "text-[#34D399]" },
        { label: "Active SRE Plugins", value: "8 / 12", color: "text-[#F59E0B]" },
        { label: "Knowledge Nodes", value: "650+", color: "text-[#EC4899]" }
    ];

    const recentBugs = [
        { desc: "JWT Signature Mismatch", cause: "UTF-8 secret encoding", fix: "Auto-Resolved" },
        { desc: "SQL injection in router decorator", cause: "Raw query binds", fix: "Parameterized query applied" }
    ];

    const promptEvolutions = [
        { old: "Build a dashboard.", new: "Build a scalable React dashboard using RBAC, charts, and lazy loading.", version: "v1.4" },
        { old: "Create authentication.", new: "Build production-grade JWT authentication with secure cookies and hashing.", version: "v1.2" }
    ];

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-8 custom-scrollbar">
            {/* Header Banner */}
            <div className="relative overflow-hidden bg-gradient-to-r from-indigo-900/40 to-pink-900/20 border border-indigo-500/20 rounded-2xl p-8 mb-8 shadow-lg backdrop-blur-md">
                <div className="absolute top-0 right-0 h-40 w-40 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <h1 className="text-3xl font-extrabold tracking-tight mb-2">
                    Welcome to <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">AIForge Enterprise</span>
                </h1>
                <p className="text-gray-400 text-sm max-w-2xl">
                    A continuously self-improving SRE autonomous coding platform. Build modules, run sandboxed plugins, review security profiles, and deploy in one click.
                </p>
            </div>

            {/* Quick Actions Grid */}
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <button 
                    onClick={() => setView("chat")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 rounded-xl transition text-left group"
                >
                    <div className="bg-[#6366F1]/10 p-3 rounded-lg text-[#6366F1] mb-4 group-hover:scale-110 transition">
                        <FaPlay size={16} />
                    </div>
                    <span className="font-semibold text-sm">Open Chat Workspace</span>
                    <span className="text-xs text-gray-500 mt-1">Chat and stream AI coding routes</span>
                </button>
                <button 
                    onClick={() => setView("project")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 rounded-xl transition text-left group"
                >
                    <div className="bg-emerald-500/10 p-3 rounded-lg text-emerald-400 mb-4 group-hover:scale-110 transition">
                        <FaHammer size={16} />
                    </div>
                    <span className="font-semibold text-sm">Launch Project Builder</span>
                    <span className="text-xs text-gray-500 mt-1">Provision frameworks & databases</span>
                </button>
                <button 
                    onClick={() => setView("plugins")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 rounded-xl transition text-left group"
                >
                    <div className="bg-[#F59E0B]/10 p-3 rounded-lg text-[#F59E0B] mb-4 group-hover:scale-110 transition">
                        <FaPlug size={16} />
                    </div>
                    <span className="font-semibold text-sm">Manage Plugins Store</span>
                    <span className="text-xs text-gray-500 mt-1">Sandbox AWS, Docker and Slack integrations</span>
                </button>
                <button 
                    onClick={() => setView("reflection")}
                    className="flex flex-col items-start p-5 bg-[#1E293B]/40 hover:bg-[#1E293B]/70 border border-gray-800 rounded-xl transition text-left group"
                >
                    <div className="bg-pink-500/10 p-3 rounded-lg text-pink-400 mb-4 group-hover:scale-110 transition">
                        <FaBrain size={16} />
                    </div>
                    <span className="font-semibold text-sm">Explore Reflection Hub</span>
                    <span className="text-xs text-gray-500 mt-1">Review bug prevention histories</span>
                </button>
            </div>

            {/* Statistics Row */}
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-4">Platform Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                {stats.map((s, idx) => (
                    <div key={idx} className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                        <span className="text-xs text-gray-500 block mb-1">{s.label}</span>
                        <span className={`text-2xl font-extrabold ${s.color}`}>{s.value}</span>
                    </div>
                ))}
            </div>

            {/* Experience levels & Evolved Prompts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Evolved Prompts Panel */}
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6">
                    <h3 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                        <FaSyncAlt className="text-indigo-400 animate-spin-slow" /> Evolved Directives (Prompt Evolution)
                    </h3>
                    <div className="space-y-4">
                        {promptEvolutions.map((pe, idx) => (
                            <div key={idx} className="bg-[#1E293B]/30 border border-gray-800/80 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-[10px] text-gray-500 font-mono">Original: "{pe.old}"</span>
                                    <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-bold">{pe.version}</span>
                                </div>
                                <p className="text-xs text-gray-300 font-medium">
                                    Evolved to: <span className="text-emerald-400">"{pe.new}"</span>
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bug Intelligence Panel */}
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6">
                    <h3 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                        <FaBug className="text-pink-400" /> Bug Memory Database
                    </h3>
                    <div className="space-y-4">
                        {recentBugs.map((bug, idx) => (
                            <div key={idx} className="bg-[#1E293B]/30 border border-gray-800/80 rounded-lg p-4 flex justify-between items-center">
                                <div>
                                    <h4 className="text-xs font-semibold text-white">{bug.desc}</h4>
                                    <p className="text-[10px] text-gray-500 mt-1">Cause: {bug.cause}</p>
                                </div>
                                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-bold">
                                    {bug.fix}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
