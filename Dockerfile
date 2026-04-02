# Francis Suite — reproducible runtime with Playwright (aligned with uv.lock).
#
# Image vs container:
#   - Image  = blueprint built with `docker build` (layers + tag, e.g. francis-suite:local).
#   - Container = one running (or stopped) instance: `docker run` / `docker compose run`.
#
# Copied into the image: francis_suite/ only (+ pyproject.toml, uv.lock, README.md).
# No examples/ and no workflows/ baked in — XML always comes from a host mount at /app/workflows.
#
# Build: docker build -t francis-suite:local .
# Run (workflows folder can live OUTSIDE this repo):
#   docker run --rm \
#     -v "${PWD}/docker-output:/app/output" \
#     -v "/path/to/your/workflows:/app/workflows" \
#     francis-suite:local francis-suite run workflows/my.xml
# Compose: set WORKFLOWS_HOST_PATH in .env (see .env.example) or use default ./workflows.

FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

LABEL org.opencontainers.image.title="francis-suite" \
      org.opencontainers.image.description="Francis Suite workflow runner (Python + Playwright)" \
      org.opencontainers.image.source="https://github.com/mangelrfdev/francis-suite"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY francis_suite ./francis_suite

RUN mkdir -p /app/workflows \
    && uv sync --frozen --no-dev \
    && uv cache clean

ENV PATH="/app/.venv/bin:$PATH"

# Base image bundles browser deps; Python playwright package version matches uv.lock.
# Override at run time — the workflow file must exist under the mounted /app/workflows.
CMD ["francis-suite", "run", "workflows/record_pipeline_minimal.xml"]
