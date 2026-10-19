# SRS — tracker17

**Status:** Settled
**Owner:** CTO
**Version:** 6 — PRD v6's second purpose, kensaiapp's own testing ground, folded in on the owner's answer (`products/tracker17/docs/trail/srs/cycle-5.md` § 3.1): § 1 names it, FR-41 has the README's opening paragraph name both purposes, AC-21 checks it, RN-18 narrows its § Purpose drop-line, and RN-25 records why
**Inputs read:** PRD Settled (v6) · Agari no Status line (`agari_template.md` carries none) · UXD Settled (no companion; searched for the README and the product's purposes, not a source) · tracker17 doctrine no Status line (stamped, unfilled) · SDD Settled, DESIGN Settled, CONTENT Settled, fdr Settled and nfdr Settled (downstream; searched for the README and the product's purposes, not sources — none has a companion)

> The SRS is the technical source of truth: the system-level **what**, derived from the PRD and
> read cold by the Principal PM (Delivery Plan / FDR) and the Principal Architect (ADR / NFDR).
> It is updated in place with versioning (bump the line above on each material change); every
> delta in a revision traces to an owner answer/directive or a change in the upstream PRD, and
> the Version line names what changed and why.
> Every requirement traces back to a PRD feature or goal — no requirement without a source. Keep the
> **how** — architecture, component design, delivery sequencing — out; that belongs downstream
> (the SDD you write, with the CPO's and the CDO's calls folded in, the ADRs/NFDR the Principal Architect owns, the Delivery
> Plan). Give every item a stable typed ID (`FR-n`, `NFR-n`, `DR-n`, `C-n`, `AC-n`) so downstream
> documents can reference it. Omit a section only when it genuinely does not apply; do not pad
> one to fill it.

**How to read the markers.** A requirement marked *(confirmed: `trail/srs/cycle-<N>.md` § 2.n)*
states a call the PRD does not make. The CTO drafted it and the owner confirmed it, in the answered
round kept at `products/tracker17/docs/trail/srs/cycle-<N>.md` § 2.n. A marker that reads *confirmed
with an addition* means the owner's answer also added to the requirement, and the requirement as
written here carries that addition. A marker that reads *(answered: `trail/srs/cycle-<N>.md` § 3.n)*
means the requirement changed on the owner's answer to an item a downstream seat raised, kept at
`products/tracker17/docs/trail/srs/cycle-<N>.md` § 3.n.

---

## 1. Purpose

tracker17 is a single-operator task tracker that runs on the operator's own machine and is used in a
desktop browser (`products/tracker17/docs/PRD.md` § Blurb). The system must hold projects, tasks,
assignees, labels, due dates and comments under the task rules tracker16-X already defines. It must
also offer filtering, sorting and a per-project summary. It keeps everything on the machine and uses
no outside service. The product intent it serves is a worked example: a reader must be able to set
it up quickly, see that it works, read its code, and follow one feature from the product definition
to its code and tests (PRD § Purpose, § Key Use Cases). tracker17 is also kensaiapp's own testing
ground: building it with kensaiapp is how issues in kensaiapp are found and fixed (PRD § Blurb,
§ Purpose).

## 2. Scope

**What this SRS covers.** Every PRD Core Feature, the written setup instructions, persistence on the
operator's machine, the failure states in PRD § UX Notes, and the three test layers (PRD § Scope (In)).

**What the system deliberately does not do** (PRD § Out of Scope):

- hosting, or use by more than one person over a network
- login, accounts or access control
- real-time collaboration and notifications
- export
- threaded comment replies, filters with more than one value per field, sorting by more than one
  field, moving a task between projects, and a summary across projects
- a command-line interface, including tracker16-X's command names and flags, its relative-date
  shorthand (`+3d`) and its data kept per working directory
- a package, an installer or a hosted demo

**The terminus this SRS is scoped against** is the project's 上がり Agari,
`system/projects/tracker17/agari.md`. Done is reached when the owner passes the PRD's three bars,
**Works**, **Simple to set up** and **Simple to read**, on one run-through on their own machine. The
Agari places two things outside done, and this SRS specifies neither:

- **Publishing tracker17**, or a trial by an outside reader. The Agari says done "does not require
  tracker17 to be published or tried by an outside reader". No requirement here serves a public
  repository, a public download location or an outside reader's environment.
- **Re-checking the three bars "again on every later release"** (PRD § Success Metrics). The Agari
  calls that upkeep after done. The acceptance criteria in § 8 are written so the same checks can be
  run again, and no requirement here schedules or automates the re-check.

## 3. Functional Requirements

### 3.1 Starting, reaching and setting up the tracker

- **FR-1:** The tracker is started by a command named in the written setup instructions. Once it is
  ready, it states the local address the operator opens in the browser. *(traces to: PRD § Key Use
  Cases 1; § UX Notes, Arrival)*
