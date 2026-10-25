import React, { useState, useMemo, useEffect } from 'react';
import { FaFolder, FaFolderOpen, FaFileCode, FaFileAlt, FaDatabase, FaDocker, FaChevronRight, FaChevronDown, FaSearch } from 'react-icons/fa';

function TreeItem({ node, activePath, onFileSelect, forceOpen }) {
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    if (node.isDir && forceOpen) {
      setIsOpen(true);
    }
  }, [node.isDir, forceOpen]);

  if (node.isDir) {
    return (
      <div>
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1.5 px-2 py-1 hover:bg-slate-900 rounded cursor-pointer text-xs font-semibold text-slate-300 select-none"
        >
          {isOpen ? <FaChevronDown className="w-2.5 h-2.5 text-slate-500" /> : <FaChevronRight className="w-2.5 h-2.5 text-slate-500" />}
          {isOpen ? <FaFolderOpen className="w-3.5 h-3.5 text-amber-400" /> : <FaFolder className="w-3.5 h-3.5 text-amber-400" />}
          <span>{node.name}</span>
          <span className="ml-auto text-[10px] text-slate-500">{node.children?.length ?? 0}</span>
        </div>

        {isOpen && node.children && (
          <div className="pl-4 space-y-0.5 border-l border-slate-800/60 ml-2">
            {node.children.map((child, idx) => (
              <TreeItem
                key={idx}
                node={child}
                activePath={activePath}
                onFileSelect={onFileSelect}
                forceOpen={forceOpen}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const isSelected = activePath === node.path;
  let icon = <FaFileCode className="w-3.5 h-3.5 text-cyan-400" />;
  if (node.name.endsWith('.sql')) icon = <FaDatabase className="w-3.5 h-3.5 text-purple-400" />;
  else if (node.name.endsWith('.md')) icon = <FaFileAlt className="w-3.5 h-3.5 text-slate-400" />;
  else if (node.name.toLowerCase().includes('docker')) icon = <FaDocker className="w-3.5 h-3.5 text-blue-400" />;

  return (
    <div
      onClick={() => onFileSelect(node)}
      className={`flex items-center gap-2 px-2.5 py-1 rounded cursor-pointer text-xs font-mono transition select-none ${
        isSelected ? 'bg-indigo-600/30 text-white font-bold border-l-2 border-cyan-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
      }`}
    >
      {icon}
      <span className="truncate">{node.name}</span>
    </div>
  );
}

export default function FileExplorer({ files = [], activeFile, onFileSelect }) {
  const [filterText, setFilterText] = useState('');

  const filteredFiles = useMemo(() => {
    if (!filterText.trim()) return files;
    const normalized = filterText.toLowerCase();
    return files.filter((file) => {
      const path = file.path || '';
      const name = file.name || '';
      return path.toLowerCase().includes(normalized) || name.toLowerCase().includes(normalized);
    });
  }, [files, filterText]);

  const buildTreeFromFlat = (flatFiles) => {
    const root = [];
    const map = {};

    flatFiles.forEach((file) => {
      const parts = file.path.split('/');
      let currentLevel = root;

      parts.forEach((part, idx) => {
        const isFile = idx === parts.length - 1;
        const currentPath = parts.slice(0, idx + 1).join('/');

        if (!map[currentPath]) {
          const item = isFile
            ? { ...file, isDir: false }
            : { name: part, path: currentPath, isDir: true, children: [] };
          map[currentPath] = item;
          currentLevel.push(item);
        }

        if (!isFile) {
          currentLevel = map[currentPath].children;
        }
      });
    });

    return root;
  };

  const treeData = useMemo(() => buildTreeFromFlat(filteredFiles), [filteredFiles]);
  const forceOpen = Boolean(filterText.trim());

  return (
    <div className="bg-[#090d16] border-r border-slate-800/80 w-56 sm:w-60 flex flex-col font-sans shrink-0 min-h-0 select-none">
      <div className="p-2.5 border-b border-slate-800/80 text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between shrink-0">
        <span>File Explorer</span>
        <span className="text-slate-500 font-normal text-[10px]">{filteredFiles.length} files</span>
      </div>

      <div className="p-2 border-b border-slate-800/60 shrink-0">
        <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs">
          <FaSearch className="w-2.5 h-2.5 text-slate-500 shrink-0" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter files..."
            className="bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none w-full text-[11px] font-mono"
          />
        </div>
      </div>

      <div className="p-2 overflow-y-auto flex-1 min-h-0 space-y-0.5 custom-scrollbar">
        {treeData.map((node, idx) => (
          <TreeItem
            key={idx}
            node={node}
            activePath={activeFile?.path}
            onFileSelect={onFileSelect}
            forceOpen={forceOpen}
          />
        ))}
      </div>
    </div>
  );
}
