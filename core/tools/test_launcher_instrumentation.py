"""Fleet-wide guard: every launcher that spawns a `claude` run calls an instrumenting function.

Every instrumented launcher tags its run with the telemetry environment by calling `run_telemetry`
(`core/tools/run_telemetry.sh`, over the telemetry package's `turn-on`). One predicate
(`_is_instrumenting_call`) recognises that call, the only instrumenting call, so every check below
reads it the same way. Station 1's own "a real run lands" bar was a person typing five `OTEL_*`
variables onto the command line by hand, because nothing reached the receiver otherwise. This
guard is what keeps the next launcher from being written without the call: it is unconditional, not
opt-in, and this file is the rule that outlives the launchers satisfying it today.

**Why this is enumerated from disk rather than listed.** `core/tools/test_agent_id_handover.py`
states the same reasoning for its own sweep: a list of the launchers that invoke `claude` is a
list that goes stale the first time a new one is written by copying an old one. Every check here
walks the tree, so a new site is held to the rule the day it lands.

The rule is one line: **a `core/launchers/<identity>/launcher.sh` that invokes `claude` calls an
instrumenting function.** Not "sources the library" — sourcing alone has no side effect (each
library's own contract), so the guard is on the call itself: a line starting with the function's
name, exactly as every real call site writes it. A definition, a path, a comment or a `source` line
is not a call. A launcher whose usage line names none of `project` / `document` / `skill` /
`instance` owes no subject key: its call carries the four provenance keys (`provider=`, `model=`,
`effort=`, `source=`) and nothing else. One that does owes the `key=value` pairs its own usage line
names, using the variable it already parsed (`_owed_keys`, below, derives which). That obligation
holds for every launcher the call discovers, including one the spawn sweep cannot see.

A launcher that spawns nothing (`chain-development`, `chain-product`, `chain-agari`,
`product-skeleton`) is correctly outside this guard's reach: it never invokes `claude`, so there is
no run for an instrumenting function to tag. `chain-development`, `chain-product` and
`chain-agari` are the three whose engines start runs through `<CORE>/launchers/skill/launcher.sh`,
which is swept here and tags its own through `run_telemetry`.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]

# `core/launchers/*/launcher.sh` only — one level of identity folders, never recursive. This
# excludes `.worktrees/` structurally: that tree sits beside `core/` at the repo root, not under
# it, so a non-recursive glob rooted at `core/launchers/` never reaches it — the same reasoning
# `test_agent_id_handover.py:32-34` states for its own `core/`-rooted sweep, applied to this
# narrower root.
_LAUNCHERS_DIR = _REPO / "core" / "launchers"

_CALL_LIBRARY = Path("core/tools/run_telemetry.sh")


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


# The function that instruments a run. A new one is added here and nowhere else: the sweep, the
# provenance check and the usage checks all read the one predicate below.
_INSTRUMENTING_CALL = "run_telemetry"


def _is_instrumenting_call(line: str) -> bool:
    """A line starting with the instrumenting function's name — bare, or followed by the
    `key=value` pairs the launcher hands over. Excludes a line that only defines the function
    (`name() {`), names its path (`…/run_telemetry.sh`) or `source`s its library, all of which
    legitimately contain the name: a real call site's line, once stripped, either *is* the bare
    word or starts with it plus a space."""
    stripped = line.strip()
    return stripped == _INSTRUMENTING_CALL or stripped.startswith(f"{_INSTRUMENTING_CALL} ")


# The provenance every instrumented run is stamped with (`run_telemetry.sh`'s accepted keys).
_PROVENANCE_KEYS = ("provider", "model", "effort", "source")


def _handed_keys(call: str) -> set[str]:
    """The `key=` words a call line hands over, read as shell words with its trailing comment
    stripped — never as substrings, so `run_model=` is not `model=`. A trailing `\\` continues the
    call onto a line this never reads, which is the point: the keys must sit on the call's own line
    (CP-229), and `shlex` would otherwise refuse the dangling escape rather than answer."""
    words = shlex.split(call.strip().removesuffix("\\"), comments=True)
    return {word.split("=", 1)[0] for word in words[1:] if "=" in word}


def _calls_instrumenting(lines: list[str]) -> bool:
    return any(_is_instrumenting_call(line) for line in lines)


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
    a stray instrumenting call to one of these is caught as loudly as a missing one would be."""
    found = _launcher_files()
    for name in ("chain-development", "chain-product", "chain-agari", "product-skeleton"):
        path = Path(f"core/launchers/{name}/launcher.sh")
        assert path not in found, f"{name} invokes no claude run and should not be in the sweep"
        lines = _non_comment_lines(_REPO / path)
        assert not _calls_instrumenting(lines), (
            f"{name} calls an instrumenting function but spawns no run — nothing to tag"
        )


