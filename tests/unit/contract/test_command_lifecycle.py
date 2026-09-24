from declusor import contract, testing


def test_command_execute_runs_send_request_before_read_response(
    test_session: contract.SessionContext,
) -> None:
    """ICommand.execute must invoke send_request before read_response."""

    command = testing.DummyCommand()
    test_session.execute(command)

    assert command.call_sequence == ["send_request", "read_response"]
