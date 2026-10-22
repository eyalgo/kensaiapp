# UXD — tracker17

**Status:** Settled
**Owner:** CDO
**Version:** 9 — the seventh answered round folded in (`products/tracker17/docs/trail/uxd/cycle-7.md`): a refusal states what holds when its page is built and claims no event before it. The overtaken move states the task's status and what that status allows, the assignee refusals say the name is not on the list, and UX-I3's out-of-date refusal no longer says the page was out of date (UX-F3, UX-F4, UX-F9, UX-I3, RN-34, RN-35). PRD version 7 read, unchanged since version 8.
**Inputs read:** PRD Settled (version 7) · SRS Settled · Agari no Status line (`agari_template.md` carries none) · visual_restrictions Settled · voice_restrictions Settled · tracker17 doctrine no Status line (stamped, unfilled) · CONTENT Draft (version 14) (downstream; read to check what the answered round cites, not a source)

> The UXD is the experience source of truth: the experience-level **what**, derived from the
> settled PRD, authored concurrent with the SRS, and consumed cold by the SDD (so
> the architecture accommodates the experience) and by UI-touching change specs. It is updated
> in place with versioning (bump the line above on each material change); on a revision or a
> re-authoring it is **stable by default** — every delta traces to an owner answer or an
> upstream PRD change. Every entry traces back to a PRD feature, goal, use case, or `## UX
> Notes` item — no entry without a source. Keep technical feasibility and architecture out
> (SRS/SDD), and product intent out (PRD). Give every requirement-shaped entry a stable typed ID
> (`UX-Un`, `UX-Fn`, `UX-Sn`, `UX-In`, `UX-An`) so downstream documents can reference it. Omit a
> section only when it genuinely does not apply; do not pad one to fill it.

Every `PRD §` reference below is to `products/tracker17/docs/PRD.md`.

**How to read the markers.** An entry marked *(confirmed: `trail/uxd/cycle-N.md` § 2.n)* states a
call the PRD does not make. The CDO drafted it, and it was confirmed in the answered round kept at
`products/tracker17/docs/trail/uxd/cycle-N.md` § 2.n. *Confirmed with an addition* means the answer
also added to the entry, and the entry as written here carries that addition. *Overridden* means
the answer replaced the drafted value, and the entry carries the answer's value. *Answered* marks a
product question the round settled. The reasoning behind the answers in `cycle-1.md` is
`products/tracker17/docs/trail/uxd/self_answer-1.md`. The reasoning behind the answer in `cycle-2.md`
is `products/tracker17/docs/trail/uxd/self_answer-2.md`, and the reasoning behind the answers in
`cycle-3.md` is `products/tracker17/docs/trail/uxd/self_answer-3.md`. The reasoning behind the answer
in `cycle-4.md` is `products/tracker17/docs/trail/uxd/self_answer-4.md`, and the reasoning behind
the answer in `cycle-5.md` is `products/tracker17/docs/trail/uxd/self_answer-5.md`. The reasoning behind the
answer in `cycle-6.md` is `products/tracker17/docs/trail/uxd/self_answer-6.md`, and the reasoning behind the
answer in `cycle-7.md` is `products/tracker17/docs/trail/uxd/self_answer-7.md`. The Review Note named beside
a marker says why this document reads as it does.

---

## 1. Design Read

Reading this as: **a small single-operator task tracker that a developer runs locally to judge how
kensaiapp builds apps**, with a **plain, quiet, utilitarian** language, leaning toward **plain
semantic HTML pages with the browser's own form controls and one small stylesheet** *(confirmed:
`trail/uxd/cycle-1.md` § 2.1; why, RN-22)*.

Basis: the product is "a real, working task tracker, kept small on purpose" so a person can "read
end to end, run locally, and judge" it (PRD § Purpose). Its edge over its predecessor is "an app that
people recognise as an app, which runs in the browser" (PRD § Why This). Its first risk is that "a
web interface adds parts that a command-line tool never needed" (PRD § Risks). On this reading,
every visual and interaction decision below is weighed against one question: does it add a part the
reader has to read?

## 2. Design Dials

| Dial | Value (1–10) | Reasoning (from the PRD) |
|---|---|---|
| VARIANCE (layout experimentation: symmetric ↔ asymmetric) | 2 | PRD § Why This promises "an app that people recognise as an app", and PRD § Goals "It is simple". A recognisable app is a conventional layout: a header with navigation, a list, a detail page. Nothing in the PRD rewards an unexpected layout. |
| MOTION (animation depth: static ↔ cinematic) | 1 | PRD § Goals "It is simple … small enough to read end to end", and PRD § Risks: a web interface "adds parts". Animation is code the reader must read and serves no PRD goal. Real-time updates are out of scope (PRD § Out of Scope), so nothing arrives on screen that motion would need to announce. Static: no animation or transition beyond what the browser does by itself. |
| DENSITY (information per viewport: airy ↔ packed) | 6 *(confirmed with an addition: `trail/uxd/cycle-1.md` § 2.2; why, RN-23)* | PRD § Core Features gives every task six attributes a list must show (status, priority, assignee, labels, due date, overdue), and PRD § Key Use Cases 4 has the operator compare tasks by sorting and filtering. Comparison across rows needs one row per task with every attribute in a column, which is what is derivable. How tightly those rows pack is taste, and it is set at 6: a table, with breathing room. A title or a set of labels longer than its column wraps inside its cell, and never pushes an attribute onto a second row. |
| TYPOGRAPHY (conventional ↔ characterful) | 2 *(confirmed: `trail/uxd/cycle-1.md` § 2.2; why, RN-23)* | PRD § Why This "an app that people recognise as an app", and the product has no brand (`system/experience/visual_restrictions.md` § 3 Deliberate absences, "Typography: n/a"). Both push toward conventional type that carries no personality of its own. The exact lean is taste, and it is set at 2. |

## 3. Users & Contexts

- **UX-U1** — **The operator.** One person, at a desktop browser on the same machine the tracker
  runs on, with a keyboard and a pointer. English only, and comfortable with a desktop app. They
  track a small team's work, and they are the only person who ever touches the interface. They use
  it in sittings: open the tracker, adjust tasks, close the tab. No assistive technology is named
  by the PRD; the bar the interface holds is § 8. *(→ PRD § Target Users, The operator; § UX
  Notes, Defaults)*
- **UX-U2** — **The reader.** A developer evaluating how kensaiapp builds apps. Their experience
  starts in a terminal and the written setup instructions, then moves to the browser, where they
  act as the operator. Today the reader and the operator are the same person, the owner (PRD
  § Assumptions, "Until then the owner is the only reader"). What they judge is how few steps and
  how little reading it takes to get from a fresh copy to a working tracker. *(→ PRD § Target
  Users, The reader; § Key Use Cases 1)*

**The team members are not users.** They appear only as names on the assignee list and on tasks,
never sign in and never see a screen (PRD § Target Users, The operator). No screen in this UXD is
designed for them. On the same ground, no screen shows anything that reads as an account: no
"signed in as", no avatar, no sign-out (PRD § Risks, "'Small team' can mislead a reader").

## 4. Information Architecture

Three top-level areas, reached from one header that sits on every page:

- **Projects** — the home page. The list of projects, and the way into each one.
  - **A project** has two views of its own, switched by a link pair under the project's name:
    - **Tasks** (the default view): the project's task list with its filter and sort controls,
      and the form that adds a task.
    - **Summary**: the project summary.
  - The project's rename and delete controls sit on the project's Tasks view, below the list.
  - **A task** opens from any task list into its own page.
- **All tasks** — one task list across every project, with the same filter and sort controls and a
  project column. It has no summary, because a summary across projects is out of scope (PRD § Out
  of Scope).
- **People** — the operator's own name, and the assignee list. Both are names the operator types,
  and both are needed before Key Use Cases 3 and 5 can finish, so they share one place.

**Every page has its own address**, and the browser's back, forward and reload buttons work on
every one. A task list's filter and sort choices are part of its address (UX-I7), so a reload or a
return through back shows the same narrowed list.

**One page replaces all of them** when the saved data cannot be read (UX-S9): every address shows
that page, and no area of the tracker is reachable until the data is dealt with.

*(→ PRD § Core Features; § Key Use Cases 3–5; § UX Notes, First run and Failure states)*

## 5. Key Flows

### 5.1 UX-F1 — From a fresh copy to the tracker in the browser *(→ PRD § Key Use Cases 1; § Purpose; § UX Notes, Arrival and Failure states; § Success Metrics, Simple to set up)*

- Steps: the reader opens the setup instructions (UX-S1) → reads, first, what tracker17 is and the
  two reasons it exists (RN-31) → checks the stated prerequisites → runs
  the stated commands, no more than three, in order → the last command starts the tracker, and the
  console names the address to open (UX-S2) → the reader opens that address → the Projects page
  (UX-S3) shows its first-run state.
- Decision points: none. The instructions give one path, with no options to choose between.
- Data the UI needs at each step: the console needs the address the tracker serves and the
  location of the saved data, both known at start.
