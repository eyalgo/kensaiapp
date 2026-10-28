# Change Design — Rename a project from its Tasks view

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the Rename area on a project's Tasks view, its completion line, its refusal reasons and its failed-save line; the console's rename failure message; the timed run's rename labels and fixture report

---

## 1. Change Summary

Add one project rename, from the Tasks view through the existing whole-state save. The rule belongs
to `domain`, save-before-publication to `application`, and the form, request, outcome address and
page to `web` (product `docs/SDD.md` § 3, *The parts*; spec CP-546–CP-563). Extend
`tests/timed_run.py` with the same action at task volume (spec CP-566). Keep the project identity,
description, tasks, comments, other state and stored shape unchanged (spec CP-554).

All code and test paths below are relative to `products/tracker17/`; `docs/` means that product's
documents, as resolved by `development_path.py resolve` for
`tracker17 · tobiishi · 2026-10-28_rename-a-project`. The design's home is the change-unit area
specified by `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, *Per-project*, `journey/tobiishi/`.

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3, *The parts*. Its parts share the product-root Python unit;
the directories in the table below are the parts' code locations stated in their `Owns` cells.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | Owning part: `domain`. In `projects.py`, add the immutable rename outcome and rule, share creation's validation and uniqueness check, decide exact equality/no change against the current state, and replace only the matching project's name. Export the rule and outcome from `__init__.py`; keep the Projects feature docstring accurate (CP-552–CP-555, CP-558, CP-568). |
| `application/` | Modified | Owning part: `application`. In `tracker.py`, add the rename action, saving only a domain-reported change before publication. Re-export its outcome through `__init__.py` for `web` (CP-550, CP-553–CP-557). |
| `web/` | Modified | Owning part: `web`. In `routes.py`, add the rename POST, share creation's typed-refusal translation, and carry the rename outcome through the existing redirect builder. In `pages.py`, add the Rename area and its request-scoped presentation value, share `_name_reason`, and add the field/Save focus and descriptions. Reuse existing form, focus and pointer-target styling in `style.css`; change that file only if the new control fails CP-560 (CP-546–CP-561). |
| `persistence/` | Unchanged | Neither the saver interface nor the stored fields change; rename reaches the existing whole-state save (CP-554; `application/contracts.py`, `Saver`; `docs/adr/0004-whole-state-saved-atomically-on-every-change.md` § Decision). |
| `main.py` | Unchanged | Existing composition supplies the same Tracker, saver, clock and Site; no new collaborator is needed (`docs/SDD.md` § 3, `main`, SM-7). |
| `errors.py` | Unchanged | Use existing `BlankName`, `NameInUse`, `TextTooLong` and `ProjectNotFound`, already exported through `application` (`domain/refusals.py`, those classes; `application/__init__.py`). |
| `tests/timed_run.py` | Modified | Test-support module: time a project rename and its landing, check the exact saved delta and completion, report fixture lengths, and include its verdict without replacing an earlier measurement (CP-566). |

The allowed directions remain `web → application → domain`, `persistence → domain`, and
`main →` the four parts (`docs/nfdr.md` § 1.2, QC-13–QC-18). The new exports extend existing
surfaces; they replace no signature consumed by `persistence` or `main`. Those importers need no
production change. Name-displaying reads continue to resolve the current project by identity:
`Tracker.projects`/`project`, `Site._summary_page`, `Site._all_tasks_page`, and
`pages._project_cell`/`task_page` are the existing seams to verify, rather than a second stored name
on each task (`application/tracker.py`, those readers; `web/routes.py`, those page methods;
`web/pages.py`, those builders; CP-551, CP-554). Their regression coverage is T07 below.

## 3. Sub-jobs

### A — `domain/`: one project-name rule path

**Scope:** `domain/projects.py` and its public exports. Keep `check_project_values` as the common
value validation used by creation and rename. Rename supplies the project's unchanged, already
valid description. Share the name-availability check between creation and rename, with a self
exclusion for rename. Preserve creation's existing precedence: name length, description length,
blank name, then name in use (`domain/projects.py:36-61`, `check_project_values` and
`create_project`). Do not move blank-name checking ahead of description length as a side effect.

**Exposes:**

- `ProjectRenameOutcome`: frozen value with `project: Project`, `previous_name: str`,
  `changed: bool`. The previous name is the name in the state when the action runs, not a value
  carried from a stale form. It supports the completion wording CP-550 leaves open.
- `rename_project(state: TrackerState, project_id: int, name: str) -> tuple[TrackerState, ProjectRenameOutcome]`.
  A missing project raises existing `ProjectNotFound`. Otherwise, validation and availability
  precede the exact comparison with that project's current name (CP-552–CP-555, CP-558).
- An identical name returns the input state and an outcome reporting no change. A different valid
  name returns a new state with only that project's name replaced, in the same projects-tuple
  position. The tasks tuple and both counters are retained, not rebuilt (CP-553, CP-554).
- Existing creation, restoration and listing contracts remain intact. In particular, listing
  continues to use the explicit `(name.casefold(), name)` key in `list_projects`, rather than the
  position retained by rename (`domain/projects.py:64-68`, `list_projects`; CP-551).

**Depends on:** none.

### B — `application/`: rename, save, publish

**Scope:** `application/tracker.py` and `application/__init__.py`.

**Exposes:** `Tracker.rename_project(project_id: int, name: str) -> ProjectRenameOutcome`, with
the outcome also importable from `application`. It calls A against the current state once, calls
the existing `_save_then_publish` only when the outcome reports a change, and returns the outcome
only after that save succeeds. A refusal or saver failure propagates with the old state still
current; there is no application-side name comparison, disk read, clock read or validation
(`docs/nfdr.md`, QC-21, QC-44, QC-49, QC-54; `Tracker.set_operator_name` and
`Tracker._save_then_publish`; CP-550, CP-553–CP-557).

**Depends on:** A's rename rule and outcome.

### C — `web/`: one form, one POST, address-carried outcomes

**Scope:** `web/pages.py`, `web/routes.py`, and existing styling if needed for CP-560.

**Exposes — request contract:**

- `POST /projects/{id}/rename`, registered as `SUBMISSION` in `ROUTES`, reads field `name` and
  uses `_line_feeds` before the application call. It runs under Site's existing host/origin check
  and request lock (CP-552, CP-559; `Site.handle`, `_submission`, `_line_feeds`).
- A missing project answers the existing project not-found page, 404, without saving (CP-558).
  It is not redirected to an invented refusal page.
- Changed success redirects 303 to `/projects/{id}` carrying `rename_saved=<new name>`.
  If the completion wording uses the old name, carry `rename_from=<previous_name>` as well;
  CP-550 leaves that wording decision open. A no-change outcome redirects to the bare project
  address, with no completion, refusal, focus or list-choice marker (CP-550, CP-553).
- Refusals redirect to the same base address carrying `rename_refused=<existing project refusal
  code>`. Blank/in-use also carry `rename_typed`, including an explicitly empty string. Too-long
  carries no submitted text at all. Failure carries `rename_failed=save` and `rename_typed`.
  These redirects carry no filter/sort choices and no fragments (CP-550, CP-556, CP-557).
- Creation and rename share one typed-exception-to-project-refusal translation in `routes.py`,
  retaining creation's codes `BLANK_NAME`, `NAME_IN_USE`, `TEXT_TOO_LONG` and its `TextField` detail.
  The shared translator covers creation's description-too-long case too; its existing retention
  and reason remain intact. Catch the existing refusal types, not their messages. Both name
  presentations call the existing `_name_reason` in `pages.py` (CP-555;
  `Site._create`; `pages._name_reason`).
- Route unexpected failures through `_guarded` and `_report_failure`. The console line names
  the rename; exception detail stays in the console, outside the outcome address and HTML
  (CP-557; `Site._guarded`, `_report_failure`).

**Exposes — page contract:**

- A request-scoped `ProjectRenameArea` presentation value carries optional typed text, the
  recognized refusal code, a failure flag, the completed new name and optional previous name.
  Absence differs from an empty submitted value. Unknown refusal/failure markers are ignored;
  a too-long refusal discards any forged typed value too. It stores no state between requests
  (`docs/nfdr.md`, QC-8, QC-23; CP-556).
- Add optional keyword `rename_area: ProjectRenameArea | None = None` to `pages.project_page`.
  A default area renders the saved name with no autofocus. Append the Rename area after the
  list/empty/refused-results output, outside every task-count or list-result condition, so every
  Tasks-view state has it (CP-546). No other page builder adds it.
- The area's form contains its visibly labelled name field, then Save. The field receives
  `SHORT_TEXT_MAX` through `application` and no maximum-length sentence. It sends no old-name
  or shown-name field (CP-547, CP-550, CP-553; spec Locked Answer Gap 6).
- Success and a name refusal focus the Rename field. A failure focuses its Save. Exactly one
  relevant line describes that focused element through `aria-describedby`; the line never takes
  focus. Fresh loads and unchanged saves add neither a line nor autofocus (CP-550, CP-553,
  CP-556, CP-557; `docs/adr/0003-no-script-in-any-page.md` § Decision).
- The field holds the current saved name on ordinary loads, completion and too-long refusal;
  blank/in-use refusals and failures retain submitted text. Escape every value in HTML with
  `_escape`, including attributes, titles, completion and duplicate-name reasons. Normalize
  nothing else (CP-552, CP-556, CP-561; `pages._escape`, `_document`, `_name_reason`).
- Preserve the focus/outcome precedence of existing creation, task-add, move and deletion
  states. Their pages also show the ordinary Rename area. A combined, hand-written query does
  not give a second element autofocus; generated rename addresses contain no competing outcome
  markers (`pages.project_page`, its outcome precedence; CP-546).

GETs decode the address and render current state; they never call the rename action. Success and
refusal addresses therefore reconstruct their lines on reload or history traversal without another
save (CP-550, CP-556; `docs/adr/0011-a-submission-is-a-post-form-and-its-outcome-travels-in-the-address.md`
§ Decision). Rename has no confirmation step, so it adds no 202/history-cache mechanism
(CP-549; `docs/adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md`
§ Decision).

**Depends on:** B's action, outcome and application exports.

### D — `tests/timed_run.py`: rename at the existing task volume

**Scope:** only this measurement module and its corresponding harness tests.

**Exposes:** a rename measurement producing the existing `Timed` request, landing and total
results, plus a fixture report. Use a separately seeded project that holds tasks; state the task
and comment counts and ordinary text lengths. Send the same-origin POST from C. Build the expected
state independently from the loaded fixture by replacing only the target project's name, rather
than calling A to calculate the expected answer. The request counts only after a correct redirect
and exact saved-state comparison; the landing counts only after a 200 showing the new heading
and completion. The total requires both. Measure disk inspection outside the request and landing
intervals (CP-566; `tests/timed_run.py`, `TimedAction` and `_measure_action`).

Append this block after the existing measurements, and include its verdict in the run's exit
status. Do not replace the task deletion or alter an older action's fixture. Use the existing
one-second verdict for the request, landing and total (CP-566; `tests/timed_run.py`, `main`,
`verdict` and `_measure_action`).

**Depends on:** C's live POST, redirect and completion contract.

**Build sequence:** A → B → C → D. Each edge consumes the preceding contract described above.
No cross-part atomic-landing edge is required: the domain and application additions are additive,
the page keyword has a default, and the measurement is added after its route exists. The changed
Tasks-view presence assertions and the new control describe the same web delta (spec Locked Answer
Gap 10).

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `domain/` | Reuse `check_project_values` with the unchanged description, and one shared availability check with self exclusion. Retain creation's cross-field refusal precedence; immutable replacement changes only the selected project within the state. |
| B — `application/` | None |
| C — `web/` | Share typed refusal translation and `_name_reason` with creation; carry outcomes through `_address`/`_redirect`, and use native autofocus with one described line. No session or page script. |
| D — `tests/timed_run.py` | Reuse `TimedAction`/`_measure_action` for the request, landing and total; its saved-state predicate compares an independently constructed expected whole state. |

## 5. Test Additions

Test layers follow `docs/nfdr.md` § 9. New test modules name their SRS requirements and acceptance
criteria (CP-568). `T01`–`T16` below are coverage-row identifiers, not prescribed test-function names.

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T01 / A — layer 1 | `tests/unit/test_projects.py` | Rename replaces only one project's name and reports the prior/current project and change flag; no name change reports none and returns unchanged state. Cover case-only, leading/trailing spaces, exactly 200 code points including a supplementary character, and line-feed values already normalized by web. CP-552–CP-554. |
| T02 / A — layer 1 | `tests/unit/test_projects.py` | Blank: empty, ASCII whitespace and creation's other whitespace cases; exact other-project collision; 201 code points; 201 spaces selecting too-long before blank; missing identity. Assert unchanged input state and typed refusal. Keep creation's blank-name plus overlong-description precedence and existing duplicate/length assertions. CP-555, CP-558; `check_project_values`. |
| T03 / B — layer 3 | new `tests/integration/test_rename_tracker.py` | Changed rename saves once before publication; own current name saves zero times. Refusals and a failing saver retain current state. Recording saver receives only saves, and a recording clock receives no read. Stale-state comparisons use current state, never the page's old name. CP-550, CP-553, CP-555, CP-557, CP-567. |
| T04 / B — layers 2–3 | new `tests/integration/test_rename_tracker.py` | With real SavedData and several varied tasks/comments plus another project, compare every task/comment and the entire expected state before/after, including descriptions, assignees, operator name, both counters and stored keys. Reload from disk and construct a fresh Tracker: name survives restart. CP-554, CP-562. |
| T05 / C — layer 4 | new `tests/integration/test_rename_pages.py` | Area after results with tasks, no tasks, no matches, invalid filter, invalid sort, and each existing completion/refusal/failure/confirmation state. Field exact saved value, visible label, field-before-Save order, maxlength from application export, no maximum sentence, POST action and no shown-name field. Other page builders offer no rename. CP-546–CP-549, CP-564. |
| T06 / C — layers 3–4 | new `tests/integration/test_rename_routes.py`; `test_rename_pages.py` | Success: one save, 303 to unfiltered project address, new heading/title, one completion, field autofocus with line as description. Reload success and refusal locations saves nothing. Unchanged submission redirects bare, shows no outcome and adds no autofocus. CP-550, CP-553, CP-556. |
| T07 / C — layer 3 | new `tests/integration/test_rename_routes.py` | Rename Alpha to Zed beside Gamma/delta: assert Projects order and absence of the old name as this project's name. Check Tasks, Summary heading/title, All tasks Project cells, each task's Project field, and unchanged task/project/summary links; include an empty description and an empty project. CP-551, CP-554. |
| T08 / C — layer 3 | new `tests/integration/test_rename_routes.py` | Separate refusal tests for empty/whitespace, other-project name, 201 code points including 201 spaces, and missing project. Each compares saved bytes and Tracker state before/after, counts zero saves, and asserts exact existing reason/404, heading/title, retained field or complete omission of sent text from HTML and Location, and field focus/description where applicable. CP-555, CP-556, CP-558, CP-563. |
| T09 / C — layer 3 | new `tests/integration/test_rename_routes.py` | Stale page after another tab creates the desired name refuses it; after another tab renames the target, a new value overwrites it; unchanged stale field renames it back; value now equal to current saved name makes no save. CP-550, CP-553, CP-555; spec Locked Answer Gap 6. |
| T10 / C — layer 3 | new `tests/integration/test_rename_routes.py` | Failing saver: saved bytes, all name-displaying reads and current state unchanged; console identifies rename and error; failed landing retains typed value and focuses Save with its failure description; no Python error text in HTML/Location. CP-557. |
| T11 / C — layers 3–4 | new `tests/integration/test_rename_routes.py`; `test_rename_pages.py` | Reject cross-site, same-site, none, missing and other non-same-origin marks before action; retain Host checks and unchanged state. Normalize CRLF/CR once at the web boundary. Exercise `<`, `&`, quotes and spaces in field, completion and duplicate reason, title and all displayed names. Check forged too-long+typed query omits the typed value and unknown codes are inert. CP-552, CP-556, CP-559, CP-561. |
| T12 / C — layer 5 | new `tests/e2e/test_rename_project.py` | In Chromium, Tab to the field and submit with Enter; assert rename on first submission, focus and accessible description after success/refusal, visible keyboard focus and Save's pointer-target floor. Type `<b>R&D "x"</b>` and verify literal text in heading/title/Projects/field/completion, plus duplicate refusal. Actual reload, Back and Forward preserve the finished line without another action. CP-549, CP-550, CP-556, CP-560, CP-561, CP-565. |
| T13 / C — existing assertion continuity | `tests/integration/test_pages.py`; `test_filter_pages.py`; `test_sort_pages.py`; `tests/e2e/test_first_project.py` | Update the four presence assumptions named by spec Locked Answer Gap 10 and the first-project browser test's full-page form/input/button counts. Scope add-form checks to its action and Add button, retaining its fields, heading, description, invitation and title. Keep header links/addresses and absence of deletion; keep rename absent on other pages. Empty-project tests now admit the additional POST, retaining no GET/filter/sort/table and the invitation. The first-project browser test keeps the creation URL, line, exact description, pre-wrap, no textarea and heading focus, while asserting Rename separately. |
| T14 / C — layer 3 | `tests/integration/test_routes.py`; new `test_rename_tracker.py` | Add POST sample/body to route enumeration, preserving exact route-set coverage, redirects, saves, no cookies and CSP headers on every response. Drive rename and landing in no-outbound sequence. Prove the recording saver receives only saves in T03. CP-567. |
| T15 / D — harness tests | `tests/integration/test_timed_run.py` | Add four timer readings and three labels after the existing deletion block, update `_run_readings` and every fixed whole-run reading/label sequence, keeping prior verdicts. Verify correct delta/landing, no-op/refusal/failure/wrong redirect, wrong or extra saved change, missing/wrong completion, threshold failure for each interval and total, correct same-origin mark, fixture volume/lengths, and aggregate nonzero exit on failure. CP-566. |
| T16 / A–D — trace continuity | `tests/architecture/test_trace.py` (existing checks); opening docstrings of new tests and `domain/projects.py` | Existing pointer checks keep passing; Projects names FR-12 and every participating application/web/test module for this change. Preserve all prior feature/test references; no slice-wide `domain/tasks.py` docstring expansion. CP-568. |

**Examples pass.** Number the spec's Examples rows from the first scenario as E01. Coverage is:
E01→T05; E02→T05; E03→T05; E04→T05; E05→T06/T12; E06→T06/T12;
E07→T07; E08→T07; E09→T01/T06; E10→T03/T06; E11→T01/T06;
E12→T01; E13→T04; E14→T04; E15→T08; E16→T08; E17→T09;
E18→T09; E19→T09; E20→T08; E21→T10; E22→T08; E23→T11;
E24→T12; E25→T12; E26→T15; E27→T14/T03; E28→T16
(spec § Examples, rows 1–28).

**Rules pass.** Every rule-implied edge is assigned: all Tasks-view states and other-page exclusion
(CP-546)→T05/T13; shared limit/no sentence (CP-547)→T05; content placement (CP-548)→T06/T08/T10;
first press and history (CP-549/550)→T06/T12; every live name/order/address (CP-551)→T07;
exact text/code-point boundary/normalization (CP-552)→T01/T11; equal/stale/space-only differences
(CP-553)→T01/T03/T06/T09; whole-state preservation/restart (CP-554)→T04;
validation order and current uniqueness (CP-555)→T02/T08/T09; retention, too-long omission and
refusal reload (CP-556)→T06/T08/T11/T12; saver failure (CP-557)→T03/T10;
missing target (CP-558)→T02/T08; all denied origin marks (CP-559)→T11;
keyboard/focus/target size (CP-560)→T12; literal typed text (CP-561)→T11/T12;
CP-562→T04; CP-563→T08/T03/T06; CP-564→T05; CP-565→T12;
CP-566→T15; CP-567→T14/T03; CP-568→T16.

The only retired assertions are the Tasks-view absence of rename and its old total form/button
counts, released by the spec's Locked Answer Gap 10 and re-proved as scoped old-control checks
plus Rename presence in T05/T13. No other clause is retired. The old timed action readings,
labels and verdicts are retained in T15 (`tests/integration/test_pages.py:177-242`,
`test_filter_pages.py:126-136`, `test_sort_pages.py:90-103`,
`tests/e2e/test_first_project.py:54-83`,
`test_the_first_project_lands_on_its_page_with_spaces_line_break_and_created_line`;
`test_timed_run.py`, `_run_readings` and whole-run label assertions).

## Records this change makes false

None — read `docs/adr/README.md` and the accepted ADR decisions (0001–0005, 0007–0009,
0011–0012; 0006 and 0010 are superseded), `docs/fdr.md` Projects and Refusals,
`docs/nfdr.md` §§ 1–9 and RN-33, and `docs/SDD.md` § 3. Rename is already covered by
FDR R-34/R-35 and the domain/application/web boundaries; the design changes no import permission,
saving contract, stored field, identity scheme or foundation decision. The existing record gaps
for project deletion and the slice-wide docstring bar remain in `deferred_decisions.md`.

## Architect Review Notes

Decisions and review verdicts below are the architect's, 2026-10-28.

- **Language resolution:** Python — step 1, `project.md` `Languages:`. Opened
  `<CORE>/doctrine/engineering/languages/python/README.md` and its seven concern destinations;
  product ADR/NFDR decisions govern its Python 3.11 floor, pins and test layout, per
  `<CORE>/doctrine/engineering/languages/README.md` § Precedence.
- **Focus choice (b):** Choose the Rename field for successful completion, so the new name is
  directly available to edit again and its completion describes that control. CP-550 explicitly
  delegates this choice. Refusal and failure focus are those CP-556/557 already fix.
- **Shared rules by construction (b):** Reuse `check_project_values` with the unchanged saved
  description and share the availability check. This satisfies CP-555 without weakening creation's
  cross-field precedence (`domain/projects.py:36-61`). Comparison and the change flag belong
  exclusively to the domain; retained tuple positions cannot stand in for Projects' explicit
  sorting contract (`list_projects`, CP-551).
- **Shared refusal path by construction (b):** Both actions consume the same typed-refusal
  translation and `_name_reason`, rather than two independently tested copies of the reasons.
  Creation's description refusal remains part of that translation (CP-555;
  `Site._create`, `pages._name_reason`, `_description_reason`).
- **Replay and competing focus (b):** Address-carried rename outcomes add no session. Normal
  rename redirects contain only their own outcome; existing page outcomes retain their precedence
  for hand-written combinations, and no second autofocus is added. This protects existing
  `pages.project_page` contracts while the area remains present (CP-546, CP-550, CP-556;
  ADR-0011 § Decision).
- **Sub-job shape:** A/B/C each stay within one production part; D is the existing standalone
  measurement module. Its edge from C is a real request/landing dependency. No sub-job spans
  production modules, and no task ordering beyond those interface edges is prescribed.
- **Additional existing assertion (b):** The first-project browser test also pins one form and
  only Add on the created Tasks view (`tests/e2e/test_first_project.py:54-83`,
  `test_the_first_project_lands_on_its_page_with_spaces_line_break_and_created_line`). T13
  scopes its creation-control assertions and adds Rename presence, retaining every other check.
  This is the further presence assertion spec Locked Answer Gap 10 asks this stage to identify;
  no existing behaviour is released beyond the requested new area.
- **QC-5 review — pass:** Reuse existing domain refusal types and application re-exports. The
  web translation branches by type, never exception text; application defines no new refusal
  (`domain/refusals.py`, `application/__init__.py`; § 3 A–C).
- **QC-8/QC-20/QC-21/QC-23/QC-27 review — pass:** Rules and exact comparison live in the
  domain; application reads only its outcome flag and saves before publishing; form/HTML/address
  logic stays in web, with no request state retained. No framework, script, new collaborator or
  save-contract replacement is added (§ 3 A–C; `docs/SDD.md` § 3). QC-22/QC-25/QC-26 are
  not triggered: persistence and the saver contract are unchanged.
- **QC-12/QC-41/QC-46/QC-60 review — pass:** Use existing parts and Python 3.11-compatible
  frozen values, functions and standard-library facilities; add no runtime/test dependency,
  credential or saved field. The rename outcome is transient (§ 3 A–D; `docs/nfdr.md`, these
  obligations). This is a design compatibility review, not a run of the product under Python 3.11.
- **QC-36 review — pass:** Every new HTML interpolation goes through existing `_escape`, and
  the duplicate-name reason remains `_name_reason`; URL encoding stays in `_address`. T11/T12
  cover the hostile text on each new display and the real browser input (§ 3 C; CP-561/565).
- **QC-40 review — pass within the dated browser exception:** The public GitHub critical-PyPI
  advisory feed was downloaded without sending the lock's contents, following all pagination
  links: 9 pages, 833 entries, compared locally against all 15 names in `tests/requirements.txt`.
  Its only matching package entry is Pygments, GHSA-fff8-4w9p-7v76, affected range
  `>= 1.2.2, < 2.1`; the lock's 2.21.0 is outside it
  (https://api.github.com/advisories?ecosystem=pip&severity=critical&per_page=100;
  https://github.com/advisories/GHSA-fff8-4w9p-7v76). This verdict covers that published feed,
  not unpublished advisories. The installed full-browser Info.plist reports 153.0.8010.12
  (`/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString'` on
  `<a path on Eyal's machine> Chrome for Testing.app/Contents/Info.plist`
  → `153.0.8010.12`), matching `tests/e2e/test_moves.py`, `PINNED_BROWSER`, and the
  `playwright==1.63.0` lock. Chrome's September 15 release lists critical fixes at
  153.0.8010.47/.48, and its October 20 release lists further critical fixes
  (https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html;
  https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_02018666648.html).
  The installed build is covered on this review date by `docs/nfdr.md` RN-33's owner exception,
  through 2026-11-07; it is not declared free of critical advisories. No pin is moved here.

The cold read checked part placement, importer impact, interface sufficiency, dependency order,
all 28 Examples and CP-546–CP-568, explicit comparison/sort/state-delta contracts, the text header,
record changes and the review decisions above. No spec line is set aside and this design requires
no write into a repository outside the instance/product worktree.