- **FR-2:** The tracker answers only requests that come from the machine it runs on. A request from
  any other machine gets no response from the tracker. *(traces to: PRD § Out of Scope, "reachable
  only from the machine it runs on")*
- **FR-3:** If the tracker cannot take the local address it uses, because something else holds it,
  the start fails with a plain message saying so. A failed start writes nothing to the saved data.
  *(traces to: PRD § UX Notes, Failure states)*
- **FR-4:** The written setup instructions state:
  - the prerequisites the machine needs before setup, including that setup needs a network
    connection once, to fetch the declared dependencies (§ 5.3), so that a setup run offline fails
    in a way the instructions already explain
  - the commands that take a fresh copy to the tracker open in the browser
  - where the tracker keeps its saved data, and that, because the data is kept out of version
    control (FR-6), a clean of the copy that removes ignored files deletes it
  - how to start the tracker again after it has stopped
  - how to set the saved data aside and start fresh on purpose
  - how to run the full automated test suite

  *(traces to: PRD § Scope (In); § UX Notes, Arrival and Failure states; § Data & Privacy, Deletion;
  § Success Metrics, Works)* *(confirmed with an addition: `trail/srs/cycle-1.md` § 2.1, the
  network line; § 2.9, the clean line)*
- **FR-41:** The README, `README.md` at the root of a copy of tracker17, is the document that carries
  the written setup instructions FR-4 lists, and a reader arrives at it first. Its opening paragraph,
  under its title and before anything else, names both of tracker17's purposes: the worked example
  and kensaiapp's own testing ground. Of tracker17's earlier versions, the opening paragraph names
  only tracker16-X. The wording is `CONTENT.md`'s, not this document's. *(traces to: PRD § Purpose,
  "A reader learns both purposes from the first thing they read about tracker17"; § UX Notes,
  Arrival)* *(answered: `trail/srs/cycle-5.md` § 3.1; why, RN-25)*

### 3.2 Saved data

- **FR-5:** Everything the operator enters is still present after the tracker is stopped and
  started again on the same machine. *(traces to: PRD § UX Notes, Persistence)*
- **FR-6:** The saved data lives in one location that does not depend on the directory the tracker
  was started from. The location is inside the operator's copy of tracker17, and it is never
  committed to version control. *(traces to: PRD § Data & Privacy, Deletion; § Out of Scope, a
  command-line interface)* *(confirmed: `trail/srs/cycle-1.md` § 2.9)*
- **FR-7:** When no saved data exists, the tracker starts empty, with no projects and no sample data.
  *(traces to: PRD § UX Notes, First run)*
- **FR-8:** When saved data exists but cannot be read, the tracker says so plainly and names the
  data's location. It does not present an empty tracker in place of the operator's work. It never
  writes to, replaces or deletes saved data it could not read. *(traces to: PRD § UX Notes, Failure
  states)*
- **FR-9:** The tracker reports an action to the operator as done only after the result is in the
  saved data. *(traces to: PRD § UX Notes, Persistence)*

### 3.3 Projects

- **FR-10:** The operator creates a project with a name and an optional description. The name must
  contain at least one non-whitespace character. A name already used by another project is refused.
  Names are compared exactly, so `Alpha` and `alpha` are different names. *(traces to: PRD § Core
  Features, Projects)*
- **FR-11:** The operator lists all projects. *(traces to: PRD § Core Features, Projects)*
- **FR-12:** The operator renames a project. The new name follows FR-10's rules. Renaming leaves the
  project's tasks unchanged. *(traces to: PRD § Core Features, Projects)*
- **FR-13:** The operator deletes a project. Deleting a project deletes all of its tasks and their
  comments. *(traces to: PRD § Core Features, Projects)*
- **FR-14:** The system offers no way to move a task from one project to another. *(traces to: PRD
  § Core Features, Projects; § Out of Scope)*

### 3.4 Tasks

- **FR-15:** The operator creates a task within a project. The task has:
  - a title, which must contain at least one non-whitespace character and need not be unique
  - a priority, which is `low`, `medium`, `high` or `critical`, and `medium` when none is given
  - zero or one assignee
  - any number of labels
  - an optional due date

  A new task starts in status `todo`. The system records when the task was created, and it keeps
  the order in which tasks were created independently of that recorded time, so two tasks created
  within the same recorded instant still have a fixed order. Each task gets an identity that is
  unique across all projects and is never reused, even after the task is deleted. *(traces to: PRD
  § Core Features, Tasks, Status workflow, Priorities, Sorting)* *(confirmed with an addition:
  `trail/srs/cycle-1.md` § 2.4, the creation-order rule)* *(answered: `trail/srs/cycle-4.md` § 3.1,
  the four priorities; why, RN-24)*
- **FR-16:** The operator edits any field of a task except its status. The editable fields are the
  title, the priority, the assignee (set to a name on the list, or cleared), the labels (FR-23) and
  the due date (set, changed or cleared). *(traces to: PRD § Core Features, Tasks)*
- **FR-17:** The operator deletes a task. Deleting a task deletes its comments. *(traces to: PRD
  § Core Features, Tasks)*

### 3.5 Status workflow

- **FR-18:** A task's status changes only through the workflow. The allowed moves are:

  | From | To |
  |---|---|
  | `todo` | `in-progress`, `cancelled` |
  | `in-progress` | `done`, `cancelled`, `todo` |
  | `done` | none |
  | `cancelled` | none |

  Any other move, including a move to the status the task already has, is refused with the reason.
  *(traces to: PRD § Core Features, Status workflow)*
- **FR-19:** For a given task, the system offers only the moves allowed from its current status. A
  task in `done` or `cancelled` is offered none. *(traces to: PRD § UX Notes, The status workflow is
  visible)*

### 3.6 Assignees

- **FR-20:** The operator keeps one list of names that tasks can be assigned to. The operator adds a
  name, removes a name and sees the list. A name must contain at least one non-whitespace character.
  A name already on the list is refused, compared exactly. *(traces to: PRD § Core Features,
  Assignees)*
- **FR-21:** A task can be assigned only to a name on the list. Any other name is refused with the
  reason. *(traces to: PRD § Core Features, Assignees; § UX Notes, Refusals say why)*
- **FR-22:** Removing a name from the list leaves that name on every task that already carries it.
  *(traces to: PRD § Core Features, Assignees)*

### 3.7 Labels

- **FR-23:** The operator adds a label to a task, or removes one, one label at a time. A label is
  free text and must not be empty. It is stored exactly as typed and compared exactly. Adding a label
  the task already carries leaves the task unchanged. *(traces to: PRD § Core Features, Labels)*

### 3.8 Due dates and overdue

- **FR-24:** A due date is a calendar date with no time of day. *(traces to: PRD § Core Features, Due
  dates)*
- **FR-25:** A task is overdue when its due date is before today and its status is neither `done`
  nor `cancelled`. A task due today is not overdue. "Today" is the machine's local calendar date at
  the moment the system produces the list, the summary or the filter result that shows the overdue
  state. *(traces to: PRD § Core Features, Due dates; § UX Notes, Defaults)*
- **FR-26:** Every task the system shows in a list shows whether it is overdue. *(traces to: PRD § UX
  Notes, What must feel effortless, "seeing which tasks are overdue")*

### 3.9 The operator's name and comments

- **FR-27:** The operator sets their own name in the app, and can change it later. The name must
  contain at least one non-whitespace character. *(traces to: PRD § Core Features, Comments)*
  *(confirmed: `trail/srs/cycle-1.md` § 2.7; why, RN-19)*
- **FR-28:** The operator adds a comment to a task. The comment text must contain at least one
  non-whitespace character. The system records the operator's current name as the author, and the
  moment the comment was written. A comment added before the operator has set a name is refused with
  the reason. *(traces to: PRD § Core Features, Comments; § UX Notes, Refusals say why)*
  *(confirmed: `trail/srs/cycle-1.md` § 2.7, for the non-blank text rule; why, RN-19)*
- **FR-29:** A task's comments show oldest first, as one flat list, each with its author and the time
  it was written. The system offers no way to edit or delete a comment. *(traces to: PRD § Core
  Features, Comments)*
- **FR-30:** Changing the operator's name leaves every existing comment with the name it was written
  under. *(traces to: PRD § Core Features, Comments)*

### 3.10 Task lists: filtering and sorting

- **FR-31:** The operator views a task list for one project or across all projects. A list across all
  projects shows each task's project. *(traces to: PRD § Core Features, Filtering)*
- **FR-32:** The operator filters a task list by any combination of status, priority, assignee,
  label, a due-date range and overdue. Each field takes one value. Fields combine as AND. A label
  filter matches a task carrying exactly that label. *(traces to: PRD § Core Features, Filtering;
  § Key Use Cases 4)*
- **FR-33:** The assignee filter accepts only a name on the current assignee list. A name not on the
  list is refused with the reason, so a task carrying a removed name cannot be found by its assignee.
  *(traces to: PRD § Core Features, preamble, "behaves as its predecessor does wherever both cover a
  rule")* *(confirmed: `trail/srs/cycle-1.md` § 2.5)*
- **FR-34:** The due-date range has a from-date and a to-date, and either may be left out. A task
  matches when its due date is on or after the from-date and on or before the to-date. A task with no
  due date matches no range that has at least one end set. A range whose from-date is later than its
  to-date is refused under FR-39, with a reason saying the dates are the wrong way round, instead of
  showing that nothing matched. *(traces to: PRD § Core Features, Filtering; § UX Notes, Refusals say
  why)* *(confirmed with an addition: `trail/srs/cycle-1.md` § 2.3, the reversed-range refusal)*
- **FR-35:** The overdue filter shows only tasks that are overdue under FR-25. *(traces to: PRD § Core
  Features, Filtering)*
- **FR-36:** The operator sorts a task list by one field at a time: due date, priority, created time
  or title. The direction is ascending or descending, and ascending applies when none is chosen. The
  sort order is:
  - **Priority:** ascending runs `low`, `medium`, `high`, `critical`.
  - **Due date:** tasks with no due date come last in either direction.
  - **Title:** alphabetical, ignoring letter case.
  - **Ties:** tasks equal on the chosen field keep the order in which they were created.
  - **Same recorded creation time:** the tie rule, and a sort by created time itself, follow the
    creation order FR-15 keeps, so they come out the same way every time even when two tasks carry
    the same recorded creation time.

  *(traces to: PRD § Core Features, Sorting)* *(confirmed with an addition: `trail/srs/cycle-1.md`
  § 2.4, the same-recorded-time rule)* *(answered: `trail/srs/cycle-4.md` § 3.1, `critical` after
  `high`; why, RN-24)*
- **FR-37:** When a project list, a task list or a filter result is empty, the system says so rather
  than showing a blank space. With no projects it invites the operator to create one. An empty project
  invites a first task. A filter that matches nothing says that nothing matched. *(traces to: PRD § UX
  Notes, First run)*

### 3.11 Project summary

- **FR-38:** For one project, the summary shows:
  - the total number of tasks
  - the count for each of the four statuses, a zero count included
  - the count for each of the four priorities, a zero count included
  - the overdue count, under FR-25
  - the count of tasks with no due date
  - the open tasks (neither `done` nor `cancelled`) for each assignee

  The per-assignee part has one row for every name on the current assignee list, a zero count
  included. It has one more row for each name not on the list that an open task in the project still
  carries. It always has one row for "(unassigned)". *(traces to: PRD § Core Features, Project
  summary; § Key Use Cases 4)* *(confirmed: `trail/srs/cycle-1.md` § 2.6, for which rows appear)*
  *(answered: `trail/srs/cycle-4.md` § 3.1, the four priority counts; why, RN-24)*

### 3.12 Refusals

- **FR-39:** Every refused action leaves the saved data unchanged and tells the operator the reason
  in plain words. Refused actions include:
  - a status move the workflow does not allow
  - a name that is not on the assignee list
  - a comment before the operator has set a name
  - a project name already in use
  - a required text field left blank
  - a due-date range whose from-date is later than its to-date (FR-34)
  - an action that NFR-3 refuses because the task has changed since it was shown, or because the
    project or task it acts on no longer exists
  - a text value longer than the maximum FR-40 sets for its field

  *(traces to: PRD § UX Notes, Refusals say why)* *(confirmed with an addition:
  `trail/srs/cycle-1.md` § 2.2, the no-longer-exists case; § 2.3, the reversed range;
  `trail/srs/cycle-2.md` § 2.1, the over-long value)*

### 3.13 Length of typed text

- **FR-40:** A project name, a task title, an assignee name, the operator's name and a label each
  take at most 200 characters. A project description and a comment each take at most 4,000
  characters. A longer value is refused under FR-39, and the tracker never shortens a value to make
  it fit. A value that the tracker's own field let the operator enter is never refused as too long.
  *(traces to: PRD § Core Features, Projects, Tasks, Assignees, Labels and Comments, which name the
  fields; § UX Notes, Refusals say why)* *(confirmed with an addition: `trail/srs/cycle-2.md` § 2.1;
  why, RN-21)*

## 4. Non-Functional Requirements

### 4.1 Performance

- **NFR-1:** With up to 1,000 tasks across all projects, and up to 20 comments on any one task, every
  operator action shows its result in the browser within 1 second on the operator's machine. This
  covers creating, editing, moving, deleting, filtering, sorting, opening a summary and adding a
  comment. The bar is set at ordinary text lengths, not at the maximums FR-40 allows. *(traces to:
  PRD § Goals, It works; § UX Notes, What must feel effortless)* *(confirmed: `trail/srs/cycle-1.md`
  § 2.8; with an addition: `trail/srs/cycle-2.md` § 2.1, the text lengths; why, RN-22)*

### 4.2 Availability & Reliability

- **NFR-2:** If the tracker is stopped part-way through saving, by a crash, a killed process or a
  power cut, the saved data afterwards reads as the state either before or after that action. It
  never reads as a partial mix of the two. *(traces to: PRD § UX Notes, Persistence and Failure
  states)*
- **NFR-3:** Each page shows the data as it stood when the page was loaded, and pages do not update
  themselves. Every action is checked against the saved data at the moment it is applied, not against
  what the page showed. An action that is no longer valid, such as a status move on a task another
  browser tab has already moved, is refused under FR-39 with the reason. An action on a project or
  task that no longer exists, because another tab deleted it, is refused under FR-39 with the reason
  and changes nothing. A plain field edit made from a stale page replaces whatever the other tab saved
  for that field: this is stated rather than prevented, because both edits come from the one operator
  and no workflow rule is broken. The operator reloads the page to see the current state. At most one
  running tracker uses a given saved-data location. A second start against the same location, while
  another tracker is actually running against it, refuses with a plain message and changes nothing. A
  tracker stopped by a crash, a killed process or a power cut does not stop the next start. *(traces
  to: PRD § UX Notes, Refusals say why; § Out of Scope, real-time collaboration)* *(confirmed with an
  addition: `trail/srs/cycle-1.md` § 2.2, the deleted-target refusal, the stale plain edit and the
  start after a stopped tracker)*

### 4.3 Security & Privacy

- **NFR-4:** A web page from any other origin, open in the operator's browser, cannot read, change or
  delete tracker data. The tracker refuses any request that does not come from its own pages, and
  that refusal changes nothing. *(traces to: PRD § Out of Scope, hosting; § Data & Privacy)*
- **NFR-5:** While the tracker runs, nothing is sent off the machine. The tracker makes no outbound
  network request, and its pages load nothing from outside the machine. There is no telemetry, usage
  reporting or update check. *(traces to: PRD § Data & Privacy, "None of it leaves the machine";
  § Goals, It costs nothing to run; § Dependencies / Integrations, No outside service)*
- **NFR-6:** The saved data holds only what DR-1 to DR-5 describe. It holds nothing else about any
  person, and no record of requests, addresses or usage. *(traces to: PRD § Data & Privacy, "Nothing
  else is stored about anyone")*

### 4.4 Scalability

- **NFR-7:** The system serves one operator on one machine. The data volume it must hold is NFR-1's,
  and there is no requirement to serve more than one operator. *(traces to: PRD § Target Users, The
  operator; § Out of Scope, hosting)*

### 4.5 Observability

- **NFR-8:** On start, the tracker writes to the console it was started from the address to open and
  the saved-data location. When an action fails for a reason that is not a refusal under FR-39, the
  tracker writes a message to that console naming the action and the error. The browser then tells
  the operator in plain words that the action failed, and the saved data is unchanged. *(traces to:
  PRD § UX Notes, Failure states and Refusals say why; § Data & Privacy, Deletion)*

### 4.6 Maintainability

- **NFR-9:** For every Core Feature the operator uses, a reader can reach the code that builds the
  feature and the tests that check it from the product definition documents, by following what the
  documents and the code point to, without searching. *(traces to: PRD § Success Metrics, Simple to
  read; § Key Use Cases 2; § Why This, What tracker17 adds)*
- **NFR-10:** The code and tests are small and plain enough for the owner, reading cold, to judge the
  product simple. No line count or size metric stands in for that judgement. *(traces to: PRD § Goals,
  It is simple; § Success Metrics, Simple to read)*
- **NFR-11:** The automated test suite has three layers: unit, integration and end-to-end. The
  end-to-end layer drives the tracker through the browser interface the operator uses. *(traces to:
  PRD § Core Features, Tested throughout; § Success Metrics, Works; § Goals, It works)*

### 4.7 Usability & Accessibility

- **NFR-12:** Every action in Key Use Cases 3, 4 and 5 can be done from the keyboard alone. *(traces
  to: PRD § UX Notes, Defaults)*
- **NFR-13:** The interface is in English and is built for a desktop browser. The supported browsers
  are current stable desktop Chrome and other Chromium-based browsers, and the end-to-end layer runs
  in Chromium. A phone layout is not a requirement. *(traces to: PRD § UX Notes, Defaults)*
  *(confirmed: `trail/srs/cycle-1.md` § 2.10)*
- **NFR-14:** Due dates show as calendar dates. A comment's time shows in the machine's local time.
  *(traces to: PRD § UX Notes, Defaults; § Core Features, Comments)*

## 5. Interfaces

### 5.1 User Interface

- The browser is the only interface (PRD § Out of Scope, a command-line interface). The tracker
  serves pages at a local address on the operator's machine, and the operator works in a desktop
  browser on the same machine. Every operation in § 3 is reached through those pages.
- The console the tracker was started from carries the start message, the start failures in FR-3,
  FR-8 and NFR-3, and the messages in NFR-8. The operator does not act through the console beyond
  starting and stopping the tracker.

### 5.2 API

- The system exposes no programmatic interface for outside use. Any exchange between the tracker's
  pages and the tracker is internal to the product and is not a supported surface (PRD § Out of
  Scope, a command-line interface: "The browser is tracker17's only interface").

### 5.3 External Services

- **At run time: none** (PRD § Dependencies / Integrations, No outside service). The tracker depends
  only on the operator's machine. It reads the machine's clock for the local date (FR-25) and the
  comment time (FR-28), and the machine's disk for the saved data (FR-6).
- **At setup:** a fresh copy may fetch its declared dependencies from public sources that need no
  account, key or sign-up. Setup therefore needs a network connection once, which FR-4's
  prerequisites state, and the declared dependencies are fixed to exact versions (C-8).
  *(confirmed with an addition: `trail/srs/cycle-1.md` § 2.1)*

## 6. Data Requirements

- **DR-1:** **Project.** A name and an optional description. The name is unique among projects,
  compared exactly. A project owns its tasks.
- **DR-2:** **Task.** An identity unique across all projects and never reused, the project it belongs
  to, a title, a status, a priority, an assignee name or none, a set of labels, a due date or none, the
  time it was created, its place in the order tasks were created (FR-15), and its comments. The assignee name is plain text and stays valid after the
  name leaves the assignee list (FR-22).
- **DR-3:** **Comment.** Text, the author name as it stood when the comment was written, and the
  moment it was written. A comment belongs to one task and never changes after it is written.
- **DR-4:** **Assignee list.** One list of names, each unique, compared exactly.
- **DR-5:** **Operator name.** One name, or no name until the operator sets one.
- **DR-6:** **Saved data read at start.** The saved data is the one input the tracker reads that it
  did not just write, and it may have been changed by hand or damaged. At start, saved data counts as
  unreadable under FR-8 when the tracker cannot read all of it, or when it breaks a rule above. Such
  breaks include an unknown status or priority, a task whose project does not exist, two projects
  with one name, a reused task identity, and a saved value longer than the maximum FR-40 sets for
  its field. The tracker never loads part of the saved data and silently drops the rest. *(traces
  to: PRD § UX Notes, Failure states, "rather than starting empty and hiding the operator's work")*
  *(confirmed with an addition: `trail/srs/cycle-2.md` § 2.1, the over-long saved value)*

## 7. Constraints

- **C-1:** tracker17 runs on the operator's own machine and is never hosted. *(traces to: PRD § Goals,
  It costs nothing to run; § Out of Scope, hosting)*
- **C-2:** No step, in setup or in use, asks for an account, a key, a sign-up or a payment. The
  product uses no outside service at run time. *(traces to: PRD § Success Metrics, Simple to set up;
  § Dependencies / Integrations, No outside service)*
- **C-3:** The browser is the only interface. tracker16-X's command-line mechanics are not carried
  over. *(traces to: PRD § Out of Scope, a command-line interface)*
- **C-4:** tracker17 is offered as source code to read and run, with no package, installer or hosted
  demo. *(traces to: PRD § Out of Scope, a package, an installer, or a hosted demo)*
- **C-5:** tracker17's task rules are tracker16-X's wherever both cover a rule, with one exception:
  tracker16-X's three-value priority set is not taken over, and FR-15 names tracker17's four.
  tracker16-X's working code at `task-tracker-X` is the preferred starting point. *(traces
  to: PRD § Core Features, preamble, including "The one exception is **Priorities**"; § Dependencies /
  Integrations, tracker16-X)* *(answered: `trail/srs/cycle-4.md` § 3.1, the priority exception; why,
  RN-24)*
- **C-6:** The product is built test-first. *(traces to: PRD § Core Features, Tested throughout)*
- **C-7:** From a fresh copy, on a machine with only the stated prerequisites, the written setup
  instructions take the operator to the tracker open in the browser in at most three commands and
  within ten minutes. Commands joined with `&&` or `;` count as separate commands. *(traces to: PRD
  § Success Metrics, Simple to set up)*
- **C-8:** The declared dependencies are fixed to exact versions, so a fresh copy set up later gets
  the same versions the suite last passed with. *(traces to: PRD § Success Metrics, Works and Simple
  to set up)* *(confirmed with an addition: `trail/srs/cycle-1.md` § 2.1)*

## 8. Acceptance Criteria

Each criterion names how it is verified. Owner checks are the PRD's own pass/fail calls and are not
replaced by automated tests.

- **AC-1:** **Works, in the browser.** The owner runs through Key Use Cases 3, 4 and 5 in the browser
  with no error and no wrong result. Verified by an owner run-through. *(covers: FR-10 to FR-39,
  NFR-12)*
- **AC-2:** **Works, in the suite.** The full automated suite passes, with unit, integration and
  end-to-end layers all present, and the end-to-end layer driving the browser interface. Verified by
  running the suite as FR-4 instructs. *(covers: NFR-11, C-6)*
- **AC-3:** **Simple to set up.** The owner starts on a machine with only the stated prerequisites,
  from a fresh copy, and follows only the written setup instructions. They reach the tracker open in
  the browser in at most three commands and within ten minutes, and nothing asks for an account, a key
  or a sign-up. The console shows the address to open. Verified by an owner run-through. Every
  declared dependency is fixed to an exact version, verified by inspection of the dependency
  declarations. *(covers: FR-1, FR-4, C-2, C-7, C-8, NFR-8)*
- **AC-4:** **Simple to read.** The owner reads the code and its tests cold and judges them simple.
  Verified by the owner's pass/fail call. *(covers: NFR-10)*
- **AC-5:** **The trace.** At check time, the owner picks any one Core Feature the operator uses. They
  reach the code that builds it and the tests that check it from the product definition documents, by
  following what the documents and the code point to, without searching. Verified by the owner's
  pass/fail call. *(covers: NFR-9)*
- **AC-6:** **Persistence.** After the operator has entered a project, a task with every field set, an
  assignee, a label, a comment and their own name, a stop and a start show all of them unchanged.
  Verified by an automated test. *(covers: FR-5, FR-9)*
- **AC-7:** **Unreadable saved data.** With saved data that cannot be read, or that breaks a rule in
  DR-6, a start shows a plain message naming the data's location, and no empty tracker is presented.
  The saved data's bytes are unchanged afterwards. Verified by automated tests, one per kind of break
  DR-6 names. *(covers: FR-8, DR-6)*
- **AC-8:** **Setting saved data aside.** After the owner follows the instructions to set the saved
  data aside, the tracker starts empty, and the set-aside data still holds the earlier work. Verified
  by an owner run-through. *(covers: FR-4, FR-7)*
- **AC-9:** **Interrupted save.** When a save is cut off part-way, a start afterwards reads the state
  from before or after that action. Verified by an automated test that interrupts a save. *(covers:
  NFR-2)*
- **AC-10:** **Reachability and other origins.** A request to the tracker from another machine gets no
  response. A request that does not come from the tracker's own pages is refused and changes nothing.
  Verified by automated tests for the second part. The first part is verified by inspection of the
  address the tracker listens on, because a test suite running on one machine cannot be another
  machine. *(covers: FR-2, NFR-4)*
- **AC-11:** **Nothing leaves the machine.** With the machine's network connection turned off, the
  AC-1 run-through still passes, and the browser records no request to any address outside the
  machine. Verified by an owner run-through with the browser's network view open. *(covers: NFR-5,
  C-2)*
