# Change Design — the README sets up the test suite with uv

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** yes — the README's Running the tests section, How it's built bullets, and The documents list

---

## 1. Change Summary

This blueprint owns the placement and verification of the companion `change_spec.md`, Rules CP-668–CP-684. Change only `products/tracker17/README.md`: the suite instructions, the test-environment description and architecture-decision link in How it's built, and the decision-log entry in The documents. Keep the tracker's own setup text byte-identical (CP-679).

The documentation describes the existing environment contract: `products/tracker17/docs/SDD.md:299-333`, § 4 RT-4, and `products/tracker17/docs/adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md:22-37`, § Decision, prescribe uv. Paths below are relative to `products/tracker17` unless an instance-relative path is written explicitly.

## 2. Blast Radius

The parts table exists in `docs/SDD.md:204-234`, § 3, The parts, and the seams between them. No executable logic is added to place in a part. The README is the setup-instructions artifact named by SDD § 6 S-1, Artifact (`docs/SDD.md:827-847`).

| Module / artifact | Status | What changes |
|---|---|---|
| `README.md` | Modified | CP-668–CP-680: suite setup and prose, test-environment bullet, current ADR link, and decision-log count wording. CP-681 retains all headings. |
| `domain/` | Unchanged | No rule, value, refusal or public surface changes. |
| `application/` | Unchanged | No action, state, saver or clock contract changes. |
| `persistence/` | Unchanged | No saved-data, file or locking changes. |
| `web/` | Unchanged | No route, page, style or request changes. |
| `main.py` | Unchanged | No wiring, start command or console text changes. |
| `errors.py` | Unchanged | No exception changes. |
| `tests/` | Unchanged | No test or fixture edits (CP-682). |
| `pyproject.toml`, `uv.lock` | Unchanged | Use the committed environment definition without edits or lock regeneration (CP-682–CP-683). |
| `docs/`, instance project card | Unchanged | Foundation records and card lines are outside the product edit (CP-682). |

No transitive blast radius: no Python public interface or import changes. The forbidden-import graph is `docs/nfdr.md:166-197`, § 1.2. The README headings consumed by existing tests stay unchanged (`tests/integration/test_start.py:193-208`, closing-sentence and fixed-heading tests).

One documentation delta; no sub-job split. All affected prose lives in one file, with no interface dependency or internal ordering edge. The resulting README must describe one consistent test environment in both sections (companion `change_spec.md`, CP-670, CP-676).

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `README.md` — documentation delta | None |

## 5. Test Additions

No test files are added or modified: CP-682 excludes them. These are document acceptance checks and command verification, not permanent tests that mirror prose. Each row maps the companion `change_spec.md` Rules and Examples; V1–V13 cover every Example.

| Check / rules | Test file or artifact | What to add / modify / verify |
|---|---|---|
| V1 — CP-668 | `README.md`, Running the tests | Read for uv as a prerequisite before the block, the exact official installation URL and lowercase tool spelling throughout the README. No installer command or uv version is added. |
| V2 — CP-669 | `README.md`, Running the tests | Compare the block against CP-669 as an ordered five-line sequence, with no other line. Read the lead-in for opening the terminal at the top of the copy. |
| V3 — CP-670, CP-672 | `README.md`, Running the tests | Read for what sync and run do, and the distinct non-end-to-end and Chromium end-to-end commands. Run CP-672's exact pipeline: no output, exit 1. Check prose as well as the block for bare commands. |
| V4 — CP-671 | `README.md`, Linux paragraph | Read for the exact `uv run playwright install --with-deps chromium` replacement. Retain package-manager use, administrator rights, the tracker/non-end-to-end exemption and every specified distribution, version and architecture. No Linux execution is required. |
| V5 — CP-673 | `README.md`, environment paragraph | Read for sync making `.venv` inside `products/tracker17`, keeping it there, the dot-directory reason and the failure of an environment elsewhere inside the product. |
| V6 — CP-674 | `README.md`, new-terminal paragraph | Read for directly rerunning the `uv run` test commands inside `products/tracker17`, with no preliminary environment step. Cover the second-terminal path separately from first setup. |
| V7 — CP-675 | `README.md`, Running the tests | Retain the network requirement only for test setup. Compare the entire Git-repository paragraph byte for byte with the pre-change file, including the one failing test, what it checks and the tracker's exemption. |
| V8 — CP-676, CP-677 | `README.md`, How it's built | CP-676's exact section/uv check prints at least one line, exit 0. Read the test bullet for exact-version dependencies, three layers, Chromium and its RT-4/TS-1 citation. Check the first bullet's exact ADR-0013 link and absence of any ADR-0002 link. |
| V9 — CP-678 | `README.md`, The documents | Use no numerical decision count; retain the pointer to `docs/adr/README.md`. Read the entry against that requirement. |
| V10 — CP-679, CP-681 | `README.md` | Compare the setup slice, from `## Setup instructions` up to but excluding `### Running the tests`, byte for byte with the pre-change file. CP-679's no-uv check prints nothing, exit 1. Compare all heading texts, levels and order, disregarding shifted line numbers. Retain the two-command start. |
| V11 — CP-680 | `README.md`, whole file | Run CP-680's exact fixed-string, case-sensitive grep: no output, exit 1. Include all sections and new prose. Its negative Example, “nothing to activate”, is covered by the same `activate` substring check; prefixing the old Playwright spelling likewise cannot evade its pattern. Do not weaken the check. |
| V12 — CP-682 | Product tree and instance project card | Compare with the pre-change product baseline: only `products/tracker17/README.md` differs under the product, and no card line differs. Change-folder artifacts are outside that product comparison. |
| V13 — CP-683 | Fresh Git clone of the branch commit on macOS | With uv installed and network available, type all five CP-669 lines in order from the clone root; each exits 0. Confirm product-local `.venv` exists and is Git-ignored. Compare `uv.lock` byte for byte with its committed blob after both suites. Use a disposable clone, never the shared primary checkout. |
| V14 — CP-684 | Architect Review Notes below | QC-12 and QC-41 are reviewed here; their verdicts are design evidence. |

