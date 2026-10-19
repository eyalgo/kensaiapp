# FDR — tracker17

**Status:** Settled
**Owner:** Principal PM
**Version:** 4 — no behaviour changed from version 3: a task's priority is one of four, `critical` the highest, and for Linux the written instructions give the one-time step that installs the browser's system libraries and name the Linux systems the end-to-end tests run on
**Inputs read:** PRD Settled (version 5) · SRS Settled (version 5) · SDD Settled (version 7) · Agari no Status line (`agari_template.md` carries none) · UXD Settled (version 4; no `products/tracker17/docs/UXD_open_issues.md` beside it; a sibling, read for collisions, not a source) · tracker17 doctrine no Status line (stamped, unfilled) · writing_bar Settled

> The FDR is tracker17's behavioural contract: what the product does, and the product decisions every
> change after it is built against. It is derived from `products/tracker17/docs/PRD.md`,
> `products/tracker17/docs/SRS.md` and `products/tracker17/docs/SDD.md`, and it is read cold by the
> Principal Architect, the PM, the Product Owner and the QA seat. Every entry carries a stable typed
> ID — `R-n` a rule, `PD-n` a product decision, `OOS-n` an out-of-scope entry, `RN-n` a review note.
> An ID is never reused and never renumbered. Every rule and product decision carries an inline trace
> tag naming the upstream document and section it realizes. Module names, file paths and data
> structures are the SDD's, and this document states none of them.

Every `PRD §`, `SRS` and `SDD §` reference below is to the three files named above.

---

## Description

tracker17 is a small task tracker that one operator runs on their own machine and uses in a desktop
browser. It holds projects, the tasks in them, a list of names tasks can be assigned to, labels, due
dates and comments, and it filters, sorts and summarises a project's tasks. It exists as a worked
example: a reader must be able to set it up from its written instructions, see that it works, read
its code, and follow one feature from the product definition to its code and tests (PRD § Purpose,
§ Key Use Cases). The rules below are the behaviour that serves that intent, scoped to the project's
上がり Agari, `system/projects/tracker17/agari.md`.

---

## Rules

### Starting and reaching the tracker

- **R-1:** The tracker is started by one command, which takes no argument and is named in the
  written setup instructions. *(traces to: SRS § 3.1 FR-1; SDD § 4 RT-2)*
- **R-2:** Once the tracker is ready, the console it was started from shows the local address to open
  in the browser and the saved data's location, and shows nothing before them. *(traces to: SRS § 3.1
  FR-1; § 4.5 NFR-8; SDD § 4 OB-2)*
- **R-3:** The tracker answers only requests that come from the machine it runs on. A request from
  any other machine gets no response. *(traces to: SRS § 3.1 FR-2)*
- **R-4:** The tracker always uses the same local address. When something else holds that address,
  the start fails with one plain console message saying so, and the start writes nothing to the saved
  data. *(traces to: SRS § 3.1 FR-3; SDD § 9 TO-6)*
- **R-5:** When a tracker is already running against the saved-data location, a second start refuses
  with one plain console message. The running tracker and the saved data are unaffected. *(traces to:
  SRS § 4.2 NFR-3)*
- **R-6:** A tracker stopped by a crash, a killed process or a power cut does not stop the next start
  against the same location. *(traces to: SRS § 4.2 NFR-3)*
- **R-7:** The running tracker works with the machine's network connection turned off. *(traces to:
  SRS § 8 AC-11; SDD § 4 RT-1)*

### The written setup instructions

- **R-8:** The written setup instructions state the prerequisites, the commands that take a fresh copy
  to the tracker open in the browser, where the saved data is kept, how to start the tracker again
  after it has stopped, how to set the saved data aside and start fresh on purpose, and how to run the
  full automated test suite. *(traces to: SRS § 3.1 FR-4)*
- **R-9:** The prerequisites name Python 3.11 or later and the command that shows the installed
  Python version, and they say what to do when that version is lower. *(traces to: SDD § 4 RT-1)*
- **R-10:** The prerequisites name macOS and Linux as supported, say the tracker has been checked on
  macOS only, and say Windows is not supported. *(traces to: SDD § 4 RT-3)*
- **R-11:** The prerequisites say that setting up the test suite needs a network connection once, to
  fetch the test dependencies and the browser the end-to-end tests drive. *(traces to: SRS § 3.1 FR-4;
  SDD § 4 RT-1, RT-4)*
- **R-12:** The instructions say that, because the saved data is kept out of version control, a clean
  of the copy that removes ignored files deletes the saved data. *(traces to: SRS § 3.1 FR-4)*
- **R-119:** For Linux, the instructions on running the test suite give the one-time step that
  installs the browser together with the system libraries it needs. They say that step uses the
  system's package manager and asks for administrator rights, and that the tracker and the tests that
  do not drive the browser need none of it. *(traces to: SDD § 4 RT-4)*
- **R-120:** The instructions name the Linux systems the end-to-end tests run on, which are the
  systems the pinned version of the browser-driving test dependency supports. *(traces to: SDD § 4
  RT-3, RT-4)*
- **R-13:** From a fresh copy, on a machine with only the stated prerequisites, the instructions take
  the operator to the tracker open in the browser in at most three commands and within ten minutes.
  Commands joined with `&&` or `;` count as separate commands. *(traces to: SRS § 7 C-7)*
- **R-14:** No step in setup or in use asks for an account, a key, a sign-up or a payment. *(traces to:
  SRS § 7 C-2)*

### Saved data

- **R-15:** Everything the operator enters is still present after the tracker is stopped and started
  again on the same machine. *(traces to: SRS § 3.2 FR-5)*
- **R-16:** The saved data lives in one location inside the operator's copy of tracker17. The location
  does not depend on the directory the start command was run from, and the saved data is never
  committed to version control. *(traces to: SRS § 3.2 FR-6)*
