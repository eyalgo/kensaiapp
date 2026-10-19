"""The two contracts `application` depends on, stated as structural types (SDD § 3 SM-3, SM-7).

A class satisfies one by having the method, and inherits from neither (NFDR QC-3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from domain import TrackerState


class Saver(Protocol):
    """Saves the whole state, or raises. `persistence` satisfies it without inheriting from it."""

    def save(self, state: TrackerState) -> None: ...


class Clock(Protocol):
    """The source of the current instant, an aware UTC datetime."""

    def now(self) -> datetime: ...
