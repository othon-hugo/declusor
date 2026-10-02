from pathlib import Path

import pytest

from declusor import config, contract, core, testing


def test_render_terminal_writes_to_view() -> None:
    """Verify LauncherRenderer delivers launcher text to view in TERMINAL mode."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    delivery = contract.LauncherDelivery(script=b"echo hello_world")
    renderer.render(delivery)

    assert "echo hello_world" in view.messages


def test_render_silent_suppresses_output() -> None:
    """Verify LauncherRenderer suppresses output in SILENT mode."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    delivery = contract.LauncherDelivery(
        script=b"echo secret_payload",
        output_mode=config.LauncherOutputMode.SILENT,
    )
    renderer.render(delivery)

    assert len(view.messages) == 0


def test_render_file_writes_payload_to_path(tmp_path: Path) -> None:
    """Verify LauncherRenderer writes launcher payload to the specified file path."""

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


def test_render_file_creates_parent_directories(tmp_path: Path) -> None:
    """Verify LauncherRenderer creates parent directories if they do not exist."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    target_file = tmp_path / "nested" / "sub" / "launcher.sh"
    delivery = contract.LauncherDelivery(
        script=b"echo nested",
        output_mode=config.LauncherOutputMode.FILE,
        output_path=target_file,
    )
    renderer.render(delivery)

    assert target_file.is_file()
    assert target_file.read_text(encoding="utf-8") == "echo nested"


def test_render_file_os_error_raises_declusor_exception(tmp_path: Path) -> None:
    """Verify LauncherRenderer wraps filesystem errors in DeclusorException."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    # Creating a directory at the target path causes write_text to fail with IsADirectoryError
    target_path = tmp_path / "already_a_dir"
    target_path.mkdir()

    delivery = contract.LauncherDelivery(
        script=b"echo err",
        output_mode=config.LauncherOutputMode.FILE,
        output_path=target_path,
    )

    with pytest.raises(config.DeclusorException, match="Failed to write client launcher"):
        renderer.render(delivery)


def test_render_wrapper_template_substitutes_script() -> None:
    """Verify LauncherRenderer applies wrapper template containing $DECLUSOR_SCRIPT."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    delivery = contract.LauncherDelivery(
        script=b"import sys; sys.exit(0)",
        wrapper_template="python3 -c '$DECLUSOR_SCRIPT'",
    )
    renderer.render(delivery)

    assert "python3 -c 'import sys; sys.exit(0)'" in view.messages


def test_render_wrapper_template_with_braced_placeholder() -> None:
    """Verify LauncherRenderer supports ${DECLUSOR_SCRIPT} braced placeholder."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    delivery = contract.LauncherDelivery(
        script=b"exec_me",
        wrapper_template="/bin/sh -c '${DECLUSOR_SCRIPT}'",
    )
    renderer.render(delivery)

    assert "/bin/sh -c 'exec_me'" in view.messages


def test_render_wrapper_preserves_shell_variables_in_script() -> None:
    """Verify script containing shell variables is preserved without corruption."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    script_with_vars = b'export PATH=$PATH:/usr/bin; echo "user: $USER"'
    delivery = contract.LauncherDelivery(
        script=script_with_vars,
        wrapper_template="bash -c '$DECLUSOR_SCRIPT'",
    )
    renderer.render(delivery)

    assert "bash -c 'export PATH=$PATH:/usr/bin; echo \"user: $USER\"'" in view.messages


def test_render_wrapper_with_file_output_mode(tmp_path: Path) -> None:
    """Verify wrapper template is applied when writing to file in FILE mode."""

    view = testing.DummyView()
    renderer = core.LauncherRenderer(view)

    target_file = tmp_path / "wrapped_launcher.sh"
    delivery = contract.LauncherDelivery(
        script=b"payload_content",
        output_mode=config.LauncherOutputMode.FILE,
        output_path=target_file,
        wrapper_template="eval '$DECLUSOR_SCRIPT'",
    )
    renderer.render(delivery)

    assert target_file.read_text(encoding="utf-8") == "eval 'payload_content'"
