# DESIGN open issues — tracker17

> Companion to `DESIGN.md`. The CDO authored the design language non-interactively; this file
> holds the calls it made and wants your sign-off on — each with the reason behind it, and what
> moves underneath it if you override — plus the few things it genuinely could not settle, and,
> when a design run has produced output for this product, the pointer to it.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-design`. It folds your answers into `DESIGN.md` and drops the resolved
> items. When nothing is left open, `product-design` **deletes this file**: no file = the
> design language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/design/` — so what you decided, and why, stays readable and citable
> for good.
>
> **§ 3 is not the CDO asking.** The design language is read by everything built after it, and a
> seat downstream can find a rule missing that the authoring run had no occasion to write. That item
> lands in § 3 and is folded by the same run.

---

## 1. Open issues

None. No input conflicts with another, every input was readable, and every UXD constraint is met
(`products/tracker17/docs/DESIGN.md` § Traceability).

## 2. Choices to confirm

tracker17 has no source code and no brand asset, so every value in `DESIGN.md` is a CDO choice
(`DESIGN.md` RN-1). The seven items below are the calls the other values hang from. Confirming an
item confirms the values its **If overridden** line names.

### 2.1 The design read: a worked example written out on an engineer's computation pad
- **Drafted into DESIGN.md:** § Overview. The page reads as a pale pad with square white sheets on
  it, written in green-black ink, with deep green for actions and one red pencil for what needs
  attention. The feel is quiet, flat and finished. The fallback order for a case no rule covers is
  fewest stylesheet lines, then native behaviour, then red kept for its one meaning.
- **Grounds:** none in evidence: taste call. The pad comes from the product's own purpose, "a worked
  example" (`products/tracker17/docs/PRD.md` § Purpose). The quiet, flat feel follows
  `products/tracker17/docs/UXD.md` § 1 Design Read ("plain, quiet, utilitarian") (RN-2).
- **If overridden:** the palette (2.2), the red-pencil signature (2.5) and the ink confirming button
  (2.7) all take their reason from the pad and are re-chosen with it. Type (2.3), density (2.4) and
  long text (2.6) stand, because each rests on a UXD constraint rather than on the pad.
- **Confirm or override:** confirm, with one addition. § Overview's three fallbacks rank below the two this product inherits from `system/experience/visual_direction.md` § Overview. First, legibility of state beats ornament. Second, finished beats expressive. "Fewest stylesheet lines" then decides only between options those two leave tied, and § Overview says so. Reasoning in `docs/trail/design/self_answer-1.md`.

### 2.2 The palette: one light mode on a pale green-grey page, green-black ink, deep green for actions, and no colour on status or priority
- **Drafted into DESIGN.md:** {colors.paper} `#EDF1EC`, {colors.surface} `#FBFCFA`,
  {colors.surface-sunk} `#DDE4DD`, {colors.ink} `#18211C`, {colors.ink-muted} `#4F5C54`,
  {colors.primary} `#23674A`, {colors.primary-deep} `#1A523A`, {colors.done-tint} `#E1EEE5`.
  `color-scheme: light`, with `accent-color` set to {colors.primary}. Status and priority are
  uncoloured words.
- **Grounds:** the UXD leaves the mode to this document (`UXD.md` § 9, "Which mode is the design
  language's call"). Light is the mode a desktop app is most often recognised in (`PRD.md` § Why
  This, "an app that people recognise as an app"). Every pair clears WCAG AA, computed in RN-7.
  **This item carries the document's one flagged aesthetic risk: the pale green-grey page.** A white
  or neutral grey page is the safe choice, and the green-grey tint is what makes tracker17 look like
  itself rather than like any small web app (RN-3, RN-6).
- **If overridden:** a different page tone moves {colors.paper}, {colors.surface-sunk} and
  {colors.done-tint}, and RN-7's contrast figures are recomputed. A different action colour moves
  {colors.primary}, {colors.primary-deep}, the focus ring and `accent-color`. A dark mode replaces
  every colour token, and `color-scheme` changes with it. Colour on status or priority would add one
  token per value, and those colours would then compete with the red pencil (2.5).
