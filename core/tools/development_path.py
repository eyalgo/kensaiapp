#!/usr/bin/env python3
"""development_path.py — which repo and worktree a change's code and pipeline commits land in.

One question, answered deterministically from one source of truth: the `**Product path:**` line of
`system/projects/<project>/project.md` in the instance worktree. A relative value means the product
lives inside the instance repo (`relative` topology: one repo, one worktree, code and pipeline commits
share it). An absolute value means the product is its own git repo (`fixed` topology: code commits go
to `<product_repo>/.worktrees/<key>`, pipeline commits to the instance worktree, and delivery handles
both repos separately) — unless it names a directory of the instance repository itself, which is one
repo and so `relative`, whatever way the path was written. A leading `~/` is the home directory, the
way the chain launcher reads the same line, so it is absolute too.

Three commands share one resolver:

- `resolve`  — the full contract as JSON (or `key=value` text).
- `validate` — prove the contract is usable for a live flow run; exit 0 or a specific error code.
- `target`   — one projection of the contract: `code`, `pipeline` or `delivery`.

The tool resolves and validates only. It never commits, merges, runs tests, or authorizes delivery.

Stdlib only, like every other tool in this folder. Git is reached through the injected `Git`
collaborator, never by a `subprocess` call anywhere else, so a test can hand in a fake where a real
repository is not the point.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from typing import Protocol, Sequence, TextIO, TypedDict

__version__ = "1.1.0"

PRODUCT_PATH_FIELD = "**Product path:**"
WORKTREES_DIR = ".worktrees"

RELATIVE = "relative"
FIXED = "fixed"

TARGET_KINDS = ("code", "pipeline", "delivery")


class ToolError(Exception):
    """A failure the caller can act on: a stable `code` from the proposal's failure contract, and a
    `message` saying what was wrong, with the offending value, and what to do about it."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code)
        self.code = code
        self.message = message


class Git:
    """The read-only questions this tool asks git. Each answer is `None` when git cannot give one,
    so the caller — which knows which side of the contract it is resolving — picks the error."""

    def _ask(self, path: str, *args: str) -> str | None:
        result = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def toplevel(self, path: str) -> str | None:
        """The root of the working tree containing `path` — for a linked worktree, that worktree."""
        return self._ask(path, "rev-parse", "--show-toplevel")

    def main_worktree(self, path: str) -> str | None:
        """The main working tree of the repository `path` belongs to — the repository's identity,
        the same answer from the main checkout and from every linked worktree of it. `git worktree
        list` always lists the main working tree first."""
        listing = self._ask(path, "worktree", "list", "--porcelain")
        if not listing or not listing.startswith("worktree "):
            return None
        return listing.splitlines()[0][len("worktree "):]

    def branch(self, path: str) -> str | None:
        """The checked-out branch of the working tree containing `path`; `None` on a detached
        HEAD, which `rev-parse --abbrev-ref` would instead report as a branch named `HEAD`."""
        return self._ask(path, "symbolic-ref", "--quiet", "--short", "HEAD")


# --- parsing ------------------------------------------------------------------------------------


# One HTML comment closing the line; `_strip_trailing_comments` removes them one at a time.
_TRAILING_COMMENT = re.compile(r"\s*<!--(?:(?!-->).)*-->\s*$")


def _strip_trailing_comments(text: str) -> str:
    """`text` without the HTML comments that end it. A comment anywhere else stays, so the
    caller can refuse it rather than silently splice the text around it."""
    while True:
        stripped = _TRAILING_COMMENT.sub("", text)
        if stripped == text:
            return text.strip()
        text = stripped


_HOME_PREFIX = "~/"


def _expand_home(value: str, home: str | None) -> str:
    """`value` with a leading `~/` replaced by `home` — the one form the chain launcher expands
    (`<CORE>/launchers/chain-development/launcher.sh`, `"~"/*`). With no `home` given, or any
    other `~` form, the value is returned as written and refused by the check that follows."""
    if home and value.startswith(_HOME_PREFIX):
        return os.path.join(home, value[len(_HOME_PREFIX):])
    return value


