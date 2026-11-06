---
version: "1.3.0"
---

# Shell — testing

This language's implementation of the layer model in `testing_doctrine.md` — the tool, where a test
file goes, and the run command per layer. The pass/fail bar for the suite as a gate is
`quality_gates.md`'s, per `languages/README.md` § The seven concerns.

Every measurement below was taken on 2026-08-23, except two restated on 2026-10-03 after the SDD
runner's launcher and its suite were removed, and the count of tracked bash files, restated on
2026-10-26 when the git hook shims and the hook runner gained suites — each says so where it stands.

## The tool is pytest, and the tests are written in Python

**No shell test framework is used, and none is installed.** `git ls-files '*.bats'` returns nothing,
and neither `bats` nor `shunit` appears anywhere in the tree. A shell file here is tested by a Python
suite that runs the real script as a subprocess.

**All twenty-three tracked bash files carry a suite (2026-10-26, over
`git ls-files '*.sh' 'core/githooks/*'`).** The twelve launchers each carry one flat beside them
(`core/launchers/<identity>/test_<identity>.py`, the hyphens of the identity written as underscores,
and `_launcher` appended in three cases). The nine bash files under `core/tools/` each carry one there
(`test_detach_watcher.py`, `test_detach_process_watcher.py`, `test_detached_run.py`,
`test_run_telemetry.py`, `test_pin_run.py`, `test_launch_audit.py`, `test_launch_apply_packet.py`,
`test_launch_fix_author.py`, `test_locked_python.py`). The two git hook shims share one,
`core/tools/test_githooks.py`.

**The two git hook shims are tested as git runs them.** `core/tools/test_githooks.py` commits in a
scratch repository with no `pyproject.toml` whose `core.hooksPath` is the host's `core/githooks`, with
a `python3` that only exits 1 first on `PATH`. A well-formed commit lands, and a commit the checkers
refuse is refused with the checker's own message, not the stub's exit. That covers each shim's own two
lines — the self-location `core="$(cd "$(dirname "$0")/.." && pwd)"` and the `exec` through
`core/tools/locked_python.sh` — and that neither reaches the machine's `python3`. The Python checkers
the shims run keep their own suites (`core/tools/test_verify_commit_msg.py`,
`core/tools/test_written_forward.py`), and `.claude/tests/test_resolve_core_githooks.py` still tests
the wiring of `core.hooksPath` against stub hook files.

**Where the file goes and what it is called is `kensaiapp_structure.md`'s**, not this file's:
§ Owner-run launcher folder fixes both, and states the reason the generic name is banned — "pytest
imports test modules by basename, so a second `test_launcher.py` anywhere under `core/launchers/`
aborts the whole run with `import file mismatch` before a single test executes".

## The run command

| Scope | Command |
|---|---|
| One file's suite | `python3 -m pytest core/launchers/<identity>/test_<identity>.py -q` |
| Every shell suite | `python3 -m pytest core/launchers/ core/tools/ -q` |

Measured on 2026-10-03, the suites covering shell — the thirteen launcher suites plus
`test_detach_watcher.py`, `test_launch_audit.py`, `test_launch_apply_packet.py`,
`test_launch_fix_author.py`, `test_keep_awake_binding.py` and `test_agent_id_handover.py` — ran
**1445 passed in 131s**. The whole-suite command ran **6873 passed, 1 skipped in 231s**, which is
nearly four minutes: the reason a single file's suite has its own row is that the whole-suite command
is not what a per-file change should reach for first.

## The layers, and where shell actually lands

`testing_doctrine.md` orders layers 1–5 by scope and 6–7 by phase. A launcher is a CLI entry point with
no domain behind it, so the ladder collapses toward its ends.

| Layer | For a shell file here |
|---|---|
| 1 — Unit | A function in a **sourced library**, exercised through a wrapper (§ Technique 2). `core/tools/test_detach_watcher.py` is the whole of it — no other shell file has a function worth isolating. |
| 2 — Integration | Not distinct here. A shell script's "cross-boundary flow" *is* running it, which is layer 5. |
| 3 — Application | Not applicable. There is no use case to enter inside the entry point, because the entry point is the whole program. |
| 4 — UI | Not applicable. `testing_doctrine.md` states the exemption: "A CLI or a library has no components." |
| 5 — End-to-End | **Where nearly every shell test sits** — the real script, run through its real entry point, with the outside world stubbed (§ Technique 1). |
| 6 — Architecture | A property asserted over **every** shell file on disk rather than over one. `core/tools/test_keep_awake_binding.py` and `core/tools/test_agent_id_handover.py` are both this. |
| 7 — Specification | Not written for shell today. |

**Layer 6 is the one worth reaching for deliberately**, because a launcher set is written by copying
a sibling and a rule stated in one file's comment does not travel. `core/tools/test_keep_awake_binding.py`
says why it enumerates from disk instead of listing: "a list of nine is a list that goes stale the first
time a tenth launcher is written by copying a ninth. Every check here walks the tree, so a new site is
held to the rule the day it lands and nobody has to remember to add it here." Its own header also names
the one file it deliberately exempts and why — a layer-6 rule that fires on correct code is the failure
`languages/README.md` § Audit describes.

