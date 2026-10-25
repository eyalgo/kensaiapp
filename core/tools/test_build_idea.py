"""The `build-idea` engine's suite — driven through the ports it is given, never around them.

WHY THIS FILE LOOKS LIKE THIS
    `build_idea.py` runs a refine report's `## Next moves` as a queue: each row starts when the rows
    it names have LANDED, and landed is read off the disk, never off the run that was launched. So
    every test here scripts a disk (an in-memory tree), a seedbed and a process port, and asserts
    what the engine read off them or the exact ordered `argv` the process port received. Nothing
    here monkeypatches the module under test; `core/tools/test_chain.py` states why that is the
    only honest shape.

    Nothing here names a real product or project: `proj`, `a-seed` and `a-station` are the fixtures
    (`core/tools/test_check_vendor_neutrality.py` is the gate).
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

import build_idea as bi
import chain
import chain_development as cd
import completion_shim
import gate_suite as gs
import product_checkout
import providers
import walk_stop
from test_chain_development import FakeCheckout, FakeProcessTable
from test_providers import (COPY_COMMAND, DELIVERED_TEXT, ProviderText, edited_text,
                            provider_files)


# --- the fakes: one per port the engine is given ------------------------------------------


class FakeFiles:
    """An in-memory tree. `files` maps an absolute path to its text; a directory exists when
    something lives under it. `links` maps a path prefix to the real place it points at, so
    `real_path` answers what the disk would."""

    def __init__(self, files: dict[str, str] | None = None, links: dict[str, str] | None = None):
        self.files = {os.path.normpath(path): text for path, text in (files or {}).items()}
        self.links = dict(links or {})
        self.executable: set[str] = set()

    def is_file(self, path: str) -> bool:
        return os.path.normpath(path) in self.files

    def is_dir(self, path: str) -> bool:
        prefix = os.path.normpath(path).rstrip("/") + "/"
        return any(key.startswith(prefix) for key in self.files)

    def list_dir(self, path: str) -> list[str]:
        prefix = os.path.normpath(path).rstrip("/") + "/"
        return sorted({key[len(prefix):].split("/", 1)[0]
                       for key in self.files if key.startswith(prefix)})

    def read_text(self, path: str) -> str | None:
        return self.files.get(os.path.normpath(path))

    def write_text(self, path: str, text: str) -> None:
        self.files[os.path.normpath(path)] = text

    def make_dirs(self, path: str) -> None:
        pass

    def make_executable(self, path: str) -> None:
        self.executable.add(os.path.normpath(path))

    def replace(self, source: str, destination: str) -> None:
        self.files[os.path.normpath(destination)] = self.files.pop(os.path.normpath(source))

    def real_path(self, path: str) -> str:
        normal = os.path.normpath(path)
        for prefix, target in self.links.items():
            if normal == prefix or normal.startswith(prefix + "/"):
                return os.path.normpath(target + normal[len(prefix):])
        return normal


# --- the world -------------------------------------------------------------------------------

INSTANCE = "/instance"
INSTANCE_PROVIDER_FILE = providers.instance_file(INSTANCE)
CORE = "/core"
PROJECT = "proj"

CARD = f"{INSTANCE}/system/projects/{PROJECT}/project.md"
FULL_CARD = "# Project Context — proj\n\n**Definition:** full   <!-- a comment -->\n"


def card_defining(value: str) -> str:
    """A project card whose one `**Definition:**` line reads `value`."""
    return f"# Project Context — proj\n\n**Definition:** {value}\n"


SIX_COLUMNS = "| # | Move | Whose | Command | After | From |"
_PROMPT = (Path(__file__).resolve().parents[2] / "skills" / "pm" / ".claude" / "skills"
           / "shukuba-refine" / "prompts" / "rich.md")
_NEMAWASHI_PROMPT = (Path(__file__).resolve().parents[2] / "skills" / "principal-pm" / ".claude"
                     / "skills" / "nemawashi-refine" / "prompts" / "rich.md")
_PROMPTS = (_PROMPT, _NEMAWASHI_PROMPT)

SWEEP = "sweep the product's companions"
CLOSE = "close the reached station"
RETIRE = "retire a seed"
DROP = "drop a seed"
CUT_SEED = "cut a seed"
ACROSS = "route across projects"
PICK = "pick a seed"
CUT_ROUTE = "cut the route"
README_STATUS = "readme-status"
CHANGE = "walk the next change"
OWNER = "the owner's act"
FULL = bi.Definition.FULL
PRD_AGARI = bi.Definition.PRD_AGARI

DISPOSITIONS = {
    SWEEP: bi.Disposition.RUN_CHAIN,
    CLOSE: bi.Disposition.RUN_SKILL,
    README_STATUS: bi.Disposition.RUN_SKILL,
    PICK: bi.Disposition.RUN_SKILL,
    CUT_ROUTE: bi.Disposition.RUN_SKILL,
    CHANGE: bi.Disposition.HAND_OFF,
    OWNER: bi.Disposition.OWNER,
    RETIRE: bi.Disposition.RUN_SKILL,
    "refine a seed": bi.Disposition.RUN_SKILL,
    "cut from the product's documents": bi.Disposition.RUN_SKILL,
    "re-run a halted cut": bi.Disposition.OWNER,
    DROP: bi.Disposition.SKIP,
    CUT_SEED: bi.Disposition.SKIP,
    ACROSS: bi.Disposition.SKIP,
}


def command_for(kind: str, core: str = CORE, project: str = PROJECT,
                definition: bi.Definition = bi.Definition.FULL) -> str:
    """The Command cell a report carries for a runnable kind: the code-spanned argv. The sweep's
    is the chain the card's `definition` names; every other kind ignores it."""
    argv = bi.expected_argv(kind, core_dir=core, project=project, definition=definition)
    return "`" + shlex.join(argv) + "`"


def next_moves(*rows: str, header: str = SIX_COLUMNS) -> str:
    """A report carrying one `## Next moves` table. Each row is the text between the pipes."""
    columns = header.count("|") - 1
    separator = "|" + "---|" * columns
    body = "\n".join(f"| {row} |" for row in rows)
    return f"# a report\n\n## Next moves\n\n{header}\n{separator}\n{body}\n\n## Read\n\nx\n"


def row(number: int, move: str, command: str | None = None, after: str = "—",
        whose: str = "owner", source: str = "Moves row 1") -> str:
    if command is None:
        command = command_for(move) if DISPOSITIONS[move] in (
            bi.Disposition.RUN_SKILL, bi.Disposition.RUN_CHAIN,
            bi.Disposition.HAND_OFF) else f"none — {move}"
    return f"{number} | {move} | {whose} | {command} | {after} | {source}"


def validated(text: str, *, core: str = CORE, instance_root: str = INSTANCE,
              card: str | None = FULL_CARD) -> list[bi.Row]:
    rows = bi.parse_queue(text)
    refused = bi.validate(rows, core_dir=core, instance_root=instance_root, project=PROJECT,
                          card=card)
    assert refused == {}, refused
    return rows


def refusals(text: str, *, core: str = CORE, instance_root: str = INSTANCE,
             card: str | None = FULL_CARD) -> dict[int, str]:
    """The rows `validate` refuses on their own, each with why."""
    return bi.validate(bi.parse_queue(text), core_dir=core, instance_root=instance_root,
                       project=PROJECT, card=card)


def _pin_of(tmp_path: Path, host: Path) -> Path:
    """A real `pin.json` naming `host` as the pin's source host root — enough for
    `pin.same_launcher`'s own `of_core` to recognize the pin (a real-filesystem check; it takes
    no `Files` port). Nothing under either tree needs to exist beyond the manifest itself."""
    pin_root = tmp_path / "pin"
    pin_root.mkdir()
    (pin_root / "pin.json").write_text(json.dumps(
        {"id": "test-pin", "source_host_root": str(host), "created": "2026-09-22T00:00:00Z"}))
    return pin_root / "core"


# --- the kind table ---------------------------------------------------------------------------


def _prompt_kind_table(prompt=_PROMPT) -> list[list[str]]:
    """The rows of the prompt's kind table — the one whose header is `Move | Owed when`."""
    lines = prompt.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith("| Move | Owed when |"))
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def test_every_prompt_kind_is_in_the_table_with_its_disposition():
    """The table is a literal, and the prompt is where a new kind would first be written — so the
    keys are read off the real prompt file, and a tenth kind there fails here."""
    prompt_kinds = [cells[0] for cells in _prompt_kind_table()]

    nema_kinds = {cells[0] for cells in _prompt_kind_table(_NEMAWASHI_PROMPT)}
    assert set(bi.KINDS) == set(prompt_kinds) | nema_kinds | {"refine a seed"}
    assert {kind: bi.KINDS[kind].disposition for kind in bi.KINDS} == DISPOSITIONS


def _filled(command: str) -> str:
    return (command.replace("<CORE>", CORE).replace("<project>", PROJECT)
            .replace("<station>", STEM))


def test_a_runnable_kinds_argv_is_the_command_the_prompt_writes():
    """`expected_argv` is checked against each prompt's own Command column, `<CORE>` and
    `<project>` filled in, so the table cannot drift from what the PM is told to write. The
    sweep's cell names one command for each definition that has a sweep, each as its own code
    span, and the set of them is the set `expected_argv` gives."""
    sweeps_checked = 0
    for prompt in _PROMPTS:
        for cells in _prompt_kind_table(prompt):
            kind, command = cells[0], cells[3]
            if bi.KINDS[kind].disposition in (bi.Disposition.SKIP, bi.Disposition.OWNER):
                continue
            if kind == SWEEP:
                written = {tuple(shlex.split(_filled(span)))
                           for span in re.findall(r"`([^`]+)`", command)}
                assert written == {
                    tuple(bi.expected_argv(SWEEP, core_dir=CORE, project=PROJECT,
                                           definition=definition))
                    for definition in (FULL, PRD_AGARI)}, prompt.name
                sweeps_checked += 1
                continue
            station = STEM if "<station>" in command else ""
            assert bi.expected_argv(kind, core_dir=CORE, project=PROJECT,
                                    station=station) == shlex.split(
                _filled(command.strip("`"))), kind
            assert ("<station>" in command) == (bi._STATION in bi.KINDS[kind].arguments), kind
    assert sweeps_checked == len(_PROMPTS)


def test_both_prompts_say_no_sweep_row_for_a_none_card():
    for prompt in _PROMPTS:
        cells = next(cells for cells in _prompt_kind_table(prompt) if cells[0] == SWEEP)
        owed_when, command = cells[1], cells[3]

        assert "no sweep row" in command and "none" in command, prompt.name
        assert "not none" in owed_when, prompt.name


def test_each_runnable_kind_names_what_it_lands_and_the_seat_that_runs_it():
    assert bi.KINDS[CLOSE].landed is bi.Landed.STATION_CLOSED
    assert bi.KINDS[PICK].landed is bi.Landed.SEED_PICKED
    assert bi.KINDS[CUT_ROUTE].landed is bi.Landed.ROUTE_CUT
    assert bi.KINDS[SWEEP].landed is bi.Landed.WALK_ENDED
    assert (bi.KINDS[CLOSE].role, bi.KINDS[PICK].role, bi.KINDS[CUT_ROUTE].role,
            bi.KINDS[RETIRE].role) == ("scrum-master", "pm", "pm", "scrum-master")


def test_an_owners_act_row_is_a_kind_the_queue_accepts():
    """The row's Command is prose for the owner: it is not refused as an unknown kind and it is
    compared with nothing."""
    text = next_moves(row(1, OWNER, command="none — walk it yourself"))

    rows = validated(text)

    assert [(r.number, r.move, r.command) for r in rows] == [
        (1, OWNER, "none — walk it yourself")]


def test_an_owners_act_row_has_no_argv():
    with pytest.raises(ValueError, match="runs nothing"):
        bi.expected_argv(OWNER, core_dir=CORE, project=PROJECT)


# --- parsing the table ------------------------------------------------------------------------


def test_a_six_column_table_parses_to_rows_with_after_tuples():
    text = next_moves(row(1, SWEEP), row(2, CLOSE, after="1"), row(3, PICK, after="1, 2"))

    rows = bi.parse_queue(text)

    assert [(r.number, r.move, r.after) for r in rows] == [
        (1, SWEEP, ()), (2, CLOSE, (1,)), (3, PICK, (1, 2))]
    assert rows[0].whose == "owner" and rows[0].source == "Moves row 1"
    assert rows[0].command == command_for(SWEEP)


def test_a_five_column_table_is_refused_naming_the_after_column():
    text = next_moves(f"1 | {SWEEP} | owner | {command_for(SWEEP)} | Moves row 1",
                      header="| # | Move | Whose | Command | From |")

    with pytest.raises(bi.QueueRefused) as refused:
        bi.parse_queue(text)

    assert "After" in str(refused.value)
    assert SIX_COLUMNS in str(refused.value)


def test_a_table_missing_any_other_required_column_is_refused_naming_it():
    text = next_moves(f"1 | {SWEEP} | {command_for(SWEEP)} | — | Moves row 1",
                      header="| # | Move | Command | After | From |")

    with pytest.raises(bi.QueueRefused, match="Whose"):
        bi.parse_queue(text)


def test_the_columns_are_found_by_header_not_by_position():
    text = next_moves(f"{command_for(CLOSE)} | 1 | {CLOSE} | Moves row 1 | scrum master | —",
                      header="| Command | # | Move | From | Whose | After |")

    (parsed,) = bi.parse_queue(text)

    assert (parsed.number, parsed.move, parsed.after) == (1, CLOSE, ())
    assert parsed.command == command_for(CLOSE)


def test_a_none_section_is_an_empty_queue():
    text = "# a report\n\n## Next moves\n\nNone — the route holds still.\n\n## Read\n\nx\n"

    assert bi.parse_queue(text) == []


def test_a_report_with_no_next_moves_section_is_refused():
    with pytest.raises(bi.QueueRefused, match="Next moves"):
        bi.parse_queue("# a report\n\n## Read\n\nx\n")


# --- validating it ----------------------------------------------------------------------------


def test_an_unknown_kind_is_refused_naming_the_row():
    text = next_moves(row(1, SWEEP), f"2 | reticulate the splines | owner | none | — | x")

    with pytest.raises(bi.QueueRefused) as refused:
        validated(text)

    assert "row 2" in str(refused.value) and "reticulate the splines" in str(refused.value)


@pytest.mark.parametrize("after", ["after 1", "1 lands", "one", "1,,2", "-", "1 2", ""])
def test_a_malformed_after_is_refused(after):
    text = next_moves(row(1, SWEEP), row(2, CLOSE, after=after))

    with pytest.raises(bi.QueueRefused) as refused:
        validated(text)

    assert "row 2" in str(refused.value) and after in str(refused.value)


def test_an_after_naming_a_missing_row_is_refused():
    text = next_moves(row(1, SWEEP), row(2, CLOSE, after="7"))

    with pytest.raises(bi.QueueRefused) as refused:
        validated(text)

    assert "row 2" in str(refused.value) and "7" in str(refused.value)


@pytest.mark.parametrize("after", ["2", "3"], ids=["itself", "a-later-row"])
def test_an_after_naming_itself_or_a_later_row_is_refused(after):
    """Only earlier rows can be waited on, which is what keeps the table from holding a cycle."""
    text = next_moves(row(1, SWEEP), row(2, CLOSE, after=after), row(3, PICK, after="2"))

    with pytest.raises(bi.QueueRefused) as refused:
        validated(text)

    assert "row 2" in str(refused.value)


def test_a_duplicate_or_non_integer_row_number_is_refused():
    duplicated = next_moves(row(1, SWEEP), row(1, CLOSE))
    lettered = next_moves(row(1, SWEEP), f"b | {CLOSE} | owner | {command_for(CLOSE)} | — | x")

    for text in (duplicated, lettered):
        with pytest.raises(bi.QueueRefused):
            validated(text)


@pytest.mark.parametrize("drifted", [
    "`/core/launchers/chain-change/launcher.sh proj`",
    "`/core/launchers/chain-product/launcher.sh another`",
    "`/core/launchers/chain-product/launcher.sh proj --dry-run`",
    "`/core/launchers/chain-product/launcher.sh`",
], ids=["wrong-launcher", "wrong-project", "extra-argument", "missing-argument"])
def test_a_runnable_rows_command_drift_is_refused_on_its_row(drifted):
    refused = refusals(next_moves(row(1, SWEEP, command=drifted)))

    assert list(refused) == [1] and "is not what" in refused[1]


def test_an_absolute_and_a_relative_core_path_both_match():
    """A real report carries the absolute `<CORE>`; a hand-written one may type the path from the
    instance root, which is where the launcher runs."""
    absolute = next_moves(row(1, CLOSE, command="`/instance/core/launchers/skill/launcher.sh "
                                                 "shukuba-retire proj`"))
    relative = next_moves(row(1, CLOSE, command="`core/launchers/skill/launcher.sh "
                                                 "shukuba-retire proj`"))

    for text in (absolute, relative):
        validated(text, core="/instance/core")


def test_a_command_through_a_symlink_to_core_matches(tmp_path):
    """`pin.same_launcher` resolves a real symlink the same way `os.path.realpath` did before it
    — a real filesystem check, never a `Files` port, so this one needs an actual symlink on
    disk rather than `FakeFiles`'s in-memory `links` map."""
    real_core = tmp_path / "core"
    real_core.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real_core)
    text = next_moves(row(1, SWEEP, command=f"`{link}/launchers/chain-product/launcher.sh proj`"))

    validated(text, core=str(real_core), instance_root=str(tmp_path))


def test_a_row_naming_the_live_launcher_validates_under_a_pinned_core(tmp_path):
    """A queue running under a pin (`core_dir` is the pin's own `core/`) still accepts a row
    whose Command cell names the live host's own launcher path — the shape a real report can
    carry unmodified across a launch that happens to pin."""
    host = tmp_path / "host"
    pin_core = _pin_of(tmp_path, host)
    live_command = command_for(SWEEP, core=str(host / "core"))
    text = next_moves(row(1, SWEEP, command=live_command))

    validated(text, core=str(pin_core), instance_root=str(host))


def test_a_row_naming_a_pruned_pins_launcher_validates_under_a_later_pin(tmp_path):
    """A satellite walk of 2026-10-13: its report, written under a pin since pruned, named that
    pin's launcher in every Command, and every row was refused before any ran."""
    host = tmp_path / "host"
    pin_core = _pin_of(tmp_path, host)
    pruned_core = tmp_path / "20261007T081759Z-q7vsml" / "core"
    text = next_moves(row(1, CLOSE, command=command_for(CLOSE, core=str(pruned_core))))

    validated(text, core=str(pin_core), instance_root=str(host))


def test_a_row_naming_a_relative_core_launchers_path_validates_under_a_pinned_core(tmp_path):
    host = tmp_path / "host"
    pin_core = _pin_of(tmp_path, host)
    relative_command = "`" + shlex.join(
        ["core/launchers/chain-product/launcher.sh", PROJECT]) + "`"
    text = next_moves(row(1, SWEEP, command=relative_command))

    validated(text, core=str(pin_core), instance_root=str(host))


def test_a_validated_row_runs_the_pins_launcher(tmp_path):
    """The row still runs `expected_argv`, which is always under `core_dir` — the pin's own,
    never the live host path the report happened to name."""
    host = tmp_path / "host"
    pin_core = _pin_of(tmp_path, host)
    live_command = command_for(SWEEP, core=str(host / "core"))
    queue = Queue(row(1, SWEEP, command=live_command))

    plan = queue.describe(core_dir=str(pin_core))

    assert plan.rows[0].argv[0] == str(pin_core / "launchers" / "chain-product" / "launcher.sh")


def test_a_row_naming_another_launcher_is_still_refused(tmp_path):
    """Pin-awareness widens which paths count as the *same* launcher; it does not widen which
    launcher a row may name."""
    host = tmp_path / "host"
    pin_core = _pin_of(tmp_path, host)
    unrelated = "`" + shlex.join(
        [str(tmp_path / "unrelated" / "launcher.sh"), PROJECT]) + "`"
    text = next_moves(row(1, SWEEP, command=unrelated))

    assert list(refusals(text, core=str(pin_core), instance_root=str(host))) == [1]


def test_the_command_cell_may_be_a_code_span():
    plain = command_for(SWEEP).strip("`")

    validated(next_moves(row(1, SWEEP, command=plain)))
    validated(next_moves(row(1, SWEEP, command=f"`{plain}`")))


def test_a_command_that_cannot_be_split_is_refused_never_executed():
    text = next_moves(row(1, SWEEP, command="`/core/launchers/chain-product/launcher.sh 'proj`"))

    refused = refusals(text)

    assert list(refused) == [1] and "cannot be read as a command" in refused[1]


def test_a_skip_rows_command_is_not_checked():
    text = next_moves(row(1, DROP, command="none — `nemawashi-drop`, in a `principal-pm:` session"),
                      row(2, CUT_SEED), row(3, ACROSS))

    assert [r.move for r in validated(text)] == [DROP, CUT_SEED, ACROSS]


def test_a_retire_rows_command_is_checked_like_any_runnable_row():
    """The retire used to be a person's move, and its Command prose; it runs now, so a report
    written with the retired `nemawashi-retire/launcher.sh <seed> --project` form is refused."""
    old = "`/core/launchers/nemawashi-retire/launcher.sh a-seed --project proj`"

    assert list(refusals(next_moves(row(1, RETIRE, command=old)))) == [1]
    assert refusals(next_moves(row(1, RETIRE))) == {}


def test_a_skip_rows_after_is_still_validated():
    text = next_moves(row(1, DROP, after="4"))

    with pytest.raises(bi.QueueRefused, match="row 1"):
        validated(text)


# --- the queue: the rest of the ports and a world to run it in ---------------------------------


class FakeProcesses:
    """Records every launch. `codes` scripts the exit status each successive call returns;
    `on_run` lets a test look at the world at the moment a launch happens."""

    def __init__(self, codes: list[int] | None = None, on_run=None):
        self.calls: list[dict] = []
        self.codes = list(codes or [])
        self.on_run = on_run

    def run(self, argv, *, cwd=None, env=None, capture=False, timeout=None) -> int:
        self.calls.append({"argv": list(argv), "cwd": cwd, "env": dict(env or {})})
        if self.on_run:
            self.on_run(list(argv))
        return self.codes.pop(0) if self.codes else 0

    @property
    def launched(self) -> list[list[str]]:
        return [call["argv"] for call in self.calls]


class FakeWatcher:
    """Records each watch the queue leaves behind. `starts` is what `start` answers, and
    `on_sleep(call_number)` lets a test change the world while the watcher waits."""

    def __init__(self, starts: bool = True, on_sleep=None, on_start=None):
        self.on_start = on_start
        self.starts = starts
        self.on_sleep = on_sleep
        self.started: list[dict] = []
        self.sleeps: list[float] = []

    def start(self, argv, log_path) -> bool:
        self.started.append({"argv": list(argv), "log": log_path})
        if self.on_start:
            self.on_start()
        return self.starts

    def sleep(self, seconds) -> None:
        self.sleeps.append(seconds)
        if self.on_sleep:
            self.on_sleep(len(self.sleeps))


class FakeNotifier:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


class FakeIdSource:
    def new_id(self) -> str:
        return "queue-1"


class FakeLock:
    """Records every hold, and whether one was open when something else happened."""

    def __init__(self):
        self.holds: list[str] = []
        self.held = False

    def hold(self, path: str):
        lock = self

        class _Held:
            def __enter__(self):
                lock.holds.append(path)
                lock.held = True

            def __exit__(self, *exc):
                lock.held = False
                return False

        return _Held()


class FakeLog:
    def __init__(self):
        self.lines: list[tuple[str, str]] = []

    def append(self, path: str, line: str) -> None:
        self.lines.append((path, line))


class FakeJourney:
    """The seedbed, as data: `seeds` is what sits at its root, `checklists` a seed's item count."""

    def __init__(self):
        self.seeds: list[str] = []
        self.checklists: dict[str, int] = {}

    def report_revision(self, path):
        return self.files.read_text(path)

    def root_seeds(self, nemawashi_dir: str) -> list[str]:
        return list(self.seeds)

    def checklist_items(self, seed_path: str) -> int:
        return self.checklists.get(seed_path, 0)


KEY = "2026-09-18_a-unit"
OTHER_KEY = "2026-09-10_an-older-unit"
SEED = "2026-09-01_a-seed"
STATION = "2026-09-18_a-station.md"
STEM = STATION.removesuffix(".md")
ENGINE = f"{CORE}/tools/build_idea.py"
LOGS = f"{INSTANCE}/system/logs"
STATE = f"{LOGS}/build-idea-{PROJECT}-state.json"
JOURNEY = f"{INSTANCE}/system/projects/{PROJECT}/journey"
NEMAWASHI = f"{JOURNEY}/nemawashi"
STATION_PATH = f"{JOURNEY}/shukuba/{STATION}"
CONTEXT_PM = f"{INSTANCE}/system/projects/{PROJECT}/contexts/CONTEXT_PM.md"
ROOT_SEED = f"{NEMAWASHI}/{SEED}.md"


def report_path(key: str = KEY) -> str:
    return f"{NEMAWASHI}/unpicked/{SEED}/{key}_report.md"


def shim_path(number: int) -> str:
    return f"{LOGS}/build-idea-{PROJECT}-row-{number}.sh"


def sealed_world(*rows: str, key: str = KEY, station: bool = True) -> dict[str, str]:
    """A project whose unit `key` is sealed and refined: the context, the trail folder, the
    report carrying `rows`, and the station still open at the shukuba root."""
    files = {
        CONTEXT_PM: f"# CONTEXT_PM\n\n**Status:** Sealed\n\n`{key}` — the unit.\n",
        f"{JOURNEY}/tobiishi/trail/{key}/change_request.md": "sealed",
        report_path(key): next_moves(*rows) if rows else next_moves(),
        CARD: FULL_CARD,
    }
    if station:
        files[STATION_PATH] = "a station"
    return files


class Queue:
    """One engine over one scripted disk. `engine()` builds a fresh one over the same ports each
    call, which is what the shim's detached process does."""

    def __init__(self, *rows: str, files: dict | None = None, codes=None, on_run=None,
                 environ: dict | None = None, notifier=None,
                 provider_port: ProviderText | None = None, checkout: FakeCheckout | None = None,
                 watcher: FakeWatcher | None = None, git=None):
        self.git = git
        self.files = FakeFiles(files if files is not None else sealed_world(*rows))
        # The provider file, apart from the engine's disk: the delivered text unless a test hands
        # in a copy, and replaceable between calls to script an edit made mid-queue.
        self.provider_port = provider_port or ProviderText()
        self.journey = FakeJourney()
        self.journey.files = self.files
        if any(f"| {RETIRE} |" in text for text in self.files.files.values()):
            self.journey.seeds = [ROOT_SEED]
            self.files.files[ROOT_SEED] = "# seed\n- [x] walked\n"
        self.processes = FakeProcesses(codes=codes, on_run=on_run)
        self.table = FakeProcessTable()
        self.notifier = notifier or FakeNotifier()
        self.lock = FakeLock()
        self.log = FakeLog()
        self.environ = {"PATH": "/usr/bin"} if environ is None else environ
        self.checkout = checkout or FakeCheckout()
        self.watcher = watcher or FakeWatcher()

    def engine(self) -> bi.BuildIdea:
        return bi.BuildIdea(
            store=bi.QueueStore(self.files, STATE),
            reader=cd.DiskReader(files=self.files, git=self.git),
            journey=self.journey, files=self.files, processes=self.processes,
            notifier=self.notifier, lock=self.lock, log=self.log, id_source=FakeIdSource(),
            environ=self.environ, engine_path=ENGINE,
            providers=provider_files(port=self.provider_port), process_table=self.table,
            checkout=self.checkout, watcher=self.watcher)

    def start(self, **kwargs):
        return self.engine().start(instance_root=INSTANCE, project=PROJECT, core_dir=CORE,
                                   shim_dir=LOGS, **kwargs)

    def advance(self, number: int, outcome: str = "completed"):
        return self.engine().advance(number, outcome)

    def describe(self, **kwargs):
        return self.engine().describe(INSTANCE, PROJECT, **kwargs)

    def wake(self, queue_id: str = "queue-1"):
        return self.engine().wake(queue_id)

    def wait_on_walk(self, queue_id: str = "queue-1"):
        return self.engine().wait_on_walk(queue_id)

    def stop(self, requested_at: str = "2026-09-18T10:00:00+00:00") -> str:
        return self.engine().stop(INSTANCE, PROJECT, requested_at)

    def edit_state(self, change) -> None:
        """Rewrite the saved state through `change(dict)` — a state a crash, or an older run,
        could have left, which no sequence of engine calls reaches on purpose."""
        state = json.loads(self.files.files[STATE])
        change(state)
        self.files.files[STATE] = json.dumps(state)

    @property
    def state(self) -> dict:
        return json.loads(self.files.files[STATE])

    def statuses(self) -> dict[int, str]:
        return {entry["number"]: entry["status"] for entry in self.state["rows"]}

    # the landed facts, each one a change to the disk a real run would have made
    def close_station(self) -> None:
        """What `shukuba-retire` leaves: the station moved whole into `trail/`."""
        self.files.files[f"{JOURNEY}/shukuba/trail/{STATION}"] = self.files.files.pop(STATION_PATH)

    def pick_seed(self) -> None:
        self.journey.seeds.append(ROOT_SEED)

    def cut_route(self, items: int = 3) -> None:
        self.journey.checklists[ROOT_SEED] = items


