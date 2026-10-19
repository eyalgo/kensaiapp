# UXD — Trimly

**Status:** Draft
**Owner:** CDO
**Version:** 1 — first authoring off the settled PRD; the link-lifetime question and two taste calls are open.

> The UXD is the experience source of truth: the experience-level **what**, derived from the
> settled PRD, authored concurrent with the SRS, and consumed cold by the SDD write pass and by
> UI-touching change specs.

---

## 1. Design Read

Reading this as: a **campaign-operations tool for small marketing teams**, with a **plain, dense,
get-out-of-the-way** language, leaning toward a **utility-dashboard** aesthetic. *(Basis: PRD §2 —
3–15 marketing people per workspace, at a desk, working against a campaign deadline; PRD §4 F2 — the
product's centre of gravity is a table of numbers, not a canvas.)*

## 2. Design Dials

| Dial | Value (1–10) | Reasoning (from the PRD) |
|---|---|---|
| VARIANCE (layout experimentation: symmetric ↔ asymmetric) | 2 | PRD §4 F1/F2 — the product is a list and a detail view. Symmetric, predictable layout is what a table of campaign links wants. |
| MOTION (animation depth: static ↔ cinematic) | 4 | The PRD sets no motion intent. Drafted mid-low so that live-arriving clicks (F2, "analytics update as clicks arrive") register as movement without the dashboard feeling animated. **Choice to confirm 2.1.** |
| DENSITY (information per viewport: airy ↔ packed) | 8 | PRD §3 G3 — up to 2,000 active links per workspace, and PRD § UX Notes puts comparison across links ahead of the single-link view. Comparison at that count needs rows, not cards. |

## 3. Users & Contexts

- **UX-U1** — Workspace **member**, at a desk on a wide screen, mid-campaign: creates links in bursts
  and checks numbers between other work. Expects to keep a browser tab open all day. *(→ PRD § 2
  Target users)*
- **UX-U2** — Workspace **admin**: everything a member does, plus members, roles, and the
  subscription. Visits the admin surfaces rarely — days or weeks apart — so those surfaces must be
  self-explanatory on return. *(→ PRD § 2 Target users)*
- **UX-U3** — The **end visitor**, who never sees a Trimly screen: they experience the product only
  as a redirect that resolves. Their whole experience is latency and correctness. *(→ PRD § 3 G4)*

## 4. Information Architecture

Three top-level areas inside a workspace, with the workspace switcher above them:

- **Links** — the default landing area; the list of the workspace's links and, one level down, a
  link's detail and analytics.
- **Members** — the roster, invitations, and role assignment. Admin-only.
- **Billing** — plan, seats, payment method, invoices. Admin-only.

Navigation is flat: one persistent left rail for the three areas, and a single detail level under
Links. A member sees Links only; an admin sees all three, and the two admin areas are adjacent
because they are visited in the same sitting. *(→ PRD § 4 F1, F3, F4)*

## 5. Key Flows

### 5.1 UX-F1 — Create a short link *(→ PRD § 4 F1; § UX Notes)*

- Steps: paste the long URL into the create field on the Links screen → the slug field shows the
  generated slug, editable → confirm → the new link appears at the top of the list with its short URL
  already selected for copying.
- Data the UI needs at each step: nothing at paste; on slug edit, a **live uniqueness check against
  the branded domain**; on confirm, the created link record (slug, destination, created-at, creator).
- Failure/recovery: a taken slug is reported **while typing**, not on submit (PRD § UX Notes — being
  told after submitting is too late); the typed destination survives any failure and the field is
  never cleared on error.

### 5.2 UX-F2 — Read the numbers and act *(→ PRD § 4 F2; § 3 G2; § UX Notes)*

- Steps: land on the Links list, which carries per-link click totals → sort or scan to find the
  outlier → open that link's detail for unique visitors, geography, referrers, and the time series.
- Data the UI needs at each step: the list needs a **click total per link, aggregated**, and
  pagination at 2,000 links; the detail needs the time series over a selectable window, the
  referrer and geography breakdowns, and the unique-visitor count.
- Failure/recovery: the geography breakdown comes from a third-party lookup — when it is
  unavailable, that panel alone reports it and the rest of the detail view still renders.

### 5.3 UX-F3 — Invite a teammate and set their role *(→ PRD § 4 F3)*

- Steps: admin opens Members → invites by email → picks admin or member → the invitee appears as
  pending until they accept.
- Data the UI needs at each step: the roster with each member's role and invitation state; the seat
  count against the subscription, since an invitation may cross a seat boundary.
- Failure/recovery: an invitation that would exceed paid seats is stopped **before** it is sent, and
  says what it would cost.

## 6. Screen Inventory & States

| ID | Screen | Empty | Loading | Error | Success |
|---|---|---|---|---|---|
| UX-S1 | Links list | No links yet — the create field, and one line on what a short link is for | Row skeletons; the create field is live immediately | The list failed to load — retry, with the create field still usable | The list, sortable by clicks, with the newest link first. Links with no clicks for 12 months carry an **Inactive — purges soon** badge. **Open issue 1.1.** |
| UX-S2 | Link detail & analytics | Created but no clicks yet — "nothing yet", explicitly not an error state (PRD § UX Notes) | The metric tiles and chart load independently, so a slow series doesn't block the totals | Per-panel: a failed geo lookup reports inside its own panel and leaves the rest readable | Totals, unique visitors, geography, referrers, and the time series over the selected window |
| UX-S3 | Create link (inline on UX-S1) | The default state — an empty field with the paste affordance | Slug-uniqueness check in flight, shown on the slug field itself | Slug taken, or the destination is not a URL — both reported at the field, both preserving what was typed | The link is created and its short URL is selected, ready to copy |
| UX-S4 | Members | Just the admin, with the invite affordance | Roster skeleton | The roster failed to load, or an invitation failed to send — the typed address survives | The roster with roles, pending invitations distinguishable from accepted members |
| UX-S5 | Billing | n/a — a workspace always has a plan, so this screen has no empty state | The subscription state is fetched from Stripe | Stripe unreachable — say the plan cannot be shown right now rather than implying it lapsed | Plan, seats used against seats paid, payment method, and invoice history |

## 7. Interaction Patterns

- **UX-I1** — **Destructive actions are confirmed, not undone.** Deleting a link or changing a live
  slug breaks a redirect that may be printed on physical material, so each takes an explicit
  confirmation naming the slug. Undo is not offered, because the damage happens at the first
  unresolved redirect and cannot be taken back by restoring the record later. *(→ PRD § UX Notes)*
- **UX-I2** — **Validation is reported at the field while typing**, never as a summary after submit.
  *(→ PRD § UX Notes — slug collisions)*
- **UX-I3** — **Live data arrives without a reload.** Click totals update in place while the screen
  is open; an updating figure is marked as it changes so a reader is not misled by a number that
  moved while they looked at it. *(→ PRD § 4 F2)*
- **UX-I4** — **A degraded dependency degrades one panel, never the screen.** *(→ PRD § 8 External
  dependencies)*

## 8. Accessibility Requirements

- **UX-A1** — WCAG 2.1 AA contrast on all text and on the chart's non-text indicators.
- **UX-A2** — Every flow in §5 completable by keyboard alone, with a visible focus indicator that
  meets the same AA contrast bar.
- **UX-A3** — Live-updating figures (UX-I3) announce politely to assistive technology, and never
  move focus.
- **UX-A4** — The analytics never carry meaning in colour alone; geography and referrer breakdowns
  are readable as values, not only as a chart.

## 9. Design-System Direction

- Direction: **built from primitives** — an unstyled accessible primitive layer with a thin in-house
  layer over it, rather than an official design-system package. Reasoning: the product is five
  screens of tables and forms, and the PRD names no house style to honour. **Choice to confirm 2.2.**
- Constraints the design language must satisfy: an AA-clearing accent that stays legible on the
  chart surfaces; a tabular numeral treatment, since the whole product is columns of figures; a
  focus treatment that survives on both the list rows and the chart controls.
- Design language: `trimly/docs/DESIGN.md` (authored by `product-design` off this direction; may
  trail the SDD).

## 10. Out of Scope

This UXD is scoped against Trimly's declared terminus — the launch cohort live: 50 workspaces on
real campaign links, analytics they act on, and subscriptions that renew. What it deliberately does
not design:

- **Any experience for the v1-excluded features** — the public/developer API, a native mobile app,
  per-workspace custom domains, and A/B link splitting. *(PRD § 6 Out (v1); the terminus places them
  outside done.)*
- **The end visitor's experience beyond the redirect itself.** UX-U3 sees no Trimly surface; there is
  no branded interstitial and none is designed.
- **The design language's token values** — those are `DESIGN.md`'s, off §9's direction.

## 11. Traceability

| UXD entry | PRD source |
|---|---|
| UX-U1, UX-U2 | § 2 Target users |
| UX-U3 | § 3 G4 |
| UX-F1 | § 4 F1; § UX Notes |
| UX-F2 | § 4 F2; § 3 G2; § UX Notes |
| UX-F3 | § 4 F3 |
| UX-S1, UX-S3 | § 4 F1; § UX Notes |
| UX-S2 | § 4 F2; § UX Notes |
| UX-S4 | § 4 F3 |
| UX-S5 | § 4 F4 |
| UX-I1 | § UX Notes |
| UX-I2 | § UX Notes |
| UX-I3 | § 4 F2 |
| UX-I4 | § 8 External dependencies |
| UX-A1–UX-A4 | § 2 Target users (assistive-tech expectations); § 4 F2 |

---

## UXD Review Notes

- **RN-1:** *(added)* The accessibility bar is stated at WCAG 2.1 AA rather than left unstated —
  *because* the PRD names no bar and a document that states none hands the decision to whoever
  implements it. AA is the floor a named standard sets, not a bar above it. *(re: UX-A1–UX-A4; PRD
  source: § 2 Target users)*
- **RN-2:** *(added)* Undo is not offered on destructive actions; confirmation is — *because* the
  damage from a broken redirect happens at the visitor's first failed resolve and restoring the
  record afterwards does not undo it. *(re: UX-I1; PRD source: § UX Notes — printed material)*
- **RN-3:** *(added)* Pagination is stated as a requirement of the list's data needs — *because* PRD
  § 3 G3's 2,000 active links per workspace makes an unpaginated list unusable, and the SDD's data
  model has to carry it. *(re: UX-F2; PRD source: § 3 G3)*

---

## Open Questions

- [OPEN: does a Trimly link ever stop resolving? PRD § 4 F5 says a link never expires; PRD § 5 says
  links with no clicks for 12 months are automatically purged. The link list's badge and the
  detail view's states differ depending on which holds. Routed as open issue 1.1.]
