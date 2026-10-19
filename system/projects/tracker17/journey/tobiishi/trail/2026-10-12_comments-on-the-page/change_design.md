# Change Design — Comments on a task's page

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the task page's Comments heading, empty state, author and time presentation, comment field label and maximum sentence, no-name notice and People link, Add button, refusal reasons, failure line, completion line and accessible descriptions; the console's failed-comment action line
**Inputs read:** change_request.md no Status line · change_spec.md no Status line · deferred_decisions.md no document Status line · SDD Settled version 10 · FDR Settled version 4 · NFDR Settled version 12 · ADR-0001 through ADR-0009 Accepted · DESIGN Settled version 3 · CONTENT Settled version 10 · writing_bar Settled

This document owns the structural delta for `tracker17 · tobiishi · 2026-10-12_comments-on-the-page`, including contracts, affected parts and test coverage. The business rules remain `change_spec.md`'s, with the timed-run reading set aside in Architect Review Notes.

Paths beginning `domain/`, `application/`, `persistence/`, `web/`, `tests/` or `docs/` are relative to `products/tracker17/`; the path resolver returned `product_path: products/tracker17` and `product_worktree: .worktrees/2026-10-12_comments-on-the-page` for this key. This artifact's home is the change folder, per `core/doctrine/setup/kensaiapp_structure.md` § 2, “Holds the change arc” (L2089-L2093).

---

## 1. Change Summary

Add comment rules and restoration checks in `domain`, an add action in `application`, and the list, form and submission in `web`, following the owning parts in `docs/SDD.md` § 3, “The parts” (L199-L205). The saved-data adapter already encodes the three Comment fields and restores every task through `restore_task`, so this design adds no saved key or file-format migration (`persistence/saved_data.py` “COMMENT_KEYS”, L46; “_encode_task”, L144-L151; “_decode_task”, L205-L215).

Carry the accepted rules CP-240–CP-272 and CP-274–CP-275 from `change_spec.md` “Rules” (L23-L108). Keep `tests/timed_run.py` and `tests/integration/test_timed_run.py` byte-identical, as the request's “Must not be weakened or added” requires (L11-L15); CP-273 and its Example are set aside, with the unmet timing obligation handed on in `deferred_decisions.md`.

---

## 2. Blast Radius

The following placement is the Architect's decision of 2026-10-12, derived from the parts table in `docs/SDD.md` § 3 (L199-L205) and the module set in `docs/nfdr.md` § 1.2 (L129-L150).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified; new `comments.py` within the existing part | The domain part owns comment text checks, typed refusals, author snapshot, immutable append and saved-comment validation. `comments.py` is the feature entry; `tasks.py` integrates the task lookup, append and restore path; `refusals.py` and `__init__.py` expose the new types. CP-249, CP-254–CP-259, CP-264, CP-266 (`change_spec.md:L35-L67`). |
| `application/` | Modified | The application part owns applying the add to current state, obtaining the injected instant, saving before publishing, and handing domain refusal types to web. Add `Tracker.add_task_comment`; extend package re-exports. CP-249–CP-252, CP-260 (`change_spec.md:L35-L49`). |
| `persistence/` | Modified transitively; production source unchanged | Its existing restore path now receives comment-content refusals from domain. The adapter part retains shape/type/instant decoding and whole-state saving; adapter and start tests prove unreadability and compatibility. CP-263–CP-265 (`change_spec.md:L55-L63`; `persistence/saved_data.py:L95-L108,L205-L231`). |
| `web/` | Modified | The web part owns the add address, normalization, typed-outcome redirect, comment-area presentation, local-time formatting, escaping and focus. Extend `routes.py`, `pages.py` and `style.css`. CP-240–CP-248, CP-250, CP-255–CP-262 (`change_spec.md:L23-L51`). |
| `main.py` | Unchanged | The existing `UnreadableData` handling returns 1 before building the tracker or listener; comment validation reaches that same path (`main.py` “start”, L37-L49). Its contract is exercised by the start tests. |
| `errors.py` | Unchanged | New domain refusals inherit the existing `Refusal` base, which already derives from `AppError` (`domain/refusals.py` “Refusal”, L24-L25; `docs/nfdr.md` QC-4, L50-L55). |