- **R-17:** When no saved data exists, the tracker starts empty, with no projects and no sample data.
  *(traces to: SRS § 3.2 FR-7)*
- **R-18:** The tracker reports an action as done only after its result is in the saved data. When
  the save fails, the action is reported as failed and the tracker's state is the state from before
  the action. *(traces to: SRS § 3.2 FR-9; SDD § 4 SD-2)*
- **R-19:** When the tracker is stopped part-way through saving, by a crash, a killed process or a
  power cut, the saved data afterwards reads as the state either before or after that action, and
  never as a mix of the two. *(traces to: SRS § 4.2 NFR-2)*
- **R-20:** The saved data is read once, at start. A change made to the saved data from outside the
  tracker while it runs is not shown, and the tracker's next save replaces it. *(traces to: SDD § 4
  SD-1; § 9 TO-4)*
- **R-21:** At start, saved data counts as unreadable when the tracker cannot read all of it, or when
  it breaks a data rule. The breaks include an unknown status or priority, a task whose project does
  not exist, two projects with one name, a reused task identity, and a value longer than the maximum
  R-76 sets for its field. *(traces to: SRS § 6 DR-6; SDD § 4 SD-5)*
- **R-22:** Saved data that holds a value an action of the tracker refuses to create — a blank
  required name, title or comment text, an empty label, an over-long value, or a duplicate project or
  assignee name — counts as unreadable under R-21. *(traces to: SRS § 6 DR-6; SDD § 4 SD-5)*
- **R-23:** The tracker never loads part of the saved data and drops the rest. *(traces to: SRS § 6
  DR-6)*
- **R-24:** When the saved data is unreadable, the console says so and names the data's location.
  *(traces to: SRS § 3.2 FR-8; § 5.1)*
- **R-25:** When the saved data is unreadable, every page the tracker serves says plainly that the
  saved data could not be read, names its location, and presents no empty tracker. *(traces to: SRS
  § 3.2 FR-8; SDD § 3 SM-6)*
- **R-26:** While the saved data is unreadable, the tracker offers no action and no navigation into
  any other area. *(traces to: SRS § 3.2 FR-8; SDD § 4 EX-12)*
- **R-27:** The tracker never writes to, replaces or deletes saved data it could not read. *(traces to:
  SRS § 3.2 FR-8; SDD § 4 SD-4)*
- **R-28:** After the operator sets the saved data aside as the instructions describe, the next start
  is empty, and the set-aside data still holds the earlier work. *(traces to: SRS § 8 AC-8)*
- **R-29:** The saved data holds only projects, tasks, comments, the assignee list and the operator's
  name, with the fields SRS § 6 DR-1 to DR-5 name. It holds nothing else about any person, and no record of
  requests, addresses or usage. *(traces to: SRS § 4.3 NFR-6; § 6 DR-1 to DR-5)*

### Projects

- **R-30:** The operator creates a project with a name and an optional description. *(traces to: SRS
  § 3.3 FR-10)*
- **R-31:** A project name with no non-whitespace character is refused. *(traces to: SRS § 3.3 FR-10)*
- **R-32:** A project name already used by another project is refused. Names are compared exactly, so
  `Alpha` and `alpha` are different names. *(traces to: SRS § 3.3 FR-10)*
- **R-33:** The operator lists all projects. *(traces to: SRS § 3.3 FR-11)*
- **R-34:** The operator renames a project. The new name follows R-31 and R-32. Renaming a project to
  the name it already has is not refused. *(traces to: SRS § 3.3 FR-12)*
- **R-35:** Renaming a project leaves its tasks unchanged, and the project's pages keep their
  addresses. *(traces to: SRS § 3.3 FR-12; SDD § 3, What the system holds)*
- **R-36:** A project's description is set when the project is created, and no action changes it
  afterwards. *(traces to: PRD § Core Features, Projects; SRS § 3.3 FR-10 to FR-13)*
- **R-37:** The operator deletes a project. Deleting a project deletes all of its tasks and their
  comments, in one change. *(traces to: SRS § 3.3 FR-13; SDD § 3, What the system holds)*
- **R-38:** Deleting a project leaves the assignee list and the operator's name unchanged. *(traces to:
  SRS § 6 DR-1, DR-4, DR-5)*

### Tasks

- **R-39:** The operator creates a task within a project. A task has a title, a priority, zero or one
  assignee, any number of labels and an optional due date. *(traces to: SRS § 3.4 FR-15)*
- **R-40:** A task title with no non-whitespace character is refused. Titles need not be unique.
  *(traces to: SRS § 3.4 FR-15)*
- **R-41:** A new task starts in status `todo`. *(traces to: SRS § 3.4 FR-15)*
- **R-42:** A task created with no priority given has priority `medium`. *(traces to: SRS § 3.4
  FR-15)*
- **R-43:** The tracker records when a task was created, and keeps the order tasks were created in
  independently of that recorded time. Two tasks created within the same recorded instant still have a
  fixed order. *(traces to: SRS § 3.4 FR-15)*
- **R-44:** Each task gets an identity that is unique across all projects and is never reused, even
  after the task is deleted and the tracker restarted. *(traces to: SRS § 3.4 FR-15; SDD § 3, What the
  system holds)*
- **R-45:** The operator edits a task's title, priority, assignee, labels and due date. The assignee
  is set to a name on the list or cleared. The due date is set, changed or cleared. *(traces to: SRS
  § 3.4 FR-16)*
- **R-46:** A task's fields other than status can be edited whatever the task's status, `done` and
  `cancelled` included. *(traces to: PRD § Core Features, Tasks; SRS § 3.4 FR-16)*
