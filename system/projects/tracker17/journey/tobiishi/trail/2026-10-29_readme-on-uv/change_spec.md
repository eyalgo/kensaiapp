# Change Spec — the README sets up the test suite with uv

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing
**Request:** Make the product README tell the reader to set up the test suite with uv. Today its "Running the tests" section (`products/tracker17/README.md`, L93-L109) has the reader make a `venv`, activate it and `pip install -r tests/requirements.txt`, a file the last change deleted, so those instructions no longer work. SDD § 4 RT-4 and ADR-0013 already give the uv path. After this change:

- "Running the tests" says uv has to be installed first, and where to get it. Its command block is `cd products/tracker17`, `uv sync --locked`, `uv run playwright install chromium`, `uv run pytest tests/` and `uv run pytest tests/e2e/`. The Linux paragraph says to type `uv run playwright install --with-deps chromium` in place of the install command. The `.venv` paragraph and the "new terminal, `source .venv/bin/activate`" paragraph are reworded to match uv (no activation step; `uv sync --locked` makes `.venv`). The `pytest tests/` and `pytest tests/e2e/` prose names the `uv run` forms.
- The "How it's built" test line says the suite's environment is made by uv, in place of "Python's `venv`".
- `grep -nF -e 'python3 -m venv' -e 'pip install' -e 'requirements.txt' -e 'activate' -e 'python -m playwright' -e '`venv`' README.md` prints nothing and exits 1.
- The tracker's own setup text (`## Setup instructions` down to `### Running the tests`) names uv nowhere, and the tracker's start path stays `python3 main.py` with nothing installed. That text changes only for a sentence this edit makes false.

Each command is the one SDD § 4 RT-4 gives, and works from `products/tracker17` on `main`. No tracker code, test, record under `docs/`, or project card line changes: the card's Setup and Test commands are the next station's.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The README's "Running the tests" section and its "How it's built" test line move from a `venv` filled
from the deleted `tests/requirements.txt` to the uv path SDD § 4 RT-4 and ADR-0013 state: install uv,
then `uv sync --locked`, then every suite command through `uv run`. The tracker's own setup text, and
its two-command start, stay as they are.

Every path below is relative to the product root, the directory `system/projects/tracker17/project.md`
`Product path:` names, and every command is typed from there unless the rule says otherwise. "The
section" means the README's text from the `### Running the tests` heading down to the next `## `
heading (`## Where it came from`).

---

## Rules

### The suite section — `### Running the tests`

