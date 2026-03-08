# Tests Directory

The **tests** directory contains the complete test suite for Declusor. Test files mirror the source-code package structure using the naming convention `test_<package>_<module>.py`.

## Running Tests

```bash
.venv/bin/python -m pytest tests/         # full suite
.venv/bin/python -m pytest tests/ -q      # quiet output
.venv/bin/python -m pytest tests/ -k core  # run only core tests
```

Tests must not depend on external resources or network access — all I/O is mocked.

## Test File Map

| Package        | Test file                    | Module under test                                    |
| -------------- | ---------------------------- | ---------------------------------------------------- |
| **command**    | `test_command_command.py`    | `command.execute` (`ExecuteCommand`)                 |
|                | `test_command_file.py`       | `command.file` (`ExecuteFile`, `UploadFile`)         |
|                | `test_command_load.py`       | `command.load` (`LoadPayload`)                       |
|                | `test_command_shell.py`      | `command.shell` (`LaunchShell`)                      |
| **config**     | `test_config_exceptions.py`  | `config.exceptions`                                  |
|                | `test_config_namespace.py`   | `config.enums` (`ClientFile`, `OperationCode`)       |
|                | `test_config_settings.py`    | `config.settings` (`Settings`, `BasePath`)           |
| **controller** | `test_controller_command.py` | `controller.command` (`call_command`)                |
|                | `test_controller_execute.py` | `controller.execute` (`call_execute`)                |
|                | `test_controller_exit.py`    | `controller.exit` (`call_exit`)                      |
|                | `test_controller_help.py`    | `controller.help` (`create_help_controller`)         |
|                | `test_controller_load.py`    | `controller.load` (`call_load`)                      |
|                | `test_controller_shell.py`   | `controller.shell` (`call_shell`)                    |
|                | `test_controller_upload.py`  | `controller.upload` (`call_upload`)                  |
| **core**       | `test_core_console.py`       | `core.console` (`Console`)                           |
|                | `test_core_parser.py`        | `core.parser` (`Parser`)                             |
|                | `test_core_prompt.py`        | `core.prompt` (`PromptCLI`)                          |
|                | `test_core_router.py`        | `core.router` (`Router`)                             |
|                | `test_core_session.py`       | `connection.shell_socket` (`ShellSocketConnection`)  |
| **util**       | `test_util_client.py`        | Client-script formatting utilities                   |
|                | `test_util_encoding.py`      | `util.encoding` (hex, base64)                        |
|                | `test_util_network.py`       | `util.network` (`await_connection`)                  |
|                | `test_util_parsing.py`       | `util.parsing` (`Parser`, `parse_command_arguments`) |
|                | `test_util_security.py`      | `util.security` (extension & path validation)        |
|                | `test_util_storage.py`       | `util.storage` (file loading & existence checks)     |

## Test File Structure

Each test file follows a consistent layout:

1. **Module docstring** — describes the module under test and scope of coverage.
2. **Fixtures** — `pytest` fixtures providing mocked dependencies.
3. **Test functions** — grouped by feature area with section headers.

## Docstring Convention

Test docstrings are **concise, single-sentence descriptions** of the expected behaviour:

```python
def test_connect_duplicate_raises_value_error(sample_controller: MagicMock) -> None:
    """Registering the same route twice must raise ``ValueError``."""
```

## Guidelines for Adding Tests

1. Follow the `test_<package>_<module>.py` naming convention.
2. Use `MagicMock` fixtures for all external dependencies (the codebase is synchronous — do **not** use `AsyncMock` or `@pytest.mark.asyncio`).
3. Write a single-sentence docstring per test describing the expected outcome.
4. Tests must be independent and runnable in any order.
5. Group related tests under section-header comments (`# === Tests: ... ===`).
