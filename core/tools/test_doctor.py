"""Tests for core/tools/doctor.sh and the root Brewfile it is paired with.

The doctor is run for real, as a subprocess, through an absolute interpreter and script path, so the
child's PATH is controlled on its own: a stub's body uses builtins only, and an empty PATH does not
disable the fixtures. No assertion depends on a real tool's installed version (CP-916); the floors
are read from the doctor's own `--help`, never copied into a table here.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

BASH = "/bin/bash"
DOCTOR = Path(__file__).resolve().parent / "doctor.sh"
LABELS = ("uv", "git", "podman", "tart", "gh", "claude")
USAGE = "doctor: usage: <CORE>/tools/doctor.sh [--help]\n"
SCRATCH_HOME_VARIABLE = "DOCTOR_TEST_SCRATCH_HOME"
FLOOR_ROW = re.compile(r"^(uv|git|podman|tart|gh|claude): (\d+(?:\.\d+)+)$")

# Each tool's own first version line, as the tool prints it (change_spec.md § Verified Claims).
NATIVE_FIRST_LINE = {
    "uv": "uv {v} (3fdfdc7d4 2026-05-12 aarch64-apple-darwin)",
    "git": "git version {v} (Apple Git-157)",
    "podman": "podman version {v}",
    "tart": "{v}",
    "gh": "gh version {v} (2026-10-23)",
    "claude": "{v} (Claude Code)",
}

HELP_TEMPLATE = """\
usage: <CORE>/tools/doctor.sh [--help]

Checks whether this machine has the six tools kensaiapp runs on, each at its minimum version.
Prints one line per tool: present, missing or too old.
Each tool is named by its command, and claude is Claude Code.
A tool is checked where your PATH finds it first, so a tool outside your PATH is reported missing.
Nothing is installed, upgraded or changed.
Exits 0 when all six are present, 1 when any is missing or too old, and 2 for any argument other than --help.

Minimum versions:
{rows}
"""


def make_stub(
    directory: Path,
    label: str,
    *,
    stdout: tuple[str, ...] = (),
    stderr: tuple[str, ...] = (),
    exit_code: int = 0,
    record: Path | None = None,
    shebang: str = "#!/bin/bash",
) -> Path:
    """An executable answering `--version` with builtins only, so an empty PATH cannot break it."""
    directory.mkdir(parents=True, exist_ok=True)
    lines = [shebang]
    if record is not None:
        lines.append(f'echo "$#:$*" >> {shlex.quote(str(record))}')
    for text in stdout:
        lines.append(f"printf '%s\\n' {shlex.quote(text)}")
    for text in stderr:
        lines.append(f"printf '%s\\n' {shlex.quote(text)} >&2")
    lines.append(f"exit {exit_code}")
    path = directory / label
    path.write_text("\n".join(lines) + "\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def run_doctor(
    *args: str, path: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [BASH, str(DOCTOR), *args],
        env={"PATH": path, "HOME": os.environ[SCRATCH_HOME_VARIABLE]},
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(autouse=True)
def scratch_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A real tool linked in by the missing-tool cases may write under HOME (gh does)."""
    home = tmp_path / "scratch-home"
    home.mkdir()
    monkeypatch.setenv(SCRATCH_HOME_VARIABLE, str(home))


@pytest.fixture
def floors(tmp_path: Path) -> dict[str, str]:
    """The six `{label}: {floor}` rows of the doctor's own help, in the doctor's order."""
    empty = tmp_path / "empty-for-help"
    empty.mkdir()
    result = run_doctor("--help", path=str(empty))
    assert result.returncode == 0, result.stderr
    rows = [FLOOR_ROW.match(line) for line in result.stdout.splitlines()]
    found = {match.group(1): match.group(2) for match in rows if match}
    assert tuple(found) == LABELS
    return found


def first_line(label: str, version: str) -> str:
    return NATIVE_FIRST_LINE[label].format(v=version)


def stubs_at(directory: Path, versions: dict[str, str], record_dir: Path | None = None) -> None:
    for label in LABELS:
        record = record_dir / f"{label}.log" if record_dir else None
        make_stub(directory, label, stdout=(first_line(label, versions[label]),), record=record)


