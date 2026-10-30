# Change request — 2026-10-30_ready-start-non-text-path

---

**Request:** When the tracker's saved data sits at a path holding a byte that is not text, a start on readable saved data (none yet, or a valid file) currently fails while it builds the ready line: the line's text cannot be written to the console, `UnicodeEncodeError` is raised and the tracker does not start. Make that start print the ready line and serve its page. The path in the line is written in the one form `products/tracker17/docs/CONTENT.md` § *A path the tracker prints* fixes: the byte as a backslash, an x and two hex digits (`\xe9`), nothing else in the path changed and no replacement mark, so a path decoded from `b'/tmp/caf\xe9/data'` ends the line as `Saved data is kept at /tmp/caf\xe9/data.`. Add a test under `products/tracker17/tests/` that starts the tracker on readable saved data at such a location, holds that stdout carries that ready line and that the page is served on the printed address, and fails on `main` before the change with `UnicodeEncodeError`. The line for a path with no such byte must not change, so the existing ready-line tests pass untouched, and the full suite passes as the project's `Test command:`.

Sizing: one capability (the ready start on such a path), one merge; the acceptance boundary is the station's reached-when 1 to 4. The unreadable start (its line and the unreadable-data page) is the seed's next item and stays out. The path form must hold to `CONTENT.md` with no new wording and no other message text changed. No document changes (FDR R-2, R-24 and R-25 hold as written). Where the saved data lives (FDR R-16), the claim, the lock and the page must not change beyond what the ready start needs.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 1 has a start that today raises print a line and serve, a new observable behaviour at the FDR-level contract (R-2, "shows ... the saved data's location"), not a restructuring that preserves what the suite pins.

---

**Sealed:** 2026-10-30 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
