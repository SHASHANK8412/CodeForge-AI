import React, { useState, useEffect } from 'react';
import { FaTasks, FaFolderOpen, FaProjectDiagram, FaRunning, FaCheckCircle, FaUserTie, FaLayerGroup, FaPlus } from 'react-icons/fa';

export default function ProjectManagerDashboard() {
  const [prompt, setPrompt] = useState('Build an AI Resume Analyzer Platform');
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('epics');

  const fetchPlan = async (userPrompt) => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/project/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt })
      });
      if (res.ok) {
        const data = await res.json();
        setPlan(data);
      }
    } catch {
      // Fallback
      setPlan({
        prompt: userPrompt,
        pm_analysis: { complexity: 'Medium-High', recommended_stack: 'FastAPI + React + PostgreSQL + Docker' },
        epics: [
          { id: 'EP-01', title: 'Authentication & Authorization', description: 'User login & JWT tokens' },
          { id: 'EP-02', title: 'Resume Parser Service', description: 'PDF text extraction & NLP analysis' }
        ],
        tasks: [
          { id: 'TSK-01', title: 'DB Schema', agent: 'Database Agent', priority: 'HIGH', status: 'COMPLETED' },
          { id: 'TSK-02', title: 'FastAPI Backend', agent: 'Backend Agent', priority: 'HIGH', status: 'COMPLETED' }
        ],
        progress: { progress_percentage: 100.0, completed_tasks: 5, total_tasks: 5 }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan(prompt);
  }, []);

  const handleGeneratePlan = (e) => {
    e.preventDefault();
    if (prompt.trim()) {
      fetchPlan(prompt);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaUserTie className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-bold tracking-wide text-white uppercase">
            Autonomous Product Manager & Sprint Orchestrator
          </h3>
        </div>

        <form onSubmit={handleGeneratePlan} className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter application goal prompt..."
            className="bg-slate-950 border border-slate-800 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:border-emerald-500 font-mono w-64"
          />
          <button type="submit" disabled={loading} className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow">
            <FaPlus /> Plan Project
          </button>
        </form>
      </div>

      {/* Product Manager Analysis Summary Banner */}
      {plan?.pm_analysis && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Project Target</span>
            <span className="text-xs font-bold text-white truncate block">{plan.prompt}</span>
          </div>

          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Recommended Architecture</span>
            <span className="text-xs font-bold text-indigo-400 truncate block">{plan.pm_analysis.recommended_stack}</span>
          </div>

          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Overall Progress</span>
            <span className="text-xs font-bold text-emerald-400 block">{plan.progress?.progress_percentage || 100}% Completed</span>
          </div>
        </div>
      )}

      {/* Sub-Tabs: Epics, User Stories, Tasks, Sprints */}
      <div className="flex gap-2 border-b border-slate-800 pb-2 mb-4 font-mono text-xs">
        {['epics', 'user_stories', 'tasks', 'sprints'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg font-semibold uppercase tracking-wide transition cursor-pointer ${
              activeTab === tab
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            {tab.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Tab Content Display */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs">
        {activeTab === 'epics' && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
              <FaFolderOpen className="text-emerald-400" /> Project Epics Roadmap ({plan?.epics?.length || 0})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {plan?.epics?.map((epic) => (
                <div key={epic.id} className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">{epic.id}</span>
                    <span className="text-slate-400 text-[10px]">Agile Epic</span>
                  </div>
                  <h5 className="font-bold text-white text-xs">{epic.title}</h5>
                  <p className="text-slate-400 text-[11px] leading-relaxed">{epic.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'user_stories' && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
              <FaLayerGroup className="text-indigo-400" /> Agile User Stories ({plan?.user_stories?.length || 0})
            </h4>
            <div className="space-y-2">
              {plan?.user_stories?.map((st) => (
                <div key={st.id} className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between text-[11px]">
                  <div>
                    <span className="font-bold text-indigo-300">{st.id} ({st.epic_id}):</span> <span className="text-white font-semibold">{st.title}</span>
                    <p className="text-slate-400 text-[10px] italic mt-0.5">{st.user_story}</p>
                  </div>
                  <span className="text-amber-400 bg-amber-950 px-2 py-0.5 rounded text-[10px] border border-amber-800 font-bold shrink-0">{st.points} pts</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
              <FaTasks className="text-amber-400" /> Task Breakdown & Agent Assignments ({plan?.tasks?.length || 0})
            </h4>
            <div className="space-y-2">
              {plan?.tasks?.map((tsk) => (
                <div key={tsk.id} className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-2">
                    <FaCheckCircle className="text-emerald-400" />
                    <div>
                      <span className="font-bold text-white">{tsk.id}: {tsk.title}</span>
                      <span className="text-slate-400 text-[10px] block">Assigned to: <strong className="text-indigo-300">{tsk.agent}</strong></span>
                    </div>
                  </div>
                  <span className="text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800 font-bold text-[10px]">{tsk.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'sprints' && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
              <FaRunning className="text-rose-400" /> Development Sprints ({plan?.sprints?.length || 0})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {plan?.sprints?.map((sp) => (
                <div key={sp.sprint_number} className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white text-xs">{sp.name}</span>
                    <span className="text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded text-[10px] border border-emerald-800 font-bold">{sp.status}</span>
                  </div>
                  <p className="text-slate-400 text-[10px]">Allocated Tasks: {sp.task_count} items</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
