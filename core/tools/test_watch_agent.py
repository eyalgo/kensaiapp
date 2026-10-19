"""Contract tests for `watch_agent.py` — the completion watcher.

The watcher watches a `--bg` run to a terminal state and composes the notification. What
the run PRODUCED is the reporter's to say (reporters.py, test_reporters.py); this file
pins what the WATCHER owns:

- **It routes to the named --reporter and never reads a run's files itself.** The outcome
  body comes from `reporters.get_reporter(name)`; the watcher appends the state as a
  footnote and the reporter's optional trailing caveat. An unknown reporter, or one that
  raises, degrades to the plain "run ended." — the message must never be lost.
- **The state is a footnote, not the outcome.** Measured over seven real runs: `done`
  never occurs, `blocked` is what a run reports when it *finished* and went idle, and
  `stopped` covers both a clean halt and a session that never started. So the state
  qualifies the outcome; it never claims how the work went.
- **One death is named, and only the one that is written down.** A refused run reaches
  `blocked` — "finished its turn and is idle" — while its transcript records the refusal
  with a category and a model. The watcher reads that record and puts it ABOVE the state
  note, because a correction underneath a flattering line is the shape that failed. It says
  what the record says and never that the record ended the run; every other way a run can
  die still reads as the hedge.
- **It gathers the HEAD, the reporter judges it.** `git_head` before the watch and at the
  terminal state; the reporter decides whether an unchanged HEAD means "committed nothing".
- **Silence is not success** — every exit path notifies. An agent that never appears, an
  agent that vanishes, a timeout, and an unreadable `claude` CLI must each produce a
  message, not quiet. This extends to delivery: a send whose outcome is not written down
  is a send nobody can audit.
- **Identity** — the watched agent is (name, cwd, id-not-seen-before). A relaunch reuses
  the same fixed prompt, so name alone would match the previous run.
- **A run ends two ways, and only one of them is a `state`.** A run whose process exited
  reaches a terminal state and reports no `status` key at all. A run whose *turn* ended
  while its process is still alive reports `status: idle` and keeps `state: working` —
  in no terminal set, so a state-only watch polls to its deadline and sends nothing. That
  second ending is terminal too, DEBOUNCED over two consecutive polls where a state is
  immediate. The entries these tests build carry no `status` unless one is asked for,
  which is what pins "a record without the key is watched exactly as it always was".

A handful of `--reporter prd` tests remain here as integration — proof the watcher routes
to a reporter and composes body + state note + footnote end to end. The exhaustive PRD
outcome cases live in test_reporters.py.

`list_agents` is monkeypatched to return a scripted sequence of agent lists — no
`claude` process, no sleeping. `--poll-seconds 0` keeps the loops instant.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import watch_agent  # noqa: E402

CWD = "/repo"
NAME = "invoke the product-prd skill for the example-product project."

# Captured before the autouse `stops` fixture replaces it, so the tests that exercise the
# real stop_agent can still reach it.
REAL_STOP_AGENT = watch_agent.stop_agent


def agent(agent_id, state, name=NAME, cwd=CWD, kind="background", started=1,
          session_id=None, status=None):
    """`session_id` and `status` are omitted from the entry unless given — the shape a
    list without them takes, which is what those reads must degrade on rather than raise.

    `status` defaulting to omitted is the load-bearing part. Every test written before
    Claude Code began reporting a `status` builds its entry through here, so they go on
    pinning the watcher's pre-`status` behaviour without a line changing in any of them —
    which is what proves the new terminal condition added a case rather than moved one."""
    entry = {
        "id": agent_id,
        "name": name,
        "cwd": cwd,
        "kind": kind,
        "state": state,
        "startedAt": started,
    }
    if session_id is not None:
        entry["sessionId"] = session_id
    if status is not None:
        entry["status"] = status
    return entry


# The real record, from the run this came from: a --bg CPO session that died on a model
# refusal and was reported as "finished its turn and is idle". Every key below is copied
# from ~/.claude/projects/<slug>/ae3783a2-ef0d-4f47-ad2a-737137feb0ae.jsonl, line 144.
REAL_SESSION_ID = "ae3783a2-ef0d-4f47-ad2a-737137feb0ae"
REFUSAL_RECORD = {
    "type": "system",
    "subtype": "model_refusal_no_fallback",
    "content": "",
    "level": "warning",
    "originalModel": "claude-fable-5",
    "apiRefusalCategory": "reasoning_extraction",
    "apiRefusalExplanation": "This request was blocked as it seems to violate Anthropic's "
                            "Terms of Service restrictions on reverse engineering or "
                            "duplicating model outputs.",
    "sessionKind": "bg",
    "sessionId": REAL_SESSION_ID,
    "timestamp": "2026-08-20T06:06:20.080Z",
}


def transcript(projects_dir, session_id, *records, project="-repo"):
    """Write a session transcript where the watcher looks for one."""
    import json as _json
    d = projects_dir / project
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{session_id}.jsonl"
    f.write_text("".join(_json.dumps(r) + "\n" for r in records))
    return f


@pytest.fixture
def sent(monkeypatch):
    """Capture notifier messages instead of shelling out."""
    messages = []
    monkeypatch.setattr(watch_agent, "notify", lambda notifier, msg: messages.append(msg))
    return messages


@pytest.fixture(autouse=True)
def stops(monkeypatch):
    """Record which agents were stopped, instead of shelling out to `claude stop`.

    Autouse deliberately: every terminal-state test reaches the stop, so without this one
    of them would eventually run `claude stop a1` against the real CLI. A test suite that
    reaches for the machine's actual background agents is not a test suite.
    """
    calls = []

    def _fake(agent_id):
        calls.append(agent_id)
        return True

    monkeypatch.setattr(watch_agent, "stop_agent", _fake)
    return calls


@pytest.fixture
def hooks(monkeypatch):
    """Record --on-complete hook invocations, instead of shelling out.

    Not autouse: only a test that passes --on-complete exercises the hook at all, so a
    test carrying neither this fixture nor the flag is untouched by it.
    """
    calls = []

    def _fake(hook, *args, **kwargs):
        calls.append((hook, args, kwargs))
        return True

    monkeypatch.setattr(watch_agent, "run_on_complete_hook", _fake)
    return calls


@pytest.fixture
def scripted(monkeypatch):
    """Return `script(*lists)` — each call to list_agents() returns the next list.

    The final list repeats once exhausted, so a loop that keeps polling sees a stable
    world rather than an IndexError.
    """

    def _script(*lists):
        calls = list(lists)

        def _fake():
            return calls.pop(0) if len(calls) > 1 else calls[0]

        monkeypatch.setattr(watch_agent, "list_agents", _fake)

    return _script


def run_watcher(*extra):
    return watch_agent.main(
        ["--name", NAME, "--label", "example-product", "--cwd", CWD,
         "--notify", "/nonexistent", "--poll-seconds", "0", *extra]
    )


BUCKET_TITLES = {
    1: "Open issues — product-defining questions with no answer yet",
    2: "Choices to confirm — the CPO drafted a best-effort answer; confirm or override",
    3: "Directives — an action you asked for that the CPO can't perform itself",
}


def companion(n1=0, n2=0, n3=0):
    """A companion shaped like the real one — em-dash headings, prose for empty buckets.

    The prose matters: an empty bucket has no sentinel on disk, it just says something
    like "None this cycle.". A parser that looks for a marker finds nothing and must
    still count zero.
    """
    out = []
    for bucket, n in ((1, n1), (2, n2), (3, n3)):
        out.append(f"## {bucket}. {BUCKET_TITLES[bucket]}\n")
        if n == 0:
            out.append("None this cycle.\n")
        for i in range(1, n + 1):
            out.append(f"### {bucket}.{i} the decision, in one line\n")
            out.append("- **Why it matters:** because.\n")
    return "\n".join(out)


def product(tmp_path, prd=True, open_issues=False, status="Settled", version=2,
            trail=(), buckets=(0, 1, 0)):
    """A product tree shaped like the one product-prd authors into.

    `trail` is the cycle numbers present in trail/prd/, e.g. `(1,)` or `(1, 3)`.
    """
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if prd:
        (docs / "PRD.md").write_text(
            f"# PRD — thing\n\n**Status:** {status}\n**Owner:** CPO\n"
            f"**Version:** {version} — what this revision changed\n"
        )
    if open_issues:
        (docs / "PRD_open_issues.md").write_text(companion(*buckets))
    if trail:
        (docs / "trail/prd").mkdir(parents=True, exist_ok=True)
        for n in trail:
            (docs / "trail/prd" / f"cycle-{n}.md").write_text("# cycle\n")
    return str(tmp_path)


def notifier_script(tmp_path, exit_code=0, stderr_text=""):
    """A stand-in notifier script with a chosen exit code and diagnostic."""
    path = tmp_path / "notify_stub.sh"
    path.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s\\n' {stderr_text!r} >&2\n"
        f"exit {exit_code}\n"
    )
    path.chmod(0o755)
    return str(path)


def hook_script(tmp_path, exit_code=0, stderr_text="", record_path=None, sleep_seconds=None):
    """A stand-in for an --on-complete hook. Records the one argument it was given (its
    outcome) to `record_path`, when given one, so a test can read back what it received."""
    path = tmp_path / "on_complete_stub.sh"
    lines = ["#!/usr/bin/env bash"]
    if sleep_seconds is not None:
        lines.append(f"sleep {sleep_seconds}")
    if record_path is not None:
        lines.append(f"printf '%s\\n' \"$1\" >> {str(record_path)!r}")
    if stderr_text:
        lines.append(f"printf '%s\\n' {stderr_text!r} >&2")
    lines.append(f"exit {exit_code}")
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o755)
    return str(path)


# --- the state is a footnote, not the outcome --------------------------------
#
# It still says which terminal state was reached — `blocked` (reached a natural stop)
# and `stopped` (something ended it) are genuinely different facts. What it must never
# do is claim how the work went. Run with no --product-path so these pin the qualifier
# in isolation.


@pytest.mark.parametrize(
    "state, expect",
    [("done", "state: done"),
     ("stopped", "was stopped"),
     ("blocked", "finished its turn and is idle")],
)
def test_each_terminal_state_notifies_with_its_own_note(scripted, sent, state, expect):
    scripted([agent("a1", state)])

    rc = run_watcher()

    assert rc == 0
    assert len(sent) == 1
    assert expect in sent[0]


def test_a_stopped_run_is_never_called_a_failure(scripted, sent):
    """1.1.0 said "stopped before finishing". A clean 39-minute halt reports `stopped`,
    so that wording called real, finished work a failure."""
    scripted([agent("a1", "stopped")])

    run_watcher()

    assert "stopped before finishing" not in sent[0]


def test_waits_through_a_running_agent_until_it_stops(scripted, sent):
    scripted(
        [agent("a1", "running")],
        [agent("a1", "running")],
        [agent("a1", "blocked")],
    )

    rc = run_watcher()

    assert rc == 0
    assert "run ended" in sent[0]


# --- integration: the watcher routes to a reporter and composes the message --
#
# These go through main() with --reporter prd, proving the watcher selects the reporter,
# composes body + state note + footnote, and that --product-path still feeds the reporter
# its artifact. The exhaustive prd outcome cases are unit-tested in test_reporters.py.


def test_prd_reporter_settled_run_says_nothing_is_pending(scripted, sent, tmp_path):
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "prd", "--product-path", product(tmp_path, status="Settled"))

    assert "settled" in sent[0]
    assert "nothing pending" in sent[0].lower()


def test_prd_reporter_open_issues_names_the_file_and_the_state_rides_along(scripted, sent, tmp_path):
    """One end-to-end proof that body and state note compose: the outcome names the file
    to answer, and the footnote still carries which terminal state was reached."""
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "prd", "--product-path",
                product(tmp_path, status="Draft", open_issues=True, buckets=(0, 1, 0)))

    assert "PRD_open_issues.md" in sent[0]
    assert "commit" in sent[0]
    assert "re-run" in sent[0]
    assert "idle" in sent[0]          # the state note (blocked) rode along on the message


def test_a_stopped_run_still_reports_what_is_on_disk(scripted, sent, tmp_path):
    """The inverse of what 1.1.0 believed. It read the product only on `done` because
    "a stopped run never got to write one" — but `stopped` is what a clean halt after
    real work reports, and that work is sitting right there on disk."""
    scripted([agent("a1", "stopped")])

    run_watcher("--reporter", "prd", "--product-path",
                product(tmp_path, status="Draft", open_issues=True, trail=(1,)))

    assert "cycle 2 complete" in sent[0]
    assert "was stopped" in sent[0]


# --- a run that did nothing must not inherit the last run's work -------------


def test_a_run_that_committed_nothing_says_so(scripted, sent, tmp_path, monkeypatch):
    """A session that never started leaves the previous run's files on disk. Reading
    them without this check would announce work this run did not do. The prd reporter
    owns the caveat; this proves it rides through the watcher onto the message."""
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    scripted([agent("a1", "stopped")])

    run_watcher("--reporter", "prd", "--product-path",
                product(tmp_path, status="Draft", open_issues=True, trail=(1,)))

    assert "committed nothing" in sent[0]


def test_a_run_that_committed_is_not_flagged(scripted, sent, tmp_path, monkeypatch):
    heads = iter(["before-sha", "after-sha"])
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: next(heads))
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "prd", "--product-path",
                product(tmp_path, status="Draft", open_issues=True, trail=(1,)))

    assert "committed nothing" not in sent[0]


def test_a_product_that_is_not_a_repo_is_not_flagged(scripted, sent, tmp_path):
    """git_head returns None outside a git repo, and an unknown HEAD is not
    evidence of an idle run."""
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "prd", "--product-path", product(tmp_path, status="Settled"))

    assert "committed nothing" not in sent[0]


# --- routing: the watcher selects a reporter and never crashes on a bad one ---
#
# The 'future ones' property lives here: a reporter the watcher was never taught about is
# reached through the registry alone, and a broken or unknown one degrades to the plain
# end rather than costing the message. The outcome-content best-effort cases (unreadable
# product, parser bug) are the reporter's, and live in test_reporters.py.


def test_no_reporter_defaults_to_the_generic_end(scripted, sent):
    """The watcher stays usable for any agent — no --reporter is the plain run-ended."""
    scripted([agent("a1", "blocked")])

    rc = run_watcher()

    assert rc == 0
    assert "run ended" in sent[0]


def test_an_unknown_reporter_falls_back_to_generic(scripted, sent):
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "does-not-exist")

    assert "run ended" in sent[0]


def test_a_reporter_that_raises_degrades_to_the_plain_end(scripted, sent, monkeypatch):
    """A reporter is best-effort like the notify: if it blows up, the person still gets a
    message. The watcher's own try/except is the net under the reporter's."""
    def boom(_ctx):
        raise ValueError("reporter blew up")

    monkeypatch.setitem(watch_agent.reporters.REGISTRY, "boom", boom)
    scripted([agent("a1", "blocked")])

    rc = run_watcher("--reporter", "boom")

    assert rc == 0
    assert "run ended" in sent[0]


def test_a_newly_registered_reporter_is_routed_without_touching_the_watcher(scripted, sent, monkeypatch):
    """Add an entry to the registry and the watcher routes to it — no edit to the watcher.
    That is what makes a future run type a reporters.py change alone."""
    def custom(ctx):
        return watch_agent.reporters.Outcome(f"{ctx.label}: custom body.")

    monkeypatch.setitem(watch_agent.reporters.REGISTRY, "custom-kind", custom)
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "custom-kind")

    assert "custom body" in sent[0]


def test_apply_packet_reporter_reads_the_head_repo(scripted, sent, monkeypatch):
    """End-to-end for a non-prd reporter: --head-repo feeds git_head, and a moved HEAD
    becomes 'committed'. Proves head tracking is generic, not prd-only."""
    heads = iter(["before", "after"])
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: next(heads))
    scripted([agent("a1", "blocked")])

    run_watcher("--reporter", "apply-packet", "--head-repo", "/repo")

    assert "committed" in sent[0]


# --- delivery: a send nobody wrote down is a send nobody can audit -----------
#
# The `sent` fixture replaces notify wholesale, so these call the real thing against a
# stub notifier script.


def test_a_successful_send_is_logged(tmp_path, capsys):
    ok = watch_agent.notify(notifier_script(tmp_path, exit_code=0), "hello")

    assert ok is True
    assert "notify: sent." in capsys.readouterr().err


def test_a_rejected_send_is_logged(tmp_path, capsys):
    """A notifier exits 1 with a diagnostic when its service rejects the send.
    1.1.0 ignored the exit code, so this was indistinguishable from success."""
    notifier = notifier_script(tmp_path, exit_code=1, stderr_text="send rejected: bad token")

    ok = watch_agent.notify(notifier, "hello")

    err = capsys.readouterr().err
    assert ok is False
    assert "exited 1" in err
    assert "send rejected" in err


def test_a_notifier_that_will_not_run_is_logged(tmp_path, capsys):
    ok = watch_agent.notify(str(tmp_path / "nope" / "missing.sh"), "hello")

    assert ok is False
    assert "did not run" in capsys.readouterr().err


def test_no_notifier_is_logged_and_nothing_runs(capsys):
    """KENSAIAPP_NOTIFIER unset leaves no notifier: the message is still printed, nothing is
    sent, and the log says why rather than raising."""
    ok = watch_agent.notify(None, "hello")

    captured = capsys.readouterr()
    assert ok is False
    assert "hello" in captured.out
    assert "no notifier set (KENSAIAPP_NOTIFIER)" in captured.err


def test_the_default_notifier_comes_from_the_environment_with_no_fallback(monkeypatch):
    monkeypatch.delenv("KENSAIAPP_NOTIFIER", raising=False)
    assert watch_agent.parse_args(["--name", "x", "--label", "l"]).notify is None
    monkeypatch.setenv("KENSAIAPP_NOTIFIER", "/opt/notify.sh")
    assert watch_agent.parse_args(["--name", "x", "--label", "l"]).notify == "/opt/notify.sh"


def test_the_message_is_printed_even_when_the_send_fails(tmp_path, capsys):
    """Print before the attempt, so the log carries the text we meant to send even if
    the notifier hangs or the process dies mid-send."""
    watch_agent.notify(notifier_script(tmp_path, exit_code=1), "the message body")

    assert "the message body" in capsys.readouterr().out


def test_the_watcher_announces_itself_on_stderr(scripted, sent, capsys):
    """This is what makes an empty log mean "never started" and a start line with no
    send line mean "died" — the two that were indistinguishable."""
    scripted([agent("a1", "blocked")])

    run_watcher()

    assert "watch_agent: watching example-product" in capsys.readouterr().err


# --- stopping the run it watched ---------------------------------------------
#
# A finished --bg session does not exit; it idles holding its memory, waiting for a
# prompt nobody will type. `claude stop` keeps the conversation and `claude attach` still
# resumes it, so there is nothing to lose and no flag to gate.


def test_a_finished_run_is_stopped(scripted, sent, stops):
    scripted([agent("a1", "blocked")])

    run_watcher()

    assert stops == ["a1"]


def test_an_already_stopped_run_is_not_stopped_again(scripted, sent, stops):
    scripted([agent("a1", "stopped")])

    run_watcher()

    assert stops == []


def test_a_run_that_is_still_working_is_never_stopped(scripted, sent, stops):
    """The timeout means "I stopped watching", not "the run is finished". Killing a run
    that is still working after six hours would destroy the thing we were waiting for."""
    scripted([agent("a1", "running")])

    run_watcher("--timeout-seconds", "0")

    assert stops == []


def test_a_vanished_run_is_not_stopped(scripted, sent, stops):
    scripted([agent("a1", "running")], [])

    run_watcher()

    assert stops == []


def test_a_run_that_never_appeared_is_not_stopped(scripted, sent, stops):
    scripted([])

    run_watcher("--appear-seconds", "0.01")

    assert stops == []


def test_the_notification_goes_out_before_the_stop(scripted, monkeypatch):
    """The message is the whole point of this process; a `claude stop` that hangs must
    not be able to swallow it."""
    order = []
    monkeypatch.setattr(watch_agent, "notify", lambda _n, _m: order.append("notify"))
    monkeypatch.setattr(watch_agent, "stop_agent", lambda _a: order.append("stop"))
    scripted([agent("a1", "blocked")])

    run_watcher()

    assert order == ["notify", "stop"]


def test_a_failed_stop_is_logged_and_does_not_raise(monkeypatch, capsys):
    class _Rejected:
        returncode = 1
        stderr = "no such session"

    monkeypatch.setattr(watch_agent.subprocess, "run", lambda *a, **k: _Rejected())

    assert REAL_STOP_AGENT("a1") is False
    assert "exited 1" in capsys.readouterr().err


def test_a_stop_that_cannot_run_is_logged_and_does_not_raise(monkeypatch, capsys):
    def boom(*_a, **_k):
        raise OSError("claude not on PATH")

    monkeypatch.setattr(watch_agent.subprocess, "run", boom)

    assert REAL_STOP_AGENT("a1") is False
    assert "could not run" in capsys.readouterr().err


def test_a_successful_stop_is_logged(monkeypatch, capsys):
    class _Ok:
        returncode = 0
        stderr = ""

    monkeypatch.setattr(watch_agent.subprocess, "run", lambda *a, **k: _Ok())

    assert REAL_STOP_AGENT("a1") is True
    assert "stopped a1" in capsys.readouterr().err


# --- silence is not success --------------------------------------------------


def test_agent_that_never_appears_notifies(scripted, sent):
    scripted([])

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert len(sent) == 1
    assert "no matching agent appeared" in sent[0]


def test_unreadable_claude_cli_notifies(monkeypatch, sent):
    monkeypatch.setattr(watch_agent, "list_agents", lambda: None)

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert "unreadable" in sent[0]


def test_agent_vanishing_from_the_list_notifies(scripted, sent):
    """`--all` retains completed runs, so a disappearance is not a normal
    completion and must not pass as silence."""
    scripted(
        [agent("a1", "running")],
        [],
    )

    rc = run_watcher()

    assert rc == 1
    assert "vanished" in sent[0]


def test_timeout_notifies(scripted, sent):
    scripted([agent("a1", "running")])

    rc = run_watcher("--timeout-seconds", "0")

    assert rc == 1
    assert "still going" in sent[0]


# --- identity ----------------------------------------------------------------


def test_excluded_ids_are_not_watched(scripted, sent):
    """The pre-launch snapshot's agents are somebody else's run."""
    scripted([agent("old", "done")])

    rc = run_watcher("--exclude-ids", "old", "--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


def test_newest_matching_agent_wins(scripted, sent):
    scripted([agent("old", "stopped", started=1), agent("new", "blocked", started=99)])

    rc = run_watcher()

    assert rc == 0
    assert "new" in sent[0]


def test_agent_in_another_cwd_is_not_watched(scripted, sent):
    scripted([agent("a1", "done", cwd="/somewhere/else")])

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


# --- the retitle: the name is a preference, the id is the handle -------------
#
# Measured 2026-08-22 from /private/tmp/wa-probe: `claude --bg "Reply with the single word
# OK and stop."` was listed by `claude agents --json --all` as `"name": "user intent
# extraction task"` — an AI title, on a run launched seconds earlier. The name the launcher
# passed cannot be matched, so a run that started fine reads as one that never started.
#
# What identifies the run instead is what the launcher already knows: a background agent
# under --cwd whose id was NOT in the pre-launch --exclude-ids snapshot. The name is kept
# as a PREFERENCE, so every launcher that still matches by name behaves exactly as before,
# and an explicit --agent-id is the exact handle for a launcher that captured the id at
# launch.

# The title Claude Code actually gave the probe run. Nothing about it is derivable from the
# prompt, which is the whole point.
AI_TITLE = "user intent extraction task"


def test_a_retitled_agent_is_still_found(scripted, sent):
    """The defect: the only candidate is ours, and its name no longer matches."""
    scripted([agent("a1", "blocked", name=AI_TITLE)])

    rc = run_watcher()

    assert rc == 0
    assert "run ended" in sent[0]


def test_an_explicit_agent_id_matches_whatever_the_name_is(scripted, sent):
    """A launcher that captured the id at launch needs no name at all."""
    scripted([agent("a1", "blocked", name=AI_TITLE)])

    rc = watch_agent.main(
        ["--agent-id", "a1", "--label", "example-product", "--cwd", CWD,
         "--notify", "/nonexistent", "--poll-seconds", "0"]
    )

    assert rc == 0
    assert "run ended" in sent[0]


def test_an_explicit_agent_id_beats_a_name_matching_sibling(scripted, sent, stops):
    """The id is authoritative: a sibling whose name still matches is not this run."""
    scripted(
        [
            agent("mine", "blocked", name=AI_TITLE, started=1),
            agent("theirs", "blocked", name=NAME, started=99),
        ]
    )

    rc = run_watcher("--agent-id", "mine")

    assert rc == 0
    assert stops == ["mine"]


def test_the_name_still_decides_when_it_matches(scripted, sent, stops):
    """The disambiguation the name check provides survives. An agent still carrying the
    launcher's own prompt is this run, even when a retitled stranger started later."""
    scripted(
        [
            agent("mine", "blocked", name=NAME, started=1),
            agent("theirs", "blocked", name=AI_TITLE, started=99),
        ]
    )

    rc = run_watcher()

    assert rc == 0
    assert stops == ["mine"]


