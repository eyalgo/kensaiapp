# Crossing rules open issues — Stonebridge

> Companion to `system/standards/crossing_rules.md`. The Crossing Keeper wrote those rules without
> stopping to interview you; this file holds the calls it made and wants your sign-off on, each with the
> reason behind it, plus the few things it genuinely could not settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `crossing-rules`. It folds your answers into the rules and drops the resolved items. When
> nothing is left open it **deletes this file**: no file = the rules are settled.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses to
> remove a file with uncommitted edits in it — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Crossing Keeper folds them in, it first copies this
> file whole to `system/standards/crossing_rules_trail/` — so what you decided, and why, stays readable
> and citable for good.

---

## 1. Open issues

### 1.1 The 4.2 m headroom in § 2 names no datum, so the limit is not a limit
- **Why it matters:** § 2 bars any vessel over 4.2 m air draught from the centre span, and the whole
  enforcement ladder in § 4 counts from that number. The same vessel passes or fails depending on
  whether the 4.2 m is read from chart datum or from the water surface at high water — and the survey
  records an observed range of 1.8 m on this reach (`river_survey.md` § 4), which is wider than the
  margin most of the traffic here is working to.
- **What was searched:** `river_survey.md` § 3, which states the 4.2 m and the date it was measured but
  names no datum; § 4, which gives the range without tying the headroom to it; and the crossing's own
  § 2 and § 4, which cite the figure and add nothing.
- **Whose it is:** the datum belongs to the survey. `river_survey.md` is where every measured figure on
  this reach is fixed, and these rules only cite them — stating a datum here would put half of that
  measurement in a second place, and a resurvey would move one copy and not the other. The survey is
  settled and has no open-issues file beside it.
- **Answer:** <the owner fills this in>

## 2. Choices to confirm

### 2.1 A vessel under tow is bound by the towing vessel's transit call, not its own
- **Written into the rules:** § 3's calling duty falls on the powered vessel, and § 1 brings an
  unpowered vessel under tow inside the rules without giving it a separate call.
- **Grounds:** the two logged near-misses at the span both involved a tow whose barge called
  independently and arrived on a different minute from the tug. One call from the powered vessel keeps
  the keeper's log single-valued, which is what § 4's enforcement reads against.
- **If overridden:** § 3 gains a second call for the towed vessel, and § 4's rolling count has to say
  which of the two calls a recorded transit attaches to.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">