- **Confirm or override:** confirm, with three additions. (1) RN-3's reason for light, "the mode a desktop app is most often recognised in", cites nothing. The reason that holds is the read confirmed in 2.1: a pale page with dark ink is a light mode by construction. (2) `accent-color` reaches the checkbox, radio, range and progress elements only (MDN, *accent-color*). § Colors drops "and the date picker's selected day". `color-scheme: light` alone is what draws the date picker pop-up in light, and that is what `UXD.md` § 9 asks. (3) The focus ring does not sit only "on paper or on a sheet". It also sits on {colors.surface-sunk} inside the confirmation strip, where UX-I2 puts focus, and on {colors.late-tint} around the reload a refusal offers (UX-I3). RN-7 adds {colors.primary} on {colors.surface-sunk} 5.21, on {colors.late-tint} 5.71 and on {colors.done-tint} 5.65, and § Components names those grounds. Every value stays as drafted. Reasoning in `docs/trail/design/self_answer-1.md`.

### 2.3 Type: the system interface face only, 16-pixel body, 15-pixel table text with tabular figures
- **Drafted into DESIGN.md:** every typography level uses `system-ui, sans-serif`, and no font file
  ships. The sizes are {typography.page-title} 24, {typography.section-heading} 18,
  {typography.body} 16, {typography.table} 15 with tabular figures, {typography.control} 15, and
  {typography.label} and {typography.meta} 14. Headings use weight 600, and nothing else is bold.
