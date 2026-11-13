# Flow Findings — development-specs  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3 (classification copied verbatim from the request, in vocabulary), 5, 6 and 8 found nothing. Altitude (lens 2) holds: the table names and the `uv run` command come from the request and QC-39.

- **[non-blocking · change-local · coverage]** CP-774's "does not read as TOML" and CP-775's "does not read as TOML" sub-cases have no Examples row, and CP-776's name-normalisation (`Behave==1.3.3`) is an Examples row with no test in CP-779's list. Where: `change_spec.md §Rules CP-774/CP-775/CP-779, §Examples`. Rule-implied edges (corrupt TOML, case-folded name) risk being dropped downstream; direction: map each to a named test case or an Examples row.
- **[non-blocking · change-local · coverage]** CP-776 is silent on a lock holding several records of one name at different versions. Where: `change_spec.md §Rules CP-776`. "A package record whose name and version equal" reads as any-match; state it or the downstream reader will pick.
- **[non-blocking · change-local · evidence-that-could-have-failed]** The Verified Claims row on the suite's set (four lists, `[-_.]+` folding, extras cut) was read from the source of `test_pins.py`, not run. Where: `change_spec.md §Verified Claims`, row 6. It is a claim about what the existing check decides, and the spec builds CP-773/CP-776 on it. Direction: run the check on a lock/manifest pair that differs only by case or separator and quote what came back.
