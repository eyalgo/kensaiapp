"""chain.py — the engine that walks the spine it is given, advanced by the event.

WHY THIS EXISTS
    A project's documents fold in a fixed shape: `producer launcher -> companion-self-answer
    -> producer`, repeated, one cycle per document, upstream first. Walking that by hand is
    what this engine replaces. It never waits on a run: the completion watcher's `--on-complete`
    hook (`watch_process.py`, through `watch_agent.run_on_complete_hook`) calls the chain with an
    outcome value the moment a launched run stops, one argument
    and nothing else — no run identity, no document. So the chain keeps its own position on
    disk (`ChainState`) and reads it fresh on every call; `advance()` is idempotent by
    construction (fed the same event twice, it advances once), which is what lets a fresh
    process — a re-fired hook, a hand-run retry after a crash — resume exactly where the file
    and the disk agree.

WHAT IT IS GIVEN, AND WHY THAT IS THE DESIGN
    Every collaborator this engine uses is handed to it: the SPINE it walks, the document
    REGISTRY it reads a document's shape from, and the four ports — `files`, `processes`,
    `reports`, `notifier` — plus the environment it launches into and the engine path its
    shim pins. `main()` is the only function in this file that constructs a concrete
    implementation, per `<CORE>/doctrine/engineering/arch_defaults.md` § Composition Root.

    This is not decoration. The engine that preceded this one built its own collaborators,
    and all three defects the owner rejected it for on 2026-09-01 were that fact wearing
    different clothes: a spine it could not be given (so a second chain could not differ from
    the first), a suite that could not see a walk (so 197 tests were green over a feature that
    did not exist), and a shim that read `__file__` (so editing this file killed a chain in
    flight). A module that constructs its own dependencies cannot be varied and cannot be
    tested at its seams.

THE SPINE AND THE OWED SET ARE TWO DIFFERENT THINGS
    The SPINE is what a chain walks on its own initiative — an ordered tuple of documents,
    handed in by the launcher that started it and persisted on the state. The OWED SET is what
    a self-answer report asks for, and it is never narrowed by the spine: an owed bullet
    naming a document outside it is run anyway, sorted by `DEPENDENCY_ORDER` so a document is
    never run before one it reads. That is the owner's own ruling, 2026-08-31 — "the name
    states the entry and the spine, not the blast radius". One launch is the exception to that
    order: a validated `product-card` launch runs after every other item the queue holds, at
    every dispatch, and once per drain (below).

THE CYCLE
    For the document in front of it: document absent -> launch the producer; a companion
    present -> launch `companion-self-answer`; neither -> classify without launching anything.
    A stamped placeholder is absent, not present — `DocumentSpec.placeholder_marker`.
    A self-answer's own report says what happens next: its `## Launchers owed` section is the
    owed set — the document it answered plus every companion it opened — and that set drains,
    upstream first, before the spine moves past the documents it names. The card is the one
    item that does not take its document's place in that order: a command that validates to
    the `product-card` launcher is a card item, and it launches after every other item the
    queue holds, the later-added and the unresolved-document ones included, in the order the
    card items arrived. Equal validated argv is one launch, kept as the copy queued first, and
    it is launched once per DRAIN: `ChainState.card_launches_in_drain` remembers each launched
    card until the empty queue hands over to the next spine document or concludes the walk, so
    the answer round the card's own completion opens cannot owe it a second time. A command the
    check refuses is no card item; it keeps its document's place and is refused there. A command
    quoted from that section is never shelled: it is tokenized, matched against a real
    `launcher.sh` under `<CORE>/launchers/`, and its positional count checked against that
    launcher's own `# USAGE` block before anything launches.

HOW A DOCUMENT IS LAUNCHED
    Every document names the skill that produces it, and its producer runs as
    `<CORE>/launchers/skill/launcher.sh <skill> <project>`, from that skill's own `launcher.md`,
    the SDD's included. The answer step is `companion-self-answer`'s launcher, and an owed
    bullet is launched as quoted once it validates. The owner's ruling, 2026-09-17, which also
    retired the per-skill launchers.

    Every launcher but one detaches: it starts its run, leaves a watcher that calls the
    launch's shim when the run ends, and exits. The card launcher runs in the foreground and
    leaves no watcher, because its second half reads the card its first half writes — so a
    card launch that exits 0 IS the run's end, and `_launch` finishes it itself, as the shim
    would have with `completed`. Until 2026-10-21 nothing did, and a walk that reached the card
    waited on its shim forever.

THE PROVIDER A LAUNCH GOES TO
    The provider the walk was forced onto (`--provider`, kept on the state as `forced_provider`),
    else the one the instance's provider file (`.providers.toml` at its root) names for the launch's
    member, else a refusal naming the entry — never a default. A document's producer, its answer
    step and a round it is owed all take that document's entry; an owed item that resolves to no
    document takes the file's owed-item entry. The file, its format and the rule are
    `providers.py`'s, and the engine is handed a `ProviderFiles`, which answers for the instance
    root a launch is for. An unforced start checks every member before it saves anything, and each
    launch reads the file again as it stands then, so a refusal mid-walk halts it. A forced walk
    never reads the file. `_launch` never lets a launch inherit `KENSAIAPP_AGENT_PROVIDER`, because
    the engine's own environment is the previous run's: it sets the variable; an unforced walk's
    on-end hook has it removed, because a chain launcher the hook may reach reads it as a force
    (`with_provider`, below, which `chain_development.py` and `build_idea.py` use too).

THE PRODUCT CHECKOUT
    `_launch` reads the product checkout — the lines `git status --porcelain
    --untracked-files=all` prints for `product_path`, the reading the seal's preflight makes — and
    keeps them on the launch's `pending` entry, so the fresh process the run's end starts can read
    them. When that run's end reaches `advance`, before anything else of it is read and whatever
    its outcome, the checkout is read again. A line present now and absent at launch ends the walk
    `machinery`, naming the document, through `_halt` so the owed queue is not drained; a checkout
    read at launch and unreadable at the end ends it the same way with its own reason. A line
    present at launch is never counted against the run. A launch whose checkout could not be read
    records nothing, and a pending with nothing recorded — that includes every one written before
    this check — is not checked. The reading, the comparison and both reasons are
    `product_checkout.py`'s, handed to the engine as `checkout`; this engine never writes the
    checkout.

THE SEVEN ENDS
    settled, empty_run, left_for_the_owner, could_not_be_settled, machinery, cap,
    no_runnable_command — kept separate because they route to different seats. `settled` and
    `empty_run` are not failures and never stop the chain. `left_for_the_owner` is recorded
    with the unsettled ends and does not stop the chain either: an item left for the owner
    blocks nothing, so the walk moves on, and the end is written only when the spine is walked
    out with that item still open. The other four are halt-fast's own concern
    (`_HALTING_ENDS`): a cycle that ends on one of them stops the whole chain — forfeiting unstarted siblings
    is the accepted cost — unless the queue already holds something that could still change
    the outcome, in which case draining it continues instead. There is no entry gate anywhere
    in this module: an unsettled upstream is read, never waited for, because no producer waits
    for one either.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import traceback
import uuid
from collections.abc import Iterable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar

import completion_shim
import pin
import product_checkout
import providers
import reporters
import walk_stop
from providers import ProviderFiles, ProvidersRefused
from run_intelligence import PROVIDERS

__version__ = "5.9.4"

# The state file's own shape. `StateStore.load` refuses anything else by name rather than
# raising out of the completion hook, because the hook's traceback is what killed a live
# chain on 2026-09-01 when an engine edit landed under a running walk.
STATE_SCHEMA = 2

# What `main` returns when a start is refused because the project's chain is still walking. A
# caller that launches a chain tells that refusal from every other failure by this number.
EXIT_ALREADY_WALKING = 4


def walk_is_live(raw: dict) -> bool:
    """Whether a state file's raw dict is a walk that is still going — the one rule the chain's
    own refusal and any other module asking "is this project mid-walk" both apply."""
    if not raw or raw.get("ended") is not None:
        return False
    if raw.get("pending") is None:
        return False
    # A walk this engine could not resume even if asked: `advance` refuses it, so nothing is
    # coming to finish it, and calling it live would lock a project out of its own launcher.
    # Live shape, 2026-09-01: a product's state was written at an older schema and its chain
    # died inside the completion hook — the owner's next `chain-foundation <project>` has to
    # start, not wait on a walk that ended hours ago.
    return raw.get("schema_version") == STATE_SCHEMA


# --- The document registry: one record per document, and nothing else describing one -------


class Home(str, Enum):
    """Where a document and its companion live. `(str, Enum)` because a member's value is
    written out as well as compared, per `conventions.md` § Constructs."""

    PRODUCT_DOCS = "product_docs"        # <product>/docs/
    INSTANCE_PROJECT = "instance_project"  # <instance>/system/projects/<project>/


class Shape(str, Enum):
    """What "present" means for a document."""

    FILE = "file"
    RECORD_DIRECTORY = "record_directory"   # the ADR: numbered records, no single file


# --- The provider a launch carries ---------------------------------------------------------
#
# Which provider a launch goes to is `providers.py`'s rule over `.providers.toml`: the forced one,
# else the file's entry for the launch's member, else a refusal. What is left here is how the
# answer travels. The launchers below an engine read the variable as their provider, and a chain
# launcher reads it as a force — so an engine always sets or removes it, and never lets a launch
# inherit the one its own process was started under, which is only the previous run's.

PROVIDER_VARIABLE = "KENSAIAPP_AGENT_PROVIDER"


def with_provider(env: dict, provider: str) -> dict:
    """A copy of `env` carrying `provider`, or carrying none when `provider` is empty."""
    carried = dict(env)
    if provider:
        carried[PROVIDER_VARIABLE] = provider
    else:
        carried.pop(PROVIDER_VARIABLE, None)
    return carried


@dataclass(frozen=True)
class DocumentSpec:
    """Everything this engine knows about one document, in one place.

    Its predecessor spread the same knowledge across eight module-level tables and three
    `if document is X` branches, so adding a document — or reading what the engine believed
    about one — meant visiting nine sites. `home` and `shape` are what retired two of those
    branches: they are fields, not special cases."""

    name: str
    # The skill that produces this document — what `<CORE>/launchers/skill/launcher.sh` starts,
    # from that skill's own `launcher.md`.
    skill: str
    stem: str
    self_answer_arg: str
    home: Home = Home.PRODUCT_DOCS
    shape: Shape = Shape.FILE
    # `None` means "derive it from the document's own stem as found on disk" — measured on a
    # live product, `docs/SRS.md`'s companion is `docs/srs_open_issues.md`, because the run
    # that opened it took the stem from the lower-case template filename. A literal is for the
    # companion that is named for neither document it answers for: ADR and NFDR share one,
    # because one `product-architecture` run writes both.
    companion_stem: str | None = None
    # Extra path segments that name this document in a report's bullet.
    aliases: tuple[str, ...] = ()
    # A file carrying this text is the stamped placeholder, not the document, and reads as
    # absent. `project-stamp` writes `agari.md` before any Agari exists, from a template that
    # carries `PLACEHOLDER` (`agari_template.md:12`) — the same signal `reporters.py` keys on.
    placeholder_marker: str | None = None

    @property
    def trail_stem(self) -> str:
        """The `trail/<stem>/` directory this document's self-answer report lands in — Step 5
        composes it from the companion's own stem, lower-cased, which is the same value
        `companion-self-answer` takes as its `<document>` argument."""
        return self.self_answer_arg.lower()


def _spec(name, skill, stem, *, self_answer_arg=None, **kwargs) -> DocumentSpec:
    return DocumentSpec(name=name, skill=skill, stem=stem,
                        self_answer_arg=self_answer_arg or name, **kwargs)


# ADR and NFDR share `product-architecture`, because one run writes both the ADR records and the
# NFDR.
DOCUMENT_REGISTRY: dict[str, DocumentSpec] = {
    spec.name: spec for spec in (
        _spec("PRD", "product-prd", "prd"),
        _spec("Agari", "project-agari", "agari", home=Home.INSTANCE_PROJECT,
              companion_stem="agari_open_issues", placeholder_marker="PLACEHOLDER"),
        _spec("SRS", "product-srs", "srs"),
        _spec("UXD", "product-uxd", "uxd"),
        _spec("DESIGN", "product-design", "design"),
        _spec("CONTENT", "product-content", "content"),
        _spec("SDD", "product-sdd", "sdd"),
        _spec("FDR", "product-fdr", "fdr"),
        _spec("ADR", "product-architecture", "adr", self_answer_arg="architecture",
              shape=Shape.RECORD_DIRECTORY, companion_stem="architecture_open_issues",
              aliases=("adr",)),
        _spec("NFDR", "product-architecture", "nfdr", self_answer_arg="architecture",
              companion_stem="architecture_open_issues"),
    )
}


# Which document reads which — used to sort an owed set so a document is never run before one
# it reads, and for nothing else. It is NOT a walk order: what a chain walks is the spine it
# was given. Members of one tier share a rank, because nothing orders UXD against DESIGN
# against CONTENT, or ADR against NFDR.
DEPENDENCY_ORDER: tuple[tuple[str, ...], ...] = (
    ("PRD",), ("Agari",), ("SRS",), ("UXD", "DESIGN", "CONTENT"), ("SDD",), ("FDR",),
    ("ADR", "NFDR"),
)

_RANK: dict[str, int] = {name: rank
                          for rank, tier in enumerate(DEPENDENCY_ORDER)
                          for name in tier}


def document(name: str) -> DocumentSpec:
    """The spec for `name`, matched case-insensitively. Raises `KeyError` for an unknown
    document — a name this engine cannot describe is never guessed at."""
    for spec in DOCUMENT_REGISTRY.values():
        if spec.name.lower() == name.strip().lower():
            return spec
    raise KeyError(name)


def canonical_rank(spec: DocumentSpec) -> int:
    """Where `spec` sits in the dependency order — lower sorts earlier. Two documents in the
    same tier share a rank; nothing orders them further."""
    return _RANK[spec.name]


def resolve_document(path: str) -> DocumentSpec | None:
    """The document a report's backticked path names, or `None` when it names none — never a
    guess. Case-insensitive, because the documents' own casing on disk is not uniform.

    An alias is matched against EVERY path segment, not just the parents: a directory is also
    named by the path that ends at it, and `adr/` — the most natural way for a report to write
    the ADR — is exactly that shape."""
    normalized = path.strip().strip("`").strip().replace("\\", "/")
    segments = [segment for segment in normalized.split("/") if segment]
    if not segments:
        return None
    lowered = {segment.lower() for segment in segments}
    for spec in DOCUMENT_REGISTRY.values():
        if lowered & {alias.lower() for alias in spec.aliases}:
            return spec
    basename = segments[-1]
    stem = basename.rsplit(".", 1)[0] if "." in basename else basename
    for spec in DOCUMENT_REGISTRY.values():
        if spec.shape is Shape.FILE and spec.stem.lower() == stem.lower():
            return spec
    # A companion names the document it answers for. A self-answer report owes a round on the
    # architecture companion by the companion's own path, because no one document is it — a
    # live product, 2026-10-20, where reading that bullet as no document ended the walk
    # `no_runnable_command` on a report that had routed the companion.
    for spec in DOCUMENT_REGISTRY.values():
        companion = spec.companion_stem or (
            f"{spec.stem}_open_issues" if spec.shape is Shape.FILE else None)
        if companion is not None and companion.lower() == stem.lower():
            return spec
    return None


def parse_spine(text: str) -> tuple[DocumentSpec, ...]:
    """A chain's spine, read off the one string its launcher hands the engine —
    `"FDR,ADR,NFDR"`. Ordered, and refused by name when it carries a document this engine
    cannot describe, so a typo in a launcher's literal fails at start rather than halfway
    through a walk."""
    names = [part.strip() for part in text.split(",") if part.strip()]
    if not names:
        raise ValueError("a chain must be given a spine — one or more document names, "
                         "comma-separated (e.g. 'FDR,ADR,NFDR')")
    spine = []
    for name in names:
        try:
            spine.append(document(name))
        except KeyError:
            known = ", ".join(DOCUMENT_REGISTRY)
            raise ValueError(f"{name!r} is not a document this engine knows — known: {known}")
    return tuple(spine)


# --- The ports -----------------------------------------------------------------------------
#
# Each is the seam one collaborator is reached through. The real implementations live at the
# bottom of this file, beside `main()`, which is the only place any of them is constructed.


class Files:
    """Every filesystem touch this engine makes."""

    def is_file(self, path: str) -> bool:
        return os.path.isfile(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def list_dir(self, path: str) -> list[str]:
        try:
            return sorted(os.listdir(path))
        except FileNotFoundError:
            return []

    def read_text(self, path: str) -> str | None:
        """`None` when the file cannot be read — an absence this engine always has a decision
        for, never an exception it would have to catch at every call site."""
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read()
        except OSError:
            return None

    def write_text(self, path: str, text: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def make_dirs(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def make_executable(self, path: str) -> None:
        os.chmod(path, 0o755)

    def replace(self, source: str, destination: str) -> None:
        os.replace(source, destination)

    def real_path(self, path: str) -> str:
        return os.path.realpath(path)


class Processes:
    """Every process this engine starts."""

    def run(self, argv, *, cwd=None, env=None, capture=False, timeout=None) -> int:
        """The command's exit status. `-1` when it could not be started at all — the caller
        treats a non-zero status as a machinery stop either way, which is why an unlaunchable
        command is a value here rather than an exception out of the completion hook."""
        try:
            result = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                                     capture_output=capture, text=True if capture else None)
        except (OSError, subprocess.SubprocessError):
            return -1
        return result.returncode


class Reports:
    """The self-answer report reader — `reporters.py` for everything it already parses, plus
    this module's own `owed_set` for the one field it reads differently."""

    def __init__(self, files: Files):
        self.files = files

    def present(self, search_root: str, trail_stem: str) -> tuple[str, ...]:
        """Every self-answer report on disk for this trail, right now — the launch-time
        reading `_launch` takes and persists on `state.reports_before`, so `.find` below
        can tell a report this round wrote from one that predates it."""
        return reporters.self_answer_reports_present(search_root, trail_stem)

    def find(self, search_root: str, trail_stem: str,
              reports_before: list | None = None) -> str | None:
        return reporters.find_self_answer_report(search_root, trail_stem, reports_before)

    def find_round(self, search_root: str, trail_stem: str,
                    reports_before: list | None = None) -> tuple[str, ...]:
        """Every report this launch wrote, ascending by report number. A companion answered
        seat by seat leaves one per run, and the round is read whole."""
        return reporters.new_self_answer_reports(search_root, trail_stem, reports_before)

    def read(self, path: str) -> SelfAnswerReport | None:
        text = self.files.read_text(path)
        if text is None:
            return None
        parsed = reporters._parse_self_answer_report(text)
        raw_document = parsed["document"]
        return SelfAnswerReport(
            document=raw_document.strip("`").strip() if raw_document else raw_document,
            counts=parsed["counts"],
            companions_opened=parsed["companions_opened"],
            owed=owed_set(text),
            raised=parsed["raised"],
            unnamed=parsed["unnamed"],
            missing_headings=reporters._self_answer_missing_headings(text),
        )


