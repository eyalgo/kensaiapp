# PRD open issues — trimly

> Companion to `PRD.md`. The CPO authored the PRD non-interactively; this file holds what it
> could not settle from the inputs. Answer inline, commit, then re-run `product-prd` — it folds
> the answers into the PRD and drops the resolved items. When nothing is left, it clears this
> file: no file = the PRD is done.

---

## 1. Open issues — product-defining questions with no answer yet

### 1.1 What launch scale should the product be built for?
- **Why it matters:** it bounds the whole capacity story — how many workspaces, links, and redirects.
- **Reasoning / what would settle it:** the brief gives a rough "figure ~50 / a couple thousand / a
  couple hundred thousand"; only the owner can commit the figure.
- **Answer:** 50 workspaces at launch, up to 2,000 active links each, ~200,000 redirects/day.

### 1.2 What do we keep of a visitor's IP, and for how long?
- **Why it matters:** the analytics geography feature and the privacy story both depend on it.
- **Reasoning / what would settle it:** the brief says "shouldn't hang onto raw IPs for long" — the
  owner's call on the exact window.
- **Answer:** Retain a raw IP no longer than 30 days, then discard; keep only the coarse geography
  derived from it for the life of the link.

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

### 2.1 One shared branded domain for all links (no per-workspace custom domains) in v1?
- **Drafted into the PRD:** all links live on a single shared branded domain; per-workspace custom
  domains are out of scope for v1.
- **Rationale:** keeps v1 focused; custom domains add DNS/cert operational load with no launch-scale need.
- **Confirm or override:** confirm.

## 3. Directives — an external action the owner confirms as a gate

<!-- none this round -->
