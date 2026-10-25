---
version: "1.0.1"
---
<!-- The version above is template-file metadata; it is not copied into the report. Nor is this block.

     What this is: the shape of ONE `ad-hoc-plan` report, written on every run, a stop included, as
     `ad_hoc_plan_report.md` in the change folder beside `ad_hoc_plan_brief.md` — or beside
     `change_request.md` when the run had no brief and the Request was the brief. Where it is
     committed is `SKILL.md` § *The run's report*. A model reads this and writes a fresh file. Nothing
     here is copied.

     Who reads it: the caller. In a session, the owner. Unattended, whoever comes to the change next,
     with nobody having read the run's closing message. So it says what happened plainly, and nothing
     a reader would have to ask about. -->

# Plan report — <key>

*Brief: `<path>`, or `none — the Request is the brief`. <YYYY-MM-DD>. Outcome: <planned | stopped>.*

## The ask, line by line

<One row per line of the brief's `## The ask`, or per sentence of the Request when there is no brief.>

| Ask line | Carried by | Or why not |
|---|---|---|
| "<the line, as the brief quotes it>" | <`CP-<n>`, a task, or a `## Locked Answers` line> | — |
| "<the line>" | — | <out of scope, as the brief's `## Out` says · held smaller, and what was measured · not reached, because the run stopped> |

## Claims that did not hold as stated

<Each claim that held smaller or did not hold: the claim, the check that measured it, and what the
plan did instead. Or `none`.>

## Picks the run made for itself

<Each direction the request left open that Step 3 picked, as its `## Locked Answers` line records
it. Or `none`.>

## What it left

<On a plan: the branch, the worktree, the three files by path, the step the chain enters (`content`
or `implementation`, from the design's `Publishes text:` line), how the card's `Test command:` run in
Step 6 came out, and the next move as Step 9 names it.
On a stop: what exists — nothing, the branch and worktrees Step 4's command printed, or on a Step 6
stop those worktrees and the stub files written in them, uncommitted.>

## Stop

<Only on a stop: which case fired, the file or claim that fired it, the check that produced the
verdict, and what would settle it. Otherwise omit the section.>
