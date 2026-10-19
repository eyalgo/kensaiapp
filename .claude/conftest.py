"""Pytest bootstrap for the skill-evals scripts.

Puts this directory (the `scripts` package's parent) on `sys.path` so the tests
import the package the same way the scripts do (`from scripts.utils import ...`),
regardless of pytest's import mode or the working directory it is launched from.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
