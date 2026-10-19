# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Every claim it leans on was re-read in `CONTENT.md`, `DESIGN.md`, `UXD.md`, `PRD.md` and `web/pages.py` on 2026-10-07.

## Items worked

### 3.1 — Terminology says `tracker17` appears only in page titles, and the design puts the product name in the header

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** overridden
- **Why:** The item's outcome is taken and its wording is replaced. The header may carry `tracker17`, and `CONTENT.md` § Terminology, row "The running product", stops saying otherwise. The proposal was that the row "also names the header". The answer is that the row names no place at all. It now reads: "`tracker17` is the product's name, written as § Grammar and mechanics (Case) sets it. For itself, in a sentence, the tracker says "the tracker"." This is written in the slot, for the next `product-content` run to fold.

  *Seat.* This item is `CONTENT.md`'s. The edit lands in one note of one Terminology row, in this document. It binds no person and no outside party, and I could name no ground the owner holds that I cannot see. The item's second branch ("if the header should not carry it, the change is the design's") is an alternative to the same question and not a second one, so the item does not split. It is not a widening either: it corrects a statement that is false against a settled document, and it cites an occurrence anyway (`web/pages.py:52`).

  *The contradiction is real, and I measured it.* `CONTENT.md:144` says "`tracker17` appears only in page titles." `DESIGN.md:350` says "The product name sits on the left" of the header, and `DESIGN.md:427` says the unreadable-data page's header "shows the product name and no nav links". `web/pages.py:52` renders `<span class="product-name">{PRODUCT_NAME}</span>` in every page's header, with `PRODUCT_NAME = "tracker17"` at `web/pages.py:21`.

  *Why the design stands and the row moves.* `DESIGN.md` is Settled and states the placement twice. `UXD.md` is silent on the product name (§ 4 says only that "one header sits on every page" and reaches three areas, `UXD.md:79`), so nothing upstream argues against it. Where a name sits on a page is the CDO's call and not the Content Manager's, so the row's "only in page titles" was a placement rule written in the wrong seat. No document I read gives a reason to take the name out of the header.

  *Why the row names no place, and so differs from the proposal.* The proposal says the row would name the header. That makes `CONTENT.md` the second home of a placement fact the design owns (`DESIGN.md:350`, `DESIGN.md:427`), and the two would drift the next time the design moves the name. The title pattern is already stated once, in § Accessibility of text (`CONTENT.md:349`, `" - tracker17"`). Case is stated once, in § Grammar and mechanics (`CONTENT.md:102-103`, "always lowercase and never starts a sentence"). The row only has to say what the name is and how it differs from the tracker's word for itself, "the tracker".

  *Failure paths.* Absent: on the unreadable-data page the header holds the name and no links (`DESIGN.md:427`), and the new wording covers it because it names no page. Stale: if the design later moves or drops the name from the header, the row needs no change, which the old wording would have. Refused, concurrent and empty: not reached, since the row concerns a word and not an action. Named and not covered: I did not read the written setup instructions, and none is named in the record I read. The old "only" also sat badly with them, since § Scope puts them in the language (`CONTENT.md:25`). The new wording names no place, so it holds for them either way. The sentence "For itself, in a sentence, the tracker says "the tracker"" restates § Voice (`CONTENT.md:98-99`) and doesn't forbid `tracker17` as a name, which the Case rule (`CONTENT.md:102-103`) allows mid-sentence.

  *Close call.* I considered confirming the proposal as written, since its outcome is the same. What tipped it to a different wording is the second home for a placement fact.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — RN-16 says tracker17 has no code yet, and the product now has pages with strings in them

- **What the document is owed:** Review Note RN-16 (`CONTENT.md:493`) is corrected so it no longer says the product has no code and no strings of its own.
- **Why it is worth a cycle:** it meets the prompt's ground "A fact in it is now false", in `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The items are not the whole of what a document is owed. Measured on 2026-10-07: `CONTENT.md:493` says "it has no code yet", and `web/pages.py` was added in commit `5f1f13d81` (2026-10-07, after `CONTENT.md` was settled in `f60f6a6de` on 2026-10-06) and writes strings a reader sees, such as "A project needs a name. Type one." (`web/pages.py:63`). I was close to leaving it, since RN-16 is a note about the evidence at the time of writing and no rule moves. What tipped it is that the corpus is what shows a rule can be applied, and a cold reader is told none exists. Line 434 and RN-15 (line 491) give "no corpus" as the reason for a call made at the time, and I left them out of the item as history.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
