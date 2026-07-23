"""
AIForge Unified LLM Model Router
================================
Coordinates task classification, model selection, parallel multi-model dispatch, response evaluation, failover retries, and historical learning.
"""

import logging
from typing import Dict, Any, List
from backend.llm.model_registry import MODELS
from backend.llm.model_memory import ModelMemory
from backend.llm.model_selector import ModelSelector
from backend.llm.model_manager import ModelManager
from backend.llm.response_evaluator import ResponseEvaluator
from backend.llm.benchmark import ModelBenchmarker

_logger = logging.getLogger("aiforge.llm")

class ModelRouter:
    """
    Unified LLM Orchestration layer for Day 71 Multi-LLM Collaboration.
    """

    def __init__(self) -> None:
        self.memory = ModelMemory()
        self.selector = ModelSelector(self.memory)
        self.evaluator = ResponseEvaluator()
        self.manager = ModelManager(self.evaluator)
        self.benchmarker = ModelBenchmarker()

    async def route_and_execute(self, prompt: str, strategy: str = "auto") -> Dict[str, Any]:
        """
        Routes and executes prompt based on selected strategy:
        Strategies: auto, fast, cheap, accurate, parallel, benchmark
        """
        _logger.info(f"ModelRouter received request with strategy='{strategy}'")

        if strategy == "parallel":
            # Run multi-model parallel evaluation
            res = await self.manager.execute_parallel(prompt, model_keys=["qwen", "deepseek", "gpt"])
            # Benchmark winner
            bench = self.benchmarker.benchmark_execution(res["winner"], latency=0.08)
            # Record in model memory
            self.memory.record_performance("coding", res["winner"], latency=0.08, quality_score=res["winner_score"], cost=bench["cost_usd"])
            res["benchmark"] = bench
            return res

        elif strategy == "benchmark":
            # Run benchmark comparison across Qwen, DeepSeek, GPT
            benchmarks = []
            for mk in ["qwen", "deepseek", "gpt"]:
                single_res = await self.manager._execute_single_model(mk, prompt)
                bench = self.benchmarker.benchmark_execution(mk, latency=single_res["latency"])
                benchmarks.append(bench)
            return {"strategy": "benchmark", "benchmarks": benchmarks}

        else:
            # Auto, Fast, Cheap, Accurate strategies
            selected_info = self.selector.select_model(prompt, strategy=strategy)
            model_key = selected_info["selected_key"]

            # Execute with automatic failover fallback
            exec_res = await self.manager.execute_with_failover(model_key, prompt)
            
            # Evaluate output quality
            eval_res = self.evaluator.evaluate_response(exec_res["response"])
            bench = self.benchmarker.benchmark_execution(exec_res["model_key"], latency=exec_res["latency"])

            # Save historical performance
            self.memory.record_performance(selected_info["task_type"], exec_res["model_key"], latency=exec_res["latency"], quality_score=eval_res["score"], cost=bench["cost_usd"])

            return {
                "strategy": strategy,
                "selected_model": exec_res["model_key"],
                "model_name": exec_res["model_name"],
                "provider": exec_res["type"],
                "task_type": selected_info["task_type"],
                "response": exec_res["response"],
                "quality_score": eval_res["score"],
                "retries": exec_res.get("retries_count", 0),
                "benchmark": bench
            }

global_model_router = ModelRouter()
