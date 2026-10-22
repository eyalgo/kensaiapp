"""Contract tests for `seeds-from-idea/launcher.sh`.

**The model is `companion-self-answer/launcher.sh`.**
This launcher takes exactly **one positional**: a path to the idea being cut — the seed's own
§ *Plan goal*, "with nothing the caller composes reaching the run's prompt". Unlike
`companion-self-answer` (`<project> <document>`) and `seeds-from-product-docs` (`<project>`), this launcher's
positional is a **path**, never a project name: the run's third input — a live session — has
nothing to pass, so only the two path-shaped inputs (a seed, a file) become an argument form
(plan § *Plan goal*).

**Project-card address resolution is derived from the path, not typed.** When the idea path sits
under `system/projects/<project>/…`, that segment names the project whose card is read for
`Product path:` — stripped through its trailing HTML comment, external-vs-internal `--add-dir`
exactly as every sibling resolves it (`companion-self-answer/launcher.sh` § THE MODEL). An idea at instance
level (`system/nemawashi/…`, or any path outside `system/projects/`) derives no project and gets
no `--add-dir` — there is nothing to grant beyond the instance repo the run's cwd already covers.
This is a judgment call the plan's § *Instance root and the launch address* names but does not
spell out mechanically; it is the only reading under which "a satellite and this instance behave
identically" and "the project card's `Product path:` is read" are both literally true for a
launcher whose sole argument is a path.

**The seat is fixed, not resolved.** Unlike `companion-self-answer`, which reads the seat off the
companion it will answer, this launcher always launches under `--agent principal-pm` — "the
posture the skill gates to" (plan § *The fixed prompt*), the same fixed seat `product-fdr` uses.

**It opens no worktree, and since 2026-09-05 neither does the run.** The owner's call that day has
a cut work in the instance it was started in (`<CORE>/prompts/principal_pm_cut_seeds_run.md` § *Where the
run works*), reversing the 2026-08-30 call under which the skill opened one. This launcher opened
none before and opens none now, so every assertion in this suite stands unchanged — what moved is
that no worktree is created downstream of it either.

Isolation: the real script at its real location, an independent `tmp_path` tree standing in for a
whole instance.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

import pytest

import launcher_telemetry_test_support as support
from provenance_test_support import (
    HOST_TOOLS,
    assert_provenance_stamped,
    isolated_host,
    REFUSED_OWN_INTELLIGENCE,
    place_own_skill,
    place_refused_own_skill,
)
from test_skill_launcher_telemetry import install_telemetry_command

# The isolated hosts the own-skill cases build hold the shared tools a launch reads; the telemetry
# helper is one of them now that the launcher calls it, and the explicit command each case names
# means the host needs no resolver.
_HOST_TOOLS = (*HOST_TOOLS, "run_telemetry.sh")

from kensaiapp_launchers_conftest import _granted_dirs, _plugin_skills

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_CORE_DIR = _SCRIPT.parent.parent.parent
# The delivered provider file: the tracked template at the instance root, copied into the instance
# a case runs for. No suite leans on a live `.providers.toml`, which is untracked.
_PROVIDER_EXAMPLE = _CORE_DIR.parent / ".providers.toml.example"

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
"""

WATCHER_STUB = """import sys
if "--list-ids" in sys.argv:
    print("pre1,pre2")
else:
    print("watcher-stub: stdout line")
    print("watcher-stub: stderr line", file=sys.stderr)
    with open(__import__("os").environ["WATCHER_ARGV_LOG"], "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
    # Held only for a case that asserts keep-awake PRESENCE. The watcher's exit is what releases
    # caffeinate, so a watcher that exits before the caffeinate stub has recorded makes that record
    # depend on a race. The hold ends on the record or at the case's teardown, never on a clock.
    import os, time
    hold_until = os.environ.get("WATCHER_STUB_HOLD_UNTIL")
    release = os.environ.get("WATCHER_STUB_RELEASE")
    while hold_until and not os.path.exists(release):
        if os.path.exists(hold_until) and open(hold_until).read().strip():
            break
        time.sleep(0.05)
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""

# The keep-awake bind is detached, so its caffeinate lands after the launcher returns. Under a
# loaded parallel run (`-n 32`, `core/pytest.ini`) the stub's first exec queues behind every other
# first exec on the machine — `warm_executables` (`core/launchers/conftest.py`) takes that out of
# the window — and a presence case also holds its watcher until the record exists. A presence
# check waits this long; an absence check passes `wait=2.5`, since it always waits its whole
# budget out.
_KEEPAWAKE_WAIT = 10.0

CAFFEINATE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$CAFFEINATE_ARGV_LOG"
"""


