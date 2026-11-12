# 宿場 Shukuba — a failed action at a non-text-byte path prints its error text as the system reported it

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`. Slug: `failed-action-path`.*

## What it is

When an action fails (a save, say), the tracker prints its plain sentence, which names no path, then the underlying error text
(`Site._report_failure`, `products/tracker17/web/routes.py`). Where the failing path holds a byte that is not text, the error
text carries it as the system reported it (`\udce9`), and `CONTENT.md` RN-35 settled that this is right: a path inside the error
text is not rewritten to `\xe9`. The site already behaves so and does not raise, and no test holds it. This station adds that
test, and changes production code only if the test shows the write raises or the path is rewritten. It is one station because
the test and a fix, if one is needed, are one behaviour.

## Reached when

All hold, checked from the repository root on `main`:

1. **The test.** A test under `products/tracker17/tests/` makes an action fail with an `OSError` whose message holds the path
   `os.fsdecode(b'/tmp/caf\xe9')` (`/tmp/caf\udce9`), and captures what the tracker writes to the console's error stream.
   It asserts: the plain sentence line (for example `Could not save.`) is written first and holds neither `caf` nor `\xe9`;
   the next line holds the error's kind and the path as `\udce9`, exactly as the error carried it, and does not hold `\xe9`;
   and the write raised nothing.
2. **It was absent.** `git grep -n 'report_failure\|Could not save' -- products/tracker17/tests` prints nothing at the commit
   this station was opened at, and prints the new test after.
3. **Not a rewrite.** The test fails when `_report_failure` is changed to rewrite the path to `\xe9` (a mutation tried and
   reverted by the walker), and the walker records that in the unit's report.
4. **Suites.** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and
   `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both exit 0.

## Guardrail

- The path inside the error text is never rewritten to `\xe9` (RN-35); only the tracker's own words use that form.
- The plain sentence names no path.
- No document is changed: `CONTENT.md` already settled the line.
- The ready line, the unreadable line and the unreadable-data page stay as landed.
- **Not here:** a character the terminal's own encoding cannot write, and a folder whose name really holds a backslash, an x and
  two hex digits, are `CONTENT.md` RN-33's "not covered" and not this station's.
- **Not here:** the start-level surfaces are `tracker17 · shukuba · 2026-10-30_ready-start` and
  `tracker17 · shukuba · 2026-10-30_unreadable-start`, both reached.
