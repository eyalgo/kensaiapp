# SRS open issues — tracker17

> Companion to `SRS.md`. The CTO authored the SRS non-interactively; this file holds
> what it could not settle from the inputs (the PRD and any context/constraints).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this
> file**, then re-run `product-srs`. It folds your answers into the SRS and drops the
> resolved items. When nothing is left open, `product-srs` **deletes this file**: no file =
> the SRS is done.
>
> Your answers are never thrown away. Each time the CTO folds them in, it first copies this
> file whole to `docs/trail/srs/` — so what you decided, and why, stays readable and citable
> for good.
>
> **§§ 1–2 are the CTO's own questions; § 3 is somebody else's.** A seat reading the SRS long after
> it settled can find a gap the authoring run had no way to see, and § 3 is where it says so.

---

## 1. Open issues — technical questions with no answer yet

None. Every call the PRD leaves open has a drafted answer in § 2.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

### 2.1 Setup may download public dependencies, and the running tracker uses no network
- **Drafted into the SRS:** `products/tracker17/docs/SRS.md` § 5.3 says a fresh copy may fetch its
  declared dependencies during setup, from public sources that need no account, key or sign-up. NFR-5
  says the running tracker sends nothing off the machine.
- **Rationale:** The PRD says two things that pull apart here. § Dependencies / Integrations says
  nothing needs "a network connection beyond the machine itself". § Success Metrics, Simple to set up,
  bans only "an account, a key or a sign-up" during setup. On my reading, the network ban is about
  using the tracker, because § Goals says it "runs on the operator's machine and uses no outside
  service". tracker16-X, the preferred starting point, is a Python project with a `pyproject.toml`, and
  its FDR allows third-party libraries (`task-tracker-X/docs/fdr.md`
  § Product decisions, "Third-party libraries are allowed"). The end-to-end layer must drive a browser
  (NFR-11), and browser-driving test tools are normally fetched at setup. Banning every download would
  rule those tools out.
- **If overridden** (no network even at setup): § 5.3's setup line becomes "none". C-2 gains "and
  setup needs no network connection". The SDD then has to build with only what the stated
  prerequisites already contain. The end-to-end layer in NFR-11 and AC-2 would need a browser-driving
  tool that ships with those prerequisites, or the owner would have to accept one as a prerequisite,
  which puts weight on C-7's ten-minute bound. RN-12 would need re-reading against that.
- **Confirm or override:** confirm, with two additions. (1) FR-4's prerequisites say that setup needs a network connection once, to fetch the declared dependencies, so a setup run offline fails in a way the instructions already explain. (2) The declared dependencies are fixed to exact versions, so a fresh copy fetched later gets the same versions the suite last passed with. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.2 Pages show the state when they were loaded, and every action is checked against the saved data
- **Drafted into the SRS:** NFR-3. Pages do not update themselves. Every action is checked against
  the saved data when it is applied. An action that is no longer valid, such as moving a task that
  another tab already moved, is refused with the reason, and the operator reloads to see the current
  state. A list left open past midnight keeps showing yesterday's overdue marks until it is reloaded
  (FR-25). A second tracker started against the same saved data refuses to start.
- **Rationale:** One operator can still open the tracker in two browser tabs, or leave a list open
  overnight. The PRD's trail names both cases and leaves them to the SRS
  (`products/tracker17/docs/trail/prd/self_answer-1.md` § 2.8, "One operator may have the tracker open
  in two browser tabs, or leave a list open past midnight"). Pages that update themselves would come
  close to the "real-time collaboration" PRD § Out of Scope excludes, and would add parts a reader has
  to read. Checking each action against the saved data keeps the workflow rules true whatever a stale
  page shows. The one-tracker rule stops two running trackers overwriting each other's saves, which
  would break FR-5.
- **If overridden** (pages update themselves): NFR-3 changes to a live-update requirement with a
  stated delay. A new acceptance criterion would check a second tab updating. FR-25's "at the moment
  the system produces" would need a rule for re-marking overdue tasks at midnight. NFR-10's simplicity
  judgement takes on the cost.
  **If overridden** (last action wins, with no check): FR-39's last refusal and AC-12's stale-action
  case are removed, and a stale page could then make a workflow move FR-18 forbids.
- **Confirm or override:** confirm, with three additions. (1) A tracker stopped by a crash, a killed process or a power cut does not stop the next start: the one-tracker check refuses only while another tracker is actually running, and AC-16 also checks that a start after a killed tracker succeeds. (2) An action on a project or task that no longer exists, because another tab deleted it, is refused with the reason and changes nothing, and FR-39's last refusal covers it alongside a task that has changed. (3) A plain field edit made from a stale page replaces whatever the other tab saved for that field. That is stated rather than prevented, because both edits come from the one operator and no workflow rule is broken. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.3 Due-date range ends are included, and tasks with no due date fall outside any range
- **Drafted into the SRS:** FR-34. A task matches when its due date is on or after the from-date and
  on or before the to-date. A task with no due date matches no range that has at least one end set.
- **Rationale:** PRD § Core Features, Filtering says only "a due-date range with either end optional".
  tracker16-X's FDR says the same and does not say whether the ends are included (`fdr.md` § 9,
  "two independent optional bounds"). PRD § Risks notes its code has no filtering, so no tested
  behaviour exists to copy. Including both ends is how a person reads "from the 1st to the 5th". A
  task with no due date has no date to place inside a range. Which tasks a filter shows is something
  you see, so the call is yours.
