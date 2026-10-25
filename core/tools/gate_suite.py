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
    decision files choose it, or the owner asked. The ask is `--owners-mac`, or
    `OWNERS_MAC_VARIABLE` set to exactly `1` in the environment the host was given — a managed
    walk's launch context — so a run that misses the recipe's ask still lands where the owner asked.

    In the macOS guest the share is how the run proves the guest reaches its checkout, never what
    it builds from: the suite runs in a copy streamed from the host onto the guest's own disk
    (`_copy_to_guest_disk`).
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import TextIO

__version__ = "1.13.0"

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
    tag_source: Source | None = None


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
    """What a language's packet names for the macOS guest: the tool its gates run with, the
    folder that holds it when the guest's own PATH does not (`None`), and the further folders a
    cell of a mixed gate may find the tool at a version of its own in (`version_folders`)."""

    language: str
    tool: str
    folder: str | None
    version_folders: tuple[str, ...] = ()


class InstallNone(Enum):
    """A packet's install line that says `none`: the language needs no install there. Distinct
    from `None`, a packet that states no install at all."""

    NONE = "none"


NO_INSTALL = InstallNone.NONE


@dataclass(frozen=True)
class LanguageInstall:
    """What a language's packet states it installs before the suite, for a container and for the
    macOS guest. Each side is one shell command, `NO_INSTALL` (the packet says `none`), or `None`
    (the packet states no install for that kind of environment)."""

    language: str
    container: str | InstallNone | None
    guest: str | InstallNone | None


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
    installs: tuple[LanguageInstall, ...] = ()


@dataclass(frozen=True)
class Resolved:
    kind: EnvironmentKind
    image: str | None
    tag: str | None
    architecture: Architecture | None
    owners_mac_cause: OwnersMacCause | None
    # The CI lines that state this container's version, every one validated. Provenance only: two
    # containers are the same container whatever lines state them, so it takes no part in equality.
    sources: tuple[Source, ...] = field(default=(), compare=False)
    # The version the product's CI states for a macOS guest cell of a mixed CI, exactly as stated.
    # `None` for every other environment, a one-guest environment included.
    ci_version: str | None = None


@dataclass(frozen=True)
class ResolvedMatrix:
    """Two or more cells, in run order: a container for each version the product's Linux CI states
    for its languages and, on a CI that runs on both macOS and Linux, one macOS guest cell at the
    newest of those versions. The containers keep the order each version first appears among the
    candidates; the platforms keep the order the CI's runners first name them."""

    targets: tuple[Resolved, ...]

    def __post_init__(self) -> None:
        if len(self.targets) < 2:
            raise ValueError("a matrix holds two or more cells; one environment is a Resolved")


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
_VERSIONED_FOLDERS = re.compile(r"^\*\*Versioned Python folders:\*\*(.*)$")
_VERSIONED_LANGUAGE = "python"


def guest_tool(language: str, packet_text: str | None) -> GuestTool | None:
    """The tool a packet's `## In the macOS guest` table names, or `None` when the packet has no
    such table — a language with no guest default. The table is that section's and no other's.
    The Python packet's section may also hold a `**Versioned Python folders:**` line of absolute
    folders in backticks; they are data, and no other language's section is read for one."""
    in_section = False
    row = None
    folders: tuple[str, ...] = ()
    for line in (packet_text or "").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == GUEST_SECTION
            continue
        if not in_section:
            continue
        found = _GUEST_ROW.match(line.strip())
        if found and row is None:
            row = found
        listed = _VERSIONED_FOLDERS.match(line.strip())
        if listed and language == _VERSIONED_LANGUAGE:
            folders = tuple(folder for folder in re.findall(r"`([^`]+)`", listed.group(1))
                            if folder.startswith("/"))
    if row is None:
        return None
    return GuestTool(language, row.group(1), row.group(2), folders)


PROVISIONING_SECTION = "## Provisioning"
_INSTALL_LINE = re.compile(r"^\*\*(Container|Guest) install:\*\*(.*)$")
_INSTALL_COMMAND = re.compile(r"^`([^`]+)`$")
_INSTALL_SECTION = {"Container": PROVISIONING_SECTION, "Guest": GUEST_SECTION}


def _install_value(text: str) -> str | InstallNone | None:
    value = text.strip()
    if value == InstallNone.NONE.value:
        return NO_INSTALL
    found = _INSTALL_COMMAND.match(value)
    if found and found.group(1).strip():
        return found.group(1).strip()
    return None


def language_install(language: str, packet_text: str | None) -> LanguageInstall:
    """The install lines a packet states: `**Container install:**` only under `## Provisioning`,
    `**Guest install:**` only under `## In the macOS guest` (CP-833). The value is one command in
    one pair of backticks or the bare word `none`; any other value, a line in another section, or
    no line states no install, which is `None`."""
    sides: dict[str, str | InstallNone | None] = {"Container": None, "Guest": None}
    seen: set[str] = set()
    section = ""
    for line in (packet_text or "").splitlines():
        if line.startswith("## "):
            section = line.strip()
            continue
        found = _INSTALL_LINE.match(line.strip())
        if not found or _INSTALL_SECTION[found.group(1)] != section or found.group(1) in seen:
            continue
        seen.add(found.group(1))
        sides[found.group(1)] = _install_value(found.group(2))
    return LanguageInstall(language, sides["Container"], sides["Guest"])


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
    return Candidate(language, image, tag, version_known, failed, tag_source)


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
    packets = {language: files.read_text(core_root / PACKET_ROOT / language / "environment.md")
               for language in languages.languages}
    named = (guest_tool(language, text) for language, text in packets.items())
    return GateRequest(
        project=project, languages=languages, ci=_ci_finding(raw.get("ci"), checker),
        override=override,
        amd64=_amd64(decisions.get("amd64"), checker),
        candidates=tuple(_candidate(item, checker) for item in raw.get("candidates") or []),
        guest=Guest(guest["name"], _shares(guest.get("shares"))) if guest.get("name") else None,
        guest_tools=tuple(tool for tool in named if tool is not None),
        conflicting_decisions=isinstance(current, RecordConflict),
        installs=tuple(language_install(language, text) for language, text in packets.items()))


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


