# kensaiapp-core (`core/`)

The shared **foundation** layer of a kensaiapp — the stable centre every skill
and role resolves back to: doctrine, role loaders, cross-role contracts, the
pipeline contracts, the setup templates, and the memory **conventions** (the
discipline over Claude's native memory — not the mechanism, which is Claude's).

This is **not** the engine — the skills are. Core is what the skills run *on*.
The host instance manages it; everything else points here.

## Layout

- `doctrine/`  — all standing doctrine in 5 subfolders (see `doctrine/README.md`): `governance/` · `flow/` · `engineering/` · `setup/` · `kaizen/` (+ parked flat `sandbox.md`)
- `roles/`     — `CROSS_ROLE.md`, `role_handoff_boundaries.md`, and `loaders/` (16 role loaders)
- `templates/` — the single-source shapes stamped into a new instance/project

## Provenance — how this folder was built

Copied **non-destructively** from the live OS on 2026-06-27. The originals at
`~/.claude/doctrine/` and `~/.claude/system/doctrine/` are **untouched** — `core/`
is a parallel, corrected copy, not a move. The two historical doctrine homes were
merged into one `doctrine/`. Not carried: the stray `system/doctrine/.__wtest`
worktree artifact, and the divergent `doctrine/templates/fdr_template.md` duplicate
(see Known notes).

## Reference convention

Intra-core references go through the **`<CORE>` token** — resolved once per
session by the instance's `resolve_core.py` SessionStart/SubagentStart hook from
`.env` (`CORE=`, default `core/`). This closed the interim state (2026-07-02):
during the 2026-06-27 copy they were rewritten to `~/.claude/core/…`, the
machine address while core lived inside `~/.claude`; with core relocated into
the repo, that prefix was rewritten to `<CORE>/`.

References that point *out* of core:

- **native** — the vendored `.claude/skills/`, `.claude/agents/` inside this
  repo (repointed 2026-07-02 when those layers were vendored; the original
  host-global refs predated vendoring). `~/.claude/CLAUDE.md` mentions stay —
  the user's global rules genuinely live there.
- **personal / privacy-guard** — `~/.claude/rules_parked/…`,
  `~/.claude/projects/<slug>/memory/…`. These correctly point at the host's real
  personal files; core must never copy their content.

## Known notes (flagged, not fixed — out of this step's scope)

1. **Sandbox portability — PASSED (2026-06-29).** Audited: the sandbox files carry **no
   machine-specific paths** (all `~/`-home-relative, portable across users) — nothing to
   "strip"; the earlier "strip host paths" framing was inaccurate. The one real residual is
   an **external dependency** — the wrappers delegate to a host-provided `~/.claude/docker/`
   runner (`run.sh` / `entry.sh` / `Dockerfile.base`) **not shipped in this repo**, now made
   explicit in `templates/docker_sandbox_template.md`. **Resolved (Product, 2026-06-29): docker
   is publish-excluded / parked** — kept on the OS, out of the publish set, de-wiring deferred to
   publish-prep. See the registry `system/publish_exclude.md` for artifacts + re-add steps.
2. **`fdr_template` divergence — RESOLVED (Product, 2026-06-28).** The two live
   homes carried diverging copies; the `~/.claude/doctrine/` (root-doctrine) one was
   the **old** version. Core kept the canonical `system/doctrine/` version, so
   `templates/fdr_template.md` is correct. (The stale root copy at
   `~/.claude/doctrine/templates/fdr_template.md` was **deleted 2026-06-29** — nothing
   consumed it; the FDR skill used the `system/doctrine/` canonical copy.)

## Not in core (by design)

Native Claude features — `skills/`, `commands/`, `agents/`, `hooks`, `settings.json`,
**`rules/`, and memory** — plus instance state (`system/queues|shukuba|requirements|docs`)
and live personal memory all stay outside core; kensaiapp does not control any native
mechanism. Core = doctrine + roles + pipeline + templates + the memory **conventions** doctrine.
