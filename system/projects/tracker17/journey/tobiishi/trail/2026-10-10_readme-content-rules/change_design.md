# Change Design — README setup prose meets the content rules

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** preserving
**Publishes text:** no

---

## 1. Change Summary

This design owns the repair's placement, affected parts and continuity checks.
Its input is `tracker17 · tobiishi · 2026-10-10_readme-content-rules`, `change_spec.md` § Invariants and § Structural Goal.
Reword the existing setup prose in `products/tracker17/README.md` in place, to the existing sentence-length and relative-word rules (`products/tracker17/docs/CONTENT.md:L120-L129`, § Grammar and mechanics).
The characterization contract remains the spec's; this design introduces no new instruction, behaviour or public import surface (`change_spec.md:L29-L48` § Invariants in the named Tobiishi).

## 2. Blast Radius

No transitive blast radius — public surfaces unchanged, per `change_spec.md:L35-L48` § Invariants.
The parts table exists at `products/tracker17/docs/SDD.md` § 3; this repair adds no logic to place in a part (`change_spec.md:L46-L48` § Invariants).
The module set below follows `products/tracker17/docs/nfdr.md:L122-L153`, § 1.2.

| Module / document | Status | What changes |
|---|---|---|
| `products/tracker17/README.md` | Modified (rewording only) | Existing prose stays in its existing sections; placement is § 3. |
| `products/tracker17/domain/` | Unchanged | No code or export changes, per `change_spec.md:L46-L48` § Invariants, Product continuity. |
| `products/tracker17/application/` | Unchanged | Product continuity invariant (`change_spec.md:L46-L48`, § Invariants). |
| `products/tracker17/persistence/` | Unchanged | Product continuity invariant (`change_spec.md:L46-L48`, § Invariants). |
| `products/tracker17/web/` | Unchanged | Product continuity invariant (`change_spec.md:L46-L48`, § Invariants). |
| `products/tracker17/main.py` | Unchanged | Product continuity invariant (`change_spec.md:L46-L48`, § Invariants). |
| `products/tracker17/errors.py` | Unchanged | Product continuity invariant (`change_spec.md:L46-L48`, § Invariants). |
| `products/tracker17/tests/` | Unchanged | Existing assertions remain intact, per `change_spec.md:L31-L34` § Invariants, Test continuity. |
| `products/tracker17/docs/` | Unchanged | Definition documents remain intact, per `change_spec.md:L46-L48` § Invariants, Product continuity. |

## 3. Layout Plan

