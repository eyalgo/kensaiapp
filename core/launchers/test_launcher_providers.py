"""The seven skill launchers take their provider from the instance's own provider file, and refuse
by name when it cannot give one — proved the same way for every launcher, from one builder.

WHY THIS EXISTS
    The instance's `.providers.toml` holds one `[launchers]` entry per instance skill launcher,
    and `core/tools/providers.py` is its only reader. A launcher with its entry missing, or naming a
    provider it cannot run, must refuse before any agent run starts and before any completion
    watcher is spawned; a dry run refuses exactly where the launch would. That is one behaviour
    seven times over, so the cases are parametrized over `LAUNCHERS` rather than written into seven
    suites, and each launcher's own suite keeps the cases that are about its own command line.

    A launcher is run from a copy of the host (`provenance_test_support.isolated_host`): the real
    script, the real reader and a `.providers.toml` the test writes at the root of the instance the
    launcher runs for, beside stubs for `claude`, `codex` and `agy` that record any call and for
    the two watchers that record any spawn. No environment variable or flag selects the file: the
    instance's own `.providers.toml` is the only one the reader reads (CP-483). The host copy is
    a pin and the instance a folder beside it, so a decoy at the host root can be told from the
    instance's file.

Adding a launcher to the proof is one row of `LAUNCHERS`.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from provenance_test_support import HOST_TOOLS, isolated_host

_CORE = Path(__file__).resolve().parents[1]
# The delivered text is the tracked template at the instance root, located from this file:
# core/launchers/test_launcher_providers.py -> parents[2]. No suite leans on a live
# `.providers.toml`, which is untracked and absent from a fresh checkout.
_EXAMPLE = Path(__file__).resolve().parents[2] / ".providers.toml.example"
_DELIVERED = _EXAMPLE.read_text(encoding="utf-8")

# What a launcher reaches before it decides, or would reach once it launched — the real files, so
# a refusal that comes too late shows up as a stub that was called.
_EXTRA_TOOLS = (
    "detach_watcher.sh",
    "detach_process_watcher.sh",
    "detached_run.sh",
    "skill_path.py",
    "task_context.py",
    "env_file.py",
    "codex_skill_run.py",
)
_RECORDING_STUBS = ("watch_agent.py", "watch_process.py")

_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$(basename "$0") $*" >> "$STUB_CALLS_LOG"
exit 0
"""
_WATCHER_STUB = """import os, sys
with open(os.environ["STUB_CALLS_LOG"], "a") as log:
    log.write("watcher " + " ".join(sys.argv[1:]) + "\\n")
"""


@dataclass(frozen=True)
class Launcher:
    """One launcher under proof: its folder name (which is its entry's key), and the arguments of
    a launch that is valid in shape, so it reaches the read with no skill, project or round
    placed."""

    name: str
    args: tuple[str, ...]
    forcible: bool = False
    # What a forced launch that got past the provider decision has said by the time the copy stops
    # (its copy places no skill or project, so it stops at the next thing it needs).
    reached: str = ""
    # A launcher that checks its project card before it reads the provider file is given one:
    # the name of a project whose card the copy places under its instance.
    card: str = ""
    # Files, relative to the copy's instance, a launch needs to exist so that nothing before the
    # provider read can be the reason it stops: an idea the launcher is pointed at.
    files: tuple[str, ...] = ()


LAUNCHERS = (
    Launcher("skill", ("demo", "some-project"), forcible=True, reached="Provider:  codex"),
    Launcher(
        "companion-self-answer", ("example-product", "PRD"), forcible=True, reached="no project card at"
    ),
    Launcher("cold-read", ("product-uxd", "--project", "product-definition")),
    Launcher("launch-eval-fix", ("demo-skill",)),
    Launcher("launch-skill-evals", ("demo-skill",)),
    Launcher("product-card", ("product-planning",), card="product-planning"),
    Launcher(
        "seeds-from-idea",
        ("system/nemawashi/2026-10-01_an-idea.md",),
        files=("system/nemawashi/2026-10-01_an-idea.md",),
    ),
)
FORCIBLE = tuple(launcher for launcher in LAUNCHERS if launcher.forcible)
NOT_FORCIBLE = tuple(launcher for launcher in LAUNCHERS if not launcher.forcible)


def toml_without(name: str) -> str:
    """The delivered file with only `launchers.<name>` removed."""
    lines = _DELIVERED.splitlines(keepends=True)
    kept = [line for line in lines if not re.fullmatch(rf"{re.escape(name)} = \"[a-z]+\"\n", line)]
    assert len(kept) == len(lines) - 1, f"launchers.{name} is not one line of the delivered file"
    return "".join(kept)


