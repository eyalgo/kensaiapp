# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** four sources outside this repository, each read on 2026-10-06.
  - https://docs.python.org/3/library/fcntl.html, the page for Python 3.14.8. Its availability line
    reads "Availability: Unix, not WASI." The page names constants the module exposes "On macOS" and
    "On Linux".
  - https://docs.python.org/3/library/msvcrt.html, the page for Python 3.14.8. Its availability line
    reads "Availability: Windows." It describes `msvcrt.locking(fd, mode, nbytes)` as "Lock part of a
    file based on file descriptor *fd* from the C runtime."
  - This machine. `uname -s` printed `Darwin`. `python3 -c 'import sys,platform;
    print(sys.platform, platform.python_version())'` printed `darwin 3.14.7`.
  - `task-tracker-X`, the predecessor. A search of `tasktracker16x/`
    for `fcntl`, `msvcrt`, `flock` and `lockf` returned no line. A search of `docs/`, `README.md` and
    `pyproject.toml` for "windows", "macos", "linux", "operating system" and "posix" returned no line.

This run was given four items: 2.2, 2.5, 3.1 and 3.2. It decided them in the order 2.2, 3.1, 3.2,
2.5. Item 2.5 confirms "the eight slices", and the count is eight only if items 3.1 and 3.2 both keep
the drafted cut, so those two were decided first.

## Items worked

### 2.2 — The tracker is supported on macOS and Linux, and not on Windows

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed. The tracker runs on macOS and Linux, and Windows is not supported.
  Three additions say what "supported" means for a system nobody checks, and what a reader on the
  wrong system meets.

  *Seat.* This item is the CPO's, and this run answered it in that seat. The edit lands in `SDD.md`
  § 4 RT-3, and `SDD.md` RN-11 gives the reason the call is the CPO's: "which readers the product
  serves is product scope". The answer commits nobody outside the product.
  `system/projects/tracker17/agari.md` says done "does not require tracker17 to be published or tried
  by an outside reader", so no reader on any system is promised anything today. I can name no ground
  the owner holds that this run could not see.

  *The draft's conclusion holds, and its stated reason proves less than it claims.* The draft excludes
  Windows because supporting it "would mean building and testing that second way on a machine the
  owner's check never touches". The owner's check never touches a Linux machine either. The owner's
  machine is macOS (third source above). So "the check does not reach it" cannot be what separates
  Linux from Windows. What separates them is the building. `SDD.md` § 4 RT-1 holds the tracker to
  Python's standard library, and that library gives file locking to Unix systems through one module
  and to Windows through another (first and second sources above). macOS and Linux are both Unix
  systems, so one lock serves both. Windows needs a second one. On this reading, Linux costs the
  reader no extra code to read and Windows does, and that is the real ground. `PRD.md` § Goals makes
  the product "small enough to read end to end", and `SDD.md` § 1 says "Every part this design adds
  is a part the reader has to read."

  *Addition (1), Linux is named and unchecked (check 4, absent).* No run in the Agari's check uses
  Linux. `system/projects/tracker17/project.md` carries "**Execution type:** headless", so the
  pipeline builds on the owner's machine too, and not in a Linux container. The predecessor gives no
  evidence either way: it takes no lock and states no operating system (fourth source above).
  `products/tracker17/docs/trail/sdd/self_answer-1.md` already recorded the same gap from the CTO's
  seat: "nothing here was checked on Linux". The answer to item 2.1 met the same shape of problem
  with the Python floor, kept the declared floor, and added a risk to `SDD.md` § 11 saying nothing
  checks it. This answer does the same for Linux, so the two answers treat an unchecked claim the
  same way. The risk shows up as a setup or a suite failure on a Linux machine. One run of the setup
  instructions and both suites on Linux would settle it, and no slice requires that run. Where the
  risk sits in § 11 and how it is numbered are the CTO's.

  *Addition (2), a reader on the wrong system (check 4, refused).* The reason to expect a poor
  failure on Windows is the lock: a tracker built on the Unix-only module would stop there with
  whatever Python prints when a module is missing. `SDD.md` § 4 OB-2
  promises "one plain message" for a start that cannot proceed, and the answer to item 2.1 already
  scoped that promise to "a start the tracker itself refuses". `UXD.md` UX-F1 says whose failure a
  missing prerequisite is: "the failure is one the instructions already describe, and they say what
  to install or do." So the setup instructions carry it. Their prerequisites section names macOS and
  Linux, says which one the tracker has been checked on, and says Windows is not supported. The
  second of those three statements is what keeps the setup instructions honest with a Linux reader.
  `products/tracker17/docs/CONTENT.md` owns the wording.

  *Addition (3), nothing for Windows.* The tracker holds no code for Windows and no test runs on it.
  This is the draft's own meaning, stated so that a later change does not add a Windows branch in
  passing. The item's *If overridden* field already describes what adding Windows would change.

  *Checked against the settled record (check 3).* No settled document names an operating system.
  A search of `products/tracker17/docs/` for "windows", "macos", "linux", "darwin" and "operating
  system" found matches only in `DESIGN.md`, which names the operating system's own typeface, and in
  three trail reports. `SRS.md` NFR-13 names browsers and no system. `PRD.md` § Success Metrics
  checks setup "on a machine that has only the product's stated prerequisites installed", and the
  operating system is one of those stated prerequisites. No PRD, SRS or UXD sentence has to move.

  *Named and not covered.* A Linux system running inside a Windows machine is Linux for this answer,
  and is as unchecked as any other Linux. What the browser the end-to-end tests drive needs from a
  Linux system was not looked at, by this run or by the run that wrote `SDD.md`. Empty and concurrent
  cases do not arise: the choice of operating system changes neither a first run nor two trackers on
  one location.

  *Close calls.* I weighed overriding to macOS alone, on the ground that this instance does not
  assert what it has not run. I kept Linux because dropping it would turn away readers the product
  is for and save no code, and because addition (2) makes the setup instructions say what was
  checked. A Linux failure that needs code of its own to fix would tip it, and the SDD would then
  record a re-cut. I also weighed raising the Windows exclusion on `PRD.md`, whose § Out of Scope
  does not list it. I did not. Nothing in the PRD is false, and its "stated prerequisites" already
  leave room for the statement. The owner deciding to publish would tip it: `PRD.md` § Assumptions
  says the bars "would need revisiting" for an outside reader, and the exclusion belongs in the PRD
  at that point.