def test_every_claude_invoking_launcher_calls_an_instrumenting_function():
    """The rule. A launcher that starts a `claude` run and never instruments it is a run
    that reaches the receiver only if a person types the `OTEL_*` variables by hand — exactly the
    bar station 1 measured and this station exists to close."""
    offenders = [
        str(path) for path, lines in _launcher_files().items() if not _calls_instrumenting(lines)
    ]

    assert not offenders, (
        "these launchers start a claude run and never call an instrumenting function, so the "
        "run reaches "
        "the telemetry receiver only if someone types the OTEL_* variables by hand:\n  "
        + "\n  ".join(sorted(offenders))
    )


_HANDS_OVER = '"$INSTRUMENT_RUN_SETTINGS"'


def _call_index(lines: list[str]) -> int | None:
    return next((i for i, line in enumerate(lines) if _is_instrumenting_call(line)), None)


def _hands_settings_after_call(lines: list[str]) -> bool:
    """The value the call leaves behind is handed to a spawn, on a line after the call."""
    call = _call_index(lines)
    handed = [i for i, line in enumerate(lines) if _HANDS_OVER in line and "--settings" in line]
    return call is not None and any(i > call for i in handed)


def test_every_claude_invoking_launcher_hands_its_variables_to_the_spawn():
    """Task 7. Calling an instrumenting function exports the telemetry variables, and an exported
    variable never reaches a `claude --bg` session — measured 2026-09-10 over three haiku probes
    against the live receiver. What reaches it is `--settings`, so the value the
    call leaves behind has to be handed to the spawn, after the call that sets it."""
    offenders = [
        str(path)
        for path, lines in _launcher_files().items()
        if not _hands_settings_after_call(lines)
    ]
    assert not offenders, (
        'these launchers never pass --settings "$INSTRUMENT_RUN_SETTINGS" to their spawn after '
        "calling an instrumenting function, so a backgrounded run starts with no telemetry at "
        "all:\n  "
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

    Both instrumenting functions derive `kensai.arm` from the caller's own `$SCRIPT_DIR`, because
    that is
    the only value resolved at the right moment: a launcher takes it from its own
    `${BASH_SOURCE[0]}` *before* it `cd`s to the instance root, so it survives both the `cd` and
    a launcher started by a path relative to its own folder. A launcher that stopped resolving
    `SCRIPT_DIR` this way would still call its function, still pass every check above, and
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
        "what the instrumenting functions derive kensai.arm from:\n  "
        + "\n  ".join(sorted(offenders))
    )


def test_the_shared_library_exists_at_the_path_every_launcher_resolves():
    assert (_REPO / _CALL_LIBRARY).is_file(), (
        f"{_CALL_LIBRARY} is missing — every instrumented launcher's INSTRUMENT_LIB resolves "
        "to it"
    )


# --- Task 4 — every spawning launcher hands over what its usage names ----------------------

# usage token -> instrumenting-call key, per the plan's own table. Order doesn't matter for
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


def _swept_launchers(launchers_dir: Path = _LAUNCHERS_DIR) -> dict[Path, list[str]]:
    """Every launcher the guard holds to a usage-derived obligation, keyed by absolute path: the
    ones the call discovers (which includes a `--shape turn` runner the spawn sweep cannot see)
    and, on the real tree, the ones that spawn `claude` as well."""
    found = dict(_instrumented_launchers(launchers_dir))
    if launchers_dir == _LAUNCHERS_DIR:
        found.update({_REPO / path: lines for path, lines in _launcher_files().items()})
    return found


