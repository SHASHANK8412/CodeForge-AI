import React from 'react';
import { FaCommentAlt, FaProjectDiagram, FaCode, FaCheckDouble, FaDownload } from 'react-icons/fa';

export default function HowItWorks() {
  const steps = [
    {
      num: '01',
      title: 'Describe',
      subtitle: 'Tell AIForge what you want to build.',
      icon: FaCommentAlt,
      color: 'from-cyan-500 to-blue-500'
    },
    {
      num: '02',
      title: 'Plan',
      subtitle: 'AIForge analyzes requirements and creates a development plan.',
      icon: FaProjectDiagram,
      color: 'from-blue-500 to-indigo-500'
    },
    {
      num: '03',
      title: 'Build',
      subtitle: 'Specialized agents generate the frontend, backend, and database.',
      icon: FaCode,
      color: 'from-indigo-500 to-purple-500'
    },
    {
      num: '04',
      title: 'Validate',
      subtitle: 'Reviewer and Testing agents inspect and validate the generated project.',
      icon: FaCheckDouble,
      color: 'from-purple-500 to-pink-500'
    },
    {
      num: '05',
      title: 'Export',
      subtitle: 'Download your complete project and continue development.',
      icon: FaDownload,
      color: 'from-emerald-500 to-teal-500'
    }
  ];

  return (
    <section id="how-it-works" className="py-20 bg-[#090d16] font-sans border-t border-slate-800/60 relative overflow-hidden">
      {/* Subtle Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-cyan-500/5 blur-[140px] pointer-events-none rounded-full" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs uppercase tracking-widest font-mono text-cyan-400 font-bold mb-2">
            Seamless Autonomous Journey
          </h2>
          <p className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            How AIForge Works
          </p>
          <p className="text-slate-300 text-base sm:text-lg">
            From natural language prompt to production-ready software in five automated steps.
          </p>
        </div>

        {/* 5-Step Horizontal Workflow */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 relative">
          {/* Animated Connecting Line (Desktop) */}
          <div className="hidden md:block absolute top-12 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-cyan-500 via-purple-500 to-emerald-500 -z-0 opacity-40" />

          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="bg-slate-950/90 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 text-center relative z-10 flex flex-col items-center shadow-xl backdrop-blur-md group hover:-translate-y-1 transition-all"
              >
                {/* Step Number Badge */}
                <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-mono font-extrabold text-cyan-400 mb-3 flex items-center justify-center">
                  {step.num}
                </div>

                {/* Step Icon */}
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${step.color} flex items-center justify-center text-white mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
                  <Icon className="w-5 h-5" />
                </div>

                <h3 className="text-base font-bold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                  {step.title}
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  "{step.subtitle}"
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
