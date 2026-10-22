#!/usr/bin/env python3
"""gate_suite.py — run a product's suite command in the environment its CI calls for, and print
which environment that was.

WHY THIS EXISTS
    The developer's suite run, the code-integrity run and the seal's suite run each ran the project
    card's `Test command:` on the owner's Mac, and no closing record said where a suite ran, so a
    green verdict from a Mac was indistinguishable from one produced where the product's CI runs.
    `core/doctrine/engineering/languages/README.md` § Gate environment defaults says which
    environment a product's gates belong in — the macOS guest, a Podman container, or the owner's
    Mac — and this tool is the one place that answer is applied (resolution) and the one place the
    command is issued there (execution). It does not decide what a CI file means: the run that
    reads the repository supplies source-backed facts (`<CORE>/prompts/gate_suite.md`), and this
    tool re-opens each quoted source in the product's own checkout before it believes the fact.

TWO SEAMS IN ONE MODULE
    Resolution (`parse_request`, `resolve_environment`) is pure — a request built from findings
    goes
    in, an environment or a refusal comes out, and no process starts. Execution (`run_gate`) takes
    its filesystem, its readiness probes and its process runner as collaborators; the only place a
    real one is built is `build_host`, called from `main`.

    A third entry, `check_gate`, answers what `run` would decide for the same evidence without the
    owner's ask, and starts nothing: it is given the path contract, the tracked-file list and the
    product's decision record as data, reads files through a collaborator that can only read, and
    has no process runner, lock or writer to receive.

    The product's environment decision is the one fact that is not read from the change's branch.
    It is read from the product's `docs/nfdr.md` § 8 as committed on its local `main`, at every
    ask, in two steps that never mix: acquisition (`read_decision_record`, with a read-only Git
    collaborator and the `record` command) returns a snapshot of the file, or says `main` holds
    none; resolution (`read_current_decision`, `parse_request`) interprets that snapshot, lets its
    entry replace the frozen override and validates the entry's quote against the same snapshot.
    Acquisition has no environment policy, and nothing about a snapshot is kept between asks.

    A refusal is a value with no execution target, never a fallback to another environment, and the
    owner's Mac is returned in exactly three cases: the product has no CI, the product's own
    decision files choose it, or the owner asked.

    In the macOS guest the share is how the run proves the guest reaches its checkout, never what
    it builds from: the suite runs in a copy streamed from the host onto the guest's own disk
    (`_copy_to_guest_disk`).
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import TextIO

__version__ = "1.7.0"

PACKET_ROOT = Path("doctrine") / "engineering" / "languages"
REGISTRY_FILE = PACKET_ROOT / "README.md"

PLATFORM_MACOS = "macos"
PLATFORM_LINUX = "linux"
_ROOT_PRODUCT = "product"
_ROOT_CORE = "core"
_ROOT_RECORD = "record"
_LATEST_TAG = "latest"


class InputError(ValueError):
    """The sourced input is malformed — a field of the wrong shape or an unknown value. Distinct
    from a refusal: a refusal is a resolution outcome, this is an input that cannot be read."""


class EnvironmentKind(str, Enum):
    MACOS_GUEST = "macos-guest"
    CONTAINER = "container"
    OWNERS_MAC = "owners-mac"


class Architecture(str, Enum):
    ARM64 = "arm64"
    AMD64 = "amd64"


class OwnersMacCause(str, Enum):
    NO_CI = "no CI"
    OWNERS_ASK = "owner's ask"
    PRODUCT_DECISION = "product's decision"


class RefusalCase(str, Enum):
    """CP-619's cases. (f) is two values because the refusal text differs: a `decisions.amd64`
    source that does not hold up names its file, which a record ruling out both environments does
    not."""

    OTHER_PLATFORM = "a"
    MIXED_PLATFORMS = "b"
    NO_CONTAINER_DEFAULT = "c"
    CONFLICTING_IMAGES = "d"
    UNDETERMINED_VERSION = "e"
    DECISIONS_RULE_OUT_BOTH = "f-neither"
    FAILED_AMD64_SOURCE = "f-amd64"
    UNREADABLE_CI = "g"
    NO_GUEST_DEFAULT = "h"
    CONFLICTING_DECISIONS = "i"


class CiKind(str, Enum):
    NONE = "none"
    READABLE = "readable"
    UNREADABLE = "unreadable"


class OverrideKind(str, Enum):
    MACOS_GUEST = "macos-guest"
    CONTAINER = "container"
    OWNERS_MAC = "owners-mac"
    NEITHER = "neither"


# --- source-backed findings -----------------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    """A file and a line the input quotes from it. `root` says whose tree the file is in: the
    product's checkout, `<CORE>` for a language packet, or the committed decision record the ask
    was prepared with."""

    root: str
    file: str
    anchor: str


@dataclass(frozen=True)
class Runner:
    platform: str
    source: Source


@dataclass(frozen=True)
class CiFinding:
    kind: CiKind
    runners: tuple[Runner, ...] = ()
    failed: tuple[Source, ...] = ()


@dataclass(frozen=True)
class Override:
    kind: OverrideKind
    image: str | None
    tag: str | None
    architecture: Architecture | None
    failed: tuple[Source, ...]


@dataclass(frozen=True)
class Amd64Ask:
    failed: tuple[Source, ...]


@dataclass(frozen=True)
class Candidate:
    """The container a language's packet names, taken at the version CI or the toolchain file
    states. `image` is `None` for a language with no container default."""

    language: str
    image: str | None
    tag: str | None
    version_known: bool
    failed: tuple[Source, ...]


@dataclass(frozen=True)
class Share:
    """One folder the guest was started with: where it is on the host, and where it appears
    inside the guest."""

    host: str
    guest: str


@dataclass(frozen=True)
class Guest:
    """The host's guest and every share it was started with. A guest with no shares is a guest
    that was named and can place no run folder, which is not the same as no guest."""

    name: str
    shares: tuple[Share, ...]


@dataclass(frozen=True)
class GuestTool:
    """What a language's packet names for the macOS guest: the tool its gates run with, and the
    folder that holds it when the guest's own PATH does not (`None`)."""

    language: str
    tool: str
    folder: str | None


@dataclass(frozen=True)
class LanguageResolution:
    step: str
    languages: tuple[str, ...]


@dataclass(frozen=True)
class GateRequest:
    project: str
    languages: LanguageResolution
    ci: CiFinding
    override: Override | None
    amd64: Amd64Ask | None
    candidates: tuple[Candidate, ...]
    guest: Guest | None
    guest_tools: tuple[GuestTool, ...] = ()
    conflicting_decisions: bool = False


@dataclass(frozen=True)
class Resolved:
    kind: EnvironmentKind
    image: str | None
    tag: str | None
    architecture: Architecture | None
    owners_mac_cause: OwnersMacCause | None


@dataclass(frozen=True)
class Refused:
    """No environment. Carries what the refusal text names and nothing to execute."""

    project: str
    case: RefusalCase
    platforms: tuple[str, ...] = ()
    languages_without_default: tuple[str, ...] = ()
    candidate_images: tuple[tuple[str, str, str], ...] = ()
    image: str | None = None
    failed_sources: tuple[Source, ...] = field(default=())


# --- language resolution (languages/README.md § The resolution chain) ------------------------


def registry_extensions(readme_text: str) -> dict[str, str]:
    """Extension -> packet folder, read off the registry table of `languages/README.md` — the
    registry's own table and no other: the concern table below it has the same row shape."""
    extensions: dict[str, str] = {}
    in_registry = False
    for line in readme_text.splitlines():
        if line.startswith("## "):
            in_registry = "registry" in line.lower()
            continue
        if not in_registry or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] == "Language" or set(cells[1]) <= {"-", " "}:
            continue
        for extension in cells[2].split(","):
            extensions[extension.strip().strip("`")] = cells[1]
    return extensions


def resolve_languages(*, declared: list[str] | None, invoked: list[str] | None,
                      tracked: list[str], extensions: dict[str, str]) -> LanguageResolution:
    """The chain's first answer: `project.md` `Languages:`, else the invocation's, else the
    extensions of the git-tracked files — an untracked or ignored file is never in `tracked`."""
    if declared:
        return LanguageResolution("declared", tuple(name.lower() for name in declared))
    if invoked:
        return LanguageResolution("invoked", tuple(name.lower() for name in invoked))
    present = {extensions[suffix] for path in tracked
               if (suffix := PurePosixPath(path).suffix) in extensions}
    if present:
        ordered = tuple(dict.fromkeys(
            folder for folder in extensions.values() if folder in present))
        return LanguageResolution("inferred", ordered)
    return LanguageResolution("none", ())


