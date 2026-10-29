# Change Design — real-start tests under ignored SIGINT

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** preserving
**Publishes text:** no

This document owns the test-harness boundaries and proof for `tracker17 · tobiishi · 2026-10-29_start-tests-under-ignored-sigint`. The characterization contract remains in its `change_spec.md`, § Invariants.

---

## 1. Change Summary

Keep the product unchanged. Put temporary signal setup in the shared pytest harness and put the regression proof beside the existing real-start tests. The shared harness must make test-launched trackers interruptible during the test session and restore the exact incoming SIGINT handler when that session ends. This is the architect's choice, 2026-10-29, of the test-side fixture placement left open by `change_spec.md:L30-L34`, § Structural Goal.

Also make the two repository-root launches in `change_spec.md:L6`, § Request, collect all four requested test folders. Preserve the separate, product-local test commands documented in `products/tracker17/README.md:L91-L105`, § Running the tests. The collection rule must distinguish an invocation outside the product naming the whole test directory from a product-local invocation; it must not treat a passing exit status as proof of browser coverage.

No transitive blast radius — public surfaces unchanged. No product import, return value, signature, saved-data format, message or operator signal behavior changes. The two public entry signatures are `start(address, location)` and `main(argv=None)` in `products/tracker17/main.py:L30-L77`, `start` and `main`.

---

## 2. Blast Radius

The production module set and import restrictions come from `products/tracker17/docs/nfdr.md:L32-L41,L166-L199`, § 1.1 QC-1/QC-2 and § 1.2 Forbidden imports. The production ownership table is `products/tracker17/docs/SDD.md:L202-L238`, § 3 The parts, and the seams between them. Test-session setup and collection belong to test support, outside those five product parts; no product part acquires logic.

| Module | Status | What changes |
|---|---|---|
| `products/tracker17/tests/conftest.py` | Modified (test support only) | Own the session's temporary SIGINT disposition and its restoration. Extend collection only for an outer invocation explicitly naming the entire product test directory. Keep the import shim, source walk and existing product-local collection behavior. |
| `products/tracker17/tests/integration/test_start.py` | Modified (characterization proof only) | Add one isolated regression test exercising an existing real-start case from a pytest process launched with SIGINT ignored. Keep every existing case, assertion, helper signature and timeout. |
| `products/tracker17/domain/` | Unchanged | No rule, entity, implementation symbol or export changes. |
| `products/tracker17/application/` | Unchanged | No action, collaborator contract or export changes. |
| `products/tracker17/persistence/` | Unchanged | No load, save, lock or export changes. |
| `products/tracker17/web/` | Unchanged | No listener, page, route or export changes. |
| `products/tracker17/main.py` | Unchanged | No production signal setup or entry-point changes. |
| `products/tracker17/errors.py` | Unchanged | No error or import changes. |
| `products/tracker17/tests/e2e/` | Unchanged | Existing trackers inherit the shared test session's launch conditions. No end-to-end test body, fixture or assertion is edited. |
| Remaining `products/tracker17/tests/` | Unchanged | Existing assertions and architecture checks continue to run. |

The test-only rows are not relocations; § Architect Review Notes records the departure from the relocation-shaped template. No `__init__.py` is affected and no public product surface changes, so the production forbidden-import graph has no transitive effect.

---

## 3. Layout Plan

Retain the existing files. There is no symbol move, package split, new named module or re-export change. All existing implementation symbols remain where they are; the table lists only the affected test-support symbols and the new proof.

| Symbol | Kind | Target module |
|---|---|---|
| `_interruptible_test_session` | New private, autouse session fixture | `products/tracker17/tests/conftest.py` |
| `pytest_ignore_collect` | Existing pytest hook | `products/tracker17/tests/conftest.py` |
| `_command_line_names_end_to_end` | Existing private collection predicate; retain its signature and direct end-to-end selection behavior | `products/tracker17/tests/conftest.py` |
| `test_real_start_stops_when_pytest_inherits_ignored_sigint` | New characterization test | `products/tracker17/tests/integration/test_start.py` |

### Signal boundary

The fixture saves the incoming SIGINT handler before changing it, makes the pytest session interruptible in its main thread, and restores that saved handler in teardown even if a test fails. Its lifetime encloses the subprocess fixtures' setup and cleanup. It does not rewrite product modules or install a permanent handler in an operator's tracker.