class Notifier:
    """The owner's completion channel. The command is resolved by whoever starts the chain and
    carried on the state, because the hook re-enters as a fresh process — this engine reads no
    environment for it. An unset notifier is skipped, never an error."""

    def __init__(self, command: str, processes: Processes):
        self.command = command
        self.processes = processes

    def send(self, message: str) -> bool:
        if not self.command:
            return False
        return self.processes.run([self.command, message], capture=True, timeout=60) == 0


class IdSource:
    """The one capability `start()` needs to mint a walk's own id: a string it did not already
    have. Nothing else — this is not a UUID validator and it does not read one back."""

    def new_id(self) -> str:
        return str(uuid.uuid4())


# --- The owed set is read off the report, and the tail is dropped --------------------------


@dataclass(frozen=True)
class OwedItem:
    """One `## Launchers owed` bullet: which document a round is owed on, and the command to
    run it — backticks stripped off both, everything past the command's own closing backtick
    discarded. `command` is `None` for a bullet written with no backticked command at all."""

    document_path: str
    command: str | None


def owed_set(report_text: str) -> list[OwedItem]:
    """The `## Launchers owed` section, read the way `reporters.py`'s own
    `_self_answer_launchers_owed` reads it — through `_self_answer_section` and its wrap-join,
    so a bullet split across physical lines is one entry — with one deliberate difference:
    that reader strips a value's wrapping backticks only when they wrap the whole value,
    because it is feeding a human a line to read, tail included. This reader's ruling is the
    opposite — the tail is for a person, not for the launch this engine is about to validate
    and run — so it takes only the FIRST backticked span as the command and discards the
    rest."""
    section = reporters._self_answer_section(report_text, "## Launchers owed")
    section = re.sub(r"\n[ \t]+(?=\S)", " ", section)
    items = []
    for match in re.finditer(r"^-\s+\*\*(.+?)\*\*\s+—\s+(.+?)\s*$", section, re.MULTILINE):
        document_raw, tail = match.group(1).strip(), match.group(2).strip()
        command_match = re.search(r"`([^`]+)`", tail)
        items.append(OwedItem(
            document_path=document_raw.strip("`").strip(),
            command=command_match.group(1) if command_match else None,
        ))
    return items


# --- An owed command is validated, never shelled -------------------------------------------


class CommandRefused(Exception):
    """A `## Launchers owed` command failed validation. Nothing that raises this is ever
    passed to a shell."""


class StateIncompatible(Exception):
    """The state file on disk was written by an engine with a different idea of its shape.
    Named and caught, because the alternative — a raise out of the completion hook — is what
    killed a live chain on 2026-09-01."""


class ChainAlreadyWalking(Exception):
    """A chain was asked to start over a state file that is still walking. Every chain
    launcher derives its state path from the project alone, so starting a second chain on a
    project mid-walk would overwrite the position the first is keeping. Refused by name rather
    than silently, because nothing downstream of the overwrite could ever notice it. The first
    chain's runs finishing into the second's state is `Chain.advance`'s to refuse — each
    finish names its launch. The refusal offers the stop, which ends the walk and stops the run
    it waits on and its watcher; a walk it ended keeps its state file, and a finish delivered
    after it is a counted re-entry."""


@dataclass(frozen=True)
class ValidatedCommand:
    """A command this module has proven safe to launch: a real `launcher.sh` under
    `<CORE>/launchers/<folder>/`, its positional count matched against its own `# USAGE`
    block. `argv` is a token list, never a string — there is no shell for a string to be
    interpreted by."""

    launcher_folder: str
    argv: list[str]


def _usage_signature(launcher_path: str, files: Files) -> tuple[int, bool] | None:
    """How many positional (`<...>`) arguments a launcher's own `# USAGE` block declares, read
    off the invocation line itself — the same line a bullet's command is quoted from — and
    whether a `[<name>...]` token after them takes any number more. `None` when the file carries
    no `# USAGE` block at all. The first bracketed token ends the positional run, because every
    launcher in the fleet lists its required arguments before its optional flags. The one
    variadic launcher is `skill/launcher.sh <skill> [<argument>...]`, whose arguments after the
    skill are that skill's `launcher.md`'s to judge, not this check's."""
    text = files.read_text(launcher_path)
    if text is None:
        return None
    match = re.search(r"^# USAGE\s*\n#\s+(\S.*)$", text, re.MULTILINE)
    if not match:
        return None
    count = 0
    variadic = False
    for token in match.group(1).split()[1:]:   # [0] is the launcher's own script path
        if token.startswith("<") and token.endswith(">"):
            count += 1
            continue
        variadic = bool(re.fullmatch(r"\[<[^>]+>\.\.\.\]", token))
        break
    return count, variadic


def _usage_positional_count(launcher_path: str, files: Files) -> int | None:
    """The positional count alone — `_usage_signature` without whether more may follow."""
    signature = _usage_signature(launcher_path, files)
    return None if signature is None else signature[0]


# A `[...]` token is the `# USAGE` line's own optional-flag notation, not an argument. A report
# is told to quote "the command line out of" that block, and every producer's line carries
# `[--dry-run] [--keep-awake]` after its positionals — so a bullet that quotes it faithfully
# arrives here with them attached. Live, 2026-09-01: a product whose four owed bullets were
# all refused for it.
#
# They are DROPPED rather than unwrapped. `--dry-run` honoured off a report would make the
# launcher print a command instead of running one, and the chain would go on believing it had
# launched — the quietest failure this engine could have. `--keep-awake` is the caller's own
# instruction, appended after validation, and is not a report's to ask for either.
_USAGE_PLACEHOLDER = re.compile(r"^\[.*\]$")


