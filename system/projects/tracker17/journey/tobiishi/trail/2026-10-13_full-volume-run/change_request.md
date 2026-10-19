# Change request — 2026-10-13_full-volume-run

**Request:** Make the timed run cover every action NFR-1 lists, now that all of them exist. `tests/timed_run.py` today times project creation, task add, field edit, label add and remove, and the name save. Add the three it leaves out: adding a comment, adding an assignee on People, and removing one. Each one is done the way the run already does the others: on its own 1,000-task, 20-comments-each fixture, as a same-origin submission, timing the POST, the page it lands on, and the total, each under the 1.0-second limit. The run prints the fixture it used for each of the three, with the task count, the comments per task and the text lengths. A run that did not really do the action fails, and does not count as a pass: a comment not saved under the saved name, an assignee not added or removed in the saved state, a refused action, or a landing page that does not show the result. Tests in `tests/integration/test_timed_run.py` feed the harness a refused action and a landing that does not show the result for each of the three and find the non-zero verdict, and one test checks the printed fixture report. Run from `products/tracker17` in a fresh clone at the commit under test, `python3 tests/timed_run.py` exits 0, and `pytest products/tracker17/tests/` exits 0 with every existing test in `test_timed_run.py` still present and passing.

What must not be weakened: no product code under `domain/`, `application/`, `persistence/` or `web/` changes to make a timing pass (a time over the limit is a finding about the saved data's design, not something to edit away here). The limit stays 1.0 second, and no existing timed action's bar or test is loosened, deleted or skipped. No action beyond these three is added; NFR-1's other actions are timed by their own stations once they exist. Deleting a task with its comments, and the unreadable-data pages, are not here.

**Sizing:** one honest merge. The unit of acceptance is one claim: the timed run times every listed action that exists. The three additions are one harness extension in one file and its one test file, and the station is reached when the run covers all three. Splitting them would leave the run claiming coverage it does not have.

**Category:** nfdr
**Behaviour:** changing
**Classified because:** the station's reached-when 1 and 2 have the run's verdict change for three new actions, and a check that gains a rule changes what an enforcement command reports (NFDR QC-48, `change_classification.md` § *Category notes*, `nfdr`); no product code moves.


**Sealed:** 2026-10-13 — accepted; merged to `main` via `--no-ff`.
