"""`collect_timing.py` recovers per-run timing from a workflow's agent transcripts.

The numbers were structurally 0.0 for every benchmark ever produced, because `timing.json` had two
readers and no writer. The hard part is not arithmetic — it is knowing which run a transcript belongs
to, since the journal's key is an opaque hash and the per-agent meta says only "workflow-subagent". The
only handle is the workspace path inside the transcript's own prompt, so most of these tests pin that
matching rather than the sums.

Drive the real CLI as a subprocess over its exit-code contract, per `test_fixture_guard.py`.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

COLLECT = Path(__file__).resolve().parent / "collect_timing.py"

EXIT_OK = 0
EXIT_PRECONDITION = 2
EXIT_NO_MATCH = 3

EXECUTOR_MARKER = "You are an executor agent."
GRADER_MARKER = "and grade this run."


def _record(ts: str, text: str, usage: dict | None = None, role: str = "user") -> str:
    message = {"role": role, "content": [{"type": "text", "text": text}]}
    if usage:
        message["usage"] = usage
    return json.dumps({"type": "message", "timestamp": ts, "message": message})


def _transcript(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "iteration-9"
    for case in ("case-one", "case-two"):
        for config in ("with_skill", "without_skill"):
            (ws / case / config / "outputs").mkdir(parents=True)
    return ws


@pytest.fixture
def transcripts(tmp_path: Path) -> Path:
    d = tmp_path / "wf_transcripts"
    d.mkdir()
    return d


def _run(transcripts: Path, workspace: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(COLLECT),
            "--transcript-dir",
            str(transcripts),
            "--workspace",
            str(workspace),
        ],
        capture_output=True,
        text=True,
    )


def _timing(workspace: Path, case: str, config: str) -> dict:
    return json.loads((workspace / case / config / "timing.json").read_text())


# --------------------------------------------------------------------------- the happy path


def test_executor_duration_and_tokens(transcripts: Path, workspace: Path):
    outputs = f"{workspace}/case-one/with_skill/outputs"
    _transcript(
        transcripts / "agent-aaa.jsonl",
        [
            _record("2026-07-25T10:00:00.000Z", f"Do the thing.\n{EXECUTOR_MARKER}\nSave to {outputs}"),
            _record(
                "2026-07-25T10:02:30.000Z",
                "done",
                usage={
                    "input_tokens": 10,
                    "output_tokens": 90,
                    "cache_read_input_tokens": 400,
                    "cache_creation_input_tokens": 500,
                },
                role="assistant",
            ),
        ],
    )

    done = _run(transcripts, workspace)

    assert done.returncode == EXIT_OK, done.stderr
    timing = _timing(workspace, "case-one", "with_skill")
    assert timing["executor_duration_seconds"] == 150.0
    assert timing["total_duration_seconds"] == 150.0
    assert timing["duration_ms"] == 150_000
    # Cache reads and creations are real spend — the reason to measure a model change at all.
    assert timing["total_tokens"] == 1000
    # The shape the existing readers expect (aggregate_benchmark._load_timing_into).
    assert "total_duration_seconds" in timing and "total_tokens" in timing


def test_executor_and_graders_are_separated(transcripts: Path, workspace: Path):
    base = f"{workspace}/case-one/without_skill"
    _transcript(
        transcripts / "agent-exec.jsonl",
        [
            _record("2026-07-25T10:00:00.000Z", f"{EXECUTOR_MARKER}\nSave to {base}/outputs"),
            _record("2026-07-25T10:01:00.000Z", "x", usage={"output_tokens": 100}, role="assistant"),
        ],
    )
    _transcript(
        transcripts / "agent-grade.jsonl",
        [
            _record("2026-07-25T10:02:00.000Z", f"Read grader.md {GRADER_MARKER}\nOutputs dir: {base}/outputs"),
            _record("2026-07-25T10:02:20.000Z", "y", usage={"output_tokens": 50}, role="assistant"),
        ],
    )

    assert _run(transcripts, workspace).returncode == EXIT_OK

    timing = _timing(workspace, "case-one", "without_skill")
    assert timing["executor_duration_seconds"] == 60.0
    assert timing["grader_duration_seconds"] == 20.0
    assert timing["grader_agents"] == 1
    assert timing["executor_tokens"] == 100
    assert timing["grader_tokens"] == 50
    assert timing["total_tokens"] == 150
    # Total spans executor start → grader end, so it includes the gap between them.
    assert timing["total_duration_seconds"] == 140.0


def test_multiple_graders_are_summed_and_counted(transcripts: Path, workspace: Path):
    """The split path runs a structural grader, a nuanced grader and a merge — three agents, one run."""
    base = f"{workspace}/case-two/with_skill"
    for i, (start, end) in enumerate(
        [("10:00:00", "10:00:30"), ("10:00:00", "10:01:00"), ("10:01:10", "10:01:20")]
    ):
        _transcript(
            transcripts / f"agent-g{i}.jsonl",
            [
                _record(f"2026-07-25T{start}.000Z", f"{GRADER_MARKER}\nOutputs dir: {base}/outputs"),
                _record(f"2026-07-25T{end}.000Z", "ok", usage={"output_tokens": 10}, role="assistant"),
            ],
        )

    assert _run(transcripts, workspace).returncode == EXIT_OK

    timing = _timing(workspace, "case-two", "with_skill")
    assert timing["grader_agents"] == 3
    assert timing["grader_tokens"] == 30
    assert timing["grader_duration_seconds"] == 100.0  # 30 + 60 + 10, summed not wall-clock


# --------------------------------------------------------------------------- matching and degradation


def test_a_transcript_naming_no_run_is_skipped_not_guessed(transcripts: Path, workspace: Path):
    _transcript(
        transcripts / "agent-setup.jsonl",
        [
            _record("2026-07-25T10:00:00.000Z", "Read evals.json and return structured output."),
            _record("2026-07-25T10:00:05.000Z", "{}", usage={"output_tokens": 5}, role="assistant"),
        ],
    )

    done = _run(transcripts, workspace)

    assert done.returncode == EXIT_NO_MATCH
    assert "no transcript named a run" in done.stderr
    assert not list(workspace.rglob("timing.json"))


def test_a_run_whose_directory_is_missing_is_skipped(transcripts: Path, workspace: Path):
    """The arm that died mid-run has no directory; it must not be resurrected by a timing write."""
    _transcript(
        transcripts / "agent-a.jsonl",
        [
            _record(
                "2026-07-25T10:00:00.000Z",
                f"{EXECUTOR_MARKER}\nSave to {workspace}/case-absent/with_skill/outputs",
            ),
            _record("2026-07-25T10:00:10.000Z", "x", usage={"output_tokens": 1}, role="assistant"),
        ],
    )

    done = _run(transcripts, workspace)

    assert done.returncode == EXIT_OK
    assert "wrote 0 timing.json" in done.stdout
    assert not (workspace / "case-absent").exists()


def test_a_garbled_transcript_does_not_crash_the_others(transcripts: Path, workspace: Path):
    (transcripts / "agent-broken.jsonl").write_text("{not json at all\n\n{\"also\": bad}\n")
    outputs = f"{workspace}/case-one/with_skill/outputs"
    _transcript(
        transcripts / "agent-good.jsonl",
        [
            _record("2026-07-25T10:00:00.000Z", f"{EXECUTOR_MARKER}\nSave to {outputs}"),
            _record("2026-07-25T10:00:20.000Z", "x", usage={"output_tokens": 7}, role="assistant"),
        ],
    )

    done = _run(transcripts, workspace)

    assert done.returncode == EXIT_OK, done.stderr
    assert _timing(workspace, "case-one", "with_skill")["total_tokens"] == 7


def test_missing_dirs_are_precondition_failures(tmp_path: Path, workspace: Path):
    absent = tmp_path / "nope"

    assert _run(absent, workspace).returncode == EXIT_PRECONDITION
    assert _run(workspace, absent).returncode == EXIT_PRECONDITION