- **R-47:** Saving a task's edit form changes only the fields the operator changed on that page. A
  field left as the page showed it keeps whatever value is saved at the moment the edit is applied.
  *(traces to: SRS § 4.2 NFR-3; § 7 C-5)*
- **R-115:** In a save of a task's edit form, a field counts as changed when the value submitted for
  it differs from the value the page showed. It is not compared with the value saved at the moment
  the edit is applied. *(traces to: SRS § 4.2 NFR-3; § 7 C-5; SDD § 4 RT-7)*
- **R-116:** A save of a task's edit form in which no field changed changes nothing and is not
  refused. *(traces to: SRS § 4.2 NFR-3; § 7 C-5)*
- **R-117:** When any changed field in a save of a task's edit form is refused, the save changes no
  field. *(traces to: SRS § 3.12 FR-39)*
- **R-48:** An edit that leaves a task's assignee unchanged keeps an assignee name that is no longer
  on the list, and is not refused for it. *(traces to: SRS § 6 DR-2; § 3.6 FR-21, FR-22; SDD § 4
  RT-7)*
- **R-118:** Changing the assignee of a task that carries a name no longer on the list, to a listed
  name or to none, replaces that name. The replaced name cannot be set on any task again while it is
  off the list. *(traces to: SRS § 3.6 FR-21; § 6 DR-2)*
- **R-49:** No action moves a task from one project to another. *(traces to: SRS § 3.3 FR-14)*
- **R-50:** The operator deletes a task. Deleting a task deletes its comments. *(traces to: SRS § 3.4
  FR-17)*
- **R-51:** A priority other than `low`, `medium`, `high` or `critical`, or a due date that is not a
  valid calendar date, is refused. *(traces to: SRS § 3.4 FR-15; § 7 C-5; § 6 DR-6)*

### Status workflow

- **R-52:** A task's status changes only through a workflow move. No action sets a status directly.
  *(traces to: SRS § 3.5 FR-18)*
- **R-53:** The allowed moves are `todo` → `in-progress` or `cancelled`, and `in-progress` → `done`,
  `cancelled` or `todo`. *(traces to: SRS § 3.5 FR-18)*
- **R-54:** `done` and `cancelled` are final. A task in either has no allowed move. *(traces to: SRS
  § 3.5 FR-18)*
- **R-55:** Any other move, a move to the status the task already has included, is refused with the
  reason. *(traces to: SRS § 3.5 FR-18)*
- **R-56:** For a given task, the tracker offers only the moves allowed from its current status. A
  task in `done` or `cancelled` is offered none. *(traces to: SRS § 3.5 FR-19; SDD § 4 EX-7)*

### Assignees and the operator's name

- **R-57:** The operator keeps one list of names tasks can be assigned to, and adds a name, removes a
  name and sees the list. *(traces to: SRS § 3.6 FR-20)*
- **R-58:** An assignee name with no non-whitespace character is refused. A name already on the list
  is refused, compared exactly. *(traces to: SRS § 3.6 FR-20)*
- **R-59:** Removing a name that is not on the list is refused with the reason. *(traces to: SRS § 7
  C-5; § 4.2 NFR-3)*
- **R-60:** A task can be assigned only to a name on the list. Any other name is refused with the
  reason. *(traces to: SRS § 3.6 FR-21)*
- **R-61:** Removing a name from the list leaves that name on every task that already carries it.
  *(traces to: SRS § 3.6 FR-22)*
- **R-62:** The operator sets their own name, and changes it later. A name with no non-whitespace
  character is refused. Once set, the operator's name is never unset. *(traces to: SRS § 3.9 FR-27;
  § 6 DR-5)*

### Labels

- **R-63:** The operator adds a label to a task, or removes one, one label at a time. *(traces to: SRS
  § 3.7 FR-23)*
- **R-64:** A label is free text, stored exactly as typed and compared exactly. Only the empty label is
  refused, so a label of spaces only is accepted. *(traces to: SRS § 3.7 FR-23; § 7 C-5)*
- **R-65:** Adding a label the task already carries leaves the task unchanged and is not refused.
  *(traces to: SRS § 3.7 FR-23)*
- **R-66:** Removing a label the task does not carry is refused with the reason. *(traces to: SRS § 7
  C-5; § 4.2 NFR-3)*

### Due dates and overdue

- **R-67:** A due date is a calendar date with no time of day. *(traces to: SRS § 3.8 FR-24)*
- **R-68:** A task is overdue when its due date is before today and its status is neither `done` nor
  `cancelled`. A task due today is not overdue. *(traces to: SRS § 3.8 FR-25)*
- **R-69:** "Today" is the machine's local calendar date at the moment the tracker produces the list,
  the summary or the filter result that shows the overdue state. *(traces to: SRS § 3.8 FR-25)*
- **R-70:** Every task shown in a list shows whether it is overdue. *(traces to: SRS § 3.8 FR-26)*

### Comments

- **R-71:** The operator adds a comment to a task. Comment text with no non-whitespace character is
  refused. A comment added before the operator has set a name is refused with the reason. *(traces to:
  SRS § 3.9 FR-28)*
- **R-72:** A comment records the operator's current name as its author and the moment it was
  written. Changing the operator's name later leaves every existing comment with the name it was
  written under. *(traces to: SRS § 3.9 FR-28, FR-30)*
- **R-73:** A task's comments show oldest first, as one flat list, each with its author and the time
  it was written in the machine's local time. *(traces to: SRS § 3.9 FR-29; § 4.7 NFR-14)*
- **R-74:** No action edits or deletes a comment. A comment is removed only with its task or its
  project. *(traces to: SRS § 3.9 FR-29; § 3.3 FR-13; § 3.4 FR-17)*
