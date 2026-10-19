# Self-answer report — SRS.md

## Header

- **Companion:** products/tracker17/docs/SRS_open_issues.md
- **Document:** products/tracker17/docs/SRS.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** None. The answer rests only on files in this repository: `SRS.md` version 3,
  `SDD.md` version 2 and `trail/sdd/cycle-1.md`.

## Items worked

### 2.2 — The open question on the runtime is answered, and closes

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The last item of `SRS.md` § Open Questions is removed. No requirement changes, and nothing
  from the runtime is copied into the SRS. The addition says why closing the question does not depend
  on the SDD being Settled.

  *Seat (check 1).* This item is mine, in the owner's seat. The edit removes one line from `SRS.md`,
  which is the CTO's document. It binds nobody outside the product, and I can name no ground I cannot
  see.

  *The draft holds (check 2).* I found each of its claims where it says.
  - `SDD.md` § 4 RT-1 reads "The tracker runs on Python 3.11 or later and imports nothing outside the
    Python standard library", and it ends "settles SRS § Open Questions, the second item".
  - `trail/sdd/cycle-1.md` § 2.1's slot reads "confirm, with four additions". The choice was answered
    and folded, so it is no longer a draft.
  - FR-4 asks for "the prerequisites the machine needs before setup" and names no runtime. C-7 sets
    the three-command, ten-minute bound. AC-3 checks it "on a machine with only the stated
    prerequisites".
  - The SRS header says to keep "the **how**" out. So the draft is right to copy nothing from RT-1.

  *Addition: the SDD's Draft status (check 3).* `SDD.md` reads `**Status:** Draft`. Its one open item
  is § 2.1, the text lengths, which does not touch the runtime. Closing the question does not wait for
  the SDD to reach Settled, but the reason is not that RT-1 is final. The reason is that no SRS
  requirement names the runtime. FR-4, C-7 and AC-3 hold for any runtime the SDD names, and AC-3 checks
  against whatever prerequisites the setup instructions state. The open question was never a gap in a
  requirement. It said only that AC-3's check would wait for a choice, and the choice has been made.

  *Settled record (check 3).* RT-1's first addition reads "The one-time network connection that SRS
  FR-4 and UXD UX-S1 list among the prerequisites is needed only to set up the test suite". I checked
  whether that makes FR-4's line "setup needs a network connection once, to fetch the declared
  dependencies" false. It does not. The declared dependencies are the test suite's (RT-4), and FR-4's
  instructions include "how to run the full automated test suite". § 5.3's "may fetch" allows a
  tracker that fetches nothing. So FR-4 and § 5.3 do not change. I came close to raising a narrowing
  of FR-4 to the suite. What decided against it is that the line is true as written, and wording it
  better is not worth a cycle (`prompts/rich.md` § *What is not worth it*).

  *Failure paths (check 4).* Empty: removing the item leaves § Open Questions with nothing in it. How
  an empty section reads is the SRS template's and `product-srs`'s call. Absent: nothing depends on
  something that can be unreachable. Stale: if a later round changed RT-1, the SRS would still be
  true, because no requirement carries the runtime. The setup instructions and AC-3 would follow the
  new choice. Concurrent: `product-srs` and `product-sdd` may fold in either order. Removing the item
  leaves SDD § 4 RT-1 ("settles SRS § Open Questions, the second item") and RN-3 pointing at a
  question that no longer exists. RT-1's position number is already wrong, because SRS version 3's
  list has one item. That is the SDD's to fix, and it is raised there (§ Companions opened), worded
  to hold under either order. Refused: not applicable.

  *Close call.* I weighed a plain *confirmed*. What tipped it is that the draft's rationale reads as if
  closing depends on the SDD having chosen for good. A later reader could then reopen the question
  every time RT-1 moves. The addition records why that is not needed.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/SDD_open_issues.md** — **appended** — companion to `SDD.md`, item 2.2,
  landed in commit `72125aec4`

*What the SDD is owed, and why it is worth a cycle.* The grounds are "A fact in it is now false" and
"Something upstream moved and it has not seen it" (`prompts/rich.md` § *The items are not the whole
of what a document is owed*). `SRS.md` version 3 states the maximum lengths as FR-40, adds AC-20,
and closes its first open question. `SDD.md` version 2 has not seen any of this. RT-10 says "No SRS
requirement states a bound today", which is false since FR-40. RT-10, RN-4 and RN-22 cite "SRS § Open
Questions, the first item", which has closed. RT-1 cites "the second item", but the list has one
item, and this run's answer closes that one. `grep -c "FR-40\|AC-20" SDD.md` printed `0`, so no slice
delivers the new requirement or its test.

`trail/srs/self_answer-2.md` deferred this change on purpose: "The identifier does not exist until
the fold assigns it". The fold has since assigned FR-40 (commit `4c64b4279`), so the deferral is
over. The item's slot is left at its placeholder. It does not revise SDD item 2.1, because 2.1's
slot is filled.

## Launchers owed

- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