def _owed_subject_problems(launchers_dir: Path = _LAUNCHERS_DIR) -> list[str]:
    """One line per launcher whose call does not hand over every pair its usage line owes. The
    keys are read as shell words off the call's own line, so a comment, a `\\` continuation or a
    lookalike name (`other_project=`) never supplies one."""
    problems = []
    for path, lines in _swept_launchers(launchers_dir).items():
        owed = _owed_keys(_usage_line(path))
        if not owed:
            continue
        call_index = _call_index(lines)
        call = lines[call_index].strip() if call_index is not None else None
        missing = owed - (_handed_keys(call) if call is not None else set())
        if missing:
            problems.append(f"{path.parent.name}: missing {sorted(missing)} in {call!r}")
    return problems


def test_every_launchers_instrumenting_call_carries_the_pairs_its_usage_line_owes():
    """The rule, derived from disk rather than a hardcoded table — a usage line naming
    `<project>` or `--project` owes `project=`, `<document>` owes `document=`, `<skill>` owes
    `skill=`, and `<instance>` owes `target_instance=`. A launcher owing more than one owes all
    of them on its one call line, whichever instrumenting function that call is."""
    problems = _owed_subject_problems()
    assert not problems, (
        "these launchers owe key=value pairs their own usage line names, and their "
        "instrumenting call is missing at least one:\n  " + "\n  ".join(problems)
    )


def _no_subject_problems(launchers_dir: Path = _LAUNCHERS_DIR) -> list[str]:
    """One line per launcher owing no subject key whose call hands over anything but exactly the
    four provenance keys."""
    problems = []
    for path, lines in _swept_launchers(launchers_dir).items():
        if _owed_keys(_usage_line(path)):
            continue
        call_index = _call_index(lines)
        call = lines[call_index].strip() if call_index is not None else None
        if call is None or _handed_keys(call) != set(_PROVENANCE_KEYS):
            problems.append(f"{path.parent.name}: {call!r}")
    return problems


def test_a_launcher_owing_no_usage_key_carries_exactly_the_four_provenance_keys():
    """The negative half: a launcher owing no subject key hands over the four provenance keys every
    run is stamped with, and nothing else — it must not grow a subject key (`project=`,
    `document=`, `skill=`, `target_instance=`) by copying a sibling that has one. The keys are read
    as shell words off the call's own line, so a comment never supplies one.

    No launcher on disk owes no subject key since 2026-10-24, when the last one, `seeds-from-idea`'s,
    was deleted — the skill has no launcher of its own. On the real tree this reads nothing, then,
    and it holds the next such launcher the day it lands; that the rule catches one is proved on
    constructed launchers by `test_no_subject_usage_requires_only_provenance`."""
    problems = _no_subject_problems()
    assert not problems, (
        "these launchers owe no subject key per their own usage line, but their instrumenting "
        f"call hands over something other than exactly {list(_PROVENANCE_KEYS)}:\n  "
        + "\n  ".join(problems)
    )


# --- The fleet sweep — every instrumented launcher stamps its provenance -------------------

# Six launchers, every one calling `run_telemetry`: the skill launcher, and the five of the eleven
# that gained the four keys beside it still on disk. `kensaiapp-writing-bar`'s, `experience-visual`'s
# and `experience-voice`'s were deleted on 2026-09-30, each skill launching through the skill
# launcher from its `launcher.md`, and `product-sdd`'s on 2026-10-03 with the three-seat runner it
# launched, and `ratify`'s the same day, and `seeds-from-idea`'s on 2026-10-24, the skill having no
# launcher of its own. A count, not a list: which launchers call an instrumenting
# function is read from disk, and this number is what stops a broken glob or a predicate that
# matches nothing from reading as every launcher complying.
_INSTRUMENTED_LAUNCHER_COUNT = 6


