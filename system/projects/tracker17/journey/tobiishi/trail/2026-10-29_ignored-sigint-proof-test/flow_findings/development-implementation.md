# Flow Findings — development-implementation  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lens 9 (placement): skipped as a finding source — no production code was added; the one test module
sits in `tests/`, the unit `docs/SDD.md` § 3 places there, and matches the code-integrity report's
**Placement**. Lens 7 language resolution (Python) matches `project.md` `Languages:`; all seven packet
concerns have their own line; the Step 1b block carries both counts (0 / 0) and every behaviour in
Task 1's list is asserted by the test.

- **[non-blocking · change-local · evidence-that-could-have-failed]** The test's `1 passed` assertion is
  green over a rule that could be deleted: the Developer Review Notes say "no case discriminates it", so
  no run showed that assertion go red. Only the exit-0 assertion was flipped (the `970f6a4ca` run). Where:
  `test_sigint_launch.py` last line (`ONE_CASE_PASSED.search`); Developer Review Notes, *Rule
  discrimination*. The plan's "exactly one case passed" is a stated assertion with no failing evidence;
  disclosed, and the spec's one-test limit blocked a discriminating case. Direction: a hand-run mutation
  (a skipped selected node) recorded as evidence, or the owner ruling the assertion unneeded.
- **[non-blocking · change-local · evidence-that-could-have-failed]** The `toolchain.md:35` line cites the
  wrong owner for its override. It says the product's floor "pyproject.toml requires-python >=3.11"
  outranks the packet; the clause says the floor is 3.13 "for the products the skeleton stamps all the
  same". The override is real but lives in the product's decision file, `docs/nfdr.md` QC-59 and QC-60,
  which `languages/README.md` (§ Precedence) lets outrank a packet; `pyproject.toml` is not one. Where:
  closing commit `<a commit not in the public history>`, *Language resolution*, `toolchain.md:35`. A reader holding only the commit
  cannot tell why the packet loses. Direction: cite QC-59 as the override and label it a divergence.
- **[non-blocking · change-local · evidence-that-could-have-failed]** The `conventions.md:59` quote is not
  verbatim: it reads `"**A test function is not**" annotated`, with "annotated" outside the quotation
  marks, though the packet's sentence continues "— 1,264 of the 1,350 `def test_*` functions ... carry no
  annotation". Where: closing commit `<a commit not in the public history>`, *Language resolution*. The verdict is right; the quote
  is a splice. Direction: quote through the full clause.
