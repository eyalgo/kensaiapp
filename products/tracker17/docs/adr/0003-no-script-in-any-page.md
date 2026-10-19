# ADR-0003: Run no script in any page, and answer every action with a whole page

**Status:** Accepted
**Date:** 2026-10-06

## Context

The UXD reads the product as plain semantic HTML pages with the browser's own form controls, and
weighs each decision against whether it adds a part the reader has to read (UXD § 1). It already
rules out partial pages and pages that update themselves (UX-I8, UX-I9). Three UXD entries then had
to hold on a page that reloads whole: the operator "stays where they were" after an action (UX-F4),
a refusal's reason sits "beside the control that was used" (UX-I3), and messages are "announced to
assistive technology without moving focus" (UX-A5).

## Decision

No page runs a script. Every interaction is a link or a form submission, answered by a whole page.
The page that answers a submission opens at the place of the action: keyboard focus is set there
with the HTML `autofocus` attribute, and the address carries no fragment (SDD § 4 RT-9). A
completion line or a refusal is the accessible description of the element the page opens on, and
never takes focus (EX-14). The in-place confirmation of UX-I2 is its own page load (EX-6).

This is the CDO's call. The answer kept the no-script model and replaced two of the draft's three
consequences: where a page opens after an action, and how a message is announced.

## Alternatives ruled out

- **One script file in `web`**, to change part of a page in place, announce messages on arrival and
  keep focus on the row acted on. It lost because it adds a second language for the reader, a second
  units-table row and project-card language, a rewrite of the page policy that now forbids scripts
  outright (SDD § 4 SEC-3), and a way to test it.
- **An application in the browser.** It lost for the reasons ADR-0001 records against it.

## Consequences

Easier: the reader reads one language. The browser keeps no state that has to stay in step with the
tracker. UX-I8 and UX-I9 hold by construction. The page policy can refuse every script.

Harder: no part of a page changes in place. A page reopens with the place of the action in view, but
not always at the same height in the window (SDD § 9 TO-2). The CDO accepted both costs.

Undoing it costs one script file in `web`, a second language in SDD § 3's units table and on the
project card, a change to SEC-3's policy, and tests for the script.

**Dependence:** Chromium's handling of `autofocus`. The HTML standard says the attribute "applies to
all elements, not just to form controls". Whether current Chromium focuses an element that is not a
control, brings it into view and reads its description is not verified (SDD § 11 R-2 and its Open
Questions). Focus tests on a form control, on an element that is not a control, and on the
confirmation settle it. If one fails, the experience conditions stand and the fallback is undoing
this record inside `web`, which would land as a record superseding this one.

## Traces to

- `products/tracker17/docs/SDD.md` § 4 EX-2, EX-4, EX-5, EX-6, EX-14, RT-9, SEC-3; § 9 TO-2;
  § 11 R-2; § Open Questions, the second item; SDD Review Notes RN-12, RN-20, RN-21.
- `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.3 — the CDO's answer, "override: keep the
  no-script page model, and replace two of its three consequences".
- `products/tracker17/docs/SDD.md` § 2, the shape table's fourth row.

## Binds

QC-34.