- **If overridden:** FR-34's wording changes. AC-14's range cases change with it. Nothing else depends
  on the ends.
- **Confirm or override:** confirm, with one addition. A range whose from-date is later than its to-date is refused with the reason, which says the dates are the wrong way round, instead of showing "nothing matched". FR-34 states it and AC-14's range cases include it. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.4 How sorting orders priority, missing due dates, titles and ties
- **Drafted into the SRS:** FR-36.
  - Priority ascending runs `low`, `medium`, `high`.
  - Tasks with no due date come last whichever direction is chosen.
  - Titles sort alphabetically, ignoring letter case.
  - Tasks equal on the chosen field keep the order they were created in.
- **Rationale:** PRD § Core Features, Sorting names the four fields and the direction only.
  tracker16-X's FDR says no more (`fdr.md` § 10), and its code has no sorting (PRD § Risks). Each rule
  above is the reading that I expect would surprise you least. `low` to `high` follows the order the
  PRD lists the priorities in, read upwards. Keeping undated tasks last stops them crowding the top of
  a list sorted by due date. Ignoring case keeps "apple" and "Banana" in the order a person expects. A
  fixed tie order makes the same list come out the same way every time, which the tests need.
- **If overridden:** FR-36's list changes and AC-14's sort cases change with it. If undated tasks are
  to sort first, or flip with the direction, only FR-36 and AC-14 move.
- **Confirm or override:** confirm, with one addition. The tie rule holds even when two tasks carry the same recorded creation time: the system keeps the order in which tasks were created independently of the time it records, so ties, and a sort by created time itself, still come out the same way every time. The priority rule's reason is that ascending means rising, and `high` is more than `low`. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.5 The assignee filter takes only names on the current list, so a removed name can't be filtered on
- **Drafted into the SRS:** FR-33. The assignee filter accepts only a name on the current list. A
  name not on the list is refused. A task that still carries a removed name cannot be found by its
  assignee.
