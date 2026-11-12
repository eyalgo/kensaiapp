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

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 Once the SDD names the four layers and the verified fakes, § 1.2 names the layer each clause binds and a new entry binds one fake and one contract suite per port
- **Lands in:** `nfdr.md` § 1.2 (QC-13 to QC-17, their trace tags) and one new `nfdr.md` entry under
  § 1 with its row in § 10. No ADR moves: ADR-0001's five parts and direction of dependence stand as
  written.
- **Drafted into the records:** nothing yet — this run writes no record. The call, for the Principal
  Architect's run to write: `products/tracker17/docs/SDD_open_issues.md` § 5.1 is answered in the CTO's
  seat on 2026-11-12, and the SDD takes `<CORE>/doctrine/engineering/arch_defaults.md` § The four
  layers with its five parts standing as the layers and no part added or renamed. The `domain` layer is
  `domain/` and `application/`. The `ports` are the two contracts `application` states (SDD § 3 SM-3,
  SM-7), sharing the `application` package with the flow. The `adapters` are `persistence/`, the real
  clock `main` builds, and `web/`, the browser's adapter, routes included. `main.py` is the
  `entrypoints` layer. On that answer the records gain two things. QC-13 to QC-17 keep every allowed and
  forbidden set as written, and each names the layer its clause binds, with a trace to `arch_defaults.md`
  § The four layers beside ADR-0001. A new entry binds `<CORE>/doctrine/engineering/testing_doctrine.md`
  § A fake is verified against its port's contract: each of the two ports has one fake, written once in
  one test-support module under `tests/`, in the Python form `<CORE>/doctrine/engineering/testing_python.md`
  § 2 states ("the fakes live in a test-support module such as `tests/fakes.py`"), never redefined in a
  test module; and one contract suite per port, run against the real implementation and against the
  fake, both filed at layer 2 — *verified by:* the two suite modules passing in `pytest tests/`, and a
  layer-6 walk over `tests/` that fails on a class outside the test-support module defining a `save` or
  a `now` method *(traces to: SDD § 4 TS-1, TS-2; the two doctrine sections named)*.
- **Rationale:** the dependency rule the four layers state is already held and verified in tracker17
  (QC-13 to QC-24, QC-42 to QC-45), so the naming costs the records words and moves no obligation. The
  fakes rule is the one obligation the choice adds, and it is not held today: from the product root,
  `grep -rnE '^\s*class \w*(Clock|Saver)\b' tests --include='*.py' | grep -v /e2e/` listed 60 fake
  clock and saver classes across 22 test modules on 2026-11-12, and no contract suite exists. The SDD's
  seat chose the shape because § 3 already drew it and `arch_defaults.md` § The four layers binds a
  product "only once that SDD has chosen it". What the records bind, and how the fakes rule is verified,
  is this seat's call — which is why the slot below is left for it.
- **If overridden:** with no layer names, QC-13 to QC-17 stand as they are and the records describe a
  product outside the four-layer default while its SDD § 3 says it is inside it. With no fakes entry, the
  60 per-module fakes stay unverified and `testing_doctrine.md`'s rule binds tracker17 with nothing in
  § 10 that checks it.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

> **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-11-12 while
> answering `products/tracker17/docs/SDD_open_issues.md` § 5.1 in the CTO's seat, after reading
> `nfdr.md` §§ 1.2, 1.3, 1.4 and 9 against the answer it gave. `product-architecture` has no record of
> writing it. The SDD's answer and its reasoning, `products/tracker17/docs/trail/sdd/self_answer-21.md`,
> land in the commit after the one that carries this item, and `product-sdd` folds the answer on its
> next run. The item is here so that the records follow the SDD whichever of the two folds runs first,
> as they followed SDD § 4 RT-4 to uv through this companion's § 3.1 (NFDR RN-54).

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-1 says no other top-level code part exists, and `.behave/` now holds Python at the root
- **Raised by:** PM — 2026-11-12
- **Which record:** `nfdr.md` § 1.1, QC-1
- **Tracked by:** `product-development · nemawashi · 2026-11-10_a-changes-behaviour-is-red-before-the-code-and-green-before-the-seal`
- **What it blocks:** nothing is blocked. QC-1's layer-6 test still passes, because the source walk
  skips dot-folders; the obligation's words are false where its test is not.
- **Where it shows:** QC-1 reads "No other top-level code part exists." The product root now holds
  `.behave/`, the Behave scenario folder, with Python modules in it
  (`.behave/features/environment.py`, `.behave/features/*_way_in.py`, `.behave/features/steps/*.py`).
- **If a document has to be written:** none. A corrected QC-1 would name `.behave/`, the Behave
  scenario folder, beside `tests/` as test code outside the package unit.
- **Answer:** <the owner fills this in>

### 3.2 QC-19 says no module outside `tests/` imports a third-party module, and `.behave/`'s modules do
- **Raised by:** PM — 2026-11-12
- **Which record:** `nfdr.md` § 1.2, QC-19
- **Tracked by:** `product-development · nemawashi · 2026-11-10_a-changes-behaviour-is-red-before-the-code-and-green-before-the-seal`
- **What it blocks:** nothing is blocked. The import walk does not read `.behave/`, so the test
  passes.
- **Where it shows:** QC-19 reads "No module outside `tests/` imports a third-party module". Inside
  `.behave/`, `features/environment.py:3` imports `behave`, `features/server_way_in.py:5` imports
  `httpx`, and `features/browser_way_in.py:6` imports `playwright`.
- **If a document has to be written:** none. A corrected QC-19 would say "outside `tests/` and
  `.behave/`".
- **Answer:** <the owner fills this in>

### 3.3 QC-43 says no module outside `web/` imports `http.server`, and a `.behave/` step file does
- **Raised by:** PM — 2026-11-12
- **Which record:** `nfdr.md` § 3, QC-43
- **Tracked by:** `product-development · nemawashi · 2026-11-10_a-changes-behaviour-is-red-before-the-code-and-green-before-the-seal`
- **What it blocks:** nothing is blocked. The import walk does not read `.behave/`, so the test
  passes.
- **Where it shows:** QC-43 reads "No module outside `web/` imports `socket`, `socketserver` or
  `http.server`". `.behave/features/steps/page_steps.py:3` imports `BaseHTTPRequestHandler` and
  `ThreadingHTTPServer` from `http.server`, for the browser scenario's local page.
- **If a document has to be written:** none. A corrected QC-43 would exempt `.behave/`, as a
  corrected QC-19 does.
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.
