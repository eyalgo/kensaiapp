# Self-answer report — DESIGN.md

## Header

- **Companion:** products/tracker17/docs/DESIGN_open_issues.md
- **Document:** products/tracker17/docs/DESIGN.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:**
  - MDN, *accent-color*, https://developer.mozilla.org/en-US/docs/Web/CSS/accent-color. It lists the
    elements the property applies to as `<input type="checkbox">`, `<input type="radio">`,
    `<input type="range">` and `<progress>`. A date input and the date picker are not on that list
    (item 2.2).
  - MDN, *color-scheme*, https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme. The user
    agent changes "the default colors of scrollbars and other interaction UI", "the default colors of
    form controls" and "the default colors of other browser-provided UI" to match the scheme used
    (item 2.2).
  - W3C, *Understanding SC 1.4.11 Non-text Contrast*,
    https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html. "Most focus indicators appear
    outside the component - in that case it needs to contrast with the background that the component
    is on." The page says nothing about lines that divide table rows (items 2.2, 2.4).
  - MDN, *font-size*, https://developer.mozilla.org/en-US/docs/Web/CSS/font-size. "Defining font sizes
    in `px` is not accessible, because the user cannot change the font size in some browsers", and
    "it is generally best to use values that are relative to the user's default font size" (item 2.3).
  - MDN, *overflow-wrap*, https://developer.mozilla.org/en-US/docs/Web/CSS/overflow-wrap. With
    `anywhere`, "an otherwise unbreakable string of characters — like a long word or URL — may be
    broken at any point if there are no otherwise-acceptable break points in the line", and "soft wrap
    opportunities introduced by the word break are considered when calculating min-content intrinsic
    sizes". With `break-word` they are not considered (item 2.6).
  - The contrast figures were recomputed rather than re-read. The WCAG 2.x relative-luminance formula
    was run over every token pair on 2026-10-06. All of RN-7's figures matched, and the run added four
    pairs: {colors.primary} on {colors.surface-sunk} 5.21, on {colors.late-tint} 5.71 and on
    {colors.done-tint} 5.65, and {colors.ink-muted} on {colors.late-tint} 5.94 (item 2.2).

## Items worked

### 2.1 — The design read: a worked example written out on an engineer's computation pad

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The read stands. It passes the test the UXD sets for every visual decision: "does it add a
  part the reader has to read?" (`UXD.md` § 1 Design Read). What the pad produces is colour values,
  square sheets and one 3-pixel mark. It brings no texture, grid paper, image or font, so it adds no
  part. It also gives the palette, the signature and the radii one source, which makes them easier to
  judge together.
  Check 2: the grounds are honest about being taste. One caution for later readers: the pad reads the
  word "worked example" (`PRD.md` § Purpose) more literally than the PRD means it. There it means an
  example product, not a worked calculation. So the pad is a taste choice that fits the product, not
  something derived from it. RN-2's "cannot be reused for an unrelated product" holds as a statement
  about the choice, and claims nothing more.
  Check 1: the aesthetic call is the design run's (`<CORE>/doctrine/governance/where_taste_appears.md`
  § The rule), and this run sits in the owner's seat. I looked for an owner ruling that keeps the
  visual calls back. The only visual step the owner holds is the later Claude Design run, and it reads
  these documents rather than deciding them. Nothing reserves `DESIGN.md`'s calls, so I answered. The
  same seat finding holds for 2.2 to 2.7.
  Check 3 found a conflict, and it is the addition. `system/experience/visual_direction.md` § Overview
  gives every product under this instance two fallbacks, "in order": "Legibility of the working
  system beats ornament", then "Finished over expressive". `DESIGN.md` § Overview gives its own three,
  starting with "fewest lines to the stylesheet", and does not mention the inherited two. They can
  disagree. Suppose a case where the more legible option costs more lines. The inherited order picks
  legibility, and the product's list as written picks fewer lines. The product's list adds to the
  inherited two and cannot replace them, so it ranks below them. Here "legibility of the working
  system" means legibility of the operator's task state, because `role-visibility` is moot for
  tracker17 (`UXD.md` RN-20).
  Check 4: no failure path reaches a design read. The fallback order is what does the work on cases
  nobody foresaw, and the addition is what makes it safe there.
  What would have tipped me to override: a read that brought an asset or a part with it, such as a
  paper texture, ruled lines or a hand-drawn face. This one brings none.