@pytest.fixture
def run(tmp_path, warm_executables):
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as its
    cwd — which is how the launcher resolves its instance root (`$PWD`). Helpers hang off the
    callable, mirroring `companion-self-answer`'s fixture, adapted for one path-shaped positional.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, content in (("claude", CLAUDE_STUB), ("caffeinate", CAFFEINATE_STUB)):
        warm_executables.link(bin_dir / name, content)

    watcher_stub = tmp_path / "watch_agent_stub.py"
    watcher_stub.write_text(WATCHER_STUB)

    notifier_stub = warm_executables.link(tmp_path / "notify_stub.sh", NOTIFIER_STUB)

    argv_log = tmp_path / "claude_argv.log"
    watcher_log = tmp_path / "watcher_argv.log"
    caffeinate_log = tmp_path / "caffeinate_argv.log"
    watcher_release = tmp_path / "watcher_release"

    home = tmp_path / "home"
    home.mkdir()
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_PROVIDER_EXAMPLE.read_text(encoding="utf-8"))

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # Points at a path nothing occupies, so this fixture never reads this machine's real
    # published telemetry endpoint (`a-launcher-tags-its-own-run`) — a launcher's own suite
    # is isolated from real machine state exactly like the watcher and the notifier above.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    # Explicitly unconfigured: absent would let the source host's own setting answer, and a case
    # that is not about the telemetry command must not depend on this machine's package.
    env[support.COMMAND_VARIABLE] = ""
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["WATCHER_ARGV_LOG"] = str(watcher_log)
    env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)
    env["WATCHER_STUB_RELEASE"] = str(watcher_release)
    env["LAUNCH_SEEDS_FROM_IDEA_WATCHER"] = str(watcher_stub)
    env["LAUNCH_SEEDS_FROM_IDEA_NOTIFIER"] = str(notifier_stub)
    env["HOME"] = str(home)

    def _run(*cli_args, script=_SCRIPT, cwd=None):
        return subprocess.run(
            [str(script), *cli_args],
            cwd=cwd or str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

    def _resolve_product_dir(product_path):
        if product_path.startswith("~/"):
            return home / product_path[2:]
        if product_path.startswith("/"):
            return Path(product_path)
        return tmp_path / product_path

    def _project(name, product_path="products/thing", card=None):
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True)
        if card is None:
            card = f"# {name}\n\n**Product path:** {product_path}\n"
        (project_dir / "project.md").write_text(card)
        product_dir = _resolve_product_dir(product_path)
        product_dir.mkdir(parents=True, exist_ok=True)
        return product_dir

    def _idea_in_project(project, name, content="# an idea\n\nsomething said in passing.\n"):
        """A seed-shaped idea file under a project's own nemawashi seedbed — the ordinary case
        an idea path derives a project from."""
        seedbed = tmp_path / "system" / "projects" / project / "journey" / "nemawashi"
        seedbed.mkdir(parents=True, exist_ok=True)
        path = seedbed / name
        path.write_text(content)
        return path

    def _instance_idea(name, content="# an idea\n\nsomething said in passing.\n"):
        """An idea at instance level — no project is derivable from this path."""
        seedbed = tmp_path / "system" / "nemawashi"
        seedbed.mkdir(parents=True, exist_ok=True)
        path = seedbed / name
        path.write_text(content)
        return path

    def _hold_watcher_until_kept_awake():
        env["WATCHER_STUB_HOLD_UNTIL"] = str(caffeinate_log)

    def _launched_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _watcher_argv():
        for _ in range(50):
            if watcher_log.exists():
                return watcher_log.read_text().splitlines()
            time.sleep(0.05)
        return []

    def _caffeinate_calls(wait=_KEEPAWAKE_WAIT):
        for _ in range(int(wait / 0.05)):
            if caffeinate_log.exists() and caffeinate_log.read_text():
                return len([l for l in caffeinate_log.read_text().splitlines() if l == "-i"])
            time.sleep(0.05)
        return 0

    _run.root = tmp_path
    _run.home = home
    _run.env = env
    _run.hold_watcher_until_kept_awake = _hold_watcher_until_kept_awake
    _run.project = _project
    _run.idea_in_project = _idea_in_project
    _run.instance_idea = _instance_idea
    _run.launched_argv = _launched_argv
    _run.watcher_argv = _watcher_argv
    _run.caffeinate_calls = _caffeinate_calls
    yield _run
    watcher_release.touch()


# --- Task 1 — the argument contract --------------------------------------------------------


def test_no_args_dies_naming_the_path_as_required(run):
    result = run()

    assert result.returncode != 0
    assert "is required" in result.stderr
    assert run.launched_argv() == []


def test_a_single_existing_path_is_accepted(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea))

    assert result.returncode == 0
    assert "does not look like a path" not in result.stderr
    assert "no file at" not in result.stderr


def test_more_than_one_positional_is_refused(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea), "system/nemawashi/another-file.md")

    assert result.returncode != 0
    assert run.launched_argv() == []


