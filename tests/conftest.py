"""Pytest configuration and fixture registrations for Declusor test suites."""

from collections.abc import Generator

import pytest

from declusor.testing import doubles

pytest_plugins = ["declusor.testing.pytest_plugin"]


@pytest.fixture(autouse=True)
def reset_test_doubles() -> Generator[None, None, None]:
    """Ensure static test double state is cleanly reset before and after every test."""

    doubles.DummyPlugin.reset()
    yield
    doubles.DummyPlugin.reset()
