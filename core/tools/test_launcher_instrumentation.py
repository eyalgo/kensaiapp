"""Fleet-wide guard: every launcher that spawns a `claude` run calls `instrument_run`.

`instrument_run.sh` (`core/tools/instrument_run.sh`) is the one home for tagging a run with the
telemetry environment — station 1's own "a real run lands" bar was a person typing five `OTEL_*`
variables onto the command line by hand, because nothing reached the receiver otherwise. This
guard is what keeps the next launcher from being written without the call: it is
unconditional, not opt-in, and this file is the rule that outlives the launchers satisfying it
today.

**Why this is enumerated from disk rather than listed.** `core/tools/test_agent_id_handover.py`
states the same reasoning for its own sweep: a list of the launchers that invoke `claude` is a
list that goes stale the first time a new one is written by copying an old one. Every check here
walks the tree, so a new site is held to the rule the day it lands.

The rule is one line: **a `core/launchers/<identity>/launcher.sh` that invokes `claude` calls
`instrument_run`.** Not "sources the library" — sourcing alone has no side effect
(`instrument_run.sh`'s own contract), so the guard is on the call itself: a line starting
`instrument_run`, exactly as every real call site writes it. A launcher whose usage line names
none of `project` / `document` / `skill` / `instance` owes no subject key: its call carries the four
provenance keys (`provider=`, `model=`, `effort=`, `source=`) and nothing else. One that does owes
the `key=value` pairs its own usage line names, using the variable it already parsed (`_owed_keys`,
below, derives which).

A launcher that spawns nothing (`chain-development`, `chain-product`, `chain-agari`,
`product-skeleton`) is correctly outside this guard's reach: it never invokes `claude`, so there is
no run for `instrument_run` to tag. `chain-development`, `chain-product` and
`chain-agari` are the three whose engines start runs through `<CORE>/launchers/skill/launcher.sh`,
which is swept here and tags its own.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

# `core/launchers/*/launcher.sh` only — one level of identity folders, never recursive. This
# excludes `.worktrees/` structurally: that tree sits beside `core/` at the repo root, not under
# it, so a non-recursive glob rooted at `core/launchers/` never reaches it — the same reasoning
# `test_agent_id_handover.py:32-34` states for its own `core/`-rooted sweep, applied to this
# narrower root.
_LAUNCHERS_DIR = _REPO / "core" / "launchers"

_CALL_LIBRARY = Path("core/tools/instrument_run.sh")


def _non_comment_lines(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if not line.lstrip().startswith("#")]


def _invokes_claude(lines: list[str]) -> bool:
    """A real spawn — `claude --bg …` / `claude -p …` built directly, or the one Claude builder
    (`core/tools/agent_run.py`) invoked with a `background`/`print` shape — on a non-comment
    line. Anchored on the adapter and the shape rather than on a provider literal, because a
    launcher takes its provider from the central file and names none; and on the flag rather than
    the bare word `claude`, because `claude agents` / `claude stop` (the watch/attach hints every
    launcher echoes) name the same program without spawning a run."""
    return any(
        ("claude --bg" in line)
        or ("claude -p " in line)
        or (
            "agent_run.py" in line
            and ("--shape background" in line or "--shape print" in line)
        )
        for line in lines
    )


def _is_instrument_run_call(line: str) -> bool:
    """A line starting `instrument_run` — bare, or followed by the `key=value` pairs Task 4
    hands over. Excludes a line that only defines `INSTRUMENT_LIB=` or only `source`s the
    library (both legitimately contain the substring `instrument_run` as part of a path): a real
    call site's line, once stripped, either *is* the bare word or starts with it plus a space."""
    stripped = line.strip()
    return stripped == "instrument_run" or stripped.startswith("instrument_run ")


# The provenance every instrumented run is stamped with (`instrument_run.sh`'s accepted keys).
_PROVENANCE_KEYS = ("provider", "model", "effort", "source")


def _handed_keys(call: str) -> set[str]:
    """The `key=` words a call line hands over, read as shell words with its trailing comment
    stripped — never as substrings, so `run_model=` is not `model=`. A trailing `\\` continues the
    call onto a line this never reads, which is the point: the keys must sit on the call's own line
    (CP-229), and `shlex` would otherwise refuse the dangling escape rather than answer."""
    words = shlex.split(call.strip().removesuffix("\\"), comments=True)
    return {word.split("=", 1)[0] for word in words[1:] if "=" in word}


def _calls_instrument_run(lines: list[str]) -> bool:
    return any(_is_instrument_run_call(line) for line in lines)


