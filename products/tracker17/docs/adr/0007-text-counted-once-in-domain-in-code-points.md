# ADR-0007: Count typed text once, in `domain`, in code points, after `web` turns each line break back into one character

**Status:** Accepted
**Date:** 2026-10-06

## Context

Every text field has a maximum length: 200 characters for a name, a title or a label, 4,000 for a
project description or a comment (SRS FR-40). FR-40 also says "A value that the tracker's own field
let the operator enter is never refused as too long". The field and the rule do not naturally count
alike. The HTML standard measures `maxlength` in UTF-16 code units and counts a line break as one
character, and a form submission sends that line break as the two characters CR LF (SDD § 4 RT-10
quotes both). Saved data is checked against the same rules when it is read at start (SDD § 4 SD-5),
so the rule's count also decides which saved data is readable.

## Decision

The two lengths are stated once, in `domain`. `web` receives them through `application` and writes
each field's `maxlength` from them. One character is one Unicode code point, counted on the value as
it would be saved, spaces included. Before a submitted value reaches `application`, `web` turns
every CR LF pair, and every remaining CR, into a single LF, as the Infra standard's *normalize
newlines* does. No part changes a typed value in any other way, and no part shortens a value to make
it fit. `domain` refuses a longer value with a typed refusal, and `web` maps that refusal by its
type, so `web` compares no length.

## Alternatives ruled out

- **A second copy of the lengths in `web`.** It lost because the field and the rule could then
  disagree about the number (SDD RN-25).
- **Counting the value as the browser sends it**, line break as two characters. It lost because a
  comment or description the field let in, holding line breaks and filled to its maximum, would be
  refused, which FR-40 forbids and SRS AC-20 tests.
- **Counting in UTF-16 code units, as the field does.** *Reconstructed:* the SDD does not weigh this
  as an option. It states the property it chose instead — counting code points, so "the field's own
  count is never the looser one" — and the cost it accepted (SDD § 11 R-11). The reason recorded here
  is that one: with code points the field can only be stricter than the rule, never looser.

## Consequences

Easier: the field and the rule cannot disagree about the number. Every value the field lets in is
accepted, which is what makes the over-long refusal reachable only by a request no page of the
tracker sends.

Harder: a character outside the Basic Multilingual Plane counts two in the field and one in the
rule, so such a field can stop before the stated number. Nothing is refused, and the SDD accepts it
(SDD § 11 R-11). A slice that adds a text field must write its `maxlength` and test a longer value.

Undoing it is costly in a way no diff shows. The count decides which saved data is readable at start,
so changing how a character is counted can make data saved under the old count unreadable under the
new one.

**Dependence:** the HTML and Infra standards, as SDD § 4 RT-10 quotes them, and Chromium's
following them. Whether Chromium counts a line break as one character against `maxlength` and sends it
as CR LF is open (SDD § Open Questions, the first item). The description half of SRS AC-20's test
settles it.

## Traces to

- `products/tracker17/docs/SDD.md` § 4 RT-10, SD-5, OB-4; § 11 R-10, R-11; § Open Questions, the
  first item; SDD Review Notes RN-22, RN-24, RN-25.
- `products/tracker17/docs/trail/sdd/cycle-2.md` § 2.1 — the answer, "confirm, with two additions",
  that fixed the outcome and left the means to the CTO.
- `products/tracker17/docs/SRS.md` FR-39, FR-40, DR-6, AC-20, RN-21.

## Binds

QC-9.
