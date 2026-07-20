OLLAMA_SMALL_MODEL = "qwen2.5-coder:latest"
OLLAMA_MEDIUM_MODEL = "qwen2.5-coder:latest"
OLLAMA_LARGE_MODEL = "qwen2.5-coder:latest"
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

# Per-task context window sizes (num_ctx). Prevents VRAM bloat and speeds up prefill.
TASK_NUM_CTX = {
    "planner": 2048,
    "architect": 4096,
    "frontend": 8192,
    "backend": 8192,
    "database": 4096,
    "reviewer": 8192,
    "testing": 4096,
    "documentation": 4096,
    "reflection": 4096,
    "github": 4096,
}

# Per-task output length caps (num_predict). Increased to prevent truncation/incomplete responses.
TASK_NUM_PREDICT = {
    "planner": 2500,
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

# ---------------- Project Generation Options (Day 22) ---------------- #
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 80
DEFAULT_PYTHON_VERSION = "3.13-slim"
DEFAULT_NODE_VERSION = "20-slim"
DEFAULT_LICENSE_TYPE = "MIT"
DEFAULT_ENV_KEYS = ["DATABASE_URL", "JWT_SECRET", "OPENAI_API_KEY", "OLLAMA_MODEL", "PORT"]
GENERATED_PROJECTS_DIR_NAME = "generated_projects"

# ---------------- Self-Healing & Review Options (Day 23) ---------------- #
MAX_RETRY = 3
QUALITY_THRESHOLD = 8.0
MAX_PATCH_SIZE = 100
ENABLE_SELF_HEAL = True
ENABLE_SECURITY_SCAN = True
ENABLE_PERFORMANCE_SCAN = True
REVIEW_MODEL = "qwen2.5-coder:latest"