### 2.2 — The palette: one light mode on a pale green-grey page, green-black ink, deep green for actions, and no colour on status or priority

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The palette stands, the flagged green-grey page included. Every value is unchanged, and the
  three additions correct the text around them.
  The page tint is mild. {colors.paper} `#EDF1EC` differs from {colors.surface} by 1.11:1 in
  luminance (the sheet stands on it by tone alone, which § Elevation & Depth wants). Text on it still
  clears AA by a wide margin: ink 14.45, ink-muted 6.15, primary 5.91. Each was recomputed this run,
  and every RN-7 figure matched. So the risk the draft takes is a matter of taste only, with no
  legibility cost. It is also the one thing that makes the product look like itself, which is the
  read 2.1 confirmed. Status and priority stay uncoloured. UX-A4 is then met by construction, and red
  keeps its single meaning (2.5).
  Check 2, the argument. RN-3 says light is "the mode a desktop app is most often recognised in". No
  source is given, and I did not take it as a ground. The conclusion is right for a reason that holds:
  2.1's read is a pale sheet in dark ink, which is a light mode by definition. `UXD.md` § 9 asks for
  one mode, and this is it. That is addition (1).
  Check 3, the source. § Colors says `accent-color` makes "the checkbox and the date picker's selected
  day take the product's action colour". MDN lists the property's elements as checkbox, radio, range
  and progress, and the date picker is not among them. The record says more than the source supports,
  so the claim goes (addition 2). Nothing moves underneath it. The date picker's pop-up is kept in
  light by `color-scheme`, which MDN says sets "the default colors of form controls" and of "other
  browser-provided UI". That is the property `UXD.md` § 9 and its answered round
  (`trail/uxd/cycle-1.md` § 2.1) actually need.
  Check 4, the grounds a focused control sits on. § Components says the ring "sits on paper or on a
  sheet". The W3C measures a ring drawn outside a control against "the background that the component
  is on". Two grounds the text misses get focus in normal use. The confirmation strip is
  {colors.surface-sunk}, and UX-I2 moves focus into it. The reload control a stale-page refusal
  offers (UX-I3) sits on {colors.late-tint}. Both clear 3:1: 5.21 and 5.71, and 5.65 on
  {colors.done-tint} should a confirmation ever carry a link. So no value moves, but RN-7's list and
  § Components' sentence have to name these grounds (addition 3). Otherwise a later reader takes
  "paper or sheet" as the whole set.
  Check 4, refused: with the operating system's forced-colours mode on, the tints and the margin mark
  are replaced by system colours and may vanish. The meaning survives, because every state is also a
  word (UX-A4). I name this rather than design for it, because nothing upstream asks for a
  forced-colours treatment.
  What would have tipped me to override: a tint that pushed any text pair under 4.5:1. None does. I
  also checked whether {colors.done-tint} reads as its own ground. It is 1.05:1 against
  {colors.paper}, which would be too close, but a confirmation sits on a sheet (§ Components,
  {components.note-done}), where it is 1.16:1 against {colors.surface} and carries the green mark.
  The tint is a reinforcement, and the sentence and the mark carry the note.