# --- describe ---------------------------------------------------------------------------------


def test_describe_resolves_the_sealed_unit_and_its_report():
    queue = Queue(row(1, SWEEP), row(2, CLOSE, after="1"), row(3, DROP))

    plan = queue.describe(core_dir=CORE)

    assert (plan.key, plan.report) == (KEY, report_path())
    assert [(r.number, r.move, r.disposition, r.after, r.argv) for r in plan.rows] == [
        (1, SWEEP, bi.Disposition.RUN_CHAIN, (),
         bi.expected_argv(SWEEP, core_dir=CORE, project=PROJECT, definition=FULL)),
        (2, CLOSE, bi.Disposition.RUN_SKILL, (1,), bi.expected_argv(CLOSE, core_dir=CORE,
                                                                    project=PROJECT,
                                                                    station=STEM)),
        (3, DROP, bi.Disposition.SKIP, (), None)]


def test_describe_derives_core_from_the_engine_when_it_is_not_given():
    """The launcher's dry run asks for a plan with no `--core-dir`; the engine sits at
    `<core>/tools/build_idea.py`, so `<core>` is the directory above its own."""
    queue = Queue(row(1, SWEEP))

    assert queue.describe().rows[0].argv[0] == f"{CORE}/launchers/chain-product/launcher.sh"


def test_describe_uses_a_given_key():
    files = {**sealed_world(row(1, SWEEP)), **sealed_world(row(1, CLOSE), key=OTHER_KEY)}
    queue = Queue(files=files)

    plan = queue.describe(key=OTHER_KEY)

    assert (plan.key, plan.report) == (OTHER_KEY, report_path(OTHER_KEY))
    assert [r.move for r in plan.rows] == [CLOSE]


def test_no_sealed_unit_or_no_report_is_refused_naming_the_path():
    no_context = Queue(files={STATION_PATH: "a station"})
    no_report = Queue(files={k: v for k, v in sealed_world(row(1, SWEEP)).items()
                             if not k.endswith("_report.md")})

    with pytest.raises(bi.QueueRefused) as first:
        no_context.describe()
    with pytest.raises(bi.QueueRefused) as second:
        no_report.describe()

    assert CONTEXT_PM in str(first.value)
    assert f"{KEY}_report.md" in str(second.value) and NEMAWASHI in str(second.value)


def test_describe_refuses_a_report_the_table_layer_refuses():
    queue = Queue(row(1, "reticulate the splines", command="none"))

    with pytest.raises(bi.QueueRefused, match="row 1"):
        queue.describe()


def test_describe_names_a_row_whose_command_is_not_its_kinds():
    queue = Queue(row(1, CLOSE, command="`/core/launchers/chain-change/launcher.sh proj`"))

    assert "is not what 'close the reached station' runs" in queue.describe().rows[0].refused


def test_describe_touches_nothing():
    queue = Queue(row(1, SWEEP), row(2, CLOSE, after="1"))
    before = dict(queue.files.files)

    queue.describe()

    assert queue.lock.holds == [] and queue.processes.calls == []
    assert queue.notifier.messages == [] and queue.log.lines == []
    assert queue.files.files == before


def test_describe_refuses_while_a_queue_is_in_flight():
    queue = Queue(row(1, SWEEP))
    queue.start()

    with pytest.raises(bi.QueueRefused, match=STATE):
        queue.describe()


# --- starting a queue -------------------------------------------------------------------------


def test_rows_free_at_the_start_run_one_at_a_time():
    queue = Queue(row(1, SWEEP), row(2, CLOSE))

    queue.start()

    assert [argv[0].rsplit("/", 2)[-2] for argv in queue.processes.launched] == ["chain-product"]
    assert queue.statuses() == {1: "launched", 2: "waiting"}
    assert sorted(queue.state["pending"]) == ["1"]

    queue.advance(1, "settled")

    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert sorted(queue.state["pending"]) == ["2"]


def test_two_rows_behind_one_close_never_run_together():
    """The shape that halted a queue on 2026-10-12: both rows are ready once the close lands."""
    queue = Queue(row(1, CLOSE), row(2, README_STATUS, after="1"), row(3, RETIRE, after="1"))
    queue.start()

    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "launched", 3: "waiting"}


def test_a_launch_that_fails_at_once_leaves_no_row_running():
    """CP-572: a row whose launcher exits non-zero is not running, so the next ready row starts in
    the same pass."""
    queue = Queue(row(1, CLOSE), row(2, SWEEP), codes=[3])

    queue.start()

    assert queue.statuses() == {1: "failed", 2: "launched"}
    assert queue.state["pending"].keys() == {"2"}


def test_the_start_records_the_unit_the_report_and_the_station_it_found():
    queue = Queue(row(1, CLOSE))

    queue.start()

    state = queue.state
    assert (state["key"], state["report"], state["station"]) == (KEY, report_path(), STATION)
    assert (state["project"], state["queue_id"], state["core_dir"]) == (PROJECT, "queue-1", CORE)
    assert queue.lock.holds == [STATE]


def test_a_row_waits_until_every_after_row_has_landed():
    """Fan-in: the second of two dependencies landing is what starts the third."""
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, PICK, after="1, 2"))
    queue.start()
    assert len(queue.processes.launched) == 1

    queue.close_station()
    queue.advance(1)
    assert queue.statuses()[3] == "waiting" and len(queue.processes.launched) == 2

    queue.advance(2, "settled")

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "launched"}
    assert queue.processes.launched[-1] == bi.expected_argv(PICK, core_dir=CORE, project=PROJECT)


def test_launched_is_not_landed():
    """A close whose run completed with its station still at the root did not close anything, so
    the pick behind it never starts."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()

    queue.advance(1)

    assert queue.statuses() == {1: "failed", 2: "blocked"}
    assert len(queue.processes.launched) == 1
    assert queue.state["ended"] == "halted"
    assert "1. close the reached station" in queue.state["ended_reason"]


@pytest.mark.parametrize("kind, outcome, make_true, expected", [
    (CLOSE, "completed", None, "failed"),
    (CLOSE, "completed", "close_station", "landed"),
    (CLOSE, "produced_nothing", "close_station", "landed"),
    (CLOSE, "timeout", "close_station", "failed"),
    (PICK, "completed", None, "failed"),
    (PICK, "completed", "pick_seed", "landed"),
    (CUT_ROUTE, "completed", "pick_seed", "failed"),
    (CUT_ROUTE, "completed", "cut_route", "landed"),
    (SWEEP, "settled", None, "landed"),
    (SWEEP, "left_for_the_owner", None, "landed"),
    (SWEEP, "machinery", None, "failed"),
    (SWEEP, "cap", None, "failed"),
])
def test_each_landed_fact_true_and_false(kind, outcome, make_true, expected):
    queue = Queue(row(1, kind))
    queue.start()
    if make_true == "cut_route":
        queue.pick_seed()
    if make_true:
        getattr(queue, make_true)()

    queue.advance(1, outcome)

    assert queue.statuses() == {1: expected}


def test_a_close_is_landed_when_there_was_no_station_at_start_and_none_is_there_now():
    queue = Queue(files=sealed_world(row(1, CLOSE), station=False))
    queue.start()

    queue.advance(1)

    assert queue.statuses() == {1: "landed"}


def test_a_failed_row_blocks_only_its_dependents_and_the_queue_ends_halted():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, PICK, after="1"))
    queue.start()

    queue.advance(1)
    assert queue.statuses() == {1: "failed", 2: "launched", 3: "blocked"}
    assert queue.state["ended"] is None

    queue.advance(2, "settled")

    assert queue.statuses() == {1: "failed", 2: "landed", 3: "blocked"}
    assert queue.state["ended"] == "halted"
    assert "3. pick a seed" in queue.notifier.messages[-1]


def test_a_launcher_exiting_non_zero_fails_its_row():
    queue = Queue(row(1, CLOSE), codes=[3])

    queue.start()

    assert queue.statuses() == {1: "failed"}
    assert queue.state["pending"] == {}
    assert queue.state["ended"] == "halted"
    assert "exited 3" in queue.state["ended_reason"]


def test_a_launcher_that_cannot_start_fails_its_row_like_any_other_exit():
    queue = Queue(row(1, CLOSE), codes=[-1])

    queue.start()

    assert queue.statuses() == {1: "failed"} and queue.state["ended"] == "halted"


def test_a_row_dependent_on_a_row_that_failed_at_launch_is_blocked_not_left_waiting():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"), codes=[3])

    queue.start()

    assert queue.statuses() == {1: "failed", 2: "blocked"}
    assert queue.state["ended"] == "halted"


def test_a_skip_row_is_named_and_blocks_nothing_independent():
    queue = Queue(row(1, DROP), row(2, CLOSE))
    queue.start()
    assert queue.statuses() == {1: "skipped", 2: "launched"}

    queue.close_station()
    queue.advance(2)

    assert queue.state["ended"] == "done"
    assert "skipped: 1. drop a seed" in queue.notifier.messages[-1]


def test_a_retire_row_waits_for_the_close_then_waits_for_retirement():
    queue = Queue(row(1, CLOSE), row(2, RETIRE, after="1"))
    queue.start()
    assert queue.statuses() == {1: "launched", 2: "waiting"}

    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert queue.processes.launched[-1] == bi.expected_argv(RETIRE, core_dir=CORE,
                                                            project=PROJECT)
    assert queue.processes.launched[-1][1:] == ["nemawashi-retire", PROJECT]
    assert queue.state["ended"] is None
    assert queue.state["pending"] == {"2": {"move": RETIRE, "identity": identity_file(2)}}


def test_a_retire_names_no_manual_refine_command_while_it_is_still_running():
    queue = Queue(row(1, RETIRE))
    queue.start()
    assert queue.state["ended"] is None
    assert queue.notifier.messages[-1].endswith("launched 1. retire a seed")


def test_the_retire_is_launched_as_the_scrum_master_with_a_completion_hook():
    """The existing skill completion hook wakes the queue after retirement."""
    queue = Queue(row(1, RETIRE))
    queue.start()

    env = queue.processes.calls[-1]["env"]
    assert env["INSTRUMENT_RUN_ROLE"] == "scrum-master"
    assert env["INSTRUMENT_RUN_CHAIN"] == "build-idea"
    assert env["DETACH_WATCHER_ON_COMPLETE"] == shim_path(1)


def test_the_old_reports_successors_wait_for_the_new_refinement_report():
    """The retire files the seed the report lives in, so the queue stops at it — a row that does
    not wait on it is blocked as well as one that does."""
    queue = Queue(row(1, CLOSE), row(2, RETIRE, after="1"), row(3, PICK, after="1"),
                  row(4, SWEEP, after="2"))
    queue.start()
    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "launched", 3: "blocked", 4: "blocked"}
    assert queue.state["ended"] is None
    assert [argv[1] for argv in queue.processes.launched] == ["shukuba-retire",
                                                              "nemawashi-retire"]


def test_a_retire_whose_launcher_fails_halts_the_queue():
    queue = Queue(row(1, RETIRE), codes=[1])
    queue.start()

    assert queue.statuses() == {1: "failed"}
    assert queue.state["ended"] == "halted"


# --- the owner's act: a station only the owner walks, where the queue stops --------------------

WALK_YOURSELF = "none — walk it yourself"
RESUME = f"{CORE}/launchers/build-idea/launcher.sh {PROJECT}"


def chain_change_launched(queue: Queue) -> bool:
    return any(argv[0].endswith("/launchers/chain-change/launcher.sh")
               for argv in queue.processes.launched)


def test_an_owners_act_row_ends_the_queue_and_no_row_waiting_on_it_starts():
    queue = Queue(row(1, CLOSE), row(2, OWNER, command=WALK_YOURSELF, after="1"),
                  row(3, PICK, after="2"))

    queue.start()

    assert queue.statuses() == {1: "launched", 2: "end", 3: "blocked"}
    assert queue.state["ended"] is None
    queue.close_station()
    queue.advance(1)
    assert queue.state["ended"] == "owner-owed"
    assert queue.processes.launched == [bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, station=STEM)]


def test_a_row_independent_of_the_owners_act_still_runs():
    queue = Queue(row(1, OWNER, command=WALK_YOURSELF), row(2, CLOSE))

    queue.start()

    assert queue.statuses() == {1: "end", 2: "launched"}
    assert queue.processes.launched == [bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, station=STEM)]
    queue.close_station()
    queue.advance(2)
    assert queue.state["ended"] == "owner-owed"


def test_the_owners_act_notification_carries_the_owners_step_and_the_resume_command():
    queue = Queue(row(1, OWNER, command=WALK_YOURSELF))

    queue.start()

    assert queue.notifier.messages[-1].splitlines()[0] == (
        f"instance · {PROJECT} · build-idea — owner's act owed — 1. {WALK_YOURSELF} — "
        f"once it is made, resume with: {RESUME}")


def test_a_table_with_an_owners_act_row_starts_no_chain_change_beside_it():
    queue = Queue(row(1, CLOSE), row(2, OWNER, command=WALK_YOURSELF, after="1"),
                  row(3, CHANGE, after="1"))
    queue.start()

    queue.close_station()
    queue.advance(1)

    assert not chain_change_launched(queue)
    assert queue.statuses()[3] == "blocked"
    assert ("blocked: 3. walk the next change — the owner's act comes first (row 2)"
            in queue.notifier.messages[-1])


def test_a_walk_row_beside_an_owners_act_with_no_wait_is_never_launched():
    queue = Queue(row(1, CHANGE), row(2, OWNER, command=WALK_YOURSELF))

    queue.start()

    assert queue.processes.launched == []
    assert queue.statuses() == {1: "blocked", 2: "end"}
    assert queue.state["ended"] == "owner-owed"


def test_a_walk_row_after_the_owners_act_is_blocked_not_launched():
    queue = Queue(row(1, OWNER, command=WALK_YOURSELF), row(2, CHANGE, after="1"))

    queue.start()

    assert queue.statuses() == {1: "end", 2: "blocked"}
    assert not chain_change_launched(queue)


def test_halted_outranks_owner_owed_and_owner_owed_outranks_a_retire():
    failed = Queue(row(1, CLOSE), row(2, OWNER, command=WALK_YOURSELF), codes=[1])
    failed.start()
    assert failed.state["ended"] == "halted"

    both = Queue(row(1, OWNER, command=WALK_YOURSELF), row(2, RETIRE, after="1"))
    both.start()

    assert both.state["ended"] == "owner-owed"
    assert WALK_YOURSELF in both.notifier.messages[-1]
    assert "retire launched" not in both.notifier.messages[-1]
    assert both.processes.launched == []


def test_the_start_message_and_the_dry_run_name_the_owners_act():
    queue = Queue(row(1, CLOSE), row(2, OWNER, command=WALK_YOURSELF, after="1"))

    plan = queue.describe()
    queue.start()

    assert bi._describe_line(plan.rows[1]) == "2. the owner's act — after 1 — owner"
    assert ("2. the owner's act — after 1 — end — the owner makes it"
            in queue.notifier.messages[0].splitlines())


def test_several_owners_act_rows_are_each_named():
    queue = Queue(row(1, OWNER, command="none — first act"),
                  row(2, OWNER, command="none — second act"))

    queue.start()

    assert "1. none — first act; 2. none — second act" in queue.notifier.messages[-1]


def owner_owed_after_a_close(*extra_rows: str) -> Queue:
    """A queue that has run its close and ended `owner-owed`: `1` close, `2` the owner's act
    after it, then `extra_rows` numbered from 3."""
    queue = Queue(row(1, CLOSE), row(2, OWNER, command=WALK_YOURSELF, after="1"), *extra_rows)
    queue.start()
    queue.close_station()
    queue.advance(1)
    assert queue.state["ended"] == "owner-owed"
    return queue


def test_a_plain_start_lands_the_owners_act_and_runs_what_waits_on_it():
    queue = owner_owed_after_a_close(row(3, CHANGE, after="2"))
    assert queue.statuses() == {1: "landed", 2: "end", 3: "blocked"}

    queue.start()

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "handed-off"}
    assert queue.processes.launched.count(
        [*bi.expected_argv(CHANGE, core_dir=CORE, project=PROJECT),
         "--context-cap", "250000"]) == 1
    assert queue.state["ended"] == "handed-off"


def test_a_walk_row_beside_the_owners_act_stays_blocked_on_resume():
    queue = owner_owed_after_a_close(row(3, CHANGE, after="1"), row(4, PICK, after="2"))

    queue.start()

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "blocked", 4: "launched"}
    assert queue.state["rows"][2]["reason"] == "the owner's act comes first (row 2)"
    assert not chain_change_launched(queue)


def test_a_walk_row_waiting_on_the_owners_act_through_another_row_runs_after_the_resume():
    queue = owner_owed_after_a_close(row(3, PICK, after="2"), row(4, CHANGE, after="3"))

    queue.start()

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "launched", 4: "waiting"}
    queue.pick_seed()
    queue.advance(3)
    assert queue.statuses()[4] == "handed-off"
    assert chain_change_launched(queue)


def test_a_hook_start_never_lands_the_owners_act():
    queue = owner_owed_after_a_close(row(3, CHANGE, after="2"))

    queue.start(by_hook=True)

    assert queue.statuses() == {1: "landed", 2: "end", 3: "blocked"}
    assert queue.state["ended"] == "owner-owed"
    assert not chain_change_launched(queue)


def test_the_owners_act_is_not_landed_while_a_row_it_waits_on_has_not():
    queue = Queue(row(1, CLOSE), row(2, OWNER, command=WALK_YOURSELF, after="1"))
    queue.start()
    queue.stop()
    queue.advance(1)
    assert queue.state["ended"] == "stopped"
    assert queue.statuses() == {1: "failed", 2: "end"}

    queue.start()

    assert queue.statuses() == {1: "launched", 2: "end"}
    assert queue.processes.launched.count(
        bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, station=STEM)) == 2


def test_a_resume_with_nothing_waiting_on_the_owners_act_is_refused_as_fully_consumed():
    queue = owner_owed_after_a_close()

    with pytest.raises(bi.QueueRefused, match="is fully consumed"):
        queue.start()


def test_a_row_waiting_on_the_owners_act_is_named_blocked_in_the_end_message():
    """CP-96: a row that waits on the owner's act does not start and is named `blocked`."""
    queue = owner_owed_after_a_close(row(3, PICK, after="2"))

    assert "blocked: 3. pick a seed — waits on 2" in queue.notifier.messages[-1].splitlines()


def test_the_owners_resume_launches_a_retire_that_waits_on_the_owners_act():
    """CP-94 has the refine write a retire after the owner's act when the owner's station is the
    last one, and says `build-idea` runs the rows naming the owner's act once the owner resumes it.
    The first end is `owner-owed`, and the retire waits on it; the owner's resume launches it."""
    queue = owner_owed_after_a_close(row(3, RETIRE, after="2"))
    assert not any(argv[1:2] == ["nemawashi-retire"] for argv in queue.processes.launched)

    queue.start()

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "launched"}
    assert queue.state["ended"] is None
    assert queue.processes.launched[-1][1:] == ["nemawashi-retire", PROJECT]
    assert not chain_change_launched(queue)


def test_a_close_landing_continues_the_queue_to_the_change_row():
    queue = Queue(row(1, CLOSE), row(2, CHANGE, after="1"),
                  environ={"PATH": "/usr/bin", "DETACH_WATCHER_ON_COMPLETE": "/stale/shim.sh"})
    queue.start()
    assert queue.statuses() == {1: "launched", 2: "waiting"}

    queue.close_station()
    queue.advance(1)

    assert queue.processes.launched[-1] == [
        *bi.expected_argv(CHANGE, core_dir=CORE, project=PROJECT), "--context-cap", "250000"]
    assert "DETACH_WATCHER_ON_COMPLETE" not in queue.processes.calls[-1]["env"]
    assert queue.statuses() == {1: "landed", 2: "handed-off"}
    assert queue.state["ended"] == "handed-off" and queue.state["pending"] == {}


def test_a_report_that_says_none_ends_done_at_once():
    queue = Queue(files={**sealed_world(), report_path():
                         "# r\n\n## Next moves\n\nNone — the route holds still.\n"})

    queue.start()

    assert queue.state["ended"] == "done" and queue.processes.launched == []


def test_a_start_while_a_queue_is_in_flight_is_refused():
    queue = Queue(row(1, SWEEP))
    queue.start()
    launched = len(queue.processes.launched)

    with pytest.raises(bi.QueueRefused, match=STATE):
        queue.start()

    assert len(queue.processes.launched) == launched


def test_a_start_on_a_new_report_replaces_the_old_record():
    files = {**sealed_world(row(1, DROP)), **sealed_world(row(1, CLOSE), key=OTHER_KEY)}
    queue = Queue(files=files)
    queue.start(key=KEY)
    assert queue.state["ended"] == "done" and queue.state["key"] == KEY

    queue.start(key=OTHER_KEY)

    assert queue.state["key"] == OTHER_KEY and queue.state["report"] == report_path(OTHER_KEY)
    assert queue.state["ended"] is None and queue.statuses() == {1: "launched"}


def test_a_repeated_or_stale_advance_is_a_no_op():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.close_station()
    queue.advance(1)
    launched = len(queue.processes.launched)
    before = queue.state

    repeated = queue.advance(1)
    stale = queue.advance(9)

    assert (repeated.acted, stale.acted) == (False, False)
    assert len(queue.processes.launched) == launched
    assert queue.state == before


def test_an_advance_after_the_queue_ended_is_counted_and_ignored():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.advance(1)
    assert queue.state["ended"] == "halted"

    result = queue.advance(1)

    assert result.acted is False and queue.state["reentries"] == 1


def test_the_advance_holds_the_state_lock():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.lock.holds.clear()

    queue.advance(1)

    assert queue.lock.holds == [STATE]


def test_the_report_is_byte_identical_after_start_and_every_advance():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, PICK, after="1"), row(4, DROP))
    before = queue.files.files[report_path()]

    queue.start()
    assert queue.files.files[report_path()] == before
    queue.close_station()
    queue.advance(1)
    queue.advance(2, "settled")
    queue.pick_seed()
    queue.advance(3)

    assert queue.files.files[report_path()] == before


def test_the_pending_row_is_on_disk_before_its_launcher_runs():
    seen: list = []
    queue = Queue(row(1, CLOSE))
    queue.processes.on_run = lambda argv: seen.append(queue.state["pending"])

    queue.start()

    assert len(seen) == 1 and list(seen[0]) == ["1"]


# --- what the owner is told -----------------------------------------------------------------------


def test_the_start_launch_and_end_messages():
    queue = Queue(row(1, CLOSE), row(2, RETIRE, after="1"), row(3, DROP))

    queue.start()

    start, launch = queue.notifier.messages
    assert f"{KEY}" in start and "3 rows" in start
    assert "1. close the reached station — after — — runs" in start
    assert "2. retire a seed — after 1 — runs" in start
    assert "3. drop a seed — after — — skip" in start
    assert launch.endswith("launched 1. close the reached station")

    queue.close_station()
    queue.advance(1)

    assert queue.notifier.messages[-1].endswith("launched 2. retire a seed")
    queue.advance(2, "failed")
    ended = queue.notifier.messages[-1]
    assert "halted" in ended and "skipped: 3. drop a seed" in ended


def test_an_unset_notifier_sends_nothing():
    processes = FakeProcesses()
    queue = Queue(row(1, CLOSE), notifier=chain.Notifier("", processes))
    queue.processes = processes

    queue.start()

    assert [argv[0].rsplit("/", 2)[-2] for argv in processes.launched] == ["skill"]


# --- how each kind of row is launched -----------------------------------------------------------


def test_a_skill_row_carries_the_shim_and_tags_and_a_chain_row_does_not_inherit_the_shim():
    stale = {"PATH": "/usr/bin", "DETACH_WATCHER_ON_COMPLETE": "/stale/shim.sh",
             "INSTRUMENT_RUN_AUDIT_TARGET": "development-plan"}
    queue = Queue(row(1, CLOSE), row(2, SWEEP), environ=stale)

    queue.start()
    queue.close_station()
    queue.advance(1)

    skill, sweep = queue.processes.calls
    assert skill["cwd"] == INSTANCE
    assert skill["env"]["DETACH_WATCHER_ON_COMPLETE"] == shim_path(1)
    assert skill["env"]["INSTRUMENT_RUN_CHAIN"] == "build-idea"
    assert skill["env"]["INSTRUMENT_RUN_WALK_ID"] == "queue-1"
    assert skill["env"]["INSTRUMENT_RUN_ROLE"] == "scrum-master"
    assert "INSTRUMENT_RUN_AUDIT_TARGET" not in skill["env"]
    assert "DETACH_WATCHER_ON_COMPLETE" not in sweep["env"]

    shim = queue.files.files[shim_path(1)]
    assert shim_path(1) in queue.files.executable
    assert shim.startswith("#!/usr/bin/env bash") and "nohup" in shim
    for part in (ENGINE, "--advance", STATE, " 1 ", '"$1"'):
        assert part in shim


def test_the_queue_shim_is_the_owners_rendering():
    queue = Queue(row(1, CLOSE), row(2, SWEEP))

    queue.start()

    assert queue.files.files[shim_path(1)] == completion_shim.shim_text(
        ENGINE, ("--advance", STATE, "1"), f"{LOGS}/build-idea-{PROJECT}.log")


def test_the_queue_shim_preserves_its_pre_extraction_bytes():
    queue = Queue(row(1, CLOSE), row(2, SWEEP))

    queue.start()

    assert queue.files.files[shim_path(1)] == (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'nohup python3 {ENGINE} --advance {STATE} 1 "$1" </dev/null '
        f">>{LOGS}/build-idea-{PROJECT}.log 2>&1 &\n"
    )


def test_a_pick_and_a_cut_are_tagged_with_the_pm_seat():
    queue = Queue(row(1, PICK), row(2, CUT_ROUTE, after="1"))

    queue.start()
    queue.pick_seed()
    queue.advance(1)

    assert queue.processes.calls[0]["env"]["INSTRUMENT_RUN_ROLE"] == "pm"
    assert queue.processes.calls[1]["env"]["INSTRUMENT_RUN_ROLE"] == "pm"


def test_a_sweep_row_is_launched_with_on_end_naming_its_shim():
    queue = Queue(row(1, SWEEP))

    queue.start()

    assert queue.processes.launched == [
        [*bi.expected_argv(SWEEP, core_dir=CORE, project=PROJECT, definition=FULL),
         "--on-end", shim_path(1)]]


def test_keep_awake_is_passed_to_every_launched_launcher():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, CHANGE, after="1, 2"))

    queue.start(keep_awake=True)
    queue.close_station()
    queue.advance(1)
    queue.advance(2, "settled")

    assert len(queue.processes.launched) == 3
    assert all(argv[-1] == "--keep-awake" for argv in queue.processes.launched)
    assert queue.state["keep_awake"] is True


def test_no_launcher_gets_keep_awake_unless_asked_for():
    queue = Queue(row(1, CLOSE), row(2, SWEEP))

    queue.start()

    assert all("--keep-awake" not in argv for argv in queue.processes.launched)


# --- rules a first pass left unproved: each found by breaking it and watching the suite stay green


def test_a_row_waiting_on_a_skip_row_is_blocked_and_named():
    """A kind with no launcher never lands, so what waits on it never can."""
    queue = Queue(row(1, DROP), row(2, PICK, after="1"))

    queue.start()

    assert queue.statuses() == {1: "skipped", 2: "blocked"}
    assert queue.state["ended"] == "done" and queue.processes.launched == []
    assert "blocked: 2. pick a seed" in queue.notifier.messages[-1]


def test_a_row_waiting_on_the_hand_off_row_is_blocked():
    """A hand-off is over the moment its launcher exits: its walk is not this queue's to wait on,
    so nothing can wait on it landing."""
    queue = Queue(row(1, CHANGE), row(2, SWEEP, after="1"))

    queue.start()

    assert queue.statuses() == {1: "handed-off", 2: "blocked"}
    assert len(queue.processes.launched) == 1


def test_a_close_lands_by_its_own_station_going_not_by_the_root_being_empty():
    """The next station may open the moment this one closes; the close still landed."""
    queue = Queue(row(1, CLOSE))
    queue.start()

    queue.close_station()
    queue.files.files[f"{JOURNEY}/shukuba/2026-09-19_the-next-station.md"] = "the next station"
    queue.advance(1)

    assert queue.statuses() == {1: "landed"}


# --- the command line: the composition root -----------------------------------------------------
#
# These run the real composition over a `tmp_path` instance — the real disk, the real seedbed
# reader, the real lock — on paths that launch nothing: a report of rows that only ever skip, or a
# state whose row lands on its own.


@pytest.fixture
def notifier_log(tmp_path):
    """A notifier that records its one argument, so what reached the owner is observable without
    any real channel being touched."""
    log = tmp_path / "notified.log"
    script = tmp_path / "notify.sh"
    script.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$1\" >> {log}\n")
    script.chmod(0o755)
    return script, log


