# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** five sources outside this repository, each read on 2026-10-06.
  - `task-tracker-X/pyproject.toml`. It reads
    `requires-python = ">=3.11"`. Its `[project]` table has no `dependencies` key, and its one optional
    group is `dev = ["pytest"]`. A scan of every `import` line under `tasktracker16x/` found the
    package itself and ten standard-library modules, and no third-party one.
  - This machine. `python3 --version` printed `Python 3.14.7`, and `/usr/bin/python3 --version`
    printed `Python 3.9.6`. `python3 -m pip install --no-index --no-deps zz-tracker17-no-such-package`
    printed `error: externally-managed-environment` and installed nothing. The same command inside a
    scratch virtual environment made with `python3 -m venv` got past that check and failed only on the
    made-up package name. `importlib.util.find_spec('cgi')` returned `None` under 3.14.7.
  - https://packaging.python.org/en/latest/specifications/externally-managed-environments/. It says
    that outside a virtual environment "the installer should exit with an error message indicating
    that package installation into this Python interpreter's directory are disabled outside of a
    virtual environment."
  - https://docs.python.org/3/library/http.server.html, the page for Python 3.14.8. It carries both
    sentences `SDD.md` § 11 R-4 and R-7 quote. It marks `CGIHTTPRequestHandler` and the `--cgi` option
    as removed in 3.15, and the fetch found no other deprecation notice on the page.
  - https://docs.python.org/3/whatsnew/3.13.html. It lists `cgi` and `cgitb` among nineteen modules
    that "were deprecated in Python 3.11, and are now removed".

## Items worked

