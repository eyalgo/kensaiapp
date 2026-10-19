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
        self.read: list[Path] = []

    def read_text(self, path: Path) -> str | None:
        self.read.append(path)
        return self.files.get(path)

    def tracked_files(self, root: Path) -> list[str]:
        return list(self.tracked)


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
    "f-owners-mac": (raw_input(override={"environment": "owners-mac",
                                         "source": source(anchor="jobs:")}),
                     RefusalCase.DECISIONS_NAME_OWNERS_MAC),
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


def test_a_recorded_override_that_names_the_owners_mac_is_refused_not_obeyed():
    raw, case = REFUSALS["f-owners-mac"]
    assert resolve(raw).case is case
    assert resolve(raw, owners_ask=True).owners_mac_cause is OwnersMacCause.OWNERS_ASK


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
    (lambda: raw_input(override={"environment": "owners-mac", "source": source(anchor="jobs:")}),
     "name the owner's Mac, which a product record cannot choose", "f"),
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


def test_only_the_languages_the_card_declares_are_probed_in_the_guest():
    # A Swift-only card never asks the guest for cargo, though Rust's packet names it.
    harness = Harness()
    harness.run(raw=raw_input(ci=ci_readable("macos"), languages=(), declared=["Swift"]))
    tool_probes = [argv[-1] for argv in harness.processes.probes if "command -v" in argv[-1]]
    assert tool_probes == ["command -v swift"]
    [(argv, _cwd)] = harness.processes.issued
    assert "cargo" not in argv[-1]
