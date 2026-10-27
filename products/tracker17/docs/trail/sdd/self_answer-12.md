# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-27
- **Sources re-read:** the HTML standard, form submission
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, read 2026-10-27): the
  algorithm's scheme-by-method table gives "Mutate action URL" for `http` and `https` under GET and
  "Submit as entity body" under POST, and "Mutate action URL" reads "Set parsed action's query
  component to query" followed by "Plan to navigate to parsed action" — so the standard's own
  "form submission" covers a `get` form, which is the fact the answer rests on for why RT-8's word
  needs defining. Everything else is this repository's, read on disk: `SDD.md` whole, and § 4 RT-7,
  RT-8, RT-9, RT-10, RT-11, SEC-2, EX-2, EX-3, EX-4; § 6 S-5; § 9 TO-7; § 11 R-10; § 12; RN-21,
  RN-24, RN-25, RN-49; § Open Questions; the companion whole; `architecture_open_issues.md` whole;
  `adr/0006-last-action-travels-in-the-page-address.md`; `nfdr.md` QC-7, QC-8; SRS NFR-4, FR-31 to
  FR-36, AC-13, AC-14; UXD § 4 ("Every page has its own address"), UX-F5, UX-I3, UX-I6, UX-I7,
  UX-I9, UX-S4; `web/routes.py:L50-L135` (the route table, `SUBMISSION`, `_address`),
  `L231-L251` (`handle`, the same-origin check keyed on `route.kind`), `L481-L507`
  (`_project_page`), `L799-L805` (`_carried_filters`); `web/pages.py:L1140-L1200` (`_filter_field`,
  `autofocus` on the first refused field, `_filter_area`, the `method="get"` form at L1189);
  `domain/text.py:L12-L13` (`SHORT_TEXT_MAX = 200`); `tests/integration/test_routes.py:L1090-L1110`;
  `tests/integration/test_filter_routes.py:L67-L85`, `L107-L130` (`REFUSING`, the 200 page with no
  result), `L159-L180`; the seed `2026-10-11_narrow-and-sort`, the open station
  `2026-10-27_project-list-filter`, the refine report and recommendations of 2026-10-27, and the
  sealed unit's `flow_findings/development-design.md` and `change_design.md` § Architect Review
  Notes (GET Apply) — journey material read as input, cited nowhere in the answer. No suite was run:
  the item is about what RT-8's words mean against a form that exists, every claim rests on code
  and tests read at `HEAD`, and this round changes no code.

The companion held one open item, § 5.1, `Seat: cto`, raised by the PM's `shukuba-refine` run after
the `project-list-filter` unit sealed; §§ 1 to 4 read None. The invocation listed no items, so this
run worked the one open item. It did not split: one question, one seat.

## Items worked

