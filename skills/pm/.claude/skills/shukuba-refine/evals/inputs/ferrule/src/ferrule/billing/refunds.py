"""Refunds of the booking fee (SRS FR-5).

The booking-fee refund on cancellation is owed and unassigned — no change unit now owns it.
"""


def refund_due(fee_pence: int, minutes_before_window: int) -> int:
    """Return the refund owed for a cancellation made this many minutes before the window."""
    raise NotImplementedError("FR-5 refund is not built")
