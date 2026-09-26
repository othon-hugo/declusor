from declusor import contract, testing


def test_session_context_initialization_and_properties(
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_input_source: testing.DummyInputSource,
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """SessionContext should properly hold and expose connection, view, input, and files."""

    session = contract.SessionContext(
        connection=dummy_connection,
        view=dummy_view,
        input=dummy_input_source,
        files=dummy_file_store,
    )

    assert session.connection is dummy_connection
    assert session.view is dummy_view
    assert session.input is dummy_input_source
    assert session.files is dummy_file_store


def test_session_context_execute_invokes_command_execute(
    test_session: contract.SessionContext,
) -> None:
    """session.execute(command) must dispatch command.execute(session)."""

    command = testing.DummyCommand()
    test_session.execute(command)

    assert command.call_sequence == ["send_request", "read_response"]