def _instrumented_launchers(launchers_dir: Path = _LAUNCHERS_DIR) -> dict[Path, list[str]]:
    """Every `<launchers_dir>/*/launcher.sh` whose non-comment lines hold an instrumenting call
    (`run_telemetry`) — enumerated by the call itself, not by
    `_invokes_claude`, which never sees the `--shape turn` launcher (`companion-self-answer`) that
    is instrumented too."""
    found = {}
    for path in sorted(launchers_dir.glob("*/launcher.sh")):
        lines = _non_comment_lines(path)
        if _calls_instrumenting(lines):
            found[path] = lines
    return found


def _calls_missing_provenance(lines: list[str]) -> list[str]:
    """Each instrumenting call line that does not hand over all four provenance keys on its
    own line, described with the keys it lacks. Empty when every call carries them."""
    return [
        f"missing {[key for key in _PROVENANCE_KEYS if key not in _handed_keys(line)]} in "
        f"{line.strip()!r}"
        for line in lines
        if _is_instrumenting_call(line) and not set(_PROVENANCE_KEYS) <= _handed_keys(line)
    ]


def test_every_launcher_with_an_instrumenting_call_carries_the_four_provenance_keys_on_that_line():
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
        f"these instrumented launchers do not hand {list(_PROVENANCE_KEYS)} to their instrumenting "
        "call on its own line:\n  " + "\n  ".join(offenders)
    )


def test_the_call_sweep_finds_six_launchers():
    """A silent filter passes everything: a sweep that found nothing would pass the rule above.
    Six is the skill launcher and the five other launchers that spawn a run, each calling
    `run_telemetry`. A new instrumented launcher moves this number, deliberately, in the same
    commit that makes it one."""
    found = sorted(str(path.relative_to(_REPO)) for path in _instrumented_launchers())

    assert len(found) == _INSTRUMENTED_LAUNCHER_COUNT, (
        f"the call sweep found {len(found)} instrumented launchers, expected "
        f"{_INSTRUMENTED_LAUNCHER_COUNT}: {found}"
    )
    assert "core/launchers/companion-self-answer/launcher.sh" in found, (
        "the sweep missed a --shape turn launcher, which _invokes_claude cannot see"
    )


def test_all_six_real_launchers_use_the_shared_helper():
    """The migration is complete on the real tree: disk enumeration finds exactly six, each one
    resolves its library to the helper at the path the next test checks."""
    launchers = _instrumented_launchers()

    assert len(launchers) == _INSTRUMENTED_LAUNCHER_COUNT, sorted(map(str, launchers))
    assert (_REPO / _CALL_LIBRARY).is_file(), f"{_CALL_LIBRARY} is missing"
    resolves = f'INSTRUMENT_LIB="$CORE_DIR/{_CALL_LIBRARY.relative_to("core")}"'
    offenders = [
        f"{path.relative_to(_REPO)}: does not set {resolves}"
        for path in launchers
        if resolves not in _non_comment_lines(path)
    ]
    assert not offenders, "\n  ".join(["not every launcher uses the shared helper:", *offenders])


def test_a_continued_call_line_does_not_satisfy_the_sweep(tmp_path: Path):
    """CP-229 on a constructed launcher: the four keys on the `\\`-continued line below the call
    are not on the call's line, so the sweep names that launcher — and a sibling whose call holds
    them on its own line is not named, so the sweep is not failing everything."""
    continued = tmp_path / "continued" / "launcher.sh"
    continued.parent.mkdir()
    continued.write_text(
        "#!/usr/bin/env bash\n"
        'run_telemetry skill="$skill" \\\n'
        '  provider=claude model="$run_model" effort="$run_effort" source="$run_source"\n'
    )
    one_line = tmp_path / "one-line" / "launcher.sh"
    one_line.parent.mkdir()
    one_line.write_text(
        "#!/usr/bin/env bash\n"
        'run_telemetry skill="$skill" provider=claude model="$run_model" effort="$run_effort"'
        ' source="$run_source"\n'
    )

    swept = _instrumented_launchers(tmp_path)

    assert set(swept) == {continued, one_line}
    assert _calls_missing_provenance(swept[continued]) == [
        "missing ['provider', 'model', 'effort', 'source'] in "
        "'run_telemetry skill=\"$skill\" \\\\'"
    ]
    assert _calls_missing_provenance(swept[one_line]) == []


