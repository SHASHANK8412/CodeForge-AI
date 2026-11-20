"""
Local Hugging Face models: small task models that run on the CPU inside the backend process.

| role        | default model                                    | what it replaces                         | setting                  |
|-------------|--------------------------------------------------|------------------------------------------|--------------------------|
| injection   | protectai/deberta-v3-base-prompt-injection-v2    | pattern-only prompt-injection flagging   | AIFORGE_INJECTION_MODEL  |
| reranker    | cross-encoder/ms-marco-MiniLM-L6-v2              | keyword-boost reranking of RAG results   | AIFORGE_RERANKER_MODEL   |
| embeddings  | BAAI/bge-small-en-v1.5                           | word-hash vectors (no semantic model ran) | EMBEDDING_MODEL          |
| speech      | Systran/faster-whisper-base                      | (new) spoken build requests              | AIFORGE_WHISPER_MODEL    |

Models load once, on first use, from the local Hugging Face cache only (local_files_only): nothing is downloaded while
the app runs. ``python -m backend.ml.local_models download`` fetches them. A role set to ``off`` (or every role, with
AIFORGE_HF_MODELS=off), or whose model is not in the cache or fails to load, is unavailable: its caller keeps its
rule-based behaviour, and ``status()`` (shown by /health) says which roles are active and why not.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence

_logger = logging.getLogger("aiforge.ml")

ROLES: Dict[str, tuple] = {
    "injection": ("AIFORGE_INJECTION_MODEL", "protectai/deberta-v3-base-prompt-injection-v2"),
    "reranker": ("AIFORGE_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2"),
    "embeddings": ("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
    "speech": ("AIFORGE_WHISPER_MODEL", "Systran/faster-whisper-base"),
}
# Files each model needs (one weights format, config, tokenizer) - what `download` fetches.
_FILES = {
    "injection": ["*.json", "model.safetensors", "*.model", "*.txt"],
    "reranker": ["*.json", "model.safetensors", "*.txt"],
    "embeddings": ["*.json", "model.safetensors", "*.txt", "1_Pooling/*"],
    "speech": ["*.json", "model.bin", "*.txt"],
}
# bge v1.5: short queries are embedded with this instruction; documents are embedded as they are.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_lock = threading.Lock()
_loaded: Dict[str, Any] = {}
_errors: Dict[str, str] = {}


def model_id(role: str) -> Optional[str]:
    """The configured model for a role, or None when the role (or all local models) is switched off."""
    if os.environ.get("AIFORGE_HF_MODELS", "on").strip().lower() in ("off", "0", "false", "no"):
        return None
    env, default = ROLES[role]
    value = os.environ.get(env, "").strip()
    if value.lower() in ("off", "0", "false", "no", "none"):
        return None
    # EMBEDDING_MODEL used to name the old (never loaded) all-MiniLM-L6-v2 default; a bare name maps to its repo.
    if value and "/" not in value and role == "embeddings":
        value = f"sentence-transformers/{value}"
    return value or default


def _load(role: str, mid: str) -> Any:
    if role == "injection":
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
        tok = AutoTokenizer.from_pretrained(mid, local_files_only=True)
        mdl = AutoModelForSequenceClassification.from_pretrained(mid, local_files_only=True)
        return pipeline("text-classification", model=mdl, tokenizer=tok, device=-1, truncation=True, max_length=512,
                        top_k=None)
    if role == "reranker":
        from sentence_transformers import CrossEncoder
        return CrossEncoder(mid, device="cpu", local_files_only=True)
    if role == "embeddings":
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(mid, device="cpu", local_files_only=True)
    if role == "speech":
        from faster_whisper import WhisperModel
        return WhisperModel(mid, device="cpu", compute_type="int8", local_files_only=True)
    raise KeyError(role)


def get(role: str) -> Any:
    """The loaded model for a role, or None (switched off, not downloaded, or failed to load - logged once)."""
    mid = model_id(role)
    if not mid:
        return None
    key = f"{role}:{mid}"
    if key in _loaded:
        return _loaded[key]
    if key in _errors:
        return None
    with _lock:
        if key in _loaded or key in _errors:
            return _loaded.get(key)
        try:
            _loaded[key] = _load(role, mid)
            _logger.info("Local model ready: %s = %s", role, mid)
        except Exception as e:  # noqa: BLE001 - a missing model means the rule-based path, not a crash
            _errors[key] = f"{type(e).__name__}: {str(e)[:200]}"
            _logger.warning("Local model %s (%s) unavailable, using the rule-based path: %s", role, mid, _errors[key])
            return None
    return _loaded[key]


def status() -> Dict[str, Dict[str, Any]]:
    """Per role: the configured model and whether it is loaded (models load on first use, so 'not loaded yet' is not
    a failure). Never loads anything."""
    out = {}
    for role in ROLES:
        mid = model_id(role)
        key = f"{role}:{mid}"
        out[role] = {"model": mid, "state": ("off" if not mid else "loaded" if key in _loaded
                                             else "unavailable" if key in _errors else "not loaded yet")}
        if key in _errors:
            out[role]["error"] = _errors[key]
    return out


def reset() -> None:
    """Forget loaded models and failures (tests; or after downloading a model while the app runs)."""
    with _lock:
        _loaded.clear()
        _errors.clear()
        _injection_cache.clear()


# --- injection ---------------------------------------------------------------------------------------------------

_injection_cache: "OrderedDict[str, float]" = OrderedDict()
_CACHE_MAX = 4096


def injection_threshold() -> float:
    try:
        return float(os.environ.get("AIFORGE_INJECTION_THRESHOLD", "0.5"))
    except ValueError:
        return 0.5


def injection_scores(texts: Sequence[str]) -> Optional[List[float]]:
    """Probability that each text is a prompt injection, or None when the classifier is unavailable. Results are cached
    by content, since the same passage is scanned and then redacted."""
    clf = get("injection")
    if clf is None:
        return None
    keys = [hashlib.sha256((t or "").encode("utf-8")).hexdigest() for t in texts]
    todo = sorted({k: t for k, t in zip(keys, texts) if k not in _injection_cache and (t or "").strip()}.items())
    if todo:
        results = clf([t for _, t in todo], batch_size=8)
        for (k, _), res in zip(todo, results):
            labels = {r["label"].upper(): r["score"] for r in (res if isinstance(res, list) else [res])}
            _injection_cache[k] = float(labels.get("INJECTION", 1.0 - labels.get("SAFE", 1.0)))
            if len(_injection_cache) > _CACHE_MAX:
                _injection_cache.popitem(last=False)
    return [_injection_cache.get(k, 0.0) for k in keys]


# --- reranker ----------------------------------------------------------------------------------------------------

def rerank_scores(query: str, passages: Sequence[str]) -> Optional[List[float]]:
    """Relevance of each passage to the query in [0, 1] (sigmoid of the cross-encoder logit), or None."""
    ce = get("reranker")
    if ce is None or not passages:
        return None
    logits = ce.predict([(query, (p or "")[:2000]) for p in passages], batch_size=16, show_progress_bar=False)
    return [1.0 / (1.0 + math.exp(-float(x))) for x in logits]


# --- embeddings --------------------------------------------------------------------------------------------------

def embed(texts: Sequence[str], query: bool = False) -> Optional[List[List[float]]]:
    """Normalised embeddings, or None when the model is unavailable. Queries get bge's retrieval instruction."""
    st = get("embeddings")
    if st is None:
        return None
    mid = model_id("embeddings") or ""
    prefix = BGE_QUERY_PREFIX if query and "bge-" in mid and "v1.5" in mid else ""
    vectors = st.encode([prefix + (t or "") for t in texts], batch_size=32, normalize_embeddings=True,
                        show_progress_bar=False)
    return [v.tolist() for v in vectors]