### 3.1 — `delete-and-rename` is its own slice, and not part of `tasks-in-a-project`

- **Bucket:** 3. Cut calls to confirm — where the slicing could reasonably have gone another way
- **Verdict:** confirmed
- **Why:** Keep. `delete-and-rename` stays its own slice, and `tasks-in-a-project` deletes nothing.

  *Seat.* The item asks which order value should arrive in. `SDD.md`, under "Who decides what", gives
  § 5 step 4 and each slice's *Delivers* to the CPO, and says the CTO must not decide "whether a
  slice is worth delivering". The edit, had there been one, would land in `SDD.md` § 6 and § 7 only.

  *The draft holds, and the Agari gives it a stronger reason than the two it states.* The item says
  the alternative "gives the operator a complete task and project editor sooner". Nobody operates
  tracker17 before it is done. `system/projects/tracker17/agari.md` makes done one run-through by the
  owner, and its Works bar is "Key Use Cases 3, 4 and 5 in the browser". `PRD.md` § Key Use Cases 3,
  4 and 5 create, move, narrow, sort, summarise and comment. None of them deletes a task or a
  project, and none renames a project. So what arrives sooner under the alternative is three actions
  the owner's run-through never performs, and what arrives later is every slice that run-through
  does perform. The draft's own two reasons also hold. `tasks-in-a-project` already carries five Core
  Features (`SDD.md` S-2, *Traces to*), and five of the six slices after it wait on it: "Every later
  slice except `protect-saved-data` acts on a task" (`SDD.md` S-2, *Why here in the order*). Deletion carries
  no rule `PRD.md` § Risks marks as new: the features it names as built fresh are "no filtering, no
  sorting, no project summary, and no editing of a task's title".

  *Failure paths (check 4).* Refused: if pages that run no script cannot carry the in-place
  confirmation (`SDD.md` § 11 R-2), the draft finds that out in `status-moves`, on one action.
  The alternative would find it out inside the slice everything else waits on. Stale: a deleted
  task's identity must never be issued again (`SRS.md` FR-15). Task identities "come from a counter
  in the state that only rises" (`SDD.md` § 3, "What the system holds"), and tasks are first created
  in `tasks-in-a-project`. The test for the rule arrives with `delete-and-rename`. On this reading,
  keeping the slices apart leaves no gap in the rule itself.
  Empty and concurrent: a project emptied by deletion shows the no-tasks state that
  `first-project` builds, and an action on something another tab deleted is in this slice's own
  *Reached when*.

  *Not a close call.* An Agari whose run-through deleted or renamed something would tip it. The
  Agari is the CPO's own declaration, and it names no such step.