`application` and `persistence` consume domain's changed restore/public surface; `web` consumes application's added action and refusal exports, so all three are included above (`docs/nfdr.md` QC-14–QC-16, L132-L143). No forbidden import is needed: web receives domain values and lengths through application, and persistence continues to use domain's existing facade (`application/__init__.py` “Re-exports”; `persistence/saved_data.py:L22`; `docs/SDD.md` “The direction of dependence”, L230-L232).

---

## 3. Sub-jobs

The four sub-jobs each stay within one production part; their tests sit in the locations listed in § 5. The named contracts below are Architect decisions of 2026-10-12, realizing `docs/SDD.md` seams SM-1–SM-4 (L220-L225).

### Sub-job A — `domain/`

**Scope:** Add `domain/comments.py`, integrate the comment add and restoration in `domain/tasks.py`, define refusals in `domain/refusals.py`, and update `domain/__init__.py` re-exports, for CP-249, CP-254–CP-259, CP-264 and CP-266 (`change_spec.md:L35-L67`). A also owns the existing domain, architecture and saved-comment fixture/assertion corrections CP-274 names, because those tests consume the changed domain contract (`change_spec.md:L98-L102`).

**Exposes:**

- `Comment` remains the frozen value with exactly `text`, `author` and `created_at`. Define it in `comments.py`, and retain the importable `domain.Comment` and `domain.tasks.Comment` names by re-exporting the same class; its current fields are `domain/tasks.py` “Comment” (L66-L72).
- `check_comment_text(text)` returns the unchanged valid text or raises `TextTooLong(TextField.COMMENT, LONG_TEXT_MAX)` or `BlankComment`, in that order. `TextField.COMMENT` is added to the field vocabulary; `LONG_TEXT_MAX` and the shared length checker remain the sole length source (`domain/text.py` “The two text maximums”, L12-L19; CP-254, CP-256–CP-258, `change_spec.md:L40-L47`).
- `create_comment(text, operator_name, created_at)` returns a Comment after checking text, then raises `OperatorNameNotSet` if the name is absent. The supplied name and instant are copied into the value without consulting state or a clock; CP-258 fixes length, blank, then no-name precedence (`change_spec.md:L35-L47`).
- `check_saved_comment(comment)` returns the same valid Comment or a domain refusal. Use the same text rule and the existing `check_operator_name` scalar rule for its historical author; no current operator name is required or compared. `check_saved_comments(comments)` returns their validated tuple in input order. `restore_task` keeps its signature and delegates to this check instead of accepting unchecked content (`domain/operator_name.py` “check_operator_name”, L39-L49; `domain/tasks.py:L315-L351`; CP-264, `change_spec.md:L56-L62`).
- `add_task_comment(state, task_id, text, created_at)` returns `(new_state, updated_task)` or raises `TaskNotFound`/one of the comment refusals. In `tasks.py`, find the task first; then ask `comments.py` to create the Comment from `state.operator_name` and append it to that task's tuple. All other state values stay identical; successful additions always append once, including a repeated text. No status guard is introduced (CP-249, CP-251, CP-253, CP-259, `change_spec.md:L35-L48`).

`comments.py` holds the value and scalar comment rules and does not import the task/state modules at runtime. The task/state operation stays in `tasks.py`, which can depend on those scalar rules without a cycle; this split is an Architect choice of 2026-10-12, not an added part (SDD § 3 “domain”, L201; CP-266, `change_spec.md:L67`).

**Depends on:** none.

### Sub-job B — `application/`

**Scope:** Add `Tracker.add_task_comment(task_id, text)` and export `BlankComment`, `OperatorNameNotSet` and the updated `TextField` vocabulary through `application/__init__.py`, following CP-266 (`change_spec.md:L67`).

**Exposes:** The action reads one instant through the existing injected `Clock.now`, applies A's state rule, passes the whole new state to the existing saver, and returns the updated Task only after the save succeeds. A refusal or a saver failure propagates while the old state remains current; `Tracker.operator_name()` and `Tracker.task_edit_context()` keep their signatures (`application/contracts.py` “Clock” and “Saver”; `application/tracker.py` “_save_then_publish”, L179-L181; CP-249–CP-252, CP-260, `change_spec.md:L35-L49`).

