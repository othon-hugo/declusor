"""Tests for the ``declusor.interface.parser`` module."""

import pytest

from declusor.interface import parser


# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyParser(parser.IParser[dict[str, str]]):
    """Null-implementation subclass delegating attributes to the interface."""

    def parse(self) -> dict[str, str]:
        return super().parse()


# =============================================================================
# Tests: IParser (Interface contract)
# =============================================================================

def test_iparser_methods_raise_not_implemented_error() -> None:
    """Calling the abstract parsing method on ``IParser`` must raise a ``NotImplementedError``."""

    # ARRANGE: Mock parser wrapper
    dummy = DummyParser()

    # ACT & ASSERT: Ensure the abstract method fails correctly defaulting to explicit implementations
    with pytest.raises(NotImplementedError):
        dummy.parse()
