# NFDR — tracker17

**Status:** Settled
**Owner:** Principal Architect
**Version:** 15 — the owner's answer to companion § 2.2 folded in (`products/tracker17/docs/trail/architecture/cycle-13.md`): RN-15 counts the SDD § 4 EX-6 confirmation verified, as SDD version 11's § 11 R-2 does, states the browser build as R-2 states it, and counts the one SDD Open Question left (RN-46); no obligation, trace tag or § 10 row moves, nothing is left open, so the companion is removed and this document is Settled
**Inputs read:** SRS Settled (version 6) · SDD Settled (version 11) · FDR Settled (version 4) · PRD Settled (version 7) · UXD Settled (version 8) · DESIGN Settled (version 4) · CONTENT Settled (version 12) · Agari no Status line · tracker17 doctrine no Status line (stamped, unfilled)

> The NFDR is the product's **standing obligations, consolidated and verifiable**: every quality
> constraint a change is checked against, derived from the SRS, the SDD, the FDR and the ADR — never
> invented here. It is updated in place with versioning (unlike the ADRs, which supersede).
> **Every entry carries a stable typed ID** (`QC-n`, never reused or renumbered), **a
> `verified by:` tail** naming the command, test layer, or review gate that fails when the
> obligation is broken, and **an inline trace tag** naming the upstream fact it realizes
> (`SRS NFR-n`/`C-n`, `SDD § 4`, an ADR record, or a doctrine default). An entry with no
> nameable verification is not yet an entry. A conditional section that does not bind this product
> is declared not applicable with the reason — never silently omitted. **`Inputs read:` names every
> upstream document this revision read and the status it carried at the time** — an obligation
> derived from a Draft source is still binding, and the line is how a later reader knows which ones
> were.

`SRS`, `SDD`, `FDR` and `UXD` below are `products/tracker17/docs/SRS.md`, `SDD.md`, `fdr.md` and
`UXD.md`. `ADR-n` is the record of that number in `products/tracker17/docs/adr/`. Paths to code are
relative to the product root, `products/tracker17/`; a path beginning `trail/` is relative to
`products/tracker17/docs/`. Test layers are
`<CORE>/doctrine/engineering/testing_doctrine.md`'s, realized in § 9; "layer 6" is a plain pytest
module under `tests/architecture/`, which `pytest tests/` runs.

---

## 1. Structural integrity

### 1.1 Architectural invariants

- **QC-1:** The product's code is five parts at the product root — the directories `domain/`,
  `application/`, `persistence/` and `web/`, and `main.py` — plus `errors.py` and `tests/`, in one
  Python package unit. No other top-level code part exists.
  — *verified by:* layer 6, a test that lists the product root's Python packages and modules and
  fails on one outside that set *(traces to: ADR-0001; SDD § 3, the parts and the units)*
- **QC-2:** `main.py` is the composition root. It is the only module that names a concrete
  `persistence` or `web` class, and it builds the real clock. No module imports `main`.
  — *verified by:* layer 6, an import and name walk over every module outside `tests/`
  *(traces to: ADR-0001; SDD § 3 `main` row; `<CORE>/doctrine/engineering/arch_defaults.md`
  § Composition Root)*
- **QC-3:** `application` states its two contracts — saving the whole state, and the clock — as
  `typing.Protocol` classes. The classes that satisfy them do so structurally and inherit from
  neither.
  — *verified by:* layer 6, a walk of every class definition outside `tests/` that fails on a base
  class naming either contract *(traces to: ADR-0004; ADR-0005; SDD § 3 `SM-3`, `SM-7`;
  `<CORE>/doctrine/engineering/arch_defaults_python.md` § Repository typing)*
- **QC-4:** `errors.py` holds the one base error, which derives from `Exception`. Every other
  exception class in the product derives from that base, and none derives directly from
  `Exception` or `BaseException`.
  — *verified by:* layer 6, a walk of every class definition outside `tests/`
  *(traces to: SDD § 3, the units; § 4 OB-4; `<CORE>/doctrine/engineering/arch_defaults.md`
  § Exception shape)*
- **QC-5:** Each refused condition has its own refusal type, defined in `domain/` and raised by
  `domain`. `application` names each refusal type for `web` and defines no refusal of its own, and
  `web` receives the types only through `application` (QC-16). `web` maps a refusal to its reason by
  type, and no part tells one refusal from another by reading its message.
  — *verified by:* SRS AC-12's tests, one per refusal, at layer 3, which fail when a refusal shows the
  wrong reason — including a refusal `domain` adds and `application` does not hand on, which `web`
  then cannot map; the by-type half, and the half that `application` defines no refusal, are a review
  at `development-design` for a change that adds a refusal or touches `application`'s or `web`'s
  handling of one, because no scanner tells code that formats a message from code that branches on
  one, and the SDD gives a refusal no base class of its own that a walk could look for *(traces to:
  SDD § 3 `domain` row, the units, `SM-1`; § 4 OB-4; SRS FR-39; owner,
  `trail/architecture/cycle-1.md` § 2.3; see RN-5)*
- **QC-6:** Every entity and the tracker state in `domain/` is immutable, and every rule returns a
  new value instead of changing the one it was given.
  — *verified by:* layer 6, a walk that fails on a `domain/` dataclass not declared `frozen=True`
  *(traces to: ADR-0004; SDD § 3 `domain` row; `<CORE>/doctrine/engineering/arch_defaults_python.md`
  § Entity immutability)*
- **QC-7:** Only a form submission changes the tracker state. A request that is not a form submission
  leaves the state unchanged, and every form submission is answered by sending the browser to a page
  address built by the one function in `web` that builds them.
  — *verified by:* layer 3, a test that enumerates `web`'s routes from `web` itself, sends each
  non-submission request and asserts the state is unchanged, and sends each submission and asserts a
  redirect *(traces to: ADR-0006; SDD § 4 RT-8; SRS NFR-4)*
- **QC-8:** No response sets a cookie, and `web` keeps nothing between requests except what reaches
  it through `application`.
  — *verified by:* layer 3, the QC-7 route test also asserts no `Set-Cookie` header on any response;
  layer 6 fails on an import of `http.cookies`; the keeps-nothing half is a review at
  `development-design` for a change to `web`, because state held in a module-level value is not
  reliably distinguishable from a constant by a scanner *(traces to: ADR-0006; SDD § 4 RT-7)*
- **QC-63:** A page that shows a pending confirmation of a move to `cancelled` is answered with HTTP
  status 202, and every other page a move's interaction or outcome lands on with 200. Each of them
  carries `Cache-Control: no-store`. The status is read off the page as built, never off the address
  alone. A confirmation address naming a task no task holds answers the not-found page, 404, with no
  `no-store`, and is outside this obligation. No move response carries `Clear-Site-Data`: no move
  submission's response, and neither the confirmation page nor the back-out page.
  — *verified by:* layer 3, `tests/integration/test_routes.py`,
  `test_pending_confirmation_response_matches_the_rendered_page`,
  `test_non_confirmation_move_views_keep_their_response_contract`,
  `test_move_interaction_and_outcome_pages_are_not_stored` and
  `test_move_responses_do_not_clear_site_data`; layer 5, `tests/e2e/test_moves.py`,
  `test_history_matrix_revalidates_current_saved_status` and
  `test_real_history_traversal_revalidates_the_confirmation`, which fail when a return to a
  confirmation's address is restored from history instead of loaded. Layer 5 proves the build the
  pinned library installs, Chromium 153.0.8010.12 under `playwright==1.63.0`, and not the operator's
  current stable Chrome *(traces to: ADR-0010; SDD § 4 RT-11, § 9 TO-8, § 11 R-12; SRS NFR-3, NFR-13;
  UXD § 4, UX-F4, UX-I3; owner, `trail/architecture/cycle-12.md` § 2.1; see RN-44)*
- **QC-9:** The two maximum text lengths are stated once, in `domain`, and every text field's
  `maxlength` is written from them, as is the maximum the description field and the comment field
  state beside them. `web` turns each submitted CR LF pair, and each remaining CR, into
  one LF before the value reaches `application`, and changes a typed value in no other way. A change
  that adds a text field writes its `maxlength` and a test that a longer value is refused.
  — *verified by:* layer 6, a test that fails on the literals `200` or `4000` used as a length outside
  `domain/`; layer 4, a test that builds the create-project form and the add-comment form and fails
  when the number the sentence beside the field states differs from that field's `maxlength`; SRS
  AC-20's end-to-end tests at layer 5; SRS AC-12's over-long refusal test at layer 3
  *(traces to: ADR-0007; SDD § 4 RT-10; SRS FR-40; UXD UX-F2, UX-F7; see RN-19, RN-15)*
- **QC-10:** Project and task identities are issued only from the two counters kept in the tracker
  state, and both counters are saved with it.
  — *verified by:* layer 2, a test that deletes a task, restarts on the same saved data and creates a
  task, and asserts the deleted identity is not issued again; SRS AC-7's reused-identity test
  *(traces to: ADR-0008; SDD § 3, What the system holds; SRS FR-15, DR-6)*
- **QC-11:** Each Core Feature in SDD § 4 TS-3's table whose slice has landed has its entry module
  `domain/<feature word>.py`, and its word is listed as landed in the pointer test. Its opening
  docstring names the SRS requirements it realizes, every `application` and `web` module that takes
  part, and the test modules that check it. Every test module names the requirements or acceptance
  criteria it checks.
  — *verified by:* the pointer test of SDD § 4 TS-4, in `pytest tests/`, which fails on a named path
  that does not exist, a requirement identifier not in `products/tracker17/docs/SRS.md`, a feature
  word in TS-3's table whose slice has landed and that has no module, or a feature word in that table
  that has its module and is not listed as landed. `tests/architecture/test_trace.py` holds all four
  checks. The fourth, `test_each_feature_word_with_its_domain_module_is_listed_as_landed`, reads
  TS-3's words from `docs/SDD.md` when the suite runs and fails when it reads none, the rule § 1.2
  and § 9 give every layer-6 walk. The reverse check reads only TS-3's words, so a `domain/` module
  that is no feature's entry is never flagged *(traces to: SRS NFR-9, AC-5; SDD § 4 TS-3, TS-4,
  RN-34; owner, `trail/architecture/cycle-3.md` § 3.1, `trail/architecture/cycle-5.md` § 3.1; see
  RN-21, RN-26)*
- **QC-12:** The code and tests stay small and plain enough for the owner, reading cold, to judge the
  product simple. No size metric stands in for that judgement.
  — *verified by:* review at `development-design`, asking whether a change adds a part that no
  requirement pays for (SDD § 1, "Every part this design adds is a part the reader has to read"), and
  the owner's pass/fail call at the Agari check (SRS AC-4). No command can check it, because NFR-10
  forbids a metric standing in *(traces to: SRS NFR-10, AC-4)*

### 1.2 Forbidden imports

Each module appears once. "Third-party" means any module not in Python's standard library
(`sys.stdlib_module_names`) and not part of tracker17. Every entry is verified by one layer-6 test
that walks the imports of every module on disk, and that test fails when a directory it walks holds
no module, so a walk rooted at the wrong path cannot pass by finding nothing (§ 9).

- **QC-13:** `domain/` may import `errors` and the standard library. It must not import from:
  `application`, `persistence`, `web`, `main`, `tests`, or any third-party module.
  — *verified by:* layer 6, import walk *(traces to: ADR-0001; SDD § 3, the direction of dependence)*
- **QC-14:** `application/` may import `domain` and `errors`. It must not import from:
  `persistence`, `web`, `main`, `tests`, or any third-party module.
  — *verified by:* layer 6, import walk *(traces to: ADR-0001; SDD § 3 `application` row)*
- **QC-15:** `persistence/` may import `domain` and `errors`. It must not import from:
  `application`, `web`, `main`, `tests`, or any third-party module.
  — *verified by:* layer 6, import walk *(traces to: ADR-0001; SDD § 3 `persistence` row)*
- **QC-16:** `web/` may import `application` and `errors`. It must not import from: `domain`,
  `persistence`, `main`, `tests`, or any third-party module. The refusal types `web` maps reach it
  through `application` (QC-5).
  — *verified by:* layer 6, import walk *(traces to: ADR-0001; SDD § 3, the direction of dependence
  and `SM-1`; § 4 RT-10, "`web` receives them through `application`"; owner,
  `trail/architecture/cycle-1.md` § 2.3; see RN-5)*
- **QC-17:** `main.py` may import `domain`, `application`, `persistence`, `web` and `errors`. It must
  not import from: `tests`, or any third-party module.
  — *verified by:* layer 6, import walk *(traces to: ADR-0001; SDD § 3, "`main` imports all four")*
