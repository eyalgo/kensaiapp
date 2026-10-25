"""The setup step's launcher: the card half, then the skeleton half, in that order.

Layer 5 throughout (`<CORE>/doctrine/engineering/languages/shell/testing.md` § The layers) — the real
script through its real entry point, with the outside world stubbed. Two things are stubbed and
nothing else: a fake `claude` on `PATH` that records the argv it was handed, in the shape
`core/launchers/launch-eval-fix/test_launch_eval_fix.py` uses one; and the skeleton launcher, reached through
`LAUNCH_PRODUCT_CARD_SKELETON`, which records its own argv and replays a scripted stdout so a test
can say what its dry run found.

No case pays for a model run.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest

import launcher_telemetry_test_support as support
from kensaiapp_launchers_conftest import _plugin_skills
from path_test_support import path_without_caffeinate
from provenance_test_support import (
    assert_provenance_stamped,
    REFUSED_OWN_INTELLIGENCE,
    place_own_skill,
    place_refused_own_skill,
)
from test_skill_launcher_telemetry import install_telemetry_command

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
# The delivered provider file: the tracked template at the instance root, copied into the instance
# a case runs for. No suite leans on a live `.providers.toml`, which is untracked.
_PROVIDER_EXAMPLE = Path(__file__).resolve().parents[3] / ".providers.toml.example"

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$CLAUDE_ARGV_LOG"
exit "${CLAUDE_STUB_EXIT:-0}"
"""

# Records one line per invocation — the whole argv, tab-joined — so a test can count invocations as
# well as read them. The dry-run reply is scripted per test: SKELETON_DRY_STDOUT is what the first
# (dry) invocation prints, and the launcher's read of it is what task 5 turns on.
# caffeinate is stubbed for the same reason claude is: `--keep-awake` wraps the card half, so an
# unstubbed one would hold the real machine awake for the length of the suite.
CAFFEINATE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CAFFEINATE_ARGV_LOG"
# Real caffeinate takes its own flags, then the command it wraps. Drop the flags before exec'ing,
# or the command inherits them — which is what the wrapper form means and what this stub must model.
while [ $# -gt 0 ]; do
  case "$1" in
    -*) shift ;;
    *)  break ;;
  esac
done
exec "$@"
"""

SKELETON_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$SKELETON_ARGV_LOG"
case "$*" in
  *--dry-run*) printf '%s\\n' "${SKELETON_DRY_STDOUT:-DRY RUN — would create:}" ;;
  *)           printf 'Wrote the skeleton.\\n' ;;
esac
exit "${SKELETON_STUB_EXIT:-0}"
"""