def _resolve_linux(request: GateRequest) -> Resolved | ResolvedMatrix | Refused:
    """CP-767 to CP-769: one container for each version the candidates state, when the candidates
    name one image and every resolved language is given the same set of versions. Every
    candidate's evidence is validated before any two are called one container."""
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
    version_sets = {language: {(candidate.image, candidate.tag) for candidate in
                               by_language[language]} for language in languages}
    if len({candidate.image for candidate in chosen}) > 1 \
            or len({frozenset(found) for found in version_sets.values()}) > 1:
        return _refuse(request, RefusalCase.CONFLICTING_IMAGES, candidate_images=tuple(
            (candidate.image, candidate.tag, candidate.language) for candidate in chosen))
    # Sets decide membership; the output order is the original candidates' first occurrences.
    resolved_languages = set(languages)
    supporting: dict[tuple[str, str], list[Source]] = {}
    for candidate in request.candidates:
        if candidate.language in resolved_languages:
            supporting.setdefault((candidate.image, candidate.tag), []).append(
                candidate.tag_source)
    targets = []
    for (image, tag), sources in supporting.items():
        target = _container(request, image, tag, None)
        if isinstance(target, Refused):
            return target
        targets.append(replace(target, sources=_unique(sources)))
    return targets[0] if len(targets) == 1 else ResolvedMatrix(tuple(targets))


def _resolve_mixed(request: GateRequest,
                   platforms: tuple[str, ...]) -> ResolvedMatrix | Refused:
    """CP-788: the Linux side is decided as a Linux-only CI is, its refusals standing for the whole
    gate; then every language's guest tool must be named. The guest runs once, at the newest
    version the Linux cells give, because its suites run one at a time; the platforms keep the
    order the runners first name them."""
    linux = _resolve_linux(request)
    if isinstance(linux, Refused):
        return linux
    guest = _resolve_guest(request)
    if isinstance(guest, Refused):
        return guest
    containers = cells_of(linux)
    newest = max(containers, key=lambda cell: _version_key(cell.tag))
    guests = (replace(guest, ci_version=newest.tag, sources=newest.sources),)
    return ResolvedMatrix(tuple(cell for platform in platforms
                                for cell in (containers if platform == PLATFORM_LINUX else guests)))


def _version_key(tag: str | None) -> tuple[int, ...]:
    """A version tag's numbers, in order, so `3.9` sorts below `3.14`."""
    return tuple(int(number) for number in re.findall(r"\d+", tag or ""))


def cells_of(outcome: Resolved | ResolvedMatrix | Refused) -> tuple[Resolved, ...]:
    """The environments an outcome runs, in order: one for a single environment, every cell of a
    matrix, none for a refusal. How execution and the check read either success shape."""
    if isinstance(outcome, ResolvedMatrix):
        return outcome.targets
    return (outcome,) if isinstance(outcome, Resolved) else ()


