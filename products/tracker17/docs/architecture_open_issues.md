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

### 3.1 QC-40's first-review check of the dependency graph could not read the graph
- **Raised by:** PM — 2026-10-29
- **Which record:** `nfdr.md` QC-40
- **Tracked by:** `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`
- **What it blocks:** QC-40's *verified by* (`nfdr.md:386-390`) says "The first review after
  `uv.lock` is on `main` also checks that the repository's dependency graph lists the packages
  `uv.lock` fixes; where it lists none, the package feed is down". That first review has happened,
  and its check could not be made. It recorded that `gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependency-graph/sbom`
  returned `Not Found (HTTP 404)`, exit 1, which says neither that the graph lists the packages nor
  that it lists none. An OSV query on the 16 registry versions `uv.lock` fixes found no advisory
  (2026-10-29), which is not the GitHub feed QC-40 names. So whether the owner's Dependabot feed for
  `uv.lock` is live is unknown, and QC-40 names no fallback for a review that cannot read the graph.
- **Where it shows:** QC-40's *verified by*, the first-review moment; no row in § 10, as QC-40 is a
  review gate (`nfdr.md:689`).
- **If a document has to be written:** none — QC-40 says how the moment is met when the graph cannot
  be read, with which access, and whether it stays owed until then.
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.