def test_two_unidentifiable_candidates_are_refused_rather_than_guessed(scripted, sent, stops):
    """Ambiguity is not resolved by guessing. Two retitled candidates, neither excluded and
    neither name-matching, cannot be told apart — and a guess would be stopped by `claude
    stop`, so it would stop somebody else's run.

    What the refusal costs has changed, and this test is where that shows. It used to end
    the watch: rc 1, "no matching agent appeared", and the process gone. Both candidates
    here are already `blocked`, so the blind watch has nothing left to wait for and ends
    immediately — but it ends by REPORTING rather than by disappearing, and it still stops
    nothing. The refusal to guess is untouched; only what follows it is."""
    scripted(
        [
            agent("a1", "blocked", name=AI_TITLE, started=1),
            agent("a2", "blocked", name="some other title", started=99),
        ]
    )

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 0
    assert "no matching agent appeared" not in sent[0]
    assert stops == []


# --- the blind watch: a watcher that cannot identify its run still holds and still reports ---
#
# `find_agent_id` refusing to rank two candidates is correct and is not touched here. What was
# wrong is what came after it: the watcher exited ~90 seconds into a run that was still going,
# and three things went down with it — the `--keep-awake` caffeinate bound to its lifetime, the
# completion ping, and the `claude stop` that tidies up. The message it left, "the run may not
# have started", was the only signal the owner got, and it was wrong in both directions at once.
#
# So the appear deadline now asks one more question — is there anything under this cwd at all? —
# and the two answers are two paths. Nothing there: the message is true, and nothing changes.
# Candidates there but unidentifiable: hold, watch the set, and report at the real end.


