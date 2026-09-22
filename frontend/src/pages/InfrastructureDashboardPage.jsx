import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Building2,
  Cloud,
  Shield,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  Play,
  RotateCcw,
  RefreshCw,
  Eye,
  FileCode2,
  Lock,
  ChevronRight,
  X
} from 'lucide-react';

export default function InfrastructureDashboardPage() {
  const { projectId = 'aiforge-demo' } = useParams();
  const [provider, setProvider] = useState('AWS');
  const [environment, setEnvironment] = useState('production');
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [driftResult, setDriftResult] = useState(null);

  const [infraData, setInfraData] = useState({
    provider: 'AWS',
    environment: 'production',
    plan: {
      to_create_count: 8,
      to_modify_count: 2,
      to_destroy_count: 0,
      is_destructive: false,
      destructive_resources: [],
      items: [
        { resource_type: 'aws_vpc', resource_name: 'main_vpc', action: 'CREATE', is_destructive: false, reason: 'Private network VPC' },
        { resource_type: 'aws_db_instance', resource_name: 'postgres', action: 'CREATE', is_destructive: false, reason: 'Managed PostgreSQL Instance' },
        { resource_type: 'aws_elasticache_cluster', resource_name: 'redis', action: 'CREATE', is_destructive: false, reason: 'Managed ElastiCache Redis' },
        { resource_type: 'aws_lb', resource_name: 'alb', action: 'CREATE', is_destructive: false, reason: 'Application Load Balancer' },
        { resource_type: 'aws_ecs_service', resource_name: 'backend', action: 'MODIFY', is_destructive: false, reason: 'Backend task definition update' }
      ]
    },
    cost: {
      monthly_compute_usd: 48.0,
      monthly_database_usd: 35.0,
      monthly_redis_usd: 15.0,
      monthly_total_usd: 98.0,
      label: 'ESTIMATE AVAILABLE'
    },
    security: {
      passed: true,
      violations: [],
      warnings: []
    }
  });

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/infrastructure/overview?project_id=${projectId}&environment=${environment}&provider=${provider}`);
      if (res.ok) {
        const data = await res.json();
        setInfraData(data);
      }
    } catch (e) {
      console.warn('Failed to fetch infrastructure overview:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [projectId, provider, environment]);

  const handleApply = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/infrastructure/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, environment, user_approved: true })
      });
      const data = await res.json();
      alert(`Infrastructure Apply Result: ${data.message || data.status}`);
      fetchOverview();
    } catch (e) {
      alert(`Apply Error: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDetectDrift = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/infrastructure/drift?project_id=${projectId}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDriftResult(data);
      }
    } catch (e) {
      console.error('Drift detection error:', e);
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
            <Building2 style={{ color: '#F59E0B' }} size={32} />
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>
              Intelligent Infrastructure-as-Code Engine
            </h1>
            <span style={{
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              color: '#F59E0B',
              border: '1px solid #F59E0B',
              borderRadius: '20px',
              padding: '4px 12px',
              fontSize: '12px',
              fontWeight: '600'
            }}>
              TERRAFORM IaC
            </span>
          </div>
          <p style={{ color: '#9CA3AF', margin: 0, fontSize: '14px' }}>
            Provider: <strong style={{ color: '#E5E7EB' }}>{infraData.provider}</strong> | Environment: <strong style={{ color: '#E5E7EB' }}>{infraData.environment}</strong> | Project: <strong style={{ color: '#E5E7EB' }}>{projectId}</strong>
          </p>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select value={provider} onChange={e => setProvider(e.target.value)} style={{ backgroundColor: '#1F2937', color: '#FFFFFF', border: '1px solid #374151', borderRadius: '8px', padding: '10px 14px', fontSize: '13px' }}>
            <option value="AWS">Cloud Provider: AWS</option>
            <option value="Azure">Cloud Provider: Azure</option>
            <option value="GCP">Cloud Provider: GCP</option>
            <option value="Local">Cloud Provider: Local</option>
          </select>

          <select value={environment} onChange={e => setEnvironment(e.target.value)} style={{ backgroundColor: '#1F2937', color: '#FFFFFF', border: '1px solid #374151', borderRadius: '8px', padding: '10px 14px', fontSize: '13px' }}>
            <option value="production">Environment: Production</option>
            <option value="staging">Environment: Staging</option>
            <option value="development">Environment: Development</option>
          </select>

          <button onClick={handleApply} disabled={loading} style={{ backgroundColor: '#2563EB', color: '#FFFFFF', border: 'none', borderRadius: '8px', padding: '10px 18px', fontSize: '14px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Play size={16} /> Apply Plan
          </button>

          <button onClick={handleDetectDrift} disabled={loading} style={{ backgroundColor: '#1E293B', color: '#E2E8F0', border: '1px solid #334155', borderRadius: '8px', padding: '10px 18px', fontSize: '14px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={16} /> Detect Drift
          </button>
        </div>
      </div>

      {/* Destructive Warning Banner */}
      {infraData.plan.is_destructive && (
        <div style={{ backgroundColor: 'rgba(220, 38, 38, 0.15)', border: '1px solid #EF4444', borderRadius: '12px', padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle size={24} style={{ color: '#EF4444' }} />
          <div>
            <strong style={{ color: '#EF4444', fontSize: '15px' }}>⚠ HIGH-RISK DESTRUCTIVE CHANGE DETECTED</strong>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#FCA5A5' }}>
              Terraform plan will destroy sensitive resource(s): <code>{infraData.plan.destructive_resources.join(', ')}</code>. Explicit approval is required.
            </p>
          </div>
        </div>
      )}

      {/* Drift Detection Result Banner */}
      {driftResult && driftResult.has_drift && (
        <div style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', border: '1px solid #F59E0B', borderRadius: '12px', padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle size={24} style={{ color: '#F59E0B' }} />
          <div>
            <strong style={{ color: '#F59E0B', fontSize: '15px' }}>⚠ INFRASTRUCTURE DRIFT DETECTED</strong>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#FDE68A' }}>
              Resource <code>{driftResult.resource_name}</code> drift: Expected {driftResult.expected} vs Actual {driftResult.actual}. Cause: {driftResult.potential_cause}
            </p>
          </div>
        </div>
      )}

      {/* Top Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '6px' }}>Compute Resources</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#FFFFFF' }}>3 Instances</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>ECS / EC2 Private Subnet</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '6px' }}>Managed Database</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#60A5FA' }}>1 PostgreSQL</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Encrypted &amp; Non-Public</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '6px' }}>Managed Cache</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#A7F3D0' }}>1 ElastiCache Redis</div>
          <div style={{ fontSize: '12px', color: '#10B981', marginTop: '4px' }}>Port 6379 Private</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
          <div style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '6px' }}>Monthly Cost Estimate</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#F59E0B' }}>${infraData.cost.monthly_total_usd} / mo</div>
          <div style={{ fontSize: '12px', color: '#9CA3AF', marginTop: '4px' }}>{infraData.cost.label}</div>
        </div>
      </div>

      {/* Main Terraform Plan Table & Details */}
      <div style={{ backgroundColor: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCode2 size={20} style={{ color: '#F59E0B' }} />
            Terraform Execution Plan Summary
          </h3>
          <div style={{ display: 'flex', gap: '12px', fontSize: '13px' }}>
            <span style={{ backgroundColor: '#064E3B', color: '#A7F3D0', padding: '4px 10px', borderRadius: '6px', fontWeight: '600' }}>
              Create: {infraData.plan.to_create_count}
            </span>
            <span style={{ backgroundColor: '#78350F', color: '#FDE68A', padding: '4px 10px', borderRadius: '6px', fontWeight: '600' }}>
              Modify: {infraData.plan.to_modify_count}
            </span>
            <span style={{ backgroundColor: infraData.plan.to_destroy_count > 0 ? '#7F1D1D' : '#1F2937', color: infraData.plan.to_destroy_count > 0 ? '#FCA5A5' : '#9CA3AF', padding: '4px 10px', borderRadius: '6px', fontWeight: '600' }}>
              Destroy: {infraData.plan.to_destroy_count}
            </span>
          </div>
        </div>

        {/* Resources Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {infraData.plan.items.map((item, idx) => (
            <div key={idx} onClick={() => setSelectedItem(item)} style={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}>
              <div>
                <span style={{
                  backgroundColor: item.action === 'CREATE' ? 'rgba(34, 197, 94, 0.15)' : item.action === 'MODIFY' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: item.action === 'CREATE' ? '#22C55E' : item.action === 'MODIFY' ? '#F59E0B' : '#EF4444',
                  fontWeight: '700',
                  fontSize: '12px',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  marginRight: '12px'
                }}>
                  {item.action}
                </span>
                <code style={{ fontSize: '14px', color: '#FFFFFF', fontWeight: '600' }}>{item.resource_type}.{item.resource_name}</code>
                <span style={{ fontSize: '13px', color: '#9CA3AF', marginLeft: '12px' }}>{item.reason}</span>
              </div>
              <ChevronRight size={18} style={{ color: '#9CA3AF' }} />
            </div>
          ))}
        </div>
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '12px', padding: '28px', maxWidth: '520px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', margin: 0, color: '#FFFFFF' }}>Resource Details</h3>
              <X size={20} onClick={() => setSelectedItem(null)} style={{ cursor: 'pointer', color: '#9CA3AF' }} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px', color: '#D1D5DB' }}>
              <div>Resource Type: <code>{selectedItem.resource_type}</code></div>
              <div>Resource Name: <code>{selectedItem.resource_name}</code></div>
              <div>Planned Action: <strong style={{ color: selectedItem.action === 'CREATE' ? '#22C55E' : '#F59E0B' }}>{selectedItem.action}</strong></div>
              <div>Destructive Risk: <strong>{selectedItem.is_destructive ? 'HIGH (DESTRUCTIVE)' : 'LOW'}</strong></div>
              <div>Reason: <span>{selectedItem.reason}</span></div>
            </div>

            <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setSelectedItem(null)} style={{ backgroundColor: '#1F2937', color: '#FFFFFF', border: 'none', borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
