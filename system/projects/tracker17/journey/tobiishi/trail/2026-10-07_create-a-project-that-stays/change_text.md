# Change Text — Create a first project that stays after a restart

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is written to `products/tracker17/docs/CONTENT.md` (Version 3) and to
`system/doctrine/writing_bar.md`. A part in braces is the one variable part of its string, and the
line under the string says what fills it. Quotes, full stops, spaces and the hyphen in page titles are
part of each string and are placed exactly as shown.

### The terminal, when the tracker is ready

**The tracker answers requests, and nothing has been shown in the terminal before this**

> The tracker is running. Open {address} in your browser. Saved data is kept at {location}.

`{address}` is the address the tracker serves, written as `http://`, the host, a colon and the port,
with no trailing slash, such as `http://127.0.0.1:8017`. `{location}` is the absolute path of the
saved data's directory, with no trailing slash, such as `/Users/sam/tracker17/data`.

When the person sees it: they have just typed the start command, and they open the address in their
browser next.

### The terminal, when a start finds saved data it can't read

**The start stops, nothing is served, and the saved data is left as it was**

> The tracker didn't start, because it couldn't read its saved data at {location}. Nothing in it was changed.

`{location}` is the same absolute path the ready message states, with no trailing slash.

When the person sees it: they have just typed the start command, and the tracker has stopped
without serving. They know where the saved data is and that the tracker left it untouched.

### The terminal, when creating a project fails

**A create failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this
order, the second straight after the first.

> The tracker couldn't create '{name}', and nothing was changed.

> {error}

`{name}` is the project name exactly as it was sent, surrounding spaces included. `{error}` is the
underlying error exactly as the system reported it, on its own line, with the kind of error first,
then a colon, a space and the error's own text, such as
`PermissionError: [Errno 13] Permission denied: '/Users/sam/tracker17/data/tracker.json'`. Where the
error carries no text of its own, the line is the kind of error alone.

When the person sees it: they are reading the terminal after the browser showed that the project
couldn't be created, and they learn which action failed and what the system reported.

### The Projects page

**The page title, in every state of the page**

> Projects - tracker17

**The page heading, in every state of the page**

> Projects

**The header, on every page this change serves.** The product name, then the one link.

> tracker17

> Projects

The first is the product name as it sits in the header. The second is the header's link to the
Projects page, and its accessible name is the same word.

When the person sees it: on any page, they can open Projects from the header.

**No project exists yet**

> There are no projects yet. Type a name for your first project and press Create.

When the person sees it: first run, with the create form in view. They type a name and press Create.

**The create form's field labels**

> Name

> Description

**The note beside the description field, in view before Create is pressed.** Two sentences, in this
order.

> You can't change the description after you create the project. A description can hold up to {maximum} characters.

`{maximum}` is the description field's own maximum, the same number as that field's limit, written as
digits with no separator, which is `4000` today. Where the maximum is 1, the second sentence reads
`A description can hold up to 1 character.`

When the person sees it: before they create a project, so they know the description is set once
and how long it can be.

**The Create button**

> Create

**Refused: the name has no character other than spaces, tabs or line breaks, or is empty.** Beside
the name field.

> A project needs a name. Type one.

When the person sees it: they pressed Create with a blank name. The page opens with focus in the name
field, what they typed is still in both fields, and they type a name.

**Refused: another project already has exactly this name.** Beside the name field.

> A project named '{name}' already exists. Choose a different name.

`{name}` is the name as typed, exactly, surrounding spaces included.

When the person sees it: they pressed Create with a name already in use. The page opens with focus
in the name field, what they typed is still in both fields, and they change the name.

**Refused: the name is longer than its maximum.** Beside the name field.

> A project name can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the name's maximum, which is `200` today, written as digits with no separator. Where
the maximum is 1, the first sentence reads `A project name can't be longer than 1 character.` The
string quotes nothing that was sent.

When the person sees it: a request built by hand sent a name over the maximum, since the form can't
send one. The page opens with focus in the name field, both fields are empty, and they type a shorter
name.

**Refused: the description is longer than its maximum.** Beside the description field.

> A description can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the description's maximum, which is `4000` today, written as digits with no separator.
Where the maximum is 1, the first sentence reads `A description can't be longer than 1 character.`
The string quotes nothing that was sent.

When the person sees it: a request built by hand sent a description over the maximum, and the name
was not over its own. The page opens with focus in the description field, both fields are empty, and
they type a shorter description.

**The project couldn't be created, for a reason that is not a refusal.** Beside the Create button.
Three sentences, in this order.

> The tracker couldn't create '{name}', and nothing was changed. What you typed is still in the form. Try again.

`{name}` is the name as typed, exactly, surrounding spaces included.

When the person sees it: they pressed Create and the save didn't happen. The page opens with focus on
Create, what they typed is in both fields, and they press Create again.

### A project's page

**The page title**

> {name} - tracker17

`{name}` is the project's name, exactly as saved.

