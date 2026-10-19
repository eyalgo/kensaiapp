"""The price list's two views."""

from datetime import date


def _money(pence: int) -> str:
    return f"£{pence // 100}.{pence % 100:02d}"


def _date(day: date) -> str:
    return day.strftime("%d %b %Y")


def _pad(text: str, width: int) -> str:
    return text.ljust(width)


def list_page(items: list[tuple[str, int]]) -> str:
    """Return the price list, one item per line."""
    return "\n".join(f"{_pad(name, 20)}{_money(price)}" for name, price in items)


def detail_page(name: str, price: int, updated: date) -> str:
    """Return one item's detail."""
    return f"{name}\n{_money(price)}\nUpdated {_date(updated)}"
