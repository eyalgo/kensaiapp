# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md` (NFDR version 11, Settled)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-12
- **Sources re-read:** None. Both answers rest on files in this repository, which were read on disk: `core/roles/CROSS_ROLE.md:L14-L19`, the product's code and tests, the SDD, the SRS and the NFDR.

## Items worked

### 3.1 — QC-21 says every action's report compares with the value the page showed; setting the operator name compares with the saved name

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** QC-21 is now false, and the item's proposed fix is right but too narrow. I treated "The change asked" as the draft. QC-21 (`nfdr.md:L171-L173`) says every report compares the submitted value with the value the page showed. SDD version 10 changed the sentence QC-21 traces to. Its § 3 `application` row (`SDD.md:L202`; RN-47, `trail/sdd/cycle-7.md` § 5.1) now says the comparison is `domain`'s, decided per action. The task edit compares with what the page showed (§ 4 RT-7). The operator name and adding a label compare with the state at the moment of the action, which is SRS NFR-3's rule (`SRS.md:L320-L322`). The code agrees. `domain/operator_name.py:L59-L62` compares with `state.operator_name`. `domain/tasks.py:L256` calls `add_label(current.labels, label)`. `application/tracker.py` saves only `if outcome.changed:`, at L75, L133, L145 and L155. This is a correction, not a widening.
  - **First addition, the label.** The item named only the operator name. A QC-21 corrected for that action alone would still be false for the label. The rule should be written per action, as SDD v10 now writes it, so it stays true when another action starts reporting.
  - **Second addition, the tests.** The current `verified by:` tail names only the task-edit test. Two tests fail if the at-the-moment comparison breaks, and both are on disk: `test_people_routes.py:L520` and `test_tasks.py:L727`.
  - **What stays.** The no-rule half stays a review at `development-design`. ADR-0001 contains no page-showed sentence (grep of `docs/adr/` finds none), so no record moves. *Inputs read* catches up to SDD version 10.
  - **Failure paths.** In the concurrent case, a stale People tab that resubmits the name another tab saved reports no change and saves nothing; the test asserts this. A stale task edit that sets a field to the value another tab saved does report a change, and it saves a state equal to the current one; SDD § 3 states this. In the empty case, an unset name differs from any submitted name, so the action reports a change. In the refused case, a blank or too-long name is refused before any outcome exists (`check_operator_name`), so it can never be a no-change outcome.
  - I considered *answered* and did not choose it. The item's proposal holds; it is incomplete, not wrong.

### 3.2 — QC-47 and RN-28 say the cross-role contract runs checks in a `git archive` copy; it now requires a fresh clone

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** QC-47 and RN-28 now misstate the contract they cite. `core/roles/CROSS_ROLE.md:L14-L19` requires "a fresh clone of the repository that holds it, checked out at the commit under test … A clone, not `git archive`". `nfdr.md:L396-L397` and `L908` still say that contract sends the run to a copy "unpacked from `git archive`". That is a fact now false, a correction and not a widening. The proposal holds: name the clone, keep the Git-repository prerequisite, and keep fail-not-skip.
  - **The addition is RN-28's *because*.** RN-28 exists because a cold reader running the suite where the contract sends them would meet one failure and misread it. A clone is a repository, so on the contract's copy the test now passes; the PM measured 937 passed at `2866e76de`. The note is still needed for a copy that is not a repository. The README's "Running the tests" already names one, "a copy … unpacked from a download" (quoted in SDD RN-39, `SDD.md:L1827-L1829`), and a `git archive` copy is another. RN-28 should name that case instead of the contract's.
  - **What stays.** The obligation itself does not move. SDD RN-39's `git archive` measurement (`SDD.md:L1820`) is a dated record of a past run, and SDD § 6 `first-project` states the prerequisite without naming any copy. Neither is false, so no SDD companion is opened.
  - **The absent case.** With no `git` on the path, the test errors rather than fails (SDD RN-39). QC-47 already lists `git` on the path as a prerequisite, so nothing is missing.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
