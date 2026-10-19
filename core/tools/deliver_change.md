---
version: "1.2.0"
---

# Deliver a development-path contract

This document defines the caller interface for `core/tools/deliver_change.py` and supplies
two complete temporary-repository recipes.
The executable accepts a development-path contract, per-repository merge metadata and a caller's
seal action (`core/tools/deliver_change.py:L645-L657`, `main`).

## Invoke the executable

Use the public command from `core/tools/deliver_change.py:L645-L654`, `main`:

```sh
python3 /absolute/core/tools/deliver_change.py \
  --contract /absolute/contract.json \
  --merges /absolute/merges.json \
  --seal-action /absolute/seal.json \
  [--builder /absolute/commit_builder.py]
```

The brackets mark the optional argument; omit them when invoking the command.
The default builder is the executable's sibling `commit_builder.py`
(`core/tools/deliver_change.py:L650-L654`, `main`).
The CLI resolves the three input paths and builder path once against its invocation directory
(`core/tools/deliver_change.py:L652-L656`, `main`).
Place caller input files outside every contract worktree scheduled for removal
(`core/tools/deliver_change.py:L595-L598`, `Delivery.deliver`).
For separate repositories, place the builder outside the product change worktree because product
cleanup precedes instance delivery (`core/tools/deliver_change.py:L599-L601,L624-L630`,
`Delivery.deliver`).

## Supply all contract fields

Use the complete object returned by the public `development_path.build_contract` or path resolver;
the shape belongs to `core/tools/development_path.py:L242-L279`, `Contract` and `build_contract`.
Every field is required, every field except `delivery_repos` is a nonempty string, and unknown fields
refuse (`core/tools/deliver_change.py:L327-L346`, `Delivery._contract`).

| Field | Value |
| --- | --- |
| `kind` | `relative` for one repository; `fixed` for separate repositories |
| `project` | Caller project name |
| `key` | Legal change branch name, different from `main` |
| `product_path` | Declared product path; absolute for `fixed` |
| `instance_repo` | Absolute primary instance checkout |
| `instance_worktree` | Absolute registered instance change worktree |
| `product_repo` | Absolute primary product checkout |
| `product_worktree` | Absolute registered product change worktree |
| `code_repo` | Same as `product_repo` |
| `code_worktree` | Same as `product_worktree` |
| `pipeline_repo` | Same as `instance_repo` |
| `pipeline_worktree` | Same as `instance_worktree` |
| `delivery_repos` | Exactly `["instance"]` for `relative`; exactly `["product", "instance"]` for `fixed` |

The table's field types and aliases come from
`core/tools/development_path.py:L242-L279`, `Contract` and `build_contract`;
the branch, topology and absolute-path restrictions come from
`core/tools/deliver_change.py:L334-L357`, `Delivery._contract`.
Relative delivery requires the same repository and change worktree for both roles
(`core/tools/deliver_change.py:L347-L350`, `Delivery._contract`).
Fixed delivery requires distinct repositories and an absolute product path
(`core/tools/deliver_change.py:L351-L353`, `Delivery._contract`).
Aliases and role order must equal the public projection; reversed, duplicate, missing or unknown roles
refuse (`core/tools/deliver_change.py:L342-L346`, `Delivery._contract`).
The repository, source branch `key` and target branch `main` are derived from the contract and cannot
be overridden in merge metadata (`core/tools/deliver_change.py:L168-L171,L360-L369`,
`Processes.builder` and `Delivery._inputs`).

## Supply merge metadata and a literal seal action

The merges JSON is an object keyed by exactly the contract's delivery roles
(`core/tools/deliver_change.py:L360-L372`, `Delivery._inputs`).
Each value has the following schema
(`core/tools/deliver_change.py:L231-L234,L360-L372`, `_REQUIRED_MERGE_FIELDS`,
`_OPTIONAL_MERGE_FIELDS` and `Delivery._inputs`):

| Fields | Type and requirement |
| --- | --- |
| `description`, `merge_context`, `surface` | Required strings |
| `actor` or `authorizer` | Exactly one required string; builder validates identity/authorization |
| `co_authored_by`, `reasoning_effort`, `claude_session` | Optional strings |
| `branch_commits`, `bump` | Optional arrays of strings, preserving order |

