"""Tests for `providers.py` — the one reader of the chains' provider file.

Every test hands `ProviderFile` a fake `files` port, so none depends on the delivered file's
contents; the delivered file's own entries are asserted by `test_chain.py`, beside the engine
tables they must match.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import providers
from chain import Files
from providers import (OWED_ITEM, Member, ProviderFile, ProvidersRefused, build_idea_row,
                       document, step)

PATH = "/instance/.providers.toml"


# --- shared with the three engine suites: a copy of the delivered file, handed in ---------------
#
# An engine is given its `ProviderFile`, so a suite hands it one over this port rather than
# pointing any engine at another file (CP-280). These live here, beside the reader's own suite,
# and `test_chain.py`, `test_chain_development.py` and `test_build_idea.py` import them.

# The delivered text is the tracked template at the instance root, located from this file:
# core/tools/test_providers.py -> parents[2] is the root. No suite leans on a live
# `.providers.toml`, which is untracked and absent from a fresh checkout.
EXAMPLE_FILE = Path(__file__).resolve().parents[2] / ".providers.toml.example"
DELIVERED_TEXT = EXAMPLE_FILE.read_text(encoding="utf-8")


class ProviderText:
    """A `files` port holding the provider file's text — `None` for a missing file. A test may
    replace `text` between launches; `reads` counts every read it answered. Each read answers
    `text`, and then, while `then` holds anything, `text` becomes the next of it — so a file that
    changes right after a read is scripted without reaching into the engine."""

    def __init__(self, text: str | None = DELIVERED_TEXT):
        self.text = text
        self.then: list[str | None] = []
        self.reads = 0

    def read_text(self, path: str) -> str | None:
        self.reads += 1
        answered = self.text
        if self.then:
            self.text = self.then.pop(0)
        return answered


def edited_text(changes: dict[str, str | None], text: str = DELIVERED_TEXT) -> str:
    """`text` with each `"<table>.<key>"` of `changes` set to its value, or removed for `None`."""
    tables = tomllib.loads(text)
    for dotted, value in changes.items():
        table, key = dotted.split(".", 1)
        if value is None:
            del tables[table][key]
        else:
            tables.setdefault(table, {})[key] = value
    lines = []
    for table, entries in tables.items():
        lines.append(f"[{table}]")
        lines.extend(f"{json.dumps(key)} = {json.dumps(value)}" for key, value in entries.items())
    return "\n".join(lines) + "\n"


def provider_file(text: str | None = DELIVERED_TEXT, port: ProviderText | None = None
                  ) -> ProviderFile:
    """A `ProviderFile` over `port`, or over a fresh `ProviderText(text)`."""
    return ProviderFile(PATH, port or ProviderText(text))


def provider_files(text: str | None = DELIVERED_TEXT, port: ProviderText | None = None):
    """A `ProviderFiles` over `port`, or over a fresh `ProviderText(text)` — what an engine is
    handed, which answers for whatever instance root the engine asks it about."""
    return providers.ProviderFiles(port or ProviderText(text))


class FakeFiles:
    """A `files` port holding one text, counting the reads it answers."""

    def __init__(self, text: str | None) -> None:
        self.text = text
        self.reads: list[str] = []

    def read_text(self, path: str) -> str | None:
        self.reads.append(path)
        return self.text


class RefusingFiles:
    """A `files` port that fails the test if anything reads it."""

    def read_text(self, path: str) -> str | None:
        raise AssertionError(f"read {path} on a forced launch")


class ChangingFiles:
    """A `files` port whose text is the next of a sequence on every read."""

    def __init__(self, *texts: str) -> None:
        self.texts = list(texts)

    def read_text(self, path: str) -> str | None:
        return self.texts.pop(0)


GOOD = """
[documents]
PRD = "claude"
DESIGN = "codex"

[steps]
design = "claude"
code-integrity = "codex"
audit = "codex"

[build-idea]
"pick a seed" = "claude"

