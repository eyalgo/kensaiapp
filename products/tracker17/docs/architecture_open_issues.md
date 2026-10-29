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

> **No producing run wrote this file.** It was opened by hand on 2026-10-29, in the owner's session,
> to carry § 3.1 down from SDD version 15. `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 SDD § 4 RT-4 moved the test suite to uv, and ADR-0002 and the NFDR still read `venv`
- **Raised by:** Product (the owner) — 2026-10-29
- **Which record:** `adr/0002-standard-library-only-no-web-framework.md` § Decision, and `nfdr.md`
  § 10 *Verification map*, RN-13 and QC-40
- **Tracked by:** none — the owner's top-down call; no seed watches it
- **What it blocks:** nothing is blocked. The records say the test dependencies go into a virtual
  environment made with Python's `venv`, while the SDD they follow now says uv makes it.
- **Where it shows:** SDD version 15 § 4 RT-4 says the lock file is `uv.lock`, setup is
  `uv sync --locked`, and every suite command runs through `uv run` (`docs/SDD.md:L299-L313`), and
  its RN-63 lists what downstream now reads thinner (`docs/SDD.md:L2842-L2862`). ADR-0002 says the
  test dependencies are "installed into a virtual environment made with Python's `venv`" and records
  that they "go into a `venv`" (`docs/adr/0002-standard-library-only-no-web-framework.md:L20-L27`).
  The NFDR types every row's command "inside the virtual environment of SDD § 4 RT-4"
  (`docs/nfdr.md:L597`), says in RN-13 that "RT-4's `venv` was forced by the owner's machine, not
  chosen" (`docs/nfdr.md:L769`), and rests QC-40's package feed on the lock file being "in a format
  GitHub's dependency graph reads" (`docs/nfdr.md:L365`), which RN-63 found GitHub's page does not
  list for `uv.lock`.
- **If a document has to be written:** a new ADR superseding ADR-0002's environment sentence, and
  `nfdr.md` itself, both by `product-architecture`.
- **Answer:** Yes — the records follow RT-4 to uv. The owner, 2026-10-29: "can we switch to uv
  instead of python?", then "yes" to carrying it top-down through the definition chain. How QC-40's
  feed holds for `uv.lock` is the Principal Architect's to re-derive.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