- **QC-18:** `errors.py` imports no part of tracker17 — not `domain`, `application`, `persistence`,
  `web` or `main` — and no third-party module.
  — *verified by:* layer 6, import walk *(traces to: ADR-0001; SDD § 3, "Every part may import
  `errors.py`")*
- **QC-19:** No module outside `tests/` imports a third-party module, and no module outside `tests/`
  imports from `tests/`.
  — *verified by:* layer 6, import walk *(traces to: ADR-0002; SDD § 4 RT-1, RT-4)*

### 1.3 Layer isolation

The import half of each clause is § 1.2's. The reach half — files, sockets, the clock, the console —
is checked by § 3's capability entries, named in each clause.

- **QC-20:** `domain` takes everything it needs as arguments and returns values. It does no input or
  output — no file, no socket, no console — never reads the machine's clock, builds no HTML, and holds
  no wording shown to the operator.
  — *verified by:* layer 6, a walk of `domain/` that fails on a call to `open`, `print` or `input`, on
  a clock read (QC-44), and on an import of `html`; the no-wording half is a review at
  `development-design`, because a scanner cannot tell a refusal's reason from an identifier string
  *(traces to: ADR-0001; SDD § 3 `domain` row; § 4 TS-1)*
- **QC-21:** `application` holds the current state and nothing else between requests. Each action is
  one call that applies a `domain` rule to the current state. An action whose `domain` outcome
  reports a change saves the new state and only then makes it current. An action whose outcome
  reports none returns the current state and saves nothing. Which outcomes report none is `domain`'s,
  decided per action and read off the outcome. What the report compares is `domain`'s too, decided
  per action. The task edit compares each value submitted with the value the page showed (SDD § 4
  RT-7). An action that compares with what the state holds at the moment of the action — setting the
  operator name and adding a label do — follows SRS NFR-3. `application` compares nothing in either
  case. It owns no rule of its own, no HTML or request detail, and no knowledge of how or where the
  state is saved. It does no input or output of its own; the saver and the clock are handed to it.
  — *verified by:* layer 6, QC-42 to QC-45 over `application/`; layer 3,
  `tests/integration/test_task_tracker.py::test_tracker_unchanged_edit_never_saves`, which fails when
  an unchanged edit reaches the saver; layer 3,
  `tests/integration/test_people_routes.py::test_stale_people_name_submission_compares_with_current_name`,
  which fails when a name equal to the saved one reaches the saver or when the People form carries a
  shown-name value; layer 1, `tests/unit/test_tasks.py::test_duplicate_task_label_reports_no_change`,
  which fails when a label the task already carries reports a change; the no-rule half is a review
  at `development-design`, because a scanner cannot tell a rule from the flow that calls one, and a
  state comparison added to `application` is a rule *(traces to: ADR-0001; SDD § 3 `application`
  row (version 10), § 4 RT-7; SRS NFR-3; owner, `trail/sdd/cycle-6.md` § 5.1,
  `trail/sdd/cycle-7.md` § 5.1, `trail/architecture/cycle-9.md` § 3.1,
  `trail/architecture/cycle-10.md` § 3.1; `<CORE>/doctrine/engineering/arch_defaults.md`
  § Application Layer; see RN-37, RN-39)*
- **QC-22:** `persistence` owns the saved data's file input and output and nothing else: its
  location, its format, reading it at start, writing it whole, and the one-tracker lock. It holds no
  data rule. It builds the state through `domain`'s constructors and reports their refusal as
  unreadable data, and decides nothing about what happens then.
  — *verified by:* SRS AC-7's tests at layer 2, one per kind of break DR-6 names, which fail when a
  break is not reported as unreadable; layer 6, QC-43 to QC-45 over `persistence/`; the no-rule half
  is a review at `development-design` *(traces to: ADR-0001; SDD § 3 `persistence` row; § 4 SD-5)*
- **QC-23:** `web` owns listening, the request check, addresses, reading form fields, page building
  and the stylesheet. It owns no rule and keeps no state between requests (QC-8). It reaches neither
  the saved data nor the clock, and writes to the console only at its one failure site (QC-45).
  — *verified by:* layer 6, QC-42, QC-44 and QC-45 over `web/`; the no-rule half is a review at
  `development-design` *(traces to: ADR-0001; SDD § 3 `web` row)*
- **QC-24:** `main.py` wires the parts, chooses between the normal tracker and the page for
  unreadable data, and writes the start messages. It holds no rule, no page and no file format.
  — *verified by:* layer 6, QC-42 and QC-43 over `main.py`; the no-rule half is a review at
  `development-design` *(traces to: ADR-0001; SDD § 3 `main` row)*

### 1.4 Replaceability

- **QC-25:** Changing the saved data's file format touches `persistence` only; no other part changes.
  — *verified by:* review at `development-design` when a change touches `persistence`. No test can
  exercise a swap that has not happened; QC-15 and QC-14 keep the other parts from knowing the format
  *(traces to: ADR-0004; SDD § 11 R-1, the first remedy; FDR PD-15)*
- **QC-26:** Replacing the whole-state save with one operation per kind of change touches
  `persistence`, the saving contract and the `application` actions that call it. `domain` and `web`
  do not change, and the change lands with a record superseding ADR-0004.
  — *verified by:* review at `development-design` when a change touches the saving contract
  *(traces to: ADR-0004; SDD § 9 TO-3)*
- **QC-27:** Replacing the browser interface — adding a framework, a script, or a store for the last
  outcome — touches `web` and the wiring in `main.py` only. `domain`, `application` and `persistence`
  do not change.
  — *verified by:* review at `development-design` when a change touches `web`; QC-16 and QC-14 keep
  HTML and request detail out of the inner parts *(traces to: ADR-0001; SDD § 9 TO-1, TO-2, TO-7; FDR
  PD-15)*
- **QC-28:** The source of the current date and time is replaceable: a test hands `application` a
  clock, and no test patches a name inside a product module.
  — *verified by:* SRS AC-13's tests, which set today's date through a clock handed in; layer 6, a
  walk of `tests/` that fails on `monkeypatch.setattr` or `unittest.mock.patch` aimed at a product
  module *(traces to: SDD § 4 TS-2; § 2, force 4; FDR PD-15)*
- **QC-29:** The saver is replaceable: a test hands `application` an object that saves, and can
  interrupt or fail it.
  — *verified by:* SRS AC-9's interrupted-save test and AC-18's failure test *(traces to: SDD § 4
  TS-2; § 2, force 4; FDR PD-15)*

## 2. Security

**Trust boundaries.** Four, and every entry below names the one it guards:

- **B-1, the listener** — requests reaching the tracker's loopback address from the operator's
  browser, including requests a page from any other origin open in that browser makes it send.
- **B-2, the saved data at start** — the one input the tracker did not just write, which may have
  been changed by hand or damaged (SRS DR-6).
- **B-3, typed text shown back** — every value the operator typed, put into a page.
- **B-4, setup** — the test dependencies and the browser fetched once from public sources, and, on
  Linux, the system libraries that browser needs, which the same one-time step installs through the
  distribution's package manager with administrator rights (SDD § 4 RT-4). The system libraries are
  the operating system's, as Python is: no lock file names them, nothing pins them, and QC-39 and
  QC-40 do not reach them (see RN-27).

- **QC-30:** *(B-1)* The tracker listens on one loopback address and no other; the address constant's
  host is a loopback address.
  — *verified by:* layer 1, a test that asserts `ipaddress.ip_address(<host>).is_loopback` on the
  address `main` passes to `web` *(traces to: SRS FR-2, AC-10; SDD § 4 RT-5; § 11 R-7; see RN-2)*
- **QC-31:** *(B-1)* A request whose `Host` header does not name the tracker's own address is refused
  before any other code in `web` runs, and the refusal changes nothing.
  — *verified by:* layer 3, a test per refusal asserting the reply and unchanged saved data
  *(traces to: SRS NFR-4, AC-10; SDD § 4 SEC-2)*
- **QC-32:** *(B-1)* Before any other code in `web` runs, the request check refuses every request
  the browser marks `Sec-Fetch-Site: cross-site` or `same-site` — a page from another port on the
  same machine is `same-site` — and every form submission it does not mark `same-origin`, a
  submission marked `none` or carrying no mark included. A request marked `none` that is not a
  submission opens its page. A refusal changes nothing. Every test that sends `web` a submission
  without a browser — the layer-3 tests and `tests/timed_run.py` — marks it `same-origin`.
  — *verified by:* layer 3, SRS AC-10's tests: one request under each refused mark, one submission
  marked `none` and one with no mark, each asserting a refusal and unchanged saved data, and one page
  request marked `none` asserting the page opens; QC-48's timed run fails on a refused action, so a
  run that sends no mark cannot pass by timing refusals *(traces to: SRS NFR-4, AC-10; SDD § 4 SEC-2,
  TS-5; owner, `trail/architecture/cycle-1.md` § 2.1; see RN-3)*
- **QC-33:** *(B-1)* No page can be shown inside a frame. The page policy travels as a
  `Content-Security-Policy` response header on every response, never as a tag in a page, and it
  carries the directive `frame-ancestors 'none'`.
  — *verified by:* layer 3, the QC-7 route test also reads the directive from the response header of
  every response; layer 4, the same tests assert that no built page carries the policy as a `<meta>`
  tag *(traces to: SRS NFR-4; SDD § 4 SEC-3; owner, `trail/architecture/cycle-1.md` § 2.2; see
  RN-4)*
- **QC-34:** *(B-1, B-3)* Every page is served with a policy that lets the browser load only from the
  tracker's own address and run no script.
  — *verified by:* layer 3, the QC-7 route test also asserts the policy, read from the response
  header QC-33 names, on every page *(traces to: ADR-0003; SRS NFR-5; SDD § 4 SEC-3, EX-2, EX-10;
  see RN-15)*
- **QC-35:** *(B-1)* The running tracker opens no outbound connection.
  — *verified by:* layer 3, a test that drives every action through `web` in one process under a
  Python audit hook and fails on any `socket.connect` event; the owner's run-through with the network
  off (SRS AC-11) *(traces to: SRS NFR-5, AC-11; SDD § 4 SEC-3;
  `<CORE>/doctrine/engineering/quality_defaults.md` § The boundary set; see RN-8)*
- **QC-36:** *(B-3)* Typed text is shown as text. One function in `web` puts a value into a page and
  escapes every value it is given; no page builds HTML from a typed value any other way.
  — *verified by:* the end-to-end tests at layer 5 that enter `<`, `&` and `"` in every text field a
  change adds and assert the page shows them as typed (SDD § 11 R-3); the one-function half is a
  review at `development-design` for a change to page building, because a scanner cannot tell an
  escaped value from one that needs no escaping *(traces to: ADR-0002; SDD § 4 SEC-4; § 11 R-3; FDR
  R-112)*
- **QC-37:** *(B-2)* The saved data is read as data. It is parsed by a reader that executes nothing,
  built only through `domain`'s constructors, and refused whole when any part breaks a rule; it is
  never partly loaded. No module outside `tests/` imports `pickle`, `marshal` or `shelve`, or calls
  `eval` or `exec`.
  — *verified by:* SRS AC-7's tests at layer 2; layer 6, an import and call walk
  *(traces to: SRS DR-6; SDD § 4 SD-5; `<CORE>/doctrine/engineering/quality_defaults.md` § Outside
  content; see RN-9)*
- **QC-38:** *(B-1)* Every value a request carries is checked by a `domain` rule before any state
  changes, and a value that breaks one changes nothing. `web` checks no value of its own beyond the
  request check of QC-31 and QC-32.
  — *verified by:* SRS AC-12's tests at layer 3, one per refusal, each asserting unchanged saved data
  *(traces to: SRS FR-39; SDD § 4 SD-5, § 3 `web` row; `<CORE>/doctrine/engineering/quality_defaults.md`
  § Input at the boundary; see RN-7)*
- **QC-39:** *(B-4)* Every test dependency is declared in `pyproject.toml` at an exact version, and
  one committed lock file fixes it and everything it pulls in.
  — *verified by:* layer 6, a test that reads `pyproject.toml` with `tomllib` and fails on a test
  dependency not pinned with `==`, or on a missing lock file *(traces to: ADR-0002; SRS C-8, AC-3;
  SDD § 4 RT-4)*
- **QC-40:** *(B-4)* A change that adds a test dependency, or moves a pin, picks no version that a
  known critical advisory is against when a version free of one is published on the index the pin
  installs from. Moving the browser-driving library's pin chooses the browser build, so the browser
  build is held to the same rule. A change that adds a dependency whose every version on that index
  carries a critical advisory may choose one; where that advisory is more than 30 days old, the
  change needs the owner's dated exception before it lands. A critical advisory against a test dependency the lock file of QC-39 fixes, or
  against the browser build the pinned browser-driving library installs, is fixed within **30 days of
  the day the advisory is published**. A fix moves the pin; where none comes within the window, the
  dependency is replaced or removed, or the owner records a dated exception with its reason in a
  Review Note here, which is the only way to be past the window without being late. **The owner
  watches the advisories**, through two feeds: Dependabot alerts on the repository that holds
  tracker17, for the packages, which reach them only while the lock file is in a format GitHub's
  dependency graph reads; and, for the browser, which no manifest or lock file names, a comparison of
  the installed browser version with the browser vendor's security releases at each
  `development-design` review.
  — *verified by:* review at `development-design`, at two moments: when a change adds or changes a
  test dependency or chooses the lock file's format, where the version chosen is checked against
  published advisories and against the versions on the index the pin installs from, and at every review, where the pins and the
  browser build are checked against published advisories and a critical advisory more than 30 days
  old blocks the change until the pin moves or a dated exception is recorded. No command can measure
  a window, and no audit command exists for this product: the Python packet names none and tracker17
  installs none *(traces to: `<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies;
  owner, `trail/architecture/cycle-2.md` § 1.1, `trail/architecture/cycle-6.md` § 2.1,
  `trail/architecture/cycle-7.md` § 3.1; see RN-10, RN-18, RN-31, and RN-33 for the dated exception in
  force)*
- **QC-41:** The product reads, holds and writes no secret: no account, no key, no credential, at
  setup or in use. A change that introduces one is out of bounds.
  — *verified by:* review at `development-design`. No secrets scanner exists for this product, and
  that is the gap: a secret committed by mistake is caught by no command *(traces to: SRS C-2;
  `<CORE>/doctrine/engineering/quality_defaults.md` § Secrets; see RN-10)*

## 3. Authentication & access control

**Identity and authorization — not applicable.** There is one operator, on the machine the tracker
runs on, and no part adds a user, a role or a login (SDD § 4 SEC-1; SRS C-1, NFR-7; FDR PD-16). What
makes that true is the boundary of QC-30: the tracker answers only the loopback address, so the only
caller is someone already at the operator's machine. **What would change it:** a listener on any
address other than loopback, or a second operator. Either is a change to SRS C-1 and NFR-7 before it
is a change here.

**What the loopback boundary does not cover.** Any other program on the machine, under any account,
can reach the loopback address. QC-31 and QC-32 stop requests a browser sends for another origin's
page, because the browser writes `Host` and `Sec-Fetch-Site` and a page cannot forge them. They do
not stop a local program, which writes both headers itself. With one operator on their own machine
(SRS C-1, NFR-7; SDD § 4 SEC-1), that caller is already inside the machine, and this declaration
accepts it. A second account on the machine in scope would be a change to SRS C-1 and NFR-7 first
(owner, `trail/architecture/cycle-1.md` § 2.5; see RN-16).

**Privilege — binds.** The parts have different reach, and the entries below hold each to its own.

- **QC-42:** Only `persistence` opens a file for writing, renames, replaces or deletes one, and only
  inside `data/` under the product root. The location is worked out from where the code is, never
  from the directory the command was run in.
  — *verified by:* layer 6, a walk outside `persistence/` and `tests/` that fails on `open` in a write
  mode, `Path.write_text`/`write_bytes`, `os.replace`, `os.rename`, `os.remove` or `os.unlink`;
  layer 2, a test that starts from another working directory and asserts the location is unchanged
  *(traces to: SDD § 4 SD-3, SD-6, OB-1; SRS FR-6; `<CORE>/doctrine/engineering/quality_defaults.md`
  § Capability)*
- **QC-43:** Only `web` opens a socket, and only to listen. No module outside `web/` imports `socket`,
  `socketserver` or `http.server`, and no module imports `http.client`, `urllib.request`, `ftplib` or
  `smtplib`.
  — *verified by:* layer 6, import walk *(traces to: ADR-0002; SDD § 4 RT-5, SEC-3;
  `<CORE>/doctrine/engineering/quality_defaults.md` § Capability)*
- **QC-44:** No module in `domain/`, `application/`, `persistence/` or `web/` reads the machine's
  clock. The real clock is built in `main.py` and handed in.
  — *verified by:* layer 6, a call walk that fails on `datetime.now`, `datetime.today`, `date.today`,
  `time.time` or `time.localtime` in those directories *(traces to: SDD § 3 `SM-7`; § 4 TS-2; § 2,
  force 4)*
- **QC-45:** Only `main.py`, and one site in `web/`, write to the console.
  — *verified by:* layer 6, a walk that fails on `print`, `sys.stdout` or `sys.stderr` elsewhere
  outside `tests/`, and on more than one module in `web/` using them *(traces to: SDD § 4 OB-1, OB-2,
  OB-3)*

## 4. Privacy, data retention & compliance

tracker17 holds the names the operator types — the assignee list, the operator's own name, comment
authors — and the work they enter, on their machine only, until they delete the saved data (PRD
§ Data & Privacy; SRS NFR-6). No obligation beyond the operator's own applies, and the PRD names no
regulation. The tracker keeps no log file (QC-42 keeps every file write inside `persistence`). Typed
text that travels in an address reaches the browser's history, which is the browser's store and a
cost ADR-0006 records.

- **QC-46:** The saved data holds the fields SRS DR-1 to DR-5 describe, the two identity counters
  (ADR-0008), and nothing else — no other fact about any person, and no record of requests, addresses
  or usage.
  — *verified by:* layer 2, a test that runs SRS AC-6's sequence and fails on any key in the saved
  file outside that set; the owner's inspection after the AC-1 run-through (SRS AC-17); a review at
  `development-design` for any change that adds a saved field *(traces to: SRS NFR-6, AC-17; SDD § 4
  SD-6; `<CORE>/doctrine/engineering/quality_defaults.md` § Data; see RN-11)*
- **QC-47:** Version control ignores `data/`.
  — *verified by:* `git check-ignore -q data/probe`, run from the product root, exits 0; the same
  check rides `pytest tests/` as `test_data_is_ignored_by_version_control` in
  `tests/integration/test_start.py`. Both need the copy to be a Git repository with `git` on the
  path. The disposable copy `<CORE>/roles/CROSS_ROLE.md` § *Every seat* has a run outside the
  change's worktree use is a fresh clone at the commit under test, which is one, so the check runs
  and passes there. In a copy that is not one — one unpacked from a download, or from `git archive`
  — the check fails rather than skips, and that one failure is the suite's missing prerequisite, not
  this obligation broken *(traces to: SRS FR-6; SDD § 4 SD-6; § 6 `first-project` *Artifact*,
  RN-39; owner, `trail/architecture/cycle-10.md` § 3.2; see RN-28, RN-40)*

## 5. Performance & capacity

- **QC-48:** With 1,000 tasks across all projects and 20 comments on every task, at ordinary text
  lengths, every action SRS NFR-1 lists shows its result within 1 second on the owner's machine. The
  timed run states the lengths it uses, and a change that adds a listed action adds it to the run.
  It marks every submission `same-origin` (QC-32) and fails when a timed action is refused or fails,
  so it times only actions that happened.
  Capacity beyond that volume is not an obligation: one operator is the only scale (SRS NFR-7).
  — *verified by:* `python3 tests/timed_run.py` exits 0 *(traces to: SRS NFR-1, NFR-7, AC-15; SDD
  § 4 TS-5, SEC-2; § 11 R-1; see RN-3)*

## 6. Availability & reliability

- **QC-49:** An action is reported done only after the whole new state is on disk. When the save
  fails, the state from before the action stays current and the action is reported as failed.
  — *verified by:* SRS AC-18's test at layer 3, with a saver that fails, asserting the old state and
  the failure page *(traces to: ADR-0004; SRS FR-9, NFR-8; SDD § 4 SD-2)*
- **QC-50:** A save writes the new state to a second file in the same directory, forces it to disk and
  renames it over the old one. A save cut off part-way leaves the state from before or after, never a
  mix.
  — *verified by:* SRS AC-9's interrupted-save test at layer 2 *(traces to: ADR-0004; SRS NFR-2; SDD
  § 4 SD-3)*
- **QC-51:** Saved data that could not be read is never written, replaced or deleted.
  — *verified by:* SRS AC-7's tests at layer 2, each asserting the saved data's bytes are unchanged
  *(traces to: SRS FR-8; SDD § 4 SD-4)*
- **QC-52:** At most one running tracker uses a saved-data location. A second start against it
  refuses and changes nothing; a start after a tracker was killed succeeds.
  — *verified by:* SRS AC-16's two tests at layer 2 *(traces to: ADR-0005; ADR-0009; SRS NFR-3; SDD
  § 3 `persistence` row)*
- **QC-53:** One action is applied at a time: a single lock is held from the start of a request's
  check until its result is saved.
  — *verified by:* layer 3, a test that holds a first save open through a saver handed in and asserts
  a second request does not reach the saver until the first is released *(traces to: ADR-0005; SRS
  NFR-3; SDD § 4 RT-6)*
- **QC-54:** The saved data is read once, at start, and never again while the tracker runs.
  — *verified by:* layer 3, a test that runs every action against an `application` built with a
  recording saver and asserts the saver received only saves *(traces to: ADR-0005; SDD § 4 SD-1)*

## 7. Observability & monitoring

The console the tracker was started from is the only place a failure shows outside a page (SDD § 4
OB-1). There is no record of who did what beyond the saved data itself, and NFR-6 forbids one: with
one operator, a comment's author and time is the whole of that record, and it is behaviour (FDR R-72).

- **QC-55:** At start, the console shows the address to open and the saved-data location, and nothing
  before them.
  — *verified by:* layer 5, the end-to-end harness starts `python3 main.py` and asserts its first
  console lines *(traces to: SRS FR-1, NFR-8; SDD § 4 OB-2)*
- **QC-56:** A failure that is not a refusal is caught in one place in `web`, which writes the action
  and the error to the console and answers with the page saying the action did not happen. The saved
  data is unchanged.
  — *verified by:* SRS AC-18's test at layer 3 *(traces to: SRS NFR-8, AC-18; SDD § 4 OB-3;
  `<CORE>/doctrine/engineering/quality_defaults.md` § Failure visibility)*
- **QC-57:** No page shows error text produced by Python — no exception message and no traceback.
  — *verified by:* the AC-18 test also asserts the page holds neither *(traces to: SDD § 4 OB-3; FDR
  R-108; `<CORE>/doctrine/engineering/quality_defaults.md` § Failure visibility)*
- **QC-58:** A start the tracker itself refuses — the address taken, another tracker running —
  shows one plain console message and writes nothing to the saved data.
  — *verified by:* layer 2 tests for each refused start, asserting the message and the saved data's
  bytes *(traces to: SRS FR-3, NFR-3; SDD § 4 OB-2)*

## 8. Operational constraints

The execution context — headless, and the suite command — is `system/projects/tracker17/project.md`'s.
The start command and the setup steps are behaviour (FDR R-1, R-8 to R-13). What exceeds both:

- **QC-59:** `pyproject.toml` declares `requires-python = ">=3.11"`.
  — *verified by:* layer 6, a test that reads `pyproject.toml` with `tomllib` *(traces to: ADR-0002;
  SDD § 4 RT-1)*
- **QC-60:** The tracker and its tests run on Python 3.11.
  — *verified by:* review at `development-design` for a change that uses a language or library
  feature. The harness is missing: the suite runs only on the machine's Python, 3.14.7 on the owner's
  machine, and one run of `pytest tests/` under a 3.11 interpreter would settle it (SDD § 11 R-8)
  *(traces to: ADR-0002; SDD § 4 RT-1; § 11 R-8)*
- **QC-61:** The tracker checks no operating system and carries no code for one: no module outside
  `tests/` reads `sys.platform`, `os.name` or `platform.system`, or imports `msvcrt` or `winreg`.
  — *verified by:* layer 6, an import and attribute walk *(traces to: ADR-0009; SDD § 4 RT-3; see
  RN-29)*
- **QC-62:** The code passes Ruff's format check, Ruff's lint at the rule set `pyproject.toml`
  configures, and mypy over QC-1's parts outside `tests/`, at the versions QC-39 pins. Where a Ruff
  rule contradicts an entry in this document, the entry wins, and the site turns that one rule off
  inline with a comment naming the entry: QC-56's one catch site, which Ruff reports as `BLE001`, is
  the standing case. A change that moves the Ruff or the mypy pin repairs or turns off, in that
  change, what the new version finds.
  — *verified by:* three commands, each passing on exit 0: `ruff format --check .`, `ruff check .`,
  and `mypy main.py errors.py domain application persistence web`. mypy is held to those parts
  because over the whole root it stops on the two `conftest.py` files, exit 2, before checking
  anything. The gate starts red: on the code as of commit `691edf98b`, `ruff check .` reports 8
  findings and mypy 3 errors, and the owner's answer has the first change after this revision repair
  them *(traces to: owner, `trail/architecture/cycle-3.md` § 3.2;
  `<CORE>/doctrine/engineering/languages/python/quality_gates.md` § What a product installs, when it
  installs one; QC-39; see RN-22)*

## 9. Test strategy

The layer set is **not defined here** — it is `<CORE>/doctrine/engineering/testing_doctrine.md`, and
this table is one project's realization of it. Tooling and paths come from that doctrine's language
overlay (`testing_python.md` for Python; a product in another language records its own tools here). If
this table and the doctrine disagree on the layers, this table is the copy and is wrong.

SDD § 4 TS-1 names three layers — unit, integration and end-to-end — and the table places what it
names on the doctrine's seven.

| Level | Scope | Tool | Where it lives |
|---|---|---|---|
| 1 — Unit | `domain`: every rule, with no file and no clock; and QC-30's check of the address constant, which needs no file, socket or clock | pytest | `tests/`, one module per feature word |
| 2 — Integration | `persistence` against real files in a test's own directory: AC-7, AC-9, AC-16, the restart tests | pytest with `tmp_path` | `tests/` |
| 3 — Application | `web` with `application` and `domain` in one process with no socket, the clock and the saver handed in: refusals, the request check, the page policy, the route test | pytest | `tests/` |
| 4 — UI | the page `web` builds for a given state: escaping, `maxlength`, `autofocus` — asserted in the same in-process tests as layer 3 | pytest | `tests/` |
| 5 — End-to-End | a tracker started by `main` on its own location and port, driven in Chromium | pytest with the browser-driving library SDD § 4 RT-4 pins (named by no upstream document) | `tests/e2e/` |
| 6 — Architecture | the import graph and the reach checks of §§ 1–3 and § 8 | pytest | `tests/architecture/` |
| 7 — Specification | — | — | — |

- **Layer 3 and layer 4 are both present.** SDD TS-1 calls the in-process tests "integration". By the
  doctrine's door rule they enter inside the listener, which makes them layer 3, and the assertions
  they make on built pages are layer 4's scope. Neither layer is omitted.
- **Layers 6 and 7 are QA-owned.** QA is not a step in this product's chain. Until it is, layer 6 is
  written as plain pytest under `tests/architecture/` with the change that first builds the module it
  checks, and runs in `pytest tests/`. Every layer-6 walk fails when the directory it walks holds no
  module, so a walk rooted at the wrong path, or run before the module exists, cannot pass by finding
  nothing. Layer 7 has no producer; SRS § 8's acceptance criteria are
  verified instead by the tests the SDD slices name at layers 2, 3 and 5, and by the owner's
  run-throughs for AC-1, AC-3, AC-4, AC-5, AC-8, AC-11 and AC-17.
- **Layer 5 runs on fewer systems than the rest.** On macOS it runs where the tracker does. On Linux
  it runs where the pinned browser-driving library does — for `playwright==1.63.0`, the Debian and
  Ubuntu releases SDD § 4 RT-4 lists — with the browser's system libraries RT-4 names installed. On
  any other Linux the tracker and `pytest tests/` run, and `pytest tests/e2e/` is a missing
  prerequisite (SDD § 4 RT-3, RT-4). The list is the pin's and moves only when the pin does. Layers
  1 to 4 and 6 need neither the browser nor administrator rights (see RN-27).
- **Outside the layers.** `python3 tests/timed_run.py` is the measurement of § 5, and the pointer test
  of QC-11 runs in `pytest tests/`. The two Python gates of
  `<CORE>/doctrine/engineering/languages/python/quality_gates.md` — compile and suite — apply as
  stated there, and QC-62 adds the three Ruff and mypy gates the same file names as the house default
  for a product that installs those tools.

## 10. Verification map

**"Runs over" is not decoration.** The same check catches different defects at different scopes: a
secrets scan over a change's diff catches a secret being *introduced*, over the whole tree catches one
already *there*; a dependency audit is only meaningful over the whole resolved set; a path-confinement
test runs against the entry points a change touches. Two values, and a row that cannot pick one has not
decided what it is checking.

Every row's command is typed from the product root, inside the virtual environment of SDD § 4 RT-4.
"Suite" in the last column means the green suite that `development-implementation`,
`development-code-integrity` and the step that seals a change each end on, stages 5 to 7 of
`<CORE>/doctrine/flow/development_flow.md` § The stages, run with the project card's `Test command:`; typed from the product root, as every row here is, that command is `pytest tests/`. SDD § 6 names
`pytest tests/e2e/` beside it as the second suite, and the layer-5 rows need both.

| QC | Check | Command / layer | Runs over | Gated at |
|---|---|---|---|---|
| QC-1 | top-level parts | `pytest tests/` · layer 6 | the tree | suite |
| QC-2 | composition root | `pytest tests/` · layer 6 | the tree | suite |
| QC-3 | contracts are structural | `pytest tests/` · layer 6 | the tree | suite |
| QC-4 | one error base | `pytest tests/` · layer 6 | the tree | suite |
| QC-5 | one refusal per condition | `pytest tests/` · layer 3 (AC-12) | the tree | suite |
| QC-6 | immutable entities | `pytest tests/` · layer 6 | the tree | suite |
| QC-7 | only submissions change state | `pytest tests/` · layer 3 | the tree | suite |
| QC-8 | no cookie | `pytest tests/` · layers 3 and 6 | the tree | suite |
| QC-9 | lengths stated once | `pytest tests/` · layers 3, 4 and 6; `pytest tests/e2e/` · layer 5 (AC-20) | the tree | suite |
| QC-10 | identities never reissued | `pytest tests/` · layer 2 | the tree | suite |
| QC-11 | trace pointers | `pytest tests/` · pointer test | the tree | suite |
| QC-13 | `domain/` imports | `pytest tests/` · layer 6 | the tree | suite |
| QC-14 | `application/` imports | `pytest tests/` · layer 6 | the tree | suite |
| QC-15 | `persistence/` imports | `pytest tests/` · layer 6 | the tree | suite |
| QC-16 | `web/` imports | `pytest tests/` · layer 6 | the tree | suite |
| QC-17 | `main.py` imports | `pytest tests/` · layer 6 | the tree | suite |
| QC-18 | `errors.py` imports | `pytest tests/` · layer 6 | the tree | suite |
| QC-19 | no third-party at run time | `pytest tests/` · layer 6 | the tree | suite |
| QC-20 | `domain` does no I/O | `pytest tests/` · layer 6 | the tree | suite |
| QC-21 | `application` does no I/O; saves only a reported change | `pytest tests/` · layers 1, 3 and 6 | the tree | suite |
| QC-22 | rules enforced at start | `pytest tests/` · layer 2 (AC-7) | the tree | suite |
| QC-23 | `web` reach | `pytest tests/` · layer 6 | the tree | suite |
| QC-24 | `main.py` reach | `pytest tests/` · layer 6 | the tree | suite |
| QC-28 | clock handed in, no patching | `pytest tests/` · layers 1–3 (AC-13) and 6 | the tree | suite |
| QC-29 | saver handed in | `pytest tests/` · layers 2–3 (AC-9, AC-18) | the tree | suite |
| QC-30 | loopback only | `pytest tests/` · layer 1 | the tree | suite |
| QC-31 | `Host` check | `pytest tests/` · layer 3 | the tree | suite |
| QC-32 | request check by `Sec-Fetch-Site` | `pytest tests/` · layer 3 (AC-10) | the tree | suite |
| QC-33 | no framing; policy as a header | `pytest tests/` · layers 3 and 4 | the tree | suite |
| QC-34 | page policy | `pytest tests/` · layer 3 | the tree | suite |
| QC-35 | no outbound connection | `pytest tests/` · layer 3 | the tree | suite |
| QC-36 | typed text shown as text | `pytest tests/e2e/` · layer 5 | the change | suite |
| QC-37 | saved data read as data | `pytest tests/` · layers 2 and 6 | the tree | suite |
| QC-38 | rules before state changes | `pytest tests/` · layer 3 (AC-12) | the tree | suite |
| QC-39 | test dependencies pinned | `pytest tests/` · layer 6 | the tree | suite |
| QC-42 | file writes | `pytest tests/` · layers 2 and 6 | the tree | suite |
| QC-43 | sockets | `pytest tests/` · layer 6 | the tree | suite |
| QC-44 | clock reads | `pytest tests/` · layer 6 | the tree | suite |
| QC-45 | console writes | `pytest tests/` · layer 6 | the tree | suite |
| QC-46 | stored fields | `pytest tests/` · layer 2 | the tree | suite |
| QC-47 | `data/` ignored | `git check-ignore -q data/probe`; `pytest tests/` · `test_data_is_ignored_by_version_control` — both in a Git repository only | the tree | suite |
| QC-48 | response time | `python3 tests/timed_run.py` | the tree | `development-implementation`, on the owner's machine |
| QC-49 | save before current | `pytest tests/` · layer 3 (AC-18) | the tree | suite |
| QC-50 | atomic replace | `pytest tests/` · layer 2 (AC-9) | the tree | suite |
| QC-51 | unreadable data untouched | `pytest tests/` · layer 2 (AC-7) | the tree | suite |
| QC-52 | one tracker per location | `pytest tests/` · layer 2 (AC-16) | the tree | suite |
| QC-53 | one action at a time | `pytest tests/` · layer 3 | the tree | suite |
| QC-54 | read once at start | `pytest tests/` · layer 3 | the tree | suite |
| QC-55 | start message first | `pytest tests/e2e/` · layer 5 | the tree | suite |
| QC-56 | failure path | `pytest tests/` · layer 3 (AC-18) | the tree | suite |
| QC-57 | no Python error text on a page | `pytest tests/` · layer 3 (AC-18) | the tree | suite |
| QC-58 | refused start | `pytest tests/` · layer 2 | the tree | suite |
| QC-59 | Python floor declared | `pytest tests/` · layer 6 | the tree | suite |
| QC-61 | no OS check | `pytest tests/` · layer 6 | the tree | suite |
| QC-62 | formatting | `ruff format --check .` | the tree | suite |
| QC-62 | lint | `ruff check .` | the tree | suite |
| QC-62 | types | `mypy main.py errors.py domain application persistence web` | the tree | suite |
| QC-63 | move pages: 202 for a pending confirmation, `no-store` | `pytest tests/` · layer 3; `pytest tests/e2e/` · layer 5 | the tree | suite |

QC-12, QC-25, QC-26, QC-27, QC-40, QC-41 and QC-60 are review gates and have no row.

---

## NFDR Review Notes

- **RN-1:** This run read the SRS, the SDD and the FDR in full, with the SDD's two answered rounds
  (`products/tracker17/docs/trail/sdd/cycle-1.md` in full, `cycle-2.md` § 2.1), the Agari and the
  project's doctrine in full, `UXD_open_issues.md` in full, and the PRD's § Data & Privacy. It read
  the UXD, `DESIGN.md` and `CONTENT.md` for their headers only and derived nothing from them: their
  bearing on this document reaches it through SDD § 4's experience conditions. It read three vendor
  pages for facts the upstream documents do not cite, named in RN-3, RN-4 and ADR-0004 —
  *because* every entry here must trace, and a vendor fact used is a fact cited. *(re: Inputs read)*
- **RN-2:** QC-30 checks the address in a test, where SRS AC-10 verifies FR-2's other-machine half by
  inspection — *because* the inspection's object, the address the tracker listens on, is a constant
  a test can read, so the check need not wait for a person. AC-10 still stands as written. *(re:
  QC-30; source: SRS AC-10, RN-17; SDD § 4 RT-5)*
- **RN-3:** QC-32 states the request check as SDD § 4 SEC-2 states it at version 4 — *because* the
  owner confirmed the drafted reading with an addition (`trail/architecture/cycle-1.md` § 2.1;
  reasoning, `trail/architecture/self_answer-1.md` § 2.1), and SDD RN-28 then restated SEC-2 to
  match. Version 1 of this entry read SEC-2's earlier "a request the browser marks as coming from
  another site" as "not marked same-origin", because SRS NFR-4 refuses "any request that does not
  come from its own pages" and a site ignores the port
  (https://developer.mozilla.org/en-US/docs/Glossary/Site), so a page from another program on the
  loopback address is `same-site`. The answer added SEC-2's every-request scope, which version 1
  dropped: any request marked `same-site` or `cross-site` is refused, and only a submission is held to
  `same-origin`, because the operator opening the tracker from the address bar sends `none`. It also
  added that a submission with no mark is refused, and that every test driving `web` without a
  browser marks its submissions. One improvement beyond the answer: QC-48's timed run fails on a
  refused action — *because* a run that forgot the mark would time refusals and still exit 0, and the
  answer names that risk without naming what catches it. *(re: QC-32, QC-48; source: SRS NFR-4,
  AC-10; SDD § 4 SEC-2, TS-5, RN-28)*
- **RN-4:** QC-33 adds `frame-ancestors 'none'` to the page policy — *because* SRS NFR-4 says a page
  from another origin "cannot read, change or delete tracker data", and a page that frames the
  tracker can lead the operator's own click to a submission the browser marks `same-origin`, which
  QC-31 and QC-32 both let through. SDD § 4 SEC-3's policy loads "only from the tracker's own address",
  and that does not stop framing: MDN on `frame-ancestors`, "A policy that declares `default-src
  'none'` still allows the resource to be embedded by anyone"
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).
  The owner confirmed it with an addition (`trail/architecture/cycle-1.md` § 2.2; reasoning,
  `trail/architecture/self_answer-1.md` § 2.2): the policy travels as a response header, because the
  directive "is not supported in the `<meta>` element" (the same MDN page), so a policy written as a
  tag would carry it and do nothing. SDD § 4 SEC-3 states both at version 4 (SDD RN-28), and QC-34's
  check reads the policy from the same header. *(re: QC-33, QC-34; source: SRS NFR-4; SDD § 4 SEC-3)*
- **RN-5:** QC-16 forbids `web` importing `domain`, and QC-5 places the refusal types in `domain/`,
  handed to `web` by `application` — *because* the owner overrode version 1's placement and kept its
  import rule (`trail/architecture/cycle-1.md` § 2.3; reasoning, `trail/architecture/self_answer-1.md`
  § 2.3). The import half rests on SDD § 3's direction of dependence, which lists `web` importing
  `application` and no other part, and on § 4 RT-10's "through `application`". Version 1 put the
  refusal types in `errors.py`, on the units line's "No part owns more of that file than its own
  subclasses". Two clearer SDD sentences put them in `domain/`: the `domain` row ("It holds … one
  typed refusal per refused condition") and the units line's "every typed error in every part derives
  from" the base in `errors.py`. `application` owns `SM-1`, whose outward side carries "a typed
  refusal", so naming `domain`'s types for `web` is that seam's work and no rule, and QC-21's "owns no
  rule of its own" holds. Every SDD sentence stays true on this reading, so no SDD item is raised.
  *(re: QC-5, QC-16; source: SDD § 3, `SM-1`; § 4 RT-10, OB-4)*
- **RN-6:** § 9 places SDD TS-1's in-process tests at doctrine layers 3 and 4, and records layers 6 and
  7 as QA-owned with what verifies them instead — *because* the doctrine's door rule puts a test that
  enters inside the listener at layer 3, and `testing_doctrine.md` refuses a product with a UI the
  layer-4 exemption. No upstream document maps the SDD's three layers onto the seven. The owner
  confirmed the mapping with two additions (`trail/architecture/cycle-1.md` § 2.4; reasoning,
  `trail/architecture/self_answer-1.md` § 2.4). The layer-1 row also takes QC-30's address check,
  which version 1's row scoped out while QC-30 named layer 1. Every layer-6 walk fails when it finds no
  module in the directory it walks, *because* a walk rooted at the wrong directory would otherwise
  report a clean tree it never read; § 1.2's preamble carries the same rule for the import walk.
  *(re: § 9, § 1.2, QC-30; source: SDD § 4 TS-1; `<CORE>/doctrine/engineering/testing_doctrine.md`)*
- **RN-7:** QC-38 realizes the quality floor "validated at the boundary it enters through, before it
  reaches domain logic" as "checked by a `domain` rule before any state changes" — *because* this SDD
  gives every rule to `domain` and forbids `web` owning one (SDD § 3), and a floor never overrides an
  upstream sentence (`<CORE>/doctrine/engineering/quality_defaults.md`, "A floor never overrides an
  upstream sentence"). The request check of QC-31 and QC-32 is the boundary's own part. *(re: QC-38)*
- **RN-8:** QC-35 turns SDD § 4 SEC-3's "No part opens an outbound connection" from a statement into
  a test, through Python's audit hook on `socket.connect` — *because* the quality floor on egress
  names a test asserting the connection set of a full run, and the owner's AC-11 run-through cannot be
  repeated on every change. *(re: QC-35; source: `quality_defaults.md` § The boundary set)*
- **RN-9:** QC-37's ban on `pickle`, `marshal`, `shelve`, `eval` and `exec` is a doctrine floor
  applied, not an SDD sentence — *because* the saved data is the one input the tracker did not just
  write (SRS DR-6), and the floor treats outside content as data. The SDD leaves the file's format to
  `persistence`; this entry leaves it there too and forbids only readers that execute what they read.
  *(re: QC-37; source: `quality_defaults.md` § Outside content)*
- **RN-10:** QC-40 and QC-41 apply the dependency and secrets floors with their harness named as
  missing — *because* the floors bind every product, and the Python packet's quality gates name no
  audit command and no scanner (`<CORE>/doctrine/engineering/languages/python/quality_gates.md`
  § What is not installed). Installing either is a toolchain decision this document does not make.
  The remediation window the dependency floor asks for is a value no upstream document states, so it
  went to the owner as companion § 1.1. The floor is a doctrine default this document realizes with the
  product's own measure, so the owner's answer landed in QC-40 itself, with no SRS round first (RN-18). Version 1 of
  that item routed it through SRS § 4.3 (`trail/architecture/cycle-1.md` § 1.1), and the report at
  `trail/architecture/self_answer-1.md`, *Left for the owner*, showed why that routing does not hold.
  *(re: QC-40, QC-41; source: `quality_defaults.md` § Dependencies)*
- **RN-11:** QC-46 adds a test to SRS AC-17's inspection — *because* the set of fields SRS DR-1 to
  DR-5 describe is closed, so a test can fail on an extra key after AC-6's sequence and catch a
  change that adds one without a review. *(re: QC-46; source: SRS NFR-6, AC-17)*
- **RN-12:** Six upstream items land here as no entry, each for its reason. SRS NFR-12, NFR-13 and
  NFR-14 and SDD § 4 EX-1 to EX-14 are experience and behaviour, which the FDR (R-113, R-114, PD-9)
  and the UXD hold. SDD § 4 TS-1's test-first rule is a property of the build, held by § 9 and the
  suite gates. SDD § 9 TO-6's fixed address is behaviour (FDR PD-10). SRS C-1, C-3 and C-4 are
  properties of what is shipped (FDR PD-1, PD-2, PD-4). The setup instructions' content is behaviour
  (FDR R-8 to R-14). *(re: §§ 1–8)*
- **RN-13:** Five decisions in the SDD earn no record — *because* each fails a gate. SDD § 9 TO-6, the
  fixed address, costs "one argument read in `main`" to undo, so it is not hard to reverse. The request
  check and page policy of SDD § 4 SEC-2 and SEC-3 live in one function each in `web`, so they are not
  hard to reverse either; QC-31 to QC-34 bind them. The trace mechanism of TS-3 and TS-4 has no
  neglected option argued anywhere (SDD RN-9 argues the need, not an alternative), so it fails the
  trade-off gate; QC-11 binds it. The single error base and typed refusals are a doctrine default and
  surprise no one; QC-4 and QC-5 bind them. RT-4's `venv` was forced by the owner's machine, not
  chosen. *(re: `adr/`)*
- **RN-14:** QC-61 and QC-28 make two SDD sentences checkable — RT-3's "The tracker itself checks no
  operating system" and TS-2's "never patches a name inside it" — *because* each is an absolute a
  layer-6 walk can prove over every module, where a behaviour test proves only the paths it walked.
  *(re: QC-28, QC-61; source: SDD § 4 RT-3, TS-2)*
- **RN-15:** One SDD Open Question bears on these records, and it bears on ADR-0003. It does not
  settle here: it settles in a run by the owner. ADR-0003's `## Traces to` cites the list's second
  item, the question of assistive-technology speech, which is now the list's only item. What is
  verified, in Chromium: `autofocus` focuses and brings into view a form control (SDD RN-36), and an element that
  is not a control, made focusable with `tabindex="-1"`, in two places. The first is the added name
  on the People page (`tests/e2e/test_people.py`,
  `test_added_markup_name_has_browser_focus_and_accessible_description` and
  `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action`): both passed at `641bb58b5`
  (`pytest products/tracker17/tests/e2e/`, 18 passed), with playwright 1.63.0 and Chromium
  153.0.8010.12 (SDD § 11 R-2, RN-41). The second is the added comment, given `tabindex="-1"
  autofocus` at `web/pages.py:L948` (`tests/e2e/test_comments.py:L89`,
  `test_keyboard_comment_add_brings_the_new_comment_into_view_and_focus`, and `:L171`,
  `test_keyboard_comment_refusals_keep_text_focus_and_description`): the same command gave 33 passed
  at `4f6f59752` with playwright 1.63.0, and 33 passed at `c0e4d65f4`, whose product code and tests
  match `4f6f59752`, with playwright 1.63.0 and Chromium 153.0.8010.12. The confirmation of SDD § 4
  EX-6 is verified too, in its three parts: the sentence alone holding focus, the double press that
  never confirms, and back-out returning focus. SDD § 11 R-2 names the four tests in
  `tests/e2e/test_moves.py` that verify them (`test_keyboard_opening_focuses_the_visible_sentence`,
  `test_keyboard_confirming_and_back_out_use_their_own_intents`,
  `test_double_click_never_confirms_at_the_original_trigger_coordinates` and
  `test_keyboard_opening_on_a_far_row_focuses_the_visible_sentence`): all four passed in a fresh
  clone at `9b05680c7` (`tests/e2e/`, 67 passed), with the pinned library, `playwright==1.63.0`. That
  run asserts the browser build rather than inferring it from the pin: its
  `test_history_matrix_revalidates_current_saved_status` asserts `153.0.8010.12` on the full Chromium
  of that install, and the four focus tests drive the headless shell the same install provides.
  Each result is a count at the commit it names, not a claim about the tree after it; `git diff
  <commit>` shows what has moved since. What stays open is one case: assistive technology speaking
  the description SDD § 4 EX-14 needs. None of ADR-0003's three focus tests reaches it,
  because a computed accessible description does not prove the line is spoken. One VoiceOver pass on
  the owner's macOS machine settles it, and no slice requires that run. The passing tests stay as
  regression triggers, because a Chromium release could change the behaviour. If any focus test
  fails, ADR-0003's own fallback applies, and it lands as a record superseding ADR-0003. Two
  questions this note counted at SDD version 4 are closed at version 6. The line break against
  `maxlength` (ADR-0007) closed in SDD RN-36: Chromium counted each line break as one, and what it
  sends no longer matters, because `web` turns CR LF and a lone CR into LF before the value reaches
  `application`, which is what ADR-0007 decided. The port closed in SDD RN-35, with the address
  `127.0.0.1:8017` (SDD § 4 RT-5), whose host QC-30 checks. The EX-6 confirmation, which this note
  counted open through NFDR version 14, closed at SDD version 11 (§ 11 R-2). ADR-0007's *Dependence*
  calls the line-break question open as the list's first item. The list's first item is now the
  assistive-technology question and names no RN-36; SDD RN-36 itself records the line-break question
  closing. ADR-0003's *Dependence* calls the not-a-control case unverified and cites
  SDD § 11 R-2 and its Open Questions, which SDD version 8 narrowed (SDD RN-41), so the citation lands
  on the current state. Both records are Accepted and stay as written, because neither decision
  moved and each was true on its date. A reader reaches this note from either record through its
  `## Binds` line — ADR-0003 binds QC-34 and ADR-0007 binds QC-9, and both entries' trace tags name
  RN-15. An answer that contradicts a record lands as a superseding record. *(re: ADR-0003,
  ADR-0007, QC-9, QC-30, QC-34; source: SDD § Open Questions, § 4 RT-5, EX-6, EX-14, § 11 R-2, RN-35,
  RN-36, RN-41; owner, `trail/architecture/cycle-4.md` § 2.1, `trail/architecture/cycle-8.md` § 3.1,
  `trail/architecture/cycle-11.md` § 3.1, `trail/architecture/cycle-13.md` § 2.2; see RN-23, RN-35,
  RN-42, RN-46)*
- **RN-16:** § 3 names what the loopback boundary leaves open — *because* the owner confirmed the
  not-applicable declaration with that addition (`trail/architecture/cycle-1.md` § 2.5; reasoning,
  `trail/architecture/self_answer-1.md` § 2.5). Version 1 said "the only caller is someone already at
  the operator's machine", which is true and reads as "only the operator". The addition decides no new
  risk: no login (SDD § 4 SEC-1; SRS C-2) and one machine (SRS C-1) already accept it, and § 3 now
  says so in words. *(re: § 3; source: SDD § 4 SEC-1, SEC-2; SRS C-1, NFR-7)*
- **RN-17:** Version 2 was written on 2026-10-07. It read the answered companion, copied whole to
  `trail/architecture/cycle-1.md` before the fold, and its reasoning at
  `trail/architecture/self_answer-1.md`. It read SDD version 4's change in full — § 4 SEC-2, SEC-3,
  § 12 and RN-28 to RN-30 — and re-read SDD §§ 1 to 4 and SRS § 4.3 and AC-10, against which the
  answers were folded. The SRS and the FDR are unchanged since version 1. SDD § 12 now states that
  where a § 4 condition and an entry here disagree, § 4 wins; QC-32, QC-33 and QC-34 now say what
  SEC-2 and SEC-3 say, so no entry disagrees. No record in `adr/` moved: every answer landed in this
  document, and RN-13's reason for giving the request check and page policy no record still holds at
  version 4, which keeps each in one function in `web`. *(re: Version 2)*
- **RN-18:** QC-40 states a 30-day remediation window, the owner as the one who watches, and a feed
  for the packages and one for the browser — *because* the owner confirmed the recommendation in
  `trail/architecture/self_answer-3.md` § *Left for the owner* (`trail/architecture/cycle-2.md` § 1.1),
  and with one operator (SRS NFR-7) the watcher can only be the owner. The browser has its own feed
  because the pinned library fetches it at setup and no manifest or lock file names it (SDD § 4 RT-4),
  so GitHub's alerts cannot see it. The package feed rests on a platform fact this product does not
  hold: GitHub's dependency graph reads pip's `requirements.txt` and Poetry's `poetry.lock`, among
  others
  (https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/dependency-graph-supported-package-ecosystems).
  QC-39 leaves the lock file's format unchosen, and choosing it stays the toolchain decision RN-10
  names; QC-40 states only the condition, and makes the change that chooses the format a review
  moment. The answer names a second moment, every `development-design` review, *because* QC-40's
  first gate runs only when a change touches a dependency, and an advisory against an untouched pin
  would otherwise reach nobody. The window was set while tracker17 is unpublished and only the owner
  installs its test dependencies (PRD § Assumptions); publishing is the moment to look at the number
  again. *(re: QC-40; source: owner, `trail/architecture/cycle-2.md` § 1.1;
  `quality_defaults.md` § Dependencies)*
- **RN-19:** QC-9 now covers the maximum the description field and the comment field state beside
  them — *because* UXD version 4 added those sentences and says "The number is the field's own
  maximum, taken from the same place that sets the field's limit, so the sentence and the field
  cannot disagree" (UXD UX-F2; UX-F7 on the same terms). SDD § 4 RT-10 already states the lengths
  once, in `domain`, and has `web` receive them through `application`; a sentence that types the
  number again would be a second statement QC-9's layer-6 check misses, because it looks for the
  number as a length and not inside text. The layer-4 test compares the sentence's number with the
  field's own `maxlength` on the same page, which is what the UXD asks for, and fails the day the two
  part. It does not tell a number formatted from the constant from the same number typed, and it
  needs not to: a typed number that still matches breaks nothing the operator sees, and the first
  change to a length makes it fail. No SDD sentence moves, so nothing is raised to the CTO.
  *(re: QC-9; source: UXD UX-F2, UX-F7, RN-29; SDD § 4 RT-10)*
- **RN-20:** Version 3 was written on 2026-10-07. It read the answered companion, copied whole to
  `trail/architecture/cycle-2.md` before the fold, and the reasoning behind its one answer at
  `trail/architecture/self_answer-3.md`. The SRS, the SDD and the FDR are unchanged since version 2.
  It read what changed in the UXD (version 4) and `DESIGN.md` (version 3) since then; RN-19 is the one
  entry that change moves. UX-F9's refusal of an assignee who left the list after the page loaded is a
  `domain` refusal that QC-5 and QC-38 already bind, and the rest is behaviour and experience (RN-12).
  No record in `adr/` moved. Nothing is left open, so the companion is removed and this document is
  Settled. *(re: Version 3)*
- **RN-21:** QC-11 holds the pointer test to the feature words whose slice has landed, and has it
  fail in both directions — *because* the owner confirmed the PM's correction and added the reverse
  (`trail/architecture/cycle-3.md` § 3.1; reasoning, `trail/architecture/self_answer-5.md` § 3.1),
  and SDD version 6 states TS-4 the same way (SDD RN-34), with SDD § 12 having § 4 win where it and
  an entry here disagree. Version 3's tail failed on every feature word with no module, which no
  slice before the last can pass: TS-3's table names eleven words and `domain/` holds one entry
  module, `projects.py`. One change beyond the answer: the obligation's first sentence is held to the
  landed words too, where it read "Each Core Feature … has its entry module" — *because* an obligation
  no build before the last can meet, verified by a check that can, leaves the entry and its tail
  disagreeing. The reverse check is in `tests/architecture/test_trace.py`, beside the list of landed
  words, `LANDED_FEATURE_WORDS`, and the entry's tail names it. *(re: QC-11; source: owner,
  `trail/architecture/cycle-3.md` § 3.1, `trail/architecture/cycle-5.md` § 3.1; SDD § 4 TS-4,
  RN-34)*
- **RN-22:** QC-62 makes Ruff's format check, Ruff's lint and mypy gates — *because* the owner
  answered the PM's question that way (`trail/architecture/cycle-3.md` § 3.2; reasoning,
  `trail/architecture/self_answer-5.md` § 3.2). The product installs and configures both tools
  (`pyproject.toml`, `[dependency-groups] dev`, `[tool.ruff]`, `[tool.mypy]`), QC-39 already pins
  them and QC-40 already watches their advisories, and `quality_gates.md` names Ruff and mypy as the
  house default for a product that installs them. The answer asked for a line in § 9 and three rows
  in § 10. The obligation is also an entry, QC-62, in § 8 beside the other toolchain entries —
  *because* § 10 is a projection, and a row with no entry is a defect this document's own bar
  forbids. It is no record, *because* dropping a gate is a one-line change and fails the
  hard-to-reverse gate, as the answer's reasoning says. QC-62 names QC-56's catch site as the
  standing exception: Ruff 0.16.10 reports `BLE001` at `web/routes.py:194`, the `except Exception`
  QC-56 requires, and a bare gate would reward breaking a settled entry. *(re: QC-62, § 9, § 10;
  source: owner, `trail/architecture/cycle-3.md` § 3.2; `quality_gates.md` § What a product
  installs, when it installs one)*
