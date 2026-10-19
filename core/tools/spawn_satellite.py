#!/usr/bin/env python3
"""Stand up a shared-core kensaiapp satellite — the deterministic half of spawning one.

WHAT IT IS FOR
    A satellite is a local sibling instance that carries no `core/` of its own and reads a host
    instance's core through an absolute `CORE=` binding in an untracked `.env` (see
    `<CORE>/doctrine/setup/shared_core_instance.md`). `kensaiapp-spawn` v1.0.0 (`89122ed`) tried
    to do this as an eight-step prose procedure a human followed by hand, and was withdrawn
    (`f6d5c0a`) after one run carried a sibling instance's own facts — its trading-domain section,
    a reference specific to that instance — into a fresh instance, because a prose step can assert
    something false and nothing evaluates the assertion. This script exists to replace every one
    of those steps with a line of code that either does the right thing or raises: a missing
    template is a `SystemExit` naming the path, never a silently-skipped file; a wrong location is
    a refusal naming the offending value, never a plausible-looking guess.

WHAT IT DOES, IN ORDER
    1. Validates the invocation — target doesn't already belong to someone else, `--location` is an
       existing directory (a satellite may live anywhere; the absolute links resolve from any
       location), the host has a `.claude/` layer, `--skills-mode` is one of the two answers
       `link_satellite.py` understands.
    2. Creates the satellite directory, `git init`s it (skippable with `--no-git`), copies the
       host's `.env.example` and `.providers.toml.example` verbatim (the satellite makes its own
       `.providers.toml` from the second with `cp`; the spawn never writes it), and writes `.env`
       binding `<CORE>` to the host's `core/`, absolute. No local `core/` is ever created — that
       is the design, not an omission.
    3. Stamps the satellite's own §1 files from `<CORE>/templates/` — `AGENTS.md`, `kensaiapp.md`, `CLAUDE.md`, `.gitignore`,
       `claude-design-instructions.md`,
       `system/michi.md`, `system/nemawashi/README.md` (+ its `unpicked/`, `trail/` and `drop/` stubs and
       the instance **setup seed** filed in it), `system/shukuba/README.md` (+ its `trail/` stub),
       and the three `system/doctrine/*.md` (which take the generic word "kensaiapp", never the
       satellite's own name —
       `kensaiapp_structure.md`'s own note on why: inferring the name from the instance produced
       the `tracker_doctrine.md` bug).
    4. Stamps the role layer — the fourteen per-role overlays plus `system/CROSS_ROLE.md` — from
       `<CORE>/templates/role-templates/`. These are exactly the files the withdrawn skill copied
       from a sibling; here they can only come from a template, and every leading HTML comment
       block (template metadata) is stripped, never carried into the stamped file.
    5. Writes a fresh `.claude/settings.local.json` — gitignored, per-machine, and never read from
       the host (a mature host's copy carries dozens of grants that are not this satellite's to
       inherit).
    6. Delegates to the two tools that already own their jobs: `link_satellite.py` writes the
       satellite's `.claude/settings.json` from the host's hook wiring, and for a producer links
       the root `skills/` layer back to the host if the host has one,
       and `project-stamp`'s `stamp_project.py` stamps the first project, when `--project`
       is given. Neither is reimplemented here.
    7. Verifies what it produced — `link_satellite.py --check` returns 0, no `core/` directory
       exists, no core-referencing file it authored (the role layer) carries a literal `core/…` or
       `~/.claude/…` path, the fourteen overlays name the satellite, not the host — and commits the
       result through `commit_builder.py` as the satellite's own genesis commit.

WHAT IT NEVER TOUCHES
    `core/tools/link_satellite.py`, `core/tools/commit_builder.py`, `skills/interactive-product/.claude/skills/project-stamp/**`,
    and `core/templates/**` — all reused exactly as they are; this script calls them, never
    reimplements them. It never creates a local `core/` in the satellite, and it never overwrites a
    real file already sitting at a path it would write (Task 8 — re-runnable, so an interrupted run
    is a resume, not a redo).

IDEMPOTENCE — WHY "ALREADY EXISTS" DOES NOT ALWAYS REFUSE
    `--location/--name` refuses when the target is occupied by something this tool doesn't
    recognize — an empty directory, an unrelated project, anything with no `.env`. It resumes,
    filling only the gaps, when the target already carries an `.env` this tool itself would have
    written (Task 2 writes `.env` before any of the stamped §1/role-layer files, so its presence
    is the earliest reliable marker of "this is our own satellite, interrupted or complete," and
    its absence on an occupied path is the earliest reliable marker of "this is not ours"). Every
    write in this script but one is create-if-missing, never-overwrite — that single rule is what
    makes both the refusal and the resume correct with no separate "resume mode" to fall out of step.
    The one exception is the template-owned pair, `AGENTS.md` and the one-line `CLAUDE.md` that
    imports it: each is the same in every instance and carries nothing an instance wrote, so a
    resume rewrites it from the template whenever the two differ
    (`_write_template_owned`) — which is how a routing change reaches an instance already stamped.

    The instance setup seed is the one write that cannot key on an exact path, because a seed is
    filed as `<YYYY-MM-DD>_<slug>.md` and a resume made on a later day would key on a name the
    first run never wrote. It keys on the **slug**, across the seedbed's root and both bins — so a
    seed already picked, un-picked or walked to `trail/` is found and left alone, and a re-run
    never stamps a second one or resurrects a retired one. `_write_seed_if_absent` is that rule.

USAGE
    python3 <CORE>/tools/spawn_satellite.py \\
        --name kensaiapp-<name> --location /abs/path/to/parent --host /abs/path/to/host \\
        --skills-mode consumer|producer \\
        [--project <name>] [--product-path <path>] [--date YYYY-MM-DD] [--check] [--no-git]

    `--check` resolves and prints the plan, creates nothing, and exits 1 if anything would change,
    0 if nothing would — a drift/readiness gate, same contract as `link_satellite.py --check`.

EXIT CODES
    0  nothing needed doing, or everything asked for was done
    1  a refusal (bad invocation, occupied unrecognized target, a delegated tool's own failure), or
       `--check` found something that would change
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import link_satellite
import skill_path
from typing import Callable

__version__ = "1.13.2"

SKILLS_MODES = ("consumer", "producer")

# The word every stamped doctrine file's title takes instead of the satellite's own name — fixed,
# never inferred from the instance, per `kensaiapp_doctrine_template.md`'s own note on why
# (inferring it produced the `tracker_doctrine.md` bug).
GENERIC_DOMAIN_WORD = "kensaiapp"

# role token (== its global loader's filename stem, == `system/loaders/<role>.md`'s stem) -> title.
# The thirteen roles that read no context — `pm` has its own template and title, handled separately,
# because its on-invocation context read is structural, not a substitution.
ROLE_TITLES: dict[str, str] = {
    "architect": "Architect",
    "cdo": "CDO",
    "content_editor": "Content Editor",
    "content_manager": "Content Manager",
    "cpo": "CPO",
    "cto": "CTO",
    "developer": "Developer",
    "principal_architect": "Principal Architect",
    "principal_pm": "Principal PM",
    "product_owner": "Product Owner",
    "scrum_master": "Scrum Master",
    "senior_engineer": "Senior Engineer",
    "tech_lead": "Tech Lead",
}

DEFAULT_CO_AUTHORED_BY = "Claude Code <noreply@anthropic.com>"


@dataclass(frozen=True)
class SpawnPlan:
    """The resolved, validated spawn — everything downstream reads this, nothing re-derives it."""

    name: str
    host: Path
    location: Path
    satellite: Path
    skills_mode: str
    project: str | None
    product_path: str | None
    no_git: bool
    date: str


@dataclass
class Report:
    """What a run did (or, under `--check`, would do) — mirrors `link_satellite.py`'s Report."""

    created: list[str] = field(default_factory=list)
    already: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)

    @property
    def would_change(self) -> bool:
        return bool(self.created or self.updated)

    def render(self, *, check: bool) -> str:
        verb = "would create" if check else "created"
        update_verb = "would update" if check else "updated"
        lines = [f"{verb}: {len(self.created)}", f"already present: {len(self.already)}"]
        if self.updated:
            lines.append(f"{update_verb}: {len(self.updated)}")
        for path in self.created:
            lines.append(f"  [{verb}] {path}")
        for path in self.updated:
            lines.append(f"  [{update_verb}] {path}")
        return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spawn_satellite.py",
        description=(
            "Stand up a shared-core kensaiapp satellite. Idempotent — re-run to resume an "
            "interrupted spawn or fill a gap."
        ),
    )
    parser.add_argument("--name", required=True, help="the satellite's instance name")
    parser.add_argument(
        "--location", required=True,
        help="the existing directory the satellite is created under — anywhere on the machine",
    )
    parser.add_argument("--host", required=True, help="the root of the host instance, the one that holds the shared core")
    parser.add_argument(
        "--skills-mode", required=True, choices=SKILLS_MODES,
        help=(
            "consumer = no skills layer is linked (launchers find grouped skills in the host); "
            "producer = the host's root skills/ mirrored as real dirs, for skill-evals output"
        ),
    )
    parser.add_argument(
        "--project", default=None,
        help="scaffold this project into the satellite via project-stamp (optional)",
    )
    parser.add_argument(
        "--product-path", default=None,
        help="the project's Product path — absolute means external, relative means internal",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="resolve and print the plan; create nothing; exit 1 if anything would change",
    )
    parser.add_argument("--no-git", action="store_true", help="skip git init")
    parser.add_argument(
        "--date", default=None,
        help=(
            "the date the instance setup seed is filed under (YYYY-MM-DD). Default: today. "
            "The seedbed names every idea <YYYY-MM-DD>_<slug>.md, so the seed needs one."
        ),
    )
    parser.add_argument(
        "--co-authored-by", default=None,
        help=(
            "override the satellite genesis commit's Co-Authored-By: trailer. Default: the "
            "KENSAIAPP_COMMIT_MODEL env var, else a generic placeholder — this script cannot "
            "detect the running model's own identity the way a live session can."
        ),
    )
    return parser


