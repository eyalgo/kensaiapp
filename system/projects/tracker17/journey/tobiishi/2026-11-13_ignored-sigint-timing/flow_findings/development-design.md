# Flow Findings — development-design  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1–6 and 8 walked against `change_design.md`, read beside `change_spec.md` and `change_request.md`. Lenses 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · divergence-record]** A security-review item with a deadline (a browser build owed by 2026-12-11) is recorded only in this change's design notes, with no owner or route out of the change folder. Where: `change_design.md §Architect Review Notes` (QC-40, browser build). The note is honest and correctly not blocking, but the change folder is not where a dated obligation gets picked up; direction: say where the owed item is carried, or state that the review step owns it.

**Lens results, stated so the file does not read as unaudited:**

- Coverage: clean. Spec I-1 to I-10 each map to a § 5 row or to the "Coverage by invariant" list. The rule-implied edges (the nested run must not recurse into the measurement; the planted leftover must be one pytest would delete; the new test must fail on an assertion, not an `ImportError`) are all in § 4.
- Altitude: clean. Mechanism sits in the design's Code Strategy, where it belongs.
- Classification propagation: clean. `Category: bug` and `Behaviour: preserving` match the spec verbatim, and `Publishes text: no` follows from preserving.
- Divergence record: clean otherwise. The one divergence from the request (cause in the test's setup, not the product, and in the 120-second outer limit, not the 30-second wait) is recorded with its reason in notes (a), and the spec's Structural Goal allows that branch. The design states the cause as a match by mechanism, not a matched log, and does not overclaim.
- Contract realized by construction: clean. The measurement asserts the shared root's listing is unchanged, which rests on pytest's own clean-up rule rather than elapsed time, and the leftover is planted so the rule applies by construction.
- Step-specific contract: clean. "Records this change makes false" is present and names what was read. No build sequence is claimed, and ordering is left to the plan step.
- Handed-down constraint: clean. The design states the red-at-base property and leaves task ordering and commits to the plan step.