### 3.2 — People arrives in two halves, and there is no slice for People alone

- **Bucket:** 3. Cut calls to confirm — where the slicing could reasonably have gone another way
- **Verdict:** confirmed
- **Why:** Keep. The assignee list arrives in `tasks-in-a-project`, the operator's name arrives in
  `comment-on-a-task`, and there is no `people` slice.

  *Seat.* The item asks whether a finished screen counts as value on its own. `SDD.md`, under "Who
  decides what", gives § 5 step 2, "Strike the fragments", to the CPO.

  *The draft holds, for the reason it gives.* `SDD.md` § 5 step 1 asks for each entry in the form
  "after this, <someone> can <do something they could not>". After a `people` slice built second,
  the operator could type names into two fields. Nothing would read them: no task exists to assign,
  and no comment exists to sign. The item says so itself: the slice "delivers names that nothing yet
  uses". `SDD.md` § 5 step 2 strikes "every entry whose only value is that a later entry needs it",
  and this is one. The product's bars measure what the operator can do and what the reader can run
  and read (`PRD.md` § Success Metrics). A screen that is complete and does nothing passes neither.
  `UXD.md` § 4 puts the two names on one screen because both "are needed before Key Use Cases 3 and 5
  can finish, so they share one place". That is a reason to share a screen. It is not a reason to
  share a slice.

  *Failure paths (check 4).* Empty: with no assignee on the list, the add-task form offers "none"
  and a link to People (`UXD.md` UX-F3), and People exists by then because it arrives in the same
  slice. With no operator name set, the comment form's notice links to People (`UXD.md` UX-F7), and
  the Your name half arrives in that same slice. So neither half is ever linked to before it exists.
  Stale: between the two slices, People shows the assignee list and nothing about the operator's
  name. `SDD.md` § 4 EX-12 already forbids a link to an area no slice has delivered, and whether a
  screen may be watched arriving in steps is item 2.4, which the CDO answers. This answer does not
  decide it.

  *What follows for the cut below the slice.* The same reasoning binds the Principal PM when it
  divides `tasks-in-a-project` into seeds. `SDD.md` § 8 says each share of *Delivers* "must be worth
  something on its own, or it is a fragment". The assignee list alone is not such a share, for the
  reason it is not a slice.

  *Not a close call.* A use for the operator's name outside comments would tip the second half, and
  `SRS.md` FR-28 gives it none.

