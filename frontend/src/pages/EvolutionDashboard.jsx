import React, { useState } from "react";
import { FaSyncAlt, FaBrain, FaChartLine, FaCheckDouble, FaRocket } from "react-icons/fa";

export default function EvolutionDashboard() {
    const [benchmarks] = useState([
        { metric: "Execution Time", before: "54s", after: "44s", improvement: "+18.5%" },
        { metric: "Cyclomatic Complexity", before: "18", after: "7", improvement: "-61.1%" },
        { metric: "Test Coverage", before: "82%", after: "94.7%", improvement: "+15.5%" },
        { metric: "Performance Score", before: "84.0", after: "92.0", improvement: "+9.5%" },
        { metric: "Security Rating", before: "88.0", after: "98.0", improvement: "+11.4%" }
    ]);

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-8 custom-scrollbar">
            <div className="mb-8">
                <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400">
                    Self-Improving AI Continuous Evolution Dashboard
                </h1>
                <p className="text-gray-400 text-sm mt-1">
                    Track autonomous learning loops, pattern library growth, prompt optimization, and generation benchmarks over time.
                </p>
            </div>

            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Overall AI Score</span>
                    <span className="text-2xl font-extrabold text-emerald-400">95.6%</span>
                </div>
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Learned Patterns</span>
                    <span className="text-2xl font-extrabold text-[#6366F1]">312</span>
                </div>
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Bugs Reduced</span>
                    <span className="text-2xl font-extrabold text-[#F59E0B]">-40%</span>
                </div>
                <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 shadow-sm">
                    <span className="text-xs text-gray-500 block mb-1">Prompt Quality Boost</span>
                    <span className="text-2xl font-extrabold text-[#EC4899]">+14.2%</span>
                </div>
            </div>

            {/* Continuous Benchmarks Table */}
            <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-6 mb-8">
                <h2 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                    <FaChartLine className="text-emerald-400" /> Continuous Project Generation Benchmarks
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-gray-400">
                        <thead className="bg-[#1E293B]/50 text-gray-300 uppercase tracking-wider text-[10px]">
                            <tr>
                                <th className="p-3">Benchmark Metric</th>
                                <th className="p-3">Previous Baseline</th>
                                <th className="p-3">Current Generation</th>
                                <th className="p-3">Improvement %</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/60">
                            {benchmarks.map((row, idx) => (
                                <tr key={idx} className="hover:bg-[#1E293B]/30 transition-colors">
                                    <td className="p-3 font-medium text-gray-200">{row.metric}</td>
                                    <td className="p-3 text-rose-400 font-mono">{row.before}</td>
                                    <td className="p-3 text-emerald-400 font-mono">{row.after}</td>
                                    <td className="p-3 font-bold text-cyan-400">{row.improvement}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
