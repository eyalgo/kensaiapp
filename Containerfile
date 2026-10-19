# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    grep \
    sed \
    coreutils \
    findutils \
    diffutils \
    procps \
    less \
    ca-certificates \
    openssh-client \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Node.js 22 + npm, required for Claude Code npm install
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get update \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# Install Claude Code in the image
RUN npm install -g @anthropic-ai/claude-code

RUN useradd -m -u 1000 -s /bin/bash kensai \
 && mkdir -p /workspace /seed /opt/kensai/bin \
 && chown -R kensai:kensai /workspace /seed /opt/kensai

COPY --chown=kensai:kensai <<'EOF' /opt/kensai/bin/entrypoint.sh
#!/usr/bin/env bash
set -euo pipefail

# SEED_REPO names the instance repo mounted under /seed, and has no default: the image serves any
# instance, so it cannot guess which one was mounted. TARGET_REPO defaults to the seed's own name.
SEED_REPO="${SEED_REPO:?set SEED_REPO to the instance repo mounted under /seed, e.g. /seed/<instance>}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
TARGET_REPO="${TARGET_REPO:-$WORKSPACE_ROOT/$(basename "$SEED_REPO")}"

if [ ! -d "$TARGET_REPO/.git" ]; then
  if [ ! -d "$SEED_REPO/.git" ]; then
    echo "Seed repo missing or not a git repo: $SEED_REPO" >&2
    exit 1
  fi
  mkdir -p "$WORKSPACE_ROOT"
  cp -a "$SEED_REPO" "$TARGET_REPO"
fi

cd "$TARGET_REPO"
exec "$@"
EOF

RUN chmod +x /opt/kensai/bin/entrypoint.sh

USER kensai
WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/workspace/.venv/bin:${PATH}"

ENTRYPOINT ["/opt/kensai/bin/entrypoint.sh"]
CMD ["bash"]
