import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function SectionCard({ icon, title, children, badge }) {
    return (
        <div className="bg-[#1E293B] border border-gray-800 rounded-xl p-5 mb-5 shadow-lg backdrop-blur-sm transition-all hover:border-indigo-500/40">
            <div className="flex items-center justify-between mb-4 border-b border-gray-700/60 pb-3">
                <div className="flex items-center space-x-2">
                    <span className="text-xl">{icon}</span>
                    <h3 className="text-lg font-bold text-white tracking-wide">{title}</h3>
                </div>
                {badge && (
                    <span className="px-3 py-1 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                        {badge}
                    </span>
                )}
            </div>
            <div className="text-gray-300 text-sm">{children}</div>
        </div>
    );
}

function PlannerCard({ plan }) {
    if (!plan) return null;

    const isString = typeof plan === "string";
    const structuredPlan = isString ? null : (plan.planning_artifacts || plan.artifacts || plan);

    if (isString) {
        return (
            <div className="bg-[#0F172A] rounded-xl p-6 mt-6 text-white border border-gray-800 shadow-2xl">
                <h2 className="text-2xl font-bold mb-5 flex items-center gap-2">
                    <span>📋</span> AI Solutions Architecture Plan
                </h2>
                <div className="prose prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{plan}</ReactMarkdown>
                </div>
            </div>
        );
    }

    const domain = structuredPlan?.domain || "Software System";
    const reqs = structuredPlan?.requirements || {};
    const techStack = structuredPlan?.tech_stack || {};
    const dbSchema = structuredPlan?.database_schema || [];
    const apiSpecs = structuredPlan?.api_specifications || [];
    const folderStructure = structuredPlan?.folder_structure || [];
    const taskBreakdown = structuredPlan?.task_breakdown || [];
    const dependencyGraph = structuredPlan?.dependency_graph || {};
    const risks = structuredPlan?.risks || [];
    const costEstimate = structuredPlan?.cost_estimate || {};

    return (
        <div className="bg-[#0F172A] rounded-xl p-6 mt-6 text-white border border-gray-800 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-gray-800 pb-4">
                <div>
                    <h2 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                        🚀 AI Solutions Architecture Plan
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">Day 42 — Autonomous Architecture & Pre-Coding Artifacts</p>
                </div>
                <span className="px-4 py-1.5 rounded-full text-xs font-bold bg-green-500/20 text-green-400 border border-green-500/30">
                    Domain: {domain}
                </span>
            </div>

            {/* 1. Requirements Analysis */}
            <SectionCard icon="✅" title="Functional & Non-Functional Requirements" badge="Pre-Coding Verified">
                {reqs.executive_summary && (
                    <p className="mb-4 text-gray-300 italic border-l-2 border-indigo-500 pl-3">{reqs.executive_summary}</p>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 className="font-semibold text-indigo-400 mb-2">Functional Requirements</h4>
                        <ul className="space-y-1 text-xs">
                            {(reqs.functional_requirements || []).map((fr, idx) => (
                                <li key={idx} className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span> {fr}
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-purple-400 mb-2">Non-Functional Requirements</h4>
                        <ul className="space-y-1 text-xs">
                            {(reqs.non_functional_requirements || []).map((nfr, idx) => (
                                <li key={idx} className="flex items-center gap-2">
                                    <span className="text-purple-400">⚡</span> {nfr}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {reqs.user_stories && (
                    <div className="mt-4 pt-3 border-t border-gray-800">
                        <h4 className="font-semibold text-pink-400 mb-2 text-xs uppercase tracking-wider">User Stories</h4>
                        <ul className="space-y-1.5 text-xs text-gray-400">
                            {reqs.user_stories.map((us, idx) => (
                                <li key={idx}>📖 {us}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </SectionCard>

            {/* 2. Recommended Tech Stack */}
            <SectionCard icon="🛠️" title="Recommended Tech Stack" badge="Architecture Selected">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {Object.entries(techStack).map(([key, val]) => (
                        <div key={key} className="bg-[#111827] border border-gray-800 rounded-lg p-3">
                            <span className="text-xs text-gray-500 uppercase font-semibold block">{key}</span>
                            <span className="text-sm font-bold text-indigo-300">{val}</span>
                        </div>
                    ))}
                </div>
            </SectionCard>

            {/* 3. Database Schema */}
            <SectionCard icon="🗄️" title="Database Schema & Data Model" badge={`${dbSchema.length} Core Tables`}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {dbSchema.map((tbl, idx) => (
                        <div key={idx} className="bg-[#111827] border border-gray-800 rounded-lg p-4">
                            <h4 className="font-bold text-green-400 mb-2 text-sm flex items-center justify-between">
                                📊 Table: {tbl.table}
                                <span className="text-[10px] text-gray-500 font-mono">PK: {tbl.primary_key}</span>
                            </h4>
                            <div className="space-y-1 text-xs text-gray-400 font-mono">
                                <div><span className="text-gray-500">FKs:</span> {tbl.foreign_keys?.join(", ") || "None"}</div>
                                <div><span className="text-gray-500">Indexes:</span> {tbl.indexes?.join(", ") || "None"}</div>
                                <div><span className="text-gray-500">Relations:</span> {tbl.relationships?.join("; ") || "Direct"}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </SectionCard>

            {/* 4. API Specifications */}
            <SectionCard icon="🔌" title="REST API Endpoint Planner" badge={`${apiSpecs.length} Endpoints`}>
                <div className="space-y-2">
                    {apiSpecs.map((ep, idx) => {
                        const methodColor =
                            ep.method === "GET" ? "bg-blue-500/20 text-blue-400 border-blue-500/30" :
                            ep.method === "POST" ? "bg-green-500/20 text-green-400 border-green-500/30" :
                            ep.method === "PUT" ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" :
                            "bg-red-500/20 text-red-400 border-red-500/30";

                        return (
                            <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between bg-[#111827] border border-gray-800 rounded-lg p-3 gap-2">
                                <div className="flex items-center gap-3 font-mono text-xs">
                                    <span className={`px-2.5 py-1 rounded text-[10px] font-bold border ${methodColor}`}>
                                        {ep.method}
                                    </span>
                                    <span className="text-gray-200 font-semibold">{ep.path}</span>
                                </div>
                                <div className="text-[11px] text-gray-400 flex items-center gap-3">
                                    <span>Req: <code className="text-indigo-300">{ep.request_body}</code></span>
                                    <span>Status: <code className="text-green-300">{ep.status_code}</code></span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </SectionCard>

            {/* 5. Folder Structure & Task Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <SectionCard icon="📁" title="Project Folder Structure">
                    <pre className="bg-[#111827] border border-gray-800 rounded-lg p-3 text-xs text-indigo-300 font-mono overflow-x-auto">
                        {Array.isArray(folderStructure) ? folderStructure.join("\n") : JSON.stringify(folderStructure, null, 2)}
                    </pre>
                </SectionCard>

                <SectionCard icon="📌" title="Ordered Task Execution Breakdown">
                    <ol className="space-y-2 text-xs font-mono">
                        {taskBreakdown.map((t, idx) => (
                            <li key={idx} className="flex items-center gap-2 bg-[#111827] border border-gray-800 p-2.5 rounded-lg text-gray-200">
                                <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-[10px] font-bold">
                                    {idx + 1}
                                </span>
                                {t}
                            </li>
                        ))}
                    </ol>
                </SectionCard>
            </div>

            {/* 6. Risk Analysis & Cost Estimation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <SectionCard icon="⚠️" title="Architectural Risk Analysis" badge={`${risks.length} Mitigated Risks`}>
                    <div className="space-y-2">
                        {risks.map((r, idx) => (
                            <div key={idx} className="bg-[#111827] border border-gray-800 rounded-lg p-3 text-xs">
                                <div className="font-bold text-red-400 mb-1">🚨 Risk: {r.risk}</div>
                                <div className="text-gray-300">💡 <span className="text-gray-500">Mitigation:</span> {r.mitigation}</div>
                            </div>
                        ))}
                    </div>
                </SectionCard>

                <SectionCard icon="💰" title="Resource & Cost Estimator">
                    <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                        <div className="bg-[#111827] border border-gray-800 p-3 rounded-lg">
                            <span className="text-gray-500 block text-[10px]">DEV TIME</span>
                            <span className="text-indigo-300 font-bold">{costEstimate.estimated_development_time || "3-4 weeks"}</span>
                        </div>
                        <div className="bg-[#111827] border border-gray-800 p-3 rounded-lg">
                            <span className="text-gray-500 block text-[10px]">TOKENS</span>
                            <span className="text-purple-300 font-bold">{costEstimate.token_usage || "150,000"}</span>
                        </div>
                        <div className="bg-[#111827] border border-gray-800 p-3 rounded-lg">
                            <span className="text-gray-500 block text-[10px]">COMPUTE (RAM/CPU)</span>
                            <span className="text-green-300 font-bold">{costEstimate.ram || "8GB RAM"} / {costEstimate.cpu || "4 vCPU"}</span>
                        </div>
                        <div className="bg-[#111827] border border-gray-800 p-3 rounded-lg">
                            <span className="text-gray-500 block text-[10px]">MONTHLY INFRA COST</span>
                            <span className="text-pink-300 font-bold">{costEstimate.deployment_cost || "$45-$120/mo"}</span>
                        </div>
                    </div>
                </SectionCard>
            </div>
        </div>
    );
}

export default PlannerCard;