- Failure/recovery:
  - A prerequisite is missing, or setup runs without a network connection: the failure is one the
    instructions already describe, and they say what to install or do.
  - The tracker cannot start (UX-S2 error): the console says why in plain words, and nothing is
    written to the saved data.
  - Later, the tracker is not running: the browser shows its own "can't reach this page" page,
    which the tracker cannot change. The setup instructions carry a section on starting the
    tracker again, findable by its heading.

### 5.2 UX-F2 — Create a first project *(→ PRD § Key Use Cases 3; § UX Notes, First run and Refusals say why; § Core Features, Projects)*

- Steps: on the Projects page, the empty state invites a first project and puts the create form in
  view → the operator types a name and, optionally, a description → Create → the operator lands on
  the new project's Tasks view, whose empty state invites a first task.
- The description is set once, here. The form says beside the description field that the
  description cannot be changed after the project is created. *(answered: `trail/uxd/cycle-1.md`
  § 1.1; why, RN-21)*
- The form also says beside the description field the most characters a description can hold, in
  view before the operator submits. The number is the field's own maximum, taken from the same place
  that sets the field's limit, so the sentence and the field cannot disagree. The description field
  and the comment field (UX-F7) are the only fields that state their maximum. A project name, a task
  title, an assignee name, the operator's name and a label do not. *(confirmed with an addition:
  `trail/uxd/cycle-3.md` § 2.1; why, RN-29)*
- Data the UI needs at each step: at the form, the description field's maximum length. At Create,
  the existing project names, because a name already in use is refused (PRD § Core Features,
  Projects, "A project has a name, which is unique").
- Failure/recovery: a blank name or a name already in use is refused under UX-I3. The form keeps
  what was typed, and the reason sits beside the name field.

### 5.3 UX-F3 — Add a task *(→ PRD § Key Use Cases 3; § Core Features, Tasks, Priorities, Assignees, Labels, Due dates)*

- Steps: on a project's Tasks view, the add-task form → title (required), priority (`medium`
  pre-selected), assignee (a choice of the names on the assignee list, or none, pre-selected none),
  due date (optional, a date picker) → Add → the operator lands on the new task's page (UX-S6),
  where labels are added one at a time *(confirmed: `trail/uxd/cycle-1.md` § 2.6; why, RN-27)*.
- Data the UI needs at each step: at the form, the current assignee list. At Add, nothing beyond
  the form.
- Decision point: when the assignee list is empty, the assignee control offers only "none" and a
  link to People, so the operator can see why there is no one to pick.
- Failure/recovery: a blank title is refused under UX-I3, keeping what was typed. A name that is not
  on the assignee list cannot be picked from the control, so that refusal arises only when the list
  changed in another tab after the page loaded. It is then refused under UX-I3. The reason says the
  name is not on the list *(confirmed with an addition: `trail/uxd/cycle-7.md` § 2.1; why, RN-35)*
  and names what is left to do: pick another assignee, or none. It offers no
  reload, because the Tasks view it lands on is built after the refusal, and its assignee control
  already offers only the names now on the list. *(confirmed with an addition: `trail/uxd/cycle-6.md`
  § 2.2; why, RN-34)*

### 5.4 UX-F4 — Move a task to its next status *(→ PRD § Key Use Cases 3; § UX Notes, What must feel effortless, The status workflow is visible and Refusals say why; § Core Features, Status workflow)*

- Steps: on any task list row, or on the task's page, the moves allowed from the task's current
  status appear as buttons, each named by the status it moves to → the operator presses one → the
  move is saved and the operator stays where they were, with the row or page showing the new
  status and a one-line confirmation (UX-I4). A move to `cancelled` takes one more, confirming press,
  with a way to back out (UX-I2). A move to `done` takes effect on the first press. *(confirmed with
  an addition: `trail/uxd/cycle-1.md` § 2.4; why, RN-25)*
- Data the UI needs at each step: for every task shown, its current status and the moves allowed
  from it. A task in `done` or `cancelled` has none, and its row shows no move buttons.
- Failure/recovery: a move the workflow does not allow is refused under UX-I3 and nothing changes.
  On this interface that refusal arises in two ways. The first is a press made after the task was
  moved in another tab, once the page had loaded. The reason states the task's current status and
  the moves that status allows, or that there are none when the status is final, and claims no
  change: the same page is shown again by a reload, by Back or from a bookmark, with no press
  (UX-I3). *(confirmed with an addition: `trail/uxd/cycle-7.md` § 2.1; why, RN-35)* It offers no
  reload: the list or the task's page it lands on is built after the refusal and already shows the
  task's current status and the moves that status allows (UX-I3). *(confirmed with an addition:
  `trail/uxd/cycle-6.md` § 2.2; why, RN-34)* The second is reached by an address, with no press. The address that shows the
  confirmation for a move to `cancelled`, or the one that backs out of it (UX-I2), is opened again by
  a reload, by Back or from a bookmark, once the task's status no longer allows that move. Only
  `done` and `cancelled` are final, so the task is in one of them. Both addresses reach it, on a
  project's Tasks view as well as on the task's page. The refusal shows where the confirmation would
  have been asked for, beside the task's status. It says what is true now, names no action and offers
  no reload (UX-I3). *(confirmed with an addition: `trail/uxd/cycle-5.md` § 2.1; why, RN-33)*
- When the list was filtered by status, the moved task no longer matches the filter. It leaves the
  list, and the confirmation names it, so the operator knows where it went.

### 5.5 UX-F5 — Narrow and sort a task list *(→ PRD § Key Use Cases 4; § UX Notes, What must feel effortless; § Core Features, Filtering, Sorting, Due dates)*

- Steps: on a project's Tasks view or on All tasks, the filter controls sit above the list → the
  operator sets any of status, priority, assignee, label, due from, due to and overdue, and a sort
  field and direction → Apply → the list shows only the matching tasks, sorted, with the count of
  matches and the active choices still shown in the controls → Clear returns the list to no filter
  and the default sort.
- Data the UI needs at each step: the current assignee list (the assignee filter offers those names
  only). The distinct labels carried by tasks in the list's scope, one project or all (the label
  filter offers those labels). For the result: every matching task with the attributes UX-S4 lists,
  its overdue state as of today's local date, and the match count. The whole result is one page,
  with no pagination.
- Defaults: no filter, so every task in the scope shows, `done` and `cancelled` included. Sorted by
  due date ascending: the earliest due comes first, and tasks with no due date come last. Every
  overdue task therefore comes before every task that is not yet due. The order does not put every
  overdue task at the top: a `done` or `cancelled` task with an earlier due date sits above them.
  The overdue filter and the "Overdue" marker are what show overdue work in one action. A list where
  no task has a due date shows in creation order, oldest first. *(confirmed with an addition:
  `trail/uxd/cycle-1.md` § 2.5; why, RN-26)*
- Failure/recovery: a due-date range whose from-date is after its to-date is refused under UX-I3,
  with a reason saying the dates are the wrong way round. A filter that matches nothing shows the
  no-match state (UX-S4, UX-S7), with Clear in view.
- Seeing what is overdue takes one action from any list: the overdue filter. Every listed task that
  is overdue also carries a visible "Overdue" marker in text, beside its due date (UX-A4).

### 5.6 UX-F6 — Open a project's summary *(→ PRD § Key Use Cases 4; § Core Features, Project summary)*

- Steps: on a project, the Summary link → the summary shows the total, the count per status, the
  count per priority, the overdue count, the count with no due date, and each assignee's open-task
  count with unassigned tasks counted as "(unassigned)".
- Every status count, priority count and the overdue count is a link to the project's task list
  filtered to exactly that value, so the summary is also a way into narrowing. The no-due-date count,
  the per-assignee counts and "(unassigned)" are plain numbers. The filter fields the PRD defines
  cannot express "no due date", "open" or "unassigned", so a link from those counts would land on a
  list that does not match the number (PRD § Core Features, Filtering).
- Data the UI needs: every count above, computed as of today's local date for the overdue count.
  Every status and priority shows, a zero included. The per-assignee part shows every name on the
  current assignee list, every name no longer on the list that an open task in the project still
  carries, and "(unassigned)".
- Failure/recovery: an empty project shows its counts as zeros, with the invitation to add a first
  task.

### 5.7 UX-F7 — Comment on a task *(→ PRD § Key Use Cases 5; § Core Features, Comments; § UX Notes, Refusals say why)*

- Steps: on a task's page, the comments list sits under the task's fields, oldest first, each
  comment with its author and the time it was written → the add-comment form sits below the newest
  comment → the operator types and presses Add → the comment appears at the bottom of the list under
  the operator's current name and the time it was written.
- Decision point: when no name is set, a notice above the comment form says a name is needed to
  comment and links to People. The notice is in view before the operator types, so no text is lost
  by going to set a name.
- The add-comment form says beside its text field the most characters a comment can hold, in view
  before the operator submits. A comment cannot be edited once it is added, so text the field did not
  take cannot be put back afterwards. The number is the field's own maximum, on the same terms as the
  description field's in UX-F2. *(confirmed with an addition: `trail/uxd/cycle-3.md` § 2.1; why,
  RN-29)*
- Data the UI needs at each step: the task's comments in written order, each with author and
  written time. Whether an operator name is set, and the name itself. The comment field's maximum
  length.
