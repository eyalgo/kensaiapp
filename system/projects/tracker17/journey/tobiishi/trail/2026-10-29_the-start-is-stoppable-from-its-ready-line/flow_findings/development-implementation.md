# Flow Findings — development-implementation  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: closing commit `<a commit not in the public history>` and the code, tests and `code-integrity-report.md` behind it, against `tl_instruction.md`, `change_design.md`, `docs/SDD.md` § 3 and the card (`Languages: Python`).

- **[non-blocking · change-local · evidence]** The `conventions.md:129` line (a port is a plain class, never `typing.Protocol`) is judged "under the clause's own words", but the exception in those words is scoped to "a **product's** repository layer". `StopRequests` and `Serving` in `main.py` are stop-and-serving collaborators, not a repository layer. The clause's other branch covers only "code no gate runs over", and mypy runs here. The cited pre-existing site (`application/contracts.py`) is not code this change wrote. Where: closing commit, `Language resolution:` block, `conventions.md:129` line. The words contain no exception for this use, so the verdict is a divergence. Direction: record it as diverged with its reason, or have the packet owner decide whether the exception reaches non-repository ports.
- **[non-blocking · change-local · evidence]** The `environment.md:16` line is judged "followed", but the quoted clause says Python's gates "run in a Linux container on the official Python image" (the block's quote also stops mid-sentence). The line itself says no container was used and the suite ran on the owner's Mac. The exception for a product with no CI is `languages/README.md:169`, which the line does not cite. As quoted, the clause has no such exception, so the verdict is a divergence. Where: closing commit, `environment.md:16` line. Direction: quote the clause that permits the no-CI path, or word it as diverged.
- **[non-blocking · skill-general · evidence]** Both findings above have the same shape: a verdict that reads as compliance because it rests on a clause elsewhere than the quoted one. `development-implementation` lets a `followed` line stand on a clause it does not quote. → kaizen `language-resolution-verdict-rests-on-unquoted-clause` (candidate; capture, not fixed).

Lenses with nothing to report:
- **Resolved language:** Python matches `Languages: Python` and the touched files.
- **Packet roll-call:** `python/README.md` lists seven concerns and each has its own per-concern lines. The quotes for `toolchain.md`, `layout.md`, `quality_gates.md`, `errors_logging.md`, `testing_python.md` and the other `conventions.md` lines match the packet text verbatim. The `toolchain.md:35` and `conventions.md:148` divergences are stated as divergences with reasons.
- **Step 1b block:** present, with both counts (3 added, 0 not delivered). All named test cases from the instruction exist, and the spot-checked assertions match their listed behaviours.
- **Multi-rule discrimination:** the notes name which case goes red when each Task 2 rule is reverted alone.
- **Placement (lens 9):** `serve_until` is in `web`, which owns listening. The signal adapter and coordinator are in `main`, the composition root and start command. The `Placement` section of `code-integrity-report.md` matches the code. No misplacement.
- **Lenses 3, 8 and 10:** not applicable to this step's artifact, or no hit.
