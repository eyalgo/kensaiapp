"""Contract tests for `companion-self-answer/launcher.sh` (rebuilt v2).

**v1 is deleted (`b68d56de`) and is not the model.** It addressed a bare `<target>` — a
`REFERENCE_ROOT/../<target>` guess that could not reach a satellite living elsewhere, could not
take `<satellite>/<project>` addressing, and could not be told which companion to answer at all
(its prompt was fixed at "scoped to the target"). This suite proves none of that comes back.

**The model was the product document launchers', `product-fdr`'s first.** This launcher takes `<project> <document>`, resolves
the project card exactly as every `product-*` sibling does (`Product path:`, stripped through its
trailing HTML comment, external-vs-internal `--add-dir`), and resolves `<document>` against the
`docs/` **directory entry** — matched case-insensitively, used at the case the FILE carries, and
the companion taken beside it. Never a path, never an instance, never a `case` arm naming a
document. The case is read rather than composed because six of the seven documents are upper-case
on disk and the FDR alone is lower, so no casing rule fits all seven and any that tried would
need the list this launcher may not hold.

**The one designed part, kept from v1 because it was never the defect: seat resolution.** The
seat is read at launch time from the companion the run will answer — never mapped from a table —
in this order: read the companion's `re-run \\`<skill>\\`` line, read that skill's own launcher's
`--agent` value (bare-identity folder first, then the fixed prompt-literal grep). Two fallbacks,
neither a halt: no seat derivable, or a seat whose agent file is not on disk — both launch a
seatless session. The run's model is the producing skill's own (`intelligence/<provider>.md`),
never a fallback of this launcher's.

Two env overrides beyond the usual watcher/notifier pair, kept from v1 for the same reason:
`LAUNCH_COMPANION_SELF_ANSWER_LAUNCHERS_DIR` / `_AGENT_GROUPS_DIR` stand in for `<CORE>/launchers/`
and the groups directory `skills/`, so seat resolution is proven on a fixture tree, never on
whatever this repo happens to hold that day.

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

from provenance_test_support import (
    assert_instrument_run_call_carries_provenance,
    assert_provenance_stamped,
    telemetry_pairs,
)

from kensaiapp_launchers_conftest import (
    _PRINT_RUN_HEAD,
    assert_launch_recorded_its_identity,
    _granted_dirs,
    _plugin_skills,
    _prompt_of,
    _provider_argv,
    _without_session_id,
)

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
_CORE_DIR = _SCRIPT.parent.parent.parent
_REPO = _CORE_DIR.parent

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
printf '%s\\n' '{"type":"result","subtype":"success","is_error":false,"result":"ok"}'
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


# The run is a detached process: its stub records after the launcher returns, and under the
# suite's parallel load its first exec can queue behind other workers — the same ten-second budget
# the Codex cases use. A launch that was refused, or only dry-run, spawned nothing and never will,
# so its absence is read after a short settle rather than the whole budget.
_DETACHED_WAIT = 10.0
_ABSENT_WAIT = 0.5


@pytest.fixture
def run(tmp_path, warm_executables):
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as its
    cwd — which is how the launcher resolves its instance root (`$PWD`). Helpers hang off the
    callable, mirroring `product-fdr`'s fixture plus `companion-self-answer` v1's seat-resolution
    helpers (`skill_launcher` / `agent_file`), adapted for `<project> <document>` addressing.
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

    launchers_dir = tmp_path / "fixture_launchers"
    launchers_dir.mkdir()
    groups_dir = tmp_path / "fixture_groups"
    groups_dir.mkdir()
    loaders_dir = tmp_path / "fixture_loaders"
    loaders_dir.mkdir()

    home = tmp_path / "home"
    home.mkdir()
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_DELIVERED_PROVIDERS)

    env = dict(os.environ)
    env.pop("KENSAIAPP_AGENT_PROVIDER", None)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # Points at a path nothing occupies, so this fixture never reads this machine's real
    # published telemetry endpoint (`a-launcher-tags-its-own-run`) — a launcher's own suite
    # is isolated from real machine state exactly like the watcher and the notifier above.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["WATCHER_ARGV_LOG"] = str(watcher_log)
    env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)
    env["WATCHER_STUB_RELEASE"] = str(watcher_release)
    env["LAUNCH_COMPANION_SELF_ANSWER_WATCHER"] = str(watcher_stub)
    env["LAUNCH_COMPANION_SELF_ANSWER_NOTIFIER"] = str(notifier_stub)
    env["LAUNCH_COMPANION_SELF_ANSWER_LAUNCHERS_DIR"] = str(launchers_dir)
    env["LAUNCH_COMPANION_SELF_ANSWER_AGENT_GROUPS_DIR"] = str(groups_dir)
    env["LAUNCH_COMPANION_SELF_ANSWER_LOADERS_DIR"] = str(loaders_dir)
    env["LAUNCH_COMPANION_SELF_ANSWER_SKILLS_ROOT"] = str(tmp_path)
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
        (product_dir / "docs").mkdir(parents=True, exist_ok=True)
        return product_dir

    def _document(product_dir, doc, content=None):
        docs = Path(product_dir) / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        path = docs / f"{doc}.md"
        path.write_text(content or f"# {doc.upper()}\n\nSettled document.\n")
        return path

    def _companion(product_dir, doc, skill=None, extra_header=""):
        docs = Path(product_dir) / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        header = f"> Companion to `{doc}.md`.\n"
        if skill:
            header += f"> Answer inline, commit, then re-run `{skill}`.\n"
        header += extra_header
        path = docs / f"{doc}_open_issues.md"
        path.write_text(
            f"# {doc} open issues\n\n{header}\n---\n\n## 1. Open issues\n\n"
            "### 1.1 A question\n- **Answer:** <the owner fills this in>\n"
        )
        return path

    def _skill_launcher(skill, agent=None, folder=None, prompt_skill=None):
        """A fixture sibling launcher under `LAUNCHERS_DIR` — the model
        `set -- claude --bg "$prompt" --agent <agent> --permission-mode auto` line, or a bare
        seatless line when `agent` is None (a skill that names no seat)."""
        d = launchers_dir / (folder or skill)
        d.mkdir(parents=True, exist_ok=True)
        body = f'#!/usr/bin/env bash\nprompt="invoke the {prompt_skill or skill} skill for the thing."\n'
        if agent:
            body += f'set -- claude --bg "$prompt" --agent {agent} --permission-mode auto\n'
        else:
            body += 'set -- claude --bg "$prompt" --model opus --permission-mode auto\n'
        (d / "launcher.sh").write_text(body)
        return d / "launcher.sh"

    def _agent_path(seat):
        """Where a seat's agent file lives in the fixture: its own group, as in the real tree."""
        return groups_dir / seat / ".claude" / "agents" / f"{seat}.md"

    def _write_agent(seat, text):
        _agent_path(seat).parent.mkdir(parents=True, exist_ok=True)
        _agent_path(seat).write_text(text)

    def _agent_file(seat, loader=True):
        """An agent file, and by default the loader that makes the agent a SEAT.

        `loader=False` builds the other kind on purpose — a posture-free agent carrying only a
        tool grant (`delegate`). The launcher must not answer a companion
        under one of those, and the loader is the only thing on disk that tells them apart.
        """
        _write_agent(seat, f"# {seat}\n")
        if loader:
            (loaders_dir / f"{seat.replace('-', '_')}_global.md").write_text(f"# {seat} loader\n")

    def _hold_watcher_until_kept_awake():
        env["WATCHER_STUB_HOLD_UNTIL"] = str(caffeinate_log)

    def _launched_argv(wait=_DETACHED_WAIT):
        # The run is a detached process, so what its stub recorded lands after the launcher returns.
        for _ in range(int(wait / 0.05)):
            if argv_log.exists() and argv_log.read_text():
                return argv_log.read_text().splitlines()
            time.sleep(0.05)
        return []

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

    def _no_notifier():
        env["LAUNCH_COMPANION_SELF_ANSWER_NOTIFIER"] = str(tmp_path / "nope" / "missing.sh")

    def _default_watcher():
        env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER", None)

    _run.root = tmp_path
    _run.home = home
    _run.launchers_dir = launchers_dir
    _run.groups_dir = groups_dir
    _run.agent_path = _agent_path
    _run.write_agent = _write_agent
    _run.loaders_dir = loaders_dir
    _run.env = env
    _run.hold_watcher_until_kept_awake = _hold_watcher_until_kept_awake
    _run.project = _project
    _run.document = _document
    _run.companion = _companion
    _run.skill_launcher = _skill_launcher
    _run.agent_file = _agent_file
    _run.launched_argv = _launched_argv
    _run.watcher_argv = _watcher_argv
    _run.caffeinate_calls = _caffeinate_calls
    _run.no_notifier = _no_notifier
    _run.default_watcher = _default_watcher
    yield _run
    watcher_release.touch()


# --- Task 1 — <project> <document> resolves to the document and its companion ------------


def test_no_args_dies_naming_the_project_as_required(run):
    result = run()

    assert result.returncode != 0
    assert "<project> is required" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_project_with_no_document_dies_naming_the_document_as_required(run):
    run.project("example-product")

    result = run("example-product")

    assert result.returncode != 0
    assert "<document> is required" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_unknown_flag_dies_before_launching(run):
    run.project("example-product")
    run.document(run.root / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "--nonsense")

    assert result.returncode != 0
    assert "unknown argument" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_extra_prose_after_the_document_dies_rather_than_being_silently_ignored(run):
    """A caller cannot append prose to what the run receives — anything after the positionals
    that is not a known flag is refused."""
    run.project("example-product")
    run.document(run.root / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "and also summarise the previous round")

    assert result.returncode != 0
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_unknown_project_dies_naming_the_project_card_path(run):
    result = run("nope", "fdr")

    assert result.returncode != 0
    assert "no project card at" in result.stderr
    assert "system/projects/nope/project.md" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_project_card_without_product_path_dies(run):
    project_dir = run.root / "system" / "projects" / "example-product"
    project_dir.mkdir(parents=True)
    (project_dir / "project.md").write_text("# example-product\n\nno binding line here\n")

    result = run("example-product", "fdr")

    assert result.returncode != 0
    assert "no 'Product path:' line" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_neither_the_document_nor_a_companion_is_refused_naming_both_paths(run):
    """Neither file is the one case that still refuses: there is nothing to answer. The message
    names BOTH paths it looked at, because after the bare-stem relaxation the document's absence
    alone is no longer the reason."""
    run.project("example-product")
    # neither docs/fdr.md nor docs/fdr_open_issues.md written

    result = run("example-product", "fdr")

    assert result.returncode != 0
    assert "products/thing/docs/fdr.md" in result.stderr
    assert "products/thing/docs/fdr_open_issues.md" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


# --- the document homes — a project's documents do not all live in its product's docs/ ------
#   The Agari is written into the instance, at system/projects/<project>/agari.md, and its
#   companion beside it. Measured on a live product, 2026-09-17: `<project> Agari` was refused
#   while `system/projects/<project>/agari_open_issues.md` stood open.


def _launched_prompt(companion):
    """The prompt argument of a launched Claude run: this launcher's own fixed prompt, then the
    sentence the Claude adapter appends for the level every run here starts at, `high`."""
    return (
        f"invoke the companion-self-answer skill for the companion at {companion}. "
        'Pass `--reasoning-effort "high"` to the builder; the launch already resolved this value.'
    )


def _project_home_companion(run, project, stem, skill=None):
    home = run.root / "system" / "projects" / project
    header = f"> Companion to `{stem}.md`.\n"
    if skill:
        header += f"> Answer inline, commit, then re-run `{skill}`.\n"
    path = home / f"{stem}_open_issues.md"
    path.write_text(f"# {stem} open issues\n\n{header}\n---\n\n## 1. Open issues\n")
    return path


def test_a_companion_in_the_projects_own_home_resolves_and_launches(run):
    run.project("example-product")
    companion = _project_home_companion(run, "example-product", "agari", skill="project-agari")
    (companion.parent / "agari.md").write_text("# Agari\n")
    run.skill_launcher("project-agari", agent="cpo")
    run.agent_file("cpo")

    result = run("example-product", "Agari")

    assert result.returncode == 0, result.stderr
    assert f"Document:  {companion.parent / 'agari.md'}" in result.stdout
    argv = run.launched_argv()
    assert _prompt_of(argv) == _launched_prompt(companion)
    assert argv[argv.index("--agent") + 1] == "cpo"