def test_a_blind_watcher_with_candidates_running_does_not_give_up_at_the_appear_window(
    scripted, sent, stops
):
    """The half the seed measured at ~90 seconds into a 34-minute run. Two candidates neither
    of which can be identified, both still `running`: the watcher must not send the false alarm
    and must not exit, because a keep-awake keyed to its lifetime follows it down."""
    scripted(
        [
            agent("a1", "running", name=AI_TITLE, started=1),
            agent("a2", "running", name="some other title", started=99),
        ],
        [
            agent("a1", "running", name=AI_TITLE, started=1),
            agent("a2", "running", name="some other title", started=99),
        ],
        [
            agent("a1", "done", name=AI_TITLE, started=1),
            agent("a2", "done", name="some other title", started=99),
        ],
    )

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 0
    assert len(sent) == 1, f"expected exactly one message, at the end: {sent}"
    assert "may not have started" not in sent[0], (
        f"a blind watcher raised the never-started alarm on runs that were working: {sent[0]!r}"
    )
    assert stops == [], "a watcher stopped a run it never identified"


def test_a_blind_watcher_reports_what_it_could_not_identify(scripted, sent):
    """The ending must not be silent, and it must not overclaim. The body is the caller's own
    reporter's — it reads the artifact and the repo HEAD, facts about the launcher's product that
    are true whoever ran them — and what this watcher could not do is said outright rather than
    left for the owner to infer from a message that reads like an ordinary completion."""
    scripted(
        [
            agent("a1", "done", name=AI_TITLE, started=1),
            agent("a2", "done", name="some other title", started=99),
        ]
    )

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 0
    assert "could not identify" in sent[0].lower(), (
        f"the degraded ending reads as an ordinary one: {sent[0]!r}"
    )
    assert "2" in sent[0], f"the message does not say how many runs it waited for: {sent[0]!r}"


def test_a_blind_watcher_still_gives_up_after_the_timeout(scripted, sent, stops):
    """The 6-hour path is not bypassed by the blind watch — it is the same deadline, reached the
    same way. A set of candidates that never finishes ends in the still-going message, not in a
    process that holds a machine awake forever."""
    scripted(
        [
            agent("a1", "running", name=AI_TITLE, started=1),
            agent("a2", "running", name="some other title", started=99),
        ]
    )

    rc = run_watcher("--appear-seconds", "0.01", "--timeout-seconds", "0.05")

    assert rc == 1
    assert "still going" in sent[0], f"expected the timeout message, got: {sent[0]!r}"
    assert stops == []


def test_nothing_under_this_cwd_is_still_reported_as_a_run_that_may_not_have_started(
    scripted, sent
):
    """The other branch, unchanged and deliberately so. With no candidate at all the original
    message is exactly right, and blurring the two would lose the one case where the watcher
    genuinely does know something is wrong."""
    scripted([agent("elsewhere", "running", name=AI_TITLE, cwd="/somewhere/else")])

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


