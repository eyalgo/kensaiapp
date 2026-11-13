# Change Design — the ignored-SIGINT proof test holds in a full run

**Date:** 2026-11-13
**Category:** bug
**Behaviour:** preserving
**Publishes text:** no
<!-- A preserving change adds no words, so the line is always `no`. Moving existing text is placement, and placement is the Developer's. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `<CORE>/doctrine/engineering/testing_python.md`)

Paths are relative to the product (`system/projects/tracker17/project.md` `Product path:`) unless
they say otherwise.

---

## 1. Change Summary

**The cause is in the test's own setup, not in the start's stop path.** The proof test launches a
second pytest and gives it nothing but a test to run. So that pytest takes its base folder from the
temp root every pytest session on the machine shares (`pytest-of-<user>` under the system temp
folder). When it exits, it does what every pytest session does there: it deletes each earlier
session folder that is three or more numbers below the newest and holds no live lock. A lock older
than pytest's three-day lock timeout counts as dead. How long that takes depends on what other
sessions left behind, and all of it is inside the proof test's 120-second outer limit
(`OUTER_DEADLINE_SECONDS`). The selected case's 30-second wait is not involved, because the clean-up
runs after that case has finished.

Measured at the base `8c3f7e74d` on 2026-11-13, in this change's worktree:

- With the shared root holding a leftover full-run folder of about 296,000 entries, one run of the
  proof test alone took `1 passed in 34.79s` instead of its usual 0.7–1.3 s, and the leftover was
  gone afterwards.
- The shared root held 18 more session folders with stale locks, dated 2026-11-10 onwards, some of
  about 300,000 entries each. Each is deleted by the first session that exits after its lock passes
  three days, and several fall due within hours of each other.
- Load alone does not cause the failure. 150 runs of the selected case launched with SIGINT ignored,
  with 20 CPU-bound processes running beside them, and one full run of `tests/` (3335 passed) all
  passed.

The run that failed did not keep its output, so this is a match by mechanism, not by a matched log.
It is the one step in the test's chain whose length depends on the machine's history, and it runs
inside the test's limit.

The fix gives the launched pytest a base folder of its own, under the proof test's `tmp_path`, so it
never makes or cleans a numbered session folder in the shared root. A new layer-2 test measures the
dependence by its effect. It runs the proof test against a private temp root that holds a leftover
session pytest would delete, and asserts that the root is untouched. That fails on the base on every
run and passes after the change. No product module, public name or wait limit changes.

---

## 2. Blast Radius

No transitive blast radius — no product module changes and no public surface (spec I-2) changes, so
no importing module is affected. No new logic lands in a product part. Every piece is test code,
which SDD § 3's parts table does not cover (Architect Review Notes, kind (e)).

| Module | Status | What changes |
|---|---|---|
| `domain/`, `application/`, `persistence/`, `web/` | Unchanged | — |
| `main.py`, `errors.py` | Unchanged | — (the stop path `SigintStopRequests`, `serve_until_stopped` and `Listener.serve_until` is not where the cause sits) |
| `tests/integration/test_sigint_launch.py` | Modified (test setup only) | `test_real_start_stops_when_pytest_launch_ignores_sigint` takes `tmp_path`. The launched command adds `--basetemp` with a folder under it. The module docstring says why: a launched pytest given no base folder cleans the machine's shared temp root inside the outer limit. The assertions, `SELECTED_CASE`, `IGNORE_INTERRUPT_THEN_RUN`, `OUTER_DEADLINE_SECONDS` and `ONE_CASE_PASSED` do not change |
| `tests/integration/test_sigint_launch_temp_root.py` | New | The measurement (spec I-4) |
| `tests/integration/test_start.py` | Unchanged | The selected case and `_run_real_start`, with its `timeout=30`, stay as they are |
| `tests/conftest.py` | Unchanged | `_interruptible_test_session` is still what the proof test shows from outside |
| `tests/architecture/test_trace.py` | Unchanged | Reads the new module's docstring (spec I-7) |

---

## 3. Layout Plan

No product module moves. The layout decided here is where the measurement lives, and the one setup
change in the proof test's module. `tests/integration/` has no `__init__.py`, and the product's
`__init__.py` re-exports are not touched.

Neither file depends on a contract the other adds, so there is **no build sequence**. The new test
is red at the base until the setup change lands (§ 5). Ordering those two is `development-plan`'s.

### `tests/integration/test_sigint_launch_temp_root.py` (new)

| Symbol | Kind | Target module |
|---|---|---|
| `test_launched_pytest_leaves_the_shared_temp_root_alone` | test function | `tests/integration/test_sigint_launch_temp_root.py` |
| the nested run's deadline | module constant | `tests/integration/test_sigint_launch_temp_root.py` |

### `tests/integration/test_sigint_launch.py` (modified)