def _folder_from_launcher_path(path: str) -> str | None:
    """The single path segment between a `launchers/` directory and a trailing `launcher.sh` —
    the shape every host launcher's own path carries, wherever the copy naming it lives. `None`
    when `path` does not end `launchers/<something>/launcher.sh`."""
    parent, name = os.path.split(path)
    if name != "launcher.sh":
        return None
    grandparent, folder = os.path.split(parent)
    if not folder or os.path.basename(grandparent) != "launchers":
        return None
    return folder


def _folder_by_pin_equivalence(script_path: str, *, core_dir: str, instance_root: str
                                ) -> str | None:
    """`script_path`'s launcher folder, accepted only once `pin.same_launcher` confirms
    `core_dir`'s own copy of that folder is the same host launcher — the live host's own path,
    another pin of that host, or a relative `core/launchers/...` form. `None` when the path
    names no folder shape at all, or names one `core_dir` does not share with it."""
    folder = _folder_from_launcher_path(script_path)
    if folder is None:
        return None
    expected = os.path.join(core_dir, "launchers", folder, "launcher.sh")
    if pin.same_launcher(script_path, expected, core_dir=core_dir, instance_root=instance_root):
        return folder
    return None


def validate_owed_command(command: str | None, *, core_dir: str, instance_root: str, files: Files
                           ) -> ValidatedCommand:
    """Prove `command` — a bullet's text, never a value to hand a shell — names a real
    launcher under `<core_dir>/launchers/` with the right number of positional arguments, or
    refuse it with `CommandRefused` naming what failed. `<CORE>` is resolved before anything is
    stat-ed, because it appears literally in a report's command. A path naming a different copy
    of the same host launcher — the live host's own, another pin of it, or a relative
    `core/launchers/...` form — is accepted too, through `pin.same_launcher`; what the returned
    `argv` runs is always `core_dir`'s own copy, never the path the bullet happened to name."""
    if not command:
        raise CommandRefused("no command to validate")
    resolved = command.replace("<CORE>", core_dir)
    try:
        argv = shlex.split(resolved)
    except ValueError as exc:
        raise CommandRefused(f"could not tokenize {command!r}: {exc}") from exc
    if not argv:
        raise CommandRefused(f"{command!r} tokenizes to nothing")
    argv = [argv[0]] + [token for token in argv[1:] if not _USAGE_PLACEHOLDER.match(token)]

    script_path = argv[0]
    launchers_dir = files.real_path(os.path.join(core_dir, "launchers"))
    real_script = files.real_path(script_path)
    try:
        shared = os.path.commonpath([real_script, launchers_dir])
    except ValueError:
        # A relative path against an absolute launchers directory — `commonpath` raises here,
        # and a raise that is not `CommandRefused` leaves the completion hook. It is still
        # offered to the equivalence check below, which reads a relative path from the instance
        # root: a `core/launchers/…` bullet names a host launcher (CP-114). Live shape of the
        # refusal: the honest-absence bullet, whose command is a producing skill's bare name
        # (`product-nfdr`) rather than a path.
        shared = None
    if shared != launchers_dir:
        elsewhere = _folder_by_pin_equivalence(script_path, core_dir=core_dir,
                                                instance_root=instance_root)
        if elsewhere is None and shared is None:
            raise CommandRefused(f"{script_path} is not an absolute path under {launchers_dir}")
        if elsewhere is None:
            raise CommandRefused(f"{script_path} is not under {launchers_dir}")
        real_script = os.path.join(launchers_dir, elsewhere, "launcher.sh")
        argv = [real_script] + argv[1:]
    if os.path.basename(real_script) != "launcher.sh":
        raise CommandRefused(f"{script_path} is not a launcher.sh")
    folder = os.path.relpath(os.path.dirname(real_script), launchers_dir)
    if folder in ("", os.curdir, os.pardir) or os.sep in folder:
        raise CommandRefused(f"{script_path} does not resolve to one launcher folder")
    if not files.is_file(real_script):
        raise CommandRefused(f"no launcher.sh on disk at {script_path}")

    signature = _usage_signature(real_script, files)
    if signature is None:
        raise CommandRefused(f"{folder}'s launcher.sh carries no # USAGE block")
    required, variadic = signature
    given = [token for token in argv[1:] if not token.startswith("-")]
    if variadic and len(given) < required:
        raise CommandRefused(f"{folder} takes at least {required} positional argument(s), "
                             f"{command!r} gives {len(given)}")
    if not variadic and len(given) != required:
        raise CommandRefused(
            f"{folder} takes {required} positional argument(s), {command!r} gives {len(given)}")

    return ValidatedCommand(launcher_folder=folder, argv=argv)


# --- The cycle's next step follows the disk ------------------------------------------------


class CycleEntry(str, Enum):
    PRODUCER = "producer"
    ANSWER = "answer"
    NONE = "none"


@dataclass(frozen=True)
class DocumentLocation:
    document_path: str | None
    companion_path: str | None
    document_present: bool
    companion_present: bool
    # The file is on disk but is still the stamped placeholder — so `document_present` is False.
    placeholder: bool = False


def cycle_entry(location: DocumentLocation) -> CycleEntry:
    """Document absent -> the producer. Companion present -> the answer step. Neither -> no
    launch at all, a later classification and never this function's to make."""
    if not location.document_present:
        return CycleEntry.PRODUCER
    if location.companion_present:
        return CycleEntry.ANSWER
    return CycleEntry.NONE


# --- The cycle's seven ends, and the round that changed nothing ----------------------------


class CycleEnd(str, Enum):
    """The seven places a cycle can stop, kept separate because they route to different
    seats: a settled document needs nobody; an empty run is not a failure; a signature is owed
    to the owner; a repair is owed to the producing skill; a failed run or the reporter's own
    anomaly is machinery; the round cap is a knob, not a verdict; and an owed bullet with no
    runnable command is refused, not retried."""

    SETTLED = "settled"
    EMPTY_RUN = "empty_run"
    LEFT_FOR_THE_OWNER = "left_for_the_owner"
    COULD_NOT_BE_SETTLED = "could_not_be_settled"
    MACHINERY = "machinery"
    CAP = "cap"
    NO_RUNNABLE_COMMAND = "no_runnable_command"


# A knob with no measured basis, recorded as one.
DEFAULT_CYCLE_CAP = 3

# The launcher folder whose launch is the card: it runs once per drain, after every other owed item.
CARD_LAUNCHER_FOLDER = "product-card"

# Ends that are RECORDED — a cycle that did not settle, whether or not the walk goes on. Read by
# `_reach_end` to decide what lands in `state.deferred_ends`, so the owner is told at the conclusion.
_UNSETTLED_ENDS = frozenset({
    CycleEnd.LEFT_FOR_THE_OWNER,
    CycleEnd.COULD_NOT_BE_SETTLED,
    CycleEnd.MACHINERY,
    CycleEnd.CAP,
    CycleEnd.NO_RUNNABLE_COMMAND,
})

# Ends that HALT the walk — the four real failures. Narrower than the recorded set by exactly one
# member, and the difference is the point: `LEFT_FOR_THE_OWNER` is a SUCCESSFUL cycle. It produced a
# decision — that this item is the owner's — and `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md`
# § *Nothing you leave blocks* says so in as many words: an item left for the owner "blocks nothing
# else", and "that an item is left costs the chain nothing", resting on the owner's call of
# 2026-08-29 that the gates downstream read an unsettled document. That call shipped in the prompt
# and never reached here, so for a year the engine abandoned a walk over a verdict the prompt
# promised was free. Measured on a live product, 2026-09-03: two chains ended this way, the
# second (that product's `caa3e0c`) over one item about what a version number promises, with a
# decided answer left
# unfolded behind it.
#
# It stays in the recorded set. Not halting is not the same as not happening.
_HALTING_ENDS = _UNSETTLED_ENDS - {CycleEnd.LEFT_FOR_THE_OWNER}


@dataclass(frozen=True)
class SelfAnswerReport:
    """What one `companion-self-answer` run produced, read off its own report file."""

    document: str | None
    counts: dict
    companions_opened: list
    owed: list[OwedItem]
    raised: int
    unnamed: int
    missing_headings: list[str]


_RoundEntry = TypeVar("_RoundEntry")


def _without_repeats(entries: Iterable[_RoundEntry]) -> list[_RoundEntry]:
    """`entries` in order with each exact repeat dropped. Compared by equality, not by hash:
    an opened companion is a list, which a set cannot hold."""
    kept = []
    for entry in entries:
        if entry not in kept:
            kept.append(entry)
    return kept


def combine_round(pairs: list[tuple[str, SelfAnswerReport | None]]) -> SelfAnswerReport | None:
    """One report for a launch that left several, from `(path, report-or-None)` pairs in report
    order. `None` stands for a report that could not be read.

    Nothing or one report is returned as read — the same object, so a launch that left a single
    report reads exactly as it did before a launch could leave several. Two or more are folded:
    the verdict tallies, `raised` and `unnamed` are summed; `owed` and `companions_opened` keep
    report order with each exact repeat dropped (two spellings of one launcher stay two entries
    here, and are queued once by `Chain._queue_owed`); the document is the first one a report
    names.

    A round whose verdicts are not all known is not counted, so a report that lacks a required
    heading, or cannot be read, makes the whole round a machinery stop — its entry in
    `missing_headings` carries the file's name, which is how the reason names it."""
    if not pairs:
        return None
    if len(pairs) == 1:
        return pairs[0][1]

    counts: dict = {}
    missing: list[str] = []
    for path, member in pairs:
        name = os.path.basename(path)
        if member is None:
            missing.append(f"{name}: could not be read")
            continue
        missing += [f"{name}: {heading}" for heading in member.missing_headings]
        for verdict, count in member.counts.items():
            counts[verdict] = counts.get(verdict, 0) + count
    members = [member for _, member in pairs if member is not None]
    return SelfAnswerReport(
        document=next((member.document for member in members if member.document), None),
        counts=counts,
        companions_opened=_without_repeats(
            entry for member in members for entry in member.companions_opened),
        owed=_without_repeats(item for member in members for item in member.owed),
        raised=sum(member.raised for member in members),
        unnamed=sum(member.unnamed for member in members),
        missing_headings=missing,
    )


def classify_report(report: SelfAnswerReport | None) -> CycleEnd | None:
    """Which of the seven ends this report reaches — or `None`, meaning continue the cycle.

    - No report at all: the answer step met an absent companion, so the document already reads
      settled. The one point this module parses nothing.
    - Missing required headings: not in the template's shape, so a machinery stop — there is
      nothing here to classify.
    - Any `left for the owner` item: the unsettled end halt-fast reacts to.
    - Otherwise both "items worked" and "worked none, owner none, launchers owed" continue —
      a round that changed nothing on its own report still advances. A genuinely empty run —
      nothing worked, nothing owed, nothing raised, no companion opened — is the one case
      left, and it is not a failure either."""
    if report is None:
        return CycleEnd.SETTLED
    if report.missing_headings:
        return CycleEnd.MACHINERY
    if report.counts.get("left for the owner", 0):
        return CycleEnd.LEFT_FOR_THE_OWNER
    # A RAISED item is deliberately not an end here, and that is measured rather than assumed.
    # `## Raised on this document` is a new item a run found while reading the document whole
    # and did not decide itself; it looks like an owner-facing slot, and ending on it was tried
    # and is wrong. An end reached here skips the branch below that queues the report's owed
    # set, so halting on a raise halts BEFORE the producer that would fold it ever runs — and a
    # producer often folds it: a live product, 2026-09-01, `e59446a` "SDD open issues
    # answered — 2 of 2 items, and a third raised on the document itself" then `5c776aa` "SDD
    # run 3 folds the
    # reopened companion into v3, closes clean". On that same walk, ending here would have
    # stopped at the SRS and forfeited UXD, DESIGN, CONTENT and SDD — 177 dead trail pointers
    # repaired and one document settled.
    #
    # What catches a raise the producer could NOT fold is the disk, one step later: a producer
    # whose companion is still there sends its document back through the answer step
    # (`Chain._step`), and the round that follows reports the slot for what it is. Live: one
    # product's SRS and CONTENT, whose raised items survived their folds and stayed open.
    worked = (sum(count for verdict, count in report.counts.items()
                  if verdict != "left for the owner")
              + report.unnamed)
    if worked == 0 and not report.owed and not report.raised and not report.companions_opened:
        return CycleEnd.EMPTY_RUN
    return None


