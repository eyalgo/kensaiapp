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

> **No producing run wrote this file.** The PM opened it on 2026-10-27, after reading the product's
> filter form against § 4 RT-8, to carry § 5.1. `product-sdd` has no record of writing it.

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

### 5.1 RT-8 says every submission is answered by a redirect; the filter form is answered with a page
- **Raised by:** PM — 2026-10-27
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`
- **What it blocks:** nothing is blocked. RT-8 reads "Every submission is answered by sending the
  browser to a page address" (`SDD.md:L330-L332`). The project page now carries a filter form sent
  with `method="get"` (`web/pages.py:L1189`), and Apply, its reload and Clear are answered with the
  project page itself, 200, saving nothing (`tests/integration/test_routes.py:L1090-L1093`, "Apply,
  its reload and Clear are the one project GET route"). The product reads a GET form as a read, not a
  submission; RT-8 never says so, so a reader holding RT-8 to its words finds a form it does not
  cover. The sort controls and the All tasks list (FR-36, UX-S7) add more forms of the same kind.
- **Where it shows:** § 4 RT-8, its second sentence. The record it owes: whether "submission" means
  a form that asks for a change (POST), so a GET form that only narrows or orders a list is answered
  with the page and stays outside the redirect rule — or the opposite, with the redirect a GET form is
  then owed.
- **If a document has to be written:** none; RT-8's wording only. ADR-0006 and NFDR QC-7 state the
  same sentence and are raised on their own companion.
- **Answer:** A submission, in RT-8 and wherever this document uses the word, is a form sent with
  `method="post"`: a request that asks the tracker for a change. A form sent with `method="get"` is
  a read, not a submission, and stays outside the redirect rule. **The sentence RT-8 gains, after
  "so reload, back and forward never repeat an action":** A form sent with `method="get"` is not a
  submission. The browser puts its values into a page address (§ 4 EX-3; UXD UX-I7) and the tracker
  answers that address with the page, 200, as it answers a link: it changes nothing, saves nothing,
  and is marked like any page request under SEC-2, so it opens from a bookmark. It takes no
  redirect, because the redirect exists so that an action is never repeated, and a read repeated is
  what UX-I7 asks for. A refusal of such a form — a range whose from-date is after its to-date (SRS
  FR-34), a name not on the list (FR-33), a value its control cannot hold — is answered with the page
  at the asked address, 200, with no list, the reason beside the control and focus on the first
  refused control (EX-4); the address already carries what was typed, so no address is built for
  it. RT-8's one function builds the redirects that `post` forms answer with; a `get` form's address
  is the browser's. **Why the word has to be defined:** the HTML standard's form submission
  algorithm covers a `get` form too — for `http` and `https` its GET column is "Mutate action URL":
  "Set parsed action's query component to query", then "Plan to navigate to parsed action"
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, re-read 2026-10-27) —
  and UXD UX-I6's "Enter submits the form the focus is in" uses the browser's verb for every form,
  Apply included. So read with the browser's word, RT-8 is false of the product, and read with
  this document's it is true; the sentence says which. **What stays as it is:** RT-8's first
  sentence, "Only a form submission changes the tracker state" — a `get` form never changes it,
  which RT-11 already leans on ("the GET schedules, saves and records nothing"). SEC-2 as written:
  a request from the address bar or a bookmark is marked `none`, "a page opens on it and a
  submission does not", and the opposite reading would have SEC-2 refuse the bookmarked narrowed
  list that UX-I7 and EX-3 require to open — the product keys the same-origin check on the route's
  kind, every `post` route a submission and every `get` route a page (`web/routes.py:L103-L119`,
  `L247`; `tests/integration/test_filter_routes.py:L159-L180` refuses a cross-site filter GET and
  needs no `same-origin` mark on Apply). **Which forms this reaches:** the filter form today
  (`web/pages.py:L1189`), and the sort controls and the All tasks list's controls when S-5 adds
  them, the same kind; the Summary's linked counts (UX-F6) are links and were never in question.
  **The address's size:** a `get` form's values travel in the address, so § 11 R-10's limit reaches
  them as it reaches a redirect; the filter's values are the ones its controls offer — a status, a
  priority, a name or a label bounded by RT-10's 200 characters, two dates, one flag — so seven keys
  stay under 6,000 of the 65,536 bytes the listener accepts, and an address hand-typed with a key
  repeated is a request the tracker's own pages did not send, the boundary RT-8 already draws for
  the over-long refusal. A move submitted from a narrowed list carries the list's choices in its
  form and its redirect lands on the narrowed address (`web/routes.py:L799-L805`,
  `_carried_filters`): the `post` takes the redirect and the `get` it lands on is a read, each half
  under its own sentence. **Downstream:** ADR-0006 § Decision and NFDR QC-7 carry the same word and
  are owed the same sentence on their own companion, `architecture_open_issues.md` § 3.1, the
  Principal Architect's; § 12 says § 4 wins where the two disagree and the entry is re-derived.
  QC-7's route test holds under this reading as it stands: each `get` route is a non-submission it
  sends and asserts unchanged state on, each `post` route a submission it asserts a redirect on.
  Nothing settled moves and no slice's *Reached when*, fence or place moves, so this is a
  correction to RT-8's words and not a re-cut under § 10. Reasoning, with the failure paths:
  `products/tracker17/docs/trail/sdd/self_answer-12.md` § 5.1.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
