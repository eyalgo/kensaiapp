"""Tests for `gate_suite.py` — the resolver and the runner of a gate's suite command.

Resolution (CP-615 to CP-620) is pure: a request built from source-backed findings goes in, an
environment or a refusal comes out, and no process is started. The tests hand the loader a fake
file collaborator, so a source "in the product's checkout" is a key in a dictionary and an
identical file somewhere else is a different key.

The execution half (CP-621 to CP-624) lives further down this file, in its own section.
"""

from __future__ import annotations

import contextlib
import copy
import dataclasses
import re
from pathlib import Path

import pytest

import gate_suite
from gate_suite import (
    Architecture,
    EnvironmentKind,
    OwnersMacCause,
    Refused,
    RefusalCase,
    Resolved,
)

PRODUCT = Path("/work/product")
CORE = Path("/work/core")
PROJECT = "demo"

CI_FILE = ".github/workflows/ci.yml"
PACKET_DIR = "doctrine/engineering/languages"

# What each fake source file holds. The anchors the inputs quote are lines of these texts.
CI_TEXT = (
    "jobs:\n"
    "  test:\n"
    "    runs-on: ubuntu-latest\n"
    "  build:\n"
    "    runs-on: macos-latest\n"
    "    steps:\n"
    '      - python-version: "3.12"\n'
    "      - node-version: 22\n"
    "      - node-version: 20\n"
    "      - toolchain: 1.85.0\n"
    "      - distribution: ubuntu-24.04\n"
)
def guest_table(tool: str, folder: str = "—") -> str:
    """A packet's `## In the macOS guest` section: the tool its gates run with, and the folder
    that holds it when the guest's own PATH does not."""
    return ("\n## In the macOS guest\n\n| Tool | Folder |\n|---|---|\n"
            f"| `{tool}` | {folder if folder == '—' else f'`{folder}`'} |\n\n## Next\n")


RUST_FOLDER = "/Users/admin/.cargo/bin"
PACKET_TEXT = {
    "python": "Python's gates run in a Linux container on the official Python image.\n"
              + guest_table("python3"),
    "javascript": "JavaScript's gates run on the official Node image.\n" + guest_table("node"),
    "typescript": "TypeScript's gates run on the official Node image.\n" + guest_table("node"),
    "rust": "Rust's gates run on the official Rust image.\n" + guest_table("cargo", RUST_FOLDER),
    "shell": "Shell's gates run on the official Ubuntu image.\n" + guest_table("bash"),
    "swift": "Swift has no container default.\n" + guest_table("swift"),
}
PACKET_ANCHOR = {
    "python": "the official Python image",
    "javascript": "the official Node image",
    "typescript": "the official Node image",
    "rust": "the official Rust image",
    "shell": "the official Ubuntu image",
}
IMAGE = {
    "python": ("python", "3.12", 'python-version: "3.12"'),
    "javascript": ("node", "22", "node-version: 22"),
    "typescript": ("node", "22", "node-version: 22"),
    "rust": ("rust", "1.85.0", "toolchain: 1.85.0"),
    "shell": ("ubuntu", "24.04", "distribution: ubuntu-24.04"),
}

REGISTRY_TEXT = (
    "## The language registry\n\n"
    "| Language | Folder | File extensions |\n"
    "|---|---|---|\n"
    "| JavaScript | javascript | `.js`, `.mjs`, `.cjs` |\n"
    "| Python | python | `.py` |\n"
    "| Rust | rust | `.rs` |\n"
    "| Shell | shell | `.sh` |\n"
    "| Swift | swift | `.swift` |\n"
    "| TypeScript | typescript | `.ts`, `.tsx`, `.mts`, `.cts` |\n\n"
    "## The seven concerns\n\n"
    "| Concern | File |\n|---|---|\n| Toolchain | `toolchain.md` |\n"
)


class FakeFiles:
    """The file collaborator: a dictionary of absolute path to text, and a tracked-file list."""

    def __init__(self, files: dict[Path, str], tracked: list[str] | None = None) -> None:
        self.files = dict(files)
        self.tracked = tracked or []
        self.linked: tuple[Path, Path] | None = None
        self.read: list[Path] = []

    def read_text(self, path: Path) -> str | None:
        self.read.append(path)
        return self.files.get(path)

    def tracked_files(self, root: Path) -> list[str]:
        return list(self.tracked)

    def linked_git_dirs(self, root: Path) -> tuple[Path, Path] | None:
        return self.linked


def standard_files(**extra: str) -> FakeFiles:
    files = {PRODUCT / CI_FILE: CI_TEXT, CORE / PACKET_DIR / "README.md": REGISTRY_TEXT}
    for language, text in PACKET_TEXT.items():
        files[CORE / PACKET_DIR / language / "environment.md"] = text
    for relative, text in extra.items():
        files[PRODUCT / relative] = text
    return FakeFiles(files, tracked=["src/app.py"])


def source(file: str = CI_FILE, anchor: str = "runs-on: ubuntu-latest", root: str = "product"):
    return {"root": root, "file": file, "anchor": anchor}


def runner(platform: str, anchor: str | None = None) -> dict:
    anchors = {"linux": "runs-on: ubuntu-latest", "macos": "runs-on: macos-latest"}
    return {"platform": platform, "source": source(anchor=anchor or anchors.get(platform, "jobs:"))}


def candidate(language: str, **override) -> dict:
    image, tag, tag_anchor = IMAGE[language]
    found = {
        "language": language,
        "image": image,
        "tag": tag,
        "image_source": source(f"{PACKET_DIR}/{language}/environment.md", PACKET_ANCHOR[language],
                               root="core"),
        "tag_source": source(CI_FILE, tag_anchor),
    }
    found.update(override)
    return found


def ci_readable(*platforms: str) -> dict:
    return {"finding": "readable", "runners": [runner(platform) for platform in platforms]}


CI_NONE = {"finding": "none", "inventory": "ls -d .github .gitlab-ci.yml .circleci: no such file"}
CI_UNREADABLE = {"finding": "unreadable", "reason": "an unfamiliar service file"}
PRODUCTS_SHARE = {"host": "/work/products", "guest": "/Volumes/My Shared Files/products"}
INSTANCE_SHARE = {"host": "/work/instance", "guest": "/Volumes/My Shared Files/instance"}
GUEST = {"name": "swift-guest", "shares": [PRODUCTS_SHARE, INSTANCE_SHARE]}


def raw_input(ci=None, languages=("python",), override=None, amd64=None, candidates=None,
              guest=GUEST, declared=None) -> dict:
    wanted = list(languages)
    return {
        "languages": {"declared": declared if declared is not None else wanted, "invoked": None},
        "ci": ci if ci is not None else ci_readable("linux"),
        "decisions": {"override": override, "amd64": amd64},
        "candidates": (candidates if candidates is not None
                       else [candidate(name) for name in wanted if name in IMAGE]),
        "guest": guest,
    }


def request_from(raw: dict | None, files: FakeFiles | None = None):
    return gate_suite.parse_request(
        copy.deepcopy(raw), files=files or standard_files(), product_checkout=PRODUCT,
        language_root=PRODUCT, core_root=CORE, project=PROJECT)


def resolve(raw: dict | None, owners_ask: bool = False, files: FakeFiles | None = None):
    return gate_suite.resolve_environment(request_from(raw, files), owners_ask=owners_ask)


def container(image: str, tag: str, arch: Architecture = Architecture.ARM64) -> Resolved:
    return Resolved(kind=EnvironmentKind.CONTAINER, image=image, tag=tag, architecture=arch,
                    owners_mac_cause=None)


# --- CP-615 / CP-620: the CI runner picks the default --------------------------------------------


@pytest.mark.parametrize("language", ["python", "javascript", "typescript", "rust", "shell"])
def test_ci_runner_selects_packet_environment_on_linux(language):
    image, tag, _anchor = IMAGE[language]
    assert resolve(raw_input(languages=(language,))) == container(image, tag)


def test_ci_runner_selects_the_guest_on_macos_whatever_the_languages():
    result = resolve(raw_input(ci=ci_readable("macos"), languages=("swift", "python")))
    assert result == Resolved(kind=EnvironmentKind.MACOS_GUEST, image=None, tag=None,
                              architecture=None, owners_mac_cause=None)


def test_no_ci_selects_the_owners_mac():
    result = resolve(raw_input(ci=CI_NONE))
    assert result == Resolved(kind=EnvironmentKind.OWNERS_MAC, image=None, tag=None,
                              architecture=None, owners_mac_cause=OwnersMacCause.NO_CI)


def test_a_macos_guest_is_resolved_even_when_the_run_was_given_no_guest():
    result = resolve(raw_input(ci=ci_readable("macos"), guest=None))
    assert result.kind is EnvironmentKind.MACOS_GUEST


# --- CP-616: the architecture ---------------------------------------------------------------------


def test_product_architecture_changes_only_architecture():
    default = resolve(raw_input())
    asked = resolve(raw_input(amd64={"source": source(anchor="runs-on: ubuntu-latest")}))
    assert default.architecture is Architecture.ARM64
    assert asked.architecture is Architecture.AMD64
    assert (asked.image, asked.tag) == (default.image, default.tag) == ("python", "3.12")


def test_an_explicit_override_architecture_is_retained():
    override = {"environment": "container", "image": "python", "tag": "3.11",
                "architecture": "amd64",
                "source": source(anchor="jobs:")}
    assert resolve(raw_input(override=override)) == container("python", "3.11", Architecture.AMD64)


# --- CP-617: an override outranks the language default ------------------------------------------


def guest_override() -> dict:
    return {"environment": "macos-guest", "source": source(anchor="jobs:")}


def container_override(**fields) -> dict:
    found = {"environment": "container", "image": "ghcr.io/acme/builder", "tag": "7.1",
             "source": source(anchor="jobs:")}
    found.update(fields)
    return found


@pytest.mark.parametrize("platforms", [("macos",), ("linux",), ("macos", "linux"), ("windows",)])
def test_override_wins_without_requiring_default_sources(platforms):
    # No candidates and no readable language packet: the override must not need either.
    bare = raw_input(ci=ci_readable(*platforms) if platforms != ("windows",) else
                     {"finding": "readable", "runners": [runner("windows")]},
                     languages=("swift",), candidates=[])
    guest = resolve({**bare, "decisions": {"override": guest_override(), "amd64": None}})
    boxed = resolve({**bare, "decisions": {"override": container_override(), "amd64": None}})
    assert guest.kind is EnvironmentKind.MACOS_GUEST
    assert boxed == container("ghcr.io/acme/builder", "7.1")


def test_an_override_container_without_a_tag_cannot_fall_back_to_a_default_version():
    result = resolve(raw_input(override=container_override(tag=None)))
    assert isinstance(result, Refused) and result.case is RefusalCase.UNDETERMINED_VERSION


# --- CP-615 / CP-617: no CI ignores every record --------------------------------------------------


@pytest.mark.parametrize("override", [
    guest_override(), container_override(),
    {"environment": "neither", "source": source(anchor="jobs:")},
    {"environment": "owners-mac", "source": source(anchor="jobs:")},
    container_override(source=source(anchor="not in the file"))])
def test_no_ci_ignores_recorded_overrides(override):
    # The last override quotes a line its file does not hold, which a no-CI branch never opens.
    result = resolve(raw_input(ci=CI_NONE, override=override, candidates=[]))
    assert result.kind is EnvironmentKind.OWNERS_MAC
    assert result.owners_mac_cause is OwnersMacCause.NO_CI


def test_an_omitted_ci_answer_is_never_no_ci():
    raw = raw_input()
    del raw["ci"]
    result = resolve(raw)
    assert isinstance(result, Refused) and result.case is RefusalCase.UNREADABLE_CI
    assert resolve(None).case is RefusalCase.UNREADABLE_CI


# --- CP-618: the owner's ask ---------------------------------------------------------------------


def ask_scenarios() -> list[dict]:
    return [
        raw_input(),
        raw_input(ci=ci_readable("macos")),
        raw_input(ci=CI_NONE),
        raw_input(override=guest_override()),
        raw_input(override=container_override()),
        raw_input(override={"environment": "owners-mac", "source": source(anchor="jobs:")}),
        raw_input(ci=CI_UNREADABLE),
        raw_input(ci={"finding": "readable", "runners": [runner("windows")]}),
        raw_input(ci=ci_readable("macos", "linux")),
        raw_input(languages=("swift",)),
        raw_input(languages=("python", "shell")),
        raw_input(candidates=[candidate("python", tag=None)]),
    ]


@pytest.mark.parametrize("raw", ask_scenarios())
def test_owner_ask_wins_over_every_resolution_branch(raw):
    result = resolve(raw, owners_ask=True)
    assert result == Resolved(kind=EnvironmentKind.OWNERS_MAC, image=None, tag=None,
                              architecture=None, owners_mac_cause=OwnersMacCause.OWNERS_ASK)


def test_the_owner_ask_needs_no_input_at_all():
    assert resolve(None, owners_ask=True).owners_mac_cause is OwnersMacCause.OWNERS_ASK


def test_product_text_or_input_json_cannot_supply_owner_authority():
    raw = raw_input()
    raw["owners_mac"] = True
    raw["decisions"]["owners_ask"] = True
    raw["ask"] = "owner asked for the Mac"
    assert resolve(raw).kind is EnvironmentKind.CONTAINER


# --- CP-619: the refusals -----------------------------------------------------------------------


REFUSALS = {
    "a": (raw_input(ci={"finding": "readable", "runners": [runner("windows")]}),
          RefusalCase.OTHER_PLATFORM),
    "b": (raw_input(ci=ci_readable("macos", "linux")), RefusalCase.MIXED_PLATFORMS),
    "c": (raw_input(languages=("swift",)), RefusalCase.NO_CONTAINER_DEFAULT),
    "d": (raw_input(languages=("python", "shell")), RefusalCase.CONFLICTING_IMAGES),
    "e": (raw_input(candidates=[candidate("python", tag=None)]), RefusalCase.UNDETERMINED_VERSION),
    "f-neither": (raw_input(override={"environment": "neither", "source": source(anchor="jobs:")}),
                  RefusalCase.DECISIONS_RULE_OUT_BOTH),
    "g": (raw_input(ci=CI_UNREADABLE), RefusalCase.UNREADABLE_CI),
}


@pytest.mark.parametrize("name", REFUSALS)
def test_refusal_identifies_product_and_case(name):
    raw, case = REFUSALS[name]
    result = resolve(raw)
    assert isinstance(result, Refused)
    assert (result.project, result.case) == (PROJECT, case)
    assert not hasattr(result, "kind")


def test_refusal_details_name_the_platforms_the_languages_and_the_images():
    other = resolve(REFUSALS["a"][0])
    assert other.platforms == ("windows",)
    nodefault = resolve(raw_input(languages=("python", "swift", "mystery")))
    assert nodefault.languages_without_default == ("swift", "mystery")
    conflict = resolve(REFUSALS["d"][0])
    assert conflict.candidate_images == (("python", "3.12", "python"), ("ubuntu", "24.04", "shell"))
    untagged = resolve(REFUSALS["e"][0])
    assert untagged.image == "python"


def test_a_language_with_no_packet_has_no_container_default():
    result = resolve(raw_input(languages=("mystery",)))
    assert result.case is RefusalCase.NO_CONTAINER_DEFAULT
    assert result.languages_without_default == ("mystery",)


@pytest.mark.parametrize("tag", [None, "", "latest", "LATEST"])
def test_an_untagged_or_latest_default_is_refused(tag):
    result = resolve(raw_input(candidates=[candidate("python", tag=tag)]))
    assert result.case is RefusalCase.UNDETERMINED_VERSION


def test_the_host_interpreter_supplies_no_fallback_version():
    # A tagless candidate on a machine whose own python3 is some version still refuses.
    result = resolve(raw_input(candidates=[candidate("python", tag=None)]))
    assert result.case is RefusalCase.UNDETERMINED_VERSION and result.image == "python"


def test_unreadable_ci_refuses_even_when_an_override_exists():
    result = resolve(raw_input(ci=CI_UNREADABLE, override=guest_override()))
    assert result.case is RefusalCase.UNREADABLE_CI


def test_a_readable_ci_with_no_runner_is_unreadable_not_no_ci():
    result = resolve(raw_input(ci={"finding": "readable", "runners": []}))
    assert result.case is RefusalCase.UNREADABLE_CI


def test_the_owners_ask_outranks_a_recorded_owners_mac_decision():
    raw = raw_input(override={"environment": "owners-mac", "source": source(anchor="jobs:")})
    assert resolve(raw, owners_ask=True).owners_mac_cause is OwnersMacCause.OWNERS_ASK
    assert resolve(raw).owners_mac_cause is OwnersMacCause.PRODUCT_DECISION


# --- CP-615: several languages --------------------------------------------------------------------


def test_matching_language_candidates_collapse():
    # Javascript and TypeScript both name the Node image at the same version: one container.
    result = resolve(raw_input(languages=("javascript", "typescript")))
    assert result == container("node", "22")


def test_different_images_or_different_tags_refuse():
    different_tag = candidate("typescript", tag="20",
                              tag_source=source(CI_FILE, "node-version: 20"))
    result = resolve(raw_input(languages=("javascript", "typescript"),
                               candidates=[candidate("javascript"), different_tag]))
    assert result.case is RefusalCase.CONFLICTING_IMAGES
    assert resolve(raw_input(languages=("python", "rust"))).case is RefusalCase.CONFLICTING_IMAGES


def test_a_version_matrix_without_one_candidate_refuses():
    matrix = candidate("python", tag=None, tag_source=None)
    assert resolve(raw_input(candidates=[matrix])).case is RefusalCase.UNDETERMINED_VERSION


# --- CP-620: where each input comes from ----------------------------------------------------------


def test_loader_reopens_evidence_in_product_checkout():
    files = standard_files()
    request = request_from(raw_input(), files)
    assert PRODUCT / CI_FILE in files.read
    assert request.ci.failed == ()

    # An identical file in another checkout cannot validate a source quoted from this one.
    elsewhere = FakeFiles({Path("/other/checkout") / CI_FILE: CI_TEXT,
                           CORE / PACKET_DIR / "README.md": REGISTRY_TEXT})
    refused = resolve(raw_input(), files=elsewhere)
    assert refused.case is RefusalCase.UNREADABLE_CI
    assert [(failed.file, failed.anchor) for failed in refused.failed_sources] == [
        (CI_FILE, "runs-on: ubuntu-latest")]


def test_a_missing_or_mismatched_ci_source_is_unreadable_ci():
    bad_anchor = raw_input(ci={"finding": "readable",
                               "runners": [runner("linux", anchor="runs-on: nonexistent")]})
    assert resolve(bad_anchor).case is RefusalCase.UNREADABLE_CI
    missing = {"finding": "readable",
               "runners": [{"platform": "linux", "source": source("no/such/file.yml")}]}
    assert resolve(raw_input(ci=missing)).case is RefusalCase.UNREADABLE_CI


def test_a_missing_or_mismatched_version_source_is_an_undetermined_version():
    wrong_tag_line = candidate("python", tag_source=source(CI_FILE, "python-version: 'gone'"))
    assert resolve(raw_input(candidates=[wrong_tag_line])).case is RefusalCase.UNDETERMINED_VERSION
    wrong_packet = candidate("python", image_source=source("nope.md", "the official Python image",
                                                             root="core"))
    assert resolve(raw_input(candidates=[wrong_packet])).case is RefusalCase.UNDETERMINED_VERSION


def test_a_tag_the_quoted_line_does_not_contain_is_undetermined():
    claimed = candidate("python", tag="3.99")  # the quoted CI line says 3.12
    assert resolve(raw_input(candidates=[claimed])).case is RefusalCase.UNDETERMINED_VERSION


def test_failed_sources_are_listed_on_a_refusal():
    gone = candidate("python", tag_source=source(CI_FILE, "python-version: 'gone'"))
    result = resolve(raw_input(candidates=[gone]))
    assert [failed.anchor for failed in result.failed_sources] == ["python-version: 'gone'"]
    # A claim the quoted line does not carry has no missing source to list.
    claimed = resolve(raw_input(candidates=[candidate("python", tag="3.99")]))
    assert claimed.case is RefusalCase.UNDETERMINED_VERSION and claimed.failed_sources == ()


def test_decision_sources_that_do_not_hold_up_refuse_instead_of_resolving_a_default():
    bad = container_override(source=source(anchor="not in the file"))
    result = resolve(raw_input(override=bad))
    assert isinstance(result, Refused)
    assert result.case is RefusalCase.DECISIONS_RULE_OUT_BOTH
    assert [failed.anchor for failed in result.failed_sources] == ["not in the file"]
    bad_amd64 = resolve(raw_input(amd64={"source": source(anchor="not in the file")}))
    assert isinstance(bad_amd64, Refused)


def test_unfamiliar_configuration_works_through_source_facts():
    odd = "pipeline { agent { label 'mac-mini' } }\n"
    files = standard_files(**{"Jenkinsfile": odd})
    ci = {"finding": "readable", "runners": [
        {"platform": "macos", "source": source("Jenkinsfile", "agent { label 'mac-mini' }")}]}
    assert resolve(raw_input(ci=ci), files=files).kind is EnvironmentKind.MACOS_GUEST


def test_every_job_and_matrix_runner_is_represented():
    ci = {"finding": "readable", "runners": [runner("linux"), runner("macos")]}
    request = request_from(raw_input(ci=ci))
    assert [item.platform for item in request.ci.runners] == ["linux", "macos"]
    assert resolve(raw_input(ci=ci)).case is RefusalCase.MIXED_PLATFORMS


def test_override_and_amd64_ask_come_from_decision_findings_only():
    # A top-level field of the input is not a decision finding.
    raw = raw_input()
    raw["override"] = guest_override()
    raw["amd64"] = True
    result = resolve(raw)
    assert result == container("python", "3.12")


# --- the packet source drives the candidate -------------------------------------------------------


def test_packet_source_changes_selected_candidate():
    other_ci = CI_TEXT.replace('"3.12"', '"3.13"')
    files = standard_files(**{CI_FILE: other_ci})
    shifted = candidate("python", tag="3.13", tag_source=source(CI_FILE, 'python-version: "3.13"'))
    assert resolve(raw_input(candidates=[shifted]), files=files) == container("python", "3.13")
    # The same input against the original source no longer holds up.
    assert resolve(raw_input(candidates=[shifted])).case is RefusalCase.UNDETERMINED_VERSION


# --- CP-620: the product's languages --------------------------------------------------------------


def test_language_resolution_follows_the_registry_owner_and_excludes_untracked_files():
    extensions = gate_suite.registry_extensions(REGISTRY_TEXT)
    assert extensions[".py"] == "python" and extensions[".tsx"] == "typescript"
    assert ".md" not in extensions  # the second table's rows are not registry rows

    tracked = ["src/app.py", "tools/run.sh", "README.md"]
    # node_modules/ is untracked or ignored, so `git ls-files` never lists it.
    inferred = gate_suite.resolve_languages(declared=None, invoked=None, tracked=tracked,
                                            extensions=extensions)
    assert (inferred.step, inferred.languages) == ("inferred", ("python", "shell"))

    declared = gate_suite.resolve_languages(declared=["rust"], invoked=["python"], tracked=tracked,
                                            extensions=extensions)
    assert (declared.step, declared.languages) == ("declared", ("rust",))
    invoked = gate_suite.resolve_languages(declared=None, invoked=["python"], tracked=tracked,
                                           extensions=extensions)
    assert (invoked.step, invoked.languages) == ("invoked", ("python",))
    none = gate_suite.resolve_languages(declared=None, invoked=None, tracked=["a.txt"],
                                        extensions=extensions)
    assert (none.step, none.languages) == ("none", ())


def test_the_loader_infers_languages_from_the_checkouts_tracked_files():
    raw = raw_input()
    raw["languages"] = {"declared": None, "invoked": None}
    request = request_from(raw, standard_files())
    assert request.languages.languages == ("python",)
    assert resolve(raw) == container("python", "3.12")


def test_a_product_with_no_resolved_language_has_no_container_default():
    raw = raw_input(candidates=[])
    raw["languages"] = {"declared": None, "invoked": None}
    files = standard_files()
    files.tracked = ["notes.txt"]
    assert resolve(raw, files=files).case is RefusalCase.NO_CONTAINER_DEFAULT


# --- the macOS guest's toolchains: each language's packet names its tool --------------------------


def test_a_packets_guest_table_names_its_tool_and_the_folder_that_holds_it():
    assert gate_suite.guest_tool("rust", guest_table("cargo", RUST_FOLDER)) == (
        gate_suite.GuestTool("rust", "cargo", RUST_FOLDER))
    # A dash is a tool the guest's own PATH already reaches.
    assert gate_suite.guest_tool("swift", guest_table("swift")) == (
        gate_suite.GuestTool("swift", "swift", None))


@pytest.mark.parametrize("text", [
    None,
    "Rust's gates run on the official Rust image.\n",
    # A table under another heading is not the guest's.
    "## Provisioning\n\n| Tool | Folder |\n|---|---|\n| `cargo` | — |\n",
])
def test_a_packet_with_no_guest_table_names_no_tool(text):
    assert gate_suite.guest_tool("rust", text) is None


def without_guest_table(language: str) -> FakeFiles:
    files = standard_files()
    files.files[CORE / PACKET_DIR / language / "environment.md"] = PACKET_TEXT[language].split(
        "\n## In the macOS guest")[0]
    return files


def test_a_language_whose_packet_names_no_guest_tool_has_no_guest_default():
    result = resolve(raw_input(ci=ci_readable("macos"), languages=("swift", "rust")),
                     files=without_guest_table("rust"))
    assert isinstance(result, Refused)
    assert result.case is RefusalCase.NO_GUEST_DEFAULT
    assert result.languages_without_default == ("rust",)
    assert gate_suite.refusal_case_text(result) == (
        "the product's CI runs on macOS, no macOS guest toolchain is named for rust, and the "
        "product's decision files record no override")