def round_signature(report: SelfAnswerReport) -> tuple:
    """The set of open items a round leaves behind, text included — sorted so the comparison
    is order-independent, and never the report file's bytes, which always move.

    It is NOT the owed set alone: the owed set is a routing list, so a document folding in
    place owes the same bullet every round however much moved on it. Measured on a real
    product's live SRS cycle, both rounds read 2026-08-31: both carry an identical owed
    section, and the second is the one that must CONTINUE. Keyed on the owed set alone, that
    round reads as stagnation and halts the chain on its own live proof. So the signature also
    carries what the round decided — the verdict tally, the unnamed verdicts, the items it
    raised, and the companions it opened."""
    return (
        tuple(sorted((item.document_path, item.command) for item in report.owed)),
        tuple(sorted((verdict, count) for verdict, count in report.counts.items() if count)),
        report.unnamed,
        report.raised,
        tuple(sorted(str(entry) for entry in report.companions_opened)),
    )


def _comparable(value):
    """`value` in the shape a JSON round trip leaves it — every tuple a list — so a signature
    read back off the state file compares equal to one just built in memory."""
    if isinstance(value, (list, tuple)):
        return [_comparable(item) for item in value]
    return value


def next_round_end(previous_signature, report: SelfAnswerReport, round_number: int,
                    cap: int = DEFAULT_CYCLE_CAP) -> CycleEnd | None:
    """Given `classify_report` already said continue, whether a full round actually made
    progress. An unchanged signature is `COULD_NOT_BE_SETTLED`; reaching `cap` rounds is
    `CAP`, checked after stagnation so a round that both stagnates and hits the cap reports
    the more specific cause."""
    signature = round_signature(report)
    if (previous_signature is not None
            and _comparable(signature) == _comparable(previous_signature)):
        return CycleEnd.COULD_NOT_BE_SETTLED
    if round_number >= cap:
        return CycleEnd.CAP
    return None


def _companion_paths(report: SelfAnswerReport) -> list[str]:
    """The companion file paths a report's `## Companions opened` names — its FIRST field, the
    path, as against `unrouted_companions`, which reads the last one, the document. Backticks
    stripped; a relative path is left as it is and the sweep that reads these simply will not
    find it on disk, which is the honest outcome for a path this engine cannot resolve."""
    paths = []
    for entry in report.companions_opened:
        if isinstance(entry, (list, tuple)) and entry:
            path = str(entry[0]).strip().strip("`").strip()
            if path:
                paths.append(path)
    return paths


def unrouted_companions(report: SelfAnswerReport) -> list[str]:
    """The documents `## Companions opened` names that no `## Launchers owed` bullet does.

    The owed set has two derivations and they are one set. Where they disagree the chain has a
    document it is owed a round on and no command to run it with — never a document it
    silently forgets, because a forgotten one takes its whole sub-graph with it. Matched on
    the bullet's own path first and on the resolved document second, so a report spelling the
    same document two ways is not read as a disagreement."""
    owed_paths = {item.document_path.strip("`").strip() for item in report.owed}
    owed_documents = {resolve_document(item.document_path) for item in report.owed}
    owed_documents.discard(None)
    unrouted = []
    for entry in report.companions_opened:
        document_path = str(entry[-1]).strip("`").strip()
        if document_path in owed_paths:
            continue
        spec = resolve_document(document_path)
        if spec is not None and spec in owed_documents:
            continue
        unrouted.append(document_path)
    return unrouted


def sort_owed_by_dependency(items: list[OwedItem]) -> list[OwedItem]:
    """`items`, upstream first — a document is never run before one it reads. An item whose
    document does not resolve sorts last, so it never blocks one that does; `sorted` is
    stable, so two items in the same tier keep the order they arrived in."""

    def sort_key(item: OwedItem) -> tuple[int, int]:
        spec = resolve_document(item.document_path)
        return (1, 0) if spec is None else (0, canonical_rank(spec))

    return sorted(items, key=sort_key)


def next_owed_item(queue: list[OwedItem]) -> tuple[OwedItem | None, list[OwedItem]]:
    """Pop the most upstream item off `queue` — `(item, remaining)`, or `(None, [])` when it
    is empty."""
    if not queue:
        return None, []
    head, *rest = sort_owed_by_dependency(queue)
    return head, rest


def _is_card(validated: ValidatedCommand | None) -> bool:
    """Whether `validated` — an owed command that passed the check — is the card's launcher."""
    return validated is not None and validated.launcher_folder == CARD_LAUNCHER_FOLDER


def _owed_identity_of(validated: ValidatedCommand | None, command: str | None) -> tuple[str, ...]:
    """What makes two owed commands one launch: the argv the check resolves them to, or, for a
    command it refuses, its own text."""
    if validated is None:
        return ("unresolved", command or "")
    return tuple(validated.argv)


def should_halt(end: CycleEnd, remaining_queue: list[OwedItem]) -> bool:
    """Halt-fast: a cycle that ends in FAILURE stops the whole chain — forfeiting unstarted
    siblings is the accepted cost — unless the queue already holds something that could still
    change that outcome, in which case draining it continues instead.

    Reads `_HALTING_ENDS`, not `_UNSETTLED_ENDS`: an item left for the owner is recorded and
    walked past, per that constant's own note. `_conclude` does not rely on this — its
    out-of-moves branch halts directly."""
    if end not in _HALTING_ENDS:
        return False
    return not remaining_queue


# What the owner does next, for each of the seven ends. Keyed on `CycleEnd` so a new end
# cannot be added without this table also growing.
_END_GUIDANCE: dict[CycleEnd, str] = {
    CycleEnd.SETTLED: "every spine document this chain walked is settled — nothing left to do.",
    CycleEnd.EMPTY_RUN: "the last run produced nothing — not a failure; the chain moves on.",
    CycleEnd.LEFT_FOR_THE_OWNER:
        "an item is left for the owner to decide — answer it on the document's own companion, "
        "then re-enter the chain.",
    CycleEnd.COULD_NOT_BE_SETTLED:
        "a full round left the open items unchanged — a repair is owed to the producing skill.",
    CycleEnd.MACHINERY:
        "a run failed to complete, or its report was not in the template's shape — read the "
        "run's own log.",
    CycleEnd.CAP:
        f"the cycle reached its round cap ({DEFAULT_CYCLE_CAP} rounds) without settling — read "
        "the document's own trail.",
    CycleEnd.NO_RUNNABLE_COMMAND:
        "an owed bullet named no real launcher — a repair is owed to the producing skill's own "
        "Step 6.",
}


@dataclass(frozen=True)
class ChainEnding:
    """Everything the owner's message needs to read one chain's stop, gathered in one value
    rather than passed as positional scalars a reorder could silently break
    (`python/conventions.md` § Constructs — the house's own default for a value read after it
    is built). Built once, by `.of()`, off the state the walk is actually keeping."""

    end: CycleEnd
    chain_name: str
    project: str
    document: str | None
    spine: tuple[str, ...]
    position: int
    reason: str
    deferred: str

    @classmethod
    def of(cls, state: "ChainState", end: CycleEnd, document: str | None,
           reason: str) -> "ChainEnding":
        return cls(
            end=end, chain_name=state.chain_name, project=state.project, document=document,
            spine=tuple(state.spine), position=state.spine_index, reason=reason,
            deferred=_deferred_summary(state))


def describe_end(ending: ChainEnding) -> str:
    """The message the owner reads: an unmistakable banner, then one labelled fact per line, so
    the eye finds a fact without reading prose. `end:` (plus which document, or the whole
    walk), `walk:` (the spine in order, then how far in), `why:` (the raw reason — never the
    reason composed with what the queue deferred; that is `also:`'s alone), `next:` (the
    guidance table, verbatim), and `also:` (omitted when nothing was deferred)."""
    banner = (f"CHAIN ENDED — {ending.chain_name} / {ending.project}" if ending.chain_name
             else f"CHAIN ENDED — {ending.project}")
    where = f"at {ending.document}" if ending.document else "the whole walk"
    lines = [
        banner,
        f"end: {ending.end.value} — {where}",
        f"walk: {', '.join(ending.spine)} — {ending.position} of {len(ending.spine)} entered",
        f"why: {ending.reason}",
        f"next: {_END_GUIDANCE[ending.end]}",
    ]
    if ending.deferred:
        lines.append(f"also: {ending.deferred}")
    return "\n".join(lines)


def describe_start(state: "ChainState") -> str:
    """The message the owner reads when a walk begins — `describe_end`'s shape, so a start and
    its end read as one pair: a banner, then one labelled fact per line.

    Why a chain says anything at all on the way in (the owner's ask, 2026-09-03): a walk runs
    for hours and, until this, spoke only when it stopped. On 2026-09-03 two chains were taken
    for running long after they had died, because nothing had ever marked the beginning against
    which the silence could be read. `engine:` carries the version because the engine changes
    under the walks it runs, and an end whose behaviour surprises the owner is read against the
    version that started it, not the one on disk when it finished.
    """
    banner = (f"CHAIN STARTED — {state.chain_name} / {state.project}" if state.chain_name
             else f"CHAIN STARTED — {state.project}")
    return "\n".join([
        banner,
        f"walk: {', '.join(state.spine)} — {len(state.spine)} to enter",
        f"product: {state.product_path}",
        f"engine: chain.py {__version__}",
    ])


def _deferred_summary(state: "ChainState") -> str:
    """What `state.deferred_ends` says, as one clause — the module-level author `ChainEnding.of`
    and `Chain._halt_reason` share, so the `also:` line on the message and the composed
    `ended_reason` on disk are never independently wrong of each other."""
    if not state.deferred_ends:
        return ""
    earlier = "; ".join(
        f"{name or 'the chain'} — {end}" + (f" ({text})" if text else "")
        for end, name, text in state.deferred_ends)
    return f"earlier, while the queue drained: {earlier}"


def describe_refusal(reason: str) -> str:
    """The message the owner reads when a chain's walk stops with no `CycleEnd` reached at
    all — refused before it could resume or start, or crashed advancing on an event neither
    was ever caught by name. Never `describe_end`'s `CHAIN ENDED` banner: every one of these
    leaves `ended: null` on disk, so a banner claiming an end would be a false report. Task 7's
    own words for `StateIncompatible` — that walk is *stranded*, not ended — extended to a
    third, unnamed case: a crash is unresolved the same way a refusal is."""
    return f"chain: UNRESOLVED — {reason}"


def run_end_hook(hook: str, end: str, *, cwd: str, processes: Processes, notifier: Notifier,
                 headline: str, env: dict | None = None) -> None:
    """Run the `--on-end` command a walk was started with, once, with the end appended. The hook is
    split the way a shell quotes it, and a hook that fails costs the owner one message and nothing
    else: the walk's end is already recorded and is not this command's to undo. `chain_development`
    ends its walks through this too, so a hook means one thing in both engines."""
    try:
        words = shlex.split(hook)
    except ValueError as exc:
        # A string that cannot be split is a hook that cannot start; it runs nothing.
        notifier.send(f"{headline} — the on-end hook {hook!r} could not be started: {exc}")
        return
    if not words:
        return
    exit_code = processes.run(words + [end], cwd=cwd, env=env)
    if exit_code != 0:
        # `Processes.run` answers -1 for a command it could not start, so one branch is both.
        notifier.send(f"{headline} — the on-end hook {hook!r} exited {exit_code}")


# --- The state file ------------------------------------------------------------------------


