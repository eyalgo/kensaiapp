# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

> **No producing run wrote this file.** The PM opened it on 2026-10-21, in a route review, to carry
> items § 3.1 and § 3.2: the refusal formula's fifth example still offers a reload, and RN-26 waits
> for an occurrence that the product now has, while citing one it no longer has.

---

## 1. Open issues

None.

## 2. Choices to confirm

### 2.1 RN-26 records an occurrence that is gone and says the reloaded case waits, and it doesn't

> **No `product-content` run wrote this item.** A `companion-self-answer` run raised it on 2026-10-21
> while answering item 3.2, which asked two things. This is the half that is `CONTENT.md`'s, the run
> answered it, and it is here so the next round confirms it. Item 3.2 is left asking only the other
> half: what the reloaded page's line should say instead, which changes UXD UX-F4 and is carried on
> `docs/UXD_open_issues.md` item 2.1. Reasoning: `products/tracker17/docs/trail/content/self_answer-12.md`.

- **To write into CONTENT.md:** Four changes to RN-26, and no change to the formula or the examples.
  (1) Drop the sentence "No occurrence is cited for it, so it waits until one occurs", because the
  case now occurs. (2) Replace the cited occurrence, the refusal at `web/pages.py:760` whose wording
  is "the move you pressed". It no longer exists: `grep -rn "the move you pressed" products/tracker17/web`
  prints nothing, and the refusal for the cancellation address is now `_ADDRESS_LINE`
  (`web/pages.py:L758-L761`), which meets the rule. The occurrence to cite is the overtaken-move
  line, which is worded at `web/pages.py:L751-L756` and shown from `move_refused`, a code the tracker
  reads on every load (`web/routes.py:L384-L396`). A reload, Back or a bookmark shows it again.
  (3) Record the finding: that line, reached with no press, doesn't meet the rule. "Has changed to" is
  a claim about the past, the tracker holds only the address, and an address typed for a task that was
  never moved shows the same line. The formula's reach ("by a reload, Back, or a saved or typed
  address") already includes that page, so the finding is that the product's line breaks the rule and
  not that the rule has a gap. (4) Replace the pointer to `docs/UXD_open_issues.md` item 2.1 as pending.
  That earlier item was folded into UXD version 8 (`docs/trail/uxd/cycle-5.md` § 2.1), and the file
  now holds a different item 2.1. RN-26 cites UX-I3 and that trail entry for the settled case, and
  `docs/UXD_open_issues.md` item 2.1 for the reloaded landing page.
- **Grounds:** `CONTENT.md` § Voice, "State only what the tracker established", which RN-26 already
  uses against "the move you pressed". The code reads: `web/routes.py:L353` returns the outcome
  without reading the task's status, and `web/pages.py:L764-L770` shows the line whenever the address
  names the task on the page. I read this in the code and did not run a request against it. The
  grep above ran on 2026-10-21.
- **What moves if you override:** RN-26 keeps citing a refusal the product no longer writes and says a
  case waits that already occurs, so the standard's record is wrong about the product. Nothing else in
  the document moves.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 The out-of-date refusal example still offers a reload that no refusal may offer
- **Raised by:** PM — 2026-10-21
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** nothing is blocked. A writer copying § Message patterns → Error → *A refusal*
  gets an example that contradicts the product and its two upstream documents.
- **Where it shows:** `docs/CONTENT.md:L219`, the fifth example: "The status of 'Set up CI' has
  changed since this page loaded. Reload the page to see it." UXD version 8 says no refusal offers a
  reload on a page built after it (UX-I3, UX-F4), and SDD version 11 § 6 `status-moves` says a move
  pressed after another tab moved the task "says the task's status has changed and names the moves
  the page now shows, or none for a final status, and offers no reload" (`docs/SDD.md:L882-L885`).
  The product's words now follow that: `web/pages.py:L752-L757` writes "The status of '{title}' has
  changed to {status}." then "A task in {status} can be moved to {0} or {1}." (or "can't be moved"
  for a final status). The example should show the no-reload form, naming the moves.