def test_a_companion_standing_alone_in_the_projects_home_resolves(run):
    run.project("example-product")
    companion = _project_home_companion(run, "example-product", "agari", skill="project-agari")

    result = run("example-product", "agari", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert f"Companion: present — {companion}" in result.stdout


def test_the_reporter_is_pointed_at_the_instance_for_a_document_in_the_projects_home(run):
    """The reporter walks `system/projects/*/trail/<doc>/` under the root it is given, and a
    product path holds no `system/`, so a project-home document's report is found only from the
    instance root."""
    run.project("example-product")
    _project_home_companion(run, "example-product", "agari", skill="project-agari")

    run("example-product", "agari")

    argv = run.watcher_argv()
    assert argv[argv.index("--artifact-path") + 1] == str(run.root)
    assert "example-product-agari" in argv


def test_neither_home_holding_the_document_names_every_path_looked_at(run):
    run.project("example-product")

    result = run("example-product", "agari")

    assert result.returncode != 0
    for looked in ("products/thing/docs/agari.md", "products/thing/docs/agari_open_issues.md",
                   "system/projects/example-product/agari.md", "system/projects/example-product/agari_open_issues.md"):
        assert looked in result.stderr, looked
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_document_in_both_homes_is_refused_rather_than_guessed(run):
    product = run.project("example-product")
    run.companion(product, "agari")
    _project_home_companion(run, "example-product", "agari")

    result = run("example-product", "agari", "--dry-run")

    assert result.returncode != 0
    assert "both" in result.stderr
    assert "products/thing/docs" in result.stderr and "system/projects/example-product" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


# --- the bare companion stem — a companion with no document entry behind it ------------------
#   product-architecture's companion answers for the ADR and the NFDR together and is named for
#   neither, so `docs/architecture.md` is never written. Owner's ruling 2026-08-31: the launcher's
#   guard relaxes; the skill needed the document file at no point.


def test_a_companion_with_no_document_behind_it_resolves_and_launches(run):
    product = run.project("example-product")
    run.companion(product, "architecture", skill="product-architecture")
    run.skill_launcher("product-architecture", agent="principal-architect")
    run.agent_file("principal-architect")
    assert not (product / "docs" / "architecture.md").exists()

    result = run("example-product", "architecture")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert any("architecture_open_issues.md" in a for a in argv), argv
    assert "principal-architect" in argv


def test_a_bare_stem_reports_the_document_as_absent_rather_than_naming_a_file(run):
    product = run.project("example-product")
    run.companion(product, "architecture", skill="product-architecture")

    result = run("example-product", "architecture", "--dry-run")

    assert result.returncode == 0, result.stderr
    document_line = next(l for l in result.stdout.splitlines() if l.startswith("Document:"))
    assert "none" in document_line.lower()
    assert "products/thing/docs/architecture_open_issues.md" in result.stdout


def test_the_bare_stems_case_is_read_off_the_companion_entry_not_composed(run):
    """The same rule the document half already follows. The argument is lower-case, the companion
    on disk is not, and the path that reaches the prompt is the entry's own."""
    product = run.project("example-product")
    docs = product / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "Architecture_open_issues.md").write_text(
        "# Architecture open issues\n\n> Answer inline, commit, then re-run `product-architecture`.\n"
    )

    result = run("example-product", "architecture", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "docs/Architecture_open_issues.md" in result.stdout
    assert "docs/architecture_open_issues.md" not in result.stdout


def test_a_bare_stem_still_reads_its_seat_off_the_companion(run):
    """Seat resolution reads the companion, not the document, so it is unaffected by the absent
    document — pinned because the relaxation is what makes this path reachable at all."""
    product = run.project("example-product")
    run.companion(product, "architecture", skill="product-architecture")
    run.skill_launcher("product-architecture", agent="principal-architect")
    run.agent_file("principal-architect")

    result = run("example-product", "architecture", "--dry-run")

    assert "Seat:      principal-architect" in result.stdout


def test_a_bare_stem_labels_the_watcher_with_the_stem_the_companion_carries(run):
    product = run.project("example-product")
    run.companion(product, "architecture", skill="product-architecture")

    run("example-product", "architecture")

    argv = run.watcher_argv()
    assert "example-product-architecture" in argv


def test_a_present_document_still_wins_over_the_bare_stem_path(run):
    """The relaxation is a fallback, never a replacement: with both files there, the document is
    resolved and reported exactly as it was before."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert "Document:  " in result.stdout
    assert "products/thing/docs/fdr.md" in result.stdout
    assert "none" not in result.stdout.split("Companion:")[0].lower()


def test_a_document_name_the_fixture_invents_resolves_with_no_case_arm(run):
    """A launcher that grew a `case` arm naming a known document would fail on any name it
    does not enumerate — this name exists nowhere else in the repo or in this suite."""
    run.project("example-product")
    run.document(run.root / "products" / "thing", "zorpix")

    result = run("example-product", "zorpix", "--dry-run")

    assert result.returncode == 0
    assert "products/thing/docs/zorpix.md" in result.stdout


def test_the_argument_case_never_reaches_the_path_when_the_file_disagrees(run):
    """The negative half of the case rule: an upper-case argument against a lower-case file must
    not appear in the composed path. It is the assertion that separates "read the docs/ entry"
    from "echo what the caller typed" — the plan's § The argument surface, corrected 2026-08-30:
    "Resolve it against the docs/ directory entry and take the file's own case."
    """
    run.project("example-product")
    run.document(run.root / "products" / "thing", "fdr")

    result = run("example-product", "FDR", "--dry-run")

    assert result.returncode == 0
    assert "docs/fdr.md" in result.stdout
    assert "docs/FDR.md" not in result.stdout


def test_a_lower_case_argument_still_resolves_to_the_upper_case_file(run):
    """The symmetric case, and the one a caller actually hits: the six upper-case documents typed
    in lower case. `<document>` "matches <document> case-insensitively" against the docs/ entry
    (§ The argument surface), so `prd` must reach docs/PRD.md at the file's own case — neither
    refused nor re-spelled as docs/prd.md.
    """
    product = run.project("example-product")
    run.document(product, "PRD")

    result = run("example-product", "prd", "--dry-run")

    assert result.returncode == 0
    assert f"{product}/docs/PRD.md" in result.stdout
    assert "docs/prd.md" not in result.stdout


def test_a_document_named_in_upper_case_resolves_to_the_file_as_it_is_named(run):
    """§ The argument surface: `<document>` is "any document carrying the open-issues pattern,
    named as the document is named (FDR, PRD, ...)", and § Post-implementation acceptance names
    PRD-shaped documents as in scope. Only the FDR is lowercase on disk —
    `skills/principal-pm/.claude/skills/product-fdr/SKILL.md:68` states it outright: "The three names are lowercase,
    and they match each other on purpose." The sibling skills' Outputs tables name upper-case
    documents, and so do the two live products, which each hold docs/PRD.md, SRS.md, UXD.md,
    DESIGN.md, CONTENT.md, SDD.md beside a lowercase docs/fdr.md.
    """
    product = run.project("example-product")
    run.document(product, "PRD")
    companion = run.companion(product, "PRD", skill="product-prd")

    result = run("example-product", "PRD", "--dry-run")

    assert result.returncode == 0
    assert f"{product}/docs/PRD.md" in result.stdout
    assert "docs/prd.md" not in result.stdout
    assert str(companion) in result.stdout


def test_the_companion_case_is_read_off_disk_not_derived_from_the_document(run):
    """A companion's case does NOT reliably follow its document's, so it gets the same
    directory-entry lookup the document gets rather than a name composed from the document's
    stem.

    Measured on a live product, 2026-08-30: `docs/SRS.md` beside `docs/srs_open_issues.md`. The
    lower-case half is written by whichever run opened it — `companion-self-answer` finds that
    document's template by globbing `<CORE>/templates/*/*_open_issues_template.md`, whose
    filenames are all lower-case, and the skill states no destination name — so the run takes
    the template's stem. Composing `SRS_open_issues.md` here names a file no directory entry
    matches, and a case-insensitive volume opens it anyway, so the run is handed a path that is
    wrong and works. On a case-sensitive volume it is wrong and fails."""
    product = run.project("example-product")
    run.document(product, "SRS")
    docs = Path(product) / "docs"
    companion = docs / "srs_open_issues.md"
    companion.write_text(
        "# SRS open issues\n\n> Companion to `SRS.md`.\n"
        "> Answer inline, commit, then re-run `product-srs`.\n\n---\n\n"
        "## 1. Open issues\n\n### 1.1 A question\n- **Answer:** <the owner fills this in>\n")

    result = run("example-product", "SRS", "--dry-run")

    assert result.returncode == 0
    assert f"{product}/docs/SRS.md" in result.stdout      # the document keeps ITS case
    assert f"{product}/docs/srs_open_issues.md" in result.stdout   # the companion keeps ITS own
    assert "SRS_open_issues.md" not in result.stdout


def test_the_launched_prompt_names_the_companion_as_it_is_named_on_disk(run):
    """The composed prompt is the one string this launcher exists to produce, and the skill it
    launches is "given the companion to answer - a path, required" (SKILL.md description). It
    must carry the companion's real path, not a re-cased spelling of it.
    """
    product = run.project("example-product")
    run.document(product, "PRD")
    companion = run.companion(product, "PRD", skill="product-prd")

    result = run("example-product", "PRD")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert _prompt_of(argv) == _launched_prompt(companion)


def test_the_fdr_still_resolves_to_the_lowercase_file_the_foundation_step_names(run):
    """The constraint that keeps the case question a decision rather than a find-replace: the FDR
    is the one document whose file is lowercase (`<CORE>/doctrine/setup/setting_up_a_project.md`
    § The foundation step), and the plan's own
    § Post-implementation acceptance runs `FDR` against a product carrying
    `docs/fdr_open_issues.md`. Whatever resolves `PRD` must not break this.
    """
    product = run.project("example-product")
    run.document(product, "fdr")
    companion = run.companion(product, "fdr", skill="product-fdr")

    result = run("example-product", "FDR", "--dry-run")

    assert result.returncode == 0
    assert f"{product}/docs/fdr.md" in result.stdout
    assert str(companion) in result.stdout


def test_missing_companion_is_reported_absent_and_does_not_refuse(run):
    run.project("example-product")
    run.document(run.root / "products" / "thing", "fdr")
    # no docs/fdr_open_issues.md written

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0
    assert "absent" in result.stdout.lower()


def test_present_companion_is_reported_present(run):
    run.project("example-product")
    run.document(run.root / "products" / "thing", "fdr")
    run.companion(run.root / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0
    assert "products/thing/docs/fdr_open_issues.md" in result.stdout


def test_the_product_path_is_read_through_the_trailing_html_comment_every_card_carries(run):
    project_dir = run.root / "system" / "projects" / "example-product"
    project_dir.mkdir(parents=True)
    (project_dir / "project.md").write_text(
        "# example-product\n\n**Product path:** products/thing   <!-- set at scaffold -->\n"
    )
    (run.root / "products" / "thing" / "docs").mkdir(parents=True)
    run.document(run.root / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0
    assert "<!--" not in result.stdout


def test_relative_product_path_gets_no_extra_add_dir_beyond_the_pins_own(run):
    """Task 19: a relative product path itself gets no --add-dir, but the pin's own
    (Task 7's delivery, always present on a Claude run) still is."""
    run.project("example-product", product_path="products/thing")
    run.document(run.root / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "--dry-run")

    argv = _dry_run_argv(result.stdout)
    granted = _granted_dirs(argv)
    assert len(granted) == 1
    assert "products/thing" not in granted[0]


def test_absolute_product_path_resolves_into_the_products_own_repo_and_gets_add_dir(
    run, tmp_path_factory
):
    external = tmp_path_factory.mktemp("external_product")
    run.project("example-product", product_path=str(external))
    run.document(external, "fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0
    assert "--add-dir" in result.stdout
    assert str(external) in result.stdout


def test_tilde_product_path_expands_to_home_and_gets_add_dir(run):
    run.project("example-product", product_path="~/products/thing")
    run.document(run.home / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0
    assert "--add-dir" in result.stdout
    assert str(run.home / "products" / "thing") in result.stdout


# --- Task 19 — the pin ---------------------------------------------------------------------


def test_dry_run_prints_the_pin_line(run):
    # pin_enter runs right after the CORE_DIR guard, ahead of everything else.
    run.project("example-product")
    run.document(run.root / "products" / "thing", "fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_claude_seat_and_model_forms_both_carry_the_delivery(run):
    """The two Claude forms this launcher can take — a resolved seat's --agent, and the seatless
    fallback — both go through the one adapter and both carry the pin delivery."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    seated = run("example-product", "fdr", "--dry-run")
    assert seated.returncode == 0, seated.stderr
    seated_argv = _dry_run_argv(seated.stdout)
    assert seated_argv[seated_argv.index("--agent") + 1] == "principal-pm"
    assert "--setting-sources" in seated_argv
    assert "--plugin-dir" in seated_argv

    run.companion(product, "fdr")  # no skill named -> no seat -> the bare fallback
    fallback = run("example-product", "fdr", "--dry-run")
    assert fallback.returncode == 0, fallback.stderr
    fallback_argv = _dry_run_argv(fallback.stdout)
    assert "--model" not in fallback_argv
    assert "--agent" not in fallback_argv
    assert "--setting-sources" in fallback_argv
    assert "--plugin-dir" in fallback_argv


def test_the_claude_launch_grants_companion_self_answer(run):
    # `companion-self-answer` is grouped under `skills/companion/`: granting it reaches that group,
    # so the launched plugin lists it and no other group.
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    listed, groups = _plugin_skills(_dry_run_argv(result.stdout))
    assert "companion-self-answer" in listed
    assert groups == {"companion"}


def test_codex_prompt_paths_lie_in_the_pin(run):
    """Nothing on the Codex path is rebuilt — the <CORE> and SKILL.md paths it already derives
    from $CORE_DIR / $SKILLS_ROOT now resolve inside the pin, because pin_enter has already
    re-exec'd this script from there by the time those variables are read."""
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_SKILLS_ROOT", None)
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr")

    result = run("example-product", "fdr", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    pin_match = re.search(r"^Pin: (\S+) \(inherited\)$", result.stdout, re.MULTILINE)
    assert pin_match, result.stdout
    pin_root = pin_match.group(1)
    prompt = _dry_run_argv(result.stdout)[-1]
    assert f"<CORE> resolves to: {pin_root}/core." in prompt
    argv = _dry_run_argv(result.stdout)
    assert argv[argv.index("--skill-path") + 1] == f"{pin_root}/skills/companion/.claude/skills/companion-self-answer/SKILL.md"
    # The instance root itself legitimately still appears (the companion path this run answers,
    # and the "instance root is:" sentence) — only the SKILL.md/<CORE> paths move into the pin.


# --- Task 2 — the seat is resolved per run, from the companion ---------------------------


def test_seat_is_read_from_the_producing_skills_own_launcher(run):
    """Companion found → header names a skill → that skill's own launcher's `--agent` value
    is passed through. Read, never mapped."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" in argv and argv[argv.index("--agent") + 1] == "principal-pm"
    assert "--model" not in argv


def _intelligence(skill_dir, provider, model="claude-m-1", effort=None, text=None):
    """`<skill dir>/intelligence/<provider>.md` — the producing skill's model and effort."""
    folder = skill_dir / "intelligence"
    folder.mkdir(exist_ok=True)
    if text is None:
        text = f"# {provider} intelligence\n\n**Model:** {model}\n"
        if effort is not None:
            text += f"**Effort:** {effort}\n"
    (folder / f"{provider}.md").write_text(text)
    return folder / f"{provider}.md"


def _skill_declaration(run, skill, agent=None, model=None, group=None):
    """A producing skill's own `launcher.md`, where `<CORE>/launchers/skill/launcher.sh` reads its
    seat — flat under `.claude/skills/`, or grouped under `skills/<group>/`."""
    base = run.root / "skills" / group if group else run.root
    skill_dir = base / ".claude" / "skills" / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {skill}\n---\n")
    fields = ""
    if agent:
        fields += f"**Agent:** {agent}\n"
    if model:
        fields += f"**Model:** {model}\n"
    (skill_dir / "launcher.md").write_text(
        f"# {skill} — unattended launch\n\nProse naming **Agent:** mid-line.\n\n{fields}"
        f"**Arguments:** <project>\n**Prompt:** invoke the {skill} skill for the {{project}} project.\n")
    return skill_dir / "launcher.md"


def test_seat_is_read_from_the_producing_skills_launcher_md(run):
    """A skill started through the skill launcher declares its seat in its own `launcher.md`, and
    has no launcher folder of its own to read one from."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    declaration = _skill_declaration(run, "product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    assert f"Seat:      principal-pm (from {declaration})" in result.stdout
    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "principal-pm"


def test_a_satellite_reads_the_seat_from_the_hosts_launcher_md(run, tmp_path_factory):
    """A satellite holds no skills: the producing skill's `launcher.md` is read from the host."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.agent_file("principal-pm")
    host = tmp_path_factory.mktemp("host")
    skill_dir = host / "skills" / "principal-pm" / ".claude" / "skills" / "product-fdr"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: product-fdr\n---\n")
    (skill_dir / "launcher.md").write_text(
        "**Agent:** principal-pm\n**Arguments:** <project>\n**Prompt:** invoke product-fdr for {project}.\n")
    run.env["LAUNCH_COMPANION_SELF_ANSWER_SKILLS_ROOT"] = str(host)

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    assert f"Seat:      principal-pm (from {skill_dir / 'launcher.md'})" in result.stdout


def test_a_grouped_skills_launcher_md_is_found_too(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    _skill_declaration(run, "product-fdr", agent="principal-pm", group="principal-pm")
    run.agent_file("principal-pm")

    run("example-product", "fdr")

    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "principal-pm"


def test_the_launcher_md_wins_over_a_launcher_folder_of_the_same_name(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    _skill_declaration(run, "product-fdr", agent="principal-pm")
    run.skill_launcher("product-fdr", agent="cto")
    run.agent_file("principal-pm")
    run.agent_file("cto")

    run("example-product", "fdr")

    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "principal-pm"


def test_a_launcher_md_naming_no_agent_names_no_seat_and_the_run_takes_the_producers_model(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    _intelligence(_skill_declaration(run, "product-fdr").parent, "claude", "claude-m-1")

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert "--agent" not in argv
    assert argv[argv.index("--model") + 1] == "claude-m-1"


def test_a_posture_free_agent_is_not_taken_as_the_seat(run):
    """A launcher may pass `--agent` for a tool grant with no posture behind it —
    one can be passed as `delegate`. The grep cannot tell that from a seat; the loader can. No
    loader, no seat: the run falls back exactly as it does when no seat is derivable."""
    product = run.project("example-product")
    run.document(product, "sdd")
    run.companion(product, "sdd", skill="product-sdd")
    run.skill_launcher("product-sdd", agent="delegate")
    run.agent_file("delegate", loader=False)

    result = run("example-product", "sdd", "--dry-run")

    assert result.returncode == 0
    assert "posture-free agent, not a seat" in result.stdout
    # A token check, not a substring one — the pin delivery's own --agents flag (Task 7)
    # contains "--agent" as a substring and would false-positive-fail a substring check.
    assert "--agent" not in shlex.split(result.stdout.split("DRY RUN", 1)[1])
    assert "--model" not in shlex.split(result.stdout.split("DRY RUN", 1)[1])


def test_the_seat_check_reads_the_global_loaders_in_the_core_it_runs_from(run):
    """No fixture loaders: the launcher runs from the session pin, whose `core/roles/loaders/`
    holds `content_manager_global.md`, so content-manager is a seat. A pin holds no `system/`, so a
    check reading the instance tree's `system/loaders/` beside the script found nothing there and
    took every seat for a posture-free agent."""
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_LOADERS_DIR")
    product = run.project("example-product")
    run.document(product, "CONTENT")
    run.companion(product, "CONTENT", skill="product-content")
    run.skill_launcher("product-content", agent="content-manager")
    run.agent_file("content-manager", loader=False)

    result = run("example-product", "CONTENT")

    assert result.returncode == 0, result.stderr
    assert "posture-free agent" not in result.stdout
    argv = run.launched_argv()
    assert argv[argv.index("--agent") + 1] == "content-manager"


def test_the_core_loaders_still_tell_a_posture_free_agent_from_a_seat(run):
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_LOADERS_DIR")
    product = run.project("example-product")
    run.document(product, "sdd")
    run.companion(product, "sdd", skill="product-sdd")
    run.skill_launcher("product-sdd", agent="delegate")
    run.agent_file("delegate", loader=False)

    result = run("example-product", "sdd", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "posture-free agent, not a seat" in result.stdout


def test_seat_is_found_via_the_prompt_literal_grep_when_the_folder_lacks_the_bare_name(run):
    """The skill's own Step 6 names a second resolution path for when the launcher folder does
    not carry the producing skill's bare name — the fixed prompt-literal grep."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="renamed-skill")
    run.skill_launcher(
        "renamed-skill", agent="renamed-seat",
        folder="launch-renamed-skill", prompt_skill="renamed-skill",
    )
    run.agent_file("renamed-seat")

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" in argv and argv[argv.index("--agent") + 1] == "renamed-seat"


def test_no_rerun_line_falls_back_to_a_bare_model_session(run):
    """A companion is live, but its header names no skill to re-run — never guessed, never
    grepped for a plausible one."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill=None)

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" not in argv
    assert "--model" not in argv


def test_no_companion_at_all_falls_back_to_a_bare_model_session(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    # no companion written

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" not in argv
    assert "--model" not in argv


def test_no_launcher_for_the_named_skill_falls_back_to_a_bare_model_session(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="nobody-launches-this")

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" not in argv
    assert "--model" not in argv


def test_a_seat_whose_agent_file_is_absent_falls_back_and_names_it_in_the_prompt(run):
    """`principal-architect` is the live case: files name it and `.claude/agents/` does not
    hold it. Never invent an agent name, and never halt."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="some-skill")
    run.skill_launcher("some-skill", agent="principal-architect")
    # deliberately no run.agent_file() call — the agent file does not exist

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" not in argv
    assert "--model" not in argv
    assert "principal-architect" in _prompt_of(argv)


def _seat_run(run, seat):
    """A `example-product` FDR produced by `product-fdr` under `seat`."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent=seat)
    return product


def test_grouped_seat_with_loader_resolves_as_seat(run):
    _seat_run(run, "pm")
    run.agent_file("pm")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Seat:      pm (from " in result.stdout


def test_grouped_seat_without_loader_prints_posture_free_line(run):
    _seat_run(run, "delegate")
    run.agent_file("delegate", loader=False)

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Seat:      delegate named by " in result.stdout
    assert "is a posture-free agent, not a seat" in result.stdout


def test_agent_groups_default_to_the_skills_roots_groups(run):
    """With no override, the groups searched are `$SKILLS_ROOT/skills` — the host root's — so a
    seat is found where the shipped tree holds it."""
    del run.env["LAUNCH_COMPANION_SELF_ANSWER_AGENT_GROUPS_DIR"]
    _seat_run(run, "pm")
    agent = run.root / "skills" / "pm" / ".claude" / "agents" / "pm.md"
    agent.parent.mkdir(parents=True, exist_ok=True)
    agent.write_text("# pm\n")
    (run.loaders_dir / "pm_global.md").write_text("# pm loader\n")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Seat:      pm (from " in result.stdout


def test_item_seat_tag_matches_any_case_in_groups(run):
    _seat_fixture(run, [("1.1", "PM", False)], agents=("pm",))

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) == "pm"


def test_missing_group_agent_prints_cp46_line(run):
    _seat_run(run, "ghost")

    # A real launch, read off the stubbed `claude`: the report sentence carries an em dash, which
    # the dry run's `printf %q` splits under the fixture's locale.
    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.startswith("Seat:      ghost"))
    assert line == (
        "Seat:      ghost named by "
        + line.split("named by ", 1)[1].split(", but no agent file", 1)[0]
        + ", but no agent file for it in any group — falling back to a seatless session"
    )
    assert ".claude/agents/" not in line
    assert ("this run could not take the 'ghost' seat named by the companion's producing skill's "
            "launcher — no agent file exists for it") in _prompt_of(run.launched_argv())


@pytest.mark.parametrize("provider", ["codex", "gemini"])
def test_codex_prompt_names_group_file_for_seat(run, provider):
    _codex_fixture(run)
    _seat_run(run, "architect")
    run.agent_file("architect")

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    group_file = run.groups_dir / "architect" / ".claude" / "agents" / "architect.md"
    assert str(group_file) in _dry_run_argv(result.stdout)[-1]


def test_seat_grep_ignores_an_agent_mentioned_only_in_a_comment(run):
    """A comment reads `--agent` in prose without a real invocation line; the grep is anchored
    on the adjacent `--permission-mode` so it cannot be misread as a resolved seat."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="commented-skill")
    d = run.launchers_dir / "commented-skill"
    d.mkdir(parents=True)
    (d / "launcher.sh").write_text(
        "#!/usr/bin/env bash\n"
        "# WHY NO --agent: this skill has no seat of its own.\n"
        'prompt="invoke the commented-skill skill for the thing."\n'
        'set -- claude --bg "$prompt" --model opus --permission-mode auto\n'
    )

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert "--agent" not in argv
    assert "--model" not in argv


# --- Task 3 — the launch and its completion watch -----------------------------------------


def test_launches_with_a_fixed_prompt_naming_the_resolved_companion(run):
    """Fence 4: proven on a REAL launch, never paired only with --dry-run — a --dry-run test
    proves nothing about caller prose."""
    product = run.project("example-product")
    run.document(product, "fdr")
    companion = run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr")

    assert result.returncode == 0
    argv = run.launched_argv()
    assert argv[:4] == _PRINT_RUN_HEAD
    assert argv[argv.index("--permission-prompts") + 1] == "none"
    assert _prompt_of(argv) == _launched_prompt(companion)


def test_caller_cannot_append_to_the_prompt(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr", "--dry-run")

    # --dry-run means nothing launched; a caller has no channel to compose prose into anyway —
    # the positionals are structured (project, document), never free text.
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_the_run_is_launched_in_auto_permission_mode(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr")

    argv = run.launched_argv()
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_allowed_tools_and_bare_are_never_passed_and_the_run_is_a_print_run(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr")

    argv = run.launched_argv()
    assert "--allowedTools" not in argv
    assert "--bare" not in argv
    assert "--bg" not in argv
    assert argv[:4] == _PRINT_RUN_HEAD


# --- the reporter (fence 3 — asserted against the real REGISTRY) ---------------------------


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
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr")

    argv = run.watcher_argv()
    assert argv != []
    name = argv[argv.index("--reporter") + 1]
    assert name in _registered_reporter_names(), (
        f"--reporter {name} is not in reporters.py's REGISTRY — it would silently behave as generic"
    )


def test_watcher_is_spawned_with_the_companion_self_answer_reporter(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr")

    argv = run.watcher_argv()
    assert argv != []
    assert argv[argv.index("--reporter") + 1] == "companion-self-answer"


def test_watcher_is_told_the_resolved_product_path_via_artifact_path(run, tmp_path_factory):
    """Fence 6: `--artifact-path` stays a ROOT — the reporter globs document homes under it, and
    the companion's own file path would find no report."""
    external = tmp_path_factory.mktemp("external_product")
    run.project("example-product", product_path=str(external))
    run.document(external, "fdr")

    run("example-product", "fdr")

    argv = run.watcher_argv()
    assert argv[argv.index("--artifact-path") + 1] == str(external)
    assert "--product-path" not in argv


def test_watcher_is_handed_the_runs_process_and_its_log(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr")

    argv = run.watcher_argv()
    assert argv[argv.index("--provider") + 1] == "claude"
    assert argv[argv.index("--pid") + 1].isdigit()
    assert argv[argv.index("--log") + 1].startswith(
        str(run.root / "system" / "logs" / "claude-self-answer-example-product-fdr-")
    )


def test_the_watch_still_runs_when_no_notifier_is_installed(run):
    """The watch is what hands a chain its outcome, so it runs whether or not anything can be
    told; with no notifier it is told to notify nothing."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.no_notifier()

    result = run("example-product", "fdr")

    assert result.returncode == 0
    assert run.launched_argv() != []
    argv = run.watcher_argv()
    assert argv[argv.index("--notify") + 1] == "/usr/bin/true"


# --- the two <CORE>-relative paths this folder makes it easy to get wrong (fence 2) --------


def test_watcher_is_found_at_its_resolved_home_when_the_env_override_is_unset(run):
    """Pinned deliberately: this launcher sits at `<CORE>/launchers/companion-self-answer/`, one
    level deeper than the flat launchers. A wrong default does not fail the launch — the primary
    run still starts and only the completion notification never arrives — so the override is
    unset ON PURPOSE and the real `watch_process.py` has to resolve, spawn, and write its log."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.default_watcher()

    result = run("example-product", "fdr")

    assert result.returncode == 0
    assert "completion watch skipped" not in result.stdout
    assert "Completion watch:" in result.stdout
    assert len(_watcher_logs(run.root)) >= 1


def test_the_default_watcher_path_is_written_relative_not_absolute():
    text = _SCRIPT.read_text()

    assert '$CORE_DIR/tools/watch_process.py' in text
    assert '$SCRIPT_DIR/../tools/watch_process.py' not in text


def test_detach_watcher_is_found_at_its_resolved_home_when_nothing_overrides_it(run):
    """The second `<CORE>`-relative path, and the one that fails LOUDLY. There is no env override
    for `DETACH_LIB`, so every passing launch in this suite already runs against the real
    `core/tools/detach_process_watcher.sh` at its real relative depth."""
    product = run.project("example-product")
    run.document(product, "fdr")

    result = run("example-product", "fdr")

    assert result.returncode == 0
    assert "no completion-watch library at" not in result.stdout
    assert run.watcher_argv() != []


def test_a_missing_detach_watcher_is_reported_distinctly_and_does_not_block_the_launch(
    run, tmp_path_factory
):
    product = run.project("example-product")
    run.document(product, "fdr")

    isolated = tmp_path_factory.mktemp("no_detach_lib")
    core_root = isolated / "core"
    launcher_dir = core_root / "launchers" / "companion-self-answer"
    launcher_dir.mkdir(parents=True)
    copied_script = launcher_dir / "launcher.sh"
    copied_script.write_text(_SCRIPT.read_text())
    copied_script.chmod(0o755)
    tools_dir = core_root / "tools"
    tools_dir.mkdir()  # no detach_process_watcher.sh inside it
    # `isolated` carries its own pin.json, so `pin_enter` treats this tree as already its own
    # pin (rule 1) — no `pin.py` call there — but the Claude branch still shells out to
    # `agent_run.py` (Task 19) for its argv, which imports `model_assignment` / `task_context` / `env_file`.
    for tool in ("pin_run.sh", "pin.py", "agent_run.py", "model_assignment.py", "task_context.py",
                 "hook_wiring.py",
                 "env_file.py", "detached_run.sh", "intelligence.py", "run_intelligence.py",
                 "providers.py"):
        shutil.copy(_CORE_DIR / "tools" / tool, tools_dir / tool)
    (isolated / "pin.json").write_text(
        json.dumps({"id": "isolated", "source_host_root": str(isolated), "created": "1970-01-01T00:00:00+00:00"})
        + "\n"
    )

    result = run("example-product", "fdr", script=copied_script)

    assert result.returncode == 0
    assert run.launched_argv() != []          # the primary launch still happened
    assert run.watcher_argv() == []
    assert "no completion-watch library at" in result.stdout


def test_the_detach_block_is_not_hand_copied():
    text = _SCRIPT.read_text()

    assert "detach_process_watcher.sh" in text
    assert "source" in text
    assert "nohup python3" not in text and 'nohup "python3"' not in text


def _watcher_logs(root, expect=1):
    logs_dir = root / "system" / "logs"
    last_sizes = None
    stable_reads = 0
    for _ in range(100):
        if logs_dir.exists():
            logs = sorted(p for p in logs_dir.glob("watch-*.log") if p.stat().st_size)
            if len(logs) >= expect:
                sizes = tuple(p.stat().st_size for p in logs)
                if sizes == last_sizes:
                    stable_reads += 1
                    if stable_reads >= 2:
                        return logs
                else:
                    stable_reads = 0
                last_sizes = sizes
        time.sleep(0.05)
    return sorted(logs_dir.glob("watch-*.log")) if logs_dir.exists() else []


# --- --keep-awake ---------------------------------------------------------------------------


def test_keep_awake_reaches_the_shared_home(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run.hold_watcher_until_kept_awake()
    run("example-product", "fdr", "--keep-awake")

    assert run.caffeinate_calls() >= 1


def test_no_keep_awake_flag_means_zero_caffeinate_invocations(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr")

    assert run.caffeinate_calls(wait=2.5) == 0


# --- --dry-run -------------------------------------------------------------------------------


def _dry_run_argv(stdout):
    """The provider argv a dry run printed, from the provider's own name on."""
    for line in stdout.splitlines():
        tokens = _provider_argv(shlex.split(line.strip())) if line.strip() else []
        if tokens[:1] in (["claude"], ["codex"], ["codex-skill"], ["agy"]):
            return tokens
    raise AssertionError(f"no provider command in:\n{stdout}")


def test_dry_run_prints_the_resolved_companion_seat_and_exact_command(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    companion = run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0
    assert str(companion) in result.stdout
    assert "principal-pm" in result.stdout
    assert "DRY RUN" in result.stdout
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_dry_run_spawns_no_watcher(run):
    product = run.project("example-product")
    run.document(product, "fdr")

    run("example-product", "fdr", "--dry-run")

    assert run.watcher_argv() == []


def test_dry_run_prints_the_exact_command_the_real_launch_runs(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    dry = run("example-product", "fdr", "--dry-run")
    run("example-product", "fdr")

    printed = _dry_run_argv(dry.stdout)
    actual = ["claude", *run.launched_argv()]
    assert _without_session_id(printed) == _without_session_id(actual)


def test_every_guard_still_fires_under_dry_run(run):
    result = run("nope", "fdr", "--dry-run")

    assert result.returncode != 0
    assert "no project card at" in result.stderr


# --- --instance-root override ----------------------------------------------------------------


def test_instance_root_override_is_honoured(run, tmp_path_factory):
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    product = run.project("example-product")
    run.document(product, "fdr")

    result = run("--instance-root", str(run.root), "example-product", "fdr", cwd=str(elsewhere))

    assert result.returncode == 0
    assert run.launched_argv() != []


# --- no literal <CORE> path -------------------------------------------------------------------


def test_the_launcher_names_no_literal_core_path():
    text = _SCRIPT.read_text()
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))

    assert "~/.claude/" not in code
    assert not re.search(r"(?<![\w/.])core/", code)


# --- executable --------------------------------------------------------------------------


def test_launcher_is_executable():
    assert os.access(_SCRIPT, os.X_OK), f"{_SCRIPT} is not executable"


def test_dry_run_states_the_arm_it_would_run_under(run, tmp_path):
    """`a-launcher-tags-its-own-run` — a dry run that hides the instrument is a dry run that
    lies. With a published endpoint file present, `instrument_run` prints the arm it derived
    (this launcher's own directory name) even though nothing is actually spawned."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")
    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.arm=companion-self-answer" in result.stdout
    assert "--settings" in result.stdout, "a dry run that hides the settings hides what a backgrounded run needs"


# Exercise the real provider adapter with a recording executable, without paid model runs.
def _codex_fixture(run):
    skill = run.root / "skills/companion/.claude/skills/companion-self-answer"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Answer the companion\n")
    log = run.root / "codex-argv.json"
    run.env["CODEX_ARGV_LOG"] = str(log)
    stub = run.root / "bin/codex"
    from kensaiapp_launchers_conftest import CODEX_STUB
    stub.write_text(CODEX_STUB)
    stub.chmod(0o755)
    return skill, log


def _codex_args(path):
    import json

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if path.exists() and path.read_text():
            return json.loads(path.read_text())
        time.sleep(0.05)
    pytest.fail("Codex recording executable did not run")


@pytest.mark.parametrize("flags", [(), ("--provider", "codex"), ("--provider=codex",)])
def test_codex_self_answer_routes_seat_and_completion(run, flags):
    product = run.project("example-product", str(run.root / "external product"))
    run.document(product, "CONTENT")
    companion = run.companion(product, "CONTENT", skill="product-content")
    declaration = run.root / "skills/content-manager/.claude/skills/product-content"
    declaration.mkdir(parents=True)
    (declaration / "launcher.md").write_text("**Agent:** content-manager\n")
    _intelligence(declaration, "codex", "claude-m-1")
    run.agent_file("content-manager")
    agent = run.agent_path("content-manager")
    skill, log = _codex_fixture(run)
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex" if not flags else "claude"
    hook = run.root / "chain-completion.sh"
    hook.write_text("#!/bin/sh\nexit 0\n")
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)

    dry = run("example-product", "CONTENT", *flags, "--dry-run")
    assert dry.returncode == 0, dry.stderr
    launch = _dry_run_argv(dry.stdout)
    assert launch[launch.index("--model") + 1] == "claude-m-1"
    result = run("example-product", "CONTENT", *flags)

    assert result.returncode == 0, result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    args = _codex_args(log)
    assert args[0] == "app-server"
    assert "--skill-path" in args and "--model" in args
    assert str(agent) in args[-1]
    assert args[args.index("--skill-path") + 1] == str(skill / "SKILL.md")
    assert str(companion) in args[-1]
    assert "Take the content-manager seat" in args[-1]
    assert str(product) in args
    assert "--settings" not in args
    watcher = run.watcher_argv()
    for flag, expected in (("--provider", "codex"), ("--reporter", "companion-self-answer"),
                           ("--artifact-path", str(product)), ("--document-stem", "CONTENT"),
                           ("--on-complete", str(hook))):
        assert watcher[watcher.index(flag) + 1] == expected
    assert "--pid" in watcher and "--log" in watcher
    assert "claude agents" not in result.stdout


def test_codex_self_answer_fallback_dry_run(run):
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    _, log = _codex_fixture(run)
    result = run("example-product", "PRD", "--provider", "codex", "--dry-run")
    assert result.returncode == 0, result.stderr
    args = _dry_run_argv(result.stdout)
    assert args[0] == "codex-skill"
    assert "--model" not in args
    assert not log.exists()
    assert not (run.root / "system/logs").exists()
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_gemini_self_answer_fallback_dry_run(run):
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    result = run("example-product", "PRD", "--provider", "gemini", "--dry-run")
    assert result.returncode == 0, result.stderr
    args = _dry_run_argv(result.stdout)
    assert args[0] == "agy"
    assert "--mode" in args and args[args.index("--mode") + 1] == "accept-edits"
    assert "--model" not in args
    assert args[args.index("--effort") + 1] == "high"
    assert "--output-format" in args and args[args.index("--output-format") + 1] == "stream-json"
    assert not (run.root / "system/logs").exists()
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_a_seated_gemini_run_carries_effort_high_and_reads_no_model_from_the_agent(run):
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "CONTENT")
    run.companion(product, "CONTENT", skill="product-content")
    run.skill_launcher("product-content", agent="content-manager")
    run.agent_file("content-manager")
    run.write_agent("content-manager", "---\nmodel: fable\n---\n# Content manager\n")

    result = run("example-product", "CONTENT", "--provider", "gemini", "--dry-run")
    assert result.returncode == 0, result.stderr
    args = _dry_run_argv(result.stdout)
    assert args[0] == "agy"
    assert "--model" not in args
    assert args[args.index("--effort") + 1] == "high"
    prompt = args[-1]
    assert args[-2] == "-p"
    assert "content-manager" in prompt
    assert "invoke the companion-self-answer skill" in prompt
    assert "`--surface Gemini`" in prompt


# --- the provider: the flag, else the variable, else this launcher's entry in .providers.toml ---

# The delivered text is the tracked template at the instance root, which no suite leans a live
# `.providers.toml` for: that file is untracked and absent from a fresh checkout.
_DELIVERED_PROVIDERS = (_CORE_DIR.parent / ".providers.toml.example").read_text()
_ENTRY = 'companion-self-answer = "claude"\n'


def _entry(value):
    """The delivered file with only `launchers.companion-self-answer` changed to `value`."""
    assert _ENTRY in _DELIVERED_PROVIDERS
    return _DELIVERED_PROVIDERS.replace(_ENTRY, f'companion-self-answer = "{value}"\n', 1)


def _instance_provider_file(run, text):
    """The instance's own `.providers.toml` — the launcher's cwd is the instance — holding
    `text` (removed when `None`). The launcher is the real one, so the file the reader reads is
    the instance's and nothing in a core copy."""
    file = run.root / ".providers.toml"
    if text is None:
        file.unlink(missing_ok=True)
    else:
        file.write_text(text)
    return _SCRIPT


def _publish_endpoint(run):
    """A published telemetry endpoint, so a dry run prints its `Telemetry:` line."""
    endpoint = run.root / "published-endpoint"
    endpoint.write_text("http://127.0.0.1:4318\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint)


def _document_to_answer(run):
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    return product


def test_unforced_dry_run_on_the_delivered_file_runs_claude(run):
    _document_to_answer(run)

    result = run("example-product", "PRD", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[:2] == ["claude", "--print"]


def test_forced_codex_dry_run_goes_to_codex(run):
    _codex_fixture(run)
    _document_to_answer(run)
    _publish_endpoint(run)

    result = run("example-product", "PRD", "--provider", "codex", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"
    assert "kensai.provider=codex" in result.stdout


def test_the_flag_wins_over_the_variable(run):
    _codex_fixture(run)
    _document_to_answer(run)
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "gemini"

    spaced = run("example-product", "PRD", "--provider", "codex", "--dry-run")
    joined = run("example-product", "PRD", "--provider=codex", "--dry-run")

    assert spaced.returncode == 0 and joined.returncode == 0, spaced.stderr + joined.stderr
    assert _dry_run_argv(spaced.stdout)[0] == "codex-skill"
    assert _dry_run_argv(joined.stdout)[0] == "codex-skill"


def test_the_variable_forces_when_no_flag_is_given(run):
    _codex_fixture(run)
    _document_to_answer(run)
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = run("example-product", "PRD", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"


def test_the_entry_decides_an_unforced_launch(run):
    _codex_fixture(run)
    _document_to_answer(run)
    _publish_endpoint(run)
    script = _instance_provider_file(run, _entry("codex"))

    result = run("example-product", "PRD", "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"
    assert "kensai.provider=codex" in result.stdout


def test_a_forced_launch_on_a_copy_without_the_entry_goes_to_codex(run):
    _codex_fixture(run)
    _document_to_answer(run)
    without_entry = _DELIVERED_PROVIDERS.replace(_ENTRY, "", 1)
    assert without_entry != _DELIVERED_PROVIDERS

    for text in (without_entry, None):
        script = _instance_provider_file(run, text)
        result = run("example-product", "PRD", "--provider", "codex", "--dry-run", script=script)

        assert result.returncode == 0, result.stderr
        assert _dry_run_argv(result.stdout)[0] == "codex-skill"


def test_an_empty_variable_is_unforced(run):
    _document_to_answer(run)
    run.env["KENSAIAPP_AGENT_PROVIDER"] = ""

    result = run("example-product", "PRD", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[:2] == ["claude", "--print"]


@pytest.mark.parametrize("contents", [b"[launchers\n", b"\xff", None,
                                       b'[launchers]\ncompanion-self-answer = "grok"\n'],
                         ids=["malformed-toml", "non-utf8", "directory", "unknown-entry"])
@pytest.mark.parametrize("force_channel", ["flag", "environment"])
def test_a_force_bypasses_an_unreadable_or_invalid_provider_file(
    run, contents, force_channel
):
    """CP-296: both force channels reach Codex regardless of the instance file's condition."""
    _codex_fixture(run)
    _document_to_answer(run)
    script = _instance_provider_file(run, None)
    path = run.root / ".providers.toml"
    if contents is None:
        path.mkdir()
    else:
        path.write_bytes(contents)
    if force_channel == "environment":
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    args = ("--provider", "codex") if force_channel == "flag" else ()

    result = run("example-product", "PRD", *args, "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[0] == "codex-skill"
    assert ".providers.toml" not in result.stderr


def test_claude_overrides_inherited_codex(run):
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    result = run("example-product", "PRD", "--provider", "claude")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv()[:4] == _PRINT_RUN_HEAD


@pytest.mark.parametrize(
    "flags, refusal",
    [
        (("--provider",), "--provider needs claude, codex, gemini, hf or ollama"),
        (
            ("--provider", "unknown"),
            "provider must be claude, codex, gemini, hf or ollama (got 'unknown')",
        ),
    ],
)
def test_bad_provider_is_refused(run, flags, refusal):
    result = run("example-product", "PRD", *flags)
    assert result.returncode != 0
    assert refusal in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


@pytest.mark.parametrize("failed", [False, True])
def test_codex_completion_reaches_real_chain_hook_with_provider(run, failed):
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    _codex_fixture(run)
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"
    if failed:
        stub = run.root / "bin/codex"
        stub.write_text(stub.read_text().replace("'status': 'completed'", "'status': 'failed'"))
    hook_log = run.root / "hook-result"
    run.env["TEST_HOOK_RESULT"] = str(hook_log)
    hook = run.root / "completion-hook"
    hook.write_text('#!/bin/sh\n'
                    'printf "%s:%s" "$KENSAIAPP_AGENT_PROVIDER" "$1" > "$TEST_HOOK_RESULT"\n')
    hook.chmod(0o755)
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)

    result = run("example-product", "PRD")

    assert result.returncode == 0, result.stderr
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not hook_log.exists():
        time.sleep(0.05)
    assert hook_log.exists(), result.stdout
    assert hook_log.read_text() == ("codex:failed" if failed else "codex:completed")
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_claude_completion_reaches_real_chain_hook_with_provider(run):
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER")
    hook_log = run.root / "hook-result"
    run.env["TEST_HOOK_RESULT"] = str(hook_log)
    hook = run.root / "completion-hook"
    hook.write_text('#!/bin/sh\n'
                    'printf "%s:%s" "$KENSAIAPP_AGENT_PROVIDER" "$1" > "$TEST_HOOK_RESULT"\n')
    hook.chmod(0o755)
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)

    result = run("example-product", "PRD")

    assert result.returncode == 0, result.stderr
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not hook_log.exists():
        time.sleep(0.05)
    assert hook_log.exists(), result.stdout
    assert hook_log.read_text() == "claude:completed"


# --- every run starts at `--effort high` — both providers, every launch form -----------------


def _carries_effort_high(argv):
    """Parsed, never grepped: the run's paths can carry a branch name such as
    `…-pass-effort-high`, so a substring match on `effort` passes before the change."""
    return argv.count("--effort") == 1 and argv[argv.index("--effort") + 1] == "high"


def _codex_dry_run_argv(result):
    assert result.returncode == 0, result.stderr
    return _dry_run_argv(result.stdout)


def _codex_carries_effort_high(argv):
    """Codex's own spelling of the launcher's `--effort high`: one reasoning setting, `high`."""
    settings = [arg for arg in argv if arg.startswith("model_reasoning_effort=")]
    return settings == ['model_reasoning_effort="high"']


def test_a_seated_claude_run_carries_effort_high(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert _carries_effort_high(argv), argv


def _no_skill(run, product):
    run.companion(product, "fdr", skill=None)


def _seat_without_an_agent_file(run, product):
    run.companion(product, "fdr", skill="some-skill")
    run.skill_launcher("some-skill", agent="principal-architect")


def _posture_free_agent(run, product):
    run.companion(product, "fdr", skill="product-sdd")
    run.skill_launcher("product-sdd", agent="delegate")
    run.agent_file("delegate", loader=False)


@pytest.mark.parametrize(
    "setup", [_no_skill, _seat_without_an_agent_file, _posture_free_agent],
    ids=["no-skill-named", "no-agent-file", "posture-free-agent"],
)
def test_every_seatless_claude_run_carries_effort_high(run, setup):
    product = run.project("example-product")
    run.document(product, "fdr")
    setup(run, product)

    if setup is _seat_without_an_agent_file:
        # A real launch, read off the stubbed `claude`: this cause's fallback line puts an em dash
        # into the prompt, and the dry run's `printf %q` splits its bytes under the fixture's
        # locale, so the dry-run stdout is not decodable here.
        result = run("example-product", "fdr")
        assert result.returncode == 0, result.stderr
        assert "no agent file for it in any group" in result.stdout
        argv = run.launched_argv()
    else:
        result = run("example-product", "fdr", "--dry-run")
        assert result.returncode == 0, result.stderr
        argv = _dry_run_argv(result.stdout)
    assert "--model" not in argv
    # A token check — the pin delivery's `--agents` holds `--agent` as a substring.
    assert "--agent" not in argv
    assert _carries_effort_high(argv), argv


def test_a_seat_without_an_agent_file_dry_run_carries_effort_high(run):
    """The spec's own example for this cause is a `--dry-run`: the fallback prompt carries an em
    dash, and the printed command still parses to no `--model`, no `--agent`, and one
    `--effort high`."""
    product = run.project("example-product")
    run.document(product, "fdr")
    _seat_without_an_agent_file(run, product)

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    announced = result.stdout.split("DRY RUN — would launch:", 1)[0]
    assert "no agent file for it in any group" in announced
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    argv = _dry_run_argv(result.stdout)
    assert "--model" not in argv
    assert "--agent" not in argv
    assert _carries_effort_high(argv), argv


def test_a_seatless_codex_run_carries_effort_high(run):
    product = run.project("example-product")
    run.document(product, "PRD")
    run.companion(product, "PRD")
    _codex_fixture(run)

    argv = _codex_dry_run_argv(run("example-product", "PRD", "--provider", "codex", "--dry-run"))

    assert "--model" not in argv
    assert _codex_carries_effort_high(argv), argv


def test_a_fable_agent_file_gives_a_codex_run_no_model_and_effort_high(run):
    product = run.project("example-product")
    run.document(product, "CONTENT")
    run.companion(product, "CONTENT", skill="product-content")
    run.skill_launcher("product-content", agent="content-manager")
    run.agent_file("content-manager")
    run.write_agent("content-manager", "---\nmodel: fable\n---\n# Content manager\n")
    _codex_fixture(run)

    argv = _codex_dry_run_argv(run("example-product", "CONTENT", "--provider", "codex", "--dry-run"))

    assert "--model" not in argv
    assert _codex_carries_effort_high(argv), argv


def test_a_callers_effort_is_refused_as_an_unknown_argument(run):
    """The level is the launcher's, not a caller's: the argument loop's catch-all arm refuses
    `--effort` as it refuses any flag it does not know, and nothing launches."""
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr")

    result = run("example-product", "fdr", "--effort", "low", "--dry-run")

    assert result.returncode != 0
    assert "companion-self-answer: unknown argument: --effort" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


# --- the run's model is the producing skill's (CP-176, CP-177) ------------------------------------

_PROVIDERS = ["claude", "codex", "gemini"]


def _models(argv):
    return [argv[i + 1] for i, a in enumerate(argv) if a == "--model"]


def _effort_levels(argv, provider):
    if provider == "codex":
        return [a.split('"')[1] for a in argv if a.startswith("model_reasoning_effort=")]
    return [argv[i + 1] for i, a in enumerate(argv) if a == "--effort"]


def _producer(run, provider_files=("claude", "codex", "gemini"), effort=None):
    """A `example-product` FDR companion whose producer `product-fdr` declares its seat and carries an
    intelligence file for each named provider. Returns the producer's skill dir."""
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    declaration = _skill_declaration(run, "product-fdr", agent="principal-pm", group="principal-pm")
    run.agent_file("principal-pm")
    for provider in provider_files:
        _intelligence(declaration.parent, provider, "claude-m-1", effort)
    return declaration.parent


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_the_run_takes_the_producers_model_on_every_provider(run, provider):
    _producer(run)

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _models(_dry_run_argv(result.stdout)) == ["claude-m-1"]


def test_a_real_launch_takes_the_producers_model(run):
    _producer(run)

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    assert _models(run.launched_argv()) == ["claude-m-1"]


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_the_effort_is_high_whatever_the_producer_declares(run, provider):
    _producer(run, effort="low")

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _effort_levels(_dry_run_argv(result.stdout), provider) == ["high"]


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_a_producer_folder_without_the_providers_file_is_refused_naming_the_path(run, mode):
    producer_dir = _producer(run, provider_files=("claude",))

    dry_run = ["--dry-run"] if mode == "--dry-run" else []
    result = run("example-product", "fdr", "--provider", "codex", *dry_run)

    assert result.returncode != 0
    assert str(producer_dir / "intelligence" / "codex.md") in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    assert not (run.root / "codex-argv.json").exists()


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_a_malformed_producer_intelligence_file_is_refused_naming_it(run, mode):
    producer_dir = _producer(run, provider_files=())
    path = _intelligence(producer_dir, "claude", text="**Model:** two words\n")

    result = run("example-product", "fdr", *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode == 1  # CP-170: a malformed file is refused with exit status 1
    assert str(path) in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def _no_companion(run, product):
    pass


def _companion_with_no_rerun_line(run, product):
    run.companion(product, "fdr", skill=None)


def _companion_naming_a_skill_that_resolves_nowhere(run, product):
    run.companion(product, "fdr", skill="nobody-launches-this")


def _seat_with_no_agent_file(run, product):
    run.companion(product, "fdr", skill="some-skill")
    run.skill_launcher("some-skill", agent="principal-architect")


_UNDERIVABLE = [
    _no_companion,
    _companion_with_no_rerun_line,
    _companion_naming_a_skill_that_resolves_nowhere,
    _seat_with_no_agent_file,
]


@pytest.mark.parametrize("provider", _PROVIDERS)
@pytest.mark.parametrize("setup", _UNDERIVABLE, ids=lambda f: f.__name__.lstrip("_"))
def test_an_underivable_producer_launches_with_no_model_at_effort_high(run, setup, provider):
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "fdr")
    setup(run, product)

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert _models(argv) == []
    assert _effort_levels(argv, provider) == ["high"]
    for tier_model in ("opus", "gpt-5.6-sol", "gemini-3.1-pro-high"):
        assert tier_model not in argv


def _producer_with_no_intelligence_folder(run, product):
    run.companion(product, "fdr", skill="product-fdr")
    _skill_declaration(run, "product-fdr", agent="principal-pm", group="principal-pm")
    run.agent_file("principal-pm")


_FALLBACKS = _UNDERIVABLE + [_producer_with_no_intelligence_folder]


@pytest.mark.parametrize("provider", _PROVIDERS)
@pytest.mark.parametrize("setup", _FALLBACKS, ids=lambda f: f.__name__.lstrip("_"))
def test_no_run_is_ever_given_model_opus(run, setup, provider):
    """Every fallback case — no companion, no re-run line, a producer that resolves nowhere, a seat
    with no agent file, a producer with no intelligence folder — launches with no `--model` at all.
    The bare `--model opus` that used to stand in for a seatless run is gone, and so is the tier
    the agent-file read gave a seated one: no argument is `opus`, no `--model` or `--model-tier`
    is passed."""
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "fdr")
    setup(run, product)

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert "--model" not in argv
    assert "--model-tier" not in argv
    assert "opus" not in argv


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_a_producer_with_no_intelligence_folder_launches_with_no_model(run, provider):
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "fdr")
    run.companion(product, "fdr", skill="product-fdr")
    _skill_declaration(run, "product-fdr", agent="principal-pm", group="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert _models(argv) == []
    assert _effort_levels(argv, provider) == ["high"]


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_a_producer_that_has_only_a_launcher_folder_still_resolves_its_intelligence(run, provider):
    """A producer with a launcher folder and no launcher.md still resolves its intelligence from its
    own skill folder."""
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "sdd")
    run.companion(product, "sdd", skill="product-sdd")
    run.skill_launcher("product-sdd", agent="cpo")
    run.agent_file("cpo")
    sdd_dir = run.root / ".claude" / "skills" / "product-sdd"
    sdd_dir.mkdir(parents=True)
    (sdd_dir / "SKILL.md").write_text("---\nname: product-sdd\n---\n")
    _intelligence(sdd_dir, provider, "claude-m-sdd-1", "medium")

    result = run("example-product", "sdd", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert _models(argv) == ["claude-m-sdd-1"]
    assert _effort_levels(argv, provider) == ["high"]


def test_untagged_sdd_items_use_the_shipped_cto_declaration(run):
    """The shipped `product-sdd` declaration names `cto`, so an SDD companion whose open items carry
    no `Seat:` is answered in one run under that seat (CP-403)."""
    shutil.copy(_REPO / "skills" / "cto" / ".claude" / "skills" / "product-sdd" / "launcher.md",
                _skill_declaration(run, "product-sdd", group="cto"))
    product = run.project("example-product")
    run.document(product, "sdd")
    companion = product / "docs" / "sdd_open_issues.md"
    companion.write_text(
        _items_text([("1.1", None, False), ("1.2", None, False)])
        .replace("`fdr.md`", "`SDD.md`").replace("`product-fdr`", "`product-sdd`"))
    run.agent_file("cto")

    result = run("example-product", "sdd", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "Run 1 of" not in result.stdout
    assert "Seat:      cto (from " in result.stdout
    assert _agent_of(_dry_run_argv(result.stdout)) == "cto"
    assert result.stdout.count("DRY RUN") == 1


# --- the run's provenance (CP-218, CP-219, CP-225, CP-226, CP-227, CP-229, CP-230) ------------


def test_the_instrument_run_call_carries_the_four_provenance_keys():
    assert_instrument_run_call_carries_provenance(_SCRIPT)


def _stamped_dry_run(run, *flags):
    """A dry run with a published endpoint, so `instrument_run` prints what it stamps."""
    endpoint_file = run.root / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    result = run("example-product", "fdr", *flags, "--dry-run")
    assert result.returncode == 0, result.stderr
    return result


def test_a_producer_with_a_claude_file_stamps_its_model_effort_high_and_source_intelligence(run):
    """The run goes at the producer's model and at `high` — the file's own effort, `low` here, is
    discarded (CP-225) — and the stamp carries exactly the pair the run is handed (CP-218)."""
    producer_dir = _producer(run, provider_files=("claude",), effort="low")

    result = _stamped_dry_run(run)

    assert_provenance_stamped(
        result.stdout, provider="claude", model="claude-m-1", effort="high", source="intelligence"
    )
    argv = _dry_run_argv(result.stdout)
    assert _models(argv) == ["claude-m-1"]
    assert _effort_levels(argv, "claude") == ["high"]
    assert f"Intelligence: {producer_dir}/intelligence/claude.md" in result.stdout


def test_a_producer_with_no_intelligence_folder_stamps_effort_high_source_default_and_no_model(
    run,
):
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "fdr")
    _producer_with_no_intelligence_folder(run, product)

    result = _stamped_dry_run(run)

    assert_provenance_stamped(result.stdout, provider="claude", effort="high", source="default")
    argv = _dry_run_argv(result.stdout)
    assert "--model" not in argv
    assert _effort_levels(argv, "claude") == ["high"]
    assert (
        "Intelligence: none — product-fdr has no intelligence/ folder; provider default model"
        in result.stdout
    )


@pytest.mark.parametrize("setup", _UNDERIVABLE, ids=lambda f: f.__name__.lstrip("_"))
def test_no_derivable_producer_stamps_the_same_as_no_folder(run, setup):
    _codex_fixture(run)
    product = run.project("example-product")
    run.document(product, "fdr")
    setup(run, product)

    result = _stamped_dry_run(run)

    assert_provenance_stamped(result.stdout, provider="claude", effort="high", source="default")
    assert "--model" not in _dry_run_argv(result.stdout)
    assert "Intelligence: none — no producing skill derivable; provider default model" in (
        result.stdout
    )


def test_the_project_document_and_product_pairs_are_still_stamped_beside_the_new_keys(run):
    """CP-227: the pairs stamped before this change keep their values and their order, and the
    provenance pairs follow them."""
    _producer(run, provider_files=("claude",))

    result = _stamped_dry_run(run)

    pairs = dict(telemetry_pairs(result.stdout))
    assert (pairs["project"], pairs["product"], pairs["document"]) == ("example-product", "thing", "fdr")
    assert_provenance_stamped(
        result.stdout,
        provider="claude",
        model="claude-m-1",
        effort="high",
        source="intelligence",
        after=("project", "product", "document"),
    )


def test_a_producer_whose_intelligence_folder_lacks_the_providers_file_is_refused_before_any_spawn(
    run,
):
    """The refusal is the reader's own words, byte for byte behind the launcher's prefix, and it
    comes before the run is tagged or spawned — nothing is stamped and nothing launches."""
    producer_dir = _producer(run, provider_files=("codex",))
    endpoint_file = run.root / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    reader = subprocess.run(
        ["python3", str(_CORE_DIR / "tools" / "intelligence.py"),
         "--skill-dir", str(producer_dir), "--provider", "claude"],
        capture_output=True, text=True,
    )
    assert reader.returncode == 4, reader.stderr

    result = run("example-product", "fdr")

    assert result.returncode == 1
    assert result.stderr == f"companion-self-answer: {reader.stderr}"
    assert "Telemetry:" not in result.stdout
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_the_effort_handed_and_the_effort_stamped_are_the_same_value_on_every_provider(
    run, provider
):
    """One variable feeds all three provider branches and the stamp (CP-218), and the provider
    stamped is the one the run goes through (CP-219)."""
    _producer(run, effort="low")

    result = _stamped_dry_run(run, "--provider", provider)

    stamped = dict(telemetry_pairs(result.stdout))
    assert stamped["provider"] == provider
    assert _effort_levels(_dry_run_argv(result.stdout), provider) == [stamped["effort"]] == ["high"]


def test_a_provider_taken_from_the_environment_is_the_provider_stamped(run):
    """`--provider` is absent, so the run goes through `KENSAIAPP_AGENT_PROVIDER` — and that is
    the provider the stamp names, with that provider's own file (CP-219)."""
    _producer(run, provider_files=("codex",))
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = _stamped_dry_run(run)

    assert_provenance_stamped(
        result.stdout, provider="codex", model="claude-m-1", effort="high", source="intelligence"
    )


def test_a_launch_records_its_run_and_watcher_for_the_engine_that_named_a_file(run):
    run.project("example-product")
    companion = _project_home_companion(run, "example-product", "agari", skill="project-agari")
    (companion.parent / "agari.md").write_text("# Agari\n")
    run.skill_launcher("project-agari", agent="cpo")
    run.agent_file("cpo")
    identity = run.root / "launch.identity.json"
    run.env["DETACHED_RUN_IDENTITY_FILE"] = str(identity)

    result = run("example-product", "Agari")

    assert result.returncode == 0, result.stderr
    assert_launch_recorded_its_identity(result.stdout, identity)


# --- a companion answered seat by seat — items group by the seat their `Seat:` tag resolves to --
#   Each open item may carry `- **Seat:** <seat>`. The launcher reads the open items through
#   `core/tools/companion_items.py`, resolves every tag with the checks it already holds for the
#   producer's seat, and starts one run per distinct seat, one after another. A single group is
#   today's launch.

_SLOT_HEADER = (
    "> Companion to `fdr.md`.\n"
    ">\n"
    "> **Answer inline** — fill each **Answer** / **Your call** slot — **commit this file**, then\n"
    "> re-run `product-fdr`.\n"
)
_OPEN_SLOT = "<the owner fills this in>"


def _items_text(items):
    """`items`: (number, tag or None, filled) — a companion body, one `### ` block per item."""
    blocks = []
    for number, tag, filled in items:
        block = f"### {number} A question\n"
        if tag is not None:
            block += f"- **Seat:** {tag}\n"
        block += f"- **Answer:** {'confirm' if filled else _OPEN_SLOT}\n"
        blocks.append(block)
    return (f"# fdr open issues\n\n{_SLOT_HEADER}\n---\n\n## 1. Open issues\n\n"
            + "\n".join(blocks))


def _seat_fixture(run, items, producer="cto", agents=("cpo", "cdo"), product_path="products/thing"):
    """A `example-product` FDR whose companion carries `items`, produced by `product-fdr` in the `producer`
    seat, with an agent file and loader for the producer and for each of `agents`, and an
    intelligence file for every provider. Returns the companion's path."""
    _codex_fixture(run)
    product = run.project("example-product", product_path)
    run.document(product, "fdr")
    companion = product / "docs" / "fdr_open_issues.md"
    companion.write_text(_items_text(items))
    declaration = _skill_declaration(run, "product-fdr", agent=producer, group="producer")
    for seat in (producer, *agents):
        run.agent_file(seat)
    for provider in _PROVIDERS:
        _intelligence(declaration.parent, provider, "claude-m-1")
    return companion


def _run_entries(stdout):
    """The per-run entries of a multi-run dry run, in the order printed: each opens with
    `Run <k> of <n>: seat <seat> — items <n>, <n>`, then a `Why:` line, then the provider
    command."""
    entries, current = [], None
    for line in stdout.splitlines():
        opened = re.match(r"Run (\d+) of (\d+): seat (\S+) — items (.+)$", line)
        if opened:
            current = {"index": int(opened[1]), "of": int(opened[2]), "seat": opened[3],
                       "items": opened[4].split(", "), "reason": "", "lines": []}
            entries.append(current)
        elif current is not None and line.startswith("  Why: "):
            current["reason"] = line[len("  Why: "):]
        elif current is not None:
            current["lines"].append(line)
    for entry in entries:
        entry["argv"] = _dry_run_argv("\n".join(entry["lines"]))
    return entries


def _agent_of(argv):
    return argv[argv.index("--agent") + 1] if "--agent" in argv else None


def _prompt_in(argv):
    """The prompt a dry-run command carries: the one argument holding the fixed task sentence."""
    return next(a for a in argv if "invoke the companion-self-answer skill" in a)


def _one_run_dry(run, *flags):
    result = run("example-product", "fdr", "--dry-run", *flags)
    assert result.returncode == 0, result.stderr
    assert "Run 1 of" not in result.stdout, result.stdout
    return result, _dry_run_argv(result.stdout)


# What the launcher printed for an untagged companion before this change — captured from the
# launcher at `main` (329a26a5b) on the fixture below: a producer `principal-pm`, a document
# and a companion holding two open items and no `Seat:` field. Only what varies between runs is
# a placeholder: the fixture root, the pin directory and its instance hash, and the session id.
# The provider command carries this repository's whole agent set as one `--agents` JSON value,
# which is not the launcher's to pin, so that value alone is compared by shape.
_MAIN_UNTAGGED_DRY_RUN_HEAD = (
    "Pin: <PIN> (inherited)\n"
    "Document:  <ROOT>/products/thing/docs/fdr.md\n"
    "Companion: present — <ROOT>/products/thing/docs/fdr_open_issues.md\n"
    "Intelligence: none — no producing skill derivable; provider default model\n"
    "Seat:      principal-pm (from <ROOT>/fixture_launchers/product-fdr/launcher.sh)\n"
    "          (no published telemetry endpoint at <ROOT>/no-instrument-endpoint — run "
    "uninstrumented)\n"
    "DRY RUN — would launch:\n"
    "  env CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1 BASH_DEFAULT_TIMEOUT_MS=600000 "
    "BASH_MAX_TIMEOUT_MS=21600000 CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude --print "
    "--output-format stream-json --verbose --session-id <SESSION> --agent principal-pm "
    "--effort high --permission-mode auto --permission-prompts none 'invoke the "
    "companion-self-answer skill for the companion at "
    "<ROOT>/products/thing/docs/fdr_open_issues.md. Pass `--reasoning-effort \"high\"` to the "
    "builder; the launch already resolved this value.' --setting-sources user --plugin-dir "
    "<PIN>/instances/<HASH>/plugins/c989edf18246e9c8 --settings "
    "<PIN>/instances/<HASH>/settings.json"
)


def test_untagged_dry_run_matches_main_output(run):
    product = run.project("example-product")
    run.document(product, "fdr")
    (product / "docs" / "fdr_open_issues.md").write_text(
        _items_text([("1.1", None, False), ("1.2", None, False)]))
    run.skill_launcher("product-fdr", agent="principal-pm")
    run.agent_file("principal-pm")

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    out = result.stdout.replace(str(run.root), "<ROOT>")
    pin = re.search(r"^Pin: (.*) \(inherited\)$", out, flags=re.M)[1]
    out = out.replace(pin, "<PIN>")
    out = re.sub(r"--session-id \S+", "--session-id <SESSION>", out)
    out = re.sub(r"instances/[0-9a-f]+/", "instances/<HASH>/", out)
    head, agents, tail = out.partition(" --agents '")
    assert head == _MAIN_UNTAGGED_DRY_RUN_HEAD, out
    assert agents and tail.endswith("}}' --add-dir=<PIN>\n"), tail[-80:]
    assert "Answer only these items" not in out and "Run 1 of" not in out


def test_seat_groups_keep_first_item_order_and_only_their_items(run):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "cpo", False), ("2.1", "cdo", False),
                        ("2.2", "cpo", False)])

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    entries = _run_entries(result.stdout)
    assert [(e["index"], e["of"], e["seat"], e["items"]) for e in entries] == [
        (1, 3, "cto", ["1.1"]), (2, 3, "cpo", ["1.2", "2.2"]), (3, 3, "cdo", ["2.1"])]
    assert [_agent_of(e["argv"]) for e in entries] == ["cto", "cpo", "cdo"]
    assert [e["reason"] != "" for e in entries] == [True, True, True]
    for entry in entries:
        assert f"Answer only these items: {', '.join(entry['items'])}." in _prompt_in(entry["argv"])
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_unknown_tag_keeps_item_and_names_unavailable_seat(run):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "cfo", False)])

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    entries = _run_entries(result.stdout)
    assert [(e["seat"], e["items"]) for e in entries] == [("cto", ["1.1"]), ("seatless", ["1.2"])]
    seatless = entries[1]["argv"]
    assert _agent_of(seatless) is None
    assert "Answer only these items: 1.2." in _prompt_in(seatless)
    assert "'cfo' seat" in _prompt_in(seatless)
    assert "'cfo'" not in _prompt_in(entries[0]["argv"])


def test_a_launch_whose_every_item_names_an_unavailable_seat_runs_seatless_and_says_so(run):
    companion = _seat_fixture(run, [("1.1", "cfo", False), ("1.2", "cfo", False)])

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) is None
    prompt = _prompt_in(argv)
    assert prompt.startswith(f"invoke the companion-self-answer skill for the companion at "
                             f"{companion}.")
    assert "'cfo' seat" in prompt and prompt.count("'cfo' seat") == 1
    assert "Answer only these items" not in prompt


def test_tag_case_uses_agent_file_spelling(run):
    _seat_fixture(run, [("1.1", "CPO", False)])

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) == "cpo"


def test_posture_free_tag_is_answered_seatless(run):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "delegate", False)])
    run.write_agent("delegate", "# delegate\n")   # an agent file and no loader

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    entries = _run_entries(result.stdout)
    assert [(e["seat"], e["items"]) for e in entries] == [("cto", ["1.1"]), ("seatless", ["1.2"])]
    assert _agent_of(entries[1]["argv"]) is None
    assert "delegate" not in _prompt_in(entries[1]["argv"])


def test_tagged_and_untagged_same_seat_merge_into_one_run(run):
    companion = _seat_fixture(run, [("1.1", "cto", False), ("1.2", None, False)])

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) == "cto"
    assert _prompt_in(argv) == _launched_prompt(companion)


def test_single_tagged_group_uses_that_seat_and_original_prompt(run):
    companion = _seat_fixture(run, [("1.1", "cpo", False), ("1.2", "cpo", False)])

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) == "cpo"
    assert _prompt_in(argv) == _launched_prompt(companion)
    assert "Seat:      cpo" in result.stdout


def test_absent_or_fully_answered_companion_uses_original_launch(run):
    # An absent companion is one run, as before.
    product = run.project("example-product")
    run.document(product, "fdr")
    absent, argv = _one_run_dry(run)
    assert "Companion: absent" in absent.stdout
    assert "Seat:      none derivable" in absent.stdout
    assert _agent_of(argv) is None


def test_answered_tagged_items_never_create_a_group(run):
    companion = _seat_fixture(run, [("1.1", "cpo", True), ("1.2", None, False)])

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) == "cto"
    assert _prompt_in(argv) == _launched_prompt(companion)


def test_a_fully_answered_companion_launches_once_under_the_producer(run):
    companion = _seat_fixture(run, [("1.1", "cpo", True), ("1.2", "cdo", True)])

    result, argv = _one_run_dry(run)

    assert _agent_of(argv) == "cto"
    assert _prompt_in(argv) == _launched_prompt(companion)


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_every_seat_uses_one_provider_producer_model_and_high_effort(run, provider):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "cpo", False), ("2.1", "cdo", False)])

    result = run("example-product", "fdr", "--provider", provider, "--dry-run")

    assert result.returncode == 0, result.stderr
    entries = _run_entries(result.stdout)
    assert [e["seat"] for e in entries] == ["cto", "cpo", "cdo"]
    for entry in entries:
        assert _models(entry["argv"]) == ["claude-m-1"]
        assert _effort_levels(entry["argv"], provider) == ["high"]
        prompt = entry["argv"][-1] if provider != "claude" else _prompt_in(entry["argv"])
        assert f"Answer only these items: {', '.join(entry['items'])}." in prompt
        if provider == "claude":
            assert _agent_of(entry["argv"]) == entry["seat"]
        elif provider == "codex":
            assert f"Take the {entry['seat']} seat" in prompt
            assert "--skill-name" in entry["argv"]  # the skill the run is granted
        else:
            assert f"You are running as the {entry['seat']} agent" in prompt


@pytest.mark.parametrize("flag, variable, expected", [
    (["--provider", "codex"], "gemini", "codex"),
    ([], "gemini", "gemini"),
])
def test_multi_run_provider_precedence_is_flag_then_environment(run, flag, variable, expected):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "cpo", False)])
    run.env["KENSAIAPP_AGENT_PROVIDER"] = variable

    result = run("example-product", "fdr", *flag, "--dry-run")

    assert result.returncode == 0, result.stderr
    entries = _run_entries(result.stdout)
    assert len(entries) == 2
    expected_heads = {"codex": ("codex", "codex-skill"), "gemini": ("agy",)}[expected]
    assert [e["argv"][0] in expected_heads for e in entries] == [True, True]


