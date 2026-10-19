# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-08
- **Sources re-read:** three, all read at the source on 2026-10-08, because the answer to § 5.1 rests
  on them. (1) https://playwright.dev/python/docs/browsers, § *Install system dependencies*: "System
  dependencies can get installed automatically", `playwright install-deps chromium`, and the two can
  be combined as `playwright install --with-deps chromium`; on Linux the command runs the package
  manager and "Playwright will attempt to become a root", so it needs administrator rights. (2)
  https://playwright.dev/python/docs/intro, § *System requirements*: "Debian 12 / 13, Ubuntu 22.04 /
  24.04 / 26.04 (x86-64 or arm64)" for Linux; "macOS 14 (Sonoma) or later"; Python 3.8 or higher.
  (3) https://pypi.org/pypi/playwright/json: `info.version` is `1.63.0`, the version
  `tests/requirements.txt:12` pins, so the two documentation pages describe the pinned library.
  What was read in-repo, besides `SDD.md` whole and the companion: `SRS.md` FR-4, § 5.3, NFR-11,
  NFR-13, C-7, C-8, AC-2, AC-3, RN-23; `PRD.md` (grep for platform words: none); `UXD.md` UX-F1
  and UX-S1; `nfdr.md` QC-40, QC-47 and the layer-5 row; `adr/0009-one-unix-lock-no-windows.md`;
  `architecture_open_issues.md` § 3.1; `README.md` whole; `pyproject.toml`,
  `tests/requirements.txt`, `tests/e2e/conftest.py`, `tests/integration/test_start.py:165-170`,
  `.gitignore`; the open station
  `system/projects/tracker17/journey/shukuba/2026-10-08_setup-instructions.md` and the PM's refine
  report beside the seed, `2026-10-08_setup-instructions_report.md`, which records the Linux run the
  item cites. No suite was run: the item's measurements are the PM's, recorded in that report and in
  commit `5cbaf3a80`, and this run changed no code.

The companion held one open item, § 5.1, `Seat: cto`, and the invocation listed none, so this run
worked it. It cites an occurrence — a run on Debian 12 aarch64 on 2026-10-08 — so § *A widening item
waits until it occurs* does not send it back.

## Items worked

