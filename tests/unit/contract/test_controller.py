from dataclasses import FrozenInstanceError

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


def test_controller_result_factory_for_continuation() -> None:
    """ControllerResult.for_continuation must create a CONTINUE result with optional message."""

    default_result = contract.ControllerResult.for_continuation()
    assert default_result.action == contract.ControllerAction.CONTINUE
    assert default_result.message is None

    custom_result = contract.ControllerResult.for_continuation("In progress.")
    assert custom_result.action == contract.ControllerAction.CONTINUE
    assert custom_result.message == "In progress."


def test_controller_result_factory_for_termination() -> None:
    """ControllerResult.for_termination must create a TERMINATE result with optional message."""

    default_result = contract.ControllerResult.for_termination()
    assert default_result.action == contract.ControllerAction.TERMINATE
    assert default_result.message is None

    custom_result = contract.ControllerResult.for_termination("Goodbye!")
    assert custom_result.action == contract.ControllerAction.TERMINATE
    assert custom_result.message == "Goodbye!"