GUEST_SECTION = "## In the macOS guest"
_GUEST_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(?:`([^`]+)`|\u2014)\s*\|\s*$")


def guest_tool(language: str, packet_text: str | None) -> GuestTool | None:
    """The tool a packet's `## In the macOS guest` table names, or `None` when the packet has no
    such table — a language with no guest default. The table is that section's and no other's."""
    in_section = False
    for line in (packet_text or "").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == GUEST_SECTION
            continue
        found = _GUEST_ROW.match(line.strip()) if in_section else None
        if found:
            return GuestTool(language, found.group(1), found.group(2))
    return None


# --- the loader: untrusted facts in, source-checked findings out ----------------------------------


def _text(value: object, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InputError(f"{where} must be text")
    return value


def _mapping(value: object, where: str) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InputError(f"{where} must be an object")
    return value


def _source(value: object, where: str) -> Source:
    found = _mapping(value, where)
    root = found.get("root", _ROOT_PRODUCT)
    if root not in (_ROOT_PRODUCT, _ROOT_CORE):
        raise InputError(f"{where}.root must be '{_ROOT_PRODUCT}' or '{_ROOT_CORE}'")
    file, anchor = _text(found.get("file"), f"{where}.file"), _text(found.get("anchor"),
                                                                     f"{where}.anchor")
    if not file or not anchor:
        raise InputError(f"{where} must quote a file and a line of it")
    return Source(root=root, file=file, anchor=anchor)


class _Checker:
    """Re-opens a quoted source in the tree it names — the product's own checkout or `<CORE>` —
    and says whether the file holds the quoted line."""

    def __init__(self, files, product_checkout: Path, core_root: Path,
                 record: DecisionRecord | None = None) -> None:
        self._files = files
        self._roots = {_ROOT_PRODUCT: product_checkout, _ROOT_CORE: core_root}
        self._record = record

    def holds(self, source: Source) -> bool:
        if source.root == _ROOT_RECORD:
            # The committed record this ask was prepared with, never a file in any checkout.
            return (self._record is not None and self._record.text is not None
                    and source.anchor in self._record.text)
        relative = PurePosixPath(source.file)
        if relative.is_absolute() or ".." in relative.parts:
            return False
        text = self._files.read_text(self._roots[source.root] / source.file)
        return text is not None and source.anchor in text

    def failed(self, *sources: Source | None) -> tuple[Source, ...]:
        return tuple(source for source in sources if source is not None and not self.holds(source))


def _ci_finding(raw: object, checker: _Checker) -> CiFinding:
    found = _mapping(raw, "ci")
    kind = found.get("finding")
    if kind == CiKind.NONE.value:
        # No CI is a finding with its evidence: the inventory that found none. Without it the
        # answer is missing, and a missing answer is a CI whose runner cannot be read.
        inventory = _text(found.get("inventory"), "ci.inventory")
        return CiFinding(CiKind.NONE if inventory and inventory.strip() else CiKind.UNREADABLE)
    if kind != CiKind.READABLE.value:
        return CiFinding(CiKind.UNREADABLE)
    runners = []
    for position, item in enumerate(found.get("runners") or []):
        entry = _mapping(item, f"ci.runners[{position}]")
        platform = _text(entry.get("platform"), f"ci.runners[{position}].platform")
        if not platform:
            raise InputError(f"ci.runners[{position}] must name a platform")
        runners.append(Runner(platform.strip().lower(),
                              _source(entry.get("source"), f"ci.runners[{position}].source")))
    return CiFinding(CiKind.READABLE, tuple(runners),
                     checker.failed(*(runner.source for runner in runners)))


def _override(raw: object, checker: _Checker) -> Override | None:
    if raw is None:
        return None
    found = _mapping(raw, "decisions.override")
    try:
        kind = OverrideKind(found.get("environment"))
    except ValueError:
        raise InputError("decisions.override.environment must be macos-guest, container, "
                         "owners-mac or neither") from None
    architecture = found.get("architecture")
    return Override(
        kind=kind, image=_text(found.get("image"), "decisions.override.image"),
        tag=_text(found.get("tag"), "decisions.override.tag"),
        architecture=Architecture(architecture) if architecture else None,
        failed=checker.failed(_source(found.get("source"), "decisions.override.source")))


def _amd64(raw: object, checker: _Checker) -> Amd64Ask | None:
    if not raw:
        return None
    found = _mapping(raw, "decisions.amd64")
    return Amd64Ask(failed=checker.failed(_source(found.get("source"), "decisions.amd64.source")))


def _candidate(raw: object, checker: _Checker) -> Candidate:
    found = _mapping(raw, "candidates[]")
    language = (_text(found.get("language"), "candidates[].language") or "").lower()
    image = _text(found.get("image"), f"candidates[{language}].image")
    tag = _text(found.get("tag"), f"candidates[{language}].tag")
    if not image:
        return Candidate(language, None, None, False, ())
    image_source = _source(found["image_source"], f"candidates[{language}].image_source") \
        if found.get("image_source") else None
    tag_source = _source(found["tag_source"], f"candidates[{language}].tag_source") \
        if found.get("tag_source") else None
    failed = checker.failed(image_source, tag_source)
    version_known = (bool(tag) and tag.lower() != _LATEST_TAG and image_source is not None
                     and tag_source is not None and not failed and tag in tag_source.anchor)
    return Candidate(language, image, tag, version_known, failed)


def _share(raw: object, position: int) -> Share:
    where = f"guest.shares[{position}]"
    if not isinstance(raw, dict):
        raise InputError(f"{where} must be an object")
    host = _text(raw.get("host"), f"{where}.host")
    if not host:
        raise InputError(f"{where} must name its host folder")
    if not host.startswith("/"):
        raise InputError(f"{where}.host must be an absolute path, not {host}")
    inside = _text(raw.get("guest"), f"{where}.guest")
    if not inside:
        raise InputError(f"{where} must name the folder it appears at inside the guest")
    return Share(host, inside)


def _shares(raw: object) -> tuple[Share, ...]:
    """The guest's share list, each share valid and no two naming one host folder. An absent,
    null or empty list is no shares; the retired scalar `share` supplies no mapping."""
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise InputError("guest.shares must be a list")
    shares: list[Share] = []
    first_at: dict[tuple[str, ...], int] = {}
    for position, item in enumerate(raw):
        share = _share(item, position)
        key = _components(share.host)
        if key in first_at:
            raise InputError(f"guest.shares[{first_at[key]}] and guest.shares[{position}] name "
                             f"the same host folder, {share.host}")
        first_at[key] = position
        shares.append(share)
    return tuple(shares)


def _components(path: str) -> tuple[str, ...]:
    """A path as its components, compared as given: a trailing `/` is nothing, and no symbolic
    link is followed."""
    return PurePosixPath(path).parts


def map_run_folder(shares: tuple[Share, ...], run_folder: str) -> str | None:
    """The run folder's in-guest folder, or `None` when no share holds it (CP-633, CP-634). A
    share holds the folder when its host folder is the folder or one of its ancestors, compared
    whole component by component; of several, the deepest wins whatever order they were given."""
    folder = _components(run_folder)
    holding = [share for share in shares
               if folder[:len(_components(share.host))] == _components(share.host)]
    if not holding:
        return None
    deepest = max(holding, key=lambda share: len(_components(share.host)))
    suffix = folder[len(_components(deepest.host)):]
    return str(PurePosixPath(deepest.guest, *suffix))


def parse_request(raw: dict | None, *, files, product_checkout: Path, language_root: Path,
                  core_root: Path, project: str,
                  record: DecisionRecord | None = None) -> GateRequest:
    """The sourced input as findings, every quoted source re-opened where it must be. An absent
    input is a request with no CI evidence — which resolves only for the owner's ask. A source is
    re-opened from `product_checkout`, the repository's root, where CI lives; languages are
    inferred from the tracked files under `language_root`, the product's own tree in it.

    `record` is the committed decision snapshot prepared for this ask. An environment entry in it
    is the product's decision: it replaces the input's `decisions.override` before that override is
    validated, and its quote is re-opened in the snapshot. Every other source keeps its root. With
    no record, or a record holding no entry, the input's own override stands."""
    checker = _Checker(files, product_checkout, core_root, record)
    raw = _mapping(raw, "input")
    chosen = _mapping(raw.get("languages"), "languages")
    extensions = registry_extensions(files.read_text(core_root / REGISTRY_FILE) or "")
    languages = resolve_languages(
        declared=chosen.get("declared"), invoked=chosen.get("invoked"),
        tracked=files.tracked_files(language_root), extensions=extensions)
    decisions = _mapping(raw.get("decisions"), "decisions")
    current = read_current_decision(record.text if record is not None else None)
    if isinstance(current, RecordDecision):
        override = _record_override(current, record, checker)
    elif isinstance(current, RecordConflict):
        override = None
    else:
        override = _override(decisions.get("override"), checker)
    guest = _mapping(raw.get("guest"), "guest")
    named = (guest_tool(language, files.read_text(
        core_root / PACKET_ROOT / language / "environment.md"))
        for language in languages.languages)
    return GateRequest(
        project=project, languages=languages, ci=_ci_finding(raw.get("ci"), checker),
        override=override,
        amd64=_amd64(decisions.get("amd64"), checker),
        candidates=tuple(_candidate(item, checker) for item in raw.get("candidates") or []),
        guest=Guest(guest["name"], _shares(guest.get("shares"))) if guest.get("name") else None,
        guest_tools=tuple(tool for tool in named if tool is not None),
        conflicting_decisions=isinstance(current, RecordConflict))


# --- resolution (CP-615 to CP-620), pure ----------------------------------------------------------


def _unique(items) -> tuple:
    return tuple(dict.fromkeys(items))


def _refuse(request: GateRequest, case: RefusalCase, **details) -> Refused:
    return Refused(project=request.project, case=case, **details)


def _resolve_guest(request: GateRequest) -> Resolved | Refused:
    """The macOS guest, for a product whose every language's packet names its guest tool."""
    named = {tool.language for tool in request.guest_tools}
    without_default = tuple(language for language in request.languages.languages
                            if language not in named)
    if without_default:
        return _refuse(request, RefusalCase.NO_GUEST_DEFAULT,
                       languages_without_default=without_default)
    return Resolved(EnvironmentKind.MACOS_GUEST, None, None, None, None)


def _resolve_override(request: GateRequest, override: Override) -> Resolved | Refused:
    if override.failed:
        return _refuse(request, RefusalCase.DECISIONS_RULE_OUT_BOTH, failed_sources=override.failed)
    if override.kind is OverrideKind.NEITHER:
        return _refuse(request, RefusalCase.DECISIONS_RULE_OUT_BOTH)
    if override.kind is OverrideKind.OWNERS_MAC:
        return Resolved(EnvironmentKind.OWNERS_MAC, None, None, None,
                        OwnersMacCause.PRODUCT_DECISION)
    if override.kind is OverrideKind.MACOS_GUEST:
        return _resolve_guest(request)
    if not override.image or not override.tag:
        return _refuse(request, RefusalCase.UNDETERMINED_VERSION, image=override.image)
    return _container(request, override.image, override.tag, override.architecture)


def _container(request: GateRequest, image: str, tag: str,
               architecture: Architecture | None) -> Resolved | Refused:
    if architecture is None:
        if request.amd64 is not None and request.amd64.failed:
            return _refuse(request, RefusalCase.FAILED_AMD64_SOURCE,
                           failed_sources=request.amd64.failed)
        architecture = Architecture.AMD64 if request.amd64 is not None else Architecture.ARM64
    return Resolved(EnvironmentKind.CONTAINER, image, tag, architecture, None)


