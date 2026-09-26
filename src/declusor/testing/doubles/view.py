from declusor import contract


class DummyView(contract.IView):
    """Fully-typed in-memory view capturing all presentation output."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.binary_data: list[bytes] = []
        self.errors: list[str | BaseException] = []
        self.warnings: list[str | BaseException] = []
        self.info_messages: list[str] = []
        self.success_messages: list[str] = []

    def write_message(self, message: str, /) -> None:
        """Capture generic message."""

        self.messages.append(message)

    def write_error(self, message: str | BaseException, /) -> None:
        """Capture error output message or exception."""

        self.errors.append(message)

    def write_warning(self, message: str | BaseException, /) -> None:
        """Capture warning output message or exception."""

        self.warnings.append(message)

    def write_info(self, message: str, /) -> None:
        """Capture info output message."""

        self.info_messages.append(message)

    def write_success(self, message: str, /) -> None:
        """Capture success output message."""

        self.success_messages.append(message)

    def write_binary_data(self, data: bytes, /) -> None:
        """Capture transmitted raw bytes."""

        self.binary_data.append(data)