- **R-75:** A comment can be added to a task in any status. *(traces to: PRD § Core Features,
  Comments; SRS § 3.9 FR-28)*

### Length of typed text

- **R-76:** A project name, a task title, an assignee name, the operator's name and a label each take
  at most 200 characters. A project description and a comment each take at most 4,000 characters.
  *(traces to: SRS § 3.13 FR-40)*
- **R-77:** One character is one Unicode code point, counted on the value as it is saved, spaces
  included. A line break counts as one character. *(traces to: SDD § 4 RT-10)*
- **R-78:** A longer value is refused with the reason, and the tracker never shortens a value to make
  it fit. *(traces to: SRS § 3.13 FR-40)*
- **R-79:** A value that the tracker's own field let the operator enter is never refused as too long.
  *(traces to: SRS § 3.13 FR-40)*
- **R-80:** The tracker saves a typed value exactly as it was typed, surrounding spaces included,
  except that a line break is saved as one character. *(traces to: SRS § 3.7 FR-23; SDD § 4 RT-10)*

### Task lists, filtering and sorting

- **R-81:** The operator views a task list for one project, or across all projects. A list across all
  projects shows each task's project. *(traces to: SRS § 3.10 FR-31)*
- **R-82:** The operator filters a task list by any combination of status, priority, assignee, label,
  a due-date range and overdue. Each field takes one value, and the fields combine as AND. *(traces
  to: SRS § 3.10 FR-32)*
- **R-83:** A label filter matches a task carrying exactly that label. *(traces to: SRS § 3.10 FR-32)*
- **R-84:** The assignee filter accepts only a name on the current assignee list. A name not on the
  list is refused with the reason. *(traces to: SRS § 3.10 FR-33)*
- **R-85:** The due-date range has a from-date and a to-date, and either may be left out. A task
  matches when its due date is on or after the from-date and on or before the to-date. *(traces to:
  SRS § 3.10 FR-34)*
- **R-86:** A task with no due date matches no range that has at least one end set. *(traces to: SRS
  § 3.10 FR-34)*
- **R-87:** A range whose from-date is later than its to-date is refused, with a reason saying the
  dates are the wrong way round, and no result is shown in its place. *(traces to: SRS § 3.10 FR-34)*
- **R-88:** The overdue filter shows only tasks that are overdue under R-68. *(traces to: SRS § 3.10
  FR-35)*
- **R-89:** The operator sorts a task list by one field at a time: due date, priority, created time or
  title. The direction is ascending or descending, and ascending applies when no direction is chosen.
  *(traces to: SRS § 3.10 FR-36)*
- **R-90:** Priority ascending runs `low`, `medium`, `high`, `critical`, and descending runs
  `critical`, `high`, `medium`, `low`. *(traces to: SRS § 3.10 FR-36)*
- **R-91:** In a sort by due date, tasks with no due date come last in either direction. *(traces to:
  SRS § 3.10 FR-36)*
- **R-92:** A sort by title is alphabetical and ignores letter case. *(traces to: SRS § 3.10 FR-36)*
- **R-93:** Tasks equal on the chosen sort field keep the order they were created in (R-43). A sort by
  created time follows that same order, so it comes out the same way every time. *(traces to: SRS
  § 3.10 FR-36)*
- **R-94:** A list's filter and sort choices are carried in the list page's address and are stored
  nowhere else. *(traces to: SDD § 4 EX-3)*
- **R-95:** When there are no projects, the tracker says so and invites the operator to create one.
  An empty project invites a first task. A filter that matches nothing says that nothing matched. No
  empty list shows as a blank space. *(traces to: SRS § 3.10 FR-37)*

### Project summary

- **R-96:** For one project, the summary shows the total number of tasks, the count for each of the
  four statuses, the count for each of the four priorities, the overdue count under R-68, and the
  count of tasks with no due date. A zero count is shown. *(traces to: SRS § 3.11 FR-38)*
- **R-97:** The summary shows each assignee's open tasks, where an open task is neither `done` nor
  `cancelled`. *(traces to: SRS § 3.11 FR-38)*
- **R-98:** The per-assignee part has one row for every name on the current assignee list, a zero
  included, one row for each name not on the list that an open task in the project still carries, and
  always one row for "(unassigned)". *(traces to: SRS § 3.11 FR-38)*
- **R-99:** The overdue state agrees across the list marking, the overdue filter and the summary's
  overdue count for the same task on the same day. *(traces to: SRS § 8 AC-13)*

### Refusals, stale pages and failures

- **R-100:** Every refused action leaves the saved data unchanged and tells the operator the reason in
  plain words. *(traces to: SRS § 3.12 FR-39)*
- **R-101:** Each page shows the data as it stood when the page was loaded, and no page updates
  itself. *(traces to: SRS § 4.2 NFR-3)*
- **R-102:** Every action is checked against the saved data at the moment it is applied, not against
  what the page showed. An action that is no longer valid, such as a status move on a task another
  browser tab has already moved, is refused with the reason. *(traces to: SRS § 4.2 NFR-3)*
- **R-103:** An action on a project or task that no longer exists is refused with the reason and
  changes nothing. *(traces to: SRS § 4.2 NFR-3)*
- **R-104:** A plain field edit made from a stale page replaces whatever another tab saved for that
  field, and is not refused. *(traces to: SRS § 4.2 NFR-3)*
- **R-105:** An address for a project or task that does not exist shows a not-found page. *(traces
  to: SDD § 4 EX-13)*
- **R-106:** Only a form submission changes the tracker's data. Following a link, reloading a page, or
  going back or forward never changes it and never repeats an action. *(traces to: SDD § 4 RT-8)*
- **R-107:** When an action fails for a reason that is not a refusal, the console shows a message
  naming the action and the error. The browser tells the operator in plain words that the action
  failed, and the saved data is unchanged. *(traces to: SRS § 4.5 NFR-8)*
