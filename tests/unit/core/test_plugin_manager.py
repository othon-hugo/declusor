"""Unit tests for PluginManager in declusor.core.plugin."""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from declusor import config, contract, core, testing


class DummyValidConfig(contract.ParsedArguments, total=False):
    """Configuration options for DummyValidPlugin."""


class DummyValidPlugin(contract.IPluginExtension[DummyValidConfig]):
    """Compliant test plugin implementing all required IPlugin methods."""

    name = "dummy_valid"
    description = "A valid dummy plugin for unit tests"
    version = "1.0.0"
    options_type = DummyValidConfig
    routes = {"eval": core.OFFICIAL_ROUTES["eval"]}

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DummyValidConfig:
        return DummyValidConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DummyValidConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DummyValidConfig]:
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
    def validate(cls, plugin_config: contract.PluginConfig[DummyValidConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DummyValidConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


class NotAPlugin:
    """Class that does not inherit from IPluginExtension."""

    name = "not_a_plugin"


class MissingAbstractMethods(contract.IPluginExtension[contract.ParsedArguments]):
    """Plugin subclass missing required abstract method implementations."""

    name = "missing_methods"


class DummyEntryPoint:
    """Typed test double simulating an importlib.metadata.EntryPoint."""

    def __init__(self, name: str, plugin_cls: type[contract.IPluginExtension[Any]], load_error: Exception | None = None) -> None:
        self.name = name
        self._plugin_cls = plugin_cls
        self._load_error = load_error

    def load(self) -> type[contract.IPluginExtension[Any]]:
        if self._load_error is not None:
            raise self._load_error
        return self._plugin_cls


class TestPluginValidation:
    """Tests verifying candidate class validation on PluginManager."""

    def test_validate_plugin__valid_compliant_plugin__passes_validation_without_error(self) -> None:
        """A compliant IPluginExtension subclass passes contract validation without error."""

        manager = core.PluginManager()

        manager.validate_plugin(DummyValidPlugin)

    def test_validate_plugin__non_class_object__raises_plugin_validation_error(self) -> None:
        """Passing a non-class object raises PluginValidationError."""

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must be a class"):
            manager.validate_plugin("not_a_class")  # type: ignore[arg-type]

    def test_validate_plugin__class_not_subclassing_iplugin__raises_plugin_validation_error(self) -> None:
        """Passing a class not inheriting from IPluginExtension raises PluginValidationError."""

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must implement 'IPlugin'"):
            manager.validate_plugin(NotAPlugin)

    def test_validate_plugin__empty_string_name__raises_plugin_validation_error(self) -> None:
        """A plugin class with an empty string name raises PluginValidationError."""

        class EmptyNamePlugin(DummyValidPlugin):
            name = ""

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must define a non-empty string 'name'"):
            manager.validate_plugin(EmptyNamePlugin)

    def test_validate_plugin__whitespace_name__raises_plugin_validation_error(self) -> None:
        """A plugin class with only whitespace in name raises PluginValidationError."""

        class WhitespaceNamePlugin(DummyValidPlugin):
            name = "   "

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must define a non-empty string 'name'"):
            manager.validate_plugin(WhitespaceNamePlugin)

    def test_validate_plugin__non_string_name__raises_plugin_validation_error(self) -> None:
        """A plugin class with a non-string name raises PluginValidationError."""

        class NonStringNamePlugin(DummyValidPlugin):
            name = 12345  # type: ignore[assignment]

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must define a non-empty string 'name'"):
            manager.validate_plugin(NonStringNamePlugin)

    def test_validate_plugin__route_with_invalid_registration__raises_plugin_validation_error(self) -> None:
        """A plugin with a non-RouteRegistration route value is rejected."""

        class InvalidRoutesPlugin(DummyValidPlugin):
            routes = {"custom": "not a registration"}  # type: ignore[dict-item]

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="RouteRegistration"):
            manager.validate_plugin(InvalidRoutesPlugin)

    def test_validate_plugin__empty_route_name__raises_plugin_validation_error(self) -> None:
        """A plugin route name must be non-empty after trimming."""

        class EmptyRouteNamePlugin(DummyValidPlugin):
            routes = {"  ": core.OFFICIAL_ROUTES["eval"]}

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="non-empty string route names"):
            manager.validate_plugin(EmptyRouteNamePlugin)

    def test_validate_plugin__whitespace_equivalent_route_names__raises_plugin_validation_error(self) -> None:
        """Routes that normalize to the same name are rejected before application setup."""

        class DuplicateNormalizedRoutesPlugin(DummyValidPlugin):
            routes = {"custom": core.OFFICIAL_ROUTES["eval"], " custom ": core.OFFICIAL_ROUTES["eval"]}

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="duplicate normalized route 'custom'"):
            manager.validate_plugin(DuplicateNormalizedRoutesPlugin)

    def test_validate_plugin__reserved_route_name__raises_plugin_validation_error(self) -> None:
        """Plugins cannot replace the application-owned help and exit routes."""

        class ReservedRoutePlugin(DummyValidPlugin):
            routes = {"help": core.OFFICIAL_ROUTES["eval"]}

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="cannot override protected route 'help'"):
            manager.validate_plugin(ReservedRoutePlugin)

    def test_validate_plugin__unimplemented_abstract_methods__raises_plugin_validation_error_with_sorted_methods(
        self,
    ) -> None:
        """A plugin class with unimplemented abstract methods raises PluginValidationError listing them."""

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError) as exc_info:
            manager.validate_plugin(MissingAbstractMethods)

        message = str(exc_info.value)
        assert "unimplemented abstract methods:" in message
        assert "build_config" in message
        assert "build_runtime" in message
        assert "configure_parser" in message
        assert "extract_options" in message
        assert "validate" in message

    def test_validate_plugin__missing_name_attribute__raises_plugin_validation_error(self) -> None:
        """A plugin class without a 'name' attribute raises PluginValidationError."""

        class MissingNamePlugin(contract.IPluginExtension[contract.ParsedArguments]):
            pass

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must define a non-empty string 'name'"):
            manager.validate_plugin(MissingNamePlugin)

    def test_validate_plugin__none_name_attribute__raises_plugin_validation_error(self) -> None:
        """A plugin class with name set to None raises PluginValidationError."""

        class NoneNamePlugin(DummyValidPlugin):
            name = None  # type: ignore[assignment]

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError, match="must define a non-empty string 'name'"):
            manager.validate_plugin(NoneNamePlugin)

    def test_validate_plugin__positional_only__rejects_keyword_arguments(self) -> None:
        """The validate_plugin method enforces positional-only parameter delivery."""

        manager = core.PluginManager()

        with pytest.raises(TypeError, match="positional-only"):
            manager.validate_plugin(candidate=DummyValidPlugin)  # type: ignore[call-arg]


