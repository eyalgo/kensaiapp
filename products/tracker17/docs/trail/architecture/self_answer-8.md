# Self-answer report — `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-08
- **Sources re-read:**
  - PyPI, `https://pypi.org/pypi/playwright/json`, read 2026-10-08. The newest release is 1.63.0,
    uploaded 2026-09-15T16:49. Before it came 1.62.0 (2026-07-31) and 1.61.0 (2026-06-29).
  - Playwright's `packages/playwright-core/browsers.json` at tag `v1.63.0`. Chromium and Chromium
    Headless Shell are at revision 1243, `browserVersion` 153.0.8010.12. At tag `v1.64.0` they are at
    revision 1248, 156.0.8078.4.
  - GitHub releases. `microsoft/playwright` published v1.64.0 on 2026-10-07T20:40Z, v1.63.0 on
    2026-09-04 and v1.62.0 on 2026-07-24. `microsoft/playwright-python` published v1.63.0 on 2026-09-15
    and v1.62.0 on 2026-07-31. Its newest commits, up to 2026-10-08T18:48Z, include none that rolls to
    1.64.
  - Chrome Releases, "Stable Channel Update for Desktop", Tuesday 2026-09-08
    (`https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html`).
    It moves Chrome 153 to stable at 153.0.8010.36 for Linux. It rates five CVEs Critical:
    CVE-2026-87438 (out-of-bounds write in WebGL), -87464 (use after free in WebGL), -87488 (use after
    free in WebGL), -87527 (buffer overflow in WebGL) and -87628 (use after free in Cast). It also says
    "an exploit for CVE-2026-87491 exists in the wild". That one is rated Medium (out-of-bounds write in
    V8).
  - Chrome Releases, the desktop stable posts from 2026-09-15 to 2026-10-06, counted by the "Critical"
    rating on each:
    - 2026-09-15, 153.0.8010.47: three Critical.
    - 2026-09-17, 153.0.8010.52: two Critical.
    - 2026-09-22, 154.0.8037.57: eleven Critical.
    - 2026-09-29, 154.0.8037.92: one Critical.
    - 2026-10-01, 154.0.8037.97: one Critical.
    - 2026-10-06, 155.0.8059.39: four Critical.

    I did not read each of those bugs to see whether it affects 153.0.8010.12. The count treats every
    one as affecting it, which is the cautious reading.

## Items worked

