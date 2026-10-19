# 宿場 Shukuba — Your name on People

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`. Slug: `operator-name`.*

## What it is

People gains **Your name**: a field that sets or changes the one saved operator name (SRS DR-5, SDD § 3 Operator name), with a sentence beside it saying that comments already written keep their name. A blank name is refused with the typed text kept and the reason shown (UXD UX-F8). The name is saved and survives a stop and a start. It is one station so the next one, the comment form, has a saved name to write under; nothing about comments is built here.

## Reached when

1. `GET /people` on a running tracker shows a Your name field with the sentence beside it that comments already written keep their name. Checked by an integration test in `tests/integration/test_people_pages.py` that finds both in the built page.
2. Submitting a name saves it, and submitting a different one replaces it. Checked by an integration test in `tests/integration/test_people_routes.py` that reads the saved name back, including after a real save and restart, as `test_people_survives_real_save_and_restart` does for the list.
3. Submitting a blank name (empty, and whitespace only) is refused: the saved name is unchanged, the page shows the refusal, and the field keeps the typed text. Checked by an integration test in `tests/integration/test_people_routes.py` that starts with a saved name and one with none.
4. An end-to-end test in `tests/e2e/test_people.py` sets the name in the browser, sees it again after reload, and sees a blank one refused with the typed text kept.
5. `pytest products/tracker17/tests/` exits 0, run in a fresh clone checked out at the commit under test (`core/roles/CROSS_ROLE.md` § *Every seat*); a `git archive` copy is no Git repository and fails `test_data_is_ignored_by_version_control`. Before the work, no test asserts a Your name field is present: `git grep -n -i "your name" -- products/tracker17/tests` finds only two absence checks in `tests/integration/test_people_pages.py` (`for unavailable in (...)`, at the open L115 and L441), which the new field makes false. Tests 1 to 4 therefore fail before the work.

## Guardrail

- No comment is written, listed or refused here, and `domain/comments.py` does not appear. The Operator name entity is stored; the Comment entity is not.
- No existing People test is deleted, skipped or loosened, except that the two absence checks above drop `"your name"` from their lists, which is the one change this station makes true; the assignee list behaves as before.
- The saved-data shape changes only by the one operator name SRS DR-5 allows (SRS AC-17); a start on data saved before this station keeps its projects, tasks and people.
- **Not here:** the comment form, the no-name notice and earlier comments keeping the earlier name — `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, item 2 `comments-on-the-page`. The 1,000 × 20 timed run — the same seed, item 3 `full-volume-run`.
