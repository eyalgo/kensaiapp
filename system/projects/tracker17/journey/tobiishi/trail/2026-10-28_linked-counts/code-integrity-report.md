# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_linked-counts`, a project's Summary counts as links
into its filtered task list. **Mode:** workflow. **Outcome:** clean pass. Three tests were
tightened from the intent, and the code already met them. No code was changed.

## Deferrals

None. The closing marker (`<a commit not in the public history>`, `developer: 2026-10-28_linked-counts — implementation
complete`) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The change's product commits on `2026-10-28_linked-counts` against `main`, under
`products/tracker17/`:

- `web/pages.py`: the count-link values (`_CountName`, `_CountLink`, `_SummaryRow`), the
  eighteen published names, `_summary_cell`, `_summary_group` and `summary_page`, and the shared
  `OVERDUE_VALUE`.
- `web/style.css`: the `.summary-group .count-link` target geometry.
- `tests/timed_run.py`: the structural Summary row reader (`_SummaryRows`, `summary_rows`) and its
  use in `_summary_landing_shows`.
- `tests/integration/test_timed_run.py`, `test_summary_pages.py`, `test_summary_routes.py`,
  `test_pages.py` and `tests/e2e/test_summary.py`.

## The intent it was checked against

`tl_instruction.md` (Tasks 1 and 2, every `#### Behaviours to verify` line and the two
`#### Held by review` items), `change_spec.md` (CP-513 to CP-528 and its Examples),
`change_text.md` (the eighteen names, word for word) and `change_design.md` §§ 2–5. As context,
`docs/fdr.md` R-82, R-99, R-101 and R-106, the rules the spec cites. They are held by T03, T09,
T07 and T08.

## Placement

The parts table is `docs/SDD.md` § 3, *The parts*.

- Link selection, address building, name choice and cell markup are in `web/pages.py`. Owning
  part: `web` ("the addresses of pages … building each whole HTML page"). They were already there.
  They decide no count, no membership and no overdue rule, so nothing belongs in `domain`.
- The count-link style is in `web/style.css`. Owning part: `web` ("the one stylesheet"). It was
  already there.
- The Summary row reader is in `tests/timed_run.py`. It is not runtime logic, so no part owns it.
  It sits in the `tests/` boundary that `change_design.md` § 3 sub-job B and the SDD's units note
  place it in.

Nothing was moved, and no `… — placement` commit was made. `web` gains no import beyond
`Priority`, which comes through `application`, as QC-16 requires.

## The tests added or fixed

All three are tightenings of tests the plan names. Each one was derived from the spec and would
have passed on wrong code before.

1. **`test_summary_routes.py::test_zero_links_on_populated_project_show_no_match`** (T04, CP-518).
   Before, it checked only that one filter control was set on each of Beta's seven zero
   destinations, and checked the address of the `done` link alone. Now it asserts that the seven
   zero links are Beta's own one-choice addresses, in page order. It also asserts that each answers
   200 and that each destination's controls show exactly that link's choice (`lone(field, choice)`).
   CP-518 requires the no-match state "with the choice shown in the controls". A link that opened
   the wrong filter would also land on no-match with one control set, so the old test could not
   tell the two apart.
2. **`test_summary_routes.py::test_empty_project_count_links_keep_no_tasks_state`** (T05,
   CP-518). Before, it checked only that a `no-tasks` paragraph existed. Now it asserts the
   paragraph is exactly `This project has no tasks yet. Give the first task a title and press
   Add.`, the words CP-518 states. It also asserts that Gamma's nine links are Gamma's own nine
   addresses with the numeral `0`, and that each answers 200.
3. **`test_summary_pages.py::test_summary_count_names_identify_zero_one_and_many_tasks`** (T06,
   CP-522). Before, the rule that equal names mean equal addresses ran only on a populated Summary.
   Now it also runs on an empty project's page. CP-522 singles that page out: nine `0` links, and
   two `Tasks` links that may share a name because they share `/projects/3`. The test also asserts
   that the two `Tasks` links are present and that the nine zero names are distinct.

**The tightenings catch a wrong link.** On a copy of `web/pages.py` whose overdue link chose
`filter_status=done`, tests 1 and 2 both failed. The old versions would have passed it. The file
was restored and checked unchanged with `git diff --quiet`.

