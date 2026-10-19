# product-architecture eval fixtures

Read-only inputs the eval prompts (`../evals.json`) point at. A `skill-evals` run **reads** these;
`stage_fixtures.py` gives **both** arms their own private copy under the gitignored `workspace/` tree
(`stage_fixtures.py:202-204`), so the tracked fixtures stay clean and nothing needs restoring after a
run.

**All eval annotations live here, never inside an ingested file.** The grader and the executor read
the fixture files *whole* — a comment inside `SRS.md` / `SDD.md` / `fdr.md` / `adr/*.md` / `nfdr.md` /
`architecture_open_issues.md` that revealed the expected behaviour would let a blind baseline pass on
the instruction rather than on the skill. So the fixtures carry only product content (plus a benign
path-resolution note on each `project.md`'s `Product path:` line, which staging strips before the run
sees it); the "what each case exercises" notes are all in this file. This file itself is dropped from
the staged copy — `stage_fixtures.py`'s `ignore_annotations` excludes the fixture root's `README.md`.

Paths are **repo-relative** (publish-safe — no machine-absolute path). `product-architecture` reads a
relative `Product path:` as an in-repo product and resolves `<Product path>/docs/adr/`,
`<Product path>/docs/nfdr.md` and `<Product path>/docs/architecture_open_issues.md` under it.

## The full-input fixture shape

`product-architecture` reads three upstream documents, not one. Each product's `docs/` replicates the
state the foundation step actually starts from:

- `docs/SRS.md` — **`Status: Settled`** (the CTO's, closed).
- `docs/SDD.md` — **`Status: Settled`** (the three-seat conversation's, closed).
- `docs/fdr.md` — **`Status: Draft`**, deliberately. See *The Draft FDR* below.
- `docs/trail/srs/cycle-1.md` — the answered SRS companion, retired whole, which is where the owner's
  already-authorized answers live (the prompt's authority order puts them above every document).

Beside `docs/`, each fixture carries **`agari.md`** — the declared terminus — and **`project.md`**,
the card whose `Product path:` resolves every output. In a real instance the Agari and the card sit in
the project folder (`system/projects/<name>/`) while the product lives elsewhere; the fixtures collapse
the two, exactly as `product-srs`'s fixtures do.

**No `system/projects/<name>/doctrine/` folder is shipped.** That absence is load-bearing for case 3:
with no project doctrine pointing at an engineering floor, the missing observability requirement has
no doctrine default to be answered from, which is what puts it on the prompt's *route it* branch
rather than its *apply and cite it* branch.

## The one product, and what was built into it

**sealbox** — a self-hosted document-signing service a law firm installs on its own host. One product,
shaped so the stack's signature behaviours have something real to bite:

- **Two § 2 shape tables in the SDD** (runtime shape; where document bytes live), each with
  alternatives and a *right when / wrong when / taken?* column, plus **three § 9 trade-offs** and
  **four SDD Review Notes** — the three surfaces the prompt says a decision is found on. There is
  enough here for several records that clear all three significance gates, which is what makes
  *many files, not one* gradeable.
- **A decision visible in the design and argued nowhere.** The PDF renderer runs **inside the request
  process** — stated in the SDD's § 3 parts table and again in § 4 CN-3, and weighed in no § 2 row,
  no `TO-n`, and no SDD Review Note. § 2's runtime-shape table decides how many *processes* ship and
  rejects a three-service split; it never reaches whether flattening runs inline or in a child process
  the same binary forks, which is where the crash-and-memory isolation trade-off actually sits. That
  makes it hard to reverse, surprising, and a real trade-off — so it earns a record, and one whose
  `## Traces to` must say it is **reconstructed**. Case 2's flagship assertion.
- **A real security requirement** (NFR-3 at-rest encryption; NFR-4 single-use 72-hour links; NFR-5
  link secrecy as the whole boundary) and **a real performance requirement** (NFR-1 flatten under 2 s
  at p95; NFR-2 signer page under 1.5 s), so the universal sections have upstream facts to trace to.
- **No observability requirement at all.** SRS § 4 carries 4.1, 4.3 and 4.4 and stops — there is no
  4.5. Nothing upstream states what must be visible when sealbox fails, so the run cannot trace an
  entry to anything and must not invent one. Case 3's `observability-gap-routed-not-invented`.
- **Constraints that make one conditional section genuinely inapplicable.** C-2 puts deployment and
  operation with the customer and commits no uptime target; SDD RN-3 fixes no runtime topology beyond
  the single process; the FDR's OOS-2 excludes clustering and failover. So NFDR § 5 has nothing to
  bind — and must be **declared not applicable with its reason**, not silently dropped. Case 3's
  `availability-declared-not-applicable-with-reason`.
- **A gap the run can draft into.** DR-2 fixes no default retention term, and the SRS trail's owner
  answer explicitly asks whoever writes the constraint set to propose one for the reference
  deployment. That is a *choice to confirm* rather than an *open issue* — which is why the companion
  is owed both of its slot labels, and it is the item the re-entry fixture's owner overrides.

## The Draft FDR

`docs/fdr.md` reads `Status: Draft` in both fixtures, on purpose. It is a live behaviour under test,
not an oversight: the owner's ruling of 2026-08-30 is that an unsettled input is **read, derived from,
and its status recorded in the trace** — never halted on, and never handed back as a request to settle
the upstream document first. Case 3's `draft-fdr-read-and-its-status-recorded` grades exactly that,
and the FDR carries its own reason for being Draft in its Review Note RN-2 (two behaviours still with
the CPO), so the state reads as a real document mid-flight rather than as a fixture trick.

## `sealbox/` — cases 1, 2, 3 (fresh create)

The full-input shape and **no records yet**: no `docs/adr/`, no `docs/nfdr.md`, no companion. The run
authors the first log and the first constraint set.

- **Case 1 `fresh-log-index-and-constraint-set`** — the shape of the output. Records land as separate
  `docs/adr/NNNN-slug.md` files plus a `docs/adr/README.md` index that lists every one of them;
  `## Alternatives ruled out` is present in **every** record; every constraint carries all three of a
  `QC-n` id, a `verified by:` tail and an inline `(traces to: …)` tag; and § 9's verification map
  projects the machine-checkable entries.
- **Case 2 `silent-decision-and-record-provenance`** — the reconstructed record (the in-process
  renderer), every `## Traces to` naming an openable locator, and the `## Binds` pointer that keeps
  the log and the constraint set navigable in both directions without copying content across.
- **Case 3 `upstream-silence-routed-and-draft-input-read`** — what the run does when upstream is
  silent: the observability gap routed to the SRS rather than invented, the companion carrying both
  exact slot labels, § 5 declared not applicable with its reason, the Draft FDR read with its status
  recorded, and the constraint set stamped `Draft` because a companion remains.

Three cases on one fixture is deliberate. They grade different behaviours over the same input, and a
second invented product would buy variety in the prose rather than in what is being measured.

## `sealbox-reentry/` — case 4 (loop re-entry)

The same product, carried one cycle further: three **Accepted** records under `docs/adr/` with their
index, a `docs/nfdr.md` at **Version 1 / Status: Draft**, and a `docs/architecture_open_issues.md` the
owner has **answered in every slot** — the observability floor answered (structured JSON to stderr per
event), the drafted 7-year retention default **overridden to 3 years**, and the § 5 not-applicable
declaration **confirmed**.

Every slot is answered, so this run is the close: retire the companion whole to
`docs/trail/architecture/cycle-1.md`, fold the answers in, **remove** the companion, stamp `Settled`,
bump the `Version:` and name the authorization in a review note — all without rewriting a single
accepted record.

- The fixture's companion is **committed** in this repo and the run's private copy lands under the
  gitignored `workspace/` tree, so the skill's first-closing-touch gate reads it as clean and the
  close happens in one run. The **dirty**-companion path — where the run changes nothing and reports
  CLOSING — has no fixture and is not covered: a staged copy cannot be made to present as a
  tracked-and-modified file.
- **Judge discrimination on the fresh-create cases, not here.** A re-entry case feeds the skill's own
  structure back in as input, so a strong baseline simply continues it. Case 4 is kept as a
  with-skill reliability guard on the fold/trail/append-only loop, and its two most baseline-reachable
  assertions (`owner-answers-folded`, `accepted-records-not-rewritten`) say so in their own
  descriptions.
- The fixture ships `docs/trail/srs/cycle-1.md`, which makes the trail *pattern* visible in the input.
  That weakens `answered-companion-retired-whole-to-trail` as evidence of lift, and it is kept anyway:
  a real product at this point in its life has upstream trails, and a fixture that hid them would be
  testing a state the skill never meets.
- **No cycle-numbering rule is graded.** There is no `docs/trail/architecture/` in the fixture, so
  `cycle-1` is the unconditional answer and a hardcoded value is indistinguishable from correct
  max-based numbering. Testing that rule needs its own pre-seeded fixture and case.

## No fixture — case 5 (posture halt)

Case 5's prompt is a bare, non-Principal-Architect request. The skill halts on the posture check and
authors nothing, so it needs no fixture — the absence of every product artifact is the signal.

## The executor's model

`evals.json` pins `{"executor": {"model": "fable"}}` — the skill's **production slot**.
`<CORE>/doctrine/governance/model_assignment.md:32` gives the Principal Architect row as Fable, and its
§ *Eval runs* requires the executor be chosen explicitly rather than inherited, because a run whose
models are unknown cannot be compared with another run. Both arms get the same pin: the measured delta
must isolate the skill.

The pin is a **model**, not an agent slot. Pinning `agentType: 'principal-architect'` would inject the
role's loader stack ahead of the task — which legitimately restates the companion's shape, the
append-only rule and the done signal, i.e. the very things being graded — and would also satisfy, on
both arms, the posture gate case 5 exists to withhold.