def test_a_language_with_no_packet_has_no_guest_default():
    result = resolve(raw_input(ci=ci_readable("macos"), languages=("kotlin",)))
    assert result.case is RefusalCase.NO_GUEST_DEFAULT
    assert result.languages_without_default == ("kotlin",)


def test_an_override_to_the_guest_needs_each_languages_guest_tool_too():
    override = {"environment": "macos-guest", "source": source(anchor="jobs:")}
    result = resolve(raw_input(languages=("rust",), override=override),
                     files=without_guest_table("rust"))
    assert result.case is RefusalCase.NO_GUEST_DEFAULT


def test_the_request_carries_each_languages_guest_tool_in_language_order():
    request = request_from(raw_input(ci=ci_readable("macos"), languages=("rust", "swift")))
    assert request.guest_tools == (gate_suite.GuestTool("rust", "cargo", RUST_FOLDER),
                                   gate_suite.GuestTool("swift", "swift", None))


# ==================================================================================================
# Execution (CP-621 to CP-624): the card's command issued in the resolved environment
# ==================================================================================================

import io
import json
import shlex

WORKTREE = "/work/instance/.worktrees/key1"
PRODUCT_WORKTREE = "/work/product-repo/.worktrees/key1"
CARD_COMMAND = "python3 -m pytest core/tools/ -q"
TOKEN = "tok123"
MAPPED = "/Volumes/My Shared Files/instance/.worktrees/key1"
# The guest-local copy a guest run's suite builds in, on the guest's own disk, never the share.
SCRATCH = f"/tmp/kensaiapp-gate-suite-{TOKEN}"
# The copy is streamed from the host, never read through the share: the guest's view of a share
# goes stale for a file the host replaced, and a copy read through it fails on that file.
COPY = (f"rm -rf /tmp/kensaiapp-gate-suite-* && mkdir {shlex.quote(SCRATCH)} && "
        f"tar -C {shlex.quote(SCRATCH)} -xf -")
CLEAN = f"rm -rf {shlex.quote(SCRATCH)}"


def packed(folder: str, *excluded: str) -> list[str]:
    """The host-side half of the copy: the checkout as a tar stream, each named build folder
    left out by its exact path."""
    return ["tar", "-C", folder, "--no-mac-metadata",
            *(arg for path in excluded for arg in ("--exclude", path)), "-cf", "-", "."]

TOKEN_PATH = Path(WORKTREE) / f".gate_suite_token_{TOKEN}"
DASH = "—"

NASTY_COMMANDS = [
    "python3 -m pytest core/tools/ -q && echo done",
    'pytest -k "a b" -q',
    "pytest -k 'it''s' -q",
    "echo $(whoami) `id` ; pytest",
    "pytest 'dir with spaces/' && echo 'it\"s'",
]


def card_text(command: str = CARD_COMMAND) -> str:
    return (f"# Project Context\n\n**Product path:** .claude\n"
            f"**Test command:** {command}       <!-- the project's own suite -->\n")


def contract(kind: str = "relative", product_worktree: str | None = None) -> dict:
    external = kind != "relative"
    return {"kind": kind,
            "product_worktree": product_worktree or (PRODUCT_WORKTREE if external else WORKTREE),
            "pipeline_worktree": WORKTREE, "product_repo": "/work/product-repo",
            "product_path": "/work/product-repo" if external else ".claude",
            "instance_worktree": WORKTREE}


class Events:
    """One ordered log shared by the streams, the probes and the process runner."""

    def __init__(self) -> None:
        self.log: list[tuple] = []


class RecordingStream(io.StringIO):
    def __init__(self, events: Events, name: str) -> None:
        super().__init__()
        self._events, self._name = events, name

    def write(self, text: str) -> int:
        self._events.log.append((self._name, "write", text))
        return super().write(text)

    def flush(self) -> None:
        self._events.log.append((self._name, "flush"))
        super().flush()


class GateFiles(FakeFiles):
    """FakeFiles plus the two writes the guest identity token needs."""

    def __init__(self, *args, events: Events, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.events = events
        self.written: list[Path] = []
        self.removed: list[Path] = []
        self.fail_write = False

    def write_text(self, path: Path, text: str) -> None:
        self.events.log.append(("files", "write", path))
        self.written.append(path)
        self.files[path] = text

    def remove(self, path: Path) -> None:
        self.events.log.append(("files", "remove", path))
        self.removed.append(path)
        self.files.pop(path, None)


class FakeGuestLock:
    """The lock collaborator a test host is given: it records when it was entered and left, in the
    same log as the streams, the files and the processes."""

    def __init__(self, events: Events) -> None:
        self.events = events
        self.holds = 0

    @contextlib.contextmanager
    def hold(self):
        self.holds += 1
        self.events.log.append(("lock", "acquire"))
        try:
            yield
        finally:
            self.events.log.append(("lock", "release"))


class FakeProcesses:
    """Probes and suite issues are separate calls and separate lists. A script entry is
    `(argv prefix, Completed | exception)`; a probe no entry matches answers ready."""

    def __init__(self, events: Events) -> None:
        self.events = events
        self.probes: list[list[str]] = []
        self.issued: list[tuple[list[str], str]] = []
        self.script: list[tuple[tuple[str, ...], object]] = []
        self.suite = gate_suite.Completed(0, "suite out\n", "")
        self.suite_error: Exception | None = None
        self.pipes: list[tuple[list[str], list[str], str]] = []
        self.pipe_result: object = gate_suite.Completed(0, "", "")

    def when(self, *prefix: str, result) -> None:
        self.script.append((prefix, result))

    def probe(self, argv: list[str]):
        self.events.log.append(("process", "probe", list(argv)))
        self.probes.append(list(argv))
        for prefix, result in self.script:
            if tuple(argv[:len(prefix)]) == prefix:
                if isinstance(result, BaseException):
                    raise result
                return result
        if argv[:2] == ["tart", "list"]:
            return gate_suite.Completed(0, json.dumps([{"Name": "swift-guest",
                                                       "State": "running"}]), "")
        return gate_suite.Completed(0, "", "")

    def issue(self, argv: list[str], *, cwd: str):
        self.events.log.append(("process", "issue", list(argv)))
        self.issued.append((list(argv), cwd))
        if self.suite_error is not None:
            raise self.suite_error
        return self.suite

    def pipe(self, producer: list[str], consumer: list[str], *, cwd: str):
        self.events.log.append(("process", "pipe", list(consumer)))
        self.pipes.append((list(producer), list(consumer), cwd))
        if isinstance(self.pipe_result, Exception):
            raise self.pipe_result
        return self.pipe_result


class Harness:
    def __init__(self, *, card: str | None = None, kind: str = "relative",
                 run_folder: str | None = None, guest_lock=None) -> None:
        self.events = Events()
        self.contract = contract(kind, run_folder)
        product_root = Path(self.contract["product_worktree"])
        # The product's own files live where the contract says its checkout is.
        moved = {(product_root / path.relative_to(PRODUCT) if PRODUCT in path.parents else path):
                 text for path, text in standard_files().files.items()}
        self.files = GateFiles(moved, tracked=["src/app.py"], events=self.events)
        self.files.files[Path(WORKTREE) / "system/projects/demo/project.md"] = (
            card if card is not None else card_text())
        self.processes = FakeProcesses(self.events)
        self.lock = guest_lock if guest_lock is not None else FakeGuestLock(self.events)
        self.out = RecordingStream(self.events, "stdout")
        self.err = RecordingStream(self.events, "stderr")
        self.host = gate_suite.Host(
            files=self.files, contract=lambda worktree, project, key: self.contract,
            processes=self.processes, new_token=lambda: TOKEN, core_root=CORE,
            guest_lock=self.lock)

    def run(self, gate: str = "developer", raw: dict | None = None, owners_ask: bool = False):
        return gate_suite.run_gate(gate=gate, worktree=WORKTREE, project=PROJECT, key="key1",
                                   inputs=raw, owners_ask=owners_ask, host=self.host,
                                   out=self.out, err=self.err)

    @property
    def first_line(self) -> str:
        return self.out.getvalue().split("\n")[0]


def guest_raw(guest: dict | None = None) -> dict:
    return raw_input(ci=ci_readable("macos"), guest=guest if guest is not None else GUEST)


def container_raw(**kwargs) -> dict:
    return raw_input(**kwargs)


def mac_raw() -> dict:
    return raw_input(ci=CI_NONE)


# --- CP-621: the command issued as each environment issues it -------------------------------------


@pytest.mark.parametrize("command", NASTY_COMMANDS)
def test_each_environment_receives_unchanged_card_shell_text(command):
    mac = Harness(card=card_text(command))
    mac.run(raw=mac_raw())
    assert mac.processes.issued == [(["sh", "-c", command], WORKTREE)]

    box = Harness(card=card_text(command))
    box.run(raw=container_raw())
    assert box.processes.issued == [(["podman", "run", "--rm", "-v", f"{WORKTREE}:/work", "-w",
                                      "/work", "python:3.12", "sh", "-c", command], WORKTREE)]

    guest = Harness(card=card_text(command))
    guest.run(raw=guest_raw())
    [(argv, cwd)] = guest.processes.issued
    assert argv[:5] == ["tart", "exec", "swift-guest", "sh", "-c"] and len(argv) == 6
    assert argv[5] == f"cd {shlex.quote(SCRATCH)} && {command}"
    assert cwd == WORKTREE


def test_a_command_with_a_newline_crosses_every_argv_boundary_as_one_argument():
    command = "pytest -q\nexport A='b c' && pytest"
    resolved = Resolved(kind=EnvironmentKind.CONTAINER, image="python", tag="3.12",
                        architecture=Architecture.ARM64, owners_mac_cause=None)
    assert gate_suite.mac_argv(command) == ["sh", "-c", command]
    assert gate_suite.container_argv(resolved, command, WORKTREE)[-1] == command
    guest = gate_suite.Guest("g", ())
    assert gate_suite.guest_argv(guest, command, MAPPED)[-1] == (
        f"cd {shlex.quote(MAPPED)} && {command}")


def test_an_amd64_container_adds_the_architecture_before_the_image():
    harness = Harness()
    harness.run(raw=container_raw(amd64={"source": source(anchor="runs-on: ubuntu-latest")}))
    [(argv, _cwd)] = harness.processes.issued
    assert argv[:9] == ["podman", "run", "--rm", "-v", f"{WORKTREE}:/work", "-w", "/work",
                        "--arch", "amd64"]
    assert argv[9] == "python:3.12"


def test_the_card_command_loses_its_markup_and_comment_and_nothing_else():
    harness = Harness(card="**Test command:** `python3 -m pytest 'a b' -q`   <!-- why -->\n")
    harness.run(raw=mac_raw())
    assert harness.processes.issued[0][0] == ["sh", "-c", "python3 -m pytest 'a b' -q"]


@pytest.mark.parametrize("kind", ["relative", "fixed"])
def test_path_topologies_execute_product_checkout(kind):
    harness = Harness(kind=kind)
    seen = []
    original = harness.files.read_text

    def spy(path):
        seen.append(path)
        return original(path)

    harness.files.read_text = spy
    harness.run(raw=container_raw())
    [(argv, cwd)] = harness.processes.issued
    # Product facts come from the product checkout, and the suite runs there too: an external
    # product's tests are not in the instance worktree.
    expected_root = PRODUCT_WORKTREE if kind == "fixed" else WORKTREE
    assert cwd == expected_root and f"{expected_root}:/work" in argv
    assert Path(expected_root) / CI_FILE in seen
    assert not any(str(path).startswith(PRODUCT_WORKTREE) for path in seen) or kind == "fixed"


# --- CP-622: readiness, never provisioning, never a fallback -------------------------------------


def _unreachable(harness: Harness, *, stderr_fragment: str, issued: int = 0):
    assert harness.processes.issued == [] if issued == 0 else True
    assert stderr_fragment in harness.err.getvalue()
    assert harness.err.getvalue().rstrip("\n").endswith(
        "The test command was not run, on the owner's Mac or anywhere else.")


def test_readiness_failure_issues_no_suite_guest_not_running():
    harness = Harness()
    harness.processes.when("tart", "list", result=gate_suite.Completed(
        0, json.dumps([{"Name": "swift-guest", "State": "stopped"}]), ""))
    status = harness.run(raw=guest_raw()).status
    assert status != 0
    _unreachable(harness, stderr_fragment="gate_suite: the macOS guest swift-guest is not running.")


def test_readiness_failure_issues_no_suite_guest_missing():
    harness = Harness()
    harness.processes.when("tart", "list", result=gate_suite.Completed(0, "[]", ""))
    assert harness.run(raw=guest_raw()).status != 0
    _unreachable(harness, stderr_fragment="the macOS guest swift-guest is not running.")


def test_readiness_failure_guest_does_not_answer():
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "true",
                           result=gate_suite.Completed(1, "", "no route\n\n"))
    assert harness.run(raw=guest_raw()).status != 0
    _unreachable(harness, stderr_fragment="the macOS guest swift-guest cannot be reached through "
                                          "tart exec.")
    assert "The check that failed reported: no route\n" in harness.err.getvalue()


@pytest.mark.parametrize("scripted", [
    gate_suite.Completed(1, "", "No such file\n"),
])
def test_readiness_failure_guest_cannot_see_this_checkout(scripted):
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "sh", "-c", result=scripted)
    assert harness.run(raw=guest_raw()).status != 0
    _unreachable(harness, stderr_fragment=f"the macOS guest swift-guest cannot see this run's "
                                          f"checkout, {WORKTREE}.")
    assert harness.processes.probes[-1][-1].count(f".gate_suite_token_{TOKEN}") == 1
    # The token is looked for at the run's own folder inside the guest, never at a share's root.
    assert harness.processes.probes[-1] == [
        "tart", "exec", "swift-guest", "sh", "-c",
        f"test -f {shlex.quote(MAPPED + '/.gate_suite_token_' + TOKEN)}"]


def test_readiness_failure_tart_missing():
    harness = Harness()
    harness.processes.when("tart", result=gate_suite.ExecutableMissing("tart"))
    assert harness.run(raw=guest_raw()).status != 0
    _unreachable(harness, stderr_fragment="gate_suite: tart was not found on PATH, so the macOS "
                                          "guest cannot be reached.")
    assert "The check that failed reported" not in harness.err.getvalue()


def test_readiness_failure_podman_stopped_unavailable_and_missing():
    stopped = Harness()
    stopped.processes.when("podman", "info", result=gate_suite.Completed(1, "", "boom\n"))
    stopped.processes.when("podman", "machine", result=gate_suite.Completed(0, "stopped\n", ""))
    assert stopped.run(raw=container_raw()).status != 0
    _unreachable(stopped, stderr_fragment="gate_suite: the Podman machine is not running.")

    other = Harness()
    other.processes.when("podman", "info", result=gate_suite.Completed(125, "", "weird\n"))
    other.processes.when("podman", "machine", result=gate_suite.Completed(0, "running\n", ""))
    assert other.run(raw=container_raw()).status != 0
    _unreachable(other, stderr_fragment="gate_suite: Podman cannot be reached.")
    assert "The check that failed reported: weird" in other.err.getvalue()

    missing = Harness()
    missing.processes.when("podman", result=gate_suite.ExecutableMissing("podman"))
    assert missing.run(raw=container_raw()).status != 0
    _unreachable(missing, stderr_fragment="gate_suite: podman was not found on PATH.")


def test_a_run_given_no_guest_is_unreachable_not_a_fallback():
    harness = Harness()
    result = harness.run(raw=raw_input(ci=ci_readable("macos"), guest=None))
    assert result.status != 0 and harness.processes.issued == []
    assert harness.first_line == f"Environment: macos-guest {DASH} no guest given"
    assert "gate_suite: this run was given no macOS guest to run in." in harness.err.getvalue()
    assert harness.processes.probes == []


def test_readiness_failure_keeps_resolved_declaration():
    harness = Harness()
    harness.processes.when("podman", "info", result=gate_suite.Completed(1, "", "x\n"))
    harness.run(raw=container_raw())
    assert harness.first_line == f"Environment: container {DASH} python:3.12, arm64"


def test_no_fallback_or_provisioning_call_ever_happens():
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "true",
                           result=gate_suite.Completed(1, "", ""))
    harness.run(raw=guest_raw())
    forbidden = {"clone", "run", "start", "pull", "init", "create"}
    for argv in harness.processes.probes:
        assert not (forbidden & set(argv[1:3])), argv
    assert harness.processes.issued == []


def _guest_outcomes() -> dict:
    """One harness per way a guest run can end, each already run."""
    outcomes = {}
    passed = Harness()
    passed.run(raw=guest_raw())
    outcomes["pass"] = passed
    red = Harness()
    red.processes.suite = gate_suite.Completed(3, "", "bad\n")
    red.run(raw=guest_raw())
    outcomes["red suite"] = red
    missing = Harness()
    missing.processes.when("tart", "list", result=gate_suite.Completed(0, "[]", ""))
    missing.run(raw=guest_raw())
    outcomes["missing guest"] = missing
    unreachable = Harness()
    unreachable.processes.when("tart", "exec", "swift-guest", "true",
                               result=gate_suite.Completed(1, "", "no route\n"))
    unreachable.run(raw=guest_raw())
    outcomes["unreachable guest"] = unreachable
    invisible = Harness()
    invisible.processes.when("tart", "exec", "swift-guest", "sh", "-c",
                             result=gate_suite.Completed(1, "", ""))
    invisible.run(raw=guest_raw())
    outcomes["invisible token"] = invisible
    unshared = Harness()
    unshared.run(raw=guest_raw({"name": "swift-guest", "shares": [PRODUCTS_SHARE]}))
    outcomes["unshared"] = unshared
    malformed = Harness()
    with pytest.raises(gate_suite.InputError):
        malformed.run(raw=guest_raw({"name": "swift-guest", "shares": "nope"}))
    outcomes["malformed"] = malformed
    return outcomes


def test_every_guest_process_in_every_outcome_is_a_tart_list_or_a_tart_exec():
    for name, harness in _guest_outcomes().items():
        seen = [*harness.processes.probes, *(argv for argv, _cwd in harness.processes.issued),
                *(consumer for _producer, consumer, _cwd in harness.processes.pipes)]
        for argv in seen:
            assert argv[:2] in (["tart", "list"], ["tart", "exec"]), (name, argv)


# --- the guest identity token --------------------------------------------------------------------


@pytest.mark.parametrize("outcome", ["success", "probe-fails", "suite-fails", "execution-error"])
def test_guest_identity_token_is_removed_on_every_outcome(outcome):
    harness = Harness()
    unrelated = Path(WORKTREE) / "keep.txt"
    harness.files.files[unrelated] = "keep"
    if outcome == "probe-fails":
        harness.processes.when("tart", "exec", "swift-guest", "sh", "-c",
                               result=gate_suite.Completed(1, "", ""))
    if outcome == "suite-fails":
        harness.processes.suite = gate_suite.Completed(3, "", "bad\n")
    if outcome == "execution-error":
        harness.processes.suite_error = RuntimeError("runner died")
        with pytest.raises(RuntimeError):
            harness.run(raw=guest_raw())
    else:
        harness.run(raw=guest_raw())
    assert harness.files.written == [TOKEN_PATH]
    assert harness.files.removed == [TOKEN_PATH]
    assert TOKEN_PATH not in harness.files.files
    assert harness.files.files[unrelated] == "keep"


def test_the_token_is_written_before_the_probe_and_the_other_environments_write_none():
    harness = Harness()
    harness.run(raw=guest_raw())
    order = [entry[1] for entry in harness.events.log if entry[0] in ("files", "process")]
    assert order.index("write") < max(i for i, step in enumerate(order) if step == "probe")
    assert order.index("remove") > order.index("issue")
    for raw in (container_raw(), mac_raw()):
        other = Harness()
        other.run(raw=raw)
        assert other.files.written == []


# --- the guest's own disk: the suite builds in a copy, never on the share ------------------------


def _guest_steps(harness: Harness) -> list[str]:
    """Every guest process's shell text (probes, the copy, the suite) in the order they ran."""
    return [entry[2][-1] for entry in harness.events.log
            if entry[0] == "process" and entry[2][:2] == ["tart", "exec"] and len(entry[2]) >= 6]


def _suite_text() -> str:
    return f"cd {shlex.quote(SCRATCH)} && {CARD_COMMAND}"


def test_the_checkout_is_streamed_from_the_host_onto_the_guests_own_disk_before_the_suite():
    harness = Harness()
    harness.run(raw=guest_raw())
    assert harness.processes.pipes == [(
        packed(WORKTREE), ["tart", "exec", "-i", "swift-guest", "sh", "-c", COPY], WORKTREE)]
    steps = _guest_steps(harness)
    assert steps.index("command -v python3") < steps.index(COPY) < steps.index(_suite_text())
    # The suite's folder is under none of the guest's shares: nothing it builds crosses virtiofs.
    [(argv, _cwd)] = harness.processes.issued
    folder = shlex.split(argv[-1])[1]
    assert not any(folder.startswith(share["guest"]) for share in GUEST["shares"])


@pytest.mark.parametrize("suite_status", [0, 3])
def test_the_copy_is_removed_after_the_suite_whatever_it_returned(suite_status):
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(suite_status, "", "")
    result = harness.run(raw=guest_raw())
    assert result.status == suite_status and result.suite_issued
    steps = _guest_steps(harness)
    assert steps[-1] == CLEAN and steps.index(CLEAN) > steps.index(_suite_text())
    assert harness.events.log.index(("lock", "release")) > max(
        i for i, entry in enumerate(harness.events.log) if entry[0] == "process")


def test_the_copy_is_removed_and_the_token_too_when_the_suite_raises():
    harness = Harness()
    harness.processes.suite_error = RuntimeError("runner died")
    with pytest.raises(RuntimeError):
        harness.run(raw=guest_raw())
    assert _guest_steps(harness)[-1] == CLEAN
    assert harness.files.removed == [TOKEN_PATH]


def test_only_the_build_folder_beside_each_tracked_manifest_is_left_out_of_the_copy():
    harness = Harness()
    harness.files.tracked = ["Cargo.toml", "ka reader/Package.swift", "src/target/main.rs",
                             "lib/.build/notes.md", "deep/Cargo.toml.bak", "we[i]rd/Package.swift"]
    harness.run(raw=guest_raw())
    [(producer, _consumer, _cwd)] = harness.processes.pipes
    # Anchored at the checkout's root: a source folder or a file of the same name elsewhere,
    # and a build folder no manifest owns, are copied.
    assert producer == packed(WORKTREE, "^./target", "^./ka reader/.build",
                              "^./we\\[i]rd/.build")


def test_a_checkout_with_no_manifest_is_copied_whole():
    harness = Harness()
    harness.run(raw=guest_raw())
    assert harness.processes.pipes[0][0] == packed(WORKTREE)


# --- the copy's git data: a linked worktree's `.git` pointer names a path only the host has -------

import subprocess

LINKED_GIT_DIR = Path("/work/instance/.git/worktrees/key1")
COMMON_GIT_DIR = Path("/work/instance/.git")
GIT_COPY = shlex.quote(f"{SCRATCH}/.git")


def _shared_git_data(common: Path, *own_state: str) -> list[str]:
    return ["tar", "-C", str(common), "--no-mac-metadata",
            *(arg for path in ("worktrees", *own_state) for arg in ("--exclude", f"^./{path}")),
            "-cf", "-", "."]


def test_a_linked_worktree_is_copied_with_a_git_folder_that_resolves_in_the_guest():
    harness = Harness()
    harness.files.linked = (LINKED_GIT_DIR, COMMON_GIT_DIR)
    harness.run(raw=guest_raw())
    into = ["tart", "exec", "-i", "swift-guest", "sh", "-c"]
    # The pointer file stays behind; the shared data goes in first, the worktree's own state
    # (its HEAD, its index) over it, and neither file that names a host path.
    assert harness.processes.pipes == [
        (packed(WORKTREE, "^./.git"), [*into, COPY], WORKTREE),
        (_shared_git_data(COMMON_GIT_DIR, *gate_suite.MAIN_CHECKOUT_STATE),
         [*into, f"mkdir {GIT_COPY} && tar -C {GIT_COPY} -xf -"], WORKTREE),
        (["tar", "-C", str(LINKED_GIT_DIR), "--no-mac-metadata", "--exclude", "^./commondir",
          "--exclude", "^./gitdir", "-cf", "-", "."],
         [*into, f"tar -C {GIT_COPY} -xf -"], WORKTREE)]
    steps = _guest_steps(harness)
    assert steps.index(f"tar -C {GIT_COPY} -xf -") < steps.index(_suite_text())


def test_a_pointer_to_a_repository_of_its_own_carries_its_data_and_no_worktree_state():
    harness = Harness()
    harness.files.linked = (COMMON_GIT_DIR, COMMON_GIT_DIR)
    harness.run(raw=guest_raw())
    assert [producer for producer, _consumer, _cwd in harness.processes.pipes] == [
        packed(WORKTREE, "^./.git"), _shared_git_data(COMMON_GIT_DIR)]


def test_git_data_that_fails_to_copy_is_the_environments_failure_and_no_suite_is_issued():
    harness = Harness()
    harness.files.linked = (LINKED_GIT_DIR, COMMON_GIT_DIR)
    results = iter([gate_suite.Completed(0, "", ""),
                    gate_suite.Completed(1, "", "tar: No space left on device\n")])
    harness.processes.pipe = lambda producer, consumer, *, cwd: (
        harness.processes.pipes.append((producer, consumer, cwd)) or next(results))
    result = harness.run(raw=guest_raw())
    assert result.status == gate_suite.REFUSAL_STATUS and harness.processes.issued == []
    _unreachable(harness, stderr_fragment=(
        f"gate_suite: the git data of this run's checkout, {COMMON_GIT_DIR}, could not be copied "
        f"onto the macOS guest swift-guest's own disk, where its suite builds."))
    assert len(harness.processes.pipes) == 2
    assert _guest_steps(harness)[-1] == CLEAN


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout


