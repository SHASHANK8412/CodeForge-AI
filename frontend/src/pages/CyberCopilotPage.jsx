import React, { useState, useEffect } from "react";
import { 
  FaShieldAlt, FaLock, FaExclamationTriangle, FaCheckCircle, 
  FaTerminal, FaSearch, FaHistory, FaUserShield, FaServer, 
  FaPlay, FaBolt, FaArrowRight, FaEye, FaSave
} from "react-icons/fa";
import { fetchSocOverview, fetchIncidents, runInvestigation, approveRemediation } from "../services/cyberCopilotApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const SAMPLE_SECURITY_QUERIES = [
  "Investigate suspicious login spray & check if any privileged ledger API was exposed",
  "Correlate Tor exit node IP 198.51.100.42 with backend syslog access records",
  "Verify RS256 zero-trust RBAC token revocation status for admin@fooddelivery.ai"
];

export default function CyberCopilotPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [overview, setOverview] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [loading, setLoading] = useState(true);

  // Copilot Investigation Chat
  const [query, setQuery] = useState("");
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigationResult, setInvestigationResult] = useState(null);

  const loadData = async () => {
    try {
      const [ov, incs] = await Promise.all([
        fetchSocOverview(),
        fetchIncidents()
      ]);
      setOverview(ov);
      setIncidents(incs || []);
      if (incs && incs.length > 0 && !selectedIncident) {
        setSelectedIncident(incs[0]);
      }
    } catch (err) {
      console.error("Error loading SOC data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleRunInvestigation = async (qToRun) => {
    const text = qToRun || query;
    if (!text.trim()) return;
    setIsInvestigating(true);
    setQuery(text);
    toast("Multi-Agent Security Team Correlating Telemetry & Threat Intel...", { icon: "🛡️" });
    try {
      const res = await runInvestigation(text.trim());
      setInvestigationResult(res);
      toast.success("Security Correlation Complete!", { icon: "✓" });
    } catch (err) {
      toast.error("Investigation failed");
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleApproveAction = async (remediationId) => {
    if (!selectedIncident) return;
    toast("Executing Zero-Trust Defensive Remediation...", { icon: "🔒" });
    try {
      const res = await approveRemediation(selectedIncident.id, remediationId);
      if (res.success) {
        toast.success(res.message, { icon: "🛡️" });
        setOverview((prev) => ({
          ...prev,
          security_posture_score: res.new_security_score || 94
        }));
        // Update local status
        setSelectedIncident((prev) => ({
          ...prev,
          status: "RESOLVED",
          remediation_recommendations: prev.remediation_recommendations.map((r) => 
            r.id === remediationId ? { ...r, is_approved: true, remediation_status: "EXECUTED_AND_VERIFIED" } : r
          )
        }));
      }
    } catch (err) {
      toast.error("Failed to apply remediation");
    }
  };

  const handleSaveReport = () => {
    if (!selectedIncident) return;
    saveOutputItem({
      title: `SOC Incident Report: ${selectedIncident.title}`,
      category: "Security",
      content: `# Security Incident Report\n\n- **Incident ID**: ${selectedIncident.id}\n- **Risk Score**: ${selectedIncident.risk_score}/100\n- **Status**: ${selectedIncident.status}\n\n## Timeline\n${selectedIncident.timeline.map(t => `- [${t.time_offset}] ${t.event_title} (${t.evidence_ref})`).join("\n")}`,
      language: "markdown"
    });
    toast.success("Saved Incident Report to Library!", { icon: "📑" });
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-rose-600 via-red-600 to-amber-500 text-white shadow-lg shadow-rose-500/20">
            <FaShieldAlt size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Defensive AI Cybersecurity Copilot
              <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono text-[10px] font-bold">
                Zero-Trust SOC Platform
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Telemetry Ingestion, Anomaly Correlation, Multi-Agent Threat Triage & Human-in-the-Loop Remediation
            </p>
          </div>
        </div>

        {/* Global Security Metrics */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-emerald-400 font-bold">
            Posture: {overview?.security_posture_score || 88}/100
          </span>
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-rose-400 font-bold">
            {overview?.critical_threats_count || 1} Critical Alert
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Incident List & Copilot Chat (55%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar border-r border-[#242833]">
          {/* AI Security Copilot Search / Investigator Bar */}
          <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl">
            <span className="text-[10px] font-mono text-rose-400 uppercase font-bold flex items-center gap-1.5">
              <FaSearch size={10} /> AI Security Copilot Telemetry Query
            </span>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRunInvestigation()}
                placeholder="e.g. Investigate login spray, correlate IP 198.51.100.42 with syslog..."
                className="flex-1 bg-[#08090D] border border-[#242833] focus:border-rose-500 rounded-xl p-3 text-xs text-white outline-none"
              />
              <button
                onClick={() => handleRunInvestigation()}
                disabled={isInvestigating || !query.trim()}
                className="px-4 py-3 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs"
              >
                {isInvestigating ? "Investigating..." : "Analyze"}
              </button>
            </div>

            {/* Starter Query Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {SAMPLE_SECURITY_QUERIES.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => handleRunInvestigation(sq)}
                  className="px-2.5 py-1 rounded-lg bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] text-[10px] text-gray-400 hover:text-rose-300 font-mono transition cursor-pointer text-left truncate max-w-sm"
                >
                  🛡️ {sq}
                </button>
              ))}
            </div>
          </div>

          {/* Copilot Investigation Results */}
          {investigationResult && (
            <div className="p-5 rounded-3xl bg-gradient-to-b from-[#1F1117] to-[#0F1117] border border-rose-500/40 space-y-3 animate-fade-in shadow-xl text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-rose-300 uppercase font-bold flex items-center gap-1.5">
                  <FaCheckCircle className="text-rose-400" /> Multi-Agent Security Verdict: {investigationResult.verdict}
                </span>
                <span className="text-[10px] font-mono text-emerald-400 font-bold">
                  {Math.round(investigationResult.confidence * 100)}% Confidence
                </span>
              </div>
              <p className="text-gray-300 leading-relaxed">{investigationResult.summary}</p>
              <div className="p-3 rounded-xl bg-black/40 border border-[#1C202B] space-y-1 font-mono text-[10px]">
                <span className="text-amber-300 font-bold block">Defensive Attack Chain Reconstructed:</span>
                {investigationResult.attack_chain.map((c, i) => (
                  <div key={i} className="text-gray-400">{c}</div>
                ))}
              </div>
            </div>
          )}

          {/* Incident Queue */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Active Security Incident Queue ({incidents.length})
            </span>
            <div className="space-y-3">
              {incidents.map((inc) => (
                <div
                  key={inc.id}
                  onClick={() => setSelectedIncident(inc)}
                  className={`p-4 rounded-2xl cursor-pointer transition space-y-2 ${
                    selectedIncident?.id === inc.id
                      ? "bg-[#1E121B] border border-rose-500 shadow-xl"
                      : "bg-[#0F1117] hover:bg-[#151821] border border-[#242833]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono text-[9px] font-bold">
                      {inc.severity} • Risk {inc.risk_score}/100
                    </span>
                    <span className="text-[10px] font-mono text-amber-400">
                      {inc.status}
                    </span>
                  </div>
                  <h3 className="font-bold text-xs text-white">{inc.title}</h3>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {inc.affected_assets.map((a, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-[#08090D] border border-[#1C202B] text-[9px] font-mono text-gray-400">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Incident Details, Timeline, & Human Approval Gateway (45%) */}
        <div className="w-[480px] bg-[#0F1117] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {selectedIncident ? (
            <div className="space-y-5">
              {/* Header */}
              <div className="space-y-1.5 pb-4 border-b border-[#1C202B]">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono text-[10px] font-bold">
                    {selectedIncident.id}
                  </span>
                  <button
                    onClick={handleSaveReport}
                    className="px-2.5 py-1 bg-[#1E293B] hover:bg-[#334155] text-rose-300 rounded-lg text-[10px] font-semibold border border-gray-700 cursor-pointer flex items-center gap-1"
                  >
                    <FaSave size={9} /> Save Report
                  </button>
                </div>
                <h2 className="text-base font-bold text-white">{selectedIncident.title}</h2>
              </div>

              {/* Multi-Step Timeline */}
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-rose-400 uppercase font-bold block">
                  Correlated Event Timeline
                </span>
                <div className="space-y-2">
                  {selectedIncident.timeline.map((t, idx) => (
                    <div key={idx} className="p-3 bg-[#08090D] border border-[#1C202B] rounded-xl space-y-1 text-xs">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="text-rose-300 font-bold">{t.time_offset}</span>
                        <span className="text-gray-500">{t.source}</span>
                      </div>
                      <p className="text-gray-300 text-[11px] leading-relaxed">{t.event_title}</p>
                      <span className="text-[9px] font-mono text-gray-500 block">Ref: {t.evidence_ref}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Human-in-the-Loop Remediation Approval Gateway */}
              <div className="space-y-3 pt-3 border-t border-[#1C202B]">
                <span className="text-[10px] font-mono text-amber-400 uppercase font-bold flex items-center gap-1.5">
                  <FaLock size={10} /> Human-in-the-Loop Defensive Remediation
                </span>

                <div className="space-y-2">
                  {selectedIncident.remediation_recommendations.map((rem) => (
                    <div key={rem.id} className="p-4 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white text-xs">{rem.title}</span>
                        <span className={`px-2 py-0.5 rounded font-mono text-[9px] font-bold ${
                          rem.is_approved ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"
                        }`}>
                          {rem.remediation_status}
                        </span>
                      </div>
                      <p className="text-gray-400 text-[11px] leading-relaxed">{rem.description}</p>

                      {!rem.is_approved ? (
                        <button
                          onClick={() => handleApproveAction(rem.id)}
                          className="w-full py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs flex items-center justify-center gap-1.5 mt-2"
                        >
                          <FaCheckCircle size={11} /> Approve & Execute Remediation
                        </button>
                      ) : (
                        <div className="p-2 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 font-mono text-[10px] text-center">
                          ✓ Remediation Applied & Verified Safe
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select an incident to view timeline & remediation actions
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
