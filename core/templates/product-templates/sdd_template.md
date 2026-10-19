---
version: "5.1.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# SDD — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = open issues or choices to confirm remain (open-issues file present).
     Settled = nothing left for the owner to answer and no open technical question — the done
       signal, and the state a finished SDD carries; the open-issues file is gone.
     Locked = ratified as the source of truth. -->
**Owner:** CTO — writes every part; the CPO and the CDO decide the parts the lane table names, through `SDD_open_issues.md` items carrying their `Seat:`
**Version:** <n> — <one-line note on what this revision changed>
**Inputs read:** PRD <status> · SRS <status> · UXD <status>
<!-- `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO
     STATE. `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every
     document in the chain rather than this one — write the line from there. **Every input this
     revision read, not only the unsettled ones**: a line that appears only when something was
     `Draft` is indistinguishable from a run that forgot it. -->

> The SDD is the technical **how**, and it ends in a **cut**. It states the architecture the rest of
> the system builds against — derived from the PRD (the *what and why*), the SRS (the system-level
> *what*) and the UXD (the experience) — and it then cuts that architecture into an ordered set of
> **slices, each of which delivers something on its own**. A slice is not itself a unit of work:
> the Principal PM draws one and cuts it into **one or more** 根回し Nemawashi seeds. § 8 states how
> a slice's fields land in them; how many seeds, when a slice is drawn, and what a seed's stations
> reach into are all `<CORE>/roles/loaders/principal_pm_global.md`'s.
>
> **The cut is the point of the document.** Part B states the method — the steps that turn a design
> into contained slices — and Part C is what those steps produce. A reader who needs to know how to
> plan opens § 5. A reader who needs to know what was planned opens § 6.
>
> It is a **living document**, updated in place with versioning: bump the Version line above on each
> material change. When the build contradicts the cut, § 10 records the contradiction before the cut
> is redrawn.
>
> Omit a section only when it genuinely does not apply; do not pad one to fill it.

## Who decides what

<The CTO writes every part of this document. The table below does not say who writes a part; it says
whose call the part is. A part the CPO or the CDO decides is still drafted by the CTO, best-effort,
from the inputs and any answers already in hand. A call that the inputs leave unsettled, or that the
draft needs that seat to confirm, reaches the document through an `SDD_open_issues.md` item carrying
`- **Seat:** cpo` or `- **Seat:** cdo`, and the answer is folded in on the skill's next round. The
table is the standing split; leave it as written. A draft that decides another seat's column on the
CTO's own judgment has found an open issue, not a mandate.>

**The rule every row follows:** a part is decided by the seat that would have to be overruled for it
to be wrong. Where two seats would each be overruled about different clauses of one part, the part is
split by named clause and each clause names its seat. No part is shared — a shared row is an open
question in the shape of an answer.

| Part | Decided by |
|---|---|
| § 1 What this design must achieve | **CPO** |
| § 2 The shape, and what it was chosen over | **CTO** |
| § 3 The parts, and the seams between them | **CTO** |
| § 4 — runtime and deployment shape, instrumentation and failure visibility, identity, authorization, data protection | **CTO** |
| § 4 — the experience conditions the UXD binds on every surface | **CDO** |
| § 5 step 1 — the entries themselves | **CPO** |
| § 5 step 1 — that each entry is genuinely observable, not an architecture box | **CDO** |
| § 5 step 2 Strike the fragments | **CPO** |
| § 5 step 3 Separate dependency from preference | **CTO** |
| § 5 step 4 Size each one against a reached-when | **CPO** |
| § 5 step 5 Order by what each slice falsifies | **CTO** |
| § 6 *Slug*, *Delivers*, *Moves toward*, *Not in this slice* | **CPO** |
| § 6 *Rests on*, *Why here in the order* | **CTO** |
| § 6 *Reached when* — the behaviour observable in the running product | **CDO** |
| § 6 *Reached when* — the command and its result, and the artifact that must exist | **CTO** |
| § 6 *Traces to* — the PRD section | **CPO** |
| § 6 *Traces to* — the SRS `FR-n` / `NFR-n` / `DR-n` / `C-n` | **CTO** |
| § 6 *Traces to* — the UXD section | **CDO** |
| § 7 The order, and why | **CTO** |
| § 9 Trade-offs taken | **CTO** |
| § 10 Re-cut record | the seat whose ground moved — see below |
| § 11 Technical risks | **CTO** |
| § 12 — the PRD boundary | **CPO** |
| § 12 — the SRS boundary, and the downstream boundary | **CTO** |
| § 12 — the UXD boundary | **CDO** |
| *Open Questions* | **CTO** |

