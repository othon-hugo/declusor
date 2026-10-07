"""Unit tests for the plugin contract interfaces and delivery envelopes."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from declusor import config, contract, testing


class TestPluginConfig:
    """Tests for PluginConfig."""

    def test_plugin_config_mutation__reassign_attribute__raises_frozen_instance_error(self, tmp_path: Path) -> None:
        """Verify PluginConfig is frozen and rejects attribute reassignment."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind="dummy",
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        with pytest.raises(FrozenInstanceError):
            plugin_config.host = "10.0.0.1"  # type: ignore[misc]

    def test_plugin_config_init__default_fields__populates_expected_defaults(self, tmp_path: Path) -> None:
        """Verify PluginConfig assigns default values for optional fields."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind="dummy",
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        assert plugin_config.kind == "dummy"
        assert plugin_config.host == "127.0.0.1"
        assert plugin_config.port == 9000
        assert plugin_config.filesystem == fs
        assert plugin_config.mode == config.DEFAULT_EXECUTION_MODE
        assert plugin_config.mode == config.ExecutionMode.CLI
        assert plugin_config.timeout is None
        assert plugin_config.launcher_output_mode == config.DEFAULT_LAUNCHER_OUTPUT_MODE
        assert plugin_config.launcher_output_mode == config.LauncherOutputMode.TERMINAL
        assert plugin_config.launcher_output_path is None
        assert plugin_config.launcher_wrapper is None
        assert plugin_config.transport_layers == ()

    def test_plugin_config_init__custom_values__stores_all_provided_attributes(self, tmp_path: Path) -> None:
        """Verify PluginConfig stores custom values for all configurable fields."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        output_path = tmp_path / "custom_launcher.sh"
        plugin_config = contract.PluginConfig(
            kind="custom_plugin",
            host="10.0.0.1",
            port=8443,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            mode=config.ExecutionMode.API,
            timeout=10.5,
            launcher_output_mode=config.LauncherOutputMode.FILE,
            launcher_output_path=output_path,
            launcher_wrapper="python3 -c '$DECLUSOR_SCRIPT'",
            transport_layers=("xor", "base64"),
        )

        assert plugin_config.kind == "custom_plugin"
        assert plugin_config.host == "10.0.0.1"
        assert plugin_config.port == 8443
        assert plugin_config.filesystem == fs
        assert plugin_config.mode == config.ExecutionMode.API
        assert plugin_config.timeout == 10.5
        assert plugin_config.launcher_output_mode == config.LauncherOutputMode.FILE
        assert plugin_config.launcher_output_path == output_path
        assert plugin_config.launcher_wrapper == "python3 -c '$DECLUSOR_SCRIPT'"
        assert plugin_config.transport_layers == ("xor", "base64")


class TestLauncherDelivery:
    """Tests for LauncherDelivery."""

    def test_launcher_delivery_mutation__reassign_script__raises_frozen_instance_error(self) -> None:
        """Verify LauncherDelivery is frozen and rejects attribute reassignment."""

        delivery = contract.LauncherDelivery(script=b"echo original")

        with pytest.raises(FrozenInstanceError):
            delivery.script = b"echo mutated"  # type: ignore[misc]

    def test_launcher_delivery_init__default_fields__populates_expected_defaults(self) -> None:
        """Verify LauncherDelivery assigns expected defaults for output options."""

        delivery = contract.LauncherDelivery(script=b"echo hello")

        assert delivery.script == b"echo hello"
        assert delivery.output_mode == config.DEFAULT_LAUNCHER_OUTPUT_MODE
        assert delivery.output_mode == config.LauncherOutputMode.TERMINAL
        assert delivery.output_path is None
        assert delivery.wrapper_template is None

    def test_launcher_delivery_text_and_str__utf8_script_bytes__decodes_to_string(self) -> None:
        """Verify LauncherDelivery decodes UTF-8 script bytes via text property and str representation."""

        delivery = contract.LauncherDelivery(script=b"echo 'decoded utf8'")

        assert delivery.text == "echo 'decoded utf8'"
        assert str(delivery) == "echo 'decoded utf8'"

    def test_launcher_delivery_init__custom_wrapper_template__stores_template_string(self) -> None:
        """Verify LauncherDelivery stores optional wrapper template string."""

        template = "python3 -c '$DECLUSOR_SCRIPT'"
        delivery = contract.LauncherDelivery(script=b"payload", wrapper_template=template)

        assert delivery.wrapper_template == template

    def test_launcher_delivery_wrapped_text__with_wrapper_template__substitutes_script(self) -> None:
        """Verify wrapped_text formats script payload into wrapper_template."""

        delivery = contract.LauncherDelivery(
            script=b"print('hello')",
            wrapper_template="python3 -c '$DECLUSOR_SCRIPT'",
        )

        assert delivery.wrapped_text == "python3 -c 'print('hello')'"
        assert str(delivery) == delivery.wrapped_text

    def test_launcher_delivery_wrapped_text__without_wrapper_template__returns_raw_text(self) -> None:
        """Verify wrapped_text returns raw text unchanged when wrapper_template is None."""

        delivery = contract.LauncherDelivery(script=b"echo raw")

        assert delivery.wrapped_text == "echo raw"
        assert str(delivery) == "echo raw"

    def test_launcher_delivery_file_mode__with_output_path__instantiates_successfully(self, tmp_path: Path) -> None:
        """Verify LauncherDelivery allows FILE mode when output_path is provided."""

        target_file = tmp_path / "launcher.sh"
        delivery = contract.LauncherDelivery(
            script=b"echo hello",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=target_file,
        )

        assert delivery.output_mode == config.LauncherOutputMode.FILE
        assert delivery.output_path == target_file

    def test_launcher_delivery_file_mode__without_output_path__raises_launcher_delivery_error(self) -> None:
        """Verify LauncherDelivery rejects FILE mode when output_path is None."""

        with pytest.raises(config.LauncherDeliveryError, match="output_path must be set when output_mode is FILE"):
            contract.LauncherDelivery(
                script=b"echo hello",
                output_mode=config.LauncherOutputMode.FILE,
                output_path=None,
            )

    def test_launcher_delivery_non_file_mode__with_output_path__raises_launcher_delivery_error(self, tmp_path: Path) -> None:
        """Verify LauncherDelivery rejects output_path when output_mode is not FILE."""

        with pytest.raises(config.LauncherDeliveryError, match="output_path is only valid when output_mode is FILE") as exc_info:
            contract.LauncherDelivery(
                script=b"echo hello",
                output_mode=config.LauncherOutputMode.TERMINAL,
                output_path=tmp_path / "out.sh",
            )

        assert exc_info.value.output_path == tmp_path / "out.sh"


