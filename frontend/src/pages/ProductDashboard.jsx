import React, { useState, useEffect } from "react";
import { FaBoxes, FaListOl, FaExclamationCircle, FaChartLine, FaCheckCircle } from "react-icons/fa";

export default function ProductDashboard() {
    const [backlog, setBacklog] = useState([
        { id: "FEAT-101", title: "Fix login & dashboard crashes", priority: "High", impact: "9/10", complexity: "3/10", status: "Sprint 1" },
        { id: "FEAT-102", title: "Dark mode theme toggle", priority: "High", impact: "8/10", complexity: "2/10", status: "Sprint 1" },
        { id: "FEAT-103", title: "Push notification preferences", priority: "Medium", impact: "7/10", complexity: "4/10", status: "Sprint 2" },
        { id: "FEAT-104", title: "Mobile responsive navigation drawer", priority: "Medium", impact: "6/10", complexity: "3/10", status: "Sprint 2" }
    ]);

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-8 custom-scrollbar">
            <div className="mb-8">
                <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                    Product Intelligence & Requirement Evolution Dashboard
                </h1>
                <p className="text-gray-400 text-sm mt-1">
                    AI Product Manager feedback analysis, duplicate merging, business value scoring, and automated sprint roadmaps.
                </p>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Feedback Items Analyzed</span>
                    <span className="text-2xl font-extrabold text-[#6366F1]">48</span>
                </div>
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Duplicate Issues Merged</span>
                    <span className="text-2xl font-extrabold text-[#34D399]">14</span>
                </div>
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">High Business Value Tasks</span>
                    <span className="text-2xl font-extrabold text-[#F59E0B]">8</span>
                </div>
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Planned Sprints</span>
                    <span className="text-2xl font-extrabold text-[#EC4899]">3</span>
                </div>
            </div>

            {/* Product Backlog & Roadmap */}
            <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6 mb-8">
                <h2 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                    <FaListOl className="text-indigo-400" /> Automated Sprint Backlog & Priority Queue
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-gray-400">
                        <thead className="bg-[#1E293B]/50 text-gray-300 uppercase tracking-wider text-[10px]">
                            <tr>
                                <th className="p-3">ID</th>
                                <th className="p-3">Feature Request</th>
                                <th className="p-3">Priority</th>
                                <th className="p-3">Impact</th>
                                <th className="p-3">Complexity</th>
                                <th className="p-3">Sprint Target</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/60">
                            {backlog.map((item) => (
                                <tr key={item.id} className="hover:bg-[#1E293B]/30 transition-colors">
                                    <td className="p-3 font-mono text-indigo-400">{item.id}</td>
                                    <td className="p-3 font-medium text-gray-200">{item.title}</td>
                                    <td className="p-3">
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${item.priority === 'High' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>
                                            {item.priority}
                                        </span>
                                    </td>
                                    <td className="p-3 text-emerald-400 font-bold">{item.impact}</td>
                                    <td className="p-3 text-gray-300">{item.complexity}</td>
                                    <td className="p-3 font-semibold text-purple-400">{item.status}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
