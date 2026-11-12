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

None.

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
