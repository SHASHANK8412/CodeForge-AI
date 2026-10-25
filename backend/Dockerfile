# AIForge backend (FastAPI + LangGraph). Build from the repository root:
#   docker build -f backend/Dockerfile -t aiforge-backend .
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# git is used by the GitHub export / workspace features.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install the CPU-only torch wheel first; the default PyPI wheel bundles CUDA (~2GB+).
COPY requirements.txt .
RUN pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 aiforge \
    && mkdir -p /app/generated_projects /app/backend/logs \
    && chown -R aiforge:aiforge /app
USER aiforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8).status == 200 else 1)"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