§ 8 is decided by nobody — it is left as written. *SDD Review Notes* names the seat whose call it was on every entry.

**§ 10 has no standing deciding seat, deliberately.** A re-cut is written when a cut meets a reality
that contradicts it, and the trigger says whose ground moved: a *Reached when* that cannot be met
belongs to whichever half failed; a slice that turned out to be a fragment is the CPO's, by § 5
step 2; no slice left that can be started is the CTO's, by step 3; an upstream change belongs to the
seat that owns that document. The CTO writes the record, and it names that seat as the one whose
call moved. A standing decider here would have one seat recording another's error as its own
verdict, which is how a correction stops being distinguishable from a drift.

**What each seat must not decide:** the CTO, whether a slice is worth delivering — that is product
value. The CPO, the architecture style, the data model and the seams. The CDO, product scope and the
technical order.

---

# Part A — What is being cut

<Part A is the design, kept only as far as the cut is made from it. The SRS holds the requirements
and the UXD holds the experience; neither is restated here. A section of Part A that no slice in
§ 6 rests on is padding — cut it.>

## 1. What this design must achieve

<One short section. The product intent this architecture serves, the terminus it is scoped against —
the project's 上がり Agari — and the constraints that were fixed before any choice below was made.
Name the PRD goals and the SRS requirements that bound the design; do not re-list them.>

## 2. The shape, and what it was chosen over

<The architecture style, and the alternatives weighed against it. A shape presented with no
alternative has not been chosen, only assumed.

For the shape taken and each one rejected, state **when it is the right call** and **when it is the
wrong one**, then which side this product falls on and why. Close with what it would take to undo
this choice if it turns out wrong — a shape that is cheap to reverse and one that is not are
different decisions, and the difference is what a reader needs from this section.>

| Shape | Right when | Wrong when | Taken? |
|---|---|---|---|
| <the one taken> | <...> | <...> | **yes** — <the reason, in a clause> |
| <an alternative> | <...> | <...> | no — <what ruled it out> |

## 3. The parts, and the seams between them

<The components the system is made of, what each owns, and — as load-bearing — what each must not
own. Then the seams: every place two parts meet, what crosses, and which side owns the contract.
A seam with no named owner is where the design will be argued about later.

**These tables are read by a tool, not only by a person.** The skeleton launcher lays out the
product before any code exists, and it does that by reading the parts and units tables with nothing
in the loop to interpret them. That is why the shapes below are fixed rather than left to the run:
prose carries the same content, but no two documents shape it the same way, and a reader that has to
interpret gives a different answer twice over the same settled text. Leave the tables as written.>

**The parts.**

| Part | Lives in | Owns | Must not own |
|---|---|---|---|
| `<slug>` | `<the module, package or crate this part belongs to>` | <what it owns> | <what it must not own> |

<**Part** is a **slug**, and what makes one usable is not cosmetic. **Lowercase letters and digits,
single hyphens between them, and nothing else**, written in backticks — no capital, no space, no
underscore, no dot, and no `__PROJECT__`. The skeleton launcher validates this machine identifier and
uses it to relate the part to its unit; it does not infer a language-specific file or directory from
the slug. Nothing in this column is substituted, and a cell of any other shape is refused.

It names *the thing* — `connect-unit`, `cache-reader`, `session-store` — never its position in the
list. A positional label (`P-1`, `C-3`) is what a document reaches for on its own and it fails twice
over: it cannot become a directory name, and renumbering the list silently invalidates every
reference to it. A slug survives a renumbering because it never encoded the number. **That half is
the author's to keep, because no tool can check it:** the launcher refuses `P-1` for its capital, and
a lowercase `p-1` is a well-formed slug it has no grounds to refuse.

