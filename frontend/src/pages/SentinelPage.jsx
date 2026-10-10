import React, { useState, useEffect } from "react";
import { 
  FaShieldAlt, FaExclamationTriangle, FaCheckCircle, FaLock, 
  FaBug, FaCodeBranch, FaPlay, FaKey, FaHistory, FaFileAlt, 
  FaBrain, FaServer, FaCheck, FaTimes, FaUndo, FaArrowRight
} from "react-icons/fa";
import { fetchSecurityPosture, runSecurityAudit, remediateFinding } from "../services/sentinelApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

export default function SentinelPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [posture, setPosture] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [activeTab, setActiveTab] = useState("triage"); // "triage", "attack-path", "threat-model", "ai-security"

  const loadData = async () => {
    try {
      const data = await fetchSecurityPosture(activeProjectId);
      setPosture(data);
      if (data?.findings?.length > 0 && !selectedFinding) {
        setSelectedFinding(data.findings[0]);
      }
    } catch (err) {
      console.error("Error loading Sentinel posture:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleRunAudit = async () => {
    setIsAuditing(true);
    toast("AIForge Sentinel scanning code, dependencies, AST, and AI prompts...", { icon: "🛡️" });
    try {
      const updated = await runSecurityAudit(activeProjectId);
      setPosture(updated);
      toast.success("Security Audit Complete! Posture updated.", { icon: "✓" });
    } catch (err) {
      toast.error("Security audit failed");
    } finally {
      setIsAuditing(false);
    }
  };

  const handleRemediate = async (findingId, approved = true) => {
    try {
      const res = await remediateFinding({
        projectId: activeProjectId,
        findingId,
        approved
      });
      if (res.success) {
        toast.success(`Remediated! Security Score upgraded: ${res.previous_score} → ${res.new_score}`, {
          icon: "🚀"
        });
        setShowDiffModal(false);
        loadData();
      }
    } catch (err) {
      toast.error("Remediation failed");
    }
  };

  const handleExportReport = () => {
    if (!posture) return;
    const reportMd = `# 🛡️ AIForge Sentinel Security Posture Report

## 📊 Executive Score: ${posture.overall_score} / 100
- **Authentication**: ${posture.score_breakdown?.Authentication}%
- **Authorization**: ${posture.score_breakdown?.Authorization}%
- **Dependencies**: ${posture.score_breakdown?.Dependencies}%
- **Secrets**: ${posture.score_breakdown?.Secrets}%
- **API Security**: ${posture.score_breakdown?.["API Security"]}%
- **AI Security**: ${posture.score_breakdown?.["AI Security"]}%

## 🔍 Active Findings (${posture.findings?.length})
${posture.findings?.map(f => `### [${f.severity}] ${f.title}
- **Location**: \`${f.location}\`
- **Impact**: ${f.impact}
- **Fix**: ${f.recommended_fix}`).join("\n\n")}`;

    saveOutputItem({
      title: `Sentinel Security Report: ${posture.project_id}`,
      category: "Security",
      content: reportMd,
      language: "markdown"
    });
    toast.success("Saved Security Report to Library!", { icon: "📑" });
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0B0F19] text-gray-400 font-mono text-xs">
        Loading AIForge Sentinel SOC Posture...
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Sentinel Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-emerald-600 via-teal-600 to-indigo-600 text-white shadow-lg shadow-emerald-500/20">
            <FaShieldAlt size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              AIForge Sentinel
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                Defensive AI-SOC
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Continuous AST Code Analysis, Redacted Secret Scanner, AI Prompt Injection Defense & Auto-Remediation
            </p>
          </div>
        </div>

        {/* Action CTAs */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportReport}
            className="px-3.5 py-2 bg-[#151821] hover:bg-[#1E2330] text-gray-200 border border-gray-700 rounded-xl font-semibold transition cursor-pointer text-xs flex items-center gap-1.5"
          >
            <FaFileAlt size={11} className="text-emerald-400" /> Export Report
          </button>
          <button
            onClick={handleRunAudit}
            disabled={isAuditing}
            className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl font-bold transition shadow-lg shadow-emerald-500/20 cursor-pointer text-xs"
          >
            <FaPlay size={10} />
            <span>{isAuditing ? "Auditing Repository..." : "Run Security Audit"}</span>
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Score & Categorical Posture (30%) */}
        <div className="w-80 bg-[#0F1117] border-r border-[#242833] overflow-y-auto p-4 space-y-5 custom-scrollbar">
          {/* Security Posture Score Card */}
          <div className="p-5 rounded-3xl bg-[#08090D] border border-[#242833] space-y-4 shadow-xl">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Project Security Posture
            </span>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-3xl font-black text-white font-mono tracking-tight">
                  {posture?.overall_score}
                </span>
                <span className="text-gray-500 text-xs font-mono"> / 100</span>
                <span className="block text-[10px] text-emerald-400 font-mono mt-0.5">
                  ✓ Defensive Baseline Strong
                </span>
              </div>
              <div className="w-12 h-12 rounded-full border-4 border-emerald-500 flex items-center justify-center text-xs font-bold font-mono text-emerald-300">
                {posture?.overall_score}%
              </div>
            </div>

            {/* Severity Pill Counts */}
            <div className="grid grid-cols-4 gap-1 pt-2 border-t border-[#1C202B] text-center font-mono">
              <div className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
                <span className="text-[9px] text-rose-400 block font-bold">CRIT</span>
                <span className="text-xs font-bold text-white">{posture?.severity_counts?.CRITICAL || 0}</span>
              </div>
              <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <span className="text-[9px] text-amber-400 block font-bold">HIGH</span>
                <span className="text-xs font-bold text-white">{posture?.severity_counts?.HIGH || 0}</span>
              </div>
              <div className="p-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                <span className="text-[9px] text-yellow-400 block font-bold">MED</span>
                <span className="text-xs font-bold text-white">{posture?.severity_counts?.MEDIUM || 0}</span>
              </div>
              <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <span className="text-[9px] text-blue-400 block font-bold">LOW</span>
                <span className="text-xs font-bold text-white">{posture?.severity_counts?.LOW || 0}</span>
              </div>
            </div>
          </div>

          {/* Category Breakdown Bars */}
          <div className="space-y-2.5">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Security Domain Score Breakdown
            </span>
            {Object.entries(posture?.score_breakdown || {}).map(([cat, score]) => (
              <div key={cat} className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-gray-300">{cat}</span>
                  <span className="font-mono text-emerald-400 font-bold">{score}%</span>
                </div>
                <div className="w-full h-1.5 bg-[#1C202B] rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      score >= 90 ? "bg-emerald-500" : score >= 80 ? "bg-teal-500" : "bg-amber-500"
                    }`}
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Navigation View Tabs */}
          <div className="space-y-1 pt-3 border-t border-[#1C202B]">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block mb-1">
              Sentinel Views
            </span>
            <button
              onClick={() => setActiveTab("triage")}
              className={`w-full p-2.5 rounded-xl text-left text-xs font-semibold flex items-center gap-2 cursor-pointer transition ${
                activeTab === "triage" ? "bg-[#1E293B] text-emerald-300 border border-emerald-500/30" : "text-gray-400 hover:bg-[#151821]"
              }`}
            >
              <FaBug size={11} /> Vulnerability Triage ({posture?.findings?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("attack-path")}
              className={`w-full p-2.5 rounded-xl text-left text-xs font-semibold flex items-center gap-2 cursor-pointer transition ${
                activeTab === "attack-path" ? "bg-[#1E293B] text-indigo-300 border border-indigo-500/30" : "text-gray-400 hover:bg-[#151821]"
              }`}
            >
              <FaCodeBranch size={11} /> Attack-Path Topology
            </button>
            <button
              onClick={() => setActiveTab("threat-model")}
              className={`w-full p-2.5 rounded-xl text-left text-xs font-semibold flex items-center gap-2 cursor-pointer transition ${
                activeTab === "threat-model" ? "bg-[#1E293B] text-amber-300 border border-amber-500/30" : "text-gray-400 hover:bg-[#151821]"
              }`}
            >
              <FaShieldAlt size={11} /> STRIDE Threat Model
            </button>
            <button
              onClick={() => setActiveTab("ai-security")}
              className={`w-full p-2.5 rounded-xl text-left text-xs font-semibold flex items-center gap-2 cursor-pointer transition ${
                activeTab === "ai-security" ? "bg-[#1E293B] text-rose-300 border border-rose-500/30" : "text-gray-400 hover:bg-[#151821]"
              }`}
            >
              <FaBrain size={11} /> AI Prompt & Agent Security
            </button>
          </div>
        </div>

        {/* Right Side: Tab View Content (70%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {/* TAB 1: Vulnerability Triage & Auto-Remediation */}
          {activeTab === "triage" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="space-y-1">
                <h2 className="text-base font-bold text-white">Prioritized Vulnerabilities & Fixes</h2>
                <p className="text-xs text-gray-400">
                  Every finding explains: What is wrong, why it matters, where it occurs, and provides atomic auto-remediation diffs.
                </p>
              </div>

              <div className="space-y-4">
                {(posture?.findings || []).map((finding) => (
                  <div
                    key={finding.id}
                    className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl transition"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                            finding.severity === "CRITICAL" ? "bg-rose-500/20 text-rose-300 border border-rose-500/30" :
                            finding.severity === "HIGH" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" :
                            "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          }`}>
                            {finding.severity}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-gray-300">
                            {finding.category}
                          </span>
                          {finding.cwe_id && (
                            <span className="text-[10px] font-mono text-gray-500">{finding.cwe_id}</span>
                          )}
                        </div>
                        <h3 className="text-sm font-bold text-white">{finding.title}</h3>
                        <span className="text-[10px] font-mono text-indigo-400 block">{finding.location}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {finding.remediation_diff && finding.status !== "RESOLVED" && (
                          <button
                            onClick={() => {
                              setSelectedFinding(finding);
                              setShowDiffModal(true);
                            }}
                            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer flex items-center gap-1.5"
                          >
                            <FaCheck size={10} /> Auto-Remediate
                          </button>
                        )}
                        {finding.status === "RESOLVED" && (
                          <span className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 rounded-xl text-xs font-mono font-bold flex items-center gap-1">
                            <FaCheckCircle size={10} /> Resolved
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs">
                      <div className="p-3 bg-[#08090D] border border-[#1C202B] rounded-2xl space-y-1">
                        <span className="text-[9px] font-mono text-gray-500 uppercase block font-bold">Impact</span>
                        <p className="text-gray-300 text-[11px] leading-relaxed">{finding.impact}</p>
                      </div>
                      <div className="p-3 bg-[#08090D] border border-[#1C202B] rounded-2xl space-y-1">
                        <span className="text-[9px] font-mono text-gray-500 uppercase block font-bold">Recommended Fix</span>
                        <p className="text-emerald-300 text-[11px] leading-relaxed">{finding.recommended_fix}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: Defensive Attack-Path Topology */}
          {activeTab === "attack-path" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="space-y-1">
                <h2 className="text-base font-bold text-white">Defensive Attack-Path Visualization</h2>
                <p className="text-xs text-gray-400">
                  Visual mapping showing how entrypoints and missing tenant boundaries interconnect.
                </p>
              </div>

              <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4">
                <div className="flex flex-col gap-3">
                  {(posture?.attack_path || []).map((node, idx) => (
                    <React.Fragment key={node.id}>
                      <div className="p-4 rounded-2xl bg-[#08090D] border border-[#1C202B] flex items-center justify-between gap-3 text-xs">
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-slate-800 text-indigo-300 flex items-center justify-center font-mono font-bold text-xs">
                            {idx + 1}
                          </span>
                          <div>
                            <span className="font-bold text-white block">{node.label}</span>
                            <span className="text-[10px] font-mono text-gray-400">{node.stage}</span>
                          </div>
                        </div>
                        <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                          node.risk_level === "CRITICAL" ? "bg-rose-500/20 text-rose-300" :
                          node.risk_level === "HIGH" ? "bg-amber-500/20 text-amber-300" : "bg-gray-800 text-gray-300"
                        }`}>
                          {node.risk_level}
                        </span>
                      </div>
                      {idx < (posture?.attack_path?.length || 0) - 1 && (
                        <div className="flex justify-center text-gray-600">
                          ↓
                        </div>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: STRIDE Threat Model */}
          {activeTab === "threat-model" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="space-y-1">
                <h2 className="text-base font-bold text-white">STRIDE Threat Modeling Matrix</h2>
                <p className="text-xs text-gray-400">
                  Defensive architectural controls mapping threats across Spoofing, Tampering, and Elevation of Privilege.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(posture?.threat_model || []).map((tm, idx) => (
                  <div key={idx} className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-2.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold">
                        {tm.category}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 font-bold">
                        ✓ {tm.status}
                      </span>
                    </div>
                    <h3 className="font-bold text-white text-sm">{tm.asset}</h3>
                    <p className="text-gray-400 text-[11px]"><span className="text-gray-500 font-mono">Threat:</span> {tm.threat}</p>
                    <div className="p-2.5 rounded-xl bg-[#08090D] border border-[#1C202B] text-emerald-300 text-[10px] font-mono">
                      Mitigation: {tm.mitigation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: AI & Agent Boundary Security */}
          {activeTab === "ai-security" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="space-y-1">
                <h2 className="text-base font-bold text-white">AIForge Agent Permission & Prompt Defense</h2>
                <p className="text-xs text-gray-400">
                  Defensive boundaries protecting autonomous agents from prompt injection, tool abuse, and data leakage.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3">
                  <span className="text-[10px] font-mono text-rose-400 font-bold uppercase block">
                    Prompt Injection Defense
                  </span>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2.5 bg-[#08090D] rounded-xl">
                      <span className="text-gray-300">XML Context Isolation</span>
                      <span className="text-emerald-400 font-mono font-bold">Active</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-[#08090D] rounded-xl">
                      <span className="text-gray-300">Untrusted Document Delimiters</span>
                      <span className="text-emerald-400 font-mono font-bold">Active</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-[#08090D] rounded-xl">
                      <span className="text-gray-300">System Instruction Overrides</span>
                      <span className="text-emerald-400 font-mono font-bold">Blocked</span>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3">
                  <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase block">
                    Agent Security Boundaries
                  </span>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2.5 bg-[#08090D] rounded-xl">
                      <span className="text-gray-300">Sandbox Isolation (vNode-22)</span>
                      <span className="text-emerald-400 font-mono font-bold">Enforced</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-[#08090D] rounded-xl">
                      <span className="text-gray-300">Destructive Mutation Gateway</span>
                      <span className="text-amber-400 font-mono font-bold">Human Consent</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-[#08090D] rounded-xl">
                      <span className="text-gray-300">Host Network / Secrets Access</span>
                      <span className="text-emerald-400 font-mono font-bold">Restricted</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Auto-Remediation Diff Review Modal */}
      {showDiffModal && selectedFinding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-2xl bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4 glow-violet">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FaShieldAlt className="text-emerald-400" /> Review Auto-Remediation Patch
            </h3>
            <p className="text-xs text-gray-300">
              Target Finding: <span className="font-bold text-white">{selectedFinding.title}</span>
            </p>
            <div className="p-4 bg-[#08090D] border border-[#1C202B] rounded-2xl font-mono text-xs text-emerald-400 whitespace-pre-wrap max-h-80 overflow-y-auto">
              {selectedFinding.remediation_diff}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowDiffModal(false)}
                className="px-4 py-2 bg-[#151821] text-gray-300 rounded-xl font-semibold cursor-pointer"
              >
                Close
              </button>
              <button
                onClick={() => handleRemediate(selectedFinding.id, true)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold cursor-pointer transition shadow"
              >
                Approve & Apply Fix
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
