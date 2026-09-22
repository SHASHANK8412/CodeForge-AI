import React, { useState } from 'react';
import { FaCommentAlt, FaSpinner, FaFileCode, FaBookOpen } from 'react-icons/fa';
import { chatSoftwareAssistant } from '../services/intelligence';

export default function SoftwareAssistantPage({ projectId = 'aiforge-demo' }) {
  const [messages, setMessages] = useState([
    { sender: 'ai', text: "Hello! I am your AI Software Assistant. Ask me anything about your generated codebase structure, security, dependencies, or decisions.", files: [], citations: [] }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input;
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const res = await chatSoftwareAssistant(projectId, userText);
      const resp = res.response;
      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: resp.answer,
          files: resp.relevant_files || [],
          citations: resp.citations || []
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'ai', text: `Failed to answer query: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 flex flex-col">
      {/* Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex items-center gap-4 shrink-0">
        <div className="p-3 bg-indigo-600/20 border border-indigo-500/40 rounded-xl text-indigo-400">
          <FaCommentAlt className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            Talk to Your Software — Interactive Assistant
          </h1>
          <p className="text-xs text-slate-400">
            Ask structural and dependency questions powered by Code + Day 12 Memory + Day 13 RAG + DNA Graph.
          </p>
        </div>
      </div>

      {/* Chat Messages Window */}
      <div className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 overflow-y-auto min-h-[400px]">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-2xl p-4 rounded-2xl text-xs space-y-2 font-sans ${
                m.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none'
              }`}
            >
              <p className="whitespace-pre-line leading-relaxed">{m.text}</p>

              {(m.files || []).length > 0 && (
                <div className="pt-2 border-t border-slate-800/80 font-mono text-[11px] text-cyan-300 space-y-1">
                  <span className="text-slate-400 font-bold block">Relevant Code Files:</span>
                  {m.files.map((f, i) => (
                    <div key={i} className="flex items-center gap-1.5"><FaFileCode /> {f}</div>
                  ))}
                </div>
              )}

              {(m.citations || []).length > 0 && (
                <div className="pt-1 font-mono text-[10px] text-indigo-300 flex flex-wrap gap-1.5">
                  {m.citations.map((c, i) => (
                    <span key={i} className="px-2 py-0.5 bg-indigo-950/60 border border-indigo-500/30 rounded">{c}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
            <FaSpinner className="w-4 h-4 animate-spin text-indigo-400" />
            <span>Searching RAG, DNA graph & Memory context…</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="flex gap-3 shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. Which APIs depend on the users table? or Why is auth implemented this way?"
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs text-white font-mono outline-none focus:border-indigo-500 transition"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-2 disabled:opacity-50"
        >
          Send Query
        </button>
      </form>
    </div>
  );
}
