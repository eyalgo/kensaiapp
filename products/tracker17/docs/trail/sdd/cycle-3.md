# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.

> **No `product-sdd` run wrote this file.** The PM opened it on 2026-10-07, reading the product's code
> against the settled SDD, with the three items in § 5. It exists because the SDD is settled and had no
> companion, so without one these changes would reach no seat that can make them.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

None.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 § 4 TS-4 asks the pointer test to fail on every feature word with no module, which no slice before the last can pass
- **Raised by:** PM — 2026-10-07
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** the pointer test as TS-4 words it. The TS-3 table names eleven feature words and `products/tracker17/domain/` holds one of them, `projects.py`; the test therefore checks only the words whose slice has landed (`tests/architecture/test_trace.py:6-7`, `LANDED_FEATURE_WORDS = ["projects"]` at `:19`), which TS-4 does not say.
- **Where it shows:** § 4 TS-4, the clause "or when a feature word in the table below has no module". Proposed wording: "…or when a feature word whose slice has landed has no module; each slice that delivers a feature adds its word to the test."
- **If a document has to be written:** none — the SDD's own sentence. The NFDR states the same clause in QC-11 *verified by*, raised on `architecture_open_issues.md`.
- **Answer:** Confirmed, with one addition. TS-4's third clause reads: "…or when a feature word whose slice has landed has no module, or when a feature word in the table has its module but is not listed as landed; each slice that delivers a feature adds its word to the test." The middle clause is the addition: without it a slice can land `domain/<word>.py` and forget the list, and that feature's pointers go unchecked with nothing failing — the stale-pointer case § 11 R-6 exists to catch. The test today has the first direction (`tests/architecture/test_trace.py`, `test_each_landed_feature_word_has_its_domain_module`) and not the reverse, so the fold leaves the test owed that one check. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-5.md` § 5.1.

### 5.2 The port of the fixed address is now chosen, and § Open Questions still asks for it
- **Raised by:** PM — 2026-10-07
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** nothing runs wrong; the SDD reads as undecided on a fact the code has fixed. `main.py:20` reads `ADDRESS = ("127.0.0.1", 8017)`.
- **Where it shows:** § Open Questions, the item "Which port the fixed address uses" (`SDD.md:1590-1591`), and § 4 RT-5 (`SDD.md:283-285`), which names one constant and no port. Proposed: remove the open question and record the port as `8017` in RT-5.
- **If a document has to be written:** none.
- **Answer:** Confirmed, with one addition: RT-5 records the whole address, `127.0.0.1:8017`, not the port alone. RT-5 says "one loopback address" and there is more than one; `main.py:20` fixes both halves in the one constant, `ADDRESS = ("127.0.0.1", 8017)`, and `tests/unit/test_address.py` pins both (a loopback host, port 8017). § Open Questions drops the item. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-5.md` § 5.2.

### 5.3 Two Chromium questions in § Open Questions are answered by the end-to-end tests that now pass
- **Raised by:** PM — 2026-10-07
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** nothing runs wrong; § Open Questions asks what `tests/e2e/test_first_project.py` now checks. `test_a_description_of_4000_characters_with_line_breaks_is_saved_whole` (`:108`) answers how Chromium counts a line break against `maxlength`, and `test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description` (`:94`) answers `autofocus` for a form control. Both pass: `pytest tests/e2e/` was recorded at 9 passed, exit 0, at commit `691edf98b`, the code now on `main`.
- **Where it shows:** § Open Questions, the first item (`SDD.md:1582-1584`), and the form-control half of the second (`SDD.md:1586-1589`). Proposed: remove the first, and narrow the second to an element that is not a form control, which a later slice's focus tests settle.
- **If a document has to be written:** none.
- **Answer:** Confirmed, with one addition. Remove the first open question and narrow the second to an element that is not a form control, as proposed. The addition is what the SDD says when it records the first as closed: the test observes that the field counted each of fifty line breaks as one of the 4,000 and that the value was saved whole; it does not observe whether Chromium sent CR LF, because `web/routes.py:84` turns CR LF and a lone CR into LF before the value reaches `application` (`tests/integration/test_routes.py:228` checks that). The question closes because RT-10's design no longer turns on its answer, not because CR LF was seen on the wire, and the SDD should say so rather than leave a reader to infer an observation. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-5.md` § 5.3.
