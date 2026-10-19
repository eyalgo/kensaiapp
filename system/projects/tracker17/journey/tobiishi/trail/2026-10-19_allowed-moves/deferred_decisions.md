# Deferred Decisions — allowed-moves

What this change held back, for `shukuba-refine` to place after the unit lands. Three kinds of entry, each stamped with the stage that wrote it and shaped below:

- a **direction** decision the spec could not responsibly make — destructive / irreversible, or no safe default existed (development-specs, Step 5 *Direction ambiguity*);
- a **record gap** — a behaviour a product document states, binding nothing this change adds or alters, that the product does not have today and the request does not ask for — or one the request explicitly rules out (development-specs, Step 5 *A record's unbuilt behaviour is handed on*);
- a **reading set aside** — spec lines the design did not carry, because another reading kept every existing contract and delivered the request (development-design, Step 7).

**Collection, read after the unit lands.** Downstream stages (development-design, development-plan, development-implementation) append their own entries, creating the file from this template when it is absent; `shukuba-refine` reads the collection and acts on the route for each entry that has lost its owner. Fill only the fields of the entry's own kind.

---

## The `cancelled` move offered on a page, behind its in-place confirmation — record gap, handed on by development-specs (2026-10-19)
**Record:** `docs/UXD.md` UX-I1 ("offers exactly the moves allowed from its current status"), UX-I2 and UX-F4 (a move to `cancelled` takes one more, confirming press); `docs/SDD.md` § 4 EX-6 and § 6 S-4 *Reached when* (the in-place confirmation, its focus, the double press, the first press for a move no longer allowed, and their end-to-end tests); `docs/CONTENT.md` § Message patterns, Needs confirming (the `cancelled` sentence and "Move to cancelled").
**Product today:** no page offers any move. A row is title, status, priority, assignee, labels and due date (`web/pages.py:558-573`), and the task's page holds no status and no move (`web/pages.py:1078-1088`). After this change, the rows and the task's page offer every allowed move except `cancelled`, and the workflow rule still allows `todo` → `cancelled` and `in-progress` → `cancelled` (change_spec CP-293, CP-297, CP-301).
**Why not this change:** the request rules it out: "No `cancelled` button appears on any page and no confirmation is built here, because a move to `cancelled` must never save unconfirmed (EX-6) and no page shows a control before its slice (EX-12)".
**Owner:** none — for shukuba-refine
**Status:** open

## A refused move that says the page is out of date and offers a reload — record gap, handed on by development-specs (2026-10-19)
**Record:** `docs/UXD.md` UX-F4, failure and recovery ("The reason says the task's status has changed and offers a reload") and UX-I3 ("A refusal caused by the page being out of date … says so and offers a reload"); `docs/SDD.md` § 6 S-4 *Reached when* ("A move made from a page that is out of date is refused, says the status has changed, and offers a reload") and its *Command*, "the out-of-date move of AC-12"; `docs/CONTENT.md` § Message patterns, Error, the fifth refusal example ("The status of 'Set up CI' has changed since this page loaded. Reload the page to see it.").
**Product today:** no move exists. After this change, a move pressed on a stale page is checked against the saved status, refused where the workflow refuses it, and answered with a reason in plain words on the page it came from. The spec requires neither the out-of-date wording nor a reload offer (change_spec CP-308, CP-312; Locked Answers, Gap 5). With only the moves this change offers, every press from a page whose shown status differs from the saved one is refused by the rule itself. A stale move to `cancelled` arrives only with the entry above.
**Why not this change:** the request rules it out: "No out-of-date-move handling".
**Owner:** none — for shukuba-refine
**Status:** open

## The overdue effect of a move on the overdue filter, the summary count and the All tasks list — record gap, handed on by development-specs (2026-10-19)
**Record:** `docs/fdr.md` R-88 (the overdue filter), R-96 (the summary's overdue count), R-99 (the list marking, the filter and the summary agree); `docs/SRS.md` AC-13 ("The list marking, the overdue filter and the summary count agree on all three"); `docs/UXD.md` UX-S7 (All tasks, "As UX-S4", rows with their moves) and UX-F4's last bullet (a moved task leaving a status-filtered list).
**Product today:** none of these views exists. `grep -rni 'filter\|summary' web/*.py application/*.py` finds nothing, and the one task list is a project's own (`web/pages.py:596-630`). The list marking is the only overdue view, and it follows the saved status (`domain/due_dates.py:44-46`; change_spec CP-307).
**Why not this change:** each requirement binds a view this change leaves as it is, because that view is not built. The request asks for the effect on the filter and the summary only "where those exist at this point", and neither does.
**Owner:** none — for shukuba-refine
**Status:** open

## CP-315 and its Example (a timed move in `tests/timed_run.py`) — reading set aside by development-design (2026-10-19)
**Spec lines:** change_spec CP-315; the Example row "`python3 tests/timed_run.py` on the full-volume fixture"; Locked Answers Gap 6.
**Conflict:** the request: "No out-of-date-move handling and no change to `tests/timed_run.py`", with the timed run sized into the later station `move-timed-run`. The tree: `tests/integration/test_timed_run.py::test_timed_run_appends_exactly_three_ordered_action_blocks` asserts the run prints exactly the old labels plus three blocks, "no more", and the module's `whole_run` fixture feeds `main` an exact count of timer readings. CP-318 names neither as changing.
**Reading taken:** CP-315 is not carried, so `tests/timed_run.py` and its tests stay as they are. That keeps every existing test and delivers everything the request asks. What it leaves unmet is a record, not a test: `docs/nfdr.md` QC-48 and `docs/SDD.md` § 4 TS-5 ("a change that adds a listed action adds it to the run"; SRS NFR-1 lists "moving"). Both go true again when `move-timed-run` adds the timed move (change_design.md § Records this change makes false; § Architect Review Notes, R-1).
**Owner:** none — for shukuba-refine
**Status:** open

## CP-318's "except the three named as changing" — reading set aside by development-design (2026-10-19)
**Spec lines:** change_spec CP-318 ("Every existing test passes unchanged, except the three named as changing"); Example 30.
**Conflict:** four more existing tests pin exactly what the request asks to change. The finding was measured on a prototype of this design in a clone at `c01872b`: 8 failed and 1083 passed, against 1091 passed on the unchanged tree. The four:
- `tests/architecture/test_shapes.py::test_only_the_task_features_are_added_to_domain` asserts `domain/workflow.py` does not exist.
- `tests/integration/test_task_pages.py::test_task_page_shows_the_four_fields_in_the_one_authorized_form` asserts the task page shows neither `status` nor `todo`, and its exact forms.
- `tests/integration/test_task_pages.py::test_task_page_opens_edit_form_from_saved_values` asserts the task page's exact forms per status.
- `tests/integration/test_comment_pages.py::test_written_comments_offer_no_edit_delete_or_reply_control` asserts the task page's exact forms.
**Reading taken:** CP-293, CP-297 and CP-299 release exactly the assertions that pin what they reverse, as the spec's Gap 12 released the six-column test. Each of the four keeps every other assertion. A reading that kept those assertions would drop the workflow module or the task page's moves, both of which the request asks for (change_design.md § 5, E2 and E5 to E7; § Architect Review Notes, R-2).
**Owner:** none — for shukuba-refine
**Status:** open

## CP-316's first sentence, read literally ("The workflow module imports only `errors` and the standard library") — reading set aside by development-design (2026-10-19)
**Spec lines:** change_spec CP-316, first sentence; the Example row "The layer-6 import walks, and `ruff` and `mypy` over the parts", its clause "with the workflow module importing only `errors` and the standard library".
**Conflict:** the request: "Files other than `domain/workflow.py`, the pages and routes that offer the moves, and their tests stay as they are". Read literally, the sentence bars `domain/workflow.py` from importing any `domain` sibling. The move rule would then have to sit in `domain/tasks.py` and the refusal in `domain/refusals.py`, both of which the request keeps as they are, or the refusal would sit outside the `Refusal` family.
**Reading taken:** the sentence is read as NFDR QC-13, the rule it cites: `domain/` imports `errors`, the standard library and no other part. `domain/workflow.py` imports `domain.tasks` and `domain.refusals`, and every QC-13 walk stays green (change_design.md § Architect Review Notes, R-3).
**Owner:** none — for shukuba-refine
**Status:** open
