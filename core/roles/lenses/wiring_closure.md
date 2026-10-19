---
version: "1.0.10"
---

# wiring_closure — a role and its machinery name things that are not there

Wiring a seat touches files in several trees, and the trees do not see each other. A loader names a
skill; a manifest enumerates an agent; a role map in code lists an actor. Each of those is a claim that
something exists, and nothing checks the claim in either direction. **The tell is a name — of a skill, a
file, a folder, an actor — written as though it resolves.** A seat can pass every check a reader would
think to run and still be missing from a registration nobody remembers.

Two directions, one shape. Outward: the role layer names machinery that is absent. Inward: machinery
enumerates a seat that is absent, or omits one that is present.

## What this lens reads

Both sides, for one seat:

- `core/roles/loaders/<role>_global.md` and `system/loaders/<role>.md` — every name they contain.
- `skills/*/.claude/agents/` and an instance's own `.claude/agents/`, `.claude/skills/`, `.claude/workflows/`, `.claude/settings.json`.
- `core/tools/commit_builder.py` — the actor-to-Role map.
- `core/doctrine/setup/kensaiapp_structure.md` — the manifest that enumerates each layer.
- `AGENTS.md`, and the user-global instruction file above it — the loader map.
- `core/doctrine/setup/adding_a_role.md` — the wiring order, which names the closure.

## The question

**Does every name written on either side resolve to something on disk, and does every seat that exists
appear in every registration that should hold it?**

## What the shape looks like

| The lens finds | Which is a defect when | Must not |
|---|---|---|
| A loader naming a skill, folder or file that is not on disk. | Nothing in the loader marks it as planned. | Report an absence the file itself records as an absence. |
| A manifest enumerating machinery that is not on disk. | The enumeration presents it as existing. | Report it when a peer file records the absence *and* the manifest points there. |
| A seat with an agent file and no row in the actor-to-Role map. | The seat's loader obliges it to commit. | Report a seat that never commits as missing a Role. |
| A skill that a loader presents as working, which declares itself a stub in its own text. | The loader states its output as produced. | Treat a self-declared stub as a hidden defect — it is a disclosed one, and the finding is the loader's silence. |
| A seat present in one registration and absent from a peer registration. | Both registrations cover the same population. | Assume every registration covers every seat; several deliberately do not. |

## Evidence this shape is real

**Instance one — outward, live for twenty-six days.**
`core/roles/loaders/scrum_master_global.md:18` named a skill (at `1ce14717`): "`retrospective` — write the process retro
for a completed TL-Dev chain". No such skill exists — `.claude/skills/` holds no `retrospective`
directory. The absence was found on 2026-07-30 and recorded then as "No `retrospective` skill exists;
no handoff folder exists." It was not acted on until the posture was restamped at `946c80af`. That finding cites the loader at line 23; the sentence is now at
line 18, which is why a citation here carries its quoted phrase and not only a number.

**Instance two — inward, found by this lens.** `core/tools/commit_builder.py`'s `AGENT_ROLE` map held
fifteen actors and no `qa` (measured before `946c80af` added `scrum-master`), while `skills/qa/.claude/agents/qa.md` exists and
`core/roles/loaders/qa_global.md:19` obliges the seat to "write and commit the verification file". The
seat is wired everywhere except the one table that lets it originate a commit.

**Instance three — a disclosed stub the loader presents as working.** At `fd939ab6e` — before the stubs
were deleted on 2026-09-29 — `core/roles/loaders/qa_global.md:30` listed "`development-acceptance-specs` — verification for
`change_spec.md`; produces and commits `acceptance_change_spec.md`". That skill's own frontmatter read
"STUB — all gates always pass; real implementation built in a later iteration", and its rules repeated
"All gates always PASS — stub only". The skill was honest; the loader did not carry the disclosure.

**Instance four — an enumeration and a peer file disagreeing about existence.** At `57df2d46~1` —
the last commit before the skill landed — `core/doctrine/setup/kensaiapp_structure.md:242` listed
the SDD skill's folder — under the runner group that held it then, a path no longer in the tree — as
"the SDD, station 5 of the definition sequence" with no marker, while
`core/doctrine/setup/setting_up_a_project.md:69` stated "**Station 5 is not: `product-sdd` has no skill
on disk**". One file recorded the absence and the other enumerated the name as present.

Four instances, in four different file kinds, is the shape.

## What this lens may not assert

- **That a named-but-absent thing must be built.** An absence may be a stated state rather than work
  owed. The finding is that one file presents as existing what another records as absent, or that
  nothing records it at all.
- **That an omission from a registration is an oversight.** Some registrations deliberately exclude
  seats — `core/doctrine/setup/kensaiapp_structure.md` § *Role layer* states "**Thirteen roles** — qa
  excluded (fork-invoked, no prefix, so no app-level loader)". An exclusion the manifest explains is
  not a gap.
- **That a stub is a defect.** A skill declaring itself a stub has disclosed its state. The finding is
  against whatever presents its output as real.
- **That the wiring closure is complete because the loader directory looks right.** Several
  registrations are invisible from there, which is the whole reason this lens reads both sides.

## Reporting

One finding per unresolved name, with the file that names it quoted, the location searched, and which
of the two sides — the namer or the registry — the finding sits against. Where another file already
records the absence, the finding cites that record and reports the age of it, because a defect found
twice and repaired never is a different problem from a defect found once.

## The lens ran clean when

- every name in both loaders was resolved against disk, including names in prose rather than in a
  skills list;
- every registration that should hold the seat was enumerated from
  `core/doctrine/setup/adding_a_role.md` rather than from memory, since the ones that are forgotten are
  the ones invisible from the loader directory;
- each skill the loader presents as working was opened and its own frontmatter read;
- every exclusion found was checked against the file that explains it before being reported;
- the lens says so explicitly when it found nothing.