def _check_product_path_value(kind: str, value: str) -> None:
    """Refuse a value that no topology can route: leftover comment markup, a `~` nothing
    expanded, or a relative value that climbs out of the instance tree."""
    if "<!--" in value or "-->" in value:
        raise ToolError("invalid-product-path",
                        f"**Product path:** value '{value}' has an HTML comment that does not end "
                        f"the line; only a trailing comment is allowed — move it to the line's end")
    if kind == FIXED:
        return
    if value.startswith("~"):
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{value}' starts with '~', which expands only as a "
                        f"leading '~/' and only when a home directory is known; write '~/<path>' "
                        f"or the absolute path instead")
    if os.path.normpath(value).split(os.sep)[0] == os.pardir:
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{value}' leaves the instance repository; a relative "
                        f"value must stay inside it — declare a product outside the instance by "
                        f"its absolute path")


def parse_product_path(content: str, home: str | None = None) -> tuple[str, str]:
    """`(kind, value)` from the first line of a project.md that starts with `**Product path:**`.

    The value is what follows the field, minus trailing HTML comments and surrounding
    whitespace, with a leading `~/` expanded against `home` when one is given. A leading `/`
    makes it `fixed`; anything else is `relative`. Only the first declaration is read — an
    empty one is an error, never a reason to look further down."""
    for line in content.splitlines():
        if line.startswith(PRODUCT_PATH_FIELD):
            value = _strip_trailing_comments(line[len(PRODUCT_PATH_FIELD):])
            if not value:
                break
            value = _expand_home(value, home)
            kind = FIXED if value.startswith("/") else RELATIVE
            _check_product_path_value(kind, value)
            return kind, value
    raise ToolError("missing-product-path",
                    "project.md does not declare **Product path:** with a value; add a line "
                    "starting '**Product path:** <path>' — relative for a product inside the "
                    "instance repo, absolute for a separate repo")


# --- repository identity ------------------------------------------------------------------------


def _product_repo(git: Git, product_path: str) -> str:
    """The repository a fixed `**Product path:**` names — which may be any directory inside it."""
    if not os.path.isdir(product_path):
        raise ToolError("product-repo-unresolved",
                        f"product path '{product_path}' does not exist or is not a directory; "
                        f"fix **Product path:** in project.md or clone the product there")
    product_repo = git.main_worktree(product_path)
    if product_repo is None:
        raise ToolError("product-repo-unresolved",
                        f"product path '{product_path}' is not inside a git repository; a fixed "
                        f"product must be its own git repo")
    return product_repo


class Repos(Protocol):
    """How repository identities are established — by git, or under `--no-check-git` by path
    layout alone. `resolve` is handed one and never knows which."""

    def instance_repo(self, worktree: str) -> str: ...

    def product_repo(self, product_path: str) -> str: ...

    def is_instance_repo(self, product_repo: str, instance_repo: str) -> bool:
        """Whether the repository `product_repo` returned is the instance repository itself — an
        absolute `**Product path:**` that names a directory of the instance, not a repo of its
        own."""
        ...


class GitRepos:
    """Repository identities from git: each is the main working tree of the repository the given
    path belongs to, so a linked worktree resolves to the checkout it was added from, and a fixed
    product path naming a subdirectory resolves to its repository's root."""

    def __init__(self, git: Git) -> None:
        self._git = git

    def instance_repo(self, worktree: str) -> str:
        instance_repo = self._git.main_worktree(worktree)
        if instance_repo is None:
            raise ToolError("instance-repo-unresolved",
                            f"instance worktree '{worktree}' is not inside a git repository; pass "
                            f"the change's worktree of the instance repo")
        return instance_repo

    def product_repo(self, product_path: str) -> str:
        return _product_repo(self._git, product_path)

    def is_instance_repo(self, product_repo: str, instance_repo: str) -> bool:
        """Git named both, so the same repository is the same main working tree. A separate
        repository nested inside the instance directory has a main working tree of its own."""
        return _same_path(product_repo, instance_repo)