- **AC-12:** **Refusals.** Each refusal FR-39 lists shows its reason, and the saved data is the same
  before and after. Verified by automated tests, one per refusal, with NFR-3's refusal tested both
  for a task that has changed and for a project or task another tab deleted. *(covers: FR-18, FR-21,
  FR-28, FR-34, FR-39, FR-40, NFR-3)*
- **AC-13:** **Overdue boundary.** With today's date set by the test, an open task due yesterday is
  overdue. A task due today is not. A task due yesterday in `done` or `cancelled` is not. The list
  marking, the overdue filter and the summary count agree on all three. Verified by automated tests.
  *(covers: FR-25, FR-26, FR-35, FR-38)*
- **AC-14:** **Filtering, sorting and the summary.** Each filter field, the AND combination, both
  due-date range ends, and each sort field in both directions return the result FR-32 to FR-36 define.
  A range whose from-date is later than its to-date is refused with FR-34's reason. Two tasks carrying
  the same recorded creation time sort the same way every time, on a tie and on a sort by created
  time. The summary's counts and rows match FR-38 on a project built to exercise each row. Verified by
  automated tests. *(covers: FR-15, FR-31 to FR-38)*
- **AC-15:** **Response time.** With 1,000 tasks loaded, each carrying 20 comments, each action NFR-1
  lists shows its result within 1 second. The timed run states the text lengths it uses. Verified by
  a timed run on the owner's machine. *(covers: NFR-1)* *(confirmed with an addition:
  `trail/srs/cycle-2.md` § 2.1, the stated lengths)*
