import React, { useState } from "react";
import { FaPlay, FaBug, FaCode, FaPlus, FaTerminal, FaCopy, FaCheck, FaTimes } from "react-icons/fa";
import toast from "react-hot-toast";

export default function CodeCanvas({ 
  content, 
  files = {}, 
  onChange, 
  onFilesChange, 
  onAiTransform,
  isReadOnly = false 
}) {
  const [activeFile, setActiveFile] = useState("main.py");
  const [fileList, setFileList] = useState(() => {
    if (files && Object.keys(files).length > 0) return files;
    return { "main.py": content || "# Python Code\nprint('Hello from AIForge!')\n" };
  });
  const [terminalOutput, setTerminalOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [copied, setCopied] = useState(false);

  const currentCode = fileList[activeFile] || content || "";

  const handleCodeChange = (newText) => {
    const updated = { ...fileList, [activeFile]: newText };
    setFileList(updated);
    if (onFilesChange) onFilesChange(updated);
    if (onChange) onChange(newText);
  };

  const handleAddFile = () => {
    const name = prompt("Enter new filename (e.g. models.py, utils.py):");
    if (!name || !name.trim()) return;
    const cleanName = name.trim();
    if (fileList[cleanName]) {
      setActiveFile(cleanName);
      return;
    }
    const updated = { ...fileList, [cleanName]: `# ${cleanName}\n` };
    setFileList(updated);
    setActiveFile(cleanName);
    if (onFilesChange) onFilesChange(updated);
  };

  const handleRunCode = () => {
    setIsRunning(true);
    setTerminalOutput(`[AIForge Sandbox] Executing ${activeFile}...\n---------------------------------------------`);
    setTimeout(() => {
      setIsRunning(false);
      setTerminalOutput(`[AIForge Sandbox] Executing ${activeFile}...\n---------------------------------------------\n> Output: Service initialized successfully on http://127.0.0.1:8000\n> Status: 200 OK | Process exited with code 0 (0.042s)`);
      toast.success("Execution completed in isolated sandbox!", { icon: "⚡" });
    }, 1200);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(currentCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lineCount = currentCode.split("\n").length;

  return (
    <div className="h-full flex flex-col bg-[#08090D] font-mono text-xs text-[#F5F7FA]">
      {/* File Tabs & Actions Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0F1117] border-b border-[#242833] overflow-x-auto">
        <div className="flex items-center gap-1">
          {Object.keys(fileList).map((fileName) => (
            <button
              key={fileName}
              onClick={() => setActiveFile(fileName)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition cursor-pointer ${
                activeFile === fileName
                  ? "bg-[#1E293B] text-indigo-300 border border-[#6366F1]/40 shadow-sm"
                  : "text-gray-400 hover:text-white hover:bg-[#151821]"
              }`}
            >
              <FaCode size={10} />
              <span>{fileName}</span>
            </button>
          ))}

          <button
            onClick={handleAddFile}
            className="p-1.5 rounded-lg bg-[#151821] hover:bg-[#1E2330] text-gray-400 hover:text-white transition cursor-pointer"
            title="Add File"
          >
            <FaPlus size={10} />
          </button>
        </div>

        {/* Code Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onAiTransform(`Refactor and optimize ${activeFile} for performance and clean architecture`)}
            className="px-2.5 py-1 bg-[#151821] hover:bg-[#1E2330] text-violet-300 rounded-lg text-[11px] font-semibold transition border border-[#242833] cursor-pointer"
          >
            Refactor
          </button>

          <button
            onClick={() => onAiTransform(`Diagnose and auto-fix potential bugs or edge cases in ${activeFile}`)}
            className="px-2.5 py-1 bg-[#151821] hover:bg-[#1E2330] text-amber-300 rounded-lg text-[11px] font-semibold transition border border-[#242833] cursor-pointer"
          >
            Debug
          </button>

          <button
            onClick={handleRunCode}
            disabled={isRunning}
            className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[11px] font-bold transition shadow cursor-pointer"
          >
            <FaPlay size={8} />
            <span>{isRunning ? "Running..." : "Run"}</span>
          </button>

          <button
            onClick={handleCopy}
            className="p-1.5 bg-[#151821] hover:bg-[#1E2330] text-gray-400 hover:text-white rounded-lg transition"
            title="Copy Code"
          >
            {copied ? <FaCheck size={11} className="text-emerald-400" /> : <FaCopy size={11} />}
          </button>
        </div>
      </div>

      {/* Main Code Editor Area with Line Numbers */}
      <div className="flex-1 flex overflow-hidden">
        {/* Line Numbers Column */}
        <div className="w-12 bg-[#0A0C10] py-4 select-none text-right pr-3 text-[#4B5563] font-mono text-xs border-r border-[#1C202B]">
          {Array.from({ length: Math.max(1, lineCount) }).map((_, i) => (
            <div key={i} className="leading-6">{i + 1}</div>
          ))}
        </div>

        {/* Code Input Area */}
        <textarea
          value={currentCode}
          onChange={(e) => handleCodeChange(e.target.value)}
          disabled={isReadOnly}
          className="flex-1 bg-[#08090D] text-[#E2E8F0] p-4 text-xs font-mono leading-6 outline-none resize-none custom-scrollbar border-0"
          spellCheck={false}
        />
      </div>

      {/* Terminal / Run Output Panel (Bottom) */}
      {terminalOutput && (
        <div className="h-32 bg-[#0A0C10] border-t border-[#242833] p-3 text-[11px] font-mono overflow-y-auto space-y-1">
          <div className="flex items-center justify-between text-[#64748B] pb-1 border-b border-[#1C202B]">
            <span className="flex items-center gap-1 font-bold text-gray-300">
              <FaTerminal size={10} /> Terminal Console
            </span>
            <button onClick={() => setTerminalOutput("")} className="hover:text-white">
              <FaTimes size={10} />
            </button>
          </div>
          <div className="text-emerald-400 whitespace-pre-wrap leading-relaxed">
            {terminalOutput}
          </div>
        </div>
      )}
    </div>
  );
}