class TestIPluginExtension:
    """Tests for IPluginExtension interface."""

    def test_iplugin_extension_instantiation__direct_call__raises_type_error(self) -> None:
        """Verify IPluginExtension cannot be instantiated directly."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IPluginExtension()  # type: ignore[abstract]

    def test_iplugin_extension_abstract_methods__defined_on_interface__matches_expected_set(self) -> None:
        """Verify IPluginExtension declares all required abstract classmethods."""

        expected_abstract_methods = {
            "configure_parser",
            "extract_options",
            "validate",
            "build_config",
            "build_runtime",
        }

        assert contract.IPluginExtension.__abstractmethods__ == expected_abstract_methods

    def test_iplugin_extension_subclass__missing_abstract_methods__raises_type_error_on_instantiation(self) -> None:
        """Verify incomplete subclass of IPluginExtension cannot be instantiated."""

        class IncompletePluginExtension(contract.IPluginExtension[contract.ParsedArguments]):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompletePluginExtension()  # type: ignore[abstract]

    def test_iplugin_extension_concrete_double__implements_all_methods__can_be_instantiated(self) -> None:
        """Verify DummyPlugin implements all abstract methods of IPluginExtension."""

        assert issubclass(testing.DummyPlugin, contract.IPluginExtension)
        assert not testing.DummyPlugin.__abstractmethods__

        instance = testing.DummyPlugin()
        assert isinstance(instance, contract.IPluginExtension)
        assert instance.routes == testing.DummyPlugin.routes


class TestIPluginRuntime:
    """Tests for IPluginRuntime interface."""

    def test_iplugin_runtime_instantiation__direct_call__raises_type_error(self) -> None:
        """Verify IPluginRuntime cannot be instantiated directly."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IPluginRuntime()  # type: ignore[abstract]

    def test_iplugin_runtime_abstract_methods__defined_on_interface__matches_expected_set(self) -> None:
        """Verify IPluginRuntime declares all required abstract methods and properties."""

        expected_abstract_methods = {
            "processor",
            "launcher",
            "create_connection",
        }

        assert contract.IPluginRuntime.__abstractmethods__ == expected_abstract_methods

    def test_iplugin_runtime_subclass__missing_abstract_methods__raises_type_error_on_instantiation(self) -> None:
        """Verify incomplete subclass of IPluginRuntime cannot be instantiated."""

        class IncompletePluginRuntime(contract.IPluginRuntime):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompletePluginRuntime()  # type: ignore[abstract]

    def test_iplugin_runtime_concrete_double__implements_all_methods__can_be_instantiated(self) -> None:
        """Verify DummyPluginRuntime implements all abstract methods of IPluginRuntime."""

        runtime = testing.DummyPluginRuntime()

        assert isinstance(runtime, contract.IPluginRuntime)
        assert isinstance(runtime.processor, contract.IPluginProcessor)
        assert isinstance(runtime.launcher, contract.LauncherDelivery)


class TestIPluginProcessor:
    """Tests for IPluginProcessor interface."""

    def test_iplugin_processor_instantiation__direct_call__raises_type_error(self) -> None:
        """Verify IPluginProcessor cannot be instantiated directly."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IPluginProcessor()  # type: ignore[abstract]

    def test_iplugin_processor_abstract_methods__defined_on_interface__matches_expected_set(self) -> None:
        """Verify IPluginProcessor declares all required abstract methods and properties."""

        expected_abstract_methods = {
            "filesystem",
            "load_all_helpers",
            "find_module",
            "find_helper",
            "load_module",
            "load_helper",
            "render_launcher",
        }

        assert contract.IPluginProcessor.__abstractmethods__ == expected_abstract_methods

    def test_iplugin_processor_subclass__missing_abstract_methods__raises_type_error_on_instantiation(self) -> None:
        """Verify incomplete subclass of IPluginProcessor cannot be instantiated."""

        class IncompletePluginProcessor(contract.IPluginProcessor):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompletePluginProcessor()  # type: ignore[abstract]

    def test_iplugin_processor_concrete_double__implements_all_methods__can_be_instantiated(self) -> None:
        """Verify DummyPluginFileStore implements all abstract methods of IPluginProcessor."""

        processor = testing.DummyPluginFileStore()

        assert isinstance(processor, contract.IPluginProcessor)
        assert isinstance(processor.filesystem, contract.PluginFilesystem)
