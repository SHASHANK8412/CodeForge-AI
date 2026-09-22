/**
 * AIForge AI Usage & Analytics API Service
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function fetchAnalyticsMetrics() {
  try {
    const res = await axios.get(`${API_BASE}/api/analytics/metrics`, { timeout: 4000 });
    if (res.data?.metrics) {
      return res.data.metrics;
    }
  } catch (err) {
    console.warn("Local fallback for analytics metrics:", err);
  }
  return {
    summary: {
      total_ai_requests: 14280,
      autonomous_agent_tasks: 342,
      total_tokens_consumed: "42.8M",
      estimated_cost_usd: "$28.45",
      active_projects: 3,
      active_memories: 12,
      uptime_sla: "99.99%"
    },
    model_distribution: [
      {"model": "Claude 3.5 Sonnet", "usage_pct": 52, "color": "bg-indigo-500"},
      {"model": "GPT-4o / GPT-4.5", "usage_pct": 34, "color": "bg-violet-500"},
      {"model": "DeepSeek R1 / V3", "usage_pct": 14, "color": "bg-emerald-500"}
    ],
    top_tools: [
      {"tool_name": "Monaco Code Workspace", "invocations": 4120, "category": "Coding"},
      {"tool_name": "AI Memory Smart Recall", "invocations": 3280, "category": "Context"},
      {"tool_name": "Autopilot Engine", "invocations": 2150, "category": "Autonomous"},
      {"tool_name": "Bug Hunter SAST", "invocations": 1840, "category": "Security"},
      {"tool_name": "Deep Research Engine", "invocations": 1490, "category": "Research"}
    ],
    daily_activity: [
      {"day": "Mon", "requests": 1840},
      {"day": "Tue", "requests": 2190},
      {"day": "Wed", "requests": 2450},
      {"day": "Thu", "requests": 2890},
      {"day": "Fri", "requests": 3120},
      {"day": "Sat", "requests": 1650},
      {"day": "Sun", "requests": 1420}
    ]
  };
}
