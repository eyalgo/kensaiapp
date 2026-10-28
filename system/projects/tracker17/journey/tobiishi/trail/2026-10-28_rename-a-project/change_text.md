# Change Text — Rename a project from its Tasks view

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing

---

## Text

### The Rename area on a project's Tasks view

**The field's visible label, in every state of the Tasks view**

> Project name

When the person sees it: they are on a project's Tasks view, below its list. The field holds the
project's saved name, and they can type a new one.

**The button after the field, in every state of the Tasks view**

> Save

When the person sees it: they have typed a name in the field and press Save to rename the project.
The spec fixes this label (CP-546). It is the only Save on the Tasks view, so its accessible name is
its visible label alone.

**The page after Save is pressed with exactly the project's saved name**

No string. The Tasks view shows no completion line, no refusal and no failure line (CP-553).

When the person sees it: nothing changed and nothing was saved, so there is nothing to report.

### The Rename area's completion line

**The project was renamed, shown on landing and again on reload, Back or Forward**

> You renamed '{previous name}' to '{new name}'.

`{previous name}` is the project's name just before this rename, as it was saved when the rename ran.
`{new name}` is the name the rename saved, exactly as typed, spaces and letter case included. Both
quotes belong to the string.

When the person sees it: the heading and title now show the new name. The line tells them what
the old name was, which they need if they want to rename the project back.

### The Rename area's refusal reasons

These are project creation's three reasons, unchanged. The Rename area shows them through the same
refusal path the Projects page's create form uses, and they are not written a second time (CP-555).
Each sits beside the Project name field and is that field's accessible description.

**The name typed is more than 200 code points**

> A project name can't be longer than 200 characters. Type a shorter one.

The number is the short-text maximum, written as creation's reason already writes it.

When the person sees it: the field holds the project's saved name again, and they can type a
shorter one.

**The name typed is empty, or only whitespace**

> A project needs a name. Type one.

When the person sees it: the field still holds what they typed, and they can type a name.

**Another project already has exactly the name typed**

> A project named '{typed name}' already exists. Choose a different name.

`{typed name}` is the name they typed, exactly as sent.

When the person sees it: the field still holds what they typed, and they can choose another name.

### The Rename area's failed-save line

**The save failed for a reason that is not a refusal, shown beside Save as its accessible description**

> The tracker couldn't rename the project to '{typed name}', and nothing was changed. What you typed is still in the form. Try again.

`{typed name}` is the name they typed, exactly as sent. The field holds the same text.

When the person sees it: the project still has its old name on every page. They can press Save
again.

### The terminal's message when a rename fails

**The save of a rename failed for a reason that is not a refusal**

> The tracker couldn't rename the project to '{typed name}', and nothing was changed.

`{typed name}` is the name the rename tried to save, exactly as sent. The line is printed on its own,
and the error text follows it on the next line, exactly as the error reported it, as every action's
failure already does in the terminal.

When the person sees it: they are a developer reading the terminal the tracker was started from, and
they need to know which action failed before reading the error.

### The timed run's rename labels

**The row timing the Save submission**

> rename a project at {task volume} tasks

**The row timing the page the rename lands on**

> rename landing page at {task volume} tasks

**The row adding the two together**

> rename total at {task volume} tasks

`{task volume}` is the fixture's task count, the same number every other row of the run uses.

When the person sees them: a developer reads the run's rows, each followed by its time and verdict as
the run already writes them.

### The timed run's rename fixture report

**The line stating what the rename was measured on**

> rename fixture: {volume line}; title of {title length} characters, comment of {comment length} characters, old name of {old name length} characters, new name of {new name length} characters

`{volume line}` is the run's existing task-and-comment count, the same one the move and delete fixture
lines start with. `{title length}` and `{comment length}` are the code-point lengths of a task of the
renamed project and of that task's first comment. `{old name length}` is the code-point length of the
renamed project's name as seeded. `{new name length}` is the code-point length of the name the run
saves.

When the person sees it: a developer checks that the rename was measured at the stated volume and at
ordinary text lengths.

---

## Wording decisions

- **The field's label is "Project name"**, not "Name" or "New name". The spec leaves the label to this
  stage (CP-548). The area has no heading, because CP-546 lists its parts as the field and then Save.
  So the label alone has to say what the field is when a screen reader reads it out of place, and on
  the Tasks view "Name" could be read as a task's. "New name" would be false on every ordinary load,
  when the field holds the current name.
- **The completion line names the old name as well as the new one.** CP-550 leaves this to this stage.
  The page no longer shows the old name anywhere, and the spec's way back from a rename is to rename
  again (spec § Out of Scope, "Renaming again is the way back"). A person can do that only if they
  know the old name. The line names it as part of the rename, never as the project's current name, so
  CP-551 still holds. The old name is the name saved when the rename ran, which the design.s rename
  outcome carries (design § 3 A, "The previous name is the name in the state when the action runs"), so the line claims nothing the tracker didn't
  establish.
- **The failed-save line says "the project" and quotes only the typed name.** CONTENT.md's rename
  example reads "The tracker couldn't rename 'Alpha', …", and its failure formula asks for the typed
  value to be quoted. The typed value is the new name. On a reload of the failure page the tracker
  holds only the address and the current saved name. If the name had changed in the meantime, a line
  naming the current name would describe a rename of a name the person never saw. "The project" is
  true on every load, and the heading beside the line already names the project.
- **The terminal message is the failed-save line's first sentence, unchanged.** Every existing
  terminal failure line is the first sentence of its page's failure line, for example creating a
  project. Using the same sentence keeps one string for one concept and asks for no value the page
  line doesn't already have.
- **The refusal reasons are not rewritten.** They are creation's, and the request bars a second
  scheme ("The project-creation validation and refusal wording must not be duplicated or replaced by
  a second scheme"). They already meet CONTENT.md's refusal formula.
- **The timed run's lines follow the run's own shape, not CONTENT.md.** CONTENT.md § Scope governs no
  output of a script a developer runs to measure the tracker (RN-25). The labels copy the existing
  three-row pattern ("delete a task at …", "delete landing page at …", "delete total at …"). The
  fixture report copies the move and delete fixture lines and adds the two name lengths, because the
  project name is the text this action changes. The edit fixture line does the same ("edited title of
  … characters").
- **Banned-word check.** Every string was checked against CONTENT.md § Terminology's banned list and
  § Grammar and mechanics (no "error", "failed", "successfully", "please", "click", no exclamation
  mark, em dash, semicolon or ellipsis in the tracker's own words) and against the writing bar. There
  were no hits. The product carries no check that enforces its vocabulary, so none was run. The
  semicolon in the timed run's fixture report is the run's existing separator, which CONTENT.md
  doesn't govern (RN-25).

---

## Findings for the Content Manager

None
