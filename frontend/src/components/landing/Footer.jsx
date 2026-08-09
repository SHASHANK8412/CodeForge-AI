import React from 'react';
import { FaGithub, FaLayerGroup } from 'react-icons/fa';

export default function Footer() {
  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <footer className="bg-[#060911] border-t border-slate-800/80 py-12 font-sans text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
        {/* Left Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <FaLayerGroup className="w-4 h-4" />
          </div>
          <div>
            <span className="text-sm font-extrabold text-white">AIForge</span>
            <p className="text-[11px] text-slate-500">Autonomous AI Software Engineer</p>
          </div>
        </div>

        {/* Links */}
        <div className="flex flex-wrap items-center gap-6 font-medium text-slate-300">
          <a
            href="https://github.com/SHASHANK8412/CodeForge-AI"
            target="_blank"
            rel="noreferrer"
            className="hover:text-cyan-400 transition flex items-center gap-1.5"
          >
            <FaGithub className="w-3.5 h-3.5" /> GitHub
          </a>
          <button onClick={() => scrollTo('features')} className="hover:text-cyan-400 transition">Documentation</button>
          <button onClick={() => scrollTo('architecture')} className="hover:text-cyan-400 transition">Architecture</button>
          <a href="mailto:support@aiforge.dev" className="hover:text-cyan-400 transition">Contact</a>
        </div>

        {/* Copyright */}
        <div className="text-slate-500">
          © 2026 AIForge. Built with AI.
        </div>
      </div>
    </footer>
  );
}
