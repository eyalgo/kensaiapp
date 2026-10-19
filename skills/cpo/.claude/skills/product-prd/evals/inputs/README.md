# product-prd eval fixtures

Read-only inputs the eval prompts (`../evals.json`) point at. A `skill-evals` run **reads** these and
writes its output into `../workspace/iteration-N/<case>/<config>/outputs/` — the fixtures themselves
are never written to, so they stay clean across runs.

**All eval annotations live here, never inside an ingested file.** The harness feeds the fixture files
to the graded model *whole*, comments included — so a note inside `product_request.md` / `PRD.md` /
`PRD_open_issues.md` saying what the case exercises hands the model its answer, and a run can pass on
the annotation rather than on the skill. The fixtures below carry only product content (plus a benign
path-resolution note in each `project.md`); every "what this case exercises" note is in this file.

Paths are **repo-relative** (publish-safe — no machine-absolute path). `product-prd` reads a relative
`Product path:` as an in-repo product.

## `mailmate/` — cases 1, 3, 4 (first-run authoring)

`docs/product_request.md` is a raw owner brief, **deliberately incomplete** — not a finished, gap-free
request. Open target segment, no success metric, no data/privacy story, per-seat **Stripe** billing, and
an unpublished **enterprise SLA** only the infra vendor's account rep can give. The gaps are the point:
the CPO must draft a PRD from the brief and surface what it can't settle, which exercises
surface-don't-interview (case 1), the directive/gate lifecycle (case 3, the SLA), and the external tag
contract (case 4, Stripe).

## `mailmate-reentry/` — case 2 (loop re-entry)

The same raw brief, plus an existing `docs/PRD.md` (Status: Draft) and an already-**answered**
`docs/PRD_open_issues.md` — both `Answer:` slots filled, as if the owner had answered and committed.
Re-running `product-prd` should fold both answers into the PRD, copy the answered companion whole to
`docs/trail/prd/cycle-1.md`, and close. That expectation is stated here and nowhere else: what a re-run
does with an answered companion is the skill's to know, so the fixture must not tell it.

## No fixture — case 5 (posture-halt)

Case 5's prompt is a bare, non-CPO request; the skill halts on the posture check and authors nothing,
so it needs no fixture.
