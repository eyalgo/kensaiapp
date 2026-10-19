# Change Design — Linux test setup and the suite's Git prerequisite

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** yes — the setup instructions' Running the tests section

---

## 1. Change Summary

This design settles the placement and checks for the README edit specified by
`change_spec.md` § Rules, CP-69 to CP-79, in
`tracker17 · tobiishi · 2026-10-11_readme-linux-setup-and-git` (`change_spec.md:22-38`).
The product edit is confined to `products/tracker17/README.md` § Running the tests,
per CP-78 (`change_spec.md:37`).

The section has two edit sites:

1. Insert the Linux note after the existing introductory paragraph and before the
   seven-command block (`README.md:89-99`, § Running the tests).
   The note carries CP-69 to CP-72 and identifies the browser command as a
   replacement at that step, after dependency installation.
   The replacement command appears in an inline code span, so it cannot read as
   an additional sequence to run before creating the virtual environment.
2. Replace the entire existing closing paragraph with the CP-73 to CP-76 Git
   explanation (`README.md:107`, § Running the tests).
   The explanation is one paragraph and remains last in the section.
   Both missing-prerequisite cases belong to that paragraph's failure explanation.

Published wording is left open within these placements and the spec's locked
rules, including CP-77's grammar requirements (`change_spec.md:36`).

Paths such as `README.md`, `docs/` and `tests/` below are relative to
`products/tracker17/` in this change's worktree.
The product binding is `system/projects/tracker17/project.md:3`, **Product path**.
The change artifact's home is the active Tobiishi folder, per
`<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, **journey/tobiishi/**
(`core/doctrine/setup/kensaiapp_structure.md:2097-2101`).

---

## 2. Blast Radius

No new executable logic is proposed.
The SDD parts table assigns runtime responsibilities to five parts, and assigns
none of them the setup instructions (`docs/SDD.md:186-207`, § 3 **The parts**).
The README is the setup artifact named by SDD S-1
(`docs/SDD.md:672-687`, § 6 **first-project**, *Artifact*).
This places the edit in that artifact without adding a runtime part.

| Module / artifact | Status | What changes |
|---|---|---|
| `README.md` § Running the tests | Modified | Two prose edit sites from § 1, satisfying CP-69 to CP-79. |
| `domain/` | Unchanged | No runtime edit. |
| `application/` | Unchanged | No runtime edit. |
| `persistence/` | Unchanged | No runtime edit. |
| `web/` | Unchanged | No runtime edit. |
| `main.py` | Unchanged | No start-command or console-text edit. |
| `errors.py` | Unchanged | No error-type edit. |
| `tests/`, `pyproject.toml`, `docs/` | Unchanged | No test, dependency, configuration or foundation edit. |

The unchanged rows follow CP-78 and § Out of Scope
(`change_spec.md:37,82-89`).
The import graph lists the runtime parts and `errors.py`
(`docs/nfdr.md:122-153`, § 1.2 **Forbidden imports**).
No interface or import edge changes, so there is no transitive code blast radius.

One artifact is affected, with no interface contract or ordering edge between
modules. There is no sub-job split or module build sequence.

---

## 4. Code Strategy

| Change | Hint |
|---|---|
| `README.md` § Running the tests | None |

---

## 5. Test Additions

No test file is added or modified: CP-78 prohibits any product edit outside the
README (`change_spec.md:37`).
The checks below are readings and one-off commands against the edited artifact.
They introduce no committed harness and execute no install command.

Example numbers below count the rows of `change_spec.md` § Examples from top to
bottom (`change_spec.md:46-59`).

| Check | Test file / artifact | What to verify |
|---|---|---|
| V-1 — CP-69 | `README.md` § Running the tests | Reading: the exact Linux replacement command appears in a code span before the block. The prose tells the reader to use it instead of the block's browser-install command at that step, after installing dependencies. Covers Example 1. |
| V-2 — CP-70, CP-71 | Same section | Reading: the Linux note names the system package manager and administrator rights. It expressly exempts both the tracker and `pytest tests/` from what that command installs. Covers Examples 3 and 4. |
| V-3 — CP-72 | Same section | Reading against `docs/SDD.md` § 4 RT-4 (`:291-296`): all five releases and both architectures appear. `Debian 12` is literal. No additional Linux system is named as supported by the end-to-end tests. Covers Examples 5 and 6, including the unlisted-system boundary. |
| V-4 — CP-73, CP-75 | Section's final paragraph | Reading: the full suite needs both a Git repository and `git` on the path. Either absent condition makes the same one test fail. The explanation says the test checks that Git ignores saved data. Covers Examples 7 and 8. |
| V-5 — CP-74 | Section's final paragraph | Reading: the tracker itself needs neither Git condition. Covers Example 9. |
| V-6 — CP-76 | Section's final paragraph | Compare with the pre-edit README: the old two sentences at `README.md:107` are absent verbatim. The Git prerequisite is stated once, in the last paragraph. Covers Example 10. |
| V-7 — CP-77 | Added and rewritten sentences | Reading and word count: each sentence has at most 20 words, counting words inside command spans too. Check contracted negatives, the absence of Latin abbreviations, and command/tool spellings against `docs/CONTENT.md:98-137`, § Grammar and mechanics. Run the six-word grep below over the whole README; expect no output, exit 1. Covers Examples 11 and 12. |
| V-8 — CP-78 | README diff and product diff | Compare with the pre-edit README: all heading lines, the seven-command block and the four fixed paragraphs stay byte-for-byte identical. Text before and after the section stays identical. Within the product, the only changed path is `products/tracker17/README.md`. Covers Examples 2 and 13. |
| V-9 — CP-79 | `README.md` § Running the tests | Run the two-pattern grep below; expect exit 0, with at least one match for each pattern. Locate every match between the section heading and `## How it's built`. Covers Example 14. |