- **R-108:** No page shows error text produced by the programming language. *(traces to: SDD § 4
  OB-3)*
- **R-109:** The tracker writes only to the console it was started from. It keeps no log file.
  *(traces to: SDD § 4 OB-1; SRS § 4.3 NFR-6)*

### Protection of the operator's data

- **R-110:** A web page from any other origin, open in the operator's browser, cannot read, change or
  delete tracker data. A request that does not come from the tracker's own pages is refused, and the
  refusal changes nothing. *(traces to: SRS § 4.3 NFR-4)*
- **R-111:** While the tracker runs, nothing is sent off the machine. The tracker makes no outbound
  network request, its pages load nothing from outside the machine, and there is no telemetry, usage
  reporting or update check. *(traces to: SRS § 4.3 NFR-5)*
- **R-112:** Text the operator typed is shown as text on every page, so a value containing `<` or `&`
  displays as typed and changes nothing around it. *(traces to: SDD § 4 SEC-4; § 11 R-3)*

### Use of the interface

- **R-113:** Every action in Key Use Cases 3, 4 and 5 can be done from the keyboard alone. *(traces to:
  SRS § 4.7 NFR-12)*
- **R-114:** Due dates show as calendar dates. *(traces to: SRS § 4.7 NFR-14)*

---

## Product decisions

- **PD-1:** tracker17 runs on the operator's own machine and is never hosted. *(traces to: SRS § 7
  C-1)*
- **PD-2:** The browser is tracker17's only interface. There is no command-line interface and no
  programmatic interface for outside use, and the exchange between the tracker's pages and the
  tracker is not a supported surface. *(traces to: SRS § 7 C-3; § 5.2)*
- **PD-3:** tracker17 uses no outside service at run time, paid or free, and nothing in it needs a
  login, a payment or an outside API. *(traces to: SRS § 7 C-2; § 5.3)*
- **PD-4:** tracker17 is offered as source code to read and run. There is no package, installer or
  hosted demo. *(traces to: SRS § 7 C-4)*
- **PD-5:** tracker17's task rules are tracker16-X's wherever both products cover a rule, with one
  exception: tracker17 has the four priorities R-51 names, where tracker16-X has `low`, `medium` and
  `high` only. Any other departure from a tracker16-X rule is a change to this document. tracker16-X's
  working code at `task-tracker-X` is the preferred starting point. *(traces to: SRS § 7 C-5; PRD
  § Core Features, preamble and Priorities)*
- **PD-6:** The tracker runs on Python 3.11 or later and needs nothing beyond Python's standard library
  to run. Only the automated tests have dependencies. *(traces to: SDD § 4 RT-1, RT-4)*
- **PD-7:** Every declared dependency is fixed to an exact version, so a fresh copy set up later gets
  the versions the suite last passed with. *(traces to: SRS § 7 C-8; SDD § 4 RT-4)*
- **PD-8:** The supported operating systems are macOS and Linux. Windows is not supported, and nothing
  is built or tested for it. The tracker runs on any Linux with Python 3.11 or later. The end-to-end
  tests run only on the Linux systems R-120 names, and on any other Linux the tracker and the tests
  that do not drive the browser still run. *(traces to: SDD § 4 RT-3, RT-4)*
- **PD-9:** The supported browsers are current stable desktop Chrome and other Chromium-based
  browsers. The interface is in English and is built for a desktop browser. *(traces to: SRS § 4.7
  NFR-13)*
- **PD-10:** The tracker's address is fixed and the start command takes no option. *(traces to: SDD
  § 9 TO-6)*
- **PD-11:** What a page says about the last action travels in that page's address. An address
  reopened after an action shows that action's line again, and text typed into a refused form is
  recorded in the browser's history. After a refusal for an over-long value, the page gives the
  reason and not the typed text. *(traces to: SDD § 4 RT-8; § 9 TO-7)*
- **PD-12:** The product is built test-first, and its automated suite has three layers: unit,
  integration and end-to-end. The end-to-end layer drives the tracker through the browser interface
  in Chromium. *(traces to: SRS § 7 C-6; § 4.6 NFR-11; SDD § 4 RT-4)*
- **PD-13:** For every Core Feature the operator uses, a reader reaches the code that builds it and
  the tests that check it from the product definition documents, by following what the documents and
  the code point to, without searching. *(traces to: SRS § 4.6 NFR-9)*
- **PD-14:** The code and tests stay small and plain enough for the owner, reading cold, to judge the
  product simple. No line count or size metric stands in for that judgement. *(traces to: SRS § 4.6
  NFR-10)*
- **PD-15:** The task rules, the browser interface and the saved data are each replaceable
  independently of the other two. The source of the current date and time is replaceable, so that a
  test sets today's date. *(traces to: SDD § 3, The seams; § 2, force 4)*
- **PD-16:** There is no identity and no permission check, because there is one operator. No change
  adds a user, a role or a login. *(traces to: SDD § 4 SEC-1; SRS § 4.4 NFR-7)*

---

## Out of scope

- **OOS-1:** Publishing tracker17, or a trial by an outside reader. The Agari's done does not require
  it. *(traces to: `system/projects/tracker17/agari.md`, "What this Agari does not require")*
- **OOS-2:** Re-checking the three bars on every later release. The Agari calls that upkeep after
  done. *(traces to: `system/projects/tracker17/agari.md`, "What this Agari does not require")*
- **OOS-3:** Hosting, and use by more than one person over a network. *(traces to: PRD § Out of
  Scope)*