**A part slug is not a slice slug.** § 6 gives every slice one too, and § 8's map from a slice's
fields to a seed's sections is keyed on *those*. The two name different kinds of thing — a part is a
component that goes on existing, a slice is a unit of work that lands once and is done — and they
must never be spelled the same. Where a slice delivers one part, give them different words rather
than letting one string mean both; § 8 cannot tell them apart, and neither can a reader six weeks
later.

**Lives in** is the module, package or crate the part belongs to, **written as a bare path and
nothing else** — `app-core`, `src/domain`, `crates/reader`. One value, relative to the product
root, no leading `/` and no `..` in it. Not a sentence, not two options, no backticks, no bold, no
trailing clause: the units table repeats this value verbatim as its key, so prose or markup prevents
the two tables from describing the same structure. Where a part's placement genuinely needs
explaining, the explanation goes in *Owns* and the cell stays a path. Leave the cell empty for a part
that sits at the product root. This is the one column in which `__PROJECT__` is substituted, for the
package named after the product itself.

It is the column most easily left
out, because a human reader infers it from context a script does not have — and without it nothing
knows where a part's directory goes. On a product with more than one language it carries more still:
it is what says which language's layout this part takes.

**A value here is a unit, and the parts that share it are inside it.** Six parts reading
`crates/reader` are six modules of one crate, not six directories beneath it. Write the unit the
part belongs to and stop: the slug says which piece of that unit it is, and the units table below
says what the unit itself is.>

**The units.** One row per *distinct* value in `Lives in` above — no more, no fewer.

| Unit | Language | Kind |
|---|---|---|
| `<the Lives in value, verbatim>` | `<one of the card's Languages:, or none>` | `<crate \| package \| module root \| directory>` |

<**This table exists because `Lives in` alone cannot be built from.** A path says where something
goes; it does not say what it *is*. `crates/reader`, `app-ui` and `checks` are indistinguishable as
strings, and a Rust crate, a TypeScript package and a plain harness directory need three different
things created — a manifest and a `src/`, a `package.json` and its config, and an empty directory
respectively. Measured on a real product, 2026-09-03: with only the paths to read, the skeleton
launcher made all four of them bare directories, put the language frames somewhere else entirely,
and produced a tree whose own test command compiled nothing the design named. The design was
correct and unbuildable at the same time, which is the gap this table closes.

**Language** is one of the values on the project card's `Languages:` line, spelled the same way, or
`none` for a unit no packet governs — a fixtures folder, a docs tree. A shell harness is NOT
that case: the shell packet binds it, so it names Shell and takes `directory` for its Kind. A language
here that the card does not declare is an error in one of the two files, and which one is the
author's to decide.

**Kind** takes the word that language's own packet uses for a buildable unit —
`<CORE>/doctrine/engineering/languages/<language>/layout.md`. Rust's § *A multi-crate product* is
explicit that "workspace members live under `crates/`, one directory per member", so a Rust `crate`
is `crates/<name>` and never a bare name at the product root. Read the packet and write the row
against it, not against what reads naturally: a unit placed where its language does not look is
legal as a path and invisible to the toolchain.

**Kind is decided by what has to be created, not by whether a language is attached.** A `crate` or
`package` gets its language's frame; a `module root` — a unit that holds parts but is not itself
built, a directory inside a crate or package that the parts live under — gets nothing of its own;
and a `directory` gets exactly itself.

So **a unit may carry a language and still be a `directory`**. A shell harness is the standing case:
the shell packet's conventions, testing and quality-gate files all govern those scripts, so the
Language column names Shell — writing `none` would tell a reader no packet binds them, which is
false — and the Kind is `directory`, because Shell ships no `layout.md`, has no word for a buildable
unit, and the harness produces no artifact. Language says which packet governs the unit; Kind says
what the skeleton creates for it. They are answered separately and a unit that needs nothing built
takes `directory` whichever language owns it.

