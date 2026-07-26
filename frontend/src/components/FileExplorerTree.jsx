import React, { useState } from 'react';
import { FaFolder, FaFileCode, FaCopy, FaCheck } from 'react-icons/fa';

export default function FileExplorerTree({ files = {} }) {
  const [selectedFile, setSelectedFile] = useState(Object.keys(files)[0] || '');
  const [copied, setCopied] = useState(false);

  const fileKeys = Object.keys(files);

  if (fileKeys.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 bg-slate-900 rounded-xl border border-slate-800">
        No project files generated yet.
      </div>
    );
  }

  const activeContent = files[selectedFile] || '';

  const handleCopy = () => {
    navigator.clipboard.writeText(activeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl text-slate-100 grid grid-cols-1 md:grid-cols-4 min-h-[420px]">
      {/* File Tree Sidebar */}
      <div className="border-r border-slate-800 bg-slate-950/60 p-4 font-mono text-xs overflow-y-auto max-h-[500px]">
        <div className="text-slate-400 font-sans font-semibold text-xs mb-3 uppercase tracking-wider flex items-center gap-2">
          <FaFolder className="w-4 h-4 text-indigo-400" />
          Project File Explorer
        </div>
        <div className="space-y-1">
          {fileKeys.map((filename) => {
            const isSelected = selectedFile === filename;
            return (
              <button
                key={filename}
                onClick={() => setSelectedFile(filename)}
                className={`w-full text-left px-2.5 py-1.5 rounded flex items-center gap-2 transition-all ${
                  isSelected
                    ? 'bg-indigo-600/30 text-indigo-300 font-semibold border border-indigo-500/40'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <FaFileCode className={`w-3.5 h-3.5 ${isSelected ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span className="truncate">{filename}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Code Viewer Panel */}
      <div className="md:col-span-3 flex flex-col bg-slate-900">
        <div className="bg-slate-950 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between font-mono text-xs">
          <span className="text-indigo-300 font-medium">{selectedFile || 'Select a file'}</span>
          {activeContent && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors cursor-pointer"
            >
              {copied ? <FaCheck className="w-3.5 h-3.5 text-emerald-400" /> : <FaCopy className="w-3.5 h-3.5 text-slate-400" />}
              {copied ? 'Copied!' : 'Copy Code'}
            </button>
          )}
        </div>
        <div className="p-4 font-mono text-xs text-slate-200 overflow-x-auto overflow-y-auto max-h-[460px] bg-slate-900 leading-relaxed">
          <pre>
            <code>{activeContent || '// Select a file from the explorer on the left to preview code'}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