def test_an_explicit_agent_id_that_never_appears_is_not_blind_watched(scripted, sent):
    """A caller that passed `--agent-id` named its run exactly. If that id is not in the list,
    the run really did not start under it, and candidates around it are somebody else's — so
    this keeps the original message rather than holding for runs that are not ours."""
    scripted(
        [
            agent("a1", "running", name=AI_TITLE, started=1),
            agent("a2", "running", name="some other title", started=99),
        ]
    )

    rc = run_watcher("--agent-id", "never-launched", "--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


def test_a_retitled_agent_in_the_pre_launch_snapshot_is_not_watched(scripted, sent):
    """The snapshot is what makes the fallback sound — an agent that existed before this
    launch is somebody else's run however it is now titled."""
    scripted([agent("old", "done", name=AI_TITLE)])

    rc = run_watcher("--exclude-ids", "old", "--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


def test_a_snapshot_that_landed_identifies_the_retitled_run_beside_an_older_one(scripted, sent):
    """The `--exclude-ids` half of the rule, exercised where it can actually do work.

    The rule reads "a background agent under `cwd` whose id was not in the pre-launch
    snapshot", and its two neighbours here each hold one agent — so the exclusion set is
    either empty or holds the only candidate, and never has to SEPARATE anything. This is
    the case where it does: an older run and this launch's, this one retitled past its
    name, and the snapshot is the whole of what tells them apart.

    Measured against 1.7.0, where the same list returns None: the rescue does not merely
    survive an older sibling, it depends on the snapshot having caught it."""
    scripted([
        agent("old", "done", name="an earlier run's title", started=1),
        agent("new", "done", name=AI_TITLE, started=2),
    ])

    rc = run_watcher("--exclude-ids", "old")

    assert rc == 0
    assert "run ended" in sent[0]


def test_a_retitled_agent_in_another_cwd_is_not_watched(scripted, sent):
    scripted([agent("a1", "done", name=AI_TITLE, cwd="/somewhere/else")])

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


def test_a_retitled_interactive_session_is_not_watched(scripted, sent):
    scripted([agent("a1", "done", name=AI_TITLE, kind="interactive")])

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


def test_a_multiline_launch_name_matches_its_whitespace_collapsed_stored_name(scripted, sent):
    """Regression, measured 2026-07-24: a launcher with a MULTI-LINE prompt, and Claude Code
    stores an agent's name with every run of whitespace
    collapsed to a single space. The launcher passes the raw multi-line prompt as --name,
    so an exact compare against the stored single-line name never matched — the watcher
    reported "never appeared" for a run that was in fact working, and released the
    caffeinate that was tied to its pid mid-run. The name is normalized on both sides now,
    so the multi-line launch name resolves to the collapsed stored name."""
    multiline = "Read the lens at /p/ratify.md.\n\n- Skill: product-prd.\n    example-product: /r/PRD.md"
    stored = "Read the lens at /p/ratify.md. - Skill: product-prd. example-product: /r/PRD.md"
    assert multiline != stored          # the exact-compare the old matcher did would miss
    scripted([agent("a1", "blocked", name=stored)])

    rc = watch_agent.main(
        ["--name", multiline, "--label", "ratify", "--cwd", CWD,
         "--notify", "/nonexistent", "--poll-seconds", "0"]
    )

    assert rc == 0
    assert "run ended" in sent[0]       # matched, watched to its terminal state, notified


def test_interactive_session_is_not_watched(scripted, sent):
    """The launcher only ever starts background agents; an interactive session
    that happens to match is not this run."""
    scripted([agent("a1", "done", kind="interactive")])

    rc = run_watcher("--appear-seconds", "0.01")

    assert rc == 1
    assert "no matching agent appeared" in sent[0]


# --- --list-ids (the launcher's pre-launch snapshot) -------------------------


def test_list_ids_prints_background_ids_under_the_cwd(scripted, capsys):
    scripted(
        [
            agent("a1", "done"),
            agent("a2", "running"),
            agent("elsewhere", "done", cwd="/other"),
            agent("interactive", "idle", kind="interactive"),
        ]
    )

    rc = watch_agent.main(["--list-ids", "--cwd", CWD])

    assert rc == 0
    assert capsys.readouterr().out.strip() == "a1,a2"


def test_list_ids_survives_an_unreadable_cli(monkeypatch, capsys):
    """A failed snapshot must not stop a launch — it only costs disambiguation."""
    monkeypatch.setattr(watch_agent, "list_agents", lambda: None)

    rc = watch_agent.main(["--list-ids", "--cwd", CWD])

    assert rc == 0
    assert capsys.readouterr().out.strip() == ""


def test_name_and_label_are_required_when_actually_watching():
    with pytest.raises(SystemExit):
        watch_agent.main(["--cwd", CWD])


# --- --multi-turn / --done-when-exists: declaring a run and the fact that ends it --
#
# A caller has two things to say: that its run ends its turn many times on purpose
# (--multi-turn), and what fact will say the run is actually over (--done-when-exists).
# --multi-turn without --done-when-exists is refused at parse time, because with idle no
# longer terminal the deadline would be the only ending left.


def _parse(*argv):
    return watch_agent.parse_args(
        ["--name", NAME, "--label", "example-product", "--cwd", CWD, *argv]
    )


def test_multi_turn_parses_to_true_and_defaults_to_false():
    assert _parse("--multi-turn", "--done-when-exists", "/some/path").multi_turn is True
    assert _parse().multi_turn is False


def test_done_when_exists_parses_to_the_path_and_defaults_to_none():
    assert _parse("--done-when-exists", "/some/path").done_when_exists == "/some/path"
    assert _parse().done_when_exists is None


def test_multi_turn_without_done_when_exists_is_refused(capsys):
    with pytest.raises(SystemExit) as excinfo:
        _parse("--multi-turn")

    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "--multi-turn" in err
    assert "--done-when-exists" in err


def test_multi_turn_with_done_when_exists_parses_cleanly():
    args = _parse("--multi-turn", "--done-when-exists", "/some/path")

    assert args.multi_turn is True
    assert args.done_when_exists == "/some/path"


def test_done_when_exists_without_multi_turn_is_legal_alone():
    args = _parse("--done-when-exists", "/some/path")

    assert args.multi_turn is False
    assert args.done_when_exists == "/some/path"


def test_list_ids_needs_neither_new_flag():
    args = watch_agent.parse_args(["--list-ids", "--cwd", CWD])

    assert args.multi_turn is False
    assert args.done_when_exists is None


def test_an_argv_with_neither_new_flag_is_unchanged():
    """The regression this task must not cause: a caller that names neither flag gets
    exactly the namespace it gets today."""
    args = _parse()

    assert args.multi_turn is False
    assert args.done_when_exists is None
    assert args.label == "example-product"
    assert args.name == NAME

    with pytest.raises(SystemExit):
        watch_agent.parse_args(["--cwd", CWD])


def test_help_mentions_both_new_flags(capsys):
    with pytest.raises(SystemExit):
        watch_agent.parse_args(["--help"])

    out = capsys.readouterr().out
    assert "--multi-turn" in out
    assert "--done-when-exists" in out


# --- --on-complete: an optional hook invoked beside the notifier ---------------------
#
# The chain's own event hook. This task only adds the flag to the parser — the six call
# sites and the outcome it is given are the tasks after it.


def test_on_complete_defaults_to_none():
    assert _parse().on_complete is None


def test_on_complete_parses_the_given_path():
    assert _parse("--on-complete", "/some/hook.sh").on_complete == "/some/hook.sh"


def test_list_ids_needs_no_on_complete():
    args = watch_agent.parse_args(["--list-ids", "--cwd", CWD])

    assert args.on_complete is None


def test_an_argv_with_no_on_complete_is_unchanged():
    """The regression this task must not cause: a caller that never names the flag gets
    exactly the namespace it gets today."""
    args = _parse()

    assert args.on_complete is None
    assert args.label == "example-product"
    assert args.name == NAME


def test_help_mentions_on_complete_and_that_it_runs_beside_the_notifier(capsys):
    with pytest.raises(SystemExit):
        watch_agent.parse_args(["--help"])

    out = capsys.readouterr().out
    assert "--on-complete" in out
    assert "beside" in out


def test_the_flags_own_help_says_beside_the_notifier_and_not_instead_of_it(capsys):
    """The claim is about the FLAG's line, not about `--help` anywhere.

    `--help` prints this module's docstring as its description, and that docstring says
    "BESIDE notify()" on its own — so a whole-output grep for the word passes even if the
    flag's own help said nothing at all. The last `--on-complete` in the output is the one
    in the options block; everything after it is that flag's own entry, because it is the
    last argument the parser defines.
    """
    with pytest.raises(SystemExit):
        watch_agent.parse_args(["--help"])

    out = capsys.readouterr().out
    entry = " ".join(out[out.rindex("--on-complete"):].split())

    assert "beside the notifier" in entry
    assert "instead of it" in entry


# --- the hook fires on every path where the watcher stops --------------------
#
# `--on-complete <script>` is called beside notify() on the same six paths that end this
# watcher. This task only wires the six call sites — the outcome it is given, and that the
# notifier still fires beside it, are the next task's.


def test_on_complete_absent_calls_the_hook_nowhere(scripted, sent, hooks):
    scripted([agent("a1", "blocked")])

    run_watcher()

    assert hooks == []


def test_a_normal_completion_calls_the_hook_once(scripted, sent, hooks):
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", "/some/hook.sh")

    assert len(hooks) == 1
    assert hooks[0][0] == "/some/hook.sh"


def test_a_blind_completion_calls_the_hook_once(scripted, sent, hooks):
    scripted([
        agent("a1", "done", name=AI_TITLE, started=1),
        agent("a2", "done", name="some other title", started=99),
    ])

    run_watcher("--appear-seconds", "0.01", "--on-complete", "/some/hook.sh")

    assert len(hooks) == 1


def test_an_appearance_error_calls_the_hook_once(scripted, sent, hooks):
    scripted([])

    run_watcher("--appear-seconds", "0.01", "--on-complete", "/some/hook.sh")

    assert len(hooks) == 1


def test_a_vanished_run_calls_the_hook_once(scripted, sent, hooks):
    scripted([agent("a1", "running")], [])

    run_watcher("--on-complete", "/some/hook.sh")

    assert len(hooks) == 1


def test_a_blind_timeout_calls_the_hook_once(scripted, sent, hooks):
    scripted([
        agent("a1", "running", name=AI_TITLE, started=1),
        agent("a2", "running", name="some other title", started=99),
    ])

    run_watcher(
        "--appear-seconds", "0.01", "--timeout-seconds", "0.05",
        "--on-complete", "/some/hook.sh",
    )

    assert len(hooks) == 1


def test_a_plain_timeout_calls_the_hook_once(scripted, sent, hooks):
    scripted([agent("a1", "running")])

    run_watcher("--timeout-seconds", "0", "--on-complete", "/some/hook.sh")

    assert len(hooks) == 1


# --- the outcome the hook is given, and the notifier beside it ----------------
#
# A caller routing on this needs to know WHICH of these four happened, not which of the
# six internal paths got there — so a completion is a completion whether the watcher
# named its run or watched blind, and a timeout is a timeout either way. On every path
# the notifier fires too, and it keeps firing first: the hook never reorders it.


@pytest.mark.parametrize(
    "build_scripted, extra_args, expect_outcome",
    [
        (lambda s: s([agent("a1", "blocked")]), (), "COMPLETED"),
        (
            lambda s: s([
                agent("a1", "done", name=AI_TITLE, started=1),
                agent("a2", "done", name="some other title", started=99),
            ]),
            ("--appear-seconds", "0.01"),
            "COMPLETED",
        ),
        (lambda s: s([]), ("--appear-seconds", "0.01"), "APPEAR_ERROR"),
        (lambda s: s([agent("a1", "running")], []), (), "VANISHED"),
        (
            lambda s: s([
                agent("a1", "running", name=AI_TITLE, started=1),
                agent("a2", "running", name="some other title", started=99),
            ]),
            ("--appear-seconds", "0.01", "--timeout-seconds", "0.05"),
            "TIMEOUT",
        ),
        (lambda s: s([agent("a1", "running")]), ("--timeout-seconds", "0"), "TIMEOUT"),
    ],
    ids=["normal-completion", "blind-completion", "appear-error", "vanished",
         "blind-timeout", "plain-timeout"],
)
def test_each_path_gives_the_hook_its_own_outcome_and_still_notifies(
    scripted, sent, hooks, build_scripted, extra_args, expect_outcome
):
    build_scripted(scripted)

    run_watcher("--on-complete", "/some/hook.sh", *extra_args)

    assert len(sent) == 1, "the notifier must still fire beside the hook"
    assert len(hooks) == 1
    assert hooks[0][1][0] == getattr(watch_agent.HookOutcome, expect_outcome)


# --- PRODUCED_NOTHING: the hook is told whether the run made a difference, not just how
# it ended ---------------------------------------------------------------------------
#
# `HookOutcome` gains a fifth value, read off `outcome.produced_nothing`
# (`reporters.py`, task 1) — this file never re-derives the fact itself from
# `ctx.head_before`/`head_after` or the report set; it reads the one field.


def test_the_hook_is_told_produced_nothing_when_the_outcome_says_so(
    scripted, sent, hooks, tmp_path, monkeypatch
):
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    scripted([agent("a1", "stopped")])

    run_watcher("--on-complete", "/some/hook.sh", "--reporter", "prd",
                "--artifact-path", str(tmp_path))

    assert hooks[0][1][0] == watch_agent.HookOutcome.PRODUCED_NOTHING
    assert len(sent) == 1


def test_the_hook_is_still_told_completed_when_the_run_committed(
    scripted, sent, hooks, tmp_path, monkeypatch
):
    heads = iter(["before-sha", "after-sha"])
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: next(heads))
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", "/some/hook.sh", "--reporter", "prd",
                "--artifact-path", str(tmp_path))

    assert hooks[0][1][0] == watch_agent.HookOutcome.COMPLETED