class TestPluginManagerRegistration:
    """Tests verifying plugin registration and source tracking on PluginManager."""

    def test_register__valid_plugin__records_source_and_makes_available_in_names(self) -> None:
        """Registering a plugin stores the class and exposes its name."""

        manager = core.PluginManager()

        manager.register(DummyValidPlugin, source="custom_source")

        assert manager.get("dummy_valid") is DummyValidPlugin
        assert "dummy_valid" in manager.names()
        assert manager.get_source("dummy_valid") == "custom_source"

    def test_register__default_source__records_manual_source(self) -> None:
        """When source parameter is omitted, the default source label is 'manual'."""

        manager = core.PluginManager()

        manager.register(DummyValidPlugin)

        assert manager.get_source("dummy_valid") == "manual"

    def test_register__duplicate_without_override__raises_value_error_with_source(self) -> None:
        """Registering an existing name without allow_override raises ValueError indicating origin."""

        manager = core.PluginManager()
        manager.register(DummyValidPlugin, source="first_origin")

        with pytest.raises(ValueError, match="already registered from first_origin"):
            manager.register(DummyValidPlugin, source="second_origin", allow_override=False)

    def test_register__duplicate_with_override__replaces_instance_and_updates_source(self) -> None:
        """Registering an existing name with allow_override replaces the plugin and updates the source."""

        class ReplacementPlugin(DummyValidPlugin):
            description = "Replaced version"

        manager = core.PluginManager()
        manager.register(DummyValidPlugin, source="original")
        manager.register(ReplacementPlugin, source="updated", allow_override=True)

        assert manager.get("dummy_valid") is ReplacementPlugin
        assert manager.get_source("dummy_valid") == "updated"

    def test_get_source__registered_plugin__returns_source_label(self) -> None:
        """get_source returns the registered source label for known plugins."""

        manager = core.PluginManager()
        manager.register(DummyValidPlugin, source="tested_source")

        assert manager.get_source("dummy_valid") == "tested_source"

    def test_get_source__unregistered_plugin__returns_none(self) -> None:
        """get_source returns None for unregistered plugin names."""

        manager = core.PluginManager()

        assert manager.get_source("nonexistent") is None

    def test_register__invalid_candidate__fails_validation_before_registration(self) -> None:
        """Registering an invalid candidate class fails validation without updating registry."""

        manager = core.PluginManager()

        with pytest.raises(config.PluginValidationError):
            manager.register(NotAPlugin)  # type: ignore[arg-type]

        assert manager.names() == ()

    def test_register__positional_only__rejects_keyword_arguments(self) -> None:
        """The register method enforces positional-only candidate plugin delivery."""

        manager = core.PluginManager()

        with pytest.raises(TypeError, match="positional-only"):
            manager.register(plugin=DummyValidPlugin)  # type: ignore[call-arg]

    def test_get_source_positional_only__rejects_keyword_arguments(self) -> None:
        """The get_source method enforces positional-only plugin name delivery."""

        manager = core.PluginManager()
        manager.register(DummyValidPlugin)

        with pytest.raises(TypeError, match="positional-only"):
            manager.get_source(name="dummy_valid")  # type: ignore[call-arg]


