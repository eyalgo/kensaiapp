# Tech Lead instruction — deleted-project-redirect: redirect missing-project submissions and supply the confirmation count

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it. Commands state their working directory separately.
**Scope:** Implement `change_spec.md` § Rules CP-594–CP-608 through the `web` delta in `change_design.md` § 2 and § 5.

This instruction owns the implementation tasks and their verification gates for
`tracker17 · tobiishi · 2026-10-28_deleted-project-redirect`.
Read `change_spec.md` and `change_design.md` beside this file for the required behaviour and structural decisions.

## Project layout

```text
products/tracker17/
  web/
    routes.py                                  ← modified, Tasks 1 and 2
    pages.py                                   ← modified, Task 2
  tests/integration/
    test_delete_project_routes.py              ← modified, Task 1
    test_task_routes.py                        ← modified, Task 1
    test_rename_routes.py                      ← modified, Task 1
    test_delete_project_pages.py               ← modified, Task 2
    test_pages.py                              ← modified, Task 2
    test_task_pages.py                         ← modified, Task 2
    test_move_pages.py                         ← modified, Task 2
    test_rename_pages.py                       ← modified, Task 2
    test_summary_pages.py                      ← modified, Task 2
```

Create no directory, package initializer or test module, per `change_design.md` § 2, “Blast Radius”.
The full module set remains `domain/`, `application/`, `persistence/`, `web/`, `main.py` and `errors.py`,
with `tests/`, per `docs/nfdr.md:34-38` § 1.1 QC-1.
Placement follows `docs/SDD.md:204-214` § 3, “The parts”: put address selection and rendering in `web`.
Keep the count as an application-supplied value, per the `web` row's “what a count is” boundary.
Follow the complete allowed/forbidden import graph in `docs/nfdr.md:166-197` § 1.2 QC-13–QC-19.
In particular, `web` may import `application`, `errors` and the standard library; it must not import
`domain`, `persistence`, `main`, `tests` or third-party packages, per QC-16/QC-19.

Language resolution: Python, step 1 (`system/projects/tracker17/project.md`, `Languages: Python`).
The planning review opened `<CORE>/doctrine/engineering/languages/python/README.md` and all seven
destinations in its “The seven concerns and where each is answered” table.
Use the product's Python 3.11 floor and pinned development tools, per `docs/nfdr.md:520-545`
§ 8 QC-59/QC-60/QC-62 and `pyproject.toml:1-18`.

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-28.

- **Task split:** split the single `web/` delta into a redirect task and a count task because they
  have separate observable contracts and no dependency on one another (`change_design.md:67-73`,
  § 2, “There is no ordering dependency”). Keep the required renderer argument, its production
  caller and every direct test caller together in Task 2, respecting that section's atomic-landing edge.
- **Test shape:** retain both tasks in the test-first lane. Task 1's two deleted-project cases
  exercise the direct-404 exits in `web/routes.py:869-878` and `:898-911`.
  Task 2's no-listing renderer cases exercise the row-count fallback in `web/pages.py:2037-2039`.
  The existing filtered-page count test already checks whole-project counts
  (`tests/integration/test_delete_project_pages.py:149-184`), so its extension is regression coverage
  within Task 2, rather than a separate task whose red would be artificial.
- **Coverage sharpened:** include a wholly absent form as well as the valid and invalid values in
  Task 1. This makes the “whatever the form carries” clauses explicit (`change_spec.md` § Rules,
  CP-594/CP-595), without adding a product rule.
- **Hint split:** carry design § 4's identity/address hint in Task 1. Its remaining sentence,
  “The explicit count input needs no algorithm”, leaves Task 2 without a hint because that task's
  approach is explicit in the renderer contract.
- **Structural checks stay in review:** hold the shared redirect builder, absence of row counting,
  unchanged page wording and production blast radius by the named diff/source checks below.
  These carry design § 5 T8–T10 and the spec's scope guard without inventing tests pinned to this
  change's base.
- **Gate baseline:** the card's exact command, `pytest products/tracker17/tests/`, collected 2,556
  cases and exited 1 with `20 failed, 2505 passed, 31 errors in 273.53s` on 2026-10-28.
  Keep that command in both task gates because it collects the intended suite; no green baseline
  is claimed. The diagnostic command
  `pytest -q products/tracker17/tests/integration/test_label_listener.py::test_real_listener_serves_label_area_and_actions --tb=short`
  returned `PermissionError: [Errno 1] Operation not permitted` at `self.socket.bind` and
  `1 error in 0.05s`. That result identifies the listener fixture's permission restriction, not
  the cause of every failing case. No product change or assertion weakening is authorized by it.
- **Focused baseline:** the command below returned `12 passed in 1.05s`. These existing tests
  assert the old redirect behaviour and the already-working filtered count, so they are not
  pre-existing red tests for either task. The new redirect expectations and direct count-input
  cases supply each task's changed contract.

