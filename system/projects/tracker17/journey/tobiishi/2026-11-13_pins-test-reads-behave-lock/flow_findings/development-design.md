# Flow Findings — development-design  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1 to 5, 6 and 8 walked against `change_design.md` beside `change_spec.md`. Lenses 7, 9 and 10 do not apply to this step. `docs/adr/`, `docs/nfdr.md` and `docs/fdr.md` were present and cross-checked.

- **[non-blocking · change-local · divergence record]** The design's "Records this change makes false" section names `docs/nfdr.md` QC-39 *verified by* as going false, but that document sits inside the product folder and CP-783 confines the product diff to `test_pins.py`. The design does not say who corrects the record or when, or that CP-783 is why it is left. Where: `change_design.md §Records this change makes false` against `change_spec.md` CP-783. The successor's instruction does carry it as "Owed outside this change's reach", so nothing is lost; direction: state the owner of the correction in the design itself.

Otherwise clean:
- **Coverage:** every rule (CP-773 to CP-784) and rule-implied edge (wildcard, extras, case folding, an empty lock, an unreadable file) maps to a §5 row or a covered-by note.
- **Altitude:** held.
- **Classification:** `nfdr` / `changing` copied verbatim.
- **Divergence record:** the one design-level divergence (`EXACT` refusing `*` for both sets) is recorded with its reason in Architect Review Notes.
- **Handed-down constraints:** stated, not enacted.
- **Step contract:** the design stays inside the one file.