def test_multi_group_dry_run_starts_nothing(run):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "cpo", False)])

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert [e["seat"] for e in _run_entries(result.stdout)] == ["cto", "cpo"]
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    assert not (run.root / "system" / "logs").exists(), "a dry run wrote a plan or a log"


def test_item_list_prompt_matches_skill_input_literal(run):
    skill = (_CORE_DIR.parent / "skills" / "companion" / ".claude" / "skills" / "companion-self-answer" / "SKILL.md")
    quoted = re.search(r"^> `(Answer only these items: <n>, <n>\.)`$", skill.read_text(),
                       flags=re.M)
    assert quoted, "the skill quotes its item-list sentence in § Input"
    companion = _seat_fixture(run, [("1.1", None, False), ("1.2", "cpo", False),
                                    ("2.1", "cdo", False), ("2.2", "cpo", False)])

    result = run("example-product", "fdr", "--dry-run")

    entries = _run_entries(result.stdout)
    cpo = next(e for e in entries if e["seat"] == "cpo")
    sentence = quoted[1].replace("<n>, <n>", ", ".join(cpo["items"]))
    base = f"invoke the companion-self-answer skill for the companion at {companion}."
    assert _prompt_in(cpo["argv"]) == _launched_prompt(companion).replace(
        base, f"{base} {sentence}")