Rule-implied paths: the Linux alternative and exemption are V4; a misplaced environment is V5; a new terminal is V6; a non-Git copy or missing `git` is preserved in V7 without inventing a fallback; forbidden substrings in otherwise reasonable prose are V11. Setup boundaries, headings and file scope are V10 and V12. No assertion is retired: CP-682 keeps test code unchanged, and V10 retains the heading surfaces consumed by `tests/integration/test_start.py:193-208`.

## Records this change makes false

None — the README edit makes no statement false in `docs/adr/` (the index and applicable Accepted ADR-0013), `docs/nfdr.md` § 1.2 and its review gates, `docs/fdr.md` R-11–R-14, R-119–R-120 and PD-7, or `docs/SDD.md` § 3, § 4 RT-4 and § 6 S-1. The prerequisites discrepancy in the companion `deferred_decisions.md` predates this delta; retain its entry and leave the protected setup slice untouched.

## Architect Review Notes

- **Documentation shape (d), Architect, 2026-10-29:** Use document checks in § 5 instead of new test files because CP-682 forbids test edits. The single README delta has no interface seam requiring sub-jobs. All code parts from SDD § 3 remain outside the edit.
- **Explicit consistency (b), Architect, 2026-10-29:** Compare commands as a sequence, the protected setup slice and Git paragraph as bytes, and headings as text/level/order. Presence greps alone cannot establish CP-669's exact order or CP-675/CP-679's unchanged wording; V2, V7 and V10 realize those contracts directly.
- **Decision count (b), Architect, 2026-10-29:** Choose CP-678's permitted no-count form. The index remains the count's owner, so adding a record cannot make a numerical claim in the README stale.
- **QC-12 — pass:** No code part, dependency, helper or test file is added. The product delta is the README required by CP-668–CP-682, so no added part lacks a requirement (`docs/nfdr.md:159-164`, QC-12; `docs/SDD.md:204-234`, parts table).
- **QC-41 and FDR R-14 — pass:** The referenced standalone installation path is a public download and shell install, with no account, credential, sign-up or payment step shown (https://docs.astral.sh/uv/getting-started/installation/, Standalone installer, checked 2026-10-29). Publish its page link, leaving the installer recipe with its owner (CP-668).
- **QC-40 — packages reviewed, 2026-10-29:** Parsed the 16 registry package/version pairs from `uv.lock` and submitted those exact PyPI versions to https://api.osv.dev/v1/querybatch. The request exited 0 and returned an empty result object for every pair: no matching advisory was reported. This is an advisory-database result, not proof that an unreported vulnerability cannot exist. No pin or lock format changes (CP-682).
- **QC-40 — browser exception applies, 2026-10-29:** The versioned Playwright manifest names Chromium `153.0.8010.12` (https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json). Google's October 27 release reports critical fixes in `156.0.8078.73/.74` (https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html). Do not read that comparison as a finding that the older test build is free of those defects. The owner's exception expressly allows `153.0.8010.12` through 2026-11-07 (`docs/nfdr.md:1074-1088`, RN-33); the unchanged build does not block this review.
- **QC-40 — dependency feed unresolved:** `gh api repos/<owner>/<repository>/dependency-graph/sbom` returned `Not Found (HTTP 404)`, exit 1. That proves neither an empty graph nor working lock-file coverage. The companion `deferred_decisions.md` records this unmet verification for the Principal Architect. This delta changes neither the feed nor its permissions.
- **Other delegated reviews:** The `development-design` tails for refusals, code-part responsibilities, page building, saved fields and language/library features do not reach the edit in § 2 (`docs/nfdr.md`, QC-5, QC-8, QC-20–QC-27, QC-34, QC-49, QC-60). No spec line is set aside; the existing prerequisites gap stays with its companion entry.