def resolve_environment(request: GateRequest, *,
                        owners_ask: bool) -> Resolved | ResolvedMatrix | Refused:
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
        return _resolve_mixed(request, platforms)
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
# Where a matrix run keeps each container's private copy of the checkout, on the host.
CELL_PREFIX = "kensaiapp-gate-suite-cell-"
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
_CARD_DEPENDENCIES = re.compile(r"^\s*\**Dependencies command:\**\s*(.*)$")
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
    `guest_lock.hold()` is the blocking, exclusive context one guest run lives in, taken once for a
    one-guest run and once for each macOS cell of a matrix;
    `record_reader` reads the product's committed decision (`read_decision_record`) — a host with
    none resolves from the sourced inputs alone; `run_records` keeps what a completed `run` printed
    (`FileRunRecords`) — a host with none records nothing, which is what keeps every existing
    `Host` construction and every direct `run_gate` call as it was; `workspaces.checkout(source)`
    is the context one container cell of a matrix runs in — a private copy of the checkout at
    `source`, its path given on entry and the copy removed on exit (`CheckoutCopies`) — a host with
    none cannot run a matrix. A macOS cell takes no workspace: its copy is streamed onto the
    guest's own disk. `environ` is the environment `run` reads the launch context's ask from
    (`OWNERS_MAC_VARIABLE`) — a host given none has no ask there, whatever the process holds."""

    files: object
    contract: Callable[[str, str, str], dict]
    processes: object
    new_token: Callable[[], str]
    core_root: Path
    guest_lock: object
    record_reader: object | None = None
    run_records: object | None = None
    workspaces: object | None = None
    environ: Mapping[str, str] = field(default_factory=dict)


# The owner's ask carried by a managed walk's launch context: set to exactly `1` for the steps
# that run a card's suite (`chain_development.py`). Any other value, and an unset one, is no ask.
OWNERS_MAC_VARIABLE = "KENSAIAPP_GATE_OWNERS_MAC"


def launch_context_asks(environ: Mapping[str, str]) -> bool:
    return environ.get(OWNERS_MAC_VARIABLE) == "1"


class NotReadyCause(str, Enum):
    """The four reasons an environment is not ready (CP-837); none of them is a failing suite."""

    NO_INSTALL = "no-install"
    INSTALL_FAILED = "install-failed"
    DEPENDENCIES_FAILED = "dependencies-failed"
    TEST_TOOL_NOT_FOUND = "test-tool-not-found"


@dataclass(frozen=True)
class NotReady:
    """An environment that was not ready: the cause, the kind of environment, and the language
    the two install causes name (`None` for the other two)."""

    cause: NotReadyCause
    kind: EnvironmentKind
    language: str | None = None


@dataclass(frozen=True)
class CellResult:
    """One cell of a matrix, a container or a versioned macOS guest: where it ran (`line` is its
    declaration) and what its run returned. A macOS cell's `stdout` and `stderr` include its
    diagnostics, kept whole for the replay."""

    target: Resolved
    line: str
    status: int
    stdout: str
    stderr: str
    not_ready: NotReady | None = None


@dataclass(frozen=True)
class GateResult:
    """What the run did: the line it printed first, the command and directory it was given, the
    exit status it ends with, whatever the suite wrote, and whether a suite was issued at all.
    A matrix run names every line it declared (`environment_lines`) and each cell's result
    (`cells`, container or macOS guest), in cell order, with `environment_line` the first
    declaration; a single run's
    `environment_lines` is its one line and its `cells` are none."""

    environment_line: str
    command: str
    cwd: str
    status: int
    stdout: str
    stderr: str
    suite_issued: bool
    environment_lines: tuple[str, ...] | None = None
    cells: tuple[CellResult, ...] = ()
    not_ready: NotReady | None = None

    def __post_init__(self) -> None:
        if self.environment_lines is None:
            object.__setattr__(self, "environment_lines", (self.environment_line,))


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


def read_card_dependencies(card_text: str) -> str | None:
    """The card's `Dependencies command:` read the way `Test command:` is (CP-834). `None` for
    `none` in any case, an empty value, or a card with no such line."""
    for line in card_text.splitlines():
        found = _CARD_DEPENDENCIES.match(line)
        if not found:
            continue
        value = _CARD_COMMENT.sub("", found.group(1)).strip()
        if len(value) > 1 and value.startswith("`") and value.endswith("`") \
                and "`" not in value[1:-1]:
            value = value[1:-1].strip()
        return None if not value or value.lower() == "none" else value
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
        line = f"Environment: macos-guest {DASH} {guest.name if guest else 'no guest given'}"
        return line if resolved.ci_version is None else f"{line}, toolchain {resolved.ci_version}"
    return f"Environment: container {DASH} {container_text(resolved)}"


def container_text(resolved: Resolved) -> str:
    """A container as the gate prints it everywhere: `{image}:{tag}, {architecture}`."""
    return f"{resolved.image}:{resolved.tag}, {resolved.architecture.value}"


def refusal_case_text(refused: Refused, *, failed_override_source: Source | None = None) -> str:
    """The text that follows `unresolved — ` on the printed line, and `{case}` in the first line
    of the refusal on standard error. `failed_override_source` is the already checked source of a
    recorded override that did not hold up; only the refusal for that cause is given it."""
    case = refused.case
    if case is RefusalCase.OTHER_PLATFORM:
        return f"the product's CI runs on a platform other than macOS or Linux, {NO_OVERRIDE}"
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


# --- what runs in an environment, and when it was not ready (CP-835 to CP-840) --------------------

# The status a failed install or dependencies command exits the shell with. The stage line, never
# this status, tells it from the test command's own exit.
STAGE_STATUS = 97
_INSTALL_STAGE = "install "
_DEPENDENCIES_STAGE = "dependencies"
_TEST_TOOL_NOT_FOUND_STATUS = 127


def compose_shell(installs: Sequence[tuple[str, str]], dependencies: str | None, command: str,
                  token: str) -> str:
    """The shell an environment issues: one outer group holding each install (a `(language,
    command)` pair, in order) and the dependencies command, then the test command. Each is a brace
    group in the one shell, so an `export` reaches the test command, and one that fails names its
    stage with `token` on standard error and exits the shell. With nothing to add the result is
    `command` exactly."""
    stages = [(f"{_INSTALL_STAGE}{language}", line) for language, line in installs]
    if dependencies:
        stages.append((_DEPENDENCIES_STAGE, dependencies))
    if not stages:
        return command
    groups = "\n".join(
        f"{{ {line}\n}} || {{ echo {shlex.quote(f'{token} {words}')} >&2; exit {STAGE_STATUS}; }}"
        for words, line in stages)
    return f"{{ {groups}\n{command}\n}}"


def _side(kind: EnvironmentKind) -> str:
    return "container" if kind is EnvironmentKind.CONTAINER else "guest"


@dataclass(frozen=True)
class _Stages:
    """What runs before the test command in each environment: every resolved language's stated
    installs and the card's dependencies command."""

    installs: tuple[LanguageInstall, ...] = ()
    dependencies: str | None = None

    def commands(self, kind: EnvironmentKind) -> list[tuple[str, str]]:
        """The installs for `kind`, in language order, each distinct command once."""
        found: list[tuple[str, str]] = []
        for item in self.installs:
            value = getattr(item, _side(kind))
            if isinstance(value, str) and all(value != command for _, command in found):
                found.append((item.language, value))
        return found

    def missing(self, kind: EnvironmentKind) -> str | None:
        """The first language whose packet states no install for `kind`."""
        return next((item.language for item in self.installs
                     if getattr(item, _side(kind)) is None), None)

    def shell(self, kind: EnvironmentKind, command: str, token: str) -> str:
        return compose_shell(self.commands(kind), self.dependencies, command, token)


_NO_STAGES = _Stages()


def _stage_of(completed: Completed, token: str) -> str | None:
    """The stage this run's token names on a line of standard error, if it names one."""
    for line in completed.stderr.splitlines():
        words = line.rstrip()
        if words == f"{token} {_DEPENDENCIES_STAGE}" or words.startswith(
                f"{token} {_INSTALL_STAGE}"):
            return words[len(token) + 1:]
    return None


def not_ready_cause(completed: Completed, token: str) -> NotReadyCause | None:
    """Why a completed run was not ready, if it was. The token's stage line decides first;
    otherwise status 127 does (CP-837)."""
    stage = _stage_of(completed, token)
    if stage == _DEPENDENCIES_STAGE:
        return NotReadyCause.DEPENDENCIES_FAILED
    if stage is not None:
        return NotReadyCause.INSTALL_FAILED
    if completed.status == _TEST_TOOL_NOT_FOUND_STATUS:
        return NotReadyCause.TEST_TOOL_NOT_FOUND
    return None


def failing_language(completed: Completed, token: str) -> str | None:
    stage = _stage_of(completed, token)
    if stage is None or not stage.startswith(_INSTALL_STAGE):
        return None
    return stage[len(_INSTALL_STAGE):]


def _without_stage_lines(text: str, token: str) -> str:
    return "".join(line for line in text.splitlines(keepends=True)
                   if not (line.rstrip() == f"{token} {_DEPENDENCIES_STAGE}"
                           or line.startswith(f"{token} {_INSTALL_STAGE}")))