- **If a document has to be written:** `CONTENT.md` itself, by `product-content`.
- **Answer:** Confirmed with addition. Yes, the fifth example is out of date and is replaced. The settled UXD (version 8, UX-F4 and UX-I3) says an overtaken move says the status has changed, names the moves the page now shows or none for a final status, and offers no reload, because the page it lands on is built after the refusal. Replace example 5 with two examples, the forms the product's own tests pin (`web/pages.py:L751-L756`, `tests/integration/test_move_routes.py:L87-L99`): "The status of 'Set up CI' has changed to todo. A task in todo can be moved to in-progress or cancelled." and "The status of 'Set up CI' has changed to done. A task in done can't be moved." Three additions the item did not carry. (1) The formula says "then one action where one exists", and these examples name moves, not one action, so the formula gains a clause: for a move another change overtook, the second sentence names the moves the page now shows, or says there are none for a final status. Without it the examples contradict their own formula. (2) "Since this page loaded" is wrong for this refusal, because the page it lands on is built after the refusal. The banned-words row for "another tab" and RN-11 both give that phrase as the replacement, and both are revised to a form that doesn't date the page, such as "has changed to". (3) RN-24 says UX-I3 "still says" an out-of-date refusal offers a reload, and that this is raised on `docs/UXD_open_issues.md` item 2.1. Both are now false: UXD version 8 says no refusal offers a reload on a page built after it (`docs/trail/uxd/cycle-5.md` § 2.1, `docs/trail/uxd/cycle-6.md` § 2.2), and that earlier item is gone. RN-24 cites the settled UXD, and its "goes back to unconditional" clause is dropped. These examples carry "has changed to", which item 3.2 questions for a visit with no press (`docs/UXD_open_issues.md` item 2.1), so if the CDO drops that wording they move again. Reasoning: `products/tracker17/docs/trail/content/self_answer-12.md`.

### 3.2 RN-26's reloaded-press case now occurs, and the occurrence it cites is gone
- **Raised by:** PM — 2026-10-21
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** nothing is blocked. The out-of-date refusal's page, reopened with no press,
  has no rule to be written against.
- **Where it shows:** RN-26 (`docs/CONTENT.md:L556`) says "A refusal shown after a redirect from a
  real press and then reloaded has the same property. No occurrence is cited for it, so it waits
  until one occurs." It occurs now: the page a refused out-of-date press lands on carries the refusal
  in its address (`web/routes.py:L384-L392` reads `move_refused` from the query on every load), so a
  reload, Back or a bookmark of that page shows "The status of '…' has changed to {status}. …" again
  (`web/pages.py:L752`), where the tracker sees only an address and cannot establish that anything
  changed since a page the reader holds. Two things for the round: whether that line meets the rule
  when reached with no press, and if not, what it says instead; and RN-26's cited occurrence, "the
  refusal `web/pages.py:760` writes … ('the move you pressed')", which no longer exists —
  `grep -rn "the move you pressed" web` prints nothing.
- **If a document has to be written:** `CONTENT.md` itself, by `product-content`; whether the
  reopened page shows the refusal at all is UX-I3's, in the UXD.
- **Answer:** Raised upstream, for the half that is not `CONTENT.md`'s. The item asks two things. The half that is the verbal language's, that the line does not meet the rule when reached with no press and that RN-26's cited occurrence is gone, is answered and moved out to § 2, item 2.1, where the next round confirms it. This item is left asking only what the reloaded page's line should say instead. That is the UXD's, because the tracker can't tell the first landing from a later visit, so one string serves both, and any wording that makes a later visit true drops UX-F4's confirmed "says the task's status has changed". It is carried on `docs/UXD_open_issues.md` item 2.1, with this run's lean: state the task's status and what it allows, and claim no change. `CONTENT.md` keeps its current wording and examples until the CDO answers. Reasoning: `products/tracker17/docs/trail/content/self_answer-12.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