[owed-items]
no-document = "claude"
"""


def _refusal(text: str | None, members) -> str:
    with pytest.raises(ProvidersRefused) as caught:
        ProviderFile(PATH, FakeFiles(text)).resolve(members)
    return str(caught.value)


def _refusal_at(root: str, text: str | None, members) -> str:
    with pytest.raises(ProvidersRefused) as caught:
        providers.ProviderFiles(FakeFiles(text)).at(root).resolve(members)
    return str(caught.value)


def test_resolve_returns_each_asked_member_from_one_read():
    files = FakeFiles(GOOD)
    members = [document("PRD"), document("DESIGN"), step("code-integrity"),
               build_idea_row("pick a seed"), OWED_ITEM]

    resolved = ProviderFile(PATH, files).resolve(members)

    assert resolved == {document("PRD"): "claude", document("DESIGN"): "codex",
                        step("code-integrity"): "codex", build_idea_row("pick a seed"): "claude",
                        OWED_ITEM: "claude"}
    assert files.reads == [PATH]


def test_resolve_refuses_every_missing_entry_by_its_dotted_name():
    text = """
    documents = "PRD"

    [steps]
    design = "claude"
    """
    message = _refusal(text, [step("design"), step("code-integrity"), document("PRD"),
                              build_idea_row("pick a seed"), OWED_ITEM])

    assert "steps.code-integrity" in message
    assert "documents.PRD" in message
    assert 'build-idea."pick a seed"' in message
    assert "owed-items.no-document" in message
    assert "steps.design" not in message


def test_a_key_is_case_sensitive():
    text = """
    [documents]
    design = "codex"

    [steps]
    DESIGN = "claude"
    """
    message = _refusal(text, [document("DESIGN"), step("design")])

    assert "documents.DESIGN" in message
    assert "steps.design" in message


@pytest.mark.parametrize("value, shown", [
    ('"grok"', "'grok'"),
    ("3", "3"),
    ('""', "''"),
    ("true", "True"),
])
def test_a_value_that_is_not_a_known_provider_is_refused_with_entry_and_value(value, shown):
    message = _refusal(f"[steps]\naudit = {value}\n", [step("audit")])

    assert "steps.audit" in message
    assert shown in message


def test_a_missing_file_and_unreadable_text_are_refused_naming_the_path():
    assert PATH in _refusal(None, [step("audit")])
    assert PATH in _refusal("[steps\naudit = ", [step("audit")])


def test_an_entry_naming_no_asked_member_is_ignored():
    text = """
    sdd-cdo = "grok"

    [documents]
    PRD = "claude"

    [steps]
    audit = "codex"
    not-a-step = "grok"

    [sdd]
    cdo = "grok"
    """

    resolved = ProviderFile(PATH, FakeFiles(text)).resolve([step("audit"), document("PRD")])

    assert resolved == {step("audit"): "codex", document("PRD"): "claude"}


def test_a_force_is_returned_without_reading():
    assert ProviderFile(PATH, RefusingFiles()).launch_provider("codex", step("audit")) == "codex"

    files = FakeFiles(GOOD)
    assert ProviderFile(PATH, files).launch_provider("", step("audit")) == "codex"
    assert files.reads == [PATH]


def test_a_step_and_a_document_of_the_same_word_have_different_names():
    assert str(step("design")).lower() != str(document("DESIGN")).lower()
    assert step("design") != document("DESIGN")


def test_member_dotted_form_quotes_a_key_that_needs_it():
    assert str(step("code-integrity")) == "steps.code-integrity"
    assert str(document("DESIGN")) == "documents.DESIGN"
    assert str(build_idea_row("pick a seed")) == 'build-idea."pick a seed"'
    assert str(OWED_ITEM) == "owed-items.no-document"
    assert isinstance(OWED_ITEM, Member)


def test_the_core_carries_no_provider_file():
    """CP-488: no file under `<CORE>` is a provider file, and the reader has no way to name one."""
    assert not (Path(providers.__file__).resolve().parent / "providers.toml").exists()
    assert [name for name in dir(providers) if name.startswith("core_")] == []


def test_the_example_is_the_delivered_file():
    """CP-488: the template at the root parses and holds every member the three engines and the
    ten launchers ask for."""
    import build_idea
    import chain
    import chain_development

    table = tomllib.loads(EXAMPLE_FILE.read_text(encoding="utf-8"))
    launchers = ("skill", "companion-self-answer", "cold-read", "launch-eval-fix",
                 "launch-skill-evals", "product-card", "seeds-from-idea", "launch-apply-packet",
                 "launch-audit", "launch-fix-author")

    assert set(chain.DOCUMENT_REGISTRY) <= set(table["documents"])
    steps = {entry.id for entry in chain_development.DEVELOPMENT_STEPS}
    steps |= {entry.id for entry in chain_development.CHANGE_STEPS}
    assert steps <= set(table["steps"])
    assert set(build_idea._SKILL_ROWS) <= set(table["build-idea"])
    assert "no-document" in table["owed-items"]
    assert set(launchers) <= set(table["launchers"])
    assert len(launchers) == 10


# --- the reader answers for an instance root it is given -----------------------------------------

COPY_COMMAND = "cp .providers.toml.example .providers.toml"


def test_instance_file_is_the_dot_file_at_the_root():
    assert providers.instance_file("/i") == "/i/.providers.toml"


def test_provider_files_reads_the_file_at_the_root_it_is_given():
    port = FakeFiles(GOOD)

    resolved = providers.ProviderFiles(port).at("/i").resolve([step("audit")])

    assert resolved == {step("audit"): "codex"}
    assert port.reads == ["/i/.providers.toml"]


def test_provider_files_reads_afresh_on_every_call():
    port = ChangingFiles('[steps]\nseal = "claude"\n', '[steps]\nseal = "codex"\n')
    files = providers.ProviderFiles(port)

    assert files.at("/i").launch_provider("", step("seal")) == "claude"
    assert files.at("/i").launch_provider("", step("seal")) == "codex"


def test_a_missing_file_names_its_path_and_the_copy_command():
    message = _refusal_at("/i", None, [step("audit")])

    assert "/i/.providers.toml" in message
    assert COPY_COMMAND in message


def test_a_missing_file_refusal_is_the_published_wording_whole():
    """CP-486: the refusal is one string, the same for every engine and the command line, worded
    as the change's text publishes it — the path, why it is needed, and the command that makes
    it."""
    assert _refusal_at("/i", None, [step("audit")]) == (
        "the provider file /i/.providers.toml is missing or cannot be read — every unforced "
        "launch takes its provider from it, and it is made at the instance root with "
        "`cp .providers.toml.example .providers.toml`")


def test_a_missing_file_is_refused_even_beside_an_example(tmp_path):
    (tmp_path / ".providers.toml.example").write_text(GOOD, encoding="utf-8")

    with pytest.raises(ProvidersRefused) as refused:
        providers.ProviderFiles(Files()).at(str(tmp_path)).resolve([step("audit")])

    message = str(refused.value)
    assert str(tmp_path / ".providers.toml") in message
    assert COPY_COMMAND in message


def test_a_forced_launch_at_a_root_reads_nothing():
    files = providers.ProviderFiles(RefusingFiles())

    assert files.at("/i").launch_provider("codex", step("audit")) == "codex"


def test_launch_provider_makes_a_fresh_read_each_time():
    files = ChangingFiles('[steps]\nseal = "claude"\n', '[steps]\nseal = "codex"\n')
    provider_file = ProviderFile(PATH, files)

    assert provider_file.launch_provider("", step("seal")) == "claude"
    assert provider_file.launch_provider("", step("seal")) == "codex"


def test_launch_provider_refuses_a_missing_entry_by_name():
    with pytest.raises(ProvidersRefused, match=r"steps\.seal"):
        ProviderFile(PATH, FakeFiles("[steps]\n")).launch_provider("", step("seal"))


def test_non_utf8_file_is_refused_naming_its_path(tmp_path):
    """CP-282: unreadable bytes must use the same refusal as invalid TOML text."""
    path = tmp_path / "providers.toml"
    path.write_bytes(b'[steps]\naudit = "codex"\n# \xff\n')

    with pytest.raises(ProvidersRefused) as refused:
        ProviderFile(str(path), Files()).resolve([step("audit")])

    assert str(path) in str(refused.value)


@pytest.mark.parametrize("force", ["claude", "codex", "gemini"])
def test_a_force_bypasses_a_non_utf8_file(tmp_path, force):
    """CP-285: even a file that cannot decode must not obstruct an explicit force."""
    path = tmp_path / "providers.toml"
    path.write_bytes(b"\xff")

    assert ProviderFile(str(path), Files()).launch_provider(force, step("audit")) == force


# --- the launchers' entries, and the command-line face a bash launcher reads them through --------

LAUNCHER_NAMES = ("skill", "companion-self-answer", "cold-read", "launch-eval-fix",
                  "launch-skill-evals", "product-card", "seeds-from-idea")

LAUNCHERS_CLAUDE = "[launchers]\n" + "".join(f'{name} = "claude"\n' for name in LAUNCHER_NAMES)


CLI_ROOT = "/i"
CLI_PATH = providers.instance_file(CLI_ROOT)


def _cli(text: str | None, *argv: str) -> tuple[int, str, str]:
    """`providers.run` over a fake file holding `text`, for the instance at `CLI_ROOT`: (exit
    status, stdout, stderr)."""
    stdout, stderr = io.StringIO(), io.StringIO()
    status = providers.run([*argv, "--instance-root", CLI_ROOT],
                           providers.ProviderFiles(FakeFiles(text)), stdout, stderr)
    return status, stdout.getvalue(), stderr.getvalue()


def test_launcher_member_is_named_by_its_table_and_key():
    assert str(providers.launcher("cold-read")) == "launchers.cold-read"
    assert providers.launcher("cold-read") != step("design")
    assert providers.launcher("audit") != step("audit")
    assert providers.launcher("DESIGN") != document("DESIGN")


def test_cli_prints_the_delivered_entry(tmp_path):
    """The real `main`, run as a script: it reads the file at the instance root it is given, and
    stdout is the provider and a newline, which is what a launcher captures as the value."""
    (tmp_path / ".providers.toml").write_text(DELIVERED_TEXT, encoding="utf-8")
    done = subprocess.run([sys.executable, str(Path(providers.__file__)), "launcher", "skill",
                           "--instance-root", str(tmp_path)],
                          capture_output=True, text=True, check=False)

    assert (done.returncode, done.stdout, done.stderr) == (0, "claude\n", "")


def test_cli_without_instance_root_is_a_usage_error_even_beside_a_file_in_its_cwd(tmp_path):
    """CP-485 and the spec's Gap 1, at the real script: run from a directory holding a complete
    `.providers.toml`, a call without `--instance-root` exits 2 with stdout empty — the reader
    never takes its cwd for the instance root."""
    (tmp_path / ".providers.toml").write_text(DELIVERED_TEXT, encoding="utf-8")
    done = subprocess.run([sys.executable, str(Path(providers.__file__)), "launcher", "skill"],
                          cwd=str(tmp_path), capture_output=True, text=True, check=False)

    assert (done.returncode, done.stdout) == (2, "")
    assert "--instance-root" in done.stderr


def test_cli_refuses_a_missing_file_naming_its_path_and_the_copy_command(tmp_path):
    """CP-486, at the real script: an instance holding only the example is refused, naming the
    instance's file and the command that makes it, and the example is not read in its place."""
    (tmp_path / ".providers.toml.example").write_text(DELIVERED_TEXT, encoding="utf-8")
    done = subprocess.run([sys.executable, str(Path(providers.__file__)), "launcher", "skill",
                           "--instance-root", str(tmp_path)],
                          capture_output=True, text=True, check=False)

    assert (done.returncode, done.stdout) == (providers.REFUSED_EXIT, "")
    assert str(tmp_path / ".providers.toml") in done.stderr
    assert COPY_COMMAND in done.stderr