This choice realizes the launch condition explicitly: Python installs its interrupt handler only when the parent's disposition permits it, and only the main thread may set a handler ([Python 3.11 signal documentation](https://docs.python.org/3.11/library/signal.html), § General rules and § Signals and threads). A session autouse fixture runs before non-autouse fixtures of that scope ([pytest fixture reference](https://docs.pytest.org/en/stable/reference/fixtures.html#autouse-fixtures-are-executed-first-within-their-scope)). Restoration belongs to the same fixture as setup.

### Collection boundary

Keep the existing product-local rule: from `products/tracker17`, `pytest tests/` excludes the browser tests and an explicit `pytest tests/e2e/` includes them, as documented in `products/tracker17/README.md:L101-L105`, § Running the tests. Keep the no-argument default's existing selection too.

Add exactly the requested outer full-suite case: when pytest is invoked from outside the product and an explicit directory argument resolves to this product's entire `tests/` directory, include `e2e/` with the other test folders. Decide from the invocation directory and resolved argument paths, rather than a hardcoded project name or string prefix. A selected integration node or an integration-only directory does not become a full-suite request. Existing explicit end-to-end selection continues to work from either location.

### Regression boundary

The new proof starts a separate Python process with `sys.executable`. That driver explicitly sets SIGINT to ignored and checks that precondition before invoking pytest on one existing real-start case, `test_every_supported_saved_form_keeps_all_existing_values[current]`. The nested run does not select the new proof, so it cannot recurse. The driver checks that SIGINT is ignored again after pytest returns, proving fixture restoration. The outer proof requires a successful run of the selected case, not merely successful collection. Its signal check precedes its collection checks, so its failure on the starting commit demonstrates the stop timeout rather than only the already-missing browser collection.

The selected case already checks real process startup, a real SIGINT, exit status 0, empty standard error, saved values, unchanged saved bytes and unchanged file listing (`products/tracker17/tests/integration/test_start.py:L730-L758`, `test_every_supported_saved_form_keeps_all_existing_values`). Reusing it keeps the regression attached to the existing assertions. Neither the driver nor the fixture patches a product name. Keep the helper's 30-second stop wait and cleanup as they stand (`products/tracker17/tests/integration/test_start.py:L516-L535`, `_run_real_start`).

There are no new product interface contracts or product-module build dependencies. Test-task ordering is not specified here.

---

## 4. Code Strategy

| Module | Hint |
|---|---|
| `products/tracker17/tests/conftest.py` | Use a session autouse fixture with `signal.default_int_handler`, retaining the previous handler for teardown. Do the setup in pytest's main thread. The collection seam is `config.invocation_params.dir` together with explicit arguments resolved to `TESTS_DIRECTORY`; preserve the product-local exclusion. |
| `products/tracker17/tests/integration/test_start.py` | Use an isolated Python driver that sets `SIG_IGN` before `pytest.main` and selects one existing parametrized real-start node. Assert the incoming and restored dispositions in that driver. Invoke subprocesses with argument lists and the same interpreter; keep the existing timeout and kill/reap behavior. |

No write outside the instance/product worktree is part of this design.

---

## 5. Test Continuity

No assertion is retired. Every existing parametrization and assertion in the four real-start callers stays intact (`products/tracker17/tests/integration/test_start.py:L538-L588,L680-L758`, the four caller definitions). The added proof characterizes the pass-the-suite contract; it adds no tracker behavior.

The spec's § Invariants and § Structural Goal supply the characterization cases (`change_spec.md:L17-L34`); it has no separate Examples table. The following rows cover those clauses, including the collection and restoration edges exposed by this design.

