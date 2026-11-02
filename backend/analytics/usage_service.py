"""
AIForge usage analytics, aggregated from what generation runs actually recorded: run outcomes
and the real token counts reported by Ollama (backend/telemetry/usage.py). Runs from before
token tracking existed have no usage and count as zero tokens.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

_logger = logging.getLogger("aiforge.analytics.service")


class UsageAnalyticsService:
    def get_platform_metrics(self) -> Dict[str, Any]:
        from backend.generation.store import global_generation_store
        runs = global_generation_store.list_all()

        totals = {"prompt_tokens": 0, "completion_tokens": 0, "llm_calls": 0, "cached_calls": 0, "cost_usd": 0.0}
        by_model: Dict[str, int] = defaultdict(int)
        by_agent: Dict[str, Dict[str, int]] = defaultdict(lambda: {"tokens": 0, "calls": 0})
        tracked_runs = 0

        today = datetime.now(timezone.utc).date()
        days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        daily = {d: {"runs": 0, "tokens": 0} for d in days}

        for run in runs:
            usage = run.get("usage") or {}
            run_tokens = usage.get("total_tokens", 0)
            if usage:
                tracked_runs += 1
                for key in totals:
                    totals[key] += usage.get(key, 0) or 0
                for agent, stats in (usage.get("by_agent") or {}).items():
                    tokens = stats.get("prompt_tokens", 0) + stats.get("completion_tokens", 0)
                    by_agent[agent]["tokens"] += tokens
                    by_agent[agent]["calls"] += stats.get("calls", 0)
                    by_model[stats.get("model") or "unknown"] += tokens
            try:
                created = datetime.fromisoformat(str(run.get("created_at"))).date()
            except (TypeError, ValueError):
                continue
            if created in daily:
                daily[created]["runs"] += 1
                daily[created]["tokens"] += run_tokens

        total_tokens = totals["prompt_tokens"] + totals["completion_tokens"]
        statuses = defaultdict(int)
        for run in runs:
            statuses[run.get("status") or "unknown"] += 1

        return {
            "summary": {
                "total_runs": len(runs),
                "completed_runs": statuses["completed"],
                "failed_runs": statuses["failed"] + statuses["cancelled"],
                "runs_with_token_data": tracked_runs,
                "total_tokens": total_tokens,
                "prompt_tokens": totals["prompt_tokens"],
                "completion_tokens": totals["completion_tokens"],
                "llm_calls": totals["llm_calls"],
                "cached_calls": totals["cached_calls"],
                "cost_usd": round(totals["cost_usd"], 4),
            },
            "model_distribution": [
                {"model": model, "tokens": tokens, "usage_pct": round(tokens / total_tokens * 100, 1) if total_tokens else 0}
                for model, tokens in sorted(by_model.items(), key=lambda kv: -kv[1])
            ],
            "top_agents": [
                {"agent": agent, **stats}
                for agent, stats in sorted(by_agent.items(), key=lambda kv: -kv[1]["tokens"])[:8]
            ],
            "daily_activity": [
                {"day": d.strftime("%a"), "date": d.isoformat(), **daily[d]} for d in days
            ],
        }


global_usage_service = UsageAnalyticsService()