def real_instance(tmp_path: Path, *rows: str, key: str = KEY) -> Path:
    """`sealed_world` written to a real tree, its `/instance` root moved to `tmp_path/instance`,
    holding its own `.providers.toml` — an unforced queue reads it at the instance root
    (CP-483)."""
    root = tmp_path / "instance"
    root.mkdir(parents=True, exist_ok=True)
    (root / ".providers.toml").write_text(DELIVERED_TEXT, encoding="utf-8")
    for path, text in sealed_world(*rows, key=key).items():
        target = root / os.path.relpath(path, INSTANCE)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    if any(RETIRE in text for text in rows):
        active = root / os.path.relpath(ROOT_SEED, INSTANCE)
        active.write_text("# seed\n- [x] walked\n")
    return root


def start_args(root: Path, *extra: str) -> list[str]:
    return ["--start", str(root / "system" / "logs" / "state.json"),
            "--instance-root", str(root), "--project", PROJECT, "--core-dir", CORE,
            "--shim-dir", str(root / "system" / "logs"), *extra]


def test_main_requires_exactly_one_entry(capsys):
    assert bi.main([]) == 2
    err = capsys.readouterr().err
    for entry in ("--start", "--advance", "--describe", "--stop", "--wait-on-walk"):
        assert entry in err

    assert bi.main(["--start", "/s", "--advance", "/s", "1", "completed"]) == 2
    assert "mutually exclusive" in capsys.readouterr().err
    assert bi.main(["--describe", "/s", "--start", "/s"]) == 2


def test_start_names_its_missing_required_flags(capsys):
    assert bi.main(["--start", "/s", "--project", PROJECT]) == 2

    err = capsys.readouterr().err
    for flag in ("--instance-root", "--core-dir", "--shim-dir"):
        assert flag in err
    assert "--project" not in err


def test_describe_names_its_missing_required_flags(capsys):
    assert bi.main(["--describe", "/s"]) == 2

    err = capsys.readouterr().err
    assert "--instance-root" in err and "--project" in err


def test_a_refused_start_exits_3_and_notifies(tmp_path, capsys, notifier_log):
    script, log = notifier_log
    root = tmp_path / "instance"
    (root / "system" / "projects" / PROJECT / "contexts").mkdir(parents=True)

    code = bi.main(start_args(root, "--notifier", str(script)))

    assert code == 3
    err = capsys.readouterr().err
    assert "no sealed unit" in err and "Traceback" not in err
    assert "no sealed unit" in log.read_text()
    assert not (root / "system" / "logs" / "state.json").exists()


def test_a_start_over_a_real_disk_records_the_end_through_the_real_composition(
        tmp_path, notifier_log):
    script, log = notifier_log
    root = real_instance(tmp_path, row(1, DROP), row(2, CUT_SEED))

    code = bi.main(start_args(root, "--notifier", str(script)))

    state = json.loads((root / "system" / "logs" / "state.json").read_text())
    assert code == 0
    assert (state["ended"], state["key"], state["notifier"]) == ("done", KEY, str(script))
    assert state["engine_path"] == os.path.abspath(bi.__file__)
    lines = log.read_text().splitlines()
    assert lines[0].endswith(f"build-idea started — {KEY}, 2 rows from {KEY}_report.md")
    assert any("done" in line for line in lines)


def test_start_takes_a_key_and_the_keep_awake_flag(tmp_path):
    root = real_instance(tmp_path, row(1, DROP), key=OTHER_KEY)

    code = bi.main(start_args(root, "--key", OTHER_KEY, "--keep-awake"))

    state = json.loads((root / "system" / "logs" / "state.json").read_text())
    assert code == 0 and state["key"] == OTHER_KEY and state["keep_awake"] is True


def test_describe_prints_one_line_per_row_and_sends_nothing(tmp_path, capsys, notifier_log):
    script, log = notifier_log
    root = real_instance(tmp_path, row(1, CLOSE), row(2, SWEEP, after="1"),
                         row(3, RETIRE), row(4, DROP))
    state = root / "system" / "logs" / "state.json"

    code = bi.main(["--describe", str(state), "--instance-root", str(root),
                    "--project", PROJECT, "--core-dir", CORE])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "1. close the reached station — after — — /core/launchers/skill/launcher.sh "
        "shukuba-retire proj 2026-09-18_a-station",
        "2. sweep the product's companions — after 1 — /core/launchers/chain-product/launcher.sh "
        "proj",
        "3. retire a seed — after — — /core/launchers/skill/launcher.sh nemawashi-retire proj",
        "4. drop a seed — after — — skip"]
    assert not state.exists() and not log.exists()


def test_describe_derives_core_from_the_engine_when_no_core_dir_is_given(tmp_path, capsys):
    root = real_instance(tmp_path, row(1, DROP))

    code = bi.main(["--describe", str(tmp_path / "s.json"), "--instance-root", str(root),
                    "--project", PROJECT])

    assert code == 0 and capsys.readouterr().out.splitlines() == [
        "1. drop a seed — after — — skip"]


def test_describe_refusing_says_so_on_stderr_and_never_messages_the_owner(tmp_path, capsys):
    root = tmp_path / "instance"
    (root / "system" / "projects" / PROJECT / "contexts").mkdir(parents=True)

    code = bi.main(["--describe", str(tmp_path / "s.json"), "--instance-root", str(root),
                    "--project", PROJECT])

    captured = capsys.readouterr()
    assert code == 3 and "no sealed unit" in captured.err
    assert "Traceback" not in captured.err and captured.out == ""


def test_advance_reads_the_notifier_off_the_state_and_lands_a_row(tmp_path, notifier_log):
    script, log = notifier_log
    root = real_instance(tmp_path, row(1, CLOSE))
    (root / "system" / "projects" / PROJECT / "journey" / "shukuba" / STATION).unlink()
    state_path = root / "system" / "logs" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = bi.QueueState(
        project=PROJECT, instance_root=str(root), core_dir=CORE, shim_dir=str(state_path.parent),
        notifier=str(script), key=KEY, report="r", queue_id="queue-1",
        rows=[{"number": 1, "move": CLOSE, "command": "c", "after": [], "argv": [],
               "status": "launched", "reason": ""}],
        pending={"1": {"move": CLOSE}})
    state_path.write_text(json.dumps(state.to_json()), encoding="utf-8")

    code = bi.main(["--advance", str(state_path), "1", "completed"])

    saved = json.loads(state_path.read_text())
    assert code == 0 and saved["ended"] == "done"
    assert "done" in log.read_text()


def test_advance_with_no_state_file_refuses_without_a_traceback(tmp_path, capsys):
    code = bi.main(["--advance", str(tmp_path / "missing.json"), "1", "completed"])

    assert code == 3
    err = capsys.readouterr().err
    assert "no build-idea queue state" in err and "Traceback" not in err


def test_a_crash_exits_5_without_an_uncaught_traceback(tmp_path, capsys, notifier_log):
    """A state whose pending row has no entry in its rows is a defect no engine method plans for;
    it must reach the owner, not die in a shim's log."""
    script, log = notifier_log
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(bi.QueueState(
        project=PROJECT, instance_root=str(tmp_path), notifier=str(script),
        pending={"1": {"move": CLOSE}}).to_json()), encoding="utf-8")

    code = bi.main(["--advance", str(state_path), "1", "completed"])

    assert code == 5
    assert "StopIteration" in capsys.readouterr().err
    assert "crashed advancing 1" in log.read_text() and "StopIteration" in log.read_text()


def test_the_journey_adapter_reads_a_file_seed_and_a_folder_seed(tmp_path):
    """On a `tmp_path` seedbed: a file seed, a folder seed holding `seed.md`, and the two things
    that are not seeds — the README, and a folder with no `seed.md`."""
    seedbed = tmp_path / "nemawashi"
    (seedbed / "unpicked").mkdir(parents=True)
    (seedbed / "a-file-seed.md").write_text("# a\n\n- [x] one\n- [ ] two\n", encoding="utf-8")
    (seedbed / "a-folder-seed").mkdir()
    (seedbed / "a-folder-seed" / "seed.md").write_text("# b\n\n- [ ] one\n", encoding="utf-8")
    (seedbed / "README.md").write_text("# readme\n", encoding="utf-8")
    (seedbed / "not-a-seed").mkdir()
    journey = bi.Journey()

    seeds = journey.root_seeds(str(seedbed))

    assert [os.path.basename(seed) for seed in seeds] == ["a-file-seed.md", "a-folder-seed"]
    assert [journey.checklist_items(seed) for seed in seeds] == [2, 1]


def test_the_journey_adapter_answers_empty_for_a_missing_seedbed_and_a_seed_with_no_items(
        tmp_path):
    seedbed = tmp_path / "nemawashi"
    seedbed.mkdir()
    (seedbed / "bare.md").write_text("# a seed with no checklist\n", encoding="utf-8")
    journey = bi.Journey()

    assert journey.root_seeds(str(tmp_path / "absent")) == []
    assert journey.checklist_items(str(seedbed / "bare.md")) == 0


# --- the owner's stop, and starting again from what is on disk ---------------------------------
#
# A stop is a field on the queue's one state file, so the lock that serialises the advances also
# serialises it. It lets the runs in flight finish and starts nothing new — including the restart
# `chain-change`'s end would otherwise make — until a plain start clears it and picks up from the
# disk, skipping what already landed.

CHAIN_CHANGE_STATE = f"{LOGS}/chain-change-{PROJECT}-state.json"
RESUME = f"{CORE}/launchers/build-idea/launcher.sh {PROJECT}"


def stopped_mid_way(*rows: str, **kwargs) -> Queue:
    """A queue started on `rows` and stopped while its first rows are in flight: nothing has ended
    yet, and nothing on the disk has changed."""
    queue = Queue(*rows, **kwargs)
    queue.start()
    queue.stop()
    return queue


def test_the_stopped_end_and_the_stop_fields_exist_and_a_bare_state_loads():
    assert bi.QueueEnd("stopped") is bi.QueueEnd.STOPPED
    only_the_stop = {"schema_version": 1, "project": PROJECT, "stop_requested": True,
                     "stop_requested_at": "2026-09-18T10:00:00+00:00"}

    loaded = bi.QueueState.from_json(only_the_stop)

    assert (loaded.stop_requested, loaded.rows, loaded.ended) == (True, [], None)
    assert bi.QueueState().stop_requested is False


def test_a_stop_with_nothing_live_creates_the_state_with_the_request():
    queue = Queue(row(1, CLOSE))
    assert STATE not in queue.files.files

    said = queue.stop()

    assert queue.state["stop_requested"] is True
    assert queue.state["stop_requested_at"] == "2026-09-18T10:00:00+00:00"
    assert queue.state["project"] == PROJECT
    assert "no queue is live — the loop will not restart itself" in said
    assert RESUME in said and PROJECT in said
    assert queue.notifier.messages == [said]
    assert queue.lock.holds == [STATE]
    assert queue.processes.launched == []


def test_a_stop_on_a_queue_that_has_ended_records_the_request_and_says_none_is_live():
    queue = Queue(row(1, DROP))
    queue.start()
    assert queue.state["ended"] == "done"

    said = queue.stop()

    assert queue.state["stop_requested"] is True and queue.state["ended"] == "done"
    assert "no queue is live" in said


def test_a_stop_on_a_live_queue_with_nothing_in_flight_ends_it_stopped():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.edit_state(lambda state: (state["pending"].clear(),
                                    state["rows"][0].update(status="landed")))

    said = queue.stop()

    assert queue.state["ended"] == "stopped" and queue.state["stop_requested"] is True
    assert queue.statuses() == {1: "landed", 2: "waiting"}
    assert "2. pick a seed" in queue.notifier.messages[-1]
    assert RESUME in said


RUN_START = "Fri Oct  2 15:24:58 2026"
WATCHER_START = "Fri Oct  2 15:24:59 2026"


def identity_file(number: int) -> str:
    return walk_stop.identity_path(shim_path(number))


def record_identity(queue: Queue, number: int, run_pid: int = 100, watcher_pid: int = 101) -> None:
    """What the run launcher leaves for a skill row: the run and its watcher, each with its start."""
    queue.table.starts[run_pid], queue.table.starts[watcher_pid] = RUN_START, WATCHER_START
    queue.files.write_text(identity_file(number), walk_stop.identity_text(
        queue.table, run_pid, watcher_pid))


def test_a_skill_row_launch_records_its_identity_on_pending_and_in_its_environment():
    queue = Queue(row(1, CLOSE), environ={"PATH": "/usr/bin", "DETACHED_RUN_PID": "7"},
                  files={**sealed_world(row(1, CLOSE)), identity_file(1): "left by an earlier run"})

    queue.start()

    env = queue.processes.calls[0]["env"]
    assert queue.state["pending"]["1"]["identity"] == identity_file(1)
    assert env[walk_stop.IDENTITY_VARIABLE] == identity_file(1)
    assert "DETACHED_RUN_PID" not in env
    assert queue.files.files[identity_file(1)] == ""


def test_a_chain_row_and_a_hand_off_launch_carry_no_identity_file():
    inherited = {"PATH": "/usr/bin", walk_stop.IDENTITY_VARIABLE: "/elsewhere.identity.json",
                 "DETACHED_RUN_PID": "7"}
    queue = Queue(row(1, SWEEP), row(2, CHANGE), environ=inherited)

    queue.start()
    assert queue.state["pending"] == {"1": {"move": SWEEP}}

    queue.advance(1, "settled")

    assert len(queue.processes.calls) == 2
    for call in queue.processes.calls:
        assert walk_stop.IDENTITY_VARIABLE not in call["env"]
        assert "DETACHED_RUN_PID" not in call["env"]
    assert queue.state["pending"] == {}
    assert identity_file(1) not in queue.files.files


def test_a_stop_mid_queue_stops_the_skill_row_in_flight_and_ends_the_queue_at_once():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    record_identity(queue, 1)

    said = queue.stop()

    assert queue.table.stopped == [101, 100], "the watcher, then the run"
    assert queue.state["ended"] == "stopped" and queue.state["pending"] == {}
    assert queue.state["stop_requested"] is True
    assert queue.statuses() == {1: "failed", 2: "waiting"}
    reason = queue.state["rows"][0]["reason"]
    assert "stopped by the owner" in reason and "run 100 stopped" in reason
    assert "never run: 2. pick a seed" in said and "failed: 1. close the reached station" in said
    assert RESUME in said and queue.notifier.messages[-1] == said


def test_a_stop_stops_a_chain_row_through_its_own_launchers_stop():
    environ = {"PATH": "/usr/bin", walk_stop.IDENTITY_VARIABLE: "/elsewhere.identity.json"}
    queue = Queue(row(1, SWEEP), row(2, CLOSE, after="1"), codes=[0, 3], environ=environ)
    queue.start()

    said = queue.stop()

    assert queue.processes.launched[-1] == [
        f"{CORE}/launchers/chain-product/launcher.sh", PROJECT, "--stop"]
    assert walk_stop.IDENTITY_VARIABLE not in queue.processes.calls[-1]["env"]
    assert queue.statuses() == {1: "failed", 2: "waiting"}
    assert "exited 3" in queue.state["rows"][0]["reason"]
    assert queue.state["ended"] == "stopped" and queue.state["pending"] == {}
    assert "never run: 2. close the reached station" in said


def test_a_stop_with_a_row_whose_run_is_gone_ends_the_queue():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    record_identity(queue, 1)
    queue.table.starts.clear()

    queue.stop()

    assert queue.table.stopped == []
    assert queue.state["ended"] == "stopped" and queue.state["pending"] == {}
    assert "already gone" in queue.state["rows"][0]["reason"]


def test_a_stop_never_signals_a_recycled_pid():
    queue = Queue(row(1, CLOSE))
    queue.start()
    record_identity(queue, 1)
    queue.table.starts[100] = "Sat Oct  3 09:00:00 2026"
    queue.table.starts[101] = "Sat Oct  3 09:00:01 2026"

    queue.stop()

    assert queue.table.stopped == []
    assert "already gone" in queue.state["rows"][0]["reason"]


def test_a_stop_on_a_skill_row_with_no_recorded_identity_signals_nothing_and_says_so():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.edit_state(lambda state: state["pending"]["1"].pop("identity"))

    queue.stop()

    assert queue.table.stopped == []
    assert queue.state["ended"] == "stopped"
    assert "no recorded identity" in queue.state["rows"][0]["reason"]


def test_a_finish_delivered_after_the_stop_is_a_counted_reentry():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    record_identity(queue, 1)
    queue.stop()
    queue.close_station()
    before = queue.files.files[STATE]

    result = queue.advance(1)

    assert result.acted is False and result.ended == "stopped"
    assert queue.state["reentries"] == 1
    assert queue.statuses() == {1: "failed", 2: "waiting"}
    assert json.loads(before) | {"reentries": 1} == queue.state


def test_the_stop_still_suppresses_the_hook_restart_and_a_plain_start_resumes():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    record_identity(queue, 1)
    queue.stop()
    before = queue.files.files[STATE]
    launched = len(queue.processes.launched)

    result = queue.start(by_hook=True)

    assert result.acted is False and queue.files.files[STATE] == before
    assert len(queue.processes.launched) == launched

    queue.start()

    assert queue.state["stop_requested"] is False and queue.state["ended"] is None
    assert queue.statuses() == {1: "launched", 2: "waiting"}
    assert queue.processes.launched[-1] == bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, station=STEM)


def test_the_refusal_names_the_stop_command_and_never_deleting():
    queue = Queue(row(1, CLOSE))
    queue.start()

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    assert f"{CORE}/launchers/build-idea/launcher.sh {PROJECT} --stop" in str(refused.value)
    assert "delete" not in str(refused.value)


def test_the_refusal_says_nothing_will_finish_a_queue_whose_runs_are_gone():
    queue = Queue(row(1, CLOSE))
    queue.start()
    record_identity(queue, 1)
    queue.table.starts.clear()

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    assert "Nothing will finish it" in str(refused.value)
    assert "delete" not in str(refused.value)


def test_a_stop_is_seen_by_the_hook_start():
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))
    queue.close_station()
    queue.advance(1)
    before = queue.files.files[STATE]
    launched, sent = len(queue.processes.launched), len(queue.notifier.messages)

    result = queue.start(by_hook=True)

    assert result.acted is False
    assert queue.files.files[STATE] == before, "a suppressed hook start changes nothing"
    assert len(queue.processes.launched) == launched
    assert len(queue.notifier.messages) == sent + 1
    said = queue.notifier.messages[-1]
    assert f"{PROJECT}: build-idea is stopped — chain-change's end did not restart it" in said
    assert f"run {RESUME} to resume" in said


def test_a_stop_persists_across_a_new_report():
    files = {**sealed_world(row(1, CLOSE)), **sealed_world(row(1, SWEEP), key=OTHER_KEY)}
    queue = Queue(files=files)
    queue.start(key=KEY)
    queue.stop()
    queue.close_station()
    queue.advance(1)

    result = queue.start(by_hook=True, key=OTHER_KEY)

    assert result.acted is False and queue.state["key"] == KEY
    assert queue.state["stop_requested"] is True


def test_a_hook_start_with_no_stop_requested_starts_as_any_other():
    queue = Queue(row(1, CLOSE))

    queue.start(by_hook=True)

    assert queue.statuses() == {1: "launched"}


def test_a_plain_start_clears_the_stop_and_resumes():
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))
    queue.close_station()
    assert queue.statuses() == {1: "failed", 2: "waiting"} and queue.state["ended"] == "stopped"

    queue.start()

    assert queue.state["stop_requested"] is False and queue.state["ended"] is None
    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert queue.processes.launched[-1] == bi.expected_argv(PICK, core_dir=CORE, project=PROJECT)


def test_a_plain_start_on_a_stop_that_found_no_queue_starts_a_fresh_one():
    queue = Queue(row(1, CLOSE))
    queue.stop()

    queue.start()

    assert queue.state["stop_requested"] is False and queue.statuses() == {1: "launched"}


def test_rows_landed_while_stopped_are_skipped_on_resume():
    """The close's run finished after the queue stopped, so the stop recorded it failed; the
    station is closed on disk now, so the resume lands it without launching it again."""
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))
    queue.advance(1)
    assert queue.statuses() == {1: "failed", 2: "waiting"}
    queue.close_station()
    launched = len(queue.processes.launched)

    queue.start()

    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert [argv[0].rsplit("/", 2)[-2:][0] for argv in queue.processes.launched[launched:]] == [
        "skill"]
    assert queue.processes.launched[-1] == bi.expected_argv(PICK, core_dir=CORE, project=PROJECT)


def test_a_resume_reruns_a_row_that_failed_or_never_ran():
    queue = Queue(row(1, SWEEP), row(2, CLOSE), row(3, PICK, after="2"))
    queue.start()
    queue.advance(1, "settled")
    queue.stop()
    assert queue.statuses() == {1: "landed", 2: "failed", 3: "waiting"}
    launched = len(queue.processes.launched)

    queue.start()

    assert queue.statuses() == {1: "landed", 2: "launched", 3: "waiting"}
    assert queue.processes.launched[launched:] == [
        bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, station=STEM)]
    assert queue.state["pending"].keys() == {"2"}


def test_a_resume_reblocks_what_a_still_failed_row_blocked():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.advance(1)
    assert queue.statuses() == {1: "failed", 2: "blocked"}

    queue.start()

    assert queue.statuses() == {1: "launched", 2: "waiting"}


def test_a_resume_trusts_a_recorded_landed_sweep_and_reruns_an_unrecorded_one():
    """A sweep has no fact on the disk to check, so what the record says is all there is: landed
    stays landed, and one that never recorded an end runs again."""
    queue = Queue(row(1, SWEEP), row(2, SWEEP))
    queue.start()
    queue.advance(1, "settled")
    queue.stop()
    assert queue.statuses() == {1: "landed", 2: "failed"}
    launched = len(queue.processes.launched)

    queue.start()

    assert queue.processes.launched[launched:] == [
        [*bi.expected_argv(SWEEP, core_dir=CORE, project=PROJECT, definition=FULL),
         "--on-end", shim_path(2)]]
    assert queue.statuses() == {1: "landed", 2: "launched"}


def test_a_resume_keeps_a_skipped_row_and_a_handed_off_row_as_they_were():
    """With those two kept and the one runnable row landed on the disk, nothing is left to run —
    so the resume is refused, and refused without disturbing the record the stop left."""
    queue = Queue(row(1, CHANGE), row(2, DROP), row(3, CLOSE))
    queue.start()
    assert queue.statuses() == {1: "handed-off", 2: "skipped", 3: "launched"}
    queue.stop()
    queue.close_station()
    launched = len(queue.processes.launched)

    with pytest.raises(bi.QueueRefused):
        queue.start()

    assert queue.statuses() == {1: "handed-off", 2: "skipped", 3: "failed"}
    assert len(queue.processes.launched) == launched

def test_a_fully_consumed_report_is_refused():
    queue = Queue(row(1, CLOSE), row(2, DROP), row(3, CHANGE, after="1"))
    queue.start()
    queue.close_station()
    queue.advance(1)
    assert queue.state["ended"] == "handed-off"

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    assert f"{report_path()} is fully consumed" in str(refused.value)
    assert "every row it runs has landed or was handed off" in str(refused.value)


def test_a_resume_announces_the_rows_it_carried_over_as_already_landed():
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))
    queue.close_station()
    queue.advance(1)

    queue.start()

    started = [m for m in queue.notifier.messages if "started" in m][-1]
    assert "1. close the reached station — after — — already landed" in started
    assert "2. pick a seed — after 1 — runs" in started


def test_a_start_is_refused_while_a_chain_change_walk_is_live():
    queue = Queue(row(1, CLOSE))
    live = {"ended": None, "pending": {"specs": {"step": "specs", "audited": None}}}
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps(live)

    with pytest.raises(bi.QueueRefused, match="chain-change"):
        queue.start()

    assert queue.processes.launched == []


def test_a_start_is_allowed_once_the_chain_change_walk_records_an_end():
    queue = Queue(row(1, CLOSE))
    ended = {"ended": "sealed", "pending": {}}
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps(ended)

    queue.start()

    assert queue.statuses() == {1: "launched"}


def test_a_chain_change_walk_with_nothing_pending_is_not_live():
    queue = Queue(row(1, CLOSE))
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps({"ended": None, "pending": {}})

    queue.start()

    assert queue.statuses() == {1: "launched"}


def test_a_plain_start_refused_by_a_live_chain_change_walk_still_clears_the_stop():
    """The owner running a plain start means: no longer stopped. If a walk is live it cannot start
    now, but its end will reach this queue through the hook — which must not find the stop."""
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))
    queue.close_station()
    queue.advance(1)
    live = {"ended": None, "pending": {"specs": {"step": "specs", "audited": None}}}
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps(live)

    with pytest.raises(bi.QueueRefused, match="chain-change"):
        queue.start()

    assert queue.state["stop_requested"] is False


def test_the_report_is_byte_identical_through_stop_and_resume():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    before = queue.files.files[report_path()]

    queue.start()
    queue.stop()
    queue.close_station()
    queue.advance(1)
    queue.start()

    assert queue.files.files[report_path()] == before


def test_the_stop_holds_the_state_lock_with_every_advance():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.lock.holds.clear()

    queue.stop()
    queue.advance(1)

    assert queue.lock.holds == [STATE, STATE]


# --- the command line grows the stop ------------------------------------------------------------


def test_main_stop_prints_its_line_and_exits_0(tmp_path, capsys, notifier_log):
    script, log = notifier_log
    root = tmp_path / "instance"
    root.mkdir()
    state = root / "system" / "logs" / "state.json"

    code = bi.main(["--stop", str(state), "--instance-root", str(root), "--project", PROJECT,
                    "--notifier", str(script)])

    printed = capsys.readouterr().out.strip()
    assert code == 0
    assert "no queue is live — the loop will not restart itself" in printed
    assert log.read_text().strip() == printed
    assert json.loads(state.read_text())["stop_requested"] is True


def test_main_stop_names_its_missing_required_flags_and_is_exclusive(capsys):
    assert bi.main(["--stop", "/s", "--instance-root", "/i"]) == 2
    assert "--project" in capsys.readouterr().err
    assert bi.main(["--stop", "/s", "--start", "/s"]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_main_start_passes_by_hook(tmp_path, notifier_log):
    """A stopped queue, started by the hook: nothing starts, the owner is told, and the exit is
    0 — the suppressed restart is a decision, not a failure."""
    script, log = notifier_log
    root = real_instance(tmp_path, row(1, DROP))
    state = root / "system" / "logs" / "state.json"
    assert bi.main(["--stop", str(state), "--instance-root", str(root), "--project", PROJECT]) == 0
    before = state.read_text()

    code = bi.main(start_args(root, "--by-hook", "--notifier", str(script)))

    assert code == 0 and state.read_text() == before
    assert "build-idea is stopped" in log.read_text()


# --- code-integrity: the dry run refuses what the start refuses (CP-77), and a sweep's hook is
# one word whatever its path holds (CP-79, CP-86) ------------------------------------------------


def test_the_dry_run_refuses_while_a_chain_change_walk_is_live():
    """CP-77: a queue that would be refused makes the dry run fail with the same reason — and a
    start is refused while a chain-change walk is live (CP-76)."""
    queue = Queue(row(1, CLOSE))
    live = {"ended": None, "pending": {"specs": {"step": "specs", "audited": None}}}
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps(live)

    with pytest.raises(bi.QueueRefused, match="chain-change walk is live"):
        queue.describe(core_dir=CORE)


def test_the_dry_run_refuses_a_fully_consumed_report():
    """CP-77 over CP-76's fully-consumed refusal: the dry run says what the start would say."""
    queue = Queue(row(1, CLOSE), row(2, DROP), row(3, CHANGE, after="1"))
    queue.start()
    queue.close_station()
    queue.advance(1)
    assert queue.state["ended"] == "handed-off"
    before = dict(queue.files.files)

    with pytest.raises(bi.QueueRefused, match="is fully consumed"):
        queue.describe(core_dir=CORE)

    assert queue.files.files == before


def test_the_dry_run_still_describes_a_report_the_queue_can_resume():
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))
    queue.advance(1)
    assert queue.state["ended"] == "stopped"

    plan = queue.describe(core_dir=CORE)

    assert [planned.number for planned in plan.rows] == [1, 2]


def test_a_sweep_rows_on_end_is_one_word_when_its_shim_path_holds_a_space():
    """CP-86: the chain splits its `--on-end` the way a shell does. The sweep's shim must reach
    it as one command, or the sweep's end never lands its row (CP-79) and the queue waits on it
    for ever."""
    spaced = f"{INSTANCE}/system/my logs"
    queue = Queue(row(1, SWEEP))

    queue.engine().start(instance_root=INSTANCE, project=PROJECT, core_dir=CORE,
                         shim_dir=spaced)

    argv = queue.processes.launched[0]
    hook = argv[argv.index("--on-end") + 1]
    assert shlex.split(hook) == [f"{spaced}/build-idea-{PROJECT}-row-1.sh"]


# --- the provider: forced for the queue, else the provider file's entry for the row --------------