### 5.1 — RT-8 says every submission is answered by a redirect; the filter form is answered with a page

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** The item carries no draft — it poses the two readings and leans to neither — so it is
  answered from scratch. It is a correction, not a widening: RT-8 as worded is false of a form the
  item cites on disk (`web/pages.py:L1189`), so § *A widening item waits until it occurs* does not
  reach it.

  *Seat (check 1).* The edit lands in § 4 RT-8, under *The runtime and how it is started — CTO*, a
  CTO row of § *Who decides what*. It binds the document's agreement with the product and with its
  own SEC-2 and EX-3, commits no person, party, money or risk, and I can name no ground I cannot
  see. Mine. The CDO's rows are not touched: EX-3 and EX-4 already say what the experience
  requires, and the answer shows they hold. The same sentence in ADR-0006 and QC-7 is the Principal
  Architect's and already sits on its own companion (§ 3.1, `632123a1c`), so nothing is raised
  upstream from here; § 12 says § 4 wins where they disagree.

  *The question (check 2).* It is the right question and it is answerable from the document: RT-8
  states its own purpose, "so reload, back and forward never repeat an action", and the purpose
  decides the word. A redirect after a `post` keeps a reload from re-sending a change. A `get` form
  changes nothing (RT-8's first sentence, which the product keeps — `test_filter_get_preserves_route_security_and_state_contracts`,
  `test_a_refused_filter_changes_nothing_on_disk`), so a reload of it repeats a read, which UX-I7
  asks for by name ("reload, back and a bookmark all keep the narrowed list"). A redirect there would
  send the browser to the address it had just asked for and buy nothing. One second question was
  inside the item and is answered in the same slot, same seat: *why* the words alone do not settle
  it. The HTML standard's "form submission" covers a `get` form (re-read at the source, above) and
  UXD UX-I6 uses the browser's verb, "submits", for every form, Apply included — so read with the
  browser's word RT-8 is false and read with the narrower word it is true, and RT-8 has to say which
  it means. I was close to writing only the narrow reading; what tipped it to also naming the
  browser's word is that a reader holding the standard's definition reaches the opposite conclusion
  for a stated reason, and a sentence that does not meet that reason reopens.

  *Nothing settled moves (check 3), and the opposite reading would move something.* SEC-2 is the
  decisive settled text: "A request the operator starts from the address bar or a bookmark is
  marked `none`, so a page opens on it and a submission does not." UX-I7 and EX-3 require a
  bookmarked narrowed list to open. If a `get` form were a submission, SEC-2 would refuse the
  bookmark, so the two readings cannot both hold against the UXD, and the UXD is settled. The
  product keys the check the same way: every `post` route is `SUBMISSION`, every `get` route `PAGE`
  (`web/routes.py:L103-L119`), the same-origin requirement fires on `route.kind == SUBMISSION`
  (`L247`), and the filter test refuses `cross-site` and `same-site` GETs while sending Apply with
  no `same-origin` mark (`test_filter_routes.py:L159-L180`). SRS NFR-4 holds: a request from
  another origin is still refused. UXD § 4, UX-F5, UX-I3, UX-I6, UX-I7, UX-I9 hold. EX-2 (no
  script) and EX-3 (choices in the address and nowhere else) hold, and EX-3 is what a `get` form
  realizes with no script. RT-7 holds. RT-11's "the GET schedules, saves and records nothing (RT-8)"
  is the same reading, and my answer in `self_answer-10.md` § 5.1 rests on it; the two agree. QC-7's
  route test holds as it stands under this reading — "sends each non-submission request and asserts
  the state is unchanged, and sends each submission and asserts a redirect" — the filter GET is a
  non-submission in its enumeration (`test_routes.py:L1090-L1110`). The `change_design.md` review
  note justified GET by reloadability only, which is the design flow finding that raised this;
  the answer supplies the reason the note lacked. The refine's "Considered, not moved" row on the
  address-size bound (a non-occurrence) is not reopened: the answer names the bound as already
  covered by R-10 and RT-10, with the number, and raises nothing.

  *Failure paths (check 4).* *Empty*: a project with no tasks shows no filter form (`_filter_area`,
  "for a project that has tasks"); a hand-typed filtered address on it answers the page as any
  address does. *Absent*: the project no longer exists — the not-found page, 404
  (`test_missing_project_wins_over_invalid_filter_choices`), a page under either reading. *Stale*: a
  bookmarked address naming an assignee who has since left the list, or a status the filter does
  not know — FR-33's refusal, the page, 200, no list, nothing saved (`REFUSING`,
  `test_a_refused_filter_changes_nothing_on_disk`); a later load of the same address reflects the
  current state and clock (`test_reload_bookmark_and_back_recompute_without_saving`,
  `test_date_boundaries_follow_the_clock_not_the_address`), which is RT-7 and UX-I9. *Concurrent*:
  a move posted from a narrowed list carries the list's choices and its redirect lands on the
  narrowed address (`_carried_filters`); a malformed carried filter stops the move before it saves.
  The `post` takes the redirect, the `get` it lands on is a read — each half under its own
  sentence, and the answer says so. *Refused*: the reversed range, the off-list name, a value the
  control cannot hold — answered with the page at the asked address, the reason beside the control
  and `autofocus` on the first refused field (`web/pages.py:L1168`), so EX-4 holds without an
  address being built; what was typed is already in the address. *Size*: seven keys, a name or a
  label at most 200 characters (`SHORT_TEXT_MAX`) at 12 bytes each, two dates and a flag — under
  6,000 of the 65,536 bytes (R-10); a hand-typed address with repeated keys is outside the
  tracker's own forms, the boundary RT-8 draws for the over-long refusal. Named and not covered:
  what the pinned browser does with a `get` form whose selected value contains a character outside
  the Basic Multilingual Plane is the same case RN-25 already leaves to the UXD, and nothing here
  changes it.

  *Noticed, not raised.* The document's header says `SDD_open_issues.md` does not exist and that
  `architecture_open_issues.md` holds § 2.1 opened on 2026-10-20; both are the producing run's own
  lines about its inputs and are rewritten by the fold this answer is owed, so neither is worth a
  cycle of its own.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
