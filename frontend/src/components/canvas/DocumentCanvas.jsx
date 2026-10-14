import React, { useState, useEffect, useRef } from "react";
import { FaBolt, FaMagic, FaCompressAlt, FaExpandAlt, FaSpellCheck, FaCopy, FaCheck } from "react-icons/fa";

export default function DocumentCanvas({ 
  content, 
  onChange, 
  onAiTransform, 
  isReadOnly = false 
}) {
  const [selectedText, setSelectedText] = useState("");
  const [floatingToolbarPos, setFloatingToolbarPos] = useState(null);
  const [copied, setCopied] = useState(false);
  const editorRef = useRef(null);

  const handleSelection = () => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    if (text.length > 3 && editorRef.current?.contains(selection.anchorNode)) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      setSelectedText(text);
      setFloatingToolbarPos({
        top: Math.max(10, rect.top - 45),
        left: Math.max(20, rect.left + rect.width / 2 - 120)
      });
    } else {
      setSelectedText("");
      setFloatingToolbarPos(null);
    }
  };

  const handleFloatingAction = (actionLabel) => {
    if (!selectedText) return;
    onAiTransform(`${actionLabel} the selected text: "${selectedText}"`, selectedText);
    setSelectedText("");
    setFloatingToolbarPos(null);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative h-full flex flex-col font-sans" onMouseUp={handleSelection}>
      {/* Floating Selection AI Toolbar */}
      {floatingToolbarPos && (
        <div 
          className="fixed z-50 flex items-center gap-1.5 p-1.5 bg-[#0F1117]/95 border border-[#6366F1]/60 rounded-xl shadow-2xl backdrop-blur-md animate-fade-in text-[11px]"
          style={{ top: `${floatingToolbarPos.top}px`, left: `${floatingToolbarPos.left}px` }}
        >
          <span className="px-1.5 font-bold text-indigo-400 flex items-center gap-1">
            <FaMagic size={9} /> AI:
          </span>
          <button
            onClick={() => handleFloatingAction("Improve & polish")}
            className="px-2 py-1 bg-[#151821] hover:bg-[#6366F1] hover:text-white rounded-lg transition font-medium text-gray-200 cursor-pointer"
          >
            ✨ Improve
          </button>
          <button
            onClick={() => handleFloatingAction("Summarize & shorten")}
            className="px-2 py-1 bg-[#151821] hover:bg-[#6366F1] hover:text-white rounded-lg transition font-medium text-gray-200 cursor-pointer"
          >
            Compress
          </button>
          <button
            onClick={() => handleFloatingAction("Expand with concrete examples")}
            className="px-2 py-1 bg-[#151821] hover:bg-[#6366F1] hover:text-white rounded-lg transition font-medium text-gray-200 cursor-pointer"
          >
            Expand
          </button>
        </div>
      )}

      {/* Main Document Textarea / Rich Editor */}
      <textarea
        ref={editorRef}
        value={content || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={isReadOnly}
        placeholder="# Document Title\n\nStart typing your document, PRD, or specifications..."
        className="w-full h-full bg-[#0B0F19] text-[#F5F7FA] p-6 text-sm font-sans leading-relaxed outline-none resize-none custom-scrollbar focus:ring-0 border-0"
      />
    </div>
  );
}
