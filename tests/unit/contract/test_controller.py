"""Unit tests for controller contracts and data structures."""

from dataclasses import FrozenInstanceError

import pytest

from declusor import contract


class TestControllerAction:
    """Tests for ControllerAction string enumeration."""

    def test_controller_action__enum_members__match_expected_string_values(self) -> None:
        """Verify ControllerAction enum members match expected string values."""

        from enum import StrEnum

        assert issubclass(contract.ControllerAction, StrEnum)
        assert contract.ControllerAction.CONTINUE.value == "CONTINUE"
        assert contract.ControllerAction.TERMINATE.value == "TERMINATE"
        assert len(contract.ControllerAction) == 2

    def test_controller_action__str_instance__is_subclass_and_instance_of_str(self) -> None:
        """Verify ControllerAction members are string instances."""

        assert isinstance(contract.ControllerAction.CONTINUE, str)
        assert isinstance(contract.ControllerAction.TERMINATE, str)


class TestControllerResult:
    """Tests for ControllerResult dataclass."""

    def test_controller_result__equality_and_factory_helpers__match_default_construction(self) -> None:
        """Verify factory classmethods create instances equal to explicit constructor calls."""

        assert contract.ControllerResult() == contract.ControllerResult.for_continuation()
        assert contract.ControllerResult(action=contract.ControllerAction.TERMINATE, message="Done") == contract.ControllerResult.for_termination(
            "Done"
        )

    def test_controller_result__default_instantiation__sets_default_action_and_none_message(self) -> None:
        """Verify ControllerResult defaults action to CONTINUE and message to None."""

        result = contract.ControllerResult()

        assert result.action == contract.ControllerAction.CONTINUE
        assert result.message is None

    def test_controller_result__explicit_arguments__preserves_provided_attributes(self) -> None:
        """Verify ControllerResult stores explicitly provided action and message."""

        result = contract.ControllerResult(
            action=contract.ControllerAction.TERMINATE,
            message="Session closed.",
        )

        assert result.action == contract.ControllerAction.TERMINATE
        assert result.message == "Session closed."

    def test_controller_result__attribute_mutation__raises_frozen_instance_error(self) -> None:
        """Verify ControllerResult is frozen and rejects attribute mutation."""

        result = contract.ControllerResult()

        with pytest.raises(FrozenInstanceError):
            result.message = "mutated"  # type: ignore[misc]

    def test_controller_result_for_continuation__without_message__returns_continue_with_none_message(self) -> None:
        """Verify for_continuation factory creates CONTINUE result with default None message."""

        result = contract.ControllerResult.for_continuation()

        assert result.action == contract.ControllerAction.CONTINUE
        assert result.message is None

    def test_controller_result_for_continuation__with_message__returns_continue_with_message(self) -> None:
        """Verify for_continuation factory creates CONTINUE result with provided message."""

        result = contract.ControllerResult.for_continuation("In progress.")

        assert result.action == contract.ControllerAction.CONTINUE
        assert result.message == "In progress."

    def test_controller_result_for_termination__without_message__returns_terminate_with_none_message(self) -> None:
        """Verify for_termination factory creates TERMINATE result with default None message."""

        result = contract.ControllerResult.for_termination()

        assert result.action == contract.ControllerAction.TERMINATE
        assert result.message is None

    def test_controller_result_for_termination__with_message__returns_terminate_with_message(self) -> None:
        """Verify for_termination factory creates TERMINATE result with provided message."""

        result = contract.ControllerResult.for_termination("Goodbye!")

        assert result.action == contract.ControllerAction.TERMINATE
        assert result.message == "Goodbye!"


class TestIControllerRequest:
    """Tests for IControllerRequest abstract base class."""

    def test_icontroller_request__direct_instantiation__raises_type_error(self) -> None:
        """Verify IControllerRequest cannot be instantiated directly."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IControllerRequest()  # type: ignore[abstract]

    def test_icontroller_request__concrete_subclass__satisfies_abstract_contract(self) -> None:
        """Verify concrete subclass implementing abstract members functions correctly."""

        class _ConcreteRequest(contract.IControllerRequest[contract.ControllerArguments]):
            """Concrete test double for IControllerRequest."""

            def __init__(self, line: str) -> None:
                self._line = line

            @property
            def request_line(self) -> str:
                return self._line

            def parse_arguments(
                self,
                definitions: contract.ArgumentDefinitions,
                allow_unknown: bool = False,
            ) -> tuple[contract.ControllerArguments, list[str]]:
                return {}, []

        request = _ConcreteRequest("status --verbose")

        assert request.request_line == "status --verbose"
        parsed, unknown = request.parse_arguments({})
        assert parsed == {}
        assert unknown == []


class TestControllerArguments:
    """Tests for ControllerArguments TypedDict."""

    def test_controller_arguments__subclass_instantiation__behaves_as_typed_dictionary(self) -> None:
        """Verify ControllerArguments subclass allows structured dictionary access."""

        class _SampleArguments(contract.ControllerArguments):
            query: str
            limit: int

        arguments: _SampleArguments = {"query": "SELECT 1", "limit": 10}

        assert arguments["query"] == "SELECT 1"
        assert arguments["limit"] == 10

    def test_controller_arguments__empty_instance__behaves_as_empty_dictionary(self) -> None:
        """Verify base ControllerArguments can be initialized as an empty dictionary."""

        arguments: contract.ControllerArguments = {}

        assert len(arguments) == 0
        assert dict(arguments) == {}
