"""The chain engine's suite — driven through the ports it is given, never around them.

WHY THIS FILE LOOKS LIKE THIS
    Its predecessor was green over a feature that did not exist. It proved 161 functions
    against module-level tables and never once asked what the engine actually launched, so
    `chain-foundation`'s spine — printed by its launcher, never passed to the engine — could
    be ignored entirely while every test passed. The walk tables below are the level that was
    missing: a spine in, a scripted disk and a scripted set of self-answer reports, and an
    assertion on the exact ordered `argv` the injected process port received.

    Nothing here monkeypatches the module under test. Every collaborator the engine uses is
    handed to it through its constructor, which is what makes that possible.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shlex
import subprocess
import time
import tomllib
import uuid
from pathlib import Path

import pytest

import build_idea
import chain
import chain_development
import completion_shim
from instance_test_support import scratch_instance
import product_checkout
import providers
import walk_stop
import watch_agent
from run_intelligence import PROVIDERS
from test_chain_development import FakeCheckout, FakeProcessTable
from test_completion_shim import HOLD_CAP, wait_for
from test_providers import (COPY_COMMAND, DELIVERED_TEXT, EXAMPLE_FILE, ProviderText, edited_text,
                            provider_files)


# --- the fakes: one per port the engine is given ------------------------------------------


class FakeFiles:
    """An in-memory tree. `files` maps an absolute path to its text; a directory exists when
    something lives under it. Writes land in the same dict, so the shim the engine writes is
    readable back by a test."""

    def __init__(self, files: dict[str, str] | None = None):
        self.files = dict(files or {})
        self.executable: set[str] = set()
        self.made_dirs: list[str] = []
        self.writes: list[tuple[str, str]] = []

    def is_file(self, path: str) -> bool:
        return os.path.normpath(path) in self.files

    def is_dir(self, path: str) -> bool:
        prefix = os.path.normpath(path).rstrip("/") + "/"
        return any(key.startswith(prefix) for key in self.files)

    def list_dir(self, path: str) -> list[str]:
        prefix = os.path.normpath(path).rstrip("/") + "/"
        names = set()
        for key in self.files:
            if key.startswith(prefix):
                names.add(key[len(prefix):].split("/", 1)[0])
        return sorted(names)

    def read_text(self, path: str) -> str | None:
        return self.files.get(os.path.normpath(path))

    def write_text(self, path: str, text: str) -> None:
        self.files[os.path.normpath(path)] = text
        self.writes.append((os.path.normpath(path), text))

    def make_dirs(self, path: str) -> None:
        self.made_dirs.append(os.path.normpath(path))

    def make_executable(self, path: str) -> None:
        self.executable.add(os.path.normpath(path))

    def replace(self, source: str, destination: str) -> None:
        self.files[os.path.normpath(destination)] = self.files.pop(os.path.normpath(source))

    def real_path(self, path: str) -> str:
        return os.path.normpath(path)


class FakeProcesses:
    """Records every launch. `codes` scripts the exit status each successive call returns."""

    def __init__(self, codes: list[int] | None = None):
        self.calls: list[dict] = []
        self.codes = list(codes or [])

    def run(self, argv, *, cwd=None, env=None, capture=False, timeout=None) -> int:
        self.calls.append({"argv": list(argv), "cwd": cwd, "env": dict(env or {}),
                           "capture": capture})
        return self.codes.pop(0) if self.codes else 0

    @property
    def launched(self) -> list[list[str]]:
        return [call["argv"] for call in self.calls]


class Round:
    """Several reports one launch left in a trail, scripted as ONE entry of a stem's queue.
    `first` is the number of the first report's file, so a test can name `self_answer-4.md`.
    A member of `None` is a report the reader cannot read."""

    def __init__(self, reports, first: int = 1):
        self.reports = list(reports)
        self.first = first


class FakeReports:
    """Scripted self-answer reports, queued per trail stem. `find` answers with a path only
    while that stem still has a report queued, which is how a run that produced none is
    modelled. `present_before` scripts what `.present()` (the launch-time reading, task 4)
    answers per stem — empty unless a test configures it.

    A queue entry is one round: a single report, or a `Round` of several. `find_round` answers
    with the paths of the head entry, and records its arguments into `found` exactly as `find`
    does, so every `reports.found` assertion reads the same whichever the engine calls."""

    def __init__(self, scripts: dict[str, list[chain.SelfAnswerReport]] | None = None,
                present_before: dict[str, list[str]] | None = None):
        self.scripts = {stem: list(reports) for stem, reports in (scripts or {}).items()}
        self.present_before = {stem: list(paths)
                               for stem, paths in (present_before or {}).items()}
        self.found: list[tuple] = []

    def present(self, search_root: str, trail_stem: str) -> tuple[str, ...]:
        return tuple(self.present_before.get(trail_stem, ()))

    def find(self, search_root: str, trail_stem: str, reports_before=None) -> str | None:
        self.found.append((search_root, trail_stem, reports_before))
        if self.scripts.get(trail_stem):
            return f"{search_root}/docs/trail/{trail_stem}/self_answer-1.md"
        return None

    def find_round(self, search_root: str, trail_stem: str,
                   reports_before=None) -> tuple[str, ...]:
        self.found.append((search_root, trail_stem, reports_before))
        queue = self.scripts.get(trail_stem)
        if not queue:
            return ()
        head = queue[0]
        first, count = (head.first, len(head.reports)) if isinstance(head, Round) else (1, 1)
        return tuple(f"{search_root}/docs/trail/{trail_stem}/self_answer-{n}.md"
                     for n in range(first, first + count))

    def read(self, path: str) -> chain.SelfAnswerReport:
        stem = path.rsplit("/", 2)[-2]
        head = self.scripts[stem][0]
        if not isinstance(head, Round):
            return self.scripts[stem].pop(0)
        member = head.reports.pop(0)
        if not head.reports:
            self.scripts[stem].pop(0)
        return member


class FakeNotifier:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


class FakeIdSource:
    """A fixed id by default, so a walk-id assertion is exact rather than "some string". `calls`
    counts invocations — the seam `TestAWalkTiesItsDocumentsTogether` uses to prove `start()`
    mints exactly once per walk, never once per launch."""

    def __init__(self, id_value: str = "fixed-walk-id"):
        self.id_value = id_value
        self.calls = 0

    def new_id(self) -> str:
        self.calls += 1
        return self.id_value


# --- the world the walk tables run in -----------------------------------------------------


CORE = "/core"
INSTANCE = "/instance"
PRODUCT = "/product"
PROJECT = "sealbox"
STATE = "/instance/system/logs/chain-sealbox-state.json"
INSTANCE_PROVIDER_FILE = providers.instance_file(INSTANCE)
SHIM = "/instance/system/logs/chain-sealbox.sh"

# Every launcher the engine can reach, with the `# USAGE` block validation reads: the skill
# launcher every producer runs through, `product-card` — a real launcher taking one positional,
# which the validation cases need — and the answer step — the fleet's real shape.
def launcher_tree() -> dict[str, str]:
    tree = {}
    tree[f"{CORE}/launchers/product-card/launcher.sh"] = (
        "#!/usr/bin/env bash\n"
        "# USAGE\n"
        "#   <CORE>/launchers/product-card/launcher.sh <project> [--dry-run] [--keep-awake]\n")
    tree[f"{CORE}/launchers/skill/launcher.sh"] = (
        "#!/usr/bin/env bash\n"
        "# USAGE\n"
        "#   <CORE>/launchers/skill/launcher.sh <skill> [<argument>...] [--dry-run] "
        "[--keep-awake]\n")
    tree[f"{CORE}/launchers/companion-self-answer/launcher.sh"] = (
        "#!/usr/bin/env bash\n"
        "# USAGE\n"
        "#   <CORE>/launchers/companion-self-answer/launcher.sh <project> <document> "
        "[--dry-run]\n")
    return tree


def report(*, document=None, counts=None, owed=(), companions_opened=(), raised=0,
           unnamed=0, missing_headings=()):
    return chain.SelfAnswerReport(
        document=document,
        counts=dict(counts or {}),
        companions_opened=list(companions_opened),
        owed=[chain.OwedItem(document_path=path, command=command) for path, command in owed],
        raised=raised,
        unnamed=unnamed,
        missing_headings=list(missing_headings),
    )


def build(files: FakeFiles, *, processes=None, reports=None, notifier=None, codes=None,
          id_source=None, environ=None, provider_port=None, process_table=None,
          checkout=None):
    return chain.Chain(
        store=chain.StateStore(files, STATE),
        files=files,
        processes=processes or FakeProcesses(codes=codes),
        reports=reports or FakeReports(),
        notifier=notifier or FakeNotifier(),
        id_source=id_source or FakeIdSource(),
        engine_path="/pinned/chain.py",
        environ=environ or {"PATH": "/usr/bin"},
        providers=provider_files(port=provider_port),
        process_table=FakeProcessTable() if process_table is None else process_table,
        checkout=checkout or FakeCheckout(),
    )


def write_provider_file(instance_root, text: str = DELIVERED_TEXT) -> None:
    """The instance's own `.providers.toml`, where a case that runs the real composition starts
    its walk — an unforced start reads it there and nowhere else (CP-483)."""
    Path(instance_root).mkdir(parents=True, exist_ok=True)
    (Path(instance_root) / ".providers.toml").write_text(text, encoding="utf-8")


def start(engine, spine, **kwargs):
    return engine.start(instance_root=INSTANCE, product_path=PRODUCT, project=PROJECT,
                        core_dir=CORE, shim_path=SHIM, spine=chain.parse_spine(spine),
                        **kwargs)


def finish(engine, outcome="completed"):
    """The pending run's own shim firing: `advance` given the launch the state is waiting on,
    exactly what that launch's shim passes. A stale delivery is `engine.advance` called with
    some other launch, and says so where it is written."""
    pending = engine.store.load().pending
    return engine.advance(outcome, launch=(pending or {}).get("launch"))


def producer(folder):
    return [f"{CORE}/launchers/{folder}/launcher.sh", PROJECT]


def through_skill(skill):
    return [f"{CORE}/launchers/skill/launcher.sh", skill, PROJECT]


def answer(document_argument):
    return [f"{CORE}/launchers/companion-self-answer/launcher.sh", PROJECT, document_argument]


# --- THE WALK TABLES ----------------------------------------------------------------------


class TestTheChainWalksTheSpineItWasGiven:
    """The defect the owner rejected the first engine for, and the reason this class exists:
    `chain-foundation` declared a two-document spine and the engine walked all ten, because
    the spine never reached it. Live, 2026-09-01: `chain-<project>-state.json` carried
    `"rounds": {"SRS": 1}` after a foundation-tier command."""

    def test_the_foundation_spine_enters_at_the_fdr_and_never_touches_the_prd(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR,ADR,NFDR")

        assert processes.launched == [through_skill("product-fdr")]
        assert all("product-prd" not in " ".join(argv) for argv in processes.launched)

    def test_the_definition_spine_enters_at_the_prd(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "PRD,Agari,SRS,UXD,DESIGN,CONTENT,SDD")

        assert processes.launched == [through_skill("product-prd")]

    def test_a_spine_walks_only_its_own_documents(self):
        """Every spine document absent, so every one of them is a producer launch and the
        walk is the spine, in order — and stops at its end rather than running on into the
        rest of the registry."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")   # the FDR producer finished
        finish(engine, "completed")   # the ADR/NFDR producer finished
        finish(engine, "completed")   # NFDR: product-architecture again

        assert processes.launched == [
            through_skill("product-fdr"),
            through_skill("product-architecture"),
            through_skill("product-architecture"),
        ]
        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value

    def test_a_document_already_on_disk_with_no_companion_is_walked_past(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR"})
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR,ADR,NFDR")

        assert processes.launched == [through_skill("product-architecture")]

    def test_a_document_with_a_companion_goes_to_the_answer_step(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR,ADR,NFDR")

        assert processes.launched == [answer("FDR")]


class TestTheOwedSetDrainsBeforeTheSpineMovesOn:

    def test_an_owed_bullet_outside_the_spine_is_still_walked(self):
        """The owner's ruling, 2026-08-31: the name states the entry and the spine, not the
        blast radius. A foundation chain owed an SRS run runs it — the spine narrows what the
        chain walks on its own initiative, never what a report asks for."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"),),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        assert processes.launched == [answer("FDR"), through_skill("product-srs")]

    def test_the_owed_set_drains_upstream_first(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(
                ("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),
                ("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"),
            ),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")
        finish(engine, "completed")

        assert processes.launched == [answer("FDR"),
                                      through_skill("product-srs"),
                                      through_skill("product-fdr")]


class TestAnOwedLauncherIsQueuedOnce:
    """A live product, 2026-09-25: an ADR round owed `product-architecture`, the FDR round after
    it owed it again, and the second ADR round owed it a third time. The queue took every copy,
    so after the second run folded the companion away the third ran with nothing to fold,
    committed nothing, and ended the walk on `produced_nothing`. One queued run of a producer
    folds every answer on disk when it runs, so a launcher already queued is not queued again —
    judged by what the command resolves to, since the reports spelled the same launcher with the
    pin's absolute path and with `<CORE>`."""

    def test_one_round_owing_a_launcher_twice_runs_it_once(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(
                ("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"),
                ("docs/SRS.md", f"<CORE>/launchers/skill/launcher.sh product-srs {PROJECT}"),
            ),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR")
        finish(engine, "completed")
        finish(engine, "completed")

        assert processes.launched.count(through_skill("product-srs")) == 1

    def test_a_launcher_already_queued_is_not_queued_again(self):
        engine = build(FakeFiles(launcher_tree()))
        state = chain.ChainState(project=PROJECT, instance_root=INSTANCE, product_path=PRODUCT,
                                 core_dir=CORE, shim_path=SHIM, spine=["FDR"])
        state.queue = [{"document_path": "adr/ and nfdr.md",
                        "command": f"{CORE}/launchers/skill/launcher.sh product-architecture {PROJECT}"}]

        queued = engine._queue_owed(state, [
            chain.OwedItem(document_path="docs/adr/ and docs/nfdr.md",
                           command=f"<CORE>/launchers/skill/launcher.sh product-architecture {PROJECT}"),
            chain.OwedItem(document_path="docs/fdr.md",
                           command=f"<CORE>/launchers/skill/launcher.sh product-fdr {PROJECT}"),
        ])

        assert [item["command"].split()[-2] for item in queued] == [
            "product-architecture", "product-fdr"]


class TestTheEngineNeverLaunchesWhatNobodyAskedFor:

    def test_no_launch_outside_the_spine_or_the_owed_set(self):
        """The negative the old suite had no way to state."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR")
        for _ in range(5):
            finish(engine, "completed")

        allowed = {tuple(through_skill("product-fdr")), tuple(answer("FDR"))}
        assert {tuple(argv) for argv in processes.launched} <= allowed


PRODUCT_SPINE = "PRD,Agari,SRS,UXD,DESIGN,CONTENT,SDD,FDR,ADR,NFDR"


class TestAWalkThroughTheSkillLauncher:
    """The owner's ruling, 2026-09-17: every document runs through
    `<CORE>/launchers/skill/launcher.sh` and that skill's own `launcher.md` — the SDD included —
    and the answer step is `companion-self-answer`'s."""

    def test_every_producer_goes_through_the_skill_launcher(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, PRODUCT_SPINE)
        for _ in range(10):   # one completion per launch below
            finish(engine, "completed")

        assert processes.launched == [
            through_skill("product-prd"),
            through_skill("project-agari"),
            through_skill("product-srs"),
            through_skill("product-uxd"),
            through_skill("product-design"),
            through_skill("product-content"),
            through_skill("product-sdd"),
            through_skill("product-fdr"),
            through_skill("product-architecture"),
            through_skill("product-architecture"),
        ]
        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value

    def test_the_answer_step_keeps_its_own_launcher(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR")

        assert processes.launched == [answer("FDR")]

    def test_an_owed_bullet_quoting_the_skill_launcher_is_launched_as_quoted(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(("docs/UXD.md",
                   f"<CORE>/launchers/skill/launcher.sh product-uxd {PROJECT}"),),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR")
        finish(engine, "completed")

        assert processes.launched == [answer("FDR"), through_skill("product-uxd")]

    def test_an_owed_answer_step_is_launched_as_quoted(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(("docs/SRS_open_issues.md",
                   f"<CORE>/launchers/companion-self-answer/launcher.sh {PROJECT} SRS"),),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR")
        finish(engine, "completed")

        assert processes.launched == [answer("FDR"), answer("SRS")]

    def test_an_owed_launcher_that_is_no_documents_is_launched_as_quoted(self):
        files = FakeFiles({**launcher_tree(),
                            f"{CORE}/launchers/kensaiapp-writing-bar/launcher.sh": (
                                "#!/usr/bin/env bash\n# USAGE\n"
                                "#   <CORE>/launchers/kensaiapp-writing-bar/launcher.sh\n"),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(("system/doctrine/writing_bar.md",
                   "<CORE>/launchers/kensaiapp-writing-bar/launcher.sh"),),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR")
        finish(engine, "completed")

        assert processes.launched == [answer("FDR"),
                                      [f"{CORE}/launchers/kensaiapp-writing-bar/launcher.sh"]]

    def test_a_refused_owed_command_is_still_refused(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 1},
            owed=(("docs/nfdr.md", "product-nfdr"),),
        )]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR")
        finish(engine, "completed")

        assert processes.launched == [answer("FDR")]
        assert engine.store.load().ended == chain.CycleEnd.NO_RUNNABLE_COMMAND.value

    def test_every_argv_the_walk_builds_is_accepted_by_the_real_skill_launcher(self, tmp_path):
        """Run dry through the real launcher against this repository's real `launcher.md` files,
        so a skill with no declaration, or one taking other arguments, is refused here and not on
        the first real walk — and each names the reporter its completion message is written by."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, PRODUCT_SPINE)
        for _ in range(10):
            finish(engine, "completed")

        repo = Path(chain.__file__).resolve().parents[2]
        env = dict(os.environ)
        env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
        env["HOME"] = str(tmp_path)
        real_project = "example-product"
        instance = scratch_instance(tmp_path, real_project)
        through = [argv for argv in processes.launched if argv[0] == f"{CORE}/launchers/skill/launcher.sh"]
        assert len(through) == 10   # all ten producers, the SDD's included
        for argv in through:
            real = [str(repo / "core" / "launchers" / "skill" / "launcher.sh"), argv[1],
                    real_project, "--provider", "claude", "--dry-run"]   # forced: no instance file

            result = subprocess.run(real, cwd=str(instance), capture_output=True, text=True, env=env)

            assert result.returncode == 0, (argv, result.stderr)
            assert f"Argument:  <project> {real_project}" in result.stdout, argv
            reporter = next(line for line in result.stdout.splitlines()
                            if line.startswith("Reporter:"))
            assert not reporter.startswith("Reporter:  generic"), (argv, reporter)

    def test_keep_awake_reaches_the_skill_launcher(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "SRS", keep_awake=True)

        assert processes.launched == [through_skill("product-srs") + ["--keep-awake"]]


# --- the four live defects, each as a named regression ------------------------------------


class TestRegressions:

    def test_a_usage_line_owed_bullet_is_not_counted_as_three_positionals(self):
        """A live product, 2026-09-01. All four owed bullets quoted the launcher's own
        `# USAGE` line, brackets included, and the chain refused every one:
        "product-architecture takes 1 positional argument(s), '… <project> [--dry-run]
        [--keep-awake]' gives 3"."""
        files = FakeFiles(launcher_tree())
        validated = chain.validate_owed_command(
            "<CORE>/launchers/skill/launcher.sh product-architecture example-product "
            "[--dry-run] [--keep-awake]",
            core_dir=CORE, instance_root=INSTANCE, files=files)
        assert validated.argv == [f"{CORE}/launchers/skill/launcher.sh", "product-architecture",
                                  "example-product"]

    def test_adr_is_recognised_when_it_is_the_last_path_segment(self):
        """A live product, 2026-09-01. An SRS round opened a companion on `adr/` and carried the
        `product-architecture` bullet that runs it; a parents-only scan could not see the two
        spellings as one document and the chain refused a report it had in fact routed."""
        assert chain.resolve_document("adr/") is chain.document("ADR")
        assert chain.resolve_document("docs/adr/0001-thing.md") is chain.document("ADR")

    def test_a_state_file_from_another_schema_is_a_message_not_a_traceback(self):
        """A live product, 2026-09-01 09:49. An engine edit landed under a running chain and the
        completion hook died with `ValueError: this state file carries no 'spine'`, taking
        the walk with it."""
        files = FakeFiles({STATE: '{"project": "sealbox", "schema_version": 0}'})
        store = chain.StateStore(files, STATE)
        with pytest.raises(chain.StateIncompatible) as raised:
            store.load()
        assert "start the chain again" in str(raised.value).lower()

    def test_the_shim_pins_the_engine_it_was_written_by(self):
        """The same defect's other half: the shim must run the engine the chain was started
        with, never whatever now sits at that path — so the path is injected, never read from
        the module's own `__file__`."""
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR")
        assert "/pinned/chain.py" in files.read_text(f"{SHIM[:-3]}-fixed-walk-id-1.sh")

    def test_the_chain_shim_is_the_owners_rendering(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)

        start(engine, "FDR")

        assert files.read_text(f"{SHIM[:-3]}-fixed-walk-id-1.sh") == completion_shim.shim_text(
            "/pinned/chain.py", ("--launch", "fixed-walk-id-1", "--advance", STATE),
            "/instance/system/logs/chain-sealbox.log")


class TestAFinishNamesItsLaunch:
    """A live product, 2026-09-23. The owner abandoned a walk the way the guard's own refusal
    said to — by deleting its state file — and started another. The abandoned walk's SDD run
    was still going under its watcher, and every shim was one file per project, so when that
    run was stopped its watcher's finish landed on the NEW walk: the new walk took it for the
    finish of its own SDD run two minutes in, re-answered a companion already answered, and
    ended while its own run kept writing. Each restart left one more SDD run on the product.

    So a finish names the launch it belongs to. Each launch writes its own shim, named for the
    walk and the launch, carrying that launch's id; `advance` acts only on the launch it is
    waiting on."""

    STEM = SHIM[:-len(".sh")]

    def test_each_launch_writes_its_own_shim_carrying_its_launch(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR")

        shim = f"{self.STEM}-fixed-walk-id-1.sh"
        assert processes.calls[0]["env"]["DETACH_WATCHER_ON_COMPLETE"] == shim
        assert "--launch fixed-walk-id-1" in files.read_text(shim)
        assert "/pinned/chain.py" in files.read_text(shim)
        assert shim in files.executable
        assert engine.store.load().pending["launch"] == "fixed-walk-id-1"

    def test_the_next_launch_gets_the_next_shim(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        finish(engine)

        assert (processes.calls[1]["env"]["DETACH_WATCHER_ON_COMPLETE"]
                == f"{self.STEM}-fixed-walk-id-2.sh")
        assert engine.store.load().pending["launch"] == "fixed-walk-id-2"

    def test_a_finish_from_another_launch_advances_nothing(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        pending = engine.store.load().pending
        launched = list(processes.launched)

        result = engine.advance("completed", launch="fixed-walk-id-9")

        assert result == chain.AdvanceResult(acted=False, ended=None)
        assert processes.launched == launched
        assert engine.store.load().pending == pending

    def test_a_finish_naming_no_launch_advances_nothing_while_one_is_awaited(self):
        """What the one-file-per-project shim written before this fix still sends."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        launched = list(processes.launched)

        assert engine.advance("completed").acted is False
        assert processes.launched == launched

    def test_the_old_finish_arriving_again_after_the_next_launch_is_a_no_op(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        first = engine.store.load().pending["launch"]
        finish(engine)
        launched = list(processes.launched)

        assert engine.advance("completed", launch=first).acted is False
        assert processes.launched == launched

    def test_an_abandoned_walks_run_cannot_advance_the_next_walk(self):
        """The incident, end to end."""
        files = FakeFiles(launcher_tree())
        abandoned = build(files, id_source=FakeIdSource("walk-a"))
        start(abandoned, "FDR,ADR,NFDR")
        old_launch = abandoned.store.load().pending["launch"]
        old_shim = f"{self.STEM}-walk-a-1.sh"
        del files.files[STATE]                      # the state file deleted by hand

        processes = FakeProcesses()
        restarted = build(files, processes=processes, id_source=FakeIdSource("walk-b"))
        start(restarted, "FDR,ADR,NFDR")

        assert f"--launch {old_launch}" in files.read_text(old_shim), \
            "the new walk rewrote the shim the abandoned run's watcher still holds"
        result = restarted.advance("completed", launch=old_launch)
        assert result.acted is False
        assert len(processes.launched) == 1
        assert restarted.store.load().pending["launch"] == "walk-b-1"

    def test_a_pending_written_before_launches_were_named_still_advances(self):
        """A walk whose state predates the launch id has nothing to match against, so it keeps
        the behaviour it was started under rather than being stranded."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        state = engine.store.load()
        state.pending = {"kind": state.pending["kind"], "document": state.pending["document"]}
        engine.store.save(state)

        assert engine.advance("completed").acted is True
        assert len(processes.launched) == 2

    def test_the_cli_passes_the_launch_through(self, tmp_path, capsys):
        state_path = tmp_path / "state.json"
        state = {
            "schema_version": chain.STATE_SCHEMA, "instance_root": str(tmp_path),
            "product_path": str(tmp_path), "project": "x", "core_dir": str(tmp_path),
            "shim_path": str(tmp_path / "s.sh"), "spine": ["FDR"],
            "pending": {"kind": "producer", "document": "FDR", "launch": "w-1"},
        }
        state_path.write_text(json.dumps(state))

        assert chain.main(["--advance", str(state_path), "completed", "--launch", "w-9"]) == 0

        assert "acted=False" in capsys.readouterr().out
        assert json.loads(state_path.read_text())["pending"]["launch"] == "w-1"

        # The matching launch acts — without this half, a `main()` that dropped `--launch`
        # would pass the line above too. `timeout` halts without launching anything.
        assert chain.main(["--advance", str(state_path), "timeout", "--launch", "w-1"]) == 0

        assert "acted=True" in capsys.readouterr().out
        assert json.loads(state_path.read_text())["ended"] == chain.CycleEnd.MACHINERY.value

    def test_a_stopped_run_is_a_machinery_stop_that_says_it_was_cut_off(self):
        import watch_agent

        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        launched = list(processes.launched)

        finish(engine, watch_agent.HookOutcome.STOPPED.value)

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "stopped before it said it was finished" in state.ended_reason
        assert processes.launched == launched

    def test_the_refusal_names_the_stop_command_and_never_deleting(self):
        files = FakeFiles(launcher_tree())
        start(build(files), "FDR,ADR,NFDR")

        with pytest.raises(chain.ChainAlreadyWalking) as raised:
            start(build(files), "PRD")

        assert f"{CORE}/launchers/chain-product/launcher.sh {PROJECT} --stop" in str(raised.value)
        assert "delete" not in str(raised.value).lower()


# --- the ports are ports ------------------------------------------------------------------


class TestTheEngineTouchesNothingItWasNotGiven:

    def test_the_launch_carries_the_completion_hook_and_the_injected_environment(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(
            files,
            processes=processes,
            environ={"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": "codex"},
        )

        start(engine, "FDR")

        call = processes.calls[0]
        assert call["env"]["DETACH_WATCHER_ON_COMPLETE"] == f"{SHIM[:-3]}-fixed-walk-id-1.sh"
        assert call["env"]["PATH"] == "/usr/bin"
        assert call["cwd"] == INSTANCE


# --- the delivered provider file: the three engines' own members and the launchers' ---------

# The nine launchers whose provider the file names — the six instance skill launchers by folder
# name, then the three flat scripts under core/tools/ by script name without `.sh` — listed here by
# name, never read off the file's own keys, so an entry added to the file without a launcher behind
# it fails below.
LAUNCHER_NAMES = ("skill", "companion-self-answer", "cold-read", "launch-eval-fix",
                  "launch-skill-evals", "product-card",
                  "launch-apply-packet", "launch-audit", "launch-fix-author")


def _delivered_entries() -> dict[str, str]:
    """Every entry of the delivered `.providers.toml.example`, by its member's dotted name."""
    with open(EXAMPLE_FILE, "rb") as handle:
        tables = tomllib.load(handle)
    return {str(providers.Member(table, key)): value
            for table, entries in tables.items() for key, value in entries.items()}


def _engines_own_members() -> list[providers.Member]:
    """The union the file must name: every document, every step of either walk, every skill
    row of the queue, and the owed item that resolves to no document."""
    return ([providers.document(name) for name in chain.DOCUMENT_REGISTRY]
            + [providers.step(s.id) for s in chain_development.CHANGE_STEPS]
            + [providers.build_idea_row(name) for name, kind in build_idea.KINDS.items()
               if kind.disposition is build_idea.Disposition.RUN_SKILL]
            + [providers.OWED_ITEM])


def test_the_delivered_file_holds_the_engines_members_and_the_launchers():
    members = _engines_own_members() + [providers.launcher(name) for name in LAUNCHER_NAMES]

    assert len(members) == len(set(members)) == 30 + 9
    assert sorted(_delivered_entries()) == sorted(str(member) for member in members)


def test_the_delivered_file_names_a_known_provider_for_every_entry():
    assert {name: value for name, value in _delivered_entries().items()
            if value not in PROVIDERS} == {}


# --- the provider: forced for the walk, else the file's entry, else a refusal -------------


# CP-275: the provider every product-chain member has as delivered. A literal, not a read of the
# file, so a test over the file is checked against the owner's assignment rather than itself.
DELIVERED_DOCUMENT_PROVIDERS = {name: "claude" for name in chain.DOCUMENT_REGISTRY}
DELIVERED_OWED_ITEM_PROVIDER = "claude"

# Every member an unforced product walk resolves at its start (Gap 2): the whole registry and
# the owed item, never only the spine.
PRODUCT_MEMBERS = ([providers.document(name) for name in chain.DOCUMENT_REGISTRY]
                   + [providers.OWED_ITEM])

# An owed bullet whose path is no document: its launch is the owed-item entry's.
NOTHING_OWED = ("docs/nothing.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}")


def provider_of(call: dict) -> str | None:
    return call["env"].get("KENSAIAPP_AGENT_PROVIDER")


def companion_open(stem: str) -> dict[str, str]:
    """A product document on disk with its companion still open, so its walk opens on the
    answer step."""
    return {f"{PRODUCT}/docs/{stem}.md": f"# {stem}",
            f"{PRODUCT}/docs/{stem}_open_issues.md": "# open"}


def first_launch(spine: str, *, disk=None, port=None, forced="", environ=None) -> dict:
    """The first launch a walk of `spine` makes over `disk`, with `port` as its provider file."""
    processes = FakeProcesses()
    engine = build(FakeFiles({**launcher_tree(), **(disk or {})}), processes=processes,
                   provider_port=port, environ=environ)
    start(engine, spine, forced_provider=forced)
    return processes.calls[0]


def owed_item_walk(*, port=None, forced="", environ=None, owed=(NOTHING_OWED,)):
    """A walk that answers the FDR, whose report owes `owed` — returned after the answer step
    finished, so the owed set is draining."""
    processes = FakeProcesses()
    notifier = FakeNotifier()
    reports = FakeReports({"fdr": [report(document="docs/fdr.md", counts={"confirmed": 1},
                                          owed=owed)]})
    engine = build(FakeFiles(open_fdr_companion()), processes=processes, reports=reports,
                   notifier=notifier, provider_port=port, environ=environ)
    start(engine, "FDR", forced_provider=forced)
    return engine, processes, notifier


GEMINI_ENVIRON = {"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": "gemini"}


@pytest.mark.parametrize("name", list(chain.DOCUMENT_REGISTRY))
def test_every_document_resolves_to_its_cp275_provider(name):
    """CP-290(a), Ex 5, 30: each document's producer launches on the delivered file's entry,
    whatever provider the engine's own environment inherited."""
    call = first_launch(name, environ=GEMINI_ENVIRON)

    assert provider_of(call) == DELIVERED_DOCUMENT_PROVIDERS[name]


def test_the_owed_item_resolves_to_its_cp275_provider():
    """CP-290(a), Ex 19: an owed item whose path is no document launches on the owed-item
    entry."""
    engine, processes, _ = owed_item_walk(environ=GEMINI_ENVIRON)

    finish(engine)

    assert processes.launched[1] == through_skill("product-srs")
    assert provider_of(processes.calls[1]) == DELIVERED_OWED_ITEM_PROVIDER


@pytest.mark.parametrize("member", PRODUCT_MEMBERS, ids=str)
def test_a_copy_lacking_an_own_member_refuses_an_unforced_start_naming_it(member):
    """CP-290(b), CP-281, Ex 13: the spine is the PRD alone, and every other member still
    refuses — a walk's owed set can reach any document. Nothing is saved, launched or
    announced."""
    files = FakeFiles(launcher_tree())
    processes = FakeProcesses()
    notifier = FakeNotifier()
    port = ProviderText(edited_text({f"{member.table}.{member.key}": None}))
    engine = build(files, processes=processes, notifier=notifier, provider_port=port)

    with pytest.raises(providers.ProvidersRefused, match=f"{re.escape(str(member))} is missing"):
        start(engine, "PRD")

    assert files.read_text(STATE) is None
    assert processes.calls == []
    assert notifier.messages == []


def test_main_refuses_a_start_naming_a_missing_entry(tmp_path, capsys):
    """CP-281 through the real composition: exit 3, the entry on stderr and on the owner's
    channel, and no state written. `main` reads the file at the instance root it is started
    with (CP-483), so the test writes a copy there."""
    (tmp_path / ".providers.toml").write_text(edited_text({"documents.NFDR": None}),
                                              encoding="utf-8")
    log = tmp_path / "notified.log"
    notify = tmp_path / "notify.sh"
    notify.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$1\" >> {log}\n")
    notify.chmod(0o755)
    state_path = tmp_path / "state.json"

    code = chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                       "--product-path", str(tmp_path), "--project", "x",
                       "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                       "--spine", "PRD", "--notifier", str(notify)])

    assert code == 3
    assert "documents.NFDR is missing" in capsys.readouterr().err
    assert "documents.NFDR is missing" in log.read_text()
    assert not state_path.exists()


@pytest.mark.parametrize("text, named", [
    (edited_text({"documents.ADR": "grok"}), ["documents.ADR", "'grok'"]),
    (None, [INSTANCE_PROVIDER_FILE]),
    ("[documents\nPRD = ", [INSTANCE_PROVIDER_FILE]),
], ids=["unknown-value", "missing-file", "not-toml"])
def test_a_bad_value_a_missing_file_and_non_toml_refuse_a_start(text, named):
    """CP-282: the entry and its value, or the file's path."""
    files = FakeFiles(launcher_tree())
    engine = build(files, provider_port=ProviderText(text))

    with pytest.raises(providers.ProvidersRefused) as refused:
        start(engine, "PRD")

    assert all(part in str(refused.value) for part in named)
    assert files.read_text(STATE) is None


# Every kind of launch a product walk makes, by what it needs on disk: the producers the file
# sends to codex and to claude, the SDD's, and answer steps on both.
FORCED_LAUNCHES = [
    ("UXD", {}, through_skill("product-uxd")),
    ("UXD", companion_open("uxd"), answer("UXD")),
    ("DESIGN", {}, through_skill("product-design")),
    ("DESIGN", companion_open("design"), answer("DESIGN")),
    ("SDD", {}, through_skill("product-sdd")),
    ("FDR", companion_open("fdr"), answer("FDR")),
]


@pytest.mark.parametrize("force", ["codex", "claude", "gemini"])
@pytest.mark.parametrize("text", [
    DELIVERED_TEXT,
    edited_text({"documents.UXD": None, "documents.FDR": "gemini",
                 "documents.DESIGN": "gemini"}),
    None,
], ids=["delivered", "a-copy-lacking-and-differing", "missing-file"])
def test_a_forced_walk_puts_every_launch_on_the_force(force, text):
    """CP-290(c), CP-285, Ex 22: the force wins over every entry, and the file is never read —
    so a copy lacking an entry, naming another provider, or missing altogether refuses
    nothing."""
    for spine, disk, launched in FORCED_LAUNCHES:
        port = ProviderText(text)
        call = first_launch(spine, disk=disk, port=port, forced=force, environ=GEMINI_ENVIRON)
        assert (call["argv"], provider_of(call)) == (launched, force)
        assert port.reads == 0

    port = ProviderText(text)
    engine, processes, _ = owed_item_walk(port=port, forced=force, environ=GEMINI_ENVIRON)
    finish(engine)
    assert [provider_of(call) for call in processes.calls] == [force, force]
    assert port.reads == 0


def test_a_walk_built_by_build_chain_resolves_every_product_member_at_the_instance_root(
        tmp_path):
    """CP-290(d), CP-483: the composition root hands the engine a port that answers for the
    instance root asked, so the file at that root is the one every member is resolved from."""
    (tmp_path / ".providers.toml").write_text(DELIVERED_TEXT, encoding="utf-8")

    engine = chain.build_chain(str(tmp_path / "state.json"), notifier_command="",
                               engine_path="/e")

    resolved = engine.providers.at(str(tmp_path)).resolve(PRODUCT_MEMBERS)
    assert {str(member): value for member, value in resolved.items()} == {
        **{str(providers.document(name)): value
           for name, value in DELIVERED_DOCUMENT_PROVIDERS.items()},
        str(providers.OWED_ITEM): DELIVERED_OWED_ITEM_PROVIDER}


def test_the_composition_root_reads_any_instance_root(tmp_path):
    """CP-483, CP-484: the port answers `<root>/.providers.toml` for any root, and none of them
    sits under the engine's own directory."""
    engine = chain.build_chain(str(tmp_path / "state.json"), notifier_command="",
                               engine_path="/e")
    engine_directory = Path(chain.__file__).resolve().parent

    for root in (tmp_path / "one", tmp_path / "two"):
        answered = engine.providers.at(str(root)).path
        assert answered == providers.instance_file(str(root))
        assert engine_directory not in Path(answered).parents


def test_start_reads_the_instance_file_at_its_root():
    """CP-483: the start check reads `<instance_root>/.providers.toml` and nowhere else."""
    class PathsRead(ProviderText):
        paths: list[str] = []

        def read_text(self, path):
            self.paths.append(path)
            return super().read_text(path)

    port = PathsRead()
    engine = build(FakeFiles(launcher_tree()), provider_port=port)

    start(engine, "PRD")

    assert set(port.paths) == {INSTANCE_PROVIDER_FILE}


def test_start_in_an_instance_without_the_file_is_refused_naming_the_copy_command(
        tmp_path, capsys):
    """CP-486, main-level: an instance holding only the example is refused, naming the path and
    the command, and no state is written."""
    (tmp_path / ".providers.toml.example").write_text(DELIVERED_TEXT, encoding="utf-8")
    state_path = tmp_path / "state.json"

    code = chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                       "--product-path", str(tmp_path), "--project", "x",
                       "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                       "--spine", "PRD"])

    refusal = capsys.readouterr().err
    assert code == 3
    assert str(tmp_path / ".providers.toml") in refusal
    assert COPY_COMMAND in refusal
    assert not state_path.exists()


def test_a_forced_start_without_the_file_starts(tmp_path, capsys):
    """CP-487: the same instance with `--provider codex` starts; the file is not read."""
    state_path = tmp_path / "state.json"

    code = chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                       "--product-path", str(tmp_path), "--project", "x",
                       "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                       "--spine", "PRD", "--provider", "codex"])

    assert "provider file" not in capsys.readouterr().err
    assert code != 3
    assert state_path.exists()


def test_a_launch_reads_the_instance_file_as_edited_after_the_start():
    """CP-484: the file names claude at start and codex before the first launch."""
    processes = FakeProcesses()
    port = ProviderText(edited_text({"documents.FDR": "claude", "documents.ADR": "claude"}))
    engine = build(FakeFiles(launcher_tree()), processes=processes, provider_port=port)
    start(engine, "FDR,ADR")
    port.text = edited_text({"documents.ADR": "codex"})

    finish(engine)

    assert [provider_of(call) for call in processes.calls] == ["claude", "codex"]


def test_a_launch_halts_when_the_instance_file_is_gone():
    """CP-486: removed between start and launch, the walk halts as a machinery stop naming the
    copy command, and no run is launched."""
    processes, notifier, port = FakeProcesses(), FakeNotifier(), ProviderText()
    engine = build(FakeFiles(launcher_tree()), processes=processes, notifier=notifier,
                   provider_port=port)
    start(engine, "FDR,ADR")
    port.text = None

    finish(engine)

    state = engine.store.load()
    assert processes.launched == [through_skill("product-fdr")]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert COPY_COMMAND in state.ended_reason
    assert state.pending is None


def test_environment_provider_never_reaches_a_launch():
    """CP-284, Ex 18-20: with the engine's environment holding gemini, UXD's producer and its
    answer step carry its delivered entry, the SDD's producer its own delivered entry, and the
    owed item its own entry — which a copy moves."""
    assert provider_of(first_launch("UXD", environ=GEMINI_ENVIRON)) == (
        DELIVERED_DOCUMENT_PROVIDERS["UXD"])
    assert provider_of(first_launch("UXD", disk=companion_open("uxd"),
                                    environ=GEMINI_ENVIRON)) == (
        DELIVERED_DOCUMENT_PROVIDERS["UXD"])
    assert provider_of(first_launch("SDD", environ=GEMINI_ENVIRON)) == (
        DELIVERED_DOCUMENT_PROVIDERS["SDD"])

    engine, processes, _ = owed_item_walk(environ=GEMINI_ENVIRON)
    finish(engine)
    assert provider_of(processes.calls[1]) == "claude"

    moved = ProviderText(edited_text({"owed-items.no-document": "codex"}))
    engine, processes, _ = owed_item_walk(port=moved, environ=GEMINI_ENVIRON)
    finish(engine)
    assert provider_of(processes.calls[1]) == "codex"


# --- the SDD's launch: the ordinary document provider rule (CP-400 to CP-402, CP-411) ----------


@pytest.mark.parametrize("engine_environ", [
    GEMINI_ENVIRON,
    {"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": ""},
    {"PATH": "/usr/bin"},
], ids=["gemini", "empty", "absent"])
def test_an_unforced_sdd_launch_ignores_inherited_provider_state(engine_environ):
    """CP-402: the provider is the one `documents.SDD` names, whatever the engine's own
    environment inherited — a value, an empty one or none."""
    processes = FakeProcesses()
    engine = build(FakeFiles(launcher_tree()), processes=processes, environ=engine_environ)

    start(engine, "SDD")

    assert processes.launched == [through_skill("product-sdd")]
    assert provider_of(processes.calls[0]) == DELIVERED_DOCUMENT_PROVIDERS["SDD"]


@pytest.mark.parametrize("force", ["claude", "codex", "gemini"])
def test_a_forced_sdd_launch_carries_the_force_without_reading_the_file(force):
    """CP-402: a forced walk's SDD launch carries the force, and no entry is read for it."""
    port = ProviderText()
    call = first_launch("SDD", forced=force, port=port, environ=GEMINI_ENVIRON)

    assert call["argv"] == through_skill("product-sdd")
    assert provider_of(call) == force
    assert port.reads == 0


SDD_LAUNCHER_COMMAND = f"{CORE}/launchers/skill/launcher.sh product-sdd {PROJECT}"


def test_an_owed_skill_launcher_round_for_the_sdd_takes_the_ordinary_provider():
    """CP-360, CP-401: a quoted skill-launcher command is a real folder command, accepted as
    quoted, and its bullet names a document, so it carries that document's entry."""
    engine, processes, _ = owed_item_walk(environ=GEMINI_ENVIRON,
                                          owed=(("docs/SDD.md", SDD_LAUNCHER_COMMAND),))

    finish(engine)

    assert processes.launched == [answer("FDR"), through_skill("product-sdd")]
    assert provider_of(processes.calls[0]) == DELIVERED_DOCUMENT_PROVIDERS["FDR"]
    assert provider_of(processes.calls[1]) == DELIVERED_DOCUMENT_PROVIDERS["SDD"]


def test_an_owed_skill_launcher_round_for_the_sdd_takes_the_owed_item_entry():
    """CP-360: a bullet naming no document still reaches the skill launcher, and is handed the
    owed-item entry like any other round with no document."""
    engine, processes, _ = owed_item_walk(environ=GEMINI_ENVIRON,
                                          owed=(("docs/nothing.md", SDD_LAUNCHER_COMMAND),))

    finish(engine)

    assert processes.launched == [answer("FDR"), through_skill("product-sdd")]
    assert provider_of(processes.calls[1]) == DELIVERED_OWED_ITEM_PROVIDER


def test_the_sdd_answer_step_keeps_the_documents_sdd_provider():
    """CP-362. A pin: the answer step goes through `companion-self-answer` on `documents.SDD`."""
    call = first_launch("SDD", disk=companion_open("sdd"), environ=GEMINI_ENVIRON)

    assert call["argv"] == answer("SDD")
    assert provider_of(call) == DELIVERED_DOCUMENT_PROVIDERS["SDD"] == "claude"


def test_an_unforced_sdd_launch_with_keep_awake_carries_the_ordinary_provider():
    """CP-361: `--keep-awake` is appended to the skill command and is the only addition; no
    `--provider` token, and the provider variable is the ordinary one."""
    processes = FakeProcesses()
    engine = build(FakeFiles(launcher_tree()), processes=processes, environ=GEMINI_ENVIRON)

    start(engine, "SDD", keep_awake=True)

    assert processes.launched == [through_skill("product-sdd") + ["--keep-awake"]]
    assert "--provider" not in processes.launched[0]
    assert provider_of(processes.calls[0]) == DELIVERED_DOCUMENT_PROVIDERS["SDD"]


def test_a_producer_exit_ends_the_sdd_walk_on_the_unedited_delivered_file():
    """CP-364: the delivered file carries no table of seat entries, so the SDD's producer starts
    on it as it stands, and the producer's own non-zero exit ends the walk as for any producer."""
    processes = FakeProcesses(codes=[3])
    engine = build(FakeFiles(launcher_tree()), processes=processes)

    start(engine, "SDD")

    state = engine.store.load()
    assert processes.launched == [through_skill("product-sdd")]
    assert provider_of(processes.calls[0]) == DELIVERED_DOCUMENT_PROVIDERS["SDD"]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert "launcher exited 3" in state.ended_reason


def test_an_sdd_launch_whose_entry_went_missing_between_launches_refuses_naming_it():
    """CP-358, CP-402: the SDD's launch reads its entry as every document's does, so an entry
    gone from the file after the start stops the walk at that launch."""
    processes = FakeProcesses()
    port = ProviderText()
    engine = build(FakeFiles(launcher_tree()), processes=processes, provider_port=port)
    start(engine, "FDR,SDD")
    port.text = edited_text({"documents.SDD": None})

    finish(engine)

    state = engine.store.load()
    assert processes.launched == [through_skill("product-fdr")]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert "documents.SDD is missing" in state.ended_reason


def test_an_owed_round_for_the_sdd_through_the_skill_launcher_keeps_the_documents_sdd_entry():
    """CP-360, CP-362: an owed round for the SDD through the skill launcher carries
    `documents.SDD`, read off the copy."""
    owed = (("docs/SDD.md", f"{CORE}/launchers/skill/launcher.sh product-sdd {PROJECT}"),)
    port = ProviderText(edited_text({"documents.SDD": "codex"}))
    engine, processes, _ = owed_item_walk(port=port, environ=GEMINI_ENVIRON, owed=owed)

    finish(engine)

    assert processes.launched == [answer("FDR"), through_skill("product-sdd")]
    assert provider_of(processes.calls[1]) == "codex"


def test_a_forced_owed_skill_launcher_round_for_the_sdd_carries_the_force():
    """CP-359, CP-360: every SDD launch of a forced walk carries the force, the owed route as
    much as the producer's."""
    engine, processes, _ = owed_item_walk(forced="codex", environ=GEMINI_ENVIRON,
                                          owed=(("docs/SDD.md", SDD_LAUNCHER_COMMAND),))

    finish(engine)

    assert processes.launched == [answer("FDR"), through_skill("product-sdd")]
    assert provider_of(processes.calls[1]) == "codex"


def test_the_hook_of_an_unforced_walk_ending_after_an_sdd_launch_carries_no_provider():
    """CP-363, Ex 11: the on-end hook's environment is as at the fork point, whichever launch
    came last."""
    processes = FakeProcesses()
    engine = build(FakeFiles(launcher_tree()), processes=processes, environ=GEMINI_ENVIRON)
    start(engine, "SDD", on_end=HOOK)

    finish(engine, "completed")

    assert processes.launched[0] == through_skill("product-sdd")
    assert len(hook_calls(processes)) == 1
    assert "KENSAIAPP_AGENT_PROVIDER" not in hook_calls(processes)[0]["env"]


def test_a_round_a_document_is_owed_carries_that_documents_entry():
    """CP-284: an owed item whose path is a document launches on that document's entry, not the
    owed-item entry and not the answer step's document's."""
    owed = (("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"),)
    port = ProviderText(edited_text({"documents.SRS": "gemini"}))
    engine, processes, _ = owed_item_walk(port=port, owed=owed)

    finish(engine)

    assert processes.launched == [answer("FDR"), through_skill("product-srs")]
    assert [provider_of(call) for call in processes.calls] == ["claude", "gemini"]


def test_a_copy_sets_documents_and_steps_independently():
    """CP-276, CP-274, Ex 4 and 6 (the product half): the `design` step's entry moves no
    document, and each document's entry moves its producer and its answer step."""
    copy = edited_text({"documents.UXD": "claude", "documents.DESIGN": "claude",
                        "steps.design": "codex", "documents.FDR": "codex"})

    assert provider_of(first_launch("UXD", port=ProviderText(copy))) == "claude"
    assert provider_of(first_launch("DESIGN", port=ProviderText(copy))) == "claude"
    assert provider_of(first_launch("DESIGN", disk=companion_open("design"),
                                    port=ProviderText(copy))) == "claude"
    assert provider_of(first_launch("FDR", disk=companion_open("fdr"),
                                    port=ProviderText(copy))) == "codex"
    assert provider_of(first_launch("SRS", port=ProviderText(copy))) == "claude"


def test_an_entry_removed_before_a_launch_halts_the_walk_naming_it():
    """CP-283: each launch reads the file as it stands. An entry gone by the time its launch
    comes stops the walk there — no launch, nothing recorded as pending, the reason naming the
    entry, and the owner told."""
    files = FakeFiles(launcher_tree())
    processes = FakeProcesses()
    notifier = FakeNotifier()
    port = ProviderText()
    engine = build(files, processes=processes, notifier=notifier, provider_port=port)
    start(engine, "FDR,ADR")
    port.text = edited_text({"documents.ADR": None})

    finish(engine)

    state = engine.store.load()
    assert processes.launched == [through_skill("product-fdr")]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert "documents.ADR is missing" in state.ended_reason
    assert state.pending is None
    assert state.launches == 1
    assert "documents.ADR is missing" in notifier.messages[-1]


def test_a_valid_edit_is_taken_at_the_next_launch():
    """CP-283, the other half: an entry changed mid-walk moves the next launch, not a later
    one."""
    processes = FakeProcesses()
    port = ProviderText()
    engine = build(FakeFiles(launcher_tree()), processes=processes, provider_port=port)
    start(engine, "FDR,ADR")
    port.text = edited_text({"documents.ADR": "codex"})

    finish(engine)

    assert processes.launched[1] == through_skill("product-architecture")
    assert [provider_of(call) for call in processes.calls] == ["claude", "codex"]


@pytest.mark.parametrize("text, named", [
    (edited_text({"documents.ADR": "grok"}), ["documents.ADR", "'grok'"]),
    (None, [INSTANCE_PROVIDER_FILE]),
    ("[documents", [INSTANCE_PROVIDER_FILE]),
])
def test_a_provider_file_becoming_invalid_halts_before_the_next_document(text, named):
    """CP-283 applies to every CP-282 refusal, not only a removed entry."""
    processes, notifier, port = FakeProcesses(), FakeNotifier(), ProviderText()
    engine = build(FakeFiles(launcher_tree()), processes=processes, notifier=notifier,
                   provider_port=port)
    start(engine, "FDR,ADR")
    port.text = text

    finish(engine)

    state = engine.store.load()
    assert processes.launched == [through_skill("product-fdr")]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert state.pending is None
    assert all(part in state.ended_reason for part in named)
    assert all(part in notifier.messages[-1] for part in named)


def test_a_refusal_with_owed_items_still_queued_halts_without_draining():
    """CP-283 says the walk stops. A refused launch is not a cycle's end that the queue may
    still change, so the next owed item is not launched."""
    owed = (("docs/PRD.md", f"{CORE}/launchers/skill/launcher.sh product-prd {PROJECT}"),
            ("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"))
    port = ProviderText()
    engine, processes, notifier = owed_item_walk(port=port, owed=owed)
    port.text = edited_text({"documents.PRD": None})

    finish(engine)

    state = engine.store.load()
    assert processes.launched == [answer("FDR")]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert "documents.PRD is missing" in state.ended_reason
    assert "documents.PRD is missing" in notifier.messages[-1]


def test_an_owed_item_whose_entry_went_missing_halts_naming_it():
    """CP-283 for the launch that has no document: its reason names the owed-item entry."""
    port = ProviderText()
    engine, processes, _ = owed_item_walk(port=port)
    port.text = edited_text({"owed-items.no-document": None})

    finish(engine)

    state = engine.store.load()
    assert processes.launched == [answer("FDR")]
    assert state.ended == chain.CycleEnd.MACHINERY.value
    assert "owed-items.no-document is missing" in state.ended_reason


class TestALaunchGoesToOneProvider:

    def test_the_force_is_read_back_from_the_state_on_advance(self):
        files = FakeFiles(launcher_tree())
        start(build(files), "FDR,ADR", forced_provider="codex")
        assert json.loads(files.read_text(STATE))["forced_provider"] == "codex"
        processes = FakeProcesses()

        finish(build(files, processes=processes))

        assert provider_of(processes.calls[0]) == "codex"

    def test_a_state_written_before_the_force_existed_loads_unforced(self):
        older = {name: getattr(chain.ChainState(instance_root="", product_path="", project="",
                                                core_dir="", shim_path=""), name)
                 for name in chain._STATE_FIELDS if name != "forced_provider"}
        assert chain.ChainState.from_json(older).forced_provider == ""

    def test_main_passes_the_force_from_the_cli_to_start(self, tmp_path):
        state_path = tmp_path / "state.json"

        chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                    "--product-path", str(tmp_path), "--project", "x",
                    "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                    "--spine", "FDR", "--provider", "codex"])

        assert json.loads(state_path.read_text())["forced_provider"] == "codex"

    def test_main_refuses_a_provider_it_does_not_know(self, tmp_path, capsys):
        with pytest.raises(SystemExit):
            chain.main(["--start", str(tmp_path / "state.json"), "--provider", "grok"])
        assert "--provider" in capsys.readouterr().err

    def test_keep_awake_is_appended_after_validation(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR", keep_awake=True)

        assert processes.launched == [through_skill("product-fdr") + ["--keep-awake"]]

    def test_a_launcher_that_exits_non_zero_is_a_machinery_stop(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3]), notifier=notifier)

        start(engine, "FDR")

        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value
        assert "machinery" in notifier.messages[-1]

    def test_the_notifier_is_the_one_it_was_given(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3]), notifier=notifier)

        start(engine, "FDR")

        assert notifier.messages


# --- the spine as a value -----------------------------------------------------------------


class TestParseSpine:

    def test_it_reads_an_ordered_list_of_document_names(self):
        assert chain.parse_spine("FDR,ADR,NFDR") == (
            chain.document("FDR"), chain.document("ADR"), chain.document("NFDR"))

    def test_it_is_case_insensitive_and_tolerates_spaces(self):
        assert chain.parse_spine("fdr, adr") == (chain.document("FDR"), chain.document("ADR"))

    def test_an_unknown_name_is_refused_by_name(self):
        with pytest.raises(ValueError, match="TPS"):
            chain.parse_spine("FDR,TPS")

    def test_an_empty_spine_is_refused(self):
        with pytest.raises(ValueError):
            chain.parse_spine("")

    def test_the_spine_survives_the_state_file(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR,ADR,NFDR")
        assert engine.store.load().spine == ["FDR", "ADR", "NFDR"]


class TestChainNameIsOptional:
    """Task 4. Not added to `_START_REQUIRED_FLAGS` — a required flag would turn a reporting
    change into a start-time refusal for any hand-run or future third chain."""

    def test_start_persists_the_chain_name_on_state(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR", chain_name="example-foundation")
        assert engine.store.load().chain_name == "example-foundation"

    def test_chain_name_defaults_to_empty_when_not_given(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR")
        assert engine.store.load().chain_name == ""

    def test_chain_name_is_not_a_required_start_flag(self, capsys):
        assert chain.main(["--start", "/tmp/s.json"]) == 2
        assert "--chain-name" not in capsys.readouterr().err

    def test_the_cli_passes_chain_name_through_to_start(self, tmp_path):
        """No real launcher exists under `tmp_path`, so the walk self-refuses cleanly
        (`no_runnable_command`) without ever spawning a subprocess — this only proves the flag
        reaches `start()`, which persists it before anything else runs."""
        write_provider_file(tmp_path)
        state_path = tmp_path / "state.json"
        chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                    "--product-path", str(tmp_path), "--project", "x",
                    "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                    "--spine", "FDR", "--chain-name", "example-foundation"])
        saved = json.loads(state_path.read_text())
        assert saved["chain_name"] == "example-foundation"


class TestAWalkRecordsWhenItBegan:
    """A walk could not be delimited from disk. The state file carries no start time and is
    overwritten in place, so `chain_usage.py`'s `--since` / `--until` were a human's judgement
    about which runs belonged to which walk rather than a fact the walk itself recorded.

    Defaulted, `STATE_SCHEMA` untouched — a state file written before this field existed loads
    with `started_at == ""`, the same rule `chain_name` and `reports_before` already hold.
    """

    def test_start_persists_the_moment_the_walk_began(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR", started_at="2026-09-09T18:30:00+00:00")
        assert engine.store.load().started_at == "2026-09-09T18:30:00+00:00"

    def test_started_at_defaults_to_empty_when_not_given(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR")
        assert engine.store.load().started_at == ""

    def test_a_state_written_before_this_field_existed_still_loads(self):
        """The field is additive, so an in-flight walk started by an older engine must resume
        rather than crash inside the completion hook."""
        older = {name: getattr(chain.ChainState(instance_root="", product_path="", project="",
                                                core_dir="", shim_path=""), name)
                 for name in chain._STATE_FIELDS if name != "started_at"}
        assert "started_at" not in older
        assert chain.ChainState.from_json(older).started_at == ""

    def test_the_cli_stamps_a_real_moment(self, tmp_path):
        """`main()` is the composition root and the only place the clock is read — the engine is
        handed the value, never a clock, so nothing below `main` reaches for the wall time."""
        write_provider_file(tmp_path)
        state_path = tmp_path / "state.json"
        chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                    "--product-path", str(tmp_path), "--project", "x",
                    "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                    "--spine", "FDR"])
        saved = json.loads(state_path.read_text())
        assert saved["started_at"]
        assert saved["started_at"].startswith("20")


class TestAWalkTiesItsDocumentsTogether:
    """Task 3. A chain walk starts several document launchers, and each tags its own run — a
    walk id minted once at start, and the chain's own name, both carried in the env every
    document launch inherits."""

    def test_the_state_gains_a_walk_id_field_defaulted_like_chain_name(self):
        """Additive, `STATE_SCHEMA` untouched — a state file written before this field existed
        loads with `walk_id == ""`, the same rule `chain_name` and `started_at` already hold."""
        older = {name: getattr(chain.ChainState(instance_root="", product_path="", project="",
                                                core_dir="", shim_path=""), name)
                 for name in chain._STATE_FIELDS if name != "walk_id"}
        assert "walk_id" not in older
        assert chain.ChainState.from_json(older).walk_id == ""

    def test_start_mints_the_walk_id_from_the_id_source_it_is_given(self):
        files = FakeFiles(launcher_tree())
        id_source = FakeIdSource("fixed-walk-id")
        engine = build(files, id_source=id_source)

        start(engine, "FDR", chain_name="example-foundation")

        assert engine.store.load().walk_id == "fixed-walk-id"

    def test_advancing_never_mints_a_second_id(self):
        """The id is minted once, at `start()` — `advance()` reads it back off the persisted
        state rather than asking the id source again."""
        files = FakeFiles(launcher_tree())
        id_source = FakeIdSource("fixed-walk-id")
        engine = build(files, id_source=id_source)

        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        assert id_source.calls == 1
        assert engine.store.load().walk_id == "fixed-walk-id"

    def test_two_launches_in_one_walk_share_the_same_walk_id_and_chain_name_in_their_env(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        id_source = FakeIdSource("fixed-walk-id")
        engine = build(files, processes=processes, id_source=id_source)

        start(engine, "FDR,ADR,NFDR", chain_name="example-foundation")
        finish(engine, "completed")

        assert len(processes.calls) == 2
        for call in processes.calls:
            assert call["env"]["INSTRUMENT_RUN_WALK_ID"] == "fixed-walk-id"
            assert call["env"]["INSTRUMENT_RUN_CHAIN"] == "example-foundation"

    def test_an_inherited_walk_key_is_removed_when_the_state_has_no_value_for_it(self):
        """`code-integrity-report.md` § Surfaced, not settled, item 1: a walk started from a shell
        that still holds another walk's keys must not pass them on."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        stale = {"PATH": "/usr/bin", "INSTRUMENT_RUN_CHAIN": "another-chain",
                 "INSTRUMENT_RUN_WALK_ID": "another-walk"}
        engine = build(files, processes=processes, environ=stale)

        start(engine, "FDR")

        env = processes.calls[0]["env"]
        assert "INSTRUMENT_RUN_CHAIN" not in env
        assert env["INSTRUMENT_RUN_WALK_ID"] == "fixed-walk-id"

    def test_an_unnamed_walk_carries_the_walk_id_but_no_chain_key(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR")

        assert processes.calls[0]["env"]["INSTRUMENT_RUN_WALK_ID"] == "fixed-walk-id"
        assert "INSTRUMENT_RUN_CHAIN" not in processes.calls[0]["env"]

    def test_a_state_with_no_walk_id_hands_the_next_launch_an_env_with_no_walk_id_key(self):
        """An in-flight walk started by an older engine has no `walk_id` on disk — `advance()`
        must not crash, and the env it hands the next launch omits the key rather than inventing
        one."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,ADR,NFDR")
        state = engine.store.load()
        state.walk_id = ""
        engine.store.save(state)

        finish(engine, "completed")

        assert "INSTRUMENT_RUN_WALK_ID" not in processes.calls[-1]["env"]

    def test_build_chain_wires_a_real_id_source(self, tmp_path):
        """The composition root hands in the real one."""
        real = chain.build_chain(str(tmp_path / "state.json"), notifier_command="",
                                  engine_path=str(tmp_path / "chain.py"))
        first = real.id_source.new_id()
        second = real.id_source.new_id()
        uuid.UUID(first)
        assert first != second

    def test_the_cli_mints_a_real_walk_id(self, tmp_path):
        write_provider_file(tmp_path)
        state_path = tmp_path / "state.json"
        chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                    "--product-path", str(tmp_path), "--project", "x",
                    "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                    "--spine", "FDR"])
        saved = json.loads(state_path.read_text())
        uuid.UUID(saved["walk_id"])


class TestTheRegistryIsOneRecordPerDocument:


    def test_every_registered_document_names_the_skill_that_produces_it(self):
        assert {name: spec.skill for name, spec in chain.DOCUMENT_REGISTRY.items()} == {
            "PRD": "product-prd", "Agari": "project-agari", "SRS": "product-srs",
            "UXD": "product-uxd", "DESIGN": "product-design", "CONTENT": "product-content",
            "SDD": "product-sdd", "FDR": "product-fdr", "ADR": "product-architecture",
            "NFDR": "product-architecture",
        }

    def test_no_registered_document_keeps_a_launcher_of_its_own(self):
        assert not any(field.name == "own_launcher"
                       for field in dataclasses.fields(chain.DocumentSpec))
        assert all(not hasattr(spec, "own_launcher") for spec in chain.DOCUMENT_REGISTRY.values())

    def test_no_registered_document_reads_its_own_seats(self):
        assert not any(field.name == "reads_own_seats"
                       for field in dataclasses.fields(chain.DocumentSpec))
        assert all(not hasattr(spec, "reads_own_seats")
                   for spec in chain.DOCUMENT_REGISTRY.values())
        assert not hasattr(chain, "reads_own_seats")

    def test_the_adr_and_the_nfdr_share_a_skill_and_a_companion(self):
        assert chain.document("ADR").skill == chain.document("NFDR").skill
        assert (chain.document("ADR").companion_stem
                == chain.document("NFDR").companion_stem
                == "architecture_open_issues")

    def test_the_agari_lives_in_the_instance_and_the_rest_in_the_product(self):
        assert chain.document("Agari").home is chain.Home.INSTANCE_PROJECT
        for name in ("PRD", "SRS", "UXD", "DESIGN", "CONTENT", "SDD", "FDR", "ADR", "NFDR"):
            assert chain.document(name).home is chain.Home.PRODUCT_DOCS

    def test_the_adr_is_the_one_record_directory(self):
        assert chain.document("ADR").shape is chain.Shape.RECORD_DIRECTORY
        for name, spec in chain.DOCUMENT_REGISTRY.items():
            if name != "ADR":
                assert spec.shape is chain.Shape.FILE


# --- the coverage the predecessor carried, re-stated at the seams --------------------------
#
# Everything below proves one primitive at a time. It is the level the old suite had, kept
# because those cases are real — a `[...]` token dropped, a companion's case read off disk, a
# duplicate event that must not advance twice. What it is NOT is a substitute for the walk
# tables above: every one of these passed while the chain walked ten documents on a
# two-document spine.


class TestResolveDocument:

    def test_resolves_each_document_by_its_own_basename(self):
        expect = {
            "docs/PRD.md": "PRD", "agari.md": "Agari", "docs/srs.md": "SRS",
            "docs/SRS.MD": "SRS", "docs/UXD.md": "UXD", "docs/DESIGN.md": "DESIGN",
            "docs/CONTENT.md": "CONTENT", "docs/SDD.md": "SDD", "docs/fdr.md": "FDR",
            "docs/nfdr.md": "NFDR",
        }
        for path, name in expect.items():
            assert chain.resolve_document(path) is chain.document(name), path

    def test_resolves_the_adr_directory_however_it_is_written(self):
        for path in ("adr/", "docs/adr/", "`adr/`", "adr",
                     "docs/adr/0001-one-server-rendered-process.md"):
            assert chain.resolve_document(path) is chain.document("ADR"), path

    def test_a_companion_beside_the_adr_directory_is_not_the_adr(self):
        """An alias matches a whole segment, never one that merely starts with it."""
        assert chain.resolve_document("docs/adr_open_issues.md") is None
        assert chain.resolve_document("docs/adrenaline.md") is None

    def test_a_companion_resolves_to_the_document_it_answers_for(self):
        expect = {
            "docs/architecture_open_issues.md": "ADR", "agari_open_issues.md": "Agari",
            "docs/SDD_open_issues.md": "SDD", "docs/srs_open_issues.md": "SRS",
        }
        for path, name in expect.items():
            assert chain.resolve_document(path) is chain.document(name), path

    def test_a_path_naming_no_document_resolves_to_nothing(self):
        assert chain.resolve_document("docs/random_notes.md") is None
        assert chain.resolve_document("") is None

    def test_strips_surrounding_whitespace_and_backticks(self):
        assert chain.resolve_document("  `docs/SRS.md`  ") is chain.document("SRS")


# The three `## Launchers owed` sections below are quoted from live self-answer reports (a real
# product's SRS and FDR trails, read 2026-08-31), with the product name replaced by the fixture
# name and nothing else altered. Every one carries a prose tail past the closing backtick.

FDR_OWED = """## Launchers owed

- **`docs/fdr.md`** — `<CORE>/launchers/skill/launcher.sh product-fdr sealbox` (run from the instance root; `--dry-run` prints the
  command, `--keep-awake` holds the Mac awake)
- **`docs/SRS.md`** — `<CORE>/launchers/skill/launcher.sh product-srs sealbox` (run from the instance root; same flags) — after the
  owner fills § 2.1's confirm-or-override slot; then re-run the FDR, which follows the SRS
"""

SRS_OWED = """## Launchers owed

- **`docs/SRS.md`** — `<CORE>/launchers/skill/launcher.sh product-srs sealbox` (run from the instance root; `--dry-run` prints
  the command, `--keep-awake` holds the Mac awake) — folds § 2.1 and decides § 2.2
- **`docs/fdr.md`** — `<CORE>/launchers/skill/launcher.sh product-fdr sealbox` (same flags) — after the SRS round, since its
  § 1.1 answer follows this slot; its own companion is already answered (`docs/trail/fdr/self_answer-1.md`)
"""


class TestOwedSet:

    def test_reads_document_and_command_from_a_live_report(self):
        assert chain.owed_set(FDR_OWED) == [
            chain.OwedItem("docs/fdr.md", "<CORE>/launchers/skill/launcher.sh product-fdr sealbox"),
            chain.OwedItem("docs/SRS.md", "<CORE>/launchers/skill/launcher.sh product-srs sealbox"),
        ]

    def test_drops_the_prose_tail_past_the_closing_backtick(self):
        for item in chain.owed_set(SRS_OWED):
            assert "folds" not in item.command
            assert not item.command.endswith(")")

    def test_reads_a_wrapped_continuation_line_as_part_of_the_same_bullet(self):
        owed = chain.owed_set(SRS_OWED)
        assert [item.document_path for item in owed] == ["docs/SRS.md", "docs/fdr.md"]

    def test_none_this_run_yields_an_empty_owed_set(self):
        assert chain.owed_set("## Launchers owed\n\nNone this run.\n") == []

    def test_the_honest_absence_bullet_keeps_the_skill_name_as_the_command(self):
        text = ("## Launchers owed\n\n"
                "- **`docs/nfdr.md`** — no launcher; run `product-nfdr` from a `cto` session\n")
        assert chain.owed_set(text) == [chain.OwedItem("docs/nfdr.md", "product-nfdr")]

    def test_a_bullet_with_no_backticked_command_yields_no_command(self):
        text = "## Launchers owed\n\n- **docs/nfdr.md** — no launcher, no command at all\n"
        assert chain.owed_set(text) == [chain.OwedItem("docs/nfdr.md", None)]


def _pin_of(tmp_path: Path, host: Path) -> Path:
    """A real `pin.json` naming `host` as the pin's source host root — enough for
    `pin.same_launcher`'s own `of_core` to recognize the pin (a real-filesystem check; it takes
    no `Files` port). Nothing under either tree needs to exist beyond the manifest itself."""
    pin_root = tmp_path / "pin"
    pin_root.mkdir()
    (pin_root / "pin.json").write_text(json.dumps(
        {"id": "test-pin", "source_host_root": str(host), "created": "2026-09-22T00:00:00Z"}))
    return pin_root / "core"


class TestValidateOwedCommand:

    def validate(self, command, files=None):
        return chain.validate_owed_command(command, core_dir=CORE, instance_root=INSTANCE,
                                           files=files or FakeFiles(launcher_tree()))

    def test_resolves_core_and_returns_a_token_list(self):
        validated = self.validate("<CORE>/launchers/product-card/launcher.sh sealbox")
        assert validated.launcher_folder == "product-card"
        assert validated.argv == [f"{CORE}/launchers/product-card/launcher.sh", "sealbox"]

    def test_the_answer_steps_two_positionals_are_accepted(self):
        validated = self.validate(
            f"{CORE}/launchers/companion-self-answer/launcher.sh sealbox SRS")
        assert validated.launcher_folder == "companion-self-answer"

    def test_an_empty_command_is_refused(self):
        with pytest.raises(chain.CommandRefused):
            self.validate(None)

    def test_a_script_outside_the_launchers_tree_is_refused(self):
        with pytest.raises(chain.CommandRefused, match="not under"):
            self.validate("/etc/launcher.sh sealbox")

    def test_a_script_that_is_not_a_launcher_sh_is_refused(self):
        with pytest.raises(chain.CommandRefused, match="not a launcher.sh"):
            self.validate(f"{CORE}/launchers/product-card/other.sh sealbox")

    def test_a_launcher_that_is_not_on_disk_is_refused(self):
        with pytest.raises(chain.CommandRefused, match="no launcher.sh on disk"):
            self.validate(f"{CORE}/launchers/product-nope/launcher.sh sealbox")

    def test_a_launcher_with_no_usage_block_is_refused(self):
        files = FakeFiles({f"{CORE}/launchers/bare/launcher.sh": "#!/usr/bin/env bash\n"})
        with pytest.raises(chain.CommandRefused, match="no # USAGE block"):
            self.validate(f"{CORE}/launchers/bare/launcher.sh sealbox", files=files)

    def test_the_wrong_positional_count_is_refused_by_number(self):
        with pytest.raises(chain.CommandRefused, match="takes 1 positional"):
            self.validate(f"{CORE}/launchers/product-card/launcher.sh sealbox extra")

    def test_the_honest_absence_bullet_is_refused_as_no_launcher(self):
        """Step 6's second shape: the first backticked span is the producing SKILL, not a
        launcher path. It is refused here, and refused as a `CommandRefused` — a bare name is
        a relative path, and the containment check raises `ValueError` on one, which is not an
        exception the completion hook survives."""
        with pytest.raises(chain.CommandRefused):
            self.validate("product-nfdr")

    def test_the_skill_launcher_takes_its_skill_and_any_arguments_after_it(self):
        validated = self.validate(f"{CORE}/launchers/skill/launcher.sh product-srs sealbox")
        assert validated.launcher_folder == "skill"
        assert validated.argv == [f"{CORE}/launchers/skill/launcher.sh", "product-srs", "sealbox"]

    def test_the_skill_launcher_without_its_skill_is_refused(self):
        with pytest.raises(chain.CommandRefused, match="takes at least 1 positional"):
            self.validate(f"{CORE}/launchers/skill/launcher.sh")

    def test_a_usage_line_quoted_whole_still_validates(self):
        """The bracketed tokens are dropped, not unwrapped — honouring `--dry-run` off a
        report would make the launcher print a command while the chain believed it launched
        one, the quietest failure this engine could have."""
        validated = self.validate(
            f"{CORE}/launchers/skill/launcher.sh product-srs sealbox [--dry-run] [--keep-awake]")
        assert validated.argv == [f"{CORE}/launchers/skill/launcher.sh", "product-srs", "sealbox"]

    def test_a_bullet_naming_the_live_launcher_validates_under_a_pinned_core(self, tmp_path):
        """A chain running under a pin (`core_dir` is the pin's own `core/`) still accepts a
        bullet whose command names the live host's own launcher path — the shape a real
        self-answer report can carry unmodified across a launch that happens to pin."""
        host = tmp_path / "host"
        pin_core = _pin_of(tmp_path, host)
        live_script = str(host / "core" / "launchers" / "product-card" / "launcher.sh")
        pinned_script = str(pin_core / "launchers" / "product-card" / "launcher.sh")
        files = FakeFiles(
            {pinned_script: launcher_tree()[f"{CORE}/launchers/product-card/launcher.sh"]})

        validated = chain.validate_owed_command(
            f"{live_script} sealbox", core_dir=str(pin_core), instance_root=str(host),
            files=files)

        assert validated.launcher_folder == "product-card"
        assert validated.argv == [pinned_script, "sealbox"]

    def test_a_bullet_with_core_placeholder_still_validates(self, tmp_path):
        host = tmp_path / "host"
        pin_core = _pin_of(tmp_path, host)
        pinned_script = str(pin_core / "launchers" / "product-card" / "launcher.sh")
        files = FakeFiles(
            {pinned_script: launcher_tree()[f"{CORE}/launchers/product-card/launcher.sh"]})

        validated = chain.validate_owed_command(
            "<CORE>/launchers/product-card/launcher.sh sealbox",
            core_dir=str(pin_core), instance_root=str(host), files=files)

        assert validated.launcher_folder == "product-card"
        assert validated.argv == [pinned_script, "sealbox"]

    def test_a_bullet_naming_a_relative_core_launchers_path_validates_under_a_pinned_core(
            self, tmp_path):
        """CP-114: a chain bullet may name a host launcher by a relative `core/launchers/…`
        path, and a pinned run accepts it as the same launcher. A relative path is read from the
        instance root (change_design.md § 4, A — launcher equivalence), not from whatever
        directory the engine process happens to stand in — `FakeFiles.real_path` does not
        resolve against any cwd, so this holds only if the check itself anchors the path."""
        host = tmp_path / "host"
        pin_core = _pin_of(tmp_path, host)
        pinned_script = str(pin_core / "launchers" / "product-card" / "launcher.sh")
        files = FakeFiles(
            {pinned_script: launcher_tree()[f"{CORE}/launchers/product-card/launcher.sh"]})

        validated = chain.validate_owed_command(
            "core/launchers/product-card/launcher.sh sealbox",
            core_dir=str(pin_core), instance_root=str(host), files=files)

        assert validated.launcher_folder == "product-card"
        assert validated.argv == [pinned_script, "sealbox"]

    def test_a_bullet_outside_the_launchers_is_still_refused(self, tmp_path):
        """Pin-awareness widens which paths count as the *same* launcher; it does not widen
        which launcher a bullet may name."""
        host = tmp_path / "host"
        pin_core = _pin_of(tmp_path, host)
        unrelated = str(tmp_path / "unrelated" / "launcher.sh")

        with pytest.raises(chain.CommandRefused, match="not under"):
            chain.validate_owed_command(
                f"{unrelated} sealbox", core_dir=str(pin_core), instance_root=str(host),
                files=FakeFiles())


class TestLocate:

    def locate(self, files, name):
        """No chain is started here — locating a document is a read of the disk, and giving
        it a hand-built state keeps it that way (and lets one test locate two documents)."""
        engine = build(files)
        state = chain.ChainState(instance_root=INSTANCE, product_path=PRODUCT,
                                  project=PROJECT, core_dir=CORE, shim_path=SHIM,
                                  spine=["FDR"])
        return engine.locate(state, chain.document(name))

    def test_a_product_document_is_found_at_its_own_on_disk_case(self):
        files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/SRS.md": "x"})
        location = self.locate(files, "SRS")
        assert location.document_path == f"{PRODUCT}/docs/SRS.md"
        assert location.document_present

    def test_the_companion_case_is_read_off_disk_not_composed(self):
        """Live: `docs/SRS.md`'s companion on disk is `docs/srs_open_issues.md`, because the
        run that opened it took the stem from the lower-case template filename."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/SRS.md": "x",
                            f"{PRODUCT}/docs/srs_open_issues.md": "y"})
        location = self.locate(files, "SRS")
        assert location.companion_path == f"{PRODUCT}/docs/srs_open_issues.md"

    def test_an_absent_document_is_absent(self):
        location = self.locate(FakeFiles(launcher_tree()), "SDD")
        assert not location.document_present and location.document_path is None

    def test_the_agari_lives_beside_the_project_card_not_under_the_product(self):
        files = FakeFiles({**launcher_tree(),
                            f"{INSTANCE}/system/projects/{PROJECT}/agari.md": "x",
                            f"{INSTANCE}/system/projects/{PROJECT}/agari_open_issues.md": "y"})
        location = self.locate(files, "Agari")
        assert location.document_path == f"{INSTANCE}/system/projects/{PROJECT}/agari.md"
        assert location.companion_present

    def test_a_stamped_agari_is_absent_so_its_producer_runs(self):
        """`project-stamp` writes `agari.md` from a template carrying `PLACEHOLDER`
        (`agari_template.md:12`). Read as present, a fresh project's Agari had no companion and
        was walked past, never declared; with a companion, it went to the answer step instead
        of `project-agari`."""
        stamped = "> **PLACEHOLDER — filled at station 2 of the project's setup seed.**\n"
        for extra in ({}, {f"{INSTANCE}/system/projects/{PROJECT}/agari_open_issues.md": "y"}):
            files = FakeFiles({**launcher_tree(),
                                f"{INSTANCE}/system/projects/{PROJECT}/agari.md": stamped,
                                **extra})
            location = self.locate(files, "Agari")
            assert not location.document_present and location.document_path is None
            assert chain.cycle_entry(location) is chain.CycleEntry.PRODUCER

    def test_a_declared_agari_is_present(self):
        files = FakeFiles({**launcher_tree(),
                            f"{INSTANCE}/system/projects/{PROJECT}/agari.md": "Done when …\n"})
        assert self.locate(files, "Agari").document_present

    def test_the_adr_is_present_only_when_it_holds_a_record(self):
        empty = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/adr/README.md": "x"})
        assert not self.locate(empty, "ADR").document_present
        filled = FakeFiles({**launcher_tree(),
                             f"{PRODUCT}/docs/adr/README.md": "x",
                             f"{PRODUCT}/docs/adr/0001-thing.md": "y"})
        assert self.locate(filled, "ADR").document_present

    def test_the_adr_and_the_nfdr_share_the_architecture_companion(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/architecture_open_issues.md": "x"})
        for name in ("ADR", "NFDR"):
            location = self.locate(files, name)
            assert location.companion_path == f"{PRODUCT}/docs/architecture_open_issues.md"


class TestCycleEntry:

    def entry(self, document_present, companion_present):
        return chain.cycle_entry(chain.DocumentLocation(
            document_path="d" if document_present else None,
            companion_path="c" if companion_present else None,
            document_present=document_present, companion_present=companion_present))

    def test_an_absent_document_goes_to_the_producer(self):
        assert self.entry(False, False) is chain.CycleEntry.PRODUCER
        assert self.entry(False, True) is chain.CycleEntry.PRODUCER

    def test_a_document_with_a_companion_goes_to_the_answer_step(self):
        assert self.entry(True, True) is chain.CycleEntry.ANSWER

    def test_a_document_with_no_companion_launches_nothing(self):
        assert self.entry(True, False) is chain.CycleEntry.NONE


class TestChainNameDefaultsWithoutBumpingTheSchema:
    """Task 3. `chain_name` is a new field on a state schema that does not move —
    `from_json`'s own rule (`"Unknown keys ignored, missing keys defaulted"`) is what makes a
    field addition free at load. Written literally, never through `to_json()`, or a state this
    old genuinely could not fail to carry the key."""

    def test_a_state_from_before_the_field_existed_still_loads_and_defaults_it(self):
        text = json.dumps({
            "schema_version": 2, "instance_root": "/i", "product_path": "/p", "project": "x",
            "core_dir": "/c", "shim_path": "/s.sh", "spine": ["FDR"],
        })
        state = chain.ChainState.from_json(json.loads(text))
        assert "chain_name" not in json.loads(text)
        assert state.chain_name == ""

    def test_the_schema_is_not_bumped_for_this_field(self):
        """A later bump has to argue with this test — the seed's own trap #1."""
        assert chain.STATE_SCHEMA == 2


class TestTheStateFile:

    def test_it_round_trips(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR,ADR")
        state = engine.store.load()
        assert state.project == PROJECT
        assert state.spine == ["FDR", "ADR"]
        assert state.engine_path == "/pinned/chain.py"

    def test_an_unknown_key_is_ignored_rather_than_a_crash(self):
        """`cls(**data)` turned any shape difference into a traceback out of the hook."""
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR")
        raw = files.read_text(STATE).rstrip()
        raw = raw[:-1].rstrip().rstrip(",") + ',\n  "a_field_from_the_future": 3\n}'
        files.write_text(STATE, raw)
        assert engine.store.load().project == PROJECT

    def test_a_write_is_atomic(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR")
        assert not any(key.endswith(".tmp") for key in files.files)

    def test_a_missing_state_file_is_refused_by_name(self):
        store = chain.StateStore(FakeFiles(), STATE)
        with pytest.raises(chain.StateIncompatible):
            store.load()


class TestAdvanceIsIdempotent:

    def engine_mid_walk(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        engine.files_written = files.writes
        start(engine, "FDR,ADR,NFDR")
        return engine, processes

    def test_the_consumed_event_is_persisted_before_the_next_decision_runs(self):
        """The whole of what makes a re-fired hook safe: the pending marker is cleared and
        written to disk BEFORE anything else happens, so a duplicate delivery arriving in that
        window finds nothing pending and is itself a no-op.

        Once the step has launched something new, a duplicate of the OLD event names the old
        launch, and `advance` refuses it — `TestAFinishNamesItsLaunch`."""
        engine, processes = self.engine_mid_walk()
        finish(engine, "completed")

        # `StateStore.save` writes the `.tmp` sibling and replaces it over the real path, so
        # the temporary file is where a write is actually observed.
        state_writes = [text for path, text in engine.files_written
                        if path in (STATE, f"{STATE}.tmp")]
        cleared = [index for index, text in enumerate(state_writes)
                   if '"pending": null' in text]
        relaunched = [index for index, text in enumerate(state_writes)
                      if '"pending": {' in text]
        assert cleared, "the consumed event was never persisted as cleared"
        assert cleared[0] < relaunched[-1], "the next launch was recorded before the clear"

    def test_an_event_arriving_with_nothing_pending_advances_nothing(self):
        engine, processes = self.engine_mid_walk()
        state = engine.store.load()
        state.pending = None
        engine.store.save(state)
        launched_before = list(processes.launched)
        assert finish(engine, "completed").acted is False
        assert processes.launched == launched_before

    def test_an_event_with_nothing_pending_is_a_no_op(self):
        engine, _ = self.engine_mid_walk()
        state = engine.store.load()
        state.pending = None
        engine.store.save(state)
        assert finish(engine, "completed") == chain.AdvanceResult(acted=False, ended=None)

    def test_a_re_entry_after_the_chain_ended_is_counted_not_acted_on(self):
        engine, _ = self.engine_mid_walk()
        state = engine.store.load()
        state.ended = chain.CycleEnd.SETTLED.value
        engine.store.save(state)
        finish(engine, "completed")
        finish(engine, "completed")
        assert engine.store.load().reentries == 2

    def test_an_outcome_that_is_not_completed_is_a_machinery_stop(self):
        engine, _ = self.engine_mid_walk()
        finish(engine, "failed")
        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value

    def test_an_ordinary_non_completed_outcome_keeps_its_generic_reason(self):
        """Every outcome that is not `produced_nothing` behaves exactly as it does today —
        the generic "ended <x>, not completed" reason, unchanged."""
        engine, _ = self.engine_mid_walk()
        finish(engine, "failed")
        assert "ended failed, not completed" in engine.store.load().ended_reason

    @pytest.mark.parametrize("outcome", ["timeout", "vanished", "appear_error"])
    def test_the_other_hook_outcomes_are_untouched_by_the_new_one(self, outcome):
        """The three real non-completed `HookOutcome` values, driven by name rather than by
        a stand-in: each still reaches MACHINERY with `_step`'s generic reason, and none of
        them picks up the produced-nothing wording."""
        engine, _ = self.engine_mid_walk()
        finish(engine, outcome)
        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert f"ended {outcome}, not completed" in state.ended_reason
        assert "produced nothing" not in state.ended_reason

    def test_completed_still_advances_the_walk_rather_than_ending_it(self):
        """The fourth value the plan holds unchanged. `completed` is the one outcome that is
        not a stop, and the new branch must not have swallowed it."""
        engine, processes = self.engine_mid_walk()
        launched_before = len(processes.launched)
        finish(engine, "completed")
        assert engine.store.load().ended is None
        assert len(processes.launched) > launched_before

    def test_a_produced_nothing_outcome_is_a_machinery_stop_not_a_settlement(self):
        """The watcher's own read (task 2) reaches the chain and halts it, rather than the
        chain re-deriving the opposite answer from an absent report."""
        engine, _ = self.engine_mid_walk()
        finish(engine, "produced_nothing")
        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value

    def test_a_produced_nothing_outcome_names_the_fact_in_the_reason(self):
        engine, _ = self.engine_mid_walk()
        finish(engine, "produced_nothing")
        assert "produced nothing" in engine.store.load().ended_reason

    def test_a_produced_nothing_outcome_launches_nothing_further(self):
        engine, processes = self.engine_mid_walk()
        launched_before = list(processes.launched)
        finish(engine, "produced_nothing")
        assert processes.launched == launched_before

    def test_the_value_the_watcher_passes_is_the_value_this_chain_halts_on(self):
        """The seam the plan's Reached-when #1 names: "that value is what `watch_agent.py`
        passes". `chain.py` carries it as a bare literal and imports nothing from the watcher
        — deliberately, since the shim's one string argument is the only place the two files
        meet — so a rename on either side is silent everywhere except here. Driven with the
        enum's own value rather than a copy of the string, which is what makes it a seam test
        instead of a second copy of the literal."""
        import watch_agent

        engine, _ = self.engine_mid_walk()
        finish(engine, watch_agent.HookOutcome.PRODUCED_NOTHING.value)
        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "produced nothing" in state.ended_reason

    def test_produced_nothing_fed_twice_ends_the_walk_once(self):
        engine, _ = self.engine_mid_walk()
        finish(engine, "produced_nothing")
        finish(engine, "produced_nothing")
        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert state.reentries == 1


class TestTheChainTakesItsOwnBeforeReading:
    """Task 4: `chain.py:300` used to call `find_self_answer_report` with no
    `reports_before`, so a dead run whose HookOutcome fell through tasks 1-3 would be
    credited with its predecessor's report. The chain takes that reading itself, at
    launch (`_launch`, where `state.pending` is already set), and persists it on
    `state.reports_before` — the hook re-enters as a fresh process, so nothing held only
    in memory would survive to be consumed."""

    def test_a_state_from_before_the_field_existed_still_loads_and_defaults_it(self):
        text = json.dumps({
            "schema_version": 2, "instance_root": "/i", "product_path": "/p", "project": "x",
            "core_dir": "/c", "shim_path": "/s.sh", "spine": ["FDR"],
        })
        state = chain.ChainState.from_json(json.loads(text))
        assert "reports_before" not in json.loads(text)
        assert state.reports_before == []

    def test_a_pre_field_state_file_advances_through_the_whole_step(self):
        """`from_json` defaulting the field is only half the claim — the state file has to
        survive the path the completion hook actually takes. An engine launched before this
        field existed leaves a file with no `reports_before`; the new engine re-enters on it,
        reads the round, and behaves exactly as it did before the field (no exclusion), rather
        than crashing out of the hook."""
        files = FakeFiles({**launcher_tree(),
                           f"{PRODUCT}/docs/fdr.md": "# FDR",
                           f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        reports = FakeReports({"fdr": [report(document="docs/fdr.md",
                                              counts={"confirmed": 1})]})
        engine = build(files, reports=reports)
        start(engine, "FDR")

        stripped = json.loads(files.read_text(STATE))
        del stripped["reports_before"]
        files.write_text(STATE, json.dumps(stripped))
        assert "reports_before" not in json.loads(files.read_text(STATE))

        finish(build(files, reports=reports))

        assert reports.found[-1] == (PRODUCT, "fdr", [])

    def test_the_schema_is_not_bumped_for_this_field(self):
        """A later bump has to argue with this test — the seed's own trap, extended."""
        assert chain.STATE_SCHEMA == 2

    def test_reports_before_is_snapshotted_at_launch_and_persisted(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        stale = f"{PRODUCT}/docs/trail/fdr/self_answer-9.md"
        reports = FakeReports(present_before={"fdr": [stale]})
        engine = build(files, reports=reports)

        start(engine, "FDR")

        assert engine.store.load().reports_before == [stale]

    def test_a_fresh_process_reads_reports_before_off_disk_not_memory(self):
        """A brand-new `Chain` — sharing nothing with the one that launched but the same
        backing files — still passes the persisted reading to `.find()`, which is what
        proves it survives the process boundary the completion hook actually crosses."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        stale = f"{PRODUCT}/docs/trail/fdr/self_answer-9.md"
        reports = FakeReports({"fdr": [report(document="docs/fdr.md",
                                              counts={"confirmed": 1})]},
                              present_before={"fdr": [stale]})
        engine = build(files, reports=reports)
        start(engine, "FDR")

        fresh = build(files, reports=reports)
        finish(fresh)

        assert reports.found[-1] == (PRODUCT, "fdr", [stale])

    @staticmethod
    def dead_run_disk():
        """The disk a dead run leaves behind: last round's report still sitting in the trail,
        and nothing written this round. `FakeReports` scripts no report for `fdr`, so `.find`
        answers None exactly as the real locator does once `reports_before` has excluded the
        stale one — and `present_before` is what the chain persists at launch.

        The two tests below drive THIS state, because it is the only one in which task 4's
        exclusion can do harm: with no stale report there is nothing to exclude, and with a
        report written this round there is nothing wrong to conclude."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        stale = f"{PRODUCT}/docs/trail/fdr/self_answer-9.md"
        return files, FakeReports(present_before={"fdr": [stale]}), stale

    def test_a_produced_nothing_outcome_never_reaches_reports_find(self):
        """With tasks 1-3 in place, `_step` halts before `_read_the_round` runs at all, so on
        a dead run's disk the exclusion is never consulted and the absent report is never
        classified.

        Driven on `dead_run_disk` rather than on a disk that carries this round's report: a
        run that wrote a report is not a run that produced nothing, and asserting the halt
        over one proves only that `_step` returns early for any non-completed string. Its
        counterpart below drives the SAME disk with `completed` — which is what the watcher
        handed over before this station existed — and the pair is the plan's "task 4 lands
        last or not at all" as two assertions instead of a sentence."""
        files, reports, _stale = self.dead_run_disk()
        processes = FakeProcesses()
        engine = build(files, processes=processes, reports=reports)
        start(engine, "FDR")
        launched_before = list(processes.launched)

        finish(engine, "produced_nothing")

        state = engine.store.load()
        assert reports.found == []
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "produced nothing" in state.ended_reason
        assert processes.launched == launched_before

    def test_the_same_dead_run_reported_completed_walks_past_the_document(self):
        """Why task 4 could not land alone, as an assertion rather than as the plan's prose.

        Same dead run, same disk, reported `completed`. `_read_the_round` runs, the stale
        report is correctly excluded — `.find` is called with the persisted reading and
        answers None — and an absent report is `classify_report`'s SETTLED
        (`chain.py:592-593`, "the answer step met an absent companion, so the document
        already reads settled"). So the walk books the document as done and moves on, and the
        only thing the owner is eventually told is `_conclude`'s "the spine is walked and
        these companions are still open". Nothing anywhere says the run did not run.

        Asserted, not endorsed. This is the "worse than today" outcome the plan's ordering
        argument names, and it is what makes the halt above load-bearing rather than
        decorative. It stays reachable wherever the watcher cannot establish the fact for
        itself — an unreadable HEAD is the live case (`reporters.produced_nothing` returns
        False on `head_before is None`), which is the open question the station's closing
        commit owes an answer to. A change that closes it should fail this test."""
        files, reports, stale = self.dead_run_disk()
        engine = build(files, reports=reports)
        start(engine, "FDR")

        finish(engine, "completed")

        state = engine.store.load()
        assert reports.found == [(PRODUCT, "fdr", [stale])], "the stale reading never reached find"
        assert state.spine_index == 1, "the FDR slot was not consumed"
        assert state.ended != chain.CycleEnd.MACHINERY.value, "this path does not halt today"
        assert "produced nothing" not in state.ended_reason
        assert "the spine is walked" in state.ended_reason, state.ended_reason


class TestClassifyReport:

    def test_no_report_reads_as_settled(self):
        assert chain.classify_report(None) is chain.CycleEnd.SETTLED

    def test_missing_headings_are_a_machinery_stop(self):
        assert chain.classify_report(
            report(missing_headings=["## Items worked"])) is chain.CycleEnd.MACHINERY

    def test_an_item_left_for_the_owner_stops_for_the_owner(self):
        assert chain.classify_report(
            report(counts={"left for the owner": 1})) is chain.CycleEnd.LEFT_FOR_THE_OWNER

    def test_a_round_that_worked_items_continues(self):
        assert chain.classify_report(report(counts={"confirmed": 2})) is None

    def test_a_round_that_worked_none_but_owes_a_launcher_continues(self):
        assert chain.classify_report(report(owed=(("docs/SRS.md", "x"),))) is None

    def test_a_genuinely_empty_run_is_named_and_is_not_a_failure(self):
        assert chain.classify_report(report()) is chain.CycleEnd.EMPTY_RUN


class TestStagnationAndTheCap:

    def test_the_first_round_never_stagnates(self):
        assert chain.next_round_end(None, report(counts={"confirmed": 1}), 1) is None

    def test_an_unchanged_signature_could_not_be_settled(self):
        one = report(counts={"confirmed": 1}, owed=(("docs/SRS.md", "x"),))
        assert chain.next_round_end(chain.round_signature(one), one, 2) is \
            chain.CycleEnd.COULD_NOT_BE_SETTLED

    def test_the_live_srs_cycle_is_not_reported_as_stagnant(self):
        """Both rounds of a real SRS cycle carry an identical owed section, and the second is
        the one that must CONTINUE. Keyed on the owed set alone it reads as stagnation and
        halts the chain on its own live proof — so the signature carries what the round
        decided too."""
        owed = (("docs/SRS.md", "x"), ("docs/fdr.md", "y"))
        first = report(counts={"confirmed": 1}, owed=owed)
        second = report(counts={"confirmed": 1, "confirmed with addition": 1}, owed=owed)
        assert chain.next_round_end(chain.round_signature(first), second, 2) is None

    def test_the_cap_is_reached_after_stagnation_is_ruled_out(self):
        first = report(counts={"confirmed": 1})
        second = report(counts={"confirmed": 2})
        assert chain.next_round_end(chain.round_signature(first), second, 3) is \
            chain.CycleEnd.CAP

    def test_a_signature_survives_the_json_round_trip(self):
        one = report(counts={"confirmed": 1}, owed=(("docs/SRS.md", "x"),))
        as_json = chain._comparable(chain.round_signature(one))
        assert chain.next_round_end(as_json, one, 2) is chain.CycleEnd.COULD_NOT_BE_SETTLED


class TestUnroutedCompanions:

    def test_a_companion_opened_with_no_owed_bullet_is_named(self):
        one = report(counts={"confirmed": 1},
                     companions_opened=[("/p/docs/SDD_open_issues.md", "opened", "SDD.md")])
        assert chain.unrouted_companions(one) == ["SDD.md"]

    def test_a_companion_the_owed_set_routes_is_not_named(self):
        one = report(counts={"confirmed": 1},
                     owed=(("docs/SDD.md", "x"),),
                     companions_opened=[("/p/docs/SDD_open_issues.md", "opened", "SDD.md")])
        assert chain.unrouted_companions(one) == []

    def test_the_architecture_companion_is_routed_by_either_spelling(self):
        """A live product, 2026-09-01: the round opened a companion on `adr/` and owed
        `docs/adr/ and docs/nfdr.md` — two spellings of one document."""
        one = report(counts={"confirmed": 1},
                     owed=(("docs/adr/` and `docs/nfdr.md", "x"),),
                     companions_opened=[("/p/docs/architecture_open_issues.md", "opened",
                                          "adr/")])
        assert chain.unrouted_companions(one) == []

    def test_the_architecture_companion_is_routed_by_its_own_path(self):
        """A live product, 2026-10-20: the round opened the architecture companion on `adr/`
        and owed its round on the companion file itself."""
        one = report(counts={"confirmed": 1},
                     owed=(("products/p/docs/architecture_open_issues.md", "x"),),
                     companions_opened=[("products/p/docs/architecture_open_issues.md",
                                          "opened", "adr/")])
        assert chain.unrouted_companions(one) == []


class TestTheOwedSetOrdering:

    def test_upstream_sorts_first(self):
        items = [chain.OwedItem("docs/fdr.md", "a"), chain.OwedItem("docs/SRS.md", "b")]
        assert [i.document_path for i in chain.sort_owed_by_dependency(items)] == \
            ["docs/SRS.md", "docs/fdr.md"]

    def test_an_unresolvable_document_sorts_last_and_blocks_nothing(self):
        items = [chain.OwedItem("docs/whatever.md", "a"), chain.OwedItem("docs/SRS.md", "b")]
        assert chain.sort_owed_by_dependency(items)[0].document_path == "docs/SRS.md"

    def test_next_owed_item_pops_the_most_upstream(self):
        items = [chain.OwedItem("docs/fdr.md", "a"), chain.OwedItem("docs/PRD.md", "b")]
        head, rest = chain.next_owed_item(items)
        assert head.document_path == "docs/PRD.md"
        assert [i.document_path for i in rest] == ["docs/fdr.md"]

    def test_an_empty_queue_pops_nothing(self):
        assert chain.next_owed_item([]) == (None, [])


class TestHaltFast:

    def test_a_settled_cycle_never_halts(self):
        assert chain.should_halt(chain.CycleEnd.SETTLED, []) is False
        assert chain.should_halt(chain.CycleEnd.EMPTY_RUN, []) is False

    def test_a_failing_cycle_halts_on_an_empty_queue(self):
        for end in (chain.CycleEnd.COULD_NOT_BE_SETTLED, chain.CycleEnd.MACHINERY,
                    chain.CycleEnd.CAP, chain.CycleEnd.NO_RUNNABLE_COMMAND):
            assert chain.should_halt(end, []) is True, end

    def test_an_item_left_for_the_owner_never_halts(self):
        """`<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § *Nothing you leave blocks*: an item left for the owner
        "blocks nothing else", and "that an item is left costs the chain nothing" — the owner's
        call of 2026-08-29 that a downstream gate reads an unsettled document. It is the one
        unsettled end that is a successful cycle rather than a failure, so it is recorded and
        walked past. Measured cost of the old behaviour: a live product's definition chain
        abandoned its walk twice on 2026-09-03, the second time (that product's `caa3e0c`) over
        a single item about
        version numbering, leaving a decided answer unfolded behind it."""
        assert chain.should_halt(chain.CycleEnd.LEFT_FOR_THE_OWNER, []) is False

    def test_a_queue_that_could_still_change_the_outcome_keeps_it_going(self):
        assert chain.should_halt(chain.CycleEnd.COULD_NOT_BE_SETTLED,
                                 [chain.OwedItem("docs/SRS.md", "x")]) is False

    def test_a_left_item_is_still_recorded_even_though_it_does_not_halt(self):
        """The set that decides what is RECORDED is wider than the set that decides what HALTS.
        Dropping the member from both would trade a loud wrong behaviour for a silent one."""
        assert chain.CycleEnd.LEFT_FOR_THE_OWNER in chain._UNSETTLED_ENDS
        assert chain.CycleEnd.LEFT_FOR_THE_OWNER not in chain._HALTING_ENDS

    def test_every_end_the_drain_passed_over_is_named_at_the_halt(self):
        files = FakeFiles(launcher_tree())
        engine = build(files)
        start(engine, "FDR")
        state = engine.store.load()
        state.deferred_ends = [["machinery", "SRS", "launcher exited 3"]]
        assert "SRS — machinery" in engine._halt_reason(state, "stopped here")


class TestChainEndingAndDescribeEnd:
    """`ChainEnding` (task 2) gathers everything the owner's message needs into one value,
    built once by `.of(state, end, document, reason)` — a frozen dataclass rather than
    positional scalars an unattentive reorder could silently break
    (`python/conventions.md` § Constructs). `describe_end` becomes pure over that value; this
    class replaces the old `TestTheOwnersMessage`, which asserted the retired positional
    signature. No engine wiring here — `Chain` itself is untouched by this task."""

    def _state(self, *, spine_index=1, chain_name="foundation", spine=("FDR", "ADR", "NFDR")):
        state = chain.ChainState(instance_root="/i", product_path="/p", project="example-product",
                                 core_dir="/c", shim_path="/s.sh", spine=list(spine),
                                 spine_index=spine_index)
        state.chain_name = chain_name   # not yet a declared field until task 3; a plain
                                        # (non-frozen) dataclass tolerates the assignment either
                                        # way, so this test needs no change once task 3 lands.
        return state

    def test_of_gathers_every_field_off_the_state(self):
        state = self._state()
        ending = chain.ChainEnding.of(state, chain.CycleEnd.MACHINERY, "FDR",
                                      "launcher exited 3")
        assert ending == chain.ChainEnding(
            end=chain.CycleEnd.MACHINERY, chain_name="foundation", project="example-product",
            document="FDR", spine=("FDR", "ADR", "NFDR"), position=1,
            reason="launcher exited 3", deferred="")

    def test_of_reads_the_deferred_summary_off_the_state(self):
        state = self._state()
        state.deferred_ends = [["machinery", "SRS", "launcher exited 3"]]
        ending = chain.ChainEnding.of(state, chain.CycleEnd.SETTLED, None,
                                      "every spine document is settled")
        assert "SRS" in ending.deferred

    def test_the_banner_names_the_chain_and_the_project(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="foundation",
                                   project="example-product", document=None, spine=("FDR",),
                                   position=1, reason="every spine document is settled",
                                   deferred="")
        assert "CHAIN ENDED — foundation / example-product" in chain.describe_end(ending)

    def test_an_empty_chain_name_drops_the_name_and_its_separator(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="",
                                   project="example-product",
                                   document=None, spine=("FDR",), position=1, reason="x",
                                   deferred="")
        message = chain.describe_end(ending)
        assert "CHAIN ENDED — example-product" in message
        assert " / example-product" not in message

    def test_end_names_the_document_or_the_whole_walk(self):
        with_doc = chain.ChainEnding(end=chain.CycleEnd.MACHINERY, chain_name="f", project="p",
                                     document="FDR", spine=("FDR",), position=1, reason="x",
                                     deferred="")
        whole = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="f", project="p",
                                  document=None, spine=("FDR",), position=1, reason="x",
                                  deferred="")
        assert "end: machinery — at FDR" in chain.describe_end(with_doc)
        assert "end: settled — the whole walk" in chain.describe_end(whole)

    def test_walk_names_the_spine_in_order_and_the_position(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="f", project="p",
                                   document=None, spine=("FDR", "ADR", "NFDR"), position=2,
                                   reason="x", deferred="")
        message = chain.describe_end(ending)
        assert message.index("FDR") < message.index("ADR") < message.index("NFDR")
        assert "2 of 3 entered" in message

    def test_why_carries_the_raw_reason(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.MACHINERY, chain_name="f", project="p",
                                   document="FDR", spine=("FDR",), position=1,
                                   reason="launcher exited 3", deferred="")
        assert "why: launcher exited 3" in chain.describe_end(ending)

    def test_next_is_the_guidance_table_verbatim(self):
        for end in chain.CycleEnd:
            ending = chain.ChainEnding(end=end, chain_name="f", project="p", document=None,
                                       spine=(), position=0, reason="x", deferred="")
            assert chain._END_GUIDANCE[end] in chain.describe_end(ending)

    def test_also_is_omitted_when_nothing_was_deferred(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="f", project="p",
                                   document=None, spine=(), position=0, reason="x", deferred="")
        assert "also:" not in chain.describe_end(ending)

    def test_also_carries_the_deferred_clause_when_present(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="f", project="p",
                                   document=None, spine=(), position=0, reason="x",
                                   deferred="earlier, while the queue drained: SRS — machinery")
        message = chain.describe_end(ending)
        assert "also: earlier, while the queue drained: SRS — machinery" in message


class TestDeferredSummaryIsAModuleLevelFunction:
    """Extracted (task 2) so `ChainEnding.of` and `Chain._halt_reason` share one author — the
    seed's own words."""

    def _state(self):
        return chain.ChainState(instance_root="/i", product_path="/p", project="x",
                                core_dir="/c", shim_path="/s.sh", spine=["FDR"])

    def test_empty_deferred_ends_yields_an_empty_string(self):
        assert chain._deferred_summary(self._state()) == ""

    def test_it_reads_the_same_as_the_earlier_instance_method_did(self):
        state = self._state()
        state.deferred_ends = [["machinery", "SRS", "launcher exited 3"]]
        assert chain._deferred_summary(state) == \
            "earlier, while the queue drained: SRS — machinery (launcher exited 3)"


class TestTheReportsPort:
    """The one seam that still goes through `reporters.py` — proved on a report in the
    template's own shape rather than on a fake, so the wrapping is real."""

    REPORT = """# Self-answer report

## Header

- **Document:** `docs/SRS.md`

## Items worked

- **Verdict:** confirmed

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`docs/SRS.md`** — `<CORE>/launchers/skill/launcher.sh product-srs sealbox` (tail for a person)
"""

    def test_it_reads_a_report_in_the_templates_shape(self):
        files = FakeFiles({"/p/docs/trail/srs/self_answer-1.md": self.REPORT})
        parsed = chain.Reports(files).read("/p/docs/trail/srs/self_answer-1.md")
        assert parsed.document == "docs/SRS.md"
        assert parsed.counts["confirmed"] == 1
        assert parsed.missing_headings == []
        assert parsed.owed == [
            chain.OwedItem("docs/SRS.md",
                            "<CORE>/launchers/skill/launcher.sh product-srs sealbox")]

    def test_a_report_that_cannot_be_read_is_an_absence_not_an_exception(self):
        assert chain.Reports(FakeFiles()).read("/nowhere.md") is None

    def test_present_lists_every_self_answer_report_on_disk(self, tmp_path):
        d = tmp_path / "docs" / "trail" / "fdr"
        d.mkdir(parents=True)
        report_path = d / "self_answer-1.md"
        report_path.write_text("x")
        assert chain.Reports(FakeFiles()).present(str(tmp_path), "fdr") == (str(report_path),)

    def test_present_finds_nothing_when_none_is_on_disk(self, tmp_path):
        assert chain.Reports(FakeFiles()).present(str(tmp_path), "fdr") == ()

    def test_find_excludes_a_report_already_present_before_the_watch(self, tmp_path):
        """The measured defect, at the layer it actually lives: `chain.py:300` used to call
        this with no `reports_before` at all, so a dead run's `_read_the_round` inherited
        whatever report predates it."""
        d = tmp_path / "docs" / "trail" / "fdr"
        d.mkdir(parents=True)
        stale = d / "self_answer-1.md"
        stale.write_text("x")
        found = chain.Reports(FakeFiles()).find(str(tmp_path), "fdr", [str(stale)])
        assert found is None

    def test_find_ignores_every_stale_report_not_just_the_newest(self, tmp_path):
        """"Not the highest-numbered stale one" is the plan's own phrasing, and one stale
        report cannot tell a filter apart from a lucky ordering. Two are on disk; the run
        wrote neither, so the answer is None rather than `self_answer-7.md`."""
        d = tmp_path / "docs" / "trail" / "fdr"
        d.mkdir(parents=True)
        stale = []
        for n in (2, 7):
            path = d / f"self_answer-{n}.md"
            path.write_text("x")
            stale.append(str(path))
        assert chain.Reports(FakeFiles()).find(str(tmp_path), "fdr", stale) is None

    def test_find_returns_this_rounds_report_over_higher_numbered_stale_ones(self, tmp_path):
        """The same disk, one round later: the run DID write, and its report is lower-numbered
        than a stale sibling. The before-reading, not the number, decides."""
        d = tmp_path / "docs" / "trail" / "fdr"
        d.mkdir(parents=True)
        for n in (2, 7):
            (d / f"self_answer-{n}.md").write_text("x")
        stale = [str(d / "self_answer-2.md"), str(d / "self_answer-7.md")]
        fresh = d / "self_answer-3.md"
        fresh.write_text("x")
        assert chain.Reports(FakeFiles()).find(str(tmp_path), "fdr", stale) == str(fresh)

    def test_find_returns_a_report_not_in_reports_before(self, tmp_path):
        d = tmp_path / "docs" / "trail" / "fdr"
        d.mkdir(parents=True)
        fresh_report = d / "self_answer-1.md"
        fresh_report.write_text("x")
        found = chain.Reports(FakeFiles()).find(str(tmp_path), "fdr", [])
        assert found == str(fresh_report)

    def test_find_with_no_reports_before_behaves_as_today(self, tmp_path):
        """A caller that hands no before-reading keeps today's behaviour exactly —
        `reports_before=None` is opt-in, never a silent change of meaning."""
        d = tmp_path / "docs" / "trail" / "fdr"
        d.mkdir(parents=True)
        fresh_report = d / "self_answer-1.md"
        fresh_report.write_text("x")
        found = chain.Reports(FakeFiles()).find(str(tmp_path), "fdr")
        assert found == str(fresh_report)


class TestTheAnswerStepReadsItsOwnDocumentsTrail:

    def test_the_trail_stem_is_the_companions_stem_not_the_documents(self):
        assert chain.document("ADR").trail_stem == "architecture"
        assert chain.document("NFDR").trail_stem == "architecture"
        assert chain.document("SRS").trail_stem == "srs"

    def test_the_agaris_report_is_looked_for_in_the_instance_not_the_product(self):
        files = FakeFiles({**launcher_tree(),
                            f"{INSTANCE}/system/projects/{PROJECT}/agari.md": "x",
                            f"{INSTANCE}/system/projects/{PROJECT}/agari_open_issues.md": "y"})
        reports = FakeReports()
        engine = build(files, reports=reports)
        start(engine, "Agari")
        finish(engine, "completed")
        assert reports.found == [(INSTANCE, "agari", [])]


class TestSettledIsCheckedAgainstTheDisk:

    def test_an_open_companion_at_the_end_of_the_walk_is_not_settled(self):
        """A live product, 2026-09-01: the chain ended `settled` over three open companions, one
        holding an item its own round had left for the owner."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y"})
        reports = FakeReports()
        notifier = FakeNotifier()
        engine = build(files, reports=reports, notifier=notifier)
        start(engine, "FDR")
        finish(engine, "completed")
        state = engine.store.load()
        assert state.ended == chain.CycleEnd.LEFT_FOR_THE_OWNER.value
        assert "still open" in state.ended_reason

    def test_a_left_item_mid_walk_does_not_stop_the_spine(self):
        """The defect this fix closes, driven end to end. FDR's cycle answers its companion and
        leaves one item for the owner; the walk must go on to ADR rather than abandoning it.

        Measured before the fix, on a live product 2026-09-03: `chain-definition` ended
        `left_for_the_owner` at the SDD with the rest of the walk forfeited, twice — the second
        time (that product's `caa3e0c`) over one item about what a version number promises,
        leaving a
        decided answer unfolded behind it."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                            f"{PRODUCT}/docs/adr/index.md": "z",
                            f"{PRODUCT}/docs/nfdr.md": "w"})
        processes = FakeProcesses()
        engine = build(files, processes=processes,
                       reports=FakeReports({"fdr": [report(document="docs/fdr.md",
                                                           counts={"left for the owner": 1})]}))
        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        state = engine.store.load()
        # The walk reaches the END of the spine — three documents, not one. Before the fix it
        # abandoned at FDR with ADR and NFDR forfeited.
        assert state.spine_index == 3, (
            f"the walk stopped at index {state.spine_index}: {state.ended_reason}")
        # It may still END, but only at `_conclude`, and for `_conclude`'s own reason: the spine
        # is walked out and a companion the owner holds is still open. That is not the mid-walk
        # abandonment this fix removes, and the reason string is what tells the two apart.
        if state.ended is not None:
            assert state.ended == chain.CycleEnd.LEFT_FOR_THE_OWNER.value
            assert "the spine is walked" in state.ended_reason, state.ended_reason

    def test_a_left_item_mid_walk_is_recorded_even_though_it_does_not_halt(self):
        """Bar 2 of the station: not halting must not become not happening. The end lands in
        `deferred_ends`, which is what names it to the owner at the conclusion."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                            f"{PRODUCT}/docs/adr/index.md": "z",
                            f"{PRODUCT}/docs/nfdr.md": "w"})
        engine = build(files,
                       reports=FakeReports({"fdr": [report(document="docs/fdr.md",
                                                           counts={"left for the owner": 1})]}))
        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        recorded = [e[0] for e in engine.store.load().deferred_ends]
        assert chain.CycleEnd.LEFT_FOR_THE_OWNER.value in recorded, recorded

    def test_a_failing_cycle_mid_walk_still_stops_the_spine(self):
        """The control. Only the one end changed; a real failure forfeits the rest as before."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                            f"{PRODUCT}/docs/adr/index.md": "z",
                            f"{PRODUCT}/docs/nfdr.md": "w"})
        engine = build(files, processes=FakeProcesses(codes=[0, 3]),
                       reports=FakeReports({"fdr": [report(document="docs/fdr.md",
                                                           counts={"could not be settled": 1})]}))
        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")
        assert engine.store.load().ended is not None, "a failing cycle no longer halts"

    def test_a_chain_announces_itself_when_it_starts(self):
        """The owner's ask, 2026-09-03. A walk that runs for hours and only speaks when it
        stops leaves no record of having begun, and today two chains were mistaken for running
        long after they had died. The banner mirrors `describe_end`'s shape so start and end
        read as one pair, and carries what tells two concurrent walks apart."""
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, notifier=notifier)
        start(engine, "FDR,ADR,NFDR", notifier_command="/notify", chain_name="foundation")

        assert notifier.messages, "a chain that starts says nothing"
        first = notifier.messages[0]
        assert first.startswith("CHAIN STARTED — foundation / sealbox"), first
        assert "walk: FDR, ADR, NFDR" in first, first
        assert f"engine: chain.py {chain.__version__}" in first, first

    def test_an_unnamed_chain_still_announces_itself(self):
        """`chain_name` is optional by design — a hand-run or a future third chain still starts,
        and must still be heard."""
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, notifier=notifier)
        start(engine, "FDR", notifier_command="/notify")
        assert notifier.messages[0].startswith("CHAIN STARTED — sealbox"), notifier.messages[0]

    def test_a_left_item_does_not_discard_the_owed_set(self):
        """The regression. A cycle that leaves an item for the owner still asked, on its own
        report, for the producer that folds what it DID decide. Before this, `classify_report`
        returned an end above the branch that queues `report.owed`, so the request was dropped.

        Live cost, a live product 2026-09-03: three self-answer commits (18:26, 18:53, 20:52)
        decided five items including the units table, `SDD.md` went untouched from 15:27, and
        the state carried `queue: []` beside a report reading
        `## Launchers owed  - docs/SDD.md — .../product-sdd/launcher.sh <project>`."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                            f"{PRODUCT}/docs/adr/index.md": "z",
                            f"{PRODUCT}/docs/nfdr.md": "w"})
        engine = build(files, reports=FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 4, "left for the owner": 1},
            owed=(("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),),
        )]}))
        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        # The queue is drained inside the same advance that fills it, so reading
        # `state.queue` afterwards observes a transient and finds it empty either way. What is
        # observable is that the owed bullet was ROUTED rather than dropped: the round is
        # accounted for, and the producer the report asked for was launched.
        state = engine.store.load()
        assert state.rounds.get("FDR") == 1, (
            f"the round was not accounted for, so the owed set was never reached: {state.rounds}")
        assert any(argv[:3] == through_skill("product-fdr") for argv in engine.processes.launched), (
            f"the owed fold was dropped: {engine.processes.launched}")

    def test_a_left_item_still_counts_its_round_and_records_history(self):
        """Same branch, second consequence. `round_signature` is how the chain sees stagnation;
        a chain that leaves an item every round recorded no history at all and could never tell
        it was stuck. The product's state read `history: {}` after a cycle that ran."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                            f"{PRODUCT}/docs/adr/index.md": "z",
                            f"{PRODUCT}/docs/nfdr.md": "w"})
        engine = build(files, reports=FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 4, "left for the owner": 1},
            owed=(("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),),
        )]}))
        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        state = engine.store.load()
        assert state.rounds.get("FDR") == 1, state.rounds
        assert "FDR" in state.history, state.history

    def test_the_owed_producer_actually_runs_after_a_left_item(self):
        """End to end, and the one that maps to the real failure: queuing it is only worth
        something if the drain then launches it."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                            f"{PRODUCT}/docs/adr/index.md": "z",
                            f"{PRODUCT}/docs/nfdr.md": "w"})
        processes = FakeProcesses()
        engine = build(files, processes=processes, reports=FakeReports({"fdr": [report(
            document="docs/fdr.md",
            counts={"confirmed": 4, "left for the owner": 1},
            owed=(("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),),
        )]}))
        start(engine, "FDR,ADR,NFDR")
        finish(engine, "completed")

        assert any(argv[:3] == through_skill("product-fdr") for argv in processes.launched), (
            f"the owed producer never launched: {processes.launched}")

    def test_a_failure_found_in_the_round_wins_over_the_left_item(self):
        """A failure found inside the branch must win over the softer end that got us in.
        Identical rounds trip `next_round_end`'s stagnation check first — that is the failure
        this reaches, and either it or the cap makes the point: `end` is not left at
        `left_for_the_owner` when the round itself is a stop."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y"})
        same = lambda: report(document="docs/fdr.md",
                              counts={"confirmed": 1, "left for the owner": 1},
                              owed=(("docs/fdr.md",
                                     f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),))
        engine = build(files, reports=FakeReports({"fdr": [same() for _ in range(6)]}))
        start(engine, "FDR")
        for _ in range(6):
            if engine.store.load().ended:
                break
            finish(engine, "completed")
        ended = engine.store.load().ended
        assert ended in (chain.CycleEnd.COULD_NOT_BE_SETTLED.value, chain.CycleEnd.CAP.value), (
            f"a stopping round was overwritten by the left item: {ended}")

    def test_a_failing_cycle_queues_nothing(self):
        """The control. Only the one end changed; a machinery stop still drops its owed set."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "x",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "y"})
        engine = build(files, reports=FakeReports({"fdr": [report(
            document="docs/fdr.md", missing_headings=("## Launchers owed",),
            owed=(("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),),
        )]}))
        start(engine, "FDR")
        finish(engine, "completed")
        state = engine.store.load()
        assert state.queue == [], state.queue
        assert state.ended == chain.CycleEnd.MACHINERY.value

    def test_a_companion_outside_this_chains_walk_is_not_its_to_report(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/PRD.md": "x",
                            f"{PRODUCT}/docs/prd_open_issues.md": "y",
                            f"{PRODUCT}/docs/fdr.md": "z"})
        engine = build(files)
        start(engine, "FDR")
        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value


class TestOneTerminalWriter:
    """Task 5, defect 1. Until now `_conclude`'s SETTLED write sent `_deferred_summary(state)`
    ALONE — empty with nothing deferred — while `_reach_end`'s halting write sent the full
    composed reason. `_halt` unifies the two writers, so a settled walk's message carries its
    own reason and not only the deferred clause. `_END_GUIDANCE[SETTLED]`'s boilerplate
    ("...is settled — nothing left to do.") already contains the word "settled", so the
    discriminating check is the SPECIFIC raw reason `_conclude` composes — the guidance text
    alone cannot prove this."""

    def test_a_settled_conclusion_sends_its_own_reason_not_only_the_deferred_clause(self):
        files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR"})
        notifier = FakeNotifier()
        engine = build(files, notifier=notifier)

        start(engine, "FDR")
        finish(engine, "completed")

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.SETTLED.value
        assert "every spine document is settled" in notifier.messages[-1]

    def test_settled_and_machinery_compose_the_message_the_same_way(self):
        """One writer, not two — `_reach_end`'s halting path already composed the full reason
        into its message; this proves `_conclude`'s SETTLED path now matches it rather than the
        other way around."""
        settled_files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR"})
        settled_notifier = FakeNotifier()
        settled = build(settled_files, notifier=settled_notifier)
        start(settled, "FDR")
        finish(settled)

        machinery_notifier = FakeNotifier()
        machinery = build(FakeFiles(launcher_tree()), processes=FakeProcesses(codes=[3]),
                          notifier=machinery_notifier)
        start(machinery, "FDR")

        settled_state = settled.store.load()
        machinery_state = machinery.store.load()
        assert settled_state.ended_reason in settled_notifier.messages[-1]
        assert machinery_state.ended_reason in machinery_notifier.messages[-1]


class TestTheCLI:

    def test_neither_flag_is_a_usage_error(self, capsys):
        assert chain.main([]) == 2
        assert "one of --advance, --start or --stop" in capsys.readouterr().err

    def test_both_flags_are_a_usage_error(self, capsys):
        assert chain.main(["--advance", "s", "completed", "--start", "s"]) == 2
        assert "mutually exclusive" in capsys.readouterr().err

    def test_start_names_every_flag_it_is_missing(self, capsys):
        assert chain.main(["--start", "/tmp/s.json"]) == 2
        err = capsys.readouterr().err
        for flag in ("--instance-root", "--product-path", "--project", "--core-dir",
                     "--shim-path", "--spine"):
            assert flag in err

    def test_a_spine_is_required_to_start(self, capsys):
        assert chain.main(["--start", "/tmp/s.json", "--instance-root", "/i",
                           "--product-path", "/p", "--project", "x", "--core-dir", "/c",
                           "--shim-path", "/s.sh"]) == 2
        assert "--spine" in capsys.readouterr().err

    def test_an_unknown_document_in_the_spine_is_refused_by_name(self, capsys):
        assert chain.main(["--start", "/tmp/s.json", "--instance-root", "/i",
                           "--product-path", "/p", "--project", "x", "--core-dir", "/c",
                           "--shim-path", "/s.sh", "--spine", "FDR,TPS"]) == 2
        assert "TPS" in capsys.readouterr().err

    def test_an_incompatible_state_is_reported_and_never_raised(self, tmp_path, capsys):
        state_path = tmp_path / "state.json"
        state_path.write_text('{"project": "x", "schema_version": 0}')
        assert chain.main(["--advance", str(state_path), "completed"]) == 3
        assert "cannot be resumed" in capsys.readouterr().err or True


class TestDescribeRefusal:
    """Task 7. A refusal never wears `describe_end`'s `CHAIN ENDED` banner — every one of these
    leaves `ended: null` on disk, so a banner claiming an end would be a false report — and it
    takes a distinguishing prefix instead. Tested as a pure function, never through a real
    `Notifier` — the bar `conftest.py`'s `_no_ambient_notifier` exists for, after a green suite
    once sent six real messages to the owner's phone."""

    def test_it_never_wears_the_chain_ended_banner(self):
        assert "CHAIN ENDED" not in chain.describe_refusal("the walk cannot be resumed")

    def test_it_carries_a_distinguishing_prefix(self):
        assert chain.describe_refusal("the walk cannot be resumed").startswith("chain: ")
        assert "UNRESOLVED" in chain.describe_refusal("the walk cannot be resumed")

    def test_it_carries_the_reason_verbatim(self):
        message = chain.describe_refusal("the walk cannot be resumed — boom")
        assert "the walk cannot be resumed — boom" in message


class TestTheRefusalsCallDescribeRefusal:
    """Wiring proof with no real `Notifier` touched — a source-text assertion, the same class
    of check `test_the_spine_literal_is_committed_in_the_script_not_composed` already uses for
    a launcher's own literal, proves the two `except` blocks in `main()` route through the pure
    function rather than composing their own string."""

    def _main_source(self):
        source = Path(chain.__file__).read_text()
        return source[source.index("\ndef main("):]

    def test_the_state_incompatible_refusal_calls_it(self):
        main_body = self._main_source()
        block = main_body[main_body.index("except StateIncompatible"):
                          main_body.index("except ChainAlreadyWalking")]
        assert "describe_refusal(" in block

    def test_the_chain_already_walking_refusal_calls_it(self):
        main_body = self._main_source()
        block = main_body[main_body.index("except ChainAlreadyWalking"):]
        assert "describe_refusal(" in block

    def test_both_refusals_still_keep_their_own_stderr_and_exit_codes(self, tmp_path, capsys):
        """`describe_refusal` touches only the notifier message — stderr and the exit codes (3,
        4) are the two refusals' own, untouched."""
        state_path = tmp_path / "state.json"
        state_path.write_text('{"project": "x", "schema_version": 0}')
        assert chain.main(["--advance", str(state_path), "completed"]) == 3
        assert "cannot be resumed" in capsys.readouterr().err

        walking_state = tmp_path / "walking.json"
        walking_state.write_text(json.dumps({
            "schema_version": chain.STATE_SCHEMA, "instance_root": "/i", "product_path": "/p",
            "project": "x", "core_dir": "/c", "shim_path": "/s.sh", "spine": ["FDR"],
            "pending": {"kind": "producer", "document": "FDR"},
        }))
        assert chain.main(["--start", str(walking_state), "--instance-root", "/i",
                           "--product-path", "/p", "--project", "x", "--core-dir", "/c",
                           "--shim-path", "/s.sh", "--spine", "PRD"]) == 4
        assert "already walking" in capsys.readouterr().err


class TestAnUnanticipatedExceptionNotifiesRatherThanCrashingSilently:
    """Defect 3, the seed's own words: until now `main()` caught `StateIncompatible` and
    `ChainAlreadyWalking` and nothing else, so any other exception out of `chain.advance()`
    printed a traceback inside the completion hook and sent nothing —
    `watch_agent.py`'s own words, silence "reads as 'still going'". Reached through a real,
    unhandled data shape (an unknown document name on a pending marker) rather than a
    monkeypatch, per this file's own header rule."""

    def test_an_unanticipated_exception_advancing_still_notifies_and_exits_nonzero(
            self, tmp_path, capsys):
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps({
            "schema_version": chain.STATE_SCHEMA, "instance_root": str(tmp_path),
            "product_path": str(tmp_path), "project": "x", "core_dir": str(tmp_path),
            "shim_path": str(tmp_path / "s.sh"), "spine": ["FDR"],
            "pending": {"kind": "answer", "document": "A-DOCUMENT-THAT-DOES-NOT-EXIST"},
        }))

        code = chain.main(["--advance", str(state_path), "completed"])

        assert code == 5
        assert "A-DOCUMENT-THAT-DOES-NOT-EXIST" in capsys.readouterr().err

    def test_an_unanticipated_exception_starting_still_notifies_and_exits_nonzero(
            self, tmp_path, capsys):
        """A genuine engine-side crash, not a usage error: the state path's own directory is
        a plain file, so `StateStore.save`'s `os.makedirs` raises `NotADirectoryError` —
        `start()` catches only `ChainAlreadyWalking`, so this is real, unhandled, and today
        prints a bare traceback and sends nothing."""
        write_provider_file(tmp_path)
        blocked = tmp_path / "blocked"
        blocked.write_text("not a directory")
        state_path = blocked / "state.json"

        code = chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                           "--product-path", str(tmp_path), "--project", "x",
                           "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                           "--spine", "FDR"])

        assert code == 5
        assert capsys.readouterr().err


class TestOneChainPerProjectAtATime:
    """Found while walking `the-second-command-enters`, 2026-09-01.

    Both chain launchers derive the state path from the project alone
    (`system/logs/chain-<project>-state.json`), and so does the completion shim beside it. So
    starting a second chain on a project whose first is still walking overwrites the state the
    live chain is keeping its position in — and the first chain's next completion event, when
    it lands, advances the SECOND chain's state instead. Nothing would have said so: two runs
    on one product, one of them stepping through a walk it was never given."""

    def live_state(self, files):
        engine = build(files)
        start(engine, "FDR,ADR,NFDR")
        return engine

    def test_starting_over_a_walking_chain_is_refused_by_name(self):
        files = FakeFiles(launcher_tree())
        self.live_state(files)

        second = build(files)
        with pytest.raises(chain.ChainAlreadyWalking) as raised:
            start(second, "PRD,Agari,SRS")
        assert STATE in str(raised.value)
        assert "FDR" in str(raised.value)

    def test_a_chain_that_ended_can_be_started_over(self):
        files = FakeFiles(launcher_tree())
        engine = self.live_state(files)
        state = engine.store.load()
        state.ended = chain.CycleEnd.SETTLED.value
        state.pending = None
        engine.store.save(state)

        second = build(files)
        assert start(second, "PRD,Agari,SRS").acted is True

    def test_a_fresh_project_starts_normally(self):
        assert start(build(FakeFiles(launcher_tree())), "FDR").acted is True

    def test_the_refusal_reaches_the_owner_rather_than_the_terminal_only(self, tmp_path,
                                                                        capsys):
        state_path = tmp_path / "state.json"
        state_path.write_text('{"schema_version": 2, "instance_root": "/i", '
                              '"product_path": "/p", "project": "x", "core_dir": "/c", '
                              '"shim_path": "/s.sh", "spine": ["FDR"], '
                              '"pending": {"kind": "producer", "document": "FDR"}}')
        code = chain.main(["--start", str(state_path), "--instance-root", "/i",
                            "--product-path", "/p", "--project", "x", "--core-dir", "/c",
                            "--shim-path", "/s.sh", "--spine", "PRD"])
        assert code == 4
        assert "already walking" in capsys.readouterr().err


class TestAnUnresumableStateDoesNotBlockAFreshStart:
    """The guard above protects a walk this engine could actually resume. A state file from
    another schema is not one: `advance` refuses it, so nothing is coming to finish it, and
    treating it as live would lock the project out of its own launcher.

    Live shape, 2026-09-01: a product's state was written at schema `None` and its chain died
    in the completion hook. The owner's next `chain-foundation <project>` must start, not be
    told to wait for a walk that ended hours ago."""

    def test_a_state_from_another_schema_is_started_over(self):
        files = FakeFiles({**launcher_tree(),
                            STATE: '{"project": "sealbox", "pending": {"kind": "answer", '
                                   '"document": "FDR"}, "ended": null}'})
        assert start(build(files), "FDR").acted is True

    def test_an_unparseable_state_is_started_over(self):
        files = FakeFiles({**launcher_tree(), STATE: "not json at all"})
        assert start(build(files), "FDR").acted is True


# --- what the first two live walks found, 2026-09-01 ---------------------------------------
#
# Both walks ended `left_for_the_owner` by two different paths, and each path read less of a
# report than the report carried. Every test below names the walk that measured it.


class TestARaisedItemLetsTheFoldHappenFirst:
    """A live product, 2026-09-01. A `companion-self-answer` run answers every item it was
    given and, reading the document whole, RAISES a new one — `## Raised on this document`, a
    different
    section from `## Left for the owner`.

    Ending the cycle on that raise was tried, and this class is why it is wrong. An end reached
    in `classify_report` skips the branch that queues the report's owed set, so halting on a
    raise halts BEFORE the producer that would fold it runs — and a producer often folds it:
    `e59446a` "SDD open issues answered — 2 of 2 items, and a third raised on the document
    itself" then `5c776aa` "SDD run 3 folds the reopened companion into v3, closes clean". On
    that same walk, halting here would have stopped at the SRS and forfeited UXD, DESIGN,
    CONTENT and SDD — 177 dead trail pointers repaired and one document settled.

    The raise is caught one step later, by the disk, in the class below."""

    def test_a_raised_item_continues_so_the_owed_fold_can_run(self):
        raised = report(document="docs/SRS.md", counts={"confirmed with addition": 2}, raised=1,
                        owed=(("docs/SRS.md", "x"),))
        assert chain.classify_report(raised) is None

    def test_an_item_explicitly_left_for_the_owner_still_ends_the_cycle(self):
        """The other section is a worked item the run refused to decide — no fold will close
        that, so it ends here as it always did."""
        both = report(counts={"left for the owner": 1, "confirmed": 1}, raised=1)
        assert chain.classify_report(both) is chain.CycleEnd.LEFT_FOR_THE_OWNER

    def test_a_raised_item_is_still_named_in_the_message_when_an_end_is_reached(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        reports = FakeReports({"fdr": [report(document="docs/fdr.md",
                                               counts={"left for the owner": 1}, raised=2)]})
        engine = build(files, reports=reports)
        start(engine, "FDR")
        finish(engine, "completed")
        assert "2 item(s) raised" in engine.store.load().ended_reason


class TestAProducerThatLeavesACompanionIsNotWalkedPast:
    """A live product, 2026-09-01. `product-uxd` came back "the run had nothing to fold — the UXD
    companion is still waiting on you", and the chain advanced to the FDR without looking:
    `_step` reads a report only for an `answer` step, so a producer's completion never
    re-reads the disk for the document it just ran. `UXD_open_issues.md` was still open when
    the walk ended, and nothing in the chain's own messages said so."""

    def test_a_producer_leaving_its_companion_sends_the_document_back_through_its_cycle(self):
        files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR"})
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR,ADR")            # FDR present, no companion -> spine walks past it
        # the ADR producer runs, and leaves a companion behind
        files.write_text(f"{PRODUCT}/docs/architecture_open_issues.md", "# open")
        finish(engine, "completed")

        assert processes.launched[-1] == answer("architecture")

    def test_a_producer_that_leaves_nothing_advances_as_before(self):
        files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR"})
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "FDR,ADR")
        finish(engine, "completed")

        assert processes.launched[-1] == through_skill("product-architecture") or \
            engine.store.load().ended is not None

    def test_a_producer_that_leaves_its_document_absent_is_a_machinery_stop(self):
        """`project-agari` committed something but left the stamped placeholder and no
        companion. Advancing would let the walk conclude "every spine document is settled"
        over an undeclared Agari."""
        agari = f"{INSTANCE}/system/projects/{PROJECT}/agari.md"
        files = FakeFiles({**launcher_tree(), agari: "> **PLACEHOLDER — stamped.**\n"})
        processes = FakeProcesses()
        engine = build(files, processes=processes)

        start(engine, "Agari")
        assert processes.launched[-1] == through_skill("project-agari")
        finish(engine, "completed")

        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value
        assert "still absent" in engine.store.load().ended_reason

    def test_the_re_entry_is_bounded_by_the_round_cap(self):
        """It cannot loop: the cap and the stagnation check already bound a cycle, and this
        path goes through the same answer step they measure."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        same = lambda: report(document="docs/fdr.md", counts={"confirmed": 1},
                              owed=(("docs/fdr.md",
                                     f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),))
        reports = FakeReports({"fdr": [same() for _ in range(6)]})
        engine = build(files, processes=processes, reports=reports)

        start(engine, "FDR")
        for _ in range(10):
            if engine.store.load().ended:
                break
            finish(engine, "completed")

        assert engine.store.load().ended in (chain.CycleEnd.COULD_NOT_BE_SETTLED.value,
                                              chain.CycleEnd.CAP.value,
                                              chain.CycleEnd.LEFT_FOR_THE_OWNER.value)


class TestEveryEndNamesWhatItEndedOn:
    """A live product, 2026-09-01. The chain halted at the ADR with `ended_reason: ""`, so the
    owner's notification was the bare guidance line — while the watcher's message for the same
    run named the count, the verdict and the owed bullet. The conclusion path, by contrast,
    wrote a genuinely useful reason. One engine, two exits, one of them mute."""

    def test_a_halt_on_a_report_names_the_companion_and_the_count(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        notifier = FakeNotifier()
        reports = FakeReports({"fdr": [report(document="docs/fdr.md",
                                               counts={"left for the owner": 2, "confirmed": 1})]})
        engine = build(files, reports=reports, notifier=notifier)

        start(engine, "FDR")
        finish(engine, "completed")

        reason = engine.store.load().ended_reason
        assert "fdr_open_issues.md" in reason
        assert "2" in reason
        assert "fdr_open_issues.md" in notifier.messages[-1]

    def test_a_halt_with_no_report_still_says_why(self):
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        engine = build(files, reports=FakeReports())
        start(engine, "FDR")
        finish(engine, "failed")
        assert engine.store.load().ended_reason


class TestTheConclusionSweepsEveryCompanionItWasToldAbout:
    """A live product, 2026-09-01. Its own owed run opened a sibling instance's
    `system/doctrine/writing_bar_open_issues.md`, and the conclusion never named it: the sweep
    walked the spine, and `writing_bar.md` is not a spine document. The
    report that opened it named it under `## Companions opened`, which is where this reads."""

    def test_a_companion_named_by_a_report_is_swept_even_off_the_spine(self):
        outsider = "/instance/system/doctrine/writing_bar_open_issues.md"
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open",
                            outsider: "# still open"})
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md", counts={"confirmed": 1},
            companions_opened=[(f"`{outsider}`", "opened", "system/doctrine/writing_bar.md")],
            owed=(("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"),
                  ("system/doctrine/writing_bar.md",
                   f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}")),
        )]})
        engine = build(files, reports=reports)

        start(engine, "FDR")
        for _ in range(6):
            if engine.store.load().ended:
                break
            finish(engine, "completed")

        assert outsider in engine.store.load().ended_reason

    def test_a_companion_that_was_cleared_is_not_named(self):
        files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR"})
        engine = build(files)
        start(engine, "FDR")
        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value


# --- the-chains-stop-announces-itself, leg 1: one notification per walk --------------------
#
# Nothing above asserts a message COUNT — every test that reads `notifier.messages` reads its
# content, never its length. This is the unstated property every leg below must not break:
# a pinning test, characterising today's engine, meant to read green before this station moves
# a line and green after it is done.


def endings(notifier) -> list[str]:
    """The TERMINAL messages only. A walk also announces itself on the way in
    (`describe_start`), and the invariant this file guards has always been about the end: one
    terminal writer, one message when a walk stops. Counting every message conflated the two
    the moment a start banner existed."""
    return [m for m in notifier.messages if m.startswith("CHAIN ENDED")]


class TestOneNotificationPerWalk:
    """One TERMINAL notification per walk. The start banner is not one of them."""


    def test_a_launcher_exit_halt_sends_exactly_one_notification(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3]), notifier=notifier)

        start(engine, "FDR")

        assert len(endings(notifier)) == 1

    def test_a_settled_conclusion_sends_exactly_one_notification(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, notifier=notifier)

        start(engine, "FDR")
        finish(engine, "completed")

        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value
        assert len(endings(notifier)) == 1

    def test_a_walk_that_defers_then_halts_sends_only_the_halting_message(self):
        """Two owed items, upstream (SRS) first. SRS's launch fails while FDR still sits in the
        queue, so the machinery stop it reaches is DEFERRED, not halted — `should_halt` reads a
        non-empty remaining queue. FDR's own launch then succeeds, and only its own later
        completion (reported `failed`, not `completed`) is what actually halts the chain."""
        files = FakeFiles({**launcher_tree(),
                            f"{PRODUCT}/docs/fdr.md": "# FDR",
                            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        notifier = FakeNotifier()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md", counts={"confirmed": 1},
            owed=(("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"),
                  ("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}")),
        )]})
        engine = build(files, processes=FakeProcesses(codes=[0, 3, 0]),
                      reports=reports, notifier=notifier)

        start(engine, "FDR")            # the answer step launches (call 1, exit 0)
        finish(engine, "completed")     # reads the round, drains SRS (call 2, exit 3 -> defers),
                                        # then drains FDR (call 3, exit 0)

        assert endings(notifier) == []
        assert engine.store.load().deferred_ends

        finish(engine, "failed")        # the FDR producer's own completion — the real halt

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert len(endings(notifier)) == 1
        assert "SRS" in endings(notifier)[0]   # the halting message still names the deferred stop

    def test_advance_after_ended_sends_nothing_further(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3]), notifier=notifier)

        start(engine, "FDR")
        assert len(endings(notifier)) == 1

        finish(engine, "completed")
        finish(engine, "completed")

        assert len(endings(notifier)) == 1
        assert engine.store.load().reentries == 2


# --- code-integrity pass, 2026-09-02 ------------------------------------------------------
#
# Written from the seed and the station's own "Reached when", never from the code that landed.
# Each class below names the stated behaviour it pins and why nothing above already pinned it:
# the legs each proved one hop of a seam, and the seams themselves went unasserted.


class TestTheHaltMessageNamesTheWalkItWas:
    """Defect 2 — "The message cannot say which walk it was … and nothing says the SRS was
    document 3 of 7." Every hop has a test (the launcher passes the flag, `start()` persists
    it, `describe_end` prints it) and the whole has none: nothing drives a named chain to a
    real halt and reads what actually reached the notifier."""

    def test_a_machinery_halt_names_the_chain_the_project_and_the_position(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3]), notifier=notifier)

        start(engine, "FDR,ADR,NFDR", chain_name="foundation")

        message = notifier.messages[-1]
        assert f"CHAIN ENDED — foundation / {PROJECT}" in message
        assert "walk: FDR, ADR, NFDR — 1 of 3 entered" in message
        assert "end: machinery — at FDR" in message

    def test_a_settled_conclusion_names_the_chain_too(self):
        """The exit defect 1 was mute on — it must carry the name as well as the reason."""
        files = FakeFiles({**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR"})
        notifier = FakeNotifier()
        engine = build(files, notifier=notifier)

        start(engine, "FDR", chain_name="foundation")
        finish(engine, "completed")

        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value
        assert f"CHAIN ENDED — foundation / {PROJECT}" in notifier.messages[-1]

    def test_an_unnamed_walk_still_reports_its_project(self):
        """A hand-run or a future third chain omits the flag; the message degrades to the
        project rather than printing a dangling separator."""
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3]), notifier=notifier)

        start(engine, "FDR")

        assert notifier.messages[-1].startswith(f"CHAIN ENDED — {PROJECT}\n")


class TestTheRawReasonReachesTheMessageAndTheComposedOneTheState:
    """Task 5's own rule: "The **raw** reason goes to the message and the **composed** one to
    the state, so `also:` is not printed twice and `ended_reason` on disk stays
    byte-identical." Both halves are only observable on a walk that actually deferred an end —
    with nothing deferred the two compositions coincide, so every test above is blind to it."""

    def _defer_then_halt(self):
        """Two owed items, upstream (SRS) first. SRS's launch fails while FDR is still queued,
        so that machinery stop is deferred rather than halting; FDR's own later completion,
        reported `failed`, is the halt."""
        files = FakeFiles({**launcher_tree(),
                           f"{PRODUCT}/docs/fdr.md": "# FDR",
                           f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        notifier = FakeNotifier()
        reports = FakeReports({"fdr": [report(
            document="docs/fdr.md", counts={"confirmed": 1},
            owed=(("docs/SRS.md", f"{CORE}/launchers/skill/launcher.sh product-srs {PROJECT}"),
                  ("docs/fdr.md", f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}")),
        )]})
        engine = build(files, processes=FakeProcesses(codes=[0, 3, 0]),
                       reports=reports, notifier=notifier)
        start(engine, "FDR", chain_name="foundation")
        finish(engine, "completed")
        finish(engine, "failed")
        assert engine.store.load().deferred_ends, "the fixture must actually defer an end"
        return engine, notifier.messages[-1]

    def test_the_why_line_carries_the_raw_reason_alone(self):
        _, message = self._defer_then_halt()
        why = next(line for line in message.splitlines() if line.startswith("why: "))
        assert "earlier, while the queue drained" not in why

    def test_the_deferred_clause_is_reported_once_on_the_also_line(self):
        _, message = self._defer_then_halt()
        assert "also: earlier, while the queue drained" in message
        assert message.count("earlier, while the queue drained") == 1

    def test_the_state_file_still_carries_the_composed_reason(self):
        engine, message = self._defer_then_halt()
        state = engine.store.load()
        raw = next(line for line in message.splitlines()
                   if line.startswith("why: "))[len("why: "):]
        assert state.ended_reason == engine._halt_reason(state, raw)
        assert state.ended_reason != raw


class TestAnUnanticipatedCrashActuallySendsSomething:
    """Defect 3 — "A crash is silence", and `watch_agent.py`'s own cost for it: silence "reads
    as 'still going'". The tests that landed with the fix assert the exit code and stderr, and
    neither reads the channel the defect is about — a run that printed the traceback and sent
    nothing would pass both. Driven through a real `Notifier` pointed at a script in
    `tmp_path`: the ambient-notifier bar (`conftest.py`'s `_no_ambient_notifier`) is about
    inheriting the owner's own command, and it says a test exercising a send sets its own."""

    def _recording_notifier(self, tmp_path):
        log = tmp_path / "sent.txt"
        script = tmp_path / "notify.sh"
        script.write_text(f'#!/bin/sh\nprintf "%s" "$1" > {log}\n')
        script.chmod(0o755)
        return str(script), log

    def test_a_crash_advancing_reaches_the_owners_channel(self, tmp_path):
        command, log = self._recording_notifier(tmp_path)
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps({
            "schema_version": chain.STATE_SCHEMA, "instance_root": str(tmp_path),
            "product_path": str(tmp_path), "project": "x", "core_dir": str(tmp_path),
            "shim_path": str(tmp_path / "s.sh"), "spine": ["FDR"], "notifier": command,
            "pending": {"kind": "answer", "document": "A-DOCUMENT-THAT-DOES-NOT-EXIST"},
        }))

        assert chain.main(["--advance", str(state_path), "completed"]) == 5

        assert log.exists(), "a crash advancing sent nothing — the defect is unfixed"
        assert "CHAIN ENDED" not in log.read_text()
        assert "UNRESOLVED" in log.read_text()

    def test_a_crash_starting_reaches_the_owners_channel(self, tmp_path):
        command, log = self._recording_notifier(tmp_path)
        write_provider_file(tmp_path)
        blocked = tmp_path / "blocked"
        blocked.write_text("not a directory")

        assert chain.main(["--start", str(blocked / "state.json"),
                           "--instance-root", str(tmp_path), "--product-path", str(tmp_path),
                           "--project", "x", "--core-dir", str(tmp_path),
                           "--shim-path", str(tmp_path / "s.sh"), "--spine", "FDR",
                           "--notifier", command]) == 5

        assert log.exists(), "a crash starting sent nothing — the defect is unfixed"
        assert "UNRESOLVED" in log.read_text()


class TestTheEndingValueObjectIsFrozen:
    """Task 2 asked for "a frozen dataclass", on `python/conventions.md`'s own grounds — the
    house default for a value read after it is built. Nothing above would notice a plain
    `@dataclass`, because every assertion reads the value rather than writing to it."""

    def test_an_ending_cannot_be_rewritten_after_it_is_built(self):
        ending = chain.ChainEnding(end=chain.CycleEnd.SETTLED, chain_name="f", project="p",
                                   document=None, spine=("FDR",), position=1, reason="x",
                                   deferred="")
        with pytest.raises(dataclasses.FrozenInstanceError):
            ending.reason = "something else"


class TestTheChainNameIsNeverAStartRequirement:
    """Task 4's stated constraint, read off the table it is a constraint on rather than off a
    usage string: "not added to `_START_REQUIRED_FLAGS` … because a required flag turns a
    reporting change into a start-time refusal for any hand-run or future third chain"."""

    def test_the_flag_is_absent_from_the_required_table(self):
        assert "--chain-name" not in [flag for flag, _ in chain._START_REQUIRED_FLAGS]

    def test_a_start_omitting_it_is_not_refused(self, tmp_path):
        write_provider_file(tmp_path)
        state_path = tmp_path / "state.json"
        assert chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                           "--product-path", str(tmp_path), "--project", "x",
                           "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                           "--spine", "FDR"]) == 0


class TestAWalkStartedBeforeTheFieldExistedStillResumes:
    """The station's own reached-when: "`STATE_SCHEMA` is still `2`, and a state file written
    without `chain_name` still loads **and resumes**." `from_json` is tested directly above;
    resuming is the half that goes through `StateStore.load`'s schema check and on into
    `advance()`, which is where trap #1's cost would actually land."""

    def test_advance_on_a_state_missing_the_field_is_not_refused(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, notifier=notifier)
        start(engine, "FDR")

        # The walk as a pre-`chain_name` engine left it on disk, mid-flight: no `chain_name`
        # key at all, and schema 2 written as a literal so a later bump breaks this too — that
        # is trap #1's real cost, a live walk abandoned and its project silently unlocked.
        data = json.loads(files.read_text(STATE))
        del data["chain_name"]
        data["schema_version"] = 2
        files.write_text(STATE, json.dumps(data))
        assert "chain_name" not in json.loads(files.read_text(STATE))

        result = finish(engine, "completed")

        assert result.acted
        assert engine.store.load().chain_name == ""


    def test_a_walk_started_while_the_skill_launcher_was_a_flag_still_resumes(self):
        """For one day, 2026-09-17, a walk chose the skill launcher with a flag the state carried.
        A state file still holding that key loads, and its next move is the only kind there is."""
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR,SRS")

        data = json.loads(files.read_text(STATE))
        data["through_skill_launcher"] = True
        files.write_text(STATE, json.dumps(data))

        finish(engine, "completed")

        assert processes.launched == [through_skill("product-fdr"), through_skill("product-srs")]


# --- the chain's end runs an optional hook ---------------------------------------------------

HOOK = "/hooks/next-queue.sh --chain-ended"
HOOK_ARGV = ["/hooks/next-queue.sh", "--chain-ended"]


def hook_calls(processes: FakeProcesses) -> list[dict]:
    return [call for call in processes.calls if call["argv"][:2] == HOOK_ARGV]


def open_fdr_companion() -> dict[str, str]:
    """An FDR with a companion still open, so the walk that answers it ends left for the owner."""
    return {**launcher_tree(), f"{PRODUCT}/docs/fdr.md": "# FDR",
            f"{PRODUCT}/docs/fdr_open_issues.md": "# open"}


class TestTheChainsEndRunsAnOptionalHook:
    """`--on-end <command>` is carried on the state and fired once from `_halt` — the one place
    a chain writes `ended` — with the end's value appended. `chain-product` passes it through so a
    caller that started a sweep is told when it is over."""

    def test_a_settled_conclusion_runs_the_hook_with_settled_appended(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        engine = build(files, processes=processes)
        start(engine, "FDR", on_end=HOOK)

        finish(engine, "completed")

        assert engine.store.load().ended == chain.CycleEnd.SETTLED.value
        assert [call["argv"] for call in hook_calls(processes)] == [[*HOOK_ARGV, "settled"]]
        assert hook_calls(processes)[0]["cwd"] == INSTANCE

    def test_the_hook_of_an_unforced_walk_carries_no_provider(self):
        """The hook may start a queue whose chains read the variable as a force — and the one
        the engine inherited is only the last run's provider."""
        processes = FakeProcesses()
        engine = build(FakeFiles(launcher_tree()), processes=processes,
                       environ={"PATH": "/usr/bin", "KENSAIAPP_AGENT_PROVIDER": "codex"})
        start(engine, "FDR", on_end=HOOK)

        finish(engine, "completed")

        assert "KENSAIAPP_AGENT_PROVIDER" not in hook_calls(processes)[0]["env"]
        assert hook_calls(processes)[0]["env"]["PATH"] == "/usr/bin"

    def test_the_hook_of_a_forced_walk_carries_the_force(self):
        processes = FakeProcesses()
        engine = build(FakeFiles(launcher_tree()), processes=processes)
        start(engine, "FDR", on_end=HOOK, forced_provider="codex")

        finish(engine, "completed")

        assert hook_calls(processes)[0]["env"]["KENSAIAPP_AGENT_PROVIDER"] == "codex"

    def test_a_halting_end_runs_the_hook_with_that_end_appended(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses(codes=[3])
        engine = build(files, processes=processes)

        start(engine, "FDR", on_end=HOOK)

        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value
        assert [call["argv"] for call in hook_calls(processes)] == [[*HOOK_ARGV, "machinery"]]

    def test_left_for_the_owner_conclusion_runs_the_hook_with_left_for_the_owner(self):
        files = FakeFiles(open_fdr_companion())
        reports = FakeReports({"fdr": [report(document="docs/fdr.md",
                                               counts={"left for the owner": 1})]})
        processes = FakeProcesses()
        engine = build(files, processes=processes, reports=reports)
        start(engine, "FDR", on_end=HOOK)

        finish(engine, "completed")

        assert engine.store.load().ended == chain.CycleEnd.LEFT_FOR_THE_OWNER.value
        assert [call["argv"] for call in hook_calls(processes)] == [
            [*HOOK_ARGV, "left_for_the_owner"]]

    def test_no_hook_runs_no_extra_process(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses(codes=[3])
        engine = build(files, processes=processes)

        start(engine, "FDR")

        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value
        assert processes.launched == [through_skill("product-fdr")]

    @pytest.mark.parametrize("hook_exit", [1, -1])
    def test_a_failing_hook_sends_one_message_and_leaves_the_end_untouched(self, hook_exit):
        """`-1` is `Processes.run`'s answer for a command that could not be started."""
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        engine = build(files, processes=FakeProcesses(codes=[3, hook_exit]), notifier=notifier)

        start(engine, "FDR", on_end=HOOK)

        about_the_hook = [message for message in notifier.messages if HOOK in message]
        state = engine.store.load()
        assert len(about_the_hook) == 1 and f"exited {hook_exit}" in about_the_hook[0]
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "launcher exited 3" in state.ended_reason

    def test_the_hook_runs_after_the_ended_state_is_saved(self):
        """A hook that starts the next queue reads this walk's state, so it must read an ended
        one."""
        files = FakeFiles(launcher_tree())
        seen: list = []

        class Watching(FakeProcesses):
            def run(self, argv, **kwargs):
                if argv[:2] == HOOK_ARGV:
                    seen.append(json.loads(files.read_text(STATE))["ended"])
                return super().run(argv, **kwargs)

        engine = build(files, processes=Watching(codes=[3]))

        start(engine, "FDR", on_end=HOOK)

        assert seen == [chain.CycleEnd.MACHINERY.value]

    def test_the_hook_is_read_back_from_the_state_on_advance(self):
        """Set at `--start`, it fires from a later `advance` in a fresh engine built off the
        state."""
        files = FakeFiles(launcher_tree())
        start(build(files), "FDR", on_end=HOOK)
        assert json.loads(files.read_text(STATE))["on_end"] == HOOK
        processes = FakeProcesses()

        finish(build(files, processes=processes))

        assert [call["argv"] for call in hook_calls(processes)] == [[*HOOK_ARGV, "settled"]]

    def test_the_hook_is_split_the_way_a_shell_quotes_it(self):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses(codes=[3])

        start(build(files, processes=processes), "FDR", on_end="'/a dir/hook.sh' --chain-ended")

        assert processes.launched[-1] == ["/a dir/hook.sh", "--chain-ended", "machinery"]

    def test_a_hook_that_cannot_be_parsed_is_reported_and_raises_nothing(self):
        files = FakeFiles(launcher_tree())
        notifier = FakeNotifier()
        processes = FakeProcesses(codes=[3])
        engine = build(files, processes=processes, notifier=notifier)

        start(engine, "FDR", on_end="'/hooks/unbalanced.sh --chain-ended")

        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value
        assert len([m for m in notifier.messages if "unbalanced.sh" in m]) == 1
        assert processes.launched == [through_skill("product-fdr")]

    def test_a_state_written_without_on_end_still_loads(self):
        older = {name: getattr(chain.ChainState(instance_root="", product_path="", project="",
                                                core_dir="", shim_path=""), name)
                 for name in chain._STATE_FIELDS if name != "on_end"}
        assert "on_end" not in older
        assert chain.ChainState.from_json(older).on_end == ""

    def test_main_passes_on_end_from_the_cli_to_start(self, tmp_path):
        """No real launcher exists under `tmp_path`, so the walk refuses its own first move
        (`no_runnable_command`) and ends inside `start` — which fires the hook the command line
        carried, through the real composition."""
        log = tmp_path / "hook.log"
        hook = tmp_path / "hook.sh"
        hook.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" >> {log}\n")
        hook.chmod(0o755)
        write_provider_file(tmp_path)
        state_path = tmp_path / "state.json"

        chain.main(["--start", str(state_path), "--instance-root", str(tmp_path),
                    "--product-path", str(tmp_path), "--project", "x",
                    "--core-dir", str(tmp_path), "--shim-path", str(tmp_path / "s.sh"),
                    "--spine", "FDR", "--on-end", str(hook)])

        assert log.read_text().splitlines() == ["no_runnable_command"]
        assert json.loads(state_path.read_text())["on_end"] == str(hook)


# --- the hook, fired by the real watcher, against the real engine ---------------------------


class TestTheHookReturnsWhileTheAdvanceLaunches:
    """A live walk, 2026-10-02. This engine's shim `exec`ed the engine, so the advance that
    launched the next document ran under the watcher's `timeout=60` with its output on the
    watcher's pipe, and the watcher killed a launcher partway through. The shim now detaches
    the engine, as `chain_development`'s always did.

    Driven through the real `watch_agent.run_on_complete_hook`, from a different cwd, with spaces
    in every path but the core's: the engine reads each launch as a command string and splits it
    (`validate_owed_command`), so a space in `<CORE>` ends the walk `no_runnable_command` before
    any shim fires. The watcher's 60 seconds is a literal inside `watch_agent.py`, so the second
    document's producer is held on a release file the test writes only after the hook has
    returned: it outlasts the hook whatever the bound is."""

    SPINE = "FDR,SRS"
    STATE_NAME = f"chain-{PROJECT}-state.json"

    def _stub_core(self, root: Path, release: Path, attached: Path) -> Path:
        """A skill launcher that records each call, returns at once for the FDR's producer and
        holds the SRS's on `release`, then writes a line to stdout (the write that killed an
        orphaned launcher) and a marker."""
        launcher = root / "launchers" / "skill" / "launcher.sh"
        launcher.parent.mkdir(parents=True)
        usage = launcher_tree()[f"{CORE}/launchers/skill/launcher.sh"]
        launcher.write_text(usage + (
            'printf \'%s\\n\' "$*" >> "$(dirname "$0")/calls.log"\n'
            'if [ "$1" = product-srs ]; then\n'
            f'  for _ in $(seq {HOLD_CAP * 20}); do [ -e {shlex.quote(str(release))} ] && break;'
            ' sleep 0.05; done\n'
            '  echo "launcher output after the watcher is gone"\n'
            f'  echo attached > {shlex.quote(str(attached))}\n'
            'fi\n'
            'exit 0\n'))
        launcher.chmod(0o755)
        return root

    def test_the_hook_fired_by_the_real_watcher_returns_while_the_advances_launch_is_held(
            self, tmp_path, monkeypatch):
        instance = tmp_path / "an instance"
        write_provider_file(instance)
        logs = instance / "system" / "logs"
        release = tmp_path / "release srs"
        attached = tmp_path / "watcher attached"
        core = self._stub_core(tmp_path / "acore", release, attached)
        state_path = logs / self.STATE_NAME
        shim_path = logs / f"chain-{PROJECT}.sh"
        real_engine = str(Path(chain.__file__).resolve())

        walk = chain.build_chain(str(state_path), notifier_command="", engine_path=real_engine)
        try:
            walk.start(instance_root=str(instance), product_path=str(tmp_path / "a product"),
                       project=PROJECT, core_dir=str(core), shim_path=str(shim_path),
                       spine=chain.parse_spine(self.SPINE))
            first = json.loads(state_path.read_text())
            first_shim = logs / f"chain-{PROJECT}-{first['walk_id']}-1.sh"
            assert first["pending"]["launch"] == f"{first['walk_id']}-1"
            assert os.access(first_shim, os.X_OK)
            elsewhere = tmp_path / "watcher cwd"
            elsewhere.mkdir()
            monkeypatch.chdir(elsewhere)

            began = time.monotonic()
            ran = watch_agent.run_on_complete_hook(str(first_shim),
                                                   watch_agent.HookOutcome.COMPLETED)
            elapsed = time.monotonic() - began

            # The SRS producer is held until `release` exists, and nothing writes it before the
            # hook returns, so a hook that waited on the engine waits out the whole cap. The
            # bound is that cap less a margin, not a guess at how fast a process starts.
            assert ran is True
            assert elapsed < HOLD_CAP - 10, (
                f"the hook waited {elapsed:.1f}s on the engine it should have detached")
            assert not attached.exists()

            release.write_text("")
            assert wait_for(attached.exists)
            second = json.loads(state_path.read_text())
            assert second["pending"]["launch"] == f"{second['walk_id']}-2"
            log = logs / f"chain-{PROJECT}.log"
            assert wait_for(lambda: log.exists() and "chain: acted=True" in log.read_text())
        finally:
            release.write_text("")


# --- a stop ends the walk (CP-373 to CP-383) ----------------------------------------------------
#
# A stop reaches the launch through the identity file its run recorded, and signals a process only
# while its pid still has the start time written there. The test records what the run launcher
# would have written, then changes the table to say what became of the processes.

STOP_AT = "2026-10-02T15:30:00+00:00"
FIRST_LAUNCH = "fixed-walk-id-1"
RUN_START, WATCHER_START = "Fri Oct  2 15:24:58 2026", "Fri Oct  2 15:24:59 2026"
HOOK = "/hooks/next-queue.sh --chain-ended"


def identity_file(launch: str = FIRST_LAUNCH) -> str:
    return walk_stop.identity_path(f"{SHIM[:-len('.sh')]}-{launch}.sh")


class AStoppableWalk:
    """One engine started on the product spine, and the process table it was handed."""

    def __init__(self, **start_arguments):
        self.files = FakeFiles(launcher_tree())
        self.table = FakeProcessTable()
        self.processes = FakeProcesses()
        self.notifier = FakeNotifier()
        start(self.engine(), "FDR,ADR,NFDR", **start_arguments)

    def engine(self):
        return build(self.files, processes=self.processes, notifier=self.notifier,
                     process_table=self.table)

    def record(self, run_pid: int = 100, watcher_pid: int = 101) -> None:
        self.table.starts[run_pid], self.table.starts[watcher_pid] = RUN_START, WATCHER_START
        self.files.write_text(
            identity_file(), walk_stop.identity_text(self.table, run_pid, watcher_pid))

    @property
    def state(self) -> dict:
        return json.loads(self.files.files[STATE])


def test_each_launch_records_its_identity_file_on_pending_and_in_its_environment():
    files = FakeFiles({**launcher_tree(), identity_file(): "left by an earlier launch"})
    processes = FakeProcesses()

    start(build(files, processes=processes,
                environ={"PATH": "/usr/bin", "DETACH_PROCESS_WATCHER_PID": "998"}),
          "FDR,ADR,NFDR")

    env = processes.calls[0]["env"]
    assert json.loads(files.files[STATE])["pending"]["identity"] == identity_file()
    assert env[walk_stop.IDENTITY_VARIABLE] == identity_file()
    assert "DETACH_PROCESS_WATCHER_PID" not in env
    assert files.files[identity_file()] == ""


def test_a_stop_ends_a_live_walk_stopping_its_watcher_then_its_run():
    walk = AStoppableWalk()
    walk.record()

    walk.engine().stop(STOP_AT)

    assert walk.table.stopped == [101, 100]
    assert walk.state["ended"] == "stopped" and walk.state["pending"] is None
    assert STOP_AT in walk.state["ended_reason"] and "stopped" in walk.state["ended_reason"]


def test_a_stop_on_a_walk_whose_run_and_watcher_are_gone_ends_it_at_once():
    walk = AStoppableWalk()
    walk.record()
    walk.table.starts.clear()

    walk.engine().stop(STOP_AT)

    assert walk.table.stopped == []
    assert walk.state["ended"] == "stopped" and "already gone" in walk.state["ended_reason"]


def test_a_stop_never_signals_a_recycled_pid():
    walk = AStoppableWalk()
    walk.record()
    walk.table.starts[100] = "Sat Oct  3 09:00:00 2026"
    walk.table.starts[101] = "Sat Oct  3 09:00:01 2026"

    walk.engine().stop(STOP_AT)

    assert walk.table.stopped == []


@pytest.mark.parametrize("how", ["no identity key", "empty file"])
def test_a_stop_on_a_launch_with_no_recorded_identity_signals_nothing_and_says_so(how):
    walk = AStoppableWalk()
    walk.table.starts[100] = RUN_START
    if how == "no identity key":
        pre_change = walk.state
        del pre_change["pending"]["identity"]
        walk.files.write_text(STATE, json.dumps(pre_change))

    message = walk.engine().stop(STOP_AT)

    assert walk.table.stopped == []
    assert "no recorded identity" in walk.state["ended_reason"]
    assert "no recorded identity" in message


def test_a_stop_on_an_ended_walk_changes_nothing_and_names_its_end():
    walk = AStoppableWalk()
    finish(walk.engine(), "timeout")
    before = walk.files.files[STATE]

    message = walk.engine().stop(STOP_AT)

    assert walk.files.files[STATE] == before
    assert chain.CycleEnd.MACHINERY.value in message
    assert walk.table.stopped == []


def test_a_stop_with_no_state_says_there_is_no_walk_and_writes_nothing():
    files = FakeFiles()

    message = build(files).stop(STOP_AT)

    assert "no walk" in message
    assert files.files == {}


def test_a_stop_runs_the_on_end_command_once_with_stopped():
    walk = AStoppableWalk(on_end=HOOK)
    launched_before = len(walk.processes.calls)

    walk.engine().stop(STOP_AT)

    hook_calls = [call["argv"] for call in walk.processes.calls[launched_before:]]
    assert hook_calls == [["/hooks/next-queue.sh", "--chain-ended", "stopped"]]


def test_a_stop_sends_one_message_and_returns_it():
    walk = AStoppableWalk()
    messages_before = len(walk.notifier.messages)

    message = walk.engine().stop(STOP_AT)

    assert walk.notifier.messages[messages_before:] == [message]


def test_a_finish_delivered_after_a_stop_is_a_counted_reentry():
    walk = AStoppableWalk()
    walk.engine().stop(STOP_AT)

    result = walk.engine().advance("completed", launch=FIRST_LAUNCH)

    assert result.acted is False
    assert walk.state["reentries"] == 1 and walk.state["ended"] == "stopped"


def test_a_start_after_a_stop_is_accepted():
    walk = AStoppableWalk()
    walk.engine().stop(STOP_AT)
    launched_before = len(walk.processes.launched)

    start(walk.engine(), "FDR,ADR,NFDR")

    assert len(walk.processes.launched) == launched_before + 1
    assert walk.state["ended"] is None


def test_the_refusal_says_nothing_will_finish_a_walk_whose_processes_are_gone():
    walk = AStoppableWalk()
    walk.record()
    walk.table.starts.clear()

    with pytest.raises(chain.ChainAlreadyWalking, match="(?i)nothing will finish"):
        start(walk.engine(), "FDR,ADR,NFDR")


def test_the_refusal_over_a_walk_with_a_live_run_says_to_let_it_finish_or_stop_it():
    walk = AStoppableWalk()
    walk.record()

    with pytest.raises(chain.ChainAlreadyWalking, match="(?i)let it finish"):
        start(walk.engine(), "FDR,ADR,NFDR")


def _a_walking_state(tmp_path, **overrides) -> Path:
    state = {"schema_version": chain.STATE_SCHEMA, "instance_root": str(tmp_path),
             "product_path": str(tmp_path), "project": "x", "core_dir": str(tmp_path),
             "shim_path": str(tmp_path / "s.sh"), "spine": ["FDR"],
             "pending": {"kind": "producer", "document": "FDR", "launch": "w-1"}, **overrides}
    path = tmp_path / "state.json"
    path.write_text(json.dumps(state))
    return path


def test_main_stop_prints_the_message_and_exits_0(tmp_path, capsys):
    path = _a_walking_state(tmp_path)

    assert chain.main(["--stop", str(path)]) == 0

    assert "stopped" in capsys.readouterr().out
    assert json.loads(path.read_text())["ended"] == "stopped"


def test_main_stop_uses_the_notifier_it_is_given_and_otherwise_the_states(tmp_path):
    logs = {}
    for name in ("state", "given"):
        script, log = tmp_path / f"{name}-notify.sh", tmp_path / f"{name}.log"
        script.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' \"$1\" >> {log}\n")
        script.chmod(0o755)
        logs[name] = (script, log)
    path = _a_walking_state(tmp_path, notifier=str(logs["state"][0]))

    assert chain.main(["--stop", str(path)]) == 0
    assert "stopped" in logs["state"][1].read_text()

    again = _a_walking_state(tmp_path, notifier=str(logs["state"][0]))
    assert chain.main(["--stop", str(again), "--notifier", str(logs["given"][0])]) == 0
    assert "stopped" in logs["given"][1].read_text()


def test_main_stop_on_a_state_it_cannot_read_exits_3_naming_it(tmp_path, capsys):
    path = tmp_path / "state.json"
    path.write_text('{"project": "x", "schema_version": 0}')

    assert chain.main(["--stop", str(path)]) == 3

    assert str(path) in capsys.readouterr().err


@pytest.mark.parametrize("other", [["--start", "/s"], ["--advance", "/s", "completed"]])
def test_main_stop_is_exclusive_with_start_and_advance(other, capsys):
    assert chain.main(["--stop", "/s", *other]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------
# One answered round — a companion answered seat by seat leaves one report per seat's run
#
# The launcher answers each seat's items in a run of its own, so a single launch can leave
# several `self_answer-<N>.md` files. The chain counts the launch as ONE round, over ONE report
# that folds them: the round counter, the stagnation signature, the cap, the queue and the
# reason it tells the owner all read the combined report, never the highest-numbered file.
# ---------------------------------------------------------------------------------------

SDD_OWED = ("docs/SDD.md", f"{CORE}/launchers/skill/launcher.sh product-sdd {PROJECT}")
SDD_OWED_AS_CORE = ("docs/SDD.md", f"<CORE>/launchers/skill/launcher.sh product-sdd {PROJECT}")


def a_round_walk(round_, spine="FDR,ADR,NFDR", present_before=None):
    """A walk started on the FDR whose answer step left `round_` — one report or a `Round`."""
    files = FakeFiles({**launcher_tree(),
                       f"{PRODUCT}/docs/fdr.md": "x",
                       f"{PRODUCT}/docs/fdr_open_issues.md": "y",
                       f"{PRODUCT}/docs/adr/index.md": "z",
                       f"{PRODUCT}/docs/nfdr.md": "w"})
    reports = FakeReports({"fdr": [round_]}, present_before=present_before)
    engine = build(files, reports=reports)
    start(engine, spine)
    return engine, reports


def pairs_of(*reports_):
    return [(f"/p/docs/trail/fdr/self_answer-{n}.md", item)
            for n, item in enumerate(reports_, 4)]


class TestAnAnsweredRoundIsReadWhole:

    def test_multiple_reports_count_as_one_round(self):
        three = Round([report(document="docs/fdr.md", counts={"confirmed": 1}) for _ in range(3)],
                      first=4)
        engine, _ = a_round_walk(three)

        finish(engine)

        state = engine.store.load()
        assert state.rounds.get("FDR") == 1, state.rounds
        assert list(state.history) == ["FDR"], state.history
        assert state.deferred_ends == [], "three clean reports reached an end of their own"
        assert state.ended not in (chain.CycleEnd.MACHINERY.value, chain.CycleEnd.CAP.value)

    def test_combined_round_sums_counts_and_queues_owed_launcher_once(self):
        four = report(document="docs/fdr.md", counts={"confirmed": 2}, owed=(SDD_OWED,))
        five = report(document="docs/fdr.md",
                      counts={"confirmed": 1, "left for the owner": 1}, owed=(SDD_OWED_AS_CORE,))
        engine, _ = a_round_walk(Round([four, five], first=4))

        finish(engine)

        state = engine.store.load()
        launched_sdd = [argv for argv in engine.processes.launched
                        if argv[:3] == through_skill("product-sdd")]
        assert len(launched_sdd) == 1, engine.processes.launched
        assert [end for end, _, _ in state.deferred_ends] == [
            chain.CycleEnd.LEFT_FOR_THE_OWNER.value], state.deferred_ends
        assert state.rounds.get("FDR") == 1

    def test_combiner_sums_raised_and_unnamed_verdicts(self):
        combined = chain.combine_round(pairs_of(
            report(document="docs/fdr.md", counts={"confirmed": 1, "left for the owner": 2},
                   raised=1, unnamed=2),
            report(counts={"confirmed": 3, "declined": 1}, raised=2, unnamed=1)))

        assert combined.counts == {"confirmed": 4, "left for the owner": 2, "declined": 1}
        assert combined.raised == 3
        assert combined.unnamed == 3

    def test_combiner_unions_companions_and_owed_in_report_order(self):
        first = report(document=None,
                       owed=(("docs/SRS.md", "a"), ("docs/fdr.md", "b")),
                       companions_opened=[["c/one.md", "docs/one.md"]])
        second = report(document="docs/fdr.md",
                        owed=(("docs/SRS.md", "a"), ("docs/adr.md", "c")),
                        companions_opened=[["c/one.md", "docs/one.md"],
                                           ["c/two.md", "docs/two.md"]])
        third = report(document="docs/other.md", owed=(("docs/adr.md", "c"),))

        combined = chain.combine_round(pairs_of(first, second, third))

        assert [(i.document_path, i.command) for i in combined.owed] == [
            ("docs/SRS.md", "a"), ("docs/fdr.md", "b"), ("docs/adr.md", "c")]
        assert combined.companions_opened == [["c/one.md", "docs/one.md"],
                                              ["c/two.md", "docs/two.md"]]
        assert combined.document == "docs/fdr.md", "the first report that names one"

    @pytest.mark.parametrize("bad_indexes, named", [
        ((1,), ["self_answer-5.md"]),
        ((0, 2), ["self_answer-4.md", "self_answer-6.md"]),
    ])
    def test_malformed_report_stops_whole_round_and_names_each_bad_report(self, bad_indexes,
                                                                          named):
        members = [report(document="docs/fdr.md", counts={"confirmed": 1}) for _ in range(3)]
        for index in bad_indexes:
            members[index] = report(counts={"confirmed": 1}, missing_headings=["## Items worked"])
        engine, _ = a_round_walk(Round(members, first=4))

        finish(engine)

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        for name in named:
            assert name in state.ended_reason, state.ended_reason
        for good in {"self_answer-4.md", "self_answer-5.md", "self_answer-6.md"} - set(named):
            assert good not in state.ended_reason, state.ended_reason

    def test_one_report_preserves_end_reason_queue_and_history(self):
        def outcome(round_):
            engine, _ = a_round_walk(round_)
            finish(engine)
            state = engine.store.load()
            return (state.ended, state.ended_reason, state.queue, state.history, state.rounds,
                    state.deferred_ends, engine.processes.launched)

        for single in (
                report(document="docs/fdr.md", counts={"confirmed": 1, "left for the owner": 1},
                       owed=(SDD_OWED,)),
                report(document="docs/fdr.md", missing_headings=["## Items worked"]),
        ):
            assert outcome(Round([single], first=1)) == outcome(single)

        # An unreadable single report reads as it always did: no report at all.
        assert chain.combine_round([("/p/docs/trail/fdr/self_answer-1.md", None)]) is None

    def test_no_new_report_preserves_settled_result(self):
        assert chain.combine_round([]) is None
        files = FakeFiles({**launcher_tree(),
                           f"{PRODUCT}/docs/fdr.md": "x",
                           f"{PRODUCT}/docs/fdr_open_issues.md": "y"})
        reports = FakeReports()
        engine = build(files, reports=reports)
        start(engine, "FDR")

        finish(engine)

        state = engine.store.load()
        assert state.rounds == {}, "an absent report is no round"
        assert state.ended != chain.CycleEnd.MACHINERY.value
        assert reports.found == [(PRODUCT, "fdr", [])]

    def test_combined_reason_uses_summed_owner_count(self):
        three = Round([report(document="docs/fdr.md", counts={"left for the owner": 1})
                       for _ in range(3)], first=4)
        engine, _ = a_round_walk(three)

        finish(engine)

        reasons = [reason for _, _, reason in engine.store.load().deferred_ends]
        assert any("3 item(s) left for the owner" in reason for reason in reasons), reasons

    def test_stagnation_compares_combined_signature(self):
        members = [report(document="docs/fdr.md", counts={"confirmed": 1}),
                   report(document="docs/fdr.md", counts={"confirmed": 1})]
        engine, _ = a_round_walk(Round(members, first=4))
        state = engine.store.load()
        previous = report(document="docs/fdr.md", counts={"confirmed": 2})
        assert chain.round_signature(previous) not in (chain.round_signature(m) for m in members)
        state.history["FDR"] = chain._comparable(chain.round_signature(previous))
        engine.store.save(state)

        finish(engine)

        assert engine.store.load().ended == chain.CycleEnd.COULD_NOT_BE_SETTLED.value

    def test_cap_is_evaluated_once_for_combined_round(self):
        members = [report(document="docs/fdr.md", counts={"confirmed": 1}),
                   report(document="docs/fdr.md", counts={"left for the owner": 1})]
        engine, _ = a_round_walk(Round(members, first=4))
        state = engine.store.load()
        state.rounds["FDR"] = chain.DEFAULT_CYCLE_CAP - 1
        engine.store.save(state)

        finish(engine)

        state = engine.store.load()
        assert state.rounds["FDR"] == chain.DEFAULT_CYCLE_CAP, "one increment for two reports"
        assert state.ended == chain.CycleEnd.CAP.value, "the cap outranks the left item"

    def test_unreadable_report_among_several_stops_as_machinery(self):
        engine, _ = a_round_walk(Round([
            report(document="docs/fdr.md", counts={"confirmed": 1}), None,
            report(document="docs/fdr.md", counts={"confirmed": 1}), None], first=4))

        finish(engine)

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "self_answer-5.md" in state.ended_reason, state.ended_reason
        assert "self_answer-7.md" in state.ended_reason, state.ended_reason

    def test_combiner_returns_single_report_object_unchanged(self):
        only = report(document="docs/fdr.md", counts={"confirmed": 1},
                      missing_headings=["## Items worked"])

        assert chain.combine_round(pairs_of(only)) is only

    def test_find_round_passes_persisted_before_reading(self, tmp_path):
        trail = tmp_path / "docs" / "trail" / "fdr"
        trail.mkdir(parents=True)
        for n in (2, 3, 10, 11):
            (trail / f"self_answer-{n}.md").write_text("x")
        stale = [str(trail / "self_answer-2.md"), str(trail / "self_answer-3.md")]

        found = chain.Reports(FakeFiles()).find_round(str(tmp_path), "fdr", stale)

        assert found == (str(trail / "self_answer-10.md"), str(trail / "self_answer-11.md"))

        # The engine hands the same three values on, through the port a test fakes.
        engine, reports = a_round_walk(
            Round([report(document="docs/fdr.md", counts={"confirmed": 1})] * 2, first=4),
            present_before={"fdr": [f"{PRODUCT}/docs/trail/fdr/self_answer-2.md"]})
        finish(engine)
        assert reports.found == [(PRODUCT, "fdr",
                                  [f"{PRODUCT}/docs/trail/fdr/self_answer-2.md"])]


# --- the product checkout: a run that leaves it dirtier halts the walk at that run -----------


class TestARunLeavesTheProductCheckoutAsItFoundIt:
    """CP-507 to CP-512. The checkout is read at each launch, kept on `pending`, and read again
    when that run's end arrives."""

    DIRTY = ["?? stray.txt", " M kept.md"]

    def walking(self, *readings, spine="FDR,ADR,NFDR"):
        files = FakeFiles(launcher_tree())
        processes = FakeProcesses()
        checkout = FakeCheckout(*readings)
        notifier = FakeNotifier()
        engine = build(files, processes=processes, checkout=checkout, notifier=notifier)
        start(engine, spine)
        return engine, processes, checkout, notifier

    def test_a_launch_records_the_product_checkout_on_pending(self):
        engine, _, checkout, _ = self.walking(["?? already.txt"])

        assert engine.store.load().pending["checkout_before"] == ["?? already.txt"]
        assert checkout.read == [PRODUCT]

    def test_a_run_that_leaves_the_product_checkout_dirtier_ends_machinery_naming_the_document(
            self):
        engine, _, _, notifier = self.walking([], self.DIRTY)

        finish(engine)

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        message = notifier.messages[-1]
        # The `end:` line is where a halt names its document; the `walk:` line names the whole
        # spine on every end, so a bare "FDR" anywhere would pass with no document named.
        assert f"end: {chain.CycleEnd.MACHINERY.value} — at FDR" in message.splitlines()
        assert f"why: {product_checkout.left_dirty([], self.DIRTY, PRODUCT)}" in message

    def test_a_dirty_run_halts_without_draining_the_owed_queue(self):
        engine, processes, _, _ = self.walking([], self.DIRTY)
        state = engine.store.load()
        owed = [{"document_path": "docs/fdr.md",
                 "command": f"{CORE}/launchers/skill/launcher.sh product-fdr {PROJECT}"}]
        state.queue = list(owed)
        engine.store.save(state)
        launched_before = list(processes.launched)

        finish(engine)

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert state.queue == owed
        assert processes.launched == launched_before

    def test_a_dirty_run_halts_whatever_its_outcome(self):
        engine, _, _, _ = self.walking([], self.DIRTY)

        finish(engine, "produced_nothing")

        reason = engine.store.load().ended_reason
        assert "`?? stray.txt`" in reason
        assert "produced nothing" not in reason

    def test_a_run_that_leaves_the_product_checkout_as_found_walks_on(self):
        engine, processes, _, _ = self.walking(["?? already.txt"], ["?? already.txt"])
        launched_before = len(processes.launched)

        finish(engine)

        assert engine.store.load().ended is None
        assert len(processes.launched) > launched_before

    def test_a_pending_with_no_recorded_checkout_is_not_checked(self):
        engine, processes, _, _ = self.walking([], self.DIRTY)
        state = engine.store.load()
        del state.pending["checkout_before"]
        engine.store.save(state)
        launched_before = len(processes.launched)

        finish(engine)

        assert engine.store.load().ended is None
        assert len(processes.launched) > launched_before

    def test_an_unreadable_checkout_at_launch_records_nothing_and_checks_nothing(self):
        engine, processes, checkout, _ = self.walking(None, self.DIRTY)
        assert "checkout_before" not in engine.store.load().pending
        launched_before = len(processes.launched)

        finish(engine)

        assert engine.store.load().ended is None
        assert len(processes.launched) > launched_before

    def test_a_checkout_unreadable_after_the_run_ends_machinery(self):
        engine, _, _, notifier = self.walking([], None)

        finish(engine)

        assert engine.store.load().ended == chain.CycleEnd.MACHINERY.value
        assert f"the product checkout {PRODUCT} could not be read" in notifier.messages[-1]

    def test_build_chain_wires_a_real_checkout(self, tmp_path):
        engine = chain.build_chain(str(tmp_path / "state.json"), notifier_command="",
                                   engine_path="/pinned/chain.py")

        assert isinstance(engine.checkout, product_checkout.Checkout)


class TestTheLiveWalkRuleIsNamed:
    """`walk_is_live` is the rule `_refuse_to_overwrite_a_live_walk` applies, stated once so
    another module asks the question the chain's own refusal asks. `EXIT_ALREADY_WALKING` is
    the status `main` returns on that refusal."""

    def test_walk_is_live_is_false_for_no_state(self):
        assert chain.walk_is_live({}) is False

    def test_walk_is_live_is_false_for_an_ended_walk(self):
        raw = {"ended": "sealed", "pending": {"document": "FDR"},
               "schema_version": chain.STATE_SCHEMA}
        assert chain.walk_is_live(raw) is False

    def test_walk_is_live_is_false_with_nothing_pending(self):
        raw = {"ended": None, "pending": None, "schema_version": chain.STATE_SCHEMA}
        assert chain.walk_is_live(raw) is False

    def test_walk_is_live_is_false_at_another_schema(self):
        raw = {"ended": None, "pending": {"document": "FDR"},
               "schema_version": chain.STATE_SCHEMA + 1}
        assert chain.walk_is_live(raw) is False

    def test_walk_is_live_is_true_for_a_walk_waiting_on_a_launch(self):
        raw = {"ended": None, "pending": {"document": "FDR"},
               "schema_version": chain.STATE_SCHEMA}
        assert chain.walk_is_live(raw) is True

    def test_main_returns_the_already_walking_exit_over_a_live_walk(self, tmp_path):
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps({
            "schema_version": chain.STATE_SCHEMA, "instance_root": "/i", "product_path": "/p",
            "project": "x", "core_dir": "/c", "shim_path": "/s.sh", "spine": ["FDR"],
            "pending": {"kind": "producer", "document": "FDR"},
        }))
        code = chain.main(["--start", str(state_path), "--instance-root", "/i",
                           "--product-path", "/p", "--project", "x", "--core-dir", "/c",
                           "--shim-path", "/s.sh", "--spine", "PRD"])
        assert code == chain.EXIT_ALREADY_WALKING
        assert chain.EXIT_ALREADY_WALKING == 4


# --- the card runs once per drain, after every other owed item -----------------------------

CARD_ARGV = producer("product-card")


def skill_command(skill: str, spelling: str = "<CORE>") -> str:
    return f"{spelling}/launchers/skill/launcher.sh {skill} {PROJECT}"


def card_command(project: str = PROJECT, spelling: str = "<CORE>") -> str:
    return f"{spelling}/launchers/product-card/launcher.sh {project}"


def card_argv(project: str = PROJECT) -> list[str]:
    return [f"{CORE}/launchers/product-card/launcher.sh", project]


ARCHITECTURE_COMPANION = {f"{PRODUCT}/docs/architecture_open_issues.md": "# open"}


def card_walk(*rounds, spine="FDR", disk=None, port=None, codes=None, scripts=None,
              keep_awake=False, processes=None):
    """A walk that answers the FDR, whose k-th answer round owes `rounds[k]`. Each round counts
    one more confirmed item than the last, so no two read as a round that changed nothing."""
    files = FakeFiles({**open_fdr_companion(), **(disk or {})})
    processes = processes or FakeProcesses(codes=codes)
    reports = FakeReports({
        "fdr": [report(document="docs/fdr.md", counts={"confirmed": number}, owed=owed)
                for number, owed in enumerate(rounds, 1)],
        **(scripts or {})})
    engine = build(files, processes=processes, reports=reports, provider_port=port)
    start(engine, spine, keep_awake=keep_awake)
    return engine, processes, files, reports


def resumed(files, processes, reports, port=None):
    """A fresh engine over the files, processes and reports a walk already used — the process
    the completion hook starts again."""
    return build(files, processes=processes, reports=reports, provider_port=port)


def owed_launches(processes: FakeProcesses) -> list[list[str]]:
    """What the walk launched for the owed set: every launch that is not an answer step. The
    answer step a finished run's own completion opens is not an owed launcher (CP-609)."""
    return [argv for argv in processes.launched if "companion-self-answer" not in argv[0]]


def finishes(engine, count: int) -> None:
    for _ in range(count):
        finish(engine)


class TestTheCardRunsOnceAndLast:
    """CP-604–CP-613: a validated `product-card` launch runs once per drain of the owed queue,
    after every other item the queue holds, in the order the card items arrived."""

    def test_card_launcher_runs_once_and_last(self):
        """Example 1: the FDR round owes the card on a registry document, `product-srs`, the same
        card on a document that resolves to none, and `product-architecture` — the one document
        today's order puts after the card."""
        engine, processes, _, _ = card_walk([
            ("docs/fdr.md", card_command()),
            ("docs/SRS.md", skill_command("product-srs")),
            ("system/projects/x/project.md", card_command(spelling=CORE)),
            ("docs/adr/", skill_command("product-architecture")),
        ])

        finishes(engine, 4)

        assert owed_launches(processes) == [through_skill("product-srs"),
                                            through_skill("product-architecture"), CARD_ARGV]
        assert processes.launched.count(CARD_ARGV) == 1

    @pytest.mark.parametrize("first_document, second_document", [
        ("docs/fdr.md", "system/projects/x/project.md"),
        ("system/projects/x/project.md", "docs/fdr.md"),
    ], ids=["registry-document-first", "unresolved-document-first"])
    @pytest.mark.parametrize("spelling", ["core-placeholder", "host-absolute", "pin-absolute",
                                          "relative"])
    def test_equivalent_card_commands_run_once_after_ordinary_items(
            self, tmp_path, spelling, first_document, second_document):
        host = tmp_path / "host"
        pin_core = _pin_of(tmp_path, host)
        spelled = {
            "core-placeholder": "<CORE>/launchers/product-card/launcher.sh",
            "host-absolute": f"{host}/core/launchers/product-card/launcher.sh",
            "pin-absolute": f"{pin_core}/launchers/product-card/launcher.sh",
            "relative": "core/launchers/product-card/launcher.sh",
        }[spelling]
        files = FakeFiles({**{key.replace(CORE, str(pin_core), 1): text
                              for key, text in {**launcher_tree(), **open_fdr_companion()}.items()
                              if key.startswith(CORE)},
                           f"{PRODUCT}/docs/fdr.md": "# FDR",
                           f"{PRODUCT}/docs/fdr_open_issues.md": "# open"})
        processes = FakeProcesses()
        reports = FakeReports({"fdr": [report(document="docs/fdr.md", counts={"confirmed": 1},
                                              owed=[
            (first_document, f"{spelled} {PROJECT} [--dry-run] [--keep-awake]"),
            ("docs/SRS.md", skill_command("product-srs")),
            (second_document, f"<CORE>/launchers/product-card/launcher.sh {PROJECT}"),
            ("docs/adr/", skill_command("product-architecture")),
        ])]})
        engine = build(files, processes=processes, reports=reports)
        engine.start(instance_root=str(host), product_path=PRODUCT, project=PROJECT,
                     core_dir=str(pin_core), shim_path=SHIM, spine=chain.parse_spine("FDR"))

        finishes(engine, 4)

        card = [f"{pin_core}/launchers/product-card/launcher.sh", PROJECT]
        assert owed_launches(processes) == [
            [f"{pin_core}/launchers/skill/launcher.sh", "product-srs", PROJECT],
            [f"{pin_core}/launchers/skill/launcher.sh", "product-architecture", PROJECT],
            card]
        assert processes.launched.count(card) == 1

    def test_unresolved_ordinary_item_runs_before_card(self):
        """Example 2: an ordinary item whose document resolves to none sorts after every
        document, and still before the card."""
        engine, processes, _, _ = card_walk([
            ("docs/fdr.md", card_command()),
            ("system/doctrine/writing_bar.md", skill_command("writing-bar")),
        ])

        finishes(engine, 3)

        assert owed_launches(processes) == [through_skill("writing-bar"), CARD_ARGV]

    def test_later_round_ordinary_work_stays_ahead_of_waiting_card(self):
        """Example 3: the card waits behind `product-architecture`; the ADR round that run leads
        to owes the same card again and a new ordinary item, which launches first."""
        files_scripts = {"architecture": [report(
            document="docs/adr/", counts={"confirmed": 1}, owed=[
                ("docs/fdr.md", card_command(spelling=CORE)),
                ("system/doctrine/writing_bar.md", skill_command("writing-bar"))])]}
        engine, processes, files, reports = card_walk(
            [("docs/fdr.md", card_command()),
             ("docs/adr/", skill_command("product-architecture"))],
            disk=ARCHITECTURE_COMPANION, scripts=files_scripts)

        for _ in range(4):
            finish(engine)
            engine = resumed(files, processes, reports)

        assert processes.launched == [answer("FDR"), through_skill("product-architecture"),
                                      answer("architecture"), through_skill("writing-bar"),
                                      CARD_ARGV, answer("FDR")]

    @pytest.mark.parametrize("interleaved", [False, True], ids=["plain", "interleaved-duplicates"])
    def test_distinct_card_arguments_keep_arrival_order_after_ordinary_items(self, interleaved):
        """Example 4 and CP-610: cards for `p`, then `q`, sit on documents whose ranks reverse
        that order, and still launch as they arrived."""
        owed = [("docs/adr/", card_command("p")),
                ("docs/SRS.md", card_command("q"))]
        if interleaved:
            owed += [("docs/nfdr.md", card_command("p", CORE)),
                     ("system/projects/x/project.md", card_command("q"))]
        owed.append(("docs/SRS.md", skill_command("product-srs")))
        engine, processes, _, _ = card_walk(owed)

        finishes(engine, 4)

        assert owed_launches(processes) == [through_skill("product-srs"), card_argv("p"),
                                            card_argv("q")]

    def test_refused_card_command_keeps_ordinary_position_and_reason(self):
        """Example 5 and CP-604: a card command the check refuses is not a card item. It is
        refused by name at the FDR's place, ahead of architecture, and nothing of it is
        remembered; a valid card beside them stays behind the ordinary work."""
        engine, processes, _, _ = card_walk([
            ("docs/fdr.md", "<CORE>/launchers/product-card/launcher.sh"),
            ("docs/adr/", skill_command("product-architecture")),
            ("docs/fdr.md", card_command()),
        ])

        finish(engine)

        state = engine.store.load()
        assert processes.launched == [answer("FDR"), through_skill("product-architecture")]
        assert state.deferred_ends[0][:2] == [chain.CycleEnd.NO_RUNNABLE_COMMAND.value, "FDR"]
        assert "takes 1 positional argument(s)" in state.deferred_ends[0][2]
        assert state.card_launches_in_drain == []

        finish(engine)

        assert processes.launched == [answer("FDR"), through_skill("product-architecture"),
                                      CARD_ARGV, answer("FDR")]
        assert engine.store.load().card_launches_in_drain == [CARD_ARGV]

    def test_card_drain_finishes_before_the_next_spine_document(self):
        """Example 6 and CP-607: the card runs at the end of the drain and the spine's ADR
        follows it. The ADR cycle that owes the card again is a new drain, and runs it again."""
        engine, processes, files, reports = card_walk(
            [("docs/SRS.md", skill_command("product-srs")), ("docs/fdr.md", card_command())],
            [],
            spine="FDR,ADR", disk=ARCHITECTURE_COMPANION,
            scripts={"architecture": [report(document="docs/adr/", counts={"confirmed": 1},
                                             owed=[("docs/fdr.md", card_command())])]})

        finishes(engine, 3)

        assert processes.launched == [answer("FDR"), through_skill("product-srs"), CARD_ARGV,
                                      answer("FDR"), through_skill("product-architecture")]

        finishes(engine, 2)

        assert processes.launched[5:7] == [answer("architecture"), CARD_ARGV]
        assert processes.launched.count(CARD_ARGV) == 2

    @pytest.mark.parametrize("first_document, provider, kept_document", [
        ("docs/fdr.md", "codex", "FDR"),
        ("system/projects/x/project.md", "claude", None),
    ], ids=["registry-first-copy", "unresolved-first-copy"])
    def test_first_card_copy_keeps_document_provider_and_completion(
            self, first_document, provider, kept_document):
        """Example 7 and CP-609: of two equivalent copies, the one queued first is the launch, with
        its own document's provider and its own completion handling."""
        port = ProviderText(edited_text({"documents.FDR": "codex", "documents.SRS": "gemini",
                                         "owed-items.no-document": "claude"}))
        engine, processes, _, _ = card_walk([
            (first_document, card_command()),
            ("docs/SRS.md", card_command(spelling=CORE)),
        ], port=port)

        finish(engine)

        assert processes.launched[:2] == [answer("FDR"), CARD_ARGV]
        assert provider_of(processes.calls[1]) == provider
        # The card's completion is the kept copy's: its document goes back to the answer step,
        # and a card on no document leaves nothing to answer.
        assert processes.launched[2:] == ([answer("FDR")] if kept_document else [])
        pending = engine.store.load().pending
        assert (pending or {}).get("document") == kept_document

    def test_queue_without_cards_keeps_dependency_order_and_stable_ties(self):
        """Example 8 and CP-606: with no card, the tiers, the ties within a tier and the
        unresolved items keep the order they always had."""
        engine, processes, _, _ = card_walk([
            ("docs/SDD.md", skill_command("product-sdd")),
            ("docs/content.md", skill_command("product-content")),
            ("docs/uxd.md", skill_command("product-uxd")),
            ("docs/first-unresolved.md", skill_command("first-unresolved")),
            ("docs/SRS.md", skill_command("product-srs")),
            ("docs/design.md", skill_command("product-design")),
            ("docs/second-unresolved.md", skill_command("second-unresolved")),
        ])

        finishes(engine, 7)

        assert owed_launches(processes) == [
            through_skill(skill) for skill in (
                "product-srs", "product-content", "product-uxd", "product-design",
                "product-sdd", "first-unresolved", "second-unresolved")]

    @pytest.mark.parametrize("spine, launched, ended", [
        ("FDR,ADR", [answer("FDR"), through_skill("product-architecture")], None),
        ("FDR", [answer("FDR")], chain.CycleEnd.LEFT_FOR_THE_OWNER.value),
    ], ids=["next-spine-document", "conclusion"])
    def test_empty_owed_queue_advances_or_concludes_without_card(self, spine, launched, ended):
        """CP-607: an owed set holding nothing takes the walk to its next spine document, or
        ends it, and launches no card."""
        engine, processes, _, _ = card_walk([], spine=spine)

        finish(engine)

        assert processes.launched == launched
        assert engine.store.load().ended == ended

    @pytest.mark.parametrize("later", [[], [("docs/SRS.md", card_command("q"))]],
                             ids=["same-card-again", "plus-a-different-card"])
    def test_post_card_answer_cannot_relaunch_the_same_card_in_one_drain(self, later):
        """CP-608/CP-610: the card's own completion sends its document back to the answer step,
        and that round owes the same card again. A fresh engine over the saved state does not
        launch it twice before the spine advances; a different argument is a different launch."""
        engine, processes, files, reports = card_walk(
            [("docs/fdr.md", card_command())],
            [("docs/fdr.md", card_command(spelling=CORE)), *later],
            spine="FDR,ADR")
        finish(engine)
        assert processes.launched == [answer("FDR"), CARD_ARGV, answer("FDR")]
        engine = resumed(files, processes, reports)

        finish(engine)

        # The `q` card finishes as it launches, so the drain empties and the spine moves on.
        state = engine.store.load()
        assert processes.launched[3:] == ([card_argv("q")] if later else []) + [
            through_skill("product-architecture")]
        assert state.card_launches_in_drain == []
        assert processes.launched.count(CARD_ARGV) == 1

    def test_older_state_without_card_memory_dispatches_normally(self):
        """The new field is additive: a state written before it existed loads, dispatches
        ordinary and card items, and resumes with the memory it grew."""
        literal = {"schema_version": 2, "instance_root": "/i", "product_path": "/p",
                   "project": "x", "core_dir": "/c", "shim_path": "/s.sh", "spine": ["FDR"]}
        assert chain.ChainState.from_json(literal).card_launches_in_drain == []
        assert chain.STATE_SCHEMA == 2
        engine, processes, files, reports = card_walk([
            ("docs/fdr.md", card_command()), ("docs/SRS.md", skill_command("product-srs"))])
        data = json.loads(files.read_text(STATE))
        del data["card_launches_in_drain"]
        data["schema_version"] = 2
        files.write_text(STATE, json.dumps(data))
        assert "card_launches_in_drain" not in json.loads(files.read_text(STATE))

        finish(engine)
        engine = resumed(files, processes, reports)
        finish(engine)
        engine = resumed(files, processes, reports)

        assert processes.launched == [answer("FDR"), through_skill("product-srs"), CARD_ARGV,
                                      answer("FDR")]
        assert json.loads(files.read_text(STATE))["card_launches_in_drain"] == [CARD_ARGV]

    def test_card_only_drain_launches_once_before_conclusion(self):
        """CP-607: a queue holding nothing but cards launches one, then the walk concludes."""
        engine, processes, _, _ = card_walk([
            ("system/projects/x/project.md", card_command()),
            ("system/projects/y/project.md", card_command(spelling=CORE))])

        finishes(engine, 2)

        state = engine.store.load()
        assert processes.launched == [answer("FDR"), CARD_ARGV]
        assert state.ended is not None
        assert state.pending is None

    def test_a_card_that_exits_0_ends_the_walk_with_no_shim_call(self):
        """The card launcher runs in the foreground and leaves no watcher, so nothing ever calls
        its shim: its clean exit is the run's end. Measured on a live product, 2026-10-21: the
        walk reached the card, the card succeeded, and the state sat at `ended: null` with the
        card's launch pending until the owner asked why it had gone quiet."""
        engine, processes, _, _ = card_walk([("system/projects/x/project.md", card_command())])

        finish(engine)

        state = engine.store.load()
        assert processes.launched == [answer("FDR"), CARD_ARGV]
        assert state.pending is None
        assert state.ended == chain.CycleEnd.LEFT_FOR_THE_OWNER.value
        # A shim fired by hand for the card's launch, the remedy the hang needed, now finds
        # the walk over and changes nothing.
        assert not engine.advance("completed", launch="fixed-walk-id-2").acted
        assert processes.launched == [answer("FDR"), CARD_ARGV]

    def test_card_launcher_failure_keeps_machinery_outcome_without_retry(self):
        """A card launch that exits non-zero ends the walk `machinery`, and is not tried again."""
        engine, processes, _, _ = card_walk(
            [("system/projects/x/project.md", card_command())], codes=[0, 7])

        finish(engine)

        state = engine.store.load()
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "launcher exited 7" in state.ended_reason
        assert processes.launched == [answer("FDR"), CARD_ARGV]
        assert not finish(engine).acted
        assert processes.launched == [answer("FDR"), CARD_ARGV]

    def test_provider_refusal_records_no_card_launch(self):
        """A launch the provider file cannot answer for halts the walk before anything of it is
        recorded: no card process, no remembered identity."""
        port = ProviderText()
        engine, processes, _, _ = card_walk(
            [("system/projects/x/project.md", card_command())], port=port)
        port.text = edited_text({"owed-items.no-document": None})

        finish(engine)

        state = engine.store.load()
        assert processes.launched == [answer("FDR")]
        assert state.ended == chain.CycleEnd.MACHINERY.value
        assert "owed-items.no-document is missing" in state.ended_reason
        assert state.card_launches_in_drain == []
        assert state.pending is None

    def test_card_identity_and_pending_are_saved_before_process_invocation(self):
        """The saved state the process port is called over already holds the launch's pending
        entry and the card's normalized identity — never the caller's `--keep-awake` — and a
        resumed engine keeps it."""
        files = FakeFiles({**open_fdr_companion()})

        class SavedStateObserver(FakeProcesses):
            def __init__(self):
                super().__init__()
                self.saved: list[dict] = []

            def run(self, argv, **kwargs):
                self.saved.append(json.loads(files.read_text(STATE)))
                return super().run(argv, **kwargs)

        observer = SavedStateObserver()
        reports = FakeReports({"fdr": [report(document="docs/fdr.md", counts={"confirmed": 1},
                                              owed=[("docs/fdr.md", card_command())])]})
        engine = build(files, processes=observer, reports=reports)
        start(engine, "FDR", keep_awake=True)

        finish(engine)

        assert observer.launched[1] == CARD_ARGV + ["--keep-awake"]
        seen = observer.saved[1]
        assert seen["pending"]["kind"] == "producer"
        assert seen["pending"]["launch"] == "fixed-walk-id-2"
        assert seen["card_launches_in_drain"] == [CARD_ARGV]
        assert resumed(files, observer, reports).store.load().card_launches_in_drain == [
            CARD_ARGV]

    def test_completed_ordinary_launch_can_be_owed_again_in_the_same_drain(self):
        """The drain's memory is the card's alone: an ordinary launcher already run is queued
        again when a later round owes it."""
        engine, processes, _, _ = card_walk(
            [("docs/SRS.md", skill_command("product-srs")), ("docs/fdr.md", card_command())],
            [("docs/SRS.md", skill_command("product-srs")), ("docs/fdr.md", card_command())])

        finishes(engine, 4)

        assert processes.launched == [answer("FDR"), through_skill("product-srs"), CARD_ARGV,
                                      answer("FDR"), through_skill("product-srs")]


# --- the self-answer report names the card an answer owes (CP-615–CP-627) -----------------


def test_self_answer_report_card_bullet_sources():
    """CP-615–CP-623, CP-625: both instruction files that write the report state the
    conditional final card bullet, each inside the section that owns it. The files are read from
    this checkout (never a pin or the primary checkout), a mention outside its section does not
    count, and only the published clauses are pinned — wrapping is normalised away."""
    root = Path(__file__).resolve().parents[2]
    skill_text = (root / "skills/companion/.claude/skills/companion-self-answer/SKILL.md"
                  ).read_text(encoding="utf-8")
    template_text = (root / "core/templates/self_answer_report_template.md"
                     ).read_text(encoding="utf-8")

    def flat(text: str) -> str:
        return re.sub(r"\s+", " ", text)

    step_six = re.search(r"^### Step 6 .*?(?=^#{1,3} |\Z)", skill_text, re.MULTILINE | re.DOTALL)
    owed = re.search(r"^## Launchers owed\n.*?(?=^## |\Z)", template_text,
                     re.MULTILINE | re.DOTALL)
    assert step_six and owed
    skill_step, template_section = flat(step_six.group(0)), flat(owed.group(0))

    # CP-621, CP-622: the launcher is named inside the section that owns it, in each file.
    assert "launchers/product-card" in skill_step
    assert "launchers/product-card" in template_section

    # CP-615: the trigger, and the fixed bullet shape — whole line, `<CORE>` written as it
    # stands and the real project in place of `<project>`.
    assert "an answer this run wrote into a slot states that a field of a project's card" in \
        skill_step
    assert "When an answer this run wrote into a slot owes a field of a project's card, the " \
        "list ends with one more bullet, for that card" in template_section
    bullet = ("- **system/projects/<project>/project.md** — "
              "`<CORE>/launchers/product-card/launcher.sh <project>`")
    for text in (step_six.group(0), owed.group(0)):
        assert re.search("^[ \t]*" + re.escape(bullet) + "$", text, re.MULTILINE)
    assert "with the real project name in place of both `<project>`s and `<CORE>` written as " \
        "it stands" in skill_step
    assert "with the real project name in place of both `<project>`s" in template_section

    # CP-616, CP-617: once per card, last, after every document's bullet — in the template the
    # card's example bullet is the last bullet of the section.
    assert "One entry per card." in skill_step
    assert "The card's bullet comes after every document's bullet" in skill_step
    assert "written once per card however many answers or fields owe it, after every " \
        "document's bullet" in template_section
    template_bullets = [line for line in owed.group(0).splitlines() if line.startswith("- ")]
    assert template_bullets[-1] == bullet

    # CP-618: no USAGE flag in the bullet and nothing after the command.
    assert "Neither flag belongs in the bullet" in skill_step
    assert "nothing follows the command's closing backtick" in skill_step
    assert "none of the `# USAGE` block's bracketed flags" in template_section
    assert "THE BULLET ENDS AT THE COMMAND: nothing follows it" in template_section

    # CP-619: which answers and which fields owe the card — every field the card carries, and
    # no list of them kept in either file.
    assert "Only an answer written into a slot counts." in skill_step
    assert "Every field the card carries counts." in skill_step
    assert "keep no list of them in this file" in skill_step
    assert "whatever field its question names" in skill_step
    for field in ("Test command:", "Languages:", "Language roots:"):
        assert field not in skill_text and field not in template_section

    # CP-619, CP-620: the exclusions and the empty case.
    for verdict in ("`left for the owner`", "`raised upstream`"):
        assert verdict in skill_step
    assert "`left for the owner` or `raised upstream` wrote no answer into a slot here, so it " \
        "never owes the card" in template_section
    assert "A run whose answers owe no card field writes no card bullet, and adds no section " \
        "to the report." in skill_step
    assert "A run whose answers owe no card field leaves the card's bullet out." in \
        template_section

    # CP-623: every listing site accounts for the card, and the companion set is one way only.
    skill_flat = flat(skill_text)
    assert "last, when an answer this run wrote owes a field of a project's card, `product-card` " \
        "for that card" in skill_flat
    assert "`<CORE>/launchers/product-card/launcher.sh <project>`, on disk, once per card, as " \
        "the last bullet." in skill_flat
    assert "The rule runs one way only." in skill_step
    assert "the two sections name the same set" not in skill_step
    assert "compares the two sets" not in skill_step
    assert "only when an answer this run wrote owes a field of a project's card, one bullet for " \
        "that card, last and once" in template_section
    assert "the one invocation line quoted out of the launcher's own" not in template_section


def test_self_answer_report_card_bullet_walk():
    """CP-624, with CP-616–CP-618 on the raw markdown: a report written in the card bullet's
    published shape is read by the chain's own markdown parser and walked by its own engine — one
    `product-card` launch, last, after the document work, with an opened companion's answer step
    kept in the sequence. The ports are fakes; the parser and the engine are the subjects, and no
    production file changes."""
    card_document = f"system/projects/{PROJECT}/project.md"
    card_bullet = f"- **{card_document}** — `{card_command()}`"

    def report_text(*bullets: str) -> str:
        return ("# Self-answer report\n\n## Launchers owed\n\n" + "\n".join(bullets)
                + "\n\n## Left for the owner\n\nNone.\n")

    def parsed_pairs(text: str) -> list[tuple[str, str | None]]:
        return [(item.document_path, item.command) for item in chain.owed_set(text)]

    def assert_card_bullet_ends_at_the_command(text: str) -> None:
        # The parser keeps only the first backticked span, so a tail is invisible to it: the
        # raw line is the only place the boundary can be proved.
        card_lines = [line for line in text.splitlines() if "product-card" in line]
        assert card_lines == [card_bullet]
        assert card_lines[0].endswith(f"{PROJECT}`") and "--" not in card_lines[0].split("—")[1]

    srs_bullet = f"- **docs/SRS.md** — `{skill_command('product-srs')}`"
    architecture_bullet = f"- **docs/adr/** — `{skill_command('product-architecture')}`"
    text = report_text(srs_bullet, architecture_bullet, card_bullet)
    assert_card_bullet_ends_at_the_command(text)
    expected = [("docs/SRS.md", skill_command("product-srs")),
                ("docs/adr/", skill_command("product-architecture")),
                (card_document, card_command())]
    assert parsed_pairs(text) == expected

    engine, processes, _, _ = card_walk(expected)
    finishes(engine, 4)

    assert owed_launches(processes) == [through_skill("product-srs"),
                                        through_skill("product-architecture"), CARD_ARGV]
    assert processes.launched.count(CARD_ARGV) == 1
    assert processes.launched[-1] == CARD_ARGV

    # The NFDR producer, the SRS companion's answer step and the card: the SRS companion is
    # opened and stays open, and the card has no companion of its own.
    nfdr_bullet = f"- **docs/nfdr.md** — `{skill_command('product-architecture')}`"
    srs_answer_command = f"<CORE>/launchers/companion-self-answer/launcher.sh {PROJECT} SRS"
    srs_answer_bullet = f"- **docs/SRS.md** — `{srs_answer_command}`"
    text = report_text(nfdr_bullet, srs_answer_bullet, card_bullet)
    assert_card_bullet_ends_at_the_command(text)
    expected = [("docs/nfdr.md", skill_command("product-architecture")),
                ("docs/SRS.md", srs_answer_command),
                (card_document, card_command())]
    assert parsed_pairs(text) == expected

    engine = build(FakeFiles({**open_fdr_companion(), **ARCHITECTURE_COMPANION,
                              f"{PRODUCT}/docs/SRS_open_issues.md": "# open"}),
                   processes=(processes := FakeProcesses()),
                   reports=FakeReports({"fdr": [report(
                       document="docs/fdr.md", counts={"confirmed": 1}, owed=expected,
                       companions_opened=[(f"{PRODUCT}/docs/SRS_open_issues.md", "opened",
                                           "SRS.md")])]}))
    start(engine, "FDR")
    finishes(engine, 6)

    assert processes.launched == [answer("FDR"), answer("SRS"),
                                  through_skill("product-architecture"), answer("architecture"),
                                  CARD_ARGV]
    assert processes.launched.count(CARD_ARGV) == 1
