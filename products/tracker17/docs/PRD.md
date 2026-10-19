# PRD — tracker17

**Status:** Settled
**Owner:** CPO
**Version:** 7 — the not-public assumption says how tracker17 becomes public: with kensaiapp's public release, which ships it as an example. At 6: tracker17 has a second purpose, kensaiapp's own testing ground

---

## Blurb

tracker17 is a small task tracker you run on your own machine and use in your browser. It exists so
someone curious about kensaiapp can read a whole product it built, run it, and judge how simple it
was to set up. It is also kensaiapp's own testing ground: building tracker17 with kensaiapp is how
issues in kensaiapp are found and fixed.

## Purpose

tracker17 is a worked example. It is a real, working task tracker, kept small on purpose, so that a
person who wants to see how kensaiapp builds apps has one simple product to read end to end, run
locally, and judge. It is needed now because kensaiapp has no simple example product to point such a
person at.

tracker17 is also kensaiapp's own testing ground. kensaiapp built all of it, much of its definition
included, and kensaiapp has in turn been built by working on tracker17 and the versions before it.
It started as a small command-line application, made as a proof of concept, and tracker16-X is that
command-line predecessor. Once kensaiapp was mature enough, the owner made it a browser app and left
kensaiapp to go on building it. Building tracker17 with kensaiapp, and using what that shows to find
and fix issues in kensaiapp, is the second reason it exists. A reader learns both purposes from the
first thing they read about tracker17. *(confirmed: `trail/prd/cycle-6.md` § 1.1)*

## Problem Statement

A person who is interested in how kensaiapp builds apps has nothing simple to look at. They can read
about the method, but they can't open one small product it produced, check that it works, and see
what it takes to get it running on their own machine. Without that they have to take the method on
trust.

## Why This

- **The nearest alternative is tracker16-X**, the command-line task tracker this product draws its
  task rules from. It works, but it is a terminal tool, and a terminal tool is harder for a casual
  visitor to try out than an app in a browser. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.10)*
- **The other alternative is to read kensaiapp's own rules and documents.** They describe how it
  builds products, but they don't show a finished one.
- **What tracker17 adds** is an app that people recognise as an app, which runs in the browser and
  is defined from the top of kensaiapp's definition chain down. A reader can follow one feature from
  the product definition to its code and its tests. tracker16-X can't show that trace, because its
  definition starts at a feature-level document written from PM requirements and has no PRD above
  it. *(verified (external): `task-tracker-X/docs/fdr.md`, its header, and `task-tracker-X/docs/`, which holds no PRD)*
  *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.10)*
- **Not yet proven:** that a browser app built this way is simpler to read and to set up than the
  command-line predecessor. A web interface adds parts that the terminal tool never needed (see
  Risks).

## Target Users

- **The reader** — a developer who is interested in seeing how kensaiapp builds apps. They come to
  read the code, check that the app works, and see whether it is simple to set up on a machine.
  Until outside readers arrive, the owner stands in for this person.
- **The operator** — the one person who runs tracker17 on their own machine and uses it in the
  browser. The tracker models a small team's work, and team members appear in it as the names that
  tasks are assigned to. Team members don't sign in or use it themselves. One person operates it.
  "A small team" is tracker16-X's own wording, and that tracker works the same way: it has one
  user name, one list of names to assign tasks to, and no accounts. *(verified (external):
  `task-tracker-X/docs/fdr.md` § Description, § 5 Assignees, § 12 User config)* So the phrase never meant
  several people using the tracker. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.1)*

## Goals

- **It is simple.** A reader can take in the whole product, because it is small enough to read end
  to end.
- **It works.** Every core feature below does what it says, in the browser and in the automated
  tests.
- **It is simple to set up.** Someone going from a fresh copy to a working tracker in their browser
  needs only the written instructions.
- **It costs nothing to run, and it earns nothing.** It runs on the operator's machine and uses no
  outside service, paid or free. There is no revenue story, because it is an example rather than a
  business. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.10)*

The full ambition would be a tracker that a team shares over a network, with accounts, live
collaboration, notifications and export. This version deliberately cuts to one person on one
machine, because the product's job is to be readable and runnable rather than to serve a team.

## Success Metrics

All three bars are checked before the product is called done, and again on every later release.
Each bar names the Key Use Cases it checks, and together they cover all five.
*(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.4)*

- **Works** (Key Use Cases 3–5): the owner runs through Key Use Cases 3, 4 and 5 in the browser
  with no error and no wrong result, and the full automated suite passes with all three of its
  layers (unit, integration, end-to-end) present. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.4)*
- **Simple to set up** (Key Use Case 1): the owner starts on a machine that has only the
  product's stated prerequisites installed and works from a fresh copy. Following only the written
  setup instructions, they reach the tracker open in their browser in no more than three commands
  and within ten minutes. Commands joined with `&&` or `;` count as separate commands. Nothing along
  the way asks for an account, a key or a sign-up. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.4)*
