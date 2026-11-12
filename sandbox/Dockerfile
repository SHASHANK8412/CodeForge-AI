# AIForge execution sandbox image.
#
# Generated projects run in this image with --network none, so everything a
# typical generated FastAPI project imports must be installed here at build
# time. Keep this list small and pinned: it defines what "the project builds"
# means in benchmark results.
#
#   docker build -t aiforge-sandbox:py311 sandbox/
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Unprivileged user; the runner also passes --user 10001:10001.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin sandbox
USER 10001
WORKDIR /work
CMD ["python", "--version"]
