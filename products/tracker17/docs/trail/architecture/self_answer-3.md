# Self-answer report — `adr/` and `nfdr.md` (tracker17)

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md` (the one open item lands in `nfdr.md` QC-40)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:**
  - https://docs.github.com/en/code-security/dependabot/dependabot-alerts/configuring-dependabot-alerts — "You can manage Dependabot alerts for your public, private or internal repository." This settles what `self_answer-2.md` could not: the repository holding tracker17 is private (PRD § Assumptions), and it can have alerts.
  - https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/dependency-graph-supported-package-ecosystems — for pip, the dependency graph reads `requirements.txt` and `pipfile.lock` (also `pipfile` and `setup.py`); for Poetry it reads `poetry.lock` (also `pyproject.toml`). The page says the graph prefers lock files. It does not say outright that alerts depend on the graph.

Only one item was open, so there was nothing to put in order. Nothing has changed since `self_answer-2.md`. HEAD was `67e3fe90d`, the commit that filed that report. No owner ruling on the window was found: a search for `remediation window`, `advisory feed` and `QC-40` under `system/projects/*/journey` and `system/projects/tracker17` returned nothing.

## Items worked

None this run.

## Left for the owner

### 1.1 — How long may a known critical vulnerability in a test dependency stay unfixed?

- **Bucket:** 1. Open issues — questions with no answer yet
- **Verdict:** left for the owner
- **Why:** All four checks were run. The item stays with the owner for the same two named grounds as
  last round, and nothing on disk has moved either one. **First, the window commits the owner's time.**
  The floor's gate has to name "who watches the advisory feed"
  (`<CORE>/doctrine/engineering/quality_defaults.md:59-62`). With one operator (SRS NFR-7), that can
  only be the owner, and so the answer sets the date by which the owner is late. **Second, the
  other answer waives a floor.** "No window while unpublished" is not a value inside QC-40. It sets
  aside a floor that "holds for every product this system builds"
  (`quality_defaults.md` § What is not a floor), and doctrine is the owner's
  (`<CORE>/roles/CROSS_ROLE.md` § 3). What would tip this item to *answered*: the owner stating,
  somewhere a run can read, how much time they will give to watching advisories.
  **What changed this round is the feed, not the call.** Check 3 re-read the GitHub pages that
  `self_answer-2.md` left half-read (see *Sources re-read*). Dependabot alerts work on a private
  repository, so the feed exists for tracker17 today. The dependency graph reads `requirements.txt`
  and `poetry.lock`, so it will see the pinned packages if the one lock file QC-39 requires is in a
  format it reads. That format is not chosen yet (SDD § 4 RT-4, "one committed file").
  **Check 4 found a hole in last round's answer.** That answer put "the browser build that the pinned
  browser-driving library downloads" inside the window, and named GitHub's advisories as the feed. But
  the browser is fetched by the library at setup and is written in no manifest or lock file the graph
  reads (SDD § 4 RT-4; NFDR B-4 lists it separately from the test dependencies). So GitHub's alerts
  are blind to it. The answer below gives the browser its own feed, rather than leaving a component
  inside a window that nobody watches.
  *Other failure paths:* **Empty:** nothing is pinned yet (`ls products/tracker17` lists only
  `docs`), so the window is idle until the first pin. **Stale:** QC-40's gate runs only when a change
  touches a dependency, so an advisory against an untouched pin reaches nobody through it. The
  watcher and the window cover that case. **Refused:** an advisory with no fixed version gets its own
  way out below. **Concurrent:** each advisory runs its own window. **Absent:** if the feed cannot be
  reached, the watcher checks by hand at each design review.
  *Supporting text, reported, not corrected:* the item still points at `self_answer-1.md` for the
  "no window" draft. That is still where the draft is, but `self_answer-2.md` has replaced the
  recommendation with the 30-day answer below. If the fold rewrites the item, it should point to the
  newest report.
- **The answer I would have given:** A stated window of **30 days from the day the advisory is
  published**, for a critical advisory against any test dependency the lock file fixes, or against
  the browser build that the pinned browser-driving library installs. **The owner watches.**
  - **Feed for the packages:** Dependabot alerts on the repository that holds tracker17. They work
    on a private repository. This needs the QC-39 lock file to be a format GitHub's dependency graph
    reads, such as `requirements.txt` or `poetry.lock`. Choosing that format is the toolchain decision
    `nfdr.md` RN-10 leaves open, and this answer only states the condition.
  - **Feed for the browser:** no feed above covers it. At each `development-design` review, the owner
    compares the browser version the pinned library installs with the browser vendor's security
    releases.
  - **Gates:** QC-40 keeps its current gate and gains a second one. Every `development-design` review
    checks the pins, and the browser build, against published advisories. A critical advisory more
    than 30 days old blocks the change until the pin moves.
  - **No fix within the window:** the dependency is replaced or removed. If it is not, the owner
    records a dated exception with its reason in an RN. That exception is the only way to be past the
    window without being late. It is the likely path for the browser, which opens only the tracker's
    own loopback pages (QC-30, QC-35).
  - **Why 30 days:** the dependencies run only to test, on the owner's machine (SDD § 4 RT-1, RT-4).
    Until publishing, the owner is the only person who installs them (PRD § Assumptions). Publishing
    should make the owner look at the number again.
  - **The alternative:** "no window until publishing" stays open to the owner as a waiver of the
    floor. QC-40 would then say so in those words and name publishing as what ends it.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

None this run.