def lower_than(floor: str) -> str:
    """A version one step below `floor`: the last nonzero group decremented."""
    groups = [int(group) for group in floor.split(".")]
    index = max(i for i, group in enumerate(groups) if group > 0)
    groups[index] -= 1
    return ".".join(str(group) for group in groups)


def present(label: str, version: str) -> str:
    return f"{label}: present ({version})"


def too_old(label: str, version: str, floor: str) -> str:
    return f"{label}: too old ({version}, needs {floor} or later)"


def unreadable(label: str, floor: str) -> str:
    return f"{label}: too old (version unreadable, needs {floor} or later)"


# --- T1 ---------------------------------------------------------------------------------------


def test_all_tools_at_floor_are_present_in_order(tmp_path: Path, floors: dict[str, str]) -> None:
    bin_dir = tmp_path / "bin"
    stubs_at(bin_dir, floors)
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()
    expected = [present(label, floors[label]) for label in LABELS]

    for cwd in (None, elsewhere):
        result = run_doctor(path=str(bin_dir), cwd=cwd)
        assert result.stdout.splitlines() == expected
        assert result.returncode == 0
        assert result.stderr == ""


# --- T2 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("removed", LABELS)
def test_removed_tool_is_missing_with_real_tool_links(tmp_path: Path, removed: str) -> None:
    links = tmp_path / "links"
    links.mkdir()
    for label in LABELS:
        real = shutil.which(label)
        if label != removed and real:
            (links / label).symlink_to(real)

    result = run_doctor(path=str(links))

    lines = result.stdout.splitlines()
    assert len(lines) == 6
    assert [line.split(":")[0] for line in lines] == list(LABELS)
    assert lines[LABELS.index(removed)] == f"{removed}: missing"
    assert result.returncode == 1


# --- T3 ---------------------------------------------------------------------------------------