**Where a language's frame lands is this table's to say.** A product whose renderer lives in `app-ui`
says so in the row for `app-ui`, and no other file needs telling. Leaving a unit off on the
assumption that a card field carries its placement is how a frame ends up at the product root while
the design says otherwise.>

**The seams.** Each names what crosses and which side owns the contract.

| Seam | What crosses | Owner of the contract |
|---|---|---|
| <a short id, e.g. `SM-1`> <part> ↔ <part> | <what crosses, in both directions where both carry something> | <which side owns the contract> |

<Two tables, not one: merging them loses the seam's owner, and the unowned seam is the thing this
section already says arguments start over.>

<What the system holds belongs here too, in prose below the tables: the entities, their key fields
and the relationships that matter, at the design level rather than the physical schema. Trace each to
the SRS `DR-n` it realizes.>

## 4. What every slice inherits

<The conditions that hold across the whole build, whichever slice is being worked — written as
conditions rather than as chapters, because every slice in § 6 is checked against all of them.

Cover at least: the runtime and deployment shape; what is instrumented and what makes a failure
visible; how identity, authorization and data protection are handled; and the experience conditions
the UXD binds on every surface. Align each with the SRS non-functional requirement or the UXD
section it serves. State the conditions that bind this product and drop the ones that do not.

**This section and `docs/nfdr.md` are two constraint stores, and the relation is fixed.** § 4 is the
**authoring surface** — a condition is stated here first, in the design conversation, traced to the
SRS requirement it serves. The NFDR is the **enforcement store** — the consolidated, checkable form
the delivery loop reads, each entry tracing back to the § 4 condition or SRS requirement it realizes.
Where the two disagree, **the § 4 statement wins and the NFDR entry is re-derived**, because that is
the direction every derivation in this chain already runs: downstream is rebuilt from upstream, never
the reverse. Without this rule the same constraint can sit in both, disagree with itself, and give a
reader no way to tell which is stale.>

---

# Part B — How to cut it

## 5. The cut, step by step

<This section is the method. It is written once, here, so that § 6 carries slices and no method.
Leave it as written unless this product's cut genuinely departs from it — and if it does, say so
here, with the reason.>

### Step 1 — List what becomes observably different

Before any slicing, list the things that would be **observably different** about the running product
between where it is now and its Agari. Write each as one sentence in the form *after this, <someone>
can <do something they could not>*.

The list is made from behaviour, never from the architecture's boxes. "Set up the database", "build
the API layer" and "add the design system" are parts of the shape, not entries on this list. If an
entry cannot be finished in that sentence form, it is not yet a candidate.

### Step 2 — Strike the fragments

Strike every entry whose only value is that a later entry needs it, and fold it into the entry that
gives it value. A cut that needs a later cut to be worth anything is not a slice but a fragment of
one — `<CORE>/roles/loaders/principal_pm_global.md` owns that rule, and this step is where it is
applied to a design rather than to a program.

This is the step that catches infrastructure built ahead of its subject. A checker with nothing to
check is not a step forward, however finished it looks.

### Step 3 — Separate dependency from preference

For every remaining pair, ask **can the later one be built at all without the earlier one?** — not
whether building it first would be tidier. A stated order is often a preference wearing a
dependency's clothes, and the two behave differently the moment the build slips: a real dependency
blocks, a preference reorders for free.

Record each answer as a typed edge in § 7, with the reason on the same row. An edge with no reason
is a preference that has been written down as a fact.

### Step 4 — Size each one against a reached-when

A slice is the right size when someone who **did not build it** can check it is finished from the
outside. Write the *Reached when* before deciding the slice is settled — the size follows the
checkable bar, not the other way round.

- **Too broad** when a plausible intermediate result could change the slice's direction or its
  acceptance. Two answers are hiding inside one slice.
- **Too narrow** when its result cannot change what happens next. Nothing is learned by finishing
  it, so it is a task inside a slice rather than a slice.

Cut where the decision changes, not where the size is convenient.

### Step 5 — Order by what each slice falsifies