@pytest.fixture
def run(tmp_path):
    """`run(*argv, use_env=None) -> CompletedProcess`, with `tmp_path` standing in for the instance
    root. Helpers hang off the callable: `run.project(...)` writes a project card,
    `run.claude_argv()` / `run.skeleton_argv()` return what each stub recorded."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude_stub = bin_dir / "claude"
    claude_stub.write_text(CLAUDE_STUB)
    claude_stub.chmod(0o755)

    caffeinate_stub = bin_dir / "caffeinate"
    caffeinate_stub.write_text(CAFFEINATE_STUB)
    caffeinate_stub.chmod(0o755)

    skeleton_stub = tmp_path / "skeleton_stub.sh"
    skeleton_stub.write_text(SKELETON_STUB)
    skeleton_stub.chmod(0o755)

    claude_log = tmp_path / "claude_argv.log"
    skeleton_log = tmp_path / "skeleton_argv.log"
    caffeinate_log = tmp_path / "caffeinate_argv.log"

    env = dict(os.environ)
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_PROVIDER_EXAMPLE.read_text(encoding="utf-8"))
    env["HOME"] = str(tmp_path / "home")
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["CLAUDE_ARGV_LOG"] = str(claude_log)
    env["SKELETON_ARGV_LOG"] = str(skeleton_log)
    env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)
    env["LAUNCH_PRODUCT_CARD_SKELETON"] = str(skeleton_stub)
    # The skills are looked up under the host root; here the host and the instance are one tree.
    env["LAUNCH_PRODUCT_CARD_SKILLS_ROOT"] = str(tmp_path)
    # Points at a path nothing occupies, so this fixture never reads this machine's real
    # published telemetry endpoint (`a-launcher-tags-its-own-run`) — a launcher's own suite is
    # isolated from real machine state exactly like the skeleton and the two stubs above.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    # Explicitly unconfigured: absent would let the source host's own setting answer, and a case
    # that is not about the telemetry command must not depend on this machine's package.
    env[support.COMMAND_VARIABLE] = ""

    def _run(*argv, use_env=None):
        return subprocess.run(
            [str(_SCRIPT), *argv],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=use_env if use_env is not None else env,
        )

    def _project(name="example-product", product_path="products/thing", card=None, languages="pylang"):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True, exist_ok=True)
        if card is None:
            lines = [f"# {name}", "", f"**Product path:** {product_path}"]
            if languages is not None:
                lines.append(f"**Languages:** {languages}")
            card = "\n".join(lines) + "\n"
        (project_dir / "project.md").write_text(card)
        product = Path(product_path)
        (product if product.is_absolute() else tmp_path / product_path).mkdir(
            parents=True, exist_ok=True
        )
        return project_dir

    _run.root = tmp_path
    _run.env = env
    _run.project = _project
    _run.claude_argv = lambda: claude_log.read_text().splitlines() if claude_log.exists() else []
    _run.skeleton_argv = lambda: (
        skeleton_log.read_text().splitlines() if skeleton_log.exists() else []
    )
    _run.caffeinate_argv = lambda: (
        caffeinate_log.read_text().splitlines() if caffeinate_log.exists() else []
    )
    return _run


# --- Task 1 — the launcher takes a project name -------------------------------------------------


def test_the_script_is_executable_and_parses():
    assert os.access(_SCRIPT, os.X_OK), "the launcher must be executable"
    parsed = subprocess.run(["bash", "-n", str(_SCRIPT)], capture_output=True, text=True)
    assert parsed.returncode == 0, parsed.stderr


def test_no_argument_dies_with_the_usage_line(run):
    result = run()

    assert result.returncode != 0
    assert "usage:" in result.stderr
    assert "<project>" in result.stderr


def test_an_argument_holding_a_slash_is_refused_as_a_path(run):
    """Identity in, file derived. A path lets a caller name a directory the card never points at,
    and the two halves would then disagree about which product they are acting on."""
    result = run("system/projects/example-product")

    assert result.returncode != 0
    assert "project name" in result.stderr


def test_more_than_one_positional_is_refused(run):
    run.project("example-product")

    result = run("example-product", "extra")

    assert result.returncode != 0


def test_a_project_with_no_card_is_refused_naming_the_path(run):
    result = run("ghost")

    assert result.returncode != 0
    assert "system/projects/ghost/project.md" in result.stderr


# --- Task 2 — the card is resolved before anything is spent -------------------------------------


def test_a_card_with_no_product_path_is_refused_naming_the_card(run):
    run.project("example-product", card="# example-product\n\n**Languages:** pylang\n")

    result = run("example-product")

    assert result.returncode != 0
    assert "Product path" in result.stderr
    assert "system/projects/example-product/project.md" in result.stderr


def test_a_product_path_still_carrying_its_placeholder_is_refused(run):
    """`project-stamp` stamps `products/<product-dir>`. A card still carrying it has never been
    pointed at a product, and both halves resolve every file from that field."""
    run.project("example-product", product_path="products/<product-dir>")

    result = run("example-product")

    assert result.returncode != 0
    assert "placeholder" in result.stderr


@pytest.mark.parametrize(
    "card",
    [
        "# example-product\n\n**Languages:** pylang\n",
        None,
    ],
    ids=["no-product-path", "placeholder-product-path"],
)
def test_a_card_refusal_happens_before_any_model_run(run, card):
    """The card half costs a model run. A card that cannot drive it is worth finding before that is
    spent, which is only observable as the stub's argv log being empty."""
    if card is None:
        run.project("example-product", product_path="products/<product-dir>")
    else:
        run.project("example-product", card=card)

    result = run("example-product")

    assert result.returncode != 0
    assert run.claude_argv() == []
    assert run.skeleton_argv() == []


# --- Task 3 — the card half runs in Principal PM posture, in the foreground ---------------------


def test_dry_run_prints_the_pin_line(run):
    # Task 15: pin_enter runs right after the CORE_DIR guard, ahead of everything else.
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_the_command_carries_the_pin_delivery_and_the_launchers_own_flags(run):
    # Task 15: the card half's argv comes from the adapter's --print-argv, carrying the pin
    # delivery alongside the launcher's own --agent (the group --add-dir is covered by the
    # existing satellite test above — Sub-job I keeps it, unlike the skill launcher's own).
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.strip().startswith("claude"))
    argv = shlex.split(line.strip())
    assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert argv[argv.index("--setting-sources") + 1] == "user"
    assert "--plugin-dir" in argv


