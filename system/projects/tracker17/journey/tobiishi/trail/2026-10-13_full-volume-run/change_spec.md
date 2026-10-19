# Change Spec — The timed run covers the comment add and the People assignee add and remove

**Date:** 2026-10-13
**Category:** nfdr
**Behaviour:** changing
**Request:** Make the timed run cover every action NFR-1 lists, now that all of them exist. `tests/timed_run.py` today times project creation, task add, field edit, label add and remove, and the name save. Add the three it leaves out: adding a comment, adding an assignee on People, and removing one. Each one is done the way the run already does the others: on its own 1,000-task, 20-comments-each fixture, as a same-origin submission, timing the POST, the page it lands on, and the total, each under the 1.0-second limit. The run prints the fixture it used for each of the three, with the task count, the comments per task and the text lengths. A run that did not really do the action fails, and does not count as a pass: a comment not saved under the saved name, an assignee not added or removed in the saved state, a refused action, or a landing page that does not show the result. Tests in `tests/integration/test_timed_run.py` feed the harness a refused action and a landing that does not show the result for each of the three and find the non-zero verdict, and one test checks the printed fixture report. Run from `products/tracker17` in a fresh clone at the commit under test, `python3 tests/timed_run.py` exits 0, and `pytest products/tracker17/tests/` exits 0 with every existing test in `test_timed_run.py` still present and passing. What must not be weakened: no product code under `domain/`, `application/`, `persistence/` or `web/` changes to make a timing pass (a time over the limit is a finding about the saved data's design, not something to edit away here). The limit stays 1.0 second, and no existing timed action's bar or test is loosened, deleted or skipped. No action beyond these three is added; NFR-1's other actions are timed by their own stations once they exist. Deleting a task with its comments, and the unreadable-data pages, are not here.
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md` opened, and the six concerns it routes read (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing_python.md`)

---

## Change Summary

NFDR QC-48 has every action SRS NFR-1 lists show its result within 1 second at 1,000 tasks with 20 comments on each, and has a change that adds a listed action add it to the timed run. The run today times neither the comment add nor the People page's assignee add and remove, so it claims coverage it does not have. This change adds those three actions to the run. Each runs on its own full-volume fixture, as one same-origin submission whose request, landing page and total are each timed and held to the limit. Each counts only when the saved state and the landing page show it really happened.

All paths below are relative to the product root, which `system/projects/tracker17/project.md` `Product path:` names. Every command is typed from the product root unless the rule says otherwise.

---

## Rules

### What the run covers

- **CP-276:** `python3 tests/timed_run.py`, the command NFDR QC-48's `verified by:` tail names, times three actions beyond those it times today: adding a comment to a task, adding a name to the assignee list from People, and removing a name from that list. It adds no other action. Every action it times today stays timed. That is project creation at ordinary lengths and at both maximums, the task add, the field edit, the label add and remove, and the name save. Each keeps the rows, the bar and the verdict it has today.
- **CP-277:** Each of the three actions runs on a fixture of its own, as SDD § 4 TS-5 and NFDR QC-48 fix. A fixture holds 1,000 tasks and 20 comments on every task, at ordinary text lengths, not at the maximums. It is saved in a location of its own inside the run's own temporary directory and loaded from that location before its action is sent. The product's `data/` is never used, and the run leaves it exactly as present or absent as it found it. A fixture also holds what its action needs to succeed:
  - the comment add's fixture holds a saved operator name of ordinary length;
  - the assignee add's fixture does not carry the name to be added on the assignee list;
  - the assignee remove's fixture carries the name to be removed on the assignee list.

  The fixtures of the actions timed today do not change. The name save's fixture still holds no operator name.
- **CP-278:** Each of the three actions is one form submission sent through the tracker's request path. Each names the tracker's own host and is marked `Sec-Fetch-Site: same-origin` (NFDR QC-32; SDD § 4 SEC-2). Each carries only the field the tracker's own form for it sends, with an ordinary-length value:
  - the comment add: `text`, posted to `/tasks/{id}/comments` for one fixture task;
  - the assignee add: `name`, posted to `/assignees`;
  - the assignee remove: `name`, posted to `/assignees/remove`.

