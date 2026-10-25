---
version: "2.193.2"
---

# kensaiapp-instance structure manifest

Declares the expected file tree for a **kensaiapp instance** — a workspace that hosts one or more
**projects**.

Consumed by whatever stamps a kensaiapp:
- **Per-project (§2)** — `project-stamp` creates the folder tree from `templates/`.
- **Instance-level (§1)** — **`core/tools/spawn_satellite.py`, for a shared-core satellite.** It stamps
  the §1 files from `templates/`; § Templates layer names exactly which, and they are the whole of what
  it reads. It is the *code* replacement for the withdrawn `kensaiapp-spawn` **skill** (`f6d5c0a`),
  whose prose steps could assert something false with nothing to evaluate the assertion — which is how
  that skill's one run carried a sibling instance's own facts into a fresh instance.
  A **standalone** instance — one carrying its own `core/` — still has no stamper and is built by hand
  from `templates/`; `spawn_satellite.py` never creates a local `core/`, by design.
- **Audit** — **no executor today.** Nothing diffs this manifest against disk, which is why the
  enumerations below drift: with nothing counting them, each list is a floor rather than an inventory.

> **See also — the ordered setup flow.** This manifest declares *what* an instance's tree
> contains. The ordered flow for setting up a project — scaffold (which stamps the setup seed)
> → walk that seed's stations — lives in `setting_up_a_project.md`, its sibling in this folder.

> **Three scopes.**
> 1. **Instance-level** — shared, cross-project structure: doctrine, role definitions, app-level queues.
> 2. **Per-project** — one folder per project under `system/projects/<name>/`, owning that project's
>    Agari (`agari.md`) + journey (its change-work in motion) + doctrine, and pointing at its product.
> 3. **Product** — what a project builds (`docs/fdr.md`, `docs/adr/`, `docs/nfdr.md` + code); lives **inside or outside**
>    the instance, bound by `Product path:` in `project.md`.
>
> *Organizing principle: decision records travel with the product; work-in-progress travels with the
> project; the project points at its product by path.*

> **Design principle — harmless.** A public kensaiapp **only creates files and sets pointers** (paths in
> `AGENTS.md` / loaders / `project.md`). It **never manipulates the user's environment or global Claude
> Code config** — no `CLAUDE_CONFIG_DIR`, no forced writes into the user's `~/.claude`, no assumption about
> how they launch Claude. Every system-touching skill obeys this.
>
> **Design principle — `<CORE>` indirection (core is referenced, never hardcoded).** The core root
> is bound in exactly one place: the `CORE=` value in the instance's untracked `.env` (template:
> `.env.example`; default `core/` — the vendored core, so a fresh clone is ready-to-run with no `.env`).
> The `resolve_core.py` SessionStart/SubagentStart hook resolves it once and injects the resolved path
> into session context. Every file that points into
> core — skills and their own `prompts/`, `core/prompts/*.md`, `system/loaders/*.md`, `system/projects/*/contexts/CONTEXT_PM.md`, `system/CROSS_ROLE.md`,
> `skills/*/.claude/agents/*.md` and an instance's own `.claude/agents/*.md` — references it **only** through the `<CORE>` token, **never** a literal `core/…`
> and **never** a host-global `~/.claude/…`.
> This is what lets the core root move (rename, relocate, centralize) by editing one line in `.env`. **Drift-checks
> (instance-wide):** a literal `core/…` path, or any `~/.claude/…` path, in a core-referencing file is a
> defect. (The harmless principle forbids `~/.claude/…`; this principle forbids the hardcoded `core/…`.)
>
> Every entry (or its section heading, when the whole group shares one) carries exactly one tag. What each
> disposition *does* — and the per-file content drift-checks — is defined in `setup_scope.md`; that file
> does **not** re-list this tree.
> - **`[hybrid]`** — create if missing; on fix, offer the a/b/c choice (template-owned, drift-checked).
> - **`[create]`** — create if missing; never overwrite, never delete.
> - **`[template]`** — the template's bytes, the same in every instance: create if missing, and rewrite from the template whenever the two differ.
> - **`[user]`** — never created or modified by setup, in any mode (user-/pipeline-authored).
> - **`[special]`** — host-local special files (`.gitignore`, `.claude/settings.local.json`): create if missing; per-file fix behavior (append-only / grant auto-fill) defined in `setup_scope.md`.

---

## 1. Instance-level (all instances) — shared across projects

### Root
- `AGENTS.md` — `[template]`, stamped from `templates/agents_md_template.md` — the instance's
  **routing**: the loader map, the direction-and-journey paths, the commit-format pointer and the
  doctrine stubs, all through `<CORE>`. It carries nothing true of one instance only, so it is the
  same bytes in every instance and `spawn_satellite.py` rewrites it on a re-run; an instance never
  edits its own copy. It names the identity file beside it twice — in a sentence, and as a bare
  `@kensaiapp.md` import line — because one provider expands an import and another reads only the
  sentence.
- `kensaiapp.md` — `[create]`, stamped from `templates/kensaiapp_md_template.md` — the instance's
  **identity**: its title, what it is about, its prime directives, its own commit trailers, and any
  standing statement true of this instance alone (a host's satellites, the state its own doctrine
  files are in). Filled at instance setup by `kensaiapp-michi` and the instance's from then on.
- `CLAUDE.md` — `[template]`, stamped from `templates/claude_md_template.md` — one line, the bare
  import `@AGENTS.md`, and nothing else. It is Claude Code's own entry point: with it in place the
  harness loads `AGENTS.md` through the import, and `kensaiapp.md` through `AGENTS.md`'s, rather than
  falling back to `AGENTS.md` and announcing the fallback at every session start. It states no
  routing and no identity of its own — anything written here belongs in one of the two files it
  leads to. `core/tools/check_satellites.py` names an instance whose copy is missing or has grown.
- `.gitignore` — `[special]`, stamped from `templates/gitignore_template.md`
- `.env.example` — `[create]` — tracked template for the untracked `.env` (`CORE=` binding; copied per machine via `cp .env.example .env`)
- `.providers.toml.example` — `[create]` — tracked template for the untracked `.providers.toml` (the provider each unforced launch goes to, read by `core/tools/providers.py`; copied per instance via `cp .providers.toml.example .providers.toml`, and to a new satellite by `core/tools/spawn_satellite.py`)
- `.telemetry.env` — `[user]` — tracked, and read on a host only: the one line naming the
  telemetry package's command for a launch whose environment holds no
  `KENSAIAPP_TELEMETRY_COMMAND`. `core/tools/telemetry_command.py` reads it as data, from the
  source host of the core a launch runs on, so a launch from a pin or for a satellite reads its
  host's file and a satellite needs none. The command's name is written there and in no file under
  `core/`. Without it, a launch whose environment names no command runs uninstrumented.