def _resolve_linux(request: GateRequest) -> Resolved | Refused:
    # Every candidate a language was given is kept: a CI matrix can give one language several
    # versions, and keeping only the first or the last would pick a version CI never chose.
    by_language: dict[str, list[Candidate]] = {}
    for candidate in request.candidates:
        by_language.setdefault(candidate.language, []).append(candidate)
    languages = request.languages.languages
    without_default = tuple(
        language for language in languages
        if not any(candidate.image for candidate in by_language.get(language, ())))
    if without_default or not languages:
        return _refuse(request, RefusalCase.NO_CONTAINER_DEFAULT,
                       languages_without_default=without_default or languages)
    chosen = [candidate for language in languages for candidate in by_language[language]]
    unversioned = [candidate for candidate in chosen if not candidate.version_known]
    if unversioned:
        return _refuse(request, RefusalCase.UNDETERMINED_VERSION, image=unversioned[0].image,
                       failed_sources=_unique(source for candidate in unversioned
                                              for source in candidate.failed))
    for language in languages:
        versions = {(candidate.image, candidate.tag) for candidate in by_language[language]}
        if len(versions) > 1:
            return _refuse(request, RefusalCase.UNDETERMINED_VERSION,
                           image=by_language[language][0].image)
    if len({(candidate.image, candidate.tag) for candidate in chosen}) > 1:
        return _refuse(request, RefusalCase.CONFLICTING_IMAGES, candidate_images=tuple(
            (candidate.image, candidate.tag, candidate.language) for candidate in chosen))
    return _container(request, chosen[0].image, chosen[0].tag, None)


def resolve_environment(request: GateRequest, *, owners_ask: bool) -> Resolved | Refused:
    """CP-615 to CP-620. The owner's ask is an argument of its own — nothing in `request` can
    carry one — and outranks every other branch, a refusal included."""
    if owners_ask:
        return Resolved(EnvironmentKind.OWNERS_MAC, None, None, None, OwnersMacCause.OWNERS_ASK)
    ci = request.ci
    if ci.kind is CiKind.NONE:
        return Resolved(EnvironmentKind.OWNERS_MAC, None, None, None, OwnersMacCause.NO_CI)
    if ci.kind is CiKind.UNREADABLE or not ci.runners or ci.failed:
        return _refuse(request, RefusalCase.UNREADABLE_CI, failed_sources=ci.failed)
    if request.conflicting_decisions:
        return _refuse(request, RefusalCase.CONFLICTING_DECISIONS)
    if request.override is not None:
        return _resolve_override(request, request.override)
    platforms = _unique(runner.platform for runner in ci.runners)
    if set(platforms) - {PLATFORM_MACOS, PLATFORM_LINUX}:
        return _refuse(request, RefusalCase.OTHER_PLATFORM, platforms=platforms)
    if len(platforms) > 1:
        return _refuse(request, RefusalCase.MIXED_PLATFORMS, platforms=platforms)
    if platforms == (PLATFORM_MACOS,):
        return _resolve_guest(request)
    return _resolve_linux(request)


# ==================================================================================================
# Execution (CP-621 to CP-624): the card's command issued in the resolved environment
# ==================================================================================================

DASH = "\u2014"
PROJECT_CARD = Path("system") / "projects"
TOKEN_PREFIX = ".gate_suite_token_"
# Where a guest run's copy of its checkout lives: the guest's own disk, outside every share.
GUEST_SCRATCH_PREFIX = "/tmp/kensaiapp-gate-suite-"
# The build folder each package manifest keeps beside it, left out of the copy: build output
# (SwiftPM's, Cargo's) holds the absolute paths it was built at, and a build in the copy makes its
# own. Only the folder beside a tracked manifest is left out — never a source folder of that name.
BUILD_FOLDERS = {"Package.swift": ".build", "Cargo.toml": "target"}
# The per-worktree files of a repository's git dir (`git help repository-layout`): in a linked
# worktree's copy, the main checkout's are left out and the worktree's own laid in.
MAIN_CHECKOUT_STATE = ("HEAD", "ORIG_HEAD", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD",
                       "FETCH_HEAD", "index", "logs/HEAD", "refs/bisect", "refs/worktree",
                       "refs/rewritten", "config.worktree", "info/sparse-checkout")
REFUSAL_STATUS = 1
ERROR_STATUS = 2
KIND_RELATIVE = "relative"
NO_SUITE_CARD = "no suite"
NO_SUITE_SEAL = "no suite ran"

CLOSING_LINE = "The test command was not run, on the owner's Mac or anywhere else."
OVERRIDE_WAY = ("To run it, record an override in the product's decision files, or have the owner "
                "ask for the owner's Mac.")
RUNNER_WAY = ("To run it, read the runner from the product's CI configuration and supply it with "
              "its source, or have the owner ask for the owner's Mac.")
NO_OVERRIDE = "and the product's decision files record no override"
CONFLICT_CASE = ("the product's decision files name more than one environment for its gates, "
                 "and none of them is used")
CONFLICT_WAY = ("To run it, change the environment entries in § 8 of the product's docs/nfdr.md "
                "on its main branch until they name one environment, with the same image, tag and "
                "architecture, or have the owner ask for the owner's Mac.")

_CARD_LINE = re.compile(r"^\s*\**Test command:\**\s*(.*)$")
_CARD_COMMENT = re.compile(r"\s*<!--.*?(?:-->|$)")
_SKILL_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+")


class GateError(Exception):
    """The run cannot be carried out at all — no card, no path contract, an unreadable input file.
    Never a refusal (a refusal is a resolution outcome with its own printed line) and never a
    no-suite finding: it prints nothing on stdout, except the guest lock that cannot be taken,
    which is raised after the `Environment:` line is already printed and before any guest
    process."""


class ContractError(GateError):
    """The development-path contract could not be resolved."""


class ExecutableMissing(Exception):
    """The process runner could not find the executable it was asked to start."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name


# --- the product's committed decision: acquisition, then interpretation ---------------------------

NFDR_FILE = PurePosixPath("docs") / "nfdr.md"
MAIN_REF = "refs/heads/main"
RECORD_FIELDS = ("repository", "file", "revision", "text")


class RecordReadError(GateError):
    """`main` or the decision file on it could not be read. Distinct from the product holding no
    decision: an unreadable record is never read as an absent one."""


class RecordReadFailure(Exception):
    """A record reader's own failure; `str(self)` is the reason, in the reader's words."""


@dataclass(frozen=True)
class DecisionRecord:
    """What the product's repository held at one moment: where, at which commit of `main`, and the
    decision file's whole text there. `text` is `None` for a file `main` does not hold, and
    `revision` is `None` when the repository has no `main`. An empty file is a record."""

    repository: str
    file: str
    revision: str | None
    text: str | None

    def as_json(self) -> dict:
        return {"repository": self.repository, "file": self.file, "revision": self.revision,
                "text": self.text}


@dataclass(frozen=True)
class RecordDecision:
    """The environment an entry in the record names, and the entry's own text as its quote."""

    environment: OverrideKind
    image: str | None
    tag: str | None
    architecture: Architecture | None
    quote: str


@dataclass(frozen=True)
class RecordConflict:
    """The record's entries differ: none of them is the decision."""


def decision_location(paths: dict) -> tuple[str, str]:
    """The repository that holds the product, and the decision file's path inside it. A product
    path given absolutely is taken relative to its repository; one outside it is the repository's
    own root."""
    repository = str(paths["product_repo"])
    declared = PurePosixPath(str(paths["product_path"]))
    if declared.is_absolute():
        try:
            declared = declared.relative_to(repository)
        except ValueError:
            declared = PurePosixPath(".")
    return repository, str(declared / NFDR_FILE)


def read_decision_record(paths: dict, reader) -> DecisionRecord:
    """The product's decision file as committed on its local `main`, read fresh. `reader` has
    `main_revision(repository)` (the commit `main` is at, or `None`) and `file_at(repository,
    revision, path)` (the file's text there, or `None`). Main is resolved once and the file is
    read at that commit, so a `main` that moves meanwhile cannot mix two states."""
    repository, file = decision_location(paths)
    try:
        revision = reader.main_revision(repository)
        text = reader.file_at(repository, revision, file) if revision is not None else None
    except RecordReadFailure as failure:
        raise RecordReadError(f"the product's {file} cannot be read from the main branch of "
                              f"{repository}: {failure}") from None
    return DecisionRecord(repository, file, revision, text)


class GitRecordReader:
    """The real reader: read-only Git plumbing against the repository's object store. It fetches,
    checks out, merges and writes nothing, and never opens a file of the primary checkout.
    `run` is the process runner it is given, `subprocess.run` when none is."""

    def __init__(self, run: Callable[..., subprocess.CompletedProcess] | None = None) -> None:
        self._run = run

    def _git(self, repository: str, *args: str) -> subprocess.CompletedProcess:
        run = self._run if self._run is not None else subprocess.run
        try:
            return run(["git", "-C", repository, *args], capture_output=True)
        except OSError as error:
            raise RecordReadFailure(str(error)) from None

    @staticmethod
    def _reason(done: subprocess.CompletedProcess) -> str:
        reason = done.stderr.decode(errors="replace").rstrip("\n")
        return reason or f"git exited {done.returncode}"

    def main_revision(self, repository: str) -> str | None:
        done = self._git(repository, "rev-parse", "--verify", "--quiet", f"{MAIN_REF}^{{commit}}")
        if done.returncode == 0:
            return done.stdout.decode().strip()
        if done.returncode == 1 and not done.stderr.strip():
            return None
        raise RecordReadFailure(self._reason(done))

    def file_at(self, repository: str, revision: str, path: str) -> str | None:
        listed = self._git(repository, "ls-tree", "-z", revision, "--", path)
        if listed.returncode != 0:
            raise RecordReadFailure(self._reason(listed))
        if not listed.stdout:
            return None
        if listed.stdout.split(b" ", 2)[1] != b"blob":
            raise RecordReadFailure(f"{path} is not a file")
        blob = self._git(repository, "cat-file", "blob", f"{revision}:{path}")
        if blob.returncode != 0:
            raise RecordReadFailure(self._reason(blob))
        try:
            return blob.stdout.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RecordReadFailure(f"{path} is not UTF-8 text: {error}") from None


_FIELD_SPAN = re.compile(r"`([^`\n]+)`")
_FIELD = re.compile(r"^(environment|image|tag|architecture):\s*(\S.*)$")
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(\S.*)$")
_SECTION_EIGHT = re.compile(r"^8\.?(?:\s.*)?$")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])\s+")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_ENVIRONMENTS = {kind.value for kind in OverrideKind}
_ARCHITECTURES = {architecture.value for architecture in Architecture}


