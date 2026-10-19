# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. No answer rests on a source outside this repository. Both answers rest
  on the SDD and the product's code, plus three commands run on a copy of `HEAD`
  (`git archive HEAD products/tracker17`), never on the main checkout:
  - `uvx ruff@0.16.10 format --check .` printed "100 files already formatted" and exited 0.
  - `uvx ruff@0.16.10 check .` printed "Found 8 errors" and exited 1. The findings are
    `persistence/saved_data.py:91` TRY004, `tests/integration/test_listener.py:117` RUF059,
    `tests/integration/test_pages.py:92` FURB188, `tests/timed_run.py:23-26` RUF100 four times, and
    `web/routes.py:194` BLE001.
  - `uvx --from mypy==2.4.0 mypy main.py errors.py domain application persistence web` printed
    "Found 3 errors in 2 files (checked 16 source files)": `web/listener.py:60` attr-defined and
    str-bytes-safe, and `main.py:50` str-bytes-safe. Over `.`, mypy stopped on "Duplicate module
    named "conftest"" with exit 2, before checking anything.

The companion arrived with two open items, both under § 3 *Raised from downstream*. Both carry an
**Answer** slot, and both were answered. While reading SDD version 6 against `nfdr.md` version 3,
this run also raised one item, § 2.1.

## Items worked

### 3.1 — QC-11 *verified by* asks the pointer test to fail on every feature word with no module, which no slice before the last can pass

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The PM's proposed wording is right, and the item's own reason holds. SDD § 4 TS-3's table
  names eleven feature words, `domain/` holds one of them (`projects.py`), and
  `tests/architecture/test_trace.py:19` lists only `["projects"]` as landed. A test that fails on
  every word with no module cannot pass before the last slice. This is a correction, not a widening:
  the clause as written cannot be met. The addition is the reverse direction. SDD version 6 has TS-4
  also fail when a word in the table has its module and is not listed as landed (`SDD.md:430-434`;
  SDD RN-34). SDD § 12 says that where a § 4 condition and an `nfdr.md` entry disagree, the § 4
  statement wins and the entry is re-derived (`SDD.md:1207-1209`). So QC-11 takes TS-4's clause in
  both directions, not the one direction the PM proposed. Failure paths: the reverse check reads
  only the table's words, so `domain/state.py`, `refusals.py` and `text.py` are not flagged. The
  empty case, a list with no landed word, is past: `projects` landed with `first-project`. The
  stale case is real. `test_trace.py` has `test_each_landed_feature_word_has_its_domain_module` and
  no reverse test, which SDD RN-34 also records, so after the fold QC-11 names a check the code
  still owes. That is the next change's to add. The item's supporting text is now out of date: it
  says TS-4 "is raised on `SDD_open_issues.md` § 5.1". That item was folded into SDD version 6, and
  `SDD_open_issues.md` no longer exists. This is recorded here, not corrected in the item. Plain
  confirmation would have been the verdict only if the SDD had kept the PM's one-direction wording.

### 3.2 — The records do not say whether Ruff and mypy are gates, and the product installs both

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** answered
- **Why:** Both are gates. The item offers no lean, so this was decided from scratch.
  - **Whose call.** The change lands in `nfdr.md` §§ 9 and 10, which this seat owns. It binds only
    the product's own code bar, not a person, money or a risk someone carries. It is not an ADR,
    because dropping a gate is a one-line change, so it fails the "hard to reverse" test. No SDD
    sentence moves. SDD § 4 RT-4 governs dependencies, and Ruff and mypy are already in the
    `[dependency-groups] dev` set (`pyproject.toml:12-17`), locked in `tests/requirements.txt:8`
    and `:17`. QC-19 keeps them out of every module outside `tests/`, and gating them imports
    nothing.
  - **Why gate them.** The house default for a product that installs these tools is Ruff and mypy,
    and `ruff format --check` is named as "the gate form"
    (`<CORE>/doctrine/engineering/languages/python/quality_gates.md` § What a product installs, when
    it installs one). The same file says a per-product quality bar belongs in the product's own
    `docs/nfdr.md`. tracker17 installs both and configures both: the skeleton launcher copied them in
    at `c5c0b74f8`, and `83563a643` pinned them. QC-39 already pins them and QC-40 already watches
    their advisories. Leaving them out of the gates pays that cost and gets nothing for it.
  - **What the gate says.** Three commands, run from the product root inside RT-4's virtual
    environment, each passing on exit 0, gated at the suite, over the tree:
    1. `ruff format --check .`
    2. `ruff check .`
    3. `mypy main.py errors.py domain application persistence web` — QC-1's parts outside
       `tests/`.

    mypy has this scope because over `.` it stops on the two `conftest.py` files (exit 2) and checks
    nothing. Excluding `tests/` is the simplest scope that runs.
  - **Contradictions with settled entries.** Ruff 0.16.10's default rules flag `except Exception`
    at `web/routes.py:194` (BLE001). That line is QC-56's one site that catches a failure that is
    not a refusal, so a bare gate would reward breaking a settled obligation. The answer therefore
    says the entry wins, and the site turns that one rule off inline, naming the entry.
  - **Failure paths.**
    - *Stale:* a pin that moves can bring new rules or new type errors, so the change that moves the
      pin repairs or turns off what the new version finds. QC-40's review already sees that change.
    - *Starting red:* the gate begins red on `main`, with 8 Ruff findings and 3 mypy errors. The
      first change after the fold repairs them, and the PM routes that work. Each mypy error is a
      typing gap, not a fault at run time. `server_address` is typed as possibly bytes, and `site`
      is set on a class built with `type()`.
  - **What would have tipped it.** Making only Ruff a gate would have needed a reason to install a
    type checker and not run it. None exists on disk.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — The NFDR and two records cite SDD version 4's open questions, and SDD version 6 has closed two of them

- **What the document is owed:** RN-15 restated as one open question with the two closed ones named,
  `Inputs read:` brought to SDD version 6, and a Review Note that ADR-0007:53-54's open question is
  answered and that ADR-0003:55's "second item" is now the only one. Neither ADR is edited, since
  neither decision moved.
- **Why it is worth a cycle:** *Something upstream moved and it has not seen it*, and *a fact in it
  is now false*. `nfdr.md:6` reads "SDD Settled (version 4)", but the SDD is at version 6
  (`SDD.md:5`, commits `759ab7f5e` and `4e290298d`, both after `nfdr.md`'s last commit
  `facf92e37`). RN-15 (`nfdr.md:663`) counts three SDD Open Questions. SDD RN-35 and RN-36 closed
  two of them, and SDD § Open Questions now holds one. The round is already owed for § 3, so this
  costs no extra run. SDD version 5's changes, RT-7 carrying what the page showed and RT-10's stated
  maximums, move no entry I could find. QC-8 and QC-9 with RN-19 already hold them.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
