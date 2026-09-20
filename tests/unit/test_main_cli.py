from declusor.main import cli


def test_main_returns_parser_error_exit_code() -> None:
    """Invalid command-line arguments must return a non-zero exit code."""

    exit_code = cli.main(("127.0.0.1", "9000", "--client", "unknown"))

    assert exit_code == 2


def test_main_can_parse_builtin_client(monkeypatch) -> None:
    """The composition root must register the built-in client before parsing."""

    captured: dict[str, object] = {}

    class FakeApplication:
        def parse(self, argv):
            captured["argv"] = argv
            return {"host": "127.0.0.1", "port": 9000, "client": object()}

        def run(self, options) -> None:
            captured["options"] = options

    monkeypatch.setattr(cli, "create_application", lambda: FakeApplication())

    assert cli.main(("127.0.0.1", "9000")) == 0
    assert captured["argv"] == ("127.0.0.1", "9000")
