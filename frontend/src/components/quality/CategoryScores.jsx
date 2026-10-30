import React from 'react';
import { FaCode, FaSitemap, FaShieldAlt, FaTachometerAlt, FaVial, FaCogs, FaDatabase, FaBook } from 'react-icons/fa';

const META = {
  code_quality: { label: 'Code Quality', icon: <FaCode className="text-cyan-400" />, desc: 'Python syntax and the code-quality gate (ruff, imports, oxlint)' },
  api_compatibility: { label: 'API Compatibility', icon: <FaSitemap className="text-indigo-400" />, desc: 'Frontend and backend against the shared contract (Integration Engine)' },
  database: { label: 'Database', icon: <FaDatabase className="text-sky-400" />, desc: 'Schema and models against the contract (Integration Engine)' },
  security: { label: 'Security', icon: <FaShieldAlt className="text-emerald-400" />, desc: 'Static security scan (Bandit) from the Execution Guardian' },
  build_and_startup: { label: 'Build & Startup', icon: <FaCogs className="text-blue-400" />, desc: 'Dependency install, backend startup and frontend build' },
  testing: { label: 'Testing', icon: <FaVial className="text-purple-400" />, desc: "The project's own tests, run in isolation" },
  documentation: { label: 'Documentation', icon: <FaBook className="text-teal-400" />, desc: 'A README that explains setup and running' },
  performance: { label: 'Performance', icon: <FaTachometerAlt className="text-amber-400" />, desc: 'Not measured in this report' },
};

/** Each category is the share of its evaluated checks that passed; a category nothing evaluated says so. */
export default function CategoryScores({ categories = {} }) {
  const items = Object.entries(categories).map(([key, score]) => ({
    key, score, ...(META[key] || { label: key.replace(/_/g, ' '), icon: <FaCogs className="text-slate-400" />, desc: '' }),
  }));
  if (!items.length) return <p className="text-xs text-slate-500">No category could be evaluated.</p>;

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
              {it.score == null
                ? <span className="text-xs font-normal text-slate-500">Not evaluated</span>
                : <>{it.score} <span className="text-xs text-slate-500 font-normal">%</span></>}
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{it.desc}</p>
        </div>
      ))}
    </div>
  );
}