PROVIDER = "KENSAIAPP_AGENT_PROVIDER"
INHERITED = {"PATH": "/usr/bin", PROVIDER: "codex"}

# The queue's own members: every kind whose row runs a skill, by its kind's name.
SKILL_ROWS = [move for move, kind in bi.KINDS.items()
              if kind.disposition is bi.Disposition.RUN_SKILL]


def _launched_skill_row(move: str, *, forced: str = "", **queue_arguments) -> Queue:
    """A queue that has launched the row of `move` — through a report row for a report kind, and
    through a landed retirement for `refine a seed`, which no report may name."""
    if move == _REFINE_A_SEED:
        queue = retiring_queue(**queue_arguments)
        queue.start(forced_provider=forced)
        land_retirement(queue)
        return queue
    command = (f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`"
               if move == _DOCS_CUT_MOVE else None)
    queue = Queue(row(1, move, command=command), **queue_arguments)
    queue.start(forced_provider=forced)
    return queue


_REFINE_A_SEED = "refine a seed"
_DOCS_CUT_MOVE = "cut from the product's documents"


def _launch_of(queue: Queue, move: str) -> dict:
    """The one launch of `move`'s skill."""
    skill = bi.KINDS[move].arguments[0]
    [call] = [call for call in queue.processes.calls if call["argv"][1:2] == [skill]]
    return call


def test_the_skill_rows_are_the_seven_the_provider_file_names():
    assert SKILL_ROWS == ["close the reached station", "readme-status", "pick a seed",
                          "cut the route", "retire a seed", "refine a seed",
                          "cut from the product's documents"]


@pytest.mark.parametrize("move", SKILL_ROWS)
def test_every_skill_row_launches_on_its_cp275_provider(move):
    """E1 — each skill row on the provider the delivered file names for it, `claude` for each,
    whatever the engine's own environment inherited from the previous row."""
    queue = _launched_skill_row(move, environ=dict(INHERITED))

    assert _launch_of(queue, move)["env"][PROVIDER] == "claude"


@pytest.mark.parametrize("forced", ["claude", "codex", "gemini"])
@pytest.mark.parametrize("move", SKILL_ROWS)
def test_every_skill_row_can_be_forced_without_a_provider_file(move, forced):
    """CP-285: every skill row, including generated refinement, carries any known force."""
    port = ProviderText(None)

    queue = _launched_skill_row(move, forced=forced, provider_port=port, environ=dict(INHERITED))

    assert _launch_of(queue, move)["env"][PROVIDER] == forced
    assert port.reads == 0


@pytest.mark.parametrize("move", SKILL_ROWS)
def test_a_copy_lacking_a_skill_rows_entry_refuses_an_unforced_start_naming_it(move):
    """E2 — the whole own-member set is checked at start, not only the rows the report holds: a
    queue of one skipped row is refused all the same, before anything launches or is saved."""
    lacking = ProviderText(edited_text({f"build-idea.{move}": None}))
    queue = Queue(row(1, DROP), provider_port=lacking)

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    assert str(providers.build_idea_row(move)) in str(refused.value)
    assert queue.processes.calls == []
    assert STATE not in queue.files.files
    assert queue.notifier.messages == []


def test_main_refuses_a_start_naming_a_missing_row_entry(tmp_path, capsys, notifier_log):
    """E2 at the entry point (Ex 12): exit 3, the entry on stderr and on the owner's channel, and
    no state written. The file is the instance's own `.providers.toml` (CP-483)."""
    script, log = notifier_log
    root = real_instance(tmp_path, row(1, DROP))
    (root / ".providers.toml").write_text(edited_text({"build-idea.pick a seed": None}),
                                          encoding="utf-8")

    code = bi.main(start_args(root, "--notifier", str(script)))

    assert code == 3
    err = capsys.readouterr().err
    assert 'build-idea."pick a seed"' in err and "Traceback" not in err
    assert 'build-idea."pick a seed"' in log.read_text()
    assert "refused to start" in log.read_text()
    assert not (root / "system" / "logs" / "state.json").exists()


@pytest.mark.parametrize("text, named", [
    (edited_text({"build-idea.cut the route": "grok"}), ['build-idea."cut the route"', "'grok'"]),
    (None, [INSTANCE_PROVIDER_FILE]),
    ("[build-idea\n", [INSTANCE_PROVIDER_FILE]),
])
def test_a_bad_value_and_a_missing_file_refuse_an_unforced_start(text, named):
    """E3 — an unknown value names the entry and the value; a missing or non-TOML file names the
    file's path. Nothing launches and nothing is saved."""
    queue = Queue(row(1, CLOSE), provider_port=ProviderText(text))

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    for name in named:
        assert name in str(refused.value)
    assert queue.processes.calls == []
    assert STATE not in queue.files.files


@pytest.mark.parametrize("forced", ["codex", "claude"])
def test_a_forced_queue_starts_over_a_missing_file(forced):
    """E4 (Ex 23) — the force is every skill row's provider, and the file is never read."""
    port = ProviderText(None)
    queue = Queue(row(1, CLOSE), row(2, PICK), row(3, CUT_ROUTE), provider_port=port)

    queue.start(forced_provider=forced)
    queue.close_station()
    queue.advance(1)
    queue.pick_seed()
    queue.advance(2)

    assert [call["env"][PROVIDER] for call in queue.processes.calls] == [forced] * 3
    assert port.reads == 0


def test_a_forced_retirement_carries_the_force_into_its_refinement_over_a_missing_file():
    """E4 — a row the queue adds itself is forced like any report row."""
    queue = retiring_queue(provider_port=ProviderText(None))
    queue.start(forced_provider="codex")
    land_retirement(queue)

    assert [call["env"][PROVIDER] for call in queue.processes.calls] == ["codex", "codex"]


# --- the dry run refuses where the start does: `describe` runs the provider-file check ---------

LACKING_PICK = edited_text({"build-idea.pick a seed": None})


def _snapshot(queue: Queue) -> tuple:
    """Everything a describe must leave as it found it: the disk, the launches, the lock's holds,
    the owner's messages and the log."""
    return (dict(queue.files.files), list(queue.processes.calls), list(queue.lock.holds),
            list(queue.notifier.messages), list(queue.log.lines))


def test_unforced_describe_refuses_a_missing_entry_the_report_does_not_use():
    """CP-314 — the entries checked are every skill row's, whether or not the report holds a row
    of that kind: this report holds no pick row, and the dry run still names the pick's entry."""
    queue = Queue(row(1, DROP), provider_port=ProviderText(LACKING_PICK))
    before = _snapshot(queue)

    with pytest.raises(bi.QueueRefused) as refused:
        queue.describe(core_dir=CORE)

    assert 'build-idea."pick a seed"' in str(refused.value)
    assert _snapshot(queue) == before


def test_unforced_describe_refuses_an_entry_naming_no_provider():
    queue = Queue(row(1, DROP),
                  provider_port=ProviderText(edited_text({"build-idea.cut the route": "grok"})))

    with pytest.raises(bi.QueueRefused) as refused:
        queue.describe(core_dir=CORE)

    assert 'build-idea."cut the route"' in str(refused.value) and "'grok'" in str(refused.value)


def test_unforced_describe_refuses_a_missing_provider_file():
    queue = Queue(row(1, DROP), provider_port=ProviderText(None))

    with pytest.raises(bi.QueueRefused) as refused:
        queue.describe(core_dir=CORE)

    assert INSTANCE_PROVIDER_FILE in str(refused.value)


def test_unforced_describe_refuses_an_invalid_provider_file():
    queue = Queue(row(1, DROP), provider_port=ProviderText("[build-idea\n"))

    with pytest.raises(bi.QueueRefused) as refused:
        queue.describe(core_dir=CORE)

    assert INSTANCE_PROVIDER_FILE in str(refused.value)


def _a_fresh_report() -> Queue:
    return Queue(row(1, DROP))


def _a_report_the_record_already_carries() -> Queue:
    """A retire the record already carries: `describe` takes the resumed-record exit."""
    queue = retiring_queue()
    queue.start()
    queue.edit_state(lambda state: state.update(ended="stopped", pending={}))
    return queue


def _a_unit_whose_seed_retired_to_trail() -> Queue:
    return retired_queue(row(1, PICK), row(2, CUT_ROUTE, after="1"), row(3, CHANGE, after="2"))


def _a_rewritten_retirement_report() -> Queue:
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    land_refinement(queue, row(1, PICK))
    queue.pick_seed()
    queue.advance(3)
    queue.files.files[NEMA_REPORT] = next_moves(row(1, CUT_ROUTE))
    return queue


@pytest.mark.parametrize("make", [_a_fresh_report, _a_report_the_record_already_carries,
                                  _a_unit_whose_seed_retired_to_trail,
                                  _a_rewritten_retirement_report])
def test_unforced_describe_refuses_on_every_exit_path(make):
    """CP-314 — the check sits at the one end of `describe`, so no exit can skip it. The same
    tree describes without a refusal while the file is whole, so the refusal is the file's."""
    queue = make()
    queue.provider_port = ProviderText()
    queue.describe(core_dir=CORE)
    queue.provider_port = ProviderText(LACKING_PICK)
    before = _snapshot(queue)

    with pytest.raises(bi.QueueRefused) as refused:
        queue.describe(core_dir=CORE)

    assert 'build-idea."pick a seed"' in str(refused.value)
    assert _snapshot(queue) == before


@pytest.mark.parametrize("text", [None, "[build-idea\n"])
@pytest.mark.parametrize("forced", ["codex", "claude"])
def test_forced_describe_never_reads_the_provider_file(forced, text):
    """CP-317 — forced, the file is not read, so a file that is absent or not TOML cannot refuse."""
    port = ProviderText(text)
    queue = Queue(row(1, DROP), provider_port=port)

    plan = queue.describe(core_dir=CORE, forced_provider=forced)

    assert [planned.move for planned in plan.rows] == [DROP]
    assert port.reads == 0


def _a_live_queue() -> Queue:
    queue = Queue(row(1, SWEEP))
    queue.start()
    return queue


def _a_live_chain_change_walk() -> Queue:
    queue = Queue(row(1, CLOSE))
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps(
        {"ended": None, "pending": {"specs": {"step": "specs", "audited": None}}})
    return queue


def _no_sealed_unit() -> Queue:
    return Queue(files={STATION_PATH: "a station"})


def _a_row_whose_kind_is_unknown() -> Queue:
    return Queue(row(1, "reticulate the splines", command="none"))


@pytest.mark.parametrize("make, reason", [
    (_a_live_queue, "is still running"),
    (_a_live_chain_change_walk, "chain-change walk is live"),
    (_no_sealed_unit, "no sealed unit"),
    (_a_row_whose_kind_is_unknown, "row 1"),
])
def test_describe_and_start_give_the_same_non_provider_reason(make, reason):
    """CP-315 — a tree with more than one fault gives the dry run's answer the start's. Each tree
    also lacks an entry, so a check that ran first would name the entry instead of the reason."""
    queue = make()
    queue.provider_port = ProviderText(LACKING_PICK)

    with pytest.raises(bi.QueueRefused) as described:
        queue.describe(core_dir=CORE)
    with pytest.raises(bi.QueueRefused) as started:
        queue.start()

    assert str(described.value) == str(started.value)
    assert reason in str(described.value)
    assert "provider" not in str(described.value)


def _a_provider_file_lacking_pick(root: Path) -> None:
    """The instance's own `.providers.toml`, lacking one skill row's entry."""
    (root / ".providers.toml").write_text(LACKING_PICK, encoding="utf-8")


def _describe_args(root: Path, *extra: str) -> list[str]:
    return ["--describe", str(root / "system" / "logs" / "state.json"),
            "--instance-root", str(root), "--project", PROJECT, "--core-dir", CORE, *extra]


def test_main_describe_unforced_refuses_a_missing_entry(tmp_path, capsys):
    """CP-314 at the entry point: exit 3, the entry on stderr, no traceback, nothing sent or
    written — the start's refusal (`test_main_refuses_a_start_naming_a_missing_row_entry`)."""
    root = real_instance(tmp_path, row(1, DROP))
    _a_provider_file_lacking_pick(root)

    code = bi.main(_describe_args(root))

    captured = capsys.readouterr()
    assert code == 3
    assert 'build-idea."pick a seed"' in captured.err and "Traceback" not in captured.err
    assert captured.out == ""
    assert not (root / "system" / "logs" / "state.json").exists()


def test_main_describe_forced_prints_the_rows(tmp_path, capsys):
    """CP-317 at the entry point: the same copy, forced, is not read and the rows print."""
    root = real_instance(tmp_path, row(1, DROP))
    _a_provider_file_lacking_pick(root)

    code = bi.main(_describe_args(root, "--provider", "claude"))

    assert code == 0
    assert capsys.readouterr().out.splitlines() == ["1. drop a seed — after — — skip"]


def test_the_composition_root_reads_any_instance_root(tmp_path):
    """CP-483, CP-484: the port answers `<root>/.providers.toml` for any root, and none of them
    sits under the engine's own directory."""
    engine_directory = Path(bi.__file__).resolve().parent
    queue = bi.build_queue(str(tmp_path / "state.json"), notifier_command="",
                           engine_path=bi.__file__)

    for root in (tmp_path / "one", tmp_path / "two"):
        answered = queue.providers.at(str(root)).path
        assert answered == providers.instance_file(str(root))
        assert engine_directory not in Path(answered).parents


def test_describe_reads_the_instance_file_at_its_root():
    """CP-483: the row check reads `<instance_root>/.providers.toml` and nowhere else."""
    class PathsRead(ProviderText):
        paths: list[str] = []

        def read_text(self, path):
            self.paths.append(path)
            return super().read_text(path)

    port = PathsRead()
    queue = Queue(row(1, DROP), provider_port=port)

    queue.describe(core_dir=CORE)

    assert set(port.paths) == {INSTANCE_PROVIDER_FILE}


def test_start_without_the_file_is_refused_naming_the_copy_command(tmp_path, capsys,
                                                                    notifier_log):
    """CP-486, main-level: an instance holding only the example is refused, naming the path and
    the command, and no state is written."""
    script, _ = notifier_log
    root = real_instance(tmp_path, row(1, DROP))
    (root / ".providers.toml").unlink()
    (root / ".providers.toml.example").write_text(DELIVERED_TEXT, encoding="utf-8")

    code = bi.main(start_args(root, "--notifier", str(script)))

    refusal = capsys.readouterr().err
    assert code == 3
    assert str(root / ".providers.toml") in refusal
    assert COPY_COMMAND in refusal
    assert not (root / "system" / "logs" / "state.json").exists()


def test_a_forced_start_without_the_file_starts(tmp_path, capsys, notifier_log):
    """CP-487: the same instance with `--provider codex` starts; the file is not read."""
    script, _ = notifier_log
    root = real_instance(tmp_path, row(1, DROP))
    (root / ".providers.toml").unlink()

    code = bi.main(start_args(root, "--notifier", str(script), "--provider", "codex"))

    assert COPY_COMMAND not in capsys.readouterr().err
    assert code != 3
    assert (root / "system" / "logs" / "state.json").exists()


def test_a_row_launch_reads_the_instance_file_as_edited_after_the_start():
    """CP-484: a skill row's provider follows an edit made after the start."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.provider_port.text = edited_text({"build-idea.pick a seed": "codex"})
    queue.close_station()

    queue.advance(1)

    assert queue.processes.calls[-1]["env"][PROVIDER] == "codex"


def test_a_row_fails_when_the_instance_file_is_gone():
    """CP-486: the row is `failed`, its reason names the copy command, and nothing more runs."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.provider_port.text = None
    queue.close_station()

    queue.advance(1)

    assert len(queue.processes.calls) == 1
    assert queue.statuses()[2] == "failed"
    assert COPY_COMMAND in queue.state["ended_reason"]


def test_a_copy_moves_one_row_and_no_other():
    """E6 (Ex 6) — an entry governs its own row alone."""
    copy = ProviderText(edited_text({"build-idea.pick a seed": "codex"}))
    queue = Queue(row(1, CLOSE), row(2, PICK), row(3, CUT_ROUTE), provider_port=copy)

    queue.start()
    queue.close_station()
    queue.advance(1)
    queue.pick_seed()
    queue.advance(2)

    assert [(call["argv"][1], call["env"][PROVIDER]) for call in queue.processes.calls] == [
        ("shukuba-retire", "claude"), ("nemawashi-pick", "codex"),
        ("stations-from-seed", "claude")]


def test_a_forced_provider_beats_the_rows_entry():
    copy = ProviderText(edited_text({"build-idea.close the reached station": "codex"}))
    queue = Queue(row(1, CLOSE), provider_port=copy)

    queue.start(forced_provider="gemini")

    assert queue.processes.calls[0]["env"][PROVIDER] == "gemini"
    assert queue.state["forced_provider"] == "gemini"


def test_each_skill_row_launch_reads_the_file_as_it_stands_then():
    """CP-283 — a valid edit made after start is taken at the next row's launch."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.provider_port.text = edited_text({"build-idea.pick a seed": "gemini"})
    queue.close_station()

    queue.advance(1)

    assert _launch_of(queue, PICK)["env"][PROVIDER] == "gemini"


def _refused_mid_queue(*extra_rows: str) -> Queue:
    """A queue whose close has launched and landed, and whose pick's entry was removed from the
    file before the pick could launch."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"), row(3, SWEEP, after="1"), *extra_rows)
    queue.start()
    queue.provider_port.text = edited_text({"build-idea.pick a seed": None})
    queue.close_station()
    queue.advance(1)
    return queue


def test_an_entry_removed_after_start_fails_that_row_and_stops_the_queue():
    """E8 (CP-283) — the row fails naming the entry, before its shim or pending is written; no
    later row launches, a chain row included; the queue ends halted and the owner is told."""
    queue = _refused_mid_queue()

    assert [call["argv"][1] for call in queue.processes.calls] == ["shukuba-retire"]
    entry = queue.state["rows"][1]
    assert entry["status"] == "failed"
    assert 'build-idea."pick a seed"' in entry["reason"]
    assert queue.state["pending"] == {}
    assert shim_path(2) not in queue.files.files
    assert queue.statuses()[3] != "launched"
    assert queue.state["ended"] == "halted"
    assert 'build-idea."pick a seed"' in queue.state["ended_reason"]
    assert 'build-idea."pick a seed"' in queue.notifier.messages[-1]


def test_a_refused_queue_ends_halted_at_once_naming_every_row_never_run():
    """A refusal launches nothing further and, with one row in flight at a time, no run is left to
    wait for: the queue ends halted when the refused launch is made."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"), row(3, SWEEP),
                  row(4, CUT_ROUTE, after="3"))
    queue.start()
    queue.provider_port.text = edited_text({"build-idea.pick a seed": None})
    queue.close_station()

    queue.advance(1)

    assert queue.state["pending"] == {}
    assert queue.state["ended"] == "halted"
    assert [call["argv"][1] for call in queue.processes.calls] == ["shukuba-retire"]
    assert "never run: 3. sweep the product's companions" in queue.notifier.messages[-1]
    assert "never run: 4. cut the route" in queue.notifier.messages[-1]


def test_the_next_start_clears_the_refusal_record():
    """The refusal is the queue's until the next start, which checks the file again: over a
    repaired file the refused row and the rows after it run."""
    queue = _refused_mid_queue()
    queue.provider_port.text = DELIVERED_TEXT

    queue.start()

    assert queue.processes.calls[-1]["argv"][1] == "nemawashi-pick"
    assert queue.statuses() == {1: "landed", 2: "launched", 3: "waiting"}
    assert queue.state["ended"] is None

    queue.pick_seed()
    queue.advance(2)

    assert queue.processes.calls[-1]["argv"][0].endswith("/chain-product/launcher.sh")
    assert queue.state["ended"] is None


@pytest.mark.parametrize("text, named", [
    (edited_text({"build-idea.pick a seed": "grok"}), ['build-idea."pick a seed"', "'grok'"]),
    (None, [INSTANCE_PROVIDER_FILE]),
    ("[build-idea", [INSTANCE_PROVIDER_FILE]),
])
def test_a_provider_file_becoming_invalid_stops_skill_and_chain_rows(text, named):
    """CP-283: every kind of invalid file stops the queue, including later chain rows."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"), row(3, SWEEP, after="1"))
    queue.start()
    queue.provider_port.text = text
    queue.close_station()

    queue.advance(1)

    assert len(queue.processes.calls) == 1
    assert queue.statuses()[2] == "failed"
    assert queue.state["pending"] == {}
    assert shim_path(2) not in queue.files.files
    assert queue.state["ended"] == "halted"
    assert all(part in queue.state["ended_reason"] for part in named)
    assert all(part in queue.notifier.messages[-1] for part in named)


def test_a_chain_row_of_an_unforced_queue_carries_no_provider_whatever_the_file_holds():
    """E7 (Ex 24) — an entry for a chain row is no member of the queue's and is ignored: the
    hand-off still carries no provider."""
    copy = ProviderText(edited_text({"build-idea.walk the next change": "codex",
                                     "build-idea.sweep the product's companions": "codex"}))
    queue = Queue(row(1, CHANGE), row(2, SWEEP), environ=dict(INHERITED), provider_port=copy)

    queue.start()

    assert [PROVIDER in call["env"] for call in queue.processes.calls] == [False, False]


@pytest.mark.parametrize("move", [SWEEP, CHANGE])
def test_a_chain_row_of_an_unforced_queue_carries_no_provider(move):
    """The nested chain runs each step on its own, not on the previous row's provider."""
    queue = Queue(row(1, move), environ=INHERITED)

    queue.start()

    assert PROVIDER not in queue.processes.calls[0]["env"]
    assert queue.processes.calls[0]["env"]["PATH"] == "/usr/bin"


@pytest.mark.parametrize("move", [SWEEP, CHANGE])
def test_a_chain_row_of_a_forced_queue_carries_the_force(move):
    queue = Queue(row(1, move))

    queue.start(forced_provider="codex")

    assert queue.processes.calls[0]["env"][PROVIDER] == "codex"


def test_every_start_states_the_force_so_a_resume_can_lift_it():
    """The start `chain-change`'s end makes carries the force in its environment, so it restates
    the same one; an owner's plain resume states none."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start(forced_provider="codex")
    queue.stop()
    queue.close_station()
    queue.advance(1)

    queue.start()

    assert queue.state["forced_provider"] == ""
    assert queue.processes.calls[-1]["env"][PROVIDER] == "claude"


def test_a_queue_state_written_before_the_force_existed_loads_unforced():
    state = bi.QueueState(project=PROJECT, forced_provider="codex")

    assert bi.QueueState.from_json(state.to_json()).forced_provider == "codex"

    older = state.to_json()
    del older["forced_provider"]
    assert bi.QueueState.from_json(older).forced_provider == ""


def test_main_start_records_the_force(tmp_path):
    root = real_instance(tmp_path, row(1, DROP))

    assert bi.main(start_args(root, "--provider", "codex")) == 0

    state_path = root / "system" / "logs" / "state.json"
    assert json.loads(state_path.read_text())["forced_provider"] == "codex"


def test_main_refuses_a_provider_it_does_not_know(tmp_path, capsys):
    root = real_instance(tmp_path, row(1, DROP))

    with pytest.raises(SystemExit):
        bi.main(start_args(root, "--provider", "grok"))

    assert "--provider" in capsys.readouterr().err


# --- the developer's context cap: kept on the queue, put on every chain-change row --------------


def test_a_chain_row_carries_the_context_cap():
    queue = Queue(row(1, CHANGE))

    queue.start(context_cap=80000)

    assert queue.processes.launched[0][-2:] == ["--context-cap", "80000"]


def test_a_chain_row_carries_the_default_cap():
    queue = Queue(row(1, CHANGE))

    queue.start()

    assert queue.processes.launched[0][-2:] == ["--context-cap", "250000"]
    assert cd.DEFAULT_CONTEXT_CAP == 250000


def test_the_cap_comes_before_keep_awake():
    queue = Queue(row(1, CHANGE))

    queue.start(context_cap=80000, keep_awake=True)

    assert queue.processes.launched[0][-3:] == ["--context-cap", "80000", "--keep-awake"]


@pytest.mark.parametrize("move", [CLOSE, PICK, CUT_ROUTE, SWEEP])
def test_a_row_that_is_not_a_chain_change_carries_no_context_cap(move):
    """A skill row's argv is unchanged, and so is the sweep's: it runs `chain-product`, which
    refuses a flag it does not know."""
    queue = Queue(row(1, move))

    queue.start(context_cap=80000)

    assert all("--context-cap" not in argv for argv in queue.processes.launched)


def test_a_resumed_queue_keeps_its_cap():
    queue = Queue(row(1, CLOSE), row(2, CHANGE, after="1"))
    queue.start(context_cap=80000)
    queue.stop()
    queue.close_station()
    queue.advance(1)

    queue.start(context_cap=1000)

    assert queue.state["context_cap"] == 80000
    assert queue.processes.launched[-1][-2:] == ["--context-cap", "80000"]


def test_a_queue_state_round_trip_keeps_the_cap_and_an_older_file_loads_the_default():
    state = bi.QueueState(project=PROJECT, context_cap=80000)

    assert bi.QueueState.from_json(state.to_json()).context_cap == 80000

    older = state.to_json()
    del older["context_cap"]
    assert bi.QueueState.from_json(older).context_cap == cd.DEFAULT_CONTEXT_CAP


def test_main_start_records_the_context_cap_and_defaults_it(tmp_path):
    root = real_instance(tmp_path, row(1, DROP))
    state_path = root / "system" / "logs" / "state.json"

    assert bi.main(start_args(root, "--context-cap", "80000")) == 0
    assert json.loads(state_path.read_text())["context_cap"] == 80000

    fresh = real_instance(tmp_path / "second", row(1, DROP))
    assert bi.main(start_args(fresh)) == 0
    assert json.loads(
        (fresh / "system" / "logs" / "state.json").read_text())["context_cap"] == 250000


@pytest.mark.parametrize("bad", ["abc", "0", "-5", "1.5", ""])
def test_main_refuses_a_context_cap_that_is_not_a_positive_integer(tmp_path, capsys, bad):
    root = real_instance(tmp_path, row(1, DROP))

    with pytest.raises(SystemExit) as refused:
        bi.main(start_args(root, "--context-cap", bad))

    assert refused.value.code != 0
    refusal = capsys.readouterr().err
    assert "--context-cap" in refusal and "positive integer" in refusal
    assert not (root / "system" / "logs" / "state.json").exists()


# Retirement continues through the Principal PM's report, using the same queue.
NEMA_REPORT = f"{INSTANCE}/system/projects/{PROJECT}/docs/nemawashi-refine/{SEED}_report.md"
DOCS_CUT = "cut from the product's documents"


def retiring_queue(**kwargs):
    queue = Queue(row(1, RETIRE), **kwargs)
    queue.journey.seeds = [ROOT_SEED]
    queue.files.files[ROOT_SEED] = "# seed\n- [x] walked\n"
    return queue


def retire_on_disk(queue):
    queue.files.files[f"{NEMAWASHI}/trail/{SEED}.md"] = queue.files.files.pop(ROOT_SEED)
    queue.journey.seeds = []


def land_retirement(queue):
    retire_on_disk(queue)
    queue.advance(1)


def refine_on_disk(queue, *moves):
    queue.files.files[NEMA_REPORT] = next_moves(*moves)


def land_refinement(queue, *moves):
    refine_on_disk(queue, *moves)
    queue.advance(2)


def test_retirement_waits_for_its_seed_then_launches_refinement_in_the_right_seat():
    queue = retiring_queue()
    queue.start(keep_awake=True, context_cap=123456, forced_provider="codex")
    assert queue.state["ended"] is None
    assert queue.processes.calls[0]["env"]["DETACH_WATCHER_ON_COMPLETE"] == shim_path(1)
    land_retirement(queue)
    assert queue.processes.launched[-1] == [
        f"{CORE}/launchers/skill/launcher.sh", "nemawashi-refine", PROJECT, SEED,
        "--keep-awake"]
    assert queue.processes.calls[-1]["env"]["INSTRUMENT_RUN_ROLE"] == "principal-pm"
    assert queue.processes.calls[-1]["env"]["KENSAIAPP_AGENT_PROVIDER"] == "codex"
    assert queue.state["pending"] == {
        "2": {"move": "refine a seed", "identity": identity_file(2)}}
    calls = len(queue.processes.calls)
    assert not queue.advance(1).acted
    assert len(queue.processes.calls) == calls


@pytest.mark.parametrize("moved_elsewhere", [False, True])
def test_retirement_completion_without_that_seed_in_trail_halts(moved_elsewhere):
    queue = retiring_queue()
    queue.start()
    if moved_elsewhere:
        queue.files.files.pop(ROOT_SEED)
        queue.journey.seeds = []
        queue.files.files[f"{NEMAWASHI}/trail/another.md"] = "retired"
    queue.advance(1)
    assert queue.state["ended"] == "halted"
    assert len(queue.processes.calls) == 1


def test_nemawashi_report_runs_sweep_cut_pick_route_and_next_change_in_order():
    queue = retiring_queue()
    queue.start(context_cap=123456)
    land_retirement(queue)
    land_refinement(queue,
        row(1, SWEEP),
        row(2, DOCS_CUT, command=f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`", after="1"),
        row(3, PICK, after="2"), row(4, CUT_ROUTE, after="3"), row(5, CHANGE, after="4"))
    assert queue.processes.launched[-1][0].endswith("/chain-product/launcher.sh")
    queue.advance(3, "settled")
    assert queue.processes.launched[-1][1:] == ["seeds-from-product-docs", PROJECT]
    queue.files.files[f"{NEMAWASHI}/unpicked/new.md"] = "# new seed\nCut from docs/SDD.md"
    queue.advance(4)
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]
    queue.pick_seed()
    queue.advance(5)
    assert queue.processes.launched[-1][1:] == ["stations-from-seed", PROJECT]
    queue.cut_route()
    queue.advance(6)
    assert queue.processes.launched[-1] == [
        f"{CORE}/launchers/chain-change/launcher.sh", PROJECT, "--context-cap", "123456"]
    assert queue.state["ended"] == "handed-off"


