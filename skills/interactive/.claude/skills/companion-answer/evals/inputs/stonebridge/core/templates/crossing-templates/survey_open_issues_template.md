---
version: "1.0.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# River survey open issues — <reach>

> Companion to `system/standards/river_survey.md`. The Surveyor wrote that survey without stopping to
> interview you; this file holds the calls it made and wants your sign-off on, each with the reason
> behind it, plus the few things it genuinely could not settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `river-survey`. It folds your answers into the survey and drops the resolved items. When
> nothing is left open it **deletes this file**: no file = the survey is settled.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses to
> remove a file with uncommitted edits in it — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Surveyor folds them in, it first copies this file
> whole to `system/standards/river_survey_trail/` — so what you decided, and why, stays readable and
> citable for good.

---

## 1. Open issues

### 1.1 <the question, in one line>
- **Why it matters:** <what in the survey depends on this>
- **What was searched:** <where the answer was looked for, and what each source gave>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm

### 2.1 <the decision, in one line>
- **Written into the survey:** <the choice made, and where it was written>
- **Grounds:** <why this was the best-effort call, and what it derives from>
- **If overridden:** <what moves, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">