def _section_eight_items(text: str) -> list[str]:
    """Every list item of the section whose heading is numbered 8, each as its own lines (wrapped
    lines and subsections included), joined as the file holds them. The section runs to the next
    heading of the same level or a higher one. A fenced block is skipped whole."""
    items: list[str] = []
    current: list[str] | None = None
    in_section, level, fence = False, 0, None

    def close() -> None:
        nonlocal current
        if current:
            items.append("\n".join(current).rstrip())
        current = None

    for line in text.split("\n"):
        opening = _FENCE.match(line)
        if fence is not None:
            if opening and opening.group(1)[0] == fence:
                fence = None
            continue
        if opening:
            close()
            fence = opening.group(1)[0]
            continue
        heading = _HEADING_LINE.match(line)
        if heading:
            close()
            if in_section and len(heading.group(1)) <= level:
                in_section = False
            if not in_section and _SECTION_EIGHT.match(heading.group(2).strip()):
                in_section, level = True, len(heading.group(1))
            continue
        if not in_section:
            continue
        if _LIST_ITEM.match(line):
            close()
            current = [line]
        elif current is not None:
            if line.strip() and not line[:1].isspace() and not current[-1].strip():
                close()
            else:
                current.append(line)
    close()
    return items


def _entry_fields(item: str) -> dict[str, list[str]] | None:
    """The distinct values each field of the item's inline-code spans gives, in order, or `None`
    when the item names no environment this tool knows."""
    given: dict[str, list[str]] = {}
    for span in _FIELD_SPAN.findall(item):
        found = _FIELD.match(span.strip())
        if not found:
            continue
        name, value = found.group(1), found.group(2).strip()
        if (name == "environment" and value not in _ENVIRONMENTS) \
                or (name == "architecture" and value not in _ARCHITECTURES):
            continue
        if value not in given.setdefault(name, []):
            given[name].append(value)
    return given if "environment" in given else None


def read_current_decision(text: str | None) -> RecordDecision | RecordConflict | None:
    """The environment decision the record's § 8 makes. Entries are compared by what each supplies
    (environment, image, tag, architecture), before any default: equal tuples are one decision,
    and any difference — across entries or inside one — picks none. `None` is no entry at all,
    which is also what an absent file gives."""
    if text is None:
        return None
    entries: list[tuple[tuple, str]] = []
    for item in _section_eight_items(text):
        given = _entry_fields(item)
        if given is None:
            continue
        if any(len(values) > 1 for values in given.values()):
            return RecordConflict()
        entries.append((tuple((given.get(name) or [None])[0]
                              for name in ("environment", "image", "tag", "architecture")), item))
    if not entries:
        return None
    if len({fields for fields, _item in entries}) > 1:
        return RecordConflict()
    (environment, image, tag, architecture), quote = entries[0]
    return RecordDecision(OverrideKind(environment), image, tag,
                          Architecture(architecture) if architecture else None, quote)


def _record_override(decision: RecordDecision, record: DecisionRecord,
                     checker: _Checker) -> Override:
    """The override the record's entry makes: its whole entry is the quote, re-opened in the
    snapshot the entry was read from."""
    return Override(
        kind=decision.environment, image=decision.image, tag=decision.tag,
        architecture=decision.architecture,
        failed=checker.failed(Source(_ROOT_RECORD, record.file, decision.quote)))


class Gate(str, Enum):
    DEVELOPER = "developer"
    CODE_INTEGRITY = "code-integrity"
    SEAL = "seal"


@dataclass(frozen=True)
class Completed:
    status: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Host:
    """Every collaborator the run touches, handed in. `files` reads, lists, writes and removes,
    and names the git data a linked worktree's `.git` pointer leads to;
    `contract(worktree, project, key)` is the development-path contract; `processes` has `probe`
    (a readiness check), `issue` (the suite) and `pipe` (one host process's output fed to another's
    input, the guest copy) — separate calls, so a probe is never a suite issue;
    `guest_lock.hold()` is the blocking, exclusive context one guest run lives in;
    `record_reader` reads the product's committed decision (`read_decision_record`) — a host with
    none resolves from the sourced inputs alone; `run_records` keeps what a completed `run` printed
    (`FileRunRecords`) — a host with none records nothing, which is what keeps every existing
    `Host` construction and every direct `run_gate` call as it was."""

    files: object
    contract: Callable[[str, str, str], dict]
    processes: object
    new_token: Callable[[], str]
    core_root: Path
    guest_lock: object
    record_reader: object | None = None
    run_records: object | None = None


@dataclass(frozen=True)
class GateResult:
    """What the run did: the line it printed first, the command and directory it was given, the
    exit status it ends with, whatever the suite wrote, and whether a suite was issued at all."""

    environment_line: str
    command: str
    cwd: str
    status: int
    stdout: str
    stderr: str
    suite_issued: bool


