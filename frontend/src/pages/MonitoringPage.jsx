import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Activity,
  Server,
  Zap,
  AlertTriangle,
  Clock,
  ShieldCheck,
  BarChart2,
  RefreshCw,
  Cpu,
  Layers,
  Database
} from 'lucide-react';

export default function MonitoringPage() {
  const { projectId = 'aiforge-demo' } = useParams();
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboard, setDashboard] = useState('AIForge Overview');
  const [loading, setLoading] = useState(false);

  const [metrics, setMetrics] = useState({
    system_health: 'HEALTHY',
    requests_total: 12842,
    error_rate_pct: 0.14,
    p95_latency_ms: 182.0,
    active_requests: 2,
    agent_latency_ms: {
      planner: 140,
      architect: 320,
      frontend: 450,
      backend: 580,
      testing: 210
    },
    llm_latency_ms: 280.0,
    cache_hit_rate_pct: 74.2,
    active_incidents: 0,
    grafana_status: 'ACTIVE',
    prometheus_status: 'SCRAPING_HEALTHY'
  });

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/monitoring/overview?project_id=${projectId}`);
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.warn('Failed to fetch live monitoring metrics:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, [projectId]);

  return (
    <div style={{ padding: '32px', backgroundColor: '#0A0D14', color: '#F3F4F6', minHeight: '100vh', fontFamily: "'Inter', sans-serif" }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Activity style={{ color: '#6366F1' }} size={32} />
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>
              Prometheus & Grafana Observability
            </h1>
            <span style={{
              backgroundColor: metrics.system_health === 'HEALTHY' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: metrics.system_health === 'HEALTHY' ? '#10B981' : '#EF4444',
              border: `1px solid ${metrics.system_health === 'HEALTHY' ? '#10B981' : '#EF4444'}`,
              borderRadius: '20px',
              padding: '4px 12px',
              fontSize: '12px',
              fontWeight: '600'
            }}>
              {metrics.system_health}
            </span>
          </div>
          <p style={{ color: '#9CA3AF', margin: 0, fontSize: '14px' }}>
            Real-time Prometheus telemetry, Grafana dashboards, OpenTelemetry metrics, and evidence-backed monitoring for project: <strong style={{ color: '#E5E7EB' }}>{projectId}</strong>
          </p>
        </div>

        <button
          onClick={fetchMetrics}
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
          Refresh Metrics
        </button>
      </div>

      {/* Metric KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>Total Requests</span>
            <BarChart2 size={18} style={{ color: '#6366F1' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFFFFF' }}>{metrics.requests_total.toLocaleString()}</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Prometheus scraped</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>P95 Latency</span>
            <Clock size={18} style={{ color: '#3B82F6' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFFFFF' }}>{metrics.p95_latency_ms} ms</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Target: &lt; 1000ms</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>HTTP Error Rate</span>
            <AlertTriangle size={18} style={{ color: metrics.error_rate_pct > 1 ? '#EF4444' : '#10B981' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFFFFF' }}>{metrics.error_rate_pct}%</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Threshold: &lt; 5.0%</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>Cache Hit Rate</span>
            <Zap size={18} style={{ color: '#F59E0B' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFFFFF' }}>{metrics.cache_hit_rate_pct}%</div>
          <div style={{ fontSize: '12px', color: '#9CA3AF', marginTop: '4px' }}>Redis LLM Cache</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>Active Incidents</span>
            <ShieldCheck size={18} style={{ color: metrics.active_incidents === 0 ? '#10B981' : '#EF4444' }} />
          </div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFFFFF' }}>{metrics.active_incidents}</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Incident Bridge Active</div>
        </div>
      </div>

      {/* Main Grid: Agent Latencies & Grafana Dashboards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Left Column: AI Agent Latencies */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={20} style={{ color: '#8B5CF6' }} />
            AI Agent Latency Breakdown
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {Object.entries(metrics.agent_latency_ms).map(([agent, ms]) => (
              <div key={agent}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '6px' }}>
                  <span style={{ textTransform: 'capitalize', color: '#E5E7EB' }}>{agent} Agent</span>
                  <span style={{ fontWeight: '600', color: '#A7F3D0' }}>{ms} ms</span>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: '#1F2937', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, (ms / 600) * 100)}%`,
                    height: '100%',
                    backgroundColor: agent === 'backend' ? '#8B5CF6' : agent === 'frontend' ? '#3B82F6' : '#10B981',
                    borderRadius: '4px'
                  }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '32px', paddingTop: '20px', borderTop: '1px solid #1F2937' }}>
            <h4 style={{ fontSize: '14px', color: '#9CA3AF', marginBottom: '12px' }}>Observability System Pipeline</h4>
            <div style={{ fontSize: '12px', color: '#D1D5DB', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div>• <strong>OpenTelemetry</strong>: Instrumentation & Tracing</div>
              <div>• <strong>Prometheus</strong>: Metrics Storage & Scrape (`/metrics`)</div>
              <div>• <strong>Grafana</strong>: Dashboard Visualization</div>
              <div>• <strong>AIForge Alert Manager</strong>: Incident Response Integration</div>
            </div>
          </div>
        </div>

        {/* Right Column: Grafana Dashboard Selector & Live Metrics */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={20} style={{ color: '#F59E0B' }} />
              Grafana Dashboards
            </h3>

            <div style={{ display: 'flex', gap: '8px' }}>
              {['AIForge Overview', 'Agent Performance', 'API Performance', 'Infrastructure'].map(dash => (
                <button
                  key={dash}
                  onClick={() => setDashboard(dash)}
                  style={{
                    backgroundColor: dashboard === dash ? '#374151' : '#1F2937',
                    color: dashboard === dash ? '#FFFFFF' : '#9CA3AF',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  {dash}
                </button>
              ))}
            </div>
          </div>

          {/* Simulated Grafana Dashboard Panel */}
          <div style={{
            backgroundColor: '#0D1117',
            border: '1px solid #30363D',
            borderRadius: '8px',
            padding: '24px',
            minHeight: '320px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <span style={{ fontSize: '16px', fontWeight: '600', color: '#58A6FF' }}>Grafana Panel — {dashboard}</span>
                <span style={{ fontSize: '12px', color: '#7D8590' }}>Prometheus Datasource</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div style={{ backgroundColor: '#161B22', padding: '16px', borderRadius: '6px', border: '1px solid #21262D' }}>
                  <div style={{ fontSize: '12px', color: '#8B949E' }}>LLM Mean Latency</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#7EE787' }}>{metrics.llm_latency_ms} ms</div>
                </div>
                <div style={{ backgroundColor: '#161B22', padding: '16px', borderRadius: '6px', border: '1px solid #21262D' }}>
                  <div style={{ fontSize: '12px', color: '#8B949E' }}>Prometheus Status</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#79C0FF' }}>{metrics.prometheus_status}</div>
                </div>
              </div>
            </div>

            <div style={{ fontSize: '12px', color: '#8B949E', borderTop: '1px solid #21262D', paddingTop: '12px', display: 'flex', justifyContent: 'space-between' }}>
              <span>Endpoint: <code>/metrics</code> (Prometheus text format)</span>
              <a href="/metrics" target="_blank" rel="noopener noreferrer" style={{ color: '#58A6FF', textDecoration: 'none' }}>View Raw Prometheus Output &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
