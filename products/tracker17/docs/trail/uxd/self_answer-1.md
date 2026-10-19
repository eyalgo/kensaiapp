# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:**
  - `task-tracker-X/docs/fdr.md` § 1 Projects: "A project has a name
    and an optional description. Projects are created, listed, renamed, and deleted." The project
    commands in `tasktracker16x/cli/app.py` are `create` (with `--description`), `list`, `rename` and
    `delete`. `tasktracker16x/application/project_service.py` defines `create_project`,
    `rename_project`, `delete_project` and `list_projects`, and nothing that changes a description
    (item 1.1).
  - W3C, *Understanding SC 3.3.4 Error Prevention (Legal, Financial, Data)*,
    https://www.w3.org/WAI/WCAG21/Understanding/error-prevention-legal-financial-data.html. Level AA.
    The criterion covers pages "that modify or delete user-controllable data in data storage systems".
    Its intent is "to prevent mass loss of data such as deleting a file or record", and "It is not the
    intent to require a confirmation for each save command or the simple creation or editing of
    documents, records or other data" (items 2.3, 2.4).
  - W3C, *Understanding SC 1.4.10 Reflow*, https://www.w3.org/WAI/WCAG21/Understanding/reflow.html.
    Level AA. No scrolling in two dimensions "at a width equivalent to 320 CSS pixels", which is "a
    starting viewport width of 1280 CSS pixels wide at 400% zoom". The criterion lists "data tables (not
    individual cells)" among the content it exempts (item 2.3).
  - W3C, *What's New in WCAG 2.2*, https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/. WCAG
    2.2 "was published as a 'W3C Recommendation' web standard on 5 October 2023". It adds nine
    criteria, including 2.5.8 Target Size (Minimum) at AA, and removes 4.1.1 Parsing. The criteria
    carried over from 2.0 and 2.1 "are essentially the same in 2.2" (item 2.3).

## Items worked

### 1.1 — Can a project's description be changed after the project is created?

- **Bucket:** 1. Open issues — experience questions with no answer yet
- **Verdict:** answered
- **Why:** No. The description is set once, when the project is created. The PRD lists the project
  operations as created, listed, renamed and deleted (`PRD.md` § Core Features, Projects). That is
  tracker16-X's list word for word (`task-tracker-X/docs/fdr.md` § 1 Projects), and the PRD takes its
  rules from tracker16-X "wherever both cover a rule" (`PRD.md` § Core Features, preamble).
  tracker16-X's code has no way to change a description either (`project_service.py`; the `project`
  commands in `cli/app.py`). The SRS matches (`SRS.md` FR-10 to FR-13). So "no" keeps all three
  documents in agreement and changes only the UXD. That makes the item mine to answer. "Yes" would
  have been a new operation in the PRD, the CPO's to add, and a new feature built from scratch, where
  `PRD.md` § Risks already says tracker17 is most likely to drift.
  Check 4. **Refused**: an operator who mistypes a description can fix it only by deleting the project
  and creating it again, and deleting it deletes its tasks (`PRD.md` § Core Features, Projects). So the
  answer adds a note beside the description field on the create form, saying it can't be changed
  later. That puts the cost in front of the operator before the project exists. It is the same move
  UX-F8 makes for the Your name field ("The Your name section says so beside the field"). **Empty**:
  the description is optional, so a project with none is unaffected.
  What would have tipped me to "yes": if the owner, using the tracker, finds an uncorrectable
  description is a defect. That is then a one-line item on the PRD's companion, for `product-prd`, and
  UX-F10 gains the field beside Rename.

