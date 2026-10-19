"""Tests for `core/tools/pytest_guardrails.py` — the net every suite under `core/tools/` and
`core/launchers/` runs inside: no inherited telemetry variable reaches a test, and no channel a
pytest run writes to prints the value of a secret-named environment variable.

The end-to-end tests run a real pytest in a subprocess whose environment holds a fake secret and
nothing of this machine's, so a guard that stops working prints the fake, never a real credential.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.parse
from pathlib import Path

import pytest

import pytest_guardrails as pg

_TOOLS = Path(__file__).resolve().parent
# >= 64 chars, per the plan's Task 1 — long enough that pytest's own truncation (Task 2's
# territory) would shorten it if it were going to.
_FAKE = "fake-secret-value-" + "0123456789abcdef" * 4
# A fake with no repeating period, longer than pytest's default 240-character repr cap
# (`_pytest._io.saferepr.DEFAULT_REPR_MAX_SIZE`). `_FAKE` repeats every 16 characters, so a
# redaction that removes only a fixed-length head or tail run can still look complete on it — the
# same fixed tail recurs every 16 characters and gets chopped out along the middle. This one cannot
# hide a surviving run that way.
_LONG_FAKE = "fake-" + "".join(hashlib.sha256(str(i).encode()).hexdigest() for i in range(5))


def _run_pytest(
    tmp_path: Path,
    test_source: str,
    extra_env: dict[str, str],
    args: tuple[str, ...] = (),
    junit_name: str = "junit.xml",
) -> subprocess.CompletedProcess:
    """Run `test_source` under the real guard (`-p pytest_guardrails`)."""
    test_file = tmp_path / "test_probe.py"
    test_file.write_text(test_source)
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp_path), "PYTHONPATH": str(_TOOLS), **extra_env}
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-p", "pytest_guardrails",
         "-p", "no:cacheprovider", "--junitxml", str(tmp_path / junit_name), *args],
        capture_output=True, text=True, env=env, cwd=tmp_path, timeout=120,
    )


def _longest_shared_run(text: str, secret: str) -> int:
    """The length of the longest contiguous run `text` and `secret` share — a cheap, exact
    longest-common-substring by sliding every window size down from `len(secret)`."""
    for size in range(len(secret), 0, -1):
        for start in range(len(secret) - size + 1):
            if secret[start : start + size] in text:
                return size
    return 0


def _run_pytest_bare(
    tmp_path: Path,
    test_source: str,
    extra_env: dict[str, str],
    args: tuple[str, ...] = (),
    junit_name: str = "junit_bare.xml",
) -> subprocess.CompletedProcess:
    """Run the same `test_source` with no guard plugin loaded — the parity baseline."""
    test_file = tmp_path / "test_probe.py"
    test_file.write_text(test_source)
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp_path), "PYTHONPATH": str(_TOOLS), **extra_env}
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file),
         "-p", "no:cacheprovider", "--junitxml", str(tmp_path / junit_name), *args],
        capture_output=True, text=True, env=env, cwd=tmp_path, timeout=120,
    )


class TestSecretValues:
    def test_secret_named_variables_are_collected(self):
        env = {
            "ALPACA_API_SECRET": _FAKE,
            "ALPACA_API_KEY_ID": "PKABCDEFGH",
            "GITHUB_TOKEN": "ghp_abcdefgh",
            "SOME_PASSWORD": "hunter2hunter2",
        }
        assert pg.secret_values(env) == env

    def test_ordinary_names_and_short_values_are_not(self):
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/Users/someone",
            "KEY_COUNT": "3",
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        }
        assert pg.secret_values(env) == {}


class TestRedact:
    def test_every_occurrence_is_replaced_by_its_name(self):
        text = f"assert 'X' in {{'ALPACA_API_SECRET': '{_FAKE}'}} and again {_FAKE}"
        out = pg.redact(text, {"ALPACA_API_SECRET": _FAKE})
        assert _FAKE not in out
        assert out.count("<redacted:ALPACA_API_SECRET>") == 2

    def test_text_without_a_secret_is_returned_unchanged(self):
        assert pg.redact("plain text", {"X_TOKEN": _FAKE}) == "plain text"

    def test_a_longer_secret_is_replaced_before_a_shorter_one_it_contains(self):
        out = pg.redact("abcdefgh12345678", {"A_TOKEN": "abcdefgh", "B_TOKEN": "abcdefgh12345678"})
        assert out == "<redacted:B_TOKEN>"

    def test_a_head_run_of_the_minimum_length_is_redacted(self):
        head = _FAKE[: pg._MIN_FRAGMENT_LENGTH]
        out = pg.redact(f"prefix {head} suffix", {"X_TOKEN": _FAKE})
        assert head not in out
        assert "<redacted:X_TOKEN>" in out

    def test_a_tail_run_of_the_minimum_length_is_redacted(self):
        tail = _FAKE[-pg._MIN_FRAGMENT_LENGTH :]
        out = pg.redact(f"prefix {tail} suffix", {"X_TOKEN": _FAKE})
        assert tail not in out
        assert "<redacted:X_TOKEN>" in out

    # Plan Task 2: "Any run of at least N characters taken from the start or the end of a secret
    # value is redacted" — the run, not its first or last N characters.
    @pytest.mark.parametrize("length", [pg._MIN_FRAGMENT_LENGTH + 1, 40, 118])
    def test_a_head_run_longer_than_the_minimum_is_redacted_whole(self, length):
        head = _LONG_FAKE[:length]
        out = pg.redact(f"prefix '{head}...' suffix", {"X_TOKEN": _LONG_FAKE})
        assert _longest_shared_run(out, _LONG_FAKE) < pg._MIN_FRAGMENT_LENGTH, out
        assert out == "prefix '<redacted:X_TOKEN>...' suffix"

    @pytest.mark.parametrize("length", [pg._MIN_FRAGMENT_LENGTH + 1, 40, 118])
    def test_a_tail_run_longer_than_the_minimum_is_redacted_whole(self, length):
        tail = _LONG_FAKE[-length:]
        out = pg.redact(f"prefix '...{tail}' suffix", {"X_TOKEN": _LONG_FAKE})
        assert _longest_shared_run(out, _LONG_FAKE) < pg._MIN_FRAGMENT_LENGTH, out
        assert out == "prefix '...<redacted:X_TOKEN>' suffix"

    def test_a_run_one_shorter_than_the_minimum_is_left_unchanged(self):
        short_head = _FAKE[: pg._MIN_FRAGMENT_LENGTH - 1]
        text = f"prefix {short_head} suffix"
        assert pg.redact(text, {"X_TOKEN": _FAKE}) == text


class TestShortenedFragmentThreshold:
    def test_the_constant_is_no_larger_than_what_pytest_actually_keeps(self, tmp_path):
        """`_MIN_FRAGMENT_LENGTH` must never exceed the shortest head or tail run pytest's own
        truncation (`_pytest._io.saferepr._ellipsize`, driven off `_pytest/assertion/util.py`'s
        `maxsize` for a two-character operator) is measured to keep — a run shorter than the
        constant would never be checked for. Measured here against a live, unguarded pytest run
        with a plain long value (no secret-shaped name), so this fails the day pytest's own
        truncation changes shape, rather than assuming today's formula holds forever."""
        probe = "V" * 200
        result = _run_pytest_bare(tmp_path, f"def test_fails():\n    assert '{probe}' == 'x'\n", {})
        line = next(
            candidate for candidate in result.stdout.splitlines() if "AssertionError: assert '" in candidate
        )
        head_run, _, tail_run = line.partition("...")
        head_len = len(head_run) - len(head_run.rstrip("V"))
        tail_len = len(tail_run) - len(tail_run.lstrip("V"))
        assert head_len >= pg._MIN_FRAGMENT_LENGTH, (head_len, pg._MIN_FRAGMENT_LENGTH)
        assert tail_len >= pg._MIN_FRAGMENT_LENGTH, (tail_len, pg._MIN_FRAGMENT_LENGTH)