**The first slice is the smallest reversible one that proves the shape** — not the foundation the
rest will need. A first slice sized to the whole architecture cannot be wrong cheaply, and being
wrong cheaply is the one thing a first slice is for.

After the first, every slice's place in the order carries a reason: what an earlier slice must have
settled for it, or what it de-risks for the later ones. A slice that could sit anywhere in the order
says so plainly; a number is not a reason.

### The four tests one slice passes

<Apply all four to every block in § 6. A slice that fails one is not yet a slice.>

1. **It delivers something observable.** After it, something works that did not work before, and a
   person can watch it happen.
2. **Its inputs already exist when it starts.** Nothing it needs is still being built beside it.
3. **It states what it does not include** — the adjacent work a reader would assume is inside, and
   the slice that owns that instead.
4. **Its place in the order is a reason**, not a number.

### Six cuts that look like slices and are not

<Hunt these by name before § 6 is settled. The first five are the Principal PM's, at
`<CORE>/roles/loaders/principal_pm_global.md` § *You are not a scheduler*, applied here to a design;
the sixth is what a plan drifts into when it has a monitor in it.>

- **A dependency stated as an ordering preference** — a fact and a habit are not the same thing.
- **A slice whose only value is that a later slice needs it.**
- **A slice no Agari claims.**
- **A slice no project would own any of** — which project owns which seed is settled at the cut,
  not here, and a slice may well split across two.
