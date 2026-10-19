# ADR-0001: Put the task rules in a core with no input or output, behind server-rendered pages

**Status:** Accepted
**Date:** 2026-10-06

## Context

tracker17 is small. Its first readers judge it on whether it is simple to read (SRS NFR-10), and
every part the design adds is a part they have to read (SDD § 1). Against that, three facts forced
a choice:

- The product holds a real body of rules, and several are used on more than one page. SRS AC-13
  requires that "the list marking, the overdue filter and the summary count agree".
- The interface has already been replaced once while the rules carried over. tracker16-X was a
  command line, tracker17 is a browser (SRS C-3), and tracker16-X's rule code is the preferred
  starting point (SRS C-5).
- Tests must replace the clock (AC-13 sets today's date) and replace or interrupt the saved data
  (AC-9).

## Decision

tracker17 is a rule core behind server-rendered pages, in five parts at the product root:

- `domain/` holds the entities, the tracker state as one value, and every rule. It touches no disk,
  no clock and no network, builds no HTML, and imports no other part.
- `application/` holds the operator's actions. Each applies a `domain` rule to the current state,
  saves the result, and only then makes it current. It states the two contracts it depends on, one
  for saving and one for the clock.
- `persistence/` reads and writes the saved data.
- `web/` turns browser requests into actions and their results into whole HTML pages.
- `main.py` is the composition root. It wires the four together and is the only module that names
  a concrete `persistence` or `web` class.

The direction of dependence is the SDD's: `web` imports `application`, `application` imports
`domain`, `persistence` imports `domain`, `main` imports all four, `domain` imports no other part,
and no part imports `main`. Every part may import `errors.py`. This is tracker16-X's own shape with
its command-line part replaced by a browser part.

## Alternatives ruled out

- **One module per screen**, each reading the saved data, applying its rules inline and building
  its page. It is the fewest files to read. It lost because the rules are shared: the overdue rule
  appears on two lists, a filter and the summary (SRS FR-26, FR-35, FR-38), and each copy could
  drift from the others. The unit layer SRS NFR-11 requires would also have no isolated logic to
  test.
- **A database at the centre**, with filtering, sorting and the summary written as queries. It lost
  because the volume fits in memory and one operator writes (SRS NFR-1, NFR-7), and because the
  newest and least proven rules, such as undated tasks sorting last in either direction (FR-34,
  FR-36), would live in query text where a unit test cannot isolate them.
- **An application in the browser** over a local data interface. It lost because no page updates
  itself and each appears whole (UXD UX-I8, UX-I9), the product exposes no programmatic interface
  (SRS § 5.2), and it would add a second language, a second state to keep in step, and an
  interface between them.

## Consequences

Easier: the shared rules have one home, so AC-13's three-way agreement is one rule tested once. The
predecessor's rule code carries over. Tests hand the actions a clock and a saver.

Harder: a small product carries five parts and seven seams, and each seam is a contract the reader
reads. This shape keeps exactly the insulation the three facts above pay for, and no more.

Every later change is checked against the import graph and the layer clauses this record binds. A
change that adds a sixth part, or an import edge the direction above does not list, needs a new
record that supersedes this one.

Undoing it is cheap in one direction and expensive in the other. Folding parts together is moving
files, because `domain` depends on no other part. Pulling shared rules back out of page modules
after they have drifted apart is the expensive direction, and this choice avoids it.

**Dependence:** none outside the product. The browser, the disk and the clock are stable edges, and
tracker17 owns every contract across them (SDD § 2, force 2).

## Traces to

- `products/tracker17/docs/SDD.md` § 2 — the seven forces, and the shape table: row 1 taken, rows
  2 to 4 not taken, each with its *Wrong when*.
- `products/tracker17/docs/SDD.md` § 3 — the parts table, the seams `SM-1` to `SM-7`, and the
  direction of dependence.
- `products/tracker17/docs/SDD.md` SDD Review Notes RN-2.
- `products/tracker17/docs/SRS.md` C-3, C-5, AC-13, NFR-3, NFR-7, NFR-10, NFR-11.

## Binds

QC-1, QC-2, QC-13, QC-14, QC-15, QC-16, QC-17, QC-18, QC-20, QC-21, QC-22, QC-23, QC-24, QC-27.