When the person sees it: in the browser tab and window title, on the page of one project.

**The project has no tasks, which is every project in this change**

> This project has no tasks yet.

When the person sees it: on any project's page, after its name and description.

**The page answers a successful Create, and on every reload of it**

> You created '{name}'.

`{name}` is the project's name, exactly as saved, surrounding spaces included.

When the person sees it: they pressed Create, the project is saved, and they have landed on its page.

---

## Wording decisions

- **The unreadable-data terminal message gives no action and doesn't point to the setup
  instructions.** The pattern's example in `products/tracker17/docs/CONTENT.md` § Message patterns,
  *Terminal messages*, ends "See Setting saved data aside in the setup instructions." That section
  doesn't exist in this change. The spec puts the setup instructions out of scope ("The setup
  instructions in `README.md`, beyond what the tests need. The next station delivers them.",
  `change_spec.md` § Out of Scope). `products/tracker17/docs/SDD.md` § 4 EX-12 also says no words point
  to something that isn't delivered yet. Writing the set-aside steps into the terminal would put
  instructions about the person's saved data ahead of the instructions that own them. The smaller
  true thing is the reason, the location and the fact that nothing changed, which is what CP-7
  requires. This gap is raised below as a finding.
- **The no-tasks sentence has no second sentence.** The Empty formula invites a next action, as in
  "This project has no tasks yet. Give the first task a title and press Add.", but this change has no
  add-task form. CP-17 bans "words inviting a first task". § Voice says to give "none when none does"
  exist.
- **A project's page title has no view part.** The CONTENT § Accessibility of text title pattern adds
  "a colon and the view where the page has views". A project's page has no Tasks or Summary view in
  this change, so its title is the name followed by " - tracker17".
- **The description note writes its number as `4000`, with no digit grouping.** CP-11 requires that
  the number, "read as a number, equals the description field's `maxlength`", and `4000` reads as
  that number with nothing to strip. CONTENT states no rule on grouping digits, so this choice is
  raised below as a finding. Both over-long refusals write their numbers the same way, so one number
  is written one way across the change.
- **The over-long refusals quote no typed value.** The refusal formula quotes "any typed value", but
  CP-20 requires the answering page to hold none of the sent text, and that requirement takes
  precedence.
- **The over-long name refusal states the maximum, though the name field doesn't.** UX-F2 keeps the
  maximum off the name field, which a person reads before pressing Create. The refusal is reached only
  by a request built by hand, and "Type a shorter one" can't be followed without the number.
- **Each over-long refusal has its own string**, rather than one string with the field's subject
  filled in. CONTENT § Localization says "No string is assembled from fragments", and "A project name"
  and "A description" carry their own article.
- **The terminal's failure line keeps the sentence that names the action and nothing was changed, and
  drops the browser message's second and third sentences.** "What you typed is still in the form" and
  "Try again" are about the browser page. The terminal needs "the action and the error" (CP-25) and
  the error text on its own line, as CONTENT § Message patterns, *Terminal messages* sets.
- **`{error}` is fixed as the kind of error, a colon, a space and its text.** "Exactly as the system
  reported it" left the Developer to choose whether the kind is shown. A line with the kind first is
  the form the system itself reports in, and it tells "permission denied" apart from "no space left".
- **The header carries the product name `tracker17` before the Projects link.** The design's line
  names the header's Projects link under the Projects page, and `products/tracker17/docs/DESIGN.md`
  § Layout, *Header*, puts "The product name … on the left". Writing it here leaves the Developer no
  word to choose. The same header is on a project's page.
- **The tracker says nothing when it is stopped.** CONTENT § Tone, *Across the lifecycle*, gives
  leaving as "Silence", and CP-3 asks only that the stop show no traceback.
- **A project with no description gets no string.** No sentence says it has none. The reader chose
  not to type one, so there is nothing to tell them.

---

## Findings for the Content Manager

- "A description can hold up to {maximum} characters." and the two over-long refusals: CONTENT
  § Grammar and mechanics, *Numbers*, says counts are numerals and doesn't say whether a number of
  1000 or more groups its digits (`4000` or `4,000`). For now these strings are written as `4000`,
  for the reason given under Wording decisions.
- "The tracker didn't start, because it couldn't read its saved data at {location}. Nothing in it was
  changed.": the *Terminal messages* rule says a start that fails "gives one action", and the only
  action CONTENT gives for unreadable data points to a setup-instructions section. No rule covers a
  start failure whose action isn't delivered yet. For now the string has no action. Recheck it when
  the setup instructions gain "Setting saved data aside".
- No string: CONTENT has a pattern for a failed action (UX-I5), but none for a page that couldn't be
  opened, where opening it was only reading. This change has one place that catches every failure
  that isn't a refusal (`products/tracker17/docs/SDD.md` § 4 OB-3), and the design's `Publishes text:`
  line names only the create failure. So no words are written for a failed read. Until the standard
  states a pattern for it and a later design names the place, such a page has no wording.
