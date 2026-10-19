"""What counts as front matter when a manuscript's words are counted (SRS FR-2).

Front matter is, and is only:
    - the title page
    - a dedication
    - an epigraph placed before the first chapter
    - a table of contents

Anything after the first chapter heading is body text, whatever it is called.
"""

FRONT_MATTER = ("title page", "dedication", "epigraph", "table of contents")


def is_front_matter(section_title: str, before_first_chapter: bool) -> bool:
    """True when a section is excluded from the word count."""
    return before_first_chapter and section_title.strip().lower() in FRONT_MATTER
