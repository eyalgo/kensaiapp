# Deferred Decisions — start tests under ignored SIGINT

This file owns the spec reading set aside by the design for `tracker17 · tobiishi · 2026-10-29_start-tests-under-ignored-sigint`.

## Shared collection support — reading set aside by development-design (2026-10-29)

**Spec lines:** `change_spec.md:L57-L58`, § Out of Scope, especially “Any test besides the 12 cases and the new proof”. The set-aside reading would prohibit changes to shared test support as well as changes to other individual tests.

**Conflict:** The same spec requires the exact repository-root launches to cover `unit`, `integration`, `e2e` and `architecture` (`change_spec.md:L6,L19,L32`, § Request, § Invariants and § Structural Goal). The current collection hook excludes browser tests unless the command explicitly names `e2e/` or a descendant (`products/tracker17/tests/conftest.py:L33-L48`, `_command_line_names_end_to_end` and `pytest_ignore_collect`). The documented product-local `pytest tests/` exclusion must also remain true (`products/tracker17/README.md:L91-L105`, § Running the tests).

**Reading taken:** Permit the shared pytest harness to include all four folders when an invocation outside the product explicitly names the whole test directory. Preserve the product-local exclusion and every existing test body and assertion. Put temporary, restored SIGINT setup in that same shared harness; the spec leaves fixture placement open (`change_spec.md:L33`, § Structural Goal) and permits incidental coverage of the end-to-end stop tests (`change_spec.md:L57`, § Out of Scope). This reading delivers the request's exact commands and retains the existing local command contract. The design's § Architect Review Notes records the rejected readings. No other individual test is taken on for edits.

**Owner:** none — for shukuba-refine
**Status:** open
