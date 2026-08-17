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
  Code2,
  Cpu
} from 'lucide-react';

export default function GitHubDashboardPage() {
  const { projectId = 'aiforge-demo' } = useParams();
  const [loading, setLoading] = useState(false);
  const [copilotQuery, setCopilotQuery] = useState('');
  const [copilotResponse, setCopilotResponse] = useState(null);

  const [data, setData] = useState({
    connected_repository: 'SHASHANK8412/CodeForge-AI',
    active_branch: 'aiforge/fix-checkout-timeout',
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
      { sha: '9af8c96', message: 'feat(day28-29): Redis Caching & Prometheus Observability', author: 'AIForge Agent' },
      { sha: '001schema', message: 'feat(day27): Initial pgvector & PostgreSQL Schema Migration', author: 'AIForge Agent' }
    ]
  });

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/github/overview?project_id=${projectId}`);
      if (res.ok) {
        const result = await res.json();
        setData(result);
      }
    } catch (e) {
      console.warn('Failed to fetch GitHub overview:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [projectId]);

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

  return (
    <div className="min-h-screen bg-[#08090D] text-[#F5F7FA] font-sans p-8 space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#242833] pb-6">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <GitPullRequest className="text-[#8D5CF6] w-7 h-7 shrink-0" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              GitHub Integration & PR Engineering
            </h1>
            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider shrink-0">
              CONNECTED
            </span>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1.5">
            Repository: <span className="font-mono text-[#F5F7FA] font-semibold">{data.connected_repository}</span> | Project ID: <span className="font-mono text-[#F5F7FA] font-semibold">{projectId}</span>
          </p>
        </div>

        <button
          onClick={fetchOverview}
          disabled={loading}
          className="bg-[#0F1117] hover:bg-[#151821] border border-[#242833] text-[#F5F7FA] px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shrink-0"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Sync Repository
        </button>
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
          <div className="text-[10px] text-[#9AA1B2]">Autotesting Workflow Status</div>
        </div>

        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-2">
          <div className="flex justify-between items-center text-[#9AA1B2]">
            <span className="text-[10px] font-bold uppercase tracking-wider">Security Gate</span>
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
                    Browser E2E: {pr.browser_summary}
                  </span>
                  <span className="bg-[#151821] text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    Perf: {pr.performance_summary}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Codebase Copilot GitHub Integration */}
        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#F5F7FA] flex items-center gap-2 border-b border-[#242833] pb-3">
            <Cpu size={16} className="text-[#8D5CF6]" />
            PR Copilot Assistant
          </h3>

          <form onSubmit={handleCopilotSubmit} className="flex gap-2">
            <input
              type="text"
              value={copilotQuery}
              onChange={(e) => setCopilotQuery(e.target.value)}
              placeholder="Query PR checks, commits, error logs..."
              className="flex-1 bg-[#08090D] border border-[#242833] rounded-lg px-3 py-2 text-xs text-[#F5F7FA] placeholder-[#9AA1B2]/40 outline-none focus:border-[#8D5CF6] transition font-sans"
            />
            <button
              type="submit"
              className="bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white p-2 rounded-lg transition active:scale-95 cursor-pointer flex items-center justify-center shrink-0"
            >
              <Send size={13} />
            </button>
          </form>

          {copilotResponse && (
            <div className="bg-[#8D5CF6]/10 border border-[#8D5CF6]/30 rounded-lg p-3 text-xs text-[#F5F7FA]">
              <strong className="text-[#8D5CF6] block font-mono text-[10px] uppercase">Copilot Response:</strong>
              <p className="margin-top: 6px leading-relaxed text-[11px] whitespace-pre-wrap">{copilotResponse.answer}</p>
            </div>
          )}

          <div className="pt-4 border-t border-[#242833]">
            <h4 className="text-[10px] font-mono font-bold uppercase text-[#9AA1B2] mb-3">Recent Git Commits</h4>
            <div className="space-y-2">
              {data.recent_commits.map(c => (
                <div key={c.sha} className="text-[11px] text-[#9AA1B2] flex items-start gap-2 leading-relaxed">
                  <GitCommit size={13} className="text-cyan-400 shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <code className="text-[#8D5CF6] font-bold mr-1">{c.sha.slice(0, 7)}</code>
                    <span className="text-[#F5F7FA] font-sans text-xs">{c.message}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
