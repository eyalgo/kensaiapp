# Self-answer report — `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-08
- **Sources re-read:**
  - PyPI, `https://pypi.org/pypi/playwright/json`, read 2026-10-08 at 22:54 UTC. The newest release
    is still 1.63.0, uploaded 2026-09-15T16:49. Before it came 1.62.0 (2026-07-31) and 1.61.0
    (2026-06-29).
  - GitHub releases, read the same evening through the public API. `microsoft/playwright-python`'s
    newest release is v1.63.0 (2026-09-15). `microsoft/playwright`'s newest is v1.64.0
    (2026-10-07T20:40Z). The five newest commits on `microsoft/playwright-python`, up to
    2026-10-08T18:48Z, are three fixes and two dependency bumps. None of them rolls to 1.64.
  - Chrome Releases, "Stable Channel Update for Desktop", 2026-09-08
    (`https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html`).
    It still names `153.0.8010.36` and rates the same five CVEs Critical: CVE-2026-87464, -87488
    (use after free in WebGL), -87438 (out-of-bounds write in WebGL), -87527 (buffer overflow in
    WebGL) and -87628 (use after free in Cast).
  - I did not re-read the six later Chrome stable posts that `self_answer-8.md` counted (2026-09-15
    to 2026-10-06, 21 Critical CVEs). No answer here depends on how many there are, because the
    exception below names the build, not the CVEs. I did not look for a post after 2026-10-06 either.
    A new one would add more CVEs against the same build and would not change the answer.

## Items worked

