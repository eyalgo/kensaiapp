# 宿場 Shukuba refine — `2026-10-30_second-tracker-refusal`

*Unit `2026-10-30_second-tracker-refusal`, sealed Tobiishi, reviewed 2026-10-30.
Station `2026-10-30_second-tracker-refusal` (root). Seed `2026-10-11_protect-saved-data`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | the companion items raised, Moves rows 3 and 4 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-30_second-tracker-refusal` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings, specs | `flow_findings/development-specs.md` | 0 blocking, 4 change-local (probe coverage, unrecorded gaps, altitude, handed-down constraint), all about that step's output; no work left |
| flow findings, design | `flow_findings/development-design.md` | 0 blocking, 1 change-local: a location missing its parents; Considered row 5 |
| flow findings, plan | `flow_findings/development-plan.md` | 0 blocking, 2 change-local: no stream assertion on the restart, Considered row 6; README scope conflict, resolved by the integrity report's call 2 |
| flow findings, content | `flow_findings/development-content.md` | 0 blocking, 2 change-local: two README wording faults, still in the product; Moves row 1 |
| flow findings, implementation | `flow_findings/development-implementation.md` | 0 blocking, 2 change-local: the closing record's evidence lines; no work left |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; one race fixed. Five calls: call 1 Considered row 7, call 3 row 5, call 4 row 8, calls 2 and 5 accepted, no work |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 9): no dependency audit named — the NFDR already says so, no companion owed, Considered row 4 |
| developer's closing commit | `726104505` | Divergences recorded: no `__version__` marker, a third README place, a bounded retry, leaf-only creation. Terminology finding carried, Moves row 3 |
| deferred decisions | `deferred_decisions.md` | The unreadable-data page: owned by the seed's item 2, Considered row 2. The package feed's return: owned by QC-40's own review; the 404 has no meaning stated, Moves row 4 |
| the closing commit's `Deferred:` lines | `726104505` | Absent: no line begins `Deferred:` |
| corrections owed | `tl_instruction.md` | Absent: the plan holds no such section |
| work handed on | `change_spec.md` § Out of Scope | The unreadable-data work lands on the seed's item 2. Every other line only fences |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 --name-status -- docs/` in the product: `CONTENT.md`, `DESIGN.md`, `nfdr.md`, `PRD.md`, `SDD.md`, `UXD.md`, `what_left.md` and seven files under `adr/` moved in the seed's life, latest NFDR v22 at `1d11b7047`, SDD v16 at `01d3d925a`. The seed's sources still say what it says: SDD § 6 S-8 (`products/tracker17/docs/SDD.md:L1140-L1169`), SM-5 and SM-6 (`:L239-L240`), SD-4 and SD-5 (`:L541-L543`), AC-7 and AC-16 (`products/tracker17/docs/SRS.md:L486-L489`, `:L523-L526`). No live `*_open_issues.md` before this run; two now, Moves rows 3 and 4.

## Held

None. `system/logs/chain-tracker17-state.json`: `ended` is `settled`, `pending` null. No unit is open at the Tobiishi root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| Modify a seed | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Item 2 takes the README's two wording faults, because it edits those passages and nothing else carries them | `products/tracker17/README.md:L79`, `:L95`; `flow_findings/development-content.md` | `4bba2995a` |
| Modify a seed | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | The prose stated the old start as current, and the tests item 2 rewrites now stand in one more file | `products/tracker17/main.py:L113-L115`, `:L123-L130`; `products/tracker17/tests/integration/test_single_tracker.py:L45`, `:L350`, `:L485` | `4bba2995a` |
| Raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1 | No rule covers the word the README now publishes, and a missing rule is the Content Manager's | `products/tracker17/README.md:L79`; `change_text.md` § Findings for the Content Manager | `21a89b474` |
| Raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 | A 404 from the admin account is neither of the failures QC-40 names, so the moment can stay owed with no way to end it | `gh api repos/<owner>/<repository>/dependency-graph/sbom/generate-report` printed 404 in this run; `products/tracker17/docs/nfdr.md:L393-L397` | `a646961ce` |
| Modify a station | `tracker17 · shukuba · 2026-10-30_second-tracker-refusal` | Its description stated the absent lock as current; its reached-when is unchanged | `tracker17 · shukuba · 2026-10-30_second-tracker-refusal` (line 7), (line 12) | `4bba2995a` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-30_second-tracker-refusal` | All five bars hold now; the close is the Scrum Master's. Bars 1 and 2 are tests that assert the line, exit 1, nothing served, unchanged record, the first answering, and a serve after a kill | Clone at `281853622`: `pytest tests/` 2768 passed, `tests/e2e/` 121 passed. Tests copied onto `dd990dab3`: 4 failed, 1 passed of the second-or-kill selection, the named two among the failures. `grep -c -i -F "another tracker" products/tracker17/README.md` printed 2; passage at `products/tracker17/README.md:L71-L79` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, item 2 | Reachable where it stands. S-8 needs the page and console line (UX-F11, UX-S9, SM-6), the set-aside restart and the one test per break: all the station's own work. The setup section it points to exists, and the location claim it runs under landed here | `products/tracker17/docs/SDD.md:L1147-L1160`, `:L240`; `products/tracker17/README.md:L81-L97` |
| `products/tracker17/docs/what_left.md` | Its empty marker holds by its own test: the PRD asks that the tracker say so plainly and never overwrite, and today's stop does. The page is SRS and UXD work, which the file does not list. The README's sentence "Nothing that the tracker was defined to do is left to build" reads wider than that, and `readme-status` owns it | `products/tracker17/docs/PRD.md:L185-L187`; `products/tracker17/main.py:L123-L130`; `products/tracker17/README.md:L11`; `<CORE>/doctrine/setup/kensaiapp_structure.md` § The what-left file |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists and verifies QC-40 by review, as earlier refines here found. An item would ask it to state what it states | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:L399-L400` |
| `products/tracker17/persistence/location_use.py`, a location missing its parents | The form does not occur: the one location is `data` beside the code, and `main` takes no location | `grep -n DEFAULT_LOCATION products/tracker17/main.py products/tracker17/persistence/saved_data.py` printed `main.py:157` and `saved_data.py:25`, the path `parent.parent / "data"` |
| `products/tracker17/tests/integration/test_single_tracker.py`, a message on restart after Ctrl-C | The form does not occur: nothing in the start prints about an earlier tracker, and the kill path has this assertion | `products/tracker17/main.py:L110-L115`, `:L146-L152`; `code-integrity-report.md` § The tests added or fixed |
| Python packet, `conventions.md` `__version__` clause | About the packet, not this route. No module of the product carries the marker, and the integrity report names the owner | `code-integrity-report.md` § Calls made, call 1 |
| `products/tracker17/persistence/location_use.py`, rollback with no claim | The form does not occur: it needs a failed open and another start's claim in the instant between `mkdir` and the open, and no run has shown it | `code-integrity-report.md` § Calls made, call 4; the suite above |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, a retire | Item 2 is unticked, so the seed is not fully walked | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 20) |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, re-aims | One re-aim of item 2, this run's, and no earlier one, so the bar stays below the two that would send it to the owner | Moves row 1 |

## Absent

The closing commit's `Deferred:` lines and the plan's § Corrections owed while there, as in Read. The halt report: a sealed unit produces none. `<CORE>/launchers/chain-product/launcher.sh` was not run here, so whether the sweep's two items need the owner's answer is the sweep's to say.
