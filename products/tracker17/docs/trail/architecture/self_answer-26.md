# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None. No answer rests on a source outside this repository. The status 503 is
  recorded as what the product does, and no answer leans on what a standard or a browser does with
  it. Read in this repository at `86f97f253`: the companion whole; `nfdr.md` §§ 1 to 10 and RN-1 to
  RN-13 and RN-61 and RN-62 in full, with the other Review Notes searched for the unreadable-data
  mode and for a status; `adr/README.md`, ADR-0005, ADR-0011 and ADR-0012 whole;
  `SDD.md` RT-8, RT-11, EX-12, EX-13, SD-1, SD-4, TO-4, § 12, RN-69 and RN-72; `fdr.md` R-20, R-25 to
  R-27, R-105, RN-14; `SRS.md` FR-8 and DR-6; `UXD.md` UX-F11; `web/routes.py`, `Site.__init__`,
  `_respond`, `_address` and `UnreadableSite`; `main.py`, `_serve_claimed` and `_unreadable_line`;
  `tests/integration/test_unreadable_routes.py` whole; `tests/integration/test_start.py`,
  `test_an_unreadable_start_serves_one_page_and_announces_once`. No test suite was run: this round
  reads what the tests assert and changes no code.

## Items worked

### 3.1 — QC-7's 200 for a form sent with method="get" does not hold on a start on unreadable data

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** QC-7's 200 is scoped to a tracker serving its saved data, and QC-7 names the other answer.
  The item arrived with no draft, so this is decided from scratch.
  1. *Whose it is.* The edit lands in `nfdr.md`, this seat's document. It binds no person, money or
     outside party. The item corrects a statement found false and cites its occurrence
     (`web/routes.py`, `UnreadableSite.handle`), so § *A widening item waits until it occurs* does not
     hold it back.
  2. *The item holds, and it is narrower than the clause.* Only QC-7's last sentence is false. The
     first sentences hold on unreadable data: `UnreadableSite` holds no state, so none changes, and a
     `post` marked `same-origin` is sent to a page address built by `_address`, "The one place an
     address is built". The item's two exceptions are both real, and I would add one thing it leaves
     out: the request check runs first, so a request QC-31 or QC-32 refuses is answered 403 and never
     sees the page (`test_request_refusals_precede_page_stylesheet_and_redirect`).
  3. *Settled record.* SDD EX-13 says "every address shows the unreadable-data page and no other", so
     the page is settled upstream. The status is not: SDD RN-69 says "no condition in § 4 names a
     status for it" and leaves it to "the product's and the records'". FDR RN-14 says neither rule
     states a status code. So QC-7 can name 503 as the product's measured answer, traced to EX-13 and
     the test, without inventing a requirement. **One thing does not agree.** SDD RT-8 states the same
     200 with no mode, and SDD § 12 says "the § 4 statement wins and the entry is re-derived". Read
     strictly, RT-8 would overrule the scoped QC-7. I opened `products/tracker17/docs/SDD_open_issues.md`
     § 2.1 for the CTO's seat to scope RT-8 the same way. This answer does not wait on it, because EX-13
     is also § 4 and says the same thing about the page.
  4. *Failure paths.* **Absent:** the saved data removed while the page shows changes nothing, because
     the mode is fixed at start (EX-13). **Stale:** a repair made while the page shows is not read until
     the next start (FDR R-20), and `no-store` means a reload after that start is a fresh load.
     **Refused:** the 403 above. **Empty:** no saved data at all is not this mode, because `main.py`,
     `_serve_claimed`, builds a tracker on an empty state. **Concurrent:** two requests read one fixed
     page and write nothing. A method other than GET or POST also gets the page, including HEAD at
     `/style.css`, so the clause says "a request" and not "a GET".
  - *What would have tipped it.* A new QC-n for the mode was close, and it would hold the test citations
     just as well. I kept QC-7 because the item asks for the answer named there, and because QC-63 needs
     one place to point at (item 3.2).

### 3.2 — QC-63's status rules do not hold on a start on unreadable data

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** The whole of QC-63 is scoped to a tracker serving its saved data, and it points at QC-7 for
  what those addresses answer otherwise. Decided together with item 3.1, which holds the one statement
  of the mode, so the status and the header are not stated twice.
  1. *Whose it is.* The edit lands in `nfdr.md`, and the item cites its occurrence, as 3.1 does.
  2. *The item is narrower than the clause.* It names the 404 and the 202. The 200 clause goes too: a
     confirming `post` on unreadable data is sent to `/`, which answers 503, so no outcome page exists.
     And the item's phrase "with no cache header" has a counterpart worth stating: those addresses
     carry `no-store` on unreadable data (`test_checked_unreadable_reads_share_one_representation`,
     whose targets include `/tasks/1`, `/tasks/1/delete` and `/projects/1`). I scope the whole entry
     rather than each clause because no response of a confirmed action exists in that mode, so the
     `Clear-Site-Data` clause is met by having nothing to reach. No test asserts that header's absence
     on unreadable data, and the scoping is what makes that no gap: `_respond` adds only the page policy.
  3. *Settled record.* SDD RN-69 already reads RT-11's 404 as "reached only while data is served" and
     leaves it as written, so the scoped QC-63 agrees with its trace. No SDD item is owed for RT-11.
  4. *Failure paths.* **Stale:** a 404 kept by a cache from an earlier start, then a start on unreadable
     data. ADR-0012 records that Chromium gives a 404 zero freshness, so this revalidates on the pinned
     browser. I did not test the crossing, and it is left uncovered here because it shows one wrong page
     for one kept address and changes nothing. **Refused:** QC-31 and QC-32 run first, as in 3.1.