def resolve_plan(args: argparse.Namespace) -> SpawnPlan:
    """Validate the invocation and resolve it to a `SpawnPlan`. Every refusal names the offending
    value and raises `SystemExit` before anything is created — mirrors `link_satellite.py`'s
    invocation guards."""
    host = Path(args.host).expanduser().resolve()
    if not host.is_dir():
        raise SystemExit(f"error: --host is not a directory: {host}")
    if not (host / ".claude").is_dir():
        raise SystemExit(f"error: --host has no .claude/ directory: {host / '.claude'}")

    location = Path(args.location).expanduser().resolve()
    if not location.is_dir():
        # A satellite may live anywhere — `shared_core_instance.md` retired the beside-the-host
        # placement rule, since the absolute links resolve from any location. What is still worth
        # refusing is a location that does not exist: the satellite directory is created with
        # parents, so a typo'd path would silently stand an instance up in a tree nobody meant.
        raise SystemExit(f"error: --location is not an existing directory: {location}")

    name = args.name
    satellite = location / name
    if satellite.exists():
        if not satellite.is_dir():
            raise SystemExit(f"error: target already exists and is not a directory: {satellite}")
        if not (satellite / ".env").exists():
            raise SystemExit(
                f"error: target already exists: {satellite} — not recognized as a satellite of "
                "this host (no .env found). Refusing to write into an unrelated existing "
                "directory. Remove it, or point --location/--name at a fresh path, and re-run."
            )
        # Has .env -> a satellite this tool already stamped, complete or interrupted. Resume:
        # fall through and let the create-if-missing writes fill whatever is still missing.

    return SpawnPlan(
        name=name,
        host=host,
        location=location,
        satellite=satellite,
        skills_mode=args.skills_mode,
        project=args.project,
        product_path=args.product_path,
        no_git=args.no_git,
        date=args.date or datetime.date.today().isoformat(),
    )


