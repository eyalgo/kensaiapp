"""Cancelling a booked pickup (SRS FR-4)."""


def cancel_pickup(pickup, courier) -> None:
    """Mark the pickup cancelled and tell the courier. Refuses a collected pickup."""
    if pickup.status == "collected":
        raise ValueError("a collected pickup cannot be cancelled")
    pickup.status = "cancelled"
    courier.tell_cancelled(pickup.id)
