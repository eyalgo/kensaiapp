# Architecture open issues — sealbox

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

---

## 1. Open issues — questions with no answer yet

### 1.1 What has to be visible from outside when sealbox fails?

- **Lands in:** `nfdr.md` § 7
- **Why it matters:** The SRS states no observability requirement at all — § 4 carries performance,
  security and scalability and nothing else. There is no upstream fact to trace an entry to, and a
  floor invented here would be a product-shaping call made in the most downstream document. Meanwhile
  the operator runs sealbox on their own host with nobody from us on it, so whatever is not visible
  from outside is not visible to anyone.
- **Answer:** Every send, signature, render failure and erasure writes one structured JSON line to
  **stderr** carrying the envelope id, the event name and the outcome — the operator's own log
  collector takes it from there. A render failure additionally fails the request with a non-2xx and
  is counted, so an operator can see a rate rather than a single line. Nothing goes anywhere off the
  box. And yes — raise the gap against the SRS too; § 4.5 is where this should have been stated.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 The default retention term the reference deployment ships

- **Lands in:** `nfdr.md` QC-9
- **Drafted into the records:** 7 years, as the shipped default for the reference deployment, with the
  term itself configurable per DR-2.
- **Rationale:** DR-2 fixes no default and the SRS cycle-1 trail asks the constraint set to propose
  one. Seven years is the longest common professional-records term, so it fails safe on the retention
  side.
- **If overridden:** QC-9's figure moves and the layer-5 retention test's fixture moves with it.
  Nothing else in either record depends on the number.
- **Confirm or override:** override: **3 years**. Seven fails safe for records and fails badly for
  privacy — we hold client documents we were asked to erase. Three years matches our own engagement
  term, and a firm that needs longer changes the setting.

### 2.2 NFDR § 6 (Availability & reliability) declared not applicable

- **Lands in:** `nfdr.md` § 6
- **Reason it does not apply:** The customer deploys and operates sealbox on their own host and the
  vendor commits no uptime target (SRS § 7 C-2). The SDD fixes no runtime topology beyond the single
  process (RN-3), and the FDR puts clustering and failover out of scope (OOS-2). There is no service
  we operate, so there is no availability obligation for a change to break.
- **Confirm or override:** confirm. We do not run it, so we do not promise it.