class TestPluginManagerDirectoryDiscovery:
    """Tests verifying dynamic filesystem scanning in PluginManager."""

    def test_load_from_directory__nonexistent_path__returns_empty_list(self, tmp_path: Path) -> None:
        """Attempting to scan a nonexistent directory returns an empty list."""

        manager = core.PluginManager()

        loaded = manager.load_from_directory(tmp_path / "nonexistent")

        assert loaded == []

    def test_load_from_directory__file_path_target__returns_empty_list(self, tmp_path: Path) -> None:
        """Attempting to scan a file path instead of a directory returns an empty list."""

        target_file = tmp_path / "regular_file.txt"
        target_file.write_text("not a dir", encoding="utf-8")

        manager = core.PluginManager()

        assert manager.load_from_directory(target_file) == []

    def test_load_from_directory__empty_directory__returns_empty_list(self, tmp_path: Path) -> None:
        """Scanning an empty directory returns an empty list."""

        manager = core.PluginManager()

        assert manager.load_from_directory(tmp_path) == []

    def test_load_from_directory__hidden_or_dunder_subdirectories__are_ignored(self, tmp_path: Path) -> None:
        """Subdirectories starting with '.' or '_' are skipped during scanning."""

        hidden_dir = tmp_path / ".hidden_plugin"
        hidden_dir.mkdir()
        (hidden_dir / "plugin.py").write_text("# hidden", encoding="utf-8")

        dunder_dir = tmp_path / "__pycache__"
        dunder_dir.mkdir()
        (dunder_dir / "plugin.py").write_text("# dunder", encoding="utf-8")

        manager = core.PluginManager()

        assert manager.load_from_directory(tmp_path) == []

    def test_load_from_directory__flat_layout_with_plugin_py__discovers_and_registers(self, tmp_path: Path) -> None:
        """Discovers a plugin package having plugin.py at its root."""

        plugin_dir = tmp_path / "custom_agent"
        plugin_dir.mkdir()

        code = """from collections.abc import Mapping
from declusor import contract

class CustomConfig(contract.ParsedArguments, total=False):
    pass

class CustomPlugin(contract.IPluginExtension[CustomConfig]):
    name = "custom_agent"
    description = "Flat layout test plugin"
    options_type = CustomConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> CustomConfig:
        return CustomConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
        (plugin_dir / "plugin.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        loaded = manager.load_from_directory(tmp_path)

        assert "custom_agent" in loaded
        assert manager.get("custom_agent").name == "custom_agent"
        assert manager.get_source("custom_agent") == "directory:custom_agent"

    def test_load_from_directory__package_with_init_py__discovers_and_registers(self, tmp_path: Path) -> None:
        """Discovers a plugin package having __init__.py at its root."""

        plugin_dir = tmp_path / "init_agent"
        plugin_dir.mkdir()

        code = """from collections.abc import Mapping
from declusor import contract

class InitConfig(contract.ParsedArguments, total=False):
    pass

