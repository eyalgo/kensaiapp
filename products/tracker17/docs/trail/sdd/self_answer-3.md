# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** two sources outside this repository, each read on 2026-10-06 through a page
  fetch that returned quoted passages.
  - https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html. It defines a status message as
    a "Change in content that is not a change of context". Its Intent section says "Changes of
    context, by their nature, interrupt the user by taking focus. They are already surfaced by
    assistive technologies, and so have already met the goal to alert the user to new content." Its
    form example reads "text is added to the existing form". The fetch found no sentence about a
    status role that is already in a page when the page loads.
  - https://html.spec.whatwg.org/multipage/interaction.html. It says "The `autofocus` content
    attribute allows the author to indicate that an element is to be focused as soon as the page is
    loaded", and "The `autofocus` attribute applies to all elements, not just to form controls." Its
    steps for applying the attribute stop when the document "has non-null target element", which is
    the case when the page's address ends in a fragment that names an element. It also says "User
    agents are required to set the sequential focus navigation starting point to the target element
    when navigating to a fragment."

This run was given two items, 2.3 and 2.4, and decided them in that order. The answer to item 2.4
reads the answer to item 2.3 as settled.

## Items worked

### 2.3 — No page runs a script, so every action reloads a whole page

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** overridden
- **Why:** Overridden in part. The page model is kept: no page runs a script, and every action is
  answered by a whole page. Two of the draft's three consequences are replaced. The draft said that
  after an action keyboard focus "starts where it starts on any freshly opened page", and that
  "Nothing announces" a completion line or a refusal apart from the page. The answer says the page
  opens at the place of the action with keyboard focus there, and that the line is read with the
  element the page opens on.

  *Why the verdict is "overridden" and not "confirmed with addition".* The item's own *If
  overridden* field names "An override that keeps the no-script page model and changes only where
  focus lands". This answer is that kind of override. It also reaches further than the field
  expects, because it rewrites `SDD.md` § 4 EX-4 and EX-5 and § 9 TO-2 as well as EX-6. Two drafted
  sentences are replaced and not added to, and "confirmed with addition" would have hidden that.

  *Seat.* This item is the CDO's, and this run answered it in that seat. `SDD.md`, under "Who
  decides what", gives "§ 4 — the experience conditions the UXD binds on every surface" to the CDO,
  and § 9 TO-2 says "The cost spends experience, so the CDO rules on it". Every edit lands in
  `SDD.md`. The answer commits nobody outside the product, and I can name no ground the owner holds
  that this run could not see.

  *The page model holds, for the reason the draft gives (check 2).* `UXD.md` § 1 weighs every
  decision against one question: "does it add a part the reader has to read?". `UXD.md` UX-I8 and
  UX-I9 already require whole pages that do not update themselves, and § 2 sets MOTION to 1. No UXD
  entry asks for part of a page to change in place. A script would be a second language for the
  reader, and the three conditions below can be stated without one.

  *The first consequence is confirmed, with three conditions.* A confirmation that is its own page
  load can carry `UXD.md` UX-I2's order and focus, if the page sets focus itself. The HTML standard
  allows that on any element (second source above). Three cases are not in the draft.
  - *In view.* `UXD.md` UX-I2 says the confirmation "appears where the first press was made". A
    task list is one page with no pagination (`UXD.md` UX-F5, "with no pagination"), and
    `SRS.md` NFR-1 sizes it at up to 1,000 tasks. The reason to expect trouble is that a newly
    loaded page opens at its top, so a confirmation far down a list would open out of view unless
    the page brings it into view.
  - *A double press.* `UXD.md` UX-I2 has the sentence cover the first button's whole spot "so the
    second click of a double click lands on words and never on a control". That clause was written
    for a sentence that replaces a button in the same window. After a page load the row can sit at
    a different height in the window, so the layout alone does not keep the clause. The answer
    states the outcome the clause protects: a double press never confirms. It asks for that on a
    list scrolled part-way, which is where the layout stops being enough.
  - *A first press on an out-of-date page.* With a page load, the first press reaches the tracker.
    `SDD.md` § 4 EX-7 says the moves offered "are the ones `domain` returns for the task's current
    status". If another tab has already finished the task, there is no first button on the new
    page for the confirmation to take the place of. The answer gives the operator the out-of-date
    refusal at once (`UXD.md` UX-F4, "The reason says the task's status has changed and offers a
    reload"), and the not-found page when the target is gone (`UXD.md` UX-F9).

  *The third consequence is replaced (check 2: the draft answers a smaller question).* The draft
  reads `UXD.md` UX-F4's "stays where they were" as "the same page at the same address". UX-F4 says
  more: "the operator stays where they were, with the row or page showing the new status". On this
  reading, an operator who moved a task far down a list and is shown the top of that list has not
  stayed where they were, and the row is not what they see. Refusals have the same problem.
  `UXD.md` UX-I3 puts the reason "beside the control that was used". The comment form "sits below
  the newest comment" (`UXD.md` UX-F7), and a project's rename control sits "below the list"
  (`UXD.md` § 4). A reason shown beside a control that has scrolled out of view does not do what
  `PRD.md` § UX Notes asks, which is that a refusal "tells the operator the reason". `UXD.md` UX-I2
  names the harm for a keyboard user in its own words: focus is set "so a keyboard user is not sent
  back to the top of the page". The draft would send that user back to the top after every other
  action, and `PRD.md` § UX Notes lists "moving a task to its next status" among what must feel
  effortless. The answer therefore holds the place: in view, with keyboard focus on it.

  *The second consequence is replaced.* The accessibility bar is met either way. W3C defines a
  status message as a change in content "that is not a change of context", and a new page is a
  change of context (first source above). So SC 4.1.3 asks nothing of a line that arrives with a
  new page. Two settled documents still say more than the criterion. `UXD.md` UX-A5 reads
  "confirmations and refusals announced to assistive technology without moving focus", and
  `CONTENT.md` reads "A status message is announced without moving focus." Under the draft nothing
  does the announcing. The draft marks the lines as status messages, and the reason to expect that
  the mark does nothing is `SDD.md` § 4 EX-1: "no page changes after it has loaded", so there is no
  change for the mark to report. That expectation was not checked with a screen reader. The answer
  keeps focus off the line and ties the line to the element the page opens on, as that element's
  description. On this reading the operator's focus has not moved, because it is where they acted,
  and the line is read there. Whether the status mark stays is the CTO's. Nothing in the answer
  rests on it.

  *What gives way.* `SDD.md` § 11 R-2 already answers a failed focus test with "TO-2's reversal,
  confined to `web`". The answer keeps that priority and widens it. The experience conditions are
  the UXD's, and `SDD.md` § 4 says "where the two differ the UXD is right". Two costs of the page
  model are accepted, and § 9 TO-2 records them: no part of a page changes in place, and a page
  reopens with the place in view but not always at the same height in the window.

  *Checked against the settled record (check 3).* `UXD.md` UX-I6 keeps the browser's own keyboard
  model, and the answer changes only where focus starts on a page. `UXD.md` UX-I2 says its
  confirmation "takes focus on purpose" and that completion lines and refusals do not, and the
  answer keeps both. `DESIGN.md` places the completion line "at the top of the sheet it concerns",
  which is why the top of that sheet is the place when the thing acted on has left the page.
  `SDD.md` § 4 RT-7 says a page is "a function of the tracker state and the page's address", so
  the place and the line travel in the address. No sentence of `UXD.md`, `DESIGN.md` or
  `CONTENT.md` has to move.

  *Failure paths (check 4).* Empty: on a page with nothing else on it, the place is the form that
  was used. Absent: a task moved out of a filtered list, a removed name or label, and a target
  another tab deleted are all "no longer on the page", and the answer names the place for them.
  Stale: a reload, or a return through the back button, shows the completion line again and opens
  at the same place, and `SDD.md` § 4 RT-8 keeps the action from repeating. Concurrent: the double
  press on a confirmation is covered above. Refused: covered by condition (2).

  *Named and not covered.* A double press on an ordinary move sends the move twice. The second is
  refused as out of date, so the page shows a refusal beside a task that did move. Nothing wrong is
  saved, and no page without a script can disable a button after one press. How typed text reaches
  the page that a refusal opens is the CTO's and is not ruled here. `SDD.md` § 4 RT-7 keeps no
  session and RT-8 answers every submission with a page address, so on this reading the text
  travels in the address. No screen reader was run, and nothing in
  `system/projects/tracker17/agari.md` runs one. Whether Chromium sets focus as the HTML standard
  describes is still `SDD.md` § 11 R-2's open risk, and this answer rests more on it than the
  draft did. The standard skips `autofocus` on an address whose fragment names an element (second
  source above), which the CTO needs to know before choosing the means.

  *Close calls.* I weighed confirming the draft's second consequence as written, because the
  accessibility bar is met without an announcement. I did not, because condition (3) costs one
  association per line and keeps two settled sentences true. I weighed putting the outcome at the
  start of the page's title, which a screen reader reads first. I did not, because `CONTENT.md`
  fixes the pattern ("Every page has a title that names its subject"), and that standard is the
  Content Manager's. I weighed raising the place rule on `UXD.md`, which does not state where a
  page opens after an action. I did not. No UXD sentence is false, the answer reads UX-F4, UX-I3
  and UX-A5 as they are written, and `SDD.md` § 12 says a gap found upstream "is an item in
  `products/tracker17/docs/SDD_open_issues.md`", which this item is. A focus test that fails in
  `first-project` or `status-moves` would tip it. UX-I2 itself would then be in question, and
  `SDD.md` "Who decides what" gives a *Reached when* that cannot be met to the seat whose half
  failed.

### 2.4 — What a person can watch at the end of each slice, as drafted from the UXD

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed. The behaviour lines and the UXD entries of *Traces to* stand,
  every *Delivers* is something a person can watch, and a screen may arrive in steps. Five additions
  complete the lines where the draft's own rule, the answer to item 2.3, or the UXD asks for more.

  *Seat.* This item is the CDO's, and this run answered it in that seat. `SDD.md`, under "Who
  decides what", gives the CDO "§ 6 *Reached when* — the behaviour observable in the running
  product", "§ 6 *Traces to* — the UXD section", and § 5 step 1's "that each entry is genuinely
  observable, not an architecture box". Every edit lands in `SDD.md` § 4 EX-12 and § 6.

  *The draft holds (check 2).* I read each of the eight behaviour lines against the UXD flow and
  screen it names, and found no line that says something the UXD does not. Each *Delivers* is in
  the form `SDD.md` § 5 step 1 asks for, "after this, <someone> can <do something they could not>".
  Arriving in steps does not break `system/experience/visual_restrictions.md` § 2,
  `no-placeholder-delivery`. That entry forbids "a placeholder or half-wired visual state". A page
  that shows only what works is a smaller whole page, and it has no hole and no dead control. The
  entry binds here because a slice's end is checked by "someone who **did not build it**"
  (`SDD.md` § 5 step 4), and the entry counts work as delivered once it is "handed to a person
  outside the run that produced it".

  *Addition (1), the draft's rule is right and its count is incomplete.* The item and `SDD.md`
  RN-14 say "two screens arrive here in steps". The behaviour lines themselves show four. The
  task's page gains its comments in `comment-on-a-task`, its moves in `status-moves` and Delete
  task in `delete-and-rename`. The not-found page, by `UXD.md` UX-S10, "links to Projects and All
  tasks", and All tasks does not exist before `narrow-and-sort`. The draft's rule covers controls
  and links. It does not cover words. `UXD.md` UX-S4's empty state "invites a first one, with the
  add-task form in view", and `CONTENT.md` writes it as "This project has no tasks yet. Give the
  first task a title and press Add." In `first-project` the project's page has no add-task form, so
  the second of those sentences would point at a control that is not there. That is the verbal
  half of the same fence entry: "filler wording left in a delivered surface". The setup
  instructions are the same case. `first-project` delivers them whole, and `protect-saved-data`
  later changes what a start does when the saved data cannot be read (`SDD.md` S-1, "Until that
  slice, a start that cannot read the saved data stops with one plain message"). Which words each
  slice uses is `CONTENT.md`'s and the Content Editor's. The rule that no words point ahead is
  the addition.

  *Addition (2), `SDD.md` § 4 EX-12 against the UXD.* EX-12 says one header "sits on every page".
  `UXD.md` UX-S9 says the page for saved data that cannot be read offers "no navigation into the
  tracker", and `UXD.md` § 4 says "no area of the tracker is reachable until the data is dealt
  with". The behaviour line of `protect-saved-data` already says "with no navigation". EX-12 is
  the sentence that differs, and `SDD.md` § 4 says "where the two differ the UXD is right". The
  item names EX-12, so the correction is made here.

  *Addition (3), what the answer to item 2.3 changes (check 3).* That answer makes the page an
  action opens start at the place of the action, and adds three conditions to the confirmation.
  `SDD.md` § 4 binds every slice to them. The lines name them at the slices where a checker first
  watches each one: the first refusal, in `first-project`; a result that lands below the fold, in
  `comment-on-a-task`; a move from a row and the first confirmation, in `status-moves`; and a
  confirmation below a long list, in `delete-and-rename`, because a project's delete control sits
  "below the list" (`UXD.md` § 4).

  *Addition (4), states a checker would have no reason to look for.* Each is in the UXD and is
  first delivered by the slice named. `UXD.md` UX-F2 has the create form say that "the description
  cannot be changed after the project is created", and that note is an answered product question
  (`UXD.md` RN-21). `UXD.md` UX-F8 refuses a blank name, and the Your name half of People arrives
  in `comment-on-a-task`, after the line in `tasks-in-a-project` that covers a blank assignee
  name. `UXD.md` UX-S7 makes All tasks "UX-S4's filter, sort and list", and UX-S4's rows carry the
  moves. The line in `status-moves` says "Every row" at a point where only a project's list
  exists, so the rows that `narrow-and-sort` adds need the same said of them. UX-S7 also has its
  own empty state. `UXD.md` UX-F11 says of the page for unreadable data, "Its only way forward is
  the instructions", and the drafted line does not say the page points there.

  *Addition (5), the UXD entries of Traces to.* `SDD.md` § 8 says *Traces to* fills a seed's
  `## Source`, "narrowed to what the seed's share touches". A seed that adds controls to a screen
  needs that screen in its source. `status-moves` adds the move buttons to the project's list and
  the task's page and traces to neither UX-S4 nor UX-S6. The same gap is on `first-project`,
  `project-summary` and `delete-and-rename`, and on the not-found page for the two slices that add
  to it. Two lines cite an entry they do not trace: `tasks-in-a-project` cites UX-F5 for the
  default order, and `narrow-and-sort` cites UX-F4 for a task leaving a filtered list. I counted
  each UXD entry against the *Traces to* lines and `SDD.md` § 4. UX-I5, UX-I6, UX-I9, UX-A1,
  UX-A2, UX-A3, UX-A5 and UX-A7 are in no slice's *Traces to*, and each is cited by a condition
  of § 4, which every slice rests on. Those need no entry, and the answer says so, so that their
  absence reads as decided.

  *Failure paths (check 4).* Empty: the project's page in `first-project` is covered by addition
  (1). Absent: an address for an area no slice has delivered yet is a wrong address, and `UXD.md`
  UX-S10 already covers "the address is wrong". Refused: a line that cannot be met is a re-cut,
  and `SDD.md` "Who decides what" gives it to "whichever half failed". Concurrent: two tabs are in
  the lines of `status-moves` and `delete-and-rename` already.

  *Named and not covered.* Stale: whether a later slice's tracker reads the data an earlier
  slice's tracker saved is not ruled here. Before `protect-saved-data`, data the newer build
  cannot read stops the start with one message. That is the CTO's, under `SDD.md` § 4 SD-5. The
  commands and artifacts of *Reached when* are the CTO's and are not part of this item, so the
  tests that check additions (3) and (4) are the CTO's to name.

  *Close calls.* I weighed adding UX-I3 and UX-I4 to every slice whose line shows a refusal or a
  completion line, as `first-project` and `status-moves` already list them. I did not, because
  `SDD.md` § 4 EX-4 and EX-5 carry both to every slice. I weighed overriding to deliver People
  whole, so that no screen is seen half-built. I did not. The answer to item 3.2 already keeps
  People in two halves on product grounds, and a page that shows only what works is not
  half-built.

## Left for the owner

None this run.

## Skipped

- **2.1 — The tracker runs on Python 3.11 or later and uses only the Python standard library when it
  runs** — its slot was already filled when this run reached it. It is left exactly as it stands.
- **2.2 — The tracker is supported on macOS and Linux, and not on Windows** — its slot was already
  filled when this run reached it. It is left exactly as it stands.
- **2.5 — The eight slices: what each delivers, and what each leaves to another** — its slot was
  already filled when this run reached it. It is left exactly as it stands.
- **3.1 — `delete-and-rename` is its own slice, and not part of `tasks-in-a-project`** — its slot was
  already filled when this run reached it. It is left exactly as it stands.
- **3.2 — People arrives in two halves, and there is no slice for People alone** — its slot was
  already filled when this run reached it. It is left exactly as it stands.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