def test_trailing_prose_after_the_path_is_refused_rather_than_ignored(run):
    """A caller cannot append prose to what the run receives — anything after the one positional
    that is not a known flag is refused."""
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea), "and also summarise the previous round")

    assert result.returncode != 0
    assert run.launched_argv() == []


def test_a_path_that_does_not_exist_is_refused(run):
    result = run("system/nemawashi/nope.md")

    assert result.returncode != 0
    assert "no file at" in result.stderr
    assert run.launched_argv() == []


def test_a_bare_word_with_no_slash_and_no_leading_dot_is_refused(run):
    """Unlike the retired `ad-hoc-flow`, a bare slug has no meaning here — there is no per-slug folder
    convention for an idea, so a bare word is refused outright rather than resolved somehow."""
    result = run("someidea")

    assert result.returncode != 0
    assert "does not look like a path" in result.stderr
    assert run.launched_argv() == []


def test_a_bare_word_is_refused_even_when_a_same_named_file_exists_in_cwd(run):
    (run.root / "someidea").write_text("# not a real idea path form\n")

    result = run("someidea")

    assert result.returncode != 0
    assert "does not look like a path" in result.stderr


def test_every_refusal_happens_before_any_process_is_spawned(run):
    for args in (
        (),
        ("someidea",),
        ("system/nemawashi/nope.md",),
    ):
        result = run(*args)
        assert result.returncode != 0
        assert run.launched_argv() == []
        assert run.watcher_argv() == []


def test_unknown_flag_is_refused(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea), "--nonsense")

    assert result.returncode != 0
    assert run.launched_argv() == []


# --- Task 2 — instance root and the launch address -----------------------------------------


def test_instance_root_override_is_honoured(run, tmp_path_factory):
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run("--instance-root", str(run.root), str(idea), "--dry-run", cwd=str(elsewhere))

    assert result.returncode == 0
    assert str(idea) in result.stdout


def test_the_variable_is_no_force_and_the_command_is_unchanged(run):
    """seeds-from-idea reads no force: an exported provider neither changes the command nor
    refuses."""
    idea = run.instance_idea("2026-08-30_an-idea.md")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^  claude  --bg  ", result.stdout, re.MULTILINE), result.stdout[:400]