# --- The one instrumenting call — `run_telemetry` -------------------------------------------

_CALL = _INSTRUMENTING_CALL
_FOUR_KEYS = 'provider="$p" model="$m" effort="$e" source="$s"'


def _write_launcher(root: Path, name: str, usage: str, body: str) -> Path:
    """A constructed `<root>/<name>/launcher.sh` with a `# USAGE` block, for counterexamples."""
    path = root / name / "launcher.sh"
    path.parent.mkdir(parents=True)
    path.write_text(f"#!/usr/bin/env bash\n# USAGE\n#   {usage}\n{body}\n")
    return path


@pytest.mark.parametrize(
    "line",
    [
        "{name}",
        "  {name}",
        "{name} skill=x",
        '  {name} skill="$skill" project="$project" ' + _FOUR_KEYS,
        "\t{name}   provider=claude",
    ],
)
def test_the_retained_call_is_discovered(line: str):
    assert _is_instrumenting_call(line.format(name=_CALL))


@pytest.mark.parametrize(
    "line",
    [
        "{name}() {{",
        "function {name} {{",
        '{name}_helper skill="x"',
        'source "$CORE_DIR/tools/{name}.sh"',
        '. "$CORE_DIR/tools/{name}.sh"',
        'HELPER="$CORE_DIR/tools/{name}.sh"',
        "# {name} skill=x",
        '[ -f "$CORE_DIR/tools/{name}.sh" ] && echo {name}',
        'echo "{name} skill=x"',
    ],
)
def test_definitions_paths_comments_and_sourcing_are_not_calls(line: str):
    assert not _is_instrumenting_call(line.format(name=_CALL))


def test_a_call_sweep_discovers_the_call_on_disk(tmp_path: Path):
    _write_launcher(tmp_path, "caller", "<skill>", f'{_CALL} skill="$skill" {_FOUR_KEYS}')
    _write_launcher(tmp_path, "sourcing-only", "<skill>", f'source "$CORE/tools/{_CALL}.sh"')
    _write_launcher(tmp_path, "commented", "<skill>", f"# {_CALL} skill=x")

    assert [p.parent.name for p in _instrumented_launchers(tmp_path)] == ["caller"]


def test_the_call_sweep_keeps_six_launchers_including_skill():
    found = {str(path.relative_to(_REPO)) for path in _instrumented_launchers()}

    assert len(found) == _INSTRUMENTED_LAUNCHER_COUNT == 6, sorted(found)
    assert "core/launchers/skill/launcher.sh" in found
    assert "core/launchers/companion-self-answer/launcher.sh" in found


@pytest.mark.parametrize("missing", _PROVENANCE_KEYS)
def test_each_call_requires_all_provenance_keys_on_its_own_line(missing: str):
    keys = " ".join(f'{key}="${key[0]}"' for key in _PROVENANCE_KEYS if key != missing)

    problems = _calls_missing_provenance([f'{_CALL} skill="$skill" {keys}'])

    assert len(problems) == 1 and missing in problems[0]


@pytest.mark.parametrize(
    "lines",
    [
        ['{name} skill="$skill" \\', '  ' + _FOUR_KEYS],
        ['{name} skill="$skill" ' + _FOUR_KEYS.replace("source=", "run_source=")],
        ['{name} skill="$skill" # ' + _FOUR_KEYS],
        ['{name} skill="$skill" provider="$p" model="$m" effort="$e" # source="$s"'],
    ],
    ids=["continued-line", "similarly-named-key", "trailing-comment", "key-only-in-comment"],
)
def test_a_continued_commented_or_lookalike_key_supplies_no_provenance(lines: list[str]):
    problems = _calls_missing_provenance([line.format(name=_CALL) for line in lines])

    assert problems, "the call was held to nothing"