class TestShortenedValuesLeakNoRun:
    def test_the_shortened_summary_line_shares_no_run_at_or_above_the_minimum(self, tmp_path):
        source = f"def test_leaks():\n    assert '{_FAKE}' == 'something else'\n"
        for extra_args in (("-rA",), ("-v", "-rA")):
            result = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=extra_args)
            output = result.stdout + result.stderr
            shared = _longest_shared_run(output, _FAKE)
            assert shared < pg._MIN_FRAGMENT_LENGTH, (
                f"a {shared}-char run of the secret survived under {extra_args}"
            )


class TestAFailingTestPrintsNoSecret:
    def test_the_report_the_summary_the_captured_output_and_junit_are_redacted(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_leaks():\n"
            "    print(dict(os.environ))\n"
            "    assert 'NOT-THERE' in dict(os.environ)\n",
            {"PROBE_API_SECRET": _FAKE},
            args=("-rA",),
        )
        output = result.stdout + result.stderr
        assert result.returncode == 1, "the probe test was written to fail"
        assert _FAKE not in output, "the fake secret reached the terminal output"
        assert "<redacted:PROBE_API_SECRET>" in result.stdout
        assert _FAKE not in (tmp_path / "junit.xml").read_text(), "the fake secret reached junit"

    def test_a_secret_a_test_sets_for_itself_is_redacted_too(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "def test_leaks(monkeypatch):\n"
            f"    monkeypatch.setenv('LATE_TOKEN', '{_FAKE}')\n"
            f"    assert '{_FAKE}' == 'something else'\n",
            {},
            args=("-rA",),
        )
        assert result.returncode == 1
        assert _FAKE not in result.stdout + result.stderr

    def test_a_secret_a_test_sets_for_itself_is_redacted_under_xdist(self, tmp_path):
        """Under `-n`, the test runs in a worker and the report prints in the controller — which
        never saw the worker's `monkeypatch.setenv`."""
        pytest.importorskip("xdist")
        result = _run_pytest(
            tmp_path,
            "def test_leaks(monkeypatch):\n"
            f"    monkeypatch.setenv('LATE_TOKEN', '{_FAKE}')\n"
            f"    assert '{_FAKE}' == 'something else'\n",
            {},
            args=("-rA", "-n", "2"),
        )
        assert result.returncode == 1
        assert _FAKE not in result.stdout + result.stderr
        assert _FAKE not in (tmp_path / "junit.xml").read_text(), "the fake secret reached junit"


