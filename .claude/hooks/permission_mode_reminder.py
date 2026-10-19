#!/usr/bin/env python3
"""UserPromptSubmit hook — permission-mode reminder.

When the user prompt mentions `--dangerously-skip-permissions` or close
variants, write an advisory paragraph to stdout. The harness surfaces
stdout from a UserPromptSubmit hook as additional context to the model.

Non-blocking, advisory only. Exit code 0 on every path including
malformed input. Stdlib-only imports.

Doctrine: ~/.claude/CLAUDE.md §Permission mode — acceptEdits is the standing
choice as of 2026-04-22; --dangerously-skip-permissions is off the
table on this unsandboxed laptop. Full doctrine: system/sandbox/DOCTRINE.md
(sandbox) and ~/.claude/CLAUDE.md §Permission mode (interactive).

Manual smoke test:
    echo '{"prompt": "let me try --dangerously-skip-permissions"}' \\
        | python3 .claude/hooks/permission_mode_reminder.py
"""

from __future__ import annotations

import json
import sys

__version__ = "1.0.1"

# Canonical trigger phrases per dev instruction
# architect/dev_instructions/perm_mode_hook_remediation.md §Tech-Lead-locked
# decisions #11. Substring match, case-insensitive. Do NOT broaden — every
# fire adds context tokens to a prompt the user did not flag, and any
# addition must be flag-shaped (literal flag name or hyphenated near-variant),
# not generic English.
TRIGGER_PHRASES = (
    "dangerously-skip-permissions",
    "dangerously skip permissions",
    "bypass-permissions",
)

REMINDER = (
    "## Permission-mode reminder\n"
    "\n"
    "The current prompt mentions a bypass-mode flag. Per ~/.claude/CLAUDE.md "
    "§Permission mode and the standing decision recorded on 2026-04-22, "
    "Claude Code on this laptop is launched with `--permission-mode "
    "acceptEdits` — never `--dangerously-skip-permissions`.\n"
    "\n"
    "Rationale: this laptop is not a sandboxed container/VM with "
    "restricted internet that can be easily restored if damaged, so the "
    "bypass-mode warning's preconditions are not met. Product accepts "
    "~1–3 Bash permission prompts per autonomous run as the price of "
    "retaining oversight of side effects. The accepted cost is by "
    "design and not negotiable per-run.\n"
    "\n"
    "Before proposing or executing `--dangerously-skip-permissions`, "
    "surface this standing choice explicitly and ask: has something "
    "changed?\n"
)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str):
        return 0
    lowered = prompt.lower()
    for phrase in TRIGGER_PHRASES:
        if phrase in lowered:
            sys.stdout.write(REMINDER)
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
