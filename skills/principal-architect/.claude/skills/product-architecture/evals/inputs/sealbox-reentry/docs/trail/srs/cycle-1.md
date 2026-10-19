# SRS open issues — sealbox

> Companion to `SRS.md`. The CTO authored the SRS non-interactively; this file held what that run
> could not settle. Retired whole to the trail when the answers were folded in.

---

## 1. Open issues — questions with no answer yet

### 1.1 How long is a signed envelope kept?

- **Why it matters:** DR-2 and the erasure path both need it, and a number here would bind every
  deployment.
- **Answer:** Don't pick one. Firms have different contractual terms and their compliance people will
  not accept ours. Make it a setting, say so in the SRS, and let whoever writes the constraint set
  propose a default for the reference deployment.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

### 2.1 The render budget for a signed PDF

- **Drafted into the SRS:** NFR-1 at under 2 s at p95 for a 20-page document on the reference host.
- **Rationale:** It is the wait a signer sits through after the last click, and the reference host is
  the smallest box a buying firm has offered to run.
- **Confirm or override:** confirm. 2 s is the right side of "did that work?".

### 2.2 Concurrent signer sessions on one host

- **Drafted into the SRS:** NFR-6 at 50 concurrent sessions.
- **Rationale:** carried from the PRD's launch-scale estimate; nothing has been measured.
- **Confirm or override:** confirm, but write in the review notes that it is an estimate. I don't want
  someone treating it as a measurement later.
