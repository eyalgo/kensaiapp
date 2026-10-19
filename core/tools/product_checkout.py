"""The product checkout, read at a run's launch and again at its end — and what a difference
between the two means to a chain engine.

WHY THIS EXISTS
    A run that wrote into the product checkout and was not stopped there walked on until the
    seal's preflight in `deliver_change.py` refused it several steps later, with
    no way to tell which run had written what. `chain.py`, `chain_development.py` and
    `build_idea.py` each record a reading when they launch a run and compare it with a second
    one when that run's end reaches them, so the halt names the run. The reading and the
    comparison are the same for all three, which is why they live here once.

    It reads and never writes: nothing here cleans, repairs or touches the checkout. The engines
    are handed a `Checkout` and construct none; the one place a real one is built is each
    engine's own wiring function.

    The reading is `git status --porcelain --untracked-files=all`, one line per
    entry, a nested untracked folder listed file by file — run under `--no-optional-locks`, which
    changes no line it prints: a plain `git status` refreshes a stale index entry by rewriting
    `.git/index`, a write into the shared checkout under the lock a commit there also takes.
    Two readings are compared as sets of lines: a run is blamed only for a line the end reading
    holds and the launch reading did not.
    A path already dirty at launch that the run edits further keeps its line, and is not caught.

    Only the product's own folder is read (`-- .`, from the product path). A product inside the
    instance shares one checkout with every other project's product and with the journey, so a
    whole-repo reading blamed a run for another project's edit: tools' walk halted on 2026-10-07 for
    ` M products/tracker17/docs/CONTENT_open_issues.md`, written by tracker17's walk. A product that
    is its own repository is that repository's root, so `.` is the whole checkout, as before. The
    seal's own preflight still reads the whole checkout, and refuses only a staged entry or one on a
    path its merge writes.
"""

from __future__ import annotations

import subprocess

__version__ = "1.1.1"

# The key an engine records the launch reading under on a pending entry, so the fresh process a
# run's end starts can compare against it. One name for the three engines' state files.
CHECKOUT_BEFORE = "checkout_before"

# Past this many new entries the reason says how many more there are, so one unpacked fixture
# does not bury the reason in the owner's message.
ENTRY_CAP = 5


class Checkout:
    """The port: what a product checkout holds right now."""

    def entries(self, path: str) -> list[str] | None:
        """The lines `git -C <path> status --porcelain --untracked-files=all -- .` prints, in order,
        leading spaces kept — read without the index refresh that would write the checkout.
        `None` when `path` is empty, lies in no git work tree, or the command fails or cannot
        start — an unreadable checkout is not an empty one."""
        if not path:
            return None
        try:
            result = subprocess.run(
                ["git", "--no-optional-locks", "-C", path, "status", "--porcelain",
                 "--untracked-files=all", "--", "."],
                capture_output=True, text=True, check=False)
        except OSError:
            return None
        if result.returncode != 0:
            return None
        return result.stdout.splitlines()


def left_dirty(before: list[str] | None, after: list[str] | None, path: str) -> str | None:
    """The reason a run's end halts its engine, or `None` when it does not.

    `None` when nothing was recorded at launch (`before is None`) or when `after` holds no line
    `before` lacks. The unreadable reason when a list was recorded and `after` is `None`.
    Otherwise the dirty reason: the new lines in `after`'s order, at most `ENTRY_CAP`, then how
    many more."""
    if before is None:
        return None
    if after is None:
        return (f"the product checkout {path} could not be read with `git status --porcelain` "
                f"when the run ended, so whether it gained entries is not known")
    recorded = set(before)
    new = [line for line in after if line not in recorded]
    if not new:
        return None
    named = ", ".join(f"`{line}`" for line in new[:ENTRY_CAP])
    more = len(new) - ENTRY_CAP
    remainder = f", and {more} more" if more > 0 else ""
    return (f"`git status --porcelain` in the product checkout {path} shows entries it did not "
            f"show when the run launched: {named}{remainder}")
