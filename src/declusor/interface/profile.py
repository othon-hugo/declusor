from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor import config


class IProfile(ABC):
    @property
    @abstractmethod
    def bufsize(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float | None:
        raise NotImplementedError

    @abstractmethod
    def load_payload(self, payload_name: str, /) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def load_library(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def format_operation_script(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def format_client_script(self, host: str, port: int, /) -> str:
        raise NotImplementedError
