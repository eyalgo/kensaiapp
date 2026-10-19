# Flow Findings — development-design  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited `change_design.md` against `change_spec.md` (CP-80 to CP-105, E1 to E26), and against the product's `docs/DESIGN.md`, `docs/SDD.md` § 3, ADR-0003 and the test files it cites. Lenses 1–6 and 8 walked; 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · divergence-record]** The failed-add focus target is decided without an entry. The design puts focus and description on the "Add button" (§ 3 D, outcome-address table, "Failed add" row), where CP-97 says only "focus is on the Add form". Narrowing a spec phrase to one element is a load-bearing observable choice (it is what T12 and T15 assert), and § Architect Review Notes records the other focus choices (removal heading, stale history) but not this one. Where: `change_design.md §3 Sub-job D` vs `§Architect Review Notes`. Add a one-line note with its reason.

Checked and clean:
- Coverage: every CP rule and E-row maps to a T-row (§ 5 rule-edge pass), including rule-implied edges (empty list after remove-last, legacy list, malformed present list, query-combination precedence → T18). No dropped edge found.
- Classification: `feature` / `changing` copied verbatim from the spec header.
- Contracts by construction: ordering is an ordered tuple and array; the query-outcome precedence is a stated rule.
- Constraints handed down: atomic-landing edges are stated as properties and name no downstream role. Build order is stated as contract order, with no tasks.
- Citations spot-checked at the change tip: `docs/DESIGN.md` header (three links, People after Projects), `tests/requirements.txt` holds 15 pins, ADR-0003 § Consequences Dependence text. The landed-words and saved-data test line numbers moved after implementation, which is expected and not a design defect.
