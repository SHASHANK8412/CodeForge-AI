import React from 'react';
import { FaTimes, FaFileCode } from 'react-icons/fa';

export default function EditorTabs({ openFiles = [], activeFile, onSelectTab, onCloseTab, unsavedChanges = {} }) {
  if (!openFiles || openFiles.length === 0) return null;

  return (
    <div className="bg-slate-950 border-b border-slate-800/80 flex items-center overflow-x-auto font-sans text-xs select-none shrink-0">
      {openFiles.map((file, idx) => {
        const isActive = activeFile?.path === file.path;
        const hasUnsaved = unsavedChanges[file.path] !== undefined;
        return (
          <div
            key={idx}
            onClick={() => onSelectTab(file)}
            className={`flex items-center gap-2 px-3.5 py-2 border-r border-slate-800 cursor-pointer transition max-w-[200px] ${
              isActive
                ? 'bg-[#0b0f19] text-cyan-400 font-bold border-t-2 border-t-cyan-400'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <FaFileCode className="w-3 h-3 shrink-0" />
            <span className="truncate text-xs font-mono">
              {file.name}
              {hasUnsaved && <span className="ml-1 text-amber-400 font-bold">•</span>}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCloseTab(file);
              }}
              className="p-0.5 rounded text-slate-500 hover:text-white hover:bg-slate-800 transition ml-1"
            >
              <FaTimes className="w-2.5 h-2.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