def test_cli_prints_an_entry_from_the_file_it_is_handed():
    assert _cli('[launchers]\nratify = "gemini"\n', "launcher", "ratify") == (0, "gemini\n", "")


def test_cli_refuses_a_missing_entry_naming_the_dotted_key():
    status, stdout, stderr = _cli(GOOD, "launcher", "cold-read")

    assert status not in (0, 2)
    assert stdout == ""
    assert "launchers.cold-read" in stderr


def test_cli_refuses_an_unknown_value_naming_entry_and_value():
    status, stdout, stderr = _cli('[launchers]\nskill = "grok"\n', "launcher", "skill")

    assert status not in (0, 2)
    assert stdout == ""
    assert "launchers.skill" in stderr and "grok" in stderr


@pytest.mark.parametrize("text", [None, "[launchers\nskill = "])
def test_cli_refuses_a_missing_or_non_toml_file_naming_the_path(text):
    status, stdout, stderr = _cli(text, "launcher", "skill")

    assert status not in (0, 2)
    assert stdout == ""
    assert CLI_PATH in stderr


def test_cli_refusal_status_is_one_fixed_number_apart_from_argparses():
    statuses = {_cli(GOOD, "launcher", "cold-read")[0],
                _cli(None, "launcher", "skill")[0],
                _cli(LAUNCHERS_CLAUDE, "launcher", "skill", "--accept", "codex")[0]}

    assert len(statuses) == 1 and statuses.isdisjoint({0, 2})


