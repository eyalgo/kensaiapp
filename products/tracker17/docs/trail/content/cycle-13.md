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

> **Round 12 folded.** The earlier § 3.1 (the out-of-date refusal's examples) is in `CONTENT.md`
> version 13 (RN-27), and the earlier § 3.2 is split: its `CONTENT.md` half is § 2.1 below, its UXD
> half is § 3.1 below. The answered file is `docs/trail/content/cycle-12.md`.

---

## 1. Open issues

None.

## 2. Choices to confirm

### 2.1 RN-26 records an occurrence that is gone and says the reloaded case waits, and it doesn't

> **No `product-content` run wrote this item.** A `companion-self-answer` run raised it on 2026-10-21
> while answering item 3.2, which asked two things. This is the half that is `CONTENT.md`'s, the run
> answered it, and it is here so the next round confirms it. Item 3.1 below is left asking only the other
> half: what the reloaded page's line should say instead, which changes UXD UX-F4 and is carried on
> `docs/UXD_open_issues.md` item 2.1. Reasoning: `docs/trail/content/self_answer-12.md`.

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
- **Confirm or override:** confirm, with three additions. The four changes stand as drafted. Addition 1, the citation. The overtaken-move wording is `_CHANGED` and `_OVERTAKEN_LINES` in `web/pages.py`, lines 751 to 757, and not 751 to 756. RN-26 takes the corrected range. RN-27 cites the same wording at 751 to 756 and takes the same correction. Addition 2, the pointer. The settled case is the second way in that UXD UX-F4 describes, the address that shows or backs out of the confirmation for a move to `cancelled` (`docs/trail/uxd/cycle-5.md` § 2.1). That settles RN-26's sentence that whether the interface shows this refusal "is the UXD's call", because UXD version 8 keeps it. That sentence goes, and so does "if the CDO removes the refusal the clause goes with it". Addition 3, the formula. § Error says a refusal reached with no press "names the move the address asks for". The overtaken page's address carries the task and the code `not_allowed` and no move (`_move_outcome` in `web/routes.py`, which reads only `move_task`, `move_refused`, `move_failed` and `moved`). That page can't meet the clause. The formula gains "where the address carries one", and RN-26 says one line serves the first landing and every later visit, so the wording that fits both is the CDO's answer on `docs/UXD_open_issues.md` item 2.1. Reasoning in `docs/trail/content/self_answer-13.md`.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 What the page a refused out-of-date move lands on says when it is opened again with no press
- **Raised by:** PM — 2026-10-21 (the residue of the earlier § 3.2, re-raised by the Content Manager)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** nothing is blocked. `CONTENT.md` keeps its current wording and examples until the CDO answers.
- **Where it shows:** the page a refused out-of-date press lands on carries the refusal in its address, so a reload, Back or a bookmark shows "The status of '…' has changed to {status}. …" again. The tracker sees an address and can't establish a change. One string serves both the first landing and a later visit, so any wording true on a later visit drops UX-F4's confirmed "says the task's status has changed".
- **If a document has to be written:** `UXD.md`, by the CDO (`product-uxd`), carried on `docs/UXD_open_issues.md` item 2.1 with the lean "state the task's status and what it allows, and claim no change". `CONTENT.md` follows the answer (RN-26, RN-27).
- **Answer:** Carried upstream, and not decided here. This is the CDO's change. It replaces UXD UX-F4's sentence that the reason "says the task's status has changed", which the owner confirmed (`docs/trail/uxd/cycle-6.md` § 2.2), and the SDD and tests that repeat it. It sits on `docs/UXD_open_issues.md` item 2.1, which an earlier self-answer run wrote and committed, and whose slot is still open there. My answer for that item is its lean (a). The line states the task's status and what that status allows, and claims no change, such as "The status of 'Set up CI' is done. A task in done can't be moved." Only that form is true on every arrival. The address carries the task and the code `not_allowed` and no earlier status or target move, so a wording that says the move isn't allowed is false for an address typed for a task in `todo`. The cost is that the line no longer says the press was refused. The status and the move buttons beside it show what is now possible. `CONTENT.md` keeps its wording and examples until the CDO answers, and item 2.1 above settles RN-26's side. Reasoning in `docs/trail/content/self_answer-13.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
