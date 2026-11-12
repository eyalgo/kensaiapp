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

### 5.1 The design does not yet say whether it takes the four layers and verified fakes
- **Raised by:** PM — 2026-11-05
- **Seat:** cto
- **Tracked by:** none yet — `seeds-from-product-docs` cuts one from the fold
- **What it blocks:** holding tracker17's code to the four-layer default and to one verified fake per port. That default binds a product "only once that SDD has chosen it" (`core/doctrine/engineering/arch_defaults.md:85-87`), and this SDD has not chosen it either way, so neither the dependency rule nor the contract suites bind tracker17 today.
- **Where it shows:** § 3's parts table already draws most of the shape. `domain` holds "no file, no clock, no network"; `application` "states the two contracts it depends on: one for saving and one for the clock"; `persistence` implements saving; `main` is "the composition root". What § 3 does not say: whether the two contracts are `ports` in the sense of `arch_defaults.md` § *The four layers* (`:89-94`), whether `persistence` and the real clock are its `adapters`, and whether `web` is an adapter or sits in `entrypoints`. Nor does it say whether each contract has one fake and one contract suite run against both the real implementation and the fake (`core/doctrine/engineering/testing_doctrine.md` § *A fake is verified against its port's contract*), or what `docs/nfdr.md` § 1.2 *Forbidden imports* gains as a result (`arch_defaults.md:111`). The lean is to take the shape: § 3 already holds the separation, so the cost is naming it plus two contract suites.
- **If a document has to be written:** none beyond `SDD.md`, through `product-sdd`. The NFDR's § 1.2 then follows through `product-nfdr` if the answer moves it.
- **Answer:** Take the shape, with tracker17's five parts standing as the four layers and no part
  added or renamed. The `domain` layer is `domain/` and `application/`: `domain/` holds the rules,
  `application/` holds the flow that applies them, and neither reaches a file, a socket, the console or
  the clock except through what it is handed (NFDR QC-20, QC-21 and QC-42 to QC-45 verify that today).
  The `ports` are the two contracts `application` states, saving (SM-3) and the clock (SM-7). They share
  the `application` package with the flow, which `<CORE>/doctrine/engineering/arch_defaults.md` § The
  four layers permits ("elsewhere each may be its own"). The `adapters` are `persistence/`, which
  implements saving; the real clock, which `main` builds and no part imports (QC-2); and `web/`, the
  browser's adapter, routes included — the one part that touches the socket (QC-43), handed the
  `application` object it calls (SM-6), under QC-16's import rule, which is narrower than the doctrine
  gives an inbound handler and stays. The `entrypoints` layer is `main.py`. The dependency rule already
  holds and is verified, so § 3 gains the naming, no allowed or forbidden set in NFDR § 1.2 moves, and
  each clause there gains the layer it binds and a trace to the doctrine. Each of the two contracts gets
  one fake, written once in one test-support module under `tests/` and never redefined in a test
  module, and one contract suite, run against the real implementation and against the fake, both at the
  integration layer (§ 4 TS-1, TS-2); a test that needs behaviour the fake lacks adds it to the fake,
  with that case in the suite. The one place tracker17's form departs from the Python guide's spelling
  (`<CORE>/doctrine/engineering/languages/python/conventions.md`, "a port is an abstraction in the
  `ports` package") is that the ports sit in `application`: a sixth top-level part would move § 3, QC-1
  and ADR-0001 for no change in the rule, and § 1 counts every added part against the reader. The
  records' side is carried to the Principal Architect on
  `products/tracker17/docs/architecture_open_issues.md` § 2.1. Reasoning:
  `products/tracker17/docs/trail/sdd/self_answer-21.md`.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file.