def not_ready_words(not_ready: NotReady) -> str:
    """The cause as the not-ready lines word it."""
    side = _side(not_ready.kind)
    cause = not_ready.cause
    if cause is NotReadyCause.NO_INSTALL:
        return f"the {not_ready.language} packet states no {side} install"
    if cause is NotReadyCause.INSTALL_FAILED:
        return f"the {not_ready.language} {side} install failed"
    if cause is NotReadyCause.DEPENDENCIES_FAILED:
        return "the card's dependencies command failed"
    return ("the test command exited 127, the status the shell gives a command it cannot "
            "find")


def not_ready_line(environment: str, not_ready: NotReady) -> str:
    """The `Environment: not-ready` line for the environment `environment` declared: the text
    after `{DASH} ` on its own line, then the cause."""
    detail = environment.partition(f" {DASH} ")[2]
    return f"Environment: not-ready {DASH} {detail} {DASH} {not_ready_words(not_ready)}"


def _guest_where(guest: Guest | None, version: str | None) -> str:
    text = f"the macOS guest {guest.name if guest else 'no guest given'}"
    return text if version is None else f"{text}, toolchain {version}"


def _where(target: Resolved, guest: Guest | None) -> str:
    if target.kind is EnvironmentKind.MACOS_GUEST:
        return _guest_where(guest, target.ci_version)
    return container_text(target)


def _not_ready_report(where: str, not_ready: NotReady) -> str:
    return (f"gate_suite: the environment was not ready for the suite in {where}, because "
            f"{not_ready_words(not_ready)}.")


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


def _where_looked(tool: GuestTool) -> str:
    """Where a refusal says the guest was searched for `tool`."""
    searched = f"in {tool.folder} or on the guest's PATH" if tool.folder else (
        "on the guest's PATH")
    if not tool.version_folders:
        return searched
    own = f"in {tool.folder}, " if tool.folder else ""
    return (f"{own}on the guest's PATH or in any of these folders: "
            f"{', '.join(tool.version_folders)}")


def _check_guest_tools(host: Host, guest: Guest, tools: Sequence[GuestTool], *,
                       by_version: bool = False) -> None:
    """Each language's tool, looked for in the guest as the suite will look for it — so a guest
    built without a toolchain stops the run here, before a suite whose `command not found` would
    read as a failing test. A tool whose cells are found by version (`by_version`, for a tool with
    `version_folders`) is looked for by `_check_guest_versions` alone, since the guest's own PATH
    need not hold any of the Pythons a cell can use."""
    for tool in tools:
        if by_version and tool.version_folders:
            continue
        found = _probe(host, ["tart", "exec", guest.name, "sh", "-c",
                              _on_path((tool,), f"command -v {shlex.quote(tool.tool)}")],
                       "gate_suite: tart was not found on PATH, so the macOS guest cannot be "
                       "reached.")
        if found.status != 0:
            raise _NotReady(f"gate_suite: the macOS guest {guest.name} has no {tool.tool}, the "
                            f"tool {tool.language}'s gates run with, {_where_looked(tool)}.",
                            _last_stderr_line(found))


_VERSION_IN_REPORT = re.compile(r"(?<![\w.])v?(\d+(?:\.\d+)*)")


def _reported_parts(report: Completed) -> tuple[str, ...] | None:
    """The dot-separated parts of the version a tool's `--version` gives: the first number in the
    first line it wrote, a labelled (`Python 3.12.4`) or `v`-prefixed (`v22.3.0`) report alike.
    `None` for a tool that answered with an error, or gave no version. A number written further
    along the line (a build, a header) is never the tool's version."""
    if report.status != 0:
        return None
    for text in (report.stdout, report.stderr):
        lines = [line for line in text.splitlines() if line.strip()]
        found = _VERSION_IN_REPORT.search(lines[0]) if lines else None
        if found:
            return tuple(found.group(1).split("."))
    return None


def _reports_version(report: Completed, version: str) -> bool:
    """CP-794: the tool reports `version` when its parts, as text, begin with every part of it."""
    parts = _reported_parts(report)
    required = tuple(version.split("."))
    return parts is not None and parts[:len(required)] == required


def _lookups(tool: GuestTool) -> list[GuestTool]:
    """The descriptors a version is looked for with, in the order tried: the guest's own lookup,
    then each of the packet's further folders. A folder is run by its own location, so an absent
    one cannot be answered for by a tool further along the guest's PATH."""
    ordinary = replace(tool, version_folders=())
    return [ordinary, *(replace(tool, folder=folder, version_folders=())
                        for folder in tool.version_folders)]


def _version_probe(guest: Guest, tool: GuestTool, ordinary: bool) -> list[str]:
    if ordinary:
        command = _on_path((tool,), f"{shlex.quote(tool.tool)} --version")
    else:
        located = shlex.quote(f"{tool.folder}/{tool.tool}")
        command = f"test -x {located} && {located} --version"
    return ["tart", "exec", guest.name, "sh", "-c", command]


def _check_guest_versions(host: Host, guest: Guest, tools: Sequence[GuestTool],
                          versions: Sequence[str]) -> dict[str, tuple[GuestTool, ...]]:
    """Every macOS cell's version, in cell order: each tool reports it, the tool looked for as the
    suite will look for it. Each location is asked once. Nothing is installed or switched: a tool
    at another version, with no version, or that does not answer is a refusal naming the version.

    Returns, for each requested version, the descriptor of each tool that reported it: the tool
    itself, or — for a tool with `version_folders` — the lookup whose own report matched, which the
    cell's suite is then given."""
    reports: dict[tuple[str, str | None, bool], Completed] = {}
    chosen: dict[str, tuple[GuestTool, ...]] = {}
    for version in versions:
        selected = []
        for tool in tools:
            lookups = _lookups(tool)
            matched = None
            for position, lookup in enumerate(lookups):
                key = (lookup.tool, lookup.folder, position == 0)
                if key not in reports:
                    reports[key] = _probe(
                        host, _version_probe(guest, lookup, position == 0),
                        "gate_suite: tart was not found on PATH, so the macOS guest cannot be "
                        "reached.")
                if _reports_version(reports[key], version):
                    matched = lookup
                    break
            if matched is None:
                first = reports[(tool.tool, tool.folder, True)]
                raise _NotReady(f"gate_suite: the macOS guest {guest.name} has no {tool.tool} at "
                                f"version {version}, the version the product's CI states for "
                                f"{tool.language}, {_where_looked(tool)}.",
                                _last_stderr_line(first) if first.status != 0 else None)
            selected.append(matched)
        chosen[version] = tuple(selected)
    return chosen


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
    """One `Environment:` line, printed first. A stream that keeps declarations apart from the rest
    of what it forwards (`_Forwarding.declare`) is handed the line as a declaration; a plain
    stream is just written to."""
    declare = getattr(out, "declare", None)
    if declare is not None:
        declare(line)
    else:
        out.write(line + "\n")
    out.flush()


