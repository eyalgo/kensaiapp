---
name: changelog-line
description: Content-editor-posture skill the change chain runs on a change's branch after implementation and before code integrity. It writes the change's entry under the Unreleased heading of the CHANGELOG.md of each product path the branch changes, with the change's own product path always considered and a change to a root file the structure map lists logged in core/tools/CHANGELOG.md. It removes from docs/what_left.md at the change's own product path only the entries whose whole want the change completes, so a part-complete entry stays. A product path with no CHANGELOG.md loses nothing and the step still finishes, and so does one with no what-left file. It commits on the change's branch in each repository that holds a file it changed, writes changelog-report.md in the change folder as the proof it finished, and never touches main. Halts outside Content Editor posture. Run when a change has implemented work on its branch and its changelog lines and what-left file are not yet brought up to it.
license: MIT
metadata:
  version: "1.1.1"
---

# changelog-line

**The prompt owns judgment, and this file owns the loop.** `prompts/thin.md` decides what the change
built, whether it earns an entry in each changelog the run considers, which wants it wholly completes
and the words of every outcome. This file gates the posture, resolves the worktrees, finds the
changelogs the run considers, validates every file the run may write, writes only those files and
commits in the order below. It reads that one prompt and no other judgment body. The posture refusal
below runs before the prompt is read.

## When to Use

- The chain's `changelog` step launches it for every change, after `implementation` lands and before
  `code-integrity`, whether or not the earlier content step ran. Start it by hand with
  `<CORE>/launchers/skill/launcher.sh changelog-line <project> <key>`.
- **Content Editor role only.** Outside a `content-editor` session or subagent the run changes no
  file, makes no commit, writes no report and reads no project input. Its final message says it needs
  Content Editor posture.

**Refused for posture — the session is not a Content Editor session**

> changelog-line changed no file and made no commit.

> It needs Content Editor posture.

> Open a session or subagent as `content-editor` and run changelog-line again.

**The two jobs.**

1. It writes the change's entry under `## [Unreleased]` of the `CHANGELOG.md` of each product path the
   branch changes, on the change's branch. The change's own product path is always considered, and a
   change to a root file is logged in `core/tools/CHANGELOG.md`. Step 2 finds these changelogs. Each one
   earns an entry or none on its own.
2. It removes from `docs/what_left.md` at the change's own product path only the entries whose
   **whole** want the change completes. A part-complete entry stays. A product with no
   `docs/what_left.md` loses nothing, and the step still finishes. No other product path's what-left
   file is read or written.

**Do not use for:**
- A README, a release-notes file or any product file but the considered changelogs and the what-left
  file at the change's own product path.
- Adding, rewording or reordering a changelog entry already there, or a what-left entry. Reducing is
  all the run does to the what-left file (`<CORE>/doctrine/setup/kensaiapp_structure.md` § 3,
  *The what-left file*).
- Writing a product's first `CHANGELOG.md`, or moving `## [Unreleased]` under a release at a cut.
- Deciding whether a merge declares its changelog line. That check is another change's.
- Launching or naming any step that follows. The run knows no successor.

## Inputs

`<project>` and `<key>`, the project name and the change key (`<YYYY-MM-DD>_<slug>`, the Tobiishi
folder and the branch name). Nothing else is handed over.

## Workflow

Run from the instance root. The run's own commits go through `<CORE>/tools/commit_builder.py`,
following `<CORE>/doctrine/governance/commit_via_builder.md`. Never `cd` into a repository to run git.

### 1 — Check the posture

Before reading any input, confirm the session is a `content-editor` session or subagent. If it is not,
give the refusal above, write nothing and stop.

### 2 — Enter the worktree, resolve the product and find the changelogs

The change's earlier steps opened an isolated worktree at `<instance>/.worktrees/<key>` on branch
`<key>`. Derive it from the key alone and write its absolute path down before anything else, because a
shell variable does not survive from one command to the next. Refuse if the worktree is absent: the
run never creates one and never falls back to `main`.

Ask the path tool, every run, and never compose a product path by hand:

```bash
"<CORE>/tools/locked_python.sh" "<CORE>/tools/development_path.py" resolve --format json \
  --worktree "<instance worktree>" --project <project> --key <key>
```

A non-zero exit is a refusal carrying the tool's `message` verbatim. From the contract's
`product_path`, `product_repo` and `product_worktree`: `<sub>` is `product_path` when it is relative,
else `product_path` relative to `product_repo` (`.` when the same). That `<sub>`, in the product's
repository, is the change's **own product path**. Its changelog is `<product_worktree>/<sub>/CHANGELOG.md`,
and `<product_worktree>/<sub>/docs/what_left.md` is the one what-left file the run reads or writes. For
an in-repo product `product_worktree` is the instance worktree. For an external one it is the product
worktree opened for this change, never the product's primary checkout.

