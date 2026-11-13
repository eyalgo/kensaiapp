# Flow Findings — development-implementation  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: the closing commit `<a commit not in the public history>`, `products/tracker17/tests/architecture/test_pins.py` at the change tip,
against `tl_instruction.md`, `change_design.md`, `code-integrity-report.md` and the card.

- **[non-blocking · change-local · evidence-that-could-have-failed (lens 7, language resolution)]** The `Gate environment` line of the `Language resolution:` block quotes `environment.md:16` ("Python's gates run in a Linux container on the official Python image, at the Python version the product's CI uses.") and concludes "bore on nothing this change wrote". The quoted clause carries no no-CI exception; the exception the verdict relies on ("A product with no CI runs its gates on the owner's Mac") is in `languages/README.md`, a line the block neither cites nor quotes. The concern also governs the run's own commands (the card's `Test command:`, run through `uv run` on the owner's Mac), so it bore on the run. Where: commit `<a commit not in the public history>`, `Language resolution:` block, `environment.md:16` line. Direction: record it as a followed-by-exception line that quotes the README clause, not as bore-on-nothing.

Checked and held:
- Resolved language (`python`) matches `project.md` `Languages: Python` and the one `.py` file touched.
- All seven packet concerns are answered by their own destination's line (Toolchain, Layout, Quality gates, Conventions, Errors and logging, Testing, Gate environment). The quoted clauses and the `test_pins.py` line numbers the lines cite match the files.
- Step 1b block is present with both counts (0 added, 0 not delivered). Each instruction case in Tasks 1 to 3 asserts what its `Behaviours to verify` entry lists (the finding names the entry; all four manifest lists appear; the plain-file, no-manifest and not-TOML cases; the lock cases).
- Tasks 2 and 3 name which case goes red when each rule alone is reverted.
- Lens 9: SDD § 3 exists; its five parts own tracker behaviour and the new logic is layer-6 test code, which `code-integrity-report.md` Placement records as having no owning part. It sits where QC-39's *verified by* puts it. No misplacement.
- Lens 6: the diff inside the product is `tests/architecture/test_pins.py` alone (CP-783). The four root tests keep every assertion (the only removed lines are the docstring, the `EXACT` pattern and the in-test parsing replaced by `pinned_pair`, which the closing commit records).
