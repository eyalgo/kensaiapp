# Flow Findings — development-design  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Read against `change_spec.md`. No `docs/adr/`, `nfdr.md`, `fdr.md` or `SDD.md` exists for this product, so those cross-checks were skipped and no finding is raised for their absence. The design's claims about `_cstack` (lines 240 and 245) match the product source.

- **[non-blocking · change-local · divergence record]** The design resolves a contradiction inside the spec: it narrows CP-13 bullet 1 and pins T6, which changes values for simple multi-input right-hand operands (`Identity(2)`, `Pix2Sky_CAR`). The spec text is left as written. Where: `change_design.md §Architect Review Notes 1`; `change_spec.md §CP-13`. The divergence is recorded with its reasons, and it is flagged for the owner. But the note says "the spec has to go back" only if the owner objects, and it names no owner-confirmation step. A later step reading CP-13 against T6 sees a conflict. Direction: the record should say where the owner's answer enters, or that the design stands until it does.
- **[non-blocking · change-local · coverage]** Review Note 1 and §2 "Values that change" name a simple `separable = True` model with more than one input (`Pix2Sky_CAR`) as an operand whose value changes. T6 pins only `Identity(2)`. No row covers a `separable = True` simple operand, which is the other half of the class the design says it is changing. Where: `change_design.md §5 T6`, `§2`. Direction: a row for that member, or a line saying why `Identity(2)` stands for it.
- **[non-blocking · change-local · step-specific contract]** Section numbering skips §3 (§1, §2, §4, §5). Where: `change_design.md`. Possibly a dropped section, such as a parts or placement section. §2 does say that no parts table exists, so nothing load-bearing looks missing. Direction: renumber or state that §3 is intentionally absent.

Lenses 2, 3, 5, 8 and 10: clean. Category and Behaviour were copied verbatim. CP-12 is realized by construction (Note 2), not by coincidence. The design hands down properties without naming a downstream role or enacting its decisions. `Publishes text: no`, so lens 10 does not apply.
