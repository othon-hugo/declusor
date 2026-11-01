"""Unit tests for clipboard utilities in declusor.util.clipboard."""

import base64

import pytest

from declusor import config, testing, util


class TestBuildOsc52Sequence:
    """Tests verifying OSC 52 terminal sequence construction."""

    def test_build_osc52_sequence__ascii_string__returns_osc52_bytes(self) -> None:
        """ASCII payload is converted to base64 and wrapped in OSC 52 envelope."""

        payload = b"hello world"
        result = util.build_osc52_sequence(payload)

        b64_str = base64.b64encode(payload).decode("ascii")
        expected = f"\x1b]52;c;{b64_str}\x07".encode("ascii")

        assert result == expected

    def test_build_osc52_sequence__unicode_payload__encodes_utf8_base64(self) -> None:
        """Unicode UTF-8 byte payload is wrapped in OSC 52 envelope."""

        payload = "çãõ-launcher-payload".encode()
        result = util.build_osc52_sequence(payload)

        b64_str = base64.b64encode(payload).decode("ascii")
        expected = f"\x1b]52;c;{b64_str}\x07".encode("ascii")

        assert result == expected

    def test_build_osc52_sequence__empty_bytes__returns_osc52_empty_envelope(self) -> None:
        """Empty payload produces empty base64 OSC 52 envelope."""

        result = util.build_osc52_sequence(b"")

        assert result == b"\x1b]52;c;\x07"


class TestGetClipboardCommands:
    """Tests verifying candidate clipboard commands determination across platforms."""

    def test_get_clipboard_commands__darwin__returns_pbcopy(self) -> None:
        """macOS (darwin) platform returns pbcopy command."""

        commands = util.get_clipboard_commands(platform="darwin")

        assert commands == [["pbcopy"]]

    def test_get_clipboard_commands__win32__returns_clip_exe(self) -> None:
        """Windows (win32) platform returns clip.exe command."""

        commands = util.get_clipboard_commands(platform="win32")

        assert commands == [["clip.exe"]]

    def test_get_clipboard_commands__cygwin__returns_clip_exe(self) -> None:
        """Cygwin platform returns clip.exe command."""

        commands = util.get_clipboard_commands(platform="cygwin")

        assert commands == [["clip.exe"]]

    def test_get_clipboard_commands__linux_with_wayland__prioritizes_wl_copy(self) -> None:
        """Linux with WAYLAND_DISPLAY prioritizes wl-copy over xclip and xsel."""

        env = {"WAYLAND_DISPLAY": "wayland-0"}
        commands = util.get_clipboard_commands(platform="linux", env=env)

        assert commands == [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "-b", "-i"],
        ]

    def test_get_clipboard_commands__linux_without_wayland__prioritizes_xclip(self) -> None:
        """Linux without WAYLAND_DISPLAY prioritizes xclip over xsel and wl-copy."""

        env: dict[str, str] = {}
        commands = util.get_clipboard_commands(platform="linux", env=env)

        assert commands == [
            ["xclip", "-selection", "clipboard"],
            ["xsel", "-b", "-i"],
            ["wl-copy"],
        ]

    def test_get_clipboard_commands__unsupported_platform__returns_empty_list(self) -> None:
        """Unsupported platform returns an empty list of commands."""

        commands = util.get_clipboard_commands(platform="unknown_os")

        assert commands == []

    def test_get_clipboard_commands__default_env_resolution(self) -> None:
        """Omitting env parameter resolves commands using os.environ."""

        commands = util.get_clipboard_commands(platform="linux")

        assert len(commands) == 3
        assert any("wl-copy" in cmd for cmd in commands)


class TestDefaultCommandRunner:
    """Tests verifying default subprocess command execution wrapper."""

    def test_default_command_runner__nonexistent_binary__returns_false(self) -> None:
        """Nonexistent executable returns False without uncaught exceptions."""

        result = util.default_command_runner(["nonexistent_command_12345"], b"data")

        assert result is False

    def test_default_command_runner__failing_command__returns_false(self) -> None:
        """Executable exiting with non-zero code returns False."""

        result = util.default_command_runner(["sh", "-c", "exit 1"], b"data")

        assert result is False

    def test_default_command_runner__successful_command__returns_true(self) -> None:
        """Executable exiting with zero code returns True."""

        result = util.default_command_runner(["sh", "-c", "cat > /dev/null"], b"data")

        assert result is True


