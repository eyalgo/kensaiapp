---
version: "3.8.0"
---

# Shared-core instance — a satellite that reads another instance's core

A kensaiapp instance gets its core one of two ways. **Standalone** — it carries its own `core/`
(vendored in; the publishable shape). **Shared-core** — it carries no `core/` of its own and reads
a host instance's, resolving `<CORE>` to the host. This file describes the shared-core kind: a
**satellite**, which may live anywhere on the machine. A producer satellite is the worked example —
it reads the host's core. The trait that defines a satellite is the shared core, not its name
and not where it sits.

## What is shared, what is linked or written from the host, what is the sibling's own

**Shared — the core store, bound by `<CORE>`.** The sibling's `.env` sets `CORE=<absolute path to
the host's core>`; the `resolve_core.py` SessionStart / SubagentStart hook reads it and resolves
the `<CORE>` token to that path. Everything under core is the host's, read live — doctrine, role
posture bodies, cross-role and pipeline contracts, setup templates. A core change is seen by every
sibling the moment it lands: zero duplication, nothing to mirror. The sibling has **no local
`core/`** by design.

**Written from the host — the hook wiring.** A satellite's `.claude/settings.json` is a real file that
`link_satellite.py` writes: the host's `hooks` key and nothing else, with each command pointed at the
host's own `.claude/hooks/` by absolute path. So a satellite holds no hook scripts and no link to
them, and an edit to a hook script in the host runs in it at once. The file is a copy of the wiring.
A hook wired into the host reaches the satellite only when `link_satellite.py` is run against it
again, and `check_satellites.py` reports the satellite as drifted until then. The hooks include
`resolve_core.py`, which is load-bearing for the binding and shareable anyway. It reads the `.env` of
`CLAUDE_PROJECT_DIR`, which is still the satellite, so one hook file resolves each satellite's own
binding.

