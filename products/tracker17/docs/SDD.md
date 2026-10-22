# SDD — tracker17

**Status:** Settled
**Owner:** CTO — writes every part; the CPO and the CDO decide the parts the lane table names, through `SDD_open_issues.md` items carrying their `Seat:`
**Version:** 11 — the eighth answered round folded in (`products/tracker17/docs/trail/sdd/cycle-8.md`), two items the PM raised from the product's code and from the UXD and one a `companion-self-answer` run raised from § 11 read against the suite, all three answered in the CTO's seat. § 4 gains RT-11, the history-admission boundary: a page that shows a pending confirmation of a move to `cancelled` is answered 202 and every other move page 200, each with `Cache-Control: no-store`; § 9 TO-8 and § 11 R-12 surface the decision and its browser dependence, and RT-8's last sentence is scoped to a finished outcome. § 6 `status-moves`'s behaviour bar has the overtaken move name the moves the page now shows and offer no reload, and names the refusal reached by an address with no press; § 4 EX-4 says where that refusal sits; § 10 RC-4 records the UXD moving to version 8. § 11 R-2 counts the confirmation case verified, by four tests at `9b05680c7`, and § Open Questions keeps the assistive-technology case alone. RN-49 to RN-52 record the round. The header's *Inputs read* catches up with PRD version 7 and NFDR version 13, neither of which moves a line of this document (RN-52). Nothing is left open
**Inputs read:** PRD Settled (version 7) · SRS Settled (version 6) · UXD Settled (version 8; no `products/tracker17/docs/UXD_open_issues.md` beside it) · Agari no Status line (`agari_template.md` carries none) · tracker17 doctrine no Status line (stamped, unfilled) · writing_bar Settled · ADR-0001 to ADR-0009 Accepted and NFDR Settled (version 13, its header; `products/tracker17/docs/architecture_open_issues.md` is also present, opened on 2026-10-20 in the CTO's seat with its one item, § 2.1, unanswered) (downstream; read for the decisions already recorded, as the authoring lens says, never as a source) · FDR Settled (version 4; downstream, read to check what the answered round says does not move, not a source) · the product's code and tests the answered round cites (read to verify each citation on disk, not sources)

> The SDD is the technical **how**, and it ends in a **cut**. It states the architecture the rest of
> the system builds against — derived from the PRD (the *what and why*), the SRS (the system-level
> *what*) and the UXD (the experience) — and it then cuts that architecture into an ordered set of
> **slices, each of which delivers something on its own**. A slice is not itself a unit of work:
> the Principal PM draws one and cuts it into **one or more** 根回し Nemawashi seeds. § 8 states how
> a slice's fields land in them; how many seeds, when a slice is drawn, and what a seed's stations
> reach into are all `<CORE>/roles/loaders/principal_pm_global.md`'s.
>
> **The cut is the point of the document.** Part B states the method — the steps that turn a design
> into contained slices — and Part C is what those steps produce. A reader who needs to know how to
> plan opens § 5. A reader who needs to know what was planned opens § 6.
>
> It is a **living document**, updated in place with versioning: bump the Version line above on each
> material change. When the build contradicts the cut, § 10 records the contradiction before the cut
> is redrawn.

Every `PRD §`, `SRS` and `UXD` reference below is to `products/tracker17/docs/PRD.md`,
`products/tracker17/docs/SRS.md` and `products/tracker17/docs/UXD.md`. Paths to code are relative to
the product root, `products/tracker17/`.

**How to read the markers.** A statement marked *(confirmed: `trail/sdd/cycle-<N>.md` § n.n)* states
a call the upstream documents do not make. The CTO drafted it, and it was confirmed in the answered
round kept at `products/tracker17/docs/trail/sdd/cycle-<N>.md` at the item named. *Confirmed with an
addition* means the answer also added to the statement, and the statement as written here carries
that addition. *Overridden* means the answer replaced the drafted value, and the statement carries
the answer's value. The reasoning behind each answer is in the same folder:
`products/tracker17/docs/trail/sdd/self_answer-1.md` (cycle 1, item 2.1), `self_answer-2.md` (cycle 1,
items 2.2, 2.5, 3.1 and 3.2), `self_answer-3.md` (cycle 1, items 2.3 and 2.4), `self_answer-4.md`
(cycle 2, item 2.1), `self_answer-5.md` (cycle 3, items 5.1 to 5.3), `self_answer-6.md` (cycle 4,
item 5.1), `self_answer-7.md` (cycle 5, item 5.1), `self_answer-8.md` (cycle 6, item 5.1),
`self_answer-9.md` (cycle 7, item 5.1), `self_answer-10.md` (cycle 8, items 5.1 and 5.2) and
`self_answer-11.md` (cycle 8, item 2.1). The items of cycles 3 to 8 were raised by the PM, from the
product's code, from a run of the setup instructions on Linux, from a passing end-to-end test, in
cycles 6 and 7 from the product's code again and in cycle 8 from the product's code and from the
UXD, not drafted by the CTO, and were answered in the CTO's seat. Cycle 8's one item in § 2 was
raised by the run that answered its § 5 items, in the CTO's seat, from reading § 11 against the
suite. The Review Note named beside a marker says why this document reads as it does.

No statement in this document awaits an answer. `products/tracker17/docs/SDD_open_issues.md` does not
exist, and its absence is the done signal.

## Who decides what

The CTO writes every part of this document. The table below does not say who writes a part; it says
whose call the part is. A part the CPO or the CDO decides is still drafted by the CTO, best-effort,
from the inputs and any answers already in hand. A call that the inputs leave unsettled, or that the
draft needs that seat to confirm, reaches the document through an `SDD_open_issues.md` item carrying
`- **Seat:** cpo` or `- **Seat:** cdo`, and the answer is folded in on the skill's next round.

**The rule every row follows:** a part is decided by the seat that would have to be overruled for it
to be wrong. Where two seats would each be overruled about different clauses of one part, the part is
split by named clause and each clause names its seat. No part is shared — a shared row is an open
question in the shape of an answer.

| Part | Decided by |
|---|---|
| § 1 What this design must achieve | **CPO** |
| § 2 The shape, and what it was chosen over | **CTO** |
| § 3 The parts, and the seams between them | **CTO** |
| § 4 — runtime and deployment shape, instrumentation and failure visibility, identity, authorization, data protection | **CTO** |
| § 4 — the experience conditions the UXD binds on every surface | **CDO** |
| § 5 step 1 — the entries themselves | **CPO** |
| § 5 step 1 — that each entry is genuinely observable, not an architecture box | **CDO** |
| § 5 step 2 Strike the fragments | **CPO** |
| § 5 step 3 Separate dependency from preference | **CTO** |
| § 5 step 4 Size each one against a reached-when | **CPO** |
| § 5 step 5 Order by what each slice falsifies | **CTO** |
| § 6 *Slug*, *Delivers*, *Moves toward*, *Not in this slice* | **CPO** |
| § 6 *Rests on*, *Why here in the order* | **CTO** |
| § 6 *Reached when* — the behaviour observable in the running product | **CDO** |
| § 6 *Reached when* — the command and its result, and the artifact that must exist | **CTO** |
| § 6 *Traces to* — the PRD section | **CPO** |
| § 6 *Traces to* — the SRS `FR-n` / `NFR-n` / `DR-n` / `C-n` | **CTO** |
| § 6 *Traces to* — the UXD section | **CDO** |
| § 7 The order, and why | **CTO** |
| § 9 Trade-offs taken | **CTO** |
| § 10 Re-cut record | the seat whose ground moved — see below |
| § 11 Technical risks | **CTO** |
| § 12 — the PRD boundary | **CPO** |
| § 12 — the SRS boundary, and the downstream boundary | **CTO** |
| § 12 — the UXD boundary | **CDO** |
| *Open Questions* | **CTO** |

§ 8 is decided by nobody — it is left as written. *SDD Review Notes* names the seat whose call it was on every entry.

**§ 10 has no standing deciding seat, deliberately.** A re-cut is written when a cut meets a reality
that contradicts it, and the trigger says whose ground moved: a *Reached when* that cannot be met
belongs to whichever half failed; a slice that turned out to be a fragment is the CPO's, by § 5
step 2; no slice left that can be started is the CTO's, by step 3; an upstream change belongs to the
seat that owns that document. The CTO writes the record, and it names that seat as the one whose
call moved. A standing decider here would have one seat recording another's error as its own
verdict, which is how a correction stops being distinguishable from a drift.

**What each seat must not decide:** the CTO, whether a slice is worth delivering — that is product
value. The CPO, the architecture style, the data model and the seams. The CDO, product scope and the
technical order.

---

# Part A — What is being cut

## 1. What this design must achieve

tracker17 is a worked example: a small task tracker one person runs on their own machine and uses
in a desktop browser, so that a reader can run a whole product kensaiapp built, read it end to end,
and judge how simple it was to set up (PRD § Purpose). tracker17 is also kensaiapp's own testing
ground: building it with kensaiapp is how issues in kensaiapp are found and fixed, and a reader
learns both purposes from the first thing they read about tracker17 (PRD § Purpose; SRS § 1). The
second purpose adds no behaviour to the tracker (SRS RN-18) and no part to this design. It reaches
the product as one requirement on the setup instructions' opening paragraph, SRS FR-41, which
`first-project` carries (§ 6).

The design is scoped against the project's 上がり Agari, `system/projects/tracker17/agari.md`. Done
is the owner passing three bars on one run-through on their own machine: **Works**, **Simple to set
up** and **Simple to read**. The Agari places publishing and a re-check on later releases outside
done, and this design builds for neither.

Three things were fixed before any choice below was made, and each bounds the design:

- **The reader reads all of it.** The code and tests must be small and plain enough for the owner to
  judge them simple on a cold read, and one feature must be traceable from the definition documents
  to its code and tests without searching (PRD § Goals, "It is simple"; SRS NFR-9, NFR-10). Every
  part this design adds is a part the reader has to read.
- **Setup is at most three commands and ten minutes**, with no account, key or sign-up (PRD § Success
  Metrics, Simple to set up; SRS C-2, C-7).
- **One operator, one machine, nothing leaves it.** There is no hosting, no login and no outside
  service at run time (PRD § Out of Scope; SRS C-1, NFR-5, NFR-7).

The task rules are tracker16-X's wherever both products cover a rule, and its working code at
`task-tracker-X` is the preferred starting point (SRS C-5). The one exception is the priority set:
SRS FR-15 names four values, `low`, `medium`, `high` and `critical`, where tracker16-X has three
(SRS C-5; PRD § Core Features, Priorities).

## 2. The shape, and what it was chosen over

**The shape taken is a rule core behind server-rendered pages.** The task rules sit in one part
that touches no disk, no clock and no network. A thin layer of operator actions applies them to the
tracker's current state and saves the result. One outer part turns browser requests into those
actions and their results into whole HTML pages. One outer part reads and writes the saved data.
One module wires the four together. It is tracker16-X's own shape with its command-line part
replaced by a browser part.

**The forces the choice was weighed against**, each from this product's documents:

1. **Where change arrives.** The features built fresh are filtering, sorting, the project summary
   and title editing, and the PRD names them as where tracker17 is "most likely to drift from its
   predecessor's rules" (PRD § Risks). The interface is the other thing that moved: it was a
   command line in tracker16-X and is a browser here (SRS C-3). Change arrives in the list rules
   and at the interface, and nowhere else inside the Agari's horizon.
2. **What the system talks to.** One browser interface, the machine's disk and the machine's clock.
   There is no API and no outside service (SRS § 5.2, § 5.3). All three edges are stable, and
   tracker17 owns every contract.
3. **Judgment against plumbing.** The requirements hold a real body of rules: the status workflow
   (SRS FR-18), the overdue rule (FR-25), the assignee-list rules (FR-21, FR-22, FR-33), the filter,
   range and sort semantics (FR-32 to FR-36), the summary's counts and rows (FR-38) and the rules
   saved data must satisfy to be readable (DR-6). Several are used on more than one page: SRS AC-13
   requires that the "list marking, the overdue filter and the summary count agree". The rest of
   the product moves form fields to the saved data and back.
4. **What must be replaceable.** Two substitutions are exercised before the Agari. Tests replace the
   clock, because SRS AC-13 is checked with "today's date set by the test". Tests replace or
   interrupt the saved-data part, because AC-9 interrupts a save. A third is possible: SRS AC-15's
   timed run at 1,000 tasks with 20 comments each is the one measurement that could force a
   different way of saving. Nothing replaces the browser interface inside the horizon.
5. **What the numbers force at run time.** One operator and at most 1,000 tasks (SRS NFR-1, NFR-7)
   fit in one process and in memory. SRS NFR-3 requires every action to be "checked against the
   saved data at the moment it is applied", which is simplest when one process applies one action
   at a time. No number argues for more than one process.
6. **What a first slice could prove.** For this shape, one action carried from a page through the
   rules into the saved data and back after a restart exercises every part and every seam once.
   That slice is `first-project` in § 6.
7. **What being wrong costs.** Stated per row below, and in the closing paragraph.

| Shape | Right when | Wrong when | Taken? |
|---|---|---|---|
| **A rule core behind server-rendered pages**: rules in one part with no input or output, operator actions over it, a page part and a saved-data part outside, one module wiring them | The rules are shared across pages and must agree (force 3). The interface has already been replaced once while the rules carried over (force 1). Tests must replace the clock and the saved data (force 4). | The product is almost all plumbing, so the core guards nothing and the layers are files to read for no gain. | **yes** — AC-13's three-way agreement and the carried-over rules of SRS C-5 need one home, and the predecessor's code already has this shape |
| **One module per screen**, each reading the saved data, applying its rules inline and building its page | Each rule belongs to one screen, and nothing is carried over from a predecessor. It would win here if tracker17 had no shared rules: it is the fewest files to read. | A rule is used on several screens. Here the overdue rule appears on two lists, a filter and the summary (SRS FR-26, FR-35, FR-38), and the workflow appears on every row and on the task page (UXD UX-I1). Each copy can drift from the others. | no — force 3: the shared rules would be written several times, and the unit layer SRS NFR-11 requires would have no isolated logic to test |
| **A database at the centre**, with filtering, sorting and the summary written as queries and thin handlers around it | The data outgrows memory, more than one process writes, or queries are open-ended. It would win here at a hundred times NFR-1's volume or with a second operator. | The volume fits in memory and the query rules are the product's newest and least proven. Here FR-34 and FR-36 carry confirmed edge cases, such as undated tasks sorting last in either direction, that would live in query text where a unit test cannot isolate them. | no — forces 1 and 5: the rules most likely to change would be the hardest to test, and SRS NFR-7 names one operator |
| **An application in the browser** over a local data interface | Pages must change without a reload: live updates, drag and drop, work offline. It would win here if the UXD asked for any of them. | Pages do not update themselves and each appears whole (UXD UX-I8, UX-I9), and the product exposes no programmatic interface (SRS § 5.2). It adds a second language, a second state to keep in step, and an interface between them. | no — force 2 and § 1: every one of those is a part the reader has to read, and no UXD entry needs them |

**Where this product falls.** tracker17 has few edges and they are stable, which argues against
insulation. It also has shared rules, a predecessor whose rule code is to be reused, and tests that
must replace the clock and the saved data. The shape taken keeps exactly the insulation those three
facts pay for, and no more: there is one contract toward the saved data and one toward the clock.

**What undoing it would take.** Folding the parts together is cheap. The rule core has no
dependency on any other part, so `application` or `web` could absorb it by moving files. The
expensive direction is the one this choice avoids: pulling shared rules back out of page modules
after they have drifted apart. One choice inside the shape is less cheap to reverse, and it is how
the saved data is written. § 9 TO-3 states that cost.

## 3. The parts, and the seams between them

**The parts.**

| Part | Lives in | Owns | Must not own |
|---|---|---|---|
| `domain` | | The rule core, as the directory `domain/` at the product root. It holds the entities, the tracker state as one value, every rule that accepts or refuses a change, the overdue rule, the filter, sort and summary computations, and one typed refusal per refused condition. Every function takes what it needs as arguments and returns a new value. | Any input or output: no file, no clock, no network, no HTML. Any import of another part. Any wording shown to the operator. |
| `application` | | The operator's actions, as the directory `application/`. It holds the tracker's current state while the tracker runs. Each action is one call that applies a `domain` rule to the current state. Where the rule's outcome reports a change, the action saves the new state and only then makes it current. Where the outcome reports none, the action returns the current state and saves nothing, and the current state stays as it was. Which outcomes report none is `domain`'s, decided per action and read off the outcome. What the report compares is `domain`'s, decided per action. The task edit compares each value submitted with the value the page showed (§ 4 RT-7), because its form is the one that carries those values, so a field changed to the value another tab already saved reports a change and saves a state equal to the current one. Setting the operator name, and adding a label, compare the value submitted with what the state holds at the moment of the action, the saved name and the labels the task carries, which is SRS NFR-3's rule for every action the task edit excepts, so a name or a label submitted equal to what another tab already saved reports no change and saves nothing. `application` compares nothing in either case. It also answers what a page needs to show. It states the two contracts it depends on: one for saving and one for the clock. *(confirmed with an addition: `trail/sdd/cycle-6.md` § 5.1 and `trail/sdd/cycle-7.md` § 5.1; why, RN-45, RN-47)* | Any rule of its own: it never decides whether a change is allowed. Any HTML or request detail. Any knowledge of how or where the state is saved. Any import of `web` or `persistence`. |
| `persistence` | | The saved data, as the directory `persistence/`. It owns where the file is, its format, reading it once at start, writing it whole and atomically, and the lock that lets one running tracker use a location. | Any data rule: it builds the state through `domain`'s constructors and reports their refusal as unreadable data. Any decision about what happens when data is unreadable. Any import of `application` or `web`. |
| `web` | | The browser interface, as the directory `web/`. It owns listening on the loopback address, the check every request passes first, the addresses of pages and actions, reading form fields, calling one `application` action per request, and building each whole HTML page and the one stylesheet. | Any rule: it never works out which moves are allowed, whether a task is overdue, or what a count is. It shows what `application` returns. Any access to the saved data or the clock. Any state kept between requests. |
| `main` | | The composition root, as `main.py` at the product root. It is the start command. It builds the other four parts with the address, the saved-data location and the real clock, chooses between the normal tracker and the page for unreadable data, and writes the start messages to the console. | Any rule, page or file format. It is the only module that names a concrete `persistence` or `web` class. |

**The units.** One row per *distinct* value in `Lives in` above — no more, no fewer.

| Unit | Language | Kind |
|---|---|---|
| | `Python` | `package` |

Every part sits at the product root, so `Lives in` is empty on every row and the one unit is the
product root itself. Its language frame places `main.py`, `errors.py`, `pyproject.toml` and `tests/`
there. `errors.py` holds the single base error that every typed error in every part derives from.
No part owns more of that file than its own subclasses.

**The seams.** Each names what crosses and which side owns the contract.

| Seam | What crosses | Owner of the contract |
|---|---|---|
| `SM-1` `web` ↔ `application` | Inward: one call per operator action, carrying plain values read from the form and the address. Outward: the result, or a typed refusal, and the plain values a page shows. No HTML and no request object crosses. | `application` |
| `SM-2` `application` ↔ `domain` | Inward: the current state, the action's values, and the current date or instant where a rule needs one. Outward: a new state, a computed list or summary, or a typed refusal. | `domain` |
| `SM-3` `application` ↔ `persistence` | Inward: the whole state, to be saved. Outward: confirmation that it is saved, or a failure. `application` states the contract and `persistence` satisfies it without inheriting from it. | `application` |
| `SM-4` `persistence` ↔ `domain` | `persistence` hands stored values to `domain`'s constructors and receives entities and a state, or a typed refusal naming the broken rule. | `domain` |
| `SM-5` `main` ↔ `persistence` | Inward: the saved-data location. Outward: the state read at start, or one of three signals: no saved data yet, saved data unreadable, or another tracker already running on that location. | `persistence` |
| `SM-6` `main` ↔ `web` | Inward: the address to listen on, and either the `application` object or the fact that the saved data is unreadable together with its location. Outward: a running listener, or the signal that the address is taken. | `web` |
| `SM-7` `main` ↔ `application` | Inward: the starting state, the object that saves, and the clock. | `application` |

**The direction of dependence.** `web` imports `application`. `application` imports `domain`.
`persistence` imports `domain`. `main` imports all four. `domain` imports no other part, and no part
imports `main`. Every part may import `errors.py`.

**What the system holds.** The whole of what tracker17 keeps is one value, the *tracker state*,
made of the five things SRS § 6 names:

- **Project** (SRS DR-1): an identity, a name unique among projects and compared exactly, and an
  optional description. The identity is this design's addition. It is a number that is never
  reused, and it gives a project an address that survives a rename (UXD § 4, "Every page has its
  own address").
- **Task** (DR-2): an identity, the identity of its project, a title, a status, a priority, an
  assignee name or none, its labels, a due date or none, the instant it was created, and its
  comments in the order they were written. One number carries two of DR-2's fields. Task identities
  come from a counter in the state that only rises, so an identity is unique across all projects,
  is never reused after a deletion, and the order of identities is the order of creation that SRS
  FR-15 requires independently of the recorded time.
- **Comment** (DR-3): its text, the author name as it stood when written, and the instant it was
  written. A comment is held inside its task and is never changed.
- **Assignee list** (DR-4): the names, each unique and compared exactly, in the order added.
- **Operator name** (DR-5): one name, or none.

The two counters that issue identities are part of the state, because a deleted task's identity
must stay retired across a restart. An instant is stored as a point in universal time and shown in
the machine's local time (SRS NFR-14). A due date is stored as a calendar date with no time
(FR-24). Deleting a project removes its tasks, and removing a task removes its comments, in the one
change of state (FR-13, FR-17).

## 4. What every slice inherits

Each condition below binds every slice in § 6. Each names the requirement it serves, and each is
written so that a slice breaking it could be named.

### The runtime and how it is started — CTO

- **RT-1: The tracker runs on Python 3.11 or later and imports nothing outside the Python standard
  library.** A part that imports a third-party package breaks this condition. The tracker needs
  Python and nothing else to run, and it needs no network connection at any point, setup included.
  The one-time network connection that SRS FR-4 and UXD UX-S1 list among the prerequisites is
  needed only to set up the test suite (RT-4). `pyproject.toml` declares the floor. A `python3`
  older than 3.11 is a missing prerequisite, and UXD UX-F1 gives that failure to the setup
  instructions: their prerequisites section names the command that shows the version and says what
  to do when the version is lower. *(serves SRS C-2, C-7, NFR-10; the SRS names no runtime and
  leaves it to this document, SRS RN-23)* *(confirmed with an addition: `trail/sdd/cycle-1.md`
  § 2.1; why, RN-3, RN-18)*
- **RT-2: One command starts the tracker.** From the product root it is `python3 main.py`, and it
  takes no argument. Together with moving into the copy, setup is two commands. *(serves SRS FR-1,
  C-7; UXD UX-S2, "the command takes no input")* *(confirmed: `trail/sdd/cycle-1.md` § 2.1)*
- **RT-3: The tracker runs on macOS and Linux, and Windows is not supported.** Only macOS is
  checked: the owner's machine is macOS, and nothing in the Agari's check runs the tracker or its
  suite on Linux (§ 11 R-9). Linux stays named because the tracker needs no code of its own for it.
  The tracker runs on any Linux with Python 3.11 or later. The end-to-end suite runs on fewer Linux
  systems than the tracker, and RT-4 says which. Nothing is built or tested for Windows. An
  unsupported operating system is a missing prerequisite, and UXD UX-F1 gives that failure to the
  setup instructions: their prerequisites section names macOS and Linux, says the tracker has been
  checked on macOS only, and says Windows is not supported. The tracker itself checks no operating
  system and carries no message for one.
  *(serves SRS FR-4, the prerequisites)* *(confirmed with an addition: `trail/sdd/cycle-1.md`
  § 2.2; why, RN-11, RN-19; the suite's narrower bound on Linux, `trail/sdd/cycle-4.md` § 5.1; why,
  RN-38)*
- **RT-4: Only the tests have dependencies, and each is fixed to an exact version.** They are
  declared in `pyproject.toml` and locked, with every dependency they pull in, in one committed
  file. They are installed with the installer that ships with Python, into a virtual environment
  made with Python's own `venv` module. Setting up the suite is the one step that needs a network
  connection, once, to fetch the test dependencies and the browser the end-to-end tests drive. The
  end-to-end layer drives Chromium. On Linux that browser needs system libraries the operating
  system does not ship by default, and the same one-time step fetches them: the instructions'
  section on running the suite gives, for Linux, `python -m playwright install --with-deps chromium`
  in place of `python -m playwright install chromium`, says that the command runs the distribution's
  package manager and asks for administrator rights, and says that the tracker and `pytest tests/`
  need none of this. On Linux the end-to-end suite runs where the pinned browser-driving library
  does. For the pin in `tests/requirements.txt`, `playwright==1.63.0`, that library's documentation
  lists "Debian 12 / 13, Ubuntu 22.04 / 24.04 / 26.04 (x86-64 or arm64)"
  (https://playwright.dev/python/docs/intro, "System requirements", read 2026-10-08), and the
  instructions carry that list. On another Linux the tracker and `pytest tests/` run, and `pytest
  tests/e2e/` is a missing prerequisite. The list is the pin's and moves only when the pin does
  (SRS C-8). The system libraries are the operating system's, as Python is, and are not declared
  dependencies under C-8, so nothing pins them. No module outside `tests/` imports a test
  dependency. *(serves SRS C-8, NFR-11, NFR-13, FR-4)* *(confirmed with an addition:
  `trail/sdd/cycle-1.md` § 2.1; why, RN-18; the Linux step and bound, `trail/sdd/cycle-4.md` § 5.1;
  why, RN-38)*
- **RT-5: The tracker listens on one loopback address and on no other.** The address is
  `127.0.0.1:8017`, fixed in one constant, `ADDRESS` in `main.py`. `main` passes it to `web`, so a
  test can start a tracker on another port. *(serves SRS FR-2, FR-3)* *(confirmed with an addition:
  `trail/sdd/cycle-3.md` § 5.2; why, RN-35)*
- **RT-6: The tracker applies one request at a time.** A single lock is held from the moment a
  request's check begins until its result is saved, so no two actions interleave. Connections are
  still accepted while one is being served (§ 11 R-4). *(serves SRS NFR-3)*
- **RT-7: The tracker keeps nothing between requests except the tracker state.** There is no
  cookie and no session. What a page shows is a function of the tracker state and the page's
  address. A form whose save must tell a field the operator changed from a field left as the page
  showed it carries the values the page showed, in the form itself, because this condition leaves
  nowhere else to hold them. The task's edit form is that form: a field counts as changed when the
  value submitted for it differs from the value the page showed, so a save writes only the fields
  the operator changed, and an assignee left as the page showed it is never refused for being off
  the list (SRS NFR-3, "for that field"; UXD UX-F9). *(serves SRS NFR-3, NFR-6; UXD UX-I7, UX-F9)*
  *(why, RN-32)*
- **RT-8: Only a form submission changes the tracker state.** Following a link or reloading a page
  never does. Every submission is answered by sending the browser to a page address, so reload,
  back and forward never repeat an action. What that page says about the action travels in the
  address and nowhere else, as RT-7 requires: the place the page opens at, what a completion line
  names, and, after a refusal or a failure, the reason and what was typed. One refusal is the
  exception. After `domain` refuses a value as longer than its field's maximum (RT-10), the address
  carries the reason and the place and nothing that was typed, because that text is what an address
  cannot hold. No form of the tracker's own can reach that refusal, so UXD UX-I3's "Everything the
  operator typed stays in the form" holds on every form. One function in `web` builds every such
  address. A reload of that page, or a return to it through back, shows the same line at the same
  place when the address names a finished outcome: a completion line, a refusal or a failure. A
  page whose address asks for a pending step is built from the saved state on every load (RT-7)
  and shows what the state now allows, which RT-11 and UXD UX-F4 state. *(serves SRS NFR-4; UXD
  § 4, "the browser's back, forward and reload buttons work on every one"; UXD UX-I3, UX-I4)*
  *(why, RN-21, RN-24, RN-25; the scope, `trail/sdd/cycle-8.md` § 5.1; why, RN-49)*
- **RT-9: A page that opens at the place of an action sets keyboard focus there with the HTML
  `autofocus` attribute, and its address carries no fragment.** The HTML standard says the
  attribute "applies to all elements, not just to form controls", and its steps skip a document
  that "has non-null target element", which is the case when the address ends in a fragment naming
  an element (https://html.spec.whatwg.org/multipage/interaction.html, "The autofocus attribute").
  An element at the place that is not a control takes focus without becoming a stop in the Tab
  order. § 11 R-2 covers the browser not doing what the standard describes. *(serves UXD UX-I2,
  UX-I6; § 4 EX-4 to EX-6, EX-14)* *(why, RN-21)*
- **RT-10: Every text field has a maximum length, and a value the field let in is never refused as
  too long.** A project name, a task title, an assignee name, the operator's name and a label take
  at most 200 characters. A project description and a comment take at most 4,000. `domain` refuses
  a longer value with a typed refusal, and no part ever shortens a value to make it fit. The two
  lengths are stated once, in `domain`, and `web` receives them through `application` to write each
  field's `maxlength` attribute, so the field and the rule cannot disagree about the number. The
  two fields that state the most characters they hold beside the field, the project description
  and the comment, write that number from the same value, so the sentence cannot disagree with
  either (UXD UX-F2, UX-F7; why, RN-32). One character is one Unicode code point, counted on the
  value as it would be saved, spaces included. The field's own count is never the looser one. The HTML standard measures `maxlength` in code
  units: "The number of characters is measured using length and, in the case of textarea elements,
  with all newlines normalized to a single character (as opposed to CRLF pairs)"
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Limiting user input
  length: the `maxlength` attribute"), where a string's length "is the number of code units it
  contains" (https://infra.spec.whatwg.org/). A code point is one code unit or two, so a character
  outside the Basic Multilingual Plane counts two in the field and one in the rule, and such a field
  can stop before the stated number without anything it let in being refused. A line break is the
  one case where the browser sends more than the field counted: the field counts it as one
  character, and a form submission sends it as the two characters CR LF
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Converting an entry
  list to a list of name-value pairs"). `web` therefore turns every line break in a submitted value
  back into the single line-feed character the field counted, as the Infra standard's *normalize
  newlines* does ("replace every U+000D CR U+000A LF code point pair with a single U+000A LF code
  point, and then replace every remaining U+000D CR code point with a U+000A LF code point",
  https://infra.spec.whatwg.org/), before the value reaches `application`. No part changes a typed
  value in any other way between the field and the rule. A slice that adds a text field writes the
  field's `maxlength` and adds a test that a longer value is refused. The bound exists because of
  RT-8: typed text travels in an address, and the listener refuses an address it cannot read (§ 11
  R-10). A code point takes at most four bytes in UTF-8 and each byte takes three in an address, so
  a character takes at most 12 bytes, and the longest form, a project's name and description
  together, stays under 51,000 bytes of the 65,536 the listener accepts. *(serves SRS FR-40, FR-39,
  DR-6; UXD UX-I3)* *(confirmed with an addition: `trail/sdd/cycle-2.md` § 2.1; why, RN-22, RN-24,
  RN-25)*
- **RT-11: A page that shows a pending confirmation of a move to `cancelled` is answered with HTTP
  status 202, and every other page a move's interaction or outcome lands on with 200; each of them,
  the confirmation included, carries `Cache-Control: no-store`.** The status is read off the page as
  built, after outcome precedence, task membership and the workflow's answer against the saved state
  (`web/routes.py`, `Site._pending_status` and `_move_view`), so an address that asks for a
  confirmation the page does not show is 200, and one naming a task no task holds is 404. The 202 is
  the history-admission boundary: the pinned browser admits only a main document answered 200 to
  its back/forward cache, so a return to a confirmation's address through Back or Forward is loaded
  afresh from the saved status and, once the task is in a final status, shows UXD UX-F4's no-press
  refusal and never a stale confirmation. `no-store` serves a separate purpose: it keeps the HTTP
  cache from reusing a move's interaction or outcome page, and does not by itself keep a page out of
  the browser's history cache. The meaning taken for 202 is the standard's, a request accepted for
  processing that is not complete, here a move intent awaiting the operator's confirmation; the GET
  schedules, saves and records nothing (RT-8), and no page script, cookie or session is used (RT-7;
  ADR-0003, ADR-0006). The earlier `Clear-Site-Data: "cache"` header on the confirming redirect was
  measured not to evict the page from the pinned browser's history cache and is gone
  (`tests/integration/test_routes.py` asserts its absence). The dependence is exact: Chromium admits
  a main document to its back/forward cache only when its status is exactly 200, not any 2xx
  (`content/browser/back_forward_cache/back_forward_cache_impl.cc`,
  `PopulateReasonsForMainDocument`, `if (rfh->last_http_status_code() != net::HTTP_OK)`, read at
  the source on 2026-10-20), and 202 is not among the status codes the HTTP standard lets a cache
  store heuristically (RFC 9110 § 15.1 lists 200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414
  and 501), so the HTTP cache cannot keep the confirmation even without the header, and `no-store`
  is what protects the 200 outcome pages. Chrome's own documentation says a `no-store` page can be
  restored from the history cache and is evicted on a cookie change (developer.chrome.com,
  "bfcache-ccns", read 2026-10-20), which is why the header alone was not enough. The rule is
  stated as the pinned browser's, as RT-9 and § 11 R-2 state `autofocus`, and SRS NFR-13 bounds the
  product to Chromium-based browsers; § 11 R-12 covers a release that changes it. One case is named
  and left where it occurs: a confirmation address whose task another tab has deleted answers the
  not-found page, 404, with no `no-store` (`web/routes.py`, the `task_not_found_page` answers on
  the task's page and on a project's Tasks view); the same exact-200 rule keeps it out of the
  history cache, and whether the HTTP cache may keep a 404 heuristically is `delete-and-rename`'s,
  where a task first becomes deletable. Tests: `tests/integration/test_routes.py`,
  `test_pending_confirmation_response_matches_the_rendered_page`,
  `test_non_confirmation_move_views_keep_their_response_contract` and
  `test_move_interaction_and_outcome_pages_are_not_stored`; `tests/e2e/test_moves.py`,
  `test_history_matrix_revalidates_current_saved_status` and
  `test_real_history_traversal_revalidates_the_confirmation`; 67 passed in `tests/e2e/` in a
  fresh clone at `9b05680c7`. *(serves SRS NFR-3, NFR-4, NFR-13; UXD § 4, "the browser's back,
  forward and reload buttons work on every one"; UX-F4, UX-I3; § 4 RT-7, RT-8, EX-2, EX-6, SEC-3;
  § 9 TO-2)* *(confirmed with an addition: `trail/sdd/cycle-8.md` § 5.1; why, RN-49)*

### The saved data — CTO

- **SD-1: The saved data is read once, at start, and never again while the tracker runs.** *(serves
  SRS DR-6, "At start")*
- **SD-2: An action is reported done only after the whole new state is on disk.** `application`
  saves first and makes the new state current second. If the save fails, the current state is the
  old one and the action is reported as failed. *(serves SRS FR-9, NFR-8)*
- **SD-3: A save replaces the saved data in one step.** The new state is written to a second file in
  the same directory, forced to disk, and renamed over the old one. No other code path writes the
  saved data. *(serves SRS NFR-2)*
- **SD-4: Saved data that could not be read is never written, replaced or deleted.** *(serves SRS
  FR-8)*
- **SD-5: A data rule is enforced where the state is built.** Reading the saved data builds the
  state through the same `domain` constructors every action uses, so every rule a slice adds is
  also a check at start. A slice that adds a data rule adds a test that saved data breaking the
  rule is reported as unreadable. *(serves SRS DR-6)*
- **SD-6: The saved data is one file in `data/` under the product root.** The location is worked out
  from where the code is, never from the directory the command was run in. Version control ignores
  `data/`. The file holds the tracker state and nothing else. *(serves SRS FR-6, NFR-6)*

### What is instrumented, and what makes a failure visible — CTO

- **OB-1: The tracker writes to the console it was started from, and to nowhere else.** It keeps no
  log file and no record of requests. *(serves SRS NFR-6, NFR-8)*
- **OB-2: At start the console shows the address to open and the saved-data location, and nothing
  before them.** A start the tracker itself refuses shows one plain message and writes nothing to
  the saved data. The condition does not reach a `python3` too old to run the tracker, which RT-1
  gives to the setup instructions. *(serves SRS FR-1, FR-3, NFR-8; UXD UX-S2)* *(confirmed with an
  addition: `trail/sdd/cycle-1.md` § 2.1; why, RN-18)*
- **OB-3: A failure that is not a refusal is caught in one place in `web`.** That place writes the
  action and the error to the console, and answers with the page that says the action did not
  happen. No error text from the language reaches a page. *(serves SRS NFR-8; UXD UX-I5)*
- **OB-4: A refusal is a typed error, one type per refused condition, raised by `domain`.** `web`
  maps the type to its reason. No part tells one refusal from another by reading a message. *(serves
  SRS FR-39)*

### Identity, authorization and data protection — CTO

- **SEC-1: There is no identity and no permission check, because there is one operator.** No part
  adds a user, a role or a login. *(serves SRS C-1, NFR-7)*
- **SEC-2: Every request passes one check before any other code in `web` runs.** The check refuses
  a request that does not name the tracker's own address as its host. It refuses every request the
  browser marks `Sec-Fetch-Site: cross-site` or `same-site`, and it refuses a form submission the
  browser does not mark `same-origin`, a submission with no mark included. A refused request
  changes nothing. A request the operator starts from the address bar or a bookmark is marked
  `none`, so a page opens on it and a submission does not. A test that sends `web` a submission
  without a browser, the integration layer of TS-1 and `tests/timed_run.py` of TS-5, marks it
  `same-origin`, or the check refuses it. SRS AC-10's tests send one request under each refused
  mark and one submission with no mark, and each is refused with the saved data unchanged.
  *(serves SRS NFR-4)* *(changed; why, RN-28)*
- **SEC-3: No part opens an outbound connection, and no page refers to an address outside the
  tracker.** Every page is served with a policy that tells the browser to load only from the
  tracker's own address, to run no script, and to show the page inside no frame
  (`frame-ancestors 'none'`). The policy travels as a response header on every response, never as a
  tag in the page. An integration test of TS-1 reads the directive from the header of every page.
  *(serves SRS NFR-5, NFR-4)* *(changed; why, RN-28)*
- **SEC-4: Text the operator typed is shown as text.** One function in `web` puts a value into a
  page, and it escapes every value it is given. No page builds HTML from a typed value any other
  way. *(serves SRS FR-23, "stored exactly as typed"; § 11 R-3)*

### Tests and the trace — CTO

- **TS-1: Every slice is built test-first and leaves all three layers passing.** Unit tests cover
  `domain` with no file and no clock. Integration tests cover `persistence` against real files, and
  `web` with `application` in one process with no socket. End-to-end tests, under `tests/e2e/`,
  drive Chromium against a tracker started by `main` on a location and a port of the test's own.
  *(serves SRS C-6, NFR-11)*
- **TS-2: A test hands a part its collaborators and never patches a name inside it.** The clock and
  the object that saves are passed in, which is how SRS AC-13 sets today's date. *(serves SRS
  NFR-11)*
- **TS-3: Each Core Feature has one entry point in the code, named in the table below.** The entry
  point is the module `domain/<feature word>.py`. Its opening docstring names the SRS requirements
  the module realizes, every module in `application` and `web` that takes part in the feature, and
  the test modules that check it. Every test module names the requirements or acceptance criteria
  it checks. *(serves SRS NFR-9)*
- **TS-4: A test checks the pointers.** It fails when a path named in a docstring does not exist,
  when a requirement identifier named there is not in `products/tracker17/docs/SRS.md`, when a
  feature word in the table below whose slice has landed has no module, or when a feature word in
  the table has its module but is not listed as landed. Each slice that delivers a feature adds its
  word to the test. *(serves SRS NFR-9)* *(confirmed with an addition: `trail/sdd/cycle-3.md`
  § 5.1; why, RN-34)*
- **TS-5: A timed run covers every action SRS NFR-1 lists that exists so far.** `python3
  tests/timed_run.py` builds NFR-1's volume in a location of its own and times each action through
  `web`. It states the text lengths it uses, which are ordinary lengths and not RT-10's maximums. A
  slice that adds a listed action adds it to the run. *(serves SRS NFR-1, AC-15)*

| PRD Core Feature | Feature word | SRS requirements |
|---|---|---|
| Projects | `projects` | FR-10 to FR-14, FR-40 |
| Tasks | `tasks` | FR-15 to FR-17, FR-40 |
| Status workflow | `workflow` | FR-18, FR-19 |
| Priorities | `priorities` | FR-15, FR-16, FR-36 |
| Assignees | `assignees` | FR-20 to FR-22, FR-33, FR-40 |
| Labels | `labels` | FR-23, FR-40 |
| Due dates | `due_dates` | FR-24 to FR-26 |
| Comments | `comments` | FR-27 to FR-30, FR-40 |
| Filtering | `filtering` | FR-31 to FR-35 |
| Sorting | `sorting` | FR-36 |
| Project summary | `summary` | FR-38 |

A reader tracing a feature goes from its PRD Core Feature to the SRS section of the same name, from
there to this table, and from the table to `domain/<feature word>.py`, whose docstring names the
rest. The twelfth Core Feature, "Tested throughout", is not one the operator uses and has no row.
FR-40 sits on five rows because five features take text. The lengths and the check against them
live once in `domain` (RT-10), and each of the five modules points at that place.

### The experience conditions — CDO

Each condition restates a UXD entry as something a slice could break. The UXD entry is the source,
and where the two differ the UXD is right. EX-4, EX-5, EX-6 and EX-14 say how four UXD entries hold
when every action is answered by a whole page. Where a test shows that a page with no script cannot
hold them, those conditions stand and § 11 R-2's fallback applies (`trail/sdd/cycle-1.md` § 2.3).

- **EX-1: A page is built whole by the tracker and arrives whole.** No page shows partial content,
  a placeholder or a spinner, and no page changes after it has loaded. *(UXD UX-I8, UX-I9)*
- **EX-2: No page runs a script.** Every interaction is a link or a form submission answered by a
  whole page. *(UXD § 1 Design Read; § 9, the direction)* *(confirmed: `trail/sdd/cycle-1.md`
  § 2.3; why, RN-12, RN-20)*
- **EX-3: Every page has its own address.** A list's filter and sort choices are in its address and
  are stored nowhere else. *(UXD § 4; UX-I7)*
- **EX-4: A refusal changes nothing, shows its reason beside the control that was used, and keeps
  what was typed.** A rule is checked when the form is submitted and never while the operator
  types. The page that answers a refused or failed submission opens at the control that was used:
  the control is in view, keyboard focus is on it, and the reason is beside it. A refusal reached by
  an address and no control sits beside the task's status (UXD UX-I3), so a reader building the
  no-press case does not look for a control that was not used. *(UXD UX-I3; UX-I5; UX-A3)*
  *(overridden: `trail/sdd/cycle-1.md` § 2.3; why, RN-20; the no-press sentence:
  `trail/sdd/cycle-8.md` § 5.2; why, RN-50)*
- **EX-5: A completed action shows one line naming what changed, on the page it leaves the operator
  on.** When that page is the page the form was on, it opens at the thing acted on and not at its
  top. The thing is in view and keyboard focus is on it, so the next Tab goes on from there. When
  the thing acted on is no longer on the page, the page opens at the top of the sheet the thing
  was on, where the completion line sits. A page reached by a link, and a different page that an
  action lands on, open at their start. *(UXD UX-I4; UX-F4, "the operator stays where they were")*
  *(overridden: `trail/sdd/cycle-1.md` § 2.3; why, RN-20)*
- **EX-6: Deleting a project, deleting a task and moving a task to `cancelled` are confirmed in
  place, as UXD UX-I2 lays out, and the confirmation is its own page load.** The first press opens
  the same page with the confirmation in the first button's place, in view, with keyboard focus on
  its sentence. A double press on the first button never confirms, on a short page and on a list
  scrolled part-way. Backing out opens the page again with keyboard focus on the restored button.
  A first press for an action the page would no longer offer shows no confirmation. It is refused
  under UX-I3, or it shows UX-S10 when its target is gone. *(UXD UX-I2)* *(confirmed with an
  addition: `trail/sdd/cycle-1.md` § 2.3; why, RN-20)*
- **EX-7: A task's status is changed only by pressing one of the moves offered for it.** The moves
  offered are the ones `domain` returns for the task's current status. *(UXD UX-I1)*
- **EX-8: Every action can be done with the keyboard alone, using the browser's own keys.** The
  tracker adds no shortcut. Every control shows when it has focus. *(UXD UX-I6; UX-A1; UX-A2)*
- **EX-9: Every page meets WCAG 2.2 Level AA as UXD § 8 states it.** Every field has a label, every
  page a title and the page language. Status, priority and overdue are written in text. Every
  pointer target meets UX-A6's floor, and every page outside the task tables reflows as UX-A7
  requires. *(UXD UX-A3 to UX-A7)*
- **EX-10: One stylesheet, written for this product, styles every page.** No component library, no
  second colour mode, and nothing fetched from outside the machine. The values are
  `products/tracker17/docs/DESIGN.md`'s. *(UXD § 9)*
- **EX-11: Every word a page or the console shows is written to
  `products/tracker17/docs/CONTENT.md`.** *(UXD UX-I2, "the word itself is `CONTENT.md`'s")*
- **EX-12: One header with the areas that exist so far sits on every page but one.** The page for
  saved data that cannot be read carries no header and no navigation. Until the slice that delivers
  a control or an area, no page shows it, links to it, or carries words that point to it. The same
  holds for the setup instructions, which describe the tracker as it stands after each slice. No
  page shows anything that reads as an account. *(UXD § 3; § 4; UX-S9; UX-I8)* *(confirmed with an
  addition: `trail/sdd/cycle-1.md` § 2.4; why, RN-14)*
- **EX-13: An address for a project or task that does not exist shows the not-found page.** *(UXD
  UX-S10)*
- **EX-14: No completion line and no refusal takes keyboard focus.** The line is the accessible
  description of the element the page opens on, so assistive technology reads the line when the
  page opens. That is how UXD UX-A5's "announced to assistive technology without moving focus"
  holds on a page load. *(UXD UX-A5; UX-I3; UX-I4)* *(overridden: `trail/sdd/cycle-1.md` § 2.3;
  why, RN-20)*

---

# Part B — How to cut it

## 5. The cut, step by step

This section is the method. It is written once, here, so that § 6 carries slices and no method.
tracker17's cut does not depart from it.

### Step 1 — List what becomes observably different

Before any slicing, list the things that would be **observably different** about the running product
between where it is now and its Agari. Write each as one sentence in the form *after this, <someone>
can <do something they could not>*.

The list is made from behaviour, never from the architecture's boxes. "Set up the database", "build
the API layer" and "add the design system" are parts of the shape, not entries on this list. If an
entry cannot be finished in that sentence form, it is not yet a candidate.

### Step 2 — Strike the fragments

Strike every entry whose only value is that a later entry needs it, and fold it into the entry that
gives it value. A cut that needs a later cut to be worth anything is not a slice but a fragment of
one — `<CORE>/roles/loaders/principal_pm_global.md` owns that rule, and this step is where it is
applied to a design rather than to a program.

This is the step that catches infrastructure built ahead of its subject. A checker with nothing to
check is not a step forward, however finished it looks.

### Step 3 — Separate dependency from preference

For every remaining pair, ask **can the later one be built at all without the earlier one?** — not
whether building it first would be tidier. A stated order is often a preference wearing a
dependency's clothes, and the two behave differently the moment the build slips: a real dependency
blocks, a preference reorders for free.

Record each answer as a typed edge in § 7, with the reason on the same row. An edge with no reason
is a preference that has been written down as a fact.

### Step 4 — Size each one against a reached-when

A slice is the right size when someone who **did not build it** can check it is finished from the
outside. Write the *Reached when* before deciding the slice is settled — the size follows the
checkable bar, not the other way round.

- **Too broad** when a plausible intermediate result could change the slice's direction or its
  acceptance. Two answers are hiding inside one slice.
- **Too narrow** when its result cannot change what happens next. Nothing is learned by finishing
  it, so it is a task inside a slice rather than a slice.

Cut where the decision changes, not where the size is convenient.

### Step 5 — Order by what each slice falsifies

**The first slice is the smallest reversible one that proves the shape** — not the foundation the
rest will need. A first slice sized to the whole architecture cannot be wrong cheaply, and being
wrong cheaply is the one thing a first slice is for.

After the first, every slice's place in the order carries a reason: what an earlier slice must have
settled for it, or what it de-risks for the later ones. A slice that could sit anywhere in the order
says so plainly; a number is not a reason.

### The four tests one slice passes

1. **It delivers something observable.** After it, something works that did not work before, and a
   person can watch it happen.
2. **Its inputs already exist when it starts.** Nothing it needs is still being built beside it.
3. **It states what it does not include** — the adjacent work a reader would assume is inside, and
   the slice that owns that instead.
4. **Its place in the order is a reason**, not a number.

### Six cuts that look like slices and are not

- **A dependency stated as an ordering preference** — a fact and a habit are not the same thing.
- **A slice whose only value is that a later slice needs it.**
- **A slice no Agari claims.**
- **A slice no project would own any of** — which project owns which seed is settled at the cut,
  not here, and a slice may well split across two.
- **A milestone that only restates its last task's completion.**
- **A slice whose completion evidence is that someone kept watching.** Observation is not delivery;
  a poll that reports no change keeps a plan alive without advancing it
  (`huangruiteng/loopx`, `skills/loopx-pr-program/SKILL.md`: "Quiet monitor polls keep liveness but
  do not count as delivery progress").

---

# Part C — The cut

## 6. The slices

In every block, the behaviour lines of *Reached when* and the UXD entries of *Traces to* are the
CDO's clauses *(confirmed with an addition: `trail/sdd/cycle-1.md` § 2.4; why, RN-14)*. *Slug*,
*Delivers*, *Moves toward*, *Not in this slice* and the PRD entries of *Traces to* are the CPO's
*(confirmed with an addition: `trail/sdd/cycle-1.md` § 2.5; the two cut calls kept, § 3.1 and
§ 3.2; why, RN-13)*.

Every suite command is typed from the product root, inside the virtual environment the setup
instructions make for the test dependencies (§ 4 RT-4). "Both suites pass" means `pytest tests/`
exits 0 and `pytest tests/e2e/` exits 0.

### S-1 — From a fresh copy to a first project that stays

- **Slug:** `first-project`
- **Delivers:** After this, a reader can follow the written setup instructions from a fresh copy to
  the tracker open in their browser, create a first project there, and find it still there after
  stopping and starting the tracker.
- **Reached when:**
  - *Behaviour.* A person following only the setup instructions reaches the Projects page in its
    first-run state, with the create form in view (UXD UX-F1, UX-S3). The console shows the address
    and the saved-data location and nothing before them (UX-S2). The create form says beside the
    description field that the description cannot be changed later, and the most characters it can
    hold (UX-F2). Creating a project
    lands on that project's page, which shows its name and description and says it has no tasks
    yet. The page does not invite a first task, because the add-task form arrives with
    `tasks-in-a-project` (UX-S4; § 4 EX-12). A blank name and a name already in use are each
    refused beside the name field, with the typed text kept, and the page opens at the name field
    (UX-I3; § 4 EX-4). Projects lists every project by name, ignoring case. After a stop and a
    start the project is still listed. An address for a project that does not exist shows the
    not-found page, which speaks of a project only and links to Projects only (UX-S10; § 4 EX-12).
    Starting while something else holds the address shows one plain message.
  - *Command.* `python3 main.py` prints the address and the saved-data location and serves until
    stopped. Both suites pass, and they hold at least one unit, one integration and one end-to-end
    test, including the tests SRS AC-9, AC-10 and AC-18 describe and AC-6 for a project. An
    end-to-end test shows that a refused project name opens the page with keyboard focus in the
    name field and the reason as that field's accessible description (§ 4 EX-4, EX-14, RT-9). An
    end-to-end test fills a project's description to its maximum with line breaks in it and finds
    the project created with the description saved whole, which is the description half of SRS
    AC-20. A test sends a tracker started by `main` a project name longer than its maximum, in a
    request no page of the tracker can send: the page that answers opens, gives the reason and holds
    none of the sent text, and the saved data is unchanged, which is AC-12's over-long refusal (§ 4
    RT-8, RT-10; § 11 R-10). An integration test builds the create-project form and finds the
    number its sentence states equal to the description field's `maxlength` (§ 4 RT-10). After a
    project is created, `git status --short` in the copy lists nothing under `data/`.
  - *Artifact.* `products/tracker17/README.md` holds the setup instructions with every section UXD
    UX-S1 lists and the way to run the suite (SRS FR-4). Its opening paragraph, under its title and
    before anything else, names both of tracker17's purposes, the worked example and kensaiapp's own
    testing ground, and of tracker17's earlier versions names only tracker16-X (SRS FR-41, whose
    wording is `products/tracker17/docs/CONTENT.md`'s; the check is AC-21's inspection). Its
    prerequisites section holds what § 4 RT-1, RT-3 and RT-4 give it: Python 3.11 or later, with the command that shows the version and
    what to do when the version is lower; macOS and Linux, checked on macOS only, and Windows not
    supported; and a network connection needed once, only to set up the test suite. Its section on
    running the suite says how to make the virtual environment and install the test dependencies,
    and holds what § 4 RT-4 gives it for Linux: the install command that also fetches the browser's
    system libraries, that the command runs the package manager and asks for administrator rights,
    that the tracker and `pytest tests/` need none of it, and the Linux systems the pinned library's
    documentation lists. The same section says the full suite needs the copy to be a Git repository
    with `git` on the path, which the tracker's own setup does not, and says what the one test that
    does not pass otherwise checks: that Git ignores the saved data (SRS FR-6). That test is
    `test_data_is_ignored_by_version_control` in `tests/integration/test_start.py`, and it runs
    `git check-ignore`. `pyproject.toml` declares `requires-python = ">=3.11"`. `main.py`,
    `domain/projects.py`, `application/`, `persistence/` and `web/` exist. *(the Linux line and the
    Git prerequisite: `trail/sdd/cycle-4.md` § 5.1; why, RN-38, RN-39; the opening paragraph: SRS
    version 6, § 10 RC-3; why, RN-43)*
- **Rests on:** § 2; § 3, all five parts and all seven seams; § 4, every condition. No earlier
  slice.
- **Traces to:** PRD § Purpose, § Key Use Cases 1, 2 and 3, § Core Features Projects and Tested
  throughout, § UX Notes Arrival, First run, Persistence, Refusals say why and Failure states,
  § Success Metrics Simple to set up and Simple to read, § Data & Privacy, § Out of Scope, hosting.
  SRS FR-1 to FR-7, FR-9, FR-10, FR-11, FR-37, FR-39, FR-40, FR-41, NFR-2, NFR-4, NFR-5, NFR-8,
  NFR-9, NFR-11, DR-1, C-2, C-6, C-7, C-8. UXD UX-F1, UX-F2, UX-S1, UX-S2, UX-S3, UX-S4, UX-S10,
  UX-I3, UX-I4, UX-I8.
- **Moves toward:** the Agari's second bar, Simple to set up, in full. The first step of its first
  bar, Works. The first step of its third bar, Simple to read, for the Projects feature and for the
  first code a reader can read cold.
- **Not in this slice:** tasks, and the add-task form on the project's page — `tasks-in-a-project`.
  Renaming or deleting a project — `delete-and-rename`. The page for saved data that cannot be read,
  and the refusal of a second tracker — `protect-saved-data`. Until that slice, a start that cannot
  read the saved data stops with one plain message and writes nothing (§ 4 SD-4). The header's
  People and All tasks links arrive with `tasks-in-a-project` and `narrow-and-sort`. A package, an
  installer or a hosted demo, which the PRD places out of scope and no slice owns.
- **Why here in the order:** first. It is the smallest slice that carries one action from a page
  through the rules into the saved data and back after a restart, under the real start command. It
  uses all five parts and all seven seams, so it is the cheapest place for the shape of § 2 to be
  shown wrong. It also puts the whole Simple-to-set-up bar in front of the
  owner before any feature is built on a setup that might fail it. Its refused project name is the
  first page an action opens at a place, so § 11 R-2 is first tested here, on a form control. Its
  description is the first multi-line field, so § 4 RT-10's count of a line break and § 11 R-11 are
  first tested here too.

### S-2 — Tasks in a project

- **Slug:** `tasks-in-a-project`
- **Delivers:** After this, the operator can keep the list of people tasks can be assigned to, add
  tasks to a project with a priority, a due date and an assignee, see them in the project's list
  with overdue tasks marked, and open a task to change its fields and its labels.
- **Reached when:**
  - *Behaviour.* The header gains People (§ 4 EX-12). People shows the assignee list with Add and a
    Remove beside each name, and nothing yet about the operator's name. A removal needs no
    confirmation, and its completion line says the name stays on the tasks that carry it (UXD
    UX-F8, UX-S8). The project's page gains the add-task form, with `medium` chosen, the assignee
    offered from the list or none, and a date picker, and its no-tasks state now invites a first
    task. Adding lands on the new task's page (UX-F3). The project's list shows one row per task
    with its title, status, priority, assignee or "unassigned", labels and due date, and the word
    "Overdue" beside the due date when it applies (UX-S4, UX-A4). The list is in due-date order,
    earliest first, undated tasks last (UX-F5, Defaults). The task's page changes title, priority,
    assignee and due date, and adds or removes one label at a time (UX-F9, UX-S6). A task whose
    assignee has left the list shows that name as the assignee control's current choice, with a
    sentence beside the control saying the name is no longer on the list and that choosing another
    assignee or none replaces it. A save that leaves the control as it showed keeps the name
    (UX-F9, UX-S6; § 4 RT-7). A blank title, a blank or repeated assignee name, and an assignee
    changed to a name that left the list after the page loaded are each refused where they were
    entered, the last as out of date (UX-I3). The not-found page now also speaks of a task (UX-S10).
  - *Command.* Both suites pass, including the tests SRS AC-19 describes and AC-13's first two
    cases for the list marking, a test that a save of the edit form leaving an assignee as the page
    showed it keeps a name that has left the list, and a test that an assignee changed to a name
    that left the list after the page loaded is refused with the saved data unchanged (SRS FR-21,
    FR-22, NFR-3; § 4 RT-7). An end-to-end test shows that after an assignee name is added, and
    after a label is added, the page opens with keyboard focus on the added name or label and the
    completion line as its accessible description (§ 4 EX-5, EX-14, RT-9). `python3
    tests/timed_run.py` exits 0 with 1,000 tasks loaded, states the text lengths it uses (SRS
    AC-15), and reports every action it covers under 1 second.
  - *Artifact.* `domain/tasks.py`, `domain/priorities.py`, `domain/assignees.py`, `domain/labels.py`
    and `domain/due_dates.py` exist, and `tests/timed_run.py` exists.
- **Rests on:** § 3; § 4; `first-project`.
- **Traces to:** PRD § Key Use Cases 2 and 3, § Core Features Tasks, Priorities, Assignees, Labels
  and Due dates, § UX Notes First run, Refusals say why, What must feel effortless and Defaults,
  § Success Metrics Simple to read. SRS FR-15, FR-16, FR-20 to FR-26, FR-31, FR-37, FR-39, FR-40,
  NFR-1, NFR-3, NFR-9, NFR-14, DR-2, DR-4. UXD UX-F3, UX-F5, UX-F8, UX-F9, UX-S4, UX-S6, UX-S8,
  UX-S10, UX-A4.
- **Moves toward:** the Agari's first bar, Works, for the first half of Key Use Case 3. Its third
  bar, Simple to read, for the Tasks, Priorities, Assignees, Labels and Due dates features, whose
  entry points this slice adds (§ 4 TS-3).
- **Not in this slice:** moving a task's status — `status-moves`. Deleting a task —
  `delete-and-rename`. The filter and sort controls, and the list across all projects —
  `narrow-and-sort`. The Summary view — `project-summary`. Comments, and the Your name half of
  People — `comment-on-a-task`.
- **Why here in the order:** second. Every later slice except `protect-saved-data` acts on a task,
  so none of them can be reached before a task exists. This slice also fixes the saved form of a
  task and the row every list shows. Its focus test is the first on an element that is not a
  control, the case § 11 R-2 left unverified until this slice's People half ran (RN-41), and only
  `first-project` rests on the page model when it runs.

### S-3 — Comments under the operator's name

- **Slug:** `comment-on-a-task`
- **Delivers:** After this, the operator can set their own name and comment on a task, and each
  comment shows under the name it was written with and the time it was written.
- **Reached when:**
  - *Behaviour.* People gains Your name, which sets or changes the name and says beside the field
    that comments already written keep their name. A blank name is refused (UXD UX-F8). A task's
    page lists its comments oldest first, each with its author and its time in the machine's local
    time, with the form below the newest, which says beside its text field the most characters a
    comment can hold (UX-F7). After Add, the page opens with the new comment in
    view (§ 4 EX-5). With no name set, a notice above the form says a name is needed and links to
    People. A comment with no name set, and a blank comment, are each refused with the typed text
    kept. After the name changes, earlier comments still show the earlier name. No control edits or
    deletes a comment.
  - *Command.* Both suites pass, including SRS AC-6 with every field it lists. An end-to-end test
    adds a comment to a task whose comments fill more than the window, and shows the new comment in
    view with keyboard focus on it (§ 4 EX-5, RT-9). An end-to-end test fills a comment to its
    maximum with line breaks in it and finds it saved whole, which completes SRS AC-20 beside
    `first-project`'s test of the description (§ 4 RT-10). An integration test builds the
    add-comment form and finds the number its sentence states equal to the comment field's
    `maxlength` (§ 4 RT-10). `python3 tests/timed_run.py` exits 0 with 1,000 tasks carrying 20
    comments each.
  - *Artifact.* `domain/comments.py` exists.
- **Rests on:** § 3, the Comment and Operator name entities; § 4; `tasks-in-a-project`.
- **Traces to:** PRD § Key Use Cases 2 and 5, § Core Features Comments, § UX Notes Refusals say why
  and Defaults, § Success Metrics Simple to read. SRS FR-27 to FR-30, FR-39, FR-40, NFR-1, NFR-9,
  NFR-14, DR-3, DR-5. UXD UX-F7, UX-F8, UX-S6, UX-S8.
- **Moves toward:** the Agari's first bar, Works, for Key Use Case 5. Its third bar, Simple to
  read, for the Comments feature, whose entry point this slice adds (§ 4 TS-3).
- **Not in this slice:** deleting a task together with its comments — `delete-and-rename`. Threaded
  replies to a comment, which the PRD places out of scope and no slice owns.
- **Why here in the order:** third, and it could be built at any point after `tasks-in-a-project`.
  It is placed here because it brings the saved data to SRS NFR-1's full volume. That measurement
  is the one most able to overturn the way the saved data is written (§ 9 TO-3), and it is cheapest
  to learn while only two slices rest on that choice.

### S-4 — Moving a task through its workflow

- **Slug:** `status-moves`
- **Delivers:** After this, the operator can move a task through its status workflow from any list
  row or from the task's page, and a move the workflow does not allow is refused with its reason.
- **Reached when:**
  - *Behaviour.* Every row and the task's page offer exactly the moves allowed from the task's
    status, as buttons named by the status they move to. A task in `done` or `cancelled` offers
    none (UXD UX-I1). A press saves the move and leaves the operator at the moved task's row, or at
    the task's moves on the task's page, with the new status shown and one line naming what changed
    (UX-F4, UX-I4). A move to `cancelled` first shows the in-place confirmation. It opens in view,
    with its sentence, its confirming control and its back-out control in that order, and with
    focus where UX-I2 places it. A double press on the first button never confirms, on a list
    scrolled part-way too. Backing out returns focus to the restored button. A first press for a
    move the task no longer allows is refused with no confirmation. A move pressed after another
    tab moved the task is refused, says the task's status has changed and names the moves the page
    now shows, or none for a final status, and offers no reload, because the list or the task's
    page it lands on is built after the refusal and already shows the current status and the moves
    it allows (UX-I3, UX-F4). A move refusal reached by an address and no press — the address that
    shows the confirmation of a move to `cancelled`, or the one that backs out of it, opened again
    by a reload, by Back or from a bookmark once the task is in `done` or `cancelled`, on a
    project's Tasks view and on the task's page alike — shows where the confirmation would have
    been, beside the task's status, says what is true now, names no action and offers no reload
    (UX-F4, UX-I3). A task moved to `done` or `cancelled` is no longer marked overdue. *(the two
    refusals: `trail/sdd/cycle-8.md` § 5.2; why, RN-50)*
  - *Command.* Both suites pass, including a test for every allowed move, every refused move and a
    move to the status a task already has (SRS FR-18), the out-of-date move of AC-12, and AC-13's
    third case. End-to-end tests show where focus lands in the confirmation and on backing out,
    that a double press on the first button of a row far down a list scrolled part-way does not
    confirm, and that a first press for a move the task no longer allows opens no confirmation
    (§ 4 EX-6). `python3 tests/timed_run.py` exits 0 and covers a move.
  - *Artifact.* `domain/workflow.py` exists.
- **Rests on:** § 4 EX-5, EX-6, EX-7; `tasks-in-a-project`.
- **Traces to:** PRD § Key Use Cases 2 and 3, § Core Features Status workflow, § UX Notes The status
  workflow is visible, What must feel effortless and Refusals say why, § Success Metrics Simple to
  read. SRS FR-18, FR-19, FR-25, FR-39, NFR-1, NFR-3, NFR-9, NFR-12. UXD UX-F4, UX-S4, UX-S6,
  UX-I1, UX-I2, UX-I3, UX-I4, UX-A6.
- **Moves toward:** the Agari's first bar, Works, completing Key Use Case 3. Its third bar, Simple
  to read, for the Status workflow feature, whose entry point this slice adds (§ 4 TS-3).
- **Not in this slice:** the confirmations on deleting a task and a project — `delete-and-rename`.
  A moved task leaving a list that is filtered by status — `narrow-and-sort`.
- **Why here in the order:** fourth. It is the first use of the in-place confirmation and of the
  out-of-date refusal. The confirmation is the interaction most exposed to pages that run no
  script (§ 9 TO-2): its focus lands on a sentence, and its double press has to fail on a scrolled
  list. A failure found here costs the pages of one action. `narrow-and-sort` also needs tasks in
  more than one status, and only this slice puts a task in one.

### S-5 — Narrowing and sorting a task list

- **Slug:** `narrow-and-sort`
- **Delivers:** After this, the operator can narrow a task list by status, priority, assignee,
  label, due-date range or overdue, sort it by one field, and do both within one project or across
  all projects.
- **Reached when:**
  - *Behaviour.* The header gains All tasks, and the not-found page links to it from this slice on
    (§ 4 EX-12; UXD UX-S10). The filter and sort controls sit above the project's list and above
    the new All tasks list, which adds a project column (UX-F5, UX-S7). The All tasks rows carry
    everything a project's rows carry, the moves included. With no tasks anywhere, All tasks says
    so and links to Projects (UX-S7). Apply shows only the matching tasks,
    sorted, with the count of matches and the choices still shown. The choices are in the address,
    so a reload, the back button and a bookmark all show the same list (UX-I7). Clear returns to
    every task in due-date order. The assignee filter offers the names on the list, and the label
    filter offers the labels carried in the list's scope. A range whose from-date is after its
    to-date is refused. A filter that matches nothing says so and shows Clear. A task moved out of
    a status the list is filtered by leaves the list, and the completion line names it (UX-F4).
  - *Command.* Both suites pass, including the filter and sort tests SRS AC-14 lists, the reversed
    range of AC-12, and the overdue filter agreeing with the list marking on AC-13's three cases.
    `python3 tests/timed_run.py` exits 0 and covers a filter and a sort.
  - *Artifact.* `domain/filtering.py` and `domain/sorting.py` exist.
- **Rests on:** § 4 EX-3; `tasks-in-a-project`; `status-moves`.
- **Traces to:** PRD § Key Use Cases 2 and 4, § Core Features Filtering and Sorting, § UX Notes What
  must feel effortless and Refusals say why, § Success Metrics Simple to read. SRS FR-31 to FR-37,
  FR-39, NFR-1, NFR-9. UXD UX-F4, UX-F5, UX-S4, UX-S7, UX-S10, UX-I7.
- **Moves toward:** the Agari's first bar, Works, for the first half of Key Use Case 4. Its third
  bar, Simple to read, for the Filtering and Sorting features, whose entry points this slice adds
  (§ 4 TS-3).
- **Not in this slice:** the project summary and its links into a filtered list —
  `project-summary`. More than one value in a filter field, and sorting by more than one field,
  which the PRD places out of scope and no slice owns.
- **Why here in the order:** fifth. These are the rules the PRD names as most likely to drift (PRD
  § Risks), so they come as early as their inputs allow, which is directly after `status-moves`.
  `project-summary` links into this slice's lists and waits for it.

### S-6 — The project summary

- **Slug:** `project-summary`
- **Delivers:** After this, the operator can open a project's summary to see where the project
  stands, and step from a count into the list of the tasks it counts.
- **Reached when:**
  - *Behaviour.* A project gains its Tasks and Summary links. The summary shows the total, a count
    for each status and each priority with zeros shown, the overdue count, the count with no due
    date, and the open tasks for each assignee, with a row for every listed name, every unlisted
    name an open task still carries, and "(unassigned)" (UXD UX-F6, UX-S5). Each status count, each
    priority count and the overdue count is a link to the project's list filtered to that value.
    The other counts are plain numbers. An empty project shows zeros and invites a first task.
  - *Command.* Both suites pass, including the summary test of SRS AC-14 on a project built to
    exercise each row, and the overdue count agreeing with the marking and the filter on AC-13's
    three cases. `python3 tests/timed_run.py` exits 0 and covers opening a summary.
  - *Artifact.* `domain/summary.py` exists.
- **Rests on:** § 3; `narrow-and-sort`.
- **Traces to:** PRD § Key Use Cases 2 and 4, § Core Features Project summary, § Success Metrics
  Simple to read. SRS FR-25, FR-38, NFR-1, NFR-9. UXD UX-F6, UX-S4, UX-S5.
- **Moves toward:** the Agari's first bar, Works, completing Key Use Case 4. Its third bar, Simple
  to read, for the Project summary feature, whose entry point this slice adds (§ 4 TS-3).
- **Not in this slice:** a summary across projects, which the PRD places out of scope and no slice
  owns.
- **Why here in the order:** sixth. Its linked counts open lists that only `narrow-and-sort` can
  show, so it follows that slice directly.

### S-7 — Deleting, and renaming a project

- **Slug:** `delete-and-rename`
- **Delivers:** After this, the operator can delete a task, rename a project, and delete a project
  together with its tasks.
- **Reached when:**
  - *Behaviour.* Delete task on a task's page shows the in-place confirmation, then lands on the
    task's project with a line naming the deleted task (UXD UX-F9). Below a project's list, Rename
    holds the current name, and a blank name or one in use is refused (UX-F10). Delete project
    shows a confirmation naming the project and its number of tasks, then lands on Projects with a
    line naming the deleted project. Both confirmations behave as the one in `status-moves` does,
    and Delete project's holds below a list long enough to scroll (§ 4 EX-6). The deleted project's
    tasks appear in no list. The address of a deleted task or project shows the not-found page
    (UX-S10). An action sent from another tab for something already deleted is refused and changes
    nothing.
  - *Command.* Both suites pass, including tests that a deleted project's tasks and comments are
    gone (SRS FR-13, FR-17), that a deleted task's identity is not issued again (FR-15), that a
    rename leaves the project's tasks unchanged (FR-12), and the deleted-target refusals of AC-12.
    An end-to-end test shows Delete project's confirmation below a list long enough to scroll: it
    opens in view with keyboard focus on its sentence, and a double press on the first button does
    not confirm (§ 4 EX-6). `python3 tests/timed_run.py` exits 0 and covers a deletion.
  - *Artifact.* No new feature module. The opening docstrings of `domain/projects.py` and
    `domain/tasks.py` name the tests this slice adds.
- **Rests on:** § 4 EX-6, EX-13; `tasks-in-a-project`.
- **Traces to:** PRD § Key Use Cases 2, § Core Features Projects and Tasks, § UX Notes Refusals say
  why, § Success Metrics Simple to read. SRS FR-12, FR-13, FR-15, FR-17, FR-39, FR-40, NFR-1,
  NFR-3, NFR-9. UXD UX-F9, UX-F10, UX-I2, UX-S4, UX-S6, UX-S10.
- **Moves toward:** the Agari's first bar, Works, for the Projects and Tasks features in full. Its
  third bar, Simple to read, by completing the traces of those two features: their entry points
  name the tests this slice adds.
- **Not in this slice:** moving a task to another project, which SRS FR-14 excludes and no slice
  owns. Changing a project's description, which UXD § 10 excludes.
- **Why here in the order:** seventh, and it could sit anywhere after `tasks-in-a-project`. It is
  placed after `status-moves` so that it reuses a confirmation already shown to work, and after
  `comment-on-a-task` so that deletion is checked with comments present. Both are preferences. It
  carries no rule the PRD marks as risky, which is why the slices before it come first.

### S-8 — Saved data that cannot be read, and a second tracker

- **Slug:** `protect-saved-data`
- **Delivers:** After this, an operator whose saved data cannot be read is told so on every page,
  with where the data is and that nothing was changed, and a second tracker started on the same
  saved data refuses to start.
- **Reached when:**
  - *Behaviour.* With saved data that cannot be read, the console says so and names its location,
    and every address shows the one page that says the data could not be read, where it is and that
    nothing was changed, with no navigation and no control that acts on the data (UXD UX-F11,
    UX-S9). The page points to the setup instructions' section on setting saved data aside
    (UX-S9). After the operator sets the data aside as the setup instructions say, the tracker
    starts empty and the set-aside file still holds the earlier work. A second start on a location
    a running tracker is using shows one plain message, and the first tracker carries on (UX-S2).
    A start after a tracker was killed succeeds.
  - *Command.* Both suites pass, including one test for each kind of break SRS DR-6 names, a saved
    value longer than its field's maximum among them, each asserting the saved data's bytes are
    unchanged (AC-7), and both halves of AC-16.
  - *Artifact.* No new feature module. The tests live with `persistence` and `main`.
    `products/tracker17/README.md` describes what a start does with saved data that cannot be read,
    and with a second tracker, as this slice leaves them (§ 4 EX-12).
- **Rests on:** § 3, `SM-5` and `SM-6`; § 4 SD-4, SD-5; `first-project`.
- **Traces to:** PRD § UX Notes Failure states. SRS FR-8, NFR-3, DR-6. UXD UX-F11, UX-S2, UX-S9.
- **Moves toward:** the Agari's first bar, Works, for the PRD's failure states.
- **Not in this slice:** any control inside the tracker that sets data aside or repairs it. The
  setup instructions own that, and they are delivered by `first-project`.
- **Why here in the order:** last, and it could sit anywhere after `first-project`. It is placed
  last so that AC-7's one test for each kind of break is written once, against the complete data
  model. Nothing waits on it, because § 4 SD-4 already keeps unreadable data from being written.

## 7. The order, and why

This table is a projection of § 6. Where the two disagree, § 6 is right and this table is stale.

| From | Relation | To | Why — the reason this holds |
|---|---|---|---|
| `tasks-in-a-project` | `depends_on` | `first-project` | A task belongs to a project (SRS DR-2), so no task can be added before a project can be created and saved. |
| `comment-on-a-task` | `depends_on` | `tasks-in-a-project` | A comment belongs to one task (SRS DR-3), and its form sits on the task's page. |
| `status-moves` | `depends_on` | `tasks-in-a-project` | A move acts on a task and is offered on the list row that slice builds. |
| `narrow-and-sort` | `depends_on` | `tasks-in-a-project` | A filter and a sort act on the task list, and the assignee and label filters offer values only tasks and the assignee list hold. |
| `narrow-and-sort` | `depends_on` | `status-moves` | Its *Reached when* shows a status filter and an overdue filter working in the running product, and until `status-moves` every task is `todo`. |
| `project-summary` | `depends_on` | `narrow-and-sort` | Its status, priority and overdue counts are links to a filtered list (UXD UX-F6), and that list does not exist before `narrow-and-sort`. |
| `delete-and-rename` | `depends_on` | `tasks-in-a-project` | It deletes tasks, and a project's deletion confirmation names its number of tasks (UXD UX-F10). |
| `protect-saved-data` | `depends_on` | `first-project` | There is no saved data to fail to read, and no start to refuse, before `first-project`. |
| `comment-on-a-task` | `validates` | `first-project` | Its timed run at SRS NFR-1's full volume tests the whole-state save that `first-project` introduces. |
| `tasks-in-a-project` | `validates` | `first-project` | Its focus test shows whether a page that runs no script can open at an element that is not a control and hold keyboard focus there (§ 4 RT-9). |
| `status-moves` | `validates` | `first-project` | Its confirmation tests show whether pages that run no script can carry UXD UX-I2: focus on the sentence, and a double press that never confirms. |
| `status-moves` | `hands_off_to` | `delete-and-rename` | The in-place confirmation, as built and tested, is reused for the two deletions. |
| `protect-saved-data` | `supersedes` | `first-project` | `first-project` stops a start that cannot read the saved data. This slice replaces that stop with a tracker that starts and shows UXD UX-S9. |

## 8. Slice → seeds

A slice is **not a seed**: the Principal PM draws one and cuts it into **one or more** 根回し
Nemawashi seeds, authored to `<CORE>/templates/journey-templates/nemawashi_template.md`. How many,
and when a slice is drawn at all, are that seat's — `<CORE>/roles/loaders/principal_pm_global.md`
owns the round, and this section neither restates it nor constrains it. What this section owns is
the other half: where a slice's fields land once the cut is made.

Because a slice can yield several seeds, a field does one of three things, and the third column
says which. **Repeats** — the fact binds every seed cut from the slice, and each carries its own
copy, because each is read cold with no sibling beside it. **Divides** — the slice's whole is split
and each seed states only its share; copied whole instead, every seed would claim the slice's full
delivery. **Stays here** — a fact about this slice's place among slices, which no seed carries.

| Slice field | Seed section | Across the seeds |
|---|---|---|
| **Slug** | recorded in `## Source` as the slice this seed came from | repeats |
| **Delivers** | `## What it is` | divides — each share must be worth something on its own, or it is a fragment (§ 5 step 2) |
| **Rests on**, the SDD sections it realizes | `## What it is` | repeats |
| **Moves toward** | `## What it is` | repeats — a seed that advances no Agari is a finding |
| **Traces to**, and this SDD's path | `## Source` | repeats, narrowed to what the seed's share touches |
| **Rests on**, the slices it names by slug | `## Relation to existing work` | repeats — the order *among* these seeds is decided at the cut and is not in this SDD |
| **Not in this slice** | `## Out (later / elsewhere)` | repeats, and grows — each seed also fences off its siblings' shares, naming the seed that owns each |
| **Reached when** | the bar each 宿場 Shukuba opened from that seed is closed against | divides — the slice's own bar is met when the last of its seeds closes |
| **Why here in the order** | — | stays here |

**A seed's `## Stations — dynamic checklist` is not in this table, and that is a decision.** No
field of a slice maps to it: the route a seed is walked by is the PM's, drawn at the cut and after
it, and nothing in this document proposes one. An SDD that named the change units a slice should
break into would be writing the PM's checklist under another name — and a route written by the seat
that designed the thing anchors the seat that has to walk it, however plainly it is labelled a
suggestion. The owner's call, 2026-08-26.

**No field lands in exactly one of the seeds.** Where one looks as though it should — a dependency
in *Rests on* that only one seed turns out to consume — the edge in § 7 was drawn coarser than the
work it constrains. That is a finding about § 7, not a call to be made at the cut.

**A slice that cannot fill one of these fields is not yet a slice — go back to § 5.** The rule
survives the cut being one-to-many and binds harder for it: an unfillable field is no longer one gap
in one seed, it is the same gap in every seed the slice yields. A slice whose *Delivers* is vague
cannot be divided into shares that each stand on their own, and a slice with no fence leaves every
one of its seeds without one.

---

# Part D — What the cut costs, and what it cannot reach

## 9. Trade-offs taken

- **TO-1: No web framework and no template engine.** The design gives up a framework's routing,
  its templates and their automatic escaping, and the familiarity a reader has with them. `web`
  carries its own small versions instead. — *buys* a run time with no dependency: nothing to
  install, pin or check for advisories before the tracker runs, a setup of two commands, and a
  product whose every running line is in the copy the reader holds (§ 4 RT-1). — *undoing it costs*
  a rewrite of `web`'s page building and an install step in the setup instructions. `domain`,
  `application` and `persistence` are untouched, because no HTML crosses `SM-1`.
- **TO-2: No script in any page.** The design gives up changing part of a page in place. Every
  action is answered by a whole page, on every page an action opens. That page reopens with the
  place of the action in view, but not always at the same height in the window. — *buys* one
  language for the reader, no state in the browser to keep in step, and UXD UX-I8 and UX-I9 held by
  construction. — *undoing it costs* one script file in `web`, a second language in § 3's units
  table and on the project card, a change to § 4 SEC-3's policy, and a way to test it. The cost
  spends experience, and the CDO accepted it (`trail/sdd/cycle-1.md` § 2.3; RN-20).
- **TO-3: The whole tracker state is saved on every change.** The design gives up a save whose cost
  follows the size of the change. Here it follows the size of everything saved. — *buys* one
  contract of two operations at `SM-3`, rules that are functions from one state to the next, and a
  save that is whole or absent by construction (§ 4 SD-3). — *undoing it costs* a new `persistence`
  and a wider `SM-3`, with one operation for each kind of change, which every action in
  `application` would then call. `domain` and `web` are untouched. § 11 R-1 names the measurement
  that would force this.
- **TO-4: The state is held in memory and the file is read only at start.** A change made to the
  file by hand while the tracker runs is overwritten by the next save. — *buys* pages that need no
  disk read, and no moment in the middle of a sitting at which the data can turn out unreadable,
  which SRS DR-6 defines only "at start". — *undoing it costs* a read at the top of each request in
  `application`, and a decision the SRS does not yet make about unreadable data found mid-run.
- **TO-5: tracker16-X's saving contract is not carried over.** Its `Repository` has one method for
  each kind of change, and each method reads and rewrites the file
  (`task-tracker-X/tasktracker16x/domain/repository.py`, class
  `Repository`). The design reuses the predecessor's entities, rules and typed errors and replaces
  that contract with `SM-3`'s. — *buys* SRS NFR-3's single check-and-apply and § 4 SD-5's check at
  start, neither of which the predecessor needed. — *undoing it costs* nothing further: it is the
  same reversal as TO-3.
- **TO-6: The address is fixed and the start command takes no option.** A machine where another
  program holds the port cannot run the tracker until that program stops. — *buys* setup
  instructions with one path and no choice in them (UXD UX-F1, "Decision points: none"). —
  *undoing it costs* one argument read in `main`, which already passes the address to `web`.
- **TO-7: What a page says about the last action travels in its address.** An address copied or
  bookmarked straight after an action shows that action's line again when it is opened. Text typed
  into a refused form appears in the browser's history. Text has to fit in an address, which is
  why § 4 RT-10 bounds it, and after the one refusal whose text cannot fit the page gives the reason
  and not the text (§ 4 RT-8). — *buys* a tracker that keeps nothing between requests (§ 4 RT-7), one
  way to answer every submission, and a reload or a return through back that shows the same page
  (§ 4 RT-8). — *undoing it costs* a store in `web` for the outcome of the last submission, a
  rewrite of § 4 RT-7 and RT-8, and a rule for what a reload shows once that outcome is gone.
  `domain`, `application` and `persistence` are untouched.
- **TO-8: A page that shows a pending confirmation is answered 202.** The design gives up the plain
  reading of a status line: a 202 on a GET that completes nothing, which a reader meets as a
  mistake until § 4 RT-11 says why. — *buys* a confirmation that cannot be restored from the
  browser's history cache without a script, a cookie or a session (TO-2, TO-7), and a return
  through Back that shows the saved status. — *undoing it costs* one line in `web` and the two
  history tests RT-11 names, after which Back after confirming shows a stale confirmation on the
  pinned browser, which `test_real_history_traversal_revalidates_the_confirmation` failed on before
  the change. `domain`, `application` and `persistence` are untouched. *(confirmed with an
  addition: `trail/sdd/cycle-8.md` § 5.1; why, RN-49)*

## 10. Re-cut record

A cut meets a reality that contradicts it, and the contradiction is recorded before the cut is
redrawn. A re-cut is written only when a slice's *Reached when* cannot be met as written, a slice
turned out to be a fragment, no slice is left that can be started, or the PRD, the SRS or the UXD
changed upstream. A re-cut that moves § 2's shape or § 3's seams is also an ADR for the Principal
Architect to record. None of RC-1 to RC-4 moves either.

### RC-1 — 2026-10-06 — the SRS gained a requirement no slice realized

*Whose ground moved: the CTO's, as the owner of the SRS, which changed upstream.*

- **Prior assumption:** the cut was made against an SRS with no bound on typed text and nineteen
  acceptance criteria, and § 4 RT-10 stood on this document's own draft (`trail/sdd/cycle-2.md`
  § 2.1, "Drafted into the SDD").
- **Observed reality:** `products/tracker17/docs/SRS.md` version 4 states the bound as FR-40, lists
  the over-long value under FR-39 and DR-6, sets NFR-1's bar at ordinary lengths, has AC-15 state
  the lengths it uses, and adds AC-20. `grep -n "FR-40\|AC-20" products/tracker17/docs/SDD.md`
  printed nothing on 2026-10-06, before this revision. The SRS also closed both items of its
  § Open Questions, which RT-1, RT-10, RN-3, RN-4 and RN-22 cited by position in a list that no
  longer exists.
- **Retained:** the eight slices, their slugs, their *Delivers*, their fences, their order and every
  edge in § 7.
- **Changed:** RT-10 serves FR-40 and no longer calls itself a draft. RT-8 names the one refusal
  whose page carries no typed text. TS-3's table and TS-5 carry FR-40 and AC-15. `first-project`,
  `tasks-in-a-project`, `comment-on-a-task` and `delete-and-rename` trace FR-40, and the command
  halves of `first-project`, `tasks-in-a-project`, `comment-on-a-task` and `protect-saved-data` name
  the tests of AC-12, AC-15, AC-20 and DR-6 that the SRS added. The five citations by position now
  cite the SRS text that stands.
- **Stopped:** nothing.
- **Still unresolved:** whether a page tells the operator a field's maximum, which is the UXD's to
  answer (`products/tracker17/docs/UXD_open_issues.md` § 2.1, unanswered on 2026-10-06). When the
  UXD states it, this document follows it as an upstream change. RC-2 records the UXD stating it.

### RC-2 — 2026-10-07 — the UXD stated what two slices were waiting on

*Whose ground moved: the CDO's, as the owner of the UXD, which changed upstream.*

- **Prior assumption:** whether a page tells the operator a field's maximum was open (RC-1), and
  the behaviour line of `tasks-in-a-project` read every save of a task whose assignee had left the
  list as refused, because UXD version 3's UX-F9 refused "an assignee not on the list".
- **Observed reality:** `products/tracker17/docs/UXD.md` version 4, landed at commit `6091a6f8b`,
  folds `products/tracker17/docs/trail/uxd/cycle-3.md` §§ 2.1 and 2.2. UX-F2 and UX-F7 have the
  project-description field and the comment field state the most characters they hold, beside the
  field, with the number "taken from the same place that sets the field's limit", and no other
  field states one. UX-F9 shows an assignee who has left the list as the control's current choice,
  with a sentence beside the control, keeps the name when a save leaves the control as it showed,
  and refuses only an assignee changed to a name that left the list after the page loaded.
  `products/tracker17/docs/UXD_open_issues.md` no longer exists.
- **Retained:** the eight slices, their slugs, their *Delivers*, their fences, their order and every
  edge in § 7. RT-10's two lengths and its count.
- **Changed:** § 4 RT-7 has a form whose save must tell a changed field from one left as shown carry
  the values the page showed. RT-10 has the two sentences take their number from the same value as
  the field's `maxlength`. The behaviour halves of `first-project`, `tasks-in-a-project` and
  `comment-on-a-task` follow UX-F2, UX-F9 and UX-F7, and their command halves name the tests that
  check each. § 11 R-11 names the UXD entries that state the maximum where it named an unanswered
  question.
- **Stopped:** nothing.
- **Still unresolved:** nothing this change leaves open.

### RC-3 — 2026-10-11 — the PRD and the SRS gained a priority and a requirement no slice carried

*Whose ground moved: the CPO's, as the owner of the PRD, and the CTO's, as the owner of the SRS,
both of which changed upstream. The SRS carried the PRD's two changes down, so one record covers
both.*

- **Prior assumption:** the cut was made against PRD version 4 and SRS version 4, under which the
  priority set was tracker16-X's three values with no exception to SRS C-5, tracker17 had one
  purpose, and the setup instructions owed nothing about it.
- **Observed reality:** `products/tracker17/docs/PRD.md` version 5 adds `critical` to § Core
  Features, Priorities, and names Priorities as "The one exception" to the predecessor rule
  (commit `29352d2fc`). Version 6 gives tracker17 a second purpose, kensaiapp's own testing ground,
  and ends § Purpose with "A reader learns both purposes from the first thing they read about
  tracker17" (commit `cafd1cb92`). `products/tracker17/docs/SRS.md` version 5 names the four
  priorities in FR-15, orders them in FR-36, counts four in FR-38 and carries the exception in C-5
  (commit `083aa6d92`). Version 6 names the second purpose in § 1, adds FR-41, the README's opening
  paragraph, and AC-21, its inspection (commit `b72ea80e6`). `grep -n "critical\|FR-41\|AC-21"
  products/tracker17/docs/SDD.md` printed nothing on 2026-10-11, before this revision. On the same
  day the opening paragraph of `products/tracker17/README.md` names the worked example and not the
  testing ground, and its Status section says so ("The tracker doesn't say first that it is
  kensaiapp's testing ground, built and worked on to fix kensaiapp's problems yet").
- **Retained:** the eight slices, their slugs, their *Delivers*, their fences, their order and every
  edge in § 7. § 2's shape, § 3's parts and seams, and every § 4 condition. The priority set was
  never enumerated in this document: § 3 holds "a priority", § 4 TS-3's `priorities` row names
  FR-15, FR-16 and FR-36, and `tasks-in-a-project`'s behaviour line names `medium` as the default,
  so each stands as written under four values.
- **Changed:** § 1 names the second purpose and C-5's exception. `first-project`'s *Artifact* holds
  FR-41's opening paragraph, and its *Traces to* names PRD § Purpose and SRS FR-41. § 11 R-5 names
  the priority set as the third place a carried-over rule differs from tracker16-X's. The header's
  *Inputs read* names both versions.
- **Stopped:** nothing.
- **Still unresolved:** nothing this change leaves open to this document. `first-project`'s
  *Artifact* as it now reads is not met by the README on the day of the fold, and meeting it is the
  build's: the requirement is one paragraph in the setup instructions, no new part and no new
  slice, and a slice made of it alone would be the fragment § 5 step 2 strikes.

### RC-4 — 2026-10-21 — the UXD had no refusal offer a reload on a page built after it

*Whose ground moved: the CDO's, as the owner of the UXD, which changed upstream.*

- **Prior assumption:** the cut was made against UXD version 6, under which a status move another
  tab overtook was refused with an offer to reload, and the behaviour half of `status-moves`'s
  *Reached when* read "A move made from a page that is out of date is refused, says the status has
  changed, and offers a reload (UX-I3)". The refusal reached by an address with no press was not
  named by this document.
- **Observed reality:** `products/tracker17/docs/UXD.md` version 7, landed at commit `f90b692f9`,
  keeps the no-press refusal as a case of its own (UXD RN-33): the address that shows the
  confirmation of a move to `cancelled`, or the one that backs out of it, opened again once the
  task's status no longer allows the move, shows the refusal beside the task's status, says what is
  true now, names no action and offers no reload (UX-F4). Version 8, at `afffd0d5e`, has no refusal
  offer a reload on a page built after it: the overtaken move names the moves the page now shows,
  or none for a final status (UX-I3, UX-F4; UXD RN-34). The PM found `status-moves`'s bar false
  against both (`trail/sdd/cycle-8.md` § 5.2).
- **Retained:** the eight slices, their slugs, their *Delivers*, their fences, their order and every
  edge in § 7. § 2's shape, § 3's parts and seams. The command half of `status-moves`'s *Reached
  when*: "the out-of-date move of AC-12" still names the test, and SRS AC-12 asks only that the
  refusal shows its reason and the saved data is unchanged. `tasks-in-a-project`'s assignee refused
  "as out of date" states no reload and does not move.
- **Changed:** the behaviour half of `status-moves`'s *Reached when* states the overtaken move's
  refusal as UX-I3 and UX-F4 now state it, and names the no-press refusal beside it. § 4 EX-4 says
  where a refusal reached by an address and no control sits. The header's *Inputs read* names
  version 8.
- **Stopped:** nothing.
- **Still unresolved:** nothing this change leaves open to this document. The words the product's
  no-press refusal carries today ("the move you pressed", `web/pages.py`, the refused move's line)
  and whether its assignee refusal lines still offer a reload are changes to strings, which the UXD
  and `products/tracker17/docs/CONTENT.md` own (UXD RN-34; CONTENT RN-26), not to this document.

## 11. Technical risks

- **R-1: Saving the whole state is too slow at full volume.** — *shows up as* `python3
  tests/timed_run.py` reporting any action over 1 second with 1,000 tasks carrying 20 comments
  each. — *response* the run reaches full volume in `comment-on-a-task`, the third slice. The first
  remedy is a more compact file format inside `persistence`. If that is not enough, TO-3 is undone
  and § 10 records it.
- **R-2: Pages that run no script cannot open at the place of an action as § 4 EX-4 to EX-6 and
  EX-14 require.** The risk covers every page an action opens. The HTML standard says the
  `autofocus` attribute lets "the author … indicate that an element is to be focused as soon as
  the page is loaded", and that it "applies to all elements, not just to form controls"
  (https://html.spec.whatwg.org/multipage/interaction.html, "The autofocus attribute"). The
  standard promises focus and no more: its section says nothing about bringing the element into
  view and nothing about assistive technology (`trail/sdd/self_answer-7.md`, Header, read at the
  source on 2026-10-11). Two cases are verified in Chromium. On a form control, `first-project`'s
  refused name opens with focus in the field and the reason as its description (RN-36). On an
  element that is not a form control, made focusable with `tabindex="-1"` and carrying `autofocus`
  on a page whose address has no fragment, Chromium focuses it and brings it into view:
  `tests/e2e/test_people.py`, `test_added_markup_name_has_browser_focus_and_accessible_description`,
  finds the added name, a `span` (`web/pages.py`, `_assignee_row`, its `tabindex="-1" autofocus`
  attributes), holding keyboard focus, in the viewport, with the completion line as its computed
  accessible description and no `script` element on the page, and the same file's
  `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action` finds the People heading
  focused after a removal (`web/pages.py`, the `if on_heading:` branch), a second such element.
  Both passed at `641bb58b5` (`pytest products/tracker17/tests/e2e/`, 18 passed;
  `trail/sdd/cycle-5.md` § 5.1) and in a disposable copy of `7653f25c8` with the pinned library,
  playwright 1.63.0 and Chromium 153.0.8010.12 (`pytest tests/e2e/`, 18 passed;
  `trail/sdd/self_answer-7.md`, Header), and `git diff --stat 7653f25c8 1bdfc68fe --
  products/tracker17 ':!products/tracker17/docs'` printed nothing on 2026-10-11, so the code they
  ran against is the code on `main`. On the confirmation (§ 4 EX-6), `tests/e2e/test_moves.py`
  verifies the three parts of the case: `test_keyboard_opening_focuses_the_visible_sentence` finds
  the sentence alone holding focus, in view, with repeated Enter and Space changing nothing;
  `test_keyboard_confirming_and_back_out_use_their_own_intents` finds visible focus back on the
  trigger after backing out; `test_double_click_never_confirms_at_the_original_trigger_coordinates`
  double-clicks for real on a short page, on the task's page and on row 40 of 60 with the list
  scrolled part-way, and never confirms; and
  `test_keyboard_opening_on_a_far_row_focuses_the_visible_sentence` does the focus case on that far
  row. The four passed in a fresh clone at `9b05680c7`, 67 passed in `tests/e2e/`, with the pinned
  library, `playwright==1.63.0` (`pyproject.toml`). The browser build is asserted by the run and
  not inferred from the pin: the same run's `test_history_matrix_revalidates_current_saved_status`
  asserts `browser.version` equals `PINNED_BROWSER`, `153.0.8010.12`, on the full Chromium of that
  install (`tests/e2e/conftest.py`, the `history_browser` fixture, `channel="chromium"`), while
  the four focus tests drive the headless shell the same install provides (the `browser` fixture,
  `chromium.launch()`). `git diff --stat 9b05680c7 HEAD -- products/tracker17
  ':!products/tracker17/docs'` listed one line of `products/tracker17/README.md` and no code on
  2026-10-21, at `6de932f9d`. One case stays unverified. Assistive technology reading the
  description when the page opens (§ 4 EX-14): a computed accessible description puts the line in
  the accessibility tree and does not prove it is spoken, no test drives a screen reader, and no
  slice requires one. One pass with VoiceOver on the owner's macOS machine would settle it, and no
  slice requires that run. One bound holds on the verified cases: the suite drives the Chromium
  build the pinned library installs, and the operator's browser is current stable Chrome (SRS
  NFR-13), so a divergence between the two shows only in the owner's run-through. — *shows up as*
  a focus test failing: on a form control in `first-project`, on an element that is not a control
  in `tasks-in-a-project`, or on the confirmation in `status-moves`. The tests that pass stay among
  the triggers as the regression signal, because a Chromium release could change the behaviour and
  both suites run on every slice (§ 4 TS-1; RN-36). — *response* the three tests fall in the first,
  second and fourth slices, before the two deletions reuse the confirmation. If one fails, the
  conditions stand and the fallback is TO-2's reversal, confined to `web` (`trail/sdd/cycle-1.md`
  § 2.3). *(narrowed: `trail/sdd/cycle-5.md` § 5.1; why, RN-41; the confirmation case:
  `trail/sdd/cycle-8.md` § 2.1; why, RN-51)*
- **R-3: A page built by hand shows typed text as markup.** — *shows up as* a title, label, name or
  comment containing `<` or `&` displaying wrongly, or changing the page around it. — *response*
  § 4 SEC-4 gives every value one way into a page, and each slice's end-to-end test enters such
  text in the fields the slice adds.
- **R-4: The standard library's listener stalls on a connection that sends nothing.** Python's
  documentation says its threaded server "is useful to handle web browsers pre-opening sockets, on
  which `HTTPServer` would wait indefinitely" (https://docs.python.org/3/library/http.server.html).
  — *shows up as* a page that never finishes loading in Chromium. — *response* § 4 RT-6 accepts
  connections concurrently and applies requests one at a time, and the end-to-end layer runs in
  Chromium from `first-project` on.
- **R-5: A carried-over rule drifts from tracker16-X.** — *shows up as* a rule test taken from
  tracker16-X failing or missing in tracker17. — *response* each slice that brings a predecessor
  rule into `domain` brings that rule's tests with it, and changes one only where the SRS differs.
  The SRS names three such places: a blank operator name and a blank comment are refused (SRS
  RN-19), and the priority set is four values, `critical` after `high`, where tracker16-X's is
  three (SRS C-5, FR-15, FR-36, RN-24). *(the third place: SRS version 5, § 10 RC-3; why, RN-43)*
- **R-6: The trace pointers go stale.** — *shows up as* § 4 TS-4's test failing. — *response* that
  test runs in `pytest tests/` from `first-project` on, so a moved file fails the suite in the
  slice that moved it, and a feature module that lands without its word in the test's list fails it
  too (§ 4 TS-4; RN-34).
- **R-7: A reader takes the listener for one fit to face a network.** Python's documentation says
  "`http.server` is not recommended for production"
  (https://docs.python.org/3/library/http.server.html). — *shows up as* a change that makes the
  tracker listen on an address other than loopback. — *response* § 4 RT-5 and SEC-2 hold the
  listener to the machine, and SRS AC-10 inspects the address.
- **R-8: The Python floor is declared and nothing checks it.** The suite runs only on the Python
  the machine has. On the owner's machine that is 3.14.7 today (`python3 --version` printed `Python
  3.14.7` on 2026-10-06). Code written and tested there can use something Python 3.11 lacks, and
  no test on that machine would fail. — *shows up as* a start or a suite failure on a Python
  between 3.11 and the one the suite last passed on. — *response* § 4 RT-1 keeps the run-time code
  to the standard library, and `pyproject.toml` declares the floor. One run of `pytest tests/`
  under a Python 3.11 interpreter would settle it, and no slice requires that run.
- **R-9: Linux is named as supported, and the end-to-end suite has not passed there.** The owner's
  machine is macOS (`uname -s` printed `Darwin` on 2026-10-06), and no run in the Agari's check uses
  Linux. One run outside that check has happened. On 2026-10-08, on Debian 12 (bookworm), aarch64,
  in a fresh copy and following the setup instructions' commands, `python3 main.py` started and
  served, `pytest tests/` gave 224 passed, and `pytest tests/e2e/` gave `1 failed, 1 passed, 10
  errors`, each from the browser build the pinned library installs failing to load
  `libglib-2.0.so.0` (`trail/sdd/cycle-4.md` § 5.1). That run settled the tracker and the
  non-browser suite on Linux, as § 4 RT-3 expected. What it found was a prerequisite the
  instructions did not name, which § 4 RT-4 now names, and not a defect of the tracker. — *shows up
  as* `pytest tests/e2e/` failing on a Linux the pinned library lists, with the libraries RT-4 names
  installed; or any other setup or suite failure on Linux. — *response* § 4 RT-3 has the setup
  instructions say the tracker has been checked on macOS only, and RT-4 has them give the Linux
  install command and the systems the suite runs on. One green run of `pytest tests/e2e/` on a
  listed Linux with those libraries installed would settle what remains, and no slice requires that
  run. A Linux failure that needs code of its own is a re-cut under § 10.
- **R-10: An address cannot carry what a page must show after an action.** § 4 RT-8 puts typed
  text in the address. Python's listener refuses a request line longer than 65,536 bytes: on
  Python 3.14.7, `http.server`'s `handle_one_request` reads `if len(self.raw_requestline) > 65536:`
  followed by `self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)`. — *shows up as* a page that
  fails to open after a form is refused, or after something with a very long name is deleted. —
  *response* § 4 RT-10 holds every text field under a length whose address fits, and RT-8 keeps
  typed text out of the address after the one refusal where it would not. A failure that is not a
  refusal carries what was typed (§ 4 OB-3), and on this reading it follows a value `domain`
  accepted: `application` applies the rule before it saves (§ 4 SD-2), and the save is where such a
  failure arises.
- **R-11: The field and the rule count a value differently.** — *shows up as* a comment or a
  description the field accepted being refused as too long, which is SRS AC-20's test failing, in
  `first-project` for the description and in `comment-on-a-task` for the comment; or as a field
  stopping short of its stated number on text outside the Basic Multilingual Plane. — *response*
  § 4 RT-10 turns each submitted line break back into the one character the field counted and
  counts code points, which the field never under-counts, and the first case is tested in the first
  slice. The second case refuses nothing and is accepted. The description field and the comment field
  state the most characters they hold beside the field, and the number is the field's own maximum
  (UXD UX-F2, UX-F7; § 4 RT-10), so a field that stops short of it on such text has still taken no
  more than the sentence says.
- **R-12: A browser release admits a non-200 main document to its history cache.** § 4 RT-11 rests
  on the pinned Chromium admitting only a main document answered exactly 200 to its back/forward
  cache, a rule read at its source on 2026-10-20 and promised by no standard. — *shows up as*
  `tests/e2e/test_moves.py`, `test_history_matrix_revalidates_current_saved_status` or
  `test_real_history_traversal_revalidates_the_confirmation`, failing: a return to a confirmation's
  address restored from history instead of loaded. — *response* both run on every slice (§ 4 TS-1),
  and the fallback is TO-2's reversal confined to `web`, as R-2's. The bound R-2 states holds here
  too: the suite drives the build the pinned library installs, and the operator's browser is
  current stable Chrome (SRS NFR-13). *(confirmed with an addition: `trail/sdd/cycle-8.md` § 5.1;
  why, RN-49)*

## 12. What this design is not

**Above.** This document changes no product goal or scope, which are the PRD's. It changes no
system requirement, which are the SRS's. It changes nothing of the experience, which is the UXD's.
A gap found in any of the three is an item in `products/tracker17/docs/SDD_open_issues.md`, never a
rewrite here.

**Below.** This document authors no ADR. The architecturally significant decisions are surfaced in
three places and no fourth: § 2's shape table, § 9's trade-offs and the SDD Review Notes. The
Principal Architect records them. The records are `products/tracker17/docs/adr/`, ADR-0001 to
ADR-0009, and `products/tracker17/docs/nfdr.md`. Where a condition in § 4 and an entry in `nfdr.md`
disagree, the § 4 statement wins and the entry is re-derived, because downstream is rebuilt from
upstream and never the reverse (`<CORE>/templates/product-templates/sdd_template.md` § 4). This
document designs no individual change. It names no file inside a part beyond the feature entry points of
§ 4 TS-3, and how each part is laid out inside is the delivery-tier Architect's, one change at a
time.

---

## SDD Review Notes

RN-1 to RN-17 were written on 2026-10-06, in this document's first authoring. RN-18 to RN-23 were
written the same day, when the first answered round was folded in
(`products/tracker17/docs/trail/sdd/cycle-1.md`). RN-24 to RN-27 were written the same day too, when
the second answered round was folded in (`products/tracker17/docs/trail/sdd/cycle-2.md`) and the
document caught up with SRS version 4 (§ 10 RC-1). RN-28 to RN-30 were written on 2026-10-07, when
two choices raised for the CTO's seat were settled and the document first referred to the ADRs and
the NFDR. RN-31 to RN-33 were written the same day, when the document caught up with UXD version 4
(§ 10 RC-2). RN-34 to RN-37 were written the same day, when the third answered round was folded in
(`products/tracker17/docs/trail/sdd/cycle-3.md`): three items the PM raised from the product's code,
answered in the CTO's seat. RN-38 to RN-40 were written on 2026-10-08, when the fourth answered
round was folded in (`products/tracker17/docs/trail/sdd/cycle-4.md`): one item the PM raised after
running the setup instructions on Linux, answered in the CTO's seat. RN-41 to RN-44 were written on
2026-10-11, when the fifth answered round was folded in
(`products/tracker17/docs/trail/sdd/cycle-5.md`): one item the PM raised from a passing end-to-end
test, answered in the CTO's seat, and the document caught up with PRD version 6 and SRS version 6
(§ 10 RC-3). RN-45 and RN-46 were written on 2026-10-12, when the sixth answered round was folded in
(`products/tracker17/docs/trail/sdd/cycle-6.md`): one item the PM raised from the product's code,
answered in the CTO's seat. RN-47 and RN-48 were written the same day, when the seventh answered
round was folded in (`products/tracker17/docs/trail/sdd/cycle-7.md`): one item the PM raised from
the product's code, answered in the CTO's seat. RN-49 to RN-52 were written on 2026-10-21, when the
eighth answered round was folded in (`products/tracker17/docs/trail/sdd/cycle-8.md`): two items the
PM raised from the product's code and from the UXD, and one a `companion-self-answer` run raised
from § 11 read against the suite, all three answered in the CTO's seat, and the document caught up
with UXD version 8 (§ 10 RC-4). Where an answer settled what an earlier note called
a draft, that note now says so and names the note that carries the answer.

- **RN-1:** *(CPO)* *(added)* § 1 is drafted and treated as settled by the inputs. Each sentence
  restates the PRD, the Agari or the SRS and adds nothing to them, so no item was raised — *because*
  the template asks § 1 to name the goals and requirements that bound the design, and those are
  already settled upstream. *(re: § 1; source: PRD § Purpose, § Goals, § Success Metrics;
  `system/projects/tracker17/agari.md`; SRS C-1, C-2, C-5, C-7, NFR-9, NFR-10)*
- **RN-2:** *(CTO)* *(added)* The shape of § 2 — *because* of the seven forces stated there. The
  upstream documents name no architecture. *(re: § 2; source: SRS C-5, AC-13, NFR-3, NFR-7)*
- **RN-3:** *(CTO)* *(added)* Python 3.11 or later, standard library only at run time. The draft
  was confirmed with four additions, which RN-18 carries — *because* the SRS names no runtime and
  leaves it to this document (SRS RN-23, "The runtime is how the system is built, so it is the
  SDD's"), and the choice sets the prerequisites the setup instructions show. tracker16-X
  requires the same floor
  (`task-tracker-X/pyproject.toml`, `requires-python = ">=3.11"`)
  and has no run-time dependency. The UXD's own reasoning for writing the stylesheet by hand is that
  a package is "a dependency and a body of styling code they would also have to read or take on
  trust" (UXD § 9), and the same reasoning is applied to a web framework. *(re: § 4 RT-1, § 9 TO-1;
  source: SRS C-5, C-7, C-8, RN-23)*
- **RN-4:** *(CTO)* *(added)* NFR-1 needs no bound on text of its own — *because* NFR-1 is measured
  at ordinary lengths (SRS NFR-1, "The bar is set at ordinary text lengths, not at the maximums
  FR-40 allows"), and § 4 SEC-2 leaves the operator as the only party who can send text. This note
  answers for NFR-1 only. The maximum lengths of § 4 RT-10 exist for a different reason, and RN-22,
  RN-24 and RN-25 carry them. *(re: § 4 TS-5; source: SRS NFR-1, AC-15)*
- **RN-5:** *(CTO)* *(changed)* The predecessor's saving contract is replaced, and its entities,
  rules and typed errors are kept. SRS C-5 calls tracker16-X's code "the preferred starting point",
  and this departs from it for one part — *because* SRS NFR-3, FR-9 and DR-6 ask for a single
  check-and-apply, a save before a report, and a check of every rule at start, none of which the
  predecessor's contract was built for. *(re: § 3 `SM-3`, § 9 TO-3, TO-5; source: SRS C-5, NFR-3,
  FR-9, DR-6)*
- **RN-6:** *(CTO)* *(added)* SRS NFR-3's "checked against the saved data at the moment it is
  applied" is met by checking against the state held in memory — *because* § 4 SD-1, SD-2 and RT-6,
  with the one-tracker lock, keep that state identical to the saved data at every moment an action
  is applied. On this reading no requirement changes. *(re: § 4 SD-1, § 9 TO-4; source: SRS NFR-3)*
- **RN-7:** *(CTO)* *(added)* A project carries an identity, and a task's identity doubles as its
  place in creation order — *because* a project's address must survive a rename (UXD § 4), and a
  counter that only rises already gives SRS FR-15's order "independently of that recorded time".
  SRS DR-1 lists no identity for a project, and DR-2 lists the task's identity and its creation
  order as two fields. *(re: § 3, What the system holds; source: SRS DR-1, DR-2, FR-15)*
- **RN-8:** *(CTO)* *(added)* The request check of § 4 SEC-2 and the page policy of SEC-3 —
  *because* SRS NFR-4 and NFR-5 state what must hold and not how. With no login and no cookie
  (§ 4 RT-7), the request's own host and the browser's mark of where it came from are what the
  tracker has to check. *(re: § 4 SEC-2, SEC-3; source: SRS NFR-4, NFR-5)*
- **RN-9:** *(CTO)* *(added)* The trace mechanism of § 4 TS-3 and TS-4 — *because* SRS NFR-9
  requires that a reader reach a feature's code and tests "by following what the documents and the
  code point to", and no upstream document says what points to what. *(re: § 4 TS-3, TS-4; source:
  SRS NFR-9, AC-5)*
- **RN-10:** *(CTO)* *(added)* The setup instructions are `products/tracker17/README.md`, and the
  saved data is `data/` under the product root — *because* SRS FR-4 and FR-6 require both and name
  neither location. *(re: § 4 SD-6, `first-project`; source: SRS FR-4, FR-6)*
- **RN-11:** *(CTO)* *(added)* macOS and Linux as the supported machines was drafted for the CPO to
  answer, and was confirmed with three additions, which RN-19 carries — *because* neither the PRD nor the
  SRS names an operating system, the one-tracker lock of SRS NFR-3 is built differently on Windows,
  and which readers the product serves is product scope. *(re: § 4 RT-3; source: SRS FR-4, NFR-3)*
- **RN-12:** *(CDO)* *(added)* § 4's experience conditions are drafted from the UXD and treated as
  settled by it, with two exceptions. EX-2 and the focus clause of EX-6 follow from this document's
  choice to run no script, and they were sent to the CDO, whose answer RN-20 carries — *because* the UXD specifies
  focus for UX-I2 and says UX-A5's messages are "announced to assistive technology without moving
  focus", and it does not say how either holds when every action loads a whole page. *(re: § 4 EX-1
  to EX-13, § 9 TO-2; source: UXD UX-I2, UX-A5, § 9)*
- **RN-13:** *(CPO)* *(added)* The eight entries, the two struck fragments, the sizes and the CPO's
  fields of every slice were drafted by the CTO and confirmed in
  `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.5, § 3.1 and § 3.2 — *because*
  the PRD lists features and use cases and does not cut them into deliverable steps. Nothing of
  tracker17 is built today, so every entry is a difference between no product and the Agari:
  `ls products/tracker17` returned `docs` and nothing else on 2026-10-06. § 5 step 1 gave ten
  entries, and step 2 struck two as fragments. *After this, the operator can keep the list of
  people tasks can be assigned to* was struck, because a list of names with no task to assign has
  no value alone, and it is folded into `tasks-in-a-project`. *After this, the operator can set
  their own name* was struck, because the name is used only as a comment's author (SRS FR-28), and
  it is folded into `comment-on-a-task`. The eight entries that remain are the eight slices, and
  each *Delivers* is its entry. The answers kept both cut calls. `delete-and-rename` stays its own
  slice (§ 3.1), because the Agari's Works bar runs Key Use Cases 3, 4 and 5 and none of them
  deletes anything or renames a project, so folding it into `tasks-in-a-project` would put three
  more actions in front of every slice a Key Use Case needs. People arrives in two halves and
  there is no `people` slice (§ 3.2), because a screen of names that nothing yet uses lets the
  operator do nothing new, and § 5 step 2 strikes it. The answer to § 2.5 confirmed the eight
  slices, their slugs, their *Delivers* sentences and their fences, and added three things. Seven
  slices' *Moves toward* now name the Agari's third bar, Simple to read, and their *Traces to* name
  PRD § Key Use Cases 2 and § Success Metrics Simple to read, because each slice that adds a
  feature entry point makes that feature traceable from the PRD to its code and tests.
  `protect-saved-data` adds no entry point and gains neither. *Traces to* names the PRD sections
  the slices deliver and no slice named. *Not in this slice* names the PRD's remaining exclusions
  on the slice a reader would expect each in. *(re: § 5 steps 1, 2 and 4, § 6; source: PRD § Key
  Use Cases, § Core Features, § Out of Scope; `system/projects/tracker17/agari.md`)*
- **RN-14:** *(CDO)* *(added)* The behaviour lines of every *Reached when* and the UXD entries of
  every *Traces to* were drafted by the CTO and confirmed with five additions in
  `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.4 — *because* the UXD describes finished flows
  and screens, and screens arrive here in steps. The answer counts four such screens where the
  draft counted two: People, a project's page, the task's page and the not-found page. One rule
  covers the four and the header, and § 4 EX-12 now states it: until the slice that delivers a
  control or an area, no page shows it, links to it, or carries words that point to it, and the
  setup instructions follow the same rule. EX-12 excepts the page for saved data that cannot be
  read, which UXD UX-S9 gives no navigation. The lines carry what the answer to § 2.3 changes, at
  the slice where a checker first watches each case. Four lines gain a state the UXD requires at
  the slice that delivers it. *Traces to* names every UXD screen a slice adds to and every UXD
  entry its line cites. UX-I5, UX-I6, UX-I9, UX-A1, UX-A2, UX-A3, UX-A5 and UX-A7 are in no
  slice's *Traces to* on purpose: § 4 carries them to every slice. *(re: § 4 EX-12, § 6; source:
  UXD § 5, § 6, UX-S7, UX-S9, UX-S10)*
- **RN-15:** *(CTO)* *(added)* The units table names `Python`, and the project card's `Languages:`
  line is `<blank>` today (`system/projects/tracker17/project.md`, "**Languages:** <blank>") —
  *because* the card's line is written after this document settles. The header of
  `<CORE>/launchers/product-card/launcher.sh` names "write the card's architecture-determined
  fields" as a move made between a settled foundation and the cut of seeds. The table is right and
  the card is the file that follows. *(re: § 3, The units)*
- **RN-16:** *(CTO)* *(added)* This run read four things beyond the PRD, the SRS, the UXD, the
  Agari and the project's doctrine. It read tracker16-X's code under
  `task-tracker-X/tasktracker16x/`, to draw § 3's seams against the
  code SRS C-5 prefers. It read the engineering doctrine under `<CORE>/doctrine/engineering/`, for
  the Python frame and the test layers. It read `<CORE>/launchers/product-skeleton/launcher.sh`, to
  write § 3's tables in the form that tool reads. It searched `products/tracker17/docs/DESIGN.md`
  and `products/tracker17/docs/CONTENT.md` for a statement about scripts, focus or the console, to
  check for a collision, found none, and derived nothing from either.
- **RN-17:** *(CTO)* *(added)* § 5 step 3 found three orderings that are preferences and no
  dependency: `delete-and-rename` after `status-moves`, `delete-and-rename` after
  `comment-on-a-task`, and `protect-saved-data` last. Each is stated as a preference in its slice's
  *Why here in the order* and has no `depends_on` row in § 7 — *because* each of those slices can be
  built without the slice it is placed after. *(re: § 6, § 7)*
- **RN-18:** *(CTO)* *(added)* The answer to `trail/sdd/cycle-1.md` § 2.1 confirmed the runtime and
  added four things — *because* each closes a gap between the draft and a settled document or the
  owner's machine. First, the tracker needs no network connection, and the one-time connection of
  SRS FR-4 and UXD UX-S1 belongs to setting up the test suite. The draft's RT-4 said "so running
  the suite adds no prerequisite", which left the setup instructions nowhere to put FR-4's line.
  Second, the test dependencies go into a virtual environment made with `venv`. On the owner's
  machine the installer refuses outside one: `python3 -m pip install --no-index --no-deps
  zz-tracker17-no-such-package` printed `error: externally-managed-environment` on 2026-10-06.
  Third, a `python3` below the floor is a missing prerequisite that the setup instructions carry,
  and OB-2 is scoped to a start the tracker itself refuses. The answer's reasoning weighed a
  version check with its own message in `main.py` and did not take it, because that message would
  be a fourth start failure where UXD UX-S2 lists three
  (`products/tracker17/docs/trail/sdd/self_answer-1.md`, "Close calls"). Fourth, § 11 R-8 records that nothing checks the floor. The card's
  `**Setup command:** none` line (`system/projects/tracker17/project.md`) is written before a
  virtual environment exists, and follows this document the way RN-15 says the `Languages:` line
  does. *(re: § 4 RT-1, RT-4, OB-2, § 11 R-8, `first-project`; source: SRS FR-4, C-7; UXD UX-F1,
  UX-S1, UX-S2)*
- **RN-19:** *(CPO)* *(added)* The answer to `trail/sdd/cycle-1.md` § 2.2 confirmed macOS and Linux
  and added three things — *because* the draft's reason proved less than it claimed. The draft
  excluded Windows because the owner's check never reaches it, and that check never reaches Linux
  either. On the answer's reasoning, what separates the two is the building: under § 4 RT-1 one
  lock serves both Unix systems, and Windows would need a second
  (`products/tracker17/docs/trail/sdd/self_answer-2.md`, "one lock serves both"). The answer therefore keeps Linux named, says only
  macOS is checked, gives an unsupported system to the setup instructions as a missing
  prerequisite, and has nothing built or tested for Windows. § 11 R-9 records that nothing checks
  Linux. *(re: § 4 RT-3, § 11 R-9, `first-project`; source: SRS FR-4, NFR-3; UXD UX-F1)*
- **RN-20:** *(CDO)* *(changed)* The answer to `trail/sdd/cycle-1.md` § 2.3 overrode the draft in
  part. It kept the page model: no page runs a script, and every action is answered by a whole
  page. It replaced two of the draft's three consequences — *because* the draft read UXD UX-F4's
  "stays where they were" as the same page at the same address, and UX-F4 goes on "with the row or
  page showing the new status". An operator shown the top of a long list after moving a task far
  down it has not stayed where they were. UX-I3 puts a reason "beside the control that was used",
  and a reason beside a control that has scrolled out of view tells the operator nothing. The page
  an action opens therefore starts at the place of the action, with keyboard focus there (§ 4
  EX-4, EX-5). The draft also said nothing announces a completion line or a refusal apart from the
  page. The answer makes the line the accessible description of the element the page opens on
  (§ 4 EX-14), which keeps UXD UX-A5's "announced to assistive technology without moving focus"
  true on a page load. The confirmation of UX-I2 stays its own page load and gains three
  conditions (§ 4 EX-6). Two costs are accepted and § 9 TO-2 records them. Where a test shows a
  page with no script cannot hold these conditions, the conditions stand and § 11 R-2's fallback
  applies. The CDO's reasoning also accepts that a reload, or a return through back, shows the
  completion line again (`products/tracker17/docs/trail/sdd/self_answer-3.md`, "shows the
  completion line again and opens at the same place"). *(re: § 4 EX-2, EX-4, EX-5, EX-6, EX-14,
  § 9 TO-2, § 11 R-2; source: UXD UX-F4, UX-I2, UX-I3, UX-A5)*
- **RN-21:** *(CTO)* *(added)* The means by which a page opens at a place, and what the answer to
  § 2.3 does to the order — *because* that answer leaves both to the CTO: "what that does to the
  order is the CTO's". The place, the completion line's subject, the reason and the typed text
  travel in the address (§ 4 RT-8). This follows from RT-7 and RT-8 as first written: a tracker
  that keeps nothing between requests and answers every submission with an address has nowhere
  else to put them. Focus is set with `autofocus`, and the address carries no fragment, because
  the HTML standard skips `autofocus` when a fragment names an element (§ 4 RT-9). The order does
  not change. § 11 R-2 is now tested earlier than `status-moves`: on a form control in
  `first-project`, and on an element that is not a control in `tasks-in-a-project`, which gains a
  `validates` row in § 7. No `depends_on` row moves. *(re: § 4 RT-8, RT-9, § 6, § 7, § 9 TO-7,
  § 11 R-2; source: UXD UX-I2, UX-I3, UX-I4)*
- **RN-22:** *(CTO)* *(added)* § 4 RT-10's maximum lengths were drafted for the CPO to answer, and
  were confirmed with two additions, which RN-24 carries — *because* RT-8 puts typed text in an
  address, the listener refuses an address longer than 65,536 bytes (§ 11 R-10), and when the draft
  was written no upstream document bounded any text. What the product accepts as a title or a
  comment is product scope. The lengths, 200 and 4,000 characters, were this document's values and
  are now SRS FR-40's. They are sized so that the longest form fits: 4,200 characters at 12 bytes
  each is 50,400 bytes. *(re: § 4 RT-10, § 9 TO-7, § 11 R-10; source: SRS FR-40; PRD § Core
  Features)*
- **RN-23:** *(CTO)* *(added)* The round that folded the answers read five things beyond the inputs
  RN-16 lists. It read the three reasoning reports in `products/tracker17/docs/trail/sdd/`. It
  read https://html.spec.whatwg.org/multipage/interaction.html for the two sentences § 4 RT-9
  quotes. It read the source of `http.server` on the machine's Python 3.14.7 for the limit § 11
  R-10 quotes. It ran the installer command RN-18 quotes. It searched
  `products/tracker17/docs/DESIGN.md` and `products/tracker17/docs/CONTENT.md` for a rule that
  shortens long text, and found the opposite: `DESIGN.md` § Layout says "Long text wraps, and the
  stylesheet shortens nothing".
- **RN-24:** *(CPO)* *(added)* The answer to `trail/sdd/cycle-2.md` § 2.1 confirmed the maximum
  lengths at the drafted values and added two things — *because* the draft's own mechanism left two
  cases open (`products/tracker17/docs/trail/sdd/self_answer-4.md`, "Addition (1)" and "Addition
  (2)"). First, a value the tracker's own field let the operator enter is never refused as too
  long. The known case is a line break: a multi-line field counts it as one character and the
  browser sends it as two, so the field and `domain` must count the same text the same way, and
  RT-10 says what it counts as one character so that its 12 bytes for each character holds. The
  means are the CTO's, and RN-25 carries them. Second, the over-long refusal is the one refusal
  whose page does not carry the typed text, because that text is what an address cannot hold, and
  its page still opens and still says why (§ 4 RT-8, RT-10). Only a request the tracker's own pages
  did not send can reach it, so UXD UX-I3 holds on every form. The answer carried two consequences
  to other documents: the lengths as a system requirement, which the SRS now states as FR-40 (SRS
  RN-21), and whether a page tells the operator a field's maximum, which is the UXD's
  (`products/tracker17/docs/UXD_open_issues.md` § 2.1, unanswered on 2026-10-06). The answer's
  reasoning weighed holding RT-10 out of this document until the SRS stated the rule, and did not,
  because § 11 R-10 needs its response whichever document states the rule first
  (`self_answer-4.md`, "Close calls"). *(re: § 4 RT-8, RT-10, § 9 TO-7, § 11 R-10; source: SRS
  FR-39, FR-40; UXD UX-I3; PRD § Core Features)*
- **RN-25:** *(CTO)* *(added)* How the field and the rule come to count the same text, and four
  points the answer's reasoning named as the CTO's (`self_answer-4.md`, "Named and not covered") —
  *because* the answer fixed the outcome and left the means to this seat. One character is one
  Unicode code point, counted on the value as it would be saved, spaces included, so that § 4 SD-5's
  check at start counts what the rule counted. `web` turns each submitted line break back into the
  one line-feed character the field counted, because the second character is the form submission's
  and not the operator's, and reading form fields is `web`'s (§ 3). The lengths live once in
  `domain` and reach `web` through `application` as plain values across `SM-1`, so no second copy
  can drift. The over-long refusal's address is keyed on the refusal's type, which `web` already
  maps to a reason (§ 4 OB-4), so `web` compares no length. On the four points: a character outside
  the Basic Multilingual Plane counts two in the field and one in the rule, so the field is the
  stricter and may stop before the stated number, which refuses nothing (§ 11 R-11); the size of a
  request body is not bounded, because § 4 SEC-2 leaves the operator as the only party who can send
  one and no SRS requirement asks for a bound; surrounding spaces are counted, as above; and what
  Chromium does with a paste longer than a field's maximum is not tested here and is the UXD's
  question. One alternative the reasoning noticed, answering a refused form on the spot so that
  typed text never enters an address, was not taken, because § 4 RT-8 answers every submission with
  an address so that reload, back and forward never repeat an action (SRS NFR-4). *(re: § 4 RT-8,
  RT-10, § 11 R-10, R-11; source: SRS FR-40, NFR-4; UXD UX-I3)*
- **RN-26:** *(CTO)* *(changed)* The document's references to the SRS caught up with
  `products/tracker17/docs/SRS.md` version 4, and § 10 RC-1 records what moved — *because* the SRS
  changed upstream after this cut was made, and a settled document is revised on an upstream
  change. Five citations named an SRS open question by its position in a list that no longer
  exists, and RT-10 said no SRS requirement bounded text. Each now cites the SRS text that stands
  (FR-40, RN-21, RN-23). The tests the SRS added are placed where their fields first exist: the
  description half of AC-20 and AC-12's over-long refusal in `first-project`, the comment half of
  AC-20 in `comment-on-a-task`, AC-15's stated lengths in `tasks-in-a-project`, where the timed run
  first exists, and DR-6's over-long saved value in `protect-saved-data`, which already owns one
  test for each kind of break. The split of AC-20 follows § 5 step 5: RT-10's count of a line break
  is first falsified in the first slice, on the description, rather than in the third.
  `trail/sdd/cycle-2.md` § 2.2 raised this catch-up as a choice for the CTO's seat, and its answer
  slot is empty. This run made the change without one, because the SRS it reads is the authority
  for what the SRS says, and because the item's proposal was written against SRS version 3, and
  version 4 has since closed the open question the item proposed citing by subject. No requirement
  changes, and no slice changes its slug, its *Delivers* or its place. *(re: § 4 RT-1, RT-8, RT-10,
  TS-3, TS-5, § 6, § 10, RN-3, RN-4, RN-22; source: SRS FR-39, FR-40, DR-6, NFR-1, AC-7, AC-12,
  AC-15, AC-20, RN-21, RN-23)*
- **RN-27:** *(CTO)* *(added)* The round that folded the second answered round read six things
  beyond the inputs RN-16 and RN-23 list. It read `products/tracker17/docs/trail/sdd/self_answer-4.md`,
  the reasoning behind the answer to cycle-2 § 2.1. It read
  `products/tracker17/docs/UXD_open_issues.md`, because that answer routed a question there, and
  found its item 2.1 unanswered on 2026-10-06. It read https://infra.spec.whatwg.org/,
  https://html.spec.whatwg.org/multipage/form-control-infrastructure.html and
  https://html.spec.whatwg.org/multipage/form-elements.html for the sentences § 4 RT-10 quotes. It
  ran `urllib.parse.quote` on the machine's Python 3.14.7, which returned 12 bytes for U+1F600 and
  3 for a line feed, and printed the three lines of `http.server` around `65536` that § 11 R-10
  quotes. It searched `products/tracker17/docs/DESIGN.md` and `products/tracker17/docs/CONTENT.md`
  for a rule about length, line breaks or multi-line fields, and found one the design rests on:
  `DESIGN.md` § Components, "a comment is multi-line and keeps the line breaks the operator typed".
- **RN-28:** *(CTO)* *(changed)* § 4 SEC-2 refuses a request the browser marks `same-site`, and a
  form submission it does not mark `same-origin`, where it refused only a request "from another
  site". SEC-3's policy travels as a response header and forbids framing, where it named a tag or a
  header and said nothing of frames — *because* SRS NFR-4 says the tracker "refuses any request
  that does not come from its own pages" and that a page from another origin "cannot read, change
  or delete tracker data", and SEC-2 as written fell short of both on two readings that were
  checked against the standards on 2026-10-07. First, a site is wider than the tracker's own pages:
  for a host that is an address and not a name, the HTML standard's site is the scheme and the host
  with no port ("If origin's host's registrable domain is null, then return (origin's scheme,
  origin's host)", https://html.spec.whatwg.org/multipage/browsers.html, "obtain a site"), so a
  page served by any other program on the loopback address, on another port, is `same-site`, and
  "another site" let its submissions through. Second, SEC-3's policy did not stop another origin
  from framing a tracker page and leading the operator's own click to a submission the browser
  marks `same-origin`: "A policy that declares `default-src 'none'` still allows the resource to be
  embedded by anyone", and the directive that stops it "is not supported in the `<meta>` element"
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors),
  which is why the policy is a header. The browser sends the mark to the tracker: the header "is
  only included in requests to potentially trustworthy URLs"
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Site), and a host
  in `127.0.0.0/8` is a potentially trustworthy origin
  (https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts). A request from
  the address bar or a bookmark is marked `none` (the `Sec-Fetch-Site` page above), so only a
  submission is held to `same-origin`, or the tracker could not be opened. The two readings reached
  this document as `products/tracker17/docs/SDD_open_issues.md` §§ 2.1 and 2.2, committed at
  `86c8acfb0` by a `companion-self-answer` run that was answering
  `products/tracker17/docs/architecture_open_issues.md` §§ 2.1 and 2.2 in the owner's seat; those
  answers confirmed `products/tracker17/docs/nfdr.md` QC-32 and QC-33 with the additions SEC-2 and
  SEC-3 now carry, and their reasoning is `products/tracker17/docs/trail/architecture/self_answer-1.md`
  §§ 2.1 and 2.2. Both slots were empty, and this run made the change without one, as RN-26's round
  did, because § 4's data protection is this seat's call in § *Who decides what*, the ground is a
  settled requirement, and the readings were verified here. The NFDR did not authorize it: where § 4
  and `nfdr.md` disagree, § 4 wins (§ 12), and what moved § 4 is NFR-4 read correctly. No slice
  moves. The check is one function in `web`, SRS AC-10's tests already sit in `first-project`, and
  no edge in § 7 changes. A browser that sends no mark cannot submit a form; SRS NFR-13 names the
  supported browsers, and the header has "been available across browsers since March 2023" (the
  `Sec-Fetch-Site` page above). *(re: § 4 SEC-2, SEC-3, TS-1, TS-5; source: SRS NFR-4, NFR-5,
  NFR-13, AC-10)*
- **RN-29:** *(CTO)* *(changed)* § 12 refers to `products/tracker17/docs/adr/`, ADR-0001 to
  ADR-0009, and `products/tracker17/docs/nfdr.md`, where it said they did not exist — *because*
  both landed at commit `ab7a066ff`, after this document's version 3, and § 12's own text has this
  document refer to the records once they exist. The sentence is written as what is true now, with
  no claim about when it became true, under `<CORE>/doctrine/governance/written_forward.md` § 2.
  § 12 also states which store wins when the two disagree, which this round is the first case of.
  *(re: § 12)*
- **RN-30:** *(CTO)* *(added)* The round that settled the two choices read seven things beyond the
  inputs RN-16, RN-23 and RN-27 list. It read `products/tracker17/docs/SDD_open_issues.md` as
  intake found it. It read `products/tracker17/docs/architecture_open_issues.md` §§ 1.1 to 2.4 and
  `products/tracker17/docs/trail/architecture/self_answer-1.md`, for the owner's-seat answers and
  their reasoning. It read `products/tracker17/docs/nfdr.md` QC-32, QC-33, RN-3 and RN-4, and
  `products/tracker17/docs/adr/README.md` with the status line of each of the nine records. It read
  the four web pages RN-28 cites. It read `products/tracker17/docs/UXD_open_issues.md` and found its
  items 2.1 and 2.2 unanswered on 2026-10-07. It read the commit history of this document, its
  companion and the architecture records, for the order in which version 3, the records and the
  companion landed. It did not read `products/tracker17/docs/DESIGN.md` or
  `products/tracker17/docs/CONTENT.md` this round, because nothing it changed names a word a page
  shows or a value the stylesheet sets.
- **RN-31:** *(CDO)* *(changed)* The behaviour lines of `first-project`, `tasks-in-a-project` and
  `comment-on-a-task` follow UXD version 4 — *because* the UXD changed upstream, and these lines
  are drafted from it and settled by it: UX-F2, UX-F7 and UX-F9 as confirmed in
  `products/tracker17/docs/trail/uxd/cycle-3.md` §§ 2.1 and 2.2, with the reasoning in
  `products/tracker17/docs/trail/uxd/self_answer-3.md`. The line of `tasks-in-a-project` read "an
  assignee no longer on the list" as refused, which under UX-F9 as it now stands would refuse a save
  of every task carrying a removed name; UX-F9 refuses only an assignee changed to a name that left
  the list after the page loaded, and the line now says so. No item is raised, because the input
  settles the call. RN-24, RN-25, RN-27 and RN-30 record whether a page tells the operator a field's
  maximum as the UXD's question, unanswered on the dates they name; UX-F2 and UX-F7 answer it, and
  § 11 R-11 and § 10 RC-2 say so. *(re: § 6 `first-project`, `tasks-in-a-project`,
  `comment-on-a-task`; § 10 RC-2; § 11 R-11; source: UXD UX-F2, UX-F7, UX-F9, UX-S3, UX-S6)*
- **RN-32:** *(CTO)* *(added)* § 4 RT-7 has a form whose save must tell a changed field from one
  left as the page showed it carry the values the page showed, and RT-10 has the two sentences that
  state a maximum take their number from the same value as the field's `maxlength` — *because* UXD
  UX-F9 refuses an assignee "changed to a name that has left the list since the page loaded" and
  keeps one "left as the page showed it", and SRS NFR-3 has a stale edit replace what another tab
  saved "for that field". Both need the save to know what the page showed. RT-7 keeps nothing
  between requests, so the form is the only place that can carry it. Comparing the submitted value
  with the saved one instead would refuse a kept name whenever another tab had changed the
  assignee, and would write back every unchanged field of a stale page over what the other tab
  saved. The number beside a field is RT-10's one statement reaching `web` through `application`
  as it already does, so no second copy exists to drift (UXD UX-F2, "taken from the same place
  that sets the field's limit"). The command halves name one test for each: the kept name and the
  refused change in `tasks-in-a-project`, and the sentence's number against the field's
  `maxlength` in `first-project` and `comment-on-a-task`. Two downstream records were read as a
  check and not as a source: `products/tracker17/docs/fdr.md` R-47, R-48, R-115 and R-118 state the
  same saves, and `products/tracker17/docs/nfdr.md` QC-9 already binds the sentence's number to
  the field's `maxlength`. Neither moved § 4; what moved it is the UXD. *(re: § 4 RT-7, RT-10;
  § 6; source: UXD UX-F2, UX-F7, UX-F9; SRS NFR-3, FR-21, FR-22, FR-40)*
- **RN-33:** *(CTO)* *(added)* The round that caught up with UXD version 4 read seven things
  beyond the inputs RN-16, RN-23, RN-27 and RN-30 list. It read `git diff 35aec4aad HEAD --
  products/tracker17/docs/UXD.md`, the whole change to the UXD since this document's version 4. It
  read `products/tracker17/docs/trail/uxd/cycle-3.md` and
  `products/tracker17/docs/trail/uxd/self_answer-3.md`, the answered round and its reasoning. It
  read `products/tracker17/docs/nfdr.md` QC-9, RN-19 and RN-20, and
  `products/tracker17/docs/adr/README.md` with ADR-0007. It read `products/tracker17/docs/fdr.md`
  R-46 to R-49 and R-115 to R-118 with their Examples rows. It read
  `products/tracker17/docs/DESIGN.md` RN-14 and RN-26, which place the three new sentences as field
  hints, and searched `products/tracker17/docs/CONTENT.md` for "maximum", "characters" and "no
  longer on the list", which returned nothing; the UXD's round records that the verbal language's
  instruction form covers the sentences and their words are written when a change publishes them
  (`self_answer-3.md`, "`CONTENT.md` is owed nothing"). It read `git log 35aec4aad..HEAD --
  products/tracker17/docs/ system/projects/tracker17/` for the order in which the UXD, the design
  language and the NFDR moved. The SRS and the PRD are unchanged since this document's version 4:
  `git diff --stat 35aec4aad HEAD` on both printed nothing on 2026-10-07.
- **RN-34:** *(CTO)* *(changed)* § 4 TS-4 holds the pointer test to the feature words whose slice
  has landed, where it held it to every word in TS-3's table, and it fails in both directions: a
  landed word with no module, and a word with a module that is not listed as landed — *because*
  the table names eleven feature words and the first slice delivers one, so a test that fails on
  any word with no module cannot pass until the last slice lands, and a test that cannot pass for
  seven slices is not a test. The PM found it reading the test against the condition
  (`trail/sdd/cycle-3.md` § 5.1): `tests/architecture/test_trace.py` reads `LANDED_FEATURE_WORDS =
  ["projects"]` and checks those words, which was the one passable reading and the one TS-4 did
  not state. The answer confirmed the PM's wording and added the reverse direction, so that a
  slice which lands `domain/<word>.py` and forgets the list fails rather than leaving that
  feature's pointers unchecked. That is the drift § 11 R-6 names TS-4's test as the signal for,
  and the reasoning is `products/tracker17/docs/trail/sdd/self_answer-5.md` § 5.1. On the day of
  the fold the test has the first direction, `test_each_landed_feature_word_has_its_domain_module`,
  and not the reverse, so TS-4 states one check the code is owed, and R-6 names it. This is a
  correction of a condition and not a re-cut under § 10: no slice's *Reached when*, fence or place
  moves, and no edge in § 7 changes. SRS NFR-9 asks the trace of "every Core Feature the operator
  uses", which before the last slice is the features that exist, so no requirement moves. The NFDR
  states the same clause in QC-11's *verified by*, and
  `products/tracker17/docs/architecture_open_issues.md` § 3.1 already carries it to the Principal
  Architect; where the two disagree, § 4 wins (§ 12), so this document did not wait on that
  answer. *(re: § 4 TS-4, § 11 R-6; source: SRS NFR-9, AC-5)*
- **RN-35:** *(CTO)* *(added)* § 4 RT-5 records the address, `127.0.0.1:8017`, and § Open
  Questions no longer asks which port the fixed address uses — *because* `first-project` wrote
  the constant the question said would settle it: `main.py` reads `ADDRESS = ("127.0.0.1", 8017)`,
  and `tests/unit/test_address.py`, `test_the_address_host_is_loopback`, asserts the host is
  loopback and the port is 8017. The PM raised the port (`trail/sdd/cycle-3.md` § 5.2), and the
  answer recorded the whole address, because RT-5 said "one loopback address" and there is more
  than one, so the port alone would have left the host unstated while the code fixes both. No
  upstream document names a port: `grep -n "8017\|port " SRS.md PRD.md UXD.md` in
  `products/tracker17/docs/` printed nothing bearing on one on 2026-10-07. A later change of the
  address is a change to this document first, as every § 4 condition already is, and § 4 TS-1
  already has each end-to-end test start its tracker on a port of its own, so the recorded port
  touches no test. *(re: § 4 RT-5, TS-1, § 9 TO-6; source: SRS FR-2, FR-3)*
- **RN-36:** *(CTO)* *(changed)* § Open Questions no longer asks whether Chromium counts a line
  break as one character against `maxlength` and sends it as CR LF, and its `autofocus` question
  is narrowed to an element that is not a form control — *because* the end-to-end tests of
  `first-project` now pass and answer what each question put to them.
  `tests/e2e/test_first_project.py`,
  `test_a_description_of_4000_characters_with_line_breaks_is_saved_whole`, fills the description
  to 4,000 characters holding fifty line breaks, presses one more and finds the value unchanged,
  submits, and reads the saved description equal to what was typed: the field counted each line
  break as one, and the value reached the saved data whole. The same file's
  `test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description` finds
  focus in the name field and the reason as its accessible description, which is what § 11 R-2
  asks on a form control. Both passed at commit `691edf98b`, `pytest tests/e2e/` at 9 passed, exit
  0, and `git diff --stat 691edf98b HEAD -- products/tracker17 ':!products/tracker17/docs'`
  printed nothing when the round was answered, so the code they ran against is the code on `main`
  (`products/tracker17/docs/trail/sdd/self_answer-5.md`, Header). The PM raised both
  (`trail/sdd/cycle-3.md` § 5.3), and the answer added one sentence on how the first closes: the
  test does not observe whether Chromium sent CR LF, because `web/routes.py`, `_line_feeds`, turns
  CR LF and a lone CR into LF before the value reaches `application`, and
  `tests/integration/test_routes.py`, `test_line_breaks_in_a_description_are_saved_as_lf`, checks
  that on `"a\r\nb\rc\nd"`. The question closes because § 4 RT-10's design no longer turns on what
  the browser sends, not because CR LF was seen on the wire, and the standard's description of the
  submission stays in RT-10 as the standard's. § 11 R-2 keeps `first-project`'s test among its
  triggers, because a Chromium release could change either behaviour and both tests run on every
  slice. *(re: § 4 RT-9, RT-10, § 11 R-2, R-11, § Open Questions; source: SRS AC-20; UXD UX-I3,
  UX-A3)*
- **RN-37:** *(CTO)* *(added)* The round that folded the third answered round read these things
  beyond the inputs RN-16, RN-23, RN-27, RN-30 and RN-33 list. It read
  `products/tracker17/docs/SDD_open_issues.md` as intake found it, committed at `c3493c396` with
  all three answer slots filled, and `products/tracker17/docs/trail/sdd/self_answer-5.md`, the
  reasoning behind the answers. It read `main.py`, `tests/unit/test_address.py`,
  `tests/architecture/test_trace.py`, `web/routes.py`, `tests/integration/test_routes.py` and
  `tests/e2e/test_first_project.py`, to verify on disk each line the answers cite. It read
  `products/tracker17/docs/nfdr.md` QC-11 and `products/tracker17/docs/architecture_open_issues.md`
  § 3.1, for the NFDR's copy of TS-4's clause, and `products/tracker17/docs/adr/README.md` for the
  status of the nine records. It ran no suite: the answers rest on recorded runs, and this round
  changed no code. It did not read `products/tracker17/docs/DESIGN.md` or
  `products/tracker17/docs/CONTENT.md`, because nothing it changed names a word a page shows or a
  value the stylesheet sets.
- **RN-38:** *(CTO)* *(added)* § 4 RT-4 names the system libraries the browser needs on Linux, the
  one command that installs them with the browser, and the Linux systems the end-to-end suite runs
  on; § 4 RT-3 says the suite runs on fewer Linux systems than the tracker; § 6 `first-project`'s
  *Artifact* holds that line; and § 11 R-9 is narrowed from "nothing checks it" to a green
  end-to-end run — *because* R-9's own settling run happened and settled half of what it named. The
  PM ran the setup instructions in a fresh copy on Debian 12 aarch64 on 2026-10-08
  (`trail/sdd/cycle-4.md` § 5.1): the tracker served and `pytest tests/` passed 224, so the tracker
  needs no code of its own for Linux, as RT-3 said; `pytest tests/e2e/` could not start its browser
  for want of `libglib-2.0.so.0`, a library of the operating system that the prerequisites did not
  name. Debian 12 is on the pinned library's own supported list, so this was a missing
  prerequisite, not an unsupported machine and not a tracker defect. The library's documented
  remedy is the command RT-4 now gives: `playwright install --with-deps chromium` installs "the
  browsers and OS dependencies" in one step, and on Linux "Playwright will attempt to become a
  root", so it asks for administrator rights (https://playwright.dev/python/docs/browsers, "Install
  system dependencies", read 2026-10-08). The item offered a second answer, naming Linux for the
  tracker and not for the suite, and the answer took only its bound: withholding a one-line fix from
  every Debian and Ubuntu reader was judged worse than giving the suite a narrower list than the
  tracker. The reasoning is `products/tracker17/docs/trail/sdd/self_answer-6.md` § 5.1. RT-3's
  "checked on macOS only" stays in the instructions, because the Agari's check reaches only macOS
  and no end-to-end run has passed on Linux. Nothing settled upstream moves: SRS FR-4 has the
  prerequisites say setup needs a network connection once "to fetch the declared dependencies
  (§ 5.3)", and § 5.3 lets setup fetch from "public sources that need no account, key or sign-up",
  which a distribution's package repository is; SRS C-7's three-command bound and AC-3 cover the
  tracker's setup, which RT-2 keeps at two commands and the suite's section is outside; SRS C-8
  fixes the declared dependencies, and the system libraries are not among them, which RT-4 says so
  that a reader does not look for a pin. This is a correction of a condition and of the artifact
  bar that reads it, not a re-cut under § 10: `first-project`'s *Artifact* could be met as written,
  and the slice's place, fence and § 7 edges do not move. One record downstream reads thinner now:
  `products/tracker17/docs/adr/0009-one-unix-lock-no-windows.md` § Consequences says "Linux is named
  as supported and nothing checks it (SDD § 11 R-9)". The tracker's prerequisites are still one set
  and the Agari's check still does not reach Linux, so on this reading neither sentence is false.
  The record is the Principal Architect's to re-read against R-9 as narrowed, and where the two
  disagree § 4 wins (§ 12). *(re: § 4 RT-3, RT-4; § 6 `first-project`; § 11 R-9; source: SRS FR-4,
  § 5.3, C-7, C-8, NFR-13, AC-3)*
- **RN-39:** *(CTO)* *(added)* § 6 `first-project`'s *Artifact* has the suite's section say that the
  full suite needs the copy to be a Git repository with `git` on the path, and say what the one test
  that does not pass otherwise checks — *because* `tests/integration/test_start.py`,
  `test_data_is_ignored_by_version_control`, runs `git check-ignore -q data/tracker.json` from the
  product root and asserts exit 0. Outside a repository Git exits 128 and the test fails; with no
  `git` on the path `subprocess.run` raises and the test errors. The PM measured the first in a copy
  made with `git archive`: `pytest tests/` gave `1 failed, 223 passed`, that test the one failure
  (`trail/sdd/cycle-4.md` § 5.1). The test checks a property of a repository, that SRS FR-6's "never
  committed to version control" holds for `data/`, so the honest statement is that the suite needs
  one. It is named as a prerequisite of the suite and not of the tracker, because the tracker's
  setup needs no Git and a downloaded copy runs it; SRS C-7's bound is untouched. The answer weighed
  making the test skip outside a repository and did not take it: a skip reads green in exactly the
  copy where the property cannot be checked, where the instructions' sentence makes the absence
  visible. `products/tracker17/README.md`, "Running the tests", already carries that sentence ("In a
  copy that isn't a Git repository, such as one unpacked from a download, one test doesn't pass.
  That test checks that Git ignores the saved data."), so the artifact and its bar agree on the day
  of the fold. The reasoning is `products/tracker17/docs/trail/sdd/self_answer-6.md` § 5.1. *(re:
  § 6 `first-project`; source: SRS FR-6, C-7, NFR-11)*
- **RN-40:** *(CTO)* *(added)* The round that folded the fourth answered round read these things
  beyond the inputs RN-16, RN-23, RN-27, RN-30, RN-33 and RN-37 list. It read
  `products/tracker17/docs/SDD_open_issues.md` as intake found it, committed at `7c6137157` with its
  one answer slot filled, and `products/tracker17/docs/trail/sdd/self_answer-6.md`, the reasoning
  behind the answer. It read `products/tracker17/README.md` whole, `tests/requirements.txt`,
  `pyproject.toml`, `tests/integration/test_start.py` and `tests/e2e/conftest.py`, to verify on disk
  each line the answer cites. It read `products/tracker17/docs/SRS.md` FR-4, FR-6, § 5.3, NFR-11,
  NFR-13, C-7, C-8, AC-2, AC-3 and RN-23, for what the answer says does not move;
  `products/tracker17/docs/adr/0009-one-unix-lock-no-windows.md` and
  `products/tracker17/docs/adr/README.md`, for the record RN-38 names; and
  `products/tracker17/docs/nfdr.md`'s header and
  `products/tracker17/docs/architecture_open_issues.md` § 3.1, for the state of the downstream
  records. It re-read the two pages the answer rests on, at
  the source, on 2026-10-08: https://playwright.dev/python/docs/intro, "System requirements", which
  lists "Debian 12 / 13, Ubuntu 22.04 / 24.04 / 26.04 (x86-64 or arm64)", and
  https://playwright.dev/python/docs/browsers, "Install system dependencies", which gives
  `playwright install --with-deps chromium` and says "Playwright will attempt to become a root". It
  ran no suite: the answer rests on the PM's recorded run, and this round changed no code. It did
  not read `products/tracker17/docs/DESIGN.md` or `products/tracker17/docs/CONTENT.md`, because what
  this round changed states what the setup instructions hold and not how a sentence of theirs is
  worded, which the standard those two files set reaches when a change writes the words.
- **RN-41:** *(CTO)* *(changed)* § 11 R-2 says which of its three cases are verified and which are
  not, where it said the not-a-control case was "not verified here"; § Open Questions keeps only
  the two cases still open; and § 6 `tasks-in-a-project`'s *Why here in the order* says R-2 left
  the case unverified until this slice's People half ran — *because* R-2's own second test has run
  and passed. The PM found it reading R-2 against the suite (`trail/sdd/cycle-5.md` § 5.1):
  `tests/e2e/test_people.py`, `test_added_markup_name_has_browser_focus_and_accessible_description`,
  asserts in Chromium that the added name, a `span`, holds keyboard focus, is in the viewport and
  has the completion line as its computed accessible description, with no script on the page, and
  it passed on `main` at `641bb58b5`. The answer, given in the CTO's seat, narrowed both places as
  the item asked and added four things, with the reasoning in
  `products/tracker17/docs/trail/sdd/self_answer-7.md` § 5.1. First, the precision `tabindex="-1"`:
  the standard makes `autofocus` apply to all elements, and only a focusable element takes focus,
  so a narrowing written from the item's words alone would claim more than the test shows. Second,
  the heading after a removal is a second element that is not a control, verified by the same
  file's `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action`. Third, the standard
  promises focus and no more, re-read at the source on 2026-10-11 (`self_answer-7.md`, Header), so
  in view and described are Chromium's behaviour as measured and not the standard's. Fourth,
  assistive-technology speech keeps a settling path, one VoiceOver pass on the owner's macOS
  machine, which no slice requires, in the form R-8 and R-9 use, because an open question with no
  settling path is a hole. The measurement was re-made in a disposable copy of `7653f25c8` rather
  than read off the record, 18 passed with the pinned library, and this round checked that no code
  moved between that commit and `main` at `1bdfc68fe` (RN-44), so the recorded runs stand against
  the code on `main` and this round ran no suite. The two passing tests stay among R-2's triggers,
  as RN-36 keeps `first-project`'s, because a Chromium release could change the behaviour. Nothing
  settled moves: UXD UX-A5 and § 4 EX-14's mechanism stand as written, the answer says only what is
  and is not proven about them, and the no-script decision (§ 4 EX-2, § 9 TO-2, ADR-0003) does not
  move. § 7's `validates` row for `tasks-in-a-project` describes what the test shows and stays
  true. One record downstream reads thinner now:
  `products/tracker17/docs/adr/0003-no-script-in-any-page.md` § Consequences, Dependence, says the
  not-a-control case "is not verified"; `products/tracker17/docs/architecture_open_issues.md` § 3.1
  already carries the same narrowing to the Principal Architect, and where the two disagree § 4
  wins (§ 12). This is a correction of a risk's statement and not a re-cut under § 10: no slice's
  *Reached when*, fence or place moves, and no edge in § 7 changes. *(re: § 6
  `tasks-in-a-project`; § 11 R-2; § Open Questions; source: UXD UX-A5, UX-I4; SRS NFR-13)*
- **RN-42:** *(CPO)* *(changed)* § 1 names tracker17's second purpose and the one exception to the
  predecessor rule, and `first-project`'s *Traces to* names PRD § Purpose — *because* the PRD
  changed upstream, and § 1 and the PRD entries of *Traces to* are drafted from it and settled by
  it. PRD version 5 adds `critical` and names Priorities as "The one exception" to the rule that
  tracker17 behaves as its predecessor does (`products/tracker17/docs/trail/prd/cycle-5.md` § 1.1,
  the owner's answer). Version 6 gives tracker17 its second purpose and has a reader learn both
  from the first thing they read (`products/tracker17/docs/trail/prd/cycle-6.md` § 1.1). No item is
  raised, because the input settles the call, as RN-1 read § 1 and RN-31 read the UXD's change.
  § 1's new sentence says the second purpose adds no part to this design, on the SRS's own reading
  that it "adds no behaviour to the tracker" (SRS RN-18), and this document holds no part, seam,
  condition or slice that exists for it. *(re: § 1; § 6 `first-project`; source: PRD § Blurb,
  § Purpose, § Core Features, preamble and Priorities; SRS § 1, RN-18)*
- **RN-43:** *(CTO)* *(changed)* The document's references to the SRS caught up with
  `products/tracker17/docs/SRS.md` version 6, and § 10 RC-3 records what moved — *because* the SRS
  changed upstream after the fourth round was folded, and a settled document is revised on an
  upstream change, as RN-26 did for version 4. Two things reach this document. FR-41 is a
  requirement on the setup instructions' opening paragraph, and `first-project` is the slice whose
  *Artifact* is those instructions, so its *Artifact* now holds the paragraph and its *Traces to*
  names FR-41. AC-21 is an inspection and names no test, so the command half does not change. The
  paragraph lands in a slice that has already been walked, which RC-1's placing of AC-20's tests
  also did, and the Status section of `products/tracker17/README.md` already says the paragraph is
  owed, so the artifact bar and the product's own statement of what is left agree on the day of the
  fold. The priority set reaches § 11 R-5 as a third place a carried-over rule differs from
  tracker16-X's, and nowhere else: this document never enumerated the set, and RC-3's *Retained*
  line names the three places it comes close. SRS RN-19 still names the two places R-5 cited, so
  that citation stands. § 4 TS-3's `priorities` row keeps FR-15, FR-16 and FR-36, which the SRS
  renumbered nothing of. No requirement changes, and no slice changes its slug, its *Delivers* or
  its place. *(re: § 1; § 6 `first-project`; § 10 RC-3; § 11 R-5; source: SRS § 1, FR-15, FR-36,
  FR-38, FR-41, C-5, AC-21, RN-18, RN-24, RN-25)*
- **RN-44:** *(CTO)* *(added)* The round that folded the fifth answered round read these things
  beyond the inputs RN-16, RN-23, RN-27, RN-30, RN-33, RN-37 and RN-40 list. It read
  `products/tracker17/docs/SDD_open_issues.md` as intake found it, committed at `1bdfc68fe` with its
  one answer slot filled, and `products/tracker17/docs/trail/sdd/self_answer-7.md`, the reasoning
  behind the answer. It read `tests/e2e/test_people.py`, `tests/e2e/conftest.py`,
  `tests/requirements.txt` and `web/pages.py`, to verify on disk each line the answer cites. It ran
  `git diff --stat 7653f25c8 1bdfc68fe -- products/tracker17 ':!products/tracker17/docs'`, which
  printed nothing, and `git log` on `products/tracker17/docs/SRS.md`, `PRD.md` and `UXD.md`, for
  the versions that landed since this document's version 7: SRS version 5 at `083aa6d92`, version
  6 at `b72ea80e6`, PRD version 5 at `29352d2fc`, version 6 at `cafd1cb92`, and the UXD unchanged at
  version 4. It read `products/tracker17/README.md`, its opening paragraph and Status section, for
  what the setup instructions say of the second purpose today. It read
  `products/tracker17/docs/adr/0003-no-script-in-any-page.md` and
  `products/tracker17/docs/adr/README.md`, for the record RN-41 names, and
  `products/tracker17/docs/nfdr.md`'s header and
  `products/tracker17/docs/architecture_open_issues.md` § 3.1, for the state of the downstream
  records. It ran no suite: the answer rests on two recorded runs, the diff above shows no code
  moved since the later one, and this round changed no code. It did not read
  `products/tracker17/docs/DESIGN.md` or `products/tracker17/docs/CONTENT.md`, because what this
  round changed states what the setup instructions hold and what a risk has verified, and names no
  word a page shows or a value the stylesheet sets.
- **RN-45:** *(CTO)* *(changed)* § 3's `application` row qualifies the save-then-make-current
  sequence to an action whose `domain` outcome reports a change, says that an action reporting none
  returns the current state and saves nothing, and names what the report compares, where it said
  every action saves the new state — *because* the product no longer saves on every action, and the
  PM found the row false against it (`trail/sdd/cycle-6.md` § 5.1). `application/tracker.py`,
  `Tracker.edit_task`, saves on `outcome.changed` and on nothing else, and its docstring says "one
  that reports none saves and publishes nothing". `domain/tasks.py`, `edit_task`, returns the state
  as it came with `changed=False` when no submitted field differs from what the page showed.
  `tests/integration/test_task_tracker.py`, `test_tracker_unchanged_edit_never_saves`, finds no save
  and the state untouched. The answer, given in the CTO's seat, took the item's wording and added
  two things, with the reasoning in `products/tracker17/docs/trail/sdd/self_answer-8.md` § 5.1.
  First, the bound: the report is `domain`'s comparison of submitted against shown (§ 4 RT-7), never
  of the new state against the current one, so a field changed to the value another tab already
  saved reports a change and saves a state equal to the current one, one whole write under § 4 SD-3
  with nothing lost, and `application` compares nothing. Without that sentence a reader would "fix"
  the row with a state comparison, which would hand `application` a rule. Second, what does not
  move: § 4 SD-2 and SRS FR-9 bind the done report to the disk, and an action reporting no change
  reports nothing done. `web/routes.py` adds `saved` to the address only on `outcome.changed`,
  which is FDR R-116 and UXD UX-I4's "A result is shown only once it is saved". § 9 TO-3 already
  says "on every change". SRS NFR-3's stale edit replaces "for that field", and an unchanged field
  is not written. The row's *Must not own* stands as written, because which outcomes report none is
  `domain`'s, decided per action and read off the outcome. Today the edit is the one action that
  reports. A move to the status a task already has is a refusal (SRS FR-18, RN-2), not a no-change
  outcome, and FDR R-65's label already carried will be the second action to report none, which the
  row covers without naming it. § 2's summary of the shape, "applies them to the tracker's current
  state and saves the result", is read as the layer's job and not as the per-action sequence, which
  § 3's row states, so it is not changed. The same sentence in `products/tracker17/docs/nfdr.md`
  QC-21 and in `products/tracker17/docs/adr/0001-rule-core-behind-server-rendered-pages.md`
  § Decision is the Principal Architect's and is already
  `products/tracker17/docs/architecture_open_issues.md` § 3.1, unanswered on 2026-10-12. This
  document did not wait on that answer, as RN-34's round did not: downstream is rebuilt from
  upstream (§ 12). This is a correction of a part's description and not a re-cut under § 10, as
  RN-34 and RN-41 were: no slice's *Reached when*, fence or place moves, and no edge in § 7 changes.
  *(re: § 3, the `application` row; source: SRS FR-9, FR-18, NFR-3; UXD UX-I4; FDR R-65, R-116)*
- **RN-46:** *(CTO)* *(added)* The round that folded the sixth answered round read these things
  beyond the inputs RN-16, RN-23, RN-27, RN-30, RN-33, RN-37, RN-40 and RN-44 list. It read
  `products/tracker17/docs/SDD_open_issues.md` as intake found it, committed at `65f0bb1a4` with its
  one answer slot filled, and `products/tracker17/docs/trail/sdd/self_answer-8.md`, the reasoning
  behind the answer. It read `application/tracker.py`, `application/contracts.py`, `domain/tasks.py`,
  `web/routes.py` and `tests/integration/test_task_tracker.py`, to verify on disk each line the
  answer cites. It read `products/tracker17/docs/SRS.md` FR-9, FR-18, NFR-3 and RN-2,
  `products/tracker17/docs/UXD.md` UX-I4 and UX-S6, and `products/tracker17/docs/fdr.md` R-65,
  R-116, R-117 and RN-12, for what the answer says does not move;
  `products/tracker17/docs/nfdr.md` QC-21 and
  `products/tracker17/docs/adr/0001-rule-core-behind-server-rendered-pages.md`, for the two
  downstream copies of the sentence; and `products/tracker17/docs/nfdr.md`'s header,
  `products/tracker17/docs/adr/README.md` and
  `products/tracker17/docs/architecture_open_issues.md` § 3.1, for the state of the downstream
  records. It read the headers of the PRD, the SRS and the UXD, which stand at the versions
  version 8 read, 6, 6 and 4. It ran `git diff --stat 8315df674 65f0bb1a4 -- products/tracker17
  ':!products/tracker17/docs'`, which listed two lines of `products/tracker17/README.md` and no
  code, so the code the answer read at `8315df674` is the code on `main`. It ran no suite: the item
  is about what the code says, which was read on disk, and this round changed no code. It read the
  status lines of `products/tracker17/docs/DESIGN.md` and `products/tracker17/docs/CONTENT.md` and
  nothing more of either, because what this round changed describes a part and names no word a
  page shows or a value the stylesheet sets.
- **RN-47:** *(CTO)* *(changed)* § 3's `application` row names what a reporting action's outcome
  compares, decided by `domain` per action, where it said the report is always the comparison of
  the value submitted with the value the page showed — *because* two actions that landed after
  version 9 compare with the state at the moment of the action, and the PM found the row false
  against the first of them (`trail/sdd/cycle-7.md` § 5.1). `domain/operator_name.py`,
  `set_operator_name`, returns the state as it came with `changed=False` when the checked name
  equals `state.operator_name` (its docstring: "A name exactly equal to the saved one returns the
  original state and `changed=False`"), and the People form carries no shown-name value:
  `tests/integration/test_people_routes.py`,
  `test_stale_people_name_submission_compares_with_current_name`, asserts the form's only input is
  `name` and that a stale page's repeat of the saved name saves nothing. `application/tracker.py`,
  `set_operator_name`, saves on `if outcome.changed:` and on nothing else. The answer, given in the
  CTO's seat, took the item's wording and added two things, with the reasoning in
  `products/tracker17/docs/trail/sdd/self_answer-9.md` § 5.1. First, the label is the same shape:
  `domain/tasks.py`, `add_task_label`, checks the label "against the labels it carries now" and
  returns `changed=False` for one already carried, which `tests/unit/test_tasks.py`,
  `test_duplicate_task_label_reports_no_change`, asserts. Labels landed at `25fff47d2` and the
  operator name at `cb48338e3`, both after version 9 (`33ad1a2a7`), so RN-45's "Today the edit is
  the one action that reports" and its "will be the second action to report none" are a dated
  record of that round and stay as written. The row now names the comparison per action instead
  of enumerating the actions, so it stays true when a fourth action reports. Second, what does not
  move. § 4 RT-7 already gives the shown-value form to the task edit alone ("The task's edit form
  is that form") and is not changed. SRS NFR-3 is the source of the saved-state rule ("Every action
  is checked against the saved data at the moment it is applied, not against what the page
  showed"), and the task edit is its stated exception ("replaces whatever the other tab saved for
  that field"), so the row's per-action split traces to a requirement and not to the code. § 4 SD-2
  and SRS FR-9 stand: an action reporting no change reports nothing done, and `web/routes.py`
  opens plain People with no completion line when `outcome.changed` is false (`if not
  outcome.changed:`), which `tests/integration/test_people_routes.py`,
  `test_same_saved_name_redirects_without_save_or_outcome`, asserts and UXD UX-I4's "A result is
  shown only once it is saved" requires. FDR R-62 and R-65, SRS DR-5, UXD UX-F8 and § 6
  `comment-on-a-task`'s "sets or changes the name" stand as written. A blank or too-long name is a
  refusal `domain` raises before any outcome (`domain/operator_name.py`, `check_operator_name`;
  SRS FR-27, FR-40), never a no-change outcome, so a name that never reaches the saver cannot meet
  SD-2's failure branch. The row's *Must not own* stands: which value is compared with is
  `domain`'s, so a reader does not add a shown-name value to the People form and does not give
  `application` a comparison. The same sentence in `products/tracker17/docs/nfdr.md` QC-21 is the
  Principal Architect's and is already `products/tracker17/docs/architecture_open_issues.md`
  § 3.1, unanswered on 2026-10-12, whose ask, "qualify other actions by their own `domain`
  comparison", covers the label without naming it. This document did not wait on that answer, as
  RN-45's round did not: downstream is rebuilt from upstream (§ 12). This is a correction of a
  part's description and not a re-cut under § 10, as RN-45 was: no slice's *Reached when*, fence
  or place moves, and no edge in § 7 changes. *(re: § 3, the `application` row; source: SRS FR-9,
  FR-27, FR-40, NFR-3, DR-5; UXD UX-F8, UX-I4; FDR R-62, R-65)*
- **RN-48:** *(CTO)* *(added)* The round that folded the seventh answered round read these things
  beyond the inputs RN-16, RN-23, RN-27, RN-30, RN-33, RN-37, RN-40, RN-44 and RN-46 list. It read
  `products/tracker17/docs/SDD_open_issues.md` as intake found it, committed at `2bc621f65` with
  its one answer slot filled, and `products/tracker17/docs/trail/sdd/self_answer-9.md`, the
  reasoning behind the answer. It read `domain/operator_name.py`, `application/tracker.py`,
  `domain/tasks.py`, `web/routes.py`, `tests/integration/test_people_routes.py` and
  `tests/unit/test_tasks.py`, to verify on disk each line the answer cites, and found each as
  stated. It read `products/tracker17/docs/SRS.md` whole, and FR-9, FR-18, FR-27, FR-40, NFR-3 and
  DR-5 for what the answer says does not move; `products/tracker17/docs/UXD.md` whole, and UX-F8,
  UX-I3 and UX-I4 for the same; `products/tracker17/docs/fdr.md` R-62 and R-65;
  `products/tracker17/docs/nfdr.md`'s header, QC-21 and RN-37,
  `products/tracker17/docs/adr/README.md` and
  `products/tracker17/docs/architecture_open_issues.md` whole, for the state of the downstream
  records. It ran `git log --format='%h %ad %s' --date=iso -1` on `25fff47d2`, `cb48338e3` and
  `33ad1a2a7`, and `git merge-base --is-ancestor 33ad1a2a7` against the first two, which confirmed
  that labels and the operator name landed after version 9. It ran `git diff --stat 2bc621f65 HEAD
  -- products/tracker17 ':!products/tracker17/docs'`, which printed nothing, so the code the answer
  read is the code on `main`. It ran no suite: the item is about what the code says, which was read
  on disk, and this round changed no code. It read the headers of the PRD and the SRS, which stand
  at version 6 as version 9 read them, and `git diff 6091a6f8b HEAD --
  products/tracker17/docs/UXD.md`, the whole change to the UXD since version 4, the version this
  document last read. Two things moved there, and neither moves a line here. UXD version 5 (commit
  `7634a24bd`) has UX-S1 open with what tracker17 is and its two reasons for existing (UXD RN-31);
  `first-project`'s *Artifact* already holds that opening paragraph through SRS FR-41 (RN-43), and
  its "every section UXD UX-S1 lists" reads the list as it now stands. UXD version 6 (commit
  `5d32fb74e`) has UX-I3 name what to do only where something is left to do, and has a refusal whose
  wanted state already holds name no action and offer no reload (UXD RN-32), while "A status move
  another tab overtook" and "an assignee who left the list before an add or an edit" still offer
  one. The two places this document states an out-of-date refusal, `tasks-in-a-project`'s assignee
  refused "as out of date" and `status-moves`'s move that "offers a reload", are those two cases,
  and § 4 EX-4 restates UX-I3's first sentence, which did not change. So no re-cut under § 10 is
  recorded, and the header's *Inputs read* names version 6. The NFDR stands at version 11 (commit
  `df8ac27ea`), which folded the architecture companion's earlier § 3.1 into QC-21 in the wording
  version 9's row carried; the companion now holds the two items its header names, and this
  document does not wait on them (§ 12). It read the opening lines of
  `products/tracker17/docs/DESIGN.md` and `products/tracker17/docs/CONTENT.md` and nothing more of
  either, because what this round changed describes a part and names no word a page shows or a
  value the stylesheet sets.
- **RN-49:** *(CTO)* *(added)* § 4 RT-11 states the history-admission boundary, § 9 TO-8 surfaces
  the decision, § 11 R-12 names its browser dependence, and RT-8's last sentence is scoped to a page
  whose address names a finished outcome — *because* the product has answered a page that shows a
  pending confirmation with HTTP 202, and every move interaction and outcome page with
  `Cache-Control: no-store`, since `9b05680c7`, and no line of this document or of an ADR said so
  or why. The PM found it tracing UXD UX-F4's Back case to its code (`trail/sdd/cycle-8.md`
  § 5.1): `web/routes.py`, `Site._pending_status`, answers `HTTPStatus.ACCEPTED` when the resolved
  view renders a pending confirmation and `HTTPStatus.OK` otherwise, `_stored_as_asked` adds
  `NOT_STORED` to every page whose address carries `move_task`, and a reader who met the 202 with
  no record could "simplify" it back to 200, which brings a stale confirmation back on Back. The
  answer, given in the CTO's seat, confirmed the record as the item listed it and added four
  things, with the reasoning in `products/tracker17/docs/trail/sdd/self_answer-10.md` § 5.1.
  First, the dependence is exact and was re-read at its source: Chromium's
  `PopulateReasonsForMainDocument` admits a main document only when `last_http_status_code()` is
  `net::HTTP_OK`, exactly 200 and not any 2xx; RFC 9110 § 15.1 does not list 202 among the codes a
  cache may store heuristically, so the HTTP cache cannot keep the confirmation even without the
  header and `no-store` is what protects the 200 outcome pages; and Chrome documents that a
  `no-store` page can be restored from the history cache, which is why the header alone was not
  enough and the earlier `Clear-Site-Data: "cache"` header was measured not to evict it. RT-11
  states the rule as the pinned browser's, as RT-9 and R-2 state `autofocus`. Second, where the
  decision is surfaced: § 12 names three places and no fourth, so § 9 gains TO-8, what the plain
  reading of a status line is given up for, and § 11 gains R-12, the release that would change the
  rule, with the two history tests as its trigger. Third, RT-8's "A reload of that page, or a
  return to it through back, shows the same line at the same place" is scoped: it holds for a page
  whose address names a finished outcome, and a page whose address asks for a pending step is
  built from the saved state on every load (RT-7) and shows what the state now allows. Fourth, one
  case is named and left where it occurs: a confirmation address whose task another tab has
  deleted answers 404 with no `no-store`, kept out of the history cache by the same exact-200 rule,
  and whether the HTTP cache may keep a 404 heuristically is `delete-and-rename`'s. Nothing settled
  moves: SRS NFR-3, NFR-4 and NFR-13, UXD § 4, UX-F4 and UX-I3, § 4 EX-2, EX-6 and SEC-3 and § 9
  TO-2 stand, no page script, cookie or session is used (RT-7; ADR-0003, ADR-0006), and no slice's
  *Reached when*, fence or place moves and no edge in § 7 changes, so this is an added condition
  and not a re-cut under § 10. The decision record and the obligation that binds it are the
  Principal Architect's: `products/tracker17/docs/architecture_open_issues.md` § 2.1, opened at
  `b52bdedf1` in the CTO's seat, hands them the decision, its ruled-out alternatives, its
  dependence and the obligation's verification, to write after this fold; this document does not
  wait on that answer (§ 12). *(re: § 4 RT-8, RT-11; § 9 TO-8; § 11 R-12; source: SRS NFR-3,
  NFR-4, NFR-13; UXD § 4, UX-F4, UX-I3)*
- **RN-50:** *(CDO)* *(changed)* § 6 `status-moves`'s behaviour bar has the overtaken move's
  refusal name the moves the page now shows, or none for a final status, and offer no reload, and
  names the refusal reached by an address and no press beside it; § 4 EX-4 says where that refusal
  sits; § 10 RC-4 records the UXD moving — *because* the bar said the refusal "offers a reload
  (UX-I3)" and UXD version 8 says no refusal offers one on a page built after it. The PM found it
  with the slice's bar still to be built against (`trail/sdd/cycle-8.md` § 5.2): UXD UX-I3 at
  version 8 reads "Each lands on a page built after the refusal, so none of them offers a reload",
  and UX-F4 says the same for the overtaken move and, from version 7, keeps the no-press refusal as
  a case of its own (UXD RN-33, RN-34). The answer, given in the CTO's seat, confirmed the change
  as asked and added three things, with the reasoning in
  `products/tracker17/docs/trail/sdd/self_answer-10.md` § 5.2. First, the second case in the same
  clause: a move refusal reached by an address and no press, which RT-11 answers from the saved
  state and `tests/e2e/test_moves.py`, `test_history_matrix_revalidates_current_saved_status`,
  shows at the status. Second, EX-4's one sentence, so a reader building the no-press case does not
  look for a control that was not used. Third, that this is an upstream change and § 10 records it
  as RC-4, which retains every slice, slug, *Delivers*, fence, order and § 7 edge and changes the
  behaviour line and EX-4. The command half stands: "the out-of-date move of AC-12" still names
  the test, and SRS AC-12 asks only that the refusal shows its reason and the saved data is
  unchanged. `tasks-in-a-project`'s assignee refused "as out of date" states no reload and does not
  move; whether the product's refusal lines still offer one, or still read "the move you pressed"
  on the no-press page (`web/pages.py`, the refused move's line), is a change to strings, which the
  UXD and `products/tracker17/docs/CONTENT.md` own (UXD RN-34; CONTENT RN-26), not to this
  document. RN-48's reading of UXD version 6, under which the overtaken move still offered a
  reload, is a dated record of that round and stays as written. *(re: § 4 EX-4; § 6
  `status-moves`; § 10 RC-4; source: UXD UX-F4, UX-I3, RN-33, RN-34; SRS AC-12, FR-18)*
- **RN-51:** *(CTO)* *(changed)* § 11 R-2 counts the confirmation case verified, naming its four
  tests and the commit they passed at, and § Open Questions drops the item that asked it — *because*
  the tests R-2 named as what settles the case exist and have passed, and a risk that calls its own
  settled case unverified sends a reader to run a check that has run. A `companion-self-answer`
  run raised it in the CTO's seat, reading R-2 and § Open Questions whole against
  `tests/e2e/test_moves.py` (`trail/sdd/cycle-8.md` § 2.1), and the answer, given in the same seat,
  confirmed the draft and added four things, with the reasoning in
  `products/tracker17/docs/trail/sdd/self_answer-11.md` § 2.1. First, the form: the result is a
  count at the commit it names, 67 passed at `9b05680c7` in a fresh clone, with a dated diff beside
  it, the form R-2 already uses for `first-project` and `tasks-in-a-project` and the one
  `products/tracker17/docs/nfdr.md` RN-15 settled on (`trail/architecture/cycle-11.md` § 3.1); the
  item's "printed nothing on 2026-10-20" was true at `ca2f9e98a`, and this round re-measured the
  diff at `6de932f9d`, where it lists one line of `products/tracker17/README.md` and no code.
  Second, the browser build is asserted by the run and not inferred from the pin:
  `test_moves.py` asserts `browser.version == PINNED_BROWSER`, `153.0.8010.12`, inside
  `test_history_matrix_revalidates_current_saved_status`, on the full Chromium of the install the
  focus tests' headless shell comes from, both from `playwright==1.63.0`, and R-2 says exactly
  that, as RN-41 said `tabindex="-1"`. Third, this is a correction and not a re-cut under § 10, as
  RN-41's was: no *Reached when*, fence, place or § 7 edge moves, and `status-moves`'s *Why here in
  the order* and § 9 TO-2 explain an ordering and stand. Fourth, what stays open downstream:
  `products/tracker17/docs/nfdr.md` RN-15 and
  `products/tracker17/docs/adr/0003-no-script-in-any-page.md` § Consequences, Dependence, still
  count the confirmation case open; both are the Principal Architect's and read this document
  (§ 12), the precedent is NFDR RN-23, which caught version 6's closing of two cases by reading the
  SDD's change, and `products/tracker17/docs/architecture_open_issues.md` is live and owed a round
  that reads the SDD as it now stands, so no item is raised there. Nothing settled moves: SRS
  NFR-13, UXD UX-I2, § 4 EX-6, § 9 TO-2 and ADR-0003 stand; the four tests stay among R-2's
  triggers, as RN-36 and RN-41 keep the earlier ones; § 7's `validates` row for `status-moves`
  describes what the tests show and stays; and the assistive-technology case keeps its VoiceOver
  settling path. *(re: § 11 R-2; § Open Questions; source: UXD UX-I2, UX-A5; SRS NFR-13)*
- **RN-52:** *(CTO)* *(added)* The round that folded the eighth answered round read these things
  beyond the inputs RN-16, RN-23, RN-27, RN-30, RN-33, RN-37, RN-40, RN-44, RN-46 and RN-48 list.
  It read `products/tracker17/docs/SDD_open_issues.md` as intake found it, committed at
  `6de932f9d` with its three answer slots filled, and
  `products/tracker17/docs/trail/sdd/self_answer-10.md` and `self_answer-11.md`, the reasoning
  behind the answers. It read `web/routes.py`, `web/pages.py`, `tests/integration/test_routes.py`,
  `tests/e2e/test_moves.py`, `tests/e2e/conftest.py` and `pyproject.toml`, to verify on disk each
  line the answers cite, and found each as stated: `NOT_STORED`, `Site._pending_status`,
  `_stored_as_asked` and `_move_view`, the two `task_not_found_page` answers, the refused move's
  line, the three integration tests and the two `Clear-Site-Data` absence assertions, the six
  end-to-end tests, `PINNED_BROWSER` and its assertion, the two browser fixtures and the pin. It
  did not re-read the Chromium source, RFC 9110 or Chrome's documentation: `self_answer-10.md`'s
  Header records each at its source on 2026-10-20, and RT-11 cites them as that record does. It
  read `products/tracker17/docs/UXD.md` whole, and § 4, UX-F4, UX-I3, UX-S4, UX-S6, RN-33 and
  RN-34 for the change RC-4 records, and `git log` on it, which places version 7 at `f90b692f9`
  and version 8 at `afffd0d5e`. It read `products/tracker17/docs/PRD.md`'s header and
  § Assumptions: version 7 (commit `faf9430a4`) says tracker17 becomes public with kensaiapp's
  public release, and § 1 already places publishing outside done, so no line here moves. It read
  `products/tracker17/docs/SRS.md`'s header, which stands at version 6 as version 10 read it, and
  `products/tracker17/docs/fdr.md`'s header, at version 4. It read
  `products/tracker17/docs/nfdr.md`'s header and RN-15, which stands at version 13 (commit
  `5e68bc569`, which folded the earlier architecture companion's last item and removed it),
  `products/tracker17/docs/adr/0003-no-script-in-any-page.md` § Consequences, Dependence, the
  headers of ADR-0001 to ADR-0009, and `products/tracker17/docs/architecture_open_issues.md`
  whole, which now holds the one item § 2.1 that RN-49 names. It ran `git diff --stat 9b05680c7
  HEAD -- products/tracker17 ':!products/tracker17/docs'` at `6de932f9d`, which listed one line of
  `products/tracker17/README.md` and no code, so the code the answers read is the code on `main`.
  It ran no suite: the items are about what the code and the records say, the record holds the
  count at its commit, no code moved since, and this round changed no code. It read the headers of
  `products/tracker17/docs/DESIGN.md` and `products/tracker17/docs/CONTENT.md` and, of the latter,
  RN-26 alone, because what this round changed states a response condition and a refusal's
  placement and names no word a page shows or a value the stylesheet sets, and RN-50 names the one
  note that owns the refusal's words.

---

## Open Questions

- [OPEN: Whether assistive technology reads the completion line or the reason when a page opens on
  the element it describes, as § 4 EX-14 needs. The suite shows the line in the accessibility tree
  as the element's computed accessible description and does not show it spoken. One pass with
  VoiceOver on the owner's macOS machine settles it, and no slice requires that run (§ 11 R-2).]
