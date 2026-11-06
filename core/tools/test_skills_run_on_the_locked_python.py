"""Standing guard: a command a skill tells an agent to run starts with the locked runner, never
`python3`.

It reads every `SKILL.md` below a skills tree and every file below the `prompts/` folder of the
skill that holds it, and fails naming each line on which `python3` starts a command. Three forms
are commands: a line in a fenced block, a line in an indented code block, and an inline code span.
A shebang, a longer executable name, a lookup and a mention of the word are not. An inline span
inside a double-quoted sentence is something a document says to its own reader, such as an example
a README gives, and is not a command either.

The same function reads a temporary tree in the fixture tests and the instance's real `skills/`
tree, so the fixtures prove the diagnostics the real tree would show. A missing root, a folder that
cannot be listed and a file that cannot be read stay errors: none of them reads as a clean scan.
"""

from __future__ import annotations

import bisect
import os
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"

SKILL_FILE = "SKILL.md"
PROMPTS_FOLDER = "prompts"

REPORT_HEADER = (
    "Each line below is a command that a skill's instructions tell an agent to run with python3, "
    "so it runs on whichever Python PATH finds first, not on the Python that the instance's "
    ".python-version names.\n"
    'Replace python3 with "<CORE>/tools/locked_python.sh", quotes included, and leave the rest '
    "of the line as it is."
)

# A command starts at the beginning of its text or after a separator. Shell keywords, variable
# assignments and a word that runs the next word as a program found on PATH (`env` with its options,
# `nohup`, `command`) may stand in front of the program, whose name may be quoted. `python3.15`,
# `python3-config` and a path such as `/usr/bin/python3` name another program and are not matched,
# and neither is a lookup such as `command -v python3` or a quoted name in a call like
# `shutil.which("python3")`, which nothing runs.
COMMAND_START = re.compile(
    r"(?:^|[;&|({`])\s*"
    r"(?:"
    r"(?:then|do|else|elif|exec|time|nohup|command)\s+"
    r"|(?:/[\w.-]+)*/?env(?:\s+(?:-u\s+\S+|-[\w-]*))*\s+"
    r"|[A-Za-z_]\w*=\S*\s+"
    r")*"
    r"(?:\"(?P<double>python3)\"(?=\s|$)"
    r"|'(?P<single>python3)'(?=\s|$)"
    r"|(?P<bare>python3)(?![\w./-]))"
)
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})")
INDENTED_CODE_COLUMNS = 4
OPENING_CURLY_QUOTE = "“"
CLOSING_CURLY_QUOTE = "”"


@dataclass(frozen=True)
class Finding:
    """One physical line on which `python3` starts a command."""

    path: str
    line: int
    text: str


@dataclass(frozen=True)
class _Span:
    start: int
    content_start: int
    content_end: int
    end: int


def _walk_files(directory: Path) -> list[Path]:
    """Every file below `directory`. An error listing a folder is raised, never skipped."""
    files: list[Path] = []
    with os.scandir(directory) as entries:
        for entry in sorted(entries, key=lambda item: item.name):
            if entry.is_dir(follow_symlinks=False):
                files.extend(_walk_files(Path(entry.path)))
            else:
                files.append(Path(entry.path))
    return files


def discover_instruction_files(root: Path) -> list[Path]:
    """Each `SKILL.md` below `root`, and each file below `prompts/` in the folder holding one."""
    files = _walk_files(root)
    skill_folders = [path.parent for path in files if path.name == SKILL_FILE]
    scoped = [
        path
        for path in files
        if path.name == SKILL_FILE
        or any(path.is_relative_to(folder / PROMPTS_FOLDER) for folder in skill_folders)
    ]
    return sorted(scoped)


def _command_tokens(command_text: str) -> list[tuple[int, int]]:
    """Each `python3` starting a command: its offset, and where its word, quotes included, ends."""
    tokens: list[tuple[int, int]] = []
    for match in COMMAND_START.finditer(command_text):
        name = next(group for group in ("double", "single", "bare") if match.group(group))
        tokens.append((match.start(name), match.end()))
    return tokens


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _fenced_line_findings(line_number: int, line: str) -> list[int]:
    return [line_number] if _command_tokens(line) else []


