---
version: "1.5.0"
---
<!-- The version above is template-file metadata; it is not copied into the authored skill. Nor is
     any comment block in this file.

     WHAT THIS STAMPS: one `.claude/skills/<skill-name>/SKILL.md` — the ORCHESTRATOR half of a
     stack. What a skill may contain at all, and what belongs in its prompt instead, is
     `<CORE>/doctrine/setup/authoring_layers.md` § The carriers, whose *The skill and its prompt*
     paragraph draws the line and names the tell.
     This file carries the SHAPE those rules produce, measured off the skills that already follow
     them; it does not restate the rules.

     MODEL-FACING (`<CORE>/templates/README.md` § The rule — a template's format follows its
     consumer): a person or an agent reads this file and authors a fresh SKILL.md, so everything
     here may explain itself and none of it survives into the result.

     TOKENS: <skill-name> hyphenated, matching the folder name · <Role Title> the human name of the
     posture · <role> the session prefix · <role_file> underscored, for filenames · <DOC> the
     artifact the skill authors.

     THE SHAPE BELOW WAS MEASURED, NOT PROPOSED. Six skills on disk were read whole and their
     headings extracted with
         grep -n '^#\{1,3\} ' .claude/skills/<name>/SKILL.md
     for product-prd, product-srs, product-uxd, product-design, product-content and
     kensaiapp-writing-bar (2026-08-19). Where all six agree, this template states the element flat.
     Where they diverge, § THE OPEN CHOICES at the foot names the divergence, the count, and who
     does what — because a template that picks one quietly turns an open question into a house fact
     the next author inherits without knowing it was ever a question.

     THE GROUNDING RULE — the one check this template exists to force.
     Every sentence the authored skill states as REQUIRED — "must", "never", "always", "halt",
     "doctrinally required" — resolves one of exactly two ways, and the author writes which:
       (a) IT HAS AN OWNER. Name the file and the section that states it, open that file in the
           same session, and confirm the named section carries THE CLAIM — not the topic. A section
           that bans X is not a section that requires Y as the remedy for X, even when Y is the
           obvious remedy.
       (b) IT IS THIS FILE'S OWN. Say so in the sentence. A rule an artifact holds on its own
           authority is legitimate and cheap to argue with later; a rule wearing a citation that
           does not carry it is neither.
     THE FAILURE THIS FORBIDS, worked: `<CORE>/templates/role-templates/global_loader_template.md`
     calls part 5 of the improve clause "doctrinally required" and cites `<CORE>/roles/CROSS_ROLE.md`
     § 2. That section bans silently "improving" and is addressed to the Developer by name; it states
     no logging obligation and no obligation on any other seat. Measured with
         /usr/bin/grep -icE '\blog(s|ged|ging)?\b|Review Notes' <CORE>/roles/CROSS_ROLE.md   -> 0
     (the same grep without word boundaries returns 3, and all three are the word `logic`, so a
     re-check with a loose pattern concludes the citation holds). Filed as a seed under the owning
     project's `system/projects/<name>/journey/nemawashi/` in the instance where it was found.
     The clause is probably right; nothing on disk said so, and it went through a full authoring
     and two blind audits unnoticed, because checking it meant opening a file no reader had another
     reason to open.
     THE NEAR MISS TO AVOID WHILE FIXING ONE: repointing at a different adjacent file. That is what
     produced the finding in the first place, and `<CORE>/doctrine/task_map.md:33-35` rates it worse
     than either an empty lookup or an unresolvable name: "a plausible neighbour reads as answered, so
     the session stops looking."
     This rule is stated on THIS TEMPLATE'S OWN AUTHORITY — option (b). No doctrine file states it
     today; the seed above is a finding, not an owner. If one is written, cite it here and delete
     this paragraph.

     REMOVE ANY SECTION THE SKILL GENUINELY HAS NO CONTENT FOR — an empty heading asserts nothing.
     But the six-of-six elements below are the floor: a skill missing one is missing something every
     skill in this house was found to need, and the author owes a reason rather than an omission. -->