def _repository_with_a_worktree(tmp_path: Path) -> tuple[Path, Path]:
    main = tmp_path / "product"
    main.mkdir()
    _git("init", "-q", "-b", "main", cwd=main)
    (main / "checks").mkdir()
    (main / "checks" / "gate.sh").write_text("echo gate\n")
    _git("add", ".", cwd=main)
    _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "first", cwd=main)
    worktree = main / ".worktrees" / "key1"
    _git("worktree", "add", "-q", "-b", "key1", str(worktree), cwd=main)
    return main, worktree


def test_the_real_files_name_a_linked_worktrees_git_data_and_nothing_for_a_git_folder(tmp_path):
    main, worktree = _repository_with_a_worktree(tmp_path)
    files = gate_suite._RealFiles()
    git_dir, common_dir = files.linked_git_dirs(worktree)
    assert (git_dir.resolve(), common_dir.resolve()) == (
        (main / ".git" / "worktrees" / "key1").resolve(), (main / ".git").resolve())
    assert files.linked_git_dirs(main) is None
    assert files.linked_git_dirs(tmp_path) is None


def test_git_ls_files_in_the_copy_of_a_linked_worktree_exits_0(tmp_path):
    """The finding's case end to end, with real tar and real git: the guest is this host, its
    `tart exec -i` prefix dropped and its scratch folder moved under the test's own folder."""
    _main, worktree = _repository_with_a_worktree(tmp_path)
    (worktree / "checks" / "new.sh").write_text("echo new\n")
    _git("add", "checks/new.sh", cwd=worktree)
    guest_disk = tmp_path / "guest" / "kensaiapp-gate-suite-"
    guest_disk.parent.mkdir()
    real = gate_suite._RealProcesses()

    class LocalGuest:
        def pipe(self, producer, consumer, *, cwd):
            assert consumer[:4] == ["tart", "exec", "-i", "g"]
            text = consumer[-1].replace(gate_suite.GUEST_SCRATCH_PREFIX, str(guest_disk))
            return real.pipe(producer, ["sh", "-c", text], cwd=cwd)

    host = gate_suite.Host(files=gate_suite._RealFiles(), contract=None, processes=LocalGuest(),
                           new_token=None, core_root=CORE, guest_lock=None)
    gate_suite._copy_to_guest_disk(host, gate_suite.Guest("g", ()), str(worktree),
                                   f"{gate_suite.GUEST_SCRATCH_PREFIX}t")
    copy = Path(f"{guest_disk}t")
    assert (copy / ".git").is_dir()
    listed = subprocess.run(["git", "-C", str(copy), "ls-files", "checks"],
                            capture_output=True, text=True)
    assert (listed.returncode, listed.stdout) == (0, "checks/gate.sh\nchecks/new.sh\n")
    assert _git("-C", str(copy), "branch", "--show-current", cwd=tmp_path) == "key1\n"
    assert _git("-C", str(copy), "status", "--porcelain", cwd=tmp_path) == "A  checks/new.sh\n"


def test_the_main_checkouts_own_state_does_not_reach_a_worktrees_copy(tmp_path):
    main, worktree = _repository_with_a_worktree(tmp_path)
    (main / "staged-in-main").write_text("x\n")
    _git("add", "staged-in-main", cwd=main)
    _git("update-ref", "refs/bisect/bad", "HEAD", cwd=main)
    # A worktree with no index of its own: the main checkout's must not stand in for it.
    (Path(_git("rev-parse", "--git-dir", cwd=worktree).strip()) / "index").unlink()
    guest_disk = tmp_path / "guest" / "kensaiapp-gate-suite-"
    guest_disk.parent.mkdir()
    real = gate_suite._RealProcesses()

    class LocalGuest:
        def pipe(self, producer, consumer, *, cwd):
            text = consumer[-1].replace(gate_suite.GUEST_SCRATCH_PREFIX, str(guest_disk))
            return real.pipe(producer, ["sh", "-c", text], cwd=cwd)

    host = gate_suite.Host(files=gate_suite._RealFiles(), contract=None, processes=LocalGuest(),
                           new_token=None, core_root=CORE, guest_lock=None)
    gate_suite._copy_to_guest_disk(host, gate_suite.Guest("g", ()), str(worktree),
                                   f"{gate_suite.GUEST_SCRATCH_PREFIX}t")
    copy = Path(f"{guest_disk}t")
    assert "staged-in-main" not in _git("-C", str(copy), "ls-files", cwd=tmp_path)
    assert "refs/bisect" not in _git("-C", str(copy), "for-each-ref", cwd=tmp_path)
    assert _git("-C", str(copy), "branch", "--show-current", cwd=tmp_path) == "key1\n"


def test_a_copy_that_fails_is_the_environments_failure_and_no_suite_is_issued():
    harness = Harness()
    harness.processes.pipe_result = gate_suite.Completed(1, "", "tar: Write error\n")
    result = harness.run(raw=guest_raw())
    assert result.status == gate_suite.REFUSAL_STATUS and not result.suite_issued
    _unreachable(harness, stderr_fragment=(
        f"gate_suite: this run's checkout, {WORKTREE}, could not be copied onto the macOS guest "
        f"swift-guest's own disk, where its suite builds."))
    assert "The check that failed reported: tar: Write error" in harness.err.getvalue()
    # A copy that stopped part-way may have left files: they are removed all the same.
    assert _guest_steps(harness)[-1] == CLEAN
    assert harness.files.removed == [TOKEN_PATH]


def test_a_host_with_no_tar_cannot_copy_and_issues_no_suite():
    harness = Harness()
    harness.processes.pipe_result = gate_suite.ExecutableMissing("tar")
    result = harness.run(raw=guest_raw())
    assert result.status == gate_suite.REFUSAL_STATUS and harness.processes.issued == []
    _unreachable(harness, stderr_fragment=(
        "gate_suite: tar was not found on PATH, so this run's checkout cannot be copied onto "
        "the macOS guest swift-guest's own disk."))


def test_a_check_that_fails_before_the_copy_makes_no_copy_and_removes_none():
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "sh", "-c",
                           result=gate_suite.Completed(1, "", ""))
    harness.run(raw=guest_raw())
    assert harness.processes.pipes == [] and CLEAN not in _guest_steps(harness)


def test_a_cleanup_that_fails_leaves_the_suites_status_alone_and_says_so():
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "sh", "-c", CLEAN,
                           result=gate_suite.Completed(1, "", "busy\n"))
    result = harness.run(raw=guest_raw())
    assert result.status == 0 and result.suite_issued
    assert (f"gate_suite: the copy of this run's checkout at {SCRATCH} in the macOS guest "
            f"swift-guest could not be removed.") in harness.err.getvalue()


@pytest.mark.parametrize("raised", [OSError("EPERM"), KeyboardInterrupt()])
def test_a_cleanup_that_raises_still_removes_the_token(raised):
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "sh", "-c", CLEAN, result=raised)
    with pytest.raises(type(raised)):
        harness.run(raw=guest_raw())
    assert harness.files.removed == [TOKEN_PATH] and TOKEN_PATH not in harness.files.files


def test_the_real_pipe_feeds_the_producers_output_to_the_consumer_and_reports_either_failure(
        tmp_path):
    pipe = gate_suite._RealProcesses().pipe
    done = pipe(["printf", "a b"], ["sh", "-c", "cat; echo x >&2"], cwd=str(tmp_path))
    assert (done.status, done.stdout, done.stderr) == (0, "a b", "x\n")
    assert pipe(["sh", "-c", "echo bad >&2; exit 4"], ["cat"], cwd=str(tmp_path)).status == 4
    assert pipe(["printf", "a"], ["sh", "-c", "exit 5"], cwd=str(tmp_path)).status == 5
    # bsdtar ends a message with no newline: the two programs' messages stay on their own lines.
    joined = pipe(["sh", "-c", "printf 'tar: Write error' >&2"],
                  ["sh", "-c", "cat >/dev/null; printf 'mkdir: exists' >&2"], cwd=str(tmp_path))
    assert joined.stderr.splitlines() == ["tar: Write error", "mkdir: exists"]
    with pytest.raises(gate_suite.ExecutableMissing):
        pipe(["no-such-tool-xyz"], ["cat"], cwd=str(tmp_path))
    with pytest.raises(gate_suite.ExecutableMissing):
        pipe(["printf", "a"], ["no-such-tool-xyz"], cwd=str(tmp_path))


# --- the guest's toolchains: probed before the suite, reached by the suite -----------------------


RUST_PATH = f"export PATH={shlex.quote(RUST_FOLDER)}:\"$PATH\""


def test_each_languages_tool_is_probed_in_the_guest_after_the_share_and_before_the_suite():
    harness = Harness()
    harness.run(raw=raw_input(ci=ci_readable("macos"), languages=("rust", "swift")))
    tool_probes = [argv for argv in harness.processes.probes if "command -v" in argv[-1]]
    assert tool_probes == [
        ["tart", "exec", "swift-guest", "sh", "-c", f"{RUST_PATH} && command -v cargo"],
        ["tart", "exec", "swift-guest", "sh", "-c", "command -v swift"],
    ]
    order = [entry[2][-1] for entry in harness.events.log if entry[0] == "process"]
    share = next(i for i, step in enumerate(order) if step.startswith("test -f"))
    assert share < order.index(f"{RUST_PATH} && command -v cargo")
    assert len(harness.processes.issued) == 1


def test_a_tool_the_guest_lacks_is_a_refusal_and_no_suite_is_issued():
    harness = Harness()
    harness.processes.when("tart", "exec", "swift-guest", "sh", "-c",
                           f"{RUST_PATH} && command -v cargo",
                           result=gate_suite.Completed(1, "", ""))
    result = harness.run(raw=raw_input(ci=ci_readable("macos"), languages=("rust",)))
    assert result.status == gate_suite.REFUSAL_STATUS and not result.suite_issued
    assert harness.processes.issued == []
    _unreachable(harness, stderr_fragment=(
        f"gate_suite: the macOS guest swift-guest has no cargo, the tool rust's gates run with, "
        f"in {RUST_FOLDER} or on the guest's PATH."))
    assert harness.files.removed == [TOKEN_PATH]


def test_the_suite_runs_with_each_named_folder_on_the_guests_path():
    harness = Harness()
    harness.run(raw=raw_input(ci=ci_readable("macos"), languages=("rust", "swift")))
    [(argv, _cwd)] = harness.processes.issued
    assert argv[-1] == f"{RUST_PATH} && cd {shlex.quote(SCRATCH)} && {CARD_COMMAND}"


def test_a_guest_refusal_for_a_language_with_no_guest_tool_starts_no_guest_process():
    harness = Harness()
    harness.files.files[CORE / PACKET_DIR / "rust" / "environment.md"] = "no table\n"
    result = harness.run(raw=raw_input(ci=ci_readable("macos"), languages=("rust",)))
    assert result.status == gate_suite.REFUSAL_STATUS
    assert harness.first_line == (
        f"Environment: unresolved {DASH} the product's CI runs on macOS, no macOS guest toolchain "
        f"is named for rust, and the product's decision files record no override")
    assert harness.processes.probes == [] and harness.processes.issued == []


# --- CP-623 / CP-624: the first line ------------------------------------------------------------


def test_environment_declaration_precedes_all_output():
    harness = Harness()
    harness.run(raw=guest_raw())
    log = harness.events.log
    assert log[0] == ("stdout", "write", f"Environment: macos-guest {DASH} swift-guest\n")
    assert log[1] == ("stdout", "flush")
    assert all(entry[0] != "process" for entry in log[:2])
    assert harness.out.getvalue() == f"Environment: macos-guest {DASH} swift-guest\nsuite out\n"
    declarations = [line for line in harness.out.getvalue().splitlines()
                    if line.startswith("Environment:")]
    assert len(declarations) == 1


@pytest.mark.parametrize("raw,expected", [
    (lambda: guest_raw(), f"Environment: macos-guest {DASH} swift-guest"),
    (lambda: container_raw(), f"Environment: container {DASH} python:3.12, arm64"),
    (lambda: container_raw(amd64={"source": source(anchor="runs-on: ubuntu-latest")}),
     f"Environment: container {DASH} python:3.12, amd64"),
    (lambda: mac_raw(), f"Environment: owners-mac {DASH} no CI"),
])
def test_every_resolved_form_is_exact(raw, expected):
    harness = Harness()
    harness.run(raw=raw())
    assert harness.first_line == expected


def test_the_owners_ask_prints_its_own_cause_and_needs_no_sources():
    harness = Harness()
    result = harness.run(raw=None, owners_ask=True)
    assert harness.first_line == f"Environment: owners-mac {DASH} owner's ask"
    assert harness.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]
    assert result.status == 0


def test_suite_stdout_and_stderr_stay_separate_and_preserved():
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(0, "line one\nline two\n", "warn\n")
    harness.run(raw=mac_raw())
    assert harness.out.getvalue() == f"Environment: owners-mac {DASH} no CI\nline one\nline two\n"
    assert harness.err.getvalue() == "warn\n"


# --- refusals ------------------------------------------------------------------------------------

EXEC_REFUSALS = [
    (lambda: raw_input(ci=ci_readable("windows")), "a platform other than macOS or Linux", "a"),
    (lambda: raw_input(ci=ci_readable("linux", "macos")), "both macOS and Linux", "b"),
    (lambda: raw_input(languages=("swift",), candidates=[]),
     "no container default exists for swift", "c"),
    (lambda: raw_input(languages=("python", "shell")), "more than one container image", "d"),
    (lambda: raw_input(candidates=[candidate("python", tag="latest")]),
     "the version to tag python with cannot be determined", "e"),
    (lambda: raw_input(override={"environment": "neither", "source": source(anchor="jobs:")}),
     "can use neither the macOS guest nor a container, and name no environment", "f"),
    (lambda: raw_input(ci=CI_UNREADABLE),
     "the runner cannot be read from the product's CI configuration", "g"),
]


@pytest.mark.parametrize("raw,fragment,_case", EXEC_REFUSALS)
def test_refusal_prints_unresolved_and_issues_nothing(raw, fragment, _case):
    harness = Harness()
    result = harness.run(raw=raw())
    assert harness.first_line.startswith(f"Environment: unresolved {DASH} ")
    assert fragment in harness.first_line
    case_text = harness.first_line.split(f"unresolved {DASH} ", 1)[1]
    stderr = harness.err.getvalue().splitlines()
    assert stderr[0] == f"gate_suite: no environment resolves for project demo: {case_text}."
    assert stderr[-1] == "The test command was not run, on the owner's Mac or anywhere else."
    assert result.status != 0 and not result.suite_issued
    assert harness.processes.probes == [] and harness.processes.issued == []


def test_refusal_stderr_lists_the_platforms_the_images_and_the_failed_source():
    other = Harness()
    other.run(raw=raw_input(ci=ci_readable("windows")))
    lines = other.err.getvalue().splitlines()
    assert lines[1] == "The product's CI runs on: windows."
    assert lines[2] == ("To run it, record an override in the product's decision files, or have "
                        "the owner ask for the owner's Mac.")

    images = Harness()
    images.run(raw=raw_input(languages=("python", "shell")))
    assert ("The container images the product's languages call for: python:3.12 for python, "
            "ubuntu:24.04 for shell.") in images.err.getvalue().splitlines()

    unreadable = Harness()
    unreadable.run(raw=raw_input(ci=CI_UNREADABLE))
    lines = unreadable.err.getvalue().splitlines()
    assert lines[1] == ("To run it, read the runner from the product's CI configuration and "
                        "supply it with its source, or have the owner ask for the owner's Mac.")

    failed = Harness()
    failed.run(raw=raw_input(ci={"finding": "readable", "runners": [
        {"platform": "linux", "source": source(anchor="runs-on: nothing-like-this")}]}))
    assert (f'{CI_FILE} does not contain the text the input quotes from it: '
            f'"runs-on: nothing-like-this".') in failed.err.getvalue().splitlines()


def test_a_refusal_with_no_inputs_at_all_is_the_unreadable_runner_case():
    harness = Harness()
    harness.run(raw=None)
    assert "the runner cannot be read" in harness.first_line
    assert harness.processes.issued == []



# --- the two refusals the records describe: an empty language list, a failed override -------------

OVERRIDE_WAY_LINE = ("To run it, record an override in the product's decision files, or have the "
                     "owner ask for the owner's Mac.")
CLOSING_LINE = "The test command was not run, on the owner's Mac or anywhere else."
NEITHER_TEXT = ("the product's decision files say it can use neither the macOS guest nor a "
                "container, and name no environment")
NO_LANGUAGE_TEXT = ("the product's CI runs on Linux, no container default can be chosen because "
                    "no language was resolved for the product, and the product's decision files "
                    "record no override")
MISSING_QUOTE = "not in the file"
FAILED_DETAIL = f'{CI_FILE} does not contain the text the input quotes from it: "{MISSING_QUOTE}".'


def assert_refused_without_running(harness: Harness, result) -> None:
    assert result.status == 1 and not result.suite_issued
    assert harness.processes.probes == [] and harness.processes.issued == []
    assert harness.processes.pipes == []


def test_empty_language_linux_refusal_names_no_language():
    harness = Harness()
    harness.files.tracked = ["notes.txt"]
    raw = raw_input(languages=(), candidates=[])
    raw["languages"] = {"declared": None, "invoked": None}
    result = harness.run(raw=raw)
    stdout = harness.out.getvalue()
    assert "for ," not in stdout and ", ," not in stdout
    assert stdout == f"Environment: unresolved {DASH} {NO_LANGUAGE_TEXT}\n"
    assert harness.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {NO_LANGUAGE_TEXT}.",
        OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(harness, result)


def test_nonempty_no_default_refusal_retains_language_order():
    harness = Harness()
    result = harness.run(raw=raw_input(languages=("swift", "zig", "mystery"), candidates=[]))
    text = ("the product's CI runs on Linux, no container default exists for swift, zig, "
            "mystery, and the product's decision files record no override")
    assert harness.out.getvalue() == f"Environment: unresolved {DASH} {text}\n"
    assert harness.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {text}.",
        OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert "no language was resolved" not in harness.out.getvalue()
    assert_refused_without_running(harness, result)


def failed_override(kind: str, src: dict) -> dict:
    return {"container": lambda: container_override(source=src),
            "neither": lambda: {"environment": "neither", "source": src},
            "macos-guest": lambda: {"environment": "macos-guest", "source": src},
            "owners-mac": lambda: {"environment": "owners-mac", "source": src}}[kind]()


def failed_override_text(file: str) -> str:
    return (f"the override in the product's decision files cannot be used, because its source, "
            f"{file}, does not contain the text the input quotes from it")


@pytest.mark.parametrize("kind", ["container", "neither", "macos-guest", "owners-mac"])
def test_failed_override_refusal_names_its_source(kind):
    harness = Harness()
    result = harness.run(raw=raw_input(
        override=failed_override(kind, source(anchor=MISSING_QUOTE))))
    stdout = harness.out.getvalue()
    assert CI_FILE in stdout and NEITHER_TEXT not in stdout
    assert stdout == f"Environment: unresolved {DASH} {failed_override_text(CI_FILE)}\n"
    assert harness.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {failed_override_text(CI_FILE)}.",
        FAILED_DETAIL, OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(harness, result)


def test_failed_override_refusal_names_an_absent_source():
    harness = Harness()
    gone = source("docs/decisions/absent.md", MISSING_QUOTE)
    result = harness.run(raw=raw_input(override=container_override(source=gone)))
    assert harness.out.getvalue() == (
        f"Environment: unresolved {DASH} {failed_override_text('docs/decisions/absent.md')}\n")
    assert harness.err.getvalue().splitlines() == [
        "gate_suite: no environment resolves for project demo: "
        f"{failed_override_text('docs/decisions/absent.md')}.",
        f'docs/decisions/absent.md does not contain the text the input quotes from it: '
        f'"{MISSING_QUOTE}".', OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(harness, result)


def test_failed_override_refusal_preserves_an_alternate_source_name():
    harness = Harness()
    harness.files.files[Path(harness.contract["product_worktree"]) / "docs/decisions/env.md"] = (
        "an environment note\n")
    elsewhere = source("docs/decisions/env.md", MISSING_QUOTE)
    result = harness.run(raw=raw_input(override=container_override(source=elsewhere)))
    text = failed_override_text("docs/decisions/env.md")
    assert harness.out.getvalue() == f"Environment: unresolved {DASH} {text}\n"
    assert harness.err.getvalue().splitlines()[1] == (
        f'docs/decisions/env.md does not contain the text the input quotes from it: '
        f'"{MISSING_QUOTE}".')
    assert_refused_without_running(harness, result)

    rooted = Harness()
    in_core = source("doctrine/engineering/languages/README.md", MISSING_QUOTE, root="core")
    result = rooted.run(raw=raw_input(override=container_override(source=in_core)))
    text = failed_override_text("doctrine/engineering/languages/README.md")
    assert rooted.out.getvalue() == f"Environment: unresolved {DASH} {text}\n"
    assert "/work/core" not in rooted.out.getvalue() + rooted.err.getvalue()
    assert rooted.err.getvalue().splitlines()[1] == (
        f'doctrine/engineering/languages/README.md does not contain the text the input quotes '
        f'from it: "{MISSING_QUOTE}".')
    assert_refused_without_running(rooted, result)


AMD64_FILE = "docs/decisions/arch.md"
AMD64_QUOTE = "amd64 please"


def failed_amd64_text(file: str) -> str:
    return (f"the amd64 requirement in the product's decision files cannot be used, because its "
            f"source, {file}, does not contain the text the input quotes from it")


@pytest.mark.parametrize("override", [None, "container"])
def test_failed_amd64_source_names_its_file(override):
    harness = Harness()
    raw = raw_input(amd64={"source": source(AMD64_FILE, AMD64_QUOTE)},
                    override=container_override() if override else None)
    result = harness.run(raw=raw)
    text = failed_amd64_text(AMD64_FILE)
    assert harness.out.getvalue() == f"Environment: unresolved {DASH} {text}\n"
    assert NEITHER_TEXT not in harness.out.getvalue() + harness.err.getvalue()
    assert harness.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {text}.",
        f'{AMD64_FILE} does not contain the text the input quotes from it: "{AMD64_QUOTE}".',
        OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(harness, result)


def test_failed_amd64_source_gets_its_own_refusal_case():
    refused = resolve(raw_input(amd64={"source": source(AMD64_FILE, AMD64_QUOTE)}))
    assert refused.case is RefusalCase.FAILED_AMD64_SOURCE
    assert [found.file for found in refused.failed_sources] == [AMD64_FILE]
    neither = resolve(raw_input(override={"environment": "neither",
                                          "source": source(anchor="jobs:")}))
    assert neither.case is RefusalCase.DECISIONS_RULE_OUT_BOTH


def test_an_explicit_container_architecture_never_reaches_a_failing_amd64_source():
    harness = Harness()
    raw = raw_input(amd64={"source": source(AMD64_FILE, AMD64_QUOTE)},
                    override=container_override(architecture="arm64"))
    result = harness.run(raw=raw)
    assert harness.first_line == f"Environment: container {DASH} ghcr.io/acme/builder:7.1, arm64"
    assert result.status == 0 and harness.err.getvalue() == ""


def test_failed_override_does_not_override_earlier_environment_selection():
    bad = container_override(source=source(anchor=MISSING_QUOTE))
    unreadable = Harness()
    result = unreadable.run(raw=raw_input(ci=CI_UNREADABLE, override=bad))
    text = "the runner cannot be read from the product's CI configuration"
    assert unreadable.out.getvalue() == f"Environment: unresolved {DASH} {text}\n"
    assert unreadable.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {text}.",
        "To run it, read the runner from the product's CI configuration and supply it with its "
        "source, or have the owner ask for the owner's Mac.", CLOSING_LINE]
    assert_refused_without_running(unreadable, result)

    for raw, owners_ask in [(raw_input(ci=CI_NONE, override=bad), False),
                            (raw_input(override=bad), True)]:
        asked = Harness()
        result = asked.run(raw=raw, owners_ask=owners_ask)
        assert asked.first_line.startswith(f"Environment: owners-mac {DASH} ")
        assert asked.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]
        assert result.status == 0 and result.suite_issued


def test_failed_override_refusal_names_its_source_whatever_platform_ci_reads():
    # CP-695 holds on any readable CI: the override is read before the CI's platform is.
    harness = Harness()
    result = harness.run(raw=raw_input(
        ci=ci_readable("macos"), languages=("swift",),
        override=container_override(source=source(anchor=MISSING_QUOTE))))
    assert harness.out.getvalue() == (
        f"Environment: unresolved {DASH} {failed_override_text(CI_FILE)}\n")
    assert harness.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {failed_override_text(CI_FILE)}.",
        FAILED_DETAIL, OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(harness, result)


def test_failed_override_outranks_failed_amd64_source():
    # Both decision sources fail: the override's is the cause, so its text and only its
    # source line are printed (CP-695, CP-696).
    harness = Harness()
    result = harness.run(raw=raw_input(
        override=container_override(source=source(anchor=MISSING_QUOTE)),
        amd64={"source": source("docs/decisions/arch.md", "amd64 please")}))
    assert harness.out.getvalue() == (
        f"Environment: unresolved {DASH} {failed_override_text(CI_FILE)}\n")
    assert harness.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {failed_override_text(CI_FILE)}.",
        FAILED_DETAIL, OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(harness, result)