def _find_spans(text: str) -> list[_Span]:
    """The inline code spans of a paragraph: a run of backticks closed by a run of the same size."""
    spans: list[_Span] = []
    position = 0
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        size = run_end - position
        closing = _find_closing_run(text, run_end, size)
        if closing is None:
            position = run_end
            continue
        spans.append(_Span(position, run_end, closing, closing + size))
        position = closing + size
    return spans


def _find_closing_run(text: str, start: int, size: int) -> int | None:
    position = start
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        if run_end - position == size:
            return position
        position = run_end
    return None


def _inside_quoted_sentence(prose: str) -> bool:
    """Whether `prose`, the paragraph's text before a span with its earlier spans blanked, has a
    double quote still open."""
    straight = prose.count('"')
    return (
        straight % 2 == 1
        or prose.count(OPENING_CURLY_QUOTE) > prose.count(CLOSING_CURLY_QUOTE)
    )


def _mask(text: str, start: int, end: int) -> str:
    blanked = "".join("\n" if character == "\n" else " " for character in text[start:end])
    return text[:start] + blanked + text[end:]


def _paragraph_findings(lines: list[tuple[int, str]]) -> list[int]:
    """Physical line numbers of the commands in the inline spans of one paragraph."""
    text = "\n".join(line for _, line in lines)
    line_starts = [0]
    for _, line in lines[:-1]:
        line_starts.append(line_starts[-1] + len(line) + 1)
    prose = text
    found: list[int] = []
    for span in _find_spans(text):
        prose = _mask(prose, span.start, span.end)
        content = text[span.content_start : span.content_end]
        offsets = [
            offset for offset, word_end in _command_tokens(content) if content[word_end:].strip()
        ]
        if not offsets or _inside_quoted_sentence(prose[: span.start]):
            continue
        for offset in offsets:
            line_index = bisect.bisect_right(line_starts, span.content_start + offset) - 1
            found.append(lines[line_index][0])
    return found


def _file_findings(relative_path: str, text: str) -> list[Finding]:
    all_lines = text.split("\n")
    flagged: set[int] = set()
    paragraph: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None

    def flush_paragraph() -> None:
        if paragraph:
            if _indent(paragraph[0][1]) >= INDENTED_CODE_COLUMNS:
                for number, text_line in paragraph:
                    flagged.update(_fenced_line_findings(number, text_line))
            flagged.update(_paragraph_findings(paragraph))
            paragraph.clear()

    for line_number, line in enumerate(all_lines, start=1):
        if fence is not None:
            marker, size = fence
            stripped = line.strip()
            if stripped.startswith(marker * size) and not stripped.strip(marker):
                fence = None
            else:
                flagged.update(_fenced_line_findings(line_number, line))
            continue
        opening = FENCE_OPEN.match(line)
        if opening:
            flush_paragraph()
            run = opening.group(1)
            fence = (run[0], len(run))
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph.append((line_number, line))
    flush_paragraph()
    return [Finding(relative_path, number, all_lines[number - 1]) for number in sorted(flagged)]


def scan_skills_tree(root: Path) -> list[Finding]:
    """Every line below `root` on which `python3` starts a command, by path and then line."""
    findings: list[Finding] = []
    for path in discover_instruction_files(root):
        relative = path.relative_to(root).as_posix()
        findings.extend(_file_findings(relative, path.read_text(encoding="utf-8")))
    return sorted(findings, key=lambda finding: (finding.path, finding.line))


def assert_commands_use_the_locked_runner(root: Path) -> None:
    """Fail with every command in the tree that starts `python3`; pass on none, empty tree too."""
    findings = scan_skills_tree(root)
    if findings:
        report = [f"{item.path}:{item.line}: {item.text}" for item in findings]
        raise AssertionError("\n".join([REPORT_HEADER, *report]))


