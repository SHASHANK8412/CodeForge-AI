import React, { useState } from 'react';
import { FaRobot, FaPaperPlane, FaSpinner, FaQuestionCircle, FaDatabase, FaHeartbeat } from 'react-icons/fa';
import { askAssistant } from '../../services/project';

export default function DeploymentAssistant({ generationId }) {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'AIForge DevOps Assistant ready. I can assist with production environment variables, CORS origins, Docker deployment manifests, and health check probes. How can I help?'
    }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async (customText = inputMsg) => {
    if (!customText || customText.trim().length === 0) return;

    const userText = customText;
    setInputMsg('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setSending(true);

    const reply = await askAssistant(userText, 'Deployment Center Config', 'DevOps Target: Vercel + Render');
    setSending(false);
    setMessages((prev) => [...prev, { sender: 'ai', text: reply }]);
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaRobot className="text-cyan-400" /> AIForge DevOps & Deployment Assistant
        </h3>
      </div>

      <div className="bg-[#070b13] border border-slate-800/80 rounded-xl p-4 h-48 overflow-y-auto space-y-3 text-xs mb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-xl border ${
              msg.sender === 'user'
                ? 'bg-indigo-600/20 border-indigo-500/40 text-slate-200 ml-6'
                : 'bg-slate-900 border-slate-800 text-slate-300 mr-6'
            }`}
          >
            <div className="font-bold text-[10px] font-mono text-cyan-400 mb-1">
              {msg.sender === 'user' ? 'You' : 'DevOps Assistant'}
            </div>
            <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
          </div>
        ))}
        {sending && (
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-center gap-2">
            <FaSpinner className="animate-spin text-cyan-400" /> Analyzing deployment manifests...
          </div>
        )}
      </div>

      {/* Prompt Quick Chips */}
      <div className="flex flex-wrap gap-2 mb-4 text-xs font-sans">
        <button
          onClick={() => handleSend('Why did my deployment fail?')}
          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg flex items-center gap-1.5 transition"
        >
          <FaQuestionCircle className="text-amber-400" /> Why did my deployment fail?
        </button>

        <button
          onClick={() => handleSend('How do I configure PostgreSQL database connection strings?')}
          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg flex items-center gap-1.5 transition"
        >
          <FaDatabase className="text-purple-400" /> How do I configure PostgreSQL?
        </button>

        <button
          onClick={() => handleSend('Why is my health check failing on /health endpoint?')}
          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg flex items-center gap-1.5 transition"
        >
          <FaHeartbeat className="text-rose-400" /> Why is health check failing?
        </button>
      </div>

      {/* Input */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={inputMsg}
          onChange={(e) => setInputMsg(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask AIForge DevOps about deployment..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
        <button
          onClick={() => handleSend()}
          disabled={sending}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition disabled:opacity-50 flex items-center gap-1.5"
        >
          <FaPaperPlane className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
