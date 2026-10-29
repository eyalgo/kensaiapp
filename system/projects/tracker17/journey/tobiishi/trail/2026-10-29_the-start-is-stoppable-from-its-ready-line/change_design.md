# Change Design — the start is stoppable from its ready line

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

This document owns the structural delta for `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line`.
The requirements remain in that change's `change_spec.md`, especially CP-644 to CP-656.
All product paths below are relative to `products/tracker17/` unless prefixed otherwise.
The artifact's home follows `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2,
“journey/tobiishi/<key>/”, the change-arc folder.

## 1. Change Summary

Use a non-raising SIGINT handler to record a stop request, and have the listener observe that request
between bounded waits. Keep the handler effective through listener cleanup and the return from
`start`. Place process-signal wiring in `main.py` and socket-serving mechanics in `web/listener.py`.
This is an architect decision, 2026-10-29, to realize CP-644 by construction rather than widening one
`KeyboardInterrupt` catch around only part of the lifetime.

The current start prints readiness before its interrupt-catching region and closes the listener
outside that region's catch (`main.py:L59-L72`, `start`, “listener.server_close”).
Python documents that an exception raised by a signal handler can interrupt execution between
bytecode instructions, and recommends avoiding a raising handler for reliable shutdown
([Python 3.11, signal handlers and exceptions](https://docs.python.org/3.11/library/signal.html#note-on-signal-handlers-and-exceptions)).
On this reasoning, enlarging a catch alone does not establish the arbitrary-point and repeated-signal
contract of CP-644.

Keep the two-argument `start(address, location) -> int` entry point and its refusal paths.
Keep the ready announcement after successful loading and binding, with the existing words and flush.
No stop message, save-on-exit, new dependency, new top-level part, or change to request rules is part
of this design (change spec CP-645 to CP-648 and Out of Scope).

## 2. Blast Radius

Ownership comes from `docs/SDD.md:L204-L240`, § 3, “The parts” and “The seams”.
The import constraints come from `docs/nfdr.md:L166-L197`, § 1.2, QC-13 to QC-19.

| Module | Status | What changes |
|---|---|---|
| `main.py` | Modified | Owning part `main`: wire a per-start stop flag and the real SIGINT adapter; coordinate readiness, cooperative serving, cleanup and the successful return. Provide an internal lifecycle seam taking its listener, announcement and interrupt collaborator explicitly. |
| `web/` | Modified | Owning part `web`: add cooperative serving in `web/listener.py`, driven by a supplied stop predicate and finite socket waits. Preserve inherited `serve_forever`, `shutdown`, `server_close`, request threading, and the existing `listen` export. |
| `domain/` | Unchanged | No rule, entity, status, or computation changes. |
| `application/` | Unchanged | No action, save contract, request lock, or clock changes. |
| `persistence/` | Unchanged | No file format, load, save, or location-lock changes. |
| `errors.py` | Unchanged | No exception type is added. |
| `tests/` | Modified | Add deterministic lifecycle and real-signal regression coverage; extend listener coverage. Existing start and browser tests remain regression contracts. |

`main` is the only production importer affected by the additive listener contract under QC-16 and
QC-17; the graph forbids the inner parts from importing `web` or `main`
(`docs/nfdr.md:L174-L188`, § 1.2, “must not import”).
Existing callers using `serve_forever` and `shutdown` need no migration, including the threaded
listener fixture (`tests/integration/test_listener.py:L45-L57`, `served`).
No forbidden edge or additional unit is required.

## 3. Sub-jobs

### Sub-job A — `web/`: cooperative serving

**Scope:** Extend `Listener` in `web/listener.py` with `serve_until(stop_requested)`.
The argument is a zero-argument predicate returning a boolean.
It contains no signal number, signal handler, stop message, or saved-data reference.
Keep the existing public entry points and exports.

**Exposes:** `Listener.serve_until(stop_requested: Callable[[], bool]) -> None`.
A predicate already true at entry returns without waiting for a request.
A predicate that becomes true during an idle wait is observed after a finite wait without needing
another client connection.
Repeated true values remain true for the lifetime owned by the caller.
Use a 0.5-second idle wait, matching the documented default polling interval of `serve_forever`
([Python 3.11 socketserver, BaseServer](https://docs.python.org/3.11/library/socketserver.html#socketserver.BaseServer.serve_forever)).
The wait interval is an internal serving choice, not a new deadline for the existing tests.
Serving ends without closing the listener; `server_close()` remains the caller's cleanup operation.
Use the existing threaded dispatch and response handling.
Preserve propagation of unrelated serving failures.

**Depends on:** none.

### Sub-job B — `main.py`: the stop lifetime

**Scope:** Keep real construction in `start`; separate the successful listening lifetime into an
internal coordinator receiving the listener, ready-announcement callable and interrupt collaborator.
The collaborator exposes an operation to arm the stop handler and a zero-argument stop predicate.
Its real implementation belongs in `main.py`; hand-written test collaborators replace it by argument.
No collaborator is looked up or replaced inside the subject by a test.

**Exposes:** `start(address: tuple[str, int], location: Path) -> int` remains the entry point.
The internal coordinator returns 0 after cooperative serving and listener cleanup.
The coordinator arms the handler after successful load and bind and before invoking the ready
announcement, then supplies the stop predicate to A's `serve_until`.
Cleanup runs once on the normal stop path, also when the stop was requested during the announcement.
An unrelated failure still cleans up the listener and propagates.

The real SIGINT callback only latches the per-start flag to true.
It raises nothing, prints nothing, performs no file or socket operation, takes no lock, and calls
neither `shutdown()` nor `server_close()`.
Every later invocation leaves the flag true, including invocations during cleanup and return.
Do not restore a raising handler before `start` returns.
Leave the installed non-raising callback in place on the successful command's return; no guarantee
extends into interpreter finalization or a later caller's signal policy.
Each later successful start creates and installs its own fresh flag.

If the incoming disposition is `SIG_IGN`, keep it ignored rather than enabling Ctrl-C for that
tracker; the existing suite fixture's launch repair stays separate (change spec Out of Scope,
“SIGINT already ignored”; `tests/integration/test_sigint_launch.py:L7-L17`, “inherits that”).
The adapter is process wiring for the normal main-thread start, since Python permits handler
installation only in the main interpreter thread
([Python 3.11 signal, signals and threads](https://docs.python.org/3.11/library/signal.html#signals-and-threads)).

**Depends on:** A's predicate-driven serving contract.

**Build sequence:** A, then B.
The edge is a contract dependency: B calls the method A introduces.
No atomic-landing edge is required: A is additive and the current start can keep using
`serve_forever` until B uses the new method.

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — predicate-driven listener | Use documented `BaseServer.handle_request()` with a finite `timeout` inside the cooperative lifetime. It retains threaded dispatch on this existing `ThreadingHTTPServer` subclass. Keep timeout configuration scoped to that lifetime. Do not use a blocking `shutdown()` in the serving thread or write private standard-library shutdown flags. |
| B — signal and startup wiring | Use a non-raising, idempotent boolean latch installed before readiness, with no early restoration. Supply its predicate to the listener. Use an explicit collaborator seam for the lifecycle checks rather than patching product names. |

`handle_request` honors `timeout`; `serve_forever` ignores it, and `shutdown` must run in another
thread from `serve_forever` ([Python 3.11 socketserver, BaseServer methods](https://docs.python.org/3.11/library/socketserver.html#socketserver.BaseServer.handle_request)).
On this reasoning, changing only `Listener.timeout` while retaining `serve_forever` would not
implement the new contract.
No write into another repository is part of either sub-job.

## 5. Test Additions

The rows below own the coverage delta, including the preserved clauses that the mechanism touches.
New file names are target locations, not claims that those files already exist.

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / B — readiness regression | New `tests/integration/test_start_stop.py` | Drive unchanged `main.start(address, location)` in a child process, with real files, listener and SIGINT. Deterministically inject SIGINT at the first execution boundary after the ready write completes and before serving begins. Assert `start` returned 0, child exit 0, empty stderr, and stdout containing exactly the ready line. The same case must reach that boundary on the pre-change tree and fail on the exit/stderr assertion every time, not on a missing helper or changed signature. Covers CP-644's first Example and CP-649's before/after Examples. |
| T2 / B — lifecycle phases | New `tests/unit/test_start_lifecycle.py` | Hand the coordinator recording listener, announcement and interrupt collaborators. Deliver stop callbacks when announcement finishes, at serve entry, during serving, at close entry, during close, after close, and immediately before the coordinator returns. Include normal serving completion followed by the first stop during close; include an earlier stop followed by individually delivered further callbacks in close and return. Assert 0, no output beyond readiness, one close, and an installed non-raising callback at return. Cover every phase of CP-644, not only the first gap. |
| T3 / B — real signal lifecycle | New `tests/integration/test_start_stop.py` | In isolated children, exercise the real signal adapter and lifecycle with listener/announcement collaborators handed in. Send actual SIGINT synchronously at the T2 phase boundaries, including two separately delivered signals, and assert callback return, result 0 and empty stderr. Exercise the production start through a real request with a saver held at an explicit barrier, so SIGINT arrives while the action is active. Assert quiet exit, without adding an in-flight-save outcome requirement. Covers idle, active-request, closing, and repeated-Ctrl-C Examples of CP-644. |
| T4 / A — listener progress | `tests/integration/test_listener.py` | Cover an initially true predicate; a stop during an idle bounded wait with no client wakeup; a normal request through `serve_until`; and a stop after a request. Hand the predicate in, assert prompt thread completion using the existing timeout scale, and verify `server_close` releases the port. Keep existing `serve_forever`/`shutdown` tests unchanged. |
| T5 / B — saved bytes and silence | New `tests/integration/test_start_stop.py` | Parameterize a valid populated location and an empty location. Snapshot all relative paths and file bytes before start, stop with no action active, and compare the snapshot afterwards. Assert no stdout after readiness. Covers both CP-645 Examples. |
| T6 / B — ready and refusal continuity | Existing `tests/integration/test_start.py`; existing `tests/e2e/test_start_command.py` and end-to-end harness | Retain all existing assertions, test counts and deadlines. Confirm ready text, first-line position and single occurrence. Retain unreadable data, held address, unreadable-plus-held precedence, unchanged bytes, exit 1 and no ready line. Add a missing clause to the new stop module rather than removing an assertion. Covers CP-646, CP-647 and their Examples, including the rule-implied combined refusal. |
| T7 / B — ignored disposition and failure cleanup | New `tests/integration/test_start_stop.py`; new `tests/unit/test_start_lifecycle.py` | In a child launched with SIGINT ignored, assert arming preserves `SIG_IGN`; use explicit test cleanup rather than waiting for SIGINT to stop that child. With injected serving failure, assert one close and propagation of the original failure, not a successful quiet-stop verdict. Covers Out of Scope's ignored-start boundary and prevents accidental swallowing of unrelated failures. |
| T8 / both — seam and trace | Existing `tests/architecture/test_reach.py` and `tests/architecture/test_trace.py` | Keep the no-product-patching, import/reach and pointer walks passing. Each new or edited test module docstring names existing SRS requirements, such as FR-1 and NFR-11, plus the CP identifiers it checks. Name only paths that exist when the module lands. Covers CP-650, CP-651 and their Examples; CP-656's automated half. |
| T9 / both — existing process coverage | Existing `tests/integration/test_start.py`, `tests/integration/test_sigint_launch.py`, `tests/e2e/conftest.py` | Keep the real start, real SIGINT, no retry, no skip/xfail, and unchanged deadlines. Covers CP-648 and its Example; T1 supplements this existing coverage. |
| T10 / both — suite and tool gates | Product's complete existing test suites and `pyproject.toml` gates | In the environment made by the current README instructions, require the non-browser and browser suite commands in CP-652 each to exit 0 in foreground and ignored-SIGINT launches. Require CP-653's Ruff format, Ruff lint, mypy, and compile gates to exit 0. Covers CP-652 and CP-653 Examples. |

**Deterministic regression seam (architect decision, 2026-10-29):** T1 may use a child-local Python
execution trace as an observer that emits the real signal at the selected readiness boundary.
It must neither replace product globals nor modify product files, code objects, locals, return
values, or exception handling.
Resolve the boundary from the code under test, rather than a fixed line number; assert that the
ready line has completed and that the signal-triggering boundary was reached exactly once.
Use explicit phase barriers for concurrent actions, not sleeps chosen to make a race likely.
T2 and T3 supply collaborators through the lifecycle seam; T1 retains the original entry point to
give CP-649 a meaningful baseline failure.
An observer failure or missing target is a harness error, not the expected baseline red.
The tracing API's execution events are documented for Python 3.11
([Python 3.11 sys.settrace](https://docs.python.org/3.11/library/sys.html#sys.settrace)).

**Retired assertions:** none.
No existing test or assertion is removed, relaxed, retried, skipped or given more time by this design
(change spec CP-648).
In particular, the listener's original shutdown contract remains covered while T4 proves the new
predicate-driven contract.

**Rules pass:** CP-644 maps to T1–T4, including first SIGINT during ordinary cleanup and repeated
signals; CP-645 to T5; CP-646–CP-647 to T6; CP-648 to T9; CP-649 to T1–T3;
CP-650–CP-651 to T8; CP-652–CP-653 to T10.
The absent-example review clauses CP-654–CP-656 are answered below.
The rule-implied already-stopped predicate is T4; ignored disposition and non-SIGINT failures are T7;
the return boundary is T2–T3; no-action empty and populated locations are T5.

## Records this change makes false

None — read `docs/adr/README.md` and the Accepted decisions ADR-0001, ADR-0003–ADR-0005,
ADR-0007–ADR-0009 and ADR-0011–ADR-0013; `docs/nfdr.md` §§ 1–3 and 6–10;
`docs/fdr.md` § Rules, “Starting and reaching the tracker” and “Saved data”; and `docs/SDD.md` § 3
and § 4 TS-1–TS-4.
The design keeps their five parts, dependency direction, threaded listener, saved-state boundaries
and console contracts.
The existing suite-environment gap remains the record-gap entry already in this change's
`deferred_decisions.md`; adding a cooperative listener method does not make that gap new.

## Architect Review Notes

- **Realize CP-644 by construction (b), architect, 2026-10-29:** choose a non-raising stop latch and
  cooperative serving. The reason is the arbitrary execution point at which Python may deliver a
  raising handler, documented in the Python signal source cited in § 1. An outer catch around only
  readiness and serving leaves the cleanup and return edges unproved.
- **Return boundary (b), architect, 2026-10-29:** do not restore an interrupt-raising disposition
  before return. Restoration would reintroduce a gap inside CP-644. Leave the successful command's
  callback installed; the spec's Out of Scope, “after `start` has returned”, excludes subsequent
  interpreter shutdown. This design promises no protection there. The flag is per start, rather
  than a module-global stopped value shared by subsequent starts.
- **Pre-ready scope, architect, 2026-10-29:** arm immediately before announcing readiness, after
  both refusals. This makes the ready-write boundary protected without delaying readiness until a
  first request. The design assigns no successful-stop guarantee to load, bind, or an interrupted
  ready write; those remain outside CP-644 under the spec's “span starts once the ready line has
  been written”.
- **CP-650 proof seam (b), architect, 2026-10-29:** use handed collaborators for lifecycle tests and
  a child-local trace observer for the baseline-compatible real-start regression. The observer is
  a signal-delivery instrument, not a substitute for a product collaborator. Without a
  baseline-compatible case, a newly introduced helper's absence could masquerade as proof of the
  old readiness bug. No reading of the spec is set aside.
- **Placement:** the `main` row of `docs/SDD.md` § 3 owns the start command, and the `web` row owns
  listening. On that reading, process-signal coordination belongs in `main.py`, while the finite
  wait and request dispatch belong in `web/listener.py`. Neither needs an unowned part or an
  import QC-16 forbids. No kind-(e) placement exception applies.
- **CP-654 / QC-60 — pass by design review:** use only Python 3.11 APIs: `signal.getsignal`,
  `signal.signal`, ordinary callables and a boolean, and the public `BaseServer.handle_request`
  and timeout contracts. Python's 3.11 documentation linked in §§ 1–4 covers those APIs.
  Do not use a newer-language typing construct or a private server field. This is a design
  review verdict, not a claim that a Python 3.11 suite was run.
- **CP-655 / QC-12 — pass by design review:** no sixth part or new top-level module is designed.
  The stop adapter and coordinator serve CP-644 and CP-650; the added listener operation serves
  CP-644 without moving socket mechanics into `main`. Each addition has a named requirement.
- **CP-656 / QC-24 — pass by design review:** `main.py` only constructs collaborators, installs
  the process handler, announces readiness and coordinates lifetime. It gains no domain rule,
  HTML, file format, or direct file/socket access. T8 preserves QC-42 and QC-43's automated half.
- **QC-8, QC-23, QC-27 — pass by design review:** the predicate is an argument for one listener's
  lifetime, not page/request state. `web` gains no application rule, saved-data knowledge, clock
  read, or process-signal installation. Replacing the browser interface still affects only `web`
  and its wiring in `main`, per `docs/nfdr.md` § 1.4 QC-27.
- **QC-41 — pass by design review:** none of the specified collaborators, new inputs or tests
  introduces an account, key or credential; the design requires no secret.
- **QC-40 browser review, 2026-10-29 — exception applies:** the pinned Playwright release names
  Chromium 153.0.8010.12 in its own
  [browser manifest](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json).
  Google's [2026-09-15 desktop advisory](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html)
  lists critical fixes in 153.0.8010.47/.48, and the
  [2026-10-27 desktop advisory](https://chromereleases.googleblog.com/search/label/Stable%20updates)
  lists further critical fixes. The older build remains covered on this review date by
  `docs/nfdr.md:L1068-L1081`, RN-33, “Dated exception to QC-40”, through 2026-11-07.
  No browser or package pin moves in this design.
- **QC-40 package-advisory review — incomplete:** the sandboxed lookup of the 15 exact pins in
  `tests/requirements.txt` returned DNS errors. Automatic approval review then rejected the
  bounded public GitHub advisory API lookup, stating that it would send repository dependency
  metadata to an external destination without explicit authorization. The requested command never
  executed. No alternative route was attempted after that rejection. This is not a finding that
  the package set has no critical advisories; completing the package review requires authorization
  for that metadata and destination. The browser exception does not answer the package check.

**Cold-read:** every changed production responsibility is placed in § 2; A's full callable contract
precedes B's dependency; § 5 maps every Example and rule-implied edge; the unchanged public methods
retain their tests; no record correction or outside-repository write is required. The package
advisory review limitation above remains explicit.