def _launcher_files() -> dict[Path, list[str]]:
    found = {}
    for path in sorted(_LAUNCHERS_DIR.glob("*/launcher.sh")):
        lines = _non_comment_lines(path)
        if _invokes_claude(lines):
            found[path.relative_to(_REPO)] = lines
    return found


def test_the_sweep_finds_the_launchers_it_is_meant_to_check():
    """A silent filter passes everything. This fails if the sweep stops finding anything — what a
    moved directory or a broken glob looks like from the outside, and otherwise indistinguishable
    from a fleet that is entirely compliant."""
    found = _launcher_files()

    assert found, "the sweep found no claude-invoking launcher anywhere — the filter is broken"
    assert Path("core/launchers/cold-read/launcher.sh") in found, (
        f"the sweep missed the fan-out launcher; it found: {sorted(found)}"
    )
    assert Path("core/launchers/product-card/launcher.sh") in found, (
        "the sweep missed the one foreground (`claude -p`) launcher; it found: "
        f"{sorted(found)}"
    )


def test_a_non_spawning_launcher_is_correctly_outside_the_sweep():
    """The negative half of the sweep's correctness: a launcher that spawns nothing must not be
    swept in and must not carry the call either — both are asserted, so a future edit that adds
    a stray `instrument_run` to one of these is caught as loudly as a missing one would be."""
    found = _launcher_files()
    for name in ("chain-development", "chain-product", "chain-agari", "product-skeleton"):
        path = Path(f"core/launchers/{name}/launcher.sh")
        assert path not in found, f"{name} invokes no claude run and should not be in the sweep"
        lines = _non_comment_lines(_REPO / path)
        assert not _calls_instrument_run(lines), (
            f"{name} calls instrument_run but spawns no run — nothing here for it to tag"
        )


def test_every_claude_invoking_launcher_calls_instrument_run():
    """The rule. A launcher that starts a `claude` run and never calls `instrument_run` is a run
    that reaches the receiver only if a person types the `OTEL_*` variables by hand — exactly the
    bar station 1 measured and this station exists to close."""
    offenders = [str(path) for path, lines in _launcher_files().items() if not _calls_instrument_run(lines)]

    assert not offenders, (
        "these launchers start a claude run and never call instrument_run, so the run reaches "
        "the telemetry receiver only if someone types the OTEL_* variables by hand:\n  "
        + "\n  ".join(sorted(offenders))
    )


_HANDS_OVER = '"$INSTRUMENT_RUN_SETTINGS"'


def _call_index(lines: list[str]) -> int | None:
    return next((i for i, line in enumerate(lines) if _is_instrument_run_call(line)), None)


def test_every_claude_invoking_launcher_hands_its_variables_to_the_spawn():
    """Task 7. Calling `instrument_run` exports the telemetry variables, and an exported variable
    never reaches a `claude --bg` session — measured 2026-09-10 over three haiku probes against the
    live receiver. What reaches it is `--settings`, so the value the
    call leaves behind has to be handed to the spawn, after the call that sets it."""
    offenders = []
    for path, lines in _launcher_files().items():
        call = _call_index(lines)
        handed = [i for i, line in enumerate(lines) if _HANDS_OVER in line and "--settings" in line]
        if call is None or not any(i > call for i in handed):
            offenders.append(str(path))
    assert not offenders, (
        'these launchers never pass --settings "$INSTRUMENT_RUN_SETTINGS" to their spawn after '
        "calling instrument_run, so a backgrounded run starts with no telemetry at all:\n  "
        + "\n  ".join(sorted(offenders))
    )


def test_a_literal_spawn_line_carries_the_settings_itself():
    """A launcher that builds its argv with `set --` hands the settings over by appending to it.
    One that spawns with a literal `claude --bg …` line — `cold-read`'s fan-out loop — has no argv
    to append to, so that line must carry them itself."""
    offenders = [
        f"{path}: {line.strip()}"
        for path, lines in _launcher_files().items()
        for line in lines
        if line.strip().startswith(("claude --bg", "claude -p ")) and "INSTRUMENT_RUN_SETTINGS" not in line
    ]
    assert not offenders, "a literal spawn line without the settings:\n  " + "\n  ".join(offenders)


# The property, not one spelling of it: SCRIPT_DIR is resolved to an ABSOLUTE path — `cd … &&
# pwd` — from the launcher's own path. Twenty-four of the twenty-five write that path as
# `${BASH_SOURCE[0]}` and `product-card` writes it as `$0`; for a file that is executed rather
# than sourced the two are the same value, and both survive the `cd "$INSTANCE_ROOT"` that
# follows, which is the whole of what the arm derivation needs.
_SCRIPT_DIR_RESOLUTION = re.compile(
    r'^SCRIPT_DIR="\$\(cd "\$\(dirname "(\$\{BASH_SOURCE\[0\]\}|\$0)"\)" && pwd\)"'
)


