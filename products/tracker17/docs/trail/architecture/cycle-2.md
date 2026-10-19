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

`SRS`, `SDD` and `FDR` are `products/tracker17/docs/SRS.md`, `SDD.md` and `fdr.md`. `QC-n` and `RN-n`
are entries of `products/tracker17/docs/nfdr.md`. None of the nine records in `adr/` waits on an item
here; the one item lands in `nfdr.md`. The first answered round is kept at
`products/tracker17/docs/trail/architecture/cycle-1.md`.

---

## 1. Open issues — questions with no answer yet

### 1.1 How long may a known critical vulnerability in a test dependency stay unfixed?
- **Lands in:** `nfdr.md` QC-40
- **Why it matters:** the quality floor for dependencies asks for a stated remediation window that
  starts when the advisory is published: "A product that names no window has an obligation nobody is
  late against" (`<CORE>/doctrine/engineering/quality_defaults.md` § Dependencies). tracker17 runs on
  no third-party package, but its test suite installs pinned packages and a browser (SDD § 4 RT-4).
  No upstream document states a window, and the number commits the owner's own time: someone has to
  watch the advisory feed, and in this product that can only be the owner. The window is the floor's
  measure for this product, so the answer lands in QC-40 itself, with no SRS round first (`nfdr.md`
  RN-10). "No window while tracker17 is unpublished, because until then only the owner installs the
  test dependencies, and they run only to test" is also an answer: QC-40 would then say so, and name
  publishing as what ends it. That answer is drafted, with what it leaves uncovered, at
  `products/tracker17/docs/trail/architecture/self_answer-1.md` § *Left for the owner*.
- **Answer:** confirm the recommendation in
  `products/tracker17/docs/trail/architecture/self_answer-3.md` § *Left for the owner*, "The answer I
  would have given". A window of 30 days from the day the advisory is published, for a critical
  advisory against a test dependency the lock file fixes or against the browser build the pinned
  browser-driving library installs. The owner watches the feed: Dependabot alerts for the packages,
  and for the browser a check at each `development-design` review against the browser vendor's
  security releases. No fix within the window means the dependency is replaced or removed, or the
  owner records a dated exception in an RN.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

None.