def test_other_refusals_keep_exact_output(tmp_path):
    # Valid neither: the text of the decision files ruling out both environments.
    neither = Harness()
    result = neither.run(raw=raw_input(
        override={"environment": "neither", "source": source(anchor="jobs:")}))
    assert neither.out.getvalue() == f"Environment: unresolved {DASH} {NEITHER_TEXT}\n"
    assert neither.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {NEITHER_TEXT}.",
        OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(neither, result)

    # macOS guest with no toolchain named for the language.
    toolless = Harness()
    toolless.files.files[CORE / PACKET_DIR / "rust" / "environment.md"] = "no table\n"
    result = toolless.run(raw=raw_input(ci=ci_readable("macos"), languages=("rust",)))
    text = ("the product's CI runs on macOS, no macOS guest toolchain is named for rust, and "
            "the product's decision files record no override")
    assert toolless.out.getvalue() == f"Environment: unresolved {DASH} {text}\n"
    assert toolless.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {text}.",
        OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert_refused_without_running(toolless, result)

    # A checkout under none of the guest's shares, in every share variant.
    checkout = ("gate_suite: this run's checkout, /work/instance/.worktrees/key1, is under none "
                "of the shares this run was given for the macOS guest swift-guest.")
    variants = {
        "no match": [
            checkout, "The shares this run was given: /work/products.",
            "The checkout has to be under one of those folders, or the guest has to be started "
            "with a share that holds it.", CLOSING_LINE],
        "absent": [
            checkout, "This run was given no shares for the guest. Each share is given in "
            "guest.shares, with the host folder and the folder it appears at inside the guest.",
            CLOSING_LINE],
    }
    variants["empty"] = variants["absent"]
    guests = {"no match": {"name": "swift-guest", "shares": [PRODUCTS_SHARE]},
              "absent": {"name": "swift-guest"}, "empty": {"name": "swift-guest", "shares": []}}
    for name, guest in guests.items():
        unshared = Harness()
        result = unshared.run(raw=guest_raw(guest))
        assert unshared.out.getvalue() == f"Environment: macos-guest {DASH} swift-guest\n", name
        assert unshared.err.getvalue().splitlines() == variants[name], name
        assert result.status == 1 and not result.suite_issued, name
        assert unshared.processes.probes == [] and unshared.processes.issued == [], name

    # The lock that cannot be taken: a refusal of its own, with status 2.
    missing = tmp_path / "no-such-folder" / "guest.lock"
    locked = Harness(guest_lock=gate_suite.FileGuestLock(missing))
    assert run_cli(locked, "--gate", "developer", inputs=guest_raw()) == 2
    assert locked.out.getvalue() == f"Environment: macos-guest {DASH} swift-guest\n"
    assert locked.err.getvalue() == (
        "gate_suite: the lock that lets one gate at a time run in the macOS guest cannot be "
        f"taken, at {missing}: {os.strerror(errno.ENOENT)}\n")
    assert locked.processes.probes == [] and locked.processes.issued == []


def test_original_formatter_calls_keep_their_meaning():
    swift = resolve(raw_input(languages=("swift", "mystery"), candidates=[]))
    text = ("the product's CI runs on Linux, no container default exists for swift, mystery, "
            "and the product's decision files record no override")
    assert gate_suite.refusal_case_text(swift) == text
    assert gate_suite.refusal_lines(swift) == [
        f"gate_suite: no environment resolves for project demo: {text}.",
        OVERRIDE_WAY_LINE, CLOSING_LINE]
    neither = resolve(raw_input(
        override={"environment": "neither", "source": source(anchor="jobs:")}))
    assert gate_suite.refusal_case_text(neither) == NEITHER_TEXT
    assert gate_suite.refusal_lines(neither) == [
        f"gate_suite: no environment resolves for project demo: {NEITHER_TEXT}.",
        OVERRIDE_WAY_LINE, CLOSING_LINE]


def test_formatter_accepts_checked_override_context():
    bad = source(anchor=MISSING_QUOTE)
    refused = resolve(raw_input(override=container_override(source=bad)))
    checked = refused.failed_sources[0]
    assert gate_suite.refusal_case_text(refused, failed_override_source=checked) == (
        failed_override_text(CI_FILE))
    assert gate_suite.refusal_case_text(refused) == NEITHER_TEXT
    # The context applies to its own refusal only.
    other = resolve(raw_input(languages=("swift",), candidates=[]))
    assert gate_suite.refusal_case_text(other, failed_override_source=checked) == (
        gate_suite.refusal_case_text(other))


def test_refusal_lines_accept_selected_case_text():
    refused = resolve(raw_input(override=container_override(source=source(anchor=MISSING_QUOTE))))
    chosen = failed_override_text(CI_FILE)
    assert gate_suite.refusal_lines(refused, case_text=chosen) == [
        f"gate_suite: no environment resolves for project demo: {chosen}.",
        FAILED_DETAIL, OVERRIDE_WAY_LINE, CLOSING_LINE]
    assert gate_suite.refusal_lines(refused)[1:] == gate_suite.refusal_lines(
        refused, case_text=chosen)[1:]


# --- a recorded owner's-Mac decision (CP-709 to CP-711) -----------------------------------------


def mac_decision(**fields) -> dict:
    return {"environment": "owners-mac", "source": source(anchor="jobs:"), **fields}


@pytest.mark.parametrize("ci", [ci_readable("linux"), ci_readable("macos"),
                                ci_readable("macos", "linux"), ci_readable("windows")])
@pytest.mark.parametrize("status", [0, 3])
def test_recorded_mac_decision_runs_the_cards_command(ci, status):
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(status, "o\n", "e\n")
    result = harness.run(raw=raw_input(ci=ci, override=mac_decision()))
    assert harness.first_line == f"Environment: owners-mac {DASH} product's decision"
    assert harness.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]
    assert harness.processes.probes == [] and harness.processes.pipes == []
    assert harness.lock.holds == 0
    assert result.status == status and result.suite_issued
    assert harness.out.getvalue() == f"Environment: owners-mac {DASH} product's decision\no\n"
    assert harness.err.getvalue() == "e\n"


def test_recorded_mac_decision_keeps_existing_precedence():
    bad = mac_decision(source=source(anchor=MISSING_QUOTE))
    failed = Harness()
    result = failed.run(raw=raw_input(override=bad))
    assert failed.out.getvalue() == (
        f"Environment: unresolved {DASH} {failed_override_text(CI_FILE)}\n")
    assert_refused_without_running(failed, result)

    for ci in (CI_UNREADABLE, {"finding": "readable", "runners": []},
               {"finding": "readable", "runners": [
                   {"platform": "linux", "source": source(anchor=MISSING_QUOTE)}]}):
        unreadable = Harness()
        result = unreadable.run(raw=raw_input(ci=ci, override=mac_decision()))
        assert unreadable.first_line == (
            f"Environment: unresolved {DASH} the runner cannot be read from the product's CI "
            "configuration")
        assert_refused_without_running(unreadable, result)

    no_ci = Harness()
    no_ci.run(raw=raw_input(ci=CI_NONE, override=mac_decision()))
    assert no_ci.first_line == f"Environment: owners-mac {DASH} no CI"

    asked = Harness()
    asked.run(raw=raw_input(override=mac_decision()), owners_ask=True)
    assert asked.first_line == f"Environment: owners-mac {DASH} owner's ask"


# --- exit propagation ----------------------------------------------------------------------------


@pytest.mark.parametrize("status", [0, 1, 2, 7, 137])
def test_suite_exit_is_propagated(status):
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(status, "o\n", "e\n")
    result = harness.run(raw=mac_raw())
    assert result.status == status and result.suite_issued
    assert result.environment_line == f"Environment: owners-mac {DASH} no CI"
    assert (result.command, result.cwd) == (CARD_COMMAND, WORKTREE)
    assert (result.stdout, result.stderr) == ("o\n", "e\n")


# --- no-suite policies ---------------------------------------------------------------------------


@pytest.mark.parametrize("gate", ["developer", "code-integrity"])
def test_no_suite_policy_needs_no_sources_or_probes(gate):
    harness = Harness(card="**Test command:** none   <!-- no code -->\n")
    result = harness.run(gate=gate, raw=None)
    assert harness.out.getvalue() == f"Environment: none {DASH} no suite\n"
    assert result.status == 0 and not result.suite_issued
    assert harness.processes.probes == [] and harness.processes.issued == []


@pytest.mark.parametrize("command", ["none", "N/A", "validated by use", "skill-evals"])
def test_seal_no_command_forms_print_the_seal_line(command):
    harness = Harness(card=f"**Test command:** {command}\n")
    result = harness.run(gate="seal", raw=None)
    assert harness.out.getvalue() == f"Environment: none {DASH} no suite ran\n"
    assert not result.suite_issued and harness.processes.probes == []


def test_seal_fixed_topology_runs_no_suite_whatever_the_card_says():
    harness = Harness(kind="fixed")
    result = harness.run(gate="seal", raw=container_raw())
    assert harness.out.getvalue() == f"Environment: none {DASH} no suite ran\n"
    assert not result.suite_issued and harness.processes.issued == []


def test_the_developer_gate_treats_only_none_as_no_suite():
    harness = Harness(card="**Test command:** N/A\n")
    harness.run(raw=mac_raw())
    assert harness.processes.issued == [(["sh", "-c", "N/A"], WORKTREE)]


# --- the CLI -------------------------------------------------------------------------------------


def run_cli(harness: Harness, *args: str, inputs: dict | None = None):
    argv = ["run", "--worktree", WORKTREE, "--project", PROJECT, "--key", "key1", *args]
    if inputs is not None:
        path = Path("/tmp/inputs.json")
        harness.files.files[path] = json.dumps(inputs)
        argv += ["--inputs", str(path)]
    return gate_suite.main(argv, host=harness.host, stdout=harness.out, stderr=harness.err)


def test_the_cli_runs_a_gate_and_returns_the_suite_status():
    harness = Harness()
    harness.processes.suite = gate_suite.Completed(5, "out\n", "")
    assert run_cli(harness, "--gate", "developer", inputs=mac_raw()) == 5
    assert harness.first_line == f"Environment: owners-mac {DASH} no CI"


def test_the_cli_owner_option_needs_no_inputs():
    harness = Harness()
    assert run_cli(harness, "--gate", "seal", "--owners-mac") == 0
    assert harness.first_line == f"Environment: owners-mac {DASH} owner's ask"


def test_the_cli_owner_ask_is_not_read_from_the_input_json():
    harness = Harness()
    raw = container_raw()
    raw["owners_mac"] = True
    raw["owners_ask"] = True
    assert run_cli(harness, "--gate", "developer", inputs=raw) == 0
    assert harness.first_line.startswith("Environment: container")


def test_cli_refuses_missing_card_or_path_contract():
    no_card = Harness()
    no_card.files.files.pop(Path(WORKTREE) / "system/projects/demo/project.md")
    assert run_cli(no_card, "--gate", "developer", "--owners-mac") != 0
    assert no_card.out.getvalue() == "" and no_card.processes.issued == []
    assert no_card.err.getvalue().startswith("gate_suite: ")

    no_command = Harness(card="**Product path:** .claude\n")
    assert run_cli(no_command, "--gate", "seal", "--owners-mac") != 0
    assert no_command.processes.issued == [] and no_command.out.getvalue() == ""

    broken = Harness()

    def refuse(worktree, project, key):
        raise gate_suite.ContractError("missing-project-doc: no project.md")

    broken.host = gate_suite.Host(files=broken.files, contract=refuse, processes=broken.processes,
                                  new_token=lambda: TOKEN, core_root=CORE,
                                  guest_lock=broken.lock)
    assert run_cli(broken, "--gate", "developer", "--owners-mac") != 0
    assert broken.out.getvalue() == "" and broken.processes.issued == []
    assert "missing-project-doc" in broken.err.getvalue()


def test_the_cli_refuses_an_unreadable_inputs_file_and_an_unknown_gate():
    harness = Harness()
    assert run_cli(harness, "--gate", "developer", "--inputs", "/nope.json") != 0
    assert harness.processes.issued == [] and harness.out.getvalue() == ""
    with pytest.raises(SystemExit):
        run_cli(Harness(), "--gate", "sealing")


def test_pure_resolution_issues_no_subprocess():
    # The resolver is called with no host at all; a subprocess would have nothing to run on.
    assert resolve(raw_input()).kind is EnvironmentKind.CONTAINER


# ==================================================================================================
# Code integrity: intent the first pass left untested
# ==================================================================================================


@pytest.mark.parametrize("finding", [{"finding": "none"}, {"finding": "none", "inventory": "  "}])
def test_a_no_ci_finding_without_its_inventory_is_unreadable_not_no_ci(finding):
    # CP-620: `none` is a finding, never the absence of an answer, and design § 3 A makes it
    # require a reviewed repository inventory. A bare `none` is no evidence of absence.
    result = resolve(raw_input(ci=finding))
    assert isinstance(result, Refused) and result.case is RefusalCase.UNREADABLE_CI


MATRIX_CI_TEXT = CI_TEXT + '      - python-version: "3.13"\n'


@pytest.mark.parametrize("versions", [("3.12", "3.13"), ("3.13", "3.12")])
def test_one_language_at_several_versions_refuses_whatever_their_order(versions):
    # CP-619(e) and design T1: a version matrix that cannot yield one version refuses — the
    # resolver never keeps whichever candidate came first or last.
    files = standard_files(**{CI_FILE: MATRIX_CI_TEXT})
    candidates = [candidate("python", tag=version,
                            tag_source=source(CI_FILE, f'python-version: "{version}"'))
                  for version in versions]
    result = resolve(raw_input(candidates=candidates), files=files)
    assert isinstance(result, Refused) and result.case is RefusalCase.UNDETERMINED_VERSION


def test_one_language_named_twice_at_one_version_collapses():
    result = resolve(raw_input(candidates=[candidate("python"), candidate("python")]))
    assert result == container("python", "3.12")


@pytest.mark.parametrize("kind, product_path, product_repo, expected_root", [
    ("relative", ".claude", "/work/instance", f"{WORKTREE}/.claude"),
    ("relative", "/work/instance/products/demo", "/work/instance", f"{WORKTREE}/products/demo"),
    ("fixed", "/work/product-repo", "/work/product-repo", PRODUCT_WORKTREE),
    ("fixed", "/work/product-repo/app", "/work/product-repo", f"{PRODUCT_WORKTREE}/app"),
])
def test_language_inference_reads_the_products_own_tree_not_the_whole_repository(
        kind, product_path, product_repo, expected_root):
    # CP-620: the product's languages are the ones the resolution chain resolves *for the
    # product* — step 3 infers from the tracked files under the product's own tree, not from
    # every file of the repository that holds it (an in-repo product shares it with the instance).
    harness = Harness(kind=kind)
    harness.contract.update(product_path=product_path, product_repo=product_repo)
    asked: list[Path] = []

    def tracked(root: Path) -> list[str]:
        asked.append(Path(root))
        if Path(root) == Path(expected_root):
            return ["hooks/hook.js"]
        return ["core/tools/run.py", "core/launchers/run.sh", "hooks/hook.js"]

    harness.files.tracked_files = tracked
    raw = raw_input(languages=("javascript",))
    raw["languages"] = {"declared": None, "invoked": None}

    harness.run(raw=raw)

    assert asked == [Path(expected_root)]
    assert harness.first_line == f"Environment: container {DASH} node:22, arm64"


# ==================================================================================================
# One guest serves every run (CP-632 to CP-642): fixed shares, the mapped folder, the lock
# ==================================================================================================

import errno
import fcntl
import multiprocessing
import os
import subprocess
import sys
import tempfile
import threading
import time

from gate_suite import Share

GUEST_NAME = "swift-guest"
PRODUCTS_FOLDER = "/Volumes/My Shared Files/products"
UNSHARED_LINES = (
    "gate_suite: this run's checkout, {checkout}, is under none of the shares this run was given "
    "for the macOS guest {guest}.")
CLOSING = "The test command was not run, on the owner's Mac or anywhere else."


def token_name() -> str:
    return f".gate_suite_token_{TOKEN}"


def mapped_run(run_folder: str, guest: dict | None = None, **harness_kwargs) -> Harness:
    """A guest run from `run_folder` — an external product's worktree under the products share —
    already run."""
    harness = Harness(kind="fixed", run_folder=run_folder, **harness_kwargs)
    harness.run(raw=guest_raw(guest))
    return harness


def assert_free(path: Path) -> None:
    """The lock file can be taken at once, so nothing still holds it."""
    descriptor = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(descriptor)


def assert_busy(path: Path) -> None:
    descriptor = os.open(path, os.O_RDWR)
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(descriptor)


def finishes_within(seconds: float, call) -> tuple[bool, object]:
    """Run `call` on a thread. A call that waits on a lock must not hang the suite."""
    box: list = []
    worker = threading.Thread(target=lambda: box.append(call()), daemon=True)
    worker.start()
    worker.join(seconds)
    return (not worker.is_alive(), box[0] if box else None)


# --- CP-632: the complete fixed share set, whichever run it comes from ---------------------------


def test_named_guest_accepts_the_complete_fixed_share_set():
    expected = gate_suite.Guest(GUEST_NAME, (Share("/work/products", PRODUCTS_FOLDER),
                                             Share("/work/instance",
                                                   "/Volumes/My Shared Files/instance")))
    for product, core in ((PRODUCT, CORE), (Path("/other/instance/product"), Path("/pin/core"))):
        files = FakeFiles({product / CI_FILE: CI_TEXT, core / PACKET_DIR / "README.md":
                           REGISTRY_TEXT})
        request = gate_suite.parse_request(
            copy.deepcopy(raw_input(ci=ci_readable("macos"))), files=files,
            product_checkout=product, language_root=product, core_root=core, project=PROJECT)
        assert request.guest == expected
    assert isinstance(request.guest.shares, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.guest.shares[0].host = "/elsewhere"


@pytest.mark.parametrize("guest", [
    {"name": GUEST_NAME},
    {"name": GUEST_NAME, "shares": None},
    {"name": GUEST_NAME, "shares": []},
    {"name": GUEST_NAME, "share": "/Volumes/My Shared Files/checkout"},
], ids=["absent", "null", "empty", "retired-scalar"])
def test_named_guest_without_shares_is_unshared_not_missing(guest):
    assert request_from(guest_raw(guest)).guest == gate_suite.Guest(GUEST_NAME, ())
    harness = Harness()
    result = harness.run(raw=guest_raw(guest))
    assert result.status == 1
    assert harness.first_line == f"Environment: macos-guest {DASH} {GUEST_NAME}"
    assert harness.err.getvalue() == (
        UNSHARED_LINES.format(checkout=WORKTREE, guest=GUEST_NAME) + "\n"
        "This run was given no shares for the guest. Each share is given in guest.shares, with "
        "the host folder and the folder it appears at inside the guest.\n" + CLOSING + "\n")


@pytest.mark.parametrize("guest", [None, {}, {"shares": [PRODUCTS_SHARE]}, {"name": ""}])
def test_no_name_is_no_guest_whatever_else_was_given(guest):
    assert request_from(guest_raw(guest) if guest is not None
                        else raw_input(ci=ci_readable("macos"), guest=None)).guest is None
    harness = Harness()
    raw = raw_input(ci=ci_readable("macos"), guest=guest)
    assert harness.run(raw=raw).status != 0
    assert harness.first_line == f"Environment: macos-guest {DASH} no guest given"
    assert "gate_suite: this run was given no macOS guest to run in." in harness.err.getvalue()
    assert harness.processes.probes == [] and harness.lock.holds == 0


# --- CP-633 to CP-636: the run's folder reached through its share --------------------------------

LOCAL = Share("/h/products", PRODUCTS_FOLDER)
NESTED = Share("/h/products/widget-app", "/Volumes/My Shared Files/ka")
HOME_INSTANCE = Share("/h/kensai/host-instance", "/Volumes/My Shared Files/host-instance")


def test_two_worktrees_use_one_guest_without_restart():
    first = "/work/products/widget-app/.worktrees/k1"
    second = "/work/products/widget-app/.worktrees/k2"
    for folder in (first, second):
        harness = mapped_run(folder)
        in_guest = f"{PRODUCTS_FOLDER}/widget-app/.worktrees/{folder.rsplit('/', 1)[1]}"
        assert harness.processes.probes == [
            ["tart", "list", "--format", "json"],
            ["tart", "exec", GUEST_NAME, "true"],
            ["tart", "exec", GUEST_NAME, "sh", "-c",
             f"test -f {shlex.quote(in_guest + '/' + token_name())}"],
            ["tart", "exec", GUEST_NAME, "sh", "-c", "command -v python3"],
            ["tart", "exec", GUEST_NAME, "sh", "-c", CLEAN]]
        assert harness.processes.pipes == [
            (packed(folder), ["tart", "exec", "-i", GUEST_NAME, "sh", "-c", COPY], folder)]
        assert harness.processes.issued == [
            (["tart", "exec", GUEST_NAME, "sh", "-c",
              f"cd {shlex.quote(SCRATCH)} && {CARD_COMMAND}"], folder)]
        assert harness.first_line == f"Environment: macos-guest {DASH} {GUEST_NAME}"
        assert harness.files.written == [Path(folder) / token_name()]
    # An in-repo product's worktree is reached through the instance repository's share.
    in_repo = Harness()
    in_repo.run(raw=guest_raw())
    assert in_repo.processes.probes[-3][-1] == (
        f"test -f {shlex.quote(MAPPED + '/' + token_name())}")
    assert in_repo.processes.issued[0][0][-1] == f"cd {shlex.quote(SCRATCH)} && {CARD_COMMAND}"


@pytest.mark.parametrize("shares,folder,expected", [
    ([LOCAL], "/h/products", PRODUCTS_FOLDER),
    ([LOCAL], "/h/products/a/b", f"{PRODUCTS_FOLDER}/a/b"),
    ([Share("/h/products/", PRODUCTS_FOLDER)], "/h/products/a", f"{PRODUCTS_FOLDER}/a"),
    ([LOCAL], "/h/products/a/", f"{PRODUCTS_FOLDER}/a"),
    ([Share("/h/products/", PRODUCTS_FOLDER)], "/h/products/", PRODUCTS_FOLDER),
    ([LOCAL, NESTED], "/h/products/widget-app/.worktrees/k1",
     "/Volumes/My Shared Files/ka/.worktrees/k1"),
    ([NESTED, LOCAL], "/h/products/widget-app/.worktrees/k1",
     "/Volumes/My Shared Files/ka/.worktrees/k1"),
    ([NESTED, LOCAL], "/h/products/widget-app", "/Volumes/My Shared Files/ka"),
    ([LOCAL, NESTED], "/h/products/other/x", f"{PRODUCTS_FOLDER}/other/x"),
    ([LOCAL, HOME_INSTANCE], "/h/kensai/host-instance/.worktrees/k3",
     "/Volumes/My Shared Files/host-instance/.worktrees/k3"),
])
def test_mapping_uses_the_deepest_component_ancestor(shares, folder, expected):
    assert gate_suite.map_run_folder(tuple(shares), folder) == expected


@pytest.mark.parametrize("folder", ["/h/products2/x", "/h/products2", "/h/product", "/h",
                                    "/Users/o/scratch/w", "relative/path"])
def test_mapping_refuses_sibling_prefixes(folder):
    assert gate_suite.map_run_folder((LOCAL, HOME_INSTANCE), folder) is None


def test_mapping_does_not_resolve_symlinks(tmp_path):
    real = tmp_path / "real"
    (real / "x").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real)
    share = Share(str(real), PRODUCTS_FOLDER)
    assert gate_suite.map_run_folder((share,), str(real / "x")) == f"{PRODUCTS_FOLDER}/x"
    assert gate_suite.map_run_folder((share,), str(link / "x")) is None
    assert gate_suite.map_run_folder((Share(str(link), PRODUCTS_FOLDER),), str(real / "x")) is None


def test_a_folder_with_spaces_reaches_the_guest_shell_as_one_word():
    harness = Harness(kind="fixed", run_folder="/work/products/a b/.worktrees/k1")
    harness.run(raw=guest_raw())
    in_guest = f"{PRODUCTS_FOLDER}/a b/.worktrees/k1"
    assert harness.processes.probes[-3][-1] == f"test -f '{in_guest}/{token_name()}'"
    assert harness.processes.pipes[0][0] == packed("/work/products/a b/.worktrees/k1")


# --- CP-637: a folder under no share -------------------------------------------------------------

UNSHARED_RAWS = {
    "no match": {"name": GUEST_NAME, "shares": [PRODUCTS_SHARE]},
    "absent": {"name": GUEST_NAME},
    "empty": {"name": GUEST_NAME, "shares": []},
}


def test_unshared_run_refuses_before_lock_and_probes():
    for name, guest in UNSHARED_RAWS.items():
        harness = Harness()
        result = harness.run(raw=guest_raw(guest))
        assert result.status == 1 and not result.suite_issued, name
        assert harness.first_line == f"Environment: macos-guest {DASH} {GUEST_NAME}", name
        assert harness.out.getvalue() == harness.first_line + "\n", name
        assert harness.processes.probes == [] and harness.processes.issued == [], name
        assert harness.lock.holds == 0 and harness.files.written == [], name
        lines = harness.err.getvalue().splitlines()
        assert lines[0] == UNSHARED_LINES.format(checkout=WORKTREE, guest=GUEST_NAME), name
        assert lines[-1] == CLOSING, name
    with_shares = Harness()
    with_shares.run(raw=guest_raw(UNSHARED_RAWS["no match"]))
    assert with_shares.err.getvalue().splitlines()[1:] == [
        "The shares this run was given: /work/products.",
        "The checkout has to be under one of those folders, or the guest has to be started with "
        "a share that holds it.", CLOSING]


def test_the_refusal_lists_every_host_folder_as_given_in_order():
    harness = Harness()
    harness.run(raw=guest_raw({"name": GUEST_NAME, "shares": [
        {"host": "/h/b/", "guest": "/g/b"}, {"host": "/h/a", "guest": "/g/a"}]}))
    assert harness.err.getvalue().splitlines()[1] == "The shares this run was given: /h/b/, /h/a."


def test_a_refusal_completes_while_a_different_guest_run_holds_the_lock(tmp_path):
    lock_file = tmp_path / "guest.lock"
    holder = gate_suite.FileGuestLock(lock_file)
    harness = Harness(guest_lock=gate_suite.FileGuestLock(lock_file))
    with holder.hold():
        done, result = finishes_within(
            5, lambda: harness.run(raw=guest_raw(UNSHARED_RAWS["no match"])))
    assert done and result.status == 1
    assert harness.processes.probes == []


# --- CP-638: shares that cannot place a folder ---------------------------------------------------