class TestACollectionErrorPrintsNoSecret:
    def test_a_module_that_raises_the_secret_at_import_leaks_nothing(self, tmp_path):
        source = f"raise RuntimeError('boom {_FAKE}')\n"
        guarded = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-rA",))
        bare = _run_pytest_bare(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-rA",))
        output = guarded.stdout + guarded.stderr
        assert _FAKE not in output, "the fake secret reached a collection-error report"
        assert _FAKE not in (tmp_path / "junit.xml").read_text(), "the fake secret reached junit"
        assert guarded.returncode == bare.returncode, "the guard changed the run's outcome"


class TestAWarningPrintsNoSecret:
    def test_a_warning_carrying_the_secret_leaks_nothing_in_the_summary(self, tmp_path):
        source = (
            "import warnings\n"
            "def test_w():\n"
            f"    warnings.warn('careful: {_FAKE}')\n"
            "    assert True\n"
        )
        guarded = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-rA",))
        bare = _run_pytest_bare(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-rA",))
        output = guarded.stdout + guarded.stderr
        assert _FAKE not in output, "the fake secret reached the warnings summary"
        assert _FAKE not in (tmp_path / "junit.xml").read_text(), "the fake secret reached junit"
        assert guarded.returncode == bare.returncode, "the guard changed the run's outcome"


class TestAParametrizeIdPrintsNoSecret:
    def test_a_parametrize_id_carrying_the_secret_leaks_nothing_under_v_and_rA(self, tmp_path):
        source = (
            "import pytest\n"
            f"@pytest.mark.parametrize('val', ['{_FAKE}'])\n"
            "def test_p(val):\n"
            "    assert True\n"
        )
        guarded = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-v", "-rA"))
        bare = _run_pytest_bare(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-v", "-rA"))
        output = guarded.stdout + guarded.stderr
        assert _FAKE not in output, "the fake secret reached a parametrize id"
        assert _FAKE not in (tmp_path / "junit.xml").read_text(), "the fake secret reached junit"
        assert guarded.returncode == bare.returncode, "the guard changed the run's outcome"


class TestASkipReasonPrintsNoSecretAndExitsClean:
    def test_a_skip_reason_carrying_the_secret_leaks_nothing_and_exits_0_under_rA(self, tmp_path):
        source = (
            "import pytest\n"
            "def test_s():\n"
            f"    pytest.skip('skipping because {_FAKE}')\n"
        )
        guarded = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-rA",))
        bare = _run_pytest_bare(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-rA",))
        output = guarded.stdout + guarded.stderr
        assert _FAKE not in output, "the fake secret reached the skip summary"
        assert _FAKE not in (tmp_path / "junit.xml").read_text(), "the fake secret reached junit"
        assert bare.returncode == 0, "a skip exits 0 with no guard at all — the baseline itself"
        assert guarded.returncode == 0, "replacing longrepr with the wrong type used to break this"
        assert guarded.returncode == bare.returncode, "the guard changed the run's outcome"


class TestTbLineKeepsPathAndLine:
    def test_tb_line_keeps_the_files_path_and_line_number(self, tmp_path):
        source = f"def test_fails():\n    assert '{_FAKE}' == 'x'\n"
        result = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("--tb=line",))
        assert _FAKE not in result.stdout + result.stderr
        assert re.search(r"test_probe\.py:\d+: AssertionError", result.stdout), (
            "the --tb=line summary lost its path:line"
        )


class TestALongSecretShortenedByTheReprCapLeaksNoRun:
    """Plan Task 2, behaviour 1, on a channel the 64-character fake never reaches: pytest's
    assertion rewriting caps a repr at `DEFAULT_REPR_MAX_SIZE` (240) and keeps a head and a tail
    far longer than `_MIN_FRAGMENT_LENGTH`. Every run of at least N characters from either end
    must go, not only its outermost N."""

    @pytest.mark.parametrize("extra_args", [(), ("-q",), ("-q", "--tb=line"), ("-rA",)])
    def test_no_run_of_the_minimum_length_survives_on_any_channel(self, tmp_path, extra_args):
        source = (
            "import os\n"
            "def test_leaks():\n"
            "    assert 'NOT-THERE' in os.environ['PROBE_API_SECRET']\n"
        )
        result = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _LONG_FAKE}, args=extra_args)
        assert result.returncode == 1, "the probe test was written to fail"
        shared = _longest_shared_run(result.stdout + result.stderr, _LONG_FAKE)
        assert shared < pg._MIN_FRAGMENT_LENGTH, (
            f"a {shared}-char run of the secret survived under {extra_args}"
        )
        junit_shared = _longest_shared_run((tmp_path / "junit.xml").read_text(), _LONG_FAKE)
        assert junit_shared < pg._MIN_FRAGMENT_LENGTH, f"a {junit_shared}-char run reached junit"


class TestTheGuardNeverChangesTheExitCode:
    """Plan Task 1: "For each probe, the exit code with the guard equals the exit code without
    it." The collection, warning, parametrize and skip probes check this themselves; these are the
    remaining probes — a failing assertion, captured output, and `--tb=line`."""

    @pytest.mark.parametrize(
        "source, args",
        [
            (f"def test_fails():\n    assert '{_FAKE}' == 'something else'\n", ("-rA",)),
            (f"def test_prints():\n    print('{_FAKE}')\n    assert True\n", ("-rA",)),
            (f"def test_prints_and_fails():\n    print('{_FAKE}')\n    assert False\n", ("-rA",)),
            (f"def test_fails():\n    assert '{_FAKE}' == 'x'\n", ("--tb=line",)),
        ],
        ids=["assertion", "captured-output-pass", "captured-output-fail", "tb-line"],
    )
    def test_guarded_and_bare_runs_exit_the_same(self, tmp_path, source, args):
        guarded = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=args)
        bare = _run_pytest_bare(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=args)
        assert _FAKE not in guarded.stdout + guarded.stderr
        assert guarded.returncode == bare.returncode, (guarded.returncode, bare.returncode)


