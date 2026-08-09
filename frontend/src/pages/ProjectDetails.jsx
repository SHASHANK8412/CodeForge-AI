import React, { useState, useEffect } from 'react';
import ProjectActivity from '../components/dashboard/ProjectActivity';
import ProjectVersions from '../components/dashboard/ProjectVersions';
import ProjectMemoryDashboard from '../components/memory/ProjectMemoryDashboard';
import { fetchProjectDetails } from '../services/projects';
import { FaArrowLeft, FaCheckCircle, FaCode, FaShieldAlt, FaRocket, FaSpinner } from 'react-icons/fa';

export default function ProjectDetails({ generationId = 'aiforge-fooddelivery-ai', setView }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDetails = async () => {
      setLoading(true);
      const res = await fetchProjectDetails(generationId);
      setData(res);
      setLoading(false);
    };

    loadDetails();
  }, [generationId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-white font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-cyan-400 animate-spin" />
        <h3 className="text-base font-bold">Loading Project Details</h3>
      </div>
    );
  }

  const handleNavigate = (targetView) => {
    if (setView) {
      setView(targetView);
    } else {
      window.location.href = `/projects/${generationId}/${targetView}`;
    }
  };

  const name = data?.project_name || 'FoodDelivery AI';
  const score = data?.quality_score || 96.0;
  const testsPassed = data?.tests?.passed || 48;
  const testsTotal = data?.tests?.total || 48;
  const stack = data?.stack || ['React', 'FastAPI', 'PostgreSQL', 'Tailwind CSS'];
  const activity = data?.activity || [];
  const versions = data?.versions || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setView ? setView('dashboard') : (window.location.href = '/dashboard')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-400 hover:text-white transition"
          >
            <FaArrowLeft />
          </button>
          <div>
            <h1 className="text-xl font-extrabold text-white flex items-center gap-2">
              {name}
              <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                ● LIVE
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">Created: Aug 9, 2026 • Updated 12 minutes ago</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleNavigate('build')}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
          >
            <FaCheckCircle className="text-cyan-400" /> Build
          </button>
          <button
            onClick={() => handleNavigate('code')}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
          >
            <FaCode className="text-emerald-400" /> Code
          </button>
          <button
            onClick={() => handleNavigate('metrics')}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
          >
            <FaShieldAlt className="text-amber-400" /> Quality
          </button>
          <button
            onClick={() => handleNavigate('plugins')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center gap-1.5"
          >
            <FaRocket /> Deploy
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Project Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl">
            <span className="text-xs text-slate-400 font-sans block mb-1">Quality Score</span>
            <span className="text-2xl font-black text-emerald-400">{score} <span className="text-xs text-slate-500 font-normal">/ 100</span></span>
          </div>

          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl">
            <span className="text-xs text-slate-400 font-sans block mb-1">Tests Passed</span>
            <span className="text-2xl font-black text-cyan-400">{testsPassed} / {testsTotal}</span>
          </div>

          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl font-sans">
            <span className="text-xs text-slate-400 block mb-1">Stack Components</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {stack.map((st, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-[11px] font-mono text-slate-300">
                  {st}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Activity & Versions Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ProjectActivity activity={activity} />
          <ProjectVersions versions={versions} onViewVersion={() => handleNavigate('code')} />
        </div>

        {/* Project Memory & Decisions Dashboard */}
        <ProjectMemoryDashboard projectId={generationId} />
      </div>
    </div>
  );
}