GOOD = {"host": "/h/products", "guest": PRODUCTS_FOLDER}
MALFORMED = [
    ("a string", "nope", "guest.shares must be a list"),
    ("an object", {"host": "/h"}, "guest.shares must be a list"),
    ("a number", 5, "guest.shares must be a list"),
    ("a scalar share", [5], "guest.shares[0] must be an object"),
    ("a list share", [["/h"]], "guest.shares[0] must be an object"),
    ("a null share", [None], "guest.shares[0] must be an object"),
    ("no host", [{"guest": "/g"}], "guest.shares[0] must name its host folder"),
    ("empty host", [{"host": "", "guest": "/g"}], "guest.shares[0] must name its host folder"),
    ("null host", [{"host": None, "guest": "/g"}], "guest.shares[0] must name its host folder"),
    ("numeric host", [{"host": 5, "guest": "/g"}], "guest.shares[0].host must be text"),
    ("relative host", [{"host": "products", "guest": "/g"}],
     "guest.shares[0].host must be an absolute path, not products"),
    ("no guest folder", [{"host": "/h"}],
     "guest.shares[0] must name the folder it appears at inside the guest"),
    ("empty guest folder", [{"host": "/h", "guest": ""}],
     "guest.shares[0] must name the folder it appears at inside the guest"),
    ("numeric guest folder", [{"host": "/h", "guest": 5}], "guest.shares[0].guest must be text"),
    ("second share bad", [GOOD, {"host": "x", "guest": "/g"}],
     "guest.shares[1].host must be an absolute path, not x"),
    ("duplicate host", [GOOD, {"host": "/h/products", "guest": "/g"}],
     "guest.shares[0] and guest.shares[1] name the same host folder, /h/products"),
    ("duplicate with a trailing slash", [GOOD, {"host": "/h/products/", "guest": "/g"}],
     "guest.shares[0] and guest.shares[1] name the same host folder, /h/products/"),
    ("the host is checked first", [{"host": "p"}],
     "guest.shares[0].host must be an absolute path, not p"),
]


@pytest.mark.parametrize("shares,message", [case[1:] for case in MALFORMED],
                         ids=[case[0] for case in MALFORMED])
def test_malformed_shares_are_input_errors_without_side_effects(shares, message):
    harness = Harness()
    raw = guest_raw({"name": GUEST_NAME, "shares": shares})
    assert run_cli(harness, "--gate", "developer", inputs=raw) == 2
    assert harness.err.getvalue() == f"gate_suite: {message}\n"
    assert harness.out.getvalue() == ""
    assert harness.processes.probes == [] and harness.processes.issued == []
    assert harness.lock.holds == 0 and harness.files.written == []


# --- CP-635: readiness at the mapped folder, and what it keeps -----------------------------------


def test_mapped_readiness_retains_existing_failure_contracts():
    for name in ("missing guest", "unreachable guest", "invisible token"):
        harness = _guest_outcomes()[name]
        assert harness.processes.issued == [], name
        assert harness.err.getvalue().endswith(CLOSING + "\n"), name
    invisible = _guest_outcomes()["invisible token"]
    assert (f"the macOS guest {GUEST_NAME} cannot see this run's checkout, {WORKTREE}."
            in invisible.err.getvalue())
    stopped = Harness()
    stopped.processes.when("tart", "list", result=gate_suite.Completed(
        0, json.dumps([{"Name": GUEST_NAME, "State": "stopped"}]), ""))
    assert stopped.run(raw=guest_raw()).status == 1
    assert f"gate_suite: the macOS guest {GUEST_NAME} is not running." in stopped.err.getvalue()
    assert stopped.processes.probes == [["tart", "list", "--format", "json"]]


# --- CP-641: one guest run at a time -------------------------------------------------------------


def _record(path: str, role: str, what: str) -> None:
    with open(path, "a") as log:
        log.write(f"{role} {what}\n")
        log.flush()


class _LoggedProcesses(FakeProcesses):
    def __init__(self, events: Events, role: str, log: str, release: str, status: int) -> None:
        super().__init__(events)
        self.role, self.log, self.release = role, log, release
        self.suite = gate_suite.Completed(status, f"{role} out\n", "")

    def probe(self, argv: list[str]):
        _record(self.log, self.role, "probe")
        return super().probe(argv)

    def issue(self, argv: list[str], *, cwd: str):
        _record(self.log, self.role, "suite-start")
        while self.role == "A" and not os.path.exists(self.release):
            time.sleep(0.01)
        _record(self.log, self.role, "suite-end")
        return super().issue(argv, cwd=cwd)


class _AnnouncedLock(gate_suite.FileGuestLock):
    def __init__(self, path: Path, announce) -> None:
        super().__init__(path)
        self._announce = announce

    def hold(self):
        self._announce("lock-attempt")
        return super().hold()


def _guest_process(role: str, lock_file: str, log: str, release: str, status: int, results):
    """One independent gate process: its own host, its own lock adapter, the shared lock file."""
    harness = Harness()
    harness.processes = _LoggedProcesses(harness.events, role, log, release, status)
    host = gate_suite.Host(
        files=harness.files, contract=lambda worktree, project, key: harness.contract,
        processes=harness.processes, new_token=lambda: TOKEN, core_root=CORE,
        guest_lock=_AnnouncedLock(Path(lock_file), lambda what: _record(log, role, what)))
    harness.host = host
    result = harness.run(raw=guest_raw())
    results.put((role, result.status, harness.out.getvalue(), harness.err.getvalue()))


def _wait_for(log: Path, line: str, seconds: float = 30) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if log.exists() and line in log.read_text().splitlines():
            return True
        time.sleep(0.01)
    return False


def test_independent_guest_processes_wait_for_suite_completion(tmp_path):
    lock_file, log, release = (str(tmp_path / name) for name in ("guest.lock", "log", "release"))
    context = multiprocessing.get_context("spawn")
    results = context.Queue()
    first = context.Process(target=_guest_process,
                            args=("A", lock_file, log, release, 3, results))
    second = context.Process(target=_guest_process,
                             args=("B", lock_file, log, release, 0, results))
    first.start()
    try:
        assert _wait_for(Path(log), "A suite-start")
        second.start()
        assert _wait_for(Path(log), "B lock-attempt")
        # B has asked for the lock while A's suite is still running: it must issue nothing.
        time.sleep(0.5)
        assert [line for line in Path(log).read_text().splitlines()
                if line.startswith("B ") and line != "B lock-attempt"] == []
        Path(release).touch()
        outcomes = {role: rest for role, *rest in (results.get(timeout=60) for _ in range(2))}
    finally:
        Path(release).touch()
        for process in (first, second):
            process.join(timeout=30)
            if process.is_alive():
                process.kill()
    events = Path(log).read_text().splitlines()
    assert events.index("A suite-end") < min(
        i for i, event in enumerate(events) if event.startswith("B ") and event != "B lock-attempt")
    # What each run printed and returned is what it would have been alone.
    for role, status in (("A", 3), ("B", 0)):
        alone = Harness()
        alone.processes.suite = gate_suite.Completed(status, f"{role} out\n", "")
        assert alone.run(raw=guest_raw()).status == status
        assert outcomes[role] == [status, alone.out.getvalue(), alone.err.getvalue()]


def test_the_lock_is_held_from_before_the_first_guest_process_until_cleanup_is_done():
    harness = Harness()
    harness.run(raw=guest_raw())
    log = harness.events.log
    kinds = [entry[:2] for entry in log]
    acquire, release = kinds.index(("lock", "acquire")), kinds.index(("lock", "release"))
    first_guest = min(i for i, entry in enumerate(kinds) if entry[0] in ("process", "files"))
    last_guest = max(i for i, entry in enumerate(kinds) if entry[0] in ("process", "files"))
    assert acquire < first_guest and release > last_guest
    assert kinds[last_guest] == ("files", "remove")
    assert log[0] == ("stdout", "write", f"Environment: macos-guest {DASH} {GUEST_NAME}\n")
    assert kinds.count(("lock", "acquire")) == 1 == kinds.count(("lock", "release"))


@pytest.mark.parametrize("outcome", ["success", "readiness", "suite-exception"])
def test_guest_lock_is_released_on_every_exit(tmp_path, outcome):
    lock_file = tmp_path / "guest.lock"
    harness = Harness(guest_lock=gate_suite.FileGuestLock(lock_file))
    if outcome == "readiness":
        harness.processes.when("tart", "list", result=gate_suite.Completed(0, "[]", ""))
    if outcome == "suite-exception":
        harness.processes.suite_error = RuntimeError("runner died")
        with pytest.raises(RuntimeError):
            harness.run(raw=guest_raw())
    else:
        harness.run(raw=guest_raw())
    assert_free(lock_file)


_HOLDER = """
import pathlib, subprocess, sys, time
import gate_suite
with gate_suite.FileGuestLock(pathlib.Path(sys.argv[1])).hold():
    if sys.argv[3] == "child":
        # close_fds=False passes on every descriptor that is marked inheritable.
        child = subprocess.Popen(["sleep", "30"], close_fds=False)
        pathlib.Path(sys.argv[2]).write_text(str(child.pid))
    else:
        pathlib.Path(sys.argv[2]).write_text("held")
        time.sleep(60)
"""


def _start_holder(tmp_path: Path, mode: str) -> tuple[subprocess.Popen, Path, Path]:
    lock_file, marker = tmp_path / "guest.lock", tmp_path / "marker"
    environment = {**os.environ, "PYTHONPATH": str(Path(gate_suite.__file__).parent)}
    process = subprocess.Popen([sys.executable, "-c", _HOLDER, str(lock_file), str(marker), mode],
                               env=environment)
    deadline = time.monotonic() + 30
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    return process, lock_file, marker


def test_guest_lock_is_released_when_the_holding_process_is_terminated(tmp_path):
    process, lock_file, _marker = _start_holder(tmp_path, "wait")
    try:
        assert_busy(lock_file)
        process.kill()
        process.wait(timeout=30)
        assert_free(lock_file)
    finally:
        process.kill()


def test_guest_lock_descriptor_is_not_inherited_by_a_launched_child(tmp_path):
    process, lock_file, marker = _start_holder(tmp_path, "child")
    try:
        process.wait(timeout=30)
        # The holder has left its lock; its child, launched while it held it, is still alive.
        child = int(marker.read_text())
        os.kill(child, 0)
        assert_free(lock_file)
    finally:
        with contextlib.suppress(OSError):
            os.kill(int(marker.read_text()), 9)


def test_guest_lock_file_inode_is_stable_across_holds(tmp_path):
    lock_file = tmp_path / "guest.lock"
    lock = gate_suite.FileGuestLock(lock_file)
    with lock.hold():
        first = lock_file.stat().st_ino
    with gate_suite.FileGuestLock(lock_file).hold():
        assert lock_file.stat().st_ino == first
    assert lock_file.exists() and lock_file.stat().st_ino == first


def test_guest_lock_identity_spans_core_copies(tmp_path, monkeypatch):
    lock_file = tmp_path / "guest.lock"
    held = threading.Event()
    release = threading.Event()
    acquired = threading.Event()

    def other_copy() -> None:
        held.set()
        with gate_suite.FileGuestLock(lock_file).hold():
            acquired.set()

    with gate_suite.FileGuestLock(lock_file).hold():
        worker = threading.Thread(target=other_copy, daemon=True)
        worker.start()
        assert held.wait(5)
        assert not acquired.wait(0.3)
    assert acquired.wait(5)
    worker.join(5)
    release.set()
    monkeypatch.setenv("TMPDIR", str(tmp_path / "elsewhere"))
    production = gate_suite.build_host().guest_lock
    assert production.path == Path("/tmp/kensaiapp-macos-guest.lock")
    assert gate_suite.GUEST_LOCK_PATH == "/tmp/kensaiapp-macos-guest.lock"


def test_guest_lock_acquisition_error_issues_no_process(tmp_path):
    missing = tmp_path / "no-such-folder" / "guest.lock"
    harness = Harness(guest_lock=gate_suite.FileGuestLock(missing))
    assert run_cli(harness, "--gate", "developer", inputs=guest_raw()) == 2
    reason = os.strerror(errno.ENOENT)
    assert harness.err.getvalue() == (
        "gate_suite: the lock that lets one gate at a time run in the macOS guest cannot be "
        f"taken, at {missing}: {reason}\n")
    assert harness.first_line == f"Environment: macos-guest {DASH} {GUEST_NAME}"
    assert harness.processes.probes == [] and harness.processes.issued == []
    assert harness.files.written == []


# --- CP-642: no other environment takes the lock -------------------------------------------------


def test_non_guest_runs_bypass_a_held_guest_lock(tmp_path):
    lock_file = tmp_path / "guest.lock"
    with gate_suite.FileGuestLock(lock_file).hold():
        box = Harness(guest_lock=gate_suite.FileGuestLock(lock_file))
        done, _ = finishes_within(5, lambda: box.run(raw=container_raw()))
        assert done
        assert box.processes.probes == [["podman", "info"]]
        assert box.processes.issued == [(["podman", "run", "--rm", "-v", f"{WORKTREE}:/work", "-w",
                                          "/work", "python:3.12", "sh", "-c", CARD_COMMAND],
                                         WORKTREE)]
        mac = Harness(guest_lock=gate_suite.FileGuestLock(lock_file))
        done, _ = finishes_within(5, lambda: mac.run(raw=mac_raw()))
        assert done and mac.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]
        asked = Harness(guest_lock=gate_suite.FileGuestLock(lock_file))
        done, _ = finishes_within(5, lambda: asked.run(raw=None, owners_ask=True))
        assert done and asked.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]


def test_no_suite_and_unresolved_runs_never_enter_the_lock():
    cases = {
        "no suite": Harness(card=card_text("none")),
        "unresolved": Harness(),
        "container": Harness(),
        "owners-mac": Harness(),
    }
    cases["no suite"].run(raw=guest_raw())
    cases["unresolved"].run(raw=raw_input(ci=CI_UNREADABLE))
    cases["container"].run(raw=container_raw())
    cases["owners-mac"].run(raw=mac_raw())
    for name, harness in cases.items():
        assert harness.lock.holds == 0, name
    assert cases["no suite"].first_line == f"Environment: none {DASH} no suite"
    assert cases["unresolved"].first_line.startswith("Environment: unresolved")
    guest = Harness()
    guest.run(raw=guest_raw())
    assert guest.lock.holds == 1


# --- the shipped packets: each language a macOS-CI product holds names its guest tool -------------

_SHIPPED_PACKETS = Path(__file__).resolve().parent.parent / PACKET_DIR


@pytest.mark.parametrize("language,tool,folder", [
    ("rust", "cargo", "/Users/admin/.cargo/bin"),
    ("swift", "swift", None),
    ("shell", "bash", None),
    ("python", "python3", None),
    ("javascript", "node", None),
    ("typescript", "node", None),
])
def test_each_shipped_guest_packet_names_its_tool(language, tool, folder):
    text = (_SHIPPED_PACKETS / language / "environment.md").read_text(encoding="utf-8")
    assert gate_suite.guest_tool(language, text) == gate_suite.GuestTool(language, tool, folder)


# --- the shipped packets name their container image (CP-726 to CP-738) ---------------------------
#
# The reader below is test support. It does what `prompts/gate_suite.md` Step 3 asks of a plan:
# take the image a packet names, with the packet line that names it as the image's source. The
# tool never reads a packet itself, so nothing here is a runtime parser.

_REGISTRY_REFERENCE = r"(?:docker\.io|quay\.io|ghcr\.io|mcr\.microsoft\.com)/[a-z0-9._/-]+"
_PROVISIONING_HEADING = "## Provisioning"
_EXAMPLE_MARKERS = ("for example", "such as", "e.g.")
_FENCE = "```"
_VERSION = re.compile(r"\d+(?:\.\d+)*")
_SHIPPED_LANGUAGES = ("python", "rust", "javascript", "typescript", "shell", "swift")


@dataclasses.dataclass(frozen=True)
class PacketImage:
    """The image a shipped packet names and the whole packet line that names it. Both are `None`
    when the packet names none, which a plan gives its candidate as no `image`."""

    reference: str | None
    line: str | None


def _shipped_text(language: str) -> str:
    return (_SHIPPED_PACKETS / language / "environment.md").read_text(encoding="utf-8")


def _provisioning_prose(text: str):
    """The lines of `## Provisioning` that are ordinary prose, outside any fenced block."""
    in_provisioning = False
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(_FENCE):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            in_provisioning = line.strip() == _PROVISIONING_HEADING
        elif in_provisioning and not in_fence:
            yield line


def read_packet_image(text: str) -> PacketImage:
    """The first registry reference in the packet's provisioning prose that is not an example."""
    for line in _provisioning_prose(text):
        found = re.search(_REGISTRY_REFERENCE, line)
        if found and not any(marker in line.lower() for marker in _EXAMPLE_MARKERS):
            return PacketImage(found.group(0), line.strip())
    return PacketImage(None, None)


def shipped_ci_text(runner: str) -> str:
    return ("jobs:\n  test:\n"
            f"    runs-on: {runner}\n"
            "    steps:\n"
            '      - python-version: "3.12"\n'
            "      - node-version: 22\n")


def ci_line(ci_text: str, fragment: str) -> str:
    return next(line.strip() for line in ci_text.splitlines() if fragment in line)


def shipped_files(ci_text: str) -> FakeFiles:
    """The product's CI and the shipped registry and packets, read from the checkout under test."""
    files = {PRODUCT / CI_FILE: ci_text,
             CORE / PACKET_DIR / "README.md": (_SHIPPED_PACKETS / "README.md").read_text("utf-8")}
    for language in _SHIPPED_LANGUAGES:
        files[CORE / PACKET_DIR / language / "environment.md"] = _shipped_text(language)
    return FakeFiles(files, tracked=["src/app.py"])


def shipped_candidate(language: str, ci_text: str, tag_fragment: str) -> dict:
    """The candidate a plan builds: the packet's image with the packet line as its source, and the
    tag CI states on `tag_fragment`'s line with that line as its source. A packet that names no
    image gives a candidate with no image; a CI line stating no version gives no tag."""
    packet = read_packet_image(_shipped_text(language))
    found = {"language": language}
    if packet.reference is None:
        return found
    found["image"] = packet.reference
    found["image_source"] = source(f"{PACKET_DIR}/{language}/environment.md", packet.line,
                                   root="core")
    tag_line = ci_line(ci_text, tag_fragment)
    tag = _VERSION.search(tag_line)
    if tag:
        found["tag"] = tag.group(0)
        found["tag_source"] = source(CI_FILE, tag_line)
    return found


def resolve_shipped(ci_text: str, candidates: list[dict], declared: list[str]):
    ci = {"finding": "readable", "runners": [
        {"platform": "linux", "source": source(anchor=ci_line(ci_text, "runs-on:"))}]}
    raw = raw_input(ci=ci, candidates=candidates, declared=declared)
    return request_from(raw, shipped_files(ci_text)), resolve(raw, files=shipped_files(ci_text))


_PACKET_IMAGE_REFERENCES = [
    pytest.param("python", "docker.io/library/python", id="python"),
    pytest.param("rust", "docker.io/library/rust", id="rust"),
    pytest.param("javascript", "docker.io/library/node", id="javascript"),
    pytest.param("typescript", "docker.io/library/node", id="typescript"),
    pytest.param("shell", "docker.io/library/ubuntu", id="shell"),
]


@pytest.mark.parametrize("language,reference", _PACKET_IMAGE_REFERENCES)
def test_shipped_container_packet_names_one_untagged_provisioning_image(language, reference):
    text = _shipped_text(language)
    # Exactly one reference in the whole file: one distinct image, written once.
    assert re.findall(_REGISTRY_REFERENCE, text) == [reference]
    [image_line] = [line for line in text.splitlines() if re.search(_REGISTRY_REFERENCE, line)]
    # It sits in ordinary provisioning prose, not in a fenced block or an example.
    assert read_packet_image(text) == PacketImage(reference, image_line.strip())
    # No tag and no digest follows it, anywhere in the file.
    assert not re.search(_REGISTRY_REFERENCE + "[:@]", text)


def test_the_packet_reader_names_no_image_where_the_provisioning_prose_holds_none():
    reference = "docker.io/library/python"
    outside_section = f"## Default\n\nThe image is `{reference}`.\n\n## Provisioning\n\nNone.\n"
    fenced = f"## Provisioning\n\n```sh\npodman pull {reference}\n```\n"
    example = f"## Provisioning\n\nFor example, `{reference}` would do.\n"
    for text in ("", outside_section, fenced, example):
        assert read_packet_image(text) == PacketImage(None, None)
    prose = f"## Provisioning\n\nStart from the image, `{reference}`, tagged by CI.\n\n## Next\n"
    assert read_packet_image(prose) == PacketImage(
        reference, f"Start from the image, `{reference}`, tagged by CI.")


def test_shipped_python_ci_version_resolves_container():
    ci_text = shipped_ci_text("ubuntu-24.04")
    request, result = resolve_shipped(
        ci_text, [shipped_candidate("python", ci_text, "python-version")], ["python"])
    # Every quoted source — the packet line and the CI line — is a line the file really holds.
    assert request.candidates[0].failed == ()
    assert result == container("docker.io/library/python", "3.12")
    assert gate_suite.environment_line(result, None) == (
        f"Environment: container {DASH} docker.io/library/python:3.12, arm64")


_SHIPPED_TAG_EVIDENCE = (("python", "python-version"), ("javascript", "node-version"),
                         ("shell", "runs-on:"))
_SHIPPED_CONFLICT_LISTING = (
    "The container images the product's languages call for: docker.io/library/python:3.12 for "
    "python, docker.io/library/node:22 for javascript, docker.io/library/ubuntu:24.04 for shell.")


def shipped_candidates(ci_text: str) -> list[dict]:
    return [shipped_candidate(language, ci_text, fragment)
            for language, fragment in _SHIPPED_TAG_EVIDENCE]


def test_shipped_python_javascript_shell_report_conflicting_images():
    ci_text = shipped_ci_text("ubuntu-24.04")
    request, result = resolve_shipped(ci_text, shipped_candidates(ci_text),
                                      ["python", "javascript", "shell"])
    assert isinstance(result, Refused)
    assert result.case is RefusalCase.CONFLICTING_IMAGES
    assert [candidate.failed for candidate in request.candidates] == [(), (), ()]
    assert result.failed_sources == ()
    assert result.candidate_images == (
        ("docker.io/library/python", "3.12", "python"),
        ("docker.io/library/node", "22", "javascript"),
        ("docker.io/library/ubuntu", "24.04", "shell"))
    assert _SHIPPED_CONFLICT_LISTING in gate_suite.refusal_lines(result)


def test_shipped_ubuntu_latest_requires_a_release():
    ci_text = shipped_ci_text("ubuntu-latest")
    _request, result = resolve_shipped(ci_text, shipped_candidates(ci_text),
                                       ["python", "javascript", "shell"])
    assert isinstance(result, Refused)
    assert result.case is RefusalCase.UNDETERMINED_VERSION
    assert result.image == "docker.io/library/ubuntu"
    assert gate_suite.refusal_case_text(result) == (
        "the version to tag docker.io/library/ubuntu with cannot be determined")


def test_shipped_non_ubuntu_shell_has_no_container_default():
    ci_text = shipped_ci_text("debian-12")
    # Shell's packet names no image for a CI that runs another distribution, so a plan reading it
    # gives that candidate none. The packet's prose is held by review; this models its result.
    candidates = [shipped_candidate("python", ci_text, "python-version"),
                  shipped_candidate("javascript", ci_text, "node-version"),
                  {"language": "shell"}]
    _request, result = resolve_shipped(ci_text, candidates, ["python", "javascript", "shell"])
    assert isinstance(result, Refused)
    assert result.case is RefusalCase.NO_CONTAINER_DEFAULT
    assert result.languages_without_default == ("shell",)


def test_only_the_languages_the_card_declares_are_probed_in_the_guest():
    # A Swift-only card never asks the guest for cargo, though Rust's packet names it.
    harness = Harness()
    harness.run(raw=raw_input(ci=ci_readable("macos"), languages=(), declared=["Swift"]))
    tool_probes = [argv[-1] for argv in harness.processes.probes if "command -v" in argv[-1]]
    assert tool_probes == ["command -v swift"]
    [(argv, _cwd)] = harness.processes.issued
    assert "cargo" not in argv[-1]


# ==================================================================================================
# The check (CP-702 to CP-708, CP-721): whether the evidence resolves, with nothing run
# ==================================================================================================

CHECK_DIR = Path("/tmp/check")
CHECK_INPUTS = CHECK_DIR / "inputs.json"
CHECK_PATHS = CHECK_DIR / "paths.json"
CHECK_TRACKED = CHECK_DIR / "tracked.txt"
NO_OVERRIDE_TAIL = "and the product's decision files record no override"
RESOLVES = "resolves"
OWES = "owes a decision"
DOES_NOT = "does not resolve"
PATHS_FIELDS = ["project", "key", "instance_worktree", "product_path", "product_worktree",
                "product_repo"]


def answer_line(answer: str, detail: str) -> str:
    return f"{answer} {DASH} {detail}\n"


def check_paths(kind: str = "relative", **changes) -> dict:
    """The path tool's contract for the change: the harness contract with the two fields the tool
    adds to it."""
    return {**contract(kind), "project": PROJECT, "key": "key1", **changes}


def check_card(product_path: str = ".claude", command: str = CARD_COMMAND) -> str:
    return (f"# Project Context\n\n**Product path:** {product_path}   <!-- the anchor -->\n"
            f"**Test command:** {command}\n")


def forbidden_host():
    raise AssertionError("the check built the run host")


class ReadOnlyFiles:
    """The check's file collaborator: it can read a file and nothing else."""

    def __init__(self, files: FakeFiles) -> None:
        self._files = files
        self.reads: list[Path] = []

    def read_text(self, path: Path) -> str | None:
        self.reads.append(path)
        return self._files.read_text(path)


