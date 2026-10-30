# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None — no answer rests on a source outside this repository. Read in this
  repository at `6effdff29`: the companion whole; `SDD.md` whole; `UXD.md` § 3, § 4, UX-F11, UX-S9,
  UX-S10, RN-17, RN-18; `DESIGN.md` § Layout (Header) and § Components ({components.header});
  `CONTENT.md` at every line naming the unreadable-data page; `fdr.md` R-25, R-26 and
  `fdr_open_issues.md` §§ 3.1, 3.2; `nfdr.md`'s header; `adr/README.md`;
  `architecture_open_issues.md` whole; `trail/sdd/cycle-1.md` § 2.4, `cycle-13.md` § 2.1 and
  `self_answer-16.md`; `web/pages.py` (`_framed`, `unreadable_data_page`), `web/routes.py`
  (`UnreadableSite`), `main.py` (`start`, `_serve_claimed`),
  `tests/integration/test_start.py` (`test_an_unreadable_start_serves_one_page_and_announces_once`);
  the seed and the open station the items name, as an input; `git log 01d3d925a..HEAD --
  products/tracker17/docs/`, the whole docs history since SDD v16.

## Items worked

### 5.1 — EX-12 says the unreadable-data page carries no header, and DESIGN.md gives it one

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** The header stays on the page, showing the product name and no area link; EX-12's
  "carries no header" goes and its exception narrows to the navigation. Check 1: the edit lands in
  § 4 EX-12, a CDO column in § *Who decides what*, and the CDO has already stated the call in two
  settled documents — the UXD, which is EX-12's own source ("where the two differ the UXD is
  right"), says one header "sits on every page" (§ 4) and gives UX-S9 "no navigation into the
  tracker" and nothing about the header; `DESIGN.md` § Components says outright "On UX-S9, the
  unreadable-data page, the header shows the product name and no nav links", present since its
  version 1 (`<a commit not in the public history>`). An answer that follows the input is this seat's, as RN-31, RN-54 and
  RN-57 did for UXD changes, so no CDO item is raised. The answer binds the document's
  consistency and no person, money or risk. Check 2: the item carries no draft and one question.
  The "no header" clause entered as addition (2) of cycle-1 § 2.4, confirmed in the CDO's seat by a
  self-answer run citing "UX-S9, UXD § 4" — and neither says it; that addition over-read "no
  navigation" as "no header". Check 3: the page as built is the design language's — `_framed`
  renders `<header class="site-header">` with the product name and the navigation it is given, and
  `unreadable_data_page` gives it none; the station's bar ("no link and no form"), § 6 S-8 ("no
  navigation and no control that acts on the data"), FDR R-26 ("no action and no navigation into
  any other area") and CONTENT's note that "the unreadable-data page's header shows" the product
  name all hold under the corrected clause and none under the old one. Check 4: absent — the
  stylesheet is still served by `UnreadableSite`, so the header is styled; refused — a POST is
  redirected to the same page; stale — a later change to the header is DESIGN.md's and EX-12 now
  defers to it rather than stating a shape of its own. The close call was raising a CDO item to
  choose between the two CDO-seat statements; it lost because one of them is a settled document
  the product follows and the other a self-answer addition that cited sources which do not say it.

### 5.2 — EX-13's not-found page does not hold while the unreadable-data page shows

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** EX-13 is scoped to a tracker serving its saved data, and the unreadable-data page takes
  every address in the other mode. Check 1: the edit lands in § 4 EX-13, a CDO column, and the
  UXD settles it in so many words — § 4, "One page replaces all of them when the saved data cannot
  be read (UX-S9): every address shows that page", and UX-S10's own definition speaks of a project
  or task "deleted" or an address "wrong", which presuppose data being served — so it is a
  correction of EX-13's words in this seat, not a change to the experience, and no CDO item is
  raised. Check 2: no draft; one question; not a widening, because EX-13 as written is false of
  the product in one mode and the item cites the occurrence (the test's unknown address answers
  the one page). Check 3: read against my answer to § 5.1 — the one page at every address carries
  the header with the product name only, and the two answers describe the same page; § 4 RT-11's
  404 and § 6 S-7's not-found line speak of a deleted task or project and are reached only while
  data is served, so they stand; FDR R-105 is the same correction, already on
  `fdr_open_issues.md` § 3.2 for its own seat. Check 4: stale — the mode is fixed at start (SD-1,
  TO-4), so a repair made while the page shows is read at the next start and the page does not
  change under the operator, which the answer says; absent — a never-issued identity on
  unreadable data is the same one page; concurrent — a second tracker is refused before either
  page exists. Not covered, and not raised: the SDD states no HTTP status for the unreadable-data
  page (the product answers 503); no reader of § 4 is missing it, and the records' side of that
  mode is the Principal Architect's, on `architecture_open_issues.md` §§ 3.1 to 3.4.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — The header still reads the NFDR at version 19 and the architecture companion as one item on QC-40

- **What the document is owed:** the header's *Inputs read* reads NFDR version 23 and the
  architecture companion as live with §§ 3.1 to 3.5, the PM's five items of 2026-10-30.
- **Why it is worth a cycle:** a fact in it is now false. `SDD.md:6` says "NFDR Settled (version
  19 …" and that the companion holds "one item, § 3.1 on QC-40, unanswered"; `nfdr.md`'s header
  reads version 23 (`4a646aaf0`), the fold that answered QC-40's item and removed the companion,
  and the PM opened it again at `12499fcbe` with five items, none on QC-40. The cost is nil beyond
  this round: the fold is owed for §§ 5.1 and 5.2 anyway, and RN-60 and RN-66 show the fold's own
  catch-up reaching these lines.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
