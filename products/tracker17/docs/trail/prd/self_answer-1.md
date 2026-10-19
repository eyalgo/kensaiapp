# Self-answer report — PRD.md

## Header

- **Companion:** products/tracker17/docs/PRD_open_issues.md
- **Document:** products/tracker17/docs/PRD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-05
- **Sources re-read:**
  - `task-tracker-X/docs/fdr.md`, tracker16-X's FDR. Its § Rules 1–13
    state every rule item 2.3 carries except unique project names. § Description, "A CLI task tracker
    for a small team", is almost word for word the owner's round-0 answer 1.1. Its header line
    "Source: PM requirements (2026-06-12)" shows the predecessor has no PRD above its FDR.
  - `task-tracker-X/docs/adr.md`, Project entity, "`name`: str —
    required, unique", and `tasktracker16x/application/project_service.py`, `create_project`, which
    raises `DuplicateProjectNameError`. These are where unique project names come from.
  - `task-tracker-X/tasktracker16x/cli/app.py`, `_build_parser` and
    `main`. The command set has no filter, sort or summary command, and `task update` takes only
    `--assignee`, `--unassign`, `--priority` and `--due`, with no title. This confirms the PRD's Risks
    line. The same file imports its services from `tasktracker16x.application` and keeps argument
    parsing in the CLI layer.
  - `tasktracker16x/domain/comment.py`, `Comment`: "``author`` is resolved from the global user config
    at add time".
  - `gh repo view <instance-repo> --json visibility` returned `"visibility":"PRIVATE"`.
    `git -C task-tracker-X remote -v` printed nothing, so that
    repository has no remote.
- **Note on the companion as found:** every confirm-or-override slot was blank rather than holding the
  template's stub, `<"confirm", or "override: <what to do instead>">`
  (`<CORE>/templates/product-templates/prd_open_issues_template.md`, § 2). This run read a blank slot
  as unanswered. Correcting the stub is `product-prd`'s job, not this run's.

## Items worked

### 2.1 — Who uses it: a reader, plus one operator; the "small team" is only who tasks are assigned to

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The reading is right, and the draft's own argument for it holds. It reconciles answers 1.1,
  1.2 and 1.5 with the Agari answer "I can use it locally easily by myself"
  (`system/projects/tracker17/agari_open_issues.md`, § 1.1). The addition is the stronger ground the
  draft did not have. The owner's answer 1.1 repeats tracker16-X's FDR description almost word for
  word, "A CLI task tracker for a small team"
  (`task-tracker-X/docs/fdr.md`, § Description). That predecessor
  already serves one operator. It has one configured user name (§ 12 User config), a global assignee
  list (§ 5 Assignees) and no authentication (§ Out of scope). On this reading, "small team" is
  inherited wording for the people whose work is tracked, not a group of users, and the PRD's reader
  gains from being told where the phrase came from. Check 3 found nothing in the PRD that this
  contradicts: Out of Scope, Data & Privacy and the Risks line "'Small team' can mislead a reader" all
  agree with it. Check 4, the concurrent case, is one operator with the tracker open in two browser
  tabs at once. Neither the PRD nor this answer covers it. The predecessor put "multi-process
  concurrency" out of scope (§ Out of scope). How the tracker behaves then is a requirements question
  for the SRS, not a question about who the users are. The alternative verdict was a plain *confirmed*.
  It would have left the PRD's case resting on a reconciliation of the owner's answers, when the
  owner's own source material settles the question directly.

### 2.2 — The browser is the only interface — no command line ships

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** The owner's answers name the browser as the interface twice. Answer 1.1 says "you use it in
  the browser" and answer 1.9 says "Web" (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1). A second
  interface would double what the reader has to read, which runs against Goals "It is simple". The
  draft says reuse doesn't require exposing the command line, and that claim holds at the source. In
  tracker16-X the command line is a separate layer. `tasktracker16x/cli/app.py` imports its services
  from `tasktracker16x.application` and keeps all argument parsing to itself, so the rules can be
  reused without the commands. Check 3: dropping the per-working-directory data location
  (`fdr.md`, § 13 Persistence) leaves the PRD silent on where saved data lives. That gap matters to
  Data & Privacy's deletion line and is answered under item 2.7, which was decided with this item in
  view. Dropping the `+3d` shorthand removes no feature the owner listed. Answer 1.1 says "due dates",
  and the PRD keeps them. Check 4 found no failure path that this choice changes.

