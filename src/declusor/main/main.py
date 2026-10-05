import contextlib
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from declusor import config, contract, core, transport

from .terminal import run_terminal_app


def run(
    argv: Sequence[str] | None = None,
    *,
    application: core.Application | None = None,
    plugin_manager: core.PluginManager | None = None,
    application_factory: Callable[..., core.Application] | None = None,
    transport_registry: transport.TransportLayerRegistry | None = None,
    listener_factory: Callable[[str, int], contract.ITransportListener] | None = None,
    launcher_renderer: core.LauncherRenderer | None = None,
    router: contract.IRouter | None = None,
    view: contract.IView | None = None,
    input_source: contract.IInputSource | None = None,
    session_runner: contract.ISessionRunner | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Main application composition root and entry point.

    Discovers plugins, parses command-line arguments via DeclusorParser,
    delegates execution to the configured view/mode runner, and maps exceptions
    to deterministic process exit codes (0, 1, 2).

    Args:
        argv: Optional command-line argument list. Defaults to sys.argv[1:].
        application: Optional application instance for test injection.
        plugin_manager: Optional pre-configured plugin manager instance.
        application_factory: Optional factory creating Application when omitted.
        transport_registry: Optional transport layer registry managing layered framing.
        listener_factory: Optional factory producing an ITransportListener for network connections.
        launcher_renderer: Optional renderer responsible for delivering client launcher.
        router: Optional command router resolving prompt input to controller actions.
        view: Optional presentation view interface handling output presentation.
        input_source: Optional operator input source interface.
        session_runner: Optional session runner executing prompt workflows.
        stdout: Optional text stream for standard output. Defaults to sys.stdout.
        stderr: Optional text stream for error output. Defaults to sys.stderr.

    Returns:
        Process exit code. ``0`` for success, ``1`` for runtime error, ``2`` for usage error.
    """

    args = list(argv) if argv is not None else sys.argv[1:]
    error_stream = stderr if stderr is not None else sys.stderr

    with (
        contextlib.redirect_stdout(stdout) if stdout is not None else contextlib.nullcontext(),
        contextlib.redirect_stderr(error_stream) if stderr is not None else contextlib.nullcontext(),
    ):
        try:
            active_transport_registry = transport_registry or (application.transport_registry if application is not None else None)
            manager = plugin_manager or (application.plugin_manager if application is not None else core.PluginManager().discover())
            parser = core.DeclusorParser(config.PROJECT_NAME, config.PROJECT_DESCRIPTION)

            plugin_config = parser.parse(manager, args, transport_registry=active_transport_registry)

            match plugin_config.mode:
                case config.ExecutionMode.CLI:
                    return run_terminal_app(
                        plugin_config,
                        plugin_manager=manager,
                        application=application,
                        application_factory=application_factory,
                        transport_registry=active_transport_registry,
                        listener_factory=listener_factory,
                        launcher_renderer=launcher_renderer,
                        router=router,
                        view=view,
                        input_source=input_source,
                        session_runner=session_runner,
                    )
                case _:
                    print(f"Execution mode {plugin_config.mode.value!r} is not supported yet.", file=error_stream)
                    return 1

        except config.ParserError as error:
            print(f"parser error: {error}", file=error_stream)
            return 2
        except config.DeclusorException as error:
            print(f"declusor error: {error}", file=error_stream)
            return 1
        except KeyboardInterrupt:
            return 0
        except SystemExit as error:
            if error.code is None:
                return 0

            if isinstance(error.code, int):
                return error.code

            print(error.code, file=error_stream)

            return 1
