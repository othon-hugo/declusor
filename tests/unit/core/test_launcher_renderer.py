"""Unit tests for LauncherRenderer in declusor.core.launcher."""

from pathlib import Path

import pytest

from declusor import config, contract, core, testing


class TestLauncherRendererTerminal:
    """Tests verifying LauncherRenderer behavior when delivering to TERMINAL."""

    def test_render__terminal_mode_default__writes_script_payload_to_view(self) -> None:
        """LauncherRenderer delivers raw script payload to the view when output_mode is TERMINAL."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(script=b"echo 'launching declusor agent'")
        renderer.render(delivery)

        assert "echo 'launching declusor agent'" in view.messages

    def test_render__terminal_mode_with_wrapper__writes_wrapped_script_to_view(self) -> None:
        """LauncherRenderer delivers wrapped script to the view when wrapper_template is specified."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"python_code_here()",
            output_mode=config.LauncherOutputMode.TERMINAL,
            wrapper_template="python3 -c '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert "python3 -c 'python_code_here()'" in view.messages

    def test_render__terminal_mode_empty_script__writes_empty_string_to_view(self) -> None:
        """LauncherRenderer delivers empty string when script bytes are empty."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(script=b"")
        renderer.render(delivery)

        assert "" in view.messages

    def test_render__terminal_mode_positional_only__rejects_keyword_arguments(self) -> None:
        """The render method enforces positional-only parameter delivery."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)
        delivery = contract.LauncherDelivery(script=b"echo hi")

        with pytest.raises(TypeError, match="positional-only"):
            renderer.render(delivery=delivery)  # type: ignore[call-arg]


class TestLauncherRendererSilent:
    """Tests verifying LauncherRenderer behavior when delivering in SILENT mode."""

    def test_render__silent_mode__suppresses_all_view_output(self) -> None:
        """LauncherRenderer suppresses all output to view when output_mode is SILENT."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"sensitive_bootstrap_script",
            output_mode=config.LauncherOutputMode.SILENT,
        )
        renderer.render(delivery)

        assert len(view.messages) == 0

    def test_render__silent_mode_with_wrapper__suppresses_all_view_output(self) -> None:
        """LauncherRenderer suppresses output even if wrapper_template is supplied in SILENT mode."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"sh_code",
            output_mode=config.LauncherOutputMode.SILENT,
            wrapper_template="/bin/sh -c '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert len(view.messages) == 0


class TestLauncherRendererFile:
    """Tests verifying LauncherRenderer behavior when delivering to a FILE."""

    def test_render__file_mode_valid_path__writes_payload_to_file(self, tmp_path: Path) -> None:
        """LauncherRenderer writes script payload to the specified file path and leaves view untouched."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        target_file = tmp_path / "launcher.sh"
        delivery = contract.LauncherDelivery(
            script=b"#!/bin/bash\necho ready",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=target_file,
        )
        renderer.render(delivery)

        assert target_file.is_file()
        assert target_file.read_text(encoding="utf-8") == "#!/bin/bash\necho ready"
        assert len(view.messages) == 0

    def test_render__file_mode_nested_directories__creates_all_intermediate_parent_directories(self, tmp_path: Path) -> None:
        """LauncherRenderer recursively creates missing parent directories before writing file."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        target_file = tmp_path / "deep" / "nested" / "directory" / "launcher.sh"
        delivery = contract.LauncherDelivery(
            script=b"nested_content",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=target_file,
        )
        renderer.render(delivery)

        assert target_file.is_file()
        assert target_file.read_text(encoding="utf-8") == "nested_content"

    def test_render__file_mode_with_wrapper__writes_wrapped_payload_to_file(self, tmp_path: Path) -> None:
        """LauncherRenderer applies wrapper template before writing to target file."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        target_file = tmp_path / "wrapped_launcher.sh"
        delivery = contract.LauncherDelivery(
            script=b"payload_bytes",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=target_file,
            wrapper_template="eval '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert target_file.is_file()
        assert target_file.read_text(encoding="utf-8") == "eval 'payload_bytes'"

    def test_render__file_mode_missing_output_path__raises_launcher_delivery_error(self) -> None:
        """LauncherRenderer raises LauncherDeliveryError when output_mode is FILE but output_path is None."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"script_data",
            output_mode=config.LauncherOutputMode.TERMINAL,
        )
        object.__setattr__(delivery, "output_mode", config.LauncherOutputMode.FILE)
        object.__setattr__(delivery, "output_path", None)

        with pytest.raises(config.LauncherDeliveryError, match="Destination file path is required"):
            renderer.render(delivery)

    def test_render__file_mode_existing_directory_collision__raises_launcher_delivery_error_with_path(self, tmp_path: Path) -> None:
        """LauncherRenderer wraps OSError in LauncherDeliveryError with output_path attribute preserved."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        target_path = tmp_path / "colliding_directory"
        target_path.mkdir()

        delivery = contract.LauncherDelivery(
            script=b"echo err",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=target_path,
        )

        with pytest.raises(config.LauncherDeliveryError) as exc_info:
            renderer.render(delivery)

        assert exc_info.value.output_path == target_path
        assert isinstance(exc_info.value.__cause__, OSError)

    def test_render__file_mode_read_only_directory__raises_launcher_delivery_error(self, tmp_path: Path) -> None:
        """LauncherRenderer wraps PermissionError/OSError when target file directory is read-only."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        readonly_dir = tmp_path / "readonly_subdir"
        readonly_dir.mkdir(mode=0o555)

        target_file = readonly_dir / "launcher.sh"
        delivery = contract.LauncherDelivery(
            script=b"content",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=target_file,
        )

        try:
            with pytest.raises(config.LauncherDeliveryError) as exc_info:
                renderer.render(delivery)

            assert exc_info.value.output_path == target_file
            assert isinstance(exc_info.value.__cause__, OSError)
        finally:
            readonly_dir.chmod(0o755)


