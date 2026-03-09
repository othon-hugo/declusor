"""Tests for the ``declusor.interface.prompt`` module."""

import pytest

from declusor.interface import prompt


# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyPrompt(prompt.IPrompt):
    """Null-implementation subclass delegating attributes to the interface."""

    def run(self) -> None:
        super().run()


# =============================================================================
# Tests: IPrompt (Interface contract)
# =============================================================================

def test_iprompt_methods_raise_not_implemented_error() -> None:
    """Calling the abstract loop execution on ``IPrompt`` must raise a ``NotImplementedError``."""

    # ARRANGE: Wrap in concrete class
    dummy = DummyPrompt()

    # ACT & ASSERT: Block execution defaulting to inheriting logic requirements
    with pytest.raises(NotImplementedError):
        dummy.run()
