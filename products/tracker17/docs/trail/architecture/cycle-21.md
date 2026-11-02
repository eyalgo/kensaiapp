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

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 3.1.
> `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-40 names an SBOM export that answers 404, and says nothing about what that answer means
- **Raised by:** PM — 2026-10-30
- **Which record:** `nfdr.md` § 2 QC-40
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** QC-40's graph reading stays owed at every review. The review cannot end the moment through the export, and the entry names no other reading a review without a browser can make.
- **Where it shows:** QC-40 has a review check the graph "through the repository's dependency-graph page or GitHub's asynchronous SBOM export" and treats a call that answers neither way "for want of access or a network" as no reading (`docs/nfdr.md:L393-L397`). Run on 2026-10-30, `gh api repos/<owner>/<repository>/dependency-graph/sbom/generate-report` printed `{"message":"Not Found",…,"status":"404"}`, and the alerts endpoint printed `Dependabot alerts are disabled for this repository.` A 404 from the account the entry requires is neither want of access nor want of a network, so the entry does not say how to read it: the graph off, the export's address wrong, or something else. Whether the graph needs switching on is a repository setting no change is authorized to make.
- **If a document has to be written:** none — `nfdr.md` itself, by `product-architecture`.
- **Answer:** QC-40 should say that a 404 from the export, while the alerts endpoint refuses as disabled, is the expected answer of a feed that is down. It should not name a cause for the 404, because no cause changes what the review does. Add one sentence to the tail, after "is not a reading, and the moment is not met": "An export that answers 404 to that account, while the alerts endpoint refuses as disabled, is what a feed that is down looks like: the review records the feed as down and the moment as still owed, and raises no discrepancy." Measured 2026-10-30 from an account with admin on the repository, whose token carries `repo`: the alerts endpoint refused as disabled, `generate-report` answered 404 "Not Found", and the same call answered 201 with an `sbom_url` on a public repository, so the address is right. No further reading without a browser is owed, because the alerts refusal has already settled the feed's state, and the moment can only end after the owner turns the graph on. The obligation, the window, the "want of access or a network" clause and the rule that the moment stays owed do not move. A 404 while the alerts endpoint answers a list has not occurred: not until it occurs, and the entry's existing "stays owed" already holds it. Reasoning: `docs/trail/architecture/self_answer-25.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
