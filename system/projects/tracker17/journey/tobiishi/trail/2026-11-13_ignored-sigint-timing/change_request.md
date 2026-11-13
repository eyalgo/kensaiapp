# Change request — 2026-11-13_ignored-sigint-timing

---

**Request:** The test that starts a pytest with SIGINT ignored and has it run one real-start case (`tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint`) failed in a full run of the card's suite and passed alone, twice. The start case it selects waits a fixed 30 seconds for the tracker to stop after a real SIGINT. Find the timing dependence that is left after the ready-line fix, add a measurement among the change's tests that makes the failure happen on demand (it fails on the base commit and passes after the change, with no full run needed to hit it by luck), and remove the dependence in the product. Name the cause in the commit body or a test docstring. Where the cause sits in the start's stop path (`main.py`'s `SigintStopRequests` and `serve_until_stopped`, `web/listener.py`'s `serve_until`) the fix goes there; where it sits in the test's own setup it goes there, and the product is not touched for the sake of it. The proof test must keep proving what it proves: a start launched with SIGINT ignored stops, exits 0 and writes nothing to standard error. The test passes alone, and both commands of the card's test command (`tests/` and `tests/e2e/`) pass in full from the change worktree root. No wait limit is raised (the 30-second waits at `tests/integration/test_start.py` and `tests/integration/test_sigint_launch.py` stay as they are or shrink), and no test is skipped, retried or marked expected-to-fail. Nothing the product's public names accept or return changes.

**Sizing:** one capability, one merge. The acceptance boundary is the station's reached-when 1 to 4 (`2026-11-13_the-ignored-sigint-cause`): a real start stops on SIGINT under a full run of the suite. The measurement, the cause and the removal are one obligation of that capability and stay together; a separate find-the-cause change would serve only the fix.

**Category:** bug
**Behaviour:** preserving
**Classified because:** the station's reached-when 1 to 4 and guardrail ask the existing, already-pinned contract (a start launched with SIGINT ignored stops, exits 0, writes nothing to standard error) to hold in a full run, and the guardrail says the proof test may not assert less; the new measurement characterises that contract and adds no behaviour.

**Sealed:** 2026-11-13 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
