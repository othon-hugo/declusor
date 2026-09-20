"""Tests for ``declusor.util.client`` — client-script formatting utilities.

Covers ``format_client_script`` (Template substitution, file handling, edge
cases) and ``format_function_call`` (shell-language dispatch, argument
quoting, and shell escaping).

Note: ``util/client.py`` no longer exists as a separate module.
These tests target the corresponding functions that now live in the
``connection.shell_socket`` module or ``util`` package.
"""

from pathlib import Path

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_clients_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ``BasePath.CLIENTS_DIR`` to a temporary directory."""


@pytest.fixture
def sample_client_script(mock_clients_dir: Path) -> Path:
    """Create a sample client script with ``$HOST`` and ``$PORT`` placeholders."""


# =============================================================================
# Tests: format_client_script — variable substitution
# =============================================================================


def test_substitutes_host_and_port(mock_clients_dir: Path) -> None:
    """``$HOST`` and ``$PORT`` placeholders must be replaced with actual values."""


def test_substitutes_acknowledge_placeholder(mock_clients_dir: Path) -> None:
    """``$ACKNOWLEDGE`` must be replaced with the hex-encoded ACK_CLIENT_VALUE."""


def test_safe_substitute_preserves_missing_vars(mock_clients_dir: Path) -> None:
    """An undefined ``$UNDEFINED_VAR`` placeholder must remain in the output."""


def test_substitutes_custom_kwargs(mock_clients_dir: Path) -> None:
    """Extra keyword arguments must be substituted into the template."""


# =============================================================================
# Tests: format_client_script — file handling
# =============================================================================


def test_reads_file_content(mock_clients_dir: Path) -> None:
    """The file must be read and its content returned after substitution."""


def test_file_not_found_raises(mock_clients_dir: Path) -> None:
    """A nonexistent client filename must raise ``FileNotFoundError``."""


def test_resolves_path_relative_to_clients_dir(mock_clients_dir: Path) -> None:
    """A bare filename must be resolved relative to ``BasePath.CLIENTS_DIR``."""


# =============================================================================
# Tests: format_client_script — edge cases
# =============================================================================


def test_empty_file_returns_empty_string(mock_clients_dir: Path) -> None:
    """An empty script file must produce an empty string."""


def test_no_placeholders_returns_original(mock_clients_dir: Path) -> None:
    """A script with zero ``$`` placeholders must pass through unchanged."""


def test_dollar_dollar_is_literal(mock_clients_dir: Path) -> None:
    """``$$`` must remain as a single ``$`` (Template behaviour)."""


# =============================================================================
# Tests: format_function_call — argument handling
# =============================================================================


def test_function_call_no_args() -> None:
    """A function name with no arguments must produce ``"function_name "``."""


def test_function_call_single_arg() -> None:
    """A single argument must be shell-quoted (e.g. ``'arg1'``)."""


def test_function_call_multiple_args() -> None:
    """Multiple arguments must be space-separated and individually quoted."""


# =============================================================================
# Tests: format_function_call — shell escaping
# =============================================================================


def test_escapes_single_quotes() -> None:
    """A value containing ``'`` must be safely escaped for the shell."""


def test_escapes_double_quotes() -> None:
    """A value containing ``"`` must be safely handled."""


def test_escapes_special_characters() -> None:
    """Shell metacharacters (``$``, ``;``, etc.) must be neutralised by quoting."""


def test_escapes_newlines() -> None:
    """Embedded newlines must be properly escaped."""


def test_escapes_backticks() -> None:
    """Backticks must be escaped to prevent command substitution."""


def test_base64_payload_quoted_correctly() -> None:
    """A typical base64 string must be properly quoted without extra escaping."""


# =============================================================================
# Tests: _format_bash_function_call (internal)
# =============================================================================


def test_bash_function_call_uses_shlex_quote() -> None:
    """Each argument must be passed through ``shlex.quote``."""


def test_bash_function_call_empty_string_arg() -> None:
    """An empty string argument must be quoted as ``''``."""