def _fail(err: TextIO, lines: list[str]) -> None:
    err.write("".join(line + "\n" for line in lines))
    err.flush()


def _stopped(*, line: str, command: str, cwd: str, status: int = REFUSAL_STATUS,
             lines: tuple[str, ...] | None = None) -> GateResult:
    return GateResult(line, command, cwd, status, "", "", False, lines)


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


def _not_issued(line: str, command: str, cwd: str, out: TextIO, err: TextIO,
                not_ready: NotReady, where: str, *, single: bool) -> GateResult:
    """An environment whose packet states no install: nothing is issued. A single run declares it
    and says so on standard error; a matrix cell is declared later, by the replay."""
    if not single:
        return GateResult(line, command, cwd, REFUSAL_STATUS, "", "", False, not_ready=not_ready)
    declared = not_ready_line(line, not_ready)
    _declare(out, declared)
    report = f"{_not_ready_report(where, not_ready)}\n{CLOSING_LINE}\n"
    err.write(report)
    err.flush()
    return GateResult(line, command, cwd, REFUSAL_STATUS, "", report, False, (line, declared),
                      not_ready=not_ready)


def _issue_in(host: Host, argv: list[str], cwd: str, line: str, command: str, out: TextIO,
              err: TextIO, *, token: str, kind: EnvironmentKind, where: str,
              single: bool) -> GateResult:
    """`_issue`, reading the completed run for a not-ready environment by `token`. A single run
    declares it before any output and ends standard error with its reason; a matrix cell keeps
    its output and leaves the declaring to the replay."""
    completed = host.processes.issue(argv, cwd=cwd)
    cause = not_ready_cause(completed, token)
    if cause is None:
        out.write(completed.stdout)
        err.write(completed.stderr)
        out.flush()
        err.flush()
        return GateResult(line, command, cwd, completed.status, completed.stdout,
                          completed.stderr, True)
    language = failing_language(completed, token)
    not_ready = NotReady(cause, kind, language)
    shown = _without_stage_lines(completed.stderr, token)
    suite_ran = cause is NotReadyCause.TEST_TOOL_NOT_FOUND
    stdout, stderr = (completed.stdout, shown) if suite_ran or not single else (
        "", completed.stdout + shown)
    lines = None
    if single:
        declared = not_ready_line(line, not_ready)
        _declare(out, declared)
        lines = (line, declared)
    out.write(stdout)
    err.write(stderr)
    if single:
        report = f"{_not_ready_report(where, not_ready)}\n" + ("" if suite_ran
                                                                else f"{CLOSING_LINE}\n")
        stderr += report
        err.write(report)
    out.flush()
    err.flush()
    return GateResult(line, command, cwd, REFUSAL_STATUS, stdout, stderr, True, lines,
                      not_ready=not_ready)


def _guest_cell(host: Host, guest: Guest, folder: str, command: str, cwd: str, line: str,
                out: TextIO, err: TextIO, tools: Sequence[GuestTool] = (), *,
                versions: Sequence[str] = (), barrier: Callable[[], None] | None = None,
                version: str | None = None,
                selected: dict[str, tuple[GuestTool, ...]] | None = None,
                stages: _Stages = _NO_STAGES, single: bool = False,
                token: str | None = None) -> GateResult:
    """One guest run's body, from before its first guest process to after its token and its
    guest-local copy are removed. The caller holds the host-wide lock (CP-641): another guest run
    waits until it has left. The suite runs in a copy of the checkout on the guest's own disk
    (`_copy_to_guest_disk`).

    A matrix's first cell is also the gate's preflight: it checks `versions`, every macOS cell's,
    and calls `barrier` once everything has passed. A check that fails before `barrier` is the
    whole gate's failure and is raised; one that fails after it is this cell's alone, said on
    `err` as a one-guest run says it.

    `selected` is the gate invocation's own map from a cell version to the tools that reported it.
    The preflight fills it; every cell, the first included, issues its suite with the tools its
    `version` maps to, so the interpreter that passed the check is the one the suite runs with."""
    selected = {} if selected is None else selected
    token = host.new_token() if token is None else token
    token_name = f"{TOKEN_PREFIX}{token}"
    token_path = Path(cwd) / token_name
    scratch = f"{GUEST_SCRATCH_PREFIX}{token}"
    copied = False
    preflighting = barrier is not None
    try:
        _check_guest_before_share(host, guest)
        host.files.write_text(token_path, token_name)
        _check_guest_share(host, guest, cwd, folder, token_name)
        _check_guest_tools(host, guest, selected.get(version, tools), by_version=bool(versions))
        selected.update(_check_guest_versions(host, guest, tools, versions))
        if barrier is not None:
            preflighting = False
            barrier()
        where = _guest_where(guest, version)
        missing = stages.missing(EnvironmentKind.MACOS_GUEST)
        if missing is not None:
            return _not_issued(line, command, cwd, out, err,
                               NotReady(NotReadyCause.NO_INSTALL, EnvironmentKind.MACOS_GUEST,
                                        missing), where, single=single)
        copied = True
        _copy_to_guest_disk(host, guest, cwd, scratch)
        shell = stages.shell(EnvironmentKind.MACOS_GUEST, command, token)
        return _issue_in(host, guest_argv(guest, shell, scratch, selected.get(version, tools)),
                         cwd, line, command, out, err, token=token,
                         kind=EnvironmentKind.MACOS_GUEST, where=where, single=single)
    except _NotReady as problem:
        if preflighting:
            raise
        _unreachable(err, problem)
        return _stopped(line=line, command=command, cwd=cwd)
    finally:
        try:
            if copied:
                _remove_guest_copy(host, guest, scratch, err)
        finally:
            host.files.remove(token_path)


