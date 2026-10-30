# 宿場 Shukuba — a start on unreadable saved data at a path with a non-text byte prints the line and serves the page

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`. Slug: `unreadable-start`.*

## What it is

When the saved data sits at a path holding a byte that is not text and the data cannot be read, the start builds the unreadable-data page (`web.UnreadableSite.__init__` encodes it as UTF-8) before it prints the unreadable line. Both raise `UnicodeEncodeError`, so the tracker does not start. This leg makes both surfaces write the path in the one form `products/tracker17/docs/CONTENT.md` § *A path the tracker prints* fixes: the byte as a backslash, an x and two hex digits (`\xe9`), nothing else in the path changed, no replacement mark. The ready start already does this through `main._shown_location`; this leg brings the unreadable line and the page to the same form. The line and the page are one behaviour (SDD § 6 S-8) and the page is built before the line prints, so they stay one merge. This development machine's file system refuses such a byte in a directory name (`mkdir` errno 92), so a real start on unreadable data there skips, as the ready start's valid-file case does; each surface's own test, fed the path as `os.fsdecode(b'/tmp/caf\xe9/data')`, is what carries the bar here.

## Reached when

1. **The line.** A test under `products/tracker17/tests/` builds the unreadable line for the location `Path(os.fsdecode(b'/tmp/caf\xe9/data'))` and holds that it contains `/tmp/caf\xe9/data` with the four characters `\xe9` in the text, contains no U+FFFD and no character in U+DC80–U+DCFF, and that `.encode('utf-8')` on it does not raise.
2. **The page.** A test builds `web.UnreadableSite` for the location `os.fsdecode(b'/tmp/caf\xe9/data')` and holds that it does not raise, and that a request to the root answers with a page whose body contains `/tmp/caf\xe9/data` with the four characters `\xe9`, no U+FFFD and no character in U+DC80–U+DCFF.
3. **The start.** A test starts the tracker through the start function on unreadable saved data at that location, with the file system calls faked or the case skipped as the ready start's valid-file case is where the machine refuses the byte, and holds that the start prints the unreadable line to the console with the path as `\xe9` and the tracker serves the unreadable-data page. If the machine refuses the byte and the test skips, the tests of 1 and 2 are the bar's carrier, and the skip is stated in the test's skip reason.
4. **Fails before, passes after.** Each test of 1 and 2 fails when run against the tree at the commit this station is opened at (`UnicodeEncodeError` or a failed assertion on the path text) and passes after. The failing run is recorded in the unit's report.
5. **Nothing else moves.** A path with no such byte prints the unreadable line and the page exactly as before: the existing unreadable-line and unreadable-page tests pass untouched.
6. **Suites.** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both exit 0.

## Guardrail

- Hold the path form to `CONTENT.md` § *A path the tracker prints*; no new wording, no other message text changes.
- Saved data is never written, replaced or deleted by a start on unreadable data, nor by serving the page (SDD SD-4); the location the claim, the load and the saves use is not changed, only how it is shown.
- No change to any document: FDR R-2, R-24 and R-25 hold as written. Not changing where the saved data lives (FDR R-16).
- The page carries no new control; the second-tracker refusal and the lock stay as landed.
- **Not here:** the failed-action console message is `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed`'s item 3, `failed-action-path`; the ready start is walked (`tracker17 · shukuba · 2026-10-30_ready-start`).