- Failure/recovery: a comment submitted with no name set, or with blank text, is refused under UX-I3,
  keeping the typed text.

### 5.8 UX-F8 — Set the operator's name and keep the assignee list *(→ PRD § Core Features, Assignees and Comments; § Key Use Cases 3 and 5)*

- Steps: People → **Your name**: type a name → Save, or change it later the same way. **Assignees**:
  type a name → Add. Each name on the list has a Remove button.
- Removing a name needs no confirmation. Nothing is lost by it: the tasks that carry the name keep
  it. The confirmation after a removal says so (PRD § Core Features, Assignees, "Removing a name
  from the list leaves it on the tasks that already carry it").
- Changing the operator's name leaves existing comments as they were written. The Your name section
  says so beside the field (PRD § Core Features, Comments).
- Data the UI needs: the operator's current name or its absence, and the assignee list.
- Failure/recovery: a blank name, or an assignee name already on the list, is refused under UX-I3.

### 5.9 UX-F9 — Edit or delete a task *(→ PRD § Core Features, Tasks, Assignees and Labels)*

- Steps: on a task's page, one form edits title, priority, assignee (a listed name, or none) and due
  date (set, changed or cleared) → Save. Labels have their own control: each label shows with a
  Remove button, and a text field with Add puts on one more. Status has no field in the edit form.
  It changes only through UX-F4. The task's project shows as text and cannot be changed (PRD § Core
  Features, Projects, "A task cannot move between projects").
- **A task whose assignee has left the list.** The assignee control shows that name as its current
  choice, and offers the listed names and none beside it. A save that leaves the control as it showed
  keeps the name. Choosing a listed name or none replaces it, and the replaced name cannot be set on
  any task again until it is added back on People (UX-F8). While the task carries such a name, a
  sentence beside the assignee control says that the name is no longer on the list. The sentence
  also says that choosing another assignee or none replaces the name, which can then be set again
  only after it is added back on People. The sentence sits beside the control, never inside the
  option, and its words are `CONTENT.md`'s. *(confirmed with an addition: `trail/uxd/cycle-3.md`
  § 2.2; why, RN-30)*
- Delete task removes the task and its comments, after the confirmation UX-I2 sets *(confirmed with
  an addition: `trail/uxd/cycle-1.md` § 2.4; why, RN-25)*.
  The operator then lands on the task's project, with a confirmation naming the deleted task.
- Data the UI needs: every editable field's current value, the current assignee list, whether the
  task's assignee is still on that list, and the task's labels.
- Failure/recovery: a blank title is refused under UX-I3. An assignee changed to a name that has left
  the list since the page loaded is refused under UX-I3 as out of date, the same case UX-F3 describes
  for the add-task form. An assignee left as the page showed it is never refused for being off the
  list. *(confirmed with an addition: `trail/uxd/cycle-3.md` § 2.2; why, RN-30)* The refusal says the
  name is not on the list *(confirmed with an addition: `trail/uxd/cycle-7.md` § 2.1; why, RN-35)*
  and names what is left to do: pick another assignee, or none. It offers no
  reload, because the task's page it lands on is built after the refusal and offers the names now on
  the list, showing the refused name only as the choice that failed. *(confirmed with an addition:
  `trail/uxd/cycle-6.md` § 2.2; why, RN-34)* A task that no
  longer exists, because another tab deleted it, shows UX-S10.

### 5.10 UX-F10 — Rename or delete a project *(→ PRD § Core Features, Projects)*

- Steps: on a project's Tasks view, below the list: **Rename** with the current name in a field →
  Save. **Delete project**, whose confirmation names the project and the number of tasks that go
  with it (UX-I2) → the operator lands on Projects, with a confirmation naming the deleted project.
  *(confirmed with an addition: `trail/uxd/cycle-1.md` § 2.4; why, RN-25)*
- Data the UI needs: the project's task count, for the delete confirmation.
- Failure/recovery: a blank name or one already in use is refused under UX-I3.

### 5.11 UX-F11 — Saved data that cannot be read *(→ PRD § UX Notes, Failure states; § UX Notes, Arrival)*

- Steps: the tracker starts, finds saved data it cannot read, and says so in the console (UX-S2) →
  the operator opens the address → every page shows UX-S9: the saved data could not be read, where
  it is, that it has not been changed or overwritten, and that the setup instructions' section on
  setting saved data aside says how to start fresh on purpose → the operator follows that section
  and starts the tracker again → the tracker opens empty (UX-S3, first run), and the set-aside data
  still holds the earlier work.
- Data the UI needs: the saved data's location.
- Failure/recovery: UX-S9 offers nothing that could change the saved data. Its only way forward is
  the instructions.

Key Use Case 2, reading the code and following one feature from the definition to its code and
tests, has no flow here: it happens in the code and the documents, not in the tracker's interface
(§ 10).

## 6. Screen Inventory & States

"Loading" on every page is the same state, and UX-I8 owns it: a page appears when its data is ready,
whole, and the browser's own load indicator is the only one. The rows say only where a page departs
from that.

| ID | Screen | Empty | Loading | Error | Success |
|---|---|---|---|---|---|
| UX-S1 | **Setup instructions** — the written document a reader arrives at. Its sections, in order: what tracker17 is, and its two reasons for existing — a worked example a reader can read end to end, run locally and judge, and kensaiapp's own testing ground, where building tracker17 is how issues in kensaiapp are found and fixed (PRD § Purpose; RN-31) · prerequisites (including the one-time network connection setup needs) · the commands that take a fresh copy to the tracker in the browser · what the start prints, and the address to open · where the saved data is kept · starting the tracker again · setting the saved data aside to start fresh. | n/a — a written document has no empty state. | n/a — a static document. | n/a in the document itself. It is where every console failure in UX-S2 and the browser's "can't reach" page point the reader. | The reader can follow it top to bottom with no section skipped and no choice to make. |
| UX-S2 | **Start command** — the console the tracker is started from. | n/a — the command takes no input. | The console shows nothing until the tracker is ready, then UX-S2 Success. | Plain, one-paragraph messages, each saying what is wrong and what to do: the address is in use by something else · another tracker is already running on the same saved data · the saved data cannot be read (its location named). Nothing is written to the saved data in any of them. | The address to open, and the saved data's location. |
| UX-S3 | **Projects** (home) — every project by name, with its description, sorted by name, ignoring case; the create-project form, which says beside the description field that the description cannot be changed later, and the most characters it can hold (UX-F2). | First run: no projects. The page says there are none yet and invites a first project, with the create form in view. No sample data. | UX-I8. | A create refused under UX-I3 keeps the form filled and shows the reason by the field. A failure that is not a refusal shows UX-I5's message. | The list, and after a create, the new project's Tasks view (UX-F2). |
| UX-S4 | **Project — Tasks** — the project's name and description, the Tasks / Summary links, the filter and sort controls with the match count, the task list, the add-task form, and the rename and delete controls. Each row: title (a link to the task), status, priority, assignee or "unassigned", labels, due date with the "Overdue" marker when it applies, and the moves allowed from the task's status. | Two distinct states. **No tasks yet:** the page says the project has no tasks and invites a first one, with the add-task form in view. **No match:** the filter matched nothing. The page says so, names that the filter is the reason, and shows Clear. Neither shows a blank list. | UX-I8. | Refusals under UX-I3 at the control used. A refusal reached by an address and no control sits beside the task's status in its row (UX-F4). A non-refusal failure shows UX-I5's message. A project that no longer exists shows UX-S10. | The list as filtered and sorted, with the count. After an action, UX-I4's confirmation. |
| UX-S5 | **Project — Summary** — the counts and rows UX-F6 lists, with the status, priority and overdue counts as links. | A project with no tasks: every count shows as 0, and the page invites a first task with a link to the Tasks view. | UX-I8. | A project that no longer exists shows UX-S10. | The counts, as of today's local date. |
| UX-S6 | **Task** — the edit form (title, priority, assignee, due date), the task's project as text, its status with its allowed moves, its labels with Remove and Add, Delete task, and the comments list with the add-comment form, which says beside its text field the most characters a comment can hold (UX-F7). A task whose assignee has left the list shows that name as the assignee control's current choice, with UX-F9's sentence beside the control. | No labels: the label area says the task has none, with Add in view. No comments: the comment area says there are none yet, with the form in view. No operator name: UX-F7's notice above the comment form. | UX-I8. | Refusals under UX-I3 at the control used, keeping what was typed. A refusal reached by an address and no control sits beside the task's status (UX-F4). A non-refusal failure shows UX-I5's message. A task that no longer exists shows UX-S10. | The task as saved. After an action, UX-I4's confirmation. A task in `done` or `cancelled` shows its status with no move buttons. |
| UX-S7 | **All tasks** — UX-S4's filter, sort and list, across every project, with a project column linking to each task's project. No add-task form, because a task is always created in a project. | **No tasks anywhere:** the page says there are no tasks yet and links to Projects. **No match:** as UX-S4. | UX-I8. | As UX-S4. | As UX-S4, across projects. |
| UX-S8 | **People** — Your name, and the assignee list. | No name set: the section says no name is set and that a name is needed to comment. No assignees: the section says there are none and that tasks can be assigned only to names added here. | UX-I8. | Refusals under UX-I3. A non-refusal failure shows UX-I5's message. | The current name and the list. After a removal, the confirmation says the name stays on the tasks that carry it. |
| UX-S9 | **Saved data can't be read** — replaces every page. | n/a — the page exists only because data exists and cannot be read. | UX-I8. | This page is itself the error state. It says plainly that the saved data could not be read, names its location, says nothing was changed or overwritten, and points to the setup instructions' section on setting saved data aside. It offers no control that acts on the data, and no navigation into the tracker. | n/a — the page has no success state. Success is the tracker started fresh, on purpose (UX-F11). |
| UX-S10 | **Not found** — an address for a project or task that does not exist, because it was deleted, possibly in another tab, or the address is wrong. | n/a. | UX-I8. | This page is itself the error state. It says the project or task does not exist, and links to Projects and All tasks. | n/a. |

