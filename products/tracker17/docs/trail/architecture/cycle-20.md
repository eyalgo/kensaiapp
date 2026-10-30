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

> **No producing run wrote this file.** It was opened by hand on 2026-10-30, in the owner's session,
> to carry § 3.1 from the closing record of `tracker17 · tobiishi · 2026-10-29_project-card-commands`.
> `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 § 10's preamble names the card's Test command as `pytest tests/`, and the card now runs both suites through uv
- **Raised by:** Product (the owner) — 2026-10-30, from the developer's closing record of
  `tracker17 · tobiishi · 2026-10-29_project-card-commands`
- **Which record:** `nfdr.md` § 10 *Verification map*, its preamble
- **Tracked by:** none — no seed watches it
- **What it blocks:** nothing is blocked. The preamble tells a reader the suite gate runs one suite,
  while the card that change lands runs two.
- **Where it shows:** the preamble says the stages run "with the project card's `Test command:`;
  typed from the product root, as every row here is, that command is `pytest tests/`", and that
  "SDD § 6 names `pytest tests/e2e/` beside it as the second suite" (`docs/nfdr.md:L633-L634`). The
  change sets the card's `Test command:` to `uv run --locked --project products/tracker17 pytest
  products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest
  products/tracker17/tests/e2e/`, and its `Setup command:` to `uv sync --locked --project …`
  (`system/projects/tracker17/project.md`, branch `2026-10-29_project-card-commands`, commit
  `d4fec9c85`). The developer left the sentence alone because that change's spec forbids a diff
  under the product. Gated that way, the end-to-end suite runs in the gate's empty home, which now
  carries Playwright's browser folder (`<CORE>/tools/empty_home.py`).
- **If a document has to be written:** none — `nfdr.md` itself, by `product-architecture`.
- **Answer:** The preamble follows the card: the suite gate runs both suites, through `uv run`, and
  the layer-5 rows are gated at the suite like the rest. The owner, 2026-10-30, asked for this item
  to be raised for the architect.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
