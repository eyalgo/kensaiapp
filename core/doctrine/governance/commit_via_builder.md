---
version: "1.0.0"
---

# Commit via builder — the one way a producer skill commits

The shared recipe for committing an artifact through the one builder. Read on demand by any skill whose
run makes a commit, and equally by a session that read a prompt straight, with no skill wrapping the
run — each caller names this file at its own commit step, and no roster of them is kept here.
**Single source — edit here, not in the carriers.**

It is shared material the skills Read on demand, kept beside `commit_format.md`, whose format and
operations it puts into practice. (The merge/seal callers build their `--no-ff` merge directly through the same
builder — `commit_builder.py merge` — rather than through a shared prose file.)

## The rule

A producer skill **calls the builder** with what to stage — it never hand-writes `git commit`, never spells
out a trailer, and never stages in a separate step. The builder (`<CORE>/tools/commit_builder.py`, `<CORE>`
resolved at session start) stages the paths you name (via `--add` / `--rm`), derives `Role:` from `--actor`,
and lays down the full trailer block (directional topmost + `Role:` + `Surface:` + `Co-Authored-By:`) in
canonical order per `<CORE>/doctrine/governance/commit_format.md`. The skill supplies subject / body / actor
/ context / paths and knows no trailer shape.

**NEVER `cd` into the repo to stage**, and never run `git add`/`git rm` yourself. Both are
`<CORE>/doctrine/governance/commit_format.md` § Git operations — read the reasons there. One
`commit_builder.py` call stages and commits, so there is nothing to stage by hand.

## The call

The builder stages and commits in one call — pass the paths, don't run `git` yourself:

```bash
python3 "<CORE>/tools/commit_builder.py" --repo "<repo>" commit \
  --add "<file(s) to stage>" \
  --rm "<file(s) to delete, if any>" \
  --subject "<subject>" --body "<body>" \
  --actor "<actor>" \
  --skill "<producing-skill-name>" \
  --directional "<directional>" \
  --surface "<execution surface>" --co-authored-by "<runtime identity>" \
  --claude-session "<the session URL, when the run has one>"
```

- **`--surface` and `--co-authored-by` describe the runtime that actually made the commit.** Use
  the execution surface and identity supplied by that runtime's bootstrap context; never copy a
  provider name or address from an example. Codex runs receive `Codex` and
  `<assigned model id> <noreply@openai.com>` explicitly; a Codex run whose context names no model
  receives `Codex <noreply@openai.com>`. Gemini runs receive `Gemini` and
  `<assigned model id> <noreply@google.com>` explicitly; a Gemini run whose context names no model
  receives `Gemini <noreply@google.com>`. Claude runs use their actual Claude Code surface and
  model identity. The canonical meaning and spelling of both trailers remains
  `<CORE>/doctrine/governance/commit_format.md` § Surface tracking.

- **`--claude-session <url>`** — the session that produced the commit, placed after
  `Co-Authored-By:`. Optional, and omitted correctly by a run that has no session URL to give. It is
  in this recipe because it was not: added to the builder later than the rest, it reached only the
  callers who happened to know, and one branch measured 16 of 33 commits without it while every
  caller believed it was doing the whole recipe. A flag nobody is told about is a flag half the
  callers omit.

**A `--body` that carries a backtick goes through a file, never inline.** `--body "$(cat <file>)"`
rather than a quoted literal. A backtick in an inline shell argument is command substitution: the
shell runs it, the text vanishes from the message, and the commit lands looking fine. Measured
2026-09-02, on a body whose only example of the defect it was describing was eaten.

- **`--add <paths…>`** — files to stage (created or modified). The builder runs `git -C "<repo>" add` on
  them before committing.
- **`--rm <paths…>`** — files to delete this commit (e.g. an open-issues file when a round finishes clean).
  The builder runs `git -C "<repo>" rm` on them first. Omit when nothing is being removed. Staging fails
  loud: if a `--rm`/`--add` path can't be staged, the builder exits non-zero and makes **no** commit.
- **House style: every path rides ONE flag — `--add a b c` rather than `--add a --add b`.** Both flags
  carry `action="extend"` (see `commit_builder.py`), so repeats **accumulate** — `--add a --add b` is
  `--add a b`. One flag per kind is a readability convention, not a guard against losing a path.
- **A `git mv` stages its rename, and you must still declare it.** The move is in the index the moment
  you run it, but the staged-set guard below refuses any commit whose staged set is not declared, and a
  `git mv` staged outside the builder is exactly that shape. Pass **`--staged`** naming both halves of
  the move (or a directory prefix covering them). `--staged` stages nothing; it is a declaration that
  you staged this deliberately. **Never** fall back to `git add -A` to "catch everything" — that sweeps
  in unrelated dirty files. Stage only what you touched, by name.
