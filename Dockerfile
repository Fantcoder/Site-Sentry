# Stage 1: Build dependencies with uv
FROM python:3.12-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install uv binary
COPY --from=ghcr.io/astral-sh/uv:0.5.1 /uv /uvx /bin/

# Copy dependency definition
COPY pyproject.toml README.md ./

# Install production dependencies only into a standalone venv
RUN uv sync --frozen --no-dev --no-editable

# Copy application source
COPY src/ src/
RUN uv pip install --no-deps -e .

# Stage 2: Minimal non-root runtime image
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create unprivileged user
RUN groupadd -r sitesentry && useradd -r -g sitesentry -s /bin/false sitesentry

# Copy virtual environment and application code from builder
COPY --from=builder --chown=sitesentry:sitesentry /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER sitesentry

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

ENTRYPOINT ["sitesentry"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
