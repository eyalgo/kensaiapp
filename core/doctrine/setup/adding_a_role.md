---
version: "1.6.2"
---

# Adding a role

Governs adding a **role** to a kensaiapp — a posture a session opens in, invoked by a `<role>:`
prefix or spawned as a subagent. A role is not one file. It is a closure of files across four
layers, and a role wired from the loader directory alone **looks done and is not**: the loader
exists, the prefix resolves, and the first run that reaches its commit step fails after doing all of
its work.

> **Single source of the tree.** Where each of these files lives — and its disposition tag — is the
> manifest `kensaiapp_structure.md`. This file does not re-list paths beyond naming which file each
> step touches. It owns one thing: **the order the steps go in, and what each step's closure is.**

Related, each owning its own piece: `skill_intelligence.md` (why a role's agent carries no model),
`commit_format.md` (the `Role:` value a role commits under), `setup_scope.md` (what a stamper may
create), `kensaiapp_structure.md` (paths, dispositions, and the counts an audit diffs against disk).

---

## The steps, in order

Each is separately committable, and each has a closure that is larger than it looks.

**1 — The global posture body.** `<CORE>/roles/loaders/<role>_global.md`, stamped from
`<CORE>/templates/role-templates/global_loader_template.md`. What is true of the role in every
instance: its lens, what it owns, its seams with the roles it is most easily confused with, its
hand-off triggers.

**Stamp the template; do not find-replace a sibling.** A find-replaced loader carries the sibling's
distinctions instead of the new role's, and the seam between two adjacent roles is the whole reason
the second one exists. The template holds the shape and can hold nothing else; a sibling always
carries facts that are not yours. Reason each section from whatever settled the role.

The template's own comment block carries the two things this step most often gets wrong: which of
the two loader shapes to use, and where the role's **improve clause** goes — in the loader for a
delivery role, in the authoring prompt for an executive one, and never in both.

**2 — The overlay template, and every enumeration of the role set.** The step with the surprising
closure. See § Step 2 below.

**3 — The instance overlay.** `system/loaders/<role>.md`, stamped from
`<CORE>/templates/role-templates/overlay_template.md`, plus the loader-map row in its
`AGENTS.md`. `AGENTS.md` is the template's bytes in every instance, so the row is written once, in
`<CORE>/templates/agents_md_template.md` (step 2), and an instance takes it by re-stamping. **The row
is a live pointer, so an instance's re-stamp lands with the overlay it names, never before.**

The overlay names this instance's paths; the global teaches what they mean. A Key-files bullet is a
path plus how `<product>` resolves — nothing more. An overlay that re-teaches the global has
duplicated a fact that will drift.

**4 — The agent, with its three registration surfaces, never without.** See § Step 4 below.

**5 — Ownership.** Where the role's output sits in the chain the system describes canonically —
`<CORE>/docs/michi_agari.md` § "Who owns each step", cross-checked against
`setting_up_a_project.md`'s station table. The two describe the same chain and must agree; read both
before adding to either.

Skip this step when the role's artifact has no settled place in the chain yet. A row asserting a
placement nobody decided is worse than an absent row — it answers an open question silently.

**6 — A cold `<role>:` open, confirmed by the owner.** The role's real test is a fresh session that
reasons its own distinctions, not a file check. **This is not the building session's to close:** the
agent registry picks up a new agent only after a restart, so the building session cannot run it.
Hand it to the owner and leave the work open until they confirm.

**7 — Every already-spawned satellite gets the overlay too.** Step 2 puts the role in
`<CORE>/tools/spawn_satellite.py`'s `ROLE_TITLES`, which makes a satellite spawned *after* this point
born with the overlay. **Nothing reaches one spawned before it.** Each already-spawned satellite
carries `system/loaders/` as a real directory of its own files, so a role that stops at step 6 is
invocable in the host and in none of them — while the loader map, the same file in every instance,
says the prefix resolves.

- **Find them in `system/satellites.md`**, never at a guessed sibling path. Placement is free, and
  that file is the record that replaces the guess.
- **Stamp each overlay from `<CORE>/templates/role-templates/overlay_template.md`**, naming *that*
  instance's own paths. Never copy the host's overlay or another satellite's: a filled-in file
  carries facts that are not the new instance's, which is the whole reason step 1 says stamp the
  template rather than find-replace a sibling. The same argument, one layer out.
- **The `AGENTS.md` re-stamp lands with the overlay it names, never before** — step 3's rule,
  holding per instance. `<CORE>/tools/spawn_satellite.py` rewrites a satellite's `AGENTS.md` from the
  template when it is re-run over that satellite.
- **It runs after step 6.** A satellite given an overlay for a posture the host has not yet proven
  inherits a shape that may still change, and three copies of a wrong shape are worse than none.
- **`python3 <CORE>/tools/check_satellites.py`** is how you see the galaxy is level afterwards. It is
  read-only and it already exists; do not write a second checker for this step.

Skip this step only when there are no satellites — `system/satellites.md` is then empty, and empty is
an answer. A host with satellites has not finished adding a role until they carry it.

---

## A role made by renaming or splitting a seat

**It has a second closure, in the host and in every satellite.** Stamping the new overlay is not all of it: every live file that named the old seat now
names one of two seats, and only a reader can tell which. Sweep each instance for the old name —
for the content split, `git -C <instance> grep -n -i -P 'content[-_ ]editor'`, outside `trail/` and
the journey — and read each hit: another role's overlay naming the seat in a seam, a `CROSS_ROLE.md`
list and its count, a doctrine line, a skill path that moved with a grouped skill, and a sentence the
new seat made false (*"the chain has no step in which …"*). The host's half is never skipped.
`check_satellites.py` sees only the mechanical half — a loader-map row with no overlay, or an
overlay still extending the old seat's loader — and none of the prose. Measured 2026-10-04, after the content seat split left them in three
satellites.

---

## Step 2 — the closure that gets missed

The reflex is "add the loader file and the `AGENTS.md` row." The role set is enumerated in roughly a
dozen places, and three of them are **invisible from the loader directory**:

- **`<CORE>/tools/spawn_satellite.py`'s `ROLE_TITLES`** — a second, *executable* enumeration. Miss
  it and a spawned satellite is born without the overlay while its own manifest says it should have
  one.
- **`<CORE>/templates/agents_md_template.md`** — the loader map every instance carries is this
  template's bytes, so the row is added here and nowhere else. `check_satellites.py` names an
  instance whose `AGENTS.md` has fallen behind it.
- **`kensaiapp_structure.md`** — the count appears in several separate sentences plus the file list,
  and they do not all count the same thing. One counts *roles*, one counts *overlays*, one counts
  *files*. Bump the doctrine version.

The rest: the two `CROSS_ROLE.md` layers that enumerate the standard set and the
`cross_role_template.md` twin, `context_template.md`, `setup_scope.md`, the `<CORE>/README.md`
loader count, and `overlay_template.md`'s own no-context role list.

**Find them by grepping, not by working from a file list.** A prepared list — even a careful one —
has been observed to miss a site a grep caught.

**Three sweeps, because one cannot reach all three shapes a count is written in.** Each was measured
missing a real site on 2026-08-30, while the Principal Architect was being wired:

```
# 1 — prose. Word-boundaried, over the enumeration surfaces.
grep -rnPi '\b(nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen)\b' <the files above>

# 2 — identifiers. NO word boundary: `_` is a word character, so `\bten\b` does not match
#     inside `TEN_ROLE_FILES` or `test_all_ten_role_layer_files_exist`. Sweep 1 returns
#     ZERO on a test file holding three such names.
grep -rnPi '(nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen)' <the test files>

# 3 — numerals. A count written as a digit is invisible to a word alphabet:
#     `<CORE>/README.md` carried `(13 role loaders)` and was found only by this form.
grep -rnP '\b(9|1[0-9])\b' <the files above>
```

**Use `-P`, never `-E`, wherever the pattern carries `\b`.** POSIX ERE has no `\b`, so
`git grep -E '\b…\b'` matches **nothing** and reports a clean tree — the filter fails silently and
looks exactly like a passing sweep. Measured the same day: a repo-wide `git grep -E` returned zero on
lines `git grep -F` found immediately.

Read every hit before changing it: some hits in these files count launchers, templates, citations,
frontmatter keys or agents rather than roles, and those must be left alone. Sweep 3 is the noisiest —
section numbers and line ranges match it — and that noise is the price of catching the one numeral
that matters.

**Test *names* carry counts and go stale on their own**, which is what sweep 2 exists for. A renamed
constant leaves sibling test names behind, and a passing test proves nothing about its name. Read
what each test actually asserts before renumbering it — they do not all count the same set. **Better
than renaming: derive the constant** from the table it shadows, so it cannot go stale again —
`core/tools/test_spawn_satellite.py`'s `ROLE_LAYER_FILES` is built from `spawn_satellite.ROLE_TITLES`
for exactly that reason, after its hardcoded predecessor silently excluded two overlays from seven
assertions.

---

## Step 4 — the agent file is stamped, not authored

`skills/<role>/.claude/agents/<role>.md` is **plumbing**. Its body is the same handful of lines every agent
carries, with the role token substituted — a pointer to the loader stack, and nothing else. Nothing
about posture, artifacts, ownership or seams belongs in it; that is what the loader stack it points
at is for.

**Stamp it from `<CORE>/templates/role-templates/agent_template.md`.** Authoring this file from
scratch is the characteristic failure of this step: the result reads plausibly, duplicates the
loader's job, and drifts from every other agent the first time the shared body changes.

Substitute the tokens and change nothing else in the body. **A two-word role uses two of them** —
`<role>` hyphenated for the `name:` and the invocation prefix, `<role_file>` underscored for the
loader filenames. `tech-lead:` reads `system/loaders/tech_lead.md`; a file that mixes them looks
right and resolves to nothing.

Two fields are the role's own, and the template names each as a slot: the `description`, which the
agent registry surfaces before any loader is read and which must say what this role does **and what
it is distinct from**; and the `tools`, which follow the role's **work** rather than the loader's prose.
**An agent file carries no `model:`.** The intelligence a run gets is set by the skill it runs, not by
the role (`<CORE>/doctrine/governance/skill_intelligence.md`), so adding a role decides no model.

**Tool grants follow the role's work, not the loader's prose.** A loader is not an allowlist: a role
that must research external references needs the tools for it whether or not its posture body has a
paragraph asking.

**The three registration surfaces land in the same commit as the file.** They are:

| Surface | Why it cannot wait |
|---|---|
| `kensaiapp_structure.md` agents list **and its count** | the count is what an audit diffs against disk; without it the agent reads as a stray file |
| `<CORE>/tools/commit_builder.py`'s `AGENT_ROLE` | without the row, the run raises on its commit step — **after** doing all of its work |
| `commit_format.md`'s `Role:` values | the enumerations *and* the role's own bullet |

**These are one step, not two.** An agent that cannot commit is not a working agent, and it fails at
the most expensive possible moment.

`AGENT_ROLE` lives in a tested module, so that edit runs the TDD lane while the rest of the closure
is structural.

---

## Two things that decide the shape

- **Does the role read a per-project context?** If not, it stamps from the generic
  `overlay_template.md`. A per-role template is earned only by something structural that no
  substitution can express — a context read is such a thing; a different job description is not.
- **Is the role's domain section ready?** It need not be. The generic template stamps an explicit
  *not declared yet* — a stated state rather than an oversight — so steps 1–3 proceed while the
  domain is unsettled. Leaving a role declaring **no** domain at all is false, not neutral.
