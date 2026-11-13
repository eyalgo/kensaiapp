# Flow Findings — development-implementation  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: the code at `products/tracker17/tests/conftest.py` and `tests/architecture/test_source_walk.py`,
the closing commit `<a commit not in the public history>`, `tl_instruction.md`, `change_design.md`, `code-integrity-report.md`
and the project card. Lens 9 finds nothing: `docs/SDD.md` § 3 places the five product parts and
`tests/` is no part's `Owns`, so no logic added here has an owning part, and the code-integrity
Placement entries agree with the code. Lens 10 does not apply (`Publishes text: no`).

- **[non-blocking · change-local · step-specific contract]** The closing commit records that
  `test-driven-development` was not invoked for task 1. Step 2 of the skill says to invoke it per
  task, and it owns the red/green/refactor commits. The commits were made by hand to its shape, and
  the checklist box is left unchecked, so the departure is disclosed. Where: commit `<a commit not in the public history>`
  (*Skills run this session*); `development-implementation` SKILL.md Step 2, item 5. Nothing in the
  commit gives a reason the skill could not be invoked. Direction: the producer states why, or runs
  the skill.
- **[non-blocking · change-local · evidence that could have failed]** The `Language resolution:`
  block carries no clause for the Ruff gates the run added, nor for the `uv run --locked` runner that
  the gate commands ran under. Both are governed by a concern the block cites, but by lines it does not
  quote. Where: commit `<a commit not in the public history>`, `Language resolution:`. The packet's `quality_gates.md` § Ruff
  says "Set `line-length` from `conventions.md`" and `toolchain.md` § uv gives the runner. The block
  answers Ruff only through the `conventions.md:17` line (width 100), and answers `toolchain.md` with
  the dependency and floor lines. The concern's own clauses on the run's commands are the ones the
  lens asks to see. Direction: quote the clause for each tool the run's commands used.
- **[non-blocking · change-local · evidence that could have failed]** The block's `layout.md:17`
  line gives the verdict *followed* beside a clause (*"This file adds nothing to either."*) that
  states nothing a change could follow or break. Where: commit `<a commit not in the public history>`, `Language resolution:`.
  The line itself says the rest of `layout.md` bore on nothing, so the verdict should read
  *bore on nothing this change wrote* and not *followed*. A wording slip only; the concern is
  accounted for.

Checked and clean:

- **Resolved language.** Python, as the card's `Languages:` and the touched `.py` files say.
- **Packet roll-call.** All seven concerns of the packet's `README.md` have per-concern lines; every
  quoted clause was opened and matches its file and line (`toolchain.md:35`, `:87`, `layout.md:17`,
  `quality_gates.md:14`, `:33`, `conventions.md:17`, `:21`, `:49`, `:87`, `:92`, `:159`, `:163`,
  `errors_logging.md:12`, `environment.md:16`). The `toolchain.md:35` divergence (the product's
  Python 3.11 floor over the packet's 3.13) is recorded with its reason. `environment.md:16` is
  consistent with the no-CI rule in `languages/README.md` § Gate environment defaults.
- **Step 1b.** Present, with both counts (0 added, 0 not delivered). Each of the five instructed
  behaviours asserts what its `Behaviours to verify` entry lists; read against
  `test_source_walk.py`, none is short. Code-integrity then added two cases from spec words.
- **Multi-rule task.** The notes name the case that goes red when each rule alone is reverted
  (`tests`, `.behave`, `.venv`, `__pycache__`, and the leading-dot test).
- **Classification.** `nfdr` / `changing` carried from design to plan unchanged.
- **Divergences.** The underscore rename is recorded with its reason. The new module restates the
  skip set instead of importing it from the walk; this is sound for a test (an oracle independent of
  the code under test) and no finding.
- **Owed outside the change.** `docs/nfdr.md` § 1.1 QC-1 is named by the design, the plan, the
  developer and code-integrity as owed to its owner; no one edited it here.
