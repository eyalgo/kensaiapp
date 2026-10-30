"""The saved data: its location, its file format, the read at start, the whole-state save and the claim.

`LocationUse` is the exclusive claim on the location while a tracker runs, and `LocationInUse` is
the signal that another tracker holds it.
"""

from persistence.location_use import LocationInUse, LocationUse
from persistence.saved_data import DEFAULT_LOCATION, SavedData, UnreadableData

__all__ = ["DEFAULT_LOCATION", "LocationInUse", "LocationUse", "SavedData", "UnreadableData"]
