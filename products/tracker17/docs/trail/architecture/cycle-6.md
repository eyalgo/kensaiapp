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

> **No producing run wrote this file.** The PM opened it on 2026-10-08, in a route review, to carry
> item § 3.1. `product-architecture` has no record of writing it, and it exists because the records
> read settled while QC-40's window is about to close with no pin to move to.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 QC-40's first sentence binds the change that chooses a version, the browser's included, and leaves an advisory published later to the window

> **No `product-architecture` run wrote this item.** The `companion-self-answer` run of 2026-10-08
> split it out of § 3.1 while answering that item. This is the half of § 3.1 that asks whether QC-40's
> first sentence covers the browser and blocks the setup instructions today. The run answered it, and
> its reasoning is `products/tracker17/docs/trail/architecture/self_answer-8.md` § *Items worked*.
> § 3.1 is now left asking one thing only: whether the owner records a dated exception for the
> browser build Playwright 1.63.0 installs, or lets QC-40's block stand, now that the window has
> closed and there is no pin to move to. Its slot stays open for the owner.

- **Lands in:** `nfdr.md` QC-40, its first sentence, and one new Review Note
- **Drafted into the records:** nothing. The records are untouched. The draft is to restate QC-40's
  first sentence as: "A change that adds a test dependency or moves a pin, the browser-driving
  library's included, which chooses the browser build, picks no version that a known critical
  advisory is against when a version free of one exists." Add a Review Note saying that an advisory
  published against a pin already chosen is the second sentence's, and its window runs from the day
  the advisory is published. Under this reading the browser is covered by both sentences. The setup
  instructions are not blocked today: `playwright==1.63.0` was chosen on 2026-10-07 (commit
  `83563a643`), when no Playwright release without these advisories was on PyPI. Its browser is held
  by the window, and the window closes at the end of 2026-10-08.
- **Rationale:** read literally, the first sentence bars any test dependency with a known critical
  vulnerability from the setup instructions, from the day the advisory is published. Every pinned
  dependency becomes one of those on that day. So that reading makes the second sentence's 30 days
  and its dated exception impossible to use, for packages and for the browser alike. It also
  contradicts the owner's answer that wrote QC-40 (`trail/architecture/cycle-2.md` § 1.1), which
  gave the window to "the browser build the pinned browser-driving library installs" by name. The
  floor QC-40 realizes has the same two bullets
  (`<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies: a known critical vulnerability
  "blocks release", and it "has a stated remediation window"). The two hold together only if the
  first binds the moment a version is chosen and the second binds the time after an advisory lands.
  QC-40's *verified by* already gives the first its own moment: "when a change adds or changes a
  test dependency".
- **If overridden:** with "the first sentence covers the browser literally", the setup instructions
  have broken QC-40 since 2026-09-08. They stay broken until a Playwright release on PyPI installs a
  fixed Chromium. Neither the window nor an exception would help, so § 3.1's exception would unblock
  nothing. With "the first sentence does not cover the browser", the browser is held to the window
  only, and a change that moves the Playwright pin may choose a browser build with a known critical
  advisory when a fixed one exists.
- **Confirm or override:** confirm, with two additions. First, "a version free of one exists" means a
  version published on the index the pin installs from: PyPI for the packages, and, for the browser, a
  release of the browser-driving library on PyPI whose browser build is free of the advisory. A
  release elsewhere does not count. Playwright 1.64.0 shipped on npm on 2026-10-07 and is not on PyPI
  (read 2026-10-08), so no change to this product can choose it. Second, a change that adds a
  dependency whose every published version carries a critical advisory may choose one. The second
  sentence's window has been running since that advisory was published, though, so where the advisory
  is more than 30 days old the change needs the owner's dated exception before it lands. Write the
  first sentence as two, so the browser clause reads plainly: "A change that adds a test dependency,
  or moves a pin, picks no version that a known critical advisory is against when a version free of
  one is published on the index the pin installs from. Moving the browser-driving library's pin
  chooses the browser build, so the browser build is held to the same rule." Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-9.md` § 2.1.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-40's 30-day window for the pinned browser build closes on 2026-10-08, and no newer pin exists
- **Raised by:** PM — 2026-10-08
- **Which record:** `nfdr.md` § QC-40 (`nfdr.md:291-308`), and its Review Notes, where QC-40 says a dated exception is recorded
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** every `development-design` review from 2026-10-09. QC-40's *verified by* says "a critical advisory more than 30 days old blocks the change until the pin moves or a dated exception is recorded".
- **Where it shows:** `tests/requirements.txt:12` pins `playwright==1.63.0`, which installs Chromium and Chrome Headless Shell `153.0.8010.12`, revision 1243 (`browsers.json` at tag `v1.63.0`). The Chrome Releases post of 2026-09-08 rates five CVEs Critical, all fixed in `153.0.8010.36`: CVE-2026-87438, -87464, -87488, -87527 and -87628. Counted from that post, they are 30 days old on 2026-10-08, the last day QC-40's window allows. PyPI's newest Playwright is still 1.63.0, uploaded 2026-09-15 (`https://pypi.org/pypi/playwright/json`, read 2026-10-08), so the pin cannot move. QC-40 leaves two other ways out: replace or remove the dependency, or have the owner record a dated exception with its reason in a Review Note. Neither is recorded. Also open: does QC-40's first sentence, "a test dependency with a known critical vulnerability is not installed by the setup instructions", cover the browser? The README's "Running the tests" section now installs it with `python -m playwright install chromium`. If it does, the window does not apply to the browser, and the setup instructions are blocked today.
- **If a document has to be written:** none — the fold is an edit to `nfdr.md`, by `product-architecture`. An exception is the owner's to record. Replacing the browser-driving library would also move SDD § 4 RT-4 and the end-to-end layer it pins.
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.
