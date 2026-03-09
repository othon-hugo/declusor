# Tests Directory

The **tests** directory contains the complete test suite for Declusor. Test files mirror the source-code package structure using the naming convention `test_<package>_<module>.py`.

## Running Tests

```bash
.venv/bin/python -m pytest tests/          # full suite
.venv/bin/python -m pytest tests/ -q       # quiet output
.venv/bin/python -m pytest tests/ -k core  # run only core tests
```

Tests must not depend on external resources or network access — all I/O is mocked.

## Test File Structure

Each test file follows a consistent layout:

1. **Module docstring**: describes the module under test and scope of coverage.
2. **Fixtures**: `pytest` fixtures providing mocked dependencies.
3. **Test functions**: grouped by feature area with section headers.

## Docstring Convention

Test docstrings are **concise, single-sentence descriptions** of the expected behaviour:

```python
def test_connect_duplicate_raises_value_error(sample_controller: Callable) -> None:
    """Registering the same route twice must raise ``ValueError``."""
```

## Guidelines for Adding Tests

1. Follow the `test_<package>_<module>.py` naming convention.
2. Use custom mocks from `declusor.mock` for all external dependencies.
3. Do **not** use `MagicMock`, `patch`, or `monkeypatch`.
4. Do **not** use `AsyncMock` or `@pytest.mark.asyncio` — the codebase is synchronous.
5. Write a single-sentence docstring per test describing the expected outcome.
6. Tests must be independent and runnable in any order.
7. Group related tests under section-header comments.

   ```python
    # =============================================================================
    # Tests: <class>.<method> (<quick description>)
    # =============================================================================
   ```
