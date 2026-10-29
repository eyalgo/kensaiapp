# Flow Findings — development-specs  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 2, 3, 4, 6 and 8 found nothing. The header Category and Behaviour are copied verbatim from the request. The fix's placement carries its reason in Locked Answers. Design's calls are left to design. Lenses 9 and 10 do not apply to this step.

- **[non-blocking · change-local · evidence-that-could-have-failed]** The Out of Scope entry says the two end-to-end SIGINT tests pass in the full run and fail alone because "whether they pass depends on what ran before them". Verified Claims runs only the two outcomes. The cause (what an earlier test changes) was neither run nor named, so it is an inference. Where: `change_spec.md §Out of Scope`, `§Verified Claims` (last row). Either state it as an observation only, or run the check that finds the earlier test. Design inherits an unexplained order dependence on the very signal state it must set up.
- **[non-blocking · change-local · coverage]** The Invariant that a tracker started with SIGINT ignored keeps running (a behaviour the spec verified and wants kept) has no downstream proof. The Structural Goal requires only the stop-side proof test. Nothing in the spec asks that the preserved "keeps running" behaviour be pinned, so a later start-side change could break it unseen. Where: `change_spec.md §Invariants` (SIGINT line) against `§Structural Goal` (The proof). Direction: say whether that behaviour is pinned by an existing test, or leave it explicitly unpinned.