def toml_with(name: str, value: str) -> str:
    """The delivered file with `launchers.<name>` naming `value`."""
    text = toml_without(name)
    return text.replace("[launchers]\n", f'[launchers]\n{name} = "{value}"\n', 1)


class Copy:
    """A launcher run from a copy of the host, with every stub recording to one log."""

    def __init__(self, root: Path, launcher: Launcher, toml: str | None) -> None:
        self.root = root
        self.launcher = launcher
        script = _CORE / "launchers" / launcher.name / "launcher.sh"
        self.script = isolated_host(root, script, tools=(*HOST_TOOLS, *_EXTRA_TOOLS))
        self.tools = root / "core" / "tools"
        self.cwd = root / "instance"
        self.cwd.mkdir()
        self.providers_toml = self.cwd / ".providers.toml"
        self.set_toml(toml)
        self.calls_log = root / "stub_calls.log"
        bin_dir = root / "bin"
        bin_dir.mkdir()
        for stub in ("claude", "codex", "agy", "caffeinate"):
            (bin_dir / stub).write_text(_STUB)
            (bin_dir / stub).chmod(0o755)
        for watcher in _RECORDING_STUBS:
            (self.tools / watcher).write_text(_WATCHER_STUB)
        for relative in launcher.files:
            placed = self.cwd / relative
            placed.parent.mkdir(parents=True, exist_ok=True)
            placed.write_text("# an idea\n")
        if launcher.card:
            project_dir = self.cwd / "system" / "projects" / launcher.card
            project_dir.mkdir(parents=True)
            (project_dir / "project.md").write_text(
                f"# {launcher.card}\n\n**Product path:** products/thing\n"
            )
        self.env = dict(os.environ)
        self.env.pop("KENSAIAPP_AGENT_PROVIDER", None)
        self.env.pop("KENSAIAPP_NOTIFIER", None)
        self.env.update(
            PATH=f"{bin_dir}{os.pathsep}{self.env['PATH']}",
            HOME=str(root / "home"),
            STUB_CALLS_LOG=str(self.calls_log),
            INSTRUMENT_RUN_ENDPOINT_FILE=str(root / "no-endpoint"),
            LAUNCH_SKILL_SKILLS_ROOT=str(root),
            LAUNCH_COMPANION_SELF_ANSWER_SKILLS_ROOT=str(root),
        )
        (root / "home").mkdir()

    def set_toml(self, toml: str | None) -> None:
        """Replace the instance's provider file with `toml`, or remove it."""
        if toml is None:
            self.providers_toml.unlink(missing_ok=True)
        else:
            self.providers_toml.write_text(toml, encoding="utf-8")

    def run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(self.script), *(args or self.launcher.args)],
            cwd=str(self.cwd), capture_output=True, text=True, env=self.env, check=False,
        )

    def calls(self) -> list[str]:
        """Every stub call recorded so far — an agent started or a watcher spawned."""
        return self.calls_log.read_text().splitlines() if self.calls_log.exists() else []


@pytest.fixture
def make_copy(tmp_path):
    """`make_copy(name_or_launcher, toml)` — a fresh copy of one launcher's host."""
    count = iter(range(1000))

    def _make(launcher: Launcher, toml: str | None = _DELIVERED) -> Copy:
        root = tmp_path / f"host{next(count)}"
        root.mkdir()
        return Copy(root, launcher, toml)

    return _make


def _ids(launchers):
    return [launcher.name for launcher in launchers]


def _assert_refused_before_anything_started(copy: Copy, result, *needles: str) -> None:
    assert result.returncode != 0, result.stdout
    for needle in needles:
        assert needle in result.stderr, result.stderr
    assert copy.calls() == [], "an agent or a watcher started despite the refusal"


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_a_missing_entry_refuses_by_dotted_key_before_anything_runs(make_copy, launcher):
    copy = make_copy(launcher, toml_without(launcher.name))

    result = copy.run()

    _assert_refused_before_anything_started(copy, result, f"launchers.{launcher.name}")


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_a_missing_entry_refuses_a_dry_run_too(make_copy, launcher):
    copy = make_copy(launcher, toml_without(launcher.name))

    result = copy.run(*launcher.args, "--dry-run")

    _assert_refused_before_anything_started(copy, result, f"launchers.{launcher.name}")
    assert "DRY RUN" not in result.stdout


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_an_unknown_value_is_refused_naming_entry_and_value(make_copy, launcher):
    copy = make_copy(launcher, toml_with(launcher.name, "grok"))

    result = copy.run()

    _assert_refused_before_anything_started(copy, result, f"launchers.{launcher.name}", "grok")


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_a_missing_file_refuses_naming_its_path(make_copy, launcher):
    copy = make_copy(launcher, None)

    result = copy.run()

    _assert_refused_before_anything_started(
        copy, result, str(copy.providers_toml), "cp .providers.toml.example .providers.toml")


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
@pytest.mark.parametrize("contents", [b"[launchers\n", b"\xff", None],
                         ids=["malformed-toml", "non-utf8", "directory"])
