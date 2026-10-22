---
name: tracker17
omitted:
  message patterns / partial: nothing in tracker17 is applied in part. A refused action changes nothing (UXD UX-I3), a failed action changes nothing (UXD UX-I5), and a save that is cut off reads afterwards as the state before or after, never a mix (SRS NFR-2). No state exists whose words would say "this part worked and this part did not".
  message patterns / recovered: nothing in tracker17 comes back by itself. Pages do not update themselves, and neither the PRD, the UXD nor the SRS has the tracker retry an action or hold a connection open. The pages that update themselves are closed (UXD UX-I9, PRD § Out of Scope, "Real-time collaboration and notifications"). A state the reader reaches again, such as a reload that shows a changed task, is reached by the reader's own action and is not recovery.
---

# CONTENT — tracker17

**Status:** Settled
**Owner:** Content Manager
**Version:** 15 — folds the answer to item 3.1 (cycle 14) into version 14: the overtaken-move refusal states the task's current status and what it allows and claims no change, in the clause, its two examples, the banned-words row, RN-11, RN-26 and RN-27
**Inputs read:** PRD Settled · UXD Settled (version 9) · SRS Settled · DESIGN Settled · Agari no Status line (`agari_template.md` carries none) · tracker17 doctrine no Status line (stamped, unfilled)

> The verbal language is the source of truth for everything this product says to a person. It is
> the peer of `DESIGN.md`, not a part of it: a rule about how something **looks** belongs there,
> a rule about what it **says** belongs here. It is authored off the UXD — the states the words
> live in are named there — and it holds **no per-change copy**: a line that would need editing
> when a feature ships belongs to that change, not to this file. Updated in place with
> versioning (bump the line above whenever a rule or the prose changes); on a revision it is
> **stable by default** — every shipped string was written under the voice as it stood, so a
> silent re-voicing invalidates the corpus without telling anyone. Every delta traces to an
> owner answer, a change in the evidence, or an upstream UXD/PRD change.

**Scope.** This language governs every word tracker17 says to a person: the pages in the browser, the
text the tracker prints in the terminal it was started from, and the written setup instructions. It
governs no code comment and no test name. It governs no output of a script a developer runs to check or
measure the tracker, such as the timed run, because the tracker doesn't print those words. Where such a
script prints a string the tracker wrote, the string is governed where the tracker writes it. The examples
below illustrate a rule. None of them specifies a screen.

---

## Voice

The tracker speaks as itself, in the third person ("the tracker"), to one person it addresses as "you".
That person is a developer working on their own machine. They pressed something and want to know two
things: whether it happened, and what is true now. The tracker's job with words is to answer those two
things and stop. Every sentence it adds is a part the reader has to read, and the product's first risk
is exactly that its web interface "adds parts that a command-line tool never needed" (PRD § Risks).
When no rule below decides a string, two fallbacks apply in this order. First, prefer the wording that
lets the reader name who acted and what state the thing is in. Second, prefer a complete plain sentence
to a shorter one that leaves the reader to infer the rest. Either fallback may be replaced by a rule
below.

**Conversational or casual:** conversational and not casual. The tracker writes the way a competent
person tells another competent person what happened, contractions included. It uses no slang, no jokes
and no exclamation marks. The reason is the surface: a routine status move and an irreversible
project deletion are worded by the same voice, so a register that could joke in one place would joke
beside the other.

| We do | We are not | On a real string |
|---|---|---|
| Name the actor and the resulting state in every line that reports an action. A line about what the reader did starts with "You". A line about what the tracker could not do starts with "The tracker". | A log line, which drops the actor and leaves a noun and a participle. | Right: "You moved 'Set up CI' to done." Wrong: "Task updated." |
| Give one next action when one exists, and none when none does. | A guide that closes every message with advice. | Right: "A project named 'Alpha' already exists. Choose a different name." Wrong: "That name is taken. Try again, or contact support." |
| State only what the tracker established. Where it cannot know a cause, it says the smaller true thing. | Reassuring, which promises what the tracker cannot check. | Right: "There's no task at this address." Wrong: "This task was deleted. Don't worry, nothing is lost." |
| Use the product's own term for each concept (§ Terminology) and write the reader's typed words back exactly, in quotes. | Branded, which renames the product's concepts to sound friendly. | Right: "You added 'Set up CI'." Wrong: "Your new to-do is on the board." |
| Address the reader as "you" and the tracker as "the tracker". | Chummy, which says "we", "let's" or "our". | Right: "You need a name to comment." Wrong: "Let's set your name first." |
| Say nothing a successful action does not need. A reading action, such as applying a filter or backing out of a confirmation, produces no message. | Chatty, which narrates what the page already shows. | Right: the filtered list, with its match count and no message. Wrong: "Filter applied!" |