class InitPlugin(contract.IPluginExtension[InitConfig]):
    name = "init_agent"
    description = "Init layout test plugin"
    options_type = InitConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> InitConfig:
        return InitConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
        (plugin_dir / "__init__.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        loaded = manager.load_from_directory(tmp_path)

        assert "init_agent" in loaded
        assert manager.get("init_agent").name == "init_agent"

    def test_load_from_directory__src_layout__discovers_and_registers(self, tmp_path: Path) -> None:
        """Discovers a plugin structured using canonical src/<name>/ layout."""

        plugin_root = tmp_path / "src_layout_agent"
        src_pkg = plugin_root / "src" / "src_layout_agent"
        src_pkg.mkdir(parents=True)

        code = """from collections.abc import Mapping
from declusor import contract

class SrcConfig(contract.ParsedArguments, total=False):
    pass

class SrcPlugin(contract.IPluginExtension[SrcConfig]):
    name = "src_layout_agent"
    description = "Canonical src layout test plugin"
    options_type = SrcConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> SrcConfig:
        return SrcConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
        (src_pkg / "__init__.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        loaded = manager.load_from_directory(tmp_path)

        assert "src_layout_agent" in loaded
        assert manager.get("src_layout_agent").name == "src_layout_agent"

    def test_load_from_directory__subdirectory_without_plugin_entry__skipped(self, tmp_path: Path) -> None:
        """Directories containing no valid plugin entry points are skipped."""

        empty_folder = tmp_path / "not_a_plugin_folder"
        empty_folder.mkdir()
        (empty_folder / "random_file.txt").write_text("nothing here", encoding="utf-8")

        manager = core.PluginManager()
        loaded = manager.load_from_directory(tmp_path)

        assert loaded == []

    def test_load_from_directory__invalid_plugin_class_in_file__skipped_without_raising(self, tmp_path: Path) -> None:
        """Directories defining invalid plugin classes are caught and skipped gracefully."""

        invalid_plugin_dir = tmp_path / "broken_plugin"
        invalid_plugin_dir.mkdir()

        broken_code = """from declusor import contract

class BrokenPlugin(contract.IPluginExtension[contract.ParsedArguments]):
    name = "broken_plugin"
    # Lacks all abstract methods!
"""
        (invalid_plugin_dir / "plugin.py").write_text(broken_code, encoding="utf-8")

        manager = core.PluginManager()
        loaded = manager.load_from_directory(tmp_path)

        assert loaded == []

    def test_load_from_directory__duplicate_with_allow_override_false__skips_duplicate_silently(self, tmp_path: Path) -> None:
        """When allow_override is False, existing plugins are preserved and duplicates skipped silently."""

        manager = core.PluginManager()
        manager.register(DummyValidPlugin, source="pre_existing")

        dup_dir = tmp_path / "dummy_valid"
        dup_dir.mkdir()

        code = """from collections.abc import Mapping
from pathlib import Path
from declusor import config, contract, testing

class DupConfig(contract.ParsedArguments, total=False):
    pass

class DupPlugin(contract.IPluginExtension[DupConfig]):
    name = "dummy_valid"
    description = "Duplicate plugin attempting to override"
    options_type = DupConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DupConfig:
        return DupConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=config.DEFAULT_EXECUTION_MODE):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return testing.DummyPluginRuntime()
