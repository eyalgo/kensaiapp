# 宿場 Shukuba — the setup instructions name the third line a start can print

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_protect-saved-data`. Slug: `what-the-start-prints`.*

## What it is

The README section "What the start prints" (`products/tracker17/README.md`, under `### What the start prints`) describes the ready line and says a line starting `The tracker didn't start` is the other outcome. Since the tracker now starts on unreadable saved data, a third line exists: the one starting `The tracker couldn't read`, printed while the tracker is running. This station adds that line to the section, beside the two it already describes, and says the tracker is still running when it shows. One passage, one merge; the section is the place a new operator looks first, which is why it is its own station and not folded into the page station.

## Reached when

1. In `products/tracker17/README.md`, the text from the heading `### What the start prints` up to the next `### ` heading contains the string `The tracker couldn't read` (fixed string, case-sensitive: `awk '/^### What the start prints/{f=1;next} /^### /{f=0} f' products/tracker17/README.md | grep -cF "The tracker couldn't read"` prints 1 or more). Before this station it prints 0: the only occurrences are later in the file, under the starting instructions.
2. That same text says the tracker is still running when this line shows: it contains a sentence that names the line and says the tracker keeps running, and still tells the operator what to do next (follow "Setting saved data aside"). A reader of only this section can say which of the three lines means the tracker is up and which means it stopped.
3. The section still describes the ready line and the `The tracker didn't start` line, and the wording agrees with `main.py`: the sentence beginning `The tracker couldn't read` matches the start of the text `_unreadable_line` builds there.
4. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

## Guardrail

- The README passage on the unreadable start under the starting instructions (the block quoted at lines 70–76) stays true; it is not rewritten to fit, only pointed at if useful.
- No change to `main.py`, the page, the lock or any test beyond what a README test already reads.
- The wording of the three lines is the program's; the README quotes it, never rewords the program.
- **Not here:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data` items 1 and 2 are walked (`tracker17 · shukuba · 2026-10-30_second-tracker-refusal`, `tracker17 · shukuba · 2026-10-30_unreadable-data-page`); a control that sets data aside is `tracker17 · nemawashi · 2026-10-07_first-project`'s.
