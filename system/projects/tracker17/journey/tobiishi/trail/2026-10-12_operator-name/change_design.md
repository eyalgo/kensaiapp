# Change Design — Your name on People

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the Your name section on People, its field label and Save button, the sentence about earlier comments, the no-name line, the blank and too-long reasons, the save failure and completion lines, and the console line naming a failed name save
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md` `Languages:`; `core/doctrine/engineering/languages/python/README.md` and its six routed concerns read.

This document owns the structure, interface contracts and test delta for `tracker17 · tobiishi · 2026-10-12_operator-name`. `change_spec.md` and `change_request.md` below mean the files inside that change unit; code and foundation paths are relative to the instance worktree.

## 1. Change Summary

Add the one operator name to the immutable tracker state, validate it in `domain`, save a changed name through `application`, encode and restore it in `persistence`, and show its form and outcomes on People in `web`, following `change_spec.md:L23-L66`, Rules CP-211–CP-230. The design adds no comment action, comment rule or task-page surface, per `change_spec.md:L62-L66`, CP-229–CP-230.

The architectural decisions in §§2–4 and the choices identified in Architect Review Notes are the architect's call, 2026-10-12. The spec remains the owner of observable rules; §5 names the checks that prove them.

## 2. Blast Radius

The owning parts are the rows of `products/tracker17/docs/SDD.md:L198-L216`, §3 “The parts, and the seams between them”; imports are bounded by `products/tracker17/docs/nfdr.md:L122-L153`, §1.2 “Forbidden imports”.

| Module | Status | What changes |
|---|---|---|
| `products/tracker17/domain/` | Modified | **domain** owns the scalar, its validation, restore checks and change outcome. Add `operator_name` to `state.py`; add `operator_name.py` for the rule and set operation; expose their public names from `__init__.py`. Reuse `BlankName`, `TextTooLong`, `TextField.NAME` and `SHORT_TEXT_MAX`; `refusals.py` and `text.py` need no new condition or maximum. |
| `products/tracker17/application/` | Modified | **application** owns reading the current name and applying the domain set outcome. Add `Tracker.operator_name()` and `Tracker.set_operator_name(name)` in `tracker.py`, and export the outcome through `__init__.py`. Keep `Saver.save(state)` and `Clock.now()` unchanged. |
| `products/tracker17/persistence/` | Modified | **persistence** owns the six-key JSON form, the three older exact shapes, string/null decoding and whole-state encoding in `saved_data.py`. Delegate blank/length rules to the domain restore constructor. Keep atomic writing and the lock unchanged. |
| `products/tracker17/web/` | Modified | **web** owns the name POST route, form decoding and normalized line breaks, namespaced outcome addresses in `routes.py`, and the new section and focus/description mapping in `pages.py`. Reuse the request lock/check, redirect builder, escaping function, failure catch and existing stylesheet. `listener.py`, `style.css` and the package exports need no change. |
| `products/tracker17/main.py` | Unchanged | The existing start reads `SavedData.load()` and handles `UnreadableData` before constructing the tracker/listener (`products/tracker17/main.py:L39-L49`, `start`). No new wiring or unreadable-data mode. |
| `products/tracker17/errors.py` | Unchanged | Reuse the existing refusal hierarchy (`products/tracker17/domain/refusals.py:L8-L29`, `Refusal` and `BlankName`). |
| `products/tracker17/tests/` | Modified | Add the tests in §5, make only CP-238's scoped assertion changes, extend the route/audit-hook coverage, and add the name measurement to `timed_run.py` and its harness checks. |

**Transitive check:** the domain state and exports reach application and persistence; the application additions reach web, and all three are listed. The signatures used by `main.py` stay unchanged. No import edge is added between parts; in particular, web receives domain values and refusals through application, per `products/tracker17/docs/nfdr.md:L129-L150`, QC-13–QC-18.

## 3. Sub-jobs

### A — `domain/`: the operator name and its rule

**Scope:** add `domain/operator_name.py`, extend `domain/state.py`, and update domain public re-exports. The name rule uses the same whitespace predicate as assignees and the shared length check, whose current seams are `products/tracker17/domain/assignees.py:L31-L51`, `check_assignee_names`, and `products/tracker17/domain/text.py:L12-L19`, `ensure_within`.

**Exposes:**

- `TrackerState.operator_name: str | None`, appended with default `None` so existing positional arguments retain their meanings; `empty_state()` has no name.
- `restore_state(..., *, tasks=(), next_task_id=1, operator_name: str | None = None) -> TrackerState`: keep existing arguments and add the optional keyword. For a present string, apply the same name check as the set action before returning any restored state; `None` means no name.
- `check_operator_name(name: str) -> str`: return the unchanged valid string, or raise `TextTooLong(TextField.NAME, SHORT_TEXT_MAX)` before checking blankness and raising `BlankName`. No trimming, case folding, clock, I/O or user-facing wording.
- Frozen `OperatorNameOutcome` with `name: str` and `changed: bool`.
- `set_operator_name(state: TrackerState, name: str) -> tuple[TrackerState, OperatorNameOutcome]`: validate first; compare the submitted string exactly with the current operator name. Equality returns the original state and `changed=False`; a different value returns a state differing only in `operator_name` and `changed=True`. There is no unset operation.
- Export `check_operator_name`, `set_operator_name` and `OperatorNameOutcome` alongside the existing domain surface.

**Depends on:** none.

### B — `persistence/`: the saved representation

**Scope:** extend only `saved_data.py`'s encoding and unpacking/restore path.

**Exposes:** `SavedData.save(state)` writes the existing five keys plus `operator_name` on every save: a string when set, JSON `null` when unset. `SavedData.load()` accepts exactly the three old key sets plus the new six-key full set. In an old shape, absence means `None`; in the new shape the value is either a string or `null`. Reject every other type, including booleans, numbers, lists and objects, as unreadable. Keep all existing required-key and unknown-key checks. Pass the decoded name to `restore_state`; a domain refusal becomes `UnreadableData` through the same path as other restored rules. Reading any shape writes nothing. No name-format knowledge crosses into application or web.

The three existing exact key sets are `products/tracker17/persistence/saved_data.py:L26-L29`, `SUPPORTED_STATE_KEYS`; the shape check and defaulting are `products/tracker17/persistence/saved_data.py:L144-L173`, `_unpack`. Every existing project/task/comment encoding is retained, per CP-226–CP-229 (`change_spec.md:L50-L62`).

**Depends on:** A's state field and restore keyword.

### C — `application/`: apply and publish the name

**Scope:** extend `tracker.py` and application public re-exports. No saving or clock protocol change.

**Exposes:** `Tracker.operator_name() -> str | None` reads the current scalar. `Tracker.set_operator_name(name: str) -> OperatorNameOutcome` calls the domain operation once against the current state. On `changed=True`, save the complete new state before publishing it; return the outcome only after success. On `changed=False`, return it without saving or publishing. Refusals and saver failures propagate, leaving the current state unchanged. Re-export `OperatorNameOutcome` for web; the existing `BlankName`, `TextTooLong`, `TextField` and `SHORT_TEXT_MAX` remain its refusal/bound seam (`products/tracker17/application/__init__.py:L8-L42`, public imports).

**Depends on:** A's operation and outcome. B is not an import or implementation dependency: the supplied saver still satisfies the same protocol (`products/tracker17/application/contracts.py:L15-L19`, `Saver`).

### D — `web/`: the People form and request path

**Scope:** `pages.py` adds the section and its plain outcome value; `routes.py` consumes that contract and the application action. These remain one web sub-job.

**Exposes:**

- `POST /operator-name`, classified as a submission in `ROUTES`, with URL-encoded field `name`. Missing `name` becomes the empty string and is refused by domain. Decode through `_form`, normalize through `_line_feeds`, call C through the existing guarded action site, and answer with a 303 redirect built by `_address`. GET never changes state.
- Add keyword-only `operator_name: str | None = None` and `operator_area: OperatorNameArea | None = None` to `people_page`, retaining every existing parameter and its meaning (`products/tracker17/web/pages.py:L1018-L1026`, `people_page`).
- `OperatorNameRefusal` is a closed address vocabulary: `BLANK_NAME="blank-name"`, `TOO_LONG="too-long"`. Map existing domain refusal types to it in routes, never exception messages.
- Frozen `OperatorNameArea` carries `typed: str | None = None`, `refusal: OperatorNameRefusal | None = None`, `failed: bool = False`, and `saved: str | None = None`. It is a value for this request, not a retained web store.
- Outcome query keys are `operator_refused`, `operator_failed`, `operator_typed` and `operator_saved`. Use `operator_failed=save` for failure. A changed success carries `operator_saved=<saved name>`; an unchanged success redirects to plain `/people`. Blank refusal and failure carry the normalized typed value, including empty; too-long refusal carries only `operator_refused=too-long`. Presence must distinguish an empty typed value from absence.
- Read outcome codes through the existing closed-vocabulary seam. Ignore unknown codes and consume typed text only for a recognized blank refusal or save failure. A too-long outcome ignores even a forged `operator_typed` value. Existing unprefixed assignee query keys retain their meanings (`products/tracker17/web/routes.py:L367-L378`, `_people_page`).
- Place the new section before Assignees, by explicit page composition. Stable identifiers: section `your-name`, heading `your-name-heading`, field `operator-name`, button `save-operator-name`, and outcome description `operator-name-outcome`. The form posts to `/operator-name`; its visible label points to the field, and `maxlength` comes from the application's `SHORT_TEXT_MAX` export. No limit sentence.
- In a plain page the field shows the current saved name, or empty when absent. A blank refusal or failed save shows the carried typed value instead; a too-long refusal shows the current saved name. Keep the no-name line whenever the current name is absent. The keep-their-name sentence remains beside the field.
- Success and both domain refusals focus the field, with the one outcome line as its accessible description. Failure focuses Save, described by the failure line. Use `autofocus`, no fragment or script; the line itself takes no focus. Escape every variable through `_escape`.
- A recognized operator outcome takes precedence over assignee outcome metadata in a combined/forged address; otherwise the existing assignee outcome path applies. Within the operator area precedence is refusal, failure, completion. A page has at most one focused element and one action outcome, while the static note and no-name line are not action outcomes.
- Published wording is supplied by the content record. The contract fixes message meaning and placement, not new prose, per CP-213 (`change_spec.md:L25-L26`).

**Depends on:** C's reader, set action, outcome and public refusal/bound seam. Within web, routes consume the page outcome contract. B is required for real save/restart acceptance, not for web imports.

### E — `tests/`: the full-volume name measurement

**Scope:** extend `tests/timed_run.py` and `tests/integration/test_timed_run.py`; the other tests belong to the subjects named in §5.

**Exposes:** a name-save measurement using the existing real-file, 1,000-task × 20-comment fixture, an ordinary-length name, and the same-origin marks. Separately report the POST and its landing GET; both must be below 1 second. Success requires a changed save, a successful People landing showing the saved name, and read-back of the persisted name with the rest of the fixture intact. A fast refusal, failed save, unchanged action or wrong landing is a failed measurement. These are CP-237's boundaries (`change_spec.md:L92-L92`, CP-237); the existing fixture and verdict seams are `products/tracker17/tests/timed_run.py:L51-L60`, constants, and `products/tracker17/tests/timed_run.py:L131-L150`, `verdict`.

**Depends on:** B's persisted scalar and D's POST/GET contract; C is consumed through D.

**Build sequence:** A first; B and C can then proceed independently; D follows C; E follows B and D. Prefer B complete before D's real-file acceptance because that proves durable read-back; that preference adds no import dependency. No atomic-landing edge exists between these sub-jobs: defaults retain existing callers, and each new interface can land with its own subject's tests before its consumers.

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — domain scalar/rule/outcome | The state restore constructor and operator-name rule have a potential runtime cycle. Keep rule access usable by restoration without importing the state constructor back during module initialization; the operation's state typing must not create that cycle. |
| B — persisted scalar | Keep exact accepted key sets: retain the old five-key set separately before widening the writer's full set. Missing old data and new `null` are two format representations of the same domain `None`. |
| C — save and publish | None |
| D — People and its POST | Namespace the new outcome address values so assignee outcomes cannot consume them; retain empty-versus-absent typed text, and omit/drop over-long text at both redirect construction and page reconstruction. |
| E — timed name save | Reuse the existing volume fixture and verdict, proving the stored result and landing content rather than treating any 303 as success. |

## 5. Test Additions

Paths in this table are relative to `products/tracker17/`. Row IDs are coverage references, not new requirement IDs. Every added test module names the SRS requirements or acceptance criteria it checks, per CP-230 (`change_spec.md:L66-L66`).

| Row / sub-job | Test file(s) | Add / modify |
|---|---|---|
| T1 / A | `tests/unit/test_operator_name.py` | Pure checks and set outcomes for empty, spaces, tab, U+00A0, U+3000; U+200B accepted; 200 code points including a non-BMP character accepted; 201 refused; 201 spaces get `TextTooLong` before `BlankName`. Preserve surrounding spaces and case. First set, replace, exact same no-change, `Sam` → `Sam ` change, no clearing. Assert the input state and all unrelated collections/counters remain unchanged. CP-217–CP-221, CP-229–CP-231. |
| T2 / A | `tests/unit/test_state.py` | Empty state has `None`; restore omitted name and `None`; restore exact valid/boundary/space-surrounded name; each blank or over-long string refuses the whole state through the shared rule. Non-text JSON cases belong to T4/T5. Existing restore arguments still work. CP-228, CP-231. |
| T3 / C | `tests/integration/test_operator_name_tracker.py` | Inject recording/failing savers and clock. Reader reflects the state; changed save passes the whole state once before publication; replacing changes only the name; same name makes no save, even with a saver that would fail. Each domain refusal makes no save. Saver failure keeps the old name/state. Assert clock unused and saver received only saves. CP-216–CP-222, CP-229, CP-235. |
| T4 / B | `tests/integration/test_saved_data.py` | New full form is exactly the previous five keys plus `operator_name`; save `None` as null and valid names verbatim. Round-trip a rich state with projects/tasks/labels/comments/assignees/counters intact. Load each of the three older exact forms with `None` and unchanged bytes, then save into the six-key form on an actual change. New null, 200-code-point and surrounded-space names load. Unknown keys and missing old required keys remain rejected; invalid operator type/blank/too-long refuses with unchanged bytes. CP-226–CP-228, CP-233–CP-234. |
| T5 / B, unchanged main | `tests/integration/test_start.py` | Separate real-start cases for saved empty, whitespace-only, 201-code-point and numeric names: stderr names unreadable data/location, nonzero start, no ready/listener success, no partial load and byte-identical saved file. Check other non-text types at T4. Valid null/boundary/surrounded-space names and each older form load, retaining every value those forms can hold; loading never saves. CP-227–CP-228, CP-233. |
| T6 / D | `tests/integration/test_people_pages.py` | Your name is above Assignees; title/header/navigation unchanged. Label/field/Save/note and absent-name line have their defined placement; saved name fills the field and removes the no-name line. Bound equals the application's shared maximum; no limit sentence. Parse field/line markup to prove escaping and exact text. Test success/refusal focus on field, failure focus on Save, linked accessible description, one autofocus and no fragment/script. CP-211, CP-212, CP-213, CP-214, CP-216, CP-217, CP-220–CP-222, CP-225, CP-232. |
| T7 / D | `tests/integration/test_people_routes.py` | Exercise Site POST then redirect GET for set and replacement, exact whitespace/case retention, and same-name no save/no outcome. Separate empty and whitespace refusals from both no-name and saved-name starts; reason/focus/typed value present and state/file unchanged. Separate over-long test verifies field fallback, no sent text anywhere in Location/page, and length-before-blank. Missing field follows empty refusal. Test CRLF/lone CR normalization, U+200B acceptance, and 200-code-point non-BMP boundary. Failure keeps typed value, focuses Save, names action/error on stderr and exposes no Python detail. Test empty versus missing query value, unknown codes, forged too-long typed value, and combined metadata precedence. Reload/back/forward landing GETs make no saves. CP-216–CP-223, CP-225, CP-232. |
| T8 / B, D | `tests/integration/test_people_routes.py` | Through the real listener/server, GET People, POST save, POST replacement and both blank refusals from saved and unset starts. Also save/restart with real `SavedData` and a fresh tracker/Site: name and every unrelated value survive. This adds real-server coverage alongside the in-process tests, retaining the existing `test_people_survives_real_save_and_restart` assignee check (`products/tracker17/tests/integration/test_people_routes.py:L407-L435`, that test). CP-226 and the request's real-server acceptance. |
| T9 / D | `tests/integration/test_routes.py` | Include POST `/operator-name` in route enumeration and assert 303/no cookie/page policy/unchanged GETs. Drive a changed name save under the outbound-connection audit hook and recording saver. Name-submit refusal for wrong Host and `cross-site`, `same-site`, `none`, missing and other non-`same-origin` marks leaves state/file unchanged; accepted `same-origin` saves. CP-223, CP-235. |
| T10 / A, B, D | `tests/architecture/test_shapes.py`, `tests/integration/test_people_pages.py`, `tests/integration/test_people_routes.py`, `tests/integration/test_saved_data.py` | Retire only CP-238's page-wide single-section/field/label/button/no-paragraph assertions by re-proving them inside Assignees. Keep assignee focus, list, form, content and no-script assertions. Drop only `your name` and `comment` from the two absence lists; retain every other prohibited term. State fields gain only `operator_name`; the `comments.py` prohibition and all other feature fences stay. `FULL_KEYS` gains only `operator_name`, re-proving exact keys at all seven sites, with value-preservation assertions retained. CP-215, CP-229, CP-238. |
| T11 / D | `tests/e2e/test_people.py` | Use only browser keyboard to set a name and replace it; reload/back/forward retain it without another save; refuse blank with typed text kept and accessible reason/focus. A separate hostile-name save containing `<`, `&` and quotes shows exact field/completion text, normal surrounding structure, computed accessible description and focus. CP-224–CP-225, CP-236. |
| T12 / E | `tests/integration/test_timed_run.py`, `tests/timed_run.py` | Assert the name POST/landing measurement uses real durable read-back at the stated volume, same-origin marks and ordinary name length. Harness cases reject refusal/failure/wrong landing/no actual save and each at-or-over-limit part. Retain existing measurements and their checks. Execute the timed run with both name rows below 1 second and exit 0. CP-237. |
| T13 / all | Existing architecture/trace suite and complete verification | Existing import, frozen-value, dependency, reach and trace checks include the new module without weakening them; do not list `comments` as landed or add `domain/comments.py`. Run CP-239's suite/e2e and Ruff/mypy commands, plus the Python compile gate. Checks outside the worktree use a disposable clone checked out at the explicit tested SHA, per `core/roles/CROSS_ROLE.md:L12-L24`, “Every seat”, instead of the spec's archive/init method. |

**Examples pass:** in `change_spec.md` §Examples, rows at L110–L113 map to T6; L114–L119 to T1/T3/T7; L120–L125 to T1/T7; L126 to T3/T7; L127 to T9; L128 to T11; L129 to T6/T11; L130 to T8; L131–L134 to T2/T4/T5; L135 to T1/T10/T13; L136 to T3/T7; L137 to T1–T9; L138 to T11; L139 to T12; L140 to T10; L141 to T13 with the recorded clone reading.

**Rules pass:** CP-211–CP-214 are covered by T6, CP-215 by T10, CP-216 by T3/T7/T8/T11, CP-217 by T1/T7, CP-218–CP-219 by T1/T3/T7, CP-220–CP-221 by T1/T7 (each refusal from saved and unset states), CP-222 by T3/T7, CP-223 by T9, CP-224–CP-225 by T11, CP-226 by T4/T8, CP-227–CP-228 by T2/T4/T5, CP-229 by T1/T10/T13, CP-230 by T3/T7/T13, CP-231–CP-234 by T1–T8, CP-235 by T3/T9, CP-236 by T11, CP-237 by T12, CP-238 by T10, and CP-239 by T13. Empty names after failures, absent saved name, null and old shapes, wrong-type starts, all origin marks and a no-change save are explicitly included above; no rule-implied failure path is left to the Examples table alone.

**Assertions retired and re-proved:** T10 owns every retirement CP-238 authorizes. No behavioral assignee assertion or saved-field assertion is discarded; the former is scoped to its section and the latter admits exactly the new scalar. Renaming a test whose title says “five keys” to reflect six keys changes its name, not its coverage. No other existing test is deleted, skipped or weakened.

## Records this change makes false

- `products/tracker17/docs/SDD.md:L202-L202`, §3 application row, and `products/tracker17/docs/nfdr.md:L167-L180`, QC-21: their unqualified statement that a reported change compares submitted against page-shown values does not describe this scalar operation. CP-218 requires comparison with the name saved at the moment of the action (`change_spec.md:L33-L33`). Clarify that submitted-versus-shown is the task-edit rule; other actions report change according to their own domain rule, and application never compares states. Preserve the task-edit contract and its stale-field behavior.

The other reviewed records — `products/tracker17/docs/fdr.md` Rules R-62, R-76–R-80, R-100–R-112 and PD-11, `products/tracker17/docs/adr/README.md` and Accepted ADR-0001–ADR-0009, and the remaining SDD §3/NFDR entries — require no correction caused by this change. ADR-0001's historical unconditional-save wording is already qualified by the current QC-21 obligation, as `products/tracker17/docs/nfdr.md:L1040-L1059`, RN-37, directs; do not edit or supersede that Accepted record for this delta.

## Architect Review Notes

Each design choice below is the architect's call, 2026-10-12. Gate verdicts review this blueprint, not implemented code or a passed suite.

- **(b) State and saved representation:** choose the appended optional scalar and an always-written six-key full JSON form, with null meaning unset. This locks the representation CP-228 and CP-238 leave open (`change_spec.md:L52-L58`, L97 and Locked Answers Gap 17). It retains old constructors and the three existing load shapes while giving every new write one exact shape. No account, identity, counter or other personal field is added.
- **(b) Scalar change comparison:** use a domain name comparison at action time for CP-218 (`change_spec.md:L33-L34`), with no hidden shown-name field. The SDD/NFDR clause to clarify is listed above; the existing task edit still compares submitted versus shown. Application owns only the outcome/save/publish flow. No business rule is inferred from state equality there.
- **(b) Shared refusal seam and feature home:** reuse `BlankName` and `TextTooLong` because the conditions are the same as the existing shared name rule, not a new kind of refusal (`products/tracker17/domain/refusals.py:L28-L29`, `BlankName`, and `products/tracker17/domain/refusals.py:L88-L94`, `TextTooLong`). Put the scalar rule in `domain/operator_name.py`, within the owning domain part; it is not the Comments feature entry and does not claim that feature has landed, per CP-229–CP-230 (`change_spec.md:L62-L66`).
- **(b) Focus and address realization:** choose field focus on changed success under CP-216's explicit choice (`change_spec.md:L31-L31`). Section order is explicit composition; one selected outcome determines autofocus and description, and empty retained text is represented by presence. Namespaced metadata and refusal/failure/completion precedence keep the two People actions separate and keep at most one focus. These choices realize CP-211/CP-215/CP-216/CP-220–CP-222 rather than relying on incidental markup or empty-string truthiness.
- **(c) Verification copy:** replace CP-239's archive/init method with a clone at the tested SHA because `core/roles/CROSS_ROLE.md:L12-L24`, “Every seat”, requires retained history. The named commands and zero-exit gates remain. The discarded archive-method reading is entered in `deferred_decisions.md`; it is not a permission to run a suite here.
- **QC-5 — pass:** routes map the two existing refusal types to name-area codes through application; no message-based branch or application-defined refusal. T3/T7 prove the seam. This is the review delegated by `products/tracker17/docs/nfdr.md:L56-L67`, QC-5.
- **QC-8 — pass:** every outcome is reconstructed from the address plus the current application scalar; no cookie, last-outcome store or module-level mutable state, under `products/tracker17/docs/nfdr.md:L79-L84`, QC-8.
- **QC-12 — pass:** one domain module keeps the new rule/restore seam together; all other changes extend existing parts. No sixth part, browser script, framework or new dependency is added. This meets the structural review at `products/tracker17/docs/nfdr.md:L115-L120`, QC-12; the owner's simplicity judgement remains theirs.
- **QC-20–QC-24 — pass within the requested delta:** domain holds no words or I/O; application calls its outcome and supplied saver; persistence checks shape/types and delegates the rule; web decodes and renders without validating blankness/length; main's existing unreadable-start handling is unchanged. These are the reviews delegated in `products/tracker17/docs/nfdr.md:L160-L198`, §1.3. The separate unreadable-page obligation remains the existing deferred entry.
- **QC-25/QC-26 — pass / not triggered:** JSON key sets and null are confined to B; Saver still saves the whole state. No per-change saving interface replaces it, per `products/tracker17/docs/nfdr.md:L202-L210`, §1.4.
- **QC-27 — pass:** pages, addresses and request detail remain in web; application exposes plain values only. No browser-interface replacement changes an inner part, per `products/tracker17/docs/nfdr.md:L211-L216`, QC-27.
- **QC-36 — pass:** field value, completion name, retained text and any interpolated refusal/failure value use the existing `_escape` seam; T6/T11 prove hostile text remains text. This is the one-function review at `products/tracker17/docs/nfdr.md:L278-L284`, QC-36.
- **QC-40 — pass on 2026-10-12, with the owner's existing browser exception:** the read-only command `python3 /private/tmp/tracker17_operator_name_advisories.py` queried GitHub's public advisory API for each exact pin in `products/tracker17/tests/requirements.txt:L4-L18`; its output contained `critical_advisories: []` for all 15 pins and `PyPI playwright latest: 1.63.0`. The query form is `https://api.github.com/advisories?ecosystem=pip&severity=critical&affects=<package>@<version>&per_page=100`; the package registry source is `https://pypi.org/pypi/playwright/json`. This is absence in that database response, not a claim that no vulnerability can exist. The local manifest `/private/tmp/t17-selfanswer-7/venv/lib/python3.14/site-packages/playwright/driver/package/browsers.json`, `chromium` entry, was read and returned revision `1243` and browserVersion `153.0.8010.12`, matching the build named in `products/tracker17/docs/nfdr.md:L976-L989`, RN-33. Google's 2026-09-15 release fixes three Critical issues at `153.0.8010.47/.48` (`https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html`); Google's 2026-10-06 release also lists four Critical fixes (`https://chromereleases.googleblog.com/2026/10/?amp=1`, “Stable Channel Update for Desktop”, October 6). On this comparison the installed build is older than those fixed builds. RN-33's owner-recorded exception covers that exact build through 2026-11-07; no new exception or pin change is made. The review requirement is `products/tracker17/docs/nfdr.md:L303-L327`, QC-40.
- **QC-41/QC-46 — pass:** a name is one string or none, not a secret or credential. The new saved field is only SRS DR-5's operator name; T4 re-proves exact keys and unchanged other values. No request/outcome data is persisted, under `products/tracker17/docs/nfdr.md:L328-L332`, QC-41, and `products/tracker17/docs/nfdr.md:L385-L391`, QC-46.
- **QC-60 — pass as a design review:** the blueprint uses the product's existing dataclasses, optional strings, enum and JSON seams, all within its Python 3.11 floor (`products/tracker17/pyproject.toml:L1-L4`, `requires-python`). No new language/library feature or dependency raises that floor. This does not claim a 3.11 suite run; `products/tracker17/docs/nfdr.md:L471-L475`, QC-60, names that separate missing harness.

**Cold-read:** owning parts and transitive callers are covered in §2; §3 supplies each consumed interface and its dependencies; §5 covers every Example and rule-implied edge and re-proves retired assertions; the scalar/focus/format choices and delegated gate verdicts are recorded here; the affected foundation clauses are listed above; the text verdict is settled in the header. No implementation or acceptance suite was run by this design stage.
