# Flow Findings — development-specs  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · coverage]** CP-431 states that `Straße` and `STRASSE` are equal under Unicode case folding, but no Example row and no CP-448 unit case carries it; CP-448 names only FDR's `beta`/`Alpha`/`alpha` example. Where: `change_spec.md §Rules CP-431`, `§Examples`, `CP-448`. A rule-implied edge (folding that changes length) with no downstream test row; direction: add an Example row and name it in CP-448. Also, Locked Answers Gap 3 justifies code-point order but not the stronger-than-"ignores case" choice of full case folding.
- **[non-blocking · change-local · coverage]** CP-444 (sort address for a missing project shows not-found) and CP-445's keyboard-only path have Example rows but no line in CP-449's layer-3/4 list. The combined sort-plus-filter refusal of CP-442 (focus on the first refused field in the filter-then-sort order) is an Example row, but CP-449 lists "one test per refusal kind of CP-441" only. Where: `change_spec.md §Rules CP-449`, `§Examples`. Rules with examples but no test row can drop out downstream; direction: name them in CP-449.
- **Lens 2 (altitude):** no finding. Orderings are keyed to output-observable values (task number in the title link address); mechanism named only where the records fix it.
- **Lens 3 (classification):** no finding. `feature` / `changing` match `change_request.md` verbatim.
- **Lens 4 (divergence record):** no finding. Gaps 1–18 record each decision with its reason, including the request-versus-spec differences (POST/GET both timed as GET, CP-456 existing tests changed).
- **Lens 5, 6, 8:** no finding.
- **Lens 7 (evidence):** no finding. `## Verified Claims` is present; the claims about what commands decide (probe at the base commit, the architecture-test run with and without `sorting`, the 28-test timed-run count, the rule-ID grep) were run and give the command, tree and result. The remaining rows quote source or tests read, which are claims about code, not verdicts.

Two findings, both non-blocking; otherwise clean.