def _print_plan(plan: SpawnPlan) -> None:
    print("spawn-satellite plan:")
    print(f"  name:          {plan.name}")
    print(f"  host:          {plan.host}")
    print(f"  location:      {plan.location}")
    print(f"  satellite:     {plan.satellite}")
    print(f"  skills-mode:   {plan.skills_mode}")
    print(f"  project:       {plan.project or '(none)'}")
    print(f"  product-path:  {plan.product_path or '(none)'}")
    print(f"  seed date:     {plan.date}")
    print(f"  git:           {'skipped (--no-git)' if plan.no_git else 'git init -b main'}")


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    plan = resolve_plan(args)
    _print_plan(plan)
    co_authored_by = args.co_authored_by or os.environ.get("KENSAIAPP_COMMIT_MODEL") or DEFAULT_CO_AUTHORED_BY
    report = spawn(plan, check=args.check, co_authored_by=co_authored_by)
    print(report.render(check=args.check))
    if args.check:
        return 1 if report.would_change else 0
    return 0


# --------------------------------------------------------------------------------------------
# Write primitives — every write funnels through these two, which is what makes create-if-missing
# (never overwrite a real file) and --check (never write at all) uniform across every task below,
# with no separate "resume mode" or "dry-run mode" to keep in step by hand.
# --------------------------------------------------------------------------------------------


def _write_if_missing(report: Report, target: Path, render: Callable[[], str], *, check: bool) -> None:
    """`render` is called only when `target` is missing — a template read inside it (which may
    raise `SystemExit` naming a missing template) only fires when the write is actually needed,
    check or not; the actual filesystem write is gated on `not check` alone."""
    if target.exists():
        report.already.append(str(target))
        return
    content = render()
    report.created.append(str(target))
    if check:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _write_template_owned(report: Report, target: Path, render: Callable[[], str], *, check: bool) -> None:
    """The one overwriting write. A template-owned file holds nothing an instance authored, so the
    template is the whole of what it should say: missing, it is created; present and equal, it is
    left alone; present and different, it is rewritten and reported as `updated`. `render` always
    runs, because equality cannot be judged without the template's bytes."""
    content = render()
    if not target.exists():
        report.created.append(str(target))
    elif target.read_text(encoding="utf-8") == content:
        report.already.append(str(target))
        return
    else:
        report.updated.append(str(target))
    if check:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------------------------
