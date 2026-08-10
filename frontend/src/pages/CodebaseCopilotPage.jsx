import React, { useState, useEffect, useRef } from 'react';
import { FaRobot, FaPaperPlane, FaTerminal, FaSearch, FaShieldAlt, FaRocket, FaBug, FaTachometerAlt, FaProjectDiagram, FaBrain, FaTimes, FaSpinner, FaCheckCircle, FaExclamationTriangle, FaThumbsUp, FaThumbsDown } from 'react-icons/fa';
import { askCopilot, executeCopilotPlan, fetchCopilotHistory, submitCopilotFeedback } from '../services/copilot';

const QUICK_COMMANDS = [
  { label: '/explain', prompt: '/explain How does authentication work in this project?' },
  { label: '/search', prompt: '/search Where is JWT authentication implemented?' },
  { label: '/test', prompt: '/test Run Playwright browser smoke tests' },
  { label: '/debug', prompt: '/debug Why is checkout failing?' },
  { label: '/security', prompt: '/security Find active vulnerabilities' },
  { label: '/performance', prompt: '/performance Why is the API latency slow?' },
  { label: '/whatif', prompt: '/whatif What happens if we replace PostgreSQL with MongoDB?' },
  { label: '/deploy', prompt: '/deploy Deploy the latest version' },
];

