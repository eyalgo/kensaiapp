# Architecture open issues — tracker17

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-40's browser exception ended on 2026-11-07, and QC-40 still names it as in force
- **Raised by:** Architect — 2026-11-13
- **Which record:** `nfdr.md` § 2, QC-40, and § NFDR Review Notes, RN-33
- **Tracked by:** no seed watches it. The instance's upkeep register carries the lapse as a row, as
  RN-33 says.
- **What it blocks:** every `development-design` review. QC-40's *verified by* says a critical
  advisory more than 30 days old "blocks the change until the pin moves or a dated exception is
  recorded", and RN-33 says "After that date, with neither done, QC-40 blocks every review again."
  Neither has been done: `pyproject.toml:17` and `.behave/`'s lock still pin `playwright==1.63.0`,
  and the installed browser still reports `Google Chrome for Testing 153.0.8010.12`.
- **Where it shows:** two statements in the NFDR cannot both hold. QC-40's trace tag reads "RN-33
  for the dated exception in force". RN-33 reads "2026-10-10 to 2026-11-07", and today is
  2026-11-13. RN-33's reason has also stopped being true. It reads "no newer Playwright exists on
  PyPI, so the pin cannot move", but PyPI now lists `1.64.1` (uploaded 2026-10-22), `1.65.0`
  (2026-11-09) and `1.65.1` (2026-11-11) (`https://pypi.org/pypi/playwright/json`, read 2026-11-13).
  The rest of QC-40 was checked the same day and blocks nothing. GitHub's global advisories list no
  critical advisory against any package either lock file fixes. The package feed is still down: the
  Dependabot alerts endpoint refuses with "Dependabot alerts are disabled for this repository.", so
  the feed's return check is still owed.
- **If a document has to be written:** none. Once the owner rules, QC-40 and RN-33 say which of
  three things holds. (a) The pin moves to a Playwright release whose browser build has no critical
  advisory more than 30 days old. QC-40 checks that build afresh, and RN-33 is closed. (b) The
  exception is renewed with a new end date and a reason that holds today. (c) Neither is done, and
  QC-40 no longer calls an exception in force.
- **Answer:** (a) — the pin moves. Owner, 2026-11-13: "Move the pin". Done on `main` at `21588ead4`: every pin (`pyproject.toml`, `.behave/pyproject.toml` and the starter template, with their `uv.lock` files) reads `playwright==1.65.1`, which installs Chromium 158.0.8127.18; no Critical advisory stands against that build (checked 2026-11-13, evidence in `system/projects/tracker17/docs/playwright-pin-moves/delegate-report.md`). `uv lock` dropped `pyee` 13.0.1, which 1.65.1 no longer needs. RN-33 closes. The same report lists 34 lines under `docs/` that still name `1.63.0` or `153.0.8010.12` (nfdr.md, SDD.md, ADRs 0010, 0012, 0015); fold them to the new pin and build, and raise the SDD's lines on its own companion. The platform list at `nfdr.md:704` follows 1.65.1's documentation, which is unchecked.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
