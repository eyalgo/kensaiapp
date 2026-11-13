# 宿場 Shukuba refine — `2026-11-13_saver-fake-and-suite`

*Unit `2026-11-13_saver-fake-and-suite`, sealed Tobiishi, reviewed 2026-11-13. Key named by the caller; the
project's PM context names the same unit, `Sealed`.
Station `saver-fake-and-suite` (root). Seed `2026-11-13_one-fake-and-one-contract-suite-per-contract`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/product-docs/launcher.sh tracker17` | — | Moves row 1, the companion item raised |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_saver-fake-and-suite` | — | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/walk/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-13_saver-fake-and-suite`, `flow_findings/development-specs.md` | 0 blocking, 6 change-local: I-1 skip wording, the load claim, the `def save` grep misses non-`def` stand-ins (Considered row 4), I-9 has no check, the empty e2e half unrecorded, I-6 altitude |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 2 change-local: the held-call narrowing rests on save serialization, unnamed; the design prescribes a downstream record |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 6 change-local: Task 3's grep criterion out of order, no test count compared (Considered row 3), two dropped assertions unmapped, a base-class gate with no command, a split note, the mutation record's evidence form |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 4 change-local (Step 1b count, per-rule mutations unrecorded, two mis-cited language lines), 1 skill-general → kaizen `step-1b-checks-the-layer-the-instruction-names`, not the route's |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`; rewrote two layer-1 checks off the real clock, fixed one that could not see its fault, added the 10 s bound's test; surfaced nothing it could not fix; four calls left to Tech Lead and Architect, all on the unit's own test code |
| security report | the same, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 5) |
| developer's closing commit | `<a commit not in the public history>` | Task 13's sweep past the 20-module list recorded with its reason; per-rule mutation for keep only |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` — absent, no line begins `Deferred:` | — |
| corrections owed | `tl_instruction.md` § Corrections owed while there | one *Owed outside this change's reach* line: QC-64 points at `testing_python.md` § 2 → companion item (Moves row 1) |
| work handed on | `change_spec.md` § Out of Scope | the `Clock` fake → seed item 2, carried; the layer-6 walk → seed item 3, carried; QC-64's § 2 pointer → Moves row 1; the timed-run failure under load → Considered row 3; production code, restructuring → fences, nothing handed on |

## Upstream

`git log --since=2026-11-13T02:37:24+01:00 --name-status -- products/tracker17/docs/`: FDR v7→v8, SDD v23,
CONTENT v22, UXD v12 — every one the due-today count (`243f1f6f6`, `edd4235e1`, `f3749d5bf`, `59b5394da` and
their companion commits). `nfdr.md` and `adr/` did not move; QC-64 (`products/tracker17/docs/nfdr.md:341-361`)
and SDD § 4 TS-6 still read as the seed cut them. No live `*_open_issues.md` before this run; this run opened
`architecture_open_issues.md`.

## Held

None. `system/logs/chain-tracker17-state.json`: `ended` `settled`, `pending` null — no docs chain in flight.
`system/logs/chain-walk-tracker17-state.json` carries this unit with `pending` `refine` — this run. No open unit
at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1, on `nfdr.md` QC-64 | QC-64's *form* sentence and tail point at `testing_python.md` § 2, which that file does not number; the quoted sentence stands in § Rules. | `tl_instruction.md` § Corrections owed while there; `grep -n '^#' core/doctrine/engineering/testing_python.md` → *Layers 1–5*, *Rules*, *Layer 6*, *Layer 7*; `products/tracker17/docs/nfdr.md:343`, `:360` | `5ed90130c` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_saver-fake-and-suite` | Reached-when 1 to 4 hold on `main`; the close is the Scrum Master's, owed. | 1: `tests/fakes.py:20` `FakeSaver`, `tests/integration/test_saver_contract.py:362`, `:382` the two runs. 2: `code-integrity-report.md` § Test evidence — drop-the-state mutation `16 failed, 18 passed`, `SavedData` run all 9 passed. 3: `grep -rEln --include='*.py' '^\s+def save\(' tests \| wc -l` → `1` (`tests/fakes.py:47`). 4: the card's first half in a fresh clone at `07c49b3c9` → `3370 passed, 2 skipped`; `git diff --stat 61a5b1ecc..07c49b3c9 -- products/tracker17 ':!products/tracker17/tests'` → empty |
| `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` (line 16), the next unticked station | Shape 6: reachable where it stands. QC-64 asks for the fake in one module (exists now, `tests/fakes.py`), a suite run both ways at layer 2 (the station's own work), handed `main.SystemClock` — QC-2 is scoped to code outside `tests/` so a test may import `main`; nothing it needs is a later station's. | `products/tracker17/docs/nfdr.md:341-348`; `:1952` ("QC-64's clock suite hands in `main.SystemClock` … an unscoped QC-2 would forbid it"); 24 files still define `now` under `tests/` — the station's work |
| the same seed, item 3 (the walk) | No change: the unit added nothing the walk's bar must also catch; its cases are QC-64's own list. | `products/tracker17/docs/nfdr.md:350-357` |
| plan finding: no test count compared; spec Out of Scope: the timed-run failure under load | Neither occurs now: no test was lost and the timed run passed in the full run. | base `3335 passed, 2 skipped, 1 failed` (spec Verified Claims) + 34 contract tests + 1 recovered = `3370 passed, 2 skipped` in this run's fresh clone at `07c49b3c9` |
| spec finding: non-`def` `save`/`now` stand-ins the grep cannot see | Does not occur in the tree, so the walk station carries nothing new. | `grep -rEn --include='*.py' '\b(save\|now)\s*=\|SimpleNamespace\|Mock\(\|MagicMock\|monkeypatch\.setattr\(…(save\|now)' tests` minus `tests/fakes.py` → one hit, a string fixture at `tests/architecture/test_reach.py:285` |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says so. | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* — "no audit command exists for this product" |
| unpicked seeds (the five due-today seeds) | Not this unit's ground; their upstream moved on its own path, and nothing this unit left touches them. | `git log` above; their sources are FDR/SDD/CONTENT/UXD/SRS, not QC-64 |

## Absent

`deferred_decisions.md` — the unit wrote none. `Deferred:` lines — none in `<a commit not in the public history>`. No halt report — a sealed unit.
