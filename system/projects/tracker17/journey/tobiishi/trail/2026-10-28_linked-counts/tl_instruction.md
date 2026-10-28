# Tech Lead instruction — linked-counts: Summary counts open the tasks they count

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Make the nine status, priority and overdue counts ordinary links, with the existing filter behavior and counts, and keep the timing checker valid for the linked cells.

This plan owns the task cut and verification scaffold for `tracker17 · tobiishi · 2026-10-28_linked-counts`.
Read the sibling `change_spec.md`, CP-513–CP-528, and `change_design.md`, §§ 2–5, for the behavior and design contracts.
Published names come verbatim from the sibling `change_text.md`, including its singular, zero and plural forms.
The plan's home is `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, `journey/tobiishi/<key>/`.

## Project layout

```text
products/tracker17/
  web/
    pages.py                                    ← modified, Task 2
    style.css                                   ← modified, Task 2
  tests/
    timed_run.py                                ← modified, Task 1
    integration/
      test_timed_run.py                          ← modified, Task 1
      test_summary_pages.py                      ← modified, Task 2
      test_summary_routes.py                     ← modified, Task 2
      test_pages.py                              ← modified, Task 2
    e2e/
      test_summary.py                            ← modified, Task 2
```

No directory, package, export or dependency is added. The placement decision follows `docs/SDD.md:198–235`, **The parts**: addresses, page construction and styling belong to `web`; the harness belongs to the existing `tests/` boundary.
Keep all five runtime parts within `docs/nfdr.md` § 1.2, QC-13–QC-19: `domain` → `errors`/standard library; `application` → `domain`/`errors`; `persistence` → `domain`/`errors`; `web` → `application`/`errors`; `main.py` → all four/`errors`; `errors.py` → no product part.
Each part's forbidden edges remain those records' own clauses.
Task 2 receives the existing typed filter vocabulary through `application`, never by importing `domain` from `web` (QC-16).
The counts, filter, overdue rule, sort, clock, saving and routing interfaces remain the existing ones (`domain/summary.py:94–120`, **summarize_project**; `application/tracker.py:259–288`, **project_summary/project_task_list**).

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "In the change worktree, git ls-files .github .gitlab-ci.yml Jenkinsfile azure-pipelines.yml .circleci buildkite.yml returned no paths. git -C products/tracker17 ls-files listed the product's source, docs, tests, pyproject.toml, README.md and .gitignore, with no CI configuration. A full git ls-files inventory filtered for .github/, .gitlab, Jenkinsfile, azure-pipelines, .circleci, .buildkite, buildkite, bitrise, appveyor, .travis, Taskfile and Makefile also returned no candidates."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

## TL Review Notes

- **Language resolution:** Python, step 1, the project card's **Languages** line. Opened `<CORE>/doctrine/engineering/languages/python/README.md`, its environment and quality-gate files, and `testing_python.md`/`testing_doctrine.md` for the scaffold's test layers.
- **Task cut, Tech Lead decision, 2026-10-28:** Keep design B as Task 1 and A as Task 2. Task 1 broadens the measurement reader and its independent tests; Task 2 consumes that capability. This preserves the green point described in `change_design.md` § 3, **Build sequence**, without separating a page change from the existing assertions it necessarily replaces.
- **Contract reconciled, Tech Lead decision, 2026-10-28:** Retain Alpha's full-membership fixture and use populated Beta for zero status/priority/overdue destinations. CP-525 requires both all categories populated and a zero category on the same project (`change_spec.md:51–56`, **The tests the request and the records require**). Those cannot both hold. The spec's **Examples**, Beta done 0, supplies the separate zero project. This plan adopts the design's multi-project resolution rather than silently claiming the same-project clause was met. The existing `deferred_decisions.md`, **CP-525's zero-count fixture placement**, records the reading set aside.
- **Coverage strengthened, Tech Lead decision, 2026-10-28:** Task 1 adds explicit rejection of ambiguous or nonnumeric count-cell structures. A parser that merely removes tags can accept extra markup or lose group identity, the risk named in design § 4 B. Task 1's positive linked samples are edited copies of the current real response; they do not require Task 2's renderer to exist first.
- **Coverage strengthened, Tech Lead decision, 2026-10-28:** Task 2 explicitly verifies that count targets on a Summary loaded with unrelated filter/sort/outcome query parameters still contain only the prescribed one pair. The existing request test already exercises such a Summary (`tests/integration/test_summary_routes.py`, **test_summary_get_is_a_read_of_the_requested_project**); checking its anchors closes CP-516's query-leak edge.
- **Type precision, Tech Lead decision, 2026-10-28:** Keep `FilterField` and the summary's typed status/priority identities at the link-selection boundary. If link metadata is represented as a value, give it a named typed shape with an optional link value rather than mixed integers/raw HTML or an unconstrained category string. This refines design § 4 A's metadata approach within `web/pages.py` and adds no part or rule.
- **Baseline evidence:** The card's exact `pytest products/tracker17/tests/` invocation collected 2046 tests in this worktree. It exited 1 with `20 failed, 1995 passed, 31 errors in 159.61s`. A diagnostic `pytest -q products/tracker17/tests/integration/test_label_listener.py -x --tb=short` exited 1 with `PermissionError: [Errno 1] Operation not permitted` at `socketserver.py`, **self.socket.bind(self.server_address)**, before its test body ran. That is evidence of a permission-limited listener check, not evidence that this change's behaviors are red at baseline. Both tasks keep their normal test-first marker and the card's working collection command. No baseline failure is waived by this plan.