class TestNoReportChangesType:
    """Plan Task 1: "No report's `longrepr` is replaced by a value of a different type." Observed
    from inside the child run by a conftest that logs each report as pytest's own reporters receive
    it, and compared with the same run under no guard."""

    _RECORDER = (
        "import os\n"
        "def pytest_runtest_logreport(report):\n"
        "    with open(os.environ['LONGREPR_LOG'], 'a') as log:\n"
        "        log.write(f'{report.nodeid} {report.when} {report.outcome} '\n"
        "                  f'{type(report.longrepr).__name__}\\n')\n"
    )
    _PROBES = (
        "import pytest\n"
        "def test_passes():\n"
        f"    print('{_FAKE}')\n"
        "def test_fails():\n"
        f"    assert '{_FAKE}' == 'x'\n"
        "def test_skips():\n"
        f"    pytest.skip('because {_FAKE}')\n"
        f"@pytest.mark.xfail(reason='{_FAKE}')\n"
        "def test_xfails():\n"
        "    assert False\n"
    )

    def test_every_reports_longrepr_type_matches_the_unguarded_run(self, tmp_path):
        (tmp_path / "conftest.py").write_text(self._RECORDER)
        guarded_log, bare_log = tmp_path / "guarded.log", tmp_path / "bare.log"
        _run_pytest(tmp_path, self._PROBES, {"PROBE_API_SECRET": _FAKE,
                                             "LONGREPR_LOG": str(guarded_log)}, args=("-rA",))
        _run_pytest_bare(tmp_path, self._PROBES, {"PROBE_API_SECRET": _FAKE,
                                                  "LONGREPR_LOG": str(bare_log)}, args=("-rA",))
        guarded, bare = guarded_log.read_text().splitlines(), bare_log.read_text().splitlines()
        assert len(bare) == 12, bare  # four tests, three phases each
        assert guarded == bare


