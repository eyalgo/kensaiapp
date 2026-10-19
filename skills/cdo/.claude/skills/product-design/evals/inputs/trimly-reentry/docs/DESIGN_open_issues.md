# DESIGN open issues — trimly

> Companion to `DESIGN.md`. The CDO authored the design language non-interactively; this file
> holds what it could not ground in the evidence. **Answer inline** — fill each **Answer** /
> **Confirm-or-override** slot — **commit this file**, then re-run `product-design`. When
> nothing is left open, `product-design` **deletes this file**: no file = the design language
> is done.

---

## 1. Open issues — values with no evidence and no default worth guessing

### 1.1 The heading type scale
- **Why it matters:** every screen title and section heading needs a level; DESIGN.md's `typography` map carries only the two body sizes.
- **What was searched:** src/styles/tokens.css — the only type tokens are --text-body (14px) and --text-small (12px); no heading size is defined anywhere in the source, and the UXD sets no type values (correctly — values live here).
- **Answer:** Use Inter throughout. Two levels above body: headline at 24px/32 semibold (600) for screen titles, title at 18px/24 semibold (600) for section headings. Keep body at 14. No display size — this is a dense tool, not a marketing page.

## 2. Choices to confirm — the CDO drafted a best-effort value; confirm or override

### 2.1 The interaction colour stays the shipped blue
- **Drafted into DESIGN.md:** {colors.primary} = #2563EB, with {colors.primary-hover} = #1D4ED8.
- **Grounds:** src/styles/tokens.css --color-brand / --color-brand-hover — the live shipped values.
- **Confirm or override:** override: move primary to #0F766E (hover #115E59). The brand refresh landing this quarter is teal — it's already in the new logo. Keep everything else as drafted.