def _run_in_guest(host: Host, guest: Guest, folder: str, command: str, cwd: str, line: str,
                  out: TextIO, err: TextIO, tools: Sequence[GuestTool] = (), *,
                  stages: _Stages = _NO_STAGES) -> GateResult:
    """A one-guest run: its body inside one hold of the host-wide lock."""
    with host.guest_lock.hold():
        return _guest_cell(host, guest, folder, command, cwd, line, out, err, tools,
                           stages=stages, single=True)


class _CopyFailed(Exception):
    """A container's private copy of the checkout could not be made."""

    def __init__(self, target: Resolved, reason: str) -> None:
        super().__init__(reason)
        self.target = target
        self.reason = reason


class _Cells:
    """The private checkout of each container of a matrix, made in cell order and let go in the
    reverse of it once the run is done with them, however it ended."""

    def __init__(self, host: Host, err: TextIO) -> None:
        self._host, self._err = host, err
        self._held: list[tuple[Resolved, str, contextlib.ExitStack]] = []

    def make(self, targets: Sequence[Resolved], source: str) -> list[str]:
        for target in targets:
            stack = contextlib.ExitStack()
            try:
                path = stack.enter_context(self._host.workspaces.checkout(source))
            except OSError as error:
                raise _CopyFailed(target, error.strerror or str(error)) from error
            self._held.append((target, path, stack))
        return [path for _, path, _ in self._held]

    def release(self) -> None:
        while self._held:
            target, path, stack = self._held.pop()
            try:
                stack.close()
            except OSError:
                _fail(self._err, [f"gate_suite: the private copy of this run's checkout for the "
                                  f"run in {container_text(target)}, at {path}, could not be "
                                  f"removed."])


def _copy_failed(err: TextIO, problem: _CopyFailed) -> None:
    lines = [f"gate_suite: this run's checkout could not be copied to a private folder for the "
             f"run in {container_text(problem.target)}."]
    if problem.reason:
        lines.append(f"The copy reported: {problem.reason}")
    _fail(err, [*lines, CLOSING_LINE])


def _result_line(cell: CellResult, guest: Guest | None = None) -> str:
    where = _where(cell.target, guest)
    if cell.not_ready is not None:
        return f"gate_suite: the run in {where} neither passed nor failed, because the " \
               f"environment was not ready."
    if cell.status == 0:
        return f"gate_suite: the run in {where} passed."
    return f"gate_suite: the run in {where} failed with exit status {cell.status}."


def _guest_cell_result(host: Host, guest: Guest, folder: str, command: str, cwd: str,
                       target: Resolved, line: str, tools: Sequence[GuestTool], *,
                       versions: Sequence[str] = (),
                       barrier: Callable[[], None] | None = None,
                       selected: dict[str, tuple[GuestTool, ...]] | None = None,
                       stages: _Stages = _NO_STAGES, token: str | None = None) -> CellResult:
    """One macOS cell, in a hold of its own. Its streams are kept apart, so the cell's output and
    diagnostics are replayed with the others', in cell order."""
    out, err = io.StringIO(), io.StringIO()
    with host.guest_lock.hold():
        done = _guest_cell(host, guest, folder, command, cwd, line, out, err, tools,
                           versions=versions, barrier=barrier, version=target.ci_version,
                           selected=selected, stages=stages, token=token)
    return CellResult(target, line, done.status, out.getvalue(), err.getvalue(), done.not_ready)


def _container_cell(target: Resolved, line: str, done: Completed, token: str) -> CellResult:
    """One container cell's result: its run as it came back, or a not-ready cell when `token`
    names a failed stage or the test command exited 127."""
    cause = not_ready_cause(done, token)
    if cause is None:
        return CellResult(target, line, done.status, done.stdout, done.stderr)
    return CellResult(target, line, REFUSAL_STATUS, done.stdout,
                      _without_stage_lines(done.stderr, token),
                      NotReady(cause, EnvironmentKind.CONTAINER, failing_language(done, token)))


def _replay(cells: Sequence[CellResult], command: str, cwd: str, lines: tuple[str, ...],
            out: TextIO, err: TextIO, guest: Guest | None = None) -> GateResult:
    """Each cell's complete output in cell order, then one result line per cell, each on a line of
    its own. The run's status is the first failure's in cell order, never in the order the suites
    finished. Before any cell's output, one `Environment: not-ready` line for each cell that was not
    ready, in cell order."""
    declared = tuple(not_ready_line(cell.line, cell.not_ready) for cell in cells
                     if cell.not_ready is not None)
    for line in declared:
        _declare(out, line)
    stdout = "".join(cell.stdout for cell in cells)
    out.write(stdout)
    stderr = "".join(cell.stderr for cell in cells)
    err.write(stderr)
    if stdout and not stdout.endswith("\n"):
        out.write("\n")
    out.write("".join(_result_line(cell, guest) + "\n" for cell in cells))
    out.flush()
    err.flush()
    status = next((cell.status for cell in cells if cell.status != 0), 0)
    return GateResult(lines[0], command, cwd, status, stdout, stderr, True, (*lines, *declared),
                      tuple(cells))