def test_an_unreadable_file_refuses_identically_in_real_and_dry_runs(
    make_copy, launcher, contents
):
    """CP-302/303: the real disk boundary refuses by path, before a run or watcher starts."""
    copy = make_copy(launcher, None)
    if contents is None:
        copy.providers_toml.mkdir()
    else:
        copy.providers_toml.write_bytes(contents)

    actual = copy.run()
    dry_run = copy.run(*launcher.args, "--dry-run")

    for result in (actual, dry_run):
        _assert_refused_before_anything_started(copy, result, str(copy.providers_toml))
        assert "Traceback" not in result.stderr
        assert "DRY RUN" not in result.stdout
    assert (dry_run.returncode, dry_run.stderr) == (actual.returncode, actual.stderr)


@pytest.mark.parametrize("launcher", FORCIBLE, ids=_ids(FORCIBLE))
def test_a_forced_launch_on_a_copy_without_the_entry_is_not_refused(make_copy, launcher):
    """Forced, the file is not read: the launch goes past the provider decision and nothing in
    its output is about the provider file. (That the forced launch then goes to `codex` is each
    launcher's own suite's, on a copy lacking the entry — what the rest of a launch does with no
    skill or project placed is not this builder's.)"""
    for toml in (toml_without(launcher.name), None):
        copy = make_copy(launcher, toml)

        result = copy.run(*launcher.args, "--provider", "codex", "--dry-run")

        assert launcher.reached in result.stdout + result.stderr, result.stderr
        assert ".providers.toml" not in result.stderr, result.stderr
        assert f"launchers.{launcher.name}" not in result.stderr, result.stderr


@pytest.mark.parametrize("launcher", NOT_FORCIBLE, ids=_ids(NOT_FORCIBLE))
def test_a_codex_entry_is_refused_naming_entry_and_value(make_copy, launcher):
    """A launcher that can only run Claude refuses an entry naming another provider, before any
    agent or watcher starts."""
    copy = make_copy(launcher, toml_with(launcher.name, "codex"))

    result = copy.run()

    _assert_refused_before_anything_started(copy, result, f"launchers.{launcher.name}", "codex")


@pytest.mark.parametrize("launcher", NOT_FORCIBLE, ids=_ids(NOT_FORCIBLE))
def test_the_variable_is_no_force(make_copy, launcher):
    """`KENSAIAPP_AGENT_PROVIDER` is ignored: it neither rescues a copy lacking the entry nor
    makes a launch with the entry present refuse on the provider."""
    missing = make_copy(launcher, toml_without(launcher.name))
    missing.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    present = make_copy(launcher)
    present.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    refused = missing.run()
    carried_on = present.run()

    _assert_refused_before_anything_started(missing, refused, f"launchers.{launcher.name}")
    assert f"launchers.{launcher.name}" not in carried_on.stderr, carried_on.stderr


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_the_launcher_reads_the_instance_file(make_copy, launcher):
    """CP-483: an entry naming `codex` in the instance's file is the provider the launcher takes.
    A launcher that can run it goes past the provider decision, and one that cannot refuses
    naming the value the instance's file gave it."""
    copy = make_copy(launcher, toml_with(launcher.name, "codex"))

    result = copy.run(*launcher.args, "--dry-run")

    if launcher.forcible:
        assert launcher.reached in result.stdout + result.stderr, result.stderr
        assert f"launchers.{launcher.name}" not in result.stderr, result.stderr
    else:
        _assert_refused_before_anything_started(copy, result, f"launchers.{launcher.name}", "codex")


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_a_relative_instance_root_reads_that_instance(make_copy, launcher):
    """CP-483: `--instance-root` given relative to the caller's directory — which the launcher
    then leaves — still reads that instance's file."""
    copy = make_copy(launcher, toml_with(launcher.name, "codex") if launcher.forcible
                     else _DELIVERED)

    result = subprocess.run(
        [str(copy.script), "--instance-root", copy.cwd.name, *launcher.args, "--dry-run"],
        cwd=str(copy.root), capture_output=True, text=True, env=copy.env, check=False)

    assert "is missing or cannot be read" not in result.stderr, result.stderr
    assert f"launchers.{launcher.name}" not in result.stderr, result.stderr
    if launcher.forcible:
        assert launcher.reached in result.stdout + result.stderr, result.stderr


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_the_host_file_is_never_read(make_copy, launcher):
    """CP-483: a `.providers.toml` at the host root, and none in the instance: refused, naming the
    instance's path — the host's file is not read in its place."""
    copy = make_copy(launcher, None)
    (copy.root / ".providers.toml").write_text(_DELIVERED, encoding="utf-8")

    result = copy.run()

    _assert_refused_before_anything_started(copy, result, str(copy.providers_toml))


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=_ids(LAUNCHERS))
def test_a_launcher_in_a_pin_reads_the_live_instance_file(make_copy, launcher):
    """CP-484: the host copy is a pin (`isolated_host` writes its `pin.json`). The instance's
    file names `claude` for one launch, and the same file edited between launches is what the
    second launch reads: a launcher that can run `codex` goes on, and a Claude-only one is refused,
    naming the entry."""
    copy = make_copy(launcher, toml_with(launcher.name, "claude"))
    first = copy.run(*launcher.args, "--dry-run")
    assert f"launchers.{launcher.name}" not in first.stderr, first.stderr

    copy.set_toml(toml_with(launcher.name, "codex"))
    second = copy.run(*launcher.args, "--dry-run")

    if launcher.forcible:
        assert launcher.reached in second.stdout + second.stderr, second.stderr
        assert f"launchers.{launcher.name}" not in second.stderr, second.stderr
        copy.set_toml(toml_with(launcher.name, "grok"))
        _assert_refused_before_anything_started(
            copy, copy.run(*launcher.args, "--dry-run"), f"launchers.{launcher.name}", "grok")
    else:
        _assert_refused_before_anything_started(copy, second, f"launchers.{launcher.name}",
                                                "codex")