- **AC-16:** **One running tracker.** A second start against a saved-data location already in use by
  a running tracker refuses with a plain message, and the first tracker and the saved data are
  unaffected. A start after a tracker was killed against that location succeeds. Verified by
  automated tests. *(covers: NFR-3)*
- **AC-17:** **What is stored.** The saved data holds only the fields DR-1 to DR-5 describe. Verified
  by inspection of the saved data after the AC-1 run-through. *(covers: NFR-6)*
- **AC-18:** **Failures are visible.** An induced failure that is not a refusal writes a console
  message naming the action and the error. The browser says the action failed, and the saved data is
  unchanged. Verified by an automated test. *(covers: NFR-8)*
- **AC-19:** **Stale plain edit.** A plain field edit made from a page loaded before another tab saved
  a different value for that field replaces that value, and is not refused. Verified by an automated
  test. *(covers: NFR-3)*
- **AC-20:** **A full-length field with line breaks.** Through the browser, a comment and a project
  description are each filled to their field's maximum, with line breaks in the text, and submitted.
  Both are saved, and neither is refused or shortened. Verified by an automated end-to-end test.
  *(covers: FR-40)* *(confirmed with an addition: `trail/srs/cycle-2.md` § 2.1)*
- **AC-21:** **Both purposes, first.** The owner reads the README's opening paragraph and finds both
  purposes named, the worked example and kensaiapp's own testing ground, with no earlier version
  named but tracker16-X. Verified by inspection, which can be run again on any later release.
  *(covers: FR-41)* *(answered: `trail/srs/cycle-5.md` § 3.1; the tracker16-X check is added, RN-25)*

