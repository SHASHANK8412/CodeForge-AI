# Production Dockerfile for FastAPI backend
FROM python:3.11-slim

# Prevent writing pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install native compilation dependencies for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source directory
COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