def test_a_raising_reporter_never_reports_produced_nothing(
    scripted, sent, hooks, tmp_path, monkeypatch
):
    """A reporter is best-effort, like the notify: if it blows up, the hook must still get
    COMPLETED, never PRODUCED_NOTHING — a failure to read is not evidence the run produced
    nothing, even with HEAD sitting still throughout."""
    def boom(_ctx):
        raise ValueError("reporter blew up")

    monkeypatch.setitem(watch_agent.reporters.REGISTRY, "boom", boom)
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", "/some/hook.sh", "--reporter", "boom",
                "--artifact-path", str(tmp_path))

    assert hooks[0][1][0] == watch_agent.HookOutcome.COMPLETED
    assert "run ended" in sent[0]


def test_the_notify_text_and_stop_call_are_unaffected_by_the_new_hook_value(
    scripted, sent, hooks, stops, tmp_path, monkeypatch
):
    """This task changes what the hook is told, nothing the owner sees or that the agent
    experiences."""
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", "/some/hook.sh", "--reporter", "prd",
                "--artifact-path", str(tmp_path))

    assert "committed nothing" in sent[0]
    assert stops == ["a1"]


def test_the_notify_text_and_stop_call_are_unchanged_when_the_run_did_write(
    scripted, sent, hooks, stops, tmp_path, monkeypatch
):
    """The other half of "unchanged in both cases". The produced-nothing case is pinned
    above; this pins the ending that still reports COMPLETED, so neither half of the claim
    rests on the other. The owner gets the reporter's own message and the agent gets the
    same stop it always got — only the hook's argument is this task's business."""
    heads = iter(["before-sha", "after-sha"])
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: next(heads))
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", "/some/hook.sh", "--reporter", "prd", "--product-path",
                product(tmp_path, status="Draft", open_issues=True, trail=(1,)))

    assert hooks[0][1][0] == watch_agent.HookOutcome.COMPLETED
    assert len(sent) == 1
    assert "committed nothing" not in sent[0]
    assert stops == ["a1"]


def test_a_blind_completion_can_also_report_produced_nothing(
    scripted, sent, hooks, tmp_path, monkeypatch
):
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    scripted([
        agent("a1", "done", name=AI_TITLE, started=1),
        agent("a2", "done", name="some other title", started=99),
    ])

    run_watcher("--appear-seconds", "0.01", "--on-complete", "/some/hook.sh",
                "--reporter", "prd", "--artifact-path", str(tmp_path))

    assert hooks[0][1][0] == watch_agent.HookOutcome.PRODUCED_NOTHING


def test_the_six_outcomes_are_genuinely_distinct_values():
    values = {o.value for o in watch_agent.HookOutcome}

    assert len(values) == 6


def test_the_notifier_fires_before_the_hook(scripted, monkeypatch):
    order = []
    monkeypatch.setattr(watch_agent, "notify", lambda _n, _m: order.append("notify"))
    monkeypatch.setattr(
        watch_agent, "run_on_complete_hook", lambda _h, _o: order.append("hook")
    )
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", "/some/hook.sh")

    assert order == ["notify", "hook"]


def test_a_real_hook_script_receives_the_outcome_as_its_one_argument(
    scripted, sent, tmp_path
):
    """End to end, past the `hooks` mock: the real subprocess call the watcher makes
    carries the outcome where a caller script can read it as $1."""
    record = tmp_path / "on_complete_calls.log"
    hook = hook_script(tmp_path, record_path=record)
    scripted([agent("a1", "blocked")])

    run_watcher("--on-complete", hook)

    assert record.read_text().strip() == "completed"


# --- a bad hook costs nothing --------------------------------------------------------
#
# notify() and stop_agent() are both best-effort because "a leaked process must never
# cost somebody their notification" — run_on_complete_hook is one more outbound act and
# takes the same rule: missing, non-executable, a non-zero exit, or a hang must each
# leave the notification sent and the watcher's exit code unchanged, and nothing here
# may raise out of the watcher.


def test_a_missing_hook_is_logged_and_does_not_raise(tmp_path, capsys):
    ok = watch_agent.run_on_complete_hook(
        str(tmp_path / "nope" / "missing.sh"), watch_agent.HookOutcome.COMPLETED
    )

    assert ok is False
    assert "did not run" in capsys.readouterr().err


def test_a_non_executable_hook_is_logged_and_does_not_raise(tmp_path, capsys):
    hook = tmp_path / "not_executable.sh"
    hook.write_text("#!/usr/bin/env bash\nexit 0\n")  # deliberately no chmod +x

    ok = watch_agent.run_on_complete_hook(str(hook), watch_agent.HookOutcome.COMPLETED)

    assert ok is False
    assert "did not run" in capsys.readouterr().err


def test_a_hook_that_exits_non_zero_is_logged_and_does_not_raise(tmp_path, capsys):
    hook = hook_script(tmp_path, exit_code=1, stderr_text="hook blew up")

    ok = watch_agent.run_on_complete_hook(hook, watch_agent.HookOutcome.COMPLETED)

    assert ok is False
    err = capsys.readouterr().err
    assert "exited 1" in err
    assert "hook blew up" in err


def test_a_successful_hook_is_logged(tmp_path, capsys):
    hook = hook_script(tmp_path, exit_code=0)

    ok = watch_agent.run_on_complete_hook(hook, watch_agent.HookOutcome.COMPLETED)

    assert ok is True
    assert "on_complete: ran." in capsys.readouterr().err


def test_a_hook_that_hangs_is_bounded_by_a_timeout_and_does_not_raise(monkeypatch, capsys):
    def _hangs(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd=["hook"], timeout=60)

    monkeypatch.setattr(watch_agent.subprocess, "run", _hangs)

    ok = watch_agent.run_on_complete_hook("/some/hook.sh", watch_agent.HookOutcome.COMPLETED)

    assert ok is False
    assert "did not run" in capsys.readouterr().err


def test_a_broken_hook_leaves_the_notification_sent_and_the_exit_code_unchanged(
    scripted, sent, tmp_path
):
    scripted([agent("a1", "blocked")])

    rc = run_watcher("--on-complete", str(tmp_path / "nope.sh"))

    assert rc == 0
    assert len(sent) == 1


def test_the_hook_is_bounded_by_a_timeout(monkeypatch):
    """"Bounded by a timeout" is a claim about the CALL, and only a test that reads the
    call can hold it. Mocking `subprocess.run` into raising `TimeoutExpired` proves the
    catch and nothing else: delete the bound and a hook that hangs holds the watcher open
    forever while that test stays green.
    """
    seen = {}

    def _capture(cmd, **kwargs):
        seen.update(kwargs)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(watch_agent.subprocess, "run", _capture)

    watch_agent.run_on_complete_hook("/some/hook.sh", watch_agent.HookOutcome.COMPLETED)

    assert seen.get("timeout"), "the hook is spawned with no timeout — a hang is unbounded"
    assert seen["timeout"] > 0


def _hook_that_is_not_executable(tmp_path):
    hook = tmp_path / "not_executable.sh"
    hook.write_text("#!/usr/bin/env bash\nexit 0\n")  # deliberately no chmod +x
    return str(hook)


@pytest.mark.parametrize(
    "make_hook",
    [
        lambda tmp_path: str(tmp_path / "nope" / "missing.sh"),
        _hook_that_is_not_executable,
        lambda tmp_path: hook_script(tmp_path, exit_code=1, stderr_text="hook blew up"),
    ],
    ids=["missing", "non-executable", "exits-non-zero"],
)
def test_every_kind_of_bad_hook_leaves_the_notification_sent_and_the_exit_code_unchanged(
    scripted, sent, tmp_path, make_hook
):
    """The whole list the rule names, not just the first of them: missing, non-executable
    and a non-zero exit each have to cost nothing, and "costs nothing" is two facts — the
    message went out, and this process still says what it would have said."""
    scripted([agent("a1", "blocked")])

    rc = run_watcher("--on-complete", make_hook(tmp_path))

    assert rc == 0
    assert len(sent) == 1


def test_a_bad_hook_leaves_a_FAILING_run_exiting_one(scripted, sent, tmp_path):
    """"Unchanged" is not "zero". A path that ends 1 has to still end 1 — a hook whose
    failure quietly turned a timeout into a success would satisfy every exit-code check
    written only against the completion path."""
    scripted([agent("a1", "running")])

    rc = run_watcher("--timeout-seconds", "0", "--on-complete", str(tmp_path / "nope.sh"))

    assert rc == 1
    assert len(sent) == 1


def test_a_hanging_hook_leaves_the_notification_sent_and_the_exit_code_unchanged(
    scripted, sent, monkeypatch
):
    """The fourth kind, at the watcher's level rather than the function's. The hang is
    injected only for the hook's own spawn — everything else this run shells out to is
    left alone, so what is under test is the ending and not the mock."""
    real_run = subprocess.run

    def _hangs_only_for_the_hook(cmd, **kwargs):
        if cmd and cmd[0] == "/some/hook.sh":
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout", 60))
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(watch_agent.subprocess, "run", _hangs_only_for_the_hook)
    scripted([agent("a1", "blocked")])

    rc = run_watcher("--on-complete", "/some/hook.sh")

    assert rc == 0
    assert len(sent) == 1


def test_the_module_docstring_describes_the_hook_and_its_outcome_contract():
    """The interface a caller reads before it writes a hook: the flag, and every outcome
    the hook can be handed. An outcome the file never names is one a caller has to read
    the source to discover."""
    doc = watch_agent.__doc__

    assert "--on-complete" in doc
    for outcome in watch_agent.HookOutcome:
        assert outcome.name in doc, f"the docstring never names the {outcome.name} outcome"


# --- completion_marker_seen: has the run's own marker appeared since the watch began? --
#
# Distinct from "is there a file at this path": a marker left by a PREVIOUS run would end
# the watch on its first poll and report a run that had barely started. `present_before` is
# a single reading taken once, before the watch — the same shape `git_head`'s `head_before`
# takes for HEAD. Best-effort like `git_head` and `refusal_of`: an unreadable path is
# `False`, never a raise.


def test_marker_absent_at_start_then_created_is_seen(tmp_path):
    marker = tmp_path / "done"
    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is False

    marker.write_text("done")

    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is True


def test_marker_present_at_start_is_never_seen_however_many_times_asked(tmp_path):
    marker = tmp_path / "done"
    marker.write_text("done")

    for _ in range(3):
        assert watch_agent.completion_marker_seen(str(marker), present_before=True) is False