"""
        (dup_dir / "plugin.py").write_text(code, encoding="utf-8")

        loaded = manager.load_from_directory(tmp_path, allow_override=False)

        assert "dummy_valid" not in loaded
        assert manager.get("dummy_valid") is DummyValidPlugin
        assert manager.get_source("dummy_valid") == "pre_existing"

    def test_load_from_directory__positional_only__rejects_keyword_arguments(self, tmp_path: Path) -> None:
        """The load_from_directory method enforces positional-only directory parameter."""

        manager = core.PluginManager()

        with pytest.raises(TypeError, match="positional-only"):
            manager.load_from_directory(directory=tmp_path)  # type: ignore[call-arg]


class TestPluginManagerEntryPointDiscovery:
    """Tests verifying Python Entry Points discovery on PluginManager."""

    def test_load_from_entry_points__valid_entry_points__registers_discovered_plugins(self) -> None:
        """Discovers and registers valid plugins exposed via Python entry points."""

        entry_point = DummyEntryPoint(name="valid_ep", plugin_cls=DummyValidPlugin)

        def loader(*, group: str) -> Iterable[DummyEntryPoint]:
            return [entry_point]

        manager = core.PluginManager()
        loaded = manager.load_from_entry_points(entry_points_loader=loader)

        assert "dummy_valid" in loaded
        assert manager.get("dummy_valid") is DummyValidPlugin
        assert manager.get_source("dummy_valid") == "entry_point:valid_ep"

    def test_load_from_entry_points__loader_raising_exception__returns_empty_list(self) -> None:
        """When entry_points_loader raises an exception, it is caught and returns empty list."""

        def failing_loader(*, group: str) -> Iterable[DummyEntryPoint]:
            raise RuntimeError("metadata discovery failed")

        manager = core.PluginManager()
        loaded = manager.load_from_entry_points(entry_points_loader=failing_loader)

        assert loaded == []

    def test_load_from_entry_points__entry_point_load_failure__skips_failing_entry_point(self) -> None:
        """An entry point that raises during .load() is skipped gracefully."""

        failing_ep = DummyEntryPoint(
            name="broken_ep",
            plugin_cls=DummyValidPlugin,
            load_error=ImportError("module not found"),
        )
        working_ep = DummyEntryPoint(name="good_ep", plugin_cls=DummyValidPlugin)

        def loader(*, group: str) -> Iterable[DummyEntryPoint]:
            return [failing_ep, working_ep]

        manager = core.PluginManager()
        loaded = manager.load_from_entry_points(entry_points_loader=loader)

        assert loaded == ["dummy_valid"]

    def test_load_from_entry_points__entry_point_registration_error__skips_invalid_entry_point(self) -> None:
        """An entry point producing an invalid candidate class is skipped during validation."""

        bad_ep = DummyEntryPoint(name="bad_ep", plugin_cls=NotAPlugin)  # type: ignore[arg-type]

        def loader(*, group: str) -> Iterable[DummyEntryPoint]:
            return [bad_ep]

        manager = core.PluginManager()
        loaded = manager.load_from_entry_points(entry_points_loader=loader)

        assert loaded == []

    def test_load_from_entry_points__custom_group__queries_specified_entry_point_group(self) -> None:
        """Queries the specified entry point group string."""

        observed_groups: list[str] = []

        def loader(*, group: str) -> Iterable[DummyEntryPoint]:
            observed_groups.append(group)
            return []

        manager = core.PluginManager()
        manager.load_from_entry_points(group="custom.group", entry_points_loader=loader)

        assert observed_groups == ["custom.group"]


class TestPluginManagerDiscoveryPrecedence:
    """Tests verifying multi-tier discovery and precedence in PluginManager."""

    def test_discover__builtins_enabled__discovers_builtin_plugins(self) -> None:
        """discover() loads repository built-in plugins (shell_socket and py_socket)."""

        manager = core.PluginManager()
        manager.discover(enable_entry_points=False)

        names = manager.names()
        assert "shell_socket" in names
        assert "py_socket" in names

    def test_discover__entry_points_disabled__skips_entry_point_discovery(self) -> None:
        """When enable_entry_points is False, the entry points loader is not queried."""

        queried = False

        def loader(*, group: str) -> Iterable[Any]:
            nonlocal queried
            queried = True
            return []

        manager = core.PluginManager()
        manager.discover(enable_entry_points=False, entry_points_loader=loader)

        assert queried is False

    def test_discover__custom_search_dirs__loads_plugins_from_specified_paths(self, tmp_path: Path) -> None:
        """Passing search_dirs to discover() loads drop-in plugins from those paths."""

        custom_dir = tmp_path / "custom_dir_plugin"
        custom_dir.mkdir()

        code = """from collections.abc import Mapping
from declusor import contract

class DirConfig(contract.ParsedArguments, total=False):
    pass