class LayoutRepos:
    """`--no-check-git`: identities read off the path layout, and git never runs. The instance
    repo is the directory holding `.worktrees/` when the worktree sits in one (the layout the flow
    creates), else the worktree itself; a fixed product's repo is its declared path. Nothing here
    is proven — this is for debugging, never for a flow call."""

    def instance_repo(self, worktree: str) -> str:
        worktree = os.path.normpath(worktree)
        parent = os.path.dirname(worktree)
        if os.path.basename(parent) == WORKTREES_DIR:
            return os.path.dirname(parent)
        return worktree

    def product_repo(self, product_path: str) -> str:
        return os.path.normpath(product_path)

    def is_instance_repo(self, product_repo: str, instance_repo: str) -> bool:
        """With no git to ask, a product path inside the instance directory is taken to be the
        instance's own — compared by path component, so a sibling sharing its prefix is not."""
        product_repo, instance_repo = os.path.normpath(product_repo), os.path.normpath(instance_repo)
        return os.path.commonpath([product_repo, instance_repo]) == instance_repo


# --- the contract -------------------------------------------------------------------------------


class Contract(TypedDict):
    """The development-path contract, in the proposal's key order. Paths are absolute except
    `product_path`, which is the declared value as written — a leading `~/` expanded."""

    kind: str
    project: str
    key: str
    product_path: str
    instance_repo: str
    instance_worktree: str
    product_repo: str
    product_worktree: str
    code_repo: str
    code_worktree: str
    pipeline_repo: str
    pipeline_worktree: str
    delivery_repos: list[str]


def build_contract(*, kind: str, project: str, key: str, product_path: str, instance_repo: str,
                   instance_worktree: str, product_repo: str, product_worktree: str) -> Contract:
    """The one place the contract's shape lives. Code commits follow the product; pipeline commits
    always stay on the instance; delivery handles the product repo first when it is separate."""
    return {
        "kind": kind,
        "project": project,
        "key": key,
        "product_path": product_path,
        "instance_repo": instance_repo,
        "instance_worktree": instance_worktree,
        "product_repo": product_repo,
        "product_worktree": product_worktree,
        "code_repo": product_repo,
        "code_worktree": product_worktree,
        "pipeline_repo": instance_repo,
        "pipeline_worktree": instance_worktree,
        "delivery_repos": ["instance"] if kind == RELATIVE else ["product", "instance"],
    }


def resolve(content: str, instance_worktree: str, project: str, key: str,
            repos: Repos, home: str | None = None) -> Contract:
    """The contract from a project.md's text, with repository identities from `repos`.

    An absolute value naming a directory of the instance repository is `relative`: one repo, one
    worktree, one delivery repo. `product_path` still echoes the value as declared."""
    kind, product_path = parse_product_path(content, home)
    instance_repo = repos.instance_repo(instance_worktree)
    if kind == FIXED:
        product_repo = repos.product_repo(product_path)
        if repos.is_instance_repo(product_repo, instance_repo):
            kind = RELATIVE
    if kind == RELATIVE:
        product_repo, product_worktree = instance_repo, instance_worktree
    else:
        product_worktree = os.path.join(product_repo, WORKTREES_DIR, key)
    return build_contract(kind=kind, project=project, key=key, product_path=product_path,
                          instance_repo=instance_repo, instance_worktree=instance_worktree,
                          product_repo=product_repo, product_worktree=product_worktree)


