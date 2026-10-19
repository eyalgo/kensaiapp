---
version: "3.3.0"
---

# Commit format doctrine

Extracted from CLAUDE.md §Commit message format (all roles) + §Surface tracking on 2026-05-07
as part of Batch 4 lean-CLAUDE.md refactor. Forward-only from the codification dates noted inline.
`AGENTS.md` carries the stub pointing here; this file is the single source of truth for **how this system
uses git** — both the message a commit carries and the operations that produce it. The message half is
§ Commit message format onward; the operations half is § Git operations at the end. Widened from
commit conventions alone on 2026-08-24, because the operation rules had accumulated in three other
places and a rule about the index is not a rule about a skill.

The trailer format below is *constructed* by `core/tools/commit_builder.py` (added 2026-07-07) —
the one executable a caller hands a subject + body and its own actor identity to, and gets back a
commit with every trailer in canonical order, the git op already run. This doc stays the format's
single source of truth; the builder is its executable source, not a second definition.

---

## Commit message format (all roles)

Every commit must include a `Role:` trailer line identifying the **originator** (not just the labor):

```
<subject line>

<body>

Shukuba: <YYYY-MM-DD>_<slug> — progress: <one-line how>   ← topmost is the directional trailer: `Shukuba:`/`Agari:` (project-scoped) or `Michi:` (instance-level); resolves to progress/serves / aside / none — see "Directional trailer" below
Role: Developer        ← or CPO / CTO / CDO / Product Owner / PM / Principal PM / Principal Architect / Tech Lead / Senior Engineer / Content Manager / Content Editor / Scrum Master / Architect / Auditor / KensaiApp Auditor / Kaizen Fix Author / Kaizen Fixer / Product / Meta
Surface: Claude Code   ← or Cowork / Codex / Gemini / product-skeleton (the one no-AI committer) — see "Surface:" below
Co-Authored-By: <Your Model> <noreply@anthropic.com>  ← see "Filling the model" below; fill from your own runtime identity, do NOT copy an example. OMITTED entirely when no model ran
Reasoning-Effort: <low | medium | high | xhigh | max>  ← optional, explicit-only runtime attribution; see "Reasoning-Effort: trailer" below
Claude-Session: <url>  ← optional conversation attribution; see "Claude-Session: trailer" below
Skill-Version: <skill-name>@<semver> <full-40-char-sha>  ← optional, non-required — present only when the caller passes --skill; see "Skill-Version: trailer" below
Prompt-Version: <prompt-name>@<semver> <full-40-char-sha>  ← optional, non-required — present only when the caller passes --prompt; see "Prompt-Version: trailer" below
Workflow-Version: <workflow-name>@<semver> <full-40-char-sha>  ← optional, non-required — present only when the caller passes --workflow; see "Workflow-Version: trailer" below
```

### Filling the model (dynamic — never hardcoded)

The `Co-Authored-By:` model is **dynamic**: each committer writes the model it is *actually* running, read from its own runtime/system context. Claude Code states this in the session environment block (e.g. "powered by the model named **Opus 4.8**").

- **Do not copy the model token from any example in this file.** Every example uses the `<Your Model>` placeholder precisely so a stale version (the old `Opus 4.7` / `Sonnet 4.6` literals) can't leak into commits.
- A Claude model is written by its **display name** (`Claude Opus 4.8`), not the model id (`claude-opus-4-8`).
- **A Codex run writes the model Kensaiapp assigned it**, as `<model id> <noreply@openai.com>` (e.g. `gpt-5.6-terra <noreply@openai.com>`). The value is the model id exactly as the assignment names it. It is not a self-report: the launcher resolves the model before `codex exec` starts and hands the exact value to the run in its bootstrap context (`<CORE>/tools/task_context.py` `codex_bootstrap`). A Codex run with **no assigned model** writes `Codex <noreply@openai.com>` — an AI ran, so the line stays, naming the provider where the model is unknown.
- **A Gemini run writes the model Kensaiapp assigned it**, as `<model id> <noreply@google.com>` (e.g. `gemini-3.8-flash-high <noreply@google.com>`). Same rule as Codex: the launcher resolves the model before `agy -p` starts and hands the exact value to the run in its bootstrap context (`<CORE>/tools/task_context.py` `gemini_bootstrap`). A Gemini run with **no assigned model** writes `Gemini <noreply@google.com>`.
- This is a self-report, not an enforced mechanism — the harness exposes no env var or git-hook source for the running model (verified 2026-06-19), so the committer is the source of truth. It always knows its current identity, including after a mid-session model switch.
- **A committer with no model omits the line entirely** (added 2026-09-03). Where no model ran, there is nothing to self-report and the trailer is left out — not filled with the launcher's name, not with the model of whoever happened to be watching. `Role:` and `Surface:` are the enforced set (`verify_commit_msg.py` presence-checks exactly those two), so the block stays valid without it, and the absence positively means *no model authored this commit*. `commit_builder.py`'s `--co-authored-by` is optional for this reason. The standing case is a deterministic launcher — see `Surface: product-skeleton` below. **This is not an escape for an AI committer that finds the value inconvenient**: an agent that ran at all has a runtime identity and fills it from that, per the bullet below.
- **No-slot / variable-model committer.** An agent with no pinned model — a general-purpose subagent or a `--bg` run on a selectable tier — **must** fill `--co-authored-by` from its **own runtime identity** (the "powered by the model named X" line in its session context) and **must not** use a model literal handed to it in its spawn prompt. That literal is the spawner's guess at what model would run, not the model that actually ran; only the running agent knows its real identity. A Codex run is not this case: its launcher passes the model to `codex exec` itself (`--model`), so the value in its context is the model that ran, per the Codex bullet above. (`model_assignment.md` § Runs with no standing slot owns *which tier* a no-slot run picks; this section owns *how* the chosen model is recorded.)

### `Reasoning-Effort:` trailer — resolved runtime effort

**Meaning:** the reasoning-effort level the committing run actually used. Its one authoritative input is the resolved level explicitly supplied to the builder by that run; the builder never derives, defaults, recovers, or selects it from a model, model tier, provider, surface, environment, or any other runtime state.

**Shape:** `Reasoning-Effort: <level>`, where `<level>` is exactly one of `low`, `medium`, `high`, `xhigh`, or `max`. A launch resolved to `max` records `Reasoning-Effort: max`: the level is recorded as resolved, never replaced by another level and never omitted because it is `max`.

**Optional, explicit-only, and exact once:** `commit`, `merge`, and `advance` each carry exactly one line when their caller supplies one resolved level. When the caller supplies none, the line is omitted entirely: omission means no effort reached the builder, not that it was inferred, unknown, or defaulted. This does not widen the required trailer set (`commit → Role:, Surface:`; `merge → Merge-Authorized:, Surface:`), and it does not change `Surface:` or `Co-Authored-By:` semantics.

