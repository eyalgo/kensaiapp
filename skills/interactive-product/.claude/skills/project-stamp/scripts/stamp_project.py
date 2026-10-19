#!/usr/bin/env python3
"""Scaffold a new managed project — the per-project tree of kensaiapp_structure.md §2.

Creates `system/projects/<name>/` and stamps it from the templates in
`<CORE>/templates/`:

    system/projects/<name>/
    ├── project.md                     # the Product path binding + execution fields
    ├── agari.md                       # 上がり — the project's "done" (declaration)
    ├── doctrine/
    │   ├── <name>_doctrine.md         # project domain doctrine
    │   └── ai_responsibility.md       # AI-vs-mechanical boundary, scope=<name>
    └── journey/                       # 根回し Nemawashi → 宿場 Shukuba → 飛び石 Tobiishi
        ├── nemawashi/                 # 根回し — seedbed (folder, one file per idea)
        │   ├── README.md              #   seedbed doctrine + lifecycle
        │   ├── <date>_define-the-product.md  #   the recommended definition chain, as a seed
        │   ├── unpicked/.gitkeep      #   the candidate pool, empty for a newborn seedbed
        │   ├── trail/.gitkeep         #   ripened-ideas bin (empty)
        │   └── drop/.gitkeep          #   killed-ideas bin (empty)
        ├── shukuba/                   # 宿場 — current station (folder)
        │   ├── README.md              #   station doctrine + lifecycle
        │   ├── parked/.gitkeep        #   parked-stations bin (empty)
        │   └── trail/.gitkeep         #   reached-stations bin (empty)
        └── tobiishi/                  # 飛び石 — change units
            └── trail/.gitkeep         #   crossed-stones bin (empty)

It does NOT create the product's `docs/fdr.md`, `docs/adr/` or `docs/nfdr.md`, or product code — those
travel with the product (§3), authored by the pipeline / user, never by setup.

`<CORE>` resolution mirrors the `resolve_core.py` SessionStart hook: read the `CORE`
env var (exported by the hook), else read `CORE=` from the instance `.env`, else the
`core/` default — so the script works both inside a session and standalone.

Stdlib-only. Refuses to touch an existing project folder (create-if-missing, never
overwrite — the `[create]` disposition).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

DEFAULT_CORE = "core/"

# Templates → the project-relative path each stamps into. The path is a format
# string over {name} and {date}; the seed needs {date} because the seedbed names
# every idea <YYYY-MM-DD>_<slug>.md.
# Files in TOKEN_FILES take a plain token replace ({<project>,<name>,<scope>} → name);
# project.md is built by field substitution to keep the template's inline comments.
TOKEN_FILES = [
    ("project-templates/agari_template.md", "agari.md"),
    ("project_doctrine_template.md", "doctrine/{name}_doctrine.md"),
    ("ai_responsibility_template.md", "doctrine/ai_responsibility.md"),
    ("journey_shukuba_template.md", "journey/shukuba/README.md"),
    ("journey_nemawashi_template.md", "journey/nemawashi/README.md"),
    # The project's PM context — the only per-role context a kensaiapp has. Created as the
    # template's placeholder and nothing more: the change lifecycle owns its content
    # (`tobiishi-open` overwrites it, `tobiishi-seal` marks it Sealed), so scaffold's job is
    # that the file exists from creation rather than appearing at the first change.
    ("context_template.md", "contexts/CONTEXT_PM.md"),
    # The setup seed — the recommended definition chain (PRD → Agari → SRS → SDD),
    # stamped so a new project's seedbed is never empty and the chain is never
    # re-typed from memory. A recommendation: the owner may edit or delete it.
    ("project-templates/setup_seed_template.md",
     "journey/nemawashi/{date}_define-the-product.md"),
]

# project.md fields: (label, new value). The value between `**Label:**` and the
# trailing `<!-- comment -->` is replaced; the explanatory comment is preserved.
PROJECT_FIELDS_ORDER = ["Product path", "Source material", "Type", "Definition", "Manages",
                        "Execution type", "Package slug", "Test command"]

# The card's Definition: follows from its Type: unless the caller names one — a no-code product
# is defined by its PRD and Agari alone (--type's own help), so the sweep build_idea.py derives
# from this line runs chain-agari for it, never the full chain.
DEFINITION_FOR_TYPE = {"software": "full", "no-code": "prd-agari"}


def _instance_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _read_core_from_env(env_path: str) -> str | None:
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == "CORE":
                    return value.strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def _resolve_core(instance_root: str, explicit: str | None) -> str:
    raw = explicit or os.environ.get("CORE") or _read_core_from_env(
        os.path.join(instance_root, ".env")
    ) or DEFAULT_CORE
    if os.path.isabs(raw):
        return os.path.normpath(raw)
    return os.path.normpath(os.path.join(instance_root, raw))


def _stamp_tokens(text: str, name: str) -> str:
    for token in ("<project>", "<name>", "<scope>"):
        text = text.replace(token, name)
    return text


def _stamp_project_md(template: str, values: dict[str, str]) -> str:
    """Replace the title and each field's value, preserving inline `<!-- -->` comments."""
    out = []
    for raw in template.splitlines():
        line = raw
        title = re.match(r"^(# Project Context — ).*$", line)
        if title:
            line = f"{title.group(1)}{values['name']}"
        else:
            for label in PROJECT_FIELDS_ORDER:
                fm = re.match(rf"^(\*\*{re.escape(label)}:\*\* +)(\S.*?)(\s+<!--.*)$", line)
                if fm:
                    line = f"{fm.group(1)}{values[label]}{fm.group(3)}"
                    break
        out.append(line)
    return "\n".join(out) + "\n"


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _ensure_external_grant(instance_root: str, product_path: str) -> str:
    """For an absolute (external) product path, add the directory grant to
    .claude/settings.local.json (host-local, gitignored). Merge-only: never
    clobber the user's `allow`/other keys, create file/key if absent. Returns a
    one-line status. In-repo (relative) products need no grant — never called then.
    """
    settings_path = os.path.join(instance_root, ".claude", "settings.local.json")
    grant = os.path.normpath(product_path)

    data: dict = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as fh:
                data = json.load(fh) or {}
        except (OSError, ValueError) as exc:
            return (f"WARNING: could not read {settings_path} ({exc}); "
                    f"external grant NOT set — add {grant!r} to "
                    "permissions.additionalDirectories by hand.")
        if not isinstance(data, dict):
            return (f"WARNING: {settings_path} is not a JSON object; external grant "
                    f"NOT set — add {grant!r} to permissions.additionalDirectories by hand.")

    perms = data.setdefault("permissions", {})
    dirs = perms.setdefault("additionalDirectories", [])
    if not isinstance(dirs, list):
        return (f"WARNING: permissions.additionalDirectories in {settings_path} is not "
                f"a list; external grant NOT set — add {grant!r} by hand.")
    if grant in dirs:
        return f"external grant already present: {grant}"

    dirs.append(grant)
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    return f"external grant added to .claude/settings.local.json: {grant}"