- **Simple to read** (Key Use Case 2): the owner reads the code cold and judges it simple. This is
  a pass/fail call by the owner, and no line count stands in for it.
  *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.4)*
  The owner also picks, at the time of the check, any one Core Feature the operator uses, and
  traces it from the product definition to the code that builds it and the tests that check it,
  reaching each through what the definition documents and the code point to, never by searching.
  The trace is a pass/fail call by the owner too.
  *(added — not in the input; confirmed: `trail/prd/cycle-4.md` § 2.1)*

## Key Use Cases

1. A reader gets a copy of tracker17, follows the setup instructions, and has it open in their
   browser.
2. A reader reads the code and its tests, and follows one feature from the product definition to
   where it is built and where it is tested. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.10)*
3. The operator creates a project and adds tasks with a priority, a due date, labels and an
   assignee. They move a task through its status workflow, and they see an invalid move refused
   with a clear reason.
4. The operator narrows a task list by status, priority, assignee, label, due-date range or
   overdue, sorts it, and opens a project summary to see where the project stands.
5. The operator comments on a task, and the comment appears under their name with the time it was
   written.

## Core Features

The task rules below come from tracker16-X, so tracker17 behaves as its predecessor does wherever
both cover a rule. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.3)* The one
exception is **Priorities**, which adds `critical`. *(confirmed: `trail/prd/cycle-5.md` § 1.1)*

- **Projects.** A project has a name, which is unique, and an optional description. Projects can be
  created, listed, renamed and deleted. Deleting a project deletes all of its tasks. A task cannot
  move between projects.
- **Tasks.** A task belongs to one project. It has a title (titles need not be unique), a status, a
  priority, zero or one assignee, any number of labels, an optional due date and comments. Any
  field except status can be edited. Status changes only through the workflow. Tasks can be deleted.
- **Status workflow.** The statuses are `todo`, `in-progress`, `done` and `cancelled`, and a new
  task starts in `todo`. The allowed moves are `todo` → `in-progress` or `cancelled`, and
  `in-progress` → `done`, `cancelled` or back to `todo`. `done` and `cancelled` are final. Any
  other move is refused.
- **Priorities.** A task is `low`, `medium`, `high` or `critical`, and `medium` is the default.
  *(changed — the predecessor's priorities are `low`, `medium` and `high` only; verified (external):
  `task-tracker-X/tasktracker16x/domain/priority.py`,
  `VALID_PRIORITIES`)* *(confirmed: `trail/prd/cycle-5.md` § 1.1)*
- **Assignees.** The operator keeps one list of the people tasks can be assigned to, adding and
  removing names. A task can only be assigned to a name on that list. Removing a name from the list
  leaves it on the tasks that already carry it.
- **Labels.** Labels are free text with no fixed list. Labels can be added to a task and removed
  from it one at a time.
- **Due dates.** A due date is a calendar date with no time. A task is **overdue** when its due date
  is before today and it is neither `done` nor `cancelled`. A task due today is not overdue.
- **Comments.** A comment is text on a task. It records its author and the time it was written
  automatically. The author is the operator's own name, which the operator sets in the app, and a
  comment can't be added until a name is set. If the operator changes their name, comments already
  written keep the name they were written under. *(verified (external):
  `task-tracker-X/tasktracker16x/domain/comment.py`, `Comment`)* *(confirmed: `trail/prd/cycle-2.md` § 2.3)* Comments can't be edited or
  deleted. They show oldest first, as a flat list.
- **Filtering.** A task list can be filtered within one project or across all projects, by status,
  priority, assignee, label, a due-date range with either end optional, or overdue. Each field
  takes one value, and fields combine as AND.
- **Sorting.** A task list sorts by one field at a time: due date, priority, created time or title.
  It sorts ascending or descending, and ascending is the default.
- **Project summary.** For one project, the summary shows the total number of tasks, the count per
  status, the count per priority, the overdue count, and the count of tasks with no due date. It also
  shows each assignee's open tasks (not `done` or `cancelled`), with unassigned tasks counted as
  "(unassigned)".
- **Tested throughout.** The product is built test-first and carries unit, integration and
  end-to-end tests. They are part of what the reader comes to read.

## UX Notes

- **Arrival.** A reader arrives at the written setup instructions. They state the prerequisites and
  the few commands that take a fresh copy to the tracker open in the browser.
  *(added — not in the input; confirmed: `trail/prd/cycle-3.md` § 2.2)* They also say where the tracker keeps its saved data.
  *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.7)*
- **First run.** The tracker opens empty, with no projects and no sample data, and invites the
  operator to create a first project. An empty project invites a first task, and a filter that
  matches nothing says so, rather than showing a blank list. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.8)*
- **What must feel effortless:** moving a task to its next status, seeing which tasks are overdue,
  and narrowing a list to what matters right now. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.8)*
- **The status workflow is visible.** Only the moves allowed from a task's current status are
  offered. A final status (`done`, `cancelled`) offers none. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.8)*
