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
    <div style={{ padding: '32px', backgroundColor: '#0A0D14', color: '#F3F4F6', minHeight: '100vh', fontFamily: "'Inter', sans-serif" }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <GitPullRequest style={{ color: '#22C55E' }} size={32} />
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>
              GitHub Integration & Autonomous PR Engineering
            </h1>
            <span style={{
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              color: '#22C55E',
              border: '1px solid #22C55E',
              borderRadius: '20px',
              padding: '4px 12px',
              fontSize: '12px',
              fontWeight: '600'
            }}>
              CONNECTED
            </span>
          </div>
          <p style={{ color: '#9CA3AF', margin: 0, fontSize: '14px' }}>
            Repository: <strong style={{ color: '#E5E7EB' }}>{data.connected_repository}</strong> | Project: <strong style={{ color: '#E5E7EB' }}>{projectId}</strong>
          </p>
        </div>

        <button
          onClick={fetchOverview}
          disabled={loading}
          style={{
            backgroundColor: '#1E293B',
            color: '#E2E8F0',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '10px 18px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Sync Repository
        </button>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>Active Feature Branch</span>
            <GitBranch size={18} style={{ color: '#6366F1' }} />
          </div>
          <div style={{ fontSize: '16px', fontWeight: '700', color: '#60A5FA', wordBreak: 'break-all' }}>{data.active_branch}</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Default Branch Protected (`main`)</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>Open Pull Requests</span>
            <GitPullRequest size={18} style={{ color: '#22C55E' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFFFFF' }}>{data.open_prs_count}</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Ready for Human Review</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>GitHub Actions CI Status</span>
            <CheckCircle2 size={18} style={{ color: '#10B981' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#10B981' }}>{data.ci_overall_status}</div>
          <div style={{ fontSize: '12px', color: '#9CA3AF', marginTop: '4px' }}>Build &amp; Test Workflow</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>Pre-Commit Security Gate</span>
            <Shield size={18} style={{ color: '#8B5CF6' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#A7F3D0' }}>{data.security_gate_status}</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Zero Secrets Leaked</div>
        </div>
      </div>

      {/* Main Grid: Open Pull Requests & Copilot Assistant */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Open PRs Section */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitPullRequest size={20} style={{ color: '#22C55E' }} />
            Open Pull Requests
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {data.open_prs.map(pr => (
              <div key={pr.number} style={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div>
                    <span style={{ fontSize: '16px', fontWeight: '600', color: '#FFFFFF', marginRight: '8px' }}>#{pr.number} {pr.title}</span>
                    <a href={pr.html_url} target="_blank" rel="noopener noreferrer" style={{ color: '#60A5FA', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '13px' }}>
                      <ExternalLink size={14} /> GitHub PR
                    </a>
                  </div>
                  <span style={{ backgroundColor: 'rgba(34, 197, 94, 0.15)', color: '#22C55E', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                    AI APPROVED
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '12px' }}>
                  Branch: <code style={{ color: '#E5E7EB', backgroundColor: '#111827', padding: '2px 6px', borderRadius: '4px' }}>{pr.head_branch}</code> &rarr; <code style={{ color: '#E5E7EB', backgroundColor: '#111827', padding: '2px 6px', borderRadius: '4px' }}>{pr.base_branch}</code>
                </div>

                {/* Badges Grid */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{ backgroundColor: '#111827', color: '#10B981', border: '1px solid #059669', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '500' }}>
                    Tests: {pr.test_summary}
                  </span>
                  <span style={{ backgroundColor: '#111827', color: '#A7F3D0', border: '1px solid #047857', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '500' }}>
                    Security: {pr.security_summary}
                  </span>
                  <span style={{ backgroundColor: '#111827', color: '#60A5FA', border: '1px solid #2563EB', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '500' }}>
                    Browser E2E: {pr.browser_summary}
                  </span>
                  <span style={{ backgroundColor: '#111827', color: '#F59E0B', border: '1px solid #D97706', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '500' }}>
                    Perf: {pr.performance_summary}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Codebase Copilot GitHub Integration */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={20} style={{ color: '#6366F1' }} />
            Codebase Copilot
          </h3>

          <form onSubmit={handleCopilotSubmit} style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={copilotQuery}
                onChange={(e) => setCopilotQuery(e.target.value)}
                placeholder="e.g. 'Why did CI fail?' or 'Create a PR'"
                style={{
                  flex: 1,
                  backgroundColor: '#1F2937',
                  color: '#FFFFFF',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  fontSize: '13px'
                }}
              />
              <button
                type="submit"
                style={{
                  backgroundColor: '#6366F1',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  cursor: 'pointer'
                }}
              >
                <Send size={16} />
              </button>
            </div>
          </form>

          {copilotResponse && (
            <div style={{ backgroundColor: '#1E1B4B', border: '1px solid #4338CA', borderRadius: '8px', padding: '14px', fontSize: '13px', color: '#E0E7FF' }}>
              <strong>Copilot Response:</strong>
              <p style={{ margin: '8px 0 0 0', lineHeight: '1.4' }}>{copilotResponse.answer}</p>
            </div>
          )}

          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #1F2937' }}>
            <h4 style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '10px' }}>Recent Git Commits</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {data.recent_commits.map(c => (
                <div key={c.sha} style={{ fontSize: '12px', color: '#D1D5DB', display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <GitCommit size={14} style={{ color: '#60A5FA' }} />
                  <code style={{ color: '#F59E0B' }}>{c.sha.slice(0, 7)}</code>
                  <span>{c.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