@dataclass
class ChainState:
    """Everything a fresh process needs to pick the walk up where the last one left it. The
    hook hands the entrypoint an outcome and nothing else — no run identity, no document — so
    this file is the sole place a resumed process learns which project it is, which spine it
    was given, what it was doing, and what is still owed.

    `pending` describes a launch this state has already recorded and is now waiting on — set
    before the launch it describes, and cleared by `advance()` the moment the matching event is
    read, before any further decision runs."""

    instance_root: str
    product_path: str
    project: str
    core_dir: str
    shim_path: str
    # The documents this chain walks on its own initiative, in order. Given by the launcher
    # that started it and carried here because the hook re-enters as a fresh process, so a
    # value passed only at start would not survive to the moves that follow the first.
    spine: list[str] = field(default_factory=list)
    # The chain's own name, given by the launcher that started it — never composed from an
    # argument or the environment, task 4's own rule extended to a second literal a launcher
    # owns. Defaulted, `STATE_SCHEMA` untouched: a state file written before this field existed
    # loads with `chain_name == ""` (task 3), and `ChainEnding.of` reads no name for it rather
    # than fail.
    chain_name: str = ""
    # This walk's own id, minted once by `start()` from the `IdSource` it is given and never
    # re-minted by `advance()`, which only ever reads it back off the persisted state — the same
    # rule `started_at` already holds for the wall clock. Defaulted, `STATE_SCHEMA` untouched: a
    # state file written before this field existed loads with `walk_id == ""`, and a launch this
    # engine makes for it simply omits `INSTRUMENT_RUN_WALK_ID` rather than inventing one.
    walk_id: str = ""
    # Injected, never read from the environment here: whoever starts the chain resolves
    # KENSAIAPP_NOTIFIER and passes it.
    notifier: str = ""
    # Passed down to every launcher this chain runs, never acted on here: keeping the Mac
    # awake is `core/tools/detach_watcher.sh`'s, which each launcher already sources.
    keep_awake: bool = False
    # The engine that started this walk, baked into the shim so an edit to the file at that
    # path cannot change what a chain in flight executes.
    engine_path: str = ""
    current_document: str | None = None
    pending: dict | None = None
    # The self-answer reports already on disk, taken at `_launch` (the same call that sets
    # `pending`, above) and consumed by `_read_the_round`'s `self.reports.find` — the
    # chain's own copy of the reading `watch_agent.py`'s `reports_before` already takes for
    # the exact same reason (task 4): a report that predates THIS launch cannot be this
    # round's, so the locator must exclude it rather than hand back a predecessor's
    # verdict. Persisted rather than kept in memory because the completion hook re-enters
    # as a fresh process — nothing this field's value depended on would survive otherwise.
    # Defaulted, `STATE_SCHEMA` untouched: a state file written before this field existed
    # loads with `reports_before == []`, on the same rule `chain_name` already holds.
    reports_before: list = field(default_factory=list)
    queue: list[dict] = field(default_factory=list)
    rounds: dict = field(default_factory=dict)
    history: dict = field(default_factory=dict)
    ended: str | None = None
    ended_reason: str = ""
    # Ends the drain passed over. `should_halt` lets an unsettled cycle continue while the
    # queue still holds something that could change the outcome, and until they were recorded
    # here the end it passed over was simply dropped — so the halt that eventually landed named
    # one failure out of however many the walk actually hit. Each entry is
    # `[end, document-or-null, reason]` — a list, not a tuple, because the state file is JSON.
    deferred_ends: list = field(default_factory=list)
    # A re-entry-after-settling counter, incremented on every call that arrives after `ended`
    # is set. Reported, never a halt and never a cap.
    reentries: int = 0
    # The index into `spine` of the next document to consider once the queue is empty.
    spine_index: int = 0
    # Every companion path a report told this chain it opened, whether or not the document it
    # belongs to is on the spine. The end-of-walk sweep used to walk the spine alone, so a
    # companion this chain itself caused off it was never named — live: one product's owed run
    # opened `system/doctrine/writing_bar_open_issues.md` and the conclusion did not mention it.
    known_companions: list = field(default_factory=list)
    # When this walk began, ISO-8601 UTC, stamped once by `start()` and never moved after.
    # Until it existed a walk could not be delimited from disk at all: this file carries the
    # position but not the moment, and it is overwritten in place, so a reader asking which runs
    # belonged to which walk had only a human's `--since` to go on. The value is HANDED to
    # `start()` rather than read here — `main()` is the composition root and the only place the
    # wall clock is touched, so nothing below it reaches for the time
    # (`arch_defaults.md` § Composition Root, the rule this module's own header states).
    # Defaulted, `STATE_SCHEMA` untouched: a state file written before this field existed loads
    # with `started_at == ""`, on the same rule `chain_name` and `reports_before` already hold.
    started_at: str = ""
    # The command run once when this chain ends, with the end appended (`Chain._run_end_hook`).
    # Carried here because the run that ends a chain is a fresh process handed only a state path.
    # Defaulted, `STATE_SCHEMA` untouched: a state file written before this field existed loads
    # with `on_end == ""`, on the same rule `started_at` and `walk_id` already hold.
    on_end: str = ""
    # The provider `--provider` forced every run of this walk onto, or empty when each document
    # runs on its own. Defaulted, `STATE_SCHEMA` untouched: an older state file loads unforced.
    forced_provider: str = ""
    # How many launches this walk has made. Each launch's id is `<walk_id>-<n>`, written into
    # its own shim and onto `pending`, so a finish names the launch it belongs to and `advance`
    # can refuse one that is not the launch it waits on (`Chain.advance`). Defaulted,
    # `STATE_SCHEMA` untouched: a state file written before this field existed loads with
    # `launches == 0` and a `pending` carrying no launch, which `advance` still accepts.
    launches: int = 0
    # The validated `product-card` launches this drain has made, each as its normalized argv —
    # a list of lists, because the state file is JSON. A card is launched once per drain, and
    # popping it off the queue forgets it, so this is what keeps the answer round its own
    # completion opens from owing it again (`Chain._queue_owed`). Written with the pending state
    # that describes the launch, before the process is called, and cleared when the empty queue
    # hands over to the spine or the conclusion (`Chain._advance`). Defaulted, `STATE_SCHEMA`
    # untouched: a state file written before this field existed loads with it empty.
    card_launches_in_drain: list = field(default_factory=list)
    schema_version: int = STATE_SCHEMA

    def to_json(self) -> dict:
        return {field_name: getattr(self, field_name) for field_name in _STATE_FIELDS}

    @classmethod
    def from_json(cls, data: dict) -> "ChainState":
        """Unknown keys ignored, missing keys defaulted — never `cls(**data)`, which turns any
        shape difference into a crash out of the completion hook."""
        return cls(**{name: data[name] for name in _STATE_FIELDS if name in data})


_STATE_FIELDS = tuple(ChainState.__dataclass_fields__)


class StateStore:
    """The state file, behind a seam. Writes are atomic — a `.tmp` sibling written in full,
    then replaced over the real path — so a reader never observes a half-written file, and the
    write always happens BEFORE the launch it describes: a crash between them still leaves a
    file the next call can act on."""

    def __init__(self, files: Files, path: str):
        self.files = files
        self.path = os.path.abspath(path)

    def load(self) -> ChainState:
        text = self.files.read_text(self.path)
        if text is None:
            raise StateIncompatible(f"no chain state at {self.path}. Start the chain again "
                                    f"through its launcher.")
        data = json.loads(text)
        if data.get("schema_version") != STATE_SCHEMA:
            raise StateIncompatible(
                f"{self.path} was written against state schema "
                f"{data.get('schema_version')!r}, and this engine speaks {STATE_SCHEMA} — the "
                f"walk it describes cannot be resumed. Start the chain again through its "
                f"launcher.")
        return ChainState.from_json(data)

    def raw(self) -> dict:
        """The file as it is, schema unchecked — for a caller that must read a state `load`
        would refuse: the notifier command, so a refusal still reaches the owner, and
        `walk_is_live`'s callers, which judge the schema themselves."""
        text = self.files.read_text(self.path)
        if text is None:
            return {}
        try:
            return json.loads(text)
        except ValueError:
            return {}

    def save(self, state: ChainState) -> None:
        self.files.make_dirs(os.path.dirname(self.path))
        temporary = f"{self.path}.tmp"
        self.files.write_text(temporary,
                              json.dumps(state.to_json(), indent=2, sort_keys=True) + "\n")
        self.files.replace(temporary, self.path)


@dataclass(frozen=True)
class AdvanceResult:
    """What one call did. `acted` is `False` for both no-op shapes: nothing was pending (a
    stale or duplicate event), and the chain had already ended."""

    acted: bool
    ended: str | None


# --- The engine ----------------------------------------------------------------------------