def test_marker_absent_at_start_appearing_then_disappearing_then_reappearing_is_seen_each_time(
    tmp_path
):
    """The check is never latched — each call re-reads the disk fresh, so an appearance
    followed by a disappearance and a second appearance is seen both times, exactly as the
    first appearance alone would be. `present_before` is the single fixed reading `main`
    takes once, before the watch; it is not re-derived from a previous call's answer."""
    marker = tmp_path / "done"
    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is False

    marker.write_text("done")
    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is True

    marker.unlink()
    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is False

    marker.write_text("done again")
    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is True


def test_no_path_is_never_seen_whatever_is_on_disk(tmp_path):
    marker = tmp_path / "done"
    marker.write_text("done")

    assert watch_agent.completion_marker_seen(None, present_before=False) is False
    assert watch_agent.completion_marker_seen("", present_before=False) is False


def test_a_directory_marker_is_seen_on_the_same_terms_as_a_file(tmp_path):
    marker = tmp_path / "done"
    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is False

    marker.mkdir()

    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is True


def test_a_path_whose_parent_does_not_exist_is_not_seen(tmp_path):
    marker = tmp_path / "nope" / "done"

    assert watch_agent.completion_marker_seen(str(marker), present_before=False) is False


def test_an_unreadable_existence_check_costs_the_seen_read_not_a_raise(monkeypatch):
    def boom(_path):
        raise OSError("permission denied")

    monkeypatch.setattr(watch_agent.os.path, "exists", boom)

    assert watch_agent.completion_marker_seen("/some/path", present_before=False) is False


# --- the refusal record: the one death the state cannot express ---------------
#
# `blocked` reads as "finished its turn and is idle" and a refused run reaches it, so the
# state is not merely a poor witness here — it is a flattering one. The run's own transcript
# carries the refusal, machine-readable, and the agent list carries the sessionId that finds
# it. This reads that and nothing else: it says what the record says, never that the record
# ended the run.


def test_session_id_is_read_from_the_agent_list(scripted):
    agents = [agent("a1", "blocked", session_id=REAL_SESSION_ID)]
    assert watch_agent.session_id_of(agents, "a1") == REAL_SESSION_ID


def test_session_id_is_none_when_the_list_entry_carries_none():
    assert watch_agent.session_id_of([agent("a1", "blocked")], "a1") is None
    assert watch_agent.session_id_of([], "a1") is None
    assert watch_agent.session_id_of(None, "a1") is None


def test_the_real_refusal_record_is_found_and_read(tmp_path):
    transcript(tmp_path, REAL_SESSION_ID, {"type": "user"}, REFUSAL_RECORD)

    found = watch_agent.refusal_of(REAL_SESSION_ID, projects_dir=str(tmp_path))

    assert found is not None
    assert found["category"] == "reasoning_extraction"
    assert found["model"] == "claude-fable-5"


def test_a_transcript_without_a_refusal_reads_as_none(tmp_path):
    transcript(tmp_path, REAL_SESSION_ID,
               {"type": "system", "subtype": "turn_duration"}, {"type": "assistant"})

    assert watch_agent.refusal_of(REAL_SESSION_ID, projects_dir=str(tmp_path)) is None


def test_another_runs_refusal_is_not_read_for_this_one(tmp_path):
    """The transcript is resolved by sessionId. A refusal sitting in some other session's
    file is that run's, and reporting it here would be the same borrowed-result failure in
    a new place."""
    transcript(tmp_path, "99999999-0000-0000-0000-000000000000", REFUSAL_RECORD)

    assert watch_agent.refusal_of(REAL_SESSION_ID, projects_dir=str(tmp_path)) is None


def test_a_missing_transcript_reads_as_none_rather_than_raising(tmp_path):
    assert watch_agent.refusal_of(REAL_SESSION_ID, projects_dir=str(tmp_path)) is None
    assert watch_agent.refusal_of(REAL_SESSION_ID, projects_dir="/nonexistent/nope") is None
    assert watch_agent.refusal_of(None, projects_dir=str(tmp_path)) is None


def test_a_malformed_transcript_costs_the_refusal_not_the_message(tmp_path):
    """Best-effort like git_head and list_agents: the transcript is the harness's own
    format and a shape we cannot parse must not reach the notify path as an exception."""
    d = tmp_path / "-repo"
    d.mkdir(parents=True)
    (d / f"{REAL_SESSION_ID}.jsonl").write_text("{not json at all\n[]\n")

    assert watch_agent.refusal_of(REAL_SESSION_ID, projects_dir=str(tmp_path)) is None


def test_the_refusal_note_names_the_category_and_the_model():
    note = watch_agent.refusal_note(
        {"category": "reasoning_extraction", "model": "claude-fable-5"})

    assert "refus" in note
    assert "reasoning_extraction" in note
    assert "claude-fable-5" in note


def test_a_refused_run_is_named_before_the_state_note(scripted, sent, tmp_path, monkeypatch):
    """The failure this came from: the owner read "finished its turn and is idle" for a run
    that was refused. The refusal is the better witness, so it lands ABOVE the state — a
    correction underneath a flattering line is the shape that failed."""
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    monkeypatch.setattr(watch_agent, "PROJECTS_DIR", str(tmp_path))
    transcript(tmp_path, REAL_SESSION_ID, REFUSAL_RECORD)
    scripted([agent("a1", "blocked", session_id=REAL_SESSION_ID)])

    run_watcher("--reporter", "prd", "--product-path",
                product(tmp_path, status="Draft", open_issues=True, trail=(1,)))

    message = sent[0]
    assert "reasoning_extraction" in message
    assert message.index("reasoning_extraction") < message.index("state: blocked")
    assert "committed nothing" in message


def test_a_run_with_no_refusal_record_reads_exactly_as_before(scripted, sent, tmp_path,
                                                              monkeypatch):
    monkeypatch.setattr(watch_agent, "PROJECTS_DIR", str(tmp_path))
    scripted([agent("a1", "blocked", session_id=REAL_SESSION_ID)])

    run_watcher("--reporter", "prd", "--product-path", product(tmp_path, status="Settled"))

    assert "refus" not in sent[0]
    assert "settled" in sent[0]


# --- the turn ended, the process did not: `status: idle` ----------------------
#
# Measured 2026-08-21. Claude Code began reporting a `status` key the shape this file was
# written against never carried, and a --bg run whose TURN has ended while its PROCESS is
# still alive reports `status: idle` and keeps `state: working`. `working` is in no
# terminal set, so a state-only watch polls on to its six-hour deadline and the person is
# told nothing — the silent failure, which is worse than a wrong message because nothing
# ever arrives to be doubted.
#
# So `status: idle` is a terminal condition too, and it is DEBOUNCED where the state is
# not: a status could in principle read idle between two tool calls, and a false-early
# notification reports on a run still in flight and then stops it. Two consecutive polls.
# State-based termination stays immediate, exactly as it was.


# The real record, copied from `claude agents --json --all` at 11:26 local on 2026-08-21.
# This run's final report was written at 11:04:52 and its watcher (pid 55274) was still
# polling 21 minutes later, having sent nothing.
IDLE_BUT_ALIVE_RECORD = {
    "pid": 55274,
    "id": "ba5c8b8d",
    "cwd": "/home/user/projects/kensai/example-satellite",
    "kind": "background",
    "startedAt": 1787302611593,
    "sessionId": "ba5c8b8d-f42b-4545-90bf-380e83fd1485",
    "name": "invoke experience-visual kensaiapp-open…",
    "status": "idle",
    "state": "working",
}


def test_the_real_idle_but_alive_record_is_read_for_both_keys():
    """The premise, pinned against the record itself rather than a paraphrase of it: the
    state says `working` and is in no terminal set, so `status` is the only key on this
    entry that says the turn is over."""
    agents = [IDLE_BUT_ALIVE_RECORD]

    assert watch_agent.state_of(agents, "ba5c8b8d") == "working"
    assert watch_agent.status_of(agents, "ba5c8b8d") == "idle"
    assert "working" not in watch_agent.TERMINAL_STATES


def test_status_is_none_when_the_list_entry_carries_none():
    """The older shape — a finished run whose process exited — carries no `status` at all,
    and reading one that is not there is an ordinary answer, not an error."""
    assert watch_agent.status_of([agent("a1", "blocked")], "a1") is None
    assert watch_agent.status_of([], "a1") is None
    assert watch_agent.status_of(None, "a1") is None


def test_two_consecutive_idle_polls_end_the_watch(scripted, sent, stops):
    """The bug, end to end: this run would otherwise be watched to its deadline."""
    scripted(
        [agent("a1", "working", status="idle")],   # the appearance read
        [agent("a1", "working", status="idle")],   # poll 1
        [agent("a1", "working", status="idle")],   # poll 2 — two in a row, the watch ends
        # Never reached once the idle condition holds. It is here so a regression fails
        # fast rather than polling on to the six-hour deadline the way the bug did.
        [],
    )

    rc = run_watcher()

    assert rc == 0
    assert len(sent) == 1
    assert "run ended" in sent[0]
    assert stops == ["a1"]


def test_a_single_idle_poll_does_not_end_the_watch(scripted, sent):
    """The debounce. One idle poll is not enough — the watch goes on, and this run ends on
    its state two polls later, reported as that state and not as the idle case."""
    scripted(
        [agent("a1", "working", status="idle")],   # the appearance read
        [agent("a1", "working", status="idle")],   # poll 1 — one idle, not yet terminal
        [agent("a1", "blocked")],                  # poll 2 — ends on the state instead
    )

    rc = run_watcher()

    assert rc == 0
    assert "state: blocked" in sent[0]
    assert "status: idle" not in sent[0]


def test_a_broken_run_of_idle_polls_starts_the_count_again(scripted, sent):
    """Consecutive means consecutive. Two idle polls with a busy one between them are not
    a terminal condition — had the count merely accumulated, poll 3 here would have ended
    the watch and the message would carry the idle note instead of `stopped`."""
    scripted(
        [agent("a1", "working", status="idle")],   # the appearance read
        [agent("a1", "working", status="idle")],   # poll 1 — one idle
        [agent("a1", "working", status="busy")],   # poll 2 — the run is moving again
        [agent("a1", "working", status="idle")],   # poll 3 — one idle again, never a second
        [agent("a1", "stopped")],                  # poll 4 — ends on the state
    )

    rc = run_watcher()

    assert rc == 0
    assert "was stopped" in sent[0]
    assert "status: idle" not in sent[0]


def test_a_record_with_no_status_key_is_watched_exactly_as_before(scripted, sent, stops):
    """What protects the tests written before `status` existed. A record carrying no
    `status` must never accumulate toward the idle condition, however many times it is
    polled — three polls here, then a terminal state read the way it always was."""
    scripted(
        [agent("a1", "working")],                  # the appearance read
        [agent("a1", "working")],
        [agent("a1", "working")],
        [agent("a1", "blocked")],
    )

    rc = run_watcher()

    assert rc == 0
    assert "state: blocked" in sent[0]
    assert "status" not in sent[0]
    assert stops == ["a1"]


