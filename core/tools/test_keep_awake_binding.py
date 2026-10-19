"""Fleet-wide guard on how `--keep-awake` is bound, across every shell file in the repo.

`caffeinate -i -s -w <pid>` waits on a pid **number**. When the watched process exits and the
kernel reissues that number, the hold rides whatever unrelated process now answers to it —
measured 2026-08-12 at 2h51m past its flow's own end, killed by hand
(`docs/proposals/archive/keep-awake-keys-on-identity/rationale.md`). The fix pairs the pid with
the start time it had when it was spawned, which a reissued pid cannot forge, and polls that
pair.

**Why this is enumerated from disk rather than listed.** The defect was found nine sites wide by
one exact-string grep, and a list of nine is a list that goes stale the first time a tenth
launcher is written by copying a ninth. Every check here walks the tree, so a new site is held to
the rule the day it lands and nobody has to remember to add it here.

Two rules, and the second is what makes the first mean anything:

1. **No line may start a `caffeinate` with a `-w` wait.** That flag takes a pid number; there is
   no form of it that takes an identity.
2. **A file that detaches a `caffeinate` (`nohup caffeinate`) must also key a release on
   `ps -o lstart= -p`.** A detached hold outlives the shell that started it, so something has to
   end it; if that something is not an identity check, it is a pid number by elimination.

**The utility form is deliberately exempt, and naming it is the point.**
`core/tools/launch-audit.sh:222` runs `caffeinate -i -s python3 "$WATCHER" …` — caffeinate as a
*wrapper*, holding exactly as long as its own child, with no pid anywhere and nothing to reissue.
It is not detached, so rule 2 never reaches it, and it carries no `-w`, so rule 1 passes it. A
check that flagged it would be reporting a finding against correct code, and the first reader to
learn that would stop reading the rest.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

# Where a keep-awake can live: the shell layers. A worktree is another checkout of this same
# repo — its files are some other branch's, not this tree's, and holding them to this tree's
# rules reports findings nobody here can fix.
_ROOTS = (_REPO / "core", _REPO / ".claude")

# Choosing the two roots above was how that rule used to be applied: `.worktrees/` sits beside
# them, so walking `core/` and `.claude/` skipped it. That only holds while every worktree is
# outside both, and one host is not — `.claude/worktrees/`, which the harness creates for a
# `--bg` run's isolation, sits INSIDE the second root. Measured 2026-09-01: a locked worktree
# at `.claude/worktrees/principal-pm-iteration/` put another branch's copy of
# `core/tools/detach_watcher.sh` — the library itself — in the sweep, and the suite reported
# the shared home as a stray. Nobody in this tree could fix it, which is precisely the outcome
# the comment above forbids. So the rule is applied where it is decided rather than where the
# roots happen to fall: any path under a worktree host *within this checkout* is another
# branch's — the checkout's own location says nothing. Both spellings are
# named — this repo's own branch worktrees live in `.worktrees/` and the harness's `--bg`
# isolation uses `.claude/worktrees/` — because naming one and inferring the other is the
# shape of the assumption this is repairing.
_WORKTREE_HOSTS = frozenset({"worktrees", ".worktrees"})


def _own_tree_shell_files(root):
    """Every `.sh` under `root` that belongs to THIS checkout, sorted. A file inside a worktree
    host is another branch's and is skipped — never excluded by naming one host's path, which
    is the assumption that broke.

    The host segments are read **relative to `root`**, because "another branch's" is a claim
    about where a file sits inside this checkout and not about where the checkout itself sits.
    Reading them off the absolute path made every file another branch's the moment the suite
    ran from `.worktrees/<branch>/` — which is where every branch's suite runs — and the whole
    sweep came back empty. Measured 2026-09-01: the guard below caught it, which is what it is
    for."""
    return [path for path in sorted(root.rglob("*.sh"))
            if not any(part in _WORKTREE_HOSTS for part in path.relative_to(root).parts)]


def _shell_files_invoking_caffeinate():
    """Every `.sh` under the shell layers that actually *invokes* caffeinate, paired with the
    invoking lines. Comment lines are excluded throughout: a header explaining the binding it
    replaced is exactly what this repo asks its launchers to carry, and a check that cannot tell
    an explanation from an invocation would forbid recording the reason."""
    found = {}
    for root in _ROOTS:
        if not root.is_dir():
            continue
        for path in _own_tree_shell_files(root):
            lines = [
                l for l in path.read_text().splitlines() if not l.lstrip().startswith("#")
            ]
            invoking = [l for l in lines if "caffeinate" in l and "command -v" not in l]
            if invoking:
                found[path.relative_to(_REPO)] = (invoking, lines)
    return found


def test_the_sweep_finds_the_files_it_is_meant_to_check():
    """A silent filter passes everything. This test fails if the sweep above stops finding
    anything — which is what a moved directory, a renamed extension, or a broken glob looks
    like from the outside, and is otherwise indistinguishable from a clean fleet."""
    found = _shell_files_invoking_caffeinate()

    assert found, "the sweep found no caffeinate invocation anywhere — the filter is broken"
    assert Path("core/tools/detach_watcher.sh") in found, (
        f"the sweep missed the shared completion-watch home; it found: {sorted(found)}"
    )


def test_no_keep_awake_anywhere_waits_on_a_bare_pid_number():
    """Rule 1. `-w` takes a pid number the kernel reissues, so its presence is the defect."""
    offenders = {
        str(path): [l.strip() for l in invoking if " -w " in l]
        for path, (invoking, _) in _shell_files_invoking_caffeinate().items()
    }
    offenders = {k: v for k, v in offenders.items() if v}

    assert not offenders, (
        "these files bind a keep-awake to a pid NUMBER, which the kernel reissues:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(offenders.items()))
    )


def test_every_detached_keep_awake_keys_its_release_on_process_identity():
    """Rule 2. A detached hold outlives the shell that started it, so something must end it —
    and the only handle that survives a pid being reissued is the pid paired with the start
    time it had when spawned."""
    offenders = []
    for path, (invoking, lines) in _shell_files_invoking_caffeinate().items():
        if not any("nohup caffeinate" in l for l in invoking):
            continue  # the utility form (see this module's docstring) — nothing to release
        if not any("ps -o lstart= -p" in l for l in lines):
            offenders.append(str(path))

    assert not offenders, (
        "these files detach a caffeinate but never check the watched process's identity, "
        "so nothing releases the hold when a pid is reissued:\n  " + "\n  ".join(sorted(offenders))
    )


# --- the block has one home, so there is nothing left to diverge -------------------------
#
# This used to check that the nine hand-copies of the single-watcher block agreed with each
# other — the best available claim while there were nine. There are no longer nine: the
# migration on 2026-08-22 replaced every copy with a call to `core/tools/detach_watcher.sh`
# (shukuba `every-hand-copy-reaches-the-shared-home`), so the check that copies agree became a
# check with one input, and `len(blocks) > 1` — its guard against a broken extraction anchor —
# became false against a *correct* tree.
#
# What replaces it is strictly stronger and needs no anchor at all: copies cannot drift when
# there is one. So the two tests below assert the end state directly — the block exists exactly
# once, in the library, and every file that detaches a watcher reaches that library rather than
# writing the tail itself.
#
# There is no exemption. `cold-read` — the fan-out, one keep-awake over N watchers — was the one
# file allowed to write the tail itself, because the library published `DETACH_WATCHER_PID`
# without the start time it paired with it and a poller rebuilt from that would race the pid
# reissue the pairing exists to close. The library now publishes `DETACH_WATCHER_START` beside
# it, so `cold-read` calls the library once per reader and keeps only the "there are N of them"
# part. Removing the exemption is how that is observed: these checks are what the tree is held
# to, and an exemption nobody needs is an exemption the next copy borrows.

_BLOCK_START = "detach_identity_keep_awake() {"
_BLOCK_END = "Keep-awake:"


def _normalized_keep_awake_block(text):
    """The single-watcher keep-awake block, normalized to what must be identical everywhere.

    Two things legitimately differ between sites and are canonicalized rather than compared:
    the poll-interval knob (each launcher names it in its own `LAUNCH_<X>_` namespace, the
    library in its own) and the report line's wording (each site names what stops — "the run",
    "the round", "the pass"). Everything else — the capture, the caffeinate start, the poller's
    body and the argument order it is handed — is the block, and a copy that drifted in any of
    it is the defect this test exists to find.
    """
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if _BLOCK_START in l]
    if not starts:
        return None
    ends = [i for i, l in enumerate(lines) if _BLOCK_END in l and i > starts[0]]
    if not ends:
        return None

    # Shell line continuations and indentation are whitespace, not behaviour: where a site
    # wraps a long `nohup bash -c … ' bash "$a" "$b" \` line is a formatting choice, and a
    # comparison that reads it as divergence would report a finding against identical code.
    raw = re.sub(r"\\\n\s*", " ", "\n".join(lines[starts[0] : ends[0] + 1]))

    block = []
    for line in raw.splitlines():
        stripped = " ".join(line.split())
        if not stripped or stripped.startswith("#"):
            continue
        stripped = re.sub(r'"\$\{[A-Z_]*POLL_SECONDS[^}]*\}"', "<POLL>", stripped)
        stripped = re.sub(r'"?\$[A-Z_]*POLL_SECONDS"?', "<POLL>", stripped)
        if _BLOCK_END in stripped:
            stripped = "<REPORT LINE>"
        block.append(stripped)
    return "\n".join(block)


_LIBRARY = "core/tools/detach_watcher.sh"


def test_the_single_watcher_keep_awake_block_has_exactly_one_home():
    """The migration's end state, enumerated from disk. A tenth copy written tomorrow by
    pasting a ninth is caught here the day it lands, which is the whole reason this file walks
    the tree instead of holding a list."""
    carriers = []
    for root in _ROOTS:
        if not root.is_dir():
            continue
        for path in _own_tree_shell_files(root):
            if _normalized_keep_awake_block(path.read_text()):
                carriers.append(str(path.relative_to(_REPO)))

    assert _LIBRARY in carriers, (
        f"the shared home no longer carries the block at all; found it in: {sorted(carriers)}. "
        "Either the library was gutted or the extraction anchor moved — this test proves "
        "nothing until one of those is true again"
    )
    strays = sorted(c for c in carriers if c != _LIBRARY)
    assert not strays, (
        "the single-watcher keep-awake block has copies again, outside its one home at "
        f"{_LIBRARY}:\n  " + "\n  ".join(strays)
    )


def test_every_file_that_detaches_a_watcher_reaches_the_shared_home():
    """The other side of the same claim, and the one that catches a copy written in a shape the
    block extraction above does not recognise. A file that backgrounds `watch_agent.py` is
    writing the detach-and-return tail; it either calls the library or is the named fan-out."""
    offenders = []
    for root in _ROOTS:
        if not root.is_dir():
            continue
        for path in _own_tree_shell_files(root):
            rel = str(path.relative_to(_REPO))
            if rel == _LIBRARY:
                continue
            lines = [
                l for l in path.read_text().splitlines() if not l.lstrip().startswith("#")
            ]
            body = "\n".join(lines)
            if not any("nohup python3" in l and "WATCHER" in l for l in lines):
                continue  # detaches no watcher — nothing for the shared home to serve
            if "detach_completion_watcher" not in body:
                offenders.append(rel)

    assert not offenders, (
        "these files detach a watcher by hand instead of calling the shared home at "
        f"{_LIBRARY}:\n  " + "\n  ".join(offenders)
    )


def test_every_site_carrying_the_block_spawns_the_watcher_it_names():
    """The block reads `$watcher_pid`, which is only meaningful where the same shell just set
    it from the backgrounded watcher. Block identity proves the copies match each other; this
    proves the variable they all read is not a copy's leftover."""
    offenders = []
    for root in _ROOTS:
        if not root.is_dir():
            continue
        for path in _own_tree_shell_files(root):
            text = path.read_text()
            if _normalized_keep_awake_block(text) and "watcher_pid=$!" not in text:
                offenders.append(str(path.relative_to(_REPO)))

    assert not offenders, (
        "these files key a keep-awake on $watcher_pid without ever assigning it from a "
        "backgrounded watcher:\n  " + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------------------
# The sweep walks THIS checkout, and a worktree is not it
#
# Every check above enumerates from disk, which is the whole design (see the module
# docstring). The cost of that design is that anything shaped like a shell file under a root
# gets held to this tree's rules — including a checkout of some other branch. The exclusion
# used to be implicit in the choice of roots and stopped holding the day a worktree appeared
# inside one; these cases pin it where it is now decided instead.
# ---------------------------------------------------------------------------------------


def test_a_file_inside_a_worktree_host_is_another_branchs(tmp_path):
    (tmp_path / "core" / "tools").mkdir(parents=True)
    (tmp_path / "core" / "tools" / "detach_watcher.sh").write_text("# ours\n")
    other = tmp_path / ".claude" / "worktrees" / "some-session" / "core" / "tools"
    other.mkdir(parents=True)
    (other / "detach_watcher.sh").write_text("# another branch's\n")

    found = _own_tree_shell_files(tmp_path)

    assert [p.relative_to(tmp_path).as_posix() for p in found] == [
        "core/tools/detach_watcher.sh"], (
        "a worktree's copy reached the sweep — it is some other branch's file, and a finding "
        "against it is one nobody in this tree can fix"
    )


def test_the_repo_root_worktree_host_is_excluded_by_the_same_rule(tmp_path):
    # `.worktrees/` at the repo root and `.claude/worktrees/` are two hosts, and the old
    # exclusion knew only the one that happened to sit outside the roots.
    for host in (".worktrees", ".claude/worktrees"):
        leaf = tmp_path / host / "a-branch"
        leaf.mkdir(parents=True)
        (leaf / "launcher.sh").write_text("# theirs\n")

    assert _own_tree_shell_files(tmp_path) == []


def test_a_directory_merely_named_like_a_worktree_file_is_still_walked(tmp_path):
    # The rule keys on a path SEGMENT, so a file whose name contains the word is untouched.
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "worktrees_helper.sh").write_text("# ours\n")

    assert [p.name for p in _own_tree_shell_files(tmp_path)] == ["worktrees_helper.sh"]