The returned task's comment tuple supplies the successful comment's one-based position, without another saved identifier. No `changed` comparison is needed because every accepted add is a new append; that is the Architect's decision of 2026-10-12 realizing CP-249 (`change_spec.md:L35`).

**Depends on:** A's add rule and refusal exports.

### Sub-job C — `persistence/` restoration contract

**Scope:** Add adapter/start verification through real `SavedData.load` and `main.start` against A's stricter `restore_task`, using the corrected fixtures A supplies under CP-274 (`change_spec.md:L101-L102`). Production `persistence/saved_data.py` remains unchanged, because it already decodes Comment and catches domain Refusal around the entire load (`persistence/saved_data.py:L95-L108,L205-L231`).

**Exposes:** Comment JSON remains exactly `text`, `author`, `created_at`; task/state keys, counters, four supported state forms and UTC instant encoding stay as defined today (`persistence/saved_data.py:L28-L46,L65-L77,L144-L151`). A bad comment makes the entire load raise `UnreadableData(location)`; start returns 1 and leaves the file's bytes unchanged, including when valid data appears before the bad comment (CP-263–CP-265, `change_spec.md:L55-L63`; `main.py:L37-L49`).

**Depends on:** A's saved-comment check for refusal coverage; B's add action for the full AC-6 action-and-restart sequence.

### Sub-job D — `web/`

**Scope:** Add `POST /tasks/[0-9]+/comments` to the route registry and submission dispatch, extend the task-page builder with a comment area, and place its presentation in the existing stylesheet, for CP-240–CP-262 (`change_spec.md:L23-L51`).

**Exposes — submission and redirect:**

- The form sends only `text` to `/tasks/<task_id>/comments`. It carries no author, timestamp, shown name or comment identity. Normalize CR LF and lone CR with the existing `_line_feeds` before invoking B's action; the request check and request lock remain outside the dispatch (`web/routes.py` “_line_feeds”, L163-L165; “handle”, L178-L198; CP-249, CP-251, CP-261, `change_spec.md:L35-L50`).
- Success redirects through the existing `_redirect`/`_address` to `/tasks/<task_id>?comment_added=<position>`, where position is the returned task's comment count. This is a transient focus address, not a saved field, and identifies the same comment after another add (Architect decision, 2026-10-12; CP-250, CP-263, `change_spec.md:L36,L55`; ADR-0006 “Decision”).
- `TextTooLong`, `BlankComment` and `OperatorNameNotSet` map by type to the closed comment refusal codes `too-long`, `blank`, `no-name`. The redirected address carries `comment_refused=<code>` and, for blank/no-name only, `comment_text=<normalized text>`. Too-long carries no submitted value. The failure address carries `comment_failed=add` and retained `comment_text` (CP-255–CP-258, CP-260, `change_spec.md:L44-L49`).
- `TaskNotFound` redirects to the ordinary task address, whose GET returns the existing task-not-found page. An unparseable identity follows the existing direct not-found path; no save occurs for either (CP-259, `change_spec.md:L48`; `web/routes.py:L247-L264,L497-L508`).
- Unexpected failures use the existing `_guarded` site and console reporting, with the approved failed-comment action line; no new catch/console site is introduced (`web/routes.py` “_guarded”, L639-L651; CP-260, `change_spec.md:L49`).

**Exposes — page values and rendering:**

