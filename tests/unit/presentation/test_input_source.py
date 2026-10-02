from declusor import presentation


def test_terminal_input_source_read_command() -> None:
    """Verify read_command strips whitespace from injected reader."""

    prompts: list[str] = []

    def fake_reader(prompt: str) -> str:
        prompts.append(prompt)
        return "  command arg  "

    source = presentation.TerminalInputSource(reader=fake_reader)
    assert source.read_command("> ") == "command arg"
    assert prompts == ["> "]


def test_terminal_input_source_read_raw() -> None:
    """Verify read_raw appends newline to injected reader."""

    prompts: list[str] = []

    def fake_reader(prompt: str) -> str:
        prompts.append(prompt)
        return "command arg"

    source = presentation.TerminalInputSource(reader=fake_reader)
    assert source.read_raw("> ") == "command arg\n"
    assert prompts == ["> "]
