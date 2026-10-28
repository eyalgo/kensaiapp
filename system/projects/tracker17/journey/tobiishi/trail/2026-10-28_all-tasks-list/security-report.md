# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` § QC-40, "no audit command exists for this product: the Python packet names none and tracker17 installs none"). Detailed under *Dependency audit*.
- The browser-build exception in force (NFDR RN-33, Chromium `153.0.8010.12`, lapsing 2026-11-07) was not re-checked here: it is QC-40's review at `development-design`, not an audit this run could run, and it already has its row in `system/upkeep.md`. Nothing to do now; it lapses in 10 days.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40's `verified by:` tail is a review at `development-design`, and its text states "no audit command exists for this product". No command was invented and none ran (`<CORE>/prompts/senior_engineer_repair_dependencies.md` § *Where the NFDR names none*). The change touches no dependency: `pyproject.toml` and `tests/requirements.txt` are unchanged in `git diff main...HEAD`.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran | — |

## Exceptions and upkeep rows
none

## Holes in the code
none. The threat lists applied: the product serves and stores input, so OWASP Top 10:2025 with Anthropic's five categories, over the NFDR's four trust boundaries (B-1 listener, B-2 saved data, B-3 typed text shown back, B-4 setup). The product carries no skill, prompt or launcher, so the agentic list does not apply.

What was traced, from `git diff main...HEAD -- products/tracker17` and every touched file:

- **B-1, the new entry point `GET /tasks`** (`web/routes.py:111`, `:329-330`, `:542-562`). It sits behind the same request check as every route (`Site.handle`, `:260-278`: `Host`, `Sec-Fetch-Site`, route table, CSP header on every response). It is a `PAGE` route: it reads the query through `_filter_input` / `_sort_input` (closed key sets, values passed to `domain` as sent) and `_move_view`, saves nothing, and answers through `_html`, which carries the policy header. The not-found branch returns the argument-free `task_not_found_page()`, so no address fragment reaches a page (CP-33). QC-7, QC-8, QC-31 to QC-34 hold for the new route as for the old.
- **B-1, the new `place=all_tasks` form value** (`web/routes.py:857-865`; `web/pages.py:263-270`). The destination is decoded through `_closed(pages.MovePlace, …)` — a three-member enum — and mapped to one of three addresses the code builds itself (`ALL_TASKS_ADDRESS`, `/projects/{task.project_id}`, `/tasks/{identity}`, the two ids being `int`s). No submitted string becomes a redirect target, so there is no open redirect; the design's own line (`change_design.md:115`, "a destination discriminator, never a supplied return URL") is what the code does. An unknown or missing word falls to the task's page.
- **B-1, the filter and sort values carried through the move form** (`web/routes.py:866-880`). They are re-validated by `domain` through `all_task_list(...).problems` before any save or confirmation, the same gate the project list already keeps (CP-477, QC-38). The redirect query is built by `_address` through `urlencode(doseq=True)`, so a carried value cannot break out of the query.
- **B-3, every new value placed in a page** (`web/pages.py`). The Project cell goes through `_escape` (`:956`, `project_names.get(...)`), the row title and labels and assignee through `_escape` as before (`:971-973`), the refusal lines format `_escape(task.title)` (`:842`), the hidden `place` value is an enum literal (`:748`, `:767`), the new column header and the empty-state paragraph are constants, and `_document` escapes its title (`:406`). QC-36's one-function rule holds: the only entry is `_escape`.
- **Cross-project reach on All tasks** (`web/routes.py:548`, `:561`: `_move_view(query, self._tracker.task)` and `_off_list_task(self._tracker.task, …)`). On a project's list these are scoped to the project's own tasks; on All tasks any task is in scope by definition (CP-475). There is one operator and one loopback listener (NFDR § 3, "Identity and authorization — not applicable"), so a wider read is not a privilege change.
- **`domain/` and `application/`**: pure functions over the state and a clock handed in; no I/O, no eval, no new import. `persistence/`, `main.py`, `errors.py` and `pyproject.toml` are untouched.

Candidates considered and dropped in the sceptical pass, all below the floor of 8: an All tasks page over a large tracker as resource exhaustion (excluded class); the `Location` header carrying every raw filter value back (the values are encoded, and reflected only into a same-origin address the page re-validates).

## Not checked
- The dependency audit, for the reason above.
- The browser suite (`tests/e2e/`), mypy and the timed run were not re-run: no code was changed by this step, so the code-integrity report's test evidence stands as the branch's state (1964 passed through the gate tool at `7857100b0`).
- The suite was not run by this step at all: the gate call is owed only to keep a bump or a hole fix, and there was neither.