@pytest.mark.parametrize("report", [None, "old", "# invalid report"])
def test_refinement_without_a_fresh_valid_report_halts(report):
    queue = retiring_queue()
    if report == "old":
        queue.files.files[NEMA_REPORT] = next_moves(row(1, PICK))
    queue.start()
    land_retirement(queue)
    if report == "# invalid report":
        queue.files.files[NEMA_REPORT] = report
    queue.advance(2)
    assert queue.state["ended"] == "halted"
    assert len(queue.processes.calls) == 2


def test_empty_refinement_report_finishes_without_a_pick():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    queue.files.files[NEMA_REPORT] = (
        "## Next moves\n\nNothing is owed; the project's seedbed is exhausted.\n")
    queue.advance(2)
    assert queue.state["ended"] == "done"
    assert len(queue.processes.calls) == 2


def test_stop_during_retirement_resumes_at_refinement():
    queue = retiring_queue()
    queue.start()
    queue.stop()
    retire_on_disk(queue)
    assert queue.state["ended"] == "stopped"
    assert len(queue.processes.calls) == 1
    queue.start()
    assert queue.processes.launched[-1][1:3] == ["nemawashi-refine", PROJECT]
    assert len(queue.processes.calls) == 2


def test_stop_during_refinement_resumes_its_report_without_repeating_the_refine():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    queue.stop()
    refine_on_disk(queue, row(1, PICK), row(2, CUT_ROUTE, after="1"))
    assert queue.state["ended"] == "stopped"
    queue.start()
    assert [call["argv"][1] for call in queue.processes.calls] == [
        "nemawashi-retire", "nemawashi-refine", "nemawashi-pick"]


def test_refinement_owner_row_blocks_the_next_change_until_owner_resume():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    land_refinement(queue, row(1, OWNER), row(2, CHANGE, after="1"))
    assert queue.state["ended"] == "owner-owed"
    assert not chain_change_launched(queue)
    queue.start()
    assert chain_change_launched(queue)


