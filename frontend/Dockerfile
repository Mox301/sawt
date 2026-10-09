# Sawt UI. Build from the repository root:  docker build -f frontend/Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONPATH=/srv \
    PATH=/opt/venv/bin:$PATH

COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /usr/local/bin/uv

WORKDIR /srv
COPY frontend/pyproject.toml frontend/uv.lock frontend/
RUN cd frontend && uv sync --frozen --no-dev

COPY frontend/ frontend/
RUN useradd --create-home --uid 1000 sawt
USER sawt

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