- `CommentRefusal` is web's closed presentation vocabulary, and `CommentArea` carries only `text`, `refusal`, `failed` and `added_position`, with an ordinary empty default. Extend `task_page` with optional `comment_area` and `operator_name` keyword values, preserving its existing arguments/defaults; Site supplies the current `Tracker.operator_name()` at GET time (Architect decision, 2026-10-12; existing signature `web/pages.py:L856-L863`; CP-246, `change_spec.md:L29`).
- The route decodes only recognized comment outcomes. Unknown codes, malformed/out-of-range positions and text without a retaining outcome produce the ordinary comment area. A too-long outcome ignores any forged `comment_text`; outcome selection is settled in Review Notes (Architect decision, 2026-10-12, extending the existing `_closed`/retained-form pattern in `web/routes.py:L155-L160,L275-L286`).
- Render the immutable comment tuple in its held order, with an HTML target derived from each one-based position. Each item shows escaped author, the stored instant converted to machine-local time and formatted `YYYY-MM-DD HH:MM`, and escaped text with preserved whitespace. Do not sort by timestamp or read the clock (CP-241–CP-243, `change_spec.md:L24-L26`; `docs/nfdr.md` QC-44, L373-L377).
- Below the fields and label section, render a Comments sheet with heading, list or empty line, no-name notice when the supplied name is None, then the add form. Use a visible label, a four-line textarea, `maxlength` from application's `LONG_TEXT_MAX`, and an approved maximum sentence interpolating that same value. The form has no native `required` or disabled state that blocks the server's empty/no-name refusal path (CP-240, CP-244–CP-246, CP-255–CP-256, `change_spec.md:L23-L45`; `docs/DESIGN.md` “The comment textarea”, L442-L446).
- Success gives the identified comment `tabindex=-1`, `autofocus` and an `aria-describedby` reference to exactly one completion line. A refusal focuses the textarea and associates its reason; failure focuses the Add button and associates its failure line. Messages never take focus, no fragment or script is added, and each result has exactly one focus target (CP-250, CP-255–CP-260, `change_spec.md:L36-L49`; ADR-0003 “Decision”).
- All typed values pass through the existing `_escape`; use the existing `.pre-wrap` behavior for author and text. Add comment meta/separator and focus styling to `style.css` according to `docs/DESIGN.md` “Comments” (L388-L390) and its focus contract; preserve the existing edit/label presentation (CP-243, CP-274, `change_spec.md:L26,L103`).

**Depends on:** B's action and exports. Its page/stylesheet and routing work share `CommentArea` and refusal codes within the same web part.

**Build sequence:**

1. A establishes the scalar, task-add and restore contracts.
2. B consumes A; C's restore checks can also proceed once A is available.
3. D consumes B; C's AC-6 action/restart coverage consumes B too.
4. D's browser acceptance uses the complete add and restore paths.

The sequence follows SM-1–SM-4's inward dependencies (`docs/SDD.md:L220-L225`). No cross-part atomic-landing edge is required: the old page does not call the additive action and the saved shape is unchanged; the existing assertions reversed by domain/page changes travel with the corresponding sub-job under § 5 (Architect assessment, 2026-10-12; CP-274, `change_spec.md:L97-L105`).

---

## 4. Code Strategy

These hints are Architect decisions of 2026-10-12. They name approaches at the existing seams and leave production code to implementation.

| Sub-job / change | Hint |
|---|---|
| A — domain comment rules and task integration | Keep scalar Comment construction/restoration in the feature entry and task/state composition in `tasks.py`, so restoration and adding share validation without a circular dependency. Append to the immutable tuple; preserve its order across save and load. CP-241, CP-264, CP-266 (`change_spec.md:L24,L56-L67`). |
| B — application action | None. |
| C — persistence restoration contract | None — exercise the existing Refusal-to-UnreadableData seam (`persistence/saved_data.py:L95-L108`). |
| D — comment pages and submission | Use the append position in the outcome address for a stable autofocus target, not matching text or timestamp. Reuse the one escaping and newline-normalization paths; retained textarea rendering must preserve a leading LF as well as interior line breaks. ADR-0003/0006 “Decision”; CP-243, CP-250, CP-256 (`change_spec.md:L26,L36,L45`). |

---

## 5. Test Additions

