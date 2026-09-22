import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Server,
  Cpu,
  Activity,
  Zap,
  RotateCcw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  Clock,
  ShieldCheck,
  ChevronRight,
  X
} from 'lucide-react';

export default function KubernetesDashboardPage() {
  const { projectId = 'aiforge-demo' } = useParams();
  const [loading, setLoading] = useState(false);
  const [showScaleModal, setShowScaleModal] = useState(false);
  const [scalingComponent, setScalingComponent] = useState('backend');
  const [desiredReplicas, setDesiredReplicas] = useState(5);
  const [selectedPod, setSelectedPod] = useState(null);

  const [k8sData, setK8sData] = useState({
    connected: true,
    cluster_name: 'aiforge-prod-cluster',
    namespace: `aiforge-${projectId}`,
    k8s_version: 'v1.30.2',
    nodes_count: 3,
    cpu_usage_pct: 41.0,
    memory_usage_pct: 52.0,
    p95_latency_ms: 182.0,
    error_rate_pct: 0.08,
    frontend_pods: [
      { name: 'frontend-7d8a1', component: 'frontend', status: 'Running', ready: true, restarts: 0, cpu_percent: 12, memory_mb: 128, version: 'v1.5', image: 'aiforge/frontend:v1.5' },
      { name: 'frontend-7d8a2', component: 'frontend', status: 'Running', ready: true, restarts: 0, cpu_percent: 14, memory_mb: 132, version: 'v1.5', image: 'aiforge/frontend:v1.5' }
    ],
    backend_pods: [
      { name: 'backend-8f9b1', component: 'backend', status: 'Running', ready: true, restarts: 0, cpu_percent: 31, memory_mb: 284, version: 'v1.5', image: 'aiforge/backend:v1.5' },
      { name: 'backend-8f9b2', component: 'backend', status: 'Running', ready: true, restarts: 0, cpu_percent: 28, memory_mb: 276, version: 'v1.5', image: 'aiforge/backend:v1.5' },
      { name: 'backend-8f9b3', component: 'backend', status: 'Running', ready: true, restarts: 0, cpu_percent: 33, memory_mb: 290, version: 'v1.5', image: 'aiforge/backend:v1.5' }
    ],
    redis_pods: [
      { name: 'redis-1a2b1', component: 'redis', status: 'Running', ready: true, restarts: 0, cpu_percent: 8, memory_mb: 96, version: 'v7.2', image: 'redis:7.2-alpine' }
    ]
  });

  const [events, setEvents] = useState([
    { timestamp: new Date().toISOString(), component: 'backend', event_type: 'DeploymentUpdated', message: 'Updated backend image to v1.5', severity: 'INFO' },
    { timestamp: new Date().toISOString(), component: 'backend', event_type: 'ScalingOccurred', message: 'Scaled backend replicas from 3 to 5', severity: 'INFO' },
    { timestamp: new Date().toISOString(), component: 'frontend', event_type: 'PodStarted', message: 'Frontend pod frontend-7d8a1 initialized', severity: 'INFO' }
  ]);

  const fetchK8sStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/kubernetes/status?project_id=${projectId}`);
      if (res.ok) {
        const result = await res.json();
        setK8sData(result);
      }
      const evRes = await fetch(`/api/kubernetes/events?project_id=${projectId}`);
      if (evRes.ok) {
        const evs = await evRes.json();
        setEvents(evs);
      }
    } catch (e) {
      console.warn('Failed to fetch K8s status:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchK8sStatus();
  }, [projectId]);

  const handleDeploy = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/kubernetes/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, image_tag: 'v1.5' })
      });
      const data = await res.json();
      alert(`Deployment Result: ${data.message || data.reason}`);
      fetchK8sStatus();
    } catch (e) {
      alert(`Deploy Error: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/kubernetes/rollback?project_id=${projectId}`, { method: 'POST' });
      const data = await res.json();
      alert(`Rollback Result: ${data.message}`);
      fetchK8sStatus();
    } catch (e) {
      alert(`Rollback Error: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveScaling = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/kubernetes/scale', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          component: scalingComponent,
          current_replicas: k8sData[`${scalingComponent}_pods`]?.length || 3,
          desired_replicas: desiredReplicas,
          user_approved: true,
          reason: 'Manual scale request via K8s UI'
        })
      });
      const data = await res.json();
      alert(`Scaling Result: ${data.message}`);
      setShowScaleModal(false);
      fetchK8sStatus();
    } catch (e) {
      alert(`Scaling Error: ${e}`);
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
            <span style={{ fontSize: '32px' }}>☸</span>
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>
              Kubernetes Orchestration
            </h1>
            <span style={{
              backgroundColor: 'rgba(59, 130, 246, 0.15)',
              color: '#60A5FA',
              border: '1px solid #3B82F6',
              borderRadius: '20px',
              padding: '4px 12px',
              fontSize: '12px',
              fontWeight: '600'
            }}>
              CONNECTED ({k8sData.cluster_name})
            </span>
          </div>
          <p style={{ color: '#9CA3AF', margin: 0, fontSize: '14px' }}>
            Namespace: <code style={{ color: '#60A5FA', backgroundColor: '#111827', padding: '2px 8px', borderRadius: '4px' }}>{k8sData.namespace}</code> | Nodes: <strong style={{ color: '#E5E7EB' }}>{k8sData.nodes_count}</strong> | Version: <strong style={{ color: '#E5E7EB' }}>{k8sData.k8s_version}</strong>
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handleDeploy}
            disabled={loading}
            style={{
              backgroundColor: '#2563EB',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 18px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Zap size={16} /> Deploy Manifests
          </button>

          <button
            onClick={() => setShowScaleModal(true)}
            disabled={loading}
            style={{
              backgroundColor: '#6366F1',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 18px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Sliders size={16} /> Scale Replicas
          </button>

          <button
            onClick={handleRollback}
            disabled={loading}
            style={{
              backgroundColor: '#DC2626',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 18px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RotateCcw size={16} /> Rollback
          </button>
        </div>
      </div>

      {/* Cluster Card Component Status Grid */}
      <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px', marginBottom: '32px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Server size={20} style={{ color: '#3B82F6' }} />
          Cluster Services &amp; Pod Health
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {/* Frontend Service */}
          <div style={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', padding: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '16px', fontWeight: '600', color: '#FFFFFF' }}>Frontend</span>
              <span style={{ color: '#10B981', fontSize: '14px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={16} /> 2/2 🟢
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {k8sData.frontend_pods.map(pod => (
                <div
                  key={pod.name}
                  onClick={() => setSelectedPod(pod)}
                  style={{
                    backgroundColor: '#111827',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    justify: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <code>{pod.name}</code>
                  <span style={{ color: '#9CA3AF' }}>CPU: {pod.cpu_percent}% | RAM: {pod.memory_mb}MB</span>
                </div>
              ))}
            </div>
          </div>

          {/* Backend Service */}
          <div style={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', padding: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '16px', fontWeight: '600', color: '#FFFFFF' }}>Backend</span>
              <span style={{ color: '#10B981', fontSize: '14px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={16} /> 3/3 🟢
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {k8sData.backend_pods.map(pod => (
                <div
                  key={pod.name}
                  onClick={() => setSelectedPod(pod)}
                  style={{
                    backgroundColor: '#111827',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    justify: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <code>{pod.name}</code>
                  <span style={{ color: '#9CA3AF' }}>CPU: {pod.cpu_percent}% | RAM: {pod.memory_mb}MB</span>
                </div>
              ))}
            </div>
          </div>

          {/* Redis Service */}
          <div style={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', padding: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '16px', fontWeight: '600', color: '#FFFFFF' }}>Redis Cache</span>
              <span style={{ color: '#10B981', fontSize: '14px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={16} /> 1/1 🟢
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {k8sData.redis_pods.map(pod => (
                <div
                  key={pod.name}
                  onClick={() => setSelectedPod(pod)}
                  style={{
                    backgroundColor: '#111827',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    justify: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <code>{pod.name}</code>
                  <span style={{ color: '#9CA3AF' }}>CPU: {pod.cpu_percent}% | RAM: {pod.memory_mb}MB</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Telemetry Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginTop: '24px', paddingTop: '20px', borderTop: '1px solid #1F2937' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#9CA3AF' }}>Cluster CPU Usage</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#60A5FA' }}>{k8sData.cpu_usage_pct}%</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9CA3AF' }}>Cluster Memory Usage</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#A7F3D0' }}>{k8sData.memory_usage_pct}%</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9CA3AF' }}>P95 HTTP Latency</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#F59E0B' }}>{k8sData.p95_latency_ms} ms</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9CA3AF' }}>HTTP Error Rate</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#10B981' }}>{k8sData.error_rate_pct}%</div>
          </div>
        </div>
      </div>

      {/* Cluster Events Stream */}
      <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={20} style={{ color: '#10B981' }} />
          Sanitized Kubernetes Event Stream
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {events.map((ev, idx) => (
            <div key={idx} style={{ backgroundColor: '#161B22', border: '1px solid #21262D', borderRadius: '6px', padding: '12px', fontSize: '13px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <span style={{ backgroundColor: '#1F2937', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>{ev.component}</span>
                <strong style={{ color: '#E5E7EB' }}>{ev.event_type}</strong>
                <span style={{ color: '#9CA3AF' }}>{ev.message}</span>
              </div>
              <span style={{ fontSize: '11px', color: '#6B7280' }}>{ev.timestamp.slice(11, 19)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Scaling Modal */}
      {showScaleModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '12px', padding: '28px', maxWidth: '480px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', margin: 0, color: '#FFFFFF' }}>Horizontal Pod Autoscaling</h3>
              <X size={20} onClick={() => setShowScaleModal(false)} style={{ cursor: 'pointer', color: '#9CA3AF' }} />
            </div>

            <p style={{ fontSize: '14px', color: '#D1D5DB', marginBottom: '16px' }}>
              Performance Engineer observed elevated CPU (91%) and P95 latency (680ms). Recommend increasing replicas.
            </p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '13px', color: '#9CA3AF', display: 'block', marginBottom: '6px' }}>Component</label>
              <select value={scalingComponent} onChange={e => setScalingComponent(e.target.value)} style={{ width: '100%', backgroundColor: '#1F2937', color: '#FFFFFF', border: '1px solid #374151', borderRadius: '6px', padding: '8px' }}>
                <option value="backend">Backend Deployment</option>
                <option value="frontend">Frontend Deployment</option>
              </select>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ fontSize: '13px', color: '#9CA3AF', display: 'block', marginBottom: '6px' }}>Desired Replicas ({desiredReplicas})</label>
              <input type="range" min="1" max="10" value={desiredReplicas} onChange={e => setDesiredReplicas(Number(e.target.value))} style={{ width: '100%' }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button onClick={() => setShowScaleModal(false)} style={{ backgroundColor: '#1F2937', color: '#E5E7EB', border: 'none', borderRadius: '6px', padding: '10px 16px', cursor: 'pointer' }}>Cancel</button>
              <button onClick={handleApproveScaling} style={{ backgroundColor: '#6366F1', color: '#FFFFFF', border: 'none', borderRadius: '6px', padding: '10px 16px', fontWeight: '600', cursor: 'pointer' }}>Approve Scaling</button>
            </div>
          </div>
        </div>
      )}

      {/* Pod Detail Modal */}
      {selectedPod && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '12px', padding: '28px', maxWidth: '480px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', margin: 0, color: '#FFFFFF' }}>Pod Detail — {selectedPod.name}</h3>
              <X size={20} onClick={() => setSelectedPod(null)} style={{ cursor: 'pointer', color: '#9CA3AF' }} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px', color: '#D1D5DB' }}>
              <div>Status: <span style={{ color: '#10B981', fontWeight: '600' }}>{selectedPod.status}</span></div>
              <div>Image: <code>{selectedPod.image}</code></div>
              <div>Restarts: <strong>{selectedPod.restarts}</strong></div>
              <div>CPU Usage: <strong>{selectedPod.cpu_percent}%</strong></div>
              <div>Memory: <strong>{selectedPod.memory_mb} MB</strong></div>
            </div>

            <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setSelectedPod(null)} style={{ backgroundColor: '#1F2937', color: '#FFFFFF', border: 'none', borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
