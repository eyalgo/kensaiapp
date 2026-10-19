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
> says every action's report compares the submitted value with the value the page showed, and the
> operator name's report compares with the name saved when the action runs.

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

### 5.1 § 3's `application` row says every action's report compares with the value the page showed; setting the operator name compares with the saved name
- **Raised by:** PM — 2026-10-12
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`
- **What it blocks:** nothing is blocked. The row states as true of every action a comparison that
  one action does not make, so a reader checking the operator name against it finds a breach that is
  the intended behaviour, and could "fix" it by adding a shown-name value to the People form.
- **Where it shows:** `SDD.md:L202` (§ 3, `application` row) — "The report is `domain`'s comparison
  of the value submitted with the value the page showed (§ 4 RT-7), never of the new state with the
  current one". In the product, `domain/operator_name.py:L59-L62` (`set_operator_name`) compares the
  submitted name with `state.operator_name`, the name saved when the action runs, and the People form
  carries no shown-name value: `tests/integration/test_people_routes.py:L520-L533`
  (`test_stale_people_name_submission_compares_with_current_name`) asserts the form's only input is
  `name` and that a submission equal to the current name saves nothing. The change asked: qualify the
  comparison sentence as the task edit's rule (§ 4 RT-7), and say that setting the one operator name
  reports no change when the submitted name equals the saved name at the moment of the action; the
  comparison stays `domain`'s, and `application` still compares nothing. The same sentence is in NFDR
  QC-21, raised on `architecture_open_issues.md` § 3.1.
- **If a document has to be written:** none. `SDD.md` changes through `product-sdd`.
- **Answer:** Confirm the change as asked, with two additions. **§ 3 `application` row**, replacing the sentence that begins "The report is `domain`'s comparison": What the report compares is `domain`'s, decided per action. The task edit compares each value submitted with the value the page showed (§ 4 RT-7), because its form is the one that carries those values, so a field changed to the value another tab already saved reports a change and saves a state equal to the current one. Setting the operator name, and adding a label, compare the value submitted with what the state holds at the moment of the action, the saved name and the labels the task carries, which is SRS NFR-3's own rule for every action the task edit excepts, so a name or a label submitted equal to what another tab already saved reports no change and saves nothing. `application` compares nothing in either case. `domain/operator_name.py:L60-L62` (`set_operator_name`) returns the state as it came with `changed=False` when the checked name equals `state.operator_name`; `application/tracker.py:L74-L76` saves on `outcome.changed` and on nothing else; `tests/integration/test_people_routes.py:L520-L533` asserts the People form's only input is `name` and that a stale page's submission compares with the name saved at the moment of the action. **Addition one, the label is the same shape.** `domain/tasks.py:L253-L258` (`add_task_label`) checks the label "against the labels it carries now" and returns `changed=False` for one already carried; `tests/unit/test_tasks.py:L727-L735` asserts it. Labels landed at `25fff47d2` and the name at `cb48338e3`, both after version 9 (`33ad1a2a7`), so RN-45's "the edit is the one action that reports" and "FDR R-65's label already carried will be the second" are dated and stay as the record of that round; the row now describes three reporting actions and names the comparison per action rather than enumerating them. **Addition two, what does not move.** § 4 RT-7 already gives the shown-value form to the task edit alone ("The task's edit form is that form") and is not changed. § 4 SD-2 and SRS FR-9 stand: an action reporting no change reports nothing done, and `web/routes.py:L605-L606` opens plain People with no completion line when `outcome.changed` is false, which `tests/integration/test_people_routes.py:L502-L518` asserts and UXD UX-I4 requires. FDR R-62 and R-65, SRS NFR-3 and DR-5, UXD UX-F8 and § 6 S-3's "sets or changes the name" stand as written. A blank or too-long name is a refusal raised before any outcome (`domain/operator_name.py:L47-L49`; SRS FR-27, FR-40), never a no-change outcome, and a name never reaching the saver cannot meet SD-2's failure branch. The row's *Must not own* stands: which value is compared with is `domain`'s, so a reader does not add a shown-name value to the People form and does not give `application` a comparison. The NFDR copy in QC-21 is already `products/tracker17/docs/architecture_open_issues.md` § 3.1, whose ask, "qualify other actions by their own `domain` comparison", covers the label too, and this answer adds nothing there. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-9.md` § 5.1.