### 3.3 — ADR-0011's decision has no exception for the unreadable-data page

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** A superseding record, as the item says, carrying ADR-0011's decision, alternatives and
  consequences whole, with the one qualification added.
  1. *Whose it is.* The record is this seat's. A reader could think an owner's call is hiding here,
     because `product-architecture`'s `SKILL.md` says of a correction, "that is a companion item". Item
     3.3 is that companion item, and answering it binds only the log's consistency.
  2. *The question has a second half the item does not state: three records, or one?* A single new
     record for the mode was the real alternative. It would finally record why the tracker stays up, and
     three successors each repeat a long record for one clause. It loses on three grounds. The template
     says "ONE DECISION, ONE FILE", so one record cannot carry three decisions. It has no status for a
     partial narrowing, so ADR-0011 would stay Accepted, still read as universal, with no pointer to the
     record that narrows it. And the mode fails the significance test as a decision of its own: undoing
     it costs one class, its page and one branch in `main.py`, so it is not hard to reverse. The log has done this
     twice already: ADR-0011 took ADR-0006 and ADR-0012 took ADR-0010, both as changes that were not
     reversals (`nfdr.md` RN-48, RN-50). Item 3.4 and item 3.5 were decided with this one, on the same
     reasoning.
  3. *What moves.* On this reading two sentences need the mode: "What a page shows is a function of the
     tracker state and the page's address" (`adr/0011-…`, § Decision), and the `get` form's 200. While
     the saved data is unreadable there is no tracker state, and the page is fixed by the location given
     at start. The no-session, no-cookie, `post`-only and redirect decisions stand word for word.
  4. *QC-8 does not move, and that was a close call.* QC-8 says `web` "keeps nothing between requests
     except what reaches it through `application`", and `UnreadableSite` holds a location and a host that
     do not come through `application`. I read that as not false: `Site.__init__` also holds `_own_host`,
     fixed at start, in the normal mode, so the clause has always meant what a request brings, and the
     class's docstring says "nothing a request brings". The new record should say the location is fixed
     at start, so that its first sentence stays true. Had the location been able to change during a
     sitting, this would have been a second entry to correct.
  5. *What this leaves for the fold.* Each superseded record's Status line changes and nothing else. The
     index, the QC traces to the old numbers and `nfdr.md` § 4's mention of ADR-0011 move to the new
     record. SDD RT-8, RT-11 and § 12's count of thirteen become stale once the records land, and they
     catch up the way they did for ADR-0013, so nothing is raised for them now.
  6. *Failure paths.* As 3.1. ADR-0011's *Dependence*, the listener's address limit, reads on: an address
     over the limit is refused by the listener before either handler sees it.

### 3.4 — ADR-0012's 404 for a missing identity does not hold on a start on unreadable data

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** A superseding record, carrying ADR-0012 whole, with one qualification: its status and header
  rules hold while the tracker serves its saved data, and otherwise those addresses answer as the record
  that follows ADR-0011 says. Why a superseding record and not one shared record is in 3.3, decided
  together.
  1. *The item holds, and is narrower than the record.* As in 3.2, the 202, the 200 and the 404 are all
     outside the mode, so the qualification goes on the Decision as a whole. The item cites lines 40 to
     42. The sentence starts at line 39: "The address of a deleted task or project, with any query". The
     item's citation is otherwise right, and that small miss changes nothing it asks.
  2. *Settled record.* The Dependence section, Chromium's admission rule, does not move: the rule's
     purpose is keeping a stale confirmation off Back, and on unreadable data no confirmation exists. No
     confirmation page is added, as the item says, and no alternative in the record changes. One new
     alternative is worth recording in the new record: leaving ADR-0012 as it stands and relying on SDD
     § 12 to say that § 4 wins. It loses because the delivery tier reads an Accepted record as fixed.
  3. *Failure paths.* As 3.2.

### 3.5 — ADR-0005's "overwritten by the next save" does not reach a tracker that never saves

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** A superseding record, carrying ADR-0005 whole, with two sentences qualified to agree with SDD
  TO-4 as it now reads. Why a superseding record for what looks like one line of consequences is in 3.3,
  decided together: an Accepted record has no other way to change.
  1. *The item is narrower than the record.* It names the sentence in § Consequences, and that sentence is
     false as it says. § Decision also says "`application` holds the current state", and on unreadable data
     no `application` is built (`main.py`, `_serve_claimed`). SDD RN-72 met the same word and changed "the
     state" to "a readable state", so the new record should follow it. The Decision's read-once and
     one-tracker sentences hold in both modes: `_serve_claimed` holds the location's claim on both paths.
  2. *Settled record.* The sentence to carry is the one SDD TO-4 and FDR R-20 already state: while the
     tracker serves its saved data, a change made by hand is overwritten by the next save; while the saved
     data cannot be read, it holds no state and makes no save, so the change stays and the next start reads
     it. QC-3, QC-52, QC-53 and QC-54 keep their meaning and re-point their traces to the new record. QC-54,
     "read once, at start", holds in both modes, and its test is about the normal one, which is enough
     because `UnreadableSite` holds no reader at all.
  3. *Failure paths.* **Stale:** the repair is read at the next start, and the page does not change until
     then, which the README states. **Concurrent:** a person editing the file while the page shows has no
     second writer to race, because nothing saves. **Refused:** a repair that still breaks a rule gives the
     same page at the next start.

## Left for the owner

None this run.

## Skipped

None this run.

Note on all five items: each slot was empty rather than an angle-bracketed placeholder, and I read that as
unanswered.

## Companions opened

- **products/tracker17/docs/SDD_open_issues.md** — **opened** — companion to `SDD.md`, landed in commit `36e59763d`

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 SDD`