class CheckHarness:
    """The check through its real CLI, over a fake tree it can read and no collaborator that
    could start a process, take the lock or write."""

    def __init__(self, *, card: str | None = None, kind: str = "relative",
                 product_files: dict[str, str] | None = None) -> None:
        self.paths = check_paths(kind)
        root = Path(self.paths["product_worktree"])
        base = standard_files(**(product_files or {})).files
        self.files = FakeFiles({(root / path.relative_to(PRODUCT) if PRODUCT in path.parents
                                 else path): text for path, text in base.items()})
        self.card_path = Path(WORKTREE) / "system/projects/demo/project.md"
        self.files.files[self.card_path] = (
            card if card is not None else check_card(self.paths["product_path"]))
        self.read_only = ReadOnlyFiles(self.files)
        self.host = gate_suite.CheckHost(files=self.read_only, core_root=CORE)
        self.out, self.err = io.StringIO(), io.StringIO()

    def stage(self, raw: dict | None = None, *, tracked: tuple[str, ...] = ("src/app.py",),
              inputs_text: str | None = None, paths: dict | None = None,
              paths_text: str | None = None, tracked_text: str | None = None,
              omit: tuple[str, ...] = ()) -> None:
        staged = {
            "inputs": (CHECK_INPUTS, inputs_text if inputs_text is not None else json.dumps(raw)),
            "paths": (CHECK_PATHS, paths_text if paths_text is not None
                      else json.dumps(paths if paths is not None else self.paths)),
            "tracked": (CHECK_TRACKED, tracked_text if tracked_text is not None
                        else "".join(f"{name}\n" for name in tracked)),
        }
        for name, (path, text) in staged.items():
            if name not in omit:
                self.files.files[path] = text

    def invoke(self, *extra: str) -> int:
        return gate_suite.main(
            ["check", "--worktree", WORKTREE, "--project", PROJECT, "--key", "key1",
             "--inputs", str(CHECK_INPUTS), "--paths", str(CHECK_PATHS),
             "--tracked-files", str(CHECK_TRACKED), *extra],
            check_host=self.host, host_factory=forbidden_host, stdout=self.out, stderr=self.err)

    def call(self, raw: dict | None = None, **staging) -> int:
        self.stage(raw, **staging)
        return self.invoke()


