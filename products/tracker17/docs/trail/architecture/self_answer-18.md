# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-27
- **Sources re-read:** The HTML Living Standard, § Form submission algorithm
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html), read 2026-10-27. For
  `http` and `https` its table gives GET "Mutate action URL" and POST "Submit as entity body", and
  the algorithm runs for a form whose method is GET. So in the standard's words a `get` form is
  submitted, which is why the records must define the word rather than lean on it.

## Items worked

### 3.1 — ADR-0006 and QC-7 say every form submission is redirected; the filter form is answered with a page

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** A submission is a `post` form, and a `get` form is a read answered with its page, 200,
  with no redirect. ADR-0006 is superseded by a new ADR-0011 and QC-7 is revised in place.
  - **Seat.** The edit lands in `adr/` and `nfdr.md`, so the item is this seat's. The decision under
    it, what a submission is, is the CTO's. The CTO has already made it: SDD version 12 § 4 RT-8
    (`SDD.md:330-350`) and RN-53 (`SDD.md:2384-2418`), settled at `328b15aaf` on 2026-10-27. This
    run records that decision. It does not make it. Nothing in the answer binds a person, money or
    a risk the owner carries, so it is not left for the owner.
  - **Not "not until it occurs".** The item corrects a sentence it shows to be false of the
    product, which is not widening. It also cites an occurrence that is on disk:
    `web/pages.py:1189` builds the filter form with `method="get"`. Every other form in that file
    is `post` (`:478`, `:607`, `:739`, `:1398`, `:1512`, `:1564`, `:1655`, `:1906`, `:1941`,
    `:2023`).
  - **The question is sound, and it hides a second one.** The item asks which reading the records
    owe. It also asks, without saying so, how an accepted record takes the change.
    `product-architecture`'s SKILL.md says an accepted record "is **never** rewritten, reworded",
    and that a reading where a correction was meant rather than a reversal "is a companion item,
    because guessing between the two destroys the log's only unique asset". So the answer states
    which it is. Held to its own words, and to the standard's meaning of "submission", ADR-0006
    owed the filter form a redirect. RT-8 now says the opposite for a `get` form. That is a change
    to what was decided, so ADR-0011 supersedes ADR-0006. RN-46's other path, leaving a record
    unedited because "each citation was true on its date", does not fit here. ADR-0006's Decision
    is a standing rule that the delivery tier reads as fixed. A later Architect cutting the sort
    controls or the All tasks list from ADR-0006 alone would owe them a redirect. Both answers
    belong in the one slot, because they share a seat.
  - **What ADR-0011 carries.** All of ADR-0006's decision, alternatives and consequences, unchanged,
    plus:
    - RT-8's definition of a submission.
    - The `get` form's answer: the page, 200, no redirect, nothing saved.
    - The `get` form's refusal: the page at the asked address, the reason beside the control. No
      address is built, because the address already carries what was typed (RT-8; EX-4).
    - RT-8's purpose for the redirect: so that an action is never repeated, while a read repeated
      is what UXD UX-I7 asks for.
    - The standard's GET "Mutate action URL", as the reason the word has to be defined.
    - In *Dependence*, § 11 R-10's bound on a `get` form's values: seven keys under 6,000 of 65,536
      bytes (`SDD.md:1460-1464`).
    - In its trace, SDD RN-53.
  - **Settled record checked.**
    - SEC-2 opens a bookmarked page request and refuses a bookmarked submission. Under the opposite
      reading it would refuse the bookmarked narrowed list that UX-I7 and EX-3 require to open (RN-53).
    - ADR-0010 already says "the GET schedules, saves and records nothing".
    - The product keys the check on the route's kind: every POST route is `SUBMISSION`
      (`web/routes.py:54`, `:105-115`).
    - The QC-7 route test sends each submission and asserts 303 with a `Location`, and sends each
      other route and asserts 200 with state unchanged (`tests/integration/test_routes.py:301-345`).
    - `test_filter_apply_reload_and_clear_are_pages_that_save_and_set_nothing` (`:1090-1109`) asserts
      200, no cookie and nothing saved for Apply, its reload and Clear.
    - `tests/integration/test_filter_routes.py:159`,
      `test_filter_get_preserves_route_security_and_state_contracts`, holds QC-32 for the filter.
    So QC-7's *verified by* already holds under the definition. It gains a citation, not a new test.
  - **Failure paths.**
    - *Refused:* a from-date after the to-date, or a name not on the list, is answered with the page
      and no list (RT-8, EX-4).
    - *Concurrent:* a move posted from a narrowed list takes the redirect, which lands on the
      narrowed `get` address (`web/routes.py`, `_carried_filters`). The `post` is the submission and
      the page it lands on is a read.
    - *Stale:* a bookmarked filter address reopens on today's state, which is what NFR-3 asks of any
      page.
    - *Absent:* a filter address naming no project gets the not-found page, as for any page.
    - *Over-long:* only an address hand-typed with a key repeated can exceed R-10's bound. The
      tracker's own pages did not send it, and RT-8 already draws that boundary.
    - *Not covered:* a future `get` form that changes state is refused by this definition, not
      allowed. That is the point of the rule, and QC-7's route enumeration catches it.
  - **What else the fold reaches**, for the producing run:
    - QC-8 traces to ADR-0006 (`nfdr.md:84`), and § 4's "a cost ADR-0006 records" (`:407`) cites
      ADR-0006 too. Both re-point to ADR-0011.
    - QC-32's "a request marked `none` that is not a submission opens its page" keeps its words and
      now reads by QC-7's definition.
    - The NFDR header's *Inputs read* has SDD version 11 and UXD version 8. Both moved, to 12 and 9,
      since the last fold.
    - The ADR index gains the ADR-0011 row, and its ADR-0006 row shows `Superseded`.
    - RN-44 and RN-45 are dated records and are not edited.
  - **What would have tipped it.** If the SDD had not settled RT-8 first, this item would have been
    raised upstream to the SDD, because the definition is the CTO's call. If the skill allowed a
    clarifying note on an accepted record, that would have been lighter than supersession. It does
    not allow one.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
