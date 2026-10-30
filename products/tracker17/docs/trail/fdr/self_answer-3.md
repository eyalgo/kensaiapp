# Self-answer report — products/tracker17/docs/fdr.md

## Header

- **Companion:** products/tracker17/docs/fdr_open_issues.md
- **Document:** products/tracker17/docs/fdr.md (version 4)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None. No answer rests on a source outside this repository.

## Items worked

### 3.1 — R-20's "the tracker's next save replaces it" does not hold while the unreadable-data page shows

- **Bucket:** 3. Raised from downstream — an item raised against the FDR after it settled
- **Verdict:** answered
- **Why:** R-20 is corrected so that its save clause covers only a tracker serving its saved data. The item is a correction of a statement found false, not a widening, so "not until it occurs" does not apply, and it cites its occurrence anyway. Every citation holds: `fdr.md:98-100` carries the sentence, and `web/routes.py`, `UnreadableSite`, states "no tracker, no reader and no saver, so no request can reach the saved data". It is this document's own question and binds nothing outside it, so the seat is this run's, not the owner's. It agrees with the settled record: R-27 and SDD § 4 SD-4 forbid the write, SD-1 keeps "read once", and SDD RN-69 already says "a repair made while the page shows is read at the next start". OOS-16 cites R-20 only for the read at start, and stands. On the failure paths: a repair or a set-aside made while the page shows changes no page and is read at the next start, which `main.py`'s `_serve_claimed` does by loading first; a second start while the page shows is still refused, because `start` claims the location before it reads, so R-5 holds; and a saved file removed while the page shows leaves the next start empty under R-17. "Not shown" holds in both modes, so that clause stays general. SDD § 9 TO-4, which R-20 traces to, carries the same sentence and the same defect, so this run opened the SDD's companion to keep the two agreeing (`## Companions opened`). It was not held back to wait for that round: R-20 is right whichever way TO-4 lands.

### 3.2 — R-105's not-found page does not hold while the unreadable-data page shows

- **Bucket:** 3. Raised from downstream — an item raised against the FDR after it settled
- **Verdict:** answered
- **Why:** R-105 is scoped to a tracker serving its saved data, with the unreadable case and the fixed mode stated beside it. This too is a correction with a cited occurrence, and this document's own to make. `fdr.md:326-327` carries the rule, and `tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`, asks `/`, `/people` and `/nothing?x=1` and asserts one status and one body. The answer follows the input R-105 traces to: SDD § 4 EX-13, corrected at version 17, says the same and "the not-found page included"; UXD § 4 says "every address shows that page"; and SDD RN-69 names this very item as the matching correction. RN-11's line that R-105 takes its behaviour from EX-13 stands. R-25 needs no change, since it speaks of every page served and the new sentence says every address gets that page. On the failure paths: a request from another origin is still refused under R-110 (`UnreadableSite.handle` answers 403 before anything else), and a same-origin form sent from a tab left open from an earlier run is sent back to the one page with its body unread, so nothing changes. I looked at whether R-103 and R-102 owe the same scoping, since they speak of actions checked against saved data, and did not raise them: such a form changes nothing and lands on a page stating why, which meets "refused with the reason", and R-26 already says no action is offered in this mode. A test showing that form answered otherwise would have tipped this. The test asserts status 503 and this answer states none: the FDR names no status for any page, and the records' side of that mode is on `products/tracker17/docs/architecture_open_issues.md`.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — The FDR has not read the upstream documents as they now stand, and SRS FR-41 has no rule here

- **What the document is owed:** a fold that adds R-121 for SRS FR-41, names the second purpose in the Description, brings RN-11's drop-lines up to SDD version 17, and updates the *Inputs read* line. Its slot stays open for the next round.
- **Why it is worth a cycle:** something upstream moved and it has not seen it. `fdr.md:6` reads PRD version 5, SRS version 5 and SDD version 7, and their headers read 7, 6 and 17. SRS FR-41 (`SRS.md:98-104`) came in at version 6, and `fdr.md` holds neither "FR-41" nor "testing ground". `fdr.md:572` names an SDD Open Question that `SDD.md:3112` no longer holds. A rule this doc owes the Product Owner and QA is the part that matters; the rest rides the same fold. The doubt is whether a re-run would catch it unasked: the `product-fdr` prompt allows a delta traced to an upstream change, but its re-run is a fold of answers, and two earlier folds left the line standing, so it is raised rather than assumed.

## Companions opened

- **products/tracker17/docs/SDD_open_issues.md** — **opened** — companion to `SDD.md`, landed in commit `2668d3212`

## Launchers owed

- **products/tracker17/docs/fdr.md** — `<CORE>/launchers/skill/launcher.sh product-fdr tracker17`
- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 SDD`
