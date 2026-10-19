---
version: "2.6.5"
---

# Setting up an instance

*How a kensaiapp instance goes from a directory on disk to one that can take projects. It is
**five steps**: the instance's files are stamped, its identity and 道 Michi are settled, its doctrine
layer is authored, the bar its own documents are written to is settled, and its experience layer is
authored. Registering a product is the next altitude down and begins at `setting_up_a_project.md`.*

**What this file owns.** The **sequence an instance is set up by** — its steps, in order, with what
runs each and what it produces — plus the ordering rules that fix that shape, the three standing
rules of instance setup (the `experience-visual` → `experience-voice` order, the both-medium split
rule, and that the company name is settled here), and the **marker vocabulary** both halves of the
experience layer write their direction documents in. Every other file points here and does not restate
it; a restatement that disagrees is a bug in the copy, deleted rather than reconciled
(`governance/single_source.md`).

The one deliberate copy is `templates/instance_setup_seed_template.md`, which cannot be a pointer
because it *is* the seed content stamped onto disk. When the sequence below changes, that template
changes in the same commit.

**What it does not own:** where an instance's files sit (`kensaiapp_structure.md`), what a stamper
may create or modify (`setup_scope.md`), how an instance gets its core — standalone or shared
(`shared_core_instance.md`), the sequence a *product* is defined by (`setting_up_a_project.md`), how
a role is added (`adding_a_role.md`), what an instance writing bar may say — that is
`<CORE>/../skills/content-manager/.claude/skills/kensaiapp-writing-bar/prompts/rich.md`, which owns which documents one governs and what
one reaches, and `kensaiapp-writing-bar`, which owns how one is written — or what each experience file contains — that is the two
`experience-*` skills' own, **except the three marker words** below: both halves and every reader
downstream of them have to read one set of those, so this file holds them and the skills do not.

**Where setup stops.** At the point where the instance can take a project: its files exist, its
identity and Michi are declared, the bar its own documents are held to is settled, and its experience
layer states what this instance's products may and may not look and sound like. The test is that **setup produces only artifacts that belong to the
instance** — none of them says anything about any one product. The first artifact that could only
belong to a product is that product's PRD, and that is station 1 of a *project's* journey.

---

## The steps, in order

| # | Step | Runner | Produces |
|---|---|---|---|
| 1 | Stamp | `core/tools/spawn_satellite.py` | the instance's own files — `AGENTS.md`, `kensaiapp.md`, `CLAUDE.md`, `.gitignore`, `system/michi.md`, the seedbed and router stubs, the three `system/doctrine/` files, the role layer, the `.claude/` wiring — the placeholders the steps below fill, **and the setup seed carrying steps 2–4b as a checklist** |
| 2 | Identity + Michi | `kensaiapp-michi` — grouped, so the session reaches it only after `--add-dir` / `/add-dir` on `skills/interactive-product/` | `kensaiapp.md` § "What this is about", `system/michi.md`, and `README.md` reconciled to both |
| 2a | The doctrine layer | the seat itself, reading `<CORE>/prompts/cto_create_domain_doctrine.md`, `cto_create_ai_responsibility.md` and `cto_create_doctrine_structure.md` | the three `system/doctrine/` files stamped by step 1 — the instance's standing domain rules, the AI-responsibility boundaries that project from them, and the meta-layer that classifies both. **One lens per file, CTO posture.** No skill runs this; the seat's own session reads each prompt |
| 2b | Each seat's domain | the seat itself, reading `<CORE>/prompts/declare_loader_domain.md` | § *The domain* of `system/loaders/<role>.md`, for each seat the instance actually uses — what the domain means for that seat's judgment, pointing at `system/doctrine/` for the substance rather than restating it. **Not all-or-nothing:** a seat with no domain-specific judgment keeps the stamped placeholder, which is a stated state. No skill runs this; the seat's own session reads the prompt |
| 3 | The writing bar | `kensaiapp-writing-bar` (Content Manager posture) | `system/doctrine/writing_bar.md` — **the step's output**, and the step is mandatory. Core holds no bar to fall back on, so an instance without this file has nothing binding how its documents read |
| 4a | The visual half | `experience-visual` (CDO posture) | `system/experience/visual_restrictions.md`, `visual_direction.md`, and its cross-medium entries marked in `visual_voice_contract.md` |
| 4b | The verbal half | `experience-voice` (Content Manager posture) | `system/experience/voice_restrictions.md`, `voice_direction.md`, written off the entries 4a marked |

**Runner** names what performs the step, not everything it calls.

**Step 1 stamps the seed that carries the rest.** `spawn_satellite.py` files
`system/nemawashi/<YYYY-MM-DD>_instance-setup.md` from
`templates/instance_setup_seed_template.md` — steps 2 through 4b as a station checklist — so a
new instance's seedbed is never empty and the sequence is never re-typed from memory. Step 1 is not
on it: the stamp is what produced the file.

