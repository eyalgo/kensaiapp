# Change Spec — the timed run covers a status move

**Date:** 2026-10-21
**Category:** nfdr
**Behaviour:** changing
**Request:** Add the status move to the timed run, `tests/timed_run.py`, so the run times every action SRS NFR-1 lists that the product now has (NFDR QC-48). The run does not time a status move today; the status workflow added the move and left it out. Time one move, in the run's existing manner: its own fixture of 1,000 tasks with 20 comments each, a same-origin submission, and a failure on a refused or failed action. Time the POST and the landing page it lands on apart, and as a total, each against the existing limit (`LIMIT_SECONDS`, 1.0 second). The move counts only when it happened: the run fails (non-zero) if the task's saved status is not the one moved to, or if the landing page does not show the move's result. Print the fixture used for the move, with the 1,000 tasks, the 20 comments each and the text lengths. Cover this in `tests/integration/test_timed_run.py`: tests that feed the harness a refused move and a landing page that does not show the result and find the non-zero verdict, and a test on the printed fixture report. Done when `python3 tests/timed_run.py`, run from `products/tracker17` in a fresh clone checked out at the commit under test, exits 0 and prints a timed POST, a timed landing page and a total for a move, each under 1.0 second (it prints none for a move before the work); `pytest products/tracker17/tests/` exits 0 with every existing test in `tests/integration/test_timed_run.py` still present and passing; and `pytest products/tracker17/tests/e2e/` exits 0 where layer 5 runs (NFDR § 9). Sizing: one capability (the timed run covers a move), one merge. The move to `cancelled` with its confirmation is not timed unless its press path is the plain move's. No product code under `domain/`, `application/`, `persistence/` or `web/` may change to make a timing pass; a timing over the limit is a finding about the saved data's design, not something to edit away. The limit stays 1.0 second, no existing timed action's bar or its test is loosened, deleted or skipped, and no action beyond the status move is added. Deleting a task with its comments, and the unreadable-data pages, are other stations' work.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern it routes

---

## Change Summary

The timed run of NFDR QC-48 gains one action, a status move of a task pressed from its project's task
list, timed at full volume as a POST, its landing page and their total, and counted only when the move
was saved and its landing shows it. Paths below are relative to the product root, the directory
`project.md` `Product path:` names.

