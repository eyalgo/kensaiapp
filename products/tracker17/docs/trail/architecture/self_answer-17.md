# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** None. The answer rests on the SDD, the NFDR, ADR-0003, ADR-0007 and the
  product's tests, all in this repository.

## Items worked

### 2.2 — RN-15 and RN-42 still call the EX-6 confirmation open, and SDD version 11 counts it verified

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is right, and RN-15 is owed the change. The item is about this document's own
  consistency with the SDD, so it is this seat's to answer: the edit lands in `nfdr.md` RN-15 and
  commits nothing to anyone outside it.
  - **The draft's facts hold at their source.** `nfdr.md` RN-15 (`:764`) reads "What stays open is
    two cases. The first is the confirmation of SDD § 4 EX-6", and RN-42 (`:1179-1180`) reads "both
    stay: the EX-6 confirmation". SDD version 11 § 11 R-2 (`SDD.md:1325-1333`) names the four tests
    and their pass, 67 passed in `tests/e2e/`, in a fresh clone at `9b05680c7`. SDD § Open Questions
    (`SDD.md:2332-2337`) holds only the assistive-technology item. All four tests are on disk at
    `HEAD` (`tests/e2e/test_moves.py:174`, `:208`, `:321`, `:606`). `git diff --stat 9b05680c7 HEAD
    -- products/tracker17 ':!products/tracker17/docs'` lists one line of `README.md` and no code, at
    `b4810919c`. RN-42 left as a dated record and ADR-0003 left unedited are what RN-35 and RN-42
    already did, for the same reason.
  - **First addition: the browser build.** The draft has the four tests pass "with
    `playwright==1.63.0` and Chromium 153.0.8010.12". R-2 says more carefully that the build is
    "asserted by the run and not inferred from the pin". It is asserted on the full Chromium of that
    install, by `test_history_matrix_revalidates_current_saved_status`. The four focus tests drive
    the headless shell that the same install provides. Copied as drafted, RN-15 would claim more
    about the build the focus tests ran on than the SDD records. The fold writes it R-2's way.
  - **Second addition: the draft answers a smaller question than RN-15 now needs.** SDD version 11
    closed the EX-6 item, which was the first of two in § Open Questions at version 10
    (`git show 6de932f9d:products/tracker17/docs/SDD.md`). With one item left, three more RN-15
    sentences go false: "Two SDD Open Questions bear on these records"; "ADR-0003's `## Traces to`
    cites the list's second item", when there is no second item; and "ADR-0007's *Dependence* calls
    the line-break question open as the list's first item, which now names SDD RN-36". The first
    item is now the assistive-technology question, and it names no RN-36. A reader following
    ADR-0007's citation (`adr/0007-text-counted-once-in-domain-in-code-points.md:54`, "SDD § Open
    Questions, the first item") lands on the wrong question, and RN-15 is the note QC-9's trace tag
    sends them to for the correction (RN-23). The fold restates all three. It points ADR-0007's
    reader at SDD RN-36, which records the line-break closure. Neither record is edited or
    superseded, because neither decision moved and each citation was true on its date.
  - **Failure paths.** *Stale:* the result is a count tied to `9b05680c7`, by RN-42's rule, so it
    does not go false at the next merge. *Refused/absent:* if a later Chromium build fails a focus
    test, RN-15's existing sentence still applies. The passing tests stay as regression triggers,
    and ADR-0003's fallback lands as a superseding record. The fold keeps that sentence. *Empty:* if
    the VoiceOver pass later closes the last open question, the list empties. RN-15 then has no
    list position left to map, which is a later round's change and not this one's.
  - **What would have tipped it.** If R-2 had not recorded the run's own build assertion, the first
    addition would have no basis and the draft would stand as written.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