def test_an_idea_under_a_project_derives_that_projects_product_path(run):
    run.project("example-product", product_path="products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert "Project:   example-product" in result.stdout
    assert str(run.root / "products" / "thing") in result.stdout


def test_the_product_path_is_read_through_the_trailing_html_comment_every_card_carries(run):
    project_dir = run.root / "system" / "projects" / "example-product"
    project_dir.mkdir(parents=True)
    (project_dir / "project.md").write_text(
        "# example-product\n\n**Product path:** products/thing   <!-- set at scaffold -->\n"
    )
    (run.root / "products" / "thing").mkdir(parents=True)
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert "<!--" not in result.stdout


def test_relative_product_path_gets_no_add_dir(run):
    # The one --add-dir any dry run now carries is the pin's own (Task 15's adapter delivery) —
    # never a second one for an internal product path, which the cwd already covers.
    run.project("example-product", product_path="products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.stdout.count("--add-dir") == 1


def test_absolute_product_path_resolves_externally_and_gets_add_dir(run, tmp_path_factory):
    external = tmp_path_factory.mktemp("external_product")
    run.project("example-product", product_path=str(external))
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert "--add-dir" in result.stdout
    assert str(external) in result.stdout


def test_tilde_product_path_expands_to_home_and_gets_add_dir(run):
    run.project("example-product", product_path="~/products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert "--add-dir" in result.stdout
    assert str(run.home / "products" / "thing") in result.stdout


def test_an_instance_level_idea_derives_no_project_and_gets_no_add_dir(run):
    # The one --add-dir a dry run now carries is the pin's own (Task 15) — never one for a
    # product, since an instance-level idea derives no project at all.
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert result.stdout.count("--add-dir") == 1
    assert "Project:" not in result.stdout


def test_an_idea_whose_derived_project_has_no_card_is_not_refused(run):
    """Cutting an idea does not require the idea to already belong to an existing project's
    product — a derived project name with no project.md is read best-effort, not a refusal. The
    one --add-dir a dry run now carries is the pin's own (Task 15)."""
    seedbed = run.root / "system" / "projects" / "nope" / "journey" / "nemawashi"
    seedbed.mkdir(parents=True)
    idea = seedbed / "2026-08-30_an-idea.md"
    idea.write_text("# an idea\n")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert result.stdout.count("--add-dir") == 1


def test_dry_run_prints_the_pin_line(run):
    # Task 15: pin_enter runs right after the CORE_DIR guard, ahead of everything else.
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_the_command_carries_the_pin_delivery_and_the_launchers_own_flags(run, tmp_path_factory):
    # Task 15: the Claude argv comes from the adapter's --print-argv, carrying the pin delivery
    # alongside the launcher's own --agent and the product's own --add-dir.
    external = tmp_path_factory.mktemp("external_product")
    run.project("example-product", product_path=str(external))
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert str(external) in _granted_dirs(argv)
    assert argv[argv.index("--setting-sources") + 1] == "user"
    assert "--plugin-dir" in argv


def test_the_claude_launch_grants_seeds_from_idea(run):
    run.project("example-product")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0, result.stderr
    listed, groups = _plugin_skills(_dry_run_argv(result.stdout))
    assert "seeds-from-idea" in listed
    assert groups == {"interactive"}


def test_dry_run_prints_the_resolved_address_and_spawns_nothing(run):
    run.project("example-product", product_path="products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert run.launched_argv() == []
    assert run.watcher_argv() == []


def test_every_guard_still_fires_under_dry_run(run):
    result = run("someidea", "--dry-run")

    assert result.returncode != 0
    assert "does not look like a path" in result.stderr


# --- Task 2b — one path shape, one tree: an idea is cut from inside the repository ----------
#
# The owner's ruling of 2026-08-30 removes the case rather than documenting it: there is one
# resolution, not three arms (`~/`, absolute, relative) that each accepted a different shape and
# succeeded regardless of where the path actually pointed. Whatever the caller typed is resolved
# to an absolute address and MUST land inside the instance root, or the run refuses — naming why
# and what to do, not just that it failed.


def test_an_absolute_path_outside_the_instance_root_is_refused(run, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside_the_repo")
    idea = outside / "2026-08-30_an-idea.md"
    idea.write_text("# an idea\n")

    result = run(str(idea))

    assert result.returncode != 0
    assert "outside the instance root" in result.stderr
    assert "inside the repo" in result.stderr
    assert run.launched_argv() == []


def test_a_relative_path_that_escapes_the_instance_root_is_refused(run, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside_the_repo")
    idea = outside / "2026-08-30_an-idea.md"
    idea.write_text("# an idea\n")
    escaping = os.path.relpath(str(idea), start=str(run.root))
    assert escaping.startswith("..")  # the shape under test — a relative path that climbs out

    result = run(escaping)

    assert result.returncode != 0
    assert "outside the instance root" in result.stderr
    assert run.launched_argv() == []


def test_a_tilde_path_outside_the_instance_root_is_refused(run, tmp_path_factory):
    """The fixture's own `home` sits under the instance root (`run.root`), so a `~/` path there
    would already be in-repo — HOME is overridden here to a location genuinely outside it."""
    outside_home = tmp_path_factory.mktemp("outside_home")
    idea = outside_home / "2026-08-30_outside-idea.md"
    idea.write_text("# an idea\n")
    run.env["HOME"] = str(outside_home)

    result = run("~/2026-08-30_outside-idea.md")

    assert result.returncode != 0
    assert "outside the instance root" in result.stderr
    assert run.launched_argv() == []


def test_an_outside_path_is_refused_for_being_outside_even_when_it_does_not_exist(
    run, tmp_path_factory
):
    """The containment refusal fires before the existence check — being outside the repo is the
    reason, not a coincidental 'no file at'."""
    outside = tmp_path_factory.mktemp("outside_the_repo")
    missing = outside / "does-not-exist.md"

    result = run(str(missing))

    assert result.returncode != 0
    assert "outside the instance root" in result.stderr
    assert "no file at" not in result.stderr


def test_the_refusal_says_what_to_do_about_it(run, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside_the_repo")
    idea = outside / "2026-08-30_an-idea.md"
    idea.write_text("# an idea\n")

    result = run(str(idea))

    assert result.returncode != 0
    assert "bring it in" in result.stderr.lower()


def test_dry_run_shows_no_absolute_idea_path_in_the_prompt_string(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")
    rel = idea.relative_to(run.root)

    result = run(str(idea), "--dry-run")

    assert result.returncode == 0
    line = next(l for l in result.stdout.splitlines() if l.strip().startswith("claude"))
    assert str(run.root) not in line
    argv = _dry_run_argv(result.stdout)
    assert argv[2] == f"invoke the seeds-from-idea skill for the idea at {rel}."


# --- Task 3 — the fixed prompt --------------------------------------------------------------


def test_the_launched_prompt_names_the_skill_and_the_resolved_idea_path(run):
    """Fence: proven on a REAL launch, never paired only with --dry-run — a --dry-run test proves
    nothing about caller prose reaching the run. The path cited is repo-relative — an idea is cut
    from inside the repository, and the run resolves it again against the instance it was started
    in (§ Task 4)."""
    idea = run.instance_idea("2026-08-30_an-idea.md")
    rel = idea.relative_to(run.root)

    result = run(str(idea))

    assert result.returncode == 0
    argv = run.launched_argv()
    assert argv[1] == f"invoke the seeds-from-idea skill for the idea at {rel}."


def test_caller_cannot_append_to_the_prompt(run):
    """The positional is structured (one path), never free text — there is no channel for a
    caller to compose prose into what the run receives, because anything past the path was
    already refused at task 1."""
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea), "and also summarise the previous round")

    assert result.returncode != 0
    assert run.launched_argv() == []


def test_the_run_is_launched_under_the_principal_pm_seat(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    argv = run.launched_argv()
    assert "--agent" in argv and argv[argv.index("--agent") + 1] == "principal-pm"


def test_the_run_is_launched_in_auto_permission_mode(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    argv = run.launched_argv()
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_allowed_tools_bare_and_print_are_never_passed(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    argv = run.launched_argv()
    assert "--allowedTools" not in argv
    assert "--bare" not in argv
    assert "--print" not in argv and "-p" not in argv


def test_a_project_derived_add_dir_reaches_the_real_launch(run, tmp_path_factory):
    external = tmp_path_factory.mktemp("external_product")
    run.project("example-product", product_path=str(external))
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    run(str(idea))

    argv = run.launched_argv()
    assert str(external) in _granted_dirs(argv)


def test_an_internal_relative_product_path_launches_with_no_add_dir(run):
    # The one --add-dir a real launch now carries is the pin's own (Task 15) — never a second one
    # for an internal product path, which the cwd already covers.
    run.project("example-product", product_path="products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    run(str(idea))

    assert len(_granted_dirs(run.launched_argv())) == 1


def test_an_instance_level_idea_launches_with_no_add_dir(run):
    # The one --add-dir a real launch now carries is the pin's own (Task 15).
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    assert len(_granted_dirs(run.launched_argv())) == 1


def _dry_run_argv(stdout):
    line = next(l for l in stdout.splitlines() if l.strip().startswith("claude"))
    return shlex.split(line.strip())


def test_dry_run_prints_the_exact_command_the_real_launch_runs(run):
    run.project("example-product", product_path="products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")

    dry = run(str(idea), "--dry-run")
    run(str(idea))

    assert dry.returncode == 0
    printed = _dry_run_argv(dry.stdout)
    actual = ["claude", *run.launched_argv()]
    assert printed == actual


# --- Task 4 — it does not open a worktree ----------------------------------------------------


def test_the_launcher_creates_no_worktree_and_no_branch():
    """No cut opens a worktree (principal_pm_cut_seeds_run.md § Where the run works, 2026-09-05) — and this
    launcher never did, creating no worktree and no branch of its own.
    Proved here on the source text; the sibling test below proves the same claim by effect."""
    text = _SCRIPT.read_text()
    code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))

    assert "worktree add" not in code
    assert "git branch" not in code
    assert re.search(r"git\s+worktree\b", code) is None


def test_no_worktree_directory_is_created_on_a_real_launch(run):
    """The same claim, proved by effect rather than only by source text: a real launch over a
    fixture instance leaves no `.worktrees/` behind."""
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    assert not (run.root / ".worktrees").exists()


# --- Task 5 — keep-awake and the completion watch ---------------------------------------------


def _registered_reporter_names():
    registry = Path(__file__).resolve().parents[2] / "tools" / "reporters.py"
    tree = ast.parse(registry.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "REGISTRY" for t in node.targets
        ):
            return {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    raise AssertionError(f"no REGISTRY mapping found in {registry}")


def test_the_reporter_the_launcher_passes_is_actually_registered(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    argv = run.watcher_argv()
    assert argv != []
    name = argv[argv.index("--reporter") + 1]
    assert name in _registered_reporter_names(), (
        f"--reporter {name} is not in reporters.py's REGISTRY — it would silently behave as generic"
    )


def test_watcher_excludes_agents_that_existed_before_the_launch(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    argv = run.watcher_argv()
    assert argv[argv.index("--exclude-ids") + 1] == "pre1,pre2"


def test_watcher_is_not_spawned_when_no_notifier_is_installed(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")
    run.env["LAUNCH_SEEDS_FROM_IDEA_NOTIFIER"] = str(run.root / "nope" / "missing.sh")

    result = run(str(idea))

    assert result.returncode == 0
    assert run.launched_argv() != []
    assert run.watcher_argv() == []


def test_a_missing_detach_watcher_is_reported_distinctly_and_does_not_block_the_launch(
    run, tmp_path_factory
):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    # `isolated/core` stands in for CORE_DIR, with `isolated/pin.json` marking `isolated` as its
    # own pin — so pin_enter (rule 1) finds itself already a pin and neither re-execs nor copies
    # anything: what this test builds is exactly what runs. `tools/` holds only the machinery
    # pin_enter and the adapter build unconditionally reach (Task 15) — never detach_watcher.sh,
    # which is what this test is about.
    isolated = tmp_path_factory.mktemp("no_detach_lib")
    core_root = isolated / "core"
    launcher_dir = core_root / "launchers" / "seeds-from-idea"
    launcher_dir.mkdir(parents=True)
    copied_script = launcher_dir / "launcher.sh"
    copied_script.write_text(_SCRIPT.read_text())
    copied_script.chmod(0o755)
    tools_dir = core_root / "tools"
    tools_dir.mkdir()
    for tool in ("pin.py", "pin_run.sh", "agent_run.py", "model_assignment.py", "task_context.py",
                 "hook_wiring.py",
                 "env_file.py", "run_intelligence.py", "intelligence.py", "providers.py"):
        shutil.copy(_CORE_DIR / "tools" / tool, tools_dir / tool)
    (isolated / "pin.json").write_text(
        json.dumps({"id": "isolated", "source_host_root": str(isolated), "created": "1970-01-01T00:00:00+00:00"})
        + "\n"
    )

    result = run(str(idea), script=copied_script)

    assert result.returncode == 0
    assert run.launched_argv() != []          # the primary launch still happened
    assert run.watcher_argv() == []
    assert "no completion-watch library at" in result.stdout


def test_the_detach_block_is_not_hand_copied():
    text = _SCRIPT.read_text()

    assert "detach_watcher.sh" in text
    assert "source" in text
    assert "nohup python3" not in text and 'nohup "python3"' not in text


def test_detach_completion_watcher_is_actually_called():
    text = _SCRIPT.read_text()
    code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))

    assert "detach_completion_watcher" in code


def test_watcher_is_found_at_its_resolved_home_when_the_env_override_is_unset(run):
    """`core/doctrine/setup/kensaiapp_structure.md` § Owner-run launcher folder requires this of
    each launcher's suite, and this file was the one real gap: three of 22 folders lacked it, and the
    other two spawn no model and source no completion-watch home. A wrong CORE_DIR-derived
    default fails silently — the watcher goes unspawned while the launch still succeeds — so nothing else in
    this file can see it, because every other test overrides the env var with a stub. Asserted
    through the outcome, not against a literal path."""
    idea = run.instance_idea("2026-08-30_an-idea.md")
    run.env.pop("LAUNCH_SEEDS_FROM_IDEA_WATCHER", None)   # exercise the real default

    result = run(str(idea))

    assert result.returncode == 0, result.stderr
    assert "completion watch skipped" not in result.stdout
    assert "Watcher log:" in result.stdout
    assert list((run.root / "system" / "logs").glob("watch-seeds-from-idea-*.log"))


def test_keep_awake_reaches_the_shared_home(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run.hold_watcher_until_kept_awake()
    run(str(idea), "--keep-awake")

    assert run.caffeinate_calls() >= 1


def test_no_keep_awake_flag_means_zero_caffeinate_invocations(run):
    idea = run.instance_idea("2026-08-30_an-idea.md")

    run(str(idea))

    assert run.caffeinate_calls(wait=2.5) == 0


def test_a_launch_line_with_no_agent_id_falls_back_to_name(run):
    """The `claude` stub here prints raw argv, never a `backgrounded · <id>` line, so
    `capture_agent_id` (inside the shared home) finds nothing — the watcher call must still
    succeed on `--name` rather than failing."""
    idea = run.instance_idea("2026-08-30_an-idea.md")

    result = run(str(idea))

    assert result.returncode == 0
    argv = run.watcher_argv()
    assert argv != []
    assert "--agent-id" not in argv
    assert "--name" in argv


# --- Task 6 — the manifest names it -----------------------------------------------------------

_STRUCTURE_MAP = (
    Path(__file__).resolve().parents[2] / "doctrine" / "setup" / "kensaiapp_structure.md"
)


def _owner_run_launcher_folder_section():
    text = _STRUCTURE_MAP.read_text()
    start = text.index("### Owner-run launcher folder")
    end = text.index("\n### ", start + 1)
    return text[start:end]


def test_the_manifest_names_the_new_launcher_within_its_section():
    section = _owner_run_launcher_folder_section()

    assert section.count("seeds-from-idea") >= 1


# --- executable ------------------------------------------------------------------------------


def test_launcher_is_executable():
    assert os.access(_SCRIPT, os.X_OK), f"{_SCRIPT} is not executable"


def test_dry_run_states_the_arm_it_would_run_under(run, tmp_path):
    """`a-launcher-tags-its-own-run` — a dry run that hides the instrument is a dry run that
    lies. With a runnable telemetry command and a published endpoint file present,
    `run_telemetry` prints the arm it derived (this launcher's own directory name) even though
    nothing is actually spawned."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    install_telemetry_command(tmp_path / "home", run.env)
    run.project("example-product", product_path="products/thing")
    idea = run.idea_in_project("example-product", "2026-08-30_an-idea.md")
    result = run(str(idea), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.arm=seeds-from-idea" in result.stdout
    assert "--settings" in result.stdout, "a dry run that hides the settings hides what a backgrounded run needs"


# --- the run's provenance (CP-218, CP-221, CP-227, CP-229, CP-230) -----------------------------


def test_the_run_telemetry_call_carries_the_four_provenance_keys():
    support.assert_run_telemetry_call_carries_provenance(_SCRIPT)


def _an_idea(run):
    run.project("example-product", product_path="products/thing")
    return run.idea_in_project("example-product", "2026-08-30_an-idea.md")


def _with_endpoint(run, tmp_path):
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    install_telemetry_command(tmp_path / "home", run.env)


def test_stamp_is_provider_claude_source_default_with_no_model_or_effort_and_the_argv_carries_neither(  # noqa: E501 — the instruction's own case name
    run, tmp_path
):
    """The launcher's own skill has no intelligence/ folder on this tree, so the run is handed no
    model and no effort and the stamp says `default`, after the pairs it stamped before."""
    _with_endpoint(run, tmp_path)
    idea = _an_idea(run)
    result = run(str(idea), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert_provenance_stamped(result.stdout, provider="claude", source="default", after=())
    assert "--model" not in result.stdout and "--effort" not in result.stdout


def test_an_own_skill_with_an_intelligence_file_is_handed_and_stamped_the_same_pair(
    run, tmp_path, tmp_path_factory
):
    """One resolution feeds the argv and the stamp: the own skill's intelligence file, placed where
    the launcher's host root resolves it, is what the run goes at and what it is stamped with."""
    host = tmp_path_factory.mktemp("own_skill_host")
    script = isolated_host(host, _SCRIPT, tools=_HOST_TOOLS)
    place_own_skill(host, "seeds-from-idea", "**Model:** claude-opus-5-5\n**Effort:** high\n")
    _with_endpoint(run, tmp_path)
    idea = _an_idea(run)
    result = run(str(idea), "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert_provenance_stamped(
        result.stdout,
        provider="claude",
        model="claude-opus-5-5",
        effort="high",
        source="intelligence",
    )
    assert re.search(r"--model\s+claude-opus-5-5\s", result.stdout), result.stdout
    assert re.search(r"--effort\s+high\s", result.stdout), result.stdout


def test_an_unresolvable_own_skill_is_default_and_the_launch_proceeds(
    run, tmp_path, tmp_path_factory
):
    """A host that holds no such skill is not a refusal: the run goes at the provider default."""
    host = tmp_path_factory.mktemp("no_own_skill_host")
    script = isolated_host(host, _SCRIPT, tools=_HOST_TOOLS)
    _with_endpoint(run, tmp_path)
    idea = _an_idea(run)
    result = run(str(idea), "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert_provenance_stamped(result.stdout, provider="claude", source="default")
    assert "--model" not in result.stdout and "--effort" not in result.stdout


@pytest.mark.parametrize("kind", sorted(REFUSED_OWN_INTELLIGENCE))
def test_an_own_skill_whose_intelligence_the_resolver_refuses_stops_the_launch(
    run, tmp_path, tmp_path_factory, kind
):
    """tl_instruction Task 6: the resolver's exit 4 (no file for the provider) or 2 (a malformed
    one) stops the launch with the reader's own words behind the launcher's prefix, as the skill
    launcher's refusal does — before anything is tagged or handed a model."""
    host = tmp_path_factory.mktemp("refused_own_skill_host")
    script = isolated_host(host, _SCRIPT, tools=_HOST_TOOLS)
    refusal = place_refused_own_skill(host, "seeds-from-idea", kind)
    _with_endpoint(run, tmp_path)
    idea = _an_idea(run)
    result = run(str(idea), "--dry-run", script=script)

    assert result.returncode == 1, result.stdout
    assert result.stderr.endswith(f"seeds-from-idea: {refusal}"), result.stderr
    assert "Telemetry:" not in result.stdout


# --- the launcher's launch, observed over the real helper (CP-685, CP-688, CP-759) -------------

_OWN_INTELLIGENCE = "**Model:** claude-opus-5-5\n**Effort:** high\n"
# The pairs one seeds-from-idea launch stamps, in the order its call hands them over: the arm and
# the run's own id, then the provenance. The launcher hands no subject — no skill, project or
# document — and a scratch tree that is no git checkout has no instance to add, so the whole list
# below is the launch's attributes and a subject key anywhere would fail the comparison.
_ARM_PAIRS = [("arm", "seeds-from-idea"), ("run_id", None)]
_OWN_INTELLIGENCE_PAIRS = [
    *_ARM_PAIRS,
    ("provider", "claude"),
    ("model", "claude-opus-5-5"),
    ("effort", "high"),
    ("source", "intelligence"),
]
_DEFAULT_PAIRS = [*_ARM_PAIRS, ("provider", "claude"), ("source", "default")]


def _seeds_argv(idea):
    return (str(idea), "--dry-run")


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
@pytest.mark.parametrize("endpoint", ["valid", "absent"])
@pytest.mark.parametrize("resolution", ["own-intelligence", "default"])
def test_seeds_from_idea_helper_observation_matches_case_inputs(
    run, tmp_path, resolution, endpoint, cap
):
    """CP-685, CP-688, CP-759: the launcher itself, run once over the real helper and the real
    package, prints the lines, exports the six variables and hands its run the settings its own
    inputs call for: the arm it runs under and the provenance it resolved, with no subject. Its
    own skill's intelligence names claude-opus-5-5 at high, or it has none and the default
    stands."""
    package = support.require_real_package(tmp_path / "package")
    idea = _an_idea(run)
    endpoint_file = tmp_path / "published-endpoint"
    cause = support.publish_endpoint(endpoint_file, endpoint)
    launcher = support.scratch_core(tmp_path / "scratch", _SCRIPT)
    helper = launcher.parents[2] / "tools" / "run_telemetry.sh"
    if resolution == "own-intelligence":
        place_own_skill(tmp_path / "scratch", "seeds-from-idea", _OWN_INTELLIGENCE)
    env = support.telemetry_environment(
        run.env, home=package.home, endpoint_file=endpoint_file, cap=cap, command=package.command
    )

    observation = support.run_launcher(
        launcher, _seeds_argv(idea), cwd=tmp_path, env=env, observation_dir=tmp_path / "observed"
    )

    if endpoint == "valid":
        pairs = _OWN_INTELLIGENCE_PAIRS if resolution == "own-intelligence" else _DEFAULT_PAIRS
        support.assert_instrumented_observation(observation, pairs=pairs, helper=helper, cap=cap)
    else:
        assert observation.status == 0, observation.stderr
        assert Path(observation.helper_source).resolve() == helper.resolve()
        assert observation.telemetry_lines == [f"          ({cause} — run uninstrumented)"]
        support.assert_uninstrumented(observation, cap=cap)


@pytest.mark.parametrize("combination", support.ORDINARY_COMBINATIONS)
def test_seeds_ordinary_launch_discovers_source_host_setting(run, tmp_path, combination):
    """CP-692: a launch whose environment names no command is instrumented from its source host's
    setting, whether the launcher runs from a core or a pin of it, for the host or for an
    instance that binds that core."""
    package = support.require_real_package(tmp_path / "package")
    idea = _an_idea(run)
    endpoint_file = tmp_path / "published-endpoint"
    support.publish_endpoint(endpoint_file)
    launch = support.ordinary_launch(tmp_path, _SCRIPT, tmp_path, combination, package.command)
    env = support.telemetry_environment(run.env, home=package.home, endpoint_file=endpoint_file)

    observation = support.run_launcher(
        launch.launcher, _seeds_argv(idea), cwd=launch.instance, env=env,
        observation_dir=tmp_path / "observed",
    )

    support.assert_ordinary_launch_is_instrumented(observation, environment=env)


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
@pytest.mark.parametrize("kind", support.FAILURE_KINDS)
def test_seeds_telemetry_failures_preserve_launch(run, tmp_path, kind, cap):
    """CP-687, CP-693, CP-694: whatever is wrong with the command or the endpoint, the launch is
    not failed by it — it prints the one cause on stdout and hands its run the cap alone."""
    idea = _an_idea(run)
    scenario = support.failure_scenario(
        kind, run.env, home=tmp_path / "failure-home", endpoint_file=tmp_path / "endpoint", cap=cap
    )
    host = tmp_path / "host"
    host.mkdir()
    launcher = support.scratch_core(host, _SCRIPT)
    if scenario.host_setting is not None:
        support.write_host_setting(host, scenario.host_setting)

    observation = support.run_launcher(
        launcher, _seeds_argv(idea), cwd=tmp_path, env=scenario.environment,
        observation_dir=tmp_path / "observed",
    )

    support.assert_failure_scenario(observation, scenario, cap=cap)


def test_seeds_observation_skips_an_unreachable_package_and_fails_a_reached_one(tmp_path):
    """CP-689: the observation above is skipped, with the reason named, where the package's
    command cannot be reached, and fails where it is reached and breaks the contract."""
    support.assert_selection_skips_unreachable_and_fails_reached(
        tmp_path, f"{__file__}::test_seeds_from_idea_helper_observation_matches_case_inputs"
    )
