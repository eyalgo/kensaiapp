# Change Text — the lock file is `uv.lock`, and the pin test reads it

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing

---

## Text

### The note above the suite's test-tool declarations

**The note as a person reads it, opening the product's settings to see or change a test-tool pin**

The note is replaced in full by the eight lines below. Each line is exact in its characters, including
the leading `# ` and the line breaks, and no line is longer than 100 columns.

> ```
> # The `dev` group in `[dependency-groups]` pins the tools the product's tests and checks use, so
> # that they run from the product's own environment rather than from whatever the machine happens
> # to have. Each pin is exact (`==`), not a floor (`>=`), because a later install must not change
> # behaviour without a diff (FDR PD-7, SDD § 4 RT-4). `uv.lock`, beside this file, locks these pins
> # with everything they pull in. A change to a pin in this group is followed by `uv lock`, so that
> # `uv.lock` moves in the same change. `uv sync --locked` refuses a `uv.lock` that is out of step
> # with this group. `uv run <tool>` resolves these pins. `uvx <tool>` deliberately does not, and
> # reaches past both this group and `requires-python`.
> ```

When the person sees it: a developer reading or editing the test-tool pins learns that each pin is exact
and why, which file locks the pins with everything they pull in, that changing a pin means re-locking in
the same change, and which way of running a tool uses these pins.

---

## Wording decisions

- **The lock file is named as `uv.lock`, "beside this file", where the note named the pip lock file.** The
  request and CP-660 ask for this. "Beside this file" tells a cold reader where to find it, which is SDD
  § 4 RT-4's placement ("`uv.lock`, beside `pyproject.toml`").
- **The opening became a whole sentence about the group, where it said "The tools this file configures
  below".** The old opening had no verb. It also claimed every pinned tool is configured by the file,
  which is not true of Playwright: the file has no settings table for it. The smaller true claim is that
  the group pins the tools the tests and checks use. "Below" also went, because it locates by position.
  The group is named by its table instead.
- **"Host" became "machine".** "Host" also means a network address, and the note means the computer the
  tools run on.
- **Sentences that joined two claims were split:** the colon after "Exact pins, not floors", the ", and"
  before the lock-file claim, and the semicolon between `uv run` and `uvx`. The writing bar requires one
  claim per sentence (`system/doctrine/writing_bar.md` § 1.2, rule 7).
- **"Not floors" now shows what it means: "exact (`==`), not a floor (`>=`)".** The writing bar asks for
  no label the reader would have to decode (§ 1.2, rule 6).
- **"(PD-7; SDD § 4 RT-4)" became "(FDR PD-7, SDD § 4 RT-4)".** The citation now names the document
  that holds PD-7, so the reader knows which file to open. The comma replaces a semicolon in a two-item
  list.
- **Two sentences were added for a situation the old note never covered: someone editing a pin.** The
  person who opens these declarations is usually about to change one. With `uv.lock`, a pin edit that is
  not re-locked is refused, so the note tells them so. Both claims come from SDD § 4 RT-4: "A change to
  `pyproject.toml` is followed by `uv lock`, so the lock file moves in the same change", and "The
  `--locked` flag refuses a lock file out of step with `pyproject.toml`". The first claim is narrowed
  from the whole file to "a pin in this group", which is what the note covers.
- **The `uv run` and `uvx` claims are kept as the note stated them.** This change does not touch them,
  and SDD § 4 RT-4 states that every suite command is typed through `uv run`.
- **Which standard governs.** The product's content standard governs no code comment
  (`products/tracker17/docs/CONTENT.md` § Scope, "It governs no code comment and no test name"), so
  the instance writing bar governs the note alone. The note was still checked against the standard's
  banned words and banned punctuation (§ Terminology, "Banned in anything a person sees", and § Grammar
  and mechanics, "Banned punctuation"), in every inflection. Nothing was found once "below" and "host"
  were gone. The product has no vocabulary check that reads this note: the banned names in its
  architecture tests are import names, not words.
- **Line breaks are fixed in the text** so the person placing it chooses nothing. Each line is at most
  100 columns, the line length the product's settings give its formatter.

---

## Findings for the Content Manager

None. The content standard leaves code comments out of its scope on purpose (§ Scope), so the note shows
no gap in it.
