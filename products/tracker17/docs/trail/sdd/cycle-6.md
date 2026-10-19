# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

> **No producing run wrote this file.** The PM opened it on 2026-10-12, in a route review, to carry
> item § 5.1. `product-sdd` has no record of writing it. It exists because § 3's `application` row
> says every action saves, and an edit that changes nothing now saves nothing.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

None.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 § 3's `application` row says every action saves; an edit that changes no field saves nothing
- **Raised by:** PM — 2026-10-12
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** nothing is blocked. The row states as unconditional a sequence the product no
  longer follows for every action, so a reader checking `application/` against it finds a breach that
  is the intended behaviour.
- **Where it shows:** `SDD.md:L201` (§ 3, `application` row) — "Each action is one call: it applies a
  `domain` rule to the current state, saves the new state, and only then makes it current." In the
  product, `application/tracker.py:L105-L114` (`Tracker.edit_task`) saves and publishes only when the
  `domain` outcome reports a changed field: "one that reports none saves and publishes nothing". The change asked: qualify the save-then-publish sequence as applying to an action whose
  `domain` outcome reports a change, and say that an action reporting none returns the current state
  without saving or publishing. The decision is `domain`'s, so `application` still owns no rule.
  The same sentence is in NFDR QC-21 and ADR-0001, raised on `architecture_open_issues.md` § 3.1.
- **If a document has to be written:** none. `SDD.md` changes through `product-sdd`.
- **Answer:** Confirm the change as asked, with two additions. **§ 3 `application` row.** Each action
  is one call: it applies a `domain` rule to the current state; where the rule's outcome reports a
  change, it saves the new state and only then makes it current; where the outcome reports none, it
  returns the current state, saves nothing, and the current state stays as it was. Which outcomes
  report none is `domain`'s, decided per action and read off the outcome, so the row's *Must not own*
  stands as written: `application` decides nothing. Today the edit is the one action that reports.
  `application/tracker.py:L105-L114` saves on `outcome.changed` and on nothing else;
  `domain/tasks.py`, `edit_task`, returns the state as it came with `changed=False` when no submitted
  field differs from what the page showed; `tests/integration/test_task_tracker.py`,
  `test_tracker_unchanged_edit_never_saves`, finds no save and the state untouched. **Addition one,
  the bound.** The report is `domain`'s comparison of the value submitted with the value the page
  showed (§ 4 RT-7), never of the new state with the current one. A field changed to the value
  another tab already saved therefore reports a change and saves a state equal to the current one,
  one whole write under § 4 SD-3 with nothing lost, and `application` compares nothing, which is what
  keeps a comparison rule out of it. **Addition two, what does not move.** § 4 SD-2 and SRS FR-9 bind
  the done report to the disk, and an action reporting no change reports nothing done:
  `web/routes.py:L438` opens the task's page with no completion line, which is FDR R-116 and UXD
  UX-I4's "a result is shown only once it is saved". § 9 TO-3 already says "on every change". SRS
  NFR-3's stale edit replaces "for that field", and an unchanged field is not written. A move to the
  status a task already has is a refusal (SRS FR-18), not a no-change outcome; adding a label the
  task already carries (FDR R-65) will be the second action to report none, and the row as qualified
  covers it without naming it. The NFDR and ADR-0001 copies are already
  `products/tracker17/docs/architecture_open_issues.md` § 3.1, and this answer adds nothing there.
  Reasoning: `products/tracker17/docs/trail/sdd/self_answer-8.md` § 5.1.
