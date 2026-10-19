#!/usr/bin/env python3
"""watch_agent.py — wait for a background `claude --bg` agent to stop, then notify.

Version: 1.11.0

WHY THIS EXISTS
    A launcher runs `claude --bg` and exits seconds later, while the agent runs on for
    minutes or hours. So the launcher's own exit says nothing about the run — something
    has to outlive it and watch. That is this. It is spawned detached by the launcher and
    polls until the agent reaches a terminal state.

WHAT IT POLLS
    `claude agents --json --all` — the agent's own reported `state` AND `status`. A
    directory poll cannot tell "waiting forever" from "still working": both look like
    silence.

    Two keys, because one stopped being enough. A run whose PROCESS has exited reaches a
    terminal `state` and carries no `status` key at all — the shape this was built
    against. A run whose TURN has ended while its process is still alive reports
    `status: idle` and keeps `state: working`, which is in no terminal set. Measured
    2026-08-21 on two live runs — ba5c8b8d and c6fa18cd — whose watchers had sent nothing
    21 minutes and 1h50m after those runs wrote their final reports. The state alone
    could not see either of them end.

    So `status: idle` is a terminal condition too, debounced over two consecutive polls
    where a terminal state is immediate. A `status` is a live property of a session, not
    a resting place: one idle read says nothing was in flight at that instant, and acting
    on it would notify about a run still working and then stop it — the one cost a late
    notification does not carry.

    A third fact is polled too, for a caller that names one with --done-when-exists: does
    the path it gave exist now, having not existed when the watch began. Through the agent
    list alone, a multi-turn run that has FINISHED and one that is merely RESTING between
    turns are the same record — both show `status: idle, state: working`, over and over,
    for as long as the run keeps handing out turns. The agent list cannot tell those two
    apart, so it is not asked to: the caller supplies the ending, in the one shape the
    watcher can poll without inferring anything (§ completion_marker_seen).

ONE DEATH IS WRITTEN DOWN, AND IT IS READ
    A run killed by a model refusal reaches `blocked`, which reads as "finished its turn
    and is idle". Its transcript records the refusal with a category and a model, and the
    agent list carries the sessionId that finds the transcript — so that one death is
    named on the message, above the state note. It is the only one written down anywhere
    this can reach: every other way a run can die still reads as the hedge.

THE STATE SAYS THE RUN STOPPED. IT DOES NOT SAY WHAT HAPPENED.
    The state is a poor witness: it says the run is no longer moving and nothing more —
    the same state has meant both a run that finished its work and one that never
    started. So what the run PRODUCED is read from the product's own files, on every
    terminal state, and the state is demoted to a note at the end of the message. Do not
    reintroduce a branch on state here; believing the state was the 1.1.0 bug.

IT STOPS THE RUN IT WATCHED
    A finished `--bg` session does not exit. It sits idle holding a live session process,
    waiting for a prompt that is never coming. Nothing ever attaches to continue one —
    these runs are file-based (the next step is a fresh session reading what this one
    wrote), so the session's context has no further use once its turn ends.

    So after notifying, this stops it. That costs nothing the CLI does not hand back:
    `claude stop` keeps the conversation and `claude attach` still resumes it.

    THAT PREMISE HOLDS FOR EVERY RUN EXCEPT ONE THAT WAS NOT TRADING AGAINST ANYTHING —
    UNTIL IT WAS. A run that ends its turn once per turn it hands out, and keeps its
    context across all of them, is not finished when it goes idle — it is resting between
    turns, and stopping it there is the same mistake as stopping a run mid-tool-call. Two
    real runs of the `product-sdd` runner were stopped this way, about a minute in, on
    2026-08-26. So a caller declares this with --multi-turn, and declaring it changes what
    ending means for this watch: `status: idle` stops being terminal (§ WHAT IT POLLS), and
    the caller names the fact that says the run is actually over
    (--done-when-exists). A caller that gives neither flag sees this file exactly as it
    was — the trade this section used to say did not exist is this one.

SILENCE IS NOT SUCCESS
    Every exit path notifies — terminal state, agent-never-appeared, timeout, and a
    `claude` CLI that will not run. A watcher that only reports the happy path is worse
    than no watcher, because its silence reads as "still going". The sends themselves
    hold to the same rule: each one's outcome goes to stderr, or a rejected send would
    be exactly as quiet as a delivered one.

THE ON-COMPLETE HOOK
    A caller that wants to act on a run's end, not just be told about it, passes
    --on-complete <script>. It is called BESIDE notify() — never instead of it, and
    notify() keeps firing first — on every one of the six paths where this watcher stops
    watching, given a HookOutcome as its one argument: COMPLETED (the run finished,
    identified or watched blind), PRODUCED_NOTHING (the run finished, identified or
    watched blind, and the reporter's own read of the ctx it was handed says the run made
    no difference at all — HEAD did not move and no self-answer report appeared;
    `reporters.produced_nothing`), TIMEOUT (either deadline expired), VANISHED (the run
    disappeared from the agent list), APPEAR_ERROR (nothing matching ever showed up) or
    STOPPED (a --multi-turn run ended without its --done-when-exists marker — reached
    `stopped`, or, watched blind, every candidate ended — so nothing said it was finished).
    Coarser than the six paths on purpose — a caller routing on this needs to know which
    of the six happened, not which internal path got there. A reporter that raises never
    yields PRODUCED_NOTHING: a failure to read is not evidence the run produced nothing,
    so that ending degrades to COMPLETED exactly as its message degrades to "run ended."

    Best-effort like notify() and stop_agent(), and for the same reason: by the time the
    hook runs the notification is already sent, and a leaked or broken hook must never
    cost somebody that message. A missing, non-executable, failing or hanging hook
    (bounded by a 60s timeout) costs nothing — the exit code this file returns is
    unaffected either way. Optional; a caller that omits it sees this file exactly as it
    was.

WHICH RUN IT IS WATCHING IS NOT A QUESTION OF WHAT IT IS CALLED
    Claude Code retitles a background agent, now within the appear window, so the
    launcher's fixed prompt stops matching on a run that has barely started — see
    find_agent_id. The handle is the id `claude --bg` prints at launch, passed as
    --agent-id. Without one, the name is tried and then the pre-launch --exclude-ids
    snapshot decides, and an ambiguous set is refused rather than ranked.

THE BLIND WATCH — NOT KNOWING WHICH RUN IS YOURS IS NOT THE SAME AS THERE BEING NONE
    That refusal used to end the watch. At the appear deadline this process exited, and a
    `--keep-awake` caffeinate keyed to its lifetime went with it — measured ~90 seconds
    into a 34-minute run that went on to merge, with the only message the owner ever got
    being "the run may not have started." One message was doing two jobs: sometimes
    nothing started, and sometimes several runs were here and none could be told apart.

    So the deadline asks one more question — is there anything under this cwd at all? —
    and the two answers are two paths:

      nothing here          → the message is exactly right. Notify, exit. Unchanged.
      here but unnameable   → blind watch. Hold, poll the candidate set, and report when
                              every one of them is terminal or gone.

    The blind path holds because a keep-awake is keyed to this process being alive, and it
    reports because an ending nobody is told about is the failure this whole file exists
    to prevent (§ SILENCE IS NOT SUCCESS). The body it reports is the caller's reporter's,
    which reads the artifact and the repo HEAD rather than the agent — facts about the
    launcher's product, true whoever produced them — plus a line naming what could not be
    identified. It stops nothing: `claude stop` is what makes a wrong guess expensive, and
    a watcher with no id it is entitled to is not entitled to stop anything either.

    Two boundaries, both deliberate. A caller that passed --agent-id gets the original
    message, because it named its run exactly and whatever else is here is somebody
    else's. And the blind watch is governed by the SAME --timeout-seconds deadline as the
    identified path — trading a keep-awake released at 90 seconds for one never released
    at all would be the worse defect.

USAGE
    watch_agent.py (--agent-id <id> | --name <agent name>) --label <human label>
                   [--reporter generic|prd|srs|uxd|design|content|writing-bar|agari|sdd|fdr|
                               experience-visual|experience-voice|fix-author|apply-packet|
                               companion-self-answer]
                   [--artifact-path <path>] [--head-repo <path>]
                   [--multi-turn] [--done-when-exists <path>]
                   [--on-complete <script>]
                   [--exclude-ids a,b,c] [--cwd <path>] [--notify <path>]
                   [--poll-seconds N] [--timeout-seconds N] [--appear-seconds N]

    The outcome message is composed by the named --reporter (see reporters.py); this file
    only watches. --artifact-path is what the reporter reads; --head-repo is the repo whose
    HEAD it checks for a commit (defaults to --artifact-path).

    --multi-turn declares that this run ends its turn once per turn it hands out and keeps
    its context across them, so `status: idle` is never read as this run finishing
    (§ WHAT IT POLLS, § IT STOPS THE RUN IT WATCHED). It requires --done-when-exists — a
    path the run itself creates when it is finished, checked for appearing since the watch
    began. --done-when-exists is also legal without --multi-turn, as an additional ending
    for an ordinary single-turn run.

    --on-complete is called beside --notify, given a HookOutcome, on every path where this
    watch ends (§ THE ON-COMPLETE HOOK).
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import json
import os
import subprocess
import sys
import time
from enum import Enum

__version__ = "1.18.0"

# The script's own directory is on sys.path when run directly (python3 watch_agent.py)
# and the tests insert it before importing this module, so a plain import resolves the
# sibling reporters module in both. reporters owns every run-type-specific outcome string;
# this file owns only the watch.
import reporters


class HookOutcome(str, Enum):
    """What --on-complete is given — coarser than the six paths that can reach it. A
    caller routing on this needs to know which of these six happened, not which
    internal path got there: a completion is a completion whether the watcher named its
    run or watched blind, and a timeout is a timeout either way. `(str, Enum)` because the
    value is written out — passed to the hook as a plain argument, per `conventions.md`
    § Constructs' rule for a value read back rather than only compared.

    PRODUCED_NOTHING sits beside COMPLETED, never in place of it: the run still finished
    (identified or watched blind), and what distinguishes the two is
    `reporters.produced_nothing(ctx)` — called once per ending, at the completion path that
    attaches its answer to the reporter's `Outcome`, and read back from that field by
    `_hook_outcome_for` alone. No reporter computes it and nothing here re-derives it from
    `ctx`. A reporter that raises never yields it (§ THE ON-COMPLETE HOOK, above this
    class)."""

    COMPLETED = "completed"
    PRODUCED_NOTHING = "produced_nothing"
    TIMEOUT = "timeout"
    VANISHED = "vanished"
    APPEAR_ERROR = "appear_error"
    STOPPED = "stopped"


def _hook_outcome_for(outcome: reporters.Outcome) -> HookOutcome:
    """Which `HookOutcome` this ending reports — the one read site for the fact
    `reporters.produced_nothing` computed once, so this file never inspects `ctx` itself
    a second time to decide the same question (§ THE ON-COMPLETE HOOK)."""
    return HookOutcome.PRODUCED_NOTHING if outcome.produced_nothing else HookOutcome.COMPLETED


# An agent in one of these is not coming back on its own. None of them says how the run
# went — they mean only: stop watching, go read the product.
TERMINAL_STATES = {"done", "stopped", "blocked"}

# The same question asked of a run that ends its turn on purpose, once per turn it hands
# out. Two of the three above mean only that a TURN ended, so for such a run they are
# normal events rather than endings — measured 2026-08-26 on a live `product-sdd` run,
# whose runner reported `blocked` across six samples while its seats worked and its
# document changed, then finished two more rounds and committed, and whose seats went
# `done` and back to `working` between rounds. `stopped` is the one that means gone:
# nothing revives a stopped session, and it keeps reporting that state in the list.
#
# Narrowing the set does not make such a run unwatchable. Its endings are the caller's own
# completion marker, `stopped`, the vanish check, and the timeout — see SILENCE IS NOT
# SUCCESS, which binds here exactly as it does above.
MULTI_TURN_TERMINAL_STATES = {"stopped"}

# The other ending, and the only one a still-alive process can report: the turn is over
# and the session sits idle holding it, while `state` stays `working` throughout. See
# WHAT IT POLLS — this key is the sole witness for that ending.
IDLE_STATUS = "idle"

# Debounced, where a terminal state is not. The number is a property of what `status`
# means (§ WHAT IT POLLS), not a knob — which is why it is a constant and not a flag.
IDLE_POLLS_BEFORE_TERMINAL = 2

def default_notifier():
    """KENSAIAPP_NOTIFIER, the variable every launcher reads, or None — never a machine's own
    script. Read when arguments are parsed, not at import, so a test's cleared environment holds.
    Unset means nothing is sent, which is ordinary configuration, not an error."""
    return os.environ.get("KENSAIAPP_NOTIFIER") or None

# Where Claude Code keeps a session's transcript: <PROJECTS_DIR>/<cwd slug>/<sessionId>.jsonl.
# Only the filename is derived here — the slug is globbed past, so no cwd-to-slug rule is
# reimplemented and a change to that rule cannot silently point this at the wrong file.
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--list-ids", action="store_true",
                   help="print the current background agent ids under --cwd (comma-separated) "
                        "and exit; the launcher calls this before launching to build --exclude-ids")
    p.add_argument("--agent-id", dest="agent_id",
                   help="the id `claude --bg` printed at launch. The exact handle: given "
                        "this, the name is not consulted at all. Preferred over --name.")
    p.add_argument("--name", help="agent name to match (the launcher's fixed prompt). A "
                                  "PREFERENCE, not a requirement — Claude Code retitles a "
                                  "run, so a name that no longer matches falls back to the "
                                  "--cwd + --exclude-ids candidate set.")
    p.add_argument("--label", help="human label for the message, e.g. the project")
    p.add_argument("--exclude-ids", default="", help="comma-separated ids that existed before launch")
    p.add_argument("--cwd", default=os.getcwd(), help="only match agents started under this path")
    p.add_argument("--reporter", default="generic",
                   help="which outcome composer to use (see reporters.py): generic, prd, srs, "
                        "uxd, design, fix-author, apply-packet. Unknown names fall back "
                        "to generic.")
    p.add_argument("--artifact-path", "--product-path", dest="artifact_path",
                   help="the thing the run authored — a product dir, a packet file. The reporter "
                        "reads the outcome from here. --product-path is the older name for it.")
    p.add_argument("--document-stem", default="",
                   help="which document this run worked, lower-cased — the companion-self-answer "
                        "reporter's own trail/<stem>/ under --artifact-path. Ignored by every "
                        "other reporter.")
    p.add_argument("--head-repo",
                   help="the git repo whose HEAD advancing means this run committed. Defaults to "
                        "--artifact-path. The reporter judges what an unchanged HEAD means.")
    p.add_argument("--notify", default=default_notifier(), help="notifier script, called with one message arg")
    p.add_argument("--poll-seconds", type=float, default=30.0)
    p.add_argument("--timeout-seconds", type=float, default=6 * 60 * 60)
    p.add_argument("--appear-seconds", type=float, default=90.0,
                   help="how long to wait for the launched agent to show up in the list")
    p.add_argument("--multi-turn", action="store_true",
                   help="declare that this run ends its turn once per turn it hands out "
                        "and keeps its context across them (e.g. product-sdd). Changes "
                        "what this watcher treats as an ending: `status: idle` stops being "
                        "a terminal condition, so a run resting between turns is never "
                        "read as finished and never stopped.")
    p.add_argument("--done-when-exists", dest="done_when_exists",
                   help="a path the run itself creates when it is finished. Must APPEAR "
                        "during the watch — a path already on disk when the watch starts "
                        "is ignored, so a stale marker from a previous run cannot end this "
                        "one on its first poll.")
    p.add_argument("--on-complete", dest="on_complete",
                   help="script called beside the notifier (never instead of it) on every "
                        "path where this watcher stops watching, given the run's outcome. "
                        "Optional; a caller that omits it sees this file exactly as it was.")
    args = p.parse_args(argv)
    if not args.list_ids and not (args.label and (args.agent_id or args.name)):
        p.error("--label and one of --agent-id / --name are required unless --list-ids "
                "is given")
    # Gated on --list-ids for the same reason the refusal above it is: --list-ids prints
    # and returns before any watch begins, so there is no ending for this rule to protect
    # and nothing a refusal here would save. A mode that bypasses every other requirement
    # and not this one is the shape a caller trips over while diagnosing.
    if not args.list_ids and args.multi_turn and not args.done_when_exists:
        p.error("--multi-turn requires --done-when-exists: with `status: idle` no longer "
                "terminal, the six-hour deadline would be the only ending left for this "
                "watch")
    return args


def list_ids(cwd):
    """Comma-separated ids of background agents under `cwd`, for --exclude-ids.

    An unreadable agent list yields an empty set rather than an error: the snapshot is
    an optimisation for disambiguating repeat runs, and failing it must not stop a
    launch. The cost of a miss is only that a relaunch could match an older agent.
    """
    agents = list_agents()
    return ",".join(
        a["id"] for a in (agents or [])
        if a.get("kind") == "background" and a.get("cwd") == cwd and a.get("id")
    )


def list_agents():
    """Return the agent list, or None if the CLI could not be read.

    None is distinct from []: an empty list means "no agents", None means "we cannot
    see the agent list at all" — a condition the caller must report rather than treat
    as "not finished yet".
    """
    try:
        proc = subprocess.run(
            ["claude", "agents", "--json", "--all"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except (ValueError, TypeError):
        return None


def find_agent_id(agents, name, cwd, exclude_ids, agent_id=None):
    """This launch's agent: an explicit id, else the name, else the one new candidate.

    THE NAME IS NOT A HANDLE, AND THAT IS THE THIRD TIME IT HAS PROVED IT
    Claude Code REPLACES an agent's name with an AI-generated title. Measured 2026-07-16:
    the launcher's fixed prompt "invoke the product-prd skill for the <project> project."
    became "invoke <project> product-prd skill". Measured 2026-07-24: the stored name has
    every run of whitespace collapsed to a single space, so a MULTI-LINE launch prompt
    never matched a raw compare. Measured 2026-08-22, and
    the reason this function no longer requires the name: the retitle now lands INSIDE the
    90-second appear window, on a run that has barely begun — `claude --bg "Reply with the
    single word OK and stop."` was listed as "user intent extraction task" seconds after
    launch. What this used to say — that the exposure was only "a run that finishes its
    whole turn within a second or two of launch" — is false, and three ad-hoc-flow runs
    (2026-08-21 ×2, 2026-08-22 ×1) were abandoned by their watchers because of it.

    THE ID IS THE HANDLE, AND THE LAUNCH IS WHERE IT IS KNOWABLE
    `claude --bg` prints `backgrounded · <id>` on stdout (ANSI-wrapped even when stdout is
    not a TTY), and that id is what the agent list carries. A launcher that captures it
    passes `--agent-id` and this stops guessing entirely. `--session-id` is NOT an
    alternative: `--bg` refuses a caller-chosen one ("--bg manages the session id;
    ignoring --session-id").

    THE THREE RULES, IN ORDER
    1. An explicit `agent_id` is authoritative — the run is that id, whatever it is now
       called and whoever else is running from this root. It is confirmed present in the
       list and nothing else about it is questioned.
    2. Else the NAME still decides among the candidates, exactly as it always did — newest
       first. This is what keeps the disambiguation the name check was there for: a second
       launcher running different work from this same instance root still carries its own
       prompt, so a name that matches is positive evidence and is never overridden.
    3. Else the candidate set itself identifies the run: a background agent under `cwd`
       whose id was not in the pre-launch `--exclude-ids` snapshot did not exist when this
       launch began, so it is this launch's. ONLY when there is exactly one. Two
       unidentifiable candidates are refused rather than ranked, because the caller ends by
       running `claude stop` on what this returns — a guess here stops somebody else's run.

    WHAT A REFUSAL COSTS IS NOT THIS FUNCTION'S TO DECIDE, AND IT CHANGED
    Returning None used to end the watch at the appear window. It no longer does: the
    caller reads a refusal here as "hold and watch the set blind" whenever candidates are
    present (§ THE BLIND WATCH in this module's docstring). Nothing about the three rules
    above moved — this note is here so a reader deciding whether to relax rule 3 knows the
    cost it was traded against is already gone.
    """
    if not agents:
        return None
    if agent_id:
        # Confirmed present, not assumed: the caller polls until this returns something,
        # and "the id the launcher gave me is in the list" is the appearance it waits for.
        return agent_id if any(a.get("id") == agent_id for a in agents) else None
    candidates = [
        a for a in agents
        if a.get("kind") == "background"
        and a.get("cwd") == cwd
        and a.get("id")
        and a["id"] not in exclude_ids
    ]
    want = " ".join((name or "").split())
    named = [
        a for a in candidates
        if want and " ".join((a.get("name") or "").split()) == want
    ]
    if named:
        return max(named, key=lambda a: a.get("startedAt") or 0)["id"]
    if len(candidates) == 1:
        return candidates[0]["id"]
    return None


def state_of(agents, agent_id):
    for a in agents or []:
        if a.get("id") == agent_id:
            return a.get("state")
    return None


def status_of(agents, agent_id):
    """The run's `status`, or None if the list entry does not carry one.

    A sibling of `state_of` rather than a second return value from it, deliberately: the
    watch loop reads a missing `state` as "the agent vanished from the list", and folding
    two keys into that one read would put the vanish check on a value it was never
    written for.

    None is an ordinary answer, not an error. The older shape — a finished run whose
    process has exited — carries no `status` at all, and must go on being watched by its
    state exactly as it was.
    """
    for a in agents or []:
        if a.get("id") == agent_id:
            return a.get("status")
    return None


def session_id_of(agents, agent_id):
    """The full session id for `agent_id`, or None if the list does not carry one.

    The list gives both: `id` is an 8-character prefix and `sessionId` the whole uuid the
    transcript is named for. None is an ordinary answer, not an error — the refusal read is
    simply skipped, and the message is what it would have been.
    """
    for a in agents or []:
        if a.get("id") == agent_id:
            return a.get("sessionId")
    return None


# --- the outcome repo's HEAD, for reporters that judge "did this run commit" -------
#
# The reporters (in reporters.py) own the run-type-specific outcome read; the watcher
# owns only watching. The one fact the watcher gathers on their behalf is the outcome
# repo's HEAD, before the watch and again at the terminal state — a fact reporters
# compare, but whose meaning ("committed nothing") is theirs to judge, not the watcher's.


def git_head(repo_path):
    """The repo's HEAD, or None if it cannot be read.

    None covers every "no HEAD to compare" case the same way: no path, no git, a path
    that is not a repo, or a file rather than a directory. A reporter that gets None must
    not read an unchanged HEAD into a run that idled — there is simply nothing to compare.
    """
    if not repo_path:
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


# --- the completion marker: the caller's own declaration that a multi-turn run is over ---
#
# The other before-and-after fact the watcher gathers, beside HEAD. A `--multi-turn` run
# never ends on `status: idle` (see WHAT IT POLLS), so it needs some other terminal
# condition — and this one is not the watcher inferring an ending, it is the run itself
# saying so. The watcher polls the fact and judges nothing, the same line `git_head`'s
# comment draws for HEAD.


def completion_marker_seen(path, present_before):
    """True only when `path` names something that appeared SINCE the watch began.

    `present_before` is a single reading taken once, before the watch — the same shape
    `head_before` takes for HEAD. Without it, a marker left by a PREVIOUS run would end the
    watch on its very first poll and report a run that had barely started; with it, a
    marker already on disk at the start is inert for the whole life of this watch, and
    stays inert even if it is deleted and written again. That is the cost of the reading
    being taken once rather than re-derived: the price of never firing on a stale marker
    is never firing on a path that started out stale, and a caller wanting the marker to
    count clears it before launching rather than during.

    Best-effort like `git_head` and `refusal_of`: an unreadable path is `False`, never a
    raise. A directory counts as existing, the same as a file — the caller names the path,
    and this does not police its kind.
    """
    if not path or present_before:
        return False
    try:
        return os.path.exists(path)
    except OSError:
        return False


# --- the refusal record: the one death the state cannot express -------------------
#
# `blocked` reads as "finished its turn and is idle", and a run killed by a model refusal
# reaches it — so for that death the state is not just a poor witness, it is a flattering
# one. The run's own transcript records the refusal, machine-readable, and the agent list
# carries the sessionId that finds it. That is the second fact this file gathers past the
# state, and unlike the HEAD it is not handed to a reporter: "the run was refused" is the
# same sentence for every run type, and reporters.py owns the run-type-specific ones.
#
# It says what the record says and no more. One observed refusal is not evidence that the
# record is always terminal, so nothing here claims it ended the run — that reading is the
# owner's, from this line and an unchanged HEAD together.


def refusal_of(session_id, projects_dir=None):
    """The run's model refusal — `{"category", "model"}` — or None if there is not one.

    None covers every "nothing to report" case the same way: no session id, no transcript,
    an unreadable one, a shape that will not parse. Best-effort like `git_head` and
    `list_agents`: the transcript is the harness's own undocumented format, and a file this
    cannot read must cost the refusal line, never the message.
    """
    if not session_id:
        return None
    root = projects_dir if projects_dir is not None else PROJECTS_DIR
    try:
        paths = glob.glob(os.path.join(root, "*", f"{session_id}.jsonl"))
    except OSError:
        return None
    found = None
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    # Cheap gate first: a transcript runs to thousands of lines and only a
                    # handful could ever match.
                    if "model_refusal_no_fallback" not in line:
                        continue
                    try:
                        record = json.loads(line)
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(record, dict):
                        continue
                    if record.get("subtype") != "model_refusal_no_fallback":
                        continue
                    found = {
                        "category": record.get("apiRefusalCategory"),
                        "model": record.get("originalModel"),
                    }
        except (OSError, UnicodeError):
            continue
    return found


def refusal_note(refusal):
    """What the transcript recorded, above the state note — never what it caused."""
    category = refusal.get("category") or "unnamed"
    model = refusal.get("model") or "an unnamed model"
    return (f"(the run's transcript records a model refusal with no fallback — "
            f"category: {category}, model: {model})")


def state_note(state, agent_id, status=None, marker_path=None):
    """The run's own state, as a footnote. It qualifies the outcome; it never states it.

    `blocked` and `stopped` are still worth telling apart — one reached a natural stop,
    something ended the other — but neither is allowed to claim how the work went. Note
    the hedge on `stopped`: "stopped before finishing" was 1.1.0's wording and it called
    a clean 39-minute halt a failure.

    The states are read FIRST, so a run that ended on its state reads as that state even
    when a `status` rides along on the same entry — which happens: agent 410201fc, in
    `claude agents --json --all` on 2026-08-21, carried `status: idle` and
    `state: blocked` together.

    `marker_path` is given only when THIS ending was reached on the caller's completion
    marker (never merely because --done-when-exists was passed). It goes after the states
    — a run that also ended on its state is better described by that state — and before the
    idle branch, which is unreachable for a multi-turn run anyway. A run that declared
    itself finished is better described by that declaration than by whatever `status`
    happens to ride along, for the same reason the idle branch exists: the untouched
    fallback here would print "(run X — state: working)", which reads as a run still going.

    The idle branch is for the ending the states cannot express — `state` says `working`
    and only `status` says the turn is over. It gets `blocked`'s reading because it is
    the same fact about the run, and keeps both raw keys behind it: what the fallback
    printed here was "(run X — state: working)", which reads as a run still going.
    """
    if state == "blocked":
        return f"(run {agent_id} finished its turn and is idle — state: blocked)"
    if state == "stopped":
        return f"(run {agent_id} was stopped — state: stopped; it may have been cut off mid-turn)"
    if state == "done":
        return f"(run {agent_id} completed — state: done)"
    if marker_path:
        return (f"(run {agent_id} declared itself finished at {marker_path} — "
                f"status: {status}, state: {state})")
    if status == IDLE_STATUS:
        return (f"(run {agent_id} finished its turn and is idle — "
                f"status: idle, state: {state})")
    return f"(run {agent_id} — state: {state})"


def notify(notifier, message):
    """Send, and write down what happened either way. True if the notifier confirmed it.

    Nobody is watching this process's exit code — it was detached with nohup — so a
    rejection nobody writes down is a rejection nobody can ever learn about. That is how
    a real message went missing with no way to tell a failed send from a dead watcher.

    A careful notifier exits non-zero with a diagnostic when its service rejects a send,
    and zero only when the service confirms. 1.1.0 threw all of that away.

    Not `check=True`: still nothing raises out of the watcher. Failure is recorded now,
    not propagated. And the message prints BEFORE the attempt, so the log carries the
    text we meant to send even if the notifier hangs or this process dies mid-send.

    Every print flushes. Without that the rest of this is theatre: stdout is
    block-buffered when redirected to a file — which is exactly how the launcher runs
    this — so a process killed mid-send would take the unflushed message down with it,
    losing the one line the print-first ordering exists to save.
    """
    print(message, flush=True)
    if not notifier:
        print("notify: no notifier set (KENSAIAPP_NOTIFIER) — not sent.", file=sys.stderr, flush=True)
        return False
    try:
        proc = subprocess.run([notifier, message], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"notify: notifier did not run: {exc}", file=sys.stderr, flush=True)
        return False
    if proc.returncode != 0:
        print(f"notify: notifier exited {proc.returncode}: {proc.stderr.strip()}",
              file=sys.stderr, flush=True)
        return False
    print("notify: sent.", file=sys.stderr, flush=True)
    return True


def run_on_complete_hook(hook, outcome):
    """Called beside notify() on every path where this watcher stops watching, given the
    run's HookOutcome as the hook's one argument. True if the hook exited zero.

    Best-effort, like notify() and stop_agent(), and for the same reason: by this point
    the notification is already sent, and a leaked or broken hook must never cost somebody
    that message. Bounded by a timeout so a hook that hangs cannot hold the watcher open
    forever, and every outcome — success or failure — is recorded the way a failed notify
    is, never raised.
    """
    try:
        proc = subprocess.run(
            [hook, outcome.value], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"on_complete: hook did not run: {exc}", file=sys.stderr, flush=True)
        return False
    if proc.returncode != 0:
        print(f"on_complete: hook exited {proc.returncode}: {proc.stderr.strip()}",
              file=sys.stderr, flush=True)
        return False
    print("on_complete: ran.", file=sys.stderr, flush=True)
    return True


def stop_agent(agent_id):
    """Stop the watched session. Best-effort; True if the CLI confirmed it.

    Safe in a way worth stating, because it looks destructive and is not: `claude stop`
    keeps the conversation, and `claude attach <id>` resumes it afterwards. So there is
    no case where this loses work — not even a run that stopped mid-turn waiting on a
    permission prompt, which is the one that looks most like it needs rescuing.

    Best-effort like the notify, and for the same reason: by this point the message is
    already sent, and a leaked process must never cost somebody their notification.
    """
    try:
        proc = subprocess.run(
            ["claude", "stop", agent_id], capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"stop: could not run `claude stop`: {exc}", file=sys.stderr, flush=True)
        return False
    if proc.returncode != 0:
        print(f"stop: `claude stop {agent_id}` exited {proc.returncode}: "
              f"{proc.stderr.strip()}", file=sys.stderr, flush=True)
        return False
    print(f"stop: stopped {agent_id}.", file=sys.stderr, flush=True)
    return True


def candidate_ids(agents, cwd, exclude_ids):
    """Every background agent under `cwd` that did not exist before this launch.

    The same set `find_agent_id` narrows from, exposed on its own because "which one of
    these is mine" and "is there anything here at all" are two different questions and
    only the first is ambiguous. This answers the second, and it never ranks.
    """
    return [
        a["id"]
        for a in (agents or [])
        if a.get("kind") == "background"
        and a.get("cwd") == cwd
        and a.get("id")
        and a["id"] not in exclude_ids
    ]


def await_appearance(args, exclude_ids, deadline_fn):
    """Poll until the launched agent shows up. Returns (agent_id, error_message).

    The error is for the case the message describes — nothing started. When the appear
    window expires with candidates present but none identifiable, this returns
    (None, None): not this run's agent, and not an absence either. `main` reads that third
    answer as the blind watch (§ THE BLIND WATCH in this module's docstring).
    """
    while time.monotonic() < deadline_fn:
        agents = list_agents()
        if agents is None:
            return None, (
                f"⚠️ {args.label}: launched, but `claude agents --json` is unreadable — "
                f"cannot watch this run."
            )
        agent_id = find_agent_id(agents, args.name, args.cwd, exclude_ids, args.agent_id)
        if agent_id:
            return agent_id, None
        time.sleep(min(args.poll_seconds, 5.0))

    # A caller that passed --agent-id named its run exactly; an id that is not in the list
    # is a run that did not start under it, and whatever else is here belongs to somebody
    # else. So the blind watch is for the unnamed path only.
    if not args.agent_id and candidate_ids(list_agents(), args.cwd, exclude_ids):
        return None, None

    return None, (
        f"⚠️ {args.label}: launched, but no matching agent appeared within "
        f"{int(args.appear_seconds)}s — the run may not have started."
    )


def blind_watch(args, exclude_ids, deadline, head_before, head_repo, reports_before=None,
                marker_before=False):
    """Watch a set of runs none of which could be identified as this launch's.

    Two things must not happen when the watcher cannot name its run, and neither of them is
    about naming it. The process must not exit — a `--keep-awake` caffeinate is keyed to its
    lifetime, so an exit at the appear window releases the machine ~90 seconds into a run
    that is still going. And the ending must not be silent — the owner's one signal must
    arrive when the work actually stops, saying what it can and admitting what it cannot.

    So: hold while any candidate under `cwd` is still going, then report through the caller's
    own reporter. The body is honest under blindness because a reporter reads the ARTIFACT
    and the repo HEAD — facts about the launcher's own product, true whoever produced them —
    and never the agent's state. What is added is the part that is not honest by default: a
    line saying no run here was identified, and how many were waited for.

    Nothing is stopped. `claude stop` is what makes a wrong guess expensive
    (`find_agent_id` § THE THREE RULES, rule 3), and a watcher that could not identify its
    run has no id it is entitled to stop.
    """
    print(f"watch_agent: {args.label} — no run under {args.cwd} could be identified; "
          f"watching the candidate set blind", file=sys.stderr, flush=True)

    watched = candidate_ids(list_agents(), args.cwd, exclude_ids)
    while time.monotonic() < deadline:
        agents = list_agents()
        still_going = [
            i for i in watched
            if (state_of(agents, i) or "") not in TERMINAL_STATES
            and state_of(agents, i) is not None
        ]
        if not still_going:
            ctx = reporters.OutcomeContext(
                label=args.label,
                cwd=args.cwd,
                artifact_path=args.artifact_path,
                document_stem=args.document_stem,
                state="",
                head_before=head_before,
                head_after=git_head(head_repo),
                reports_before=reports_before,
            )
            try:
                outcome = reporters.get_reporter(args.reporter)(ctx)
                # The one place `produced_nothing` is attached — computed once, off the same
                # `ctx` the reporter above already read, so `_hook_outcome_for` below never
                # has to inspect it a second time. Inside the same `try`: a reporter that
                # raises must degrade to COMPLETED, and so must a bug in this read.
                outcome = dataclasses.replace(
                    outcome, produced_nothing=reporters.produced_nothing(ctx))
            except Exception:
                outcome = reporters.Outcome(f"{args.label}: run ended.")
            text = outcome.body
            text += (
                f"\n(this watcher could not identify which run was its own — it waited for "
                f"{len(watched)} background run(s) under {args.cwd} and all of them have "
                f"stopped; none was stopped by it)"
            )
            if outcome.footnote:
                text += "\n" + outcome.footnote
            notify(args.notify, text)
            if args.on_complete:
                # Blind, a multi-turn run is still finished only by its marker: every candidate
                # stopping without it is not a completion (§ THE ON-COMPLETE HOOK).
                cut_off = args.multi_turn and not completion_marker_seen(
                    args.done_when_exists, marker_before)
                run_on_complete_hook(
                    args.on_complete,
                    HookOutcome.STOPPED if cut_off else _hook_outcome_for(outcome))
            return 0
        time.sleep(args.poll_seconds)

    notify(
        args.notify,
        f"⏱️ {args.label}: {len(watched)} unidentified run(s) under {args.cwd} still going "
        f"after {int(args.timeout_seconds / 3600)}h — no longer watching.",
    )
    if args.on_complete:
        run_on_complete_hook(args.on_complete, HookOutcome.TIMEOUT)
    return 1


def main(argv=None):
    args = parse_args(argv)

    if args.list_ids:
        print(list_ids(args.cwd))
        return 0

    # This line is what makes an empty log mean "the watcher never started", and a log
    # with a start line but no send line mean "it died". Neither was knowable before.
    print(f"watch_agent: watching {args.label} under {args.cwd} at "
          f"{time.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr, flush=True)

    exclude_ids = {i for i in args.exclude_ids.split(",") if i}

    # The repo whose HEAD tells us if the run committed — the artifact's repo unless a
    # launcher points elsewhere. Captured before the watch, so an unchanged HEAD at the
    # end is proof this run committed nothing rather than a guess about timing. The
    # reporter decides what that proof means; the watcher only gathers it.
    head_repo = args.head_repo or args.artifact_path
    head_before = git_head(head_repo)

    # The other before-and-after fact, alongside head_before: whether the caller's
    # completion marker already exists. Read once, before the watch, so a stale marker
    # from a previous run is inert for the whole life of this one (§ completion_marker_seen).
    marker_before = completion_marker_seen(args.done_when_exists, present_before=False)

    # The third before-and-after fact, on the same rule as the two above: which self-answer
    # reports were already on disk. A report that predates the watch cannot be this run's, so
    # the reporter excludes it rather than reading back a predecessor's verdict — measured on
    # a live product 2026-09-04, where a run that wrote nothing was reported as "already answered,
    # nothing left to work" off a report three days old, and the chain booked the round.
    # Read once, here, for the same reason `marker_before` is: re-deriving it during the watch
    # would let the run's own report count as pre-existing.
    reports_before = reporters.self_answer_reports_present(
        args.artifact_path, args.document_stem or None) if args.artifact_path else ()

    agent_id, error = await_appearance(
        args, exclude_ids, time.monotonic() + args.appear_seconds
    )
    if error:
        notify(args.notify, error)
        if args.on_complete:
            run_on_complete_hook(args.on_complete, HookOutcome.APPEAR_ERROR)
        return 1

    deadline = time.monotonic() + args.timeout_seconds

    # The third answer: no id, and no error either. Runs are here and none of them could be
    # told apart, which is a reporting failure and must not also be a released keep-awake
    # and a silent ending.
    if not agent_id:
        return blind_watch(args, exclude_ids, deadline, head_before, head_repo,
                           reports_before, marker_before)

    consecutive_idle_polls = 0
    while time.monotonic() < deadline:
        agents = list_agents()
        state = state_of(agents, agent_id)
        status = status_of(agents, agent_id)
        # Reset on anything that is not an idle read — a status that goes idle, busy,
        # idle is a run between tool calls, not a run that ended. Maintained unconditionally
        # — --multi-turn gates only whether the debounce below is CONSULTED, not whether it
        # is kept, so the value stays available to the message below either way.
        consecutive_idle_polls = (
            consecutive_idle_polls + 1 if status == IDLE_STATUS else 0
        )
        # The caller's own statement that the run is over, read every poll and even when
        # `agents` is None: an unreadable `claude` CLI is a reason this watcher cannot see
        # the agent, not a reason to miss the run saying it is done (§ completion_marker_seen).
        marker_seen = completion_marker_seen(args.done_when_exists, marker_before)
        # A multi-turn run ends its turn once per turn it hands out, so `status: idle` is
        # not an ending for it — the debounce below is consulted only when the caller did
        # not declare itself multi-turn (§ IT STOPS THE RUN IT WATCHED / --multi-turn).
        idle_terminal = (
            not args.multi_turn and consecutive_idle_polls >= IDLE_POLLS_BEFORE_TERMINAL
        )

        # Which states end THIS watch: a run that declared itself multi-turn is not ended by
        # a state that only reports a turn boundary (§ MULTI_TURN_TERMINAL_STATES).
        terminal_states = (
            MULTI_TURN_TERMINAL_STATES if args.multi_turn else TERMINAL_STATES
        )

        if state in terminal_states or idle_terminal or marker_seen:
            # The reporter composes the outcome body; the watcher appends the state as a
            # footnote and, when the reporter asked for one, its trailing caveat. The
            # reporter is best-effort like the notify — one that raises must not cost the
            # message, so it degrades to the plain end here.
            ctx = reporters.OutcomeContext(
                label=args.label,
                cwd=args.cwd,
                artifact_path=args.artifact_path,
                document_stem=args.document_stem,
                state=state,
                head_before=head_before,
                head_after=git_head(head_repo),
                reports_before=reports_before,
            )
            try:
                outcome = reporters.get_reporter(args.reporter)(ctx)
                # The one place `produced_nothing` is attached — computed once, off the same
                # `ctx` the reporter above already read, so `_hook_outcome_for` below never
                # has to inspect it a second time. Inside the same `try`: a reporter that
                # raises must degrade to COMPLETED, and so must a bug in this read.
                outcome = dataclasses.replace(
                    outcome, produced_nothing=reporters.produced_nothing(ctx))
            except Exception:
                outcome = reporters.Outcome(f"{args.label}: run ended.")
            text = outcome.body
            # Above the state note, not below it: the state reads as a clean end and the
            # refusal is the better witness for the same question. A correction placed
            # under a flattering line is the shape that failed here once already.
            refusal = refusal_of(session_id_of(agents, agent_id))
            if refusal:
                text += "\n" + refusal_note(refusal)
            # Only when THIS ending was reached on the marker — not merely because
            # --done-when-exists was given — so a state-triggered ending still reads as
            # that state (§ state_note).
            marker_path = args.done_when_exists if marker_seen else None
            text += "\n" + state_note(state, agent_id, status, marker_path)
            if outcome.footnote:
                text += "\n" + outcome.footnote
            # Notify first, stop second. The message is the whole point of this process;
            # a `claude stop` that hangs must not be able to swallow it.
            notify(args.notify, text)
            if args.on_complete:
                # A multi-turn run says it is finished with its marker, so `stopped` without
                # one is a run cut off mid-walk — never a completion (§ THE ON-COMPLETE HOOK).
                # A single-turn run keeps the reporter's reading: a clean halt reports
                # `stopped` there too.
                cut_off = args.multi_turn and state == "stopped" and not marker_seen
                run_on_complete_hook(
                    args.on_complete,
                    HookOutcome.STOPPED if cut_off else _hook_outcome_for(outcome))
            if state != "stopped":
                stop_agent(agent_id)
            return 0

        if agents is not None and state is None:
            # It was in the list, now it is gone — `--all` keeps completed runs, so a
            # disappearance is not a normal completion and should not pass as silence.
            notify(args.notify, f"⚠️ {args.label}: run {agent_id} vanished from the agent list.")
            if args.on_complete:
                run_on_complete_hook(args.on_complete, HookOutcome.VANISHED)
            return 1

        time.sleep(args.poll_seconds)

    timeout_message = (
        f"⏱️ {args.label}: run {agent_id} still going after "
        f"{int(args.timeout_seconds / 3600)}h — no longer watching."
    )
    if args.done_when_exists:
        # "Still going" and "the run finished and never said so" are different problems,
        # and the owner cannot tell them apart from the plain timeout sentence alone
        # (§ SILENCE IS NOT SUCCESS, applied to the ending this flag makes more likely).
        timeout_message += f" The marker at {args.done_when_exists} never appeared."
    notify(args.notify, timeout_message)
    if args.on_complete:
        run_on_complete_hook(args.on_complete, HookOutcome.TIMEOUT)
    return 1


if __name__ == "__main__":
    sys.exit(main())
