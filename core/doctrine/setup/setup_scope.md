---
version: "1.17.1"
---

# Stamping scope — dispositions and drift criteria

Governs what a **stamper** is allowed to create or modify — `project-stamp` today, and whatever
stands up an instance's own files. Applies to the Fix phase
(repairing an existing repo). In Init, all `[create]`, `[template]` and `[hybrid]` items are created fresh. `[user]`
items are never created by a stamper in any mode.

> **Single source of the tree.** The file tree — and each entry's **disposition tag** (`[hybrid]` /
> `[create]` / `[template]` / `[user]` / `[special]`) — lives in the manifest `kensaiapp_structure.md`. This file does
> **not** re-list the tree. It defines two things the manifest defers to it for: (1) what each disposition
> *does*, and (2) the per-file **drift-content checks**.

---

## What each disposition does

### `[hybrid]` — create if missing; apply user's a/b/c choice on fix
Template-owned, drift-checked. On Init: created fresh. On Fix, when drift is found: offer
**(a)** overwrite from template, **(b)** keep as-is, **(c)** show a diff and let the user merge.

### `[create]` — create if missing; never overwrite, never delete
Created fresh on Init / when absent on Fix. The skill never modifies an existing one. Some `[create]`
files are still *drift-reported* (see the criteria below); reporting never auto-modifies them.

### `[template]` — the template's bytes; rewritten whenever they differ
The same in every instance, and holding nothing an instance authored — so there is no local edit to
lose and no a/b/c choice to offer. Created fresh on Init; on Fix, or on any re-run of its stamper, a
copy that differs from the template is overwritten and reported as updated. An instance that needs
to say something of its own says it in a `[create]` file beside it.

### `[user]` — never created or modified by a stamper, in any mode
User- / pipeline-authored.

### `[special]` — `.gitignore`
Create if missing. On Fix: **append only** — add missing Claude Code entries at the end. Never modify,
reorder, or remove any existing line.

---

## Drift criteria — content checks for files that exist

For each file that **exists** on disk, the audit checks the following. Files with no entry here are not
content-checked (create-if-missing only — e.g. queue/journey files, the `journey/tobiishi/` + `trail/`
directory stubs, memory files). **Doctrine stubs *are* drift-checked** — for the host-path leak (see
the doctrine-files entry below).

### `~/.claude/CLAUDE.md`
Required sections: permission mode, loader map, commit format, direction-and-journey convention, doctrine sources.

### `<CORE>/roles/loaders/<role>_global.md`
Required sections: role posture, what project context to read on invocation (context only — queue pickup is deliberate, not a reflexive on-invocation read), role does/does not do, hand-off triggers.

### `AGENTS.md` (`[template]`)
Drift: any difference from `<CORE>/templates/agents_md_template.md` — the file is the template's
bytes. Extra: each loader map entry must reference a path that exists on disk.
`core/tools/check_satellites.py` reports it, for the host and every rostered satellite.

### `CLAUDE.md` (`[template]`)
Drift: any difference from `<CORE>/templates/claude_md_template.md` — the file is one import line,
`@AGENTS.md`. A missing one is drift too: Claude Code then falls back to `AGENTS.md` and says so at
every session start. Reported by the same check.

### `kensaiapp.md` (`[create]`, drift report-only)
Required sections: what this is about, prime directives, commit trailers. An instance may add
sections of its own; none is drift.

### `system/loaders/<role>.md`
Required sections: key files for this role, project-specific rules/overrides, active work pointers.
Cross-layer consistency (checked against the global loader + `kensaiapp_structure.md`):
- Key files must not include the pipeline-intake or journey paths `kensaiapp_structure.md` defines (the per-project pipeline intake §2; the per-project `journey/` §2; the instance `system/nemawashi/` §1) — those are picked up deliberately, not role key-file reads.
- If the overlay defines an on-invocation section, it must not duplicate what the global loader already reads or contradict the global loader's prescribed reads.
- No `qa.md` overlay: qa is **global-only** (fork-invoked, no prefix) — its entire definition lives in `core/roles/loaders/qa_global.md`; qa has **no app-level loader and no context** (the only per-role context setup stamps is the per-project PM context; qa has none).

### `system/projects/<name>/contexts/CONTEXT_PM.md` — per-project PM context (`[create]`, drift report-only)
The **only** per-role context setup stamps (the thirteen non-PM prefix-invoked roles are stamped with none;
qa has none). A hand-maintained `system/contexts/CONTEXT_<ROLE>.md` an overlay reads is the instance's,
stamped by nothing and not drift, its one skill-written section included —
`kensaiapp_structure.md` § *Role layer*. Stamped from `templates/context_template.md`; created on Init
if missing, **never auto-overwritten** (lifecycle-written by `tobiishi-open` / `tobiishi-seal`).
Holds **one item** — this project's current change from the PM's view. Drift (report-only): the single "current change — PM view" item absent, or the file still carrying
the retired four-section instance-wide shape (current state / recent decisions / next task / key source
files).

### `system/projects/<name>/project.md`
Required field: `Product path:` (the project→product binding). Drift: `Product path:` absent. The other
fields (`Source material`, `Type`, `Manages`, `Execution type`, `Package slug`, `Test command`,
`Setup command`, `Languages`, `Parallelism`) are **not** drift-checked.