def _external_repo_status(product_path: str) -> str:
    """External products live in their own git repo — the two-repo
    pipeline flow (routed by development_path.py) needs it: worktrees and branches are cut in the
    product repo, and the PRD lands there as its first commit. Report whether the
    product path is already a git repo; if not, tell the caller to `git init` it.
    Plain `.git` check (no subprocess) — works even where git isn't on PATH.
    Non-fatal: the pointer scaffolds regardless; this only surfaces the gap."""
    if os.path.exists(os.path.join(product_path, ".git")):
        return f"product repo OK: {product_path} is a git repo"
    return (f"WARNING: {product_path} is not a git repo yet — the external "
            f"pipeline flow needs one. Run: git init {product_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a kensaiapp project (§2 tree).")
    ap.add_argument("name", help="project name / slug (folder under system/projects/)")
    ap.add_argument("--placement", required=True, choices=("internal", "external"),
                    help="Where the product lives (intent). internal → in this instance "
                         "(relative path, defaults to products/<name>); external → its own "
                         "repo (absolute path, required, gets the directory grant).")
    ap.add_argument("--product-path", default=None,
                    help="Product path binding. Omit for internal (defaults to "
                         "products/<name>); required + absolute for external.")
    ap.add_argument("--type", default="software", choices=("software", "no-code"),
                    help="What the product is: software (the whole product chain) or no-code "
                         "(PRD and Agari only). Default: software.")
    ap.add_argument("--definition", default=None, choices=("full", "prd-agari", "none"),
                    help="The card's Definition: line, which names the definition chain. "
                         "Default: from --type — full for software, prd-agari for no-code.")
    ap.add_argument("--manages", default="none",
                    help="What the product looks after outside itself — a repository, an "
                         "account, a domain — or none. Default: none.")
    ap.add_argument("--source-material", default="<blank>",
                    help="The card's Source material: line, which product-prd reads. "
                         "Default: <blank>.")
    ap.add_argument("--execution-type", default="headless",
                    help="headless (claude -p) | docker. Default: headless.")
    ap.add_argument("--test-command", default="pytest tests/",
                    help='Test command. Default: "pytest tests/".')
    ap.add_argument("--core", default=None,
                    help="Override <CORE> path (else CORE env / .env / core/ default).")
    ap.add_argument("--instance-root", default=None,
                    help="Instance repo root (else CLAUDE_PROJECT_DIR / cwd).")
    ap.add_argument("--date", default=None,
                    help="Date for the setup seed's filename, YYYY-MM-DD. "
                         "Default: today. Explicit so a test can pin it.")
    args = ap.parse_args()

    name = args.name.strip()
    if not name or "/" in name or name.startswith("."):
        print(f"error: invalid project name {name!r}", file=sys.stderr)
        return 2

    # Resolve the product path from the stated intent — the intent drives both the
    # path shape and (below) whether the external directory grant is set.
    if args.placement == "internal":
        product_path = args.product_path or f"products/{name}"
        if os.path.isabs(product_path):
            print("error: internal placement needs a relative path — omit --product-path "
                  f"to default to products/{name}, or pass a relative path.",
                  file=sys.stderr)
            return 2
        if product_path.startswith(".."):
            print("error: a relative Product path must not start with '../' "
                  "(it escapes the worktree). Use products/<name>.", file=sys.stderr)
            return 2
    else:  # external
        if not args.product_path:
            print("error: external placement needs --product-path <absolute path> "
                  "(the product's own repo).", file=sys.stderr)
            return 2
        product_path = args.product_path
        if not os.path.isabs(product_path):
            print("error: external placement needs an absolute path; got relative "
                  f"{product_path!r}. Point --product-path at the product repo's absolute path.",
                  file=sys.stderr)
            return 2

    instance_root = os.path.abspath(args.instance_root or _instance_root())
    core = _resolve_core(instance_root, args.core)
    templates = os.path.join(core, "templates")
    if not os.path.isdir(templates):
        print(f"error: template dir not found: {templates}", file=sys.stderr)
        return 2

    target = os.path.join(instance_root, "system", "projects", name)
    if os.path.exists(target):
        print(f"error: project already exists: {target}\n"
              "  (create-if-missing, never overwrite — nothing changed.)",
              file=sys.stderr)
        return 3

    def tpl(fname: str) -> str:
        with open(os.path.join(templates, fname), "r", encoding="utf-8") as fh:
            return fh.read()

    created: list[str] = []

    # project.md — field substitution (preserves inline comments).
    project_md = _stamp_project_md(tpl("project_template.md"), {
        "name": name,
        "Product path": product_path,
        "Source material": args.source_material.strip() or "<blank>",
        "Type": args.type,
        "Definition": args.definition or DEFINITION_FOR_TYPE[args.type],
        "Manages": args.manages.strip() or "none",
        "Execution type": args.execution_type,
        "Package slug": name,
        "Test command": args.test_command,
    })
    p = os.path.join(target, "project.md")
    _write(p, project_md)
    created.append(p)

    # Token-substituted files.
    date = args.date or datetime.date.today().isoformat()
    for tpl_name, rel in TOKEN_FILES:
        rel = rel.format(name=name, date=date)
        content = _stamp_tokens(tpl(tpl_name), name)
        p = os.path.join(target, rel)
        _write(p, content)
        created.append(p)

    # Journey directory stubs — the empty bins the lifecycle fills later
    # (the nemawashi candidate pool, and the five record bins: nemawashi trail + drop,
    # shukuba parked + trail, tobiishi trail). The active Shukuba and Tobiishi
    # are user/pipeline-authored, never by setup; the nemawashi is the exception —
    # it starts with the setup seed stamped above.
    for rel in (
        "journey/nemawashi/unpicked/.gitkeep",
        "journey/nemawashi/trail/.gitkeep",
        "journey/nemawashi/drop/.gitkeep",
        "journey/shukuba/parked/.gitkeep",
        "journey/shukuba/trail/.gitkeep",
        "journey/tobiishi/trail/.gitkeep",
    ):
        gitkeep = os.path.join(target, *rel.split("/"))
        _write(gitkeep, "")
        created.append(gitkeep)

    print(f"Scaffolded project '{name}' at {target}")
    print(f"  <CORE> = {core}")
    for p in created:
        print(f"  + {os.path.relpath(p, instance_root)}")

    # External product → derive the Claude Code directory grant so the pipeline can
    # reach the product repo. Keyed off the stated intent, not an inferred path shape.
    if args.placement == "external":
        print(f"  {_ensure_external_grant(instance_root, product_path)}")
        print(f"  {_external_repo_status(product_path)}")
    else:
        print("  internal product — no external grant needed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
