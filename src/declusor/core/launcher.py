from declusor import config, contract


class LauncherRenderer:
    """Applies delivery mode and optional shell wrapper to client launchers."""

    def __init__(self, view: contract.IView, /) -> None:
        """Create a LauncherRenderer with the specified operator view.

        Args:
            view: Operator view interface handling output presentation.
        """

        self._view = view

    def render(self, delivery: contract.LauncherDelivery, /) -> None:
        """Render and deliver the client launcher according to its envelope.

        Args:
            delivery: Immutable envelope carrying launcher payload and delivery options.

        Raises:
            DeclusorException: If delivering the launcher to a file fails.
        """

        output = delivery.wrapped_text

        match delivery.output_mode:
            case config.LauncherOutputMode.TERMINAL:
                self._view.write_message(output)
            case config.LauncherOutputMode.SILENT:
                pass
            case config.LauncherOutputMode.FILE:
                if delivery.output_path is None:
                    raise config.LauncherDeliveryError("Destination file path is required when output_mode is FILE.")

                try:
                    delivery.output_path.parent.mkdir(parents=True, exist_ok=True)
                    delivery.output_path.write_text(output, encoding="utf-8")
                except OSError as error:
                    raise config.LauncherDeliveryError(
                        f"Failed to write client launcher to {delivery.output_path}: {error}",
                        output_path=delivery.output_path,
                    ) from error
