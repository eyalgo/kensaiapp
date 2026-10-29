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
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

> **No producing run wrote this file.** It was opened by hand on 2026-10-29, in the owner's session,
> to carry § 5.1, the owner's call. `product-sdd` has no record of writing it.

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

### 5.1 The test suite's environment is made with uv, not with `venv` and the bundled installer
- **Raised by:** Product (the owner) — 2026-10-29
- **Seat:** cto
- **Tracked by:** none — the owner's top-down call; no seed watches it
- **What it blocks:** nothing waits on it, but a run that reaches for the machine's own Python finds
  no browser-driving library and cannot run `pytest tests/e2e/`. On 2026-10-29 the run closing
  `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` stopped on
  `ModuleNotFoundError: No module named 'playwright'` for exactly that reason. In a fresh clone,
  `uv sync` in `products/tracker17` installed the `dev` group `pyproject.toml` already declares,
  Playwright included, and `uv run pytest tests/e2e/` gave `121 passed`.
- **Where it shows:** § 4 RT-4 says the test dependencies "are installed with the installer that
  ships with Python, into a virtual environment made with Python's own `venv` module"
  (`docs/SDD.md:L297-L300`), and § 6's suite commands are "typed from the product root, inside the
  virtual environment the setup instructions make" (`docs/SDD.md:L767-L768`). Downstream, ADR-0002
  (`docs/adr/0002-standard-library-only-no-web-framework.md:L22-L26`), `docs/nfdr.md:L597` and
  `docs/nfdr.md:L769`, and the README's § on running the tests, follow RT-4.
- **If a document has to be written:** `SDD.md` itself, by `product-sdd`; then the records below it
  that follow RT-4, each by its own producer as the chain walks down.
- **Answer:** Yes — switch to uv. The owner, 2026-10-29: "can we switch to uv instead of python?",
  then "yes" to making uv tracker17's way to run its tests, top-down through the definition chain.
  What the lock file is and how the suite commands read under uv are the CTO's to settle in RT-4.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