def test_a_terminal_state_is_still_immediate_when_a_status_rides_along(scripted, sent):
    """A real record from the same listing — agent 410201fc carried `status: idle` AND
    `state: blocked` together. The state is terminal, so the watch ends on the FIRST poll
    and the message reads as that state; the debounce governs only the new condition."""
    scripted([agent("a1", "blocked", status="idle")])

    rc = run_watcher()

    assert rc == 0
    assert "state: blocked" in sent[0]


def test_the_idle_note_reads_as_a_finished_turn_not_a_working_run(scripted, sent):
    """`(run a1 — state: working)` is what the untouched fallback would print for this
    case, and it reads as a run still going. The reading `blocked` already gets is the
    right one — the turn is over — and the raw keys stay on the line behind it."""
    scripted(
        [agent("a1", "working", status="idle")],
        [agent("a1", "working", status="idle")],
        [agent("a1", "working", status="idle")],
        # Never reached once the idle condition holds. It is here so a regression fails
        # fast rather than polling on to the six-hour deadline the way the bug did.
        [],
    )

    run_watcher()

    assert "finished its turn and is idle" in sent[0]
    assert "status: idle" in sent[0]
    assert "(run a1 — state: working)" not in sent[0]


def test_a_refusal_is_still_named_above_an_idle_note(scripted, sent, tmp_path, monkeypatch):
    """The refusal read hangs off the terminal branch, so it must reach the new condition
    too — a run refused mid-turn and left idle is exactly the death the state cannot
    express, and the correction still lands ABOVE the note it corrects."""
    monkeypatch.setattr(watch_agent, "PROJECTS_DIR", str(tmp_path))
    transcript(tmp_path, REAL_SESSION_ID, REFUSAL_RECORD)
    idle = agent("a1", "working", status="idle", session_id=REAL_SESSION_ID)
    scripted(
        [idle],
        [idle],
        [idle],
        # Never reached once the idle condition holds. It is here so a regression fails
        # fast rather than polling on to the six-hour deadline the way the bug did.
        [],
    )

    run_watcher()

    message = sent[0]
    assert message.index("reasoning_extraction") < message.index("status: idle")


# --- the terminal test in the watch loop: --multi-turn holds through idle -------------
#
# The task the whole plan exists for: under --multi-turn, `status: idle` stops being an
# ending, and the marker (--done-when-exists) becomes one — for any caller that named one,
# multi-turn or not. Everything else about the loop — the states, the vanish check, the
# timeout tail, the stop — is unchanged.


