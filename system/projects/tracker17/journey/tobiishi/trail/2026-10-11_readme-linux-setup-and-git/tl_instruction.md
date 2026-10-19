# Tech Lead instruction — readme-linux-setup-and-git: complete the test setup instructions

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Product root:** products/tracker17 — product paths below are relative to it.
**Scope:** Edit only `README.md` § Running the tests, at the two sites in `change_design.md:L18-L29`, § 1 Change Summary.

This instruction scaffolds the README edit for
`tracker17 · tobiishi · 2026-10-11_readme-linux-setup-and-git`.
References to `change_spec.md`, `change_design.md` and `change_text.md` name sibling artifacts in that change.
The output belongs in the change folder, per
`<CORE>/doctrine/setup/kensaiapp_structure.md:L2096-L2101`, § 2, **journey/tobiishi/**.

---

## Project layout

```text
products/tracker17/
  README.md                 ← modified, Running the tests section only
```

Create no directory or package file.
The parts table exists in `docs/SDD.md:L186-L207`, § 3 **The parts**.
Place the instructions in the README artifact named by `docs/SDD.md:L672-L687`, § 6 S-1 **Artifact**.
The import graph remains as `docs/nfdr.md:L122-L153`, § 1.2 **Forbidden imports**, defines it.

## TL Review Notes

Decisions made by the Tech Lead, 2026-10-11:

- **Task shape:** Task 1 uses the review-verified shape, with all V-1 to V-9 carried as review criteria (`change_design.md:L92-L102`, § 5 **Test Additions**). The reason is that the deliverable is instructional prose, and CP-78 forbids test edits (`change_spec.md:L37`, § **Wording and boundaries**). No test names or red phase are fabricated.
- **Task cut:** One task covers both edit sites in the one README section (`change_design.md:L18-L29`, § 1 **Change Summary**). The design explicitly supplies no sub-job split or module ordering edge (`change_design.md:L69-L70`, § 2 **Blast Radius**), so the task has no dependencies.
- **Gate made concrete:** The diff checks compare against `06af065b288da2e637e5b00868459d7191c33574`, the input revision returned by `git rev-parse HEAD`. This makes CP-78's unchanged text and product-file boundary checkable after the edit is committed as well as before (`change_spec.md:L37`, § **Wording and boundaries**).
- **Gate baseline:** The card's exact command, `pytest products/tracker17/tests/`, collected 224 tests and returned `224 passed in 10.57s` with command approval. Its sandbox execution returned `5 failed, 203 passed, 16 errors`, with socket-bind traces reporting `PermissionError: [Errno 1] Operation not permitted`. The command is retained because it collects and passes the intended suite; no failing-test baseline is declared (`system/projects/tracker17/project.md:L10-L11`, **Test command**; actual command outputs).

### Task 1: Complete Linux and Git test setup instructions (`README.md`)

**Dependencies:** None

**What to build:** Insert the Linux note before the existing command block, and replace the final paragraph with the Git explanation, per `change_design.md:L18-L32`, § 1 **Change Summary**.
All published wording comes from `change_text.md` verbatim, per `<CORE>/roles/CROSS_ROLE.md` § 2 **Implementation contract**.

#### Deliverables verified by review

- **V-1 / CP-69:** The Linux note contains exactly `python -m playwright install --with-deps chromium` in an inline code span before the block. It tells the reader to use that command in place of `python -m playwright install chromium` at the browser-install step, after installing dependencies (`change_design.md:L20-L25,L94`, § 1 **Change Summary**, § 5 **Test Additions**).
- **V-2 / CP-70, CP-71:** The note names the system package manager and administrator rights. It explicitly says both the tracker and `pytest tests/` need none of what that command installs (`change_spec.md:L23-L24`, § **Linux — the browser step in § Running the tests**).
- **V-3 / CP-72:** The end-to-end Linux list contains Debian 12 and 13, Ubuntu 22.04, 24.04 and 26.04, and both x86-64 and arm64. `Debian 12` appears literally, with no omitted release or architecture and no extra supported Linux system (`change_spec.md:L25`, **CP-72**; `docs/SDD.md:L291-L296`, § 4 **RT-4**).
- **V-4 / CP-73, CP-75:** The last paragraph says the full suite needs both a Git repository and `git` on the path. It explains that one test fails when either prerequisite is absent, including when both are absent, and says the test checks that Git ignores saved data (`change_spec.md:L29-L31`, § **Git — the suite's prerequisite in § Running the tests**; `change_design.md:L111-L112`, § 5 **Test Additions**).
- **V-5 / CP-74:** The same last paragraph explicitly exempts the tracker itself from both Git prerequisites (`change_spec.md:L30`, **CP-74**).
- **V-6 / CP-76:** The Git explanation is one paragraph, last in the section, and states the prerequisite once. Neither original sentence from `README.md:L107` at the input revision remains verbatim (`change_spec.md:L32`, **CP-76**; `change_design.md:L26-L29`, § 1 **Change Summary**).
- **V-7 / CP-77:** Every added or rewritten sentence meets `docs/CONTENT.md:L98-L137`, § **Grammar and mechanics**, including the punctuation rules, contracted negatives, tool spelling and absence of Latin abbreviations. Count words inside command spans too; every sentence has at most 20 words. The whole README has no match for the six relative-time words in the gate below (`change_spec.md:L36`, **CP-77**; `change_design.md:L100`, **V-7**).
- **V-8 / CP-78:** Compare with the input revision: every heading, the seven-command block and the four fixed paragraphs stay byte-for-byte identical. Text before and after § Running the tests stays identical. The only product path changed is `README.md` (`change_spec.md:L37`, **CP-78**; `change_design.md:L101`, **V-8**).
- **V-9 / CP-79:** The two-pattern grep matches each pattern at least once. Every match lies after `### Running the tests` and before `## How it's built` (`change_spec.md:L38`, **CP-79**).

#### Implement

Verified by review — no test.

#### Verification gate

Run the following from the change worktree root:
`.worktrees/2026-10-11_readme-linux-setup-and-git`.
The suite command is the card's **Test command** (`system/projects/tracker17/project.md:L10`); the greps are the design's artifact checks (`change_design.md:L104-L109`, § 5 **Test Additions**).

```sh
pytest products/tracker17/tests/
grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md
grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md
```

- Suite: exit 0, all 224 existing tests pass, with no new failure.
- Six-word grep: no output, exit 1.
- Two-pattern grep: exit 0, at least one match per pattern, all within the named section.

Run these diff checks, using the input revision recorded in TL Review Notes:

```sh
git -C .worktrees/2026-10-11_readme-linux-setup-and-git diff --check 06af065b288da2e637e5b00868459d7191c33574 -- products/tracker17
git -C .worktrees/2026-10-11_readme-linux-setup-and-git diff --name-only 06af065b288da2e637e5b00868459d7191c33574 -- products/tracker17
git -C .worktrees/2026-10-11_readme-linux-setup-and-git diff 06af065b288da2e637e5b00868459d7191c33574 -- products/tracker17/README.md
git -C .worktrees/2026-10-11_readme-linux-setup-and-git show 06af065b288da2e637e5b00868459d7191c33574:products/tracker17/README.md
```

- Whitespace check: exit 0, no output.
- Product path listing: exactly `products/tracker17/README.md`, per CP-78.
- Diff and baseline reading: V-1 to V-9 each meets its criterion; record one verdict per criterion.
- CP-78 comparison: the original introductory paragraph and the three paragraphs after the block stay byte-for-byte identical. The block keeps these seven commands in this order: `cd products/tracker17`, `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r tests/requirements.txt`, `python -m playwright install chromium`, `pytest tests/`, `pytest tests/e2e/` (`README.md:L89-L105` at the input revision; `change_spec.md:L37`, **CP-78**).

Pass when every review criterion holds and the existing suite has no new failure.
