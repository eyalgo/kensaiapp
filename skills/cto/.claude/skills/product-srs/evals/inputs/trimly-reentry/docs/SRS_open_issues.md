# SRS open issues — Trimly

> Companion to `SRS.md`. The CTO authored the SRS non-interactively; this file holds
> what it could not settle from the inputs (the PRD and any context/constraints).
> **Answer inline** — fill each **Answer** / **Confirm or override** slot — then re-run
> `product-srs`. It folds your answers into the SRS and drops the resolved items. When
> nothing is left open, `product-srs` **deletes this file**: no file = the SRS is done.

---

## 1. Open issues — technical questions with no answer yet

### 1.1 Link lifetime — do links ever expire?
- **Why it matters:** DR-1 (Link) and the redirect guarantee (FR-4) depend on it. The PRD contradicts
  itself: F5 says a link "never expires", but §5 says inactive links (no clicks for 12 months) "are
  automatically purged". Only one can hold, and which one is a product-intent call.
- **Answer:** Links never expire (F5 is the intent — a printed link must resolve forever). Drop the
  12-month auto-purge of inactive links entirely; the only retention rule that remains is the 30-day
  raw-IP window (NFR-4). Treat the §5 auto-purge line as a PRD error to correct.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

### 2.1 Redirect latency target
- **Drafted into the SRS:** NFR-1 — p95 redirect latency < 100 ms at the edge, under launch-scale load.
- **Rationale:** the PRD (G4) asks only that redirects "feel instant" with no number; 100 ms p95 is a
  defensible "instant" bar for an edge redirect, but it is an owner-taste UX promise, not a derived fact.
- **Confirm or override:** confirm.

### 2.2 Availability target
- **Drafted into the SRS:** NFR-2 — 99.9% monthly availability of the redirect path.
- **Rationale:** the PRD (G4) asks only that the service be "dependable" with no number; 99.9% is a common
  bar, but the target drives real infra cost and is the owner's call.
- **Confirm or override:** override: 99.5% monthly is enough for launch — don't over-commit the infra
  spend on a v1.