# --- the runs of one launch go one after another, live — and the caller hears once -----------
#   A multi-group launch hands its commands to one detached sequence runner. These cases drive the
#   real launcher, the real sequence runner and (where the callback is the subject) the real
#   watcher, with a provider stub that records when each run started and ended, and can be held
#   alive until the case releases it.

SEAT_STUB = """#!/usr/bin/env python3
import json, os, sys, time
record_dir = os.environ.get("SEAT_RECORD_DIR")
if not record_dir:
    sys.exit(0)
argv = sys.argv[1:]
seat = argv[argv.index("--agent") + 1] if "--agent" in argv else "seatless"
path = os.path.join(record_dir, seat + ".json")
record = {"argv": argv, "pid": os.getpid(), "start": time.time(), "end": None}


def save():
    with open(path + ".tmp", "w") as fh:
        json.dump(record, fh)
    os.replace(path + ".tmp", path)


save()
time.sleep(0.3)
failing = seat in os.environ.get("SEAT_STUB_FAIL", "").split(",")
if not failing:
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                      "result": "ok"}), flush=True)
if seat == os.environ.get("SEAT_STUB_HOLD"):
    release = os.environ["SEAT_STUB_RELEASE_FILE"]
    deadline = time.time() + 120
    while not os.path.exists(release) and time.time() < deadline:
        time.sleep(0.05)
record["end"] = time.time()
save()
sys.exit(1 if failing else 0)
"""

