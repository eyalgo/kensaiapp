---
version: "1.4.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document —
     an agent file carries no `version`. Nor is this block.

     What this stamps: the agent file for one role — the plumbing that lets the role be spawned as a
     subagent and that binds its tools. Lands at `skills/<role>/.claude/agents/<role>.md`, in the group of the role's own name, one file per fork-invocable role. Step 4 of `<CORE>/doctrine/setup/adding_a_role.md`, which owns the
     order and the three registration surfaces this file lands with.

     THE BODY IS NOT YOURS TO WRITE. Everything below the frontmatter is the same in every agent
     file, role token substituted. Authoring it from scratch is the characteristic failure of this
     step: the result reads plausibly, duplicates the loader's job, and drifts from every other agent
     the first time the shared body changes. Substitute the tokens; change nothing else.

     TWO TOKENS, AND THEY ARE NOT INTERCHANGEABLE — a two-word role uses both:
       <role>       hyphenated — the agent's `name:`, and the `<role>:` invocation prefix
                    (`tech-lead`, `product-owner`, `cdo`)
       <role_file>  underscored — the loader FILENAMES only
                    (`tech_lead_global.md`, `system/loaders/tech_lead.md`)
       <Role Title> the human name as it appears in `commit_format.md`'s Role values
                    (`Tech Lead`, `Product Owner`, `CDO`)
     For a one-word role the first two are the same string. Getting this wrong produces a file that
     looks right and resolves to nothing.

     THREE FIELDS ARE THE ROLE'S OWN. They are the ones that get guessed, so decide each:

     1. `description` — what this role does AND what it is distinct from. The agent registry
        surfaces this verbatim, and it is the first thing a spawning session reads — before any
        loader. If the role has a near neighbour (the executive/delivery pairs: CDO vs Architect,
        CPO vs Product Owner, CTO vs Architect), name it here; the seam is why the role exists.
        Close with what it is NOT for. Plain YAML: no `: ` inside the value, or the line parses as
        a nested mapping and the frontmatter breaks.

     2. `tools` — grants follow the role's WORK, not the loader's prose. A loader is not an
        allowlist: a role that must research external references needs the tools for it whether or
        not its posture body has a paragraph asking. Three rows exist; pick the one the work fits
        rather than copying whichever sibling is nearest:

          document-authoring    Read, Grep, Glob, Write, Bash, Skill, <references>
                                — authors whole documents. `Write`, never `Edit` — UNLESS the
                                  role co-authors a document with other seats, which earns
                                  `Edit` and needs it: several roles writing one file cannot
                                  each `Write` it whole without overwriting the others. The
                                  case that earned it was the SDD, once written by the CPO, the
                                  CTO and the CDO in one run; the CTO skill `product-sdd` now
                                  writes it alone, and the grant stays for any role that does
                                  co-author. Added 2026-08-26, after the first such run
                                  stalled — a seat with no `Edit` built a shell command to
                                  patch the file instead, and the Bash permission parser
                                  aborted on its length and asked a background session with no
                                  terminal to approve it.
          code-touching         Read, Grep, Glob, Write, Edit, Bash, Skill, <references>
                                — modifies existing code surgically, so it earns `Edit`.
          research addition     WebSearch, WebFetch
                                — added to either row when the role must read the world
                                  (standards, references, competitors) rather than only the repo.

        `<references>` is a QUESTION, NOT A LIST: what must this role read that is not in the
        repo? Answer it per role — vendor documentation whose subject the product depends on,
        research beyond the open web, whatever surface the work actually reaches — and grant one
        MCP server per answer. Grant none for a surface the role never touches. A closed list
        here would make this file the allowlist the paragraph above says a loader must not be.

        DO NOT TAKE AN INVENTORY FROM THIS FILE. Which servers are connected is a property of
        the machine and changes without this template changing, so read the session's own tool
        list for what exists. What the galaxy's roster happens to hold today is a fact about the
        roster, not the set on offer, and a role whose work reaches further says so. The test
        either way: would this role otherwise park as an open issue something that server could
        settle?

     3. No `model` field. The intelligence a run gets is set by the skill it runs, not by the role —
        `<CORE>/doctrine/governance/skill_intelligence.md`. Do not add one.

     Nothing about posture, artifacts, ownership or seams belongs in this file; that is the loader
     stack it points at. If you are writing a paragraph, you are in the wrong file. -->

---
name: <role>
description: <What this role does — and what it is distinct from. Ends with what it is not for.>
tools: <the row this role's work fits, plus any references it must ground claims against>
---

You are the <Role Title>.

This file is plumbing, not your brain. Do not act on this one line — load your operating contract first.

Before doing anything else, Read these in full, in order, with the `Read` tool. A `cat` in `Bash` does not count, and every call other than `Read`, `Grep` or `Glob` is refused until each one has been read:

1. **Global loader** — `<CORE>/roles/loaders/<role_file>_global.md` (`<CORE>` is resolved at session start by the hook — use the injected path, never assume a literal one).
2. **Project overlay** — in the instance's `AGENTS.md`, find the `<role>:` row in its "Loader map", and Read the file it names (`system/loaders/<role_file>.md`). Skip if the instance defines no overlay for this role.
3. **Cross-role contract** — `<CORE>/roles/CROSS_ROLE.md`, plus the instance overlay `system/CROSS_ROLE.md`.

Those files define your behaviour, lens, output format, and hand-off triggers — they are the source of truth, this file is not. Then execute the task in your prompt under that contract.