@pytest.mark.parametrize("text", [None, GOOD, '[launchers]\nskill = "grok"\n'])
def test_cli_forced_value_is_printed_without_reading_the_file(text):
    stdout, stderr = io.StringIO(), io.StringIO()
    status = providers.run(["launcher", "skill", "--forced", "codex", "--instance-root", CLI_ROOT],
                           providers.ProviderFiles(RefusingFiles()), stdout, stderr)
    assert (status, stdout.getvalue(), stderr.getvalue()) == (0, "codex\n", "")

    assert _cli(text, "launcher", "skill", "--forced", "codex") == (0, "codex\n", "")


def test_cli_an_empty_forced_value_is_unforced():
    assert _cli(LAUNCHERS_CLAUDE, "launcher", "skill", "--forced", "") == (0, "claude\n", "")
    assert _cli(GOOD, "launcher", "skill", "--forced", "")[0] not in (0, 2)


def test_cli_accept_set_refuses_a_value_outside_it():
    status, stdout, stderr = _cli('[launchers]\nratify = "codex"\n',
                                  "launcher", "ratify", "--accept", "claude")

    assert status not in (0, 2)
    assert stdout == ""
    assert "launchers.ratify" in stderr and "codex" in stderr

    assert _cli('[launchers]\nratify = "claude"\n',
                "launcher", "ratify", "--accept", "claude") == (0, "claude\n", "")