**Linked to the host — nothing under `.claude/`.** `link_satellite.py` makes no `hooks`, `workflows`
or `settings.json` link, and removes one an earlier version made into the host — the owner's call,
2026-10-08. A launched run takes the host's workflows from its pin, so a satellite needs no
`workflows` link. `agents` is not linked either. A satellite's `.claude/agents/` is its own, so a
satellite can differ from the host one agent at a time — the owner's call, 2026-10-06.
Skills follow `--skills-mode`, and every host skill lives in a group (`skills/<group>/.claude/skills/<name>/`), so
the flat `.claude/skills` is linked in neither mode — the owner's call, 2026-10-03. A consumer is
given no skills layer at all: the launchers it runs look a group up under the host root (`<CORE>/..`)
and grant it — through the pin's plugin on the Claude path, `--add-dir` on the Codex path
(`<CORE>/launchers/skill/launcher.sh` § A GROUPED SKILL'S GROUP IS GRANTED). A producer gets the host's root `skills/` as a per-skill tree, so its
own eval output and each skill's `evidence/` (`<CORE>/doctrine/engineering/skill_evidence.md`; the host holds none) land in real directories. That is the form `link_satellite.py` gives every satellite it stands up.

**Every such link is absolute — that is the only form.** A link carries the host's full path, so it
reads the same from anywhere and a satellite can be moved without touching it. Relative was the
earlier rule, chosen so a satellite and its host moved together; it was retired because the property
only exists when the two share a tree, and not every instance does (a satellite under one root can
read a host under another). One form that always holds beats one that is meaningful for
some instances and empty for others. The cost, stated plainly: the target is a machine path, held in
a tracked file, so a clone on another machine has dangling links until `link_satellite.py` is re-run
there. The written `settings.json` carries the same machine path in each hook command, so it is right only on the machine it was written on, and re-running `link_satellite.py` there rewrites it.

**A satellite may live anywhere.** Absolute links are what buy this: they resolve from any location,
so nothing about the binding depends on the two sharing a tree. An earlier version of this file
placed a satellite beside its host as a doctrine choice — deliberately, since the links did not
require it — and `spawn_satellite.py` enforced that by refusing any other location. Both are
retired. A satellite under another root was already the standing counter-example, and a rule contradicted by the galaxy it
governs is worth less than the freedom it costs.

The consequence to hold onto: **where a satellite lives can no longer be derived.** With placement
free, a `../<name>` guess is not a location — it is a guess that happens to be right for the
satellites that sit beside the host and silently wrong for the rest. A satellite's path has to be
recorded.

**So a host carries a roster of its satellites at `system/satellites.md`.** Any instance resolves it
at `<CORE>/../system/satellites.md` — `<CORE>` is bound to the host's core, so its parent is the host
root from anywhere in the galaxy, with no sibling assumption. The roster records each satellite's path
and which of the two `--skills-mode` kinds it is (consumer / producer); it deliberately does not
record their projects, which each satellite already declares in its own
`system/projects/<name>/project.md`. One roster per host, not one per instance — a satellite has no
satellites of its own.

**The sibling's own real files — the per-instance layer.** These cannot be shared, because each
holds its own instance's truths or its own binding:
- `.env` — `CORE=<host core>`, the binding itself; untracked, written per clone.
- role loaders (`system/loaders/*.md`) — each names its own instance's truths; deliberately real,
  not symlinked.
- the instance's stamped files — `AGENTS.md`, `kensaiapp.md`, `CLAUDE.md`, doctrine stubs, `system/michi.md`, the journey
  folders — from `<CORE>/templates/`.
- `settings.local.json` — per-machine and gitignored; written fresh, never inherited from the host. Whatever the satellite sets for itself, such as its permissions and its `worktree` setting, goes here, because `link_satellite.py` rewrites its `settings.json`.
- `.claude/agents/<name>.md` — an agent the satellite overrides, and nothing else. A launched run
  takes it in place of the agent file of the same name in the host's groups. `check_satellites.py`
  lists these as overrides, and reports a `.claude/agents` that is a symlink as drift, because a
  file written through that link lands wherever the link points.

## The consequence to remember

A **core** change reaches every sibling for free. What a change to the **host's native `.claude/` layer** reaches depends on what changed. An edit to a hook script is live in every satellite the moment it lands, because each satellite's written `settings.json` runs the host's scripts by absolute path: no release step, nothing to mirror, so editing a hook here is a galaxy-wide act. Wiring a hook into the host's `settings.json`, or removing one, is live in no satellite until `link_satellite.py` is run against it, and `check_satellites.py` reports each satellite as drifted until then. A workflow reaches a satellite's launched runs through their pin. Where a satellite carries a layer as real files, nothing propagates into it and the change obliges a matching edit there — today that is the producer satellite's root `skills/` alone, which is the producer signature rather than a divergence (`satellites.md` § The two kinds). `link_satellite.py` writes `settings.json` the same way for consumers and producers, so the satellite's *kind* changes none of this.

### And nothing flows back on its own

The paragraph above is one direction. **Upward — a satellite to its host — nothing propagates at all,
by design.** A satellite reads the host's `core/` through `<CORE>` and will find defects in it; that
is expected, and three such reports on 2026-08-31 were all real and all fixed in the host the same
day. What it may do about one is settled and narrow:

- **It writes the finding to its own instance's `docs/findings/`, never to the host's** — the owner's
  call, 2026-09-12. The record stays in the instance whose run produced it, even though the broken
  file is the host's. A satellite has no write on the host's tree and could not test a change there;
  a store that accepted cross-instance writes would make every satellite's seat a committer in a repo
  it cannot run.
- **The host reads those stores by hand**, and that is the current design rather than a missing
  feature — the owner's call, same day. No harvest, no sweep, no tool.

`governance/found_while_walking.md` § *Where a surfaced defect is written down* owns both, and states
what a finding is and who writes one; this section says only that the direction is the one thing
sharing does not give you for free.

**What a channel would eventually have to preserve is not settled here and is not being designed.**
A satellite sees what it reads and the host sees the blast radius — one 2026-08-31 report named two
places where a host sweep found six — so a report upward is a starting point to re-measure from, never
a work list. That asymmetry is why the by-hand step is the owner's rather than a relay.

### So a shared file names no product

A file in `core/` or in a symlinked `.claude/` layer is read by every satellite, byte for byte. A
product name written there crosses out of the instance that owns it the moment the file lands —
no release step, nothing to review, and nothing that would show up as an event. **Name no product in a
file a satellite reads.** The owner stated it as a test: if a product's name is in the skill, it is a
leak.

**A grounding citation is where this actually happens**, because it is the one place a writer is
*supposed* to name a real case. Losing the name does not cost the claim its ground:
`system/doctrine/writing_bar.md` rule 2 — where the source cannot be given, the document states the
smaller thing it can support — covers a source that cannot cross a boundary as squarely as one that
cannot be found. What made the claim true was almost always structural (a section number with no
file, a companion named off its template's stem), and the structure is what survives. If nothing
survives losing the name, the claim was resting on the product and needed the smaller statement
anyway.

**In test fixtures the name is a stand-in and is simply renamed** — nothing about the real product is
load-bearing in a test that builds its own instance under a temporary directory.
`<CORE>/tools/check_vendor_neutrality.py --fix` does the renaming, and keeps a rewrite only where no
test that passed before fails after it. A test that exists to catch the name — a leak test with a
word list — reads the names from their source rather than spelling them, or the rename leaves it
green and guarding nothing.

**The platform a satellite builds for counts the same as a product.** No project card yields it, so
the host declares it, in `system/satellites.md` § *Names a release must not carry*. That file is
in `system/`, which a release does not carry, so writing the name there leaks nothing. A satellite's
own `kensaiapp-<word>` name is not on the list: it says nothing private, and code finds a sibling
instance by it.

**Every product name counts, not only a private one** — the owner's ruling of 2026-09-02, restated
2026-09-05. A satellite's *own* product named in a layer **every** satellite reads is still a product
name in a shared file: it tells every other instance what this galaxy builds, and none of them has
business knowing. The earlier form of this paragraph said the opposite — that a satellite's own
product leaks nothing — and that licence is why the layer kept re-acquiring names after each sweep:
between 2026-09-01 and 2026-09-05 the launcher count went from 6 to 11 without anyone breaking a
rule.

**An invented fixture name is not a product** and is not covered. Neither is a product this galaxy no
longer builds — the owner's call, 2026-09-05, on a name that survives only as a test stand-in.

## Standing one up

`<CORE>/tools/spawn_satellite.py` stands a satellite up: it creates the directory, binds `<CORE>`
through `.env`, stamps the satellite's own files from `<CORE>/templates/`, and calls
`link_satellite.py` to write its hook wiring. That run is step 1 of the sequence
`setting_up_an_instance.md` owns, and the steps after it are that file's to state.

The script does not write the host's roster. The new satellite's row in `system/satellites.md` is
added by hand, in the host.

Files always reference the `<CORE>` token, never a literal `core/…` path — the indirection design
principle in `kensaiapp_structure.md`.
