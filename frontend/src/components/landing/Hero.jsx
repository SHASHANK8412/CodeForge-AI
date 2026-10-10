import React, { useState } from 'react';
import { FaArrowRight, FaTerminal, FaPlay, FaRobot, FaCheckCircle, FaShieldAlt, FaProjectDiagram, FaLink, FaBolt, FaSearch } from 'react-icons/fa';
import { HiSparkles } from 'react-icons/hi2';

const SUGGESTIONS = [
  { label: "Analyze", text: "Analyze my project, find security risks, research alternatives and prepare a verified report." },
  { label: "Research", text: "Research emerging agent architectures, compare with our roadmap, and prepare an executive summary." },
  { label: "Secure", text: "Investigate today's security telemetry, identify attack vectors, and recommend containment rules." },
  { label: "Automate", text: "Create an autonomous workflow that monitors our dataset, runs AST regression tests, and anchors audit proofs." }
];

export default function Hero({ onStartBuilding, onScrollToArchitecture, onLaunchMission }) {
  const [missionInput, setMissionInput] = useState(
    "Analyze my project, find security risks, research alternatives and prepare a verified report."
  );

  const handleLaunch = () => {
    if (onLaunchMission) {
      onLaunchMission(missionInput);
    } else if (onStartBuilding) {
      onStartBuilding();
    }
  };

  return (
    <section className="relative pt-12 pb-20 overflow-hidden font-sans bg-[#090d16]">
      {/* Background Glows & Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-cyan-500/10 via-indigo-500/15 to-purple-500/10 blur-[130px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-cyan-400 border border-cyan-500/20 mb-6 shadow-sm">
            <HiSparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>AI Mission Control Platform • Autonomous Multi-Agent OS</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight mb-4 leading-[1.1]">
            Give AIForge a Mission.
          </h1>

          {/* Supporting Tagline */}
          <p className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent mb-6">
            AIForge turns goals into intelligent, secure, verifiable work.
          </p>

          <p className="text-base sm:text-lg text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">
            Don't just chat. Tell AIForge what you want accomplished. AIForge plans it, assembles the right intelligence, executes safely, verifies findings, and delivers a complete result.
          </p>

          {/* Primary Mission Input Box */}
          <div className="max-w-3xl mx-auto bg-slate-900/90 border border-cyan-500/30 rounded-3xl p-4 sm:p-5 shadow-2xl shadow-cyan-500/10 backdrop-blur-xl mb-6 text-left">
            <div className="flex items-center justify-between text-xs font-mono text-cyan-400 pb-2">
              <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[11px]">
                <FaBolt size={11} /> What should AIForge accomplish?
              </span>
              <span className="text-slate-400 text-[10px]">Natural Language Goal</span>
            </div>

            <textarea
              rows={2}
              value={missionInput}
              onChange={(e) => setMissionInput(e.target.value)}
              placeholder="Describe what you want done (e.g. Analyze project security, research dependencies, prepare verified report)..."
              className="w-full bg-[#070a12] border border-slate-800 focus:border-cyan-500 rounded-2xl p-3 text-xs sm:text-sm text-white outline-none resize-none transition-all"
            />

            <div className="flex flex-wrap items-center justify-between gap-3 pt-3">
              {/* Suggestion Chips */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] font-mono text-slate-500">Try:</span>
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setMissionInput(s.text)}
                    className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[10px] font-mono text-slate-300 hover:text-cyan-300 transition cursor-pointer"
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              {/* Launch CTA */}
              <button
                onClick={handleLaunch}
                className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white rounded-xl font-bold text-xs sm:text-sm transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <span>Launch Mission</span>
                <FaArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Secondary Action */}
          <div className="flex items-center justify-center gap-4 mb-14 text-xs font-mono text-slate-400">
            <button
              onClick={onScrollToArchitecture}
              className="hover:text-cyan-400 transition flex items-center gap-1.5 cursor-pointer"
            >
              <FaTerminal className="text-cyan-400" />
              <span>Explore AIForge Architecture & Subsystems</span>
            </button>
          </div>
        </div>

        {/* Live Interactive Mission Control Pipeline Visualizer */}
        <div className="max-w-5xl mx-auto bg-slate-950/80 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-md space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3 font-mono text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-white font-bold">Mission: Project Security Analysis & Provenance Audit</span>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-purple-950/60 border border-purple-500/30 text-purple-300 text-[10px]">
              Verifiable Ledger Anchor: Block #19482115
            </span>
          </div>

          {/* 5-Step Mission Flow */}
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs">
            <div className="p-3.5 rounded-2xl bg-[#0d121f] border border-cyan-500/30 space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-cyan-400 font-bold">1. Plan</span>
                <span className="text-emerald-400 font-bold">✓ DONE</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed font-sans">Goal parsed into 4-stage DAG with specialist agent assignments.</p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#0d121f] border border-cyan-500/30 space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-cyan-400 font-bold">2. Graph RAG</span>
                <span className="text-emerald-400 font-bold">✓ DONE</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed font-sans">Traversed 42 knowledge entities & mapped microservice dependencies.</p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#0d121f] border border-indigo-500/30 space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-indigo-400 font-bold">3. Multi-Agent</span>
                <span className="text-emerald-400 font-bold">✓ DONE</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed font-sans">Coding, Security & Research agents collaborated in parallel.</p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#0d121f] border border-rose-500/30 space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-rose-400 font-bold">4. Zero-Trust</span>
                <span className="text-emerald-400 font-bold">✓ VERIFIED</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed font-sans">Human operator confirmed defensive WAF rule containment.</p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#0d121f] border border-purple-500/30 space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-purple-400 font-bold">5. Result</span>
                <span className="text-emerald-400 font-bold">✓ ANCHORED</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed font-sans">SHA-256 certificate signed & anchored to immutable ledger.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