## 7. Interaction Patterns

- **UX-I1** — **The status workflow is shown, never typed.** Every place a task's status appears
  with the means to change it, which is every list row and the task page, offers exactly the moves
  allowed from its current status, as buttons named by the target status. A final status offers
  none. No control anywhere sets a status directly. *(→ PRD § UX Notes, The status workflow is
  visible; § Core Features, Status workflow)*
- **UX-I2** — **Irreversible actions are confirmed in place, and nothing is undoable.** Deleting a
  project, deleting a task and moving a task to `cancelled` each take a second, confirming press. The
  confirmation appears where the first press was made, not in a dialog. It has three parts, in this
  order: a sentence that states the consequence ("Delete Alpha and its 12 tasks?"), the confirming
  control, and a control that backs out and changes nothing. The back-out control's word must not
  read as the status `cancelled`, and the word itself is `CONTENT.md`'s. The sentence takes the first
  button's place: it covers the whole spot the first button stood in, so the second click of a double
  click lands on words and never on a control. Starting at the same edge as the first button is not
  enough. When the confirmation appears, keyboard focus lands on the sentence, so a keyboard user is
  not sent back to the top of the page when the first button gives way. Focus never lands on the
  confirming control, so a repeated Enter or Space changes nothing. One Tab reaches the confirming
  control, and a second Tab reaches the back-out control. Backing out is the other way the
  confirmation gives way. The first button comes back in the same spot, and keyboard focus returns to
  it, for the same reason. This confirmation takes focus on purpose, so it is not one of the status
  messages UX-A5 says are "announced to assistive technology without moving focus". Those are UX-I4's
  completion lines and UX-I3's refusals. *(confirmed with an addition: `trail/uxd/cycle-2.md` § 2.1;
  why, RN-28)* Every other action, a move to `done` included, takes effect on the first press. No undo exists for any action. The
  confirmations on deletion are required by UX-A5's bar, which includes SC 3.3.4 Error Prevention:
  every deletion stays confirmed while that bar holds. A move to `done` is a status change, not a
  deletion, and stays one press. *(confirmed with an addition: `trail/uxd/cycle-1.md` § 2.4; why,
  RN-25)* *(→ PRD § Core Features, Projects,
  "Deleting a project deletes all of its tasks"; § Core Features, Status workflow, "`done` and
  `cancelled` are final"; § UX Notes, What must feel effortless)*
- **UX-I3** — **A refusal changes nothing and says why, beside the control that was used.** The
  reason is in plain words. Every refusal in this tracker is read from its page's address, so a
  reload, Back or a bookmark shows it again with no press. A refusal therefore states what holds
  when its page is built, never an event before it. *(confirmed with an addition:
  `trail/uxd/cycle-7.md` § 2.1; why, RN-35)* Where something is left for the operator to do, the
  refusal names what to do. Everything the operator typed stays in the form. A refusal caused by the
  page being out of date, because another tab changed or moved the task, names what is left to do
  on the page it lands on. *(confirmed with an addition:
  `trail/uxd/cycle-7.md` § 2.1; why, RN-35)* It offers a reload only where the page that shows it
  is itself still out of date. *(confirmed with an addition: `trail/uxd/cycle-6.md` § 2.2; why,
  RN-34)* **One kind of
  refusal names no action and offers no reload:** the state the operator wanted already holds, and the
  page the refusal lands on already shows it. That page is loaded after the refusal, from the saved
  data, so a reload would show nothing new, and the refusal says what is true now. Removing a label
  the task no longer carries is one such refusal: it lands on the task's page, which lists the task's
  current labels. Removing an assignee already off the list is another: it lands on People, which
  shows the current list. Where the wanted state does not hold, the out-of-date refusal still names
  what to do. A status move another tab overtook (UX-F4) is that case, and so is an assignee who
  left the list before an add or an edit (UX-F3, UX-F9). *(confirmed with an addition:
  `trail/uxd/cycle-4.md` § 2.1; why, RN-32)* The overtaken move names the moves the page now shows,
  or none for a final status, and the assignee refusals name picking another assignee or none. Each
  lands on a page built after the refusal, so none of them offers a reload. *(confirmed with an
  addition: `trail/uxd/cycle-6.md` § 2.2; why, RN-34)* **A refusal reached by an address and no
  control is a case of its own.** The page's address asks for a step the task's status no longer
  allows, and the operator pressed nothing to get there (UX-F4). The page was just built from the
  saved data, so it is not out of date, and with the task in a final status nothing is left for the
  operator to do. The refusal says what is true now, names no action and offers no reload, for a
  task in `done` and a task in `cancelled` alike. No control was used, so it sits beside the task's
  status, in the row or on the page. *(confirmed with an addition: `trail/uxd/cycle-5.md` § 2.1;
  why, RN-33)* Rules are checked when the action is
  submitted: no field is checked while the operator types. *(→ PRD § UX Notes, Refusals say why)*
- **UX-I4** — **A completed action is confirmed in one line, on the page it leaves the operator
  on.** The line names what changed ("Moved 'Set up CI' to done"). A result is shown only once it
  is saved: no page shows an action as done before that. *(→ PRD § UX Notes, Persistence and
  Refusals say why)*
- **UX-I5** — **A failure that is not a refusal says so, and changes nothing.** When an action fails
  for a reason the rules did not produce, the page says in plain words that the action did not
  happen and nothing was changed, and keeps what was typed. *(→ PRD § UX Notes, Refusals say why
  and Failure states)*
- **UX-I6** — **The keyboard model is the browser's own.** Tab moves through every control in
  reading order, Enter submits the form the focus is in, and Space or Enter presses a button. The
  tracker adds no keyboard shortcuts of its own. *(→ PRD § UX Notes, Defaults, "every action usable
  from the keyboard"; § Goals, It is simple)*
- **UX-I7** — **A list's filter and sort choices live in its address, and nowhere else.** Applying a
  filter changes the page's address, so reload, back and a bookmark all keep the narrowed list.
  Choices are not saved between sittings: a fresh visit to a list shows the defaults UX-F5 states.
  *(→ PRD § UX Notes, What must feel effortless, "narrowing a list to what matters right now")*
- **UX-I8** — **A page appears whole, or not at all.** No page shows partial content, a placeholder
  or a spinner while its data loads. The browser's own load indicator is the only loading state.
  *(→ PRD § Goals, It is simple; `system/experience/visual_restrictions.md` § 2,
  `no-placeholder-delivery`)*
- **UX-I9** — **Pages do not update themselves.** A page shows the data as it stood when it was
  loaded. The operator reloads to see a change made in another tab. *(→ PRD § Out of Scope,
  "Real-time collaboration and notifications")*

## 8. Accessibility Requirements

- **UX-A1** — Every action in the tracker can be done with the keyboard alone, with no keyboard trap
  (WCAG 2.2 SC 2.1.1 Keyboard, SC 2.1.2 No Keyboard Trap). *(overridden: `trail/uxd/cycle-1.md`
  § 2.3; why, RN-24)* *(→ PRD § UX Notes, Defaults, "every action usable from the keyboard")*
- **UX-A2** — Every control shows a visible focus indicator when it has keyboard focus (WCAG 2.2
  SC 2.4.7 Focus Visible). *(overridden: `trail/uxd/cycle-1.md` § 2.3; why, RN-24)* *(→ PRD § UX
  Notes, Defaults — derived from UX-A1, RN-4)*
- **UX-A3** — Every refusal and failure is identified in text, associated with the control it
  concerns, and describes how to correct it where a correction exists (WCAG 2.2 SC 3.3.1 Error
  Identification, SC 3.3.3 Error Suggestion). *(overridden: `trail/uxd/cycle-1.md` § 2.3; why,
  RN-24)* For a refusal reached by an address and no control (UX-I3), the control it concerns is the
  task's status, and the refusal is associated with that. *(confirmed with an addition:
  `trail/uxd/cycle-5.md` § 2.1; why, RN-33)* *(→ PRD § UX Notes, Refusals say why)*
- **UX-A4** — Status, priority and the overdue state are each shown in text, never by colour alone
  (WCAG 2.2 SC 1.4.1 Use of Color). *(overridden: `trail/uxd/cycle-1.md` § 2.3; why, RN-24)* *(→ PRD
  § UX Notes, What must feel effortless, "seeing which tasks are overdue")*
- **UX-A5** — The tracker conforms to WCAG 2.2 Level AA in full on its pages, including text contrast
  (SC 1.4.3), contrast of controls and focus indicators (SC 1.4.11), a label for every form field
  (SC 1.3.1, SC 3.3.2), a title for every page (SC 2.4.2), the page language set to English
  (SC 3.1.1), and confirmations and refusals announced to assistive technology without moving focus
  (SC 4.1.3 Status Messages). *(overridden: `trail/uxd/cycle-1.md` § 2.3; why, RN-24)* *(→ PRD § UX
  Notes, Defaults)*
- **UX-A6** — Every control the operator presses with a pointer, a mouse included, meets the 24 by 24
  CSS pixel target floor or one of the exceptions WCAG 2.2 SC 2.5.8 Target Size (Minimum) names. It
  matters most for the move buttons that sit side by side on every list row, where a slip onto
  `done` cannot be undone (UX-I2). *(overridden: `trail/uxd/cycle-1.md` § 2.3; why, RN-24)* *(→ PRD
  § UX Notes, Defaults)*
- **UX-A7** — At 400% zoom of a 1280-pixel-wide browser window, every page reads without scrolling in
  two directions (WCAG 2.2 SC 1.4.10 Reflow). The task tables are exempt, because the criterion
  exempts data tables. The header, the forms, the filter controls, the summary and People are not.
  This is not a phone layout, and § 9's desktop constraint stands beside it. *(overridden:
  `trail/uxd/cycle-1.md` § 2.3; why, RN-24)* *(→ PRD § UX Notes, Defaults)*