class Chain:
    """The walk itself. Everything it uses is handed to it; it constructs nothing.

    `store` is the state file, `files` the disk, `processes` the launcher, `reports` the
    self-answer reader, `notifier` the owner's channel, `id_source` what mints a walk's own id,
    `environ` the environment a launch inherits, `providers` the port that hands an unforced
    launch the provider file of the instance it is for, `checkout` the port that reads the
    product checkout, and `engine_path` what this chain's shim will run — pinned at start, so an
    edit to the engine cannot change what a walk already in flight runs."""

    def __init__(self, *, store: StateStore, files: Files, processes: Processes,
                 reports: Reports, notifier: Notifier, id_source: IdSource, environ: dict,
                 providers: ProviderFiles, engine_path: str, process_table: walk_stop.ProcessTable,
                 checkout: product_checkout.Checkout, cycle_cap: int = DEFAULT_CYCLE_CAP):
        self.store = store
        self.process_table = process_table
        self.files = files
        self.processes = processes
        self.reports = reports
        self.notifier = notifier
        self.id_source = id_source
        self.environ = dict(environ)
        self.providers = providers
        self.engine_path = engine_path
        self.checkout = checkout
        self.cycle_cap = cycle_cap

    # -- the two entrypoints ---------------------------------------------------------------

    def start(self, *, instance_root: str, product_path: str, project: str, core_dir: str,
              shim_path: str, spine: tuple[DocumentSpec, ...], notifier_command: str = "",
              keep_awake: bool = False, chain_name: str = "",
              started_at: str = "", on_end: str = "",
              forced_provider: str = "") -> AdvanceResult:
        """Bootstrap a chain's state file and make its first move. `chain_name` is optional —
        never in `_START_REQUIRED_FLAGS`, so an unnamed hand-run or a future third chain still
        starts; task 6 is what makes the omission impossible for the two real launchers.

        The walk id is minted here, once, from `self.id_source` — never `uuid` called directly
        in this method body — and persisted before the first move, so every document this walk
        launches (`_launch`, below) can read it back off `state` rather than this call's own
        local.

        An unforced walk checks the provider file before it saves anything: every document of
        the registry and the owed item, not only the spine, because a report can owe a round of
        any document. A `ProvidersRefused` naming each entry the file cannot answer for leaves
        no state behind. A forced walk never reads the file."""
        if not spine:
            raise ValueError("a chain cannot start without a spine")
        self._refuse_to_overwrite_a_live_walk()
        if not forced_provider:
            self.providers.at(instance_root).resolve(_PROVIDER_MEMBERS)
        state = ChainState(
            instance_root=instance_root, product_path=product_path, project=project,
            core_dir=core_dir, shim_path=shim_path, spine=[spec.name for spec in spine],
            notifier=notifier_command, keep_awake=keep_awake, engine_path=self.engine_path,
            chain_name=chain_name, started_at=started_at, on_end=on_end,
            forced_provider=forced_provider,
            walk_id=self.id_source.new_id())
        self.store.save(state)
        # Announced before the first move, not after it: the first move can launch a run that
        # lives for hours, and a start message that waited for it would arrive at the wrong end
        # of the thing it announces.
        self.notifier.send(describe_start(state))
        self._advance(state)
        self.store.save(state)
        return AdvanceResult(acted=True, ended=state.ended)

    def _refuse_to_overwrite_a_live_walk(self) -> None:
        """One chain per project at a time — the state file IS that project's chain."""
        existing = self.store.raw()
        if not walk_is_live(existing):
            return
        pending = existing["pending"]
        walking = pending.get("document") or "a document"
        spine = ", ".join(existing.get("spine") or []) or "an unrecorded spine"
        state = walk_stop.launch_state(self.files, self.process_table, pending.get("identity", ""))
        command = walk_stop.stop_command(
            existing.get("core_dir", ""), f"chain-{existing.get('chain_name') or 'product'}",
            existing.get("project", ""))
        raise ChainAlreadyWalking(
            f"{self.store.path} is still walking — spine {spine}, waiting on {walking}. "
            f"{walk_stop.refusal_remedy([state], command)}")

    def stop(self, stopped_at: str) -> str:
        """End the walk now: stop the launch it waits on and that run's watcher, write `stopped`,
        keep the state file, tell the owner once and run the on-end command with `stopped`.
        Returns the message sent. A walk that already ended, or none, is left as it is and the
        message says so. Takes no lock, as `advance` takes none."""
        if not self.store.raw():
            return self._tell(f"chain: no walk to stop at {self.store.path}")
        state = self.store.load()
        if state.ended is not None:
            return self._tell(f"{self._hook_headline(state)} — nothing to stop: "
                              f"the walk already ended {state.ended}")
        pending, state.pending = state.pending, None
        stops = ([] if pending is None else [walk_stop.stop_launch(
            self.files, self.process_table, pending.get("identity", ""),
            pending.get("document") or "the launch")])
        state.ended = walk_stop.STOPPED
        state.ended_reason = walk_stop.stop_reason(stopped_at, stops)
        self.store.save(state)
        message = f"{self._hook_headline(state)} — {state.ended_reason}"
        self.notifier.send(message)
        self._run_end_hook(state, walk_stop.STOPPED)
        return message

    def _tell(self, message: str) -> str:
        self.notifier.send(message)
        return message

    def advance(self, outcome: str, launch: str | None = None) -> AdvanceResult:
        """The idempotent entrypoint the completion shim calls, given the hook's one argument
        and the launch the shim was written for. Does nothing — never raises — in each no-op
        shape: the chain has already ended (a re-entry, counted but never a halt), nothing is
        pending (a duplicate delivery of an event this state has consumed, or one arriving
        after the chain moved past it), or the finish names a launch other than the one
        pending — a stale run's, an earlier launch's delivered again, or an abandoned walk's
        still running beside this one (2026-09-23: an abandoned walk's SDD run, stopped, was
        taken for the finish of the next walk's). A `pending` written before launches were
        named carries none, and accepts any finish as it did then.

        Otherwise the pending marker is cleared and persisted BEFORE anything else runs, so a
        second delivery of the same outcome finds nothing pending and is itself a no-op: fed
        the same event twice, it advances once."""
        state = self.store.load()
        if state.ended is not None:
            state.reentries += 1
            self.store.save(state)
            return AdvanceResult(acted=False, ended=state.ended)
        if state.pending is None:
            return AdvanceResult(acted=False, ended=None)
        awaited = state.pending.get("launch")
        if awaited is not None and launch != awaited:
            return AdvanceResult(acted=False, ended=None)

        self._finish(state, outcome)
        self.store.save(state)
        return AdvanceResult(acted=True, ended=state.ended)

    def _finish(self, state: ChainState, outcome: str) -> None:
        """The pending launch's end, on `state` as it stands: `advance`'s for a detached run, and
        `_launch`'s own for a foreground one, which has no shim call to wait for."""
        pending = state.pending
        state.pending = None
        self.store.save(state)
        if not self._left_the_checkout_dirty(state, pending):
            self._step(state, outcome, pending)

    def _left_the_checkout_dirty(self, state: ChainState, pending: dict) -> bool:
        """Before anything else of the run's end is read, whatever its outcome: compare the
        product checkout with the reading `_launch` took, and halt `machinery` naming the
        document when the run left new entries in it. Halts through `_halt`, never `_reach_end`,
        which would drain the owed queue — launches on top of the dirt the run left. A pending
        with nothing recorded (an unreadable checkout at launch, or a state written before this
        check existed) is not checked, and the checkout is not read for it."""
        before = pending.get(product_checkout.CHECKOUT_BEFORE)
        if before is None:
            return False
        reason = product_checkout.left_dirty(
            before, self.checkout.entries(state.product_path), state.product_path)
        if reason is None:
            return False
        name = pending.get("document")
        self._halt(state, CycleEnd.MACHINERY, document(name) if name else None, reason)
        return True

    # -- the decision ----------------------------------------------------------------------

    def _step(self, state: ChainState, outcome: str, pending: dict | None) -> None:
        name = pending.get("document") if pending else None
        spec = document(name) if name else None

        if outcome != "completed":
            # `"produced_nothing"` — `watch_agent.HookOutcome.PRODUCED_NOTHING.value` — is a
            # bare literal here on the same convention `"completed"` above already holds for
            # `HookOutcome.COMPLETED.value`: the shim's one string argument is the only place
            # the two files meet, so neither imports the other. Same seat as any other
            # non-completed outcome (MACHINERY, no eighth end) — only the reason differs, so
            # the owner reads WHY rather than `_step`'s generic "ended <x>, not completed":
            # a run this watcher itself read as having produced nothing is not evidence a
            # document is settled, which is what `_read_the_round` below would otherwise
            # conclude off an absent report.
            if outcome == "produced_nothing":
                reason = ("the launched run produced nothing — not evidence this document is "
                          "settled")
            elif outcome == "stopped":
                # `watch_agent.HookOutcome.STOPPED` — a multi-turn run that reached `stopped`
                # without its done marker: something ended it mid-walk.
                reason = ("the launched run was stopped before it said it was finished — "
                          "not evidence this document is settled")
            else:
                reason = f"the launched run ended {outcome}, not completed"
            self._reach_end(state, CycleEnd.MACHINERY, spec, reason=reason)
            return

        if pending and pending.get("kind") == "answer" and spec is not None:
            self._read_the_round(state, spec)
            return

        if (pending and pending.get("kind") == "producer" and spec is not None
                and self.locate(state, spec).companion_present):
            # The producer ran and its companion is STILL on disk, so the cycle did not close:
            # a producer clears the companion when a fold leaves nothing unresolved, and one
            # that stands is an item waiting on someone. Until 2026-09-01 a producer's
            # completion went straight to `_advance` — the chain read a report only for an
            # `answer` step and never re-read the disk for the document it had just run — so
            # the walk moved on with the companion open and said nothing. Measured on
            # a live product, whose `product-uxd` run came back "the run had nothing to fold — the
            # UXD companion is still waiting on you" while the chain advanced to the FDR.
            #
            # It goes back through the ANSWER step specifically, never through `_run_document`,
            # which could route to the producer again and loop. The round cap and the
            # stagnation check bound it from there, because that is the step they measure.
            self._launch_answer(state, spec)
            return

        if (pending and pending.get("kind") == "producer" and spec is not None
                and self.locate(state, spec).placeholder):
            # The producer completed and left its stamped placeholder standing, with no
            # companion. Advancing would let the walk conclude "every spine document is settled"
            # over a document that was never written. Narrowed to the placeholder on purpose: a
            # producer completing with no file at all still advances, as the suite pins.
            self._reach_end(state, CycleEnd.MACHINERY, spec,
                            reason="the producer completed but its document is still absent — the stamped placeholder stands")
            return

        self._advance(state)

    def _read_the_round(self, state: ChainState, spec: DocumentSpec) -> None:
        home = (state.instance_root if spec.home is Home.INSTANCE_PROJECT
                else state.product_path)
        report_paths = self.reports.find_round(home, spec.trail_stem, state.reports_before)
        report = combine_round([(path, self.reports.read(path)) for path in report_paths])
        end = classify_report(report)
        reason = (self._describe_round(state, spec, report) if report is not None
                  else f"no self-answer report found under {home}/**/trail/{spec.trail_stem}/")

        # A cycle that only LEFT AN ITEM is a successful round, so it is accounted for like any
        # other — `classify_report` returning that end must not skip the bookkeeping below.
        # This file already made the argument, at the `raised` comment in `classify_report`:
        # "an end reached here skips the branch below that queues the report's owed set, so
        # halting on a raise halts BEFORE the producer that would fold it ever runs — and a
        # producer often folds it." Every word of that is true of a left item, and it was the
        # one verdict never held to it. Measured on a live product, 2026-09-03: three
        # self-answer runs decided five items, each report asked for `product-sdd` under
        # `## Launchers owed`,
        # and the state carried `queue: []`, `rounds: {}` and `history: {}` while `SDD.md` went
        # untouched for five hours.
        accounted = end is None or end is CycleEnd.LEFT_FOR_THE_OWNER
        unrouted = unrouted_companions(report) if accounted else []
        if unrouted:
            # The owed set's two derivations disagree: this run opened a companion on a
            # document no `## Launchers owed` bullet carries a command for. Refused rather than
            # dropped, and refused before the round is counted — a report the chain cannot
            # route whole is not a round it can measure progress across.
            #
            # Checked for a left-for-the-owner round too, deliberately: a report the chain
            # cannot route whole is unroutable whatever else that round decided, and the
            # refusal is about the report's shape rather than about its verdicts.
            end = CycleEnd.NO_RUNNABLE_COMMAND
            reason = (f"{', '.join(unrouted)} — opened under `## Companions opened` with no "
                      f"`## Launchers owed` bullet to run it")
        elif accounted:
            round_number = state.rounds.get(spec.name, 0) + 1
            # A failure found here WINS over the softer end that got us in — a cap reached on a
            # round that also left an item is a cap. `None` never overwrites a real end.
            next_end = next_round_end(state.history.get(spec.name), report, round_number,
                                      self.cycle_cap)
            end = next_end if next_end is not None else end
            state.rounds[spec.name] = round_number
            state.history[spec.name] = _comparable(round_signature(report))
            state.known_companions = state.known_companions + [
                path for path in _companion_paths(report)
                if path not in state.known_companions]
            # Queued unless the round ended in a real failure. The owed set is a routing list,
            # and the producer it names is exactly what folds the answers just written.
            if end not in _HALTING_ENDS:
                state.queue = self._queue_owed(state, report.owed)

        if end is not None:
            self._reach_end(state, end, spec, reason=reason)
            return
        self._advance(state)

    def _queue_owed(self, state: ChainState, owed: list[OwedItem]) -> list[dict]:
        """`state.queue` with `owed` added, a launcher already queued not queued again.

        One run of a producer folds every answer on disk when it runs, so a second copy of it in
        the queue can only run after the first has folded everything and find nothing — which
        the watcher hands back as `produced_nothing`, and `_step` ends the walk on. Measured on a
        live product, 2026-09-25: an ADR round, the FDR round after it and a second ADR round each
        owed `product-architecture`, and the third run halted a walk that had settled.

        Two items are the same launcher when their commands resolve to the same argv through
        `validate_owed_command` — the reports spell one launcher with `<CORE>` and with a pin's
        absolute path. A command that does not resolve is kept by its own text, so it is still
        refused by name when its turn comes.

        A card is also not queued again once it has launched in this drain
        (`ChainState.card_launches_in_drain`): the queue forgets an item the moment it is popped,
        and the answer round the card's completion opens can owe it again. Only a validated card
        gains that memory; every other launcher is queued again once it has been popped."""
        queue = list(state.queue)
        seen = {self._owed_identity(state, item["command"]) for item in queue}
        for item in owed:
            validated = self._validated(state, item.command)
            identity = _owed_identity_of(validated, item.command)
            if identity in seen:
                continue
            if _is_card(validated) and list(validated.argv) in state.card_launches_in_drain:
                continue
            seen.add(identity)
            queue.append({"document_path": item.document_path, "command": item.command})
        return queue

    def _validated(self, state: ChainState, command: str | None) -> ValidatedCommand | None:
        """`command` through the owed-command check, or `None` where the check refuses it —
        refused here only to classify it; it is refused by name when its turn comes."""
        try:
            return validate_owed_command(command, core_dir=state.core_dir,
                                         instance_root=state.instance_root, files=self.files)
        except CommandRefused:
            return None

    def _owed_identity(self, state: ChainState, command: str | None) -> tuple[str, ...]:
        return _owed_identity_of(self._validated(state, command), command)

    def _next_owed(self, state: ChainState, queue: list[OwedItem]
                    ) -> tuple[OwedItem | None, list[OwedItem]]:
        """The item to launch now and what remains. Every item that is not a validated card goes
        first, by `next_owed_item`'s dependency order; a card item goes only when none is left,
        the first of them in the order they arrived. Read at every dispatch, because a later
        round can add ordinary items to a queue that already holds a card."""
        ordinary, cards = [], []
        for item in queue:
            (cards if _is_card(self._validated(state, item.command)) else ordinary).append(item)
        head, rest = next_owed_item(ordinary)
        if head is not None:
            return head, rest + cards
        if cards:
            return cards[0], cards[1:]
        return None, []

    def _describe_round(self, state: ChainState, spec: DocumentSpec,
                        report: SelfAnswerReport) -> str:
        """What the round actually said, for the message the owner reads.

        Until 2026-09-01 an end reached off a report carried `""`, so a halt notified the owner
        with the bare guidance line and named neither the companion nor how much was left —
        while the watcher's own message for the same run named the count, the verdict and the
        owed bullet. Measured on a live product, which halted at the ADR with an empty
        `ended_reason`."""
        parts = []
        left = report.counts.get("left for the owner", 0)
        if left:
            parts.append(f"{left} item(s) left for the owner")
        if report.raised:
            parts.append(f"{report.raised} item(s) raised on the document itself")
        if report.missing_headings:
            parts.append("the report is missing " + ", ".join(report.missing_headings))
        companion = self.locate(state, spec).companion_path
        if companion:
            parts.append(f"answer them on {companion}")
        return "; ".join(parts)

    def _advance(self, state: ChainState) -> None:
        """Drain the owed set before the spine moves on, or conclude when both are done. The
        owed set drains ordinary items first and its cards last (`_next_owed`). An empty queue
        is where a drain ends: the cards it launched are forgotten here, as the walk takes its
        next spine document or concludes, and nowhere earlier."""
        queue = [OwedItem(**item) for item in state.queue]
        item, rest = self._next_owed(state, queue)
        if item is not None:
            state.queue = [{"document_path": i.document_path, "command": i.command}
                           for i in rest]
            self._run_owed_item(state, item)
            return

        state.card_launches_in_drain = []
        if state.spine_index >= len(state.spine):
            self._conclude(state)
            return

        spec = document(state.spine[state.spine_index])
        state.spine_index += 1
        self._run_document(state, spec)

    def _conclude(self, state: ChainState) -> None:
        still_open = self._live_companions(state)
        if still_open:
            # The walk is out of moves and the product is not done — the owner is holding it,
            # so say that rather than "nothing left to do".
            # `_halt` directly, not `_reach_end`: this branch is terminal by construction —
            # the spine is walked out, so there is no next document to advance to — exactly like
            # the SETTLED call below it. Routing through `_reach_end` would ask `should_halt`,
            # which no longer stops on this end, and the walk would advance past the end of the
            # spine. The end value says who is owed something; this site says the walk is over.
            self._halt(state, CycleEnd.LEFT_FOR_THE_OWNER, None,
                       "the spine is walked and these companions are still open: "
                       + ", ".join(still_open))
            return
        self._halt(state, CycleEnd.SETTLED, None, "every spine document is settled")

    def _run_document(self, state: ChainState, spec: DocumentSpec) -> None:
        """Document absent -> the producer; companion present -> the answer step; neither ->
        nothing to launch, so the walk moves straight past it."""
        entry = cycle_entry(self.locate(state, spec))
        if entry is CycleEntry.PRODUCER:
            command = self._producer_command(state, spec)
        elif entry is CycleEntry.ANSWER:
            command = (f"{state.core_dir}/launchers/companion-self-answer/launcher.sh "
                       f"{state.project} {spec.self_answer_arg}")
        else:
            self._advance(state)
            return
        try:
            validated = validate_owed_command(command, core_dir=state.core_dir,
                                              instance_root=state.instance_root,
                                              files=self.files)
        except CommandRefused as exc:
            self._reach_end(state, CycleEnd.NO_RUNNABLE_COMMAND, spec, reason=str(exc))
            return
        self._launch(state, spec, entry, validated)

    def _launch_answer(self, state: ChainState, spec: DocumentSpec) -> None:
        """Send `spec` through its answer step — the one entry this takes, with no path back to
        the producer."""
        command = (f"{state.core_dir}/launchers/companion-self-answer/launcher.sh "
                   f"{state.project} {spec.self_answer_arg}")
        try:
            validated = validate_owed_command(command, core_dir=state.core_dir,
                                              instance_root=state.instance_root, files=self.files)
        except CommandRefused as exc:
            self._reach_end(state, CycleEnd.NO_RUNNABLE_COMMAND, spec, reason=str(exc))
            return
        self._launch(state, spec, CycleEntry.ANSWER, validated)

    def _producer_command(self, state: ChainState, spec: DocumentSpec) -> str:
        """The command that produces `spec` — the module header's § How a document is launched."""
        return f"{state.core_dir}/launchers/skill/launcher.sh {spec.skill} {state.project}"

    def _run_owed_item(self, state: ChainState, item: OwedItem) -> None:
        """Run one item off the owed set — validated exactly as any other command, and refused
        the same way when it does not resolve to a real, correctly-called launcher."""
        spec = resolve_document(item.document_path)
        try:
            validated = validate_owed_command(item.command, core_dir=state.core_dir,
                                              instance_root=state.instance_root,
                                              files=self.files)
        except CommandRefused as exc:
            self._reach_end(state, CycleEnd.NO_RUNNABLE_COMMAND, spec, reason=str(exc))
            return
        entry = (CycleEntry.ANSWER if validated.launcher_folder == "companion-self-answer"
                 else CycleEntry.PRODUCER)
        self._launch(state, spec, entry, validated)

    def _launch(self, state: ChainState, spec: DocumentSpec | None, entry: CycleEntry,
                validated: ValidatedCommand) -> None:
        """Record the launch on `state` and persist it BEFORE launching, then launch. A
        launcher that exits non-zero is a machinery stop, never a silent retry.

        The provider is read first, before anything is recorded: a file that cannot answer for
        this launch's member stops the walk here, as a machinery halt naming the entry. It
        halts directly rather than through `_reach_end`, because draining the queue would make
        the very launches a refusal says the walk must not make."""
        member = providers.document(spec.name) if spec is not None else providers.OWED_ITEM
        try:
            provider = self.providers.at(state.instance_root).launch_provider(
                state.forced_provider, member)
        except ProvidersRefused as refused:
            self._halt(state, CycleEnd.MACHINERY, spec, str(refused))
            return
        if spec is not None:
            state.current_document = spec.name
        state.launches += 1
        if _is_card(validated) and list(validated.argv) not in state.card_launches_in_drain:
            # Remembered with the pending state below, before the process is called: a card
            # launched is a card launched this drain, whatever the run's own end does next.
            state.card_launches_in_drain = state.card_launches_in_drain + [list(validated.argv)]
        launch = f"{state.walk_id or 'walk'}-{state.launches}"
        shim = self._shim_for(state, launch)
        state.pending = {"kind": entry.value, "document": spec.name if spec else None,
                         "launch": launch, "identity": walk_stop.identity_path(shim)}
        # The product checkout as this launch found it, on disk with the launch it describes for
        # the fresh process the run's end starts. An unreadable checkout records nothing, and
        # `advance` does not check a pending that holds nothing.
        checkout_before = self.checkout.entries(state.product_path)
        if checkout_before is not None:
            state.pending[product_checkout.CHECKOUT_BEFORE] = checkout_before
        # The chain's own before-reading (task 4) — taken here, alongside `pending`, so it
        # is on disk before the launch it describes rather than re-derived by whichever
        # process the completion hook re-enters as. `spec is None` (an owed item with no
        # resolvable document) leaves it `[]`: there is no trail to read a home/stem for.
        state.reports_before = (
            list(self.reports.present(
                state.instance_root if spec.home is Home.INSTANCE_PROJECT
                else state.product_path,
                spec.trail_stem))
            if spec is not None else []
        )
        self.store.save(state)
        self._write_shim(state, shim, launch)

        argv = list(validated.argv)
        if state.keep_awake:
            # Appended AFTER validation on purpose: validation proves what the report asked
            # for, and this is the caller's own instruction rather than something read off a
            # document.
            argv.append("--keep-awake")
        # Never inherited: the engine's own environment is the previous run's. Set to the
        # provider decided above.
        env = with_provider(self.environ, provider)
        env["DETACH_WATCHER_ON_COMPLETE"] = shim
        env, _ = walk_stop.prepare_launch(self.files, shim, env)
        # Task 3 — ties every document this walk launches to the same walk, and names the
        # chain, in the terms `run_telemetry` reads. Either key is simply absent when its state
        # value is empty (a pre-task-3 state resumed under this engine, or an unnamed walk),
        # never an empty string a receiver would have to know means "nothing".
        # An empty value also removes whatever the engine's own environment carried, so a walk
        # started from a shell that still holds another walk's keys never passes those on.
        for key, value in (("INSTRUMENT_RUN_WALK_ID", state.walk_id),
                           ("INSTRUMENT_RUN_CHAIN", state.chain_name)):
            if value:
                env[key] = value
            else:
                env.pop(key, None)
        exit_code = self.processes.run(argv, cwd=state.instance_root, env=env)
        if exit_code != 0:
            state.pending = None
            self._reach_end(state, CycleEnd.MACHINERY, spec,
                            reason=f"launcher exited {exit_code}")
            return
        if _is_card(validated):
            # The card launcher ran in the foreground and left no watcher, so its exit is the
            # run's end and nothing will ever call the shim (module header, § How a document is
            # launched). Finished on this `state`, never through `advance`, which would load a
            # copy the caller then overwrites with this one.
            self._finish(state, "completed")

    def _reach_end(self, state: ChainState, end: CycleEnd, spec: DocumentSpec | None, *,
                   reason: str = "") -> None:
        """Halt-fast: stop the whole chain unless the queue already holds something that could
        still change the outcome, in which case draining it continues instead."""
        remaining = [OwedItem(**item) for item in state.queue]
        if should_halt(end, remaining):
            self._halt(state, end, spec, reason)
            return
        if end in _UNSETTLED_ENDS:
            # Recorded, not dropped: the queue is why this one does not halt, and nothing else
            # will ever mention it.
            state.deferred_ends = state.deferred_ends + [
                [end.value, spec.name if spec else None, reason]]
        self.store.save(state)
        self._advance(state)

    def _halt(self, state: ChainState, end: CycleEnd, spec: DocumentSpec | None,
              reason: str) -> None:
        """The one place a chain writes `ended` and notifies the owner — `_reach_end`'s halting
        half and `_conclude`'s SETTLED write, unified so a fix to one applies to both. Until
        this task, `_conclude` sent `_deferred_summary(state)` ALONE as its message's reason —
        empty with nothing deferred — while this path sent the full composed one; "one engine,
        two exits, one of them mute."

        `reason` is the RAW reason — what actually happened, with no deferred-ends prefix folded
        in. It goes to `ChainEnding.of`, and from there to the message's `why:` line, untouched.
        `state.ended_reason` gets the COMPOSED reason (`_halt_reason`, raw + deferred) exactly as
        it did before this extraction, so a reader of the state file sees what they always saw —
        only the notifier message's shape changed, never what is written to disk."""
        document_name = spec.name if spec else None
        state.ended = end.value
        state.ended_reason = self._halt_reason(state, reason)
        self.store.save(state)
        ending = ChainEnding.of(state, end, document_name, reason)
        self.notifier.send(describe_end(ending))
        self._run_end_hook(state, end.value)

    def _run_end_hook(self, state: ChainState, end: str) -> None:
        """Run the command this chain was started with, once, with the end appended — after the
        ended state is saved and the owner told (`run_end_hook` owns what a failure costs)."""
        run_end_hook(state.on_end, end, cwd=state.instance_root, processes=self.processes,
                     notifier=self.notifier, headline=self._hook_headline(state),
                     env=with_provider(self.environ, state.forced_provider))

    @staticmethod
    def _hook_headline(state: ChainState) -> str:
        """Who is speaking. Never `describe_refusal`: its banner says UNRESOLVED, and this chain
        has ended — it is a hook after the end that failed, not a walk left stranded."""
        return f"chain {state.chain_name or '(unnamed)'} · {state.project}"

    # -- reading the disk -------------------------------------------------------------------

    def _is_placeholder(self, spec: DocumentSpec, path: str) -> bool:
        if spec.placeholder_marker is None:
            return False
        return spec.placeholder_marker in (self.files.read_text(path) or "")

    def locate(self, state: ChainState, spec: DocumentSpec) -> DocumentLocation:
        """Where `spec` and its companion live for this project, and whether each is on disk —
        read fresh every call: the decision is made from the files themselves and never from
        this engine's memory of what it launched."""
        if spec.home is Home.INSTANCE_PROJECT:
            # A management artifact, not a product document: it and its companion live in the
            # instance repo beside the project card, never under the resolved product path.
            directory = os.path.join(state.instance_root, "system", "projects", state.project)
            document_path = os.path.join(directory, f"{spec.stem}.md")
            companion_path = os.path.join(directory, f"{spec.companion_stem}.md")
            placeholder = (self.files.is_file(document_path)
                           and self._is_placeholder(spec, document_path))
            has_document = self.files.is_file(document_path) and not placeholder
            has_companion = self.files.is_file(companion_path)
            return DocumentLocation(
                document_path=document_path if has_document else None,
                companion_path=companion_path if has_companion else None,
                document_present=has_document, companion_present=has_companion,
                placeholder=placeholder)

        docs_dir = os.path.join(state.product_path, "docs")

        if spec.shape is Shape.RECORD_DIRECTORY:
            # No single file is ever written — this is a directory of numbered records.
            # "Present" means it holds at least one record beyond its own README.
            record_dir = os.path.join(docs_dir, spec.stem)
            records = [entry for entry in self.files.list_dir(record_dir)
                       if entry.lower().endswith(".md") and entry.lower() != "readme.md"]
            companion_path = self._docs_entry(docs_dir, spec.companion_stem)
            return DocumentLocation(
                document_path=record_dir if records else None,
                companion_path=companion_path,
                document_present=bool(records),
                companion_present=companion_path is not None)

        document_path = self._docs_entry(docs_dir, spec.stem)
        if spec.companion_stem:
            companion_path = self._docs_entry(docs_dir, spec.companion_stem)
        else:
            # The companion's case is read off disk too, off the DOCUMENT's own on-disk stem —
            # never composed from a constant, for the same reason the document's is: measured
            # on a live product, `docs/SRS.md`'s companion is `docs/srs_open_issues.md`.
            stem_on_disk = (os.path.splitext(os.path.basename(document_path))[0]
                            if document_path else spec.stem)
            companion_path = self._docs_entry(docs_dir, f"{stem_on_disk}_open_issues")
        return DocumentLocation(
            document_path=document_path,
            companion_path=companion_path,
            document_present=document_path is not None,
            companion_present=companion_path is not None)

    def _docs_entry(self, docs_dir: str, stem: str) -> str | None:
        """The `docs_dir` entry whose stem equals `stem` case-insensitively, at its own on-disk
        case — a stem in, the matching entry's real path out, never a name composed from
        another name's case."""
        wanted = stem.lower()
        for entry in self.files.list_dir(docs_dir):
            base = entry.rsplit(".", 1)[0] if "." in entry else entry
            if base.lower() == wanted:
                return os.path.join(docs_dir, entry)
        return None

    def _live_companions(self, state: ChainState) -> list[str]:
        """Every companion still on disk when the walk is otherwise done, read fresh — the
        check `SETTLED` is concluded against rather than assumed.

        A companion outlives its round only while it still holds something open: the answer
        step never removes one, and the producer clears it when a fold leaves nothing
        unresolved. So a companion standing at the end of the walk is an item waiting on the
        owner, never residue. Without this, `SETTLED` is positional — spine exhausted, queue
        empty — and says nothing about the product. Live: a product, 2026-09-01, which ended
        settled over three open companions, one of them holding an item its own architecture
        round had explicitly left for the owner.

        Scoped to what this chain actually walked — its spine plus any document a round was
        read for — because a companion on a document outside both was never this chain's to
        speak for. Deduplicated by path, since ADR and NFDR share one."""
        walked = list(state.spine) + [name for name in state.rounds if name not in state.spine]
        seen: set[str] = set()
        open_companions: list[str] = []
        for name in walked:
            path = self.locate(state, document(name)).companion_path
            if path and path not in seen:
                seen.add(path)
                open_companions.append(path)
        # And every companion a report told this chain about, on the spine or off it — the
        # chain caused those too, and only the report knows where a non-spine document's
        # companion lives.
        for path in state.known_companions:
            if path not in seen and self.files.is_file(path):
                seen.add(path)
                open_companions.append(path)
        return open_companions

    # -- messages ---------------------------------------------------------------------------

    def _halt_reason(self, state: ChainState, reason: str) -> str:
        """The ending reason as it is written to the state file and read out to the owner — the
        end's own reason, then every end the drain passed over. Both ends that conclude a chain
        compose it, `SETTLED` included: a chain that settled having quietly passed over a
        machinery stop is the one case where nothing else would ever say so."""
        summary = _deferred_summary(state)
        if not summary:
            return reason
        if not reason:
            return summary
        return f"{reason}. And {summary}"

    # -- the shim ---------------------------------------------------------------------------

    @staticmethod
    def _shim_for(state: ChainState, launch: str) -> str:
        """One shim per launch, named for the walk and the launch beside the `shim_path` the
        launcher gave. Never one file per project: an abandoned walk's watcher still holds its
        shim's path, and a new walk rewriting that file would hand it the new walk's launch."""
        stem, extension = os.path.splitext(state.shim_path)
        return f"{stem}-{launch}{extension or '.sh'}"

    @staticmethod
    def _log_path(state: ChainState) -> str:
        """The one log a project's walks share, beside the shims: `<shim_path stem>.log`. Every
        shim appends its advance's output here, and the watcher's pipe never carries it."""
        return f"{os.path.splitext(state.shim_path)[0]}.log"

    def _write_shim(self, state: ChainState, shim_path: str, launch: str) -> None:
        """Write the shim `DETACH_WATCHER_ON_COMPLETE` points at for one launch. The hook calls
        `--on-complete` as `<script> <outcome>` — one argument, carrying no run identity and no
        state path — so this shim is what closes that gap: the state path, the launch and the
        engine that wrote it are baked into its text — the engine because a chain in flight
        must not start executing a different engine because someone edited a file. The text is
        `completion_shim`'s: it starts the engine detached, and the engine's output goes to the
        walk's log at `_log_path`."""
        completion_shim.write_shim(self.files, shim_path, engine_path=self.engine_path,
                                   advance_args=("--launch", launch, "--advance",
                                                 self.store.path),
                                   log_path=self._log_path(state))


