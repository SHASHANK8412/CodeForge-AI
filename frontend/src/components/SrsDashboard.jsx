import React, { useState } from 'react';
import { FaFileAlt, FaUserCheck, FaTasks, FaListCheck, FaDownload, FaLightbulb } from 'react-icons/fa';

export default function SrsDashboard() {
  const [ideaPrompt, setIdeaPrompt] = useState('Build an e-commerce platform');
  const [srsReport, setSrsReport] = useState({
    project_title: 'Enterprise E-Commerce Platform',
    target_scale: '10,000,000 Active Users',
    functional_requirements: [
      { id: 'FR-01', description: 'User Authentication & Role-Based Access Control (RBAC).' },
      { id: 'FR-02', description: 'Real-time dashboard analytics with interactive filtering.' },
      { id: 'FR-03', description: 'Payment gateway integration with recurring subscription billing.' }
    ],
    user_stories: [
      {
        id: 'US-01',
        as_a: 'Customer',
        i_want: 'to search items by category and price filter',
        so_that: 'I can quickly find products to purchase',
        acceptance_criteria: 'Search results load in <300ms with instant pagination.'
      }
    ],
    sprint_plan: [
      { sprint: 'Sprint 1', goal: 'Core SRS Signoff & FastAPI / React Foundation Setup' },
      { sprint: 'Sprint 2', goal: 'User Auth, RBAC & Database Schema Migrations' },
      { sprint: 'Sprint 3', goal: 'Payment Integration & Real-time WebSockets' },
      { sprint: 'Sprint 4', goal: 'Self-Healing Debugging, Refactoring & Kubernetes Export' }
    ]
  });

  const [generating, setGenerating] = useState(false);

  const handleGenerateSrs = async () => {
    setGenerating(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/requirements/generate-srs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea: ideaPrompt })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.srs) setSrsReport(data.srs);
      }
    } catch (err) {
      console.log('Using fallback SRS data:', err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaFileAlt className="w-5 h-5 text-amber-400" />
          <div>
            <h3 className="text-sm font-bold tracking-wide text-white uppercase">
              AI Product Manager & Requirement Intelligence (Day 50)
            </h3>
            <p className="text-[11px] text-slate-400">Converts vague ideas into complete Software Requirement Specifications (SRS)</p>
          </div>
        </div>

        <button
          onClick={handleGenerateSrs}
          disabled={generating}
          className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-semibold text-xs px-3.5 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow w-fit"
        >
          <FaLightbulb className={generating ? 'animate-spin' : ''} />
          {generating ? 'Generating SRS Specification...' : 'Generate SRS Document'}
        </button>
      </div>

      {/* Input Prompt Box */}
      <div className="mb-5">
        <input
          type="text"
          value={ideaPrompt}
          onChange={(e) => setIdeaPrompt(e.target.value)}
          placeholder="Enter app idea (e.g. Build an Airbnb-like platform)..."
          className="w-full bg-slate-950 border border-slate-800 text-xs px-3 py-2 rounded-lg text-amber-200 outline-none font-mono"
        />
      </div>

      {/* SRS Spec Summary Banner */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 mb-5 font-mono text-xs">
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-sm font-bold text-white uppercase">{srsReport.project_title}</h4>
          <span className="text-[10px] bg-amber-950 text-amber-400 border border-amber-800 px-2 py-0.5 rounded font-bold">
            {srsReport.target_scale}
          </span>
        </div>

        {/* User Stories */}
        <div className="space-y-2 text-[11px] mb-4">
          <span className="text-slate-400 font-bold uppercase block text-[10px]">User Stories & Acceptance Criteria</span>
          {(srsReport.user_stories || []).map((us, idx) => (
            <div key={idx} className="bg-slate-900 p-2.5 rounded border border-slate-800">
              <span className="font-bold text-amber-300 block mb-0.5">[{us.id}] As a {us.as_a}, I want {us.i_want}</span>
              <span className="text-slate-400 block text-[10px]">Criteria: {us.acceptance_criteria}</span>
            </div>
          ))}
        </div>

        {/* Sprint Roadmap */}
        <div className="space-y-1 text-[10px] text-slate-300">
          <span className="text-slate-400 font-bold uppercase block mb-1">Development Sprint Roadmap</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {(srsReport.sprint_plan || []).map((sp, idx) => (
              <div key={idx} className="bg-slate-900 p-2 rounded border border-slate-800">
                <strong className="text-white block">{sp.sprint}:</strong>
                <span className="text-slate-400">{sp.goal}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