- **OOS-4:** Login, accounts or access control. *(traces to: PRD § Out of Scope)*
- **OOS-5:** Real-time collaboration and notifications. *(traces to: PRD § Out of Scope)*
- **OOS-6:** Export. *(traces to: PRD § Out of Scope)*
- **OOS-7:** Threaded comment replies. *(traces to: PRD § Out of Scope)*
- **OOS-8:** Filters that take more than one value per field, and sorting by more than one field.
  *(traces to: PRD § Out of Scope)*
- **OOS-9:** Moving a task between projects. R-49 states the absence. *(traces to: PRD § Out of
  Scope)*
- **OOS-10:** A summary across projects. *(traces to: PRD § Out of Scope)*
- **OOS-11:** A command-line interface, including tracker16-X's command names and flags, its
  relative-date shorthand (`+3d`) and its data kept per working directory. *(traces to: PRD § Out of
  Scope; SRS § 7 C-3)*
- **OOS-12:** A package, an installer or a hosted demo. *(traces to: PRD § Out of Scope)*
- **OOS-13:** Running on Windows. *(traces to: SDD § 4 RT-3)*
- **OOS-14:** A phone layout. *(traces to: SRS § 4.7 NFR-13)*
- **OOS-15:** Editing a project's description after the project is created. R-36 states the rule.
  *(traces to: PRD § Core Features, Projects)*
- **OOS-16:** Unreadable saved data found while the tracker runs. Saved data is read only at start
  (R-20), so no rule here covers a read failure mid-run. *(traces to: SDD § 9 TO-4)*

---

## Examples

| Input / Scenario | Expected behaviour | Rule |
|---|---|---|
| A task in `todo`, the operator asks to move it to `done` | Refused with the reason. The task stays in `todo`. | R-53, R-55 |
| A task in `in-progress`, moved to `todo` | Accepted. The task is in `todo`. | R-53 |
| A task in `in-progress`, the operator asks to move it to `in-progress` | Refused with the reason. | R-55 |
| A task in `cancelled` | No move is offered for it. | R-54, R-56 |
| A task in `done`, the operator changes its title | Accepted. The status stays `done`. | R-46 |
| Today is 2026-10-06. Task A is due 2026-10-05 in `todo`, task B is due 2026-10-06 in `todo`, task C is due 2026-10-05 in `done` | Only A is overdue. The list marks only A, the overdue filter returns only A, and the summary's overdue count is 1. | R-68, R-99 |
| Project `Alpha` exists, the operator creates `alpha` | Accepted. Names are compared exactly. | R-32 |
| Project `Alpha` exists, the operator creates `Alpha ` with a trailing space | Accepted as a different name. The name is saved with its trailing space. | R-32, R-80 |
| Project `Alpha` renamed to `Alpha` | Not refused. Nothing changes. | R-34 |
| Label `   ` (spaces only) added to a task | Accepted and stored as typed. | R-64 |
| Label `bug` added to a task that already carries `bug` | Not refused. The task carries `bug` once. | R-65 |
| Filter label `Bug` on a list where tasks carry `bug` | Nothing matches. | R-83 |
| `carol` removed from the assignee list while task T carries `carol` | T still shows `carol`. A filter by assignee `carol` is refused, because `carol` is not on the list. | R-61, R-84 |
| `carol` removed from the list, task T carries `carol`, the operator changes T's title | Accepted. T keeps `carol`. | R-47, R-48 |
| `carol` removed from the list, task T carries `carol`, the operator changes T's assignee to `alice` | Accepted. T carries `alice`, and `carol` cannot be set on T again while `carol` is off the list. | R-118 |
| Tab 1 shows task T with priority `low`. Tab 2 saves priority `high`. Tab 1 changes only T's title and saves | Accepted. T has the new title and priority `high`. | R-47, R-115 |
| Tab 1 shows task T with priority `low`. Tab 2 saves priority `high`. Tab 1 changes T's priority to `medium` and saves | Accepted. T has priority `medium`. | R-104, R-115 |
| The operator saves a task's edit form without changing any field | Not refused. Nothing changes. | R-116 |
| The operator blanks a task's title and changes its priority in one save | Refused with the reason. Neither the title nor the priority changes. | R-117, R-40 |
| Due-date range from 2026-10-10 to 2026-10-01 | Refused with a reason saying the dates are the wrong way round. No "nothing matched" result is shown. | R-87 |
| Due-date range from 2026-10-01 with no to-date, task with no due date | The task does not match. | R-86 |
| Sort by due date descending, tasks due 2026-10-01, 2026-10-09 and none | 2026-10-09, then 2026-10-01, then the undated task. | R-91 |
| Sort by title ascending, titles `beta`, `Alpha`, `alpha` created in that order | `Alpha`, `alpha`, `beta`. `Alpha` and `alpha` keep creation order. | R-92, R-93 |
| Summary of a project with one open task assigned to `dan`, where `dan` was removed from the list, and an empty assignee list | One row for `dan` with 1, and one row for "(unassigned)" with 0. | R-98 |
| A comment of 4,000 characters containing line breaks, entered through the comment field | Saved in full. Not refused and not shortened. | R-77, R-79 |
| A comment submitted before any operator name is set | Refused with the reason. The comment is not saved. | R-71 |
| Tab 1 shows task T in `todo`. Tab 2 moves T to `in-progress`. Tab 1 then asks to move T to `cancelled` | Accepted, because `in-progress` → `cancelled` is allowed against the saved state. | R-102 |
| Tab 1 shows task T in `todo`. Tab 2 moves T to `cancelled`. Tab 1 then asks to move T to `in-progress` | Refused with the reason. T stays `cancelled`. | R-102 |
| Tab 2 deletes task T, then tab 1 adds a comment to T | Refused with the reason. Nothing changes. | R-103 |
| The operator reloads the page that answered a task creation | No second task is created. | R-106 |
| The saved data holds a task whose project does not exist | The start shows the unreadable-data message naming the location, every page says the data could not be read, and the saved data's bytes are unchanged. | R-21, R-25, R-27 |

