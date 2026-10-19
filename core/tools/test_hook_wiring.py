"""Contract tests for `hook_wiring.py` — the one rewrite of the live hooks prefix."""

from __future__ import annotations

import copy
from pathlib import Path

import hook_wiring

HOOKS_DIR = Path("/somewhere/host/.claude/hooks")


def test_the_prefix_is_replaced_inside_a_hook_command():
    document = {"command": 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py"'}

    rewritten = hook_wiring.rewrite_hooks_dir(document, HOOKS_DIR)

    assert rewritten == {"command": 'python3 "/somewhere/host/.claude/hooks/x.py"'}


def test_the_prefix_is_replaced_at_any_depth():
    command = 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py"'
    document = {"a": [{"b": [{"c": {"command": command}}, [command]]}]}

    rewritten = hook_wiring.rewrite_hooks_dir(document, HOOKS_DIR)

    expected = 'python3 "/somewhere/host/.claude/hooks/x.py"'
    assert rewritten == {"a": [{"b": [{"c": {"command": expected}}, [expected]]}]}


def test_every_occurrence_inside_one_string_is_replaced():
    live = "${CLAUDE_PROJECT_DIR}/.claude/hooks/"
    document = f"{live}a.py && {live}b.py"

    rewritten = hook_wiring.rewrite_hooks_dir(document, HOOKS_DIR)

    assert rewritten == "/somewhere/host/.claude/hooks/a.py && /somewhere/host/.claude/hooks/b.py"


def test_another_project_dir_reference_is_left_alone():
    document = {"command": "cat ${CLAUDE_PROJECT_DIR}/system/x"}

    assert hook_wiring.rewrite_hooks_dir(document, HOOKS_DIR) == document


def test_non_string_values_and_keys_are_untouched():
    document = {
        "number": 3,
        "float": 1.5,
        "yes": True,
        "no": False,
        "nothing": None,
        "${CLAUDE_PROJECT_DIR}/.claude/hooks/key": 1,
    }

    assert hook_wiring.rewrite_hooks_dir(document, HOOKS_DIR) == document


def test_the_document_passed_in_is_not_mutated():
    document = {"hooks": [{"command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.py"}]}
    before = copy.deepcopy(document)

    hook_wiring.rewrite_hooks_dir(document, HOOKS_DIR)

    assert document == before


def test_the_prefix_constant_is_the_live_hooks_directory():
    assert hook_wiring.LIVE_HOOKS_PREFIX == "${CLAUDE_PROJECT_DIR}/.claude/hooks/"
