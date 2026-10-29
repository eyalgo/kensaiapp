# Change Design — prove the ignored-SIGINT fixture through a real start

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** preserving
**Publishes text:** no
**Language resolution:** Python — project card `Languages:`; `<CORE>/doctrine/engineering/languages/python/README.md`, with its seven routed concerns read.

---

## 1. Change Summary

This blueprint places the one characterization test and the docstring reflow required by
`tracker17 · tobiishi · 2026-10-29_ignored-sigint-proof-test`, `change_spec.md` § Structural Goal.
The architect's layout decision, 2026-10-29, is to add
`products/tracker17/tests/integration/test_sigint_launch.py` with exactly one test,
`test_real_start_stops_when_pytest_launch_ignores_sigint`.

The proof will start a child pytest with SIGINT explicitly ignored and select one existing
real-start case. The test will require that case to pass. The existing case calls `main.start`
in another process, sends SIGINT, and asserts exit 0, empty standard error and unchanged saved
data (`products/tracker17/tests/integration/test_start.py:L516-L563`, `_run_real_start` and
`test_start_reads_each_legacy_form_with_every_existing_value`). No product behaviour or public
import changes are designed.

The output belongs beside the spec in the change folder, per
`<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, `journey/tobiishi/<key>/`.
Paths beginning `products/` are instance-relative. Shorter code and `docs/` paths are relative
to the product root, `products/tracker17/`; `change_spec.md` names this change's sibling spec.

---

## 2. Blast Radius

No transitive blast radius — public surfaces unchanged. The production module set and forbidden
edges are `products/tracker17/docs/nfdr.md:L166-L197` § 1.2; every production part stays unchanged.
The parts table exists at `products/tracker17/docs/SDD.md:L202-L238` § 3.
This preserving change adds no product logic to place in one of those parts.

| Module | Status | What changes |
|---|---|---|
| `products/tracker17/domain/` | Unchanged | — |
| `products/tracker17/application/` | Unchanged | — |
| `products/tracker17/persistence/` | Unchanged | — |
| `products/tracker17/web/` | Unchanged | — |
| `products/tracker17/main.py` | Unchanged | Existing start signatures and signal handling remain the subject of the tests. |
| `products/tracker17/errors.py` | Unchanged | — |
| `products/tracker17/tests/integration/test_sigint_launch.py` | New (characterization only) | One test of the existing session fixture's effect across the pytest-to-tracker process boundary. |
| `products/tracker17/tests/conftest.py` | Modified (docstring reflow only) | Rebreak the opening paragraph so its first line fits 100 columns, preserving every word and their order. |
| `products/tracker17/tests/integration/test_start.py` | Unchanged | Supplies the existing case selected by the new test; no body, assertion or helper changes. |
| `products/tracker17/tests/e2e/` | Unchanged | Both end-to-end launches remain continuity checks. |

The two changed files have no interface or ordering dependency on each other. There is no
atomic-landing edge and no module build sequence.

---

## 3. Layout Plan

### The proof module

**New named module:** `products/tracker17/tests/integration/test_sigint_launch.py`.

| Symbol | Kind | Target module |
|---|---|---|
| `test_real_start_stops_when_pytest_launch_ignores_sigint` | Characterization test | `tests/integration/test_sigint_launch.py` |

No implementation symbol moves. No `__init__.py` is affected, so there is no symbol inventory to
relocate and no re-export change. Any local scaffolding belongs in the new test module; it adds
no production interface.

The architect's process-boundary decision, 2026-10-29:

1. Run the child from the product root derived from the test file's own location. Use the same
   interpreter as the outer pytest. Python recommends `sys.executable` with `-m` for this purpose
   ([Python subprocess documentation](https://docs.python.org/3.11/library/subprocess.html#popen-constructor)).
2. Have `/bin/sh` ignore INT and then exec that interpreter into pytest. Pass the interpreter
   and pytest arguments as positional arguments to the shell rather than interpolated path text.
   The ignored condition must be established inside the child launch, after the outer session's
   fixture has already run. Neither the outer test nor the tracker launch resets it to default.
3. Select exactly
   `tests/integration/test_start.py::test_start_reads_each_legacy_form_with_every_existing_value[projects-only]`.
   Do not select the enclosing directory or the new module, which would recurse. That exact case
   exists both on this branch and at `970f6a4ca04b93093d36873737a1087286a9a844`
   (`git show 970f6a4ca:products/tracker17/tests/integration/test_start.py`, lines 537–563).
4. Require child pytest exit 0 and evidence that exactly one test passed, with captured output
   attached to a failure. This prevents a non-executed or skipped case from passing the proof.
   Let the unchanged child case exercise the real start and the actual SIGINT.
5. Bound the outer wait above the selected case's 30-second stop timeout. Preserve the child
   failure output so the historical check can distinguish `TimeoutExpired` during the tracker
   stop from import, collection or setup failures. Child processes must be reaped on failure;
   the existing tracker helper already kills and waits for a tracker that remains running
   (`products/tracker17/tests/integration/test_start.py:L516-L535`, `_run_real_start`).

The new module's opening docstring will name SRS NFR-11 and explain that it checks the suite's
launch condition through the existing real-start case. SRS NFR-11 is the test requirement served
by SDD TS-1 and TS-2 (`products/tracker17/docs/SDD.md:L557-L564`, Tests and the trace).
No existing feature-entry docstring needs a new participant: this proof guards the test launch
condition rather than a Core Feature's domain rule.

### The shared docstring

The opening paragraph of `products/tracker17/tests/conftest.py` retains its words and order;
only the break between its first two lines changes. Its first line is currently 101 columns
(`python3` reading that line and printing `len(...)` returned `conftest line 1 columns: 101`).
All executable statements, fixture bodies and collection decisions remain byte-identical.

---

## 4. Code Strategy

| Module / change | Hint |
|---|---|
| `tests/integration/test_sigint_launch.py` — one characterization test | Use an ignored-INT shell launch of one explicit pytest node, under the current interpreter, with a bounded captured result. The extra pytest process is essential: the outer fixture has already normalized SIGINT, so directly starting another tracker from the outer test would not recreate the defect. No fixture-name import, handler replacement in the subject, or `preexec_fn` is needed. |
| `tests/conftest.py` — opening docstring reflow | None |

No persistent write outside the change's own repository is part of the implementation.

---

## 5. Test Continuity

Exactly one characterization test is added; no test for new product behaviour is designed.
No existing assertion is retired, weakened or replaced. The spec's Invariants and Structural Goal
are the continuity contract (`change_spec.md:L17-L45`).

| Row | Surface or invariant | Existing coverage / required proof |
|---|---|---|
| C1 | Proof properties 1, 2, 3 and 5 | Add only `tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint`. Run this node in the foreground and under the ignored-INT wrapper at the commit under test; both must pass. The card suite must collect it once. |
| C2 | Proof property 4: missing fixture exposes the failed stop | In a separate disposable clone at `970f6a4ca04b93093d36873737a1087286a9a844`, add only the same new proof module, then run its node in the foreground. It must fail because the selected case's real tracker does not stop on SIGINT, evidenced by that case's stop timeout or a still-running tracker. A missing dependency, skipped case, import error, collection error or outer deadline is not this proof. Keep the old conftest and product code intact. |
| C3 | Both suites under both incoming signal dispositions | In a disposable clone of the resulting commit, run the four repository-root commands below. Each must exit 0. Existing start tests keep every assertion; the proof is part of the first suite and not added to the separate browser suite. |
| C4 | Default-SIGINT operator stop, saved bytes and directory listing | Keep every existing `_run_real_start` caller unchanged. C3's foreground suite still exercises real `main.start`, SIGINT, exit 0, empty standard error and the saved-data assertions; the representative child case retains those checks (`tests/integration/test_start.py:L537-L563`). |
| C5 | Public symbols, signatures, fixtures, collection and document boundaries | Review the product diff: only the new test module and opening docstring line breaks may differ. This preserves `main.start`, `main.main`, all existing imports, the fixture, collection and every product document by construction. |
| C6 | Reflow preserves the docstring, and line 1 fits 100 columns | Compare the opening docstring's whitespace-split words before and after; require equality. Measure the resulting first line at no more than 100 columns and require no rewrap elsewhere. This is a reading/measurement, not another added test. |
| C7 | Trace pointers and collaborator boundaries | C3 includes the unchanged `tests/architecture/test_trace.py` pointer checks. The new module names NFR-11 and uses real process boundaries without patching a product name, per `docs/nfdr.md` QC-11 and QC-28. |
| C8 | Formatting, lint and types | From the product root of the disposable clone, require `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` to exit 0 at the pinned versions, per `docs/nfdr.md:L532-L545`, QC-62. |

The four C3 commands, from the disposable clone's repository root:

```sh
python -m pytest products/tracker17/tests/ -q
sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'
python -m pytest products/tracker17/tests/e2e/ -q
sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/e2e/ -q'
```

C2 is one-off validation, not code inside the lasting test. The committed test reads no Git
history, checks out no revision and needs no primary checkout. Its only data and modules are
the committed tree and the temporary saved-data location the selected case creates.

There is no Examples table or Rules section in this preserving spec. The second coverage pass
therefore covers each Invariant and Structural Goal: suite continuity C3; public interface C5;
operator stop C4; unchanged real-start cases C4/C5; document boundary C5; trace C7; collaborator
boundary C7; quality gates C8; proof properties C1/C2; reflow C6; tests-only boundary C5.
The ignored-launch failure path is covered by C2, and non-execution or unrelated failures are
rejected by C1/C2 rather than counted as a successful historical demonstration.

---

## Records this change makes false

None — read `products/tracker17/docs/adr/` (index and ADR-0001 through ADR-0012),
`products/tracker17/docs/nfdr.md` §§ 1–10 and RN-33,
`products/tracker17/docs/fdr.md`, and `products/tracker17/docs/SDD.md` § 3 and § 4 Tests and the
trace. The designed delta adds no production part, import edge, behaviour, dependency or saved
field. The NFDR QC-62 reference to two conftest files remains true: neither is added or removed.

---

## Architect Review Notes

- **Shape departure (d), architect decision, 2026-10-29:** use the preserving template with a
  characterization-only new-file row and a docstring-only modified row instead of calling either
  a relocation. The spec expressly asks for a new test and a reflow, with no symbol move.
  `<CORE>/doctrine/flow/change_classification.md` § Constraints permits added characterization
  tests on a preserving change. Layout inventory and re-exports are therefore explicitly
  inapplicable, while all public surfaces remain fixed.
- **Realization by construction (b), architect decision, 2026-10-29:** the extra pytest process,
  explicit ignored launch, exact existing node and positive one-pass result realize the proof
  properties even when the outer suite starts in the foreground. A direct extra call to the
  tracker from the already-normalized outer pytest would not isolate fixture loss. This follows
  from `tests/conftest.py:L62-L82`, `_interruptible_test_session`, and
  `tests/integration/test_start.py:L516-L563`, the real-start helper and its selected caller.
- **Failure evidence (b), architect decision, 2026-10-29:** the outer wait must outlast the inner
  stop deadline and preserve the inner report. Otherwise an outer timeout could obscure the
  historical failure that Structural Goal property 4 requires. No numeric outer deadline is
  added to the product's contract.
- **Delegated review — QC-12: pass.** One test module reuses an unchanged real-start case and
  introduces no production part. That meets the simplicity review delegated by
  `products/tracker17/docs/nfdr.md:L158-L164`, QC-12.
- **Delegated review — QC-41: pass.** The design adds no account, credential or secret; it uses
  committed code and a temporary saved-data location, satisfying the review at
  `products/tracker17/docs/nfdr.md:L379-L383`, QC-41.
- **Delegated review — QC-60: pass by API review.** The planned process calls, current-interpreter
  launch and captured bounded result exist in the Python 3.11
  [subprocess documentation](https://docs.python.org/3.11/library/subprocess.html).
  No newer language feature or dependency is required. This is not a claim of an executed
  Python 3.11 suite run.
- **Delegated review — QC-40: pass under the existing browser exception, checked 2026-10-29.**
  Read every pin in `products/tracker17/tests/requirements.txt` and queried each version's PyPI
  JSON endpoint (`https://pypi.org/pypi/<name>/<version>/json`): all 15 responses returned
  `vulnerabilities: []`. This is the public feed's result, not a claim that unknown advisories
  cannot exist. The expected browser is `153.0.8010.12`
  (`products/tracker17/tests/e2e/test_moves.py:L515-L515`, `PINNED_BROWSER`, asserted at L604).
  [Google's 2026-10-27 desktop release](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html)
  lists newer critical browser fixes. The pinned browser is not declared current or free of
  those issues. The owner's dated exception covers that exact build through 2026-11-07
  (`products/tracker17/docs/nfdr.md:L1049-L1061`, RN-33), so the browser does not block this
  review. No pin or lock format changes are designed.
- **Delegated-review sweep:** `rg -n 'development-design'` over the NFDR and ADR directory found
  stage gates in the NFDR and none in the ADR records. QC-5, QC-8, QC-20–QC-27, QC-36 and QC-46
  are unaffected: this design changes no refusal, production part, page construction, saving
  contract or saved field. Their conditions and review scopes remain at
  `products/tracker17/docs/nfdr.md` §§ 1.1, 1.3, 1.4, 2 and 4.
- **Cold read:** all Invariants and Structural Goal items map to C1–C8; no signature, importable
  production symbol or existing assertion changes. There is no affected `__init__.py`, module
  name collision, per-symbol import wiring, new dependency edge or persistent foreign-repository
  write. `Publishes text: no` is settled. This design run reads the code and records but executes
  no product suite; C1–C8 describe the evidence the implementation must establish.
