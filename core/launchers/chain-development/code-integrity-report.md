# Code integrity report — chain-development, the /development pipeline as a chain of launchers

This is the `development-code-integrity` pass over branch `2026-09-15_chain-development`, closed by
the implementer's marker `5e039e65`. It found one defect against the stated intent and fixed it. It
added six tests that ran the engine against the real contracts instead of fakes, and all six held. It
also found three things the intent does not settle, which are left for the owner below.

**Reviewed:** 2026-09-15 · interactive mode, by the Senior Engineer, who did not write this code.

## Verdict

**Red, then green.** One defect: the terminal message's shape differs from the plan's
(`core/tools/chain_development.py:496`). The intent-derived tests that caught it are committed failing
in `9cbd19c3`. The fix is committed green with this report.

## What was reviewed

| File | Role |
|---|---|
| `core/tools/chain_development.py` | the engine: step table, disk reader, walk, ports, CLI |
| `core/tools/test_chain_development.py` | its suite |
| `core/launchers/chain-development/launcher.sh` | the owner's entry command |
| `core/launchers/chain-development/test_chain_development_launcher.py` | its contract suite |

`git diff --stat main...HEAD` at the start of the pass also listed `core/doctrine/flow/folder_state_handoff.md`,
`core/doctrine/setup/kensaiapp_structure.md`, `core/tools/test_detach_watcher.py` and
`core/tools/test_launcher_instrumentation.py`. They were read for consistency with the code and not
re-tested.

## The intent it was checked against

Not the implementation, and not the marker's divergence notes (those were read only to know what to
look at):

- The approved plan, `~/.claude/plans/plan-something-like-development-frolicking-crystal.md`: § Facts
  (the done-when table, :46-54; halts, :58-61), § Design (:75-122) and § Verification (:161-176).
- The seed `system/projects/product-development/journey/nemawashi/unpicked/2026-09-11_the-loop-is-a-chain-of-runs-one-per-step.md`:
  the station `the-next-step-starts-when-the-file-lands` (:83-87) and § Rulings this carries (:76-79).
- The contracts the engine relies on, each read at its source:
  - `core/launchers/skill/launcher.sh` (the argument rules at :42-48 and :254-290)
  - `core/tools/detach_watcher.sh:317-343`
  - `core/tools/watch_agent.py`, `HookOutcome` (:184-204) and `run_on_complete_hook` (:654-676)
  - the `launcher.md` of all seven step skills
  - `development-worktree/SKILL.md:19`
  - `development-specs/SKILL.md` § Outputs (:206)
  - `development-implementation/SKILL.md:268`
  - `development-audit/SKILL.md` Step 0 (:48-73) and its commit (:158)
  - `tobiishi-seal/SKILL.md` Steps 1-4 (:93-304)
  - `core/doctrine/flow/folder_state_handoff.md`

## The finding

**The terminal message did not read the way the plan states it.** Plan § Design, *One terminal
writer* (:110-111), gives the owner's message as `<instance> · <p> · development chain — sealed <key>`
or `stopped at <step>: <reason> (<pointer>)`. `_end` joined the headline to the message with a bare
space, so the owner's phone read:

```
instance · tracker · development chain sealed 2026-09-15_add-due-dates — suite unrecorded …
instance · tracker · development chain stopped at specs: the run ended timeout
```

**The fix** is one character run at `chain_development.py:496`: `f"{headline} — {what}"`. Both
messages now start `… development chain — sealed <key>` and `… development chain — stopped at
<step>: `.

**Two parts of the plan's shape are deliberately not pinned.** The `(<pointer>)` parentheses are not
pinned, because the plan defines no pointer for a halt that left no report. The start message (`:355`)
is not pinned either, because the plan states no shape for it.

## Tests added

Eight tests in `core/tools/test_chain_development.py`, under the banner
`development-code-integrity, 2026-09-15`. Every docstring quotes the plan clause or the contract it
checks. The launcher suite gained nothing: the plan's § Tests list for it was already covered, and
its one open item is a decision (below).

