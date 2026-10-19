# Self-answer report — PRD.md

## Header

- **Companion:** products/tracker17/docs/PRD_open_issues.md
- **Document:** products/tracker17/docs/PRD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-05
- **Sources re-read:**
  - `gh repo view <instance-repo> --json visibility` returned `{"visibility":"PRIVATE"}`, and
    `git -C . remote -v` names
    `git@github.com:<instance-repo>.git` as the only remote. Item 2.1 rests on this.

## Items worked

### 2.1 — tracker17 is not public yet; the owner is its only reader until they publish it

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** The draft states a fact and leaves the publishing decision with the owner, and both halves
  hold. The fact was re-read at its source this run: `gh repo view <instance-repo> --json
  visibility` returned `"PRIVATE"`, and that repository is the only remote tracker17 sits under. So the
  Assumptions line "No outside reader can reach it today" (`products/tracker17/docs/PRD.md`,
  § Assumptions, "tracker17 is not public yet") is true as written.

  **Why this run decided it, when the last run left the same subject to the owner.** Last round's item
  2.5 asked whether tracker17 should be public and where outside readers get it, with no draft. Answering
  that meant choosing a publishing stance, which commits the owner's public presence to outside readers,
  so `products/tracker17/docs/trail/prd/self_answer-1.md` § Left for the owner left it. Item 2.1 asks
  something narrower: whether the PRD may record that tracker17 is not public and that publishing is the
  owner's to decide. Confirming publishes nothing, sets no date and rules nothing out. The PRD line itself
  says "it stays that way until the owner decides to publish it". The grounds the last run named, the
  owner's public presence and the outsider-facing instance it cannot see (`kensaiapp.md` § What this is
  about, "Documents that describe kensaiapp to an outsider are not written here"), bear on whether to
  publish, and this answer does not decide that. On this reading, the item is the same kind as last
  round's 2.6. That draft took the side that commits the owner to nothing, and it was confirmed for that
  reason (`self_answer-1.md` § 2.6). The draft is also the answer the last run said it would have given:
  "Have the PRD's Assumptions say plainly that outside readers cannot reach it until the owner publishes
  it" (`self_answer-1.md` § Left for the owner, 2.5).

  **Check 3.** The line agrees with § Target Users, "Until outside readers arrive, the owner stands in
  for this person". It also agrees with the second Assumptions bullet and with Risks, "The only judge is
  the owner". It does not conflict with § Purpose, "needed now because kensaiapp has no simple example
  product to point such a person at". The product is built now. Pointing an outside reader at it is a
  later act, and the owner's Agari answer, "I can use it locally easily by myself"
  (`system/projects/tracker17/agari_open_issues.md`, § 1.1), does not require publishing.

  **Check 4.** Stale: the line is true until the owner publishes. After that, the line is false and the
  "fresh copy" in Success Metrics, "Simple to set up", needs a place. This answer names that case and
  does not cover it, because publishing is itself a change to the PRD, made when the owner decides on
  it. Absent: today no outside reader can get a copy at all. That is the state the line records, and
  Target Users already has the owner stand in.

  **What would have tipped this to *left for the owner*:** a line that set a date, ruled out publishing,
  or named where readers get it. Any of those would make the owner's call for them. Also tipping: an owner
  statement that outside readers are wanted now. Nothing in `products/tracker17/docs/trail/prd/cycle-1.md`
  says so. The owner can still override in any later round by naming where readers get it.

### 2.2 — What a reader gets: source code to read and run — no package, installer or hosted demo

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** This is last round's item 2.11 renumbered, and the last run already reached **confirm** on it
  (`products/tracker17/docs/trail/prd/self_answer-1.md` § 2.11). That run left the slot empty only
  because the skill requires an appended item's slot to wait for the next round. A prior verdict of this
  run binds it the way the owner's would, so this run did not re-weigh the item. It checked only that
  nothing since has moved under it. Check 3: `products/tracker17/docs/PRD.md` still says the same thing
  in § Out of Scope, "A package, an installer, or a hosted demo. tracker17 is offered as source code to
  be read and run", and in § UX Notes, "Arrival". It still rests on the owner's answers 1.4, "Look at the
  code, see if it works, and see if it's simple to set up on a machine", and 1.5, "Not hosted"
  (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1). Item 2.1, decided first in this pass, was
  confirmed as "not public yet". That does not touch this item, which holds whether or not tracker17 is
  published. Check 4, absent: an outside reader with no copy cannot start. That is item 2.1's state, and
  item 2.1 records it.

## Left for the owner

None this run.

## Skipped

- **§ 1, § 3, § 4** — each says "None." and holds no item.

## Raised on this document

### 2.3 — Key Use Case 2's trace — following one feature from the PRD to its code and tests — has no success bar

- **What the document is owed:** the **Simple to read** bar in `products/tracker17/docs/PRD.md`
  § Success Metrics gains one sentence. It checks that the owner can follow one Core Feature from the
  PRD to the code that builds it and the tests that check it.
- **Why it is worth a cycle:** On the ground *a fact in it is now false*
  (`<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The items are not
  the whole of what a document is owed). § Success Metrics says "Each bar names the Key Use Cases it
  checks, and together they cover all five". **Simple to read** names Key Use Case 2 and checks only
  "the owner reads the code cold and judges it simple". Key Use Case 2 also says the reader "follows one
  feature from the product definition to where it is built and where it is tested", and no bar checks
  that half. The unchecked half is also the product's stated edge. § Why This, "What tracker17 adds",
  rests on the trace tracker16-X "can't show". So the measure that the SRS and the documents below it
  read leaves out the one claim that sets tracker17 apart. The gap was this run's own doing. Last
  round's item 2.4 was answered "use case 2, reading the code and tests, is checked by **Simple to
  read**" (`products/tracker17/docs/trail/prd/cycle-2.md` § 2.4). Item 2.10 in the same round kept the
  trace in Key Use Case 2. Each answer was sound on its own, and together they leave the trace with no
  bar. That is the contradiction check 3 exists to catch. Because a prior answer is settled, the prompt
  routes it as a raised change rather than a quiet correction (§ On a re-run). What would have kept this
  from being raised: reading "judges it simple" as already including the trace. The bar's wording does
  not support that reading, and a downstream seat would not make it.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/PRD.md** — `<CORE>/launchers/skill/launcher.sh product-prd tracker17`
