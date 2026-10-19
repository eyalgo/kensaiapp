# UXD — Briefbox

**Status:** Settled
**Owner:** CDO
**Version:** 1 — first authoring; the owner answered the single taste question (aesthetic lean) in review and it is folded here.

> The UXD is the experience source of truth. The design language (`DESIGN.md`) is authored off
> § Design-System Direction below — that section names the system and the constraints; every
> token value lives there, none here.

---

## 1. Design Read

Reading this as: a one-page editorial signup surface for tired evening readers, with a quiet,
generous language, leaning toward a print-editorial aesthetic.

## 2. Design Dials

| Dial | Value | Basis |
|---|---|---|
| VARIANCE | 5 | A single page that must feel authored, not templated *(→ PRD G2, UX Notes)* |
| MOTION | 1 | Calm is the promise; nothing moves unless it must *(→ PRD G2)* |
| DENSITY | 2 | One idea per viewport; generous whitespace is stated intent *(→ PRD UX Notes)* |

## 3. Users & Contexts

- **UX-U1** — Cold visitors on phones, evening, deciding in under thirty seconds. Mobile-first,
  one-handed. *(→ PRD §2)*

## 4. Information Architecture

One public page: pitch → sample excerpt → signup, with one full sample issue expanding inline on
the same page. There is no second surface.
No navigation chrome beyond a wordmark.

## 5. Key Flows

- **UX-F1 — Subscribe:** land → read the promise → enter email → confirmation-as-welcome.
  Failure: invalid email inline at the field; already-subscribed says so warmly. *(→ PRD F2, UX Notes)*

## 6. Screen Inventory & States

| Screen | Empty | Loading | Error | Success |
|---|---|---|---|---|
| **UX-S1** Signup page | n/a — static pitch | n/a — server-rendered | Invalid email, service down (inline) | Confirmation state, welcome-toned |
| **UX-S2** Sample issue | n/a — always has content | Minimal skeleton | Retry line | The issue, readable end to end |

## 7. Interaction Patterns

- **UX-I1** — One primary action per viewport; the email field and its button are the only
  interactive elements above the fold. *(→ PRD G1)*
- **UX-I2** — Validation inline, on blur, never on keystroke. *(→ PRD F2)*

## 8. Accessibility Requirements

- **UX-A1** — WCAG 2.1 AA; contrast at 4.5:1 minimum including the signup button pairing.
- **UX-A2** — The whole flow operable by keyboard and screen reader; the confirmation state is
  announced.

## 9. Design-System Direction

**A quiet print-editorial aesthetic, built from primitives** — no component package; the surface
is one page and earns hand-set treatment. One system per product; this is it, named honestly.

Constraints the design language must satisfy (values live in `DESIGN.md`, not here):

- AA 4.5:1 contrast everywhere, the signup button pairing included (UX-A1).
- An editorial reading voice: a display/serif register is permitted for the pitch if body text
  stays effortless on phones (UX-U1).
- Calm: no decorative motion (MOTION 1), whitespace-led composition (DENSITY 2).

**No source exists yet** — the product is greenfield; nothing has been built. There are no brand
assets beyond the name.

## 10. Out of Scope

The weekly email's own template (external service); any authenticated surface.

## Traceability

| PRD unit | Where it lands |
|---|---|
| G1 convert | UX-F1, UX-I1 |
| G2 calm | MOTION 1, DENSITY 2, § 9 |
| F2 signup | UX-F1, UX-I2 |

## UXD Review Notes

- **RN-1:** owner answer (in review): the aesthetic lean is print-editorial — "it should feel
  like a well-set book page, not a SaaS landing page."