Unknown fields and wrong types refuse before delivery
(`core/tools/deliver_change.py:L360-L372,L609-L622`, `Delivery._inputs` and `Delivery.deliver`).
Values, ordered lists and optional absence pass through to the builder without substituted
attribution or effort (`core/tools/deliver_change.py:L168-L180`, `Processes.builder`).
Authorization, effort, commit-entry and bump policy remain the builder's;
the tool checks every role through `merge --check-only` before the first merge, except an empty
product change branch, which is not merged
(`core/tools/deliver_change.py:L415-L423,L609-L619`, `Delivery._check` and `Delivery.deliver`).
Supply builder bump entries in its public `path=level` format, with `level` one of
`patch`, `minor` or `major` (`core/tools/commit_builder.py:L1417-L1464`, `BUMP_LEVELS`, `_split_bump` and `_bump_refusal`).

A relative merges object may be:

```json
{
  "instance": {
    "description": "deliver example",
    "merge_context": "verified example",
    "surface": "Codex",
    "actor": "pm",
    "co_authored_by": "gpt-6.1-sol <noreply@openai.com>",
    "reasoning_effort": "high",
    "branch_commits": ["example implementation"],
    "bump": ["version.py=patch"]
  }
}
```

For fixed delivery, supply both `product` and `instance` records; the records may use distinct
attribution and bumps (`core/tools/deliver_change.py:L360-L372,L415-L421`,
`Delivery._inputs` and `Delivery._check`).
The seal JSON carries exactly one field, `argv`, a nonempty string array whose first element names a
reachable executable (`core/tools/deliver_change.py:L373-L376,L604-L607`,
`Delivery._inputs` and `Delivery.deliver`):

```json
{"argv": ["python3", "/absolute/caller-seal.py", "literal argument ; $"]}
```

The tool executes the argv once, without a shell, in `instance_worktree`
(`core/tools/deliver_change.py:L111-L121,L182-L183,L624-L630`,
`Processes.run`, `Processes.seal` and `Delivery.deliver`).
The caller's action must exit zero and leave a clean registered worktree on `key`, without
`MERGE_HEAD`, at a new commit extending its recorded tip
(`core/tools/deliver_change.py:L451-L481`, `Delivery._seal` and `Delivery._live_change`).
The executable owns no seal content
(`core/tools/deliver_change.py:L2-L7`, module contract).

## Validate targets, observe landing, then remove only delivered worktrees

Each primary checkout must be its repository root on `main`, and each change worktree must be a
registered root owned by that repository on `key`
(`core/tools/deliver_change.py:L392-L399`, `Delivery._live`).
Both checkouts must have no unfinished merge
(`core/tools/deliver_change.py:L400-L400`, `Delivery._live`).
A change worktree must have no tracked, staged or untracked edits, because nothing but this change
works in it (`core/tools/deliver_change.py:L404-L406`, `Delivery._live`).
A primary checkout is shared with every other walk in its repository, so the delivery refuses only
two kinds of entry there.
The first is any staged entry, wherever it sits, because a merge commit records the whole index
(`core/tools/deliver_change.py:L401-L402,L378-L388`, `Delivery._live`).
The second is a tracked edit or an untracked file whose path collides with a path the merge writes
(`core/tools/deliver_change.py:L401-L402,L378-L388`, `Delivery._live`).
The paths the merge writes are every path the change branch changed since it left `main`, plus every
path named by a `bump` entry in the role's merges object.
An entry collides when its path equals one of those paths, or when one of the two paths is a folder
that contains the other.
Every check reads both sets of paths again, so the instance merge after the seal and the cleanup
recheck judge the branch as it then stands.
Any other uncommitted entry in a primary checkout is left on disk unchanged, and no merge commit
carries it.
A change branch already contained in `main` refuses instead of becoming a successful delivery, unless it is an empty product change branch on a fixed delivery
(`core/tools/deliver_change.py:L487-L489,L613-L619`, `Delivery._merge` and `Delivery.deliver`).
A product change branch is empty when `main` contains it and its reflog, the log Git keeps of the updates made to the branch, holds exactly one entry: the branch's creation, whose message begins `branch: Created from` and whose commit is the branch's current tip
(`core/tools/deliver_change.py:L209-L218,L236,L409-L413`, `Processes.reflog`, `_CREATION_MESSAGE` and `Delivery._empty_branch`).
Containment alone cannot tell an empty branch from a branch fast-forwarded into `main` by hand, because both point at a commit `main` contains, so the reflog decides
(`core/tools/deliver_change.py:L613-L616`, `Delivery.deliver`).
A contained product change branch whose reflog is missing, holds any other entry (a commit, a reset, or a fast-forward made by hand), or records its creation at a commit other than its tip refuses like any other contained branch
(`core/tools/deliver_change.py:L409-L413,L613-L616`, `Delivery._empty_branch` and `Delivery.deliver`).
The exception is the product role's alone
(`core/tools/deliver_change.py:L614`, `Delivery.deliver`).
An instance change branch contained in `main` refuses whatever its reflog holds, on a relative delivery and on a fixed one
(`core/tools/deliver_change.py:L487-L489,L613-L616`, `Delivery._merge` and `Delivery.deliver`).
An empty product change branch is still held to the clean-worktree rule above, so one whose change worktree holds a tracked, staged or untracked edit refuses
(`core/tools/deliver_change.py:L392-L406,L612`, `Delivery._live` and `Delivery.deliver`).
Readable invocation-local Git Trace2 EVENT capability is required before delivery
(`core/tools/deliver_change.py:L425-L433,L608-L608`, `Delivery._trace_preflight` and
`Delivery.deliver`).