## Technique 1 — run the real script in a fixture instance

The dominant form. A pytest fixture builds a throwaway instance under `tmp_path`, puts stubs on `PATH`,
and runs the script itself:

- **The script under test is the real file**, resolved as
  `Path(__file__).resolve().parent / "launcher.sh"`, invoked with
  `subprocess.run([str(script), *cli_args], cwd=str(tmp_path), capture_output=True, text=True, env=env)`.
  The `cwd` is what the launcher resolves as its instance root, so the fixture directory *is* the
  instance.
- **The outside world is stubbed on `PATH`, not mocked.** A `claude` stub that records the argv it was
  handed (`printf '%s\n' "$@" > "$CLAUDE_ARGV_LOG"`), a `caffeinate` stub, a Python watcher stub
  reached through the launcher's own `LAUNCH_<X>_WATCHER` override, and a notifier stub through
  `LAUNCH_<X>_NOTIFIER`. `HOME` is redirected into `tmp_path` too.
- **A path with no env override is exercised for real.** `core/launchers/launch-eval-fix/launcher.sh`
  has no override for the shared library, so every passing launch in its suite exercises the real
  `detach_watcher.sh` at its real relative depth. Its suite states this in so many words, in
  `test_detach_watcher_is_found_at_its_resolved_home_when_nothing_overrides_it`: "every passing launch
  in this suite already runs against the real `core/tools/detach_watcher.sh` at its real relative
  depth".
- **A backgrounded step is polled, not slept on.** The watcher is detached with `&`, so the fixture
  retries reading its log — "The launch backgrounds the watcher (`&`), so it may still be starting when
  the launcher exits. Give it a moment before concluding it never ran."

## Technique 2 — source the library and call one function

For `core/tools/detach_watcher.sh`, which is never run. The suite writes a small bash wrapper into
`tmp_path` that sources the real library and forwards its own argv to one function:

```sh
#!/usr/bin/env bash
set -euo pipefail
source "{lib}"
capture_agent_id "$@"
```

Its suite states the shape and why it is that shape: the wrapper is "the same 'source, then call' shape
`companion-self-answer/launcher.sh` uses, minus everything a launcher does around it."

**In a layer-1 test, a collaborator is faked with a shell function, never with a stub on `PATH`.** The wrapper defines a function that records the argv it was handed, and sets the override variable the library reads to that function's name before the call, so the fake runs inside the same bash as the subject. A stub on `PATH`, as Technique 1 uses, is a real process: a layer-5 test may start one and a layer-1 test may not (`testing_doctrine.md` § A unit test hands its unit fakes and touches nothing real). On this reading the bash that runs the wrapper is the subject's own interpreter rather than a collaborator, so starting it does not break that rule. This idiom is the packet author's call, 2026-11-04.

**A shell port has no contract suite, so its fake is not verified**, by the no-layer-2 clause of `testing_doctrine.md` § A fake is verified against its port's contract: a shell file has no layer 2, by the table above. The fake is the recording function the library's wrapper defines, the one place that port's fake is written; nothing compares it with the real program, since the layer-5 tests stub the outside world too, so review alone holds it. **Shell has no unit-tier sandbox:** nothing refuses a real process inside a bash a test starts.

## Rules that hold across both

- **The test drives the real bytes.** Neither technique reimplements the script's logic, and neither
  tests a copy of it.
- **A source-text assertion is a fallback, not a technique.** It pins a line against deletion and
  reordering and cannot prove the wiring runs. `core/launchers/ad-hoc-flow/code-integrity-report.md`
  (at `a01eb180`; retired 2026-09-18) records what that cost on this very launcher set: a test "carried the claim in its **name** … while every
  assertion under it read `fn('mergePrompt')`", and the behaviour it named was never checked. Where a
  source-text pin is the right tool — asserting that a `# shellcheck source=` directive matches the
  `source` line below it, or that a relative path appears exactly three times — it is asserting the
  text *is* the contract, which is different.
- **`--dry-run` is the assertion surface for the launch itself.** 17 of the 18 `.sh` files have one, so
  a test can assert the exact command without launching anything. Sixteen print the argv with
  `printf '  %q' "$@"`; `core/launchers/cold-read/launcher.sh` prints raw instead and says why — its
  prompts are long structured documents, and raw output "lets a reader (human or test) grep the actual
  text instead of an escaped blob". `conventions.md` § Constructs owns the `set -- … ; "$@"` form that
  makes either truthful.
- **A negative is asserted as deliberately as a positive.** `product-content`'s suite asserts the `npx`
  guard is **absent**, "so it cannot arrive by find-replace from the sibling" — the launcher set is written by
  copying, so an absence is a contract too.
- **A count in a test is derived, never divided.** `product-content`'s fixture counts `caffeinate`
  invocations "by the `-i` each invocation opens with, never by dividing the argument count", because
  "The number of arguments is the thing under test here; it cannot also be the unit of counting."
