# UXD open issues — Trimly

> Companion to `UXD.md`. The CDO authored the UXD non-interactively; this file holds
> what it could not settle from the inputs (the PRD, the project's Agari and its doctrine, the
> SRS when present, and any context the owner handed over). **Answer inline** — fill each **Answer** / **Confirm-or-override**
> slot — **commit this file**, then re-run `product-uxd`. It folds your answers into the UXD
> and drops the resolved items. When nothing is left open, `product-uxd` **deletes this file**:
> no file = the UXD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/uxd/` — so what you decided, and why, stays readable and citable
> for good.

---

## 1. Open issues — experience questions with no answer yet

### 1.1 Does a link ever stop resolving?

- **Why it matters:** UX-S1's link-list row, UX-S2's states, and UX-F2's data needs all differ
  depending on the answer. PRD § 4 F5 says a link "never expires"; PRD § 5 says links with no clicks
  for 12 months "are automatically purged". Only one can hold, and which one is a product-intent
  call the UXD cannot make. The list currently carries an **Inactive — purges soon** badge on the
  strength of § 5.
- **Answer:** Links never expire — F5 is the intent, and a link printed on physical material has to
  resolve forever. Drop the 12-month auto-purge entirely; treat the § 5 line as a PRD error to
  correct. So no expiry, no purge-pending badge, and no inactive state anywhere in the experience:
  an old link with no clicks looks exactly like a new one with no clicks. Permanence is a promise
  the interface should be willing to state, not just honour silently.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 The MOTION dial

- **Drafted into the UXD:** MOTION = 4 — enough movement that live-arriving clicks register, short
  of a dashboard that feels animated.
- **Rationale:** the PRD sets no motion intent anywhere, so this is not derived from a PRD fact. F2's
  "analytics update as clicks arrive" argues for *some* movement; 4 is the CDO's read of how much.
- **If overridden:** the dial value moves, and UX-I3's live-update treatment moves with it — a lower
  value makes an updating figure change quietly in place, a higher one lets it animate.
- **Confirm or override:** override: 2. Marketing people read these numbers between other work and
  the tab sits open all day — a figure that moves on its own is a distraction, not a delight. Update
  in place, quietly, and mark what changed without animating it.

### 2.2 The design-system direction

- **Drafted into the UXD:** built from primitives — an unstyled accessible primitive layer with a
  thin in-house layer over it, rather than an official design-system package.
- **Rationale:** the product is five screens of tables and forms and the PRD names no house style,
  so a full system looked like more than it needs. This is taste, not a PRD-derived fact.
- **If overridden:** § 9's direction changes and its constraints re-hang on whatever is named; the
  constraints themselves (AA-clearing accent, tabular numerals, a focus treatment that survives on
  rows and chart controls) hold either way, and `DESIGN.md` is authored off the new direction.
- **Confirm or override:** override: use **Radix Themes** as the official package. A thin in-house
  layer is a design system we'd end up maintaining without meaning to, and a small team shipping
  five screens should not be paying that. Name the package, use its components as they come, and let
  `DESIGN.md` carry only what we set on top of it.
