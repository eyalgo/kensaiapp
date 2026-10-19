---
version: "1.1.0"
---

# Sandboxed autonomous runs — doctrine

Generic contract for running Claude autonomous-mode sessions inside a Docker sandbox.

## Core principle

All autonomous runs that use `--dangerously-skip-permissions` must execute inside a sanctioned sandbox. The flag is legitimate only via the project's designated launch script; any other invocation is a doctrine violation regardless of intent or context.

Interactive sessions remain governed by `--permission-mode acceptEdits`; this doctrine governs only the autonomous-run surface.

## Step-1 floor — prevent-stupid defaults

No host credential mounts (specifically not `~/.claude`, `~/.ssh`, `~/.aws`, `~/.config`); no `--privileged`, no `--network host`, no docker-socket mount. Container runs as a non-root user. Two mounts: worktree → `/workdir:rw`; main repo `.git` dir → `<REPO_ROOT>/.git:<REPO_ROOT>/.git:rw` (same absolute path on host and in container — required for container-side git commits; preserves worktree `.git` pointer validity without rewriting — see VirtioFS gap). Git user identity passed via `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_*` env vars from host git config (not a credential mount).

**Non-credential read-only asset exception.** The following `~/.claude` paths may be mounted read-only (`:ro`) — they contain only markdown definitions and configuration, no API keys or session data:

| Path | Contents |
|---|---|
| `~/.claude/CLAUDE.md` | Global instruction file |
| `~/.claude/system/doctrine/` | Doctrine — role loaders, cross-role contracts, pipeline, testing, setup |
| `~/.claude/doctrine/` | Global meta-doctrine (commit format, doctrine structure, ai responsibility, sandbox) |
| `~/.claude/skills/` | Skill definitions |
| `~/.claude/commands/` | Slash command definitions |

The blanket `~/.claude` credential-mount ban does not extend to these paths when mounted `:ro`. All other `~/.claude` subdirectories (`projects/`, `sessions/`, `tools/`, `hooks/`, `rules_parked/`, `settings.json`, the rest of `system/` outside `system/doctrine/`, etc.) remain prohibited. **Do not add a `~/.claude/rules_parked/` row to the table.** Nothing loads that set on the host; mounting it into a container loads it, which is a behaviour change the run never asked for.

**Launcher self-verification.** The launch script refuses to launch if its constructed `docker run` invocation violates any prevent-stupid default. Scans for `--privileged`, `--network host`, docker-socket mounts, host-credential paths in `-v` mounts, and absence of `--user <non-root>`. Exits non-zero before invoking docker.

## Step-2 floor (lands before broker-credential trigger)

- **Network egress allowlist.** Custom bridge plus iptables rules restricting egress to the API provider, source control remote, and package registries actually used. Not "the container has internet."
- **Scoped API key with hard spend cap.** Separate-from-personal API key, scoped to sandboxed-runs use, with a workspace-level hard spend cap as the circuit breaker against infinite-loop tool-use bill surprise.
- **Launcher self-verification extended.** Launch script additionally refuses to launch unless the egress allowlist is active and scoped-key handling is wired.

## Worktree + sandbox relationship

Worktrees are filesystem/git-state isolation; the sandbox is runtime/security isolation; both apply together, not as alternatives. The worktree is created on the host before the container starts; the worktree directory is mounted into the container as the working directory; the run makes commits inside the container; push happens on the host after container exit.

## Bypass trailer

Hook-bypass requires an explicit `Sandbox-Floor-Bypass: <reason>` trailer in the commit message so any deferral is auditable in `git log`.

## Self-application

This contract binds Claude's own outputs. Run prompts, dev instructions, scripts, suggestions to Product — none may include `--dangerously-skip-permissions` outside the sanctioned launch path.

## Cloud sandboxes

Out of scope for local Docker sandboxes. Cloud sandboxes (Codespaces, ephemeral VMs) address a different threat model (walk-away-while-laptop-closed). Adding cloud as a second sanctioned path requires a new doctrine commit.
