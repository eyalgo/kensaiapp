# 宿場 Shukuba — Comments on a task's page

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`. Slug: `comments-on-the-page`.*

## What it is

A task's page lists its comments oldest first, each with its author and its time in the machine's local time, and adds one under the saved operator name (SDD § 6 S-3, UXD UX-F7, UX-F8). The form sits below the newest comment and says beside its text field the most characters a comment holds. After Add the page opens with the new comment in view and keyboard focus on it. With no name set a notice above the form says a name is needed and links to People. A comment with no name set and a blank comment are each refused with the typed text kept. Earlier comments keep the earlier name after a rename. No control edits or deletes a comment. Saved data that breaks a comment rule is reported unreadable at start (SD-5). `domain/comments.py` is the Comments feature's entry point (SDD § 4 TS-3). It is one station because the page, the form and the rule are one claim: a comment is written, shown and kept under one name. The timed run is not here.

## Reached when

1. `GET` of a task's page on a running tracker lists its comments oldest first, each with author and local time, and shows the form below the newest with a sentence naming the maximum length. Checked by an integration test that finds the order, the author and the time in the built page, and finds that number equal to the comment field's `maxlength`.
2. Adding a comment with a saved name saves it under that name and the page shows it; after the name is changed on People, earlier comments still show the earlier name and a new one shows the new name. Checked by an integration test that reads the saved comments back.
3. With no name set the page shows the notice above the form with a link to People. A comment with no name set, and a blank comment (empty and whitespace only), are each refused: nothing is saved, the page shows the reason and the field keeps the typed text. Checked by integration tests, one per refusal.
4. No edit or delete control for a comment is in the built page. Checked by an integration test on a page that has comments, so the control could have appeared.
5. An end-to-end test in `tests/e2e/` adds a comment to a task whose comments fill more than the window and finds the new comment in view with keyboard focus on it. An end-to-end test fills a comment to its maximum with line breaks and finds it saved whole (SRS AC-20).
6. Saved data holding a comment that breaks a comment rule is reported unreadable at start, not repaired or dropped. Checked by an integration test in `tests/integration/test_saved_data.py` or beside it.
7. `products/tracker17/domain/comments.py` exists. Before the work `ls products/tracker17/domain/comments.py` reports no such file.
8. `pytest products/tracker17/tests/` exits 0, run in a fresh clone checked out at the commit under test (`core/roles/CROSS_ROLE.md` § *Every seat*), since a `git archive` copy is no Git repository and fails `test_data_is_ignored_by_version_control`.

## Guardrail

- The timed run is not extended here: `tests/timed_run.py` and its test are left byte-identical.
- No existing People or task-page test is deleted, skipped or loosened; the operator-name behaviour from the previous station is unchanged.
- No threaded replies, no comment deletion with its task, and no wording change outside the comment text the content record names.
- The saved-data shape changes only as SDD § 3's Comment entity states; a start on data saved before this station keeps its projects, tasks, people and name.
- **Not here:** the 1,000 × 20 timed run and the assignee timing — `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, item 3 `full-volume-run`. Deleting a task with its comments — `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. The unreadable-data pages — `tracker17 · nemawashi · 2026-10-11_protect-saved-data`.