def test_a_call_with_all_four_keys_on_its_line_has_no_provenance_problem():
    assert _calls_missing_provenance([f'{_CALL} skill="$skill" {_FOUR_KEYS}']) == []


_TURN_USAGE = "<CORE>/launchers/x/launcher.sh <skill> <project> [--provider claude]"


def test_call_discovered_launchers_owe_their_usage_subjects(tmp_path: Path):
    ok = _write_launcher(
        tmp_path, "ok", _TURN_USAGE, f'{_CALL} skill="$skill" project="$project" {_FOUR_KEYS}'
    )
    no_project = _write_launcher(
        tmp_path, "no-project", _TURN_USAGE, f'{_CALL} skill="$skill" {_FOUR_KEYS}'
    )
    no_skill = _write_launcher(
        tmp_path, "no-skill", _TURN_USAGE, f'{_CALL} project="$project" {_FOUR_KEYS}'
    )
    commented = _write_launcher(
        tmp_path,
        "commented",
        _TURN_USAGE,
        f'{_CALL} skill="$skill" {_FOUR_KEYS} # project="$project"',
    )
    continued = _write_launcher(
        tmp_path,
        "continued",
        _TURN_USAGE,
        f'{_CALL} skill="$skill" {_FOUR_KEYS} \\\n  project="$project"',
    )
    lookalike = _write_launcher(
        tmp_path,
        "lookalike",
        _TURN_USAGE,
        f'{_CALL} skill="$skill" other_project="$project" {_FOUR_KEYS}',
    )

    problems = _owed_subject_problems(tmp_path)

    named = {p.parent.name for p in (no_project, no_skill, commented, continued, lookalike)}
    assert {line.split(":")[0] for line in problems} == {f"{n}" for n in named}
    assert not any(line.startswith(f"{ok.parent.name}:") for line in problems)
    assert "project" in next(line for line in problems if line.startswith("no-project:"))
    assert "skill" in next(line for line in problems if line.startswith("no-skill:"))


def test_no_subject_usage_requires_only_provenance(tmp_path: Path):
    _write_launcher(tmp_path, "exact", "[--provider claude]", f"{_CALL} {_FOUR_KEYS}")
    _write_launcher(tmp_path, "grown", "[--provider claude]", f'{_CALL} skill="$s" {_FOUR_KEYS}')
    _write_launcher(tmp_path, "short", "[--provider claude]", f'{_CALL} provider="$p"')

    problems = _no_subject_problems(tmp_path)

    assert sorted(line.split(":")[0] for line in problems) == ["grown", "short"]


def test_the_real_fleet_meets_both_usage_obligations():
    assert _owed_subject_problems(_LAUNCHERS_DIR) == []
    assert _no_subject_problems(_LAUNCHERS_DIR) == []


def test_legacy_spawn_and_nonspawning_exclusions_still_hold(tmp_path: Path):
    handed = 'claude --bg --settings "$INSTRUMENT_RUN_SETTINGS" x'
    # The settings handoff must come after the call.
    assert _hands_settings_after_call([f'{_CALL} skill="x"', handed])
    assert not _hands_settings_after_call([handed, f'{_CALL} skill="x"'])
    assert not _hands_settings_after_call([f'{_CALL} skill="x"', "claude --bg x"])
    assert not _hands_settings_after_call([handed])

    # A launcher that spawns nothing is outside the claude sweep, whatever it calls.
    _write_launcher(tmp_path, "quiet", "<skill>", f'{_CALL} skill="$skill" {_FOUR_KEYS}')
    quiet = _non_comment_lines(tmp_path / "quiet" / "launcher.sh")
    assert not _invokes_claude(quiet)
    assert _calls_instrumenting(quiet)

    # The spawn sweep keeps its subject set on the real tree.
    found = _launcher_files()
    for kept in ("cold-read", "product-card"):
        assert Path(f"core/launchers/{kept}/launcher.sh") in found
