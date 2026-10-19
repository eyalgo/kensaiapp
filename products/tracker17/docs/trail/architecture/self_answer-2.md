# Self-answer report — `adr/` and `nfdr.md` (tracker17)

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md` (the one open item lands in `nfdr.md` QC-40)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:**
  - https://docs.github.com/en/code-security/dependabot/dependabot-alerts/about-dependabot-alerts — alerts are raised when "A new vulnerability is added to the GitHub Advisory Database" or when the dependency graph changes. Repository administrators "can enable Dependabot alerts", and email goes to people with write, maintain or admin permission who watch the repository. The page does not say whether a private repository can have alerts.
  - https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories — the part read (the first 100,000 of 149,292 characters) lists pip, pip-compile, pipenv and poetry. It does not say which manifest or lock file each one reads, so it does not settle whether the lock file QC-39 requires would be read.

Only one item was open, so there was nothing to put in order.

## Items worked

None this run.

## Left for the owner

### 1.1 — How long may a known critical vulnerability in a test dependency stay unfixed?

- **Bucket:** 1. Open issues — questions with no answer yet
- **Verdict:** left for the owner
- **Why:** All four checks were run, and two grounds I can name keep this item with the owner.
  **First, the window commits the owner's time.** The dependency floor says the gate must name "who
  watches the advisory feed" (`<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies). In
  a one-operator product, that person can only be the owner (SRS NFR-7). An answer that names a
  person and the date they will be late by is an answer that person makes.
  **Second, either answer waives a floor or sets the risk the owner accepts.** The floor reads
  "A product that names no window has an obligation nobody is late against", and a floor holds for
  every product (`quality_defaults.md` § What is not a floor). So the item's other answer, "no window
  while tracker17 is unpublished", is not a value inside QC-40. It sets a doctrine floor aside for
  this product. Doctrine is the owner's, and no role may override it (`<CORE>/roles/CROSS_ROLE.md`
  § 3, "Doctrine is user-owned; role-level override of doctrine is not permitted"). **I have
  changed my recommendation from last round.** Last round
  (`trail/architecture/self_answer-1.md` § *Left for the owner*) recommended "no window". That
  answer had not been checked against the floor's own sentence, which is check 3's job, and it does
  not pass. What changed my recommendation is that sentence, not any new fact about the product.
  **The routing is settled now.** The item now lands in QC-40 itself (`nfdr.md` RN-10), so the owner's
  answer is folded by `product-architecture` with no SRS round first.
  **Failure paths, walked against the answer below.** *Empty:* nothing is pinned yet. The product
  holds only `docs/` (`ls products/tracker17` on 2026-10-07), so the window binds from the first
  pinned test dependency and is idle until then. *Stale:* QC-40's gate as it stands is a review at
  `development-design` "when a change adds or changes a test dependency". An advisory published
  against an existing pin, while no change touches dependencies, reaches nobody through that gate.
  The window, with a named watcher, is what makes someone late in that case. *Refused:* an advisory
  with no fixed version cannot be fixed by upgrading. The answer gives that case its own way out.
  *Concurrent:* each advisory runs its own window from its own publication date. *Absent:* if the
  feed cannot be reached, the watcher checks the advisories by hand at each design review.
  **The feed is not settled here.** GitHub's Dependabot alerts are the obvious feed for a GitHub
  repository. They fire when an advisory is added to the GitHub Advisory Database, and they email
  admins who watch the repository. But the pages I read do not say whether a private repository can
  have them. They also do not say which Python lock files are read, and the lock file's format is not
  chosen yet (SDD § 4 RT-4, "one committed file"). So the answer names the watcher and the source of
  the advisories, and leaves the tool to `languages/python/quality_gates.md` § *What is not installed*.
  Adding a tool there is a toolchain decision (`nfdr.md` RN-10).
  What would tip this item to *answered*: the owner stating, anywhere this run can read, how much of
  their time they give to watching advisories.
- **The answer I would have given:** A stated window of **30 days from the day the advisory is
  published**, for a critical advisory against any pinned test dependency or anything it pulls in.
  This includes the browser build that the pinned browser-driving library downloads, because that
  pin fixes the browser. **The owner is the one who watches**, using the advisories GitHub publishes
  for the repository that holds tracker17. QC-40 keeps its current gate and gains a second one: every
  review at `development-design` checks the pins against the published advisories. A critical
  advisory more than 30 days old blocks that change until the pin is moved. **If no fixed version
  exists within the window**, the dependency is replaced or removed. Otherwise the owner records an
  accepted exception in an RN, dated, with the reason, and that exception is the only way to be past
  the window without being late. Why 30 days and not fewer: the dependencies run only to test, on
  the owner's machine (SDD § 4 RT-1, RT-4). The browser they drive opens only the tracker's loopback
  pages (QC-30, QC-35). Until publishing, the owner is the only person who installs them (PRD
  § Assumptions, "Until then the owner is the only reader"). **Publishing should make the owner
  reconsider the number**, because strangers would then install the pins. Shortening it at that
  point is a fresh authorization of QC-40. The other answer, "no window until publishing", stays
  open to the owner. Choosing it means the owner sets aside the dependency floor for tracker17, and
  QC-40 would say so in those words and name publishing as what ends it.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

None this run.
