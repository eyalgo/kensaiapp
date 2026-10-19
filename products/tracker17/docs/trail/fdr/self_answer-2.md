# Self-answer report — products/tracker17/docs/fdr.md

## Header

- **Companion:** products/tracker17/docs/fdr_open_issues.md
- **Document:** products/tracker17/docs/fdr.md (version 3)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** https://playwright.dev/python/docs/browsers. It says `--with-deps` installs
  "the browsers and OS dependencies … with a single command", through "the linux package manager",
  and that Playwright "will attempt to become a root" to do it. https://playwright.dev/python/docs/intro,
  "System requirements", lists "Debian 12 / 13, Ubuntu 22.04 / 24.04 / 26.04 (x86-64 or arm64)". That
  is the list SDD § 4 RT-4 quotes. The page shows no version number.

## Items worked

### 2.1 — PRD v5 and SRS v5 add a fourth priority, `critical`, and the FDR now follows them

- **Bucket:** 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** The draft holds, and it holds for the reason it gives. Every claim checks out at its source.
  PRD § Core Features, Priorities (`PRD.md:128`) reads "A task is `low`, `medium`, `high` or
  `critical`". The PRD preamble (`PRD.md:115-116`) makes Priorities "The one exception". SRS v5
  FR-15 (`SRS.md:132`) names the four. FR-36 (`SRS.md:234`) has ascending run `low`, `medium`,
  `high`, `critical`. FR-38 (`SRS.md:255`) counts "each of the four priorities, a zero count
  included". C-5 (`SRS.md:436-437`) declines tracker16-X's three-value set. R-51, R-90, R-96, PD-5
  and RN-6 say the same. R-90's descending order is the exact reverse of FR-36's ascending order.
  FR-36 states only the ascending order, and FR-36's direction rule implies the reverse.
  The draft says no other FDR entry names the priority set. A search of `fdr.md` for `critical` and
  for the backticked values agrees: only R-51, R-90, R-96, PD-5 and RN-6 name them. R-21's "unknown
  priority" reads against R-51, and R-42 keeps `medium` as the default.
  Check 3 also covered the siblings, which carry no stale copy of the old set. UXD, SDD, DESIGN and
  NFDR say "per priority" or "each priority" and list no values (`UXD.md:201`, `UXD.md:209`,
  `SDD.md:463`). CONTENT.md:150 still lists `critical` among the words not to use. That is CONTENT's
  collision, and `CONTENT_open_issues.md` § 3.1 already carries it, so the FDR owes nothing for it.
  Check 4: the four failure paths are covered.
  - Empty: R-96 shows a zero `critical` count.
  - Refused: R-51 still refuses any fifth value.
  - Stale: R-102 checks a priority edit made from an old page against the saved data.
  - Saved data: once R-51 names `critical`, R-21 accepts a saved `critical` task as readable.
  An override would have needed the PRD or the SRS to change first, and neither has.

### 2.2 — SDD versions 4 to 7 changed what the setup instructions say for Linux, and the FDR now follows them

- **Bucket:** 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** The draft holds for the reason it gives. SDD v7 § 4 RT-3 (`SDD.md:269-280`) says the tracker
  runs on any Linux with Python 3.11 or later, and that the end-to-end suite runs on fewer systems.
  RT-4 (`SDD.md:281-301`) says the following about the instructions:
  - They give the `--with-deps` install for Linux.
  - They say that step runs the package manager and asks for administrator rights.
  - They say the tracker and `pytest tests/` need none of it.
  - They carry the pinned library's list of Linux systems.

  R-119, R-120 and PD-8 carry exactly this. R-120 rightly names no list, because RT-4 says "The list
  is the pin's and moves only when the pin does".
  Check 3 at the outside source: Playwright's own pages agree with what R-119 has the instructions say
  (Header, Sources re-read). The system-requirements list matches the one RT-4 quotes. R-119 and R-120
  do not depend on the list's contents.
  The review-note claims check out:
  - SDD § Open Questions (`SDD.md:1769-1774`) holds only the `autofocus` question.
  - UXD v4 has the description and comment fields state their maximum (`UXD.md:5`, UX-S6).
  - UXD v4 UX-F9 keeps an assignee left as the page showed it, which closes RN-12's collision.

  The draft's four no-rule decisions also hold:
  - The port value is the SDD's, because R-4 and PD-10 fix only that the address is fixed.
  - SEC-2, SEC-3 and TS-4 are mechanisms.
  - The Git prerequisite stays out. It sits in SDD § 6 S-1's *Artifact* (`SDD.md:681-687`), and the
    `product-fdr` prompt says "Do not read §§ 6, 7 and 8 into the FDR". No § 4 condition states it.

  Check 4: the failure paths are covered.
  - A Linux off the list: PD-8 says the tracker and the non-browser tests still run.
  - No administrator rights: R-119 says the tracker needs none.
  - A pin that moves: R-120 follows the pin by naming no list.

  An override would have tipped only if some § 4 condition stated the Git prerequisite. None does. If
  the owner wants it carried, SDD § 4 has to state it first, as the draft's "If overridden" says.

## Left for the owner

None this run.

## Skipped

- **§ 1. Open issues** — the section reads "None.", so nothing was there to answer.
- **§ 3. Raised from downstream** — the section reads "None.", so nothing was there to answer.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/fdr.md** — `<CORE>/launchers/skill/launcher.sh product-fdr tracker17`
