---
version: alpha
name: tracker17
description: The design language of tracker17's browser pages — the pages a local process serves to the one operator at a desktop Chromium browser
colors:
  primary: "#23674A"
  primary-deep: "#1A523A"
  paper: "#EDF1EC"
  surface: "#FBFCFA"
  surface-sunk: "#DDE4DD"
  ink: "#18211C"
  ink-muted: "#4F5C54"
  late: "#AE2530"
  late-tint: "#FAE8E7"
  done-tint: "#E1EEE5"
typography:
  page-title:
    fontFamily: "system-ui, sans-serif"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.25
  section-heading:
    fontFamily: "system-ui, sans-serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
  table:
    fontFamily: "system-ui, sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "\"tnum\" 1"
  label:
    fontFamily: "system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.3
  control:
    fontFamily: "system-ui, sans-serif"
    fontSize: 15px
    fontWeight: 500
    lineHeight: 1.2
  meta:
    fontFamily: "system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.4
rounded:
  none: 0px
  xs: 2px
  sm: 4px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 40px
  mark: 3px
  row-control: 28px
  control: 36px
  cell-min: 96px
  form-max: 560px
  content-max: 1180px
components:
  page:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    width: "{spacing.content-max}"
    padding: "{spacing.xl}"
  header:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.section-heading}"
    padding: "{spacing.lg}"
  nav-link:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.primary}"
    typography: "{typography.control}"
    height: "{spacing.control}"
  nav-link-current:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    height: "{spacing.control}"
  page-title:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.page-title}"
    padding: "{spacing.lg}"
  sheet:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "{spacing.xl}"
  section-heading:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.section-heading}"
    padding: "{spacing.sm}"
  form:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    width: "{spacing.form-max}"
    padding: "{spacing.lg}"
  field-label:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "{spacing.xs}"
  text-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
    height: "{spacing.control}"
    padding: "{spacing.sm}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
    height: "{spacing.control}"
    padding: "{spacing.lg}"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
    height: "{spacing.control}"
    padding: "{spacing.lg}"
  button-secondary-hover:
    backgroundColor: "{colors.surface-sunk}"
    textColor: "{colors.ink}"
  button-move:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
    height: "{spacing.row-control}"
    padding: "{spacing.md}"
  button-move-hover:
    backgroundColor: "{colors.surface-sunk}"
    textColor: "{colors.ink}"
  button-confirm:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  confirm-strip:
    backgroundColor: "{colors.surface-sunk}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.sm}"
  table-head:
    backgroundColor: "{colors.surface-sunk}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    padding: "{spacing.md}"
  task-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.table}"
    padding: "{spacing.md}"
  wrap-cell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.table}"
    padding: "{spacing.md}"
    width: "{spacing.cell-min}"
  label-tag:
    backgroundColor: "{colors.surface-sunk}"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.xs}"
    padding: "{spacing.xs}"
  overdue-marker:
    backgroundColor: "{colors.late-tint}"
    textColor: "{colors.late}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.xs}"
  margin-mark-late:
    backgroundColor: "{colors.late}"
    width: "{spacing.mark}"
  margin-mark-done:
    backgroundColor: "{colors.primary}"
    width: "{spacing.mark}"
  note-done:
    backgroundColor: "{colors.done-tint}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.md}"
  note-refusal:
    backgroundColor: "{colors.late-tint}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.md}"
  link:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.body}"
  meta-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.meta}"
  empty-state:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.xxl}"
---

# DESIGN — tracker17

**Status:** Settled
**Owner:** CDO
**Version:** 3 — UXD versions 3 and 4 carried in: the confirmation's sentence takes the first button's place and keyboard focus, and shows the focus ring (RN-25); the three new sentences beside a field are field hints (RN-26); RN-14's reason now cites `SRS.md` FR-40, which closes the one open item. No token value changed
**Inputs read:** UXD Settled (version 4, no companion) · PRD Settled · SRS Settled · Agari no Status line (`agari_template.md` carries none) · visual_direction Settled · visual_restrictions Settled · tracker17 doctrine no Status line (stamped, unfilled)