**Requirements with no criterion of their own.** FR-14 and the "no edit or delete" half of FR-29 state
an operation that does not exist, and AC-1's run-through is where its absence shows. FR-37's wording
of empty states is the UXD's, and AC-1 checks the states appear. NFR-7 sets no bar beyond NFR-1's.
NFR-13 and NFR-14 are checked by AC-1, because the owner's run-through happens in a supported desktop
browser. C-1, C-3 and C-4 are properties of what is shipped, and AC-3 is where a departure would show.
C-5 is a sourcing constraint whose result is checked rule by rule in AC-12 to AC-14.

---

## SRS Review Notes

- **RN-1:** *(added)* Rules taken from tracker16-X beyond the PRD's own text: a task identity unique
  across all projects and never reused, exact-match uniqueness of project names and assignee names,
  refusal of a blank project name, title or assignee name, refusal of an empty label, and no duplicate
  label on one task. *Because* PRD § Core Features opens "tracker17 behaves as its predecessor does
  wherever both cover a rule", and these are the predecessor's rules. The sources are
  `task-tracker-X/docs/fdr.md` § 2 Tasks ("unique across all
  projects, assigned at creation and never reused"), `docs/adr.md` § 4 Schema Design
  (Assignee "`name`: str — required, unique in the global list"), `tasktracker16x/domain/repository.py`
  `project_name_exists` ("exact (case-sensitive) name"), `tasktracker16x/domain/project.py` and
  `tasktracker16x/domain/assignee.py` (a name with no non-whitespace character is refused), and
  `tasktracker16x/domain/task.py` (the empty label is refused and the task "stores no duplicate").
  *(re: FR-10, FR-15, FR-20, FR-23, DR-1, DR-2, DR-4; PRD source: § Core Features, preamble)*
- **RN-2:** *(added)* A move to the status a task already has is refused (FR-18). *Because* the PRD's
  table lists no such move and says "Any other move is refused", and tracker16-X lists no self-move
  either (`tasktracker16x/domain/transitions.py`, "no self-loop is listed"). *(re: FR-18; PRD source:
  § Core Features, Status workflow)*
- **RN-3:** *(added)* The assignee and the due date can be cleared. *Because* PRD § Core Features,
  Tasks makes "zero or one assignee" and an "optional due date" fields that "can be edited", and
  editing an optional field to empty is part of editing it. *(re: FR-16)*
- **RN-4:** *(added)* FR-3, a start that fails when the local address is taken. *Because* PRD § UX
  Notes, Failure states, requires the tracker to say what went wrong rather than leave the operator
  guessing. A taken address is the one start failure a local web app meets that the PRD's two failure
  states do not name. *(re: FR-3, NFR-8)*
- **RN-5:** *(added)* FR-4's last item, how to run the full automated suite. *Because* PRD § Success
  Metrics, Works, requires "the full automated suite passes", and a reader working only from the
  instructions cannot run a suite the instructions do not name. *(re: FR-4, AC-2)*
- **RN-6:** *(added)* FR-6's rule that the saved-data location does not depend on the directory the
  tracker was started from. *Because* PRD § Out of Scope drops tracker16-X's "data kept per working
  directory", and PRD § Data & Privacy needs the instructions to name one place the operator deletes to
  remove every name. Where the one place sits is the owner's confirmed call,
  `products/tracker17/docs/trail/srs/cycle-1.md` § 2.9. *(re: FR-6)*
- **RN-7:** *(added)* FR-9 and NFR-2, which say when an action counts as saved and what an interrupted
  save leaves. *Because* PRD § UX Notes, Persistence, says everything entered survives a stop and
  start, and § UX Notes, Failure states, says the operator's work "stays recoverable". A save that
  could be cut off half-written would break both promises. *(re: FR-9, NFR-2, AC-9)*
- **RN-8:** *(added)* DR-6, which treats saved data breaking a data rule as unreadable, and forbids
  loading part of it. *Because* PRD § UX Notes, Failure states, forbids "starting empty and hiding the
  operator's work". A partial load hides the dropped part in the same way. *(re: DR-6, FR-8, AC-7)*
- **RN-9:** *(added)* NFR-4, the refusal of requests from other origins. *Because* PRD § Out of Scope
  keeps the tracker reachable only from its machine, so that nobody else can "read, change or delete
  the operator's data". A web page from another site, open in the operator's own browser, runs on that
  same machine and could otherwise send the tracker requests. The tracker has no login, so nothing
  else would stop it. *(re: NFR-4, AC-10; PRD source: § Out of Scope, hosting; § Data & Privacy)*
- **RN-10:** *(added)* NFR-5's rule that the pages load nothing from outside the machine. *Because*
  PRD § Data & Privacy says "None of it leaves the machine", and a page that loads a script or a font
  from an outside server tells that server the page was opened. *(re: NFR-5, AC-11)*
- **RN-11:** *(added)* NFR-8, the console messages on start and on an unexpected failure. *Because*
  PRD § UX Notes, Failure states, has the setup instructions explain how to start again, and the
  operator needs the address and the data location to act on them. PRD § UX Notes, Refusals say why,
  bars a failure that leaves the operator with no reason. *(re: NFR-8, AC-18)*
- **RN-12:** *(added)* NFR-11's rule that the end-to-end layer drives the browser interface. *Because*
  the browser is tracker17's only interface (PRD § Out of Scope), and PRD § Goals, It works, says each
  feature works "in the browser and in the automated tests". An end-to-end test that stops short of
  the browser would leave that interface untested. *(re: NFR-11, AC-2)*
- **RN-13:** *(added)* § 4.7, a seventh NFR category. *Because* PRD § UX Notes, Defaults, sets
  language, device, date display and keyboard use, and none of the template's six categories holds
  them. *(re: NFR-12, NFR-13, NFR-14)*
- **RN-14:** *(added)* FR-26, which shows the overdue state on every listed task. *Because* PRD § UX
  Notes names "seeing which tasks are overdue" as an action that must feel effortless, and the system
  must at least show the state for that to be possible. How it reads, and what makes the action
  effortless, is the UXD's. The same holds for FR-19 and the other two effortless actions in that PRD
  bullet. The SRS carries what the system must offer, and no testable bar for "effortless" itself.
  *(re: FR-19, FR-26, FR-32)*
- **RN-15:** *(added)* FR-38's zero counts for statuses and priorities. *Because* PRD § Core Features,
  Project summary, says "the count per status" and "the count per priority", and a status with no
  tasks still has a count, zero. tracker16-X's summary is specified "one line per status" and "one line
  per priority" (`task-tracker-X/docs/fdr.md` § 11). *(re: FR-38)*
- **RN-16:** *(added)* The full sort, range and summary semantics in FR-34, FR-36 and FR-38.
  *Because* PRD § Risks says tracker16-X's code "has no filtering, no sorting, no project summary", so
  tracker17 builds those fresh and inherits no tested behaviour for their edge cases. Each edge case the
  PRD and tracker16-X's FDR leave open is stated here and sent to the owner as a choice, so it is not
  settled silently in code. *(re: FR-34, FR-36, FR-38)*
- **RN-17:** *(added)* AC-10 verifies FR-2's other-machine half by inspection. *Because* a suite
  running on one machine cannot send a request from another. That half is still an obligation the
  owner gates on (PRD § Out of Scope), so it keeps a criterion with a stated method rather than none.
  *(re: AC-10)*
- **RN-18:** Reverse-walk drop-lines. These PRD items land as no requirement, each for the stated
  reason:
  - PRD § Blurb, § Purpose and § Problem Statement are carried by § 1. They set intent and require no
    behaviour, except the last sentence of § Purpose, which FR-41 carries. The testing-ground purpose
    adds no behaviour to the tracker. The tracker records nothing about kensaiapp, and NFR-5's
    no-telemetry rule stands as written. *(answered: `trail/srs/cycle-5.md` § 3.1)*
  - PRD § Why This, "Not yet proven", is a risk to the owner's judgement and is checked by AC-4.
  - PRD § Target Users, "Small team", is carried by NFR-7 and § 2: one operator, with team members
    present only as assignee names.
  - PRD § Assumptions are read as conditions on the reader and the publishing state. The first one
    bounds what FR-4 may assume of the reader. "tracker17 is not public yet" is handled by § 2's
    terminus.
  - PRD § Risks are carried where they bear: the browser-simplicity risk by AC-4, the new-feature risk
    by RN-16, the "small team" misreading by NFR-7, and the single-judge risk by AC-4 and AC-5 staying
    the owner's calls.
  - PRD § Success Metrics, "again on every later release", is upkeep after done under the Agari, as
    § 2 states.
- **RN-19:** *(added)* FR-27's non-blank operator name and FR-28's non-blank comment text. *Because*
  PRD § Core Features, Comments says "a comment can't be added until a name is set", and a blank is no
  name, and "A comment is text on a task", and a blank is no text. The predecessor clause in PRD § Core
  Features does not reach these two rules, because tracker16-X has no rule here: its comment code says
  "no validation is applied (the spec adds none)"
  (`task-tracker-X/tasktracker16x/domain/comment.py`, `Comment`), and
  its acceptance of an empty name comes from how its command-line config stores a user, which PRD § Out
  of Scope drops. The owner confirmed the rules on this reason
  (`products/tracker17/docs/trail/srs/cycle-1.md` § 2.7). *(re: FR-27, FR-28, FR-39, AC-12; PRD
  source: § Core Features, Comments)*
- **RN-20:** *(added)* The owner's confirmed calls on what the PRD leaves open, each recorded in
  `products/tracker17/docs/trail/srs/cycle-1.md` under the section named:
  - **§ 2.1:** setup may fetch declared dependencies from public sources needing no account, key or
    sign-up, and the running tracker uses no network. Setup needs a network connection once, stated
    in FR-4's prerequisites. The declared dependencies are fixed to exact versions (C-8). *(re: FR-4,
    § 5.3, C-8, AC-3)*
  - **§ 2.2:** pages show the state when loaded and every action is checked against the saved data.
    An action on a deleted project or task is refused. A stale plain field edit replaces the other
    tab's value for that field. The one-tracker check refuses only while another tracker is actually
    running. *(re: NFR-3, FR-39, AC-12, AC-16, AC-19)*
  - **§ 2.3:** both range ends are included, an undated task falls outside any range with an end set,
    and a reversed range is refused with its reason. *(re: FR-34, FR-39, AC-12, AC-14)*
  - **§ 2.4:** priority ascending runs `low`, `medium`, `high`, because ascending means rising and
    `high` is more than `low`. Undated tasks sort last, titles ignore letter case, and ties and a sort
    by created time follow a creation order kept independently of the recorded time. `critical`,
    which PRD v5 adds, follows `high` for the same reason (RN-24). *(re: FR-15, FR-36, DR-2, AC-14)*
  - **§ 2.5:** the assignee filter takes only names on the current list. *(re: FR-33)*
  - **§ 2.6:** the summary's per-assignee rows are every listed name, every unlisted name an open task
    still carries, and "(unassigned)". *(re: FR-38)*
  - **§ 2.8:** NFR-1's bar is 1,000 tasks, 20 comments per task and 1 second, and AC-15 loads 20
    comments on every task. *(re: NFR-1, AC-15)*
  - **§ 2.9:** the saved data lives inside the operator's copy, out of version control, and FR-4 warns
    that cleaning ignored files deletes it. *(re: FR-4, FR-6)*
  - **§ 2.10:** the supported browsers are current stable desktop Chrome and other Chromium-based
    browsers, and the end-to-end layer runs in Chromium. *(re: NFR-13, NFR-11, AC-2)*