def test_every_swept_launcher_resolves_its_own_directory_into_script_dir():
    """The other half of the rule, and the reason it is here rather than left implicit.

    `instrument_run` derives `kensai.arm` from the caller's own `$SCRIPT_DIR`, because that is
    the only value resolved at the right moment: a launcher takes it from its own
    `${BASH_SOURCE[0]}` *before* it `cd`s to the instance root, so it survives both the `cd` and
    a launcher started by a path relative to its own folder. A launcher that stopped resolving
    `SCRIPT_DIR` this way would still call `instrument_run`, still pass every check above, and
    tag its runs with whatever the fallback derivation could recover — which for
    `./launcher.sh` is `.`. So the derivation's one input is held here, on the same swept set,
    rather than trusted to a convention nothing checks."""
    offenders = [
        str(path)
        for path, lines in _launcher_files().items()
        # `match`, not `==`: every launcher closes this line with a trailing
        # `# <CORE>/launchers/<name>` comment naming what it just resolved.
        if not any(_SCRIPT_DIR_RESOLUTION.match(line.strip()) for line in lines)
    ]

    assert not offenders, (
        "these launchers do not resolve their own absolute directory into SCRIPT_DIR, which is "
        "what instrument_run derives kensai.arm from:\n  " + "\n  ".join(sorted(offenders))
    )


def test_the_shared_library_exists_at_the_path_every_launcher_resolves():
    assert (_REPO / _CALL_LIBRARY).is_file(), (
        f"{_CALL_LIBRARY} is missing — every launcher's INSTRUMENT_LIB resolves to it"
    )


# --- Task 4 — every spawning launcher hands over what its usage names ----------------------

# usage token -> instrument_run key, per the plan's own table. Order doesn't matter for
# membership; each launcher's usage line is checked for every token independently.
_TOKEN_TO_KEY = (
    ("<project>", "project"),
    ("--project", "project"),
    ("<document>", "document"),
    ("<skill>", "skill"),
    ("<instance>", "target_instance"),
)


def _usage_line(path: Path) -> str:
    """The line immediately below `# USAGE` in a launcher's header comment — the one line every
    launcher's own usage block carries its argument shape on."""
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "# USAGE":
            return lines[i + 1]
    raise AssertionError(f"{path} has no # USAGE block")


def _owed_keys(usage_line: str) -> set[str]:
    return {key for token, key in _TOKEN_TO_KEY if token in usage_line}


def test_every_launchers_instrument_run_call_carries_the_pairs_its_usage_line_owes():
    """The rule, derived from disk rather than a hardcoded table — a usage line naming
    `<project>` or `--project` owes `project=`, `<document>` owes `document=`, `<skill>` owes
    `skill=`, and `<instance>` owes `target_instance=`. A launcher owing more than one owes all
    of them on its one `instrument_run` line."""
    offenders = []
    for path, lines in _launcher_files().items():
        owed = _owed_keys(_usage_line(_REPO / path))
        if not owed:
            continue
        call_index = _call_index(lines)
        call = lines[call_index].strip() if call_index is not None else None
        missing = {key for key in owed if f"{key}=" not in (call or "")}
        if missing:
            offenders.append(f"{path}: missing {sorted(missing)} in {call!r}")
    assert not offenders, (
        "these launchers owe key=value pairs their own usage line names, and their "
        "instrument_run call is missing at least one:\n  " + "\n  ".join(offenders)
    )


def test_a_launcher_owing_no_usage_key_carries_exactly_the_four_provenance_keys():
    """The negative half: a launcher owing no subject key (`seeds-from-idea`) hands over the four
    provenance keys every run is stamped with, and nothing else — it must not grow a subject key
    (`project=`, `document=`, `skill=`, `target_instance=`) by copying a sibling that has one. The
    keys are read as shell words off the call's own line, so a comment never supplies one."""
    offenders = []
    for path, lines in _launcher_files().items():
        if _owed_keys(_usage_line(_REPO / path)):
            continue
        call_index = _call_index(lines)
        call = lines[call_index].strip() if call_index is not None else None
        if call is None or _handed_keys(call) != set(_PROVENANCE_KEYS):
            offenders.append(f"{path}: {call!r}")
    assert not offenders, (
        "these launchers owe no subject key per their own usage line, but their instrument_run "
        f"call hands over something other than exactly {list(_PROVENANCE_KEYS)}:\n  "
        + "\n  ".join(offenders)
    )


