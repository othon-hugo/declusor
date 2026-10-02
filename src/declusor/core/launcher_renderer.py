from declusor import config, contract, util


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

        payload = delivery.script.decode("utf-8")
        output = self._apply_wrapper(payload, delivery.wrapper_template)

        match delivery.output_mode:
            case config.LauncherOutputMode.TERMINAL:
                self._view.write_message(output)
            case config.LauncherOutputMode.SILENT:
                pass
            case config.LauncherOutputMode.FILE:
                if delivery.output_path is None:
                    raise config.DeclusorException("Destination file path is required when output_mode is FILE.")

                try:
                    delivery.output_path.parent.mkdir(parents=True, exist_ok=True)
                    delivery.output_path.write_text(output, encoding="utf-8")
                except OSError as error:
                    raise config.DeclusorException(f"Failed to write client launcher to {delivery.output_path}: {error}") from error

    @staticmethod
    def _apply_wrapper(payload: str, template: str | None) -> str:
        """Substitute payload into wrapper template if provided.

        Args:
            payload: Decoded client launcher bootstrap script.
            template: Optional shell wrapper template containing '$DECLUSOR_SCRIPT'.

        Returns:
            Wrapped launcher string, or raw payload if template is None.
        """

        if template is None:
            return payload

        return util.format_template(template, DECLUSOR_SCRIPT=payload)