### 2.1 — QC-40's first sentence binds the change that chooses a version, the browser's included, and leaves an advisory published later to the window

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** answered
- **Why:** This is one half of § 3.1, split off. § 3.1 asked two questions with different seats.
  - **Whose each half is.** Whether to record a dated exception is the owner's: QC-40 reserves it to
    them. What QC-40's first sentence means is a question about whether `nfdr.md` agrees with itself.
    That edit lands in this document whatever the owner decides about the exception, so it is mine.
  - **Why the split holds.** This half does not depend on the other half's answer, and it is fully
    answered below. So this run moved it to § 2 and left the original § 3.1 untouched. § 3.1 now asks
    only about the exception (see *Left for the owner*). The slot of this item stays open for the next
    round, as every raised item's does.

  **The answer.** QC-40's first sentence binds the moment a version is chosen. A change that adds a
  test dependency or moves a pin may not pick a version that a known critical advisory is against when
  a version free of one exists. That includes moving Playwright's pin, which chooses the browser build.
  An advisory published against a pin already chosen falls under the second sentence: it is fixed within
  30 days of the day it was published, or the dependency is replaced or removed, or the owner records a
  dated exception. So the browser is covered by both sentences. The setup instructions are not blocked
  today. They are blocked from 2026-10-09 by the second sentence, unless the owner records an exception.

  **Why the literal reading fails.** Taken literally, the first sentence bars from the setup
  instructions any test dependency with a known critical vulnerability. Every pinned dependency becomes
  one on the day an advisory is published against it. So that reading leaves the second sentence's
  window and exception with nothing to apply to, for packages and the browser alike.

  **What this rests on.**
  - **Check 3, against the owner's settled decision.** The owner's answer that wrote QC-40
    (`trail/architecture/cycle-2.md` § 1.1) gave the window to "the browser build the pinned
    browser-driving library installs" by name. A reading that takes the window away from the browser
    contradicts that answer.
  - **Check 3, against the floor.** `<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies
    holds the same two bullets: "blocks release", and "has a stated remediation window". They can both
    be true only if the first binds the choice and the second binds what comes after. QC-40's
    *verified by* already names the first moment, "when a change adds or changes a test dependency".
  - **The pin's history.** `playwright==1.63.0` was chosen on 2026-10-07 (commit `83563a643`), after the
    2026-09-08 advisory. On that day PyPI had no Playwright release that installs a fixed Chromium, and
    it still has none. So the choice was proper under this reading, and the browser is held by the
    window.

  **Failure paths (check 4).**
  - *Absent*, no fixed version exists. A change may still have to choose, as on 2026-10-07. The draft's
    "when a version free of one exists" lets it, and the window governs from the advisory's date.
  - *Stale*, an advisory lands after the pin is chosen. That is the second sentence's case.

  **What would have tipped it.** I came close to "the first sentence does not cover the browser",
  because the sentence says "test dependency" and B-4 lists the browser separately. That reading does
  not reconcile the two sentences for packages, and it would let a change move the Playwright pin to a
  browser build with a known critical advisory when a fixed one exists. So I did not take it.

  **Considered and not raised.** `nfdr.md`'s `Inputs read:` names SDD version 6, and the SDD is now at
  version 7. Version 7's § 4 RT-4 gives Linux setup `playwright install --with-deps chromium`, which asks
  for administrator rights to install the distribution's system libraries. That widens what B-4's
  "setup" boundary covers. I raised no separate item on it. The `product-architecture` run this round
  owes reads the SDD's change since version 6 by its own practice (RN-24, RN-26), and a separate item
  would spend a cycle on a change that run already has in front of it.

## Left for the owner

### 3.1 — QC-40's 30-day window for the pinned browser build closes on 2026-10-08, and no newer pin exists

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** left for the owner
- **Why:** QC-40 reserves this call to the owner by name: "the owner records a dated exception with its
  reason in a Review Note here, which is the only way to be past the window without being late". The
  risk is one the owner carries: a browser with known critical bugs, installed on their own machine.
  There is also a ground this run cannot see. `playwright install` puts the browser in a per-user cache
  that every Playwright project on the machine shares. Whether anything on the owner's machine drives
  that Chromium at pages other than the tracker's is something only the owner knows. The other half of
  this item, whether QC-40's first sentence covers the browser, was answered and moved to § 2.1. That
  answer is why the exception below is enough: under § 2.1, the window is the one rule holding the
  browser, so an exception from the window unblocks the setup instructions and the reviews.
- **The answer I would have given:** record a dated exception, and take neither of the other two exits.
  I would have written it into the slot as follows.

  > Exception, dated 2026-10-08. The Chromium build `playwright==1.63.0` installs, 153.0.8010.12, stays
  > past QC-40's window for every critical advisory against it. The reasons:
  > - No Playwright release on PyPI installs a later build. The newest is 1.63.0 (read 2026-10-08).
  > - The end-to-end suite launches that browser headless.
  > - The suite opens only a tracker it started itself, on `127.0.0.1` at a free port
  >   (`tests/e2e/conftest.py:79`; every `page.goto` in `tests/e2e/` goes to that address). The
  >   tracker's pages run no script (`script-src 'none'`, `web/routes.py:25`; ADR-0003, QC-34).
  > - The five advisories of 2026-09-08 are in WebGL and Cast. A page with no script does not reach
  >   either.
  >
  > The exception ends on 2026-11-07 at the latest, or earlier, on the day a Playwright release on PyPI
  > installs a Chromium build at or past the fixed version of every critical advisory then open against
  > 153.0.8010.12. From that day, QC-40's review blocks changes until the pin moves, as QC-40 already
  > says. If 2026-11-07 passes with no such release, the owner decides again.

  **Why the exception, and not the other two ways.**
  - **Letting the block stand** stops every `development-design` review from 2026-10-09 until
    playwright-python 1.64 ships. On the last two releases the Python package followed the Node one by
    7 days (1.62.0: 2026-07-24 to 07-31) and 11 days (1.63.0: 2026-09-04 to 09-15). Node 1.64.0 shipped
    on 2026-10-07 with Chromium 156.0.8078.4, so the block would likely last until about 2026-10-14 to
    2026-10-18. It buys no safety: blocking reviews does not take the browser off the machine.
  - **Replacing the browser** means driving the installed Google Chrome through Playwright's
    `channel="chrome"`. That moves SDD § 4 RT-4, which is the CTO's, and the setup instructions (FDR
    R-8 to R-13). It also gives up the exact pin QC-39 and PD-7 rest on, because branded Chrome updates
    itself.
  - **Removing the end-to-end layer** breaks QC-9 (AC-20), QC-36 and QC-55, which only that layer
    verifies.

  **Why the exception names the build, not the five CVEs.** The five Critical CVEs the item names are
  not the only ones. 21 more Critical CVEs were published from 2026-09-15 to 2026-10-06 (see *Sources
  re-read*), and their windows close on 2026-10-15, 10-17, 10-22, 10-29, 10-31 and 11-05. An exception
  naming only the five CVEs of 2026-09-08 would block again on 2026-10-15.

  **Failure paths (check 4).**
  - *Absent*: if no fixed release is out by 2026-11-07, the exception lapses. The owner then chooses
    again between a second exception and the `channel="chrome"` replacement, which needs a CTO round
    first.
  - *Refused*: if the owner refuses the exception, the block stands until the pin can move.
  - *Concurrent*: until the owner fills this slot and `product-architecture` folds it into a Review
    Note, QC-40 blocks every `development-design` review from 2026-10-09. A change in flight that day
    stops there.
  - *Not covered*: Playwright 1.64's Chromium 156.0.8078.4 is a build from before its stable release,
    and the vendor's advisories name stable versions. So the check at the review after the pin moves
    can only compare version numbers. 156.0.8078.4 is later than every fixed version listed above.

  **Outside QC-40, for the owner to know.** CVE-2026-87491 is exploited in the wild. It is rated
  Medium, so QC-40, which counts only Critical advisories, does not reach it. It is a V8 bug, and the
  tracker's pages run no script, so the suite does not reach it either.

  **Where the item's text falls short.** The item says what is true, but it counts only the 2026-09-08
  advisories. The later ones are what make an exception for the five CVEs alone too narrow. This is
  reported here and not corrected in the companion, because an item's text is its author's.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
