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

    A refusal is a value with no execution target, never a fallback to another environment, and the
    owner's Mac is returned in exactly two cases: the product has no CI, or the owner asked.

    In the macOS guest the share is how the run proves the guest reaches its checkout, never what
    it builds from: the suite runs in a copy streamed from the host onto the guest's own disk
    (`_copy_to_guest_disk`).
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import TextIO

__version__ = "1.3.0"

PACKET_ROOT = Path("doctrine") / "engineering" / "languages"
REGISTRY_FILE = PACKET_ROOT / "README.md"

PLATFORM_MACOS = "macos"
PLATFORM_LINUX = "linux"
_ROOT_PRODUCT = "product"
_ROOT_CORE = "core"
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


class RefusalCase(str, Enum):
    """CP-619's cases. (f) is two values because the refusal text differs: a record that names the
    owner's Mac is not a record that rules out both environments."""

    OTHER_PLATFORM = "a"
    MIXED_PLATFORMS = "b"
    NO_CONTAINER_DEFAULT = "c"
    CONFLICTING_IMAGES = "d"
    UNDETERMINED_VERSION = "e"
    DECISIONS_RULE_OUT_BOTH = "f-neither"
    DECISIONS_NAME_OWNERS_MAC = "f-owners-mac"
    UNREADABLE_CI = "g"
    NO_GUEST_DEFAULT = "h"


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
    product's checkout, or `<CORE>` for a language packet."""

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

    def __init__(self, files, product_checkout: Path, core_root: Path) -> None:
        self._files = files
        self._roots = {_ROOT_PRODUCT: product_checkout, _ROOT_CORE: core_root}

    def holds(self, source: Source) -> bool:
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
                  core_root: Path, project: str) -> GateRequest:
    """The sourced input as findings, every quoted source re-opened where it must be. An absent
    input is a request with no CI evidence — which resolves only for the owner's ask. A source is
    re-opened from `product_checkout`, the repository's root, where CI lives; languages are
    inferred from the tracked files under `language_root`, the product's own tree in it."""
    checker = _Checker(files, product_checkout, core_root)
    raw = _mapping(raw, "input")
    chosen = _mapping(raw.get("languages"), "languages")
    extensions = registry_extensions(files.read_text(core_root / REGISTRY_FILE) or "")
    languages = resolve_languages(
        declared=chosen.get("declared"), invoked=chosen.get("invoked"),
        tracked=files.tracked_files(language_root), extensions=extensions)
    decisions = _mapping(raw.get("decisions"), "decisions")
    guest = _mapping(raw.get("guest"), "guest")
    named = (guest_tool(language, files.read_text(
        core_root / PACKET_ROOT / language / "environment.md"))
        for language in languages.languages)
    return GateRequest(
        project=project, languages=languages, ci=_ci_finding(raw.get("ci"), checker),
        override=_override(decisions.get("override"), checker),
        amd64=_amd64(decisions.get("amd64"), checker),
        candidates=tuple(_candidate(item, checker) for item in raw.get("candidates") or []),
        guest=Guest(guest["name"], _shares(guest.get("shares"))) if guest.get("name") else None,
        guest_tools=tuple(tool for tool in named if tool is not None))


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
        return _refuse(request, RefusalCase.DECISIONS_NAME_OWNERS_MAC)
    if override.kind is OverrideKind.MACOS_GUEST:
        return _resolve_guest(request)
    if not override.image or not override.tag:
        return _refuse(request, RefusalCase.UNDETERMINED_VERSION, image=override.image)
    return _container(request, override.image, override.tag, override.architecture)