def test_the_claude_launch_grants_product_card(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.strip().startswith("claude"))
    listed, groups = _plugin_skills(shlex.split(line.strip()))
    assert "product-card" in listed
    assert groups == {"interactive-product"}


def test_the_variable_is_no_force_and_the_command_is_unchanged(run):
    """product-card reads no force: an exported provider neither changes the command nor
    refuses."""
    run.project("example-product")
    env = dict(run.env, KENSAIAPP_AGENT_PROVIDER="codex")

    result = run("example-product", "--dry-run", use_env=env)

    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.strip().startswith("claude"))
    argv = shlex.split(line.strip())
    assert "-p" in argv


def test_product_card_still_runs_in_the_foreground(run):
    # Task 15: shape print for product-card (claude -p), never background — the card half's
    # output gates the skeleton half, so it cannot be a detached run (see the launcher's header).
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.strip().startswith("claude"))
    argv = shlex.split(line.strip())
    assert "-p" in argv
    assert "--bg" not in argv


def test_dry_run_prints_the_card_command_and_launches_nothing(run):
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "product-card" in result.stdout
    assert "principal-pm" in result.stdout
    assert run.claude_argv() == []
    assert run.skeleton_argv() == []


def test_the_card_command_carries_print_mode_and_never_bg(run):
    """`--bg` would detach the half whose output the skeleton half reads, so the skeleton would run
    against the card as it stood before. `-p` is the foreground form. Read as TOKENS, never a raw
    substring of stdout — the pin delivery's own `--agents` JSON (Task 15) carries `claude --bg` in
    an agent file's own prose, which a substring check would misread as the card command itself."""
    run.project("example-product")

    result = run("example-product", "--dry-run")

    line = next(l for l in result.stdout.splitlines() if l.strip().startswith("claude"))
    argv = shlex.split(line.strip())
    assert "-p" in argv
    assert "--bg" not in argv


def test_a_real_run_hands_claude_what_the_dry_run_printed(run):
    run.project("example-product")

    planned = run("example-product", "--dry-run")
    actual = run("example-product")

    assert actual.returncode == 0, actual.stderr
    recorded = run.claude_argv()
    assert recorded, "the card half must actually run"
    for token in ("-p", "--agent", "principal-pm"):
        assert token in recorded, recorded
        assert token in planned.stdout



def test_a_satellite_is_granted_the_hosts_product_card_group(run, tmp_path_factory):
    """A satellite holds no skills: product-card is found in the host, and its group there is
    what the card half is granted."""
    run.project("example-product")
    host = tmp_path_factory.mktemp("host")
    skill_dir = host / "skills" / "principal-pm" / ".claude" / "skills" / "product-card"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: product-card\n---\n")
    run.env["LAUNCH_PRODUCT_CARD_SKILLS_ROOT"] = str(host)
    assert not (run.root / "skills").exists()

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    # `--add-dir` and its value, whichever spelling the adapter wrote (`b7fe07e8d`: the pin's own
    # is one token, but a group grant like this one is not required to be).
    assert re.search(
        rf"--add-dir[= ]{re.escape(str(host / 'skills' / 'principal-pm'))}",
        " ".join(result.stdout.split()),
    )


# --- Task 4 — a failed card half stops the run before the skeleton ------------------------------


def test_a_failed_card_half_never_reaches_the_skeleton(run):
    """The defect the order exists to prevent: a skeleton placed after a failed card step is placed
    against the card as it stood before, and the run looks like it worked. The exit code alone would
    not catch it — the skeleton's own argv log is what does."""
    run.project("example-product")
    env = dict(run.env)
    env["CLAUDE_STUB_EXIT"] = "3"

    result = run("example-product", use_env=env)

    assert result.returncode != 0
    assert run.claude_argv(), "the card half must have been attempted"
    assert run.skeleton_argv() == [], "the skeleton half must not have been reached"


def test_a_failed_card_half_says_which_half_failed(run):
    run.project("example-product")
    env = dict(run.env)
    env["CLAUDE_STUB_EXIT"] = "3"

    result = run("example-product", use_env=env)

    assert "card" in result.stderr.lower()


