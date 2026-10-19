# Self-answer report — `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** None. The one external claim near this answer is the HTML standard's line that
  `autofocus` "applies to all elements". The answer does not rest on it: it rests on the measured
  Chromium behaviour. SDD § 11 R-2 records that line as re-read at the source on 2026-10-11
  (`trail/sdd/self_answer-7.md`, Header).

## Items worked

### 3.1 — ADR-0003's Dependence still calls the not-a-control focus case unverified; one form of it is now checked

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** overridden
- **Why:** The item's intent stands: narrow what reads unverified, and leave the no-script decision in
  force. Its method does not. It asks for ADR-0003's Dependence to be narrowed, and that would mean
  editing an Accepted record. `product-architecture` forbids that edit: "Once its Status reads Accepted
  the file is never rewritten; the only line that ever changes in it is that Status line, and only to
  record its supersession" (`skills/principal-architect/.claude/skills/product-architecture/SKILL.md:75`).
  A superseding record is the wrong tool too, because it is for "a reversal or a change of mind"
  (`SKILL.md:87`). The decision did not move, and both the PM's item and SDD RN-41 say so. The
  replacement follows a precedent the owner confirmed. When SDD version 6 closed two Open Questions,
  NFDR RN-23 left ADR-0003 and ADR-0007 unedited "because both are Accepted, neither decision moved",
  and put the current state in NFDR RN-15. QC-34's trace tag points a reader there from ADR-0003's
  `## Binds` (`docs/nfdr.md`, RN-23; `trail/architecture/cycle-4.md` § 2.1).

  **What is actually false now is RN-15, not ADR-0003.** ADR-0003's Dependence
  (`adr/0003-no-script-in-any-page.md:L45-L50`) was true on 2026-10-06. It cites SDD § 11 R-2 and its
  Open Questions, and SDD version 8 has narrowed both (SDD RN-41). So a reader who follows the
  citation lands on the current state. RN-15 does not: it still says the open question is "whether
  Chromium honours `autofocus` on an element that is not a form control (ADR-0003)", and that
  "ADR-0003's cited item is the list's only one". SDD version 8's § Open Questions has two items. The
  first is the confirmation, and the second, the one ADR-0003's `## Traces to` cites, is
  assistive-technology speech.

  **The answer.** The fold changes no record in `adr/`. It revises RN-15 to say four things:
  - Focus and in-view are verified in Chromium on a form control (SDD RN-36), and on a focusable
    element that is not a control (`tabindex="-1"`, per SDD R-2's precision). The evidence is
    `tests/e2e/test_people.py`'s `test_added_markup_name_has_browser_focus_and_accessible_description`
    (from L70, through `assert_added_name_is_focused`, L58-L67), which passed at `641bb58b5` with playwright
    1.63.0 and Chromium 153.0.8010.12 (SDD § 11 R-2).
  - Two cases stay open. The first is the confirmation (SDD § 4 EX-6), which the `status-moves` tests
    settle. The second is assistive technology speaking the description (EX-14). None of ADR-0003's
    three named tests reaches speech, because a computed accessible description does not prove it is
    spoken. SDD R-2 gives that case one VoiceOver pass as its settling path and says no slice
    requires it.
  - Both SDD Open Questions bear on ADR-0003, and its cited "second item" is now the speech one.
  - The two passing tests stay as regression triggers. If any focus test fails, ADR-0003's own
    fallback applies, as a record superseding it.

  QC-34's trace tag already names RN-15, so no trace moves. `Inputs read:` should name SDD version 8.
  That line records what the revision read, which is RN-23's own reading of it.

  **Measured this run.** `git diff --stat 641bb58b5 HEAD -- products/tracker17
  ':!products/tracker17/docs' ':!products/tracker17/README.md'` printed nothing, so the recorded pass
  ran against the code on `main` now. This run ran no suite. The lines the item cites, L58-L78, hold
  what it says: the assertion helper (L58-L67) and the test's focus calls (L70-L78).

  **Failure paths.** *Stale:* a later Chromium could break the verified case. RN-15 should date the
  verification by commit and browser build, and the tests stay as triggers. *Absent:* `status-moves`
  is unbuilt, so the confirmation stays open, and RN-15 says so rather than implying all three are
  done. *Refused:* if the VoiceOver pass is never run, speech stays open, no slice is blocked, and the
  decision stays in force, which is SDD R-2's position. *Concurrent:* does not apply, because a
  verification statement has no second actor.

  **What would have tipped it.** I was close to **confirmed with addition**, because the narrowing
  and the decision staying in force are both taken as asked. What tipped it is the item's named
  change: narrowing the Dependence edits an Accepted record. Doing it as asked is the one move the
  log forbids, so where the change goes is replaced and not just added to. If the owner reads
  ADR-0003's Dependence as needing to carry the narrowing itself, the only append-only way to do
  that is a superseding record that restates the same decision. RN-23 already turned that down for
  this case.

## Left for the owner

None this run.

## Skipped

None this run. The companion's one item, § 3.1, was open, and this run decided it.

## Companions opened

None this run. SDD version 8 already carries this narrowing (SDD RN-41), so no other document is owed
a change by this item.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
