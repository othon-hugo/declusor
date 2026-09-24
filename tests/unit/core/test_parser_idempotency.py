from pathlib import Path

from declusor import core
from plugins.shell_socket import ShellSocketPlugin


def test_parser_parse_is_idempotent(tmp_path: Path) -> None:
    """Calling parse() multiple times on the same DeclusorParser must not error."""

    registry = core.ClientRegistry()
    registry.register(ShellSocketPlugin)

    launcher_dir = tmp_path / "shell_socket" / "launchers"
    launcher_dir.mkdir(parents=True)
    (launcher_dir / "shell_socket_client.sh").write_text("test client", encoding="utf-8")

    argv = ["127.0.0.1", "8080", "--data-root", str(tmp_path)]

    parser = core.DeclusorParser(registry, name="test_app", description="test description")
    options1 = parser.parse(argv)
    assert options1["host"] == "127.0.0.1"
    assert options1["port"] == 8080

    # Second parse on the exact same parser instance
    options2 = parser.parse(argv)
    assert options2["host"] == "127.0.0.1"
    assert options2["port"] == 8080
