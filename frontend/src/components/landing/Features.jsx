import React from 'react';
import { FaClipboardList, FaSitemap, FaDesktop, FaServer, FaDatabase, FaSearch, FaVial, FaBook, FaRobot } from 'react-icons/fa';

export default function Features() {
  const agents = [
    {
      title: 'Planner Agent',
      icon: FaClipboardList,
      color: 'from-cyan-500 to-blue-600',
      description: 'Converts natural-language requirements into structured development tasks.'
    },
    {
      title: 'Architect Agent',
      icon: FaSitemap,
      color: 'from-blue-500 to-indigo-600',
      description: 'Designs the system architecture, components, APIs, and data flow.'
    },
    {
      title: 'Frontend Agent',
      icon: FaDesktop,
      color: 'from-indigo-500 to-purple-600',
      description: 'Generates modern React interfaces and components.'
    },
    {
      title: 'Backend Agent',
      icon: FaServer,
      color: 'from-purple-500 to-pink-600',
      description: 'Creates APIs, business logic, authentication, and server-side functionality.'
    },
    {
      title: 'Database Agent',
      icon: FaDatabase,
      color: 'from-cyan-500 to-emerald-600',
      description: 'Designs schemas, relationships, queries, and database configuration.'
    },
    {
      title: 'Reviewer Agent',
      icon: FaSearch,
      color: 'from-emerald-500 to-teal-600',
      description: 'Analyzes generated code for quality, architecture, security, and maintainability.'
    },
    {
      title: 'Testing Agent',
      icon: FaVial,
      color: 'from-amber-500 to-orange-600',
      description: 'Creates and executes tests and identifies failures.'
    },
    {
      title: 'Documentation Agent',
      icon: FaBook,
      color: 'from-rose-500 to-red-600',
      description: 'Generates README files, API documentation, setup instructions, and technical documentation.'
    }
  ];

  return (
    <section id="features" className="py-20 bg-[#090d16] font-sans border-t border-slate-800/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-cyan-400 border border-indigo-500/20 mb-3">
            <FaRobot className="w-3 h-3 text-cyan-400" />
            <span>Specialized Agent Engineering Team</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            One AI. A Team of Engineers.
          </h2>
          <p className="text-slate-300 text-base sm:text-lg">
            Rather than relying on one generic LLM response, AIForge orchestrates eight specialized agents that collaborate seamlessly.
          </p>
        </div>

        {/* 8 Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {agents.map((agent, idx) => {
            const Icon = agent.icon;
            return (
              <div
                key={idx}
                className="bg-slate-950/80 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 shadow-lg hover:shadow-cyan-500/10 group backdrop-blur-md"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${agent.color} flex items-center justify-center text-white mb-5 shadow-md border border-white/10 group-hover:scale-110 transition-transform`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                  {agent.title}
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {agent.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