| Row | Affected surface | Existing coverage / required continuity | Characterization proof or check |
|---|---|---|---|
| T1 | Twelve real-start cases | Keep the 3 legacy-form cases, 3 name cases, 2 comment cases and 4 saved-form cases with every assertion unchanged. | Run `tests/integration/test_start.py` both normally and under ignored SIGINT. The only expected baseline red cases are the twelve named in `change_spec.md:L44-L46`, § Verified Claims. |
| T2 | Ignored suite launch and restoration | The saved-form `current` case exercises the same real helper as T1. | Add the one proof in § 3. On starting commit `970f6a4ca`, its selected case must fail at the existing stop wait; after the fixture change it must pass. Require exactly the selected case to run, with no skip or expected failure, and require the driver's original `SIG_IGN` after pytest returns. |
| T3 | Full-suite collection, plus the existing local selection contract | The collection hook currently only admits explicitly named `e2e/` paths (`products/tracker17/tests/conftest.py:L33-L48`, `_command_line_names_end_to_end` and `pytest_ignore_collect`). | Within the same new proof, use isolated collection-only invocations to check that the request's repository-root test-directory argument collects nonempty `unit`, `integration`, `e2e` and `architecture` sets. Check that the documented product-local `tests/` command still excludes `e2e`, and that explicitly naming `tests/e2e/` includes it. Collection-only calls do not execute the collected proof. |
| T4 | Whole suite, foreground and ignored-SIGINT launches | Keep all assertions across all four test folders, including the end-to-end stop/restart tests. | Both exact request commands below must exit 0 after the change. Retain collected node IDs or the per-folder collection evidence from T3 so an omitted browser suite cannot count as a pass. |
| T5 | Product entry points and both inherited signal dispositions | The test fixture operates only inside pytest; production entry points remain byte-for-byte unchanged. | Review the production diff as empty and run the existing start/command checks in T4. No test-only handler setup is added to `main.py` or to the real-start child program. The direct-start ignored-disposition behavior is left untouched by construction. |
| T6 | Saved-data and failure-path continuity | Existing start tests include unreadable data and refusal paths, while each of the twelve cases checks unchanged bytes and file listing (`products/tracker17/tests/integration/test_start.py:L52-L109,L538-L588,L691-L758`, the start/refusal and real-start tests). | Covered by T1 and T4. Retain the existing cleanup and stop bounds; no timeout is raised to obtain green. Fixture teardown restores the saved handler on unsuccessful sessions as well as successful ones. |
| T7 | Test trace and language gates | `change_spec.md:L24-L26`, § Invariants, names QC-11, TS-2/TS-3 and QC-62. | Keep the proof in the existing requirement-naming module. Name FR-1 and the existing saved-data requirements in its docstring. No new module or dependency is needed. Run the existing trace check and the three QC-62 commands below. |

From the repository root, with the product's locked test environment active:

```sh
python -m pytest products/tracker17/tests/ -q
sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'
```

From the product root, the unchanged QC-62 commands:

```sh
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

The new proof's baseline failure is a check to perform, not a result claimed by this design. No suite or acceptance run was executed in this architect stage.

---

## Records this change makes false

None — read `products/tracker17/docs/adr/README.md` and ADR-0001 through ADR-0012, `products/tracker17/docs/nfdr.md` §§ 1–10, `products/tracker17/docs/fdr.md` and `products/tracker17/docs/SDD.md` § 3. No production ownership or interface changes. The product-local split described by NFDR § 9 and SDD § 4 RT-4 remains intact under § 3's collection boundary. `products/tracker17/README.md:L91-L105`, § Running the tests, remains accurate, so no product document is edited.

---

## Architect Review Notes

Decisions below are the architect's, 2026-10-29.

- **(d) Preserving test repair, not relocation.** The spec's § Structural Goal asks for a test-side launch fix, not a package move (`change_spec.md:L30-L34`). Use the preserving template's sections but describe test-support changes rather than falsely marking them as file-location-only. No production symbol moves and no `__init__.py` export is added, removed or changed.
- **(a) Whole-suite coverage versus narrow test scope.** The request and spec require the two repository-root commands to cover all four test folders (`change_spec.md:L6,L19,L32`). The existing hook excludes `e2e/` for that argument (`products/tracker17/tests/conftest.py:L33-L48`, `pytest_ignore_collect`). Take the reading that permits the shared test-support change necessary for that explicit acceptance boundary while preserving all existing test bodies and local command contracts. Set aside the reading of § Out of Scope that would prohibit this support change; the companion records it. A fix confined to `RUN_START` would repair the twelve cases but leave the requested browser coverage absent. Including browser tests in every product-local run would instead break the documented separate command, so that reading is also rejected. No verified suite total in the spec substitutes for actual collection evidence.
- **(b) Session signal setup and exact restoration.** Choose the shared session fixture because the full-suite request also reaches real tracker processes started by `products/tracker17/tests/e2e/conftest.py:L76-L113`, `TrackerFactory.start`. Its SIGINT stop path is at `products/tracker17/tests/e2e/conftest.py:L54-L62`, `RunningTracker.stop`. This fixes launch conditions without editing those tests, and the spec explicitly permits a fix that also covers them (`change_spec.md:L57`, § Out of Scope). Restoration prevents a completed nested pytest session from silently changing its caller's signal policy. A permanent module-import signal change is rejected because it has no matching lifetime or restoration boundary.
- **(b) Collection by invocation context.** Preserve the documented product-local command and add only the outer explicit whole-directory case. Resolve paths and invocation directory deliberately so the request is satisfied by construction rather than by test order or by an assumed suite count. T3 pins both sides of the boundary inside the one allowed new proof.
- **Test-support placement.** SDD § 3's parts table assigns no pytest lifecycle or collection responsibility to a product part (`products/tracker17/docs/SDD.md:L206-L214`, the parts table). Keep that logic in the existing test harness. No forbidden import must be relaxed.
- **QC-12 — pass.** Two existing test-support files, one fixture and one characterization proof add no product part, port or abstraction. The extra collection boundary is paid for by the request's explicit all-folder acceptance check; NFDR § 1.1 QC-12 asks whether a part lacks such a requirement (`products/tracker17/docs/nfdr.md:L158-L164`).
- **QC-40 — pass under the existing browser exception.** The dated feed checks below cover the lock's fifteen pins (`products/tracker17/tests/requirements.txt:L4-L18`, the exact dependency list). The results are from that advisory feed, not a claim of universal absence. No pin or lock format changes. Playwright's pinned [browser manifest](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json) specifies Chromium 153.0.8010.12. Google's [October release notices](https://chromereleases.googleblog.com/2026/10/?amp=1) publish newer browser security fixes, including critical fixes. The owner already permits exactly that pinned build through 2026-11-07 (`products/tracker17/docs/nfdr.md:L1050-L1062`, RN-33, “Dated exception to QC-40”). This review is inside that window; it neither moves the pin nor renews the exception.
- **QC-41 — pass.** This design adds no credential, secret or external product service; its only subprocesses are local test processes. The gate is `products/tracker17/docs/nfdr.md:L379-L383`, QC-41.
- **QC-60 — pass by API review, not an interpreter run.** `signal.getsignal`, `signal.signal`, `signal.default_int_handler` and `SIG_IGN` are documented in [Python 3.11's signal reference](https://docs.python.org/3.11/library/signal.html). `subprocess` is documented in [Python 3.11's subprocess reference](https://docs.python.org/3.11/library/subprocess.html). Use no newer language syntax or library feature. This review does not claim that the suite ran on Python 3.11.
- **Other delegated gates — not triggered.** The `development-design` sweep of NFDR QC-5, QC-8, QC-20 through QC-27, QC-36 and QC-46 found gates for refusal handling, production rules/state, persistence replacement, page building or saved fields; none is changed in § 2 (`products/tracker17/docs/nfdr.md`, the named entries' `verified by` tails). ADR-0001 through ADR-0012 name no separate gate delegated to this stage. QC-12, QC-40, QC-41 and QC-60 are reviewed above.

### QC-40 feed checks — 2026-10-29

Each row records the `vulnerabilities` field returned by a read-only GET of that exact PyPI release URL during this run.

| Exact release queried | Returned field |
|---|---|
| [ast_serialize 0.12.1](https://pypi.org/pypi/ast_serialize/0.12.1/json) | `[]` |
| [greenlet 3.5.6](https://pypi.org/pypi/greenlet/3.5.6/json) | `[]` |
| [iniconfig 2.3.1](https://pypi.org/pypi/iniconfig/2.3.1/json) | `[]` |
| [librt 0.16.0](https://pypi.org/pypi/librt/0.16.0/json) | `[]` |
| [mypy 2.4.0](https://pypi.org/pypi/mypy/2.4.0/json) | `[]` |
| [mypy_extensions 1.1.0](https://pypi.org/pypi/mypy_extensions/1.1.0/json) | `[]` |
| [packaging 26.3](https://pypi.org/pypi/packaging/26.3/json) | `[]` |
| [pathspec 1.1.1](https://pypi.org/pypi/pathspec/1.1.1/json) | `[]` |
| [playwright 1.63.0](https://pypi.org/pypi/playwright/1.63.0/json) | `[]` |
| [pluggy 1.6.0](https://pypi.org/pypi/pluggy/1.6.0/json) | `[]` |
| [pyee 13.0.1](https://pypi.org/pypi/pyee/13.0.1/json) | `[]` |
| [Pygments 2.21.0](https://pypi.org/pypi/Pygments/2.21.0/json) | `[]` |
| [pytest 9.1.1](https://pypi.org/pypi/pytest/9.1.1/json) | `[]` |
| [ruff 0.16.10](https://pypi.org/pypi/ruff/0.16.10/json) | `[]` |
| [typing_extensions 4.16.0](https://pypi.org/pypi/typing_extensions/4.16.0/json) | `[]` |