- **RN-23:** RN-15 names the one SDD open question left and where the other two closed — *because*
  SDD version 6 closed two of the three questions RN-15 counted at version 4 (SDD RN-35, RN-36). The
  `companion-self-answer` run raised it (`trail/architecture/self_answer-5.md` § *Raised on this
  document*), and the owner confirmed it with an addition (`trail/architecture/cycle-4.md` § 2.1;
  reasoning, `trail/architecture/self_answer-6.md` § 2.1). Neither ADR-0003 nor ADR-0007 is edited
  or superseded, *because* both are Accepted, neither decision moved, and the SDD answers both
  citations itself: ADR-0003's cited item is the list's only one, and SDD RN-36, which that item
  names, records ADR-0007's closed question. Version 4 said RN-15 was where a reader following
  either citation finds the answer; that did not hold, because each citation leads into SDD § Open
  Questions and nothing on that path names RN-15. The one route from either record into this
  document is its `## Binds` line, so QC-9's and QC-34's trace tags now name RN-15. `Inputs read:`
  names SDD version 6, because it records what this revision read. *(re: RN-15, QC-9, QC-34, Inputs
  read; source: owner, `trail/architecture/cycle-4.md` § 2.1; SDD § Open Questions, RN-35, RN-36)*
- **RN-24:** Version 4 was written on 2026-10-07. It read the answered companion, copied whole to
  `trail/architecture/cycle-3.md` before the fold, and the reasoning behind its answers at
  `trail/architecture/self_answer-5.md`. It read SDD version 6's whole change since version 4
  (`git diff facf92e37 HEAD -- products/tracker17/docs/SDD.md`): § 4 RT-5, RT-7, RT-10, TS-4,
  § 10 RC-2, § 11 R-6, R-11, RN-31 to RN-37 and § Open Questions. RT-7's form carrying the values the
  page showed moves no entry: QC-8 has `web` keep nothing between requests, and a value carried in the
  form is not kept by `web`. RT-10's stated maximums are already QC-9's (RN-19). RT-5's address moves
  none: QC-30 checks the host is loopback whatever the port. The SRS, the FDR, the UXD, `DESIGN.md`,
  the Agari and the project's doctrine are unchanged since version 3; `CONTENT.md` is at version 5
  and was read for its header only, as RN-1 says. It ran QC-62's three commands on a copy of the
  product at `HEAD`, never on the main checkout, and found what the owner's answer measured: the
  format check clean, 8 Ruff findings, 3 mypy errors. § 8's and § 10's sentences that quoted the
  project card's `Test command:` as `pytest tests/` now point at the card, *because* the card's value
  is now `pytest products/tracker17/tests/`, typed from the change worktree's root
  (`system/projects/tracker17/project.md`, `Test command:`); typed from the product root it is still
  `pytest tests/`. No record in `adr/` moved. One choice is left for the owner, companion § 2.1, so
  this document is Draft. *(re: Version 4)*