### 2.1 — The design-system direction: plain HTML, the browser's own controls, one hand-written stylesheet

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The direction holds, and it is grounded in the PRD as much as in taste. The reader reads the
  whole product (`PRD.md` § Goals, "It is simple"). A design-system package is more code they have to
  read or take on trust, and the PRD's first risk is exactly that a web interface "adds parts"
  (`PRD.md` § Risks). Native controls give the keyboard model UX-I6 relies on. One colour mode with no
  switch is less styling to read.
  Check 1: the aesthetic call on direction belongs to the UXD
  (`<CORE>/doctrine/governance/where_taste_appears.md` § The rule), and this run sits in the owner's
  seat for this companion. I looked for a sign that the owner had kept this call for themselves. The
  only owner-held visual step I found is the later Claude Design run, which *reads* the experience
  documents and comes after this one. It does not reserve the UXD's direction. So I answered rather
  than left it.
  Check 2: one part of the draft does not hold, but it sits in the override branch, which was not
  taken. The branch says a package would have to "ship in the copy" under the nothing-from-outside
  constraint. In fact the SRS lets setup fetch declared dependencies (`SRS.md` § 5.3), and the
  constraint is about what the pages load at run time. The reason to avoid a package is reading cost,
  not that a package is forbidden.
  Check 4, **absent**: with one colour mode chosen in the stylesheet, the browser's own controls can
  still draw in another. Pop-ups such as the date picker and select lists can't be styled by a
  stylesheet at all, so they follow whatever mode the browser is told the page uses. If `DESIGN.md`
  picks a dark mode and the browser isn't told, those controls show light beside dark styling. That is
  the half-styled control `system/experience/visual_restrictions.md` § 2 `no-placeholder-delivery`
  forbids, and it can fail contrast. So the addition requires native controls and pop-ups to render
  in the same mode. I state this as a requirement and leave how it is met to `DESIGN.md` and the code.

### 2.2 — How packed the task rows are, and how much character the type carries: density 6, typography 2

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Both values stand. A table with breathing room fits six compared attributes (`PRD.md`
  § Core Features; § Key Use Cases 4) without the packed look that would work against a quiet,
  conventional product (§ 1 Design Read). Conventional type follows from "an app that people recognise
  as an app" (`PRD.md` § Why This). The instance fences no typography
  (`system/experience/visual_restrictions.md` § 3), so the product decides, and the UXD is where it
  decides. Seat as for 2.1.
  Check 4, **unbounded content**: § 9 then asks for density enough "to show a task row's every
  attribute on one line". A task carries "any number of labels" (`PRD.md` § Core Features, Tasks), and
  titles have no maximum length (`UXD.md` Open Questions, citing `SRS.md` § Open Questions). So no
  single line of text can hold every row, and the constraint as written cannot be met. The addition
  reads it as one row, with each attribute in its own column, and long text wrapping inside its cell.
  This keeps it consistent with the UXD's own open question, which already gives the wrap to
  `DESIGN.md`.
  Check 3 against 2.3: a 24-pixel target floor fits comfortably in a density-6 row, and the task
  table is exempt from Reflow, so the density holds at desktop width under the AA bar.

