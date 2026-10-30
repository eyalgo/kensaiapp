"""One running tracker per saved-data location: the claim on the directory and its lifetime.

Realizes SRS NFR-3 and AC-16 for the persistence part (SDD § 3, seam SM-5). `LocationUse` takes an
exclusive, nonblocking `flock` on the location's directory itself, not on `tracker.json`, a PID
or a lock file, so nothing is added to the directory, the claim spans every save (a save replaces
`tracker.json` and leaves the directory as it was), and a path, a relative path and a symbolic link
to the same directory meet the same claim. The kernel releases the claim when the process ends,
which is why a killed tracker never blocks the next start (ADR-0009: one Unix path, no operating
system check).

Only the lock call's own contention result means another tracker (`LocationInUse`). A failure to
create, open or lock the directory proves nothing about another tracker, so entry then holds no
claim and says nothing: the start goes on exactly as it did before this lock existed.

Startup rollback removes an empty directory this attempt created, and only while the claim is held
and the directory is still the one the path names. A contender that opened the directory before
that removal would otherwise hold a lock on a directory that no longer has a name, and a tracker
served from there would not exclude a third start; it discards that claim and acquires against the
live path. After `mark_started` the created directory is kept, empty or not.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
from types import TracebackType
from typing import Self

from errors import AppError

# A claim is discarded and retried only when another start removed the directory under it. Each
# retry is caused by a different start's rollback, so the bound is never met by a working system.
ACQUISITION_ATTEMPT_LIMIT = 100


class LocationInUse(AppError):
    """Another running tracker holds the claim on the saved-data location."""


class LocationUse:
    """The claim on one saved-data location, from entering the context to leaving it.

    Construction acquires nothing. Entering raises `LocationInUse` for proven contention and
    otherwise returns the lifetime, holding the claim when it could be made. Leaving releases it
    and never suppresses the body's exception.
    """

    def __init__(self, location: Path) -> None:
        self._path = os.fspath(location)
        self._descriptor: int | None = None
        self._created = False
        self._started = False

    def __enter__(self) -> Self:
        try:
            self._acquire()
        except BaseException:
            self._unwind()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._unwind()

    def mark_started(self) -> None:
        """Record that the listener was created: a directory made for the claim is now kept."""
        self._started = True

    def _acquire(self) -> None:
        for _ in range(ACQUISITION_ATTEMPT_LIMIT):
            try:
                self._created = self._make_leaf()
                self._descriptor = os.open(self._path, os.O_RDONLY | os.O_DIRECTORY)
                self._lock()
                if self._is_live_path():
                    return
            except LocationInUse:
                # Never remove the directory of the start that holds it.
                self._created = False
                raise
            except OSError:
                self._unwind()
                return
            self._discard()

    def _make_leaf(self) -> bool:
        """Create the location when absent. True when this attempt made it."""
        try:
            os.mkdir(self._path)
        except FileExistsError:
            return False
        return True

    def _lock(self) -> None:
        assert self._descriptor is not None
        try:
            fcntl.flock(self._descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise LocationInUse(self._path) from error

    def _is_live_path(self) -> bool:
        """Whether the held directory is the one the path names now."""
        assert self._descriptor is not None
        try:
            live = os.stat(self._path)
        except FileNotFoundError:
            return False
        held = os.fstat(self._descriptor)
        return (held.st_dev, held.st_ino) == (live.st_dev, live.st_ino)

    def _discard(self) -> None:
        """Drop a claim on a directory another start removed, so the next attempt begins fresh."""
        self._release()
        self._created = False

    def _unwind(self) -> None:
        try:
            self._remove_own_empty_leaf()
        finally:
            self._release()

    def _remove_own_empty_leaf(self) -> None:
        """Failed start: remove the directory this attempt made if it is still empty and ours."""
        if not self._created or self._started:
            return
        try:
            if self._descriptor is None or self._is_live_path():
                os.rmdir(self._path)
        except OSError:
            return
        self._created = False

    def _release(self) -> None:
        if self._descriptor is not None:
            descriptor, self._descriptor = self._descriptor, None
            os.close(descriptor)
