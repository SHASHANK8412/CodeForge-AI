import React, { useState } from "react";
import { FaBrain, FaSearch, FaBolt, FaArrowRight } from "react-icons/fa";
import AIToolsSection from "../components/dashboard/AIToolsSection";

export default function AIToolsPage({ setView }) {
  return (
    <div className="min-h-full p-6 md:p-8 space-y-6 text-[#F5F7FA] font-sans">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
              <FaBrain size={14} />
            </span>
            <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
              AI Tools & Engines Catalog
            </h1>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1">
            Access specialized agentic tools categorized for Coding, Writing, Study, Research, and Productivity
          </p>
        </div>

        <button
          onClick={() => setView("chat")}
          className="flex items-center gap-2 px-4 py-2 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-white rounded-xl text-xs font-bold transition cursor-pointer self-start md:self-auto"
        >
          <FaBolt className="text-[#8D5CF6]" />
          <span>Launch AI Chat</span>
        </button>
      </div>

      {/* Main Categorized Tools Directory */}
      <AIToolsSection setView={setView} />
    </div>
  );
}
