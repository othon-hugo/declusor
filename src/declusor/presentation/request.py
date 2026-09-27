from dataclasses import dataclass
from typing import cast

from declusor import contract, util


@dataclass(frozen=True)
class ControllerRequest[T: contract.ControllerArguments](contract.IControllerRequest[T]):
    """Concrete implementation of IControllerRequest using util.parse_command_arguments."""

    request_line: str = ""

    def parse_arguments(
        self,
        definitions: contract.ArgumentDefinitions,
        allow_unknown: bool = False,
    ) -> tuple[T, list[str]]:
        """Parse command-line arguments using util.parse_command_arguments."""

        parsed, unknown = util.parse_command_arguments(
            line=self.request_line,
            definitions=definitions,
            allow_unknown=allow_unknown,
        )

        return cast(T, parsed), unknown
