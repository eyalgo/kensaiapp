# Changed from Anthropic's skill-creator (Apache-2.0, https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator); this file is not the original.
"""Shared utilities for skill-creator scripts."""

import json
import os
import subprocess
from pathlib import Path


def claude_text_call(prompt: str, model: str) -> str:
    """Generate text from Claude via the login-based ``claude -p`` subprocess.

    Runs ``claude -p --output-format json --model <model>`` under the user's
    Claude Code login, so no ``ANTHROPIC_API_KEY`` is needed. The prompt is
    passed on stdin rather than as a command-line argument: the improvement
    prompt bundles the full SKILL.md plus the history of prior attempts and can
    be many kilobytes, which would risk the operating system's argument-length
    limit if passed in ``argv``. Returns the assistant's final text — the CLI's
    single JSON ``result`` object — which is the login-based analog of
    ``client.messages.create(...).content[...].text``.

    Raises ``RuntimeError`` on a failed call (non-zero exit, empty output, or
    output that is not the expected JSON) so a broken call is loud rather than a
    silent empty description.
    """
    command = ["claude", "-p", "--output-format", "json", "--model", model]

    # Drop CLAUDECODE so `claude -p` can run nested inside a Claude Code session.
    # The guard exists for interactive-terminal conflicts; a subprocess is safe.
    # This mirrors run_eval.py's env handling.
    env = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}

    completed = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            f"`claude -p` exited with status {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )

    stdout = completed.stdout.strip()
    if not stdout:
        raise RuntimeError("`claude -p` produced no output")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"`claude -p` returned unparseable output: {error}"
        ) from error

    result = payload.get("result")
    if not result:
        raise RuntimeError(
            f"`claude -p` response has no 'result' text: {payload!r}"
        )

    return result


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content