Rows T01–T22 are the coverage delta, derived from `change_spec.md` “Rules” and “Examples” (L23-L157). A new test module names its SRS requirements or acceptance criteria in its opening docstring, as CP-266 and NFDR QC-11 require (`change_spec.md:L67`; `docs/nfdr.md:L100-L114`).

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T01 / A | `tests/unit/test_comments.py` (new) | Empty, spaces, tab, LF, U+00A0, U+3000 and mixtures refuse as blank; U+200B accepts. Exact text survives. 4,000 code points accepts, including line breaks and a non-BMP character; 4,001 refuses. CP-254, CP-256, CP-267. |
| T02 / A | `tests/unit/test_comments.py` | No name refuses; length before blank before no-name, including 4,001 spaces/no-name and empty/no-name. Snapshot the supplied author and instant without I/O. CP-249, CP-258, CP-267. |
| T03 / A | `tests/unit/test_comments.py` | Task add appends after existing comments even when timestamps move backwards or are equal; identical text is a new append. All statuses accept, including done and cancelled. Missing task takes precedence over every text/name combination; old task and state remain unchanged. CP-241, CP-249, CP-253, CP-259, CP-267. |
| T04 / A | `tests/unit/test_comments.py`; `tests/unit/test_tasks.py` | Restore rejects blank/over-long text and author, accepts the exact two maxima and arbitrary historical names, and preserves tuple order. Replace only CP-274's empty-comment acceptance in `test_restore_task_checks_saved_label_rules`; retain all label assertions. The removed acceptance clause is released by CP-264 and re-proved as refusal here and in T13. |
| T05 / B | `tests/integration/test_comment_tracker.py` (new) | Inject clock and recording/failing saver. Successful add reads one instant, saves once, then publishes; each refusal and failure leaves current state and saved data unchanged. At action time use the current name, including name changed/set since a page read. Rename leaves prior authors intact. CP-249–CP-252, CP-260, CP-271. |
| T06 / D | `tests/integration/test_comment_pages.py` (new) | Real Site+Tracker with injected clock and real SavedData: heading/list/form location; flat append order, equal and backwards times; UTC instant rendered in controlled UTC+2 as `2026-10-12 14:32`. No clock read on GET. CP-240–CP-242, CP-268. |
| T07 / D | `tests/integration/test_comment_pages.py` | Exact escaped author/text, surrounding spaces, initial/interior/trailing line breaks and markup characters. Four-line labelled textarea; maximum sentence equals `maxlength` and the domain length through application. Empty area; no-name notice and People link above form; notice absent with a name. Assert approved published words. CP-243–CP-246, CP-248, CP-268. |
| T08 / D | `tests/integration/test_comment_routes.py` (new) | Add through real Site+Tracker+SavedData, follow 303, and load saved state. New comment is last with the supplied instant/name; other projects, tasks, fields, labels, comments, assignees, name and counters remain identical. Reload/back-address GET never saves again. Both stale-name cases and a later rename. Accept all four statuses. CP-249–CP-253, CP-268. |
| T09 / D | `tests/integration/test_comment_routes.py`; `tests/integration/test_comment_pages.py` | One test per refusal: no name with retained text, empty, whitespace including LF, and over-long with no retained text. Assert typed reason, one focus target/description, no save and unchanged bytes. Include precedence cases, missing field, CR LF/lone CR normalization, and a maximum whose transmitted CR LF length exceeds its normalized length. CP-254–CP-258, CP-268. |
| T10 / D | `tests/integration/test_comment_routes.py` | Missing/unparseable task identity yields the existing not-found contract, with any text/name combination and no save. A failing saver leaves prior comments/current state/file bytes intact; retain text, focus Add, describe failure, and assert console action then underlying error with neither on the page. CP-259–CP-260, CP-268. |
| T11 / D | `tests/integration/test_comment_routes.py`; `tests/integration/test_routes.py` | Refuse cross-site, same-site, none, absent and unknown submission marks before action; retain Host/policy/no-cookie checks. Add the new route to `SAMPLE_ADDRESS`. Extend the existing outbound audit-hook action sequence with a successful comment add and add the recording-saver action check. CP-261, CP-271. |
| T12 / D | `tests/integration/test_comment_pages.py`; `tests/integration/test_comment_routes.py` | On a page with several comments, no comment edit/delete link, button or form exists. Decode only closed outcomes: unknown codes, malformed/nonexistent positions, orphan retained text and forged over-long retained text; mixed query outcomes produce one settled target without changing state. A later add does not move the earlier outcome's target. CP-247, CP-250, CP-257, CP-268 plus Review Notes' conservative query reading. |
| T13 / C | `tests/integration/test_saved_data.py`; `tests/integration/test_start.py` | Separate blank/whitespace/over-long text and author cases through real load/start; assert UnreadableData, non-zero start, location message, no listener, no partial state and unchanged bytes. Retain malformed shape/type/instant coverage. Valid maximum text/author, historical author unequal to current name and comments with no current name load. CP-264, CP-270. |
| T14 / A, then C | `tests/integration/test_saved_data.py` | A corrects only the invalid saved-comment fixtures/assertions CP-274 releases, retaining historical off-list assignee and label assertions. C adds legacy/current shape verification with tasks/labels/assignees/name wherever the format holds them; absent older fields get existing defaults and load writes nothing. The old blank-comment readability assertions are re-proved as unreadability in T04/T13. CP-265, CP-270, CP-274. |
| T15 / C | `tests/integration/test_saved_data.py` or `tests/integration/test_comment_tracker.py` | AC-6 action sequence creates project, all task fields, assignee, label, name and comment; rebuild Tracker from real saved data and prove all values and order survive. Assert exact saved key sets including only text/author/created_at per comment and the existing two counters. CP-263, CP-269. |
| T16 / D | `tests/e2e/test_comments.py` (new) | Through main and Chromium, fill enough earlier comments to exceed the viewport, tab/type/Enter to add, and assert the new comment is in view, the focused element is that comment, and its accessible description is the single completion line. Reload and back/forward add nothing. CP-250, CP-262, CP-272. |
| T17 / D | `tests/e2e/test_comments.py` | Fill textarea to its native maximum using BMP text and line breaks, submit, and prove the normalized value is saved whole. The separate code-point/non-BMP maximum contract is proved at T01/T09, not by assuming native maxlength counts code points. CP-254, CP-272; ADR-0007 “Consequences”. |
| T18 / D | `tests/e2e/test_comments.py` | Enter `<`, `&` and quote characters, with line breaks/spaces, and assert browser text/author rendering and saved text. Exercise no-name/blank refusals by keyboard with field focus/retention and reason association. CP-243, CP-255–CP-256, CP-262, CP-272. |
| T19 / A | `tests/architecture/test_shapes.py`; `tests/architecture/test_trace.py` | Move comments to the landed feature lists exactly as CP-274 specifies. Keep workflow/filtering/sorting/summary excluded, frozen entities, state fields and all import/reach checks. comments.py's docstring names SRS requirements, participating application/web modules and checking tests. CP-266, CP-274. |
| T20 / D | `tests/integration/test_task_pages.py` | Amend only form ordering, the old no-comment assertion and conditional People link assertions named by CP-274. Existing edit/label/facts/no-script/no-table coverage stays; T06/T07/T12 replace the released comment-absence/no-link clauses with the required comment area and conditional link. No People test is weakened. |
| T21 / all | Existing complete suite; product quality gates | CP-275: full `pytest products/tracker17/tests/` including e2e at the tested commit in a fresh clone when outside this worktree; from product root, Ruff format/check and mypy commands named by CP-275. No production acceptance verdict is claimed by this design. |
| T22 / unchanged timing contract | `tests/timed_run.py`; `tests/integration/test_timed_run.py` | Keep both files byte-identical and their existing checks intact; compare their bytes against the pre-change commit. CP-273's new timed add, its Example and Locked Answer Gap 18 are explicitly set aside, not covered or declared proved. |

