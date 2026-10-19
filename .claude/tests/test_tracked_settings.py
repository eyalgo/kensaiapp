"""The tracked `.claude/settings.json` is the host's hook wiring and nothing else.

Permissions and the `worktree` setting are the machine owner's own and live in
`.claude/settings.local.json`; every pinned launch carries `worktree.bgIsolation` itself.
"""

import json
from pathlib import Path

TRACKED_SETTINGS = Path(__file__).resolve().parents[1] / "settings.json"


def test_the_tracked_settings_hold_only_the_hook_wiring():
    assert set(json.loads(TRACKED_SETTINGS.read_text())) == {"hooks"}