Relative delivery runs seal → instance merge → instance cleanup
(`core/tools/deliver_change.py:L624-L630`, `Delivery.deliver`).
Fixed delivery runs product merge → product cleanup → seal → instance merge → instance cleanup
(`core/tools/deliver_change.py:L624-L630`, `Delivery.deliver`).

With an empty product change branch, fixed delivery runs product cleanup → seal → instance merge → instance cleanup
(`core/tools/deliver_change.py:L624-L630`, `Delivery.deliver`).
An empty product change branch is not merged, and the builder's check does not run on it
(`core/tools/deliver_change.py:L613-L618,L625-L626`, `Delivery.deliver`).
Product cleanup removes its change worktree and its branch and leaves the product repository's `main` where it was
(`core/tools/deliver_change.py:L541-L585,L627`, `Delivery._cleanup` and `Delivery.deliver`).
Its merges record is still required and validated, and a `bump` it carries applies to no merge
(`core/tools/deliver_change.py:L360-L372,L612`, `Delivery._inputs` and `Delivery.deliver`).

The tool rechecks each role and builder inputs at its merge boundary
(`core/tools/deliver_change.py:L483-L492`, `Delivery._merge`).
A landing requires a changed `main` tip whose two ordered parents are the prior `main` tip and the
intended branch tip, with no `MERGE_HEAD`
(`core/tools/deliver_change.py:L491-L512`, `Delivery._merge`).
Process exit alone is insufficient proof
(`core/tools/deliver_change.py:L522-L537`, `Delivery._merge`).

