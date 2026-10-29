# Change request — 2026-10-29_the-start-is-stoppable-from-its-ready-line

*The PM-minted intake for one **飛び石 Tobiishi** — the single change the chain
(`core/launchers/chain-development/launcher.sh <project>` → `core/tools/chain_development.py`) carries
through the pipeline. Lives at `system/projects/<name>/journey/tobiishi/<key>/change_request.md` (`<key>` =
`<YYYY-MM-DD>_<slug>`). The PM writes this when opening the Tobiishi, through `tobiishi-open`; `development-specs`
reads it as the pipeline's first input — it does **not** coin the key or scan a queue. **No `Project:`
field** — the project is implied by which project's `journey/tobiishi/` this sits in.*


---

**Request:** Make the tracker stop cleanly on Ctrl-C from the moment it prints its ready line until `start` returns. Today
`start` in `products/tracker17/main.py` prints "The tracker is running. Open http://… in your
browser." and only then enters the `try` whose `except KeyboardInterrupt` stops it quietly
(`main.py:L59-L72`). A Ctrl-C that lands between the two ends the tracker with a traceback on
standard error and a non-zero exit instead of exit 0 and nothing written. The start tests send
SIGINT as soon as they read the ready line (`tests/integration/test_start.py:L528-L530`), so on a
loaded machine they land in that gap: the run closing
`tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` on 2026-10-29 saw
`test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` fail once in a full
foreground run that took 782 s (`2651 passed, 1 failed`), and pass alone and in a second full run
(`2652 passed`). An operator who presses Ctrl-C right after starting hits the same gap.

Measured in a disposable clone of main at `<a commit not in the public history>`, 2026-10-29: the proof test passed 15 of 15 on
its own. With a one-second pause added between the ready print and the `try`, the start case
`test_start_reads_each_legacy_form_with_every_existing_value[projects-only]` failed on
`assert (status, errors) == (0, b"")`. With the ready print moved inside the `try`, the same case
passed with the pause still there (`1 passed in 4.31s`).

**The span ends when `start` returns.** After that the tracker has stopped, and what a Ctrl-C does
while Python itself shuts down is the interpreter's, not the product's: CPython resets every Python
signal handler during finalization, so no product code can keep the quiet stop past that point. The
first walk of this change halted at its plan on exactly that, on 2026-10-29, after its spec
stretched the span to the process's end.

**What must not be weakened:** the ready line's words and when it is printed; Ctrl-C's effect for an
operator, which is a quiet stop with exit 0; the two refusals `start` prints before it listens; the
start tests keep driving the real start in a child process and stopping it with a real SIGINT; no
test is deleted, skipped, retried or marked expected-to-fail; no deadline is lengthened to hide the
gap.

**Proof:**
- A test that fails on `main` every time, not only under load, and passes after: it shows that a
  Ctrl-C at any point from the ready line being printed until `start` returns stops the tracker with
  exit 0 and nothing on standard error. A test whose red depends on timing is not the proof.
- `python -m pytest products/tracker17/tests/ -q` and `python -m pytest products/tracker17/tests/e2e/ -q`
  exit 0, in the foreground and with SIGINT ignored, run in the product's own test environment as
  the setup instructions make it.

**Category:** bug
**Behaviour:** changing
**Classified because:** a functional bug: a Ctrl-C right after the ready line ends the tracker with a
traceback and a non-zero exit, a wrong observable (`change_classification.md` § *Category notes*,
`bug`: "a functional bug (wrong observable behaviour) is `changing`").

**Sizing:** one capability, one honest merge — the start's stop path and the test that proves it.