```sh
pytest -q products/tracker17/tests/integration/test_task_routes.py::test_a_missing_project_post_gets_project_not_found_and_saves_nothing products/tracker17/tests/integration/test_rename_routes.py::test_a_missing_rename_project_answers_404_without_saving products/tracker17/tests/integration/test_delete_project_routes.py::test_deleted_project_submission_changes_nothing products/tracker17/tests/integration/test_delete_project_pages.py::test_project_confirmation_counts_all_current_tasks
```

## Gate environment inputs

The inventory `git ls-files products/tracker17` listed the product's source, documentation,
`pyproject.toml` and tests, with no build-service or runner configuration.
The repository-level inventory `git ls-files .github .gitlab-ci.yml .circleci Jenkinsfile azure-pipelines.yml buildkite.yml .buildkite`
printed nothing.
No gate-environment override or amd64 requirement is stated in `docs/nfdr.md` § 8,
`docs/SDD.md` § 3–4 or the Accepted records in `docs/adr/` § Decision.
The candidate image comes from `<CORE>/doctrine/engineering/languages/python/environment.md`
§ Provisioning, “`docker.io/library/python`”; no CI version supplies a candidate tag.

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files products/tracker17 listed source, documentation, pyproject.toml and tests with no CI configuration; git ls-files .github .gitlab-ci.yml .circleci Jenkinsfile azure-pipelines.yml buildkite.yml .buildkite returned no files"
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

### Task 1: Redirect both missing-project submissions (`web/routes.py`, `tests/integration/test_delete_project_routes.py`, `tests/integration/test_task_routes.py`, `tests/integration/test_rename_routes.py`)

**Dependencies:** None

**What to build:** Give Add task and Rename the canonical bare project redirect for every readable
missing identity, at initial lookup and at the action's typed `ProjectNotFound` boundary, per
`change_spec.md` § Rules CP-594–CP-599/CP-602/CP-605 and `change_design.md` § 2, “Response boundary”.
Keep unreadable numeric targets and all live-project outcomes within the spec's § Out of Scope guard.

#### Behaviours to verify (developer updates the three test modules in this task's paths)

- `test_deleted_project_submission_changes_nothing[add-task]` — after deleting through confirmation,
  a stale Add task returns 303 and exactly `/projects/1`. Snapshot saved bytes, save calls, projects
  and tasks after deletion and before the stale request; all remain identical afterwards, including
  the surviving project's tasks. This is CP-602's Add task regression; design § 5 T1.
- `test_deleted_project_submission_changes_nothing[rename]` — the equivalent stale Rename case
  independently proves 303, the same exact bare location and the same no-save/state assertions.
  This is CP-602's Rename regression; design § 5 T1.
- `test_missing_project_add_redirects_without_saving` — for readable `99`, `0`, `00` and `00099`,
  assert the decimal identity's bare location, 303 and no save or change to saved bytes/projects/tasks.
  Exercise valid fields, no fields, blank and overlong title, invalid priority, unlisted assignee
  and invalid date against both never-held identities and a project deleted through confirmation.
  Missing identity wins over each form refusal; no typed field, refusal, failure or query survives
  in the location. CP-594/CP-596–CP-598; design § 5 T2.
- `test_missing_project_rename_redirects_without_saving` — the corresponding Rename matrix covers
  readable `99`, `0`, `00`, `00099`, a deleted project, a valid name, no fields, blank, overlong and
  already-used names. Assert the exact canonical bare location and unchanged bytes/state/save calls.
  CP-595–CP-598; design § 5 T2.
- `test_add_redirects_when_project_is_missing_at_action` — hand the real `Site` a tracker
  collaborator whose lookup succeeds and whose Add task raises `ProjectNotFound`. For valid and
  invalid values, assert the action was reached with the parsed identity, 303, canonical bare
  location, no save and no mutation. Include a leading-zero target. CP-596/CP-597; design § 5 T3.
- `test_rename_redirects_when_project_is_missing_at_action` — independently exercise the same seam
  for Rename, including valid and invalid names and a leading-zero target. Assert the selected
  action was reached and typed absence receives the bare redirect without saving or mutating.
  CP-596/CP-597; design § 5 T3.
- `test_unreadable_project_add_keeps_not_found_without_saving` and
  `test_unreadable_project_rename_keeps_not_found_without_saving` — keep the original 5,000-digit
  cases' direct 404, no Location, exact existing not-found body and unchanged-data assertions.
  Split them from the old mixed readable/unreadable tests rather than dropping them; design § 5 T2
  and `change_spec.md` § Locked Answers, Gap 6.
- In each of the two deleted-project regression cases, follow the returned location and assert
  404, the existing heading `There's no project at this address`, and no `Cache-Control` header.
  Keep the remaining deletion cases, `test_project_delete_response_policy_matches_rendered_state`
  and `test_deleted_child_submission_changes_nothing` with their assertions intact; CP-599 and
  design § 5 T4.
- Retain `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`
  with its state and cookie assertions, and the existing live-target success/refusal/failure and
  request-origin tests; CP-605 and design § 5 T8.

#### Held by review

- Every new missing-project redirect uses the existing `Site._redirect`/`_address` builder with no
  flags or query, per design § 2, “Response boundary”. Read the `web/routes.py` diff: route tests
  prove the response but cannot distinguish an identical address assembled elsewhere.
