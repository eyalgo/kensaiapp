# Flow Findings — development-specs  (audited 2026-09-08)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[blocking · change-local · coverage]** The spec builds the cancellation that a standing deferral
  waits on, and neither takes the deferred work nor fences it out. Where: `change_spec.md §Rules`
  against `src/ferrule/billing/refunds.py:3` at the change's base, which read: "The booking-fee refund
  is not built here — it is deferred to the change unit that builds cancellation." This change is that
  unit. Building the operation a deferral waits on settles the deferral one way or the other; this spec
  does neither, so FR-5's refund has no owner. Direction: take FR-5 into this change, or fence it out
  and name what carries it.
