# Self-answer report — `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-10
- **Sources re-read:**
  - PyPI, `https://pypi.org/pypi/playwright/json`, read 2026-10-10 at 18:11 UTC. The newest release
    is still 1.63.0, uploaded 2026-09-15T16:49. The three before it are 1.62.0 (2026-07-31), 1.61.0
    (2026-06-29) and 1.60.0 (2026-05-18).
  - GitHub, `https://api.github.com/repos/microsoft/playwright-python/releases`, read the same
    minute. The newest release is still v1.63.0 (2026-09-15).
  - unreachable: Chrome Releases, "Stable Channel Update for Desktop", 2026-09-08
    (`https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html`).
    The fetch returned the post's title and date but not its body, so this run could not re-read the
    version number or the five Critical CVEs. The answer below rests on the record of
    `self_answer-9.md`, which read the post on 2026-10-08. It does not depend on the CVE list,
    because the exception names the browser build, not the CVEs.

## Items worked

None this run.

## Left for the owner

### 3.1 — QC-40's 30-day window for the pinned browser build closes on 2026-10-08, and no newer pin exists

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** left for the owner
- **Why:** The item asks one thing: does the owner record a dated exception for the browser build
  that `playwright==1.63.0` installs, or let QC-40's block stand? QC-40 gives that call to the owner
  by name: "the owner records a dated exception with its reason in a Review Note here"
  (`nfdr.md`, QC-40). The risk is the owner's to carry: a browser with known critical bugs, installed
  on their own machine. There is also a ground I cannot see. `playwright install` puts the browser in
  a per-user cache that every Playwright project on the machine shares. Only the owner knows whether
  anything else on the machine drives that Chromium at pages other than the tracker's. This is the
  same reason `self_answer-8.md` and `self_answer-9.md` left the item. Nothing since has moved it.

  **What changed since `self_answer-9.md`.** The window closed at the end of 2026-10-08, so QC-40's
  block has been live since 2026-10-09. Every `development-design` review stops until this slot is
  filled and `product-architecture` folds it into a Review Note. PyPI still has no Playwright after
  1.63.0 (read 2026-10-10), so the pin still cannot move. The project's station
  `2026-10-08_setup-instructions` is open, so the next change it sends to design meets the block.

  The item is one question. It does not split: its other half, how QC-40's first sentence reads, was
  split out earlier and folded as NFDR version 8 (RN-31).
- **The answer I would have given:** record a dated exception. It is the one `self_answer-8.md` and
  `self_answer-9.md` drafted, with its date moved to the day it is recorded. The facts below were
  re-checked this run, apart from the one source marked unreachable in the header:

  > Exception, dated <the day the owner records it>. The Chromium build `playwright==1.63.0`
  > installs, 153.0.8010.12, stays past QC-40's window for every critical advisory against it. The
  > reasons:
  > - No Playwright release on PyPI installs a later build. The newest is 1.63.0 (read 2026-10-10).
  > - The end-to-end suite launches that browser headless.
  > - The suite opens only a tracker it started itself, on `127.0.0.1` at a free port
  >   (`tests/e2e/conftest.py:79`). Every `page.goto` in `tests/e2e/test_first_project.py` goes to
  >   that tracker's address. The tracker's pages run no script (`script-src 'none'`,
  >   `web/routes.py:25`; ADR-0003, QC-34).
  > - The five advisories of 2026-09-08 are in WebGL and Cast. A page that runs no script does not
  >   reach either.
  >
  > The exception ends on 2026-11-07 at the latest. It ends earlier on the day a Playwright release
  > on PyPI installs a Chromium build at or past the fixed version of every critical advisory then
  > open against 153.0.8010.12. From that day, QC-40's review blocks changes until the pin moves, as
  > QC-40 already says. If 2026-11-07 passes with no such release, the owner decides again.

  **Why the exception, and not the other two ways.**
  - **Letting the block stand** stops every design review until playwright-python 1.64 reaches PyPI.
    On the last two releases the Python package came 7 and 11 days after the Node one, and Node
    1.64.0 shipped on 2026-10-07 (`self_answer-9.md`). So the block would likely last until about
    2026-10-14 to 2026-10-18. It buys no safety, because blocking reviews does not take the browser
    off the machine.
  - **Replacing the browser** with the installed Google Chrome, through `channel="chrome"`, moves
    SDD § 4 RT-4, which is the CTO's, and moves the setup instructions with it. It also gives up the
    exact pin QC-39 rests on, because branded Chrome updates itself.
  - **Removing the end-to-end layer** breaks the obligations only that layer checks (QC-9, QC-36 and
    QC-55, by `self_answer-9.md`'s count).

  **Why the exception names the build, not the CVEs.** More Critical CVEs against the same build were
  published after 2026-09-08 (21 from 2026-09-15 to 2026-10-06, by `self_answer-8.md`'s count). Their
  windows close from 2026-10-15 on. An exception naming only the five would block again on that day.

  **Failure paths.**
  - *Absent:* no fixed release by 2026-11-07. The exception lapses, and the owner chooses again
    between a second exception and the `channel="chrome"` replacement, which needs a CTO round first.
  - *Refused:* the owner refuses the exception. The block stands until the pin can move.
  - *Stale:* a Playwright release reaches PyPI before the owner answers. Then the fix is to move the
    pin, and the exception is not needed after that. The pin move is a change of its own, and it goes
    through design review too. QC-40's *verified by* says the block holds "until the pin moves". It
    does not say whether the change that moves the pin passes its own review. The exception, which
    ends when such a release exists, removes that doubt, so it is worth recording even then.
  - *Concurrent:* until this slot is filled and folded, every design review stays blocked. A change
    in flight stops at design.
  - *Not covered:* Playwright 1.64's Chromium 156.0.8078.4 is a pre-stable build, and the vendor's
    advisories name stable versions. So the check when the pin moves can only compare version
    numbers.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
