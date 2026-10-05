"""Unit tests for PluginRegistry in declusor.core.plugin."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from declusor import config, contract, core, testing


class _FirstSampleConfig(contract.ParsedArguments, total=False):
    pass


class _FirstSamplePlugin(contract.IPluginExtension[_FirstSampleConfig]):
    name = "alpha_plugin"
    description = "Alpha plugin for unit tests"
    options_type = _FirstSampleConfig
    supported_controllers = frozenset()

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> _FirstSampleConfig:
        return _FirstSampleConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: _FirstSampleConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[_FirstSampleConfig]:
        dummy_fs = contract.PluginFilesystem(
            root=Path("."),
            assets=Path("."),
            launchers=Path("."),
            modules=Path("."),
            helpers=Path("."),
        )
        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            options=options,
            options_type=cls.options_type,
            filesystem=filesystem or dummy_fs,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[_FirstSampleConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[_FirstSampleConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


class _SecondSampleConfig(contract.ParsedArguments, total=False):
    pass


class _SecondSamplePlugin(contract.IPluginExtension[_SecondSampleConfig]):
    name = "beta_plugin"
    description = "Beta plugin for unit tests"
    options_type = _SecondSampleConfig
    supported_controllers = frozenset()

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> _SecondSampleConfig:
        return _SecondSampleConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: _SecondSampleConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[_SecondSampleConfig]:
        dummy_fs = contract.PluginFilesystem(
            root=Path("."),
            assets=Path("."),
            launchers=Path("."),
            modules=Path("."),
            helpers=Path("."),
        )
        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            options=options,
            options_type=cls.options_type,
            filesystem=filesystem or dummy_fs,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[_SecondSampleConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[_SecondSampleConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


class TestPluginRegistry:
    """Tests verifying registration and lookup invariants on PluginRegistry."""

    def test_plugin_registry__register_and_get__stores_and_retrieves_registered_plugin(self) -> None:
        """Registering a plugin allows retrieving it by its unique name identifier."""

        registry = core.PluginRegistry()

        registry.register(_FirstSamplePlugin)

        assert registry.get("alpha_plugin") is _FirstSamplePlugin

    def test_plugin_registry__register_duplicate_name__raises_value_error(self) -> None:
        """Registering a duplicate plugin name raises ValueError."""

        registry = core.PluginRegistry()
        registry.register(_FirstSamplePlugin)

        with pytest.raises(ValueError, match="Client already registered: alpha_plugin"):
            registry.register(_FirstSamplePlugin)

    def test_plugin_registry__get_unregistered_name__raises_plugin_not_found_error_with_available_plugins(self) -> None:
        """Retrieving an unregistered name raises PluginNotFoundError with available plugin names."""

        registry = core.PluginRegistry()
        registry.register(_FirstSamplePlugin)

        with pytest.raises(config.PluginNotFoundError) as exc_info:
            registry.get("unknown_plugin")

        assert exc_info.value.plugin_name == "unknown_plugin"
        assert exc_info.value.available_plugins == ("alpha_plugin",)

    def test_plugin_registry__get_from_empty_registry__raises_plugin_not_found_error_with_empty_available_tuple(self) -> None:
        """Querying an empty registry raises PluginNotFoundError with empty available_plugins tuple."""

        registry = core.PluginRegistry()

        with pytest.raises(config.PluginNotFoundError) as exc_info:
            registry.get("missing")

        assert exc_info.value.plugin_name == "missing"
        assert exc_info.value.available_plugins == ()

    def test_plugin_registry__names_empty__returns_empty_tuple(self) -> None:
        """A freshly initialized registry returns an empty tuple of plugin names."""

        registry = core.PluginRegistry()

        assert registry.names() == ()

    def test_plugin_registry__names_multiple__returns_alphabetically_sorted_tuple(self) -> None:
        """Names returns an immutable tuple sorted in ascending alphabetical order."""

        registry = core.PluginRegistry()

        registry.register(_SecondSamplePlugin)
        registry.register(_FirstSamplePlugin)

        assert registry.names() == ("alpha_plugin", "beta_plugin")

    def test_plugin_registry__multiple_instances__remain_strictly_isolated(self) -> None:
        """Mutations to one registry instance do not affect other instances."""

        first = core.PluginRegistry()
        second = core.PluginRegistry()

        first.register(_FirstSamplePlugin)

        assert first.names() == ("alpha_plugin",)
        assert second.names() == ()

    def test_plugin_registry__register_positional_only__rejects_keyword_arguments(self) -> None:
        """The register method enforces positional-only parameter delivery."""

        registry = core.PluginRegistry()

        with pytest.raises(TypeError, match="positional-only"):
            registry.register(plugin=_FirstSamplePlugin)  # type: ignore[call-arg]

    def test_plugin_registry__get_positional_only__rejects_keyword_arguments(self) -> None:
        """The get method enforces positional-only parameter delivery."""

        registry = core.PluginRegistry()
        registry.register(_FirstSamplePlugin)

        with pytest.raises(TypeError, match="positional-only"):
            registry.get(name="alpha_plugin")  # type: ignore[call-arg]