- `claude-design-instructions.md` — `[create]`, stamped from
  `templates/claude_design_instructions_template.md` — the instance's entry point into Claude Design,
  read by both of that tool's routes (a linked-folder run from its setup form, and a `/design-sync`
  run in this repository). Root because the tool's file selection starts from the connected folder.
  It **names no product** — it resolves the one it is told from `system/projects/<name>/project.md`
  `Product path:` — and it **enumerates no input filenames**, naming folders and telling the run to
  list them. `[create]` because the instance edits its own copy: one satellite's took eight commits to
  reach the shape the template carries, and a stamper that overwrote it would discard that. It points
  at **no path outside the instance folder**, so it is the one file here with no `<CORE>` reference
  by design — the linked-folder route copies selected files out of the connected folder and follows
  no path leading out of it (`setup/shared_core_instance.md` § What is shared: a satellite has "no
  local `core/`" of its own, so a core pointer here is dead for that route).
- `README.md` — `[user]` — the instance's public-facing summary. A *summary*: the load-bearing identity
  statements live in `kensaiapp.md` § "What this is about" and `system/michi.md`, which it points at.
  Authored at instance setup and reconciled by `kensaiapp-michi`; setup never writes it.
- `system/satellites.md` — `[user]`, **host-only** — the roster of the instances that bind `<CORE>`
  to this one, with each one's path and kind, and § *Names a release must not carry*: the names no
  shipped file may carry beyond the satellites' own — a platform, the host's own name, a retired
  product or instance — and § *Projects a release ships*: the example projects a release carries
  whole, which the same check scans for those names. They are kept here because this file never ships, and
  `core/tools/check_vendor_neutrality.py` reads them, with every satellite's name, from here. Not a per-instance `[create]` item: an instance with no
  satellites has no roster, and a satellite never has one (it has no satellites of its own), so its
  absence is not drift. The rule it answers to — why placement is free and therefore has to be
  recorded — is `setup/shared_core_instance.md`, which owns it.
- `about/` — `[user]`, **host-only** — files this host stores and releases but **another instance
  manages**: documents that describe kensaiapp, written by a satellite's project and handed over to
  this host. Each one is handed over byte for byte, version line included, and is **never edited
  here**; a defect found in one is reported back to the instance that manages it, which hands over a
  new version. A release cut from this host ships the folder at the same path, unchanged, so the
  managing instance can check its own copy against the stored one with a plain `diff`. **One file
  is the exception: `about/README.md` is the public repository's README**, and the release places it
  at its own root as `README.md`, unchanged, with none left under `about/`. It is stored here, not at
  this host's root, because the root `README.md` is this host's own and is not handed over. Neither
  existing home fits: `core/docs/` would make these files core's own machinery, and root `docs/` is
  the workbench, which a release does not carry. Which instance manages which file is that instance's
  own record — its placement record names each handover by file, version, path and commit — not this
  host's. Not a per-instance `[create]` item: a satellite never has one, and a host nothing has been
  handed to has none, so its absence is not drift.
- `skills/` — `[create]` — the **grouped** skills root: `skills/<group>/.claude/skills/<name>/`, where
  `<group>` is one folder holding the skills that are read together, and `<name>/` beneath it is an
  ordinary skill directory identical in shape to a flat one under `.claude/skills/<name>/`. The two
  layouts coexist and name the same kind of thing at two depths — the flat root is what the harness
  indexes first, and a group is where a skill lives once it has moved out of it. This host's flat root
  holds none: every one of its skills is grouped, so a satellite is linked to neither layout's flat
  form (`setup/shared_core_instance.md`). A host that has
  created no group has no `skills/` at all, and that is not drift: `core/tools/link_satellite.py`
  states the same posture for a satellite — *"A host with no root `skills/` — one that has created no
  group — is not drift"*. Resolved by `core/tools/skill_path.py`, which takes a skill's name and answers with
  its directory under either layout; scoped by `core/tools/written_forward.py`'s `SCOPED_ROOTS`
  alongside `.claude/skills/`; and ignored, per group, by `.gitignore`'s
  `skills/*/.claude/skills/*/evals/workspace/`. Mirrored into a producer satellite as a tree; not linked
  into a consumer at all, whose launchers look a group up under the host root (`<CORE>/..`) and grant
  it (`core/launchers/skill/launcher.sh` § A GROUPED SKILL'S GROUP IS GRANTED;
  `setup/shared_core_instance.md`).
- `docs/proposals/` — `[user]` — one of **two** homes an ad-hoc plan can have; this one is for a plan
  with no project journey to hold it. One folder per proposal, `docs/proposals/<slug>/`, holding
  `ad_hoc_plan.md` and its reasoning (`rationale.md` / `research.md`); the ad-hoc flow filed its
  `code-integrity-report.md` beside them, keyed by the plan's `plan-id:` frontmatter. Sealed
  proposals are `git mv`d whole to `docs/proposals/archive/<slug>/` (park-don't-strike, same move as a
  journey `trail/`). Written by `agent-invoke` deliverables. **A proposal need not be a plan**
  (the owner's call, 2026-10-10): research or an idea for a satellite to take up lives here too, as
  `docs/proposals/<slug>/research.md` with no `ad_hoc_plan.md`, because this is where the satellites
  look. One of the instance's two root-level `docs/` subfolders —
  distinct from the *product's* `<product>/docs/` (§3) and from `core/docs/`.
  **The other home is a project's journey — the 宿場 Shukuba station whose work the plan describes,
  inline.** Not the 根回し Nemawashi seed, and not a file beside either: the owner's call of
  2026-08-31, which overturns the 2026-08-21 ruling that put it in the seed. **A plan and a station
  have the same lifetime and a plan and a seed do not** — a plan is the task decomposition of one leg,
  a station is created when that leg opens and moves to `shukuba/trail/` when it closes, so the plan
  retires with the work it describes and sits permanently beside the reached-when it was built
  against. A seed outlives every station on it, so a seed-homed plan is overwritten once per leg and
  the plan actually built from survives only as a diff. The station already holds the rest of one
  leg's detail; the seed holds the idea, the rulings and the route.
  `core/templates/journey_nemawashi_template.md:21` — "There is no separate plan folder — the
  checklist *is* the plan, living with the idea" — is not the counter-argument it was read as in
  2026-08-21: at `:19-21` it answers where the list of **legs** lives, not where one leg's task list
  does. Both prior records stand as records and are annotated, not rewritten.
  A plan goes here, under `docs/proposals/`, when it has no station to live in. "Archived" differs
  by home: a `docs/proposals/` plan is archived by the `git mv` above; a journey-homed plan retires
  with its station through `shukuba-retire`, run by the **Scrum Master**, which also ticks the seed's
  item. **Nothing runs a plan from either home now.** `ad-hoc-flow` — the launcher and workflow that
  did, over the `ad-hoc-implementation` skill — retired on 2026-09-18, the owner's call; the last
  commit holding all three is `a01eb180`
- `docs/reviews/` — `[user]` — one folder per outside review of this instance,
  `docs/reviews/<YYYY-MM-DD>_<reviewer>-<slug>/`, holding `report.md` (what was asked and what came
  back, including the correction history) and `conclusions.md` (the owner's calls — accepted,
  declined, and what became a seed). Optional and occasional: an instance that has never been
  reviewed has no folder, so its absence is not drift. Distinct from a **ratification verdict**,
  which judges one skill version against its own evidence and is owned by the managing project's
  `docs/` (`kaizen/ratification.md`); a review here judges the instance from outside and answers to
  nothing but the record. First folder: `2026-08-03_perplexity-outside-review/`.

- `docs/findings/` — `[user]` — one file per run that found something wrong with **kensaiapp itself**
  rather than with a product: `docs/findings/<YYYY-MM-DD>_<slug>.md`, each finding naming the piece of
  machinery it is about and what is wrong with it. **Any layer counts** — a skill, a prompt, a
  template, a loader, a doctrine file, a hook, a launcher, a workflow, a tool under `core/tools/` — and
  so does the **absence** of one, where work a run had to do by hand belongs to a tool that does not
  exist. A defect in something the run **executed** counts as much as one in a file it read. Enumerated
  rather than left to "machinery" alone because a run reads the list as the bound on what it may file,
  and a narrower list silently drops what it found (the owner's call, 2026-09-12, on a run that had a
  tool's wrong output in hand and filed it as a parenthetical). Root, because no project owns those
  files. A resolved finding sits one level down, at `docs/findings/resolved/<YYYY-MM-DD>_<slug>.md`,
  under the name it was filed with. **Who writes it, that a satellite writes to its own and never to
  the host, that the host's reading of it is by hand, that a file here is never the repair, and when
  and how a finding moves to `resolved/` are `governance/found_while_walking.md` § *Where a surfaced
  defect is written down*'s** — this row owns the path and what an entry names, and no more.
- `docs/seeds-from-idea/` — `[create]` on demand — an idea cut's brief when the seeds it produced land in
  the instance seedbed, or when the cut was left to decide the owner: `<YYYY-MM-DD>_<slug>_brief.md`, and
  its `_report.md` beside it.
  A cut whose owning project is named keeps its brief in that project's `docs/seeds-from-idea/`
  instead (§2).

### Native `.claude/` layer — the instance's own project-scoped Claude Code config

Project-scoped configuration (**not** `~/.claude`) — harmless per the design principle above: it is the
project's *own* `.claude/`, never the user's global config.

- `.claude/settings.json` — `[create]` — committed project config: the hooks wiring, and nothing else.
  Permissions and the `worktree` setting are the machine owner's own, and go in
  `.claude/settings.local.json` — the owner's call, 2026-10-08. Drift-reported (see `setup_scope.md`).
  Setup never overwrites it. A satellite's is the exception: `core/tools/link_satellite.py` writes it
  from the host's and rewrites it whenever it differs.
- `.claude/settings.local.json` — `[special]` — host-local machine overrides, **gitignored, never
  committed**; setup auto-fills the external-product directory grant (per-file behavior in `setup_scope.md`).
- `.claude/hooks/permission_mode_reminder.py` — `[create]` — UserPromptSubmit hook, vendored stdlib-only:
  advisory when a prompt mentions a bypass-mode flag.
- `.claude/hooks/resolve_core.py` — `[create]` — SessionStart/SubagentStart hook, vendored stdlib-only:
  resolves `<CORE>` from `.env` (`CORE=`, default `core/`) and injects the resolved path into session
  context; also exports `CORE` for subsequent Bash via `$CLAUDE_ENV_FILE`, and wires `core.hooksPath` to
  `<resolved-core>/githooks` when unset (guarded — see the git-native hooks layer below).
- `.claude/hooks/development-bash-approve.py` — `[create]` — PreToolUse/Bash hook, vendored stdlib-only:
  auto-approves a Bash call only when every command head is in a conservative safe set (unknown or
  dangerous ones defer to the normal prompt; `deny` rules still override), so a long unattended run
  completes without mid-run prompts and without bypass mode.
- `.claude/hooks/written_forward_guard.py` — `[create]` — PreToolUse/`Edit|Write` hook, vendored
  stdlib-only: refuses a write that would put a written-forward violation on disk, importing the
  checker (`written_forward.py`, below) through the resolved core.
- `.claude/hooks/_task_map.py` — `[create]` — **not a hook**: the compatibility import through
  which the two Claude salience hooks resolve the instance's `<CORE>` and reach
  `<CORE>/tools/task_context.py`. No `main()`, never named in `settings.json`; the leading underscore
  says so. It owns no parser or context text.
- `.claude/hooks/task_map_salience.py` — `[create]` — SessionStart/SubagentStart hook, vendored
  stdlib-only: injects **every route in the task→doctrine map**, derived from the table at run time,
  so a session knows a doctrine governs its task before it acts. It carried a hand-picked eight of
  the map's routes until 2026-09-02; that list is what kept `found_while_walking.md` unsurfaced.
  Carries a `KENSAIAPP_TASK_MAP` sentinel. The parser and rendered block come from
  `<CORE>/tools/task_context.py`, shared with Codex. Fail-open.
- `.claude/hooks/manifest_salience.py` — `[create]` — SessionStart/SubagentStart hook, vendored
  stdlib-only: injects **this file's own section index**, computed at run time, so a run can reach the
  section governing where its output belongs instead of reading 900 lines. Carries a
  `KENSAIAPP_STRUCTURE_MAP` sentinel. Fail-open.
- `.claude/hooks/standing_rules_salience.py` — `[create]` — SessionStart/SubagentStart hook, vendored
  stdlib-only: injects the routes `task_map.md` marks `unprompted` as **standing rules** rather than
  as routes — the class whose trigger a session fails to notice rather than aims at, which a routing
  index cannot deliver because consulting it is the step that never happens. Names each rule and its
  doctrine; never restates one. It then carries § The rules of `governance/talking_to_the_owner.md`
  whole, read from that file each time, under a `KENSAIAPP_OWNER_REPLY` sentinel. Carries a
  `KENSAIAPP_STANDING_RULES` sentinel. The rendered block
  comes from `<CORE>/tools/task_context.py`, shared with Codex. Fail-open.
- `.claude/hooks/brief_anchor_guard.py` — `[create]` — PreToolUse/`Agent` hook, vendored stdlib-only:
  refuses a subagent spawn whose brief cites text that is not at the lines it names, names no model
  tier for `delegate` (the one agent whose tier is chosen per run — no agent file carries a `model:` line), or names a tool that agent was not granted. Denies before the run
  starts; asserts nothing it cannot prove; fail-open.
- `.claude/hooks/subagent_stop_notify.py` — `[create]` — SubagentStop hook, vendored stdlib-only:
  posts a finished subagent's own closing message through `$KENSAIAPP_NOTIFIER`, so a delegated run
  reaching its end no longer depends on the spawning session remembering to relay it. Matched to one
  agent type (`delegate`) in `settings.json` and again in the file, on a measured volume estimate —
  every agent type is ~20 spawns a day in this instance where `delegate` is ~6. Writes nothing to
  stdout and always exits 0 on every path: `SubagentStop`'s exit code 2 *prevents the subagent from
  stopping*, so fail-open here means fail-open harder than a guard's. No host-global notifier
  default, because every satellite runs this file from the host.
- `.claude/hooks/context_cap.py` — `[create]` — PostToolUse/`Bash` hook, vendored stdlib-only: once
  a run's current context is over `$KENSAIAPP_CONTEXT_CAP`, tells it to finish the task in progress,
  make the pause commit and end, so a chain can relaunch a fresh developer after that task. Silent
  when the variable is unset or not a positive integer, which is every session but the chain's
  implementation step. Reads the gauge through the telemetry gateway (`telemetry_gateway.py`) in the
  resolved core, never a path beside itself. Where the Python running it cannot import the telemetry
  package, it runs itself once more under `~/.kensaiapp/venv/bin/python`, where that interpreter
  exists. Where neither can, and the cap is set, it prints one line on stdout saying the cap
  needs the telemetry package and this run is not capped. Every other failure stays silent.
  Fail-open, exit 0 on every path, because every satellite runs this file from the host.
- `.claude/hooks/read_first_guard.py` — `[create]` — PreToolUse hook on every tool, vendored stdlib-only:
  refuses an agent run's calls until the run has read the files its agent file tells it to read
  first. `Read`, `Grep` and `Glob` are never refused. Every other call the run makes is refused, from
  the first one on, while any of those files has not been named by a `Read` call in the same session.
  A `Grep` or `Glob` that touches a file does not count as reading it. The refusal names each file
  still unread. A call with no agent, or whose agent has no agent file, is never refused. Fail-open:
  on any error the hook prints nothing and leaves the call alone.

> **Hooks are stdlib-only — no venv.** Vendored hook commands invoke `python3` with a project-relative
> `${CLAUDE_PROJECT_DIR}` path — `python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.py"` — never a
> hardcoded interpreter path. A satellite's `.claude/settings.json` is the one exception to that form.
> `core/tools/link_satellite.py` writes each of its commands with the host's absolute `.claude/hooks/`
> path in place of `${CLAUDE_PROJECT_DIR}/.claude/hooks/`, because a satellite holds no hook scripts
> of its own.
>
> **Init vs Audit for this layer.** **Audit** enumerates these paths and gap-reports a missing/dangling
> layer today. **Init auto-creation** of the `.claude/` layer (stamping `settings.json`, vendoring the
> hook scripts) awaits vendored hook sources + a settings template — a follow-up increment.

#### Agents — fork-invocable subagents (`skills/<name>/.claude/agents/`)

`[create]` — vendored role/pipeline subagents; create if missing, never overwritten (a user may customize
one). Each is a thin **plumbing** file: front-matter (`name` / `description` / `tools`) plus a load-chain
that points the fork at its operating contract. On vendoring the chain is **repointed off the host global**:
core paths go through `<CORE>` (resolved at session start by the `resolve_core.py` hook from `.env` — same
indirection the flow-* skills use, so a moved/renamed core root only changes one line in `.env`), and
overlay paths are app-level under `system/`:
- `<CORE>/roles/loaders/<role>_global.md` — global posture
- `system/loaders/<role>.md` (via `AGENTS.md`'s Loader map) — instance overlay + on-invocation context read
- `<CORE>/roles/CROSS_ROLE.md` + `system/CROSS_ROLE.md` — cross-role contract (core + overlay)

**Drift-checks:** per the instance-wide `<CORE>`-indirection + harmless principles above — a literal
`core/…` path or any `~/.claude/…` path in a vendored agent is a defect.

**Adding the agent for a *role* is not a standalone act** — the file is one step of a closure that
includes the posture pair, the overlay, and four registration surfaces this file is only one of.
`adding_a_role.md` owns that order, and owns how the plumbing body is derived (stamped from
`templates/role-templates/agent_template.md`, not authored and not copied from a sibling).

Nineteen agents — each in the group of its own name except `delegate`, all fork-invocable:
- `skills/cpo/.claude/agents/cpo.md`
- `skills/cto/.claude/agents/cto.md`
- `skills/cdo/.claude/agents/cdo.md`
- `skills/architect/.claude/agents/architect.md`
- `skills/tech-lead/.claude/agents/tech-lead.md`
- `skills/developer/.claude/agents/developer.md`
- `skills/senior-engineer/.claude/agents/senior-engineer.md`
- `skills/content-manager/.claude/agents/content-manager.md`
- `skills/content-editor/.claude/agents/content-editor.md`
- `skills/product-owner/.claude/agents/product-owner.md`
- `skills/pm/.claude/agents/pm.md`
- `skills/principal-pm/.claude/agents/principal-pm.md`
- `skills/principal-architect/.claude/agents/principal-architect.md`
- `skills/scrum-master/.claude/agents/scrum-master.md`
- `skills/qa/.claude/agents/qa.md` — global-only (no `system/loaders/qa.md` overlay; its load-chain step 2 self-skips)
- `skills/kensaiapp-auditor/.claude/agents/kensaiapp-auditor.md` — pipeline auditor, no loader chain (task-driven; launched by the chain's audit step — `core/launchers/chain-development/launcher.sh` → `core/tools/chain_development.py`)
- `skills/kaizen-fix-author/.claude/agents/kaizen-fix-author.md` — kaizen fix author, no loader chain (task-driven; spawned by `launch-fix-author.sh`)
- `skills/kaizen-fixer/.claude/agents/kaizen-fixer.md` — kaizen fixer, no loader chain (task-driven; spawned at step 5 to apply an approved fix packet)
- `skills/interactive/.claude/agents/delegate.md` — the owner's one-off delegated work, no loader chain and no pinned model (the spawner resolves the tier per run). Its load-chain has a single step, `<CORE>/roles/delegate_contract.md` — the one agent whose body is not a loader stack, because it holds no posture to load (`authoring_layers.md` § The carriers)

Three of those groups hold an agent and nothing else: `skills/kaizen-fix-author/`, `skills/kaizen-fixer/` and `skills/qa/`. `delegate` is held by `skills/interactive/`, beside `agent-invoke`, the skill that spawns it, so the one grant an interactive session already takes reaches both. Grouped, so a session has an agent only after `--add-dir` / `/add-dir` on its group, `skills/<name>/`. A pinned Claude run carries all nineteen in its `--agents`, whatever group it is granted. When an instance holds its own `.claude/agents/<name>.md`, a launched run takes it in place of the group file of the same name. The host's `.claude/agents/` holds no agent, and a tracked `.gitkeep` keeps it in every clone. No satellite links to it, because each satellite's `.claude/agents/` is its own.

#### Skills — vendored skill definitions (`skills/<group>/.claude/skills/`)

`[create]` — vendored; create if missing, never overwritten (a user may customize one). Each skill is a
folder holding `SKILL.md` plus optional support subfolders (`references/`, `evals/`,
`agents/`, `scripts/`, `assets/`) — the audit checks the skill folder + `SKILL.md`, not the support-file
inventory. A skill that declares an unattended launch also holds a `launcher.md` at its root: the agent,
the argument shape, the fixed prompt and, optionally, the completion
message's reporter and what it reads, all of which `<CORE>/launchers/skill/launcher.sh` reads to start it (§ *Owner-run launcher folder*). The file is the launch's, not the skill's method — adding one changes
no `SKILL.md`. `skills/pm/.claude/skills/tobiishi-open/launcher.md` is the first. A skill a chain launches — all but `companion-self-answer` — also holds `intelligence/<provider>.md`: the model and effort its work runs at, one file per vendor. A skill outside the chains may hold one too; which may, and what reads it, is `<CORE>/doctrine/governance/skill_intelligence.md` § *Scope*. `evidence/` is the versioned record of how the skill behaves, and the host holds none: it is kept in the producer satellite
(`<CORE>/doctrine/engineering/skill_evidence.md`). **Drift-checks:** per the instance-wide `<CORE>`-indirection + harmless principles above — a
core-referencing skill points into core **only** via `<CORE>`; a literal `core/…` or `~/.claude/…` path
is a defect.

The flow family — the change pipeline (9):
- `skills/product-owner/.claude/skills/development-specs/` · `skills/architect/.claude/skills/development-design/` · `skills/tech-lead/.claude/skills/development-plan/` · `skills/content-editor/.claude/skills/development-content/` · `skills/developer/.claude/skills/development-implementation/` · `skills/senior-engineer/.claude/skills/development-code-integrity/` · `skills/pm/.claude/skills/tobiishi-seal/` — the seven producer stages. `development-content` is the Content Editor's step, run between plan and implementation only when the design's `Publishes text:` line reads `yes`, and it writes `change_text.md`. All seven are grouped, each under its seat, so a session reaches one only after `--add-dir` / `/add-dir` on `skills/product-owner/`, `skills/architect/`, `skills/tech-lead/`, `skills/content-editor/`, `skills/developer/`, `skills/senior-engineer/` or `skills/pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/pm/.claude/skills/tobiishi-open/` — the FDR-optional front door: places the `change_request.md`. **Gated to PM posture**, and the only member of this family that is — with a station open it derives the change from that station's reached-when and commits with no owner in the room, which is what earns the gate (§ *A skill that acts unattended gates to its seat* in `authoring_layers.md`). With no station it opens nothing and asks nothing — it reads the project's journey state, names the one next move that state determines, and returns. That is **routing, not refusal**: a project with no route yet is handed one named next action inside itself rather than being turned away, which is what the menu of candidate changes standing here until 2026-09-06 was protecting, and what a menu was the wrong shape for. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/kensaiapp-auditor/.claude/skills/development-audit/` — per-stage fresh-eyes audit (writes `flow_findings/<step>.md`, one file per audited step). Grouped under the agent the chain runs it as — the owner's call, 2026-10-03 — so a session reaches it only after `--add-dir` / `/add-dir` on `skills/kensaiapp-auditor/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher

The security review (1) — beside the flow family rather than in its count, because the chain does not
launch it yet; it joins the family when the chain runs it as a step:
- `skills/senior-engineer/.claude/skills/development-security/` — reviews a change's branch after its code-integrity step: it runs the dependency audit the product's NFDR names, repairs advisories and code holes within the owner's rules, excepts an advisory the product does not reach, and reports the rest for the PM in `security-report.md`. Thin over its own `prompts/rich.md`. **Gated to Senior Engineer posture.** Declares an unattended launch in `launcher.md`, taking `<project> <key>`, with its `intelligence/` beside it, which the skill launcher reads (`<CORE>/doctrine/governance/skill_intelligence.md` § *Scope*); the chain runs it as its `security` step, after `code-integrity`. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/senior-engineer/`

The repair of a red `main` (1) — not a step of the chain's tables; a Senior Engineer runs it on `main` itself, and the chain launches it once when a closing marker's red is no deferral's and the product has an NFDR:
- `skills/senior-engineer/.claude/skills/dependency-repair/` — repairs a product's `main` gone red by itself: on a branch off `main` it runs the dependency audit the NFDR names, answers every advisory by `<CORE>/prompts/senior_engineer_repair_dependencies.md`, writes `system/projects/<project>/docs/dependency-repair/<key>_report.md`, and merges on a green suite. **Gated to Senior Engineer posture.** Declares an unattended launch in `launcher.md`, taking `<project>`, with its `intelligence/` beside it (Haiku on Claude, `gpt-6-luna` on Codex, both medium — the owner's call, 2026-10-24); the chain launches it on a red closing marker no deferral owns, on a product with an NFDR (`core/tools/chain_development.py`), and halts or re-closes the change by its report. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/senior-engineer/`

Shared by every producer skill, in `<CORE>` rather than in a skills root (Read on demand):
- `<CORE>/doctrine/governance/commit_via_builder.md` — the producer-commit-through-the-builder recipe, beside `commit_format.md`. The audit checks the file itself, since the citing skills break without it.

  (The `--no-ff` merge format that `merge-format.md` used to carry retired 2026-07-08 into `core/tools/commit_builder.py merge` — the merge/seal callers now build their merge directly through the builder, so there is no shared merge prose file.)

The journey ops — folder-based journey maintenance (6), grouped by destination:
- `skills/scrum-master/.claude/skills/shukuba-retire/` — close a **reached** 宿場 Shukuba station: move it into its sibling `trail/`, tick the item it was opened from on the active Nemawashi seed, and report whether any item is still unchecked. It asks nothing about what comes next — the next station is `shukuba-open`'s, and the idea's retire is `nemawashi-retire`'s, which this skill names as owed once no checklist item remains. **Gated to Scrum Master posture.** Project-level only — the instance's **router** station (§1) is a different kind and is moved to its `trail/` by hand. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/scrum-master/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/scrum-master/.claude/skills/nemawashi-retire/` — retire a **walked** 根回し Nemawashi seed: move it whole into its sibling `trail/`, restoring nothing, and remove its line from the Principal PM's `## Picked seeds`, in one commit. Mechanical — no report and no judgment; it names `nemawashi-refine` as owed to the Principal PM, and the pick after it. Refuses a seed with an open item or no checklist, one not at the seedbed root, and a seed with a station or change unit still open. **Gated to Scrum Master posture** — the owner's call, 2026-09-24. Project-level only — an instance seed is moved to `trail/` by hand. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/scrum-master/`; a run started by `<CORE>/launchers/skill/launcher.sh nemawashi-retire <project>` is granted that group by the launcher
- `skills/pm/.claude/skills/shukuba-park/` — park an **unreached** station: move it into its sibling `parked/` and leave the seed's checklist item unticked. It asks nothing — the idea's un-pick is `nemawashi-unpick`'s. A station it finds already reached it closes through `shukuba-retire` instead of parking — the one way the PM reaches the close. **Gated to PM posture** — the owner's call, 2026-10-03: a station set down unreached frees the slot the PM's traverse fills. Project-level only — a router station has no `parked/` (§1). Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/pm/`
- `skills/principal-pm/.claude/skills/nemawashi-drop/` — drop a **killed** 根回し Nemawashi idea: move it into its sibling `drop/`, restoring nothing. **Principal PM only**, because it decides whether the program walks an idea at all. Takes the active idea from the root and — the one origin no other journey skill accepts — a candidate from `unpicked/` ruled out before it was ever picked, which never had a checklist to have walked. Dropping the active idea also removes its line from the Principal PM's `## Picked seeds`. One procedure at both levels. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/principal-pm/`; a project seed launches through `<CORE>/launchers/skill/launcher.sh nemawashi-drop <project> <slug> "<reason>"` from its `launcher.md`, and an instance seed is dropped from a `principal-pm:` session, which adds the group itself
- `skills/pm/.claude/skills/nemawashi-unpick/` — un-pick an **unfinished** idea: the inverse of a pick, so it moves the seed itself, root → `unpicked/`, leaving the root **empty** — no candidate moves — checklist intact, which is what "no longer active" means — and removes the seed's line from the Principal PM's `## Picked seeds`. **Gated to PM posture.** Declares an unattended launch in `launcher.md`, taking `<project> <reason>`; the reason is the commit body. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/pm/`. Project-level only — the instance seedbed has a pick too (§1), but it is made and undone there by hand

- `skills/pm/.claude/skills/tobiishi-drop/` — drop an **unsealed** 飛び石 Tobiishi change unit: move its folder whole into `journey/tobiishi/drop/`, mark the project's PM context dropped when it names the unit, commit that on `main` with the caller's reason as the body, then close the change's worktrees. **Every branch is kept, unmerged** — a drop merges nothing, which is where it departs from the seal. Refuses a blank reason, a sealed or already dropped unit, and a worktree holding uncommitted work. Touches no station, no seed and no seal. **Gated to PM posture**, because whether a unit is dropped is the PM's judgment: `shukuba-refine` makes it and runs this skill as one of its moves — the owner's call, 2026-09-19. Declares an unattended launch in `launcher.md`, taking `<project> <key> <reason>`. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher

  (All six are interactive rather than pipeline steps. Five move a station or a seed. `tobiishi-drop` is a Tobiishi's — a finished Tobiishi is sealed by `tobiishi-seal` and one that will not be finished is dropped by `tobiishi-drop`, never retired or unpicked. `nemawashi-unpick` halts outside the **PM**, because setting an idea down frees the slot the PM's traverse fills — the owner's call, 2026-09-17 — and so does `shukuba-park`, for a station set down unreached — the owner's call, 2026-10-03 — and `tobiishi-drop`, because the PM decides a drop inside `shukuba-refine` — the owner's call, 2026-09-19. `shukuba-retire` and `nemawashi-retire` halt outside the **Scrum Master** — save that the PM's `shukuba-park`, finding the station it was asked to set down already reached, closes it through `shukuba-retire` itself, the owner's call, 2026-10-03 — the second the owner's call, 2026-09-24, because it is a mechanical move — and `nemawashi-drop` halts outside the **Principal PM**, because it decides whether the program walks an idea at all — the owner's call, 2026-09-12. They no longer form pairs, and `nemawashi-drop` is why: it has no station counterpart, because a station set down is parked and taken up again where an idea can simply be dead. The four that do pair split by destination — `trail/` for what ripened into work, `unpicked/`/`parked/` for what is waiting — and `drop/` holds what is dead — a seed `nemawashi-drop` kills, or an unsealed change unit `tobiishi-drop` sets down. Historically: the retire pair replaced the single `journey-retire`, which carried the archive move for both parts and deliberately stopped there; the navigation each part owes after the move was documented in the journey READMEs but performed by no skill. The unpick pair covers the third destination: `trail/` is the record of things that *ripened*, so a station or idea being set down mid-walk needs `unpicked/`, and the operation must not tick or mark anything done.)

Shared by every skill that moves a journey item, in `<CORE>` beside `michi_agari.md` (Read on demand):
- `<CORE>/docs/journey_move.md` — the journey-move mechanic and its bookkeeping commit: the two levels, the **seedbed's `unpicked/` is the candidate pool** invariant (holds any number of candidates at any time, whether or not an idea is active) and **the pick and the un-pick** — the two single-file moves a nemawashi skill performs — **the Principal PM's picked seeds** (the line a pick adds and an un-pick, a drop of the active idea or a retire of a project seed removes), target resolution, park-don't-strike, move-whole and the one correction a move may make, the destination stub, the builder call (`--role`, `--staged` both halves, no `--skill`, the directional's `progress:`/`aside:` reading), the stat check, and don't-bloat. Single source for every skill that moves a journey item — the six above and others that make a move among their steps; each points at it rather than carrying a copy, and the file keeps no roster of them.

The seedbed's producers (2) — where the six above *move* a journey item, these *write* new ones.
Their shared run mechanics are `<CORE>/prompts/principal_pm_cut_seeds_run.md`. They differ in their input:
- `skills/principal-pm/.claude/skills/seeds-from-idea/` — the **idea** cutter: one idea in — something said in passing, a note, a seed someone else wrote — and 根回し Nemawashi seeds out, each landing in the owning project's `unpicked/` pool (or the instance seedbed) with its own station checklist and its trace back to the idea. Thin over its own `prompts/rich.md`, which extends `<CORE>/prompts/principal_pm_cut_seeds.md`. The one of the two whose input is itself a journey artifact, which earns it two moves the other has no use for: picking or un-picking that idea-seed, and leaving its retire — made by hand at instance level — to wait on the cut being approved. It writes seeds and never a station — opening one is a later move, made from the seed's own checklist item. **Gated to Principal PM posture, and grouped under that seat beside its sibling** — the owner's call, 2026-10-24, reversing the 2026-09-18 move to `skills/interactive/`: `nemawashi-refine` calls it inside its own run, and one group reaches both. So a session reaches it only after `--add-dir` / `/add-dir` on `skills/principal-pm/`. It has **no launcher of any kind** — the owner's call, 2026-10-24, superseding the 2026-09-18 plan to move it onto `<CORE>/launchers/skill/launcher.sh`: it runs in an owner's session, or inside `nemawashi-refine`'s own unattended run, which invokes it as a skill.
- `skills/principal-pm/.claude/skills/seeds-from-product-docs/` — the same seat's **document** cutter: a product's settled `docs/SDD.md`, `docs/fdr.md`, `docs/adr/` and `docs/nfdr.md` in, seeds out, landing in the owning project's `unpicked/` pool. Thin over `<CORE>/../skills/principal-pm/.claude/skills/seeds-from-product-docs/prompts/rich.md`. What it adds over its sibling is resolving *which* product to cut — the project from the invocation, the product path from that project's `project.md`, which may sit outside the instance — and a settled-input check before the lens is applied. It yields four kinds of seed, and the **upstream** kind owes a second write the sibling has no equivalent of: the item raised on the owing document's own `*_open_issues.md` companion, by hand, which the seed then tracks until it is folded in. Like its sibling it writes seeds and never a station, and it picks nothing it produced. Declares an unattended launch in `launcher.md`, taking `<project>`. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/principal-pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher

Shared by every cutter, in `<CORE>` beside the two cut prompts (Read on demand):
- `<CORE>/prompts/principal_pm_cut_seeds_run.md` — the run shape a cut has whatever its input is: where the run works, where a seed lands and under what name (a project's `unpicked/` pool or the instance seedbed, never a seedbed root), the `Cut from ` trace-back line every seed opens its `## Source` with, what a run may move in a seedbed and what it may not, the builder commit (`--skill`/`--prompt`, one commit per scope, the originator derived from the actor), and the shape of a clean close and of a stop. Single source for the cutters; each points at it and adds only its own posture gate, its method prompt, and any move its particular input earns.

The seed's picker (1) — where the producers above stock the pool, this one elects from it. The **PM**'s,
gated to that seat:
- `skills/pm/.claude/skills/nemawashi-pick/` — one seed lifted from `unpicked/` into an empty seedbed root. The
  judgment is `prompts/thin.md`, inside the skill folder, and chooses only; `scripts/pick.py` (tested in
  `tests/`) owns validity — it refuses an active seed, an open station or change unit, an empty pool, a
  dirty tree, a record naming other than one seed, a seed outside `unpicked/` or fully walked, and a
  stated condition — then makes the move, and appends the pick to `## Picked seeds` in the instance's
  `system/contexts/CONTEXT_PPM.md` when that file and section exist (append only; the move that takes
  the seed off its root removes the line — `<CORE>/docs/journey_move.md` § *The Principal
  PM's picked seeds*). The model's record is the commit body. Declares an unattended launch in `launcher.md`.
  Project-level only. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on
  `skills/pm/`, and a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the
  launcher

The seed's splitter (1) — where the producers above write seeds and the six before them move one,
this one settles the **route inside** a seed already picked. The **PM**'s, and gated to that seat as
`tobiishi-open` is:
- `skills/pm/.claude/skills/stations-from-seed/` — the picked seed's `## Stations — dynamic checklist` re-cut into
  the 1 to N 宿場 Shukuba stations that will be walked, in place, in the seed itself. Thin over
  `<CORE>/../skills/pm/.claude/skills/stations-from-seed/prompts/rich.md`. It stops on an empty seedbed root and on a seed being walked, never
  touches an already-ticked item, and writes no station file and no `change_request.md` — opening a
  station and opening a change unit are the two moves that follow it, and both stay the PM's own.
  Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher

The station's opener (1) — where the splitter settles the route, this one opens its next leg. The
**PM**'s, gated to that seat:
- `skills/pm/.claude/skills/shukuba-open/` — the next unticked item on the active seed's route opened as the one
  station at `journey/shukuba/`'s root. No prompt: the judgment is
  `<CORE>/templates/journey-templates/shukuba_template.md`'s comment block, which the run writes the
  station from; `scripts/open.py` (tested in `tests/`) owns validity — it refuses no active seed, an
  open station or change unit, a seed with no route or nothing on it unticked, an item with no slug, a
  dirty tree, and a station whose `*Item` line or three parts are not the template's — then lands it
  under today's date. A parked station of the same seed for that item is taken up again instead, moved
  whole. Declares an unattended launch in `launcher.md`. Project-level only. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher

The route's refiners (2) — where the splitter settles a route before it is walked, these re-read it:
the PM's after a unit lands, the Principal PM's after a seed is retired. Each is gated to its seat:
- `skills/pm/.claude/skills/shukuba-refine/` — reads what a sealed or halted unit, or an ad-hoc merge, left and what moved upstream, and acts on
  the project's route. Thin over `<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md`. It parks, un-picks and drops a
  halted unit through their own skills, names a reached station's close as owed to the Scrum Master, raises companion items on upstream documents rather than editing them, and
  always leaves `<unit-key>_report.md` and `<unit-key>_recommendations.md` in the unit's seed
  folder. It never drops, closes or writes a seed. Grouped, so a session reaches it only after
  `--add-dir` / `/add-dir` on `skills/pm/`; a run started by `<CORE>/launchers/skill/launcher.sh` is
  granted that group by the launcher, which is also how that run reaches `nemawashi-unpick` and
  `tobiishi-drop`.
- `skills/principal-pm/.claude/skills/nemawashi-refine/` — the Principal PM's answer to a retired seed,
  run after `nemawashi-retire`: every recommendation the seed's `shukuba-refine` runs left in
  `trail/<seed>/` is processed — a companion item, a docs cut, carried by a candidate, a drop, a seed
  cut from an idea, a route across projects, or ignored with its reason — and every candidate in `unpicked/` is
  kept, modified or dropped. It drops through `nemawashi-drop`, cuts work no product document should
  state through `seeds-from-idea`, and writes companion items rather than editing documents. It never
  runs `product-fdr` or `seeds-from-product-docs`, picks, retires, or writes under `trail/` or `drop/`;
  its `## Next moves` names the companion sweep (`chain-product` or `chain-agari`, as the project
  card's `**Definition:**` line names), `seeds-from-product-docs` — even with candidates left in
  `unpicked/` — `nemawashi-pick` and `stations-from-seed`. Thin over its own `prompts/rich.md`, its report's shape
  `templates/report.md`, both inside the skill folder. Always leaves
  `system/projects/<project>/docs/nemawashi-refine/<seed>_report.md`, opening with `## Next moves`. The
  owner's call, 2026-09-25. Project-level only. Grouped, so a session reaches it only after
  `--add-dir` / `/add-dir` on `skills/principal-pm/`; a run started by
  `<CORE>/launchers/skill/launcher.sh nemawashi-refine <project> [<seed>]` is granted that group by the
  launcher.

The skill-* authoring cluster (4) — three grouped under `skills/interactive/`, so a session reaches them only after `--add-dir` / `/add-dir` on `skills/interactive/`, and the eval runner under `skills/experimental/` — the owner's call, 2026-10-17 — so a run `launch-skill-evals` starts is not granted the session-only skills beside the other three:
- `skills/interactive/.claude/skills/skill-creator/` — skill authoring
- `skills/interactive/.claude/skills/skill-evals-creator/` · `skill-evals-trigger/` — eval authoring + trigger-eval authoring
- `skills/experimental/.claude/skills/skill-evals/` — eval runner. `skill-creator`'s `depends-on:` names it, so a grant of `skill-creator` reaches `skills/experimental/` too

The definition family — the upstream chain, thin skill over fat prompt (9). **All nine are
grouped**, so a session reaches one only after `--add-dir` / `/add-dir` on that group; a run started
by `<CORE>/launchers/skill/launcher.sh` is granted the group by the launcher. Seven sit under the seat
that authors their document. Two members sit outside that sentence: **`project-stamp` and
`project-setup` are grouped apart**, under `skills/interactive-product/`, because neither gates to a
posture (`project-stamp`'s § *Posture*: "no `<role>:` prefix, no loader, no posture"; `project-setup`
runs with the owner answering), so there is no seat whose group either would sit in:
- `skills/cpo/.claude/skills/product-prd/` — the PRD (CPO)
- `skills/cto/.claude/skills/product-srs/` — the SRS (CTO)
- `skills/cdo/.claude/skills/product-uxd/` · `product-design/` — the UXD and the design language (CDO)
- `skills/content-manager/.claude/skills/product-content/` — the verbal language, `CONTENT.md` (Content Manager): voice and
  tone, grammar and mechanics, terminology, the message patterns for the error / empty / loading /
  partial / recovered states, the accessibility bar for text, and localization. `DESIGN.md`'s peer
  and the only member of this family whose seat is delivery-tier. The one member with **no machine
  gate** — its sibling lints `DESIGN.md` against an external format, and nothing publishes a schema
  or a lint for a content standard, so its bar is carried entirely in the wording of
  `skills/content-manager/.claude/skills/product-content/prompts/rich.md` § The checkability bar.
- `skills/cto/.claude/skills/product-sdd/` — the SDD, station 5 of the definition sequence (CTO).
  One CTO run drafts the whole document; the CPO's and the CDO's calls reach it as companion items
  carrying their `Seat:`, folded in on the skill's next round. Grouped like the rest, so a session
  reaches it only after `--add-dir` / `/add-dir` on `skills/cto/`; a run started by
  `<CORE>/launchers/skill/launcher.sh product-sdd <project>` is granted that group by the launcher,
  reading the skill's own `launcher.md` (`**Agent:** cto`, `**Reporter:** sdd-document`).
- `<member>/stack.json` — the stack manifest: which files are that skill's substance.
  **The audit checks the file itself** — the `ratify` and `cold-read` launchers resolve what to judge
  and what to read blind from it, so a member missing one drops out of both silently. Carried by
  `kensaiapp-writing-bar`, `product-architecture`, `product-card`, `product-content`, `product-design`, `product-fdr`,
  `product-prd`, `product-sdd`, `product-srs` and `product-uxd` — ten, counted
  2026-09-17 with `for d in .claude/skills/*/ skills/*/.claude/skills/*/; do [ -f "$d/stack.json" ] &&
  basename "$d"; done`, which scans both roots — a member's own directory sits under either.
  The five this line used to name were the definition family alone, and the enumeration had not
  moved since.
- `skills/cpo/.claude/skills/project-agari/` — the project's 上がり Agari declaration (CPO). **Gated to
  CPO posture**, so it is grouped beside `product-prd`: a session reaches it only after `--add-dir` /
  `/add-dir` on `skills/cpo/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that
  group by the launcher
- `skills/interactive-product/.claude/skills/project-stamp/` — the per-project folder tree (§2), over `scripts/stamp_project.py`.
  Grouped under `skills/interactive-product/` — the owner's call, 2026-09-18 — so a session reaches it
  only after `--add-dir` / `/add-dir` on that group; `core/tools/spawn_satellite.py` resolves it
  through `core/tools/skill_path.py` and runs its script by path, which needs no grant
- `skills/interactive-product/.claude/skills/project-setup/` — the front door: one plain-language interview with the
  owner, then `project-stamp`'s script, the PRD's and the Agari's companions written as round 0 by
  `scripts/write_companion.py` and committed, and `core/launchers/chain-agari/` started. Interactive
  and posture-free; carries a README, its script and its tests. Grouped beside `project-stamp`, which
  it calls, so a session reaches it only after `--add-dir` / `/add-dir` on that group

The companion loop — answering the open-issues file a definition run parks (2):
- `skills/interactive/.claude/skills/companion-answer/` — walks a `*_open_issues.md` companion **with the owner present**,
  one item per turn: it puts each unanswered item to them in plain language, writes their words into
  that item's slot, commits, and names the launcher that re-runs the producing skill. It fills slots and
  never writes the document; the fold is the producing skill's. Posture-neutral, and useless unattended
  by design. It knows no list of producing skills, documents or companion paths — every fact comes off
  the companion's own header — which is why it serves this family and the definition family above
  without naming either. Grouped under `skills/interactive/` — the owner's call, 2026-09-18: the
  session that reaches for it is one the owner is in, which is the only session it can serve. So a
  session reaches it only after `--add-dir` / `/add-dir` on `skills/interactive/`. Its sibling below
  is grouped apart, under `skills/companion/`, because its session is the unattended one
- `skills/companion/.claude/skills/companion-self-answer/` — the same walk **with the run in the owner's seat**: same
  finding, same slots, same commit, same stop at naming the launcher. What differs is who decides, and
  the deciding is not in the skill — it is `skills/companion/.claude/skills/companion-self-answer/prompts/rich.md`, the fat half of
  a thin-skill-over-fat-prompt pair. It reaches further than its sibling in one direction only: it may
  raise a change on the companion it is answering, and open or update another document's, on its own
  judgment with nobody to ask. Run from `core/launchers/companion-self-answer/`, whose seat is resolved
  per run from the companion rather than pinned. Grouped under `skills/companion/` — the owner's call,
  2026-10-03: it has no one seat to be grouped under, since it answers in whichever seat owns the
  document — so a session reaches it only after `--add-dir` / `/add-dir` on that group; its launcher
  grants it through the pin, `--grant-skill` on the Claude path

The instance + kaizen family (7):
- `skills/interactive-product/.claude/skills/kensaiapp-michi/` — declares an instance's identity and its 道 Michi.
  Grouped under `skills/interactive-product/` — the owner's call, 2026-09-18 — so a session reaches it
  only after `--add-dir` / `/add-dir` on that group
- `skills/content-manager/.claude/skills/kensaiapp-writing-bar/` — settles the instance's **writing bar**, the bar every document authored here is held to (Content Manager posture): `system/doctrine/writing_bar.md`, with an open-issues companion whose absence is the done signal and a permanent trail under `system/doctrine/trail/writing_bar/`. **The bar is always the run's output** — core holds none to fall back on, so every instance states its own (§ Instance-shared doctrine). Thin over `<CORE>/../skills/content-manager/.claude/skills/kensaiapp-writing-bar/prompts/rich.md` and the `writing-bar-templates/` shapes. Step 3 of `setting_up_an_instance.md`; instance-level, so its own commits take `Michi:`. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/content-manager/`; it declares an unattended launch in `launcher.md`, and a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/cdo/.claude/skills/experience-visual/` — authors the instance's **visual** experience layer (CDO posture): `system/experience/visual_restrictions.md` and `visual_direction.md`, each with an open-issues companion whose absence is that document's done signal. **Creates** `visual_voice_contract.md` on a first run, from `experience-templates/visual_voice_contract_template.md`, and records a row there for every entry of the fence it writes — marking the ones that reach the verbal medium; `visual_direction.md`'s values carry no slug and no reach and get no row (`setting_up_an_instance.md` § The three rules, rule 2). Thin over `<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md` and the `experience-templates/` shapes. Step 4a of `setting_up_an_instance.md`; instance-level, so its own commits take `Michi:`. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/cdo/`; it declares an unattended launch in `launcher.md`, and a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/content-manager/.claude/skills/experience-voice/` — authors the instance's **verbal** experience layer (Content Manager posture): `system/experience/voice_restrictions.md` and `voice_direction.md`, each with an open-issues companion whose absence is that document's done signal. Reads the entries `experience-visual` marked in `visual_voice_contract.md` and records its own rows there. Thin over `<CORE>/../skills/content-manager/.claude/skills/experience-voice/prompts/rich.md` and the `experience-templates/` shapes. Step 4b of `setting_up_an_instance.md`; instance-level, so its own commits take `Michi:`. Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/content-manager/`; it declares an unattended launch in `launcher.md`, and a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/experimental/.claude/skills/kaizen-audit/` — the blind auditor fan-out over a produced
  artifact. Grouped under `skills/experimental/` — the owner's call, 2026-10-17, moving it out of
  `skills/interactive/` so an audit run is not granted the session-only skills there — so a session reaches
  it only after `--add-dir` / `/add-dir` on that group; a run started by `<CORE>/tools/launch-audit.sh`
  is granted the group by the launcher, which reads it off the resolved path
- `skills/interactive/.claude/skills/agent-invoke/` — runs an owner's ad-hoc delegated work as a configured background subagent. Grouped under `skills/interactive/`, beside the `delegate` agent it spawns, so a session reaches it only after `--add-dir` / `/add-dir` on that group, and that one grant gives it the agent too
- `skills/interactive/.claude/skills/session-close/` — closes a working session by sweeping what it
  produced onto durable surfaces, so the next session picks it up cold: four gated sweeps in order —
  uncommitted work, the journey's position, findings the session surfaced but must not act on, and
  durable session-craft. It **routes rather than acts**, each sweep naming the skill or file that owns
  the move. Grouped under `skills/interactive/`, so a session reaches it only after `--add-dir` / `/add-dir` on that group. Listed here from 2026-09-18 — it carried
  no manifest entry from its own grouping commit `e8a1a985`, found by the disk-vs-manifest sweep a
  cold read of the seat-group branch ran

The engineering-practice family (7):
- `skills/tech-lead/.claude/skills/ad-hoc-plan/` — the plan half of the ad-hoc pair: a hand-opened
  飛び石 Tobiishi planned end to end in one pass — a stub `change_spec.md`, a stub `change_design.md`
  and a full `tl_instruction.md` planned by `<CORE>/prompts/tech_lead_create_tl_instruction.md`, the
  body `development-plan` follows too, with a report beside them — so the chain can
  carry it from the content step, or from implementation when the change publishes no text, onward.
  It plans a product in this repository or in its own. **Gated to Tech Lead posture**, and grouped
  under its seat beside its pipeline sibling `development-plan` — the owner's call, 2026-10-17,
  moving it out of `skills/interactive/`, where the call of 2026-09-18 had put it. So a session
  reaches it only after `--add-dir` / `/add-dir` on `skills/tech-lead/`; a run started by
  `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
- `skills/developer/.claude/skills/test-driven-development/` · `source-driven-development/` · `debugging-and-error-recovery/`
- `skills/developer/.claude/skills/refactor-for-clarity/` · `refactor-for-reuse/` · `refactor-for-optimize/`
- The six above are grouped under the Developer's seat, so a session reaches one only after `--add-dir` / `/add-dir` on `skills/developer/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher
The verification helper (1):
- `skills/developer/.claude/skills/verify-before-claim/` — grouped under the Developer's seat with the six above, whose loader and two refactor skills are its only callers — the owner's call, 2026-10-03

The foundation family — the three decision records, written once per product after the SDD (2):
- `skills/principal-pm/.claude/skills/product-fdr/` — the FDR (`docs/fdr.md`): the **Principal PM**'s thin orchestrator
  over `skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md`, gated to that seat's posture, reading the template
  pair in `product-templates/` and run through `core/launchers/skill/launcher.sh` from its own
  `launcher.md`, which grants it its group. Grouped, so a session reaches it only after `--add-dir`
  / `/add-dir` on `skills/principal-pm/`. Carries `stack.json` and
  `evals/`, so it is cold-readable
- `skills/principal-architect/.claude/skills/product-architecture/` — the Principal Architect's two records: the append-only decision log (`docs/adr/`) and the constraint set (`docs/nfdr.md`). Grouped, so a session reaches it only after `--add-dir` / `/add-dir` on `skills/principal-architect/`; a run started by `<CORE>/launchers/skill/launcher.sh` is granted that group by the launcher

After the foundation — the step that makes the product buildable (1):
- `skills/interactive-product/.claude/skills/product-card/` — the project card's architecture-determined fields (`Languages:`,
  `Language roots:`, `Test command:`) and the product's `README.md`, both derived from the settled
  document set: the **Principal PM**'s thin orchestrator over
  `skills/interactive-product/.claude/skills/product-card/prompts/rich.md`, gated to that seat's posture. Carries `stack.json`,
  so it is cold-readable, and no template — the card's shape is `project_template.md`'s and a
  product's README has none. It runs after the foundation records land and **before**
  `core/launchers/product-skeleton/launcher.sh`, which reads the card it writes. It is the only
  member of this family that writes into two repositories in one run, because the card is the
  instance's and the README is the product's. Grouped under `skills/interactive-product/` — the
  owner's call, 2026-09-18 — so a session reaches it only after `--add-dir` / `/add-dir` on that
  group; a run started by `core/launchers/product-card/launcher.sh` is granted that group by the
  launcher, which reads it off the resolved path

#### Workflows — saved Workflow scripts (`.claude/workflows/`)

- `.claude/workflows/run-skill-evals.js` — `[create]` — the eval-runner script the `skill-evals` skill
  launches by name (`meta.name: 'run-skill-evals'`); allow-listed via `Workflow(run-skill-evals)`.
- `.claude/workflows/eval-fix.js` — `[create]` — the eval-fix loop.

#### Rules — path-scoped session rules (`.claude/rules/`)

`[create]` — vendored project rules: markdown files with optional `paths:` frontmatter, loaded by Claude
Code's memory system (unscoped rules at launch; path-scoped rules on-demand when a matching file is opened).
Create if missing, never overwritten (a user may add their own). **No rule ships today**, so the audit
checks the folder only — the directory exists as the place a rule lands, not as a carrier of one. When a
rule is added, enumerate it here in the same change.

> `core-change-blast-radius.md` was enumerated here until 2026-07-25. It was deleted in `c9703bb`
> (2026-07-09) as defective — "a memory-driven prose checklist of dependents to hand-sync… it relied on
> recall, grew a bullet each time it failed, and omitted the generator" — but this entry outlived it, so
> the manifest kept asserting a file that setup would stamp and the audit would check. That gap is the
> reason a later document cited the rule in good faith as still governing.

> **Drift-checks — rules are exempt from the `<CORE>`-indirection literal check.** Unlike the vendored
> plumbing above, a rule is behavioral prose and is **not** in the `<CORE>`-substitution set (§1 design
> principle lists skills / prompts / loaders / contexts / `CROSS_ROLE` / agents — not rules); its `paths:` frontmatter
> is matched literally by Claude Code. So rules **reference `core/…` paths literally** and a literal `core/…`
> in a rule is **not** a defect. The harmless principle still holds: no host-global `~/.claude/…` path.

### Shared-tools layer — vendored executables under `core/tools/`

`[create]` — the standalone executables a kensaiapp **element** (a role, a skill, a hook, the pipeline, a
workflow, the harness) *calls* to do a cross-cutting job it would otherwise hand-implement — or that the
machine runs on the system's behalf with no caller at all — reached by every caller through the
already-resolved `<CORE>`; create if missing, never overwritten. This is the
`tools` project's home (`system/projects/tools/`); it **succeeds the retired `scripts` project — there is
no `core/scripts/`.** Audit enumerates these paths; Init auto-creation follows the same later-increment
posture as the `.claude/` layer.

**What belongs here is decided by lifetime, not by how many instances use it.** Almost everything below
is *invoked and exits* — it runs inside a caller's lifetime and is handed its subject by argument. A
program that must be alive when nothing is calling it, up before a run starts and still up after it
ends, has no caller to be invoked by, so the machine starts it instead. Its **code** still belongs
here — written, tested and audited like the rest — because what makes it a singleton is its launchd
plist, not its source: it names no port and no data directory, both are handed in, so a test binds
neither. The plist, and the bytes it writes, are machine state rather than instance files (§5).

Do not read that criterion as *"would two copies conflict"*. A tool that collides with its own second
copy has hardcoded what it should have been given; that is a defect to fix by injection, never a reason
to move it out of this layer.

- `core/tools/commit_builder.py` — `[create]` — the one commit-message builder: assembles a commit's
  trailers in canonical order and runs the git op, so no caller re-implements the format. Before a
  feature-branch commit lands, it also refuses marker movement against local `main`, while allowing
  a marker-preserving rename, a new artifact at `1.0.0`, and a new file at another version whose
  bytes equal a file at a source declared with `--copied-from`. Landing bumps remain the merge
  path's.
- `core/tools/verify_commit_msg.py` — `[create]` — the pure, stdlib-only trailer checker (home-of-record
  here): presence-checks the required trailer keys (commit → `Role:`, `Surface:`; `--no-ff` merge →
  `Merge-Authorized:`, `Surface:`) and exits non-zero naming any missing key. Its consumer is the
  git-native `commit-msg` hook (below).
- `core/tools/written_forward.py` — `[create]` — the pure, stdlib-only written-forward checker
  (home-of-record here): holds the phrase set and the scope, and takes the repo it scans by
  argument rather than deriving one from its own location, so the checker reads whichever repo git
  is committing in when a satellite routes `core.hooksPath` here. Two consumers: the `pre-commit`
  hook (below) and the `.claude/hooks/` `PreToolUse` guard (above).
- `<CORE>/tools/core_indirection.py` — `[create]` — the forward-only `<CORE>` indirection checker:
  reads newly added staged lines when explicitly invoked, reports hardcoded shared-core paths, and leaves
  historical debt visible without making every unrelated commit repair it. Doctrine/rule files,
  tests and historical records are exempt for the reasons their own layers state.
- `<CORE>/tools/model_assignment.py` — `[create]` — the provider binding for the four stable Kensaiapp
  workload tiers (Fable / Opus / Sonnet / Haiku). It resolves a tier to a concrete provider model and,
  where the provider exposes one, reasoning effort. Doctrine owns why work earns a tier; this small
  replaceable map owns what that tier means to Claude, Codex, or Gemini today.
- `<CORE>/tools/intelligence.py` — `[create]` — the reader of a skill's
  `intelligence/<provider>.md` (`<CORE>/doctrine/governance/skill_intelligence.md`): `read(skill_dir,
  provider)` returns its `**Model:**` and optional `**Effort:**`, `None` when the skill has no `intelligence/` folder,
  and raises naming the file when the provider's file is missing or malformed. Its command line
  answers the launchers in shell — `model=` and `effort=` on exit 0, silent exit 3 for an absent
  folder, exit 4 naming a missing file, exit 2 naming a malformed one. The launchers that read a skill's file
  reach it through `run_intelligence.py`, below: the skill and companion launchers, and the one that
  runs a skill of its own (`product-card`).
- `<CORE>/tools/run_intelligence.py` — `[create]` — the one resolution of a run's model and effort,
  and of where they came from. It composes `intelligence.py`'s `read` and `model_assignment.py`'s
  `resolve`. It reads no environment and spawns nothing. Its command line is `--provider
  <claude|codex|gemini|hf|ollama> [--skill-dir <dir>] [--tier <t>]`. On exit 0, stdout is
  exactly three lines in order: `model=` (the id, or empty), `effort=` (the level, or empty) and
  `source=`, which is `intelligence`, `tier` or `default` and never another value. The order: a skill
  dir with an `intelligence/` folder answers from its provider's file (`source=intelligence`).
  Otherwise a tier answers through `model_assignment.py`
  (`source=tier`, a null effort printed empty). Otherwise the answer is `source=default` with an empty
  pair. Exit 4 is a missing provider file and exit 2 a malformed one, with `intelligence.py`'s own
  `intelligence:` message. Exit 5 is an unknown tier, with `model_assignment.py`'s own
  `model-assignment:` message. Exit 6 is a tier named for a skill whose folder exists, which wins over
  a missing or malformed file. Exit 64 is a usage error. No exit 3 exists: an absent folder is `tier`
  or `default`. Every instrumented launcher calls it once, hands its run the model and effort it
  answers, and stamps the same values with `source=` on its `run_telemetry` line. So the stamp and the
  run are one resolution. A launcher's own documented input overlays the answer, and the overlay stays
  in that launcher: `ratify`'s non-tier `--model` (the raw value, no source), the companion's fixed
  effort `high` (`<CORE>/doctrine/governance/skill_intelligence.md`).
- `<CORE>/tools/task_context.py` — `[create]` — the provider-neutral reader and renderer for
  `<CORE>/doctrine/task_map.md`: one parser produces the complete routing block and the `unprompted`
  standing-rules block, and a second reads § The rules of `governance/talking_to_the_owner.md`,
  which ends the standing-rules block. Claude's salience hooks wrap those blocks in hook JSON; Codex adapters
  prepend the same blocks to a run prompt. It is handed the resolved core root and fails empty.
- `<CORE>/tools/development_path.py` — `[create]` — where a change lives: reads a project's
  `Product path:` and returns the contract the pipeline skills route commits and delivery by — `kind` (`relative`,
  one repo; `fixed`, the product its own repo), each repo and worktree, `code_worktree`,
  `pipeline_worktree` and `delivery_repos`. `validate` and `resolve --strict` prove the worktrees exist,
  belong to their repos and are on `<key>`. Standard library only. `create_change_worktree.py`,
  `development-implementation`, `development-code-integrity` and `tobiishi-seal` call it through
  `<CORE>`; it replaced the two prose path skills `development-path-fixed` and
  `development-path-relative`.
- `<CORE>/tools/agent_run.py` — `[create]` — the provider-neutral boundary for one unattended agent
  run. Callers hand it a prompt plus optional agent, model tier or explicit provider model, an effort level
  (`low`, `medium`, `high`), which the Claude and Gemini adapters pass as `--effort` and the Codex
  adapter as the one `model_reasoning_effort`, over the tier's, directory grants, settings, logical name or conversation ID to
  resume; a provider adapter alone owns the
  executable and provider-specific flags. Its
  Claude adapter builds `claude --bg` (`Shape.BACKGROUND`, the owner-run launchers' shape, unchanged)
  and `claude --print --output-format stream-json --permission-mode auto --permission-prompts none`
  (`Shape.TURN`, the shape every run the three chains start takes). Its Codex adapter maps the
  shared subset to `codex exec --approve-for-me` and an existing thread to `codex exec
  resume`, resolves `--model-tier` to
  model plus reasoning effort, translates `agent` into a sentence naming the agent and its file,
  prepended to the prompt — translates
  `settings`'s `env` object into the process environment as a leading `env KEY=value …` on the argv,
  and refuses `name`. When handed
  `--core-dir`, the Codex adapter prepends `task_context.py`'s resolved route and standing-rule
  blocks; Claude keeps receiving those blocks through its existing session hooks. The Gemini adapter
  builds `agy -p --mode accept-edits --output-format stream-json`, resolves `--model-tier`
  to model plus `--effort`, translates each directory grant into `--add-dir`, and prepends
  the same blocks through `task_context.py` `gemini_bootstrap`. The
  background contract serves every adapter, and who owns the detach is the adapter's to say per request:
  a `claude --bg` launch owns its own detached run, while a Claude `--print` run and every Codex or Gemini run
  are started in a new local process session under an exit-record wrapper (a `kensai.exit` line once
  the process ends) and identified by PID. A detached `--print` run ends with its turn and nothing
  wakes it after, the way a `--bg` session was woken when its background work finished, so it is
  started with background tasks off (`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`), a ten-minute default
  and six-hour ceiling on a Bash command (`BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS` — the
  ceiling is as long as the run watcher's own deadline); a command past its timeout is stopped and
  reported to the run, which can run it again with a longer one, and `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`. All write to a caller-supplied new log and return normalized JSON naming the
  provider, lifecycle owner, PID, the Claude session ID the run was started under, and the log. The
  two launchers the chains start — `skill` and `companion-self-answer` — are its callers on that
  process path, for each provider.
- `<CORE>/tools/agent_session.py` — `[create]` — the persistent-conversation layer above `agent_run.py`.
  It starts a turn, captures the durable provider identity (Claude background-agent ID, Codex thread
  ID, or Gemini conversation ID), resumes that identity on a later turn, and normalizes inspection into starting / running / idle /
  completed / failed / vanished state. A launcher-computed logical name remains metadata around that
  provider identity; neither is an agent selection and neither is a role. Claude state comes from
  `claude agents --json --all`; Codex state and the last agent message come from its JSONL event log.
  A Gemini conversation ID is the `conversation_id`
  on its `stream-json` log, reduced by its own inspector.
  The layer does not translate a selected agent for Codex: callers must still make that identity
  explicit in the prompt as the general skill launcher does, rather than silently discard it.
- `<CORE>/tools/agent_turn.py` — `[create]` — one detached, machine-readable turn in a durable
  provider conversation. Claude runs in print / stream-JSON mode under a caller-visible UUID;
  Codex runs in JSONL mode and exposes its thread ID. Both return immediately with a PID and reduce
  their log to a normalized final reply. Starting a Codex conversation under a selected agent
  requires that agent's file and prepends an instruction to read it; every Codex turn can also
  prepend the same provider-neutral task context as `agent_run.py`, including after compaction or
  resume. The agent remains an identity, never a role, and is never silently dropped.
- `<CORE>/tools/completion_shim.py` — `[create]` — the one owner of the completion-hook shim the
  walk engines (`chain.py`, `chain_development.py`, `build_idea.py`) write; its contract — a hook
  hands off and returns at once — is its own docstring's.
- `<CORE>/tools/walk_stop.py` — `[create]` — the shared launch identity and process-stop owner,
  used by the walk engines, by `detached_run.sh`'s `record_detached_run_identity` and by the
  process observer, which takes its process-group stop (`stop_lingering`) from it.
- `<CORE>/tools/watch_process.py` — `[create]` — the completion observer for detached provider
  processes whose lifecycle is a structured log — a Claude `--print` run's stream-json, a Codex
  run's JSONL, or a Gemini run's stream-json, read by the provider's own inspector (`agent_turn.inspect`). It honors the same
  optional completion marker and reporter contract as `watch_agent.py` and forwards the same
  completion hook outcomes that advance chains: a Claude `result` of any subtype ends the run and the
  disk decides, as an idle `--bg` session did; a Codex failed turn and a process that died with no
  terminal event are `failed`; a `--multi-turn` run that ends without its marker is `stopped`. It
  carries `watch_agent.py`'s refusal note, names the run's session and any permission denials, and
  stops a process that outlives its ending through `walk_stop.py`'s `stop_lingering`.
- `<CORE>/tools/detached_run.sh` — `[create]` — the launch half of that process path, sourced by the
  three chain launchers for either provider: `start_detached_run` hands `agent_run.py --background`
  its command with the launcher-scope variables a chain sets (`DETACH_WATCHER_ON_COMPLETE`,
  `INSTRUMENT_RUN_*`, `DETACHED_RUN_IDENTITY_FILE`) withheld from the run — none of them reached a `--bg` session —
  and reads back the run's PID and Claude session ID; `print_detached_run` is the dry run and
  `announce_detached_run` the lines naming the run's log and session. Required where the watcher
  home is optional: nothing launches without it. `record_detached_run_identity` writes the run's and
  the watcher's pid, each with its start time, to the file a walk engine names in
  `DETACHED_RUN_IDENTITY_FILE` — the identity `walk_stop.py` stops by; the `skill` and
  `companion-self-answer` launchers call it after their watcher block, so the
  watcher's pid is recorded only when a watcher was started.
- `<CORE>/tools/detach_process_watcher.sh` — `[create]` — the shared Bash home that detaches
  `watch_process.py`, gives it the provider, the run PID and its log, records the observer's own log
  under `detach_watcher.sh`'s one name for it (`detach_watch_log_file`, the name `chain_usage.py`
  reads), and binds optional `caffeinate` to the observer. A missing notifier becomes a silent notifier rather than
  disabling observation, because completion hooks must still advance unattended chains.
- `core/tools/watch_agent.py` — `[create]` — the completion watcher for the owner-run launchers that still
  start `claude --bg` (a chain's runs are `watch_process.py`'s): waits for a `claude --bg` run to reach
  a terminal state, then composes a notification via a named reporter and stops the run. Takes the instance
  by argument (`--cwd` / `--instance-root`), never from its own location. When it cannot identify which run
  is its own it **does not exit** — it holds, watches every unidentified background run under `--cwd`, and
  reports when all of them stop, saying what it could not identify and stopping none of them. That path
  exists because a `--keep-awake` `caffeinate` is keyed to this process's lifetime, so an exit at the
  appear window releases the machine mid-run; a launch that genuinely started nothing is still reported as
  such, and both paths share one `--timeout-seconds` deadline.
- `core/tools/chain.py` — `[create]` — the chain engine: walks an ordered spine of document cycles
  (`producer launcher -> companion-self-answer -> producer`), advanced by the completion event rather
  than by waiting. It **constructs nothing it uses**. The spine it walks, the document registry, and
  four ports — the filesystem, the process launcher, the self-answer report reader and the notifier —
  plus the environment a launch inherits and the engine path its completion shim pins, are all handed
  to `Chain(...)`; `main()` is the only function in the file that builds a concrete implementation, per
  `<CORE>/doctrine/engineering/arch_defaults.md` § Composition Root. That is load-bearing rather than
  tidy: at 1.x it built its own, and the three defects that got it rejected on 2026-09-01 were that one
  fact — a spine it could not be given (so a second chain could not differ from the first), a suite
  that could not see a walk (197 tests green over a feature that did not exist), and a shim reading
  `__file__` (so editing this file killed a chain in flight). A chain launcher hands it a spine through
  `--start ... --spine`; the state file it keeps carries a `schema_version` and a mismatch is a message
  naming the restart, never a raise out of the completion hook. One chain per project at a time — the
  state file is that project's chain — and a state this engine could not resume never blocks a fresh
  start. `core/launchers/chain-product/` and `core/launchers/chain-agari/` are its entry commands,
  each a folder plus one spine literal. Every producer runs as
  `core/launchers/skill/launcher.sh <skill> <project>` from that skill's own
  `launcher.md`, the SDD keeping its own launcher and the answer step staying
  `companion-self-answer`'s; an owed bullet is launched as quoted once it validates. The rule is the
  module header's § How a document is launched. `chain-foundation` and `chain-definition`, one spine
  per tier, were retired into it on 2026-09-17. Started with the optional `--on-end <command>`, it
  runs that command once when the chain ends, with the end appended and after the ended state is
  saved; a hook that fails is one message to the owner and never a change to the end, and
  `chain-product` passes the flag through.
- `core/tools/providers.py` — `[create]` — the one reader of the provider file, and the rule a launch follows. The provider file is `.providers.toml` at the root of the instance a launch is for (§ Root, `.providers.toml.example`), and it names the provider every chain launch, instance skill launcher and kaizen tool script (`launch-apply-packet.sh`, `launch-audit.sh`, `launch-fix-author.sh`) goes to. It names one for each member of the three engines — `[documents]` (`chain.py`'s registry), `[steps]` (the development and change walks' steps, one entry per step for both), `[build-idea]` (the queue's skill rows) and `[owed-items]` (`no-document`, the product chain's launch for an owed item that names no document) — and for the launchers: `[launchers]` (one entry per instance skill launcher, keyed by its folder name, and one per kaizen tool script, keyed by its name without `.sh`). The module owns the file's name, its format, the member names and the rule: the provider a walk was forced onto (`--provider`), else the file's entry for the launch's member, else a refusal naming the entry or the file — never a default. A missing file is refused naming its path and `cp .providers.toml.example .providers.toml`, and the example is never read in its place. The instance root is the one an engine was started or described with (`--instance-root`), or the one a launcher resolved and hands to `providers.py launcher --instance-root`. No file under `<CORE>` is read for a provider, so a satellite's launch reads the satellite's own file, and a walk running from a pin reads the live instance file. An unforced start checks every member the engine can launch, and each launch reads the file again as it stands then, so an edit reaches a walk that is already running. An entry no engine asks for is ignored.
- `core/tools/chain_development.py` — `[create]` — the development chain engine: walks the
  change pipeline's nine steps (specs, design, plan, content, implementation, code-integrity,
  security, the
  `development-audit` fan-out — four runs, or five when the change publishes text — seal) as one detached `claude --print` run per step, each started through
  `core/launchers/skill/launcher.sh` from that skill's own `launcher.md`, and advanced by the
  completion event. **It decides a step is done from disk, never from a message a run returns**,
  because a detached run returns none: the artifact on the change branch, the developer's closing marker
  read the way `tobiishi-seal` reads it, each audit's findings file on its own audit branch, and the
  change folder under `trail/` on `main`. A run that ends without its artifact halts the walk, pointing
  at a `halt_report.md` where one was left — except the developer's run past its context cap, which
  ends on a **pause commit** (`developer: <key> — implementation paused after task <N>`) rather than
  the closing marker: the engine reads `<N>` off it and relaunches the implementation step with `<N>`
  after the key, so the launch prompt starts a fresh developer at the next task, and a pause that is not
  after a later task than the last one halts. `--context-cap <tokens>` (default 250000) is that cap,
  kept on the walk's state and handed to the implementation run alone as `KENSAIAPP_CONTEXT_CAP`, which
  `.claude/hooks/context_cap.py` reads. It stands **beside** `chain.py` rather than extending it —
  it imports that engine's `Files`, `Processes`, `Notifier` and `IdSource` ports and changes nothing
  there — and adds a `Git` port and an exclusive `flock` on its state file, because four or five audit runs can
  end within a second of each other. Its state file is its own,
  `system/logs/chain-development-<project>-state.json`, so a development walk can run beside a document
  chain on the same project. Each run's completion shim is `completion_shim.py`'s. Its suite,
  `core/tools/test_chain_development.py`, drives a whole walk through injected fakes and exercises the
  real `Git` port and lock against a scratch repository. `core/launchers/chain-development/` is its
  entry command. Beside `--start` and `--advance` it has a third entry, `--describe`, which answers
  which change a start would carry and the step it would enter at — or why it would refuse — from
  the **same checks** `start` makes, and writes, launches, locks and sends nothing; the launcher's
  `--dry-run` is its one caller. It holds **two step tables**, and `--steps` says which walk a
  start is: `development`, the nine above, and `change`, the same nine behind `shukuba-open` and
  `tobiishi-open` and ahead of `shukuba-refine` — the walk `core/launchers/chain-change/` enters.
  The flag names a literal the engine holds; a caller composes neither. A `change` walk starts with
  **no key** — `tobiishi-open` is what makes one — so the key is read off the disk the moment that
  step lands, and the walk's own name, carried on its state, is what its shim, its log, its
  `INSTRUMENT_RUN_CHAIN` tag and every message the owner reads are named after. A `change` walk
  does not end at the seal: its `refine` step runs `shukuba-refine` on the sealed unit, and is done
  when `<key>_report.md` sits in a seed folder under `journey/nemawashi/`. Started with no change
  open, a `change` walk first takes the unit `contexts/CONTEXT_PM.md` names as `Sealed` — the
  default `shukuba-refine` itself takes — and, if that unit has no report yet and its station is
  still open at the shukuba root, carries its key and enters at `refine`; a sealed change's earlier steps are taken as landed on the seal's word.
  It takes the same optional `--on-end <command>`, carried on the walk's state and run once from the
  walk's one ending with `sealed` or `halted` appended; `core/launchers/chain-change/` always passes
  it, naming `build-idea`.
- `core/tools/build_idea.py` — `[create]` — the engine behind `core/launchers/build-idea/`.
  Runs refine reports' next moves and connects retirement to seedbed refinement; its kinds,
  landing checks, continuation and stop/resume contract are owned by the engine. State and
  completion shims live under `system/logs/`. Its suite is `core/tools/test_build_idea.py`.
- `core/tools/detach_watcher.sh` — `[create]` — the shared completion-watch home: a sourced bash library,
  never run directly, exposing one function (`detach_completion_watcher`) that resolves the watcher/notifier
  pair a caller already computed, detaches `watch_agent.py`, writes its own timestamped log, and holds
  `--keep-awake`'s `caffeinate` open on the spawned watcher's **identity** — its pid paired with the start
  time it had when spawned, never a bare pid number the kernel can reissue — carrying the two-condition
  `else` fix (name whichever of watcher/notifier is actually missing, independently) from the start rather
  than a copy of the bug. Every launcher that sources it carries no `caffeinate` of its own, so a fix here
  reaches all of them without one being edited; the file's own header names the current set. Since
  2026-08-22 that set is **every** launcher that detaches a watcher — the hand-copies migrated onto
  it, and `core/tools/test_keep_awake_binding.py` proves from disk that no copy is left and exempts
  nothing. It publishes the spawned watcher's identity as a **pair** — `DETACH_WATCHER_PID` and
  `DETACH_WATCHER_START` — which is what lets `core/launchers/cold-read/launcher.sh` bind one
  keep-awake across N watchers while still calling this library once per reader: the pid alone is
  not a handle, and a caller completing it with its own `ps` afterwards would be inside the reissue
  window the pairing closes. `cold-read` is the one caller that passes no `--keep-awake`, because
  the hold it wants spans the set rather than any one member of it.
- `core/tools/hook_wiring.py` — `[create]` — the one rewrite of `${CLAUDE_PROJECT_DIR}/.claude/hooks/`
  to a given absolute hooks directory, at any depth of a settings document; stdlib only. Shared by
  `link_satellite.py` (a satellite's `settings.json`) and `agent_run.py` (a pinned run's hook wiring).
- `core/tools/link_satellite.py` — `[create]` — writes a shared-core satellite's `.claude/settings.json`
  from its host's hook wiring, with each command pointed at the host's `.claude/hooks/` by absolute
  path, and for a producer links the host's root `skills/` by absolute symlink; re-runnable, with
  `--check` as a drift gate.
- `<CORE>/tools/telemetry_command.py` — `[create]` — the one resolver of the name
  `run_telemetry.sh` runs as the telemetry command: the invoking environment's
  `KENSAIAPP_TELEMETRY_COMMAND` when it holds one, else the source host's `.telemetry.env`
  (§ Root). The precedence, how the source host is found and what an unreadable setting answers
  are the tool's own. Takes the core directory by argument (`--core`), never from the caller's
  working directory, and prints the name alone. It runs, checks and searches for no command: what
  happens to the name next is `run_telemetry.sh`'s.
- `<CORE>/tools/run_telemetry.sh` — `[create]` — the telemetry tagging every instrumented launcher
  sources and calls (`run_telemetry key=value ...`), over the telemetry package's `turn-on`. It
  hands the launch its settings document and its six telemetry exports, and it never fails the
  launch. Its contract, where the command's name comes from included, is its own header's.
- `core/tools/skill_path.py` — `[create]` — the one resolver: a skill name in, its directory out,
  under either layout — the flat path when it exists, else the single match of
  `skills/*/.claude/skills/<name>` (not found and ambiguous never look the same to a caller). Takes
  the instance root **by argument**, never derived from its own location, the same posture
  `written_forward.py` and `watch_agent.py` hold. Both an importable form (`resolve_skill_dir`,
  `instance_root`) and a command line whose exit codes (0 / 3 / 4) distinguish found from
  not-found from ambiguous, for the bash launchers that cannot import Python.
- `core/tools/check_satellites.py` — `[create]` — fans `link_satellite.py`'s `--check` across every
  satellite in an instance's own `system/satellites.md` and prints one headline each, with a line
  beneath it listing the agents a satellite overrides in its own `.claude/agents/`. Exits 1 if the
  host's or any satellite's instruction files or role overlays are wrong, or if any satellite is
  absent, fails `link_satellite.py`'s own `--check`, carries a skills layer whose shape contradicts
  its rostered kind (a consumer holding any, a producer whose root `skills/` is a symlink), or holds
  `.claude/agents` as a symlink. An override is not drift and never sets the exit code. Read-only,
  and reuses `link_satellite` rather than holding a second definition of correct.
  Takes the instance by argument (`--instance-root`, defaulting to the caller's cwd), never from its
  own location — the rule this section states for `written_forward.py` and `watch_agent.py`.
- `core/tools/evals_round_lock.py` — `[create]` — the eval-round lock.
- `core/tools/reporters.py` — `[create]` — the run-outcome composers `watch_agent.py` dispatches on
  (`--reporter`): one per run type (`prd`, `srs`, `uxd`, `design`, `fix-author`, `apply-packet`,
  `generic`). A new run type is a new reporter here, not a watcher edit.
- `core/tools/launch-fix-author.sh`, `launch-apply-packet.sh`, `launch-audit.sh` — `[create]` — the
  run launchers still living flat here: each builds a FIXED `claude --bg` prompt for one pipeline run and
  detaches the watcher. Being core-shared, they resolve the
  **instance** from the caller's cwd (`--instance-root` defaults to `$PWD`), never from their own location,
  and take the notifier from `KENSAIAPP_NOTIFIER` (no host-global default). Invoked `<CORE>/tools/launch-…`
  from the instance root. **The not-yet-migrated remainder** — `core/launchers/<name>/` below is the
  destination for owner-run launchers, and these move there incrementally, one at a time (owner decision,
  2026-07-27). A launcher's move is otherwise mechanical: `CORE_DIR` resolves from the launcher's own
  location at any nesting depth, so the default watcher path (`$CORE_DIR/tools/watch_agent.py`) needs
  no change at all.
- `core/tools/brief_gaps.py` — `[create]` — reads every `delegate-report.md` in the repo and prints
  what each run recorded about its own brief. Computed, never maintained, so it cannot drift from the
  reports it reads. `agent-invoke` § Step 4 runs it before a brief is written.
- `core/tools/check_brief_quotes.py` — `[create]` — names every citation in a brief file whose quoted
  text is not at its lines, through `.claude/hooks/brief_anchor_guard.py`'s own check rather than a
  copy of it. `seeds-from-idea` runs it on its brief before it cuts, and `ad-hoc-plan` before it
  plans; each stops on any line it prints.
- `core/tools/journey_status.py` — `[create]` — reads an instance's own journey state
  (`system/nemawashi/`, `system/shukuba/`, and each project's `journey/`) and renders one
  self-contained HTML page naming every place the repo has drifted from `core/docs/michi_agari.md`'s
  own model. Read-only: never writes inside a journey folder, and never outside the instance it was
  run against. Its own output (`--out`, default `system/logs/journey_status.html`) is gitignored.
- `core/tools/journey_names.py` — `[create]` — the one statement of a station's slug and dated stem.
  `build_idea.py` imports it, and so do `shukuba-open`'s and `shukuba-retire`'s `scripts/`, which
  reach it through their own path, so the three cannot disagree on a station's name.
- `core/tools/chain_board.py` — `[create]` — reads one instance's `system/logs/` walk state, for every
  chain kind (`build-idea`, `chain-change`, `chain-development`, `chain-agari`, `chain-product`), into
  WAITING ON YOU and RUNNING NOW, adds each listed project's route — its active seed's checklist, with
  the walks opened for each station — and prints them as JSON. Read-only: it opens no file for
  writing. Whether a walk still runs comes from `walk_stop.py`'s `launch_state`, never from a copy of its
  rules here; which station a walk was opened for comes from its opening commit's `Shukuba:` line.
- `core/tools/kensaiapp-panel/` — `[create]` — the home of the kensaiapp side pane: a Claude Code mod
  that draws `chain_board.py`'s output in a pane beside the session. It holds `.claude-plugin/plugin.json`,
  `hooks/hooks.json`, `hooks/register.tsx`, `types/index.d.ts`, `tests/pane.test.tsx` and `tsconfig.json`,
  and no Python. The engine lays `.claude-plugin/types/` there at each load, with its own `.gitignore`,
  so git never sees it. How the mod loads is the `CLAUDE_CODE_PLUGIN_DIRS` entry in § *Machine state*.


> **Tests ship alongside, but are not the shipped tools.** `core/tools/` also carries each tool's pytest
> suite (`test_agent_run.py`, `test_agent_session.py`, `test_agent_turn.py`, `test_intelligence.py`, `test_model_assignment.py`, `test_commit_builder.py`,
> `test_verify_commit_msg.py`, `test_watch_agent.py`, `test_reporters.py`,
> `test_watch_process.py`, `test_detach_watcher.py`, `test_detach_process_watcher.py`, `test_detached_run.py`,
> `test_keep_awake_binding.py`, `test_launch_fix_author.py`,
> `test_launch_apply_packet.py`, `test_launch_audit.py`,
> `test_link_satellite.py`, `test_skill_path.py`,
> `test_evals_round_lock.py`, `test_spawn_satellite.py`, `test_templates_are_instance_neutral.py`,
> `test_skeleton_trees.py`,
> `test_written_forward.py`, `conftest.py`) —
> vendored so the tools are provable on a fresh clone, but Audit checks the executables, not the fixtures
> (per the tools Agari: test artifacts are out of scope).
>
> **Two of those suites have no tool of their own here, and that is the pattern rather than an
> exception.** `test_templates_are_instance_neutral.py` and `test_skeleton_trees.py` hold
> `core/templates/` to a property — no instance fact in a template; no placeholder token in a
> skeleton tree that the product-skeleton launcher will not substitute. They live here because
> `core/tools/` is where a repo-wide rule over an artifact set runs (`test_language_packets.py`
> does the same for a doctrine family), and because the alternative for the
> second one was a scan inside the launcher, which could only ever refuse a tree of ours on the
> owner's machine, at copy time.
>
> **Drift-checks:** the tools are **executables, not core-pointing plumbing**, so — like the hooks — they
> are **not** in the `<CORE>`-substitution set (§1 design principle); the `<CORE>`-indirection literal-check
> does **not** apply here. Only the harmless principle holds: no host-global `~/.claude/…` path.

### Owner-run launcher folder — `core/launchers/`, sibling of `core/tools/`

`[create]` — a per-launcher folder for an owner-run launcher that carries its own nested test file.
**This is the destination for every owner-run launcher**; the flat `core/tools/launch-*.sh` set above is
the not-yet-migrated remainder, moving here incrementally, one launcher at a time (owner decision,
2026-07-27). Sibling of `core/tools/`, not nested inside it: `core/tools/` is system-called machinery
(a kensaiapp element calls it), while a launcher here is owner-run (the owner invokes it directly) — the
two are separate homes under `core/`. Audit enumerates these paths; Init auto-creation follows the same
later-increment posture as the `.claude/` layer.

Each folder is `core/launchers/<identity>/` holding `launcher.sh` (the script itself is named for its
role, the folder carries the identity) plus its contract-test suite flat beside it. A change-pipeline
step's launcher is permitted to nest one level deeper instead, at
`core/launchers/development/<step>/` — both are the destination this section names.

**The folder name is the bare identity — no `launch-` prefix** (owner decision, 2026-07-28). The parent
folder already says these are launchers, so the prefix only restates it: `core/launchers/cold-read/`, not
`core/launchers/launch-cold-read/`. This is **forward-only**. The two folders that still predate the
decision — `launch-eval-fix/` and `launch-skill-evals/` — keep their names until someone chooses to
rename them; the inconsistency on disk is a migration in progress, not a mistake to copy. A new or
relocated launcher takes the bare form.

**Test-file names must be globally unique, which the role-naming rule cannot give them.** `test_launcher.py`
works for exactly one folder: pytest imports test modules by basename, so a second `test_launcher.py`
anywhere under `core/launchers/` aborts the whole run with `import file mismatch` before a single test
executes (measured 2026-07-28, adding a second one). There is no pytest config in this repo to change that,
so the test file is named for its identity — `test_ratify.py` — while the launcher is named for its role.
The generic name is now unused, and it stays unused: whichever folder took it would silently forbid it
to every other, so each suite is named for its identity instead.

Because the folder sits one level deeper than the flat launchers, a launcher here reaches shared machinery
through `CORE_DIR` — resolved from the launcher's own location (a prefix strip at the `/launchers/`
boundary, not a fixed number of parent steps), so the same expression reaches
`<CORE>/tools/watch_agent.py` correctly whether the launcher sits at `core/launchers/<identity>/` or
nested at `core/launchers/development/<step>/`. A migration into either home changes no path at all —
the failure mode this used to name (a wrong default leaving the watcher unspawned while the launch still
succeeds, so only the absent completion notification shows it) is what the depth-independent resolution
exists to close. `core/launchers/test_core_resolution.py` pins it as a cross-launcher contract; each
launcher's own suite additionally pins its own default with a test that unsets the watcher env override
on purpose.

**Every launcher enters the pin first, through `<CORE>/tools/pin_run.sh`.** Right after resolving
`CORE_DIR`, before reading any other argument, a launcher sources that library and calls one of its
two entries. Every launcher but `build-idea` calls `pin_enter`. It either finds itself already inside
a pin, inherits one from `KENSAIAPP_PIN` (when that pin's own source is this host), or makes a fresh
one of the host as it stands (`core/tools/pin.py`) — then, if the running script is not already the
pin's own copy, re-execs into it. `build-idea` alone calls `pin_enter_renewing`, which follows the
same rules except at the two points where `pin_enter` would inherit a pin. There it first asks
`core/tools/pin_host_changed.py` whether the pin's source host has changed, and when that host's
`core/`, `.claude/` or `skills/` differ from the pin's copies — "differ" as that file defines it — it
takes a new pin of the host instead. A run started either way keeps the version it started on: a live
edit to `core/`, `.claude/` or `skills/` made after the launch has already copied them cannot reach
it. A launcher the run itself starts through `pin_enter` inherits the run's pin rather than making its
own; a `build-idea` it starts takes a new pin when the host has changed. The Claude adapter
(`core/tools/agent_run.py`) then carries that pin into the `claude` process it builds — a plugin
linking the flat skills, the instance's own skills and every workflow, plus only the skill groups
the run is granted, and merged settings whose hooks point into the pin. A launcher grants the skill
it starts (`--grant-skill`), and the grant follows each granted skill's `depends-on:` into the
groups that names, so a Claude run needs no group `--add-dir` to see its skill and sees no other
group's. The Codex path is unchanged: it still reaches a grouped skill's group with its own
`--add-dir`, read off where the skill lives.

A launcher that reads anything else under `<CORE>` — a prompt, a lens, a doctrine file — has a **second**
path to rewrite, and that one is *not* silent: it is guarded and dies loudly on the first invocation. The
watcher path is the one a migration can get wrong without noticing; both still have to be walked.

- `core/launchers/test_core_resolution.py` — `[create]` — the cross-launcher contract suite, at the
  root of `core/launchers/` beside `conftest.py` rather than inside a launcher folder, because it
  asserts a property of the *set* — every `launcher.sh` on disk, and the `CORE_DIR` resolution
  mechanism itself over a synthetic tree — never the behaviour of one launcher. Pins: no file under
  `core/launchers` reaches `core/tools/` by counting folders; every `launcher.sh` derives `CORE_DIR`
  by the one sanctioned expression; a launcher nested at `core/launchers/development/<step>/`
  resolves the same `<CORE>` a flat one does and spawns the real watcher with its override unset; a
  launcher with no `launchers/` ancestor at all refuses loudly rather than guessing. Its basename is
  globally unique, per the naming rule below.
- `core/launchers/cold-read/launcher.sh` — `[create]` — one command opens the blind cold reads over a
  skill's producing stack, and stops: reads the skill's `stack.json` through
  `<CORE>/tools/coldread/manifest.py` and builds N+1 FIXED `claude --bg` prompts
  (`--agent kensaiapp-auditor`) — one blind reader per substance file plus, when there is more than
  one, a seam reader over the whole set — then detaches one completion watcher per run through the
  shared home (`<CORE>/tools/detach_watcher.sh`, called once per reader; the watcher it spawns is
  `<CORE>/tools/watch_agent.py`, and both are reached via `CORE_DIR`, resolved from this folder's own
  location). It is the
  fan-out caller that home's contract is written for: it collects each spawn's published identity
  pair and runs **one** keep-awake poller over the set, so it passes no `--keep-awake` of its own. Carries the
  bare-identity folder name per the 2026-07-28 decision; no fixing, no loop, no `--outcome`/`--wait`,
  because it is the whole of move 1 in `<CORE>/doctrine/kaizen/skills.md` § Running the cold-read and
  the fixing there is the owner's. Same
  core-shared contract as its neighbours (`--instance-root` defaults to `$PWD`, `KENSAIAPP_NOTIFIER`
  for the notifier); invoked `<CORE>/launchers/cold-read/launcher.sh <skill> --project <project>` from
  the instance root.
- `core/launchers/cold-read/test_cold_read.py` — `[create]` — its contract-test suite, flat beside the
  launcher. Named for the identity rather than `test_launcher.py`, per the uniqueness rule above.
- `core/launchers/launch-eval-fix/launcher.sh` · `core/launchers/launch-skill-evals/launcher.sh` —
  `[create]` — the eval-fix and skill-evals run launchers. Both carry the `launch-` prefix and are the
  two predating folders named above.
- `core/launchers/companion-self-answer/launcher.sh` — `[create]` — the run launcher for the
  **posture-neutral** `companion-self-answer` skill. **Built, deleted, rebuilt**: a first
  version took a bare `<target>` and addressed it like `experience-visual` — an instance rather
  than a product — and could not reach a satellite living elsewhere, could not take this
  instance's own `<satellite>/<project>` addressing, and could not name which companion to
  answer at all; the owner deleted it whole (`b68d56de`). This version takes
  **`<project> <document>`** instead — `product-fdr`'s own address shape, not
  `experience-visual`'s — resolving the project card and its `Product path:` exactly as every
  `product-*` sibling does, and deriving the pair from `<document>` with **no list of documents
  anywhere in the file**: `<document>` is matched case-insensitively against a **directory entry**
  in one of the project's two document homes — the product's `docs/` and
  `system/projects/<project>/`, where the Agari lives — and used at the case that **file** carries —
  `document` = the matched `<home>/*.md`, `companion` = `<that stem>_open_issues.md` beside it. The
  home is whichever holds the document or its companion; a name found in both is refused rather than
  guessed. The case is read and never
  composed, because six of the seven documents are upper-case on disk and the FDR alone is lower
  (`skills/principal-pm/.claude/skills/product-fdr/SKILL.md`, "The three names are lowercase"), so no casing rule is right for all
  seven and any that tried would need the list this file may not hold.
  Only a name with neither the document nor its companion, in either home, is refused; a companion
  standing alone and a missing companion both launch, and the skill's own Step 1 is what a missing
  companion means for its run.
  Unlike every launcher above, it builds no FIXED `--agent` — **the seat is resolved per run,
  from the companion the run will answer**, never mapped from a table. It reads that companion's
  `re-run \`<skill>\`` line, and reads THAT skill's own launcher's `--agent` value — its
  bare-identity folder first, then the fixed prompt-literal grep the skill's own Step 6 names for
  a folder that does not carry the bare name. No companion, no re-run line, no launcher for the
  named skill, or a seat whose agent file is not on disk — all four fall back to a seatless session
  rather than a halt; the fourth also
  tells the run, in its own fixed prompt, which seat it could not take. **The run's model is the
  producer's:** the `**Model:**` of the `intelligence/<provider>.md` of the skill that `re-run` line
  names, resolved through `run_intelligence.py` and passed as `--model` on every provider, at `--effort high`
  whatever that file's effort says. A producer that cannot be derived, or has no `intelligence/`
  folder, launches with no `--model`; a folder with no file for the provider is refused naming the
  path. No run is ever given a fallback model. Two env overrides
  beyond the usual watcher/notifier pair — `LAUNCH_COMPANION_SELF_ANSWER_LAUNCHERS_DIR` /
  `LAUNCH_COMPANION_SELF_ANSWER_AGENT_GROUPS_DIR` — make seat resolution provable on a fixture tree, never the live
  `core/launchers/` or the host's skill groups. Passes **`--reporter companion-self-answer`**, which
  reads the run's own report file — the highest-numbered `*_self_answer_<N>.md` beside the
  companion, in `self_answer_report_template.md`'s shape — and **`--artifact-path` set to the root
  the reporter globs document homes under** — the resolved product path for a document in its
  `docs/`, the instance root for one in `system/projects/<project>/` — never the companion's own
  file. Provider selection is `--provider claude|codex|gemini|hf|ollama`, then `KENSAIAPP_AGENT_PROVIDER`, else the launcher's `launchers.companion-self-answer` entry in the instance's `.providers.toml`, else a refusal. Every provider's run goes through `core/tools/agent_run.py` and `core/tools/detach_process_watcher.sh`. Claude is launched as a detached `claude --print` run under the resolved seat's `--agent`, and Codex with explicit agent/skill instructions. Every run carries the reporter, document stem, artifact root, completion hook and keep-awake binding. An `hf` run is that same Claude run, aimed at Hugging Face's router, and it is refused before anything spawns when `~/.env` holds no non-empty `HF_TOKEN`. An `ollama` run is that same Claude run, aimed at the local Ollama server, and it is refused before anything spawns when that server does not answer. Same core-shared contract as its neighbours
  (`--instance-root` overrides the instance root, `KENSAIAPP_NOTIFIER` for the notifier);
  invoked `<CORE>/launchers/companion-self-answer/launcher.sh <project> <document>` from the
  instance root. Rebuilt 2026-08-30 under the same bare-identity name v1 held before its
  deletion — no relocation, so no provenance sentence.
- `core/launchers/companion-self-answer/test_companion_self_answer.py` — `[create]` — its
  contract-test suite, flat beside the launcher. Named for the identity rather than
  `test_launcher.py`, per the uniqueness rule above. Pins the `<project> <document>` resolution
  (both positionals required, an unknown flag / trailing prose refused, the `Product path:` line
  read through its trailing HTML comment, external-vs-internal `--add-dir`, the document
  resolved at the case the file carries in both directions — an upper-case argument against the
  lower-case FDR and a lower-case one against an upper-case `PRD.md` — with the derivation
  proven on a name the fixture invents, a missing document refused and a missing companion only
  reported) and `--instance-root`, the fixed prompt on a
  real launch (never paired only with `--dry-run`), the `--reporter` value asserted against the
  real `REGISTRY` in `core/tools/reporters.py`, `--artifact-path` equal to the resolved product
  path, the watcher's CORE_DIR-resolved default-path with the override deliberately
  unset, and all four seat-resolution outcomes — plus a seat grep that does not misread an
  `--agent` mentioned only in a comment — on a fixture tree.
- `core/launchers/chain-product/launcher.sh` — `[create]` — the entry command for a product's whole
  document chain: the spine literal `"PRD,Agari,SRS,UXD,DESIGN,CONTENT,SDD,FDR,ADR,NFDR"` — both
  tiers, so a companion opened on either is swept by one walk — and the name literal `"product"`;
  every producer runs through `core/launchers/skill/launcher.sh` (the owner's ruling,
  2026-09-17), which is the engine's rule, not a flag this launcher passes. It resolves `<project>` and
  its `Product path:`, resolves `KENSAIAPP_NOTIFIER` here and passes it to the engine as a parameter,
  and hands `--keep-awake` down to every launcher the walk runs rather than holding a caffeinate of its
  own. `--provider claude|codex|gemini|hf|ollama`, or an exported `KENSAIAPP_AGENT_PROVIDER`, **forces** every
  round onto one provider and is handed to the engine, which keeps it on the walk's state; with
  neither, each document runs on the provider the instance's `.providers.toml` names for it, and a start
  whose file lacks an entry is refused by name, never defaulted — the rule is
  `core/tools/providers.py`. Its state is
  `system/logs/chain-<project>-state.json`, one walk per project. It replaced
  `chain-definition` and `chain-foundation`, one spine per tier, on 2026-09-17. `--on-end <command>`
  takes the next argument as its value and is carried to the engine, which runs it when the walk
  ends; `build-idea` uses it to be told when a sweep it started is over. Same bare-identity folder
  name, invoked
  `<CORE>/launchers/chain-product/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--on-end <command>] [--dry-run] [--keep-awake]`
  or `<CORE>/launchers/chain-product/launcher.sh <project> --stop` from the instance root.
- `core/launchers/chain-product/test_chain_product.py` — `[create]` — its contract-test suite, flat
  beside the launcher. Pins the guards, the four `Product path:` forms, the `--start` invocation's
  required arguments, the notifier layering, `--dry-run` and `--keep-awake`; the spine literal
  reaching the engine as argv, committed in the script, and holding every document in `chain.py`'s
  registry, upstream first; that every skill the walk starts resolves to a
  `launcher.md` taking `<project>`; and explicit and environment-selected provider propagation.
- `core/launchers/chain-agari/launcher.sh` — `[create]` — the entry command for a walk over a
  project's PRD and then its Agari, so a freshly stamped project can be taken to its Agari without
  the walk running on into the SRS. It carries the spine literal `"PRD,Agari"` and the chain-name
  literal `"agari"`. The folder name is `chain-` plus that chain name, because the engine builds
  the stop command it prints from the name a live walk recorded (`core/tools/walk_stop.py`
  § `stop_command`). It hands the engine the state `system/logs/chain-<project>-state.json`, the
  same file `chain-product` hands it, so the two share one walk per project. Neither starts over
  the other's live walk, and either one's `--stop` ends whichever walk is live. A
  `## Launchers owed` bullet naming a document outside the spine is still walked, by the engine's
  rule. In everything else it is `chain-product/launcher.sh` with its own spine and chain name: the
  same guards, the same `Product path:` resolution, `KENSAIAPP_NOTIFIER` passed to the engine as a
  parameter, and the same `--provider`, `--on-end`, `--dry-run` and `--keep-awake`. Same
  bare-identity folder name, invoked
  `<CORE>/launchers/chain-agari/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--on-end <command>] [--dry-run] [--keep-awake]`
  or `<CORE>/launchers/chain-agari/launcher.sh <project> --stop` from the instance root.
- `core/launchers/chain-agari/test_chain_agari.py` — `[create]` — its contract-test suite, flat
  beside the launcher. It drives the real `launcher.sh` against a stub engine that records its argv,
  and never starts the real engine. It pins the spine literal and the chain-name literal three ways
  each: reaching the engine as argv, committed in the script, and unchanged by an exported
  environment value. It also pins that both spine documents are ones the engine knows and that each
  one's producing skill resolves to a `launcher.md` taking `<project>`, and that the folder name and
  the chain name give the stop command the engine prints. Beyond those it pins the shared state
  path, the four start lines, every refusal, the flags in any order, `--stop` standing alone, this
  bullet pair's place in this section, and the `core/tools/chain.py` bullet naming both entry
  commands.
- `core/launchers/chain-development/launcher.sh` — `[create]` — the entry command for the
  change pipeline, walked as a chain of step launchers. It replaced the Workflow
  (`.claude/workflows/development.js`, deleted 2026-09-18): it resolves `<project>` and its
  `Product path:` the way its chain siblings do and hands the walk to
  `core/tools/chain_development.py --start`. **It passes no spine and no chain name** — the
  pipeline is one fixed sequence with an audit fan-out inside it, so the step table is the engine's
  own literal — and keeps its own state file, `system/logs/chain-development-<project>-state.json`,
  apart from the `chain-<project>-state.json` its siblings share. It spawns no model itself: every
  step's run is started by `core/launchers/skill/launcher.sh`, which detaches that run's watcher,
  holds its `--keep-awake` and tags it, so this script carries no `caffeinate` and no
  `run_telemetry` call. `KENSAIAPP_NOTIFIER` is resolved here and passed as `--notifier`. Its
  `--dry-run` asks the engine's `--describe` first and names the change and the entry step before
  the command it would run, or fails with the reason a start would be refused, so a dry run never
  reports a walk the real start turns away. Same
  bare-identity folder name, invoked
  `<CORE>/launchers/chain-development/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]`
  or `<CORE>/launchers/chain-development/launcher.sh <project> --stop` from the instance root.
  `--provider` is the same force `chain-change` takes, below; its
  `--dry-run` names the provider each step would run on.
- `core/launchers/chain-development/test_chain_development_launcher.py` — `[create]` — its
  contract-test suite, flat beside the launcher. **Named `test_chain_development_launcher.py`, not
  for its identity**, because `core/tools/test_chain_development.py` — the engine's suite — already
  holds `test_chain_development.py`, and the uniqueness rule above forbids the same basename twice.
  Pins the guards, the four `Product path:` forms, every `--start` flag the engine requires with its
  resolved value, the state file being its own, no `--spine` and no `--chain-name`, the notifier
  layering with no real notifier invoked, `--dry-run` calling `--describe` and never `--start`,
  naming the change and the entry step, failing on a refused describe, and printing the exact argv,
  `--keep-awake`, and the absence of any `claude` spawn, `caffeinate` or `run_telemetry` call. The
  engine is stubbed throughout; its decisions are `core/tools/test_chain_development.py`'s.
- `core/launchers/chain-change/launcher.sh` — `[create]` — the entry command for a change unit's
  whole life, from the station that names it to the seal that lands it on `main` and the
  `shukuba-refine` run that re-reads the route after it: the same walk `chain-development` makes,
  entered two steps earlier at `shukuba-open` and `tobiishi-open`, which that command requires a
  caller to have run by hand. Started on a project whose last unit is sealed and not yet refined, it
  enters at the refine. It resolves `<project>` and its `Product
  path:` the way its chain siblings do and hands the walk to the **same engine**,
  `core/tools/chain_development.py --start`, naming the table with `--steps change` — a literal
  here, like `chain-product`'s spine, so a caller reaches into no step table. A second engine would
  be a third copy of the state store, the live-walk refusal, the launch environment and the shim
  write. It keeps its own state file, `system/logs/chain-change-<project>-state.json`, apart from
  both siblings', because one state file **is** one walk and this one has to run beside them. It
  spawns no model itself, and `KENSAIAPP_NOTIFIER` is resolved here and passed as `--notifier`,
  both as its sibling does. **Every start reads the card's `**Definition:**` line and runs the
  definition walk it names before the change walk, never in its place.** `full` runs the project's
  `chain-product` walk and `prd-agari` its `chain-agari` walk, each through that sibling's own
  launcher, so each spine stays written in one place. `none` runs no definition walk, and the start
  is the change walk alone, as it was before the line existed. The value is the text after the
  bold label on the card's one line beginning exactly `**Definition:**`, up to any `<!--` comment.
  No flag and no environment variable sets it, and `Type:` is never read for it. A card with no such
  line, a value other than exactly `full`, `prd-agari` or `none`, and a card carrying the line
  twice are each refused before anything starts, with one line on stderr naming the card and an
  exit code of 1. No value is ever assumed, by the owner's ruling of 2026-10-05. A start prints
  `definition=<value>` after its `product path=` line. Under `full` and `prd-agari` the sibling
  launcher is handed an `--on-end` naming this launcher's end-hook form,
  `<CORE>/launchers/chain-change/launcher.sh <project> --after-definition <token> --definition-ended <end>`,
  and the change walk is started from there only when the definition walk ended `settled` or
  `left_for_the_owner`, the two ends of a walk that walked its whole spine. Every other end, and a
  refused definition start, starts no change walk, and a refused start exits non-zero with the
  sibling's refusal on its stderr. Before the sibling launcher runs, the start writes a
  **pending-launch record**, `system/logs/chain-change-<project>-pending.<token>`, one per launch.
  It holds the product path, the provider force, `--keep-awake`, `--context-cap` and the notifier,
  and the end hook rebuilds from it the change walk the same launch would have started under
  `none`. Three things remove a record, and nothing else does: the launch when its definition start
  is refused, the end hook, which claims it once, and `--stop`, which removes every record of the
  project. `--provider` and `--keep-awake` reach the definition walk, and `--context-cap` does
  not. Its `--dry-run` asks `--describe` first and is answered by the **entry
  step**, not the key: a walk that has not reached `tobiishi-open` has none, and prints
  `change=(none yet)`. A dry run starts no definition walk. Nothing but the project is named to
  it — the station and the change are read off the disk — so starting it again after a stop
  continues rather than restarts. **Its walk's end starts `build-idea`**: the launcher always hands
  the engine an `--on-end` naming `<CORE>/launchers/build-idea/launcher.sh <project> --chain-ended`,
  each word quoted so a core path holding a space survives, and the engine appends its end value.
  `--provider claude|codex|gemini|hf|ollama`, or an exported `KENSAIAPP_AGENT_PROVIDER`, **forces** every
  step onto one provider: it is handed to the engine, kept on the walk's state, set on every step's
  run, and carried to that ending `build-idea` command. With neither, each step runs on the
  provider the instance's `.providers.toml` names for it, a start whose file lacks an entry is refused
  by name, never defaulted, and the ending command carries no provider — the rule is
  `core/tools/providers.py`. Its `--dry-run` names the provider each step would run on. A
  `--stop` is never refused over the `Definition:` line, and it does not stop a definition walk.
  Same bare-identity folder name, invoked
  `<CORE>/launchers/chain-change/launcher.sh <project> [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--context-cap <tokens>]`
  or `<CORE>/launchers/chain-change/launcher.sh <project> --stop` from the instance root.
- `core/launchers/chain-change/test_chain_change_launcher.py` — `[create]` — its contract-test
  suite, flat beside the launcher. **Named `test_chain_change_launcher.py`, not for its identity**,
  on the same rule its sibling's name states: this launcher shares an engine, and so nearly a name,
  with `chain-development`. Pins the guards, the `Product path:` forms, every `--start` flag with
  its resolved value, the state file being neither sibling's, `--steps change` with still no
  `--spine`, the notifier layering with no real notifier invoked, and the dry run — asking
  `--describe` and never `--start`, naming the change and the entry step, printing `(none yet)`
  where there is no key yet, refusing an exit 0 that names no entry step, and failing on a refused
  describe. It also pins the `--on-end` naming `build-idea`, including a core path with a space in
  it, plus explicit and environment-selected provider propagation. **It pins the `Definition:`
  line**: only the bold label at line start is read, and its `<!--` comment is stripped. The three
  refusals each give their exact line on a start and on a dry run, with no engine asked anything,
  and no flag or environment variable stands in for a missing line. The `definition=` line follows
  `product path=`. `none` starts the change walk exactly as before. `full` and `prd-agari` start
  their sibling's walk with its spine and an `--on-end` naming the end-hook form, and the change
  walk does not start at launch. `--provider` and `--keep-awake` reach the definition walk, and
  `--context-cap` does not. The end hook starts the change walk, with the same argv a `none` start
  gives it, only on `settled` and `left_for_the_owner`. Every other end, including one not known
  here, starts nothing and exits 0. A refused definition start exits non-zero with the refusal on
  stderr. The suite also pins the pending-launch record's three removers, one launch's refusal
  leaving another launch's record in place, a stop during a definition walk keeping the change walk
  from starting, a token holding `/` or `..` refused before any file is read, and a card built from
  `core/templates/project_template.md` being accepted. The definition launchers run for real
  against a stubbed definition engine. The change engine is stubbed throughout, except in the one
  test that drops its override to prove the default engine path answers.
- `core/launchers/build-idea/launcher.sh` — `[create]` — the owner's command for the moves a
  `shukuba-refine` report leaves owed: it reads the report's `## Next moves` table and runs it as a
  queue, each row starting when the earlier rows its After cell names have **landed** — read off the
  disk, never off a launcher's exit, because every launcher backgrounds its run and returns at once.
  The report is the sealed unit's (`contexts/CONTEXT_PM.md` names it) or the `<unit-key>` it is
  given, found as `<key>_report.md` in a seed folder; nothing edits that report, and the queue's
  progress is its own state file, `system/logs/build-idea-<project>-state.json`, one queue per
  project. It resolves `<project>` and hands the queue to `core/tools/build_idea.py --start`,
  resolving `KENSAIAPP_NOTIFIER` here and passing it as `--notifier`. It spawns no model, holds no
  caffeinate and declares no completion-watch library: every row's launcher owns its own run.
  `--provider claude|codex|gemini|hf|ollama`, or an exported `KENSAIAPP_AGENT_PROVIDER`, **forces** every
  queued row and nested chain onto one provider; with neither, a skill row runs on the provider
  the instance's `.providers.toml` names for it (a start whose file lacks an entry is refused by name,
  never defaulted) and a nested chain runs each of its steps on its own — the rule is
  `core/tools/providers.py`. Every start states the force, a resume included. Its
  `--dry-run` asks the engine's `--describe` and prints each row with its After and its command.
  `--chain-ended <end>` is what a `chain-change` walk's end passes — `sealed` starts the queue as the
  hook's own start, anything else prints that nothing was started and exits 0. Its `--stop` contract
  is stated in `core/launchers/build-idea/launcher.sh` § USAGE.
  Same bare-identity folder name, invoked
  `<CORE>/launchers/build-idea/launcher.sh <project> [<unit-key>] [--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake] [--context-cap <tokens>] [--chain-ended <end>]`
  or `<CORE>/launchers/build-idea/launcher.sh <project> --stop` from the instance root.
- `core/launchers/build-idea/test_build_idea_launcher.py` — `[create]` — its contract-test suite,
  flat beside the launcher. **Named `test_build_idea_launcher.py`, not for its identity**, on the
  uniqueness rule above: `core/tools/test_build_idea.py` already holds `test_build_idea.py`, and
  pytest imports test modules by basename. Pins the guards, the `--start` flags with their resolved
  values, an optional unit key and a second positional dying, the notifier layering with no real
  notifier invoked, `--keep-awake`, provider propagation, the dry run asking `--describe` and never `--start`,
  `--chain-ended` starting the queue only on `sealed`, `--stop` and its refusals, and the absence of
  any `claude` spawn, `caffeinate` or `run_telemetry` call. The engine is stubbed for those. The
  end-to-end tests run the real launcher and the real engine over a synthetic core whose `skill`,
  `chain-product` and `chain-change` launchers are stubs that record their argv: the station's six —
  After order, a retire row ending the loop, a halt ending it, a failed row ending it, a row with no
  launcher named and skipped, and the report byte-identical after a run — and the stop's two, a stop
  then a chain end starting nothing and a plain start after a stop resuming what is still owed.
- `core/launchers/product-card/launcher.sh` — `[create]` — the owner's one move after the foundation
  step settles: the **card half** (the `product-card` skill in Principal PM posture, writing the
  card's architecture-determined fields and the product's `README.md`) and then the **skeleton half**
  (`core/launchers/product-skeleton/launcher.sh`), in that order. Takes a project name — a bare word;
  a path is refused. **It is the one launcher here that waits.** Every sibling fires `claude --bg`
  and exits in about a second behind a completion watcher; this one runs `claude -p` in the
  foreground and blocks, because `product-skeleton` reads `Languages:` and `Language roots:` off the
  card the first half writes — a backgrounded first half means the second runs against the card as
  it stood before. Two consequences follow and are the reason the divergence is cheap: it carries no
  watcher and no notifier (nothing outlives the script to report on), and its `--keep-awake` is the
  wrapper form `core/tools/test_keep_awake_binding.py` names as its one deliberate exemption, so
  neither fleet-wide guard reaches this file. The skeleton half **dry-runs first** and a dry run
  with nothing to create ends the run reported rather than re-invoked — the owner's *run the
  skeleton only where there is none*, 2026-09-05, held as a report because `product-skeleton`
  already never overwrites and leaves a built frame whole. An unknown argument is refused rather than ignored, which the siblings'
  default-less `case` does not do.
- `core/launchers/product-card/test_product_card.py` — `[create]` — its suite, flat beside it per
  § Owner-run launcher folder's naming rule. Layer 5 throughout: a fake `claude` on `PATH` and a
  stub skeleton launcher reached through `LAUNCH_PRODUCT_CARD_SKELETON`, both recording argv, so
  the order and the already-framed skip are asserted on invocation counts rather than on a disk that
  looks the same either way. No case pays for a model run.
- `core/launchers/product-skeleton/launcher.sh` — `[create]` — the owner-run command that gives a
  product its skeleton once its foundation step has settled: resolves `<project>` and its
  `Product path:` the way its siblings do, then reads the card's `Languages:` and `Package slug:`
  and the product's `docs/SDD.md` § 3 parts table. **Not the fleet's archetype — this one spawns no
  model at all.**
  Every other launcher here builds a fixed `claude --bg` prompt behind an `--agent` seat; this one
  is a copier — it copies the language tree(s) `core/templates/skeleton-templates/<language>/`
  holds for each declared language (excluding that tree's own `README.md`, substituting every
  `__PROJECT__` token in file content and path names with the card's `Package slug:`, or with the
  unit's last path segment when the SDD's units table places the tree at a unit), creates one
  directory per the SDD's parts-table row when the SDD has no units table, and
  exits — no `--agent`, no `--permission-mode`, no completion watcher, no `--keep-awake`. It
  **inspects nothing else it copies**: a tree carrying a placeholder-shaped token the launcher
  cannot substitute is caught by `core/tools/test_skeleton_trees.py` at authoring time, not by the
  launcher at the owner's copy time — the trees are ours, and a scan that runs where the copy
  happens can only refuse something too late, having already had to guess which angle brackets and
  braces were placeholders and which were code. A
  language folder holding only its own `README.md` (`shell/`, today) is a declared absence and is
  skipped and reported rather than copied or refused; a declared language with no folder at all is
  fatal. It never overwrites a file or directory the product already has, and it places each
  frame (a language root, a unit of the SDD's units table, or a language's product-level tree)
  whole or not at all against what the product already holds: a frame with any of its files other
  than a `.gitkeep` already in the product is reported as already built, and none of it is placed. Same bare-identity folder
  name as its neighbours; invoked `<CORE>/launchers/product-skeleton/launcher.sh <project>
  [--dry-run]` from the instance root. Built through `ad-hoc-implementation`, created 2026-09-02
  under the bare-identity name — no relocation, so no provenance sentence.
- `core/launchers/product-skeleton/test_product_skeleton.py` — `[create]` — its contract-test
  suite, flat beside the launcher. Named for the identity rather than `test_launcher.py`, per the
  uniqueness rule above. Builds its own fake project card, `docs/SDD.md` and skeleton-templates
  tree per test, except the tests that read a real tree through the pin (the Rust tree by a card's
  spelling, the Swift tree at a package unit) — the templates root the launcher reads is itself
  overridable (`LAUNCH_PRODUCT_SKELETON_TEMPLATES_ROOT`), the one env-override seam this launcher
  needs though it spawns no watcher to justify the pattern's usual reason. Pins the argument
  contract, the path-shaped-positional refusal, the project/`Product path:` resolution, the three
  before-anything-is-written refusals, `Package slug:` substitution in content and in a path name,
  the three per-language outcomes, that a file the launcher does not understand is copied byte for
  byte (a generic, HTML markup, a format-string brace escape), a tree's own `README.md` never
  copied, the parts-table rows
  becoming directories in the right places, the never-overwrite guard, `--dry-run`'s full listing
  with every refusal still firing, and that no model is ever spawned.
- `core/launchers/skill/launcher.sh` — `[create]` — the **general** launcher: one file for every skill
  that declares an unattended launch, naming none of them. Takes `<skill> [<argument>...]`, resolves
  the skill's directory through `core/tools/skill_path.py`, and reads that directory's `launcher.md`
  (§ *Skills — vendored skill definitions*) for what differs per skill — `**Agent:**`,
  `**Arguments:**`, the fixed
  `**Prompt:**`, and the optional `**Reporter:**` with the `**Reads:**` it needs (`product`, `project` or `instance`), and the optional `**Requires:**` naming the programs the run cannot do without. The file's grammar, and what an argument
  name means (`project` resolves a project and grants its product best-effort, `*path` must exist,
  `reason` is bounded free text for a quoted prompt value, anything else is a bare word), are stated once in this launcher's header. The model and effort a run goes at are
  not in `launcher.md` — a `**Model:**` or `**Effort:**` line there is a declaration defect — but in
  the skill's `intelligence/<provider>.md`, resolved through `core/tools/run_intelligence.py`: its model is
  passed as `--model` and its effort, when declared, as `--effort`, on every provider; a skill with
  no `intelligence/` folder launches on the provider's default; a folder with no file for the
  provider is refused naming the missing path. A defect in `launcher.md`
  is refused naming that file, and a malformed call is refused, both before anything spawns. Everything
  else is the fleet's shape: `CORE_DIR` by the sanctioned expression, `run_telemetry` with
  `skill=`/`project=`, and `--dry-run`. The provider is `--provider`, else `KENSAIAPP_AGENT_PROVIDER`, else the launcher's `launchers.skill` entry in the instance's `.providers.toml`, else a refusal; on Claude the run is a detached
  `claude --print` process `agent_run.py` starts, with `--settings`, and its completion watch runs
  through `core/tools/detach_process_watcher.sh` with `KENSAIAPP_NOTIFIER` and the declared reporter handed what it
  reads as `--artifact-path` — `generic` when a declaration names none, and a best-effort fall back to
  `generic`, with a warning, when the path it reads is not there. The message's
  label is `<instance> · <project> · <skill>` — the instance being the folder name of the git
  checkout the launch runs in (for a worktree, the checkout it was cut from), else the instance
  root's folder name, and the project left out when the run takes none. A skill resolved under `skills/<group>/` has that group
  granted with `--add-dir` on the Codex path, read off where the skill lives rather than off
  `**Agent:**`, because a grouped skill is hidden from a session at startup; a flat skill gains no
  flag there either. On the Claude path a grouped skill's group reaches the run through the pin's
  plugin instead ("Every launcher enters the pin first", above), and the launcher passes no group
  `--add-dir` at all. `--provider hf` is the Claude run, aimed at Hugging Face's router, and it is refused before anything spawns when `~/.env` holds no non-empty `HF_TOKEN`. `--provider ollama` is the Claude run, aimed at the local Ollama server, and it is refused before anything spawns when that server does not answer. `--provider codex`
  is the first parallel provider path: it asks `<CORE>/tools/agent_run.py` to launch detached on the
  intelligence file's model and effort, and prepends
  explicit instructions to read the named agent and skill because Codex has no Claude-style
  `--agent` switch. Its inherited environment carries instrumentation and its lifecycle goes to a
  named JSONL log. `watch_process.py` observes that log and process through the provider-process
  detach home, carrying the declared reporter, `DETACH_WATCHER_ON_COMPLETE`, and `--keep-awake` exactly as it does for a Claude run. Opens no worktree. Invoked
  `<CORE>/launchers/skill/launcher.sh <skill> [<argument>...] [--provider claude|codex|gemini|hf|ollama] [--model-tier fable|opus|sonnet|haiku] [--dry-run]
  [--keep-awake]` from
  the instance root. Created 2026-09-15 under the bare-identity name — no relocation, so no provenance
  sentence.
- `core/launchers/skill/test_skill.py` — `[create]` — its contract-test suite, flat beside the
  launcher, named for the identity per the uniqueness rule above. Every fixture writes its own
  `launcher.md` into a `tmp_path` instance; tests read the shipped
  `skills/pm/.claude/skills/tobiishi-open/launcher.md`, `nemawashi-pick`'s, `nemawashi-unpick`'s,
  `tobiishi-drop`'s, `shukuba-refine`'s, `shukuba-retire`'s, `project-agari`'s, `nemawashi-drop`'s and
  `seeds-from-product-docs`'s, and
  one holds every shipped `**Reporter:**` to the `--reporter` and path of the dedicated launcher its
  skill still has. Pins the group grant — a grouped skill's
  group, read off its location and granted beside the product, and none for a flat skill — the call's refusals and the declaration's (each
  naming the file, `--dry-run` included), the optional `[ … ]` segment, a `reason` value's bounds, a `-`-led value holding a space accepted
  only as a `reason` and a `--`-led one never, the prompt read off the spawned
  argv, the product grant and the reporter's path never refusing, `--dry-run` printing exactly the
  spawned command, the telemetry and completion-watch tails, and that the launcher's code names no
  skill. The intelligence cases pin the file's model and effort on the command of every provider, a
  missing provider file refused, a malformed one refused, and a skill with no folder launching with
  neither. The Codex cases pin explicit and environment provider selection, the agent
  and skill bootstrap prompt, detached JSONL launch, completion observation, hook forwarding and
  keep-awake binding.

> **The destination is settled; the migration is incremental.** Owner-run launchers belong in their own
> folder here — that is decided (owner, 2026-07-27), superseding both the earlier `core/tools/launchers/<name>/`
> nested layout and the reading that the flat launchers would never move. What remains a matter of pace, not
> direction, is *when* each flat launcher migrates: one at a time, as the owner calls it. Background on how
> the two homes were told apart lives in the `tools` project's own journey.

### Git-native hooks — commit-time enforcement via `core.hooksPath`

`[create]` — git-native hooks that run on every commit-creating operation, whichever surface (a human,
Codex, or Claude) runs `git commit`: a `commit-msg` hook that presence-checks the required commit
trailers, and a `pre-commit` hook that blocks a commit whose staged content carries a written-forward
violation. Distinct from the `.claude/hooks/` layer above: those are Claude Code harness hooks; these
are git's own. Audit enumerates these paths; Init auto-creation follows the same later-increment
posture as the `.claude/` layer.

- `core/githooks/commit-msg` — `[create]` — git-native hook shim (bash, stdlib): self-locates core from
  its own directory and execs the checker with git's message-file path.
- `core/tools/verify_commit_msg.py` — the trailer checker the shim execs; enumerated in the shared-tools
  layer above (its home-of-record).
- `core/githooks/pre-commit` — `[create]` — git-native hook shim (bash, stdlib), beside `commit-msg`:
  self-locates core the same way, resolves the committing repo separately via `--show-toplevel` (the
  two roots differ whenever a satellite commits), and execs `written_forward.py` in `--staged` mode. Does not
  fire on a `--no-ff` merge — git invokes `pre-merge-commit` for that, and none is registered.
- `core/tools/written_forward.py` — the written-forward checker the shim execs; enumerated in the
  shared-tools layer above (its home-of-record).

> **Wired by `resolve_core.py`, because the clone cannot carry it.** `core.hooksPath` is **local,
> untracked** git config, so no clone brings it and until it is set the hook is inert — a commit with no
> trailers is accepted in silence, with nothing to notice. The `resolve_core.py` SessionStart hook sets it
> to `<resolved-core>/githooks` when it is unset; resolution owns the verb because the target *is* the
> resolved core, which also means a `set_core` that repoints core is picked up on the next session.
>
> It declines to act on four guards, each preventing a *silent* breakage: the githooks dir must exist; the
> main working tree only (linked worktrees **share one `.git/config`**, and a worktree resolves core to its
> own copy — writing from inside one would repoint every tree at a path that dies with that worktree); never
> over an existing value; and never when `.git/hooks/` holds an active (non-`.sample`) hook, since
> `core.hooksPath` makes git ignore that directory **entirely** and would silently disable a user's own
> hooks. Fail-open — a wiring failure never breaks the session. Pinned by `.claude/tests/test_resolve_core_githooks.py`.
>
> Setting a path pointer in the project's own `.git/config` is within the harmless principle above (it is
> repo-local, not the user's global config), and it does not re-open `a7c6db6`'s retirement of
> inject-and-block: it performs no verification and rewrites no commit — it enables the git-native checker
> that retirement handed verification to.

### Role layer — split by scope (instance loaders flat under `system/`; per-project PM context under `system/projects/`; shared cross-role + globals in `core/`)

**App-level loaders** (`system/loaders/`) — `[create]`, stamped from
`templates/role-templates/overlay_template.md` for the thirteen roles that read no context, and from
`templates/role-templates/pm_overlay_template.md` for **pm** (its own template, because its
on-invocation context read is a structural difference, not a substitution). The stamped file's
**domain section is deliberately undeclared** — authored per instance when the instance has a domain to
declare, and **never copied from a sibling instance**, whose overlay names that sibling's truths.
Drift-checked against the global loader + this manifest; never overwritten after stamping.
One file per **prefix-invoked** role; filename is just `<role>.md` (no project slug, path provides scope).
A thin overlay: points at its `core/` global for posture. The **pm** overlay carries an on-invocation
context read by construction — the directed project's per-project
`system/projects/<name>/contexts/CONTEXT_PM.md` (§2), written by the change lifecycle. **An instance may
give another overlay a context read of its own**, at `system/contexts/CONTEXT_<ROLE>.md`: that file is
the instance's, hand-maintained, stamped by nothing, and its overlay says so. The one section skills
write is the Principal PM's `## Picked seeds`: `nemawashi-pick` appends a line, and `nemawashi-unpick`,
and `nemawashi-drop` remove it. Every other overlay
carries no context read — posture from the global, live state from the project's `journey/`.
**Fourteen roles** — qa excluded (fork-invoked, no prefix, so no app-level loader; qa is global-only —
see the contexts note below):
- `system/loaders/cpo.md`
- `system/loaders/cto.md`
- `system/loaders/cdo.md`
- `system/loaders/architect.md`
- `system/loaders/tech_lead.md`
- `system/loaders/developer.md`
- `system/loaders/content_manager.md`
- `system/loaders/content_editor.md`
- `system/loaders/product_owner.md`
- `system/loaders/pm.md`
- `system/loaders/principal_pm.md`
- `system/loaders/principal_architect.md`
- `system/loaders/scrum_master.md`
- `system/loaders/senior_engineer.md`

**Contexts** — **the stamp produces one.** The only context setup creates is the **PM's**, and it is
**per-project** — `system/projects/<name>/contexts/CONTEXT_PM.md` (§2), holding one item: that project's
current change from the PM's view. The other thirteen roles are stamped with **no context** — posture from
the loader, live state from the project's `journey/`. qa has none (fork-invoked, global-only). An
instance may still give an overlay a hand-maintained context of its own; where it lives, what its
overlay must say and the one section a skill writes are the app-level loaders paragraph above, and a
file there is not drift.

**Cross-role contract — two tiers** (mirrors the loader split: shared core + app-level overlay):
- `core/roles/CROSS_ROLE.md` — `[create]` — the **shared** cross-role contract (instance-agnostic,
  vendored into `core/` like the global loaders).
- `system/CROSS_ROLE.md` — `[create]`, stamped from `templates/role-templates/cross_role_template.md`
  — the **app-level** instance overlay, flat top-level under
  `system/` (sibling to `system/loaders/`, `system/michi.md`, `system/nemawashi/`).
  Carries instance-specific cross-role additions and points at the core contract.

**Global loaders — live in `core/`:** `core/roles/loaders/<role>_global.md` — the shared posture layer
each `system/loaders/<role>.md` overlay points at.

**Delegate contract — live in `core/`:** `core/roles/delegate_contract.md` — `[create]` — the body of
the `delegate` carrier (`skills/interactive/.claude/agents/delegate.md`), holding what every delegated run owes: routing,
verification, measurement, surfacing, committing and its `Role:`, its fence, and the `delegate-report.md`
every run leaves. Not a
loader and not a posture — the delegate has neither — but the same carrier→body pair, and the audit
checks the file itself, since the agent that points at it has no other instruction.

**Role lenses — live in `core/`:** `core/roles/lenses/` — `[create]` — the lens set an audit of the
**role layer** reads with, sibling of `loaders/` and enumerated as its own layer so a missing lens is a
reported gap. One file per failure shape, each versioned on its own, plus a `README.md` indexing the
set. A **second set**, not part of `core/doctrine/kaizen/lenses/`: that set judges a skill through its
output, and a role emits no artifact of its own, so its question is a different one — the arrangement
its own § *What does not live here* sanctions. Which shapes exist and how the set grows are the
`README.md`'s; this manifest owns only where the folder sits.

### Prompts layer — a skill's own `prompts/`, and the shared ones under `core/prompts/`

`[create]` — the **fat authoring prompts** the thin definition skills read on demand. **A prompt lives
beside the skill that reads it**, as that skill's `prompts/rich.md` (a thin judgment prompt beside it is
`prompts/thin.md`, as `nemawashi-pick`'s is). **`core/prompts/` holds only what no single skill owns** —
a prompt more than one skill reads, or one a seat's session or a launcher reads with no skill above it.
The move into the skills was the owner's call, 2026-10-04. Each definition
skill is a thin orchestrator that **points at** its prompt, and the prompt **owns the authoring
doctrine** — so a content fix lands in the prompt, never in the skill (the shipped `product-prd` /
`product-srs` split; the causal chain is
`system/projects/product-definition/docs/product-prd-split/00_ROOT_CAUSE.md`). Create if missing, never
overwritten (a user may customize one). **Drift-checks:** a prompt is core-referencing material read by
the skills — it points into core **only** via `<CORE>`; a literal `core/…` or any `~/.claude/…` path is a
defect (same check as skills / loaders / agents). Audit enumerates these paths; Init auto-creation follows
the same later-increment posture as the `.claude/` layer.

**A second path check, same reason, other direction.** These files are vendored: every satellite binds
this folder and reads the same bytes, so a prompt naming a **per-instance** path must name it in a form
that resolves wherever it is read. A placeholder (`system/projects/<name>/agari.md`) or a glob
(`system/projects/*/doctrine/`) resolves against the reading instance and is the working form. **A
literal project name — `system/projects/product-planning/…` — is a host-only reference**, and a
satellite reading it finds nothing: a consumer satellite may hold a single project of its own, and
neither `product-planning` nor `roles` need be among its projects. Two forms are permitted and no third:

- **A placeholder or a glob**, which is what the layer already uses in most of its citations —
  `grep -rn "system/projects/" core/prompts/ skills/*/.claude/skills/*/prompts/` returns 25,
  re-measured 2026-10-04.
- **A literal host path explicitly marked as host-only provenance**, where the file also says that
  nothing in it depends on opening the path. That is for a *where this was decided* pointer, never for
  an input a run must read.

`grep -rn "system/projects/[a-z]" core/prompts/ skills/*/.claude/skills/*/prompts/` is the whole check
and returns nothing today. Stated
2026-08-26, after six citations — five of them a day old — named a project only the host carries.

- `core/prompts/codex_execution.md` — shared Codex execution-permission prompt, supplied by the native skill runner.
- `skills/cpo/.claude/skills/product-prd/prompts/rich.md` — CPO PRD-authoring lens.
- `skills/cto/.claude/skills/product-srs/prompts/rich.md` — CTO SRS-authoring lens.
- `skills/cdo/.claude/skills/product-uxd/prompts/rich.md` — CDO UXD-authoring lens.
- `skills/cdo/.claude/skills/product-design/prompts/rich.md` — CDO design-language authoring lens.
- `skills/content-manager/.claude/skills/product-content/prompts/rich.md` — Content Manager verbal-language authoring lens, read
  by `product-content`. Under the **Content Manager**'s skills, not the CDO's — `CONTENT.md` is that seat's. The one prompt here that
  states its seat's authority in full rather than pointing at a posture body for it: the split it applies
  — meaning against wording, experience against words — fires line by line while authoring, so it belongs
  in the file under the author's hands.
- `skills/cdo/.claude/skills/experience-visual/prompts/rich.md` — CDO lens for an **instance's** visual experience layer,
  read by `experience-visual`. The one prompt here whose subject is the instance rather than a product.
- `skills/content-manager/.claude/skills/experience-voice/prompts/rich.md` — Content Manager lens for an **instance's**
  verbal experience layer, read by `experience-voice`. Instance-subject like the one above it. Its seat
  is delivery-tier rather than executive, as the three PM lenses below it are.
- `core/prompts/pm_right_size.md` — the PM's **sizing test**, and only that: read by `tobiishi-open`
  sizing the change that reaches an open station, and by `stations-from-seed`'s prompt sizing a station, which
  quotes the test rather than rewording it. It carried the no-station proposal logic — read-first
  inputs, a short menu of candidate changes, and the stop that waited on the owner — until 2026-09-06,
  when that run stopped proposing and the sections describing it were cut rather than left to
  reinstate the stop. Renamed from `pm_next_change.md` in the same change, because a file named for
  the next change described the run that was cut out of it. **The one prompt in `core/prompts/` whose name has no
  artifact slot** — the `<role_file>_<verb>_<artifact>` form its core neighbours take would need one noun, and its two
  callers size different ones (a station, a change unit); the test holds for both, so naming either
  in the filename or the section would narrow it. **No live machinery cites the old path** — the only
  occurrence outside a record is the sentence above, naming the rename. Everything else that still spells
  `pm_next_change.md` is a record of what was true when it was written, and records are not repaired:
  journey `trail/` entries, a project's `docs/`, the live journey files of the change that made the
  rename, and one retired `agari.md`. The homes are listed because a reader applying the path-repair
  standing rule needs to know which hits to leave; the list is what disk held at the rename and is not a
  guarantee no record elsewhere names it.
- `skills/pm/.claude/skills/stations-from-seed/prompts/rich.md` — PM seed-splitting lens, read by `stations-from-seed`: what a station
  is and is not, why the checklist a seed arrives with is a proposal, how one seed becomes 1 to N
  stations, the reached-when that a fresh session can check, the six defects the loader names, the
  divergence log, what the split does not write, and the four cases it stops on. The PM's second lens,
  and the two sit at different moves — this one settles a picked seed's whole route, `pm_right_size.md`
  sizes each unit that route is walked in, and this file is one of the two that read it.
- `skills/pm/.claude/skills/shukuba-refine/prompts/rich.md` — PM review lens for a sealed or halted unit, read by `shukuba-refine`: what a
  unit's records are read for, the six shapes a finding takes, the hold list, which of the six
  moves each finding owes, companion over recommendation, what the run never does, and the what / why
  / where-from every entry carries. The PM's third lens, and it sits after a unit lands, where
  `stations-from-seed`'s sits before a seed is walked.
- `skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md` — Principal Architect recording-and-binding
  lens, read by `product-architecture`: the inputs and their authority order, the three surfaces the SDD
  surfaces a decision on, the three significance gates, the ownership test, the constraint bar and its
  two verification classes, the unsettled-input rule, the two lifecycles and the finish walk. One body
  for both records, because one run writes both. Carries the seat's **improve clause** — the executive
  half of `adding_a_role.md`'s loader-or-prompt split.
- `core/prompts/principal_pm_cut_seeds.md` — Principal PM idea-cutting lens, read by
`seeds-from-idea`, and by `seeds-from-product-docs` and `ad-hoc-plan` for its grounding pass, which is why
it stays in core: what an idea is and is not, the grounding pass and its three outcomes, the seedbed
sweep, how one idea becomes 1 to N seeds, the owning project the Agari decides, where the seed lands,
when a routing seed is earned, the trace back to the idea, and the four cases a cut stops on. **The one
prompt in `core/prompts/` whose verb slot is not `create`** — the `<role_file>_<verb>_<artifact>` form takes
the real verb, and this seat cuts rather than creating a document. It restates neither the four defects and three
seed tests of `core/roles/loaders/principal_pm_global.md` nor the seed shape of
`core/templates/journey-templates/nemawashi_template.md`; it points at both.
- `skills/principal-pm/.claude/skills/seeds-from-product-docs/prompts/rich.md` — Principal PM **document**-cutting lens, the
  sibling of the one above and the second of that seat's two cutting paths: the four documents a cut
  draws from (SDD, FDR, ADR, NFDR) against the five it only reads for faithfulness (PRD, SRS, UXD,
  `DESIGN.md`, `CONTENT.md`) and the double-cut the split prevents, the 上がり Agari as the cut's
  **filter and routing key** rather than an input, the four kinds of seed a document set yields
  (downstream, documentation, upstream through the owning document's companion, scaffold), the
  priority-and-incremental-slicing judgment the documents do not make, what the SDD's § 7 order and
  § 8 slice→seed map bind the seat to, and the three-position sweep of the product's own seedbed that
  a **re**-cut needs and a one-shot idea cut does not. It restates neither that sibling — grounding, the sweep's outcomes, the four stops,
  the no-interview rule, the re-run fold and the tone are read there — nor the file loop, which is
  `<CORE>/prompts/principal_pm_cut_seeds_run.md`'s.
- `skills/principal-pm/.claude/skills/seeds-from-idea/prompts/rich.md` — the idea cutter's own lens, read by
  `seeds-from-idea` before `core/prompts/principal_pm_cut_seeds.md`, which it extends. It tightens three things for an
  idea cut only: one seed unless the idea's own words name more, a routing seed only when the owner asks for one,
  and no input from a `drop/` folder, a revert or a dropped attempt as grounding or a proof subject. It sits
  beside the skill rather than in the shared lens because `seeds-from-product-docs` reads that lens too.
- `core/prompts/tech_lead_create_tl_instruction.md` — the Tech Lead's planning body, read by
  `development-plan` and `ad-hoc-plan`: how a `tl_instruction.md` is reviewed, cut into tasks,
  written and committed once the change's spec and design are in its worktree. The two skills differ
  in how they reach that point — the pipeline's spec and design, or stubs `ad-hoc-plan` writes from a
  brief — and in nothing they plan by. The plan's shape stays `development-plan`'s
  `references/tl_instruction_template.md`.
- `core/prompts/senior_engineer_repair_dependencies.md` — the Senior Engineer's rules for answering a
  product's dependency advisories: the edge of a repair, the audit the NFDR names, the owner's repair
  rulings quoted word for word, the one answer each advisory takes, the exception record and its upkeep
  row, and how a forbidden move waits for the end. Read by `development-security` on a change's branch
  and by `dependency-repair` on a branch off a red `main`.
- `core/prompts/principal_pm_cut_seeds_run.md` — the run shape both cut prompts share, read by
  `seeds-from-idea` and `seeds-from-product-docs` beside their method prompt. What it carries is stated
  once, in the skills layer's cutter block above.
- `core/prompts/qa_create_acceptance.md` — QA acceptance-file authoring lens, covering all three
  acceptance artifacts with one method. Read by the seat's own session, since each of the three
  `development-acceptance-*` skills writes a file whose gates pass unconditionally.
- `core/prompts/ratify_skill.md` — skill-ratification lens.
- `skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` — the answering lens, read by `companion-self-answer`: the
  four checks in order with check 1 gating the rest, the six verdicts each carrying its *why*, and the
  rule that a verdict the run needs and cannot name is reported rather than forced into the nearest
  word. Like `ratify_skill.md` it serves a judgment rather than a seat: its launcher resolves the
  posture per run from the companion being answered. It creates no document either: it decides, and
  the skill writes.
- `core/prompts/declare_loader_domain.md` — the lens for declaring one seat's domain in one instance,
  writing § *The domain* of `system/loaders/<role>.md`. **Role-agnostic**, and so named: the reasoning
  is identical for every seat and only the seat changes, which is why it takes a role-neutral name like
  `ratify_skill.md` above rather than the `<role_file>_create_<artifact>` form the other prompts left in
  `core/prompts/` use. It is read by no skill — the seat's own session reads it directly (step 2b of
  `setting_up_an_instance.md`).
- `skills/cto/.claude/skills/product-sdd/prompts/rich.md` — CTO SDD-authoring lens: the whole-document lens the CTO's
  `product-sdd` run reads — the shape, the seams, the conditions, the order and the
  machine-checkable bars, and how a part the CPO or the CDO decides is drafted best-effort and
  raised as a `Seat:`-tagged companion item — including how an architecture shape is weighed for
  the SDD's § 2. Listed in the skill's `stack.json`.
- `core/prompts/cto_create_domain_doctrine.md` — CTO lens for an **instance's** domain doctrine,
  `system/doctrine/kensaiapp_doctrine.md`.
- `core/prompts/cto_create_ai_responsibility.md` — CTO lens for an **instance's** AI-responsibility
  layer, `system/doctrine/ai_responsibility.md` § 1 (§ 0 is core's and § 2 starts empty).
- `core/prompts/cto_create_doctrine_structure.md` — CTO lens for an **instance's** doctrine
  meta-layer, `system/doctrine/doctrine_structure.md`, which classifies what the other two produce.

  **Five prompts here have no skill above them** — the three CTO lenses immediately above, read by the
  seat's own session at step 2a of `setting_up_an_instance.md`, `declare_loader_domain.md` at step
  2b, and `qa_create_acceptance.md`, whose seat verifies directly because the skills that would carry
  the loop pass every gate by construction. `ratify_skill.md` has none either and is launcher-read
  rather than seat-read. A prompt read this
  way leaves no `Skill-Version:` on the commits it produces — a known gap, tracked as a seed in the
  `tools` project's own nemawashi.

### Templates layer — vendored stamping shapes under `core/templates/`

`[create]` — the **single-source shapes** stamped from (`project-stamp` stamps a project's files;
the definition skills stamp product docs; `spawn_satellite.py` stamps an instance's own). Referenced throughout this
manifest as "stamped from `templates/…`" — enumerated here as their own audited layer so a **missing
template is a reported gap, not a silent stamping failure**. Create if missing, never overwritten.
**Drift-checks:** templates are prose shapes with `<PLACEHOLDER>` tokens, not core-pointing plumbing —
like the tools they are **not** in the `<CORE>`-substitution set; but where a template *does* point into
core it uses `<CORE>` (a literal `core/…` is a defect — **2 today**, both in `journey-templates/`:
`nemawashi_template.md:11` and `shukuba_template.md:11`; the count read 0 until it was measured on
2026-08-29 and had been wrong for as long as those two lines have existed). The harmless principle holds: no
host-global `~/.claude/…`. Audit enumerates these paths; Init auto-creation follows the same
later-increment posture as the `.claude/` layer.

**What format a template must be in is not this manifest's rule** — it belongs to whoever adds a
template, and lives beside them:
- `core/templates/README.md` — a template's format follows its consumer. A **model**-read template
  (the `product-*` skills, `project-stamp`'s document steps) may carry frontmatter and `<!-- -->`
  guidance, because the model authors a fresh document and never copies it. A **script**-read template
  (`spawn_satellite.py`) is the file itself with `<token>` placeholders and nothing else, because
  anything it carries has to be removed by code. The README also states the manifest entry below as a
  required step when adding one.

Instance / root stamping — **stamped by `core/tools/spawn_satellite.py`** (`_stamp_instance_files`):
- `core/templates/agents_md_template.md` · `kensaiapp_md_template.md` · `claude_md_template.md` ·
  `gitignore_template.md` ·
  `claude_design_instructions_template.md` · `michi_template.md` ·
  `nemawashi_template.md` · `instance_setup_seed_template.md` · `system_shukuba_template.md` ·
  `kensaiapp_doctrine_template.md` · `ai_responsibility_template.md` ·
  `doctrine_structure_template.md`

The instance's **role layer** (`core/templates/role-templates/`) — one of seven scope folders, beside
`product-templates/`, `project-templates/`, `journey-templates/`, `experience-templates/`,
`writing-bar-templates/` and `authoring-templates/` — **stamped by
`spawn_satellite.py`**
(`_stamp_role_layer`):
- `role-templates/overlay_template.md` — `system/loaders/<role>.md` for the thirteen context-free roles
- `role-templates/pm_overlay_template.md` — `system/loaders/pm.md`
- `role-templates/cross_role_template.md` — `system/CROSS_ROLE.md`

**Those two groups together are the whole spawn-time subset** — thirteen templates, ten in the
instance/root group and three in the role group. `spawn_satellite.py`
reads no template outside them, and nothing else reads one of theirs **except
`ai_responsibility_template.md`, which is also stamped per-project** by `stamp_project.py` — the
one dual-scope template, and why it sits flat rather than in a scope folder. Every group below is
stamped on demand, by the stamper named on it.

Two more live in the same folder and are **not** spawn-time — `spawn_satellite.py` never reads
them. They are stamped when a **role is added** (`adding_a_role.md` steps 1 and 4), which is a
galaxy-wide act rather than a per-instance one, because the agent file lands in the host's group and a pinned run in any instance takes its agents from the host:
- `role-templates/global_loader_template.md` — `<CORE>/roles/loaders/<role>_global.md`
- `role-templates/agent_template.md` — `skills/<role>/.claude/agents/<role>.md`

The instance's **experience layer** (`core/templates/experience-templates/`) — **read by a model, no
stamper**: the `experience-visual` and `experience-voice` skills read these and author fresh documents
into `system/experience/` at setup steps 4a and 4b. Not spawn-time — `spawn_satellite.py` reads none of
them. Seven shapes: three per half, plus the handoff between the halves. Neither half's three bind
the other's; the seventh is neither half's and both resolve to it:
- `experience-templates/visual_restrictions_template.md` — `system/experience/visual_restrictions.md`
- `experience-templates/visual_direction_template.md` — `system/experience/visual_direction.md`, in the
  external DESIGN.md format one layer up from a product's own design language
- `experience-templates/visual_open_issues_template.md` — **both** of the visual half's companions
  (`visual_restrictions_open_issues.md`, `visual_direction_open_issues.md`); one shape rather than two
  near-identical ones, since the two documents raise the same kinds of item
- `experience-templates/voice_restrictions_template.md` — `system/experience/voice_restrictions.md`
- `experience-templates/voice_direction_template.md` — `system/experience/voice_direction.md`. Prose end
  to end: the verbal half has no vendor format and no linter, so the shape is this file's own
- `experience-templates/voice_open_issues_template.md` — **both** of the verbal half's companions
  (`voice_restrictions_open_issues.md`, `voice_direction_open_issues.md`). It is its own file rather
  than a second use of the visual shape because it carries a third bucket the visual half has no use
  for: an entry originating in words that also reaches the visual medium, which the second author can
  record but not write
- `experience-templates/visual_voice_contract_template.md` — `system/experience/visual_voice_contract.md`,
  the handoff the ordered pair turns on. `experience-visual` **creates** the file from this shape on the
  first run of the pair; both halves then read the stamped document's own header. The one shape here
  belonging to neither half, and the only one with no companion beside it: a handoff persists and its
  absence is a defect (`setting_up_an_instance.md` § The three rules, rule 1)

The instance's **writing bar** (`core/templates/writing-bar-templates/`) — **read by a model, no stamper**:
the `kensaiapp-writing-bar` skill reads these and authors fresh documents into `system/doctrine/` at
setup step 3. Not spawn-time — `spawn_satellite.py` reads neither. Two shapes, and a run lands both:
- `writing-bar-templates/writing_bar_template.md` — `system/doctrine/writing_bar.md`, the step's
  output. Every instance holds one; core states no bar to fall back on (§ Instance-shared doctrine)
- `writing-bar-templates/writing_bar_open_issues_template.md` — `system/doctrine/writing_bar_open_issues.md`.
  Its own file rather than a reuse of a sibling companion shape because its first section carries the
  whole bar for the owner to confirm in one place, which no sibling companion does

The instance's **authoring shapes** (`core/templates/authoring-templates/`) — **read by a model, no
stamper**: an author building a new stack reads these and writes a fresh file. Not spawn-time —
`spawn_satellite.py` reads none of them. Their output is **machinery** rather than a document —
which the role group's shapes are too, but those produce the role layer specifically and sit under
its scope, while a stack's three layers cut across every scope folder here. That is why these sit in
their own rather than under an existing one. What may be written in each layer they shape is
`authoring_layers.md`'s; these carry the shape it produces, measured off the stacks on disk, and
each names the divergences it did not resolve rather than picking one silently. Three shapes, one
per layer of a stack — the orchestrator, the thinking, the section shape:
- `authoring-templates/skill_template.md` — one `.claude/skills/<name>/SKILL.md`, the orchestrator
  half of a stack: the eleven-key frontmatter, the posture refusal, the file-and-loop table, the
  four-step workflow, and the register of what the six measured skills disagree about
- `authoring-templates/authoring_prompt_template.md` — one skill's own `prompts/rich.md`,
  the layer a stack's substance lives in. Alone of the three it shapes a **header and not a body**:
  across the eight `*_create_*` prompts the header block is eight of eight, while no `##` section
  below it is carried by more than four of them, so the file carries a register of the recurring
  moves with their counts in place of a section list it would have had to invent
- `authoring-templates/document_template_template.md` — a stack's **document template** and the
  `*_open_issues_template.md` companion beside it. The doubled word is the layer's naming convention
  applied honestly: it is a template whose output is a template

Per-project stamping:
- `core/templates/project_template.md` · `project_doctrine_template.md` · `context_template.md` ·
  `change_request_template.md` · `journey_nemawashi_template.md` · `journey_shukuba_template.md` ·
  `project-templates/agari_template.md` · `project-templates/agari_open_issues_template.md` ·
  `project-templates/setup_seed_template.md` · `ai_responsibility_template.md`

  The last is the **dual-scope** template — stamped here *and* in the instance group above, which
  is why it sits flat rather than in a scope folder.

Journey artifacts (`core/templates/journey-templates/`) — **read by a model, no stamper**. These hold
the shape of **one item**; the folder READMEs above (`journey_nemawashi_template.md`,
`journey_shukuba_template.md`, `nemawashi_template.md`, `system_shukuba_template.md`) hold the shape of
the **folder** and are copied bytes. Same names, opposite consumers — `core/templates/README.md` § the
two-consumer table is why:
- `journey-templates/nemawashi_template.md` — one 根回し Nemawashi seed, authored into
  `journey/nemawashi/unpicked/<YYYY-MM-DD>_<slug>.md` — the candidate pool, never the seedbed root,
  because lifting one to the root is the PM's pick — by the **Principal PM** cutting seeds; and into
  `system/nemawashi/…` by the Principal PM alone, which no PM can reach.
  The instance **setup seed** is the one seed no seat authors — it is stamped, from its own
  script-facing template (§1).
- `journey-templates/shukuba_template.md` — one 宿場 Shukuba station, authored into
  `journey/shukuba/<YYYY-MM-DD>_<slug>.md` by the **PM** when it opens the station
  (`<CORE>/docs/michi_agari.md` § *Who owns each step — and where the seeds come from*, the row *Open the station*). Project level only — the instance's `system/shukuba/` is a router
  and is never walked.

- `journey-templates/shukuba_refine_report_template.md` — one `shukuba-refine` report, authored into
  `journey/nemawashi/<idea>/<unit-key>_report.md` by the **PM** after a unit lands.
- `journey-templates/shukuba_refine_recommendations_template.md` — that run's recommendations to the
  Principal PM, authored into `journey/nemawashi/<idea>/<unit-key>_recommendations.md` beside it, every
  run.
  No template for a 飛び石 Tobiishi item: a change unit is opened by `tobiishi-open` and its documents
  are stamped from `change_request_template.md` and the `development-*` skills, so the gap these two
  close does not exist there.

Product decision-records (authored from, in the foundation step — not stamped at scaffold):
- `core/templates/product-templates/fdr_template.md` · `product-templates/fdr_open_issues_template.md` ·
  `product-templates/adr_record_template.md` · `product-templates/adr_index_template.md` ·
  `product-templates/nfdr_template.md` · `product-templates/architecture_open_issues_template.md`

  **The trio sits in one folder, and that was the Principal Architect's stack to settle** (2026-08-30).
  It sat in two until then, deliberately (owner, 2026-08-28): the FDR pair was in `product-templates/`
  because it carried the definition-tier stack shape — a thin skill, a fat prompt, and a document
  template with the companion that makes the loop's done signal work — while `adr_template.md` and
  `nfdr_template.md` sat flat at the templates root with no such stack behind them. `product-architecture`
  gave the ADR/NFDR pair that same shape, so the reason for the split went with it. **The move was
  earned by the stack, not by the name** — the earlier instruction not to tidy the trio together on the
  strength of its name still holds for anything else that shares it.

  **The ADR is many files, one per decision.** `adr_record_template.md` shapes one record at
  `<Product path>/docs/adr/NNNN-slug.md`; `adr_index_template.md` shapes the index over them. The log is
  append-only — a reversal supersedes, never rewrites — which is why the unit of the template is one
  record rather than one document.

Product upstream-docs (`core/templates/product-templates/`, stamped by the definition skills):
- `product-templates/prd_template.md` · `prd_open_issues_template.md` · `srs_template.md` ·
  `srs_open_issues_template.md` · `uxd_template.md` · `uxd_open_issues_template.md` ·
  `design_template.md` · `design_open_issues_template.md` · `content_template.md` ·
  `content_open_issues_template.md` · `sdd_template.md` · `sdd_open_issues_template.md`

  The content pair is the one shape in this list that follows **no external format**. Every other
  upstream-doc template either carries our own shape by default or, in `design_template.md`'s case,
  tracks a vendor's; nothing publishes a schema for a content standard, so `content_template.md`'s
  sections are ours and there is no `spec --rules` to re-read them against.

Product what-left file (`core/templates/product-templates/`, model-read — authored from, never
stamped):
- `product-templates/what_left_template.md` — the shape of `<product>/docs/what_left.md`. The rules
  for the file, including who adds an entry and who removes one, are § 3 Product's *The what-left
  file — the one place a product states what is still to build*.

Product skeleton trees (`core/templates/skeleton-templates/`) — **script-facing**, copied wholesale
(never read by a model) by `core/launchers/product-skeleton/launcher.sh`, matching
`core/templates/README.md`'s consumer split: `__PROJECT__` is the one substitution token, and each
tree's own `README.md` documents it for a reader of this repo and is excluded from the copy. One
folder per language a project card's `Languages:` may declare — the six language answers this
manifest owes are `javascript/`, `python/`, `rust/`, `swift/` and `typescript/`, each a real tree, and
`shell/`, which holds **only its own `README.md`** — a declared absence, not an unwritten tree, and
the launcher skips it (reporting the skip) rather than copying it or refusing the run over it.

User-global memory (§5) — **no stamper reads these** (verified 2026-08-04: no reference to either name
outside this manifest and the template files themselves). Recorded, not fixed — "nothing stamps it" is a
different gap from "the stamper is unnamed", and it is not `spawn_satellite.py`'s to close:
- `core/templates/user_profile_template.md` · `my_profile_template.md`

Kaizen / other:
- `core/templates/fix_packet_template.md` · `owner_answers_template.md` · `docker_sandbox_template.md`
- `core/templates/self_answer_report_template.md` — `[create]` — the shape
  `skills/companion/.claude/skills/companion-self-answer/SKILL.md` § Step 5 stamps into `<stem>_self_answer_<N>.md`
  beside the companion a self-answer run answered. Flat rather than in a scope folder, the shape the
  kaizen pair above also takes. **Its `## ` headings are a parser's contract**:
  `core/tools/reporters.py`'s `companion-self-answer` reporter composes the run's completion
  notification from this file — five required headings it checks the shape by, `## Launchers owed`
  read by its heading, and the `**Verdict:**` field read anywhere. Which one fails which way is the
  template's own note at its head, and it is the file to edit — a heading changed here without it is
  a notification that quietly stops saying what the run did.
- `core/templates/brief_template.md` — `[create]` — the common part of a brief, the checked input a
  skill takes in place of a loose idea: the quote rules, the `none` rule, and the five sections every
  brief carries. Read by a model, never alone: each skill that takes a brief has its own template,
  which names this one and adds its own sections — `seeds-from-idea`'s and `ad-hoc-plan`'s
  `templates/brief.md`. It also holds the rules a session drafts a brief by. Flat: it belongs to no one scope.

### Doctrine layer — the vendored foundation store under `core/doctrine/`

`[create]` — what every loader, skill and hook resolves `<CORE>/doctrine/…` against. Create if
missing, never overwritten. Enumerated **per subfolder**: a per-file list goes stale faster than
the drift it would catch, and Audit diffs a subfolder as readily as a file.

- `core/doctrine/README.md` — the index, by subfolder. `task_map.md`'s sibling: the same set indexed
  by **subfolder** instead of by **task**.
- `core/doctrine/task_map.md` — the task → doctrine route, naming each doctrine by bare filename.
- `core/doctrine/sandbox.md` — the autonomous-run surface, and the launcher that may enter it.
- `core/doctrine/governance/` — how the instance governs itself: commit format, single source,
  model assignment, AI responsibility, doctrine structure, versioning, system anatomy,
  written-forward, where taste appears.
- `core/doctrine/flow/` — the change pipeline: its stages, change classification, folder-state
  handoff, and the step outcome contract each stage returns.
- `core/doctrine/engineering/` — how code is built and proven: architecture defaults, the testing
  layer model and its Python implementation, skill evidence, and the `languages/` practice family.
- `core/doctrine/setup/` — how an instance, a project and a role come to exist: this manifest, setup
  scope, authoring layers, adding a role, setting up an instance, setting up a project, shared-core
  instances.
- `core/doctrine/kaizen/` — the hardening loop: its skills, its lens set, the fix packet, ratification.

`core/docs/michi_agari.md` — the journey model (道 Michi, 上がり Agari, and the three journey parts)
— ships beside this layer and is audited with it. `core/docs/journey_move.md`, the mechanic every
skill that moves a journey item reads, sits beside it; those two are the only files under `core/docs/`.

> **See also — walking the journey.** This manifest declares *where* a journey's parts live and which
> skill moves each. The loop itself — the order of the moves, who owns each, and what a move may not do
> — is `michi_agari.md` § *How we work — walking a project's journey* and § *Who owns each step — and
> where the seeds come from*. `task_map.md`'s four journey rows route here and this pointer is the
> second hop, because the map indexes doctrine by filename and the loop's owner is a `core/docs/`
> guide. The seat's own statement of its moves is `<CORE>/roles/loaders/pm_global.md`
> § *Responsibilities*.

**Drift-checks:** doctrine is prose, **not** in the `<CORE>`-substitution set (§ Root, the closed
set) — a literal `core/…` in a doctrine file is not a defect. The harmless principle holds: no
host-global `~/.claude/…` path. Audit enumerates these paths.

### Instance-shared doctrine — `[create]`

Distinct from the layer above: this is the **instance's own** doctrine under `system/doctrine/`,
stamped from templates and layered over core's. Three files, not the vendored store.

- `system/doctrine/kensaiapp_doctrine.md` — the instance's general domain doctrine. **Fixed neutral name** (no project inference); stamped from `templates/kensaiapp_doctrine_template.md`. *(Per-project domain doctrine is separate — `system/projects/<name>/doctrine/<project>_doctrine.md`, §2.)*
- `system/doctrine/ai_responsibility.md` — stamped **verbatim** from `templates/ai_responsibility_template.md`.
- `system/doctrine/doctrine_structure.md` — stamped **verbatim** from `templates/doctrine_structure_template.md`.

**Stamped is where they start, not where they stay.** All three are **authored at step 2a of
`setting_up_an_instance.md`**, one CTO lens each, and until that step runs an instance holds three
shapes rather than three rules. Both consumer satellites ran the whole layer by hand on 2026-08-19
because no step owned it; `[create]` is what makes the authoring safe — created if missing, never
overwritten, so a re-stamp cannot undo it.

**An honest emptiness is a finished state**, and it is not the same as an unrun step: an instance whose
subject the layer below already governs says so in the file and stops. The instance that holds the
shared core is the standing case, and records it in its own `kensaiapp.md`.

An instance's own **writing bar** is `system/doctrine/writing_bar.md` — **authored rather than stamped**,
which is why it is not in the three above. Every instance holds one: core states no bar to fall back
on, so an instance without this file has nothing binding how its documents read. Writing it is step 3
of `setting_up_an_instance.md`.

**A project does not hold its own writing bar**, and there is no per-project tenant of this file — a
writing bar sits at the instance altitude and nowhere else. It is the bar kensaiapp's own documents
hold, and a product's definition documents are kensaiapp's. The words a product shows its **users**
are a different object with a different owner: `<product>/docs/CONTENT.md` (§3).

An instance may also hold **topic doctrine** — `system/doctrine/<topic>_doctrine.md` — `[user]`. One
file per instance-wide topic that several or all of its projects read, where folding it into
`kensaiapp_doctrine.md` would bury a subject projects cite on its own. It is authored rather than
stamped, so no stamper creates or touches it, and an instance with none is complete. It adds what no
other file owns: it does not restate a stamped file, the writing bar or a core rule
(`<CORE>/doctrine/governance/single_source.md`). The instance's `doctrine_structure.md` lists each one
by name, because that file owns the names and this section owns which kinds may exist.

### App-level — the solar system that drives the agari(s)

The instance carries three things of its own at app level — a **bearing** (`michi.md`), a
**seedbed** (`nemawashi/`) and a **router station** (`shukuba/`). All three sit **directly under
`system/`** (siblings). Once there is upkeep to hold, handed over by a project, asked for by the
owner, or owed by an exception a run records that lapses on a date, a fourth file sits beside them: the **upkeep register** (`upkeep.md`), which is not a journey
item. There is **no `system/queues/`
folder** in the canonical instance:

- `system/michi.md` — 道 Michi, the instance's **Way(s)** (MANDATORY) — `[create]`, stamped from
  `templates/michi_template.md`. A *declaration*, not a queue (a Way is declared once, never retired).
  Mirrors one level down as the per-project `agari.md` (§2).
- `system/nemawashi/` — 根回し Nemawashi, the instance's **seedbed** — a **folder** (one file per seed, so
  a closed seed is moved whole; never struck through in a shared queue):
  - `system/nemawashi/README.md` — the seedbed's doctrine + lifecycle — `[create]`, stamped from
    `templates/nemawashi_template.md`.
  - `system/nemawashi/<date>_instance-setup.md` — the **setup seed**: the steps that follow the
    stamp (the writing bar, then the ordered experience pair) as a station checklist, projected from
    `setting_up_an_instance.md` § The steps, in order and not restated here — `[create]`, stamped by
    `spawn_satellite.py` from `templates/instance_setup_seed_template.md`. The one idea setup
    authors, so a new instance's seedbed is never empty. A **recommendation** — the owner may edit or
    delete it, so its absence in an existing instance is not a gap. Its items are walked by running
    the skill and ticking the item; **no station is opened**, unlike a project's setup seed (§2).
  - `system/nemawashi/<seed>.md` — any other seed (`<seed>` = `<YYYY-MM-DD>_<slug>`) — `[user]`.
  - `system/nemawashi/unpicked/` — the candidate pool, holding any number at any time — `[create]` (directory stub).
  - `system/nemawashi/trail/` — seeds that **ripened into work** moved here — `[create]` (directory stub).
  - `system/nemawashi/drop/` — seeds that were **killed** moved here (ruled out, superseded, or abandoned before they were ever picked) — `[create]` (directory stub). Two bins rather than one, because a killed seed filed with the walked ones claims a walk that never happened, and the commit body that says otherwise is not where a reader looks. **A seedbed stamped before this row existed does not gain the bin from a re-run** — `_write_if_missing` leaves what is there and creates only what is absent — so it is satisfied lazily by the `mkdir -p` in `<CORE>/docs/journey_move.md` § Ensure the destination exists, on the first drop.
  Sibling to `michi.md`. Nemawashi exists at both levels; each project has its own in `journey/` (§2).
  Like a project's, this seedbed has a **pick** — an occupied root holds the active idea alone, an
  empty root means none is active, and the candidate pool sits in `unpicked/` — made and undone by
  hand here, since the pick skills are project-level (§ Native `.claude/` layer).
- `system/shukuba/` — 宿場 Shukuba, the instance's **router station** — a **folder** (one file per
  station, so a finished station is moved whole):
  - `system/shukuba/README.md` — the router's doctrine + lifecycle — `[create]`, stamped from
    `templates/system_shukuba_template.md`.
  - `system/shukuba/<station>.md` — the one active router station (`<station>` = `<YYYY-MM-DD>_<slug>`)
    — `[user]`. Names the shared cross-project thing, its **cross-project reached-when**, and a
    `currently active: <project>` pointer the Principal PM maintains by hand.
  - `system/shukuba/trail/` — finished router stations moved here by hand — `[create]` (directory stub).
  Sibling to `michi.md`. Shukuba exists at both levels **as two different kinds**: a project *walks*
  its own in `journey/` (§2) — opened from a Nemawashi checklist item, crossed by 飛び石 Tobiishi — while
  this one only *coordinates* across projects and is never walked. There is no `parked/` here: a router
  station has one destination, `trail/`.
- `system/upkeep.md` — the instance's **upkeep register** — `[user]`, written the first time a project
  hands over upkeep, the owner asks for a standing task, or a run records an exception that lapses on
  a date (the security skill's advisory exceptions). It holds the recurring work that outlives a
  project's Agari: re-checks on a cadence, and corrections due when the world changes. Each task gets one
  row naming the rule it serves, its cadence, when it was last done, when it is next due, and what
  reminds the owner. None of the three above can hold this work. The Michi is a declaration, a seed is
  walked once, and a router station coordinates projects. A project that kept the work in its own
  journey would never reach its Agari. The rule a task serves stays in its own file, and the register
  says only what to do and when. A task that ends is removed, and the commit says why.

- `system/tests/` — the instance's **own checks over its own tree** — `[user]`. A test belongs here,
  not beside the tool it exercises, when what it checks is true of this instance only: its journey
  records, its project set, the allowlists tuned to them, its own `system/` files. `core/` ships to
  every instance and a release, where those records are absent, so a check of them under `core/`
  fails there for a reason that is no defect of the tool. The test of the tool stays beside it, on
  inputs it builds itself; the check of this instance's tree is here, importing the tool by the
  `conftest.py` beside it. A file here is named `test_instance_<subject>.py`: pytest imports a test
  module by its bare name, so one sharing a name with a tool's suite breaks collection of both. Run
  as the suite map's `system-readers` suite.

**Not at app level:** 飛び石 Tobiishi · 上がり Agari — both project-level (§2). Nothing reaches the Michi,
so the instance has no terminus and no change-pipeline of its own.

---

## 2. Per-project — `system/projects/<name>/`

One folder per **managed engagement**. `project-stamp` scaffolds the skeleton (`project.md` +
the `agari.md` and `journey/` placeholders — the pipeline front door is the `journey/tobiishi/`
folder, holding the active Tobiishi `journey/tobiishi/<key>/`); the change-work content is authored
by the pipeline, never by setup. The one exception is the **setup seed** in the seedbed below —
the definition chain a project starts with, stamped rather than hand-written.

- `system/projects/<name>/project.md` — the project's card — `[create]` (drift-checked for `Product path:`
  presence). Its load-bearing field is the **`Product path:` binding**; template
  `templates/project_template.md`.
- `system/projects/<name>/doctrine/` — the project's own doctrine — `[create]`:
  - `system/projects/<name>/doctrine/<project>_doctrine.md` — the project's **domain doctrine**, stamped
    from `templates/project_doctrine_template.md`.
  - `system/projects/<name>/doctrine/ai_responsibility.md` — the project's **AI-responsibility doctrine**,
    stamped from `templates/ai_responsibility_template.md`.
  *(Project-level **doctrine** home is `doctrine/`. The product's own docs are `<product>/docs/`,
  reached through `project.md`'s Product path — a different thing from the project's own
  `docs/` below, which holds working records rather than doctrine or product documents.)*
- `system/projects/<name>/docs/` — the project's **working records** — `[create]` on demand, not
  stamped: a run record, an audit, a design package — what a session produced *about* the project's
  own work, which is neither doctrine (`doctrine/`, above) nor a product document
  (`<product>/docs/`, reached through `project.md`). Six projects carry one today. Absent until a
  project has something to keep; never created empty. `docs/nemawashi-refine/<seed>_report.md` is the
  Principal PM's answer to a retired seed, written by `nemawashi-refine` — here and not in the seed,
  because the seed is in `trail/` by then.
  `docs/seeds-from-idea/<YYYY-MM-DD>_<slug>_brief.md` is an idea cut's input, in the shape of
  `seeds-from-idea`'s `templates/brief.md`, which extends `<CORE>/templates/brief_template.md`. It is
  committed with the seeds it produced — the owner's call, 2026-10-24, so every cut keeps its input
  on record. Its `_report.md` sits beside it, in that skill's
  `templates/report.md` shape: what the cut did with each line of the ask, read by `nemawashi-refine`
  when the cut ran inside it.
- `system/projects/<name>/contexts/CONTEXT_PM.md` — the project's **per-project PM context** — `[create]`,
  stamped from `templates/context_template.md`. Holds **one item**: this project's current change from the
  PM's view (scope / FDR-fit / product-fit) — PM memory, **not** a journey mirror. Sits below the two PM
  loader layers as a project-scoped read; kept fresh by the change lifecycle (`tobiishi-open` overwrites,
  `tobiishi-seal` marks it done), never hand-edited. The **only** per-role context setup stamps (§1 *Role layer*) — the
  other thirteen roles are stamped with none.
- `system/projects/<name>/agari.md` — the project's **上がり Agari declaration** (MANDATORY — the
  product's "done", set by CPO) — `[create]`, stamped from `templates/project-templates/agari_template.md`. A *declaration*,
  not a queue — it mirrors the instance's `system/michi.md` one level down (§1). **No Michi** at project
  level (a project serves the instance's Way). Setup stamps the placeholder; `project-agari` fills it at
  station 2 of the setup seed, off the back of the settled PRD.
- `system/projects/<name>/agari_open_issues.md` — the Agari's **companion**, holding what the
  `project-agari` round could not settle for the owner to answer inline — `[user]` (written by the skill,
  never by setup), from `templates/project-templates/agari_open_issues_template.md`. **Transient**: the
  closing round removes it, and its **absence is the done signal** for the Agari.
- `system/projects/<name>/trail/agari/cycle-<N>.md` — each answered companion, retired whole before its
  answers are folded in — `[user]`, written by `project-agari`. Permanent: it is where the owner's
  decisions and their reasoning stay citable once the companion is rewritten or removed.
- `system/projects/<name>/journey/` — the project's **journey**: the work in motion toward the Agari.
  It runs **根回し Nemawashi (seedbed) → 宿場 Shukuba (current station) → 飛び石 Tobiishi (change units)**
  — each a **folder** with one active item and a `trail/` of finished ones (same lifecycle throughout;
  park-don't-strike). The active idea's **dynamic checklist** names its stations — there is no separate
  plan folder.
  - `journey/nemawashi/` — the **根回し Nemawashi** seedbed (a folder; the ideas that carry the product
    toward its Agari — one **active** idea carrying a dynamic checklist of its stations, plus
    **candidates**, held in `unpicked/` at any time whether or not one is active. A pick lifts one
    candidate out of `unpicked/` to the root, alone; no other candidate moves):
    - `journey/nemawashi/README.md` — the seedbed's doctrine + lifecycle — `[create]`, stamped from
      `templates/journey_nemawashi_template.md`.
    - `journey/nemawashi/<date>_define-the-product.md` — the **setup seed**: the recommended definition
      sequence as a station checklist, projected from `setting_up_a_project.md` § The flow at a
      glance and not restated here — `[create]`, stamped by `project-stamp` from
      `templates/project-templates/setup_seed_template.md`. The one idea setup authors, so a new
      project's seedbed is never empty. A **recommendation** — the owner may edit or delete it, so
      its absence in an existing project is not a gap.
    - `journey/nemawashi/<idea>.md` — any other idea (`<idea>` = `<YYYY-MM-DD>_<slug>`) — `[user]`
      (authored as ideas arise, never by setup).
    - `journey/nemawashi/<idea>/` — the same idea, once a `shukuba-refine` run has written into it —
      `[user]`, moved whole: `seed.md` is the idea itself (the one file ever read as the seed), plus,
      per reviewed unit — a sealed or halted 飛び石 Tobiishi, or an ad-hoc merge — `<unit-key>_report.md` and
      `<unit-key>_recommendations.md`.
      Lazy — nothing converts a `<idea>.md` seed into this shape until the first report lands.
    - `journey/nemawashi/unpicked/` — the candidate pool, holding any number at any time — `[create]`
      (directory stub).
    - `journey/nemawashi/trail/` — finished ideas moved here — `[create]` (directory stub).
    - `journey/nemawashi/drop/` — ideas that were **killed** moved here — `[create]` (directory
      stub). Same reason `parked/` exists one folder over: a record has to say which thing
      happened, and an idea ruled out was not walked to the end.
  - `journey/shukuba/` — the **宿場 Shukuba** current station (a folder; exactly **one** active station
    in full — what it is, its reached-when, its guardrail):
    - `journey/shukuba/README.md` — the station's doctrine + lifecycle — `[create]`, stamped from
      `templates/journey_shukuba_template.md`.
    - `journey/shukuba/<station>.md` — the active station (`<station>` = `<YYYY-MM-DD>_<slug>`) — `[user]`.
    - `journey/shukuba/parked/` — stations set down **unreached**, waiting to be taken up again —
      `[create]` (directory stub). It exists because an unreached station in `trail/` would make that
      record claim a walk that never happened, so a set-down needs somewhere else to go. Nothing ever
      empties it: a parked station waits until someone opens it again.
    - `journey/shukuba/trail/` — reached stations moved here — `[create]` (directory stub).
  - `journey/tobiishi/` — the **飛び石 Tobiishi** change-unit area (a **folder**, not a file):
    - `journey/tobiishi/<key>/` — the active Tobiishi (`<key>` = `<YYYY-MM-DD>_<slug>`) — `[user]`
      (pipeline-authored, never created by setup). Holds the change arc, in order:
      `change_request.md` → `change_spec.md` → `change_design.md` → `tl_instruction.md` →
      `change_text.md` → `flow_findings/` → code → `code-integrity-report.md` → `security-report.md`.
      A change planned by `ad-hoc-plan` from a brief also holds `ad_hoc_plan_brief.md`, its input,
      beside `change_request.md`, and an `ad-hoc-plan` run leaves `ad_hoc_plan_report.md` there,
      save the three stops its `SKILL.md` § *The run's report* names.
    - `journey/tobiishi/trail/` — crossed stones: sealed Tobiishi moved here on seal — `[create]`
      (directory stub).
    - `journey/tobiishi/drop/` — Tobiishi dropped **unsealed** by `tobiishi-drop`, whole and unedited.
      The folder is created on the first drop and is not stamped by setup. Its branches are kept
      unmerged, so a dropped unit's work is never lost and never reaches `main`.
  **Agari is *not* here** — it lives in `agari.md` above (a declaration, not a moving part).

**The binding field in `project.md`:**

```markdown
**Product path:** products/<product>                    # relative → internal product (instance-root-relative, no leading ../)
**Product path:** /Users/you/projects/trading-system   # absolute → external product (recommended)
```

`development-specs` / `development-design` / `development-plan` resolve `fdr.md` / `adr/` / `nfdr.md` under the
product's `docs/`, located through `<CORE>/tools/development_path.py`'s contract (`product_worktree` plus the
`Product path:` below its repo), not by hand. A **relative** `Product path:` is **instance-root-relative — no leading
`../`**: it is resolved against the worktree root (a *nested* checkout, `<repo>/.worktrees/<key>`), so
a leading `../` escapes the worktree and breaks resolution. Place an in-repo product under
`products/<name>`. An **external** product uses an **absolute** path (a leading `~/` counts, expanded to
the home directory) to its own git repo — never worktree-prepended. An absolute path that lands inside the
instance's own repo is **not** external: the tool reads it as one repo, like a relative one.


### When a project stops — it moves to the galaxy archive

§ 2 above describes a project's whole life except its end. A project stops in one of two ways, and
only one of them was ever named: it **settles**, having reached its Agari, or it is **taken out of
service** — finished, superseded, or simply stopped. Every real case in this galaxy has been the
second.

**Either way the folder moves whole to the galaxy archive**, which is the producer satellite's
`system/archive/projects/<instance>/<name>/` (the host's `system/satellites.md` § Producers names it).
The producer is the side that remembers — its `kensaiapp.md`
states that the producing side forgets each kaizen round while judging has to remember them all, and a
stopped project is that same forgetting one level up. **No instance keeps an archive of its own.**

**Namespaced by source instance, because names collide across the galaxy** — `product-definition`
exists in two instances today, and it is not the first name to have.

**The move is by hand, in one commit each side, and nothing inside the folder is edited.** The card,
Agari, doctrine and journey read exactly as they did on the day it was set down, because a project's
reasoning stops being evidence once it has been tidied. Park-don't-strike, applied to a whole project.

**Every entry carries an `ORIGIN.md`, and that is not decoration.** A move between instances is not a
`git mv` — it is a removal in one repo and an addition in another, so **the commits do not travel**.
The origin record names the source instance, the path it held there, and the SHA it was taken at, so
the history stays reachable. Without it the folder arrives with its reasoning cut in half.

**What does not move:** the product repo, which the archived card still points at; and records
elsewhere naming the project, which stay as written because they record what was true then. **What
must move with it:** every *live* statement that names the project as in service.

**One thing this does not answer, deliberately.** A project so entangled that live doctrine derives a
rule from it may cost more to move than the archive is worth — the host's own `scripts` was kept in
place for exactly that reason, with a banner in its card, and its ten inbound references are why. That
is the owner's call per project, not a rule.

---

## 3. Product — pointed to by `project.md`, inside or outside the instance

The **durable deliverable**: decision records + code. Travels as a unit — which is exactly why an
external product is clean. **Mapped 1:1 to a project.**

- `<product>/docs/fdr.md`, `<product>/docs/adr/`, `<product>/docs/nfdr.md` — decision records — `[user]`.
  They **stay with the product**; **never created by the stamper.**
- `<product>/docs/trail/<doc>/` — the **answer-trail** of the document `<doc>` names — `[user]`, written
  by the producing skill, never by the stamper. Permanent. The rule that puts it there is below.
- `<product>/docs/what_left.md` — the **what-left file**, listing what the product's Agari and PRD
  want that its code does not do — `[user]`, never created by the stamper. Its shape and the rules
  for changing it are below.
- `<product>/…` — the product's own code + tests — `[user]`.

The stamper does **not** create product folders or decision records (user- / pipeline-authored).
`project-stamp` formalizes the project→product map via `Product path:`; a `project.md` lacking
`Product path:` is drift.

### A trail is not the document's sibling — it is filed under `trail/`

**A document's answer-trail lives at `<the document's own directory>/trail/<document-slug>/`.** It is
never a `<doc>_trail/` sibling of the document. This holds at every layer, so §1's instance documents
and §2's `agari.md` name their own paths against this rule and do not restate it.

| the document | its trail |
|---|---|
| `<product>/docs/{PRD,SRS,UXD,SDD,DESIGN,CONTENT}.md` and `<product>/docs/fdr.md` | `<product>/docs/trail/{prd,srs,uxd,sdd,design,content,fdr}/` |
| `system/doctrine/writing_bar.md` | `system/doctrine/trail/writing_bar/` |
| `system/experience/visual_direction.md` + `visual_restrictions.md` | `system/experience/trail/visual/` |
| `system/experience/voice_direction.md` + `voice_restrictions.md` | `system/experience/trail/voice/` |
| `system/projects/<name>/agari.md` | `system/projects/<name>/trail/agari/` |

**The slug is lower-case and names the document, not its file's case.** Six of the seven product
documents are upper-case on disk and the FDR alone is lower
(`core/launchers/companion-self-answer/launcher.sh`, "six of the seven documents are upper-case on disk
and the FDR alone is lower"), so a slug read off the case would be two conventions. Where one trail
serves a **pair** — the two experience halves — the slug names the half.

**What goes in it** is everything recording how that document reached its current state:
`cycle-<N>.md`, each answered companion retired whole by the producing skill; `self_answer-<N>.md`,
each `companion-self-answer` run's own report; and, in `trail/sdd/` only, `run-<N>.md`, the record of
one retired three-seat `product-sdd` conversation, beside `run-<N>.state.json`, that run's own
working file — not a record of what happened. Both are frozen, and the paragraph below says who still
reads them. The folder is the **document's** record rather than
one skill's, which is what lets more than one skill write into it without any of them owning it.
Their filename patterns do not collide, and a reader of `trail/<doc>/` sees the document's whole
history in one listing.

**A trail holds a record while it is still being written, not only once it closes** — the owner
reaffirmed on 2026-09-02 that the SDD's conversation record moves under `trail/`; that it lands
*here*, in the SDD's own trail rather than in a `trail/sdd_conversation/` sibling, was the call of
the PM run that walked it the same day (`03fe1879`). Which folder a file belongs in turns on **what
it records**, never on whether the recording has finished. The SDD's `run-<N>.md` was the case that
made the distinction worth stating, and the only one of the three patterns above whose recording was
still open while it sat here: the retired runner appended it after every round of a live run and read
it back at the next invocation to resume one, so it was the run's own state rather than a report
about it. That was a real difference from every other file here, and it was not a reason to keep the
record out — the membership test is the subject matter, and the record's subject is the SDD.
(`trail/sdd/` also took delivery of a file mid-run: the runner copied the answered companion to
`cycle-<N>.md` before any seat touched it. That file was finished when it landed, so it settled
*when* the folder was written to and not whether a still-open record may sit in it.) **What a live
record does oblige is its reader:** a folder holding several numbered patterns cannot be read by "the
highest-numbered file", so anything looking for it matches `run-<N>.md` by name —
`core/tools/reporters.py`'s `_sdd_record_text` filters on the `run-` prefix for exactly this reason.

**The archived run record is a frozen format, and this paragraph is its one in-tree statement.** The
three-seat conversation that wrote `trail/sdd/run-<N>.md` and `run-<N>.state.json` was retired after
commit `c87cd04af`; nothing writes either file now, and the records already on disk are read, never
edited. Two readers remain. `core/tools/chain_usage.py` reads both files and the background sessions
named after them. `core/tools/reporters.py`'s `read_sdd` reads the latest `run-<N>.md`. Two shapes of
the record are what `chain_usage.py` depends on:

- the seat block of the record's head, opened by the line `Seats, and the names they answer to:`, with
  one two-space-indented line per seat in the form `  - CTO — `<session-name>``, and likewise `CPO`
  and `CDO`;
- the default session name each seat answered to, `sdd-<project>-run<N>-<cpo|cto|cdo>`, which
  `chain_usage.py` consults only as its named fallback when a record states no name.

A reader cites this paragraph for either shape; no other file states them.

**Why not a sibling per document.** A directory holding seven documents then holds seven trails, and
the documents a person opens are outnumbered by the record of how they got there — measured on a
live product at 20 entries in `docs/`, of which 9 are trails and 11 are documents. One `trail/` costs
that listing one entry instead of seven.

**Why not a dot-folder inside `docs/`**, the other candidate the owner named. A leading dot means
*machinery* in this repo — `.claude/`, `.worktrees/`, `.git/` — and the answer-trail is content: it is
the authorization record a ratification cites (`core/doctrine/engineering/skill_evidence.md`, "each
retired answer `trail/prd/cycle-N.md`"). Hiding an audit record from `ls`, from a shell `*` glob, and
from a file tree is the opposite of what the record is for. `trail/` uncrowds the listing without
concealing anything.

**Why not a sibling of `docs/`**, the owner's other candidate. `docs/` is the one directory a product
repo gives this system; a second top-level entry spends the product's own root namespace on our
record-keeping, and the product's root is its stack's. It also does not generalise — the instance
documents in §1 have no `docs/` to sit beside, so that shape would need a second rule for them.

### The what-left file — the one place a product states what is still to build

**A product's what-left file lists what the product's Agari and PRD want that its code does not
do.** It lives at `<product>/docs/what_left.md`, and a reader tests for it with
`test -f <product>/docs/what_left.md`. The Agari is the one at `system/projects/<name>/agari.md`, for
the project mapped to the product, and the PRD is `<product>/docs/PRD.md`. The what-left file is the
one place a product's "what is left to build" is stated. Any other file that needs a product's build
state points at it rather than restating it. `core/doctrine/governance/written_forward.md` § 2, *A
file does not carry a build-state claim*, names the what-left file as an exception to that rule.

**Its shape is `core/templates/product-templates/what_left_template.md`.** The file holds an H1
heading and one lead sentence, then either entries or the empty marker. The heading and the lead
sentence are neither an entry nor the marker, so they never change which reading below applies.

**An entry is one wanted thing, written as a list item with three labelled fields.** Its first line
begins `- **Wanted:** `, and the other two fields follow it on two indented lines.

- `**Wanted:**` — one thing the product does, or one thing that is true of it, for its user or
  reader. It is written as a want, never as a step, a task or an order of work. "Add a `Task`
  dataclass to `domain/`" is a step and is not an entry. "The operator adds tasks to a project" is a
  want.
- `**Source:**` — the document that wants it and the section that says so: `Agari` or `PRD`, then
  ` § ` and the section heading, adding the bolded item name where the section has named items, as
  in `PRD § Core Features, **Projects**`.
- `**Missing at:**` — one short commit SHA in an inline code span. It names a commit that `main`
  carries, at which the product's code does not do the wanted thing. It is set when the entry is
  added and is never rewritten.

**An entry holds only a want that the code can be shown to miss.** The product's Agari or PRD wants
the thing, and at the entry's `Missing at` commit, `git grep` over the product or running its code
shows that the code does not do it. A want that only the owner's judgement can pass or fail is not
such a thing, and it gets no entry. An entry names no station, seed, change unit or `journey/` path.
The file is not a plan and not a task list, and it carries no step and no order of work.

**An entry is added only by whoever changes the product's Agari or PRD.** This rule governs adding
to a what-left file that exists. It does not govern writing a product's first one.

**The CPO writes a product's first what-left file, with `skills/cpo/.claude/skills/first-what-left/`,
once the project's Agari is settled** (`agari.md` present, no `agari_open_issues.md`). The run writes
only where no file exists, and that skill's `SKILL.md` owns the rest.

**A Content Editor run removes an entry, and only once the entry's wanted thing has merged.** The
commit that removes the entry names the commit that merged its thing, in a body line of its message,
one line per removed entry:
`Merged in <commit>: <the entry's Wanted text, verbatim>`. A later reader finds that commit for any
removed entry with `git log -p -- <product>/docs/what_left.md`.
The Content Editor run that removes an entry is `readme-status`. After each station close, a
product's what-left file shrinks at the `build-idea` queue's `readme-status` row. `shukuba-refine`
writes one `readme-status` row after each `close the reached station` row in its report's
`## Next moves` table, for a product that has both a what-left file and a README with one `## Status`
line; for one lacking either it writes none, since the run would refuse it. The queue starts that row only once the close it follows has landed.

**Reducing the file belongs to that run alone, and reducing is all that run does to the file.** It
never adds an entry and never rewords one. No one else removes an entry, whether or not its thing
has merged.

**A reader reads the product's state from what sits at `<product>/docs/what_left.md`.** The empty
marker is the line `Nothing is left to build.`, exactly, alone on its line.

| On disk at `<product>/docs/what_left.md` | Reads as |
|---|---|
| no file | **never given**. The product was never given a what-left file, and that says nothing about what the product lacks. |
| the file, holding one or more entries and no empty marker | **still to build**. The entries are what is left. |
| the file, holding the empty marker and no entry | **done**. Nothing the Agari or PRD wants is left to build. |
| the file, holding neither an entry nor the empty marker | **malformed**. It reads as neither done nor never given. |
| the file, holding the empty marker and one or more entries | **malformed**. It reads as neither done nor never given. |

A file with no entry and no marker reads as malformed rather than done, because malformed is the
reading that never claims a product is finished.

**The run that removes a product's last entry leaves the file in place, holding the empty marker.**
It never deletes the file. A deleted file reads as never given, which would turn a finished product
into one that was never given the file.

---

## 4. Conditional — Docker sandbox

Required when the project uses sandboxed autonomous runs. All `[hybrid]`, stamped from
`templates/docker_sandbox_template.md` (substitute `<project>` / `<image-name>` / `<network-name>`).
Detection: `system/sandbox/` directory exists, or `scripts/sandbox-launch.sh` exists.

- `system/sandbox/Dockerfile`
- `system/sandbox/run.sh`
- `system/sandbox/DOCTRINE.md`
- `scripts/sandbox-launch.sh`

---

## 5. User-global (not in the instance tree)

Stored under `~/.claude/`, checked per-project. All `[create]`:
- `~/.claude/projects/<project-slug>/memory/MEMORY.md` — index stub.
- `~/.claude/projects/<project-slug>/memory/user_profile.md` — stamped from `templates/user_profile_template.md`.
- `~/.claude/projects/<project-slug>/memory/my_profile.md` — stamped from `templates/my_profile_template.md`.

> **Privacy guard.** `user_profile.md` / `my_profile.md` are stamped **verbatim** from their neutral
> templates — placeholder bodies only. A stamper must **never** transcribe the host machine's
> actual profile (`~/.claude/rules_parked/{user,my}_profile.md`) or personal session-context details into a
> fresh instance's memory (privacy leak). A new instance starts with empty profiles.

Project slug derivation: absolute project path with `/` replaced by `-`
(e.g., `/Users/you/projects/foo` → `-Users-you-projects-foo`).

Global loaders (`<CORE>/roles/loaders/<role>_global.md` — **sixteen** on disk, one per role with a
posture body, `qa` and `teacher` included) are shared across all projects — checked once, not
per-project.

### Machine state — never `[create]`

Nothing in the per-project rules above reaches these: no stamper creates one, no audit enumerates them,
and stamping a new instance must never install one. They exist **once per machine** and serve every
instance on it.

- `~/Library/LaunchAgents/<label>.plist` — what starts a program the machine runs on the system's
  behalf. The plist, not the program, is what makes that program a singleton: it names the one port and
  the one directory that the code — vendored under `core/tools/` — takes by argument.
- `~/.kensaiapp/telemetry/` — the raw run-telemetry stream. Unbounded, machine-specific, disposable:
  losing it costs a re-measurement, not a rebuild. **Not `~/.claude/telemetry/`**, which Claude Code
  already owns: it spools its own `1p_failed_events.*.json` there (five on this machine, dated from
  2026-08-18), and it sweeps `~/.claude` on its own retention schedule. A directory the vendor writes
  and rotates is a poor home for the only copy of a measurement.
- `~/.kensaiapp/pins/<id>/` — a pin: a copy of the host's `core/`, `.claude/` and `skills/` trees as
  they stood at the moment a launch made it, through `core/tools/pin.py`. Which pin a launch runs in
  is decided by the rules in `core/tools/pin_run.sh`. A run keeps the version it started on: a live
  edit to those trees made after the launch cannot reach it. A `build-idea` start that a run makes
  takes a new pin when the host has changed since the run's pin was made. Nothing deletes a pin; they
  accumulate until an owner clears them by hand. `KENSAIAPP_PINS_HOME` overrides the pins home for
  tests, so a suite never writes under the real path.
- `~/.claude/settings.json`, `env` key `CLAUDE_CODE_PLUGIN_DIRS` — the line that loads the kensaiapp
  side pane: it names the host's `<CORE>/tools/kensaiapp-panel` folder. With it, every Claude Code
  session on the machine loads the mod, and the pane opens only in a session whose project root is in an
  instance. One line serves every instance that binds this core, and no stamper writes it. Without it
  the mod simply does not load, and nothing else needs it.

**No tool may require machine state to exist.** A reader over an absent stream reports nothing; it does
not fail. And a stream being machine-local does not make what is *derived* from it machine-local — a
comparison drawn from one is a document, it is evidence, and it belongs in a repo.

---

## 6. Migration map

When the audit finds a file **missing at its canonical path but present at an old path**, the Fix phase uses `git mv` instead of creating a new file. After moving, the fix updates all path references in template-owned files from old → new.

| Old path | New canonical path |
|---|---|
| `.claude/skills/project-scaffold/` | `skills/interactive-product/.claude/skills/project-stamp/` |
| `.claude/skills/shukuba-park/` | `skills/pm/.claude/skills/shukuba-park/` |
| `.claude/skills/verify-before-claim/` | `skills/developer/.claude/skills/verify-before-claim/` |
| `.claude/skills/development-audit/` | `skills/kensaiapp-auditor/.claude/skills/development-audit/` |
| `.claude/skills/companion-self-answer/` | `skills/companion/.claude/skills/companion-self-answer/` |
| `system/doctrine/roles/loaders/<role>.md` | `system/loaders/<role>.md` |
| `system/doctrine/roles/CROSS_ROLE.md` | `system/CROSS_ROLE.md` |
| `system/loaders/<role>_<project>.md` | `system/loaders/<role>.md` (drop project slug) |
| `system/contracts/CROSS_ROLE.md` | `system/CROSS_ROLE.md` |
| `system/roles/loaders/<role>.md` | `system/loaders/<role>.md` |
| `system/roles/CROSS_ROLE.md` | `system/CROSS_ROLE.md` |
| `system/doctrine/writing_bar_trail/` | `system/doctrine/trail/writing_bar/` |
| `system/experience/visual_trail/` | `system/experience/trail/visual/` |
| `system/experience/voice_trail/` | `system/experience/trail/voice/` |
| `system/projects/<name>/agari_trail/` | `system/projects/<name>/trail/agari/` |

*(The instance-wide `CONTEXT_<ROLE>.md` relocation rows are **removed** — setup no longer stamps a
context there. Legacy contexts are handled report-only, below.)*

> **The `CLAUDE.md` split is report-only — NOT in the auto-move table above.** An older instance
> carries one root `CLAUDE.md` holding both its routing and its identity. It does not move to one
> path: its identity sections (title, what this is about, prime directives, and anything else true
> of that instance alone) are carried by hand into `kensaiapp.md`, `AGENTS.md` is stamped from the
> template, and `CLAUDE.md` is then replaced by the template's one-line import of `AGENTS.md`
> (§1 Root).

After moving the last file out, `system/doctrine/roles/`, `system/contracts/`, and `system/roles/` become empty and are removed by git automatically. (`system/doctrine/` itself remains — it holds the instance-shared doctrine files in §1.)

> **Legacy change-work relocation is report-only — NOT in the auto-move table above.** Nothing
> auto-moves legacy change-work folders (an old shared `system/requirements/<date>_<slug>/`,
> or a per-project `requirements/`) into the new per-project `journey/tobiishi/<key>/`. Repair **reports
> the potential-to-move and Product performs the move** (non-destructive). The canonical change unit is
> the Tobiishi folder `journey/tobiishi/<key>/` (§2); intake is the Tobiishi — there is **no `inbox.md`**.

> **Legacy single-file Shukuba → folder is report-only — NOT in the auto-move table above.** An older
> instance carries `journey/shukuba.md` as a single file. The canonical shape is now a **folder**
> (`journey/shukuba/` with `README.md` + `trail/`, §2). Setup does **not** auto-move the single file into
> the folder — its content is a filled station, not the folder's README doctrine, so a blind `git mv`
> would clobber. Repair **reports** the relocation; Product moves the content into the folder's active
> `<slug>.md` and lets setup create the `README.md` + `trail/`. **Legacy 方針 Hoshin is obsolete** — the
> hoshin layer was dropped in favor of the active idea's dynamic checklist; a legacy `journey/hoshin.md`
> or `journey/hoshin/` is reported for removal, not migrated.

> **Legacy instance-wide contexts are superseded — report-only, NOT auto-moved.** A context a
> `system/loaders/` overlay reads is the instance's own (§1 *Role layer*) and is **never legacy** —
> everything below is about the files no overlay reads. The stamped context shape is now **per-project
> PM only** (§1 / §2): a legacy non-PM `CONTEXT_<ROLE>.md` no overlay reads is **obsolete** (removed, not
> migrated — like legacy Hoshin above), and a legacy instance-wide `system/contexts/CONTEXT_PM.md` has
> **no project to auto-assign to**. So the instance-wide `CONTEXT_<ROLE>` relocation rows are gone from
> the auto-move table. Repair **reports** each such file (or older `.../roles/contexts/…`): Product
> removes the obsolete non-PM ones and places the PM one under the owning `system/projects/<name>/contexts/`.

> **A product's `<doc>_trail/` → `docs/trail/<doc>/` is report-only — NOT in the auto-move table
> above.** The four rows added there are instance files, which this skill owns. A product repo is not
> its to touch — §3, "The stamper does **not** create product folders" — so the seven product trails
> (`prd`, `srs`, `uxd`, `sdd`, `design`, `content`, `fdr`) are **reported** and Product performs the
> move. **The move is one `git mv` per trail that exists, and nothing else**, because the cycle files
> keep their names and no producing skill reads a path out of them:
>
> ```bash
> cd <product> && mkdir -p docs/trail
> for d in prd srs uxd sdd design content fdr; do
>   [ -d "docs/${d}_trail" ] && git mv "docs/${d}_trail" "docs/trail/$d"
> done
> ```
>
> Each `docs/<DOC>_self_answer_<N>.md` moves in the same pass to
> `docs/trail/<doc>/self_answer-<N>.md`, keeping its `<N>`.
>
> **Until a product is moved, its next run starts a second trail** — the producing skill numbers
> cycles by listing `docs/trail/<doc>/`, finds it absent, and writes `cycle-1.md` there while the old
> folder keeps cycles 1..N. That is a split record rather than a lost one, and the `git mv` above
> still repairs it, at the cost of renumbering by hand. Move a product before its next definition run
> rather than after.

> **A product's `docs/sdd_conversation/` → `docs/trail/sdd/` is report-only — NOT in the auto-move
> table above.** Same reason as the block above it: a product repo is not this skill's to touch, so
> the relocation is **reported** and Product performs it. The SDD's conversation record records how
> the SDD reached its current state, so it joins the SDD's own trail rather than taking a slug of its
> own — § 3, *A trail is not the document's sibling*, whose slug names a document.
>
> **The move is the record files, not the directory, and the renumber comes first.** A product that
> has run `product-sdd` already has a `docs/trail/sdd/`, and `git mv <dir> <existing-dir>` nests the
> source inside the destination rather than merging into it. Two states break a straight loop, and
> this block predicts both of them itself — each reproduced in a scratch repo, 2026-09-02:
>
> - **The destination already holds a `run-<N>.md`**, which is what a window run mints there
>   (below). `git mv` will not overwrite it: `fatal: destination exists`, exit 128. **Renumber by
>   hand before the loop, never after** — once the loop has half run, nothing on disk tells the two
>   numberings apart.
> - **The record is untracked**, because a run the retired runner interrupted mid-way left its
>   files on disk uncommitted. `git mv`
>   refuses that too: `fatal: not under version control`. Staging the folder first clears it.
>
> ```bash
> ls <product>/docs/trail/sdd/run-*.md          # an <N> that also arrives → renumber by hand first
> mkdir -p <product>/docs/trail/sdd
> git -C <product> add docs/sdd_conversation    # an interrupted run's record is untracked
> for f in <product>/docs/sdd_conversation/run-*.md; do
>   n=$(basename "$f")
>   git -C <product> mv "docs/sdd_conversation/$n" "docs/trail/sdd/$n" || break
> done
> rmdir <product>/docs/sdd_conversation         # refuses while anything is left — that is the signal
> ```
>
> `git -C <product>` rather than `cd <product> && git …`, which trips the harness's *changes
> directory before running git* guard (`commit_format.md` § *Never `cd` into a repo to run git*);
> and `|| break`, so the first refusal stops the loop instead of printing one `fatal:` per file and
> leaving a half-migrated tree behind two lines of stderr.
>
> Each `run-<N>.md` keeps its `<N>` unless the renumber above moved it, and `cycle-<N>.md` /
> `self_answer-<N>.md` are already in that folder without colliding with it.
>
> **No run is live to be disturbed.** The runner that read this record as its resume surface at the
> next invocation was retired after `c87cd04af` (§ 3), so the records are frozen and the move can
> happen at any time.
>
> **Until a product is moved, its record is not read.** `core/tools/reporters.py` and
> `core/tools/chain_usage.py` read `docs/trail/sdd/` and nowhere else, so a product still holding
> `docs/sdd_conversation/` has records neither of them sees. The recipe above repairs that.

### Reference-only path migrations

These are **paths that are referenced from inside template-owned files but never moved by this skill** — global ones under `~/.claude/`, outside the project tree, skills-layer files that moved into `<CORE>`, and prompts that moved out of `<CORE>/prompts/` into the one skill that reads them. The stale-reference sweep must rewrite them wherever they appear — including in CONTEXT files and in `CROSS_ROLE.md`'s own canonical-body pointer.

| Old referenced path | New canonical path |
|---|---|
| `~/.claude/loaders/<role>_global.md` | `<CORE>/roles/loaders/<role>_global.md` |
| `~/.claude/contracts/CROSS_ROLE.md` | `<CORE>/roles/CROSS_ROLE.md` |
| `~/.claude/rules/<name>.md` | `~/.claude/rules_parked/<name>.md` |
| `.claude/skills/_shared/commit-via-builder.md` | `<CORE>/doctrine/governance/commit_via_builder.md` |
| `.claude/skills/_shared/journey-move.md` | `<CORE>/docs/journey_move.md` |
| `.claude/skills/_shared/seed-cut-run.md` | `<CORE>/prompts/principal_pm_cut_seeds_run.md` |
| `<CORE>/prompts/cdo_create_design.md` | `<CORE>/../skills/cdo/.claude/skills/product-design/prompts/rich.md` |
| `<CORE>/prompts/cdo_create_uxd.md` | `<CORE>/../skills/cdo/.claude/skills/product-uxd/prompts/rich.md` |
| `<CORE>/prompts/cdo_create_visual_experience.md` | `<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md` |
| `<CORE>/prompts/content_manager_create_content.md` | `<CORE>/../skills/content-manager/.claude/skills/product-content/prompts/rich.md` |
| `<CORE>/prompts/content_manager_create_voice_experience.md` | `<CORE>/../skills/content-manager/.claude/skills/experience-voice/prompts/rich.md` |
| `<CORE>/prompts/content_manager_create_writing_bar.md` | `<CORE>/../skills/content-manager/.claude/skills/kensaiapp-writing-bar/prompts/rich.md` |
| `<CORE>/prompts/cpo_create_prd.md` | `<CORE>/../skills/cpo/.claude/skills/product-prd/prompts/rich.md` |
| `<CORE>/prompts/cto_create_sdd.md` | `<CORE>/../skills/cto/.claude/skills/product-sdd/prompts/rich.md` |
| `<CORE>/prompts/cto_create_srs.md` | `<CORE>/../skills/cto/.claude/skills/product-srs/prompts/rich.md` |
| `<CORE>/prompts/principal_architect_create_architecture.md` | `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md` |
| `<CORE>/prompts/principal_pm_create_fdr.md` | `<CORE>/../skills/principal-pm/.claude/skills/product-fdr/prompts/rich.md` |
| `<CORE>/prompts/principal_pm_set_up_product.md` | `<CORE>/../skills/interactive-product/.claude/skills/product-card/prompts/rich.md` |
| `<CORE>/prompts/pm_shukuba_refine.md` | `<CORE>/../skills/pm/.claude/skills/shukuba-refine/prompts/rich.md` |
| `<CORE>/prompts/pm_split_seed.md` | `<CORE>/../skills/pm/.claude/skills/stations-from-seed/prompts/rich.md` |
| `<CORE>/prompts/principal_pm_cut_seeds_from_docs.md` | `<CORE>/../skills/principal-pm/.claude/skills/seeds-from-product-docs/prompts/rich.md` |
| `<CORE>/prompts/decide_companion_answers.md` | `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` |
| `<CORE>/launchers/product-setup/launcher.sh` | `<CORE>/launchers/product-card/launcher.sh` |
| `<CORE>/../skills/interactive-product/.claude/skills/product-setup/` | `<CORE>/../skills/interactive-product/.claude/skills/product-card/` |
| `<CORE>/../skills/interactive/.claude/skills/ad-hoc-plan/` | `<CORE>/../skills/tech-lead/.claude/skills/ad-hoc-plan/` |
