"""Puts the project root on sys.path so a test can import its subject by module name.

The frame ships no build system and does not install the product itself, so a module at the project
root cannot be imported by package name without this shim.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