class TestLauncherRendererWrapper:
    """Tests verifying wrapper template substitutions in LauncherRenderer."""

    def test_render__wrapper_standard_dollar_placeholder__substitutes_script(self) -> None:
        """Wrapper template with '$DECLUSOR_SCRIPT' substitutes the raw script payload."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"import os; os.getpid()",
            wrapper_template="python3 -c '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert "python3 -c 'import os; os.getpid()'" in view.messages

    def test_render__wrapper_braced_dollar_placeholder__substitutes_script(self) -> None:
        """Wrapper template with '${DECLUSOR_SCRIPT}' substitutes the script payload."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"exec_target",
            wrapper_template="/bin/sh -c '${DECLUSOR_SCRIPT}'",
        )
        renderer.render(delivery)

        assert "/bin/sh -c 'exec_target'" in view.messages

    def test_render__wrapper_preserves_shell_variables__does_not_corrupt_dollar_vars(self) -> None:
        """Script containing internal shell variables ($PATH, $USER, etc.) is preserved verbatim."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        script = b'export PATH=$PATH:/custom/bin; echo "current user: $USER"'
        delivery = contract.LauncherDelivery(
            script=script,
            wrapper_template="bash -c '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert "bash -c 'export PATH=$PATH:/custom/bin; echo \"current user: $USER\"'" in view.messages

    def test_render__wrapper_multiple_dollar_placeholders__substitutes_all_occurrences(self) -> None:
        """Wrapper template containing multiple '$DECLUSOR_SCRIPT' substitutes all instances."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"script_data",
            wrapper_template="echo '$DECLUSOR_SCRIPT' ; eval '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert "echo 'script_data' ; eval 'script_data'" in view.messages

    def test_render__wrapper_escaped_dollar_syntax__preserves_literal_dollar(self) -> None:
        """Wrapper template with '$$' preserves literal dollar sign while substituting placeholder."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"script_payload",
            wrapper_template="echo '$$LITERAL' ; eval '$DECLUSOR_SCRIPT'",
        )
        renderer.render(delivery)

        assert "echo '$LITERAL' ; eval 'script_payload'" in view.messages

    def test_render__wrapper_none__returns_raw_payload_unchanged(self) -> None:
        """When wrapper_template is None, LauncherRenderer delivers the raw payload unchanged."""

        view = testing.DummyView()
        renderer = core.LauncherRenderer(view)

        delivery = contract.LauncherDelivery(
            script=b"plain_unwrapped_script",
            wrapper_template=None,
        )
        renderer.render(delivery)

        assert "plain_unwrapped_script" in view.messages


class TestLauncherRendererInitialization:
    """Tests verifying LauncherRenderer initialization invariants."""

    def test_launcher_renderer__init_positional_only__rejects_keyword_arguments(self) -> None:
        """LauncherRenderer __init__ requires positional-only view parameter."""

        view = testing.DummyView()

        with pytest.raises(TypeError, match="positional-only"):
            core.LauncherRenderer(view=view)  # type: ignore[call-arg]
