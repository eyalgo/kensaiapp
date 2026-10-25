"""The cross-launcher contract: `<CORE>` is resolved from a launcher's own location, at any
nesting depth, never by counting a fixed number of parent steps.

Sits at the root of `core/launchers/`, beside `conftest.py` rather than inside a launcher folder,
because every test here asserts a property of the *set* — every `launcher.sh` on disk, or the
resolution mechanism itself over a synthetic tree — never the behaviour of one launcher. Its
basename is globally unique, which `core/doctrine/setup/kensaiapp_structure.md`
§ *Owner-run launcher folder* requires of every test file under this tree: "a second
`test_launcher.py` anywhere under `core/launchers/` aborts the whole run with
`import file mismatch`" — the same reasoning applies to this file's own name.

CP-1 — no file under `core/launchers` reaches `core/tools/` by counting `../../`.
CP-2 — every `launcher.sh` resolves `<CORE>` by one expression that names no fixed depth.
CP-3 — a launcher nested under `core/launchers/development/<step>/` still finds the real
       `<CORE>/tools/watch_agent.py` and spawns it, with its watcher override unset.
CP-4 — a launcher with no `launchers/` ancestor at all refuses loudly rather than guessing.

Every sweep below carries its own positive control — a filter matching nothing is
indistinguishable from a fleet that complies, so an empty read fails the test rather than
passing it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

_LAUNCHERS_DIR = Path(__file__).resolve().parent
_CORE_DIR = _LAUNCHERS_DIR.parent
# The real launcher this file runs end to end, standing in for "a launcher.sh": one that detaches its
# completion watcher through the shared home and defaults that watcher to `<CORE>/tools/watch_agent.py`.
# `launch-eval-fix` since 2026-10-24, when `seeds-from-idea`'s launcher — the stand-in until then —
# was deleted, the skill having no launcher of its own.
_MODEL_LAUNCHER = _LAUNCHERS_DIR / "launch-eval-fix" / "launcher.sh"
_DETACH_LIB = _CORE_DIR / "tools" / "detach_watcher.sh"
_REAL_WATCHER = _CORE_DIR / "tools" / "watch_agent.py"
# The delivered provider file: the tracked template at the instance root, which a case copies
# into the instance it runs for.
_PROVIDER_EXAMPLE = _CORE_DIR.parent / ".providers.toml.example"

# The one sanctioned expression every launcher.sh derives <CORE> by. A prefix strip at the
# `/launchers/` boundary, shortest-suffix (`%`, never `%%`) so an outer directory that merely
# shares the name `launchers` is never mistaken for the real ancestor.
_SANCTIONED_CORE_DIR_LINE = 'CORE_DIR="${SCRIPT_DIR%/launchers/*}"'

# The guard's condition — the strip returning its input unchanged is the only way the resolution
# can fail, so this is the whole of what every launcher must refuse on. The message differs per
# launcher (each names itself, the way its own `die` does), so only the condition is a literal.
_CORE_DIR_GUARD_CONDITION = '[ "$CORE_DIR" != "$SCRIPT_DIR" ]'


def _core_dir_for(launcher_dir: Path) -> Path:
    """Python's own copy of the bootstrap's algorithm, for asserting its properties (same depth
    from a flat home and a nested one, an outer `launchers`-named directory not capturing the
    strip) without shelling out to bash for every case. `test_every_launcher_resolves_core_by_the_same_expression`
    below is what proves the shell and this Python copy agree on the real corpus."""
    text = str(launcher_dir)
    marker = "/launchers/"
    idx = text.rfind(marker)
    assert idx != -1, f"{launcher_dir} has no /launchers/ ancestor"
    return Path(text[:idx])


# The retired two-parent-step walk into `tools/`, built by concatenation rather than spelled as
# one literal — CP-1's own reached-when greps this exact substring across `core/launchers`, and a
# file whose CHECKING code contains the substring it checks for would fail its own gate. Building
# it at runtime keeps the substring out of this file's bytes while the check still matches exactly
# what CP-1 means.
_RETIRED_TOOLS_WALK = "../" + "../tools"


def _every_launcher_script() -> list[Path]:
    """Every `launcher.sh` under `core/launchers`, at any depth. `rglob`, never `glob("*/…")`:
    a launcher at the newly permitted `core/launchers/development/<step>/` is a level below what
    a flat glob reaches, and a contract sweep blind to the home the rule was widened for would
    report compliance it never checked. The floor is a positive control — 12 launchers exist
    today (the three-seat product-sdd runner's was deleted on 2026-10-03; ten per-skill and chain
    launchers were retired on 2026-09-17, and chain-change arrived the same day;
    ad-hoc-flow was retired on 2026-09-18, and build-idea joined on 2026-09-18; seeds-from-product-docs's was
    retired on 2026-09-25, the skill launching from its launcher.md; kensaiapp-writing-bar's,
    experience-visual's and experience-voice's were retired on 2026-09-30 the same way, and
    chain-agari arrived on 2026-10-04; seeds-from-idea's was deleted on 2026-10-24, the skill
    having no launcher of its own), so a smaller read means the glob or the tree moved, not
    that the fleet complies. It is
    a floor rather than an equality because a nested step launcher is expected to arrive and must
    join this contract rather than break it."""
    scripts = sorted(_LAUNCHERS_DIR.rglob("launcher.sh"))
    assert len(scripts) >= 12, (
        f"expected at least the 12 known launcher.sh files, found {len(scripts)} — this sweep "
        f"would pass over an incomplete set"
    )
    return scripts


def _uncommented_lines(source: str) -> list[tuple[int, str]]:
    """The source's lines paired with their index, comments dropped. A header comment naming
    `$CORE_DIR` is prose about the bootstrap, not a read of it, and ten launchers carry one
    above the assignment — so an ordering check that counted comments would read every one of
    them as using the variable before it is guarded."""
    return [
        (i, line)
        for i, line in enumerate(source.splitlines())
        if not line.lstrip().startswith("#")
    ]


def _text_files_under_launchers() -> list[Path]:
    """Every readable file under `core/launchers`, at any depth — the same set CP-1's own
    reached-when reads (`grep -rlE '\\.\\./\\.\\./tools' core/launchers`, run from the instance
    root), which recurses and is blind to a file's name. Two exclusions, both because `grep -r`
    would not report them either: `__pycache__` (untracked build output, regenerated on every
    run) and any file whose bytes are not text."""
    files = []
    for path in sorted(_LAUNCHERS_DIR.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            path.read_text()
        except UnicodeDecodeError:
            continue
        files.append(path)
    return files


def test_no_file_under_launchers_reaches_tools_by_counting_folders():
    """CP-1: no file under `core/launchers` contains the retired two-parent-step spelling that
    reaches `tools/` (`_RETIRED_TOOLS_WALK` above). Recursive, not one level deep and not scoped
    to two filename shapes: the home this change exists to permit —
    `core/launchers/development/<step>/` — sits a level below every glob a flat sweep would use,
    so a flat sweep would be blind to exactly the file the rule was widened for. The sweep first
    asserts it read a plausible number of files, so an empty read (a wrong glob, a moved tree)
    fails loudly rather than passing vacuously over nothing."""
    files = _text_files_under_launchers()
    assert len(files) >= 33, (
        f"expected at least 33 readable files under core/launchers, found {len(files)} — "
        f"this sweep would pass vacuously over too few files"
    )
    offenders = sorted(str(p) for p in files if _RETIRED_TOOLS_WALK in p.read_text())
    assert not offenders, f"files still spelling the retired walk into tools/: {offenders}"


def test_no_launcher_script_contains_a_two_levels_up_expression():
    """CP-1, CP-2: no `launcher.sh` under `core/launchers` contains `../..` in any spelling that
    reaches `<CORE>` or `core/tools/` — scoped to `launcher.sh` (never a suite) because a suite
    may legitimately carry `../..` as fixture data, exactly as
    `product-skeleton/test_product_skeleton.py`'s own path-traversal-escape fixture
    (`("escapee", "../../elsewhere")`) does.

    No launcher is exempt: the companion launcher's walk to the flat agents folder is gone, so the
    sweep reads every script whole.
    """
    scripts = _every_launcher_script()

    offenders = []
    for path in scripts:
        source = path.read_text()
        if "../.." in source:
            offenders.append(path.parent.name)
    assert not offenders, (
        f"launchers still spelling a fixed-depth walk: {offenders}"
    )


def test_every_launcher_resolves_core_by_the_same_expression():
    """CP-2: every `launcher.sh` derives `CORE_DIR` by the one sanctioned expression, and none
    derives it any other way — a second, different `CORE_DIR=` assignment in the same file would
    be a second, competing answer to "where is `<CORE>`"."""
    scripts = _every_launcher_script()

    missing = []
    for path in scripts:
        lines = path.read_text().splitlines()
        core_dir_lines = [l for l in lines if l.strip().startswith("CORE_DIR=")]
        if core_dir_lines != [_SANCTIONED_CORE_DIR_LINE]:
            missing.append((path.parent.name, core_dir_lines))
    assert not missing, f"launchers not deriving CORE_DIR by exactly the sanctioned expression: {missing}"


def test_the_flat_and_the_nested_launcher_resolve_the_same_core():
    """CP-2: the `<CORE>` resolved from `<CORE>/launchers/<identity>/` and the `<CORE>` resolved
    from `<CORE>/launchers/development/<step>/` are the same directory, and
    `<that>/tools/watch_agent.py` is the real file and exists."""
    flat = _core_dir_for(_CORE_DIR / "launchers" / "some-identity")
    nested = _core_dir_for(_CORE_DIR / "launchers" / "development" / "specs")

    assert flat == _CORE_DIR
    assert nested == _CORE_DIR
    assert flat == nested

    watcher = flat / "tools" / "watch_agent.py"
    assert watcher == _REAL_WATCHER
    assert watcher.exists(), f"resolved watcher does not exist: {watcher}"


def test_an_outer_directory_named_launchers_does_not_capture_the_strip():
    """CP-2: a launcher under `/…/launchers/…/core/launchers/development/<step>/` resolves the
    INNER `<CORE>`, not the outer directory that merely shares the name `launchers` — the
    shortest-suffix strip (`%`, never `%%`) is what makes this true."""
    tricky = Path("/x/launchers/y") / "core" / "launchers" / "development" / "specs"
    resolved = _core_dir_for(tricky)
    assert resolved == Path("/x/launchers/y/core"), (
        f"the strip captured the outer 'launchers' directory instead of the inner one: {resolved}"
    )


def test_every_launcher_refuses_before_it_reads_the_core_it_could_not_resolve():
    """CP-4 is a property of *a* `launcher.sh`, not of the one this file runs end to end below.
    The behavioural test that follows proves the guard works; this one proves every launcher has
    it, and has it in the only place where it helps — after the derivation and before the first
    read through `CORE_DIR`. A launcher that derived `CORE_DIR` and then read through it
    unguarded would resolve `<CORE>` to its own folder and go on to source nothing, silently,
    which is the failure the whole change exists to close."""
    for path in _every_launcher_script():
        lines = _uncommented_lines(path.read_text())

        derivations = [i for i, line in lines if line.strip() == _SANCTIONED_CORE_DIR_LINE]
        guards = [i for i, line in lines if _CORE_DIR_GUARD_CONDITION in line]
        reads = [
            i
            for i, line in lines
            if "$CORE_DIR" in line and i not in derivations and i not in guards
        ]

        assert len(guards) == 1, (
            f"{path.parent.name}: expected exactly one CORE_DIR guard, found {len(guards)}"
        )
        assert derivations and guards[0] > derivations[0], (
            f"{path.parent.name}: the guard does not follow the CORE_DIR derivation"
        )
        assert not reads or guards[0] < min(reads), (
            f"{path.parent.name}: CORE_DIR is read at line {min(reads) + 1}, before the guard at "
            f"line {guards[0] + 1} — an unresolvable <CORE> would be used rather than refused"
        )

        guard = dict(lines)[guards[0]]
        assert ">&2" in guard, f"{path.parent.name}: the refusal does not go to stderr"
        assert "exit 1" in guard, f"{path.parent.name}: the refusal does not exit non-zero"
        assert "/launchers/" in guard, (
            f"{path.parent.name}: the refusal does not name the missing /launchers/ ancestor"
        )
        assert "$SCRIPT_DIR" in guard, (
            f"{path.parent.name}: the refusal does not name the directory it ran from"
        )


def test_a_launcher_with_no_launchers_ancestor_exits_non_zero_naming_the_assumption(tmp_path):
    """CP-4: a `launcher.sh` whose own directory has no `launchers/` ancestor exits non-zero,
    writes one stderr line naming the missing ancestor and the directory it ran from, and
    spawns nothing. Uses the stand-in launcher (`_MODEL_LAUNCHER`) unmodified — the guard fires
    before the script reads a single argument or spawns anything, so no stub of any kind is needed."""
    orphan_dir = tmp_path / "somewhere" / "with" / "not_even" / "one" / "ancestor"
    orphan_dir.mkdir(parents=True)
    orphan_script = orphan_dir / "launcher.sh"
    shutil.copy(_MODEL_LAUNCHER, orphan_script)
    orphan_script.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude_stub = bin_dir / "claude"
    claude_marker = tmp_path / "claude_was_called"
    claude_stub.write_text(f"#!/usr/bin/env bash\ntouch {claude_marker}\n")
    claude_stub.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [str(orphan_script)], cwd=str(tmp_path), capture_output=True, text=True, env=env
    )

    assert result.returncode != 0
    stderr_lines = [l for l in result.stderr.splitlines() if l.strip()]
    assert len(stderr_lines) == 1, f"expected exactly one stderr line, got: {stderr_lines}"
    assert "/launchers/" in stderr_lines[0] and "no" in stderr_lines[0].lower()
    assert str(orphan_dir) in stderr_lines[0], "the refusal does not name the directory it ran from"
    assert not claude_marker.exists(), "the refusal spawned something despite the missing ancestor"


@pytest.fixture
def _nested_synthetic_core(tmp_path):
    """A whole synthetic `<CORE>` under `tmp_path`: `core/launchers/development/<step>/launcher.sh`
    copied from the real stand-in launcher (`_MODEL_LAUNCHER`), the real `detach_watcher.sh`
    (sourced by the copy, so it must be the real behaviour, not a stub), and a recording
    `watch_agent.py` stub standing in for the real one — the one file this fixture does NOT copy
    real, because the whole point is to observe whether it gets spawned. The instance it launches
    for holds the one thing that launcher needs before it reaches its watcher: a skill with a
    settled eval round (a `benchmark.md`) for it to act on."""
    core = tmp_path / "core"
    step_dir = core / "launchers" / "development" / "specs"
    step_dir.mkdir(parents=True)
    nested_script = step_dir / "launcher.sh"
    shutil.copy(_MODEL_LAUNCHER, nested_script)
    nested_script.chmod(0o755)

    tools_dir = core / "tools"
    tools_dir.mkdir(parents=True)
    shutil.copy(_DETACH_LIB, tools_dir / "detach_watcher.sh")
    # The pin machinery every launcher and every Claude launch now unconditionally reaches
    # (Task 15) — `pin_enter` sources `pin_run.sh`, which shells out to `pin.py`; the adapter
    # build shells out to `agent_run.py`, which imports `model_assignment` and `task_context`; and
    # the run's provenance is resolved by `run_intelligence.py`, which imports `intelligence` and
    # `model_assignment`; the launcher's provider is read by `providers.py` from the instance's
    # own `.providers.toml`, which this fixture writes at the instance root; the skill it acts on
    # is resolved by `skill_path.py`, and the round lock it stands down for is read by
    # `evals_round_lock.py` — both real, so the launch the watcher follows is the real one.
    for tool in (
        "pin.py",
        "pin_run.sh",
        "agent_run.py",
        "hook_wiring.py",
        "model_assignment.py",
        "task_context.py",
        "env_file.py",
        "run_intelligence.py",
        "intelligence.py",
        "providers.py",
        "skill_path.py",
        "evals_round_lock.py",
    ):
        shutil.copy(_CORE_DIR / "tools" / tool, tools_dir / tool)
    # `tmp_path/core` is marked as its own pin, so `pin_enter` (rule 1) finds itself already
    # pinned and neither re-execs nor copies anything: what this fixture builds is exactly what
    # runs.
    (tmp_path / "pin.json").write_text(
        json.dumps({"id": "isolated", "source_host_root": str(tmp_path),
                    "created": "1970-01-01T00:00:00+00:00"})
        + "\n"
    )

    watcher_log = tmp_path / "watcher_argv.log"
    watcher_stub = tools_dir / "watch_agent.py"
    watcher_stub.write_text(
        "import sys\n"
        "if '--list-ids' in sys.argv:\n"
        "    print('')\n"
        "else:\n"
        f"    with open({str(watcher_log)!r}, 'w') as fh:\n"
        "        fh.write('\\n'.join(sys.argv[1:]))\n"
    )

    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    shutil.copy(_PROVIDER_EXAMPLE, instance_root / ".providers.toml")
    skill = "demo-skill"
    settled_round = (
        instance_root / ".claude" / "skills" / skill / "evals" / "workspace" / "iteration-1"
    )
    settled_round.mkdir(parents=True)
    (settled_round / "benchmark.md").write_text("# benchmark 1\n")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude_stub = bin_dir / "claude"
    claude_stub.write_text("#!/usr/bin/env bash\necho '{\"status\": \"ok\"}'\n")
    claude_stub.chmod(0o755)

    # detach_completion_watcher's happy path (the one that actually spawns the watcher) is
    # `[ -x notifier ] && [ -f watcher ]` — an absent notifier takes the else branch and skips
    # the watcher entirely (`errors_logging.md` § *The two-condition else branch*), so a
    # notifier stub is required here even though CP-3 is not about the notifier at all.
    notifier_stub = tmp_path / "notifier.sh"
    notifier_stub.write_text("#!/usr/bin/env bash\ntrue\n")
    notifier_stub.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()
    # The watcher override is deliberately left UNSET — CP-3 is about the launcher's own
    # default, not a test-supplied stand-in for it.
    env.pop("LAUNCH_EVAL_FIX_WATCHER", None)
    env["LAUNCH_EVAL_FIX_NOTIFIER"] = str(notifier_stub)
    env.pop("KENSAIAPP_NOTIFIER", None)
    # The round lock is read for real, at a path nothing occupies, so the launch never consults
    # this machine's own lock and never stands down for a round running on it.
    env["KENSAIAPP_EVALS_LOCK"] = str(tmp_path / "no-round-lock.json")

    def _watcher_argv():
        for _ in range(50):
            if watcher_log.exists():
                return watcher_log.read_text().splitlines()
            time.sleep(0.05)
        return []

    return type(
        "NestedSyntheticCore",
        (),
        {
            "script": nested_script,
            "instance_root": instance_root,
            "skill": skill,
            "env": env,
            "watcher_argv": staticmethod(_watcher_argv),
            "real_watcher_home": tools_dir / "watch_agent.py",
        },
    )()


def _every_tools_launch_script() -> list[Path]:
    """Every `launch-*.sh` script under `core/tools` — the sibling fleet the two sweeps below run
    over alongside `_every_launcher_script`'s `core/launchers/**/launcher.sh` set. A floor, not an
    equality, for the same reason as that reader's: three exist today
    (`launch-audit.sh`, `launch-apply-packet.sh`, `launch-fix-author.sh`), so a smaller read means
    the glob or the tree moved, not that the fleet complies."""
    scripts = sorted((_CORE_DIR / "tools").glob("launch-*.sh"))
    assert len(scripts) >= 3, (
        f"expected at least the 3 known core/tools/launch-*.sh scripts, found {len(scripts)} — "
        f"this sweep would pass over an incomplete set"
    )
    return scripts


def _every_fleet_script() -> list[Path]:
    """Task 21's fleet: every `launcher.sh` under `core/launchers` plus every `launch-*.sh` under
    `core/tools` — the set `tl_instruction.md` Task 21 names ("Every `launcher.sh` and
    `launch-*.sh` calls `pin_enter` — or, for `build-idea` alone, `pin_enter_renewing`… No file…
    builds a `claude` command itself")."""
    return _every_launcher_script() + _every_tools_launch_script()


def _fleet_script_name(path: Path) -> str:
    """The name a fleet-sweep offender is reported under: a `launcher.sh`'s own folder (matching
    every other sweep in this file), or a `launch-*.sh` script's own basename."""
    return path.parent.name if path.name == "launcher.sh" else path.stem


# The two lines that are load-bearing prerequisites to calling pin_enter itself, and so the only
# uses of $CORE_DIR permitted between its derivation and that call: the guard that refuses an
# unresolvable <CORE> (present on every launcher.sh; a core/tools/launch-*.sh script's plain
# `cd ..` cannot fail the same way and carries none), and the `source` that defines pin_enter in
# the first place. Any other read is a use of $CORE_DIR that ran before the pin was entered.
_CORE_DIR_ENTRY_ALLOWED_USES = (_CORE_DIR_GUARD_CONDITION, 'source "$CORE_DIR/tools/pin_run.sh"')


def _core_dir_entry_offense(text: str) -> str | None:
    """Task 21: the single-file check
    `test_every_launcher_enters_the_pin_right_after_resolving_core` sweeps the fleet with —
    factored out to a pure function so the same logic that reads the real
    fleet can also be proven, against a synthetic positive control, to flag a launcher that skips
    or delays entering the pin. Returns the offense found, or None when `pin_enter` runs right
    after `CORE_DIR` is derived and nothing else reads `$CORE_DIR` before it."""
    lines = _uncommented_lines(text)
    derivations = [i for i, line in lines if line.strip().startswith("CORE_DIR=")]
    pin_enters = [
        i
        for i, line in lines
        if line.strip().startswith(("pin_enter ", "pin_enter_renewing "))
    ]

    if not derivations:
        return "no CORE_DIR derivation"
    if not pin_enters:
        return "no pin_enter call"

    derivation, pin_call = derivations[0], pin_enters[0]
    if pin_call <= derivation:
        return "pin_enter precedes the CORE_DIR derivation"

    between = dict(lines)
    stray = [
        i
        for i in range(derivation + 1, pin_call)
        if i in between
        and "$CORE_DIR" in between[i]
        and not any(allowed in between[i] for allowed in _CORE_DIR_ENTRY_ALLOWED_USES)
    ]
    if stray:
        return f"CORE_DIR read before pin_enter at line(s) {[i + 1 for i in stray]}"
    return None


def test_every_launcher_enters_the_pin_right_after_resolving_core():
    """Task 21: every `launcher.sh` and `launch-*.sh` calls `pin_enter` — or, for `build-idea`
    alone, `pin_enter_renewing` — immediately once `CORE_DIR` is resolvable — before anything
    else reads through it. A launcher that derived `CORE_DIR` and then built something (a
    `claude` command, an `--add-dir`, a Python invocation) ahead of `pin_enter` would run that
    something against the un-pinned live host, defeating the one thing Task 4 exists to
    guarantee.
    """
    offenders = [
        (_fleet_script_name(path), offense)
        for path in _every_fleet_script()
        for offense in [_core_dir_entry_offense(path.read_text())]
        if offense is not None
    ]
    assert not offenders, (
        f"scripts not entering the pin right after resolving CORE_DIR: {offenders}"
    )

    # Positive control: a synthetic launcher lacking `pin_enter` entirely is flagged.
    missing_pin_enter = (
        'CORE_DIR="${SCRIPT_DIR%/launchers/*}"\n'
        '[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "no ancestor" >&2; exit 1; }\n'
        'echo "$CORE_DIR"\n'
    )
    assert _core_dir_entry_offense(missing_pin_enter) is not None, (
        "the check does not flag a launcher that never calls pin_enter"
    )

    # Positive control: a synthetic launcher reading $CORE_DIR (to build something with it)
    # before pin_enter is flagged, even though pin_enter is called right after.
    early_read = (
        'CORE_DIR="${SCRIPT_DIR%/launchers/*}"\n'
        '[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "no ancestor" >&2; exit 1; }\n'
        'echo "reading $CORE_DIR before the pin is entered"\n'
        '# shellcheck source=/dev/null\n'
        'source "$CORE_DIR/tools/pin_run.sh"\n'
        'pin_enter "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?\n'
    )
    assert _core_dir_entry_offense(early_read) is not None, (
        "the check does not flag a $CORE_DIR read that runs before pin_enter"
    )

    # Positive control: a launcher entering through `pin_enter_renewing` right after the guard
    # and the `source` is not flagged — the entry `build-idea` alone uses.
    renewing_entry = (
        'CORE_DIR="${SCRIPT_DIR%/launchers/*}"\n'
        '[ "$CORE_DIR" != "$SCRIPT_DIR" ] || { echo "no ancestor" >&2; exit 1; }\n'
        '# shellcheck source=/dev/null\n'
        'source "$CORE_DIR/tools/pin_run.sh"\n'
        'pin_enter_renewing "$CORE_DIR" "$SCRIPT_PATH" "$@" || exit $?\n'
    )
    assert _core_dir_entry_offense(renewing_entry) is None, (
        "the check flags a launcher that enters the pin through pin_enter_renewing"
    )


def test_only_build_idea_enters_through_the_renewing_entry():
    """CP-165: of every `launcher.sh` and `launch-*.sh`, `build-idea` alone calls
    `pin_enter_renewing`. The rest call `pin_enter`, which keeps the pin a launch is inside — so
    a launcher written by copying a sibling cannot start switching pins by copying this one."""
    renewing = sorted(
        _fleet_script_name(path)
        for path in _every_fleet_script()
        if any(
            line.strip().startswith("pin_enter_renewing ")
            for _, line in _uncommented_lines(path.read_text())
        )
    )
    assert renewing, "no script calls pin_enter_renewing — this check would pass over nothing"
    assert renewing == ["build-idea"]


# The three literal shapes a launcher must no longer assemble itself — every claude invocation
# now comes from agent_run.py's --print-argv (Tasks 6, 7). Comments naming these shapes in prose
# (what `claude --bg` does, why a launcher uses `claude -p` rather than `--bg`) are not a build of
# the command and stay legal; `_uncommented_lines` is what tells the two apart.
_CLAUDE_COMMAND_LITERALS = ("claude --bg", "claude -p", "claude --print")


def _claude_command_offense(text: str) -> list[str]:
    """Task 21: the single-file check `test_no_launcher_builds_a_claude_command_itself` sweeps
    the fleet with — factored out so the same logic can be proven against a synthetic positive
    control. Returns every literal shape found on an uncommented line, or an empty list when none
    is."""
    lines = _uncommented_lines(text)
    return sorted(
        {
            literal
            for _, line in lines
            for literal in _CLAUDE_COMMAND_LITERALS
            if literal in line
        }
    )


def test_no_launcher_builds_a_claude_command_itself():
    """Task 21: no `launcher.sh` and no `launch-*.sh` runs or assembles `claude --bg`, `claude -p`
    or `claude --print` itself, outside a comment — every Claude invocation is read from
    `agent_run.py --print-argv` (Tasks 6, 7, 13, 15-19) instead.
    """
    offenders = [
        (_fleet_script_name(path), found)
        for path in _every_fleet_script()
        for found in [_claude_command_offense(path.read_text())]
        if found
    ]
    assert not offenders, f"scripts still assembling a claude command themselves: {offenders}"

    # Positive control: a synthetic line assembling `claude --bg` directly is caught.
    direct_command = 'exec claude --bg --agent principal-pm --permission-mode auto "$PROMPT"\n'
    assert _claude_command_offense(direct_command) == ["claude --bg"], (
        "the check does not flag a line that assembles claude --bg directly"
    )


def test_the_fleet_is_all_counted():
    """Task 21: the two sweeps above both read the same fleet — twelve `launcher.sh` files and
    three `launch-*.sh` scripts — so a filter that
    matches nothing (a moved tree, a renamed glob) fails loudly rather than passing vacuously over
    an empty read."""
    launchers = _every_launcher_script()
    tools_scripts = _every_tools_launch_script()
    assert len(launchers) >= 12, f"expected at least 12 launcher.sh files, found {len(launchers)}"
    assert len(tools_scripts) >= 3, (
        f"expected at least 3 launch-*.sh scripts, found {len(tools_scripts)}"
    )

    fleet = _every_fleet_script()
    assert len(fleet) == len(launchers) + len(tools_scripts)
    assert len(set(fleet)) == len(fleet), "the fleet counts a file twice"


def test_a_nested_launcher_spawns_the_real_watcher_with_the_override_unset(_nested_synthetic_core):
    """CP-3: with its watcher environment override unset, a `launcher.sh` sitting at
    `<CORE>/launchers/development/<step>/` resolves its completion watcher to
    `<CORE>/tools/watch_agent.py` — the file above it, which exists — and spawns that file. The
    old fixed-two-levels-up default would have resolved to a path inside `launchers/`, where no
    such file exists, and the launch would still have reported success (`errors_logging.md`
    § *An optional tail is reported and skipped, never fatal*) — silently, which is the exact
    failure this contract exists to catch.
    """
    fixture = _nested_synthetic_core
    result = subprocess.run(
        [str(fixture.script), fixture.skill],
        cwd=str(fixture.instance_root),
        capture_output=True,
        text=True,
        env=fixture.env,
    )
    assert result.returncode == 0, f"the launch itself failed: {result.stderr}"

    argv = fixture.watcher_argv()
    assert argv, "the watcher stub was never spawned — the nested resolution did not reach it"
    assert "--cwd" in argv and str(fixture.instance_root) in argv, (
        f"the watcher stub ran, but not with the real detach_completion_watcher call: {argv}"
    )
