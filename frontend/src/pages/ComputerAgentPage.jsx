import React, { useState, useEffect } from "react";
import { 
  FaGlobe, FaRobot, FaPlay, FaCheckCircle, FaLock, 
  FaArrowRight, FaTerminal, FaCode, FaExternalLinkAlt, FaSave, FaSearch 
} from "react-icons/fa";
import { fetchBrowserSessions, createBrowserSession } from "../services/sprintApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const SAMPLE_BROWSER_GOALS = [
  "Navigate to FastAPI documentation, research WebSockets endpoint specs, and extract connection protocol.",
  "Open GitHub repo, inspect open issues for JWT security vulnerabilities, and extract report.",
  "Navigate to Redpanda documentation, research Kafka compatibility layer, and extract topic specs."
];

export default function ComputerAgentPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);

  // New Browser Action
  const [goal, setGoal] = useState("");
  const [targetUrl, setTargetUrl] = useState("https://fastapi.tiangolo.com/advanced/websockets/");
  const [isBrowsing, setIsBrowsing] = useState(false);

  const loadData = async () => {
    try {
      const list = await fetchBrowserSessions();
      setSessions(list || []);
      if (list && list.length > 0 && !selectedSession) {
        setSelectedSession(list[0]);
      }
    } catch (err) {
      console.error("Error loading browser sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleLaunchSession = async (gToRun) => {
    const text = gToRun || goal;
    if (!text.trim()) return;
    setIsBrowsing(true);
    setGoal(text);
    toast("Computer Agent Launching Isolated Sandbox Browser Session...", { icon: "🌐" });
    try {
      const sess = await createBrowserSession({
        goal: text.trim(),
        targetUrl
      });
      setSessions([sess, ...sessions]);
      setSelectedSession(sess);
      toast.success("Web Page Navigated & Specs Extracted!", { icon: "✓" });
    } catch (err) {
      toast.error("Browser session failed");
    } finally {
      setIsBrowsing(false);
    }
  };

  const handleSaveExtracted = () => {
    if (!selectedSession) return;
    saveOutputItem({
      title: `Browser Agent Data: ${selectedSession.page_title}`,
      category: "Research",
      content: `# Browser Automation Result\n\n- **URL**: ${selectedSession.current_url}\n- **Goal**: ${selectedSession.goal}\n\n## Extracted Data\n\`\`\`json\n${JSON.stringify(selectedSession.extracted_data, null, 2)}\n\`\`\``,
      language: "json"
    });
    toast.success("Saved Extracted Data to Library!", { icon: "📑" });
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-emerald-500 via-teal-600 to-cyan-500 text-white shadow-lg shadow-emerald-500/20">
            <FaGlobe size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Computer-Using AI / Browser Agent
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                Isolated Sandbox Browser
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Visual Screen Comprehension, DOM Navigation, Technical Spec Extraction & Zero-Trust Domain Allowlists
            </p>
          </div>
        </div>

        {/* Global Session Counter */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-emerald-300 font-bold">
            {sessions.length} Browser Sessions Recorded
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Browser Control & Goal Dispatch (55%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar border-r border-[#242833]">
          {/* Dispatch Input Box */}
          <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl text-xs">
            <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold flex items-center gap-1.5">
              <FaRobot size={10} /> State Web Navigation & Extraction Goal
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <input
                  type="text"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="e.g. Navigate to FastAPI docs and extract WebSockets handler signature..."
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-emerald-500 rounded-xl p-3 text-xs text-white outline-none"
                />
              </div>
              <div>
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-emerald-500 rounded-xl p-3 text-xs text-white outline-none font-mono"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <span className="text-[10px] font-mono text-gray-500">Allowed: fastapi.tiangolo.com, github.com, aiforge.dev</span>
              <button
                onClick={() => handleLaunchSession()}
                disabled={isBrowsing || !goal.trim()}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs flex items-center gap-1.5"
              >
                <FaPlay size={10} />
                <span>{isBrowsing ? "Automating Browser..." : "Launch Computer Agent"}</span>
              </button>
            </div>

            {/* Quick Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {SAMPLE_BROWSER_GOALS.map((sg, i) => (
                <button
                  key={i}
                  onClick={() => handleLaunchSession(sg)}
                  className="px-2.5 py-1 rounded-lg bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] text-[10px] text-gray-400 hover:text-emerald-300 font-mono transition cursor-pointer text-left truncate max-w-sm"
                >
                  🌐 {sg}
                </button>
              ))}
            </div>
          </div>

          {/* Session List */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Recorded Browser Sessions ({sessions.length})
            </span>

            <div className="space-y-3">
              {sessions.map((sess) => (
                <div
                  key={sess.session_id}
                  onClick={() => setSelectedSession(sess)}
                  className={`p-4 rounded-2xl cursor-pointer transition space-y-2 ${
                    selectedSession?.session_id === sess.session_id
                      ? "bg-[#101D1A] border border-emerald-500 shadow-xl"
                      : "bg-[#0F1117] hover:bg-[#151821] border border-[#242833]"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                      {sess.status}
                    </span>
                    <span className="text-gray-400 font-bold truncate max-w-xs">{sess.current_url}</span>
                  </div>

                  <h3 className="font-bold text-xs text-white">{sess.goal}</h3>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Virtual Browser Screen & Extracted Data (45%) */}
        <div className="w-[480px] bg-[#0F1117] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {selectedSession ? (
            <div className="space-y-5">
              {/* Browser Address Bar */}
              <div className="p-3 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                  </div>
                  <div className="flex-1 bg-[#151821] border border-[#242833] rounded-lg px-3 py-1 text-[11px] font-mono text-emerald-300 truncate">
                    🔒 {selectedSession.current_url}
                  </div>
                </div>
                <h3 className="font-bold text-white text-xs pt-1">{selectedSession.page_title}</h3>
              </div>

              {/* Action History Stepper */}
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block">
                  Executed Browser Actions ({selectedSession.actions_history?.length || 0})
                </span>

                <div className="space-y-2">
                  {(selectedSession.actions_history || []).map((act, idx) => (
                    <div key={act.id || idx} className="p-3 bg-[#08090D] border border-[#1C202B] rounded-xl space-y-1 text-xs">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="text-emerald-300 font-bold">[{act.action_type}]</span>
                        <span className="text-gray-500">{act.duration_seconds}s</span>
                      </div>
                      <p className="text-gray-300 text-[11px] leading-relaxed">{act.description}</p>
                      <span className="text-[10px] font-mono text-gray-400 block bg-black/40 p-1.5 rounded">
                        ✓ {act.result_summary}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Extracted Structured Data Box */}
              <div className="space-y-2 pt-2 border-t border-[#1C202B]">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
                    Grounded Extracted Specifications
                  </span>
                  <button
                    onClick={handleSaveExtracted}
                    className="px-2.5 py-1 bg-[#1E293B] hover:bg-[#334155] text-cyan-300 rounded-lg text-[10px] font-semibold border border-gray-700 cursor-pointer flex items-center gap-1"
                  >
                    <FaSave size={9} /> Save to Library
                  </button>
                </div>

                <pre className="p-3.5 rounded-2xl bg-[#08090D] border border-[#1C202B] text-xs font-mono text-cyan-300 overflow-x-auto">
                  {JSON.stringify(selectedSession.extracted_data, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select a browser session to inspect actions & extracted specifications
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
