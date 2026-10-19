---
version: "2.6.1"
---

# Step outcome contract

How a flow-* step reports its result. The chain
(`core/launchers/chain-development/launcher.sh` → `core/tools/chain_development.py`, run via
`chain-development` / `chain-change`) is this pipeline's orchestrator, and it **never receives** the
message below — it reads a step's outcome off disk instead, per § *The chain's on-disk transport*,
below.

The message this document defines is what a step returns to whatever session ran it — the human or
subagent that invoked it, not an orchestrator reading it as a spawn contract.

This is layered on, not a replacement: `halt_report.md` (the human-readable halt detail) and the
action-file pattern (`folder_state_handoff.md`) are unchanged. The contract
adds the machine-readable return value that sits on top of them.

---

## The message

Every flow-* subagent ends its run by returning this object as its final output:

```
{
  step:        "development-specs" | "development-design" | "development-plan" | "development-content" | "development-implementation" | "development-code-integrity" | "tobiishi-seal",
  status:      "ok" | "halt",
  key:         "<YYYY-MM-DD>_<slug>",   // development-specs discovers it (the active folder name); every later step echoes it
  artifact:    "<filename>" | null,     // the file written on success; null when output is code/merge
  halt_reason: "<code>",                // present only on halt
  halt_report: "<path to halt_report.md>", // present only on halt — a pointer, not content
  suite:       "green" | "red" | null,  // development-implementation only — the terminal signal
  language:    { resolved, via, packet } // development-implementation only — required, never null
}
```

- **`status: "ok"`** — the step produced its result with no unresolved blocker.
- **`status: "halt"`** — the step stopped short of its result; `halt_reason` and `halt_report` name why.
- **`key`** — the change key. development-specs discovers it (the single active `<key>/` folder name under
  `journey/tobiishi/`); every later step receives it and echoes it back.
- **`artifact`** — the file written on success (`change_spec.md`, `change_design.md`, …). `null` for
  steps whose output is not a folder artifact: development-implementation writes code, tobiishi-seal seals + merges.
- **`halt_reason` / `halt_report`** — present only on a halt: the reason code, and a **pointer to**
  `halt_report.md` — content, not a value carried in the message itself. A human reads the file for
  detail.
- **`suite`** — development-implementation only: `"green"`/`"red"`, the terminal signal that the code stage
  passed. There is no stage-5 folder artifact to derive this from, so it travels in the message.
- **`language`** — development-implementation only, and the one field with no `null` case: `resolved` (the
  language, or `"none"`), `via` (`"project.md"` | `"plan"` | `"inference"` | `"none"` — which step of the
  chain answered), and `packet` (the folder read, or `null` for the floor). **`packet: null` is a real
  answer; an absent `language` is not.** The chain's equivalent fact is a `Language resolution:` line
  in the closing commit's body (§ *The chain's on-disk transport*); its absence is what halts
  `missing-language` there. This field is required rather than optional because the two states it
  distinguishes are indistinguishable in prose: on 2026-08-21 an implementer skipped language
  resolution entirely, recorded nothing, and read exactly like a run that resolved and had nothing to
  report. A field the schema forces cannot be answered by silence. Added 2026-08-21 with the mandate
  in `<CORE>/doctrine/engineering/languages/README.md` § The resolution chain.

---

## The chain's on-disk transport

The chain (`core/tools/chain_development.py`) never receives the message above. It reads the same
outcome — `Suite:`, `Language resolution:`, `Integrity:` — off three **declared lines**, written by
the steps that already carry them in their artifacts, and the closing marker's `Deferred:` and
`Failing:` lines beside them. It reads a fourth, `Publishes text:`, from the design, before the step it
gates runs, so the chain reads **four declared lines** in all:

- **`Suite:`** and **`Language resolution:`** are read from the body of the newest commit in
  `main..<key>` whose subject contains `implementation complete` — development-implementation's
  closing marker (`.claude/skills/development-implementation/SKILL.md` Step 3). Newest, because the
  chain walks `git log`'s own order (`chain_development.py`'s `DiskReader.marker_commit`, over
  `Git.commits_ahead`), so a re-implementation's later marker is the one read.