The target is the existing README; no text moves to another section or file, per `change_spec.md:L52-L62` § Structural Goal.
No implementation symbol moves, and no `__init__.py` re-export changes, per `change_spec.md:L35-L48` § Invariants.
Architect decision, 2026-10-10: the two in-place prose repairs expose no new interface or ordering edge (§ 3's placement table).

| Existing statement / boundary | Before place | Target place | Repair |
|---|---|---|---|
| Prerequisite sentence | README § What you need, `products/tracker17/README.md:L23` | Same section | Split the installation condition and action into shorter sentences; keep the meaning protected by the spec's README meaning and commands invariant. |
| Saved-data description | README § Setting saved data aside, `products/tracker17/README.md:L81` | Same section | Reword the description without a banned word; keep the information protected by the same invariant. |
| Any further sentence violating either constraint | README span from § Status to immediately before § How it's built | Same section as that sentence | Apply the spec's meaning-preserving repair only if the full-span check finds a violation (`change_spec.md:L52-L61` § Structural Goal). |
| All protected headings, commands and retained prose | Existing README positions | Same positions | Retain the spec's Headings and retained sections and README meaning and commands invariants (`change_spec.md:L37-L45` § Invariants). |

The full-span constraint is checked across the entire bounded prose, rather than inferred from repairing two lines (§ 5, C1 and C2).
No final replacement wording is fixed here, as permitted by `change_spec.md:L62` § Structural Goal.

## 4. Code Strategy

| Module / change | Hint |
|---|---|
| `products/tracker17/README.md` — reword existing setup prose in place | None |

## 5. Test Continuity

No test additions — the existing suite is the characterization contract (`change_spec.md:L31-L34` § Invariants, `L46-L48`).
No assertion is retired: tests and their assertions remain unchanged under the Product continuity invariant (`change_spec.md:L46-L48` § Invariants).
The spec has no Examples table; the rows below cover its Structural Goal and every Invariant, including their condition and failure branches (`change_spec.md:L29-L73` § Invariants).

| ID | Surface / obligation | Existing check or continuity check | Test change |
|---|---|---|---|
| C1 | Sentence-length repair and any additional violation in the full bounded span | Count every prose sentence using the spec's token and sentence-boundary definitions (`change_spec.md:L52-L58` § Structural Goal, `L61-L73`); every count must be at most 20. Read addresses, paths, versions and inline commands as whole tokens; exclude headings and fenced shell blocks. | None |
| C2 | Relative-word repair, including case variants and further violations | Run the exact grep in `change_spec.md:L64-L70` § Structural Goal from the instance worktree root; no returned line may lie in the bounded span. A grep exit 1 means no matches; an execution error is not a passing check. | None |
| C3 | Prerequisite meaning across both installation conditions | Compare the complete § What you need before and after, especially `products/tracker17/README.md:L17-L23`, against the spec's README meaning and commands invariant (`change_spec.md:L37-L41` § Invariants). Check the lower-version and missing-command alternatives separately, and retain the download address and repeat action. | None |
| C4 | Set-aside meaning, empty start and missing saved-data branch | Compare the complete § Setting saved data aside before and after (`products/tracker17/README.md:L69-L85`) against `change_spec.md:L37-L41` § Invariants, README meaning and commands. Include the location, naming example and listing command, the `mv` failure branch at line 83 and the empty-start statement at line 85. | None |
| C5 | Every heading, command and command order; prose outside the permitted span | Compare README headings with their levels and order, fenced blocks and inline commands before and after; compare the prefix before § Status and suffix starting at § How it's built byte for byte. Review each prose edit for unchanged meaning (`change_spec.md:L37-L48` § Invariants, `L52`). | None |
| C6 | Both fixed headings and the terminal message's pointer | Retain `test_the_readme_has_both_fixed_headings` and `test_the_message_closing_sentence_quotes_a_heading_the_readme_has` (`products/tracker17/tests/integration/test_start.py:L147-L162`). Their heading reader excludes fenced code (`products/tracker17/tests/integration/test_start.py:L94-L120`, `_headings`); keep the real heading lines. | None |
| C7 | Code, public imports, tests and definition documents | Product diff contains only permitted README prose edits; all code, exports, tests and `docs/` remain unchanged (`change_spec.md:L35-L48` § Invariants). | None |
| C8 | Full test continuity | From the product directory in the existing test environment, `pytest tests/` and `pytest tests/e2e/` both exit 0, as required by `change_spec.md:L31-L34` § Invariants; C6 runs in the first suite. | None |

The fixed-address end-to-end test binds `127.0.0.1:8017` before starting the tracker and raises if that bind fails (`products/tracker17/tests/e2e/test_start_command.py:L17-L18`, `L38-L55`).
A green end-to-end result therefore needs that address available for the test's own listener; changing the address, skipping the test or weakening its assertion does not meet C8 (`change_spec.md:L31-L34` § Invariants, `L46-L48`).
Earlier suite results are recorded in `change_spec.md:L87-L90` § Verified Claims. Suite execution is outside this design run's scope (`core/roles/loaders/architect_global.md`, § Verification is not yours to call).

## Records this change makes false

None — read `products/tracker17/docs/adr/README.md` and ADR-0001 through ADR-0009, `products/tracker17/docs/nfdr.md`, `products/tracker17/docs/fdr.md` and `products/tracker17/docs/SDD.md` § 3; on this reading, rewording in place with the spec's invariants intact makes no sentence in them false.
In particular, the setup and saved-data contract stays as stated in `products/tracker17/docs/fdr.md` § The written setup instructions, R-8 to R-14, and § Saved data, R-28.

## Architect Review Notes

The design decisions below are the architect's, made 2026-10-10.

- **RN-1 — shape departure (d):** Use the preserving template's Layout Plan for in-place prose repairs rather than a symbol partition. The product has code (`system/projects/tracker17/project.md:L5`, **Type:**, and `:L11-L13`, **Test command:** and **Languages:**), but this change excludes every code and test edit (`change_spec.md:L46-L48` § Invariants); a symbol relocation would cross that boundary.
- **RN-2 — checks by construction (b):** C1 and C2 inspect the full permitted span, and C5 compares protected structure and boundaries separately. This realizes the spec's whole-span requirement and preservation contract explicitly (`change_spec.md:L37-L45` § Invariants, `L52-L73`), rather than treating two repaired lines or two passing heading tests as proof of all of them. These are repair checks, not new product tests.
- **RN-3 — delegated reviews:** The sweep of `products/tracker17/docs/nfdr.md` and `products/tracker17/docs/adr/` for `development-design` found stage-specific gates in the NFDR. QC-12 passes: this design adds no part (`products/tracker17/docs/nfdr.md:L115-L120`, § 1.1 QC-12; § 2 above). QC-41 passes for this change: the proposed README-only repair introduces no secret, account or credential (`products/tracker17/docs/nfdr.md:L320-L324`, § 2 QC-41; § 3 above). QC-5, QC-8, QC-20 to QC-27, QC-36, QC-46 and QC-60 are not triggered by this prose-only scope: their refusal, layer, persistence, page-building, saved-field and language-feature subjects remain unchanged (`products/tracker17/docs/nfdr.md` §§ 1.1–1.4, 2, 4 and 8; `change_spec.md:L46-L48` § Invariants). QC-40's every-review gate is performed below, rather than treated as conditional on a pin change (`products/tracker17/docs/nfdr.md:L295-L319`, § 2 QC-40).
- **RN-4 — language resolution:** Python, resolved from `system/projects/tracker17/project.md:L13`, **Languages:**; opened `core/doctrine/engineering/languages/python/README.md`. Code was read only to locate existing continuity coverage; this design changes no Python unit (§ 2).
- **RN-5 — QC-40 package review, 2026-10-10:** Queried GitHub's global advisory endpoint for each exact locked package below with `ecosystem=pip`, `affects=<name>@<version>`, `severity=critical`, `per_page=100`. Each successful response was the actual empty JSON list `[]`; the query URLs are in the table. The set is `products/tracker17/tests/requirements.txt:L4-L18`, the exact pins under “Test dependencies, locked with everything they pull in”. Verdict: no critical advisory was returned for these pinned versions by this database on this review; this is not a claim that no vulnerability exists.

| Locked package | Exact critical-advisory query | Actual response |
|---|---|---|
| `ast_serialize==0.12.1` | https://api.github.com/advisories?ecosystem=pip&affects=ast_serialize%400.12.1&severity=critical&per_page=100 | `[]` |
| `greenlet==3.5.6` | https://api.github.com/advisories?ecosystem=pip&affects=greenlet%403.5.6&severity=critical&per_page=100 | `[]` |
| `iniconfig==2.3.1` | https://api.github.com/advisories?ecosystem=pip&affects=iniconfig%402.3.1&severity=critical&per_page=100 | `[]` |
| `librt==0.16.0` | https://api.github.com/advisories?ecosystem=pip&affects=librt%400.16.0&severity=critical&per_page=100 | `[]` |
| `mypy==2.4.0` | https://api.github.com/advisories?ecosystem=pip&affects=mypy%402.4.0&severity=critical&per_page=100 | `[]` |
| `mypy_extensions==1.1.0` | https://api.github.com/advisories?ecosystem=pip&affects=mypy_extensions%401.1.0&severity=critical&per_page=100 | `[]` |
| `packaging==26.3` | https://api.github.com/advisories?ecosystem=pip&affects=packaging%4026.3&severity=critical&per_page=100 | `[]` |
| `pathspec==1.1.1` | https://api.github.com/advisories?ecosystem=pip&affects=pathspec%401.1.1&severity=critical&per_page=100 | `[]` |
| `playwright==1.63.0` | https://api.github.com/advisories?ecosystem=pip&affects=playwright%401.63.0&severity=critical&per_page=100 | `[]` |
| `pluggy==1.6.0` | https://api.github.com/advisories?ecosystem=pip&affects=pluggy%401.6.0&severity=critical&per_page=100 | `[]` |
| `pyee==13.0.1` | https://api.github.com/advisories?ecosystem=pip&affects=pyee%4013.0.1&severity=critical&per_page=100 | `[]` |
| `Pygments==2.21.0` | https://api.github.com/advisories?ecosystem=pip&affects=Pygments%402.21.0&severity=critical&per_page=100 | `[]` |
| `pytest==9.1.1` | https://api.github.com/advisories?ecosystem=pip&affects=pytest%409.1.1&severity=critical&per_page=100 | `[]` |
| `ruff==0.16.10` | https://api.github.com/advisories?ecosystem=pip&affects=ruff%400.16.10&severity=critical&per_page=100 | `[]` |
| `typing_extensions==4.16.0` | https://api.github.com/advisories?ecosystem=pip&affects=typing_extensions%404.16.0&severity=critical&per_page=100 | `[]` |

- **RN-6 — QC-40 browser review, 2026-10-10:** The installed build was checked by running `"~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" --version`: exit 0, output `Google Chrome for Testing 153.0.8010.12`. Google's [2026-09-22 desktop security release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0856730748.html) reports critical fixes in Chrome 154. Verdict: pass under the owner's dated exception for this exact build through 2026-11-07 (`products/tracker17/docs/nfdr.md:L952-L962`, RN-33); this design changes neither the pin nor the exception.
