from dataclasses import dataclass

from declusor import config, contract, util
from declusor.command.base import BaseStreamCommand


@dataclass(frozen=True)
class LoadModuleDTO:
    """Data transfer object containing parameters for loading a client module.

    Encapsulates and validates the name of the module to load from the client's
    module repository. Prevents path traversal vulnerabilities.

    Raises:
        InvalidOperation: If ``module_name`` is empty or attempts directory traversal.
    """

    module_name: str
    """Clean module identifier (e.g. ``discovery/sysinfo``)."""

    def __post_init__(self) -> None:
        if not self.module_name or not self.module_name.strip():
            raise config.InvalidOperation("Module name cannot be empty.")

        clean_name = self.module_name.strip()

        if ".." in clean_name or clean_name.startswith("/") or "\\" in clean_name:
            raise config.InvalidOperation(f"Invalid module name '{self.module_name}': path traversal is not permitted.")


class LoadModule(BaseStreamCommand):
    """Load an operator-selected module into the remote client.

    Retrieves module payload from the active session's client file store,
    encodes and renders it via the client profile's ``LOAD_MODULE`` operation,
    transmits it across the network connection, and streams the client response.
    """

    def __init__(self, dto: LoadModuleDTO, /) -> None:
        """Initialize LoadModule with validated module parameters.

        Args:
            dto: Validated DTO containing the clean module identifier.
        """

        super().__init__()
        self._dto = dto

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Send the rendered module payload to the remote client.

        Args:
            session: Active session providing connection transport and file store.

        Raises:
            CommandError: If the session file store is unavailable.
            ModuleNotFound: If the requested module file cannot be found.
            InvalidOperation: If the profile cannot render the load operation command.
            ConnectionClosed: If the connection is closed.
            ConnectionWriteError: If transmitting the module payload fails.
        """

        if session.files is None:
            raise config.CommandError("Client file store is not configured for this session.")

        module_bytes = session.files.load_module(self._dto.module_name)
        module_b64 = util.convert_to_base64(module_bytes)

        rendered = session.connection.profile.render_operation_command(
            config.OperationCode.LOAD_MODULE,
            module_b64,
        )

        if not rendered:
            raise config.InvalidOperation("Failed to generate script data for module loading.")

        session.connection.write(rendered.encode())
