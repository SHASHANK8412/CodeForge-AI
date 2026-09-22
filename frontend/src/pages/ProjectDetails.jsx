import React, { useState, useEffect } from 'react';
import ProjectActivity from '../components/dashboard/ProjectActivity';
import ProjectVersions from '../components/dashboard/ProjectVersions';
import ProjectMemoryDashboard from '../components/memory/ProjectMemoryDashboard';
import RAGKnowledgeDashboard from '../components/rag/RAGKnowledgeDashboard';
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
      <div className="min-h-screen bg-[#08090D] text-white font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-[#8D5CF6] animate-spin" />
        <h3 className="text-sm font-bold">Loading telemetry pipelines...</h3>
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
    <div className="min-h-screen bg-[#08090D] text-[#F5F7FA] font-sans p-6 space-y-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto flex items-center justify-between border-b border-[#242833] pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setView ? setView('dashboard') : (window.location.href = '/dashboard')}
            className="p-2 bg-[#0F1117] border border-[#242833] rounded-xl text-[#9AA1B2] hover:text-[#F5F7FA] transition cursor-pointer"
          >
            <FaArrowLeft />
          </button>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              {name}
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                ● LIVE
              </span>
            </h1>
            <p className="text-[11px] text-[#9AA1B2] mt-0.5">Telemetry Active • Created Aug 9, 2026</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleNavigate('build')}
            className="px-3.5 py-2 bg-[#0F1117] hover:bg-[#151821] border border-[#242833] text-[#F5F7FA] text-xs font-bold rounded-xl transition flex items-center gap-1.5 cursor-pointer"
          >
            <FaCheckCircle className="text-[#8D5CF6]" /> Pipeline
          </button>
          <button
            onClick={() => handleNavigate('code')}
            className="px-3.5 py-2 bg-[#0F1117] hover:bg-[#151821] border border-[#242833] text-[#F5F7FA] text-xs font-bold rounded-xl transition flex items-center gap-1.5 cursor-pointer"
          >
            <FaCode className="text-emerald-400" /> Workspace
          </button>
          <button
            onClick={() => handleNavigate('metrics')}
            className="px-3.5 py-2 bg-[#0F1117] hover:bg-[#151821] border border-[#242833] text-[#F5F7FA] text-xs font-bold rounded-xl transition flex items-center gap-1.5 cursor-pointer"
          >
            <FaShieldAlt className="text-amber-400" /> Reviews
          </button>
          <button
            onClick={() => handleNavigate('plugins')}
            className="px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white text-xs font-bold rounded-xl transition shadow-lg shadow-violet-500/25 flex items-center gap-1.5 cursor-pointer"
          >
            <FaRocket /> Deploy
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Project Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
          <div className="bg-[#0F1117] border border-[#242833] p-5 rounded-2xl">
            <span className="text-xs text-[#9AA1B2] font-sans block mb-1">Quality Health Score</span>
            <span className="text-2xl font-black text-emerald-400">{score} <span className="text-xs text-[#9AA1B2]/50 font-normal">/ 100</span></span>
          </div>

          <div className="bg-[#0F1117] border border-[#242833] p-5 rounded-2xl">
            <span className="text-xs text-[#9AA1B2] font-sans block mb-1">Testing Pipeline</span>
            <span className="text-2xl font-black text-cyan-400">{testsPassed} / {testsTotal}</span>
          </div>

          <div className="bg-[#0F1117] border border-[#242833] p-5 rounded-2xl font-sans">
            <span className="text-xs text-[#9AA1B2] block mb-1">Engine Stack Info</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {stack.map((st, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-[#08090D] border border-[#242833] rounded text-[11px] font-mono text-[#F5F7FA]">
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

        {/* Project RAG Knowledge Engine */}
        <RAGKnowledgeDashboard projectId={generationId} />
      </div>
    </div>
  );
}
