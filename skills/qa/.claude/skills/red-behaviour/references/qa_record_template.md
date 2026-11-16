<!-- Template-file metadata is stamped by the merge, never on a change branch; this file carries none. -->

# QA record — {key}

<!-- One file per change, at the path the paths command prints, committed with `Role: QA` on the
instance's change branch. A record takes one of two forms, and never both.
A red record carries the `Red commit:` line and one or more `Scenario:` lines, and no `No reach:` line.
A no-reach record carries one `No reach:` line, and no `Red commit:` line and no `Scenario:` line.
Both forms carry `Change:`, `Way in:`, `Base commit:` and `Review notes:`.
The chain reads the slots below by their labels, in this order, and refuses the record when a slot its
form carries is missing or empty. Write each slot on one line. Delete the slots the record's form does
not carry, because a record holding a slot of each form is refused.
The change key goes in the first slot, exactly as the run was given it.
The way in goes in the second, as the product's docs/nfdr.md on main records it.
The third takes the full hash of the base commit the verdict printed.
In a red record, the fourth takes the full hash of the red commit, and the record is committed after
that red commit. Write one scenario line per scenario, in the order the verdict printed them. Each gives
Behave's location, the kind (`new or changed` or `kept`), the spec rule it shows by its CP label, and
the outcome before the change (`failed` or `passed`), separated by ` — `.
In a no-reach record, the `No reach:` line says why nothing the change states can be reached through
the way in the second slot names. The record is committed alone, with no red commit.
The last slot holds every review note, with its reason, on that one line, or `none`. -->

Change: {key}

Way in: {way in}

Base commit: {base commit}

Red commit: {red commit}

Scenario: {location} — {kind} — {rule} — {outcome}

No reach: {why}

Review notes: {notes, or none}