Commands below run from the change worktree's root:

```sh
grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md
grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md
```

The Rules pass adds the combined case where both Git prerequisites are absent:
V-4's explanation covers it as well as each individual failure.
V-3 covers an omitted release, an omitted architecture and an extra supported
system; V-8 covers a misplaced insertion or an accidental block edit.
The 20-word boundary is covered by V-7, and a missing or out-of-section grep
match by V-9.
These checks cover every edge admitted by CP-69 to CP-79
(`change_spec.md:22-38`, § Rules).

No existing assertion is retired.
In particular, the Git-ignore assertion remains in
`tests/integration/test_start.py:165-170`, **test_data_is_ignored_by_version_control**.
The fixed-heading assertions remain in
`tests/integration/test_start.py:147-162`, **test_the_readme_has_both_fixed_headings**
and **test_the_message_closing_sentence_quotes_a_heading_the_readme_has**.
There is no new runtime behavior to exercise, per
`change_spec.md:82-89`, § Out of Scope.

---

## Records this change makes false

None — read `docs/adr/README.md` and ADR-0001 to ADR-0009, `docs/nfdr.md`,
`docs/fdr.md`, and `docs/SDD.md` § 3, § 4 RT-3/RT-4 and § 6 S-1 *Artifact*;
nothing in them goes false.
The edit fulfills the existing setup obligations in FDR R-119/R-120
(`docs/fdr.md:70-76`, **The written setup instructions**) and SDD S-1
(`docs/SDD.md:677-687`, *Artifact*).
ADR-0009's consequence about one set of prerequisites remains the tracker's own
setup, as NFDR RN-29 already explains (`docs/nfdr.md:889-903`, **RN-29**).

---

## Architect Review Notes

- **Placement — architect decision, 2026-10-11, kind (b):** § 1 chooses the
  insertion point and an inline command span where the spec left placement open
  (`change_spec.md:96`, § Locked Answers, **Gap 2**).
  The reason is to expose the Linux replacement before a reader follows the
  unchanged block, without presenting it as a separate earlier command.
- **Document checks — architect decision, 2026-10-11, kind (d):** § 5 uses
  artifact checks instead of new test modules.
  This departs from the skill template's test-file examples because CP-78 forbids
  modifying tests (`change_spec.md:37`).
  It retains an explicit verification row for every Example and rule-implied edge.
- **QC-12 — pass:** the design adds no code part or test harness, and uses the
  README artifact SDD S-1 requires (`docs/nfdr.md:115-120`, **QC-12**;
  `docs/SDD.md:672-687`, § 6 S-1 *Artifact*).
- **QC-41 — pass:** the two edit sites introduce no credential, secret or account
  requirement (`change_spec.md:22-38`, § Rules;
  `docs/nfdr.md:320-324`, **QC-41**).
- **Conditional reviews — not triggered:** QC-5, QC-8, QC-20 to QC-27, QC-36,
  QC-46 and QC-60 concern changes to runtime handling, saved fields or language
  features (`docs/nfdr.md:56-84,160-208,270-276,377-383,463-467`).
  The blast radius in § 2 changes none of those surfaces.
  The sweep `rg -n 'development-design' products/tracker17/docs/nfdr.md
  products/tracker17/docs/adr/` returned NFDR entries and no ADR match.
- **QC-40 package review — pass, checked 2026-10-11:** a POST to
  `https://api.osv.dev/v1/querybatch` queried all 15 exact PyPI package/version
  pairs in `tests/requirements.txt:4-18` and returned
  `{"results":[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]}` (curl exit 0).
  The database returned no advisory for those pairs; this is a result for the
  queried pins, not a claim about every possible vulnerability.
  No pin or lock-file format is changed, so QC-40's version-selection review is
  not triggered (`docs/nfdr.md:295-319`, **QC-40**).
- **QC-40 browser review — pass under the owner's existing exception, checked
  2026-10-11:** the pinned release's own manifest names Chromium and its headless
  shell as `153.0.8010.12`
  (`https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json`).
  Google's September 17 security release names critical CVE-2026-93374 and
  CVE-2026-93372 in the later `153.0.8010.52/.53` release
  (`https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0194356994.html`).
  Google's October 1 release also names critical CVE-2026-103628
  (`https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop.html`),
  and its October 6 release lists four critical fixes
  (`https://chromereleases.googleblog.com/2026/10/`, **Stable Channel Update for Desktop**, October 6).
  The comparison therefore does not treat the pinned browser as current or
  advisory-free.
  RN-33 explicitly permits this exact build at a design review through
  2026-11-07 (`docs/nfdr.md:952-964`, **RN-33**).
  This review applies that exception without changing its dates or scope.
  The comparison is of the pin's browser manifest: the worktree has no product
  `.venv` (`rg --files --hidden products/tracker17/.venv` returned
  `No such file or directory`).
