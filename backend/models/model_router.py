"""
AIForge Intelligent Model Router & Generation Profiles
======================================================
Centralized model routing, dynamic Ollama model discovery, model capability registry,
and task-specific generation profiles for AIForge V2.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set

_logger = logging.getLogger("aiforge.models.router")
if not _logger.handlers and not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
_logger.setLevel(logging.INFO)


@dataclass
class GenerationProfile:
    name: str
    preferred_capability: str
    temperature: float
    num_predict: int
    num_ctx: int
    timeout: float


# Predefined Generation Profiles (Step 2, Step 11, Step 12)
PROFILES: Dict[str, GenerationProfile] = {
    "GENERAL": GenerationProfile(
        name="GENERAL",
        preferred_capability="general",
        temperature=0.3,
        num_predict=1500,
        num_ctx=4096,
        timeout=120.0,
    ),
    "EXPLANATION": GenerationProfile(
        name="EXPLANATION",
        preferred_capability="general",
        temperature=0.4,
        num_predict=2048,
        num_ctx=4096,
        timeout=180.0,
    ),
    "CODING": GenerationProfile(
        name="CODING",
        preferred_capability="coding",
        temperature=0.1,
        num_predict=2500,
        num_ctx=8192,
        timeout=300.0,
    ),
    "DEBUGGING": GenerationProfile(
        name="DEBUGGING",
        preferred_capability="coding",
        temperature=0.0,
        num_predict=2500,
        num_ctx=8192,
        timeout=300.0,
    ),
    "RAG": GenerationProfile(
        name="RAG",
        preferred_capability="general",
        temperature=0.1,
        num_predict=1500,
        num_ctx=4096,
        timeout=180.0,
    ),
    "RESUME": GenerationProfile(
        name="RESUME",
        preferred_capability="general",
        temperature=0.2,
        num_predict=2048,
        num_ctx=4096,
        timeout=180.0,
    ),
    "PLANNING": GenerationProfile(
        name="PLANNING",
        preferred_capability="general",
        temperature=0.3,
        num_predict=2200,
        num_ctx=6144,
        timeout=240.0,
    ),
    "ARCHITECTURE": GenerationProfile(
        name="ARCHITECTURE",
        preferred_capability="coding",
        temperature=0.2,
        num_predict=2800,
        num_ctx=8192,
        timeout=300.0,
    ),
    "REVIEW": GenerationProfile(
        name="REVIEW",
        preferred_capability="coding",
        temperature=0.1,
        num_predict=2048,
        num_ctx=8192,
        timeout=240.0,
    ),
    "TESTING": GenerationProfile(
        name="TESTING",
        preferred_capability="coding",
        temperature=0.1,
        num_predict=1500,
        num_ctx=4096,
        timeout=180.0,
    ),
    "DOCUMENTATION": GenerationProfile(
        name="DOCUMENTATION",
        preferred_capability="general",
        temperature=0.3,
        num_predict=2048,
        num_ctx=4096,
        timeout=180.0,
    ),
}


@dataclass
class ModelSelection:
    profile: GenerationProfile
    selected_model: str
    fallback_models: List[str]
    temperature: float
    num_predict: int
    num_ctx: int
    timeout: float
    is_fallback: bool = False
    reason: str = ""


# Dynamic Discovery & Memory Cache (Step 4)
_INSTALLED_MODELS_CACHE: Optional[List[str]] = None


def discover_installed_models(force_refresh: bool = False) -> List[str]:
    """
    Safely discovers installed Ollama models without calling 'ollama pull'.
    Caches results in memory. Handles Ollama connection failures gracefully.
    """
    global _INSTALLED_MODELS_CACHE
    if _INSTALLED_MODELS_CACHE is not None and not force_refresh:
        return _INSTALLED_MODELS_CACHE

    installed = []
    try:
        from ollama import Client
        client = Client(timeout=5.0)
        res = client.list()
        models_list = res.get("models", [])
        for m in models_list:
            if isinstance(m, dict):
                name = m.get("name") or m.get("model")
            else:
                name = getattr(m, "model", None) or getattr(m, "name", str(m))
            if name and not any(emb in name.lower() for emb in ["embed", "embedding", "minilm", "bge", "bert"]):
                installed.append(name)
    except Exception as e:
        _logger.debug(f"Ollama list discovery failed or offline: {e}")

    # Fallback default if offline or discovery empty
    if not installed:
        installed = ["qwen2.5:latest", "qwen2.5-coder:latest"]

    _INSTALLED_MODELS_CACHE = installed
    return installed


# Model Capability Registry (Step 5)
def get_model_capabilities(model_name: str) -> Set[str]:
    """
    Returns set of capabilities for a given model name.
    """
    name_lower = model_name.lower()
    capabilities = set()

    # Coder capability
    if any(kw in name_lower for kw in ["coder", "code", "deepseek-coder", "starcoder", "wizardcoder"]):
        capabilities.update(["coding", "debugging", "review", "testing", "architecture"])

    # General / Reasoning capability
    if any(kw in name_lower for kw in ["qwen2.5:", "qwen2.5", "llama", "mistral", "gemma", "phi", "instruct", "general"]) and not ("coder" in name_lower and "qwen2.5:" not in name_lower):
        capabilities.update(["general", "explanation", "reasoning", "resume", "rag", "planning", "documentation"])

    # Default fallback capability if uncategorized
    if not capabilities:
        capabilities.update(["general", "coding"])

    return capabilities


class ModelRouter:
    """
    Centralized Model Router:
    Maps canonical intents and agent roles to generation profiles and optimal installed models.
    """

    def select(
        self,
        intent_or_task: str,
        agent_name: str = "",
        prompt: str = "",
        user_override: Optional[str] = None
    ) -> ModelSelection:
        t_lower = (intent_or_task or "").upper().strip()
        a_lower = (agent_name or "").lower().strip()

        # Step 6 & 7: Map Intent / Agent Role -> Profile Name
        profile_key = "GENERAL"

        if t_lower in ["EXPLANATION"]:
            profile_key = "EXPLANATION"
        elif t_lower in ["CODING"]:
            profile_key = "CODING"
        elif t_lower in ["DEBUGGING"]:
            profile_key = "DEBUGGING"
        elif t_lower in ["RAG_QUERY", "RAG"]:
            profile_key = "RAG"
        elif t_lower in ["RESUME"]:
            profile_key = "RESUME"
        elif t_lower in ["GENERAL_QA", "UNKNOWN"]:
            profile_key = "GENERAL"
        elif t_lower in ["PROJECT_GENERATION"] or "project" in a_lower:
            # Step 7: Route by Project Agent Role
            if "planner" in a_lower:
                profile_key = "PLANNING"
            elif "architect" in a_lower:
                profile_key = "ARCHITECTURE"
            elif "frontend" in a_lower or "backend" in a_lower or "database" in a_lower:
                profile_key = "CODING"
            elif "reviewer" in a_lower:
                profile_key = "REVIEW"
            elif "testing" in a_lower or "test" in a_lower:
                profile_key = "TESTING"
            elif "doc" in a_lower:
                profile_key = "DOCUMENTATION"
            else:
                profile_key = "ARCHITECTURE"
        else:
            # Fallback by agent_name / task string
            if "explanation" in a_lower or "explanation" in t_lower.lower():
                profile_key = "EXPLANATION"
            elif "coding" in a_lower or "coding" in t_lower.lower():
                profile_key = "CODING"
            elif "debug" in a_lower or "debug" in t_lower.lower():
                profile_key = "DEBUGGING"
            elif "resume" in a_lower or "resume" in t_lower.lower():
                profile_key = "RESUME"
            elif "rag" in a_lower or "rag" in t_lower.lower():
                profile_key = "RAG"
            elif "planner" in a_lower:
                profile_key = "PLANNING"
            elif "architect" in a_lower:
                profile_key = "ARCHITECTURE"
            elif "reviewer" in a_lower:
                profile_key = "REVIEW"
            elif "testing" in a_lower:
                profile_key = "TESTING"

        profile = PROFILES.get(profile_key, PROFILES["GENERAL"])

        # Discover installed models
        installed = discover_installed_models()

        # Step 25: Check environment variable overrides
        env_override = None
        if profile.preferred_capability == "general" and os.environ.get("AIFORGE_GENERAL_MODEL"):
            env_override = os.environ.get("AIFORGE_GENERAL_MODEL")
        elif profile.preferred_capability == "coding" and os.environ.get("AIFORGE_CODING_MODEL"):
            env_override = os.environ.get("AIFORGE_CODING_MODEL")
        elif profile_key == "DEBUGGING" and os.environ.get("AIFORGE_DEBUG_MODEL"):
            env_override = os.environ.get("AIFORGE_DEBUG_MODEL")

        selected_model: Optional[str] = None
        reason = ""

        # 1. User / Env Override
        target_override = user_override or env_override
        if target_override:
            for inst in installed:
                if target_override.lower() in inst.lower():
                    selected_model = inst
                    reason = f"Explicit override to '{selected_model}'"
                    break

        # 2. Preferred Capability Match from Installed Models
        if not selected_model:
            preferred = profile.preferred_capability
            # Exact capability match
            for inst in installed:
                caps = get_model_capabilities(inst)
                if preferred in caps:
                    # Give preference to specific model names for general vs coding
                    if preferred == "general" and ("coder" not in inst.lower() or "qwen2.5:" in inst.lower()):
                        selected_model = inst
                        reason = f"Matched preferred capability '{preferred}' for profile '{profile.name}'"
                        break
                    elif preferred == "coding" and "coder" in inst.lower():
                        selected_model = inst
                        reason = f"Matched preferred capability '{preferred}' for profile '{profile.name}'"
                        break

            # Secondary pass if no strict name preference match
            if not selected_model:
                for inst in installed:
                    caps = get_model_capabilities(inst)
                    if preferred in caps:
                        selected_model = inst
                        reason = f"Matched capability '{preferred}' for profile '{profile.name}'"
                        break

        # 3. Step 19: Single-model or fallback to first available installed model
        if not selected_model and installed:
            selected_model = installed[0]
            reason = f"Defaulted to first installed model '{selected_model}'"

        if not selected_model:
            selected_model = "qwen2.5-coder:latest"
            reason = "Default fallback model"

        # Build fallback model chain (Step 9)
        fallbacks = [m for m in installed if m != selected_model]

        # Log selection once per request (Step 15)
        _logger.info(
            "[AIForge Model Router] Intent/Task: %s | Agent: %s | Profile: %s | Model: %s | Temp: %.1f | Fallback: False | Reason: %s",
            t_lower or "GENERAL",
            agent_name or "Agent",
            profile.name,
            selected_model,
            profile.temperature,
            reason
        )

        return ModelSelection(
            profile=profile,
            selected_model=selected_model,
            fallback_models=fallbacks,
            temperature=profile.temperature,
            num_predict=profile.num_predict,
            num_ctx=profile.num_ctx,
            timeout=profile.timeout,
            is_fallback=False,
            reason=reason
        )


# Global ModelRouter Instance
global_model_router = ModelRouter()