# --- The fleet sweep — every instrumented launcher stamps its provenance -------------------

# The skill launcher and the six of the eleven that gained the four keys beside it still on disk —
# `kensaiapp-writing-bar`'s, `experience-visual`'s and `experience-voice`'s were deleted on
# 2026-09-30, each skill launching through the skill launcher from its `launcher.md`, and
# `product-sdd`'s on 2026-10-03 with the three-seat runner it launched, and `ratify`'s the same day. A count, not a
# list:
# which launchers call `instrument_run` is read from disk, and this number is what stops a broken
# glob or a predicate that matches nothing from reading as a compliant fleet.
_INSTRUMENTED_LAUNCHER_COUNT = 7


def _instrumented_launchers(launchers_dir: Path = _LAUNCHERS_DIR) -> dict[Path, list[str]]:
    """Every `<launchers_dir>/*/launcher.sh` whose non-comment lines hold an `instrument_run`
    call — enumerated by the call itself, not by `_invokes_claude`, which never sees the two
    `--shape turn` launcher (`companion-self-answer`) that is instrumented too."""
    found = {}
    for path in sorted(launchers_dir.glob("*/launcher.sh")):
        lines = _non_comment_lines(path)
        if _calls_instrument_run(lines):
            found[path] = lines
    return found


def _calls_missing_provenance(lines: list[str]) -> list[str]:
    """Each `instrument_run` call line that does not hand over all four provenance keys on its
    own line, described with the keys it lacks. Empty when every call carries them."""
    return [
        f"missing {[key for key in _PROVENANCE_KEYS if key not in _handed_keys(line)]} in "
        f"{line.strip()!r}"
        for line in lines
        if _is_instrument_run_call(line) and not set(_PROVENANCE_KEYS) <= _handed_keys(line)
    ]


def test_every_launcher_with_an_instrument_run_call_carries_the_four_provenance_keys_on_that_line():
    """CP-229. A run of any instrumented launcher reaches the receiver stamped with the provider it
    went through, the model and effort it went at, and where those came from — or
    `run_provenance.py <run_id>` has nothing to answer. The keys are read off the call's own line
    as shell words, so a comment naming them, or a `\\`-continued line holding them, is no stamp."""
    offenders = [
        f"{path.relative_to(_REPO)}: {problem}"
        for path, lines in _instrumented_launchers().items()
        for problem in _calls_missing_provenance(lines)
    ]
    assert not offenders, (
        f"these instrumented launchers do not hand {list(_PROVENANCE_KEYS)} to instrument_run on "
        "the call's own line:\n  " + "\n  ".join(offenders)
    )


def test_the_call_sweep_finds_seven_launchers():
    """A silent filter passes everything: a sweep that found nothing would pass the rule above.
    Seven is the skill launcher and the six; a new instrumented launcher moves this number,
    deliberately, in the same commit that makes it one."""
    found = sorted(str(path.relative_to(_REPO)) for path in _instrumented_launchers())

    assert len(found) == _INSTRUMENTED_LAUNCHER_COUNT, (
        f"the call sweep found {len(found)} instrumented launchers, expected "
        f"{_INSTRUMENTED_LAUNCHER_COUNT}: {found}"
    )
    assert "core/launchers/companion-self-answer/launcher.sh" in found, (
        "the sweep missed a --shape turn launcher, which _invokes_claude cannot see"
    )


def test_a_continued_call_line_does_not_satisfy_the_sweep(tmp_path: Path):
    """CP-229 on a constructed launcher: the four keys on the `\\`-continued line below the call
    are not on the call's line, so the sweep names that launcher — and a sibling whose call holds
    them on its own line is not named, so the sweep is not failing everything."""
    continued = tmp_path / "continued" / "launcher.sh"
    continued.parent.mkdir()
    continued.write_text(
        "#!/usr/bin/env bash\n"
        'instrument_run skill="$skill" \\\n'
        '  provider=claude model="$run_model" effort="$run_effort" source="$run_source"\n'
    )
    one_line = tmp_path / "one-line" / "launcher.sh"
    one_line.parent.mkdir()
    one_line.write_text(
        "#!/usr/bin/env bash\n"
        'instrument_run skill="$skill" provider=claude model="$run_model" effort="$run_effort"'
        ' source="$run_source"\n'
    )

    swept = _instrumented_launchers(tmp_path)

    assert set(swept) == {continued, one_line}
    assert _calls_missing_provenance(swept[continued]) == [
        "missing ['provider', 'model', 'effort', 'source'] in "
        "'instrument_run skill=\"$skill\" \\\\'"
    ]
    assert _calls_missing_provenance(swept[one_line]) == []
