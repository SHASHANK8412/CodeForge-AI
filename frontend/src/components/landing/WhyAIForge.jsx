import React from 'react';
import { FaUserShield, FaCheckDouble, FaInfinity, FaPuzzlePiece } from 'react-icons/fa';

export default function WhyAIForge() {
  const points = [
    {
      title: 'Autonomous',
      icon: FaPuzzlePiece,
      color: 'from-cyan-500 to-blue-600',
      description: 'Multiple specialized agents collaborate instead of relying on one generic AI response.'
    },
    {
      title: 'Local AI',
      icon: FaUserShield,
      color: 'from-indigo-500 to-purple-600',
      description: 'Use local LLMs through Ollama for greater control, privacy, and zero API costs.'
    },
    {
      title: 'Quality First',
      icon: FaCheckDouble,
      color: 'from-purple-500 to-pink-600',
      description: 'Generated projects pass review, static analysis, and automated testing before export.'
    },
    {
      title: 'End-to-End',
      icon: FaInfinity,
      color: 'from-emerald-500 to-teal-600',
      description: 'AIForge handles planning, architecture, implementation, testing, and documentation.'
    }
  ];

  return (
    <section id="why-aiforge" className="py-20 bg-[#090d16] font-sans border-t border-slate-800/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs uppercase tracking-widest font-mono text-cyan-400 font-bold mb-2">
            The Autonomous Advantage
          </h2>
          <p className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            Why AIForge?
          </p>
          <p className="text-slate-300 text-base sm:text-lg">
            Built from the ground up for serious software development rather than simple code completion.
          </p>
        </div>

        {/* 4 Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {points.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="bg-slate-950/90 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 shadow-xl group backdrop-blur-md"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${item.color} flex items-center justify-center text-white mb-5 shadow-lg group-hover:scale-110 transition-transform`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