### 5.1 — § 11 R-9 has shown up: on Linux the end-to-end suite cannot start its browser, and a copy that is not a Git repository fails one test

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** Answered on both of its questions, in one slot. The item hands no draft — it asks two
  questions and names one command as an example — so there was nothing to confirm or overturn, and
  the verdict is *answered*. Both questions resolve to the same seat, so the item did not split.

  *Seat (check 1).* Every edit lands in a CTO part of the SDD: § 4 RT-3 and RT-4 (runtime shape),
  § 6 S-1 *Artifact* (the artifact that must exist), § 11 R-9. SRS RN-23 puts the prerequisites
  with the SDD. RT-3 was first drafted for the CPO (RN-11) because which readers the product serves
  is product scope — but neither answer moves that: the tracker still runs on macOS and Linux, and
  what changes is what the *test suite* needs, which binds nobody outside the document. No ground
  the owner holds is one this run could not see, so the item is mine in the owner's seat.

  *The questions hold (check 2), and the answers.* **Linux.** The failure is a missing shared
  library for the browser build the pinned library installs (`libglib-2.0.so.0`), on Debian 12
  aarch64, which is on that library's own supported list (Header, source 2). So it is not an
  unsupported machine and not a tracker defect: the tracker served and `pytest tests/` passed 224,
  as RT-3 expected ("needs no code of its own"). It is a prerequisite the instructions do not name,
  and the library's documented remedy is exactly the item's example, `python -m playwright install
  --with-deps chromium`, which runs the distribution's package manager and needs administrator
  rights (source 1). The alternative the item offers — name Linux for the tracker and not for the
  suite — I did not take whole, because it would make the instructions withhold a one-line fix from
  every Debian and Ubuntu reader; but it carries a true bound, which I kept: the tracker runs on any
  Linux with Python 3.11 (RT-1, standard library only), while the end-to-end suite runs only where
  the pinned library does, Debian 12/13 and Ubuntu 22.04/24.04/26.04. The answer therefore names
  Linux for both and gives the suite its narrower bound, and says that on another Linux the tracker
  and `pytest tests/` run while `pytest tests/e2e/` is a missing prerequisite. The list is the
  pin's: SRS C-8 fixes the pin, so the list moves only when the pin does. RT-3's "checked on macOS
  only" stays in the instructions, because the Agari's check reaches only macOS and no end-to-end
  run has passed on Linux — one PM run of the tracker and the non-browser suite is evidence R-9
  records, not the check RT-3 names. R-9 is narrowed rather than closed: its own text said one run
  of the instructions and both suites on Linux would settle it; the run happened and settled the
  tracker and one suite, and the end-to-end suite stays unsettled until it passes there with the
  named libraries. No slice requires that run, as before. **Git.** The test
  (`tests/integration/test_start.py:165-170`) runs `git check-ignore` from the product root and
  asserts exit 0; outside a repository Git exits 128, so the test fails, and with no `git` at all
  `subprocess.run` raises, so it errors — either way the reader's suite is not green. It is NFDR
  QC-47's verification, and the property it checks is a property of a repository, so the honest
  statement is that the full suite needs the copy to be a Git repository with `git` on the path.
  Named as a prerequisite *of the suite*, not of the tracker: the tracker's setup needs no Git, and
  a downloaded copy runs it. I weighed making the test skip outside a repository and did not take
  it: a skip makes the suite read green in exactly the copy where QC-47 cannot be checked, which is
  a hidden absence where the README's current sentence ("one test doesn't pass") is a visible one.
  The README already carries that sentence (`README.md`, "Running the tests", landed in
  `9f587e679`); the fold has S-1 *Artifact* record it, so the artifact and its specification agree.

  *Nothing settled moves (check 3).* SRS FR-4 asks the prerequisites to say setup needs a network
  connection once "to fetch the declared dependencies (§ 5.3)", and § 5.3 lets setup fetch from
  "public sources that need no account, key or sign-up" — a distribution's package repository is
  one. SRS C-7's three-command bound and AC-3 cover the tracker's setup, which neither answer
  touches; the suite's section is outside that count already (RT-2, "setup is two commands"). C-8
  fixes "the declared dependencies" to exact versions; the system libraries are the operating
  system's, as Python is, and not declared dependencies, which the answer says so that a reader does
  not look for a pin on them. NFR-13 keeps the end-to-end layer in Chromium. ADR-0009 says "setup
  instructions have one set of prerequisites" and "Linux is named as supported and nothing checks
  it (SDD § 11 R-9)": the tracker's prerequisites stay one set, and the Agari's check still does
  not reach Linux, so I judged neither sentence false and raised nothing on
  `architecture_open_issues.md`; the Principal Architect reads the SDD when it folds, and § 3.1
  there already holds the browser build's advisory window, which this answer does not touch. My
  doubt, for the owner: the ADR's "nothing checks it" reads thinner once R-9 records a Linux run,
  and if the owner reads it as now false, it is one item on the architecture companion. SDD § 1's
  "setup is at most three commands" and § 9 are untouched. No earlier answer of this run bears on
  it; there was one item.

  *Failure paths (check 4).* *Absent*: no network — the install fails, and FR-4 already has the
  instructions explain an offline setup. *Refused*: a reader declines administrator rights — the
  end-to-end suite is a missing prerequisite, `pytest tests/` still passes, and the answer has the
  instructions say the tracker and `pytest tests/` need none of it. *Empty*: a Linux outside the
  pinned library's list, such as the Fedora machine this run is on — the tracker and `pytest tests/`
  run, `pytest tests/e2e/` is a missing prerequisite, named as such. *Stale*: the library's list
  moves with its versions — the SDD states the rule (the suite's Linux support is the pinned
  library's), the instructions carry the list for the pin, and moving the pin re-reads it; a
  changed pin is already a design review under QC-40. *Concurrent*: none — the command is a one-time
  install. For Git: the instance's own seats run `pytest tests/` in disposable `git archive` copies
  (every refine report records the one failure), while the pipeline's real suite runs in a change
  worktree, which is a repository — so the pipeline is green and the ad-hoc copies show one known
  red, which the prerequisite now explains rather than hides. I was close to *confirmed with
  addition* on the strength of the item's example command; what kept it at *answered* is that the
  item asks rather than proposes, and the bound on Linux and the Git placement are decided here,
  not handed.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