- **RN-25:** Version 5 was written on 2026-10-07. It read the answered companion, copied whole to
  `trail/architecture/cycle-4.md` before the fold, and the reasoning behind its one answer at
  `trail/architecture/self_answer-6.md`. It checked the answer's facts at their source: SDD § Open
  Questions holds the one `autofocus` item, which names RN-36; SDD RN-36 records the line-break
  question closing; ADR-0003's `## Traces to` cites "the second item" and its `## Binds` names QC-34;
  ADR-0007's *Dependence* cites "the first item" and its `## Binds` names QC-9. The fold changed the
  reasons in RN-15 and RN-23 and the trace tags of QC-9 and QC-34. It changed no obligation, no
  `verified by:` tail and no § 10 row. No upstream document has changed since version 4, and no
  record in `adr/` moved. Nothing is left open, so the companion is removed and this document is
  Settled. *(re: Version 5)*
- **RN-26:** Version 6 was written on 2026-10-07. It read the answered companion, copied whole to
  `trail/architecture/cycle-5.md` before the fold, and the reasoning behind its one answer at
  `trail/architecture/self_answer-7.md`. The answer confirmed the PM's correction: QC-11's tail and
  RN-21 said the pointer test lacked its reverse check, and `tests/architecture/test_trace.py` holds it
  (`:223-226`), reads TS-3's words from `docs/SDD.md` (`:21`, `:65-84`), fails on reading none
  (`:225`), and shows it can fail (`:229-236`). This run checked each locator at `HEAD` and ran the
  file on a copy of the product, never on the main checkout: 18 passed. The fold rewrote QC-11's tail
  and RN-21's last sentence. It changed no obligation and no § 10 row: QC-11's row already names
  `pytest tests/`. The tail now names the check by its test name rather than stating the code's state
  on a date, *because* the clause that went false was the dated one (owner's addition). The SRS, the
  SDD, the FDR, the UXD, `DESIGN.md`, the Agari and the project's doctrine are unchanged since
  version 5. `CONTENT.md` moved from version 5 to version 7 (not-found wording, the terminal
  examples' address, accessible names of links). It was read for its header and that change only,
  as RN-1 says, and moves no entry. No record in `adr/` moved. Nothing is left open, so the companion
  is removed and this document is Settled. *(re: Version 6; QC-11)*
- **RN-27:** B-4 now covers the system libraries the end-to-end browser needs on Linux, and § 9 states
  the end-to-end layer's Linux bound — *because* SDD version 7's § 4 RT-4 has the Linux setup step
  run `python -m playwright install --with-deps chromium`, which installs those libraries through the
  distribution's package manager and asks for administrator rights, and limits the end-to-end suite on
  Linux to the systems the pinned library lists; § 4 RT-3 says the tracker runs on any Linux with
  Python 3.11 or later (SDD RN-38). That widens what B-4's "setup" crosses, which
  `trail/architecture/self_answer-8.md` § 2.1, *Considered and not raised*, named and left to this
  run. No entry is added. The libraries are outside QC-39 and QC-40 *because* the SDD settles them as
  the operating system's, "as Python is", and "not declared dependencies under C-8, so nothing pins
  them"; recording that faithfully is this document's part, and a reader who wants them watched has
  an SDD sentence to move first, not an entry here. The administrator rights bind no § 3 entry
  *because* they are confined to the one-time setup of the end-to-end suite, which is behaviour of the
  setup instructions (RN-12), and the SDD says the tracker and `pytest tests/` need none of it; at run
  time QC-42 and QC-43 already hold each part to its reach. § 9's layer-5 bullet carries the bound
  where a delivery session choosing which suite to run will look. *(re: § 2 B-4, § 9; source: SDD
  § 4 RT-3, RT-4, RN-38; SRS C-8, FR-4)*
- **RN-28:** QC-47's tail names the test that carries its check in the suite, and the Git repository
  both need — *because* SDD version 7's § 6 `first-project` *Artifact* makes a Git repository with
  `git` on the path a prerequisite of the full suite, and has the one test that checks it fail outside
  one rather than skip (SDD RN-39). A cold reader running the suite in a copy that is not a
  repository — one unpacked from a download, the README's case, or from `git archive` — meets that
  one failure, and without this sentence would read it as `data/` no longer ignored. The copy
  `<CORE>/roles/CROSS_ROLE.md` § *Every seat* sends a run outside the change's worktree to is a fresh
  clone at the commit under test, which is a repository, so that run does not meet it (RN-40). The
  obligation does not move. § 10's QC-47 row names the test beside the command, *because* the row is
  the entry's projection. *(re: QC-47, § 10; source: SDD § 6 `first-project`, RN-39; SRS FR-6;
  owner, `trail/architecture/cycle-10.md` § 3.2)*
- **RN-29:** `products/tracker17/docs/adr/0009-one-unix-lock-no-windows.md` stays as written, and no
  record supersedes it — *because* SDD RN-38 left its *Consequences* line "Linux is named as supported
  and nothing checks it (SDD § 11 R-9)" to this seat to re-read against R-9 as narrowed, and the
  decision has not moved: macOS and Linux, one locking path, no Windows, only macOS checked. The
  Debian 12 run SDD R-9 now records was one run outside the Agari's check, and no standing check
  reaches Linux, so "nothing checks it" still holds. The record's "Setup instructions have one set of
  prerequisites" reads thinner for the end-to-end suite on Linux, which now has its own install
  command and a narrower list (RN-27), and holds for the tracker's own setup, which is what the
  decision bought. A record is append-only: a consequence that a later fact refines is recorded here,
  and only a decision that moves earns a superseding record. ADR-0009's `## Binds` names QC-61, whose
  trace tag now names this note, so a reader of the record reaches the narrowing. No other SDD
  version 7 change earns a record: the Linux install command, the suite's Linux list and the Git
  prerequisite are each a sentence in the setup instructions, cheap to reverse, and fail the
  hard-to-reverse gate. *(re: ADR-0009, QC-61, `adr/`; source: SDD § 4 RT-3, RT-4, § 11 R-9, § 12,
  RN-38)*
- **RN-30:** Version 7 was written on 2026-10-08. It read SDD version 7's whole change since version
  6 (`git show 4156e81b2 -- products/tracker17/docs/SDD.md`): § 4 RT-3, RT-4, § 6 `first-project`
  *Artifact*, § 11 R-9 and RN-38 to RN-40, with `trail/sdd/cycle-4.md` behind them. RN-27 to RN-29
  are what it moves; it changed no obligation. The SRS, the FDR, the PRD, the UXD, `DESIGN.md`,
  `CONTENT.md`, the Agari and the project's doctrine are unchanged since version 6. It read the
  companion as it stands at `7d6c3feee` and `trail/architecture/self_answer-8.md`. The companion holds
  two items with no answer slot filled — § 2.1, the reading of QC-40's first sentence, and § 3.1, the
  owner's call on a dated exception for the browser build — so it was not consumed, no trail cycle was
  written, and neither item is folded here: QC-40 stands as version 6 wrote it. Version 6 was Settled
  when written; the PM opened the companion after it, so this document is Draft while the companion
  exists. No record in `adr/` moved. *(re: Version 7)*
- **RN-31:** QC-40's first sentence now binds the moment a change chooses a version, and its second
  binds the time after an advisory lands — *because* the owner confirmed the draft in companion § 2.1
  with two additions (`trail/architecture/cycle-6.md` § 2.1; reasoning at
  `trail/architecture/self_answer-9.md` § 2.1). Read literally, version 7's first sentence barred
  every pinned dependency from the setup instructions on the day an advisory was published against
  it, which left the 30-day window and the dated exception nothing to apply to, and contradicted the
  answer that gave the window to the browser build by name (`trail/architecture/cycle-2.md` § 1.1).
  The same two bullets sit in the floor QC-40 realizes (`quality_defaults.md` § Dependencies: a
  critical vulnerability "blocks release", and it "has a stated remediation window"), and they hold
  together only under this reading. An advisory published against a pin already chosen is the second
  sentence's, and its window runs from the day the advisory is published. The owner's first addition
  fixes what "exists" means: a version published on the index the pin installs from. For this
  product that is PyPI, for the packages, and for the browser it is a release of the browser-driving
  library on PyPI whose browser build is free of the advisory; a release elsewhere does not count.
  The case that made it live: Playwright 1.64.0 shipped on npm on 2026-10-07 and is not on PyPI (read
  2026-10-08), so no change to this product can choose it. The owner's second addition: a dependency
  whose every published version carries a critical advisory may be added, but the window has run
  since that advisory was published, not since the day of the change, so an advisory more than 30
  days old needs the owner's dated exception before the change lands. This run wrote "every version
  on that index" for the owner's "every published version", the reading the first addition fixes for
  the same entry. It also added to the tail's first moment what that review checks: the version chosen
  against advisories and against the index. That is the check the first sentence now names, and the
  tail did not say it. Under this reading the setup instructions are not blocked by the first sentence:
  `playwright==1.63.0` was chosen on 2026-10-07, when no Playwright release on PyPI installed a fixed
  Chromium, and its browser build is held by the window. Whether the owner records a dated exception
  for that build is companion § 3.1, still open, and this revision records none. No record in `adr/`
  moves: the reading settles how an entry binds, it is cheap to revise in place, and it earns no
  record. *(re: QC-40; source: owner, `trail/architecture/cycle-6.md` § 2.1)*
- **RN-32:** Version 8 was written on 2026-10-08. It read the answered companion as committed at
  `96dcb86b7` and copied it whole to `trail/architecture/cycle-6.md` before the fold. Of its two
  items, § 2.1 was answered and is folded here (RN-31). § 3.1, the owner's call on a dated exception
  for the browser build `playwright==1.63.0` installs, has no answer, so it stays in the companion
  and this document stays Draft. The SRS, the SDD, the FDR, the PRD, the UXD, `DESIGN.md`,
  `CONTENT.md`, the Agari and the project's doctrine are unchanged since version 7
  (`git log 332311003..96dcb86b7` touches only the companion). The one obligation that moves is
  QC-40's. QC-40 is a review gate, so § 10 gains no row. No record in `adr/` moved. *(re: Version 8;
  QC-40)*