# Task 2 — create the instance and bind <CORE>
# --------------------------------------------------------------------------------------------


def _run_git_init(satellite: Path) -> None:
    result = subprocess.run(
        ["git", "init", "-q", "-b", "main", str(satellite)], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise SystemExit(f"error: git init failed for {satellite}:\n{result.stdout}{result.stderr}")
    _ensure_git_identity(satellite)


def _ensure_git_identity(satellite: Path) -> None:
    """A fresh `git init` inherits `user.name`/`user.email` from the global config when set. When
    neither resolves (a bare CI/test environment), Task 7's genesis commit would otherwise fail
    with "Please tell me who you are." Set a local, repo-scoped fallback — same harmless posture
    as the other repo-local git config this codebase already sets (`core.hooksPath`) — only when
    nothing resolves, never overriding a real identity."""
    for key, fallback in (("user.name", "kensaiapp"), ("user.email", "kensaiapp@localhost")):
        resolved = subprocess.run(
            ["git", "-C", str(satellite), "config", key], capture_output=True, text=True
        ).stdout.strip()
        if not resolved:
            subprocess.run(["git", "-C", str(satellite), "config", key, fallback], check=True)


def _create_instance(plan: SpawnPlan, report: Report, *, check: bool) -> None:
    satellite = plan.satellite
    if not satellite.exists():
        report.created.append(str(satellite))
        if not check:
            satellite.mkdir(parents=True)
    else:
        report.already.append(str(satellite))

    if not plan.no_git:
        git_dir = satellite / ".git"
        if not git_dir.exists():
            report.created.append(str(git_dir))
            if not check:
                _run_git_init(satellite)
        else:
            report.already.append(str(git_dir))

    def _render_env_example() -> str:
        host_env_example = plan.host / ".env.example"
        if not host_env_example.exists():
            raise SystemExit(f"error: host has no .env.example: {host_env_example}")
        return host_env_example.read_text(encoding="utf-8")

    _write_if_missing(report, satellite / ".env.example", _render_env_example, check=check)

    def _render_providers_example() -> str:
        host_providers_example = plan.host / ".providers.toml.example"
        if not host_providers_example.exists():
            raise SystemExit(
                f"error: host has no .providers.toml.example: {host_providers_example}")
        return host_providers_example.read_text(encoding="utf-8")

    _write_if_missing(
        report, satellite / ".providers.toml.example", _render_providers_example, check=check
    )

    def _render_env() -> str:
        core_path = plan.host / "core"
        return (
            f"# {plan.name} — shared core: resolves <CORE> to {plan.host.name}'s core store.\n"
            "# This instance carries no local core/ of its own by design; it shares the host's.\n"
            f"CORE={core_path}\n"
        )

    _write_if_missing(report, satellite / ".env", _render_env, check=check)


# --------------------------------------------------------------------------------------------
# Task 3 — stamp the instance's own §1 files
# --------------------------------------------------------------------------------------------


def _read_template(templates_dir: Path, name: str) -> str:
    """A missing template is a loud, immediate failure naming the path — never a silently
    skipped file. This is the behaviour the whole script exists for (a prose step that asserts
    something false sits inertly until a human runs it; this raises on line one instead)."""
    path = templates_dir / name
    if not path.exists():
        raise SystemExit(f"error: missing template: {path}")
    return path.read_text(encoding="utf-8")


def _stamp_instance_token(text: str, value: str) -> str:
    return text.replace("<instance>", value)


def _write_seed_if_absent(
    report: Report, seedbed: Path, slug: str, date: str, render: Callable[[], str], *, check: bool
) -> None:
    """The one write that cannot key on an exact path. A seed is filed as `<YYYY-MM-DD>_<slug>.md`,
    so `_write_if_missing` would stamp a *second* setup seed on any re-run made on a later day —
    and would resurrect one the instance had already walked and moved to `trail/`. Presence is
    therefore matched on the **slug**, across the seedbed's root and all three of its bins: root (the
    active seed, or nothing), `unpicked/` (the candidate pool), `trail/` (walked) and `drop/`
    (killed). Any hit means this instance already has its setup seed and this run leaves it alone —
    a bin left out of this glob resurrects a seed the instance already dealt with."""
    existing = sorted(
        p for bin_ in (seedbed, seedbed / "unpicked", seedbed / "trail", seedbed / "drop")
        for p in bin_.glob(f"*_{slug}.md")
    )
    if existing:
        report.already.extend(str(p) for p in existing)
        return
    target = seedbed / f"{date}_{slug}.md"
    content = render()
    report.created.append(str(target))
    if check:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _extract_fenced_block(text: str) -> str:
    """`gitignore_template.md` is prose wrapping a code fence — the stamped `.gitignore` is the
    fenced content only, verbatim, never the surrounding prose or the fence markers themselves."""
    lines = text.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            if start is None:
                start = i
            else:
                end = i
                break
    if start is None or end is None:
        raise SystemExit("error: gitignore_template.md has no fenced code block to extract")
    return "\n".join(lines[start + 1 : end]) + "\n"


def _stamp_instance_files(plan: SpawnPlan, report: Report, templates: Path, *, check: bool) -> None:
    satellite = plan.satellite

    # The routing file is the same bytes in every instance — no token to fill — and is the one
    # stamp a resume rewrites. The identity file beside it is the instance's own from the first
    # edit on, so it is created once and never touched again.
    _write_template_owned(
        report, satellite / "AGENTS.md",
        lambda: _read_template(templates, "agents_md_template.md"),
        check=check,
    )
    # Claude Code's entry point: one import line leading to the routing file above. Without it the
    # harness falls back to `AGENTS.md` and announces the fallback at every session start.
    _write_template_owned(
        report, satellite / "CLAUDE.md",
        lambda: _read_template(templates, "claude_md_template.md"),
        check=check,
    )
    _write_if_missing(
        report, satellite / "kensaiapp.md",
        lambda: _stamp_instance_token(_read_template(templates, "kensaiapp_md_template.md"), plan.name),
        check=check,
    )
    _write_if_missing(
        report, satellite / ".gitignore",
        lambda: _extract_fenced_block(_read_template(templates, "gitignore_template.md")),
        check=check,
    )
    # The Claude Design brief — the instance's entry point into the design platform, at the root
    # because the tool's file selection starts from the connected folder. It names no product and
    # enumerates no input filenames by design: it resolves the product it is told from
    # `system/projects/<name>/project.md` and reads folders rather than expecting files. Stamped
    # here rather than authored later so a new instance starts from the proven shape; `[create]`,
    # so the owner's own edits to it are never overwritten by a re-run.
    _write_if_missing(
        report, satellite / "claude-design-instructions.md",
        lambda: _stamp_instance_token(
            _read_template(templates, "claude_design_instructions_template.md"), plan.name
        ),
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "michi.md",
        lambda: _stamp_instance_token(_read_template(templates, "michi_template.md"), plan.name),
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "nemawashi" / "README.md",
        lambda: _stamp_instance_token(_read_template(templates, "nemawashi_template.md"), plan.name),
        check=check,
    )
    # The instance setup seed — the three steps that follow this stamp (writing bar, then the ordered
    # experience pair), as a station checklist, so a new instance's seedbed is never empty and the
    # sequence is never re-typed from memory. The instance-altitude twin of the setup seed
    # `project-stamp` stamps into a project's seedbed. A recommendation: the owner may edit or
    # delete it, so its absence in an existing instance is not a gap.
    _write_seed_if_absent(
        report, satellite / "system" / "nemawashi", "instance-setup", plan.date,
        lambda: _stamp_instance_token(
            _read_template(templates, "instance_setup_seed_template.md"), plan.name
        ),
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "nemawashi" / "trail" / ".gitkeep",
        lambda: "",
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "nemawashi" / "unpicked" / ".gitkeep",
        lambda: "",
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "nemawashi" / "drop" / ".gitkeep",
        lambda: "",
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "shukuba" / "README.md",
        lambda: _stamp_instance_token(_read_template(templates, "system_shukuba_template.md"), plan.name),
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "shukuba" / "trail" / ".gitkeep",
        lambda: "",
        check=check,
    )

    # The three instance-shared doctrine files take the GENERIC word, never the satellite's own
    # name — `kensaiapp_doctrine_template.md`'s own note on why: inferring the name from the
    # instance produced the `tracker_doctrine.md` bug.
    _write_if_missing(
        report, satellite / "system" / "doctrine" / "kensaiapp_doctrine.md",
        lambda: _stamp_instance_token(
            _read_template(templates, "kensaiapp_doctrine_template.md"), GENERIC_DOMAIN_WORD
        ),
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "doctrine" / "ai_responsibility.md",
        lambda: _read_template(templates, "ai_responsibility_template.md").replace(
            "<scope>", GENERIC_DOMAIN_WORD
        ),
        check=check,
    )
    _write_if_missing(
        report, satellite / "system" / "doctrine" / "doctrine_structure.md",
        lambda: _stamp_instance_token(
            _read_template(templates, "doctrine_structure_template.md"), GENERIC_DOMAIN_WORD
        ),
        check=check,
    )


# --------------------------------------------------------------------------------------------
# Task 4 — stamp the role layer
# --------------------------------------------------------------------------------------------

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _strip_template_metadata(body: str) -> str:
    """Strip every leading HTML comment block (template metadata — the line-4 convention every
    core template follows) and normalize the blank-line runs their removal leaves behind. The
    stamped file carries none of this — only the content a reader of the instance should see."""
    body = _HTML_COMMENT_RE.sub("", body)
    body = body.lstrip("\n")
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body


def _split_frontmatter(text: str) -> str:
    """Return the body after a template's `---\\nversion: ...\\n---\\n` frontmatter block."""
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise SystemExit("error: template has no frontmatter block (--- ... ---) to split")
    return parts[2]


def _stamp_overlay(text: str, *, role: str, title: str, instance: str) -> str:
    body = _strip_template_metadata(_split_frontmatter(text))
    body = body.replace("<role>", role)
    body = body.replace("<Role Title>", title)
    body = body.replace("<instance>", instance)
    return f'---\nversion: "1.0.0"\n---\n\n{body}'


def _stamp_pm_overlay(text: str, instance: str) -> str:
    body = _strip_template_metadata(_split_frontmatter(text))
    body = body.replace("<instance>", instance)
    return f'---\nversion: "1.0.0"\n---\n\n{body}'


def _stamp_cross_role(text: str, instance: str) -> str:
    body = _strip_template_metadata(text)
    return body.replace("<instance>", instance)


def _stamp_role_layer(plan: SpawnPlan, report: Report, templates: Path, *, check: bool) -> None:
    role_templates = templates / "role-templates"
    loaders = plan.satellite / "system" / "loaders"

    for role, title in ROLE_TITLES.items():
        _write_if_missing(
            report, loaders / f"{role}.md",
            lambda role=role, title=title: _stamp_overlay(
                _read_template(role_templates, "overlay_template.md"),
                role=role, title=title, instance=plan.name,
            ),
            check=check,
        )

    _write_if_missing(
        report, loaders / "pm.md",
        lambda: _stamp_pm_overlay(_read_template(role_templates, "pm_overlay_template.md"), plan.name),
        check=check,
    )

    _write_if_missing(
        report, plan.satellite / "system" / "CROSS_ROLE.md",
        lambda: _stamp_cross_role(_read_template(role_templates, "cross_role_template.md"), plan.name),
        check=check,
    )


# --------------------------------------------------------------------------------------------
# Task 5 — the satellite's own settings.local.json
# --------------------------------------------------------------------------------------------


def _write_settings_local(plan: SpawnPlan, report: Report, *, check: bool) -> None:
    def render() -> str:
        dirs: list[str] = []
        if plan.product_path and os.path.isabs(plan.product_path):
            dirs = [os.path.normpath(plan.product_path)]
        data = {"permissions": {"allow": [], "additionalDirectories": dirs}}
        return json.dumps(data, indent=2) + "\n"

    # The host's settings.local.json is never opened — a mature host's copy carries dozens of
    # its own grants, none of which are this satellite's to inherit.
    _write_if_missing(report, plan.satellite / ".claude" / "settings.local.json", render, check=check)


# --------------------------------------------------------------------------------------------
# Task 6 — delegate the linking and the first project. Two jobs that already have owners; a
# second implementation of either is a second thing to keep in step.
# --------------------------------------------------------------------------------------------


def _invoke_link_satellite(plan: SpawnPlan) -> link_satellite.Report:
    """Call the linker in-process rather than as a subprocess, so its own `Report` — what it
    created, and what it repointed — comes back structured. `_commit_satellite` reads it to know
    which top-level path(s) the linker created that the spawn's own record never mentions (a
    producer's root `skills/` layer is the one that exists today; the linker writes the satellite's
    `.claude/settings.json` and links nothing else under `.claude/`). Never reimplements the linker's logic — only calls the function
    it already exposes."""
    try:
        return link_satellite.link_satellite(
            plan.satellite, plan.host, skills_mode=plan.skills_mode, check=False,
        )
    except SystemExit as exc:
        raise SystemExit(f"error: link_satellite.py failed: {exc}") from exc


def _invoke_stamp_project(plan: SpawnPlan) -> None:
    if not plan.project:
        return
    project_dir = plan.satellite / "system" / "projects" / plan.project
    if project_dir.exists():
        # Idempotence (Task 8): stamp_project.py itself refuses on an existing project
        # folder, which would otherwise turn a harmless resume into an aborted run.
        return

    resolution = skill_path.resolve_skill_dir(plan.host, "project-stamp")
    if resolution.status == skill_path.NOT_FOUND:
        raise SystemExit(
            f"error: no skill named 'project-stamp' found under the host ({plan.host})"
        )
    if resolution.status == skill_path.AMBIGUOUS:
        matches = "\n".join(str(m) for m in resolution.matches)
        raise SystemExit(
            f"error: 'project-stamp' is ambiguous under the host ({plan.host}) — matches:\n"
            f"{matches}"
        )
    script = resolution.path / "scripts" / "stamp_project.py"
    placement = "external" if plan.product_path and os.path.isabs(plan.product_path) else "internal"
    argv = [
        sys.executable, str(script), plan.project,
        "--placement", placement,
        "--instance-root", str(plan.satellite),
    ]
    if plan.product_path:
        argv += ["--product-path", plan.product_path]

    # CORE is BOUND here, not inherited. stamp_project.py resolves <CORE> from the environment
    # FIRST (its `_resolve_core`: the CORE env var, then the instance `.env`, then the `core/`
    # default), so an inherited value silently wins over the host we were told to stamp from — and a
    # session exports one at start-up. Left to inherit, a spawn run from a worktree reads templates
    # out of whatever checkout that session opened in: a template the branch adds is invisible, and
    # one it removes is still found. We already resolved the host; bind it rather than letting the
    # ambient environment decide.
    env = {**os.environ, "CORE": str(plan.host / "core")}

    result = subprocess.run(argv, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise SystemExit(
            f"error: stamp_project.py failed (exit {result.returncode}):\n"
            f"{result.stdout}{result.stderr}"
        )


# --------------------------------------------------------------------------------------------
# Task 7 — verify what was produced, then commit it. The script proves its own result rather
# than reporting success; each check is one the withdrawn skill listed as an instruction for a
# human, now a line that raises instead of a sentence a reader trusts.
# --------------------------------------------------------------------------------------------

# The core-referencing files this script authors — `kensaiapp_structure.md`'s §1 design
# principle scopes the "<CORE> indirection" drift-check (no literal `core/…`, no `~/.claude/…`)
# to skills / prompts / loaders / CONTEXT_PM / CROSS_ROLE / agents. Of what this script writes,
# only the role layer is in that set — AGENTS.md legitimately mentions `~/.claude/CLAUDE.md` in
# prose about the user's own global config, and scanning it would be a false positive, not a
# stricter check.
def _core_referencing_targets(plan: SpawnPlan) -> list[Path]:
    loaders = plan.satellite / "system" / "loaders"
    return [loaders / f"{role}.md" for role in ROLE_TITLES] + [
        loaders / "pm.md",
        plan.satellite / "system" / "CROSS_ROLE.md",
    ]


def _verify(plan: SpawnPlan) -> None:
    link_script = Path(__file__).resolve().parent / "link_satellite.py"
    result = subprocess.run(
        [
            sys.executable, str(link_script),
            "--satellite", str(plan.satellite),
            "--host", str(plan.host),
            "--skills-mode", plan.skills_mode,
            "--check",
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "error: verification failed — link_satellite.py --check did not return 0 against "
            f"the produced satellite:\n{result.stdout}{result.stderr}"
        )

    core_dir = plan.satellite / "core"
    if core_dir.exists():
        raise SystemExit(f"error: verification failed — a core/ directory exists in the satellite: {core_dir}")

    for path in _core_referencing_targets(plan):
        if not path.exists():
            raise SystemExit(f"error: verification failed — missing core-referencing file: {path}")
        text = path.read_text(encoding="utf-8")
        if "core/" in text:
            raise SystemExit(f"error: verification failed — literal 'core/…' path in {path}")
        if "~/.claude" in text:
            raise SystemExit(f"error: verification failed — literal '~/.claude/…' path in {path}")

    loaders = plan.satellite / "system" / "loaders"
    for role in list(ROLE_TITLES) + ["pm"]:
        path = loaders / f"{role}.md"
        text = path.read_text(encoding="utf-8")
        if plan.name not in text:
            raise SystemExit(f"error: verification failed — {path} does not name this instance ({plan.name})")
        if plan.host.name in text:
            raise SystemExit(f"error: verification failed — {path} names the host ({plan.host.name})")


def _repo_is_dirty(satellite: Path) -> bool:
    """Whether the satellite's own repo has anything uncommitted — the guard `_commit_satellite`
    is called behind. `report.would_change` alone is not enough: recreating a missing file with
    byte-identical content (Task 8, resume) produces a `report.created` entry but no git diff, and
    `git commit` with nothing staged fails even without `--allow-empty` being withheld on purpose.
    Checking git's own status is what makes "second run over a complete satellite" and "second
    run recreating a since-deleted-but-identical file" both correctly commit nothing."""
    result = subprocess.run(
        ["git", "-C", str(satellite), "status", "--porcelain"], capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def _is_gitignored(repo: Path, name: str) -> bool:
    """Whether the satellite's own `.gitignore` excludes `name` outright. `git add` refuses a
    path that is wholly ignored (exit 1) — not a directory holding *some* ignored content
    alongside real files (`.claude` is never wholly ignored; `git add .claude` stages what isn't
    and silently skips what is), only a path that is nothing but ignored content, such as `.env`.
    A candidate this run created but the satellite means to keep untracked is dropped here before
    it ever reaches the builder."""
    result = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "-q", "--", name], capture_output=True
    )
    return result.returncode == 0


def _derive_add_paths(plan: SpawnPlan, report: Report, link_report: link_satellite.Report) -> list[str]:
    """The genesis commit's staged set — every top-level entry the spawn's own record and the
    linker's name, read off both `Report`s rather than a fixed tuple someone has to remember to
    extend. `created` (freshly written this run) and `already` (found in place, this run or an
    earlier one) both count, and so does `updated` (a template-owned file this run rewrote): a resumed run over a satellite that drifted outside this tool — a
    raw filesystem move, a hand edit — still needs `system`/`.claude`/`skills` swept for whatever
    changed underneath, and `git add <dir>` recursively picks up a deletion or an untracked file
    the same way it picks up a fresh write. Every path is absolute under `plan.satellite`; its
    top-level component (`.claude`, `system`, a producer's root `skills` tree once a host has one, …) is
    what needs to reach the commit, regardless of how deep the actual write landed — staging the
    top-level name stages everything under it."""
    satellite = plan.satellite
    touched = (
        *report.created, *report.already, *report.updated,
        *link_report.created, *link_report.already, *link_report.repointed,
        *link_report.written,
    )
    top_level: set[str] = set()
    for p in touched:
        parts = Path(p).relative_to(satellite).parts
        if not parts:
            continue  # the satellite directory itself (Task 2's own `report.created` entry)
        if parts[0] == ".git":
            continue  # the git dir Task 2 creates — git already excludes it from every add
        top_level.add(parts[0])
    return [name for name in sorted(top_level) if not _is_gitignored(satellite, name)]


def _commit_satellite(
    plan: SpawnPlan, report: Report, link_report: link_satellite.Report, *, co_authored_by: str
) -> None:
    builder = Path(__file__).resolve().parent / "commit_builder.py"
    add_paths = _derive_add_paths(plan, report, link_report)
    subject = f"spawn-satellite: create {plan.name} as a shared-core satellite of {plan.host.name}"
    body_lines = [f"Skills mode: {plan.skills_mode}."]
    if plan.project:
        body_lines.append(f"Project scaffolded: {plan.project}.")
    body = "\n".join(body_lines)
    directional = f"Michi: none — spawned {plan.name} as a shared-core satellite of {plan.host.name}"

    argv = [
        sys.executable, str(builder),
        "--repo", str(plan.satellite),
        "commit",
        "--add", *add_paths,
        "--subject", subject,
        "--body", body,
        "--role", "Meta",
        "--directional", directional,
        "--surface", "Claude Code",
        "--co-authored-by", co_authored_by,
    ]
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"error: commit_builder.py failed to commit the satellite (exit {result.returncode}):\n"
            f"{result.stdout}{result.stderr}"
        )


def spawn(plan: SpawnPlan, *, check: bool = False, co_authored_by: str = DEFAULT_CO_AUTHORED_BY) -> Report:
    report = Report()
    templates = plan.host / "core" / "templates"

    _create_instance(plan, report, check=check)
    _stamp_instance_files(plan, report, templates, check=check)
    _stamp_role_layer(plan, report, templates, check=check)
    _write_settings_local(plan, report, check=check)

    if check:
        return report

    link_report = _invoke_link_satellite(plan)
    _invoke_stamp_project(plan)
    _verify(plan)
    if not plan.no_git and _repo_is_dirty(plan.satellite):
        # --no-git means there is no repo to commit into — the genesis commit is a property of
        # the satellite's own git history, which the caller explicitly opted out of. A clean repo
        # (a resumed run that changed nothing, or recreated a file with identical content) has
        # nothing for git commit to do, --allow-empty or not — that is the Task 8 property.
        _commit_satellite(plan, report, link_report, co_authored_by=co_authored_by)
    return report


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
