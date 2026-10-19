# kensaiapp instance — routing

This file is the same in every kensaiapp instance. It carries the routing — the loader map, the
journey paths, the commit format and the doctrine pointers — and nothing that is true of one
instance only. **What this instance is** — its identity, its prime directives and its own standing
statements — is `kensaiapp.md`, beside this file. Read it before acting on a task.

`kensaiapp.md` is stamped from `<CORE>/templates/kensaiapp_md_template.md` when an instance is
created (`<CORE>/doctrine/setup/setting_up_an_instance.md` § The steps, in order). A clone that has
none has nothing for the import line below to load: write it from that template before working in
the clone.

@kensaiapp.md

Where the machine also carries a user-global `~/.claude/CLAUDE.md`, it applies on top of this file —
but a kensaiapp never requires one.

Before acting on a task, consult `<CORE>/doctrine/task_map.md`. Read every doctrine file it routes
for the operation before the first write or command that performs it. This includes staging,
committing, merging, changing version markers, and working in a worktree.

## Loader map

`<role>:` prefix → `system/loaders/<role>.md` (read on session open). Each is a thin overlay naming
what is true of this instance, which then points at the posture body in
`<CORE>/roles/loaders/<role>_global.md`.

- `cpo:`            → system/loaders/cpo.md
- `cto:`            → system/loaders/cto.md
- `cdo:`            → system/loaders/cdo.md
- `architect:`      → system/loaders/architect.md
- `tech-lead:`      → system/loaders/tech_lead.md
- `developer:`      → system/loaders/developer.md
- `content-manager:` → system/loaders/content_manager.md
- `content-editor:` → system/loaders/content_editor.md
- `product-owner:`  → system/loaders/product_owner.md
- `pm:`             → system/loaders/pm.md
- `principal-pm:`   → system/loaders/principal_pm.md
- `principal-architect:` → system/loaders/principal_architect.md
- `scrum-master:`   → system/loaders/scrum_master.md
- `senior-engineer:` → system/loaders/senior_engineer.md

(qa is fork-invoked, not prefix-invoked — no entry. `teacher:` is global-only — `<CORE>/roles/loaders/teacher_global.md`, no instance overlay. `ppm:` is an accepted alias for `principal-pm:`, resolving to the same overlay — the one abbreviation, so every other prefix spells its own loader file.)

## Direction and journey

Declarations set the bearing; the journey is the work moving along it. Neither is a queue.

- App-level: `system/michi.md` (道 Michi — the Way, a declaration) + `system/nemawashi/` (根回し — the seedbed) + `system/shukuba/` (宿場 — the router station that coordinates projects pushing on one thing).
- Per-project (`system/projects/<name>/`): `agari.md` (上がり — the product's "done", a declaration) + `journey/` (nemawashi · shukuba · tobiishi).

No instance inbox/backlog, and no `system/queues/` — both retired. The model: `<CORE>/docs/michi_agari.md`.

**Travelling it is written down** — the same file's § *How we work — walking a project's journey* is the
loop, and § *Who owns each step* is who does what. Read it before picking a seed, opening a station or
closing one. The moves it names are the PM's, except the close and the retire, which are the **Scrum Master**'s
(the PM closes a station only when its park finds it already reached),
and the answer to a retired seed, `nemawashi-refine`, which is the **Principal PM**'s —
`<CORE>/roles/loaders/pm_global.md` § *Responsibilities*, `<CORE>/roles/loaders/scrum_master_global.md`
and `<CORE>/roles/loaders/principal_pm_global.md` § *Retiring a finished seed* are those seats' own
statements of them.

## Commit format and git operations

Both per `<CORE>/doctrine/governance/commit_format.md` — the canonical body for the commit **message**
(trailers, enforced on every commit by `<CORE>/githooks/commit-msg`) and for the **operations** that
produce it: the staged-set guard, never `cd` to run git, and a destructive operation names an explicit
SHA. Whether this instance adds trailers of its own is `kensaiapp.md` § *Commit trailers*.

## Doctrine

Inline stubs; canonical bodies on disk. How a body meets `<CORE>`'s is that file's own to state, and
the three differ: `ai_responsibility.md` § 0 fixes precedence — core dominates, and this layer adds
or tightens a boundary, never relaxes one. `doctrine_structure.md` extends core's meta-layer rather
than restating it, and the domain doctrine has no core base to layer over at all.

App-level (`system/doctrine/`):

- Domain doctrine     → `system/doctrine/kensaiapp_doctrine.md`
- AI responsibility   → `system/doctrine/ai_responsibility.md`
- Doctrine structure  → `system/doctrine/doctrine_structure.md`
- Writing bar         → `system/doctrine/writing_bar.md`

Per-project (`system/projects/<name>/doctrine/`):

- Domain doctrine     → `<project>_doctrine.md`
- AI responsibility   → `ai_responsibility.md`

What state this instance's own doctrine files are in is `kensaiapp.md`'s to say.

Core states it and a lower layer may tighten it, never relax it: **where taste appears** — the
aesthetic call is made in the run that owns it, and a document upstream of that run states the
requirement rather than the preference — `<CORE>/doctrine/governance/where_taste_appears.md`. What
an instance or a project may add to it, and what it may not, is that file's § A lower layer may
tighten this, never relax it.

Core-only (no instance layer): **versioning** → `<CORE>/doctrine/governance/versioning.md` — who
reads a file decides: model-facing artifacts (doctrine, prompts, launchers, scripts, workflows,
model-read templates) carry a `version:`; script-stamped templates carry none, because their bytes land
verbatim in the instance. Bump semantics (patch/minor/major + the enumeration clause) live there
too — except for a **skill**, whose marker and bump belong to the kaizen layer,
`<CORE>/doctrine/kaizen/skills.md` § The version's three digits, reading the same three digits.

## Skills and agents

For task-specific workflows, inspect and follow the relevant instructions under:

- `.claude/skills/`
- `<CORE>/../skills/<group>/.claude/agents/` — which group holds each agent is `<CORE>/doctrine/setup/kensaiapp_structure.md` § Agents. A session has an agent once it adds that group with `--add-dir` / `/add-dir`.
- `.claude/agents/` — where this instance holds an agent of its own. A launched run takes it in place of the group's agent of the same name.