COUNTING_WATCHER_STUB = """import json, os, sys
with open(os.environ["WATCHER_COUNT_LOG"], "a") as fh:
    fh.write(json.dumps(sys.argv[1:]) + "\\n")
"""

_THREE_SEATS = [("1.1", None, False), ("1.2", "cpo", False), ("2.1", "cdo", False)]


def _seat_stub(run, **env):
    """Replace the fixture's provider stub with one that records each run, and return the
    directory it records into (one `<seat>.json` per run: argv, pid, start, end)."""
    records = run.root / "seat_records"
    records.mkdir()
    claude = run.root / "bin" / "claude"
    claude.unlink()
    claude.write_text(SEAT_STUB)
    claude.chmod(0o755)
    run.env["SEAT_RECORD_DIR"] = str(records)
    run.env.update(env)
    return records


def _records(records):
    return {p.stem: json.loads(p.read_text()) for p in records.glob("*.json")}


def _wait_for(predicate, timeout=60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    return predicate()


def _all_ended(records, count):
    found = _records(records)
    return found if len(found) == count and all(r["end"] for r in found.values()) else None


def _record_pid(stdout):
    return next(json.loads(line) for line in stdout.splitlines() if line.startswith("{"))["pid"]


def _hook(run):
    """A completion hook that appends `<provider>:<outcome>` per call, for the real watcher."""
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER")
    calls = run.root / "hook-calls"
    run.env["TEST_HOOK_RESULT"] = str(calls)
    hook = run.root / "completion-hook"
    hook.write_text(
        '#!/bin/sh\n'
        'printf "%s:%s\\n" "$KENSAIAPP_AGENT_PROVIDER" "$1" >> "$TEST_HOOK_RESULT"\n')
    hook.chmod(0o755)
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)
    return calls