### 2.3 — The accessibility bar: WCAG 2.1 Level AA in full, above the PRD's keyboard requirement

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** overridden
- **Why:** The draft was WCAG 2.1 Level AA. It is replaced by WCAG 2.2 Level AA. The level stands on
  the draft's own reasons: AA is the usual bar, native controls (2.1) meet much of it for free, and
  the instance leaves the bar to each product's UXD (`system/experience/visual_restrictions.md` § 3,
  "An accessibility floor: n/a"). That last point also makes the call this document's, so it is mine
  to answer.
  Check 2: the draft argued for the level and never for the version. That answers a smaller question
  than the item asks. WCAG 2.2 has been the W3C Recommendation since 5 October 2023 and keeps every 2.1
  criterion except 4.1.1 Parsing (W3C, *What's New in WCAG 2.2*). So 2.2 AA asks for everything the
  draft named. Of its new A and AA criteria, only one changes this product. 2.5.7 Dragging Movements
  and 3.3.8 Accessible Authentication have nothing to apply to: no dragging, no login. Redundant
  Entry is already met, because UX-I3 keeps what was typed. The one that changes the product is
  **2.5.8 Target Size (Minimum)**, and it has a reason here beyond being current. Under 2.4 a move to
  `done` takes one press and can never be undone (`PRD.md` § Core Features, Status workflow, "`done`
  and `cancelled` are final"). An `in-progress` row shows its three move buttons side by side. A
  pointer-target floor is what guards that permanent one-press action against a slip. Since 2.5.8
  covers any pointer, a mouse included, § 8's "Touch-target size: n/a" line no longer holds.
  Check 4, **zoom** (`SC 1.4.10 Reflow`, AA under both versions, unstated in the draft): at 400% zoom
  of a 1280-pixel window, the non-table parts of every page must read without scrolling in two
  directions. These are the header, the forms, the filter controls, the summary and People. The task
  tables are exempt as data tables (W3C, *Understanding SC 1.4.10*). This does not commit the product
  to a phone layout, so § 9's desktop line and `PRD.md` § UX Notes, Defaults still hold. But the
  design language can't assume a wide window outside the tables.
  Check 3: SC 3.3.4, at AA, covers pages that delete stored data, and its intent is "to prevent mass
  loss of data such as deleting a file or record". It excludes "the simple creation or editing of
  documents, records or other data" (W3C, *Understanding SC 3.3.4*). Choice 2.4's confirmations on
  deletion meet it. Its one-press `done` and its comments, which can never be edited, are editing and
  creation, so they are not caught. Decided together with 2.4.
  I was close to a plain *confirmed with addition* on 2.1. What tipped it was the permanent one-press
  `done` beside its neighbours.

### 2.4 — Which actions ask for a confirming press: deleting a project or task, and moving a task to `cancelled`; nothing is undoable

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The split holds for the reasons the draft gives. Deleting a project takes its tasks with it,
  and both final statuses are permanent (`PRD.md` § Core Features, Projects; Status workflow). Moving
  to the next status must feel effortless (`PRD.md` § UX Notes), and `done` is the next status of
  every task in progress. Confirming instead of offering undo keeps the saved data free of a
  deleted-but-restorable state. An undo for a final status would also contradict the PRD's "final".
  Check 4, **refused**: the draft says what the second press does, but not how the operator says no.
  A confirmation with no way back out leaves a pending destructive step on the page. So the addition
  is a back-out control that changes nothing. Its word must not read as the status `cancelled`.
  "Cancel" beside a move to `cancelled` reads both ways, and the word is the Content Manager's to set
  in `CONTENT.md`. **Keyboard**: the confirmation appears in place of the pressed button (UX-I2). If
  focus stays on a button that is removed, a keyboard user is sent back to the start of the page, and
  that breaks UX-A1's every-action-by-keyboard. So focus lands on the confirming step.
  **Concurrent**: a confirming press after another tab has deleted or moved the item is already
  covered, by UX-I3's out-of-date refusal and UX-S10.
  Check 3, decided together with 2.3: under the AA bar, SC 3.3.4 requires deleting a record to be
  confirmed, checked or reversible. So the companion's "confirm nothing" alternative is closed for
  deletions while that bar stands. Status moves and edits are outside that criterion's intent, so
  `done` stays one press.

### 2.5 — A task list's default order: by due date, earliest first

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The conclusion is right and part of the argument is not. Due date, earliest first, is the
  best default among the four sort fields the PRD allows (`PRD.md` § Core Features, Sorting).
  Creation order and title order put nothing urgent first, and priority order ascending puts `low`
  first (`SRS.md` FR-36). But the draft says it puts "every overdue task at the top". With no default
  filter, `done` and `cancelled` tasks show (`UXD.md` RN-12), and an old finished task with an earlier
  due date sorts above every overdue one. The claim fails more as finished work builds up. What the
  order does guarantee is weaker and still useful: every overdue task comes before every task not yet
  due. Overdue tasks are due before today, and the rest are due today or later, or have no date and
  sort last (`SRS.md` FR-36). The overdue filter and the "Overdue" marker are what show overdue work in
  one action (UX-F5). So the UXD's sentence in UX-F5 is corrected rather than the default changed.
  Check 4, **empty**: a list where no task has a due date falls back to the tie rule, which is
  creation order, oldest first (`SRS.md` FR-36). The UXD should say so, because it is what most first
  lists will show.

### 2.6 — Adding a task: labels are added on the task's own page, which the operator lands on after Add

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Landing on the new task's page stands, but not for the reason given. "One way to add a
  label" rules out labels in the add-task form, and I agree with that part (`PRD.md` § Core Features,
  Labels, "one at a time"). But it is just as true of the companion's first alternative, staying on
  the project. So it does not choose between landing and staying. What chooses is check 4,
  **filtered**: the add-task form sits on a list that may be filtered and sorted (UX-I7). A new task
  starts in `todo` with no labels (`PRD.md` § Core Features, Status workflow; Labels). So under a
  status filter other than `todo`, any label filter, or an assignee filter it doesn't match, it would
  not appear in the list the operator stayed on. In a long list sorted by due date it can land out of
  view. The task's page shows it whole as saved (UX-I4), whatever the list's filters. Key Use Case 3's
  labels then go on right there.
  The cost the draft names stays true, and I accept it: adding several tasks in a row means going
  back to the project each time.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
