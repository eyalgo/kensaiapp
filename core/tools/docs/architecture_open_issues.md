# Architecture open issues — tools

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

### 3.1 ADR-0001 says skills' commands still run the first `python3` on `PATH`, and they no longer do
- **Raised by:** PM — 2026-10-27
- **Which record:** `adr/0001-lock-the-tools-suite-with-uv.md` § Consequences, lines 66–68
- **What it blocks:** nothing is blocked; the record states as current a consequence that is now false.
- **Where it shows:** line 66–67 reads "What stays as it was: the `python3` commands skills give an
  agent still run the `python3` that `PATH` finds first … This record does not move them." Every such
  command under `skills/` now starts `"<CORE>/tools/locked_python.sh"`: `git grep -nw python3 --
  'skills/*.md'` prints only `readme-status/prompts/thin.md:93` (a sentence quoted for a reader) and
  the three `#!/usr/bin/env python3` shebangs in `tobiishi-seal/SKILL.md`, and `git grep -nF
  'locked_python.sh' -- 'skills/*.md' | wc -l` prints 64. The same paragraph's other two meanings
  still hold: a bare `pytest` runs on the machine's pytest, and what a launch hands the processes it
  starts is unchanged.
- **If a document has to be written:** none — an amending note on ADR-0001, or a superseding record,
  is the record owner's choice.
- **Answer:** <the owner fills this in>

### 3.2 ADR-0001's "exactly two dependencies" holds again, and this item closes with no edit to the record
- **Raised by:** Product Owner — 2026-11-10; revised by PM — 2026-11-12
- **Which record:** `adr/0001-lock-the-tools-suite-with-uv.md` § Decision, lines 28–30
- **What it blocks:** nothing is blocked, and nothing in the record is now false.
- **Where it shows:** § Decision reads "declares exactly two dependencies under
  `[project.dependencies]`, pytest and pytest-xdist, each pinned to an exact version with `==`".
  For a while the instance root's `pyproject.toml` pinned a third, `behave==1.3.3`, for
  `core/tools/test_behave_starter.py`. It pins two again: `pytest==9.0.3` and `pytest-xdist==3.8.0`
  (`pyproject.toml` lines 5–8). Behave is now pinned in the Behave starter's own
  `core/templates/behave-starter/pyproject.toml`, beside its own `uv.lock`, so the record reads true
  as written.
- **If a document has to be written:** none. The item closes on the next `product-architecture` run,
  with ADR-0001 left as it stands.
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.
