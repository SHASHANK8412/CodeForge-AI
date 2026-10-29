"""
AIForge Benchmark Lab — Configuration Manager
=============================================
Manages discovery of models, configuration validation, dynamic Ollama detection,
and safe credential isolation.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from backend.benchmark_lab.models import (
    BenchmarkConfig,
    WorkflowType,
)

_logger = logging.getLogger("aiforge.benchmark_lab.config")


class ConfigurationManager:
    """
    Manages benchmark configurations and hardware/model availability discovery.
    """

    def __init__(self) -> None:
        self._saved_configs: Dict[str, BenchmarkConfig] = {}
        self._initialize_defaults()

    def discover_installed_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Dynamically queries local Ollama daemon and checks configured remote providers.
        NEVER exposes secret tokens or API keys.
        """
        models: List[Dict[str, Any]] = []

        # 1. Discover local Ollama models
        try:
            from ollama import Client
            client = Client(timeout=5.0)
            listing = client.list()
            entries = listing.get("models", []) if isinstance(listing, dict) else getattr(listing, "models", [])

            for entry in entries:
                name = entry.get("model") or entry.get("name") if isinstance(entry, dict) else getattr(entry, "model", None)
                if not name:
                    continue

                details = entry.get("details", {}) if isinstance(entry, dict) else getattr(entry, "details", None)
                param_size = getattr(details, "parameter_size", "") if details else ""
                family = getattr(details, "family", "") if details else ""

                # Distinguish embedding models
                is_embedding = any(k in name.lower() for k in ("embed", "minilm", "bge", "bert"))

                models.append({
                    "name": name,
                    "provider": "Ollama",
                    "type": "local",
                    "parameter_size": param_size,
                    "family": family,
                    "is_embedding": is_embedding,
                    "is_available": True,
                    "status": "Installed"
                })
        except Exception as e:
            _logger.warning(f"Could not reach Ollama client during model discovery: {e}")

        # 2. Check remote providers WITHOUT leaking credentials
        has_openai = bool(os.getenv("OPENAI_API_KEY", "").strip())
        models.append({
            "name": "gpt-4o",
            "provider": "OpenAI",
            "type": "remote",
            "parameter_size": "N/A",
            "family": "gpt",
            "is_embedding": False,
            "is_available": has_openai,
            "status": "Configured" if has_openai else "Missing API Key"
        })

        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
        models.append({
            "name": "claude-3-5-sonnet-20241022",
            "provider": "Anthropic",
            "type": "remote",
            "parameter_size": "N/A",
            "family": "claude",
            "is_embedding": False,
            "is_available": has_anthropic,
            "status": "Configured" if has_anthropic else "Missing API Key"
        })

        return models

    def is_model_available(self, model_name: str, provider: str = "Ollama", models: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Determines whether a model is genuinely available in this environment."""
        if models is None:
            models = self.discover_installed_models()
        for m in models:
            if m["name"].lower() == model_name.lower() and m["provider"].lower() == provider.lower():
                return m["is_available"]
            # Fallback check for tag matching (e.g., qwen2.5-coder vs qwen2.5-coder:latest)
            if provider.lower() == "ollama" and m["provider"].lower() == "ollama":
                base_requested = model_name.split(":")[0].lower()
                base_found = m["name"].split(":")[0].lower()
                if base_requested == base_found:
                    return m["is_available"]
        return False

    def validate_configuration(self, config: BenchmarkConfig, models: Optional[List[Dict[str, Any]]] = None) -> BenchmarkConfig:
        """Validates configuration parameters and assigns genuine availability status."""
        is_avail = self.is_model_available(config.model_name, config.provider, models=models)
        config.is_available = is_avail
        if not is_avail:
            config.availability_reason = (
                f"Model '{config.model_name}' on provider '{config.provider}' is not installed or available."
            )
        else:
            config.availability_reason = None

        if config.timeout_seconds <= 0:
            config.timeout_seconds = 30.0
        if config.max_repair_attempts < 0:
            config.max_repair_attempts = 0

        return config

    def save_configuration(self, config: BenchmarkConfig) -> BenchmarkConfig:
        validated = self.validate_configuration(config)
        self._saved_configs[validated.id] = validated
        return validated

    def get_configuration(self, config_id: str) -> Optional[BenchmarkConfig]:
        return self._saved_configs.get(config_id)

    def list_configurations(self) -> List[BenchmarkConfig]:
        # Single discovery pass for all configurations
        models = self.discover_installed_models()
        return [self.validate_configuration(c, models=models) for c in self._saved_configs.values()]

    def _initialize_defaults(self) -> None:
        """Populates sensible default configurations reflecting real environment options."""
        default_configs = [
            BenchmarkConfig(
                id="cfg_qwen_coder_direct",
                name="Qwen 2.5 Coder (Direct Generation)",
                provider="Ollama",
                model_name="qwen2.5-coder:latest",
                prompt_version="v1.0",
                workflow=WorkflowType.DIRECT,
                review_enabled=False,
                testing_enabled=False,
                max_repair_attempts=0,
                timeout_seconds=45.0,
                temperature=0.1
            ),
            BenchmarkConfig(
                id="cfg_qwen_coder_planner_coder",
                name="Qwen 2.5 Coder (Planner → Coder)",
                provider="Ollama",
                model_name="qwen2.5-coder:latest",
                prompt_version="v1.0",
                workflow=WorkflowType.PLANNER_CODER,
                review_enabled=False,
                testing_enabled=False,
                max_repair_attempts=0,
                timeout_seconds=60.0,
                temperature=0.2
            ),
            BenchmarkConfig(
                id="cfg_qwen_coder_reviewed",
                name="Qwen 2.5 Coder (Planner → Coder → Reviewer)",
                provider="Ollama",
                model_name="qwen2.5-coder:latest",
                prompt_version="v1.0",
                workflow=WorkflowType.PLANNER_CODER_REVIEWER,
                review_enabled=True,
                testing_enabled=True,
                max_repair_attempts=1,
                timeout_seconds=75.0,
                temperature=0.2
            ),
            BenchmarkConfig(
                id="cfg_qwen_coder_full_repair",
                name="Qwen 2.5 Coder (Full Pipeline + Self-Repair)",
                provider="Ollama",
                model_name="qwen2.5-coder:latest",
                prompt_version="v1.0",
                workflow=WorkflowType.FULL_PIPELINE,
                review_enabled=True,
                testing_enabled=True,
                max_repair_attempts=3,
                timeout_seconds=90.0,
                temperature=0.2
            ),
            BenchmarkConfig(
                id="cfg_qwen_general_full",
                name="Qwen 2.5 General (Planner → Coder → Repair)",
                provider="Ollama",
                model_name="qwen2.5:latest",
                prompt_version="v1.0",
                workflow=WorkflowType.FULL_PIPELINE,
                review_enabled=True,
                testing_enabled=True,
                max_repair_attempts=2,
                timeout_seconds=90.0,
                temperature=0.2
            ),
            BenchmarkConfig(
                id="cfg_llama3_standard",
                name="Llama 3.1 8B (Standard Generation)",
                provider="Ollama",
                model_name="llama3.1:8b",
                prompt_version="v1.0",
                workflow=WorkflowType.DIRECT,
                review_enabled=False,
                testing_enabled=True,
                max_repair_attempts=1,
                timeout_seconds=60.0,
                temperature=0.2
            ),
        ]

        for cfg in default_configs:
            self._saved_configs[cfg.id] = cfg


global_config_manager = ConfigurationManager()
