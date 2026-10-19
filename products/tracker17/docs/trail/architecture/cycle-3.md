# Architecture open issues — tracker17

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

> **No `product-architecture` run wrote this file.** The PM opened it on 2026-10-07, reading the
> product's code against the settled records, with the two items in § 3. It exists because the records
> are settled and had no companion, so without one these changes would reach no seat that can make them.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 The NFDR and two records cite SDD version 4's open questions, and SDD version 6 has closed two of them

> **No `product-architecture` run wrote this item.** The `companion-self-answer` run of 2026-10-07
> raised it while answering § 3, after reading SDD version 6 against `nfdr.md` version 3. Its
> reasoning is `products/tracker17/docs/trail/architecture/self_answer-5.md`, § *Raised on this
> document*.

- **Lands in:** `nfdr.md` `Inputs read:` and RN-15; `adr/0003-no-script-in-any-page.md` and
  `adr/0007-text-counted-once-in-domain-in-code-points.md`, where they cite the SDD's open questions
- **Drafted into the records:** nothing. The records are untouched. The draft: restate RN-15 as one
  open question, the `autofocus` one, and name where the other two closed (SDD RN-35, RN-36). Update
  `Inputs read:` to SDD version 6. Edit neither ADR, because both are append-only and neither
  decision moved. Record in a Review Note that ADR-0007:53-54's open question is answered in SDD
  RN-36, and that ADR-0003:55's "second item" is now the first and only one, narrowed.
- **Rationale:** `nfdr.md:6` reads "SDD Settled (version 4)", and the SDD is at version 6
  (`SDD.md:5`). RN-15 (`nfdr.md:663`) says three SDD Open Questions bear on these records: the line
  break against `maxlength` (ADR-0007), `autofocus` on an element that is not a control (ADR-0003),
  and the port (QC-30). SDD version 6 closed the line-break and port questions and narrowed the
  `autofocus` one (SDD RN-35, RN-36), and its § Open Questions now holds one item. ADR-0007:53-54 calls
  the line-break question "open (SDD § Open Questions, the first item)". ADR-0003:55 cites "§ Open
  Questions, the second item", and that list now holds one item. Neither decision is reversed: RN-36 records
  that each line break counts as one and that `web` turns CR LF into LF, which is what ADR-0007
  decided.
- **If overridden:** with "leave it", RN-15 and `Inputs read:` keep describing an SDD that no longer
  exists, and a reader following ADR-0003's citation finds no second item. With "supersede both
  ADRs", two new records restate unchanged decisions only to move a citation.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-11 *verified by* asks the pointer test to fail on every feature word with no module, which no slice before the last can pass
- **Raised by:** PM — 2026-10-07
- **Which record:** `nfdr.md` QC-11
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** the obligation's verification as worded. SDD § 4 TS-3's table names eleven feature words and `domain/` holds one, `projects.py`; the pointer test checks only the words whose slice has landed (`tests/architecture/test_trace.py:6-7`, `:19`).
- **Where it shows:** `nfdr.md:104-106`, the clause "or a feature word with no module". Proposed: "…or a feature word, among those whose slice has landed, with no module." The SDD's TS-4 states the same clause and is raised on `SDD_open_issues.md` § 5.1.
- **If a document has to be written:** none.
- **Answer:** Confirmed, with an addition. QC-11's *verified by* states SDD § 4 TS-4 as SDD version 6 states it, in both directions: the pointer test fails on a named path that does not exist, a requirement identifier not in `products/tracker17/docs/SRS.md`, a feature word in TS-3's table whose slice has landed and has no module, or a feature word in that table that has its module and is not listed as landed. The PM's wording carries the first direction. The second is the addition: SDD version 6 adopted it (SDD RN-34), and SDD § 12 says that where § 4 and an NFDR entry disagree, § 4 wins. The reverse check reads only TS-3's words, so `domain/state.py`, `domain/refusals.py` and `domain/text.py` are not flagged. `tests/architecture/test_trace.py` has the first direction today and not the second, so the second is a check the next change owes. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-5.md` § 3.1.

### 3.2 The records do not say whether Ruff and mypy are gates, and the product installs both
- **Raised by:** PM — 2026-10-07
- **Which record:** `nfdr.md` § 9 (or an ADR, if the call is a decision)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** a settled answer to whether a change may land with type or lint errors. `pyproject.toml:13` pins `mypy==2.4.0` and `:16` `ruff==0.16.10`, with `[tool.ruff]` at `:19` and `[tool.mypy]` at `:27`; the house default says a product that installs them takes Ruff and mypy (`<CORE>/doctrine/engineering/languages/python/quality_gates.md` § What a product installs, when it installs one), and no line of `nfdr.md`, `SDD.md` or `adr/` names either as a gate. mypy reports three errors on the code as it stands, at `main.py:50` and twice at `web/listener.py:60`, and nothing says whether they block.
- **Where it shows:** `nfdr.md` § 9 names the two Python gates, compile and suite (`nfdr.md:477-479`), and nothing for Ruff or mypy.
- **If a document has to be written:** none — a line in `nfdr.md` saying gate or not, for each tool.
- **Answer:** Both are gates. Three commands, each typed from the product root inside the virtual environment of SDD § 4 RT-4, each passing on exit 0, gated at the suite like the other tree-wide rows of § 10: `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web`, which is QC-1's parts outside `tests/`. mypy is held to those parts because over the whole root it stops on the two `conftest.py` files before checking anything (exit 2). Ruff runs the rule set `pyproject.toml` configures at the version QC-39 pins. Where a Ruff rule contradicts an entry in `nfdr.md`, the entry wins and the site turns that one rule off inline, naming the entry: measured, `BLE001` at `web/routes.py:194` is QC-56's one catch site. A change that moves either pin repairs or turns off what the new version finds, in that change. Measured on 2026-10-07 in a copy of `HEAD`: the format check is clean, `ruff check` reports 8 findings and mypy the 3 errors this item names. Each mypy error is a typing gap, not a fault at run time. The first change after the fold repairs all of them. This is a line in § 9 and three rows in § 10, and no ADR, because dropping a gate is a one-line change. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-5.md` § 3.2.
