---
version: "1.10.1"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# SRS — <product name>

**Status:** Draft | Settled | Locked
<!-- Draft = open issues or choices to confirm remain (open-issues file present).
     Settled = nothing left for the owner to answer and no open technical question — the done
       signal, and the state a finished SRS carries; the open-issues file is gone.
     Locked = ratified as the source of truth. -->
**Owner:** CTO
**Version:** <n> — <one-line note on what this revision changed>
**Inputs read:** PRD <status>
<!-- `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO
     STATE. `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every
     document in the chain rather than this one — write the line from there. **Every input this
     revision read, not only the unsettled ones**: a line that appears only when something was
     `Draft` is indistinguishable from a run that forgot it. -->

> The SRS is the technical source of truth: the system-level **what**, derived from the PRD and
> read cold by the Principal PM (Delivery Plan / FDR) and the Principal Architect (ADR / NFDR).
> It is updated in place with versioning (bump the line above on each material change); every
> delta in a revision traces to an owner answer/directive or a change in the upstream PRD, and
> the Version line names what changed and why.
> Every requirement traces back to a PRD feature or goal — no requirement without a source. Keep the
> **how** — architecture, component design, delivery sequencing — out; that belongs downstream
> (the SDD you write, with the CPO's and the CDO's calls folded in, the ADRs/NFDR the Principal Architect owns, the Delivery
> Plan). Give every item a stable typed ID (`FR-n`, `NFR-n`, `DR-n`, `C-n`, `AC-n`) so downstream
> documents can reference it. Omit a section only when it genuinely does not apply; do not pad
> one to fill it.

---

## 1. Purpose
<One short paragraph: what the system must do, at the system level, and the product intent (from
the PRD) it serves.>

## 2. Scope
<What the system covers and — as load-bearing — what it deliberately does not. Name the PRD scope
this SRS realizes; anything in the PRD that this SRS does not yet cover is called out here. Name
the **terminus** this SRS is scoped against — the project's 上がり Agari — and what it places
outside done; where no terminus was available, say that instead of implying one.>

## 3. Functional Requirements
<The behaviors the system must exhibit, each as a testable `FR-n`. Group them under thematic
subsections (add or rename subsections to fit the product). Every FR names the PRD feature or use
case it traces to.>

### 3.1 <Capability area — e.g. Accounts & Access>
- **FR-1:** <A single, testable behavior the system must exhibit.> *(traces to: PRD <feature/goal>)*
- **FR-2:** ...

### 3.2 <Capability area>
- **FR-3:** ...

## 4. Non-Functional Requirements
<Quality bars the system must hold, each as a measurable `NFR-n` (a number or observable, not a
vibe). Keep the six categories; add one only if the product genuinely needs it. Every NFR either
traces to a PRD goal or success metric, or — when the PRD sets no number (the usual case for a
latency, availability, or throughput bar) — carries the provenance of the threshold you invented:
either a *choice to confirm* in the open-issues file for owner sign-off, or a Review Note recording
the basis of a CTO-derived value. No NFR asserts an invented threshold with no provenance — a bare
invented bar reads as a ratified requirement when it is an unconfirmed owner-taste call. (This is
the NFR twin of the FR trace rule above.)>

### 4.1 Performance
- **NFR-1:** <e.g. p95 request latency < 300 ms under N concurrent users.>

### 4.2 Availability & Reliability
- **NFR-2:** <e.g. 99.9% monthly availability; graceful degradation when <dependency> is down.>

### 4.3 Security & Privacy
- **NFR-3:** <e.g. all data in transit over TLS 1.2+; data at rest encrypted; authZ model.>

### 4.4 Scalability
- **NFR-4:** <e.g. scales to N users / M records without architectural change.>

### 4.5 Observability
- **NFR-5:** <e.g. structured logs, metrics, and traces for every critical flow; alertable.>

### 4.6 Maintainability
- **NFR-6:** <e.g. modular boundaries; a new <thing> added without touching <other thing>.>

