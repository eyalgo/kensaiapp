# Deferred Decisions — comments-on-the-page

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## Deleting a task or a project together with its comments — record gap, handed on by development-specs (2026-10-12)
**Record:** `products/tracker17/docs/fdr.md` R-37, R-50 (SRS FR-13, FR-17; SDD § 3, What the system holds)
**Product today:** no action deletes a task or a project; `ROUTES` holds no delete route (`products/tracker17/web/routes.py:87-101`).
**Why not this change:** the requirement binds deletion, which this change leaves as it is, and the request rules it out: "no deleting a comment with its task". The request names `tracker17 · nemawashi · 2026-10-11_delete-and-rename` as the place.
**Owner:** none — for shukuba-refine
**Status:** open

## Pages served while saved data is unreadable — record gap, handed on by development-specs (2026-10-12)
**Record:** `products/tracker17/docs/fdr.md` R-25, R-26 (SRS FR-8; SDD § 3 SM-6, § 4 EX-12)
**Product today:** the start refuses and returns before any listener exists, so no page is served for any unreadable data (`products/tracker17/main.py:39-48`).
**Why not this change:** the requirement binds the unreadable-data mode, which this change leaves as it is. A broken saved comment only widens when the existing start refusal happens (change_spec CP-264). The request leaves these pages to `tracker17 · nemawashi · 2026-10-11_protect-saved-data`.
**Owner:** none — for shukuba-refine
**Status:** open

## The task's status and its moves on the task's page — record gap, handed on by development-specs (2026-10-12)
**Record:** `products/tracker17/docs/UXD.md` UX-S6 ("its status with its allowed moves"); `products/tracker17/docs/fdr.md` R-56
**Product today:** the task's page shows its title, its project, the edit form and its labels, and no status (`products/tracker17/web/pages.py:893-902`); no `domain/workflow.py` exists.
**Why not this change:** the requirement binds the status workflow, which this change leaves as it is, and the request does not ask for it. `tracker17 · nemawashi · 2026-10-07_status-moves` cuts it.
**Owner:** none — for shukuba-refine
**Status:** open

## CP-273's timed comment add — reading set aside by development-design (2026-10-12)
**Spec lines:** CP-273 (`change_spec.md` Rules, L96), its Example (L155), the timed-run Verified Claims as obligations of this change (L173-L174), Out of Scope's “CP-273 times only the comment add” (L187), and Locked Answers Gap 18 (L218).
**Conflict:** the request explicitly requires `tests/timed_run.py` and `tests/integration/test_timed_run.py` to stay byte-identical and leaves full-volume timing to the next station (`change_request.md` “Must not be weakened or added” and “Left to later stations”, L11-L15; `tracker17 · shukuba · 2026-10-12_comments-on-the-page`, Guardrail). The harness currently times no comment add (`products/tracker17/tests/timed_run.py` “main”, L525-L555). Extending it would violate the requested boundary; no Rule releases the existing timed-run test contract.
**Reading taken:** deliver CP-240–CP-272 and CP-274–CP-275, preserving both timed-run files and their existing checks. The alternative implements CP-273 now; it is set aside because it violates the request. The remaining timing obligation is `products/tracker17/docs/nfdr.md` QC-48 (L412-L419) and `products/tracker17/docs/SDD.md` § 4 TS-5, which this design does not claim fulfilled or amend. The request names `tracker17 · nemawashi · 2026-10-07_comment-on-a-task` item 3 `full-volume-run` as its later place; this entry leaves the route decision to the owner of that journey.
**Owner:** none — for shukuba-refine
**Status:** open
