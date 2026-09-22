import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  Cpu,
  Database,
  Server,
  Zap,
  Eye,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  GitBranch,
  Shield,
  Target,
  Activity,
  Cloud,
  HardDrive,
} from "lucide-react";

const PROVIDERS = ["AWS", "AZURE", "GCP", "LOCAL"];
const ENVIRONMENTS = ["production", "staging", "dev"];
const POLICIES = ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"];

const PROVIDER_COLORS = {
  AWS: "#FF9900",
  AZURE: "#0078D4",
  GCP: "#4285F4",
  LOCAL: "#6366F1",
};

function StatusBadge({ status }) {
  const colors = {
    OK: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    WARNING: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    CRITICAL: "bg-red-500/20 text-red-300 border-red-500/40",
    ESTIMATED: "bg-blue-500/20 text-blue-300 border-blue-500/40",
    FORECAST: "bg-violet-500/20 text-violet-300 border-violet-500/40",
    HIGH: "bg-red-500/20 text-red-300 border-red-500/40",
    MEDIUM: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    LOW: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  };
  return (
    <span
      className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${colors[status] || "bg-slate-700 text-slate-300 border-slate-600"}`}
    >
      {status}
    </span>
  );
}

function CostCard({ label, value, icon: Icon, color, note }) {
  return (
    <div
      className="rounded-xl p-4 border border-slate-700/60 bg-slate-800/60 hover:bg-slate-800/90 transition-all duration-200"
      style={{ borderLeftColor: color, borderLeftWidth: 3 }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">
          {label}
        </span>
        <Icon size={16} style={{ color }} />
      </div>
      <div className="text-2xl font-bold text-white">${value.toFixed(0)}</div>
      {note && <div className="text-xs text-slate-500 mt-1">{note}</div>}
    </div>
  );
}

function BudgetBar({ budget }) {
  if (!budget) return null;
  const pct = Math.min(budget.percent_used || 0, 100);
  const color =
    budget.status === "CRITICAL"
      ? "#ef4444"
      : budget.status === "WARNING"
        ? "#f59e0b"
        : "#10b981";
  return (
    <div className="rounded-xl p-5 border border-slate-700/60 bg-slate-800/60">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-slate-400" />
          <span className="text-sm font-semibold text-white">Budget Status</span>
        </div>
        <StatusBadge status={budget.status} />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span>
          ${(budget.current_estimate || 0).toFixed(0)} of ${(budget.monthly_limit || 0).toFixed(0)}
        </span>
        <span>{pct.toFixed(1)}% used</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
        <div
          className="h-3 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      {budget.status !== "OK" && (
        <div className="mt-2 text-xs text-amber-400">
          ⚠ {budget.status === "CRITICAL" ? "Budget exceeded. Approval required before adding new resources." : "Approaching budget limit. Review infrastructure spend."}
        </div>
      )}
    </div>
  );
}

function WasteCard({ item, onCreatePlan }) {
  return (
    <div className="rounded-xl p-4 border border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/10 transition-all">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle size={15} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <div className="text-sm font-semibold text-white">{item.resource_name}</div>
            <div className="text-xs text-slate-400 mt-0.5">{item.resource_type}</div>
          </div>
        </div>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 flex-shrink-0">
          {item.waste_label}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="bg-slate-800/60 rounded-lg p-2">
          <div className="text-slate-500">Allocated</div>
          <div className="text-white font-medium">{item.allocated}</div>
        </div>
        <div className="bg-slate-800/60 rounded-lg p-2">
          <div className="text-slate-500">Observed Avg</div>
          <div className="text-white font-medium">{item.observed_average}</div>
        </div>
      </div>
      <div className="mt-3 text-xs text-slate-400 leading-relaxed">{item.recommendation}</div>
      <div className="mt-3 flex gap-2">
        <button
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
          onClick={() => alert("Analysis coming soon")}
        >
          Analyze
        </button>
        <button
          className="text-xs px-3 py-1.5 rounded-lg bg-violet-600/30 hover:bg-violet-600/50 text-violet-300 border border-violet-500/40 transition-colors flex items-center gap-1"
          onClick={() => onCreatePlan(item)}
        >
          <GitBranch size={11} />
          Create Terraform Plan
        </button>
      </div>
    </div>
  );
}

function RecommendationCard({ rec }) {
  return (
    <div className="rounded-xl p-4 border border-slate-700/60 bg-slate-800/40 hover:bg-slate-800/70 transition-all">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <DollarSign size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
          <span className="text-sm font-semibold text-white">{rec.title}</span>
        </div>
        <StatusBadge status={rec.risk} />
      </div>
      <p className="text-xs text-slate-400 leading-relaxed mb-3">{rec.description}</p>
      <div className="flex items-center gap-3 text-xs text-slate-500">
        <span>Saving: <span className="text-slate-300">{rec.potential_saving}</span></span>
        <span>•</span>
        <span>Evolution: <span className="text-slate-300">{rec.evolution_priority}</span></span>
        {rec.requires_approval && <span className="text-amber-400">Requires Approval</span>}
      </div>
    </div>
  );
}

function TrendChart({ trend }) {
  if (!trend?.trend?.length) return null;
  const max = Math.max(...trend.trend.map((t) => t.estimate));
  return (
    <div className="rounded-xl p-5 border border-slate-700/60 bg-slate-800/60">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={15} className="text-indigo-400" />
        <span className="text-sm font-semibold text-white">Cost Trend</span>
        <StatusBadge status="ESTIMATED" />
      </div>
      <div className="flex items-end gap-3 h-28">
        {trend.trend.map((t, i) => {
          const pct = max > 0 ? (t.estimate / max) * 100 : 0;
          const isLast = i === trend.trend.length - 1;
          return (
            <div key={i} className="flex flex-col items-center gap-1 flex-1">
              <div className="text-xs text-slate-400">${t.estimate.toFixed(0)}</div>
              <div
                className="w-full rounded-t-md transition-all duration-500"
                style={{
                  height: `${pct}%`,
                  minHeight: 8,
                  background: isLast
                    ? "linear-gradient(180deg,#6366f1,#4338ca)"
                    : "linear-gradient(180deg,#334155,#1e293b)",
                }}
              />
              <div className="text-xs text-slate-500 truncate w-full text-center">{t.month.slice(0, 3)}</div>
            </div>
          );
        })}
      </div>
      <div className="mt-2 text-xs text-slate-600">{trend.note}</div>
    </div>
  );
}

function ForecastPanel({ forecast }) {
  if (!forecast) return null;
  if (!forecast.forecast_available) {
    return (
      <div className="rounded-xl p-5 border border-slate-700/60 bg-slate-800/60">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp size={15} className="text-slate-500" />
          <span className="text-sm font-semibold text-slate-400">Forecast</span>
        </div>
        <p className="text-sm text-slate-500">FORECAST UNAVAILABLE</p>
      </div>
    );
  }
  return (
    <div className="rounded-xl p-5 border border-violet-500/30 bg-violet-500/5">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={15} className="text-violet-400" />
        <span className="text-sm font-semibold text-white">Cost Forecast</span>
        <StatusBadge status="FORECAST" />
      </div>
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">7 Days</div>
          <div className="text-lg font-bold text-white">${forecast.next_7_days?.toFixed(0)}</div>
        </div>
        <div className="text-center border-x border-slate-700">
          <div className="text-xs text-slate-500 mb-1">30 Days</div>
          <div className="text-lg font-bold text-violet-300">${forecast.next_30_days?.toFixed(0)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">90 Days</div>
          <div className="text-lg font-bold text-white">${forecast.next_90_days?.toFixed(0)}</div>
        </div>
      </div>
      {forecast.trend_pct != null && (
        <div className="text-xs text-violet-400 flex items-center gap-1">
          <TrendingUp size={11} />
          Projected growth: +{forecast.trend_pct}%/month
        </div>
      )}
      <div className="mt-2 text-xs text-slate-600 leading-relaxed">{forecast.note}</div>
    </div>
  );
}

function ArchComparisonTable({ data }) {
  if (!data?.options?.length) return null;
  const labelColor = { LOW: "text-emerald-400", MEDIUM: "text-amber-400", HIGH: "text-red-400" };
  return (
    <div className="rounded-xl p-5 border border-slate-700/60 bg-slate-800/60">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 size={15} className="text-sky-400" />
        <span className="text-sm font-semibold text-white">Architecture Comparison</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-700">
              {["Architecture", "Cost", "Complexity", "Scalability", "Reliability", "Est. $/mo"].map((h) => (
                <th key={h} className="text-left py-2 px-2 text-slate-400 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.options.map((opt, i) => (
              <tr
                key={i}
                className={`border-b border-slate-700/40 hover:bg-slate-700/20 transition-colors ${data.recommended === opt.name ? "bg-emerald-500/5" : ""}`}
              >
                <td className="py-2.5 px-2 text-white font-medium">
                  {opt.name}
                  {data.recommended === opt.name && (
                    <span className="ml-2 text-xs text-emerald-400">★ Recommended</span>
                  )}
                </td>
                <td className={`py-2.5 px-2 font-semibold ${labelColor[opt.cost_label]}`}>{opt.cost_label}</td>
                <td className={`py-2.5 px-2 ${labelColor[opt.complexity_label]}`}>{opt.complexity_label}</td>
                <td className={`py-2.5 px-2 ${labelColor[opt.scalability_label]}`}>{opt.scalability_label}</td>
                <td className={`py-2.5 px-2 ${labelColor[opt.reliability_label]}`}>{opt.reliability_label}</td>
                <td className="py-2.5 px-2 text-slate-300">${opt.estimated_monthly_cost.toFixed(0)} <span className="text-slate-600">est.</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.reasoning && (
        <div className="mt-3 p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg text-xs text-slate-300 leading-relaxed">
          <span className="font-semibold text-emerald-400">AIForge: </span>
          {data.reasoning}
        </div>
      )}
      <div className="mt-2 text-xs text-slate-600">{data.note}</div>
    </div>
  );
}

function KubernetesPanel({ data }) {
  if (!data) return null;
  return (
    <div
      className={`rounded-xl p-5 border ${data.is_justified ? "border-emerald-500/30 bg-emerald-500/5" : "border-amber-500/30 bg-amber-500/5"}`}
    >
      <div className="flex items-center gap-2 mb-3">
        <Server size={15} className={data.is_justified ? "text-emerald-400" : "text-amber-400"} />
        <span className="text-sm font-semibold text-white">Kubernetes Justification</span>
        <StatusBadge status={data.is_justified ? "OK" : "WARNING"} />
      </div>
      <p className="text-sm font-medium text-white mb-3">{data.recommendation}</p>
      {!data.is_justified && data.alternative && (
        <div className="text-xs text-amber-300 mb-3">
          💡 Alternative: {data.alternative}
        </div>
      )}
      <ul className="text-xs text-slate-400 space-y-1">
        {(data.factors || []).map((f, i) => (
          <li key={i} className="flex items-start gap-1.5">
            <ChevronRight size={10} className="mt-0.5 flex-shrink-0" />
            {f}
          </li>
        ))}
      </ul>
      <div className="mt-2 text-xs text-slate-600">{data.note}</div>
    </div>
  );
}

export default function FinOpsDashboardPage() {
  const { projectId = "aiforge-demo" } = useParams();
  const [provider, setProvider] = useState("AWS");
  const [environment, setEnvironment] = useState("production");
  const [policy, setPolicy] = useState("BALANCED");
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState(null);
  const [k8sData, setK8sData] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState(null);
  const [copilotLoading, setCopilotLoading] = useState(false);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const [ovRes, k8sRes, cmpRes] = await Promise.all([
        fetch(`/api/finops/overview?project_id=${projectId}&provider=${provider}&environment=${environment}`),
        fetch(`/api/finops/kubernetes?project_id=${projectId}&service_count=2&avg_rps=25`),
        fetch(`/api/finops/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_id: projectId, question: "Which architecture should I choose?" }),
        }),
      ]);
      setOverview(await ovRes.json());
      setK8sData(await k8sRes.json());
      setComparison(await cmpRes.json());
    } catch (err) {
      console.error("FinOps fetch error", err);
    } finally {
      setLoading(false);
    }
  };

  const askCopilot = async () => {
    if (!copilotQuestion.trim()) return;
    setCopilotLoading(true);
    try {
      const res = await fetch("/api/finops/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, question: copilotQuestion }),
      });
      setCopilotAnswer(await res.json());
    } catch {
      setCopilotAnswer({ answer: "Unable to reach FinOps Copilot." });
    } finally {
      setCopilotLoading(false);
    }
  };

  useEffect(() => { fetchOverview(); }, [projectId, provider, environment]);

  const bd = overview?.breakdown;
  const budget = overview?.budget;
  const forecast = overview?.forecast;
  const waste = overview?.waste || [];
  const recs = overview?.recommendations || [];
  const trend = overview?.trend;

  const providerColor = PROVIDER_COLORS[provider] || "#6366f1";

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: providerColor }} />
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">AI FinOps Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Infrastructure Cost Intelligence</h1>
          <p className="text-sm text-slate-400 mt-1">Project: <span className="text-slate-200">{projectId}</span></p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Provider selector */}
          <div className="flex gap-1 p-1 bg-slate-800 rounded-lg">
            {PROVIDERS.map((p) => (
              <button
                key={p}
                onClick={() => setProvider(p)}
                className={`text-xs px-2.5 py-1.5 rounded-md transition-all font-medium ${provider === p ? "bg-slate-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                {p}
              </button>
            ))}
          </div>
          {/* Environment selector */}
          <div className="flex gap-1 p-1 bg-slate-800 rounded-lg">
            {ENVIRONMENTS.map((e) => (
              <button
                key={e}
                onClick={() => setEnvironment(e)}
                className={`text-xs px-2.5 py-1.5 rounded-md transition-all capitalize ${environment === e ? "bg-slate-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                {e}
              </button>
            ))}
          </div>
          <button
            onClick={fetchOverview}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Estimated Notice */}
      <div className="mb-5 flex items-center gap-2 text-xs text-blue-300 bg-blue-500/10 border border-blue-500/30 rounded-xl px-4 py-2.5">
        <Eye size={13} />
        All cost figures are <strong>ESTIMATED</strong> based on published cloud pricing ({provider}, 2024-Q4). Not actual billing data.
      </div>

      {loading && !overview && (
        <div className="flex items-center justify-center h-40">
          <RefreshCw size={24} className="animate-spin text-slate-500" />
        </div>
      )}

      {bd && (
        <>
          {/* Cost Breakdown Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
            <CostCard label="Total / Month" value={bd.total_monthly_estimate} icon={DollarSign} color={providerColor} note="ESTIMATED" />
            <CostCard label="Compute" value={bd.compute || 0} icon={Cpu} color="#6366f1" />
            <CostCard label="Database" value={bd.database || 0} icon={Database} color="#0ea5e9" />
            <CostCard label="Redis" value={bd.redis || 0} icon={Zap} color="#f59e0b" />
            <CostCard label="Networking" value={bd.networking || 0} icon={Activity} color="#10b981" />
            <CostCard label="Monitoring" value={bd.monitoring || 0} icon={BarChart3} color="#a78bfa" />
          </div>

          {/* Budget + Trend */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
            <BudgetBar budget={budget} />
            <ForecastPanel forecast={forecast} />
          </div>

          {/* Trend Chart */}
          {trend && (
            <div className="mb-5">
              <TrendChart trend={trend} />
            </div>
          )}
        </>
      )}

      {/* Waste Detection */}
      {waste.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={15} className="text-amber-400" />
            <span className="text-sm font-semibold text-white">Potential Waste ({waste.length})</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {waste.map((w, i) => (
              <WasteCard key={i} item={w} onCreatePlan={(item) => alert(`Creating Terraform plan for ${item.resource_name}…`)} />
            ))}
          </div>
        </div>
      )}

      {/* Rightsizing Recommendations */}
      {recs.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Shield size={15} className="text-emerald-400" />
              <span className="text-sm font-semibold text-white">Recommendations ({recs.length})</span>
            </div>
            <div className="flex gap-1 p-1 bg-slate-800 rounded-lg">
              {POLICIES.map((p) => (
                <button
                  key={p}
                  onClick={() => setPolicy(p)}
                  className={`text-xs px-2 py-1 rounded-md transition-all ${policy === p ? "bg-slate-600 text-white" : "text-slate-400 hover:text-white"}`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recs.map((r) => (
              <RecommendationCard key={r.id} rec={r} />
            ))}
          </div>
        </div>
      )}

      {/* Architecture Comparison */}
      {comparison && (
        <div className="mb-5">
          <ArchComparisonTable data={comparison} />
        </div>
      )}

      {/* Kubernetes Justification */}
      {k8sData && (
        <div className="mb-5">
          <KubernetesPanel data={k8sData} />
        </div>
      )}

      {/* FinOps Copilot */}
      <div className="rounded-xl p-5 border border-slate-700/60 bg-slate-800/60 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Cloud size={15} className="text-indigo-400" />
          <span className="text-sm font-semibold text-white">FinOps Copilot</span>
        </div>
        <div className="flex gap-2">
          <input
            value={copilotQuestion}
            onChange={(e) => setCopilotQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && askCopilot()}
            placeholder="e.g. Why did our cost increase? Do we need Kubernetes? Can we reduce cost?"
            className="flex-1 text-sm bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={askCopilot}
            disabled={copilotLoading || !copilotQuestion.trim()}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-sm font-medium transition-colors"
          >
            {copilotLoading ? "…" : "Ask"}
          </button>
        </div>
        {copilotAnswer && (
          <div className="mt-4 p-4 bg-slate-900/60 rounded-xl border border-slate-700/40">
            <div className="flex items-center gap-1.5 mb-2">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
              <span className="text-xs font-semibold text-indigo-400">AIForge FinOps</span>
            </div>
            <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
              {copilotAnswer.answer}
            </p>
          </div>
        )}
        {/* Sample questions */}
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            "What does this architecture cost?",
            "Why did infrastructure cost increase?",
            "Do we need Kubernetes?",
            "Can we reduce cost?",
            "Forecast next month's cost",
          ].map((q) => (
            <button
              key={q}
              onClick={() => { setCopilotQuestion(q); }}
              className="text-xs px-2.5 py-1 rounded-full bg-slate-700/60 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors border border-slate-700/60"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Security Guardrail Notice */}
      <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/40 flex items-start gap-3">
        <Shield size={15} className="text-emerald-400 mt-0.5 flex-shrink-0" />
        <div className="text-xs text-slate-400 leading-relaxed">
          <span className="font-semibold text-emerald-400">Security Guardrails Active</span> — FinOps optimizations never disable encryption, remove authentication, open databases publicly, disable audit logging, or reduce backups below policy. Security and reliability always take precedence over cost reduction.
        </div>
      </div>
    </div>
  );
}