# --- speech ------------------------------------------------------------------------------------------------------

SAMPLE_RATE = 16000


def decode_audio(path: str):
    """16 kHz mono float32 samples of an audio file (webm/ogg/wav/mp3/m4a), decoded with PyAV's stable API.
    (faster-whisper's own decoder passes an argument that newer PyAV releases removed.)"""
    import av
    import numpy as np
    resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    chunks = []
    with av.open(path, mode="r") as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame) or []:
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None) or []:          # flush
            chunks.append(out.to_ndarray().reshape(-1))
    samples = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int16)
    return samples.astype(np.float32) / 32768.0


def transcribe(path: str, language: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Text of an audio file, or None when the speech model is unavailable. Voice-activity filtering drops silence."""
    model = get("speech")
    if model is None:
        return None
    audio = decode_audio(path)
    segments, info = model.transcribe(audio, language=language or None, beam_size=1, vad_filter=True)
    text = " ".join(s.text.strip() for s in segments).strip()
    return {"text": text, "language": info.language, "duration_seconds": round(len(audio) / SAMPLE_RATE, 2)}


# --- download ----------------------------------------------------------------------------------------------------

def download(roles: Optional[Sequence[str]] = None) -> Dict[str, str]:
    """Fetch the configured models into the local Hugging Face cache (the only place anything is downloaded)."""
    from huggingface_hub import snapshot_download
    out = {}
    for role in roles or list(ROLES):
        mid = model_id(role)
        if mid:
            out[role] = snapshot_download(mid, allow_patterns=_FILES[role])
    return out


if __name__ == "__main__":
    import json
    import sys
    if sys.argv[1:2] == ["download"]:
        print(json.dumps(download(sys.argv[2:] or None), indent=2))
    else:
        print(json.dumps(status(), indent=2))
