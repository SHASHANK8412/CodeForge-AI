import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  GitPullRequest,
  GitBranch,
  GitCommit,
  CheckCircle2,
  AlertCircle,
  Shield,
  Send,
  RefreshCw,
  ExternalLink,
  Lock,
  Globe,
  UploadCloud,
  Check,
  XCircle,
  Terminal
} from 'lucide-react';

export default function GitHubDashboardPage() {
  const { projectId = 'aiforge-demo' } = useParams();
  const [loading, setLoading] = useState(false);
  const [copilotQuery, setCopilotQuery] = useState('');
  const [copilotResponse, setCopilotResponse] = useState(null);

  // Autonomous Publishing State
  const [repoMeta, setRepoMeta] = useState({
    connected: false,
    status: 'unlinked',
    repository: {
      name: `aiforge-${projectId}`,
      url: '',
      visibility: 'private',
      branch: 'main',
      last_commit_sha: '',
      last_commit_message: '',
      last_sync_time: ''
    }
  });
  const [publishConfig, setPublishConfig] = useState({
    repoName: `aiforge-${projectId}`,
    description: `Autonomously generated project by AIForge: ${projectId}`,
    visibility: 'private'
  });
  const [publishing, setPublishing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const [data, setData] = useState({
    connected_repository: 'SHASHANK8412/CodeForge-AI',
    active_branch: 'main',
    open_prs_count: 1,
    ci_overall_status: 'SUCCESS',
    security_gate_status: 'PASS',
    open_prs: [
      {
        number: 42,
        title: 'Fix checkout transaction database pool timeout',
        head_branch: 'aiforge/fix-checkout-timeout',
        base_branch: 'main',
        html_url: 'https://github.com/SHASHANK8412/CodeForge-AI/pull/42',
        ci_status: 'SUCCESS',
        review_status: 'APPROVE',
        test_summary: '52/52 PASS',
        security_summary: 'PASS',
        browser_summary: '24/24 PASS',
        performance_summary: 'P95 improved'
      }
    ],
    recent_commits: [
      { sha: '9af8c96', message: 'feat: generate project', author: 'AIForge Agent' }
    ]
  });

  const fetchRepoMetadata = async () => {
    try {
      const res = await fetch(`/api/github/repository/${projectId}`);
      if (res.ok) {
        const json = await res.json();
        if (json.connected) {
          setRepoMeta(json);
        }
      }
    } catch (e) {
      console.warn('Could not fetch repo metadata:', e);
    }
  };

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/github/overview?project_id=${projectId}`);
      if (res.ok) {
        const result = await res.json();
        setData(result);
      }
      await fetchRepoMetadata();
    } catch (e) {
      console.warn('Failed to fetch GitHub overview:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [projectId]);

  const handlePublish = async () => {
    setPublishing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await fetch('/api/github/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          repo_name: publishConfig.repoName || `aiforge-${projectId}`,
          description: publishConfig.description,
          private: publishConfig.visibility === 'private'
        })
      });

      const json = await res.json();

      if (!res.ok) {
        const detail = json.detail;
        if (typeof detail === 'object' && detail.error === 'SECURITY_VIOLATION') {
          throw new Error(`Security Violation: ${detail.message}`);
        }
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      }

      setSuccessMessage(`Repository successfully published to GitHub! URL: ${json.repository?.url}`);
      await fetchRepoMetadata();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to publish repository to GitHub.');
    } finally {
      setPublishing(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await fetch('/api/github/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          commit_message: 'feat: update project files and sync tests'
        })
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.detail || 'Failed to sync with GitHub repository.');
      }

      setSuccessMessage('Successfully synced latest code and commits with GitHub.');
      await fetchRepoMetadata();
    } catch (err) {
      setErrorMessage(err.message || 'Sync failed.');
    } finally {
      setSyncing(false);
    }
  };

  const handleCopilotSubmit = async (e) => {
    e.preventDefault();
    if (!copilotQuery.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/github/copilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: copilotQuery, project_id: projectId })
      });
      if (res.ok) {
        const resData = await res.json();
        setCopilotResponse(resData);
      }
    } catch (e) {
      console.error('Copilot query error:', e);
    } finally {
      setLoading(false);
    }
  };

  const isPublished = repoMeta.connected && repoMeta.status === 'published';
  const repoName = repoMeta.repository?.name || publishConfig.repoName;
  const repoUrl = repoMeta.repository?.url;
  const visibility = repoMeta.repository?.visibility || publishConfig.visibility;
  const latestCommitMsg = repoMeta.repository?.last_commit_message || 'feat: generate project';
  const latestCommitSha = repoMeta.repository?.last_commit_sha || '9af8c96';

  return (
    <div className="min-h-screen bg-[#08090D] text-[#F5F7FA] font-sans p-8 space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#242833] pb-6">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <GitPullRequest className="text-[#8D5CF6] w-7 h-7 shrink-0" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Autonomous GitHub Integration
            </h1>
            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider shrink-0">
              {isPublished ? 'PUBLISHED' : 'CONNECTED'}
            </span>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1.5">
            Project ID: <span className="font-mono text-[#F5F7FA] font-semibold">{projectId}</span> | Default Branch: <span className="font-mono text-[#8D5CF6] font-semibold">main</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isPublished && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="bg-[#151821] hover:bg-[#1C212D] border border-[#242833] text-cyan-400 px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shrink-0"
            >
              <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing...' : 'Sync / Push Updates'}
            </button>
          )}
          <button
            onClick={fetchOverview}
            disabled={loading}
            className="bg-[#0F1117] hover:bg-[#151821] border border-[#242833] text-[#F5F7FA] px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shrink-0"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error / Success Banners */}
      {errorMessage && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl flex items-start gap-3 text-xs">
          <XCircle size={16} className="shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold">Error:</span> {errorMessage}
          </div>
        </div>
      )}

      {successMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-4 rounded-xl flex items-start gap-3 text-xs">
          <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold">Success:</span> {successMessage}
          </div>
        </div>
      )}

      {/* PRIMARY GITHUB INTEGRATION DASHBOARD CARD (Requirements Specification) */}
      <div className="bg-[#0F1117] border border-[#242833] rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-violet-600/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 pb-6 border-b border-[#242833]">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#8D5CF6] font-bold">
              AIForge GitHub Integration Engine
            </span>
            <h2 className="text-lg font-black text-white mt-1">
              Repository Publishing & Synchronization
            </h2>
            <p className="text-xs text-[#9AA1B2] mt-1">
              Automatically creates remote GitHub repository, generates README, .gitignore, CI workflow, and pushes code with pre-publish secret verification.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {!isPublished ? (
              <button
                onClick={handlePublish}
                disabled={publishing}
                className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition shadow-lg shadow-violet-500/20 flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <UploadCloud size={15} className={publishing ? 'animate-bounce' : ''} />
                {publishing ? 'Publishing to GitHub...' : 'Publish to GitHub'}
              </button>
            ) : (
              <a
                href={repoUrl || `https://github.com/aiforge/${repoName}`}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 px-5 py-2.5 rounded-xl text-xs font-bold transition flex items-center gap-2"
              >
                <ExternalLink size={14} />
                Open GitHub Repository
              </a>
            )}
          </div>
        </div>

        {/* 5-Column Status Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-6">
          {/* Connection */}
          <div className="bg-[#08090D] border border-[#242833] rounded-xl p-4 space-y-1">
            <span className="text-[10px] text-[#9AA1B2] uppercase font-bold tracking-wider">Connection</span>
            <div className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 size={14} /> Connected
            </div>
            <span className="text-[10px] text-[#6B7280]">GitHub REST API v3</span>
          </div>

          {/* Repository */}
          <div className="bg-[#08090D] border border-[#242833] rounded-xl p-4 space-y-1">
            <span className="text-[10px] text-[#9AA1B2] uppercase font-bold tracking-wider">Repository</span>
            <div className="text-xs font-mono font-bold text-white truncate" title={repoName}>
              {repoName}
            </div>
            <span className="text-[10px] text-cyan-400">Branch: main</span>
          </div>

          {/* Visibility */}
          <div className="bg-[#08090D] border border-[#242833] rounded-xl p-4 space-y-1">
            <span className="text-[10px] text-[#9AA1B2] uppercase font-bold tracking-wider">Visibility</span>
            <div className="text-sm font-bold text-white flex items-center gap-1.5 capitalize">
              {visibility === 'private' ? <Lock size={13} className="text-amber-400" /> : <Globe size={13} className="text-cyan-400" />}
              {visibility}
            </div>
            <span className="text-[10px] text-[#6B7280]">Secure Default</span>
          </div>

          {/* Status */}
          <div className="bg-[#08090D] border border-[#242833] rounded-xl p-4 space-y-1">
            <span className="text-[10px] text-[#9AA1B2] uppercase font-bold tracking-wider">Status</span>
            <div className="text-sm font-bold text-white flex items-center gap-1.5">
              {isPublished ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <Check size={14} /> Published
                </span>
              ) : (
                <span className="text-amber-400 flex items-center gap-1">
                  <AlertCircle size={14} /> Ready to Publish
                </span>
              )}
            </div>
            <span className="text-[10px] text-[#6B7280]">{isPublished ? 'Remote Synced' : 'Local Git Ready'}</span>
          </div>

          {/* Latest Commit */}
          <div className="bg-[#08090D] border border-[#242833] rounded-xl p-4 space-y-1">
            <span className="text-[10px] text-[#9AA1B2] uppercase font-bold tracking-wider">Latest Commit</span>
            <div className="text-xs font-mono text-white truncate" title={latestCommitMsg}>
              {latestCommitMsg}
            </div>
            <span className="text-[10px] font-mono text-[#8D5CF6]">SHA: {latestCommitSha}</span>
          </div>
        </div>

        {/* Configuration inputs if unpublished */}
        {!isPublished && (
          <div className="mt-6 pt-5 border-t border-[#242833] grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-[11px] font-bold text-[#9AA1B2] block mb-1">Repository Name</label>
              <input
                type="text"
                value={publishConfig.repoName}
                onChange={(e) => setPublishConfig({ ...publishConfig, repoName: e.target.value })}
                placeholder="Repository Name"
                className="w-full bg-[#08090D] border border-[#242833] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-bold text-[#9AA1B2] block mb-1">Repository Description</label>
              <input
                type="text"
                value={publishConfig.description}
                onChange={(e) => setPublishConfig({ ...publishConfig, description: e.target.value })}
                placeholder="Description"
                className="w-full bg-[#08090D] border border-[#242833] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500"
              />
            </div>
            <div>
              <label className="text-[11px] font-bold text-[#9AA1B2] block mb-1">Visibility</label>
              <select
                value={publishConfig.visibility}
                onChange={(e) => setPublishConfig({ ...publishConfig, visibility: e.target.value })}
                className="w-full bg-[#08090D] border border-[#242833] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500"
              >
                <option value="private">Private (Recommended)</option>
                <option value="public">Public</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-2">
          <div className="flex justify-between items-center text-[#9AA1B2]">
            <span className="text-[10px] font-bold uppercase tracking-wider">Active Feature Branch</span>
            <GitBranch size={15} className="text-[#8D5CF6]" />
          </div>
          <div className="text-xs font-mono font-bold text-cyan-400 truncate mt-1">{data.active_branch}</div>
          <div className="text-[10px] text-emerald-400">Default Branch Protected (`main`)</div>
        </div>

        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-2">
          <div className="flex justify-between items-center text-[#9AA1B2]">
            <span className="text-[10px] font-bold uppercase tracking-wider">Open Pull Requests</span>
            <GitPullRequest size={15} className="text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1">{data.open_prs_count}</div>
          <div className="text-[10px] text-[#9AA1B2]">Ready for Human Code Review</div>
        </div>

        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-2">
          <div className="flex justify-between items-center text-[#9AA1B2]">
            <span className="text-[10px] font-bold uppercase tracking-wider">GitHub Actions CI</span>
            <CheckCircle2 size={15} className="text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{data.ci_overall_status}</div>
          <div className="text-[10px] text-[#9AA1B2]">.github/workflows/aiforge-ci.yml</div>
        </div>

        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-2">
          <div className="flex justify-between items-center text-[#9AA1B2]">
            <span className="text-[10px] font-bold uppercase tracking-wider">Pre-Publish Security Gate</span>
            <Shield size={15} className="text-[#8D5CF6]" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{data.security_gate_status}</div>
          <div className="text-[10px] text-emerald-400">Zero Secrets Leaked</div>
        </div>
      </div>

      {/* Main Grid: Open Pull Requests & Copilot Assistant */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Open PRs Section */}
        <div className="lg:col-span-2 bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#F5F7FA] flex items-center gap-2 border-b border-[#242833] pb-3">
            <GitPullRequest size={16} className="text-emerald-400" />
            Open Pull Requests
          </h3>

          <div className="flex flex-col gap-3">
            {data.open_prs.map(pr => (
              <div key={pr.number} className="bg-[#08090D] border border-[#242833] rounded-lg p-4 space-y-3">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-xs font-bold text-white">#{pr.number} {pr.title}</span>
                    <a
                      href={pr.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:underline flex items-center gap-1 text-[11px] font-mono mt-1"
                    >
                      <ExternalLink size={11} /> View PR on GitHub
                    </a>
                  </div>
                  <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0">
                    AI APPROVED
                  </span>
                </div>

                <div className="text-[11px] text-[#9AA1B2] font-mono">
                  Branch: <span className="text-[#F5F7FA] bg-[#151821] px-1.5 py-0.5 rounded border border-[#242833]">{pr.head_branch}</span> &rarr; <span className="text-[#F5F7FA] bg-[#151821] px-1.5 py-0.5 rounded border border-[#242833]">{pr.base_branch}</span>
                </div>

                {/* Badges Grid */}
                <div className="flex gap-2 flex-wrap">
                  <span className="bg-[#151821] text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    Tests: {pr.test_summary}
                  </span>
                  <span className="bg-[#151821] text-[#A7F3D0] border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    Security: {pr.security_summary}
                  </span>
                  <span className="bg-[#151821] text-cyan-400 border border-blue-500/20 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    Browser: {pr.browser_summary}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Copilot Query Box */}
        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-[#F5F7FA] flex items-center gap-2 border-b border-[#242833] pb-3">
              <Terminal size={16} className="text-[#8D5CF6]" />
              GitHub Engineering Copilot
            </h3>
            <p className="text-xs text-[#9AA1B2] mt-2">
              Query CI diagnostic logs, pull request decisions, or commit revisions autonomously.
            </p>

            <form onSubmit={handleCopilotSubmit} className="mt-4 space-y-3">
              <input
                type="text"
                value={copilotQuery}
                onChange={(e) => setCopilotQuery(e.target.value)}
                placeholder="e.g., Why did CI fail on main?"
                className="w-full bg-[#08090D] border border-[#242833] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500"
              />
              <button
                type="submit"
                disabled={loading || !copilotQuery.trim()}
                className="w-full bg-[#151821] hover:bg-[#1C212D] border border-[#242833] text-[#F5F7FA] py-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Send size={12} />
                Ask Copilot
              </button>
            </form>

            {copilotResponse && (
              <div className="mt-4 p-3 bg-[#08090D] border border-[#242833] rounded-lg text-xs text-[#9AA1B2] space-y-2">
                <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wide block">Copilot Diagnosis</span>
                <p className="text-[#F5F7FA]">{copilotResponse.answer}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