- **If you also edited the file, `--staged` alone silently drops the edit.** `git mv` stages the rename
  and nothing after it, so content changes made once the file is at its new path are still unstaged, and
  `--staged` will not stage them — the commit lands as a pure rename at 100% similarity and the edit is
  gone. Pass the **new path in `--add` as well as in `--staged`**: `--staged old new --add new`. Measured
  2026-09-06, when a rename-plus-edit commit landed with the rename only and had to be repaired by a
  second commit. The tell is a `git show --stat` whose rename line reads `(100%)` when you know you
  changed the file — check it, because nothing else will.

**Empty marker commit** (nothing staged — e.g. `development-implementation`'s closing commit): pass no
`--add`/`--rm` and add `--allow-empty`. The builder passes it through so the marker commit lands; without it
git refuses an empty tree.

## The staged-set guard

The builder refuses a commit whose staged set you did not declare, because the index is shared and
another session's work would otherwise ride along. What the guard covers, what a refusal means, why
re-running is safe, when `--take-index` applies, and the one window it cannot close are
`<CORE>/doctrine/governance/commit_format.md` § Git operations. Read it there; this file does not
restate it.

What is yours as a caller is the declaring itself — the flags and the `git mv` case are item 1 and its
`--staged` bullet above.

## The variables the caller supplies

1. **`<repo>` + `--add`/`--rm` paths** — which repo/worktree the commit lands in and what to stage. In the
   flow that is the change worktree `$WORKTREE` and the one artifact the step produced (e.g.
   `change_spec.md`, `change_design.md`, `tl_instruction.md`, `flow_findings/`, the code-integrity
   report). Stage **only** that artifact. Pass paths to `--add`/`--rm`; never run `git add`/`git rm`
   yourself, and never `cd` into the repo (see the rule above).
2. **`<actor>`** — the agent_type you run as, passed as a token (not a Role display value): the token from
   your `You are the <token>` pipeline prompt in workflow mode, or the role you run as in interactive mode.
   The builder maps it through `AGENT_ROLE` to derive `Role:`; an unmapped actor is refused, not guessed.

   **An actor with no `AGENT_ROLE` row passes `--role` instead, and the refusal is the point.** The
   builder takes exactly one of the two. `--actor` is for a caller whose `agent_type` *is* an
   originator; `--role` is for one with no such identity, and it carries what the **work** originates
   as. The `delegate` agent is the standing case — `<CORE>/roles/delegate_contract.md` § *Your `Role:`*
   owns why it has no row and what it passes instead. Read it there rather than inferring a value: a
   run that answers the refusal by capitalising its own actor token writes a `Role:` that names the
   mechanism instead of the originator, which `<CORE>/doctrine/governance/commit_format.md` records
   six commits of.
3. **`--skill <name>`** — the producing skill's own name, so the commit records what ran
   (`Skill-Version:`). As a producer skill committing your own artifact, pass **your own skill name**.
   The flag is the only thing that stamps the line, so **omit it when no producing skill authored this
   commit's output**. What that absence positively means, and why it is a stated result rather than a
   gap, are `<CORE>/doctrine/governance/commit_format.md` § `Skill-Version:` trailer. Read it there;
   this file does not restate it.
4. **`--prompt <name>`** — the prompt this session read to produce the output, so the commit records
   what it followed (`Prompt-Version:`). Pass **your own prompt's name** — never a prompt you did not
   read; that is the one part of this only you know. The flag's value form, its independence from
   `--skill`, and what omitting it positively records are
   `<CORE>/doctrine/governance/commit_format.md` § `Prompt-Version:` trailer. Read it there; this file
   does not restate it.
5. **`<subject>` / `<body>`** — the commit's own content, exactly as the step would describe it.
6. **`<directional>`** — the full directional line, resolved against the project's journey by phase.
   Which trailer applies, how each one resolves, and what `progress:` / `aside:` / `none` each mean are
   `<CORE>/doctrine/governance/commit_format.md` § Directional trailer. Read it there; this file does
   not restate it.

   What is yours as a caller: the directional follows the **scope of what the run wrote**. A producer
   skill committing a project's artifact takes `Shukuba:` or `Agari:`; one committing an instance-tree
   artifact (an instance-level document, the instance seedbed) takes `Michi:`. A project's artifact
   never carries `Michi:`, which is the instance level's.
7. **`--reasoning-effort <level>`** — the reasoning-effort level this run's launch resolved, so the
   commit records it (`Reasoning-Effort:`). A run whose bootstrap names a resolved level passes that
   level as `--reasoning-effort`, exactly as named. A run whose bootstrap names none **omits the
   flag** and never picks a level to fill it; an interactive session is the standing case. What the
   trailer means and which levels exist are `<CORE>/doctrine/governance/commit_format.md`
   § `Reasoning-Effort:` trailer. Read it there; this file does not restate it.

## Hook

If the repo has a `commit-msg` hook validating trailers, it fires on the commit. A builder-made commit
always passes it. On hook failure, stop and surface the error.
