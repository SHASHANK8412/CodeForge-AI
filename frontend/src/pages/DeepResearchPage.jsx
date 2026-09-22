import React, { useState, useEffect } from "react";
import { 
  FaSearch, FaBook, FaExternalLinkAlt, FaDownload, FaSave, 
  FaBrain, FaPlay, FaCheckCircle, FaLayerGroup, FaPlus
} from "react-icons/fa";
import { fetchResearchReports, runDeepResearch } from "../services/researchApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

export default function DeepResearchPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [topicInput, setTopicInput] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  const loadReports = async () => {
    try {
      const data = await fetchResearchReports(activeProjectId);
      setReports(data || []);
      if (!activeReport && data && data.length > 0) {
        setActiveReport(data[0]);
      }
    } catch (err) {
      console.error("Error loading research reports:", err);
    }
  };

  useEffect(() => {
    loadReports();
  }, [activeProjectId]);

  const handleRunResearch = async () => {
    if (!topicInput.trim() || isRunning) return;
    setIsRunning(true);
    toast("Deep Research Agent gathering sources & benchmarks...", { icon: "🔬" });

    try {
      const report = await runDeepResearch(topicInput.trim(), activeProjectId);
      toast.success("Deep Research completed with cited benchmarks!", { icon: "🚀" });
      setTopicInput("");
      setActiveReport(report);
      loadReports();
    } catch (err) {
      toast.error("Research execution failed");
    } finally {
      setIsRunning(false);
    }
  };

  const handleSaveToSavedOutputs = () => {
    if (!activeReport) return;
    saveOutputItem({
      title: activeReport.topic,
      category: "Research",
      content: activeReport.markdown_report,
      language: "markdown"
    });
    toast.success("Saved research report to Saved Library!", { icon: "📑" });
  };

  const handleExport = () => {
    if (!activeReport) return;
    const blob = new Blob([activeReport.markdown_report], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `research_${activeReport.id}.md`;
    a.click();
    toast.success("Exported research markdown report!");
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-indigo-500 to-cyan-500 text-white shadow-lg shadow-cyan-500/20">
            <FaSearch size={16} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Deep Research & Evidence Engine
              <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono text-[10px]">
                Multi-Source Synthesis
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Autonomous topic deconstruction, architectural benchmarking, and cited RFC reports
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {activeReport && (
            <>
              <button
                onClick={handleSaveToSavedOutputs}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1E293B] hover:bg-[#334155] text-indigo-300 rounded-xl font-semibold transition border border-gray-700 cursor-pointer"
              >
                <FaSave size={10} />
                <span>Save to Library</span>
              </button>

              <button
                onClick={handleExport}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1E293B] hover:bg-[#334155] text-gray-300 rounded-xl font-semibold transition border border-gray-700 cursor-pointer"
              >
                <FaDownload size={10} />
                <span>Export RFC</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Research Search Bar */}
      <div className="p-4 bg-[#0F1117] border-b border-[#242833]">
        <div className="flex items-center gap-3 bg-[#08090D] border border-[#242833] focus-within:border-cyan-500 rounded-2xl px-4 py-3 shadow-inner">
          <FaSearch className="text-cyan-400 shrink-0" size={14} />
          <input
            type="text"
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRunResearch();
            }}
            placeholder="Enter research topic... e.g. 'Compare Redis Streams vs Kafka vs NATS for geolocation latency'"
            disabled={isRunning}
            className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 outline-none"
          />
          <button
            onClick={handleRunResearch}
            disabled={!topicInput.trim() || isRunning}
            className="px-4 py-1.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer shrink-0 flex items-center gap-1.5"
          >
            <FaPlay size={9} />
            <span>{isRunning ? "Gathering Sources..." : "Run Deep Research"}</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Reports List (30%) */}
        <div className="w-80 bg-[#0F1117] border-r border-[#242833] overflow-y-auto p-4 space-y-2.5 custom-scrollbar">
          <span className="text-[10px] font-mono text-gray-500 uppercase block font-bold">
            Recent Research Reports ({reports.length})
          </span>

          {reports.map((r) => (
            <div
              key={r.id}
              onClick={() => setActiveReport(r)}
              className={`p-3 rounded-2xl cursor-pointer transition-all space-y-1.5 ${
                activeReport?.id === r.id
                  ? "bg-[#1E293B] border border-cyan-500/50 shadow-md"
                  : "bg-[#151821] hover:bg-[#1C202B] border border-[#242833]"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-cyan-400 font-bold">100% CITED</span>
                <span className="text-gray-500">{r.created_at?.slice(0, 10)}</span>
              </div>
              <h3 className="text-xs font-bold text-white line-clamp-2">
                {r.topic}
              </h3>
            </div>
          ))}
        </div>

        {/* Right Side: Active Research Report Viewer (70%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {activeReport ? (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Executive Summary Card */}
              <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl">
                <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase block">
                  Executive Briefing
                </span>
                <h2 className="text-lg font-bold text-white">
                  {activeReport.topic}
                </h2>
                <p className="text-xs text-gray-300 leading-relaxed">
                  {activeReport.executive_summary}
                </p>
              </div>

              {/* Key Findings */}
              {activeReport.key_findings && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-gray-400 uppercase font-mono">
                    Key Empirical Findings
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {activeReport.key_findings.map((f, idx) => (
                      <div key={idx} className="p-3.5 rounded-2xl bg-[#0F1117] border border-[#242833] text-xs text-gray-200 flex items-start gap-2.5">
                        <FaCheckCircle className="text-cyan-400 shrink-0 mt-0.5" size={12} />
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cited Sources */}
              {activeReport.sources && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-gray-400 uppercase font-mono">
                    Verified Source References ({activeReport.sources.length})
                  </h3>
                  <div className="space-y-2">
                    {activeReport.sources.map((s, idx) => (
                      <div key={idx} className="p-3.5 rounded-2xl bg-[#0F1117] border border-[#242833] flex items-center justify-between gap-3 text-xs">
                        <div className="space-y-0.5 min-w-0">
                          <a href={s.url} target="_blank" rel="noreferrer" className="font-bold text-cyan-300 hover:underline flex items-center gap-1.5 truncate">
                            <span>{s.title}</span>
                            <FaExternalLinkAlt size={9} />
                          </a>
                          <p className="text-[11px] text-gray-400 truncate">{s.summary}</p>
                        </div>
                        <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 font-mono text-[10px] shrink-0 font-bold">
                          {Math.round(s.relevance_score * 100)}% Match
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Markdown Deliverable */}
              <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4">
                <span className="text-[10px] font-mono text-gray-500 uppercase block font-bold">
                  Synthesized Technical RFC
                </span>
                <div className="text-xs font-mono text-gray-300 whitespace-pre-wrap leading-relaxed bg-[#08090D] p-5 rounded-2xl border border-[#1C202B]">
                  {activeReport.markdown_report}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select or run a research topic to view report
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
