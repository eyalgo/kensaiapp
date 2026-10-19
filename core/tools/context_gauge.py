"""context_gauge.py — how large a run's context is right now.

WHY THIS EXISTS
    A hook that tells a developer run to pause past a cap needs one number: the size of the
    context the run's latest request carried. `run_usage.py` sums a run's spend per class over the
    whole transcript, which is the wrong figure for this — the cache classes repeat on every
    request, so a sum over responses counts the same context once per turn. The current context is
    the **last** response's `input_tokens + cache_read_input_tokens +
    cache_creation_input_tokens`, and nothing else. `output_tokens` is what the response produced,
    not what it was given, so it is left out.

    The de-duplication per `message.id` and the tolerance of a half-written final line are
    `run_usage.usage_records`'s, reused rather than restated: a transcript is read while its own
    run is still writing to it.

    **stdlib-only, on purpose.** A hook imports this module, and a hook that needs an installed
    package fails in a satellite that has none.
"""

from __future__ import annotations

from pathlib import Path

import run_usage

__version__ = "1.0.0"

_CONTEXT_CLASSES = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def current_context(path: Path, files: run_usage.Files) -> int | None:
    """The three input classes of the newest API response in `path`, summed, or `None` when the
    transcript is unreadable or holds no assistant usage.

    A class the response does not carry counts as 0, so a response that never wrote the cache
    still gives a number rather than hiding the ones it did carry.
    """
    latest_usage = None
    for usage, _model, _timestamp in run_usage.usage_records(path, files):
        latest_usage = usage
    if latest_usage is None:
        return None
    return sum(latest_usage.get(name) or 0 for name in _CONTEXT_CLASSES)