- **RN-33:** **Dated exception to QC-40, recorded by the owner: 2026-10-10 to 2026-11-07.** The
  Chromium build `playwright==1.63.0` installs, `153.0.8010.12`, stays past QC-40's 30-day window for
  the critical advisories against it, until the end of 2026-11-07. The owner's reason: no newer
  Playwright exists on PyPI, so the pin cannot move, and the browser drives only tracker17's own
  local pages in tests. Ending it is the owner's, by moving the pin or renewing the exception with a
  reason, and is tracked as a row in the instance's upkeep register, `system/upkeep.md`. At a
  `development-design` review on or before 2026-11-07, that build does not block the change. After
  that date, with neither done, QC-40 blocks every review again. The exception names the build, not
  the advisories, so it covers that build only: a moved pin installs another build, which QC-40
  checks afresh. This run checked the reason's first fact at its source: PyPI's newest Playwright is
  still 1.63.0, uploaded 2026-09-15 (`https://pypi.org/pypi/playwright/json`, read 2026-10-10), and
  `tests/requirements.txt:12` pins it. *(re: QC-40; source: owner, `trail/architecture/cycle-7.md`
  § 3.1)*
- **RN-34:** Version 9 was written on 2026-10-10. It read the answered companion as committed at
  `1aa6a4a8e` and copied it whole to `trail/architecture/cycle-7.md` before the fold, with the
  reasoning behind the item at `trail/architecture/self_answer-10.md` and `self_answer-11.md`. Its one
  item, § 3.1, was answered and is folded here as RN-33. The SRS, the SDD, the FDR, the PRD, the UXD,
  `DESIGN.md`, `CONTENT.md`, the Agari and the project's doctrine are unchanged since version 8
  (`git diff --stat 1f536001f..HEAD` over the product's `docs/` and the project folder touches only
  the companion, those two reports, `what_left.md` and one journey report). This run read
  `what_left.md` in full: it lists features the code does not yet have, and moves no entry. No
  obligation's text moves. QC-40's trace tag now names the exception. QC-40 is a review gate, so § 10
  gains no row. No record in `adr/` moves: an exception with an end date is cheap to reverse and fails
  the hard-to-reverse gate. Nothing is left open, so the companion is removed and this document is
  Settled. *(re: Version 9; QC-40)*