def test_docs_cut_without_new_or_changed_candidates_still_releases_the_pick():
    # The owner's ruling, 2026-09-30: the PM always picks unless it can't. A cut that found
    # nothing new leaves the pool as it was, and the pool still holds a candidate to pick.
    queue = retiring_queue()
    queue.files.files[f"{NEMAWASHI}/unpicked/existing.md"] = "# existing candidate"
    queue.start()
    land_retirement(queue)
    land_refinement(queue,
        row(1, DOCS_CUT, command=f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`"),
        row(2, PICK, after="1"))
    queue.advance(3)
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_docs_cut_leaving_no_candidate_at_all_halts_before_the_pick():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    land_refinement(queue,
        row(1, DOCS_CUT, command=f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`"),
        row(2, PICK, after="1"))
    queue.advance(3)
    assert queue.state["ended"] == "halted"
    assert queue.processes.launched[-1][1:] == ["seeds-from-product-docs", PROJECT]
    assert "no candidate" in queue.state["rows"][2]["reason"]


def test_a_failed_docs_cut_run_halts_even_with_candidates_in_the_pool():
    queue = retiring_queue()
    queue.files.files[f"{NEMAWASHI}/unpicked/existing.md"] = "# existing candidate"
    queue.start()
    land_retirement(queue)
    land_refinement(queue,
        row(1, DOCS_CUT, command=f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`"),
        row(2, PICK, after="1"))
    queue.advance(3, "failed")
    assert queue.state["ended"] == "halted"
    assert queue.processes.launched[-1][1:] == ["seeds-from-product-docs", PROJECT]


@pytest.mark.parametrize("text", [
    "## Next moves\nI could not finish the refinement.\n",
    next_moves(row(1, PICK, command="`/evil/launcher.sh proj`")),
    next_moves(row(1, RETIRE)),
])
def test_invalid_nemawashi_moves_fail_before_any_successor_launches(text):
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    queue.files.files[NEMA_REPORT] = text
    queue.advance(2)
    assert queue.state["ended"] == "halted"
    assert len(queue.processes.calls) == 2


def test_refinement_report_survives_the_seed_folder_move_and_plain_resume():
    queue = retiring_queue()
    folder = f"{NEMAWASHI}/{SEED}"
    queue.files.files.pop(ROOT_SEED)
    queue.files.files.pop(report_path())
    queue.files.files[f"{folder}/seed.md"] = "- [x] walked"
    queue.files.files[f"{folder}/{KEY}_report.md"] = next_moves(row(1, RETIRE))
    queue.journey.seeds = [folder]
    queue.start()
    for path in list(queue.files.files):
        if path.startswith(folder + "/"):
            destination = path.replace(folder, f"{NEMAWASHI}/trail/{SEED}", 1)
            queue.files.files[destination] = queue.files.files.pop(path)
    queue.journey.seeds = []
    queue.advance(1)
    queue.stop()
    land_refinement(queue, row(1, PICK), row(2, CUT_ROUTE, after="1"))
    queue.start()
    assert queue.processes.launched[-1][1:3] == ["nemawashi-pick", PROJECT]
    assert queue.files.files[f"{NEMAWASHI}/trail/{SEED}/{KEY}_report.md"] == (
        next_moves(row(1, RETIRE)))


def test_failed_refine_retries_only_refinement_and_keeps_the_seed_identity():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    queue.advance(2, "failed")
    queue.start()
    assert [call["argv"][1] for call in queue.processes.calls] == [
        "nemawashi-retire", "nemawashi-refine", "nemawashi-refine"]
    assert queue.processes.launched[-1][-1] == SEED


def test_refinement_failure_does_not_release_moves_even_when_a_report_exists():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    queue.files.files[NEMA_REPORT] = next_moves(row(1, PICK))
    queue.advance(2, "failed")
    assert queue.state["ended"] == "halted"
    assert len(queue.processes.calls) == 2


def test_a_halted_cut_needs_the_owner_before_a_dependent_pick():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    land_refinement(queue, row(1, "re-run a halted cut", command="none — principal-pm session"),
                    row(2, PICK, after="1"))
    assert queue.state["ended"] == "owner-owed"
    assert len(queue.processes.calls) == 2
    queue.start()
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_describe_refuses_retirement_without_exactly_one_active_seed():
    queue = retiring_queue()
    queue.journey.seeds = []
    with pytest.raises(bi.QueueRefused, match="exactly one"):
        queue.describe()



def test_an_old_retire_launched_state_resumes_at_refinement_after_the_folder_moved():
    queue = retiring_queue()
    queue.start()
    def old_end(state):
        state.pop("seed")
        state["rows"][0]["status"] = "handed-off"
        state["pending"] = {}
        state["ended"] = "retire-launched"
    queue.edit_state(old_end)
    queue.journey.seeds = []
    queue.files.files.pop(ROOT_SEED)
    retired = f"{NEMAWASHI}/trail/{SEED}"
    queue.files.files[f"{retired}/seed.md"] = "- [x] walked"
    queue.files.files[f"{retired}/{KEY}_report.md"] = queue.files.files.pop(report_path())
    queue.start()
    assert queue.processes.launched[-1][1:] == ["nemawashi-refine", PROJECT, SEED]
    assert len(queue.processes.calls) == 2


def test_internal_refinement_cannot_be_injected_as_a_report_move():
    text = next_moves(row(1, "refine a seed"))
    with pytest.raises(bi.QueueRefused, match="internal"):
        validated(text)


def test_report_revision_changes_when_identical_content_is_written_again(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("## Next moves\nNothing is owed; the project's seedbed is exhausted.\n")
    reader = bi.Journey()
    before = reader.report_revision(str(report))
    os.utime(report, ns=(1, 1))
    assert reader.report_revision(str(report)) != before
    assert reader.report_revision(str(tmp_path / "missing")) is None


def test_the_retired_seeds_owner_act_does_not_block_the_next_seeds_walk():
    queue = Queue(row(1, OWNER), row(2, RETIRE, after="1"))
    queue.start()
    assert queue.state["ended"] == "owner-owed"
    queue.start()
    queue.files.files[f"{NEMAWASHI}/trail/{SEED}.md"] = queue.files.files.pop(ROOT_SEED)
    queue.journey.seeds = []
    queue.advance(2)
    queue.files.files[NEMA_REPORT] = next_moves(row(1, CHANGE))
    queue.advance(3)
    assert chain_change_launched(queue)
    assert queue.state["ended"] == "handed-off"


# A report rewritten in place is a new report; a retired seed's own refine report is the queue.
def test_a_report_rewritten_in_place_starts_a_new_queue_on_its_new_rows():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.close_station()
    queue.advance(1)
    assert queue.state["ended"] == "done"
    queue.files.files[report_path()] = next_moves(row(1, PICK))

    queue.start()

    assert [entry["move"] for entry in queue.state["rows"]] == [PICK]
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_report_written_again_unchanged_still_resumes():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.close_station()
    queue.advance(1)
    queue.files.files[report_path()] = next_moves(row(1, CLOSE))

    with pytest.raises(bi.QueueRefused, match="fully consumed"):
        queue.start()


def test_a_state_recorded_without_a_digest_resumes_as_before():
    queue = Queue(row(1, OWNER), row(2, PICK, after="1"))
    queue.start()
    first = queue.state["queue_id"]
    queue.edit_state(lambda state: state.pop("report_digest"))

    queue.start()

    assert queue.state["queue_id"] == first
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


RETIRED_REPORT = f"{NEMAWASHI}/trail/{SEED}/{KEY}_report.md"


def retired_world(*moves: str) -> dict[str, str]:
    """The sealed unit's report moved to trail/ with its retired seed, and that seed's
    nemawashi-refine report written by a run the queue did not start."""
    files = sealed_world(row(1, CLOSE), row(2, RETIRE, after="1"), station=False)
    files[RETIRED_REPORT] = files.pop(report_path())
    files[f"{NEMAWASHI}/trail/{SEED}/seed.md"] = "- [x] walked"
    if moves:
        files[NEMA_REPORT] = next_moves(*moves)
    return files


def retired_queue(*moves: str) -> Queue:
    queue = Queue(files=retired_world(*moves))
    queue.journey.seeds = []
    queue.files.files.pop(ROOT_SEED)
    return queue


def test_a_plain_start_after_the_seed_retired_runs_its_refine_report():
    docs_cut = row(1, DOCS_CUT,
                   command=f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`")
    queue = retired_queue(docs_cut, row(2, PICK, after="1"), row(3, CUT_ROUTE, after="2"),
                          row(4, CHANGE, after="3"))

    queue.start()

    assert queue.state["report"] == NEMA_REPORT
    assert queue.processes.launched[-1][1:] == ["seeds-from-product-docs", PROJECT]
    queue.files.files[f"{NEMAWASHI}/unpicked/new.md"] = "# new seed"
    queue.advance(1)
    queue.pick_seed()
    queue.advance(2)
    queue.cut_route()
    queue.advance(3)
    assert chain_change_launched(queue)
    assert queue.state["ended"] == "handed-off"


def test_a_retired_seeds_refine_report_runs_over_the_old_units_record():
    queue = Queue(row(1, CLOSE), row(2, OWNER, after="1"))
    queue.start()
    queue.close_station()
    queue.advance(1)
    assert queue.state["ended"] == "owner-owed"
    queue.files.files.pop(report_path())
    queue.files.files.update(retired_world(row(1, PICK)))

    queue.start()

    assert queue.state["report"] == NEMA_REPORT
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_consumed_refine_report_is_refused_and_its_rewrite_runs():
    queue = retired_queue(row(1, PICK))
    queue.start()
    queue.pick_seed()
    queue.advance(1)
    with pytest.raises(bi.QueueRefused, match="fully consumed"):
        queue.start()
    queue.files.files[NEMA_REPORT] = next_moves(row(1, CUT_ROUTE))

    queue.start()

    assert queue.processes.launched[-1][1:] == ["stations-from-seed", PROJECT]


def test_a_retired_seed_with_no_refine_report_is_refused_naming_the_refine():
    queue = retired_queue()
    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()
    assert NEMA_REPORT in str(refused.value)
    assert f"nemawashi-refine {PROJECT} {SEED}" in str(refused.value)
    assert not queue.processes.calls


def test_a_retired_seeds_refine_report_holding_a_unit_move_is_refused():
    queue = retired_queue(row(1, CLOSE))
    with pytest.raises(bi.QueueRefused, match="not a nemawashi next move"):
        queue.describe()


def test_a_rewritten_report_holding_a_retire_runs_before_the_retire_has_launched():
    queue = Queue(row(1, OWNER), row(2, RETIRE, after="1"))
    queue.start()
    assert queue.state["ended"] == "owner-owed"
    queue.files.files[report_path()] = next_moves(row(1, CLOSE), row(2, RETIRE, after="1"))

    queue.start()

    assert [entry["move"] for entry in queue.state["rows"]] == [CLOSE, RETIRE]
    assert queue.processes.launched[-1][1:] == ["shukuba-retire", PROJECT, STEM]


def test_a_refine_report_rewritten_after_the_queue_carried_it_runs_its_new_rows():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)
    land_refinement(queue, row(1, PICK))
    queue.pick_seed()
    queue.advance(3)
    with pytest.raises(bi.QueueRefused, match="fully consumed"):
        queue.start()
    queue.files.files[NEMA_REPORT] = next_moves(row(1, CUT_ROUTE))

    queue.start()

    assert queue.state["report"] == NEMA_REPORT
    assert queue.processes.launched[-1][1:] == ["stations-from-seed", PROJECT]


def test_a_resumed_record_without_a_digest_takes_one():
    queue = Queue(row(1, OWNER), row(2, PICK, after="1"))
    queue.start()
    queue.edit_state(lambda state: state.pop("report_digest"))
    queue.start()
    queue.pick_seed()
    queue.advance(2)
    queue.files.files[report_path()] = next_moves(row(1, CUT_ROUTE))

    queue.start()

    assert queue.processes.launched[-1][1:] == ["stations-from-seed", PROJECT]


# The PM picks unless it can't (owner, 2026-09-30): with a product document's companion live, the
# pick waits for the product chain to settle it, then picks.
PRODUCT = "/product"
COMPANION = f"{PRODUCT}/docs/srs_open_issues.md"


def cut_then_pick(queue, *, outcome="completed"):
    queue.files.files[f"{NEMAWASHI}/unpicked/existing.md"] = "# existing candidate"
    queue.start(product_path=PRODUCT)
    land_retirement(queue)
    land_refinement(queue,
        row(1, DOCS_CUT, command=f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`"),
        row(2, PICK, after="1"))
    queue.advance(3, outcome)


def test_a_live_companion_runs_the_product_chain_before_the_pick():
    queue = retiring_queue()
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    cut_then_pick(queue)
    assert queue.processes.launched[-1][:2] == [f"{CORE}/launchers/chain-product/launcher.sh",
                                                 PROJECT]
    sweep = max(entry["number"] for entry in queue.state["rows"])
    queue.files.files.pop(COMPANION)

    queue.advance(sweep, "settled")

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_product_chain_that_halts_holds_the_pick():
    queue = retiring_queue()
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    cut_then_pick(queue)
    sweep = max(entry["number"] for entry in queue.state["rows"])

    queue.advance(sweep, "halted")

    assert queue.state["ended"] == "halted"
    assert not any(argv[1:2] == ["nemawashi-pick"] for argv in queue.processes.launched)


def test_no_live_companion_picks_at_once():
    queue = retiring_queue()
    cut_then_pick(queue)
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_the_product_chain_runs_once_for_a_pick():
    queue = retiring_queue()
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    cut_then_pick(queue)
    sweep = max(entry["number"] for entry in queue.state["rows"])

    queue.advance(sweep, "settled")

    chains = [argv for argv in queue.processes.launched if argv[0].endswith("chain-product/launcher.sh")]
    assert len(chains) == 1
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_resume_after_a_failed_docs_cut_picks_from_the_pool_it_has():
    # Picks unless it can't: a failed cut leaves the pool as it was, and the pool can be picked.
    queue = retiring_queue()
    cut_then_pick(queue, outcome="failed")
    assert queue.state["ended"] == "halted"

    queue.start()

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_sweep_left_for_the_owner_still_releases_the_pick():
    queue = retiring_queue()
    queue.files.files[COMPANION] = "- [ ] an item only the owner settles"
    cut_then_pick(queue)
    sweep = max(entry["number"] for entry in queue.state["rows"])

    queue.advance(sweep, "left_for_the_owner")

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_link_loop_under_the_products_docs_is_walked_once(tmp_path):
    docs = tmp_path / "product" / "docs"
    (docs / "sub").mkdir(parents=True)
    (docs / "sub" / "srs_open_issues.md").write_text("- [ ] live")
    (docs / "sub" / "loop").symlink_to(docs)
    engine = bi.build_queue(str(tmp_path / "state.json"), notifier_command="",
                            engine_path=ENGINE)

    found = engine._live_companions(str(tmp_path / "product"), str(tmp_path / "instance"), PROJECT)

    assert found == [str(docs / "sub" / "srs_open_issues.md")]


def test_a_start_with_no_product_path_clears_the_recorded_one():
    queue = Queue(row(1, OWNER), row(2, PICK, after="1"))
    queue.start(product_path=PRODUCT)
    queue.files.files[COMPANION] = "- [ ] live"

    queue.start()

    assert queue.state["product_path"] == ""
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


# --- the product checkout: a run that leaves it dirtier fails its row and holds the queue -------


DIRTY = ["?? stray.txt", " M kept.md"]


def _dirty_reason(path: str = PRODUCT) -> str:
    return product_checkout.left_dirty([], DIRTY, path)


def test_a_skill_row_launch_records_the_product_checkout():
    checkout = FakeCheckout(["?? already.txt"])
    queue = Queue(row(1, CLOSE), checkout=checkout)

    queue.start(product_path=PRODUCT)

    assert queue.state["pending"]["1"]["checkout_before"] == ["?? already.txt"]
    assert checkout.read == [PRODUCT]


def test_a_row_that_leaves_the_product_checkout_dirtier_fails_and_the_queue_ends_halted():
    queue = Queue(row(1, CLOSE), checkout=FakeCheckout([], DIRTY))
    queue.start(product_path=PRODUCT)
    queue.close_station()

    queue.advance(1)

    entry = queue.state["rows"][0]
    assert entry["status"] == "failed"
    assert entry["reason"] == _dirty_reason()
    assert queue.state["ended"] == "halted"
    assert f"1. {CLOSE} failed: {_dirty_reason()}" in queue.notifier.messages[-1]


def _held_queue() -> Queue:
    """Row 1 ends dirtier with nothing else in flight, and rows 2 and 3 wait: the checkout reads
    clean at row 1's launch and dirty at its end."""
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, CUT_ROUTE, after="2"),
                  checkout=FakeCheckout([], DIRTY))
    queue.start(product_path=PRODUCT)
    queue.advance(1)
    return queue


def test_no_row_launches_after_a_dirty_row_even_one_that_does_not_wait_on_it():
    queue = _held_queue()

    assert queue.statuses() == {1: "failed", 2: "waiting", 3: "waiting"}
    assert [call["argv"][1] for call in queue.processes.calls] == ["shukuba-retire"]


def test_a_dirty_row_ends_the_queue_halted_at_once_naming_every_row_never_run():
    queue = _held_queue()

    assert queue.state["pending"] == {}
    assert queue.state["ended"] == "halted"
    assert "never run: 2. " in queue.notifier.messages[-1]
    assert "never run: 3. " in queue.notifier.messages[-1]


def test_a_chain_rows_end_is_checked():
    queue = Queue(row(1, SWEEP),
                  checkout=FakeCheckout(["?? old.txt"], ["?? old.txt", "?? new.txt"]))
    queue.start(product_path=PRODUCT)
    assert queue.state["pending"]["1"]["checkout_before"] == ["?? old.txt"]

    queue.advance(1, "settled")

    assert queue.state["rows"][0]["status"] == "failed"
    assert queue.state["ended"] == "halted"
    assert "`?? new.txt`" in queue.state["ended_reason"]
    assert "old.txt" not in queue.state["ended_reason"]


def test_an_empty_product_path_checks_nothing():
    checkout = FakeCheckout([], DIRTY)
    queue = Queue(row(1, CLOSE), checkout=checkout)

    queue.start()
    assert "checkout_before" not in queue.state["pending"]["1"]
    queue.close_station()
    queue.advance(1)

    assert checkout.read == []
    assert queue.statuses()[1] == "landed"


def test_a_row_pending_with_no_recorded_checkout_is_not_checked():
    queue = Queue(row(1, CLOSE), checkout=FakeCheckout([], DIRTY))
    queue.start(product_path=PRODUCT)
    queue.edit_state(lambda state: state["pending"]["1"].pop("checkout_before"))
    queue.close_station()

    queue.advance(1)

    assert queue.statuses()[1] == "landed"
    assert queue.state["ended"] == "done"


def test_a_checkout_unreadable_after_the_run_fails_the_row():
    queue = Queue(row(1, CLOSE), checkout=FakeCheckout([], None))
    queue.start(product_path=PRODUCT)
    queue.close_station()

    queue.advance(1)

    assert queue.state["rows"][0]["reason"].startswith(f"the product checkout {PRODUCT} could not")
    assert queue.state["ended"] == "halted"


def test_a_start_lifts_the_dirty_hold():
    queue = Queue(row(1, CLOSE), checkout=FakeCheckout([], DIRTY))
    queue.start(product_path=PRODUCT)
    queue.advance(1)
    assert queue.state["checkout_dirty"] is True and queue.statuses()[1] == "failed"

    queue.start(product_path=PRODUCT)

    assert queue.state["checkout_dirty"] is False
    assert queue.statuses()[1] == "launched"
    assert len(queue.processes.calls) == 2
    assert queue.state["ended"] is None


def test_build_queue_wires_a_real_checkout(tmp_path):
    engine = bi.build_queue(str(tmp_path / "state.json"), notifier_command="",
                            engine_path="/pinned/build_idea.py")

    assert isinstance(engine.checkout, product_checkout.Checkout)


# --- added by the code-integrity review ----------------------------------------------------


def test_a_dirty_row_fails_with_the_dirt_whatever_its_outcome():
    """tl_instruction.md, TL Review Notes: a dirty checkout fails the row with the dirt as its
    reason, never the outcome's — a `failed` end included."""
    queue = Queue(row(1, CLOSE), checkout=FakeCheckout([], DIRTY))
    queue.start(product_path=PRODUCT)

    queue.advance(1, "failed")

    assert queue.state["rows"][0]["reason"] == _dirty_reason()
    assert queue.state["ended"] == "halted"


# --- the card's `Definition:` decides the sweep (CP-516 to CP-518) --------------------------------

AGARI_SWEEP = f"{CORE}/launchers/chain-agari/launcher.sh"
PRODUCT_SWEEP = f"{CORE}/launchers/chain-product/launcher.sh"
NO_LINE = (f"no 'Definition:' line in {CARD}, and the sweep is decided by that line — "
           f"add **Definition:** full, prd-agari or none")


def sweep_text(definition: bi.Definition = FULL) -> str:
    return next_moves(row(1, SWEEP, command=command_for(SWEEP, definition=definition)))


def test_the_definition_is_read_up_to_its_comment():
    card = "# card\n\n**Definition:** prd-agari   <!-- full | prd-agari | none -->\n"

    assert bi.read_definition(card, card=CARD) is PRD_AGARI


def test_only_a_line_beginning_with_the_label_is_the_definition():
    """CP-518: the one line beginning *exactly* `**Definition:**`, as `chain-change`'s
    `^\\*\\*Definition:\\*\\*` reads it. An indented line, or prose naming the label mid-line, is
    not the card's line: it is not counted as a second one and does not give the value."""
    card = ("# card\n\nThe **Definition:** line below decides the sweep.\n"
            "  **Definition:** none\n"
            "**Definition:** prd-agari\n")

    assert bi.read_definition(card, card=CARD) is PRD_AGARI


@pytest.mark.parametrize("card", ["# card\n\nDefinition: full\n", None], ids=["no-line", "no-card"])
def test_a_card_with_no_definition_line_refuses_a_sweep_row(card):
    """A missing card reads the same as a card with no line, and both name the card's path."""
    with pytest.raises(bi.QueueRefused) as refused:
        validated(sweep_text(), card=card)

    assert str(refused.value) == NO_LINE


def test_a_card_with_two_definition_lines_refuses_a_sweep_row():
    card = "**Definition:** full\n\n**Definition:** none\n"

    with pytest.raises(bi.QueueRefused) as refused:
        validated(sweep_text(), card=card)

    assert str(refused.value) == (f"{CARD} carries 2 'Definition:' lines, and the sweep is "
                                  f"decided by that line — it must carry one")


@pytest.mark.parametrize("value", ["partial", ""])
def test_a_definition_outside_the_three_refuses_a_sweep_row(value):
    with pytest.raises(bi.QueueRefused) as refused:
        validated(sweep_text(), card=card_defining(value))

    assert str(refused.value) == (f"'Definition:' in {CARD} reads '{value}', and the sweep is "
                                  f"decided by that line — it must be full, prd-agari or none")


def test_a_queue_with_no_sweep_row_starts_on_a_card_with_no_definition_line():
    queue = Queue(row(1, CLOSE))
    queue.files.files[CARD] = "# card with no such line\n"

    queue.start()

    assert queue.processes.launched == [bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, station=STEM)]


def test_a_full_card_accepts_the_chain_product_sweep():
    rows = validated(sweep_text(FULL), card=card_defining("full"))

    assert [r.move for r in rows] == [SWEEP]


def test_a_prd_agari_card_accepts_the_chain_agari_sweep():
    rows = validated(sweep_text(PRD_AGARI), card=card_defining("prd-agari"))

    assert [r.move for r in rows] == [SWEEP]


def test_a_full_card_refuses_the_chain_agari_sweep():
    refused = refusals(sweep_text(PRD_AGARI), card=card_defining("full"))

    assert list(refused) == [1] and refused[1].startswith("its Command")
    assert f"{PRODUCT_SWEEP} {PROJECT}" in refused[1]


def test_a_prd_agari_card_refuses_the_chain_product_sweep():
    refused = refusals(sweep_text(FULL), card=card_defining("prd-agari"))

    assert list(refused) == [1] and refused[1].startswith("its Command")
    assert f"{AGARI_SWEEP} {PROJECT}" in refused[1]


@pytest.mark.parametrize("command_definition", [FULL, PRD_AGARI])
def test_a_none_card_refuses_any_sweep_row(command_definition):
    with pytest.raises(bi.QueueRefused) as refused:
        validated(sweep_text(command_definition), card=card_defining("none"))

    assert str(refused.value) == (
        f"row 1: 'Definition:' in {CARD} reads none — the card defines no product chain, so no "
        f"\"sweep the product's companions\" row runs for it")


def test_a_prd_agari_sweep_row_launches_chain_agari():
    queue = Queue(row(1, SWEEP, command=command_for(SWEEP, definition=PRD_AGARI)))
    queue.files.files[CARD] = card_defining("prd-agari")

    queue.start()

    assert queue.processes.launched == [[AGARI_SWEEP, PROJECT, "--on-end", shim_path(1)]]


@pytest.mark.parametrize("card", [card_defining("none"), None], ids=["none", "no-card"])
def test_describe_refuses_where_start_does_over_the_definition(card):
    queue = Queue(row(1, SWEEP))
    if card is None:
        queue.files.files.pop(CARD)
    else:
        queue.files.files[CARD] = card

    with pytest.raises(bi.QueueRefused) as described:
        queue.describe()
    with pytest.raises(bi.QueueRefused) as started:
        queue.start()

    assert str(described.value) == str(started.value)
    assert queue.processes.launched == []


@pytest.mark.parametrize("definition", [bi.Definition.NONE, None])
def test_the_sweeps_argv_needs_a_definition(definition):
    with pytest.raises(ValueError, match="sweep"):
        bi.expected_argv(SWEEP, core_dir=CORE, project=PROJECT, definition=definition)


def test_a_kind_other_than_the_sweep_ignores_the_definition():
    assert (bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT, definition=PRD_AGARI)
            == bi.expected_argv(CLOSE, core_dir=CORE, project=PROJECT))


def test_a_refinement_reports_sweep_row_is_checked_against_the_card():
    """The continuation validates the Principal PM's report with the same card as a start."""
    queue = retiring_queue()
    queue.files.files[CARD] = card_defining("prd-agari")
    queue.start()
    land_retirement(queue)

    land_refinement(queue, row(1, SWEEP, command=command_for(SWEEP, definition=FULL)))

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "failed"}
    assert f"{AGARI_SWEEP} {PROJECT}" in queue.state["rows"][2]["reason"]


def test_a_resumed_start_reads_the_card_again():
    queue = Queue(row(1, SWEEP), row(2, CLOSE, after="1"))
    queue.start()
    queue.stop()
    queue.files.files[CARD] = card_defining("none")

    with pytest.raises(bi.QueueRefused, match="reads none"):
        queue.start()


# --- the engine's own sweep follows the card (CP-519) ---------------------------------------------


def settle_a_pick_behind_a_live_companion(definition_card: str | None, *, companion: bool = True):
    """The unit retires, its refinement owes a pick, and the card reads as given."""
    queue = retiring_queue()
    if companion:
        queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    if definition_card is None:
        queue.files.files.pop(CARD)
    else:
        queue.files.files[CARD] = definition_card
    cut_then_pick(queue)
    return queue


def test_a_live_companion_on_a_prd_agari_card_runs_chain_agari_before_the_pick():
    queue = settle_a_pick_behind_a_live_companion(card_defining("prd-agari"))
    assert queue.processes.launched[-1][:2] == [AGARI_SWEEP, PROJECT]
    sweep = max(entry["number"] for entry in queue.state["rows"])
    queue.files.files.pop(COMPANION)

    queue.advance(sweep, "settled")

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_live_companion_on_a_none_card_does_not_hold_the_pick():
    queue = settle_a_pick_behind_a_live_companion(card_defining("none"))

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]
    assert not any(entry["move"] == SWEEP for entry in queue.state["rows"])


@pytest.mark.parametrize("card,reason", [
    ("# no such line\n", NO_LINE),
    ("**Definition:** full\n**Definition:** none\n",
     f"{CARD} carries 2 'Definition:' lines, and the sweep is decided by that line — "
     f"it must carry one"),
    (card_defining("partial"),
     f"'Definition:' in {CARD} reads 'partial', and the sweep is decided by that line — "
     f"it must be full, prd-agari or none"),
    (None, NO_LINE),
], ids=["no-line", "two-lines", "out-of-vocabulary", "no-card"])
def test_a_live_companion_on_an_unreadable_card_fails_the_pick(card, reason):
    queue = settle_a_pick_behind_a_live_companion(card)

    pick = next(entry for entry in queue.state["rows"] if entry["move"] == PICK)
    assert (pick["status"], pick["reason"]) == ("failed", reason)
    assert queue.state["ended"] == "halted"
    assert not any(argv[1:2] == ["nemawashi-pick"] for argv in queue.processes.launched)
    assert not any(entry["move"] == SWEEP for entry in queue.state["rows"])


def test_no_live_companion_never_reads_the_card():
    queue = settle_a_pick_behind_a_live_companion("# no such line\n", companion=False)

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_pick_failed_over_the_card_halts_the_queue_only_once_nothing_is_in_flight():
    """CP-519: the queue ends halted *once nothing is in flight* — a row running beside the
    failed pick is waited for, not cut off."""
    queue = retiring_queue()
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    queue.files.files[CARD] = "# no such line\n"
    queue.files.files[f"{NEMAWASHI}/unpicked/existing.md"] = "# existing candidate"
    queue.start(product_path=PRODUCT)
    land_retirement(queue)
    cut_command = f"`{CORE}/launchers/skill/launcher.sh seeds-from-product-docs {PROJECT}`"
    land_refinement(queue, row(1, DOCS_CUT, command=cut_command), row(2, PICK))

    pick = next(entry for entry in queue.state["rows"] if entry["move"] == PICK)
    cut = next(entry for entry in queue.state["rows"] if entry["move"] == DOCS_CUT)
    assert (pick["status"], pick["reason"]) == ("failed", NO_LINE)
    assert cut["status"] == "launched"
    assert queue.state["ended"] is None

    queue.advance(cut["number"])

    assert queue.state["ended"] == "halted"


# --- the Agari's companion is a live companion (CP-520) -------------------------------------------

AGARI_COMPANION = f"{INSTANCE}/system/projects/{PROJECT}/agari_open_issues.md"


def pick_behind_the_agari_companion(*, product_path: str, companion: bool):
    """The unit retires and its refinement owes a pick, the queue started with `product_path`."""
    queue = retiring_queue()
    if companion:
        queue.files.files[AGARI_COMPANION] = "- [ ] an item the Agari raised"
    queue.files.files[f"{NEMAWASHI}/unpicked/existing.md"] = "# existing candidate"
    queue.start(product_path=product_path)
    land_retirement(queue)
    land_refinement(queue, row(1, PICK))
    return queue


def test_a_live_agari_companion_alone_runs_the_sweep_before_the_pick():
    queue = pick_behind_the_agari_companion(product_path=PRODUCT, companion=True)

    assert queue.processes.launched[-1][:2] == [PRODUCT_SWEEP, PROJECT]
    sweep = max(entry["number"] for entry in queue.state["rows"])
    queue.files.files.pop(AGARI_COMPANION)

    queue.advance(sweep, "settled")

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_the_agari_companion_is_found_with_no_product_path():
    queue = pick_behind_the_agari_companion(product_path="", companion=True)

    assert queue.processes.launched[-1][:2] == [PRODUCT_SWEEP, PROJECT]
    assert any(entry["move"] == SWEEP for entry in queue.state["rows"])


def test_no_agari_companion_and_no_product_path_picks_at_once():
    queue = pick_behind_the_agari_companion(product_path="", companion=False)

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]
    assert not any(entry["move"] == SWEEP for entry in queue.state["rows"])


# --- a pick waits on the sweep the queue already holds (CP-522) -----------------------------------


def chain_launches(queue) -> list[list[str]]:
    return [argv for argv in queue.processes.launched if argv[0] == PRODUCT_SWEEP]


def rows_by_number(queue) -> dict[int, dict]:
    return {entry["number"]: entry for entry in queue.state["rows"]}


def companion_queue(*rows: str) -> Queue:
    """A queue over `rows`, with the product's companion live and the product path passed."""
    queue = Queue(*rows)
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    queue.start(product_path=PRODUCT)
    return queue


def test_a_pick_behind_a_launched_sweep_row_waits_on_it():
    queue = companion_queue(row(1, SWEEP), row(2, PICK))

    rows = rows_by_number(queue)
    assert queue.statuses() == {1: "launched", 2: "waiting"}
    assert rows[2]["after"] == [1] and rows[2]["swept"] is True
    assert len(chain_launches(queue)) == 1


def test_the_pick_waits_on_the_queued_sweep_then_picks_when_it_lands():
    queue = companion_queue(row(1, SWEEP), row(2, PICK))
    queue.files.files.pop(COMPANION)

    queue.advance(1, "settled")

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]
    assert len(chain_launches(queue)) == 1


def test_the_pick_is_blocked_when_the_queued_sweep_fails():
    queue = companion_queue(row(1, SWEEP), row(2, PICK))

    queue.advance(1, "halted")

    assert queue.statuses()[2] == "blocked"
    assert queue.state["ended"] == "halted"
    assert not any(argv[1:2] == ["nemawashi-pick"] for argv in queue.processes.launched)


def test_a_pick_waits_on_a_sweep_row_still_waiting():
    queue = companion_queue(row(1, CLOSE), row(2, SWEEP, after="1"), row(3, PICK))

    rows = rows_by_number(queue)
    assert sorted(rows) == [1, 2, 3]
    assert rows[2]["status"] == "waiting" and rows[3]["after"] == [2]
    assert rows[3]["swept"] is True
    assert chain_launches(queue) == []


def test_a_pick_ready_while_a_row_runs_gets_its_sweep_row_which_waits_its_turn():
    """CP-574: the pick is put behind the sweep row the queue adds even while another row runs;
    only the launches wait, one row at a time (CP-572)."""
    queue = companion_queue(row(1, CLOSE), row(2, PICK))

    rows = rows_by_number(queue)
    assert [entry["move"] for entry in queue.state["rows"]] == [CLOSE, PICK, SWEEP]
    assert queue.statuses() == {1: "launched", 2: "waiting", 3: "waiting"}
    assert rows[2]["after"] == [3] and rows[2]["swept"] is True
    assert chain_launches(queue) == []

    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "waiting", 3: "launched"}
    assert len(chain_launches(queue)) == 1

    queue.advance(3, "settled")

    assert queue.statuses() == {1: "landed", 2: "launched", 3: "landed"}
    assert queue.processes.launched[-1][1] == "nemawashi-pick"


def test_a_sweep_row_the_queue_adds_takes_its_turn_after_the_rows_it_already_held():
    """CP-573: a row the queue adds itself comes after the rows already held in row order, so the
    held row ready beside it starts first."""
    queue = companion_queue(row(1, CLOSE), row(2, PICK), row(3, CUT_ROUTE))
    assert queue.statuses() == {1: "launched", 2: "waiting", 3: "waiting", 4: "waiting"}

    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "waiting", 3: "launched", 4: "waiting"}
    assert chain_launches(queue) == []

    queue.pick_seed()
    queue.cut_route()
    queue.advance(3)

    assert queue.statuses() == {1: "landed", 2: "waiting", 3: "landed", 4: "launched"}
    assert len(chain_launches(queue)) == 1


def test_a_sweep_row_that_waits_on_the_pick_is_not_waited_on():
    queue = companion_queue(row(1, PICK), row(2, SWEEP, after="1"))

    rows = rows_by_number(queue)
    assert sorted(rows) == [1, 2, 3]
    assert rows[1]["after"] == [3] and rows[1]["swept"] is True
    assert rows[3]["move"] == SWEEP and rows[3]["status"] == "launched"
    assert len(chain_launches(queue)) == 1


def test_a_landed_sweep_row_does_not_hold_the_pick():
    queue = Queue(row(1, SWEEP), row(2, PICK, after="1"))
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    queue.start(product_path=PRODUCT)

    queue.advance(1, "settled")

    rows = rows_by_number(queue)
    assert sorted(rows) == [1, 2, 3]
    assert rows[2]["after"] == [1, 3] and rows[3]["move"] == SWEEP
    assert len(chain_launches(queue)) == 2


# --- the queue holds for a walk already in flight (CP-523 to CP-526) --------------------------------

WALK = f"{LOGS}/chain-{PROJECT}-state.json"
WAITING_ON_A_WALK = "waiting-on-a-walk"
WAITING_END = (f"instance · {PROJECT} · build-idea — waiting on a walk — {WALK} is still walking, "
               f"so nothing more was started. The queue is watching that walk and continues by "
               f"itself once it is no longer walking, unless the walk was stopped. If the queue "
               f"does not continue, resume with: {RESUME}")
UNWATCHED_END = (f"instance · {PROJECT} · build-idea — waiting on a walk — {WALK} is still "
                 f"walking, so nothing more was started. The queue could not watch that walk, so "
                 f"it does not continue by itself when the walk is no longer walking. Once that "
                 f"walk is no longer walking, resume with: {RESUME}")
CONTINUING = (f"instance · {PROJECT} · build-idea — continuing — {WALK} is no longer walking, so "
              f"the queue carries on from the rows that waited for it")
WALK_STOPPED = (f"instance · {PROJECT} · build-idea — still waiting on a walk — {WALK} was "
                f"stopped, so the queue does not continue by itself. Resume with: {RESUME}")
WATCH_ARGV = ["python3", ENGINE, "--wait-on-walk", STATE, "queue-1"]
WATCH_LOG = f"{LOGS}/build-idea-{PROJECT}.log"
REFUSED_AS_WALKING = (f"its launcher exited 4: {WALK} is still walking, so its chain did not "
                      f"start — the row waits, and is launched again when the queue continues "
                      f"after that walk is no longer walking")


def a_walk_is_in_flight(queue: Queue, **changes) -> None:
    """The chain's state file for the project, as a walk waiting on a launch leaves it."""
    walk = {"ended": None, "pending": {"document": "SRS"}, "schema_version": chain.STATE_SCHEMA}
    queue.files.files[WALK] = json.dumps({**walk, **changes})


def a_pick_over_a_live_companion(*rows: str, codes=None) -> Queue:
    queue = Queue(*(rows or (row(1, PICK),)), codes=codes)
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"
    return queue


def test_a_live_walk_adds_no_sweep_row_and_the_queue_waits_on_it():
    queue = a_pick_over_a_live_companion()
    a_walk_is_in_flight(queue)

    queue.start(product_path=PRODUCT)

    assert [entry["move"] for entry in queue.state["rows"]] == [PICK]
    assert queue.statuses() == {1: "waiting"} and not queue.state["rows"][0].get("swept")
    assert queue.processes.launched == []
    assert queue.state["ended"] == WAITING_ON_A_WALK


def test_the_waiting_end_names_the_walk_and_the_resume_command():
    queue = a_pick_over_a_live_companion()
    a_walk_is_in_flight(queue)

    queue.start(product_path=PRODUCT)

    first_line = queue.notifier.messages[-1].splitlines()[0]
    assert first_line == WAITING_END
    assert queue.state["ended_reason"] == WAITING_END.split(" — ", 1)[1]
    assert "never run: 1. pick a seed" in queue.notifier.messages[-1]


def test_an_ended_walk_does_not_hold_the_pick():
    queue = a_pick_over_a_live_companion()
    a_walk_is_in_flight(queue, ended="settled")

    queue.start(product_path=PRODUCT)

    assert [entry["move"] for entry in queue.state["rows"]] == [PICK, SWEEP]
    assert len(chain_launches(queue)) == 1


def test_a_walk_at_another_schema_does_not_hold_the_pick():
    queue = a_pick_over_a_live_companion()
    a_walk_is_in_flight(queue, schema_version=chain.STATE_SCHEMA + 1)

    queue.start(product_path=PRODUCT)

    assert [entry["move"] for entry in queue.state["rows"]] == [PICK, SWEEP]
    assert len(chain_launches(queue)) == 1


def test_a_sweep_refused_as_already_walking_waits_and_holds_the_queue():
    queue = Queue(row(1, SWEEP), row(2, CLOSE, after="1"), codes=[chain.EXIT_ALREADY_WALKING])

    queue.start(product_path=PRODUCT)

    rows = rows_by_number(queue)
    assert queue.statuses() == {1: "waiting", 2: "waiting"}
    assert rows[1]["reason"] == REFUSED_AS_WALKING
    assert queue.state["pending"] == {}
    assert queue.state["ended"] == WAITING_ON_A_WALK
    assert queue.notifier.messages[-1].splitlines()[0] == WAITING_END


def test_a_sweep_exiting_another_code_still_fails():
    queue = Queue(row(1, SWEEP), codes=[3])

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "failed"}
    assert rows_by_number(queue)[1]["reason"] == "its launcher exited 3"
    assert queue.state["ended"] == "halted"


def change_launches(queue: Queue) -> list[list[str]]:
    return [argv for argv in queue.processes.launched
            if argv[0].endswith("/launchers/chain-change/launcher.sh")]


def test_a_hand_off_refused_as_already_walking_waits_and_holds_the_queue():
    queue = Queue(row(1, CHANGE), codes=[chain.EXIT_ALREADY_WALKING])

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "waiting"}
    assert rows_by_number(queue)[1]["reason"] == REFUSED_AS_WALKING
    assert queue.state["pending"] == {}
    assert queue.state["waiting_on_walk"] == WALK
    assert queue.state["ended"] == WAITING_ON_A_WALK


def test_a_hand_off_exiting_another_code_still_fails():
    queue = Queue(row(1, CHANGE), codes=[3])

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "failed"}
    assert rows_by_number(queue)[1]["reason"] == "its launcher exited 3"
    assert queue.state["ended"] == "halted"


def test_a_hand_off_waits_while_a_sweep_row_runs():
    """tracker17's shape: the sweep row is walking, so the hand-off behind it is not launched."""
    queue = Queue(row(1, SWEEP), row(2, CHANGE))

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "launched", 2: "waiting"}
    assert change_launches(queue) == []
    assert queue.state["ended"] is None


def test_a_start_relaunches_a_held_hand_off():
    queue = Queue(row(1, CHANGE), codes=[chain.EXIT_ALREADY_WALKING])
    queue.start(product_path=PRODUCT)
    assert queue.state["ended"] == WAITING_ON_A_WALK

    queue.start(product_path=PRODUCT)

    assert len(change_launches(queue)) == 2
    assert queue.statuses() == {1: "handed-off"}


def test_exit_four_on_a_skill_row_still_fails():
    queue = Queue(row(1, CLOSE), codes=[4])

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "failed"}
    assert rows_by_number(queue)[1]["reason"] == "its launcher exited 4"
    assert queue.state["ended"] == "halted"


def test_a_start_resumes_a_waiting_queue_and_relaunches_the_sweep():
    queue = Queue(row(1, SWEEP), row(2, PICK, after="1"), codes=[chain.EXIT_ALREADY_WALKING])
    queue.start(product_path=PRODUCT)
    assert queue.state["ended"] == WAITING_ON_A_WALK

    queue.start(product_path=PRODUCT)

    assert queue.state["waiting_on_walk"] == "" and queue.state["ended"] is None
    assert len(chain_launches(queue)) == 2 and queue.statuses()[1] == "launched"
    queue.advance(1, "settled")
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_a_start_lets_a_held_pick_check_the_companions_again():
    queue = a_pick_over_a_live_companion()
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    assert queue.state["ended"] == WAITING_ON_A_WALK
    a_walk_is_in_flight(queue, ended="settled")
    queue.files.files.pop(COMPANION)

    queue.start(product_path=PRODUCT)

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]
    assert [entry["move"] for entry in queue.state["rows"]] == [PICK]


def test_the_hand_off_launches_when_the_sweep_before_it_lands():
    """tracker17's shape. The chain saves `ended` before it runs its end hook, so the sweep row's
    own advance already finds its walk ended."""
    queue = Queue(row(1, SWEEP), row(2, CHANGE))
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    a_walk_is_in_flight(queue, ended="settled")

    queue.advance(1, "settled")

    assert queue.statuses() == {1: "landed", 2: "handed-off"}
    assert len(change_launches(queue)) == 1
    assert queue.state["waiting_on_walk"] == ""
    assert queue.state["ended"] == "handed-off"


def held_sweep_after_a_close() -> Queue:
    """The sweep row waits behind the close and is refused as walking once the close lands, not at
    the start, where one row runs at a time."""
    queue = Queue(row(1, CLOSE), row(2, SWEEP), codes=[0, chain.EXIT_ALREADY_WALKING])
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    assert queue.statuses() == {1: "launched", 2: "waiting"}
    queue.close_station()
    return queue


def test_a_sweep_row_refused_after_a_close_relaunches_when_the_walk_ends():
    queue = held_sweep_after_a_close()
    queue.advance(1)
    assert queue.statuses() == {1: "landed", 2: "waiting"}
    assert queue.state["ended"] == WAITING_ON_A_WALK
    a_walk_is_in_flight(queue, ended="settled")

    queue.wake()

    assert len(chain_launches(queue)) == 2
    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert queue.state["waiting_on_walk"] == ""


def test_a_walk_still_live_at_a_rows_end_keeps_the_hold():
    queue = held_sweep_after_a_close()

    queue.advance(1)

    assert len(chain_launches(queue)) == 1
    assert queue.statuses() == {1: "landed", 2: "waiting"}
    assert queue.state["ended"] == WAITING_ON_A_WALK


def test_a_held_pick_checks_the_companions_again_when_the_walk_has_ended():
    queue = a_pick_over_a_live_companion(row(1, CLOSE), row(2, PICK))
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    assert queue.state["waiting_on_walk"] == WALK
    a_walk_is_in_flight(queue, ended="settled")
    queue.close_station()

    queue.advance(1)

    assert [entry["move"] for entry in queue.state["rows"]] == [CLOSE, PICK, SWEEP]
    assert len(chain_launches(queue)) == 1
    assert queue.state["waiting_on_walk"] == ""


def test_a_failed_row_outranks_the_wait():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), codes=[3, chain.EXIT_ALREADY_WALKING])

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "failed", 2: "waiting"}
    assert queue.state["ended"] == "halted"


def test_a_stop_outranks_the_wait():
    queue = a_pick_over_a_live_companion(row(1, CLOSE), row(2, PICK))
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    assert queue.state["waiting_on_walk"] == WALK and queue.state["ended"] is None
    queue.edit_state(lambda state: state.update(stop_requested=True))
    queue.close_station()

    queue.advance(1)

    assert queue.state["ended"] == "stopped"


def test_a_state_without_the_hold_loads():
    queue = Queue(row(1, CLOSE))
    queue.start(product_path=PRODUCT)
    queue.edit_state(lambda state: state.pop("waiting_on_walk"))

    loaded = queue.engine().store.load()

    assert loaded.waiting_on_walk == ""
    assert bi.BuildIdea._held(loaded) is False


# --- the queue watches the walk it ended on, and wakes when it ends (CP-542 to CP-544) ---------------


def held_pick_waiting(**kwargs) -> Queue:
    """CP-523's held pick with nothing of the queue's own in flight: the queue ends waiting."""
    queue = a_pick_over_a_live_companion(**kwargs)
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    assert queue.state["ended"] == WAITING_ON_A_WALK
    return queue


def held_sweep_waiting(*, move: str = SWEEP, watcher: FakeWatcher | None = None) -> Queue:
    """A sweep row, or a row that walks the next change, refused with exit 4; the queue ends
    waiting on the walk."""
    queue = Queue(row(1, move), codes=[chain.EXIT_ALREADY_WALKING], watcher=watcher)
    a_walk_is_in_flight(queue)
    queue.start(product_path=PRODUCT)
    assert queue.state["ended"] == WAITING_ON_A_WALK
    return queue


def test_a_queue_ending_on_a_walk_starts_one_watcher():
    queue = held_pick_waiting()

    assert queue.watcher.started == [{"argv": WATCH_ARGV, "log": WATCH_LOG}]
    assert queue.state["walk_watched"] is True


def test_no_watcher_starts_while_a_run_is_in_flight():
    queue = Queue(row(1, SWEEP), row(2, CHANGE), codes=[0, chain.EXIT_ALREADY_WALKING])

    queue.start(product_path=PRODUCT)

    assert queue.state["ended"] is None
    assert queue.watcher.started == []


def test_a_halted_queue_starts_no_watcher():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), codes=[3, chain.EXIT_ALREADY_WALKING])

    queue.start(product_path=PRODUCT)

    assert queue.state["ended"] == "halted"
    assert queue.watcher.started == []


def test_a_stopped_queue_starts_no_watcher():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), codes=[0, chain.EXIT_ALREADY_WALKING])
    queue.start(product_path=PRODUCT)
    queue.edit_state(lambda state: state.update(stop_requested=True))
    queue.close_station()

    queue.advance(1)

    assert queue.state["ended"] == "stopped"
    assert queue.watcher.started == []


def test_the_waiting_end_says_the_queue_continues_by_itself():
    queue = held_pick_waiting()

    first_line = queue.notifier.messages[-1].splitlines()[0]

    assert first_line == WAITING_END
    assert WALK in first_line and RESUME in first_line


def test_a_watcher_that_cannot_start_leaves_the_resume_message():
    queue = held_sweep_waiting(watcher=FakeWatcher(starts=False))

    assert queue.notifier.messages[-1].splitlines()[0] == UNWATCHED_END
    assert queue.state["walk_watched"] is False


def test_wake_after_the_walk_ends_relaunches_the_held_sweep_row():
    queue = held_sweep_waiting()
    a_walk_is_in_flight(queue, ended="settled")

    result = queue.wake()

    assert result.acted is True
    assert len(chain_launches(queue)) == 2
    assert queue.statuses() == {1: "launched"}
    assert queue.state["waiting_on_walk"] == "" and queue.state["walk_watched"] is False


def test_wake_after_the_walk_ends_relaunches_the_held_hand_off():
    queue = held_sweep_waiting(move=CHANGE)
    a_walk_is_in_flight(queue, ended="settled")

    queue.wake()

    assert len(change_launches(queue)) == 2
    assert queue.statuses() == {1: "handed-off"}
    assert queue.state["ended"] == "handed-off"


def test_wake_lets_a_held_pick_check_the_companions_again():
    queue = held_pick_waiting()
    a_walk_is_in_flight(queue, ended="settled")
    queue.files.files.pop(COMPANION)

    queue.wake()

    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


def test_wake_sends_the_continuing_message():
    queue = held_sweep_waiting()
    a_walk_is_in_flight(queue, ended="settled")
    before = len(queue.notifier.messages)

    queue.wake()

    sent = queue.notifier.messages[before:]
    assert sent[0] == CONTINUING
    assert "launched 1." in sent[1]


def test_wake_does_nothing_while_the_walk_is_live():
    queue = held_sweep_waiting()

    result = queue.wake()

    assert result.acted is False
    assert len(chain_launches(queue)) == 1
    assert queue.state["ended"] == WAITING_ON_A_WALK


def test_wake_does_nothing_after_the_owners_stop():
    queue = held_sweep_waiting()
    queue.stop()
    a_walk_is_in_flight(queue, ended="settled")

    result = queue.wake()

    assert result.acted is False
    assert len(chain_launches(queue)) == 1


def test_wake_does_nothing_for_another_queue():
    queue = held_sweep_waiting()
    a_walk_is_in_flight(queue, ended="settled")

    result = queue.wake("another-queue")

    assert result.acted is False
    assert len(chain_launches(queue)) == 1
    assert queue.state["ended"] == WAITING_ON_A_WALK


def test_wake_does_nothing_once_a_start_has_resumed_the_queue():
    queue = held_sweep_waiting()
    a_walk_is_in_flight(queue, ended="settled")
    queue.start(product_path=PRODUCT)
    assert len(chain_launches(queue)) == 2

    result = queue.wake()

    assert result.acted is False
    assert len(chain_launches(queue)) == 2


def test_a_second_wake_of_the_same_end_is_a_no_op():
    queue = held_sweep_waiting()
    a_walk_is_in_flight(queue, ended="settled")

    first, second = queue.wake(), queue.wake()

    assert (first.acted, second.acted) == (True, False)
    assert len(chain_launches(queue)) == 2


def test_a_stopped_walk_leaves_the_queue_waiting_and_says_so():
    queue = held_sweep_waiting()
    a_walk_is_in_flight(queue, ended="stopped")

    result = queue.wake()

    assert result.acted is False
    assert queue.state["ended"] == WAITING_ON_A_WALK
    assert len(chain_launches(queue)) == 1
    assert queue.notifier.messages[-1] == WALK_STOPPED


def test_wait_on_walk_sleeps_until_the_walk_ends_then_wakes():
    queue = held_sweep_waiting()
    queue.watcher.on_sleep = (
        lambda call: a_walk_is_in_flight(queue, ended="settled") if call == 2 else None)

    result = queue.wait_on_walk()

    assert result.acted is True
    assert queue.watcher.sleeps == [bi.WALK_POLL_SECONDS, bi.WALK_POLL_SECONDS]
    assert len(chain_launches(queue)) == 2


def test_wait_on_walk_returns_when_the_queue_was_resumed_meanwhile():
    queue = held_sweep_waiting()
    queue.watcher.on_sleep = lambda call: queue.start(product_path=PRODUCT)

    result = queue.wait_on_walk()

    assert result.acted is False
    assert queue.watcher.sleeps == [bi.WALK_POLL_SECONDS]


def test_wait_on_walk_returns_when_the_owner_stops_meanwhile():
    queue = held_sweep_waiting()
    queue.watcher.on_sleep = lambda call: queue.stop()

    result = queue.wait_on_walk()

    assert result.acted is False
    assert queue.watcher.sleeps == [bi.WALK_POLL_SECONDS]


def test_a_state_without_the_watch_flag_loads():
    queue = Queue(row(1, CLOSE))
    queue.start(product_path=PRODUCT)
    queue.edit_state(lambda state: state.pop("walk_watched"))

    loaded = queue.engine().store.load()

    assert loaded.walk_watched is False


# --- the real watcher and `--wait-on-walk` (CP-542) ----------------------------------------------


def test_the_watcher_detaches_a_process_that_writes_to_the_log(tmp_path):
    log = tmp_path / "not-yet-made" / "build-idea.log"

    program = ("import os, sys; "
               "print(f'session={os.getsid(0)} pid={os.getpid()}', flush=True); "
               "print(f'stdin={sys.stdin.read()!r}', flush=True); "
               "print('the-watch-ran', file=sys.stderr)")
    started = bi.WalkWatcher().start([sys.executable, "-c", program], str(log))

    assert started is True
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline and "the-watch-ran" not in (
            log.read_text() if log.exists() else ""):
        time.sleep(0.05)
    output = log.read_text()
    assert "the-watch-ran" in output
    assert "stdin=''" in output
    identity = re.search(r"session=(\d+) pid=(\d+)", output)
    assert identity is not None and identity[1] == identity[2]
    assert int(identity[1]) != os.getsid(0)


def test_the_watcher_reports_a_command_it_cannot_start(tmp_path):
    started = bi.WalkWatcher().start([str(tmp_path / "no-such-executable")],
                                     str(tmp_path / "build-idea.log"))

    assert started is False


def test_wait_on_walk_is_exclusive_with_the_other_modes(capsys):
    code = bi.main(["--wait-on-walk", "/s", "queue-1", "--advance", "/s", "1", "completed"])

    assert code == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_wait_on_walk_on_a_queue_that_has_ended_returns_at_once(tmp_path, capsys):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"queue_id": "queue-1", "ended": "done",
                                 "schema_version": bi.QUEUE_SCHEMA}))

    code = bi.main(["--wait-on-walk", str(state), "queue-1"])

    assert code == 0
    assert "acted=False" in capsys.readouterr().out


# --- the code-integrity review: the spec's sentences no case above pins --------------------------


def test_a_failed_sweep_row_does_not_hold_the_pick():
    """CP-522 waits on a sweep row that is `waiting` or `launched` — one that can still land. A
    failed row never will, so the pick gets a sweep row of its own rather than going blocked."""
    queue = Queue(row(1, SWEEP), row(2, PICK), codes=[3])
    queue.files.files[COMPANION] = "- [ ] an item the cut raised"

    queue.start(product_path=PRODUCT)

    rows = rows_by_number(queue)
    assert rows[1]["status"] == "failed"
    assert rows[2]["status"] == "waiting" and rows[2]["after"] == [3]
    assert rows[3]["move"] == SWEEP and rows[3]["status"] == "launched"


def test_a_pick_held_for_a_walk_launches_nothing_more_and_ends_once_its_run_lands():
    """CP-523: the hold stops every later launch, a ready row included, and the queue ends
    waiting-on-a-walk only once no run of its own is in flight."""
    queue = a_pick_over_a_live_companion(row(1, CLOSE), row(2, PICK), row(3, CUT_ROUTE))
    a_walk_is_in_flight(queue)

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "launched", 2: "waiting", 3: "waiting"}
    assert queue.state["ended"] is None
    queue.close_station()

    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "waiting", 3: "waiting"}
    assert len(queue.processes.launched) == 1
    assert queue.state["ended"] == WAITING_ON_A_WALK


def test_the_wait_outranks_an_owners_act_owed():
    """CP-526 puts waiting-on-a-walk above every end a queue has today, `owner-owed` among them."""
    queue = Queue(row(1, OWNER, command=WALK_YOURSELF), row(2, SWEEP),
                  codes=[chain.EXIT_ALREADY_WALKING])

    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "end", 2: "waiting"}
    assert queue.state["ended"] == WAITING_ON_A_WALK


@pytest.mark.parametrize("entry", ["start", "advance"])
def test_an_immediately_started_watch_observes_the_waiting_queue(entry):
    """CP-542: a detached reader may run before its parent returns from watcher.start."""
    observed = []
    if entry == "start":
        queue = Queue(row(1, SWEEP), codes=[chain.EXIT_ALREADY_WALKING])
    else:
        queue = held_sweep_after_a_close()
    a_walk_is_in_flight(queue)
    queue.watcher.on_start = lambda: observed.append(queue.state)

    if entry == "start":
        queue.start(product_path=PRODUCT)
    else:
        queue.advance(1)

    assert len(observed) == 1
    assert observed[0]["ended"] == WAITING_ON_A_WALK
    assert observed[0]["waiting_on_walk"] == WALK
    assert observed[0]["pending"] == {}
    assert observed[0]["queue_id"] == "queue-1"


def test_wake_keeps_the_recorded_rows_when_the_report_changes():
    """Locked Answer 5: a watch continues the saved rows; only a start rereads the report."""
    queue = held_sweep_waiting(move=CHANGE)
    queue.files.files[report_path()] = next_moves(row(1, CLOSE))
    a_walk_is_in_flight(queue, ended="settled")

    queue.wake()

    assert len(change_launches(queue)) == 2
    assert queue.statuses() == {1: "handed-off"}
    assert queue.state["rows"][0]["move"] == CHANGE


def test_wait_on_walk_returns_when_another_queue_replaces_it():
    """CP-542: the old watch cannot continue a replacement queue."""
    queue = held_sweep_waiting()

    def replace_queue(call):
        assert call == 1, "the old watch must stop at the next poll"
        queue.edit_state(lambda state: state.update(queue_id="queue-2"))

    queue.watcher.on_sleep = replace_queue
    result = queue.wait_on_walk()

    assert result.acted is False
    assert queue.watcher.sleeps == [bi.WALK_POLL_SECONDS]
    assert len(chain_launches(queue)) == 1


def test_wake_without_a_queue_does_nothing():
    queue = Queue()

    result = queue.wake()

    assert result.acted is False
    assert queue.processes.launched == []
    assert queue.notifier.messages == []


def test_the_watcher_reports_a_log_folder_it_cannot_create(tmp_path):
    blocked = tmp_path / "file-in-the-way"
    blocked.write_text("not a folder")

    assert bi.WalkWatcher().start([sys.executable, "-c", "pass"],
                                  str(blocked / "watch.log")) is False


@pytest.mark.parametrize("failure", ["schema", "missing-walk-path"])
def test_wait_on_walk_reports_errors_through_the_saved_notifier(tmp_path, capsys,
                                                               notifier_log, failure):
    """Task 4: a refusal is exit 3; an unexpected failure is exit 5; both notify."""
    notifier, log = notifier_log
    state = tmp_path / "state.json"
    data = {"queue_id": "queue-1", "ended": WAITING_ON_A_WALK,
            "schema_version": bi.QUEUE_SCHEMA + 1, "waiting_on_walk": str(tmp_path / "walk"),
            "notifier": str(notifier)}
    if failure == "missing-walk-path":
        del data["waiting_on_walk"]
    state.write_text(json.dumps(data))

    code = bi.main(["--wait-on-walk", str(state), "queue-1"])

    assert code == (3 if failure == "schema" else 5)
    assert ("refused to continue" if failure == "schema" else "crashed watching") in log.read_text()
    error = capsys.readouterr().err
    assert error
    assert "Traceback" not in error


# --- the `readme-status` row ------------------------------------------------------------------
#
# The row follows each `close the reached station` row and settles on what the Content Editor's
# run reported, which reaches the queue through a receipt the watcher publishes, or on the
# product's tree when it never had a what-left file. The disk below is scripted: a receipt is
# written to the destination the row's launch named, the way the watcher would.

import tomllib  # noqa: E402

README_PROJECT_RULE = "readme-status"
WHAT_LEFT = f"{PRODUCT}/docs/what_left.md"
COMMIT_SENTENCE = "readme-status made commit `1a2b3c4d5` in `/x/product`."
NOTHING_SENTENCE = "readme-status found nothing to change and made no commit."
NOT_REPORTED = ("the run finished but readme-status neither made its commit nor found nothing "
                "to change")
RESULT_FILE = completion_shim.RESULT_FILE_VARIABLE
EXAMPLE_PROVIDER_FILE = Path(__file__).resolve().parents[2] / ".providers.toml.example"


def status_queue(*extra_rows: str, what_left: str | None = "# what left\n- a want\n",
                 start: bool = True, product_path: str = PRODUCT, **kwargs) -> Queue:
    """A close (row 1) and its `readme-status` row (row 2, After 1), started over a product that
    holds a what-left file unless `what_left` is `None`."""
    files = sealed_world(row(1, CLOSE), row(2, README_STATUS, after="1"), *extra_rows)
    if what_left is not None:
        files[WHAT_LEFT] = what_left
    queue = Queue(files=files, **kwargs)
    if start:
        queue.start(product_path=product_path)
    return queue


def entry_of(queue: Queue, number: int = 2) -> dict:
    return next(entry for entry in queue.state["rows"] if entry["number"] == number)


def land_the_close(queue: Queue) -> None:
    queue.close_station()
    queue.advance(1)


def receipt_message(queue: Queue, message: str | None, *, number: int = 2,
                    raw: str | None = None) -> None:
    """What the watcher would have published at the destination the row's launch named."""
    destination = entry_of(queue, number)["receipt"]
    queue.files.files[destination] = (
        raw if raw is not None else json.dumps({"last_message": message}))


def a_status_row_that_finished_with(message: str | None, outcome: str = "completed",
                                    **kwargs) -> Queue:
    queue = status_queue(**kwargs)
    land_the_close(queue)
    if message is not None:
        receipt_message(queue, message)
    queue.advance(2, outcome)
    return queue


# Kind, listing and order -------------------------------------------------------------------


def test_a_readme_status_row_with_the_canonical_command_is_accepted():
    rows = validated(next_moves(row(1, CLOSE), row(2, README_STATUS, after="1")))

    assert [(r.number, r.move, r.after) for r in rows] == [
        (1, CLOSE, ()), (2, README_STATUS, (1,))]


def test_a_readme_status_row_with_a_wrong_command_is_refused_on_its_row():
    wrong = f"`{CORE}/launchers/skill/launcher.sh shukuba-retire {PROJECT}`"
    queue = Queue(row(1, CLOSE), row(2, README_STATUS, command=wrong, after="1"))

    queue.start()

    reason = queue.state["rows"][1]["reason"]
    assert queue.statuses() == {1: "launched", 2: "failed"}
    assert reason.startswith("its Command") and "is not what 'readme-status' runs" in reason
    assert f"{CORE}/launchers/skill/launcher.sh readme-status {PROJECT}" in reason
    assert [argv[1] for argv in queue.processes.launched] == ["shukuba-retire"]


def test_an_unknown_kind_is_still_refused():
    text = next_moves(row(1, CLOSE), "2 | reticulate the splines | owner | none | 1 | x")

    with pytest.raises(bi.QueueRefused, match="row 2: 'reticulate the splines' is not a kind"):
        validated(text)


def test_the_readme_status_kind_sits_immediately_after_the_close_kind_in_the_table():
    kinds = list(bi.KINDS)

    assert kinds.index(README_STATUS) == kinds.index(CLOSE) + 1


def test_the_readme_status_kind_is_a_content_editor_skill_row_with_its_own_landing_fact():
    kind = bi.KINDS[README_STATUS]

    assert (kind.disposition, kind.launcher, kind.arguments, kind.role) == (
        bi.Disposition.RUN_SKILL, "skill", (README_STATUS, "<project>"), "content-editor")
    assert kind.landed not in (bi.Landed.NONE, bi.KINDS[CLOSE].landed)
    assert README_STATUS not in bi._NEMAWASHI_KINDS


def test_dispositions_and_the_prompt_union_hold_the_new_kind():
    assert README_STATUS in DISPOSITIONS
    assert README_STATUS in [cells[0] for cells in _prompt_kind_table()]
    assert README_STATUS not in {cells[0] for cells in _prompt_kind_table(_NEMAWASHI_PROMPT)}
    assert bi.expected_argv(README_STATUS, core_dir=CORE, project=PROJECT) == [
        f"{CORE}/launchers/skill/launcher.sh", README_STATUS, PROJECT]


def test_the_start_message_lists_the_row():
    queue = status_queue()

    message = queue.notifier.messages[0]

    assert "1. close the reached station — after — — runs" in message
    assert "2. readme-status — after 1 — runs" in message


def test_describe_lists_the_row_with_its_launcher():
    queue = status_queue(start=False)

    plan = queue.describe()

    assert (f"2. readme-status — after 1 — {CORE}/launchers/skill/launcher.sh readme-status "
            f"{PROJECT}") in [bi._describe_line(planned) for planned in plan.rows]


# Ordering and seat ---------------------------------------------------------------------------


def test_the_row_is_not_launched_while_its_close_is_in_flight():
    queue = status_queue()

    assert queue.statuses() == {1: "launched", 2: "waiting"}
    assert len(queue.processes.launched) == 1


def test_the_row_launches_after_its_close_lands_on_the_content_editor_seat():
    queue = status_queue()

    land_the_close(queue)

    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert queue.processes.launched[-1] == bi.expected_argv(
        README_STATUS, core_dir=CORE, project=PROJECT)
    assert queue.processes.calls[-1]["env"]["INSTRUMENT_RUN_ROLE"] == "content-editor"


def test_a_failed_close_blocks_the_row_and_the_queue_ends_halted_on_the_close():
    queue = status_queue()

    queue.advance(1)

    assert queue.statuses() == {1: "failed", 2: "blocked"}
    assert len(queue.processes.launched) == 1
    assert queue.state["ended"] == "halted"
    assert "1. close the reached station failed" in queue.state["ended_reason"]
    assert queue.notifier.messages[-1].splitlines()[-1] == "blocked: 2. readme-status — waits on 1"


def test_a_blocked_close_blocks_the_row():
    queue = Queue(row(1, DROP), row(2, CLOSE, after="1"), row(3, README_STATUS, after="2"))

    queue.start()

    assert queue.statuses() == {1: "skipped", 2: "blocked", 3: "blocked"}
    assert queue.processes.calls == []


def test_every_named_after_row_must_land_before_the_row_starts():
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, README_STATUS, after="1, 2"))
    queue.start()

    land_the_close(queue)
    assert queue.statuses() == {1: "landed", 2: "launched", 3: "waiting"}

    queue.advance(2, "settled")
    assert queue.statuses() == {1: "landed", 2: "landed", 3: "launched"}


def test_a_repeated_completion_callback_neither_relaunches_nor_reorders_rows():
    queue = status_queue()
    land_the_close(queue)
    launched = list(queue.processes.launched)

    assert queue.advance(1).acted is False

    assert queue.processes.launched == launched
    assert queue.statuses() == {1: "landed", 2: "launched"}


# Landing -------------------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", ["completed", "produced_nothing"])
def test_the_commit_sentence_lands_the_row_for_both_finished_endings(outcome):
    queue = a_status_row_that_finished_with(COMMIT_SENTENCE + " It rewrote the status.", outcome)

    assert queue.statuses() == {1: "landed", 2: "landed"}
    assert queue.state["ended"] == "done"


@pytest.mark.parametrize("outcome", ["completed", "produced_nothing"])
def test_the_nothing_to_change_sentence_lands_the_row_for_both_finished_endings(outcome):
    queue = a_status_row_that_finished_with(NOTHING_SENTENCE + "\nThe README is current.", outcome)

    assert queue.statuses() == {1: "landed", 2: "landed"}


@pytest.mark.parametrize("receipt", [
    None,
    {"raw": ""},
    {"raw": "not json {"},
    {"raw": json.dumps({"last_message": None})},
    {"raw": json.dumps({"last_message": 7})},
    {"raw": json.dumps(["readme-status found nothing to change and made no commit."])},
])
def test_a_missing_empty_or_malformed_receipt_does_not_land_a_row_whose_file_exists(receipt):
    queue = status_queue()
    land_the_close(queue)
    if receipt is not None:
        receipt_message(queue, None, raw=receipt["raw"])

    queue.advance(2)

    assert queue.statuses() == {1: "landed", 2: "failed"}
    assert entry_of(queue)["reason"] == NOT_REPORTED


@pytest.mark.parametrize("message", [
    "Done. " + COMMIT_SENTENCE,
    "\n" + COMMIT_SENTENCE,
])
def test_a_commit_sentence_that_is_not_the_opening_does_not_land_the_row(message):
    queue = a_status_row_that_finished_with(message)

    assert queue.statuses() == {1: "landed", 2: "failed"}


@pytest.mark.parametrize("message", [
    "I checked both entries against `main`.\n\n" + NOTHING_SENTENCE,
    "I checked both entries.\n\n**" + NOTHING_SENTENCE + "**",
    "*" + NOTHING_SENTENCE + "*",
    "> " + NOTHING_SENTENCE,
    " " + NOTHING_SENTENCE,
    NOTHING_SENTENCE + " No entry in `/x/product/docs/what_left.md` is wholly built at `main`.",
])
def test_the_nothing_to_change_sentence_lands_the_row_as_the_opening_or_a_whole_line_anywhere(message):
    queue = a_status_row_that_finished_with(message)

    assert queue.statuses() == {1: "landed", 2: "landed"}


@pytest.mark.parametrize("message", [
    "I ran it. " + NOTHING_SENTENCE,
    "It said " + NOTHING_SENTENCE + " and stopped.",
    "**" + NOTHING_SENTENCE.replace("no commit.", "no commit**."),
    "I ran it.\n" + NOTHING_SENTENCE.capitalize(),
])
def test_the_nothing_to_change_sentence_inside_a_line_or_misquoted_does_not_land_the_row(message):
    queue = a_status_row_that_finished_with(message)

    assert queue.statuses() == {1: "landed", 2: "failed"}


@pytest.mark.parametrize("message", [
    "readme-status made commit `` in `/x/product`.",
    "readme-status made commit `1a2b3c4d5` in ``.",
    "readme-status made commit `1a2b3c4d5` in `/x/product`",
    "readme-status made commit 1a2b3c4d5 in /x/product.",
    "readme-status made commit `1a2b3c4d5`.",
])
def test_an_incomplete_commit_sentence_does_not_land_the_row(message):
    queue = a_status_row_that_finished_with(message)

    assert queue.statuses() == {1: "landed", 2: "failed"}
    assert entry_of(queue)["reason"] == NOT_REPORTED


@pytest.mark.parametrize("message", [
    COMMIT_SENTENCE.capitalize(), NOTHING_SENTENCE.upper(),
    NOTHING_SENTENCE.replace("nothing to change", "nothing  to change"),
    "readme-status found nothing to change and made no commit",
])
def test_the_receipt_message_is_compared_verbatim(message):
    queue = a_status_row_that_finished_with(message)

    assert queue.statuses() == {1: "landed", 2: "failed"}


@pytest.mark.parametrize("outcome", ["completed", "produced_nothing"])
def test_a_product_without_a_what_left_file_lands_the_row_for_both_finished_endings(outcome):
    queue = a_status_row_that_finished_with(None, outcome, what_left=None)

    assert queue.statuses() == {1: "landed", 2: "landed"}
    assert queue.files.files.get(entry_of(queue)["receipt"]) is None


def test_a_close_and_a_readme_status_row_end_done_when_both_land_including_a_product_with_no_what_left_file():
    queue = a_status_row_that_finished_with(None, what_left=None)

    assert queue.state["ended"] == "done"
    assert queue.state["ended_reason"] == "done — every row ran or was named"
    assert queue.notifier.messages[-1] == (
        "instance · proj · build-idea — done — every row ran or was named")


@pytest.mark.parametrize("what_left", ["", "{ not what-left", "# what left\n"])
def test_an_empty_or_malformed_what_left_file_does_not_count_as_absent(what_left):
    queue = a_status_row_that_finished_with(None, what_left=what_left)

    assert queue.statuses() == {1: "landed", 2: "failed"}


@pytest.mark.parametrize("recorded", ["products/tools", "/abs/product", "products/a/b/c"])
def test_absence_is_resolved_for_relative_absolute_and_nested_product_paths(recorded):
    directory = os.path.normpath(os.path.join(INSTANCE, recorded))
    absent = status_queue(what_left=None, product_path=recorded)
    land_the_close(absent)
    absent.advance(2)
    present = status_queue(what_left=None, product_path=recorded)
    present.files.files[f"{directory}/docs/what_left.md"] = "# what left\n"
    land_the_close(present)
    present.advance(2)

    assert absent.statuses() == {1: "landed", 2: "landed"}
    assert present.statuses() == {1: "landed", 2: "failed"}


def _a_legacy_state_with_the_card(card_line: str | None, *, what_left_at: str | None = None):
    """A queue whose state holds no product path, as one written before it did, over a card
    carrying `card_line`; the what-left file sits at `what_left_at` when that is given."""
    card = FULL_CARD + (f"{card_line}\n" if card_line is not None else "")
    queue = status_queue(what_left=None, product_path="")
    queue.files.files[CARD] = card
    if what_left_at:
        queue.files.files[what_left_at] = "# what left\n"
    land_the_close(queue)
    queue.advance(2)
    return queue


@pytest.mark.parametrize("line, product", [
    ("**Product path:** products/tools   <!-- a comment -->", f"{INSTANCE}/products/tools"),
    ("**Product path:** /abs/product", "/abs/product"),
])
def test_an_empty_legacy_state_product_path_is_resolved_from_a_valid_project_card(line, product):
    gone = _a_legacy_state_with_the_card(line)
    kept = _a_legacy_state_with_the_card(line, what_left_at=f"{product}/docs/what_left.md")

    assert gone.statuses() == {1: "landed", 2: "landed"}
    assert kept.statuses() == {1: "landed", 2: "failed"}


@pytest.mark.parametrize("line", [None, "**Product path:**", "**Product path:** ../outside"])
def test_an_unresolved_product_card_never_claims_the_file_is_absent(line):
    queue = _a_legacy_state_with_the_card(line)

    assert queue.statuses() == {1: "landed", 2: "failed"}
    assert entry_of(queue)["reason"] == NOT_REPORTED


def test_a_missing_card_never_claims_the_file_is_absent():
    queue = status_queue(what_left=None, product_path="")
    queue.files.files.pop(CARD)
    land_the_close(queue)

    queue.advance(2)

    assert queue.statuses() == {1: "landed", 2: "failed"}


def test_an_existing_file_with_a_readme_that_has_no_status_line_fails_with_the_exact_reason_and_end_line():
    queue = a_status_row_that_finished_with(
        "readme-status refused: the README has no `## Status` line.")

    assert queue.state["ended"] == "halted"
    assert queue.state["ended_reason"] == f"halted — 2. readme-status failed: {NOT_REPORTED}"
    assert queue.notifier.messages[-1].splitlines()[0] == (
        f"instance · proj · build-idea — halted — 2. readme-status failed: {NOT_REPORTED}")


def test_a_commit_builder_refusal_fails_the_row_with_the_exact_reason():
    queue = a_status_row_that_finished_with(
        "commit_builder refused: the staged set was not declared.")

    assert entry_of(queue)["status"] == "failed"
    assert entry_of(queue)["reason"] == NOT_REPORTED


def test_an_unrecognised_final_message_fails_the_row_with_the_exact_reason():
    queue = a_status_row_that_finished_with("All done, the README looks good now.")

    assert entry_of(queue)["reason"] == NOT_REPORTED


def test_an_independent_next_change_row_after_the_close_still_hands_off_when_the_row_fails():
    queue = status_queue(row(3, CHANGE, after="1"))
    land_the_close(queue)

    queue.advance(2)

    assert queue.statuses() == {1: "landed", 2: "failed", 3: "handed-off"}
    assert queue.state["ended"] == "halted"
    assert queue.state["ended_reason"].startswith("halted — 2. readme-status failed:")


def test_a_row_depending_on_a_failed_readme_status_row_is_blocked_and_the_queue_waits_for_independent_work_before_its_halted_summary():
    queue = status_queue(row(3, PICK, after="2"), row(4, SWEEP, after="1"))
    land_the_close(queue)

    queue.advance(2)
    assert queue.statuses() == {1: "landed", 2: "failed", 3: "blocked", 4: "launched"}
    assert queue.state["ended"] is None

    queue.advance(4, "settled")
    assert queue.state["ended"] == "halted"
    assert queue.notifier.messages[-1].splitlines()[0] == (
        f"instance · proj · build-idea — halted — 2. readme-status failed: {NOT_REPORTED}")


@pytest.mark.parametrize("end", ["timeout", "failed", "stopped", "vanished"])
@pytest.mark.parametrize("scenario", ["file absent", "success receipt"])
def test_every_non_finished_ending_fails_with_the_run_ended_reason(end, scenario):
    queue = status_queue(what_left=None if scenario == "file absent" else "# what left\n")
    land_the_close(queue)
    if scenario == "success receipt":
        receipt_message(queue, COMMIT_SENTENCE)

    queue.advance(2, end)

    assert queue.statuses() == {1: "landed", 2: "failed"}
    assert entry_of(queue)["reason"] == f"the run ended {end}"


def test_a_resume_does_not_land_a_row_that_never_launched_or_never_finished_because_a_file_is_absent():
    never_launched = status_queue(what_left=None)
    never_launched.stop()
    never_launched.start(product_path=PRODUCT)
    never_finished = status_queue(what_left=None)
    land_the_close(never_finished)
    never_finished.stop()
    never_finished.start(product_path=PRODUCT)

    assert entry_of(never_launched)["status"] == "waiting"
    assert entry_of(never_finished)["status"] == "launched"
    assert [argv[1] for argv in never_finished.processes.launched].count(README_STATUS) == 2


def test_a_relaunch_clears_the_old_ending_and_receipt_evidence():
    queue = a_status_row_that_finished_with("All done, the README looks good now.")
    first = entry_of(queue)
    assert first["ending"] == "completed" and first["status"] == "failed"

    queue.start(product_path=PRODUCT)

    second = entry_of(queue)
    assert second["status"] == "launched"
    assert "ending" not in second
    assert second["receipt"] != first["receipt"]
    assert second["receipt"] not in queue.files.files


# Receipts per attempt --------------------------------------------------------------------------


def test_each_attempt_and_each_row_gets_a_distinct_receipt_destination():
    queue = status_queue(row(3, README_STATUS, after="1"))
    land_the_close(queue)
    queue.advance(2)
    queue.advance(3)
    queue.start(product_path=PRODUCT)
    queue.advance(2)

    launches = [call["env"][RESULT_FILE] for call in queue.processes.calls
                if call["argv"][1] == README_STATUS]
    assert len(launches) == 4 and len(set(launches)) == 4
    assert all(os.path.isabs(path) for path in launches)
    assert entry_of(queue, 2)["receipt"] == launches[2]


def test_the_receipt_destination_is_saved_in_the_row_before_the_launcher_runs():
    seen = []

    def on_run(argv):
        if argv[1:2] == [README_STATUS]:
            seen.append(json.loads(queue.files.files[STATE])["rows"][1].get("receipt"))

    queue = status_queue(on_run=on_run)
    land_the_close(queue)

    assert seen == [queue.processes.calls[-1]["env"][RESULT_FILE]]


def test_a_late_first_attempt_receipt_cannot_satisfy_a_retry():
    queue = a_status_row_that_finished_with("All done, the README looks good now.")
    first = entry_of(queue)["receipt"]
    queue.start(product_path=PRODUCT)
    queue.files.files[first] = json.dumps({"last_message": COMMIT_SENTENCE})

    queue.advance(2)

    assert queue.statuses() == {1: "landed", 2: "failed"}
    assert entry_of(queue)["reason"] == NOT_REPORTED


def test_a_restart_retains_valid_finished_evidence():
    queue = status_queue(row(3, SWEEP, after="2"))
    land_the_close(queue)
    receipt_message(queue, COMMIT_SENTENCE)

    def delivered_but_not_recorded(state):
        state["pending"].pop("2")
        state["rows"][1]["ending"] = "completed"

    queue.edit_state(delivered_but_not_recorded)
    queue.start(product_path=PRODUCT)

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "launched"}
    assert [argv[1] for argv in queue.processes.launched].count(README_STATUS) == 1


def test_inherited_receipt_destinations_are_cleared_for_every_other_row():
    inherited = {"PATH": "/usr/bin", RESULT_FILE: "/old/receipt.json"}
    queue = Queue(row(1, CLOSE), row(2, SWEEP), row(3, PICK, after="1"),
                  row(4, CHANGE, after="1"), environ=inherited)
    queue.start()
    queue.close_station()
    queue.advance(1)
    queue.advance(2, "settled")
    queue.pick_seed()
    queue.advance(3)

    assert len(queue.processes.calls) == 4
    assert all(RESULT_FILE not in call["env"] for call in queue.processes.calls)


def test_a_readme_status_launch_replaces_an_inherited_destination_with_its_own():
    queue = status_queue(environ={"PATH": "/usr/bin", RESULT_FILE: "/old/receipt.json"})
    land_the_close(queue)

    assert queue.processes.calls[-1]["env"][RESULT_FILE] == entry_of(queue)["receipt"]
    assert entry_of(queue)["receipt"] != "/old/receipt.json"


def test_the_checkout_dirty_failure_still_overrides_success_evidence():
    queue = status_queue(checkout=FakeCheckout([], [], [], ["?? junk.md"]))
    land_the_close(queue)
    receipt_message(queue, COMMIT_SENTENCE)

    queue.advance(2)

    assert queue.statuses() == {1: "landed", 2: "failed"}
    assert queue.state["checkout_dirty"] is True


# Provider (CP-553, CP-554) ---------------------------------------------------------------------

def lacking_status() -> str:
    """The delivered provider file without the row's entry — built when a test asks, since the
    delivered file is what carries the entry."""
    return edited_text({f"build-idea.{README_STATUS}": None})


def test_an_unforced_start_with_a_provider_file_lacking_the_entry_is_refused_naming_it():
    queue = status_queue(start=False, provider_port=ProviderText(lacking_status()))

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    assert "build-idea.readme-status is missing" in str(refused.value)
    assert queue.processes.calls == [] and STATE not in queue.files.files


def test_an_unforced_describe_with_a_provider_file_lacking_the_entry_is_refused_the_same_way():
    queue = status_queue(start=False, provider_port=ProviderText(lacking_status()))

    with pytest.raises(bi.QueueRefused) as refused:
        queue.describe()

    assert "build-idea.readme-status is missing" in str(refused.value)


def test_a_forced_start_reads_no_file_for_the_row_and_runs_on_the_forced_provider():
    port = ProviderText(None)
    queue = status_queue(start=False, provider_port=port)
    queue.start(forced_provider="gemini", product_path=PRODUCT)

    land_the_close(queue)

    assert queue.processes.calls[-1]["env"][PROVIDER] == "gemini"
    assert port.reads == 0


def test_a_codex_entry_routes_the_row_to_codex():
    port = ProviderText(edited_text({f"build-idea.{README_STATUS}": "codex"}))
    queue = status_queue(provider_port=port)

    land_the_close(queue)

    assert queue.processes.calls[-1]["env"][PROVIDER] == "codex"
    assert queue.processes.calls[0]["env"][PROVIDER] == "claude"


def test_every_skill_row_is_preflighted_even_on_a_report_without_a_status_row():
    queue = Queue(row(1, CLOSE), provider_port=ProviderText(lacking_status()))

    with pytest.raises(bi.QueueRefused, match="build-idea.readme-status is missing"):
        queue.start()


def test_the_example_provider_file_carries_the_readme_status_entry():
    table = tomllib.loads(EXAMPLE_PROVIDER_FILE.read_text(encoding="utf-8"))
    queue = status_queue(start=False, provider_port=ProviderText(DELIVERED_TEXT))

    queue.start(product_path=PRODUCT)

    assert table["build-idea"][README_STATUS] == "claude"
    assert queue.state["rows"][1]["move"] == README_STATUS


# Nemawashi (CP-557) ----------------------------------------------------------------------------


def test_a_nemawashi_refine_report_row_readme_status_is_refused_as_not_a_nemawashi_next_move():
    queue = retired_queue(row(1, README_STATUS))

    with pytest.raises(bi.QueueRefused, match="row 1: 'readme-status' is not a nemawashi next move"):
        queue.describe()


def test_a_station_report_without_a_status_row_is_not_augmented():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))

    queue.start()

    assert [entry["move"] for entry in queue.state["rows"]] == [CLOSE, PICK]
    assert "receipt" not in queue.state["rows"][0]


# The close names its station (2026-10-13) ---------------------------------------------------

CLOSE_LAUNCHER = f"{CORE}/launchers/skill/launcher.sh"


def close_naming(stem: str) -> str:
    return f"`{CLOSE_LAUNCHER} shukuba-retire {PROJECT} {stem}`"


def test_a_close_row_naming_the_station_by_its_dated_stem_is_accepted():
    rows = bi.parse_queue(next_moves(row(1, CLOSE, command=close_naming(STEM))))

    assert bi.validate(rows, core_dir=CORE, instance_root=INSTANCE, project=PROJECT,
                       card=FULL_CARD) == {}


def test_a_close_row_written_before_the_station_was_named_is_still_accepted():
    rows = bi.parse_queue(next_moves(row(1, CLOSE,
                                         command=f"`{CLOSE_LAUNCHER} shukuba-retire {PROJECT}`")))

    assert bi.validate(rows, core_dir=CORE, instance_root=INSTANCE, project=PROJECT,
                       card=FULL_CARD) == {}


@pytest.mark.parametrize("named", ["a-station", f"trail/{STEM}"])
def test_a_close_row_naming_something_other_than_a_dated_stem_is_refused_showing_the_form(named):
    rows = bi.parse_queue(next_moves(row(1, CLOSE, command=close_naming(named))))

    refused = bi.validate(rows, core_dir=CORE, instance_root=INSTANCE, project=PROJECT,
                          card=FULL_CARD)

    assert list(refused) == [1]
    assert f"names {named!r} where the station's dated stem goes" in refused[1]
    assert f"shukuba-retire {PROJECT} <YYYY-MM-DD>_<slug>" in refused[1]


def test_a_close_row_with_a_word_after_the_station_is_refused():
    rows = bi.parse_queue(next_moves(row(1, CLOSE, command=close_naming(f"{STEM} extra"))))

    refused = bi.validate(rows, core_dir=CORE, instance_root=INSTANCE, project=PROJECT,
                          card=FULL_CARD)

    assert list(refused) == [1] and "is not what 'close the reached station' runs" in refused[1]


def test_a_close_row_naming_its_station_with_md_is_repaired_not_refused():
    """The engine fixes what it can: the `.md` suffix is the file name, and the stem is plain."""
    queue = Queue(row(1, CLOSE, command=close_naming(f"{STEM}.md")))

    queue.start()

    assert queue.processes.launched[0] == [CLOSE_LAUNCHER, "shukuba-retire", PROJECT, STEM]


def test_the_close_is_launched_naming_the_station_the_queue_found_open():
    queue = Queue(row(1, CLOSE))

    queue.start()

    assert queue.processes.launched[0] == [CLOSE_LAUNCHER, "shukuba-retire", PROJECT, STEM]


def test_the_close_is_launched_naming_the_station_its_row_names():
    queue = Queue(row(1, CLOSE, command=close_naming("2026-09-17_another-station")))

    queue.start()

    assert queue.processes.launched[0] == [
        CLOSE_LAUNCHER, "shukuba-retire", PROJECT, "2026-09-17_another-station"]


def test_two_stations_at_the_root_launch_the_close_naming_none():
    """The queue does not pick one of two: the skill's resolve refuses a root holding two."""
    files = sealed_world(row(1, CLOSE))
    files[f"{JOURNEY}/shukuba/2026-09-19_a-second-station.md"] = "a second station"
    queue = Queue(files=files)

    queue.start()

    assert queue.processes.launched[0] == [CLOSE_LAUNCHER, "shukuba-retire", PROJECT]


def test_a_close_lands_when_the_station_it_named_has_moved_to_trail():
    queue = Queue(row(1, CLOSE, command=close_naming(STEM)))
    queue.start()
    queue.close_station()

    queue.advance(1)

    assert queue.statuses() == {1: "landed"}


def test_the_close_lands_on_the_station_it_was_launched_naming_not_on_the_record():
    """Two stations at the start record none, so only the launched argv can say which one the
    close was for — the reviewer's reproduction of a named close that could never land."""
    files = sealed_world(row(1, CLOSE, command=close_naming(STEM)))
    files[f"{JOURNEY}/shukuba/2026-09-19_a-second-station.md"] = "a second station"
    queue = Queue(files=files)
    queue.start()
    assert queue.state["station"] == ""
    queue.close_station()

    queue.advance(1)

    assert queue.statuses() == {1: "landed"}


def test_a_close_naming_a_station_that_was_never_open_does_not_land():
    """The skill refuses a station not at the root and moves nothing; a check reading only "is it
    gone from the root" would count that refusal as the close."""
    queue = Queue(row(1, CLOSE, command=close_naming("2026-09-17_never-opened")))
    queue.start()

    queue.advance(1)

    assert queue.statuses() == {1: "failed"}
    assert "has not moved from the shukuba root to trail/" in queue.state["rows"][0]["reason"]


def test_a_station_gone_from_the_root_but_not_to_trail_has_not_been_closed():
    queue = Queue(row(1, CLOSE))
    queue.start()
    queue.files.files[f"{JOURNEY}/shukuba/parked/{STATION}"] = queue.files.files.pop(STATION_PATH)

    queue.advance(1)

    assert queue.statuses() == {1: "failed"}


def test_two_stations_at_the_root_and_a_named_close_fail_the_row():
    """The skill refuses a root holding two, named or not, so nothing moves and the row fails."""
    files = sealed_world(row(1, CLOSE, command=close_naming(STEM)))
    files[f"{JOURNEY}/shukuba/2026-09-19_a-second-station.md"] = "a second station"
    queue = Queue(files=files)
    queue.start()

    queue.advance(1)

    assert queue.statuses() == {1: "failed"}


def test_describe_shows_the_close_naming_its_station():
    queue = Queue(row(1, CLOSE))

    assert queue.describe().rows[0].argv == [CLOSE_LAUNCHER, "shukuba-retire", PROJECT, STEM]


# A Command cell that is not its kind's command fails its own row (2026-10-13) ----------------

PROSE = (f"`{CORE}/launchers/chain-change/launcher.sh {PROJECT}`. If the pick is a seed of the "
         f"owner's own acts, this row does not apply")


def test_a_prose_command_is_refused_on_its_row_saying_it_is_not_a_command():
    rows = bi.parse_queue(next_moves(row(1, CLOSE), row(2, CHANGE, command=PROSE, after="1")))

    refused = bi.validate(rows, core_dir=CORE, instance_root=INSTANCE, project=PROJECT,
                          card=FULL_CARD)

    assert list(refused) == [2]
    assert refused[2].startswith("its Command") and "cannot be read as a command" in refused[2]


def test_the_rows_before_a_refused_row_run_and_the_queue_halts_at_it():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"), row(3, CHANGE, command=PROSE, after="2"))

    queue.start()
    assert queue.statuses() == {1: "launched", 2: "waiting", 3: "failed"}
    queue.close_station()
    queue.advance(1)
    queue.pick_seed()
    queue.advance(2)

    assert [argv[1] for argv in queue.processes.launched] == ["shukuba-retire", "nemawashi-pick"]
    assert queue.state["ended"] == "halted"
    assert "3. walk the next change failed: its Command" in queue.state["ended_reason"]
    assert "cannot be read as a command" in queue.state["ended_reason"]


def test_a_wrong_command_fails_its_row_and_blocks_the_rows_that_wait_on_it():
    wrong = f"`{CORE}/launchers/chain-change/launcher.sh another`"
    queue = Queue(row(1, CLOSE), row(2, CHANGE, command=wrong, after="1"), row(3, OWNER, after="2"))

    queue.start()
    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "failed", 3: "end"}
    assert "is not what 'walk the next change' runs" in queue.state["rows"][1]["reason"]
    assert [argv[1] for argv in queue.processes.launched] == ["shukuba-retire"]
    assert queue.state["ended"] == "halted"


