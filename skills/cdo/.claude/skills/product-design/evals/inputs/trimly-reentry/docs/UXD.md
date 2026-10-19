# UXD — Trimly

**Status:** Settled
**Owner:** CDO
**Version:** 2 — folded the cycle-1 answers: motion lowered to 2, the direction confirmed as built-from-primitives, link permanence stated everywhere; nothing left unresolved and the companion cleared.

> The UXD is the experience source of truth: the experience-level what, derived from the PRD. The
> design language (`DESIGN.md`) is authored off § Design-System Direction below — that section
> names the system and the constraints; every token value lives there, none here.

---

## 1. Design Read

Reading this as: a campaign-operations tool for small marketing teams, with a plain, dense
language, leaning toward a utility-dashboard aesthetic.

## 2. Design Dials

| Dial | Value | Basis |
|---|---|---|
| VARIANCE | 3 | One shared workspace surface; recognisability across screens beats novelty *(→ PRD §2)* |
| MOTION | 2 | Owner answer, cycle-1: "this is a tool people check between tasks — keep it still" |
| DENSITY | 8 | Up to 2,000 active links per workspace; tables are the product *(→ PRD G3)* |

## 3. Users & Contexts

- **UX-U1** — Marketing team members, 3–15 per workspace, desktop-first during the workday;
  intermittent, task-driven visits. *(→ PRD §2)*
- **UX-U2** — Workspace admins managing members and billing; same surface, occasional use. *(→ PRD §2, F3)*

## 4. Information Architecture

Single workspace surface, five areas: link list (home), link detail/analytics, create link,
members, billing. Left rail navigation; the link list is always one click away.

## 5. Key Flows

- **UX-F1 — Create a branded link:** paste URL → optional custom slug → create → copy. Failure:
  slug taken (inline, at the field). *(→ PRD F1, G1)*
- **UX-F2 — Read a link's performance:** list → link row → analytics detail (totals, uniques,
  geography, referrers, time series). Data arrives progressively; series can be large. *(→ PRD F2, G2)*

## 6. Screen Inventory & States

| Screen | Empty | Loading | Error | Success |
|---|---|---|---|---|
| **UX-S1** Link list | "No links yet" + create action | Skeleton rows | Retry banner | Table of links, permanent — a link never expires *(→ PRD F5)* |
| **UX-S2** Link analytics | "No clicks yet" | Chart placeholders | Per-panel degraded state (geo provider down ≠ totals down) | Charts + tables |
| **UX-S3** Create link | n/a — form | Submitting | Slug taken, invalid URL | Created + copy affordance |
| **UX-S4** Members | Invite prompt | Skeleton | Retry banner | Member table with roles |
| **UX-S5** Billing | No plan yet | Skeleton | Stripe unreachable — read-only summary | Plan + seats + payment method |

## 7. Interaction Patterns

- **UX-I1** — Destructive actions (delete link, remove member) confirm explicitly; deleting a
  link warns that the short URL stops resolving. *(→ PRD F1)*
- **UX-I2** — Long operations show progress within the panel they affect; no full-screen blocking. *(→ PRD G4)*
- **UX-I3** — Full keyboard operability on the create-link flow. *(→ UX-A1)*

## 8. Accessibility Requirements

- **UX-A1** — WCAG 2.1 AA across the product; contrast at AA 4.5:1 minimum **on the analytics and
  table surfaces especially**, where dense small text lives. *(→ PRD §2, G2)*
- **UX-A2** — All figures (click counts, money) render in **tabular numerals** so columns scan. *(→ PRD F2)*
- **UX-A3** — Visible focus everywhere; reduced-motion honoured (motion is already dialled to 2).

## 9. Design-System Direction

**Built from primitives with a thin in-house layer** — no established component package. The
product reads as a utility dashboard; the team owns its own small set of table, form, and chart
surfaces. One system per product; this is it, named honestly.

Constraints the design language must satisfy (values live in `DESIGN.md`, not here):

- Contrast at AA 4.5:1 on analytics/table surfaces (UX-A1) — including every component
  background/text pairing.
- Tabular numerals for all figures (UX-A2).
- Density-first: spacing and type sized for tables of 2,000-link workspaces (DENSITY 8), not for
  marketing pages.
- Stillness: no decorative motion (MOTION 2, owner answer).

## 10. Out of Scope

Scoped against the declared terminus (one paying workspace through a full billing cycle): no
public API surface, no browser extension, no mobile app. Adoption metrics are outside done.

## Traceability

| PRD unit | Where it lands |
|---|---|
| G1 fast creation | UX-F1, UX-S3 |
| G2 analytics | UX-F2, UX-S2 |
| G3 launch scale | DENSITY 8, UX-S1 |
| F5 permanence | UX-S1 success state |

## UXD Review Notes

- **RN-1:** *(added)* per-panel degraded states on analytics (UX-S2) — because the PRD names
  external providers (Stripe, geo-IP) whose failure must not read as product failure.
- **RN-2:** owner answer, cycle-1 (see `docs/trail/uxd/cycle-1.md`): MOTION overridden 4 → 2;
  direction confirmed as built-from-primitives.