- **RN-35:** RN-15 says which of ADR-0003's focus cases are verified and which two stay open, and
  ADR-0003 is neither edited nor superseded — *because* the owner overrode where the PM's item put
  the change (`trail/architecture/cycle-8.md` § 3.1; reasoning,
  `trail/architecture/self_answer-12.md` § 3.1). The item asked for ADR-0003's *Dependence* to be
  narrowed. That edits an Accepted record, and a superseding record is for a decision that moved,
  which this one did not (SDD RN-41). The sentence that went false was RN-15's: it still called the
  not-a-control case open, and called ADR-0003's cited second item the list's only one, where SDD
  version 8's list has two. The answer kept the narrowing and the no-script decision, and set the
  four things RN-15 now says. This run checked them at their source: SDD § 11 R-2 and § Open
  Questions at version 8; `tests/e2e/test_people.py:L58-L78`, the assertion helper and the test that
  calls it, and `:L90`, the removal test; `web/pages.py:L316` and `:L404`, the `tabindex="-1"
  autofocus` attributes on the added name and the heading; and `tests/requirements.txt:L12`,
  `playwright==1.63.0`. `git diff --stat 641bb58b5 HEAD -- products/tracker17
  ':!products/tracker17/docs' ':!products/tracker17/README.md'` printed nothing, so the recorded
  pass ran against the code on `main` now. This run ran no suite. RN-15 keeps its ADR-0007 and port
  sentences, *because* QC-9's trace tag still sends a reader of ADR-0007 there (RN-23); it now says
  the list's first item names SDD RN-36, where version 9 said the only item did. *(re: RN-15,
  ADR-0003; source: owner, `trail/architecture/cycle-8.md` § 3.1; SDD § 11 R-2, § Open Questions,
  RN-41)*