---

## FDR Review Notes

- **RN-1:** *(added)* R-34's second sentence: renaming a project to the name it already has is not
  refused — *because* SRS § 3.3 FR-10 refuses "A name already used by another project", and a
  project's own name is not used by another project. *(re: R-34; source: SRS § 3.3 FR-10, FR-12)*
- **RN-2:** *(added)* R-36: a project's description is fixed at creation — *because* PRD § Core
  Features, Projects names the project actions as "created, listed, renamed and deleted", and SRS
  FR-10 to FR-13 state those four and no other. On this reading no description edit exists, and the
  rule states the absence so that a builder does not add one. *(re: R-36, OOS-15; source: PRD § Core
  Features, Projects; SRS § 3.3)*
- **RN-3:** *(added)* R-38: deleting a project leaves the assignee list and the operator's name
  unchanged — *because* SRS § 6 DR-1 says a project owns its tasks, and DR-4 and DR-5 hold the
  assignee list and the operator's name outside any project. *(re: R-38; source: SRS § 6)*
- **RN-4:** *(added)* R-46 and R-75: a task's fields can be edited, and a comment added, whatever the
  task's status — *because* PRD § Core Features, Tasks says "Any field except status can be edited",
  and neither the PRD nor the SRS limits editing or commenting by status. A final status bars only
  further moves (SRS FR-18). *(re: R-46, R-75; source: PRD § Core Features, Tasks, Comments; SRS
  § 3.4 FR-16, § 3.9 FR-28)*
- **RN-5:** *(added)* R-47 and R-48: what a save of the task's edit form writes, and what it does with
  an assignee name no longer on the list — confirmed choices, answered in
  `products/tracker17/docs/trail/fdr/cycle-1.md` §§ 2.1 and 2.2 — *because* SRS § 4.2 NFR-3 limits a
  stale plain field edit to replacing "whatever the other tab saved for that field", and SRS § 7 C-5
  carries tracker16-X's rule, which writes each field on its own path: its `update_task_priority`
  reads "a priority-only change leaves the assignee intact"
  (`task-tracker-X/tasktracker16x/application/task_service.py`).
  SRS § 6 DR-2 says an assignee name "stays valid after the name leaves the assignee list (FR-22)",
  and tracker16-X checks the list only when an assignee is given (`update_task_assignee`, same file).
  The answer's reasoning is `products/tracker17/docs/trail/fdr/self_answer-1.md`. *(re: R-47, R-48;
  source: SRS § 4.2 NFR-3; § 7 C-5; § 6 DR-2; § 3.6 FR-21, FR-22)*
- **RN-12:** *(added)* R-115, R-116, R-117 and R-118: when a field of the edit form counts as changed,
  that a save changing nothing is not refused, that a save with a refused field changes no field, and
  that changing an unlisted assignee replaces it — owner directives, the additions in
  `products/tracker17/docs/trail/fdr/cycle-1.md` § 2.1 (2) and § 2.2 (2). R-116 matches R-34 and R-65,
  which refuse no other action that changes nothing, and R-117 applies R-100 to the form as one
  action. The same answer names a collision with `products/tracker17/docs/UXD.md` UX-F9, whose edit
  form offered only a listed name or none and read as refusing the save of a task carrying an
  unlisted assignee, which R-48 does not refuse. How the form shows that name is the UXD's to state,
  and the answer routed it to the UXD's own companion. UXD version 4's UX-F9 keeps a name left as the
  page showed it, and SDD § 4 RT-7 states the same save, so the collision is closed. *(re: R-115,
  R-116, R-117, R-118, R-48; source: `products/tracker17/docs/trail/fdr/cycle-1.md` §§ 2.1, 2.2; SRS
  § 3.12 FR-39; § 3.6 FR-21; SDD § 4 RT-7)*
- **RN-6:** *(added)* R-51, R-59 and R-66: a priority outside the four SRS FR-15 names, a due date
  that is not a calendar date, removing an unlisted assignee name, and removing a label the task does
  not carry are each refused — *because* SRS § 7 C-5 makes tracker16-X's rules tracker17's wherever
  both cover one, and tracker16-X refuses each: `task-tracker-X/tasktracker16x/domain/errors.py`
  defines `UnknownPriorityError`, `InvalidDueDateError`, `UnknownAssigneeError` ("an operation targets
  an assignee name not present in the global list") and `LabelNotFoundError` ("removing a label that
  is not present on the task"). The browser offers these actions only on values that exist, so on
  this reading each refusal arises from a stale page (SRS NFR-3) or a request the tracker's own pages
  did not send. C-5 takes over tracker16-X's refusal of an unknown priority and not its three-value
  set, which is C-5's one exception. *(re: R-51, R-59, R-66; source: SRS § 7 C-5, § 3.4 FR-15, § 4.2
  NFR-3, § 6 DR-6)*
- **RN-7:** *(added)* R-62's last sentence: once set, the operator's name is never unset — *because*
  SRS § 6 DR-5 holds "One name, or no name until the operator sets one", and SRS FR-27 lets the
  operator set and change the name, with no action that clears it. *(re: R-62; source: SRS § 6 DR-5;
  § 3.9 FR-27)*
- **RN-8:** *(added)* R-64's second sentence: a label of spaces only is accepted — *because* SRS
  § 3.7 FR-23 says a label "must not be empty" where every other name and title "must contain at
  least one non-whitespace character", and SRS § 7 C-5 carries tracker16-X's rule, whose `add_label`
  reads "Only the exact empty string `""` is rejected … a single space `" "` is a valid label and is
  stored verbatim" (`task-tracker-X/tasktracker16x/domain/task.py`,
  `Task.add_label`). SRS FR-39's "a required text field left blank" does not reach a label, because
  a task needs no label. *(re: R-64; source: SRS § 3.7 FR-23; § 7 C-5)*