def _container(request: GateRequest, image: str, tag: str,
               architecture: Architecture | None) -> Resolved | Refused:
    if architecture is None:
        if request.amd64 is not None and request.amd64.failed:
            return _refuse(request, RefusalCase.DECISIONS_RULE_OUT_BOTH,
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
    """Every collaborator the run touches, handed in. `files` reads, lists, writes and removes;
    `contract(worktree, project, key)` is the development-path contract; `processes` has `probe`
    (a readiness check), `issue` (the suite) and `pipe` (one host process's output fed to another's
    input, the guest copy) — separate calls, so a probe is never a suite issue;
    `guest_lock.hold()` is the blocking, exclusive context one guest run lives in."""

    files: object
    contract: Callable[[str, str, str], dict]
    processes: object
    new_token: Callable[[], str]
    core_root: Path
    guest_lock: object


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


def refusal_case_text(refused: Refused) -> str:
    """The text that follows `unresolved — ` on the printed line, and `{case}` in the first line
    of the refusal on standard error."""
    case = refused.case
    if case is RefusalCase.OTHER_PLATFORM:
        return f"the product's CI runs on a platform other than macOS or Linux, {NO_OVERRIDE}"
    if case is RefusalCase.MIXED_PLATFORMS:
        return f"the product's CI runs on both macOS and Linux, {NO_OVERRIDE}"
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
    if case is RefusalCase.DECISIONS_RULE_OUT_BOTH:
        return ("the product's decision files say it can use neither the macOS guest nor a "
                "container, and name no environment")
    if case is RefusalCase.DECISIONS_NAME_OWNERS_MAC:
        return ("the product's decision files name the owner's Mac, which a product record "
                "cannot choose")
    return "the runner cannot be read from the product's CI configuration"


def refusal_lines(refused: Refused) -> list[str]:
    """The refusal on standard error, one string per line, in the order the Content Editor wrote."""
    lines = [f"gate_suite: no environment resolves for project {refused.project}: "
             f"{refusal_case_text(refused)}."]
    if refused.case is RefusalCase.OTHER_PLATFORM:
        lines.append(f"The product's CI runs on: {', '.join(refused.platforms)}.")
    if refused.case is RefusalCase.CONFLICTING_IMAGES:
        images = ", ".join(f"{image}:{tag} for {language}"
                           for image, tag, language in refused.candidate_images)
        lines.append(f"The container images the product's languages call for: {images}.")
    for source in refused.failed_sources:
        lines.append(f'{source.file} does not contain the text the input quotes from it: '
                     f'"{source.anchor}".')
    lines.append(RUNNER_WAY if refused.case is RefusalCase.UNREADABLE_CI else OVERRIDE_WAY)
    lines.append(CLOSING_LINE)
    return lines


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
    code's. A copy that fails is the environment's failure, never the suite's."""
    excluded = [arg for path in build_output(host.files.tracked_files(Path(cwd)))
                for arg in ("--exclude", path)]
    producer = ["tar", "-C", cwd, "--no-mac-metadata", *excluded, "-cf", "-", "."]
    unpack = (f"rm -rf {GUEST_SCRATCH_PREFIX}* && mkdir {shlex.quote(scratch)} && "
              f"tar -C {shlex.quote(scratch)} -xf -")
    try:
        found = host.processes.pipe(producer, ["tart", "exec", "-i", guest.name, "sh", "-c",
                                               unpack], cwd=cwd)
    except ExecutableMissing as missing:
        raise _NotReady(f"gate_suite: {missing.name} was not found on PATH, so this run's "
                        f"checkout cannot be copied onto the macOS guest {guest.name}'s own "
                        f"disk.") from None
    if found.status != 0:
        raise _NotReady(f"gate_suite: this run's checkout, {cwd}, could not be copied onto the "
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

    request = parse_request(
        inputs, files=host.files, product_checkout=Path(paths["product_worktree"]),
        language_root=product_tree(paths), core_root=host.core_root, project=project)
    resolved = resolve_environment(request, owners_ask=owners_ask)
    if isinstance(resolved, Refused):
        line = f"Environment: unresolved {DASH} {refusal_case_text(resolved)}"
        _declare(out, line)
        _fail(err, refusal_lines(resolved))
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


# --- the wiring: the only place a real collaborator is built --------------------------------------


class _RealFiles:
    def read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def tracked_files(self, root: Path) -> list[str]:
        listed = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True,
                                text=True)
        return listed.stdout.splitlines() if listed.returncode == 0 else []

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
                guest_lock=FileGuestLock(Path(GUEST_LOCK_PATH)))


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
    return parser


def main(argv: Sequence[str] | None = None, *, host: Host | None = None,
         stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    args = build_parser().parse_args(argv)
    host = host if host is not None else build_host()
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    try:
        raw = None
        if args.inputs:
            text = host.files.read_text(Path(args.inputs))
            if text is None:
                raise GateError(f"the inputs file {args.inputs} cannot be read")
            try:
                raw = json.loads(text)
            except ValueError as error:
                raise GateError(f"the inputs file {args.inputs} is not JSON: {error}") from error
        result = run_gate(gate=args.gate, worktree=args.worktree, project=args.project,
                          key=args.key, inputs=raw, owners_ask=args.owners_mac, host=host,
                          out=out, err=err)
    except (GateError, InputError) as error:
        err.write(f"gate_suite: {error}\n")
        return ERROR_STATUS
    return result.status


if __name__ == "__main__":
    sys.exit(main())