def _calls(path):
    return path.read_text().splitlines() if path.exists() else []


def test_live_groups_do_not_overlap_after_earlier_failure(run):
    _seat_fixture(run, _THREE_SEATS)
    release = run.root / "release"
    records = _seat_stub(run, SEAT_STUB_FAIL="cto", SEAT_STUB_HOLD="cto",
                         SEAT_STUB_RELEASE_FILE=str(release))

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    assert _wait_for(lambda: "cto" in _records(records)), "run 1 never started"
    assert set(_records(records)) == {"cto"} and _records(records)["cto"]["end"] is None, (
        "the launcher did not return while run 1 was still going")
    release.touch()
    done = _wait_for(lambda: _all_ended(records, 3))
    assert done, _records(records)
    ordered = sorted(done.items(), key=lambda item: item[1]["start"])
    assert [seat for seat, _ in ordered] == ["cto", "cpo", "cdo"]
    for (_, earlier), (_, later) in zip(ordered, ordered[1:]):
        assert earlier["end"] <= later["start"]


def test_watcher_is_started_once_for_sequence_completion(run):
    _seat_fixture(run, _THREE_SEATS)
    _seat_stub(run)
    counting = run.root / "counting_watcher.py"
    counting.write_text(COUNTING_WATCHER_STUB)
    run.env["LAUNCH_COMPANION_SELF_ANSWER_WATCHER"] = str(counting)
    log = run.root / "watcher_calls.log"
    run.env["WATCHER_COUNT_LOG"] = str(log)

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    assert _wait_for(lambda: log.exists() and log.read_text())
    time.sleep(1.0)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(calls) == 1
    argv = calls[0]
    assert argv[argv.index("--pid") + 1] == str(_record_pid(result.stdout))
    watched = argv[argv.index("--log") + 1]
    assert watched.startswith(str(run.root / "system" / "logs")) and watched.endswith(
        "-completion.jsonl"), watched
    assert argv[argv.index("--reporter") + 1] == "companion-self-answer"


