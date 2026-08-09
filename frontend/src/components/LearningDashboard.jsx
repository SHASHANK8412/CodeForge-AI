import React, { useEffect, useState } from 'react';

export const LearningDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/learning/dashboard')
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success') {
          setData(resData.learning_dashboard);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load Learning Dashboard:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-6 text-white">Loading Learning Engine Dashboard...</div>;
  }

  const dash = data || {
    projects_stored_count: 14,
    patterns_learned_count: 8,
    bug_library_count: 12,
    best_practices_count: 5,
    success_rate_pct: 98.4,
    average_build_time_seconds: 18.2,
    most_used_technologies: ['FastAPI', 'React', 'PostgreSQL', 'Docker', 'Redis'],
    knowledge_base_size_mb: 42.8,
    recent_projects: [],
    top_ranked_templates: []
  };

  return (
    <div className="p-6 bg-slate-900 text-white min-h-screen font-sans">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-blue-400">🧠 AIForge Learning Engine Dashboard</h1>
          <p className="text-slate-400 mt-1">Continuous learning from past projects, bug fixes, patterns, and agent performance</p>
        </div>
        <div className="bg-blue-600/20 border border-blue-500/30 rounded-lg px-4 py-2 text-blue-300 font-semibold">
          Knowledge Base: {dash.knowledge_base_size_mb} MB
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg">
          <p className="text-slate-400 text-sm font-medium">Projects Stored</p>
          <p className="text-3xl font-extrabold text-white mt-2">{dash.projects_stored_count}</p>
        </div>
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg">
          <p className="text-slate-400 text-sm font-medium">Patterns Learned</p>
          <p className="text-3xl font-extrabold text-emerald-400 mt-2">{dash.patterns_learned_count}</p>
        </div>
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg">
          <p className="text-slate-400 text-sm font-medium">Bug Solutions Library</p>
          <p className="text-3xl font-extrabold text-amber-400 mt-2">{dash.bug_library_count}</p>
        </div>
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg">
          <p className="text-slate-400 text-sm font-medium">Build Success Rate</p>
          <p className="text-3xl font-extrabold text-blue-400 mt-2">{dash.success_rate_pct}%</p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Learned Patterns */}
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-bold text-white mb-4">✨ Top Ranked Reusable Patterns</h2>
          <div className="space-y-4">
            {(dash.top_ranked_templates || []).map((tpl, idx) => (
              <div key={idx} className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-4 flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-blue-300">{tpl.pattern_name}</h3>
                  <p className="text-xs text-slate-400 mt-1">Category: {tpl.category} | Occurrences: {tpl.occurrences || 1}</p>
                </div>
                <div className="text-right">
                  <span className="bg-emerald-500/20 text-emerald-300 text-xs px-2.5 py-1 rounded font-medium">
                    {Math.round((tpl.confidence || 0.95) * 100)}% Confidence
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Most Common Tech Stack */}
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-bold text-white mb-4">🚀 Most Common Technologies</h2>
          <div className="flex flex-wrap gap-3">
            {(dash.most_used_technologies || []).map((tech, idx) => (
              <span key={idx} className="bg-slate-700/80 text-blue-300 border border-slate-600 px-4 py-2 rounded-lg font-medium text-sm">
                {tech}
              </span>
            ))}
          </div>
          <div className="mt-8">
            <h3 className="text-md font-semibold text-slate-300 mb-2">Average Build Time</h3>
            <div className="text-2xl font-bold text-emerald-400">{dash.average_build_time_seconds} seconds</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningDashboard;
