# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-13_full-volume-run` — the only change unit expected for station `2026-10-13_full-volume-run` (seed `2026-10-07_comment-on-a-task`, item 3), opened for its reached-when 1 to 4. `tests/timed_run.py` gains the comment add, the assignee add and the assignee remove, each timed as POST, landing GET and total under 1.0 second on its own 1,000 × 20 fixture, with the fixture and text lengths printed; each counts only when it happened, shown by `tests/integration/test_timed_run.py` feeding a refused action and a landing that does not show the result. Scope boundary: no product code under `domain/`, `application/`, `persistence/` or `web/` changes, the 1.0 limit and every existing timed action and test stay as they are, no action beyond the three. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present; NFDR QC-48 drives it. Product-fit: the comment add landed in `2026-10-12_comments-on-the-page` and the assignee add and remove in `2026-10-11_people-and-assignees`; the run times neither yet. Classified `nfdr` / `changing`: the run's verdict gains three rules.
