"""
AIForge Multi-Model Registry
============================
Registers available local and cloud LLM models with capabilities, speed, quality, coding scores, and cost metrics.
"""

from typing import Dict, Any

MODELS: Dict[str, Dict[str, Any]] = {
    "qwen": {
        "name": "Qwen 2.5 Coder",
        "provider": "ollama",
        "type": "local",
        "model_id": "qwen2.5-coder:latest",
        "speed": 10,
        "quality": 8,
        "coding": 9,
        "cost_per_1k_tokens": 0.0,
        "context_length": 32768,
        "supported_tasks": ["coding", "quick_fix", "refactoring", "unit_test"]
    },
    "deepseek": {
        "name": "DeepSeek R1 / Coder",
        "provider": "ollama",
        "type": "local",
        "model_id": "deepseek-coder:latest",
        "speed": 8,
        "quality": 9,
        "coding": 10,
        "cost_per_1k_tokens": 0.0,
        "context_length": 64000,
        "supported_tasks": ["coding", "reasoning", "complex_architecture", "security_audit"]
    },
    "llama3": {
        "name": "Llama 3.3 70B",
        "provider": "ollama",
        "type": "local",
        "model_id": "llama3.3:latest",
        "speed": 7,
        "quality": 9,
        "coding": 8,
        "cost_per_1k_tokens": 0.0,
        "context_length": 128000,
        "supported_tasks": ["explanation", "documentation", "general_reasoning"]
    },
    "gpt": {
        "name": "OpenAI GPT-4o",
        "provider": "openai",
        "type": "cloud",
        "model_id": "gpt-4o",
        "speed": 9,
        "quality": 10,
        "coding": 10,
        "cost_per_1k_tokens": 0.005,
        "context_length": 128000,
        "supported_tasks": ["complex_architecture", "multi_agent_review", "system_design"]
    },
    "claude": {
        "name": "Anthropic Claude 3.5 Sonnet",
        "provider": "anthropic",
        "type": "cloud",
        "model_id": "claude-3-5-sonnet-20241022",
        "speed": 8,
        "quality": 10,
        "coding": 10,
        "cost_per_1k_tokens": 0.003,
        "context_length": 200000,
        "supported_tasks": ["complex_architecture", "refactoring", "failover_fallback"]
    }
}
