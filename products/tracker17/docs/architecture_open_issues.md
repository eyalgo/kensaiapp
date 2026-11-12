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

### 2.2 QC-39 says one lock file fixes every test dependency, and § 9 gives layer 7 no tool, while `.behave/` pins its own set and is Behave
- **Lands in:** `nfdr.md` § 2, QC-39, and § 9's layer-7 row. No ADR moves.
- **Drafted into the records:** nothing yet. This run writes no record. The call, for the Principal
  Architect's run to write: QC-39 says the product's own suite has its test dependencies pinned in the root
  `pyproject.toml` and fixed by the root `uv.lock`. It also says `.behave/` pins its own set,
  `behave==1.3.3`, `httpx==0.28.1` and `playwright==1.63.0`, in `.behave/pyproject.toml` at exact
  versions, fixed by `.behave/uv.lock`. Both sets are held to the same bar: the pins test reads both
  files, and `uv lock --check` runs in both folders. § 9's layer-7 row names Behave as its tool and
  `.behave/features/` as where it lives. The row also says that the scenarios there today prove only
  that each way in works and test nothing of tracker17.
- **Rationale:** QC-39 says "one committed lock file, `uv.lock` beside `pyproject.toml`", and that is
  now false: the product holds two. Behave and `httpx` are test dependencies of the product that the
  root `pyproject.toml` does not declare. B-4 guards third-party code run on the operator's machine,
  whichever folder pins it, so the scenario folder's set needs the same bar, not an exemption. §
  9's layer 7 is `testing_doctrine.md`'s "Behavioural contracts — feature scenarios" in the BDD style.
  `.behave/` is that tool, committed in the product, and the row still reads "—" for both tool and
  place. This follows from §§ 3.1 to 3.3, which call `.behave/` test code. § 9 is where the records
  say which layer test code is on. § 9's sentence "Layer 7 has no producer" still holds:
  `<CORE>/doctrine/flow/development_flow.md` names no step that writes scenarios (it has no match for
  "behave" or "scenario"), so that sentence does not change.
- **If overridden:** QC-39 goes on saying the product holds one lock file while it holds two. The
  scenario folder's dependencies stay outside every pins check. § 9 goes on leaving layer 7 empty
  while a layer-7 tool sits at the product root.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

> **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-11-12, in the
> Principal Architect's seat, while it answered §§ 3.1 to 3.3 of this companion. It read every `nfdr.md`
> entry scoped to the whole product against `.behave/`. `product-architecture` has no record of
> writing it. The run measured the two lock files and the scenario folder's pins on disk. It ran Ruff
> over `.behave/` in a disposable clone and found that QC-62 holds there. The reasoning is in
> `products/tracker17/docs/trail/architecture/self_answer-27.md`.

### 2.3 Seven entries that say "outside `tests/`" still reach `.behave/` in their words, and the walk behind them now skips it by name
- **Lands in:** `nfdr.md` QC-2, QC-3, QC-4, QC-37, QC-42, QC-45 and QC-61. No ADR moves.
- **Drafted into the records:** nothing yet. The seven entries are settled and change only on an
  answer. The call, for the Principal Architect's next run to write: each of the seven reads
  "outside `tests/` and `.behave/`" where it now reads "outside `tests/`", or names `.behave/` beside
  `tests/` where it names what it does not bind, as QC-19's first clause and QC-43 already do.
  QC-42's walk then runs "outside `persistence/`, `tests/` and `.behave/`".
- **Rationale:** version 25 has the source walk skip `tests/`, `.behave/` and `.venv/` by name (QC-1,
  on companion § 3.1's answer). Each of the seven is checked by that walk, and each says "outside
  `tests/`" or binds the whole product, so its words reach `.behave/` and its check does not. Six
  hold there today: no module under `.behave/features/` imports `pickle`, `marshal`, `shelve` or a
  tracker part, opens a file for writing, calls `print`, reads `sys.platform` or `os.name`, or names
  a contract as a base. **QC-4 does not.** Its words say every exception class "in the product"
  derives from the one base in `errors.py`, and `.behave/features/browser_way_in.py:17` defines
  `ChromiumMissing(AssertionError)`. The `companion-self-answer` run behind cycle 23 found that
  QC-37, QC-45, QC-59 and QC-61 hold there, and did not read QC-4. `.behave/` is test code (QC-1),
  and the answers to §§ 3.2 and 3.3 exempted it as test code wherever the question came up. So the draft gives the
  seven the same scope, with nothing walked that is not bound. Answering "override" with a walk of
  `.behave/` per entry, as QC-19 now has for its second clause, keeps the words and adds seven checks
  over test code. Neither choice moves an obligation on the tracker.
- **If overridden:** each of the seven gains a walk of `.behave/` in its tail, which a change to
  `tests/conftest.py` realizes, and QC-4's walk fails until `ChromiumMissing` derives from the base
  in `errors.py`, a folder outside `.behave/`'s own Python setup. With no answer, the seven entries'
  words go on binding a folder no check reads, which is how QC-1's words went false while its test
  passed.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write these records

None.
