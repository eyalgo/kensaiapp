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
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix.

> **No producing run wrote this file.** The PM opened it on 2026-10-11, in a route review, to carry
> item § 5.1. `product-sdd` has no record of writing it. It exists because a focus test on an element
> that is not a control now passes in Chromium, and § 11 R-2 and § Open Questions still call that case
> wholly unverified.

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

### 5.1 § 11 R-2 and § Open Questions still call the not-a-control focus case unverified; one form of it is now checked
- **Raised by:** PM — 2026-10-11
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** nothing is blocked. The SDD reads as if no focus test on an element that is not
  a control has passed, so a reader of § 11 R-2 cannot tell which of its three tests is still owed,
  and § Open Questions keeps open a case a passing test now answers in part.
- **Where it shows:** `SDD.md:L1154-L1164` (§ 11 R-2) — whether Chromium applies `autofocus` to an
  element that is not a form control, "brings that element into view, and reads its description is
  not verified here". `SDD.md:L1769-L1774` (§ Open Questions) — the same question, open except for
  the form-control case. In the product, `tests/e2e/test_people.py:L58-L78` asserts, in Chromium, that
  after an add on People the added name (a `span`, not a control) holds keyboard focus, is in the
  viewport, and has the completion line as its computed accessible description, with no script on
  the page. Measured on `main` at `641bb58b5`: `pytest products/tracker17/tests/e2e/` → `18 passed`.
  What stays unchecked: the confirmation's focus test (`status-moves` in § 11 R-2's response), and
  assistive-technology speech, which a computed accessible description does not prove. The change
  asked: narrow § 11 R-2 and the Open Question to what is still unverified, keeping R-2's experience
  conditions, its fallback and the untested cases as they stand. The no-script decision is not in
  question.
- **If a document has to be written:** none. `SDD.md` changes through `product-sdd`.
- **Answer:** Narrow both to what is still unverified, as the item asks, and keep R-2's experience
  conditions, its fallback and its three tests as triggers. **§ 11 R-2.** Chromium focusing an element
  that is not a form control, made focusable with `tabindex="-1"` and carrying `autofocus` on a page
  whose address has no fragment, and bringing it into view, is verified: `tests/e2e/test_people.py`,
  `test_added_markup_name_has_browser_focus_and_accessible_description`, finds the added name (a
  `span`, `web/pages.py:316`) holding keyboard focus, in the viewport, with the completion line as its
  computed accessible description and no `script` element on the page; the same file's
  `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action` finds the People heading focused
  after a removal, a second element that is not a control. Both passed at `main` `641bb58b5` (the PM's
  run, 18 passed) and again in this run, in a disposable copy of `main` at `7653f25c8` with the
  pinned library (playwright 1.63.0, Chromium 153.0.8010.12): `pytest tests/e2e/` → 18 passed.
  `git diff --stat 641bb58b5 7653f25c8 -- products/tracker17 ':!products/tracker17/docs'` lists only
  `README.md`, two sentences of its Status section, which no end-to-end test reads. What R-2 still
  calls unverified: the confirmation case — focus on the confirmation's sentence, the double press that
  never confirms, and back-out returning focus to the restored button (§ 4 EX-6), which `status-moves`
  tests; and whether assistive technology reads the description when the page opens (§ 4 EX-14), which
  a computed accessible description puts in the accessibility tree and does not prove is spoken. No
  test drives a screen reader and no slice requires one; one pass with VoiceOver on the owner's macOS
  machine would settle it, and no slice requires that run (the form R-8 and R-9 use). R-2's *shows up
  as* keeps all three tests, the two that pass as the regression signal, because a Chromium release
  could change the behaviour and both suites run on every slice (RN-36's reasoning for
  `first-project`'s test). One bound to name: the suite drives the Chromium build the pinned library
  installs, and the operator's browser is current stable Chrome (SRS NFR-13), so a divergence between
  the two shows only in the owner's run-through. **§ Open Questions.** The not-a-control case is
  settled for focus and in-view, and a Review Note records where, as RN-36 does for the form-control
  case; what stays open is the confirmation case, which `status-moves` settles, and
  assistive-technology speech, for which R-2 names the run. **One sentence follows R-2:** § 6 S-2's
  *Why here in the order* calls its focus test "the case § 11 R-2 leaves unverified", which is now the
  case R-2 left unverified until this slice's People half ran; § 7's `validates` row stands as
  written. The no-script decision (§ 4 EX-2, ADR-0003) does not move. ADR-0003's Dependence is already
  raised on `products/tracker17/docs/architecture_open_issues.md` § 3.1, and this answer adds nothing
  there. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-7.md` § 5.1.
