"""Render each page's body."""


def render_welcome(name: str) -> str:
    """Return the welcome page's HTML."""
    return f"<h1>Welcome, {name}</h1>"


def render_goodbye() -> str:
    """Return the goodbye page's HTML."""
    return "<h1>Goodbye</h1>"