def _write_tree(root: Path, files: dict[str, str]) -> Path:
    for relative, content in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def _skill(group: str, name: str, filename: str = SKILL_FILE) -> str:
    return f"{group}/.claude/skills/{name}/{filename}"


def _failure_lines(root: Path) -> list[str]:
    with pytest.raises(AssertionError) as raised:
        assert_commands_use_the_locked_runner(root)
    message = str(raised.value).split("\n")
    assert message[:2] == REPORT_HEADER.split("\n")
    return message[2:]


@pytest.mark.parametrize(
    ("group", "name"),
    [("pm", "shukuba-open"), ("tech-lead", "ad-hoc-plan"), ("fresh", "brand-new-skill")],
)
def test_fenced_agent_commands_are_reported(tmp_path, group, name):
    path = _skill(group, name)
    command = 'python3 "<CORE>/tools/commit_builder.py" --repo . commit'
    body = (
        "# Skill\n\nRun:\n\n"
        f"```bash\n{command} \\\n  --subject x\n```\n\n"
        "1. Step\n\n"
        "   ```sh\n"
        '   python3 "<CORE>/tools/a.py" \\\n'
        "     --flag\n"
        "   python3 <CORE>/tools/b.py --x\n"
        "   ```\n\n"
        "~~~\n"
        "  python3\n"
        "~~~\n"
    )
    _write_tree(tmp_path, {path: body})

    assert _failure_lines(tmp_path) == [
        f"{path}:6: {command} \\",
        f'{path}:13:    python3 "<CORE>/tools/a.py" \\',
        f"{path}:15:    python3 <CORE>/tools/b.py --x",
        f"{path}:19:   python3",
    ]


def test_indented_code_blocks_are_reported(tmp_path):
    path = _skill("tech-lead", "indented")
    body = (
        "Check first:\n\n"
        '    python3 <CORE>/tools/check_brief_quotes.py\n\n'
        "6. Read the brief. Otherwise run\n\n"
        "       python3 <CORE>/tools/other.py <brief>\n\n"
        "   It prints a line.\n\n"
        "  - nested item\n\n"
        "    A sentence that says `python3 y.py` in a nested paragraph.\n\n"
        "    Not a command: python3 is named only in this sentence.\n"
    )
    _write_tree(tmp_path, {path: body})

    assert _failure_lines(tmp_path) == [
        f'{path}:3:     python3 <CORE>/tools/check_brief_quotes.py',
        f"{path}:7:        python3 <CORE>/tools/other.py <brief>",
        f"{path}:13:     A sentence that says `python3 y.py` in a nested paragraph.",
    ]


@pytest.mark.parametrize(
    "line",
    [
        'x=$(python3 "<CORE>/tools/a.py")',
        'cd "$W" && python3 "<CORE>/tools/a.py"',
        'cat in | python3 "<CORE>/tools/a.py"',
        'PYTHONPATH=. python3 "<CORE>/tools/a.py"',
    ],
)
def test_a_command_after_a_separator_or_assignment_is_reported(tmp_path, line):
    path = _skill("pm", "any")
    _write_tree(tmp_path, {path: f"```bash\n{line}\n```\n"})

    assert _failure_lines(tmp_path) == [f"{path}:2: {line}"]


@pytest.mark.parametrize(
    "line",
    [
        'env python3 "<CORE>/tools/a.py"',
        'env PYTHONPATH=. python3 "<CORE>/tools/a.py"',
        'env -u KENSAIAPP_PIN python3 "<CORE>/tools/a.py"',
        '/usr/bin/env python3 "<CORE>/tools/a.py"',
        'nohup python3 "<CORE>/tools/a.py"',
        'command python3 "<CORE>/tools/a.py"',
        '"python3" "<CORE>/tools/a.py"',
        "'python3' <CORE>/tools/a.py",
    ],
)
def test_a_command_behind_a_wrapper_or_with_a_quoted_name_is_reported(tmp_path, line):
    path = _skill("pm", "wrapped")
    sentence = f"Run `{line}` once."
    _write_tree(tmp_path, {path: f"```bash\n{line}\n```\n\n{sentence}\n"})

    assert _failure_lines(tmp_path) == [f"{path}:2: {line}", f"{path}:5: {sentence}"]


