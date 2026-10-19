# product-srs eval fixtures

Read-only inputs the eval prompts (`../evals.json`) point at. A `skill-evals` run **reads** these; the
with-skill config writes its output into a sandboxed workspace, so the fixtures stay clean.

**All eval annotations live here, never inside an ingested file.** The grader and the runme agent read
the fixture files *whole* — a comment inside `PRD.md` / `SRS.md` / `SRS_open_issues.md` /
`trail/prd/*.md` that reveals the expected behavior would let a blind baseline pass on the instruction
rather than the skill. So the fixtures below carry only product content (plus a benign path-resolution
note in each `project.md`); the "what each case exercises" notes are all in this file.

Paths are **repo-relative** (publish-safe — no machine-absolute path). `product-srs` reads a relative
`Product path:` as an in-repo product and resolves `<Product path>/docs/SRS.md` +
`<Product path>/docs/SRS_open_issues.md`.

## The full-input fixture shape

product-srs needs **all** the input, not only the PRD. Each product's `docs/` replicates the complete
state a real `product-prd` run leaves behind — the same shape the CTO reads when the SRS begins:

- `docs/PRD.md` — **`Status: Settled`** (the PRD done-state; template vocab is `Draft | Settled | Locked`).
- `docs/trail/prd/cycle-1.md` — the answered PRD companion, copied whole and trailed (`product-prd` creates
  the trail on the fold-and-close cycle).
- `docs/product_request.md` — the raw owner brief.
- (the answered `PRD_open_issues.md` is **deleted** when the PRD loop closed — absent by design.)

Beside `docs/`, each fixture also carries **`agari.md`** — the project's declared terminus, which
`product-srs` reads as the boundary it scopes against. In a real instance the Agari sits in the
project folder (`system/projects/<name>/agari.md`) while the product lives elsewhere; the fixtures
collapse the two, exactly as they already do for `project.md`.

**The eval prompts deliberately never mention `agari.md`.** They name the binding and say to read
the product input; only the skill's own intake knows the terminus is there. That is what keeps the
terminus assertion discriminating — a prompt that named the file would hand the behavior to the
baseline and grade the instruction instead of the skill.

The re-entry fixture adds a first-authored `docs/SRS.md` + an answered `docs/SRS_open_issues.md`.

## Two fixture products

- **mailmate** — the genuine `product-prd` eval product (a shared team inbox), carried to its Settled
  form: the exact PRD `product-prd` produces once its two open issues are answered. Thin — no scale
  number, no NFRs, no contradiction — so it anchors the happy path but can't exercise the SRS-signature
  behaviors.
- **trimly** — a purpose-shaped product (a team link-shortener with click analytics) that *can* bite the
  signature cases: it carries a **derivable scale fact** (50 workspaces, up to 2,000 links each, ~200,000
  redirects/day → a throughput NFR can be *derived*), **no latency/availability number** (G4 only says
  "feels instant" / "dependable" → owner-taste NFRs that must route to *choices to confirm*), an
  **internal contradiction** (F5 "links never expire" vs §5 inactive links "auto-purged after 12 months"),
  and **external dependencies** (Stripe, a geo-IP provider, a CDN).

## `mailmate/` — case 1 (first-run authoring)

The full-input shape, no SRS yet — the run authors one.

- **Case 1 `draft-and-surface-two-bucket`** — the skill drafts the whole SRS best-effort and surfaces
  what it can't settle into a two-bucket companion (*Open issues* + *Choices to confirm*, and **no**
  *Directives* bucket — that one is the PRD's, not the SRS's). Each *choice* carries the literal
  `Confirm or override:` slot; every requirement is a typed `FR-n` with a `(traces to: PRD …)` tag;
  and the SRS's `Status:` line reads `Draft`, since items remain open (`Locked` is ratification,
  which the skill never writes). It also carries **`scope-names-the-terminus`**: mailmate's
  `agari.md` declares done as one paying team running a full billing cycle and puts the adoption and
  retention numbers outside it, so a Scope section scoped against that terminus reads differently
  from one scoped against the PRD alone — which is all a baseline has, since the prompt never says
  the file exists.

## `trimly/` — cases 2, 4 (first-run authoring)

The full-input shape, no SRS yet.

- **Case 2 `invented-nfr-routing`** — the signature SRS behavior. The owner-taste NFRs (redirect latency,
  availability) route to *choices to confirm*, never asserted as settled bars; the derivable throughput
  NFR is stated in the SRS with its derivation recorded in a Review Note (`RN-n`).
- **Case 4 `prd-critique-surface-not-halt`** — the never-expire vs auto-purge contradiction is caught:
  named in a Review Note or surfaced in the companion, and the SRS is produced anyway (never halts).

## `trimly-reentry/` — case 3 (loop re-entry)

The full-input shape, plus an existing **`docs/SRS.md`** (Version 1 — latency/availability drafted
best-effort as choices to confirm, the contradiction surfaced as an open issue) and an already-**answered**
`docs/SRS_open_issues.md` (the owner has filled every *Answer* / *Confirm or override* slot: latency
confirmed at p95 < 100 ms, availability overridden 99.9% → 99.5%, the contradiction resolved to
never-expire).

- **Case 3 `reentry-fold-and-delete`** — every slot is answered, so this run is the close: it retires
  the answered companion whole to `docs/trail/srs/cycle-1.md`, folds the owner's values into the SRS
  (p95 redirect < 100 ms kept, availability changed to 99.5%, the contradiction resolved in favor of
  never-expire), records that owner provenance in the SRS Review Notes citing the trail path (durable,
  captured *before* the companion goes), and **removes** `SRS_open_issues.md` — its absence is the
  done signal.

  This fixture carries the same `agari.md` as `trimly/`, but **no terminus assertion is graded here**,
  deliberately. Its baseline `SRS.md` was authored before the terminus existed, so a fold run meets a
  boundary its settled content was never scoped against — realistic (it is what happened to the
  product that surfaced this gap) and a poor thing to grade, since the stability rule and the terminus
  pull in opposite directions on the same text. The terminus is graded on the fresh-create case.

  The fixture's companion is **committed** in this repo, and the with-skill run's private copy lands
  under the gitignored `workspace/` tree, so the skill's closing-touch gate reads it as clean and the
  close happens in one run. The first-closing-touch path — a *dirty* companion, where the run changes
  nothing and reports CLOSING — has no fixture and is not covered here; a sandboxed copy cannot be
  made to present as a tracked-and-modified file.

## No fixture — case 5 (posture-halt)

Case 5's prompt is a bare, non-CTO request; the skill halts on the posture check and authors nothing, so
it needs no fixture.

## Run-time note — baseline writes into in-repo fixtures

The *without-skill* baseline config does **not** sandbox: it resolves the relative `Product path:` and
writes its produced `SRS.md` (and, for re-entry, may overwrite the tracked `docs/SRS.md`) straight into
the fixture tree. This doesn't corrupt grading, but it dirties the tree. After a run, restore the
fixtures — `git checkout skills/cto/.claude/skills/product-srs/evals/inputs` and delete any stray untracked
`SRS.md` / `SRS_open_issues.md` under a fixture's `docs/`.
