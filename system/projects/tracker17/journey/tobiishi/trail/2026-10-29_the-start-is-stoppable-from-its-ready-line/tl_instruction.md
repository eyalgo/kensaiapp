# Tech Lead instruction — the start is stoppable from its ready line

**Category:** bug
**Behaviour:** changing
**Product root:** products/tracker17 — product paths below are relative to this directory; commands explicitly naming `products/tracker17` run from the change worktree root.
**Scope:** Quiet SIGINT stopping from completed readiness through the return from `start`, including repeated signals and cleanup.

This instruction owns the task cut and verification scaffold for `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line`.
Its home is the change-arc folder under `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, “journey/tobiishi/<key>/” (L2203–L2210).
Requirements and structural choices are the sibling `change_spec.md` and `change_design.md`.
The classification above propagates `change_design.md:L4-L5`, “Category” and “Behaviour”.

## Project layout

```text
products/tracker17/
  main.py                                ← modified, Task 2
  web/
    listener.py                          ← modified, Task 1
  tests/
    integration/
      test_listener.py                   ← modified, Task 1
      test_start_stop.py                 ← new, Task 2
    unit/
      test_start_lifecycle.py             ← new, Task 2
```

No directory or package initializer needs creating for these paths: `tests/integration/`, `tests/unit/` and `web/` are present in `git ls-files products/tracker17` at `7a6340232139badfbc4b62d6614e5b088b89c3e7`.
Placement follows `docs/SDD.md:L204-L240`, § 3, “The parts”: `main` owns startup and process wiring; `web` owns listening.
The full module set and allowed/forbidden edges remain `docs/nfdr.md:L166-L197`, § 1.2, QC-13–QC-19.
In particular, socket mechanics stay in `web/listener.py`; the signal adapter and lifecycle coordinator stay in `main.py`.
The listener receives a boolean predicate, with no knowledge of SIGINT, saved data or the clock.
The public `start(address, location)` signature and `web` exports remain those in `main.py:L30-L35` and `web/__init__.py:L7-L10`.

**Language resolution:** Python, step 1 of the resolution chain, from the instance-relative `system/projects/tracker17/project.md` “Languages: Python”; read `<CORE>/doctrine/engineering/languages/python/README.md` and its seven concern destinations, including `testing_python.md` outside the packet (card line L12; packet router L12–L22).

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files in the instance change worktree returned 5992 tracked paths; the complete listing contains no CI configuration or build-service runner configuration. git -C products/tracker17 ls-files returned 280 product paths, with no CI configuration."
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

## TL Review Notes

Decisions below are the Tech Lead's critical review, 2026-10-29.

- **Task cut:** retain sub-jobs A and B as Tasks 1 and 2 because B consumes A's additive method, and the design states no atomic-landing edge (`change_design.md:L111-L116`, “Build sequence”). Give the change-only guardrails their own review task, Task 3, because CP-648 compares this branch with its base rather than defining a lasting product behaviour (`change_spec.md:L28-L30`, “What stays as it is”).
- **Coverage strengthened:** add explicit timeout-restoration checks on both normal and exceptional listener exit. The design scopes the timeout to the cooperative lifetime but T4 does not explicitly assert restoration (`change_design.md:L120-L123`, “Keep timeout configuration scoped to that lifetime”). This prevents the additive operation from changing later use of the existing server API. Add a concurrent-client response check as well: T4's single normal request cannot distinguish threaded dispatch from a sequential listener.
- **Coverage strengthened:** assert two consecutive successful starts use independent latches, and exercise the actual `start` return boundary as well as the coordinator's. These make the per-start and no-early-restoration clauses directly testable (`change_design.md:L95-L102`, “Each later successful start”).
- **Coverage strengthened:** add an announcement-failure cleanup case because sub-job B says an unrelated failure still closes and propagates, while T7 only names serving failure (`change_design.md:L89-L93`, “An unrelated failure”).
- **Proof clarified:** Task 2's readiness case must work against the old two-argument entry point without importing the new coordinator. Missing helpers and missed observer targets are harness failures, not CP-649's red (`change_design.md:L138-L158`, “Deterministic regression seam”). Keep the portable case independently selectable for the pre-change check.
- **Active-request seam clarified:** T3 asks for production `start` with a saver barrier, while B retains construction inside the unchanged two-argument entry point (`change_design.md:L82-L88`, “Keep real construction”, and L140, “production start”). For that real-start case, use a child-local observational barrier while the real saver is active, extending the same no-mutation observer approach used by T1. Do not add a saver parameter to public `start` or patch a product global. The separate coordinator cases still receive their collaborators as arguments. The reason is to prove real-start signal wiring without replacing the production path.
- **Environment boundary:** use the environment from `README.md:L89-L109`, “Running the tests”, as CP-652 requests. The move to uv is already held in sibling `deferred_decisions.md:L19-L24`, “The test suite's environment made by uv”; it does not belong to these tasks. Preserve dependency pins and the pin test.
- **Baseline gate:** the card command `pytest products/tracker17/tests/` collected 2652 tests on Python 3.15.0 with pytest 9.1.1. The Python probe `listener.bind(('127.0.0.1', 0))` returned `PermissionError: [Errno 1] Operation not permitted` in this sandbox. The command exited 1 with `21 failed, 2600 passed, 31 errors in 269.11s`; its reported listener setup errors include the same bind refusal. This run did not establish a green baseline. Do not treat these results as CP-649 proof or use the red-at-baseline task lane: no earlier unit supplied a deferred task and named failing tests for this plan.
- **Review limitation:** the design's QC-40 package-advisory review is explicitly incomplete (`change_design.md`, “QC-40 package-advisory review — incomplete”). This instruction makes no package-security verdict. The browser exception is only `docs/nfdr.md:L1068-L1081`, RN-33, “Dated exception to QC-40”; it supplies no package verdict.

### Task 1: Cooperative listener serving (`web/listener.py`, `tests/integration/test_listener.py`)

**Dependencies:** None

**What to build:** Add `Listener.serve_until(stop_requested: Callable[[], bool]) -> None` in the listening part, with a 0.5-second idle wait and unchanged threaded request dispatch, per `change_design.md:L59-L76`, sub-job A. Serving ends without closing the listener. The caller owns the predicate's lifetime and cleanup.

#### Behaviours to verify

Add to `tests/integration/test_listener.py`; retain its existing tests and fixture.

- `test_cooperative_listener_returns_when_stop_is_already_requested` — a true predicate at entry returns without accepting or awaiting a request; the listener remains open until its caller closes it.
- `test_cooperative_listener_observes_stop_while_idle_without_a_client` — signal the supplied predicate through an explicit test barrier during an idle wait; the serving thread joins within the existing 10-second scale without any client connection to wake it.
- `test_cooperative_listener_serves_a_real_request` — a real loopback request receives the existing page and response policy while the predicate is false; no console output is produced.
- `test_cooperative_listener_stops_after_a_request` — a completed request followed by a latched stop ends serving, and caller cleanup releases the port.
- `test_cooperative_listener_preserves_threaded_dispatch` — hold one client with incomplete request headers and show a second client receives a complete normal response before releasing the first. Use explicit barriers and existing timeout scales; a second TCP connection merely entering the backlog does not prove dispatch.
- `test_cooperative_listener_restores_timeout_after_return` — after a normal cooperative lifetime, the listener's pre-existing timeout is restored.
- `test_cooperative_listener_restores_timeout_and_propagates_failure` — an explicitly supplied predicate that raises a sentinel exception causes that same exception to propagate, restores the timeout, and leaves closure to the caller.
- Existing `serve_forever`/`shutdown` tests remain green, including `test_the_listener_stops_on_server_close`; their public contract is preserved (`tests/integration/test_listener.py:L42-L57`, `served`, and L137–L148, that test).

Each edited module docstring names SRS FR-1, FR-2 and NFR-11, the applicable CP-644/CP-650/CP-651 clauses, and only existing paths, per `change_spec.md:L35-L36`, CP-650–CP-651.

#### Held by review

- Keep the 0.5-second wait an internal serving choice, not a new test deadline (`change_design.md:L71-L74`, “not a new deadline”).
- QC-23 and QC-43: no process-signal installation, saved-data knowledge, rule or clock read enters `web`; inspect the production diff against `docs/nfdr.md` § 1.3 and § 3.

#### Implement

Infer from failing tests.

```text
# Hint:
Use documented `BaseServer.handle_request()` with a finite `timeout` inside the cooperative lifetime. It retains threaded dispatch on this existing `ThreadingHTTPServer` subclass. Keep timeout configuration scoped to that lifetime. Do not use a blocking `shutdown()` in the serving thread or write private standard-library shutdown flags.
```

#### Verification gate

From the change worktree root, in the README's activated product environment:

```sh
pytest products/tracker17/tests/
```

Pass: all Task 1 behaviours and the existing non-browser suite pass, including architecture and pointer walks. The existing start tests pass while the additive listener method lands. No socket or interpreter prerequisite failure counts as a behavioural red.

### Task 2: Quiet stop lifetime (`main.py`, `tests/unit/test_start_lifecycle.py`, `tests/integration/test_start_stop.py`)

**Dependencies:** Task 1 — supplies `Listener.serve_until`.

**What to build:** Keep construction and refusals in `start`, and add the internal successful-lifetime coordinator and real per-start interrupt adapter in `main.py`, per `change_design.md:L80-L109`, sub-job B. The coordinator receives its listener, zero-argument ready announcement and interrupt collaborator explicitly. The interrupt collaborator exposes arming and a zero-argument boolean stop predicate. Real construction stays in `start`; fakes enter only by arguments. Use explicit parameter and return types compatible with the product's Python 3.11 floor.

Arm after load and bind succeed, immediately before announcing readiness. Once armed, every callback only latches true. Keep the non-raising callback installed through the return of public `start`; retain incoming `SIG_IGN`. Keep the ready print and both refusal messages verbatim. Cleanup closes the listener once on successful stop and on unrelated serving failure; unrelated failures propagate. These are B's contracts (`change_design.md:L88-L106`) and CP-644–CP-647 (`change_spec.md:L23-L30`).

#### Behaviours to verify

In `tests/unit/test_start_lifecycle.py`, hand-written recording collaborators exercise the coordinator:

- `test_lifecycle_arms_before_announcing_and_passes_the_stop_predicate` — call records establish arm, announcement, serving and close order, with the supplied predicate reaching the supplied listener.
- `test_lifecycle_stops_quietly_at_each_phase` — parameterize completion of announcement, serve entry, serving, close entry, closing, after close and immediately before coordinator return; result 0, one close and no output beyond readiness.
- `test_lifecycle_accepts_the_first_stop_during_normal_cleanup` — serving completes normally, the first callback occurs during close, and cleanup and return remain quiet.
- `test_lifecycle_accepts_further_stops_during_cleanup_and_return` — after an earlier stop, individually deliver additional callbacks during close and return; the latch stays true and no callback raises.
- `test_lifecycle_closes_once_and_propagates_unrelated_announcement_failure` — a sentinel announcement failure still causes one close and propagates unchanged.
- `test_lifecycle_closes_once_and_propagates_unrelated_serving_failure` — a sentinel serving failure propagates as the same failure after one close, rather than becoming result 0.

In `tests/integration/test_start_stop.py`, isolate real signal policy in child processes:

- `test_real_start_stops_at_the_completed_ready_write` — invoke unchanged `main.start(address, location)` with a real listener and real files; deliver actual SIGINT at the first execution boundary after the ready print completes and before serving begins. Assert child exit 0, returned result 0, exactly one ready line and empty stderr. This case alone supplies the baseline-compatible CP-649 proof.
- `test_real_signal_stops_quietly_at_each_lifecycle_phase` — use the real interrupt adapter with handed listener and announcement collaborators; synchronously deliver actual SIGINT at each phase above, including normal cleanup's first signal. Assert successful callback completion, result 0 and empty stderr.
- `test_real_signal_accepts_separately_delivered_repeated_stops` — acknowledge the first callback before delivering the second, including during close and return; two sends must not pass merely because the OS combined pending signals.
- `test_real_start_keeps_the_non_raising_handler_through_its_return` — drive the actual public entry point, observe its return boundary and deliver SIGINT before that return completes; result and child exit are 0, stderr empty. Also inspect the installed disposition immediately after return without asserting interpreter-finalization behaviour.
- `test_real_start_stops_while_a_real_request_is_saving` — reach production `start` through a real request and acknowledge a barrier inside the real saver before sending SIGINT. Assert quiet exit while an action is active; use the non-mutating child observer described in TL Review Notes. Make no new claim about which saved state wins.
- `test_idle_stop_preserves_every_saved_path_and_byte` — parameterize empty and valid populated saved-data locations; compare the full relative-path and byte snapshots before and after a no-action stop, with no stdout after readiness.
- `test_arming_preserves_an_inherited_ignored_sigint` — launch a child with SIGINT ignored, arm the real adapter and verify `SIG_IGN` remains; explicitly clean up the child without waiting for SIGINT to stop it.
- `test_successive_starts_have_independent_stop_requests` — in one isolated interpreter, stop one successful start and show a later successful start begins with a fresh false latch and installs its own callback.
- `test_refused_start_retains_its_message_and_saved_bytes` — cover unreadable data, occupied address and both together; result 1, one existing stderr message, no ready line, unchanged saved paths/bytes, unreadable-data precedence. Existing assertions stay in place; add any missing clause here.
- Ready-line assertions preserve the exact CP-646 wording, first-line position, flush and single occurrence; this is also checked by the existing browser start test (`change_spec.md:L28-L29`, CP-646–CP-647; `change_design.md:L143`, T6).

For the readiness observer, resolve the completed-print boundary from the source under test, not a fixed line number. Record separately that the ready write completed and that the injection target was reached exactly once. Do not mutate globals, code objects, files, frame locals, return values or exception handling. Missing targets and observer exceptions fail as harness errors. Use explicit barriers for concurrency, not timing sleeps (`change_design.md:L149-L158`, “Deterministic regression seam”).

The baseline-compatible test reads no Git history during ordinary suite execution. Its proof against the pre-change tree is a change-only verification, held by Task 3. New test module docstrings name SRS FR-1 and NFR-11, the CP clauses checked and only paths that exist; the existing architecture suite enforces the pointer and no-patching halves (CP-650–CP-651).

#### Held by review

- The callback raises nothing, prints nothing, takes no lock, performs no file/socket work and calls neither `shutdown` nor `server_close`; read its complete body against `change_design.md:L95-L101`, “only latches”. The lifecycle tests sample phase boundaries; the simple callback body supplies the arbitrary-point argument for CP-644.
- No early restoration creates a gap between coordinator return and `start` return; inspect the complete successful return path, including any context-manager exit or `finally` block.
- CP-654–CP-656: review Python 3.11 compatibility, requirement-paid additions and the absence of rules, pages or file formats in `main.py`; retain the design's review clauses rather than calling a newer-interpreter suite a Python 3.11 run (`change_spec.md:L39-L41`).
- No guarantee is added for pre-ready interrupts, ignored-start stopping, post-return finalization or an in-flight save's outcome (`change_spec.md:L85-L93`, “Out of Scope”).

#### Implement

Infer from failing tests.

```text
# Hint:
Use a non-raising, idempotent boolean latch installed before readiness, with no early restoration. Supply its predicate to the listener. Use an explicit collaborator seam for the lifecycle checks rather than patching product names.
```

#### Verification gate

From the change worktree root, in the README's activated product environment:

```sh
pytest products/tracker17/tests/
```

Pass: all new behaviours and every existing non-browser test pass, including real-start, ignored-launch, reach and trace tests. The readiness case has a deterministic failure on the unmodified start path, caused by the quiet-stop assertion rather than a missing new seam. Neither Task 1 nor Task 2 has a probabilistic-red property: the added regressions use controlled delivery points.

### Task 3: Review the change-only proof and preserve existing tests (`tests/integration/test_start.py`, `tests/integration/test_sigint_launch.py`, `tests/e2e/`, `tests/conftest.py`)

**Dependencies:** Tasks 1 and 2 — reviews their completed diff and runs their resulting product.

**What to build:** Supply the change-scoped verification record for CP-648, CP-649, CP-652 and CP-653; no lasting suite test reads the change's merge base or fixed historical commit. This is a review-verified task because its invariants compare this change with its base, per `<CORE>/prompts/tech_lead_create_tl_instruction.md` Step 3, “A check that holds only for this change”.

#### Deliverables verified by review

- CP-648: from the change worktree root, `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/integration/test_start.py products/tracker17/tests/integration/test_sigint_launch.py products/tracker17/tests/e2e products/tracker17/tests/conftest.py` is empty. Review the additive `test_listener.py` diff separately: every existing assertion, test, deadline and real-signal path remains; no retry, skip or xfail is added. The fixed CP-648 reference is the sibling spec, “What stays as it is” (`change_spec.md:L28-L30`).
- CP-649: run the independently selectable `tests/integration/test_start_stop.py::test_real_start_stops_at_the_completed_ready_write` against the branch's merge-base production tree in a disposable Git clone, with only that portable regression module supplied. The clone is outside the main checkout and the ordinary suite never creates it. The signal target and completed ready write are both acknowledged; failure is on exit status/stderr. Run the same selected case on the completed branch and require success. Record commands, baseline identity, acknowledgements and the two verdicts. No numeric repeat count or race hit rate substitutes for deterministic placement.
- CP-652: execute the four commands below in the README's product environment, preserving their exact foreground and ignored-SIGINT distinction; each exits 0. Existing process tests continue to start real children and send real SIGINT.
- CP-653: execute all four tool commands below at the installed versions from `tests/requirements.txt`; each exits 0. No dependency, lock-format or setup migration belongs to the deliverable (`change_spec.md:L93`, environment record gap).

#### Implement

Verified by review — no test.

#### Verification gate

For the CP-649 baseline comparison, from the change worktree root, use the already activated README environment and a disposable clone:

```sh
proof_repository=$(git rev-parse --show-toplevel)
proof_base=$(git merge-base main HEAD)
proof_clone=$(mktemp -d)
git clone --quiet "$proof_repository" "$proof_clone"
git -C "$proof_clone" checkout --quiet "$proof_base"
cp products/tracker17/tests/integration/test_start_stop.py "$proof_clone/products/tracker17/tests/integration/test_start_stop.py"
python -m pytest "$proof_clone/products/tracker17/tests/integration/test_start_stop.py::test_real_start_stops_at_the_completed_ready_write" -q -p no:cacheprovider
```

Expected: the selected case reaches its ready boundary exactly once and fails on the exit/stderr verdict. A collection error or missing helper does not pass this criterion. Record the clone's baseline identity with `git -C "$proof_clone" rev-parse HEAD`. The portable test module imports no new lifecycle symbol at collection time. Read the output before removing this run's clone, from outside it, in a separate command:

```sh
rm -rf "$proof_clone"
```

On the completed change worktree, the same readiness case must pass:

```sh
python -m pytest products/tracker17/tests/integration/test_start_stop.py::test_real_start_stops_at_the_completed_ready_write -q
```

After following `README.md` § “Running the tests”, activate that product environment from the change worktree root:

```sh
source products/tracker17/.venv/bin/activate
pytest products/tracker17/tests/
python -m pytest products/tracker17/tests/ -q
python -m pytest products/tracker17/tests/e2e/ -q
/bin/sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'
/bin/sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/e2e/ -q'
```

From the product root, using the same activated environment:

```sh
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
python3 -m compileall -q main.py errors.py domain application persistence web tests
```

Pass: every review criterion has a recorded verdict, the baseline comparison fails for the specified behaviour, the completed-branch comparison passes, all four CP-652 runs exit 0 and all CP-653 tool gates exit 0. The card suite remains green; no failure is hidden by a longer deadline or changed test disposition.