- **Refusals say why.** A refused action leaves nothing changed and tells the operator the reason
  in plain words. Refused actions include a move the workflow doesn't allow, a name that isn't on the
  assignee list, and a comment before a name is set.
- **Failure states.**
  - If the tracker isn't running, the browser can't reach it, and the setup instructions say how to
    start it again. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.8)*
  - If the saved data can't be read, the tracker says so plainly rather than starting empty and
    hiding the operator's work. It never overwrites saved data it couldn't read, so the work stays
    recoverable. The setup instructions say how to set that data aside and start fresh on purpose.
    *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.8)*
- **Persistence.** Everything the operator enters is still there after the tracker is stopped and
  started again on the same machine. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.8)*
- **Defaults:** English only, a desktop browser, dates shown as calendar dates in the machine's local
  day, and every action usable from the keyboard. There is no commitment to a phone layout.
  *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.9)*

## Scope (In)

- Everything under Core Features, used in a browser on the machine it runs on.
- Written setup instructions that take a fresh copy to a running tracker, and that say where the
  saved data is kept and how to set it aside.
- Unit, integration and end-to-end tests.

## Out of Scope

- **Hosting, and use by more than one person over a network.** The tracker is reachable only from
  the machine it runs on. It has no login, so a tracker other machines could open would let anyone
  on that network read, change or delete the operator's data, and the data would no longer stay on
  the machine (Data & Privacy). *(the reachability line is added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.6)*
- **Login, accounts or access control.**
- **Real-time collaboration and notifications.**
- **Export.**
- **Some list and task features:**
  - threaded comment replies
  - filters that take more than one value per field
  - sorting by more than one field
  - moving a task between projects
  - a summary across projects
- **A command-line interface.** The browser is tracker17's only interface. The predecessor's
  command-line mechanics are not carried over: its command names and flags, its relative-date
  shorthand (`+3d`), and its data kept per working directory. tracker17's experience is designed
  for the browser. *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.2)*
- **A package, an installer, or a hosted demo.** tracker17 is offered as source code to be read and
  run. *(added — not in the input; confirmed: `trail/prd/cycle-3.md` § 2.2)*

## Assumptions

- The reader is a developer who is comfortable getting a copy of a code repository and running a few
  commands on their own machine.
- Until there are outside readers, the owner's own reading and setup stand in for theirs. If an
  outside reader would judge "simple" differently, the bars above would need revisiting.
- **tracker17 is not public yet.** No outside reader can reach it today, and it stays that way
  until the owner decides to publish it. It becomes public with kensaiapp's public release, which
  ships tracker17 as an example, when the owner publishes that release. Until then the owner is the
  only reader. *(verified (external), 2026-10-13: the GitHub repository that holds tracker17 is
  private, and so is `kensaiapp/kensaiapp`, the repository the release is published to)* *(the
  release ships tracker17: the owner's decision of 2026-10-11, recorded in
  `docs/findings/2026-10-11_tracker17-ships-in-the-release-and-names-what-must-not-ship.md`)*
  *(added — not in the input; confirmed: `trail/prd/cycle-3.md` § 2.1)*
- The predecessor's task rules are a sound base. The owner's list of features and exclusions mirrors
  them, so carrying them over changes no product decision the owner made.

## Dependencies / Integrations (Conceptual)

- **No outside service.** Nothing needs a login, a payment, an outside API or a network connection
  beyond the machine itself.
- **tracker16-X**, the predecessor. tracker17 draws its task rules from it, and its working code is
  the preferred starting point.

## Data & Privacy

- tracker17 holds names that the operator types in. These are the people on the assignee list, the
  operator's own name, and the comment authors. It also holds the work the operator enters. Nothing
  else is stored about anyone. *(changed — the input answered that no personal data is handled;
  confirmed: `trail/prd/cycle-2.md` § 2.7)*
- **None of it leaves the machine.** Nothing is sent anywhere, and no account exists.
- **Deletion:** the operator removes all of it by deleting the tracker's saved data. No obligation
  beyond the operator's own applies to it. The written setup instructions say where that saved data
  is kept, because deleting it is the only way to remove the names.
  *(added — not in the input; confirmed: `trail/prd/cycle-2.md` § 2.7)*

## Risks

- **A browser app may be less simple than the terminal tool it follows.** A web interface adds parts
  that a command-line tool never needed, and this would show up as a cold read that the owner does
  not judge simple.
- **Part of the feature set is new rather than reused.** The predecessor's working code has no
  filtering, no sorting, no project summary, and no editing of a task's title. *(verified
  (external): `task-tracker-X/tasktracker16x/cli/app.py`, its full
  command set)* Those features are built fresh, so they are where tracker17 is most likely to drift
  from its predecessor's rules.
- **"Small team" can mislead a reader.** A reader may expect several people to use it at once. The
  Target Users and Out of Scope sections are written to prevent that reading.
- **The only judge is the owner.** "Simple" is measured by the owner's own judgement. Until an
  outside reader tries it, that judgement is untested against the person the product is for.

## Open Questions

None.
