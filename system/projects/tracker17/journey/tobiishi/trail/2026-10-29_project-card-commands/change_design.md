# Change Design — the project card sets up and runs the suite through uv

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** no
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md:12`, `Languages:`; opened `core/doctrine/engineering/languages/python/README.md` § The seven concerns and where each is answered.

This blueprint owns the command boundaries and the checks for the two project-card values in `tracker17 · tobiishi · 2026-10-29_project-card-commands`.

---

## 1. Change Summary

Change only the Setup and Test values in `system/projects/tracker17/project.md`, as required by the change's `change_spec.md` § Rules, CP-685–CP-692 (`:23-36`). Setup selects the product explicitly and makes its locked environment from either the repository root or the product directory. Test selects that same product and runs the two complete suites in separate processes, refusing a stale lock in each process. The existing values are on `system/projects/tracker17/project.md:10-11`, `Test command:` and `Setup command:`.

The implementation is one card delta. There is no module split, public-interface change or new product file: CP-691–CP-692 fix the edit boundary (`change_spec.md:35-36`, § What the change touches).

## 2. Blast Radius

**Placement decision — Architect, 2026-10-29.** Put project selection, lock enforcement and the two-suite exit contract in the card's command values. No part in `products/tracker17/docs/SDD.md:212-218`, § 3 The parts, owns suite setup or execution: its five rows own tracker rules, actions, storage, browser pages and composition. The card owns the execution context and suite command by `products/tracker17/docs/nfdr.md:541-544`, § 8 Operational constraints. This is tooling outside the product parts table, not a sixth product part.

| Module | Status | What changes |
|---|---|---|
| `system/projects/tracker17/project.md` | Modified | The card owns the new tooling logic: location-independent Setup project selection, locked synchronization, and locked execution of both complete suites with failure propagated. Only the two values change (CP-685–CP-692). |
| `products/tracker17/domain/` | Unchanged | No rule, symbol or import changes; CP-692. |
| `products/tracker17/application/` | Unchanged | No action, protocol or import changes; CP-692. |
| `products/tracker17/persistence/` | Unchanged | No saving, loading, lock or import changes; CP-692. |
| `products/tracker17/web/` | Unchanged | No route, page, wording or import changes; CP-692. |
| `products/tracker17/main.py` | Unchanged | No composition or interpreter-selection changes; CP-692. |
| `products/tracker17/errors.py` | Unchanged | No exception or import changes; CP-692. |
| `products/tracker17/tests/`, `pyproject.toml`, `uv.lock` | Unchanged | Existing collection, assertions and pins remain the subject of the command checks; `change_spec.md:81-89`, § Out of Scope. |
| `products/tracker17/README.md` | Unchanged | Its commands explicitly enter the product directory and run both suites through uv (`:95-107`, § Running the tests); the card edit makes none of those instructions false. |
| `core/tools/create_change_worktree.py`, `core/tools/gate_suite.py` | Unchanged | Setup is consumed in the product directory (`create_change_worktree.py:472-476`, `run_setup`); Test is consumed at the product-worktree root (`gate_suite.py:2140-2149`, `run_gate`). Accommodate those directories in the card. |

The module set and forbidden imports remain those of `products/tracker17/docs/nfdr.md:166-197`, § 1.2 Forbidden imports. No transitive blast radius — public surfaces unchanged. The card is read by the existing command consumers; their contracts and source do not change.

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| Single card delta — Setup and Test values | For Setup's `--project` argument, use the quoted Git top-level directory with the fixed `products/tracker17` suffix; `git rev-parse --show-toplevel` supplies the checkout being operated in. Keep `uv sync --locked`. For Test, keep the working directory at the worktree root, select `products/tracker17` with `--project`, and name `products/tracker17/tests/` and `products/tracker17/tests/e2e/` in separate pytest processes. Join the two locked `uv run` invocations with shell `&&`, so either failure remains non-zero. |

The hint fixes the approach, not a finished shell expression. The following command properties are required by the cited rules:

- **Setup location and quoting:** both permitted working directories must select the same `products/tracker17/pyproject.toml` and `uv.lock`, making only `products/tracker17/.venv`, without relying on uv's fallback for a nonexistent relative project directory (CP-685–CP-686, `change_spec.md:23-24`, § Setup command). Quote the resolved project argument so a checkout path containing spaces remains one argument. uv documents that `--project` discovers the project without changing the working directory (https://docs.astral.sh/uv/reference/cli/#uv-sync--project).
- **Lock refusal in every invocation:** use `--locked` on synchronization and on each test runner, not `--frozen` or an unlocked run (CP-687 and CP-690, `change_spec.md:25,31`). uv's `--locked` option checks whether the lock needs updating and exits with an error instead of updating it (https://docs.astral.sh/uv/reference/cli/#uv-run--locked).
- **Two suites with failure propagated:** keep both full directory arguments, with no selection flags, retry, skip, ignore, success fallback or output suppression (CP-689, `change_spec.md:30`, § Test command). The first process runs before the second; failure in the first prevents the second starting, while failure in the second makes the whole value fail. A collection failure or an empty suite must retain pytest's non-zero status. Separate processes also keep equal test-module basenames apart: the collection hook explicitly omits end-to-end tests unless their directory is named (`products/tracker17/tests/conftest.py:44-59`, `_command_line_names_end_to_end` and `pytest_ignore_collect`).
- **No browser fetch in Setup:** retain the request's conditional boundary. A fresh Git clone does not imply an empty browser cache. Browser installation remains the prerequisite explained in `products/tracker17/README.md:91-100`, § Running the tests; `change_spec.md:89,101`, § Out of Scope and Locked Answer Gap 5, excludes provision of an absent browser from this delta. An unavailable browser must surface as suite failure, never a skipped layer.
- **Card preservation:** replace each value between its field prefix and its existing trailing comment, preserving both HTML comments and all other bytes (CP-691, `change_spec.md:35`). No README edit or additional card field is required (CP-692 and § Out of Scope, `change_spec.md:36,84-85`).

No write outside the instance/product change worktree is part of this delta. No product source file, persistent test or helper script is added.

## 5. Test Additions

No product test file changes: the request expressly preserves every test (`change_spec.md:83`, § Out of Scope). The additions are command acceptance checks in disposable Git clones at the implementation commit, with the card's actual extracted values passed to `/bin/sh` from each specified directory. A clone preserves the Git-dependent suite prerequisite (`products/tracker17/README.md:109`, § Running the tests). Keep any deliberate manifest or test mutation inside a separate disposable copy; none is committed or carried into the successful clean run.

Every row below belongs to the single card delta. “Scratch check” denotes a temporary check, not a repository file to create. Examples are numbered in their existing order in `change_spec.md:44-55`, § Examples.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| Card — T1 | Scratch check; card under test | Examples 1–3: begin with neither root nor product `.venv`; run Setup from the clone root, then independently from the product directory in another fresh clone. Each exits 0, creates product `.venv`, creates neither root `.venv` nor `products/tracker17/products/`, and emits no stderr line beginning `warning:`. Covers CP-685–CP-686. Include a scratch clone whose path contains spaces to exercise the quoted project selection. |
| Card — T2 | Scratch manifest mutation | Example 4: make `pyproject.toml` disagree with `uv.lock` in disposable copies and run Setup separately from both permitted directories. Each exits non-zero; the lock's bytes before and after match. Covers CP-687 and CP-686's two-directory requirement. |
| Card — T3 | Scratch check; card under test | Example 5: read both actual command values, removing only the trailing HTML comments. Setup is not `none` and includes uv; Test includes uv and does not start with `pytest`. Inspect both test invocations for the same product selector and `--locked`; inspect Setup for locked sync. Covers CP-685, CP-688 and CP-690. |
| Card — T4 | Existing `products/tracker17/tests/` and `tests/e2e/` | Examples 6 and 10: after Setup, execute the actual Test value from the clone root. Require exit 0 and separate pytest summaries covering unit, integration, architecture and end-to-end tests. Keep both complete directory arguments and assert no command-driven deselection or skipped layer. Compare lock bytes and require empty `git status --short -- products/tracker17` afterwards. Covers CP-689–CP-690; the example's counts describe its earlier measurement, not a new hard-coded count contract. |
| Card — T5 | Scratch-only mutations to one unit test and one end-to-end test | Examples 7–8: in independent copies, make one otherwise collected test fail in each suite. Run the complete card Test value; both cases exit non-zero. The end-to-end case starts with the first suite green so the second process is reached. Covers CP-689's failure propagation. |
| Card — T6 | Scratch-only collection mutations | Rule-implied CP-689 edges: independently introduce a collection error in each suite and require non-zero from the card Test value. Also exercise a suite collecting no tests, leaving the other suite healthy, and require non-zero; do this for each suite. An earlier suite failure need not run a later suite. |
| Card — T7 | Scratch manifest mutation | Example 9: make the lock stale, record its bytes, then run the actual Test value. Require non-zero before test collection or execution and byte-identical lock. Inspect `--locked` on both invocations in T3 so refusal is not confined to the first process. Covers CP-690. |
| Card — T8 | Scratch diff check | Examples 11–12: compare the card with its pre-edit bytes, masking only the two command-value spans; all remaining bytes must match. Require exactly those two changed card lines, unchanged trailing comments and other fields, and no implementation diff under `products/tracker17/`. Change-folder records are allowed. Covers CP-691–CP-692. |

**Rule coverage:** CP-685 → T1/T3; CP-686 → T1/T2; CP-687 → T2; CP-688 → T3/T4; CP-689 → T4/T5/T6; CP-690 → T3/T4/T7; CP-691 → T8; CP-692 → T8. No existing assertion is retired; both existing suites and their collection rule remain unchanged under the request's edit boundary (`change_spec.md:30,35-36,83`).

## Records this change makes false

- `products/tracker17/docs/nfdr.md:633-634`, § 10 Verification map, preamble — the sentence identifying the card's Test value as `pytest tests/`, with the end-to-end suite beside it, becomes false. Replace the copied command with a pointer to the card's Test value, and state that the suite gate runs both suites through that value from the change-worktree root. The existing record-gap entry in this change's `deferred_decisions.md`, “NFDR § 10's account of the card's Test command,” already hands this correction on.

No other record correction follows from this delta: reviewed `products/tracker17/docs/adr/README.md` and its Accepted ADRs (0001, 0003–0005, 0007–0009, 0011–0013), `products/tracker17/docs/nfdr.md` §§ 1–10, `products/tracker17/docs/fdr.md` §§ Rules and Product decisions, and `products/tracker17/docs/SDD.md` § 3, RT-4 and § 6 preamble. The SDD's product-root examples remain the manual slice commands; the card supplies the chain's working-directory form. Foundation files remain outside this design's writes.

## Architect Review Notes

All decisions below are the Architect's, 2026-10-29.

1. **Placement outside the parts table (e):** the card owns the tooling delta, as § 2 places it. The SDD's tracker parts own none of this logic (`products/tracker17/docs/SDD.md:212-218`, § 3 The parts); NFDR § 8 explicitly gives the execution context and suite command to the card (`:541-544`). No new product module or import permission is needed.
2. **Realize the location and exit contracts by construction (b):** use a Git-root-derived, quoted project path for Setup, and two separately locked test processes joined by `&&`. These choices realize CP-686, CP-689 and CP-690 explicitly; a relative Setup path interpreted from the product directory or a single pytest process does not provide those contracts (`core/tools/create_change_worktree.py:472-476`, `run_setup`; `products/tracker17/tests/conftest.py:44-59`, collection hook). The specification's Rules stand as written; no reading is set aside.
3. **Browser readiness boundary (b):** do not add a browser installation to Setup. This selects the smaller option left open in Locked Answer Gap 5 (`change_spec.md:101`) while retaining § Out of Scope's absent-browser boundary (`:89`). Existing README browser setup remains applicable (`products/tracker17/README.md:91-100`, § Running the tests).
4. **Published-text verdict:** `no` covers an executable configuration edit with no new label, message or prose; CP-691 fixes every non-value byte, and CP-692 confines the product diff (`change_spec.md:35-36`). Existing pytest output is retained, not newly authored.
5. **NFDR design-stage review sweep:** QC-12 passes: the design adds no product part, dependency or helper. QC-41 passes: neither command introduces a credential, account or secret. QC-5, QC-8, QC-20–QC-27, QC-36 and QC-46 do not trigger a changed-path review: no refusal, runtime part, page, saving contract or saved field changes. QC-60 introduces no language/library feature to review and no interpreter pin; its separate Python 3.11 run stays outside the request. These verdicts apply the triggers in `products/tracker17/docs/nfdr.md` §§ 1.1–1.4, § 2 QC-36/QC-41, § 4 QC-46 and § 8 QC-60 to the § 2 blast radius.
6. **QC-40 package review:** the exact registry versions in `products/tracker17/uv.lock` were read against PyPI's per-version JSON API on 2026-10-29; each source in the table below returned `vulnerabilities: []`. This records what that feed returned, not a claim that every possible advisory source is empty. No package pin or lock format changes in this delta (CP-692, `change_spec.md:36`).

| Package version reviewed | Published metadata — returned `vulnerabilities: []` |
|---|---|
| ast-serialize 0.12.1 | https://pypi.org/pypi/ast-serialize/0.12.1/json |
| colorama 0.4.6 | https://pypi.org/pypi/colorama/0.4.6/json |
| greenlet 3.5.6 | https://pypi.org/pypi/greenlet/3.5.6/json |
| iniconfig 2.3.1 | https://pypi.org/pypi/iniconfig/2.3.1/json |
| librt 0.16.0 | https://pypi.org/pypi/librt/0.16.0/json |
| mypy 2.4.0 | https://pypi.org/pypi/mypy/2.4.0/json |
| mypy-extensions 1.1.0 | https://pypi.org/pypi/mypy-extensions/1.1.0/json |
| packaging 26.3 | https://pypi.org/pypi/packaging/26.3/json |
| pathspec 1.1.1 | https://pypi.org/pypi/pathspec/1.1.1/json |
| playwright 1.63.0 | https://pypi.org/pypi/playwright/1.63.0/json |
| pluggy 1.6.0 | https://pypi.org/pypi/pluggy/1.6.0/json |
| pyee 13.0.1 | https://pypi.org/pypi/pyee/13.0.1/json |
| pygments 2.21.0 | https://pypi.org/pypi/pygments/2.21.0/json |
| pytest 9.1.1 | https://pypi.org/pypi/pytest/9.1.1/json |
| ruff 0.16.10 | https://pypi.org/pypi/ruff/0.16.10/json |
| typing-extensions 4.16.0 | https://pypi.org/pypi/typing-extensions/4.16.0/json |

7. **QC-40 browser review:** the pinned driver's Chromium is revision 1243, version 153.0.8010.12 (https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json, `chromium` and `chromium-headless-shell`). Google's 2026-10-27 desktop release is 156.0.8078.73/.74 and lists four critical fixes (https://chromereleases.googleblog.com/2026/?amp=1, “Stable Channel Update for Desktop”, 2026-10-27). The comparison does not establish which individual fixes affect the pinned build. The owner's exception expressly covers that build through 2026-11-07, so the unchanged build does not block this 2026-10-29 review (`products/tracker17/docs/nfdr.md:1083-1092`, RN-33).
8. **QC-40 repository-feed review:** `gh api repos/kensaiapp/<the instance KensaiApp is developed in> --jq '{permissions: .permissions}'` returned `admin: true`. `gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependabot/alerts` returned HTTP 403, “Dependabot alerts are disabled for this repository.” The authenticated GraphQL query of `dependencyGraphManifests(first:100)` returned `totalCount: 0, nodes: []`. Opening https://github.com/kensaiapp/<the instance KensaiApp is developed in>/network/dependencies returned “Failed to fetch … Cache miss.” No dependency-graph page or asynchronous SBOM export listing the locked packages was read, so QC-40's graph-reading moment remains owed (`products/tracker17/docs/nfdr.md:389-399`, QC-40). The corresponding record gap is handed on in `deferred_decisions.md`; this verdict does not waive the obligation or change repository settings.
