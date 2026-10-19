# Flow Findings — development-specs  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1, 3, 4, 5, 6, 8 and 7 (specs form): clean. Header `bug` / `changing` copied verbatim from `change_request.md`, in vocabulary. `## Verified Claims` is present and its verdicts were run (command, tree, result), not read. Every rule maps to Examples rows and to CP-13 proof cases. Each gap is recorded with its reason in `## Locked Answers`.

- **[non-blocking · change-local · altitude]** Mechanism leaks into the rationale. Gap 3 states "emptying in place meets every rule" and "a fix that keeps the old list's contents could meet them as well". Where: `change_spec.md §Locked Answers, Gap 3`. The spec says elsewhere that pinning an outcome would "pick the mechanism of the fix", yet the rationale argues in mechanism terms. Direction: state only the observable (a list held across a clear is unspecified).
- **[non-blocking · change-local · altitude]** The Change Summary names the cause as source lines and a mechanism (`logging.py` line 699, `clear()` "swaps in a new list rather than emptying"). Where: `change_spec.md §Change Summary`. The rules themselves stay observable, but a storage anchor sits in the spec's lead paragraph, where design reads first. Direction: keep the cause as evidence in Verified Claims; keep the summary at the observable.
- **[non-blocking · change-local · evidence-could-fail]** Two *Today* values were not run as stated. The CP-11 row "Setup logs `s1` with no clear; during call, clear; `get_records("setup")` is `[s1]`" was not run. The probe's setup fixture cleared and logged `s2`, so that variant was inferred from Gap 1. Where: `change_spec.md §Examples` against `§Verified Claims`. The expected value is also CP-11's own rule, so the risk is low. Direction: run the no-clear-in-setup variant.
