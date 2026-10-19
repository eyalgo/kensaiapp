# CONTEXT_PM — per-project PM context for project <name>

*The **per-project PM context**: the one thing a `pm:` session working `<name>` should carry that the
project's `journey/` doesn't already hold — the current change from the PM's view (scope / FDR-fit /
product-fit). **One item**, not a log and not a journey mirror. It sits **below** the two PM loader layers
(`<CORE>/roles/loaders/pm_global.md` + `system/loaders/pm.md`) as a project-scoped read. Kept fresh by the
change lifecycle — `tobiishi-open` overwrites it when a change opens, `tobiishi-seal` marks it done (flips
its status to `Sealed`, retaining the content) — **not** hand-edited. The **only** per-role context setup stamps: no other role is stamped one. `project-stamp`
stamps this into each project's `contexts/CONTEXT_PM.md`.*

---

> **PLACEHOLDER — lifecycle-written, not hand-edited.** Empty only before the first change ever opens for
> this project; after that it holds the current change, marked `Open` while active and `Sealed` once
> delivered.

## Current change — PM view

**Status:** <Open | Sealed>

<The active change for this project as the PM sees it: what it is, its scope boundary, how it sits against
the FDR, any product-fit note that isn't already in the journey. One item. `tobiishi-open` writes it
`Open`; `tobiishi-seal` marks it done in place — retains this content and flips the status to `Sealed`,
never empties it. Empty only before the first-ever change opens for this project.>