- **Reduced motion: n/a** — the motion dial is 1 (§ 2), and the tracker animates nothing, so there is
  no motion to reduce.

## 9. Design-System Direction

- Direction: **plain semantic HTML with the browser's own form controls, styled by one small
  stylesheet the product writes itself — built from primitives, with no component library or
  design-system package** *(confirmed with an addition: `trail/uxd/cycle-1.md` § 2.1; why,
  RN-22)*. Reasoning: the reader reads the whole product (PRD § Goals,
  It is simple), and a design-system package is a dependency and a body of styling code they would
  also have to read or take on trust. Native controls bring keyboard operation (UX-A1) with them.
  The look is deliberate, not a default: quiet, conventional, and recognisably an app (§ 1).
- Constraints the design language must satisfy:
  - **Nothing is loaded from outside the machine.** No hosted font, stylesheet, icon set or script.
    Every asset the pages use ships in the copy (PRD § Data & Privacy, "None of it leaves the
    machine"; § Dependencies / Integrations, "No outside service").
  - **No control is left half-styled.** The design language states which controls it styles, and
    styles every instance of each one. A control left in the browser's default look beside the
    product's own styling breaks `system/experience/visual_restrictions.md` § 2,
    `no-placeholder-delivery`.
  - **One colour mode, and no mode switch.** Which mode is the design language's call. The
    browser's own controls and pop-ups, the date picker, select lists and scrollbars included,
    render in that same mode, so no native control shows in the other mode beside the product's
    styling. `DESIGN.md` states this alongside the mode it picks. *(confirmed with an addition:
    `trail/uxd/cycle-1.md` § 2.1; why, RN-22)*
  - **The contrast floor UX-A5 sets**, on every text and control colour, and a focus indicator that
    meets it (UX-A2).
  - **The target-size floor UX-A6 sets**, on every control a pointer presses.
  - **Status, priority and overdue read without colour** (UX-A4). Colour may reinforce them, never
    carry them alone.
  - **Built for a desktop browser window.** No phone layout is designed (PRD § UX Notes, Defaults).
    Outside the task tables, no page assumes a wide window: UX-A7's reflow holds at 400% zoom.
  - **One row per task, with each attribute in its own column**, at a desktop width (§ 2, DENSITY).
    A title or a set of labels longer than its column wraps inside its cell, and never pushes an
    attribute onto a second row. *(confirmed with an addition: `trail/uxd/cycle-1.md` § 2.2; why,
    RN-23)*
- Design language: `products/tracker17/docs/DESIGN.md` (authored by `product-design` off this
  direction; may trail the SDD).

## 10. Out of Scope

This UXD is scoped against the project's 上がり Agari, `system/projects/tracker17/agari.md`: done is
the owner passing the PRD's three bars, Works, Simple to set up and Simple to read, on one
run-through on their own machine. The Agari places two things outside done, and this UXD designs
neither:

- **Publishing, and an outside reader.** No public landing page, no "about" page, and no link to a
  public repository or download location (`system/projects/tracker17/agari.md`, "What this
  Agari does not require").
- **Re-checking the bars on later releases.** No in-app release notes or version display serves it.

What the PRD places out of scope, and therefore has no screen, control or state here:

- **Use by anyone but the operator, and any reach beyond the machine.** No sign-in, account,
  sign-out or "signed in as" (PRD § Out of Scope, Hosting and Login).
- **Live updates and notifications.** No badge, alert, unread count or self-refreshing page (UX-I9).
- **Export.** No export or download control.
- **Threaded replies.** Comments are one flat list, with no reply control.
- **More than one value per filter field, or more than one sort field.** Every filter control takes
  one value, and the sort control takes one field.
- **Moving a task between projects.** The task's project is shown as text, never as a field.
- **A summary across projects.** All tasks has no summary view.
- **A command-line interface.** The console is used only to start and stop the tracker (UX-S2).
  tracker16-X's command names, flags and `+3d` dates have no counterpart.
- **A package, an installer or a hosted demo.** UX-S1 starts from a copy of the source.
- **A phone layout.**
- **Sample data, a guided tour, or onboarding beyond the empty states.** The tracker opens empty
  (PRD § UX Notes, First run).

What this UXD itself does not design:

- **Key Use Case 2, reading the code and following one feature to its code and tests.** The tracker's
  interface does not carry it: it happens in the code and the documents. What makes the trace
  followable is the SRS's (NFR-9) and the documents' that come after.
- **Undo, and app-specific keyboard shortcuts** — not designed, by UX-I2 and UX-I6.
- **Filter and sort choices remembered between sittings** — not designed, by UX-I7.
- **Editing a project's description after creation.** A project's description is fixed at
  creation, and Rename and Delete are the only changes to a project. *(answered:
  `trail/uxd/cycle-1.md` § 1.1; why, RN-21)*

## 11. Traceability

| UXD entry | PRD source |
|---|---|
| UX-U1 | § Target Users, The operator; § UX Notes, Defaults |
| UX-U2 | § Target Users, The reader; § Key Use Cases 1; § Assumptions |
| UX-F1 | § Key Use Cases 1; § Purpose; § UX Notes, Arrival, Failure states; § Success Metrics, Simple to set up |
| UX-F2 | § Key Use Cases 3; § UX Notes, First run, Refusals say why; § Core Features, Projects |
| UX-F3 | § Key Use Cases 3; § Core Features, Tasks, Priorities, Assignees, Labels, Due dates |
| UX-F4 | § Key Use Cases 3; § UX Notes, What must feel effortless, The status workflow is visible, Refusals say why; § Core Features, Status workflow |
| UX-F5 | § Key Use Cases 4; § UX Notes, What must feel effortless; § Core Features, Filtering, Sorting, Due dates |
| UX-F6 | § Key Use Cases 4; § Core Features, Project summary |
| UX-F7 | § Key Use Cases 5; § Core Features, Comments; § UX Notes, Refusals say why |
| UX-F8 | § Core Features, Assignees, Comments; § Key Use Cases 3, 5 |
| UX-F9 | § Core Features, Tasks, Assignees, Labels, Projects |
| UX-F10 | § Core Features, Projects |
| UX-F11 | § UX Notes, Failure states, Arrival |
| UX-S1 | § Purpose; § UX Notes, Arrival, Failure states; § Scope (In); § Data & Privacy, Deletion |
| UX-S2 | § Key Use Cases 1; § UX Notes, Arrival, Failure states |
| UX-S3 | § Core Features, Projects; § UX Notes, First run, Refusals say why |
| UX-S4 | § Core Features, Tasks, Filtering, Sorting, Due dates; § UX Notes, First run, What must feel effortless |
| UX-S5 | § Core Features, Project summary |
| UX-S6 | § Core Features, Tasks, Assignees, Labels, Comments, Status workflow; § UX Notes, Refusals say why |
| UX-S7 | § Core Features, Filtering; § Key Use Cases 4 |
| UX-S8 | § Core Features, Assignees, Comments |
| UX-S9 | § UX Notes, Failure states |
| UX-S10 | § Core Features, Projects, Tasks (deletion) |
| UX-I1 | § UX Notes, The status workflow is visible; § Core Features, Status workflow |
| UX-I2 | § Core Features, Projects, Status workflow; § UX Notes, What must feel effortless |
| UX-I3 | § UX Notes, Refusals say why |
| UX-I4 | § UX Notes, Persistence, Refusals say why |
| UX-I5 | § UX Notes, Refusals say why, Failure states |
| UX-I6 | § UX Notes, Defaults; § Goals, It is simple |
| UX-I7 | § UX Notes, What must feel effortless |
| UX-I8 | § Goals, It is simple |
| UX-I9 | § Out of Scope, Real-time collaboration and notifications |
| UX-A1 | § UX Notes, Defaults |
| UX-A2 | § UX Notes, Defaults |
| UX-A3 | § UX Notes, Refusals say why |
| UX-A4 | § UX Notes, What must feel effortless |
| UX-A5 | § UX Notes, Defaults |
| UX-A6 | § UX Notes, Defaults |
| UX-A7 | § UX Notes, Defaults |

**Every unit of the PRD's enumerable sections is accounted for.** Key Use Cases 1, 3, 4 and 5 land
as flows, and Key Use Case 2 has its line in § 10. Every Core Feature lands in a flow or a screen,
except **Tested throughout**, which has no interface: the tests are the reader's to read, under
Key Use Case 2. Both Target Users land as UX-U1 and UX-U2. The Goals **It is simple** and **It
works** shape the dials, UX-I6 and UX-I8. **Simple to set up** lands in UX-F1 and UX-S1. **It costs
nothing to run** lands in § 9's nothing-from-outside constraint. Every `## UX Notes` item lands in a
flow, a screen or a pattern. Every Out of Scope item has its line in § 10. PRD § Purpose's second
purpose, kensaiapp's own testing ground, has no interface of its own. Its one experience
requirement, that a reader learns both purposes from the first thing they read, lands in UX-S1
(RN-31).

---

## UXD Review Notes

- **RN-1:** *(added)* The setup instructions' section order in UX-S1, and the console's start and
  failure messages in UX-S2 — *because* PRD § UX Notes, Arrival names what the instructions state,
  and PRD § Success Metrics, Simple to set up makes "only the written instructions" the whole path. A
  reader following one path top to bottom needs the sections in the order the path uses them. The
  console is where the last command leaves them, and it must say what to open next. *(re: UX-F1,
  UX-S1, UX-S2; PRD source: § UX Notes, Arrival, Failure states)*
- **RN-2:** *(added)* The information architecture, with Projects as home, a project's Tasks and
  Summary views, All tasks and People — *because* PRD § UX Notes, First run has the tracker open by
  inviting a first project, which makes the project list the home. PRD § Core Features, Filtering
  covers "within one project or across all projects", which needs both list scopes. The operator's
  name and the assignee list are both names typed in once and used everywhere, so they share one
  place. This is the CDO's derivation. *(re: § 4; PRD source: § UX Notes, First run; § Core
  Features)*
- **RN-3:** *(added)* No account-like element on any page — *because* PRD § Risks says "'small team'
  can mislead a reader" into expecting several people, and an element that reads as an account
  would invite exactly that reading. *(re: § 3, § 10; PRD source: § Risks; § Out of Scope, Login)*
- **RN-4:** *(added)* UX-A2 focus visible — *because* PRD § UX Notes, Defaults requires every action
  to be usable from the keyboard, and a keyboard user cannot use a control they cannot see is
  focused. The CDO's derivation from UX-A1. *(re: UX-A2; PRD source: § UX Notes, Defaults)*
- **RN-5:** *(added)* Status moves offered on every list row, not only on the task's page —
  *because* PRD § UX Notes names "moving a task to its next status" as an action that must feel
  effortless, and a move that needs a page change first is two actions where one serves. *(re:
  UX-F4, UX-S4, UX-I1; PRD source: § UX Notes, What must feel effortless)*
- **RN-6:** *(added)* The one-line confirmation after every completed action (UX-I4) — *because* a
  status move under a status filter makes the task leave the list, and with no confirmation the
  operator sees a task vanish. PRD § UX Notes, Refusals say why tells the operator what did not
  happen, and UX-I4 is the same courtesy for what did. *(re: UX-I4, UX-F4; PRD source: § UX Notes,
  Refusals say why, Persistence)*
- **RN-7:** *(added)* UX-I5, the message for a failure that is not a refusal — *because* PRD § UX
  Notes, Refusals say why bars an action that fails without a reason, and a failure that is not a
  rule's refusal can still happen. *(re: UX-I5; PRD source: § UX Notes, Refusals say why, Failure
  states)*