- **A milestone that only restates its last task's completion.**
- **A slice whose completion evidence is that someone kept watching.** Observation is not delivery;
  a poll that reports no change keeps a plan alive without advancing it
  (`huangruiteng/loopx`, `skills/loopx-pr-program/SKILL.md`: "Quiet monitor polls keep liveness but
  do not count as delivery progress").

---

# Part C — The cut

## 6. The slices

<One block per slice, in the order they are to be built. Number them `S-1`, `S-2`, … and refer to a
slice by its slug everywhere else in this document. Copy the block below once per slice.>

### S-<n> — <what it delivers, in a phrase>

- **Slug:** `<kebab-case-slug>` — how this slice is named everywhere else in this document, and
  what each seed cut from it records as its origin (§ 8). Not a seed filename: those are named at
  the cut.
- **Delivers:** <one sentence, in step 1's form. What works after this slice that did not before,
  stated as something a person can watch happen.>
- **Reached when:** <conditions someone who did not build the slice can check: the behaviour
  observable in the running product, the command and the result it must produce, the artifact that
  must exist. A condition that turns on something unobservable is a defect in the condition, not a
  judgment to make later.>
- **Rests on:** <the sections of this SDD this slice realizes, and the slices that must land first,
  by slug.>
- **Traces to:** <PRD section; SRS `FR-n` / `NFR-n` / `DR-n` / `C-n`; UXD section.>
- **Moves toward:** <the 上がり Agari this slice advances. A slice that advances none is a finding,
  not a rounding error.>
- **Not in this slice:** <the adjacent work a reader will assume is included, and the slice slug
  that owns it instead.>
- **Why here in the order:** <what an earlier slice must have settled for this one, or what this one
  de-risks for the later ones. Say plainly that it could sit anywhere, if it could.>

<!-- repeat as S-2, S-3, … one block per slice -->

## 7. The order, and why

<The dependency edges between the slices in § 6, one row each. This table is a **projection of
§ 6, not a second store**: when the two disagree, § 6 is right and this table is stale
(`huangruiteng/loopx`, `docs/reference/protocols/task-graph-projection-v0.md` — the graph is
read-only over state that lives elsewhere).

Use these relations and no others. `depends_on` is the only one that constrains the build order;
the rest describe the cut without ordering it.>

| From | Relation | To | Why — the reason this holds |
|---|---|---|---|
| `<slug>` | `depends_on` | `<slug>` | <what the later one cannot be built without> |
| `<slug>` | `validates` | `<slug>` | <what it proves about the earlier slice> |
| `<slug>` | `hands_off_to` | `<slug>` | <what crosses, and in what form> |
| `<slug>` | `supersedes` | `<slug>` | <what the earlier slice stops being needed for> |

<A row with an empty *Why* is step 3 left undone. Delete it, or find the reason.>

## 8. Slice → seeds

<Stated once, here, so that cutting a slice is reading rather than re-deriving. A slice is **not a
seed**: the Principal PM draws one and cuts it into **one or more** 根回し Nemawashi seeds, authored
to `<CORE>/templates/journey-templates/nemawashi_template.md`. How many, and when a slice is drawn
at all, are that seat's — `<CORE>/roles/loaders/principal_pm_global.md` owns the round, and this
section neither restates it nor constrains it. What this section owns is the other half:
where a slice's fields land once the cut is made. Leave this table as written.>

<Because a slice can yield several seeds, a field does one of three things, and the third column
says which. **Repeats** — the fact binds every seed cut from the slice, and each carries its own
copy, because each is read cold with no sibling beside it. **Divides** — the slice's whole is split
and each seed states only its share; copied whole instead, every seed would claim the slice's full
delivery. **Stays here** — a fact about this slice's place among slices, which no seed carries.>

| Slice field | Seed section | Across the seeds |
|---|---|---|
| **Slug** | recorded in `## Source` as the slice this seed came from | repeats |
| **Delivers** | `## What it is` | divides — each share must be worth something on its own, or it is a fragment (§ 5 step 2) |
| **Rests on**, the SDD sections it realizes | `## What it is` | repeats |
| **Moves toward** | `## What it is` | repeats — a seed that advances no Agari is a finding |
| **Traces to**, and this SDD's path | `## Source` | repeats, narrowed to what the seed's share touches |
| **Rests on**, the slices it names by slug | `## Relation to existing work` | repeats — the order *among* these seeds is decided at the cut and is not in this SDD |
| **Not in this slice** | `## Out (later / elsewhere)` | repeats, and grows — each seed also fences off its siblings' shares, naming the seed that owns each |
| **Reached when** | the bar each 宿場 Shukuba opened from that seed is closed against | divides — the slice's own bar is met when the last of its seeds closes |
| **Why here in the order** | — | stays here |

**A seed's `## Stations — dynamic checklist` is not in this table, and that is a decision.** No
field of a slice maps to it: the route a seed is walked by is the PM's, drawn at the cut and after
it, and nothing in this document proposes one. An SDD that named the change units a slice should
break into would be writing the PM's checklist under another name — and a route written by the seat
that designed the thing anchors the seat that has to walk it, however plainly it is labelled a
suggestion. The owner's call, 2026-08-26.

**No field lands in exactly one of the seeds.** Where one looks as though it should — a dependency
in *Rests on* that only one seed turns out to consume — the edge in § 7 was drawn coarser than the
work it constrains. That is a finding about § 7, not a call to be made at the cut.

**A slice that cannot fill one of these fields is not yet a slice — go back to § 5.** The rule
survives the cut being one-to-many and binds harder for it: an unfillable field is no longer one gap
in one seed, it is the same gap in every seed the slice yields. A slice whose *Delivers* is vague
cannot be divided into shares that each stand on their own, and a slice with no fence leaves every
one of its seeds without one.

---

# Part D — What the cut costs, and what it cannot reach

## 9. Trade-offs taken

<What this design gives up, one line each, with what it buys. A design with no stated cost has not
been weighed. For each, say what undoing it would take if it turned out wrong.>

- **TO-1:** <what is given up> — *buys* <what it buys>; *undoing it costs* <the reversal>.

## 10. Re-cut record

<A cut meets a reality that contradicts it, and the contradiction is recorded **before** the cut is
redrawn. A cut silently redrawn leaves the next reader unable to tell a correction from a drift.
Shape borrowed from `huangruiteng/loopx`,
`docs/reference/protocols/goal-vision-replan-contract-v0.md` § *Path Delta*.

Re-cut when, and only when, one of these holds: a slice's *Reached when* cannot be met as written; a
slice turned out to be a fragment once its neighbour landed; no slice is left that can be started;
or the PRD, SRS or UXD changed upstream. Finishing a slice is not a trigger.

Omit this section until the first re-cut. An empty heading reads as a cut already in doubt.

**A re-cut that moves the shape is also an ADR.** This section is the home for *cut* history — the
slices are this document's own and no other record holds them, and that does not change. But an
`RC-n` whose *Changed* line moves § 2's shape or § 3's seams is an architecturally significant
reversal, and the decision log is append-only: it lands there as a **new record superseding** the one
it reverses, in addition to the row here. Without that, shape history has two homes and the log
silently misses every reversal made mid-build.>

### RC-<n> — <date> — <what was re-cut, in a phrase>

- **Prior assumption:** <what the cut assumed when it was made>
- **Observed reality:** <what was seen instead, cited — the run, the commit, the file>
- **Retained:** <what still holds, and is deliberately not being redrawn>
- **Changed:** <what the cut now says instead>
- **Stopped:** <what is no longer being attempted at all>
- **Still unresolved:** <the question this re-cut did not answer>

## 11. Technical risks

<The risks this design carries, each with what would make it real and what the design does about it.
A risk with no trigger and no response is an observation.>

- **R-1:** <the risk> — *shows up as* <the observable trigger>; *response* <what the design does>.

## 12. What this design is not

<The boundaries, so a reader does not look here for something this document never held.

Above: it never changes product goals or scope (the PRD), system requirements (the SRS), or the
experience (the UXD). A gap in any of them is an open issue in the companion, not a rewrite here.

Below: it authors no ADR. The architecturally-significant decisions are **surfaced**; the Principal
Architect records them, and this SDD references those ADRs once they exist. It designs no individual
change — that is the delivery-tier Architect's `change_design.md`, one change at a time against the
system defined here.

**What "surfaced" means, exactly:** the Principal Architect reads three surfaces of this document and
no fourth — **§ 2's shape table** (each alternative's *right when / wrong when / taken?* row),
**§ 9's trade-offs**, and **the SDD Review Notes**. That is the set, not a sample: a run that has
written those three has surfaced everything the recorder will look for. What earns a record, how one
is written, and what to do with a decision visible in the design but argued in none of the three are
`<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md`'s, not this section's.>