def _run_matrix(host: Host, matrix: ResolvedMatrix, guest: Guest | None, command: str, cwd: str,
                out: TextIO, err: TextIO, tools: Sequence[GuestTool] = (), *,
                stages: _Stages = _NO_STAGES) -> GateResult:
    """A matrix run: every cell's line declared first, then — before any suite — the checks that
    hold for the whole gate and every container's private checkout. The containers' suites are all
    issued at once; the macOS cells run one after another, each in a hold of the guest lock of its
    own, the first hold carrying the gate's checks. Every cell's result is kept by its position, so
    what is replayed is in cell order whatever order the cells finished in."""
    lines = tuple(environment_line(target, guest) for target in matrix.targets)
    for line in lines:
        _declare(out, line)
    if host.workspaces is None:
        raise GateError("a run in several containers needs the host's workspaces, and this host "
                        "has none")
    containers = [(position, target) for position, target in enumerate(matrix.targets)
                  if target.kind is EnvironmentKind.CONTAINER]
    guests = [(position, target) for position, target in enumerate(matrix.targets)
              if target.kind is EnvironmentKind.MACOS_GUEST]
    cells = _Cells(host, err)
    try:
        if containers:
            _check_podman(host)
        folder = None
        if guests:
            if guest is None:
                raise _NotReady("gate_suite: this run was given no macOS guest to run in.")
            folder = map_run_folder(guest.shares, cwd)
            if folder is None:
                _fail(err, unshared_lines(guest, cwd))
                return _stopped(line=lines[0], command=command, cwd=cwd, lines=lines)
        paths = cells.make([target for _, target in containers], cwd)
        results: dict[int, CellResult] = {}
        # Every guest cell's token is drawn before any container's, so the guests hold the tokens
        # a run with no containers would hand them.
        guest_tokens = [host.new_token() for _ in guests]
        missing = stages.missing(EnvironmentKind.CONTAINER)
        issuable = []
        for (position, target), path in zip(containers, paths):
            if missing is not None:
                results[position] = CellResult(
                    target, lines[position], REFUSAL_STATUS, "", "",
                    NotReady(NotReadyCause.NO_INSTALL, EnvironmentKind.CONTAINER, missing))
            else:
                issuable.append((position, target, path, host.new_token()))
        with ThreadPoolExecutor(max_workers=max(1, len(containers))) as pool:
            pending: list[tuple[int, Resolved, object, str]] = []

            def submit() -> None:
                pending.extend(
                    (position, target, pool.submit(
                        host.processes.issue,
                        container_argv(target, stages.shell(EnvironmentKind.CONTAINER, command,
                                                            token), path),
                        cwd=path), token)
                    for position, target, path, token in issuable)

            if not guests:
                submit()
            versions = tuple(target.ci_version for _, target in guests)
            selected: dict[str, tuple[GuestTool, ...]] = {}
            for turn, (position, target) in enumerate(guests):
                results[position] = _guest_cell_result(
                    host, guest, folder, command, cwd, target, lines[position], tools,
                    versions=versions if turn == 0 else (),
                    barrier=submit if turn == 0 else None, selected=selected, stages=stages,
                    token=guest_tokens[turn])
            for position, target, work, token in pending:
                results[position] = _container_cell(target, lines[position], work.result(),
                                                    token)
        return _replay([results[position] for position in range(len(matrix.targets))], command,
                       cwd, lines, out, err, guest)
    except _NotReady as problem:
        _unreachable(err, problem)
    except _CopyFailed as problem:
        _copy_failed(err, problem)
    finally:
        cells.release()
    return _stopped(line=lines[0], command=command, cwd=cwd, lines=lines)


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

    if isinstance(resolved, ResolvedMatrix):
        return _run_matrix(host, resolved, request.guest, command, cwd, out, err,
                           request.guest_tools,
                           stages=_Stages(request.installs, read_card_dependencies(card)))
    line = environment_line(resolved, request.guest)
    _declare(out, line)
    stages = _Stages(request.installs, read_card_dependencies(card))
    try:
        if resolved.kind is EnvironmentKind.OWNERS_MAC:
            return _issue(host, mac_argv(command), cwd, line, command, out, err)
        if resolved.kind is EnvironmentKind.CONTAINER:
            _check_podman(host)
            where = container_text(resolved)
            missing = stages.missing(EnvironmentKind.CONTAINER)
            if missing is not None:
                return _not_issued(line, command, cwd, out, err,
                                   NotReady(NotReadyCause.NO_INSTALL, EnvironmentKind.CONTAINER,
                                            missing), where, single=True)
            token = host.new_token()
            shell = stages.shell(EnvironmentKind.CONTAINER, command, token)
            return _issue_in(host, container_argv(resolved, shell, cwd), cwd, line, command,
                             out, err, token=token, kind=EnvironmentKind.CONTAINER, where=where,
                             single=True)
        if request.guest is None:
            raise _NotReady("gate_suite: this run was given no macOS guest to run in.")
        folder = map_run_folder(request.guest.shares, cwd)
        if folder is None:
            _fail(err, unshared_lines(request.guest, cwd))
            return _stopped(line=line, command=command, cwd=cwd)
        return _run_in_guest(host, request.guest, folder, command, cwd, line, out, err,
                             request.guest_tools, stages=stages)
    except _NotReady as problem:
        _unreachable(err, problem)
        return _stopped(line=line, command=command, cwd=cwd)


# ==================================================================================================
# The last-run record: what a completed `run` printed, kept for the commit that closes the change
# ==================================================================================================

RUN_RECORDS_NAMESPACE = "kensaiapp-gate-runs"


@dataclass(frozen=True)
class GateRun:
    """One completed `run`, as its caller saw it: the change key, the checkout this copy answers
    for, the `Environment:` lines the run declared (`environment_lines`, in the order it declared
    them), every character forwarded to each stream, and the status returned. Disposable runtime
    evidence, never a committed artifact — distinct from `DecisionRecord`, the product's committed
    decision.

    `environment_line` is the first declaration only, kept so a record built or read the way it
    always was keeps its meaning: a record that names no `environment_lines` has them made from
    that one string (none when it is None). Lines named explicitly, none included, are the whole
    answer — they are never rebuilt from the singular string or from the stored output."""

    key: str
    checkout: str
    environment_line: str | None
    stdout: str
    stderr: str
    status: int
    environment_lines: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.environment_lines is None:
            lines = (self.environment_line,) if self.environment_line is not None else ()
        else:
            lines = tuple(self.environment_lines)
        object.__setattr__(self, "environment_lines", lines)
        if self.environment_line is None and lines:
            object.__setattr__(self, "environment_line", lines[0])


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
                           "environment_line": run.environment_line,
                           "environment_lines": list(run.environment_lines),
                           "stdout": run.stdout, "stderr": run.stderr, "status": run.status},
                          staged)
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
                          found["stdout"], found["stderr"], found["status"],
                          _stored_lines(found))
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return run if (run.checkout, run.key) == (wanted, key) else None


def _stored_lines(found: dict) -> tuple[str, ...] | None:
    """The array a stored record names, or None for a record written before there was one. An
    array of anything but strings is a record this tool did not write."""
    if "environment_lines" not in found:
        return None
    lines = found["environment_lines"]
    if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
        raise TypeError("the record's environment_lines is not a list of strings")
    return tuple(lines)