**Limits the product holds, stated as its own rules.** No delivered string carries filler: no "lorem
ipsum", no authoring marker left in (`TODO`, `TBD`, `FIXME`, `XXX`), no unsubstituted template slot
(`<name>`, `{value}`, `%s`), and no wording that stands in for content that does not exist ("coming
soon", "description here"). A deliberate stub says in its own words that it is one. Delivered means
handed to a person outside the run that produced it. Separately, tracker17's words attribute no
pipeline-produced work to anyone, so no string needs the rule that governs naming the role behind such
work. A string that ever does name one names that role by its own role name, never by a model name, a
tool name, or a stand-in such as "the AI" or "the system".

## Tone

The voice stays the same and its magnitude changes. Three levels describe every change. **Level 0** is
the result and nothing else. **Level 1** is the result and one next action where one exists. **Level 2** is the result or
the question, the consequence it carries, and why it can't be reversed. The tracker never goes beyond
level 2, and no level adds a feeling.

**Across one high-stakes flow, deleting a project (UXD UX-F10 and UX-I2):**

| Moment | Tone, and how far | Why it changes here |
|---|---|---|
| The reader presses the first Delete project button | Level 0. The label is the bare action, with no warning word on it. | The press is not the guard. The confirmation is. |
| The confirmation appears in the button's place | Level 2. It asks the question with the project's name and its task count, then says the step can't be undone. No softener, no alarm word. | It is the only guard on a deletion that takes every task with it and cannot be undone (UXD UX-I2). |
| The reader presses Back out | Silence. | Nothing happened, so there is nothing to report. |
| The reader presses the confirming control and lands on Projects | Level 0. One sentence names what went, with the count. No relief, no regret. | The reader needs the fact that closes the action. |
| The same project's address is opened later | Level 1. It says there's no project at the address and offers the two lists. | The tracker can't establish why the project is gone (§ Error). |

**Across the lifecycle:**

| Stage | Tone, and how far | Why it changes here |
|---|---|---|
| First run | Level 1. An empty state says what is absent and names the one thing to do. No welcome, no tour. | The product has no onboarding beyond its empty states (UXD § 10). |
| Habitual use | Level 0. Each action gets one sentence naming what changed. | The reader repeats actions all sitting and reads only the result. |
| Failure | Level 1, at its plainest. The reason comes first and the action second, where one exists. No apology and no reassurance. | The reader needs precision more than comfort, and the tracker can't know how they feel. |
| Saved data that can't be read | Level 2. It says what happened, where the data is, that nothing was changed, and where the way forward is written. | It is the one state where the reader's work may be at stake, so the tracker states what it knows and nothing it doesn't. |
| Leaving | Silence. The tracker has no sign-out, no farewell and no summary of the sitting. | There are no accounts to leave (PRD § Out of Scope, "Login, accounts or access control"). |

## Grammar and mechanics

- **Person.** The tracker says "you" and "your" to the reader and "the tracker" for itself. No string
  uses "we", "our", "I", "let's", "the user" or "the operator".
- **Tense.** A line reporting a completed action is in the past tense ("You moved…"). A line stating a
  state is in the present tense ("This project has no tasks yet."). A line telling the reader what to
  do is an imperative ("Type a name.").
- **Case.** Sentence case for every heading, label, button, link, column header and page title. The
  exceptions are the product name `tracker17`, which is always lowercase and never starts a sentence,
  and the status and priority words, which are always written as defined (§ Terminology). No string
  starts with a status or priority word, except a string whose whole text is that word: a control label, a table cell, a list option or a summary row label.
- **Sentence endings.** Every complete sentence ends with a full stop, or with a question mark where it
  asks. Buttons, labels, headings, links, column headers and page titles end with no punctuation.
- **Banned punctuation.** No exclamation mark, no em dash, no semicolon, no ellipsis (neither the
  character nor three full stops). A colon appears only in a page title, inside a time, and inside an
  address or a path the tracker prints. Parentheses appear only in the summary's "(unassigned)". These
  bans govern the tracker's own words. They don't reach a value the reader typed, such as the title
  'Fix: login', or the underlying error text a terminal diagnostic carries verbatim. Both are written
  back exactly (§ Voice, § Quotes, § Message patterns, Error).
- **Quotes.** A value the reader typed, such as a title, a project name, a label or an assignee name,
  is written back inside straight single quotes whenever it appears in a sentence. Quotes are
  straight everywhere, apostrophes included. The value is shown whole, because nothing the tracker says
  is shortened (`DESIGN.md` § Layout, "Long text wraps, and the stylesheet shortens nothing").
- **Contractions.** Negatives are always contracted: can't, doesn't, isn't, couldn't, didn't, wasn't.
  "Cannot" and "do not" do not appear. "There's" and "it's" are allowed.
- **Sentence length.** No sentence is longer than 20 words. A message has at most three sentences, and a
  refusal at most two. A completion line is one sentence.
- **Numbers.** Counts are numerals ("1 task", "12 tasks", "3 commands"), never words. A count of zero is
  "no" inside a sentence and "0" inside a summary cell.
- **Dates and times.** A date is `YYYY-MM-DD`, such as `2026-10-06`, in the machine's local day. A time
  is `HH:MM` on a 24-hour clock in local time, with no seconds, no AM or PM and no time zone, such as
  `14:32`. A date and a time together are `2026-10-06 14:32`. No string says "today", "yesterday",
  "tomorrow", "now", "ago" or "recently", because a page doesn't update itself (UXD UX-I9) and a
  relative word would be wrong by the next reload. This rule governs every date the tracker writes as text,
  a refusal message included. The date field's displayed form is the browser's own and is not a tracker
  string, so no string tells the reader how to type or pick a date, a refusal included. The tracker
  states no way of entering a date, so a refusal names the outcome instead of the means, such as "Give
  a calendar date, or leave the due date empty."
- **Abbreviations.** None in a string, and no Latin abbreviation ("e.g.", "i.e.", "etc.", "vs."). The
  names of commands and tools in the setup instructions are written as their own owners write them.
- **Verbs for pressing.** A button is "pressed", a link is "opened", an option is "picked" and text is
  "typed". No string says "click", which excludes the keyboard (UXD UX-A1).
- **Control labels.** A control label is one verb, or a verb and its noun, in at most three words. It
  names what the control does and never "OK", "Yes", "No", "Submit" or "Confirm".
- **Setup and set up.** "Set up" is the verb and "setup" is the noun and the adjective.

## Terminology

| Concept | The term | Rejected, and why | Notes |
|---|---|---|---|
| The person using the tracker | "you" and "your" | operator, user, admin, owner. The first is the definition documents' word for the role and none of them is what a person calls themselves. | "Operator" never appears in a string. |
| The running product | "the tracker" | app, application, server, instance, service, system. Each names a mechanism, and "system" is the stand-in the fence on naming roles rejects. | `tracker17` is the product's name, written as § Grammar and mechanics (Case) sets it. For itself, in a sentence, the tracker says "the tracker". |
| A unit of work | task | ticket, issue, item, card, to-do. Each belongs to another product's vocabulary. | |
| A group of tasks | project | workspace, board, folder, team. "Team" would suggest several people use the tracker (PRD § Risks, "'Small team' can mislead a reader"). | |
| Where a task stands | status | state, stage, phase, column. | |
| The four statuses | `todo`, `in-progress`, `done`, `cancelled` | To do, To-do, In progress, Complete, Completed, Closed, Canceled. The PRD fixes these four words (§ Core Features, Status workflow). | Always lowercase and hyphenated as shown. "Cancelled" keeps both l's. |
| A task that is neither `done` nor `cancelled` | open | active, pending, unfinished, incomplete. | Used only for that meaning, as in "open tasks". Never a status. |
| How important a task is | priority, with `low`, `medium`, `high`, `critical` | urgent, normal, P1. | The four values are the PRD's (§ Core Features, Priorities). Always lowercase as shown. |
| The person a task is given to | assignee | owner, member, team member, person, resource. | The list is "the assignee list". A task with none is "unassigned" in a task row and "(unassigned)" in the summary. Both forms stand because the parentheses keep the summary's row from reading as a person's name. |
| A word attached to a task | label | tag, category, keyword. | |
| The date a task is due | due date | deadline, due, target date. | The two filter fields are "Due from" and "Due to". |
| A task past its due date and neither `done` nor `cancelled` | Overdue | late, past due, expired, delayed. | Written as the one-word marker "Overdue" beside the due date, and as the filter "Overdue". |
| Text on a task | comment | note, reply, message, remark. | |
| The reader's own name, set in the tracker | "your name" | username, account, profile, login. | The section is "Your name". |
| What the tracker keeps between sittings | saved data | database, data file, storage, state, backup. | |
| What the browser opens | address | URL, link, endpoint, host, port. | |
| The window the tracker is started from | terminal | console, shell, command prompt, CLI. | The UXD says "console" for the same thing. Both mean the one window, and this document picks the one a developer says. |
| The written document a reader starts from | setup instructions | README, install guide, getting started, manual. | |
| Two sections of the setup instructions that other strings point to | "Starting the tracker again" and "Setting saved data aside" | Restart, Reset, Wipe, Clear data. | A string that points to one quotes its heading exactly. |
| Putting saved data out of the tracker's reach on purpose | set aside, and "start fresh" for the result | reset, wipe, clear, delete, erase. Each claims a loss, and the PRD promises the work stays recoverable (§ UX Notes, Failure states). | |
| Moving a task to another status | move | change, update, set, advance, transition. | Status changes only through the workflow (PRD § Core Features, Tasks). |
| Making a project | Create | New, Add. | Create is for a thing that holds other things. |
| Putting something into a thing that holds it | Add | Create, New, Insert. | Used for a task, an assignee, a label and a comment. |
| Taking a name or a label off | Remove | Delete, Clear. | Removing leaves the thing's other uses alone. A removed assignee name stays on the tasks that carry it (PRD § Core Features, Assignees). |
| Destroying a project or a task and what it holds | Delete | Remove, Erase. | The word the reader sees on the two controls that ask for a confirming press. |
| Leaving a pending irreversible step | Back out | Cancel, No, Keep. "Cancel" reads as the status `cancelled`, which UXD UX-I2 forbids. | |

**Banned in anything a person sees:**

| Never | Say instead | Why |
|---|---|---|
| error, failed, failure, invalid, illegal, incorrect, wrong, bad, as a label or about what the reader typed | What happened, in the tracker's terms: "A project needs a name." or "didn't happen" | The words blame the reader or say nothing. |
| oops, whoops, uh-oh | Nothing | They are casual (§ Voice). |
| sorry, unfortunately, apologies | The plain fact | An apology performs a feeling the tracker can't know the reader has. |
| please | An imperative: "Type a name." | It adds a word with no information. |
| successfully, successful | The completion line | A line is shown only once the result is saved (UXD UX-I4), so the adverb repeats it. |
| simple, simply, just, easy, easily, quick, quickly | Cut the word | Whether the product is simple is the owner's judgement alone (PRD § Risks, "The only judge is the owner"). |
| null, undefined, NaN, token, payload, exception, traceback, endpoint | The plain thing | They are internal vocabulary. The one permitted place is the verbatim text the tracker's terminal diagnostics carry (§ Message patterns, Error). |
| corrupt, corrupted, damaged, broken, lost, about saved data | "couldn't read" | The tracker can't establish a cause, and the PRD says the data stays recoverable. |
| deleted or gone, to explain a missing page; "another tab" or "another window", to explain an out-of-date page | "There's no project at this address." and "The status of 'Set up CI' is todo. A task in todo can be moved to in-progress or cancelled." | The tracker can't establish either cause. The second form states the status the page shows and claims no earlier event, so it is true on the first landing and on every later visit. |
| safe, secure, protected, backed up, "never lose" | State only the fact that applies | The tracker makes none of those guarantees. |
| Cancel, as a control label or a verb | Back out | It reads as the status `cancelled`. |
| OK, Yes, No, Submit, Confirm, as control labels | The action's own verb | They say nothing about the action. |
| Loading, please wait, any ellipsis | Nothing | No page shows loading text (UXD UX-I8). |
| sign in, sign out, log in, account, profile, welcome | Nothing | The tracker has no accounts (PRD § Out of Scope). |
| click | press, open, pick or type | Click excludes the keyboard. |
| above, below, left, right, here, "the red mark", "the button on the right" | The control's own label | A string can't locate a control by position, colour or shape alone (§ Accessibility of text). |
| we, our, I, let's | "the tracker", "you" | The tracker is not a team (§ Voice). |
| An exclamation mark, an emoji | Nothing | The product is plain and quiet (UXD § 1). |

## Message patterns

The five standing states are error, empty, loading, partial and recovered. Two of them are declared
absent in the frontmatter, each with its reason. Three more states carry words in the UXD and have a
pattern here: a completed action, a step that needs confirming, and the tracker being ready. Each
formula lists its parts in order. Each example illustrates the rule and specifies no screen.

### Error

An error is any state where the thing the reader tried didn't happen. Four kinds carry different parts.

**A refusal** (UXD UX-I3) is an action the rules turned down, such as a blank title or a name already
in use. It sits beside the control that was used.
**Formula:** the reason, stated as a fact about what the reader typed or pressed, naming the field's
subject in words and quoting any typed value, then one action where one exists. Two sentences. It never says "nothing
changed", because a refusal changes nothing by definition. Where the state the reader wanted already holds and the page already shows it, no action exists, and the second sentence says what the page shows. A refusal on input the reader can still fix always has an action.
A refusal of a move another change overtook states the task's current status and the moves that status allows, or says there are none for a final status. It claims no change and offers no reload, because the page it lands on is built after the refusal and the tracker can't tell its first landing from a later visit.
A refusal the reader reached without typing or pressing anything in that step, by a reload, Back, or a saved or typed address, states its reason as a fact about the task and what its status allows, and never as a fact about a press. It doesn't say "the move you pressed". It names the move the address asks for, where the address carries one, gives no action and offers no reload, and its second sentence says what the page shows. The same formula serves a task in `done` and a task in `cancelled`. This rule applies only while the interface shows that refusal.
**Examples:**
- "A project named 'Alpha' already exists. Choose a different name."
- "A task needs a title. Type one."
- "The Due from date, 2026-10-10, is later than the Due to date, 2026-10-01. Change one so Due from is the earlier date."
- "A comment needs your name. Set it on the People page, then add the comment."
- "The status of 'Set up CI' is todo. A task in todo can be moved to in-progress or cancelled." This is the form for a move another change overtook, naming the moves the status allows.
- "The status of 'Set up CI' is done. A task in done can't be moved." This is the same form for a final status, where no move is left.
- "The label 'bug' isn't on 'Set up CI'. The labels shown are the ones the task carries." This is the form with no action.
- "The status of 'Set up CI' is done, which doesn't allow a move to cancelled. A task in done can't be moved." This is the form for a refusal reached without a press.

**A failure that is not a refusal** (UXD UX-I5) is a failure the rules did not produce.
**Formula:** the tracker couldn't do the named action, said as "The tracker couldn't…" with the typed
value quoted, and nothing was changed, then what the reader typed is still in the form where that is
true, then one action. Three sentences at most. It names no cause, because the tracker doesn't
establish one for the browser.
**Examples:**
- "The tracker couldn't add 'Set up CI', and nothing was changed. What you typed is still in the form. Try again."
- "The tracker couldn't rename 'Alpha', and nothing was changed. What you typed is still in the form. Try again."

**An address with nothing at it** (UXD UX-S10).
**Formula:** one sentence that says there is no project or no task at this address, then a link to
each place the tracker has to send the reader, named by its label, Projects first and All tasks after
it. It names no cause. The sentence offers only places the tracker has, because a sentence that tells
the reader to open a place it doesn't have is a claim it can't keep (§ Voice, "State only what the
tracker established").
**Examples:**
- "There's no project at this address. Open Projects or All tasks." This is the form with two places.
- "There's no task at this address. Open Projects or All tasks." This is the form with two places.
- "There's no project at this address. Open Projects." This is the form with one place.

**Saved data that can't be read** (UXD UX-S9) replaces every page.
**Formula:** a heading that states the fact, then three sentences: the tracker couldn't read its saved
data and where it is, nothing in it was changed or overwritten, and the setup instructions' section
that says how to start fresh on purpose, named exactly. It offers no control that acts on the data.
**Example:**
- Heading: "The saved data can't be read". Body: "The tracker couldn't read its saved data, which is kept at /Users/sam/tracker17/data. Nothing in it was changed or overwritten. To start fresh on purpose, follow Setting saved data aside in the setup instructions."

**Terminal messages** (UXD UX-S2). A start that fails is one paragraph that begins "The tracker didn't
start", gives the reason, and gives one action. Where saved data is the reason, it names the location.
When an action fails for a reason that is not a refusal, the terminal also prints the underlying
error text, on its own line after the plain sentence and exactly as the system reported it (SRS NFR-8).
That text is the one place the banned technical vocabulary may appear, because it is for the developer
reading the terminal and is not the tracker's own wording.
**Examples:**
- "The tracker didn't start, because something else is already using the address 127.0.0.1:8017. Stop that program, then start the tracker again."
- "The tracker didn't start, because another tracker is already running on the same saved data. Stop that one first, then start this one."
- "The tracker didn't start, because it couldn't read its saved data at /Users/sam/tracker17/data. Nothing in it was changed. See Setting saved data aside in the setup instructions."

### Empty

**Formula:** one sentence that says what is absent in the product's own noun, or, for a filter that
matched nothing, says the filter is the reason. Then one sentence naming the one thing to do next and
the control to do it with, by its label. Never "no data", "nothing here" or "empty". It shows no sample
data and no welcome.
**Examples:**
- "There are no projects yet. Type a name for your first project and press Create."
- "No tasks match this filter. Press Clear to see every task."
- "This project has no tasks yet. Give the first task a title and press Add."
- "No name is set. You need a name to comment."
- "There are no assignees yet. Tasks can be assigned only to names on this list."

The no-match state never says "no tasks", and the no-tasks state never mentions a filter. The two are
different facts (UXD UX-S4).

### Loading

**Formula:** none for a page. A page appears whole or not at all, and the browser's own indicator is the
only loading state (UXD UX-I8), so the tracker writes no loading wording. The one place the tracker says
something at the end of a wait is the terminal, when it is ready. The terminal says nothing until then,
and the ready line has these parts in order: the tracker is running, the address to open, where the saved
data is kept.
**Example:**
- "The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/tracker17/data."

### Partial

Omitted. See `omitted:` above for the reason.

### Recovered

Omitted. See `omitted:` above for the reason.

### Completed

**Formula:** one sentence, a full stop at the end. "You" and a past-tense verb, then the object, with
a typed value quoted. When the action's visible consequence differs from what the reader would assume,
the consequence follows in the same sentence after a comma. It is shown only once the result is saved
(UXD UX-I4). An action that only reads, such as applying a filter, opening a project or backing out,
produces none.
A line that reports a project deletion gives the count of tasks the action deleted, read when it ran. It
doesn't repeat the count the confirmation showed, because that count is the page's as loaded and may be out
of date.
The verbs are fixed by the action: created, added, saved changes to, moved, removed, deleted, renamed,
set.
**Examples:**
- "You added 'Set up CI'."
- "You moved 'Set up CI' to done."
- "You moved 'Set up CI' to done, so it no longer matches the status filter and has left this list."
- "You removed 'Dana' from the assignees, and tasks that already carry the name keep it."
- "You deleted 'Alpha' and its 12 tasks."
- "You set your name to 'Sam'."

### Needs confirming

This is the in-place confirmation for deleting a project, deleting a task and moving a task to
`cancelled` (UXD UX-I2). The UXD fixes its three parts and their order. This pattern fixes the words.
**Formula:** the sentence part has two sentences. The first asks the question, naming the thing and the
count of what goes with it. The second says why the step can't be reversed. After it come the confirming
control and then the back-out control. The confirming control is labelled with the action as a verb
phrase naming what it acts on. The back-out control is always "Back out".
**Examples:**
- "Delete 'Alpha' and its 12 tasks? You can't undo this." The confirming control reads "Delete project".
- "Delete 'Alpha', which has no tasks? You can't undo this." This is the form for a project with no tasks, where "and its 0 tasks" would read as noise.
- "Delete 'Set up CI'? You can't undo this." The confirming control reads "Delete task".
- "Move 'Set up CI' to cancelled? A cancelled task can't be moved again." The confirming control reads "Move to cancelled".

## Accessibility of text

This section binds the text to the UXD's accessibility requirements (UX-A1 to UX-A7). The tracker
conforms to WCAG 2.2 Level AA (UXD UX-A5), and each rule names the requirement it serves.

- **The accessible name of a control contains its visible label as one unbroken string.** Where the same
  visible label appears more than once on a page, the accessible name adds the thing the control acts
  on. So a move button whose visible label is `in-progress` has the name "Move 'Set up CI' to
  in-progress", and a Remove button beside a label has the name "Remove label 'bug' from 'Set up CI'".
  Links that share a label and open the same address share one name, and the added thing applies where
  controls act on different things. A link acts on its destination, so two links with the same label
  and the same address have nothing to tell apart. (UXD UX-A5 requires WCAG 2.2 AA in full, and SC 2.5.3 Label in Name is part of it.)
- **Every field has a visible label.** A field's label is its name. No field shows text inside itself as
  an instruction. An instruction is plain text beside the field and states the constraint in a full
  sentence, such as "You can't change the description after you create the project." or "Comments
  you've already written keep the name they were written under." (UXD UX-A5, SC 3.3.2; UXD UX-F2 and
  UX-F8.)
- **A refusal or failure is identified in words and reads alone.** Its first sentence names the field's
  subject ("A project needs a name."), so a screen reader announcing it out of place still says what it
  is about. It does not begin with "Error" or "Invalid" (UXD UX-A3).
- **The first words of a status message carry the result.** A completion line starts "You moved…" and a
  refusal starts with its reason, so an announcement cut short still says what happened. A status message
  is announced without moving focus. The confirmation of an irreversible step is not one of these. It
  takes focus on purpose (UXD UX-I2).
- **Link text means something read out of context.** It names the destination and nothing else:
  "People", "All tasks", "Projects", a task's own title. It is never "here", "click here", "this",
  "more", "link" or a bare address. Two links to different places never share their text. A link whose
  visible text is only a number, such as a summary count, has an accessible name that starts with that
  number and says what it counts: "12 tasks in todo", "3 overdue tasks".
- **State is carried by words, never by colour, position or shape.** Status, priority and the overdue
  state are words (UXD UX-A4). No string locates a control as above, below, left or right, or by its
  colour or shape. A string names the control by its label.
- **Every page has a title that names its subject.** The pattern is the subject, a colon and the view
  where the page has views, then " - tracker17". It begins with the part that tells pages apart.
  (UXD UX-A5, SC 2.4.2.) Examples: "Projects - tracker17", "Alpha: Tasks - tracker17",
  "Alpha: Summary - tracker17", "Set up CI - tracker17", "All tasks - tracker17", "People - tracker17",
  "Not found - tracker17", "The saved data can't be read - tracker17".
- **The page language is English.** Every string is English. The only other language on a page is text
  the reader typed.
- **No image carries information, so none needs alternative text.** The tracker shows no image. The red
  mark along an overdue row's left edge is decoration, and the word "Overdue" carries the state
  (`DESIGN.md` § Components, the margin mark and the overdue marker).
- **The reading bar.** No sentence is longer than 20 words, and each carries one claim. No idiom and no
  word a first-time reader would have to look up appears in a page string, except the product's own terms
  in § Terminology. The setup instructions may use the names of the commands and tools the reader runs.

## Localization

The tracker ships in English only (PRD § UX Notes, Defaults). These rules cost nothing now and are
expensive to add after strings exist.

- **No string is assembled from fragments.** Each action has its own complete string. "You moved…",
  "You added…" and "You deleted…" are three strings, and code doesn't join a verb to an object.
- **A placeholder is named for what it stands for** and holds one typed value or one number, such as a
  project name, a task title, a status name, a task count, an address or a data location. It never holds
  a verb, an article or a grammatical choice. A string that needs "a" or "an" fixes its own noun, so the
  article is part of the string.
- **Plurals are written out.** Every string that carries a count has a written form for one and for the
  rest, and for zero where the text says "no". The localization system picks the form. No string writes
  "task(s)".
- **The quotes around a typed value belong to the string**, not to the value.
- **A date and a time come from one formatter** that writes `YYYY-MM-DD` and `HH:MM` (§ Grammar and
  mechanics). No string spells a date by hand. The date field's displayed form is the browser's and is
  outside this rule.
- **Placeholders may be reordered by a translator.** A string with two placeholders doesn't depend on
  English word order.
- **Address and gender.** "You" carries no gender or formality choice. No string refers to an assignee
  by a gendered word.
- **Expansion.** No string depends on fitting a fixed width. Text wraps and nothing is shortened
  (`DESIGN.md` § Layout), which this rule relies on.
- **A translator gets context.** Each string is handed over with a note naming the state it answers and
  what the reader had just done.
- **Never translated:** the product name `tracker17`, anything the reader typed, addresses, file paths,
  the commands in the setup instructions, and the verbatim error text in terminal diagnostics. The
  status and priority words are product values and are translated, if ever, once each as one table, so a
  status is spelled one way everywhere.

## Traceability

| UXD state or requirement | Covered by | Notes |
|---|---|---|
| UX-S1 Setup instructions | Voice, Grammar and mechanics, Terminology | The written commands are per-change copy. The two section headings others point to are fixed in § Terminology. It has no empty, loading or error state of its own. |
| UX-S2 Start command | Error (terminal messages), Loading (the ready line) | The terminal says nothing until ready. |
| UX-S3 Projects, empty | Empty | First run. |
| UX-S3 Projects, error | Error, refusal and failure | Create refused or failed. |
| UX-S4 Project Tasks, empty | Empty | Two states, no tasks and no match. |
| UX-S4 Project Tasks, error | Error, refusal and failure, and the address with nothing at it | |
| UX-S4 Project Tasks, success | Completed | After an action. |
| UX-S5 Project Summary | Empty, Error (address with nothing at it), Accessibility (number links) | A project with no tasks shows 0 and the Empty invitation. |
| UX-S6 Task, empty | Empty | No labels, no comments, no name. |
| UX-S6 Task, error | Error | |
| UX-S6 Task, success | Completed | A task in `done` or `cancelled` shows no move buttons and so no words for them. |
| UX-S7 All tasks | Empty, Error, Completed | No tasks anywhere and no match. |
| UX-S8 People | Empty, Error, Completed | The removal line carries its consequence. |
| UX-S9 Saved data that can't be read | Error, saved data that can't be read | |
| UX-S10 Not found | Error, an address with nothing at it | |
| UX-I1 Status workflow shown | Terminology, Accessibility | Move buttons are named by the target status, and the accessible name adds the move and the task. |
| UX-I2 Irreversible actions confirmed in place | Needs confirming | The UXD fixes the structure and focus. This document fixes the words. |
| UX-I3 A refusal says why | Error, refusal | |
| UX-I4 A completed action is confirmed | Completed | |
| UX-I5 A failure that is not a refusal | Error, failure | |
| UX-I6 The keyboard model | Grammar and mechanics (verbs for pressing) | No string says "click". |
| UX-I7 Filter and sort in the address | none | The tracker says nothing about it, so there are no words to cover. |
| UX-I8 A page appears whole | Loading | The tracker writes no loading text. |
| UX-I9 Pages do not update themselves | Grammar and mechanics (dates and times) | No relative time word is used. |
| UX-A1 to UX-A7 | Accessibility of text | UX-A7 (reflow) and UX-A6 (target size) are layout and are DESIGN's. The words' part is that no string depends on a fixed width. |
| UXD Open Question: how a due date and a comment's written time are written | Grammar and mechanics (dates and times) | Settled here and confirmed by the owner (`trail/content/cycle-1.md` § 2.3). The date field's own display is outside the rule (§ 1.1 there). |
| UXD Open Question: how long text wraps | none | `DESIGN.md` carries the display. The words' part is that typed values are shown whole. |

## CONTENT Review Notes

- **RN-1:** The voice paragraph and the fallbacks. *Because* the UXD reads the product as "plain, quiet,
  utilitarian" (UXD § 1) and the PRD's first risk is that a web interface "adds parts" (PRD § Risks), so
  the voice is built to add as few words as the reader's next step needs. The two fallbacks are the
  inherited preference for naming the actor and the state, and for a complete plain sentence. They are
  marked replaceable because the rules below take their place wherever they speak.
- **RN-2:** Not casual. *Because* the same voice words a routine status move and an irreversible
  cascade deletion (UXD UX-I2), and a register that could joke at one could joke beside the other.
  This is a call with no corpus behind it, confirmed by the owner (`trail/content/cycle-1.md` § 2.1).
- **RN-3:** Completion lines start "You…". The UXD's own example is "Moved 'Set up CI' to done"
  (UXD UX-I4), which names no actor. *Because* the inherited fallback is that a reader can say who did it
  and what happened, and a line that drops the actor reads as a log. This changes the UXD's example, not
  its rule, since UXD UX-I4 requires only that the line "names what changed". Confirmed by the owner
  (`trail/content/cycle-1.md` § 2.2).
- **RN-4:** Typed values are quoted in straight single quotes everywhere. The UXD's examples disagree: UX-I4
  quotes "Set up CI" and UX-I2 writes "Delete Alpha and its 12 tasks?" with no quotes. *Because* a typed
  value can contain spaces, so the boundary of the value has to show, and a title that ends in a question
  mark would otherwise end the sentence ambiguously. The UX-I2 example is therefore written here as
  "Delete 'Alpha' and its 12 tasks?". Both UXD examples illustrate and neither is a rule.
- **RN-5:** "Terminal" replaces the UXD's "console" for the window the tracker starts from. *Because*
  the UXD itself says "a terminal" for the reader's starting point (UXD UX-U2) and the PRD says "terminal
  tool" (PRD § Why This), so "terminal" is the word the sources already use for the same window. This
  changes a word and no meaning.
- **RN-6:** Dates are `YYYY-MM-DD` and times are `HH:MM` on a 24-hour clock in local time. The UXD leaves
  the written form to this document (UXD Open Questions). *Because* the PRD fixes dates as calendar
  dates in the machine's local day (PRD § UX Notes, Defaults), a numeric form can't be read two ways
  across regions, and `DESIGN.md` sets table figures to line up, so a fixed-width numeric date suits the
  columns (`DESIGN.md` § Typography, "tabular figures"). Relative words are banned because pages don't
  update themselves (UXD UX-I9). Confirmed by the owner (`trail/content/cycle-1.md` § 2.3). Its one known
  collision, the browser's own date field, is settled there at § 1.1: the field is outside the rule.
- **RN-7:** The back-out word is "Back out", the confirming control repeats the action as a verb phrase,
  and the sentence has two parts. *Because* the UXD leaves the word to this document and forbids a word
  that reads as the status `cancelled` (UXD UX-I2), "Cancel" is rejected. "Back out" is the UXD's own
  phrase for the control. A confirming control that reads "Confirm" or "Yes" says nothing about what it
  does. Confirmed by the owner (`trail/content/cycle-1.md` § 2.4), with the addition that a project
  deletion's completion line gives the count read when the action ran.
- **RN-8:** Status and priority words are written as the PRD fixes them, lowercase, even as button labels.
  *Because* the PRD fixes the four status words as values (PRD § Core Features, Status workflow) and the
  UXD names the move buttons by the status they move to (UXD UX-I1), so a button labelled with a status
  uses the status as defined. Confirmed by the owner (`trail/content/cycle-1.md` § 2.5), with the exception
  widened to any string whose whole text is a status or priority word.
- **RN-9:** Partial and Recovered are omitted. The reasons are in the frontmatter. *Because* the UXD and
  the SRS leave no state for either to answer. Both confirmed by the owner (`trail/content/cycle-1.md` § 2.6, § 2.7),
  and the Recovered reason restated to say only what the sources say.
- **RN-10:** Three patterns beyond the five standing ones: Completed, Needs confirming and the ready
  line under Loading. *Because* each is a state the UXD names with words attached (UXD UX-I4, UX-I2 and
  UX-S2), and a state without a pattern is a state whose words nobody specified.
- **RN-11:** A not-found page says "There's no project at this address" and not "was deleted". The
  out-of-date refusal states the task's status and what it allows, and not "has changed", "in another tab" or "since this page loaded", because the page it lands on is built after the refusal and an address can't show an earlier event (RN-26). The unreadable-data page
  says "couldn't read" and not "corrupted". *Because* the tracker establishes none of those causes, and a
  message that names a cause it didn't establish is wrong in the most expensive way. The UXD's reasoning
  for those states names "another tab" and "deleted", which is the UXD's reasoning, and the string says
  the smaller true thing.
- **RN-12:** The terminal's diagnostics may carry the system's own error text verbatim. *Because* SRS
  NFR-8 requires the terminal to name "the action and the error" for a failure that is not a refusal, and
  the reader of the terminal is a developer. It is the one exception to the banned technical vocabulary
  and it doesn't reach the browser.
- **RN-13:** The summary's "(unassigned)" and a task row's "unassigned" are both kept. *Because* the PRD
  names "(unassigned)" in the summary (PRD § Core Features, Project summary) and the UXD names "unassigned"
  in a task row (UXD UX-S4), and the parentheses stop the summary row reading as a person.
- **RN-14:** Remove and Delete are two verbs, and Create and Add are two verbs. *Because* removing an
  assignee name leaves it on the tasks that carry it (PRD § Core Features, Assignees), so "Remove" can't
  mean what "Delete" means, and the UXD uses "Create" only for a project and "Add" for the rest (UXD
  UX-F2, UX-F3).
- **RN-15:** The reading bar is 20 words a sentence and no idiom, and "please", "sorry" and "successfully"
  are banned. *Because* the tracker has no corpus and these are checkable on one string, where a bar of
  "plain language" is not. They were confirmed by the owner along with the voice (`trail/content/cycle-1.md` § 2.1).
- **RN-16:** The corpus. tracker17 now has strings of its own, written after these rules were settled
  on 2026-10-06. They are in three files: `web/pages.py` (the pages, for instance "A project needs a
  name. Type one.", line 63), `web/routes.py` (the terminal line printed when an action fails, line 210)
  and `main.py` (the terminal's ready line and its failed-start line, lines 41 and 50). All three were
  committed on 2026-10-07. This is the state at the time of this revision, and the files are named so a
  reader can find the strings, not as a promise that they stay there. RN-2 and RN-15 give "no corpus"
  as the reason a call was made, and that records the position when the calls were made, when none
  existed. This note does not say whether the product's strings meet the rules: a Content Editor run
  on a change that publishes text, or an audit, finds that out. The predecessor's command-line wording
  is no longer the nearest evidence, though it still shows the shapes the formulas here replace.
  "Cannot change status from {current} to {new}." (the predecessor's
  `tasktracker16x/domain/transitions.py`, line 35) states a reason and no next action, and "Task {id}
  status: {new_status}" (`tasktracker16x/cli/app.py`, line 256) names no actor. The predecessor is not
  tracker17's corpus, and its command-line mechanics are out of scope (PRD § Out of Scope, "A command-line
  interface"). Owner answer, with its addition (`trail/content/cycle-4.md` § 2.1, reasoning in
  `trail/content/self_answer-4.md`).
- **RN-17:** No collision with `DESIGN.md` needs surfacing. Its rule that text wraps and nothing is
  shortened fits the whole-value quoting here, its refusal and completion notes hold one sentence each,
  and its confirmation strip leaves the order and focus to the UXD and the words to this document.
- **RN-18:** The "The running product" row no longer says `tracker17` appears only in page titles, and
  names no place for the name. *Because* that note was a placement rule written in this document's seat,
  and `DESIGN.md` is Settled on the placement: the product name sits on the left of the header
  (`DESIGN.md:350`) and the unreadable-data page's header shows it (`DESIGN.md:427`). Naming a place here would
  make this document a second home for a fact the design owns. The title pattern is stated once, in
  § Accessibility of text, and case once, in § Grammar and mechanics. Owner answer, in the wording the
  owner set (`trail/content/cycle-3.md` § 3.1, reasoning in `trail/content/self_answer-3.md`).
- **RN-19:** The not-found formula names a link to each place the tracker has, with "Open Projects." as
  the one-place form. *Because* a sentence that sends the reader to a place the tracker doesn't have
  claims what it can't keep (§ Voice, "State only what the tracker established"), and a definition
  document states no build order, so the formula carries no count. The two examples stand as the
  two-place form. The occurrence is the not-found page's one link, `web/pages.py` line 210. Owner
  answer (`trail/content/cycle-5.md` § 3.1, reasoning in `trail/content/self_answer-5.md`).
- **RN-20:** Two links with the same label and the same address are not a repeated label. *Because* the
  rule that adds a thing to an accessible name exists to tell controls apart by what they act on, a link
  acts on its destination, and the section already bars the opposite case, "Two links to different
  places never share their text". Naming one place two ways would run against the W3C's stated
  direction, "It is a best practice for links with the same destination to have consistent text"
  (https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html, re-read 2026-10-07). The
  occurrence is the two "Projects" links on the not-found page, `web/pages.py` lines 53 and 210, both to
  `/`. Owner answer (`trail/content/cycle-5.md` § 3.2, reasoning in `trail/content/self_answer-5.md`).
- **RN-21:** The two terminal-message examples name `127.0.0.1:8017`, with no note calling the address a
  placeholder. *Because* the terminal strings fill the address from the one the start was given and a
  real start prints `127.0.0.1:8017` (`main.py:20`, `main.py:55`, `main.py:61`;
  `tests/e2e/test_start_command.py:22`; `SDD.md:286`), so the example is the string the reader sees, and
  port 8000 was a string the product never printed. Owner answer, with its addition
  (`trail/content/cycle-6.md` § 3.1, reasoning in `trail/content/self_answer-6.md`).
- **RN-22:** The priority term takes `critical` as its fourth value, and the rejected list drops it. *Because* the PRD fixes the priority values (PRD § Core Features, Priorities, "A task is `low`, `medium`, `high` or `critical`"), and a priority value is product meaning, so the terminology row can't ban one of them. The row's rejected list gave no reason for banning `critical`. `critical` is written lowercase as defined, like the other three (§ Grammar and mechanics, Case), and it nowhere else appears in this document, so no other rule or example moves. Owner answer (`trail/content/cycle-7.md` § 3.1, reasoning in `trail/content/self_answer-7.md`).
- **RN-23:** The date rule bars every string that tells the reader to pick or type a date, a refusal included, and a refusal names the outcome instead. *Because* the tracker states no way of entering a date for a control whose look is the browser's own, so "Pick one" would claim a means the tracker doesn't establish. The rule keeps the words the owner confirmed ("type or pick", `trail/content/cycle-1.md` § 1.1), and "picked" in § Grammar and mechanics (Verbs for pressing) is for an option in a list and doesn't reach the date field. The refusal string at `web/pages.py:276` ends "Pick one", so it doesn't meet the rule. That is a finding for a change that publishes text, not an edit here. Owner answer (`trail/content/cycle-8.md` § 3.1, reasoning in `trail/content/self_answer-8.md`).
- **RN-24:** A refusal gives one action where one exists, and where none does its second sentence says what the page shows. *Because* the refusal formula is § Voice's rule applied to the usual case, where the reader has something to fix (§ Voice, "Give one next action when one exists, and none when none does"), and not a second rule overriding it. Where the wanted state already holds and the page shows it, the only action left is a reload that shows what the page already shows, which is the advice-closing guide § Voice rejects. § Tone, the Failure row and the Level 1 definition take the same "where one exists". The occurrence is the refusal for removing a label the task no longer carries, `web/pages.py:L717-L722`, which already follows the rule and needs no change. UXD version 8 (UX-F4, UX-I3) says no refusal offers a reload on a page built after it, and an out-of-date refusal now names the moves the page shows (`trail/uxd/cycle-5.md` § 2.1, `trail/uxd/cycle-6.md` § 2.2). Owner answer (`trail/content/cycle-9.md` § 3.1, reasoning in `trail/content/self_answer-9.md`). Revised by RN-27.
- **RN-25:** § Scope governs no output of a script a developer runs to check or measure the tracker, such as the timed run. *Because* the test in § Scope is who says the words, and the timed run is not the tracker speaking: it is a script a developer starts, it runs the pages in-process and never starts the tracker, so its output is not "the text the tracker prints in the terminal it was started from". No UXD state names it, so no pattern here answers to it, and § Voice's rules can't be applied to a row that reports a measurement. Where such a script prints a string the tracker wrote, the string is governed where the tracker writes it, so the clause leaves no gap. The clause states the kind of script and not a file, because this document holds standing rules and a path can move (RN-16). The occurrences are the rows that end " — refused or failed" and the fixture lines joined by "; " (`tests/timed_run.py:153`, `:158`, `:691`, `:783`). Their em dash, semicolon and "failed" break no rule here. If the UXD ever makes the run's output something the reader is told to read, § Scope follows it. Owner answer (`trail/content/cycle-10.md` § 3.1, reasoning in `trail/content/self_answer-10.md`).
- **RN-26:** A refusal the reader reached without a press states its reason as a fact about the task and what its status allows, names the move the address asks for where the address carries one, and gives no action and no reload. *Because* the tracker sees an address and can't establish that a press produced it, so "the move you pressed" claims what it didn't establish (§ Voice, "State only what the tracker established"), and after a saved move the status beside the line shows the move took effect, so the line would deny it. The formula's reason is a fact about what the reader typed or pressed, and this refusal has nothing typed or pressed to state a fact about. No action exists because the page is built from the saved data when it loads, `done` and `cancelled` are final (PRD § Core Features, Status workflow), and a reload shows the same page. A refusal shown after a redirect from a real press and then reloaded has the same property. The settled case is the second way in that UXD UX-F4 describes: the address that shows, or backs out of, the confirmation for a move to `cancelled`, opened again once the task is final (`trail/uxd/cycle-5.md` § 2.1, UXD UX-I3). UXD version 8 keeps that refusal, so the rule stands. The product's line for it meets the rule (`web/pages.py:L758-L761`, `_ADDRESS_LINE`). The clause "where the address carries one" is there because the address of the overtaken-move page carries the task and the refusal code and no move (`web/routes.py:L384-L396`), so that page can't name one. The finding is the other page's. The overtaken-move line (`_CHANGED` and `_OVERTAKEN_LINES`, `web/pages.py:L751-L757`) is read from the address on every load, so a reload, Back or a bookmark shows it again with no press. "Has changed to" is a claim about the past, and the tracker holds only the address, so an address typed for a task that was never moved shows the same line. That line doesn't meet this rule, and the rule has no gap: the formula's reach, "a reload, Back, or a saved or typed address", already includes that page. One line serves the first landing and every later visit, so the wording that fits both is the CDO's answer, which UXD version 9 holds (UX-F4, UX-I3, RN-35): the line states the task's current status and what it allows, and claims no change. The clause for a move another change overtook now says so, and the product's line still says "has changed to", so the finding stands for a change that publishes text, not for an edit here. Owner answer (`trail/content/cycle-11.md` § 3.1, reasoning in `trail/content/self_answer-11.md`), revised by the answer that confirms it with three additions (`trail/content/cycle-13.md` § 2.1, reasoning in `trail/content/self_answer-13.md`), and by the answer that follows the CDO's (`trail/content/cycle-14.md` § 3.1, reasoning in `trail/content/self_answer-14.md`).
- **RN-27:** The out-of-date refusal's examples are the two forms the product's tests pin, and the refusal formula gains a clause for a move another change overtook. *Because* the fifth example offered a reload that UXD version 8 (UX-F4, UX-I3) and the SDD's `status-moves` unit both bar, and the product's own wording follows them (`web/pages.py:L751-L757`, `tests/integration/test_move_routes.py:L87-L99`). The formula said "then one action where one exists", and the new examples name moves, not one action, so without the clause they would contradict their own formula. "Since this page loaded" is dropped from the banned-words row and RN-11 because the page the refusal lands on is built after the refusal, so the phrase dates a page that is not the one shown. The examples state the task's current status and claim no change, as UXD version 9 sets (UX-I3, RN-35), so they are true on a reload with no press (RN-26). The product's line and its tests still carry "has changed to" (`_CHANGED` and `_OVERTAKEN_LINES`), which is a finding for a change that publishes text, not an edit here. Owner answer (`trail/content/cycle-12.md` § 3.1, reasoning in `trail/content/self_answer-12.md`), revised by `trail/content/cycle-14.md` § 3.1 (reasoning in `trail/content/self_answer-14.md`).
