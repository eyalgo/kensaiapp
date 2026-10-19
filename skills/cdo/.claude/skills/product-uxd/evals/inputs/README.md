# product-uxd eval fixtures

Read-only inputs the eval prompts (`../evals.json`) point at. A `skill-evals` run **reads** these; the
with-skill config writes its output into a sandboxed workspace, so the fixtures stay clean.

**All eval annotations live here, never inside an ingested file.** The grader and the runme agent read
the fixture files *whole* — a comment inside `PRD.md` / `UXD.md` / `UXD_open_issues.md` /
`trail/prd/*.md` that reveals the expected behavior would let a blind baseline pass on the instruction
rather than the skill. So the fixtures below carry only product content (plus a benign path-resolution
note in each `project.md`); the "what each case exercises" notes are all in this file.

Paths are **repo-relative** (publish-safe — no machine-absolute path). `product-uxd` reads a relative
`Product path:` as an in-repo product and resolves `<Product path>/docs/UXD.md` +
`<Product path>/docs/UXD_open_issues.md`.

## The full-input fixture shape

product-uxd needs **all** the input, not only the PRD. Each product's `docs/` replicates the complete
state a real `product-prd` run leaves behind — the same shape the CDO reads when the UXD begins:

- `docs/PRD.md` — **`Status: Settled`** (the PRD done-state; template vocab is `Draft | Settled | Locked`),
  carrying a **`## UX Notes`** section: the one PRD section written *for* this document, which the
  authoring prompt walks item by item and places across the Design Read, Key Flows, Screen Inventory,
  and Interaction Patterns. A fixture PRD without it would starve the derivation's primary seed.
- `docs/trail/prd/cycle-1.md` — the answered PRD companion, copied whole and trailed (`product-prd` creates
  the trail on the fold-and-close cycle).
- `docs/product_request.md` — the raw owner brief.
- (the answered `PRD_open_issues.md` is **deleted** when the PRD loop closed — absent by design.)

Beside `docs/`, each fixture also carries **`agari.md`** — the project's declared terminus, which
`product-uxd` reads as the boundary it scopes against. In a real instance the Agari sits in the
project folder (`system/projects/<name>/agari.md`) while the product lives elsewhere; the fixtures
collapse the two, exactly as they already do for `project.md`.

**The eval prompts deliberately never mention `agari.md`.** They name the binding and say to read
the product input; only the skill's own intake knows the terminus is there. That is what keeps the
terminus assertion discriminating — a prompt that named the file would hand the behavior to the
baseline and grade the instruction instead of the skill.

**No `SRS.md` in any fixture.** The SRS and the UXD are siblings authored off the same settled PRD at
the same time, so its absence is the normal case, and the authoring prompt treats it as a sibling that
is never a source. Nothing here grades the collision-noticing path.

The re-entry fixture adds a first-authored `docs/UXD.md` + an answered `docs/UXD_open_issues.md`.

## Two fixture products

Both are the `product-srs` eval products carried over — the same PRDs, plus the `## UX Notes` section
above. Grading two definition-tier skills off one pair of settled PRDs is faithful to how the tier
actually runs: the CTO and the CDO read the same document at the same time.

- **mailmate** — the genuine `product-prd` eval product (a shared team inbox), carried to its Settled
  form. Thin — few screens, no aesthetic direction stated, no accessibility bar — so it anchors the
  document-shape and loop contract but can't exercise the derivation-signature behaviors.
- **trimly** — a purpose-shaped product (a team link-shortener with click analytics) that *can* bite the
  signature cases: a **five-screen surface** with real empty / loading / error / success stories, a
  **stated density fact** (2,000 active links per workspace → a DENSITY dial that *is* derivable), **no
  motion intent and no house style anywhere** (→ owner-taste calls that must route to *choices to
  confirm*), an **internal contradiction** (F5 "links never expire" vs §5 inactive links "auto-purged
  after 12 months") that lands on a screen state rather than on a data rule, and **external
  dependencies** (Stripe, a geo-IP provider, a CDN) that give the degraded-panel story its basis.

## `mailmate/` — case 1 (first-run authoring)

The full-input shape, no UXD yet — the run authors one.

- **Case 1 `first-authoring-two-bucket`** — the definition-tier loop contract. The skill drafts the whole
  UXD best-effort and surfaces what it can't settle into a two-bucket companion (*Open issues* +
  *Choices to confirm*, and **no** *Directives* bucket — that one is the PRD's, not the UXD's). Each
  *choice* carries the literal `Confirm or override` slot; entries are typed `UX-…` IDs with an inline
  `(→ PRD …)` trace tag; and the UXD's `Status:` line reads `Draft`, since items remain open (`Locked`
  is ratification, which the skill never writes). It also carries **`scope-names-the-terminus`**:
  mailmate's `agari.md` declares done as one paying team running a full billing cycle and puts the
  adoption and retention numbers outside it, so an *Out of Scope* section scoped against that terminus
  reads differently from one scoped against the PRD alone — which is all a baseline has, since the
  prompt never says the file exists.