- **RN-21:** *(added)* FR-40's maximum text lengths: 200 characters for a project name, a task
  title, an assignee name, the operator's name and a label, and 4,000 for a project description and
  a comment. A longer value is refused and never shortened, and a value the tracker's own field
  accepted is never refused. *Because* the PRD names these fields and sets no length (PRD § Core
  Features), and the lengths are the owner's confirmed call, recorded with the reason they exist in
  `products/tracker17/docs/trail/srs/cycle-2.md` § 2.1. How a character is counted is the SDD's to
  state, within FR-40's rule that what the field accepted is never refused. That rule covers a
  line break: a multi-line field counts it as one character, its length taken "with newlines
  normalized" (https://html.spec.whatwg.org/multipage/form-elements.html, the `textarea` element, as
  quoted in `trail/srs/cycle-2.md` § 2.1), and on submission the browser sends it as two, CR LF.
  The HTML standard has the browser "Replace every occurrence of U+000D (CR) not
  followed by U+000A (LF), and every occurrence of U+000A (LF) not preceded by U+000D (CR), in
  value, by a string consisting of U+000D (CR) and U+000A (LF)"
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, § 4.10.22.6). AC-20
  tests that case. FR-39's entry for the over-long value states only the refusal and its reason.
  This is the one refusal whose page cannot show the typed text again, because the over-long text
  cannot be carried back to the page. Only a request the tracker's own pages did not send can reach
  it, since the field stops at its length. What a refusal shows of the typed text is the UXD's
  (UX-I3), so the SRS states nothing about it. DR-6 names the over-long saved value, so AC-7 tests
  it. *(re: FR-39, FR-40, DR-6, AC-7, AC-12, AC-20; PRD source: § Core Features, Projects, Tasks,
  Assignees, Labels and Comments; § UX Notes, Refusals say why)*
