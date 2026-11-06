# NFDR — tools

**Status:** Settled
**Owner:** Principal Architect
**Version:** 1 — the first revision, which fixes one obligation: QC-1, the dependency audit over `uv.lock`, with its owner
**Inputs read:** ADR-0001 Accepted

This document holds the tools product's standing quality obligations: the constraints every change to
the product is checked against. Each obligation carries a stable ID that is never reused or
renumbered, a check that fails when the obligation is broken, and a trace to the upstream fact it
realizes.

**This revision fixes one obligation, QC-1 in § 2, and is settled for QC-1 alone.** It is not the
tools product's full quality contract. A section below that reads *Not stated in this revision* fixes
nothing, and it does not say whether its concern applies to the tools product.

`ADR-0001` below is `core/tools/docs/adr/0001-lock-the-tools-suite-with-uv.md`. `uv.lock` is the lock
file tracked at the repository's top-level directory.

---

## 1. Structural integrity

### 1.1 Architectural invariants

Not stated in this revision.

### 1.2 Forbidden imports

**This revision fixes no module set and no import graph.** It lists no module of the tools product,
and it neither allows nor forbids any import. This section is not an empty graph that forbids every
import.

### 1.3 Layer isolation

Not stated in this revision.

### 1.4 Replaceability

Not stated in this revision.

## 2. Security

This revision states one supply-chain obligation and names no trust boundary or threat class.

- **QC-1:** No package that `uv.lock` resolves carries a published advisory that has not been
  answered. The audit that checks this takes `uv.lock` as its input and runs from the repository's
  top-level directory, where `uv.lock` is tracked. It covers every package `uv.lock` resolves,
  transitive and platform-conditional packages included, and not only the packages a change touches.
  — *verified by:* `uv audit --locked --preview-features audit`
  A run passes only when it exits 0 and prints that it found no known vulnerabilities. Any other
  outcome is not a pass: an advisory reported, a non-zero exit, or a run that could not reach the
  advisory data. `--locked` makes a missing or out-of-date `uv.lock` stop the run with an error
  instead of rewriting the lock (`uv help audit`, `--locked`: "If the lockfile is missing or needs to
  be updated, uv will exit with an error"). The run needs the network to reach the advisory data
  (RN-2) *(traces to: ADR-0001 § Decision)*
- **Audit owner:** the Senior Engineer seat, which runs QC-1's audit and answers what it reports.

## 3. Authentication & access control

Not stated in this revision.

## 4. Privacy, data retention & compliance

Not stated in this revision.

## 5. Performance & capacity

Not stated in this revision.

## 6. Availability & reliability

Not stated in this revision.

## 7. Observability & monitoring

Not stated in this revision.

## 8. Operational constraints

Not stated in this revision. This section makes no decision about the environment the tools suite
runs in.

## 9. Test strategy

Not stated in this revision.

## 10. Verification map

The one row below projects QC-1. Where the row and QC-1 disagree, QC-1 is right.

| QC | Check | Command / layer | Runs over | Gated at |
|---|---|---|---|---|
| QC-1 | advisory audit of `uv.lock` | the command QC-1 names, in § 2 | the tree: every package `uv.lock` resolves | `development-security` |

---

## NFDR Review Notes

- **RN-1:** This revision states QC-1 and nothing else — *because* it was written to give `uv.lock`
  an owned audit, and the PM's change request of 2026-10-28 asked for one audit command and one owner.
  A full NFDR for the tools product is the Principal Architect's to write, with `product-architecture`.
  *(re: QC-1; § 1 to § 10)*
- **RN-2:** QC-1's command is uv's own audit, so the audit adds no dependency and no file to the
  repository — *because* the Architect chose it on 2026-10-28 over installing an audit tool into the
  repository's dependencies. Measured that day with uv 0.11.14 in a fresh clone of the repository, the
  command exited 0 and printed "Resolved 9 packages" and "Found no known vulnerabilities and no adverse
  project statuses in 8 packages". `git status --short` in the clone printed nothing afterwards. The
  ninth entry in `uv.lock` is the repository's own project, which comes from no package registry. The
  eight audited packages include colorama, which `uv.lock` resolves only on Windows, so the audit
  covers a platform-conditional package. `--preview-features audit` is in the command because uv
  0.11.14 marks the audit as experimental and warns without the flag. On the same day, a run with no
  network access exited 2 and reported the advisory data unavailable. That run had failed, and it was
  not a result. uv documents the audit at <https://docs.astral.sh/uv/reference/cli/#uv-audit>.
  *(re: QC-1)*
- **RN-3:** The audit's owner is the Senior Engineer seat — *because* that seat runs QC-1's audit
  wherever it runs: `development-security` on every change, and `dependency-repair` when the chain
  repairs a red suite. Each skill runs only in Senior Engineer posture. The Product Owner's choice,
  2026-10-28. *(re: QC-1)*
- **RN-4:** § 1.2 says outright that it fixes no import graph — *because* a tech-lead plan treats
  this document's § 1.2 as binding whenever the document exists
  (`core/prompts/tech_lead_create_tl_instruction.md`: "the module set and the import graph
  (`nfdr.md § 1.2`) below are binding"). § 8 makes no environment decision because the suite gate
  reads one from this document's § 8 (`core/tools/gate_suite.py` § `read_current_decision`). This
  revision leaves the gate's choice as it was. *(re: § 1.2; § 8)*
- **RN-5:** § 2 names no advisory exception record and no exception window. With none named, the
  security step uses its own default (`core/prompts/senior_engineer_repair_dependencies.md`
  § *The exception record*). *(re: QC-1)*
