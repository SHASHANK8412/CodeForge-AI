import React, { useState } from 'react';
import {
  FaRobot,
  FaPaperPlane,
  FaSpinner,
  FaLightbulb,
  FaWrench,
  FaChartLine,
  FaMagic,
  FaCheckCircle,
  FaLayerGroup,
  FaBrain,
  FaChevronDown,
  FaChevronUp
} from 'react-icons/fa';
import { askAssistant } from '../../services/project';

export default function AIAssistant({ activeFile, selectedCode, projectId = 'AIForge Project' }) {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello! I am AIForge Assistant. I have full context on your codebase, project architecture, active file, and symbol dependency graph. How can I help?'
    }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [showContextDetails, setShowContextDetails] = useState(false);

  const selectedLinesCount = selectedCode ? selectedCode.split('\n').length : 0;

  const handleSend = async (customPrompt = inputMsg) => {
    if (!customPrompt || customPrompt.trim().length === 0) return;

    const userText = customPrompt;
    setInputMsg('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setSending(true);

    const responseText = await askAssistant(
      userText,
      activeFile ? activeFile.path : '',
      selectedCode || ''
    );

    setSending(false);
    setMessages((prev) => [...prev, { sender: 'ai', text: responseText }]);
  };

  return (
    <div className="bg-[#0F1117] w-full flex-1 min-h-0 flex flex-col font-sans overflow-hidden">
      {/* Header & AI Context Indicator */}
      <div className="border-b border-[#242833] bg-[#0F1117] shrink-0">
        <div className="p-2.5 flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-[#F5F7FA]">
          <div className="flex items-center gap-2">
            <FaRobot className="text-[#8D5CF6] w-3.5 h-3.5" />
            <span>AI Workspace Assistant</span>
          </div>
          <button
            onClick={() => setShowContextDetails(!showContextDetails)}
            className="flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-300 font-mono lowercase cursor-pointer"
          >
            <span>context</span>
            {showContextDetails ? <FaChevronUp className="w-2.5 h-2.5" /> : <FaChevronDown className="w-2.5 h-2.5" />}
          </button>
        </div>

        {/* AI Context Transparency Banner */}
        <div className="px-2.5 pb-2">
          <div className="p-2 rounded-lg bg-[#08090D] border border-[#242833] text-[10px] font-mono text-[#9AA1B2] space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <FaCheckCircle className="w-2.5 h-2.5 shrink-0" />
              <span className="truncate">File: {activeFile ? activeFile.path : 'None open'}</span>
            </div>
            {selectedCode && (
              <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                <FaCheckCircle className="w-2.5 h-2.5 shrink-0" />
                <span>Selected: {selectedLinesCount} line(s)</span>
              </div>
            )}
            {showContextDetails && (
              <div className="pt-1 mt-1 border-t border-slate-800 space-y-1 text-[9px] text-slate-400">
                <div className="flex items-center gap-1.5 text-violet-400">
                  <FaBrain className="w-2.5 h-2.5 shrink-0" />
                  <span>Project Memory: Active architecture loaded</span>
                </div>
                <div className="flex items-center gap-1.5 text-blue-400">
                  <FaLayerGroup className="w-2.5 h-2.5 shrink-0" />
                  <span>Codebase Intelligence: Symbol index linked</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages Output List */}
      <div className="flex-1 min-h-0 p-2.5 overflow-y-auto space-y-2.5 text-xs custom-scrollbar">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-2.5 rounded-xl border transition ${
              msg.sender === 'user'
                ? 'bg-[#8D5CF6]/15 border-[#8D5CF6]/30 text-[#F5F7FA] ml-3 shadow-lg shadow-violet-500/5'
                : 'bg-[#08090D] border-[#242833] text-[#9AA1B2] mr-3'
            }`}
          >
            <div className="font-bold text-[9px] font-mono text-[#8D5CF6] mb-0.5">
              {msg.sender === 'user' ? 'You' : 'AIForge'}
            </div>
            <p className="leading-relaxed whitespace-pre-wrap text-[11px] font-sans">{msg.text}</p>
          </div>
        ))}
        {sending && (
          <div className="p-2 bg-[#08090D] border border-[#242833] rounded-xl text-xs text-[#9AA1B2] flex items-center gap-2">
            <FaSpinner className="animate-spin text-[#8D5CF6]" />
            <span className="text-[11px]">Retrieving symbols and project memory...</span>
          </div>
        )}
      </div>

      {/* Quick Action Chips */}
      <div className="p-1.5 border-t border-[#242833] bg-[#0F1117] flex flex-wrap gap-1 text-[10px] shrink-0 select-none">
        <button
          onClick={() => handleSend(`Explain the core logic and relationships in ${activeFile ? activeFile.path : 'the codebase'}`)}
          className="px-1.5 py-0.5 bg-[#08090D] hover:bg-[#151821] border border-[#242833] text-[#9AA1B2] hover:text-[#F5F7FA] rounded flex items-center gap-1 transition cursor-pointer"
        >
          <FaLightbulb className="text-yellow-400 text-[9px]" /> Explain
        </button>
        <button
          onClick={() => handleSend(`Fix any potential bugs, types, or syntax issues in ${activeFile ? activeFile.path : 'this file'}`)}
          className="px-1.5 py-0.5 bg-[#08090D] hover:bg-[#151821] border border-[#242833] text-[#9AA1B2] hover:text-[#F5F7FA] rounded flex items-center gap-1 transition cursor-pointer"
        >
          <FaWrench className="text-cyan-400 text-[9px]" /> Fix
        </button>
        <button
          onClick={() => handleSend(`Refactor and optimize code in ${activeFile ? activeFile.path : 'this file'}`)}
          className="px-1.5 py-0.5 bg-[#08090D] hover:bg-[#151821] border border-[#242833] text-[#9AA1B2] hover:text-[#F5F7FA] rounded flex items-center gap-1 transition cursor-pointer"
        >
          <FaChartLine className="text-emerald-400 text-[9px]" /> Refactor
        </button>
        <button
          onClick={() => handleSend(`Generate comprehensive pytest / jest test cases for ${activeFile ? activeFile.path : 'the main module'}`)}
          className="px-1.5 py-0.5 bg-[#08090D] hover:bg-[#151821] border border-[#242833] text-[#9AA1B2] hover:text-[#F5F7FA] rounded flex items-center gap-1 transition cursor-pointer"
        >
          <FaMagic className="text-purple-400 text-[9px]" /> Tests
        </button>
      </div>

      {/* Chat Input Bar */}
      <div className="p-2 bg-[#0F1117] border-t border-[#242833] flex items-center gap-1.5 shrink-0">
        <input
          type="text"
          value={inputMsg}
          onChange={(e) => setInputMsg(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask AIForge (with file & memory context)..."
          className="flex-1 bg-[#08090D] border border-[#242833] rounded-md px-2.5 py-1.5 text-xs text-[#F5F7FA] placeholder-[#9AA1B2]/40 focus:outline-none focus:border-[#8D5CF6] font-sans"
        />
        <button
          onClick={() => handleSend()}
          disabled={sending || !inputMsg.trim()}
          className="px-3 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] disabled:opacity-50 text-white rounded-md text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
        >
          <FaPaperPlane className="w-2.5 h-2.5" />
        </button>
      </div>
    </div>
  );
}
