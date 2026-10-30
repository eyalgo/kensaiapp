# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md (version 18)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None — no answer rests on a source outside this repository. The HTML
  standard's form submission algorithm, which RT-8 cites, is not leaned on: the item does not reopen
  what a `get` form is, only what status its address answers in one mode. Read in this repository at
  `c6946020b`: the companion whole; `SDD.md` whole at its header, § 4 (RT-5 to RT-11, SD-1 to SD-6,
  SEC-2, EX-11 to EX-14), § 6 S-8, § 12, RN-53, RN-55 and RN-69 to RN-73, and § Open Questions;
  `SRS.md` FR-8 and NFR-4 at their lines; `UXD.md` § 4 and the UX-S9 and UX-I7 rows; `fdr.md`'s
  header at version 6, searched for a `get`-form status; `nfdr.md`'s header and QC-7;
  `architecture_open_issues.md` § 3.1 and `trail/architecture/self_answer-26.md` whole;
  `trail/sdd/self_answer-18.md` and `cycle-15.md`; `web/routes.py` (`_refused_before_routing`,
  `Site.handle`, `UnreadableSite`); `tests/integration/test_unreadable_routes.py` (`TARGETS`,
  `test_checked_unreadable_reads_share_one_representation`, `test_only_checked_get_serves_the_stylesheet`,
  `test_checked_post_always_redirects_without_decoding_or_acting`); the open station the item's
  raiser walks, as an input for the commit's directional alone. No suite was run: the round changes
  no code and reads what the tests assert.

## Items worked

### 2.1 — § 4 RT-8's 200 for a form sent with method="get" does not hold while the unreadable-data page shows

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is taken, and two things are added that a reader would otherwise re-raise.
  Check 1: the edit lands in § 4 RT-8, a CTO condition under *The runtime and how it is started —
  CTO*, and binds the document's consistency alone — no person, money or risk — so it is this seat's.
  The item carries a Principal Architect `Raised by:` under a § 2 heading the header reserves for the
  three lane seats; it carries a real lean, so it is weighed as a draft and not re-bucketed, as RN-72
  did for the Principal PM's. Check 2: the item holds, and the doubt it records is answered no. RT-8,
  `SDD.md` "the tracker answers that address with the page, 200, as it answers a link", names a
  status with no mode; `UnreadableSite.handle` answers every checked non-POST request that is not
  `GET /style.css` with the one page, 503, `no-store`, and the test asserts it at eleven addresses,
  two with a query. EX-13 does not settle it alone, because EX-13 names a page and RT-8 names a
  status, and the status is the false part: under § 12, "the § 4 statement wins and the entry is
  re-derived", RT-8 read alone would overrule the scoped QC-7 that
  `architecture_open_issues.md` § 3.1 answers. So the sentence is needed, and it is a correction of a
  statement false in one mode, not a widening; it cites its occurrence. The draft keeps § 4 silent on
  the mode's status, and that is right: RN-69 placed the status with the product and the records, no
  upstream document names one, and a § 4 clause naming 503 would bind a requirement nothing above
  states, which the item did not ask. The two additions. (1) The `get` passage states two 200s, the
  page's and the refusal's, and the draft's "this 200" reaches one. On unreadable data the form's
  values are never read — `handle` partitions the target and drops the query, and the test sends
  `/people?name=needle` and asserts no "needle" in the page — so no refusal arises and neither 200
  reaches that mode. The sentence says so. (2) The draft says RT-8's serving-mode rule does not move,
  but not that the submission half holds *in the unreadable mode*. It does, as written: a same-origin
  `post` is answered 303 to `/`, built by `_address`, with its body unread
  (`test_checked_post_always_redirects_without_decoding_or_acting`), and a link or a reload changes
  nothing because no state exists. EX-13 and TO-4 were scoped whole; RT-8 is not, and a reader who
  has seen those two rounds would otherwise ask why. One clause says it. Check 3: the answer agrees
  with SD-1 and TO-4 (the mode is fixed at start), SD-4 (no write), EX-13 (one page, every address),
  SEC-2 (the request check runs first in both handlers, `_refused_before_routing`), RT-11 ("the GET
  schedules, saves and records nothing"), § 11 R-10 (the listener's bound reaches a `get` form's
  address before either handler sees it), RN-53 (a `get` form is a read, 200, which stands for the
  serving mode), RN-69 ("no condition in § 4 names a status for it", still true), SRS NFR-4 and
  FR-8, UXD UX-I7 and UX-S9, and with the scoped QC-7 and the ADR-0011 successor
  `self_answer-26.md` §§ 3.1 and 3.3 decide. The FDR carries no `get`-form status (`fdr.md` at
  version 6, searched: its one "200" is a field length), so no companion is owed there. Check 4:
  empty — no saved data at all is the serving mode on an empty state, and the 200 stands; absent —
  data removed or repaired while the page shows changes nothing, the mode being fixed at start;
  concurrent — two `get`-form requests read one fixed page and write nothing; refused — a
  cross-site, same-site or wrong-host request is 403 before either handler, in both modes, and a
  bookmark's `none` mark opens the page in both. One case named and not covered: a browser's cached
  copy of a filter page from an earlier sitting, shown on a start on unreadable data. RT-8 binds no
  cache header on an ordinary page, a reload fetches the 503 page, and nothing saved is touched, so
  the sentence does not reach it and does not need to. The close call was *confirmed*; it lost
  because "this 200" is one of two, and because the submission half's standing in the mode is what
  the next reader of EX-13 and TO-4 would ask. One thing seen and not raised: the header's *Inputs
  read* still says the FDR is at version 4 with a live companion and the architecture companion
  unanswered, and `fdr.md` reads version 6 with its companion removed at `86f97f253` and
  `architecture_open_issues.md` answered at `c6946020b`. The fold catches the header up on its own
  run, as RN-60, RN-66 and RN-70 record it doing without an item, so no item is appended for it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