**Position:** directly after `Co-Authored-By:` when that trailer is present, otherwise directly after `Surface:`, and before `Claude-Session:` and every provenance trailer. It is runtime attribution beside the surface and model identity, not provenance for machinery that produced the output.

### Directional trailer — Shukuba / Agari (project) / Michi (instance) (added 2026-06-22; Michi split added 2026-07-04; Agari pre-station referent added 2026-07-10)

Every commit carries a **directional trailer** as its **topmost** trailer — it states how the commit relates to where the system is headed. Which trailer applies depends on the commit's scope, and **exactly one** appears per commit:

- **Project-scoped commit** (work on one project `<name>`) → **`Shukuba:`** or **`Agari:`**, depending on the project's phase. A station is the *near* referent (the current leg being walked); the 上がり Agari is the *far* referent (the product's terminus). Use the finest one that exists: an **open station** → `Shukuba:`, resolved against `system/projects/<name>/journey/shukuba/`; **no open station** (the executive / pre-station phase — CPO authoring the PRD and declaring the Agari, upstream of the delivery loop) → `Agari:`, resolved against `system/projects/<name>/agari.md`. See "`Shukuba:`" and "`Agari:`" below.
- **Instance / app-level commit** (touches no single project — instance doctrine, a skill, `michi.md`, the README, setup/scaffold tooling) → **`Michi:`**, resolved against `system/michi.md` — the endless Way(s) (道) the instance steers by.

In a kensaiapp instance 宿場 Shukuba exists at **both levels, as two different kinds**: a project's is *walked*, and the instance's `system/shukuba/` is a **router** that coordinates several projects pushing on one shared thing (`kensaiapp_structure.md` §1). **The directional trailer follows scope, not item type.** An instance-scoped commit takes **`Michi:`** whatever it touches — a commit editing `system/shukuba/` included — because the instance steers by its 道 Michi, which nothing reaches; `Shukuba:` names a **project's** station only, resolved against that project's `journey/shukuba/`. If a commit genuinely spans both an instance concern and one project, that's a batching smell — split it so each commit carries one directional trailer.

**This trailer never blocks a commit. It is always resolved.**

**`Shukuba:` — project-scoped commits.** Read the project's `journey/shukuba/`, then one of three:

1. **Commit progresses the named station:**
   ```
   Shukuba: <YYYY-MM-DD>_<slug> — progress: <how this commit advances toward the station>
   ```
2. **Commit is an aside** (points away / undoes progress, or is orthogonal — hygiene, an unrelated concern), committed anyway:
   ```
   Shukuba: <YYYY-MM-DD>_<slug> — aside: <why this commit is made, given it doesn't advance the station>
   ```
When the project has **no open station** — its `journey/shukuba/` holds only the placeholder README, because the station referent doesn't exist yet — do **not** write `Shukuba: none`. Resolve against the project's terminus instead, using **`Agari:`** (next). The pre-station executive phase is real progress toward the done, not a station-less nothing.

Don't stretch a `progress:` proof to dodge `aside:` — if the commit doesn't genuinely move toward the station, it's an aside, and saying so is the honest record.

**The station is named by its dated stem, `<YYYY-MM-DD>_<slug>`** — its filename under `journey/shukuba/` without `.md`, the same name the triple carries (`single_source.md` § *A pointer at a journey artifact names project, kind and name*). Never the bare `<slug>`: one project may hold two stations under one slug on different dates, and the bare form cannot tell them apart. Settled 2026-09-14; commits written before often carry the bare slug, and they stay as written.