@pytest.mark.parametrize(
    "line",
    [
        "command -v python3",
        "which python3",
        'found = shutil.which("python3")',
        'print("python3 is the interpreter")',
        "#!/usr/bin/env python3",
    ],
)
def test_a_lookup_or_a_string_naming_python3_passes(tmp_path, line):
    path = _skill("pm", "named")
    _write_tree(tmp_path, {path: f"```\n{line}\n```\n\nThe word `\"python3\"` alone.\n"})

    assert_commands_use_the_locked_runner(tmp_path)


@pytest.mark.parametrize(
    ("script", "form"),
    [
        ("scripts/open.py", "Run `python3 {script} --root .`"),
        ("tools/x.py", "`<drop>` is `python3 {script} --root .`."),
        ("scripts/q.py", 'Then run `python3 "{script}" --repo "<instance root>"` and report.'),
        ("scripts/w.py", 'Then run `python3\n  "{script}"` too.'),
        ("tools/c.py", 'Afterwards run\n`\npython3 "{script}"\n--repo .` and read it.'),
    ],
)
@pytest.mark.parametrize("filename", [SKILL_FILE, "prompts/step.md", "prompts/nested/deep.md"])
def test_inline_instructions_and_command_definitions_are_reported(
    tmp_path, script, form, filename
):
    path = _skill("scrum-master", "some-skill", filename)
    sentence = form.format(script=script)
    _write_tree(tmp_path, {path: f"Intro line.\n\n{sentence}\n"})
    if filename != SKILL_FILE:
        _write_tree(tmp_path, {_skill("scrum-master", "some-skill"): "# Skill\n"})
    sentence_lines = sentence.split("\n")
    token_index = next(i for i, text in enumerate(sentence_lines) if "python3" in text)

    assert _failure_lines(tmp_path) == [f"{path}:{3 + token_index}: {sentence_lines[token_index]}"]


def test_quoted_reader_prose_does_not_exempt_agent_commands(tmp_path):
    reader = _skill("content-editor", "sample-skill", "prompts/thin.md")
    moved = _skill("content-editor", "sample-skill")
    reworded = _skill("anything", "new-skill")
    command = 'Run `python3 "<CORE>/tools/x.py" --root .` yourself.'
    _write_tree(
        tmp_path,
        {
            reader: (
                'Write a clause, for example "You can start the tracker with `python3 main.py`".\n'
                "\n"
                "The reader sees\n\u201cStart it with `python3 run.py`\u201d, and nothing more.\n"
                "\n"
                f"{command}\n"
            ),
            moved: "# Skill\n",
            reworded: (
                "# Skill\n\n"
                'Say to the user: "Open a terminal, then `python3 -m http.server`."\n\n'
                'Or write it as: "Run the app with\n`python3 app.py --port 8000`".\n'
            ),
        },
    )

    assert _failure_lines(tmp_path) == [f"{reader}:6: {command}"]


def test_a_quote_inside_an_earlier_span_does_not_exempt_a_later_command(tmp_path):
    path = _skill("pm", "quoted-argument")
    sentence = 'Pass `--title "one` first, then run `python3 "<CORE>/tools/x.py"` once.'
    _write_tree(tmp_path, {path: f"{sentence}\n"})

    assert _failure_lines(tmp_path) == [f"{path}:1: {sentence}"]


def test_shebangs_converted_commands_and_noncommands_pass(tmp_path):
    path = _skill("pm", "tobiishi-seal")
    body = (
        "```python\n"
        "#!/usr/bin/env python3\n"
        "```\n\n"
        "```bash\n"
        '"<CORE>/tools/locked_python.sh" "<CORE>/tools/commit_builder.py" --repo .\n'
        "/usr/bin/python3 --version\n"
        "python3.15 script.py\n"
        "python3-config --includes\n"
        "mypython3 run\n"
        "# python3 in a comment\n"
        "echo python3 is a word here\n"
        "```\n\n"
        "Never run the bare `python3` yourself; `python3.15 x.py` is another program.\n"
        'Run `"<CORE>/tools/locked_python.sh" "<CORE>/tools/x.py"`, not python3 directly.\n'
    )
    _write_tree(tmp_path, {path: body})

    assert_commands_use_the_locked_runner(tmp_path)


