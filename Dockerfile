# Build a small image that runs the API.
FROM python:3.12-slim

# uv: the same tool we use locally to install dependencies.
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first: Docker caches this layer, so rebuilds are fast
# unless the dependencies themselves change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

# The database lives in /data so it can be kept in a volume between container restarts.
ENV DATABASE_URL=sqlite:////data/kb.db \
    PATH="/app/.venv/bin:$PATH"
RUN mkdir /data
VOLUME ["/data"]

EXPOSE 8000
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
