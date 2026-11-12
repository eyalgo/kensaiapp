# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md (version 20)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-12
- **Sources re-read:** One source outside this repository. uv's documentation,
  https://docs.astral.sh/uv/concepts/projects/sync/, "Automatic lock and sync", read 2026-11-12: it
  names `uv run --locked` and says that with the flag, "If the lockfile is not up-to-date, uv will
  raise an error instead of updating the lockfile." The answer's claim that the scenario folder's
  one command holds C-8 the way `uv sync --locked` does rests on that sentence. Read in this
  repository at `5a133b3e6`: the companion whole; `SDD.md` at its header, § 3 whole, § 4 RT-1 to RT-7
  (RT-4 whole, `SDD.md:335-361`), § 12 and RN-77; `products/tracker17/docs/SRS.md` C-7 and C-8;
  `products/tracker17/docs/nfdr.md` at its header (version 25), QC-1, QC-19, QC-39 and QC-40;
  `products/tracker17/docs/adr/0013-*.md` at its Decision;
  `products/tracker17/docs/architecture_open_issues.md` § 2.2 whole, slot filled;
  `products/tracker17/docs/trail/architecture/self_answer-28.md` whole, the run that opened this
  companion; `products/tracker17/docs/trail/sdd/self_answer-21.md` whole; under the product root,
  `pyproject.toml` whole, `.behave/pyproject.toml` whole, `.behave/uv.lock` at its head,
  `.behave/README.md` whole, every `import` and `from` line under `.behave/features/`, and
  `tests/architecture/test_pins.py` whole; `<CORE>/doctrine/setup/kensaiapp_structure.md` on the
  Behave starter and the start-of-run check; `system/projects/tracker17/project.md`,
  `finish_line.md` and `journey/shukuba/`, the last as an input for the commit's directional alone —
  no station is open, so the commit resolves against the finish line; and
  `system/doctrine/writing_bar.md` § 1. No test suite was run; this answer changes no code.

## Items worked

### 2.1 — § 4 RT-4 says every test dependency is declared in `pyproject.toml` and locked in one `uv.lock`, while `.behave/` declares and locks its own

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The seat is mine. The edit lands in § 4 RT-4, a condition this seat owns, and the answer
  binds the document's agreement with the product and the records, not a person, a risk or an outside
  party. The item is a correction and not a widening: RT-4 states "one committed file, `uv.lock`"
  and the product holds two, so the prompt's rule for a widening item waiting on an occurrence does
  not reach it. The draft's facts hold on disk. `.behave/pyproject.toml` pins `behave==1.3.3`,
  `httpx==0.28.1` and `playwright==1.63.0`; `.behave/uv.lock` sits beside it; the root
  `pyproject.toml` declares `mypy`, `playwright`, `pytest` and `ruff` and no `behave` or `httpx`. The
  draft's reason holds too: the heading "Only the tests have dependencies" stays true because NFDR
  QC-1 calls the folder test code, and only the sentence after it is false. I confirmed the two
  sentences as drafted and added three things.
  1. **A second sentence of RT-4 is false for the same folder (the argument is incomplete).** RT-4
     also says "No module outside `tests/` imports a test dependency." `.behave/features/server_way_in.py`
     imports `httpx`, `browser_way_in.py` imports `playwright`, and `environment.py` and the four
     step modules import `behave`. The draft says "Nothing else in RT-4 moves", and that sentence
     moves. It takes the scope NFDR QC-19 already carries, "outside `tests/` and `.behave/`", and
     QC-19 traces to RT-4, so the two agree once the fold runs. Without this, the fold would fix one
     false sentence of RT-4 and leave a second, and § 12 would have the second overrule QC-19.
  2. **The scope goes where the claim is (the draft answers at the wrong place).** The draft appends
     its two sentences at the end of the first paragraph, after some two hundred words, while the
     claim it corrects is RT-4's second sentence. A reader who stops at "in one committed file,
     `uv.lock`" still reads it as every test dependency's. So that sentence opens "The suite's are
     declared in `pyproject.toml`" in place of "They are declared", a change of one word that states
     the bound where it is read. This was the point closest to a different verdict: I weighed
     overriding the draft's placement and moving its two sentences up to follow that claim. I did not,
     because the draft's placement reads well where the condition finishes with the tracker's own
     setup, and the one-word bound does the work at the claim.
  3. **The folder's own setup is named, so "the one step" stays true (the absent case).** RT-4 says
     "Setting up the suite is the one step that needs a network connection, once". The scenario
     folder needs its own fetch: `uv run --locked behave` builds its environment on its first run, and
     `uv run --locked playwright install chromium` fetches its browser, both typed inside `.behave/`,
     as `.behave/README.md` gives them. The setup instructions name neither, and they need not: the
     folder is not the suite, no stage and no `Test command:` runs it (the NFDR's layer-7 row, as the
     architecture companion's § 2.2 answer has it), and § 6 S-1's prerequisites are the suite's and
     the tracker's. The addition says so, which keeps the claim true of the suite and tells a reader
     where the folder's commands live. A machine with no network after the suite is set up runs the
     tracker and the suite and fails the first `uv run --locked behave`, and that failure is at no
     gate.

  **Check 3.** SRS C-8, "the declared dependencies are fixed to exact versions", holds in both
  folders, and the draft's claim that C-8 holds the folder's pins rests on uv's `--locked` behaviour,
  which I re-read at the source named in the header. ADR-0013's Decision reads "in one committed
  file, `uv.lock`"; the Principal Architect's § 2.2 answer has a Review Note narrow it to the suite's
  set and no record move, and § 12 says the records are re-derived from § 4, so nothing here
  contradicts that. § 3's units table has one row, the product root, and its paragraph says what the
  language frame places there without claiming the root holds nothing else, as RN-77 already read it;
  the folder is no part and gets no row. The header's *Inputs read* line reads NFDR version 24 with the
  architecture companion removed, and the NFDR is at 25, Draft, with that companion live; three prior
  folds caught that line up without an item (RN-60, RN-66, RN-70), so none is raised for it here.
  **Check 4.** *Stale:* the start-of-run check writes the starter once and does not overwrite a
  committed `.behave/`, so its pins move only in this product's copy. The addition names the two
  files and no pin, so a pin bump does not make RT-4 false. *Concurrent:* the two manifests both pin
  `playwright==1.63.0` today, so one browser build is installed. Where the pins diverge, two builds
  are, and RT-4's Linux list is the suite's pin's; the folder's bound is its own pin's, and nothing in
  RT-4 ties the two. That is the named uncovered case, and QC-40 as the records' answer widened it
  reaches each pin. *Absent:* with `.behave/` removed, the two sentences describe a folder that is not
  there, and the pins test reads nothing (QC-1's "may also hold"); removing a committed folder is a
  change that re-reads RT-4 as any change does. *Refused:* a stale `.behave/uv.lock` stops the
  scenario command with an error, which is C-8 held at the folder as at the root. *Empty:* a
  `.behave/` with no manifest or lock fails the pins test as the records' answer has it, and RT-4
  needs no case for it.

## Left for the owner

None this run.

## Skipped

None this run. §§ 1, 3, 4 and 5 each read "None.", and § 2.1 is the companion's only item.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
