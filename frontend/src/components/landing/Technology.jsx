import React from 'react';

export default function Technology() {
  const techStack = [
    { name: 'React 18', desc: 'Frontend UI', color: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/5' },
    { name: 'Vite', desc: 'Build Tooling', color: 'border-purple-500/30 text-purple-400 bg-purple-500/5' },
    { name: 'Tailwind CSS', desc: 'Styling Framework', color: 'border-teal-500/30 text-teal-400 bg-teal-500/5' },
    { name: 'FastAPI', desc: 'Async Core REST API', color: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5' },
    { name: 'Python 3.11', desc: 'Backend Engine', color: 'border-blue-500/30 text-blue-400 bg-blue-500/5' },
    { name: 'LangGraph', desc: 'Parallel Orchestrator', color: 'border-indigo-500/30 text-indigo-400 bg-indigo-500/5' },
    { name: 'Ollama', desc: 'Local Inference', color: 'border-amber-500/30 text-amber-400 bg-amber-500/5' },
    { name: 'Qwen 2.5 Coder', desc: 'Coding LLM (14B)', color: 'border-rose-500/30 text-rose-400 bg-rose-500/5' },
    { name: 'PostgreSQL', desc: 'Relational DB', color: 'border-cyan-500/30 text-cyan-300 bg-cyan-500/5' },
    { name: 'MongoDB', desc: 'NoSQL Persistence', color: 'border-emerald-500/30 text-emerald-300 bg-emerald-500/5' },
    { name: 'Docker', desc: 'Containerization', color: 'border-blue-500/30 text-blue-300 bg-blue-500/5' },
    { name: 'Git', desc: 'Version Control', color: 'border-orange-500/30 text-orange-400 bg-orange-500/5' }
  ];

  return (
    <section id="technology" className="py-20 bg-[#090d16] font-sans border-t border-slate-800/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="max-w-3xl mx-auto mb-14">
          <h2 className="text-xs uppercase tracking-widest font-mono text-cyan-400 font-bold mb-2">
            Modern Tech Stack
          </h2>
          <p className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            Powered by Leading Technologies
          </p>
          <p className="text-slate-300 text-base sm:text-lg">
            AIForge integrates modern web frameworks, parallel state orchestrators, and open-weight local LLMs.
          </p>
        </div>

        {/* Badges Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 max-w-5xl mx-auto">
          {techStack.map((tech, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${tech.color} backdrop-blur-md flex flex-col items-center justify-center transition-all hover:scale-105 hover:shadow-lg`}
            >
              <span className="text-sm font-bold tracking-tight mb-1">{tech.name}</span>
              <span className="text-[11px] font-mono text-slate-400">{tech.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
