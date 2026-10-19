"""Closures drawn on the trail map (SRS FR-2, FR-3)."""


def closed_trail_ids(closures: list[dict]) -> set[str]:
    """Return the ids of trails with a posted closure that has not been lifted."""
    return {c["trail_id"] for c in closures if not c.get("lifted")}
