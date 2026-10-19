# Self-answer report — UXD.md

## Header

- **Companion:** `products/tracker17/docs/UXD_open_issues.md`
- **Document:** `products/tracker17/docs/UXD.md` (version 5, Draft)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-12
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository.
  Everything it leans on was read in this repository on 2026-10-12: `UXD.md` (v5), `PRD.md`
  § UX Notes, `CONTENT.md` (v10, Settled), `docs/trail/content/self_answer-9.md`,
  `products/tracker17/web/pages.py`, `products/tracker17/web/routes.py`.

## Items worked

### 2.1 — A refusal whose page already shows what the reader wanted: does UX-I3 still require it to name an action or offer a reload?

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** UX-I3 takes the exception. A refusal names what to do where something is left to do.
  Where the state the operator wanted already holds, and the page the refusal lands on already shows
  it, the refusal says what is true now, and names no action and offers no reload.

  *Seat.* The edit lands in `UXD.md` § 7, UX-I3, which is this document. It binds no person, no
  outside party and no risk the owner carries, and I could name no ground the owner holds that I
  cannot see. The item is one question, so it does not split. Its downstream half, `CONTENT.md`, is
  already folded: `CONTENT.md` v10 says "then one action where one exists" (`CONTENT.md:L209-L210`)
  and records this item as the open UXD side (`CONTENT.md:L550`).

  *Check 2.* The draft's facts hold. UX-I3 says the reason "names what to do" and that an out-of-date
  refusal "says so and offers a reload" (`UXD.md:L349-L353`). The shipped label refusal is at
  `web/pages.py:L717-L722`, and it names no action. The draft's reasoning also holds: the PRD asks
  only for "the reason in plain words" (`PRD.md:L179-L180`), and the Content Manager cannot relax a
  UXD requirement, so the UXD has to state the exception. It missed a stronger reason inside the UXD
  itself. UX-A3 already asks a refusal to describe how to correct it "where a correction exists"
  (`UXD.md:L386-L389`). UX-I3's unconditional "names what to do" therefore disagrees with its own
  document's accessibility entry, as well as with `CONTENT.md`. The exception brings UX-I3 into line
  with UX-A3.

  *Addition 1 — the exception is bounded by where the refusal is shown.* It holds because the refusal
  lands on a page loaded after the refusal and built from the saved data. Removing a label the task no
  longer carries redirects to the task's own address (`web/routes.py:L506-L522`). That page lists the
  task's current labels, so a reload would show nothing new. A reload helps only on a page that is
  still out of date. Where the wanted state does not hold, the refusal still names what to do. That
  covers a status move another tab overtook (UX-F4) and an assignee who left the list before an add
  or an edit (UX-F3, UX-F9). Those entries stand.

  *Addition 2 — a second occurrence that does not follow the exception.* Removing an assignee who is
  already off the list is the same kind of refusal. The route redirects to People, freshly built
  (`web/routes.py:L568-L580`). Its line still ends "Open People again to reload the list."
  (`web/pages.py:L925-L930`), and that reload shows what the page already shows. The code gives both
  refusals the same outcome, `STALE_REMOVE` (`web/pages.py:L722`, `L930`). Neither document needs a
  change for it. The string has to change, through a change that publishes text, to meet UX-I3 as
  amended and `CONTENT.md` v10's refusal pattern. No companion can carry a product string, so this
  report is where it is recorded.

  *Check 3.* The exception moves no other settled entry. UX-A3 already agrees. UX-I4, UX-I5 and UX-S9
  are not refusals of this kind. RN-17, which gives the reason for the out-of-date refusal, still
  holds for every case where the page is still out of date. `CONTENT.md` v10 already states the same
  rule, so the two documents agree once the UXD folds this.

  *Check 4.* Empty: if another tab removed the task's last label, the page shows the no-labels
  sentence, and the refusal's "The labels shown are the ones the task carries." then points at an
  empty list. The rule still holds, because the wanted state still holds and the page shows it. How
  the line reads there is wording, which belongs to `CONTENT.md` and the product, and
  `content/self_answer-9.md` already names it. Absent: if the task itself is gone, the route
  redirects to the task's address (`web/routes.py:L517-L518`) and UX-S10 applies, outside this
  exception. Stale: the exception depends on the refusal being shown on a freshly loaded page. A
  refusal shown on the page the operator acted from would still owe a reload, and Addition 1 is
  worded for that reason. Concurrent: two removals of the same label give this refusal on the
  second. That is the case itself, and Addition 2 is its People counterpart. Refused: this is the
  refused path.

  *Close call.* The other reading was an override: every refusal names an action, and both shipped
  strings change to supply one. What would tip it is the owner wanting every refusal to have one
  shape, which is a taste call. UX-A3's "where a correction exists" and `CONTENT.md` § Voice
  (`CONTENT.md:L53`) both stand against it, and under that reading the only action available would
  be a reload that shows nothing new.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