@pytest.fixture
def no_processes(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the check started a process")

    for name in ("run", "Popen", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)
    monkeypatch.setattr(os, "system", refuse)


def untagged(language: str) -> dict:
    return candidate(language, tag=None, tag_source=None)


def no_language_input() -> dict:
    raw = raw_input(candidates=[])
    raw["languages"] = {"declared": None, "invoked": None}
    return raw


def test_check_reports_multilanguage_default_resolution(no_processes):
    mac = CheckHarness()
    status = mac.call(raw_input(ci=ci_readable("macos"), languages=("rust", "swift", "shell"),
                                candidates=[], guest=None))
    assert status == 0
    assert mac.out.getvalue() == answer_line(
        RESOLVES, "macos-guest: the product's gates run in the macOS guest")
    assert mac.err.getvalue() == ""

    linux = CheckHarness()
    status = linux.call(raw_input(languages=("python", "javascript", "shell"), guest=None))
    assert status == 1
    assert linux.out.getvalue() == answer_line(
        OWES, "the product's CI runs on Linux, the languages python, javascript, shell call for "
        f"more than one container image, {NO_OVERRIDE_TAIL}")
    assert "Environment:" not in mac.out.getvalue() + linux.out.getvalue()
    assert linux.err.getvalue() == ""


def test_check_has_no_process_or_write_effects(no_processes, tmp_path):
    raws = {
        "resolves": raw_input(ci=ci_readable("macos"), languages=("swift",), candidates=[]),
        "owes": raw_input(languages=("python", "shell")),
        "does not resolve": raw_input(ci=CI_UNREADABLE),
    }
    for name, raw in raws.items():
        harness = CheckHarness()
        harness.stage(raw)
        before = dict(harness.files.files)
        harness.invoke()
        assert harness.files.files == before, name
        assert harness.out.getvalue().splitlines()[0].startswith(
            {"resolves": RESOLVES, "owes": OWES, "does not resolve": DOES_NOT}[name]), name
        assert all(isinstance(path, Path) for path in harness.read_only.reads), name

    # Its collaborators can read and cannot do anything else.
    assert [field.name for field in dataclasses.fields(gate_suite.CheckHost)] == [
        "files", "core_root"]
    for name in ("write_text", "remove", "tracked_files", "linked_git_dirs"):
        assert not hasattr(gate_suite.ReadOnlyFiles, name), name

    # A real prepared tree, read through the real CLI: nothing is created, changed or removed.
    core, instance = tmp_path / "core", tmp_path / "instance" / ".worktrees" / "key1"
    context = tmp_path / "context"
    for relative, text in {
        f"{PACKET_DIR}/README.md": REGISTRY_TEXT,
        **{f"{PACKET_DIR}/{language}/environment.md": text
           for language, text in PACKET_TEXT.items()}}.items():
        (core / relative).parent.mkdir(parents=True, exist_ok=True)
        (core / relative).write_text(text, encoding="utf-8")
    (instance / "system/projects/demo").mkdir(parents=True)
    (instance / "system/projects/demo/project.md").write_text(check_card("prod"), encoding="utf-8")
    (instance / CI_FILE).parent.mkdir(parents=True)
    (instance / CI_FILE).write_text(CI_TEXT, encoding="utf-8")
    context.mkdir()
    paths = {**check_paths(), "instance_worktree": str(instance), "product_path": "prod",
             "product_worktree": str(instance), "product_repo": str(instance)}
    (context / "paths.json").write_text(json.dumps(paths), encoding="utf-8")
    (context / "tracked.txt").write_text("prod/app.py\n", encoding="utf-8")
    (context / "inputs.json").write_text(json.dumps(raw_input(guest=None)), encoding="utf-8")

    def listing() -> dict:
        return {str(path): (path.stat().st_mtime_ns, path.stat().st_size if path.is_file() else 0)
                for path in sorted(tmp_path.rglob("*"))}

    before, out, err = listing(), io.StringIO(), io.StringIO()
    status = gate_suite.main(
        ["check", "--worktree", str(instance), "--project", PROJECT, "--key", "key1",
         "--inputs", str(context / "inputs.json"), "--paths", str(context / "paths.json"),
         "--tracked-files", str(context / "tracked.txt")],
        check_host=gate_suite.CheckHost(files=gate_suite.ReadOnlyFiles(), core_root=core),
        host_factory=forbidden_host, stdout=out, stderr=err)
    assert (status, err.getvalue()) == (0, "")
    assert out.getvalue() == answer_line(
        RESOLVES, "container: the product's gates run in python:3.12, arm64")
    assert listing() == before


def owed_cases() -> list:
    matrix = [candidate("python", tag=version,
                        tag_source=source(CI_FILE, f'python-version: "{version}"'))
              for version in ("3.12", "3.13")]
    return [
        ("other-platform", raw_input(ci={"finding": "readable", "runners": [runner("windows")]}),
         None, None, "the product's CI runs on a platform other than macOS or Linux, its "
         f"platforms are windows, {NO_OVERRIDE_TAIL}"),
        ("other-platforms-deduplicated", raw_input(ci={"finding": "readable", "runners": [
            runner("windows"), runner("freebsd"), runner("windows")]}), None, None,
         "the product's CI runs on a platform other than macOS or Linux, its platforms are "
         f"windows, freebsd, {NO_OVERRIDE_TAIL}"),
        ("mixed-platforms", raw_input(ci=ci_readable("macos", "linux")), None, None,
         f"the product's CI runs on both macOS and Linux, its platforms are macos, linux, "
         f"{NO_OVERRIDE_TAIL}"),
        ("no-container-default", raw_input(languages=("swift",), candidates=[]), None, None,
         f"the product's CI runs on Linux, no container default exists for swift, "
         f"{NO_OVERRIDE_TAIL}"),
        ("no-default-keeps-priority-over-conflicts",
         raw_input(languages=("python", "swift"), candidates=[candidate("python")]), None, None,
         f"the product's CI runs on Linux, no container default exists for swift, "
         f"{NO_OVERRIDE_TAIL}"),
        ("no-default-follows-resolved-order",
         raw_input(languages=("swift", "kotlin"), candidates=[]), None, None,
         f"the product's CI runs on Linux, no container default exists for swift, kotlin, "
         f"{NO_OVERRIDE_TAIL}"),
        ("no-language", no_language_input(), ("notes.txt",), None,
         "the product's CI runs on Linux, no container default can be chosen because no language "
         f"was resolved for the product, {NO_OVERRIDE_TAIL}"),
        ("conflicting-images", raw_input(languages=("python", "javascript", "shell")), None, None,
         "the product's CI runs on Linux, the languages python, javascript, shell call for more "
         f"than one container image, {NO_OVERRIDE_TAIL}"),
        ("conflicting-images-reversed-and-duplicated",
         raw_input(languages=("python", "javascript", "shell"),
                   candidates=[candidate("shell"), candidate("javascript"), candidate("python"),
                               candidate("python")]), None, None,
         "the product's CI runs on Linux, the languages python, javascript, shell call for more "
         f"than one container image, {NO_OVERRIDE_TAIL}"),
        ("conflicting-images-language-named-twice",
         raw_input(languages=("python", "shell", "python")), None, None,
         "the product's CI runs on Linux, the languages python, shell call for more than one "
         f"container image, {NO_OVERRIDE_TAIL}"),
        ("untagged-shell", raw_input(
            languages=("python", "javascript", "shell"),
            candidates=[candidate("python"), candidate("javascript"), untagged("shell")]),
         None, None, "the product's CI runs on Linux, the container version cannot be determined "
         f"for shell, {NO_OVERRIDE_TAIL}"),
        ("several-unversioned-languages-in-resolved-order",
         raw_input(languages=("python", "shell"), candidates=[untagged("shell"),
                                                              untagged("python")]),
         None, None, "the product's CI runs on Linux, the container version cannot be determined "
         f"for python, shell, {NO_OVERRIDE_TAIL}"),
        ("one-language-with-a-version-matrix", raw_input(candidates=matrix), None,
         {CI_FILE: MATRIX_CI_TEXT}, "the product's CI runs on Linux, the container version "
         f"cannot be determined for python, {NO_OVERRIDE_TAIL}"),
        ("no-guest-default", raw_input(ci=ci_readable("macos"), languages=("swift", "kotlin"),
                                       candidates=[]), None, None,
         "the product's CI runs on macOS, no macOS guest toolchain is named for kotlin, "
         f"{NO_OVERRIDE_TAIL}"),
    ]


@pytest.mark.parametrize("name,raw,tracked,files,detail", owed_cases(),
                         ids=[case[0] for case in owed_cases()])
def test_check_names_the_reached_owed_case(name, raw, tracked, files, detail, no_processes):
    harness = CheckHarness(product_files=files)
    raw = {**raw, "guest": None}
    status = harness.call(raw, **({"tracked": tracked} if tracked else {}))
    assert harness.out.getvalue() == answer_line(OWES, detail)
    assert (status, harness.err.getvalue()) == (1, "")


def run_case_text(raw: dict) -> str:
    harness = Harness()
    harness.run(raw=raw)
    prefix = f"Environment: unresolved {DASH} "
    assert harness.first_line.startswith(prefix)
    return harness.first_line[len(prefix):]


def test_check_distinguishes_other_refusals_from_owed_decisions(no_processes):
    resolving = {
        "single-image": (raw_input(), answer_line(
            RESOLVES, "container: the product's gates run in python:3.12, arm64")),
        "no-ci": (raw_input(ci=CI_NONE), answer_line(
            RESOLVES, "owners-mac: the product has no CI, so its gates run on the owner's Mac")),
        "recorded-mac": (raw_input(override=mac_decision()), answer_line(
            RESOLVES, "owners-mac: the product's decision files choose the owner's Mac for its "
            "gates")),
        "amd64-container": (raw_input(amd64={"source": source(anchor="runs-on: ubuntu-latest")}),
                            answer_line(RESOLVES, "container: the product's gates run in "
                                        "python:3.12, amd64")),
    }
    for name, (raw, expected) in resolving.items():
        harness = CheckHarness()
        status = harness.call({**raw, "guest": None})
        assert (harness.out.getvalue(), status) == (expected, 0), name

    other = {
        "unreadable-ci": raw_input(ci=CI_UNREADABLE),
        "no-runner": raw_input(ci={"finding": "readable", "runners": []}),
        "failed-runner-source": raw_input(ci={"finding": "readable", "runners": [
            {"platform": "linux", "source": source(anchor=MISSING_QUOTE)}]}),
        "valid-neither": raw_input(
            override={"environment": "neither", "source": source(anchor="jobs:")}),
        "failed-override": raw_input(override=container_override(
            source=source(anchor=MISSING_QUOTE))),
        "failed-amd64": raw_input(amd64={"source": source(AMD64_FILE, AMD64_QUOTE)}),
        "guest-override-without-guest-default": raw_input(
            languages=("kotlin",), candidates=[], override=guest_override()),
        "override-container-without-version": raw_input(
            override=container_override(tag=None)),
    }
    for name, raw in other.items():
        harness = CheckHarness()
        status = harness.call({**raw, "guest": None})
        assert harness.out.getvalue() == answer_line(DOES_NOT, run_case_text(raw)), name
        assert (status, harness.err.getvalue()) == (1, ""), name


@pytest.mark.parametrize("name,staging,message", [
    ("inputs unreadable", {"omit": ("inputs",)},
     f"the inputs file {CHECK_INPUTS} cannot be read"),
    ("paths unreadable", {"omit": ("paths",)}, f"the paths file {CHECK_PATHS} cannot be read"),
    ("tracked list unreadable", {"omit": ("tracked",)},
     f"the tracked-files list {CHECK_TRACKED} cannot be read"),
    *[(f"paths lack {field}",
       {"paths": {key: value for key, value in check_paths().items() if key != field}},
       f"the paths file {CHECK_PATHS} has no {field}") for field in PATHS_FIELDS],
    ("another project", {"paths": check_paths(project="other")},
     f"the paths file {CHECK_PATHS} is for project other, not demo"),
    ("another change", {"paths": check_paths(key="other")},
     f"the paths file {CHECK_PATHS} is for change key other, not key1"),
    ("another worktree", {"paths": check_paths(instance_worktree="/elsewhere")},
     f"the paths file {CHECK_PATHS} is for instance worktree /elsewhere, not {WORKTREE}"),
    ("another product path", {"paths": check_paths(product_path=".elsewhere")},
     f"the paths file {CHECK_PATHS} gives the product path .elsewhere, but the project card "
     "names .claude"),
])
def test_check_rejects_unavailable_or_mismatched_context(name, staging, message, no_processes):
    harness = CheckHarness()
    status = harness.call(raw_input(guest=None), **staging)
    assert (status, harness.out.getvalue()) == (2, "")
    assert harness.err.getvalue() == f"gate_suite: {message}\n"
    assert not [path for path in harness.read_only.reads if path.name == "ci.yml"]


@pytest.mark.parametrize("staging,reading", [
    ({"inputs_text": "{not json"}, "the inputs file {path} is not JSON: "),
    ({"paths_text": "not json"}, "the paths file {path} is not JSON: "),
])
def test_check_rejects_malformed_json_with_the_readers_own_message(staging, reading, no_processes):
    harness = CheckHarness()
    path = CHECK_INPUTS if "inputs_text" in staging else CHECK_PATHS
    status = harness.call(**staging)
    assert (status, harness.out.getvalue()) == (2, "")
    assert harness.err.getvalue().startswith("gate_suite: " + reading.format(path=path))
    assert harness.err.getvalue().count("\n") == 1


def test_check_rejects_an_unreadable_card_and_unusable_inputs(no_processes):
    no_card = CheckHarness()
    no_card.files.files.pop(no_card.card_path)
    assert no_card.call(raw_input(guest=None)) == 2
    assert no_card.out.getvalue() == "" and no_card.err.getvalue().startswith("gate_suite: ")

    for text in ("[1, 2]", "null", '"text"'):
        odd = CheckHarness()
        assert odd.call(inputs_text=text) == 2, text
        assert odd.out.getvalue() == "" and odd.err.getvalue().startswith("gate_suite: "), text


def test_check_accepts_an_empty_tracked_snapshot_without_git(no_processes):
    class Unreadable(ReadOnlyFiles):
        def tracked_files(self, root: Path) -> list[str]:
            raise AssertionError("the check asked the files for the tracked list")

    raw = no_language_input()
    files = Unreadable(CheckHarness().files)
    empty = io.StringIO()
    result = gate_suite.check_gate(
        worktree=WORKTREE, project=PROJECT, key="key1", inputs=raw,
        context=gate_suite.CheckContext(paths=check_paths(), tracked_files=()),
        files=files, core_root=CORE, out=empty)
    detail = ("the product's CI runs on Linux, no container default can be chosen because no "
              f"language was resolved for the product, {NO_OVERRIDE_TAIL}")
    assert result.answer is gate_suite.CheckAnswer.OWES_DECISION
    assert (result.detail, result.status) == (detail, 1)
    assert empty.getvalue() == answer_line(OWES, detail)

    # The same evidence with one tracked Python file infers the language the empty list lacks.
    filled = CheckHarness()
    raw["candidates"] = [candidate("python")]
    assert filled.call(raw, tracked=("src/app.py",)) == 0
    assert filled.out.getvalue().startswith(answer_line(RESOLVES, "container:")[:-1])

    # And through the CLI a valid empty list is the same empty snapshot, not a missing file.
    cli = CheckHarness()
    assert cli.call(raw, tracked_text="") == 1
    assert cli.out.getvalue() == answer_line(OWES, detail)


def test_check_without_a_suite_needs_no_environment(no_processes):
    expected = answer_line(
        RESOLVES, "none: the product has no suite, because its project card names no test command")
    for text in ("{}", "[1]", "null"):
        harness = CheckHarness(card=check_card(command="none"))
        assert harness.call(inputs_text=text) == 0, text
        assert harness.out.getvalue() == expected, text
        # Past the three prepared files, the card is the only thing it read.
        assert [path for path in harness.read_only.reads if CHECK_DIR not in path.parents] == [
            harness.card_path], text

    malformed = CheckHarness(card=check_card(command="none"))
    assert malformed.call(inputs_text="{bad") == 2
    assert malformed.out.getvalue() == ""
    assert malformed.err.getvalue().startswith(f"gate_suite: the inputs file {CHECK_INPUTS} is not")


def test_check_never_inherits_an_owners_ask(no_processes, monkeypatch):
    conflicting = raw_input(languages=("python", "javascript", "shell"), guest=None)
    conflicting.update({"owners_mac": True, "owners_ask": True, "ask": "owner asked"})
    conflicting["decisions"]["owners_ask"] = True
    monkeypatch.setenv("KENSAIAPP_GATE_OWNERS_MAC", "1")
    harness = CheckHarness()
    assert harness.call(conflicting) == 1
    assert harness.out.getvalue().startswith(OWES)
    assert "owner's ask" not in harness.out.getvalue()

    with pytest.raises(SystemExit) as refused:
        harness.stage(conflicting)
        harness.invoke("--owners-mac")
    assert refused.value.code == 2


def test_check_answers_are_exactly_three_and_carry_status_and_detail(no_processes):
    assert [answer.value for answer in gate_suite.CheckAnswer] == [RESOLVES, OWES, DOES_NOT]
    assert {answer.name for answer in gate_suite.CheckAnswer} == {
        "RESOLVES", "OWES_DECISION", "DOES_NOT_RESOLVE"}
    harness = CheckHarness()
    out = io.StringIO()
    result = gate_suite.check_gate(
        worktree=WORKTREE, project=PROJECT, key="key1", inputs=raw_input(ci=CI_UNREADABLE),
        context=gate_suite.CheckContext(paths=check_paths(), tracked_files=("src/app.py",)),
        files=harness.read_only, core_root=CORE, out=out)
    assert result.answer is gate_suite.CheckAnswer.DOES_NOT_RESOLVE
    assert result.status == 1
    assert result.detail == "the runner cannot be read from the product's CI configuration"


def test_check_command_help_names_what_each_option_holds(capsys):
    with pytest.raises(SystemExit) as shown:
        gate_suite.main(["--help"])
    assert shown.value.code == 0
    assert "answer whether the sourced inputs resolve an environment, starting nothing" in (
        " ".join(capsys.readouterr().out.split()))
    with pytest.raises(SystemExit) as shown:
        gate_suite.main(["check", "--help"])
    assert shown.value.code == 0
    text = " ".join(capsys.readouterr().out.split())
    for help_text in ("the sourced-input JSON",
                      "the path tool's contract for the change, as a JSON file",
                      "the product's tracked files, one product-relative path per line"):
        assert help_text in text


# ==================================================================================================
# The product's committed decision: acquisition (a snapshot of `main`'s docs/nfdr.md, nothing more)
# ==================================================================================================

NFDR_MAIN = "# Product\n\n## 8. Operational constraints\n\n- **QC-1:** on main\n"


def _commit_all(repo: Path, message: str) -> None:
    _git("add", "-A", cwd=repo)
    _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", message, cwd=repo)


def _repository(tmp_path: Path, files: dict[str, str], *, branch: str = "main",
                name: str = "repo") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git("init", "-q", "-b", branch, cwd=repo)
    for relative, text in files.items():
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_text(text, encoding="utf-8")
    _commit_all(repo, "first")
    return repo


def _contract_for(repo: Path, product_path: str) -> dict:
    return {"product_repo": str(repo), "product_path": product_path}


def _main_revision(repo: Path) -> str:
    return _git("rev-parse", "main", cwd=repo).strip()


RECORD_LAYOUTS = {
    # name: (files main holds, product path as the contract gives it, the decision file's path)
    "relative-root": ({"docs/nfdr.md": NFDR_MAIN}, ".", "docs/nfdr.md"),
    "relative-nested": ({"docs/nfdr.md": "# another product's\n", "app/docs/nfdr.md": NFDR_MAIN},
                        "app", "app/docs/nfdr.md"),
    "external-root": ({"docs/nfdr.md": NFDR_MAIN}, "REPO", "docs/nfdr.md"),
    "external-subdirectory": ({"docs/nfdr.md": "# another product's\n",
                               "app/docs/nfdr.md": NFDR_MAIN}, "REPO/app", "app/docs/nfdr.md"),
}


@pytest.mark.parametrize("layout", RECORD_LAYOUTS)
def test_record_reads_the_product_nfdr_from_committed_local_main(layout, tmp_path):
    files, declared, expected_file = RECORD_LAYOUTS[layout]
    repo = _repository(tmp_path, files)
    # A branch holds a conflicting entry and is the checked-out one: its file is on disk, and it
    # is not the record.
    _git("checkout", "-q", "-b", "key1", cwd=repo)
    (repo / expected_file).write_text("## 8. Operational constraints\n\n- **QC-9:** branch\n")
    _commit_all(repo, "branch edit")
    product_path = declared.replace("REPO", str(repo))

    record = gate_suite.read_decision_record(
        _contract_for(repo, product_path), gate_suite.GitRecordReader())

    assert record == gate_suite.DecisionRecord(
        repository=str(repo), file=expected_file, revision=_main_revision(repo), text=NFDR_MAIN)


def test_record_ignores_uncommitted_edits_and_refreshes_after_commit(tmp_path):
    repo = _repository(tmp_path, {"docs/nfdr.md": NFDR_MAIN})
    contract = _contract_for(repo, ".")
    reader = gate_suite.GitRecordReader()
    first = gate_suite.read_decision_record(contract, reader)

    (repo / "docs/nfdr.md").write_text("an uncommitted edit\n")
    assert gate_suite.read_decision_record(contract, reader) == first

    _commit_all(repo, "commit the edit")
    second = gate_suite.read_decision_record(contract, reader)
    assert second.text == "an uncommitted edit\n"
    assert second.revision == _main_revision(repo) != first.revision


def test_record_absence_is_distinct_from_read_failure(tmp_path):
    reader = gate_suite.GitRecordReader()

    no_main = _repository(tmp_path, {"docs/nfdr.md": NFDR_MAIN}, branch="trunk", name="a")
    record = gate_suite.read_decision_record(_contract_for(no_main, "."), reader)
    assert (record.revision, record.text) == (None, None)

    no_file = _repository(tmp_path, {"README.md": "x\n"}, name="b")
    record = gate_suite.read_decision_record(_contract_for(no_file, "."), reader)
    assert record.revision == _main_revision(no_file) and record.text is None

    empty = _repository(tmp_path, {"docs/nfdr.md": ""}, name="c")
    assert gate_suite.read_decision_record(_contract_for(empty, "."), reader).text == ""

    # Failures are errors, in the command's own words, and never an absent record.
    not_a_repository = tmp_path / "d"
    not_a_repository.mkdir()
    with pytest.raises(gate_suite.RecordReadError) as error:
        gate_suite.read_decision_record(_contract_for(not_a_repository, "."), reader)
    assert str(error.value).startswith(
        f"the product's docs/nfdr.md cannot be read from the main branch of {not_a_repository}: ")
    assert not str(error.value).endswith("\n")

    undecodable = _repository(tmp_path, {"README.md": "x\n"}, name="e")
    (undecodable / "docs").mkdir()
    (undecodable / "docs/nfdr.md").write_bytes(b"\xff\xfe not utf-8")
    _commit_all(undecodable, "binary")
    with pytest.raises(gate_suite.RecordReadError, match="docs/nfdr.md is not UTF-8 text"):
        gate_suite.read_decision_record(_contract_for(undecodable, "."), reader)

    a_folder = _repository(tmp_path, {"docs/nfdr.md/part.md": "x\n"}, name="f")
    with pytest.raises(gate_suite.RecordReadError, match="docs/nfdr.md is not a file"):
        gate_suite.read_decision_record(_contract_for(a_folder, "."), reader)


class FakeRecordReader:
    """A read-at-revision collaborator that moves `main` after each time it is asked where it is."""

    def __init__(self, text: str | None = NFDR_MAIN, *, revisions=("rev1", "rev2"),
                 failure: str | None = None) -> None:
        self.text, self.failure = text, failure
        self.revisions = iter(revisions)
        self.calls: list[tuple] = []

    def main_revision(self, repository: str) -> str | None:
        self.calls.append(("main", repository))
        if self.failure:
            raise gate_suite.RecordReadFailure(self.failure)
        return next(self.revisions)

    def file_at(self, repository: str, revision: str, path: str) -> str | None:
        self.calls.append(("file", repository, revision, path))
        return self.text


class RecordingRun:
    """The real reader's process runner, handed in: each command it is given is recorded, then
    run for real."""

    def __init__(self) -> None:
        self.sent: list[list[str]] = []

    def __call__(self, argv, **kwargs):
        self.sent.append(list(argv))
        return subprocess.run(argv, **kwargs)


def test_record_reads_one_revision_without_git_mutation(tmp_path):
    reader = FakeRecordReader()
    record = gate_suite.read_decision_record(_contract_for(Path("/p/repo"), "app"), reader)
    # `main` is resolved once and the file read at that commit, though `main` moves straight after.
    assert reader.calls == [("main", "/p/repo"), ("file", "/p/repo", "rev1", "app/docs/nfdr.md")]
    assert record == gate_suite.DecisionRecord("/p/repo", "app/docs/nfdr.md", "rev1", NFDR_MAIN)

    # The real reader sends read-only plumbing only, and no probe or suite is involved.
    repo = _repository(tmp_path, {"docs/nfdr.md": NFDR_MAIN})
    run = RecordingRun()
    record = gate_suite.read_decision_record(
        _contract_for(repo, "."), gate_suite.GitRecordReader(run=run))
    assert record.text == NFDR_MAIN
    assert {argv[3] for argv in run.sent} == {"rev-parse", "ls-tree", "cat-file"}
    assert all(argv[:3] == ["git", "-C", str(repo)] for argv in run.sent)


class RecordHarness:
    """The `record` command through its real CLI, over a fake tree and a fake reader."""

    def __init__(self, reader=None, *, paths: dict | None = None) -> None:
        self.paths = paths if paths is not None else check_paths()
        self.files = FakeFiles({Path(WORKTREE) / "system/projects/demo/project.md": check_card(),
                                CHECK_PATHS: json.dumps(self.paths)})
        self.reader = reader if reader is not None else FakeRecordReader()
        self.out, self.err = io.StringIO(), io.StringIO()

    def invoke(self, *, worktree: str = WORKTREE) -> int:
        return gate_suite.main(
            ["record", "--worktree", worktree, "--project", PROJECT, "--key", "key1",
             "--paths", str(CHECK_PATHS)],
            record_host=gate_suite.RecordHost(files=ReadOnlyFiles(self.files), reader=self.reader),
            host_factory=forbidden_host, stdout=self.out, stderr=self.err)


def test_record_cli_emits_validated_present_and_absent_snapshots():
    present = RecordHarness(FakeRecordReader("line one\n\n  `x` — é\n"))
    assert present.invoke() == 0
    assert present.err.getvalue() == ""
    assert json.loads(present.out.getvalue()) == {
        "repository": "/work/product-repo", "file": ".claude/docs/nfdr.md", "revision": "rev1",
        "text": "line one\n\n  `x` — é\n"}
    present.files.files[CHECK_DIR / "record.json"] = present.out.getvalue()
    assert gate_suite.load_decision_record(
        ReadOnlyFiles(present.files), str(CHECK_DIR / "record.json")) == (
            gate_suite.DecisionRecord("/work/product-repo", ".claude/docs/nfdr.md", "rev1",
                                      "line one\n\n  `x` — é\n"))

    absent = RecordHarness(FakeRecordReader(None))
    assert absent.invoke() == 0
    assert json.loads(absent.out.getvalue())["text"] is None
    assert json.loads(absent.out.getvalue())["revision"] == "rev1"

    # Nothing prepared is trusted unread: bad context stops the command before any read.
    for name, change in {
        "unreadable": lambda h: h.files.files.pop(CHECK_PATHS),
        "malformed": lambda h: h.files.files.update({CHECK_PATHS: "not json"}),
        "another project": lambda h: h.files.files.update(
            {CHECK_PATHS: json.dumps(check_paths(project="other"))}),
        "a field missing": lambda h: h.files.files.update({CHECK_PATHS: json.dumps(
            {k: v for k, v in check_paths().items() if k != "product_repo"})}),
    }.items():
        broken = RecordHarness()
        change(broken)
        assert broken.invoke() == 2, name
        assert broken.out.getvalue() == "" and broken.err.getvalue().startswith("gate_suite: ")
        assert broken.reader.calls == [], name

    unreadable_main = RecordHarness(FakeRecordReader(failure="fatal: bad object"))
    assert unreadable_main.invoke() == 2
    assert unreadable_main.out.getvalue() == ""
    assert unreadable_main.err.getvalue() == (
        "gate_suite: the product's .claude/docs/nfdr.md cannot be read from the main branch of "
        "/work/product-repo: fatal: bad object\n")


# ==================================================================================================
# The product's committed decision: interpretation (an entry in § 8 replaces only the override)
# ==================================================================================================

OWNERS_MAC_ENTRY = (
    "- **QC-1:** The product's gates run on the owner's Mac — `environment: owners-mac`, the "
    "owner's call when the packet defaults did not resolve. Traces to: the runner pool. "
    "Verified by: the gate check answers `resolves`.")
CONTAINER_ENTRY = ("- **QC-2:** The gates run in a container — `environment: container`, "
                   "`image: docker.io/library/python`, `tag: 3.13`, `architecture: arm64`.")


def nfdr(*entries: str, heading: str = "## 8. Operational constraints", before: str = "") -> str:
    return ("# Product\n\n## 7. Quality\n\n- **QC-0:** nothing to run\n\n" + before + heading
            + "\n\n" + "\n".join(entries) + "\n")


def record_of(text: str | None, file: str = "docs/nfdr.md") -> gate_suite.DecisionRecord:
    return gate_suite.DecisionRecord("/work/product-repo", file, "rev1", text)


def decided(text: str | None):
    return gate_suite.read_current_decision(text)


@pytest.mark.parametrize("heading", [
    "## 8", "## 8.", "## 8. Operational constraints", "# 8 Operational constraints",
    "### 8 Operational constraints"])
def test_nfdr_section_eight_accepts_the_numbered_headings(heading):
    found = decided(nfdr(OWNERS_MAC_ENTRY, heading=heading))
    assert found == gate_suite.RecordDecision(
        gate_suite.OverrideKind.OWNERS_MAC, None, None, None, OWNERS_MAC_ENTRY)


@pytest.mark.parametrize("name,text", [
    ("an entry in section 7 only", "# P\n\n## 7. Quality\n\n" + OWNERS_MAC_ENTRY + "\n"),
    ("section 80", nfdr(OWNERS_MAC_ENTRY, heading="## 80. Other")),
    ("a heading that only starts with 8", nfdr(OWNERS_MAC_ENTRY, heading="## 8b. Other")),
    ("a later peer section", nfdr("- **QC-3:** nothing", "", "## 9. Later", "", OWNERS_MAC_ENTRY)),
    ("ordinary prose, not a list item", nfdr(
        "The gates run on the owner's Mac, `environment: owners-mac`.")),
    ("a field outside inline code", nfdr("- **QC-1:** environment: owners-mac")),
    ("a heading naming an environment", nfdr(
        "### `environment: owners-mac`", "", "- **QC-1:** nothing")),
    ("a fenced sample entry", nfdr("```markdown", OWNERS_MAC_ENTRY, "```")),
    ("a tilde-fenced sample entry", nfdr("~~~", OWNERS_MAC_ENTRY, "~~~")),
    ("an unknown environment", nfdr("- **QC-1:** `environment: lambda`")),
    ("no section at all", "# Product\n\nNothing here.\n"),
    ("an empty file", ""),
    ("a section with no entries", nfdr("- **QC-1:** nothing recorded")),
])
def test_nfdr_section_eight_rejects_what_declares_no_decision(name, text):
    assert decided(text) is None, name


def test_nfdr_section_eight_keeps_subsections_and_stops_at_the_next_peer():
    inside = nfdr("### 8.1 Sub", "", OWNERS_MAC_ENTRY, "", "#### 8.1.1 Deeper", "", "- **QC-4:** x")
    assert decided(inside).quote == OWNERS_MAC_ENTRY
    after_peer = nfdr("- **QC-3:** nothing", "", "## 9. Later", "", OWNERS_MAC_ENTRY)
    assert decided(after_peer) is None
    # A heading of a higher level ends the section just as a peer does.
    higher = nfdr("- **QC-3:** nothing", "", "# Appendix", "", OWNERS_MAC_ENTRY)
    assert decided(higher) is None


def test_nfdr_entries_read_every_environment_architecture_and_wrapped_field():
    for token, kind in (("macos-guest", gate_suite.OverrideKind.MACOS_GUEST),
                        ("container", gate_suite.OverrideKind.CONTAINER),
                        ("owners-mac", gate_suite.OverrideKind.OWNERS_MAC),
                        ("neither", gate_suite.OverrideKind.NEITHER)):
        assert decided(nfdr(f"- **QC-1:** x `environment: {token}`.")).environment is kind
    for token, arch in (("arm64", Architecture.ARM64), ("amd64", Architecture.AMD64)):
        found = decided(nfdr(f"- **QC-1:** `environment: container`, `image: i`, `tag: 1`, "
                             f"`architecture: {token}`"))
        assert found.architecture is arch

    wrapped = ("- **QC-5:** The gates run in a container, per the runner pool —\n"
               "  `environment: container`, with the image\n"
               "  `image: docker.io/library/python` and `tag: 3.13`,\n"
               "  `architecture: amd64`. Traces to: CI.\n"
               "  Verified by: the check answers `resolves`.")
    found = decided(nfdr(wrapped, "", "- **QC-6:** unrelated"))
    assert (found.environment, found.image, found.tag, found.architecture) == (
        gate_suite.OverrideKind.CONTAINER, "docker.io/library/python", "3.13", Architecture.AMD64)
    assert found.quote == wrapped

    # A blank line inside an indented item keeps the item whole; an unindented line ends it.
    loose = "- **QC-7:** a loose item\n\n  `environment: owners-mac` on a second paragraph"
    assert decided(nfdr(loose)).quote == loose
    flush = "- **QC-7:** a loose item\n\nflush prose `environment: owners-mac`"
    assert decided(nfdr(flush)) is None


@pytest.mark.parametrize("name,entries", [
    ("environments", [OWNERS_MAC_ENTRY, CONTAINER_ENTRY]),
    ("images", ["- a `environment: container` `image: i` `tag: 1`",
                "- b `environment: container` `image: j` `tag: 1`"]),
    ("tags", ["- a `environment: container` `image: i` `tag: 1`",
              "- b `environment: container` `image: i` `tag: 2`"]),
    ("architectures", ["- a `environment: container` `image: i` `tag: 1` `architecture: arm64`",
                       "- b `environment: container` `image: i` `tag: 1` `architecture: amd64`"]),
    ("one entry leaving a field out", [
        "- a `environment: container` `image: i` `tag: 1` `architecture: arm64`",
        "- b `environment: container` `image: i` `tag: 1`"]),
    ("fields inside one entry", ["- a `environment: owners-mac` `environment: neither`"]),
    ("an image given twice in one entry", [
        "- a `environment: container` `image: i` `image: j` `tag: 1`"]),
])
def test_current_decisions_compare_supplied_values_before_defaults(name, entries):
    assert isinstance(decided(nfdr(*entries)), gate_suite.RecordConflict), name


def test_identical_decisions_collapse_whatever_their_wording_or_order():
    one = "- first wording `environment: container` `image: i` `tag: 1` `architecture: arm64`"
    two = "- second `architecture: arm64` words `tag: 1`, `image: i`, `environment: container`"
    for entries in ([one, two], [two, one], [one, one]):
        found = decided(nfdr(*entries))
        assert isinstance(found, gate_suite.RecordDecision), entries
        assert (found.image, found.tag, found.architecture) == ("i", "1", Architecture.ARM64)
    # The quote is the first entry's own text, whichever tuple-equal entry follows.
    assert decided(nfdr(one, two)).quote == one
    # A field repeated with the same value is one value.
    assert isinstance(decided(nfdr("- `environment: owners-mac` and `environment: owners-mac`")),
                      gate_suite.RecordDecision)


def _frozen_container() -> dict:
    return container_override()


def _parse(raw: dict | None, record: gate_suite.DecisionRecord | None, files=None):
    return gate_suite.parse_request(
        copy.deepcopy(raw), files=files or standard_files(), product_checkout=PRODUCT,
        language_root=PRODUCT, core_root=CORE, project=PROJECT, record=record)


def test_current_record_replaces_only_the_frozen_override():
    record = record_of(nfdr(OWNERS_MAC_ENTRY))
    frozen = raw_input(override=_frozen_container(), amd64={"source": source()},
                       languages=("python", "javascript"))
    snapshot = copy.deepcopy(frozen)
    without, with_record = _parse(frozen, None), _parse(frozen, record)
    assert frozen == snapshot
    assert without.override.kind is gate_suite.OverrideKind.CONTAINER
    assert with_record.override.kind is gate_suite.OverrideKind.OWNERS_MAC
    assert with_record.override.failed == ()
    assert dataclasses.replace(with_record, override=without.override) == without
    resolved = gate_suite.resolve_environment(with_record, owners_ask=False)
    assert (resolved.kind, resolved.owners_mac_cause) == (
        EnvironmentKind.OWNERS_MAC, OwnersMacCause.PRODUCT_DECISION)

    # A superseded override is never validated: malformed, or sourced to a line no file holds.
    for stale in ({"environment": "bogus"}, {"environment": "container"},
                  container_override(source=source(anchor=MISSING_QUOTE))):
        request = _parse(raw_input(override=stale), record)
        assert request.override.kind is gate_suite.OverrideKind.OWNERS_MAC, stale
        assert request.override.failed == ()
    # And without a current declaration the same malformed override is still an input error.
    with pytest.raises(gate_suite.InputError):
        _parse(raw_input(override={"environment": "bogus"}), None)
    with pytest.raises(gate_suite.InputError):
        _parse(raw_input(override={"environment": "bogus"}), record_of(nfdr("- nothing")))


def test_current_source_validation_uses_the_prepared_record():
    record = record_of(nfdr(OWNERS_MAC_ENTRY))
    # The branch holds the quoted text; the prepared record does not. The record is the source.
    only_here = "## 8. Operational constraints\n- QC-7: only here\n"
    branch = standard_files(**{"docs/nfdr.md": only_here})
    request = _parse(raw_input(), record, branch)
    quoted = gate_suite.RecordDecision(gate_suite.OverrideKind.OWNERS_MAC, None, None, None,
                                       "- QC-7: only here")
    checker = gate_suite._Checker(branch, PRODUCT, CORE, record)
    override = gate_suite._record_override(quoted, record, checker)
    assert override.failed == (gate_suite.Source("record", "docs/nfdr.md", "- QC-7: only here"),)
    refused = gate_suite.resolve_environment(
        dataclasses.replace(request, override=override), owners_ask=False)
    assert refused.case is RefusalCase.DECISIONS_RULE_OUT_BOTH
    assert gate_suite.refusal_case_text(refused, failed_override_source=override.failed[0]) == (
        failed_override_text("docs/nfdr.md"))
    # The same quote held by the record is accepted, wherever the branch stands.
    assert gate_suite._record_override(
        dataclasses.replace(quoted, quote="- **QC-0:** nothing to run"), record, checker
    ).failed == ()

    # A record that matches does not rescue another source that fails.
    unreadable = _parse(raw_input(ci={"finding": "readable", "runners": [
        {"platform": "linux", "source": source(anchor=MISSING_QUOTE)}]}), record)
    assert gate_suite.resolve_environment(unreadable, owners_ask=False).case is (
        RefusalCase.UNREADABLE_CI)
    arch_less = record_of(nfdr("- `environment: container` `image: i` `tag: 1`"))
    failing_amd64 = _parse(raw_input(amd64={"source": source(AMD64_FILE, AMD64_QUOTE)}), arch_less)
    assert gate_suite.resolve_environment(failing_amd64, owners_ask=False).case is (
        RefusalCase.FAILED_AMD64_SOURCE)


@pytest.mark.parametrize("record", [
    None, record_of(None), record_of(""), record_of("# Product\n\n## 7. Quality\n"),
    record_of(nfdr("- **QC-1:** nothing recorded")),
], ids=["no-record", "no-file", "empty-file", "no-section", "no-declaration"])
def test_absent_current_declaration_preserves_legacy_resolution(record):
    valid = raw_input(override=mac_decision())
    assert _parse(valid, record) == _parse(valid, None)
    resolved = gate_suite.resolve_environment(_parse(valid, record), owners_ask=False)
    assert resolved.owners_mac_cause is OwnersMacCause.PRODUCT_DECISION

    failed = raw_input(override=container_override(source=source(anchor=MISSING_QUOTE)))
    refused = gate_suite.resolve_environment(_parse(failed, record), owners_ask=False)
    assert refused.case is RefusalCase.DECISIONS_RULE_OUT_BOTH and refused.failed_sources
    owed = _parse(raw_input(languages=("python", "javascript", "shell")), record)
    assert gate_suite.resolve_environment(owed, owners_ask=False).case is (
        RefusalCase.CONFLICTING_IMAGES)
    assert owed.override is None and not owed.conflicting_decisions


def test_current_decision_preserves_resolution_precedence_and_details():
    def resolve_record(entries, raw=None, owners_ask=False):
        request = _parse(raw or raw_input(), record_of(nfdr(*entries)))
        return request, gate_suite.resolve_environment(request, owners_ask=owners_ask)

    conflicting = [OWNERS_MAC_ENTRY, CONTAINER_ENTRY]
    # The owner's ask, no CI and an unreadable CI each outrank the record, a conflict included.
    for entries in ([OWNERS_MAC_ENTRY], conflicting):
        _request, asked = resolve_record(entries, owners_ask=True)
        assert asked.owners_mac_cause is OwnersMacCause.OWNERS_ASK
        _request, no_ci = resolve_record(entries, raw_input(ci=CI_NONE))
        assert no_ci.owners_mac_cause is OwnersMacCause.NO_CI
        _request, unreadable = resolve_record(entries, raw_input(ci=CI_UNREADABLE))
        assert unreadable.case is RefusalCase.UNREADABLE_CI

    # A conflict is refused at the override position and is never an owed decision.
    request, refused = resolve_record(conflicting)
    assert request.conflicting_decisions and request.override is None
    assert refused.case is RefusalCase.CONFLICTING_DECISIONS
    answer, detail = gate_suite._classify(request, refused)
    assert answer is gate_suite.CheckAnswer.DOES_NOT_RESOLVE
    assert detail == ("the product's decision files name more than one environment for its "
                      "gates, and none of them is used")
    assert RefusalCase.CONFLICTING_DECISIONS not in gate_suite.OWED_CASES

    # Full containers keep the exact image, tag and architecture; an absent architecture is chosen
    # as an override that gives none is.
    _request, full = resolve_record([CONTAINER_ENTRY])
    assert full == container("docker.io/library/python", "3.13", Architecture.ARM64)
    _request, implicit = resolve_record(["- `environment: container` `image: i` `tag: 1`"])
    assert implicit == container("i", "1", Architecture.ARM64)
    _request, with_amd64 = resolve_record(
        ["- `environment: container` `image: i` `tag: 1`"],
        raw_input(amd64={"source": source()}))
    assert with_amd64 == container("i", "1", Architecture.AMD64)
    for missing in ("- `environment: container` `image: i`", "- `environment: container` `tag: 1`",
                    "- `environment: container`"):
        _request, undetermined = resolve_record([missing])
        assert undetermined.case is RefusalCase.UNDETERMINED_VERSION, missing
    _request, neither = resolve_record(["- `environment: neither`"])
    assert neither.case is RefusalCase.DECISIONS_RULE_OUT_BOTH and not neither.failed_sources

    # The guest follows the languages' guest tools, as an override to it does today.
    _request, guest = resolve_record(["- `environment: macos-guest`"])
    assert guest.kind is EnvironmentKind.MACOS_GUEST
    _request, no_tool = resolve_record(["- `environment: macos-guest`"],
                                       raw_input(languages=("kotlin",), candidates=[]))
    assert no_tool.case is RefusalCase.NO_GUEST_DEFAULT


# ==================================================================================================
# The product's committed decision: the check and the gates (one decision for every entry point)
# ==================================================================================================

CHECK_RECORD = CHECK_DIR / "record.json"
RECORD_FILE = ".claude/docs/nfdr.md"
CONFLICT_TEXT = ("the product's decision files name more than one environment for its gates, and "
                 "none of them is used")
MAC_DECISION_LINE = f"Environment: owners-mac {DASH} product's decision"


def stage_record(harness: CheckHarness, text: str | None, *, file: str = RECORD_FILE,
                 as_text: str | None = None) -> None:
    prepared = record_of(text, file)
    harness.files.files[CHECK_RECORD] = (
        as_text if as_text is not None else json.dumps(prepared.as_json()))


def check_with_record(text: str | None, raw: dict | None = None, **staging) -> tuple:
    harness = CheckHarness()
    stage_record(harness, text)
    harness.stage(raw if raw is not None else raw_input(guest=None), **staging)
    status = harness.invoke("--decision-record", str(CHECK_RECORD))
    return status, harness


def test_check_accepts_current_record_without_process_or_write_capabilities(no_processes):
    status, harness = check_with_record(nfdr(OWNERS_MAC_ENTRY))
    assert (status, harness.err.getvalue()) == (0, "")
    assert harness.out.getvalue() == answer_line(
        RESOLVES, "owners-mac: the product's decision files choose the owner's Mac for its gates")
    assert "Environment:" not in harness.out.getvalue()

    # A record that says `main` holds no file is a prepared answer: the sourced inputs stand.
    for text in (None, nfdr("- **QC-1:** nothing")):
        status, absent = check_with_record(
            text, raw_input(override=mac_decision(), guest=None))
        assert (status, absent.err.getvalue()) == (0, "")
        assert absent.out.getvalue() == harness.out.getvalue()
    status, owed = check_with_record(None, raw_input(languages=("python", "shell"), guest=None))
    assert status == 1 and owed.out.getvalue().startswith(f"{OWES} {DASH} ")

    # Direct callers prepare the same value in the context; nothing starts, nothing is written.
    harness = CheckHarness()
    before = dict(harness.files.files)
    out = io.StringIO()
    result = gate_suite.check_gate(
        worktree=WORKTREE, project=PROJECT, key="key1", inputs=raw_input(guest=None),
        context=gate_suite.CheckContext(
            paths=check_paths(), tracked_files=("src/app.py",),
            decision_record=record_of(nfdr(CONTAINER_ENTRY), RECORD_FILE)),
        files=harness.read_only, core_root=CORE, out=out)
    assert (result.answer, result.status) == (gate_suite.CheckAnswer.RESOLVES, 0)
    assert result.detail == ("container: the product's gates run in "
                             "docker.io/library/python:3.13, arm64")
    assert harness.files.files == before
    assert [field.name for field in dataclasses.fields(gate_suite.CheckHost)] == [
        "files", "core_root"]
    for name in ("write_text", "remove", "tracked_files", "linked_git_dirs", "main_revision"):
        assert not hasattr(gate_suite.ReadOnlyFiles, name), name


@pytest.mark.parametrize("name,staging,message", [
    ("unreadable", {"omit": True}, f"the decision-record file {CHECK_RECORD} cannot be read"),
    ("not json", {"as_text": "not json"}, None),
    ("a list", {"as_text": "[1]"},
     f"the decision-record file {CHECK_RECORD} is not the record command's output"),
    *[(f"no {field}", {"as_text": json.dumps(
        {key: value for key, value in record_of("x", RECORD_FILE).as_json().items()
         if key != field})}, f"the decision-record file {CHECK_RECORD} has no {field}")
      for field in ("repository", "file", "revision", "text")],
    ("a repository that is not text", {"as_text": json.dumps(
        {**record_of("x", RECORD_FILE).as_json(), "repository": 7})},
     f"the decision-record file {CHECK_RECORD} is not the record command's output"),
    ("text without a revision", {"as_text": json.dumps(
        {**record_of("x", RECORD_FILE).as_json(), "revision": None})},
     f"the decision-record file {CHECK_RECORD} is not the record command's output"),
    ("another repository", {"file": RECORD_FILE, "repository": "/elsewhere"},
     f"the decision-record file {CHECK_RECORD} is for product repository /elsewhere, not "
     "/work/product-repo"),
    ("another decision file", {"file": "docs/nfdr.md"},
     f"the decision-record file {CHECK_RECORD} is for decision file docs/nfdr.md, not "
     f"{RECORD_FILE}"),
])
def test_check_rejects_unreadable_malformed_or_mismatched_record_context(
        name, staging, message, no_processes):
    harness = CheckHarness()
    if not staging.get("omit"):
        if "as_text" in staging:
            harness.files.files[CHECK_RECORD] = staging["as_text"]
        else:
            prepared = record_of("x", staging["file"])
            harness.files.files[CHECK_RECORD] = json.dumps(
                {**prepared.as_json(),
                 "repository": staging.get("repository", "/work/product-repo")})
    harness.stage(raw_input(guest=None))
    status = harness.invoke("--decision-record", str(CHECK_RECORD))
    assert (status, harness.out.getvalue()) == (2, "")
    error = harness.err.getvalue()
    assert error.startswith("gate_suite: ") and error.count("\n") == 1
    if message is not None:
        assert error == f"gate_suite: {message}\n"
    else:
        assert error.startswith(
            f"gate_suite: the decision-record file {CHECK_RECORD} is not JSON: ")
    assert not [path for path in harness.read_only.reads if path.name == "ci.yml"]

    # The option stays optional: every existing way to call the check still works.
    plain = CheckHarness()
    plain.stage(raw_input(guest=None))
    assert plain.invoke() == 0


class MovingMain:
    """A `main` whose file changes between asks, as a decision committed after the plan does."""

    def __init__(self, *texts: str | None) -> None:
        self.texts = list(texts)
        self.asks = 0
        self.calls: list[tuple] = []

    def main_revision(self, repository: str) -> str | None:
        self.calls.append(("main", repository))
        self.asks += 1
        return f"rev{self.asks}"

    def file_at(self, repository: str, revision: str, path: str) -> str | None:
        self.calls.append(("file", revision, path))
        return self.texts[min(self.asks, len(self.texts)) - 1]


def gate_with(reader, *, kind: str = "relative", card: str | None = None) -> Harness:
    harness = Harness(kind=kind, card=card)
    harness.host = dataclasses.replace(harness.host, record_reader=reader)
    return harness


@pytest.mark.parametrize("gate", ["developer", "code-integrity", "seal"])
def test_gate_acquires_current_record_for_every_issuing_ask(gate):
    main = MovingMain(nfdr(OWNERS_MAC_ENTRY), nfdr(CONTAINER_ENTRY), None)
    harness = gate_with(main)
    raw = raw_input(guest=None)

    harness.run(gate=gate, raw=raw)
    assert harness.first_line == MAC_DECISION_LINE
    assert harness.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]

    # The next run reads `main` again and sees the entry that replaced the first.
    second = gate_with(main)
    second.run(gate=gate, raw=raw)
    assert second.first_line == (
        f"Environment: container {DASH} docker.io/library/python:3.13, arm64")
    assert second.processes.issued[0][0][:4] == ["podman", "run", "--rm", "-v"]

    third = gate_with(main)
    third.run(gate=gate, raw=raw)
    assert third.first_line == f"Environment: container {DASH} python:3.12, arm64"
    assert main.asks == 3 and [call[0] for call in main.calls].count("main") == 3
    assert {call[2] for call in main.calls if call[0] == "file"} == {RECORD_FILE}


