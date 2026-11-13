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

> **No producing run wrote this file.** The PM opened it on 2026-11-13, from the architecture
> companion template, to carry item § 3.1 below: a settled NFDR owed a line no item had raised. It
> exists because a settled record has no other way to read open again for `product-architecture`.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 § 9 makes the Behave call `behave` and records no way in
- **Raised by:** PM — 2026-11-13
- **Which record:** `nfdr.md` § 9
- **Tracked by:** `product-development · nemawashi · 2026-11-10_a-changes-behaviour-is-red-before-the-code-and-green-before-the-seal`
- **What it blocks:** the way tracker17's Behave scenarios reach it. The NFDR's § 9 now carries a
  `**Behave way in:**` line below the `**Behave:**` line, taking exactly one of `command`, `server` or
  `browser`, and `product-architecture` picks it once per product, on the first run that finds the
  Behave call `behave` and no way in picked. tracker17's § 9 has the call and not the line, so no way
  in is recorded, and a change's design step, which reads the recorded way in and picks none of its
  own, has nothing to read.
- **Where it shows:** `products/tracker17/docs/nfdr.md` line 720, `**Behave:** behave`, with no
  `Behave way in` line anywhere in the file (`grep -cF 'Behave way in' products/tracker17/docs/nfdr.md`
  → `0`).
- **If a document has to be written:** none; the pick is a line in § 9, made by `product-architecture`
  under its own rule.
- **Answer:** `browser` — § 9 takes the line `**Behave way in:** browser` below `**Behave:** behave`. The browser is tracker17's only interface (SRS C-3: every operation is reached through its pages), and several behaviours the operator sees exist only in a browser: where focus lands, the completion line's accessible description, a double press that never confirms (SDD § 4 RT-9, UXD UX-I2). `server` reaches every request and page but none of those; `command` reaches nothing, since starting the tracker is its only command. The pick adds no dependency: `.behave/pyproject.toml` already pins `playwright==1.65.1`, and it inherits layer 5's platform limit (§ 9, SDD § 4 RT-4). Reasoning in `products/tracker17/docs/trail/architecture/self_answer-30.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
