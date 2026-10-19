---
version: "1.10.0"
---

# Versioning — which artifacts carry a `version:`, and how it moves

**This file owns:** which kensaiapp artifacts carry a version marker, the test that decides it, the
marker's form per kind, and the bump semantics. `doctrine_structure.md` § Versioning points here for
doctrine's own case. **It does not own** a template's format — that is `core/templates/README.md`
(a template's format follows its consumer) — nor how a commit records the skill that produced it
(`commit_format.md` § `Skill-Version:` trailer).

## The test — who reads the file, not what kind of thing it is

- **Model-facing** — read by a human or an agent, and its own bytes never land verbatim in a
  product. The marker is metadata for its readers, so the file **carries one**.
- **Script-facing** — stamped verbatim by a tool, so its bytes *are* the product's
  (`core/templates/README.md` § Adding a script-facing template owns that cost). It **must not
  carry one**: the marker would be stamped into every instance created after it, as content nobody
  wrote for that instance.

Kind is not the test. Most templates are script-facing, but a template a model reads is not — the
split runs *through* the template layer, not around it.

## Where the test lands

| Kind | Version marker |
|---|---|
| Doctrine — `core/doctrine/` | frontmatter `version: "x.y.z"` |
| Explanatory docs — `core/docs/` | frontmatter |
| Prompts — `core/prompts/`, and a skill's own `prompts/` | frontmatter |
| Launchers — `core/launchers/*/launcher.sh` | `# Version: x.y.z` header comment |
| Scripts & hooks, shell — `core/tools/`, `core/githooks/`, `.claude/hooks/` | `# Version:` header comment |
| Scripts & hooks, Python | `__version__ = "x.y.z"` |
| Workflows — `.claude/workflows/*.js` | `// Version: x.y.z` comment, **below** the `meta` block |
| Mods — a Claude Code plugin under `core/tools/<mod>/` | `"version": "x.y.z"` in its `.claude-plugin/plugin.json`, once per mod |
| Templates a model reads | frontmatter |
| Templates a script stamps | **none — must not carry one** |
| Test files | none — a test is proven by running; the version that moves is its subject's |

The marker takes the file's native form — frontmatter where frontmatter exists, a header comment
where it does not, `__version__` in Python, a plugin manifest's `"version"` for a mod. Presence is this file's rule; the form is the format's
own convention. A kind not listed here is decided by the test, not by the table.

**A Python package carries its version once.** Where `core/tools/` or `.claude/hooks/` groups
several modules into a package (a directory with an `__init__.py`), the `__version__` marker lives
in that `__init__.py` only, following `package.__version__` — the Python convention. Its
submodules carry none; the package is the versioned unit, not each file inside it. Decided
2026-08-11, alongside the sweep that first populated `core/tools/auditrun/__init__.py` and
`core/tools/coldread/__init__.py`.

**A mod carries its version once, in its manifest.** A mod is a Claude Code plugin, and the
plugin's own format puts its version in `.claude-plugin/plugin.json`. Its hooks module, its
contract and its tests carry none: the mod is the versioned unit, as a Python package is.

**A saved Workflow script's marker sits below its `meta` block, not above it.** Every other
header-comment kind in the table puts the marker at the head of the file; a workflow cannot, and the
reason is a fact about how these files are tested rather than a preference. A workflow is not an
importable module, so a test that executes its real bytes strips the one `export` with
`source.replace(/^export const meta/, 'const meta')` — **no `m` flag**, so the anchor is the start of
the file — and asserts that the replace changed something. Any text above the block makes
that a no-op and trips the assert; a second `export` makes the compiled `AsyncFunction` body a syntax
error, which rules out `export const version` too. So the marker follows the block. Decided 2026-08-24,
the same day the four scripts were first stamped, all at `1.0.0` — a first marker on an existing file
states no history, following the 2026-08-11 sweep (`2c6ca752`) that gave sixteen of eighteen a bare
`1.0.0`.

## Templates — the stamper's code is the proof

The template layer is the one place both classes live, so the ruling there is per template, proven
by the stamper that reads it:

- A template a **model reads** never copies bytes into the product — the model authors a fresh
  document, the frontmatter stays behind, and the template carries its own `version:`
  (the `product-templates/` set).
- A template a **script stamps whole** is the product's bytes — no frontmatter, no version
  (`nemawashi_template.md`, `michi_template.md`, the `journey_*_template.md` pair,
  `system_shukuba_template.md` and their kind).
- **Stripped stamping is model-facing metadata riding a script path.** As stamped on 2026-08-11:
  `spawn_satellite.py`'s `_stamp_overlay` and `_stamp_pm_overlay` split off the template's
  frontmatter and comments and restamp the instance overlay fresh at `version: "1.0.0"`, so
  `overlay_template.md` and `pm_overlay_template.md` carry a template `version:` that provably
  never lands. `_stamp_cross_role` strips comments only — a frontmatter on
  `cross_role_template.md` would land in every satellite spawned after it, and that template's own
  metadata block records the choice: "No frontmatter, matching the instances on disk." **A template may carry a `version:`
  only where its stamping path provably keeps the marker out of the product — and the stamper's
  code is that proof, re-read before any marker is added.**

## What tracks a script-facing file instead

No marker is not no history. A script-facing file's change record is `git log` on the file, and its
description lives in its manifest entry — `kensaiapp_structure.md` § Templates layer, the entry
`core/templates/README.md` § Adding a script-facing template requires when one is added.

## A version is not a resync

A bump says the source moved. It does not say which stamped copies moved with it: a stamped file is
a real per-instance file, and nothing compares or resyncs one today. Read a version as a
statement about the source, never as a claim about the galaxy.

## Bump semantics — every versioned artifact

- The marker is **bumped by the commit that lands the edit on `main`**, on every substantive change
  — the same commit when the edit is committed directly, the **merge commit** when it arrives on a
  branch. **A branch never edits a version marker.** The counter is shared by every branch at once,
  so two branches bumping it is a conflict by construction, not bad luck — and a conflict there
  stops an unattended merge inside the repo everything else works in.
- **The commit path enforces the branch half of that rule.** On a branch with a local `main`,
  `commit_builder.py commit` refuses an existing artifact whose marker differs from `main`. It
  allows a rename that preserves the marker, a genuinely new versioned artifact at `1.0.0`, and a
  new file at another version whose bytes equal a file at a source declared with
  `--copied-from <repo> <revision>`. The declaration is recorded against the branch, at the commit
  the revision resolved to, and holds for every later commit on that branch.
  The check runs after the builder has assembled the final staged set and before `git commit`; it is
  provider-neutral, so forgetting the rule in a Claude or Codex session cannot land the invalid
  commit. A repository with no local `main` is outside this instance's landing convention and the
  generic builder leaves it alone.
- **The landing commit's bump reads every form in the table.** `commit_builder.py merge --bump`
  moves a frontmatter `version:`, a Python `__version__`, a workflow `// Version:`, a mod's
  `plugin.json` `"version"` and a shell `# Version:` header alike, so no marker is set by hand and
  none is exempt for being an executable. A shell header is the one form it does not rewrite in place: it **prepends** a new
  entry above the current one, carrying the merge's own one-line description. Do not rewrite such
  an entry's digits — that header is a changelog stack whose topmost line says what *that* version
  changed, so moving the number leaves the previous change's note under it. `commit_builder.py
  markers --base <ref>` is the check for the rule above it: it names every file whose marker moved
  between `<ref>` and the working tree and exits non-zero, so a branch can be proven clean before it
  lands rather than trusted to be.
- **No artifact upstream of the landing commit locks a version value.** A planning artifact — a
  `change_spec`, a `tl_instruction`, a brief — may classify a bump's **level** (patch / minor /
  major: a judgment about the change, made where the change is understood) and never the resulting
  **number**: the value exists only at the commit that lands the edit, computed there from the
  marker as it then stands, so an upstream artifact enumerating target values is directing the
  branch to edit the marker — the rule above, broken by instruction. A marker a branch edited
  anyway is a defect the merge **surfaces**, recorded in the merge's own context — never silently
  re-bumped, never silently skipped, whether the branch bumped one of the change's markers or all
  of them. Do not make the landing commit's bump idempotent (bump-unless-already-bumped): it would
  absorb exactly the deviation that must surface.
- **patch** (x.y.Z) — typo, formatting, a pointer touch-up. **minor** (x.Y.0) — a rule added or
  changed. **major** (X.0.0) — a rewrite, or removing/inverting an established rule.
- **When the change is to an enumeration** — a manifest entry, an index row, a registry value,
  wherever it sits — the same three digits read against the **entry**: **patch** re-expresses one
  without changing what it names; **minor** adds one, drops one, or corrects a wrong one; **major**
  re-cuts the enumeration itself — its key, its granularity, or its scope — so entries other files
  already cite have to be re-read.
- New versioned artifacts are created at `1.0.0` in their first commit, except a verbatim copy of a file in another repository, which keeps the version its source carries.
- The semantics are one set whatever the marker's form — a `# Version:` header and a `__version__`
  move by the same three digits as a frontmatter.

## Out of scope

- **Skills (`.claude/skills/`)** — by the owner's call (2026-08-11), this file does not decide
  whether a `SKILL.md` carries a marker or when one moves. The kaizen layer does: `../kaizen/skills.md`
  § *The version's three digits* reads the digits below against a skill and names who makes the bump,
  `../kaizen/fix_packet.md` carries it inside a round, and `../kaizen/ratification.md` owns what a bump
  ends. **The digits themselves are the ones above** — one set across every artifact, per § *Bump
  semantics*. How a commit records the skill that produced its output is `commit_format.md`
  § `Skill-Version:` trailer, and stays there.
- **A product's own documents** — a PRD or SRS carries its own `**Version:** <n>` line, owned by
  its template (`product-templates/prd_template.md` and siblings). A product's artifacts version by
  the product's rules, not the instance's.

## The measurement this rule was cut from

Measured 2026-08-11, the day this file was written: prompts were 8/8 versioned and launchers 10/10
— perfectly consistent with no rule to cite — while the hooks were 0/9 (non-test), thirteen of the
fifteen non-test Python modules under `core/tools/` carried no `__version__` (every shell script
there had a `# Version:`), and `cross_role_template.md` stood apart from its two versioned
siblings. The habit deserved to be the rule; the pockets it never reached are gaps by rule now,
not by taste.
