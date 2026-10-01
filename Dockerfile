# Builds the static site and serves it with nginx.
#
# Audio clips are generated on your machine (`uv run audio`) and committed to git,
# so this image never installs the voice model.
#
#   docker build -t viet-textbook .
#   docker run -d -p 80:80 viet-textbook

# ---- Stage 1: build dist/ ----
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/uv
ENV UV_LINK_MODE=copy
WORKDIR /app

# Dependencies first, so they're cached between builds.
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --locked --no-default-groups --no-install-project

COPY . .
RUN uv sync --locked --no-default-groups \
 && uv run --no-sync anki \
 && uv run --no-sync site --strict

# ---- Stage 2: serve it ----
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