def test_completion_callback_waits_for_last_process_exit(run):
    _seat_fixture(run, _THREE_SEATS)
    release = run.root / "release"
    records = _seat_stub(run, SEAT_STUB_HOLD="cdo", SEAT_STUB_RELEASE_FILE=str(release))
    calls = _hook(run)

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    # The last run has written its terminal event and is held alive; the two before it ended.
    assert _wait_for(lambda: "cdo" in _records(records)), _records(records)
    assert all(_records(records)[seat]["end"] for seat in ("cto", "cpo"))
    time.sleep(8.0)   # longer than the watcher's own poll interval
    assert _calls(calls) == [], "the callback fired while the last run's process was alive"
    release.touch()
    assert _wait_for(lambda: _calls(calls)), "the callback never fired after the last run ended"
    time.sleep(2.0)
    assert _calls(calls) == ["claude:completed"]


def test_final_failed_run_still_has_one_post_sequence_callback(run):
    _seat_fixture(run, _THREE_SEATS)
    records = _seat_stub(run, SEAT_STUB_FAIL="cdo")
    calls = _hook(run)

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    assert _wait_for(lambda: _all_ended(records, 3))
    assert _wait_for(lambda: _calls(calls)), "no callback after the sequence ended"
    time.sleep(2.0)
    assert _calls(calls) == ["claude:failed"]


def test_keep_awake_covers_whole_sequence(run):
    _seat_fixture(run, _THREE_SEATS)
    _seat_stub(run)
    run.hold_watcher_until_kept_awake()

    result = run("example-product", "fdr", "--keep-awake")

    assert result.returncode == 0, result.stderr
    assert run.caffeinate_calls() == 1
    time.sleep(1.0)
    assert run.caffeinate_calls() == 1, "keep-awake was bound once per run, not once per watcher"
    watcher = run.watcher_argv()
    assert watcher[watcher.index("--pid") + 1] == str(_record_pid(result.stdout))


def test_identity_records_sequence_run_and_single_watcher(run):
    _seat_fixture(run, _THREE_SEATS)
    release = run.root / "release"
    records = _seat_stub(run, SEAT_STUB_HOLD="cto", SEAT_STUB_RELEASE_FILE=str(release))
    identity_file = run.root / "launch.identity.json"
    run.env["DETACHED_RUN_IDENTITY_FILE"] = str(identity_file)
    try:
        result = run("example-product", "fdr")

        assert result.returncode == 0, result.stderr
        assert_launch_recorded_its_identity(result.stdout, identity_file)
        assert _wait_for(lambda: "cto" in _records(records))
        provider_pid = _records(records)["cto"]["pid"]
        sequence_pid = _record_pid(result.stdout)
        assert provider_pid != sequence_pid

        os.kill(sequence_pid, 15)   # the stop a walk sends its recorded run

        def provider_gone():
            try:
                os.kill(provider_pid, 0)
            except ProcessLookupError:
                return True
            return False
        assert _wait_for(provider_gone, timeout=30), "a stop did not reach the active provider run"
        time.sleep(3.0)
        assert set(_records(records)) == {"cto"}, "a stopped sequence started a successor"
    finally:
        release.touch()


def test_any_refused_group_command_prevents_entire_launch(run):
    _seat_fixture(run, _THREE_SEATS)
    records = _seat_stub(run)
    shim = run.root / "bin" / "python3"
    shim.write_text(
        "#!/bin/sh\n"
        'case " $* " in *" --agent cdo "*) case " $* " in *" --dry-run "*) '
        'echo "refused cdo" >&2; exit 7 ;; esac ;; esac\n'
        f'exec {shlex.quote(__import__("sys").executable)} "$@"\n')
    shim.chmod(0o755)

    result = run("example-product", "fdr")

    assert result.returncode != 0
    assert "nothing launched" in result.stderr
    assert _records(records) == {}
    assert not (run.root / "system" / "logs").exists(), "a refused launch wrote a plan or a log"
    assert run.watcher_argv() == []


def test_reader_failure_reports_grouping_skipped_and_launches_once(run):
    companion = _seat_fixture(run, _THREE_SEATS)
    companion.chmod(0)
    try:
        result = run("example-product", "fdr")
        argv = run.launched_argv()
    finally:
        companion.chmod(0o644)

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("Grouping:  skipped") == 1, result.stdout
    assert "Sequence log" not in result.stdout and "Answer only these items" not in " ".join(argv)
    assert argv != []


def test_seatless_causes_merge_without_losing_items_or_explanations(run):
    _seat_fixture(run, [("1.1", None, False), ("1.2", "cfo", False), ("1.3", "cfo", False),
                        ("2.1", "delegate", False), ("2.2", "other", False),
                        ("3.1", "cpo", False)],
                  producer="ghost", agents=("cpo",))
    run.agent_path("ghost").unlink()   # the producer's seat has no agent file
    run.write_agent("delegate", "# delegate\n")   # an agent file and no loader

    result = run("example-product", "fdr", "--dry-run")

    assert result.returncode == 0, result.stderr
    entries = _run_entries(result.stdout)
    assert [(e["seat"], e["items"]) for e in entries] == [
        ("seatless", ["1.1", "1.2", "1.3", "2.1", "2.2"]), ("cpo", ["3.1"])]
    prompt = _prompt_in(entries[0]["argv"])
    for named in ("ghost", "cfo", "other"):
        assert prompt.count(f"'{named}' seat") == 1, prompt
    assert "delegate" not in prompt
    assert "'cfo'" not in _prompt_in(entries[1]["argv"])


def test_plan_preserves_prompt_paths_and_item_lists_as_argv(run):
    companion = _seat_fixture(run, [("1.1", None, False), ("1.2", "cpo", False)],
                              product_path="products/it's \"odd\" $dir `x`")
    records = _seat_stub(run)

    result = run("example-product", "fdr")

    assert result.returncode == 0, result.stderr
    done = _wait_for(lambda: _all_ended(records, 2))
    assert done, _records(records)
    base = f"invoke the companion-self-answer skill for the companion at {companion}."
    prompts = {seat: next(a for a in record["argv"] if a.startswith("invoke the companion"))
               for seat, record in done.items()}
    launched = _launched_prompt(companion)   # today's prompt as the adapter hands it to a run
    assert prompts == {
        "cto": launched.replace(base, f"{base} Answer only these items: 1.1."),
        "cpo": launched.replace(base, f"{base} Answer only these items: 1.2."),
    }


