# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-12
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-12: `CONTENT.md` (v9), `UXD.md` (v4, Settled), `PRD.md` (Settled), `products/tracker17/web/pages.py`, `products/tracker17/web/routes.py`.

## Items worked

### 3.1 — A refusal whose page already shows what the reader wanted: does it give an action?

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** The Voice rule governs. A refusal gives one action when one exists. Where the wanted state already holds and the page shows it, the refusal gives the reason and what the page shows, and no action. The item carries no draft, so this was decided from scratch.

  *Seat.* The question is `CONTENT.md`'s: two of its own rules disagree, and the edit lands in this document. It binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is not a widening item. It asks which of two existing rules governs, and it cites an occurrence, `web/pages.py:L718-L721`. It is one question, so it doesn't split. One consequence of the answer reaches another document and is raised there (below).

  *Check 2.* The item's facts hold. The refusal formula (`CONTENT.md:L206-L210`) asks for the reason "then one action". § Voice (`CONTENT.md:L53`) says "when one exists, and none when none does". The shipped string is at `web/pages.py:L717-L722`. The page it lands on shows the task's current labels: `routes.py:L519-L522` redirects to the task's address with the refusal named, and `pages.py` renders the label list from the saved task (`_label_section`, `pages.py:L759-L790`).

  *Why Voice governs.* Three things point the same way.
  1. The formula is the Voice rule applied to the usual case, where the reader has something to fix. It is not a second rule that overrides it. Where no action exists, the formula's "then one action" would force the tracker to invent one.
  2. The only action available here is a reload, and a reload shows what the page already shows. That is the "guide that closes every message with advice" the Voice table rejects (`CONTENT.md:L53`), and it would assert something false about what a reload does.
  3. The Voice table's first row says the reader wants two things, whether it happened and what is true now. The shipped second sentence, "The labels shown are the ones the task carries.", answers the second. Without it the refusal states a fact and leaves the reader to work out the page's state.

  *What the rule becomes.* The refusal formula reads "then one action where one exists". Where none exists, the second sentence says what the page shows, so the two-sentence limit (§ Grammar and mechanics, Sentence length) holds. "No action" is limited to a refusal whose wanted state already holds and is shown. A refusal on input the reader can still fix always has an action, such as "A task needs a title. Type one." (`CONTENT.md:L213`).

  *The fold also checks two other places.* § Tone, the Failure row, says "The reason comes first and the action second", and the Level 1 definition says "the result and one next action". Both state an action without the condition, so the fold adds "where one exists" to both, or leaves them with the reason it gives. I did not decide their wording, because that is the fold's.

  *Check 3.* One settled document reads differently. `UXD.md:L348-L352` (UX-I3, v4, Settled) says the reason "names what to do" and that an out-of-date refusal "says so and offers a reload". The label refusal arises from another tab removing the label, so it is the out-of-date case, and it offers no reload. The PRD does not require an action: it asks only that the refusal tells "the reason in plain words" (`PRD.md:L179-L180`). I answered on `CONTENT.md`'s own rules and raised the UXD wording rather than relax it silently (see `## Companions opened`). If the CDO overrides, the formula returns to unconditional and the shipped string has to change through a change that publishes text.

  *Failure paths.* Empty: if the other tab removed the task's last label, the page shows the no-labels sentence, and "The labels shown are the ones the task carries." then points at an empty list. It is still true, and it reads oddly. I named it and did not settle it, because it concerns the product's string and not the rule. Absent: if the task itself is gone, the route redirects to the task's address (`routes.py:L517-L518`, `TaskNotFound`) and the page is the address-with-nothing-at-it state, which has its own pattern. Stale: the rule holds only where the page shows the state the reader wanted. A refusal on a page that does not show it still owes an action, and the rule says "already shows" for that reason. Concurrent: two removals of the same label produce this refusal on the second, which is the case itself. Refused: this is it.

  *Close call.* The formula governing was the other reading, with the string changed to supply an action. What would tip it is the owner wanting every refusal to share one shape, which is a taste call, and the Voice table already gives the reason against it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/UXD_open_issues.md** — **opened** — companion to `UXD.md`, landed in commit `5a6570821`

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