def test_a_runnable_row_waiting_on_a_refused_row_is_blocked_and_never_launched():
    queue = Queue(row(1, CLOSE), row(2, PICK, command=PROSE, after="1"),
                  row(3, CUT_ROUTE, after="2"))

    queue.start()
    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "failed", 3: "blocked"}
    assert [argv[1] for argv in queue.processes.launched] == ["shukuba-retire"]
    assert "blocked: 3. cut the route" in queue.notifier.messages[-1]


def test_a_refused_row_is_never_launched_on_a_resume():
    queue = Queue(row(1, CLOSE), row(2, PICK, command=PROSE, after="1"))
    queue.start()
    queue.advance(1, "failed")

    queue.start()

    assert [argv[1] for argv in queue.processes.launched] == ["shukuba-retire", "shukuba-retire"]
    assert queue.statuses()[2] == "failed"


def test_a_row_refused_at_the_first_start_runs_on_a_resume_that_accepts_it():
    """A resume rechecks every Command: a halted walk refused its rows under a check since
    fixed, and replaying the recorded refusal kept it halted on a report that now runs."""
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start()
    queue.advance(1, "failed")

    def refuse_row_2(state):
        state["rows"][1].update(status="failed", reason="stale", refused="stale", argv=[])
    queue.edit_state(refuse_row_2)
    queue.start()
    queue.close_station()
    queue.advance(1)

    assert queue.statuses() == {1: "landed", 2: "launched"}
    assert "refused" not in queue.state["rows"][1]
    assert [argv[1] for argv in queue.processes.launched] == [
        "shukuba-retire", "shukuba-retire", "nemawashi-pick"]