Every other behaviour the plan lists already had a test that matched the intent, and those tests
were left alone. Each one was read against its line: T01–T03, T06–T18, the CP-516 query-leak edge,
the AC-13 extension, the header-address repair, and Task 1's bare, linked, forbidden, ambiguous,
midnight, full-volume and one-second checks in both accepted shapes. The two *Held by review*
items hold on reading. `web` formats supplied counts and addresses and computes no membership,
overdue or sort (CP-523). `measure_project_summary` still sends one Summary GET, and no timed
action or label was added (CP-527).

## The finding

No issues in the code. Every behaviour of the intent has a correct test, and the full suite passes.
Nothing was misplaced.

**One false claim in the developer's handoff.** The closing marker says the e2e suite "is inside
the 2090". It is not. The card's `Test command:` (`pytest products/tracker17/tests/`) does not
collect `tests/e2e/`, and the gated run's output names no `tests/e2e/` file. `change_spec.md`'s
Locked Answer e-1 already says so. CP-528 requires both suites, so this review ran the e2e suite
on its own: 93 passed (test evidence, below). Nothing is unproven. The seal and the PM should not
read the card's run as covering the browser.

## Calls made

1. **The harness clock in the midnight test stays monkeypatched.**
   - *Question:* `test_timed_run.py::test_timed_summary_accepts_a_run_that_crosses_midnight` still
     replaces `harness._local_today` with `monkeypatch.setattr`. `testing_python.md:31` says a
     seam is "a hand-written fake passed to the constructor — not `monkeypatch.setattr` on the
     module under test", and the packet's rule wins over the file's own style. Should this change
     fix it?
   - *Readings weighed:* (a) give `measure_project_summary` an injected clock and drop the patch;
     (b) keep the patch the file already held on `main`, and record the gap.
   - *Taken:* (b). `change_design.md` § 3 sub-job B fixes `measure_project_summary(*, site,
     saved_data, timer)` as unchanged. Adding a clock parameter changes an interface the design
     names, which this review may not do. The patch is older than this change, and the developer
     reused it rather than adding it.
   - *Whose document:* the Tech Lead's plan and the Architect's design, which own the harness's
     interface.
   - *If they rule the other way:* a later change gives the harness a clock seam and rewrites this
     test, and the other harness tests that read the day, to pass a fake clock. No behaviour of
     this change moves.

## Language resolution

- **Language:** Python, from step 1 of the chain, `project.md` `Languages: Python`.
- **Packet read:** `<CORE>/doctrine/engineering/languages/python/README.md`, which routes seven
  concerns. Used as the review bar here: `conventions.md` (100 columns, PEP 604 unions, annotated
  production functions, `@dataclass(frozen=True)` values, `Enum` for closed sets, a module given its
  collaborators), `quality_gates.md` (Ruff format and lint, mypy over the five parts) and
  `testing_python.md` (the hand-written-fake seam rule at `:31`).
- **Result:** the new code meets every one of them. The one divergence is the inherited
  monkeypatch, recorded under **Calls made** and left in place for the reason given there.
  `layout.md` and `errors_logging.md` bear on nothing here: no file was added and no error was
  written. `environment.md`: the product has no CI, so the gate tool chose the owner's Mac.

## Test evidence

- **The verdict run**, the full card through the gate tool:
  `locked_python.sh gate_suite.py run --worktree <change worktree> --project tracker17 --key
  2026-10-28_linked-counts --gate code-integrity --inputs <inputs>`. The inputs file had no CI,
  with the inventory quoted in it, no decision override, no amd64 requirement and no candidates.
  Exit 0. It printed the `Environment:` line above and `2090 passed in 164.64s`. Its error file was
  empty. It was the only full-card run in this review.
- **Targeted, before the gated run:** `pytest -q` on `test_summary_routes.py` and
  `test_summary_pages.py` gave 40 passed. The overdue-link mutation gave 2 failed, then the file
  was restored.
- **E2E (CP-528):** `pytest -q products/tracker17/tests/e2e/` gave 93 passed in 44.77s. It ran with
  the developer's tool venv (`/tmp/tracker17-tools.Nh3lxn/v`), because the system `python3` has no
  `playwright`.
- **Timed run (CP-527):** `python3 tests/timed_run.py` from the product root exited 0. Its last
  line is `open a project summary at 1000 tasks: 3.2 ms`, with Summary still last.
- **Quality gates (QC-62):** from the product root, `ruff format --check .` gave 247 files already
  formatted, `ruff check .` gave all checks passed, and `mypy main.py errors.py domain application
  persistence web` gave no issues in 27 source files.
- **Tree:** after the runs, `git status --short` showed only the two edited test files. The main
  checkout was clean.
