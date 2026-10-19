# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-11
- **Sources re-read:** one source outside this repository, read at the source on 2026-10-11, because
  the narrowed R-2 keeps resting on it: https://html.spec.whatwg.org/multipage/interaction.html, "The
  autofocus attribute" — "The autofocus attribute applies to all elements, not just to form
  controls"; the flush step returns when "topDocument has non-null target element"; the section says
  nothing about scrolling the element into view and nothing about assistive technology, and lets the
  user agent "optionally return" where the user has indicated they do not want focus changed. So the
  standard promises focus and no more, and what the item cites as verified — in view, described — is
  Chromium's behaviour as measured, not the standard's. The in-repo measurement the answer rests on was
  re-made rather than read off the record: `git archive 7653f25c8 products/tracker17` into a scratch
  folder, a scratch `venv` with `tests/requirements.txt` installed (playwright 1.63.0, the pin), and
  `pytest tests/e2e/` there → `18 passed`, `test_people.py` alone → `6 passed`, in Chromium
  153.0.8010.12 (`browser.version`). The product's main checkout ran nothing. `git diff --stat
  641bb58b5 7653f25c8 -- products/tracker17 ':!products/tracker17/docs'` lists only `README.md` —
  two sentences of its Status section, landed at `7653f25c8` while this run was open, which
  `tests/integration/test_start.py:159-160` reads for its headings and no end-to-end test reads — so
  the code the suite drives is the code the PM measured. Read in-repo besides `SDD.md` whole and the
  companion: `SRS.md` NFR-13;
  `UXD.md` UX-I4, UX-A5; `web/pages.py:312-330, 395-410`; `tests/e2e/test_people.py` whole;
  `tests/e2e/conftest.py:133-141`; `nfdr.md` RN-15, RN-25; `adr/0003-no-script-in-any-page.md`;
  `architecture_open_issues.md` § 3.1; the seed's checklist,
  `system/projects/tracker17/journey/nemawashi/2026-10-07_tasks-in-a-project/seed.md:86-92`.

The companion held one open item, § 5.1, `Seat: cto`, and the invocation listed none, so this run
worked it. It cites an occurrence — a passing test on `main` — and asks for a correction of a
statement now false, not a widening, so § *A widening item waits until it occurs* does not send it
back.

## Items worked

### 5.1 — § 11 R-2 and § Open Questions still call the not-a-control focus case unverified; one form of it is now checked

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** Answered from scratch: the item asks for a narrowing and hands no draft of it, so there was
  nothing to confirm or overturn. One question, one seat; it did not split.

  *Seat (check 1).* Every edit lands in a CTO row of § *Who decides what*: § 11 R-2, § Open
  Questions, and the one sentence of § 6 S-2's *Why here in the order* that cites R-2. The answer
  binds nothing outside the document — no person, no party, no risk the owner carries — and the
  experience decision it touches (no script, § 4 EX-2) is left exactly as the CDO decided it. No
  ground I cannot see; mine, in the owner's seat. The downstream record with the same sentence,
  ADR-0003's *Dependence*, is the Principal Architect's and already carries its own item,
  `architecture_open_issues.md` § 3.1 (commit `fae779439`), still at its placeholder; my finding is the
  same narrowing, so I neither appended a near-duplicate nor revised it.

  *The question holds (check 2), and the answer.* Every citation in the item is as stated: R-2 is
  `SDD.md:1154-1164`, the Open Question `SDD.md:1769-1774`, the assertions `test_people.py:58-78`.
  The verified element is a `span` carrying `tabindex="-1" autofocus aria-describedby`
  (`web/pages.py:316`), focused, in the viewport, described by the completion line, with the next
  Tab landing on its Remove and `tabIndex == -1` — which is RT-9's "takes focus without becoming a
  stop in the Tab order" exactly. The item names one form; the same page verifies a second not-a-control
  element, the People heading after a removal (`pages.py:404`, `test_people.py:124-126`), and the
  answer names both. I kept the item's two unverified cases and sharpened each. The confirmation case
  is EX-6's whole shape — focus on the sentence, the double press, back-out — and `status-moves`
  owns it; the SDD already says so. Assistive-technology speech: Playwright's
  `to_have_accessible_description` reads the accessibility tree, so the test proves the line is
  *exposed*, not *spoken*; no slice tests a screen reader, and leaving an open question with no
  settling path is a hole, so the answer gives R-2 the form R-8 and R-9 already use — one named run
  would settle it, and no slice requires it. I named the run as VoiceOver on macOS because RT-3 makes
  macOS the owner's machine. I added the precision the item lacked, `tabindex="-1"`: the spec makes
  `autofocus` apply to all elements, but only a focusable one takes focus, and a reader narrowing
  R-2 from the item's words alone would state a wider claim than the test makes. The S-2 sentence is
  a consequence of the narrowing, not a separate change, so it rides in this answer rather than as a
  raised item: once R-2 no longer "leaves" the case unverified, "the case § 11 R-2 leaves unverified"
  reads false. § 7's `validates` row describes what the test shows and stays true.

  *Nothing settled moves (check 3).* UXD UX-A5 asks for status messages "announced to assistive
  technology without moving focus" and EX-14's mechanism is the accessible description; the answer
  leaves both as they stand and says only what is and is not proven about them. SRS NFR-13 names
  Chromium-based browsers and Chromium for the end-to-end layer, so "verified in Chromium" is verified
  in the supported family. RN-36 already records R-2 keeping a passing test among its triggers because
  a release could change the behaviour; the answer applies the same reasoning to these two tests
  rather than inventing a different one. The spec, re-read today (Header), still says what RT-9 and
  R-2 quote. NFDR RN-15 says the question "settles in the build, not here", which is what is
  happening, so it is not false. No earlier answer of this run bears on it; there was one item.

  *Failure paths (check 4).* *Empty*: the first add on an empty list is the test's first assertion
  (position 1). *Absent*: no assistive technology running — the description is in the tree
  regardless, and the unproven half is named rather than assumed. *Stale*: a Chromium release moves —
  both suites run on every slice (§ 4 TS-1), so the two passing tests are the regression signal, and
  R-2 keeps them; and the build the suite drives is the pinned library's (Chromium 153.0.8010.12
  today) while the operator's is current stable Chrome (NFR-13), a divergence that shows only in the
  owner's run-through — named in the answer as a bound. *Concurrent*: a stale remove from a second tab
  lands focus on the heading with the reason, tested at `test_people.py:142-166`. *Refused*: the
  standard lets a user agent skip `autofocus` where the user has said they do not want focus moved;
  that is a browser preference the design cannot override and the operator's own, outside R-2 as every
  browser preference is. I was close to writing AT speech out of § Open Questions entirely, as a risk
  only; what kept it in is that the Open Question's own text names it ("reads its description") and
  the item asks the two places to be narrowed, not one closed.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
