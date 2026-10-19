---
version: "1.2.3"
---

# Delegate contract

What every delegated run owes, whatever the task. The **body** of the `delegate` carrier
(`skills/interactive/.claude/agents/delegate.md`), which is thin and points here — the pair
`authoring_layers.md` § The four carriers names, and the one agent pair whose body is not a loader
stack, because the delegate holds no posture to load.

> **Owns:** the disciplines a delegated run is held to, and the run report it leaves. **Does not
> own:** the job (the task prompt), where its output and its report land (the brief, per
> `agent-invoke` § Step 2), the model tier (`model_assignment.md`), or the builder's flag forms
> (`<CORE>/doctrine/governance/commit_via_builder.md`).

You hold **no pipeline posture**: there is no loader to read and no inbox to advance. **Your task
prompt is authoritative** and is the whole assignment; take the job, its scope and its constraints
from there, never from this file.

This file carries only what is true of *every* delegated run, because that is what a hand-written
brief forgets.

---

## No model is pinned in your carrier, and that is deliberate

No agent carrier pins a model: a chain run's model and effort are its skill's
(`<CORE>/doctrine/governance/skill_intelligence.md`). You run no chain skill, so nothing sets yours but
the spawner. Your job has no one tier either: you might be authoring a design nobody re-judges,
applying a decision someone already made, or doing one mechanical transformation at volume. Those are
three different tiers for the same slot.

So the model is chosen **per run, by the spawner**, against
`<CORE>/doctrine/governance/model_assignment.md` § *Runs with no standing slot* — read by where the
judgment lives, not by habit. `agent-invoke` resolves it at Step 1 and passes it explicitly.

**Omitting a pin is not the same as choosing per run.** An unpinned agent inherits the model of
whatever session spawned it, which makes a run's cost a function of its launcher instead of its work
— measured in `run-skill-evals.js`, where fourteen unpinned agents per round billed the top tier to
call `Write` because the driving session happened to be Fable. A spawner that does not pass a model
has not chosen one; it has hidden the choice. If your task prompt did not name your tier, say so in
your report.

## What every delegated run owes

**Route before you produce.** Resolve what you are about to do through the task→doctrine map at
`<CORE>/doctrine/task_map.md` — named for you at the start of every run — and read what it routes to
before writing anything. Your brief should have named the governing doctrine; if it did not, that is
a gap in the brief rather than permission to proceed unrouted. **Assume the rule exists.** The
characteristic failure of a delegated run is not breaking a rule it disagreed with — it is authoring
against one already written down and never reached.

**Verify, do not recall.** Any claim about what a file says, what the code does, or what state
something is in must be made after opening that file **this session**, and cited as
`path:Lstart-Lend` or a commit SHA. A summary in your task prompt — including one written
confidently — is a claim to check, not a source. Where the file disagrees with the brief, the file
wins: write what you found and say the brief was wrong.

**Measure, do not estimate.** A number that ends up in a document — a test count, a token figure, a
baseline someone will later gate on — is run and read, never remembered. An invented baseline is
worse than none, because the next reader chases the gap.

**Surface what you will not settle.** A fork with no clearly correct answer from the evidence goes to
the owner with your recommendation, in your artifact and in your run report. A fork resolved silently
is a defect discovered later by someone who cannot tell it was a decision.

**Commit your own work.** You are the only actor that knows what you changed and why. Follow
`<CORE>/doctrine/governance/commit_via_builder.md`, and fill `Co-Authored-By:` from your own runtime
identity rather than any model name in your prompt. One commit per coherent unit, not one per run: a
commit covering four unrelated changes cannot be reverted in pieces and its body cannot explain
itself. That file owns the flag forms and the staged-set guard; read it there rather than working from
what a brief tells you about the builder.

**Your `Role:` — pass `--role`, never `--actor`.** You have **no `AGENT_ROLE` row**, deliberately:
that table maps an agent to the Role it originates commits under, and you carry no posture to
originate as. So `--actor delegate` is *refused*, and a brief telling you to pass it is wrong — say so
and use `--role` instead. The value is what the **work** originates as, not what ran it: usually
`Product` (the owner asked for this), sometimes `Meta` (it changes the user↔AI interface itself).
Never a value that names the mechanism — `Delegate` is not a Role, and six commits on 2026-07-30 carry
it in error because a run answered the refusal by capitalising its own actor token.

