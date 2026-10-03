from pathlib import Path

import pytest

from declusor import contract, testing


class TestPluginConformanceHarness:
    """Verify behavior of the conformance validation harness."""

    def test_assert_conforms_to_client_plugin_with_dummy_plugin(self) -> None:
        """Ensure DummyPlugin satisfies all conformance invariants."""

        testing.assert_conforms_to_client_plugin(testing.DummyPlugin)

    def test_assert_conforms_to_plugin_alias(self) -> None:
        """Ensure assert_conforms_to_plugin alias executes the same verification."""

        testing.assert_conforms_to_plugin(testing.DummyPlugin)

    def test_assert_conforms_to_client_plugin_with_tmp_path(self, tmp_path: Path) -> None:
        """Ensure conformance validation creates stagers and validates filesystem structure."""

        testing.assert_conforms_to_client_plugin(testing.DummyPlugin, tmp_path=tmp_path)

    def test_rejection_of_invalid_class(self) -> None:
        """Ensure conformance verification raises AssertionError when passed an invalid class."""

        class InvalidPlugin:
            pass

        with pytest.raises(AssertionError, match="must subclass contract.IPluginExtension"):
            testing.assert_conforms_to_client_plugin(InvalidPlugin)  # type: ignore[arg-type]


class TestDummyPluginConformanceSuite(testing.PluginConformanceTestSuite[testing.DummyConfig]):
    """Verify standard conformance test suite inheritance using DummyPlugin."""

    @pytest.fixture
    def plugin_class(self) -> type[contract.IPluginExtension[testing.DummyConfig]]:
        """Provide DummyPlugin class for conformance suite execution."""

        return testing.DummyPlugin
