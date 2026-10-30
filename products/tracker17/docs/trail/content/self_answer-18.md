# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** `https://man7.org/linux/man-pages/man7/signal.7.html`, which says "The signals SIGKILL and SIGSTOP cannot be caught, blocked, or ignored." It lists SIGTERM's default action as terminating the process and says nothing explicit about whether SIGTERM can be caught. The answer rests on that only to keep the row from claiming the tracker had "no chance to finish", which the page supports for SIGKILL alone.

## Items worked

### 3.1 — Terminology has no term for a tracker ended by a kill it can't handle

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** Add one row to § Terminology and no other rule. The term is "killed", for a tracker the reader ended by force rather than with Ctrl-C, and the row says who may use it. The item is this document's own question, so the answer goes in its slot and no upstream companion is raised.
  1. **Whose it is.** The edit lands in `CONTENT.md` § Terminology. It commits nobody and no outside party, and I can't name a ground I'm missing, so it isn't the owner's. The definition documents say "a killed process" (`docs/SRS.md` NFR-2 and NFR-3, `docs/fdr.md` R-6 and R-19, `docs/adr/0009-one-unix-lock-no-windows.md`). They keep their own vocabulary, as they do for "console", which this document already renames to "terminal" (RN-5). So no upstream change is owed.
  2. **It cites its occurrence, so "not until it occurs" doesn't apply.** The item sits under "Raised from downstream" and asks the Terminology table to state a term it doesn't. It cites `README.md:L79`. I re-read it: "A tracker that was killed doesn't prevent the next start. There's nothing to do first. Type the same commands, and the tracker reads its saved data as the killed tracker left it." The setup instructions are inside § Scope. That is a site in the product now, for the form "killed". The other two causes the SRS names with it, a crash and a power cut, occur in no string: `grep -n -i -E 'crash|power' README.md` prints nothing, and the only product-side hits for "kill" are that line and tests. So the term is taken for "killed" and for nothing wider.
  3. **Check 2: one question, answered on both parts.** The item hides a second question, whether the term covers a crash and a power cut as well. Both parts are this seat's, so it is one answer. Naming all three "killed" would state a cause for two ends the tracker can't tell from a kill, which breaks § Voice, "State only what the tracker established". So the row covers the kill only.
  4. **Why "killed" and not "stopped".** The setup instructions use "stop" for the reader's own Ctrl-C (`README.md:L52`, `:L77`, `:L85`). The sentence at line 79 exists to say the next start works after an end that was not that. One word for both would hide the end the sentence is about. I did not rest this on what the tracker does when it gets Ctrl-C, which I haven't checked. "Killed process" and "process" are rejected as the row for the running product already rejects "server" and "instance": they name a mechanism.
  5. **Check 3, against the document and its inputs.** No row, banned word or example moves. "Kill" is in no banned list. Nothing in the PRD, UXD or DESIGN says it. The one rule with teeth is that no string the tracker prints says how an earlier tracker ended, because the tracker can't establish that. The product already holds it: the test for a start after a kill is described as serving the saved project "with no word about that tracker" (`tests/integration/test_single_tracker.py:L323`). Only the setup instructions say "killed", as the reader's own condition. The reader knows what they did, so the sentence claims nothing the tracker didn't establish. This is the same reasoning as RN-11. The row says what the reader did and claims nothing about what the tracker could finish before it ended, which the signal source above supports for a hard kill and does not state for the default one. My earlier answers in this file and the document's v17 don't conflict; the Needs confirming count and the other rows are untouched.
  6. **Check 4, the failure paths.** Empty: a first start with no earlier tracker never meets the sentence, which is conditional on the reader's own history. Stale: "as the killed tracker left it" is true because the saved data reads as the state before or after the last action and never a mix (`docs/SRS.md` NFR-2), and the row adds no promise about the action in flight. Concurrent and refused: a reader who believes they killed a tracker that is still running meets the refusal line (`README.md:L74`), which states the fact. The row is the reader's condition, so it doesn't contradict that line. **Not covered:** a crash and a power cut. `docs/SRS.md` NFR-3 and `docs/fdr.md` R-6 promise the same start after either, and the setup instructions name neither, so a reader whose machine lost power may not know "killed" covers them. No string names them, so no term is owed; when one does, that string is the occurrence and the row is extended then. Whether the setup instructions should name them is a change that publishes text, not a rule here.
  7. **The other reading, and what tipped it.** I was close to "no change: the word is the reader's own verb and needs no row". What tipped it was that the item's gap is real. A delivered string uses a word the document neither approves nor rejects, with a near neighbour ("stopped") already in the same section meaning something else, and the rule that nothing the tracker prints may say it has no home. The cost is one row and a review note; no example moves.
  8. **What the fold writes.** A row in § Terminology with the concept, the term, the two rejected names with their reasons, and the note that only the setup instructions say it and the tracker's own words never do. The review-notes entry and the wording are `product-content`'s.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