Check that the instance worktree **and** the product worktree are each on branch `<key>`
(`git -C <worktree> branch --show-current`). Refuse if either is not. Never switch a branch.

Then find the changelogs the run considers. Each path the branch changes is logged in the
`CHANGELOG.md` at the root of the product path it sits under, and a change to a root file is logged in
`core/tools/CHANGELOG.md`, by `<CORE>/doctrine/setup/kensaiapp_structure.md` § 3, *The changelog*.
Read which root files that section lists at its owner, and do not copy them here.

**(a) The product paths.** For each project folder under `system/projects/` in the instance worktree,
run the path-tool command above with that project's name, without `--strict`. Never read a value off a
project card by hand. Take each contract's `<sub>` by the rule above, in the repository its
`product_repo` names. Keep it only where that repository is the instance's or the own product's,
because those two are the repositories that hold branch `<key>`. Keep each pair of repository and
`<sub>` once. Another project's card that the tool refuses gives no product path, and the report's
§ *Change* names it. It does not stop the run.

**(b) The changed paths.** In each repository the change holds, list the paths the branch changes
since it left `main`, with both sides of a rename counted:

```bash
git -C "<worktree>" diff --name-only --no-renames main...<key>
```

**(c) The considered changelogs.** Start with the own product path's changelog, so that it is
considered on every run, whether or not the branch changes a path under it. Then take each changed
path in turn:

- In the instance repository, a path equal to a root file that § *The changelog* lists is logged in
  `core/tools/CHANGELOG.md`. This check comes before the product-path match.
- Otherwise the path is logged in the changelog of the deepest kept product path in its repository
  that the path equals or lies below. That is the longest `<sub>` that is the path itself or is
  followed by `/` in it. A `<sub>` of `.` holds every path in its repository.
- A path under no product path, and not a listed root file, is logged in no changelog.

Each considered changelog is `<worktree>/<sub>/CHANGELOG.md`, in the worktree of the repository that
holds it, and carries the changed paths assigned to it. The own product path's changelog may carry
none.

### 3 — Apply the changelog rule first

Check each considered changelog on the branch's tree, never on the file system:
`git -C <worktree> cat-file -e <key>:<sub>/CHANGELOG.md`. A changelog the branch's tree does not hold
means that product path keeps no changelog. It gets no entry, no file is created there, and the run
goes on with the other considered changelogs. Where the absent changelog is the own product path's,
the what-left reduction is skipped as well, and the what-left file is left as it is.

Each considered changelog the tree holds must hold exactly one line reading `## [Unreleased]`. Zero or
several in any of them is one refusal, naming that file. It is raised before any candidate is
prepared, with every considered changelog and the what-left file unchanged.

Where no considered changelog exists, prepare no product edit and go to step 7 with that outcome.

### 4 — Read and judge

Read the change's `change_request.md`, `change_spec.md`, `change_design.md` and `tl_instruction.md` in
the change folder, and `git log` of the branch against `main` in each repository the change holds.
For each considered changelog, read the diff the branch carries over the changed paths assigned to it.
A changelog the branch's tree does not hold is handed on as absent. Judge what was **built**, never
what was requested or deferred. Read the changelog template
(`<CORE>/templates/product-templates/changelog_template.md`) and the structure map's *The changelog*
and *The what-left file* sections (`<CORE>/doctrine/setup/kensaiapp_structure.md` § 3) at their
owners, and do not copy their grammar here. Write to `system/doctrine/writing_bar.md`. Whether a
product's `CONTENT.md` governs its changelog is an open question this run does not settle.

Then apply `prompts/thin.md`, which judges each considered changelog on its own. A check that must
execute code runs in a **disposable copy**, a fresh clone at the commit under test
(`git clone --quiet <repo> <scratch> && git -C <scratch> checkout --quiet <sha>`; never
`git archive`), from a subshell, and the copy is removed in a command of its own run from outside it
(`<CORE>/roles/CROSS_ROLE.md` § *Every seat — a run leaves the product's main checkout as it found
it*).

### 5 — Build every candidate, then check them

Prepare every candidate from the original bytes before writing any: each considered changelog that
gets an entry, and the what-left file.

- **Each changelog** takes at most the entry or entries the prompt gives it, inserted only under its
  `## [Unreleased]`, with only nonempty groups, in the template's order. Every existing entry and
  release heading stays byte-identical. A changelog where the change earns no entry is left as it is.