# --- Task 5 — the skeleton half dry-runs first --------------------------------------------------

_NOTHING_TO_CREATE = "DRY RUN — would create:"
_SOMETHING_TO_CREATE = "DRY RUN — would create:\n  file: Cargo.toml"


def test_an_already_framed_product_is_reported_and_the_skeleton_runs_once(run):
    """The owner's rule is "run the skeleton only where there is none". product-skeleton already
    never overwrites and leaves a built frame whole, so what is owed is that somebody says so — and
    the only thing that tells the two apart is how many times that half was invoked."""
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _NOTHING_TO_CREATE

    result = run("example-product")

    assert result.returncode == 0, result.stderr
    assert len(run.skeleton_argv()) == 1, run.skeleton_argv()
    assert "--dry-run" in run.skeleton_argv()[0]
    assert "already" in result.stdout


def test_an_unframed_product_gets_the_skeleton_placed(run):
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _SOMETHING_TO_CREATE

    result = run("example-product", use_env=env)

    assert result.returncode == 0, result.stderr
    recorded = run.skeleton_argv()
    assert len(recorded) == 2, recorded
    assert "--dry-run" in recorded[0]
    assert "--dry-run" not in recorded[1]


def test_the_skeleton_half_is_handed_the_project_name(run):
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _SOMETHING_TO_CREATE

    run("example-product", use_env=env)

    recorded = run.skeleton_argv()
    # `all()` over an empty list is True — the assertion below says nothing until this one holds.
    assert recorded, "the skeleton half must have been invoked at all"
    assert all("example-product" in line for line in recorded), recorded


# --- Task 6 — the report names both halves and what each did ------------------------------------


def test_a_successful_run_reports_both_halves(run):
    """One command, two steps. A caller who reads only this output must be able to say which half
    did what, without opening two logs."""
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _SOMETHING_TO_CREATE

    result = run("example-product", use_env=env)

    assert result.returncode == 0, result.stderr
    assert "Card half" in result.stdout
    assert "Skeleton half" in result.stdout
    assert "placed" in result.stdout


def test_the_already_framed_run_reports_the_skeleton_as_skipped(run):
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _NOTHING_TO_CREATE

    result = run("example-product", use_env=env)

    assert "Card half" in result.stdout
    assert "already carries its skeleton" in result.stdout


def test_a_run_stopped_at_the_card_half_names_the_skeleton_as_not_reached(run):
    run.project("example-product")
    env = dict(run.env)
    env["CLAUDE_STUB_EXIT"] = "3"

    result = run("example-product", use_env=env)

    assert result.returncode != 0
    assert "not reached" in result.stderr.lower()


# --- Task 7 — the manifest enumerates it --------------------------------------------------------

_STRUCTURE_MAP = Path(__file__).resolve().parents[2] / "doctrine" / "setup" / "kensaiapp_structure.md"


def _section(heading: str) -> str:
    text = _STRUCTURE_MAP.read_text()
    start = text.index(heading)
    end = text.index("\n### ", start + 1)
    return text[start:end]


def test_the_manifest_names_this_launcher_and_its_suite():
    """A launcher absent from the manifest is invisible to anyone reading the tree for what exists,
    which is the only reason that section is kept."""
    section = _section("### Owner-run launcher folder")

    assert "core/launchers/product-card/launcher.sh" in section
    assert "core/launchers/product-card/test_product_card.py" in section


def test_the_manifest_records_that_this_launcher_waits():
    """The one fact in the entry a later edit can silently invalidate. Every sibling backgrounds its
    run; this one does not, and the manifest is where a reader comparing them finds out why."""
    section = _section("### Owner-run launcher folder")
    entry = section[section.index("core/launchers/product-card/launcher.sh") :]
    entry = entry[: entry.index("\n- `")]

    assert "--bg" in entry
    assert "product-skeleton" in entry


# --- Task 3, coverage the plan's behaviours did not name ----------------------------------------


def test_keep_awake_wraps_the_card_half_and_never_detaches_a_hold(run):
    """`--keep-awake` was added beyond the plan, so it owes its own cases. The wrapper form is what
    keeps `core/tools/test_keep_awake_binding.py` from reaching this file: caffeinate holds exactly
    as long as its own child, so there is no `-w` on a pid and nothing to release."""
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _SOMETHING_TO_CREATE

    result = run("example-product", "--keep-awake", use_env=env)

    assert result.returncode == 0, result.stderr
    recorded = run.caffeinate_argv()
    assert recorded, "caffeinate must have wrapped the card half"
    assert "-w" not in recorded[0].split(), recorded
    assert "claude" in recorded[0]