- **RN-36:** Version 10 was written on 2026-10-11. It read the answered companion as committed at
  `58ded3cc4` and copied it whole to `trail/architecture/cycle-8.md` before the fold, with the
  reasoning behind its one item at `trail/architecture/self_answer-12.md`. Its one item, § 3.1, was
  answered and is folded into RN-15 (RN-35). The upstream documents moved since version 9
  (`git diff --stat 24aa9ecd8 HEAD` over the product's `docs/` and the project folder). This run read
  each change: SRS versions 5 and 6, SDD version 8, FDR versions 3 and 4, PRD versions 5 and 6, and
  `CONTENT.md` version 8. None moves an entry. The fourth priority, `critical`, is behaviour (FDR
  R-51, R-90, PD-5), and no entry names the priority set. SRS FR-41 and AC-21, the README's opening
  paragraph, are setup-instruction content, which is behaviour (RN-12), and SRS RN-18 says the second
  purpose adds no behaviour and leaves NFR-5's no-telemetry rule as written, which QC-34 and QC-35
  already bind. FDR R-119 and R-120 carry SDD § 4 RT-3 and RT-4's Linux lines, which RN-27 already
  reads. SDD version 8 changes no part, seam or § 4 condition, and its R-2 narrowing is what RN-15
  now records. The rest of the change, `DESIGN.md`'s one line included, replaces machine paths with
  the predecessor's repository name. One of those edits reached `adr/`: commit `878d25dac` changed
  one path in `products/tracker17/docs/adr/0004-whole-state-saved-atomically-on-every-change.md`
  § Context and changed no decision. That is an in-place edit to an Accepted record that no
  producing run made. This run leaves it as it stands, because undoing it would put a machine path
  back. The UXD, the Agari and the project's doctrine are unchanged since version 9. No obligation's
  text, no trace tag and no § 10 row moves, and no record in `adr/` moves. Nothing is left open, so
  the companion is removed and this document is Settled. *(re: Version 10; RN-15)*
- **RN-37:** QC-21 saves only an action whose `domain` outcome reports a change, where version 10 had
  every action save — *because* the owner confirmed the PM's correction with three additions
  (`trail/architecture/cycle-9.md` § 3.1; reasoning, `trail/architecture/self_answer-13.md` § 3.1),
  and SDD version 9's § 3 `application` row now reads the same way (SDD RN-45). The product had
  already moved: `application/tracker.py:L105-L114`, `Tracker.edit_task`, saves and publishes only
  `if outcome.changed`. The first addition is the bound on what the report compares, submitted
  against shown, never the new state against the current one, *because* without it a reader would
  "fix" QC-21 with a state comparison, which is a rule its no-rule half forbids `application`. The
  second is the new half's teeth: `tests/integration/test_task_tracker.py:L311-L322`,
  `test_tracker_unchanged_edit_never_saves`, asserts `saver.saved == []` after an unchanged edit, so
  the tail names it and § 10's row gains layer 3; it is layer 3 on the terms QC-54's
  recording-saver test is. The third is ADR-0001. Its § Decision `application/` bullet still says
  each action "saves the result, and only then makes it current" (`adr/0001-rule-core-behind-server-rendered-pages.md:L26-L28`).
  That bullet is the 2026-10-06 statement; QC-21, which ADR-0001's `## Binds` lists, is the current
  one. The record is neither edited nor superseded, *because* it is Accepted and the qualification
  fails the significance test: no part, edge or trade-off of a rule core behind server-rendered pages
  moves. ADR-0004's "on every change" (`adr/0004-whole-state-saved-atomically-on-every-change.md:L18`)
  stays true as written, and so do QC-49, QC-53 and QC-54: an action that reports no change reports
  nothing done, the lock still covers the whole request, and the saver still receives only saves.
  *(re: QC-21, § 10, ADR-0001; source: owner, `trail/architecture/cycle-9.md` § 3.1; SDD § 3
  `application` row, § 4 RT-7, RN-45)*
- **RN-38:** Version 11 was written on 2026-10-12. It read the answered companion as committed at
  `1ae214355` and copied it whole to `trail/architecture/cycle-9.md` before the fold, with the
  reasoning behind its one item at `trail/architecture/self_answer-13.md`. The PM opened that
  companion; no producing run wrote it. Its one item, § 3.1, was answered and is folded into QC-21
  (RN-37). The upstream documents moved since version 10 (`git diff --stat ceac03d4b HEAD` over the
  product's `docs/` and the project's `agari.md`, `doctrine/` and `project.md`). This run read each
  change: SDD version 9, whose one change is the § 3 `application` row and RN-45 and RN-46 behind it,
  and `CONTENT.md` version 9, whose one change is the date rule barring a refusal from naming how a
  date is entered. The SDD change is what QC-21 now says. The `CONTENT.md` change is wording, which
  is behaviour and experience (RN-12), and moves no entry. `what_left.md` lost the lines for features
  since built and moves no entry. The SRS, the FDR, the PRD, the UXD, `DESIGN.md`, the Agari and the
  project's doctrine are unchanged since version 10. This run checked the answer's locators at
  `HEAD` and ran no suite. One obligation's text moves, QC-21's, and its § 10 row with it. No record
  in `adr/` moves. Nothing is left open, so the companion is removed and this document is Settled.
  *(re: Version 11; QC-21)*
- **RN-39:** QC-21 says what an action's report compares per action, where version 11 said every
  report compares the value submitted with the value the page showed — *because* the owner confirmed
  the PM's correction with additions (`trail/architecture/cycle-10.md` § 3.1; reasoning,
  `trail/architecture/self_answer-14.md` § 3.1), and SDD version 10's § 3 `application` row now
  reads the same way (SDD RN-47, `trail/sdd/cycle-7.md` § 5.1). The product had already moved:
  `domain/operator_name.py:L59-L62`, `set_operator_name`, compares the checked name with
  `state.operator_name`, and `domain/tasks.py`, `add_task_label`, checks a label against the labels
  the task carries now. The PM's item named the operator name; the owner added the label, which
  makes the same comparison and SDD version 10 names, and had the rule written per action rather
  than as a list, so it stays true when another action starts reporting. The second addition is the
  new half's teeth: `tests/integration/test_people_routes.py:L520-L533`,
  `test_stale_people_name_submission_compares_with_current_name`, asserts the People form's only
  input is `name` and that a stale page's repeat of the saved name saves nothing, and
  `tests/unit/test_tasks.py:L727-L739`, `test_duplicate_task_label_reports_no_change`, asserts a
  repeated label returns the state as it came with `changed` false. The tail names both, and § 10's
  row gains layer 1 for the second. The task edit's rule, `application`'s no-comparison rule and the
  no-rule review stay as version 11 had them. ADR-0001 holds no page-showed sentence (no line in
  `adr/` names one) and is neither edited nor superseded; RN-37's reason for leaving its
  `application/` bullet as the 2026-10-06 statement still holds. *(re: QC-21, § 10, ADR-0001;
  source: owner, `trail/architecture/cycle-10.md` § 3.1; SDD § 3 `application` row, § 4 RT-7,
  RN-47; SRS NFR-3)*