- **RN-8:** *(added)* Rules checked at submit, never while typing (UX-I3) — *because* the rules a
  refusal enforces, such as a unique project name or a name on the assignee list, are checked
  against the saved data when the action is applied. Checking them live as well would be a second
  copy of each rule for the reader to read, against PRD § Goals, It is simple. The CDO's
  derivation. *(re: UX-I3; PRD source: § UX Notes, Refusals say why; § Goals, It is simple)*
- **RN-9:** *(added)* The keyboard model is the browser's own, with no shortcuts (UX-I6) — *because*
  PRD § UX Notes, Defaults asks that every action be usable from the keyboard, which native focus
  order and native controls satisfy. Shortcuts would add code and a second way to do each action,
  against PRD § Goals, It is simple. *(re: UX-I6; PRD source: § UX Notes, Defaults; § Goals, It is
  simple)*
- **RN-10:** *(added)* Filter and sort choices in the page address, not saved between sittings
  (UX-I7) — *because* pages do not update themselves (UX-I9), so reload is how the operator sees a
  change, and a reload that dropped the narrowed list would make narrowing anything but effortless.
  Saving choices between sittings would add stored state that no PRD item asks for. *(re: UX-I7,
  UX-F5; PRD source: § UX Notes, What must feel effortless)*
- **RN-11:** *(added)* The assignee and label filters offer choices rather than free text — *because*
  a filter field matches one exact value (PRD § Core Features, Filtering, "Each field takes one
  value"), and a free-text label typed slightly differently from the one on the task would match
  nothing with no sign why. Offering the labels the tasks in scope carry makes narrowing by label
  one pick. *(re: UX-F5; PRD source: § UX Notes, What must feel effortless; § Core Features,
  Filtering, Labels)*
- **RN-12:** *(added)* No default filter: every task shows until the operator narrows — *because*
  "open" is two statuses and the status filter takes one value (PRD § Core Features, Filtering), so
  a default that hid finished tasks could not be expressed by the filter controls and a task would
  disappear from a list with no control showing why. *(re: UX-F5; PRD source: § Core Features,
  Filtering)*
- **RN-13:** *(added)* Summary counts that link to a filtered list, and the counts that do not —
  *because* Key Use Case 4 moves from narrowing to the summary and back, and PRD § UX Notes asks that
  narrowing feel effortless. The no-due-date, per-assignee and unassigned counts cannot link: the PRD's
  filter fields cannot express them, and a link to a list that does not match its number would
  mislead. *(re: UX-F6, UX-S5; PRD source: § Key Use Cases 4; § Core Features, Filtering, Project
  summary)*
- **RN-14:** *(added)* The project list sorted by name, ignoring case — *because* project names are
  unique and are how the operator tells projects apart (PRD § Core Features, Projects), so name order
  is where an operator looks for one. The CDO's derivation. *(re: UX-S3; PRD source: § Core
  Features, Projects)*
- **RN-15:** *(added)* The no-name notice above the comment form (UX-F7) — *because* PRD § Core
  Features, Comments says a comment cannot be added until a name is set, and an operator who learns
  that only after typing would lose the text by going to set the name. *(re: UX-F7, UX-S6; PRD
  source: § Core Features, Comments; § UX Notes, Refusals say why)*
- **RN-16:** *(added)* Removing an assignee needs no confirmation, and its confirmation line says the
  name stays on tasks — *because* the removal loses nothing (PRD § Core Features, Assignees), so a
  confirming press would guard nothing, and the line answers the question the removal raises.
  *(re: UX-F8, UX-S8; PRD source: § Core Features, Assignees)*
- **RN-17:** *(added)* UX-S10, the not-found page, and the out-of-date refusal in UX-I3 — *because*
  projects and tasks can be deleted (PRD § Core Features, Projects, Tasks) and each has an address
  (§ 4), so an address can outlive what it names. Two tabs on one tracker make that happen without
  any mistake on the operator's part. *(re: UX-S10, UX-I3; PRD source: § Core Features, Projects,
  Tasks)*
- **RN-18:** *(added)* UX-S9 offers no control that acts on the saved data — *because* PRD § UX Notes,
  Failure states says the tracker "never overwrites saved data it couldn't read" and that the
  instructions say how to set it aside. A button in the tracker that set data aside would be a second
  way to do what the instructions own. *(re: UX-S9, UX-F11; PRD source: § UX Notes, Failure states)*
- **RN-19:** *(added)* No pagination: a task list's whole result is one page — *because* the product
  models one small team's work (PRD § Target Users), and pages of results would add controls and
  state for no PRD item. The sibling SRS does not collide with it: its volume bar
  (`products/tracker17/docs/SRS.md` § 4.1, NFR-1) asks every action to show its result within a
  second at up to 1,000 tasks, which a single page does not rule out. *(re: UX-F5; PRD source:
  § Target Users; § Goals, It is simple)*