### 2.1 — The tracker runs on Python 3.11 or later and uses only the Python standard library when it runs

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed. The tracker runs on Python 3.11 or later, imports only the standard
  library when it runs, and starts with `python3 main.py`. Four additions come from the settled SRS
  and UXD and from the failure paths.

  *Seat.* This item is the CTO's, and this run answered it in that seat. The edit lands in `SDD.md`
  § 4 and § 9, and that document's table under "Who decides what" gives "runtime and deployment shape"
  and "§ 9 Trade-offs taken" to the CTO. `SRS.md` § Open Questions hands the choice down in the words
  "The prerequisites FR-4 names follow from the SDD's choice of runtime". The answer commits nobody
  outside the product, and I can name no ground the owner holds that this run could not see.

  *The draft holds, and its second reason is stronger than it says.* Three of its claims were checked
  at their sources. The predecessor declares the same floor and has no run-time dependency (first
  source above). `UXD.md` § 9 does reject a design-system package as "a dependency and a body of
  styling code they would also have to read or take on trust". The standard library still ships the
  listener the design rests on (fourth source above). The draft says a framework's install step "uses
  up" SRS C-7's three commands. On the owner's machine it would break them. `pip` refuses to install
  outside a virtual environment there (second source above), so setup with one run-time package
  would be four commands: move into the copy, make the environment, install, start. This follows from
  the draft's own count, which treats moving into the copy as a command.

  *Addition (1), where the network prerequisite lands (check 3).* `SRS.md` FR-4 requires the setup
  instructions to state "that setup needs a network connection once, to fetch the declared
  dependencies". `UXD.md` UX-S1 lists "prerequisites (including the one-time network connection setup
  needs)". Under the draft the tracker has no declared dependency to fetch, so only the test suite
  needs that connection. `SDD.md` does not say so. RT-1 says "The stated prerequisite is therefore
  Python alone", RT-4 says "so running the suite adds no prerequisite", and
  `grep -n -i -E "network|offline" products/tracker17/docs/SDD.md` returned lines 121, 162, 181 and
  878, none of them about setup. The companion says it once, under item 2.1's *If overridden*, and the
  companion is deleted when the SDD is done. Left as written, the setup instructions built from the
  SDD would have nowhere to put FR-4's line. The addition states it in § 4 and replaces RT-4's
  clause. No SRS or UXD sentence has to move. `SRS.md` § 5.3 says a fresh copy "may fetch its declared
  dependencies", and FR-4's line stays true of the suite.

  *Addition (2), `pip` says no (check 4, refused).* RT-4 says the test dependencies "are installed
  with the installer that ships with Python". On the owner's machine that installer refuses unless it
  runs inside a virtual environment, and it works inside one made with Python's own `venv` module
  (second and third sources above). RT-4 therefore names the virtual environment. Python is still the
  only thing to install first, because `venv` and `pip` both ship with it.

  *Addition (3), an older `python3` (check 4, stale).* The case is real on this machine:
  `/usr/bin/python3` is 3.9.6, below the floor. `UXD.md` UX-F1 already says whose failure a missing
  prerequisite is: "the failure is one the instructions already describe, and they say what to
  install or do." The addition follows that. The prerequisites section names the command that shows
  the version, and `pyproject.toml` declares the floor. `SDD.md` § 4 OB-2 says "A start that cannot
  proceed shows one plain message". That sentence cannot hold under a Python too old to run the
  tracker, so the addition scopes OB-2 to a start the tracker itself refuses. OB-2 is the CTO's
  condition, in the same lane as RT-1.

  *Addition (4), the floor is declared and unchecked (check 4, stale).* The suite runs on the Python
  the machine has, which is 3.14.7 on the owner's machine. Nothing in the Agari's check runs the
  tracker on 3.11, 3.12 or 3.13. The standard library is not the same across those versions: `cgi`
  exists in 3.11 and is gone from the owner's Python (second and fifth sources above). Code written
  and tested on 3.14.7 can also use something 3.11 lacks, and no test on the owner's machine would
  fail. `SDD.md` § 11 is where the SDD records a claim that may turn out false, so the addition is a
  risk there. It shows up as a start or a suite failure on a Python between 3.11 and the one tested.
  One run of `pytest tests/` under a Python 3.11 interpreter would settle it, and no slice requires
  that run.

  *Named and not covered.* Absent: with no `python3` at all, the shell prints its own "command not
  found", and the setup instructions' prerequisites cover it under UX-F1. Empty and concurrent: the
  choice of runtime changes neither a fresh copy with no saved data (`SRS.md` FR-7) nor two trackers
  on one saved-data location (`SRS.md` NFR-3). Linux: this run measured macOS only. Whether Linux
  stays supported is item 2.2, which another seat answers, and nothing here was checked on Linux.

  *Close calls.* I nearly made addition (3) a version check as the first statement of `main.py`, with
  its own plain message. I did not, because that message would be a fourth start failure in `UXD.md`
  UX-S2, which lists three, and the UXD is settled. On the owner's machine `python3` is 3.14.7, so the
  case does not occur inside the Agari. An outside reader, or an owner machine whose `python3`
  resolves below 3.11, would tip it, and the change would then go to the UXD first. I also weighed
  stating the prerequisite as the version the suite passes on, in place of 3.11. I kept 3.11 because
  the predecessor's code and tests carry that floor and SRS C-5 prefers them as the starting point.
  Addition (4) records what keeping it costs.

## Left for the owner

None this run.

## Skipped

- **2.2 — The tracker is supported on macOS and Linux, and not on Windows** — not on this run's list.
  It carries `Seat: cpo` and is carried by another seat's run. Its slot is untouched.
- **2.3 — No page runs a script, so every action reloads a whole page** — not on this run's list. It
  carries `Seat: cdo` and is carried by another seat's run. Its slot is untouched.
- **2.4 — What a person can watch at the end of each slice, as drafted from the UXD** — not on this
  run's list. It carries `Seat: cdo` and is carried by another seat's run. Its slot is untouched.
- **2.5 — The eight slices: what each delivers, and what each leaves to another** — not on this run's
  list. It carries `Seat: cpo` and is carried by another seat's run. Its slot is untouched.
- **3.1 — `delete-and-rename` is its own slice, and not part of `tasks-in-a-project`** — not on this
  run's list. It carries `Seat: cpo` and is carried by another seat's run. Its slot is untouched.
- **3.2 — People arrives in two halves, and there is no slice for People alone** — not on this run's
  list. It carries `Seat: cpo` and is carried by another seat's run. Its slot is untouched.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