### 2.5 — The eight slices: what each delivers, and what each leaves to another

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed. The eight slices, their slugs, their *Delivers* sentences and the
  fences they carry stand. Three additions complete the three fields that say where a slice sits
  against the PRD and the Agari: *Moves toward*, the PRD entries of *Traces to*, and *Not in this
  slice*.

  *Order.* This item was decided after items 3.1 and 3.2, although the companion lists it first. It
  confirms a count of eight, and each of those two items could have changed the count. Both were
  answered keep.

  *Seat.* `SDD.md`, under "Who decides what", gives the CPO each slice's *Slug*, *Delivers*, *Moves
  toward* and *Not in this slice*, and the PRD section of *Traces to*. Every edit this answer asks
  for is in one of those fields.

  *The draft holds as a cut.* I walked `PRD.md` § Core Features against the eight *Delivers*
  sentences. Each of the eleven features the operator uses lands in a slice: Projects in
  `first-project` and `delete-and-rename`; Tasks, Priorities, Assignees, Labels and Due dates in
  `tasks-in-a-project`; Comments in `comment-on-a-task`; Status workflow in `status-moves`;
  Filtering and Sorting in `narrow-and-sort`; Project summary in `project-summary`. The failure
  states of `PRD.md` § UX Notes land in `protect-saved-data`. The twelfth feature, Tested
  throughout, is every slice's, through `SDD.md` § 4 TS-1. Each *Delivers* is in the form `SDD.md`
  § 5 step 1 asks for, and none is an architecture box. Nothing the PRD puts in scope is left with
  no slice.

  *Addition (1), the third bar (the draft is right and incomplete).*
  `system/projects/tracker17/agari.md` has three bars. `grep -n -F "first bar"
  products/tracker17/docs/SDD.md` returned eight lines, one per slice. The same search for "second
  bar" returned one line, in `first-project`. The same search for "third bar" returned none, and
  "Simple to read" appears only in § 1. `grep -n -F "Key Use Cases 2"` on the same file returned
  none. So under the draft no slice says it moves the product toward being simple to read, and no
  slice traces to the reader's own use case. The item's rationale shows the same gap: it maps
  slices to Key Use Cases 1, 3, 4 and 5 and does not mention 2.

  The slices do deliver it. `SDD.md` § 4 TS-3 gives each Core Feature "one entry point in the code",
  the module `domain/<feature word>.py`, whose docstring names the code and tests of the feature.
  Each slice's *Artifact* line says which of those modules exist after it: `domain/projects.py`
  after `first-project`, five more after `tasks-in-a-project`, and so on through
  `domain/summary.py` after `project-summary`. So after `first-project` a reader can already follow
  one feature from the PRD to its code and its tests, which is `PRD.md` § Key Use Cases 2 for that
  feature. `delete-and-rename` adds no module, and its *Artifact* line has the Projects and Tasks
  docstrings name the tests it adds, which completes those two traces. `protect-saved-data` adds
  no feature entry point, so it gains nothing here.

  It matters because of where the field goes. `SDD.md` § 8 says *Moves toward* "repeats" into every
  seed cut from a slice, and adds "a seed that advances no Agari is a finding". Under the draft,
  no seed of tracker17 would ever say it advances the third bar. The product exists so that a
  reader can "read a whole product it built" (`PRD.md` § Blurb), and no seed's statement of what it
  advances would say so.

  *Addition (2), PRD sections delivered and not named.* A search of `SDD.md` for "Refusals say
  why", "Data & Privacy" and "Scope (In)" returned no line. "Out of Scope" appears only in § 1,
  "Tested throughout" only under the table of § 4, and "Defaults" only as the name of a UXD
  paragraph. Each of these PRD sections is delivered by a slice whose *Reached when* already shows
  it. Six slices' *Behaviour* lines show an action refused, and `PRD.md` § UX Notes, Refusals say
  why, names three of those refusals outright: "a move the workflow doesn't allow, a name that
  isn't on the assignee list, and a comment before a name is set". `first-project` delivers the
  setup instructions that `PRD.md` § UX Notes, Failure states, and § Data & Privacy, Deletion, both
  lean on, and its *Command* line includes the test of `SRS.md` AC-10, which serves `PRD.md` § Out
  of Scope, "reachable only from the machine it runs on". `tasks-in-a-project` delivers the overdue
  marking, which is "seeing which tasks are overdue" in `PRD.md` § UX Notes, What must feel
  effortless. The dates half of `PRD.md` § UX Notes, Defaults, first shows in `tasks-in-a-project`
  and `comment-on-a-task`. The addition names the section on the slice. It changes what no slice
  delivers. § Scope (In) is not added, because each of its three lines restates a section already
  traced. The keyboard, English and desktop halves of Defaults are not added to any one slice,
  because `SDD.md` § 4 EX-8 and EX-9 bind every slice to them.

  The cost of leaving the entries out is small today, since the SRS and UXD entries beside them
  carry the same rules. They are added because *Traces to* is how a seed's `## Source` is filled
  (`SDD.md` § 8), and because a PRD section that no slice names cannot be told apart from one the
  cut dropped.

  *Addition (3), the fences.* `PRD.md` § Out of Scope lists five list and task features. The draft
  fences two of them on the slice a reader would expect them in: a summary across projects on
  `project-summary`, and moving a task between projects on `delete-and-rename`. A search of
  `SDD.md` for "more than one value", "more than one field" and "hosted demo" returned no line, and
  "threaded" appears only in § 11 R-4, about the listener. The other three get the same treatment,
  on `comment-on-a-task` and `narrow-and-sort`. `first-project` gains the PRD's "A package, an
  installer, or a hosted demo", because setup is where one would be added, and the answer to item
  2.1 has just given the test suite a virtual environment to set up.

  *Checked against the settled record and this run's other answers (check 3).* The answer to item
  2.1 makes setup two commands, so `first-project` still moves the second bar "in full". The answer
  to item 2.2 puts the supported systems in the setup instructions' prerequisites, which
  `first-project` already delivers. Items 3.1 and 3.2 leave every slug and every *Delivers* as
  drafted. No PRD, SRS or UXD sentence moves.

  *Failure paths (check 4).* Refused: the owner can fail the third bar at the Agari check, and
  nothing in the cut puts the cold read in front of them before the last slice. That is not a gap
  in the cut, because `system/projects/tracker17/agari.md` asks for one run-through at the end. It
  is `PRD.md` § Risks' first risk, and after `first-project` all five parts exist (`SDD.md` S-1,
  *Artifact*), which is the earliest the risk could be looked at. Stale: when a slice turns out to
  be a fragment once its neighbour lands, `SDD.md`, under "Who decides what", gives that re-cut to
  the CPO, and this answer does not pre-empt it. Concurrent: a slice may be cut into several seeds, and
  *Delivers* divides among them. Item 3.2's entry above names the one share that cannot stand
  alone.

  *Not covered.* The order of the slices is the CTO's and is not part of this item. The *Behaviour*
  lines and the UXD entries of *Traces to* are item 2.4's, which the CDO answers.

  *Close calls.* I weighed splitting `tasks-in-a-project`, the broadest slice. I did not: no result
  part-way through it would change what the product builds next, which is the test `SDD.md` § 5
  step 4 sets for "too broad". I also weighed adding the reader's trace to `first-project`'s
  *Delivers* sentence, and left it in *Moves toward*. § 4 TS-3 and TS-4 already bind every slice to
  the trace, and *Delivers* is divided among seeds where *Moves toward* repeats in each.

## Left for the owner

None this run.

## Skipped

- **2.1 — The tracker runs on Python 3.11 or later and uses only the Python standard library when it
  runs** — its slot was already filled when this run reached it. It is left exactly as it stands.
- **2.3 — No page runs a script, so every action reloads a whole page** — not on this run's list.
  It carries `Seat: cdo` and is carried by another seat's run. Its slot is untouched.
- **2.4 — What a person can watch at the end of each slice, as drafted from the UXD** — not on this
  run's list. It carries `Seat: cdo` and is carried by another seat's run. Its slot is untouched.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
