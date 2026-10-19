"""Tests for `subagent_stop_notify.py` — the SubagentStop send that stops a finishing subagent
from telling nobody.

The obligation it replaces was prose and did not hold: `agent-invoke`'s Step 6 was read and followed
six times out of nine in one evening, and the three misses fell in the busiest stretch. So what is
pinned here is the two properties prose could not have — that it fires without anyone remembering,
and that it can never cost the run it reports on.

**Fail open is the load-bearing half.** `brief_anchor_guard.py:28` states the rule for its own
failures — "Fails open on every error, matching `resolve_core.py`" — and this hook is on a sharper
edge than a guard is: `SubagentStop`'s documented exit-code-2 behaviour is "Prevents the subagent
from stopping" (`https://code.claude.com/docs/en/hooks.md`, verified 2026-08-23). A notifier that
raises here would not merely fail to report a run; it would keep the run from ending. Every path
below therefore asserts returncode 0 and empty stdout, including the paths where nothing is sent.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_HOOK = Path(__file__).resolve().parent / "subagent_stop_notify.py"

# A real payload's shape, from the doc's own example. Only the fields this hook reads are given
# values it asserts on; the rest are present so a test never passes because a key was absent.
_PAYLOAD = {
    "session_id": "abc123",
    "transcript_path": "~/.claude/projects/x/abc123.jsonl",
    "cwd": "/Users/someone/projects/kensai/example-host",
    "permission_mode": "acceptEdits",
    "hook_event_name": "SubagentStop",
    "stop_hook_active": False,
    "agent_id": "def456",
    "agent_type": "delegate",
    "agent_transcript_path": "~/.claude/projects/x/abc123/subagents/agent-def456.jsonl",
    "last_assistant_message": "Both seeds retired. Report at system/projects/roles/docs/x.md",
    "background_tasks": [],
    "session_crons": [],
}

_RECORDER = """#!/usr/bin/env bash
printf '%s' "$1" > "$NOTIFIER_MESSAGE_LOG"
"""


def _notifier(tmp_path: Path, body: str = _RECORDER, name: str = "notify.sh") -> Path:
    path = tmp_path / name
    path.write_text(body)
    path.chmod(0o755)
    return path


def _run(tmp_path: Path, payload=_PAYLOAD, notifier: Path | None = None, raw: str | None = None):
    """Run the hook with `payload` on stdin. `notifier` unset means KENSAIAPP_NOTIFIER is removed
    from the environment entirely — the absence case, not an empty value."""
    env = dict(os.environ)
    env["NOTIFIER_MESSAGE_LOG"] = str(tmp_path / "message.txt")
    if notifier is None:
        env.pop("KENSAIAPP_NOTIFIER", None)
    else:
        env["KENSAIAPP_NOTIFIER"] = str(notifier)
    stdin = raw if raw is not None else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(_HOOK)], input=stdin, capture_output=True, text=True, env=env
    )


def _message(tmp_path: Path) -> str | None:
    log = tmp_path / "message.txt"
    return log.read_text() if log.exists() else None


# --- what it sends ---------------------------------------------------------------------


def test_a_finished_delegate_produces_one_message(tmp_path):
    result = _run(tmp_path, notifier=_notifier(tmp_path))

    assert result.returncode == 0
    assert _message(tmp_path) is not None


def test_the_message_names_the_agent_type_that_finished(tmp_path):
    _run(tmp_path, notifier=_notifier(tmp_path))

    assert "delegate" in _message(tmp_path)


def test_the_message_names_the_instance_the_run_was_in(tmp_path):
    """Every satellite runs these hooks from this repo by absolute path, so a message that does
    not say WHERE is ambiguous the first time two instances are running at once."""
    _run(tmp_path, notifier=_notifier(tmp_path))

    assert "example-host" in _message(tmp_path)


def test_the_message_carries_the_agent_id(tmp_path):
    _run(tmp_path, notifier=_notifier(tmp_path))

    assert "def456" in _message(tmp_path)


def test_the_message_carries_the_agents_own_closing_words(tmp_path):
    """`last_assistant_message` is the body, because the delegate's closing message is already
    what the owner needs by contract — the SHAs, the report path, and what is waiting on them."""
    _run(tmp_path, notifier=_notifier(tmp_path))

    assert "Both seeds retired." in _message(tmp_path)


def test_a_long_closing_message_is_truncated_and_says_so(tmp_path):
    """Telegram's sendMessage rejects past 4096 characters, and a rejected send is a run nobody
    hears about with an error nobody sees. Measured over the delegate results in this fleet's
    transcripts, p90 is 826 characters and the longest 1589, so 1500 keeps effectively every real
    message whole — but the bound has to hold for the one that is not."""
    payload = dict(_PAYLOAD, last_assistant_message="x" * 9000)

    _run(tmp_path, payload=payload, notifier=_notifier(tmp_path))

    message = _message(tmp_path)
    assert len(message) < 4096
    assert "x" * 1500 in message
    assert "x" * 1501 not in message
    assert "truncated" in message.lower()


def test_a_missing_closing_message_still_sends(tmp_path):
    """The run finishing is the news. A payload with no `last_assistant_message` — an agent that
    ended without a final text — must still reach the owner, not be silently dropped."""
    payload = {k: v for k, v in _PAYLOAD.items() if k != "last_assistant_message"}

    result = _run(tmp_path, payload=payload, notifier=_notifier(tmp_path))

    assert result.returncode == 0
    assert "delegate" in _message(tmp_path)


# --- what it does not send -------------------------------------------------------------


def test_a_non_delegate_agent_type_sends_nothing(tmp_path):
    """The settings matcher is the filter, but the hook does not depend on the matcher being
    right: a `SubagentStop` for an `Explore` run reaching this file anyway is the 135-a-window
    firehose the volume estimate ruled out, and it must not fire."""
    payload = dict(_PAYLOAD, agent_type="Explore")

    result = _run(tmp_path, payload=payload, notifier=_notifier(tmp_path))

    assert result.returncode == 0
    assert _message(tmp_path) is None


def test_an_unset_notifier_sends_nothing_and_says_nothing(tmp_path):
    """Stay silent on absence. `KENSAIAPP_NOTIFIER` unset is ordinary configuration, not an error,
    and there is deliberately no host-global default: every satellite runs these hook files from the
    host, so a machine path baked in here is a machine path in a shared file."""
    result = _run(tmp_path, notifier=None)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


# --- fail open -------------------------------------------------------------------------


def test_an_unparseable_payload_exits_clean(tmp_path):
    result = _run(tmp_path, raw="{not json at all", notifier=_notifier(tmp_path))

    assert result.returncode == 0
    assert result.stdout == ""
    assert _message(tmp_path) is None


def test_an_empty_payload_exits_clean(tmp_path):
    result = _run(tmp_path, raw="", notifier=_notifier(tmp_path))

    assert result.returncode == 0
    assert result.stdout == ""


def test_a_notifier_that_does_not_exist_exits_clean(tmp_path):
    result = _run(tmp_path, notifier=tmp_path / "nowhere" / "missing.sh")

    assert result.returncode == 0
    assert result.stdout == ""


def test_a_notifier_that_fails_exits_clean(tmp_path):
    """A rejected send is the notifier's own business. The run it is reporting on has already
    finished correctly, and refusing to let it stop over a failed Telegram call would be the
    hook costing more than the silence it replaced."""
    result = _run(tmp_path, notifier=_notifier(tmp_path, "#!/usr/bin/env bash\nexit 1\n"))

    assert result.returncode == 0
    assert result.stdout == ""


def test_a_notifier_that_hangs_does_not_hang_the_session(tmp_path):
    """`SubagentStop` runs before the parent session regains control, so a hook that blocks blocks
    the session. The send is bounded and a timeout is not an error."""
    slow = _notifier(tmp_path, "#!/usr/bin/env bash\nsleep 60\n")

    result = subprocess.run(
        [sys.executable, str(_HOOK)],
        input=json.dumps(_PAYLOAD),
        capture_output=True,
        text=True,
        env=dict(os.environ, KENSAIAPP_NOTIFIER=str(slow),
                 SUBAGENT_STOP_NOTIFY_TIMEOUT="1"),
        timeout=30,
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_no_path_ever_blocks_the_subagent(tmp_path):
    """`SubagentStop` exit code 2 "Prevents the subagent from stopping", and a `decision: block`
    on stdout does the same thing more quietly. Neither may ever come out of this file — so the
    assertion is over every payload shape at once rather than trusting the happy path."""
    cases = [
        dict(_PAYLOAD),
        dict(_PAYLOAD, agent_type="Explore"),
        {k: v for k, v in _PAYLOAD.items() if k != "last_assistant_message"},
        {},
    ]
    for payload in cases:
        result = _run(tmp_path, payload=payload, notifier=_notifier(tmp_path))
        assert result.returncode == 0, payload
        assert result.stdout == "", payload
        assert "block" not in result.stdout, payload


# --- the wiring ------------------------------------------------------------------------


def test_the_hook_is_wired_in_settings_under_subagent_stop_with_the_narrow_matcher():
    """The file existing is not the fix — the fix is the harness running it. And the matcher is
    the volume decision made durable: `delegate` is 6 spawns a day where every agent type is 20,
    and 100 on the day a kaizen fan-out runs."""
    settings = json.loads((Path(__file__).resolve().parents[1] / "settings.json").read_text())

    entries = settings["hooks"]["SubagentStop"]
    assert len(entries) == 1
    assert entries[0]["matcher"] == "delegate"
    commands = [h["command"] for h in entries[0]["hooks"]]
    assert any("subagent_stop_notify.py" in c for c in commands)
    assert all("${CLAUDE_PROJECT_DIR}" in c for c in commands)


def test_the_hook_is_stdlib_only():
    """Vendored hooks run on bare `python3` with no venv (`kensaiapp_structure.md` § Native
    `.claude/` layer). A third-party import here would fail at hook time, which is a silent
    non-fire rather than a visible error."""
    body = _HOOK.read_text()
    third_party = ("import requests", "import yaml", "from anthropic", "import httpx")

    assert not [t for t in third_party if t in body]


# --------------------------------------------------------------------------------------------
# The two filters agree — a half-widening cannot ship
# --------------------------------------------------------------------------------------------
#
# Widening the announcement is TWO edits: the `matcher` in `settings.json` and `_ANNOUNCED` here.
# The second filter is deliberate — it does not depend on `settings.json` being re-read — so
# changing one and not the other produces a hook that looks widened and is not, and nothing says
# so. These tests are that "nothing".
#
# Distinct from `test_settings_wires_the_hook_narrowly` above, which pins the *current* width and
# is expected to change the day the owner widens it. These pin the two filters' *agreement*, which
# is never expected to change.


def _announced() -> set:
    """`_ANNOUNCED` as the hook actually defines it — loaded from the file, never re-typed."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_sub_stop_probe", _HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._ANNOUNCED