---
name: <skill-name>
description: <Role Title>-posture skill that authors <what> — <what that artifact is, in one clause>. Requires <Role Title> posture (halts if invoked outside a <role> session or the <role> subagent). Non-interactive by design — <how it drafts, what it surfaces to the companion, what a re-run does>. Use when <the trigger, in the caller's words>. Do not use for <the two or three nearest neighbours, each named with the skill that owns it>.
license: MIT
metadata:
  author: <instance name>
  version: "1.0.0"
  created: "<YYYY-MM-DD>"
  category: <the family this skill belongs to>
  tags: <comma-separated, no colon-space>
  risk: safe
---

<!-- FRONTMATTER — ten keys, this order, no others. Measured identical across all six skills:
         awk '/^---$/{n++; next} n==1' SKILL.md | grep -oE '^ *[a-z_]+:'
     returns the same ten names in the same order for every one of them (2026-09-06, re-measured
     after `updated:` was deleted instance-wide — it drifted stale on 26 of the 31 skills carrying
     it and was read by nothing, so the owner ruled it removed rather than maintained).

     NO COLON-SPACE IN ANY VALUE. A `: ` inside `description:` or `tags:` parses as a nested
     mapping and breaks the frontmatter. Measured 0 occurrences across all six descriptions; keep
     it that way, and verify with a real YAML parser rather than by eye.

     THE `version:` IS THE KAIZEN LAYER'S, NOT `versioning.md`'s.
     `<CORE>/doctrine/governance/versioning.md` § Out of scope hands a skill's marker and its bumps
     to `<CORE>/doctrine/kaizen/skills.md` § The version's three digits, which reads the same three
     digits against a skill: patch = wording a run's behaviour does not turn on; minor = a step, a
     refusal, a gate or an output shape added or changed; major = a rewrite, or a mandated rule
     removed or inverted. New skills start at 1.0.0.

     THE DESCRIPTION IS READ BEFORE ANY OF THE BODY, by a model deciding whether to trigger, and
     that reader then stops (`<CORE>/doctrine/setup/authoring_layers.md` § Why a teaching carrier
     fails harder than a copy elsewhere). All six carry, in this order: the posture, the artifact,
     the halt, the non-interactive contract, one `Use when`, one `Do not use for`. The
     `Do not use for` list is what stops a neighbouring skill's work landing here; name the owning
     skill beside each exclusion, not just the excluded thing. -->

# <skill-name>

## Purpose

<What the skill authors, in one sentence, naming the artifact and what it is the source of truth
for. Then where it sits in whatever sequence it belongs to — by pointer, never by restating the
sequence.>

<!-- THE CARRIER DECLARATION — required, and it is why this section exists rather than opening at
     Posture. `<CORE>/doctrine/setup/authoring_layers.md` § The carriers requires that a carrier
     point at exactly one body and that the pair be DECLARED ON BOTH SIDES, never inferred. So this
     paragraph names the prompt, and the prompt's own opening names this skill back. Model it on
     `skills/cpo/.claude/skills/product-prd/SKILL.md:25-29` with `<CORE>/../skills/cpo/.claude/skills/product-prd/prompts/rich.md:12-18`, which
     that doctrine cites as the declared pair.

     The split it declares: SKILL = orchestrator (posture, the file loop, path resolution, staging,
     the commit) · PROMPT = thinking (the diagnostic or completeness lens, the contracts, the
     principles) · TEMPLATE = section shape. The tell that a sentence has drifted into the wrong
     one is a numbered principle or a quality bar appearing in a SKILL.md.

     NOT EVERY SKILL EARNS A PROMPT — the trigger is the change-rate argument in that doctrine, not
     size. A skill with no prompt says so here and names what it applies instead. -->

