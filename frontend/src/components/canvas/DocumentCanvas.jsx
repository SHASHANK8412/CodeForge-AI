import React, { useState, useEffect, useRef } from "react";
import { FaBolt, FaMagic, FaCompressAlt, FaExpandAlt, FaSpellCheck, FaCopy, FaCheck } from "react-icons/fa";

export default function DocumentCanvas({ 
  content, 
  onChange, 
  isReadOnly = false 
}) {
  const [copied, setCopied] = useState(false);
  const editorRef = useRef(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative h-full flex flex-col font-sans">
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
