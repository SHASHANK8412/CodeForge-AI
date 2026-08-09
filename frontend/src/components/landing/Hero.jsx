import React from 'react';
import { FaArrowRight, FaTerminal, FaPlay, FaRobot, FaCheckCircle, FaSpinner, FaFileCode } from 'react-icons/fa';
import { HiSparkles } from 'react-icons/hi2';


export default function Hero({ onStartBuilding, onScrollToArchitecture }) {
  return (
    <section className="relative pt-12 pb-20 overflow-hidden font-sans bg-[#090d16]">
      {/* Background Glows & Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-500/10 via-indigo-500/15 to-purple-500/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-cyan-400 border border-cyan-500/20 mb-6 shadow-sm">
            <HiSparkles className="w-3 h-3 text-cyan-400 animate-pulse" />
            <span>Autonomous Multi-Agent AI Software Engineering Platform</span>
          </div>


          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight mb-4 leading-[1.1]">
            Your AI Software Engineer.
          </h1>

          {/* Tagline */}
          <p className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent mb-6">
            "Describe it. AIForge builds it."
          </p>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-slate-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            Describe the application you want to build. AIForge plans, designs, codes, reviews, tests, documents, and exports the complete software project using a team of specialized AI agents.
          </p>

          {/* Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <button
              onClick={onStartBuilding}
              className="w-full sm:w-auto px-8 py-3.5 text-sm font-bold text-white bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 rounded-xl shadow-xl shadow-cyan-500/20 border border-cyan-400/30 flex items-center justify-center gap-2 transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            >
              <span>Start Building</span>
              <FaArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onScrollToArchitecture}
              className="w-full sm:w-auto px-7 py-3.5 text-sm font-semibold text-slate-300 hover:text-white bg-slate-900/80 hover:bg-slate-800 border border-slate-800 rounded-xl transition flex items-center justify-center gap-2"
            >
              <FaTerminal className="w-4 h-4 text-indigo-400" />
              <span>View Architecture</span>
            </button>
          </div>
        </div>

        {/* Animated Visual Representation of Agent Workflow */}
        <div className="max-w-5xl mx-auto bg-slate-950/80 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          <div className="text-xs uppercase tracking-widest font-mono text-slate-400 mb-4 text-center font-semibold">
            Autonomous Multi-Agent Workflow Execution
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-7 gap-2 items-center text-center text-xs font-medium">
            {/* Step 1: User Idea */}
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center gap-1.5 shadow-sm">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 font-bold">
                💡
              </div>
              <span className="text-white font-bold">User Idea</span>
              <span className="text-[10px] text-slate-400">Natural Prompt</span>
            </div>

            <div className="hidden sm:block text-slate-600 text-lg">→</div>

            {/* Step 2: Planner */}
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center gap-1.5 shadow-sm">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                <FaRobot className="w-4 h-4" />
              </div>
              <span className="text-white font-bold">Planner</span>
              <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                <FaCheckCircle className="w-2.5 h-2.5" /> Spec
              </span>
            </div>

            <div className="hidden sm:block text-slate-600 text-lg">→</div>

            {/* Step 3: Architect */}
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center gap-1.5 shadow-sm">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20">
                <FaFileCode className="w-4 h-4" />
              </div>
              <span className="text-white font-bold">Architect</span>
              <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                <FaCheckCircle className="w-2.5 h-2.5" /> Blueprint
              </span>
            </div>

            <div className="hidden sm:block text-slate-600 text-lg">→</div>

            {/* Step 4: Coders (Parallel) */}
            <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl flex flex-col items-center gap-1.5 shadow-md shadow-indigo-500/10">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-400/40">
                <FaSpinner className="w-4 h-4 animate-spin text-cyan-400" />
              </div>
              <span className="text-white font-bold">Frontend + Backend + DB</span>
              <span className="text-[10px] text-cyan-300 font-mono">Code Gen</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-7 gap-2 items-center text-center text-xs font-medium mt-3">
            <div className="hidden sm:block sm:col-span-3"></div>
            <div className="hidden sm:block text-slate-600 text-lg">↓</div>
            <div className="hidden sm:block sm:col-span-3"></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 items-center text-center text-xs font-medium">
            <div className="hidden sm:block sm:col-span-1"></div>

            {/* Step 5: Reviewer */}
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center gap-1.5">
              <span className="text-white font-bold">Reviewer Agent</span>
              <span className="text-[10px] text-slate-400">Quality Audit</span>
            </div>

            <div className="hidden sm:block text-slate-600 text-lg">→</div>

            {/* Step 6: Testing */}
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center gap-1.5">
              <span className="text-white font-bold">Testing Agent</span>
              <span className="text-[10px] text-slate-400">Empirical Tests</span>
            </div>

            <div className="hidden sm:block text-slate-600 text-lg">→</div>

            {/* Step 7: Complete Project */}
            <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl flex flex-col items-center gap-1.5">
              <span className="text-emerald-400 font-bold">Complete Project</span>
              <span className="text-[10px] text-emerald-300 font-mono">ZIP Export</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
