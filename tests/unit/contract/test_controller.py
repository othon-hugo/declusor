from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from declusor import contract


def test_icontroller_request_is_abstract() -> None:
    """IControllerRequest cannot be instantiated directly without abstract implementations."""

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        contract.IControllerRequest()  # type: ignore[abstract]


def test_controller_action_enum_members() -> None:
    """ControllerAction must declare CONTINUE and TERMINATE members."""

    assert contract.ControllerAction.CONTINUE == "CONTINUE"
    assert contract.ControllerAction.TERMINATE == "TERMINATE"


def test_controller_result_defaults() -> None:
    """ControllerResult must default action to CONTINUE and message to None."""

    result = contract.ControllerResult()

    assert result.action == contract.ControllerAction.CONTINUE
    assert result.message is None


def test_controller_result_explicit_values() -> None:
    """ControllerResult must store provided action and message."""

    result = contract.ControllerResult(
        action=contract.ControllerAction.TERMINATE,
        message="Session closed.",
    )

    assert result.action == contract.ControllerAction.TERMINATE
    assert result.message == "Session closed."


def test_controller_result_is_immutable() -> None:
    """ControllerResult must be frozen and reject attribute mutation."""

    result = contract.ControllerResult()

    with pytest.raises(FrozenInstanceError):
        result.message = "mutated"  # type: ignore[misc]
