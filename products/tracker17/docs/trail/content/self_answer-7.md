# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-11: `PRD.md` (v5, Settled), `SRS.md` (v5, Settled), `fdr.md` (v4), `CONTENT.md` (v7).

## Items worked

### 3.1 — The terminology bans `critical` for priority, and the PRD now names it as a priority

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** The terminology row takes `critical` as the fourth priority. The term becomes "priority, with `low`, `medium`, `high`, `critical`", and the rejected list keeps "urgent, normal, P1" and drops `critical`.

  *Seat.* The item is `CONTENT.md`'s. The edit lands in one row of this document, binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is one question, so it doesn't split.

  *Widening.* It isn't one. The item asks for a row that now contradicts a settled document to be corrected, not for the document to state a new case, so "not until it occurs" doesn't apply. The occurrence is cited anyway: `PRD.md:128`.

  *Check 2.* The item's facts hold. `CONTENT.md:150` gives `low`, `medium`, `high` and lists `critical` among the rejected words, and `PRD.md:128` (v5, Settled) says "A task is `low`, `medium`, `high` or `critical`". The item carries no draft, so I read the question itself. It asks which side moves, and only one can. A priority value is product meaning, which this seat may not change, and the terminology row sits on the word side of that line (the CPO decides what a thing is, this seat decides what it is called). So the row moves and the PRD's word stands.

  *Check 3.* Nothing settled moves. `SRS.md:132` and `SRS.md:705-708` (RN-24) name the same four values, and `fdr.md:183` (R-51) and `fdr.md:286-287` (R-90) do too. The status row at `CONTENT.md:148` already takes its values from the PRD in the same way. `critical` appears nowhere else in `CONTENT.md` (`grep -n critical` over the docs, outside trail), so no other rule or example needs to follow. The Case rule (`CONTENT.md:103-105`) already writes priority words "as defined", so `critical` is lowercase, and it may be a string's whole text, as the other three may.

  *Check 4.* One case isn't covered, and I'm naming it. If the PRD's priority set changes again, the row goes stale the same way. The status row has the same exposure and the same cure, which is the fold that follows an upstream change. Empty, absent, concurrent and refused have no meaning for a terminology row.

  *Close call.* The verdict was close to *left for the owner* only if the word `critical` had to be kept out of strings for a reason the PRD doesn't state. The row's rejected list gives no reason for it, so there is no ground to hold the item back.

  *For the fold.* The version, the review note and the Inputs line are the fold's to write. The row can cite the PRD the way the status row does (PRD § Core Features, Priorities).

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