- **`Deferred:`** and **`Failing:`** lines are read from that same marker body, every one of them,
  in body order (`chain_development.py`'s `DiskReader.deferrals` and `DiskReader.failing_cases`). A
  `Deferred:` line is the developer's declaration that it could not land a task (`Deferred: task <N>
  — <the blocked case> — <record>`, or `— depends on task <M> —`); a `Failing:` line names a failing
  case and the task it belongs to (`Failing: <case id> — task <N>`, or `— no task`). The chain reads
  them to decide two things: whether a `Suite: red` marker's red is wholly owned by deferred tasks
  (below), and which tasks the commit-shape read leaves unjudged.
- **The commit shape** is read once that marker passes on `Suite:` and `Language resolution:`, from
  three more inputs. The branch's `tl_instruction.md` gives each task's lane: a `### Task <N>` block
  with a `#### Behaviours to verify` heading and none of the five one-commit markers in its
  `#### Implement` body is TDD-lane (`DiskReader.tdd_lane_tasks`). The per-task subjects on
  `main..<key>` of the repo the change's code lands in give each task's red and landing commits, in
  that branch's own order (`DiskReader.landed_without_red`, on `DiskReader.code_repo`). And the
  marker body's re-lane note lines, `- Task <N> no red (lane d) — <reason>` or
  `- Task <N> red at baseline (lane f) — <reason>`, each with a non-blank reason, name the tasks the
  developer re-laned (`DiskReader.relaned_tasks`). A task named by a
  `Deferred:` line or a re-lane note is not judged.
- **`Integrity:`** is read from the first line of `code-integrity-report.md`, on the change branch,
  that starts with it.
- **`Publishes text:`** is read from the first line of `change_design.md`, on the change branch, that
  starts with it, when the walk reaches the `content` step. Its value is read by first word, which must be
  exactly `yes` (run the step) or `no` (pass it with no launch). `Yes`, `maybe`, an empty value, a missing
  line and a missing file are none of these, and the walk halts `missing-text-verdict` before any launch
  (`chain_development.py`'s `DiskReader.run_verdict`). Adding the line and starting again resumes it.

**The scan.** A line counts only when it is the first line, read top to bottom, whose own start
matches the prefix — after `*`, `_` and `` ` `` are stripped from both ends of the line
(`chain_development.py`'s `_EMPHASIS`). A mention of the prefix elsewhere in the line, or in a later
line, does not count. Stripping the wrapping characters means `**Integrity: pass**` is read as
`Integrity: pass`; it does not widen what counts as the value that follows the prefix — `Integrity:
Pass` is a different string from `Integrity: pass` and still fails the pass check below
(`chain_development.py`'s `DiskReader._declared_lines` and `DiskReader._first_declared_line`, the
one scan every declared line goes through). Two lines are read more loosely than that. The `Suite:`
verdict is the value's first word, so `Suite: green — 5083 passed` declares `green`; what follows is
the record and never changes the verdict (`chain_development.py`'s `DiskReader.suite_verdict`). And
the language line still counts with a parenthesised label between the words and the colon,
`Language resolution (tasks 1 to 3):` (`chain_development.py`'s
`_LANGUAGE_HEADING`). The developer skill forbids the label, but a finished, green change does not
halt on it.

**What passes:** `Suite: green`, or `Suite: red` where the marker carries at least one `Failing:`
line and every `Failing:` line names a task that some `Deferred:` line names, or `Suite: none` where
the project card on `main` reads `Test command: none` (a product with no code, so no suite); a `Language
resolution:` line, labelled or not, present with any value; on that marker, a red commit older than its oldest
landing for every judged TDD-lane task that landed; `Integrity: pass`. A `Deferred:` line is a
declaration the chain reads, not a halt and not the origin of one: with a green suite it changes
nothing but leaving its task out of the commit-shape read, and a `Deferred:` line whose task cannot
be read defers nothing.

**The halts**, each against the value on disk that gives it:

| Halt | On disk |
|---|---|
| `red-suite` | `Suite: red` not wholly owned by deferred tasks |
| `missing-suite` | `Suite: none` beside a card on `main` that names a command or cannot be read; any other `Suite:` value; or no `Suite:` line |
| `missing-language` | no `Language resolution:` line, labelled or plain |
| `missing-red-commit — task <N>[, …]` | a TDD-lane task, neither deferred nor re-laned, landed with no red commit older than its first landing — every such task named once, ascending |
| `unreadable-plan` | `tl_instruction.md` on the branch unreadable when the check runs |
| `integrity-stopped` | `Integrity: stopped` |
| `missing-integrity` | any other `Integrity:` value, or no `Integrity:` line |
| `missing-text-verdict` | `change_design.md` with no `Publishes text:` line, a first word that is neither `yes` nor `no`, or no such file, when the walk reaches `content`; the engine writes a `halt_report.md` and launches nothing |

No value the code does not read produces a ninth halt.

`core/tools/chain_development.py` is the reader. Its `DevelopmentChain._bad_verdict` method owns the first
seven reasons and their order (`missing-text-verdict` is the gate in `DevelopmentChain._launch_step`, which
runs before a step launches and so before `_bad_verdict` has an artifact to judge); the last two it returns through `_commit_shape_verdict`, which it
reaches only on a marker that passes the three before them. `DevelopmentChain.describe`, which
`start` calls first, refuses a relaunch: it calls `_bad_verdict` for each step before the entry it
would otherwise resume at, and raises rather than passing silently over a step that declared a bad
verdict. `describe` takes the product path the start takes, so a dry run judges the commit shape on
the same repo.

The first three lines are read only once a step's artifact is on disk (`Publishes text:` is read before the step it gates, above). A run that ended without its artifact
halts before any declared line is read, whether or not it left a `halt_report.md`. The chain looks
for that file only to name it in the halt (`DevelopmentChain._settle`;
`DiskReader.halt_report`).

---

## Constraints (standing rules)

- **Message for the machine, file for the person.** `halt_report.md` is human-facing — the message
  merely points at it, content rather than a value in the message itself. The chain decides from the
  declared lines instead (§ *The chain's on-disk transport*).
- **The skill stays orchestration-blind.** Returning a typed outcome is a pure function stating its
  result; it does not imply the skill knows an orchestrator called it (`system_anatomy.md`: a hand
  names no muscle).
- **No `Project:` header, on either side.** A step never reads one, and a step's artifact never
  carries one. Per-stage re-derivation of that header is what caused the diagnosed `/development`
  resolver halt. That origin sat in `.claude/skills/development-specs/SKILL.md` from this repo's
  initial commit `5e275b5a` until it moved here.

---

*Sibling to `folder_state_handoff.md` (the blackboard handoff) — that doc owns *what state
exists*; this one owns *how a step reports its result* — by declared line to the chain.*
