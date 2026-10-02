from pathlib import Path

import pytest

from declusor import config, core, testing


def test_declusor_parser_initialization() -> None:
    """Verify parser initializes with name and description without requiring a manager."""

    parser = core.DeclusorParser(name="test_app", description="test description")
    assert parser.prog == "test_app"
    assert parser.description == "test description"


def test_declusor_parser_parse_success(tmp_path: Path) -> None:
    """Verify parser parses argv and builds validated PluginConfig."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)],
    )

    assert plugin_config.host == "127.0.0.1"
    assert plugin_config.port == 9000
    assert plugin_config.kind == testing.DummyPlugin.name
    assert plugin_config.filesystem is not None
    assert plugin_config.filesystem.root == tmp_path.resolve()
    assert parser in testing.DummyPlugin.configured_parsers


def test_declusor_parser_parse_defaults_filesystem_to_plugin_default() -> None:
    """When --assets-dir is omitted, plugin builds its default filesystem."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.filesystem is not None


def test_parser_parse_is_idempotent(tmp_path: Path) -> None:
    """Calling parse() multiple times on the same DeclusorParser must not error."""

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    argv = ["127.0.0.1", "8080", "--plugin", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)]

    parser = core.DeclusorParser(name="test_app", description="test description")
    config1 = parser.parse(manager, argv)
    assert config1.host == "127.0.0.1"
    assert config1.port == 8080

    # Second parse on the exact same parser instance
    config2 = parser.parse(manager, argv)
    assert config2.host == "127.0.0.1"
    assert config2.port == 8080


def test_declusor_parser_parse_missing_positional_raises() -> None:
    """Verify parser raises ParserError when required positional args are missing."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(manager, ["127.0.0.1"])  # missing port


def test_declusor_parser_parse_invalid_plugin_raises() -> None:
    """Verify parser raises ParserError when selected plugin is not registered."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="invalid choice"):
        parser.parse(manager, ["127.0.0.1", "9000", "-p", "nonexistent"])


def test_declusor_parser_mode_defaults_to_cli() -> None:
    """Verify parser defaults execution mode to ExecutionMode.CLI."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.mode == config.ExecutionMode.CLI


def test_declusor_parser_explicit_mode() -> None:
    """Verify parser accepts explicit --mode and -m arguments."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--mode", "http"],
    )
    assert plugin_config.mode == config.ExecutionMode.HTTP

    plugin_config_short = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-m", "mcp"],
    )
    assert plugin_config_short.mode == config.ExecutionMode.MCP


def test_declusor_parser_invalid_mode_raises() -> None:
    """Verify parser raises ParserError when invalid execution mode is provided."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(manager, ["127.0.0.1", "9000", "--mode", "invalid_mode"])


def test_declusor_parser_launcher_output_defaults_to_terminal() -> None:
    """Verify parser defaults launcher output to TERMINAL mode with no path."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.launcher_output_mode == config.LauncherOutputMode.TERMINAL
    assert plugin_config.launcher_output_path is None
    assert plugin_config.launcher_wrapper is None


def test_declusor_parser_explicit_launcher_output_silent() -> None:
    """Verify parser accepts --launcher-output silent."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--launcher-output", "silent"],
    )

    assert plugin_config.launcher_output_mode == config.LauncherOutputMode.SILENT
    assert plugin_config.launcher_output_path is None


def test_declusor_parser_explicit_launcher_output_file(tmp_path: Path) -> None:
    """Verify parser accepts --launcher-output file:<path> and resolves destination path."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    target_file = tmp_path / "client_launcher.sh"
    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--launcher-output", f"file:{target_file}"],
    )

    assert plugin_config.launcher_output_mode == config.LauncherOutputMode.FILE
    assert plugin_config.launcher_output_path == target_file


def test_declusor_parser_invalid_launcher_output_raises() -> None:
    """Verify parser raises ParserError for invalid launcher output choice."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="--launcher-output"):
        parser.parse(manager, ["127.0.0.1", "9000", "--launcher-output", "unsupported"])


def test_declusor_parser_empty_launcher_output_file_path_raises() -> None:
    """Verify parser raises ParserError when file:<path> has an empty path."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="--launcher-output"):
        parser.parse(manager, ["127.0.0.1", "9000", "--launcher-output", "file:"])


def test_declusor_parser_explicit_launcher_wrapper() -> None:
    """Verify parser accepts --launcher-wrapper template."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        [
            "127.0.0.1",
            "9000",
            "-p",
            testing.DummyPlugin.name,
            "--launcher-wrapper",
            "python3 -c '$DECLUSOR_SCRIPT'",
        ],
    )

    assert plugin_config.launcher_wrapper == "python3 -c '$DECLUSOR_SCRIPT'"


def test_declusor_parser_empty_launcher_wrapper_raises() -> None:
    """Verify parser raises ParserError when --launcher-wrapper is empty string."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="--launcher-wrapper"):
        parser.parse(manager, ["127.0.0.1", "9000", "--launcher-wrapper", ""])


def test_declusor_parser_default_timeout_is_none() -> None:
    """Verify parser defaults timeout to None."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.timeout is None


def test_declusor_parser_explicit_timeout() -> None:
    """Verify parser accepts -t and --timeout float values."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")

    cfg1 = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-t", "5.5"])
    assert cfg1.timeout == 5.5

    cfg2 = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--timeout", "10"])
    assert cfg2.timeout == 10.0


def test_declusor_parser_negative_timeout_raises() -> None:
    """Verify parser raises ParserError when timeout is negative."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="invalid Timeout value"):
        parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-t", "-1.0"])


def test_declusor_parser_invalid_timeout_type_raises() -> None:
    """Verify parser raises ParserError when timeout is not a valid float."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-t", "abc"])


def test_declusor_parser_transport_layers_defaults_to_empty() -> None:
    """Verify transport_layers is an empty tuple when --transport-layer is omitted."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.transport_layers == ()


def test_declusor_parser_single_transport_layer() -> None:
    """Verify parser captures a single --transport-layer flag."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--transport-layer", "xor"],
    )

    assert plugin_config.transport_layers == ("xor",)


def test_declusor_parser_multiple_transport_layers_in_order() -> None:
    """Verify parser accumulates repeatable --transport-layer flags in order."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        [
            "127.0.0.1",
            "9000",
            "-p",
            testing.DummyPlugin.name,
            "--transport-layer",
            "xor",
            "--transport-layer",
            "xor",
        ],
    )

    assert plugin_config.transport_layers == ("xor", "xor")


def test_declusor_parser_transport_layer_invalid_choice_raises() -> None:
    """Verify parser raises ParserError when an unknown transport layer is passed."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="invalid choice: 'unknown'"):
        parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--transport-layer", "unknown"],
        )


def test_declusor_parser_non_string_plugin_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify parser raises ParserError if preliminary parsed plugin is not a string."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    fake_args = type("Args", (), {"plugin_dir": None, "plugin": 12345})()
    monkeypatch.setattr(parser, "parse_known_args", lambda argv: (fake_args, []))

    with pytest.raises(config.ParserError, match="argument -p/--plugin: expected string, got int"):
        parser.parse(manager, ["127.0.0.1", "9000"])