| Symbol | Kind | Target module |
|---|---|---|
| `test_real_start_stops_when_pytest_launch_ignores_sigint` | test function (gains `tmp_path`) | `tests/integration/test_sigint_launch.py` (stays) |
| `PRODUCT_ROOT`, `SELECTED_CASE`, `IGNORE_INTERRUPT_THEN_RUN`, `OUTER_DEADLINE_SECONDS`, `ONE_CASE_PASSED` | module constants | `tests/integration/test_sigint_launch.py` (stay, values unchanged) |

---

## 4. Code Strategy

| Module | Hint |
|---|---|
| `tests/integration/test_sigint_launch.py` | The launched pytest takes `--basetemp` pointing at a folder that does not yet exist under the test's own `tmp_path`. Given a base folder, pytest uses that folder, deleting it first if it exists, and never makes a numbered session folder or cleans the shared root. Put the option in the argument list after `-p no:cacheprovider` and before `SELECTED_CASE`, so the shell trap and `exec "$@"` stay as they are. |
| `tests/integration/test_sigint_launch_temp_root.py` | (1) **Root:** make a private temp root under `tmp_path`. Inside it, make the user folder pytest would make, `pytest-of-` followed by `getpass.getuser()`. In that folder plant a leftover session that a pytest exit would delete: a `pytest-1` holding a file and no `.lock`, and a newer `pytest-5`, so that any new session is numbered at least three above the leftover. Take a listing of the private root. (2) **Run:** launch `sys.executable -m pytest -q -p no:cacheprovider` from `PRODUCT_ROOT` on the proof test's node id alone, never the whole module. Give it `--basetemp` under `tmp_path`, so this nested run never touches the private root itself. Give it an environment that copies `os.environ` and adds `PYTEST_DEBUG_TEMPROOT` set to the private root. That variable is the temp root pytest reads, and the proof test's launched pytest inherits it. Hand the environment to `Popen`, not to `monkeypatch`. (3) **Deadline:** start the run in a new session, wait on a module constant longer than `OUTER_DEADLINE_SECONDS`, for the same reason that one is longer than the selected case's 30 seconds, and on expiry kill the process group and fail with both outputs, as the proof test does. (4) **Assert:** the nested run exited 0 and reported exactly one case passed (reuse `ONE_CASE_PASSED`), and the private root's listing equals the one taken before. At the base the second assertion fails on every run: the launched pytest makes `pytest-6` and deletes `pytest-1`. (5) **Imports:** take only names `test_sigint_launch.py` already has at the base (`PRODUCT_ROOT`, `OUTER_DEADLINE_SECONDS`, `ONE_CASE_PASSED`), so the red at the base is on the assertion, not an `ImportError`. (6) **Docstring:** name the cause in words, with SRS NFR-11 and SDD § 4 TS-2. Name no path that does not exist under the product root, because `test_trace.py` resolves every path-shaped token in it, and write no planted file name ending `.py`, `.md`, `.toml`, `.txt` or `.css`. (7) Python 3.11 is enough (QC-60). `getpass`, `subprocess`, `pathlib` and pytest 9.1.1's `--basetemp` and `PYTEST_DEBUG_TEMPROOT` are all that is needed. |

---

## 5. Test Continuity

The existing suite is the characterization contract and keeps every assertion (spec I-1). The one
test added measures the test setup, not new product behaviour. It is red at the base by design
(spec I-4) and green after the setup change.

| Sub-job | Test file | Layer | Fakes handed in | What to add / modify |
|---|---|---|---|---|
| measurement | `tests/integration/test_sigint_launch_temp_root.py` | 2 — Integration | none: real pytest processes and a real tracker; the private temp root and both base folders sit under `tmp_path` | **I-4:** new `test_launched_pytest_leaves_the_shared_temp_root_alone` (§ 4). Fails at `8c3f7e74d` on the listing assertion, on every run, with no full run, and passes after. Its docstring names the cause |
| proof setup | `tests/integration/test_sigint_launch.py` | 2 — Integration | none, as at the base | **I-3:** the launched pytest gets its own base folder. It still asserts `launch.returncode == 0` and one `ONE_CASE_PASSED` line, and still selects the same case, which still asserts `(status, errors) == (0, b"")` |
| — | `tests/integration/test_start.py` | 2 | — | No change. The selected case keeps `communicate(timeout=30)` (I-5) |
| — | `tests/integration/test_start_stop.py` | 2 | — | No change. `test_arming_preserves_an_inherited_ignored_sigint` still holds the Out-of-Scope boundary: the fix does not make an ignored SIGINT caught |
| — | `tests/architecture/test_trace.py` | 6 | — | No change. Checks the new module's and the edited module's docstrings (I-7) |

Coverage by invariant, beyond the rows above:

- **I-1, I-9:** both commands of `Test command:` in full from the change worktree root, and the three
  code gates from the product root, are gate commands, not tests.
