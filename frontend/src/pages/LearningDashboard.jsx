import React from "react";
import { FaBrain, FaSyncAlt, FaBug, FaCube, FaChartLine } from "react-icons/fa";

function LearningDashboard() {
    const minedPatterns = [
        "CRUD Operations", "Authentication", "Pagination", "Search",
        "REST APIs", "React Hooks", "FastAPI Routers"
    ];

    const lessons = [
        { project: "Inventory System", problem: "Too many database queries", fix: "Use JOIN to avoid N+1 queries" },
        { project: "Todo App", problem: "JWT validation latency", fix: "Configure fast verification filters" }
    ];

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-8 custom-scrollbar">
            <div className="mb-6">
                <h1 className="text-2xl font-extrabold flex items-center gap-2">
                    <FaBrain className="text-indigo-400 animate-pulse" /> Self-Learning & Knowledge Hub
                </h1>
                <p className="text-gray-400 text-xs mt-1">
                    AIForge extracts architectures and merges lessons learned from every run automatically.
                </p>
            </div>

            {/* Pattern Library */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Patterns Card */}
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6 md:col-span-1">
                    <h3 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                        <FaCube className="text-indigo-400" /> Mined Patterns
                    </h3>
                    <div className="flex flex-wrap gap-2">
                        {minedPatterns.map((pat, idx) => (
                            <span key={idx} className="text-xs bg-[#1E293B] text-gray-300 px-2.5 py-1 rounded-full border border-gray-800">
                                {pat}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Lessons Learned */}
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6 md:col-span-2">
                    <h3 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                        <FaChartLine className="text-emerald-400" /> Lessons Learned & Optimizations
                    </h3>
                    <div className="space-y-4">
                        {lessons.map((l, idx) => (
                            <div key={idx} className="bg-[#1E293B]/30 border border-gray-800/80 rounded-lg p-4">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-xs font-semibold text-white">{l.project}</span>
                                    <span className="text-[10px] text-gray-500 font-mono">RESOLVED</span>
                                </div>
                                <p className="text-xs text-gray-400">Issue: {l.problem}</p>
                                <p className="text-xs text-emerald-400 mt-1">Fix applied: {l.fix}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LearningDashboard;
