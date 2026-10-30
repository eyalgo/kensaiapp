# 宿場 Shukuba refine — `2026-10-30_ready-start-non-text-path`

*Unit `2026-10-30_ready-start-non-text-path`, sealed Tobiishi, reviewed 2026-10-30.
Station `2026-10-30_ready-start` (root). Seed `2026-10-30_a-path-with-a-non-text-byte-is-printed`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-30_ready-start` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking, 3 change-local (rule altitude ×2, stderr evidence), 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking, 3 change-local; the CP-749 narrowing to U+DC80–U+DCFF is Considered row 5 |
| flow findings | `flow_findings/development-content.md` | clean |
| flow findings | `flow_findings/development-plan.md` | 0 blocking, 2 change-local (no gate for the red observation, unrecorded T5 narrowing); integrity reran the red |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking, 3 change-local, each settled by code-integrity |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; added two tests and fixed one assertion; nothing left unfixed; Call 1 is Considered row 6 |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 9): dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 4) |
| developer's closing commit | `<a commit not in the public history>` | hex hand-off to the child, errno short list, one added range test; the `__version__` divergence was ruled none by code-integrity |
| deferred decisions | `deferred_decisions.md` | entry 1, failed-action path form, `Owner: none` → seed's new `failed-action-path` (Moves row 1); entry 2, QC-40 graph-listing moment, `Owner: none` → owned by QC-40's own review (Considered row 3) |
| the closing commit's `Deferred:` lines | absent — `<a commit not in the public history>` holds none | none to route |
| corrections owed | absent — `tl_instruction.md` has no such section | none |
| work handed on | `change_spec.md` § Out of Scope | unreadable start → the seed's `unreadable-start`; failed-action message → the seed's `failed-action-path`; the rest only fences (Considered row 7) |

## Upstream

`git log --since=2026-10-30T15:47:01+01:00 --name-status -- products/tracker17/docs/` prints nothing: the last docs commit, `43673f95f`, is 15:39, before the seed. `find products/tracker17/docs -name '*_open_issues.md'` prints nothing: no live companion.

## Held

None. `chain-tracker17-state.json` has `ended: settled`, `pending` null; `journey/tobiishi/` holds only `trail/`, so no open unit. `chain-change-tracker17-state.json` is live on this key only for this refine step.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed` | Work handed on to nobody: the document asks for one form everywhere and this console site breaks it, so the seed takes it as a third station; a note on `unreadable-start` also records that a real start cannot run on this file system | `products/tracker17/docs/CONTENT.md:135-139`; `products/tracker17/web/routes.py:1327-1332`; `Site._report_failure('Could not save.', OSError(92, 'Illegal byte sequence', os.fsdecode(b'/tmp/caf\xe9')))` prints `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`; `os.makedirs` on that path → errno 92 | `804f2b156` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-30_ready-start` | All four reached-when lines hold, so the close is owed to the Scrum Master, and this run does not make it | Bars 1–2: `test_readable_start_prints_non_text_path_and_serves`, `products/tracker17/tests/integration/test_ready_start.py:203`, and `code-integrity-report.md` § Test evidence (`UnicodeEncodeError` at `a7d507b23`). Bar 3: `git diff --stat a7d507b23 97783ee64 -- products/tracker17` shows `main.py` and the two new test modules only. Bar 4: the card's command in a disposable clone at `97783ee64`: 2968 passed, 1 skipped; 122 passed |
| `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`, lines `unreadable-start` and `failed-action-path` | Both can be met where they stand: each surface and the failed-action site exists and fails today, nothing later on the route is needed, and each is that station's own work | Clauses: `products/tracker17/docs/CONTENT.md:135-139`, `products/tracker17/docs/SDD.md` § 6 S-8. Sites: `_unreadable_line` and `listen_unreadable` in `products/tracker17/main.py`; `products/tracker17/web/routes.py:1327-1332` |
| `products/tracker17/docs/nfdr.md` QC-40, graph-listing moment | Entry 2's `Owner: none` is wrong in effect: QC-40 says this reading records the feed as down and the moment as still owed, and raises no discrepancy, and its own next review carries it | `products/tracker17/docs/nfdr.md:399-418`; `deferred_decisions.md` entry 2 |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists, as earlier refines found; no companion owed | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:399-418` |
| `products/tracker17/docs/CONTENT.md` § *A path the tracker prints*, a lone surrogate outside U+DC80–U+DCFF | The form does not occur: the machine's decoding yields only that range, so no carrier | `os.fsdecode(bytes(range(128, 256)))` → min `0xdc80`, max `0xdcff`, encoding `utf-8` |
| `products/tracker17/docs/nfdr.md` § 8, a gate that can hold a byte-bearing directory | The spec chose the skip (CP-753) and the skipped case passed once in the Linux container, so no gate is owed | `code-integrity-report.md` § Calls made, item 1 |
| `products/tracker17/docs/CONTENT.md` RN-33, a real backslash-x folder name and a character the console can't write | Out of Scope only fences these, and the document already states both as not covered | `products/tracker17/docs/CONTENT.md:606`; `change_spec.md` § Out of Scope |

## Absent

The closing commit's `Deferred:` lines and `tl_instruction.md` § *Corrections owed while there*: the unit produced neither. No `*_open_issues.md` under the product's `docs/`. No other input was unreadable.