def test_cli_accept_may_name_several_providers():
    assert _cli('[launchers]\nratify = "codex"\n', "launcher", "ratify",
                "--accept", "claude", "--accept", "codex") == (0, "codex\n", "")


def test_cli_accept_value_that_is_not_a_known_provider_is_refused():
    """An `--accept` outside `PROVIDERS` does not widen what is accepted."""
    status, stdout, stderr = _cli(LAUNCHERS_CLAUDE, "launcher", "skill", "--accept", "grok")

    assert status not in (0, 2)
    assert stdout == ""
    assert "grok" in stderr


def test_cli_accept_set_holding_one_unknown_value_is_refused_though_the_entry_matches():
    """A mistyped member of the set must not pass because another member happens to match."""
    status, stdout, stderr = _cli(LAUNCHERS_CLAUDE, "launcher", "skill",
                                  "--accept", "claude", "--accept", "grok")

    assert status not in (0, 2)
    assert stdout == ""
    assert "grok" in stderr


# --- the command line's one subcommand: the runner command is retired ---------------------------


def test_help_lists_launcher_as_the_only_subcommand(capsys):
    with pytest.raises(SystemExit) as exited:
        providers.run(["--help"], providers.ProviderFiles(FakeFiles(GOOD)), io.StringIO(),
                      io.StringIO())

    shown = capsys.readouterr().out
    assert exited.value.code == 0
    assert "{launcher}" in shown
    assert "sdd-runner" not in shown


def test_retired_runner_command_is_an_invalid_choice(capsys):
    with pytest.raises(SystemExit) as exited:
        providers.run(["sdd-runner"], providers.ProviderFiles(FakeFiles(GOOD)),
                      io.StringIO(), io.StringIO())

    shown = capsys.readouterr()
    assert exited.value.code == 2
    assert shown.out == ""
    assert "invalid choice: 'sdd-runner'" in shown.err