| # | Test | Why |
|---|---|---|
| 1 | `test_the_sealed_message_reads_the_way_the_plan_states_it` | **red**: the finding above |
| 2 | `test_the_stopped_message_reads_the_way_the_plan_states_it` | **red**: the same, on a halt |
| 3 | `test_a_walk_that_halted_on_a_missing_artifact_is_re_entered_at_that_step` | plan Verification 4: one stop message naming the step, then a re-run enters at that step. The existing suite only re-entered after a *launcher* failure at specs |
| 4 | `test_every_argv_the_engine_builds_is_accepted_by_the_real_skill_launcher` | all ten argvs of a whole walk run through the real `core/launchers/skill/launcher.sh --dry-run` against this repository's real `launcher.md` files. An argument count or shape a `launcher.md` does not declare would be refused here. The suite had only checked that each `launcher.md` exists |
| 5 | `test_the_shim_fired_by_the_real_watcher_hook_returns_at_once_and_advances_the_walk` | the real `watch_agent.run_on_complete_hook` fires the real shim from a different cwd, with spaces in every path. The hook returns in under 3 s while the next step's stub launcher sleeps 4 s, and the detached engine still launches that step and writes `chain-development-<p>.log`. The suite had only checked the shim's *text* |
| 6 | `test_four_audit_ends_arriving_together_release_exactly_one_seal` | four real `--advance` processes, started at once on the real `flock`. Exactly one `tobiishi-seal` launch, all four audits recorded, and a second delivery of each launches nothing. The suite's lock tests were a fake that records holds, plus a single-process exclusivity check |
| 7 | `test_a_whole_walk_reaches_sealed_against_a_real_repository_laid_down_by_the_contracts` | a real git repository. Each step's evidence is laid down with the commands and **literal paths its own skill states**, never with `ChangeLayout`: `git worktree add -b <key> .worktrees/<key>`, the marker subject, audit branches cut from `<key>` committing `flow_findings/<step>.md`, and the seal's join, `git mv` to `trail/`, `--no-ff` merge and teardown. The walk ends `sealed`, all four audits read `findings recorded`, and a new start is refused as `no active change`. The existing whole walk used fakes keyed by the test's own copies of the engine's paths |
| 8 | (test 4's first draft) | **wrong, and fixed before the red commit.** It looked for `change key <key>` in the dry-run output, but the launcher prints the prompt through `printf %q` (`skill/launcher.sh:379`), which escapes spaces. It now checks the launcher's own `Argument:  <name> <value>` lines (`:288`) |

The three real-process tests (5, 6, 7) ran five times in a row after the fix, and passed all five:
`3 passed, 86 deselected` each time.

## Checked and clean — the questions a green suite could have been lying about

- **A whole walk reaches sealed against the real contracts' paths and names.** Yes (test 7). The
  change-branch artifact folder, the `main..<key>` marker reading (the same `implementation complete`
  substring `tobiishi-seal/SKILL.md:112` greps), the `<key>__audit-<step>` branch with
  `flow_findings/<step>.md` at the pre-move path, and `trail/<key>/` on `main` all match.
- **`advance()` is idempotent under a duplicate or concurrent end.** Yes (test 6). The run leaves
  `pending` and is saved under the lock before anything is decided, so racing deliveries are safe.
  The lock's fd is taken with `os.open` and released explicitly, so a launched watcher cannot keep
  it held. Measured 2026-09-15 while `FileLock().hold()` was open: `os.get_inheritable` on the only
  open fd above stderr returned `{3: False}`.
- **The shim's detached engine runs from the watcher's hook.** Yes (test 5). Quoting, cwd
  independence and the log path all hold. The detachment is what keeps a four-audit fan-out out of the
  hook's `timeout=60`.
- **The start refuses or enters correctly on every disk state the plan names.** Yes:
  - no change, and two changes, are refused
  - a live walk is refused
  - an ended walk does not block a new start
  - the entry step is right at each of the seven states
  - a sealed change is refused, and on a real repo that refusal comes from discovery
    (`no active change`), because the seal moves the folder
- **Rulings held.** `git diff --stat main...HEAD` touches no `development-*` skill, no `tobiishi-seal`,
  no `development-audit`, no `/development` skill, and not `.claude/workflows/development.js` (seed
  :76-79).

## Three things to decide, not fixed here

**1. With no notifier set, a walk launches its first step and never advances.**
- `detach_watcher.sh:317` detaches the watcher only when `[ -x "$notifier" ]`, and only a detached
  watcher passes `--on-complete` (`:342-343`).
- This launcher resolves `NOTIFIER="${KENSAIAPP_NOTIFIER:-}"` (`launcher.sh:59`) and documents an unset
  one as "skipped, never an error".
- So with `KENSAIAPP_NOTIFIER` unset, the first run's end wakes nothing and its entry stays in
  `pending`. Every later start is then refused as still walking (`chain_development.py:342`) until
  the state file is deleted by hand.
- `chain-definition/launcher.sh:77-81,141` carries the same layering, so this is shared with the
  document chains, not introduced here.
- It is not fixed because the options change different owners' surfaces: the launcher could refuse
  without an executable notifier, the engine could refuse at start, or `detach_watcher.sh` could run
  the watcher whenever an on-complete hook is set. Choosing among them is a decision.

**2. A seal that halts after moving the folder on the branch cannot be resumed by the chain.**
- `tobiishi-seal` Step 2 runs `git mv` on the folder to `trail/<key>` on the branch (`SKILL.md:187`).
  A Step 3 merge failure then halts and leaves the branch and worktree intact (`:283-289`).
- A re-run of the chain reads each folder artifact at `.worktrees/<key>/…/tobiishi/<key>/`
  (`chain_development.py:124,165`). That path has moved, so the walk enters at **specs**, not seal.
- Entering at seal would not help either: the seal's own precondition requires the un-moved folder
  (`SKILL.md:108`) and would refuse.
- Resuming a half-sealed change is therefore the seal skill's, and the skills are out of scope by
  ruling. Also recorded: the halt message for this case says `no trail/<key>/ on main`, not a
  report path, because `tobiishi-seal` does not state where its `halt_report.md` lands after the
  move.

**3. `--dry-run` does not print the resolved key or the entry step.**
- Plan § Verification 2 (:165-166) says it does. The launcher prints the project, the product path
  and the engine argv (`launcher.sh:94-107`).
- Plan § Design 2 (:116) makes the launcher "a copy of `chain-definition/launcher.sh` with three
  changes", and that sibling's dry run consults no engine either.
- Printing the key and entry step means a read-only engine entry point, a new CLI surface, and the
  plan contradicts itself on whether it is wanted.

## Observed, not defects

- **A halt's pointer can name an earlier step's report.** When a step ends with no artifact,
  `_settle` cites the first `halt_report.md` it finds (`chain_development.py:402-405`). A report left
  by an earlier, since-repaired step would be named. The walk still stops at the right step, and the
  plan (:105) does not distinguish reports by age.
- **Re-entering at the audit relaunches all four audits**, even where some findings already exist
  (`:430-431`). `development-audit` Step 0 stops on an existing branch (`SKILL.md:61`), so those runs
  end with nothing new and the walk proceeds. That costs runs, not correctness.

## Language resolution

- `system/projects/product-development/project.md` declares no `Languages:` (its only header fields
  are `Product path:` at :3 and `Test command:` at :7), and the plan names none.
- Resolution therefore reached **step 3 of `core/doctrine/engineering/languages/README.md` § The
  resolution chain, inference from file extensions**, logged here as an inference.
- `.py` resolved to the **Python** packet and `.sh` to the **Shell** packet (registry, `README.md:23,25`).

| Packet | Concern | Destination read | What it gave this review |
|---|---|---|---|
| Python | Quality gates | `python/quality_gates.md` | `python3 -m compileall -q` exit 0 as the compile gate; pytest exit `5` means nothing was collected |
| Python | Conventions | `python/conventions.md` | the 100-column rule (:16): **three lines this pass added were over it and were re-wrapped**; double-quoted strings; `from __future__ import annotations` first; no annotations on `def test_*` |
| Python | Testing | `core/doctrine/engineering/testing_python.md` (routed outside the packet) | the seam is a fake passed to the constructor, never `monkeypatch.setattr` on the subject (:31). The new tests hold: they use fakes or the real ports through `DevelopmentChain`/`build_chain`, and `monkeypatch` only for `setenv`/`chdir` on the process environment, which :32 says the rule is not about |
| Shell | Quality gates | `shell/quality_gates.md` | `bash -n` exit 0 as the parse gate; no ShellCheck installed (:51-56) |
| Shell | Conventions | `shell/conventions.md` | the opening three lines: `launcher.sh:1` shebang, :2-40 header, :41 `set -euo pipefail` |
| Shell | Testing | `shell/testing.md` | Technique 1, the real script in a fixture instance with the outside stubbed: the existing launcher suite already has that shape, and test 4 applies it to the skill launcher |

Toolchain, Layout and Errors-and-logging were not re-read: no dependency, file placement or failure
path changed in this pass.

## Numbers

| Suite | Command | Result |
|---|---|---|
| Named, before this pass | `python3 -m pytest core/tools/test_chain_development.py core/launchers/chain-development/ -q -p no:cacheprovider` | `103 passed` |
| Named, red (`9cbd19c3`) | same | `2 failed, 108 passed` |
| Named, after the fix | same | `110 passed` |
| Plan Verification 1, after the fix | `python3 -m pytest core/tools/test_chain_development.py core/launchers/ -q -p no:cacheprovider` | `1529 passed` |

Gates after the fix: `python3 -m compileall -q core/tools/chain_development.py core/tools/test_chain_development.py`
exits 0, and `bash -n core/launchers/chain-development/launcher.sh` exits 0.

## Version markers

**None moves.** `chain_development.py` carries `__version__ = "1.0.0"` and `launcher.sh` carries
`Version: 1.0.0`. Both files are new on this branch, and a branch never edits a version marker: the
merge sets the number. The test file and this report carry no marker, per
`core/doctrine/governance/versioning.md`.

---

# Code integrity report — the dry run that describes, 2026-09-15

This is the `development-code-integrity` pass over branch `2026-09-15_chain-dry-run-describes`, closed by
the implementer's marker `81d83b80`. It found one defect against the stated intent and fixed it. It
added 38 test cases, and all the engine's held.

**Reviewed:** 2026-09-15 · interactive mode, by the Senior Engineer, who did not write this code.

## Verdict

**Red, then green.** One defect. When the engine's `--describe` exited 0 without naming both the
change and the entry step, the dry run still printed the `DRY RUN` block and exited 0
(`core/launchers/chain-development/launcher.sh:117-121`). The tests that caught it are committed
failing in `cc60c9f5`. The fix is committed green with this report.

## What was reviewed

`git diff --stat main...HEAD` at the start of the pass:

| File | What changed |
|---|---|
| `core/tools/chain_development.py` | `StartPlan`, `DevelopmentChain.describe`, `start` calling it, `main()`'s `--describe` |
| `core/tools/test_chain_development.py` | the describe and `--describe` tests |
| `core/launchers/chain-development/launcher.sh` | `--dry-run` asks `--describe` first |
| `core/launchers/chain-development/test_chain_development_launcher.py` | the dry-run tests, the stub's `--describe` branch |
| `core/doctrine/setup/kensaiapp_structure.md` | the engine, launcher and suite entries |

The doctrine entries were read against the code and not tested. All three still say what the code
does after the fix.

## The intent it was checked against

The approved plan, `~/.claude/plans/plan-something-like-development-frolicking-crystal.md`: the outcome
(:12-14), § Design 1-2 (:18-48), § Tests (:50-72) and § Verification (:95-106). The marker's
Implementer Review Notes were read to know where to look, never as the reference.

## The finding

**A describe that answers with exit 0 but no answer produced a dry run that reported one.** The plan
says a dry run "names the change the walk would carry and the step it would enter at" (:12-13). It
also says "a dry run that reports a command the real run would refuse is a dry run that lies" (:42-43).
The launcher checked only the exit status (`launcher.sh:116`). It then read `key=` and `entry=` with
`sed` and echoed whatever came back, empty or not. Five shapes printed `chain-development: change=`
(blank), then `DRY RUN — would run:`, then exit 0:

- no output
- an unrelated line
- `key=` alone
- `entry=` alone
- both present but empty

An engine that ignores `--describe` answers exactly this way. The stub this suite used before the
change is one: it printed `engine-stub: started` and exited 0.

**The fix** is one guard at `launcher.sh:121`, in the shell packet's form
`[ <condition> ] || die "<what was wrong>"`:
`[ -n "$change_key" ] && [ -n "$entry_step" ] || die "…named no change and entry step — it said: …"`.

## Tests added

Every docstring or banner cites the plan clause it checks.

**Engine suite, `core/tools/test_chain_development.py`:1469-1630.** 7 tests, 28 cases.

| Test | Why |
|---|---|
| `test_describe_and_start_answer_alike_on_every_shape_of_state_file` (13 cases) | The plan says "cannot drift apart". The state files covered: missing, empty, unparseable, JSON `null`, `[]`, `["specs"]`, wrong schema with and without `pending`, `pending` empty or `null`, ended with `pending`, sealed, and live. For every one, both calls refuse with the same exception and message, or both enter at the same step. The implementer's tests used no state file except a live one. |
| `test_describe_and_start_agree_at_each_of_the_seven_entry_steps` (7) | Plan § Tests: "on each disk state". The implementer's agreement test covered 4 of the 7 states. |
| `test_a_refusal_reads_word_for_word_the_same_from_describe_and_from_start` (3) | The plan says "the same reason". The implementer's tests matched substrings, one caller at a time. |
| `test_describe_names_only_the_flag_it_was_not_given` (2) | Plan: "A missing flag names itself". The implementer's test left out both flags at once. |
| `test_describe_that_crashes_sends_nothing_even_when_the_state_names_a_notifier` | The plan says it "never sends". This is the exit-5 path, with a notifier named in the state. |
| `test_a_notifier_handed_to_describe_is_never_invoked` | The CLI accepts `--notifier` beside `--describe`, and a refusal still sends nothing. |
| `test_describe_does_not_wait_on_a_lock_a_live_walk_holds` | Plan: "no reason to wait on a live walk's lock". This process holds the real `flock` while the real engine answers `--describe` in a subprocess, with a 15 s timeout. The implementer's test used a `FakeLock` only. |

**Launcher suite, `test_chain_development_launcher.py`:324-411.** 5 tests, 10 cases. The engine stub
gained `DESCRIBE_STDOUT`, `DESCRIBE_STDERR` and `DESCRIBE_EXIT`, so a test can make describe crash,
say nothing or add noise.

| Test | Why |
|---|---|
| `test_a_describe_that_crashes_fails_the_dry_run_with_what_the_engine_said` | Exit 5 with a traceback fails the dry run, with the exception line on stderr and no `DRY RUN`. Held. |
| `test_a_describe_that_exits_zero_without_naming_the_change_and_step_fails_the_dry_run` (5) | **Red.** This is the finding above. |
| `test_stderr_noise_from_a_successful_describe_stays_out_of_the_change_and_the_step` | Held. |
| `test_the_dry_run_leaves_no_temporary_file_behind` (2) | The plan says a dry run "writes nothing". With `TMPDIR` pointed at a scratch folder, it stays empty on both the answered and the refused path. Held. |
| `test_with_no_active_change_the_real_engine_fails_the_dry_run_and_writes_nothing` | Plan Verification 2 in a scratch instance, with the real engine. Held. |

**The new tests are not green by accident.** Two defects the plan forbids were planted in a scratchpad
copy of the engine, and the new engine tests were run against each:

| Planted defect | Result |
|---|---|
| The exit-5 path sends to the state's notifier | `1 failed, 28 passed`. The failure was the crash test. |
| `describe` takes the lock around the live-walk check | `2 failed, 27 passed`. The failures were `…writes_launches_locks_and_says_nothing` and the real-flock test, which hit its timeout. |

## Checked and clean — the questions a green suite could have been lying about

- **Can describe and start disagree?** No. `start` calls `describe` inside its lock
  (`chain_development.py:361-365`). The three agreement tests above hold across 13 state shapes,
  7 entry steps and 3 refusals.
- **Does `--describe` ever send, including exit 5?** No. The chain is built with `Notifier("")`
  (`chain_development.py:640`), and `Notifier.send` returns before running anything when its command
  is empty (`core/tools/chain.py:337-339`). The crash test and the planted defect confirm it.
- **Does the dry run fail correctly on unexpected engine output?**
  - A crash with a traceback: yes.
  - Stderr noise on success: yes.
  - Exit 0 with no `key=` line: no. That was the finding, now fixed.
- **Does the default-engine launcher test run the real engine?** Yes.
  `test_the_engine_defaults_to_the_development_chain_under_core` removes the override and asserts
  `change=2026-09-15_real`. Only the real engine can print that key: it comes from the test's own
  folder, and the stub always prints `2026-09-15_stub-change`.
- **Plan Verification 2 on this instance.** From the working root,
  `./core/launchers/chain-development/launcher.sh launchers --dry-run` exited 1. It printed
  `a start would be refused — no active change under …/system/projects/launchers/journey/tobiishi`
  and no `DRY RUN` line. `system/logs` did not exist before the run, after it, or after the fix. No
  project here holds a folder under `journey/tobiishi/` other than `trail/`.

## Observed, not defects

- **The plan says `--describe` "never builds a notifier"; the code builds one with an empty command**
  (`chain_development.py:640`). What that clause protects is "never sends", and that holds and is
  tested. The literal wording is not met.
- **A crash reads as a refusal at the launcher.** A non-zero describe of any kind dies with
  `a start would be refused — …` (`launcher.sh:116`). That includes exit 5, a Python traceback. A real
  start on the same state crashes too, so the dry run still fails where a start would; only the word
  is loose. The plan fixes no wording beyond "the engine's own reason".
- **Some state-file shapes crash both callers identically:** a JSON array, or a `pending` that cannot
  be sorted. Those shapes reach `.get` and `sorted` in `_refuse_to_overwrite_a_live_walk`
  (`chain_development.py:379-386`), which predates this change. The crash sends nothing from
  `--describe`. From `--start`, it messages the owner (`:688-691`).
- **Two things are review-verified, not tested.** The describe output going to a file rather than a
  pipe (`launcher.sh:111-113`) is one: no test can tell the two apart from outside. The three doctrine
  entries are the other.

## Language resolution

- `system/projects/product-development/project.md` declares no `Languages:`. Its header fields at
  :3-8 are Product path, Source material, Execution type, Package slug, Test command and Parallelism.
  The plan names no language either.
- Resolution therefore reached step 3 of `core/doctrine/engineering/languages/README.md` § The
  resolution chain, inference from file extensions. It is logged here as an inference.
- `.py` resolved to **Python** and `.sh` to **Shell** (§ The language registry).

| Packet | Concern | Destination read | What it gave this review |
|---|---|---|---|
| Python | router | `python/README.md` | Testing routes outside the folder, to `testing_python.md`. That file was not re-read this pass. The new tests use the suite's existing hand-written fakes and `build()`, and patch nothing on the module. |
| Python | Conventions | `python/conventions.md:16` | Lines stay within 100 columns. No line this pass added exceeds it. |
| Shell | router | `shell/README.md` | Layout routes to `kensaiapp_structure.md`, and nothing in this pass moved a file. |
| Shell | Conventions | `shell/conventions.md:39` | "Comments wrap at 100 columns; code does not wrap at all." **The first draft of the fix wrapped the guard over two lines. It was put back on one line, because the packet binds over the draft.** |
| Shell | Errors and logging | `shell/errors_logging.md:12-15,55-57` | `die` is the failure surface, and a guard takes the form `[ <condition> ] \|\| die "…"`. The fix follows both. |
| Shell | Testing | `shell/testing.md` | Technique 1: the real script, in a fixture instance, with the outside stubbed. The launcher suite already had that shape, and the new tests use it. |

Toolchain and Quality gates were not opened in either packet. No dependency changed, and the gates
run were the ones the review brief named.

## Numbers

Named suite command: `python3 -m pytest core/tools/test_chain_development.py core/launchers/chain-development/ core/launchers/test_core_resolution.py core/tools/test_keep_awake_binding.py core/tools/test_agent_id_handover.py core/tools/test_launcher_instrumentation.py -q -p no:cacheprovider`

| State | Result |
|---|---|
| Before this pass (`81d83b80`) | `163 passed` |
| Red (`cc60c9f5`) | `5 failed, 196 passed` |
| After the fix | `201 passed`. The engine suite alone was `137 passed` and the launcher suite alone `34 passed`, measured before the guard was put on one line. |

Gates after the fix: `python3 -m compileall -q core/tools/chain_development.py` exits 0, and
`bash -n core/launchers/chain-development/launcher.sh` exits 0.

## Version markers

**None moves.** `chain_development.py` still carries `__version__ = "1.0.0"` (:43), and `launcher.sh`
still carries `Version: 1.0.0` (:6). The plan bumps them at the landing merge (:79-82), and a branch
never edits a version marker.