**`Agari:` — project-scoped commits with no open station.** The executive / definitional phase (CPO authoring the PRD and declaring the 上がり Agari, the Principal PM's FDR) runs *upstream of the delivery loop*, before the PM opens the first station — yet it is the most consequential early progress a product makes. Its referent is the project's terminus itself, its Agari (`system/projects/<name>/agari.md`). An Agari is *reached* (the project settles), so like a station it uses `progress:` (toward the done), never `serves:` — that is Michi's, for a Way nothing reaches. One of three:

1. **Commit advances the product's done:**
   ```
   Agari: <name> — progress: <how this commit defines / moves toward the product's done>
   ```
2. **Commit is an aside** (hygiene, an unrelated concern), committed anyway:
   ```
   Agari: <name> — aside: <why this commit is made, given it doesn't advance the done>
   ```
3. **No Agari declared yet** (`agari.md` is still a placeholder — a fresh project before `project-agari` has run):
   ```
   Agari: none — <what this commit did>
   ```

`<name>` is the project name. This is the project altitude's *far* referent — used exactly when the *near* referent (an open Shukuba station) doesn't exist. It retires the former `Shukuba: none` fallback: authoring the PRD and declaring the Agari is progress toward the terminus, and `Agari: <name> — progress:` says so, where `Shukuba: none` read falsely as "no progress." `none` now means only what it should — a project so fresh its Agari isn't declared yet.

**`Michi:` — instance / app-level commits.** Read `system/michi.md`. A Michi is a **declaration** (1..N Ways, never retired) and is never *reached*, so it uses `serves` (the commit walks a Way), not `progress` (toward a station). One of three:

1. **Commit serves a declared Way:**
   ```
   Michi: <way-slug> — serves: <how this commit walks that Way>
   ```
2. **Commit is an aside to the Ways** (collaboration infra, hygiene, an unrelated concern), committed anyway:
   ```
   Michi: aside: <why this commit is made, given it doesn't serve a Way>
   ```
3. **No Michi declared yet** (`system/michi.md` still a placeholder — a fresh instance, before `kensaiapp-michi` has run):
   ```
   Michi: none — <what this commit did>
   ```

`<way-slug>` is the Way's slug from `system/michi.md` (e.g. `sharpen-by-living`). A commit that serves more than one Way names the primary one and can mention the others in the body.

**Never-block rule.** No directional trailer ever gates a commit. A missing / placeholder station, Agari, or Michi is not a blocker (resolve to the next referent down, or `none`). An aside is not a blocker (explain and proceed). The committer always resolves to one of the states above and writes it — the trailer documents the directional relationship; it does not stop the commit.

**Why:** Shukuba (bounded station) and Michi (endless Way) are stable directional referents — unlike sequence-relative labels (gate / iteration numbers) that decay as more are added. Forcing every commit to state its relationship to the destination keeps `git log` honest about whether work heads where the system is going. The `progress` / `serves`-vs-`aside` split is greppable, so a run of asides during a supposed march surfaces drift early — without ever stopping a commit that needs to land.

Greppable: `git log --grep "Michi: sharpen-by-living — serves:"` returns commits walking that Way; `git log --grep "<slug> — progress:"` returns commits advancing a station — the undated part without the `Shukuba: ` prefix, so it matches the dated stem and the bare slug older commits carry; `git log --grep "Agari: <name> — progress:"` returns the executive-tier commits advancing a product's done; `git log --grep "aside:"` returns the asides; `git log --grep ": none"` returns the no-referent set.

**Role values:**

- **CPO / CTO / CDO / Product Owner / PM / Principal PM / Principal Architect / Tech Lead / Developer / Senior Engineer / Content Manager / Content Editor / Scrum Master / Architect** — an AI role or posture (per §Roles or the postures above §Roles) did the work on its own initiative and within its scope.
- **CPO** — the executive product role: it sets the project's 上がり Agari (`agari.md`) and authors the PRD (`docs/PRD.md`), upstream of the delivery loop. Distinct from the delivery-tier **Product Owner** (below), which only shares the word "product" and writes per-change specs. Applies when a `cpo:` session commits Agari or PRD work — interactively the session passes `--role CPO` verbatim; the `cpo` subagent actor maps to `CPO` via the builder's `AGENT_ROLE`. Codified 2026-07-09.
- **CTO** — the executive technical role: it authors the **SRS** (`docs/SRS.md`) and the **SDD** (`docs/SDD.md`), the CPO's and the CDO's calls reaching it through the companion, upstream of the delivery loop. Distinct from the delivery-tier **Architect**, which only designs individual changes inside the change pipeline. Applies when a `cto:` session commits SRS or SDD work — interactively the session passes `--role CTO` verbatim; the `cto` subagent actor maps to `CTO` via the builder's `AGENT_ROLE`. Codified 2026-07-10.
- **CDO** — the executive design role: it authors the **UXD** (`docs/UXD.md`) and the **design language** (`docs/DESIGN.md`), upstream of the delivery loop. Distinct from the delivery-tier **Architect**, which only designs individual changes inside the change pipeline — the word "design" collides, the altitude does not. Applies when a `cdo:` session commits UXD or design-language work — interactively the session passes `--role CDO` verbatim; the `cdo` subagent actor maps to `CDO` via the builder's `AGENT_ROLE`. Codified 2026-07-31.
- **Senior Engineer** — the Opus reviewer of the Developer's code: its own seat, with its own loader (`<CORE>/roles/loaders/senior_engineer_global.md`) that holds it to the Developer's engineering standard, running the `development-code-integrity` step on the Opus tier, and merging a reviewed ad-hoc branch. Its own loader since 2026-09-23; until then it read the Developer's. Distinct from `Developer` so the careful code-integrity review shows up as its own originator in `git log` (implementation → `Role: Developer`, code-integrity → `Role: Senior Engineer`). Actor: the `senior-engineer` subagent. Codified 2026-07-07 (roles worker/reviewer model split).
- **Content Manager** — the definition-tier role that owns the product's **words**: whether content is needed, where it belongs, and how it is worded. It authors `CONTENT.md` (the verbal language — voice, tone, terminology, the standard message patterns, the accessibility bar for text, localization), the peer of the CDO's `DESIGN.md`. Distinct from the **CDO**, which owns the experience and *reviews* the words against it rather than authoring them, and from the **CPO**, whose product truth it preserves and may not change; it may not alter product meaning, calculations, or approved legal language. It takes the retired **Editor**'s seat (below), so this instance's external-facing prose is its work too. Applies when a `content-manager:` session commits content work — interactively the session passes `--role Content Manager` verbatim; the `content-manager` subagent actor maps to `Content Manager` via the builder's `AGENT_ROLE`. Codified 2026-08-05.
- **Content Editor** — the delivery-tier role that writes the **text one change publishes**, to the standard the Content Manager keeps (`CONTENT.md` and the instance's writing bar). Distinct from the **Content Manager**, which owns the standing words — the rules — where this seat writes one change's strings; from the **Developer**, which places the text this seat wrote and does not write or alter it; and from the retired **Editor** tag (below), a different seat that shares only part of the name. Applies when a `content-editor:` session commits a change's text — interactively the session passes `--role Content Editor` verbatim; the `content-editor` subagent actor maps to `Content Editor` via the builder's `AGENT_ROLE`. It may author a commit and does not authorize a merge: the `content-editor` actor has no `MERGE_AUTHORIZER` row. Codified 2026-10-03.
- **Principal PM** — the executive delivery seat: authors a product's FDR, cuts an idea — or a product's settled documents — into 根回し Nemawashi seeds and their **proposed** station checklists, which the PM re-cuts at the pick, and decides the cross-project route order. Distinct from **PM**, which is the pipeline owner for one directed project and carries the traverse itself — picking the active idea, re-cutting its checklist into the stations that will be walked (`stations-from-seed`), opening a station, closing it, opening a change unit. Same noun, different span, so each is its own first-class value and `git log` can tell the shape from the walking. Actor: the `principal-pm` subagent. Greppable: `git log --grep "Role: Principal PM"`. Codified 2026-08-11.
- **Principal Architect** — the executive architecture seat: records a product's architecturally significant decisions as an append-only log (`<product>/docs/adr/`) and binds what a later change may not break (`<product>/docs/nfdr.md`), written from the settled SRS and SDD. Distinct from **CTO**, which *decides* the architecture in the SDD where this seat *records* it, and from **Architect**, the delivery-tier seat that *consumes* these records to design one change where this seat *produces* them — the noun collides, the altitude and the direction both do not. Actor: the `principal-architect` subagent. Greppable: `git log --grep "Role: Principal Architect"`. Codified 2026-08-30.
- **Product** — the user (product owner) is the originator of the content, decision, or request. Used for user-authored content, user-requested work whose content belongs to the user, user-ratified decisions, and user-imported artifacts (external memos, sketches, research requests from approved sources). An AI role may have synthesized the prose or executed the commit; initiative and authority sit with the user. Credit the labor in the commit body rather than the Role: trailer. **This covers machinery the user asked for — a skill, a tool, a launcher, an agent** (settled 2026-07-30): the deciding was theirs even when an AI wrote every line. Not `Meta`, which is narrower and scoped to the user↔AI interface (below), and not the posture of whoever built it, since a posture Role claims that role acted on its own initiative.
- **Meta** — the commit concerns the **user↔AI interface itself**, not project content. Narrow scope: commit message format / Role trailer conventions, run prompt launch commands, slash commands under `.claude/commands/`, prompt-writing conventions in `runs/plan.md` that govern how Claude is invoked, and any memory-organization rules that live in the repo. Does NOT apply to AI-role context files (project CONTEXT files, etc. — tech lead editing its own context is still Role: Tech Lead), workflow scripts, project doctrine, or project-internal role mechanics. Credit the originator in the body (user-initiated or tech lead-initiated), same pattern as Product.
- **Auditor** — used when an AI session commits work whose substance or specification originated from another session (typically Cowork drafted a file directly, OR Cowork drafted a handoff/spec that the committing session executed mechanically). The committing session is a courier or mechanical executor, not the originator. Distinct from Architect (substantive adversarial review or sparring) and Meta (where the committing session itself authored the interface change). No context file, no posture rules — Auditor is purely an attribution tag for the cowork→committer handoff visible in `git log`. Forward-only from codification date; pre-existing commits with `Role: Meta` for cowork-drafted work stay as-is. Subject prefix: `auditor:`. Greppable: `git log --grep "Role: Auditor"`.
- **KensaiApp Auditor** — the `development-audit` posture committing `flow_findings/<step>.md`: a fresh, role-neutral audit of **KensaiApp's own pipeline output quality** (the flow machinery — coverage / altitude / classification-propagation / divergence-record), not the product and not a cowork courier. It originates its own findings on its own initiative, so it is its own first-class value (distinct from `Auditor`, the cowork→committer courier tag, and from `Meta`, the user↔AI interface). Used only for the per-step `flow_findings/<step>.md` commits the auditor makes on its own audit branch, `<key>__audit-<step>`, which `tobiishi-seal` merges into the change branch before it seals. Subject prefix: `development-audit:`. Greppable: `git log --grep "Role: KensaiApp Auditor"`. Codified 2026-06-23.
- **Kaizen Fix Author** — the kaizen fix author: decides what a round's fix is from the audit's findings, writes its exact replacement text, and commits the resulting fix packet (`fix_packet.md`) for the fixer to apply. It originates the decision and the prose, so it is its own first-class value — distinct from `Kaizen Fixer`, which applies a packet it did not author, and from `KensaiApp Auditor`, which only reports. Actor: the `kaizen-fix-author` subagent. Its output is a packet, not a skill's product, so it passes no `--skill` and carries no `Skill-Version:` — same as `pm` (and, under explicit-only provenance, same as any actor that ran no producing skill). Subject prefix: `kaizen(<skill>):`. Greppable: `git log --grep "Role: Kaizen Fix Author"`. Codified 2026-07-20.
- **Kaizen Fixer** — the kaizen cold-read fixer: applies a fresh reader's BREAK/DEGRADE findings to a skill's `SKILL.md` and commits the round (the acting half of the loop; the `kensaiapp-auditor` reader only sees). It originates the edit, so it is its own first-class value — not `Meta` (that is the user↔AI interface, not an origination identity). Actor: the `kaizen-fixer` subagent. Subject prefix: `kaizen(<skill>):`. Greppable: `git log --grep "Role: Kaizen Fixer"`. Forward-only from 2026-07-18; prior cold-read fix commits keep `Role: Meta`.

Role tracks *origination* (for CPO / CTO / CDO / Tech Lead / Developer / Content Manager / Content Editor / Scrum Master / Architect / Product / Auditor) or *interface-vs-project-content* (for Meta). When in doubt: who decided this commit should exist *and* what does it touch? If the answer is "the user asked for this" or "the user authored this and I committed it on request," the Role: is Product. If a different AI session drafted the file or spec and the committing session is just executing/couriering, the Role: is Auditor. If the commit changes how we transact across the user↔AI channel and the committing session itself authored that change, the Role: is Meta regardless of originator. No retroactive changes to historical commits — the rule applies forward from 2026-04-23 (Role taxonomy) / 2026-05-06 (Auditor addition). **Analyst** was retired 2026-07-12 (legacy posture, no agent, no loader) — historical commits keep the tag, but it is not a valid Role going forward. **Editor** was retired 2026-08-05 the same way (prefix-only, no agent, no `AGENT_ROLE` row); its seat is taken by the **Content Manager**, whose posture carries the external-facing-docs work that was the Editor's. Historical commits keep the tag. Neither retirement is enforced anywhere — `verify_commit_msg.py` presence-checks `Role:` and never validates its value — so this list is the record of what is valid, not a gate. **Delegate** was never a Role: it names the *mechanism* (the `delegate` agent, which carries no posture) rather than the originator, so it says nothing about where a commit came from. That agent has no `AGENT_ROLE` row for the same reason — it passes `--role` with what the work originates as, usually `Product`. Six commits on 2026-07-30 (`deb750c`, `2cbf2fc`, `0aea92a`, `87c9ec5`, `89122ed`, `30309d7`) carry it in error, from runs that answered the builder's refusal of `--actor delegate` by capitalising their own actor token; they stay.

### How the `Role:` value is supplied — derived from the actor, not the skill (added 2026-07-07)

Skills say **nothing** about `Role:`. It is supplied by the **commit builder** (`core/tools/commit_builder.py`) — the one place every skill-driven committer calls to construct the trailer block. Construction and verification are separate: the builder writes `Role:`, and the git-native `commit-msg` hook (`core/githooks/commit-msg` → `core/tools/verify_commit_msg.py`) presence-checks it afterward, blocking any commit missing `Role:`/`Surface:`. The hook never injects — it only verifies.

- **In the chain** (`core/launchers/chain-development/launcher.sh` → `core/tools/chain_development.py`), each step is its own run under the `**Agent:**` its skill's `launcher.md` names (`skill/launcher.sh`, its `field Agent` read), and it passes that agent as `--actor`; the builder maps it to a Role via its `AGENT_ROLE` table: `product-owner → Product Owner`, `architect → Architect`, `tech-lead → Tech Lead`, `developer → Developer`, `senior-engineer → Senior Engineer`, `content-manager → Content Manager`, `content-editor → Content Editor`, `pm → PM`, `kensaiapp-auditor → KensaiApp Auditor`. Switching a stage's engineer (as the roles split did — the `code-integrity` stage now runs the `senior-engineer` actor) is then an `**Agent:**` edit in that step's skill `launcher.md`, plus the step's `role` in the chain's step table, which stamps telemetry (`chain_development.py`'s `DEVELOPMENT_STEPS` table, and `INSTRUMENT_RUN_ROLE` set from `step.role`) — no skill change. Add the new actor to the builder's `AGENT_ROLE` map **and** to the Role list above, together.
- **Interactively** there is no subagent identity, so the session passes its own posture `Role:` to the builder verbatim as `--role` (role-prefix → that role; user-directed → Product; interface-only → Meta). The builder takes exactly one of `--actor`/`--role`.
- **One `Role:`, no injection layer:** the builder always writes exactly one `Role:` (derived or verbatim), so there is nothing that could silently overwrite a caller's value. On a **merge** the builder replaces `Role:` and the directional trailer with `Merge-Authorized:`, derived the same way — from `--actor` via a `MERGE_AUTHORIZER` table. On an **advance** it writes `Merge-Authorized:` in place of `Role:` and the directional trailer too, but derives it from `AGENT_ROLE` directly for `--actor` (or `INTERACTIVE_MERGE_AUTHORIZERS` for `--authorizer`) rather than from `MERGE_AUTHORIZER` — an advance lands nothing on `main`, so any commit actor may authorize it. `MERGE_AUTHORIZER` stays the narrower, to-`main` set.
- **`Skill-Version:` is decoupled from the actor (2026-07-24).** `Role:` stays actor-derived (this section); skill provenance is **not** — it is supplied by an explicit `--skill <name>` only, never inferred from `--actor`. A commit's `Role:` says *who committed*; its `Skill-Version:` (when present) says *what skill produced the output* — two independent facts, so `--actor` no longer does double duty. See §`Skill-Version:` trailer.

This replaced per-skill hardcoded `Role:` lines (prototype `bugs-and-hygiene` item f, 2026-07-07) and the earlier `enforce_commit_role.py` PreToolUse inject-and-block hook (retired 2026-07-07 — construction moved to the builder, verification to the `commit-msg` hook). A skill baking in a specific Role coupled a task to an identity, so changing the actor forced a skill edit. Because the automated seal now derives from its `pm` actor, its bookkeeping commit is `Role: PM` — and the merge it makes records `Merge-Authorized: PM`, derived the same way from the `pm` actor (the chain's seal has no human gate, so the mechanical authorizer is PM, not Product). An interactive, human-gated merge derives `Merge-Authorized: Product` — **not** through the `MERGE_AUTHORIZER` map, which is keyed by actor and has no `product` actor to key on, but through the merge path's `--authorizer` flag against `INTERACTIVE_MERGE_AUTHORIZERS` (see `core/tools/commit_builder.py`, and the paragraphs below). Until 2026-07-27 this paragraph said the map "admits it as a data change"; that was wrong, and putting `Product` there would have broken the strict-subset property the map exists to state.

**`MERGE_AUTHORIZER` is deliberately narrower than `AGENT_ROLE`, and that narrowness is the policy it exists to state (2026-07-27).** Every authorizer in it is spelled exactly as that actor's `Role:`, so as a translation table it would be duplication; what it does that `AGENT_ROLE` cannot is *exclude*. `AGENT_ROLE` is everyone who may author a commit. `MERGE_AUTHORIZER` is the subset who may authorize a merge to `main` — the highest-consequence operation in the repo.

The exclusion carrying the rule: **`developer` is a commit actor and does not authorize a merge to `main`.** A developer does not merge its own branch; the `senior-engineer` runs `development-code-integrity` over it and merges on the strength of that pass. That is the worker/reviewer split — the Developer implements, the Senior Engineer reviews and merges — written down where the merge is actually constructed. `senior-engineer` was added to the map on 2026-07-27 for exactly that flow — an ad-hoc branch reviewed and merged outside the change pipeline, where `tobiishi-seal`'s `pm` actor does not apply because there is no Tobiishi to seal.

**This is a stated policy, not enforcement.** The actor is self-declared, so a `developer` passing `--actor pm` would produce `Merge-Authorized: PM` and nothing in the builder would catch it. What the map buys is an explicit set and the friction of having to edit it — not a control. `core/tools/test_commit_builder.py` pins the strict-subset property and the `developer` exclusion, because an intentional absence has no line to read and is otherwise indistinguishable from a forgotten row.

**An interactive, human-gated merge is authorized by `Product`, on its own axis (2026-07-27).** The merge path takes exactly one of `--actor` (an agent, resolved through `MERGE_AUTHORIZER`) or **`--authorizer`** (an interactive caller, supplied verbatim) — mirroring the `--actor` / `--role` split the commit path has always had, and which the merge path lacked. Until this existed, a merge the owner directed had no way to say so, and the only honest-looking option was to borrow an actor that had not done the authorizing.

`Product` is **not** a `MERGE_AUTHORIZER` row and cannot become one. That table is keyed by an actor's `agent_type` and its rows must be spelled as that actor's own `Role:`; there is no `product` subagent to key on, and adding it would break the strict-subset property that carries the policy above. It lives in `INTERACTIVE_MERGE_AUTHORIZERS` instead.

**The interactive value is validated against a closed set, where `--role` on the commit path is not.** That asymmetry is deliberate. An unchecked verbatim flag would let any caller write any authorizer, which dissolves in one argument the whole point of keeping the actor list narrow. Two closed sets — one per identity kind — keep the property true on both paths.

### `Skill-Version:` trailer — skill provenance (added 2026-07-09)

**Meaning:** which skill produced the committed output — its name, its declared semantic version, and the exact source-commit SHA of that skill at production time.

**Shape:** `Skill-Version: <skill-name>@<semver> <full-40-char-sha>` (example: `Skill-Version: development-design@1.9.0 4f2a9c7d3e1b8a06c5f4d2e9b7a3c1f0e8d6b4a2`). The SHA is always the full 40-character `%H`, never abbreviated.

**Non-required:** its presence or absence never blocks a commit. The required-trailer set `core/tools/verify_commit_msg.py` enforces (`commit → Role:, Surface:`; `merge → Merge-Authorized:, Surface:`) is unchanged.

**Absence means no producing skill authored this commit.** The line is omitted entirely (no `N/A` placeholder) whenever no `--skill` was passed — a **legitimate, common state, not a gap**: a role or general-purpose session hand-authoring an artifact, a `pm` seal/bookkeeping commit, and every **merge** (a merge is authored by the merge authorizer, not a producing skill). Absence positively means "no producing skill produced this commit's output" — it does **not** mean "unknown," "missing," or "error," and it never blocks a commit (the required set `verify_commit_msg.py` enforces is unchanged).

**How it is supplied:** the builder (`core/tools/commit_builder.py`) stamps `Skill-Version:` **iff** the caller passes `--skill <name>`, naming the producing skill outright. It then reads that skill's declared version from its `SKILL.md` frontmatter and its source's last-modifying commit SHA (`git log -1 --format=%H -- .claude/skills/<name>/`) — never repo `HEAD`, which would change on every commit and carry no drift signal. If either can't be read, the builder omits the line rather than fabricate a value or block the commit. Provenance is **explicit-only** (2026-07-24): the earlier `--actor` → `ACTOR_SKILL` derivation was retired because it inferred *what skill produced the output* from *who committed*, so a role or general-purpose session that committed via `--actor` without running a skill got a skill falsely stamped. A producing skill records its own name via `--skill` (the shared recipe `<CORE>/doctrine/governance/commit_via_builder.md` names it); a caller that ran no skill passes none and correctly carries no line.

**Position:** below `Reasoning-Effort:` when it is present, otherwise below `Claude-Session:`, and above `Prompt-Version:` and `Workflow-Version:` when they are present (see below and in §Surface tracking).

### `Prompt-Version:` trailer — prompt provenance (added 2026-08-20)

**Meaning:** which **prompt** a session read to produce the committed output — its name, its declared semantic version, and the exact source-commit SHA of that prompt at production time. The sibling of `Skill-Version:`, and the answer to the case that one structurally cannot cover.

**Why it exists.** `Skill-Version:` is read out of a skill's `SKILL.md`. A prompt read straight by a session — `core/prompts/declare_loader_domain.md`, the three `cto_create_*` doctrine lenses, `ratify_skill.md` — has no `SKILL.md` to read a version out of, so its output committed with no provenance line at all. Since absence positively means *"no producing skill produced this commit's output"* (below), a run that followed a versioned lens was byte-identical in `git log` to a hand-authored commit. Every prompt already declares a `version:`; nothing could key to it.

**Shape:** `Prompt-Version: <prompt-name>@<semver> <full-40-char-sha>` (example: `Prompt-Version: pm_right_size@2.2.0 4f2a9c7d3e1b8a06c5f4d2e9b7a3c1f0e8d6b4a2`). The SHA is always the full 40-character `%H`, never abbreviated.

**Non-required, and absence means the same kind of thing.** Its presence or absence never blocks a commit; the required set `core/tools/verify_commit_msg.py` enforces is unchanged. The line is omitted entirely (no `N/A` placeholder) whenever no `--prompt` was passed, and that absence positively means **no prompt produced this commit's output** — a legitimate, common state, not a gap, and never "unknown" or "missing."

**How it is supplied:** the builder stamps it **iff** the caller passes `--prompt <name>`, naming the prompt outright. It reads that prompt's `version:` from its own frontmatter and its last-modifying commit SHA (`git log -1 --format=%H -- <the prompt file>`) — never repo `HEAD`, which would change on every commit and carry no drift signal. If either can't be read, the builder omits the line rather than fabricate a value or block the commit. Explicit-only from the start, the property `Skill-Version:` had to be corrected into on 2026-07-24: nothing is inferred from `--actor`.

**It takes a name, never a path.** A prompt lives in one of two places, and the name says which: a bare `<name>` is `core/prompts/<name>.md`, and `<skill>/<prompt>` is that skill's own `prompts/<prompt>.md`, the skill resolved exactly as `Skill-Version:` resolves it. A satellite carries no `core/` of its own and resolves `<CORE>` to the host instance's, and its skills are the host's by symlink, so either name has exactly one resolution from anywhere, while a path has as many as there are working directories. Resolution runs against the **instance** repo, never `--repo`, for the same reason `Skill-Version:` does: an external product repo holds no prompt source. A satellite's commit therefore carries a SHA that resolves in the host instance and not in the satellite, exactly as its `Skill-Version:` already does.

**Independent of `Skill-Version:` — both may appear.** They are two facts, not two spellings of one: *which skill ran* and *which prompt ran*. There is no mutually-exclusive group. A thin skill over a fat prompt — the shape the `product-*` family now has, where the substance lives in `core/prompts/` and the skill is the routing around it — is honestly recorded by **both** lines, and neither implies the other. Which callers pass which flag is the callers' own matter; the builder only records what it is told.

**Not a widening of `--skill`.** `--skill` keeps meaning exactly what it has always meant. Teaching it to accept a prompt would have changed what an existing greppable line means across every commit already carrying one.

**Position:** below `Skill-Version:` when that is present too, below `Reasoning-Effort:` and `Claude-Session:` when it is not, and above `Workflow-Version:` when that is present.

Greppable: `git log --grep "Prompt-Version: pm_right_size@"` returns everything that prompt produced, at any version; `git log --grep "Prompt-Version: pm_right_size@2.2.0"` narrows to one version of it.

### `Workflow-Version:` trailer — workflow provenance (added 2026-08-25)

**Meaning:** which saved **Workflow script** drove the run that produced the committed output — its name, its declared semantic version, and the exact source-commit SHA of that script at production time. The third of the provenance set, and the last silent case.

**Why it exists.** A workflow can hold the load-bearing half of a capability rather than merely sequencing one. `.claude/workflows/ad-hoc-flow.js` carried the flow's four stage prompts as literals, and said so in its own text — *"This workflow is the single place these instructions live"* (`:24` at `a01eb180`; retired 2026-09-18) — so a run could commit an implementation, a code-integrity report and a merge, record which skill and which prompt were involved, and say nothing about the component that actually held the stage instructions the agents worked from. Before 2026-08-24 there was also nothing to name: `versioning.md` gained the workflow marker row that day, and a trailer with no marker to point at would have had nothing to record.

**Shape:** `Workflow-Version: <workflow-name>@<semver> <full-40-char-sha>` (example: `Workflow-Version: sdd-conversation@1.0.0 6da6fcde740e9f5b5600b1794bbd9eec9e4b3075`). The SHA is always the full 40-character `%H`, never abbreviated.

**Non-required, and absence means the same kind of thing.** Its presence or absence never blocks a commit; the required set `core/tools/verify_commit_msg.py` enforces is unchanged. The line is omitted entirely whenever no `--workflow` was passed, and that absence positively means **no workflow drove this commit's output** — the common state, not a gap.

**How it is supplied:** the builder stamps it **iff** the caller passes `--workflow <name>`. Explicit-only, like both siblings, and born that way rather than corrected into it.

**Its read is the one thing that differs from its siblings, and the difference is not cosmetic.** A skill's version is frontmatter in a `SKILL.md` and a prompt's is frontmatter in a `.md`; **a workflow has no frontmatter at all.** Its marker is a `// Version: x.y.z` comment, and `versioning.md` requires that comment to sit **below** the `meta` block rather than at the head of the file — because the workflow tests execute the real bytes through an anchored `source.replace(/^export const meta/, …)` that anything above the block would turn into a no-op. So the builder reads a comment, not frontmatter, with the first whole-line match winning; `.claude/workflows/<name>.js` is the resolved path and its last-modifying commit is the SHA. Anything unreadable omits the line rather than fabricating one.

**It takes a name, never a path**, resolved against the **instance** repo and never `--repo`, for the same reasons its siblings are: there is exactly one `.claude/workflows/`, a satellite reaches it through the host, and an external product repo holds no workflow source.

**Independent of the other two — any subset may appear.** Which skill ran, which prompt it followed, and which workflow drove it are three facts. A capability can genuinely have all three, and then the commit carries three lines in that order.

**Position:** last in the canonical trailer order — below `Prompt-Version:` when that is present, below `Skill-Version:` when only that is, and below `Reasoning-Effort:` and `Claude-Session:` when neither is.

Greppable: `git log --grep "Workflow-Version: sdd-conversation@"` returns everything that workflow drove, at any version.

### `Claude-Session:` trailer — the conversation (added 2026-09-02)

**Meaning:** the URL of the Claude Code session that produced the commit. `Co-Authored-By:` names the model; this names the conversation it ran in.

**Why it exists.** Four trailers already answer a version of *where did this come from* — `Role:` (who originated it), `Surface:` (what ran `git commit`), and the three provenance lines (what machinery produced the output). None of them reaches the transcript, which is the only record that holds the reasoning a commit body had to compress. The harness offers the URL in its own attribution block; before this trailer there was nowhere canonical to put it, so every session resolved the fork privately and the answer was invisible either way. That is the state this closes — the decision is now written once rather than re-made per session.

**Shape:** `Claude-Session: <url>` (example: `Claude-Session: https://claude.ai/code/session_01LprRdLTUV4ymkZdjQDuNer`). One line, the URL verbatim, no name and no version.

**Non-required, and the absence is clean.** Its presence or absence never blocks a commit; the required set `core/tools/verify_commit_msg.py` enforces is unchanged, and that file validates the trailer *set* nowhere — it presence-checks `Role:` and `Surface:` and nothing else, so an undeclared trailer was never the thing at risk here. The line is omitted whenever no `--claude-session` was passed, which positively means **the session had no URL to give**, not that one was withheld.

**How it is supplied:** the builder stamps it **iff** the caller passes `--claude-session <url>`. Explicit-only, like the provenance three — the URL is a fact only the running session holds, and a builder that guessed it would guess wrong in every subagent.

**Position:** directly after `Reasoning-Effort:` when it is present, otherwise directly after `Co-Authored-By:`, and above the provenance lines. The runtime identity and effort say which model and level ran; the session names the conversation, before the machinery that produced the output.

**It is on `merge` too, and that is the one way it differs from the provenance three.** Those are ignored outright on a merge, because a merge is authored by its authorizer rather than by a producing artifact. That argument does not reach this trailer: a merge is made *in a session* exactly as a commit is, and the merge to `main` is the operation whose reasoning is most worth being able to re-read.

**The link points outside this repository, and that is the cost.** It resolves for whoever holds the account and for nobody else, and it will outlive neither the repo nor a git history. It is recorded as a pointer to context, never as evidence: a claim that needs proving cites a path, a SHA, or a command's output, exactly as `single_source.md` requires — this trailer never substitutes for one.

Greppable: `git log --grep "Claude-Session: https://claude.ai/code/session_01Lpr"` returns everything one session committed.

---

## Surface tracking

Trace which AI surface authored each commit and each handoff document. Two parallel mechanisms; same vocabulary.

### Commit trailer: `Surface:`

Every commit carries a `Surface:` trailer alongside `Role:`. Tracks **what ran `git commit`** — mechanically observable, independent of where the work was drafted (which the body attributes if relevant).

Values:

- `Cowork` — Claude Cowork ran `git commit`.
- `Claude Code` — Claude Code (interactive or autonomous) ran `git commit`.
- `Codex` — Codex ran `git commit`.
- `Gemini` — Gemini ran `git commit`.
- `product-skeleton` — `<CORE>/launchers/product-skeleton/launcher.sh` ran it. **No AI session was involved**, which is what this value exists to say.

**`product-skeleton` is a different kind from the AI surfaces above it, and that is deliberate.** Those name an AI surface; this names one deterministic launcher. It was added 2026-09-03 when `product-skeleton` became the first committer in the fleet that runs no model at all — its own header states "No `claude`, no `--agent`, no `--permission-mode`, no prompt" — so there was no AI session to name and nothing honest to put here. The trailer's subject widened from *where the AI session lives* to *what ran the commit*, which the AI surfaces still answer unchanged.

**A no-AI committer omits `Co-Authored-By:` rather than naming a model** — see that trailer's own rule above. `Role:` and `Surface:` remain the enforced set, so the trailer block stays valid with the line absent.

**A launcher earns its own value; it does not borrow one.** The next deterministic committer takes its own launcher's name here rather than reusing `product-skeleton`, because the point of the field is to say which one wrote the commit. Adding a value is a doctrine change, made here.

Trailer order: `Shukuba:`/`Michi:` → `Role:` → `Surface:` → `Co-Authored-By:` → `Reasoning-Effort:` → `Claude-Session:` → `Skill-Version:` → `Prompt-Version:` → `Workflow-Version:` (the last three non-required and independent, present only when the caller passes `--skill` / `--prompt` / `--workflow`; `Reasoning-Effort:` and `Claude-Session:` are non-required too, and both may appear on a **merge** or an **advance**).

Greppable: `git log --grep "Surface: Cowork"` returns the cowork-committed set.

### Handoff field: `**Surface:**`

Every handoff document under the project's handoffs directory carries a `**Surface:**` field in its header block, on the line immediately after `**Date:**`. Same values as the commit trailer (`Cowork` | `Claude Code` | `Codex` | `Gemini`). Set once at file creation; immutable.

Greppable: `grep -l "Surface: Cowork" system/architect/handoffs/` (adjust path per project).

### Verb spec

- **Commit trailer.** Set by the AI session running `git commit`, once per commit. Never modified afterward.
- **Handoff field.** Set by the handoff author at file creation, once per handoff. Never modified — the surface that authored the file owns the attribution permanently.

### Forward-only

No retroactive changes to historical commits or handoffs. Rule applies forward from 2026-05-05 (codification date). Existing artifacts pre-dating this doctrine carry no `Surface:` field; that's expected and not a hygiene bug. (Same forward-only principle as the `Role:` trailer addition on 2026-04-23.)

Codified 2026-05-05 from cowork-session full setup audit. `Codex` added 2026-06-09. `Grok` added 2026-09-26 and retired 2026-09-29 (the provider was removed) — historical commits keep `Surface: Grok`, but it is not a valid Surface going forward. `Gemini` added 2026-09-28. Any listed surface is valid for any commit; the per-commit choice is recorded in the trailer at commit time, with no default.

---

## Git operations

The message sections above govern what a commit *says*. This section governs the operations that
produce it — the index it is built from and the history it lands on. Both halves are one subject: a
correctly-formatted commit carrying another session's staged work is still a wrong commit.

**This instance's standing condition is concurrency.** Runs are routinely detached, so more than one
writer in a repo is the normal case rather than an edge case. Every rule below follows from that.

### A commit carries what its caller declared, and nothing else

Before committing, `commit_builder.py` reads the staged set and **refuses — making no commit — unless
every staged path is covered** by `--add` ∪ `--rm` ∪ `--staged`. A path is covered by a declaration
equal to it or a directory prefix of it. Renames are read with `--no-renames`, so a rename appears as
its two halves: declare both, or a prefix covering both.

The guard exists because **the index is shared**. Another session working in the same repo stages its
own work there, and without the guard that work rides along inside the next commit anyone makes —
silently, with a SHA reported as success.

**A refusal is information, not an obstacle.** It names the undeclared paths. If a path is not yours,
**stop and look**: another session is live, and forcing past the guard produces exactly the
contaminated commit it exists to prevent. If it is yours — a `git mv` you ran — declare it with
`--staged` and re-run. A refusal leaves `--add`/`--rm` staging in place, so re-running is safe and
idempotent; a refused call is not "nothing happened."

`--take-index` waives the guard for one call. It is for an interactive session that staged by hand and
cannot usefully enumerate the paths. **It is not a way past a refusal you did not expect.**

One hole stays open by design: the milliseconds between the guard's read and the `git commit` itself.
Closing it would mean `git commit-tree`, which bypasses the `commit-msg` hook that verifies every
trailer — a worse trade. So **check `git show --stat` after committing** when another session may be
active.

### Never `cd` into a repo to run git

Do not compose `cd "<repo>" && git add …`, `&& git rm …`, or `&& git commit`. That compound trips the
harness's *changes directory before running git — can execute untrusted hooks* guard and halts the run
mid-commit waiting for a permission prompt. Staging runs inside the builder as `git -C "<repo>" …`,
which does not trip it. One builder call does everything, so there is nothing to stage by hand.

### A write into another repository is plain commands, one call each

A run's own repositories are the two `<CORE>/tools/development_path.py resolve` names: its
`pipeline_worktree` (the instance worktree) and its `code_worktree` (the product worktree). A write
anywhere else, such as copying a file into a host's `about/` and committing it there, is a write into
another repository. A launched run has no one to approve a call. The harness lets such a write through
only when an allow rule matches it; otherwise the harness decides alone, and it refuses writes to a
shared repository. Which allow rules a launched run loads, and from where, is the provider adapter's
in `<CORE>/tools/agent_run.py`, so read them where it says. A change worktree holds none of the
instance's untracked settings, so reading there finds nothing.

**An allow rule matches a call by its literal text.** A call that sets or reads a shell variable, chains
commands with `&&`, `;` or a pipe, carries a heredoc, or runs a script written for the purpose matches
no rule, however exactly the rule names the write inside it. So the write is made as:

- **one call per command.** The copy is one call, the builder's commit another. Inside a launched run
  `<CORE>` resolves to a path that differs from run to run, so the rule for the builder's call
  matches everything before `commit_builder.py` with a wildcard, and literal text after it. The copy's
  source is the run's own file, whose absolute path also differs from run to run, so the copy's rule
  wildcards the source and is literal on the destination;
- **every path a literal.** The other repository is written as its absolute path. A path inside it is
  written relative to it wherever the command takes it that way, as the builder's `--add` does. No
  variable, no substitution;
- **nothing else in the call.** A read-only check, such as the other repository's `git status`, runs
  as its own call before the write, never wrapped around it.

**Undoing the copy is a write too, so it is planned with the others.** The commands include the one that
undoes the copy, also with the allow rule it matches. That is restoring the file's previous content, or
removing the file if the copy created it. Where no allow rule matches a command, the write is not
attempted: the owner adds the rule first.

**A refusal is final for the run.** A refusal here is the harness denying the call, so the call did
not run. A refused write is never retried in another shape or another environment. If the copy landed
and the commit was refused, the run undoes the copy with its planned command. It then checks that the
other repository's status matches the status it read before the copy, and defers or halts as its own
skill says. **A commit the builder or the other repository's hook refuses is a different case:** the
builder has already staged the copy there. The run does not re-run it or unstage by hand. For a write into another repository this overrides the
re-run that § *A commit carries what its caller declared, and nothing else* allows. It stops
the write and reports the other repository's status, deferring or halting as its own skill says. So
does a status that still differs after the undo.

Measured 2026-10-13 on two runs making the same write. Written as two plain calls under allow rules
naming them, the write landed. Written as one script with shell variables, the same write under the same
rules was refused.

### A destructive operation names an explicit SHA

For any destructive or history-rewriting operation — `reset --soft/--mixed/--hard`, `rebase`,
`checkout <ref> -- .`, any force — **name the commit SHA, never a relative ref.** `HEAD~1` is a
position, not an identity: it resolves at run time against whatever HEAD is *then*, so if another
session committed in between it silently names their work. An explicit SHA turns a wrong assumption
into a loud failure instead of a destroyed commit.

**Re-read the state in the same breath as the operation**, not recently. The interval that matters is
seconds; a `git status` from a minute ago is not evidence about the repo now.

**Before rewriting history at all, establish whether another session is live.** Under a live writer,
either do not rewrite, or have the owner hold it.

**A discarded commit is usually recoverable, and recovery comes before anything else.** It survives in
the reflog and object store: confirm with `git reflog` and `git cat-file -t <sha>`, check the working
tree against it so nothing uncommitted is lost, then restore — and verify the restore is
byte-identical rather than assuming it.

**Say so.** A commit destroyed and restored, and any SHA that changed because work was replayed, is
the other session's business. Report it rather than quietly repairing it: a SHA they still hold has
gone stale, and only they can act on that.

### A branch takes `main`'s advance through `advance`

A branch takes `main`'s advance the same way it lands its own work — through one declared operation:
`commit_builder.py --repo <repo> advance --from main (--actor <actor> | --authorizer
<authorizer>) --surface <surface>`. It merges the commit `--from` resolves to into the checked-out
branch as a `--no-ff` merge, always a merge commit — even when the branch has no commits of its own
and could fast-forward. When the branch already holds it, the command exits `0` and commits nothing.

**A conflict leaves the merge in progress, on purpose** — this is a human judgement, not one the
command makes for you. Resolve it, `git add` the resolved paths, and re-run the identical `advance`
command: it recognises the merge already in progress and lands the same commit, naming the commit it
actually merged even if `main` advanced further while the conflict sat open.

**The move is wanted, not forced.** Before this existed, a branch behind `main` had no operation to
reach for and a run improvised — rebasing repeatedly, replaying every commit under a new SHA each
time. That is fixed on its own axis: the marker guard now judges the branch's own edits, not its
distance from `main`'s tip, so a branch behind `main` is not blocked from committing its own work.
Taking the advance is available whenever it is wanted; nothing here requires it before a commit.

**A branch's merge to `main` is owed `main`'s advance first.** Before a `--no-ff` merge lands a branch
on `main`, the branch takes `main`'s advance, and the project's own suite runs green on the branch as
it stands after taking it. The combination that lands on `main` is the branch plus `main`'s advance,
and a verdict measured before the advance was measured on a different tree. The pipeline pays it at
`skills/pm/.claude/skills/tobiishi-seal/SKILL.md` § *Step 1a — Take main's advance, then run the
suite*.

Who may authorize an advance, and how, is § *How the `Role:` value is supplied* above — this section
does not restate it.
