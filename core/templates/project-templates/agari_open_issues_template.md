---
version: "1.1.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Agari open issues — <project>

> Companion to `agari.md`. The CPO declared the Agari non-interactively; this file holds what it
> could not settle from the inputs (the settled PRD and the project card).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `project-agari`. It folds your answers into the Agari and drops the resolved items.
> When nothing is left open, `project-agari` **deletes this file**: no file = the Agari is declared.
>
> **Commit before re-running.** The run that finishes clean removes this file, and git refuses to
> remove a file carrying uncommitted edits — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CPO folds them in, it first copies this file
> whole to `trail/agari/` — so what you decided, and why, stays readable and citable for good.

---

## 1. Open issues — questions about the terminus with no answer yet

### 1.1 <the question, in one line>
- **Why it matters:** <what in the Agari depends on this — the terminus itself, or one of its
  named conditions>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

### 2.1 <the decision, in one line>
- **Drafted into the Agari:** <the terminus or condition the CPO wrote into agari.md>
- **Rationale:** <why this was the best-effort call, and the PRD section it derives from>
- **If overridden:** <what moves if the draft is not taken — which condition changes, and whether
  the terminus itself shifts>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

<!-- add 2.2, 2.3, … as needed -->

<!--
No third bucket. The PRD's companion carries **directives** — actions outside the authoring
role's reach. Declaring a terminus needs no such action: it is read off the settled PRD and the
owner's product taste, both already in hand. If a genuine external action ever blocks an Agari,
that is a signal the terminus is waiting on something the PRD should have settled.
-->
