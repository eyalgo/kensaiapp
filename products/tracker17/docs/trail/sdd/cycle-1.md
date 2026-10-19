# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

Every `SDD §` reference below is to `products/tracker17/docs/SDD.md`, version 1. `PRD`, `SRS` and
`UXD` are `products/tracker17/docs/PRD.md`, `products/tracker17/docs/SRS.md` and
`products/tracker17/docs/UXD.md`.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 The tracker runs on Python 3.11 or later and uses only the Python standard library when it runs
- **Raised by:** CTO
- **Seat:** cto
- **Drafted into the SDD:** SDD § 4 RT-1 and RT-2, and § 9 TO-1. The tracker needs Python 3.11 or
  later and nothing else to run. It uses no web framework and no template engine. Setup is two
  commands: move into the copy, then `python3 main.py`. Only the test suite has dependencies, each
  fixed to an exact version (SDD § 4 RT-4), and they include the browser the end-to-end tests drive.
- **Rationale:** SRS § Open Questions says "The prerequisites FR-4 names follow from the SDD's choice
  of runtime". The predecessor, whose code SRS C-5 prefers as the starting point, is Python 3.11 or
  later with no run-time dependency
  (`task-tracker-X/pyproject.toml`, `requires-python = ">=3.11"`).
  A framework would shorten the page-building code. It would also add packages the reader has to
  read or take on trust, and an install step that uses up SRS C-7's three commands. The UXD already
  rejected a design-system package on the same ground (UXD § 9, "a dependency and a body of styling
  code they would also have to read or take on trust").
- **If overridden:** the override names a framework. SDD § 4 RT-1 and RT-4, § 9 TO-1 and § 11 R-3
  and R-4 are rewritten. The setup instructions gain an install step, and the stated prerequisites
  gain whatever installs it. SDD § 3's `web` part keeps its seams and loses its own page-building
  and listening code. Under the draft, SRS FR-4's line that setup needs a network connection once
  applies only to setting up the test suite. Under an override it applies to running the tracker
  too. No slice in SDD § 6 changes its slug or its place.
- **Confirm or override:** confirm, with four additions. Python 3.11 or later, the standard library alone at run time, and `python3 main.py` as the start command all stand. (1) The tracker needs no network connection at any point, setup included. The one-time network connection that SRS FR-4 and UXD UX-S1 list among the prerequisites is needed only to set up the test suite, to fetch the test dependencies and the browser the end-to-end tests drive. SDD § 4 says so, and RT-4's "so running the suite adds no prerequisite" is replaced by that statement. (2) The test dependencies are installed into a virtual environment made with Python's own `venv` module, and RT-4 says so. On the owner's machine `pip` refuses to install outside one. (3) A `python3` older than 3.11 is a missing prerequisite. UXD UX-F1 gives that failure to the setup instructions, so their prerequisites section names the command that shows the version and says what to do when it is lower, and `pyproject.toml` declares the same floor. SDD § 4 OB-2 is scoped to a start the tracker itself refuses, because it cannot hold under a Python too old to run the tracker. (4) SDD § 11 gains a risk: the floor is declared and nothing checks it. The suite runs only on the Python the machine has, which is 3.14.7 on the owner's machine today. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-1.md`.

### 2.2 The tracker is supported on macOS and Linux, and not on Windows
- **Raised by:** CTO
- **Seat:** cpo
- **Drafted into the SDD:** SDD § 4 RT-3. The setup instructions' prerequisites name macOS and
  Linux.
- **Rationale:** neither the PRD nor the SRS names an operating system. PRD § Target Users says the
  operator runs it "on their own machine", and the Agari is checked on the owner's machine. The
  machine this run executed on reports its platform as `darwin`, which is macOS. The technical
  reason to ask is SRS NFR-3: letting only one running tracker use a
  saved-data location, and letting the next start succeed after a crash, uses an operating-system
  lock that is built one way on macOS and Linux and another way on Windows. Promising Windows would
  mean building and testing that second way on a machine the owner's check never touches.
- **If overridden:** an override that adds Windows changes SDD § 4 RT-3, adds a second locking path
  to the `persistence` part in SDD § 3, and adds to the *Reached when* of `protect-saved-data` in
  SDD § 6 a run of both suites on Windows. Nothing else moves.
- **Confirm or override:** confirm, with three additions. The tracker runs on macOS and Linux, and Windows is not supported. (1) Only macOS is checked. The owner's machine is macOS, and nothing in the Agari's check runs the tracker or its suite on Linux. Linux stays named because the tracker needs no code of its own for it. SDD § 11 gains a risk that says Linux is named and nothing checks it, beside the risk item 2.1's answer adds for the Python floor. (2) An unsupported operating system is a missing prerequisite. UXD UX-F1 gives that failure to the setup instructions, so their prerequisites section names macOS and Linux, says the tracker has been checked on macOS only, and says Windows is not supported. The tracker itself checks no operating system and carries no message for one. (3) Nothing is built or tested for Windows. An override that adds Windows later is the change this item's *If overridden* field describes. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-2.md`.

### 2.3 No page runs a script, so every action reloads a whole page
- **Raised by:** CTO
- **Seat:** cdo
- **Drafted into the SDD:** SDD § 4 EX-2 and the focus clause of EX-6, § 4 SEC-3, and § 9 TO-2.
  Every interaction is a link or a form submission answered by a whole page. Three things follow
  for the experience:
  - **UX-I2's confirmation is its own page load.** The first press opens the same page with the
    confirmation in the first button's place. The page carries the keyboard focus itself, on the
    sentence, when it opens. Backing out opens the page again with focus on the restored button.
  - **A completion line or a refusal arrives with the page that carries it.** UXD UX-A5 says these
    are "announced to assistive technology without moving focus". Under the draft they are marked
    as status messages in the page and are never given focus, and a screen reader meets them when
    it reads the page that has just loaded. Nothing announces them separately from that page.
  - **After an action other than UX-I2's, keyboard focus starts where it starts on any freshly
    opened page.** UXD UX-F4 says the operator "stays where they were". Under the draft that means
    the same page at the same address, with the same filter and sort.
- **Rationale:** UXD § 1 reads the product as "plain semantic HTML pages with the browser's own form
  controls and one small stylesheet", and weighs every decision against whether it adds "a part the
  reader has to read". UXD UX-I8 and UX-I9 already rule out partial pages and pages that update
  themselves. A script would be a second language in a product whose first bar is being simple to
  read.
- **If overridden:** an override that wants messages announced on arrival, or focus kept on the row
  that was acted on, needs a script. SDD § 3's `web` part then owns one script file, the units
  table gains a second language, SDD § 4 EX-2 and SEC-3 are rewritten, and § 9 TO-2 is replaced by
  the cost of the script. `status-moves` in SDD § 6 gains the script's behaviour in its *Reached
  when*. No seam and no order in SDD § 7 changes. An override that keeps the no-script page model
  and changes only where focus lands rewrites EX-6 alone.
- **Confirm or override:** override: keep the no-script page model, and replace two of its three consequences. SDD § 4 EX-2 and SEC-3 stand, and every action is still answered by a whole page. (1) UX-I2's confirmation is its own page load, as drafted. The page that shows it opens with the confirmation in view. A double press on the first button never confirms, on a short page and on a list scrolled part-way. A first press for an action the page would no longer offer shows no confirmation. It is refused under UX-I3, or it shows UX-S10 when its target is gone. (2) This replaces the draft's third consequence. The page that answers a form submission, when it is the page the form was on, opens at the place of the action and not at its top. After a completed action the place is the thing acted on. After a refusal or a failure the place is the control that was used, with the reason beside it. When the thing acted on is no longer on the page, the place is the top of the sheet it was on, where the completion line sits. The place is in view and keyboard focus is on it, so the next Tab goes on from there. That is how UX-F4's "stays where they were" and UX-I3's "beside the control that was used" hold on a page load. A page reached by a link, and a different page that an action lands on, open at their start. (3) This replaces "nothing announces them separately". No completion line and no refusal takes focus. The line is the accessible description of the element the page opens on, so assistive technology reads it when the page opens. That is how UX-A5's "announced to assistive technology without moving focus" holds on a page load. (4) SDD § 9 TO-2 records what is given up and accepted: no part of a page changes in place, and a page reopens with the place in view but not always at the same height in the window. Where a test shows that a page with no script cannot hold (1) to (3), those conditions stand and SDD § 11 R-2's fallback applies. R-2 and TO-2 are restated for every page an action opens. The first such page is a refused project name in `first-project`, and what that does to the order is the CTO's. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-3.md`.

### 2.4 What a person can watch at the end of each slice, as drafted from the UXD
- **Raised by:** CTO
- **Seat:** cdo
- **Drafted into the SDD:** the *Behaviour* lines of *Reached when* and the UXD entries of *Traces
  to* in all eight slices of SDD § 6. Each line was written from the UXD flow and screen it names.
  The draft also holds that each slice's *Delivers* is something a person can watch, and none is an
  architecture box. Two screens arrive in steps under this cut:
  - **People (UXD UX-S8)** shows only the assignee list after `tasks-in-a-project`, and gains Your
    name in `comment-on-a-task`.
  - **A project's page (UXD UX-S4)** shows the name, the description and the no-tasks line after
    `first-project`. It gains the add-task form and the list in `tasks-in-a-project`, the move
    buttons in `status-moves`, the filter and sort controls in `narrow-and-sort`, the Tasks and
    Summary links in `project-summary`, and Rename and Delete in `delete-and-rename`.

  The header shows only the areas that exist so far (SDD § 4 EX-12): Projects after `first-project`,
  People after `tasks-in-a-project`, All tasks after `narrow-and-sort`.
- **Rationale:** the UXD describes each screen finished. It does not say what a screen may look like
  part-way through the build, and `system/experience/visual_restrictions.md` § 2,
  `no-placeholder-delivery`, which UXD UX-I8 cites, bears on a control shown before it works. The
  draft shows no control and no link ahead of the slice that makes it work.
- **If overridden:** an override that changes one slice's bar rewrites that slice's *Behaviour*
  lines. An override that says a screen must not arrive in steps moves work between slices: People
  whole in one slice is the alternative in § 3.2 below, and a project's page whole in one slice
  would merge `tasks-in-a-project`, `status-moves`, `narrow-and-sort`, `project-summary` and
  `delete-and-rename` into one slice too broad to pass SDD § 5 step 4.
- **Confirm or override:** confirm, with five additions. The behaviour lines and the UXD entries of *Traces to* stand as drafted, every *Delivers* is something a person can watch, and a screen may arrive in steps. (1) Four screens arrive in steps, not two. The task's page (UX-S6) and the not-found page (UX-S10) do so as well as People and a project's page. One rule covers all four and the header: until the slice that delivers a control or an area, no page shows it, links to it, or carries words that point to it. In `first-project` the project's page says it has no tasks yet and does not invite a first task, and the invitation arrives with the add-task form in `tasks-in-a-project`. The not-found page speaks of a task from `tasks-in-a-project` on, and links to All tasks from `narrow-and-sort` on. The same holds for the setup instructions, which describe the tracker as it stands after each slice. (2) SDD § 4 EX-12 excepts the page for saved data that cannot be read, which carries no header and no navigation (UX-S9, UXD § 4). (3) The lines carry what the answer to item 2.3 changes. In `first-project`, a refused name opens the page at the name field. In `comment-on-a-task`, the page opens with the new comment in view. In `status-moves`, a move leaves the operator at the moved task's row, or at the task's moves on the task's page. Its confirmation opens in view, a double press on the first button never confirms on a list scrolled part-way, backing out returns focus to the restored button, and a first press for a move the task no longer allows is refused with no confirmation. In `delete-and-rename`, both confirmations behave the same, and Delete project's holds below a list long enough to scroll. (4) Four lines gain a state the UXD requires at the slice that delivers it. `first-project`: the create form says beside the description field that the description cannot be changed later (UX-F2). `comment-on-a-task`: a blank name is refused (UX-F8). `narrow-and-sort`: the All tasks rows carry everything a project's rows carry, the moves included, and with no tasks anywhere the page says so and links to Projects (UX-S7). `protect-saved-data`: the page points to the setup instructions' section on setting saved data aside (UX-S9). (5) *Traces to* names every UXD screen a slice adds to and every UXD entry its line cites. `first-project` gains UX-S4. `tasks-in-a-project` gains UX-F5 and UX-S10. `status-moves` gains UX-S4 and UX-S6. `narrow-and-sort` gains UX-F4 and UX-S10. `project-summary` gains UX-S4. `delete-and-rename` gains UX-S4 and UX-S6. The patterns and accessibility entries that no slice names reach every slice through SDD § 4 and need no entry. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-3.md`.

### 2.5 The eight slices: what each delivers, and what each leaves to another
- **Raised by:** CTO
- **Seat:** cpo
- **Drafted into the SDD:** the *Slug*, *Delivers*, *Moves toward* and *Not in this slice* fields
  and the PRD entries of *Traces to* in SDD § 6, and the record of SDD § 5 steps 1, 2 and 4 in SDD
  Review Notes RN-13. The eight slices, in build order:
  1. `first-project` — setup instructions, a running tracker, a first project that survives a
     restart.
  2. `tasks-in-a-project` — the assignee list, adding tasks, the project's list with overdue
     marked, changing a task's fields and labels.
  3. `comment-on-a-task` — the operator's name, and comments.
  4. `status-moves` — moving a task through the workflow, and refusing a move it does not allow.
  5. `narrow-and-sort` — filtering and sorting, within a project and across all projects.
  6. `project-summary` — the summary, with counts that open the list they count.
  7. `delete-and-rename` — deleting a task, renaming a project, deleting a project with its tasks.
  8. `protect-saved-data` — the page for saved data that cannot be read, and refusing a second
     tracker.
- **Rationale:** the PRD lists Core Features and Key Use Cases and does not cut them into steps that
  each deliver something. The draft cuts along the Key Use Cases: slice 1 is Key Use Case 1, slices
  2 and 4 are Key Use Case 3, slices 5 and 6 are Key Use Case 4, and slice 3 is Key Use Case 5.
  Slices 7 and 8 hold what no Key Use Case names: deletion and renaming (PRD § Core Features,
  Projects and Tasks) and the failure states (PRD § UX Notes). The order is the CTO's and is not
  part of this item.
- **If overridden:** an override that merges, splits or renames a slice changes SDD § 6 and every
  row of SDD § 7 that names it. An override that changes only a *Delivers* sentence or a *Not in
  this slice* fence changes that field alone. Whether a slice is worth delivering is this seat's
  call, and an override that drops one says which slice takes over what it delivered.
- **Confirm or override:** confirm, with three additions. The eight slices, their slugs, their *Delivers* sentences and the fences they already carry stand as drafted. Items 3.1 and 3.2 are both answered keep, so the count stays eight. (1) The cut must name the Agari's third bar, Simple to read. As drafted, no slice's *Moves toward* names it and no slice's *Traces to* names PRD § Key Use Cases 2, though each slice that adds a feature entry point makes that feature traceable from the PRD to its code and tests. `first-project` *Moves toward* gains the first step of the third bar, for the Projects feature and for the first code a reader can read cold. `tasks-in-a-project`, `comment-on-a-task`, `status-moves`, `narrow-and-sort` and `project-summary` each gain the third bar for the Core Features whose entry point they add in SDD § 4 TS-3's table. `delete-and-rename` gains it for completing the Projects and Tasks traces. Those seven slices' *Traces to* gain PRD § Key Use Cases 2 and § Success Metrics Simple to read, and `first-project` also gains § Core Features Tested throughout. (2) *Traces to* gains the PRD sections the slices deliver and no slice names. § UX Notes Refusals say why goes on `first-project`, `tasks-in-a-project`, `comment-on-a-task`, `status-moves`, `narrow-and-sort` and `delete-and-rename`. § UX Notes Failure states, § Data & Privacy and § Out of Scope, hosting, go on `first-project`. § UX Notes What must feel effortless goes on `tasks-in-a-project`, for the overdue marking. § UX Notes Defaults goes on `tasks-in-a-project` and `comment-on-a-task`, for how dates and times show. (3) *Not in this slice* names the PRD's remaining exclusions on the slice a reader would expect each in, as out of scope with no slice owning it: threaded replies on `comment-on-a-task`, more than one value per filter field and sorting by more than one field on `narrow-and-sort`, and a package, an installer or a hosted demo on `first-project`. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-2.md`.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

### 3.1 `delete-and-rename` is its own slice, and not part of `tasks-in-a-project`
- **Raised by:** CTO
- **Seat:** cpo
- **The cut as drafted:** SDD § 6 S-7, `delete-and-rename`, delivers deleting a task, renaming a
  project and deleting a project with its tasks. `tasks-in-a-project` (S-2) creates and changes
  tasks and deletes nothing.
- **The alternative cut:** fold all three into `tasks-in-a-project`, which would then deliver
  everything about tasks and projects except status moves. There would be seven slices.
- **What changes if it moves:** `tasks-in-a-project` becomes the first slice to build UXD UX-I2's
  in-place confirmation, in place of `status-moves`. The second slice grows, and every later slice
  waits on a larger one. The `hands_off_to` row from `status-moves` to `delete-and-rename` in SDD
  § 7 reverses. Deletion becomes available in the second slice and not the seventh.
- **Why it is yours to call:** both cuts pass the four tests of SDD § 5. The draft keeps the second
  slice small and puts the riskier rules ahead of deletion. The alternative gives the operator a
  complete task and project editor sooner. Which matters more is the order you want value in.
- **Keep or re-cut:** keep. `delete-and-rename` stays its own slice. The Agari's Works bar has the owner run Key Use Cases 3, 4 and 5 in the browser, and none of the three deletes anything or renames a project, so nothing in that run-through waits on this slice. Folding it into `tasks-in-a-project` would put three more actions and the first in-place confirmation in front of every slice a Key Use Case needs. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-2.md`.

### 3.2 People arrives in two halves, and there is no slice for People alone
- **Raised by:** CTO
- **Seat:** cpo
- **The cut as drafted:** the assignee list arrives in `tasks-in-a-project`, because a list of names
  with no task to assign has no value alone. The operator's name arrives in `comment-on-a-task`,
  because the name is used only as a comment's author (SRS FR-28). SDD § 5 step 2 struck both as
  fragments (SDD Review Notes RN-13).
- **The alternative cut:** one `people` slice, built second, delivering the whole People screen:
  the assignee list and the operator's name together.
- **What changes if it moves:** `tasks-in-a-project` and `comment-on-a-task` each gain a
  `depends_on` row to `people` in SDD § 7 and lose their half of the screen. There would be nine
  slices. The People screen is never seen half-built. The `people` slice itself delivers names that
  nothing yet uses.
- **Why it is yours to call:** the draft follows SDD § 5 step 2 strictly, and the alternative fails
  that step as written. The alternative is still defensible if you count a finished screen as value
  on its own. That is a judgment about product value, which the SDD's lane table gives to the CPO.
- **Keep or re-cut:** keep. People arrives in two halves, and there is no `people` slice. A finished screen is not counted as value on its own here. A screen of names that nothing yet uses lets the operator do nothing they could not do before, so SDD § 5 step 2 strikes it as a fragment. Each half arrives in the slice that first uses it: the assignee list with the first task that can be assigned, and the operator's name with the first comment. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-2.md`.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

None.
