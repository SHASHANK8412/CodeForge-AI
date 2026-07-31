import React, { useState } from 'react';
import { FaSitemap, FaDollarSign, FaRocket, FaShieldAlt, FaLayerGroup, FaServer } from 'react-icons/fa';

export default function ArchitectureOptimizerDashboard() {
  const [targetUsers, setTargetUsers] = useState(10000000);
  const [archReport, setArchReport] = useState({
    recommended_stack: {
      frontend: 'React 18 / Next.js SPA',
      backend: 'FastAPI Async Microservices',
      database: 'PostgreSQL + PgBouncer',
      cache: 'Redis Enterprise Cluster',
      storage: 'AWS S3 / Cloudflare R2',
      queue: 'RabbitMQ / Apache Kafka',
      authentication: 'Stateless OAuth2 + JWT',
      deployment: 'Docker + Kubernetes (EKS)'
    },
    cost_estimation: {
      total_monthly_usd: 3150.0,
      breakdown_usd: { compute_kubernetes: 1200, database_postgresql: 850, cache_redis: 350, object_storage_s3: 250, cdn_bandwidth: 450 }
    },
    scalability_analysis: {
      expected_throughput_rps: 8383,
      max_capacity_rps: 41915,
      scalability_score: 96.5,
      security_score: 94.0
    },
    trade_offs: [
      'PostgreSQL chosen over MongoDB for ACID transaction safety.',
      'FastAPI chosen for async throughput and AI integration.',
      'Redis cluster offloads 85% of read queries from database.'
    ]
  });

  const [loading, setLoading] = useState(false);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/architecture/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Food Delivery Platform', target_users: targetUsers })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.architecture) setArchReport(data.architecture);
      }
    } catch (err) {
      console.log('Using fallback architecture data:', err);
    } finally {
      setLoading(false);
    }
  };

  const stack = archReport.recommended_stack || {};
  const cost = archReport.cost_estimation || {};
  const scale = archReport.scalability_analysis || {};

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaSitemap className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-bold tracking-wide text-white uppercase">
              AI Architecture Optimizer (Day 49)
            </h3>
            <p className="text-[11px] text-slate-400">Multi-tier tech stack recommendations, cost estimation & scalability trade-offs</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={targetUsers}
            onChange={(e) => setTargetUsers(Number(e.target.value))}
            className="bg-slate-950 border border-slate-800 text-xs px-2.5 py-1.5 rounded text-slate-200 outline-none"
          >
            <option value={100000}>100K Users</option>
            <option value={1000000}>1M Users</option>
            <option value={10000000}>10M Users</option>
          </select>

          <button
            onClick={handleOptimize}
            disabled={loading}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-xs px-3.5 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow"
          >
            <FaRocket className={loading ? 'animate-spin' : ''} />
            {loading ? 'Optimizing Architecture...' : 'Analyze Architecture'}
          </button>
        </div>
      </div>

      {/* Tech Stack Topology Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5 font-mono text-xs">
        {Object.entries(stack).map(([layer, tech], idx) => (
          <div key={idx} className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span className="text-[9px] text-cyan-400 uppercase font-bold block mb-1">{layer}</span>
            <span className="text-[11px] font-bold text-white block">{tech}</span>
          </div>
        ))}
      </div>

      {/* Cost & Scalability Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5 font-mono text-xs">
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Estimated Cloud Cost</span>
          <span className="text-2xl font-extrabold text-emerald-400">${cost.total_monthly_usd || 3150} / mo</span>
          <span className="text-[9px] text-slate-500 block mt-1">Scale: {(targetUsers / 1000000).toFixed(0)}M Target Users</span>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Target Throughput</span>
          <span className="text-2xl font-extrabold text-cyan-400">{scale.expected_throughput_rps || 8383} RPS</span>
          <span className="text-[9px] text-slate-500 block mt-1">Max Cap: {scale.max_capacity_rps || 41915} RPS</span>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Architecture Score</span>
          <span className="text-2xl font-extrabold text-purple-400">{scale.scalability_score || 96.5}%</span>
          <span className="text-[9px] text-slate-500 block mt-1">Security Score: {scale.security_score || 94}%</span>
        </div>
      </div>
    </div>
  );
}