- **RN-20:** *(added)* `system/experience/visual_restrictions.md` § 2, `role-visibility`, binds and is
  moot here — *because* tracker17 shows the operator's own projects and tasks and no work the
  pipeline produced, which is the case that entry names as moot. Its counterpart in
  `system/experience/voice_restrictions.md` § 2 is moot on the same ground. *(re: § 9; PRD source:
  § Blurb)*
- **RN-21:** *(added)* A project's description is fixed at creation, and the create form says so
  beside the field — *because* the PRD lists projects as "created, listed, renamed and deleted" and
  names no way to change a description (PRD § Core Features, Projects). The answer kept that list as
  written (`products/tracker17/docs/trail/uxd/cycle-1.md` § 1.1). A mistyped description can then be
  fixed only by deleting the project and creating it again, which deletes its tasks. The note beside
  the field puts that cost in front of the operator before the project exists, the same way UX-F8
  explains the Your name field. *(re: UX-F2, UX-S3, § 10; PRD source: § Core Features, Projects)*
- **RN-22:** *(added)* The design-system direction, plain HTML with the browser's own controls and
  one hand-written stylesheet, in one colour mode with no switch — *because* the reader reads the
  whole product (PRD § Goals, It is simple), and a design-system package is more code to read or take
  on trust, against PRD § Risks, "a web interface adds parts". The direction is a taste call, and it
  was confirmed (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.1). The same answer added that
  native controls and pop-ups render in the product's one mode. A pop-up such as the date picker
  cannot be styled by a stylesheet and follows the mode the browser is told the page uses, so a
  control in the other mode would be the half-styled control `system/experience/visual_restrictions.md`
  § 2, `no-placeholder-delivery`, forbids. *(re: § 1, § 9; PRD source: § Goals, It is simple; § Risks)*
- **RN-23:** *(added)* DENSITY 6 and TYPOGRAPHY 2, and long text wrapping inside its cell — *because*
  how tightly rows pack and how much character the type carries are taste calls the PRD does not
  make, and both values were confirmed (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.2). The
  answer also read § 9's row constraint as one row per task with each attribute in its own column. A
  task carries any number of labels (PRD § Core Features, Tasks), so no single line of text can hold
  every row. How a cell wraps or shortens stays with `DESIGN.md`, under this document's open question
  on long text. *(re: § 2, § 9; PRD source: § Core Features; § Key Use Cases 4; § Why This)*
- **RN-24:** *(added)* The accessibility bar is WCAG 2.2 Level AA in full — *because* the PRD names
  keyboard use and no other accessibility need (PRD § UX Notes, Defaults), and the instance fences no
  floor (`system/experience/visual_restrictions.md` § 3, "An accessibility floor: n/a"), so a bar
  above the keyboard requirement is a taste call. The answer set the level and the version
  (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.3). WCAG 2.2 keeps every 2.1 criterion except
  4.1.1 Parsing (W3C, https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/). Two consequences
  follow, and the answer states both. SC 2.5.8 Target Size (Minimum) applies to any pointer, a mouse
  included, which gives UX-A6. SC 1.4.10 Reflow is Level AA, which gives UX-A7, and the criterion
  exempts data tables (W3C, https://www.w3.org/WAI/WCAG21/Understanding/reflow.html). *(re: UX-A1 to
  UX-A7, § 9; PRD source: § UX Notes, Defaults)*
- **RN-25:** *(added)* Deleting a project, deleting a task and moving a task to `cancelled` are
  confirmed in place, with a back-out control and focus on the confirmation, and nothing is undoable —
  *because* deletion cascades (PRD § Core Features, Projects, "Deleting a project deletes all of its
  tasks") and both final statuses cannot be left (PRD § Core Features, Status workflow, "`done` and
  `cancelled` are final"), while a move to the next status must feel effortless (PRD § UX Notes). The
  split was confirmed (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.4). The answer added the
  back-out control, so a pending destructive step can be refused, and focus on the confirmation, so
  UX-A1's every-action-by-keyboard holds when the first button gives way. It also recorded that SC
  3.3.4 Error Prevention, inside UX-A5's bar, requires deletions to stay confirmed or undoable, so
  removing the confirmations is closed while that bar holds. A move to `done` is a status change, not
  a deletion, and the criterion does not reach it
  (https://www.w3.org/WAI/WCAG21/Understanding/error-prevention-legal-financial-data.html). *(re:
  UX-I2, UX-F4, UX-F9, UX-F10; PRD source: § Core Features, Projects, Status workflow; § UX Notes,
  What must feel effortless)*
- **RN-26:** *(added)* A task list's default order is by due date, earliest first — *because* the PRD
  sets ascending as the default direction and names no default field (PRD § Core Features, Sorting),
  and the default was confirmed (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.5). The answer
  corrected the reason. With no default filter (RN-12), a finished task with an earlier due date sorts
  above the overdue ones, so the order does not put every overdue task at the top. What it does
  guarantee is that every overdue task comes before every task not yet due. A list where no task has
  a due date falls back to creation order, oldest first, the tie rule the sibling SRS also states
  (`products/tracker17/docs/SRS.md` FR-36, "Ties"). *(re: UX-F5; PRD source: § Core Features,
  Sorting; § UX Notes, What must feel effortless)*
- **RN-27:** *(added)* After Add, the operator lands on the new task's page, where labels go on one at
  a time — *because* labels are added "one at a time" (PRD § Core Features, Labels), which keeps them
  out of the add-task form. The choice was confirmed with its reason corrected
  (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.6). One way to add a label does not choose
  between landing on the task and staying on the project. What decides it is that a new task starts
  in `todo` with no labels (PRD § Core Features, Status workflow; Labels), so under a status, label or
  assignee filter it often would not appear in the list the operator stayed on, and in a long sorted
  list it could land out of view. The task's page shows the task whole, as saved (UX-I4). The cost is
  accepted: adding several tasks in a row means returning to the project each time. *(re: UX-F3;
  PRD source: § Key Use Cases 3; § Core Features, Labels)*
- **RN-28:** *(added)* UX-I2's confirmation puts its sentence first, covering the first button's
  whole spot and taking focus, then the confirming control, then the back-out control. Backing out
  restores the first button and returns focus to it. The confirmation is not one of UX-A5's status
  messages. *Because* the confirmation is the only guard on a deletion that cannot be undone (UX-I2),
  and a second press meant for the first button would otherwise reach the confirming control. With a
  pointer, the second click of a double click lands on whatever replaced the first button. With the
  keyboard, Enter or Space presses the focused button (UX-I6). Deleting a project deletes every task
  in it (PRD § Core Features, Projects, "Deleting a project deletes all of its tasks"). The order and
  the focus were confirmed, with three additions (`products/tracker17/docs/trail/uxd/cycle-2.md`
  § 2.1). The sentence covers the whole spot the first button stood in, not only its starting edge.
  Focus returns to the restored first button on backing out, for the reason UX-I2 already gives for
  where focus goes when the confirmation appears. UX-I2 says outright that its confirmation takes focus
  on purpose, because UX-A5 uses the word "confirmations" for UX-I4's completion lines. W3C defines a
  status message as a "change in content that is not a change of context", and says that changes of
  context "by their nature, interrupt the user by taking focus"
  (https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html). On this reading, SC 4.1.3 does
  not reach UX-I2's confirmation, and UX-A5 stands as written. *(re: UX-I2, UX-A5, UX-F4, UX-F9,
  UX-F10; PRD source: § Core Features, Projects, Status workflow)*
- **RN-29:** *(added)* The comment field and the project-description field each state their maximum
  length beside the field, and no other field does. *Because* a browser may stop text at a field's
  maximum and is not required to say so. The HTML standard's words are "User agents may prevent the
  user from causing the element's API value to be set to a value whose length is greater than the
  element's maximum allowed value length"
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Limiting user input
  length: the `maxlength` attribute"). On this reading, a field that quietly takes less than the
  operator entered has refused part of the entry with no reason, which PRD § UX Notes, Refusals say
  why, rules out. In these two fields the loss cannot be repaired. A comment cannot be changed (PRD
  § Core Features, Comments, "Comments can't be edited or deleted"), and a description is fixed at
  creation (UX-F2, RN-21). The other five fields hold one line each, so a value cut short is in view
  in the field, and each can be put right afterwards: a project is renamed (UX-F10), a title or the
  operator's name is edited (UX-F9, UX-F8), and a label or an assignee name is removed and added
  again. A sentence beside each of them would add a line to every form for a rare case, against PRD
  § Goals, It is simple. The number a sentence states is the field's own maximum, from the one place
  that also sets the field's limit, so the two cannot disagree. The maximums themselves are
  `products/tracker17/docs/SRS.md` FR-40's, and this document repeats none of them. The sentence
  beside a field is the device UX-F2 and UX-F8 already use. The two fields were confirmed with three
  additions (`products/tracker17/docs/trail/uxd/cycle-3.md` § 2.1): the other five fields state no
  maximum, the number comes from the same place as the field's limit, and the long-text open question
  cites FR-40 in place of an SRS section that no longer exists. *(re: UX-F2, UX-F7, UX-S3, UX-S6,
  § Open Questions; PRD source: § Core Features, Comments, Projects; § UX Notes, Refusals say why;
  § Goals, It is simple)*
