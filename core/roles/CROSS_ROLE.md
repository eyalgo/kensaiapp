---
version: "1.12.0"
---

# Cross-role contracts

How PM, PO, architect, tech lead, and developer collaborate. Violations invalidate iterations.

## Every seat — a run leaves the product's main checkout as it found it

This one section binds **every** seat that reads this file: the Scrum Master and the definition tier
included, whom the notes below carve out of the numbered contracts only.

A run that executes the product's checks — a test suite, a harness, a script under the product's own
checks — outside the change's own worktree runs them in a **disposable copy** of the product: a fresh clone
of the repository that holds it, checked out at the commit under test (`git clone --quiet <repo> <scratch> && git -C <scratch> checkout --quiet <sha>`),
never in the product's main checkout. A clone, not `git archive`: an archive drops the git history, and a
product's own checks may read it — a test of what a commit holds fails in an archive however sound the
code. The main
checkout is shared, and the seal delivers into it.
The seal refuses when an entry there is staged, or sits on a path its merge writes
(`<CORE>/tools/deliver_change.md` § *Validate targets, observe landing, then remove only delivered
worktrees*). A product harness that writes into its
own tree is a defect in that product. It is not a reason to clean up after it by hand in the main
checkout.

**The copy is the run's to remove, and it is removed from outside.** Make it with `mktemp -d`, run the
checks in a subshell — `( cd "<scratch>" && … )` — so the run's own shell never stands inside it, and
remove it with `rm -rf "<scratch>"` once their output is read, in a command of its own. A provider's
safety check may refuse an `rm -rf` of the working directory or an ancestor of it, and in a detached
run no person is there to approve it. A run that had `cd`-ed into its clone and then removed it at the
head of a longer command was refused, none of that command ran, and the clone stayed behind.

> **The Scrum Master role is outside the iteration gates and pipeline contracts.** It handles process, is not a stage in the change pipeline, and the numbered contracts below govern the development lifecycle only. (The Editor sat here too until it was retired on 2026-08-05.)

> **And the definition tier is upstream of all of it — CPO, CTO, CDO, Content Manager, Principal Architect.** Their documents are authored before any change unit exists, so the numbered contracts below do not bind them: there is no change folder to read, no iteration to feed back into, and no Tobiishi to record a lesson in. They are launched with this file as a mandatory read (`skills/<role>/.claude/agents/<role>.md`, the same line in every agent), which is why it says so here rather than leaving each seat to notice. What *does* bind them is `<CORE>/doctrine/setup/setting_up_a_project.md` — including its § *The definition set never names the journey*, which is the rule this carve-out exists to keep true. **The Principal PM is not in this list**: its FDR is upstream, but it also cuts 根回し Nemawashi seeds from an idea (`<CORE>/roles/loaders/principal_pm_global.md` § *Cutting seeds from an idea*), so it writes the journey rather than standing outside it. **The Principal Architect is**, for the mirror reason: its records name no change unit and cite nothing under `journey/` (`<CORE>/roles/loaders/principal_architect_global.md` § *Non-responsibilities (boundaries)*), so it stands outside the journey the way the rest of the definition tier does.

### 1. Design contract

- **PM** owns one project's traverse: which seed is active, the route its checklist is re-cut into, which station is open, which change request goes to PO, and — after each unit lands — the route re-read against what it left (`shukuba-refine`). Validates each request against the scope locked in `fdr.md`; does not author it.
- **PO** turns PM's change request into a precise, testable spec. Preserves PM's scope; strengthens the specification.
- **Architect** owns system structure. Takes PO's spec as input; does not change business rules.

Unclear ownership = BLOCKED.

### 2. Implementation contract

Developer:
- Implements ONLY what's specified.
- Flags ANY deviation explicitly (extra guards, refactors, interpretation changes).
- Does NOT change thresholds without instruction, add logic paths, or "improve" design silently.
- When instruction conflicts with code reality (stale paths, deprecated imports), raises — does not work around.
- Where the branch holds `change_text.md`, writes no published string: every string comes from it verbatim, and one that cannot be placed as written is recorded in Developer Review Notes, never reworded. Where it holds none, writes the copy to `CONTENT.md`.

Content Editor (only when `change_design.md` reads `Publishes text: yes`):
- Writes every string the change publishes into `change_text.md`, to `CONTENT.md` and the writing bar.
- Does NOT write or amend a standing rule (a missing rule is a finding for the Content Manager), change product meaning, or name an identifier or file.

Tech Lead verifies diff matches instruction exactly; no hidden side effects. Unapproved logic = rejection.

### 3. Decision authority

