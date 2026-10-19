# product-design eval fixtures

Read-only inputs the eval prompts (`../evals.json`) point at. A `skill-evals` run **reads** these;
the with-skill config writes its output into a sandboxed workspace, so the fixtures stay clean.

**All eval annotations live here, never inside an ingested file.** The grader and the runme agent
read the fixture files *whole* — a comment inside `PRD.md` / `UXD.md` / `DESIGN.md` /
`DESIGN_open_issues.md` / `src/**` that reveals the expected behavior would let a blind baseline
pass on the instruction rather than the skill. So the fixtures carry only product content (plus a
benign path-resolution note in each `project.md`); the "what each case exercises" notes are all in
this file.

Paths are **repo-relative** (publish-safe — no machine-absolute path). `product-design` reads a
relative `Product path:` as an in-repo product and resolves `<Product path>/docs/DESIGN.md` +
`<Product path>/docs/DESIGN_open_issues.md`.

**A caveat that binds every with-skill result read from these evals today:** the skill's fat
authoring prompt (`prompts/rich.md`, the v3 plan's task 12) is authored in
a later station. Until it lands, a with-skill run works from the skill and the two templates
alone, so these evals grade the **skill-owned mechanics** — posture, the loop files and their
names, the buckets and slots, the trail, the done signal, the format's stamped shape — not the
prompt's authoring doctrine. Re-run after task 12 before reading the numbers as the stack's.

## The fixture shape

product-design needs the input state a real definition chain leaves behind:

- `docs/PRD.md` — `Status: Settled` (secondary input — audience and tone).
- `docs/UXD.md` — `Status: Settled`, carrying **§ 9 Design-System Direction** (the seed: the
  system call and the constraints, no token values) and **§ 8 Accessibility Requirements** (the
  bar that binds the values). The UXD is the primary input: the skill halts without it.
- `docs/trail/uxd/cycle-1.md` — the UXD's own answered companion, trailed; part of the docs
  listing the run is entitled to.
- `src/styles/tokens.css` (trimly pair only) — **the product's own source**, the evidence base:
  CSS custom properties for palette/type/radius, component rules using them, and a closing
  comment noting the ad-hoc spacing steps. Deliberately **partial**: body type sizes only —
  nothing above 14px exists anywhere in the source, so the heading scale cannot be grounded and
  must surface rather than be invented.

**No `agari.md` in any fixture** — deliberate. Unlike `product-uxd`, this skill does not list the
terminus as an input: the design language's inputs are the UXD, the source, brand assets, and the
PRD (the fat prompt's § Inputs), and the scope boundary was already applied one document up.

**The eval prompts never say what the companion or trail should look like.** They name the
binding and say to read the product input; the file names, buckets, slots, and done signal are
the skill's own contract, which is what keeps the assertions discriminating.

## `trimly/` — case 1 (first authoring, evidence-rich)

A team link-shortener (the sibling skills' eval product, carried over) that already ships: the
UXD directs **built-from-primitives** with constraints (AA on table surfaces, tabular numerals,
density-first, stillness), and `src/styles/tokens.css` holds the live palette, the two body type
sizes, and the single 6px radius.

- **Case 1 `first-authoring-evidence-grounded`** — the evidence gate's happy path plus the
  format's stamped shape: values read from the source and cited by path; the eight canonical
  sections in order with **no `## Themes`**; frontmatter tokens with `colors.primary`; `{path}`
  references that resolve (broken-ref is the format's one hard error); at least one component
  defining a **colour pair** (the format's contrast check fires only on pairs); a three-bucket
  companion under the exact name `DESIGN_open_issues.md`; `Status: Draft`, since the heading
  scale has no source evidence by design.

## `briefbox/` — case 2 (greenfield inversion)

A one-page editorial signup surface. **No `src/`, no brand assets** — the UXD says so plainly.
With nothing to observe, nearly every value is a taste call.

- **Case 2 `greenfield-taste-routing`** — the anti-default discipline inverted: the companion's
  *Choices to confirm* bucket is the big one (≥ 3 items, each with `Grounds` and
  `Confirm or override` slots, at least one admitting there is no evidence), a category that
  genuinely does not apply is declared in `omitted:` **and** confirmed through the companion with
  its own `Confirm or override` slot, and the document stays `Draft` with the companion present
  rather than shipping a confident invented system.

## `trimly-reentry/` — case 3 (loop re-entry and close)

trimly plus an existing `docs/DESIGN.md` (Version 1, `Draft` — the shipped blue drafted as a
choice to confirm, the heading scale surfaced as an open issue) and an already-**answered**
`docs/DESIGN_open_issues.md` (heading scale answered: 24/18 semibold over 14 body; the accent
**overridden** to teal `#0F766E`).

- **Case 3 `reentry-fold-and-close`** — every slot is answered, so this run is the close: it
  retires the answered companion whole to `docs/trail/design/cycle-1.md`, folds the owner's
  values in (primary reads `#0F766E`, the two heading levels exist), records the owner
  provenance in the Review Notes citing the trail path, stamps `Status: Settled`, and
  **removes** `DESIGN_open_issues.md` — its absence is the done signal.

  Deliberately not graded here, same reasoning as the sibling set: **no cycle-numbering rule**
  (the fixture ships no `docs/trail/design/`, so `cycle-1` is the unconditional answer), and the
  **pre-existing Review Notes are exempt** from the trail-citation assertion (RN-1/RN-2 cite
  `src/styles/tokens.css` and the stability rule requires reproducing them). And read the
  with-skill-vs-baseline delta on this case with suspicion: the fixture hands the agent a
  Version-1 DESIGN.md already in the skill's idiom, so a strong baseline can continue it —
  discrimination belongs to the fresh-create cases (1 and 2).

  The fixture's companion is **committed** in this repo, so the skill's closing-touch gate reads
  it as clean and the close happens in one run. The first-closing-touch path (a *dirty*
  companion → CLOSING, no writes) has no fixture; a sandboxed copy cannot present as
  tracked-and-modified.

## `lumen/` — case 4 (missing UXD halts)

A status-page product with a Settled PRD and **no UXD** — the project arrived here out of order.

- **Case 4 `missing-uxd-halt`** — the primary-input rule: the design language is authored off
  the UXD's direction call, so with nothing at the resolved UXD path the skill halts and
  authors nothing. The prompt does not mention the UXD; a baseline writes a design doc from the
  PRD alone, which is exactly the ungrounded document the halt exists to prevent.

## No fixture — case 5 (posture-halt)

Case 5's prompt is a bare, non-CDO request; the skill halts on the posture check and authors
nothing, so it needs no fixture.

## Run-time note — baseline writes into in-repo fixtures

The *without-skill* baseline config does **not** sandbox: it resolves the relative
`Product path:` and writes its produced `DESIGN.md` (and, for re-entry, may overwrite the tracked
`docs/DESIGN.md`) straight into the fixture tree. This doesn't corrupt grading, but it dirties
the tree. After a run, restore the fixtures — `git checkout skills/cdo/.claude/skills/product-design/evals/inputs`
and delete any stray untracked `DESIGN.md` / `DESIGN_open_issues.md` / `trail/design/` under a
fixture's `docs/` (`/bin/rm`, since the interactive shell's `rm` is aliased `-i`).

A with-skill run may also invoke the format's linter through `npx`, which needs network access
the first time the pinned package version is fetched.
