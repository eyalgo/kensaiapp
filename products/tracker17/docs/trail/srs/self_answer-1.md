# Self-answer report — SRS.md

## Header

- **Companion:** products/tracker17/docs/SRS_open_issues.md
- **Document:** products/tracker17/docs/SRS.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:**
  - `task-tracker-X/docs/fdr.md`, tracker16-X's FDR. § Product
    decisions says "Third-party libraries are allowed" (item 2.1). § 9 Filtering says "two independent
    optional bounds: `--due-from <date>` and `--due-to <date>`" and does not say whether the ends are
    included (item 2.3). § 10 Sorting names the four fields and the direction only (item 2.4). § 11
    Project summary says "Open task count per assignee … tasks with no assignee are shown as
    `(unassigned): N`" (item 2.6). § Examples has "Filter tasks by `--assignee alice` where `alice` is
    not in assignee list | Rejected with error", and § 5 Assignees keeps a removed name on its tasks
    "as a historical value" (item 2.5).
  - `task-tracker-X/pyproject.toml`, which declares
    `dev = ["pytest"]`, so the predecessor already fetches a third-party test tool at setup (item 2.1).
  - `task-tracker-X/tasktracker16x/` searched for `due_from`,
    `due_to`, `sort` and `filter`. The only hits are label display order in `cli/app.py` and
    `persistence/json_repository.py`, which returns tasks "sorted(tasks, key=lambda task: task.id)" so
    that creation order survives. No range or sort rule exists in code to copy (items 2.3 and 2.4).
  - `tasktracker16x/application/task_service.py`, `add_comment`: "an empty string IS a configured user,
    per the `is None` predicate". `tasktracker16x/domain/comment.py`, `Comment`: "``text`` is stored
    verbatim — no validation is applied (the spec adds none)" (item 2.7).
  - This machine's default web browser:
    `plutil -convert json -o - ~/Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist`
    shows `LSHandlerRoleAll: com.google.chrome` for both `http` and `https`, and `/Applications` holds
    `Google Chrome.app` and `Safari.app` (item 2.10).

## Items worked

### 2.1 — Setup may download public dependencies, and the running tracker uses no network

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft's reading is right, and the PRD gives it a firmer reason than the one the draft
  gives. PRD § Dependencies / Integrations says nothing needs "a network connection beyond the machine
  itself", but Key Use Case 1 has the reader "gets a copy of tracker17", and PRD § Assumptions has the
  reader "getting a copy of a code repository". Getting the copy already uses the network. So the PRD's
  no-network line cannot be about setup, and on this reading it is about using the tracker, which is
  what PRD § Goals says ("runs on the operator's machine and uses no outside service"). The setup bar
  in PRD § Success Metrics bans only "an account, a key or a sign-up", and public package sources ask
  for none of those. tracker16-X already does this: its FDR allows third-party libraries
  (`task-tracker-X/docs/fdr.md` § Product decisions) and its
  `pyproject.toml` declares `dev = ["pytest"]`. Check 3 found no conflict: NFR-5 and AC-11 are about
  the running tracker, and C-2 bans accounts and keys, not downloads.
  Check 4 found two cases the draft does not reach. **Absent**: on a machine with no network at setup,
  the fetch fails. FR-4 already lists "the prerequisites the machine needs before setup", so the fix is
  to name the one-time network connection there. Then an offline failure is one the instructions
  explain. **Stale**: a dependency fetched by version range can change between the day the suite
  passed and the day someone takes a fresh copy, and AC-2 and AC-3 are run from a fresh copy. Fixing
  each dependency to an exact version keeps the copy that passed and the copy that is set up the same.
  This states what must hold, and the SDD chooses how. I was close to a plain *confirmed*. The stale
  case tipped it, because the owner's own Agari check is a fresh-copy run some time after the build.
  I also weighed raising an item on the PRD's companion, because PRD § Dependencies / Integrations,
  read alone, says no network at all. I did not raise it. The PRD's own Key Use Case 1 and Assumptions
  already show the line cannot cover setup, and SRS § 5.3 states the reading and cites both PRD lines,
  so a reader of the two documents together is not misled. A settled PRD is not reopened for wording
  no reader is missing. If the owner wants the PRD to say "while it runs" itself, that is a one-line
  item for `product-prd`.

