from dataclasses import dataclass

from declusor import config, contract, util

from .base import BaseStreamCommand


@dataclass(frozen=True)
class LoadModuleDTO:
    """Data transfer object containing parameters for loading a client module.

    Encapsulates and validates the name of the module to load from the client's
    module repository.

    Raises:
        InvalidOperation: If ``module_name`` is empty or consists solely of whitespace.
    """

    module_name: str
    """Non-empty module identifier or relative path (e.g. ``discovery/sysinfo``)."""

    def __post_init__(self) -> None:
        if not self.module_name or not self.module_name.strip():
            raise config.CommandValidationError(
                "Module name cannot be empty.",
                field="module_name",
                value=self.module_name,
            )

        object.__setattr__(self, "module_name", self.module_name.strip())


class LoadModule(BaseStreamCommand):
    """Load an operator-selected module into the remote client.

    Retrieves module payload from the active session's client file store,
    encodes and renders it via the client profile's ``LOAD_MODULE`` operation,
    transmits it across the network connection, and streams the client response.
    """

    def __init__(self, dto: LoadModuleDTO) -> None:
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
            config.CommandError: If the session plugin processor is unavailable.
            config.InvalidOperation: If the module is not found, attempts path traversal, or cannot be rendered.
            config.ConnectionClosed: If the connection is closed.
            config.ConnectionTimeoutError: If a transport operation times out.
            config.ConnectionError: If the connection is not ready or a write fails.
        """

        session.connection.write(self._payload(session).encode())

    def _payload(self, session: contract.SessionContext, /) -> str:
        if session.plugin is None:
            raise config.CommandError("Client file store is not configured for this session.")

        module_path = session.plugin.find_module(self._dto.module_name)

        if not module_path:
            raise config.InvalidOperation(f"Module {self._dto.module_name!r} could not be found.")

        if not util.validate_file_relative(module_path, session.plugin.filesystem.modules):
            raise config.InvalidOperation(f"Module path {self._dto.module_name!r} is outside the permitted modules directory.")

        module_bytes = session.plugin.load_module(module_path)
        module_b64 = util.convert_to_base64(module_bytes)

        rendered = session.connection.renderer.render_operation_command(
            config.OperationCode.LOAD_MODULE,
            module_b64,
        )

        if not rendered:
            raise config.InvalidOperation("Failed to generate script data for module loading.")

        return rendered
