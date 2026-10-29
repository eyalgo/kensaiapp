# 宿場 Shukuba refine — `2026-10-29_uv-lock-and-pins-test`

*Unit `2026-10-29_uv-lock-and-pins-test`, sealed Tobiishi, reviewed 2026-10-29. Key named by the caller (the PM context names the same key, `Sealed`).
Station `lock-and-pins-test` (root). Seed `2026-10-29_the-suite-runs-on-uv`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-29_lock-and-pins-test` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 3 change-local (CP-662 second clause has no Examples row; CP-664 byte-identical demand not logged as a gap; a design verdict pre-written in an Examples row) |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 2 change-local (the QC-39 rewrite named without a divergence entry; CP-663's "none skipped" has no checking row) |
| flow findings | `flow_findings/development-content.md` | 0 blocking · 1 change-local (the manifest note carries two RT-4 claims the spec does not ask for, recorded with reason) |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 2 change-local (no owner recorded for the QC-39 correction; failure edges held only by disposable probes, by design) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 2 change-local (two rule-discrimination probes cannot fail alone; one covered-by claim rests on an unfailable probe, closed by the integrity pass) · 1 skill-general (developer vs design on whether an in-repo product's `docs/` is in reach → kaizen candidate, not route work) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`, 2698 passed; one style fix (`-> None` removed); calls: the developer's QC-39 edit stands, the README is left for the next station |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 12): dependency audit did not run, the NFDR names none — the NFDR already says so, no companion owed (Considered row 3). Upkeep row for RN-33 corrected in place to name `pyproject.toml` and `uv.lock` |
| developer's closing commit | `<a commit not in the public history>` | one divergence (`-> None` kept to match neighbours, later removed by integrity); edited NFDR QC-39 on the branch as mislabelled-outside-reach |
| deferred decisions | `deferred_decisions.md` | one entry, the README's suite instructions on uv, `Owner: none` — carried by `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (line 18), station `readme-on-uv` (Considered row 4) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — the body has no line beginning `Deferred:` (`git log -1 --format=%B <a commit not in the public history> \| grep '^Deferred:'` → nothing) |
| corrections owed | `tl_instruction.md` § Corrections owed while there | two *Owed outside this change's reach* lines: NFDR QC-39 — the record already says it (Considered row 5); README `:95-103` — carried by `readme-on-uv` (Considered row 4) |
| work handed on | `change_spec.md` § Out of Scope | README suite section and "How it's built" → `readme-on-uv`; card Setup/Test commands → `project-card-commands`; QC-40's dependency-graph confirmation → QC-40's own next `development-design` review (Considered row 6); QC-60's 3.11 run → held outside this seed (seed § Out); the rest only fences |

## Upstream

`git log --since=2026-10-29T19:20:28+01:00 --name-status -- products/tracker17/docs/` → two commits, both this unit's: `79a743286` and `5eb5ec557`, `M products/tracker17/docs/nfdr.md` (QC-39 reworded to "met"). No live `*_open_issues.md` under `products/tracker17/docs/` (`find … -name '*_open_issues.md' -not -path '*/trail/*'` → nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no definition chain in flight. `system/logs/chain-change-tracker17-state.json` carries this key with only the `refine` step pending — this run. No open unit at `journey/tobiishi/` root (`ls` → `trail` only).

## Moves

None — no move was owed; see below. (The seed file became a folder to hold these two files, in this run's commit.)

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-29_lock-and-pins-test` | All four reached-when items hold on `main`; the close is the Scrum Master's, owed | station (lines 13-16); fresh clone at `3553cf36d`, product root: `uv lock --check` → exit 0, 17 packages; `ls tests/requirements.txt` → no such file; the grep → nothing, exit 1; `uv lock` removed → `1 failed, 3 passed`; `pytest>=9` → `2 failed, 2 passed`; `uv sync --locked` → 0; `uv run pytest tests/unit tests/architecture` → `686 passed` |
| `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (line 18), `readme-on-uv` | Next unticked station, walkable where it stands: what it requires is `uv.lock` (now on `main`) and the README text, which is its own work. Its bar has no refine re-aim | `products/tracker17/docs/SDD.md:299-318` (RT-4: install uv first, `uv sync --locked`, `uv run pytest tests/`, `uv run pytest tests/e2e/`, `uv run playwright install chromium`); `products/tracker17/README.md:95-103`, `:135` still venv/pip |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists and verifies QC-40 by review, as earlier refines on this product found; no companion owed | `security-report.md` (line 12); `products/tracker17/docs/nfdr.md:383-391` |
| the README record gap (`deferred_decisions.md`, plan correction line 2) | Already carried by `readme-on-uv`, whose bar names the suite section and "How it's built"; `README.md:99` names a deleted file until then | `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (line 18); `deferred_decisions.md` (lines 13-18); `git grep -n requirements.txt products/tracker17` → `README.md:99` live, the rest history in Review Notes |
| `products/tracker17/docs/nfdr.md` QC-39 (plan correction line 1) | The record already says what the line asks: QC-39 reads "The entry is met", names the new test and keeps the `9219be1e1` observation as history. No companion | `products/tracker17/docs/nfdr.md:352-367`; `code-integrity-report.md` § Calls made 1 |
| QC-40's dependency-graph confirmation, handed on by the spec | Owned by QC-40's own *verified by*: "The first review after `uv.lock` is on `main`" — the next unit's `development-design` review carries it; no route line needed | `change_spec.md` (line 178); `products/tracker17/docs/nfdr.md:387-390` |
| flow findings, change-local (10) | Each ends with this unit; none names unowned work or a failing gate | `flow_findings/*.md`; integrity pass 2698 passed |
| flow finding, skill-general (developer `docs/` reach) | Machinery, not this product's route; raised as kaizen candidate `developer-docs-record-reach` | `flow_findings/development-implementation.md` finding 3 |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Untouched by this unit; independent of the active seed | its § Relation to existing work |
| `tracker17 · shukuba · 2026-10-29_project-card-commands` (seed line 19) | Can follow `readme-on-uv`; needs only `uv.lock`, now on `main` | `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (line 19); `system/projects/tracker17/project.md` Setup `none`, Test `pytest products/tracker17/tests/` |

## Absent

- The closing commit's `Deferred:` lines — none in `<a commit not in the public history>`.
- Live companions under `products/tracker17/docs/` — none.
- `journey/shukuba/parked/` — empty.
