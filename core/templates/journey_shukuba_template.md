# 宿場 Shukuba — <project>'s current station

*The **project**-level post-station: the one reachable, bounded station this product is walking toward
right now — reach it, rest, name the next. Opened from the next unchecked item on the active 根回し
Nemawashi's checklist; the guardrail for the active idea. Shukuba exists at both levels as two
different kinds: this one is **walked**, while the instance's (`system/shukuba/`) is a **router** that
coordinates the projects pushing on one shared thing. `project-stamp` stamps this into
`system/projects/<name>/journey/shukuba/README.md`.*

---

**This is a folder, not a file.** There is always exactly **one** active station — its own file,
`<YYYY-MM-DD>_<slug>.md`, holding the station in full: what it is, its **reached-when**, and its
guardrail. One file, so a reached station is moved whole.

**Lifecycle.** Open a station from the next unchecked item on the active Nemawashi's checklist. Walk it
by crossing 飛び石 Tobiishi (change units). When its reached-when is met, **move the station file to
`trail/`** — skill: `shukuba-retire`, which also checks that item `[x]` on the Nemawashi and reports
whether any item is still unchecked. Opening the next station is `shukuba-open`'s, not this skill's. Never
strike a station through. `journey/shukuba/trail/` is the record of reached stations.

**Park one and it goes to `parked/`, not to `trail/`.** A station stopped before its reached-when is met
— paused, blocked, superseded, or the slot wanted for other work — **moves to `parked/`**, where it waits
until someone opens it again. Skill: `shukuba-park`, which leaves the Nemawashi item **unticked**, since
that leg is still unwalked. The two destinations say different things and neither substitutes for the
other: `trail/` is the record of stations *reached*, so an unreached station filed there claims a walk
that never happened, and a note inside the file does not correct it — the record is read by looking at
which folder things are in.