### 2.3 — Type: the system interface face only, 16-pixel body, 15-pixel table text with tabular figures

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The face and the sizes stand. `system-ui, sans-serif` is the only choice that meets both
  of the UXD's rules: no hosted font (`UXD.md` § 9) and type with no personality of its own
  (TYPOGRAPHY 2, `UXD.md` § 2). Shipping a font file would satisfy the first and add an asset the
  reader has to account for (`PRD.md` § Risks). Tabular figures on the table level serve the column
  comparison Key Use Case 4 asks for (RN-11).
  Check 2: the argument does not hold for the reason it gives, and the addition repairs it. RN-10 says
  the 16-pixel body is "Chromium's default, so a page reads at the operator's own browser setting".
  That is true only if the size is stated relative to that setting. MDN: "Defining font sizes in `px`
  is not accessible, because the user cannot change the font size in some browsers", and "it is
  generally best to use values that are relative to the user's default font size". If the stylesheet
  writes `16px`, an operator who has raised the browser's default gets 16 pixels anyway. So the pixel
  values stay as the tokens, which the format states in pixels and which hold at the default root.
  The stylesheet applies them as `rem`, which costs no extra line.
  Check 4, the larger setting. At a raised default, the seven-column task table is wider than a
  desktop window. That is already handled: the table scrolls sideways in its own container, and the
  page around it does not (§ Layout; RN-15). Forms are capped at {spacing.form-max} and reflow (RN-19).
  So the addition introduces no new failure.
  Check 4, absent: `system-ui` resolves to whatever the operating system's interface face is. A face
  without the `tnum` feature ignores the setting, and its digits stay as the face draws them. That
  degrades alignment and breaks nothing, so I name it and leave it.
  What would have tipped me to override: an upstream rule asking for a characterful face, or a
  readability failure at 14 pixels. Neither exists. UX-A5's bar sets no minimum size, and 14 pixels
  is used only for labels and meta.

### 2.4 — Density and motion: 12-pixel cell padding, 28-pixel move buttons, 36-pixel controls, and nothing animated

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The values stand. With 12 pixels of cell padding and 28-pixel move buttons, a row is at
  least 52 pixels tall. That reads as "a table, with breathing room", which DENSITY 6 asks for
  (`UXD.md` § 2). A 28-pixel move button with 8 pixels between neighbours clears the 24-pixel floor
  of UX-A6 (`UXD.md` § 8), and the margin matters most here, where a slip onto `done` cannot be
  undone. Thirty-six pixels for every other control is a comfortable desktop height. Motion is the
  UXD's MOTION 1, and the draft correctly says it cannot be overridden here.
  Check 2, the faint row divider (RN-8, {colors.surface-sunk} at 1.26:1 on {colors.surface}). The
  W3C's SC 1.4.11 page says nothing about lines that divide table rows. RN-8's view that a divider is
  decoration is therefore an interpretation and not a quotation. I accept it, because the table's
  structure is carried by its markup and its columns, and no row is identified by its line.
  Check 4 found the gap, and it is the addition. "36 pixels for every other control" reaches a control
  it does not fit. § Components says "the comment textarea ... take[s] the text-field contract", and
  {components.text-field} fixes `height: {spacing.control}`. That makes the comment field 36 pixels
  tall: one line of 15-pixel type with its padding. Yet a comment "keeps the line breaks the operator
  typed" (§ Typography), so it is multi-line by design. A one-line box for multi-line text would be a
  control that looks unfinished, which `system/experience/visual_restrictions.md` § 2
  `no-placeholder-delivery` forbids. The textarea therefore keeps everything in the contract except
  the height. Its height comes from its own `rows` attribute, which takes no stylesheet line and
  leaves the browser's native resize handle in place. That follows § Overview's fallbacks 1 and 2.
  Four rows is a short comment shown whole without scrolling. It is a small call, and the fold may
  pick another count.
  What would have tipped me to override: a desktop window too narrow for the seven columns at
  12-pixel padding. RN-15's scroll container covers that case, so the padding does not have to shrink
  to fit.