def _read_project_doc(instance_worktree: str, project: str) -> str:
    """The text of `system/projects/<project>/project.md` in the instance worktree."""
    if not os.path.isdir(instance_worktree):
        raise ToolError("instance-worktree-missing",
                        f"instance worktree '{instance_worktree}' does not exist or is not a "
                        f"directory; pass the absolute path of the change's instance worktree")
    project_doc = os.path.join(instance_worktree, "system", "projects", project, "project.md")
    if not os.path.isfile(project_doc):
        raise ToolError("missing-project-doc",
                        f"project '{project}' has no project.md at '{project_doc}'; check --project "
                        f"against system/projects/ in the worktree")
    try:
        with open(project_doc, "r", encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as error:
        raise ToolError("missing-project-doc",
                        f"project.md at '{project_doc}' cannot be read as UTF-8 text: {error}"
                        ) from error


def resolve_from_paths(instance_worktree: str, project: str, key: str,
                       repos: Repos, home: str | None = None) -> Contract:
    """The contract for `<project>` and `<key>`, read from the instance worktree on disk."""
    content = _read_project_doc(instance_worktree, project)
    return resolve(content, instance_worktree, project, key, repos, home)


# --- validation ---------------------------------------------------------------------------------


def _same_path(first: str, second: str) -> bool:
    """Whether two paths name the same place once symlinks are followed — git reports resolved
    paths, a caller may not have passed one."""
    return os.path.realpath(first) == os.path.realpath(second)


def _require_worktree(git: Git, *, worktree: str, repo: str, key: str, side: str) -> None:
    """Prove `worktree` is a git worktree root, of `repo`, with branch `<key>` checked out.

    `side` is `instance` or `product`, and picks the error codes: a path git cannot place in any
    repository is `<side>-repo-unresolved`; a path that is not a worktree of `repo` — absent, a
    plain directory, or a worktree of some other repository — is `<side>-worktree-missing`."""
    remedy = (f"it must be a git worktree of '{repo}' on branch '{key}' — create one with "
              f"git -C '{repo}' worktree add '{worktree}' '{key}' (add -b if the branch is new)")
    if not os.path.isdir(worktree):
        raise ToolError(f"{side}-worktree-missing",
                        f"{side} worktree '{worktree}' does not exist; {remedy}")
    toplevel = git.toplevel(worktree)
    if toplevel is None:
        raise ToolError(f"{side}-repo-unresolved",
                        f"{side} worktree '{worktree}' is not inside a git repository; {remedy}")
    if not _same_path(toplevel, worktree):
        raise ToolError(f"{side}-worktree-missing",
                        f"'{worktree}' is not the root of a git worktree (git places it inside "
                        f"'{toplevel}'); {remedy}")
    owner = git.main_worktree(worktree)
    if owner is None or not _same_path(owner, repo):
        raise ToolError(f"{side}-worktree-missing",
                        f"'{worktree}' is a worktree of the repository at '{owner}', not of the "
                        f"{side} repository '{repo}'; {remedy}")
    branch = git.branch(worktree)
    if branch is None:
        raise ToolError("branch-topology-missing",
                        f"'{worktree}' has a detached HEAD; check out branch '{key}' there")
    if branch != key:
        raise ToolError("branch-topology-missing",
                        f"'{worktree}' is on branch '{branch}', expected '{key}'; pass the "
                        f"change's own key, or check out '{key}' there")


def _in_worktree(product_path: str, repo: str, worktree: str) -> str:
    """Where an in-repo product sits in the change's worktree. A relative value is read from the
    worktree root; an absolute one names the directory in the instance's main checkout, so it is
    re-rooted from `repo` into `worktree` — the change branch is what the commits land on."""
    if not os.path.isabs(product_path):
        return os.path.join(worktree, product_path)
    within = os.path.relpath(os.path.realpath(product_path), os.path.realpath(repo))
    return os.path.normpath(os.path.join(worktree, within))


def _require_in_repo_product(git: Git, *, product_path: str, repo: str, worktree: str) -> None:
    """Prove an in-repo `**Product path:**` names a directory of the instance worktree's own
    repository: present, not reached through a symlink out of the tree, and not a nested
    repository — any of which would send "in-repo" code commits somewhere else."""
    location = _in_worktree(product_path, repo, worktree)
    if not os.path.lexists(location):
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{product_path}' does not exist in the instance "
                        f"worktree '{worktree}'; create it on the change branch or fix project.md")
    real_worktree, real_location = os.path.realpath(worktree), os.path.realpath(location)
    if os.path.commonpath([real_worktree, real_location]) != real_worktree:
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{product_path}' resolves to '{real_location}', outside "
                        f"the instance worktree '{worktree}'; declare an outside product by its "
                        f"absolute path")
    if not os.path.isdir(location):
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{product_path}' in '{worktree}' is not a directory")
    toplevel = git.toplevel(location)
    if toplevel is None:
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{product_path}' is outside the working tree of "
                        f"'{worktree}' (git metadata, not files it tracks); point it at the "
                        f"product's own directory")
    if not _same_path(toplevel, worktree):
        raise ToolError("invalid-product-path",
                        f"**Product path:** '{product_path}' belongs to another working tree, at "
                        f"'{toplevel}', nested in the instance worktree; declare a separate product "
                        f"by its absolute path so its commits go to its own repository")