def _subagent_stop_matcher() -> str:
    settings = json.loads((Path(__file__).resolve().parents[1] / "settings.json").read_text())
    entries = settings["hooks"]["SubagentStop"]
    assert len(entries) == 1, "more than one SubagentStop block — this check reads exactly one"
    return entries[0].get("matcher", "")


def _agent_types() -> list:
    """Every agent this instance can spawn, read from the roster rather than typed out — so an
    agent added later is covered without anyone remembering to add it here."""
    skills = Path(__file__).resolve().parents[2] / "skills"
    return sorted(p.stem for p in skills.glob("*/.claude/agents/*.md"))


def matcher_admits(matcher: str, agent_type: str) -> bool:
    """Whether a hook matcher fires for an agent type, per the vendor's own three modes.

    `https://code.claude.com/docs/en/hooks.md`, retrieved 2026-08-23: `"*"`, `""` or omitted is
    "Match all"; a value of "Only letters, digits, `_`, `-`, spaces, `,`, and `|`" is "Exact
    string, or list of exact strings separated by `|` or `,` with optional surrounding
    whitespace"; anything else is a JavaScript regular expression, "unanchored".

    Re-implemented here on purpose. The harness does the real matching and this test cannot call
    it, so the alternative is a check that assumes one mode — and a check assuming regex-search
    would pass on `delegate` for every agent type containing that word.
    """
    import re

    if matcher in ("", "*", None):
        return True
    if re.fullmatch(r"[A-Za-z0-9_\- ,|]+", matcher):
        return agent_type in {part.strip() for part in re.split(r"[|,]", matcher)}
    return re.search(matcher, agent_type) is not None