def test_nested_and_textual_prompts_are_scanned(tmp_path):
    skill = _skill("pm", "fresh-skill")
    textual = _skill("pm", "fresh-skill", "prompts/deeper/still/ask.txt")
    nested_md = _skill("pm", "fresh-skill", "prompts/a/b.md")
    _write_tree(
        tmp_path,
        {
            skill: "# Skill\n",
            textual: "Run `python3 x.py`.\n",
            nested_md: "```sh\n  python3 y.py\n```\n",
        },
    )

    assert _failure_lines(tmp_path) == [
        f"{nested_md}:2:   python3 y.py",
        f"{textual}:1: Run `python3 x.py`.",
    ]


def test_references_templates_agents_and_scripts_are_out_of_scope(tmp_path):
    skill = _skill("pm", "a-skill")
    command = "```sh\npython3 x.py\n```\nRun `python3 x.py`.\n"
    _write_tree(
        tmp_path,
        {
            skill: "# Skill\n",
            _skill("pm", "a-skill", "references/guide.md"): command,
            _skill("pm", "a-skill", "templates/t.md"): command,
            _skill("pm", "a-skill", "scripts/run.sh"): "python3 x.py\n",
            _skill("pm", "a-skill", "scripts/run.py"): "# python3 x.py\n",
            "pm/.claude/agents/agent.md": command,
            "pm/.claude/prompts/not-a-skill-prompt.md": command,
            "README.md": command,
        },
    )

    assert scan_skills_tree(tmp_path) == []
    assert_commands_use_the_locked_runner(tmp_path)


def test_every_offending_line_is_reported(tmp_path):
    first = _skill("a-group", "alpha")
    second = _skill("b-group", "beta", "prompts/p.md")
    _write_tree(
        tmp_path,
        {
            first: "```sh\npython3 one.py\n\npython3 two.py\n```\nRun `python3 three.py`.\n",
            second: "x\n```\npython3 four.py\n```\n",
            _skill("b-group", "beta"): "# Beta\n",
        },
    )

    assert _failure_lines(tmp_path) == [
        f"{first}:2: python3 one.py",
        f"{first}:4: python3 two.py",
        f"{first}:6: Run `python3 three.py`.",
        f"{second}:3: python3 four.py",
    ]


def test_existing_empty_tree_passes(tmp_path):
    assert_commands_use_the_locked_runner(tmp_path)
    (tmp_path / "pm" / ".claude" / "skills" / "bare").mkdir(parents=True)
    assert_commands_use_the_locked_runner(tmp_path)


@pytest.mark.parametrize("failure", ["missing-root", "unreadable-file", "unsearchable-folder"])
def test_missing_or_unreadable_input_does_not_pass(tmp_path, failure):
    if failure == "missing-root":
        with pytest.raises(FileNotFoundError):
            assert_commands_use_the_locked_runner(tmp_path / "no-such-tree")
        return
    if os.geteuid() == 0:
        pytest.skip("root reads any file and lists any folder whatever its mode")
    _write_tree(tmp_path, {_skill("pm", "locked"): "# Skill\n"})
    folder = tmp_path / "pm" / ".claude" / "skills" / "locked"
    target = folder / SKILL_FILE if failure == "unreadable-file" else folder
    target.chmod(0o000)
    try:
        with pytest.raises(PermissionError):
            assert_commands_use_the_locked_runner(tmp_path)
    finally:
        target.chmod(0o644 if target.is_file() else 0o755)


def test_real_skills_commands_use_the_locked_runner():
    assert discover_instruction_files(SKILLS_ROOT), f"no instruction file found below {SKILLS_ROOT}"

    assert_commands_use_the_locked_runner(SKILLS_ROOT)