def test_empty_tool_directory_needs_no_uv_python_or_bash_on_path(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    result = run_doctor(path=str(empty))

    assert result.stdout.splitlines() == [f"{label}: missing" for label in LABELS]
    assert result.returncode == 1
    assert result.stderr == ""


# --- T4 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("old", LABELS)
def test_each_tool_below_floor_is_too_old(tmp_path: Path, floors: dict[str, str], old: str) -> None:
    bin_dir = tmp_path / "bin"
    versions = dict(floors)
    versions[old] = lower_than(floors[old])
    stubs_at(bin_dir, versions)

    result = run_doctor(path=str(bin_dir))

    expected = [present(label, floors[label]) for label in LABELS]
    expected[LABELS.index(old)] = too_old(old, versions[old], floors[old])
    assert result.stdout.splitlines() == expected
    assert result.returncode == 1
    assert result.stderr == ""


def test_gh_zero_one_zero_is_too_old(tmp_path: Path, floors: dict[str, str]) -> None:
    bin_dir = tmp_path / "bin"
    stubs_at(bin_dir, floors)
    make_stub(bin_dir, "gh", stdout=("gh version 0.1.0 (2020-01-01)",))

    result = run_doctor(path=str(bin_dir))

    assert too_old("gh", "0.1.0", floors["gh"]) in result.stdout.splitlines()
    assert result.returncode == 1


# --- T5 ---------------------------------------------------------------------------------------

BIG = "99.01.002"


@pytest.mark.parametrize("label", LABELS)
def test_first_dotted_number_on_first_stdout_line_decides_native_forms(
    tmp_path: Path, label: str
) -> None:
    bin_dir = tmp_path / "bin"
    make_stub(bin_dir, label, stdout=(first_line(label, BIG), "more 1.0.0"))

    result = run_doctor(path=str(bin_dir))

    assert present(label, BIG) in result.stdout.splitlines()


@pytest.mark.parametrize(
    ("stdout", "stderr", "shown"),
    [
        (("tool 99.1.0 build 98.2.0",), (), "99.1.0"),
        (("tool 99.5.5", "88.0.0"), (), "99.5.5"),
        (("v3 (2026-10-23) 99.2.1",), (), "99.2.1"),
        (("tool 99.3.3",), ("tool 1.0.0",), "99.3.3"),
        (("99.1.311 (Claude Code)",), (), "99.1.311"),
    ],
    ids=["two-numbers", "later-line", "date-before-version", "ignore-stderr", "unprefixed"],
)
def test_first_dotted_number_on_first_stdout_line_decides(
    tmp_path: Path, stdout: tuple[str, ...], stderr: tuple[str, ...], shown: str
) -> None:
    bin_dir = tmp_path / "bin"
    make_stub(bin_dir, "gh", stdout=stdout, stderr=stderr)

    result = run_doctor(path=str(bin_dir))

    assert present("gh", shown) in result.stdout.splitlines()


# --- T6 ---------------------------------------------------------------------------------------

UNREADABLE_MODES = {
    "exit-1-with-number": dict(stdout=("tool 99.0.0",), exit_code=1),
    "bad-interpreter": dict(stdout=("tool 99.0.0",), shebang="#!/nonexistent/interpreter"),
    "no-number": dict(stdout=("tart",)),
    "no-output": dict(),
    "empty-first-line": dict(stdout=("", "tool 99.0.0")),
    "stderr-only": dict(stderr=("tool 99.0.0",)),
}


@pytest.mark.parametrize("mode", UNREADABLE_MODES)
@pytest.mark.parametrize("label", LABELS)
def test_unreadable_version_does_not_stop_later_reports(
    tmp_path: Path, floors: dict[str, str], label: str, mode: str
) -> None:
    bin_dir = tmp_path / "bin"
    stubs_at(bin_dir, floors)
    make_stub(bin_dir, label, **UNREADABLE_MODES[mode])

    result = run_doctor(path=str(bin_dir))

    expected = [present(other, floors[other]) for other in LABELS]
    expected[LABELS.index(label)] = unreadable(label, floors[label])
    assert result.stdout.splitlines() == expected
    assert result.returncode == 1
    assert result.stderr == ""


def test_valid_stdout_decides_and_probe_noise_stays_out_of_the_report(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    bin_dir = tmp_path / "bin"
    stubs_at(bin_dir, floors)
    make_stub(
        bin_dir, "podman",
        stdout=(first_line("podman", floors["podman"]),),
        stderr=("warning: noisy 1.0.0", "error: diagnostics"),
    )

    result = run_doctor(path=str(bin_dir))

    assert result.stdout.splitlines() == [present(l, floors[l]) for l in LABELS]
    assert result.returncode == 0
    assert result.stderr == ""


# --- T7 ---------------------------------------------------------------------------------------

WIDE = "99999999999999999999999999999999"
WIDER = "99999999999999999999999999999998"

# (a, b, relation): "equal" means a == b; "greater" means a > b.
COMPARISONS = [
    ("2.10.0", "2.9.0", "greater"),
    ("2.41", "2.41.0", "equal"),
    ("2.9.0", "2.9.0", "equal"),
    ("01.02", "1.2", "equal"),
    ("08.09", "8.9", "equal"),
    ("2.0009", "2.9", "equal"),
    ("1.010", "1.9", "greater"),
    ("1.10", "1.009", "greater"),
    ("2.9.1", "2.9.0", "greater"),
    ("2.10.0", "2.9.9", "greater"),
    ("3.0.0", "2.99.99", "greater"),
    ("2.41.0.1", "2.41", "greater"),
    ("2.41.0.0.0", "2.41", "equal"),
    ("2.41.0.0.1", "2.41.0.0", "greater"),
    (f"{WIDE}.0", f"{WIDER}.9", "greater"),
    (f"1.{WIDE}", f"1.{WIDE}", "equal"),
    ("1.100", "1.99", "greater"),
]


def version_at_least(version: str, floor: str) -> int:
    result = subprocess.run(
        [BASH, "-c", 'source "$1"; _version_at_least "$2" "$3"',
         "caller", str(DOCTOR), version, floor],
        env={"PATH": "/nonexistent"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout == "" and result.stderr == ""
    return result.returncode


@pytest.mark.parametrize(("a", "b", "relation"), COMPARISONS)
def test_version_comparison_is_numeric_and_zero_padded(a: str, b: str, relation: str) -> None:
    assert version_at_least(a, b) == 0
    assert version_at_least(b, a) == (0 if relation == "equal" else 1)


# --- T8 ---------------------------------------------------------------------------------------


def test_first_executable_path_entry_is_the_only_copy_queried(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    first, later = tmp_path / "first", tmp_path / "later"
    below = lower_than(floors["git"])
    first_log, later_log = tmp_path / "first.log", tmp_path / "later.log"
    make_stub(first, "git", stdout=(first_line("git", below),), record=first_log)
    make_stub(later, "git", stdout=(first_line("git", floors["git"]),), record=later_log)

    result = run_doctor(path=f"{first}:{later}")

    assert too_old("git", below, floors["git"]) in result.stdout.splitlines()
    assert first_log.read_text() == "1:--version\n"
    assert not later_log.exists()


def test_failed_first_executable_does_not_fall_through_to_a_later_copy(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    first, later = tmp_path / "first", tmp_path / "later"
    later_log = tmp_path / "later.log"
    make_stub(first, "git", stdout=("git version 99.0.0",), exit_code=1)
    make_stub(later, "git", stdout=(first_line("git", floors["git"]),), record=later_log)

    result = run_doctor(path=f"{first}:{later}")

    assert unreadable("git", floors["git"]) in result.stdout.splitlines()
    assert not later_log.exists()


def _scenario_non_executable_file(root: Path, floors: dict[str, str]) -> tuple[str, Path | None]:
    (root / "a").mkdir()
    (root / "a" / "git").write_text("#!/bin/bash\necho 'git version 1.0.0'\n")
    (root / "a" / "git").chmod(0o644)
    make_stub(root / "b", "git", stdout=(first_line("git", BIG),))
    return f"{root / 'a'}:{root / 'b'}", None


def _scenario_directory_named_git(root: Path, floors: dict[str, str]) -> tuple[str, Path | None]:
    (root / "a" / "git").mkdir(parents=True)
    make_stub(root / "b", "git", stdout=(first_line("git", BIG),))
    return f"{root / 'a'}:{root / 'b'}", None


def _scenario_symlinked_executable(root: Path, floors: dict[str, str]) -> tuple[str, Path | None]:
    real = make_stub(root / "real", "actual-git", stdout=(first_line("git", BIG),))
    (root / "a").mkdir()
    (root / "a" / "git").symlink_to(real)
    return str(root / "a"), None


def _scenario_directory_with_spaces(root: Path, floors: dict[str, str]) -> tuple[str, Path | None]:
    make_stub(root / "my bin dir", "git", stdout=(first_line("git", BIG),))
    return str(root / "my bin dir"), None


def _empty_component_scenario(template: str):
    def build(root: Path, floors: dict[str, str]) -> tuple[str, Path | None]:
        cwd = root / "cwd"
        make_stub(cwd, "git", stdout=(first_line("git", BIG),))
        one, two = root / "one", root / "two"
        one.mkdir()
        two.mkdir()
        return template.format(one=one, two=two), cwd

    return build


PATH_SCENARIOS = {
    "earlier-non-executable-file": _scenario_non_executable_file,
    "earlier-directory-named-git": _scenario_directory_named_git,
    "symlinked-executable": _scenario_symlinked_executable,
    "directory-with-spaces": _scenario_directory_with_spaces,
    "empty-component-at-start": _empty_component_scenario(":{one}"),
    "empty-component-in-middle": _empty_component_scenario("{one}::{two}"),
    "empty-component-at-end": _empty_component_scenario("{one}:"),
}


@pytest.mark.parametrize("scenario", PATH_SCENARIOS)
def test_path_discovery_preserves_file_and_directory_semantics(
    tmp_path: Path, floors: dict[str, str], scenario: str
) -> None:
    path, cwd = PATH_SCENARIOS[scenario](tmp_path, floors)

    result = run_doctor(path=path, cwd=cwd)

    assert present("git", BIG) in result.stdout.splitlines()


def test_current_directory_is_searched_only_through_an_empty_component(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    cwd, only = tmp_path / "cwd", tmp_path / "only"
    make_stub(cwd, "git", stdout=(first_line("git", BIG),))
    only.mkdir()

    result = run_doctor(path=str(only), cwd=cwd)

    assert "git: missing" in result.stdout.splitlines()


# --- T9 / T11 ---------------------------------------------------------------------------------


def test_help_exposes_six_ordered_valid_floors_without_probes(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    bin_dir, records = tmp_path / "bin", tmp_path / "records"
    records.mkdir()
    stubs_at(bin_dir, floors, record_dir=records)

    result = run_doctor("--help", path=str(bin_dir))

    rows = [line for line in result.stdout.splitlines() if FLOOR_ROW.match(line)]
    assert rows == [f"{label}: {floors[label]}" for label in LABELS]
    expected = HELP_TEMPLATE.format(rows="\n".join(rows))
    assert result.stdout == expected
    assert result.returncode == 0
    assert result.stderr == ""
    assert list(records.iterdir()) == []


# --- T10 --------------------------------------------------------------------------------------


def test_report_runs_only_found_tools_with_version_argument(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    bin_dir, records = tmp_path / "bin", tmp_path / "records"
    records.mkdir()
    stubs_at(bin_dir, floors, record_dir=records)
    for sentinel in ("brew", "docker", "python", "sentinel"):
        make_stub(bin_dir, sentinel, stdout=("x 1.0.0",), record=records / f"{sentinel}.log")
    fixture_bytes = {p: p.read_bytes() for p in bin_dir.iterdir()}

    result = run_doctor(path=str(bin_dir))

    assert result.returncode == 0
    for label in LABELS:
        assert (records / f"{label}.log").read_text() == "1:--version\n"
    for sentinel in ("brew", "docker", "python", "sentinel"):
        assert not (records / f"{sentinel}.log").exists()
    assert {p: p.read_bytes() for p in bin_dir.iterdir()} == fixture_bytes
    assert sorted(p.name for p in records.iterdir()) == sorted(f"{label}.log" for label in LABELS)


# --- T11 --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "arguments",
    [
        ["--frobnicate"],
        ["positional"],
        ["--help", "--help"],
        ["--help", "extra"],
        ["extra", "--help"],
        [""],
    ],
    ids=[
        "unknown-flag", "positional", "help-twice", "help-plus-argument",
        "argument-then-help", "empty",
    ],
)
def test_invalid_argument_vectors_print_only_usage_to_stderr(
    tmp_path: Path, floors: dict[str, str], arguments: list[str]
) -> None:
    bin_dir, records = tmp_path / "bin", tmp_path / "records"
    records.mkdir()
    stubs_at(bin_dir, floors, record_dir=records)

    result = run_doctor(*arguments, path=str(bin_dir))

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == USAGE
    assert list(records.iterdir()) == []


def test_sourcing_defines_comparator_without_output_or_probes(
    tmp_path: Path, floors: dict[str, str]
) -> None:
    bin_dir, records = tmp_path / "bin", tmp_path / "records"
    records.mkdir()
    stubs_at(bin_dir, floors, record_dir=records)

    sourced = subprocess.run(
        [BASH, "-c", 'source "$1"', "caller", str(DOCTOR)],
        env={"PATH": str(bin_dir)}, capture_output=True, text=True, check=False,
    )

    assert (sourced.returncode, sourced.stdout, sourced.stderr) == (0, "", "")
    assert list(records.iterdir()) == []
    assert version_at_least("2.0", "2.0") == 0
    assert version_at_least("2.1", "2.0") == 0
    assert version_at_least("1.9", "2.0") == 1


# --- house markers (added beyond the instruction) -----------------------------------------------


def test_doctor_script_carries_the_house_shell_markers() -> None:
    text = DOCTOR.read_text()
    lines = text.splitlines()
    assert lines[0] == "#!/usr/bin/env bash"
    assert os.access(DOCTOR, os.X_OK)
    assert re.search(r"^# Version: \d+\.\d+\.\d+", text, re.MULTILINE)
    parse = subprocess.run([BASH, "-n", str(DOCTOR)], capture_output=True, text=True, check=False)
    assert (parse.returncode, parse.stderr) == (0, "")


# --- the paired Homebrew inventory (CP-913, CP-915) ----------------------------------------------

BREWFILE = Path(__file__).resolve().parents[2] / "Brewfile"
HOMEBREW_NAME_OF = {"claude": "claude-code"}
DECLARATION = re.compile(r'^(?P<kind>[a-z]+) "(?P<name>[^"\s]+)"$')
INSTALL_KINDS = ("brew", "cask")
INTENDED_MANIFEST = """\
tap "cirruslabs/cli"
brew "uv"
brew "git"
brew "podman"
brew "cirruslabs/cli/tart"
brew "gh"
cask "claude-code"
"""


def help_labels(floors_text: str) -> list[str]:
    """The labels of a doctor `--help` `{label}: {floor}` data rows, in order, repeats kept."""
    return [m.group(1) for line in floors_text.splitlines() if (m := FLOOR_ROW.match(line))]


def inventory_problems(brewfile: str, labels: list[str]) -> list[str]:
    """Every way the Brewfile and the doctor's labels fail to pair one-to-one; empty means paired.

    Parses only the literal grammar the Brewfile uses: blank lines, `#` comments, and
    `tap|brew|cask "name"`. Anything else is reported rather than ignored.
    """
    problems: list[str] = []
    taps: list[str] = []
    installs: list[tuple[str, str]] = []
    for raw in brewfile.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = DECLARATION.match(line)
        if match is None or match["kind"] not in (*INSTALL_KINDS, "tap"):
            problems.append(f"unsupported declaration: {line}")
        elif match["kind"] == "tap":
            taps.append(match["name"])
        else:
            installs.append((match["kind"], match["name"]))

    for label in sorted({label for label in labels if labels.count(label) > 1}):
        problems.append(f"{label}: repeated in the doctor's inventory")
    expected = {HOMEBREW_NAME_OF.get(label, label): label for label in labels}
    seen: dict[str, int] = {}
    for _, name in installs:
        final = name.rsplit("/", 1)[-1]
        seen[final] = seen.get(final, 0) + 1
        if final not in expected:
            problems.append(f"{name}: in the Brewfile, but no doctor tool pairs with it")
    for final, count in seen.items():
        if count > 1:
            problems.append(f"{final}: installed {count} times in the Brewfile")
    for final, label in expected.items():
        if final not in seen:
            problems.append(f"{label}: in the doctor's inventory, but {final} is not installed")

    needed = {name.rsplit("/", 1)[0] for _, name in installs if name.count("/") == 2}
    for tap in taps:
        if tap not in needed:
            problems.append(f"tap {tap}: no install entry names it")
    for tap in sorted(needed - set(taps)):
        problems.append(f"tap {tap}: an install entry names it, but it is not declared")
    return problems


def doctor_help_text(tmp_path: Path) -> str:
    empty = tmp_path / "empty-for-help"
    empty.mkdir()
    result = run_doctor("--help", path=str(empty))
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_root_brewfile_matches_real_doctor_inventory(tmp_path: Path) -> None:
    labels = help_labels(doctor_help_text(tmp_path))
    assert tuple(labels) == LABELS
    assert BREWFILE.is_file(), f"{BREWFILE} does not exist"

    assert inventory_problems(BREWFILE.read_text(), labels) == []


@pytest.mark.parametrize(
    ("manifest", "labels", "named"),
    [
        (INTENDED_MANIFEST + 'brew "jq"\n', LABELS, "jq"),
        (INTENDED_MANIFEST.replace('brew "git"\n', ""), LABELS, "git"),
        (INTENDED_MANIFEST, tuple(label for label in LABELS if label != "tart"), "tart"),
        (INTENDED_MANIFEST + 'brew "gh"\n', LABELS, "gh"),
        (INTENDED_MANIFEST, LABELS + ("gh",), "gh"),
        (INTENDED_MANIFEST + 'tap "homebrew/core"\n', LABELS, "homebrew/core"),
        (INTENDED_MANIFEST.replace('tap "cirruslabs/cli"\n', ""), LABELS, "cirruslabs/cli"),
        (INTENDED_MANIFEST + 'mas "Xcode", id: 497799835\n', LABELS, "mas"),
        (INTENDED_MANIFEST + 'vscode "ms-python.python"\n', LABELS, "vscode"),
    ],
    ids=[
        "seventh-install", "missing-install", "doctor-lacks-tart", "duplicate-install",
        "duplicate-help-label", "unrelated-tap", "missing-required-tap",
        "unsupported-mas", "unsupported-vscode",
    ],
)
def test_inventory_check_rejects_unpaired_or_repeated_entries(
    manifest: str, labels: tuple[str, ...], named: str
) -> None:
    problems = inventory_problems(manifest, list(labels))

    assert problems != []
    assert any(named in problem for problem in problems), problems


def test_inventory_check_accepts_required_tap_and_claude_pairing() -> None:
    assert inventory_problems(INTENDED_MANIFEST, list(LABELS)) == []
    commented = "# the six\n\n" + INTENDED_MANIFEST
    assert inventory_problems(commented, list(LABELS)) == []