class DirPlugin(contract.IPluginExtension[DirConfig]):
    name = "cli_discovered_agent"
    description = "CLI discovered test plugin"
    options_type = DirConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DirConfig:
        return DirConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
        (custom_dir / "plugin.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        manager.discover([tmp_path], enable_entry_points=False)

        assert "cli_discovered_agent" in manager.names()
        assert manager.get_source("cli_discovered_agent") == "custom-cli:custom_dir_plugin"

    def test_discover__nonexistent_search_dirs__skips_silently(self, tmp_path: Path) -> None:
        """Nonexistent directories in search_dirs are skipped without raising errors."""

        manager = core.PluginManager()
        manager.discover([tmp_path / "does_not_exist"], enable_entry_points=False)

        # Standard discovery still completes without error
        assert "shell_socket" in manager.names()

    def test_discover__returns_self_instance_for_call_chaining(self) -> None:
        """discover() returns the PluginManager instance to allow method chaining."""

        manager = core.PluginManager()
        result = manager.discover(enable_entry_points=False)

        assert result is manager

    def test_discover__custom_search_dirs_overrides_builtin_plugin(self, tmp_path: Path) -> None:
        """Explicit search_dirs take precedence over built-in plugins with identical names."""

        custom_shell_dir = tmp_path / "shell_socket"
        custom_shell_dir.mkdir()

        code = """from collections.abc import Mapping
from declusor import contract, testing

class CustomShellConfig(contract.ParsedArguments, total=False):
    pass

class CustomShellPlugin(contract.IPluginExtension[CustomShellConfig]):
    name = "shell_socket"
    description = "Custom CLI shell override"
    options_type = CustomShellConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> CustomShellConfig:
        return CustomShellConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return testing.DummyPluginRuntime()
"""
        (custom_shell_dir / "plugin.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        manager.discover([tmp_path], enable_entry_points=False)

        assert manager.get("shell_socket").description == "Custom CLI shell override"
        assert manager.get_source("shell_socket") == "custom-cli:shell_socket"

    def test_discover__entry_point_overrides_builtin_plugin(self) -> None:
        """Entry points take precedence over repository built-in plugins with identical names."""

        class EntryPointShellPlugin(DummyValidPlugin):
            name = "shell_socket"
            description = "Entry point shell override"

        ep = DummyEntryPoint(name="shell_socket_ep", plugin_cls=EntryPointShellPlugin)

        def loader(*, group: str) -> Iterable[DummyEntryPoint]:
            return [ep]

        manager = core.PluginManager()
        manager.discover(enable_entry_points=True, entry_points_loader=loader)

        assert manager.get("shell_socket").description == "Entry point shell override"
        assert manager.get_source("shell_socket") == "entry_point:shell_socket_ep"

    def test_discover__custom_search_dirs_overrides_entry_point(self, tmp_path: Path) -> None:
        """Explicit search_dirs take precedence over entry points with identical names."""

        class EntryPointPlugin(DummyValidPlugin):
            name = "contested_plugin"
            description = "Entry point version"

        ep = DummyEntryPoint(name="contested_ep", plugin_cls=EntryPointPlugin)

        def loader(*, group: str) -> Iterable[DummyEntryPoint]:
            return [ep]

        custom_dir = tmp_path / "contested_plugin"
        custom_dir.mkdir()

        code = """from collections.abc import Mapping
from declusor import contract, testing

class ContestedConfig(contract.ParsedArguments, total=False):
    pass

class ContestedPlugin(contract.IPluginExtension[ContestedConfig]):
    name = "contested_plugin"
    description = "CLI custom dir version"
    options_type = ContestedConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> ContestedConfig:
        return ContestedConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return testing.DummyPluginRuntime()
"""
        (custom_dir / "plugin.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        manager.discover([tmp_path], enable_entry_points=True, entry_points_loader=loader)

        assert manager.get("contested_plugin").description == "CLI custom dir version"
        assert manager.get_source("contested_plugin") == "custom-cli:contested_plugin"

    def test_discover__user_plugins_dir__loads_plugins_when_directory_exists(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When USER_PLUGINS_DIR exists, drop-in plugins are loaded with 'user-dropin' source."""

        user_plugins = tmp_path / "user_plugins"
        plugin_folder = user_plugins / "user_agent"
        plugin_folder.mkdir(parents=True)

        code = """from collections.abc import Mapping
from declusor import contract, testing

class UserConfig(contract.ParsedArguments, total=False):
    pass

class UserPlugin(contract.IPluginExtension[UserConfig]):
    name = "user_agent"
    description = "User drop-in agent"
    options_type = UserConfig
    routes = {}

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> UserConfig:
        return UserConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return testing.DummyPluginRuntime()
"""
        (plugin_folder / "plugin.py").write_text(code, encoding="utf-8")

        monkeypatch.setattr(config, "USER_PLUGINS_DIR", user_plugins)

        manager = core.PluginManager()
        manager.discover(enable_entry_points=False)

        assert "user_agent" in manager.names()
        assert manager.get_source("user_agent") == "user-dropin:user_agent"

    def test_discover__positional_only__rejects_keyword_arguments(self) -> None:
        """The discover method enforces positional-only search_dirs argument."""

        manager = core.PluginManager()

        with pytest.raises(TypeError, match="positional-only"):
            manager.discover(search_dirs=[Path(".")])  # type: ignore[call-arg]