# --- hf: the Claude run, aimed at Hugging Face's router (CP-424 … CP-432) ------------------------

_HF_SENTINEL = "hf_SELF_ANSWER_sentinel_do_not_leak"
_COMPANION_USAGE = (
    "usage: <CORE>/launchers/companion-self-answer/launcher.sh <project> <document> "
    "[--provider claude|codex|gemini|hf|ollama] [--dry-run] [--keep-awake]"
)


def _give_hf_token(run, value=_HF_SENTINEL):
    (run.home / ".env").write_text(f"HF_TOKEN={value}\n")


def _hf_producer(run, model="open/model-1"):
    """The `_producer` fixture with an `hf.md` beside the `claude.md` it declares."""
    producer_dir = _producer(run, provider_files=("claude",))
    _intelligence(producer_dir, "hf", model)
    return producer_dir


@pytest.mark.parametrize("channel", ["flag", "equals-flag", "variable", "provider-file"])
def test_hf_is_accepted_by_flag_variable_and_provider_file(run, channel):
    _document_to_answer(run)
    _give_hf_token(run)
    args, script = [], _SCRIPT
    if channel == "flag":
        args = ["--provider", "hf"]
    elif channel == "equals-flag":
        args = ["--provider=hf"]
    elif channel == "variable":
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "hf"
    else:
        script = _instance_provider_file(run, _entry("hf"))

    result = run("example-product", "PRD", *args, "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[:4] == [
        "claude", "--print", "--output-format", "stream-json"]


@pytest.mark.parametrize("seated", [True, False], ids=["seated", "seatless"])
def test_hf_seated_and_seatless_runs_are_claude_turns_at_effort_high(run, seated):
    product = run.project("example-product")
    run.document(product, "fdr")
    if seated:
        run.companion(product, "fdr", skill="product-fdr")
        run.skill_launcher("product-fdr", agent="principal-pm")
        run.agent_file("principal-pm")
    else:
        run.companion(product, "fdr")
    _give_hf_token(run)

    result = run("example-product", "fdr", "--provider", "hf", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[:4] == ["claude", "--print", "--output-format", "stream-json"]
    assert "--session-id" in argv
    assert "--setting-sources" in argv and "--plugin-dir" in argv
    assert "companion-self-answer" in _plugin_skills(argv)[0]
    assert ("--agent" in argv) is seated
    if seated:
        assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert _carries_effort_high(argv), argv
    joined = "\n".join(argv)
    assert "Execute this fixed task:" not in joined
    assert "You are running a Kensaiapp unattended" not in joined


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_an_hf_run_takes_the_producers_hf_model(run, mode):
    producer_dir = _hf_producer(run)
    _give_hf_token(run)

    result = run("example-product", "fdr", "--provider", "hf",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout) if mode == "--dry-run" else run.launched_argv()
    assert _models(argv) == ["open/model-1"]
    if mode == "--dry-run":
        assert f"Intelligence: {producer_dir / 'intelligence' / 'hf.md'}" in result.stdout


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_a_producer_folder_without_hf_md_is_refused_naming_the_path(run, mode):
    producer_dir = _producer(run, provider_files=("claude",))
    _give_hf_token(run)

    result = run("example-product", "fdr", "--provider", "hf",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode != 0
    assert str(producer_dir / "intelligence" / "hf.md") in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_an_hf_run_carries_the_telemetry_settings(run):
    _document_to_answer(run)
    _give_hf_token(run)
    endpoint_file = run.root / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)

    result = run("example-product", "PRD", "--provider", "hf")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv.count("--settings") == 1
    merged = json.loads(Path(argv[argv.index("--settings") + 1]).read_text())
    assert merged["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9/v1"


@pytest.mark.parametrize("token", [None, ""], ids=["no-env-file", "empty-token"])
@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_hf_with_no_token_is_refused_before_anything_spawns(run, mode, token):
    _document_to_answer(run)
    if token is not None:
        _give_hf_token(run, token)

    result = run("example-product", "PRD", "--provider", "hf",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode != 0
    assert "HF_TOKEN" in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    assert run.watcher_argv() == []


def test_the_hf_token_leaks_nowhere(run):
    _document_to_answer(run)
    _give_hf_token(run)

    dry = run("example-product", "PRD", "--provider", "hf", "--dry-run")
    real = run("example-product", "PRD", "--provider", "hf")

    assert dry.returncode == 0 and real.returncode == 0, (dry.stderr, real.stderr)
    spoken = [dry.stdout, dry.stderr, real.stdout, real.stderr]
    spoken += run.launched_argv() + run.watcher_argv()
    assert not any(_HF_SENTINEL in text for text in spoken)
    kept_secret = run.home / ".env"
    leaked = [
        str(path)
        for path in run.root.rglob("*")
        if path.is_file() and path != kept_secret
        and _HF_SENTINEL.encode() in path.read_bytes()
    ]
    assert leaked == []


def test_hf_completion_reaches_real_chain_hook_with_provider(run):
    _document_to_answer(run)
    _give_hf_token(run)
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER")
    hook_log = run.root / "hook-result"
    run.env["TEST_HOOK_RESULT"] = str(hook_log)
    hook = run.root / "completion-hook"
    hook.write_text('#!/bin/sh\n'
                    'printf "%s:%s" "$KENSAIAPP_AGENT_PROVIDER" "$1" > "$TEST_HOOK_RESULT"\n')
    hook.chmod(0o755)
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)

    result = run("example-product", "PRD", "--provider", "hf")

    assert result.returncode == 0, result.stderr
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not hook_log.exists():
        time.sleep(0.05)
    assert hook_log.exists(), result.stdout
    assert hook_log.read_text() == "hf:completed"


def test_the_usage_line_names_hf_and_ollama(run):
    result = run()

    assert result.returncode != 0
    assert _COMPANION_USAGE in result.stderr


def test_the_header_usage_names_hf_and_ollama():
    header = {line.lstrip("#").strip() for line in _SCRIPT.read_text().splitlines()
              if line.startswith("#")}

    assert _COMPANION_USAGE.removeprefix("usage: ") in header
    assert (
        "--provider    claude, codex, gemini, hf or ollama; else KENSAIAPP_AGENT_PROVIDER, else the"
    ) in header
    assert "`launchers.companion-self-answer` entry of .providers.toml at the instance" in header
    assert "root, else a refusal — there is no default. An hf run is the Claude run," in header
    assert "aimed at Hugging Face's router, and it is refused unless ~/.env holds a" in header
    assert "non-empty HF_TOKEN. An ollama run is the Claude run, aimed at the local" in header
    assert "Ollama server, and it is refused unless that server answers" in header


# --- hf, from the spec's own words (added by development-code-integrity) -------------------------

_HF_ROUTER = "https://router.huggingface.co"

# A Claude Code turn that dies before it writes any result: no terminal provider event.
_CLAUDE_STUB_WITH_NO_RESULT = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
"""


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_an_hf_run_is_aimed_at_hugging_faces_router(run, mode):
    # CP-426: "It is pointed at Hugging Face's router."
    _document_to_answer(run)
    _give_hf_token(run)

    result = run("example-product", "PRD", "--provider", "hf",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout) if mode == "--dry-run" else run.launched_argv()
    settings = json.loads(Path(argv[argv.index("--settings") + 1]).read_text())
    assert settings["env"]["ANTHROPIC_BASE_URL"] == _HF_ROUTER


def test_hf_failure_reaches_real_chain_hook_with_provider(run):
    # CP-428: "Its completion, and its failure, reach the notifier and any chain hook naming
    # provider hf."
    _document_to_answer(run)
    _give_hf_token(run)
    stub = run.root / "bin" / "claude"
    stub.unlink()
    stub.write_text(_CLAUDE_STUB_WITH_NO_RESULT)
    stub.chmod(0o755)
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER")
    hook_log = run.root / "hook-result"
    run.env["TEST_HOOK_RESULT"] = str(hook_log)
    hook = run.root / "completion-hook"
    hook.write_text('#!/bin/sh\n'
                    'printf "%s:%s" "$KENSAIAPP_AGENT_PROVIDER" "$1" > "$TEST_HOOK_RESULT"\n')
    hook.chmod(0o755)
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)

    result = run("example-product", "PRD", "--provider", "hf")

    assert result.returncode == 0, result.stderr
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not hook_log.exists():
        time.sleep(0.05)
    assert hook_log.exists(), result.stdout
    assert hook_log.read_text() == "hf:failed"


# --- ollama: the Claude run, aimed at the local Ollama server (CP-499 … CP-502) -----------------

_NO_SERVER = "provider 'ollama' needs an Ollama server answering at {address}"


def _point_at(run, server):
    """Aim the run at an answering stub server; a case that skips this keeps the guard's
    address, where nothing listens."""
    run.env["KENSAIAPP_OLLAMA_URL"] = server.address


def _ollama_producer(run, model="local:7b"):
    """The `_producer` fixture with an `ollama.md` beside the `claude.md` it declares."""
    producer_dir = _producer(run, provider_files=("claude",))
    _intelligence(producer_dir, "ollama", model)
    return producer_dir


@pytest.mark.parametrize("channel", ["flag", "equals-flag", "variable", "provider-file"])
def test_ollama_is_accepted_by_flag_variable_and_provider_file(run, ollama_server, channel):
    _document_to_answer(run)
    _point_at(run, ollama_server)
    args, script = [], _SCRIPT
    if channel == "flag":
        args = ["--provider", "ollama"]
    elif channel == "equals-flag":
        args = ["--provider=ollama"]
    elif channel == "variable":
        run.env["KENSAIAPP_AGENT_PROVIDER"] = "ollama"
    else:
        script = _instance_provider_file(run, _entry("ollama"))

    result = run("example-product", "PRD", *args, "--dry-run", script=script)

    assert result.returncode == 0, result.stderr
    assert _dry_run_argv(result.stdout)[:4] == [
        "claude", "--print", "--output-format", "stream-json"]


@pytest.mark.parametrize("seated", [True, False], ids=["seated", "seatless"])
def test_ollama_seated_and_seatless_runs_are_claude_turns_at_effort_high(
    run, ollama_server, seated
):
    product = run.project("example-product")
    run.document(product, "fdr")
    if seated:
        run.companion(product, "fdr", skill="product-fdr")
        run.skill_launcher("product-fdr", agent="principal-pm")
        run.agent_file("principal-pm")
    else:
        run.companion(product, "fdr")
    _point_at(run, ollama_server)

    result = run("example-product", "fdr", "--provider", "ollama", "--dry-run")

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout)
    assert argv[:4] == ["claude", "--print", "--output-format", "stream-json"]
    assert "--session-id" in argv
    assert "--setting-sources" in argv and "--plugin-dir" in argv
    assert "companion-self-answer" in _plugin_skills(argv)[0]
    assert ("--agent" in argv) is seated
    if seated:
        assert argv[argv.index("--agent") + 1] == "principal-pm"
    assert _carries_effort_high(argv), argv
    joined = "\n".join(argv)
    assert "Execute this fixed task:" not in joined
    assert "You are running a Kensaiapp unattended" not in joined


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_an_ollama_run_takes_the_producers_ollama_model(run, ollama_server, mode):
    producer_dir = _ollama_producer(run)
    _point_at(run, ollama_server)

    result = run("example-product", "fdr", "--provider", "ollama",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode == 0, result.stderr
    argv = _dry_run_argv(result.stdout) if mode == "--dry-run" else run.launched_argv()
    assert _models(argv) == ["local:7b"]
    if mode == "--dry-run":
        assert f"Intelligence: {producer_dir / 'intelligence' / 'ollama.md'}" in result.stdout


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_a_producer_folder_without_ollama_md_is_refused_naming_the_path(
    run, ollama_server, mode
):
    producer_dir = _producer(run, provider_files=("claude",))
    _point_at(run, ollama_server)

    result = run("example-product", "fdr", "--provider", "ollama",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode != 0
    assert str(producer_dir / "intelligence" / "ollama.md") in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []


def test_an_ollama_run_carries_the_telemetry_settings(run, ollama_server):
    _document_to_answer(run)
    _point_at(run, ollama_server)
    endpoint_file = run.root / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)

    result = run("example-product", "PRD", "--provider", "ollama")

    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv.count("--settings") == 1
    merged = json.loads(Path(argv[argv.index("--settings") + 1]).read_text())
    assert merged["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9/v1"
    assert merged["env"]["ANTHROPIC_BASE_URL"] == ollama_server.address


@pytest.mark.parametrize("mode", ["--dry-run", "real"])
def test_ollama_with_no_server_is_refused_before_anything_spawns(run, mode):
    _document_to_answer(run)

    result = run("example-product", "PRD", "--provider", "ollama",
                 *(["--dry-run"] if mode == "--dry-run" else []))

    assert result.returncode != 0
    assert _NO_SERVER.format(address=run.env["KENSAIAPP_OLLAMA_URL"]) in result.stderr
    assert run.launched_argv(wait=_ABSENT_WAIT) == []
    assert run.watcher_argv() == []


def test_ollama_completion_reaches_real_chain_hook_with_provider(run, ollama_server):
    _document_to_answer(run)
    _point_at(run, ollama_server)
    run.env.pop("LAUNCH_COMPANION_SELF_ANSWER_WATCHER")
    hook_log = run.root / "hook-result"
    run.env["TEST_HOOK_RESULT"] = str(hook_log)
    hook = run.root / "completion-hook"
    hook.write_text('#!/bin/sh\n'
                    'printf "%s:%s" "$KENSAIAPP_AGENT_PROVIDER" "$1" > "$TEST_HOOK_RESULT"\n')
    hook.chmod(0o755)
    run.env["DETACH_WATCHER_ON_COMPLETE"] = str(hook)

    result = run("example-product", "PRD", "--provider", "ollama")

    assert result.returncode == 0, result.stderr
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not hook_log.exists():
        time.sleep(0.05)
    assert hook_log.exists(), result.stdout
    assert hook_log.read_text() == "ollama:completed"
