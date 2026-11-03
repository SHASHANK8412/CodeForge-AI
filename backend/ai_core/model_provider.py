"""
AIForge AI Core — model provider.

Answers come from the local Ollama models through backend.services.llm (model routing, fallback,
caching, telemetry). Only models that are actually installed are listed or accepted; a model call that
fails raises LLMUnavailableError instead of returning invented text.
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.services.llm import LLMUnavailableError, generate_text

_logger = logging.getLogger("aiforge.ai_core.models")

__all__ = ["LLMUnavailableError", "ModelCapability", "ModelMetadata", "ModelResponse", "UnifiedModelProvider",
           "global_model_provider"]


class ModelCapability(str, Enum):
    CHAT = "CHAT"
    EMBEDDINGS = "EMBEDDINGS"


class ModelMetadata(BaseModel):
    id: str
    name: str
    provider: str = "ollama"
    capabilities: List[ModelCapability] = Field(default_factory=lambda: [ModelCapability.CHAT])
    size_bytes: Optional[int] = None


class ModelResponse(BaseModel):
    content: str
    model_id: str
    provider: str = "ollama"


def _installed_ollama_models() -> List[Dict[str, Any]]:
    """The models the local Ollama server has, or [] when it cannot be reached."""
    try:
        from ollama import Client  # type: ignore[attr-defined]
        listing = Client(host=os.getenv("OLLAMA_HOST") or None, timeout=5.0).list()
    except Exception as exc:  # Ollama down or unreachable: no models, not invented ones
        _logger.warning("Could not list Ollama models: %s", exc)
        return []
    models = listing.get("models", []) if isinstance(listing, dict) else getattr(listing, "models", []) or []
    out = []
    for m in models:
        get = m.get if isinstance(m, dict) else (lambda k, _m=m: getattr(_m, k, None))
        name = get("model") or get("name")
        if name:
            out.append({"name": str(name), "size": get("size")})
    return out


class UnifiedModelProvider:
    def list_models(self) -> List[ModelMetadata]:
        models = []
        for m in _installed_ollama_models():
            caps = [ModelCapability.EMBEDDINGS] if "embed" in m["name"] else [ModelCapability.CHAT]
            models.append(ModelMetadata(id=m["name"], name=m["name"], capabilities=caps, size_bytes=m["size"]))
        return models

    def resolve_model(self, model_id: Optional[str]) -> Optional[str]:
        """An installed chat model with this id (`qwen2.5` also matches `qwen2.5:latest`); None lets the router pick."""
        if not model_id:
            return None
        names = [m.id for m in self.list_models() if ModelCapability.CHAT in m.capabilities]
        for name in names:
            if model_id == name or f"{model_id}:latest" == name:
                return name
        return None

    def complete(self, messages: List[Dict[str, str]], model_id: Optional[str] = None) -> ModelResponse:
        system = "\n\n".join(m.get("content", "") for m in messages if m.get("role") == "system")
        conversation = [m for m in messages if m.get("role") != "system"]
        if not conversation:
            raise ValueError("At least one user message is required.")
        prompt = "\n\n".join(f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in conversation[:-1])
        prompt = (prompt + "\n\n" if prompt else "") + conversation[-1].get("content", "")
        model = self.resolve_model(model_id)
        content = generate_text(system, prompt, model=model, task="general")
        return ModelResponse(content=content, model_id=model or "auto")


global_model_provider = UnifiedModelProvider()
