# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. The answer rests on this repository's own documents and the Behave
  starter's README; no claim it leans on comes from a source outside the repository.

## Items worked

### 3.1 — § 9 makes the Behave call `behave` and records no way in

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** The way in is `browser`, and § 9 takes `**Behave way in:** browser` below its
  `**Behave:** behave` line.
  1. **The pick is owed, and it is this document's.** The architecture prompt has the pick made once,
     on the first run that finds the Behave call `behave` and no way in picked. § 9 has the call
     (`nfdr.md` line 720) and no way-in line, so the pick has never been made. It binds only this
     document and commits nobody outside it, so it is answered in the owner's seat, not left. It is
     not a widening with nothing behind it: the item cites the place it occurs (line 720 and a grep
     count of `0`), and the line is one the document's own template and prompt require.
  2. **Why `browser`.** The SRS makes the browser tracker17's only interface. C-3 says so, and § 3's
     operations are all reached through its pages. Several behaviours the operator relies on can only
     be seen in a browser: where focus lands after an action (SDD § 4 RT-9), the completion line's
     accessible description, and a confirmation a double press never completes (UXD UX-I2, SDD slice
     `status-moves`).
  3. **Why not the other two.** `server` sends requests and reads the pages that come back. Because
     every page is whole and runs no script (SDD TO-2), it reaches every request and every page, but
     not focus or the accessible description, so scenarios on it would leave untested the behaviours
     most likely to break. `command` reaches nothing of tracker17: its one command starts it, and SRS
     C-3 rules out a command-line interface. `server` was the near miss, and only a product whose
     behaviour all sat in its responses would have tipped the pick to it.
  4. **Settled things it agrees with.** Nothing new is installed: `.behave/pyproject.toml` already
     pins `playwright==1.65.1`, which QC-39 and QC-40 already cover. The starter's browser way-in file
     is already in `.behave/features/`. § 9's layer-7 row ("test nothing of tracker17") stays true,
     since the pick decides how future scenarios reach the product, not that any exist yet.
  5. **Failure cases.** *Absent:* where Chromium cannot run, a browser scenario cannot either. That is
     layer 5's limit as § 9 states it: macOS, and the Linux releases SDD § 4 RT-4 lists. The pick
     inherits that limit and adds none. *Stale:* the pick stands until a fresh authorization changes
     it, so a later Playwright pin move changes the platform list, not the pick. *Refused:* layer 7
     has no producer and no gate (§ 9, RN-69), so a failing browser scenario fails nothing today. The
     pick doesn't change that, and it doesn't need to.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