- **CP-668:** The section says uv has to be installed before any of its commands is typed, and names
  uv's installation page, `https://docs.astral.sh/uv/getting-started/installation/`, as where to get
  it (SDD § 4 RT-4, "says to install uv first, as uv's own documentation says"). The tool's name is
  written `uv`, in lower case, everywhere the README names it (`docs/CONTENT.md`, "names of commands
  and tools in the setup instructions are written as their own owners write them").
- **CP-669:** The section's command block holds exactly these five lines, in this order, and no other
  line:

  ```
  cd products/tracker17
  uv sync --locked
  uv run playwright install chromium
  uv run pytest tests/
  uv run pytest tests/e2e/
  ```

  Each is the command SDD § 4 RT-4 gives. The section keeps saying to open the terminal at the top of
  the copy before the block, because the block's first line moves into `products/tracker17` from there.
- **CP-670:** The section says that `uv sync --locked` is the command that makes the tests'
  environment and installs the test dependencies into it, and that every test command is typed
  through `uv run` (SDD § 6 S-1 *Artifact*: "gives `uv sync --locked` as the command that makes the
  suite's environment and installs the test dependencies, and `uv run` as the way every suite command
  is typed").
- **CP-671:** The Linux paragraph says that, on Linux, where the commands say
  `uv run playwright install chromium`, the reader types `uv run playwright install --with-deps chromium`
  instead. It keeps each statement it makes today, with the command named in its `uv run` form: the
  command also installs the system libraries the browser needs, using the operating system's package
  manager; it asks for administrator rights; the tracker and `uv run pytest tests/` need none of what
  it installs; and the end-to-end tests need Debian 12 or 13, or Ubuntu 22.04, 24.04 or 26.04, on
  x86-64 or arm64 (FDR R-119, R-120; SDD § 4 RT-4).
- **CP-672:** The section's prose names `uv run pytest tests/` as the command that runs every test
  except the end-to-end ones, and `uv run pytest tests/e2e/` as the one that runs the end-to-end
  tests, which drive Chromium. Every occurrence of the string `pytest` in the section is part of the
  string `uv run pytest`: the section names no bare `pytest` command for the reader to type.
- **CP-673:** The `.venv` paragraph says that `uv sync --locked` makes the tests' environment in
  `.venv`, inside `products/tracker17`, and tells the reader to keep it there. It keeps its two
  statements: the tests read the Python in `products/tracker17` as the tracker's own, except in
  directories whose names start with a dot; and an environment anywhere else inside
  `products/tracker17` stops them passing.
- **CP-674:** The new-terminal paragraph says that, in a new terminal, the reader runs the tests again
  by typing the `uv run` test commands inside `products/tracker17`. It names no step to take before
  them: there is no activation step.
- **CP-675:** The section keeps saying that setting the tests up needs a network connection, and only
  for setting them up. The paragraph on the Git repository — that the copy needs to be a Git
  repository with `git` on the path, that otherwise 1 test doesn't pass, what that test checks, and
  that the tracker needs neither — stays word for word as it is today (SDD § 6 S-1 *Artifact*; SRS
  FR-6).

### "How it's built"

- **CP-676:** The test bullet (`- **Tests in pytest**`) says the test dependencies, each fixed to an
  exact version, are installed into an environment uv makes, where today it says "a virtual
  environment made with Python's `venv`". It keeps its other statements — three layers, unit,
  integration and end-to-end; the end-to-end tests drive Chromium; only the tests have dependencies —
  and its citation of `docs/SDD.md` § 4 RT-4 and TS-1.
  `sed -n "/^## How it's built/,/^## The documents/p" README.md | grep -nw uv` prints at least one line.
- **CP-677:** The first bullet's link names ADR-0013, at `docs/adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md`,
  where today it names ADR-0002 (`README.md:121`). ADR-0002 is superseded by ADR-0013
  (`docs/adr/README.md`, the ADR-0002 row), and ADR-0013 carries its decision whole, with the suite's
  environment made by uv.

### "The documents"

- **CP-678:** The `docs/adr/` line states no count of architecture decisions other than the number of
  records `docs/adr/README.md` indexes, which is thirteen. Today it says "the nine architecture
  decisions" (`README.md:147`). It may instead state no count. It keeps saying the records are indexed
  in `docs/adr/README.md`.

### What stays as it is

- **CP-679:** The tracker's own setup text — the README from the `## Setup instructions` heading down
  to the line before the `### Running the tests` heading — is unchanged, byte for byte. It names uv
  nowhere: `sed -n '/^## Setup instructions/,/^### Running the tests/p' README.md | grep -nw uv`
  prints nothing and exits 1. The start path it gives stays `cd products/tracker17` then
  `python3 main.py`, with nothing installed. No sentence in that text is made false by this change
  (Verified Claims), so the request's allowance for one is not used.
- **CP-680:** `grep -nF -e 'python3 -m venv' -e 'pip install' -e 'requirements.txt' -e 'activate' -e 'python -m playwright' -e '`venv`' README.md`
  prints nothing and exits 1. The grep is fixed-string, case-sensitive and reads every line of the
  README, so no new wording may hold any of those strings either: "nothing to activate" and
  "activated" each hold `activate`, and `uv run python -m playwright` holds `python -m playwright`.
- **CP-681:** Every heading of the README keeps its text, its level and its place in the order, and
  the README gains and loses no heading. The thirteen are those at `README.md` lines 1, 7, 13, 17, 31,
  42, 54, 60, 71, 89, 113, 117 and 137 today.
- **CP-682:** `README.md` is the only file under the product root that changes. No tracker code, no
  test, no file under `docs/`, `pyproject.toml`, `uv.lock` and no line of
  `system/projects/tracker17/project.md` changes.

### The commands work

- **CP-683:** On macOS, in a fresh clone of the branch's commit, with uv installed and a network
  connection, typing the five lines of CP-669 in order from the top of the copy, each exits 0.
  `uv sync --locked` leaves a `.venv` directory inside `products/tracker17` that Git ignores, and
  leaves `uv.lock` byte-identical to the committed file (SDD § 4 RT-4; ADR-0013 § Decision).

### Checks the records above require of this change

- **CP-684:** This change's `development-design` review asks the two questions NFDR QC-41 and QC-12
  put to every change there. QC-41: the step it adds, installing uv from the page CP-668 names, asks
  for no account, key, credential, sign-up or payment (FDR R-14). QC-12: the change adds no part that
  no requirement pays for.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Read the section (CP-668) | it says uv has to be installed first and names `https://docs.astral.sh/uv/getting-started/installation/`; the tool is written `uv` |
| Read the section's command block (CP-669) | the five lines of CP-669, in that order, and nothing else |
| Read the section (CP-670) | it says `uv sync --locked` makes the environment and installs the test dependencies, and that every test command goes through `uv run` |
| Read the Linux paragraph (CP-671) | `uv run playwright install --with-deps chromium` in place of `uv run playwright install chromium`; package manager, administrator rights, `uv run pytest tests/` needs none of it, the five Linux systems on two architectures |
| `sed -n '/^### Running the tests/,/^## /p' README.md \| grep -o '.\{0,7\}pytest' \| grep -vxF 'uv run pytest'` (CP-672) | prints nothing, exits 1 (on `main` today it prints bare `pytest` mentions and exits 0) |
| Read the `.venv` paragraph (CP-673) | `uv sync --locked` makes `.venv` inside `products/tracker17`; keep it there; the dot-directory reason; an environment elsewhere inside stops the tests passing |
| Read the new-terminal paragraph (CP-674) | run the `uv run` test commands again inside `products/tracker17`; no step before them |
| `git diff main -- README.md`, the Git-repository paragraph (CP-675) | no line of it differs |
| `sed -n "/^## How it's built/,/^## The documents/p" README.md \| grep -nw uv` (CP-676) | prints at least one line, the test bullet; exits 0 (on `main` today it prints nothing and exits 1) |
| `grep -n 'docs/adr/000[0-9]-\|docs/adr/001[0-9]-' README.md` (CP-677) | the first "How it's built" bullet links `docs/adr/0013-…`; no line links `docs/adr/0002-…` |
| Read the `docs/adr/` line under "The documents" (CP-678) | "thirteen", or no count; it still names `docs/adr/README.md` as the index |
| `git diff main -- README.md`, lines from `## Setup instructions` to before `### Running the tests` (CP-679) | no line differs; the CP-679 grep prints nothing and exits 1 |
| The CP-680 grep, branch tree (CP-680) | prints nothing, exits 1 (on `main` today it prints lines 93, 97, 98, 99, 100, 109 and 135, and exits 0) |
| A rewording that says "there is nothing to activate", then the CP-680 grep (CP-680) | prints that line and exits 0: the rewording breaks CP-680 |
| `grep -n '^#' README.md` (CP-681) | the same thirteen headings, at the same levels, in the same order as on `main` |
| `git diff --name-only main -- products/tracker17 system/projects/tracker17/project.md` (CP-682) | `products/tracker17/README.md` only |
| macOS, fresh clone of the branch commit, the five CP-669 lines typed in order from the top of the copy (CP-683) | each exits 0; `products/tracker17/.venv` exists and `git status --short --ignored` shows it as ignored; `uv.lock` unchanged |
| `development-design` review of this change (CP-684) | uv's installation asks for no account, key, sign-up or payment; no part is added |

---

## Verified Claims

All runs used uv 0.11.14 on macOS, in a disposable clone of the instance at `898e1ccf6` (`main`),
working in `products/tracker17`. The post-change README was built there by hand, to CP-668 to CP-676,
and the four checks run against it.

| Claim | Verified by | What came back |
|---|---|---|
| Today's README fails CP-680 at the lines the station names | the CP-680 grep on `main` | lines 93, 97, 98, 99, 100, 109, 135; exit 0 |
| The file the README installs from is gone | `ls tests/requirements.txt` on `main` | no such file |
| `uv sync --locked` works from `products/tracker17` and makes `.venv` there, ignored by Git (CP-673, CP-683) | `uv sync --locked`; `ls -d .venv`; `git status --short --ignored` | exit 0; `.venv` present; `!! .venv/` |
| `uv run` uses that environment, with nothing activated (CP-674) | `uv run python -c 'import sys; print(sys.executable)'` | the `python3` under `products/tracker17/.venv/bin/` |
| `uv run playwright install chromium` works (CP-669, CP-683) | the command, after the sync | exit 0 |
| `--with-deps` is an option of that command (CP-671) | `uv run playwright install --help` | `--with-deps    install system dependencies for browsers` |
| The four station checks can all pass on a README written to these rules | CP-680's grep; the four strings of CP-669 and the two of CP-668 and CP-671 counted in the section; CP-676's `sed … \| grep -nw uv`; CP-679's `sed … \| grep -nw uv` | exit 1; each found at least once; one line, exit 0; nothing, exit 1 |
| Two of the checks fail or pass on `main` today as the Examples say | CP-676's and CP-679's commands on `main` | CP-676's prints nothing, exit 1; CP-679's prints nothing, exit 1 |
| CP-672's check passes on the post-change README and fails on `main` | its command on each | nothing, exit 1; bare `pytest` mentions, exit 0 |
| A careless rewording breaks CP-680 | the grep's `activate` and `python -m playwright` patterns over "There is nothing to activate." and `uv run python -m playwright install chromium` | both lines printed |
| No sentence of the tracker's own setup text is made false (CP-679) | read `README.md:13-88` against ADR-0013 § Decision | the one sentence on the tests, `:29`, says setting them up needs a network connection once, to fetch their dependencies and the browser; `uv sync --locked` and `uv run playwright install chromium` do that, so it stays true. No line names `venv`, `pip` or uv |
| Two tests read the README's headings, and none reads its text otherwise (CP-681) | `grep -rn README tests --include='*.py'`; `tests/integration/test_start.py:35,37,166,196-208` | `test_the_readme_has_both_fixed_headings` and `test_the_message_closing_sentence_quotes_a_heading_the_readme_has` need "Starting the tracker again" and "Setting saved data aside"; `tests/e2e/` reads no README |
| The dot-directory statement CP-673 keeps is true | `tests/conftest.py:142` | a path with a part starting with `.` is skipped |
| `uv run pytest tests/` does not collect the end-to-end tests (CP-672) | `tests/conftest.py:15` | "The collection rule keeps the product-local ``pytest tests/`` from collecting ``tests/e2e/``" |
| ADR-0002 is superseded, and the README still links it (CP-677) | `docs/adr/README.md` ADR-0002 row; `README.md:121` | "Superseded by ADR-0013"; `[ADR-0002](docs/adr/0002-standard-library-only-no-web-framework.md)` |
| The ADR index lists thirteen records, and the README says nine (CP-678) | `docs/adr/README.md` rows ADR-0001 to ADR-0013; `README.md:147` | thirteen rows; "the nine architecture decisions" |
| The installation page CP-668 names is the one the SDD cites | `docs/SDD.md` § 4 RT-4 | `https://docs.astral.sh/uv/getting-started/installation/`, "Standalone installer", read 2026-10-29 |
| The suites pass after that setup, and leave the tree as it was (CP-683) | `uv run pytest tests/ -q`, then `uv run pytest tests/e2e/ -q`, then `git status --short` | 2698 passed, exit 0; 121 passed, exit 0; nothing listed, so `uv.lock` is unchanged |

No rule pins output that renders a language-level fact, so there is no language-rendering row.

---

## Out of Scope

- The prerequisites section, `### What you need` (`README.md:17-29`). SDD § 6 S-1 *Artifact* says it
  holds, "for the test suite only, uv and a network connection needed once". Today it names Python,
  the operating systems and the network connection, and not uv. The request rules it out: "The
  tracker's own setup text (`## Setup instructions` down to `### Running the tests`) names uv
  nowhere". SDD § 4 RT-4 says the same — "the tracker's own setup names it nowhere" — so the two SDD
  sentences pull apart on this section. Handed on as a record gap in `deferred_decisions.md`.
- The project card's `Setup command:` and `Test command:`. The request gives them to the next station.
- Every record under `docs/`, including the SDD and ADR lines that still name the `venv` path as
  history.
- The README's `## Status` paragraph. It is the `readme-status` run's, after the station closes.
- Any README section not named in the Rules: the opening paragraph, "Where it came from", and the
  rest of "How it's built" and "The documents".
- Installing uv for the reader, giving uv's installer command in the README, or naming a uv version.
  The README points at uv's own page (CP-668).
- Linux. No run on Linux is made for this change. CP-683 is checked on macOS, the only system the
  tracker has been checked on (SDD § 4 RT-3; § 11 R-9).
- The suite's run on Python 3.11 itself (`uv run --python 3.11 pytest tests/`, SDD § 11 R-8). This
  change uses no language or library feature, so NFDR QC-60's review does not reach it.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — where to get uv (CP-668):** the section names
  `https://docs.astral.sh/uv/getting-started/installation/`. (b): the request says "where to get it"
  and names no place. SDD § 4 RT-4 cites that page as the one whose instructions the reader follows,
  and SDD § 6 S-1 asks the section to say "how to install uv". Pointing at uv's own page meets both
  and leaves the installer command to uv, which changes it without a change here.
- **Gap 2 — the section says what `uv sync --locked` and `uv run` are for (CP-670):** (b): the request
  gives the commands and not this sentence. SDD § 6 S-1 *Artifact* binds the section this change
  rewrites, and asks for it in those words.
- **Gap 3 — the tool's name in lower case (CP-668):** (b): the request is silent. `docs/CONTENT.md`
  has a tool's name written as its owner writes it, and the station's `grep -nw uv` checks find the
  name only in lower case.
- **Gap 4 — the Linux paragraph names `uv run pytest tests/` (CP-671):** (b): the request asks for the
  `--with-deps` command only. The paragraph today says "`pytest tests/` need none", and the request
  has the `pytest tests/` prose name the `uv run` forms. SDD § 4 RT-4's sentence for that paragraph
  says "`uv run pytest tests/` need none of this".
- **Gap 5 — no bare `pytest` in the section (CP-672):** (b): the request names the two prose mentions.
  The section is read as one set of instructions, and a bare `pytest` there is a command that runs
  without the locked environment.
- **Gap 6 — the setup text unchanged byte for byte (CP-679):** (b): the request allows a change for "a
  sentence this edit makes false". None is (Verified Claims), so the allowance is closed rather than
  left open for a later stage to read.
- **Gap 7 — the Git paragraph and the network sentence stay (CP-675):** (b): the request leaves them
  out. SDD § 6 S-1 *Artifact* asks the section to keep the Git paragraph. Keeping both is the
  conservative reading of a rewrite of the section's other paragraphs.
- **Gap 8 — the headings stay (CP-681):** (b): the request is silent. Two tests read the headings, the
  station's checks find the section by them, and `docs/CONTENT.md` § Terminology fixes two of them.
  Keeping them all leaves both tests unchanged.
- **Gap 9 — only the README changes (CP-682):** (b): the request rules out code, tests, `docs/` and
  the card. `pyproject.toml` and `uv.lock` are named too, because the commands CP-683 runs must work
  on the lock file as it is.
- **Gap 10 — the commands work, on macOS (CP-683):** (b): the request says each command "works from
  `products/tracker17` on `main`". The rule makes that a run in a fresh clone of the branch commit,
  and holds it to macOS, the only system the tracker is checked on.
- **Gap 11 — ADR-0013 in place of ADR-0002 (CP-677):** beyond the request. The link sits in the
  section this change edits, and points at a superseded record whose decision is the `venv` path this
  change removes. A small defect found on the branch is fixed on it
  (`<CORE>/doctrine/governance/found_while_walking.md` § The rule, clause 1).
- **Gap 12 — the ADR count (CP-678):** beyond the request, for the same reason as Gap 11: "nine" has
  been wrong since the tenth record, and the fix is one word in the file this change edits.
- **Gap 13 — QC-41 and QC-12 at review (CP-684):** (e): NFDR QC-41 and QC-12 are verified by review at
  `development-design`, and this change adds a setup step. FDR R-14 asks that no setup step asks for
  an account, a key, a sign-up or a payment. The request leaves them out.