def test_a_resume_with_only_a_refused_row_left_says_so():
    queue = Queue(row(1, CLOSE), row(2, PICK, command=PROSE, after="1"))
    queue.start()
    queue.close_station()
    queue.advance(1)

    with pytest.raises(bi.QueueRefused) as refused:
        queue.start()

    assert "row 2" in str(refused.value) and "cannot be read as a command" in str(refused.value)
    assert "fully consumed" not in str(refused.value)


def test_describe_names_a_refused_row_and_its_reason():
    queue = Queue(row(1, CLOSE), row(2, PICK, command=PROSE, after="1"))

    plan = queue.describe()

    assert plan.rows[1].argv is None
    assert "cannot be read as a command" in plan.rows[1].refused
    assert bi._describe_line(plan.rows[1]).startswith(f"2. {PICK} — after 1 — refused: its Command")


def test_a_refine_report_row_with_a_prose_command_fails_alone_and_the_refine_lands():
    queue = retiring_queue()
    queue.start()
    land_retirement(queue)

    land_refinement(queue, row(1, PICK), row(2, CUT_ROUTE, after="1"),
                    row(3, CHANGE, command=PROSE, after="2"))

    assert queue.statuses() == {1: "landed", 2: "landed", 3: "launched", 4: "waiting",
                                5: "failed"}
    assert queue.processes.launched[-1][1:] == ["nemawashi-pick", PROJECT]


# --- a sealed hook start on a unit that serves no station and has no report (CP-592–CP-600) ----
#
# The walk's end starts `build-idea --start … --by-hook` on whatever it sealed. A unit that serves
# no station is owed no refine report, so with none on disk the start has nothing to run and says
# so, rather than refusing for a report nobody owes. Every other answer stays as it was.

NO_STATION_LINE = ("build_idea: nothing was started — {key} serves no station, "
                   "so it is owed no refine report")
NO_REPORT_REFUSAL = ("no {key}_report.md in any seed folder under {nemawashi} "
                     "— run shukuba-refine on {key} first")
FINISHED_STATE_NONCANONICAL = (
    b'{ "ended" : "done",\n  "key":"2026-09-10_an-older-unit",   "rows":[ ] ,\n'
    b'"pending" : {} }\n\n')


class RecordingGit:
    """The Git port, answering whether a unit served a station and recording who asked, under
    which key, and whether the start lock was held at that moment."""

    def __init__(self, serves: bool = False, lock: FakeLock | None = None):
        self.serves = serves
        self.lock = lock
        self.asked: list[tuple[str, str, bool | None]] = []

    def unit_has_shukuba(self, repo: str, key: str) -> bool:
        self.asked.append((repo, key, self.lock.held if self.lock else None))
        return self.serves


class GitNobodyMayAsk:
    """A Git port that fails the test if the station is consulted at all."""

    def unit_has_shukuba(self, repo: str, key: str) -> bool:
        raise AssertionError(f"the station was looked up for {key}, which this path never does")


def no_report_world(*, key: str = KEY) -> dict[str, str]:
    """A sealed unit with no station file and no refine report."""
    return {path: text for path, text in sealed_world(row(1, DROP), key=key, station=False).items()
            if not path.endswith("_report.md")}


def no_report_instance(tmp_path: Path, *, key: str = KEY, station_at: str | None = None) -> Path:
    """`real_instance` with the unit's report and the station placeholder removed. `station_at`
    names a folder under `shukuba/` ("" for its root) that gets a station file naming the key."""
    root = real_instance(tmp_path, row(1, DROP), key=key)
    for gone in (report_path(key), STATION_PATH):
        (root / os.path.relpath(gone, INSTANCE)).unlink()
    if station_at is not None:
        folder = root / "system" / "projects" / PROJECT / "journey" / "shukuba" / station_at
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "2026-09-18_a-station.md").write_text(f"a station serving {key}\n")
    return root


def git_history_on_main(root: Path, key: str) -> None:
    """A real repository at `root` whose `main` holds a commit that names `key` and carries a
    genuine `Shukuba:` trailer, with no station file anywhere."""
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                       check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    git("commit", "-q", "--allow-empty", "-m", f"developer: {key} — a landed unit",
        "-m", f"Shukuba: {key} — progress: a station's step")


def logs_listing(root: Path) -> list[str]:
    logs = root / "system" / "logs"
    return sorted(entry.name for entry in logs.iterdir()) if logs.exists() else []


def a_hook_start(root: Path, script: Path, *extra: str) -> list[str]:
    return start_args(root, "--by-hook", "--notifier", str(script), *extra)


@pytest.mark.parametrize("key_given", ["from-context", "explicit", "explicit-over-context"])
@pytest.mark.parametrize("state_before", [None, FINISHED_STATE_NONCANONICAL])
def test_hook_start_without_station_or_report_exits_cleanly(
        tmp_path, capsys, notifier_log, key_given, state_before):
    script, log = notifier_log
    root = no_report_instance(tmp_path, key=OTHER_KEY if key_given != "from-context" else KEY)
    if key_given == "explicit-over-context":
        # The context names a different sealed unit; the key on the command line wins.
        (root / os.path.relpath(CONTEXT_PM, INSTANCE)).write_text(
            f"# CONTEXT_PM\n\n**Status:** Sealed\n\n`{KEY}` — the unit.\n")
    if key_given == "explicit":
        (root / os.path.relpath(CONTEXT_PM, INSTANCE)).unlink()
    state = root / "system" / "logs" / "state.json"
    if state_before is not None:
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_bytes(state_before)
    logs_before = logs_listing(root)
    extra = ["--key", OTHER_KEY] if key_given != "from-context" else []

    code = bi.main(a_hook_start(root, script, *extra))

    captured = capsys.readouterr()
    key = KEY if key_given == "from-context" else OTHER_KEY
    # The streams ride in the message: against an engine that still refuses, the failure has to
    # show the refusal itself, and pytest's default diff truncates it out of the tuple.
    assert (code, captured.out, captured.err) == (0, NO_STATION_LINE.format(key=key) + "\n", ""), (
        f"exit {code}\nstdout: {captured.out!r}\nstderr: {captured.err!r}")
    assert not log.exists(), "no message is sent on the owner's channel"
    assert state.read_bytes() == state_before if state_before is not None else not state.exists()
    assert not [name for name in logs_listing(root) if name.endswith(".sh")]
    assert set(logs_listing(root)) - set(logs_before) <= {"state.json.lock"}


@pytest.mark.parametrize("station_at", ["", "trail", "parked", "git-trailer"])
def test_hook_start_with_station_and_no_report_is_refused(
        tmp_path, capsys, notifier_log, station_at):
    script, log = notifier_log
    root = no_report_instance(tmp_path, station_at=None if station_at == "git-trailer"
                              else station_at)
    if station_at == "git-trailer":
        git_history_on_main(root, KEY)
    state = root / "system" / "logs" / "state.json"

    code = bi.main(a_hook_start(root, script))

    captured = capsys.readouterr()
    refusal = NO_REPORT_REFUSAL.format(
        key=KEY, nemawashi=root / "system" / "projects" / PROJECT / "journey" / "nemawashi")
    assert (code, captured.out, captured.err) == (3, "", f"build_idea: {refusal}\n")
    assert log.read_text() == f"build-idea refused to start — {refusal}\n"
    assert not state.exists()
    assert not [name for name in logs_listing(root) if name.endswith(".sh")]


def test_hook_start_without_station_has_no_queue_effects():
    queue = Queue(files=no_report_world())
    queue.git = RecordingGit(serves=False, lock=queue.lock)

    result = queue.start(by_hook=True)

    assert isinstance(result, cd.AdvanceResult)
    assert (result.acted, result.ended, result.key) == (False, None, KEY)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.acted = True
    assert queue.git.asked == [(INSTANCE, KEY, True)], "asked once, under the start lock"
    assert STATE not in queue.files.files
    assert queue.processes.calls == [] and queue.watcher.started == []
    assert queue.log.lines == [] and queue.notifier.messages == []


def _a_standing_stop() -> Queue:
    queue = Queue(files=no_report_world())
    queue.stop()
    return queue


def _a_queue_in_flight() -> Queue:
    queue = Queue(row(1, SWEEP))
    queue.start()
    del queue.files.files[report_path()]
    return queue


def _a_live_walk_without_a_report() -> Queue:
    queue = Queue(files=no_report_world())
    queue.files.files[CHAIN_CHANGE_STATE] = json.dumps(
        {"ended": None, "pending": {"specs": {"step": "specs", "audited": None}}})
    return queue


def _no_sealed_key_and_no_report() -> Queue:
    return Queue(files={STATION_PATH: "a station"})


@pytest.mark.parametrize("make, answer", [
    (_a_standing_stop, None),
    (_a_queue_in_flight, "is still running"),
    (_a_live_walk_without_a_report, "chain-change walk is live"),
    (_no_sealed_key_and_no_report, "no sealed unit"),
])
def test_earlier_start_answers_win_over_a_missing_no_station_report(make, answer):
    queue = make()
    queue.git = GitNobodyMayAsk()
    state_before = queue.files.files.get(STATE)
    launched, sent = len(queue.processes.calls), len(queue.notifier.messages)

    if answer is None:
        result = queue.start(by_hook=True)
        assert result.acted is False and not hasattr(result, "key")
        assert len(queue.notifier.messages) == sent + 1
        assert "build-idea is stopped — chain-change's end did not restart it" in (
            queue.notifier.messages[-1])
    else:
        with pytest.raises(bi.QueueRefused, match=answer):
            queue.start(by_hook=True)

    assert queue.files.files.get(STATE) == state_before
    assert len(queue.processes.calls) == launched


@pytest.mark.parametrize("by_hook_on_describe", [False, True])
def test_plain_start_and_describe_still_refuse_a_missing_no_station_report(
        tmp_path, capsys, notifier_log, by_hook_on_describe):
    script, log = notifier_log
    root = no_report_instance(tmp_path)
    refusal = NO_REPORT_REFUSAL.format(
        key=KEY, nemawashi=root / "system" / "projects" / PROJECT / "journey" / "nemawashi")

    plain = bi.main(start_args(root, "--notifier", str(script)))
    started = capsys.readouterr()
    # describe is handed the same notifier, so "describe sends nothing" is observed rather than
    # true only because no channel was given.
    described = bi.main(_describe_args(
        root, "--notifier", str(script), *(["--by-hook"] if by_hook_on_describe else [])))
    described_out = capsys.readouterr()

    assert (plain, started.out, started.err) == (3, "", f"build_idea: {refusal}\n")
    assert log.read_text() == f"build-idea refused to start — {refusal}\n"
    assert (described, described_out.out, described_out.err) == (3, "", f"build_idea: {refusal}\n")
    assert log.read_text().count("\n") == 1, "describe sends nothing"


def test_hook_start_with_a_report_still_runs_without_station_lookup():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"), git=GitNobodyMayAsk())

    result = queue.start(by_hook=True)

    assert result.acted is True
    assert queue.statuses() == {1: "launched", 2: "waiting"}
    assert queue.processes.launched[-1] == bi.expected_argv(
        CLOSE, core_dir=CORE, project=PROJECT, station=STEM)


@pytest.mark.parametrize("providers_file", ["absent", "invalid"])
def test_no_queue_hook_start_does_not_require_provider_configuration(
        tmp_path, capsys, notifier_log, providers_file):
    script, log = notifier_log
    root = no_report_instance(tmp_path)
    if providers_file == "absent":
        (root / ".providers.toml").unlink()
    else:
        (root / ".providers.toml").write_text("this is [not valid toml", encoding="utf-8")

    code = bi.main(a_hook_start(root, script))

    captured = capsys.readouterr()
    assert (code, captured.out, captured.err) == (0, NO_STATION_LINE.format(key=KEY) + "\n", "")
    assert not log.exists()


def test_a_report_present_start_still_refuses_for_provider_configuration(
        tmp_path, capsys, notifier_log):
    script, log = notifier_log
    root = real_instance(tmp_path, row(1, DROP))
    (root / ".providers.toml").write_text("this is [not valid toml", encoding="utf-8")

    code = bi.main(a_hook_start(root, script))

    captured = capsys.readouterr()
    assert (code, captured.out) == (3, "")
    assert captured.err.startswith("build_idea: ") and "Traceback" not in captured.err
    reason = captured.err.removeprefix("build_idea: ")
    assert log.read_text() == f"build-idea refused to start — {reason}"
    assert not (root / "system" / "logs" / "state.json").exists()


def test_hook_start_keeps_retirement_continuation_and_refinement_refusals():
    continuing = retiring_queue(git=GitNobodyMayAsk())
    continuing.start(by_hook=True)
    continuing.edit_state(lambda state: state["pending"].clear())
    del continuing.files.files[report_path()]
    continuing.files.files[f"{NEMAWASHI}/trail/{SEED}.md"] = continuing.files.files.pop(ROOT_SEED)
    continuing.journey.seeds = []

    resumed = continuing.start(by_hook=True)

    assert resumed.acted is True and not hasattr(resumed, "key")

    unrefined = retired_queue()
    unrefined.git = GitNobodyMayAsk()
    with pytest.raises(bi.QueueRefused) as refused:
        unrefined.start(by_hook=True)

    assert f"nemawashi-refine {PROJECT} {SEED}" in str(refused.value)
    assert not hasattr(refused.value, "layout")
    assert not unrefined.processes.calls


def test_a_report_present_hook_start_with_a_malformed_report_is_refused_as_before():
    queue = Queue(row(1, DROP), git=GitNobodyMayAsk())
    queue.files.files[report_path()] = next_moves(
        f"1 | {SWEEP} | owner | {command_for(SWEEP)} | Moves row 1",
        header="| # | Move | Whose | Command | From |")

    with pytest.raises(bi.QueueRefused, match="After") as refused:
        queue.start(by_hook=True)

    assert not hasattr(refused.value, "layout")
    assert STATE not in queue.files.files and not queue.processes.calls


# --- the owner's Mac ask: kept on the queue, put on every chain-change row ----------------------


def test_a_chain_change_row_carries_the_owners_mac_ask():
    queue = Queue(row(1, CHANGE))

    queue.start(gate_owners_mac=True)

    assert queue.processes.launched[0][-3:] == ["--context-cap", "250000", "--gate-owners-mac"]


def test_a_queue_without_the_ask_puts_none_on_its_chain_change_row():
    queue = Queue(row(1, CHANGE))

    queue.start()

    assert "--gate-owners-mac" not in queue.processes.launched[0]


@pytest.mark.parametrize("move", [CLOSE, PICK, CUT_ROUTE, SWEEP])
def test_a_row_that_is_not_a_chain_change_carries_no_ask(move):
    """A skill row has no gate, and the sweep runs `chain-product`, which refuses the flag."""
    queue = Queue(row(1, move))

    queue.start(gate_owners_mac=True)

    assert all("--gate-owners-mac" not in argv for argv in queue.processes.launched)


def test_the_ask_travels_as_a_flag_never_in_the_environment():
    """The gate tool reads the variable itself, so a queue never puts it on a launch."""
    queue = Queue(row(1, CLOSE), row(2, CHANGE, after="1"))

    queue.start(gate_owners_mac=True)
    queue.close_station()
    queue.advance(1)

    assert all(gs.OWNERS_MAC_VARIABLE not in call["env"] for call in queue.processes.calls)


def test_every_start_states_the_ask_so_a_resume_can_lift_it():
    """The start a walk's end makes passes the flag when that walk had the ask; an owner's plain
    resume passes none, and the queue's next chain-change walk has none."""
    queue = Queue(row(1, CLOSE), row(2, CHANGE, after="1"))
    queue.start(gate_owners_mac=True)
    queue.stop()
    queue.close_station()
    queue.advance(1)

    queue.start()

    assert queue.state["gate_owners_mac"] is False
    assert "--gate-owners-mac" not in queue.processes.launched[-1]


def test_a_queue_state_round_trip_keeps_the_ask_and_an_older_file_loads_without_it():
    state = bi.QueueState(project=PROJECT, gate_owners_mac=True)

    assert bi.QueueState.from_json(state.to_json()).gate_owners_mac is True

    older = state.to_json()
    del older["gate_owners_mac"]
    assert bi.QueueState.from_json(older).gate_owners_mac is False


def test_main_start_records_the_ask_only_when_given(tmp_path):
    root = real_instance(tmp_path, row(1, DROP))
    state_path = root / "system" / "logs" / "state.json"

    assert bi.main(start_args(root, "--gate-owners-mac")) == 0
    assert json.loads(state_path.read_text())["gate_owners_mac"] is True

    fresh = real_instance(tmp_path / "second", row(1, DROP))
    assert bi.main(start_args(fresh)) == 0
    assert json.loads(
        (fresh / "system" / "logs" / "state.json").read_text())["gate_owners_mac"] is False


def test_the_owners_act_resume_hint_restates_the_ask_the_queue_holds():
    """A resume lifts the ask unless it restates it, so the queue's own hint restates it."""
    queue = Queue(row(1, OWNER, command=WALK_YOURSELF))

    queue.start(gate_owners_mac=True)

    assert queue.notifier.messages[-1].splitlines()[0].endswith(
        f"once it is made, resume with: {RESUME} --gate-owners-mac")


def test_the_stops_resume_hint_restates_the_ask_the_queue_holds():
    queue = Queue(row(1, CLOSE), row(2, PICK, after="1"))
    queue.start(gate_owners_mac=True)

    said = queue.stop()

    assert f"Resume with: {RESUME} --gate-owners-mac" in said


def test_a_suppressed_hook_starts_resume_hint_restates_that_walks_ask():
    """The walk had the ask, and the only way back the system offers must not drop it."""
    queue = stopped_mid_way(row(1, CLOSE), row(2, PICK, after="1"))

    queue.start(by_hook=True, gate_owners_mac=True)

    assert f"run {RESUME} --gate-owners-mac to resume" in queue.notifier.messages[-1]


def test_a_resume_hint_names_no_ask_the_queue_does_not_hold():
    queue = Queue(row(1, OWNER, command=WALK_YOURSELF))

    queue.start()

    assert "--gate-owners-mac" not in queue.notifier.messages[-1]