def test_check_and_gate_share_current_record_refusals(no_processes):
    conflicting = nfdr(OWNERS_MAC_ENTRY, CONTAINER_ENTRY)
    status, checked = check_with_record(conflicting)
    assert (status, checked.err.getvalue()) == (1, "")
    assert checked.out.getvalue() == answer_line(DOES_NOT, CONFLICT_TEXT)

    gate = gate_with(MovingMain(conflicting))
    result = gate.run(raw=raw_input(guest=None))
    assert gate.first_line == f"Environment: unresolved {DASH} {CONFLICT_TEXT}"
    assert (result.status, result.suite_issued) == (1, False)
    assert gate.processes.issued == [] and gate.processes.probes == []
    assert gate.err.getvalue().splitlines() == [
        f"gate_suite: no environment resolves for project demo: {CONFLICT_TEXT}.",
        "To run it, change the environment entries in § 8 of the product's docs/nfdr.md on its "
        "main branch until they name one environment, with the same image, tag and architecture, "
        "or have the owner ask for the owner's Mac.",
        "The test command was not run, on the owner's Mac or anywhere else."]

    # A current quote the snapshot does not hold is the existing failed-source refusal. No input
    # reaches it end to end (the quote is cut from the snapshot it is checked against), so it is
    # proved where the check and the gate both take their words: the shared classification.
    record = record_of(nfdr(OWNERS_MAC_ENTRY), RECORD_FILE)
    lost = gate_suite.RecordDecision(gate_suite.OverrideKind.OWNERS_MAC, None, None, None,
                                     "- QC-7: no longer in the record")
    request = _parse(raw_input(guest=None), record)
    request = dataclasses.replace(request, override=gate_suite._record_override(
        lost, record, gate_suite._Checker(standard_files(), PRODUCT, CORE, record)))
    refused = gate_suite.resolve_environment(request, owners_ask=False)
    text = failed_override_text("docs/nfdr.md").replace("docs/nfdr.md", RECORD_FILE)
    assert gate_suite._classify(request, refused) == (gate_suite.CheckAnswer.DOES_NOT_RESOLVE, text)
    failed = gate_suite._failed_override_source(request, refused)
    assert gate_suite.refusal_case_text(refused, failed_override_source=failed) == text

    # An unreadable CI is refused before the record's conflict is looked at.
    status, checked = check_with_record(conflicting, raw_input(ci=CI_UNREADABLE, guest=None))
    assert checked.out.getvalue() == answer_line(
        DOES_NOT, "the runner cannot be read from the product's CI configuration")
    gate = gate_with(MovingMain(conflicting))
    assert gate.run(raw=raw_input(ci=CI_UNREADABLE, guest=None)).status == 1
    assert gate.first_line == (
        f"Environment: unresolved {DASH} the runner cannot be read from the product's CI "
        "configuration")
    assert gate.processes.issued == [] and gate.processes.probes == []

    # No CI sends the gates to the owner's Mac before the record's conflict is looked at.
    status, checked = check_with_record(conflicting, raw_input(ci=CI_NONE, guest=None))
    assert (status, checked.out.getvalue()) == (0, answer_line(
        RESOLVES, "owners-mac: the product has no CI, so its gates run on the owner's Mac"))
    gate = gate_with(MovingMain(conflicting))
    assert gate.run(raw=raw_input(ci=CI_NONE, guest=None)).status == 0
    assert gate.first_line == f"Environment: owners-mac {DASH} no CI"


def test_no_suite_and_owners_ask_do_not_acquire_a_record():
    class Forbidden:
        def main_revision(self, repository):
            raise AssertionError("a record was acquired")

        file_at = main_revision

    asked = gate_with(Forbidden())
    result = asked.run(raw=raw_input(override=None, guest=None), owners_ask=True)
    assert asked.first_line == f"Environment: owners-mac {DASH} owner's ask"
    assert result.suite_issued
    assert asked.processes.issued == [(["sh", "-c", CARD_COMMAND], WORKTREE)]
    # Even a conflicting or unreadable record is not looked at: the ask outranks it.
    assert gate_with(Forbidden()).run(owners_ask=True).suite_issued

    for gate in ("developer", "code-integrity"):
        none = gate_with(Forbidden(), card=card_text("none"))
        assert none.run(gate=gate, raw=None).suite_issued is False
        assert none.first_line == f"Environment: none {DASH} no suite"
    sealed = gate_with(Forbidden(), kind="external")
    sealed.run(gate="seal", raw=None)
    assert sealed.first_line == f"Environment: none {DASH} no suite ran"
    assert sealed.processes.probes == [] and sealed.processes.issued == []


def test_a_read_failure_on_main_stops_the_run_before_any_environment():
    harness = gate_with(FakeRecordReader(failure="fatal: bad object"))
    harness.files.files[CHECK_INPUTS] = json.dumps(raw_input(guest=None))
    status = gate_suite.main(
        ["run", "--worktree", WORKTREE, "--project", PROJECT, "--key", "key1",
         "--gate", "developer", "--inputs", str(CHECK_INPUTS)], host=harness.host,
        stdout=harness.out, stderr=harness.err)
    assert status == 2
    assert harness.out.getvalue() == "" and harness.processes.issued == []
    assert harness.err.getvalue() == (
        "gate_suite: the product's .claude/docs/nfdr.md cannot be read from the main branch of "
        "/work/product-repo: fatal: bad object\n")


def test_gate_keeps_other_source_roots_and_does_not_mutate_inputs(no_processes):
    failing_ci = raw_input(ci={"finding": "readable", "runners": [
        {"platform": "linux", "source": source(anchor=MISSING_QUOTE)}]}, guest=None)
    snapshot = copy.deepcopy(failing_ci)
    status, checked = check_with_record(nfdr(OWNERS_MAC_ENTRY), failing_ci)
    assert checked.out.getvalue() == answer_line(
        DOES_NOT, "the runner cannot be read from the product's CI configuration")
    assert failing_ci == snapshot

    gate = gate_with(MovingMain(nfdr(OWNERS_MAC_ENTRY)))
    result = gate.run(raw=failing_ci)
    assert gate.first_line == (f"Environment: unresolved {DASH} the runner cannot be read from "
                               "the product's CI configuration")
    assert result.suite_issued is False and failing_ci == snapshot


# CP-740: an entry on `main` resolves exactly as a `decisions.override` with the same content does
# today: the same check answer and detail, the same `Environment:` line and the same refusals.
SAME_AS_OVERRIDE = {
    # name: (the entry as § 8 records it, the same decision as a frozen override)
    "owners-mac": ("- `environment: owners-mac`", mac_decision()),
    "full container": (
        "- `environment: container` `image: ghcr.io/acme/builder` `tag: 7.1` "
        "`architecture: amd64`", container_override(architecture="amd64")),
    "container, no architecture": (
        "- `environment: container` `image: ghcr.io/acme/builder` `tag: 7.1`",
        container_override()),
    "container, no tag": ("- `environment: container` `image: ghcr.io/acme/builder`",
                          container_override(tag=None)),
    "container, no image": ("- `environment: container` `tag: 7.1`",
                            container_override(image=None)),
    "macos-guest": ("- `environment: macos-guest`", guest_override()),
    "neither": ("- `environment: neither`",
                {"environment": "neither", "source": source(anchor="jobs:")}),
}


@pytest.mark.parametrize("name", SAME_AS_OVERRIDE)
def test_an_entry_on_main_answers_as_the_same_override_does_at_check_and_gate(name, no_processes):
    entry, override = SAME_AS_OVERRIDE[name]

    status, from_main = check_with_record(nfdr(entry), raw_input(guest=None))
    frozen_status, frozen = check_with_record(None, raw_input(override=override, guest=None))
    assert (status, from_main.out.getvalue(), from_main.err.getvalue()) == (
        frozen_status, frozen.out.getvalue(), frozen.err.getvalue()), name

    gate = gate_with(MovingMain(nfdr(entry)))
    result = gate.run(raw=raw_input(guest=None))
    frozen_gate = gate_with(MovingMain(None))
    frozen_result = frozen_gate.run(raw=raw_input(override=override, guest=None))
    assert (gate.first_line, result.status, result.suite_issued, gate.processes.issued) == (
        frozen_gate.first_line, frozen_result.status, frozen_result.suite_issued,
        frozen_gate.processes.issued), name


def test_an_entry_on_main_naming_no_usable_environment_is_refused_in_todays_words(no_processes):
    expected = {
        "- `environment: neither`": (
            "the product's decision files say it can use neither the macOS guest nor a "
            "container, and name no environment"),
        "- `environment: container` `image: docker.io/library/python`": (
            "the version to tag docker.io/library/python with cannot be determined"),
    }
    for entry, text in expected.items():
        status, checked = check_with_record(nfdr(entry))
        assert (status, checked.out.getvalue()) == (1, answer_line(DOES_NOT, text)), entry
        gate = gate_with(MovingMain(nfdr(entry)))
        result = gate.run(raw=raw_input(guest=None))
        assert gate.first_line == f"Environment: unresolved {DASH} {text}", entry
        assert (result.status, result.suite_issued, gate.processes.issued) == (1, False, []), entry


# ==================================================================================================
# The last-run record: what a completed `run` printed, kept for the commit that closes the change
# ==================================================================================================

OTHER_WORKTREE = "/work/other-instance/.worktrees/key1"
EXTERNAL_PRODUCT = "/work/product-repo/.worktrees/key1"


def recording(harness: Harness, store) -> Harness:
    """`harness` with the record store handed to its host — the one wiring `build_host` does."""
    harness.host = dataclasses.replace(harness.host, run_records=store)
    return harness


def run_recorded(harness: Harness, *, gate: str = "developer", key: str = "key1",
                 worktree: str = WORKTREE, inputs: dict | None = None) -> int:
    argv = ["run", "--worktree", worktree, "--project", PROJECT, "--key", key, "--gate", gate]
    if inputs is not None:
        path = Path("/tmp/inputs.json")
        harness.files.files[path] = json.dumps(inputs)
        argv += ["--inputs", str(path)]
    return gate_suite.main(argv, host=harness.host, stdout=harness.out, stderr=harness.err)


def stored_run(harness: Harness, store, *, key: str = "key1", checkout: str = WORKTREE):
    return store.latest(checkout, key)


def record_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file()]


@pytest.mark.parametrize("gate", ["developer", "code-integrity", "seal"])
@pytest.mark.parametrize("suite", [
    gate_suite.Completed(0, "suite out\n", ""),
    gate_suite.Completed(3, "FAILED tests/test_a.py::test_one\n", "warn\n"),
    gate_suite.Completed(0, "no final newline", "nor here"),
])
def test_completed_run_records_exact_forwarded_evidence(tmp_path, gate, suite):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(), store)
    harness.processes.suite = suite

    status = run_recorded(harness, gate=gate, inputs=mac_raw())

    found = stored_run(harness, store)
    assert found == gate_suite.GateRun(
        key="key1", checkout=gate_suite.canonical_checkout(WORKTREE),
        environment_line=f"Environment: owners-mac {DASH} no CI",
        stdout=harness.out.getvalue(), stderr=harness.err.getvalue(), status=status)
    assert status == suite.status
    assert found.stdout == f"Environment: owners-mac {DASH} no CI\n{suite.stdout}"
    assert found.stderr == suite.stderr


def test_refused_and_no_suite_runs_record_actual_output(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")

    refused = recording(Harness(), store)
    assert run_recorded(refused, inputs=raw_input(ci=CI_UNREADABLE)) == gate_suite.REFUSAL_STATUS
    found = stored_run(refused, store)
    assert found.status == gate_suite.REFUSAL_STATUS
    assert found.environment_line.startswith(f"Environment: unresolved {DASH} ")
    assert (found.stdout, found.stderr) == (refused.out.getvalue(), refused.err.getvalue())
    assert refused.processes.issued == []

    not_ready = recording(Harness(), store)
    not_ready.processes.when("podman", "info", result=gate_suite.Completed(1, "", "no machine\n"))
    status = run_recorded(not_ready, inputs=container_raw())
    found = stored_run(not_ready, store)
    assert found.status == status == gate_suite.REFUSAL_STATUS
    assert (found.stdout, found.stderr) == (not_ready.out.getvalue(), not_ready.err.getvalue())
    assert found.stderr != ""

    no_suite = recording(Harness(card="**Test command:** none\n"), store)
    assert run_recorded(no_suite) == 0
    found = stored_run(no_suite, store)
    assert found.environment_line == f"Environment: none {DASH} no suite"
    assert (found.stdout, found.stderr, found.status) == (
        f"Environment: none {DASH} no suite\n", "", 0)

    seal_no_suite = recording(Harness(kind="external"), store)
    assert run_recorded(seal_no_suite, gate="seal") == 0
    assert stored_run(seal_no_suite, store).environment_line == (
        f"Environment: none {DASH} no suite ran")


def test_a_handled_input_error_is_recorded_with_no_environment_line(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(card="**Product path:** .claude\n"), store)

    assert run_recorded(harness, inputs=mac_raw()) == gate_suite.ERROR_STATUS

    found = stored_run(harness, store)
    assert found.status == gate_suite.ERROR_STATUS
    assert found.environment_line is None and found.stdout == ""
    assert found.stderr == harness.err.getvalue() and found.stderr.startswith("gate_suite: ")


def test_an_error_before_the_checkout_is_known_records_nothing(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(), store)

    def refuse(worktree, project, key):
        raise gate_suite.ContractError("missing-project-doc: no project.md")

    harness.host = dataclasses.replace(harness.host, contract=refuse)
    assert run_recorded(harness, inputs=mac_raw()) == gate_suite.ERROR_STATUS
    assert record_files(tmp_path / "runs") == []
    assert stored_run(harness, store) is None


def test_run_record_includes_guest_cleanup_diagnostics(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(), store)
    harness.processes.when("tart", "exec", "swift-guest", "sh", "-c", CLEAN,
                           result=gate_suite.Completed(1, "", "busy\n"))

    assert run_recorded(harness, inputs=guest_raw()) == 0

    found = stored_run(harness, store)
    cleanup = (f"gate_suite: the copy of this run's checkout at {SCRATCH} in the macOS guest "
               f"swift-guest could not be removed.")
    assert cleanup in found.stderr and found.stderr == harness.err.getvalue()
    assert found.status == 0 and found.stdout == harness.out.getvalue()


def test_latest_completed_gate_run_replaces_previous_evidence(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(), store)
    outcomes = [("developer", gate_suite.Completed(0, "first\n", "")),
                ("seal", gate_suite.Completed(4, "second\n", "err\n")),
                ("code-integrity", gate_suite.Completed(0, "third\n", ""))]

    for gate, suite in outcomes:
        harness.processes.suite = suite
        harness.out.seek(0)
        harness.out.truncate()
        harness.err.seek(0)
        harness.err.truncate()
        status = run_recorded(harness, gate=gate, inputs=mac_raw())
        found = stored_run(harness, store)
        assert (found.status, found.stdout, found.stderr) == (
            status, f"Environment: owners-mac {DASH} no CI\n{suite.stdout}", suite.stderr)
        assert len(record_files(tmp_path / "runs")) == 1


def test_gate_records_are_isolated_by_checkout_and_key(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")

    first = recording(Harness(), store)
    first.processes.suite = gate_suite.Completed(0, "key1 here\n", "")
    run_recorded(first, key="key1", inputs=mac_raw())

    second_key = recording(Harness(), store)
    second_key.processes.suite = gate_suite.Completed(7, "key2 here\n", "")
    run_recorded(second_key, key="key2", inputs=mac_raw())

    other = recording(Harness(), store)
    other.contract = {**contract(), "pipeline_worktree": OTHER_WORKTREE,
                      "product_worktree": OTHER_WORKTREE}
    other.files.files[Path(OTHER_WORKTREE) / "system/projects/demo/project.md"] = card_text()
    other.processes.suite = gate_suite.Completed(9, "other instance\n", "")
    run_recorded(other, key="key1", worktree=OTHER_WORKTREE, inputs=mac_raw())

    assert "key1 here" in store.latest(WORKTREE, "key1").stdout
    assert "key2 here" in store.latest(WORKTREE, "key2").stdout
    assert "other instance" in store.latest(OTHER_WORKTREE, "key1").stdout
    assert store.latest(OTHER_WORKTREE, "key2") is None
    assert store.latest("/work/never-ran", "key1") is None


def test_interleaved_publications_cannot_read_each_other(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    checkout = "/work/a"

    def run(key: str, text: str, status: int):
        return gate_suite.GateRun(key=key, checkout=checkout, environment_line=None,
                                  stdout=text, stderr="", status=status)

    store.publish(run("one", "one-a", 0), [checkout])
    store.publish(run("two", "two-a", 1), [checkout])
    store.publish(run("one", "one-b", 2), [checkout])

    assert (store.latest(checkout, "one").stdout, store.latest(checkout, "one").status) == (
        "one-b", 2)
    assert (store.latest(checkout, "two").stdout, store.latest(checkout, "two").status) == (
        "two-a", 1)


def test_pipeline_and_code_checkout_aliases_retrieve_the_same_run(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(kind="external"), store)
    harness.contract = {**contract("external"), "pipeline_worktree": WORKTREE,
                        "code_worktree": EXTERNAL_PRODUCT}
    harness.processes.suite = gate_suite.Completed(0, "one run\n", "")

    run_recorded(harness, inputs=mac_raw())

    from_instance = store.latest(WORKTREE, "key1")
    from_product = store.latest(EXTERNAL_PRODUCT, "key1")
    assert from_instance is not None and from_product is not None
    assert (from_instance.stdout, from_instance.status, from_instance.environment_line) == (
        from_product.stdout, from_product.status, from_product.environment_line)
    assert from_instance.checkout == gate_suite.canonical_checkout(WORKTREE)
    assert from_product.checkout == gate_suite.canonical_checkout(EXTERNAL_PRODUCT)
    assert len(record_files(tmp_path / "runs")) == 2


def test_equivalent_path_aliases_agree(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    store.publish(gate_suite.GateRun(key="k", checkout=str(real), environment_line=None,
                                     stdout="x", stderr="", status=0), [str(real)])

    assert store.latest(str(link), "k") == store.latest(str(real), "k")
    assert store.latest(f"{real}/../real", "k") is not None
    assert gate_suite.canonical_checkout(str(link)) == gate_suite.canonical_checkout(str(real))


def test_record_lookup_verifies_embedded_identity(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    assert store.latest("/work/a", "k") is None

    store.publish(gate_suite.GateRun(key="k", checkout="/work/a", environment_line=None,
                                     stdout="mine", stderr="", status=0), ["/work/a"])
    mine = store.path_for("/work/a", "k")
    # A record found at the wrong address — another checkout's, another key's — is not accepted
    # because its path exists.
    for wrong_checkout, wrong_key in (("/work/b", "k"), ("/work/a", "other")):
        target = store.path_for(wrong_checkout, wrong_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(mine.read_bytes())
        assert store.latest(wrong_checkout, wrong_key) is None
    mine.write_text("{ not json")
    assert store.latest("/work/a", "k") is None


def test_the_record_lives_under_the_temporary_directory_namespace():
    assert gate_suite.RUN_RECORDS_NAMESPACE == "kensaiapp-gate-runs"
    store = gate_suite.default_run_records()
    assert store.root == Path(tempfile.gettempdir()) / "kensaiapp-gate-runs"
    assert gate_suite.build_host().run_records.root == store.root


def test_atomic_publication_never_exposes_partial_evidence(tmp_path):
    seen: list[object] = []
    store: gate_suite.FileRunRecords

    def run(text: str):
        return gate_suite.GateRun(key="k", checkout="/work/a", environment_line=None,
                                  stdout=text, stderr="", status=0)

    def observing_replace(source, destination):
        # Mid-publication: the replacement exists only as a temporary file, so a reader still
        # sees the previous complete record, never half of the new one.
        seen.append(store.latest("/work/a", "k"))
        os.replace(source, destination)

    store = gate_suite.FileRunRecords(tmp_path / "runs", replace=observing_replace)
    store.publish(run("old"), ["/work/a"])
    store.publish(run("new" * 10_000), ["/work/a"])

    assert seen[0] is None and seen[1].stdout == "old"
    assert store.latest("/work/a", "k").stdout == "new" * 10_000
    assert len(record_files(tmp_path / "runs")) == 1


def test_overlapping_publications_leave_one_complete_last_published_record(tmp_path):
    def run(text: str):
        return gate_suite.GateRun(key="k", checkout="/work/a", environment_line=None,
                                  stdout=text, stderr="", status=0)

    inner_done: list[bool] = []

    def overlapping_replace(source, destination):
        if not inner_done:
            inner_done.append(True)
            store.publish(run("inner"), ["/work/a"])
        os.replace(source, destination)

    store = gate_suite.FileRunRecords(tmp_path / "runs", replace=overlapping_replace)
    store.publish(run("outer"), ["/work/a"])

    # The outer publication's replacement landed last, so it is the last published one, whole.
    assert store.latest("/work/a", "k") == run("outer")
    assert len(record_files(tmp_path / "runs")) == 1


def test_recording_failure_preserves_gate_observables(tmp_path):
    def observed(store):
        harness = Harness()
        harness.processes.suite = gate_suite.Completed(5, "suite out\n", "suite err\n")
        if store is not None:
            recording(harness, store)
        status = run_recorded(harness, inputs=mac_raw())
        return status, harness.events.log

    baseline = observed(None)

    def failing_replace(source, destination):
        raise OSError(errno.ENOSPC, "No space left on device")

    root = tmp_path / "runs"
    failing = gate_suite.FileRunRecords(root, replace=failing_replace)
    assert observed(failing) == baseline
    assert record_files(root) == []
    assert failing.latest(WORKTREE, "key1") is None

    class UnwritableStore:
        def publish(self, run, checkouts):
            raise PermissionError(errno.EACCES, "Permission denied")

    assert observed(UnwritableStore()) == baseline


def test_recording_failure_keeps_the_previous_complete_record(tmp_path):
    root = tmp_path / "runs"
    store = gate_suite.FileRunRecords(root)
    harness = recording(Harness(), store)
    harness.processes.suite = gate_suite.Completed(0, "first\n", "")
    run_recorded(harness, inputs=mac_raw())
    before = stored_run(harness, store)

    def failing_replace(source, destination):
        raise OSError(errno.EIO, "I/O error")

    broken = recording(Harness(), gate_suite.FileRunRecords(root, replace=failing_replace))
    broken.processes.suite = gate_suite.Completed(1, "second\n", "")
    assert run_recorded(broken, inputs=mac_raw()) == 1

    assert stored_run(harness, store) == before


def test_recording_uses_a_separate_storage_port(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    harness = recording(Harness(), store)

    run_recorded(harness, inputs=guest_raw())

    # The guest-token port still writes and removes only its own file; the record never uses it.
    assert harness.files.written == [TOKEN_PATH]
    assert harness.files.removed == [TOKEN_PATH]
    assert stored_run(harness, store) is not None

    # An existing Host is built without the port, and a direct run_gate call records nothing.
    plain = Harness()
    assert plain.host.run_records is None
    direct = recording(Harness(), gate_suite.FileRunRecords(tmp_path / "direct"))
    direct.run(raw=mac_raw())
    assert record_files(tmp_path / "direct") == []


def test_check_and_record_commands_do_not_publish_run_evidence(tmp_path):
    store = gate_suite.FileRunRecords(tmp_path / "runs")
    held = recording(Harness(), store).host

    checked = CheckHarness()
    checked.stage(raw_input(guest=None))
    status = gate_suite.main(
        ["check", "--worktree", WORKTREE, "--project", PROJECT, "--key", "key1",
         "--inputs", str(CHECK_INPUTS), "--paths", str(CHECK_PATHS),
         "--tracked-files", str(CHECK_TRACKED)],
        host=held, check_host=checked.host, host_factory=forbidden_host,
        stdout=checked.out, stderr=checked.err)
    plain = CheckHarness()
    plain.stage(raw_input(guest=None))
    assert plain.invoke() == status
    assert (checked.out.getvalue(), checked.err.getvalue()) == (
        plain.out.getvalue(), plain.err.getvalue())

    recorded = RecordHarness(FakeRecordReader("text\n"))
    out = io.StringIO()
    gate_suite.main(
        ["record", "--worktree", WORKTREE, "--project", PROJECT, "--key", "key1",
         "--paths", str(CHECK_PATHS)],
        host=held, record_host=gate_suite.RecordHost(files=ReadOnlyFiles(recorded.files),
                                                     reader=recorded.reader),
        host_factory=forbidden_host, stdout=out, stderr=io.StringIO())
    assert json.loads(out.getvalue())["text"] == "text\n"
    assert record_files(tmp_path / "runs") == []
