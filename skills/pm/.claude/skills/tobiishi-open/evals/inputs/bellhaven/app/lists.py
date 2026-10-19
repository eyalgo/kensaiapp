"""A household's shopping lists."""

LISTS: dict[int, list[tuple[str, int]]] = {1: [("eggs", 12), ("flour", 1)]}


def items(list_id: int) -> list[tuple[str, int]]:
    """Return a list's items as (name, quantity) pairs."""
    return LISTS[list_id]
