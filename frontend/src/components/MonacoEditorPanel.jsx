import React, { useState } from 'react';
import { FaCode, FaPlay, FaCopy, FaCheck } from 'react-icons/fa';

export default function MonacoEditorPanel({
  initialCode = "import React from 'react';\n\nexport default function App() {\n  return (\n    <div className=\"p-4 bg-slate-900 text-white rounded-lg\">\n      <h1>AIForge V2 Monaco Code Editor</h1>\n    </div>\n  );\n}",
  language = "javascript",
  filename = "App.jsx"
}) {
  const [code, setCode] = useState(initialCode);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl font-mono text-xs mb-6">
      {/* Editor Header Bar */}
      <div className="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FaCode className="text-indigo-400 w-4 h-4" />
          <span className="font-bold text-white text-xs">{filename}</span>
          <span className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded uppercase font-semibold">
            {language}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] px-2.5 py-1 rounded transition flex items-center gap-1 cursor-pointer"
          >
            {copied ? <FaCheck className="text-emerald-400" /> : <FaCopy />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="p-4 bg-slate-950 text-slate-200 min-h-[220px] max-h-[400px] overflow-y-auto leading-relaxed">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck="false"
          className="w-full h-56 bg-transparent text-indigo-200 outline-none font-mono text-xs resize-none leading-relaxed"
        />
      </div>

      {/* Footer Status Bar */}
      <div className="bg-slate-900 border-t border-slate-800 px-4 py-1.5 flex items-center justify-between text-[10px] text-slate-400">
        <span>Monaco Editor Engine | IntelliSense Active</span>
        <span>UTF-8 | Lines: {code.split('\n').length}</span>
      </div>
    </div>
  );
}
