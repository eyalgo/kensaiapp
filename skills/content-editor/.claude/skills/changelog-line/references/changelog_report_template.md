---
version: "1.1.1"
---

# Changelog report — <key>

<!-- Model-read. The run writes this file fresh at `system/projects/<project>/journey/tobiishi/<key>/
     changelog-report.md`, only on success. Neither this frontmatter nor this comment survives: the
     report opens at its heading and carries no `version:`. It is factual evidence that the step
     finished, not a ledger and not an instruction to another role. It never names its own commit,
     which does not exist when it is written. Each section is written on every success. -->

## Change

<!-- The change key, the project, and the change's own product path. Then each considered changelog:
     its path, the repository that holds it, and why it is considered, which is one of three: it is
     the own product path's, a changed path lies under its product path, or a listed root file
     changed. Then each project card the path tool refused, by project name, with the tool's
     message. -->

## Changelog

<!-- Where no considered changelog gets an entry, the section opens with one line, before the lines
     below. It is the first of these two sentences when at least one considered changelog exists,
     and the second when none of them exists, written as given:

         The change earns no entry, because it alters nothing a user of a fresh clone installs, runs, types or reads at any product path this run considered.

         The product path keeps no changelog, and no other product path this run considered keeps one.

     Then one line for each considered changelog, naming it and the repository that holds it, with
     exactly one outcome: the entry or entries written, each with its group and the commits it
     cites; that the change earns no entry there, and why; or that its product path keeps no
     changelog, so no file was created there. -->

## What-left

<!-- One of: each removed want, its Wanted text verbatim and the branch commit at which its whole want
     is built; that no want is wholly built; that the file is absent; that the file is malformed, named
     and left unchanged; a kept want and why; or that the file was left as it was because the change's
     own product path keeps no changelog. -->

## Evidence

<!-- The existing source commits that justify each edit. Where the product sits in another repository
     and the run committed there, the product commit the run landed first, by hash and checkout. -->