### 2.3 — tracker16-X's task rules become tracker17's own

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Carrying the predecessor's rules was the right call. The owner's answer 1.1 repeats
  tracker16-X's FDR description almost word for word
  (`task-tracker-X/docs/fdr.md`, § Description). Answer 1.5 is that
  FDR's out-of-scope list without its two interface lines (§ Out of scope). The project card names
  tracker16-X as the code tracker17 prefers to reuse (`system/projects/tracker17/project.md`, "Source
  material:"). Check 3 re-read each listed rule at the source rather than trusting the draft's list.
  Status workflow, `medium` as default, assignees, labels, the overdue rule, comments, filtering,
  sorting, the six summary counts and the project-delete cascade are `fdr.md` § Rules 1–11. The name
  needed for comments is § 12. All of them match `products/tracker17/docs/PRD.md` § Core Features.
  One rule is not in the FDR: **unique project names**. Its source is the predecessor's ADR
  (`docs/adr.md`, Project entity, "`name`: str — required, unique") and its code
  (`application/project_service.py`, `create_project`, `DuplicateProjectNameError`). The draft's
  claim still holds. The rule is tracker16-X's, from a different document of it.
  Check 4, the stale case, found the addition. The operator may change their own name after writing
  comments. tracker16-X sets a comment's author when the comment is added
  (`tasktracker16x/domain/comment.py`, "``author`` is resolved from the global user config at add
  time"), so earlier comments keep the old name. The PRD's "behaves as its predecessor does" clause
  implies this, but the browser adaptation, where the name is set in the app, makes it a visible
  choice. One plain line in Core Features costs nothing.
  A second stale case is named and not covered. The predecessor rejects a filter on an assignee name
  that is not on the list (`fdr.md`, § Examples, "Filter tasks by `--assignee alice` where `alice` is
  not in assignee list | Rejected with error"). Names also stay on tasks after removal (§ 5). Together,
  under the PRD's "behaves as its predecessor" clause, the operator cannot filter for tasks that still
  carry a removed name. The PRD does not need to settle this. It is a requirements detail for the SRS,
  and it is recorded here so that seat meets it as a known consequence rather than discovering it.

### 2.4 — The three success bars and when they are checked

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The three bars follow from the owner's own words. Answer 1.6 says "I will run it locally
  and see it works", and answer 1.4 says "Look at the code, see if it works, and see if it's simple to
  set up" (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1). Keeping "simple to read" as the owner's
  pass/fail call is right, for the reason the draft gives. A size number would reward cramming code
  into fewer lines rather than making it clearer. Check 2 found that the **Works** bar answers a
  wider question than it can check. It requires "every Key Use Case" to run "in the browser"
  (`products/tracker17/docs/PRD.md`, § Success Metrics). Key Use Case 1 (get a copy and follow the setup)
  and Key Use Case 2 (read the code and tests) are not browser actions (§ Key Use Cases). A reader
  applying the bar literally either can't run it or counts the setup twice. The fix is to scope
  **Works** to use cases 3–5 and say which bar covers 1 and 2. All three use cases stay covered.
  Check 4, the refused case, is about gaming the count. "At most three commands" can be met on paper
  by joining any number of steps with `&&`. So the addition counts each joined command separately.
  A single script the instructions name, such as one setup command, still counts as one, and that is
  intended: it is how a simple setup reads. The numbers themselves, 3 commands and 10 minutes, have
  nothing behind them, as the draft admits. This run found no better grounds for any other number.
  They are a reasonable ceiling for a small app on a developer's machine, so they stand. What would
  have tipped this toward *left for the owner*: if the owner had said what "simple" means to them in
  numbers. They didn't, and the draft's own invitation to "change them freely" stays open to them in
  any later round.

### 2.11 — What a reader gets: source code to read and run — no package, installer or hosted demo

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** This is the answered half of item 2.5, moved out as item 2.11 because 2.5 asks two questions
  with different deciders. The other half, whether tracker17 is made public and where, is left for
  the owner under item 2.5 (see § Left for the owner). Check 2 holds for this half. The owner's answer
  1.4 is "Look at the code, see if it works, and see if it's simple to set up on a machine"
  (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1). A package or installer hides the code and the
  setup being judged. A hosted demo skips setup and is also excluded by answer 1.5, "Not hosted". The
  two halves are separable: source code with written instructions is the right form whether
  tracker17 stays private or is published, so this answer rests on no decision the owner has yet to
  make. Check 3 found it consistent with `products/tracker17/docs/PRD.md` § Out of Scope, § UX Notes
  "Arrival" and Success Metrics "Simple to set up", which starts "from a fresh copy". Check 4, the
  absent case: a reader with no copy of the source cannot start at all. Today that is every outside
  reader, which is exactly what item 2.5's remaining question is about. The slot on item 2.11 is left
  empty for the next round, as the skill requires for an item this run appended. The answer this run
  reached is **confirm**.

### 2.6 — Reachable only from the machine it runs on

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The conclusion is right, and the draft's reason, "multi-user by accident", is true but not
  the strongest one. The PRD rules out login and access control (`products/tracker17/docs/PRD.md`,
  § Out of Scope). So a tracker reachable from other machines is not only multi-user. It is open to
  anyone on the same network, who can read the names it holds and change or delete the operator's
  work. Check 3 found that this also keeps another statement true. Data & Privacy says "None of it
  leaves the machine", and that holds only if no other machine can reach the tracker. So the
  reachability line is what that privacy statement depends on, and the PRD should say so where the
  line sits. Check 4, the refused case: another machine trying to reach the tracker gets nothing,
  which is the intended outcome and needs no message. This run also asked whether this is a
  security trade-off only the owner may make. It is not a trade-off. The draft takes the safe side,
  and that commits the owner to nothing they did not already ask for in answer 1.5, "Not hosted or
  multi-user over a network" (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1.5).

### 2.7 — Data & Privacy: it does hold people's names (changes your "No")

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft corrects a fact. It does not make a privacy trade-off, and that is why this run
  decided it rather than leaving it to the owner. The product stores assignee names, the operator's
  own name and comment authors (`products/tracker17/docs/PRD.md`, § Core Features "Assignees" and
  "Comments"). Writing "no personal data" would be false. Recording the names changes no behaviour and
  commits the owner to nothing. The owner's answer 1.7, "No", still holds in what it plainly meant:
  nothing is collected, sent or shared. Check 4, the absent case, found the addition. The section's
  deletion line, "the operator removes all of it by deleting the tracker's saved data", works only if
  the operator can find that data. tracker16-X kept it in `.task_tracker/data.json` under the working
  directory (`fdr.md`, § 13 Persistence). Item 2.2 confirmed that this location is not carried over,
  and the PRD names no other. The setup instructions are already in scope (§ Scope (In)) and already
  carry how to restart (§ UX Notes "Failure states"), so they are where the location goes. Without
  it the deletion promise has nothing behind it. The stale case is covered by the draft as written. A
  removed assignee's name stays on tasks (§ Core Features), and comments cannot be edited, so one
  person's name cannot be removed on its own. The section's whole-data deletion is the honest answer
  for a single-operator local tool.

### 2.8 — First run, saved data, failure states and what must feel easy

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Each choice in the draft is the simplest one that protects the operator's work. Starting
  empty adds no sample-data scope. Offering only allowed status moves follows tracker16-X's workflow
  table (`fdr.md`, § 3). Surviving a restart is what "use it locally" needs. The effortless three
  match the owner's feature list (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1.1). Check 4 walked
  the five failure classes. **Empty**: the draft covers a first run, an empty project and a filter
  that matches nothing. **Absent**: no saved data at all is a first run, and the draft keeps that
  apart from unreadable data. **Refused** found the addition. "If the saved data can't be read, the
  tracker says so" stops short of what happens next. If the next action wrote a fresh empty store over
  the unreadable one, the operator's work would be lost after all, which is what the line exists to
  prevent. So the tracker must never overwrite data it could not read. The operator's way forward is
  in the written instructions, which item 2.7 already adds the data's location to. **Concurrent** and
  **stale** are named and not covered here. One operator may have the tracker open in two browser
  tabs, or leave a list open past midnight so its overdue marks go stale. tracker16-X put
  multi-process concurrency out of scope (`fdr.md`, § Out of scope). Live updating is close to the
  PRD's excluded "real-time collaboration". How tracker17 behaves in these cases is a requirements
  question for the SRS, which this answer records rather than settles.

### 2.9 — Everyday defaults

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** Each default is the smallest commitment that fits a single operator using a browser on
  their own machine, and none of them adds scope the owner ruled out. Check 3 found one default doing
  more work than the draft says. "Dates shown as calendar dates in the machine's local day" is also
  what the overdue rule needs. The rule compares a due date with "today" (`products/tracker17/docs/PRD.md`,
  § Core Features "Due dates"). tracker16-X takes today from the local clock,
  `datetime.date.today()` in `tasktracker16x/cli/app.py`, `_list_tasks`. So the two agree. Keyboard
  use for every action is a floor that a plain browser interface meets almost entirely with standard
  controls, and the "simple" goal does not argue against it. This run also asked whether the defaults
  are a matter of taste the owner has kept for themselves. Nothing in the owner's answers reserves
  one, and `<CORE>/doctrine/governance/where_taste_appears.md` has a document upstream state "The
  requirement, never the preference." These lines are requirements (language, device class,
  keyboard), so the PRD is the right place for them. Check 4's stale case, a list left open past
  midnight, is recorded under item 2.8 for the SRS.

### 2.10 — Why it beats the alternatives, and what it costs

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft asks whether to keep or cut the definition-to-code trace, Key Use Case 2. Keep it.
  The owner's answer 1.2 says the product is for "someone who is interested in seeing how kensaiapp
  builds apps" (`products/tracker17/docs/trail/prd/cycle-1.md`, § 1.2). How kensaiapp builds an app is
  the walk from a product definition down to code and tests. Reading the code alone shows what was
  built, not how. On this reading the trace is the answer to 1.2, not an addition to answer 1.4's
  "look at the code". It costs no extra feature to build. The definition documents are written
  anyway, because the project card sets `**Definition:** full` (`system/projects/tracker17/project.md`),
  and they sit beside the code under `products/tracker17/docs/`. Check 2 found the draft's argument
  for the edge weaker than it could be. "An app people recognise" is a difference of interface, and
  the draft itself says it is unproven. The source supplies a stronger, measurable difference.
  tracker16-X's definition begins at an FDR whose header reads "Source: PM requirements (2026-06-12)"
  (`task-tracker-X/docs/fdr.md`), with no PRD above it. So the
  predecessor cannot show a top-to-bottom trace, and tracker17 can. That is the addition. The
  "unproven" line about simplicity still stands, because the stronger reason concerns the trace, not
  whether a browser app is simpler. Check 3 found the Goals line consistent with the owner's answer
  1.8, no outside services: no running cost and no revenue for an example. Check 4: if a reader is
  put off by the number of documents, the trace becomes a cost to simplicity. That risk is already
  the one the PRD names under Risks, "A browser app may be less simple", and the owner's own
  "Simple to read" judgement in Success Metrics is what would catch it. What would have tipped this
  toward cutting Key Use Case 2: an owner statement that "how kensaiapp builds apps" meant the code
  only. None was given.

## Left for the owner

### 2.5 — How someone gets it: source code in its repository, no package or hosted demo

- **Bucket:** 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override
- **Verdict:** left for the owner
- **Why:** Item 2.5 asks two questions. The first is what form tracker17 is offered in. This run
  answered it and moved it out as **item 2.11** (see § Items worked). The second, which the draft
  raises in its own rationale, is the one left here: **should tracker17 be public, and where do
  outside readers get it?** It is the owner's call for two reasons this run can name. First, publishing
  code commits the owner's public presence to outside readers. Second, this instance does not decide
  what it shows outsiders. `kensaiapp.md` § What this is about says documents describing kensaiapp
  to an outsider are written and managed by another instance, and this run cannot see that instance's
  plans. A measured fact bears on the call without deciding it: today no outside reader can reach
  tracker17. `gh repo view <instance-repo> --json visibility` returned `"PRIVATE"`. The
  predecessor's repository at `task-tracker-X` has no git remote.
  The item's slot is left empty so that the question survives the fold.
- **The answer I would have given:** Not yet. Keep tracker17 inside this instance while the owner stands
  in for the reader, as `products/tracker17/docs/PRD.md` § Target Users already says ("Until outside
  readers arrive, the owner stands in"). Have the PRD's Assumptions say plainly that outside readers
  cannot reach it until the owner publishes it. Once outside readers are invited, publish tracker17 as
  its own small public repository holding the code, the tests and its definition documents. A reader
  should clone that one repository, not the whole instance repository. Then the "fresh copy" in
  Success Metrics "Simple to set up" means a clone of that repository, and Key Use Case 2 still works
  because the definition documents travel with the code.

## Skipped

- **§ 1, § 3, § 4** — each says "None." and holds no item.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/PRD.md** — `<CORE>/launchers/skill/launcher.sh product-prd tracker17`
