# Docker sandbox scaffold templates

Templates for the four project-level sandbox files, stamped when a project needs sandboxed runs.

Substitute throughout: `<project>` → project name, `<image-name>` → Q3a answer, `<network-name>` → Q3b answer.

> **Prerequisite — host-provided, NOT shipped in this repo.** These wrappers delegate to a generic
> runner at `~/.claude/docker/` (`run.sh`, `entry.sh`, `Dockerfile.base`, `base_image.txt`) — OS-level
> sandbox infra that lives outside the published repo. All paths below are `~/`-home-relative (portable
> across users), but a fresh clone must **provision `~/.claude/docker/` itself** before the sandbox
> feature works.

---

## `system/sandbox/Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1.6
# <project> sandbox image — extends claude-sandbox-base with project deps.
#
# Two-step build:
#
#   Step 1 — build global base (once; rebuild only when Claude Code version changes):
#     docker build --build-arg BASE_IMAGE="$(cat ~/.claude/docker/base_image.txt)" \
#                  -f ~/.claude/docker/Dockerfile.base \
#                  -t claude-sandbox-base:latest \
#                  ~/.claude/docker/
#
#   Step 2 — build project extension (context: REPO ROOT):
#     docker build -f system/sandbox/Dockerfile -t <image-name> .
#
# Doctrine: system/sandbox/DOCTRINE.md

ARG SANDBOX_BASE_IMAGE=claude-sandbox-base:latest
FROM ${SANDBOX_BASE_IMAGE}

# Add project-specific dependencies here.
# Example for Python venv from a lock file:
# USER root
# COPY requirements.lock /tmp/requirements.lock
# RUN python -m venv /opt/venv \
#  && /opt/venv/bin/pip install --no-deps -r /tmp/requirements.lock \
#  && /opt/venv/bin/pip check \
#  && rm /tmp/requirements.lock
# USER sandbox
```

---

## `system/sandbox/run.sh`

```bash
#!/usr/bin/env bash
# <project> sandbox launcher — thin wrapper over ~/.claude/docker/run.sh.
#
# Tracked source: system/sandbox/run.sh
# Doctrine:       system/sandbox/DOCTRINE.md
#
# Doctrine-bound: this is the ONLY legitimate entry point for autonomous runs
# in this project. It sets project-specific parameters (image name, network name)
# and delegates all launch logic to the generic runner at ~/.claude/docker/run.sh.
# The flag --dangerously-skip-permissions is NOT carried here; it lives in
# ~/.claude/docker/entry.sh which is baked into the container image.
#
# Args (passed through to ~/.claude/docker/run.sh):
#   $1: worktree path (host-side)
#   $2: run-dir slug

set -euo pipefail

export SANDBOX_IMAGE="<image-name>"
export SANDBOX_NETWORK="<network-name>"
exec ~/.claude/docker/run.sh "$@"
```

---

## `system/sandbox/DOCTRINE.md`

```markdown
# Sandboxed autonomous runs — <project> overlay

Extends `<CORE>/doctrine/sandbox.md`; adds project-specific launch path and container identity.

---

## Project-specific contract

**Sanctioned launch path.** `system/sandbox/run.sh` is the only legitimate entry point for autonomous runs in this project. It sets project-specific parameters (`SANDBOX_IMAGE`, `SANDBOX_NETWORK`) and delegates to `~/.claude/docker/run.sh`, which invokes the Docker container running `~/.claude/docker/entry.sh` — the ONE doctrine-legitimate carrier of `--dangerously-skip-permissions`. Any other invocation of the flag is a doctrine violation regardless of intent or context.

**Container identity.** Sandbox network `<network-name>`; in-container user `sandbox` (non-root).

---

Codified from the sandbox doctrine.
```

---

## `scripts/sandbox-launch.sh`

```bash
#!/usr/bin/env bash
# Host-side wrapper: create git worktree then invoke the sanctioned sandbox launcher.
#
# Usage: scripts/sandbox-launch.sh <worktree-path> <branch-name> <run-dir-slug>
#
# Product invokes this script and walks away. No manual git worktree add step required.

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "sandbox-launch.sh: usage: sandbox-launch.sh <worktree-path> <branch-name> <run-dir-slug>" >&2
    exit 2
fi

WORKTREE_PATH="$1"
BRANCH_NAME="$2"
RUN_DIR_SLUG="$3"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

WORKTREE_ABS="$(realpath "$(dirname "$WORKTREE_PATH")")/$(basename "$WORKTREE_PATH")"

echo "sandbox-launch.sh: creating worktree at $WORKTREE_ABS on branch $BRANCH_NAME..."
if git worktree list --porcelain | grep -qF "worktree $WORKTREE_ABS"; then
    echo "sandbox-launch.sh: worktree already exists at $WORKTREE_ABS, skipping creation..."
elif git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "sandbox-launch.sh: branch $BRANCH_NAME exists, adding worktree on existing branch..."
    git worktree add "$WORKTREE_ABS" "$BRANCH_NAME"
else
    git worktree add "$WORKTREE_ABS" -b "$BRANCH_NAME"
fi

echo "sandbox-launch.sh: launching sandbox run..."
exec system/sandbox/run.sh "$WORKTREE_ABS" "$RUN_DIR_SLUG"
```
