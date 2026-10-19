---
version: "1.0.0"
---

# first-what-left — the judgment

You are the CPO. `SKILL.md` has run the checks, recorded the tip of `main` and read the Agari and the
PRD. What is left for you is the thinking, and the thinking is two things: which of the wants those
two documents state go on the list, and how each entry is worded. The messages the owner reads are
below, and you use their sentences as written.

## What you receive

- the **Agari** and the **PRD**, whole;
- the **tip** of `main`, nine hexadecimal digits, and the product's repository to search at it;
- the **template** `<CORE>/templates/product-templates/what_left_template.md`, which owns the file's
  shape, and `<CORE>/doctrine/setup/kensaiapp_structure.md` § 3, *The what-left file*, which owns what
  an entry is.

## Which wants go on the list

An entry is one want, stated in the Agari or the PRD, that the product's code can be shown not to do
at the recorded tip. You show it by `git grep` at that commit, or by running the code in the
disposable copy `SKILL.md` allows. A want that only the owner's judgement can pass or fail gets no
entry, whichever document states it, and neither does a want the product's code already does.

- **Done:** the search finds the behaviour and, where it can be run, running it confirms the want.
  No entry.
- **Judgement only:** nothing a search or a run could show would settle it, such as how pleasant the
  prose is to read. No entry, and the message says so in the sentence for it.
- **Not shown either way:** the run could not show whether the code does it. No entry, and the
  message says so in the sentence for it. You never write an entry on a guess.
- **Missing:** the code does not do it, and you can say what you searched or ran. One entry.

When no want is missing, the file holds the heading, the lead sentence and the line
`Nothing is left to build.` alone on its line, and no entry.

## How an entry is worded

- `**Wanted:**` is the want, written as a want and never as a step, a task or an order of work, in the
  words of the document that states it where those words already say it as a want.
- `**Source:**` is `Agari § <section heading>` or `PRD § <section heading>`, adding
  `, **<item name>**` where the section has named items. The heading is one the document holds.
- `**Missing at:**` is the recorded tip in an inline code span. Every entry gives the same one.
- No entry names a station, a seed, a change unit or a `journey/` path.

## The messages

These are the words the owner reads in the final message of a `first-what-left` run. A message is
the whole sentences of its state, in the order listed, with nothing added between them. A refusal
before any write opens with the sentence under *Refused before any write*, then gives the sentences of
the condition that held. Every variable is filled in as the run resolved it:

- `{project}` is the project name the run was given.
- `{product path}` is the card's `Product path:` value, exactly as the card writes it.
- `{product}` is the directory that value resolves to.
- `{checkout}` is the root of the git repository that holds `{product}`.
- `{what_left}` is `{product}/docs/what_left.md`.
- `{prd}` is `{product}/docs/PRD.md`.

Every path variable is written inside an inline code span, as shown.

### The run's refusal messages

**Refused for posture — the session is not a CPO session or the `cpo` agent**

> first-what-left wrote no file and made no commit.

> It needs CPO posture.

> Open a session or subagent as `cpo` and run first-what-left again.

**Refused before any write — the opening sentence of every refusal below except the commit builder's**

> first-what-left wrote no file and made no commit.

**Refused — condition 1, the project has no card**

> The project {project} has no card at `system/projects/{project}/project.md`.

**Refused — condition 1, the card names no product**

> The card at `system/projects/{project}/project.md` has no `Product path:` line.

**Refused — condition 2, the Product path is nominal, and it resolves to the instance root**

> The Product path `{product path}` in `system/projects/{project}/project.md` is nominal, so it names no product.

> `{product}` is the instance root.

> The run writes a what-left list only inside a product's own `docs/`.

**Refused — condition 2, the Product path is nominal, and it resolves at or under a directory the instance places in itself**

> The Product path `{product path}` in `system/projects/{project}/project.md` is nominal, so it names no product.

> `{product}` is at or under `{directory}`, which `<CORE>/doctrine/setup/kensaiapp_structure.md` § 1 *Instance-level* places in the instance itself.

> The run writes a what-left list only inside a product's own `docs/`.

