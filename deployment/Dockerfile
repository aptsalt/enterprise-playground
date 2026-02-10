# Enterprise Playground - Web App Container
# Runs the FastAPI web app. Ollama runs as a separate service.

FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY playground/ playground/
COPY webapp/ webapp/
COPY workflows/schema.py workflows/schema.py
COPY scraper/ scraper/
COPY scripts/ scripts/
COPY .env.example .env.example

# Create data directories and non-root user
RUN mkdir -p workflows/raw workflows/structured workflows/screenshots \
    playground/generated playground/templates fine_tuning/data fine_tuning/adapters \
    .cache \
    && groupadd -r appuser && useradd -r -g appuser -d /app appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENV APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "webapp.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