- **Rationale:** PRD § Core Features says tracker17 "behaves as its predecessor does wherever both
  cover a rule". tracker16-X refuses a filter on a name not on the list (`fdr.md` § Examples, "Filter
  tasks by `--assignee alice` where `alice` is not in assignee list | Rejected with error"). It also
  keeps a removed name on its tasks (§ 5). The PRD's trail names the consequence and leaves it to the
  SRS (`products/tracker17/docs/trail/prd/self_answer-1.md` § 2.3, "the operator cannot filter for
  tasks that still carry a removed name"). I drafted the predecessor's rule because the PRD binds it. I
  am raising it because you would see the consequence.
- **If overridden** (allow any name that is on the list or on a task): FR-33 changes to accept those
  names, and still refuses a name found on neither. AC-14's assignee case changes to include a removed
  name. RN-1's predecessor list is
  unaffected, because the filter rule is stated in FR-33 and not in RN-1.
- **Confirm or override:** confirm. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.6 Which rows the summary's per-assignee part shows
- **Drafted into the SRS:** FR-38. The per-assignee part has one row for every name on the current
  assignee list, a zero count included. It has one more row for each name not on the list that an open
  task in the project still carries. It always has an "(unassigned)" row.
- **Rationale:** PRD § Core Features, Project summary says "each assignee's open tasks", with
  unassigned tasks counted as "(unassigned)". The PRD does not say whether a name with no open tasks
  appears, or whether a removed name does. tracker16-X has no summary code (PRD § Risks). On my reading,
  "each assignee" means each name on the list, so the zero rows show. A removed name still carried by
  open work is open work someone is holding, so it gets a row too.
- **If overridden** (only names with at least one open task): FR-38's last paragraph changes, and
  AC-14's summary case changes with it.
- **Confirm or override:** confirm. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.7 The operator's name and a comment's text must not be blank
- **Drafted into the SRS:** FR-27 requires the operator's name to contain a non-whitespace character.
  FR-28 requires the same of a comment's text.
- **Rationale:** This departs from tracker16-X's code, so it needs your sign-off under the PRD's
  "behaves as its predecessor" clause. That code accepts an empty name as a set name
  (`task-tracker-X/tasktracker16x/application/task_service.py`,
  `add_comment`, "an empty string IS a configured user"). It also stores comment text unchecked
  (`tasktracker16x/domain/comment.py`, `Comment`, "no validation is applied"). A
  comment by "" or with no text shows the reader nothing, and the PRD's rule that a comment needs a
  name set first would then be met by a blank one. tracker16-X already refuses blank project names,
  titles and assignee names, so this draft brings the last two text fields in line with them.
- **If overridden** (keep the predecessor's behaviour): FR-27 drops its non-whitespace rule, and FR-28
  drops the text rule. FR-39's "a required text field left blank" then excludes these two fields, and
  AC-12 loses those two cases.
- **Confirm or override:** confirm, with the reason changed. These two rules are not a departure from tracker16-X, because tracker16-X has no rule here to depart from: its comment code says "no validation is applied (the spec adds none)" (`tasktracker16x/domain/comment.py`, `Comment`), and its acceptance of an empty name comes from how its command-line config stores a user, which PRD § Out of Scope drops. The rules follow from the PRD's own words instead: "a comment can't be added until a name is set", and a blank is no name, and "A comment is text on a task", and a blank is no text. A review note for FR-27 and FR-28 cites those PRD lines. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.8 How fast is fast enough, and how much data it must hold
- **Drafted into the SRS:** NFR-1. With up to 1,000 tasks across all projects, and up to 20 comments
  on any one task, every action shows its result within 1 second on your machine. AC-15 measures it.
- **Rationale:** The PRD sets no speed or size. It does name three actions that must feel effortless (PRD § UX
  Notes, What must feel effortless), and that needs a bar a test can check. The numbers are mine, with nothing in the PRD to derive
  them from. 1,000 tasks is far above what one person tracking a small team's work would enter, and
  1 second is about where a local app starts to feel slow. Treat both as placeholders you can move.
- **If overridden:** NFR-1's numbers change, and AC-15's test data and limit change with them. A much
  larger volume could push the SDD toward a different kind of storage, which NFR-10's simplicity
  judgement would pay for.
- **Confirm or override:** confirm, with one addition. AC-15 loads the most NFR-1 allows: 1,000 tasks with 20 comments on every one of them, not 20 comments on one task. Keep 1,000 tasks, 20 comments per task and 1 second. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.9 Where the saved data lives
- **Drafted into the SRS:** FR-6. The saved data lives in one place inside your copy of tracker17,
  kept out of version control, wherever the tracker is started from.
- **Rationale:** PRD § Out of Scope drops tracker16-X's per-working-directory data. PRD § Data &
  Privacy needs the instructions to name one place you delete to remove every name. Keeping the data
  inside the copy means deleting the copy removes everything, and setting the data aside is one folder
  to move. It also leaves nothing behind in your home folder. The alternative is a fixed folder in
  your home directory, which survives deleting and re-cloning the copy. Where your data sits is
  something you see, so the call is yours.
- **If overridden** (a folder in the home directory): FR-6's location sentence changes. FR-4's
  instructions name that folder, and AC-8 checks it there. RN-6 is unaffected.
- **Confirm or override:** confirm, with one addition. FR-4's line on where the saved data is kept also says that, because the data is kept out of version control, a clean of the copy that removes ignored files deletes it. Reasoning in `docs/trail/srs/self_answer-1.md`.

### 2.10 Which browsers are supported
- **Drafted into the SRS:** NFR-13. Current stable desktop Chrome and other Chromium-based browsers
  are supported, and the end-to-end tests run in Chromium. Firefox and Safari are not a commitment.
- **Rationale:** PRD § UX Notes, Defaults says "a desktop browser" and names none. A browser the tests
  never run in is a support claim nobody checks. Running the end-to-end tests in more than one browser
  adds setup weight for anyone running the suite, so the draft names one engine. Your own **Works** run-through (AC-1) happens in whichever browser you use, so if
  that browser is Safari or Firefox, say so here.
- **If overridden** (add a browser): NFR-13 names it. NFR-11 and AC-2 run the end-to-end layer in it
  too, and the instructions in FR-4 name what it needs.
- **Confirm or override:** confirm. This machine's default web browser is Google Chrome, so the owner's **Works** run-through (AC-1) happens in a supported browser. Reasoning in `docs/trail/srs/self_answer-1.md`.

## 3. Raised from downstream — an item from a seat that did not write the SRS

None.