### When an action counts as done

- **CP-279:** The comment add counts as done only when both of these hold:
  - the answer is a `303` to exactly `/tasks/{id}?comment_added={n}`, where `{id}` is the task the comment was posted to and `{n}` is the added comment's one-based place among that task's comments (`21` on a task that held 20);
  - the saved state, read back from the fixture's own location after the submission, is the fixture with exactly one comment added to that task, last in its comments, whose text is the text submitted and whose author is the operator name the fixture saved. Nothing else in the saved state differs from the fixture. The time the tracker records for the comment is not compared with any value.
- **CP-280:** The assignee add counts as done only when both of these hold:
  - the answer is a `303` to exactly `/people?added={name}`, with the submitted name encoded as an address carries it;
  - the saved state, read back from the fixture's location, is the fixture with exactly that one name added to the assignee list, and nothing else differs.
- **CP-281:** The assignee remove counts as done only when both of these hold:
  - the answer is a `303` to exactly `/people?removed={name}`, with the name encoded as an address carries it;
  - the saved state, read back from the fixture's location, is the fixture with exactly that one name gone from the assignee list, and nothing else differs. Every task keeps whatever assignee it carried.
- **CP-282:** A refused or failed action is never counted as done (NFDR QC-48). It is reported `refused or failed`. Any of these answers is that case:
  - a redirect carrying a refusal or a failure outcome;
  - a `303` to any address other than the one CP-279 to CP-281 name;
  - any status other than `303`;
  - a `303` to the right address after which the saved state is unchanged or differs from the fixture in any way beyond the one intended change.

  When the answer is not a `303` to the exact address, the landing page is not requested. Its row and the total's row are then reported `refused or failed`.