export default function CodebaseCopilotPage({ projectId = 'aiforge-demo' }) {
  const [messages, setMessages] = useState([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [progressSteps, setProgressSteps] = useState([]);
  const [showContext, setShowContext] = useState(false);
  const [activeContext, setActiveContext] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSession();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, progressSteps]);

  const loadSession = async () => {
    try {
      const res = await fetchCopilotHistory(projectId);
      if (res?.session?.messages) {
        setMessages(res.session.messages);
      }
    } catch (err) {
      console.warn('Failed to load copilot session:', err);
    }
  };

  const handleSend = async (customPrompt = null) => {
    const promptToSend = customPrompt || inputPrompt;
    if (!promptToSend.trim() || loading) return;

    setInputPrompt('');
    setLoading(true);
    setProgressSteps([
      { step: 'Understanding request...', status: 'IN_PROGRESS' },
      { step: 'Checking Prompt Guard security...', status: 'IN_PROGRESS' },
      { step: 'Checking Engineering DNA & Memory...', status: 'IN_PROGRESS' },
    ]);

    try {
      const res = await askCopilot(projectId, promptToSend);
      if (res?.message) {
        setMessages((prev) => [...prev, res.message]);
        if (res.message.context_used) setActiveContext(res.message.context_used);
      }
    } catch (err) {
      alert(`Copilot error: ${err.message}`);
    } finally {
      setLoading(false);
      setProgressSteps([]);
    }
  };

  const handleExecutePlan = async (planId) => {
    try {
      const res = await executeCopilotPlan(projectId, planId);
      if (res?.result) {
        await loadSession();
      }
    } catch (err) {
      alert(`Plan execution failed: ${err.message}`);
    }
  };

  const handleFeedback = async (msgId, rating) => {
    try {
      await submitCopilotFeedback(projectId, 'session_active', msgId, rating);
      alert(`Feedback recorded: ${rating}`);
    } catch (err) {
      console.warn('Feedback failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none flex flex-col justify-between">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-cyan-600/20 border border-cyan-500/40 rounded-xl text-cyan-400">
            <FaRobot className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🧠 AI Codebase Copilot & Natural-Language Control
              <span className="text-xs px-2.5 py-0.5 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-full font-mono">
                LANGGRAPH MULTI-AGENT COPILOT V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Natural-Language Software Querying, Dynamic Context Assembly, Change Previews & High-Risk Confirmation.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowContext(!showContext)}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow font-mono"
        >
          <FaProjectDiagram /> {showContext ? 'Hide Context Drawer' : 'Inspect Active Context'}
        </button>
      </div>

      {/* QUICK COMMAND PALETTE */}
      <div className="flex flex-wrap gap-2 font-mono text-xs">
        {QUICK_COMMANDS.map((cmd) => (
          <button
            key={cmd.label}
            onClick={() => handleSend(cmd.prompt)}
            className="px-3 py-1.5 bg-slate-950/80 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 text-cyan-300 rounded-xl transition font-bold"
          >
            {cmd.label}
          </button>
        ))}
      </div>

      {/* MAIN CHAT & CONTEXT AREA */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 font-sans">
        {/* Chat Feed */}
        <div className={`space-y-4 ${showContext ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl h-[520px] overflow-y-auto space-y-4 font-mono text-xs">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`p-4 rounded-2xl border space-y-3 ${
                  m.sender === 'USER'
                    ? 'bg-slate-900/60 border-slate-800 text-slate-200 ml-12'
                    : 'bg-slate-950 border-cyan-500/40 text-white mr-6 shadow-lg'
                }`}
              >
                <div className="flex justify-between items-center border-b border-slate-800/80 pb-2 font-sans">
                  <span className="font-bold text-cyan-400 text-xs flex items-center gap-1.5">
                    {m.sender === 'USER' ? '👤 User' : '🤖 AIForge Copilot'}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">{m.timestamp?.split('T')[1]?.substring(0, 8)}</span>
                </div>

                <div className="whitespace-pre-wrap font-mono text-xs text-slate-200 leading-relaxed">
                  {m.text}
                </div>

                {/* Plan Card */}
                {m.plan && (
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-2 text-[11px] font-sans">
                    <div className="font-bold text-amber-400 flex items-center gap-2">
                      <FaExclamationTriangle /> Change Preview (Risk: {m.plan.risk_level})
                    </div>
                    <div className="text-slate-300 font-mono">Affected Files: {m.plan.affected_files?.join(', ')}</div>
                    {m.action_buttons?.length > 0 && (
                      <div className="flex gap-2 pt-1">
                        <button
                          onClick={() => handleExecutePlan(m.plan.plan_id)}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow transition"
                        >
                          [ Confirm & Execute ]
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Feedback */}
                {m.sender === 'COPILOT' && (
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 border-t border-slate-900 pt-2">
                    <span>Helpful?</span>
                    <button onClick={() => handleFeedback(m.id, 'USEFUL')} className="hover:text-emerald-400 transition"><FaThumbsUp /></button>
                    <button onClick={() => handleFeedback(m.id, 'NOT_USEFUL')} className="hover:text-rose-400 transition"><FaThumbsDown /></button>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-2xl text-slate-400 font-mono text-xs space-y-1">
                <div className="flex items-center gap-2 font-bold text-cyan-400">
                  <FaSpinner className="animate-spin" /> Copilot Agent Orchestration...
                </div>
                {progressSteps.map((s, idx) => (
                  <div key={idx} className="text-[10px] text-slate-400 pl-4">✓ {s.step}</div>
                ))}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Prompt Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Ask Copilot anything (e.g. 'Why is checkout failing?', 'Deploy the latest version', 'Find security flaws')..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl px-5 py-3.5 text-xs font-mono text-white outline-none focus:border-cyan-500 shadow-xl"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs rounded-2xl shadow-xl transition flex items-center gap-2"
            >
              {loading ? <FaSpinner className="animate-spin" /> : <FaPaperPlane />} Send
            </button>
          </form>
        </div>

        {/* Context Drawer Sidebar */}
        {showContext && (
          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 border-b border-slate-800 pb-2 flex items-center gap-2">
              <FaBrain /> Context Used Debugger
            </h3>

            {activeContext ? (
              <div className="space-y-3 font-sans text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">DNA Nodes</span>
                  <div className="text-white font-mono">{activeContext.dna_nodes?.join(', ')}</div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Engineering Memories</span>
                  <div className="text-emerald-400 font-mono">{activeContext.memories?.join('; ')}</div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Readiness Score</span>
                  <div className="text-cyan-400 font-mono">{activeContext.readiness_score}/100</div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Recent Commits</span>
                  <div className="text-purple-400 font-mono text-[10px]">{activeContext.recent_git_commits?.join('\n')}</div>
                </div>
              </div>
            ) : (
              <div className="text-slate-500">Send a request to inspect active context sources.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
