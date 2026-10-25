---
version: "2.3.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- The single source of the NFDR shape. Lands at `<Product path>/docs/nfdr.md`. Its companion is
     `architecture_open_issues_template.md`; the ADR pair it is written alongside is
     `adr_record_template.md` and `adr_index_template.md`, all beside this file.

     MODEL-FACING: the `product-architecture` skill reads this file and authors a fresh document, so
     everything here may explain itself and none of it survives into the result. No script stamps it,
     which is why it carries a `version:` at all
     (`<CORE>/doctrine/governance/versioning.md` § Templates — the stamper's code is the proof).

     WHAT THIS FILE OWNS: the sections of the document, their order, and the shape of an entry in each.
     Nothing else. What each section must answer, what makes an obligation verifiable, how an unsettled
     item is routed, and what may change on a re-run are
     `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md`'s — the authoring body this shape is
     stamped under, declared on both sides (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).
     The posture gate, the file loop and the commit are the `product-architecture` skill's.

     THIS DOCUMENT REVISES IN PLACE; THE ADRs DO NOT. That asymmetry is the whole cut: a record is a
     dated choice that stays true after the architecture moves on, and an entry here is a rule a future
     change could break. Same run, two lifecycles — so the ADRs supersede, and this file carries a
     `Version:` and changes under provenance.

     THREE THINGS EVERY ENTRY CARRIES, and an entry missing any of them is not yet an entry:
       - a stable typed ID `QC-n` — never reused, never renumbered, because an acceptance criterion, a
         change spec and a later revision each need to cite one obligation rather than a paragraph;
       - a `verified by:` tail naming the command, test layer, or review gate that FAILS when the
         obligation is broken. A constraint whose violation cannot be named is a sentence about the
         product. Where no harness exists the tail names a review gate AND says the harness is
         missing — that is honest and checkable; silence is neither;
       - an inline trace tag naming the upstream fact it realizes (`SRS NFR-n` / `C-n`, `SDD § 4`, an
         ADR record, or a doctrine default). Quality floors originate upstream: an entry tracing to
         nothing is an invented requirement, and the fix is a finding routed to the CTO, not a
         confidently-written rule.

     A CONDITIONAL SECTION THAT DOES NOT BIND THIS PRODUCT IS DECLARED NOT APPLICABLE WITH ITS REASON,
     never silently omitted. An absent section and an inapplicable one look identical to a reader, and
     only one of them is a finished thought.

     NO `## Open Questions` SECTION, deliberately, and for the same reason the FDR has none: this is a
     record every change is checked against, and an unresolved obligation cannot gate anything.
     Anything unsettled goes to the run's companion.

     `**Inputs read:**` IS A HEADER LINE OF THIS DOCUMENT, AND ITS FORM IS NOT THIS FILE'S TO STATE.
     `<CORE>/doctrine/governance/unsettled_inputs.md` owns the rule and the form, for every document
     in the chain rather than this one — write the line from there. This template owns only that the
     line is in the header, which is the placement that suits a document revised in place beside
     append-only records.

     SECTION NUMBERS ARE LOAD-BEARING DOWNSTREAM. The delivery loop reads forbidden imports by section
     number, and under this shape they are § 1.2. Any file citing them moves in the same commit as the
     shape does — a rename is a two-file edit, in one commit.

     PROVENANCE — the shape is OURS. No vendor publishes an NFDR schema, so there is no external format
     to track and no linter to run a filled-in one against. What stands where a linter would have stood
     is § 10's verification map, which is executable, plus the prompt's finish walk. The reasoning behind
     the roster, the entry form and the cut was written once as a research record in the instance that
     authored this shape, and is deliberately **not cited by path here**: every instance stamps from this
     file, so a path into one instance's own projects resolves in none of the others. A second copy of
     that reasoning here is the one that would go stale. -->

# NFDR — <product name>

**Status:** Draft | Settled | Locked
**Owner:** Principal Architect
**Version:** <n> — <one-line note on what this revision changed about the product's obligations>
**Inputs read:** SRS <status> · SDD <status> · FDR <status>

> The NFDR is the product's **standing obligations, consolidated and verifiable**: every quality
> constraint a change is checked against, derived from the SRS, the SDD, the FDR and the ADR — never
> invented here. It is updated in place with versioning (unlike the ADRs, which supersede).
> **Every entry carries a stable typed ID** (`QC-n`, never reused or renumbered), **a
> `verified by:` tail** naming the command, test layer, or review gate that fails when the
> obligation is broken, and **an inline trace tag** naming the upstream fact it realizes
> (`SRS NFR-n`/`C-n`, `SDD § 4`, an ADR record, or a doctrine default). An entry with no
> nameable verification is not yet an entry. A conditional section that does not bind this product
> is declared not applicable with the reason — never silently omitted. **`Inputs read:` names every
> upstream document this revision read and the status it carried at the time** — an obligation
> derived from a Draft source is still binding, and the line is how a later reader knows which ones
> were.

---

## 1. Structural integrity

<The structure-level obligations every change is verified against, derived from the ADR log's
dependency decisions and the doctrine defaults. Four fixed subsections.>

### 1.1 Architectural invariants

- **QC-1:** <invariant — cite the ADR record it realizes, do not restate its rationale>
  — *verified by:* <check> *(traces to: ADR-NNNN)*

### 1.2 Forbidden imports

<Every module appears; forbidden directions stated explicitly, never left to be inferred from the
allowed list. This is the one graph — the allowed half and the forbidden half are stated together
here and nowhere else.>

- **QC-2:** `<pkg>/domain/` must not import from: <list>
  — *verified by:* structural check (test layer 6) *(traces to: ADR-NNNN)*

### 1.3 Layer isolation

- **QC-3:** <one clause per layer: what it may and may not use>
  — *verified by:* structural check (test layer 6) *(traces to: ADR-NNNN)*

### 1.4 Replaceability

- **QC-4:** Swapping <A> for <B> touches <layer> only; no other layer changes.
  — *verified by:* review at development-design when a change touches <layer>
  *(traces to: FDR <product decision>; ADR-NNNN)*

## 2. Security

<Trust boundaries, secrets handling, input validation, supply chain — everything about resisting an
attacker that is not about *who someone is*, which is § 3's. From SRS § 4.3 and the SDD § 4
data-protection conditions. Name the trust boundaries first — an obligation that names no boundary
protects nothing in particular. The threat classes follow the product's artifact class and are not
assumed: for skills, prompts and launchers they are the agent ones — injection via read content,
exfiltration, excessive agency — not the web list.>

- **QC-<n>:** <obligation> — *verified by:* <check | gate> *(traces to: …)*
- **Advisory exception record:** <path where an exception for a dependency advisory the product does not reach is kept — read by the dependency audit — with the window an entry stands under (days from the advisory's publication, by severity) and how one is renewed. With no line here, `development-security` writes `checks/deps/advisory_exceptions.toml`.>

## 3. Authentication & access control

<Who a caller is, and what they are then allowed to do. Identity and its proof, session and credential
lifetime, authorization model and its default, and privilege boundaries between parts of the product.
From SRS § 4.3 and the SDD § 4 identity and authorization conditions.

**Its own section since 2026-08-31, at the owner's direction** — it was one clause of § 2, and the
concerns behind it have their own failure modes, their own literature and their own verification. A
constraint about *who may* is not the same kind of claim as one about *what resists*.

**Import or reach — the test against § 1.3.** The privilege half overlaps layer isolation, and without
a test a run writes the same sentence in both places. A constraint about what a component may **import**
is structural integrity, verified over the import graph at test layer 6. A constraint about what it may
**reach** — a credential, a destination, a writable path, a spawned process, a granted tool — is this
section, verified by a capability check, which is a different check even when both are greps. They
coincide often enough to be confusing and diverge exactly where it matters: a module can import nothing
forbidden and still read `~/.env`.

**Conditional, and the not-applicable case is the common one here** — a CLI run by the person who owns
the machine, and a skill stack invoked inside a session, authenticate nobody. Declare it not
applicable **with the reason and the boundary that makes it true** — the entry naming what would
change it is the section. What is never not-applicable is the *privilege* half where a product has
parts with different reach: a credential a run may read, a path it may write.>

- **QC-<n>:** <obligation> — *verified by:* <check | gate> *(traces to: …)*

## 4. Privacy, data retention & compliance

<What the product may hold, for how long, deletion paths, regulatory constraints — from SRS § 4.3 and
§ 7. Distinct from § 2: security is "can an attacker read it", this is "may we hold it at all, and for
how long". Where the product holds no personal data, the entry saying so — bounded to the data model —
is the section.

**A regulatory obligation the product must hold at release belongs here whether or not it is about
data.** A per-release audit of what the product claims, a condition on how something must be presented,
a disclosure that must be present — these are rules a change can violate and a named check can catch,
which is this document's own definition of an entry, and no other section fits them. Behaviour the
product must exhibit is the FDR's; an obligation that must be *held and shown* at release is this
section's, because the FDR carries no verification tail to hold it.>

- **QC-<n>:** <obligation> — *verified by:* <gate — typically re-review when a change adds a data
  field> *(traces to: SRS § 6 DR-n / § 7 C-n)*

## 5. Performance & capacity

<Measured ceilings — latency, volume, resource use — from SRS § 4.1 and § 4.4. Every threshold cites
its SRS NFR; the NFDR never asserts a number of its own. Not applicable only when the SRS states no
performance or scale bar and the FDR fixes no volume — say so and cite both.>

- **QC-<n>:** <obligation with the measure> — *verified by:* <timing assertion at layer 5 | review bar
  with the missing-harness reason stated> *(traces to: SRS § 4.1 NFR-n)*

## 6. Availability & reliability

<From SRS § 4.2 and the SDD § 4 runtime shape. SLO-shaped for a served product; recoverability and
degradation clauses for anything with state or a dependency that can be absent. Not applicable for a
product with neither — say so.>

- **QC-<n>:** <obligation> — *verified by:* <error-path test at layer 5 | measurement source for an
  SLO> *(traces to: SRS § 4.2 NFR-n)*

## 7. Observability & monitoring

<What makes a failure visible from outside, from SRS § 4.5 and the SDD § 4 instrumentation conditions.
For a served product: structured events, metrics, symptom-based alerting. For a CLI: exit-code and
stderr discipline. The floor is never empty — a product whose failures are invisible cannot be
operated.

**The events that prove an action occurred, and name who took it, belong here** — tracing to the
security or access-control concern that needs them. Two of ISO/IEC 25010's security subcharacteristics,
non-repudiation and accountability, are satisfied by a record of what happened, which is an
observability obligation with an observability check. Without this clause they are the one place a
security obligation falls out of the constraint set entirely: § 2 does not ask for a log, and this
section did not know it was owed one.>

- **QC-<n>:** <obligation> — *verified by:* <check> *(traces to: SRS § 4.5 NFR-n; SDD § 4)*

## 8. Operational constraints

<Only what exceeds the execution context the project card already carries: config surface, install
path, upgrade rule, interoperability contracts (SRS § 5.3). Where nothing does, declare not applicable
pointing at `project.md`.>

## 9. Test strategy

The layer set is **not defined here** — it is `<CORE>/doctrine/engineering/testing_doctrine.md`, and
this table is one project's realization of it. Tooling and paths come from that doctrine's language
overlay (`testing_python.md` for Python; a product in another language records its own tools here). If
this table and the doctrine disagree on the layers, this table is the copy and is wrong.

| Level | Scope | Tool | Where it lives |
|---|---|---|---|
| … | | | |

- **Layers 3 and 4 are optional** — omitting either requires the rationale stated here, not silence.
- **Layers 6–7 are QA-role ATDD work.** Where QA is not active on this project, record them here as
  QA-owned and name what verifies these layers instead.

## 10. Verification map

<A projection of every machine-checked entry above — one table a run can execute top to bottom. When a
row disagrees with its entry, the entry is right and this row is stale. An entry above whose
`verified by:` names a command and has no row here is a defect in this section.>

**"Runs over" is not decoration.** The same check catches different defects at different scopes: a
secrets scan over a change's diff catches a secret being *introduced*, over the whole tree catches one
already *there*; a dependency audit is only meaningful over the whole resolved set; a path-confinement
test runs against the entry points a change touches. Two values, and a row that cannot pick one has not
decided what it is checking.

| QC | Check | Command / layer | Runs over | Gated at |
|---|---|---|---|---|
| QC-2 | import direction | <command> | the change \| the tree | <pipeline step> |

---

## NFDR Review Notes

<The creation trail: every obligation not directly traceable to an upstream sentence carries its why
here — a doctrine default applied, an owner answer folded in, a derivation from the ADR log that
another architect could have made differently (and then it should not be here — route it). On a
revision, every change to settled content names the legitimate reason that authorized it.>

- **RN-1:** <what was added or changed beyond the upstream documents> — *because* <reason>
  *(re: QC-n; source: <…>)*
