# UXD open issues — tracker17

> Companion to `UXD.md`. The CDO authored the UXD non-interactively; this file holds
> what it could not settle from the inputs (the PRD, the project's Agari and its doctrine, the
> SRS when present, and any context the owner handed over) — and, when a design run has produced
> output for this product, the pointer to it. **Answer inline** — fill each **Answer** / **Confirm-or-override**
> slot — **commit this file**, then re-run `product-uxd`. It folds your answers into the UXD
> and drops the resolved items. When nothing is left open, `product-uxd` **deletes this file**:
> no file = the UXD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/uxd/` — so what you decided, and why, stays readable and citable
> for good.
>
> **A third source of items, and it is not the CDO.** § 3 holds what a seat downstream of the UXD
> found missing while working from documents the UXD fed. It is answered here and folded by the same
> run, but it was never this run's question.

---

## 1. Open issues — experience questions with no answer yet

### 1.1 Can a project's description be changed after the project is created?
- **Why it matters:** `products/tracker17/docs/PRD.md` § Core Features, Projects says a project has
  "an optional description" and that projects "can be created, listed, renamed and deleted". It
  names renaming and says nothing about the description. So today the description is set once, at
  creation, and can never be corrected. Whether it should be editable is a product call, the CPO's
  and yours, not a design one. The UXD follows the PRD's list as written meanwhile: UX-F10 and
  UX-S4 offer Rename and Delete only, and `UXD.md` § 10 records the gap.
  - **If yes:** UX-F10 gains "edit description" beside Rename, in the same form, and the PRD gains
    the operation (a `product-prd` round). The § 10 line goes.
  - **If no:** nothing in the UXD moves except the § 10 line, which becomes a plain statement that
    the description is fixed at creation.
- **Answer:** No. A project's description is set once, at creation, and Rename and Delete stay the only changes to a project. The PRD's list of project operations is tracker16-X's own list, word for word, and tracker16-X has no way to change a description either. Two changes in the UXD: (1) the § 10 line becomes a plain statement that the description is fixed at creation; (2) the create-project form (UX-F2, UX-S3) says beside the description field that it can't be changed later, the way UX-F8 already explains the Your name field beside it. The known cost: a mistyped description can only be fixed by deleting the project and creating it again, which deletes its tasks. The note beside the field is what makes that clear before the project exists. Reasoning in `docs/trail/uxd/self_answer-1.md`.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 The design-system direction: plain HTML, the browser's own controls, one hand-written stylesheet
- **Drafted into the UXD:** § 9 Direction: "plain semantic HTML with the browser's own form
  controls, styled by one small stylesheet the product writes itself — built from primitives, with
  no component library or design-system package". § 1 Design Read leans on it. § 9 also fixes one
  colour mode with no switch, and leaves which mode to `DESIGN.md`.
- **Rationale:** The reader comes to read the whole product (`PRD.md` § Goals, "It is simple"), and
  the PRD's first risk is that "a web interface adds parts that a command-line tool never needed"
  (`PRD.md` § Risks). A design-system package is one more dependency and a body of styling the reader
  would have to read or take on trust. Native controls bring keyboard use (UX-A1) for free. One
  colour mode halves the styling to read. This is still a taste call, because it sets how the
  product looks, so it is yours.
- **If overridden:** with a named system, for example a small classless stylesheet or a component
  library, § 9 names its official package and the "nothing from outside the machine" constraint
  then requires the package to ship in the copy. § 1's lean changes to that system. UX-I8 and UX-A5
  stay, and the system must meet them. With two colour modes, § 9's mode line changes and
  `DESIGN.md` carries both.
- **Confirm or override:** confirm, with one addition. The browser's own controls and pop-ups, including the date picker, select lists and scrollbars, render in the same single colour mode as the product's stylesheet. Otherwise a native control shows up in the other mode beside the product's styling. `DESIGN.md` states this alongside the mode it picks. Reasoning in `docs/trail/uxd/self_answer-1.md`.

### 2.2 How packed the task rows are, and how much character the type carries: density 6, typography 2
- **Drafted into the UXD:** § 2 Design Dials: DENSITY 6, a table with breathing room. TYPOGRAPHY 2,
  conventional type with no personality of its own.
- **Rationale:** That a list is a table, one row per task with every attribute in a column, follows
  from the PRD: each task carries six attributes the operator sorts and filters by (`PRD.md` § Core
  Features; § Key Use Cases 4). How tightly the rows pack does not follow, so 6 is drafted. The
  typography lean follows the same ground as VARIANCE 2, "an app that people recognise as an app"
  (`PRD.md` § Why This), and the instance fences no typography
  (`system/experience/visual_restrictions.md` § 3), but the exact lean is still taste.
- **If overridden:** a different DENSITY changes § 2 and the "dense enough to show a task row's
  every attribute on one line" constraint in § 9. Below about 4, rows would wrap and that constraint
  would be dropped. A different TYPOGRAPHY changes only § 2's row. Faces and hierarchy are
  `DESIGN.md`'s either way.
- **Confirm or override:** confirm, with one addition. § 9's "every attribute on one line" means one row per task, with each attribute in its own column. A title, or a set of labels, longer than its column wraps inside its cell and does not push any attribute onto a second row. A task can carry any number of labels, so a single line of text cannot hold every case. How a cell wraps or shortens stays with `DESIGN.md`, as the UXD's open question on long text already says. Reasoning in `docs/trail/uxd/self_answer-1.md`.

### 2.3 The accessibility bar: WCAG 2.1 Level AA in full, above the PRD's keyboard requirement
- **Drafted into the UXD:** UX-A4, status, priority and overdue never shown by colour alone, and
  UX-A5, WCAG 2.1 AA in full, including contrast, labels, page titles, English as the page language,
  and announced confirmations. UX-A1 to UX-A3 stand without this choice: keyboard use is the PRD's
  own (`PRD.md` § UX Notes, Defaults), and focus visible and refusals identified in text follow from
  it and from "Refusals say why".
- **Rationale:** The PRD names keyboard use and no other accessibility need, and no user with an
  assistive-technology need (`PRD.md` § Target Users). The instance deliberately fences no floor and
  leaves the bar to each product's UXD (`system/experience/visual_restrictions.md` § 3, "An
  accessibility floor: n/a"). AA is the level most products are held to, and native controls (choice
  2.1) meet much of it with no extra code, so it costs little here. It is above the floor the PRD
  sets, which makes it yours.
- **If overridden:** with no level adopted, UX-A4 and UX-A5 are dropped, § 8 keeps UX-A1 to UX-A3,
  and § 9's contrast constraint goes. Overdue could then be shown by colour alone. With a higher
  level, for example AAA contrast, UX-A5 names it and § 9's contrast constraint follows.
- **Confirm or override:** override: WCAG 2.2 Level AA in full, instead of WCAG 2.1 AA. WCAG 2.2 is the current W3C Recommendation and keeps every 2.1 criterion except 4.1.1 Parsing, which it removed. So every criterion the draft named still applies. UX-A1 to UX-A5 cite WCAG 2.2, and UX-A4 and UX-A5 otherwise stand as drafted. The UXD then states two consequences. (1) § 8's "Touch-target size: n/a" line is replaced. SC 2.5.8 Target Size (Minimum) applies to any pointer, a mouse included, so every control meets its 24 by 24 CSS pixel floor or one of its exceptions. This matters most for the move buttons that sit side by side on every row, where a slip onto `done` cannot be undone (choice 2.4). (2) AA includes SC 1.4.10 Reflow. At 400% zoom of a 1280-pixel-wide window, every page reads without scrolling in two directions. The task tables are exempt, because the criterion exempts data tables. This is not a phone layout, and § 9's desktop line stands alongside it. Reasoning in `docs/trail/uxd/self_answer-1.md`.

### 2.4 Which actions ask for a confirming press: deleting a project or task, and moving a task to `cancelled`; nothing is undoable
- **Drafted into the UXD:** UX-I2: deleting a project, deleting a task and moving a task to
  `cancelled` each take a second press, shown in place with the consequence stated. A move to
  `done` and every other action take effect at once. No action can be undone.
- **Rationale:** Deletion cascades (`PRD.md` § Core Features, Projects, "Deleting a project deletes
  all of its tasks") and both final statuses cannot be left (`PRD.md` § Core Features, Status
  workflow, "`done` and `cancelled` are final"), so a slip on any of them is permanent. Moving to the
  next status must feel effortless (`PRD.md` § UX Notes), and `done` is the next status of every task
  in progress, so it is drafted without a confirmation. `cancelled` is the side exit, used less, and
  as final, so it is drafted with one. A confirmation rather than an undo keeps the saved data free
  of a "deleted but recoverable" state the reader would also have to read.
- **If overridden:**
  - **Confirm `done` too:** UX-I2 and UX-F4 change, and every forward move to `done` takes two
    presses.
  - **Confirm nothing:** UX-I2 becomes "every action takes effect at once", and UX-F4, UX-F9 and
    UX-F10 lose their confirmation steps.
  - **Undo instead of confirming:** UX-I2 is rewritten around an undo window, every confirmation
    step in UX-F4, UX-F9 and UX-F10 goes, and the SDD has to hold a deleted-but-restorable state.
    The PRD would also need to say a final status can be left within the window.
- **Confirm or override:** confirm, with two additions. (1) The confirming step also offers a control that backs out and changes nothing. Keyboard focus lands on the confirming step when it appears, so a keyboard user is not sent back to the top of the page when the first button gives way. The back-out control's word must not read as the status `cancelled`; the word itself is `CONTENT.md`'s. (2) Under the AA bar (choice 2.3), SC 3.3.4 requires every deletion to stay confirmed or undoable. So the "confirm nothing" alternative is closed while that bar holds. A move to `done` is a status change, not a deletion, and stays one press. Reasoning in `docs/trail/uxd/self_answer-1.md`.

### 2.5 A task list's default order: by due date, earliest first
- **Drafted into the UXD:** UX-F5 Defaults: with no sort chosen, a list is sorted by due date
  ascending. The earliest due comes first, so every overdue task is at the top, and tasks with no
  due date come last.
- **Rationale:** The PRD says ascending is the default direction and names no default field
  (`PRD.md` § Core Features, Sorting), and the SRS names none either. Two of the three things that
  must feel effortless are "seeing which tasks are overdue" and "narrowing a list to what matters
  right now" (`PRD.md` § UX Notes), and due-date order puts both at the top of every list the moment
  it opens. The other strong candidate is creation order, oldest first, which is stable and
  predictable but puts the newest work at the bottom.
- **If overridden:** only UX-F5's Defaults line changes, and with it what Clear returns a list to.
- **Confirm or override:** confirm, with the reason corrected. Due date, earliest first, stays the default. It does not put every overdue task at the top: with no default filter, a `done` or `cancelled` task with an earlier due date sits above them. What it does guarantee is that every overdue task comes before every task that is not yet due. The overdue filter and the "Overdue" marker are what show overdue work in one action. UX-F5's "and therefore every overdue task, comes first" is corrected to say that. A list where no task has a due date shows in creation order, oldest first (SRS FR-36's tie rule). Reasoning in `docs/trail/uxd/self_answer-1.md`.

### 2.6 Adding a task: labels are added on the task's own page, which the operator lands on after Add
- **Drafted into the UXD:** UX-F3: the add-task form takes title, priority, assignee and due date.
  After Add, the operator lands on the new task's page, where labels are added one at a time.
- **Rationale:** Labels are free text, added and removed "one at a time" (`PRD.md` § Core Features,
  Labels). Putting several labels into the add-task form would need either a rule for separating
  them in one text field, which a free-text label could break, or a second control that adds labels
  one at a time before the task exists. Both are a second way to do one thing. Landing on the new
  task keeps one way to add a label, and Key Use Case 3 still runs end to end. The cost is that
  adding several tasks in a row means returning to the project each time.
- **If overridden:**
  - **Stay on the project after Add:** UX-F3 ends on the project's Tasks view, with the new task in
    the list and UX-I4's confirmation linking to it, and labels still go on from the task's page.
  - **Labels in the add-task form:** UX-F3 and UX-S4 gain a labels control, and the UXD has to
    state how several labels are entered.
- **Confirm or override:** confirm, with the reason corrected. Having one way to add a label is a reason to keep labels out of the add-task form. It is equally true of staying on the project after Add, so it does not choose between the two. What decides it is that the new task's page shows the task whole, as saved, whatever filter and sort the list has. A new task starts in `todo` with no labels, so under a status, label or assignee filter it often would not appear in the list the operator stayed on, and in a long sorted list it could land out of view. The task's page is also where Key Use Case 3's labels go on next. Reasoning in `docs/trail/uxd/self_answer-1.md`.

## 3. Raised from downstream — an item from a seat that did not write the UXD

None.