This file is the **orchestrator**: posture, the file loop, path resolution, staging and the commit.
**How to author** — <name the lenses and rules by their section names> — is the authoring prompt
**`prompts/rich.md`**, beside this file, applied at Step 2; a rule named below without
its content lives there. The <DOC>'s **section shape** is the template
**`<CORE>/templates/<scope>-templates/<x>_template.md`**; the companion's shape is
**`<x>_open_issues_template.md`** beside it. None of them is restated here.

**Non-interactive.** <One paragraph: the run never blocks on the owner, it derives best-effort,
writes what it cannot settle into a companion the owner answers on their own time, and a re-run
folds those answers in — which is what lets it run headless as well as interactively.>

---

## Posture

**<Role Title> role required.** If invoked outside <Role Title> posture (neither a `<role>:` session
nor the `<role>` subagent), stop and say: *"<skill-name> requires <Role Title> posture. Switch? (Open
a session with the `<role>:` prefix, or run the `<role>` subagent.)"* Do not shed the role.

<!-- SIX OF SIX carry this refusal as a quoted string, so the caller is told the same thing whichever
     skill they mis-invoked. Quote it; do not paraphrase it.

     WHERE THE SEAT ENDS is the loader's, not this file's. Five of the six add one sentence naming
     the nearest confusable seat and POINTING at the loader stack for the boundary — never
     restating it. If your role has a confusable, add that sentence; if it does not, the seat has
     probably not been thought through. -->

---

## The files and the loop

<!-- SIX OF SIX carry a three-row table, and the three rows are always the same three kinds: the
     document, the transient companion, the permanent trail. The companion's absence is the done
     signal in all six — state it in the table, not only in the workflow.

     THE THIRD COLUMN IS FIVE OF SIX. product-prd's table is `| File | What it is |` and carries the
     lifecycle in prose instead; the other five carry a `Lifecycle` column. The column is the better
     half — permanent, transient and permanent is the whole reason the three rows are three rows,
     and a reader who misses it has missed the loop. -->

| File | What it is | Lifecycle |
|---|---|---|
| `<path>/<DOC>.md` | The <DOC> — best-effort complete on every run. | Permanent; one document, revised and versioned in place, never forked. |
| `<path>/<DOC>_open_issues.md` | The companion, holding what the run could not settle, in the buckets `<x>_open_issues_template.md` defines. | Transient. **Its absence is the done signal.** |
| `<path>/trail/<doc>/cycle-<N>.md` | Each answered companion, retired whole. | Permanent. |

**Cycle numbering:** `N` is one higher than the **highest** `cycle-<N>.md` already in `trail/<doc>/` —
list the directory and take the max, so a removed or renamed cycle cannot make you collide with an
existing one. The first is `cycle-1.md`; create `trail/<doc>/` if it isn't there. Never overwrite an
existing cycle.

**The loop, repeated until clean:**

1. The run authors/updates the <DOC> and writes the companion with what it could not settle.
2. The **owner answers inline** — filling the companion's answer slots, whose names and shape are
   the companion template's — and re-runs the skill.
3. The run **copies the answered companion whole to the next trail cycle**, folds the answers in,
   and rewrites the companion with only what is still unresolved.
4. When the answers resolve everything, the run is the close: it folds, copies to the trail, and
   **removes** the companion instead of rewriting it — through the builder's `--rm`, never a
   hand-`rm`. **No companion = the <DOC> is done.** The close has a precondition the ordinary cycle
   does not: the owner's answers must already be committed. Re-entry is inline answers, so the first
   closing touch normally finds them uncommitted — and then it **changes nothing at all**: no fold,
   no trail copy, no rewrite, no commit. It reports the state and asks for that commit; the re-run
   after it is the close. That stop is a report with an ask, not a live interview.