- **RN-9:** *(added)* R-80: a typed value is saved exactly as typed, surrounding spaces included —
  *because* SDD § 4 RT-10 says "No part changes a typed value in any other way between the field and
  the rule" beyond turning a line break into one character, and SRS FR-10, FR-20 and FR-23 compare
  names and labels exactly. On this reading `Alpha` and `Alpha ` are two different project names,
  and the Examples table shows the case. *(re: R-80, R-32; source: SDD § 4 RT-10; SRS § 3.3 FR-10)*
- **RN-10:** *(added)* R-22: saved data that holds a value an action would refuse counts as
  unreadable — *because* SDD § 4 SD-5 builds the state at start "through the same `domain`
  constructors every action uses, so every rule a slice adds is also a check at start", and SRS § 6
  DR-6 names its breaks as examples ("Such breaks include"). R-22 names the value rules R-31, R-40,
  R-58, R-64, R-71 and R-76 set, and leaves out the assignment rule R-60, because SRS FR-22 keeps an
  unlisted name on a task as valid saved state. *(re: R-21, R-22; source: SDD § 4 SD-5; SRS § 6 DR-6,
  § 3.6 FR-22)*
- **RN-11:** Reverse-walk drop-lines — the upstream items that land as no rule, each for the stated
  reason:
  - SRS § 4.1 NFR-1, the one-second bar at 1,000 tasks with 20 comments each, and SRS § 4.4 NFR-7, one
    operator at that volume, are quality bars rather than behaviour. They belong to the NFDR,
    `products/tracker17/docs/nfdr.md` (SDD § 12). PD-16 carries NFR-7's one-operator consequence.
  - SRS § 8's acceptance criteria are carried by the rules they cover. AC-8 and AC-13 also state
    behaviour no FR states, and R-28 and R-99 carry it.
  - SDD § 4's experience conditions EX-1, EX-2, EX-4 to EX-6, EX-8 to EX-12 and EX-14 restate UXD
    entries — how a page appears, where focus lands, what is confirmed in place. They are the
    experience, which `products/tracker17/docs/UXD.md` owns, and this document restates none of them.
    R-26, R-56, R-94 and R-105 take behaviour from EX-12, EX-7, EX-3 and EX-13.
  - SDD § 4 RT-5, RT-6, RT-9, SD-3, SD-6, OB-4, SEC-2, SEC-3 and TS-1 to TS-5 are mechanisms. The
    behaviour each serves is the rule that cites its SRS source. RT-5's fixed address lands as R-4 and
    PD-10, which state that the address is fixed and leave its value to the SDD. SEC-2's refusals and
    SEC-3's policy, framing included, serve R-110. RT-7's form, which carries the values the page
    showed, is a mechanism too, and the save it serves is R-115 and R-48.
  - SDD § 4 RT-3 and RT-4's Linux statements land as R-119, R-120 and PD-8. SDD § 6 S-1's statement
    that the full suite needs the copy to be a Git repository is in a slice, under the bullet on SDD
    §§ 5 to 8 below, and no § 4 condition states it.
  - SDD § 9 TO-1, TO-3 and TO-5 have no consequence a user sees beyond the two-command start, which
    R-1 and R-13 bound. TO-2's consequence, a whole page answering every action, is the experience,
    under the previous bullet. TO-4, TO-6 and TO-7 land as R-20, OOS-16, PD-10 and PD-11.
  - SDD § 11's risks and SDD § Open Questions (whether Chromium applies `autofocus` to an element
    that is not a form control) are technical and settle in the build. None moves a rule here. R-79
    holds however a line break is counted.
  - SDD §§ 5 to 8 and § 10 are the cut and its record, and a definition document never names the route
    (`<CORE>/doctrine/setup/setting_up_a_project.md` § *The definition set never names the journey*).
  - PRD § Why This, § Assumptions and § Risks set intent and conditions, and require no behaviour. SRS
    RN-18 walks the same items.
  - The default sort field of a list with no sort chosen, the order of the projects list, and whether a
    page states a field's maximum length are experience calls. SRS FR-36 fixes only the default
    direction, and `products/tracker17/docs/UXD.md` § 5.5 UX-F5 and § 6 UX-S3 state the rest.
    `products/tracker17/docs/UXD.md` UX-F2 and UX-F7 have the project-description field and the
    comment field state their maximum, and SDD § 4 RT-10 takes that number from the field's own limit.
    None of the three moves a rule here.
- **RN-13:** *(added)* R-51, R-90, R-96, PD-5 and RN-6 name four priorities, and R-119, R-120 and
  PD-8 carry the Linux setup lines — confirmed choices, confirmed on 2026-10-11 in
  `products/tracker17/docs/trail/fdr/cycle-2.md` § 2.1 and § 2.2, with the reasoning in
  `products/tracker17/docs/trail/fdr/self_answer-2.md` — *because* each follows a change upstream of
  FDR version 2. PRD version 5 § Core Features, Priorities and SRS version 5 FR-15, FR-36, FR-38 and
  C-5 name `critical` as a fourth priority. SDD version 7 § 4 RT-3 and RT-4 add the Linux install step,
  its need for administrator rights, and the bound on the Linux systems the end-to-end suite runs on.
  *(re: R-51, R-90, R-96, R-119, R-120, PD-5, PD-8; source: PRD § Core Features, Priorities; SRS § 3.4
  FR-15, § 3.10 FR-36, § 3.11 FR-38, § 7 C-5; SDD § 4 RT-3, RT-4)*