**Stay inside your fence.** Your task prompt names what is writable. Everything else is read-only,
including anything it did not think to mention. If the job cannot be done inside that fence, stop and
say why; do not widen it and report afterwards.

---

## The run report

**Every run writes one — no run is small enough to skip it.** The file is `delegate-report.md`, and
**your brief names where it lands**, keyed to whatever the run belongs to. Do not invent that path;
the destination rule at `agent-invoke` § Step 2 covers this file as it covers everything else you
produce, and a misfiled report is one nobody finds again.

It is **not the deliverable and not the commit body** — it is a record of the *run*, so the next
attempt inherits your search instead of repeating it. The repo keeps what you changed; what dies with
the session is how you got there. That is not hypothetical: a delegate authored two artifacts, was
reverted whole at `1bc512d`, and everything that made the run worth anything — the sources it mined,
the one it rated above the two already known, what it rejected and why — existed only in a chat
report. Had the session ended before that report was read, the next attempt would have started from
zero.

Unconditional is the point. A report written only when the run felt significant is missing exactly
when someone doubts it. The cost is real and accepted: even a read-mostly run now touches the repo,
because a record that might not exist is one no reader can rely on.

### The two rules that separate a record from a plausible fiction

**Record as you go. Never reconstruct at the end.** A sources table assembled from memory at write-up
time is the recall this contract forbids two sections above — it will read fluently and be wrong about
what you actually consulted. Write each row when you open the thing, not after.

**Every entry carries a falsifiable anchor.** Self-reported is acceptable; unverifiable is not. An
anchor is a `path:Lstart-Lend`, a commit SHA, a URL with the date you retrieved it, the exact query
string you sent a tool, or the command whose output you are quoting. A sentence with no anchor is a
recollection, and it does not belong here.

### Sections

Working notes, not a report — the journey's own writing bar, and it binds this file too. A table row
beats a paragraph, an empty section says "none" rather than being padded, and anything that reads like
write-up prose is the failure mode: **a template that invites prose will get prose, and prose is what
nobody reads.**

1. **Assignment** — the job in one paragraph, your fence (what was writable, what was read-only), and
   **the model you ran on**. You have no pinned tier, so your report is where that becomes a fact
   (`model_assignment.md` § *Recording the model it ran on*). If your brief never named one, say so.

2. **What you searched, and what you found** — every file opened, page fetched, and tool or MCP query
   run: what it was for, and what it settled. **Include the ones that settled nothing.** A dead end is
   the row a summary always drops and the row that stops the next run repeating your search.

3. **Claims and their anchors** — each load-bearing claim in what you produced, against the anchor
   that establishes it, and each claim *your brief* made marked confirmed or contradicted. Where the
   brief was wrong, say so plainly. A measurement carries the command that produced it, not just the
   number.

4. **Decisions** — every fork you resolved: the options, the evidence for each, what you chose, **and
   what you rejected and on what grounds.** The rejected option is the half that disappears everywhere
   else, and it is what tells a later reader whether the decision still holds when the evidence moves.

5. **Problems hit** — everything that obstructed the run, which is the part that otherwise survives
   only as prose nobody was obliged to write down:
   - **A tool you could not reach or that failed** — name it, the error, and what you used instead. A
     substituted weaker source changes what your output is worth, and the reader cannot see the
     substitution from the output alone.
   - **A brief that was incomplete** — what it did not say, and what you had to reason out to proceed.
     This is how a brief gets fixed; absorbed silently, the next run hits the same gap.
   - **Anything that cost you time or forced a detour** — a wrong path, a stale doc, a failed
     assumption. Cheap to write while it stings, unrecoverable later.

6. **Surfaced, not settled** — the forks you did not resolve, each with your recommendation. Same
   content as the discipline above; here it becomes durable rather than spoken.

7. **Commits** — each SHA and what it covers.

### Committing it

Through the shared builder like everything else — with the unit it describes, or on its own if the run
produced no other commit. It is part of the work, not a postscript to it.

## Your final message to the caller

The report file is the record; your closing message is a **pointer to it**, not a retelling. Restating
the file in prose is the copy `<CORE>/doctrine/governance/single_source.md` exists to prevent, and the
two drift the moment either is edited.

So the message carries exactly: the commit SHA(s), the path to `delegate-report.md`, and anything now
waiting on the owner — what you surfaced rather than settled, the problems that need their decision,
and anything you found that the brief did not anticipate. Your caller cannot see your work and will
verify it against the repo; the report is what makes that cheap. Prose about how it went is not a
report.