# --- The composition root: the only place a concrete implementation is constructed ----------


_START_REQUIRED_FLAGS: tuple[tuple[str, str], ...] = (
    ("--instance-root", "instance_root"),
    ("--product-path", "product_path"),
    ("--project", "project"),
    ("--core-dir", "core_dir"),
    ("--shim-path", "shim_path"),
    ("--spine", "spine"),
)


# Every launch an unforced product walk can make, by the provider file's entry for it: each
# document of the registry, and the launch for an owed item that resolves to no document.
_PROVIDER_MEMBERS = ([providers.document(name) for name in DOCUMENT_REGISTRY]
                     + [providers.OWED_ITEM])


def build_chain(state_path: str, *, notifier_command: str, engine_path: str) -> Chain:
    """Wire the real implementations to the ports. This function owns wiring, not flow — it is
    the only node in this module that knows a concrete implementation exists."""
    files = Files()
    processes = Processes()
    return Chain(
        store=StateStore(files, state_path),
        files=files,
        processes=processes,
        reports=Reports(files),
        notifier=Notifier(notifier_command, processes),
        id_source=IdSource(),
        environ=dict(os.environ),
        providers=ProviderFiles(files),
        engine_path=engine_path,
        process_table=walk_stop.ProcessTable(),
        checkout=product_checkout.Checkout(),
    )


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv()
        load_dotenv(Path.home() / ".env")
    except ImportError:
        pass

    """The two CLI surfaces this module needs. `--advance <state_path> <outcome> --launch <id>`
    is what each launch's shim generates and the completion hook fires with the hook's one
    argument. `--start
    <state_path>` is a chain launcher's entry point — the launcher is shell and `start()` is a
    Python method, so without this flag no launcher could exist without reaching into Python
    itself. The two are mutually exclusive and neither is assumed; a usage error is reported on
    stderr with a non-zero return, never a raised exception."""
    parser = argparse.ArgumentParser(description="walk a chain of document cycles")
    parser.add_argument("--advance", nargs=2, metavar=("STATE_PATH", "OUTCOME"))
    parser.add_argument("--launch", default=None,
                        help="with --advance: the launch the finishing run belongs to, as its "
                             "shim carries it")
    parser.add_argument("--start", metavar="STATE_PATH")
    parser.add_argument("--stop", metavar="STATE_PATH",
                        help="end the walk now: stop its run and watcher, write `stopped`, keep "
                             "the state file; --notifier names the channel when given, else the "
                             "state's")
    parser.add_argument("--instance-root")
    parser.add_argument("--product-path")
    parser.add_argument("--project")
    parser.add_argument("--core-dir")
    parser.add_argument("--shim-path")
    parser.add_argument("--spine", help="the documents this chain walks, in order, "
                                        "comma-separated (e.g. 'FDR,ADR,NFDR')")
    parser.add_argument("--notifier", default="")
    parser.add_argument("--keep-awake", action="store_true")
    parser.add_argument("--chain-name", default="",
                        help="the chain's own name — optional, never required to start")
    parser.add_argument("--provider", choices=PROVIDERS, default="",
                        help="force every run of the walk onto this provider, over the one "
                             ".providers.toml at the instance root names, which is then not "
                             "read; read only with --start")
    parser.add_argument("--on-end", default="", metavar="COMMAND",
                        help="a command run once when the chain ends, with the end appended as "
                             "its last argument — optional, read only with --start")
    args = parser.parse_args(argv)

    if sum(bool(entry) for entry in (args.advance, args.start, args.stop)) > 1:
        print("chain: --advance, --start and --stop are mutually exclusive", file=sys.stderr)
        return 2
    if not args.advance and not args.start and not args.stop:
        print("chain: one of --advance, --start or --stop is required", file=sys.stderr)
        return 2

    engine_path = os.path.abspath(__file__)

    if args.stop:
        notifier_command = args.notifier or StateStore(Files(), args.stop).raw().get("notifier", "")
        chain = build_chain(args.stop, notifier_command=notifier_command,
                            engine_path=engine_path)
        try:
            print(chain.stop(datetime.now(timezone.utc).isoformat()))
        except StateIncompatible as exc:
            print(f"chain: {exc}", file=sys.stderr)
            return 3
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            chain.notifier.send(describe_refusal(
                f"the walk at {args.stop} crashed stopping — {exc}"))
            return 5
        return 0

    if args.advance:
        state_path, outcome = args.advance
        probe = StateStore(Files(), state_path)
        notifier_command = probe.raw().get("notifier", "")
        chain = build_chain(state_path, notifier_command=notifier_command,
                            engine_path=engine_path)
        try:
            result = chain.advance(outcome, launch=args.launch)
        except StateIncompatible as exc:
            # Never a traceback out of the completion hook: that is what took a live chain down
            # on 2026-09-01, when an engine edit landed under a running walk.
            print(f"chain: {exc}", file=sys.stderr)
            chain.notifier.send(describe_refusal(
                f"the walk at {state_path} cannot be resumed — {exc}"))
            return 3
        except Exception as exc:
            # Defect 3: everything else used to be silent — a traceback inside the completion
            # hook and nothing sent. The traceback still goes to stderr, for whoever reads the
            # log; the owner's phone is what only this line reaches.
            traceback.print_exc(file=sys.stderr)
            chain.notifier.send(describe_refusal(
                f"the walk at {state_path} crashed advancing on {outcome!r} — {exc}"))
            return 5
        print(f"chain: acted={result.acted} ended={result.ended}")
        return 0

    missing = [flag for flag, attr in _START_REQUIRED_FLAGS if not getattr(args, attr)]
    if missing:
        print(f"chain: --start requires {', '.join(missing)}", file=sys.stderr)
        return 2
    try:
        spine = parse_spine(args.spine)
    except ValueError as exc:
        print(f"chain: {exc}", file=sys.stderr)
        return 2

    chain = build_chain(args.start, notifier_command=args.notifier, engine_path=engine_path)
    try:
        result = chain.start(instance_root=args.instance_root, product_path=args.product_path,
                             project=args.project, core_dir=args.core_dir,
                             shim_path=args.shim_path, spine=spine,
                             notifier_command=args.notifier, keep_awake=args.keep_awake,
                             chain_name=args.chain_name,
                             started_at=datetime.now(timezone.utc).isoformat(),
                             on_end=args.on_end, forced_provider=args.provider)
    except ChainAlreadyWalking as exc:
        print(f"chain: already walking — {exc}", file=sys.stderr)
        chain.notifier.send(describe_refusal(f"refused to start — {exc}"))
        return EXIT_ALREADY_WALKING
    except ProvidersRefused as exc:
        print(f"chain: {exc}", file=sys.stderr)
        chain.notifier.send(describe_refusal(f"refused to start — {exc}"))
        return 3
    except Exception as exc:
        # The same defect, at the other entry point: main() caught only ChainAlreadyWalking, so
        # an unanticipated crash starting a chain was just as silent as one advancing it.
        traceback.print_exc(file=sys.stderr)
        chain.notifier.send(describe_refusal(f"the walk at {args.start} crashed starting — {exc}"))
        return 5
    print(f"chain: acted={result.acted} ended={result.ended}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