class TestCaptureNoIsMeasuredNotAssumed:
    def test_output_under_capture_no_is_not_covered_by_this_guard(self, tmp_path):
        """`-s`/`--capture=no` disables pytest's own capturing, so a test's `print()` writes
        straight to the real file descriptor rather than through the terminal writer this guard
        patches. Measured here, not assumed: the fake still leaks under `-s`. If this assertion
        ever starts failing, `-s` output has become covered — update the module docstring and
        this test together, in the same commit."""
        source = f"def test_leaks():\n    print('{_FAKE}')\n    assert True\n"
        result = _run_pytest(tmp_path, source, {"PROBE_API_SECRET": _FAKE}, args=("-s",))
        assert result.returncode == 0
        assert _FAKE in result.stdout, "this guard does not cover -s output — see the docstring"


class TestNoAmbientTelemetry:
    def test_a_test_sees_no_inherited_telemetry_variable(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_clean():\n"
            "    assert [k for k in os.environ\n"
            "            if k.startswith(('OTEL_', 'CLAUDE_CODE_ENABLE_TELEMETRY'))] == []\n",
            {"CLAUDE_CODE_ENABLE_TELEMETRY": "1", "OTEL_LOGS_EXPORTER": "otlp"},
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_test_that_sets_its_own_telemetry_variable_keeps_it(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_sets(monkeypatch):\n"
            "    monkeypatch.setenv('OTEL_LOGS_EXPORTER', 'otlp')\n"
            "    assert os.environ['OTEL_LOGS_EXPORTER'] == 'otlp'\n",
            {},
        )
        assert result.returncode == 0, result.stdout[-2000:]


class TestNoAmbientColour:
    """A shell that exports `FORCE_COLOR` makes Python 3.14's argparse colour `--help`, and the
    three `test_commit_builder.py` help tests then look for plain text and fail. Measured
    2026-10-02: `pytest core/tools/` gave 3 failed, 5585 passed, 1 skipped under it, and
    `NO_COLOR=1 pytest core/tools/` gave 5588 passed, 1 skipped."""

    def test_a_test_sees_no_inherited_force_colour_and_a_no_colour_request(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_clean():\n"
            "    assert 'FORCE_COLOR' not in os.environ\n"
            "    assert os.environ['NO_COLOR'] == '1'\n",
            {"FORCE_COLOR": "1"},
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_test_that_sets_its_own_force_colour_keeps_it(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_sets(monkeypatch):\n"
            "    monkeypatch.setenv('FORCE_COLOR', '1')\n"
            "    assert os.environ['FORCE_COLOR'] == '1'\n",
            {},
        )
        assert result.returncode == 0, result.stdout[-2000:]


class TestNoAmbientProviderForce:
    """A shell that exports `KENSAIAPP_AGENT_PROVIDER` forces every launcher a test drives, which
    then appends `--provider` to the argv the test compares. Measured 2026-10-03: the chain-*
    and build-idea launcher suites gave 5 failed, 268 passed under it."""

    def test_a_test_sees_no_inherited_provider_force(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_clean():\n"
            "    assert 'KENSAIAPP_AGENT_PROVIDER' not in os.environ\n",
            {"KENSAIAPP_AGENT_PROVIDER": "claude"},
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_test_that_sets_its_own_provider_force_keeps_it(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_sets(monkeypatch):\n"
            "    monkeypatch.setenv('KENSAIAPP_AGENT_PROVIDER', 'codex')\n"
            "    assert os.environ['KENSAIAPP_AGENT_PROVIDER'] == 'codex'\n",
            {},
        )
        assert result.returncode == 0, result.stdout[-2000:]


class TestNoAmbientOllama:
    """A launcher or adapter case that builds an `ollama` command asks the server at
    `KENSAIAPP_OLLAMA_URL` whether it answers. Left unset it asks `http://localhost:11434`, the
    owner's live server, so a suite would pass or fail on whether Ollama happens to be running."""

    def test_the_ollama_address_points_where_nothing_listens(self):
        address = urllib.parse.urlsplit(os.environ["KENSAIAPP_OLLAMA_URL"])

        assert address.scheme == "http"
        assert address.hostname == "127.0.0.1"
        with pytest.raises(ConnectionRefusedError):
            socket.create_connection((address.hostname, address.port), timeout=5).close()

    def test_the_guard_overrides_an_inherited_ollama_address(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_guarded():\n"
            "    assert os.environ['KENSAIAPP_OLLAMA_URL'] != 'http://localhost:11434'\n"
            "    assert os.environ['KENSAIAPP_OLLAMA_URL'].startswith('http://127.0.0.1:')\n",
            {"KENSAIAPP_OLLAMA_URL": "http://localhost:11434"},
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_test_that_sets_its_own_ollama_address_keeps_it(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_sets(monkeypatch):\n"
            "    monkeypatch.setenv('KENSAIAPP_OLLAMA_URL', 'http://127.0.0.1:1')\n"
            "    assert os.environ['KENSAIAPP_OLLAMA_URL'] == 'http://127.0.0.1:1'\n",
            {},
        )
        assert result.returncode == 0, result.stdout[-2000:]


class TestNoAmbientGitConfig:
    """A session whose own `core.hooksPath` is injected via `GIT_CONFIG_COUNT` +
    `GIT_CONFIG_KEY_N`/`GIT_CONFIG_VALUE_N` (rather than a repo-local `.git/config`) leaks that
    override into every `git` subprocess a test spawns — including a throwaway fixture repo's own
    commit, which this repo's real `commit-msg` hook then refuses for trailers no fixture message
    carries. Measured 2026-09-23: under such a session, `pytest core/tools/` reported 234 failed;
    with the ambient variables cleared, 3762 passed, 1 skipped."""

    def test_a_test_sees_no_inherited_git_config_override(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_clean():\n"
            "    assert [k for k in os.environ\n"
            "            if k == 'GIT_CONFIG_COUNT'\n"
            "            or k.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_'))] == []\n",
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": "/nonexistent",
            },
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_test_that_sets_its_own_git_config_override_keeps_it(self, tmp_path):
        result = _run_pytest(
            tmp_path,
            "import os\n"
            "def test_sets(monkeypatch):\n"
            "    monkeypatch.setenv('GIT_CONFIG_COUNT', '1')\n"
            "    assert os.environ['GIT_CONFIG_COUNT'] == '1'\n",
            {},
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_fixture_commit_is_not_refused_by_an_injected_hookspath(self, tmp_path):
        # Reproduces the observed failure directly: a throwaway fixture repo's own seed commit,
        # made under a session whose core.hooksPath is injected via GIT_CONFIG_* rather than
        # repo-local config, must not be refused by the real hook that path points at — the
        # fixture message carries none of the trailers that hook requires.
        real_hooks = tmp_path / "real_hooks"
        real_hooks.mkdir()
        hook = real_hooks / "commit-msg"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        result = _run_pytest(
            tmp_path,
            "import subprocess\n"
            "def _git(repo, *args):\n"
            "    return subprocess.run(\n"
            "        ['git', '-C', str(repo), *args], capture_output=True, text=True\n"
            "    )\n"
            "def test_fixture_commit_lands(tmp_path):\n"
            "    repo = tmp_path / 'throwaway'\n"
            "    repo.mkdir()\n"
            "    _git(repo, 'init', '-q')\n"
            "    _git(repo, 'config', 'user.name', 'Test')\n"
            "    _git(repo, 'config', 'user.email', 'test@example.com')\n"
            "    _git(repo, 'config', 'commit.gpgsign', 'false')\n"
            "    (repo / 'seed.txt').write_text('seed\\n')\n"
            "    _git(repo, 'add', 'seed.txt')\n"
            "    result = _git(repo, 'commit', '-q', '-m', 'seed')\n"
            "    assert result.returncode == 0, result.stderr\n",
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": str(real_hooks),
            },
        )
        assert result.returncode == 0, result.stdout[-4000:]


class TestEachSuiteRootLoadsTheGuardByEffect:
    """Proof by effect, not by text: a probe file collected *under the real root* — so its real
    `conftest.py` is on the ancestry pytest walks — runs with the fixture and the hook active,
    with no `-p pytest_guardrails` anywhere on its command line. A conftest whose import is
    present but broken, or commented out, fails this; a text grep on the conftest would not
    have."""

    @pytest.mark.parametrize("suite_root", ["tools", "launchers"])
    def test_a_test_collected_under_the_root_runs_with_the_guard_active(self, suite_root, tmp_path):
        root = _TOOLS.parent / suite_root
        probe_dir = root / "_pytest_guardrails_wiring_probe"
        shutil.rmtree(probe_dir, ignore_errors=True)  # a prior run's crash may have left this
        probe_dir.mkdir()
        try:
            probe_file = probe_dir / "test_probe.py"
            probe_file.write_text(
                "import os\n"
                "def test_ambient_telemetry_is_cleared():\n"
                "    assert [k for k in os.environ\n"
                "            if k.startswith(('OTEL_', 'CLAUDE_CODE_ENABLE_TELEMETRY'))] == []\n"
                "    assert 'KENSAIAPP_AGENT_PROVIDER' not in os.environ\n"
                "\n"
                "def test_a_secret_is_redacted(monkeypatch):\n"
                f"    monkeypatch.setenv('WIRING_PROBE_TOKEN', '{_FAKE}')\n"
                f"    assert '{_FAKE}' == 'not it'\n"
            )
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(tmp_path),
                "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
                "OTEL_LOGS_EXPORTER": "otlp",
                "KENSAIAPP_AGENT_PROVIDER": "claude",
            }
            junit = tmp_path / "junit.xml"
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(probe_file), "-p", "no:cacheprovider", "-q",
                 "--junitxml", str(junit)],
                capture_output=True, text=True, env=env, timeout=120,
            )
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)
        output = result.stdout + result.stderr
        assert "1 failed, 1 passed" in output, (
            "expected exactly one clean pass (ambient telemetry) and one redacted failure "
            f"(the secret assertion) — got:\n{output}"
        )
        assert _FAKE not in output, f"{suite_root}/conftest.py did not load the guard"
        # The guard is three hooks and a fixture; the junit redaction is the one the terminal
        # assertions above cannot see, so a conftest that dropped it would otherwise pass.
        assert _FAKE not in junit.read_text(), f"{suite_root}/conftest.py did not load the junit hook"
