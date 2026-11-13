# 宿場 Shukuba refine — `2026-11-12_failed-action-path-non-text-byte`

*Unit `2026-11-12_failed-action-path-non-text-byte`, sealed Tobiishi, reviewed 2026-11-13; key named by the caller.
Station `2026-11-12_failed-action-path` (root). Seed `2026-10-30_a-path-with-a-non-text-byte-is-printed`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-12_failed-action-path` | — | Considered row 1 |
| 2 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 3 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | 2 | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking, 3 change-local (action-to-reporter hop read not run; a method in the Structural Goal; an altitude slip); all end with the unit — the test drives a real action through `_guarded` (Considered row 3) |
| flow findings | `flow_findings/development-design.md` | 0 blocking, 1 change-local: errno form's mutation guard unstated; code-integrity's mutation table shows both spellings red in both forms (Considered row 3) |
| flow findings | `flow_findings/development-plan.md` | clean |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking, 4 change-local (closing-notes evidence; the locale-held input), 1 skill-general (`commit-via-builder-call-vs-locked-python`, the machinery's, not this route's) (Considered rows 3, 4) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; no tests added; four mutations each red; 3276 passed, 2 skipped, 122 e2e passed; nothing surfaced unfixed; its one call (`os.fsdecode` input) Considered row 4 |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 5) |
| developer's closing commit | `<a commit not in the public history>` | three packet divergences (test location, `-> None`, builder call as `python3`), each with its reason; the path-rewrite mutation recorded |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | none |
| the closing commit's `Deferred:` lines | absent — `<a commit not in the public history>` holds none | none to route |
| corrections owed | absent — `tl_instruction.md` has no § Corrections owed while there | none |
| work handed on | `change_spec.md` § Out of Scope | the stand-in move and the contract suites → "the change QC-64's walk lands with"; no seed carries it (recommendation 2); the rest only fences |

## Upstream

`git log --since=2026-10-30T15:47:01+01:00 --name-status -- products/tracker17/docs/`: CONTENT v21 (RN-35, `4f2fbdb90`) — already folded into the station by the 2026-11-05 re-cut; FDR, PRD, SRS, UXD, DESIGN — renames and the public-repo assumption (`6890e0493`, `48e3c673f`, `b04ddbdfe`, `fcb74cf87`), none this seed's source; SDD v20–v22 and NFDR v26–v28 — test-dependency pins, Playwright 1.65.1, Behave way in, and SDD v20 TS-6 one fake and one contract suite per port (`28d68f4f6`, `14cdd0245`). None moves this seed's sources (SDD S-8, FDR R-2/R-24/R-25, CONTENT RN-33/RN-35). `find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing: no live companion.

## Held

None. `chain-tracker17-state.json` has `ended: settled`, `pending` null; `journey/tobiishi/` holds only `trail/`, so no open unit. `chain-walk-tracker17-state.json` is live on this key only for this refine step.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-12_failed-action-path` | Reached-when 1 to 4 hold now: close owed to the Scrum Master, and it is the seed's last unticked item. | (1) `products/tracker17/tests/integration/test_failure_report.py` holds the two-line, no-raise cases; (2) `git grep -n 'report_failure\|Could not save' a02a27c4c -- products/tracker17/tests` prints nothing, at `d6226071e` prints `test_failure_report.py:5`; (3) path-rewrite mutation recorded in `<a commit not in the public history>` and in `code-integrity-report.md` § Tests added or fixed; (4) clone at `d6226071e`: `pytest products/tracker17/tests/` 3276 passed, 2 skipped, exit 0; `pytest products/tracker17/tests/e2e/` 122 passed, exit 0 |
| `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed` | Items 1 and 2 ticked, item 3 is the station above: fully walked once the close lands, so a retire is recommended, not a re-cut. Re-aims of item 3 by a refine number one (`804f2b156`, the line added); the 2026-11-05 re-cut `4371df952` was by hand; no owner's act owed. | `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed` (lines 15-17); `git log -- <seed>` |
| the specs, design and implementation change-local findings | Each is about this unit's records and ends with it: the test drives a real failing action through `_guarded`, and both mutation spellings go red in both forms. | `flow_findings/*.md`; `code-integrity-report.md` mutation table |
| the `os.fsdecode` input held by the locale | A non-UTF-8 filesystem encoding does not occur in the gate's environments, so no carrier is owed. | `code-integrity-report.md` § Calls made; `project.md` Test command runs on the owner's Mac and the Python image (`C.UTF-8`) |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says "no audit command exists for this product". | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 |

## Absent

`deferred_decisions.md`, the closing commit's `Deferred:` lines and `tl_instruction.md` § Corrections owed while there — none produced by this unit. No live companion under `products/tracker17/docs/`.
