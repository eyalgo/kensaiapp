---
version: "1.1.1"
---

# Lens — containment

**Your question: is every fact in this file true for every reader the file has?**

Not a lens in the set's own sense: you read a stack file's own text, not an artifact it
produced.

Where a file sits fixes who reads it. A `<CORE>` prompt is read by every instance that binds
this core; a role loader by every session that opens that seat; a template by every file
stamped from it; a skill by every satellite whose launchers grant its group. A fact
true of one instance, one satellite, one product or one project, sitting in a file with that
reach, is inherited by every reader it was never true for — and nothing fails, because the
sentence is correct where it was written.

`<CORE>/doctrine/governance/system_anatomy.md` § the dependency direction owns the rule —
each layer may depend downward but never names upward.
`<CORE>/doctrine/setup/shared_core_instance.md` owns what a host and a satellite may know of
each other. This lens is how a read finds a breach of either.

**Settle the reach first.** Who opens this file, and how many of them are there? Every check
below is measured against that answer, and a finding that skipped it is an opinion.

Then walk the file:

- **Sweep every proper noun, and sweep the whole class.** Instance, satellite, host, galaxy
  member, project, product, vendor, company, domain. The class is the point: a sweep that
  enumerates products and stops has passed a file whose first lines name an instance.
- **Sweep retired vocabulary the same way.** A term kensaiapp has stopped using is a fact
  that is no longer true of it, so it belongs to this lens rather than to a style note. The
  sea metaphor — `fleet`, `armada`, and a Michi or project that *docks* — was retired
  2026-08-27 for the astronomical one: a **galaxy** is every instance on the machine, a
  **solar system** is one instance, a **planet** is a project, and `satellite` and `host`
  are unchanged. History is deliberately not swept, so the retired words survive in files
  that are still worked. **Any file you open that still carries one is updated as part of
  that turn** — including a seed lifted from `nemawashi/unpicked/`, which is updated before
  it is worked. What is *not* a finding: a trail, a `parked/` or `unpicked/` file nobody
  opened, `docs/proposals/`, a finished run's own record under `system/projects/<name>/docs/`,
  or a generated fixture — a record is left as it was written.
- **Read the frontmatter as text.** Metadata is where a name survives longest, because a
  reader inventories the keys and moves on. `author:`, `owner:`, a path inside a `metadata:`
  block, a default in a config — each is a value nobody reads twice.
- **Does it name a real project?** `system/projects/<concrete-name>/` where the shape was
  `system/projects/<name>/`. A product's own vocabulary — its domain, its users, its units —
  travels the same way and is harder to see, because it reads as subject matter.
- **Is a sentence true of exactly one case without naming it?** The one that earns this read.
  It reads as general, no reader stops at it, and it holds for exactly one setup you can
  picture — a directory only this instance has, a seat only this galaxy runs, a count of
  things only this instance can see. Picture a second reader and check it still holds there.
- **Does it reach upward?** A `<CORE>` file reading an instance's `system/`, a shared
  launcher looking up a roster, a template pointing into a real project. It works today
  because the thing it reaches for happens to exist here.
- **Would a satellite spawned tomorrow inherit this?** What separates a defect from a
  nuisance: a leak in a stamped or shared layer is copied forward silently, and the copy has
  no way to notice it was never true.

**Perform the sweep. Do not assert it.** Three reads of one skill each reported that no
instance name appeared anywhere in it, over a file whose sixth line was an `author:` field
naming the instance that wrote it — one of those readers having run greps, and a fourth
having inventoried that very line and named the key without the value. A clean claim here is
a measurement, so show it:
name what you swept for, and quote what you cleared. An unshown sweep costs more than a miss,
because it is filed as proof.

**You need no owner to file a finding here.** A fact outside a file's reach belongs nowhere
else — there is no other document that should have held it instead. So do not go looking for
one before filing: the finding is the mismatch between the fact and the readership, and that
is complete on its own.

**What is not a finding here.**

- **A pointer into `<CORE>`.** Core is shared by every instance, so naming it names nothing
  instance-specific.
- **A placeholder** — `<name>`, `<project>`, `<instance>`, `<scope>`.
- **The host named in `.env` / `.env.example`.** The `CORE=` binding is how a satellite
  reaches its host: the mechanism, not a leak.
- **A worked example in the file that owns the concept.** A document about the host/satellite
  split names a satellite because naming one is what that document is for. The test is
  whether the file owns the fact it names.

**Where the automated floor is.** `<CORE>/tools/test_templates_are_instance_neutral.py` fails
a known instance name or a real project path in `core/templates/`. Two shapes, one directory,
exact-case substring match. Everything else is yours.

**The sharp case is the one that is currently true.** *"In this satellite, the evidence it
reads lives there"* is accurate, and useful to the reader who is in that satellite, and wrong
for every other reader of the file. Accuracy is not the test. Reach is.