def test_keep_awake_without_caffeinate_on_path_still_runs_the_card_half_and_says_so(run):
    """caffeinate is macOS-only. Where it is absent, `--keep-awake` must not stop the card half:
    the launcher runs it unwrapped and reports the skip."""
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _SOMETHING_TO_CREATE
    bin_dir = run.root / "bin"
    (bin_dir / "caffeinate").unlink()
    env["PATH"] = path_without_caffeinate(env, run.root / "path-without-caffeinate")

    result = run("example-product", "--keep-awake", use_env=env)

    assert result.returncode == 0, result.stderr
    assert "caffeinate not found" in result.stdout and "skipped" in result.stdout, result.stdout
    assert run.caffeinate_argv() == []
    assert run.claude_argv(), "the card half must still have run"


def test_without_keep_awake_no_hold_is_taken_at_all(run):
    run.project("example-product")
    env = dict(run.env)
    env["SKELETON_DRY_STDOUT"] = _SOMETHING_TO_CREATE

    run("example-product", use_env=env)

    assert run.caffeinate_argv() == []


def test_keep_awake_is_reported_by_the_dry_run(run):
    run.project("example-product")

    result = run("example-product", "--keep-awake", "--dry-run")

    assert "caffeinate" in result.stdout


def test_dry_run_states_the_arm_it_would_run_under(run, tmp_path):
    """`a-launcher-tags-its-own-run` — a dry run that hides the instrument is a dry run that
    lies. With a runnable telemetry command and a published endpoint file present,
    `run_telemetry` prints the arm it derived (this launcher's own directory name) even though
    the card half is `claude -p`, not `--bg`, and nothing is actually spawned under --dry-run."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    install_telemetry_command(tmp_path / "home", run.env)
    run.project("example-product")

    result = run("example-product", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.arm=product-card" in result.stdout
    assert "--settings" in result.stdout, "a dry run that hides the settings hides what a backgrounded run needs"


# --- the run's provenance (CP-218, CP-221, CP-227, CP-229, CP-230) -----------------------------


def test_the_run_telemetry_call_carries_the_four_provenance_keys():
    support.assert_run_telemetry_call_carries_provenance(_SCRIPT)


def _dry_run_with_endpoint(run, tmp_path):
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    install_telemetry_command(tmp_path / "home", run.env)
    run.project("example-product")
    result = run("example-product", "--dry-run")
    assert result.returncode == 0, result.stderr
    return result


def test_stamp_is_provider_claude_source_default_with_no_model_or_effort_and_the_argv_carries_neither(  # noqa: E501 — the instruction's own case name
    run, tmp_path
):
    """product-card resolves and has no intelligence/ folder, as on this tree: the card half is
    handed no model and no effort, stamped `default` after the project pair, and still runs as
    `claude -p` in the foreground."""
    place_own_skill(tmp_path, "product-card")
    result = _dry_run_with_endpoint(run, tmp_path)

    assert "kensai.project=example-product" in result.stdout
    assert_provenance_stamped(
        result.stdout, provider="claude", source="default", after=("project",)
    )
    assert "--model" not in result.stdout and "--effort" not in result.stdout
    assert re.search(r"\s-p\s", result.stdout), result.stdout


def test_an_own_skill_with_an_intelligence_file_is_handed_and_stamped_the_same_pair(run, tmp_path):
    """The skill dir the launcher already resolves is the one whose intelligence file the run goes
    at, and the stamp records the same pair from the same answer (CP-218)."""
    place_own_skill(tmp_path, "product-card", "**Model:** claude-opus-5-5\n**Effort:** high\n")
    result = _dry_run_with_endpoint(run, tmp_path)

    assert_provenance_stamped(
        result.stdout,
        provider="claude",
        model="claude-opus-5-5",
        effort="high",
        source="intelligence",
    )
    assert re.search(r"--model\s+claude-opus-5-5\s", result.stdout), result.stdout
    assert re.search(r"--effort\s+high\s", result.stdout), result.stdout


def test_an_unresolvable_own_skill_is_default_and_the_launch_proceeds(run, tmp_path):
    """The fixture's skills root holds no product-card: not a refusal, the provider default."""
    result = _dry_run_with_endpoint(run, tmp_path)

    assert_provenance_stamped(result.stdout, provider="claude", source="default")
    assert "--model" not in result.stdout and "--effort" not in result.stdout