def validate_contract(contract: Contract, git: Git) -> None:
    """Raise a `ToolError` unless the contract is usable for a live flow run: every worktree it
    routes commits to is a real git worktree of the repository the contract names for it, on the
    change key's branch, and the declared product location is real — a directory of the instance
    repository for `relative`, a directory of `product_repo` for `fixed`."""
    key = contract["key"]
    _require_worktree(git, worktree=contract["instance_worktree"], repo=contract["instance_repo"],
                      key=key, side="instance")
    if contract["kind"] == RELATIVE:
        _require_in_repo_product(git, product_path=contract["product_path"],
                                 repo=contract["instance_repo"],
                                 worktree=contract["instance_worktree"])
    else:
        product_repo = _product_repo(git, contract["product_path"])
        if not _same_path(product_repo, contract["product_repo"]):
            raise ToolError("product-repo-unresolved",
                            f"product path '{contract['product_path']}' belongs to the repository "
                            f"at '{product_repo}', not to the contract's product repository "
                            f"'{contract['product_repo']}'")
        _require_worktree(git, worktree=contract["product_worktree"],
                          repo=contract["product_repo"], key=key, side="product")


# --- targets ------------------------------------------------------------------------------------


def check_target_kind(kind: str) -> None:
    """Refuse a `--kind` outside the three target families."""
    if kind not in TARGET_KINDS:
        raise ToolError("invalid-target-kind",
                        f"--kind '{kind}' is not one of {', '.join(TARGET_KINDS)}")


def target(contract: Contract, kind: str) -> dict[str, object]:
    """One projection of the contract: where code commits go, where pipeline commits go, or which
    repos delivery handles, in order."""
    check_target_kind(kind)
    if kind == "code":
        return {"repo": contract["code_repo"], "worktree": contract["code_worktree"]}
    if kind == "pipeline":
        return {"repo": contract["pipeline_repo"], "worktree": contract["pipeline_worktree"]}
    return {"repos": contract["delivery_repos"]}


# --- the command line ---------------------------------------------------------------------------

# Printable characters git refuses in a branch name (`git check-ref-format`), plus the space;
# control characters are refused separately.
_REF_FORBIDDEN = frozenset("~^:?*[\\ ")


def _absolute_path(value: str) -> str:
    """`--worktree`: absolute, and normalised so every path the contract prints is stable."""
    if not os.path.isabs(value):
        raise argparse.ArgumentTypeError(
            f"'{value}' is not an absolute path; pass the instance worktree's absolute path")
    return os.path.normpath(value)


def _project_name(value: str) -> str:
    """`--project`: one directory name under `system/projects/`, never a path out of it."""
    if not value.strip() or value in (os.curdir, os.pardir) or os.sep in value:
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a project name; pass one directory name from system/projects/")
    return value


def _change_key(value: str) -> str:
    """`--key`: it names the branch and the `.worktrees/<key>` directory, so it must be one path
    segment git accepts as a branch — a `..` key would make the product worktree the product's
    main checkout."""
    malformed = (not value or os.sep in value or value.startswith((".", "-")) or ".." in value
                 or value.endswith((".", ".lock")) or any(char in _REF_FORBIDDEN for char in value)
                 or any(ord(char) < 32 for char in value))
    if malformed:
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a change key; pass the change's own key — one branch-name "
            f"segment, the name of its change folder and of its .worktrees/<key> directory")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="development_path.py",
        description="Which repo and worktree a change's code and pipeline commits land in, derived "
                    "from project.md's **Product path:**.",
        epilog="Validation posture: `resolve` and `target` establish repository identities with git "
               "but do not prove the worktree/branch topology unless --strict is given; `validate` "
               "always proves it. --no-check-git runs no git at all and cannot be combined with "
               "`validate` or --strict.")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--worktree", required=True, type=_absolute_path,
                        help="absolute path to the instance worktree")
    common.add_argument("--project", required=True, type=_project_name,
                        help="project name under system/projects/<project>/")
    common.add_argument("--key", required=True, type=_change_key,
                        help="change key — the branch and .worktrees/<key> directory name")
    common.add_argument("--format", choices=["json", "text"],
                        help="output format (default: json; text for validate)")
    common.add_argument("--strict", action="store_true",
                        help="also prove every worktree exists, belongs to its repo and is on "
                             "<key>; always on for validate")
    common.add_argument("--pretty", action="store_true", help="indent JSON output")
    common.add_argument("--no-check-git", action="store_true",
                        help="resolve from the path layout only, running no git; for debugging, "
                             "never for flow calls")

    subparsers.add_parser("resolve", parents=[common], help="print the full contract")
    subparsers.add_parser("validate", parents=[common],
                          help="prove the contract is usable for a live flow run")
    target_parser = subparsers.add_parser("target", parents=[common],
                                          help="print one target family of the contract")
    # Checked by `check_target_kind`, not argparse `choices`, so a wrong value is the
    # `invalid-target-kind` error in the caller's --format rather than a usage message.
    target_parser.add_argument("--kind", required=True, metavar="{code,pipeline,delivery}",
                               help="code, pipeline or delivery")
    return parser


