from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.controller import SessionContext
    from declusor.contract.router import IRouter


class ISessionRunner(ABC):
    """Contract for executing a workflow or interaction loop over an active session."""

    @abstractmethod
    def run(self, session: "SessionContext", router: "IRouter", /) -> None:
        """Execute the workflow on *session* using *router*.

        Args:
            session: Active session context holding connection, view, input, and files.
            router: Router resolving command routes to controllers.
        """

        raise NotImplementedError