def test_the_bug_gone_idle_forever_under_multi_turn_runs_to_the_deadline(
    scripted, sent, stops, tmp_path
):
    """The two real SDD runs, reproduced: idle throughout, the marker never appears, and
    the watch must not end on the idle debounce — it runs out the clock instead."""
    marker = tmp_path / "done"
    scripted([agent("a1", "working", status="idle")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "0.05"
    )

    assert rc == 1
    assert "still going" in sent[0]
    assert stops == []


def test_ten_consecutive_idle_polls_under_multi_turn_end_nothing(scripted, sent, stops):
    """Ten straight idle reads — five times the debounce that used to end the watch — and
    still nothing happens under --multi-turn.

    Its terminator was `blocked` until 2026-08-26, on the reading that "the run ends only when
    its own state does". Both halves of that sentence were true and the state chosen was not:
    `blocked` is what a runner reports between turns. `stopped` is the state that ends it."""
    idle = agent("a1", "working", status="idle")

    scripted(*([[idle]] * 10), [agent("a1", "stopped")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", "/nonexistent-marker",
        "--timeout-seconds", "5",
    )

    assert rc == 0
    assert "state: stopped" in sent[0]
    assert stops == []


def test_multi_turn_ends_on_its_marker_appearing_mid_watch(monkeypatch, sent, stops, tmp_path):
    marker = tmp_path / "done"
    calls = {"n": 0}
    idle = agent("a1", "working", status="idle")

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 3:               # the marker appears before the third poll
            marker.write_text("done")
        return [idle]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    rc = run_watcher("--multi-turn", "--done-when-exists", str(marker))

    assert rc == 0
    assert len(sent) == 1
    assert stops == ["a1"]


def test_a_marker_already_on_disk_at_start_never_ends_the_watch_on_its_own(
    scripted, sent, stops, tmp_path
):
    """A stale marker from a previous run must not end this one on its first poll —
    `present_before` is what makes it inert."""
    marker = tmp_path / "done"
    marker.write_text("stale")
    scripted([agent("a1", "working", status="idle")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "0.05"
    )

    assert rc == 1
    assert "still going" in sent[0]
    assert stops == []


def test_done_when_exists_without_multi_turn_also_ends_the_watch(
    monkeypatch, sent, stops, tmp_path
):
    """The marker is an additional terminal condition, not a multi-turn-only one."""
    marker = tmp_path / "done"
    calls = {"n": 0}

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 2:
            marker.write_text("done")
        return [agent("a1", "running")]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    # A bounded timeout so a run of this test against the pre-fix loop (which has no other
    # terminal signal for a plain "running" state with no status) fails fast rather than
    # busy-spinning to the six-hour default.
    rc = run_watcher("--done-when-exists", str(marker), "--timeout-seconds", "5")

    assert rc == 0
    assert stops == ["a1"]


def test_without_multi_turn_the_idle_debounce_still_ends_it_when_it_gets_there_first(
    scripted, sent, stops, tmp_path
):
    marker = tmp_path / "done"       # never created — the debounce must win, not the marker
    idle = agent("a1", "working", status="idle")
    scripted([idle], [idle])

    rc = run_watcher("--done-when-exists", str(marker))

    assert rc == 0
    assert "status: idle" in sent[0]
    assert stops == ["a1"]


def test_marker_appearing_while_list_agents_is_unreadable_still_ends_the_watch(
    monkeypatch, sent, stops, tmp_path
):
    """An unreadable `claude` CLI is a reason the watcher cannot see the agent, not a reason
    to miss the run's own statement that it is over."""
    marker = tmp_path / "done"
    calls = {"n": 0}

    def _list_agents():
        calls["n"] += 1
        if calls["n"] == 1:
            return [agent("a1", "running")]   # await_appearance resolves the id
        marker.write_text("done")
        return None                           # every poll after: unreadable CLI

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    # Bounded for the same reason as the test above: the pre-fix loop never reads the
    # marker at all, so nothing but the six-hour default would end this watch.
    rc = run_watcher("--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "5")

    assert rc == 0
    assert len(sent) == 1
    assert stops == ["a1"]


def test_a_marker_ending_still_runs_the_reporter_and_the_refusal_record(
    monkeypatch, sent, stops, tmp_path
):
    """The marker is a new way to reach the terminal branch, not a shortcut around it: the
    reporter still composes the body and the refusal record still lands above the state
    note, exactly as a state-triggered ending does."""
    monkeypatch.setattr(watch_agent, "PROJECTS_DIR", str(tmp_path))
    monkeypatch.setattr(watch_agent, "git_head", lambda _p: "same-sha")
    transcript(tmp_path, REAL_SESSION_ID, REFUSAL_RECORD)
    marker = tmp_path / "done"
    calls = {"n": 0}

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 2:
            marker.write_text("done")
        return [agent("a1", "working", status="idle", session_id=REAL_SESSION_ID)]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker),
        "--reporter", "prd", "--product-path",
        product(tmp_path, status="Draft", open_issues=True, trail=(1,)),
    )

    assert rc == 0
    message = sent[0]
    assert "reasoning_extraction" in message
    assert "committed nothing" in message
    assert stops == ["a1"]


def test_multi_turn_with_a_gone_state_ends_immediately_on_that_state(scripted, sent, stops):
    """Renamed and re-pointed 2026-08-26. It read `blocked` and asserted the watch ended on it,
    which was the plan's stated scope — "the states ... unchanged" — and is now known wrong: a
    live multi-turn runner reports `blocked` between turns. `stopped` is the state that still
    means gone, so it is what this test was really about."""
    scripted([agent("a1", "working")], [agent("a1", "stopped")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", "/nonexistent-marker",
        "--timeout-seconds", "5",
    )

    assert rc == 0
    assert "state: stopped" in sent[0]


def test_multi_turn_with_a_stopped_state_is_not_stopped_again(scripted, sent, stops):
    scripted([agent("a1", "stopped")])

    run_watcher("--multi-turn", "--done-when-exists", "/nonexistent-marker")

    assert stops == []


def test_multi_turn_agent_vanishing_is_still_reported(scripted, sent, stops):
    scripted([agent("a1", "running")], [])

    rc = run_watcher("--multi-turn", "--done-when-exists", "/nonexistent-marker")

    assert rc == 1
    assert "vanished" in sent[0]
    assert stops == []


def test_multi_turn_with_an_unreadable_cli_before_appearance_is_unchanged(monkeypatch, sent):
    monkeypatch.setattr(watch_agent, "list_agents", lambda: None)

    rc = watch_agent.main(
        ["--name", NAME, "--label", "example-product", "--cwd", CWD, "--notify", "/nonexistent",
         "--poll-seconds", "0", "--appear-seconds", "0.01",
         "--multi-turn", "--done-when-exists", "/nonexistent-marker"]
    )

    assert rc == 1
    assert "unreadable" in sent[0]


def test_multi_turn_blind_watch_is_unaffected(scripted, sent, stops):
    scripted([
        agent("a1", "done", name=AI_TITLE, started=1),
        agent("a2", "done", name="some other title", started=99),
    ])

    rc = run_watcher(
        "--appear-seconds", "0.01", "--multi-turn", "--done-when-exists", "/nonexistent-marker"
    )

    assert rc == 0
    assert "could not identify" in sent[0].lower()
    assert stops == []


# --- the two messages a multi-turn watch can produce ---------------------------------
#
# A run sitting at `state: working` with a `status` prints "(run a1 — state: working)" by
# the untouched fallback, which reads as still going — the exact defect the idle branch was
# added to fix, arriving again through the marker's door. `state_note` gains a marker
# branch, ordered after the three states (they win when both a state and a marker apply)
# and before the idle branch (unreachable for a multi-turn run anyway).


def test_state_note_with_a_marker_and_a_working_state_does_not_read_as_still_going():
    note = watch_agent.state_note("working", "a1", status="idle", marker_path="/some/done")

    assert "/some/done" in note
    assert "(run a1 — state: working)" not in note


@pytest.mark.parametrize("state", ["blocked", "stopped", "done"])
def test_state_note_with_a_marker_and_a_terminal_state_is_the_states_note(state):
    with_marker = watch_agent.state_note(state, "a1", marker_path="/some/done")
    without_marker = watch_agent.state_note(state, "a1")

    assert with_marker == without_marker


def test_state_note_with_a_marker_and_idle_status_is_the_marker_note_not_the_idle_note():
    note = watch_agent.state_note("working", "a1", status="idle", marker_path="/some/done")

    assert "/some/done" in note
    assert "finished its turn and is idle —" not in note   # the idle branch's own phrase


def test_state_note_with_no_marker_path_is_byte_identical_to_before():
    for state in ("blocked", "stopped", "done", "working", "running"):
        for status in (None, "idle", "busy"):
            assert (watch_agent.state_note(state, "a1", status=status)
                    == watch_agent.state_note(state, "a1", status=status, marker_path=None))


def test_multi_turn_watch_ending_on_its_marker_names_the_path_in_one_message(
    monkeypatch, sent, stops, tmp_path
):
    marker = tmp_path / "done"
    calls = {"n": 0}
    idle = agent("a1", "working", status="idle")

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 2:
            marker.write_text("done")
        return [idle]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    rc = run_watcher("--multi-turn", "--done-when-exists", str(marker))

    assert rc == 0
    assert len(sent) == 1
    assert str(marker) in sent[0]


def test_a_refusal_is_still_named_above_a_marker_note(monkeypatch, sent, tmp_path):
    """The refusal read hangs off the terminal branch, so it reaches the marker ending too —
    the correction still lands ABOVE the note it corrects."""
    monkeypatch.setattr(watch_agent, "PROJECTS_DIR", str(tmp_path))
    transcript(tmp_path, REAL_SESSION_ID, REFUSAL_RECORD)
    marker = tmp_path / "done"
    calls = {"n": 0}
    idle = agent("a1", "working", status="idle", session_id=REAL_SESSION_ID)

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 2:
            marker.write_text("done")
        return [idle]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    run_watcher("--multi-turn", "--done-when-exists", str(marker))

    message = sent[0]
    assert message.index("reasoning_extraction") < message.index(str(marker))


def test_the_timeout_under_done_when_exists_names_the_path_and_says_it_never_appeared(
    scripted, sent, tmp_path
):
    marker = tmp_path / "done"
    scripted([agent("a1", "working", status="idle")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "0.05"
    )

    assert rc == 1
    assert "still going" in sent[0]
    assert str(marker) in sent[0]
    assert "never appeared" in sent[0]


def test_the_timeout_with_no_done_when_exists_is_byte_identical_to_before(scripted, sent):
    scripted([agent("a1", "running")])

    run_watcher("--timeout-seconds", "0")

    assert sent[0] == "⏱️ example-product: run a1 still going after 0h — no longer watching."


# --- code-integrity: plan behaviours with no test of their own -----------------------
#
# Derived from the ad-hoc plan
# `system/projects/tools/journey/nemawashi/2026-08-26_the-watcher-reads-a-run-between-turns-as-finished.md`
# § Plan, never from the implementation. Each pins a bullet from a task's
# `#### Behaviours to verify` that the implementation's own suite left unasserted.


def test_list_ids_bypasses_the_multi_turn_requirement_too():
    """Task 1: "`--list-ids` still needs neither, and still bypasses every other
    requirement", and the new rule is specified "in the same shape as the existing
    required-argument refusal a few lines above it" — which is itself gated on
    `--list-ids`. `--list-ids` prints and returns before any watch begins, so no ending
    can be lost by letting it through.
    """
    args = watch_agent.parse_args(["--list-ids", "--cwd", CWD, "--multi-turn"])

    assert args.multi_turn is True
    assert args.done_when_exists is None


def test_a_marker_ending_still_emits_the_reporters_footnote(monkeypatch, sent, stops, tmp_path):
    """Task 3: "The marker's terminal ending still calls the reporter, still reads the
    refusal record, and still emits the reporter's footnote — the whole terminal block
    runs, not a shortcut out of the loop." No shipped reporter sets a footnote, so the
    only way to pin the third of those three is a reporter that does.
    """
    marker = tmp_path / "done"
    calls = {"n": 0}

    def _reporter(_ctx):
        return watch_agent.reporters.Outcome("body line", footnote="the trailing caveat")

    monkeypatch.setattr(watch_agent.reporters, "get_reporter", lambda _n: _reporter)

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 2:
            marker.write_text("done")
        return [agent("a1", "working", status="idle")]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    rc = run_watcher("--multi-turn", "--done-when-exists", str(marker))

    assert rc == 0
    message = sent[0]
    assert "the trailing caveat" in message
    # The footnote lands after the state note, which is where the marker is named.
    assert message.index(str(marker)) < message.index("the trailing caveat")
    assert stops == ["a1"]


def test_multi_turn_with_a_stopped_state_still_ends_the_watch(scripted, sent, stops):
    """Task 3: "`--multi-turn` and a record reaching `stopped` → ends, and `stop_agent` is
    not called". The suite pins the second half; this pins that it ends at all, and with
    one message.
    """
    scripted([agent("a1", "stopped")])

    rc = run_watcher("--multi-turn", "--done-when-exists", "/nonexistent-marker")

    assert rc == 0
    assert len(sent) == 1
    assert "was stopped" in sent[0]
    assert stops == []


# --- a turn boundary is not an ending, and neither is the state that reports one ------------
#
# The section above states the plan's own scope: "Everything else about the loop — the states,
# the vanish check, the timeout tail, the stop — is unchanged." That was a decision, not an
# oversight, and it is the wrong one: `blocked` and `done` both mean a TURN ended, which for a
# multi-turn run happens once per turn it hands out.
#
# Measured 2026-08-26 on a live run: its runner reported `blocked` across six samples
# eight seconds apart while its seats worked and SDD.md changed, then finished two more rounds
# and committed. That run's seats went `done` then `working` again between rounds. `stopped` is
# the one that means gone — another product's runner still reports it after `claude stop`.


def test_multi_turn_is_not_ended_by_blocked(scripted, sent, stops, tmp_path):
    """The defect: one poll reading `blocked`, no debounce, and a live run is stopped
    mid-conversation. Under --multi-turn it must run out the clock instead."""
    marker = tmp_path / "done"
    scripted([agent("a1", "blocked", status="busy")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "0.05"
    )

    assert rc == 1, "`blocked` ended a multi-turn watch"


def test_multi_turn_is_not_ended_by_done(scripted, sent, stops, tmp_path):
    """`done` is what a --bg session reports when its turn ends; the next message revives it."""
    marker = tmp_path / "done"
    scripted([agent("a1", "done")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "0.05"
    )

    assert rc == 1, "`done` ended a multi-turn watch"


def test_multi_turn_still_ends_on_the_marker_while_blocked(monkeypatch, sent, stops, tmp_path):
    """Narrowing the states must not cost the ending that replaces them: a run sitting at
    `blocked` still ends the moment its own marker appears.

    The marker must appear DURING the watch. One written before the watch begins is inert by
    design — a stale marker from a previous run must never end this one — so a test that
    pre-writes it is testing the staleness rule, not this one."""
    marker = tmp_path / "done"
    calls = {"n": 0}

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 3:
            marker.write_text("done")
        return [agent("a1", "blocked", status="busy")]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(marker), "--timeout-seconds", "5"
    )

    assert rc == 0
    assert len(sent) == 1
    assert calls["n"] >= 3, "ended before the marker appeared"


def test_multi_turn_is_still_ended_by_stopped(scripted, sent, stops, tmp_path):
    """The ending that means gone survives the narrowing. Nothing revives a stopped session.

    It appears alive and then stops, which is both what really happens and what lets the watch
    identify it at all — an agent already terminal on the first poll never appears, and the
    watcher waits out its 90s appear window instead of watching anything."""
    scripted([agent("a1", "working")], [agent("a1", "stopped")])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(tmp_path / "never"),
        "--timeout-seconds", "5",
    )

    assert rc == 0
    assert len(sent) == 1
    assert stops == [], "a run already stopped must not be stopped again"


def test_multi_turn_still_ends_when_the_agent_vanishes(scripted, sent, tmp_path):
    """SILENCE IS NOT SUCCESS. A narrowed ending set must not create a watch that runs on
    forever when its agent leaves the list entirely."""
    scripted([agent("a1", "working")], [])

    rc = run_watcher(
        "--multi-turn", "--done-when-exists", str(tmp_path / "never"),
        "--timeout-seconds", "5",
    )

    assert rc == 1
    assert len(sent) == 1
    assert "vanished" in sent[0].lower()


def test_single_turn_callers_keep_every_terminal_state(scripted, sent, stops):
    """Eighteen callers pass neither flag. `blocked` and `done` stay terminal for them — the
    half that must not move."""
    for state in ("done", "blocked", "stopped"):
        sent.clear()
        stops.clear()
        scripted([agent("a1", "working")], [agent("a1", state)])

        rc = run_watcher()

        assert rc == 0, f"{state} stopped ending an ordinary watch"
        assert len(sent) == 1, f"{state} sent no notification for an ordinary watch"


# --- a multi-turn run that was stopped is not a finished one ----------------------------
#
# A multi-turn run says it is finished by creating its marker; `stopped` without that marker
# means something ended it mid-walk. Until 2026-09-23 the hook was told COMPLETED either way,
# and a chain took a cut-off SDD run's `stopped` as the document's finish — measured on a
# live product, where an abandoned walk's SDD run was stopped and its watcher's COMPLETED
# advanced the next walk. A single-turn run keeps its old reading: a clean halt reports
# `stopped` there too (`test_a_stopped_run_is_never_called_a_failure`).


def test_a_multi_turn_run_stopped_without_its_marker_tells_the_hook_stopped(
    scripted, sent, hooks
):
    scripted([agent("a1", "stopped")])

    run_watcher("--multi-turn", "--done-when-exists", "/nonexistent-marker",
                "--on-complete", "/some/hook.sh")

    assert hooks[0][1][0] == watch_agent.HookOutcome.STOPPED
    assert "was stopped" in sent[0]


def test_a_multi_turn_run_that_created_its_marker_is_completed_whatever_its_state(
    monkeypatch, sent, hooks, tmp_path
):
    marker = tmp_path / "done"
    calls = {"n": 0}

    def _list_agents():
        calls["n"] += 1
        if calls["n"] >= 2:
            marker.write_text("done")
            return [agent("a1", "stopped")]
        return [agent("a1", "working")]

    monkeypatch.setattr(watch_agent, "list_agents", _list_agents)

    run_watcher("--multi-turn", "--done-when-exists", str(marker),
                "--on-complete", "/some/hook.sh")

    assert hooks[0][1][0] == watch_agent.HookOutcome.COMPLETED


def test_a_single_turn_run_that_stopped_still_tells_the_hook_completed(scripted, sent, hooks):
    scripted([agent("a1", "stopped")])

    run_watcher("--on-complete", "/some/hook.sh")

    assert hooks[0][1][0] == watch_agent.HookOutcome.COMPLETED


def test_a_multi_turn_run_watched_blind_without_its_marker_tells_the_hook_stopped(
    scripted, sent, hooks
):
    """The blind path's ending too: nothing it watched said it was finished, so a multi-turn
    run is not reported as a completion there either."""
    scripted([
        agent("a1", "stopped", name=AI_TITLE, started=1),
        agent("a2", "stopped", name="some other title", started=99),
    ])

    run_watcher("--appear-seconds", "0.01", "--multi-turn",
                "--done-when-exists", "/nonexistent-marker", "--on-complete", "/some/hook.sh")

    assert hooks[0][1][0] == watch_agent.HookOutcome.STOPPED
