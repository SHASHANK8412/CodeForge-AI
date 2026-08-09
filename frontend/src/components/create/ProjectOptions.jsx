import React, { useState } from 'react';
import { FaShieldAlt, FaVial, FaBook, FaDocker, FaFileAlt, FaLock, FaChevronDown, FaChevronUp, FaMicrochip } from 'react-icons/fa';

export default function ProjectOptions({ options, setOptions }) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const toggleOption = (key) => {
    setOptions({ ...options, [key]: !options[key] });
  };

  const handleModelChange = (val) => {
    setOptions({ ...options, model: val });
  };

  const standardToggles = [
    { key: 'authentication', label: 'Authentication', desc: 'JWT login, sessions & roles', icon: FaLock },
    { key: 'testing', label: 'Automated Testing', desc: 'Pytest & unit test suites', icon: FaVial },
    { key: 'documentation', label: 'API Documentation', desc: 'Swagger & OpenAPI docs', icon: FaBook },
    { key: 'docker', label: 'Docker Configuration', desc: 'Dockerfile & docker-compose', icon: FaDocker },
    { key: 'readme_generation', label: 'README Generation', desc: 'Project setup & guide', icon: FaFileAlt },
    { key: 'security_review', label: 'Security Review', desc: 'SAST & vulnerability scan', icon: FaShieldAlt },
  ];

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl backdrop-blur-md font-sans">
      <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
        Project Capabilities & Agent Controls
      </h3>

      {/* Standard Toggles Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {standardToggles.map((item) => {
          const Icon = item.icon;
          const isEnabled = options[item.key];
          return (
            <div
              key={item.key}
              onClick={() => toggleOption(item.key)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                isEnabled
                  ? 'bg-slate-900/90 border-cyan-500/40 text-slate-100 shadow-md'
                  : 'bg-slate-950 border-slate-800 text-slate-400 opacity-70 hover:opacity-100'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isEnabled ? 'bg-cyan-500/10 text-cyan-400' : 'bg-slate-800 text-slate-500'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-white">{item.label}</div>
                  <div className="text-[11px] text-slate-400">{item.desc}</div>
                </div>
              </div>

              {/* Custom Toggle Switch */}
              <div className={`w-10 h-5 flex items-center rounded-full p-0.5 transition-colors ${isEnabled ? 'bg-cyan-500 justify-end' : 'bg-slate-800 justify-start'}`}>
                <div className="w-4 h-4 rounded-full bg-white shadow-md" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Advanced Options Accordion */}
      <div className="border-t border-slate-800 pt-4">
        <button
          type="button"
          onClick={() => setAdvancedOpen(!advancedOpen)}
          className="flex items-center justify-between w-full text-xs font-bold uppercase tracking-wider text-slate-300 hover:text-white transition"
        >
          <span className="flex items-center gap-2">
            <FaMicrochip className="text-indigo-400" /> Advanced Options
          </span>
          {advancedOpen ? <FaChevronUp className="w-3.5 h-3.5" /> : <FaChevronDown className="w-3.5 h-3.5" />}
        </button>

        {advancedOpen && (
          <div className="mt-4 space-y-4 pt-3 border-t border-slate-800/60 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Use Local LLM Toggle */}
              <div
                onClick={() => toggleOption('local_llm')}
                className={`p-3 rounded-xl border cursor-pointer flex items-center justify-between ${
                  options.local_llm ? 'bg-indigo-950/40 border-indigo-500/40 text-slate-100' : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold text-white">Use Local LLM (Ollama)</div>
                  <div className="text-[11px] text-slate-400">Zero data egress, private inference</div>
                </div>
                <div className={`w-9 h-4.5 flex items-center rounded-full p-0.5 ${options.local_llm ? 'bg-indigo-500 justify-end' : 'bg-slate-800 justify-start'}`}>
                  <div className="w-3.5 h-3.5 rounded-full bg-white" />
                </div>
              </div>

              {/* Model Selection Dropdown */}
              <div>
                <label className="text-slate-300 font-semibold mb-1 block">Execution Model</label>
                <select
                  value={options.model}
                  onChange={(e) => handleModelChange(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-xs"
                >
                  <option value="qwen2.5-coder">qwen2.5-coder (14B Recommended)</option>
                  <option value="qwen2.5">qwen2.5 (14B General)</option>
                  <option value="llama3.3">llama3.3 (70B Quantized)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Enable RAG */}
              <div
                onClick={() => toggleOption('rag')}
                className={`p-3 rounded-xl border cursor-pointer flex items-center justify-between ${
                  options.rag ? 'bg-purple-950/40 border-purple-500/40 text-slate-100' : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold text-white">Enable RAG</div>
                  <div className="text-[11px] text-slate-400">Vector store retrieval</div>
                </div>
                <div className={`w-8 h-4 flex items-center rounded-full p-0.5 ${options.rag ? 'bg-purple-500 justify-end' : 'bg-slate-800 justify-start'}`}>
                  <div className="w-3 h-3 rounded-full bg-white" />
                </div>
              </div>

              {/* Enable Code Review */}
              <div
                onClick={() => toggleOption('code_review')}
                className={`p-3 rounded-xl border cursor-pointer flex items-center justify-between ${
                  options.code_review ? 'bg-cyan-950/40 border-cyan-500/40 text-slate-100' : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold text-white">Code Review</div>
                  <div className="text-[11px] text-slate-400">Quality gate inspection</div>
                </div>
                <div className={`w-8 h-4 flex items-center rounded-full p-0.5 ${options.code_review ? 'bg-cyan-500 justify-end' : 'bg-slate-800 justify-start'}`}>
                  <div className="w-3 h-3 rounded-full bg-white" />
                </div>
              </div>

              {/* Enable Automated Repair */}
              <div
                onClick={() => toggleOption('auto_repair')}
                className={`p-3 rounded-xl border cursor-pointer flex items-center justify-between ${
                  options.auto_repair ? 'bg-emerald-950/40 border-emerald-500/40 text-slate-100' : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold text-white">Automated Repair</div>
                  <div className="text-[11px] text-slate-400">Bounded self-correction</div>
                </div>
                <div className={`w-8 h-4 flex items-center rounded-full p-0.5 ${options.auto_repair ? 'bg-emerald-500 justify-end' : 'bg-slate-800 justify-start'}`}>
                  <div className="w-3 h-3 rounded-full bg-white" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
