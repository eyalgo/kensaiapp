# PRD open issues — tracker17

> Companion to `PRD.md`. The CPO authored the PRD non-interactively; this file holds
> what it could not settle from the inputs. **Answer inline** — fill each **Answer** /
> **Confirm-or-override** slot — **commit this file**, then re-run `product-prd`. It folds
> your answers into the PRD and drops the resolved items. When nothing is left unresolved,
> `product-prd` clears this file: no file = the PRD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CPO folds them in, it first copies
> this file whole to `docs/trail/prd/` — so what you decided, and why, stays readable
> and citable for good.
>
> **§§ 1–3 are the CPO's own questions. § 4 is not.** It holds what a seat downstream of the PRD —
> one that never wrote a line of it — found missing while working from the documents the PRD
> grounds. Same file, same fold, different asker.

---

## 1. Open issues — product-defining questions with no answer yet

None. Every round-0 question was answered, and each answer is now in the PRD
(`trail/prd/cycle-1.md` keeps them).

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

### 2.1 Who uses it: a reader, plus one operator; the "small team" is only who tasks are assigned to
- **Drafted into the PRD:** Target Users names two people. The **reader** is someone interested in how kensaiapp builds apps, and you stand in for them for now. The **operator** is the one person running it on their machine. The small team exists only as the names that tasks are assigned to. Team members don't sign in or use it.
- **Rationale:** Your answers pull two ways. 1.1 says "a task tracker for a small team", but 1.2 says it is for someone looking at how kensaiapp builds apps. 1.5 rules out multi-user over a network and logins, and your Agari answer is "I can use it locally easily by myself". The one reading that fits all of them is a single operator tracking a team's work.
- **Confirm or override:** confirm. Add the firmer reason under Target Users: tracker16-X's FDR opens with the same words, "A CLI task tracker for a small team" (§ Description), and it already works this way. It has one configured user (§ 12 User config), a global list of assignee names (§ 5 Assignees) and no accounts. So "small team" in answer 1.1 is that wording carried over, and it never meant several people using the tracker. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.2 The browser is the only interface — no command line ships
- **Drafted into the PRD:** Out of Scope says tracker17 has no command-line interface. It also says the predecessor's command-line mechanics are not carried over: command names and flags, the `+3d` date shorthand, and data kept per working directory.
- **Rationale:** You said people use it in the browser (1.1, 1.9). Shipping the predecessor's command line as well would give a reader two interfaces to read, which works against "simple". Reusing the code doesn't require exposing its command line.
- **Confirm or override:** confirm. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.3 tracker16-X's task rules become tracker17's own
- **Drafted into the PRD:** Core Features carries tracker16-X's rules in full:
  - the status workflow and its final states
  - `medium` as the default priority
  - one assignee list, where names stay on tasks after removal
  - free-text labels
  - the overdue rule (a task due today is not overdue)
  - comments: append-only, oldest first, authored under the operator's own name, which must be set before commenting
  - filtering within a project or across all projects, with single values combined as AND
  - single-field sorting, ascending by default
  - the summary's six counts
  - project delete cascades to its tasks
  - unique project names

  The PRD says tracker17 behaves as its predecessor does wherever both cover a rule.
- **Rationale:** Your answer 1.1 lists the same features as the predecessor's definition, almost word for word. Your exclusions in 1.5 are its exclusion list. So reading its rules as the intended ones seemed right. You never said "carry all of them", though, so the rules beyond your feature list are my call. One adaptation for the browser is also mine: the operator sets their name in the app, where the predecessor uses a `config set user` command.
- **Confirm or override:** confirm. Add one line under Comments: if the operator changes their name, existing comments keep the name they were written under. tracker16-X sets a comment's author when the comment is added (`tasktracker16x/domain/comment.py`). Every rule in the list was checked against tracker16-X. Unique project names come from its ADR and code rather than its FDR. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.4 The three success bars and when they are checked
- **Drafted into the PRD:** All three bars are checked before the product is called done, and again on every later release.
  - **Works:** every Key Use Case runs in the browser without an error, and the full suite passes with unit, integration and end-to-end tests all present.
  - **Simple to set up:** from a fresh copy, on a machine with only the stated prerequisites, the written instructions alone get you to the tracker in your browser. That takes at most 3 commands and at most 10 minutes, with no account, key or sign-up.
  - **Simple to read:** you read the code cold and judge it simple. This is your pass/fail call, and no line count stands in for it.
- **Rationale:** Your answer "I will run it locally and see it works" (1.6) covers "works" but sets no bar. Your use cases in 1.4 add "simple to set up" and "simple to read", which need bars too. I picked 3 commands and 10 minutes as a reasonable ceiling for "simple" with nothing to back them, so change them freely. I kept "simple to read" as your judgement, because any size number would reward the wrong code.
- **Confirm or override:** confirm, with two additions. (1) **Works** checks Key Use Cases 3–5 in the browser. Use case 1, setting it up, is checked by **Simple to set up**, and use case 2, reading the code and tests, is checked by **Simple to read**. Neither of those happens in the browser, so the bar as written can't be run on them. (2) In **Simple to set up**, commands joined with `&&` or `;` count as separate commands. Keep 3 commands and 10 minutes. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.5 How someone gets it: source code in its repository, no package or hosted demo
- **Drafted into the PRD:** tracker17 is offered as source code to read and run. A reader arrives at the written setup instructions. There is no package, no installer and no hosted demo (Out of Scope; UX Notes, Arrival).
- **Rationale:** You said "look at the code" and "see if it's simple to set up on a machine" (1.4), and a hosted demo would skip the setup being judged. One thing I can't tell is whether tracker17 should also be public. Today it lives inside the instance's repository. If outside readers should reach it, say where they get it.
- **Confirm or override:**

