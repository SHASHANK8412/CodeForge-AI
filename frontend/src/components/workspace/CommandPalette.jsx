import React, { useEffect, useMemo, useState } from 'react';
import {
  FaSearch,
  FaFileCode,
  FaPlay,
  FaBug,
  FaBrain,
  FaLightbulb,
  FaMagic,
  FaDownload,
  FaRocket,
  FaTerminal
} from 'react-icons/fa';

const COMMANDS = [
  { id: 'open_file', label: 'Open File', description: 'Search and open a file in the editor', icon: FaFileCode },
  { id: 'search_files', label: 'Search Project (Ctrl+Shift+F)', description: 'Search symbols and text across project', icon: FaSearch },
  { id: 'run_tests', label: 'Run Tests', description: 'Execute full test suite with assertions', icon: FaPlay },
  { id: 'run_debug_agent', label: 'Debug Project with AI', description: 'Autonomous debug, fix, and retest loop', icon: FaBug },
  { id: 'open_memory', label: 'Open Project Memory', description: 'View architectural decisions and codebase intelligence', icon: FaBrain },
  { id: 'explain_code', label: 'Explain Selected Code', description: 'Ask AI to analyze selected function or module', icon: FaLightbulb },
  { id: 'refactor_code', label: 'Refactor Selected Code', description: 'Generate clean refactored implementation', icon: FaMagic },
  { id: 'generate_tests', label: 'Generate Tests', description: 'Generate comprehensive pytest/jest test suite', icon: FaPlay },
  { id: 'toggle_terminal', label: 'Toggle Terminal / Output', description: 'Show or hide bottom execution panel', icon: FaTerminal },
  { id: 'deploy', label: 'Deploy Application', description: 'Deploy project to cloud container', icon: FaRocket },
  { id: 'export_zip', label: 'Export Project (ZIP)', description: 'Download complete source code bundle', icon: FaDownload },
];

export default function CommandPalette({ open, onClose, onExecute, activeFile }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1));
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      }
      if (event.key === 'Enter') {
        event.preventDefault();
        const command = filtered[selectedIndex];
        if (command) {
          onExecute(command.id);
        }
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, selectedIndex, onClose, onExecute]);

  const filtered = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    if (!normalized) return COMMANDS;
    return COMMANDS.filter((cmd) => cmd.label.toLowerCase().includes(normalized) || cmd.description.toLowerCase().includes(normalized));
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center p-4">
      <div className="mt-20 w-full max-w-xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden font-sans">
        <div className="px-4 py-3 border-b border-slate-800 bg-[#080d1a] flex items-center gap-2.5">
          <FaSearch className="w-4 h-4 text-cyan-400 shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder={activeFile ? `Command palette (${activeFile.name})...` : 'Type a command or search...'}
            className="w-full bg-transparent outline-none text-slate-100 placeholder-slate-500 text-sm font-sans"
          />
          <kbd className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-slate-400">ESC</kbd>
        </div>

        <div className="max-h-80 overflow-y-auto custom-scrollbar p-1.5 space-y-1">
          {filtered.map((cmd, idx) => {
            const Icon = cmd.icon;
            const isSelected = idx === selectedIndex;
            return (
              <button
                key={cmd.id}
                onClick={() => onExecute(cmd.id)}
                className={`w-full text-left px-3.5 py-2.5 rounded-xl transition flex items-center gap-3 cursor-pointer ${
                  isSelected ? 'bg-indigo-600/25 text-white border border-indigo-500/30' : 'text-slate-300 hover:bg-slate-900'
                }`}
              >
                <div className={`p-2 rounded-lg ${isSelected ? 'bg-indigo-500/20 text-cyan-300' : 'bg-slate-900 text-slate-400'}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-xs text-white truncate">{cmd.label}</div>
                  <div className="text-[11px] text-slate-400 truncate">{cmd.description}</div>
                </div>
                {isSelected && <span className="text-[10px] font-mono text-cyan-400 font-bold">↵</span>}
              </button>
            );
          })}
          {filtered.length === 0 && <div className="p-4 text-slate-500 text-xs text-center">No commands found matching "{query}"</div>}
        </div>
      </div>
    </div>
  );
}
