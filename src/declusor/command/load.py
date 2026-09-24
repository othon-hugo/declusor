from dataclasses import dataclass

from declusor import config, contract


@dataclass(frozen=True)
class LoadModuleDTO:
    """Data transfer object containing parameters for loading a client module.

    Encapsulates and validates the name of the module to load from the client's
    module repository. Prevents path traversal vulnerabilities.

    Attributes:
        module_name: Clean module identifier (e.g. ``discovery/sysinfo``).

    Raises:
        InvalidOperation: If ``module_name`` is empty or attempts directory traversal.
    """

    module_name: str

    def __post_init__(self) -> None:
        if not self.module_name or not self.module_name.strip():
            raise config.InvalidOperation("Module name cannot be empty.")

        clean_name = self.module_name.strip()

        if ".." in clean_name or clean_name.startswith("/") or "\\" in clean_name:
            raise config.InvalidOperation(f"Invalid module name '{self.module_name}': path traversal is not permitted.")


class LoadModule(contract.ICommand):
    """Load an operator-selected module into the remote client.

    Retrieves module payload from the active session's client file store,
    transmits the module definition across the network connection, and
    displays the resulting client response on the operator console.

    Attributes:
        dto: The validated parameters for this module load command.
    """

    def __init__(self, dto: LoadModuleDTO) -> None:
        """Initialize LoadModule with validated module parameters.

        Args:
            dto: Validated DTO containing the clean module identifier.
        """

        super().__init__()

        self._dto = dto
        self._module_name = dto.module_name

    @property
    def dto(self) -> LoadModuleDTO:
        """The command parameters."""

        return self._dto

    def send_request(self, session: contract.SessionContext) -> None:
        """Send the resolved module script to the remote client.

        Args:
            session: Active session providing connection transport and file store.

        Raises:
            CommandError: If the session file store is unavailable.
            ModuleNotFound: If the requested module file cannot be found.
            ConnectionClosed: If the connection is closed.
            ConnectionWriteError: If transmitting the module payload fails.
        """

        if session.files is None:
            raise config.CommandError("Client file store is not configured for this session.")

        module_bytes = session.files.load_module(self._module_name)
        session.connection.write(module_bytes)

    def read_response(self, session: contract.SessionContext) -> None:
        """Read and display the remote client's module registration response.

        Args:
            session: Active session providing connection and console interfaces.

        Raises:
            ConnectionClosed: If the remote peer terminates the connection unexpectedly.
        """

        for data in session.connection.read():
            session.console.write_binary_data(data)
