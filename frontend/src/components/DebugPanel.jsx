import { useState } from "react";
import { FaBug, FaTimes, FaCheck, FaExclamationTriangle, FaTerminal } from "react-icons/fa";

export default function DebugPanel({ isOpen, onClose, metadata }) {
    if (!isOpen) return null;

    const data = metadata || {
        agent: "CodingAgent",
        model: "Gemini 3.5 Flash",
        execution_time_seconds: 1.8,
        validation_passed: true,
        retry_count: 0,
        prompt_length: 42,
        system_prompt: "You are an expert AI assistant providing accurate knowledge.",
        final_prompt: "User Request: What is Mumbai Indians?",
        raw_llm_response: "Mumbai Indians (MI) is a legendary franchise cricket team based in Mumbai, Maharashtra competing in the IPL.",
        formatted_response: "## What is Mumbai Indians?\n\n**Mumbai Indians (MI)** is a legendary franchise cricket team based in Mumbai, Maharashtra.",
        reason: "Keyword match for IPL / Cricket / Team",
        confidence: 1.0
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
            <div className="bg-[#0F172A] border border-gray-800 rounded-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 bg-[#1E293B] border-b border-gray-800">
                    <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                        <FaBug />
                        <span>AIForge Developer Debug Trace</span>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-800 cursor-pointer"
                    >
                        <FaTimes />
                    </button>
                </div>

                {/* Content Body */}
                <div className="p-6 overflow-y-auto space-y-5 text-xs font-mono text-gray-300">
                    {/* Metadata Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="bg-[#1E293B]/60 p-3 rounded-xl border border-gray-800">
                            <span className="text-[10px] text-gray-500 uppercase block font-semibold mb-1">Selected Agent</span>
                            <span className="text-indigo-400 font-bold">{data.agent}</span>
                        </div>
                        <div className="bg-[#1E293B]/60 p-3 rounded-xl border border-gray-800">
                            <span className="text-[10px] text-gray-500 uppercase block font-semibold mb-1">Model Name</span>
                            <span className="text-cyan-400 font-bold">{data.model}</span>
                        </div>
                        <div className="bg-[#1E293B]/60 p-3 rounded-xl border border-gray-800">
                            <span className="text-[10px] text-gray-500 uppercase block font-semibold mb-1">Execution Time</span>
                            <span className="text-amber-400 font-bold">{data.execution_time_seconds}s</span>
                        </div>
                        <div className="bg-[#1E293B]/60 p-3 rounded-xl border border-gray-800">
                            <span className="text-[10px] text-gray-500 uppercase block font-semibold mb-1">Validation Status</span>
                            <span className={`font-bold ${data.validation_passed ? "text-emerald-400" : "text-rose-400"}`}>
                                {data.validation_passed ? "✓ Passed" : "✗ Failed"}
                            </span>
                        </div>
                    </div>

                    {/* Routing Details */}
                    <div className="bg-[#1E293B]/40 p-4 rounded-xl border border-gray-800/80 space-y-2">
                        <div className="flex justify-between items-center text-[11px]">
                            <span className="text-gray-400 font-semibold">Routing Confidence:</span>
                            <span className="text-indigo-300 font-bold">{((data.confidence || 1.0) * 100).toFixed(0)}%</span>
                        </div>
                        <div className="text-[11px] text-gray-400">
                            <span className="font-semibold">Reasoning: </span>
                            <span className="text-gray-300">{data.reason || "Routed based on query intent classification"}</span>
                        </div>
                    </div>

                    {/* System Prompt */}
                    <div className="space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">System Prompt</span>
                        <div className="bg-[#0B0F19] p-3 rounded-xl border border-gray-800 text-gray-400 overflow-x-auto max-h-32">
                            {data.system_prompt}
                        </div>
                    </div>

                    {/* Final Prompt */}
                    <div className="space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">Final Prompt (Sent to LLM)</span>
                        <div className="bg-[#0B0F19] p-3 rounded-xl border border-gray-800 text-cyan-300 overflow-x-auto max-h-32">
                            {data.final_prompt}
                        </div>
                    </div>

                    {/* Raw Gemini / LLM Response */}
                    <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                            <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">Raw Gemini / LLM Response</span>
                            <span className="text-[10px] text-gray-500">{data.raw_llm_response?.length || 0} chars</span>
                        </div>
                        <div className="bg-[#0B0F19] p-3 rounded-xl border border-gray-800 text-emerald-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
                            {data.raw_llm_response}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-3 bg-[#1E293B] border-t border-gray-800 flex justify-between items-center text-[11px] text-gray-500 font-mono">
                    <span>Retry Count: <strong className="text-purple-400">{data.retry_count}</strong></span>
                    <button
                        onClick={onClose}
                        className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg transition-colors cursor-pointer"
                    >
                        Close Trace
                    </button>
                </div>
            </div>
        </div>
    );
}
