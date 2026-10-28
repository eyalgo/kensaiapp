# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-28_all-tasks-list`

*From the review of unit `2026-10-28_all-tasks-list`, 2026-10-28. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` once its last station closes

- **Kind:** a seed to retire
- **Why:** its third and last station, `all-tasks-list`, is reached and only its close is owed; the
  first two are ticked. SDD § 6 S-5's bar, the seed's own, holds.
- **Source:** the seed's checklist (lines 17–19); fresh clone at `9f74b3d50`: `pytest products/tracker17/tests/` → `1964 passed`, exit 0; `python3 products/tracker17/tests/timed_run.py` → exit 0 with the filter and sort lines
- **Why no companion carries it:** it is a seed's retire, not something a document should state.

### 2. Cut a seed: the out-of-date refusal on a project's list and the task page states the status and claims no change

- **Kind:** a seed to cut
- **Why:** `CONTENT.md` RN-26 and RN-27 say the in-row refusal for a move the task's status no longer
  allows must state the current status and claim no change, and leave the product's "has changed to"
  line as a finding for a change that publishes text. All tasks now says "is"; a project's list and
  the task page still say "has changed to", so one refusal reads two ways in the product. No seed in
  the pool carries it.
- **Source:** `products/tracker17/web/pages.py:L804-L808` (`_CHANGED`); `products/tracker17/docs/CONTENT.md:L558-L559`; `tracker17 · tobiishi · 2026-10-28_all-tasks-list`, `change_text.md` § Wording decisions, first entry; `grep -rn -i 'has changed to\|RN-26' system/projects/tracker17/journey/nemawashi/unpicked` prints nothing
- **Why no companion carries it:** `CONTENT.md` already states the rule; what is owed is a change to the
  product's strings and their tests, which is work.