### 2.5 — The signature: the margin mark, a 3-pixel rule on the left edge, red pencil on overdue rows and refusals, green on confirmations

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The mark stands, and so does the separate call the item asks about: a refusal keeps the
  overdue red. Spending the product's one bold move on the overdue row puts it where `PRD.md` § UX
  Notes asks for effort to disappear: "seeing which tasks are overdue". One reserved red down a table
  is found at a glance. The mark is never the only signal: the overdue row carries the word "Overdue"
  (UX-A4), and a refusal is its sentence (UX-A3), so the mark only reinforces.
  On the refusal question: an overdue task and a refused action both ask the operator to look and do
  something. Giving refusals their own colour would add a second attention colour, with its tint, its
  contrast pair and its own rule in § Colors. That breaks fallback 3 (red kept to one meaning) and
  costs lines (fallback 1), and nothing upstream asks for the difference. The two never stand where
  they could be mistaken for each other. One marks a table row and comes with a date and a word. The
  other sits beside the control that was used and carries a sentence.
  Check 4, concurrent: an overdue row whose move is refused because the page is stale (UX-I3) carries
  two red marks, the row's and the refusal's. Both mean "this needs you", and each has its words, so
  the doubled signal is accurate rather than confusing. I name it and leave it.
  Check 4, the empty case, which gives the addition. Most rows carry no mark. If the mark is a 3-pixel
  edge drawn only on overdue rows, every overdue title starts 3 pixels to the right of the titles
  around it. That is a jagged column in the one table the operator scans for overdue work, and it is
  the kind of half-finished visual state `no-placeholder-delivery` forbids. Reserving the edge on
  every row, transparent where there is no mark, keeps the column straight for one stylesheet
  declaration.
  Check 4, refused: in forced-colours mode the mark's colour may be replaced. The word "Overdue" and the
  refusal's sentence still carry the state, as UX-A4 and UX-A3 require. Item 2.2 names the same case.
  What would have tipped me to override: a refusal and an overdue row that could share a place on
  screen and be confused. On this layout they cannot.

### 2.6 — Long text wraps inside its cell and is never shortened

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** Wrapping stands over shortening. The UXD fixed one row per task, with each attribute in
  its own column, and long text wrapping inside its cell (`UXD.md` § 9; `trail/uxd/cycle-1.md` § 2.2).
  That leaves this document only how the wrap works. Shortening would need a second way to read the
  whole value, and the second way has to work from the keyboard (UX-A1). That is more code for the
  reader, for a product with no length limit upstream (`SRS.md` § Open Questions). The draft's
  argument holds. Its rule is underspecified on three failure paths, and the additions close them.
  (1) How a cell breaks. "Wrap at any character when they meet the cell's edge" reads like breaking
  every word wherever the edge falls, which splits ordinary titles mid-word. MDN gives the intended
  behaviour as `overflow-wrap: anywhere`: an unbreakable string "may be broken at any point if there
  are no otherwise-acceptable break points in the line". In other words, words first, and inside a
  word only when there is no other choice. MDN also states the cost: those break points "are
  considered when calculating min-content intrinsic sizes". A browser laying out the table may then
  narrow the title column almost to one character before the table ever overflows, so RN-15's
  sideways scroll would never start and titles would stack one letter per line at 400% zoom. The
  alternative, `break-word`, does not shrink the column, but then one 300-character unbroken title
  widens the whole table, and every row's moves scroll off to the right. Neither alone is right. A
  minimum readable width on the four columns that wrap, below which the table scrolls in its
  container, gives both halves. About twelve characters of 15-pixel type is enough to read a word
  whole. The value is a token, and the fold may choose it.
  (2) Where the rule reaches. § Layout scopes it to "a title, a label, an assignee name and a project
  name ... inside their own cell". But the same values appear outside tables: a task's title as the
  task page's `h1` in 24-pixel type, a project's name and description, comments, label tags on the
  task page, names on People, and the confirmation that names a task (UX-I4). Those pages are not
  exempt from UX-A7, so one unbroken string there scrolls the whole page sideways at 400% zoom. The
  same break rule applies to all of them. Comments also keep their typed line breaks (§ Typography).
  (3) Native selects. The assignee filter, the label filter and the add-task and edit forms offer
  names and labels in a `<select>` (`UXD.md` UX-F3, UX-F5). A select is as wide as its longest option,
  so one long label can push the filter row past the window. Capping the select at its container
  keeps the row reflowing. The closed control then shows as much as the browser draws, and the open
  list shows every value whole. That is the browser's own control, so fallback 2 (native behaviour)
  takes it. "Nothing is shortened" stays true everywhere the stylesheet draws text, and § Layout should
  name this one exception rather than leave the sentence literally false.
  What would have tipped me to override toward shortening: a length limit set upstream that kept
  values short. The SDD may still set a technical bound (`SRS.md` § Open Questions). If it does, the
  minimum width and the select cap still hold, and nothing here moves.

