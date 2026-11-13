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

> **`product-sdd` did not write this file.** A `product-architecture` run opened it on 2026-11-13, in the
> Principal Architect's seat, while folding the owner's answer to
> `products/tracker17/docs/architecture_open_issues.md` § 3.1, which asked that the SDD's lines
> naming the old Playwright pin be raised here. That answer is at
> `products/tracker17/docs/trail/architecture/cycle-25.md` § 3.1.

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

### 5.1 § 4 RT-4 names `playwright==1.63.0`, and the pin is now `playwright==1.65.1`
- **Raised by:** Principal Architect — 2026-11-13
- **Seat:** cto
- **Tracked by:** no seed watches it. It comes from the owner's answer to the architecture
  companion's § 3.1, `products/tracker17/docs/trail/architecture/cycle-25.md` § 3.1.
- **What it blocks:** nothing is blocked. NFDR version 27 names the new pin in QC-39, QC-40, QC-63 and
  § 9, and § 9's platform line cites RT-4's list. § 12 has § 4 win where the two disagree, so until
  RT-4 moves, the SDD and the NFDR name different pins for the same suite.
- **Where it shows:** `SDD.md:383-385`, § 4 RT-4, reads "For the pin in `pyproject.toml`,
  `playwright==1.63.0`, that library's documentation lists "Debian 12 / 13, Ubuntu 22.04 / 24.04 /
  26.04 (x86-64 or arm64)" (https://playwright.dev/python/docs/intro, "System requirements", read
  2026-10-08)". On `main`, `pyproject.toml:17` and `.behave/pyproject.toml:8` read
  `playwright==1.65.1`, both `uv.lock` files lock it, and it installs Chromium 158.0.8127.18
  (`tests/e2e/test_moves.py:515`, `PINNED_BROWSER`). The pin moved at `c39e74abe`. RT-4's list does
  not change: Playwright's `docs/src/intro-python.md` at the driver commit 1.65.1 bundles
  (`a1f35e1955976e84411f9c10358228a80b763ebe`, "chore: mark v1.65.0") lists the same Debian and
  Ubuntu releases, read 2026-11-13. So the pin and the date the list was read move, and the list
  stands.
- **What it may leave alone:** the other SDD lines naming 1.63.0 or 153.0.8010.12 are dated evidence,
  each a run at the commit it names: § 11 R-2 (`SDD.md:1602`, `:1614-1616`) and the Review Notes at
  `:2605-2607`, `:2940`, `:3008` and `:3386`. They were true on their dates. NFDR RN-72 treats its
  own dated notes the same way.
- **If a document has to be written:** none. `product-sdd` folds the RT-4 sentence.
- **Answer:** Fold as the item says. RT-4's sentence names `playwright==1.65.1` and the date its platform list was read (2026-11-13, from the driver commit 1.65.1 bundles). The list itself stands. The dated evidence lines (§ 11 R-2 and the Review Notes it names) are left as they are. Owner, 2026-11-13: the pin moves (the architecture companion's § 3.1, answer (a)).

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