### Instance + per-project doctrine files (`[create]`, stamped verbatim from templates)
Covers `system/doctrine/{kensaiapp_doctrine,ai_responsibility,doctrine_structure}.md` (instance)
and `system/projects/<name>/doctrine/{<project>_doctrine,ai_responsibility}.md` (per-project).
These are `[create]` — drift is **report-only** (never auto-modified).
Drift: a **host-absolute `~/.claude/…` path** present anywhere in the body.
> The instance domain doctrine must be the **fixed** filename `kensaiapp_doctrine.md` — a project-named
> file (`tracker_doctrine.md` etc.) at instance level is caught as a §1 structural gap (the fixed name is
> missing) + the legacy file surfaces as a rename candidate, not content drift.

### Docker sandbox files (`system/sandbox/Dockerfile`, `run.sh`, `DOCTRINE.md`, `scripts/sandbox-launch.sh`)
Drift: any unsubstituted placeholder still present — `<project>`, `<image-name>`, `<network-name>`.

### `.gitignore`
**`.claude/` is tracked normally** — there is **no `.claude/*` blanket-ignore and no `!.claude/...` whitelist**. The single Claude Code entry is `.claude/settings.local.json` (machine-local overrides only).
Drift: the `.claude/settings.local.json` ignore line missing. Additionally, flag a **legacy `.claude/*` blanket-ignore** (with its `!.claude/...` whitelist lines) if still present.
Fix: append the `.claude/settings.local.json` line if missing. **Removing the legacy blanket is report-only** — `[special]` is append-only; the audit flags the stale blanket but Product performs the removal.

### `.claude/settings.json` — project Claude Code config (`[create]`, drift report-only)
Committed project config: the hooks wiring, and nothing else. Permissions and the `worktree` setting go in `.claude/settings.local.json`. `[create]` — created on Init if missing, **never auto-overwritten**. A satellite's is the exception: `link_satellite.py` writes it from its host's. Drift is **report-only**:
- A top-level key other than `hooks` — a `permissions` or `worktree` key is the machine owner's, and belongs in `.claude/settings.local.json`.
- **Orphan hook** — a script in `.claude/hooks/` not wired under `hooks`; or **dangling wire** — a
  `hooks` entry referencing a script **absent** from `.claude/hooks/`.
- A hook `command` uses a **hardcoded interpreter path** (e.g. `/Users/…/venv/bin/python`) instead of
  `python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.py"`.

### `.claude/hooks/<name>.py` — vendored hook scripts (`[create]`)
Stdlib-only, portable, no host paths. `[create]` — created on Init if missing; never auto-modified.
Drift (**report-only**): a hook file present but **not referenced** by `.claude/settings.json`, or a
host-absolute `/Users/…` path present in the script body.

### `.claude/settings.local.json` — external-product grants (`[special]`, host-local, gitignored)
Machine-local overrides only — **never committed**. The drift class here is the **external-product directory grant**: `project.md` `Product path:` is the single source, `permissions.additionalDirectories` is the derived grant.
Drift: (a) **missing grant** — a project whose `Product path:` is **absolute** and names its own repo (external — an absolute path inside the instance's repo needs no grant) with no matching entry in `permissions.additionalDirectories`; (b) **orphan grant** — an `additionalDirectories` entry no project's absolute `Product path:` claims. In-repo (relative) products need no grant.
Fix: **missing grant is auto-filled** — add the absolute path to `permissions.additionalDirectories` (merge, never clobber the user's own `allow`/other entries; create the file/key if absent). **Orphan grant is report-only** — Product confirms the external product was intentionally removed before any entry is deleted.

### Canonical-projection currency (drift class — spans template-owned files)

Some sections **project** a list that is canonically owned by a global doctrine file — they restate it locally. The audit loads the canonical source **fresh on each run** and verifies the projection enumerates every current entry. Flag content drift for any source entry absent from the projection (and any projection entry no longer in the source):

> "`<file>` § `<section>` out of sync with `<canonical source>` — missing `<entry>`."

| Projection (file § section) | Canonical source | Currency rule |
|---|---|---|
| `AGENTS.md` § loader map | the **prefix-invoked** role set — standard roles minus fork-invoked roles (exclude `qa`: it is forked by a producing role, never opened by a `qa:` prefix) | one `<role>:` entry per prefix-invoked role |
| `AGENTS.md` § direction and journey | `<CORE>/doctrine/setup/kensaiapp_structure.md` §1 (instance app-level — `system/michi.md` declaration + `system/nemawashi/` seedbed + `system/shukuba/` router station) | one entry per app-level journey path — the three named; the upkeep register is not a journey item and takes no entry |
| `<CORE>/templates/project-templates/setup_seed_template.md` § Stations | `<CORE>/doctrine/setup/setting_up_a_project.md` § The flow at a glance | one station per row of the station table, in the same order, naming the same skill |

The third row checks the **template**, not the seeds stamped from it. A stamped
`journey/nemawashi/<date>_define-the-product.md` is a recommendation the owner may edit or delete
(`kensaiapp_structure.md` §2), so a per-project copy that diverges is the owner's call, not drift.
The template is where setup's copy of the sequence lives, and it is the one that must stay current.

**Add a row only when a new *kind* of projection is introduced.**