def render(payload: Mapping[str, object], fmt: str, pretty: bool) -> str:
    """JSON, or one `key=value` line per field with a list joined by commas."""
    if fmt == "json":
        return json.dumps(payload, indent=2 if pretty else None)
    return "\n".join(f"{name}={','.join(value) if isinstance(value, list) else value}"
                     for name, value in payload.items())


VALID: dict[str, object] = {"status": "valid"}


def _run(args: argparse.Namespace, git: Git, repos: Repos, home: str) -> Mapping[str, object]:
    """Carry out one command and return what it prints on success."""
    if args.command == "target":
        check_target_kind(args.kind)
    contract = resolve_from_paths(args.worktree, args.project, args.key, repos, home)
    if args.command == "validate" or args.strict:
        validate_contract(contract, git)
    if args.command == "target":
        return target(contract, args.kind)
    return contract if args.command == "resolve" else VALID


def _success(payload: Mapping[str, object], fmt: str, pretty: bool) -> str:
    """The success output: `validate`'s text form is the single word `valid`."""
    return "valid" if payload is VALID and fmt == "text" else render(payload, fmt, pretty)


def main(argv: Sequence[str] | None = None, *, git: Git | None = None,
         stdout: TextIO | None = None, stderr: TextIO | None = None,
         home: str | None = None) -> int:
    """The composition root: the only place a concrete `Git` and `Repos` are built, and the home
    directory a `~/` product path expands against is read from the environment.

    Success goes to stdout. A failure exits 1: in JSON it is `{error, message, project, key}` on
    stdout, where a JSON caller already reads; in text it is one `<code>: <message>` line on
    stderr, so a shell caller capturing stdout never mistakes it for a value."""
    git = git if git is not None else Git()
    home = home if home is not None else os.path.expanduser("~")
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help(err)
        return 1
    if args.no_check_git and (args.command == "validate" or args.strict):
        # Proposal: "Do not silently downgrade from strict validation to best-effort path
        # guessing" — so the contradiction is refused rather than one flag quietly winning.
        parser.error(f"--no-check-git skips every git check, and '{args.command}"
                     f"{' --strict' if args.strict else ''}' exists to run them; drop one of them")
    fmt = args.format or ("text" if args.command == "validate" else "json")
    repos: Repos = LayoutRepos() if args.no_check_git else GitRepos(git)

    try:
        payload = _run(args, git, repos, home)
    except ToolError as error:
        failure = error
    except Exception as error:  # noqa: BLE001 — a JSON caller still gets JSON on an unforeseen failure
        failure = ToolError("unknown", f"unexpected {type(error).__name__}: {error}; not a "
                                       f"failure this tool anticipates — check that git is on "
                                       f"PATH, then report the command line with this message")
    else:
        print(_success(payload, fmt, args.pretty), file=out)
        return 0

    if fmt == "json":
        print(render({"error": failure.code, "message": failure.message, "project": args.project,
                      "key": args.key}, fmt, args.pretty), file=out)
    else:
        print(f"{failure.code}: {failure.message}", file=err)
    return 1


if __name__ == "__main__":
    sys.exit(main())
