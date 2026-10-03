"""Unit tests for the IView presentation contract and DummyView double."""

import inspect

import pytest

from declusor import contract
from declusor.testing import DummyView


class MinimalConcreteView(contract.IView):
    """Minimal concrete view delegating directly to abstract super methods."""

    def write_message(self, message: str, /) -> None:
        """Forward to abstract superclass."""

        super().write_message(message)  # type: ignore[safe-super]

    def write_error(self, message: str | BaseException, /) -> None:
        """Forward to abstract superclass."""

        super().write_error(message)  # type: ignore[safe-super]

    def write_warning(self, message: str | BaseException, /) -> None:
        """Forward to abstract superclass."""

        super().write_warning(message)  # type: ignore[safe-super]

    def write_info(self, message: str, /) -> None:
        """Forward to abstract superclass."""

        super().write_info(message)  # type: ignore[safe-super]

    def write_success(self, message: str, /) -> None:
        """Forward to abstract superclass."""

        super().write_success(message)  # type: ignore[safe-super]

    def write_binary_data(self, data: bytes, /) -> None:
        """Forward to abstract superclass."""

        super().write_binary_data(data)  # type: ignore[safe-super]


class TestIViewContract:
    """Tests verifying the IView abstract base class contract."""

    def test_iview_direct_instantiation__raises_type_error(self) -> None:
        """Verify IView cannot be instantiated directly as it is an abstract base class."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IView()  # type: ignore[abstract]

    def test_iview_abstract_methods__declares_all_required_output_contracts(self) -> None:
        """Verify IView declares the expected abstract methods for output presentation."""

        expected_methods = {
            "write_message",
            "write_error",
            "write_warning",
            "write_info",
            "write_success",
            "write_binary_data",
        }

        assert contract.IView.__abstractmethods__ == frozenset(expected_methods)

    def test_iview_subclass_missing_methods__cannot_be_instantiated(self) -> None:
        """Verify an incomplete subclass of IView fails instantiation."""

        class IncompleteView(contract.IView):
            def write_message(self, message: str, /) -> None:
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteView()  # type: ignore[abstract]

    def test_iview_super_calls__raise_not_implemented_error(self) -> None:
        """Verify abstract method default implementations raise NotImplementedError when called."""

        view = MinimalConcreteView()

        with pytest.raises(NotImplementedError):
            view.write_message("hello")

        with pytest.raises(NotImplementedError):
            view.write_error("error occurred")

        with pytest.raises(NotImplementedError):
            view.write_warning("warning occurred")

        with pytest.raises(NotImplementedError):
            view.write_info("informational note")

        with pytest.raises(NotImplementedError):
            view.write_success("success note")

        with pytest.raises(NotImplementedError):
            view.write_binary_data(b"\x00\x01")

    def test_iview_method_signatures__enforce_positional_only_contract(self) -> None:
        """Verify IView method signatures define positional-only parameters."""

        methods_to_param_name = {
            "write_message": "message",
            "write_error": "message",
            "write_warning": "message",
            "write_info": "message",
            "write_success": "message",
            "write_binary_data": "data",
        }

        for method_name, param_name in methods_to_param_name.items():
            func = getattr(contract.IView, method_name)
            sig = inspect.signature(func)
            param = sig.parameters[param_name]

            assert param.kind == inspect.Parameter.POSITIONAL_ONLY


class TestDummyViewContractConformance:
    """Tests verifying DummyView fulfills the IView contract with in-memory isolation."""

    def test_dummy_view_inheritance__implements_iview_interface(self) -> None:
        """Verify DummyView is a concrete subclass of IView."""

        view = DummyView()

        assert issubclass(DummyView, contract.IView)
        assert isinstance(view, contract.IView)

    def test_dummy_view_initial_state__collections_are_empty(self) -> None:
        """Verify DummyView starts with empty in-memory collections across all channels."""

        view = DummyView()

        assert view.messages == []
        assert view.errors == []
        assert view.warnings == []
        assert view.info_messages == []
        assert view.success_messages == []
        assert view.binary_data == []

    def test_write_message_valid_string__records_message_in_history(self) -> None:
        """Verify write_message captures strings in messages list."""

        view = DummyView()

        view.write_message("Session initiated")
        view.write_message("Ready for operator command")

        assert view.messages == ["Session initiated", "Ready for operator command"]

    def test_write_message_keyword_argument__raises_type_error(self) -> None:
        """Verify write_message enforces positional-only argument passing."""

        view = DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_message(message="Session initiated")  # type: ignore[call-arg]

    def test_write_error_string__records_error_string(self) -> None:
        """Verify write_error captures error strings in errors list."""

        view = DummyView()

        view.write_error("Connection refused by target host")

        assert view.errors == ["Connection refused by target host"]

    def test_write_error_exception_instance__records_exception_object(self) -> None:
        """Verify write_error captures BaseException instances directly in errors list."""

        view = DummyView()
        failure = ConnectionResetError("Connection reset by peer")

        view.write_error(failure)

        assert view.errors == [failure]

    def test_write_error_keyword_argument__raises_type_error(self) -> None:
        """Verify write_error enforces positional-only argument passing."""

        view = DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_error(message="Network timeout")  # type: ignore[call-arg]

    def test_write_warning_string__records_warning_string(self) -> None:
        """Verify write_warning captures warning strings in warnings list."""

        view = DummyView()

        view.write_warning("Session heartbeat overdue")

        assert view.warnings == ["Session heartbeat overdue"]

    def test_write_warning_exception_instance__records_exception_object(self) -> None:
        """Verify write_warning captures BaseException instances in warnings list."""

        view = DummyView()
        warning_exc = UserWarning("Deprecated protocol detected")

        view.write_warning(warning_exc)

        assert view.warnings == [warning_exc]

    def test_write_warning_keyword_argument__raises_type_error(self) -> None:
        """Verify write_warning enforces positional-only argument passing."""

        view = DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_warning(message="Heartbeat overdue")  # type: ignore[call-arg]

    def test_write_info_valid_string__records_info_message(self) -> None:
        """Verify write_info captures informational notices in info_messages list."""

        view = DummyView()

        view.write_info("Catalog cache refreshed")

        assert view.info_messages == ["Catalog cache refreshed"]

    def test_write_info_keyword_argument__raises_type_error(self) -> None:
        """Verify write_info enforces positional-only argument passing."""

        view = DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_info(message="Catalog cache refreshed")  # type: ignore[call-arg]

    def test_write_success_valid_string__records_success_message(self) -> None:
        """Verify write_success captures success notifications in success_messages list."""

        view = DummyView()

        view.write_success("Configuration applied cleanly")

        assert view.success_messages == ["Configuration applied cleanly"]

    def test_write_success_keyword_argument__raises_type_error(self) -> None:
        """Verify write_success enforces positional-only argument passing."""

        view = DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_success(message="Configuration applied cleanly")  # type: ignore[call-arg]

    def test_write_binary_data_valid_bytes__records_binary_payload(self) -> None:
        """Verify write_binary_data captures raw byte payloads in binary_data list."""

        view = DummyView()
        payload = b"\x7fELF\x02\x01\x01\x00"

        view.write_binary_data(payload)

        assert view.binary_data == [payload]

    def test_write_binary_data_keyword_argument__raises_type_error(self) -> None:
        """Verify write_binary_data enforces positional-only argument passing."""

        view = DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_binary_data(data=b"\x00\x01\x02")  # type: ignore[call-arg]

    def test_reset_populated_view__clears_all_captured_channels(self) -> None:
        """Verify reset clears all captured history across all presentation channels."""

        view = DummyView()
        view.write_message("msg")
        view.write_error("err")
        view.write_warning("warn")
        view.write_info("info")
        view.write_success("ok")
        view.write_binary_data(b"\xaa\xbb")

        view.reset()

        assert view.messages == []
        assert view.errors == []
        assert view.warnings == []
        assert view.info_messages == []
        assert view.success_messages == []
        assert view.binary_data == []