---

## SDD Review Notes

<This section is the SDD's **creation trail** — every load-bearing element carries a written *why*.
An element derived from an upstream document carries its why inline, as its *Traces to* tag;
**everything the upstream documents did not settle carries its why here**, with its reason: an
invented value, an owner's answer folded from the open-issues file, a best-effort choice the CTO
drafted for a call that is another seat's, or a place where a contradiction between the SRS and the UXD was resolved
the SDD's own way.

On a revision **or a recreate**, **every change to already-settled content carries the legitimate
reason that authorized it** — an owner answer or directive, or an upstream change. Settled content
is all of it: the shape, the seams, the cut, and the existing wording of these notes. A change with
no findable legitimate reason is a bug and should not appear in the SDD at all.

A genuine product-intent gap is *not* recorded here — it goes to the open-issues companion for the
owner. Once the owner answers, capture the answer here, because the companion is deleted when the
round finishes clean and this trail is the durable provenance.

Each note names the seat whose call it was and its relation to the upstream documents: *added* (the
SDD states something they do not) or *changed* (it departs from what they say).>

- **RN-1:** *(CTO | CPO | CDO)* *(added | changed)* <what departed from or went beyond the upstream
  documents> — *because* <reason> *(re: § n / `S-<slug>`; source: <PRD section | SRS `FR-n` | UXD section>)*

---

## Open Questions

<A technical question this SDD leaves standing — recorded so a reader does not mistake silence for
an answer.

**This section is not the companion, and never a copy of it.** Anything awaiting the owner lives in
`SDD_open_issues.md` alone, and that file's **absence is the done signal**. An item written in both
has two homes and only one of them says when it is finished.

What belongs here is a question this SDD cannot close and is **not** asking the owner to close: one
that resolves downstream — in a slice, in a spike, or against a system that does not exist yet.

Omit this section entirely when there is nothing in it. An empty heading reads as an unanswered
question.>

- [OPEN: <the question, and what would settle it>]
