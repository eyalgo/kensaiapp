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

### 2.1 QC-39 was rewritten by a delivery-tier commit, with no Review Note and no new version

> A `companion-self-answer` run raised this item on 2026-10-29 while answering the PM's item on
> QC-40. It found QC-39's text changed after version 19 settled, by two Developer commits,
> `79a743286` and `5eb5ec557`, with nothing in the NFDR recording the change. Its reasoning is in
> `docs/trail/architecture/self_answer-22.md`. The `product-architecture` run that wrote version 20
> drafted the answer below into the records.

- **Lands in:** `nfdr.md` QC-39, and a Review Note
- **Drafted into the records:** RN-57 in `nfdr.md`, version 20. It records QC-39's move from
  "starts unmet" to "is met", names the two commits, and checks the new text against the tree at
  `1bfb63f7f`: `uv.lock` sits beside `pyproject.toml`, `tests/architecture/test_pins.py:44` holds the
  test the entry names, and in a disposable clone `uv lock --check`, its `--offline` form and
  `uv sync --locked` exited 0 and the pins tests passed. QC-39's words stay as the Developer wrote
  them, because every fact checked holds.
- **Rationale:** The constraint set is revised in place only under provenance, and nothing
  downstream edits it: a discrepancy found during a change comes back here to be recorded. Version
  19's header and RN-54 said QC-39 starts unmet, and the entry said it is met, with no note between
  them, so a cold reader could not tell the change was authorized or who checked it. No fact in the
  entry is false, so this is a provenance gap, not a correction, and a note closes it.
- **If overridden:** RN-57 is revised to say what you choose instead — for example that QC-39 goes
  back to its version-19 text until a `product-architecture` run moves it. Either way the entry's
  obligation and checks do not move. Leaving the Developer's edit with no note keeps the precedent
  that a delivery-tier run edits the constraint set directly.
- **Confirm or override:** confirm, with an addition. RN-57 also says why the edit happened and
  what still lets it recur. The Developer acted on `development-implementation`'s rule that a
  correction line naming a file tracked on the branch is mislabelled. For a product kept in the same
  repository, that rule puts this document in a delivery change's reach, against the line before it
  in the same skill. The contradiction is filed as a finding against the skill
  (`docs/findings/2026-10-29_the-developer-skill-puts-a-same-repo-product-record-in-reach.md` at the
  instance root) and is not this document's to settle. Until it is settled, no check refuses a
  delivery commit that edits this document, and the next `product-architecture` run's diff of its
  inputs is what finds one. QC-39's words, obligation, checks and trace stay as RN-57 has them.
  Reasoning: `docs/trail/architecture/self_answer-23.md`.

## 3. Raised from downstream — an item from a seat that did not write these records

None.