Cleanup refuses tracked or untracked leftover content in the change worktree, rechecks the primary
checkout by the rule above, removes ignored content with the worktree
exactly as non-force removal does (a suite's caches never halt a landed delivery), uses non-force
worktree removal and safe
branch deletion, then independently observes disk, registration and ref absence
(`core/tools/deliver_change.py:L185-L190,L220-L224,L541-L585`,
`Processes.remove_worktree`, `Processes.delete_branch`, `Delivery._survivors` and `Delivery._cleanup`).
A cleanup failure reports every observed survivor or unavailable evidence and stops later steps
(`core/tools/deliver_change.py:L541-L585,L624-L636`, `Delivery._survivors`,
`Delivery._cleanup` and `Delivery.deliver`).

## Read the terminal result and retained recovery state

Successful delivery exits 0 and prints exactly this block for relative delivery
(`core/tools/deliver_change.py:L660-L669`, `main`):

```text
delivery: complete
delivered: instance
cleanup: complete
```

For fixed success, the delivered line is `delivered: product,instance`
(`core/tools/deliver_change.py:L624-L631,L663-L666`, `Delivery.deliver` and `main`).
A fixed delivery whose product change branch was empty, as § *Validate targets, observe landing, then remove only delivered worktrees* defines it, exits 0 and prints exactly this block
(`core/tools/deliver_change.py:L631-L632,L660-L669`, `Delivery.deliver` and `main`):

```text
delivery: complete
delivered: instance
empty: product
cleanup: complete
```

The `empty: product` line says the product change branch carried no commits of its own and was removed without a merge
(`core/tools/deliver_change.py:L664-L665`, `main`).
No other success block and no halt block carries an `empty:` line
(`core/tools/deliver_change.py:L631-L636,L664-L665`, `Delivery.deliver` and `main`).
A delivery halt exits 1 and prints this block, with its actual code and observed roles
(`core/tools/deliver_change.py:L660-L669`, `main`):

```text
delivery: halt
halt: deliver-precondition-failed
delivered: none
cleanup: incomplete
```

Delivered roles are comma-separated in observed landing order, or `none`; `cleanup: incomplete`
also covers a halt before cleanup was attempted
(`core/tools/deliver_change.py:L508-L512,L663-L666`, `Delivery._merge` and `main`).
A halt after an empty product change branch was removed prints the halt block above, with `delivered:` naming only the roles whose merge landed
(`core/tools/deliver_change.py:L440-L449,L633-L636`, `Delivery._halt` and `Delivery.deliver`).
That halt keeps its own code and is never reported as `instance-merge-after-product`, because no product merge landed
(`core/tools/deliver_change.py:L443-L445`, `Delivery._halt`).
Captured child output and actionable diagnostics go to stderr, leaving one terminal block on stdout
(`core/tools/deliver_change.py:L435-L449,L660-L668`, `Delivery._capture`,
`Delivery._halt` and `main`).
Argparse usage errors retain argparse's own interface
(`core/tools/deliver_change.py:L645-L651`, `main`).

The six public codes and their decisions come from
`core/tools/deliver_change.py:L41-L47,L440-L449,L466-L467,L514-L537,L582-L585,L620-L636`,
`Halt`, `Delivery._halt`, `Delivery._seal`, `Delivery._merge`, `Delivery._cleanup` and
`Delivery.deliver`:

| Halt code | Cause |
| --- | --- |
| `deliver-precondition-failed` | Invalid/unreadable input, unusable runtime/targets, containment or builder refusal |
| `merge-conflict` | Unlanded merge with observed unmerged index entries |
| `merge-hook-failed` | Unlanded merge with correlated blocking-hook rejection in invocation-local Trace2 |
| `instance-merge-after-product` | Product landed, instance remains unlanded; replaces later non-teardown failure |
| `teardown-failed` | Required cleanup failed or absence could not be proved |
| `delivery-failed` | Seal failure, process/evidence failure, or unproved merge outside the preceding classes |

`seal-failed` is a diagnostic cause, not a seventh halt code
(`core/tools/deliver_change.py:L41-L47,L466-L467`, `Halt` and `Delivery._seal`).
Partial delivery diagnostics retain the underlying cause, landed product merge SHA and instance
recovery worktree (`core/tools/deliver_change.py:L440-L449`, `Delivery._halt`).
Teardown failure keeps its own code even after product landing
(`core/tools/deliver_change.py:L443-L445`, `Delivery._halt`).
A verified merge may be counted as delivered even when its process later fails or trace becomes
unreadable; that halt keeps recovery state and does not proceed to cleanup
(`core/tools/deliver_change.py:L508-L527`, `Delivery._merge`).
The tool neither aborts failed merges nor rolls back product landing, retries a seal, joins audits,
advances branches, edits journey content or serializes competing callers
(`core/tools/deliver_change.py:L587-L636`, `Delivery.deliver`).
Callers own those policies and any later recovery, outside the operation in
`core/tools/deliver_change.py:L587-L636`, `Delivery.deliver`.

## Run a complete one-repository recipe

Run the following Python block from the instance root where `core/tools/` is available.
The recipe constructs disposable repositories, invokes the executable directly, and asserts its
terminal block, actual builder merge, ordered parents, seal inclusion and disk/list/ref absence
using the assertions adapted from `core/tools/test_deliver_change.py:L57-L201,L204-L206`,
`Scenario`, `assert_success` and `test_single_repo_seals_then_delivers_once`.

```python
import json
import subprocess
import sys
import tempfile
from pathlib import Path

tools = Path("core/tools").resolve()
builder = tools / "commit_builder.py"
delivery = tools / "deliver_change.py"
key = "example-delivery"
roles = ["instance"]

def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], check=check,
                          capture_output=True, text=True)

def commit(repo, name, content):
    (repo / name).write_text(content)
    git(repo, "add", name)
    git(repo, "commit", "-qm", name)

with tempfile.TemporaryDirectory(prefix="delivery-example-") as directory:
    root = Path(directory).resolve()
    events = root / "events.jsonl"
    repos, worktrees, before, intended = {}, {}, {}, {}
    for role in roles:
        repo = root / (role + " repo")
        repo.mkdir()
        git(repo, "init", "-qb", "main")
        git(repo, "config", "user.name", "Example")
        git(repo, "config", "user.email", "example@example.invalid")
        git(repo, "config", "core.hooksPath", str(root / (role + "-hooks")))
        commit(repo, "shared", "base\n")
        wt = root / (role + " change")
        git(repo, "worktree", "add", "-qb", key, str(wt))
        commit(wt, "shared", role + " implementation\n")
        repos[role], worktrees[role] = repo, wt
        before[role] = git(repo, "rev-parse", "main").stdout.strip()
        intended[role] = git(wt, "rev-parse", "HEAD").stdout.strip()

    instance = repos["instance"]
    instance_wt = worktrees["instance"]
    product = repos.get("product", instance)
    product_wt = worktrees.get("product", instance_wt)
    sys.path.insert(0, str(tools))
    from development_path import build_contract
    contract = build_contract(
        kind="relative", project="example", key=key,
        product_path=".",
        instance_repo=str(instance), instance_worktree=str(instance_wt),
        product_repo=str(product), product_worktree=str(product_wt),
    )
    merges = {role: {
        "description": "deliver " + role, "merge_context": "verified example",
        "surface": "Codex", "actor": "pm",
        "co_authored_by": "gpt-6.1-sol <noreply@openai.com>",
        "reasoning_effort": "high",
    } for role in roles}

    recorder = root / "record-builder.py"
    recorder.write_text(
        "import json, subprocess, sys\nfrom pathlib import Path\n"
        f"log = Path({str(events)!r})\n"
        f"result = subprocess.run([sys.executable, {str(builder)!r}, *sys.argv[1:]], "
        "capture_output=True, text=True)\n"
        "with log.open('a') as stream: stream.write(json.dumps({"
        "'argv': sys.argv[1:], 'returncode': result.returncode}) + '\\n')\n"
        "print(result.stdout, end=''); print(result.stderr, end='', file=sys.stderr)\n"
        "sys.exit(result.returncode)\n"
    )
    seal_script = root / "caller-seal.py"
    cleanup_assertions = ""
    if "product" in roles:
        cleanup_assertions = (
            f"assert not Path({str(product_wt)!r}).exists()\n"
            f"assert {str(product_wt)!r} not in git(Path({str(product)!r}), "
            "'worktree', 'list', '--porcelain').stdout\n"
            f"assert git(Path({str(product)!r}), 'show-ref', '--verify', '--quiet', "
            f"{'refs/heads/' + key!r}, check=False).returncode == 1\n"
        )
    seal_script.write_text(
        "import json, subprocess, sys\nfrom pathlib import Path\n"
        f"log = Path({str(events)!r})\n"
        "def git(repo, *args, check=True):\n"
        "    return subprocess.run(['git', '-C', str(repo), *args], check=check, "
        "capture_output=True, text=True)\n"
        + cleanup_assertions
        + "Path('seal-content').write_text(sys.argv[1])\n"
        f"subprocess.run([sys.executable, {str(builder)!r}, '--repo', str(Path.cwd()), "
        "'commit', '--add', 'seal-content', '--subject', 'seal: example', '--actor', 'pm', "
        "'--directional', 'Agari: example — progress: seal', '--surface', 'Codex', "
        "'--co-authored-by', 'gpt-6.1-sol <noreply@openai.com>', "
        "'--reasoning-effort', 'high'], check=True, capture_output=True, text=True)\n"
        "sha = git(Path.cwd(), 'rev-parse', 'HEAD').stdout.strip()\n"
        "with log.open('a') as stream: stream.write(json.dumps({'seal': sha}) + '\\n')\n"
    )
    literal = "seal argument ; $(literal)"
    seal = {"argv": [sys.executable, str(seal_script), literal]}
    inputs = []
    for name, value in [("contract", contract), ("merges", merges), ("seal", seal)]:
        path = root / (name + ".json")
        path.write_text(json.dumps(value))
        inputs.append(path)
    input_bytes = [path.read_bytes() for path in inputs]
    result = subprocess.run(
        [sys.executable, str(delivery), "--contract", str(inputs[0]),
         "--merges", str(inputs[1]), "--seal-action", str(inputs[2]),
         "--builder", str(recorder)],
        cwd=root, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    expected = "delivery: complete\ndelivered: " + ",".join(roles) + "\ncleanup: complete\n"
    assert result.stdout == expected, (result.stdout, result.stderr)
    assert [path.read_bytes() for path in inputs] == input_bytes

    records = [json.loads(line) for line in events.read_text().splitlines()]
    effects = [record for record in records
               if "seal" in record or "--check-only" not in record["argv"]]
    observed_order = [
        "seal" if "seal" in record else
        next(role for role in roles if str(repos[role]) == record["argv"][1])
        for record in effects
    ]
    assert observed_order == ["seal", "instance"]
    assert all(record["returncode"] == 0 for record in records if "argv" in record)
    seal_sha = next(record["seal"] for record in records if "seal" in record)
    for role in roles:
        repo, wt = repos[role], worktrees[role]
        branch_tip = seal_sha if role == "instance" else intended[role]
        assert git(repo, "show", "-s", "--format=%P", "main").stdout.split() == [
            before[role], branch_tip,
        ]
        assert not wt.exists()
        assert str(wt) not in git(repo, "worktree", "list", "--porcelain").stdout
        assert git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + key,
                   check=False).returncode == 1
    assert git(instance, "show", "main:seal-content").stdout == literal
    assert git(instance, "merge-base", "--is-ancestor", seal_sha, "main").returncode == 0
    print(result.stdout, end="")
```

## Run a complete separate-product recipe

Run the following independent Python block from the same instance root.
The seal action asserts product disk, registration and branch absence using the checks from
`core/tools/test_deliver_change.py:L209-L218`,
`test_fixed_delivery_orders_product_seal_instance`.
The event log asserts product merge → seal commit → instance merge, filtering read-only checks,
as in `core/tools/test_deliver_change.py:L183-L201`, `assert_success`.

```python
import json
import subprocess
import sys
import tempfile
from pathlib import Path

tools = Path("core/tools").resolve()
builder = tools / "commit_builder.py"
delivery = tools / "deliver_change.py"
key = "example-delivery"
roles = ["product", "instance"]

def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], check=check,
                          capture_output=True, text=True)

def commit(repo, name, content):
    (repo / name).write_text(content)
    git(repo, "add", name)
    git(repo, "commit", "-qm", name)

with tempfile.TemporaryDirectory(prefix="delivery-example-") as directory:
    root = Path(directory).resolve()
    events = root / "events.jsonl"
    repos, worktrees, before, intended = {}, {}, {}, {}
    for role in roles:
        repo = root / (role + " repo")
        repo.mkdir()
        git(repo, "init", "-qb", "main")
        git(repo, "config", "user.name", "Example")
        git(repo, "config", "user.email", "example@example.invalid")
        git(repo, "config", "core.hooksPath", str(root / (role + "-hooks")))
        commit(repo, "shared", "base\n")
        wt = root / (role + " change")
        git(repo, "worktree", "add", "-qb", key, str(wt))
        commit(wt, "shared", role + " implementation\n")
        repos[role], worktrees[role] = repo, wt
        before[role] = git(repo, "rev-parse", "main").stdout.strip()
        intended[role] = git(wt, "rev-parse", "HEAD").stdout.strip()

    instance = repos["instance"]
    instance_wt = worktrees["instance"]
    product = repos.get("product", instance)
    product_wt = worktrees.get("product", instance_wt)
    sys.path.insert(0, str(tools))
    from development_path import build_contract
    contract = build_contract(
        kind="fixed", project="example", key=key,
        product_path=str(product),
        instance_repo=str(instance), instance_worktree=str(instance_wt),
        product_repo=str(product), product_worktree=str(product_wt),
    )
    merges = {role: {
        "description": "deliver " + role, "merge_context": "verified example",
        "surface": "Codex", "actor": "pm",
        "co_authored_by": "gpt-6.1-sol <noreply@openai.com>",
        "reasoning_effort": "high",
    } for role in roles}

    recorder = root / "record-builder.py"
    recorder.write_text(
        "import json, subprocess, sys\nfrom pathlib import Path\n"
        f"log = Path({str(events)!r})\n"
        f"result = subprocess.run([sys.executable, {str(builder)!r}, *sys.argv[1:]], "
        "capture_output=True, text=True)\n"
        "with log.open('a') as stream: stream.write(json.dumps({"
        "'argv': sys.argv[1:], 'returncode': result.returncode}) + '\\n')\n"
        "print(result.stdout, end=''); print(result.stderr, end='', file=sys.stderr)\n"
        "sys.exit(result.returncode)\n"
    )
    seal_script = root / "caller-seal.py"
    cleanup_assertions = ""
    if "product" in roles:
        cleanup_assertions = (
            f"assert not Path({str(product_wt)!r}).exists()\n"
            f"assert {str(product_wt)!r} not in git(Path({str(product)!r}), "
            "'worktree', 'list', '--porcelain').stdout\n"
            f"assert git(Path({str(product)!r}), 'show-ref', '--verify', '--quiet', "
            f"{'refs/heads/' + key!r}, check=False).returncode == 1\n"
        )
    seal_script.write_text(
        "import json, subprocess, sys\nfrom pathlib import Path\n"
        f"log = Path({str(events)!r})\n"
        "def git(repo, *args, check=True):\n"
        "    return subprocess.run(['git', '-C', str(repo), *args], check=check, "
        "capture_output=True, text=True)\n"
        + cleanup_assertions
        + "Path('seal-content').write_text(sys.argv[1])\n"
        f"subprocess.run([sys.executable, {str(builder)!r}, '--repo', str(Path.cwd()), "
        "'commit', '--add', 'seal-content', '--subject', 'seal: example', '--actor', 'pm', "
        "'--directional', 'Agari: example — progress: seal', '--surface', 'Codex', "
        "'--co-authored-by', 'gpt-6.1-sol <noreply@openai.com>', "
        "'--reasoning-effort', 'high'], check=True, capture_output=True, text=True)\n"
        "sha = git(Path.cwd(), 'rev-parse', 'HEAD').stdout.strip()\n"
        "with log.open('a') as stream: stream.write(json.dumps({'seal': sha}) + '\\n')\n"
    )
    literal = "seal argument ; $(literal)"
    seal = {"argv": [sys.executable, str(seal_script), literal]}
    inputs = []
    for name, value in [("contract", contract), ("merges", merges), ("seal", seal)]:
        path = root / (name + ".json")
        path.write_text(json.dumps(value))
        inputs.append(path)
    input_bytes = [path.read_bytes() for path in inputs]
    result = subprocess.run(
        [sys.executable, str(delivery), "--contract", str(inputs[0]),
         "--merges", str(inputs[1]), "--seal-action", str(inputs[2]),
         "--builder", str(recorder)],
        cwd=root, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    expected = "delivery: complete\ndelivered: " + ",".join(roles) + "\ncleanup: complete\n"
    assert result.stdout == expected, (result.stdout, result.stderr)
    assert [path.read_bytes() for path in inputs] == input_bytes

    records = [json.loads(line) for line in events.read_text().splitlines()]
    effects = [record for record in records
               if "seal" in record or "--check-only" not in record["argv"]]
    observed_order = [
        "seal" if "seal" in record else
        next(role for role in roles if str(repos[role]) == record["argv"][1])
        for record in effects
    ]
    assert observed_order == ["product", "seal", "instance"]
    assert all(record["returncode"] == 0 for record in records if "argv" in record)
    seal_sha = next(record["seal"] for record in records if "seal" in record)
    for role in roles:
        repo, wt = repos[role], worktrees[role]
        branch_tip = seal_sha if role == "instance" else intended[role]
        assert git(repo, "show", "-s", "--format=%P", "main").stdout.split() == [
            before[role], branch_tip,
        ]
        assert not wt.exists()
        assert str(wt) not in git(repo, "worktree", "list", "--porcelain").stdout
        assert git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + key,
                   check=False).returncode == 1
    assert git(instance, "show", "main:seal-content").stdout == literal
    assert git(instance, "merge-base", "--is-ancestor", seal_sha, "main").returncode == 0
    print(result.stdout, end="")
```