def disagreements(matcher: str, announced: set, agent_types: list) -> list:
    """Every agent type the two filters disagree about. Empty means a widening was done whole."""
    return [
        t for t in agent_types if matcher_admits(matcher, t) != (t in announced)
    ]


def test_agent_roster_agreement_counts_19():
    # A roster read from a path that holds nothing agrees with everything: pin the count, so a
    # glob that finds zero agents fails here instead of passing the agreement test below.
    assert len(_agent_types()) == 19


def test_the_matcher_and_announced_agree_on_every_agent_this_instance_can_spawn():
    assert disagreements(_subagent_stop_matcher(), _announced(), _agent_types()) == []


def test_a_widened_matcher_with_a_stale_announced_is_caught():
    """The failure the second filter creates: `settings.json` edited, the hook not."""
    caught = disagreements("delegate|kensaiapp-auditor", {"delegate"}, _agent_types())

    assert caught == ["kensaiapp-auditor"]


def test_an_announced_entry_no_matcher_admits_is_caught():
    """The inverse: the hook edited, `settings.json` not — the hook filters to nothing new."""
    caught = disagreements("delegate", {"delegate", "kensaiapp-auditor"}, _agent_types())

    assert caught == ["kensaiapp-auditor"]


def test_a_match_all_matcher_needs_every_agent_type_announced():
    """`"*"` is the widest half-widening there is, and the one most likely to be made alone."""
    caught = disagreements("*", {"delegate"}, _agent_types())

    assert "delegate" not in caught
    assert len(caught) == len(_agent_types()) - 1


def test_an_exact_list_is_not_read_as_a_regex():
    """`delegate|pm` is the vendor's exact-list mode, not a pattern. Under a regex-search reading
    `pm` would also admit nothing extra here — but `cto` would admit `cto` only by luck, and a
    single-word matcher like `pm` would admit `principal-pm` by substring."""
    assert matcher_admits("pm", "pm") is True
    assert matcher_admits("pm", "principal-pm") is False
    assert matcher_admits("^p.*pm$", "principal-pm") is True
