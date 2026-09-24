from unittest.mock import MagicMock

import pytest

from declusor import config, contract, core


def test_declusor_parser_initialization_with_registry() -> None:
    """Verify parser configures common arguments based on registry plugins."""
    mock_plugin = MagicMock(spec=contract.IClientPlugin)
    mock_plugin.name = "mock_client"

    registry = core.ClientRegistry()
    registry.register(mock_plugin)

    parser = core.DeclusorParser(registry, name="test_app")
    assert parser.prog == "test_app"


def test_declusor_parser_parse_success(tmp_path) -> None:
    """Verify parser parses argv and builds validated ClientConfig."""
    mock_plugin = MagicMock()
    mock_plugin.name = "mock_client"
    mock_config = MagicMock(spec=contract.ClientConfig)
    mock_plugin.build_config.return_value = mock_config

    registry = core.ClientRegistry()
    registry.register(mock_plugin)

    parser = core.DeclusorParser(registry, name="test_app")
    options = parser.parse(["127.0.0.1", "9000", "-c", "mock_client", "--data-root", str(tmp_path)])

    assert options["host"] == "127.0.0.1"
    assert options["port"] == 9000
    assert options["client"] == mock_config
    mock_plugin.configure_parser.assert_called_once_with(parser)
    mock_plugin.build_config.assert_called_once()
    mock_plugin.validate.assert_called_once_with(mock_config)


def test_declusor_parser_parse_missing_positional_raises() -> None:
    """Verify parser raises ParserError when required positional args are missing."""
    registry = core.ClientRegistry()
    parser = core.DeclusorParser(registry, name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(["127.0.0.1"])  # missing port
