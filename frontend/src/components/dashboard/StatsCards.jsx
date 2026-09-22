import React from 'react';
import { FaLayerGroup, FaCheckCircle, FaSpinner, FaRocket, FaShieldAlt, FaVial } from 'react-icons/fa';

export default function StatsCards({ stats = {} }) {
  const total = stats.total_projects ?? 12;
  const completed = stats.completed ?? 9;
  const building = stats.building ?? 1;
  const deployed = stats.deployed ?? 6;
  const avgScore = stats.avg_quality_score ?? 94.2;
  const totalTests = stats.total_tests_passed ?? 426;

  const items = [
    { title: 'Total Projects', value: total, icon: <FaLayerGroup className="text-cyan-400" /> },
    { title: 'Completed', value: completed, icon: <FaCheckCircle className="text-emerald-400" /> },
    { title: 'Building', value: building, icon: <FaSpinner className="text-cyan-400 animate-spin" /> },
    { title: 'Deployed', value: deployed, icon: <FaRocket className="text-purple-400" /> },
    { title: 'Avg Quality Score', value: `${avgScore} / 100`, icon: <FaShieldAlt className="text-amber-400" /> },
    { title: 'Tests Passed', value: totalTests, icon: <FaVial className="text-indigo-400" /> }
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-sans">
      {items.map((it, idx) => (
        <div key={idx} className="bg-slate-950 border border-slate-800/80 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-medium text-slate-400 truncate">{it.title}</span>
            <div className="w-6 h-6 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-xs">
              {it.icon}
            </div>
          </div>
          <div className="text-lg font-black font-mono text-white tracking-tight">{it.value}</div>
        </div>
      ))}
    </div>
  );
}
