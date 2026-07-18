OLLAMA_SMALL_MODEL = "qwen2.5:latest"
OLLAMA_MEDIUM_MODEL = "qwen2.5:latest"
OLLAMA_LARGE_MODEL = "qwen2.5:latest"
OLLAMA_CODING_MODEL = "qwen2.5-coder:latest"

DEFAULT_OLLAMA_MODEL = OLLAMA_SMALL_MODEL

MAX_HISTORY_MESSAGES = 5
CONVERSATION_HISTORY_TURNS = 10
MAX_PROMPT_CHARS = 12000
MAX_CACHE_ITEMS = 128

# ---------------- Ollama Generation Options (performance tuning) ---------------- #
# Lower temperature/top_p = faster, more deterministic, less "wandering"
# output. A smaller num_ctx keeps the context window (and therefore the
# prompt-processing time) small while still fitting plan + architecture +
# memory context for a single agent call.

OLLAMA_BASE_OPTIONS = {
    "temperature": 0.2,
    "top_p": 0.9,
    "num_ctx": 8192,
}

# Per-task output length caps (num_predict). Increased to prevent truncation/incomplete responses.
TASK_NUM_PREDICT = {
    "planner": 1500,
    "architect": 2048,
    "frontend": 2048,
    "backend": 2048,
    "database": 1500,
    "documentation": 2048,
    "testing": 1500,
    "reviewer": 2048,
    "github": 1500,
    "explanation": 2500,
    "resume": 2048,
    "coding": 3000,
    "debug": 3000,
    "general": 2048,
}

DEFAULT_NUM_PREDICT = 2048
