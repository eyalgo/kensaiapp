# Flow Findings — development-specs  (audited 2026-10-07)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · evidence-that-could-have-failed]** CP-46 states that `pytest tests/` and `pytest tests/e2e/` each exit 0, and no Verified Claims row ran `tests/e2e/` or the full `tests/` baseline. Where: `change_spec.md §Verified Claims` (the "unreadable-start tests" row) and `§Rules` CP-46. The one suite run was two integration files in a `git archive` copy that is not a repository, and one test failed there (`19 passed, 1 failed`). A verdict about what a command returns was not obtained in a tree where it could. Direction: run both suites in the real change worktree, and record the baseline exit and any pre-existing failure.
- **[non-blocking · change-local · altitude]** The rules carry implementation anchors. CP-39 gives "the cause is the bind error that `web/listener.py:5` says it lets propagate". CP-45 says "through the content step". CP-46 names `tests/integration/test_start.py`. Where: `change_spec.md §Rules` CP-39, CP-45, CP-46. CP-45 names a downstream step and its path to the words, which is the successor's call. Most of the other anchors are the request's own, but the rules are the contract and the anchors belong in rationale. Direction: state the observable property and leave the mechanism and the routing to design.
- **[non-blocking · change-local · coverage]** CP-40 and the Examples row say standard error is "exactly" the line, and neither fixes the trailing newline. Where: `change_spec.md §Rules` CP-40, `§Examples`. An exact-match test can be written two ways, and both pass or fail on one byte. Direction: state whether the line ends with one newline.

Checked and clean:

- **Classification.** `Category: feature` and `Behaviour: changing` match `change_request.md` verbatim.
- **Divergence record.** The narrowing and additions are in Locked Answers with reasons: the 8000 to 8017 substitution (Gap 3), stderr (Gap 1), the CP-42 edge (Gaps 4 and 5), both failures at once (Gap 6) and the holder keeping the address (Gap 7).
- **Verified Claims.** The section is present and the tree-reading citations resolve. `docs/CONTENT.md:250`, `web/listener.py` and `main.py:20` (`ADDRESS = ("127.0.0.1", 8017)`) were each opened. The `SDD.md` ids RT-5, EX-11, OB-2 and TS-4 are present.
