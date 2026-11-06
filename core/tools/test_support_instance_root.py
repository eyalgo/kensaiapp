"""What every kensaiapp instance root carries for its pinned Python, for a test's own root.

`locked_python.sh` runs the Python an instance pins from the instance root's `pyproject.toml`, and
refuses a root that holds none. A real instance and a real pin carry the three files below; a root
a test builds stands for one, so it carries them too — copied from this repository, where they are
committed, never read from the machine.
"""

from __future__ import annotations

import shutil
from pathlib import Path

_INSTANCE = Path(__file__).resolve().parents[2]
PYTHON_FILES = ("pyproject.toml", ".python-version", "uv.lock")


def give_python(root: Path) -> Path:
    """`root`, holding this repository's `pyproject.toml`, `.python-version` and `uv.lock`."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for name in PYTHON_FILES:
        shutil.copy2(_INSTANCE / name, root / name)
    return root