**Sizing.** The acceptance boundary is NFDR QC-48's timed run covering every action SRS NFR-1 lists
that the product has, which SDD § 6 `status-moves` *Command* states for the move ("`python3
tests/timed_run.py` exits 0 and covers a move"). Every part of the request maps to that one boundary:
the move's measurement, its failure verdicts, its fixture line and the tests that prove them. One
capability, one merge.

---

## Rules

### The move the run times

- **CP-371:** `python3 tests/timed_run.py`, run from the product root, times one status move: a task
  whose saved status is `todo` moved to `in-progress`, by the submission that task's `in-progress`
  button sends from its row on its project's task list. The submission is marked
  `Sec-Fetch-Site: same-origin`, as NFDR QC-32 requires of every submission the run sends without a
  browser. The run sends no other submission for the move: no move to `cancelled` and no
  confirmation.
- **CP-372:** The move runs on a fixture of its own, holding 1,000 tasks across all projects with 20
  comments on every task, at ordinary text lengths (NFDR QC-48; SRS NFR-1, RN-22). The fixture is
  saved in a location of its own inside the run's temporary directory (SDD § 4 TS-5). That location
  is distinct from every other fixture the run uses. The product's own `data/` directory is as the
  run found it, either absent or unchanged byte for byte.

### What the run prints for the move

- **CP-373:** The run prints every line it prints today, unchanged and in today's order. The last of
  them today is the `assignee remove total at 1000 tasks: …` row. After those lines it prints exactly
  four more, in this order, and nothing after them:
  1. `move fixture: {tasks} tasks, {per task} comments each ({all} in all); title of {T} characters, comment of {C} characters`
  2. `move a task at 1000 tasks: {ms} ms{problems}`
  3. `move landing page at 1000 tasks: {ms} ms{problems}`
  4. `move total at 1000 tasks: {ms} ms{problems}`
- **CP-374:** In the fixture line, `{tasks}` is the number of tasks the move's fixture holds and
  `{per task}` is the number of comments on each of them. `{all}` is those two multiplied. `{T}` is
  the length of the moved task's title, and `{C}` is the length of the moved task's first comment.
  Every value is read from the fixture as loaded back from its saved location, never from the run's
  own settings. A character is one code point (ADR-0007). On the run's own fixture the line begins
  `move fixture: 1000 tasks, 20 comments each (20000 in all); `.
- **CP-375:** In each row, `{ms}` is the row's time in milliseconds with one decimal place. When the
  row passes, `{problems}` is empty. When it does not, `{problems}` is ` — ` followed by the row's
  problems joined by `, `, in this order: `refused or failed`, then `at or over 1 s`. For example:
  `move a task at 1000 tasks: 1000.0 ms — refused or failed, at or over 1 s`.

### What each row measures and when it counts

- **CP-376:** The POST row times the one move submission, from sending it to receiving its answer.
  The landing row times one GET of the address that answer redirects to, from sending it to receiving
  its answer. The total row is the POST row's time plus the landing row's time. It is not the time
  from the start of the first to the end of the second. No row's time includes the run reading the
  saved data back to check it.
- **CP-377:** The move counts as done only when both of these hold:
  (a) the submission is answered with a 303 whose `Location` is exactly
  `/projects/{project id}?moved=in-progress&move_task={task id}`, for the moved task's project and
  the moved task;
  (b) the saved data, read back from the fixture's location after the answer, is the fixture as it
  was loaded before the move, with the moved task's status `in-progress` and nothing else different.
  Every other task is unchanged, and so are the moved task's other fields, the projects, the
  assignee list and the operator's name.
  When either fails, the POST row carries `refused or failed`. This covers every answer other than
  (a)'s exact one: a refusal, a failure to save, a different address, a different status code.
- **CP-378:** The landing counts as done only when its GET is answered with a 200 and the page carries
  the line `You moved '{title}' to in-progress.`, where `{title}` is the moved task's title escaped
  the way the page shows text. When either fails, the landing row carries `refused or failed`.
- **CP-379:** When the submission's answer is not a 303 to CP-377 (a)'s exact address, the run does
  not request the landing. The landing row then reads `0.0 ms — refused or failed`, and the total
  row's time is the POST row's time. The total row carries `refused or failed` whenever the POST row
  or the landing row carries it.
- **CP-380:** Each of the three move rows is held to the same limit as every existing row, 1.0 second.
  A row whose time is 1.0 second or more carries `at or over 1 s`. This applies to the total too,
  even when both of its parts are under the limit.
- **CP-381:** The run exits 1 when any of its rows carries a problem, and that includes any of the
  three move rows. It exits 0 only when no row carries a problem.

### What does not change

- **CP-382:** No file under `domain/`, `application/`, `persistence/` or `web/` changes. A move row at
  or over the limit is reported as a finding about the saved data's design, in the printed row and in
  the exit status. It is not edited away.
- **CP-383:** The limit stays 1.0 second for every row. No existing row's label, place in the output,
  limit or done-check changes. No existing test in `tests/integration/test_timed_run.py` is deleted,
  renamed, skipped or loosened. CP-391 names the existing tests whose supplied inputs or expected
  lines change. The run times no action other than the move beyond the ones it times today.

### The tests that prove the move's measurement

`tests/integration/test_timed_run.py` is the file the request names, and the file the harness names
as its checker (`tests/timed_run.py:22-23`). It gains these:

- **CP-384:** A test that gives the move measurement a move the product refuses, and finds the POST
  row and the total row carrying `refused or failed`, the landing row reading
  `0.0 ms — refused or failed`, and a verdict of 1.
- **CP-385:** A test that gives the move measurement a submission that counts as done (CP-377), then a
  landing page that does not carry CP-378's line. It finds the landing row and the total row carrying
  `refused or failed`, and a verdict of 1.
- **CP-386:** A test on the printed fixture line. On the run's own fixture, the line is exactly
  CP-374's, with the values that fixture holds. On a fixture with a different number of tasks and of
  comments per task, and whose moved task has a title and a first comment containing characters
  outside ASCII, the line states that fixture's values, counted in code points.

### The commands that pass at the end

- **CP-387:** In a fresh clone checked out at the commit under test, `python3 tests/timed_run.py` run
  from the product root exits 0. It prints the four lines of CP-373 for the move, each of the three
  rows under 1.0 second and none carrying a problem. Today it prints no line starting `move`.
- **CP-388:** `pytest products/tracker17/tests/`, the card's `Test command:` run from the worktree
  root, exits 0. Every test `tests/integration/test_timed_run.py` holds today is still there under its
  own name and passes.
- **CP-389:** `pytest products/tracker17/tests/e2e/` exits 0 wherever layer 5 runs (NFDR § 9).
- **CP-390:** NFDR QC-62's three commands each exit 0, run from the product root inside SDD § 4
  RT-4's virtual environment at the versions QC-39 pins (`tests/requirements.txt`). They are
  `ruff format --check .`, `ruff check .` and
  `mypy main.py errors.py domain application persistence web`. Ruff's two commands cover `tests/`,
  so they reach both files this change edits.
- **CP-391:** The harness and its tests run on Python 3.11 (NFDR QC-60). QC-60's *verified by* makes
  this a review at `development-design`.

### Existing tests that change

- **CP-392:** These existing tests in `tests/integration/test_timed_run.py` give the whole run a fixed,
  finite list of timer readings:
  - `test_timed_run_fails_when_only_the_edit_fails`
  - `test_timed_run_fails_when_only_a_label_action_fails`
  - `test_full_timed_run_fails_when_only_name_measurement_fails`
  - `test_timed_run_fails_when_only_a_new_action_total_reaches_limit`, all three cases
  - `test_timed_run_propagates_new_submission_and_landing_timing_failures`, all three cases
  - the four tests on the module's whole-run fixture:
    `test_timed_run_appends_exactly_three_ordered_action_blocks`,
    `test_new_timed_fixtures_are_independent_and_preserve_name_save_precondition`,
    `test_new_timed_actions_leave_product_data_unchanged` and
    `test_timed_run_reports_actual_fixture_lengths_for_all_three_actions`

  Each one changes only by the readings the move's timing takes, added after the readings it supplies
  today and all under the limit. Every assertion it makes stays as it is.
  `test_timed_run_appends_exactly_three_ordered_action_blocks` changes in one more way: its expected
  lines gain CP-373's four move lines after the three blocks. It keeps asserting that every existing
  line keeps its label and its place, that the three blocks follow in their order, that the run exits
  0, and that no line carries `over` or `refused`. The whole output is still asserted to be exactly
  those lines and no more, either by this test or by one beside it.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| The run today, before the change (CP-387) | Exits 0. Its last line is `assignee remove total at 1000 tasks: …` and no line starts `move`. |
| The run after the change, every action fast (CP-371 to CP-376, CP-381, CP-387) | After `assignee remove total at 1000 tasks: …` it prints `move fixture: 1000 tasks, 20 comments each (20000 in all); title of {T} characters, comment of {C} characters`, then `move a task at 1000 tasks: 26.5 ms`, `move landing page at 1000 tasks: 3.1 ms` and `move total at 1000 tasks: 29.6 ms` (illustrative times), and exits 0. |
| The move is saved and lands (CP-377, CP-378) | The POST is answered 303 to `/projects/1?moved=in-progress&move_task={task id}`. The saved data is the fixture with only that task's status changed to `in-progress`. The GET of that address is 200 and carries `You moved '{title}' to in-progress.`. All three rows pass. |
| The product refuses the move, e.g. a task already `in-progress` asked to move to `in-progress` (CP-377, CP-379, CP-381, CP-384) | The answer is a 303 to a `move_refused=` address, which is not CP-377's. The rows read `move a task at 1000 tasks: {ms} ms — refused or failed`, `move landing page at 1000 tasks: 0.0 ms — refused or failed` and `move total at 1000 tasks: {same ms} ms — refused or failed`. The verdict is 1 and the run exits 1. |
| The submission is answered as done, but the saved data has a second task changed too (CP-377) | The POST row carries `refused or failed`. The landing is still requested, because the address was the exact one, and the total row carries `refused or failed`. Exit 1. |
| The landing is 200 but does not carry the moved line (CP-378, CP-385) | The landing row and the total row carry `refused or failed`. Verdict 1, exit 1. |
| A submission sent without the same-origin mark (CP-371) | The product answers 403 and saves nothing, so the move would count as refused (CP-377). A run that left out the mark cannot pass by timing refusals. |
| The move total reaches 1.0 s while its POST and landing are each under it (CP-380) | Only `move total at 1000 tasks: 1000.0 ms — at or over 1 s` carries a problem. Exit 1. |
| The POST takes 1.5 s (CP-375, CP-380) | `move a task at 1000 tasks: 1500.0 ms — at or over 1 s`, and the total row also carries `at or over 1 s`. Exit 1. |
| The fixture line on a varied fixture: 300 tasks of 3 comments, title `Plan 😀😀`, first comment `Note 😀` (CP-374, CP-386) | `move fixture: 300 tasks, 3 comments each (900 in all); title of 7 characters, comment of 6 characters` |
| A move row is over the limit on the owner's machine (CP-382) | The row is printed with `at or over 1 s` and the run exits 1. No file under `domain/`, `application/`, `persistence/` or `web/` changes to bring it under. |
| After the whole run (CP-372) | The move's fixture sits in its own location under the run's temporary directory, holding 1,000 tasks with one changed status. The product's `data/` directory is as it was. |
| A test that today gives the whole run a finite list of timer readings (CP-383, CP-392) | It supplies the move's readings after its existing ones, and every assertion it made before still holds. |
| QC-62's three commands after the change (CP-390) | Each exits 0. |
| `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` after the change (CP-388, CP-389) | Each exits 0, with every existing timed-run test present under its own name. |
| Python 3.11 (CP-391) | No example row. QC-60 is a review gate with no command, and `development-design` checks it. |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Today the run times no move and exits 0 (CP-373, CP-387) | `python3 tests/timed_run.py` from the product root in a fresh clone of the repository checked out at `8906d1e6c` (this branch's base) | Exit 0. 80 lines, with the last `assignee remove total at 1000 tasks: 36.9 ms`. `grep -c '^move'` on the output gave 0. |
| A list-row press of `in-progress` on a `todo` task at full volume is answered 303 to `/projects/1?moved=in-progress&move_task={id}`, saves only that status change, and lands on a 200 page carrying `You moved '{title}' to in-progress.` (CP-371, CP-377, CP-378) | A probe in the same clone. It used the harness's own fixture (`open_task_volume`: a real `SavedData` in a temporary directory, loaded back, a real `Site`/`Tracker` with the real clock) and the harness's `FORM_HEADERS` (same-origin), and sent `POST /tasks/500/move` with `status=in-progress&place=list`. These are the conditions CP-371 and CP-372 fix. | `303 /projects/1?moved=in-progress&move_task=500`. The saved data equals the fixture with only task 500's status replaced. The GET gave 200 with the line present and `Cache-Control: no-store`. POST 26.5 ms, landing 3.1 ms. |
| The task's-page press lands on a far smaller page than the list press (Locked Answer, Gap 1) | The same probe with `place=task`, and a GET of `/projects/1` and `/tasks/500` on the fixture | Task-page landing `/tasks/500?moved=in-progress&move_task=500`, 0.4 ms. `/projects/1` is 712,517 bytes and carries 1,250 move forms, one per allowed move on every row. `/tasks/500` is 7,649 bytes and carries 2. |
| The fixture holds `todo` tasks: every task whose number is divisible by 4 (CP-371) | `tests/timed_run.py:72` and `:184` (`SEED_STATUSES[number % len(SEED_STATUSES)]`), and the probe | Task 500 loaded as `todo`. |
| The product refuses a move to the status a task already has, with a 303 to a different address and no save (Examples, CP-384) | The probe: `POST /tasks/500/move` with `status=todo&place=task` on the `todo` task | `303 /tasks/500?move_refused=not-allowed&move_task=500`. Saved data equals the fixture. |
| An unmarked submission is refused (Examples; QC-32) | The probe: the same POST without `Sec-Fetch-Site` | 403. Saved data unchanged. |
| A move to `cancelled` from a row is two submissions, not the plain move's press path (Out of Scope) | Read `web/routes.py:744-747`, where the first press redirects to the confirmation with `move_confirm=cancelled` and saves nothing, and `:245-247`, where the save happens at `/tasks/{id}/move/confirm` | As described. This is a code reading and no rule rests on a verdict from it. |
| Existing tests that give `main` finite timer readings break once the move reads the run's timer, and the order test breaks on any added line (CP-392) | A stand-in post-change tree in the scratch clone. `main` gained, after the three new actions, a block printing `move fixture: stand-in` and three passing rows labelled as CP-373. Then `python3 -m pytest products/tracker17/tests/integration/test_timed_run.py` ran twice: (1) with the block taking four readings from the handed timer, (2) with the block taking none. | (1) 9 failed, 4 errors, 61 passed: the nine cases and four whole-run-fixture tests CP-392 lists, all from the timer running out of readings. (2) 1 failed, 73 passed: only `test_timed_run_appends_exactly_three_ordered_action_blocks`, on its exact-list assertion. The stand-in was reverted, and the clone's `git status` was clean. |
| No fixed word in the four new lines contains `over` or `refused`, which existing tests search lines for (CP-373) | `tests/integration/test_timed_run.py:108`, `:167`, `:239` and `:401` (`"over" in line`, `"refused" not in report`), against CP-373's labels and the seeded title `Seeded task {n}: write up the work for this part` | None of them contains either word. |
| The whole suite passes today (CP-388) | `python3 -m pytest -q products/tracker17/tests/` from the clone's root | `1316 passed`. |
| QC-62's three commands pass today, including over `tests/` (CP-390) | A fresh venv with only QC-39's pins of the two tools (`ruff==0.16.10`, `mypy==2.4.0`), each command run from the clone's product root | `ruff format --check .` reported "216 files already formatted" and exited 0. `ruff check .` reported "All checks passed!" and exited 0. `mypy main.py errors.py domain application persistence web` reported "Success: no issues found in 24 source files" and exited 0. |
| Language rendering | No rule pins output that renders a language-level fact. The millisecond figure, the row shape and the status word are formats the product chooses, and "a character is one code point" is ADR-0007's, a product record. | No rendering rows. The Python packet was opened and fixes none of these renderings. |

---

## Out of Scope

- The move to `cancelled` with its confirmation. Its press path is two submissions, the first only
  opening the confirmation (`web/routes.py:744-747`), so it is not the plain move's.
- A move pressed from the task's own page. Its landing, the task's page, is not timed here (Locked
  Answer, Gap 1).
- The other plain moves, `in-progress` to `done` and `in-progress` to `todo`. They send the same
  submission from the same row and land on the same list.
- Every action NFR-1 lists that the product does not have yet: deleting, filtering, sorting and
  opening a summary (`docs/what_left.md`). The SDD's later slices bring each into the run with its
  action (SDD § 6, the `narrow-and-sort`, summary and deletion slices' *Command* lines). Deleting a
  task with its comments, and the unreadable-data pages, are other stations' work, as the request
  says.
- Any change to the product's code, to the 1.0-second limit, or to an existing row (CP-382, CP-383).
- A fixture whose tasks hold unequal numbers of comments. The move's own fixture never has one, and
  the fixture line states one count for every task.

---

## Locked Answers (the divergence record — self-review 2026-10-21)

- **Gap 1 — which press is timed (b):** the list-row press, landing on the project's task list. The
  task's-page press is not timed. *Reason:* the request asks for one move and leaves the place open. A
  plain move lands on one of two pages. The task list shows every task in the project, so at
  NFR-1's volume it is the page that grows with the data: 712,517 bytes against the task page's
  7,649 (Verified Claims). Timing the list press is the reading under which a slow landing cannot go
  unmeasured. Timing the other place later adds a row and removes none.
- **Gap 2 — which move (b):** `todo` to `in-progress`. *Reason:* it is the first move the workflow
  offers from a new task's status, it is one submission, and every plain move has the same press
  path. The request rules out `cancelled`.
- **Gap 3 — what "happened" means (b):** the whole saved state must equal the fixture with only the
  moved task's status changed (CP-377 (b)). The request asked only that the task's saved status be
  the one moved to. *Reason:* under the request's check alone, a move that also changed another task
  or field would count as done. This check is stricter, it rejects nothing a correct move does, and it
  is the check the run already makes for the comment add and both assignee actions.
- **Gap 4 — what "shows the move's result" means (b):** the page carries the completion line
  `You moved '{title}' to in-progress.` (CP-378). *Reason:* that line names the task and its new
  status, and it is the page's own statement of the result (`docs/CONTENT.md:54`, "Name the actor and
  the resulting state in every line that reports an action").
- **Gap 5 — the rows when the submission is not done (b):** the landing is not requested, reads
  `0.0 ms — refused or failed`, and the total is the POST's time (CP-379). *Reason:* without the exact
  address there is no landing that belongs to this move. A row that says so is clearer than a timed
  GET of a page the move never produced. Every existing three-row action already reports this case
  this way.
- **Gap 6 — the wording of the four lines (b):** the labels in CP-373, and a fixture line stating the
  moved task's title length and first-comment length. *Reason:* the move sends no typed text, so the
  text lengths RN-22 asks the run to state are the ordinary lengths of the data it acts on. The labels
  contain neither `over` nor `refused`, the two words existing tests look for in a failing line
  (Verified Claims).
- **Gap 7 — where the move's lines go (b):** after every existing line (CP-373). *Reason:* the
  request requires every existing line to stay as it is, and appending is the one placement that
  moves no existing line.
- **Gap 8 — what the fixture-report test checks (b):** a varied fixture as well as the run's own
  (CP-386). *Reason:* on the run's own fixture, values read from the fixture and values copied from
  the run's settings are identical. Only a different fixture shows which one the line reports.
- **Gap 9 — QC-62 folded in (e):** CP-390 states Ruff's format check, Ruff's lint and mypy, which the
  request leaves out. *Reason:* NFDR QC-62 binds the tree, and Ruff's two commands run over `tests/`,
  where both of this change's files are.
- **Gap 10 — QC-60 folded in (e):** CP-391 states the Python 3.11 floor, which the request leaves out.
  *Reason:* NFDR QC-60 binds the tracker's tests, and its check is a review at `development-design`
  for a change that uses a language or library feature. This change writes Python.
- **Gap 11 — existing tests named as changing (f):** CP-392's tests change by the readings the move
  takes and, for the order test, by its expected lines. The request said every existing test stays
  "present and passing" and is not "loosened". *Reason:* the stand-in run (Verified Claims) shows that
  no harness that times the move with the timer a test hands it leaves these tests unchanged. Each one
  supplies a fixed number of readings, and the order test asserts the exact list of lines. Each keeps
  every assertion it makes, so none is loosened. Each keeps its name, so each is still present.
