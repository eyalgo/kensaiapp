# Proposed evals — development-specs

The reviewable proposal behind `skills/product-owner/.claude/skills/development-specs/evals/evals.json`: what each case
tests, what the suite deliberately does not test, and why the second list is longer than the first.
A reader deciding whether the suite proves anything about this skill should read § *What this suite
cannot reach* before reading the cases.

Three cases. Each drives the skill to a refusal, and no case reaches a `change_spec.md`. That is a
property of the harness rather than of the skill, and § *What this suite cannot reach* states it.

---

## The input the cases supply

`skills/product-owner/.claude/skills/development-specs/SKILL.md` § *Input* says "The invocation must supply:" a project
name — "the `system/projects/<project>/` folder" — and a change request, "the **Request** in the
`change_request.md` of the single **active** change folder". Every prompt below supplies exactly
those two, in that vocabulary. No prompt names a `specs.md`; the skill reads no such file.

The project name in every prompt is `nonexistent-project`, which resolves to nothing on disk. That
is deliberate and it is what bounds the suite — see § *What this suite cannot reach*.

---

## Case 1 — halt-missing-project

**What it tests:** the guard fires when the project name resolves to no `project.md`, and the halt
report names the path the skill looked at rather than saying something generic.

**Input:** none on disk.

**Prompt:**

```
You are a product owner. Run development-specs for the project `nonexistent-project` with the change request: "Add tags to tasks."
```

**Expected:**

- `halt_report.md` created, carrying the halt reason `missing-project-context`
- the report names both `system/projects/` and `project.md`
- no `change_spec.md`
- no clarifying question asked

---

## Case 2 — halt-no-project-named

**What it tests:** `SKILL.md` § *Input* says "If no project name is supplied, halt with
`missing-project-context`", and § *Step 1 — Locate project docs* says "Do not infer or invent content
from the change request alone." The case gives a clear, single, well-formed change request and no
project, so a run that drafts a specification from the request has broken the second rule while
looking helpful.

**Input:** none on disk.

**Prompt:**

```
You are a product owner. Run development-specs with the change request: "Tasks should be able to have more than one assignee."
```

**Expected:**

- `halt_report.md` created, carrying the halt reason `missing-project-context`
- the report names the missing input and specifies nothing about assignees
- no `change_spec.md`

---

## Case 3 — halt-outside-product-owner-posture

**What it tests:** the posture gate. `SKILL.md` § *Input* opens "**Product Owner role only.** If
invoked outside a product-owner session, stop immediately" and then gives the sentence the skill is
to say, which names product-owner posture. The prompt establishes no posture, so the gate is the
first thing the run meets.

This case exists because `<CORE>/doctrine/kaizen/skills.md` § *Authoring the eval set* requires it:
"a case set that never invokes the skill from the wrong posture has left the gate untested." Until
this case was written the suite had no such case.

**Input:** none on disk.

**Prompt:**

```
Can you run development-specs for the project `nonexistent-project`? The change request is: "When a task moves to DONE, record the timestamp of when it happened."
```

**Expected:**

- no `change_spec.md`
- no `halt_report.md` — the posture refusal is spoken, not written, so it leaves no file
- the run says it requires product-owner posture, and specifies nothing about the timestamp

The absence of `halt_report.md` is what separates this case from cases 1 and 2, which both write one.

---

## What this suite cannot reach

**The skill's success path cannot be executed inside `skill-evals`, and no case here pretends
otherwise.** Two independent reasons, both measurable today:

1. **No project tree.** `skills/experimental/.claude/skills/skill-evals/SKILL.md` § *Step 1b — Open the fixture guard*
   says "A skill with no `evals/inputs/` is a clean no-op", and
   `skills/experimental/.claude/skills/skill-evals/scripts/stage_fixtures.py` prints "no fixture tree … nothing to
   stage" and returns an empty case map. With nothing staged, `.claude/workflows/run-skill-evals.js`
   hands the executor the authored prompt and omits the staged-tree paragraph, so the only writable
   location a case is given is its own `outputs/` directory. `SKILL.md` § *Step 1* reads
   `system/projects/<project>/project.md` from disk. A case therefore names either a project that
   exists in this live instance — which sends an eval run into the real repository — or one that does
   not, and halts.
