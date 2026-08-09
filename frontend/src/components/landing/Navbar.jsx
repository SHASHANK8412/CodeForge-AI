import React, { useState } from 'react';
import { FaGithub, FaArrowRight, FaBars, FaTimes, FaLayerGroup } from 'react-icons/fa';

export default function Navbar({ onStartBuilding }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollTo = (id) => {
    setMobileMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav className="sticky top-0 z-50 bg-[#090d16]/80 backdrop-blur-md border-b border-slate-800/80 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-cyan-400/30">
            <FaLayerGroup className="w-5 h-5 text-white" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-extrabold tracking-tight text-white">AIForge</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-widest">v2.0</span>
          </div>
        </div>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <button onClick={() => scrollTo('features')} className="hover:text-cyan-400 transition-colors">Features</button>
          <button onClick={() => scrollTo('how-it-works')} className="hover:text-cyan-400 transition-colors">How It Works</button>
          <button onClick={() => scrollTo('architecture')} className="hover:text-cyan-400 transition-colors">Architecture</button>
          <button onClick={() => scrollTo('technology')} className="hover:text-cyan-400 transition-colors">Technology</button>
          <button onClick={() => scrollTo('why-aiforge')} className="hover:text-cyan-400 transition-colors">About</button>
        </div>

        {/* Right CTA Actions */}
        <div className="hidden md:flex items-center gap-4">
          <a
            href="https://github.com/SHASHANK8412/CodeForge-AI"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg transition"
          >
            <FaGithub className="w-4 h-4" />
            <span>GitHub</span>
          </a>

          <button
            onClick={onStartBuilding}
            className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 rounded-lg shadow-lg shadow-cyan-500/20 transition-all border border-cyan-400/30 active:scale-95"
          >
            <span>Start Building</span>
            <FaArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Mobile menu button */}
        <div className="md:hidden flex items-center">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-400 hover:text-white"
          >
            {mobileMenuOpen ? <FaTimes className="w-5 h-5" /> : <FaBars className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#0d1322] border-b border-slate-800 px-4 py-4 space-y-3 font-sans">
          <button onClick={() => scrollTo('features')} className="block w-full text-left py-2 text-sm text-slate-300 hover:text-cyan-400">Features</button>
          <button onClick={() => scrollTo('how-it-works')} className="block w-full text-left py-2 text-sm text-slate-300 hover:text-cyan-400">How It Works</button>
          <button onClick={() => scrollTo('architecture')} className="block w-full text-left py-2 text-sm text-slate-300 hover:text-cyan-400">Architecture</button>
          <button onClick={() => scrollTo('technology')} className="block w-full text-left py-2 text-sm text-slate-300 hover:text-cyan-400">Technology</button>
          <button onClick={() => scrollTo('why-aiforge')} className="block w-full text-left py-2 text-sm text-slate-300 hover:text-cyan-400">About</button>
          <div className="pt-3 border-t border-slate-800 flex flex-col gap-2">
            <a
              href="https://github.com/SHASHANK8412/CodeForge-AI"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-center gap-2 py-2 text-xs font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg"
            >
              <FaGithub className="w-4 h-4" /> GitHub
            </a>
            <button
              onClick={onStartBuilding}
              className="w-full py-2.5 text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 rounded-lg flex items-center justify-center gap-2"
            >
              <span>Start Building</span>
              <FaArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