An item is walked by running the skill named on it, in the posture it names, rooted in that
instance. **When it is ticked depends on whether the item carries a companion.** Steps 2, 2a and 2b
carry none — 2 interviews as it goes, 2a and 2b are prompt-read — so each is ticked when its run has
landed. Steps 3, 4a and 4b run in **rounds**: the run drafts what it can and parks what it could not
settle in a companion open-issues file, the owner answers inline and commits, and the skill is re-run
until a fold leaves nothing open and the run deletes the companion. **The companion's absence is the
done signal, and that is when the item is ticked** — not when the first run lands, which leaves the
document a Draft with its questions still open.

**No 宿場 Shukuba file is opened.** The
instance's `system/shukuba/` is the cross-project router (`kensaiapp_structure.md` § App-level), and
a setup step is one skill run at instance altitude, not several projects pushing on one thing — which
is the difference from a *project's* setup seed, whose stations do each open one
(`setting_up_a_project.md` § Then the journey).

Like a project's, the seed is a **recommendation**: the owner may edit, reorder or delete it, so its
absence in an existing instance is not a gap. The stamper finds it by **slug** across the seedbed's
root, `unpicked/`, `trail/` and `drop/`, so a re-run never stamps a second one and never resurrects one
the instance already walked — or already killed, which is the bin's own reason for being in that list.

**`project-stamp` sits outside this sequence.** It is the first step of *project* setup, owned by
`setting_up_a_project.md`, and it runs against an instance that already exists — once per project,
at any point in the instance's life, not once per instance. `spawn_satellite.py --project` stamps a
first project folder during step 1 as a convenience; that runs the project-altitude step early and
does not move step 4, because what the experience layer must precede is a **design run**, not a
project folder.

## What fixes the order

- **1 before everything.** Step 1 is what makes the instance exist — the repo, the core binding, the
  doctrine and role layers, the files the later steps write into. None of them has anywhere to write
  until it has landed.
- **2 before 4 is the recommendation, not a gate.** Strictly, neither *blocks* the other — neither
  reads the other's output. They are not interchangeable in practice: the experience layer states
  the limits and the direction for how this instance's products look and sound, and that is
  written *against* a settled statement of what the instance is for.
  Taken the other way round, the identity arrives after the limits it should have shaped, and is read
  against them rather than the reverse. It is also the cheaper step by a wide margin, so there is
  little to gain by deferring it.
- **2 before 2a is a gate.** The domain doctrine states the standing rules of the instance's subject,
  and what that subject *is* is what step 2 settles — so `cto_create_domain_doctrine.md` and
  `cto_create_ai_responsibility.md` both halt on a placeholder `kensaiapp.md` § *What this is about* or
  `system/michi.md`. Rules derived from a placeholder are inherited by every project in the instance,
  which is the one place a guess is most expensive to withdraw. The third lens,
  `cto_create_doctrine_structure.md`, classifies what is already on disk rather than deriving from
  identity, so it carries no such halt — it simply has nothing to classify until the other two land.
- **2a before 2b and 2a before 3 are recommendations, not gates**, and each buys something specific.
  Step 2b's whole rule is to point at `system/doctrine/` for the substance rather than restate it, so
  a domain section declared before the substance exists points at a stamp. Step 3's grounds include
  the **domain doctrine**, which 2a's first lens writes, so a bar written first rests on less. Neither
  is blocked: a seat whose global posture governs unchanged is unaffected, and an instance that runs
  step 3 first has a bar grounded in its identity and Michi, which is not nothing. **No halt is added
  to `kensaiapp-writing-bar` for this** — the owner's call, 2026-08-19, taken after a satellite's first bar
  was written over two stubs and re-authored rather than blocked.

  **Only one of 2a's three files is a ground for the bar, and this file does not decide which** —
  `<CORE>/../skills/content-manager/.claude/skills/kensaiapp-writing-bar/prompts/rich.md` enumerates the grounds and owns them. The
  consequence is a re-run rule rather than an ordering one: landing `ai_responsibility.md` or
  `doctrine_structure.md` is not by itself a change in the bar's grounds, so it does not license a
  later run to re-derive a settled bar. That prompt's § *On a re-run — fold, don't re-author* governs
  what may change; **do not infer the answer from this file.**
- **2 before 2b is the same gate, for the same reason.** A seat's domain section is what the
  instance's domain *means for that seat*, so it is derived from the same two files step 2 settles.
  Declared off a placeholder it describes an instance nobody has decided on yet, and every session
  that opens in that seat inherits the guess as posture. The prompt halts there.
- **2b before 3 is a recommendation, not a gate**, and the distinction is worth keeping straight.
  Step 3 does **not** read the overlay: `kensaiapp-writing-bar` names its own grounds, and the domain
  reaches it as the domain doctrine. What 2b changes is the *posture* the
  Content Manager brings to step 3 — the seat's own reading of what the domain demands of words — and
  a bar written with that in hand is better than one written without it. Better, not otherwise
  impossible: an instance that runs step 3 first has not broken anything.
