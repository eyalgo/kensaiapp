# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. The answer rests on SDD version 6, the two ADRs, `nfdr.md` version 4 and
  the product's code, all in this repository. ADR-0003's *Dependence* quotes the HTML standard on
  `autofocus`, but this answer does not rely on that quote, so the run did not re-read it.

The companion arrived with one open item, § 2.1, and this run answered it. §§ 1 and 3 hold no items.

## Items worked

### 2.1 — RN-15 names the one SDD open question left, and says where SDD version 6 closed the other two

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft's facts hold, and so does its decision to leave both ADRs alone. One sentence
  of its reasoning does not.
  - **Whose call.** The change lands in `nfdr.md`, which this seat owns. It binds only how the
    records agree with each other: no person, no money, no risk someone carries. So the decision is
    this run's, in the owner's seat.
  - **The facts, checked at their source.** SDD version 6's § Open Questions holds one item, the
    `autofocus` question on an element that is not a form control (`SDD.md:1660-1665`). SDD RN-35
    closes the port question with `127.0.0.1:8017` (`SDD.md:1607-1618`), and `main.py:20` reads
    `ADDRESS = ("127.0.0.1", 8017)`. SDD RN-36 closes the line-break question (`SDD.md:1619-1643`),
    and `web/routes.py:82` defines `_line_feeds`, which `:178-179` apply to the submitted fields.
    RN-15 (`nfdr.md:687-699`) states all of this correctly. Both ADRs cite the list as it stood at
    SDD version 4. ADR-0007's *Dependence* calls the line-break question open, as "the first item".
    ADR-0003's `## Traces to` cites "§ Open Questions, the second item". Neither decision moved, so
    leaving both Accepted records unedited and unsuperseded is right. The loader's rule is that an
    accepted record you edit is a record you have destroyed. A superseding record would restate an
    unchanged decision only to move a citation.
  - **The sentence that does not hold.** RN-15 says "this note is where a reader following either
    citation finds the answer", and the companion item makes the same claim. It is not true. Each
    ADR's citation leads into SDD § Open Questions, not into the NFDR, and nothing on that path
    names RN-15. The true reason no ADR needs a change is the SDD itself:
    - ADR-0003's cited item is now the list's only one, so the citation still lands on its
      question.
    - ADR-0007's citation lands on that same item, which names SDD RN-36, and RN-36 records the
      line-break question closing.

    The one route from an ADR into the NFDR is its `## Binds` line: ADR-0003 binds QC-34, and
    ADR-0007 binds QC-9. Neither entry points at RN-15. QC-9's trace ends "see RN-19"
    (`nfdr.md:94`), and QC-34's trace carries no note at all (`nfdr.md:257`). The addition has two
    parts. First, RN-15 and RN-23 give the true reason. Second, QC-9's and QC-34's trace tags
    gain "see RN-15", which makes the route RN-15 describes real.
  - **Failure paths.** *Stale:* RN-15 goes stale again when the SDD closes its last question. That
    is the next revision's work, and RN-15 already says how it lands: an answer that contradicts a
    record lands as a superseding record. *Empty:* if the SDD's list empties, RN-15 says no open
    question bears on the records. Nothing here pre-empts that. The other three cases (absent,
    concurrent, refused) do not arise for a note about citations.
  - **One observation, not raised.** The product already puts `autofocus` on a heading, which is not
    a form control (`web/pages.py:184`), and `tests/e2e/test_first_project.py:69` asserts that focus
    lands on the `H1`. So the focus half of the SDD's last question is already exercised. Bringing
    the element into view and reading its description are still not asserted, so the question and
    RN-15's "settles in the build" both still hold. Narrowing the question is the SDD's job and is
    worth no cycle of its own. This run did not run the end-to-end suite.
  - **What would have tipped it.** A plain *confirmed*, if any route from either ADR reached RN-15.
    An *overridden*, if the SDD had not recorded the closure itself, because then a superseding
    record would have been the only way to answer a stale citation.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
