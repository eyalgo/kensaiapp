# Flow Findings — development-implementation  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: closing commit `726104505` (and the task commits before it) against `tl_instruction.md`, `change_design.md`, `docs/SDD.md` § 3, `code-integrity-report.md` and `project.md`. Lenses 1–6 and 9 found nothing; lens 7 found the two below. Lens 8 and lens 10 do not apply to this step.

- **[non-blocking · change-local · evidence]** The `environment.md:16` line is closed as "bore on nothing this change wrote: the product has no CI", though the concern governs where the run's own gate commands ran. Where: commit `726104505`, `Language resolution:` block. The card's `Test command:` ran on the owner's Mac, which is what `languages/README.md` § Gate environment defaults sets for a product with no CI (line 169: "A product with no CI runs its gates on the owner's Mac."). The line should quote that clause and say the run followed it, not "bore on nothing". Direction: a concern that governs the run's commands is answered with the clause it applies.
- **[non-blocking · change-local · evidence]** The Toolchain line quotes only the dependency clause (`toolchain.md:89`) and leaves the interpreter clauses unaccounted for. Where: commit `726104505`, `Language resolution:` block. The gate commands ran as `uv run --locked --project …`, and `toolchain.md` § Interpreter fixes the runner and a supported floor ("The supported floor is Python 3.13", one number "for the products the skeleton stamps"). The product declares a 3.11 floor, and `tl_instruction.md` makes that binding. A packet clause the product departs from is a divergence to record with its reason, and none is recorded. Direction: the Toolchain concern gets a second line for the interpreter and floor clause, either followed or diverged with the reason.

Checked and clean:

- **Language** — `Python` matches `project.md` `Languages:` and the files touched.
- **Packet roll-call** — all seven concerns have their own per-concern line, and the floor `developer_standards.md` is read too.
- **Step 1b block** — present, with both counts. All 21 named cases of the instruction exist. The two with no case of that exact name (`test_invalid_location_keeps_the_unreadable_start_contract`, `test_failed_start_releases_its_location_for_retry`) are split by cause in `tests/integration/test_start.py`, and each listed assertion is present (exact unreadable line, exit 1, bytes and listing, retry ready with HTTP 200, unrelated bind error unchanged). The split is stated in the block.
- **Rule discrimination** — present for both multi-rule tasks, naming which case flips per rule.
- **Divergence record** — the `__version__` marker departure and the third README place are both recorded with reasons.
- **Lens 9** — claim, identity check and rollback sit in `persistence/location_use.py`. Composition and the typed-message mapping sit in `main.py`. This matches SDD § 3 `Owns` and `Must not own`, and `code-integrity-report.md` § Placement records no move.