- **RN-22:** *(added)* NFR-1's bar is set at ordinary text lengths, not at FR-40's maximums, and
  AC-15's timed run states the text lengths it uses. *Because* NFR-1's volume, 1,000 tasks with 20
  comments each, was confirmed with no text length (`products/tracker17/docs/trail/srs/cycle-1.md`
  § 2.8), and at the maximums that volume holds 80,000,000 characters of comment text, which nobody
  set the bar against. The owner confirmed this
  (`products/tracker17/docs/trail/srs/cycle-2.md` § 2.1, addition 1). The bar itself is unchanged.
  *(re: NFR-1, AC-15)*
- **RN-23:** *(added)* No requirement names the runtime the tracker runs on. The runtime is how the
  system is built, so it is the SDD's. FR-4 asks for the prerequisites in general terms, C-7 sets
  the bound, and AC-3 checks it against whatever prerequisites the written setup instructions state.
  So a later change of runtime leaves all three true, and AC-3 then checks against the new
  prerequisites. FR-4's network line and § 5.3 stay as written: § 5.3 lets setup fetch declared
  dependencies, and FR-4's instructions also cover running the full automated suite, so the line
  holds whichever part of setup the dependencies serve. The
  owner confirmed this, and that the SRS does not wait on the SDD settling
  (`products/tracker17/docs/trail/srs/cycle-3.md` § 2.2). *(re: FR-4, § 5.3, C-7, AC-3)*