- **The what-left file** is read to the grammar of the structure map's *The what-left file*. Absent,
  nothing is removed. Malformed (neither an entry nor the empty marker, or both): keep its bytes, name
  it in the outcome and finish the changelog job. Valid: remove only the original three-line entry
  spans of wants proven wholly built, so the H1, the lead sentence, the other entries and their order
  stay byte-identical. When the last entry goes, the file holds the line `Nothing is left to build.`
  alone on its own line beneath the preserved heading and lead. A valid empty file stays unchanged. The
  file is never deleted, and the run never adds an entry.
- Each removed entry yields one body line, `Merged in <commit>: <the entry's Wanted text, verbatim>`,
  where `<commit>` is a commit on the change's branch at which the whole want is built.
- Check the result: every cited commit is at least nine hex digits in an inline code span and is
  reachable from branch `<key>` in the repository that holds the file (`git merge-base
  --is-ancestor`), and no unselected byte moved in any candidate.

### 6 — Re-check, then write and commit

Immediately before the first write, re-check every file the run will write: its original bytes, that
it is clean (no uncommitted changes), and that the branch tip of the repository that holds it is the
one read at the start. Refuse on a change in any of them. Write only the changed files.

Then commit, always as `--actor content-editor --skill changelog-line` with the runtime's surface and
identity, `--reasoning-effort` when the launch resolved one, and a directional per
`<CORE>/doctrine/governance/commit_format.md` § Directional trailer. A body goes through a `mktemp`
file. Stage every changed file of one repository in that repository's one commit, with `--add`,
repository-relative paths, one flag.

- **One repository** (the product sits in the instance repository): write the changed changelogs, the
  what-left file where it changed, and the report (step 7). Make **one** commit in the instance
  worktree that holds them together. The body carries the `Merged in` lines.
- **Two repositories** (an external product): where the product worktree holds a changed file, its
  changelog or the what-left file, commit those first, in the product worktree, with the `Merged in`
  lines in its body. Then write the report, with that commit's actual hash in its Evidence. Commit the
  report in the instance worktree together with every changed changelog the instance repository holds.
- **No product write** (no changelog gets an entry and no want is removed): commit the report alone in
  the instance worktree.

A refusal or failure of a commit stops the run with no retry, no second attempt in another shape and no
index waiver. The final message reports the actual state in the commit-refused sentences of
`prompts/thin.md`. A report is never committed after an incomplete or refused product write.

### 7 — The report

`changelog-report.md` in the change folder (`system/projects/<project>/journey/tobiishi/<key>/`) is
written **only on success**, from `references/changelog_report_template.md`. The template's frontmatter
stays behind: the report opens at its `# Changelog report` heading and carries no `version:`, whatever
marker the template holds. It is factual completion evidence. For each considered changelog it gives
the entry and its commits, or why there is none. It gives the removed wants and the commit each cites,
or why none was removed, and the source commits that justify the edits. It never carries its own commit
and gives no instruction to another role. Its being committed on the branch is what the chain reads as
the step done, whatever the run changed.

On a refusal that raised a validation failure, write `halt_report.md` in that same existing change
folder, naming the condition and the checks behind it, commit it alone in the instance worktree and
write no success report. A posture refusal, and a run with no worktree to hold a change folder, write
nothing.

## Final message

The one outcome, in the sentences of `prompts/thin.md`. A refusal states the failure first. A finished
run states each commit, the report, then one changelog outcome for each considered changelog and the
what-left outcome that applied. Wording the standard lacks goes in the message as a finding for the
Content Manager. The run writes no file but the considered changelogs, the what-left file at the
change's own product path, `changelog-report.md` and `halt_report.md`.

## Critical Rules

- **Content Editor posture only**, checked before any input is read.
- **Only the change's branch.** Nothing is written on `main` and no branch is switched or created.
- **Only the considered changelogs and one what-left file**: the `CHANGELOG.md` of each product path
  step 2 finds, and `docs/what_left.md` at the change's own product path. No README, no release notes,
  no created changelog.
- **A product path with no changelog gets no write.** Where it is the change's own product path, the
  what-left reduction is skipped too. The other considered changelogs still get theirs.
- **Never add, reword or reorder** an entry. Reducing is all the run does to the what-left file.
- **Report only after every product commit**, and never after a refused one.
- **Evidence runs in a disposable copy**, never in a product checkout.
- **Every core reference is `<CORE>`.** The method is `prompts/thin.md`.