## 5. Interfaces
<How the system is reached and what it talks to. Requirement-level, not wire-level — name the operations and dependencies, never endpoint-path templates, header names, request-id fields, or other wire detail. This altitude holds on a revision or recreate too: do not *add* wire-level detail that was not in the prior settled version.>

### 5.1 User Interface
- <The surfaces the user interacts with, at the system level — not visual design.>

### 5.2 API
- <The programmatic surface the system exposes: the operations, not the schemas.>

### 5.3 External Services
- <Every external system or provider the system depends on, and what it relies on it for.>

## 6. Data Requirements
<The entities the system holds, their key fields, and their relationships — at the requirement
level, not the physical schema. Each as a `DR-n`.>

- **DR-1:** <Entity — its purpose, key fields, and the relationships that matter.>
- **DR-2:** ...

## 7. Constraints
<Technical, business, or regulatory constraints the system must respect. Each as a `C-n`.>

- **C-1:** <A constraint that bounds the design — platform, standard, regulation, budget.>
- **C-2:** ...

## 8. Acceptance Criteria
<End-to-end, verifiable criteria that say the system meets this SRS. Each as an `AC-n`, traceable
to the FRs/NFRs it exercises.>

- **AC-1:** <An observable, verifiable outcome that proves a requirement is met.> *(covers: FR-n / NFR-n)*
- **AC-2:** ...

---

## SRS Review Notes
<This section is the SRS's **creation trail** — every load-bearing element carries a written *why*.
A PRD-derived requirement carries its why inline, as its `*(traces to: PRD …)*` tag; **everything the
PRD did not settle carries its why here**, with its reason: an invented value, an owner's answer
folded from the open-issues file, a best-effort choice you drafted, or a place you resolved a PRD
contradiction the SRS's own way / stated a requirement the PRD only implied / tightened a vague goal
into a testable one / softened false precision. On a revision **or a recreate**, **every change to
*any* already-settled content carries the legitimate reason that authorized it** — an owner
answer/directive or an upstream PRD change, never a silent re-derivation. Settled content is all of
it: values, verification/measurement dates on unchanged facts, §5 interface detail, and the existing
wording of these very notes; none is re-stamped, reworded, or dropped without such a reason. The *why* is the **gate, not a caption**: a change with no
findable legitimate reason is a bug and should not appear in the SRS at all. A genuine product-intent
gap is *not* recorded here — it is surfaced in the open-issues companion file for the owner/CPO; once
the owner **answers** such a call (setting a load-bearing value the PRD does not state — a coverage
floor, a reliability bar, a time bound), capture that answer here, recording the value and that it
was the owner's confirmed call. The open-issues file is deleted when the round finishes clean, so a
requirement tagged only "owner-confirmed, open-issues answer" would dead-end at a file that no longer
exists; this trail is the durable provenance a cold reader can check. Omit this section only when
every element's why is already carried inline by its PRD-trace tag and the SRS added no decision
beyond a faithful read of the PRD.
Each note names its **relation to the PRD**: *added* (the SRS states something the PRD does not) or
*changed* (it departs from what the PRD says). A **suggest-remove** — something the PRD includes
that you think should be cut — is a product-intent call and never appears here; it goes to the
open-issues companion as a choice to confirm.>

- **RN-1:** *(added | changed)* <what departed from / went beyond the PRD> — *because* <reason> *(re: FR-n / NFR-n; PRD source: <feature/goal>)*
- **RN-2:** ...

---

## Open Questions

<A technical question this SRS leaves standing — recorded so a reader does not mistake
silence for an answer, and never papered over.

**This section is not the companion, and never a copy of it.** Anything awaiting the owner lives in
`SRS_open_issues.md` alone, and that file's **absence is the done signal**. An item written in
both has two homes and only one of them says when it is finished — so this document could read
settled while the list below still stands open. If the owner has to answer it, it belongs there and
not here.

What belongs here is a question this SRS cannot close and is **not** asking the owner to close:
one that resolves downstream — in the SDD, in a spike, or against a system that does not exist
yet — recorded so whoever meets it next is not the first to notice it.

Omit this section entirely when there is nothing in it. An empty heading reads as an unanswered
question.>

- [OPEN: <the question, and what would settle it>]
- ...
