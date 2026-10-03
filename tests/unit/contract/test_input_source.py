"""Unit tests for the IInputSource contract and DummyInputSource double."""

import inspect

import pytest

from declusor import contract
from declusor.testing import DummyInputSource


class MinimalConcreteInputSource(contract.IInputSource):
    """Minimal concrete input source delegating directly to abstract super methods."""

    def read_command(self, prompt: str = "", /) -> str:
        """Forward to abstract superclass."""

        return super().read_command(prompt)  # type: ignore[safe-super]

    def read_raw(self, prompt: str = "", /) -> str:
        """Forward to abstract superclass."""

        return super().read_raw(prompt)  # type: ignore[safe-super]


class TestIInputSourceContract:
    """Tests verifying the IInputSource abstract base class contract."""

    def test_iinput_source_direct_instantiation__raises_type_error(self) -> None:
        """Verify IInputSource cannot be instantiated directly as it is an abstract base class."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IInputSource()  # type: ignore[abstract]

    def test_iinput_source_abstract_methods__declares_all_required_input_contracts(self) -> None:
        """Verify IInputSource declares the expected abstract methods for reading operator input."""

        expected_methods = {"read_command", "read_raw"}

        assert contract.IInputSource.__abstractmethods__ == frozenset(expected_methods)

    def test_iinput_source_subclass_missing_methods__cannot_be_instantiated(self) -> None:
        """Verify an incomplete subclass of IInputSource fails instantiation."""

        class IncompleteInputSource(contract.IInputSource):
            def read_command(self, prompt: str = "", /) -> str:
                return "cmd"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteInputSource()  # type: ignore[abstract]

    def test_iinput_source_super_calls__raise_not_implemented_error(self) -> None:
        """Verify abstract method default implementations raise NotImplementedError when called."""

        source = MinimalConcreteInputSource()

        with pytest.raises(NotImplementedError):
            source.read_command()

        with pytest.raises(NotImplementedError):
            source.read_raw()

    def test_iinput_source_method_signatures__enforce_positional_only_contract(self) -> None:
        """Verify IInputSource method signatures define positional-only parameters with empty default."""

        for method_name in ("read_command", "read_raw"):
            func = getattr(contract.IInputSource, method_name)
            sig = inspect.signature(func)
            param = sig.parameters["prompt"]

            assert param.kind == inspect.Parameter.POSITIONAL_ONLY
            assert param.default == ""


class TestDummyInputSourceContractConformance:
    """Tests verifying DummyInputSource fulfills the IInputSource contract."""

    def test_dummy_input_source_inheritance__implements_iinput_source_interface(self) -> None:
        """Verify DummyInputSource is a concrete subclass of IInputSource."""

        source = DummyInputSource()

        assert issubclass(DummyInputSource, contract.IInputSource)
        assert isinstance(source, contract.IInputSource)

    def test_dummy_input_source_initial_state__queue_and_prompts_are_empty(self) -> None:
        """Verify DummyInputSource defaults to an empty queue and empty prompts list."""

        source = DummyInputSource()

        assert source.prompts == []
        assert source.input_exception is None

    def test_dummy_input_source_constructor_with_inputs__enqueues_initial_lines(self) -> None:
        """Verify DummyInputSource initializes its queue with provided sequence."""

        source = DummyInputSource(["first_command", "second_command"])

        assert source.read_command() == "first_command"
        assert source.read_command() == "second_command"

    def test_feed_inputs_additional_lines__appends_lines_to_queue(self) -> None:
        """Verify feed_inputs dynamically appends lines to the simulated input queue."""

        source = DummyInputSource()

        source.feed_inputs("help", "exit")

        assert source.read_command() == "help"
        assert source.read_command() == "exit"

    def test_read_command_default_empty_prompt__records_empty_string_prompt(self) -> None:
        """Verify read_command defaults prompt to empty string and records it."""

        source = DummyInputSource(["run_task"])

        result = source.read_command()

        assert result == "run_task"
        assert source.prompts == [""]

    def test_read_command_custom_prompt__records_prompt_verbatim(self) -> None:
        """Verify read_command accepts and records custom prompt string."""

        source = DummyInputSource(["status"])

        result = source.read_command("declusor> ")

        assert result == "status"
        assert source.prompts == ["declusor> "]

    def test_read_command_unstripped_input__returns_stripped_command_string(self) -> None:
        """Verify read_command strips leading and trailing whitespace from input."""

        source = DummyInputSource(["   start --verbose   \n\t"])

        result = source.read_command()

        assert result == "start --verbose"

    def test_read_command_empty_queue__returns_empty_string(self) -> None:
        """Verify read_command returns empty string when simulated input queue is exhausted."""

        source = DummyInputSource()

        result = source.read_command()

        assert result == ""

    def test_read_command_keyword_argument__raises_type_error(self) -> None:
        """Verify read_command enforces positional-only argument passing."""

        source = DummyInputSource(["exit"])

        with pytest.raises(TypeError, match="positional-only"):
            source.read_command(prompt="declusor> ")  # type: ignore[call-arg]

    def test_read_raw_default_empty_prompt__records_empty_string_prompt(self) -> None:
        """Verify read_raw defaults prompt to empty string and records it."""

        source = DummyInputSource(["raw line\n"])

        result = source.read_raw()

        assert result == "raw line\n"
        assert source.prompts == [""]

    def test_read_raw_custom_prompt__records_prompt_verbatim(self) -> None:
        """Verify read_raw accepts and records custom prompt string."""

        source = DummyInputSource(["raw line\n"])

        result = source.read_raw("enter> ")

        assert result == "raw line\n"
        assert source.prompts == ["enter> "]

    def test_read_raw_input_without_newline__appends_newline_to_raw_string(self) -> None:
        """Verify read_raw ensures returned raw line terminates with a newline."""

        source = DummyInputSource(["line without newline"])

        result = source.read_raw()

        assert result == "line without newline\n"

    def test_read_raw_input_with_existing_newline__preserves_verbatim(self) -> None:
        """Verify read_raw preserves single trailing newline without appending an extra one."""

        source = DummyInputSource(["already newline\n"])

        result = source.read_raw()

        assert result == "already newline\n"

    def test_read_raw_empty_queue__returns_single_newline(self) -> None:
        """Verify read_raw returns a single newline when simulated input queue is exhausted."""

        source = DummyInputSource()

        result = source.read_raw()

        assert result == "\n"

    def test_read_raw_keyword_argument__raises_type_error(self) -> None:
        """Verify read_raw enforces positional-only argument passing."""

        source = DummyInputSource(["raw\n"])

        with pytest.raises(TypeError, match="positional-only"):
            source.read_raw(prompt="enter> ")  # type: ignore[call-arg]

    def test_read_command_injected_exception__raises_and_clears_exception(self) -> None:
        """Verify read_command raises injected input_exception and resets it to None."""

        source = DummyInputSource(["subsequent_command"])
        source.input_exception = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            source.read_command()

        assert source.input_exception is None
        assert source.read_command() == "subsequent_command"

    def test_read_raw_injected_exception__raises_and_clears_exception(self) -> None:
        """Verify read_raw raises injected input_exception and resets it to None."""

        source = DummyInputSource(["subsequent_raw\n"])
        source.input_exception = EOFError("Console stream closed")

        with pytest.raises(EOFError, match="Console stream closed"):
            source.read_raw()

        assert source.input_exception is None
        assert source.read_raw() == "subsequent_raw\n"