- **Grounds:** the UXD forbids a hosted font (`UXD.md` § 9, "No hosted font, stylesheet, icon set or
  script"). TYPOGRAPHY 2 asks for type with no personality of its own (`UXD.md` § 2). The sizes are
  set from what each level holds and follow no ratio (RN-9, RN-10, RN-11).
- **If overridden:** a shipped typeface adds a font file to the copy, and every level's
  `fontFamily` changes. The sizes are then re-checked against the new face's x-height, and the
  table's 15 pixels may move to keep a seven-column row inside a desktop window.
- **Confirm or override:** confirm, with one addition. The tokens keep their pixel values, which hold at the browser's default 16-pixel root. The stylesheet applies every type size relative to the root (`rem`, 16 pixels = 1rem) and never in `px`. RN-10's reason, "so a page reads at the operator's own browser setting", holds only then, because a size set in `px` overrides the operator's font-size preference (MDN, *font-size*). § Typography states the rule, and RN-10 says that a larger setting widens the task table, which then scrolls in its own container (RN-15). Reasoning in `docs/trail/design/self_answer-1.md`.

### 2.4 Density and motion: 12-pixel cell padding, 28-pixel move buttons, 36-pixel controls, and nothing animated
- **Drafted into DESIGN.md:** {spacing.md} `12px` cell padding, {spacing.row-control} `28px` move
  buttons, {spacing.control} `36px` for every other control, and faint {colors.surface-sunk} row
  dividers. No transition, fade or spinner exists anywhere.
- **Grounds:** the UXD sets DENSITY 6, "a table, with breathing room", and MOTION 1, "no animation
  or transition beyond what the browser does by itself" (`UXD.md` § 2). A 28-pixel move button
  clears UX-A6's 24-pixel floor (`UXD.md` § 8) (RN-8, RN-12).
- **If overridden:** tighter rows move {spacing.md} and {spacing.row-control}, and 24 pixels is the
  floor neither may go below. Looser rows move the same two tokens up. Motion is not open to
  override here, because MOTION 1 is the UXD's and a change goes back through `product-uxd`.
- **Confirm or override:** confirm, with one addition. The comment textarea is exempt from the 36-pixel height. § Components gives it the text-field contract, and that contract fixes {spacing.control}, which is one line. A comment is multi-line and keeps the line breaks the operator typed. The textarea keeps the contract's colour, edge, radius, padding and type, but not its height. It opens four lines tall from its own `rows` attribute, with no height in the stylesheet, and keeps the browser's own vertical resize. Reasoning in `docs/trail/design/self_answer-1.md`.

### 2.5 The signature: the margin mark, a 3-pixel rule on the left edge, red pencil on overdue rows and refusals, green on confirmations
- **Drafted into DESIGN.md:** {components.margin-mark-late} and {components.margin-mark-done} at
  {spacing.mark} `3px`. {colors.late} `#AE2530` and {colors.late-tint} `#FAE8E7` are used for the
  red mark, the "Overdue" marker and a refusal, and nowhere else.
- **Grounds:** none in evidence: taste call. On the pad, red pencil marks what needs correcting.
  Both an overdue task and a refused action ask the operator to correct something, and "seeing
  which tasks are overdue" must feel effortless (`PRD.md` § UX Notes). The mark is never the only
  signal: the word "Overdue" or the sentence beside it carries the meaning (`UXD.md` UX-A4) (RN-5,
  RN-13).
- **If overridden:** with no margin mark, the "Overdue" marker and the tinted notes carry the
  states alone, and {spacing.mark} and both mark components go. With a different signature, the red
  is re-reserved for whatever replaces the mark. Refusals sharing the overdue red is a separate
  call: say so if a refusal should look different from an overdue row.
- **Confirm or override:** confirm, refusals sharing the overdue red included, with one addition. Every task row reserves the mark's {spacing.mark} edge, and the edge is transparent on a row that carries no mark. Without that, an overdue row's title starts 3 pixels to the right of every other title, and the title column stops lining up exactly where the eye is scanning for overdue work. § Components states it under {components.task-row}. Reasoning in `docs/trail/design/self_answer-1.md`.

### 2.6 Long text wraps inside its cell and is never shortened
- **Drafted into DESIGN.md:** § Layout. A title, a label, an assignee name and a project name wrap
  at any character inside their own cell. Labels wrap onto further lines. No value ends in an
  ellipsis or hides behind a tooltip. A comment keeps the line breaks the operator typed.
- **Grounds:** the UXD gives this call to `DESIGN.md` (`UXD.md` § Open Questions, "`DESIGN.md`
  carries it"). No maximum length is set upstream (`products/tracker17/docs/SRS.md` § Open
  Questions). The owner's UXD answer fixed one row per task with each attribute in its own column
  (`products/tracker17/docs/trail/uxd/cycle-1.md` § 2.2) (RN-14).
- **If overridden:** shortening to one line with an ellipsis needs a way to read the whole value,
  and that way must work from the keyboard (`UXD.md` UX-A1). The likely home is the task page,
  which already shows the task whole. Rows then stay one line high, and § Layout's long-text rule is
  rewritten.
- **Confirm or override:** confirm, with three additions. (1) "Wrap at any character" becomes: break between words first, and break inside a word only when that word alone is wider than its cell (`overflow-wrap: anywhere`, MDN). Because that also lets a column shrink almost to nothing, the title, labels, assignee and project columns keep a minimum readable width of about twelve characters of {typography.table}, set as one token. Below that, the table scrolls in its own container (RN-15) rather than squeezing. (2) The rule reaches every operator-typed value on every page, not only table cells: page titles, descriptions, comments, label tags and names on People. UX-A7's reflow binds those pages, and one unbroken string in a 24-pixel `h1` would otherwise scroll the whole page sideways. (3) A select whose option is a long name or label is capped at its container's width. The closed control shows what the browser draws, and the open list shows the value whole. § Layout names this as the one place the browser's own control may cut a value. Reasoning in `docs/trail/design/self_answer-1.md`.

### 2.7 The confirming press for an irreversible action is an ink button, not a red one
- **Drafted into DESIGN.md:** {components.button-confirm}, {colors.ink} `#18211C` with
  {colors.surface} text, inside {components.confirm-strip}. It confirms deleting a project, deleting
  a task and moving a task to `cancelled`.
- **Grounds:** none in evidence: taste call. Red is kept for what needs correcting (2.5). The
  consequence is already in words in the strip (`UXD.md` UX-I2, "states the consequence"). Ink is
  the darkest fill on the page, and on the pad an inked line cannot be erased. This departs from
  the common red delete button, which is why it is up for your cover (RN-16).
- **If overridden:** a red confirming button reuses {colors.late} as its fill, with
  {colors.surface} text, and § Colors' rule that red appears in exactly three places gains a fourth.
- **Confirm or override:** confirm, with one addition. RN-16 gains the stronger reason. The move to `cancelled` is confirmed inside a task row, so a red confirming button would put red into the table the operator scans for overdue rows. The strip's order, and where focus lands in it, are component anatomy and accessible behaviour. They belong to the UXD and are raised there as `products/tracker17/docs/UXD_open_issues.md` § 2.1. Reasoning in `docs/trail/design/self_answer-1.md`.

## 3. Raised from downstream — an item from a seat that did not write the design language

None.
