from declusor import contract


class _BaseStreamCommand(contract.ICommand):
    """Base command for operations streaming binary chunks from client connection to view.

    Encapsulates the standard response loop that reads streamed output chunks from
    ``session.connection`` and forwards them directly to ``session.view.write_binary_data``.
    """

    def read_response(self, session: contract.SessionContext, /) -> None:
        """Stream response chunks from the remote client and write them to the view.

        Args:
            session: Active session context providing connection and view interfaces.

        Raises:
            ConnectionClosed: If the remote peer terminates the connection unexpectedly.
        """

        for data in session.connection.read():
            session.view.write_binary_data(data)
