import React, { useState, useEffect } from 'react';

export default function WorkspaceDashboard() {
  const [projects, setProjects] = useState([
    { id: 'proj_ecommerce', name: 'Ecommerce', status: 'ACTIVE', description: 'Ecommerce Enterprise Suite', created_at: '2026-07-23' },
    { id: 'proj_hospital', name: 'Hospital', status: 'ACTIVE', description: 'Hospital Healthcare Portal', created_at: '2026-07-23' },
    { id: 'proj_airesume', name: 'AIResume', status: 'ACTIVE', description: 'AI Resume Builder Platform', created_at: '2026-07-23' },
    { id: 'proj_crm', name: 'CRM', status: 'ACTIVE', description: 'CRM Customer Intelligence', created_at: '2026-07-23' },
  ]);

  const [activeProjectId, setActiveProjectId] = useState('proj_ecommerce');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [chatPrompt, setChatPrompt] = useState('');
  const [chatLog, setChatLog] = useState([
    { role: 'assistant', text: 'Welcome to AIForge Autonomous Workspace. How can I assist across your projects today?' }
  ]);

  const agents = [
    { name: 'Planner Agent', status: 'ONLINE', task: 'Monitoring project roadmap' },
    { name: 'Architect Agent', status: 'ONLINE', task: 'Enforcing clean architecture' },
    { name: 'Backend Agent', status: 'WORKING', task: 'Generating FastAPI async CRUD controllers' },
    { name: 'Frontend Agent', status: 'WORKING', task: 'Rendering React Tailwind UI components' },
    { name: 'Testing Agent', status: 'ONLINE', task: 'Running Pytest verification suites' },
    { name: 'Reviewer Agent', status: 'ONLINE', task: 'Performing code quality checks' },
    { name: 'DevOps Agent', status: 'ONLINE', task: 'Managing Docker & CI/CD workflows' },
  ];

  const handleSwitchProject = (pid) => {
    setActiveProjectId(pid);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchQuery) return;
    setSearchResults([
      { project: 'Ecommerce', type: 'Source Code', file: 'src/auth/jwt_handler.py', match: 'JWT Authentication Package' },
      { project: 'CRM', type: 'Database Model', file: 'src/models/user.py', match: 'User Account Schema' },
      { project: 'Shared Templates Base', type: 'Shared Template', file: 'templates/docker-compose.yml', match: 'Multi-stage Container Config' },
    ]);
  };

  const handleSendChat = (e) => {
    e.preventDefault();
    if (!chatPrompt) return;
    const userMsg = { role: 'user', text: chatPrompt };
    setChatLog((prev) => [...prev, userMsg]);
    
    let botReply = `Executed query across all workspace projects: "${chatPrompt}"`;
    if (chatPrompt.toLowerCase().includes('jwt') || chatPrompt.toLowerCase().includes('update')) {
      botReply = 'Updated JWT Authentication package across all 4 workspace projects: Ecommerce, Hospital, AIResume, CRM.';
    }

    setTimeout(() => {
      setChatLog((prev) => [...prev, { role: 'assistant', text: botReply }]);
    }, 500);

    setChatPrompt('');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            AI Engineering Workspace Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Autonomous Multi-Agent AI Company • Managing 4 Enterprise Projects Simultaneously
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-right">
            <div className="text-xs text-slate-400">Total Tokens Used</div>
            <div className="text-sm font-semibold text-emerald-400">145,000 Tokens</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-right">
            <div className="text-xs text-slate-400">System Status</div>
            <div className="text-sm font-semibold text-blue-400">100% ONLINE</div>
          </div>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Projects & Search */}
        <div className="space-y-6">
          {/* Projects Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <h2 className="text-lg font-semibold mb-4 text-blue-400 flex justify-between items-center">
              <span>Workspace Projects</span>
              <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">4 Active</span>
            </h2>
            <div className="space-y-3">
              {projects.map((p) => (
                <div
                  key={p.id}
                  onClick={() => handleSwitchProject(p.id)}
                  className={`p-3 rounded-lg cursor-pointer transition border ${
                    activeProjectId === p.id
                      ? 'bg-blue-600/20 border-blue-500 text-white'
                      : 'bg-slate-850 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex justify-between items-center font-medium">
                    <span>{p.name}</span>
                    <span className="text-xs text-emerald-400 font-mono">● {p.status}</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{p.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Global Search Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <h2 className="text-lg font-semibold mb-3 text-indigo-400">Workspace Global Search</h2>
            <form onSubmit={handleSearch} className="flex gap-2 mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search code, components, JWT..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
              />
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium">
                Search
              </button>
            </form>
            {searchResults.length > 0 && (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {searchResults.map((r, idx) => (
                  <div key={idx} className="p-2 bg-slate-800/50 rounded border border-slate-700/50 text-xs">
                    <span className="text-blue-400 font-semibold">{r.project}</span> • <span className="text-slate-400">{r.type}</span>
                    <div className="font-mono text-slate-300 mt-1">{r.file}</div>
                    <div className="text-emerald-400 text-xs mt-0.5">{r.match}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Middle Column: Agent Status & Live Event Stream */}
        <div className="space-y-6 lg:col-span-2">
          {/* Agent Status Grid */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <h2 className="text-lg font-semibold mb-4 text-emerald-400">Autonomous AI Agent Status Grid</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {agents.map((a, idx) => (
                <div key={idx} className="p-3 bg-slate-800/60 border border-slate-700/50 rounded-lg">
                  <div className="flex justify-between items-center font-medium text-sm">
                    <span>{a.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded font-mono ${a.status === 'WORKING' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
                      {a.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{a.task}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Workspace Global Chat */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <h2 className="text-lg font-semibold mb-3 text-cyan-400">Global AI Workspace Chat Assistant</h2>
            <div className="h-48 overflow-y-auto bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3 mb-4">
              {chatLog.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-lg p-3 text-xs ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-200'}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>
            <form onSubmit={handleSendChat} className="flex gap-2">
              <input
                type="text"
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                placeholder="Ask workspace assistant e.g. 'Update JWT package everywhere'..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              />
              <button type="submit" className="bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-2 rounded-lg text-sm font-medium">
                Execute
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