## `trimly/` — cases 2, 3 (first-run authoring)

The full-input shape, no UXD yet. Two cases share it because they grade disjoint halves of the same
run's output: case 2 the document's own shape, case 3 what the skill *does* with what the PRD doesn't say.

- **Case 2 `design-read-dials-and-states`** — the UXD's signature shape, and the part of it a capable
  baseline never invents: the `Reading this as:` one-liner; the three named dials (VARIANCE, MOTION,
  DENSITY) on a 1–10 scale with reasoning from a PRD fact; a screen inventory where **every** row
  carries all four states; and a §9 direction that names one system or aesthetic family **and carries
  no token values** — colours, type scales, radii and spacing live only in `DESIGN.md`, and a baseline
  asked for a "UX design spec" reliably dumps a palette into it.
- **Case 3 `taste-routing-and-prd-critique`** — the anti-default discipline, which is the reason this
  document exists. trimly's PRD names no house style and no motion intent, so the design-system call
  is owner taste and must ride a *choice to confirm* with its sign-off slot rather than being asserted
  as settled; anything the CDO added beyond the PRD carries a Review Note marked `(added)` or
  `(changed)`; and the never-expire vs auto-purge contradiction is caught with both sides named —
  while the UXD is still produced, because the skill critiques and surfaces rather than halting.

## `trimly-reentry/` — case 4 (loop re-entry)

The full-input shape, plus an existing **`docs/UXD.md`** (Version 1 — the MOTION dial and the
design-system direction drafted best-effort as choices to confirm, the link-lifetime contradiction
surfaced as an open issue and visible in UX-S1 as an *Inactive — purges soon* badge) and an
already-**answered** `docs/UXD_open_issues.md` (every *Answer* / *Confirm or override* slot filled:
links never expire and the purge badge goes, MOTION overridden 4 → 2, the direction overridden from
built-from-primitives to the **Radix Themes** package).

- **Case 4 `reentry-fold-and-close`** — every slot is answered, so this run is the close: it retires
  the answered companion whole to `docs/trail/uxd/cycle-1.md`, folds the owner's values into the UXD
  (MOTION reads 2, §9 names Radix Themes, the purge badge is gone and permanence is stated), records
  that owner provenance in the UXD Review Notes citing the trail path (durable, captured *before* the
  companion goes), stamps `Status: Settled`, and **removes** `UXD_open_issues.md` — its absence is the
  done signal.

  Three things this case deliberately does **not** grade:

  - **No terminus assertion.** Same reasoning as the sibling set: the fixture's Version-1 UXD *does*
    carry an Out of Scope section scoped against the terminus, and the stability rule requires it be
    reproduced — so grading it here would grade reproduction, not derivation. The terminus is graded
    on the fresh-create case.
  - **No cycle-numbering rule.** The fixture ships no `docs/trail/uxd/`, so `cycle-1` is the
    unconditional answer and a hardcoded `cycle-1` is indistinguishable from correct max-based
    numbering. Testing that rule needs its own pre-seeded fixture and case.
  - **The pre-existing Review Notes are exempt** from the trail-citation assertion. RN-1 to RN-3 in the
    Version-1 UXD are settled content citing PRD sections, and the stability rule requires a compliant
    run to reproduce them verbatim — an "every citation names the trail" quantifier would fail a
    correct run. Only the notes recording *this round's* owner answers are graded.

  The fixture's companion is **committed** in this repo, and the with-skill run's private copy lands
  under the gitignored `workspace/` tree, so the skill's closing-touch gate reads it as clean and the
  close happens in one run. The first-closing-touch path — a *dirty* companion, where the run changes
  nothing and reports CLOSING — has no fixture and is not covered here; a sandboxed copy cannot be
  made to present as a tracked-and-modified file.

## No fixture — case 5 (posture-halt)

Case 5's prompt is a bare, non-CDO request; the skill halts on the posture check and authors nothing, so
it needs no fixture.

## Run-time note — baseline writes into in-repo fixtures

The *without-skill* baseline config does **not** sandbox: it resolves the relative `Product path:` and
writes its produced `UXD.md` (and, for re-entry, may overwrite the tracked `docs/UXD.md`) straight into
the fixture tree. This doesn't corrupt grading, but it dirties the tree. After a run, restore the
fixtures — `git checkout skills/cdo/.claude/skills/product-uxd/evals/inputs` and delete any stray untracked
`UXD.md` / `UXD_open_issues.md` under a fixture's `docs/`.