- **RN-40:** QC-47 and RN-28 name the fresh clone at the commit under test as the copy a run outside
  the change's worktree uses, where version 11 named a copy unpacked from `git archive` — *because*
  the owner confirmed the PM's correction with one addition (`trail/architecture/cycle-10.md` § 3.2;
  reasoning, `trail/architecture/self_answer-14.md` § 3.2), and `core/roles/CROSS_ROLE.md:L14-L19`
  now reads "a fresh clone of the repository that holds it, checked out at the commit under test …
  A clone, not `git archive`". The PM measured the difference at `2866e76de`: `pytest
  products/tracker17/tests/` gave 1 failed, 936 passed in a `git archive` copy and 937 passed in a
  fresh clone (`trail/architecture/cycle-10.md` § 3.2). The addition is RN-28's *because*: its case,
  a cold reader running the suite where the contract sends a run, is gone, and the sentence now
  serves a copy that is not a repository, the README's "a copy unpacked from a download"
  (`products/tracker17/README.md:L109`) or one from `git archive`. The obligation, the Git
  prerequisite with `git` on the path, and the check failing rather than skipping do not move.
  § 10's QC-47 row, SDD RN-39 and SDD § 6 `first-project` stand as written. *(re: QC-47, RN-28;
  source: owner, `trail/architecture/cycle-10.md` § 3.2; SDD § 6 `first-project`, RN-39)*
- **RN-41:** Version 12 was written on 2026-10-12. It read the answered companion as committed at
  `4dbc7f570` and copied it whole to `trail/architecture/cycle-10.md` before the fold, with the
  reasoning behind both items at `trail/architecture/self_answer-14.md`. The PM opened that
  companion; no producing run wrote it. Its two items, §§ 3.1 and 3.2, were answered and are folded
  into QC-21 (RN-39) and into QC-47 and RN-28 (RN-40). The upstream documents moved since version 11
  (`git diff --stat df8ac27ea HEAD` over the product's `docs/`). This run read each change: SDD
  version 10, whose one change is the § 3 `application` row and RN-47 and RN-48 behind it; UXD
  versions 5 and 6, which open UX-S1 with tracker17's two purposes (UXD RN-31) and let UX-I3 name no
  action and offer no reload where the wanted state already holds and the page shows it (UXD RN-32);
  and `CONTENT.md` version 10, which gives a refusal one action where one exists. The SDD change is
  what QC-21 now says. The UXD and `CONTENT.md` changes are what the setup instructions and a refusal
  say, which is behaviour and experience (RN-12), and move no entry: no obligation names UX-S1's
  sections, UX-I3's reload or the refusal formula, and ADR-0003's whole-page answer holds for a
  refusal with no action as for one with an action. `what_left.md` lost the line for labels, since
  built, and moves no entry. The SRS, the FDR, the PRD, `DESIGN.md`, the Agari and the project's
  doctrine are unchanged since version 11. This run checked the answers' locators at `HEAD` and ran
  no suite. Two obligations' text moves, QC-21's and QC-47's, with QC-21's § 10 row and RN-28. No
  record in `adr/` moves. Nothing is left open, so the companion is removed and this document is
  Settled. *(re: Version 12; QC-21, QC-47, RN-28)*
- **RN-42:** RN-15 ties each focus-test result to the commit it was measured at and makes no claim
  about the tree after it, where version 12 said "no product code has moved since" `641bb58b5` —
  *because* the owner confirmed the PM's correction with one addition (`trail/architecture/cycle-11.md`
  § 3.1; reasoning, `trail/architecture/self_answer-15.md` § 3.1). The sentence had gone false:
  `git diff --stat 641bb58b5 4f6f59752 -- products/tracker17/web products/tracker17/domain` prints
  `12 files changed, 2350 insertions(+), 26 deletions(-)`, `domain/comments.py` among them. The
  addition is the rule behind the fix: a "since" sentence goes false at the next merge whatever date
  it names, and a result tied to its commit does not, so RN-15 now writes none. RN-15 also records the
  comment focus tests as a second element that is not a control — the added comment carries
  `tabindex="-1" autofocus` (`web/pages.py:L948`) — with their own verdict, 33 passed at `4f6f59752`
  (the PM's run) and at `c0e4d65f4` (the answer's own run, in a fresh clone per
  `<CORE>/roles/CROSS_ROLE.md` § *Every seat*). This run checked the locators at `HEAD`
  (`web/pages.py:L948`, `tests/e2e/test_comments.py:L89` and `:L171`, `tests/requirements.txt:L12`)
  and that `git diff --stat 4f6f59752 c0e4d65f4 -- products/tracker17 ':!products/tracker17/docs'`
  names only `README.md`; it ran no suite. The comment tests reach neither open case, so both stay:
  the EX-6 confirmation, which SDD § 6 `status-moves` settles, and assistive-technology speech for
  EX-14, which one VoiceOver pass settles. ADR-0003 is neither edited nor superseded, because its
  decision did not move and its *Dependence* was true on its date (RN-15's own rule). QC-34's
  obligation and trace tag do not move, and § 10 gains no row. *(re: RN-15, ADR-0003, QC-34; source:
  owner, `trail/architecture/cycle-11.md` § 3.1)*
- **RN-43:** Version 13 was written on 2026-10-13. It read the answered companion as committed at
  `c6f8b0f65` and copied it whole to `trail/architecture/cycle-11.md` before the fold, with the
  reasoning behind its one item at `trail/architecture/self_answer-15.md`. The PM opened that
  companion; no producing run wrote it. Its one item, § 3.1, was answered and is folded into RN-15
  (RN-42). Since version 12 (`git diff --stat 1e9f21d7e HEAD` over the product's `docs/` and the
  project's `agari.md`, `doctrine/` and `project.md`), two upstream files moved. This run read each
  change. PRD version 7 says tracker17 becomes public with kensaiapp's public release, which ships
  it as an example; that is a planning assumption, no entry or record names publication, and
  `Inputs read:` now names PRD version 7. `what_left.md` lost the line for comments, since built, and
  moves no entry. The SRS, the SDD, the FDR, the UXD, `DESIGN.md`, `CONTENT.md`, the Agari and the
  project's doctrine are unchanged since version 12. No obligation's text, no trace tag and no § 10
  row moves, and no record in `adr/` moves. Nothing is left open, so the companion is removed and
  this document is Settled. *(re: Version 13; RN-15)*
- **RN-44:** ADR-0010 records the history-admission boundary and QC-63 binds it — *because* the
  owner confirmed companion § 2.1 with three additions (`trail/architecture/cycle-12.md` § 2.1;
  reasoning, `trail/architecture/self_answer-16.md` § 2.1), and SDD version 11 settled the decision
  in § 4 RT-11, § 9 TO-8 and § 11 R-12 (SDD RN-49). The product has run on it since `9b05680c7`, and
  until this version no record and no obligation named the 202 or the header. The first addition is
  the reversal cost. SDD TO-8 puts undoing the 202 at one line in `web`, and RN-13 and RN-22 refused
  records to one-line decisions. This one passes the hard-to-reverse gate because the line is not
  the decision: nothing else is left to keep UXD UX-F4's no-press refusal on Back, so undoing it
  takes a page script, which supersedes ADR-0003, a cookie or session, which supersedes ADR-0006, or
  giving that refusal up. ADR-0010's § Consequences says so, and so does this note, so the record
  does not read as contradicting RN-13. ADR-0010's *Dependence* keeps SDD R-12's bound: the history
  tests prove the pinned build, not the operator's current stable Chrome. The second addition is the
  placement. QC-63 sits in § 1.1 beside QC-7 and QC-8, which also trace to ADR-0006, and not in § 2,
  whose entries each name the trust boundary they guard; this one guards none of B-1 to B-4. IDs are
  never renumbered, so it sits out of numeric order there. The third addition is two bounds RT-11
  states: the not-found page a confirmation address answers when its task is gone, 404 with no
  `no-store`, is outside the obligation, and the `Clear-Site-Data` clause covers a move's responses,
  which is what `test_move_responses_do_not_clear_site_data` reaches, so the tail names that test
  beside the five the draft listed. QC-63 traces to SRS NFR-13 for that bound, not as an obligation
  realized from it, so RN-12's reading of NFR-13 as experience stands. This run checked each locator
  at `HEAD`: `web/routes.py`, `Site._pending_status` (`HTTPStatus.ACCEPTED` only for a rendered
  confirmation), `Site._stored_as_asked` (`NOT_STORED` when the address carries `move_task`) and
  `Site._move_view`; the four layer-3 tests in `tests/integration/test_routes.py`, the 404 rows
  among them; the two layer-5 tests and `PINNED_BROWSER` in `tests/e2e/test_moves.py`. The recorded
  result is SDD RT-11's: 67 passed in `tests/e2e/` in a fresh clone at `9b05680c7`, a count at that
  commit. This run ran no suite. ADR-0003 and ADR-0006 are neither edited nor superseded: ADR-0010
  adds a decision inside both and moves neither. *(re: ADR-0010, QC-63, § 10; source: owner,
  `trail/architecture/cycle-12.md` § 2.1; SDD § 4 RT-11, § 9 TO-8, § 11 R-12, RN-49; SRS NFR-3,
  NFR-13; UXD UX-F4, UX-I3)*
- **RN-45:** Version 14 was written on 2026-10-21. It read the answered companion as committed at
  `d9fe641ff` and copied it whole to `trail/architecture/cycle-12.md` before the fold, with the
  reasoning behind both items at `trail/architecture/self_answer-16.md`. A `companion-self-answer`
  run opened that companion in the CTO's seat; no producing run wrote it. Of its two items, § 2.1
  was answered and is folded into ADR-0010 and QC-63 (RN-44). § 2.2, which asks for RN-15 to count
  the EX-6 confirmation verified as SDD version 11's § 11 R-2 does, has no answer, so it stays in the
  companion, RN-15 stands as version 13 wrote it, and this document is Draft. Since version 13
  (`git diff --stat 5e68bc569 HEAD` over the product's `docs/` and the project's `agari.md`,
  `doctrine/` and `project.md`), upstream moved. This run read each change. SDD version 11 adds
  RT-11, TO-8 and R-12, which RN-44 records, scopes RT-8's reload sentence to a page whose address
  names a finished outcome, which moves no entry because QC-7 binds only that a submission is
  answered by an address, and changes `status-moves`'s behaviour bar and EX-4 for UXD version 8
  (SDD RC-4, RN-50), which is behaviour. UXD versions 7 and 8, `DESIGN.md` version 4 and
  `CONTENT.md` versions 11 and 12 change what a refusal says and where it sits and the confirmation
  strip's height, which is behaviour and experience (RN-12), and move no entry. `what_left.md` lost
  the lines for the status workflow and the empty project, since built, and moves no entry. The SRS,
  the FDR, the PRD, the Agari and the project's doctrine are unchanged since version 13. *(re:
  Version 14; ADR-0010, QC-63)*
- **RN-46:** RN-15 counts the SDD § 4 EX-6 confirmation verified and one SDD Open Question left —
  *because* the owner confirmed companion § 2.2 with two additions (`trail/architecture/cycle-13.md`
  § 2.2; reasoning, `trail/architecture/self_answer-17.md` § 2.2), and SDD version 11 settled it:
  § 11 R-2 counts the confirmation case verified by four tests at `9b05680c7`, and § Open Questions
  keeps only the assistive-technology item. The first addition is the browser build. RN-15 states it
  as R-2 does: the run pinned `playwright==1.63.0`, and asserted `153.0.8010.12` on the full Chromium
  of that install through `test_history_matrix_revalidates_current_saved_status`, while the four
  focus tests drive the headless shell the same install provides. RN-15 claims no more about the
  build than the SDD does. The second addition is the list. With one item left, RN-15's count of
  questions, its sentence on ADR-0003's citation and its sentence on ADR-0007's citation each went
  false, and each now reads the list as it stands: ADR-0003's cited question is the list's only item,
  and ADR-0007's reader is pointed at SDD RN-36, which records the line-break question closing. This
  run checked the locators at `HEAD`: the four tests at `tests/e2e/test_moves.py:174`, `:208`, `:321`
  and `:606`, `PINNED_BROWSER` at `:452`, the `browser` and `history_browser` fixtures in
  `tests/e2e/conftest.py`, `playwright==1.63.0` in `pyproject.toml` and `tests/requirements.txt`, and
  that `git diff --stat 9b05680c7 HEAD -- products/tracker17 ':!products/tracker17/docs'` lists one
  line of `README.md` and no code. It ran no suite. RN-42 is a dated record and is not edited.
  ADR-0003 and ADR-0007 are neither edited nor superseded, because neither decision moved and each
  citation was true on its date (RN-15's own rule). QC-9's and QC-34's obligations and trace tags do
  not move, and § 10 gains no row. *(re: RN-15, ADR-0003, ADR-0007, QC-9, QC-34; source: owner,
  `trail/architecture/cycle-13.md` § 2.2; SDD § 11 R-2, § Open Questions, RN-36)*
- **RN-47:** Version 15 was written on 2026-10-21. It read the answered companion as committed at
  `b8fec1f86` and copied it whole to `trail/architecture/cycle-13.md` before the fold, with the
  reasoning behind its one item at `trail/architecture/self_answer-17.md`. A `companion-self-answer`
  run raised that item in this seat; no producing run wrote it. It was answered and is folded into
  RN-15 (RN-46). Since version 14 (`git diff --stat b4810919c HEAD` over the product and the project's
  `agari.md`, `doctrine/` and `project.md`), only the companion and its reasoning file moved; no
  upstream document changed, so `Inputs read:` stands. No obligation's text, no trace tag and no
  § 10 row moves, and no record in `adr/` moves. Nothing is left open, so the companion is removed
  and this document is Settled. *(re: Version 15; RN-15)*