### Task 1: Accept selected anchored Summary counts in the timed checker (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** None

**What to build:** A structural Summary count-cell reader in the existing timing harness that accepts both bare numerals and the selected anchored numerals, while retaining its independent expected counts and every existing timing and rejection check (design B; T14–T16; CP-514, CP-527).
Keep the independent test reader and response-editing helpers in `tests/integration/test_timed_run.py` independent of the harness reader.
Use the current real bare-count Summary response as the base for synthetic selected-anchor responses, so this task verifies the new accepted shape before any product renderer changes.
Update affected harness/helper docstrings in these two files to describe both accepted shapes and the continuing forbidden cells.

#### Behaviours to verify

- `test_timed_summary_accepts_bare_and_selected_linked_counts` — correct bare rows and a structurally equivalent response with anchors in each of the four status, four priority and overdue count cells pass; both preserve ordered group/label/count agreement. Include all nine zero counts on an empty fixture. T14, CP-527.
- `test_timed_summary_forbids_links_outside_selected_count_cells` — retain the existing **a linked count** rejection, whose subject is Total, and **a linked label**. Add no-due-date and assignee count anchors. Include listed/unlisted assignees spelled `todo`, `low`, `Overdue` and `(unassigned)` beside the real categories and unassigned bucket. T15, CP-514.
- `test_timed_summary_rejects_ambiguous_count_cells` — reject multiple anchors, mixed extra text, nested non-anchor count markup, absent numerals and nonnumeric contents rather than recovering any digit substring. Keep label cells free of anchors. Added group/structure edge for design § 4 B.
- Extend `test_summary_oracle_reads_the_real_page_as_the_fixture_says` — the independent reader agrees with the saved fixture for both accepted shapes, including distinct category counts and assignee ordering. T14.
- Extend `test_timed_summary_validates_rows_independently` — preserve swapped-status, swapped-priority, swapped-assignee, assignee-case, assignee-order, missing-unassigned and stale-saved-state refusals for both accepted shapes. Every edited-response helper locates the intended actual cell and asserts its body changed before asking for rejection. T14.
- Preserve `test_timed_summary_rejects_fast_incorrect_responses` — wrong project/title/heading/group/count, missing row, non-HTML media type, refused/error/redirect response and changed saved bytes still fail even with a fast timer. Edited responses differ from the original. T14–T15.
- Preserve the midnight-boundary checks — rows for either calendar day bracketing the request pass, wrong rows for both fail, and the mutation changes the intended linked or bare cell. T14.
- Preserve `test_timed_summary_reads_real_full_volume_once` — 1000 tasks with 20 comments each, one same-origin Summary GET, response/saved-byte readbacks outside the measured interval, no state write and one result. T16.
- Preserve `test_timed_summary_enforces_the_strict_one_second_limit` — below one second passes; exactly one second and above fail. Preserve the whole-run label/order checks, with Summary last and no new measured action. T16.

#### Implement

Infer from failing tests.

# Hint:
Use the standard library HTML parser to recognize count cells in their Summary group and row identity/position. Accept the two sanctioned shapes only in the selected cells; do not strip all markup before reading digits. Keep the harness's fixture-derived expectation separate from the test oracle and mutation helpers. A malformed or missing group/row must remain a failed measurement. Keep `measure_project_summary`'s one-request timing boundary unchanged.

#### Verification gate

From the instance change worktree:

```sh
pytest products/tracker17/tests/integration/test_timed_run.py
pytest products/tracker17/tests/
```

From the product root:

```sh
python3 tests/timed_run.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0. The real bare-count page still passes the harness, the synthetic selected-anchor page passes, all forbidden/mutated responses fail validation, and every timed action remains below the existing limit with the same line labels/order and Summary last. No new suite failure is accepted.

### Task 2: Render and follow the nine contextual count links (`web/pages.py`, `web/style.css`, `tests/integration/test_summary_pages.py`, `tests/integration/test_summary_routes.py`, `tests/integration/test_pages.py`, `tests/e2e/test_summary.py`)

**Dependencies:** Task 1 — its timed checker accepts the linked cells that this renderer produces.

**What to build:** Attach one native anchor to each status, priority and overdue count, with names from `change_text.md` and count-link geometry/focus/reflow in the existing stylesheet (design A; T01–T13, T18).
Keep `summary_page(summary: ProjectSummary) -> str` and its group renderer inside `web/pages.py`.
Choose linked cells from typed group/row identity and construct a fresh one-choice project address.
Update `summary_page` and affected test docstrings that call all counts plain or all main links the view pair; retain their count/order/escaping/trace descriptions with CP-513–CP-528.

#### Behaviours to verify

In `tests/integration/test_summary_pages.py` (layer 4):

- Extend `test_summary_has_all_ordered_plain_rows_and_only_allowed_links` — exactly nine count anchors, each with a numeral-only text node, in the existing ordered rows. Retain title, heading, four groups, column headers, count values, no form/control/script/refresh, and the two view links. Total, no-due-date and every assignee count remain unlinked; every row header remains outside anchors. T01, CP-513–CP-515.
- Extend `test_zero_rows_are_kept_and_the_populated_summary_has_no_invitation` and `test_empty_summary_invites_first_task_beside_all_zero_rows` — every selected zero count has its link; preserve all zero rows, the empty invitation's exact wording/base Tasks target, and the populated Summary's absence of that invitation. T01, CP-513, CP-515.
- `test_summary_count_names_identify_zero_one_and_many_tasks` — all categories use the exact text artifact's names for 0, 1 and plural counts; the numeral is an unbroken prefix. Pin the required 12-todo and 3-overdue examples through their text-artifact entries. Across all Summary links, equal names imply equal addresses; Gamma's two base Tasks links are allowed. T06, CP-521–CP-522.
- `test_assignee_identity_never_selects_a_count_link` — listed/unlisted names `todo`, `low`, `Overdue` and `(unassigned)` remain plain in their assignee group, including beside a separate unassigned bucket. Preserve hostile HTML characters, padding and long names as text. T18, CP-514–CP-515, QC-36.

In `tests/integration/test_summary_routes.py` (layer 3, real Site/Tracker with injected clock and saver):

- `test_every_summary_count_opens_exactly_its_project_members` — extend AC-14 with spec Fixture A: Alpha has T1 todo/low/yesterday/unassigned; T2 in-progress/medium/undated/listed ari; T3 done/high/past/ari; T4 cancelled/critical/undated/unlisted dan; T5 todo/critical/today/unlisted eve. Current names are ari and bo; populated Beta has its independent todo task assigned to bo; Gamma is empty. For each of nine Alpha anchors assert numeral, exact URL, exact task identities and correct singular/plural match line. Explicit expected memberships are todo {T1,T5}, in-progress {T2}, done {T3}, cancelled {T4}, low {T1}, medium {T2}, high {T3}, critical {T4,T5}, overdue {T1}; never derive them with the product filter/summary. Assert the plain count cells and distinct link names on this real page too. T02, CP-514, CP-516–CP-517, CP-523, CP-525.
- `test_count_destinations_select_one_filter_and_default_sort` — on all nine destinations, only the intended filter has a choice, the other six are empty/off, the sort controls show due_date/ascending and the task rows have the default order. Add due dates whose order differs from creation order, a due-date tie preserving creation order, and an undated match last. Still exactly seven filter fields. T03, CP-516–CP-517, CP-523.
- `test_zero_links_on_populated_project_show_no_match` — follow every zero status, priority and overdue anchor on Beta. Each answers 200 with its one selected control, the exact no-match line, no task row and no error/not-found page. T04, CP-513, CP-518.
- `test_empty_project_count_links_keep_no_tasks_state` — all nine Gamma count anchors answer 200 with the existing no-tasks invitation, never the no-match line. Preserve Gamma's Summary invitation and navigation targets. T05, CP-518.
- Extend `test_summary_get_is_a_read_of_the_requested_project` — Summary addresses carrying filter, sort and outcome parameters produce the same nine fresh one-pair targets. Status URLs are `/projects/{id}?filter_status={status}`, priority URLs `/projects/{id}?filter_priority={priority}`, overdue `/projects/{id}?filter_overdue=on`; no additional key, fragment or sort choice. Added CP-516 edge.
- `test_followed_count_reads_current_saved_state` — capture Alpha's todo 2 target, move T1 to in-progress through Tracker, then follow: only T5 matches with the singular match line; the captured Summary remains unchanged. T07, CP-519.
- `test_followed_overdue_count_reads_current_local_day` — capture an overdue link before midnight, advance the handed-in clock across local midnight and follow; the list uses its load's local day and the captured Summary remains a snapshot. T07, CP-519.
- `test_count_get_and_reload_never_save` — follow each target and reload, checking Tracker state, saver calls, real saved bytes and no cookie. GET adds no state or saved field. T08, CP-520.
- Extend `test_overdue_mark_filter_and_summary_agree` without losing its existing assertions — follow the rendered overdue anchor in its own clock-controlled world and prove the same membership as marking/filter/Summary. Yesterday/open counts, today/open and done/cancelled do not. No product name is patched. T09, CP-523, CP-526.

In `tests/integration/test_pages.py`:

- Repair `test_every_page_has_a_header_with_the_projects_and_people_links` — accept precisely the supported one-choice status/priority/overdue project URLs in addition to existing base/view URLs. Retain all three header-link checks on every page and no rename/delete assertions. Do not replace the address check with unrestricted query acceptance. T10, CP-515–CP-516.

In `tests/e2e/test_summary.py` (layer 5, real listener/process with scripts disabled):

- Extend `test_browser_can_open_summary_and_return_to_tasks` — retain titles, pair, counts, no controls, empty invitation, scrolled-entry position and round trip; replace only the pair-only main-link inventory. Follow a positive count to its selected list and a zero count on a populated project to no-match. Reload and Back leave saved bytes unchanged. T08, T11, CP-518, CP-520, CP-528.
- `test_browser_count_links_have_distinct_accessible_names` — assert computed accessible names for zero, singular and plural forms across status, priority and overdue, matching `change_text.md`; numeral-only visible text remains. Check all Summary links, allowing equal names only for equal targets. T06, CP-521–CP-522.
- Extend `test_summary_links_work_with_keyboard_and_visible_focus` — retain Tasks/Summary proof. Reach all nine count links by Tab, including a zero, identify the focused anchor by its accessible name rather than visible numeral alone, assert visible focus and activate with Enter to the exact destination. Every count anchor's bounding box is at least 24 by 24 CSS pixels. T12, CP-524.
- Extend `test_summary_names_and_groups_reflow_at_four_hundred_percent` — at 320 CSS pixels keep hostile/long text, all four groups and every count link inside the viewport, with no horizontal page scroll. T13, CP-524.
- Preserve `test_browser_summary_stays_a_snapshot_until_reloaded` — the added links do not make a loaded Summary update itself. T07, CP-519.

#### Held by review

- CP-523: `web` formats supplied counts and addresses without computing membership, overdue or sort. Existing domain tests and the page/list membership tests show agreement; reading the diff checks that no second rule was introduced (owning part: `docs/SDD.md` § 3, **The parts**, domain/web rows).
- CP-527: the measurement still surrounds only the one Summary request. Task 1's tests check the boundary; reading Task 2's diff confirms no new timed action/label is added.

#### Implement

Infer from failing tests.

# Hint:
Carry optional typed link target/name metadata alongside the count within the Summary renderer. Select it at the typed row/group boundary, with the existing filter vocabulary through `application` and the page's filter-prefix convention. Use ordinary anchors and `aria-label` so only the numeral is visible. Pass dynamic text and attribute values through `_escape`; do not treat row text as trusted HTML. Scope count-link sizing to the Summary and retain its inherited visible focus and narrow-width layout.

#### Verification gate

From the instance change worktree:

```sh
pytest products/tracker17/tests/integration/test_summary_pages.py products/tracker17/tests/integration/test_summary_routes.py products/tracker17/tests/integration/test_pages.py products/tracker17/tests/integration/test_timed_run.py
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From the product root:

```sh
python3 tests/timed_run.py
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0. All nine count links reach exactly the expected same-project members; zero populated and no-tasks cases remain distinct. Keyboard activation, contextual accessible names, target size and reflow pass in the browser. AC-13 remains green. The timed run validates the actual linked page and retains every label/order with Summary last and every measured action below its existing limit. No old assertion is removed except the expressly replaced selected-cell link prohibitions and pair-only link inventories (`change_design.md` § 5, **Assertions retired**).
