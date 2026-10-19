# Shell — no skeleton tree, deliberately

**There is no tree in this folder, and its absence is the answer rather than a gap.** A product that
declares `shell` among its languages gets no shell frame from the skeleton launcher, and the launcher
reads this file's presence-without-a-tree as saying so: skip shell, report that it was skipped, and
do not fail.

That distinction is why this file exists at all. A folder that is simply missing and a language that
deliberately has no frame look identical to a script, and at least one real product declares `shell`
alongside two languages that do have trees — so the launcher will be asked for this one.

## Why there is nothing to copy

Shell is a registered language (`<CORE>/doctrine/engineering/languages/README.md` § *The language
registry*), so a product's card may legitimately declare it. What it does not have is an invariant
product-level frame, and every concern in its packet says the same thing from a different direction:

- **Layout routes out of the packet.** Shell is the only language whose Layout concern is answered
  outside its own folder — at `<CORE>/doctrine/setup/kensaiapp_structure.md` § *Owner-run launcher
  folder* and § *Shared-tools layer*. Those sections fix where **this instance's own** shell lives,
  `core/launchers/<identity>/` and `core/tools/`. They describe the instance, not a product. The
  packet's router says as much: *"A `layout.md` here would carry a pointer and nothing else."*
- **No build system and no package manager.** The packet's Toolchain destination opens with exactly
  that heading — *"A shell file here is run as it sits. Nothing compiles it, nothing bundles it,
  nothing installs it, and there is no manifest or lockfile to declare it in."* A frame is mostly a
  manifest and its configs; shell has neither to copy.
- **The gates are zero-config**, and the one tool that would bring a config file with it is still an
  open adoption question in the packet rather than a fixed choice.
- **Conventions and error shape are measured over this house's own scripts** — a `die()` keyed to a
  launcher's identity, `LAUNCH_<X>_<THING>` env overrides named for this instance's own launcher set.
  They describe the instance's shell, and copying them into a product would export facts about
  kensaiapp into something that is not kensaiapp.

A product's shell is a handful of scripts beside a product written mainly in something else. There is
no shape they all share, so there is nothing here that could be the same every time — which is the
whole test for what belongs in a skeleton tree.

## What would change this

A shell tree becomes possible when the packet fixes something a product's shell always has: a
convention for where a product's own scripts live that is *not* `core/launchers/` or `core/tools/`,
or a settled gate whose config file is worth copying. Both are the packet's to decide. Until then,
inventing a frame here would be settling a doctrine question from the wrong layer.

*Determined 2026-09-02 by the run that built the other trees, from this packet's own six
destinations.*