**Example pass:** Each Example's Rule cell maps to these rows: CP-240→T06/T07; CP-241→T03/T06; CP-242→T06; CP-243→T07/T18; CP-244→T07; CP-245→T07; CP-246→T07; CP-247→T12; CP-248→T07; CP-249→T02/T03/T05/T08; CP-250→T08/T12/T16; CP-251→T05/T08; CP-252→T05/T08; CP-253→T03/T08; CP-254→T01/T09/T17; CP-255→T09/T18; CP-256→T01/T09/T18; CP-257→T09/T12; CP-258→T02/T09; CP-259→T03/T10; CP-260→T05/T10; CP-261→T11; CP-262→T16/T18; CP-263→T15; CP-264→T04/T13; CP-265→T14; CP-266→T09/T19; CP-267→T01–T04; CP-268→T06–T12; CP-269→T15; CP-270→T13/T14; CP-271→T05/T11; CP-272→T16–T18; CP-273→T22's set-aside record; CP-274→T04/T11/T14/T19/T20; CP-275→T21 (`change_spec.md` “Examples”, L116-L157).

**Rule edge pass:** T01/T02/T09 cover the value boundaries and precedence; T03/T08 cover all statuses and state isolation; T05/T08 cover stale pages; T07 covers both empty/name states; T10/T13 cover failure/partial-load paths; T11 covers every refused mark; T12 covers read-only controls and address replay; T14/T15 cover legacy/default/restart cases. These rows cover the edge paths of CP-240–CP-272 and CP-274–CP-275; the timing exclusion is T22's explicit exception (`change_spec.md` “Rules”, L23-L108).