@pytest.mark.parametrize("kind", sorted(REFUSED_OWN_INTELLIGENCE))
def test_an_own_skill_whose_intelligence_the_resolver_refuses_stops_the_launch(
    run, tmp_path, kind
):
    """tl_instruction Task 6: the resolver's exit 4 (no file for the provider) or 2 (a malformed
    one) stops the launch with the reader's own words behind the launcher's prefix, as the skill
    launcher's refusal does — before anything is tagged or handed a model."""
    refusal = place_refused_own_skill(tmp_path, "product-card", kind)
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    run.project("example-product")
    result = run("example-product", "--dry-run")

    assert result.returncode == 1, result.stdout
    assert result.stderr.endswith(f"product-card: {refusal}"), result.stderr
    assert "Telemetry:" not in result.stdout


# --- the launcher's launch, observed over the real helper (CP-685, CP-688, CP-759) -------------

_CARD_ARGV = ("example-product", "--dry-run")
# The pairs one product-card launch stamps, in the order its call hands them over: the arm and the
# run's own id, then the project and the product it looks up, then the provenance. A scratch tree
# that is no git checkout has no instance to add.
_OWN_INTELLIGENCE = "**Model:** claude-opus-5-5\n**Effort:** high\n"


def _card_product(project_dir):
    """The product a project's card names: the basename of the first path on its `**Product
    path:**` line — taken from the card the fixture wrote, never from what the launch printed."""
    line = next(
        line
        for line in (project_dir / "project.md").read_text().splitlines()
        if line.startswith("**Product path:**")
    )
    return os.path.basename(line.removeprefix("**Product path:**").split()[0])


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
@pytest.mark.parametrize("endpoint", ["valid", "absent"])
def test_product_card_helper_observation_matches_case_inputs(run, tmp_path, endpoint, cap):
    """CP-685, CP-688, CP-759: the launcher itself, run once over the real helper and the real
    package, prints the lines, exports the six variables and hands its run the settings its own
    inputs call for: the arm it runs under, the project it was given, the product that project's
    card names, and the provider, model, effort and source its own skill's intelligence names
    (claude-opus-5-5 at high)."""
    package = support.require_real_package(tmp_path / "package")
    place_own_skill(tmp_path, "product-card", _OWN_INTELLIGENCE)
    project_dir = run.project("example-product")
    endpoint_file = tmp_path / "published-endpoint"
    cause = support.publish_endpoint(endpoint_file, endpoint)
    launcher = support.scratch_core(tmp_path / "scratch", _SCRIPT)
    helper = launcher.parents[2] / "tools" / "run_telemetry.sh"
    env = support.telemetry_environment(
        run.env, home=package.home, endpoint_file=endpoint_file, cap=cap, command=package.command
    )

    observation = support.run_launcher(
        launcher, _CARD_ARGV, cwd=tmp_path, env=env, observation_dir=tmp_path / "observed"
    )

    if endpoint == "valid":
        support.assert_instrumented_observation(
            observation,
            pairs=[
                ("arm", "product-card"),
                ("run_id", None),
                ("project", "example-product"),
                ("product", _card_product(project_dir)),
                ("provider", "claude"),
                ("model", "claude-opus-5-5"),
                ("effort", "high"),
                ("source", "intelligence"),
            ],
            helper=helper,
            cap=cap,
        )
    else:
        assert observation.status == 0, observation.stderr
        assert Path(observation.helper_source).resolve() == helper.resolve()
        assert observation.telemetry_lines == [f"          ({cause} — run uninstrumented)"]
        support.assert_uninstrumented(observation, cap=cap)


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
def test_product_card_unresolved_skill_observation_matches_case_inputs(run, tmp_path, cap):
    """CP-685, CP-759: a skills root that holds no product-card is not a refusal — the provider
    default is stamped with no model and no effort, and every other observable is what the case's
    inputs call for."""
    package = support.require_real_package(tmp_path / "package")
    project_dir = run.project("example-product")
    endpoint_file = tmp_path / "published-endpoint"
    support.publish_endpoint(endpoint_file)
    launcher = support.scratch_core(tmp_path / "scratch", _SCRIPT)
    helper = launcher.parents[2] / "tools" / "run_telemetry.sh"
    env = support.telemetry_environment(
        run.env, home=package.home, endpoint_file=endpoint_file, cap=cap, command=package.command
    )

    observation = support.run_launcher(
        launcher, _CARD_ARGV, cwd=tmp_path, env=env, observation_dir=tmp_path / "observed"
    )

    support.assert_instrumented_observation(
        observation,
        pairs=[
            ("arm", "product-card"),
            ("run_id", None),
            ("project", "example-product"),
            ("product", _card_product(project_dir)),
            ("provider", "claude"),
            ("source", "default"),
        ],
        helper=helper,
        cap=cap,
    )


