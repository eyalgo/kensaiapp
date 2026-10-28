# Tech Lead instruction — summary-page: a project's Summary with plain counts

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every code and test path below is relative to it.
**Scope:** Implement the project Summary, the two project-view links and titles, and the Summary's tests and timed read, per sibling `change_spec.md` CP-490–CP-512 (L23–L65) and `change_design.md` §§ 2–5 (L27–L291).

This instruction owns the task cut, test behaviours and verification gates for `tracker17 · tobiishi · 2026-10-28_summary-page`. Open sibling `change_spec.md` and `change_design.md` for their rules and interface contracts; this instruction does not replace either.

## Project layout

```text
products/tracker17/
  domain/
    summary.py                           ← new
    __init__.py                          ← modified, public re-exports
  application/
    tracker.py                           ← modified
    __init__.py                          ← modified, public re-exports
  web/
    routes.py                            ← modified
    pages.py                             ← modified
    style.css                            ← modified
  tests/
    unit/
      test_summary.py                    ← new
    integration/
      test_summary_tracker.py            ← new
      test_summary_routes.py             ← new
      test_summary_pages.py              ← new
      test_pages.py                      ← modified
      test_task_pages.py                 ← modified
      test_routes.py                     ← modified
      test_timed_run.py                  ← modified
    architecture/
      test_shapes.py                     ← modified
      test_trace.py                      ← modified
    e2e/
      test_summary.py                    ← new
    timed_run.py                         ← modified
```

Create the five new test files and `domain/summary.py` in the existing directories; no new package or `__init__.py` is needed (`change_design.md` § 2 and § 5:L33–L41,L223–L240).

Placement follows `docs/SDD.md` § 3, “The parts” and “The direction of dependence” (L198–L235): Summary rules in `domain`, state/clock reads in `application`, addresses/HTML/CSS in `web`, measurement in `tests/timed_run.py`.
The unchanged `persistence`, `main.py` and `errors.py` complete the module set fixed by `docs/nfdr.md` § 1.2 “Forbidden imports” (L145–L176).
Keep `domain` dependent only on its own part, `errors` and the standard library; `application` may use `domain`/`errors`; `web` may use `application`/`errors` and never imports `domain` (`docs/nfdr.md` QC-13–QC-19:L153–L176).

## TL Review Notes

The following are Tech Lead decisions made on 2026-10-28.