- **RN-30:** *(added)* The task's edit form shows an assignee who has left the list as its current
  choice, a sentence beside the control says the name is off the list, and UX-F9 refuses only an
  assignee changed to a name that left the list after the page loaded. *Because* a removed name stays
  on the tasks that carry it (PRD § Core Features, Assignees, "Removing a name from the list leaves it
  on the tasks that already carry it"), so a task carrying such a name is an ordinary state. A
  control that offered only listed names and none would show that task as unassigned or as someone
  else, while UX-S6 shows "The task as saved". Read as first written, UX-F9's refusal line would also
  have refused every save of that task. The behaviour was confirmed with an addition
  (`products/tracker17/docs/trail/uxd/cycle-3.md` § 2.2), and the addition is the sentence. Without
  it, the name looks like any listed choice, although it is offered on this task only and is lost
  from it once the operator chooses another. The sentence goes beside the control and not inside the
  option, because a closed choice control may show a long name cut short, and a note after the name
  would be the part cut. *(re: UX-F9, UX-S6; PRD source: § Core Features, Assignees, Tasks)*
- **RN-31:** *(added)* The setup instructions open with what tracker17 is and its two reasons for
  existing, ahead of the prerequisites. *Because* PRD § Purpose says "A reader learns both purposes
  from the first thing they read about tracker17", and PRD § UX Notes, Arrival says "A reader
  arrives at the written setup instructions". On that reading the setup instructions are the first
  thing a reader reads, and their opening is the first part of them read. The placement is this
  CDO's derivation from those two sentences. The section is not a step on the path the other
  sections follow in order (RN-1): it comes first because it is read first. It sits in the written
  document and on no page of the tracker, so § 10's line against an "about" page stands. How the
  section is worded is the verbal standard's, `products/tracker17/docs/CONTENT.md`. *(re: UX-S1,
  UX-F1; PRD source: § Purpose; § UX Notes, Arrival)*
- **RN-32:** *(added)* UX-I3 names what to do only where something is left to do. A refusal whose
  wanted state already holds, shown on a page loaded after it that already shows that state, says
  what is true now and names no action and offers no reload. *Because* the PRD asks a refusal only to
  tell "the reason in plain words" (PRD § UX Notes, Refusals say why), and names no action it must
  carry. UX-A3 in this document already asks a refusal to describe how to correct it "where a
  correction exists", so an unconditional "names what to do" in UX-I3 disagreed with UX-A3. The verbal
  standard gives one next action "when one exists, and none when none does"
  (`products/tracker17/docs/CONTENT.md` § Voice), and its refusal formula ends with "one action where
  one exists" (`products/tracker17/docs/CONTENT.md` § Message patterns, *A refusal*). Where the state
  the operator wanted already holds and the page shows it, the only action left is a reload that shows
  nothing new. The exception was confirmed with two additions
  (`products/tracker17/docs/trail/uxd/cycle-4.md` § 2.1). The first bounds the exception by where the
  refusal is shown, not only by what was refused. A reload offers something only on a page that is
  still out of date, so where the wanted state does not hold the refusal still names what to do, in
  UX-F3, UX-F4 and UX-F9. Whether those refusals also offer a reload is RN-34's. The second names
  the assignee refusal on People as a second refusal of the same kind. The same answer records that the product's People refusal still
  offers a reload, and that meeting UX-I3 is a change to that string, not to this document. RN-17's
  reason for the out-of-date refusal still holds for every page that is still out of date. *(re:
  UX-I3, UX-A3, UX-F3, UX-F4, UX-F9; PRD source: § UX Notes, Refusals say why)*
- **RN-33:** *(added)* A move refusal reached by an address and no press is kept. It is a case of
  its own in UX-I3: it says what is true now, names no action, offers no reload, and sits beside the
  task's status. UX-F4 names it as the second way a move refusal arises. *Because* the address asks
  for a step, the confirmation of a move to `cancelled` or the backing out of it, and the page then
  does not show it. With no line, the step would vanish with no reason, and the PRD has a refused
  action tell "the reason in plain words" (PRD § UX Notes, Refusals say why). The case is its own,
  and not RN-32's: RN-32's exception needs the wanted state to hold, and for a task in `done` the
  move to `cancelled` never holds. What covers it is that the page is not out of date, because it is
  built from the saved data when it loads (UX-I9). With the task in a final status (PRD § Core
  Features, Status workflow, "`done` and `cancelled` are final") nothing is left to do, so UX-I3's
  "where something is left for the operator to do" and UX-A3's "where a correction exists" ask for no
  action. No control was used, so "the control that was used" (UX-I3) and "the control it concerns"
  (UX-A3) read as the task's status for this case. The refusal was confirmed with three additions
  (`products/tracker17/docs/trail/uxd/cycle-5.md` § 2.1): the reason above, both addresses reaching
  it on a project's Tasks view and on the task's page, and its place beside the task's status. How
  the line is worded is `products/tracker17/docs/CONTENT.md`'s. *(re: UX-F4, UX-I3, UX-A3, UX-S4,
  UX-S6; PRD source: § UX Notes, Refusals say why; § Core Features, Status workflow)*
- **RN-34:** *(added)* No refusal offers a reload on a page built after it. A status move another tab
  overtook names the moves the page now shows, or none for a final status. An assignee who left the
  list before an add or an edit is refused with a reason that names picking another assignee or
  none. UX-I3's out-of-date refusal names what is left to do on the page it lands on, and offers a
  reload only where the page that shows it is itself still out of date. *Because* each of these refusals lands on a page built when it loads (UX-I9), not on the page
  the operator pressed from. A refused move lands on the list or the task's page it was pressed on,
  which shows the task's current status and the moves that status allows. A refused add lands on the
  project's Tasks view, whose assignee control offers only the names now on the list. A refused edit
  lands on the task's page, which offers the names now on the list and shows the refused name only as
  the choice that failed. By RN-32's own reason, "A reload offers something only on a page that is
  still out of date", a reload there shows nothing new. A reload that goes to the page's plain
  address would also drop what the operator typed, against UX-I3's "Everything the operator typed
  stays in the form". The rule is written as a condition on the page that shows the refusal, rather
  than as a list of cases, so it holds whatever page a refusal is answered with. RN-17's reason for
  the out-of-date refusal still holds: an address can outlive what it names. What the refusal says
  is RN-35's. The draft was confirmed with two additions (`products/tracker17/docs/trail/uxd/cycle-6.md`
  § 2.2): the assignee refusals go the same way as the overtaken move, and UX-I3's reload sentence
  becomes the condition above. The same answer records that the product's two assignee refusal lines
  still offer a reload, and that meeting UX-F3 and UX-F9 is a change to those strings, not to this
  document. How each line is worded is `products/tracker17/docs/CONTENT.md`'s. *(re: UX-F3, UX-F4,
  UX-F9, UX-I3, RN-32; PRD source: § UX Notes, Refusals say why)*
- **RN-35:** *(added)* A refusal states what holds when its page is built and claims no event before
  it. A status move another tab overtook states the task's current status and the moves that status
  allows, or that there are none when the status is final. The assignee refusals in UX-F3 and UX-F9
  say the name is not on the list. UX-I3's out-of-date refusal names what is left to do and does not
  say the page was out of date. *Because* every refusal in this tracker is read from its page's
  address, so a reload, Back, a bookmark or a typed address shows it again with no press, and the
  tracker cannot tell the first landing from a later visit. A line saying the status "has changed",
  that a name "has left the list" or that the page was out of date claims a past event the address
  cannot show, and on a later visit, or on an address typed for a task that was never moved, it is
  false. The verbal standard's rule is "State only what the tracker established"
  (`products/tracker17/docs/CONTENT.md` § Voice). The task's status, the moves it allows and the
  names on the list are read when the page is built, so a line stating them is true on the press and
  on every later visit. The draft, which changed UX-F4 only, was confirmed with two additions
  (`products/tracker17/docs/trail/uxd/cycle-7.md` § 2.1): UX-I3 states the rule once and drops its
  "says so", and the assignee refusals go the same way. The cost is accepted: the move line no
  longer says the press failed because the page was out of date. It still shows as a refusal beside
  the task's status, and the status it names is not the one the operator pressed from. RN-17's
  reason for the out-of-date refusal stands: an address can outlive what it names. How each line is
  worded is `products/tracker17/docs/CONTENT.md`'s. *(re: UX-F3, UX-F4, UX-F9, UX-I3, RN-34; PRD
  source: § UX Notes, Refusals say why)*

---

## Open Questions

- [OPEN: How a due date and a comment's written time are written out on screen, for example
  `2026-10-06` or `6 Oct 2026`. PRD § UX Notes, Defaults fixes them as calendar dates in the
  machine's local day, and the written form is a verbal standard. `CONTENT.md` settles it.]
- [OPEN: How a long title, label, name or comment wraps or shortens in a list row. Every field has a
  maximum length (`products/tracker17/docs/SRS.md` FR-40), and every maximum is still wider than any
  column, so the design language settles the display, and `DESIGN.md` carries it.]
  *(confirmed with an addition: `trail/uxd/cycle-3.md` § 2.1; why, RN-29)*