<!-- THE TWO-TOUCH CLOSE is six of six and is not optional decoration: `git rm` refuses a file with
     local modifications, and the owner's words are not the run's to commit. A loop written without
     it will strand every close.

     WHY THE TRAIL EXISTS is six of six too, stated as a paragraph under the loop: folding rewrites
     the companion and the close removes it, so without the trail the owner's answers are destroyed
     twice and their reasoning survives only in git history. Say it; it is the sentence that stops a
     later author "simplifying" the trail away. -->

---

## Inputs and where the files land

<!-- FIVE OF SIX carry this as its own section; product-prd folds the same content into § Purpose
     and § The files and the loop. See § THE OPEN CHOICES.

     LIST THE DIRECTORY, DO NOT NAME THE FILES. Five of six say so explicitly about the folder they
     read from, with the same reason: a list of filenames kept in a skill goes stale the day the
     subject gains a document, and the run would never know what it had missed.

     EACH INPUT SAYS WHETHER ITS ABSENCE HALTS. That is the load-bearing half. In the six on disk
     the primary input's absence halts and everything else's does not — an empty folder is silence,
     a placeholder is a companion item. State it per input; do not leave it to be inferred. -->

- **<The primary input>** — read it in full. Its location is <the skill that wrote it>'s to name;
  resolve the path from that skill, never from a path remembered here. It must exist: if nothing is
  at the resolved path, halt and report.
- **<Each further input>** — <what it carries, and whether its absence halts>.

**Path resolution.** <Where a relative path resolves, where an absolute one does, and what `<repo>`
is. If the skill has no product path to resolve, say so — that is the difference between an
instance-level skill and the product-facing family.>

---

## Workflow

### Step 1 — Read current state

<Read every input above, in order. Then the three things to establish before writing anything: what
already exists, whether a companion sits beside it, and whether that companion is clean in git.>

### Step 2 — Author the <DOC> (no interview)

**Gate first — detect the first closing touch before you write anything.** When a companion existed
at intake, its inline answers would resolve everything unresolved, and the file is uncommitted, this
run is the first closing touch and **writes nothing**: no authoring or fold, no trail copy, no
companion rewrite. Skip the rest of this step and the commit step, and report CLOSING.

<!-- SIX OF SIX open Step 2 with this gate, in this position — before any write, not after. A gate
     placed after the draft has already changed the disk it was meant to protect. -->

<Apply the prompt and the template by name. State that this step restates none of the prompt's
thinking.>

<Set the document's `Status:` from the DONE condition — the companion's absence — never from a tally
of answers. Leave **Locked** alone; ratification is the owner's act. Bump the document's `Version:`
line on any run that changes its content.>

**Consuming an answered companion.** <The three moves, in this order: copy the companion whole to
the next trail cycle *before* the fold rewrites it; fold the answers in; then drop every answered
item.>

**An answered item never survives the drop.** <Where the answer settles the item it is gone; where
it leaves something unsettled the item still drops and the residue re-enters as a fresh item with an
empty slot. The invariant this buys: a filled slot in a surviving companion is always the owner's
writing, never the run's, so a run's own rewrite can never re-fire the detection at the next
intake.>

<!-- FIVE OF SIX carry that pair verbatim in shape; product-prd states the fold in its loop and not
     the drop invariant. See § THE OPEN CHOICES. Without the invariant, a run that rewrites a
     companion can read its own text back as owner answers on the next intake. -->

### Step 3 — Commit through the builder

Commit through the shared builder — read `<CORE>/doctrine/governance/commit_via_builder.md` and supply
its variables. The builder stages, derives `Role:`, and lays the whole trailer block; this step never
hand-writes a `git commit`, spells a trailer, `cd`s into the repo, or resolves the directional
*shape*. What follows is only the values <skill-name> feeds it.

**A run that changes nothing builds no commit — and touches no disk.**

**The stage list — compose it from what this run actually did.** <Every qualifying path in one
`--add`, the removed companion as the one `--rm`. Then the per-path rules: the document always; the
companion as exactly one of add / rm / neither; the trail cycle only when this run consumed an
answered companion.>