@pytest.mark.parametrize("text", [None, "[launchers\ncold-read = "])
def test_a_launcher_over_a_missing_or_non_toml_file_names_the_path(text):
    status, stdout, stderr = _cli(text, "launcher", "cold-read")

    assert status == providers.REFUSED_EXIT
    assert stdout == ""
    assert CLI_PATH in stderr


def test_a_forced_launcher_does_not_read_the_file():
    stdout, stderr = io.StringIO(), io.StringIO()
    status = providers.run(["launcher", "cold-read", "--forced", "codex",
                            "--instance-root", CLI_ROOT],
                           providers.ProviderFiles(RefusingFiles()), stdout, stderr)
    assert (status, stdout.getvalue(), stderr.getvalue()) == (0, "codex\n", "")

    assert _cli(edited_text({"launchers.cold-read": None}), "launcher", "cold-read",
                "--forced", "codex") == (0, "codex\n", "")
    assert _cli(None, "launcher", "cold-read", "--forced", "codex") == (0, "codex\n", "")

    assert _cli(edited_text({"launchers.cold-read": "gemini"}), "launcher", "cold-read",
                "--forced", "") == (0, "gemini\n", "")
    assert _cli(None, "launcher", "cold-read", "--forced", "")[0] == providers.REFUSED_EXIT


def test_launcher_without_instance_root_is_a_usage_error(capsys):
    """CP-485: the root is required, and a call without it is argparse's usage error, with
    nothing on stdout."""
    stdout = io.StringIO()
    with pytest.raises(SystemExit) as exited:
        providers.run(["launcher", "skill"], providers.ProviderFiles(FakeFiles(GOOD)), stdout,
                      io.StringIO())

    assert exited.value.code == 2
    assert stdout.getvalue() == ""
    assert "--instance-root" in capsys.readouterr().err


def test_launcher_reads_the_root_it_is_given():
    """CP-485: the file read is `<root>/.providers.toml` of the root on the command line."""
    port = FakeFiles(LAUNCHERS_CLAUDE)

    status = providers.run(["launcher", "skill", "--instance-root", "/i"],
                           providers.ProviderFiles(port), io.StringIO(), io.StringIO())

    assert status == 0
    assert port.reads == ["/i/.providers.toml"]


# --- hf and ollama are known providers ------------------------------------------------------------


def test_an_entry_naming_hf_is_accepted():
    resolved = ProviderFile(PATH, FakeFiles('[steps]\nspecs = "hf"\n')).resolve([step("specs")])

    assert resolved[step("specs")] == "hf"


def test_accept_hf_is_not_refused_as_unknown():
    assert _cli('[launchers]\nratify = "hf"\n', "launcher", "ratify",
                "--accept", "hf") == (0, "hf\n", "")


def test_an_entry_naming_ollama_is_accepted():
    resolved = ProviderFile(PATH, FakeFiles('[steps]\nspecs = "ollama"\n')).resolve([step("specs")])

    assert resolved[step("specs")] == "ollama"


def test_accept_ollama_is_not_refused_as_unknown():
    assert _cli('[launchers]\nratify = "ollama"\n', "launcher", "ratify",
                "--accept", "ollama") == (0, "ollama\n", "")


def test_the_delivered_example_routes_nothing_to_ollama():
    """CP-504: the example names ollama in its known-provider comment and in no value."""
    tables = tomllib.loads(DELIVERED_TEXT)

    assert [f"{table}.{key}" for table, entries in tables.items()
            for key, value in entries.items() if value == "ollama"] == []


def test_the_delivered_file_routes_every_entry_to_claude():
    """The owner's call, 2026-10-16, reversing 2026-10-05's five codex entries (UXD, DESIGN,
    plan, code-integrity, audit): every entry in the delivered file runs on claude, and nothing
    runs on codex or hf."""
    tables = tomllib.loads(DELIVERED_TEXT)

    def routed_to(provider):
        return sorted(f"{table}.{key}" for table, entries in tables.items()
                      for key, value in entries.items() if value == provider)

    assert {value for entries in tables.values() for value in entries.values()} == {"claude"}
    assert routed_to("codex") == []
    assert routed_to("hf") == []
