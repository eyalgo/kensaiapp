# Flow Findings — development-specs  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · altitude]** Rules CP-609 and CP-610 carry mechanism and storage anchors in the rule text: the CSS class `delete-button`, `web/style.css:228-244` `height: 28px`, `web/pages.py:855-863` `size=TRIGGER_SIZE` / `"row-control"`. Where: `change_spec.md §Rules` (CP-609, CP-610). The rules are output-observable (36px ±0.5 bounding box); the "today it measures 28px because …" clauses are rationale and belong in Verified Claims, where they already appear. Direction: drop the code anchors from the rule bodies so design owns how the height is reached.
- **[non-blocking · change-local · coverage]** CP-609 states three forms of the first press (ordinary, restored after Back out, after a failed save) and Examples rows cover them, but the test rule CP-614 measures only the ordinary page and the confirmation. Where: `change_spec.md §Rules` (CP-609 vs CP-614). A rule-implied variant with no test rule can be dropped downstream and still leave the suite green. Direction: have CP-614 (or a sibling rule) name the Back-out and failed-save forms, or record why the ordinary page is enough.

Checked and held: Classification (`feature` / `changing`) copied verbatim from the request; the request's false premise (first press already 36px) is recorded with its reason in Locked Answers Gap 1 and backed by run measurements; `## Verified Claims` is present and its decisive claims were run (command, tree, harness, result), not read; no `Handed-down` constraint enacted or dropped; the missing-FDR and optional-doc cases do not apply.