def default_run_records() -> FileRunRecords:
    return FileRunRecords(Path(tempfile.gettempdir()) / RUN_RECORDS_NAMESPACE)


class _Forwarding:
    """A stream that writes through to the one it wraps, unchanged, and keeps what it wrote — and,
    apart from that, the lines the gate declared through `declare`. What a suite wrote is only ever
    forwarded, so output that looks like a declaration is never taken for one."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self.written: list[str] = []
        self.declared: list[str] = []

    def declare(self, line: str) -> None:
        self.declared.append(line)
        self.write(line + "\n")

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
        run = GateRun(key=key, checkout="", environment_line=None,
                      stdout="".join(self.out.written), stderr="".join(self.err.written),
                      status=status, environment_lines=tuple(self.out.declared))
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
    RefusalCase.OTHER_PLATFORM, RefusalCase.NO_CONTAINER_DEFAULT,
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
            if any(not found.version_known for found in by_language.get(language, ()))]


def _owed_detail(request: GateRequest, refused: Refused) -> str:
    """What the defaults could not settle, with its subjects in resolved-language order."""
    case = refused.case
    if case is RefusalCase.OTHER_PLATFORM:
        return ("the product's CI runs on a platform other than macOS or Linux, its platforms are "
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


def _cell_text(cell: Resolved) -> str:
    if cell.kind is EnvironmentKind.MACOS_GUEST:
        return f"the macOS guest, toolchain {cell.ci_version}"
    return container_text(cell)


def _matrix_detail(matrix: ResolvedMatrix) -> str:
    cells = "; ".join(_cell_text(target) for target in matrix.targets)
    kinds = _unique(target.kind for target in matrix.targets)
    if len(kinds) == 1:
        return (f"container: the product's gates run in {len(matrix.targets)} containers, one for "
                f"each version its CI states: {cells}")
    if kinds[0] is EnvironmentKind.CONTAINER:
        return ("container and macos-guest: the product's gates run in a container for each "
                f"version its CI states and in the macOS guest at the newest: {cells}")
    return ("macos-guest and container: the product's gates run in the macOS guest at the newest "
            f"version its CI states and in a container for each: {cells}")


def _resolved_detail(resolved: Resolved) -> str:
    if resolved.kind is EnvironmentKind.MACOS_GUEST:
        return GUEST_DETAIL
    if resolved.kind is EnvironmentKind.CONTAINER:
        return f"container: the product's gates run in {container_text(resolved)}"
    return OWNERS_MAC_DETAIL[resolved.owners_mac_cause]


def _classify(request: GateRequest,
              outcome: Resolved | ResolvedMatrix | Refused) -> tuple[CheckAnswer, str]:
    """The shared resolver's outcome as one of the three answers; no second decision tree."""
    if isinstance(outcome, ResolvedMatrix):
        return CheckAnswer.RESOLVES, _matrix_detail(outcome)
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


class CheckoutCopies:
    """The real cell workspaces: `checkout(source)` is a context holding a private copy of the
    checkout at `source` — its working files as they are now, the uncommitted and the untracked
    included — in a folder of its own, removed when the context ends.

    Nothing in a copy is shared with the checkout or with another copy: files are copied, never
    linked. A checkout whose `.git` is a pointer file (a linked worktree) names git data a copy
    must not write to, so its copy gets a `.git` folder instead: the repository's shared data,
    with the worktree's own state laid over it — a repository of its own, on the same branch and
    the same index (the same shape `_copy_to_guest_disk` gives the macOS guest)."""

    def __init__(self, files) -> None:
        self._files = files

    @contextlib.contextmanager
    def checkout(self, source: str) -> Iterator[str]:
        folder = Path(tempfile.mkdtemp(prefix=CELL_PREFIX))
        try:
            self._copy(Path(source), folder)
            yield str(folder)
        finally:
            shutil.rmtree(folder)

    def _copy(self, source: Path, folder: Path) -> None:
        linked = self._files.linked_git_dirs(source)
        # Only the checkout's own `.git` is replaced, as the guest copy replaces it (`^./.git`): a
        # repository nested inside the checkout is one of its inputs and keeps its git data.
        shutil.copytree(source, folder, symlinks=True, dirs_exist_ok=True,
                        ignore=_leaving_out(source, (".git",)) if linked is not None else None)
        if linked is None:
            return
        git_dir, common_dir = linked
        own_state = () if git_dir == common_dir else MAIN_CHECKOUT_STATE
        shutil.copytree(common_dir, folder / ".git", symlinks=True, dirs_exist_ok=True,
                        ignore=_leaving_out(common_dir, ("worktrees", *own_state)))
        if git_dir != common_dir:
            shutil.copytree(git_dir, folder / ".git", symlinks=True, dirs_exist_ok=True,
                            ignore=_leaving_out(git_dir, ("commondir", "gitdir")))


def _leaving_out(root: Path, relative: Sequence[str]):
    """A `shutil.copytree` ignore function leaving out each path, given relative to `root`."""
    left_out = {str(root / path) for path in relative}

    def ignore(folder: str, names: list[str]) -> set[str]:
        return {name for name in names if str(Path(folder) / name) in left_out}

    return ignore


def build_host() -> Host:
    core_root = Path(__file__).resolve().parent.parent
    files = _RealFiles()
    return Host(files=files, contract=_real_contract, processes=_RealProcesses(),
                new_token=lambda: uuid.uuid4().hex, core_root=core_root,
                guest_lock=FileGuestLock(Path(GUEST_LOCK_PATH)), record_reader=GitRecordReader(),
                run_records=default_run_records(), workspaces=CheckoutCopies(files),
                environ=os.environ)


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
    asked = args.owners_mac or launch_context_asks(host.environ)
    try:
        # The ask needs no evidence, so evidence handed in beside it is never read: a run that
        # missed the ask and built a malformed inputs file still lands where the owner asked.
        raw = _read_json(host.files, args.inputs, "inputs file") \
            if args.inputs and not asked else None
        status = run_gate(gate=args.gate, worktree=args.worktree, project=args.project,
                          key=args.key, inputs=raw, owners_ask=asked,
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