- **Separate browser gate:** Add the explicit `pytest tests/e2e/` gate to Task 3 because the project-card command excludes that directory (`tests/conftest.py`, “The collection rule”, L7–L9 and `pytest_ignore_collect`, L42–L48), while CP-511/CP-512 require browser proof (`change_spec.md` § Rules:L62–L65).
- **Trace follows file creation:** Each task updates `domain/summary.py`'s opening trace and the Summary-specific trace assertion for the files that task creates; the complete participant set is checked in Task 4. This makes the design's “Participants are named only once their paths exist” executable without future-path failures (`change_design.md` § 3 A:L90–L95 and § 5 T13:L236).
- **Unicode ordering edge added:** Task 1 includes different exact names with the same case-folded key, beyond `Amy`/`amy`, because the design chooses `(name.casefold(), name)` and exact bucket identity (`change_design.md` § 3 A:L69–L75). This adds proof of the chosen ordering rather than a new name rule.
- **Gate command retained:** The card's suite passed all 1,964 tests in this worktree under Python 3.15.0 and pytest 9.1.1, with local-listener permission and normal Ctrl-C handling: `python3 -c 'import os, signal; signal.signal(signal.SIGINT, signal.SIG_DFL); os.execvp("pytest", ["pytest", "products/tracker17/tests/"])'` returned `1964 passed in 146.60s`, exit 0. This wrapper changes only the launched process's signal disposition; the executed suite arguments remain the card's.
- **Gate runtime conditions:** Task gates require local socket binding and normal Ctrl-C handling. The restricted listener probe returned `PermissionError: [Errno 1] Operation not permitted` at `self.socket.bind`; the signal probe returned `SIG_IGN = 1` and `inherited SIGINT = 1`; the startup probe timed out at `child.communicate(timeout=30)` after sending SIGINT (`tests/integration/test_start.py`, `_run_real_start`:L516–L535). The full listener-authorized run retaining that ignored signal returned `12 failed, 1952 passed in 507.35s`, all twelve failures in the startup tests. The exact startup case passed in 0.55 seconds after the process-only signal reset used in the green baseline command. These are execution conditions, not new product rules or permission to skip existing tests.
- **Environment evidence checked:** The recorded JSON was accepted by `core/tools/gate_suite.py record` and `check`: `record exit: 0`, `resolves — owners-mac: the product has no CI, so its gates run on the owner's Mac`, `check exit: 0`. No suite, container or guest was started by that check (`core/prompts/gate_suite.md` § The check).
- **Task cut retained:** Tasks 1–4 correspond to A–D because each exposes one cohesive responsibility and the design's atomic-landing edges bind the feature/shape assertions, route/sample assertions, link/title compatibility assertions and timed-output expectations to their subjects (`change_design.md` § 3:L185–L203). No dependency is added solely to express order.
- **Timed read retained:** Task 4 carries CP-509 as specified, including the upstream resolution of the request's deferral; this plan makes no further scope decision (`change_spec.md`, “Locked Answers”, e-2:L132).
- **Language resolution:** Python, step 1 from `system/projects/tracker17/project.md` `Languages: Python`; opened the Python packet router, layout, conventions, quality gates, environment and `core/doctrine/engineering/testing_python.md`. The product's NFDR fixes the narrower module and test layout (`docs/nfdr.md` §§ 1.2, 9:L145–L176,L524–L566).

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files inventoried 5754 tracked paths; git ls-files products/tracker17 inventoried 246 paths. git ls-files .github .gitlab-ci.yml Jenkinsfile azure-pipelines.yml Makefile .buildkite .circleci returned no paths. Inspection of tracked configuration/build/workflow paths found no product or repository CI runner. products/tracker17/pyproject.toml configures dependencies, Ruff, mypy and pytest; root pyproject.toml configures test tools; Containerfile builds the owner-run sandbox image, not a CI job. The .claude/workflows files are local skill workflows, not product CI."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