### 2.6 Reachable only from the machine it runs on
- **Drafted into the PRD:** Out of Scope, first line: the tracker is reachable only from the machine it runs on.
- **Rationale:** This is the plainest way to keep your 1.5 "not hosted or multi-user over a network". The alternative is a tracker that other machines on the same network can open, which would make it multi-user by accident.
- **Confirm or override:** confirm. Add the stronger reason to the Out of Scope line: tracker17 has no login, so a tracker other machines could open would let anyone on that network read, change or delete the operator's data. That would also make Data & Privacy's "None of it leaves the machine" false. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.7 Data & Privacy: it does hold people's names (changes your "No")
- **Drafted into the PRD:** tracker17 holds the names you type in: assignees, your own name, and comment authors. None of it leaves the machine, and you remove all of it by deleting the tracker's saved data.
- **Rationale:** You answered "No" to personal data (1.7). The product still stores people's names, though, so I recorded that plainly rather than write "none". Your answer holds in spirit: nothing is collected, sent or shared.
- **Confirm or override:** confirm. Add one line: the written setup instructions say where the tracker keeps its saved data. Deleting that data is the only way the operator can remove the names, so they need to know where it is. The predecessor's location, a folder in the working directory, is not carried over (item 2.2). Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.8 First run, saved data, failure states and what must feel easy
- **Drafted into the PRD:**
  - Three things must feel effortless: moving a task to its next status, seeing what's overdue, and narrowing a list.
  - Only the status moves allowed from where a task is are offered, and final statuses offer none.
  - If the tracker isn't running, the setup instructions say how to start it again.
  - The tracker opens empty, with no sample data, and invites you to create a first project. Empty lists say they're empty.
  - Everything survives a stop and restart on the same machine.
  - If the saved data can't be read, the tracker says so rather than starting empty.
- **Rationale:** None of your answers covers these, but every product makes a choice on each. Starting empty keeps it simplest. Sample data would make "see if it works" faster but adds scope. Refusing to quietly start over protects your work. The effortless three are the actions your feature list centres on.
- **Confirm or override:** confirm. Add to the unreadable-data case: the tracker never overwrites saved data it couldn't read. The setup instructions say how to set that data aside and start fresh on purpose, so "says so" leaves the operator a way forward and their work is still recoverable. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.9 Everyday defaults
- **Drafted into the PRD:** English only, a desktop browser, dates shown as calendar dates in the machine's local day, and every action usable from the keyboard. There is no commitment to a phone layout.
- **Rationale:** Nothing you said covers these, and leaving them unstated means they get picked silently downstream. These are the simplest defaults that fit "use it in the browser on your own machine".
- **Confirm or override:** confirm. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.10 Why it beats the alternatives, and what it costs
- **Drafted into the PRD:**
  - **Why This:** the nearest alternative is tracker16-X itself, a terminal tool. tracker17's edge is that it is an app people recognise and can try in a browser, defined from the top of kensaiapp's definition chain so a reader can follow one feature from product definition to code to tests (also Key Use Case 2). The PRD also says plainly that this edge is unproven.
  - **Goals:** no running cost and no revenue, because it is an example rather than a business.
- **Rationale:** You said it fills a gap ("no SIMPLE example", 1.3), but you didn't say why tracker16-X doesn't already fill it. The browser is the clearest difference. Being able to follow a feature from definition to code is my addition, so cut it if you only meant the code.
- **Confirm or override:** confirm. Add the concrete reason the edge is real: tracker16-X's definition starts at an FDR written from PM requirements (its `docs/fdr.md` header, "Source: PM requirements"), with no PRD above it. tracker17 is defined from the PRD down, so the trace from product definition to code that Key Use Case 2 describes is one tracker17 can show and its predecessor cannot. Keep Key Use Case 2, because "how kensaiapp builds apps" (answer 1.2) is that trace. Reasoning in `docs/trail/prd/self_answer-1.md`.

### 2.11 What a reader gets: source code to read and run — no package, installer or hosted demo

> **Raised by a `companion-self-answer` run on 2026-10-05, not written by a `product-prd` run.** It is
> one half of item 2.5, moved out because the two halves of 2.5 belong to different deciders. This
> item is the half the run answered: the **form** tracker17 is offered in. **Item 2.5 is now left
> asking only whether tracker17 is made public, and where outside readers get it.** That question is
> the owner's, and its slot stays empty. The run's reasoning, and the answer it would have given on
> 2.5, are in `docs/trail/prd/self_answer-1.md`.

- **Drafted into the PRD:** tracker17 is offered as source code to read and run. A reader arrives at the written setup instructions. There is no package, no installer and no hosted demo (Out of Scope; UX Notes, Arrival).
- **Rationale:** The owner's answer 1.4 is "Look at the code, see if it works, and see if it's simple to set up on a machine". A package or installer would hide the code and the setup being judged, and a hosted demo would skip the setup entirely. Answer 1.5 also rules out "hosted". So source code is the only form that serves all three things the reader comes to do. The answer holds whether or not tracker17 is later made public. Either way the reader starts from a copy of the source and the written instructions. The self-answer run would confirm this as drafted.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Directives — an external action the owner confirms as a gate

None.

## 4. Raised from downstream — an item from a seat that did not write the PRD

None.
