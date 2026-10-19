# Flow Findings — development-plan  (audited 2026-10-08)

Findings for this step's output only (`tl_instruction.md`), produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.
Cross-checked against `change_design.md`, `change_spec.md`, and `change_text.md`. `docs/adr/`, `docs/nfdr.md`, and `docs/fdr.md` were not re-read: the design's Locked-record review is its own, and nothing in the plan restates them.

- **[non-blocking · change-local · contract-realized]** CP-62's run-through says to follow section 7 in a fresh copy and check `pytest tests/` exits 0. The fresh copy the plan uses is a `git archive` copy, which is not a git repository. Where: `tl_instruction.md` Task 2 §Held by review (CP-62) against its own §Corrections owed (`test_data_is_ignored_by_version_control` fails in a copy that is not a git repository) and `change_text.md` §Section 7. Direction: say the CP-62 copy is made a git repository (as CP-59 and CP-61 already are), or that the one expected failure is recorded in Developer Review Notes.
  The check as written cannot pass by the plan's own statement, so the developer must either diverge silently or report a false red.
- **[non-blocking · change-local · coverage]** The held-by-review list drops three sub-rules that the spec states. Where: `tl_instruction.md` Task 2 §Held by review. Direction: add each to its run-through.
  - CP-57: the ten-minute bound, and "needs no network connection" (the plan keeps only "installs nothing or asks for an answer").
  - CP-58: the sentence that the tracker keeps running in that terminal and that Ctrl-C stops it (CP-3).
  - CP-62: the sentence that the network is needed for the installing commands only.
  Also unchecked: CP-56's "nothing anywhere asks for an account, key, sign-up or payment" (R-14). No run-through covers the whole document, though the design delegates it to a "read the README" step.
  These are spec rules with no downstream row, and the content step is the only thing now holding them.
- **[non-blocking · change-local · coverage]** CP-57's run-through says to type "section 2's commands" and count at most three, "the version check included". Where: `tl_instruction.md` Task 2 §Held by review (CP-57) against `change_text.md` §Section 1/2 (the version check sits in section 1; section 2 has two commands). Direction: name the version check as section 1's command, so the count is not taken as two.
  A reader of the plan alone would count two and pass a README that has dropped the check from section 1.
- **[non-blocking · change-local · step-contract]** The test-shape hint is said to "also govern Task 1's test", which builds the expected sentence from one section-name constant. Task 1's behaviour, though, pins a literal whole line, and the constant is first introduced in Task 2. Where: `tl_instruction.md` §TL Review Notes (Hints carried) against Task 1 §Behaviours and Task 2 §Behaviours. Direction: state which task defines the constant and whether Task 1's test reads it or a literal.
  Two readings are possible, and the developer is left to pick one. A literal in Task 1 and a constant in Task 2 would duplicate the very name the hint says to hold once.
- **[non-blocking · change-local · divergence-record]** The gate command is handed down unresolved: the plan says it did not run the card's `pytest products/tracker17/tests/`, and tells the developer to fall back to the product-root form "if it collects nothing". Where: `tl_instruction.md` §TL Review Notes (Gate command). Direction: run the card's command at plan time and record the result, or record that the fallback is the default.
  `project.md` records that the stamped form once collected nothing and halted a seal (2026-10-07). The plan leaves an unverified gate that Task 1 and Task 2 both depend on.

**Lenses with no finding:**
- Classification propagation: Clean. `feature` / `changing` is copied verbatim from the design.
- Altitude and enacted/dropped constraints: Clean. The venv and repeated-set-aside properties are carried as properties; the plan names no downstream role's decision.
- Divergence record: the task cut and dependency edge are recorded with reasons (apart from the gate finding above).
- Lenses 7, 9 and 10 do not apply to this step.