No CI/toolchain source states a product gate container tag; the candidate deliberately carries no tag, rather than inferring one from the machine's interpreter or the unrelated sandbox image (`core/prompts/gate_suite.md` § Step 3, “The container candidates”).
The worktree decisions read for this block are `docs/adr/README.md`, ADR-0001–ADR-0011, `docs/nfdr.md` §§ 1–9 and `docs/SDD.md` § 3; none names a gate-environment override or an amd64 requirement (those files' decision sections; `docs/nfdr.md` § 8:L492–L522).

### Task 1: Pure project Summary (`domain/summary.py`, `domain/__init__.py`, `tests/unit/test_summary.py`, `tests/architecture/test_shapes.py`, `tests/architecture/test_trace.py`)

**Dependencies:** None

**What to build:** Add the pure Summary computation and its immutable public values, with unit and architecture proof, per `change_design.md` § 3 A:L51–L98 and § 5 T01–T04/T13:L224–L227,L236.

Expose `summarize_project(state: TrackerState, project_id: int, today: date) -> ProjectSummary | None` and the frozen values below; keep existing public exports (`change_design.md` § 3 A, “Exposes”, L56–L67).

| Value | Required fields |
|---|---|
| `StatusCount` | `status: TaskStatus`, `count: int` |
| `PriorityCount` | `priority: Priority`, `count: int` |
| `AssigneeCount` | `assignee: str \| None`, `count: int` |
| `ProjectSummary` | `project: Project`, `total: int`, `status_counts: tuple[StatusCount, ...]`, `priority_counts: tuple[PriorityCount, ...]`, `overdue: int`, `no_due_date: int`, `assignee_counts: tuple[AssigneeCount, ...]` |

Keep absence distinct from an empty project, identifiers distinct from display labels, and all ordering/count rules in this part (`change_design.md` § 3 A:L56–L88).
Add `summary` to `LANDED_FEATURE_WORDS` and to the shape test's positive landed set; release only the old exclusion of `summary.py`, preserving the exact saved-state field check (`change_spec.md`, “Locked Answers”, f-5:L143; `tests/architecture/test_shapes.py`, `test_only_the_task_features_are_added_to_domain`:L175–L202).

#### Behaviours to verify (developer adds tests to `tests/unit/test_summary.py` and `tests/architecture/test_trace.py`)

- `test_summary_counts_only_the_requested_project` — Use CP-507's one mixed project plus Beta; assert every row/order and both total identities against the exact five-task Example, including listed `bo` at zero and no `dan` row (`change_spec.md` CP-507 and Examples:L58,L81–L82; design T01).
- `test_summary_preserves_required_zero_rows` — Present empty projects with listed names and with no names, plus a populated project lacking some statuses/priorities, retain every required zero and the final `None` bucket (`change_spec.md` CP-496/CP-499/CP-502:L32,L37–L47; design T02).
- `test_missing_project_is_distinct_from_empty_project` — An unknown identity yields `None`, not a zero result (`change_design.md` § 3 A:L56–L59; design T02).
- `test_summary_assignees_keep_list_order_then_exact_casefold_order` — Deliberately scramble task storage order and listed alphabetical order; assert listed insertion order, then `Amy`, `amy`, `zed` with exact-case ties, repeated-name counts and exact whitespace identity (`change_spec.md` CP-499/CP-500:L37–L43; design T03).
- `test_summary_casefold_ties_keep_exact_names_separate` — Include two different exact names whose case-folded forms match, such as `Straße` and `STRASSE`; count separately and break the ordering tie by exact text (TL addition above; `change_design.md` § 3 A:L69–L75).
- `test_summary_omits_removed_names_with_only_closed_or_other_project_tasks` — Neither closed-only names here nor names found only in Beta create an unlisted row (`change_spec.md` CP-499:L37–L42; design T03).
- `test_summary_does_not_merge_a_real_unassigned_name_with_none` — A listed literal `(unassigned)` and the actual unassigned bucket remain two ordered rows with independent counts (`change_spec.md`, “Locked Answers”, b-5:L138; design T03).
- `test_summary_overdue_uses_the_supplied_date` — Yesterday/open counts; today/open, undated/open and yesterday in either final status do not; changing the supplied day changes the verdict (`change_spec.md` CP-497/CP-508:L33,L59; design T04).
- `test_summary_undated_count_includes_every_status` — Undated `done` and `cancelled` tasks contribute to no-due-date while never contributing to open-assignee counts (`change_spec.md` CP-498:L34; design T04).
- `test_summary_is_an_immutable_read` — Input remains equal, every result/row is frozen and tuple-backed, counts are nonnegative, and unassigned identity is `None` (`change_design.md` § 3 A:L56–L88; design T04).
- `test_summary_entry_names_requirements_and_existing_participants` — Require FR-38, the overdue/trace requirements and every participating/checking path that exists at this task; keep all generic path, requirement, import, reach and frozen walks (`change_spec.md` CP-504–CP-506:L53–L55; design T13).

#### Held by review

- CP-505's single-rule ownership — Read the Summary's calls to the public project filter for scope/status/priority/overdue and its use of `TaskStatus.is_open`; agreement examples alone do not prove the absence of copied predicates (`change_spec.md` CP-505:L54; `domain/filtering.py`, `filter_project_tasks`/`_matches`:L149–L158,L280–L288; `domain/tasks.py`, `TaskStatus.is_open`:L54–L65).
- CP-506's no wording — Read the domain diff for displayed labels/HTML, and the exports for re-export-only changes; the import/reach walks cannot establish every wording decision (`docs/nfdr.md` QC-20:L180–L187; `change_design.md` § 3 A:L84–L95).

#### Implement

Infer from failing tests.

# Hint:
Compose public project-filter selections for total/status/priority/overdue; aggregate open assignees from the whole-project selection so removed names remain countable. Keep bucket identity separate from its label, and return ordered immutable rows.

#### Verification gate

From the instance change-worktree root, run `pytest products/tracker17/tests/`. From the product root, run `python3 -m compileall -q domain`, `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` (`project.md`, Test command; `docs/nfdr.md` QC-62:L509–L522; Python packet quality gates § The two gates).

Pass: the new unit/trace behaviours and all existing tests pass, no unknown trace path is introduced, and each quality command exits 0. Apply the runtime conditions recorded in TL Review Notes to every task gate.

### Task 2: Current-state Summary read (`application/tracker.py`, `application/__init__.py`, `tests/integration/test_summary_tracker.py`, `domain/summary.py`, `tests/architecture/test_trace.py`)

**Dependencies:** Task 1 — its pure Summary function and values.

**What to build:** Add `Tracker.project_summary(project_id: int) -> ProjectSummary | None`; re-export the Summary values and their enum/project types through `application`; update the Summary trace for this task's checking file (`change_design.md` § 3 B:L100–L113 and § 5 T05:L228).

Use one injected clock read converted to the machine's local date and one current-state computation; add no aggregate, HTML, save, state assignment or cached result (`change_design.md` § 3 B:L106–L111).

#### Behaviours to verify (developer adds tests to `tests/integration/test_summary_tracker.py`)

- `test_summary_reads_the_injected_clock_once_per_call` — Assert the recording clock receives exactly one call for populated, empty and missing projects, and the recording saver receives none (`change_design.md` § 3 B:L106–L113; design T05).
- `test_summary_uses_the_machine_local_calendar_day` — Supply an instant across the UTC/local date boundary and set the process timezone through the environment; the count follows the machine-local day rather than the instant's unconverted date (`change_spec.md` CP-497:L33; design T05; `tests/integration/test_sort_tracker.py`, `local_zone` fixture:L80–L85).
- `test_summary_recomputes_after_midnight` — The next clock instant crosses local midnight and the next Summary changes overdue counts while the previous immutable result remains its original snapshot (`change_design.md` § 3 B:L106–L111; design T05).
- `test_summary_reads_current_tasks_and_assignees_without_saving` — After existing add/move/assignee actions, recompute the correct counts and name rows; observe no additional saves from the read and no state change (`change_design.md` § 5 T05:L228).
- `test_summary_distinguishes_missing_empty_and_current_project_metadata` — Preserve the project identity/name/description exactly, using successive same-identity states to prove rename continuity without introducing a rename action (`change_spec.md` CP-493:L27; `change_design.md` § 5 T05/T07:L228,L230).
- Extend `test_summary_entry_names_requirements_and_existing_participants` to require this task's application participant/checker paths (`change_spec.md` CP-504:L53; design T13).

#### Held by review

- No rules move outward — Read the application diff: it delegates to Task 1 and handles the clock; it does not count, classify open tasks or sort rows (`docs/SDD.md` § 3 application row:L204; `change_design.md` § 3 B:L103–L111).

#### Implement

Infer from failing tests.

#### Verification gate

From the instance change-worktree root, run `pytest products/tracker17/tests/`. From the product root, run `python3 -m compileall -q domain application`, `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` (`project.md`, Test command; `docs/nfdr.md` QC-62:L509–L522).

Pass: every Task 2 behaviour and existing test passes; all quality commands exit 0; application adds no forbidden import or saver call on this read.

### Task 3: Project views, Summary route and page (`web/routes.py`, `web/pages.py`, `web/style.css`, `tests/integration/test_summary_routes.py`, `tests/integration/test_summary_pages.py`, `tests/integration/test_pages.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_routes.py`, `tests/e2e/test_summary.py`, `domain/summary.py`, `tests/architecture/test_trace.py`)

**Dependencies:** Task 2 — the Summary read and application exports.

**What to build:** Add the Summary GET/page and shared project-view navigation, titles, escaping and wrapping styles; preserve the existing action-page contracts and update the released compatibility assertions alongside their subjects (`change_design.md` § 3 C:L115–L155 and atomic edges:L193–L199).

Register `GET /projects/[0-9]+/summary` as `PAGE` and expose `pages.summary_page(summary: ProjectSummary) -> str`; `/projects/{id}` remains Tasks (`change_design.md` § 3 C:L117–L126).
Use the existing request check/lock and safe digit parsing, call the Summary read once, and map absence to the existing project 404 (`change_design.md` § 3 C:L121–L126; `web/routes.py`, `Site.handle`/`_identity`:L260–L282,L340–L350).
Place one Tasks-then-Summary pair immediately after the project heading in both renderers; use base identity addresses without query/fragment, preserve project-name spaces, and retitle only project Tasks/Summary views (`change_spec.md` CP-491–CP-493:L25–L27; `change_design.md` § 3 C:L128–L136).
Render Task 2's ordered values without recomputing or sorting; include the header, empty invitation and plain counts, with no form, count links or automatic refresh (`change_spec.md` CP-494/CP-496/CP-502/CP-503:L28,L32,L47,L50).
Place the published strings from sibling `change_text.md` verbatim; the existing product standard is `docs/CONTENT.md`, and presentation follows `docs/DESIGN.md` (`change_design.md` § 3 C:L138–L150; `core/roles/CROSS_ROLE.md` § 2).
Add Summary to the exact route sample and every-page builder checks, update only the two project title expectations and the header test's internal-address allowance released by the spec, and keep the other assertions (`change_spec.md`, “Locked Answers”, f-1–f-3:L139–L141).

#### Behaviours to verify (developer adds tests to `tests/integration/test_summary_routes.py`, `tests/integration/test_summary_pages.py`, and `tests/e2e/test_summary.py`)

- `test_overdue_mark_filter_and_summary_agree` — With the handed-in clock, only the open task due yesterday is marked and returned by the overdue filter; rendered Summary overdue is 1 beside open/due-today, undated, done/yesterday and cancelled/yesterday cases (`change_spec.md` CP-508:L59; design T06).
- `test_summary_get_is_a_read_of_the_requested_project` — Assert 200/HTML, exactly one Summary read, current project metadata, unchanged state/saves over three reloads, and a full Summary despite filter/sort/move query values (`change_spec.md` CP-490/CP-494:L24,L28; design T07).
- `test_summary_missing_and_oversized_identity_use_project_not_found` — Both unknown IDs and digits longer than Python parses produce the existing 404/title; a same-identity renamed fixture keeps both addresses and shows the new heading/title (`change_spec.md` CP-493/CP-495:L27,L29; design T07).
- `test_summary_has_all_ordered_plain_rows_and_only_allowed_links` — Assert total, all statuses/priorities, overdue, undated and ordered assignees, their complete counts including zeros, language/header/single title, no form/script/refresh, and the exact CP-503 link set; neither label nor numeral has an anchor/control ancestor (`change_spec.md` CP-491/CP-494/CP-496/CP-503/CP-512:L25,L28,L32,L50,L65; design T08).
- `test_empty_summary_invites_first_task_beside_all_zero_rows` — With zero and nonzero listed names, retain every zero row and the invitation's base Tasks link; preserve the empty Tasks invitation (`change_spec.md` CP-502:L47; design T08/T11).
- `test_project_and_assignee_text_is_escaped_without_normalization` — Exercise `<`, `&`, quotes, padded and long names; assert exact parsed heading/title/cell text, no inserted elements/attributes, and independent literal `(unassigned)`/`None` rows (`change_spec.md` CP-492/CP-501:L26,L44; design T09).
- `test_tasks_view_pair_and_title_survive_every_outcome` — Parameterize plain/empty, filter/sort/combined/no-match, filter/sort refusal, add completion/refusal/save failure, move completion, cancellation confirmation, back-out and refused moves; each has the pair immediately under the heading and the Tasks title, with Tasks clearing choices (`change_spec.md` CP-491/CP-492:L25–L26; design T10).
- `test_new_navigation_preserves_outcome_focus_and_response_contracts` — Keep completion/refusal strings, the existing focus owner/descriptions and 202/no-store move contracts; preserve task-page titles and leave All tasks without a Summary view (`change_spec.md` CP-492 and Out of Scope:L26,L122–L127; design T10/T11).
- `test_summary_route_inherits_state_headers_and_request_checks` — Add the route's sample to `test_every_route_leaves_state_and_headers_as_the_rules_say`; assert no saves/cookies, CSP header with self-only/no-script/frame-ancestors, no CSP meta, refusal under wrong Host/cross-site/same-site, allowed reads with absent/none/same-origin marks, and inclusion in the existing outbound-connect audit (`change_spec.md` CP-510:L61; design T12).
- `test_browser_can_open_summary_and_return_to_tasks` — Drive Alpha Tasks → Summary → Tasks in the running tracker, asserting both exact titles/pairs, complete plain counts and empty-project invitation; enter Summary from a scrolled Tasks page and assert page start (`change_spec.md` CP-494/CP-511:L28,L62; design T16).
- `test_browser_summary_stays_a_snapshot_until_reloaded` — Load Summary, perform an existing data action in a second tab, observe the first page unchanged, then reload to the current counts with no additional save (`change_spec.md` CP-494:L28; design T16).
- `test_summary_links_work_with_keyboard_and_visible_focus` — Reach and activate both view links with Tab/Enter; assert visible focus and the 24×24 CSS-pixel target floor or a specifically identified permitted exception (`change_spec.md` CP-512:L65; design T17).
- `test_summary_names_and_groups_reflow_at_four_hundred_percent` — At a 1280-pixel window and 400% browser zoom, exercise long/special-character names, check exact visible text/title, wrapped groups and no page-level horizontal overflow; record the zoom/viewport method in the test's proof (`change_spec.md` CP-501/CP-512:L44,L65; design T17).
- Extend the Summary-entry trace assertion for all Task 3 participant/checker paths (`change_spec.md` CP-504:L53; design T13).

#### Held by review

- One escape path and no domain logic in web — Read each typed interpolation and title through `_escape`/`_document`; read the renderer for direct use of the supplied rows with no aggregate/ordering rule (`docs/nfdr.md` QC-23/QC-36:L230–L234,L307–L315; `web/pages.py`, `_escape`/`_document`:L380–L382,L400–L420).
- Keep unrelated production surfaces intact — From the instance change-worktree root, `git diff "$(git merge-base main HEAD)" -- products/tracker17/main.py products/tracker17/errors.py products/tracker17/persistence products/tracker17/domain/filtering.py products/tracker17/domain/sorting.py products/tracker17/domain/due_dates.py` must be empty; this is a change-only review, never a permanent suite assertion (`change_design.md` § 2:L33–L39; § 3 A:L77–L88).

#### Implement

Infer from failing tests.

# Hint:
Use one project-view link renderer at the shared project-page assembly point. Summary sheets wrap instead of inheriting the task-table minimum widths and scroll container.

#### Verification gate

From the instance change-worktree root, run `pytest products/tracker17/tests/`. From the product root, run `pytest tests/e2e/`, `python3 -m compileall -q domain application web`, `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` (`project.md`, Test command; `docs/nfdr.md` §§ 8–9:L509–L566).

Pass: all existing and new in-process/browser tests pass, including exact route enumeration and released assertion replacements; all quality commands exit 0; the review diff is empty for the protected surfaces. Browser prerequisites and local-listener permission are required; omission of layer 5 does not satisfy this gate (`tests/e2e/conftest.py`, `TrackerFactory.start` and `browser` fixtures; `tests/conftest.py`:L7–L9).

### Task 4: Timed Summary read and completed trace (`tests/timed_run.py`, `tests/integration/test_timed_run.py`, `domain/summary.py`, `tests/architecture/test_trace.py`)

**Dependencies:** Task 3 — the real Summary GET/page and its read result.

**What to build:** Add `measure_project_summary(*, site, saved_data, timer) -> list[Timed]`, its separate loaded fixture at 1,000 tasks × 20 comments, the final fixture/measurement output block and its verdict contribution; finish the Summary entry's trace (`change_design.md` § 3 D:L157–L183; § 5 T14/T15:L237–L238).

Time exactly one GET, with saved-byte readbacks and independently computed expected rows outside the measured interval; require the exact target Summary, correct plain rows, unchanged bytes and elapsed time strictly below 1 second (`change_design.md` § 3 D:L171–L181).
Use `change_text.md`'s fixture description and measurement label, reporting actual loaded volume/text lengths; preserve every existing line's label and position before the appended block (`change_design.md` § 3 D:L163–L169; `change_spec.md` CP-509:L60).
Update the whole-run label expectations and all `_run_readings` callers with the single Summary interval; complete the entry docstring and its assertion only with real paths (`change_design.md` atomic edge D:L200–L203; § 5 T13–T15:L236–L238).

#### Behaviours to verify (developer adds tests to `tests/integration/test_timed_run.py` and extends `tests/architecture/test_trace.py`)

- `test_timed_summary_reads_real_full_volume_once` — A real Summary over the independent loaded fixture passes, and a handed-in request recorder sees exactly one GET of the target Summary (`change_design.md` § 3 D:L171–L181; design T14).
- `test_timed_summary_enforces_the_strict_one_second_limit` — Below 1 second passes, exactly 1 and above fail; return one measurement and propagate its result to the existing verdict (`change_spec.md` CP-509:L60; design T14).
- `test_timed_summary_rejects_fast_incorrect_responses` — Independently exercise Tasks instead of Summary, another project's Summary, 404/forbidden/failed response, missing/wrong row, count or label linked, and changed saved bytes; every case fails even with a fast timer (`change_spec.md` CP-503/CP-509:L50,L60; design T14).
- `test_timed_summary_validates_rows_independently` — Derive expected counts and exact assignee identities/order from the loaded fixture without calling the Summary/domain-filter/application read as an oracle; prove a response with equal totals but wrong category/assignee rows fails (`change_design.md` § 3 D:L173–L178; design T14).
- `test_timed_summary_checks_fixture_and_saved_bytes_outside_the_interval` — A supplied timer/request seam verifies that only the GET lies in the measured interval and that refusal/wrong body/mutation cannot be accepted (`change_design.md` § 3 D:L171–L181; design T14).
- `test_timed_run_appends_summary_after_all_existing_blocks` — Update the released exact-label assertion, keeping old/new/move/filter/sort blocks in place and appending only the published Summary fixture/measurement lines; ensure all whole-run injected timers have the new interval (`change_spec.md`, “Locked Answers”, f-4:L142; design T15).
- `test_timed_run_includes_summary_failure_in_exit_status` — A slow, at-limit, refused, failed, corrupt or mutating Summary alone makes the full run nonzero while earlier successful statuses remain unchanged (`change_spec.md` CP-509:L60; design T15).
- `test_summary_fixture_report_uses_loaded_volume_and_text_lengths` — Assert 1,000 tasks, 20 comments on each task and the reported ordinary text lengths against the data read back; the Summary fixture's location differs from every old fixture and the product's data (`change_design.md` § 3 D:L159–L169; design T15).
- `test_summary_entry_names_every_participant_and_check` — Require the completed Summary trace: FR-38, FR-25, FR-35 and NFR-9; `application/tracker.py`, `application/__init__.py`, `web/routes.py`, `web/pages.py`, `web/style.css`; the five new test files, the modified compatibility/architecture/timing checking modules and `tests/timed_run.py`; every named path exists and every requirement resolves (`change_spec.md` CP-504:L53; `change_design.md` § 3 A:L90–L95 and § 5 T13:L236).

#### Held by review

- Keep expected values independent — Read the harness diff for fixture-derived expectations rather than reuse of the production Summary as its own oracle (`change_design.md` § 3 D:L173–L178).
- Preserve old instrumentation — From the instance change-worktree root, `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py` must show the additive Summary block and timer/label compatibility changes while retaining each existing action and its failure propagation; do not turn this change-relative check into a suite test (`change_spec.md` CP-509:L60 and Locked Answer f-4:L142; `change_design.md` atomic edge D:L200–L203).

#### Implement

Infer from failing tests.

# Hint:
Measure one read; check saved bytes and independently derived page expectations outside the interval. The existing filter Apply predicate is not a Summary predicate.

#### Verification gate

From the instance change-worktree root, run `pytest products/tracker17/tests/`. From the product root, run `pytest tests/e2e/`, `python3 tests/timed_run.py`, `python3 -m compileall -q main.py errors.py domain application persistence web tests`, `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` (`project.md`, Test command; `docs/nfdr.md` QC-48/QC-62 and § 9:L435–L442,L509–L566).

Pass: every command exits 0, all prior tests remain green alongside the new Summary tests, every old timed line keeps its position/label, the final Summary block validates the real target page with unchanged saved bytes below the strict limit, and the complete trace resolves to real files. The review checks finish with this change and pin no commit into the permanent suite.
