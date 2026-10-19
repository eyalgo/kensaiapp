---
version: "2.2.0"
---

# PM prompt — right-size a unit of work

**This file is the sizing test, and nothing else.** It holds no read-first input list, no set of
candidate changes to weigh, and no stop that waits on an owner. A run arrives here having already
settled *what* it is sizing; the only thing it takes away is whether that thing is the right size.

**Stations and changes have different scopes.** A station describes a reached-when; a change is
one deliverable increment toward it. Use the outcome boundary below when sizing either, and the
one-flow limit when sizing a change.

**Callers read this file.** It owns the sizing test; callers point here rather than quoting or
redefining it.

## Right-size to one honest merge

Establish the unit of acceptance **before** examining how the work could be split. Read the request
and the governing product contracts it cites. Name the user operation, workflow, or system
responsibility being delivered or repaired, and the conditions under which it is accepted as complete.
Use that same boundary for the whole sizing decision; do not redefine it around each requested edit.
A shared subsystem or a broad goal such as “improve quality” does not establish a unit of acceptance.
When no prior contract exists, derive the bounded capability and its completion conditions from the
request itself; a formal product document is not required.

Classify the requested work against that boundary:

- **One capability and its acceptance obligations:** keep its implementation, error paths,
  diagnostics, constraints and verification together. A repair can close several outstanding
  obligations of an existing capability even when those obligations need different code or tests.
  Neither separate test cases nor separate possible commits turn those obligations into new
  capabilities. An earlier merge does not make an unmet obligation cease to belong to its contract.
- **Separate capabilities:** split when the request introduces or repairs different user operations
  or system responsibilities, each with its own acceptance boundary. A shared screen, release,
  station or “remaining gaps” title is not evidence that they are one capability. Identify the
  separate operations or responsibilities and their source contracts; listing implementation tasks,
  diagnostic requirements or tests is not a sufficient reason to split.

Then check delivery size. The next change must fit one development flow, from spec to sealed
implementation. If the capability is too large, identify the concrete delivery obstacle and choose a
smaller complete increment with its own acceptance boundary. Keep that increment's implementation
and required proof together. A station may take several such changes to reach its reached-when.

The sizing decision names the acceptance boundary, its source, and how the requested work maps to
it. A multiple-change finding must establish separate capabilities or a concrete delivery-size
problem under this test; the fact that a subset could be tested or merged alone does not establish
one. Do not split an acceptance checklist into one change per unchecked item.
