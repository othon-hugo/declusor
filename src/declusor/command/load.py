from declusor import config, contract


class LoadModule(contract.ICommand):
    """Send an operator-selected module to the remote client.

    Modules are resolved by the active connection's client file store and are
    distinct from libraries, which are loaded automatically during startup.
    """

    def __init__(
        self,
        connection: contract.IConnection,
        console: contract.IConsole,
        files: contract.IClientFileStore,
        /,
        *,
        module_name: str,
    ) -> None:
        """[...]

        Args:
            connection: [...]
            console: [...]
            files: [...]
            module_name: [...]
        """

        super().__init__(connection, console, files)

        if self._files is None:
            raise config.CommandError("[...]")

        self._module_name = module_name

    def send_request(self) -> None:
        """[...]"""

        self._connection.write(self._files.load_module(self._module_name))

    def read_response(self) -> None:
        """[...]"""

        for data in self._connection.read():
            self._console.write_binary_data(data)