class _NotReady(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


# --- the card -------------------------------------------------------------------------------------


def read_card_command(card_text: str) -> str | None:
    """The card's `Test command:` text with its markup and trailing comment removed and nothing
    else touched — the shell text the run issues. `None` when the card carries no such line."""
    for line in card_text.splitlines():
        found = _CARD_LINE.match(line)
        if not found:
            continue
        value = _CARD_COMMENT.sub("", found.group(1)).strip()
        if len(value) > 1 and value.startswith("`") and value.endswith("`") \
                and "`" not in value[1:-1]:
            value = value[1:-1].strip()
        return value or None
    return None


def product_tree(paths: dict) -> Path:
    """The product's own tree inside its checkout — the working root the resolution chain infers
    languages under (`languages/README.md` § The resolution chain, step 3). An in-repo product
    shares its repository with the instance, so the repository's root is not the product's. A
    product path that cannot be placed under its repository gives the whole checkout: that can
    add a language the product does not hold, never drop one it does."""
    checkout = Path(paths["product_worktree"])
    declared = Path(paths["product_path"])
    if not declared.is_absolute():
        return checkout / declared
    try:
        return checkout / declared.relative_to(paths["product_repo"])
    except ValueError:
        return checkout


def _card_names_no_command(command: str) -> bool:
    """The seal's `No command` forms: `none`, `N/A`, a `validated by use` verdict, a skill name."""
    text = command.strip()
    return (text.lower() in ("none", "n/a") or text.lower().startswith("validated by use")
            or bool(_SKILL_NAME.fullmatch(text)))


# --- the printed line and the refusal's words -----------------------------------------------------


def environment_line(resolved: Resolved, guest: Guest | None) -> str:
    if resolved.kind is EnvironmentKind.OWNERS_MAC:
        return f"Environment: owners-mac {DASH} {resolved.owners_mac_cause.value}"
    if resolved.kind is EnvironmentKind.MACOS_GUEST:
        return f"Environment: macos-guest {DASH} {guest.name if guest else 'no guest given'}"
    return (f"Environment: container {DASH} {resolved.image}:{resolved.tag}, "
            f"{resolved.architecture.value}")


def refusal_case_text(refused: Refused, *, failed_override_source: Source | None = None) -> str:
    """The text that follows `unresolved — ` on the printed line, and `{case}` in the first line
    of the refusal on standard error. `failed_override_source` is the already checked source of a
    recorded override that did not hold up; only the refusal for that cause is given it."""
    case = refused.case
    if case is RefusalCase.OTHER_PLATFORM:
        return f"the product's CI runs on a platform other than macOS or Linux, {NO_OVERRIDE}"
    if case is RefusalCase.MIXED_PLATFORMS:
        return f"the product's CI runs on both macOS and Linux, {NO_OVERRIDE}"
    if case is RefusalCase.NO_CONTAINER_DEFAULT and not refused.languages_without_default:
        return ("the product's CI runs on Linux, no container default can be chosen because no "
                f"language was resolved for the product, {NO_OVERRIDE}")
    if case is RefusalCase.NO_CONTAINER_DEFAULT:
        return (f"the product's CI runs on Linux, no container default exists for "
                f"{', '.join(refused.languages_without_default)}, {NO_OVERRIDE}")
    if case is RefusalCase.NO_GUEST_DEFAULT:
        return (f"the product's CI runs on macOS, no macOS guest toolchain is named for "
                f"{', '.join(refused.languages_without_default)}, {NO_OVERRIDE}")
    if case is RefusalCase.CONFLICTING_IMAGES:
        return (f"the product's CI runs on Linux, its languages call for more than one container "
                f"image, {NO_OVERRIDE}")
    if case is RefusalCase.UNDETERMINED_VERSION:
        image = refused.image or "the container image"
        return f"the version to tag {image} with cannot be determined"
    if case is RefusalCase.DECISIONS_RULE_OUT_BOTH and failed_override_source is not None:
        return ("the override in the product's decision files cannot be used, because its source, "
                f"{failed_override_source.file}, does not contain the text the input quotes "
                "from it")
    if case is RefusalCase.DECISIONS_RULE_OUT_BOTH:
        return ("the product's decision files say it can use neither the macOS guest nor a "
                "container, and name no environment")
    if case is RefusalCase.CONFLICTING_DECISIONS:
        return CONFLICT_CASE
    if case is RefusalCase.FAILED_AMD64_SOURCE:
        return ("the amd64 requirement in the product's decision files cannot be used, because "
                f"its source, {refused.failed_sources[0].file}, does not contain the text the "
                "input quotes from it")
    return "the runner cannot be read from the product's CI configuration"


def refusal_lines(refused: Refused, *, case_text: str | None = None) -> list[str]:
    """The refusal on standard error, one string per line, in the order the Content Editor wrote.
    `case_text` is the case text already chosen for the printed line, so both carry the same one."""
    if case_text is None:
        case_text = refusal_case_text(refused)
    lines = [f"gate_suite: no environment resolves for project {refused.project}: {case_text}."]
    if refused.case is RefusalCase.OTHER_PLATFORM:
        lines.append(f"The product's CI runs on: {', '.join(refused.platforms)}.")
    if refused.case is RefusalCase.CONFLICTING_IMAGES:
        images = ", ".join(f"{image}:{tag} for {language}"
                           for image, tag, language in refused.candidate_images)
        lines.append(f"The container images the product's languages call for: {images}.")
    for source in refused.failed_sources:
        lines.append(f'{source.file} does not contain the text the input quotes from it: '
                     f'"{source.anchor}".')
    if refused.case is RefusalCase.UNREADABLE_CI:
        lines.append(RUNNER_WAY)
    elif refused.case is RefusalCase.CONFLICTING_DECISIONS:
        lines.append(CONFLICT_WAY)
    else:
        lines.append(OVERRIDE_WAY)
    lines.append(CLOSING_LINE)
    return lines


def _failed_override_source(request: GateRequest, refused: Refused) -> Source | None:
    """The recorded override's failed source when that is why the decision files were refused. A
    failed `decisions.amd64` source is refused with a case of its own and is not this cause."""
    override = request.override
    if refused.case is RefusalCase.DECISIONS_RULE_OUT_BOTH and override and override.failed:
        return override.failed[0]
    return None


def unshared_lines(guest: Guest, checkout: str) -> list[str]:
    """The refusal for a checkout no share holds, one string per line (CP-637)."""
    lines = [f"gate_suite: this run's checkout, {checkout}, is under none of the shares this run "
             f"was given for the macOS guest {guest.name}."]
    if guest.shares:
        lines.append("The shares this run was given: "
                     f"{', '.join(share.host for share in guest.shares)}.")
        lines.append("The checkout has to be under one of those folders, or the guest has to be "
                     "started with a share that holds it.")
    else:
        lines.append("This run was given no shares for the guest. Each share is given in "
                     "guest.shares, with the host folder and the folder it appears at inside the "
                     "guest.")
    return [*lines, CLOSING_LINE]


# --- the command in each environment (CP-621) -----------------------------------------------------


def mac_argv(command: str) -> list[str]:
    return ["sh", "-c", command]


def container_argv(resolved: Resolved, command: str, cwd: str) -> list[str]:
    architecture = ["--arch", "amd64"] if resolved.architecture is Architecture.AMD64 else []
    return ["podman", "run", "--rm", "-v", f"{cwd}:/work", "-w", "/work", *architecture,
            f"{resolved.image}:{resolved.tag}", "sh", "-c", command]


def _on_path(tools: Sequence[GuestTool], command: str) -> str:
    """`command` with every folder the tools name put ahead of the guest's own PATH. `tart exec`
    runs a non-login shell, so nothing the guest's login profile adds to PATH is on it."""
    folders = tuple(dict.fromkeys(tool.folder for tool in tools if tool.folder))
    if not folders:
        return command
    return f"export PATH={':'.join(shlex.quote(f) for f in folders)}:\"$PATH\" && {command}"


def guest_argv(guest: Guest, command: str, folder: str,
               tools: Sequence[GuestTool] = ()) -> list[str]:
    return ["tart", "exec", guest.name, "sh", "-c",
            _on_path(tools, f"cd {shlex.quote(folder)} && {command}")]


# --- readiness (CP-622): probes only, never a start, never a fallback -----------------------------


def _last_stderr_line(completed: Completed) -> str | None:
    lines = [line for line in completed.stderr.splitlines() if line.strip()]
    return lines[-1] if lines else None


def _probe(host: Host, argv: list[str], missing: str) -> Completed:
    try:
        return host.processes.probe(argv)
    except ExecutableMissing:
        raise _NotReady(missing) from None


def _check_podman(host: Host) -> None:
    missing = "gate_suite: podman was not found on PATH."
    answered = _probe(host, ["podman", "info"], missing)
    if answered.status == 0:
        return
    machine = _probe(host, ["podman", "machine", "inspect", "--format", "{{.State}}"], missing)
    if machine.status == 0 and machine.stdout.strip().lower() in ("stopped", "exited"):
        raise _NotReady("gate_suite: the Podman machine is not running.",
                        _last_stderr_line(answered))
    raise _NotReady("gate_suite: Podman cannot be reached.", _last_stderr_line(answered))


def _guest_is_running(listing: Completed, name: str) -> bool:
    try:
        entries = json.loads(listing.stdout)
    except ValueError:
        return False
    return any(isinstance(entry, dict) and entry.get("Name") == name
               and str(entry.get("State", "")).lower() == "running" for entry in entries)


def _check_guest_before_share(host: Host, guest: Guest) -> None:
    missing = "gate_suite: tart was not found on PATH, so the macOS guest cannot be reached."
    unreachable = f"gate_suite: the macOS guest {guest.name} cannot be reached through tart exec."
    listing = _probe(host, ["tart", "list", "--format", "json"], missing)
    if listing.status != 0:
        raise _NotReady(unreachable, _last_stderr_line(listing))
    if not _guest_is_running(listing, guest.name):
        raise _NotReady(f"gate_suite: the macOS guest {guest.name} is not running.")
    answered = _probe(host, ["tart", "exec", guest.name, "true"], missing)
    if answered.status != 0:
        raise _NotReady(unreachable, _last_stderr_line(answered))


def _check_guest_share(host: Host, guest: Guest, cwd: str, folder: str, token_name: str) -> None:
    present = f"test -f {shlex.quote(folder.rstrip('/') + '/' + token_name)}"
    found = _probe(host, ["tart", "exec", guest.name, "sh", "-c", present],
                   "gate_suite: tart was not found on PATH, so the macOS guest cannot be reached.")
    if found.status != 0:
        raise _NotReady(f"gate_suite: the macOS guest {guest.name} cannot see this run's "
                        f"checkout, {cwd}.", _last_stderr_line(found))


def _check_guest_tools(host: Host, guest: Guest, tools: Sequence[GuestTool]) -> None:
    """Each language's tool, looked for in the guest as the suite will look for it — so a guest
    built without a toolchain stops the run here, before a suite whose `command not found` would
    read as a failing test."""
    for tool in tools:
        found = _probe(host, ["tart", "exec", guest.name, "sh", "-c",
                              _on_path((tool,), f"command -v {shlex.quote(tool.tool)}")],
                       "gate_suite: tart was not found on PATH, so the macOS guest cannot be "
                       "reached.")
        if found.status != 0:
            where = f"in {tool.folder} or on the guest's PATH" if tool.folder \
                else "on the guest's PATH"
            raise _NotReady(f"gate_suite: the macOS guest {guest.name} has no {tool.tool}, the "
                            f"tool {tool.language}'s gates run with, {where}.",
                            _last_stderr_line(found))


def build_output(tracked: Sequence[str]) -> list[str]:
    """The tar exclude pattern for each build folder beside a tracked package manifest, anchored
    at the checkout's root (`^./`) with its glob characters escaped, so it matches that one
    folder and no other path of the same name."""
    patterns = []
    for path in tracked:
        found = PurePosixPath(path)
        folder = BUILD_FOLDERS.get(found.name)
        if folder is None:
            continue
        parent = "" if str(found.parent) == "." else f"{found.parent}/"
        patterns.append("^./" + re.sub(r"([\\*?\[])", r"\\\1", f"{parent}{folder}"))
    return patterns


def _copy_to_guest_disk(host: Host, guest: Guest, cwd: str, scratch: str) -> None:
    """The checkout streamed from the host onto the guest's own disk, where its suite builds,
    after any copy an earlier run left (under the host-wide lock, every one is stale).

    Not read through the share: the guest's view of a virtiofs share goes stale for a file the
    host replaced by renaming over it, and opening that file in the guest fails ("No such file or
    directory") long after — so a build or a copy on the share fails with errors that are not the
    code's. A copy that fails is the environment's failure, never the suite's.

    A checkout whose `.git` is a pointer file (a linked worktree) names git data at a host path
    the guest cannot reach, so git in the copy would fail. The copy's `.git` is a folder instead:
    the repository's shared data, with the worktree's own state (its HEAD, its index) laid over
    it — a repository that resolves inside the guest, on the same branch and the same index."""
    linked = host.files.linked_git_dirs(Path(cwd))
    excluded = [arg for path in [*build_output(host.files.tracked_files(Path(cwd))),
                                 *(["^./.git"] if linked is not None else [])]
                for arg in ("--exclude", path)]
    _stream(host, guest, ["tar", "-C", cwd, "--no-mac-metadata", *excluded, "-cf", "-", "."],
            f"rm -rf {GUEST_SCRATCH_PREFIX}* && mkdir {shlex.quote(scratch)} && "
            f"tar -C {shlex.quote(scratch)} -xf -", cwd, f"this run's checkout, {cwd},")
    if linked is None:
        return
    git_dir, common_dir = linked
    target = shlex.quote(f"{scratch}/.git")
    # The main checkout's own state never stands in for the worktree's, even where the worktree
    # has none of a kind (no index, no `config.worktree`): git would read it as the worktree's.
    own_state = [] if git_dir == common_dir else MAIN_CHECKOUT_STATE
    _stream(host, guest, ["tar", "-C", str(common_dir), "--no-mac-metadata",
                          *(arg for path in ("worktrees", *own_state)
                            for arg in ("--exclude", f"^./{path}")), "-cf", "-", "."],
            f"mkdir {target} && tar -C {target} -xf -", cwd,
            f"the git data of this run's checkout, {common_dir},")
    if git_dir == common_dir:
        return
    _stream(host, guest, ["tar", "-C", str(git_dir), "--no-mac-metadata",
                          "--exclude", "^./commondir", "--exclude", "^./gitdir",
                          "-cf", "-", "."],
            f"tar -C {target} -xf -", cwd, f"the worktree state of this run's checkout, {git_dir},")


def _stream(host: Host, guest: Guest, producer: list[str], unpack: str, cwd: str,
            what: str) -> None:
    """One host folder's tar stream unpacked in the guest; a failure is `_NotReady`."""
    try:
        found = host.processes.pipe(producer, ["tart", "exec", "-i", guest.name, "sh", "-c",
                                               unpack], cwd=cwd)
    except ExecutableMissing as missing:
        raise _NotReady(f"gate_suite: {missing.name} was not found on PATH, so this run's "
                        f"checkout cannot be copied onto the macOS guest {guest.name}'s own "
                        f"disk.") from None
    if found.status != 0:
        raise _NotReady(f"gate_suite: {what} could not be copied onto the "
                        f"macOS guest {guest.name}'s own disk, where its suite builds.",
                        _last_stderr_line(found))


def _remove_guest_copy(host: Host, guest: Guest, scratch: str, err: TextIO) -> None:
    """The guest-local copy removed, whatever the suite returned. A copy that stays is said on
    standard error and leaves the suite's status alone: the suite already ran."""
    try:
        removed = host.processes.probe(["tart", "exec", guest.name, "sh", "-c",
                                        f"rm -rf {shlex.quote(scratch)}"])
    except ExecutableMissing:
        removed = None
    if removed is None or removed.status != 0:
        _fail(err, [f"gate_suite: the copy of this run's checkout at {scratch} in the macOS guest "
                    f"{guest.name} could not be removed."])


# --- the run --------------------------------------------------------------------------------------


def _declare(out: TextIO, line: str) -> None:
    out.write(line + "\n")
    out.flush()


def _fail(err: TextIO, lines: list[str]) -> None:
    err.write("".join(line + "\n" for line in lines))
    err.flush()


def _stopped(*, line: str, command: str, cwd: str, status: int = REFUSAL_STATUS) -> GateResult:
    return GateResult(line, command, cwd, status, "", "", False)


def _unreachable(err: TextIO, problem: _NotReady) -> None:
    lines = [problem.message]
    if problem.detail is not None:
        lines.append(f"The check that failed reported: {problem.detail}")
    _fail(err, [*lines, CLOSING_LINE])


def _issue(host: Host, argv: list[str], cwd: str, line: str, command: str,
           out: TextIO, err: TextIO) -> GateResult:
    completed = host.processes.issue(argv, cwd=cwd)
    out.write(completed.stdout)
    err.write(completed.stderr)
    out.flush()
    err.flush()
    return GateResult(line, command, cwd, completed.status, completed.stdout,
                      completed.stderr, True)


def _run_in_guest(host: Host, guest: Guest, folder: str, command: str, cwd: str, line: str,
                  out: TextIO, err: TextIO, tools: Sequence[GuestTool] = ()) -> GateResult:
    """One guest run, from before its first guest process to after its token and its guest-local
    copy are removed, inside the host-wide lock (CP-641): another guest run waits until this one
    has left. The suite runs in a copy of the checkout on the guest's own disk
    (`_copy_to_guest_disk`)."""
    token = host.new_token()
    token_name = f"{TOKEN_PREFIX}{token}"
    token_path = Path(cwd) / token_name
    scratch = f"{GUEST_SCRATCH_PREFIX}{token}"
    copied = False
    with host.guest_lock.hold():
        try:
            _check_guest_before_share(host, guest)
            host.files.write_text(token_path, token_name)
            _check_guest_share(host, guest, cwd, folder, token_name)
            _check_guest_tools(host, guest, tools)
            copied = True
            _copy_to_guest_disk(host, guest, cwd, scratch)
            return _issue(host, guest_argv(guest, command, scratch, tools), cwd, line, command,
                          out, err)
        except _NotReady as problem:
            _unreachable(err, problem)
            return _stopped(line=line, command=command, cwd=cwd)
        finally:
            try:
                if copied:
                    _remove_guest_copy(host, guest, scratch, err)
            finally:
                host.files.remove(token_path)


def run_gate(*, gate: Gate | str, worktree: str, project: str, key: str, inputs: dict | None,
             owners_ask: bool, host: Host, out: TextIO, err: TextIO) -> GateResult:
    """One gate's suite run: read the card and the path contract (both required), print the
    environment line first, then issue the card's command there — or print why nothing ran."""
    gate = Gate(gate)
    paths = host.contract(worktree, project, key)
    card = host.files.read_text(Path(worktree) / PROJECT_CARD / project / "project.md")
    command = read_card_command(card) if card is not None else None
    if command is None:
        raise GateError(f"project {project} has no readable `Test command:` on its card in "
                        f"{worktree}")
    # The card's command is written from the product's change worktree root (project_template.md,
    # `Test command:`), so it runs there: the instance worktree for an in-repo product, the
    # product's own worktree for an external one.
    cwd = paths["product_worktree"]
    in_own_repo = paths["kind"] != KIND_RELATIVE

    if gate is Gate.SEAL and (in_own_repo or _card_names_no_command(command)):
        line = f"Environment: none {DASH} {NO_SUITE_SEAL}"
        _declare(out, line)
        return GateResult(line, command, cwd, 0, "", "", False)
    if gate is not Gate.SEAL and command.strip().lower() == "none":
        line = f"Environment: none {DASH} {NO_SUITE_CARD}"
        _declare(out, line)
        return GateResult(line, command, cwd, 0, "", "", False)

    # The owner's ask reads no record. Every other ask reads `main` afresh, so a decision committed
    # since the last ask is seen and one read earlier is never reused.
    record = None
    if not owners_ask and host.record_reader is not None:
        record = read_decision_record(paths, host.record_reader)
    request = parse_request(
        inputs, files=host.files, product_checkout=Path(paths["product_worktree"]),
        language_root=product_tree(paths), core_root=host.core_root, project=project,
        record=record)
    resolved = resolve_environment(request, owners_ask=owners_ask)
    if isinstance(resolved, Refused):
        case_text = refusal_case_text(
            resolved, failed_override_source=_failed_override_source(request, resolved))
        line = f"Environment: unresolved {DASH} {case_text}"
        _declare(out, line)
        _fail(err, refusal_lines(resolved, case_text=case_text))
        return _stopped(line=line, command=command, cwd=cwd)

    line = environment_line(resolved, request.guest)
    _declare(out, line)
    try:
        if resolved.kind is EnvironmentKind.OWNERS_MAC:
            return _issue(host, mac_argv(command), cwd, line, command, out, err)
        if resolved.kind is EnvironmentKind.CONTAINER:
            _check_podman(host)
            return _issue(host, container_argv(resolved, command, cwd), cwd, line, command,
                          out, err)
        if request.guest is None:
            raise _NotReady("gate_suite: this run was given no macOS guest to run in.")
        folder = map_run_folder(request.guest.shares, cwd)
        if folder is None:
            _fail(err, unshared_lines(request.guest, cwd))
            return _stopped(line=line, command=command, cwd=cwd)
        return _run_in_guest(host, request.guest, folder, command, cwd, line, out, err,
                             request.guest_tools)
    except _NotReady as problem:
        _unreachable(err, problem)
        return _stopped(line=line, command=command, cwd=cwd)


# ==================================================================================================
# The last-run record: what a completed `run` printed, kept for the commit that closes the change
# ==================================================================================================

RUN_RECORDS_NAMESPACE = "kensaiapp-gate-runs"
ENVIRONMENT_PREFIX = "Environment:"


@dataclass(frozen=True)
class GateRun:
    """One completed `run`, as its caller saw it: the change key, the checkout this copy answers
    for, the first `Environment:` line printed on stdout (None when none was), every character
    forwarded to each stream, and the status returned. Disposable runtime evidence, never a
    committed artifact — distinct from `DecisionRecord`, the product's committed decision."""

    key: str
    checkout: str
    environment_line: str | None
    stdout: str
    stderr: str
    status: int


def canonical_checkout(path: str | Path) -> str:
    """The checkout's identity: its absolute path with every link and `..` resolved."""
    return str(Path(path).resolve())


class FileRunRecords:
    """The run-record store: one JSON file per (checkout, key) pair, under `root`, named by a
    digest of the pair's unambiguous serialization. A record is written to a unique temporary file
    in its destination directory and moved into place with one atomic replace, so a reader sees the
    previous complete record or the new one and never half of either; the last replace to land is
    the last published run. The record carries its own identity and a lookup verifies it, so a file
    found at an address is never accepted for being there. `replace` is the atomic move, handed in
    so a test can stand inside a publication."""

    def __init__(self, root: Path, *, replace: Callable[[str, str], None] = os.replace) -> None:
        self.root = root
        self._replace = replace

    def path_for(self, checkout: str, key: str) -> Path:
        pair = json.dumps([canonical_checkout(checkout), key])
        return self.root / f"{hashlib.sha256(pair.encode()).hexdigest()}.json"

    def publish(self, run: GateRun, checkouts: Sequence[str]) -> None:
        """Keep `run` for the change `run.key` under each distinct checkout identity."""
        for checkout in dict.fromkeys(canonical_checkout(path) for path in checkouts):
            self._publish_one(replace(run, checkout=checkout))

    def _publish_one(self, run: GateRun) -> None:
        destination = self.path_for(run.checkout, run.key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staged = tempfile.NamedTemporaryFile(
            "w", dir=destination.parent, suffix=".tmp", delete=False, encoding="utf-8")
        try:
            with staged:
                json.dump({"key": run.key, "checkout": run.checkout,
                           "environment_line": run.environment_line, "stdout": run.stdout,
                           "stderr": run.stderr, "status": run.status}, staged)
            self._replace(staged.name, str(destination))
        except BaseException:
            Path(staged.name).unlink(missing_ok=True)
            raise

    def latest(self, checkout: str, key: str) -> GateRun | None:
        """The last completed run for this checkout and key, or None when there is none."""
        wanted = canonical_checkout(checkout)
        try:
            found = json.loads(self.path_for(wanted, key).read_text(encoding="utf-8"))
            run = GateRun(found["key"], found["checkout"], found["environment_line"],
                          found["stdout"], found["stderr"], found["status"])
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return run if (run.checkout, run.key) == (wanted, key) else None


def default_run_records() -> FileRunRecords:
    return FileRunRecords(Path(tempfile.gettempdir()) / RUN_RECORDS_NAMESPACE)


class _Forwarding:
    """A stream that writes through to the one it wraps, unchanged, and keeps what it wrote."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self.written: list[str] = []

    def write(self, text: str) -> int:
        count = self._stream.write(text)
        self.written.append(text)
        return count

    def flush(self) -> None:
        self._stream.flush()

    def __getattr__(self, name: str):
        return getattr(self._stream, name)


class _RunRecording:
    """What one `run` printed and which checkouts it ran for, gathered at the CLI boundary: the
    two streams are forwarded, and the path contract is read as the run reads it."""

    def __init__(self, out: TextIO, err: TextIO) -> None:
        self.out, self.err = _Forwarding(out), _Forwarding(err)
        self.checkouts: tuple[str, ...] = ()

    def watching(self, host: Host) -> Host:
        def contract(worktree: str, project: str, key: str) -> dict:
            paths = host.contract(worktree, project, key)
            # The path tool's `code_worktree` is its `product_worktree`; a contract naming only
            # the latter says the same thing.
            self.checkouts = (paths["pipeline_worktree"],
                              paths.get("code_worktree", paths["product_worktree"]))
            return paths

        return replace(host, contract=contract)

    def publish(self, store, key: str, status: int) -> None:
        if store is None or not self.checkouts:
            return
        stdout = "".join(self.out.written)
        declarations = [line for line in stdout.split("\n") if line.startswith(ENVIRONMENT_PREFIX)]
        run = GateRun(key=key, checkout="", environment_line=declarations[0] if declarations
                      else None, stdout=stdout, stderr="".join(self.err.written), status=status)
        try:
            store.publish(run, self.checkouts)
        except OSError:
            # Evidence is best-effort beside the gate: a record that cannot be kept changes
            # neither what the run printed nor the status it returns.
            pass


# ==================================================================================================
# The check: whether the evidence resolves, with nothing run (CP-702 to CP-708)
# ==================================================================================================

_CARD_PRODUCT_PATH = re.compile(r"^\s*\**Product path:\**\s*(.*)$")
# The refusals only a recorded environment settles: with no override recorded, the readable CI and
# the languages' packet defaults still name no environment (CP-704).
OWED_CASES = frozenset({
    RefusalCase.OTHER_PLATFORM, RefusalCase.MIXED_PLATFORMS, RefusalCase.NO_CONTAINER_DEFAULT,
    RefusalCase.CONFLICTING_IMAGES, RefusalCase.UNDETERMINED_VERSION,
    RefusalCase.NO_GUEST_DEFAULT})
PATHS_FIELDS = ("project", "key", "instance_worktree", "product_path", "product_worktree",
                "product_repo")
NO_SUITE_DETAIL = ("none: the product has no suite, because its project card names no test "
                   "command")
GUEST_DETAIL = "macos-guest: the product's gates run in the macOS guest"
OWNERS_MAC_DETAIL = {
    OwnersMacCause.NO_CI: "owners-mac: the product has no CI, so its gates run on the owner's Mac",
    OwnersMacCause.PRODUCT_DECISION: ("owners-mac: the product's decision files choose the "
                                      "owner's Mac for its gates"),
}


class CheckAnswer(str, Enum):
    RESOLVES = "resolves"
    OWES_DECISION = "owes a decision"
    DOES_NOT_RESOLVE = "does not resolve"


@dataclass(frozen=True)
class CheckContext:
    """What the caller prepared before the check: the path tool's whole contract, the product's
    tracked files (one product-relative name each) and the product's decision record as `record`
    made it just before. `paths_file` and `decision_record_file` are what a message calls the
    places those came from. No `decision_record` is the legacy path, which takes the decision from
    the sourced inputs only; a record that says `main` holds none is a prepared answer."""

    paths: dict
    tracked_files: tuple[str, ...]
    paths_file: str = "paths"
    decision_record: DecisionRecord | None = None
    decision_record_file: str = "decision-record"


@dataclass(frozen=True)
class CheckResult:
    answer: CheckAnswer
    detail: str
    status: int


@dataclass(frozen=True)
class CheckHost:
    """The check's collaborators: files it can only read, and where `<CORE>` is."""

    files: object
    core_root: Path


class _SnapshotFiles:
    """Reads through to `files` and answers the tracked list from the prepared snapshot, so
    `parse_request` never asks Git. A valid empty snapshot stays empty."""

    def __init__(self, files, tracked_files: Sequence[str]) -> None:
        self._files = files
        self._tracked = list(tracked_files)

    def read_text(self, path: Path) -> str | None:
        return self._files.read_text(path)

    def tracked_files(self, root: Path) -> list[str]:
        return list(self._tracked)


def _card_product_path(card_text: str) -> str | None:
    for line in card_text.splitlines():
        found = _CARD_PRODUCT_PATH.match(line)
        if found:
            return _CARD_COMMENT.sub("", found.group(1)).strip().strip("`") or None
    return None


def _validate_context(context: CheckContext, *, worktree: str, project: str, key: str) -> None:
    """The context is for this change: every field present, and project, change key and instance
    worktree the ones the check was asked about."""
    paths, where = context.paths, context.paths_file
    for name in PATHS_FIELDS:
        if not isinstance(paths, dict) or paths.get(name) in (None, ""):
            raise GateError(f"the paths file {where} has no {name}")
    for what, name, expected in (("project", "project", project), ("change key", "key", key),
                                 ("instance worktree", "instance_worktree", worktree)):
        found = str(paths[name])
        if found.rstrip("/") != expected.rstrip("/"):
            raise GateError(f"the paths file {where} is for {what} {found}, not {expected}")
    if context.decision_record is not None:
        repository, file = decision_location(paths)
        for what, found, expected in (
                ("product repository", context.decision_record.repository, repository),
                ("decision file", context.decision_record.file, file)):
            if found != expected:
                raise GateError(f"the decision-record file {context.decision_record_file} is for "
                                f"{what} {found}, not {expected}")


def _languages_in_order(request: GateRequest, wanted) -> str:
    """The wanted languages named once each, in the order the input resolves them."""
    wanted = set(wanted)
    return ", ".join(language for language in _unique(request.languages.languages)
                     if language in wanted)


def _undetermined_languages(request: GateRequest) -> list[str]:
    by_language: dict[str, list[Candidate]] = {}
    for found in request.candidates:
        by_language.setdefault(found.language, []).append(found)
    return [language for language in _unique(request.languages.languages)
            if any(not found.version_known for found in by_language.get(language, ()))
            or len({(found.image, found.tag) for found in by_language.get(language, ())}) > 1]


def _owed_detail(request: GateRequest, refused: Refused) -> str:
    """What the defaults could not settle, with its subjects in resolved-language order."""
    case = refused.case
    if case in (RefusalCase.OTHER_PLATFORM, RefusalCase.MIXED_PLATFORMS):
        kind = ("a platform other than macOS or Linux" if case is RefusalCase.OTHER_PLATFORM
                else "both macOS and Linux")
        return (f"the product's CI runs on {kind}, its platforms are "
                f"{', '.join(refused.platforms)}, {NO_OVERRIDE}")
    if case is RefusalCase.CONFLICTING_IMAGES:
        languages = _languages_in_order(request, (language for _image, _tag, language
                                                  in refused.candidate_images))
        return ("the product's CI runs on Linux, the languages "
                f"{languages} call for more than one container image, {NO_OVERRIDE}")
    if case is RefusalCase.UNDETERMINED_VERSION:
        return ("the product's CI runs on Linux, the container version cannot be determined for "
                f"{', '.join(_undetermined_languages(request))}, {NO_OVERRIDE}")
    ordered = _languages_in_order(request, refused.languages_without_default)
    return refusal_case_text(replace(
        refused, languages_without_default=tuple(ordered.split(", ")) if ordered else ()))


def _resolved_detail(resolved: Resolved) -> str:
    if resolved.kind is EnvironmentKind.MACOS_GUEST:
        return GUEST_DETAIL
    if resolved.kind is EnvironmentKind.CONTAINER:
        return (f"container: the product's gates run in {resolved.image}:{resolved.tag}, "
                f"{resolved.architecture.value}")
    return OWNERS_MAC_DETAIL[resolved.owners_mac_cause]


def _classify(request: GateRequest, outcome: Resolved | Refused) -> tuple[CheckAnswer, str]:
    """The shared resolver's outcome as one of the three answers; no second decision tree."""
    if isinstance(outcome, Resolved):
        return CheckAnswer.RESOLVES, _resolved_detail(outcome)
    if outcome.case in OWED_CASES and request.override is None:
        return CheckAnswer.OWES_DECISION, _owed_detail(request, outcome)
    return CheckAnswer.DOES_NOT_RESOLVE, refusal_case_text(
        outcome, failed_override_source=_failed_override_source(request, outcome))


def _command_for_ask(files, context: CheckContext, *, worktree: str, project: str,
                     key: str) -> str:
    """The card's test command, once the context is known to be for this ask: the one place the
    check and the `record` command hold the prepared context to the card."""
    _validate_context(context, worktree=worktree, project=project, key=key)
    card = files.read_text(Path(worktree) / PROJECT_CARD / project / "project.md")
    command = read_card_command(card) if card is not None else None
    if command is None:
        raise GateError(f"project {project} has no readable `Test command:` on its card in "
                        f"{worktree}")
    named = _card_product_path(card)
    given = str(context.paths["product_path"])
    if named is not None and named != given:
        raise GateError(f"the paths file {context.paths_file} gives the product path {given}, "
                        f"but the project card names {named}")
    return command


def check_gate(*, worktree: str, project: str, key: str, inputs: object, context: CheckContext,
               files, core_root: Path, out: TextIO) -> CheckResult:
    """What `run` would decide for the same evidence without the owner's ask, as one line on
    `out`. Starts no process and writes no file: it holds `files` to read, and the path contract
    and tracked list arrive in `context`."""
    command = _command_for_ask(files, context, worktree=worktree, project=project, key=key)
    if command.strip().lower() == "none":
        answer, detail = CheckAnswer.RESOLVES, NO_SUITE_DETAIL
    else:
        if not isinstance(inputs, dict):
            raise InputError("input must be an object")
        paths = context.paths
        request = parse_request(
            inputs, files=_SnapshotFiles(files, context.tracked_files),
            product_checkout=Path(paths["product_worktree"]), language_root=product_tree(paths),
            core_root=core_root, project=project, record=context.decision_record)
        answer, detail = _classify(request, resolve_environment(request, owners_ask=False))
    _declare(out, f"{answer.value} {DASH} {detail}")
    return CheckResult(answer, detail, 0 if answer is CheckAnswer.RESOLVES else REFUSAL_STATUS)


# --- the wiring: the only place a real collaborator is built --------------------------------------


class ReadOnlyFiles:
    """The files the check holds: it can read a file and do nothing else with one."""

    def read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None


class _RealFiles(ReadOnlyFiles):

    def tracked_files(self, root: Path) -> list[str]:
        listed = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True,
                                text=True)
        return listed.stdout.splitlines() if listed.returncode == 0 else []

    def linked_git_dirs(self, root: Path) -> tuple[Path, Path] | None:
        """The git dir and the shared git dir a checkout's `.git` pointer file leads to; `None`
        when `.git` is a folder (it is copied with the checkout) or there is none."""
        if not (root / ".git").is_file():
            return None
        found = subprocess.run(["git", "-C", str(root), "rev-parse", "--path-format=absolute",
                                "--git-dir", "--git-common-dir"], capture_output=True, text=True)
        lines = found.stdout.splitlines()
        if found.returncode != 0 or len(lines) != 2:
            return None
        return Path(lines[0]), Path(lines[1])

    def write_text(self, path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    def remove(self, path: Path) -> None:
        path.unlink(missing_ok=True)


class _RealProcesses:
    def probe(self, argv: list[str]) -> Completed:
        try:
            done = subprocess.run(argv, capture_output=True, text=True)
        except FileNotFoundError:
            raise ExecutableMissing(argv[0]) from None
        return Completed(done.returncode, done.stdout, done.stderr)

    def issue(self, argv: list[str], *, cwd: str) -> Completed:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        return Completed(done.returncode, done.stdout, done.stderr)

    def pipe(self, producer: list[str], consumer: list[str], *, cwd: str) -> Completed:
        """`producer`'s standard output fed to `consumer`'s standard input. The status is the
        producer's when it failed, else the consumer's; standard error is both, in that order.
        The producer's standard error goes to a file, so a chatty producer cannot stall."""
        with tempfile.TemporaryFile() as producer_err:
            try:
                first = subprocess.Popen(producer, cwd=cwd, stdout=subprocess.PIPE,
                                         stderr=producer_err)
            except FileNotFoundError:
                raise ExecutableMissing(producer[0]) from None
            try:
                second = subprocess.Popen(consumer, cwd=cwd, stdin=first.stdout,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                first.kill()
                first.wait()
                raise ExecutableMissing(consumer[0]) from None
            finally:
                first.stdout.close()
            out, consumer_err = second.communicate()
            first.wait()
            producer_err.seek(0)
            produced = producer_err.read()
            # bsdtar ends a message with no newline; each program's text keeps its own lines.
            if produced and not produced.endswith(b"\n"):
                produced += b"\n"
            errors = produced + consumer_err
        status = first.returncode or second.returncode
        return Completed(status, out.decode(errors="replace"), errors.decode(errors="replace"))


def _real_contract(worktree: str, project: str, key: str) -> dict:
    import development_path

    try:
        return dict(development_path.resolve_from_paths(
            worktree, project, key, development_path.GitRepos(development_path.Git())))
    except development_path.ToolError as error:
        raise ContractError(f"{error.code}: {error.message}") from error


# One file for the whole host, so a satellite on its own pinned copy of core and this instance
# contend on the same lock. Nothing about the repository, the pin, the guest's name or the
# temporary-directory setting is in it.
GUEST_LOCK_PATH = "/tmp/kensaiapp-macos-guest.lock"


class FileGuestLock:
    """The host-wide lock one guest run holds, as an exclusive `flock` on a file. The lock belongs
    to the open descriptor, so the operating system drops it when the process ends however it
    ends. The file is never unlinked: waiters must all open the same inode."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @contextlib.contextmanager
    def hold(self) -> Iterator[None]:
        try:
            # os.open makes the descriptor non-inheritable, so no command a run launches holds it.
            descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as error:
            raise self._cannot_be_taken(error) from error
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
            except OSError as error:
                raise self._cannot_be_taken(error) from error
            yield
        finally:
            os.close(descriptor)

    def _cannot_be_taken(self, error: OSError) -> GateError:
        return GateError(f"the lock that lets one gate at a time run in the macOS guest cannot "
                         f"be taken, at {self.path}: {error.strerror or error}")


def build_host() -> Host:
    core_root = Path(__file__).resolve().parent.parent
    return Host(files=_RealFiles(), contract=_real_contract, processes=_RealProcesses(),
                new_token=lambda: uuid.uuid4().hex, core_root=core_root,
                guest_lock=FileGuestLock(Path(GUEST_LOCK_PATH)), record_reader=GitRecordReader(),
                run_records=default_run_records())


def build_check_host() -> CheckHost:
    return CheckHost(files=ReadOnlyFiles(), core_root=Path(__file__).resolve().parent.parent)


@dataclass(frozen=True)
class RecordHost:
    """The `record` command's collaborators: files it can only read, and the record reader."""

    files: object
    reader: object


def build_record_host() -> RecordHost:
    return RecordHost(files=ReadOnlyFiles(), reader=GitRecordReader())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gate_suite", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser(
        "run", help="issue the card's test command in the resolved environment")
    run.add_argument("--worktree", required=True, help="the instance change worktree (absolute)")
    run.add_argument("--project", required=True)
    run.add_argument("--key", required=True)
    run.add_argument("--gate", required=True, choices=[gate.value for gate in Gate])
    run.add_argument("--inputs", help="the sourced-input JSON; may be omitted for an owner's ask "
                                      "or a no-suite path")
    run.add_argument("--owners-mac", action="store_true",
                     help="the owner's ask to run the command on the owner's Mac")
    check = commands.add_parser(
        "check", help="answer whether the sourced inputs resolve an environment, starting nothing")
    check.add_argument("--worktree", required=True,
                       help="the instance change worktree (absolute)")
    check.add_argument("--project", required=True)
    check.add_argument("--key", required=True)
    check.add_argument("--inputs", required=True, help="the sourced-input JSON")
    check.add_argument("--paths", required=True,
                       help="the path tool's contract for the change, as a JSON file")
    check.add_argument("--tracked-files", required=True,
                       help="the product's tracked files, one product-relative path per line")
    check.add_argument("--decision-record",
                       help="the record command's output, made just before this check, as a JSON "
                            "file (without it, the check takes the decision only from the "
                            "sourced inputs)")
    record = commands.add_parser(
        "record", help="print the product's docs/nfdr.md as its main branch holds it, or that "
                       "main holds none, as JSON for check --decision-record")
    record.add_argument("--worktree", required=True,
                        help="the instance change worktree (absolute)")
    record.add_argument("--project", required=True)
    record.add_argument("--key", required=True)
    record.add_argument("--paths", required=True,
                        help="the path tool's contract for the change, as a JSON file")
    return parser


def _read_json(files, path: str, what: str) -> object:
    text = files.read_text(Path(path))
    if text is None:
        raise GateError(f"the {what} {path} cannot be read")
    try:
        return json.loads(text)
    except ValueError as error:
        raise GateError(f"the {what} {path} is not JSON: {error}") from error


def _main_check(args: argparse.Namespace, host: CheckHost, out: TextIO) -> int:
    inputs = _read_json(host.files, args.inputs, "inputs file")
    paths = _read_json(host.files, args.paths, "paths file")
    listed = host.files.read_text(Path(args.tracked_files))
    if listed is None:
        raise GateError(f"the tracked-files list {args.tracked_files} cannot be read")
    prepared = load_decision_record(host.files, args.decision_record) \
        if args.decision_record else None
    context = CheckContext(paths=paths, tracked_files=tuple(
        name for name in listed.splitlines() if name), paths_file=args.paths,
        decision_record=prepared, decision_record_file=args.decision_record or "decision-record")
    return check_gate(worktree=args.worktree, project=args.project, key=args.key, inputs=inputs,
                      context=context, files=host.files, core_root=host.core_root, out=out).status


def load_decision_record(files, path: str) -> DecisionRecord:
    """The `record` command's output, read back for a check: every field present and of the shape
    the command writes. Whether it is for this ask is the check's to say."""
    found = _read_json(files, path, "decision-record file")
    where = f"the decision-record file {path}"
    if not isinstance(found, dict):
        raise GateError(f"{where} is not the record command's output")
    for name in RECORD_FIELDS:
        if name not in found:
            raise GateError(f"{where} has no {name}")
    repository, file, revision, text = (found[name] for name in RECORD_FIELDS)
    wellformed = (isinstance(repository, str) and bool(repository)
                  and isinstance(file, str) and bool(file)
                  and (revision is None or (isinstance(revision, str) and bool(revision)))
                  and (text is None or (isinstance(text, str) and revision is not None)))
    if not wellformed:
        raise GateError(f"{where} is not the record command's output")
    return DecisionRecord(repository, file, revision, text)


def _main_record(args: argparse.Namespace, host: RecordHost, out: TextIO) -> int:
    paths = _read_json(host.files, args.paths, "paths file")
    _command_for_ask(host.files, CheckContext(paths=paths, tracked_files=(), paths_file=args.paths),
                     worktree=args.worktree, project=args.project, key=args.key)
    record = read_decision_record(paths, host.reader)
    out.write(json.dumps(record.as_json()) + "\n")
    return 0


def _main_run(args: argparse.Namespace, host: Host, out: TextIO, err: TextIO) -> int:
    """`run` through its CLI: the gate's own output and status, and the record of them kept once
    the status is known — also for a handled error, once the checkout is."""
    recording = _RunRecording(out, err)
    try:
        raw = _read_json(host.files, args.inputs, "inputs file") if args.inputs else None
        status = run_gate(gate=args.gate, worktree=args.worktree, project=args.project,
                          key=args.key, inputs=raw, owners_ask=args.owners_mac,
                          host=recording.watching(host), out=recording.out,
                          err=recording.err).status
    except (GateError, InputError) as error:
        recording.err.write(f"gate_suite: {error}\n")
        status = ERROR_STATUS
    recording.publish(host.run_records, args.key, status)
    return status


def main(argv: Sequence[str] | None = None, *, host: Host | None = None,
         check_host: CheckHost | None = None, stdout: TextIO | None = None,
         stderr: TextIO | None = None, host_factory: Callable[[], Host] = build_host,
         record_host: RecordHost | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    try:
        if args.command == "check":
            return _main_check(args, check_host if check_host is not None
                               else build_check_host(), out)
        if args.command == "record":
            return _main_record(args, record_host if record_host is not None
                                else build_record_host(), out)
        return _main_run(args, host if host is not None else host_factory(), out, err)
    except (GateError, InputError) as error:
        err.write(f"gate_suite: {error}\n")
        return ERROR_STATUS


if __name__ == "__main__":
    sys.exit(main())