> The design language is the visual source of truth: the tokens are normative, the prose says
> how to apply them. It is authored off the UXD's § Design-System Direction — that section names
> the system and the constraints; **this document holds every value**. A token value that also
> appears in the UXD is a defect of whichever document copied it. Unlike the UXD, this document
> may legitimately trail the SDD: structural UX must be settled before the architecture locks,
> visual language iterates. Updated in place with versioning (bump the line above whenever a value
> or the prose changes); on a revision it is **stable by
> default** — every changed value traces to an owner answer, a brand change, or an upstream UXD
> change, never a silent re-derivation. Evidence binds where it exists (the product's own
> source, its brand assets, the UXD's direction); where it is silent the value is the CDO's call,
> written here with a stated reason, and the load-bearing calls go to the companion file for
> sign-off. Declare a genuinely inapplicable category in `omitted:` rather than leaving it
> silently absent.

Every value below is a CDO choice. tracker17 has no source code and no brand asset yet, so nothing
was found to carry (RN-1). The owner confirmed the load-bearing choices, each with additions, in the
answered round kept at `products/tracker17/docs/trail/design/cycle-1.md` § 2. Each Review Note names
the item that holds its call, and the reasoning behind every answer is
`products/tracker17/docs/trail/design/self_answer-1.md`.

---

## Overview

tracker17 is a worked example: a small task tracker that one developer runs on their own machine,
reads end to end, and judges. The pages look like a worked example written out on an engineer's
computation pad. A pale green-grey page carries square white sheets, the text is a green-black ink,
and actions are a deep drafting green. One red pencil marks whatever needs the operator's attention.
Nothing else on the page asks for attention.

The feel is quiet, flat and finished. It is an app a reader recognises as an app, with a header, a
table and a form, and nothing that makes them stop to work out the layout. The design spends its one
bold move on the **margin mark**: a 3-pixel rule at the left edge of a row or a message. The mark is
red pencil on what needs correcting, an overdue task or a refused action. It is green on what just
succeeded, the one-line confirmation.

**The system is plain semantic HTML with the browser's own form controls, styled by one small
stylesheet the product writes itself.** It is built from primitives, with no component library, no
classless framework, no icon set and no web font. When no token or rule here covers a case, decide
it by these two first, in order:

1. **Legibility of the operator's task state beats ornament.** Prefer the choice that makes a task's
   status, priority, assignee, due date and overdue state easier to read off the screen. A
   decoration that obscures state is wrong even when it is the prettier choice.
2. **Finished beats expressive.** Prefer the plain choice executed completely to the ambitious one
   executed partially.

Only where those two leave the options tied, decide by these three, in order:

3. Choose the option that adds the fewest lines to the stylesheet. The reader reads all of it.
4. Choose the option that leaves the browser's native behaviour in place.
5. Choose the option that keeps red for the margin mark's meaning alone.

## Colors

The product has **one colour mode, light, and no mode switch.** The stylesheet declares
`color-scheme: light` on the root element. Chromium then draws its own controls, pop-ups and
scrollbars in light, the date picker and the select list included, and that one declaration is what
keeps the date picker's pop-up in the product's mode. The stylesheet also sets `accent-color` to
{colors.primary}, so the native checkbox takes the product's action colour. `accent-color` reaches
only check boxes, radio buttons, range sliders and progress bars. It does not reach the date picker,
so no rule here may rely on it there. Every native control therefore sits in the same mode as the
product's own styling.

- **{colors.paper}** is the page. The header and the page title sit directly on it.
- **{colors.surface}** is a sheet: the white ground of every table, form, summary and comment list.
  It is also the text colour on the two dark buttons.
- **{colors.surface-sunk}** is the one sunk tone. It fills a table's header row, a label tag, the
  in-place confirmation strip and a hovered secondary button. As a 1-pixel line it divides one task
  row from the next.
- **{colors.ink}** is all body text, all headings and the confirming button's fill. It is never
  `#000`.
- **{colors.ink-muted}** is secondary text: column headers, a project's description, a comment's
  author and time, the match count and the hint beside a field. As a 1-pixel line it is the edge of
  every text field, select, date field and secondary button, and the line under the header.
- **{colors.primary}** is the action colour: the primary button, every link, the current focus
  ring, the green margin mark and the native `accent-color`. {colors.primary-deep} is the primary
  button under the pointer.
- **{colors.late}** is the red pencil. It appears in exactly three places: the red margin mark,
  the "Overdue" marker's text and the left edge of a refusal. It never colours a heading, a button,
  a status or a priority.
- **{colors.late-tint}** is the ground under the "Overdue" marker and under a refusal message.
  **{colors.done-tint}** is the ground under a confirmation.

Status and priority carry no colour at all. They are words in their own columns, so they read
without colour by construction. The overdue state is the "Overdue" word first, and its red tint and
the margin mark only reinforce it.

## Typography

One family, **`system-ui, sans-serif`**, and no font file. The face is the operating system's own
interface face, so tracker17 reads like the other apps on the operator's machine. Nothing is
fetched, and no font file ships in the copy.

| Level | Used for |
|---|---|
| {typography.page-title} | The one `h1` per page: a project's name, "All tasks", "People", a task's title, and the UX-S9 and UX-S10 messages. |
| {typography.section-heading} | Every `h2`: a summary group, "Comments", "Your name", "Assignees", a form's heading. It also sets the product name in the header. |
| {typography.body} | Running text: descriptions, comments, empty states, confirmations, refusals and inline links. |
| {typography.table} | Every task table cell and every summary count. It switches on tabular figures, so due dates, counts and times line up in their columns. |
| {typography.label} | Form field labels, table column headers and the "Overdue" marker. |
| {typography.control} | The text inside every button, text field, select, date field and nav link. |
| {typography.meta} | Comment author and time, field hints, the match count and label tags. |

**Every type size is applied relative to the root, in `rem`, and never in `px`.** The tokens above
state pixels, and they hold at the browser's default 16-pixel root, where 1rem is 16 pixels: the
stylesheet writes {typography.body} as `1rem`, {typography.table} as `0.9375rem`, and so on. A size
written in `px` overrides the operator's own font-size setting, and a size in `rem` follows it.

Headings use weight 600 and nothing else is bold. Column headers are sentence case and are never
set in capitals. A comment keeps the line breaks the operator typed.

## Layout

The page is a single centred column, at most {spacing.content-max} wide, with {spacing.xl} of
paper on each side. Spacing comes from one 4-pixel scale: {spacing.xs}, {spacing.sm},
{spacing.md}, {spacing.lg}, {spacing.xl} and {spacing.xxl}. A gap between two elements always
takes one of those six values.

- **Header.** The product name sits on the left, and the three nav links, Projects, All tasks and
  People, follow it on the same line. The header wraps onto a second line when the window is
  narrow. A 1-pixel {colors.ink-muted} line runs under it.
- **Forms are one column**, with each label above its field. A form is at most {spacing.form-max}
  wide, and its fields fill that width. A form therefore reflows at 400% zoom without a second
  scrollbar.
- **The filter controls** sit in a wrapping row above the task table: each one a label above its
  control, then Apply and Clear. At 400% zoom they stack into one column.
- **The task table** is one row per task with each attribute in its own column. The columns in
  order are title, status, priority, assignee, labels, due date and moves. All tasks adds the
  project column after the title. The title column takes the spare width, and every other column
  is as wide as its content needs.
- **Long text wraps, and the stylesheet shortens nothing.** Text breaks between words first. It breaks inside
  a word only when that word alone is wider than the space it sits in (`overflow-wrap: anywhere`).
  Labels wrap onto further lines inside the labels cell. No text anywhere ends in an ellipsis, and
  no value is hidden behind a tooltip. A row grows taller rather than losing an attribute to a
  second row.
- **The rule reaches every value the operator typed, on every page**, and not only table cells: a
  task's or project's name as a page title, a description, a comment, a label tag on the task page
  and a name on People. One unbroken string in a page title would otherwise push the whole page
  sideways.
- **The four columns that wrap keep a minimum width.** The title, labels, assignee and project
  columns are each a {components.wrap-cell}, at least {spacing.cell-min} wide: about twelve
  characters of {typography.table}. The stylesheet applies it as `6rem`, so it grows with the
  operator's font size like the type does. Below that width the table stops narrowing and scrolls
  in its own container, as the next rule says, rather than stacking a title one letter per line.
- **A select is capped at its container's width.** A select whose option is a long name or label
  would otherwise push its row past the window. Capped, the closed control shows as much of the
  value as the browser draws, and the open list shows every value whole. This is the one place a
  value may be cut, and it is cut by the browser's own control, not by the stylesheet.
- **The task table sits in its own horizontal scroll container.** When the window is too narrow for
  the table, only that container scrolls sideways. The page around it never does. WCAG 2.2 SC
  1.4.10 Reflow exempts data tables (`products/tracker17/docs/UXD.md` UX-A7, "The task tables are
  exempt").
- **Cells** take {spacing.md} of padding on every side. The moves in one cell sit side by side,
  {spacing.sm} apart.
- **Summary** is a set of small two-column tables, Status, Priority, Due dates and Assignees, each
  on its own sheet. The sheets sit side by side and wrap.
- **Comments** run down the task page's comment sheet, oldest first. Each comment has its author
  and time on one meta line above the text, and a 1-pixel {colors.surface-sunk} line separates
  one comment from the next.

## Elevation & Depth

**Nothing is elevated, and there is no shadow anywhere.** Depth is two tones and two line weights.
A sheet of {colors.surface} sits on the {colors.paper} page with no border. Inside a sheet, a
1-pixel {colors.surface-sunk} line divides rows and comments. A 1-pixel {colors.ink-muted} line
draws the edge of a control and runs under the header. Nothing floats, so no overlay, dialog or
toast exists to need a shadow. The confirmation for an irreversible action appears in place, in the
flow of the page.

## Shapes

Three radii, each with one job.

- **{rounded.none}** is a sheet. A sheet of the pad is square.
- **{rounded.sm}** is every control: buttons, text fields, selects and the date field.
- **{rounded.xs}** is a small inline token: a label tag and the "Overdue" marker.

The checkbox keeps Chromium's own shape, coloured by `accent-color`. The margin mark is square.

## Components

Each contract below holds wherever the component appears. The stylesheet styles **every** button,
text field, textarea, select, date field, checkbox and link it renders. None is left in the
browser's default look beside a styled one.

- **Focus, on every control and link, and on any other element a page sets focus on.** On
  keyboard focus, `:focus-visible` draws a 2-pixel {colors.primary} outline 2 pixels outside the
  control's edge. An element that is not a control and takes focus as the page opens, such as the
  confirmation's sentence (UX-I2), draws the same ring on `:focus`, so the ring shows wherever
  focus has landed (RN-25). The ring is measured against the
  ground it is drawn on, and five grounds take focus: {colors.paper}, a {colors.surface} sheet, the
  {colors.surface-sunk} confirmation strip, the {colors.late-tint} refusal around the reload
  control it offers, and the {colors.done-tint} confirmation. Against each it clears the 3:1 that
  SC 1.4.11 asks of a focus indicator (RN-7). No control removes the ring.
- **{components.page}** and **{components.header}** frame every page. On UX-S9, the unreadable-data
  page, the header shows the product name and no nav links.
- **{components.nav-link}** is one of the three header links, at least {spacing.control} tall.
  **{components.nav-link-current}** marks the area the page belongs to. It has ink text and a
  2-pixel underline, set with `aria-current="page"`, so the current area is told by the underline
  and not by colour.
- **{components.page-title}** is the page's `h1`, on paper above the first sheet.
- **{components.sheet}** holds every table, form, summary group, comment list, empty state and the
  UX-S9 and UX-S10 messages.
- **{components.form}**, **{components.field-label}** and **{components.text-field}** make every
  form. Text inputs, the comment textarea, selects and date fields all take the text-field contract
  and a 1-pixel {colors.ink-muted} edge. A field hint sits under its field, above the
  form's submit, in {components.meta-text}. The product has four: the two notes beside a project's
  description (it cannot be changed later, and the most characters it holds), the most characters a
  comment holds, and the note beside the assignee control when the task's assignee has left the
  list. A hint is never put inside a field or an option (RN-26).
- **The comment textarea is the one exception to the text-field height.** It keeps the contract's
  colour, edge, radius, padding and type, but not {spacing.control}, which is one line, because a
  comment is multi-line and keeps the line breaks the operator typed. It opens four lines tall from
  its own `rows="4"` attribute, the stylesheet sets no height on it, and it keeps the browser's own
  vertical resize handle.
- **{components.button-primary}** is the form's submit: Create, Add, Save and Apply. Each form
  has exactly one. Under the pointer it is {components.button-primary-hover}.
- **{components.button-secondary}** is every other full-size button: Clear, Remove, Rename's
  Save, Delete project's first press, Delete task's first press and the back-out control. It has a
  1-pixel {colors.ink-muted} edge, and {components.button-secondary-hover} is its pointer state.
- **{components.button-move}** is a status move on a task row or on the task page. It is
  {spacing.row-control} tall, which clears SC 2.5.8's 24-pixel floor, and it carries the same edge
  as the secondary button. The move to `cancelled` uses the same contract as every other move. Its
  second, confirming press is what sets it apart.
- **{components.confirm-strip}** replaces the first button in place when an irreversible action is
  pressed (`products/tracker17/docs/UXD.md` UX-I2). It holds the consequence in words,
  **{components.button-confirm}** and a back-out {components.button-secondary}. The sentence stands
  in the first button's spot and is at least as tall as that button. The confirming button takes the
  first button's height too. That height is {spacing.row-control} in a task row and {spacing.control}
  elsewhere. The confirming button is ink, the darkest fill the product has,
  because an inked line cannot be erased. The order of the strip's parts, and which part takes
  keyboard focus when the strip appears, are not this document's. They are component anatomy and
  accessible behaviour, and `products/tracker17/docs/UXD.md` UX-I2 owns them.
- **{components.table-head}** and **{components.task-row}** make the task tables on Project — Tasks
  and All tasks, and the count tables on Summary. A task row with the overdue state carries
  **{components.margin-mark-late}** along its left edge. **Every task row reserves that
  {spacing.mark} edge**, and the edge is transparent on a row that carries no mark, so every title
  in the column starts at the same place. The title, labels, assignee and project cells are each a
  **{components.wrap-cell}**, whose width token is the cell's minimum width (`min-width`), because
  the format has no separate minimum-width property (§ Layout). An overdue row's due-date cell holds
  **{components.overdue-marker}**: the word "Overdue" beside the date. The task page shows the same
  marker beside its due date.
- **{components.label-tag}** shows one label, on a task row and on the task page. Tags wrap, with
  {spacing.xs} between them.
- **{components.note-done}** is UX-I4's one-line confirmation, at the top of the sheet it concerns,
  with **{components.margin-mark-done}** on its left edge.
- **{components.note-refusal}** is a refusal or a failure (UX-I3, UX-I5), set directly beside the
  control that was used, with {components.margin-mark-late} on its left edge. The message text is
  ink, and the red is in the mark and the tint only. The red mark is the same one an overdue row
  carries, and it means the same thing: this needs your attention.
- **{components.link}** is underlined in every state. A task title in a row, a summary count, the
  project column and the links on UX-S10 all use it. A link that stands alone in a table cell, such
  as a summary count, has a box at least 24 pixels on each side.
- **{components.empty-state}** is the sheet's content when it has nothing to list. It holds a
  sentence and the form or link the sentence invites, with the same type as running text. It is
  never an illustration, an icon or a grey box.
- **{components.meta-text}** is secondary text: a comment's author and time, a field's hint, the
  match count above a table.

## Do's and Don'ts

- Do declare `color-scheme: light`, so every native control and pop-up draws in the product's one
  mode, and set `accent-color` to {colors.primary}, so the native checkbox takes the action colour.
- Do write every type size in `rem`, never in `px`.
- Do reserve the margin mark's edge on every task row, transparent where the row carries no mark.
- Do style every instance of every control the product renders. A control left in the browser's
  default look beside the product's own styling is unfinished work, and tracker17 does not ship it.
- Do show status, priority and the overdue state as words. Colour may reinforce the overdue word,
  and nothing else.
- Do keep the task table to one row per task, and let long text wrap inside its cell.
- Do give every control a pointer target at least 24 pixels on each side.
- Do keep the 2-pixel {colors.primary} focus ring on every control and link.
- Do load nothing from outside the machine. Every asset a page uses ships in the copy, and the only
  font is the system's own.
- Don't animate anything. No transition, fade or spinner exists, and a page appears whole when it
  is ready.
- Don't show a placeholder, a skeleton or filler text. An empty state is a sentence and the control
  it invites.
- Don't add a second colour mode or a mode switch.
- Don't add a shadow, a gradient, an icon or an image.
- Don't truncate a value with an ellipsis or hide it behind a tooltip. A capped select's closed
  control, which the browser draws, is the one exception (§ Layout).
- Don't use {colors.late} for anything but the margin mark, the "Overdue" marker and a refusal.

---

## DESIGN Review Notes

- **RN-1:** There is no source evidence to carry, so every value here is chosen. `products/tracker17/`
  holds only `docs/` (`find products/tracker17 -type f`, 2026-10-06, lists the PRD, SRS, UXD and
  their trails). tracker16-X, the predecessor named in the project card's `Source material:` field,
  is a command-line tool with no styling to observe. `grep -rniE "style\(|color|colour|secho"`
  over `task-tracker-X/tasktracker16x` returned no match (exit 1,
  2026-10-06).
  The instance's visual layer sets no shared value (`system/experience/visual_direction.md`
  § Colors, "This instance carries no shared colour"). *(re: every token; source: the commands named)*
- **RN-2:** The engineer's computation pad as the product's world — *because* tracker17 is "a worked
  example" (`products/tracker17/docs/PRD.md` § Purpose), and the pad is where an engineer writes a
  worked example out. The pad gives the palette, the square sheet and the red pencil one source. The
  pad reads "worked example" more literally than the PRD means it, so it is a taste choice that fits
  the product, not one derived from it. It brings no texture, ruled line, image or font, so it adds no
  part the reader has to read (`products/tracker17/docs/UXD.md` § 1). The owner confirmed it, and
  added that § Overview's own three fallbacks rank below the two this product inherits (RN-23)
  (confirmed: `products/tracker17/docs/trail/design/cycle-1.md` § 2.1). *(re: § Overview; source:
  owner answer plus stated design reason)*
- **RN-3:** One light mode, on {colors.paper} with {colors.ink} and {colors.primary} — *because* the
  UXD leaves the mode to this document (`products/tracker17/docs/UXD.md` § 9, "Which mode is the
  design language's call"), and the read in § Overview, a pale sheet written in dark ink, is a light
  mode by construction. The page is a tinted paper and the ink is a green-black, so no text is pure
  `#000` on pure `#FFF`. The pale green-grey page is the one aesthetic risk this document takes, and
  it costs no legibility: every text pair on it clears AA by a wide margin (RN-7). The owner confirmed
  the palette and replaced v1's reason for light, "the mode a desktop app is most often recognised
  in", which cited nothing (confirmed: `products/tracker17/docs/trail/design/cycle-1.md` § 2.2).
  *(re: {colors.paper}, {colors.surface}, {colors.ink}, {colors.primary}; source: owner answer plus
  stated design reason)*
- **RN-4:** `color-scheme: light` and `accent-color` — *because* the owner's answer to the UXD round
  requires that native controls and pop-ups "render in the same single colour mode as the product's
  stylesheet" (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.1). A pop-up such as the date
  picker cannot be styled by a stylesheet and follows the scheme the page declares
  (`products/tracker17/docs/UXD.md` RN-22). `color-scheme` sets "the default colors of form controls"
  and of "other browser-provided UI" (MDN, https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme),
  so it alone keeps the date picker in light. `accent-color` reaches check boxes, radio buttons, range
  sliders and progress bars only (MDN, https://developer.mozilla.org/en-US/docs/Web/CSS/accent-color),
  so v1's claim that it colours the date picker's selected day was dropped
  (confirmed with an addition: `products/tracker17/docs/trail/design/cycle-1.md` § 2.2). *(re:
  § Colors; source: owner answers, 2026-10-06)*
- **RN-5:** {colors.late} is the only red, reserved for the overdue state and refusals — *because* on
  the pad red pencil marks what needs correcting, and both an overdue task and a refused action ask
  the operator to look and do something. One reserved colour keeps the overdue state findable at a
  glance down a table, which `PRD.md` § UX Notes lists as effortless ("seeing which tasks are
  overdue"). A second attention colour for refusals would add a tint, a contrast pair and a rule, and
  the two never stand where they could be confused: one marks a table row and carries a date and a
  word, the other sits beside the control that was used and carries a sentence. The owner confirmed
  refusals sharing the overdue red (confirmed: `products/tracker17/docs/trail/design/cycle-1.md`
  § 2.5). *(re: {colors.late}, {colors.late-tint}; source: owner answer plus stated design reason)*
- **RN-6:** Status and priority carry no colour — *because* UX-A4 requires them to read without
  colour (`products/tracker17/docs/UXD.md` § 8, "never by colour alone"). A column of coloured
  statuses would also compete with the red pencil. Words in their own columns meet UX-A4 with no
  extra rule in the stylesheet. Part of the palette call (confirmed:
  `products/tracker17/docs/trail/design/cycle-1.md` § 2.2). *(re: § Colors; source: owner answer
  plus UXD constraint)*
- **RN-7:** Every text and control pair clears WCAG AA — *because* UX-A5 sets SC 1.4.3 and SC 1.4.11
  as the floor (`products/tracker17/docs/UXD.md` § 8). Computed with the WCAG 2.x relative-luminance
  formula on 2026-10-06: {colors.ink} on {colors.paper} 14.45, on {colors.surface} 16.03 and on
  {colors.surface-sunk} 12.74. {colors.ink-muted} on {colors.paper} 6.15, on {colors.surface} 6.82,
  on {colors.surface-sunk} 5.42 and on {colors.late-tint} 5.94. {colors.primary} on {colors.surface}
  6.56 and on {colors.paper} 5.91. {colors.surface} on {colors.primary} 6.56 and on
  {colors.primary-deep} 8.83. {colors.late} on {colors.late-tint} 5.72. {colors.ink} on
  {colors.done-tint} 13.79 and on {colors.late-tint} 13.95. {colors.surface} on {colors.ink} 16.03.
  The control edge ({colors.ink-muted}) clears 3:1 against paper, sheet and the refusal tint. The
  focus ring ({colors.primary}) is measured against the ground the control sits on (W3C, "it needs
  to contrast with the background that the component is on",
  https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). It clears 3:1 on all five
  grounds that take focus: paper 5.91, sheet 6.56, {colors.surface-sunk} in the confirmation strip
  5.21, {colors.late-tint} around a refusal's reload control 5.71, and {colors.done-tint} 5.65. The
  last three grounds were added by the owner's answer (confirmed with an addition:
  `products/tracker17/docs/trail/design/cycle-1.md` § 2.2), and every figure here was recomputed for
  this revision. *(re: every colour pair; source: UXD constraint plus owner answer)*
- **RN-8:** {colors.surface-sunk} as a row divider is 1.26:1 against {colors.surface} — *because* a
  row divider is decoration. The table's structure is carried by its markup and its columns.
  SC 1.4.11 asks 3:1 of "Visual information required to identify user interface components and
  states" and of "Parts of graphics required to understand the content"
  (https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), and on this reading a row
  divider is neither. A faint divider keeps DENSITY 6's breathing room (`products/tracker17/docs/UXD.md` § 2). *(re:
  {colors.surface-sunk}; source: stated design reason)*
- **RN-9:** `system-ui, sans-serif` and no font file — *because* the UXD forbids a hosted font
  (`products/tracker17/docs/UXD.md` § 9, "No hosted font, stylesheet, icon set or script"). A
  shipped font would be one more asset for the reader to account for, against `PRD.md` § Risks ("a
  web interface adds parts"). TYPOGRAPHY 2 asks for type with no personality of its own
  (`UXD.md` § 2), and the operating system's face is exactly that (confirmed:
  `products/tracker17/docs/trail/design/cycle-1.md` § 2.3). *(re: every typography level; source:
  owner answer plus UXD constraint)*
- **RN-10:** The type sizes are reading sizes, not a ratio, applied in `rem` — *because* each level
  was set from what it holds. Body is 16 pixels, Chromium's default root. Table text is 15 pixels so
  a seven-column row fits a desktop window. Labels and meta are 14 pixels, the smallest size the
  product sets. The page title at 24 pixels is the one size step that marks where the reader is. A
  page reads at the operator's own browser setting only when its sizes are relative to the root:
  "Defining font sizes in `px` is not accessible, because the user cannot change the font size in
  some browsers" (MDN, https://developer.mozilla.org/en-US/docs/Web/CSS/font-size). So the tokens
  keep their pixel values, which hold at the default root, and the stylesheet writes them in `rem`
  (confirmed with an addition: `products/tracker17/docs/trail/design/cycle-1.md` § 2.3). A raised
  setting widens the task table past a desktop window, and the table then scrolls in its own
  container (RN-15). *(re: {typography.page-title} to {typography.meta}; source: owner answer plus
  stated design reason)*
- **RN-11:** Tabular figures on {typography.table} — *because* due dates and counts are compared down
  a column (`products/tracker17/docs/PRD.md` § Key Use Cases 4), and proportional digits make equal
  dates differ in width. A `system-ui` face without the `tnum` feature ignores the setting, which
  degrades alignment and breaks nothing. *(re: {typography.table}; source: stated design reason)*
- **RN-12:** Density and motion: {spacing.md} cell padding, {spacing.row-control} move buttons,
  {spacing.control} for every other control, and no motion at all — *because* the UXD sets DENSITY 6
  and MOTION 1, "no animation or transition beyond what the browser does by itself"
  (`products/tracker17/docs/UXD.md` § 2). A 28-pixel move button keeps the row compact and still
  clears UX-A6's 24-pixel floor. The comment textarea is exempt from {spacing.control}, which is one
  line, because a comment is multi-line and keeps its typed line breaks. A one-line box for
  multi-line text would look unfinished. Its four-line height comes from its own `rows` attribute,
  which costs no stylesheet line and leaves the browser's resize handle in place (confirmed with an
  addition: `products/tracker17/docs/trail/design/cycle-1.md` § 2.4). *(re: {spacing.md},
  {spacing.row-control}, {spacing.control}; source: owner answer plus UXD constraint)*
- **RN-13:** The margin mark is the signature — *because* the product spends its one bold move where
  the operator most needs to look. The mark tells the kind of note by colour and is never the only
  signal. The overdue row also carries the word "Overdue". A refusal or a confirmation is also its
  sentence. Every task row reserves the mark's edge, transparent where there is no mark. Without
  that, an overdue title starts 3 pixels to the right of every other title, and the column stops
  lining up exactly where the eye scans for overdue work (confirmed with an addition:
  `products/tracker17/docs/trail/design/cycle-1.md` § 2.5). *(re: {components.margin-mark-late},
  {components.margin-mark-done}, {components.task-row}, {spacing.mark}; source: owner answer plus
  stated design reason)*
- **RN-14:** Long text wraps and is never shortened — *because* the UXD gives the call to this
  document (`products/tracker17/docs/UXD.md` § Open Questions, "`DESIGN.md` carries it"). Every field
  has a maximum length, and every maximum is still far wider than any column: 200 characters for a
  project name, a task title, an assignee name, the operator's name and a label, and 4,000 for a
  project description and a comment (`products/tracker17/docs/SRS.md` § 3.13 FR-40). FR-40 also says
  "the tracker never shortens a value to make it fit", which grounds this rule upstream as well.
  Version 2 gave as its reason that no maximum was set, citing an SRS section that no longer exists.
  The UXD's open question was re-sourced to FR-40 in the round kept at
  `products/tracker17/docs/trail/uxd/cycle-3.md` § 2.1, and that answer names this note as carrying
  the same outdated reason. This revision carries that upstream change. It closes the one item the
  companion held, opened in commit `b3a00490d` with its reasoning in
  `products/tracker17/docs/trail/uxd/self_answer-3.md`. The rule did not change. A shortened
  value needs a second way to read it whole, such as a tooltip. On this reading that second way is
  more code for the reader, and one more place UX-A1's keyboard rule would have to reach. Wrapping
  inside the cell keeps the owner's rule of one row per task with every attribute in its own column
  (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.2). The owner confirmed wrapping and added three
  rules (confirmed with an addition: `products/tracker17/docs/trail/design/cycle-1.md` § 2.6). Text
  breaks between words first, and inside a word only when the word alone is too wide: with
  `overflow-wrap: anywhere` an unbreakable string "may be broken at any point if there are no
  otherwise-acceptable break points in the line"
  (MDN, https://developer.mozilla.org/en-US/docs/Web/CSS/overflow-wrap). The same page says those
  break points count toward a column's minimum size, so a column could shrink almost to one
  character before the table overflowed, which is why the wrapping columns carry a minimum width
  (RN-24). The rule reaches every operator-typed value on every page, because UX-A7's reflow binds
  those pages. A select is capped at its container, and the browser's own closed control is the one
  place a value may be cut. *(re: § Layout, {components.wrap-cell}; source: owner answer plus stated
  design reason)*
- **RN-15:** The task table scrolls sideways in its own container — *because* UX-A7 requires every page
  to reflow at 400% zoom and exempts the task tables (`products/tracker17/docs/UXD.md` § 8, UX-A7).
  A container is the one way to keep the exemption from spreading to the page around the table.
  *(re: § Layout; source: UXD constraint)*
- **RN-16:** The confirming button is ink, not red — *because* one of the three confirmations, the
  move to `cancelled`, appears inside a task row (`products/tracker17/docs/UXD.md` UX-F4), and a red
  button there would put red into the table the operator scans for overdue rows, where it would read
  as one more overdue mark. That is the stronger reason, added by the owner's answer (confirmed with
  an addition: `products/tracker17/docs/trail/design/cycle-1.md` § 2.7). The reason v1 gave also
  holds: {colors.late} is reserved for what needs correcting (RN-5), and the consequence of the
  action is already stated in words in the confirmation strip (UX-I2, "states the consequence"). Ink
  is the darkest fill on the page, which sets the irreversible press apart from every other button.
  The strip's order and where focus lands in it are UX-I2's, not this document's, and the ink fill
  holds under the arrangement UX-I2 sets: the sentence first, then the confirming button, then the
  back-out control (RN-25). *(re: {components.button-confirm},
  {components.confirm-strip}; source: owner answer plus stated design reason)*
- **RN-17:** Three radii, each with one job — *because* a sheet is a square page of the pad, while
  4 pixels on a control marks it as something to press. 2 pixels on an inline tag keeps it from
  reading as a button. One radius applied everywhere would erase that difference. *(re:
  {rounded.none}, {rounded.sm}, {rounded.xs}; source: stated design reason)*
- **RN-18:** No shadow and no elevation — *because* nothing floats: the UXD puts every confirmation in
  place and "not in a dialog" (`products/tracker17/docs/UXD.md` UX-I2). Tone and line carry every
  level of the page. *(re: § Elevation & Depth; source: UXD constraint)*
- **RN-19:** The form width {spacing.form-max} and the page width {spacing.content-max} — *because* a
  560-pixel form keeps one field per line easy to scan, and a 1180-pixel page fits a 1280-pixel
  window, the width UX-A7 measures from, with {spacing.xl} of paper on each side. *(re:
  {spacing.form-max}, {spacing.content-max}; source: stated design reason)*
- **RN-20:** The current nav link is told by an underline as well as by its ink colour — *because*
  UX-A4's rule against colour alone is written for status, and on this reading the same reason
  holds for where the operator is. The underline costs one rule in the stylesheet. *(re:
  {components.nav-link-current}; source: stated design reason)*
- **RN-21:** A component token on a no-text part such as {components.margin-mark-late} defines no
  text colour — *because* the mark carries no text, and SC 1.4.11 does not bind it. The word or
  sentence beside the mark does. *(re: {components.margin-mark-late}, {components.margin-mark-done};
  source: stated design reason)*
- **RN-22:** The SRS raises no collision — *because* `products/tracker17/docs/SRS.md` NFR-13 limits
  support to "current stable desktop Chrome and other Chromium-based browsers", so the stylesheet
  answers to one engine. NFR-5's rule that pages "load nothing from outside the machine" is the
  same rule this document holds. *(re: § Colors, § Typography; source: SRS read as a sibling)*
- **RN-23:** § Overview's first two fallbacks are inherited, and its own three rank below them —
  *because* every product under this instance holds "Legibility of the working system beats
  ornament" and then "Finished over expressive", in that order
  (`system/experience/visual_direction.md` § Overview). v1's three can disagree with them: where the
  more legible option costs more stylesheet lines, the inherited order picks legibility. So the
  product's three add to the inherited two and decide only between options those two leave tied.
  "The working system" reads here as the operator's task state, because the instance fence's
  `role-visibility` entry is moot for tracker17 (`products/tracker17/docs/UXD.md` RN-20). § Overview
  states the two in this product's own terms, so a reader with only this repo can apply them
  (confirmed with an addition: `products/tracker17/docs/trail/design/cycle-1.md` § 2.1). *(re:
  § Overview; source: instance visual direction plus owner answer)*
- **RN-24:** {spacing.cell-min} is 96 pixels, applied as `6rem` — *because* the owner's answer set a
  minimum readable width of "about twelve characters of {typography.table}", as one token
  (`products/tracker17/docs/trail/design/cycle-1.md` § 2.6). A sans-serif interface face averages
  roughly half its size per character, about 7.5 pixels at 15 pixels, so twelve characters is about
  90 pixels. 96 pixels is the first multiple of the product's 4-pixel unit at or above that which
  is also a whole `rem` (6rem at the default root). It is a width, not a gap, so it sits outside the
  six gap values § Layout names. Applying it in `rem` keeps it about twelve characters when the
  operator raises the font size, under the same rule as the type (RN-10). The format has no
  minimum-width property, so {components.wrap-cell} carries the token as `width`, and § Components
  says it means `min-width`. *(re: {spacing.cell-min}, {components.wrap-cell}; source: owner answer
  plus stated design reason)*
- **RN-25:** The confirmation's sentence stands in the first button's spot, is at least that button's
  height, and shows the focus ring on `:focus` — *because* UX-I2 now has the sentence take "the first
  button's place: it covers the whole spot the first button stood in", with keyboard focus landing on
  it (`products/tracker17/docs/UXD.md` UX-I2, from UXD version 3). The height is the first button's
  height token, so the confirmation does not shrink the spot a second click would land in. Version 2
  said the confirming button takes "the height of the button it replaced". Under UX-I2 as it now
  reads, the sentence replaces the first button, so the confirming button takes the first button's
  height instead. The ring on the sentence uses `:focus` and not `:focus-visible`, because
  `:focus-visible` applies only when "the UA … determines via heuristics that the focus should be made
  evident on the element" (MDN, https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible). The
  sentence takes focus only as the page opens, never from a click on it. Whether the heuristic makes
  that focus evident is not verified here, and a keyboard user must see where focus went once the
  first button is gone. The ring sits on the strip's {colors.surface-sunk}, a ground RN-7 already
  measures at 5.21. *(re: {components.confirm-strip}, § Components focus rule, RN-16; source: UXD
  change plus stated design reason)*
- **RN-26:** Each of the three new sentences beside a field is a field hint, under its field in
  {components.meta-text} — *because* the UXD added them in version 4. The project-description field
  and the comment field each state their most characters (`products/tracker17/docs/UXD.md` UX-F2,
  UX-F7). A task whose assignee has left the list shows a sentence "beside the control, never inside
  the option" (UX-F9). The owner's answer that added the two maximums placed them "in the field-hint
  place `DESIGN.md` § Components already has" (`products/tracker17/docs/trail/uxd/cycle-3.md` § 2.1).
  The UXD needs each sentence in view before the operator submits. Under the field and above the submit
  meets that. Inside an option, a long name in a capped select would cut the note off (§ Layout,
  UXD RN-30). Meta text is {colors.ink-muted}, and the assignee note stays muted rather than red,
  because {colors.late} is kept for what needs correcting (RN-5). The note tells the operator what a
  change would do. It does not mark an error. *(re: § Components field hint; source: UXD change plus
  owner answer)*

## Traceability

| UXD constraint | How this document satisfies it |
|---|---|
| § 9 Direction: plain semantic HTML, the browser's own controls, one hand-written stylesheet, no component library or package | § Overview names the system as built from primitives. § Components styles native elements only. RN-9 keeps the font native too. |
| § 9 Nothing is loaded from outside the machine | `system-ui` with no font file, no icon set and no image. The Do's and Don'ts forbid outside assets (RN-9). |
| § 9 No control is left half-styled | § Components lists every control the stylesheet styles, and styles every instance. `color-scheme` and `accent-color` cover the parts a stylesheet cannot reach (RN-4). |
| § 9 One colour mode and no mode switch, with native controls and pop-ups in that same mode | Light, declared by `color-scheme: light`, with `accent-color` set to {colors.primary} (§ Colors, RN-3, RN-4). |
| § 9 The contrast floor UX-A5 sets, and a focus indicator that meets it (UX-A2) | Every pair computed in RN-7. The focus ring is 2 pixels of {colors.primary} on every control and link (§ Components). |
| § 9 The target-size floor UX-A6 sets | {spacing.control} and {spacing.row-control} heights, a nav link at least {spacing.control} tall, and a 24-pixel box on a standalone table link (§ Components, RN-12). |
| § 9 Status, priority and overdue read without colour (UX-A4) | Status and priority are uncoloured words. Overdue is the word "Overdue", which the red tint and the margin mark reinforce (§ Colors, RN-6, RN-13). |
| § 9 Built for a desktop browser window, with UX-A7's reflow outside the task tables | One-column forms at most {spacing.form-max} wide, a wrapping header and filter row, and the task table in its own scroll container (§ Layout, RN-15, RN-19). |
| § 9 One row per task with each attribute in its own column, long text wrapping inside its cell | § Layout's task table and long-text rules (RN-14). |
| § 2 DENSITY 6 | {spacing.md} cell padding, faint row dividers and {typography.table} at 15 pixels (RN-8, RN-12). |
| § 2 MOTION 1 | No transition, fade or spinner (§ Do's and Don'ts, RN-12). |
| § 2 TYPOGRAPHY 2 | The system interface face and one weight for headings (§ Typography, RN-9). |
| § 2 VARIANCE 2 | A header, a single centred column, sheets, a table and forms (§ Layout). |
| UX-I2 Irreversible actions confirmed in place, not in a dialog, the sentence covering the first button's spot and taking focus | {components.confirm-strip} replaces the first button in place. Its sentence stands in that spot at the first button's height and shows the focus ring on `:focus` (§ Components, RN-16, RN-18, RN-25). |
| UX-F2, UX-F7, UX-F9 A sentence beside a field: a field's maximum length, and an assignee who has left the list | A field hint under its field and above the submit, in {components.meta-text}, never inside an option (§ Components, RN-26). |
| UX-I8 A page appears whole, with no placeholder or spinner | No loading style exists, and the Don'ts forbid one. |
| § Open Questions: how a long title, label, name or comment wraps or shortens in a list row | Wraps, between words first, and is never shortened by the stylesheet. The four wrapping columns keep {spacing.cell-min} as a minimum width, and the rule reaches every operator-typed value on every page. A select is capped at its container, and its closed control is the one place the browser may cut a value. Comments keep their line breaks (§ Layout, § Typography, RN-14, RN-24). |