- Keep the request checks first and catch `ProjectNotFound` by type before form-refusal handling,
  per design § 2. Hand the action-time fake through the `Site` constructor; do not change request
  locking or patch names inside product modules, per design § 5 T3 and NFDR QC-28.
- Replace only the readable-target direct-404 expectations released by `change_spec.md`
  § Locked Answers, Gap 6. Keep the no-save assertions and existing not-found page wording.

#### Implement

Infer from failing tests.

```text
# Hint:
Use the existing identity parser to distinguish unreadable digits from a missing entity before
constructing a canonical address. Both initial absence and the action's typed absence use the
shared `_redirect`/`_address` seam with no flags or query.
```

#### Verification gate

From the change worktree root, run:

```sh
pytest products/tracker17/tests/
```

Pass: all cases above pass, both deleted-project regressions establish the changed redirect, and
the full suite exits 0 with no regression. Update touched test docstrings with their SRS/AC and CP
references; `tests/architecture/test_trace.py` must stay green, per CP-607 and design § 5 T10.

### Task 2: Supply the whole-project count to the renderer and every caller (`web/pages.py`, `web/routes.py`, `tests/integration/test_delete_project_pages.py`, `tests/integration/test_pages.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_move_pages.py`, `tests/integration/test_rename_pages.py`, `tests/integration/test_summary_pages.py`)

**Dependencies:** None

**What to build:** Make `pages.project_page` take the required keyword-only integer `task_count`,
and pass that supplied count to the deletion section without deriving, defaulting or replacing it
from rows or the optional listing, per `change_design.md` § 2, “Renderer contract”.
Have `Site._project_page` supply `listing.task_count` from its existing read.
Update all direct renderer callers in this task's paths in the same task, preserving their existing
assertions and rendering seams, per design § 5 T7.

#### Behaviours to verify (developer extends `tests/integration/test_delete_project_pages.py` and updates direct caller fixtures in the other named test modules)

- `test_project_confirmation_uses_supplied_count_without_listing` — with confirmation open, render
  no listing and supply a count read from the real application. Cover zero tasks with empty rows,
  one task with no rows and four tasks with fewer rows. Assert the exact current zero/one/many
  confirmation sentences from CP-600, using the application's count independently of displayed
  rows. CP-600/CP-601; design § 5 T6.
- Extend `test_project_confirmation_counts_all_current_tasks` — explicitly read the application's
  whole-project count and compare it to the confirmation. For four tasks, one in each status, assert
  `filter_status=done` actually shows one task row and `filter_label=nothing` shows none, while the
  sentence states four tasks. Cover unfiltered, sorted, refused-filter and refused-sort pages too.
  Keep the existing zero/one/many sentences, current-name assertion, control order and focus
  assertions. CP-600/CP-603; design § 5 T5.
- Existing direct callers in `test_pages.py`, `test_task_pages.py`, `test_move_pages.py`,
  `test_rename_pages.py` and `test_summary_pages.py` receive the required count: use the application's
  answer in worlds with a tracker and an explicit whole-project fixture count in page-only fixtures.
  Preserve every page, escaping, focus, move, rename and navigation assertion; design § 5 T7.
- Keep confirmation precedence and response/cache policy, including the existing 202 confirmation
  and the 404 missing-project landing, green in the existing page/route suites; CP-599/CP-600 and
  design § 5 T4/T5/T11.

#### Held by review

- `project_page` has no row-count fallback, per CP-601/design § 5 T9. From the change worktree root,
  run `git grep -n 'len(rows)' -- products/tracker17/web/pages.py` and inspect any match: none may be
  inside `project_page`. Exit 1 with no output means no matches; it is not a failed suite.
- The count is required and keyword-only with no numeric default. The route forwards the count
  from the listing it already read, without a second application call; design § 2, “Renderer contract”.
  Read both production diffs for this contract and for the absence of any new counting in `web`.
- Update `project_page`'s docstring to describe the explicit count argument rather than claiming
  the confirmation reads `listing.task_count` (`web/pages.py:1982`, “The confirmation counts”).
  This correction rides Task 2 because this task already opens the file.
- Keep all visible page wording unchanged and reuse the existing deletion rendering/escaping path,
  per CP-599/CP-600 and `change_spec.md` § Out of Scope. Read the `web/pages.py` diff and compare
  the tests' exact sentences; changing this numeric input does not authorize new copy.
- From the change worktree root, run
  `git diff "$(git merge-base main HEAD)" -- products/tracker17/domain products/tracker17/application products/tracker17/persistence products/tracker17/main.py products/tracker17/errors.py products/tracker17/docs`.
  Pass: empty output. This is a branch-only review check for design § 2's production boundary and
  read-only records, not a permanent test against a fixed revision.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root, run both required suites separately:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From `products/tracker17/`, with the product's pinned development tools available, run:

```sh
ruff --version
mypy --version
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0, the version commands match `pyproject.toml`'s development pins, and
every review criterion above holds. Retain the pointer suite and existing browser history checks;
no test assertion is retired by the renderer signature change, per design § 5 T7/T10–T12.