# --- the whole set --------------------------------------------------------------------------------
# What holds across all seven launchers at once, and so cannot be said before the last of them has
# changed. The per-launcher cases above are each launcher's own proof; these are the set's.

_SEVEN = (
    "skill",
    "companion-self-answer",
    "cold-read",
    "launch-eval-fix",
    "launch-skill-evals",
    "product-card",
    "seeds-from-idea",
)
# A launcher that names `claude` as the provider it launches under — a literal after
# `--provider` or `provider=`, or a `:-claude}` default.
_CLAUDE_AS_A_LITERAL = re.compile(r"(--provider |provider=)claude([^|a-z]|$)|:-claude\}")


def _source_files(root: Path, suffixes: tuple[str, ...]):
    """Every non-test source file under `root` with one of `suffixes`: a path holding `test_` is
    test support, as are `conftest.py` and any bytecode folder."""
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(_CORE).as_posix()
        if path.suffix not in suffixes or not path.is_file():
            continue
        if "test_" in relative or path.name == "conftest.py" or "__pycache__" in path.parts:
            continue
        yield path


# The three kaizen tool scripts are launchers of the same reader, keyed by their name without
# `.sh`; their own suites (`core/tools/test_launch_*.py`) prove their launches.
_TEN = (*_SEVEN, "launch-apply-packet", "launch-audit", "launch-fix-author")


@pytest.mark.parametrize("name", _TEN)
def test_each_of_the_ten_entries_resolves_to_claude(name, tmp_path):
    """CP-488: the delivered template names `claude` for all ten, read from an instance root
    holding a copy of it."""
    (tmp_path / ".providers.toml").write_text(_DELIVERED, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CORE / "tools" / "providers.py"), "launcher", name,
         "--instance-root", str(tmp_path)],
        capture_output=True, text=True, check=False,
    )

    assert (result.returncode, result.stdout) == (0, "claude\n"), result.stderr


def test_the_proof_covers_the_seven_launchers_the_set_names():
    assert {launcher.name for launcher in LAUNCHERS} == set(_SEVEN)


def test_no_launcher_names_claude_as_a_default_or_a_literal():
    scanned = list(_source_files(_CORE / "launchers", (".sh", ".py")))
    hits = [
        f"{path.relative_to(_CORE)}:{number}: {line}"
        for path in scanned
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _CLAUDE_AS_A_LITERAL.search(line)
    ]

    assert hits == []
    scanned_names = {path.parent.name for path in scanned if path.name == "launcher.sh"}
    assert set(_SEVEN) <= scanned_names, "the scan did not reach every launcher it is about"


# A string that is the file's name or a path ending in it — what code opens — and not a sentence
# that mentions it, such as a help text.
_A_PATH_TO_THE_FILE = re.compile(r"[\w./-]*providers\.toml")


