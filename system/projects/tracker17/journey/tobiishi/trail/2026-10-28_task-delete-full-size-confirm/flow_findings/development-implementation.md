# Flow Findings — development-implementation  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · evidence-that-could-have-failed]** The `environment.md` line in the closing commit's `Language resolution:` block reaches a verdict the quoted clause does not contain. Where: closing commit `<a commit not in the public history>`, `Language resolution:` last line. The quoted clause reads "Python's gates run in a Linux container on the official Python image, at the Python version the product's CI uses." — it carries no no-CI exception. The line says it "bore on the closing run only" and that the run "chose nothing", but the owner's-Mac fallback comes from `languages/README.md` § Gate environment defaults ("A product with no CI runs its gates on the owner's Mac."), which is not quoted. The developer's own pytest, ruff and mypy runs also ran on the Mac venv, so "closing run only" understates what the clause bore on. Direction: quote the defaults clause that grants the exception, or record the divergence from the container clause with its reason.

Checked and clean:
- Language resolution matches `project.md` `Languages: Python` and the touched `.py` files.
- All seven concerns are accounted for by their own per-concern lines; the quotes sampled against the packet (toolchain, layout, quality_gates, conventions, testing_python) are verbatim.
- Step 1b block is present; both counts are stated. Each T1–T3 assertion in `tl_instruction.md` § Behaviours to verify is present in `test_delete_task.py` (36px ±0.5, difference ≤0.5, sentence height, Back out, two-axis coverage, scrolled variant, focus, absent strip, saved bytes, failure line and description, obstruction removed in `finally`). Not-delivered = 0 holds.
- The one task landing two rules behind one entry point (`_delete_strip` size, `_delete_section` class) carries per-rule revert evidence in the notes.
- Lens 9: `docs/SDD.md` § 3 `web` owns pages and stylesheet; all production edits are in `web/pages.py` and `web/style.css`; the code-integrity Placement section lists no moves and the code does not contradict it.
- Lenses 3, 5, 8 and 10 do not apply to this step, or found nothing.
