"""One passing test, so a freshly stamped product's test gate proves something.

Without it `pytest` exits 5, `NO_TESTS_COLLECTED`, and the product fails a gate while working exactly
as intended. Making the empty case exit 0 would fix the exit code and prove nothing; this proves the
harness is wired — pytest found the product, read its `testpaths`, loaded `tests/conftest.py`'s
sys.path shim, and imported the product's own module through it.

Delete it once this product has a real test. It is scaffolding, not a test of the product.
"""

from __future__ import annotations

from errors import AppError


def test_the_harness_runs_and_can_import_the_product():
    assert issubclass(AppError, Exception)