def _names_the_provider_file_in_code(path: Path) -> bool:
    """Whether `path` holds code that opens or parses `providers.toml`: a parser import, or a
    path to the file in a string that is not a docstring (Python), or the file's name on a line
    that is not a comment (shell)."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".sh":
        return any(
            "providers.toml" in line
            for line in text.splitlines()
            if not line.lstrip().startswith("#")
        )
    tree = ast.parse(text)
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] in {"tomllib", "tomli", "toml"}
                                                for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in {
            "tomllib", "tomli", "toml"
        }:
            return True
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in docstrings and _A_PATH_TO_THE_FILE.fullmatch(node.value)):
            return True
    return False


def test_only_the_reader_opens_the_provider_file():
    sources = list(_source_files(_CORE, (".py", ".sh")))
    holders = sorted(
        path.relative_to(_CORE).as_posix()
        for path in sources
        if _names_the_provider_file_in_code(path)
    )

    assert holders == ["tools/providers.py"]
    assert _CORE / "tools" / "providers.py" in sources, "the scan did not reach the reader"


# --- the five chain launchers' usage text ---------------------------------------------------------
# Five launchers carry a `--provider` entry in their usage block. After the provider file became the
# one place a launch's provider comes from, an unforced launch whose entry is missing is refused by
# name — the entry says so, and says where the provider comes from.

_USAGE_LAUNCHERS = ("build-idea", "chain-agari", "chain-change", "chain-development",
                    "chain-product")
# The first is written as two literals so that CP-311's own `git grep` over `core/launchers`, which
# reads test files too, finds the phrase nowhere.
_FALSE_CLAUSES = (
    "names none " "runs on claude",
    "runs on claude",
    "the engine's step table names",
    "the engine's registry names",
)
_PROVIDER_FILE = ".providers.toml"
_CORE_PROVIDER_FILE = "core/tools/providers.toml"


def _provider_usage_entry(name: str) -> str:
    """The `--provider` entry of `name`'s usage block, its comment markers and line breaks gone:
    the entry's own line and the continuation lines indented under it."""
    lines = (_CORE / "launchers" / name / "launcher.sh").read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines)
                 if re.match(r"#\s+--provider\s", line))
    entry = [lines[start]]
    for line in lines[start + 1:]:
        if not re.match(r"#\s{10,}\S", line):
            break
        entry.append(line)
    return " ".join(" ".join(part.lstrip("#").split()) for part in entry)


@pytest.mark.parametrize("name", _USAGE_LAUNCHERS)
def test_usage_provider_entry_states_the_file_and_the_refusal(name):
    entry = _provider_usage_entry(name)

    assert _PROVIDER_FILE in entry
    assert "is refused" in entry and "naming" in entry


@pytest.mark.parametrize("name", _USAGE_LAUNCHERS)
def test_usage_provider_entry_does_not_name_the_core_file(name):
    assert _CORE_PROVIDER_FILE not in _provider_usage_entry(name)


def test_no_live_launcher_line_names_the_core_file():
    """CP-491: no launcher line, header comments included, names the file the core no longer
    carries. A `# Version:` line is history and stays as it was."""
    scripts = sorted([*(_CORE / "launchers").glob("*/launcher.sh"),
                      *(_CORE / "tools").glob("launch-*.sh")])

    naming = [f"{path}:{number}"
              for path in scripts
              for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
              if _CORE_PROVIDER_FILE in line and not line.startswith("# Version:")]

    assert scripts and naming == []


@pytest.mark.parametrize("name", _USAGE_LAUNCHERS)
def test_usage_provider_entry_carries_no_false_clause(name):
    entry = _provider_usage_entry(name)

    assert [clause for clause in _FALSE_CLAUSES if clause in entry] == []


def test_build_idea_usage_does_not_say_a_chain_row_lacks_an_entry():
    """A row that starts a chain has no entry of its own: the `[build-idea]` table's comment says
    it is handed the queue's force alone, so the entry must not call it refused for lacking one."""
    sentences = _provider_usage_entry("build-idea").split(". ")

    [about_a_chain_row] = [sentence for sentence in sentences
                           if "starts a chain" in sentence]
    assert "force alone" in about_a_chain_row
    assert "refus" not in about_a_chain_row


def test_no_launcher_says_a_step_that_names_none_runs_on_claude():
    """CP-311's grep over `core/launchers`, kept as a test: it reaches every launcher, where the
    entry tests above reach the four that carried the claim."""
    carrying = sorted(
        path.parent.name
        for path in (_CORE / "launchers").glob("*/launcher.sh")
        if _FALSE_CLAUSES[0] in path.read_text(encoding="utf-8")
    )

    assert carrying == []