### 2.2 — Pages show the state when they were loaded, and every action is checked against the saved data

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft's core rule holds. Checking each action against the saved data when it is applied
  keeps FR-18's workflow true whatever an old page shows, and pages that do not update themselves are
  the smaller product PRD § Goals, "It is simple", asks for. One part of the draft's reasoning is
  weaker than it reads. PRD § Out of Scope excludes "real-time collaboration", which is about several
  people. One operator with two tabs is not collaboration, so that exclusion does not by itself rule
  out live pages. Simplicity is the reason that carries the choice. The two cases come from the PRD's
  trail (`products/tracker17/docs/trail/prd/self_answer-1.md` § 2.8, "One operator may have the
  tracker open in two browser tabs, or leave a list open past midnight").
  Check 4 found three cases the draft does not reach. **Stale, after a crash**: NFR-3 says a second
  start "against the same location refuses". NFR-2 expects the tracker to be stopped by "a crash, a
  killed process or a power cut". If the marker that one tracker is running outlives such a stop, every
  later start refuses, and the operator's work is locked out with nothing in the instructions to fix
  it. So the check must refuse only while another tracker is actually running, and AC-16 needs a
  second case: a start after a killed tracker succeeds. **Concurrent, with a deletion**: FR-39's last
  refusal reads "because the task has changed since it was shown". A task or a project that another
  tab deleted has not changed, it is gone, and adding a task to a deleted project is not a task change
  at all. The refusal has to name that case too. **Concurrent, a plain edit**: two tabs editing the
  same task's title both pass the check, because each edit is valid against the saved data. The
  later one replaces the earlier one. I chose to state that rather than prevent it, because both edits
  are the one operator's own and preventing it needs a version check on every edit, which NFR-10's
  simplicity judgement would pay for. A named uncovered case is an answer. Check 3 read FR-25 against
  the stale overdue marks and found them consistent: FR-25 fixes "today" at the moment the list is
  produced.

### 2.3 — Due-date range ends are included, and tasks with no due date fall outside any range

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Both rules hold. tracker16-X's FDR names the bounds `--due-from` and `--due-to` and says no
  more (`task-tracker-X/docs/fdr.md` § 9), and its code has no range
  filter to copy (a search of `tasktracker16x/` for `due_from` and `due_to` finds nothing). "From" and
  "to" read as including both days, and a task with no date has nothing to place in a range. The
  draft says "which tasks a filter shows is something you see, so the call is yours". Check 1 does not
  treat that as the owner's reserved call: it names no ground I cannot see, and the PRD reserves no
  taste over filter edges. So I decided it in the owner's seat.
  Check 4 found one case the draft does not reach. **Empty, by mistake**: a from-date later than the
  to-date matches nothing under the drafted rule, so FR-37 would answer "nothing matched". That message
  is false in spirit, because tasks may well fall between the two dates the operator meant. PRD § UX
  Notes, "Refusals say why", sets the house rule that the operator is told the reason, so the reversed
  range is refused with one. A same-day range, from-date equal to to-date, is not reversed and matches
  tasks due that day. Check 3 found nothing that depends on the ends beyond FR-34 and AC-14, as the
  draft says.

### 2.4 — How sorting orders priority, missing due dates, titles and ties

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** All four rules hold, and one of the draft's reasons does not. The draft says `low` to `high`
  "follows the order the PRD lists the priorities in, read upwards". PRD § Core Features, Priorities
  lists them as `low`, `medium` or `high`, so that order read as written already gives the drafted
  answer, and "read upwards" would reverse it. The reason that carries the rule is that ascending means
  rising, and `high` is more than `low`. Undated tasks last in both directions, and titles compared
  without letter case, are the readings that surprise a person least, as the draft says. Neither the
  FDR (`task-tracker-X/docs/fdr.md` § 10) nor tracker16-X's code has
  any sort rule to copy.
  Check 4 found one case the draft does not reach. **Concurrent, at creation**: the tie rule says
  equal tasks "keep the order in which they were created". FR-15 records "when the task was created",
  and two tasks made within the same recorded instant carry the same time. The tie rule then has
  nothing to order by, and neither does a sort by created time. tracker16-X avoids this by returning
  tasks "sorted(tasks, key=lambda task: task.id)"
  (`tasktracker16x/persistence/json_repository.py`), so creation order there never depends on the
  clock. tracker17 needs the same property stated: creation order is kept independently of the
  recorded time. How it is kept is the SDD's. Check 3 read FR-15's identity rule, "unique across all
  projects and is never reused", and found that it does not promise an order, so the addition is not
  already carried.

### 2.5 — The assignee filter takes only names on the current list, so a removed name can't be filtered on

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** The PRD binds this rule, so an override is not open to the SRS. PRD § Core Features opens
  "tracker17 behaves as its predecessor does wherever both cover a rule", and both cover this one:
  the PRD filters by assignee, and tracker16-X refuses a filter on a name not on the list
  (`task-tracker-X/docs/fdr.md` § Examples, "Filter tasks by
  `--assignee alice` where `alice` is not in assignee list | Rejected with error"). The rule is a task
  rule, not one of the command-line mechanics PRD § Out of Scope drops. Overriding it would move the
  PRD's clause, which is the CPO's document, and nothing in the operator's experience is bad enough to
  argue for that.
  Check 4, the refused case, is what makes the consequence acceptable. The refusal still means
  something afterwards: FR-20 lets the operator add a name, names are compared exactly, and FR-22
  leaves the removed name on its tasks unchanged. So adding the name back makes those tasks findable by
  it again. Check 3 read this answer against item 2.6's draft, which gives a removed name still held
  by open work its own row in the summary, and the two items were decided together. The two agree. The summary shows that open work
  exists under the removed name, and adding the name back is how the operator filters to it. I was
  close to adding a line to FR-33 telling the operator about that way back. I did not, because FR-39
  already requires the refusal to give its reason, and the wording of the reason is the UXD's.

### 2.6 — Which rows the summary's per-assignee part shows

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** Each of the three row rules has a ground. A row for every listed name, zero included, is
  the plain reading of "each assignee's open tasks" (PRD § Core Features, Project summary), and it
  matches RN-15's zero counts for statuses and priorities, so the summary reads the same way
  throughout. The "(unassigned)" row is always present because tracker16-X specifies it as
  "`(unassigned): N`" with no exception for zero
  (`task-tracker-X/docs/fdr.md` § 11 and Self-review fix SR8). A
  removed name still carried by open work gets a row because that work is open and someone holds it.
  Dropping the row would make the per-assignee counts add up to fewer than the project's open tasks,
  which a reader checking the summary would read as a wrong result under PRD § Success Metrics,
  **Works**. That last ground is mine, and it is stronger than the draft's.
  Check 3 read this answer against item 2.5, and the two were decided together. 2.5 keeps the
  predecessor's rule that a removed name cannot be filtered on. The summary row tells the operator such
  work exists, and adding the name back makes it filterable. Check 4 walked the edges. An empty project
  shows every listed name at zero and "(unassigned)" at zero. With an empty assignee list only
  "(unassigned)" shows. A removed name carried only by `done` or `cancelled` tasks gets no row, which
  is right, because the part counts open work. A removed name that is added back is on the list and
  gets one row, not two, because names are compared exactly (FR-20).

### 2.7 — The operator's name and a comment's text must not be blank

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The rules are right, and the draft's reason for asking the owner does not hold. The draft
  treats them as a departure from tracker16-X that needs sign-off under PRD § Core Features, "behaves as
  its predecessor does wherever both cover a rule". The clause binds only where tracker16-X *has* a
  rule. Its FDR states none for blank names or blank comments (`fdr.md` § 8 and § 12), and its code
  says so in its own words: "``text`` is stored verbatim — no validation is applied (the spec adds
  none)" (`tasktracker16x/domain/comment.py`, `Comment`). The empty-name behaviour, "an empty string IS
  a configured user, per the `is None` predicate" (`tasktracker16x/application/task_service.py`,
  `add_comment`), is how `config set user` stores a value. That is command-line mechanics, which PRD
  § Out of Scope says "are not carried over". So the clause does not reach this case, and the PRD's own
  text decides it. PRD § Core Features, Comments says "a comment can't be added until a name is set" and
  "A comment is text on a task". A blank is neither a name nor text. The draft's consistency argument,
  that tracker16-X already refuses blank project names, titles and assignee names, is true and
  supporting. On this reading the call is the SRS's own, made in the owner's seat. It is not a
  sign-off the owner owes.
  Check 3 found no conflict: FR-39's "a required text field left blank" and AC-12 already carry both
  cases. Check 4 walked the refused case. A name change to a blank is refused and the old name stays,
  so FR-30's history is unaffected, and FR-28's "before the operator has set a name" refusal still
  covers a first run.

