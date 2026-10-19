# Ledger standard open issues — Ledgerworks

**Round:** 2
**State:** awaiting-owner

> Companion to `LEDGER.md`, and the baton for the round-based ledger loop (the Auditor writes → the
> Registrar reviews → you answer → the Auditor writes again → … until this file is gone). The two lines
> above track the loop: **Round** counts the write/review passes; **State** says whose move it is —
> `awaiting-review` (the Auditor finished a write pass; the Registrar reviews next) or `awaiting-owner`
> (the Registrar finished a review; you answer the open items below).
>
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — then the round continues.
> This file is **transient**: it exists only while something is unresolved. The Auditor write pass
> **never deletes it**; the Registrar review pass deletes it once nothing is left open and the standard
> is ratified. **No file = the ledger standard is ratified.**

---

## 1. Open issues

### 1.1 How long after a period closes may a correcting entry still be posted against it?
- **Why it matters:** § 2 permits a correcting entry against any posted entry; § 3 forbids posting into
  a closed period. The two collide the day after a close, and § 3 is written as though they do not.
- **Answer:** <the owner fills this in>

## 2. Choices to confirm

### 2.1 The Registrar's signature closes the period, not the reconciliation
- **Drafted into the standard:** § 3 — "A period closes when every account reconciles and the Registrar
  signs the close."
- **Rationale:** reconciliation is a state the books reach on their own and can leave again when a late
  movement lands; a signature is an act with a time on it. Keying the close to the act gives § 4's
  retention term a date it can count from.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">
