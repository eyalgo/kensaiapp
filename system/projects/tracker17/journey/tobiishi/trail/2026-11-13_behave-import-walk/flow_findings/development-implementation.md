# Flow Findings — development-implementation  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: the closing commit `<a commit not in the public history>` (three blocks), `tl_instruction.md`, `code-integrity-report.md`, `project.md`, the Python packet README and the cited concern lines, `docs/SDD.md` § 3, and the test names in `tests/architecture/test_behave_imports.py`.

- **[non-blocking · change-local · evidence-that-could-have-failed]** The `environment.md:16` line quotes "Python's gates run in a Linux container on the official Python image…" and concludes "bore on the closing run only", with the gates run directly on the owner's Mac through `uv run`. The quoted clause carries no no-CI exception, so the verdict reads as a divergence worded as compliance. The packet's no-CI default (`languages/README.md` § Gate environment defaults) sends the gates to the Mac, but the line does not cite it. Where: closing commit `Language resolution:` block, `environment.md:16` line. Direction: quote the clause that grants the Mac run, or record the divergence.
- **[non-blocking · change-local · evidence-that-could-have-failed]** CP-796 (the card's run lists the new module) is a *Held by review* item whose named observable is the card's closing run. The Developer Review Notes say that run's output "was not read for the module name" and rest the claim on the task 1 run. Where: closing commit § Developer Review Notes; `tl_instruction.md` Task 2 § Held by review. Direction: the observable was named and skipped. Task 2's tests appeared only in later runs.
- **[non-blocking · change-local · evidence-that-could-have-failed]** Step 1b edges missed a dangling `.behave` link (an entry that is not a folder). The Developer's "edges derived" lists absent and plain-file but not a link, and code-integrity found it red afterwards. Rule discrimination for the folder-check rule is stated honestly as "no case discriminates it", and the other two rules were established by post-landing mutation. Where: closing commit § Step 1b review; `code-integrity-report.md` § Tests added. Direction: the three-state hint named the missing case; recorded, already repaired.
- **[non-blocking · change-local · found-while-walking]** "Found while walking, not changed": a read-only temporary directory leaves a PytestWarning on every run. It is logged and passed on, with no owner named. Where: closing commit § Developer Review Notes, last item. Direction: route it to the doctrine's owner, per `found_while_walking.md`, which this audit did not open.

Lenses with no finding:
- Language match: Python resolved, matches `Languages: Python`.
- Packet roll-call: seven concerns in the README, and seven per-concern lines (the test count was made per concern).
- Quotes: the twelve cited lines were compared with the packet files and are verbatim, apart from the environment verdict above.
- Step 1b block: present, both counts present (0 and 0). All 10 Task 1 and 14 listed Task 2 test names exist in the module, and the assertions of the Task 1 and Task 2 cases the audit read were compared with the instruction.
- Multi-rule task: discrimination notes are present.
- Lens 9: `docs/SDD.md` § 3 gives no part an `Owns` over `tests/`, and code-integrity's Placement says the same and moved nothing. Skipped, with no misplacement.
- Lenses 1–6 (flow-quality, record shape): the `tests_imports` rename and the `isinstance` swap are recorded with reasons. No re-classification or enacted constraint seen.