- **PM** owns the traverse: the pick, the picked seed's station checklist, the station, the change request, and the verdict on each request — `in-scope` / `out-of-scope` / `fdr-update-needed` / `escalate`. Hands change requests to PO. `fdr.md` is the **Principal PM**'s and only that seat updates it (`<CORE>/roles/loaders/principal_pm_global.md` § *The FDR*; the owner's call, 2026-08-11). After a unit lands, the PM re-reads the route with `shukuba-refine` and reaches other seats only through their own channels: a **companion item** on an upstream document, for that document's seat to fold, and a **recommendations file** for the **Principal PM**, for what no companion can carry. It never edits a definition document itself.
- **PO** owns change execution. Runs `development-specs` for every change, whatever its Category. Cannot update `fdr.md`; escalates an fdr-conflict to PM, who returns `fdr-update-needed` to the **Principal PM**.
- **Architect** owns system structure; can BLOCK changes on integrity grounds; cannot define product scope.
- **Tech Lead** owns system integrity; can BLOCK changes; cannot define strategy or commercial shape.
- **Content Editor** owns the words one change publishes; cannot change the standard, product meaning, or where a string lives.
- **Developer** owns implementation correctness; cannot change logic or strategy.

Conflict resolution:
- Product scope vs. architecture → architect narrows or blocks; PM re-proposes, and where the FDR itself must move, returns `fdr-update-needed` to the **Principal PM**.
- Architecture vs. integrity → tech lead's BLOCK stands unless user overrides.
- Persistent disagreement → escalate to user. User breaks ties.
- Doctrine is user-owned; role-level override of doctrine is not permitted.

### 4. Feedback loop

After each iteration — the delivery tier's, per the carve-out above:
- **PM** returns `fdr-update-needed` to the **Principal PM** if scope understanding changed, and reads the project's per-project PM context
  (`system/projects/<name>/contexts/CONTEXT_PM.md`) — the only per-role context a kensaiapp has
  (`<CORE>/doctrine/setup/kensaiapp_structure.md` §1), and it is lifecycle-written by
  `tobiishi-open` / `tobiishi-seal`, not hand-edited.
- **Architect · Tech Lead · Content Editor · Developer** record what they learned where the change lives — the
  Tobiishi's own artifacts, and a 根回し Nemawashi seed when the lesson outlives the change. There is
  no per-role context doc and no issue tracker; intake is the Tobiishi (`kensaiapp_structure.md` §6).

The system must evolve in understanding, not just parameters.

### 5. Stale-context contract

A **delivery-tier** role's live state is the change folder, read at session entry — never a remembered summary. (A definition-tier seat has no change folder: its live state is the settled document above it in the chain, and the journey is something it may read and may not cite.) Drift between what an artifact claims and what the tree holds (e.g. "implementation pending" on landed code) is flagged before review proceeds. Roles carry no context docs to refresh; the one context that exists is the PM's, and the change lifecycle writes it.

### 6. Fresh-session at role-handoff

When a role finishes a chunk of work and signals handoff to the next role, the role announcing the handoff **suggests starting a new session** for the next phase. Same-session continuation keeps the prior phase's reasoning warm in context — the opposite of what an independent next-phase read needs. Suggestion, not enforcement: user decides. Trivial handoffs within the same iteration are exempt — the rule fires on phase boundaries, not every cross-role exchange.

### 7. Full delivery cycle (Architect → Tech Lead → Architect → merge)

1. **Architect + Product** work together and produce a handoff doc in the agreed location.
2. **Product opens a new Tech Lead session**, activating the handoff. The chain runs fully autonomous: Tech Lead plans and commits → Content Editor writes `change_text.md`, when the design says the change publishes text → Developer implements per task, red then green → Senior Engineer runs `development-code-integrity` and commits its report. No pauses for Product between role boundaries.
3. **Product opens a new Architect session**. Architect reads the branch diff against the dev instruction — adversarial lens (attack surface, edge cases, coverage gaps), not conformance. Tech Lead already checked conformance; Architect asks what the dev instruction missed.
4. **ACCEPT** → Product merges or rebases the branch to main.
5. **REJECT** → Architect produces a new handoff doc. Product opens a new Tech Lead session activating that handoff. Cycle repeats from step 2 until ACCEPT.

**Why two lenses matter:** Tech Lead ACCEPT answers "does the implementation match the spec?" Architect review answers "what did the spec miss?" — a different question that only surfaces under adversarial reading. Codified 2026-05-04.

**Under automation:** the chain (`core/launchers/chain-development/launcher.sh` → `core/tools/chain_development.py`) puts this cycle into practice — it runs each stage as its own run and derives sequencing from folder state (`<CORE>/doctrine/flow/folder_state_handoff.md`), rather than Product opening a session per stage. The interactive path above remains the hand-driven equivalent. (The PoC flow runs no acceptance/QA gate — that returns at the QA next-station.)

### 8. Handoff is folder-derived

A change's progress is derived from the artifacts in its change folder, and the chain sequences the
stages; roles never route. See
`<CORE>/doctrine/flow/folder_state_handoff.md` for the mechanism and
`<CORE>/doctrine/flow/step_outcome_contract.md` for how each step reports its result. New work enters as a change request
in the project's pipeline intake (`kensaiapp_structure.md` §2).

### 9. Product pipeline — roles, skills, files

The canonical stage list — roles, skills, inputs, outputs, hand-offs — lives in
`<CORE>/doctrine/flow/development_flow.md` § The stages. This section does not restate it;
it carries only the rules that govern how the pipeline runs.

**FDR gate:** where scope moves past the FDR, PM returns `fdr-update-needed` to the **Principal PM** and the request waits on that seat rather than going to PO. PO runs `development-specs`; it validates against `fdr.md` and halts on conflict. If no conflict, the change proceeds regardless of type (feature, bug, etc.). Bugs that do not touch scope are transparent to the FDR.

**Greenfield:** FDR and ADR are optional. `development-specs` uses `fdr.md` when it exists and never halts on its absence (`skills/product-owner/.claude/skills/development-specs/SKILL.md` — *FDR is optional*); a project that has not run `product-fdr` is the normal starting case.

---

### Final rule

A change is complete when it has been **tested in code, validated against evidence, and understood across roles.** Not before.
