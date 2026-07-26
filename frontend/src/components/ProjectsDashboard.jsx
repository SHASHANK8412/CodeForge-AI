import React, { useState, useEffect } from 'react';
import { FaFolderOpen, FaSearch, FaHistory, FaTrash, FaPlay, FaCopy, FaCheck, FaLayerGroup } from 'react-icons/fa';

export default function ProjectsDashboard({ onResumeProject }) {
  const [projects, setProjects] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  const [resumePrompt, setResumePrompt] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchProjects = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/memory/projects');
      if (res.ok) {
        const data = await res.json();
        setProjects(data || []);
      }
    } catch {
      // Fallback initial list
      setProjects([
        {
          project_id: 'proj_ecommerce_001',
          name: 'E-Commerce Platform',
          version: 'v2',
          prompt: 'Build an E-Commerce Platform with React, FastAPI, and PostgreSQL',
          tech_stack: { frontend: 'React', backend: 'FastAPI', database: 'PostgreSQL', auth: 'JWT' },
          updated_at: Date.now() / 1000 - 3600
        },
        {
          project_id: 'proj_hospital_002',
          name: 'Hospital Management System',
          version: 'v1',
          prompt: 'Build Hospital Management System with Patient CRUD',
          tech_stack: { frontend: 'React', backend: 'FastAPI', database: 'PostgreSQL', auth: 'JWT' },
          updated_at: Date.now() / 1000 - 86400
        }
      ]);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      fetchProjects();
      return;
    }
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/memory/search?query=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      }
    } catch (err) {
      console.error('Memory search error:', err);
    }
  };

  const handleDelete = async (projectId) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/memory/project/${projectId}`, {
        method: 'DELETE',
      });
      if (selectedProject?.project_id === projectId) setSelectedProject(null);
      fetchProjects();
    } catch (err) {
      console.error('Delete project error:', err);
    }
  };

  const handleResume = async () => {
    if (!selectedProject || !resumePrompt.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/memory/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: selectedProject.project_id,
          new_prompt: resumePrompt,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (onResumeProject) onResumeProject(data.project);
        setResumePrompt('');
        fetchProjects();
      }
    } catch (err) {
      console.error('Resume project error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaFolderOpen className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold tracking-wide text-white uppercase">
            Persistent Projects & Memory Dashboard
          </h3>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Semantic Memory Search (e.g. JWT FastAPI)..."
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono w-60"
          />
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1"
          >
            <FaSearch /> Search
          </button>
        </form>
      </div>

      {/* Projects Grid & Details Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Project List */}
        <div className="lg:col-span-6 space-y-2.5 max-h-96 overflow-y-auto pr-1">
          {projects.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs italic bg-slate-950 rounded-lg border border-slate-800">
              No saved projects found in long-term memory.
            </div>
          ) : (
            projects.map((proj) => (
              <div
                key={proj.project_id}
                onClick={() => setSelectedProject(proj)}
                className={`p-3.5 rounded-xl border transition cursor-pointer flex items-center justify-between ${
                  selectedProject?.project_id === proj.project_id
                    ? 'bg-indigo-950/60 border-indigo-500 text-white'
                    : 'bg-slate-950 border-slate-800/80 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="min-w-0 flex-1 pr-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-xs text-white truncate">{proj.name}</span>
                    <span className="text-[10px] font-mono bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800">
                      {proj.version || 'v1'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate font-mono">{proj.prompt}</p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(proj.project_id);
                    }}
                    className="text-slate-500 hover:text-rose-400 p-1.5 transition cursor-pointer"
                    title="Delete Project"
                  >
                    <FaTrash className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Selected Project Details & Resume Panel */}
        <div className="lg:col-span-6 bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          {selectedProject ? (
            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-indigo-300 text-xs">{selectedProject.name}</span>
                <span className="text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800 text-[10px]">
                  Version: {selectedProject.version || 'v1'}
                </span>
              </div>

              <div>
                <span className="text-slate-500 text-[10px]">Tech Stack:</span>
                <div className="flex flex-wrap gap-1.5 mt-1 text-[11px]">
                  {Object.entries(selectedProject.tech_stack || {}).map(([k, v]) => (
                    <span key={k} className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                      {k}: <strong className="text-white">{String(v)}</strong>
                    </span>
                  ))}
                </div>
              </div>

              {/* Resume / Bumping Version Box */}
              <div className="pt-2 border-t border-slate-800 space-y-2">
                <label className="text-[11px] text-indigo-300 font-semibold flex items-center gap-1.5">
                  <FaPlay className="w-3 h-3 text-indigo-400" /> Resume & Evolve Project ({selectedProject.version || 'v1'} → v{(parseInt((selectedProject.version || 'v1').replace('v', '')) || 1) + 1}):
                </label>
                <textarea
                  value={resumePrompt}
                  onChange={(e) => setResumePrompt(e.target.value)}
                  placeholder="Enter follow-up instructions (e.g. Add Payment gateway, Add Category CRUD)..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 h-20"
                />
                <button
                  onClick={handleResume}
                  disabled={loading || !resumePrompt.trim()}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs py-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <FaPlay className="w-3 h-3" /> Resume Development & Bump Version
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center min-h-[220px] text-slate-500 text-xs italic text-center">
              <FaLayerGroup className="w-8 h-8 mb-2 text-slate-700" />
              Select a project from the left to view details and resume development.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