---

## Records this change makes false

None — read `docs/adr/README.md` and ADR-0001–ADR-0009, `docs/nfdr.md` §§ 1–10, `docs/fdr.md` Rules/Product Decisions, and `docs/SDD.md` § 3. This design keeps their five-part model, dependency direction, Comment fields and saved-state shape (Architect review, 2026-10-12; `docs/SDD.md:L199-L255`; `docs/nfdr.md:L129-L150`; ADR-0001 “Decision”).

The timing obligation in NFDR QC-48 and SDD TS-5 is left unmet, rather than made false; its disposition is the reading-set-aside entry in `deferred_decisions.md` (request L11-L15; `docs/nfdr.md:L412-L419`; `change_spec.md:L218`). Existing deletion/unreadable-page/status gaps remain the three prior entries in that same file.

---

## Architect Review Notes

All decisions and verdicts below are the Architect's, dated 2026-10-12.

- **Request/spec timing conflict (a, c):** Take the reading that preserves both timed-run files and delivers the requested comment capability. Set aside CP-273, its timed-run Example, the CP-273 Verified Claims references as obligations of this change, Out of Scope's “CP-273 times only the comment add”, and Locked Answer Gap 18. The alternative extends `tests/timed_run.py` and times the comment add now; it is not taken because it violates the explicit request boundary and the station guardrail (request L11-L15; `tracker17 · shukuba · 2026-10-12_comments-on-the-page`, Guardrail; spec L96,L155,L173-L174,L187,L218). The minimal reading changes no comment rule or existing test contract; `deferred_decisions.md` names the lines set aside and the still-owed NFDR QC-48/SDD TS-5 review.
- **Comment value placement (b):** Move Comment's definition into the feature entry, retain its existing public aliases, and let task composition depend on the scalar entry. This keeps the feature's content checks together and avoids a runtime cycle between the entry and task restoration (`domain/tasks.py:L66-L72,L315-L351`; CP-266, spec L67). Both pieces belong to SDD's domain row; there is no unowned logic or forbidden caller import (SDD § 3, L201; NFDR QC-13–QC-16, L129-L143).
- **Restore consumers and landing continuity (b):** A's domain-restoration delta includes CP-274's existing saved-comment fixture/assertion corrections, even though those test files exercise persistence. Leaving those corrections to C would leave A's landed restore rule against fixtures that its new contract refuses; the CP-274 corrections belong with the change that reverses their assertions (`change_spec.md:L97-L105`). C owns the additional adapter/start coverage, not those corrections. This allocation changes no production-part boundary.
- **Native form refusal path (b):** The comment form remains usable when no name is set, and native required-field validation does not intercept an empty Add before the domain can return its specified refusal. This realizes CP-246 and CP-255–CP-256 through the existing server-rendered action seam (`change_spec.md:L29,L44-L45`).
- **Order and stable focus by construction (b):** Append in domain, preserve tuple/JSON list order, and render that order without sorting. Use the returned task's one-based comment position as a transient focus address, so duplicate text, equal/backwards times and a subsequent add cannot redirect focus to another comment. No new persistent identity is introduced (CP-241, CP-250, CP-263, spec L24,L36,L55; SDD “Comment”, L247-L248; existing encoder L144-L151).
- **Mixed address outcomes (b):** For a handcrafted address carrying several recognized outcomes, choose one using the existing task-page pattern: a recognized comment refusal before comment failure before valid added position; a recognized comment outcome before the existing label/edit/task outcomes. Unknown comment metadata falls through to the existing page handling. Normal comment redirects emit only one outcome. This conservative presentation decision preserves ordinary old task-page outcomes and realizes one focused element, without treating the address as authorization (`web/pages.py` “task_page”, L864-L890; CP-250, CP-255, CP-260, spec L36,L44-L49).
- **Native field and rule counts (b):** Keep the code-point contract in domain and native maxlength in the form. The non-BMP maximum Example belongs to unit/in-process request coverage; the maximum-with-line-breaks browser Example uses characters whose native count reaches that maximum. This honors both Examples without changing the browser or the accepted counting contract (spec L132,L154; ADR-0007 “Context”, “Decision” and “Consequences”).
- **Delegated QC-5/QC-20/QC-21/QC-23 review — pass:** BlankComment and OperatorNameNotSet are domain refusals; TextTooLong uses domain's existing type. Application only calls domain/saver/clock and re-exports types; web branches on types/codes, normalizes transport and presents values, and domain carries no published wording. No value rule or state comparison is placed in application or web (`docs/nfdr.md:L56-L67,L160-L189,L197-L201`; § 3 A/B/D above).
- **Delegated QC-8/QC-27/QC-36 review — pass:** Comment outcome state is in the address only; pages use `_escape` for every typed value; script/cookie/session stores and new concrete dependencies are absent from the design. The unchanged request lock/policy encloses the new submission (`docs/nfdr.md:L79-L84,L218-L223,L285-L291`; `web/routes.py:L178-L198`; § 3 D).
- **Delegated QC-22/QC-25/QC-26/QC-46 review — pass:** Restore checks are domain-owned, persistence maps their refusal without repairing/dropping values, and its format and saving contract do not change. The stored Comment remains the existing three-field value, with no extra key or record of requests (`docs/nfdr.md:L190-L196,L209-L217,L392-L398`; `persistence/saved_data.py:L46,L95-L108,L144-L151`). QC-26's saving-contract replacement gate is not triggered.
- **Delegated QC-12/QC-24/QC-41/QC-60 review — pass:** The design adds the required feature entry inside an existing part, retains main's existing start/wiring behavior, and introduces no credential. Its proposed constructs use the existing frozen-value, tuple, enum, replace and aware-datetime seams; no Python feature newer than the stated 3.11 floor is selected (`docs/nfdr.md:L115-L120,L202-L205,L335-L339,L479-L483`; `domain/tasks.py:L27-L30,L66-L88`; `application/contracts.py` “Clock”). This is a compatibility design review, not a suite verdict under 3.11.
- **Delegated QC-40 review — pass with the owner's browser exception:** On 2026-10-12, read-only queries of the 15 exact pins in `tests/requirements.txt` returned `vulnerabilities: []` from each PyPI version endpoint. The queries cover [ast_serialize](https://pypi.org/pypi/ast_serialize/0.12.1/json), [greenlet](https://pypi.org/pypi/greenlet/3.5.6/json), [iniconfig](https://pypi.org/pypi/iniconfig/2.3.1/json), [librt](https://pypi.org/pypi/librt/0.16.0/json), [mypy](https://pypi.org/pypi/mypy/2.4.0/json), [mypy_extensions](https://pypi.org/pypi/mypy_extensions/1.1.0/json), [packaging](https://pypi.org/pypi/packaging/26.3/json), [pathspec](https://pypi.org/pypi/pathspec/1.1.1/json), [playwright](https://pypi.org/pypi/playwright/1.63.0/json), [pluggy](https://pypi.org/pypi/pluggy/1.6.0/json), [pyee](https://pypi.org/pypi/pyee/13.0.1/json), [Pygments](https://pypi.org/pypi/Pygments/2.21.0/json), [pytest](https://pypi.org/pypi/pytest/9.1.1/json), [ruff](https://pypi.org/pypi/ruff/0.16.10/json) and [typing_extensions](https://pypi.org/pypi/typing_extensions/4.16.0/json); that is the registry's reported advisory set, not a claim that a package has no vulnerability. The installed chromium-1243 app's `Contents/Info.plist` reports `CFBundleShortVersionString: 153.0.8010.12` (read with Python plistlib at `~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist`). Google's [2026-10-01 security release](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop.html) fixes Critical CVE-2026-103628 in 154.0.8037.97/.98; the older installed build is covered by the owner's build-specific exception through 2026-11-07 (`docs/nfdr.md` RN-33, L986-L998). No dependency/browser pin changes are proposed.
- **Cold-read verdict:** All accepted Examples have § 5 rows, rule edges have the explicit second pass, new logic has SDD owners, public contracts/build edges agree, focus/order are realized by construction, the timing divergence is recorded, and the text verdict is settled. `change_design: clean.`