@pytest.mark.parametrize("combination", support.ORDINARY_COMBINATIONS)
def test_product_card_ordinary_launch_discovers_source_host_setting(run, tmp_path, combination):
    """CP-692: a launch whose environment names no command is instrumented from its source host's
    setting, whether the launcher runs from a core or a pin of it, for the host or for an
    instance that binds that core."""
    package = support.require_real_package(tmp_path / "package")
    place_own_skill(tmp_path, "product-card", _OWN_INTELLIGENCE)
    run.project("example-product")
    endpoint_file = tmp_path / "published-endpoint"
    support.publish_endpoint(endpoint_file)
    launch = support.ordinary_launch(tmp_path, _SCRIPT, tmp_path, combination, package.command)
    env = support.telemetry_environment(run.env, home=package.home, endpoint_file=endpoint_file)

    observation = support.run_launcher(
        launch.launcher, _CARD_ARGV, cwd=launch.instance, env=env,
        observation_dir=tmp_path / "observed",
    )

    support.assert_ordinary_launch_is_instrumented(observation, environment=env)


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
def test_product_card_missing_helper_preserves_launch(run, tmp_path, cap):
    """CP-687: a core whose tools hold no helper prints the one line naming the helper's path,
    exits as it would anyway, and hands its run no telemetry — there is no helper to carry even
    the cap, so the handoff is empty."""
    run.project("example-product")
    endpoint_file = tmp_path / "published-endpoint"
    support.publish_endpoint(endpoint_file)
    launcher = support.scratch_core(tmp_path / "scratch", _SCRIPT)
    helper = launcher.parents[2] / "tools" / "run_telemetry.sh"
    helper.unlink()
    env = support.telemetry_environment(
        run.env, home=tmp_path / "failure-home", endpoint_file=endpoint_file, cap=cap,
        command="neutral-command",
    )

    observation = support.run_launcher(
        launcher, _CARD_ARGV, cwd=tmp_path, env=env, observation_dir=tmp_path / "observed"
    )

    assert observation.status == 0, observation.stderr
    assert observation.telemetry_lines == [
        f"          (no instrument library at {helper} — run uninstrumented)"
    ]
    for name in support.TELEMETRY_EXPORT_NAMES:
        assert observation.exports.get(name) is None, f"{name} is exported"
    assert observation.exports.get(support.SETTINGS_NAME) in (None, ""), observation.exports
    assert observation.handed_settings is None, observation.handed_settings


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
@pytest.mark.parametrize("kind", support.FAILURE_KINDS)
def test_product_card_telemetry_failures_preserve_launch(run, tmp_path, kind, cap):
    """CP-687, CP-693, CP-694: whatever is wrong with the command or the endpoint, the launch is
    not failed by it — it prints the one cause on stdout and hands its run the cap alone."""
    run.project("example-product")
    scenario = support.failure_scenario(
        kind, run.env, home=tmp_path / "failure-home", endpoint_file=tmp_path / "endpoint", cap=cap
    )
    host = tmp_path / "host"
    host.mkdir()
    launcher = support.scratch_core(host, _SCRIPT)
    if scenario.host_setting is not None:
        support.write_host_setting(host, scenario.host_setting)

    observation = support.run_launcher(
        launcher, _CARD_ARGV, cwd=tmp_path, env=scenario.environment,
        observation_dir=tmp_path / "observed",
    )

    support.assert_failure_scenario(observation, scenario, cap=cap)


def test_product_card_observation_skips_an_unreachable_package_and_fails_a_reached_one(tmp_path):
    """CP-689: the observation above is skipped, with the reason named, where the package's
    command cannot be reached, and fails where it is reached and breaks the contract."""
    support.assert_selection_skips_unreachable_and_fails_reached(
        tmp_path, f"{__file__}::test_product_card_helper_observation_matches_case_inputs"
    )