### 2.7 — The confirming press for an irreversible action is an ink button, not a red one

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** Ink stands. The draft's reason holds: red is kept for what needs correcting (2.5), and
  the consequence is already in words in the strip (UX-I2, "Delete Alpha and its 12 tasks?"). I add a
  reason the draft did not give, and it is the stronger one, so it is the addition: RN-16 gains it. One of the three confirmations, the move
  to `cancelled`, appears inside a task row (`UXD.md` UX-F4; § Components, {components.confirm-strip}
  "in a task row"). A red button there would put red into the table the operator scans for overdue
  rows, and it would read as one more overdue mark. Ink is set apart without that cost. It is the
  darkest fill on the page, 16.03:1 for its text, and visibly not the green of an ordinary action.
  Departing from the common red delete button costs some recognition (`PRD.md` § Why This, "an app
  that people recognise as an app"). The sentence in the strip pays that cost, because it says what
  the press does before the press is offered.
  Check 4, concurrent: a double press. `DESIGN.md` says the strip "replaces the first button in
  place". If the confirming button lands where the first button stood, a double click confirms a
  deletion of a project and every task in it, with no undo (UX-I2). The same is true if keyboard focus
  lands on the confirming button, because UX-I6 makes Enter or Space press it. UX-I2 says the
  confirmation "appears where the first press was made" and that focus "lands on" it, and settles
  neither point. I first drafted the order of the strip as an addition here. I moved it out, because
  the CDO contract puts both component anatomy and accessible behaviour in the UXD, not in
  `DESIGN.md` (`<CORE>/roles/loaders/cdo_global.md` § Output, "it belongs in the UXD"). The UXD is
  settled and had no companion, so I opened one and raised both halves there as one item
  (§ Companions opened). This item's answer stands without it: the ink fill is right whichever
  arrangement the UXD settles.
  What would have tipped me to override toward red: no consequence sentence in the strip, which would
  leave colour as the only warning. UX-I2 requires the sentence, so that is not the case.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/UXD_open_issues.md** — **opened** — companion to `UXD.md`, landed in commits `f43d08360` and `d78e48ce7`

  Found while answering item 2.7, and not routed by any item's slot. UX-I2 says an irreversible
  action's confirmation "appears where the first press was made" and that keyboard focus "lands on"
  it, but not which part does either. If the confirming control takes the first button's place, a
  double click deletes. If it takes focus, the next Enter or Space deletes (UX-I6). Either way a
  project and its tasks go, with no undo (UX-I2). The opened item asks UX-I2 to say that the
  consequence sentence takes the first button's place and takes focus. The ground is the prompt's
  "Where you are unsure, the answer is to raise it". The UXD's sentence is not false. It allows an
  arrangement that loses data with no undo, and the SDD has not been written yet, so this is the
  cheapest point to settle it. `UXD.md` itself was not edited. The item sits in § 2 with its slot
  left open for the next round.

  The item went through two commits in this run. The first (`f43d08360`) carried the focus half
  only, under the heading "When an irreversible action's confirmation appears, focus lands on its
  sentence, never on the confirming control". The second (`d78e48ce7`) added the pointer half, the
  strip's order, which I had first written into the 2.7 slot here, and widened the heading to match.
  No other run read the file between the two commits.

## Launchers owed

- **products/tracker17/docs/DESIGN.md** — `<CORE>/launchers/skill/launcher.sh product-design tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