2. **No shell.** `SKILL.md` § *Step 4 — Create the change worktree(s)* creates "branch `<key>` + the
   **instance** worktree `<repo>/.worktrees/<key>`", and § *Step 7 — Commit outputs* commits through
   the shared builder. `run-skill-evals.js`'s executor prompt permits Bash "for exactly one thing:
   **deleting a file the skill's own contract tells you to remove**". An executor that obeys that
   fence cannot create a worktree and cannot commit.

An archived run said the same in its own words, under the heading *Notes on eval-sandbox
deviations*: "The skill's Steps 1 and 4 … presuppose the full kensaiapp instance layout and a git
worktree, which the eval sandbox does not provide and Bash was disallowed." It sits at
`skills/product-owner/.claude/skills/development-specs/evals/workspace/iteration-2/priority-no-questions/with_skill/outputs/transcript.md`,
which `.gitignore:100` excludes — a reader who cloned this repository will not find it, and the
quotation is the whole of what it said.

### The six cases removed, and what they covered

The owner ruled on 2026-09-09 that `evals/inputs/task-tracker/specs.md` be deleted — "we use the
actual code now, that's why they are stale". Six cases opened by telling the model the project specs
were at that path, and none of them survives the deletion. They are recorded here so the coverage
they claimed is not lost:

| Case | Behaviour it claimed to cover |
|---|---|
| `multiple-assignees-success` | the five required `change_spec.md` sections; rules as a delta rather than a paraphrase of the base spec; substantive Locked Answers aimed at gaps the feature opens |
| `halt-multiple-changes` | the Step 3 halt when a request carries two independently shippable changes |
| `halt-too-vague` | the Step 6 halt when rules are too ambiguous to derive tests from, and whether the report names what is missing |
| `priority-no-questions` | self-resolving an unstated enumeration into Locked Answers rather than asking |
| `completion-timestamp-scope` | a non-empty `## Out of Scope`, and a concrete field name for the recorded timestamp |
| `delete-task-deferred` | shipping the specifiable part and parking the destructive direction in `deferred_decisions.md` |

Every one of those behaviours lives at Step 3 or later, so every one needs a project on disk.

### What would restore them, and who decides

**Restoring the six needs a fixture tree in the instance's own shape** — an
`evals/inputs/<project>/project.md` carrying a `Product path:`, plus a
`journey/tobiishi/<key>/change_request.md` holding the Request. `stage_fixtures.py` already supports
the first half: it copies the tree per case and per configuration and rewrites each staged
`project.md` so its `Product path:` names the copy. It does not stage a journey folder, and the skill
resolves `system/projects/<project>/` from the instance root rather than from a fixture root, so the
second half is unbuilt.

**That is a decision the owner makes, not this document**, because a new fixture tree re-opens the
ruling that deleted the last one. What this document can say is the narrower thing: the ruling
removed the only mechanism `skill-evals` has for giving `development-specs` a project, and the six
behaviours above stay unmeasured until something replaces it.

---

## Two findings for the skill, not for the eval set

Both were found while writing these cases and neither is fixed here.

**The posture refusal leaves no artifact.** `SKILL.md` § *Input* tells the skill to "stop immediately
and say" the refusal, where every other halt writes `halt_report.md`. Case 3 therefore rests on a
nuanced assertion read from the run's transcript, which is the weakest anchor the harness offers.
`<CORE>/doctrine/kaizen/skills.md` § *Authoring the eval set* names this class directly: "a behaviour
with no observable trace is one no eval can defend, and the finding belongs to the skill's design,
not to its eval set."

**A pre-worktree halt has no stated destination.** `SKILL.md` § *Step 3 — Pre-draft checks* says
"Write `halt_report.md` and stop" and names no directory, while § *Outputs* anchors every file to
"`$WORKTREE/system/projects/<project>/journey/tobiishi/<YYYY-MM-DD>_<slug>/`" — a path that does not
exist until Step 4. Cases 1 and 2 both halt before Step 4, so where their report lands is currently
the running model's choice.
