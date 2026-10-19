# 宿場 Shukuba refine — `2026-10-07_create-a-project-that-stays`

*Unit `2026-10-07_create-a-project-that-stays`, sealed Tobiishi, reviewed 2026-10-07. Key named by the caller.
Station `2026-10-07_a-project-that-stays` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `~/.kensaiapp/pins/20261007T090524Z-dod1sn/core/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2, 3, 4 |
| 2 | walk the next change | owner | `~/.kensaiapp/pins/20261007T090524Z-dod1sn/core/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/flow_findings/development-specs.md` | 0 blocking; 5 change-local (CP-14's whitespace set verified against `str.isspace()`, a mechanism in Locked Answers, uneven Examples, CP-9 vs CP-17, CP-8's widening unrecorded). All end with the unit |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking; 4 change-local: no maximum-size refusal case, the undecodable-body 400 unrecorded, no home for the Chromium install, CP-5's test holds before any project exists. The Chromium install lands with `setup-instructions` (UX-S1 prerequisites, `docs/UXD.md:307`) |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking; 3 change-local: `main()` run by no task, QC-60 stated in Task 3 only, Task 18's dependencies short. All end with the unit |
| flow findings | `…/flow_findings/development-content.md` | 0 blocking; 2 change-local: the header's `tracker17` breaks `CONTENT.md` § Terminology while `DESIGN.md` asks for it (Moves row 4); the opening sentence names the wrong destination for strings |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking; 6 change-local: an unreproducible count, missing revert notes, two edges found only by integrity, Compile unquoted, Ruff/mypy gate status contradicted between seats (Moves row 3), one unreproduced e2e failure (Considered row 3) |
| code-integrity report | `journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/code-integrity-report.md` | `Integrity: pass`; two `web/routes.py` bugs fixed in `691edf98b`; mypy's 3 errors and Ruff's 8 default-rule findings recorded, not acted on; one e2e failure, traceback not captured; README § Status left as found |
| developer's closing commit | `3c5569254` | `Suite: green`; three packet divergences (`typing.Protocol` ports, no `__version__`, tests by layer), each under the product records' precedence |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `3c5569254` | absent — `git show -s --format=%B 3c5569254 \| grep '^Deferred:'` printed nothing, exit 1 |
| corrections owed | `journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/tl_instruction.md:92-101` | Five *Owed outside this change's reach* lines: SDD TS-4 → `SDD_open_issues.md` § 5.1; NFDR QC-11 → `architecture_open_issues.md` § 3.1; SDD port → § 5.2; SDD Chromium questions → § 5.3; `README.md` § Status → seed line `setup-instructions` (Moves row 1), no companion template names `README.md` |
| work handed on | `journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/change_spec.md` § Out of Scope | Not-found page and address-taken message → open station's reached-when 2 and 3; README setup → `setup-instructions`; tasks, rename, delete → `tasks-in-a-project` and the uncut slices the seed's § Out names; the rest only fences |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>` → `2026-10-07T02:17:39+02:00`.
`git -C products/tracker17 log --since=2026-10-07T02:17:39+02:00 --name-status -- docs/` printed
nothing: no document moved since the seed was cut. No live `*_open_issues.md` under
`products/tracker17/docs/` before this run (`find … -name '*_open_issues.md' -not -path '*/trail/*'`
printed nothing).

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null` — no product
chain in flight. `journey/tobiishi/` holds no open unit; the change chain's one pending step is this
refine.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | tracker17 · nemawashi · 2026-10-07_first-project, line `setup-instructions` | README § Status says no code exists while `main.py` serves the tracker; UX-S1 has no Status section and no companion template names `README.md`, so only this station can carry it | `products/tracker17/README.md:9-11`; `docs/UXD.md:307`; `tl_instruction.md:101` | `9f2c40396` |
| raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1–5.3 (opened) | TS-4's clause is unmeetable before the last slice; the port is chosen; two Chromium open questions are answered by passing tests | `docs/SDD.md:427-429`, `:1580-1591`; `tests/architecture/test_trace.py:19`; `main.py:20`; `tests/e2e/test_first_project.py:94`, `:108` | `7ff2c2cce`, `57d26a892` |
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1–3.2 (opened) | QC-11's *verified by* has TS-4's defect; the product pins Ruff and mypy and no record says whether they gate, with mypy reporting 3 errors | `docs/nfdr.md:104-106`, `:477-479`; `pyproject.toml:13`, `:16`; `grep -i -E 'ruff\|mypy'` over `nfdr.md`, `SDD.md`, `adr/` printed nothing | `ae18b28fe` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1 (opened) | Two settled documents disagree on the header, and the page follows one | `web/pages.py:52`; `docs/CONTENT.md:144`; `docs/DESIGN.md:350`, `:427` | `d806bfba5` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-07_a-project-that-stays | Not reached, and walkable where it stands (shape 6): reached-when 2's not-found page (UXD UX-S10, SRS R-105) and 3's address-taken message (SRS R-4) are this station's own later units; 5 and 6 rest on tests and a lock that exist; 4's ignore holds. No refine has re-aimed it, so no owner's act | `change_spec.md` § Out of Scope; `tests/e2e/test_first_project.py:94-170`; `git -C products/tracker17 check-ignore -v data/tracker.json` → `.gitignore:26:data/`, exit 0 |
| `pytest tests/` on the product | Measured in a `git archive` copy: 183 passed, 1 failed — `test_data_is_ignored_by_version_control`, `git check-ignore` exit 128 because the copy is no git repository; the same check in the real checkout exits 0. Not a product failure | `python3 -m pytest products/tracker17/tests/ -q` in `/tmp/t17refine.el5M` |
| the unreproduced e2e failure | One failure, traceback not captured, then 108 passes: no measured failure to carry, and the next unit's own suite runs re-test it | `code-integrity-report.md` § Calls made 3 |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, comment-on-a-task, status-moves | No source moved under them, and nothing this unit found touches their scope | Upstream above |
| `products/tracker17/docs/SDD.md` RT-10 maximum-size refusal case | No occurrence: no failing run at the 51,000-byte bound is recorded or measured | `flow_findings/development-design.md`, first finding |

## Absent

`deferred_decisions.md` — the unit wrote none. `Deferred:` lines — none in `3c5569254`. The halt
report — a sealed unit produces none. `pytest tests/e2e/` was not re-run here: Playwright is not
installed outside the change worktree (`python3 -c 'import playwright'` → `ModuleNotFoundError`);
its pass is the one recorded at `691edf98b`, and no product code changed since
(`git diff --quiet 691edf98b HEAD -- <code paths>`, exit 0).