- **CP-283:** The landing is a request for exactly the address the submission redirected to. It counts as done only when the answer is `200` and the page shows the action's completion line, with each typed value HTML-escaped as the page shows it:
  - the comment add: `You added a comment to '{task title}'.`, and the added comment's text;
  - the assignee add: `You added '{name}' to the assignees.`;
  - the assignee remove: `You removed '{name}' from the assignees, and tasks that already carry the name keep it.`

  A landing that is not `200`, or whose page lacks that line (or, for the comment, the comment's text), is reported `refused or failed`. The total's row is then reported the same way.

### Timing, output and verdict

- **CP-284:** For each of the three actions the run reports three durations, as it does for the label add and remove today:
  - the submission;
  - the landing request;
  - the total, which is the submission's duration plus the landing's.

  Each of the three must be strictly below 1.0 second. A duration of 1.0 second or more fails that row, and the total fails at or over the limit even when each part is under it. The limit stays 1.0 second for every row of the run.
- **CP-285:** The run prints the three actions after every line it prints today, in this order. Each action's fixture line comes first and its three rows follow:
  1. `comment fixture: …`, then `add a comment at 1000 tasks: …`, `comment landing page at 1000 tasks: …`, `comment total at 1000 tasks: …`
  2. `assignee add fixture: …`, then `add an assignee at 1000 tasks: …`, `assignee add landing page at 1000 tasks: …`, `assignee add total at 1000 tasks: …`
  3. `assignee remove fixture: …`, then `remove an assignee at 1000 tasks: …`, `assignee remove landing page at 1000 tasks: …`, `assignee remove total at 1000 tasks: …`

  Each row has the shape every row of the run has today: `{label}: {milliseconds, one decimal place} ms`. A failing row adds ` — ` and its problems, joined by `, `, drawn from `refused or failed` and `at or over 1 s`. On a run where every row passes, no line the run prints contains `over` or `refused`.
- **CP-286:** Each fixture line states the volume and the length in characters of every ordinary text value the action ran on. Characters are counted as FDR R-77 counts them, one per Unicode code point:
  - `comment fixture: 1000 tasks, 20 comments each (20000 in all); title of {n} characters, comment of {n} characters, name of {n} characters, added comment of {n} characters`. Here the title and the comment are a fixture task's, the name is the saved operator name, and the added comment is the text submitted.
  - `assignee add fixture: 1000 tasks, 20 comments each (20000 in all); title of {n} characters, comment of {n} characters, name added of {n} characters`
  - `assignee remove fixture: 1000 tasks, 20 comments each (20000 in all); title of {n} characters, comment of {n} characters, name removed of {n} characters`

  The counts are read from the fixture the action actually ran on, never typed as constants.
- **CP-287:** The run exits `0` only when every row of every action it times passes. It exits `1` when any of the nine rows CP-285 adds fails, whatever every other row reports, as it does today for a failing row of an action it already times.

### The harness's tests

- **CP-288:** `tests/integration/test_timed_run.py`, which already checks the harness (`tests/timed_run.py:L18-L19`), gains tests that show the three actions are checked. For each of the three actions:
  - a refused answer to the submission gives that action's submission row as not done, and a verdict of `1`;
  - a landing page that does not show the action's result, after a real submission, gives the landing row as not done while the submission row is done, and a verdict of `1`.

  One test runs the whole run and checks the three fixture lines CP-286 states: the task count, the comments per task, and each stated length equal to the length of the text the fixture or the action holds. The new tests hand the harness its collaborators and patch no name inside a product module (NFDR QC-28; SDD § 4 TS-2).
- **CP-289:** Every test `tests/integration/test_timed_run.py` holds today stays present and passing, and none is skipped or has an assertion loosened. Three of them run the whole run with a scripted timer and supply exactly as many timer readings as today's actions take: `test_timed_run_fails_when_only_the_edit_fails`, `test_timed_run_fails_when_only_a_label_action_fails` and `test_full_timed_run_fails_when_only_name_measurement_fails`. They change only by also supplying readings for the three added actions, each under the limit. Each keeps asserting exactly what it asserts today: the one row it makes slow is the only row reported over the limit, and the run's status is `1`.

### Where it is proven, and what does not move

- **CP-290:** Take a fresh clone of the repository at the commit under test, the copy `core/roles/CROSS_ROLE.md` § *Every seat* sends a run outside the change's worktree to. In it, `python3 tests/timed_run.py` from the product root exits `0` and prints the three fixture lines and nine rows of CP-285 with no problem on any of them. The project card's `Test command:` (`system/projects/tracker17/project.md`), typed from the clone's root, exits `0`.
- **CP-291:** `ruff format --check .` and `ruff check .`, typed from the product root, each exit `0` with the change in place, at the Ruff version NFDR QC-39 pins (NFDR QC-62).
- **CP-292:** No file under `domain/`, `application/`, `persistence/` or `web/` changes, and neither do `main.py` or `errors.py`. A duration at or over the limit is reported as the run's failure and is not made to pass by any change to the product (SDD § 11 R-1).

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| `python3 tests/timed_run.py` before the change | Exits 0 and prints no line naming a comment add or an assignee | CP-276 |
| The whole run after the change | Every line printed today, unchanged in label and order, then the three fixture lines and nine rows of CP-285; exit 0 | CP-276, CP-285, CP-287 |
| The run on a machine where `data/` is absent | `data/` is still absent after the run; each of the three fixtures sits in its own location inside the run's temporary directory | CP-277 |
| The comment fixture | 1,000 tasks, 20 comments on each, and a saved operator name of ordinary length | CP-277 |
| The name save's fixture after the change | Still holds no operator name, so the name save stays a changed save | CP-277 |
| The comment add's submission | One POST of `text` to `/tasks/{id}/comments`, marked `Sec-Fetch-Site: same-origin`, naming the tracker's host | CP-278 |
| Comment posted to task 250, which held 20 comments | `303` to `/tasks/250?comment_added=21`; saved task 250 has 21 comments, the last with the submitted text and the fixture's name as author; nothing else differs | CP-279 |
| The fixture saved no operator name and the comment is refused | Answer is `303` to `/tasks/250?comment_refused=no-name&comment_text=…`; submission row `refused or failed`; landing not requested; landing and total rows `refused or failed`; exit 1 | CP-282, CP-287 |
| A `303` to `/tasks/250?comment_added=21` with nothing saved | Submission row `refused or failed`; exit 1 | CP-279, CP-282 |
| A comment saved under a name other than the fixture's | Submission row `refused or failed`; exit 1 | CP-279, CP-282 |
| `Avery Chen` added on People | `303` to `/people?added=Avery+Chen`; saved list gains `Avery Chen` and nothing else differs; landing shows `You added 'Avery Chen' to the assignees.` | CP-280, CP-283 |
| The name to add is already on the list | Answer is `303` to `/people?refused=assignee-name-in-use&name=…`; submission row `refused or failed`; exit 1 | CP-282 |
| `Avery Chen` removed on People | `303` to `/people?removed=Avery+Chen`; saved list no longer holds it, every task keeps its assignee; landing shows `You removed 'Avery Chen' from the assignees, and tasks that already carry the name keep it.` | CP-281, CP-283 |
| The name to remove is not on the list | Answer is `303` to `/people?refused=assignee-not-found&name=…`; submission row `refused or failed`; exit 1 | CP-282 |
| A failure answer: a `failed=` outcome, or status `500` | Submission row `refused or failed`; exit 1 | CP-282 |
| A real comment add whose landing page lacks `You added a comment to '…'.` | Submission row done; landing and total rows `refused or failed`; exit 1 | CP-283 |
| Submission 0.4 s, landing 0.5 s | Both rows pass; total 0.9 s passes | CP-284 |
| Submission 0.5 s, landing 0.5 s | Both rows pass; total 1.0 s fails `at or over 1 s`; exit 1 | CP-284, CP-287 |
| Submission 1.0 s | Submission row fails `at or over 1 s`, and so does the total | CP-284 |
| A passing row | `add an assignee at 1000 tasks: 33.8 ms`, with no ` — ` suffix | CP-285 |
| A passing whole run | No printed line contains `over` or `refused` | CP-285 |
| The assignee add's fixture line | `assignee add fixture: 1000 tasks, 20 comments each (20000 in all); title of {n} characters, comment of {n} characters, name added of {n} characters`, each `{n}` the length of the text actually used | CP-286 |
| Only the assignee remove's total is over the limit | Only `assignee remove total at 1000 tasks` is reported over; exit 1 | CP-287 |
| The new tests: a refusal per action, and a wrong landing per action | Each finds that row not done and the verdict `1` | CP-288 |
| The new fixture-report test | Finds each of the three fixture lines with 1000 tasks, 20 comments each and the true lengths | CP-288 |
| `test_timed_run_fails_when_only_a_label_action_fails` after the change | Supplies readings for the three new actions too; still finds only `label add total at 1000 tasks` over and status 1 | CP-289 |
| A fresh clone at the commit under test | `python3 tests/timed_run.py` from the product root exits 0; the card's `Test command:` from the clone root exits 0 | CP-290 |
| `ruff format --check .` and `ruff check .` from the product root | Each exits 0 | CP-291 |
| The change's diff | Touches no file under `domain/`, `application/`, `persistence/`, `web/`, and neither `main.py` nor `errors.py` | CP-292 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The run today times none of the three actions and exits 0 (CP-276) | `python3 tests/timed_run.py` from the product root of a fresh clone at `e5e1cbbae`, real clock | Exit 0. Rows for the 51 creates, the task add, the edit, the label add and remove and the name save. No comment-add or assignee row |
| Each of the three actions, sent as CP-278 says to a real `Site` over a real `SavedData` holding the 1,000 × 20 fixture with the real clock, gives the addresses, saved states and landing lines CP-279 to CP-283 state | A probe script outside the clone, importing that clone's `tests/timed_run.py` and product at `e5e1cbbae`; the comment fixture with operator name `Jordan Rivera`, the remove fixture with `Avery Chen` on the list | Comment: `303 /tasks/250?comment_added=21`, 21 comments, last authored `Jordan Rivera` with the sent text, landing shows `You added a comment to '…'.` and the text. Add: `303 /people?added=Avery+Chen`, list `('Avery Chen',)`, landing line present. Remove: `303 /people?removed=Avery+Chen`, list `()`, landing line present. Submissions 27.0, 33.8 and 27.7 ms, landings ≤ 0.2 ms |
| A refusal of each action redirects with a refusal outcome (CP-282 examples) | The same probe, same conditions | Comment with no saved name: `303 /tasks/250?comment_refused=no-name&comment_text=…`, saved state unchanged. Add of a listed name: `303 /people?refused=assignee-name-in-use&name=Avery+Chen`. Remove of an unlisted name: `303 /people?refused=assignee-not-found&name=Avery+Chen` |
| The three routes exist | `web/routes.py:L96-L97`, `:L104` | `Route("POST", "/assignees", …)`, `Route("POST", "/assignees/remove", …)`, `Route("POST", "/tasks/[0-9]+/comments", …)` |
| The completion lines are the product's own | `web/pages.py:L939`, `:L1170`, `:L1173-L1174` | `You added a comment to '{title}'.`, `You added '{name}' to the assignees.`, `You removed '{name}' from the assignees, and tasks that already carry the name keep it.` |
| The row shape and problem words CP-285 restates are the run's today | `tests/timed_run.py:L138-L153` | `f"{result.label}: {result.seconds * 1000:.1f} ms"`, plus `" — "` and the problems joined by `", "`, from `"refused or failed"` and `f"at or over {limit:g} s"` |
| A passing run must print neither `over` nor `refused` | `tests/integration/test_timed_run.py:L101`, `:L232`, `:L495`, `:L760` | Each whole-run test asserts `"over" not in report and "refused" not in report` |
| The fixtures used today carry no operator name and no assignee, and a test holds the name save's fixture to that | `tests/timed_run.py:L181-L189`; `tests/integration/test_timed_run.py:L957` | `restore_state(...)` passes neither `assignees` nor `operator_name`; the test asserts `name_seeded.operator_name is None` |
| With the change in place, the three tests CP-289 names cannot pass unchanged | A constructed post-change tree in the fresh clone: `main` reads its timer four more times after the name save, as one more timed action does; then `pytest products/tracker17/tests/integration/test_timed_run.py` from the clone root, pytest 9.1.1 | Before the edit: 30 passed. After it: 3 failed, 27 passed. The three failures are exactly the tests CP-289 names, each `StopIteration` at `test_timed_run.py:L53` |
| QC-62's two Ruff gates pass on the tree as it stands (CP-291) | `ruff format --check .` and `ruff check .` from the product root of the fresh clone at `e5e1cbbae`, Ruff 0.16.10 (pinned at `tests/requirements.txt`) | `183 files already formatted`, exit 0; `All checks passed!`, exit 0 |
| `data/` is never the run's location today | `tests/timed_run.py:L528-L531`; `tests/integration/test_timed_run.py:L171-L184` | The run makes its own temporary directory; the existing test asserts `product_data.exists() == existed` |
| Language rendering | No rule pins output that renders a language-level fact. Every printed line and every checked address is a format the product or its harness chooses | none — no rendering row |

---

## Out of Scope

- Timing NFR-1's actions the product does not have yet: moving a task, deleting a task or a project, renaming a project, filtering, sorting and opening a summary. `docs/what_left.md` lists each as missing, and the request leaves each to the station that builds it.
- Deleting a task together with its comments, and the pages for unreadable saved data. The request names both as not here.
- Any change to the rows of the actions timed today, including adding a total row to the task add, the field edit or the name save, which report two rows each today (`tests/timed_run.py:L241-L248`, `:L304-L311`, `:L504-L511`).
- Setting or clearing a task's assignee. That is a field of the task edit, which the run already times. "Adding an assignee on People" is the assignee list's add (FDR R-57).
- Making any duration pass by changing the product. A duration at or over the limit is a finding about the whole-state save, whose remedy SDD § 11 R-1 and ADR-0004 name, and it lands as its own change.
- Changing the 1.0-second limit, the 1,000 × 20 volume, the ordinary lengths the existing fixtures use, or the creates at both maximums.
- Collecting the timed run into the pytest suite. It stays the script QC-48 names, gated at `development-implementation` (NFDR § 10, QC-48 row).
- Editing any product document. The NFDR, the SDD and the SRS already state the obligation this change meets (NFDR QC-48; SDD § 4 TS-5; SRS AC-15).

---

## Locked Answers (the divergence record — self-review 2026-10-13)

- **Gap 1 — where the three actions print (b):** after every line the run prints today, in the order comment add, assignee add, assignee remove. *Reason:* the request fixes no order. Appending leaves every existing line, and the order existing tests read, exactly as it is. It is reversible.
- **Gap 2 — the printed labels and fixture lines (b):** CP-285 and CP-286 fix the literal labels and the fixture-line shapes. *Reason:* the request asks for the three rows and a fixture report and gives no wording. A test cannot check a line nobody fixed. The words follow the run's existing labels, `add a label at 1000 tasks`, `label add landing page at 1000 tasks`, `label add total at 1000 tasks` (`tests/timed_run.py:L347-L357`). They contain neither `over` nor `refused`, so the existing whole-run tests stay passing.
- **Gap 3 — which text lengths a fixture line states (b):** every ordinary text value the action ran on. That is a fixture task's title and comment, the action's own submitted text, and, for the comment add, the saved operator name the comment is written under. *Reason:* QC-48 and SRS AC-15 have the run state the text lengths it uses, and a comment's saved name is text the action uses. Stating one more length loosens nothing.
- **Gap 4 — what "the landing shows the result" means (b):** the action's completion line as the product shows it. For the comment add the page must also show the added comment's text. *Reason:* the completion line is what the label actions' landing check already reads (`tests/timed_run.py:L436-L440`). A comment's result is the comment itself, so its text on the page is the stricter, observable proof the request asks for.
- **Gap 5 — the comment's recorded time (b):** CP-279 compares the added comment's text and author and the whole rest of the saved state, and not its recorded time. *Reason:* the time is the tracker's own reading of the real clock at the moment of the add (FDR R-72). No fixed value exists to compare it with, and every other saved value is still compared.
- **Gap 6 — a refused or wrongly addressed submission's landing and total (b):** the landing is not requested, and both its row and the total's row are reported as not done. *Reason:* that is how the label actions already treat it (`tests/timed_run.py:L419-L424`). It keeps a refused action from printing any row that reads as a pass.
- **Gap 7 — failure as well as refusal (e):** CP-282 counts a failed action, not only a refused one, as not done. *Reason:* NFDR QC-48 has the run fail "when a timed action is refused or fails", and the request names only the refusal. A failure leaves the saved state unchanged, so the request's own saved-state test catches it too.
- **Gap 8 — Ruff's gates (e):** CP-291 holds the change to `ruff format --check .` and `ruff check .`, which run over `tests/` as well. *Reason:* NFDR QC-62 makes both gates on the code, at the version QC-39 pins, and the request is silent on them. Both pass on the tree today (Verified Claims).
- **Gap 9 — no patching in the new tests (e):** CP-288's tests hand the harness its collaborators and patch no product-module name. *Reason:* NFDR QC-28 and SDD § 4 TS-2 bind every test, and QC-28's layer-6 walk fails on such a patch. The request is silent on it.
- **Gap 10 — three existing tests change (f):** `test_timed_run_fails_when_only_the_edit_fails`, `test_timed_run_fails_when_only_a_label_action_fails` and `test_full_timed_run_fails_when_only_name_measurement_fails` change, and only by also supplying timer readings for the three new actions. Each keeps asserting that the one row it slows is the only row over the limit and that the run's status is `1`. *Reason:* each supplies exactly the readings today's actions take. Once the run times the three actions the way it times the others, which the request asks for, these tests run out of readings: on a constructed post-change tree all three failed with `StopIteration` (Verified Claims). The request keeps every existing test "present and passing", and adding readings keeps all three present, passing and no looser.
- **Gap 11 — `main.py` and `errors.py` (b):** CP-292 also keeps `main.py` and `errors.py` unchanged, beside the four directories the request names. *Reason:* both are product code (NFDR QC-1). The request's ground, that a time over the limit is not edited away, reaches them too, and the change needs neither.