class TestCopyToClipboard:
    """Tests verifying copy_to_clipboard behavior, fallbacks, and error reporting."""

    def test_copy_to_clipboard__with_view__emits_osc52_sequence_to_view(self) -> None:
        """copy_to_clipboard writes OSC 52 sequence directly to view binary data."""

        view = testing.DummyView()
        util.copy_to_clipboard("launcher script text", view=view)

        assert len(view.binary_data) == 1
        assert view.binary_data[0].startswith(b"\x1b]52;c;")
        assert view.binary_data[0].endswith(b"\x07")
        assert len(view.messages) == 0

    def test_copy_to_clipboard__with_command_runner__executes_candidate_command(self) -> None:
        """copy_to_clipboard passes command array and binary payload to injected runner."""

        recorded: list[tuple[list[str], bytes]] = []

        def dummy_runner(args: list[str], payload: bytes) -> bool:
            recorded.append((args, payload))
            return True

        view = testing.DummyView()
        util.copy_to_clipboard(
            "echo test",
            view=view,
            command_runner=dummy_runner,
            platform="darwin",
        )

        assert len(recorded) == 1
        assert recorded[0] == (["pbcopy"], b"echo test")

    def test_copy_to_clipboard__first_command_succeeds__stops_trying_subsequent(self) -> None:
        """When the primary command succeeds, subsequent candidate commands are skipped."""

        attempted: list[list[str]] = []

        def dummy_runner(args: list[str], payload: bytes) -> bool:
            attempted.append(args)
            return True

        view = testing.DummyView()
        util.copy_to_clipboard(
            "payload",
            view=view,
            command_runner=dummy_runner,
            platform="linux",
            env={"WAYLAND_DISPLAY": "wayland-0"},
        )

        assert attempted == [["wl-copy"]]

    def test_copy_to_clipboard__first_command_fails__tries_fallback_command(self) -> None:
        """When the primary command fails, execution falls back to the next available command."""

        attempted: list[list[str]] = []

        def dummy_runner(args: list[str], payload: bytes) -> bool:
            attempted.append(args)
            return args[0] == "xclip"

        view = testing.DummyView()
        util.copy_to_clipboard(
            "payload",
            view=view,
            command_runner=dummy_runner,
            platform="linux",
            env={"WAYLAND_DISPLAY": "wayland-0"},
        )

        assert attempted == [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
        ]

    def test_copy_to_clipboard__command_runner_raises_exception__continues_to_next(self) -> None:
        """If a command runner raises an unexpected exception, it continues to fallback."""

        attempted: list[list[str]] = []

        def dummy_runner(args: list[str], payload: bytes) -> bool:
            attempted.append(args)
            if args[0] == "wl-copy":
                raise RuntimeError("compositor disconnected")
            return True

        view = testing.DummyView()
        util.copy_to_clipboard(
            "payload",
            view=view,
            command_runner=dummy_runner,
            platform="linux",
            env={"WAYLAND_DISPLAY": "wayland-0"},
        )

        assert len(attempted) == 2
        assert attempted[0] == ["wl-copy"]
        assert attempted[1] == ["xclip", "-selection", "clipboard"]

    def test_copy_to_clipboard__emit_osc52_disabled_and_runner_succeeds__does_not_raise(self) -> None:
        """When OSC 52 is disabled, successful command runner satisfies delivery."""

        view = testing.DummyView()

        def dummy_runner(args: list[str], payload: bytes) -> bool:
            return True

        util.copy_to_clipboard(
            "script_body",
            view=view,
            command_runner=dummy_runner,
            platform="darwin",
            emit_osc52=False,
        )

        assert len(view.binary_data) == 0

    def test_copy_to_clipboard__all_mechanisms_fail__raises_launcher_delivery_error(self) -> None:
        """When OSC 52 is disabled and all OS commands fail, LauncherDeliveryError is raised."""

        def failing_runner(args: list[str], payload: bytes) -> bool:
            return False

        with pytest.raises(config.LauncherDeliveryError, match="all clipboard mechanisms failed"):
            util.copy_to_clipboard(
                "script_body",
                view=None,
                command_runner=failing_runner,
                platform="unknown_os",
                emit_osc52=False,
            )

    def test_copy_to_clipboard__view_write_fails_and_runner_fails__raises_launcher_delivery_error(self) -> None:
        """When view.write_binary_data raises and commands fail, LauncherDeliveryError is raised."""

        class BrokenView:
            def write_binary_data(self, data: bytes, /) -> None:
                raise OSError("broken pipe")

        def failing_runner(args: list[str], payload: bytes) -> bool:
            return False

        with pytest.raises(config.LauncherDeliveryError, match="all clipboard mechanisms failed"):
            util.copy_to_clipboard(
                "script_body",
                view=BrokenView(),
                command_runner=failing_runner,
                platform="darwin",
            )

    def test_copy_to_clipboard__positional_only_text__rejects_keyword_arguments(self) -> None:
        """The copy_to_clipboard function enforces positional-only text argument."""

        with pytest.raises(TypeError, match="positional-only"):
            util.copy_to_clipboard(text="script")  # type: ignore[call-arg]