- **2b is per seat, and partial is a finished state.** Nothing requires all fourteen overlays before the
  sequence continues. Declare the seats the instance actually uses; a seat whose global posture
  governs unchanged keeps its placeholder, which the overlay template already calls a stated state.
- **2 before 3 is a gate.** A writing bar is written off what the instance is for — its own Michi
  and its domain doctrine are two of the three grounds a rule in it may rest on, and neither is
  available before step 2 settles them. So **step 3 halts** where `kensaiapp.md` § *What this is about*
  or `system/michi.md` still carries its placeholder: it names the file it found, writes nothing, and
  asks for step 2. There is no bar at core to fall back on, so a bar derived from a placeholder is
  not the cheaper answer — it is a rule every document in the instance is then held to, grounded in
  nothing. The owner invokes step 3 by hand, so the halt is seen.
- **3 before 4.** The writing bar is the bar the experience documents are themselves written to, so it
  exists before the run that writes them. It reaches no further than that: it governs how those two
  authors' sentences read and never what their entries may require — the distinction step 4b's own
  authoring prompt turns on, and the one a run that collapses the two gets wrong by writing house
  style into the products' fence.
- **4a before 4b is fixed**, and it is the first rule below.

---

## The three rules

### 1. `experience-visual` runs before `experience-voice`

An **ordered pair**, not two independent runs. `experience-visual` runs first and marks the entries
that cross into the verbal medium; `experience-voice` reads those marks and writes the verbal halves.
Anything voice-originated that crosses back gets a second visual pass.

The order is what makes the second author's job total: without the first run's marks, "did the author
remember?" returns to the loop, and a missing entry is indistinguishable from a deliberate
single-medium one. The marks are carried by `visual_voice_contract.md`, which is a **handoff, not a
companion**: a companion is ephemeral and its absence is a done signal, while a handoff persists
and its absence is a defect.

### 2. The both-medium split rule

> **A limit that binds both mediums is written twice — as two entries, one in each restrictions file,
> each stated in its own medium's terms. It is never filed once and looked for in the other place.**

The two entries are **not copies of one another**. *No celebratory animation on an executed trade*
and *no celebratory wording on an executed trade* are two different limits that share an origin, and
`governance/single_source.md` governs one **fact** having one owner — not one origin having one
sentence. Each entry carries the shared slug, so neither is relaxed without the other being seen.

The split is what lets a product be bound by one medium and not the other: a product that owns no
rendering surface is bound by the verbal limits in full while the visual ones are moot for it. Under
one file it is handed a document most of which does not apply to it and told to obey the parts that
do.

**Crossing is the fence's, and a direction document carries none.** This rule is written about limits
throughout, and that is its whole reach: a value or a line in `visual_direction.md` or
`voice_direction.md` has no counterpart in the other medium to share a slug with, carries no reach,
and gets no row in `visual_voice_contract.md` — whose **Kind** column admits `limit` and nothing
else. What a direction value carries instead is a marker from § The marker vocabulary, and that
marker says what a **product** inherits, not which medium the value reaches; the two are different
facts and neither stands in for the other.

Where an author finds direction in one medium that would bind the other, the binding half is not
direction: it is a limit, and it is written as one in that medium's restrictions document — where it
takes its slug, its **Reaches** and its row, under this rule like any other. That is what catches a
crossing, and nothing is owed to the contract until that limit exists. Both halves author under this
paragraph and neither restates it.

### 3. The company name is settled at instance setup

It belongs to the **instance**, not to any product: it does not change per product, so it is settled
once — at step 2, with the rest of the instance's identity — and never restated per product. A
product document that carries its own copy is exactly the copy `governance/single_source.md` deletes
rather than reconciles.

---

## The marker vocabulary

*One set of words, for both halves of the experience layer and for everything that reads what they
write.*

A value or a line in either **direction** document — `visual_direction.md`, `voice_direction.md` —
carries exactly one of:

- **`binds`** — every product under this instance takes this one, and a product's own design or
  content run may not replace it.
- **`may be replaced`** — the product starts here and may deliberately choose otherwise.
- **no marker** — each product decides for itself.

They are stated here and nowhere else. Both `experience-*` authoring prompts read them as they
write, and so does whatever later reads an instance's direction documents to author one product's
own — so the vocabulary is a fact with readers in three places and no natural home among them. Left
in the two prompts, it held only because both happened to write the same three words, and a rename
in one half would have been invisible to the other: the copy `governance/single_source.md` deletes
rather than reconciles.

**What a marker costs, and when one is worth its cost, is each half's own authoring prompt.** This
file owns which words exist and what each means; it says nothing about when to reach for one.