`{directory}` is the directory § 1 claims that `{product}` sits at or under, as the run resolved it.

**Refused — condition 3, the what-left list already exists**

> `{what_left}` already exists.

> first-what-left writes only a product's first list, so it left that file as it was.

**Refused — condition 4, the project has no Agari**

> The project {project} has no Agari at `system/projects/{project}/agari.md`.

> The run writes the first list only once the project's Agari is settled.

> Run first-what-left again once the project has a settled Agari.

**Refused — condition 5, the Agari is not settled**

> The Agari of {project} is not settled, because `system/projects/{project}/agari_open_issues.md` exists.

> The run writes the first list only once the project's Agari is settled.

> Run first-what-left again once `system/projects/{project}/agari_open_issues.md` no longer exists.

**Refused — condition 6, the product has no PRD**

> No PRD is at `{prd}`.

> The run reads both the Agari and the PRD before it writes the list.

> Run first-what-left again once `{prd}` exists.

**Refused — the product is not in a git repository**

> `{product}` is not inside a git repository, so the run has nowhere to commit.

**Refused — the product's repository has no `main`**

> The repository at `{checkout}` has no `main` branch.

> Every entry's `**Missing at:**` commit must be one that `main` carries, so the run writes no list without `main`.

**Refused — one path is staged in the product's repository**

> `{path}` is staged in `{checkout}`.

> The run's commit may hold only `{what_left}`.

> Unstage `{path}`, then run first-what-left again.

`{path}` is the staged path.

**Refused — several paths are staged in the product's repository**

> `{path}` is staged in `{checkout}`.

> The run's commit may hold only `{what_left}`.

> Unstage each path above, then run first-what-left again.

The first sentence is given once for each staged path, in the order the repository lists them. The second and third sentences are given once, after all of them.

**Refused — the what-left list appeared while the run was working**

> `{what_left}` came to exist while the run was working, so the run left it as it was.

**Refused — any other condition that stops the run before it writes**

> {One sentence naming the condition, with the file or repository it concerns}

The sentence is the run's own, written to `system/doctrine/writing_bar.md`. It names a single condition and ends with a full stop.

**The commit builder refused the commit**

> first-what-left wrote `{what_left}` and made no commit, because the commit builder refused it.

> `{what_left}` is in `{checkout}`, uncommitted.

> The builder said this: {the builder's message, verbatim}

> A new run would find `{what_left}` and leave it as it is.

> Commit the file, or delete it and run first-what-left again.

This message does not open with the *Refused before any write* sentence.

### The run's completion message

**Written — the opening sentence when the run made its commit**

> first-what-left made commit `{sha}` in `{checkout}`.

`{sha}` is the nine-character abbreviated SHA of the run's one commit.

**Written — the list's path**

> The run wrote `{what_left}`, the product's first what-left list.

This sentence follows the opening sentence in every completion message.

**Written — the list has one entry**

> The list has 1 entry.

**Written — the list has several entries**

> The list has {count} entries.

`{count}` is the number of entries, always 2 or more.

**Written — the commit every entry was judged at**

> Every entry gives `{tip}` as its `**Missing at:**` commit, the tip of `main` the run judged the product at.

`{tip}` is the nine-character abbreviated SHA of the tip of `main` that the run recorded. This sentence follows the entry count whenever the list has an entry.

**Written — no want is left to build**

> The list holds the line `Nothing is left to build.` and no entry.

This sentence takes the place of the entry count and of the `Missing at` sentence.

**Reported after a write — a want left out because only the owner's judgement can pass it**

> The list leaves out the want "{want}" from {source}, because only the owner's judgement can tell whether the product does it.

`{want}` is the want as the Agari or the PRD states it, in straight double quotes. `{source}` is written the way an entry's `**Source:**` line would name it: `Agari § {section heading}` or `PRD § {section heading}`, followed by `, **{item name}**` where that section has named items. The sentence is given once per want left out, after the sentences above.

**Reported after a write — a want left out because the run could not show the code lacks it**

> The list leaves out the want "{want}" from {source}, because the run could not show whether the product's code does it.

`{want}` and `{source}` are as above. The sentence is given once per want left out, after the sentences above.
