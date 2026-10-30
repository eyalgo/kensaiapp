# 宿場 Shukuba — a start on readable saved data prints a path with a non-text byte

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`. Slug: `ready-start`.*

## What it is

When the saved data sits at a path holding a byte that is not text, a start on readable saved data raises
while it builds the ready line, so the tracker does not start. This leg makes that start print the line
and serve. The path is written in the one form `products/tracker17/docs/CONTENT.md` § *A path the tracker
prints* fixes: the byte as a backslash, an x and two hex digits (`\xe9`), nothing else in the path changed,
no replacement mark. It is one station because the ready start is independent of the unreadable start, which
builds its page before it prints a line and is item 2 of the seed.

## Reached when

1. A test under `products/tracker17/tests/` starts the tracker on readable saved data (none yet, or a valid
   file) at a location whose path holds the byte `\xe9`, supplied as `os.fsdecode(b'/tmp/caf\xe9/data')` or
   an equivalent, and it holds that the start prints to stdout a ready line that ends
   `Saved data is kept at /tmp/caf\xe9/data.` (the four characters `\xe9` in the text, no U+FFFD) and that
   the tracker serves its page on the printed address.
2. That test fails on `main` before this change with `UnicodeEncodeError` and passes after it.
3. The line for a path with no such byte is unchanged: the existing ready-line tests still pass untouched.
4. The product's full suite passes, run as the project's `Test command:` in `project.md`.

## Guardrail

- Hold the path form to `CONTENT.md` § *A path the tracker prints*; no new wording, no other message text changes.
- No change to any document: FDR R-2, R-24 and R-25 hold as written.
- Not changing where the saved data lives (FDR R-16), nor the claim, the lock or the page beyond what the ready start needs.
- **Not here:** item 2 of the seed, `unreadable-start`, the unreadable line and the unreadable-data page, on
  `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`.