- **I-2:** no product file changes. `git diff 8c3f7e74d..HEAD --stat -- products/tracker17` lists
  only the two test modules.
- **I-5:** neither `timeout=30` nor `OUTER_DEADLINE_SECONDS = 120` moves. The new constant is a new
  limit on a new run, not a raise of either. The spec's grep must print nothing, so no added line
  may carry `retry`, `flaky`, `reruns`, `xfail` or a skip mark, in a name or a comment either.
- **I-6, I-8:** the measurement patches no name and defines no class. It hands its collaborators,
  the environment and the base folders, to the processes it starts.
- **I-10:** Architect Review Notes, QC-12.

**What the change stops proving.** Nothing. No assertion is retired. The proof test no longer
measures how fast the machine's shared temp root can be cleaned, and that was never a clause it
proved.

---

## Records this change makes false

None — read `docs/adr/` (the index and ADR-0001 to ADR-0016), `docs/fdr.md`, `docs/SDD.md` § 3 and
§ 4 TS-1 to TS-6, `docs/nfdr.md` § 1.2 and every clause naming `development-design`, and `docs/SRS.md`
NFR-11. The one record that names the proof test, SDD RN-64, records what a past round read, and it
stays true.

---

## Architect Review Notes

- **(b) The dependence is measured by its effect, not by elapsed time:** an assertion that the run
  took under some number of seconds would be red or green depending on the machine, which is the
  very failure the spec rules out (I-4, "on every run"). The leftover session's survival is decided
  by pytest's own clean-up rule, so the measurement is deterministic.
- **(a) The request points at the 30-second wait, and the cause is the 120-second outer limit:** the
  request and the spec's I-5 name the selected case's 30-second wait. The clean-up runs after that
  case finishes, inside `OUTER_DEADLINE_SECONDS`. Neither limit moves, which is all I-5 asks. The
  spec's Structural Goal allows the fix in the test's setup with the product left alone, and this
  design takes that branch. No spec line is set aside, so no `deferred_decisions.md` entry is owed.
- **(d) A preserving change with no relocation:** the template's relocation shape (symbol moves,
  `__init__.py` re-exports) has nothing to place here. § 3 records where the measurement lives
  instead, and § 2 marks the edited module "test setup only".
- **(e) Test code has no owning part:** both files sit in `tests/integration/`, by
  `testing_python.md` § Layers 1–5 (layer 2) and beside the proof test they measure. SDD § 3's `Owns`
  column covers the five product parts, and `tests/` is none of them.
- **(d) A separate module for the measurement:** it runs the proof test by node id. Kept in the proof
  test's own module, selecting the module rather than the node would make the test run itself.
- **Packet check, no conflict:** both tests are layer 2. Their subject is real processes, which
  `testing_python.md` § Layers 1–5 puts at that layer. They write only under `tmp_path`, and hand the
  launched processes their environment and folders instead of patching anything. No unit test
  touches a real resource, and no module builds its own collaborator.
- **QC-12 review (spec I-10), pass:** the change adds no part. It adds one option to one launched
  command and one integration test, both paid for by SRS NFR-11's proof holding in a full run.
- **QC-60 review, pass:** the change uses only Python 3.11 standard library calls, plus pytest
  9.1.1's `--basetemp` option and `PYTEST_DEBUG_TEMPROOT` variable, both present at the pin.
- **QC-41 review, pass:** the change reads, holds and writes no secret.
- **QC-40 review, every-review moment — packages, met:** all 27 pinned packages in `uv.lock` and
  `.behave/uv.lock` were checked against the OSV database's PyPI advisories on 2026-11-13. None has
  an advisory. No dependency is added or moved.
- **QC-40 review, every-review moment — browser build, not blocking, owed by 2026-12-11:** the build
  `playwright==1.65.1` installs is Chromium 158.0.8127.18. The vendor's Stable Channel Update for
  Desktop of 2026-11-11 (157.0.8103.78) fixes five Critical advisories: CVE-2026-126885,
  CVE-2026-126895, CVE-2026-126879, CVE-2026-126846 and CVE-2026-126911. The vendor's feed, read on
  2026-11-13, holds nothing newer with a Critical advisory. Its latest early-stable build is
  158.0.8127.36, from 2026-11-12. The vendor does not say whether the pinned build carries those
  fixes, so this review reads it as affected. The advisories are 2 days old, inside the 30-day
  window, so they do not block this change. The fix is owed within 30 days of 2026-11-11: the pin
  moves, or the owner records a dated exception.
- **QC-40 review, package feed — down, moment still owed:** the checking account has admin on the
  repository that holds tracker17. The Dependabot alerts endpoint answered "Dependabot alerts are
  disabled for this repository" (403), and the asynchronous SBOM export answered 404. As QC-40 says,
  that is a feed that is down: this review records the feed as down and the moment as still owed,
  and raises no discrepancy.
