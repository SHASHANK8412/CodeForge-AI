import React from 'react';
import { FaCode, FaSitemap, FaShieldAlt, FaTachometerAlt, FaVial, FaCogs } from 'react-icons/fa';

export default function CategoryScores({ categories = {} }) {
  const items = [
    { key: 'code_quality', label: 'Code Quality', score: categories.code_quality ?? 98, icon: <FaCode className="text-cyan-400" />, desc: 'AST static compliance & syntax cleanliness' },
    { key: 'architecture', label: 'Architecture', score: categories.architecture ?? 95, icon: <FaSitemap className="text-indigo-400" />, desc: 'Layered component decoupling & OpenAPI routes' },
    { key: 'security', label: 'Security', score: categories.security ?? 97, icon: <FaShieldAlt className="text-emerald-400" />, desc: 'JWT authentication, SAST & secret protection' },
    { key: 'performance', label: 'Performance', score: categories.performance ?? 92, icon: <FaTachometerAlt className="text-amber-400" />, desc: 'Sub-50ms endpoint latency & bundle efficiency' },
    { key: 'testing', label: 'Testing', score: categories.testing ?? 100, icon: <FaVial className="text-purple-400" />, desc: 'Automated pytest assertions & line coverage' },
    { key: 'maintainability', label: 'Maintainability', score: categories.maintainability ?? 96, icon: <FaCogs className="text-blue-400" />, desc: 'Modular design, clear documentation & typed models' }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 font-sans">
      {items.map((it) => (
        <div key={it.key} className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl hover:border-slate-700 transition">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">
                {it.icon}
              </div>
              <h4 className="text-sm font-extrabold text-white">{it.label}</h4>
            </div>
            <span className="font-mono font-extrabold text-white text-base bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg">
              {it.score} <span className="text-xs text-slate-500 font-normal">/ 100</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{it.desc}</p>
        </div>
      ))}
    </div>
  );
}