### 2.8 — How fast is fast enough, and how much data it must hold

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The PRD sets no number, so any bar is a choice, and these two are sound ones. 1,000 tasks is
  well above one person tracking a small team's work (PRD § Target Users), and 1 second is a bar the
  operator would notice being missed. Check 1 found no reserved call here: the numbers bind no person
  and no outside party, and the draft itself calls them placeholders. So I decided them in the owner's
  seat.
  Check 3 found the SRS disagreeing with itself. NFR-1 holds "up to 20 comments on any one task",
  which allows every task to carry 20. AC-15 loads "1,000 tasks and 20 comments on one task", about
  1,020 comments where NFR-1 allows 20,000. A store that is read whole on every action would pass
  AC-15 and could still miss NFR-1 at its stated limit. The test has to load what the requirement
  promises, so AC-15 moves to match NFR-1. I chose that over shrinking NFR-1, because a comment count
  per task is easier for the operator to picture than a total. On the order of 20,000 short comments is
  a few megabytes, which on this reasoning a simple local store still handles within the bar.
  Check 4, the empty case, needs nothing more: an empty tracker is the easy end of the same bar.

### 2.9 — Where the saved data lives

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** Inside the copy is right, and there is a stronger reason for it than the draft gives. The
  owner's own Agari check, **Simple to set up**, starts "from a fresh copy" on the owner's machine
  (`system/projects/tracker17/agari.md`, bar 2, and AC-3), and that machine is where tracker17 will
  already have been run while it was built. With data in a fixed home-folder location, the fresh copy
  would open on the old data, and the check would never see FR-7's empty first run. With data inside
  the copy, a fresh copy is truly fresh. The draft's own reasons also hold. Deleting the copy removes
  every name, which meets PRD § Data & Privacy, Deletion. Setting the data aside is moving one folder,
  which AC-8 checks. The draft says "where your data sits is something you see, so the call is yours".
  Check 1 does not treat that as the owner's reserved call, because it names no ground I cannot see,
  so I decided it in the owner's seat.
  Check 4 found one case the draft does not reach. **Absent, by accident**: the reader is a developer
  (PRD § Assumptions), and the data is "never committed to version control" (FR-6). A developer
  cleaning the copy of files version control ignores deletes the saved data with no warning. FR-4
  already says where the data is kept, so the addition is one more clause there. Two copies of
  tracker17 on one machine each keep their own data, and the second to start on the same local address
  meets FR-3's refusal, so that case needs nothing new.

### 2.10 — Which browsers are supported

- **Bucket:** 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed
- **Why:** The draft names one ground it could not see: which browser the owner uses for the AC-1
  run-through, and whether that is Safari or Firefox. That ground is measurable on this machine. Its
  LaunchServices settings
  (`~/Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist`) hand both
  `http` and `https` to `com.google.chrome`, so links open in Google Chrome. That is a Chromium-based
  browser, which NFR-13 supports and the end-to-end layer runs in. Safari is also installed, so the
  default browser is strong evidence of where the run-through happens, not proof. If the owner runs it
  in Safari, AC-1 would be checked in a browser nothing else tests. That is the one case that would
  tip this to an override adding WebKit to NFR-13 and NFR-11.
  The draft's reasoning otherwise holds. A browser the suite never runs is a support claim nobody
  checks, and one engine keeps the setup the reader runs small. Check 3 read this answer against item
  2.1. The browser the end-to-end layer drives is a dependency fetched at setup, which 2.1's answer
  permits and whose one-time network need it puts in FR-4's prerequisites.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SRS.md** — `<CORE>/launchers/skill/launcher.sh product-srs tracker17`
