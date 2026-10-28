# 宿場 Shukuba refine — `2026-10-27_project-list-sort`

*Unit `2026-10-27_project-list-sort`, sealed Tobiishi, reviewed 2026-10-28; key named by the caller.
Station `project-list-sort` (root). Seed `2026-10-11_narrow-and-sort`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-27_project-list-sort` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 2 |

## Read

All under `tracker17 · tobiishi · 2026-10-27_project-list-sort`.

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking; 2 change-local (CP-431's case-folding edge and three CP-449 test rows unnamed); 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking; 3 change-local: the CP-435 zero-match set-aside (Considered row 4), line citations off by a few lines, design reaching into task order; 0 skill-general |
| flow findings | `flow_findings/development-plan.md` | 0 blocking; 3 change-local (Task 5 fixture size unasserted, Task 3/4 hint overlap, Task 5 atomic edge unstated) |
| flow findings | `flow_findings/development-content.md` | clean |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking; 3 change-local: rule discrimination unrecorded for Tasks 1 and 3, the default sort stated in `domain` and by `web`'s option order (Considered row 6), one false seam claim fixed by integrity |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`, 1846 passed; added one test, fixed one; two calls (`__version__` none owed; timed-run `main` seam kept) — Considered row 7 |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: (1) dependency audit did not run, NFDR names none — Considered row 5 |
| developer's closing commit | `<a commit not in the public history>` | divergences: Python 3.11 against the packet's 3.13 floor; no `__version__` (left for integrity); two timed-run tests patched the harness (integrity fixed one) |
| deferred decisions | `deferred_decisions.md` | (1) All tasks — owned by the seed's next line; (2) the summary — owned by `tracker17 · nemawashi · 2026-10-11_project-summary`; (3) CP-435 zero-match count set aside — Considered rows 3, 4 |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing |
| corrections owed | `tl_instruction.md` § Corrections owed while there | one line, on `tests/timed_run.py`, a file the unit opened itself; no *Owed outside this change's reach* line |
| work handed on | `change_spec.md` § Out of Scope | All tasks → `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19); summary and its links → `tracker17 · nemawashi · 2026-10-11_project-summary` (lines 17, 18); the rest only fences (multi-field sort, filter rules, add-form answers, remembering choices, wording, looks) |

## Upstream

`git log --since=2026-10-27T00:00 -- products/tracker17/docs/` (the previous refine on this seed read
everything before it): `66837fe34`, `632123a1c`, `9f324007c`, `328b15aaf` (SDD v12, RT-8: a GET form is
a read), `c838e9b62`, `db16374d3` (ADR-0011, NFDR v16; ADR-0006 superseded), `fbbda3139` (README
status). All of it folded the previous refine's two companion items, and all of it landed before this
unit's spec (`a92916fbe`, 2026-10-27T19:02). `grep -E 'ADR-0006|RT-8|QC-7'` over the live seeds and
station prints nothing. No seed or station source moved against the route.

Live companions: none (`ls products/tracker17/docs/*_open_issues.md` matches nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no product chain in
flight. `chain-change-tracker17-state.json` is pending only on this refine step. No unit open at
`journey/tobiishi/`'s root.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-27_project-list-sort` | Reached-when holds on all six lines now; the close is the Scrum Master's, owed | fresh clone at `e5eaf28b6`: `ls products/tracker17/domain/sorting.py` → present; `pytest products/tracker17/tests/` → `1846 passed`, exit 0; `python3 products/tracker17/tests/timed_run.py` → `sort total at 1000 tasks: 14.2 ms`, beside `filter total at 1000 tasks: 6.4 ms`, exit 0; lines 2–4 by `tests/unit/test_sorting.py` (priority, undated, casefold, identity ties, created time, defaults), `tests/integration/test_sort_routes.py` (filter kept, same address, Clear), `tests/e2e/test_sorting.py` |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19), `all-tasks-list` | Next unticked station, reachable where it stands (shape 6): every thing SDD § 6 S-5's bar requires exists now or is this station's own work; no refine has re-aimed it | `products/tracker17/docs/SDD.md:L947-L963`; filter and sort landed (`domain/filtering.py`, `domain/sorting.py`); not-found page exists (`products/tracker17/web/pages.py:L1928`), its All tasks link is the station's own (UXD UX-S10, `products/tracker17/docs/UXD.md:L343`); timed filter and sort already run |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19); `tracker17 · nemawashi · 2026-10-11_project-summary` (lines 17, 18) | Deferred entries 1 and 2 keep their owners | `deferred_decisions.md` entries 1, 2 |
| `products/tracker17/docs/UXD.md` UX-S4 / UX-F5, zero-match count | The design kept the no-match state without a count; UX-S4's No match state asks for the sentence and Clear, not a count, and the product matches it — no document is false and the reading has nothing left to own | `deferred_decisions.md` entry 3; `products/tracker17/docs/UXD.md:L197-L216,L337`; `tests/integration/test_sort_routes.py:L130` |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states there is no audit command, so no companion item is owed (as the previous refine on this seed found) | `security-report.md` § Left for the PM, line 1; `products/tracker17/docs/nfdr.md:L333` *verified by* |
| `products/tracker17/web/pages.py` `_sort_select`, default from option order | Change-local; the default agrees today and tests pin it; no failure measured, so no carrier | `flow_findings/development-implementation.md` finding 2; this run's suite (`1846 passed`) |
| `products/tracker17/docs/nfdr.md`, `__version__` and the timed-run `main` seam | Integrity calls, each with a stated owner and reading; nothing failing | `code-integrity-report.md` § Calls made, 1, 2 |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in the unit or upstream touches their stations | `grep -n -i 'sort\|filter'` on both seeds matches nothing |
| remaining specs, design, plan and implementation flow findings | Change-local, about this unit's own artifacts; they end with it and name no unowned work | the flow findings files above |

## Absent

The closing commit's `Deferred:` lines — see ## Read. The halt report on file records an earlier
design halt (path resolution, a cache permission), since passed by the re-run; a sealed unit's halt is
not a route input.