### 2.1 — QC-40's first sentence binds the change that chooses a version, the browser's included, and leaves an advisory published later to the window

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is right, and the reason it gives holds. It leaves two cases open, and the
  additions close them.

  **Whose it is (check 1).** It is mine. The item asks whether QC-40's two sentences agree with each
  other, and the edit lands in `nfdr.md` whatever the owner decides on § 3.1. This item was split out
  of § 3.1 by the previous run (`self_answer-8.md`), which left this slot for the next round. This is
  that round. A `product-architecture` run has happened since (`332311003`, NFDR version 7), which
  read the item and folded nothing, because no slot was filled (RN-30).

  **The draft holds (check 2).** Read literally, QC-40's first sentence bars every test dependency
  with a known critical vulnerability from the setup instructions. Every pinned dependency becomes
  one on the day an advisory is published against it. So the literal reading leaves nothing for the
  second sentence's 30-day window and dated exception to apply to. The draft reads the first sentence
  as binding the moment a version is chosen, and the second as binding the time after an advisory
  lands. That is the only reading under which both sentences do work. QC-40's own *verified by*
  already names the first moment: "when a change adds or changes a test dependency".

  **What it agrees with (check 3), each read at its source this run:**
  - The owner's answer that wrote QC-40, `trail/architecture/cycle-2.md` § 1.1, gives the window to
    "the browser build the pinned browser-driving library installs" by name. A reading that takes the
    window away from the browser contradicts that answer.
  - `<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies holds the same two bullets. A
    critical vulnerability "blocks release", and it "has a stated remediation window". The two can
    both be true only if the first binds the choice and the second binds what comes after.
  - The pin's history. `playwright==1.63.0` is at `tests/requirements.txt:12` and
    `pyproject.toml:14`. Both came in with commit `83563a643` on 2026-10-07, after the 2026-09-08
    advisory, when no Playwright release on PyPI installed a fixed Chromium. So the choice was proper
    under this reading, and the window holds the browser.
  - NFDR version 7 (RN-27) puts the system libraries the Linux setup installs outside QC-40. This
    answer is about the test dependencies and the browser only, so it does not touch them.

  **The two additions (check 4).**
  - **Absent: which version counts as one that "exists".** The draft says a version free of the
    advisory must be picked "when a version free of one exists". Today that has a live wrong reading.
    Playwright 1.64.0, with Chromium 156.0.8078.4, exists on npm since 2026-10-07. It is not on PyPI,
    where this product's pins come from (read 2026-10-08). A reviewer reading "exists" loosely would
    block a change for not choosing a version it cannot install. So the sentence says "published on
    the index the pin installs from", and for the browser that means a release of the library on PyPI
    whose browser build is free of the advisory.
  - **Stale: an old advisory with no fix.** The draft lets a change add a dependency whose every
    published version carries a critical advisory. That is right: sometimes no clean version exists.
    But the second sentence's window runs from the day the advisory was published, not from the day
    the dependency was added. So if that advisory is more than 30 days old, the dependency is past the
    window the moment it lands, and needs the owner's dated exception first. The draft's own logic
    gives this result. Writing it down stops a later reader from treating "added today" as "window
    starts today".
  - **Wording.** The draft's sentence, "…or moves a pin, the browser-driving library's included, which
    chooses the browser build, picks no version…", hangs two clauses off one noun. The answer splits
    it into two sentences with the same meaning.

  **Concurrent: the same round as § 3.1.** This answer is why § 3.1's exception is enough. Under it
  the window is the only rule holding the browser, so an exception from the window unblocks the setup
  instructions and the reviews. If the owner refuses the exception, the block from the window stands
  until the pin moves. This answer does not change that.

  **What would have tipped it.** I came close to a plain "confirm". The `exists` reading only became
  a real risk the day Node 1.64.0 shipped ahead of the Python package, which is today. Earlier, either
  reading of "exists" gave the same result.

## Left for the owner

### 3.1 — QC-40's 30-day window for the pinned browser build closes on 2026-10-08, and no newer pin exists

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** left for the owner
- **Why:** The item now asks one thing: does the owner record a dated exception for the browser build
  `playwright==1.63.0` installs, or let QC-40's block stand? QC-40 gives that call to the owner by
  name: "the owner records a dated exception with its reason in a Review Note here". The risk is
  theirs to carry: a browser with known critical bugs, installed on their own machine. There is also
  a ground I cannot see. `playwright install` puts the browser in a per-user cache that every
  Playwright project on the machine shares. Only the owner knows whether anything on their machine
  drives that Chromium at pages other than the tracker's.

  The item's other half, how QC-40's first sentence reads, was split out by the previous run and
  answered this run as § 2.1 (confirmed with addition). That answer is why an exception is enough.

  What changed since `self_answer-8.md`: nothing that moves the answer. PyPI still has no Playwright
  after 1.63.0, and playwright-python has no commit that rolls to 1.64. The window closes at the end
  of today, 2026-10-08, so from 2026-10-09 QC-40 blocks every `development-design` review until this
  slot is filled and folded.
- **The answer I would have given:** record a dated exception, the same one `self_answer-8.md`
  § *Left for the owner* drafted. I re-checked its facts this run and they stand:

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
  - **Letting the block stand** stops every review from 2026-10-09 until playwright-python 1.64
    ships. On the last two releases the Python package came 7 and 11 days after the Node one. Node
    1.64.0 shipped on 2026-10-07, so the block would likely last until about 2026-10-14 to
    2026-10-18. It buys no safety: blocking reviews does not take the browser off the machine.
  - **Replacing the browser** with the installed Google Chrome, through `channel="chrome"`, moves SDD
    § 4 RT-4, which is the CTO's, and the setup instructions (FDR R-8 to R-13). It also gives up the
    exact pin QC-39 rests on, because branded Chrome updates itself.
  - **Removing the end-to-end layer** breaks QC-9 (AC-20), QC-36 and QC-55, which only that layer
    checks.

  **Why the exception names the build, not the five CVEs.** More Critical CVEs against the same build
  were published after 2026-09-08 (21 from 2026-09-15 to 2026-10-06, by `self_answer-8.md`'s count).
  Their windows close from 2026-10-15 on. An exception naming only the five would block again on
  2026-10-15.

  **Failure paths.**
  - *Absent:* no fixed release by 2026-11-07. The exception lapses, and the owner chooses again
    between a second exception and the `channel="chrome"` replacement, which needs a CTO round first.
  - *Refused:* the owner refuses the exception. The block stands until the pin can move.
  - *Concurrent:* until this slot is filled and `product-architecture` folds it into a Review Note,
    QC-40 blocks every `development-design` review from 2026-10-09. A change in flight that day stops
    there.
  - *Not covered:* Playwright 1.64's Chromium 156.0.8078.4 is a pre-stable build, and the vendor's
    advisories name stable versions. So the check when the pin moves can only compare version
    numbers. 156.0.8078.4 is later than every fixed version the earlier report listed.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