- **RN-24:** *(added)* The priority set is `low`, `medium`, `high` and `critical`, with `medium` the default,
  and priority ascending runs `low`, `medium`, `high`, `critical`. The set is PRD § Core Features,
  Priorities, where the owner added `critical` (`products/tracker17/docs/trail/prd/cycle-5.md`
  § 1.1). The PRD sets no order. `critical` sorts after `high` for the reason the owner gave for `low`
  to `high`, that ascending means rising (`products/tracker17/docs/trail/srs/cycle-1.md` § 2.4), and
  it is the order the PRD lists the four in. C-5 carries the PRD's one exception to the predecessor
  rule (PRD § Core Features, preamble), because tracker16-X's set is `low`, `medium` and `high` only
  (`task-tracker-X/tasktracker16x/domain/priority.py`, `VALID_PRIORITIES`). An unknown priority
  under DR-6 is a value outside the four, so saved data written with only the first three still
  loads. No acceptance criterion changes: AC-14 sorts each field in both directions and checks every
  summary row, and AC-7 tests an unknown priority. The order and the C-5 exception are the owner's
  answer, `products/tracker17/docs/trail/srs/cycle-4.md` § 3.1. *(re: FR-15, FR-36, FR-38, C-5,
  DR-6, AC-7, AC-14; PRD source: § Core Features, preamble and Priorities)*
- **RN-25:** *(added)* § 1's second purpose, FR-41 and AC-21. *Because* PRD § Blurb and § Purpose
  give tracker17 a second purpose, kensaiapp's own testing ground, and § Purpose ends "A reader
  learns both purposes from the first thing they read about tracker17". The owner set both in
  `products/tracker17/docs/trail/prd/cycle-6.md` § 1.1, with "let the README tell it too" and "Of the
  earlier versions, name only tracker16-X". The PRD does not name the first thing a reader reads.
  FR-41 names the README because PRD § UX Notes, Arrival says "A reader arrives at the written setup
  instructions", the README is the document that carries them, and the owner's words name it. AC-21's
  check that no earlier version but tracker16-X is named is added, so that the whole of FR-41 has a
  criterion. FR-41, AC-21 and the narrowed RN-18 line are the owner's answer,
  `products/tracker17/docs/trail/srs/cycle-5.md` § 3.1. *(re: § 1, FR-41, AC-21, RN-18; PRD source:
  § Blurb, § Purpose, § UX Notes, Arrival)*