**Actor:** `--actor <role> --skill <skill-name>` when running as the `<role>` agent; from an
interactive `<role>:` session with no agent named, `--role "<Role Title>" --skill <skill-name>`
instead.

**The directional** is `<Agari: | Shukuba: | Michi:>` — <which, and why, resolved against
`<CORE>/doctrine/governance/commit_format.md` § Directional trailer, whose rule is that the trailer
follows the commit's SCOPE rather than what kind of thing produced it>.

### Step 4 — Close / report

Report the <DOC>'s path; the commit SHA, or that the run changed nothing and built no commit; on any
run that consumed an answered companion, the **trail cycle path**, so the owner can see their answers
survived without opening the commit; and the **loop status**, exactly one of:

- **DONE** — no companion remains and nothing is unresolved.
- **CLOSING** — the answers resolve everything but the companion is dirty, so this run was the first
  closing touch and changed nothing. The one ask is: commit the companion, then re-run.
- **OPEN** — something is still unanswered. Give a count per bucket, under the bucket names the
  companion **on disk** carries, name where they live, and name the next move.

<Then one closing line: authoring the <DOC> is this skill's whole job. Do not enumerate downstream
steps.>

<!-- ============================ THE OPEN CHOICES ============================
     Divergences measured across the six skills on 2026-08-19 that no doctrine resolves. Each is a
     real choice for a new skill, not a defect to copy or avoid. Delete this block from the authored
     SKILL.md — it belongs to the template.

     1. INPUTS AS ITS OWN SECTION — 5 of 6 have `## Inputs and where the files land`; product-prd
        folds the same content into § Purpose and § The files and the loop and has no such heading.
        Both work. The section is easier to audit against, which is why this template shows it.

     2. AN EXTRA GATE STEP — 5 of 6 run four steps; product-design runs five, inserting
        `### Step 3 — Run the machine gate` between authoring and committing, because its format is
        external and machine-checked. Add one only where a real external check exists. product-content
        states the opposite case explicitly in § Purpose — "There is no machine gate" — and names what
        stands in its place. That sentence is worth copying whenever the absence could be mistaken for
        an omission.

     3. EXIT CODE AS VERDICT, OR NOT — where a skill runs two checks, they are read by opposite
        rules, and both product-design and product-content say so at the point of use rather than
        leaving it inferable. If a skill runs one check, say the code stands alone.

     4. A `## What the <DOC> is` SECTION — 1 of 6 (product-prd). The other five put the same content
        in the prompt or the template. Prefer those: it is the artifact's nature, not the
        orchestrator's.

     5. THE DROP INVARIANT — 5 of 6 carry § Consuming an answered companion and § An answered item
        never survives the drop as named blocks; product-prd carries the fold in its loop without the
        drop invariant. This template shows the five's shape, because the invariant is what stops a
        run reading its own rewrite back as owner answers.

     6. A `stack.json` BESIDE THE SKILL — 5 of 6 carry one (an ordered `substance` array naming the
        SKILL.md and its prompt); product-content does not. It is read by
        `<CORE>/tools/coldread/manifest.py`, so a skill without one cannot be cold-read. If the skill
        has a prompt, it wants one.

     7. A `README.md` BESIDE THE SKILL — owed only under the trigger in
        `<CORE>/doctrine/setup/authoring_layers.md` § A skill folder with more than a SKILL.md in it
        owes a README: a skill carrying `evals/` or `agents/`, or one that invokes another skill.
        Five of six carry one and each of those five carries `evals/`; product-content is a single
        file and correctly owes none. What sections a README carries is `skill-creator`'s and is
        adopted, not restated. Of the five, 4 open with `## Version and ratification` and a launching
        section; kensaiapp-writing-bar has neither. Nothing decides that today.
     ========================================================================= -->
