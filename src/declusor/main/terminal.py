import inspect
from collections.abc import Callable, Mapping
from typing import Any

from declusor import app, contract, core, transport


def run_terminal_app(
    plugin_config: contract.PluginConfig[contract.ParsedArguments],
    *,
    plugin_manager: core.PluginManager | None = None,
    application: core.Application | None = None,
    application_factory: Callable[..., core.Application] | None = None,
    transport_registry: transport.TransportLayerRegistry | None = None,
    listener_factory: Callable[[str, int], contract.ITransportListener] | None = None,
    launcher_renderer: core.LauncherRenderer | None = None,
    router: contract.IRouter | None = None,
    view: contract.IView | None = None,
    input_source: contract.IInputSource | None = None,
    session_runner: contract.ISessionRunner | None = None,
) -> int:
    """Compose and run an interactive terminal REPL session.

    Args:
        plugin_config: Validated client plugin configuration.
        plugin_manager: Optional pre-discovered plugin manager.
        application: Optional application instance to execute.
        application_factory: Optional factory producing Application when omitted.
        transport_registry: Optional transport layer registry managing layered framing.
        listener_factory: Optional factory producing an ITransportListener for network connections.
        launcher_renderer: Optional renderer responsible for delivering client launcher.
        router: Optional command router resolving prompt input to controller actions.
        view: Optional presentation view interface handling output presentation.
        input_source: Optional operator input source interface.
        session_runner: Optional session runner executing prompt workflows.

    Returns:
        Process exit code. ``0`` indicates successful completion.
    """

    factory = application_factory or app.create_terminal_application

    if application is not None:
        active_app = application
    else:
        factory_kwargs: dict[str, Any] = {"plugin_manager": plugin_manager}

        if transport_registry is not None:
            factory_kwargs["transport_registry"] = transport_registry

        if listener_factory is not None:
            factory_kwargs["listener_factory"] = listener_factory

        if launcher_renderer is not None:
            factory_kwargs["launcher_renderer"] = launcher_renderer

        if router is not None:
            factory_kwargs["router"] = router

        if view is not None:
            factory_kwargs["view"] = view

        if input_source is not None:
            factory_kwargs["input_source"] = input_source

        if session_runner is not None:
            factory_kwargs["session_runner"] = session_runner

        active_app = _create_application(factory, factory_kwargs)

    active_app.run(plugin_config)

    return 0


def _create_application(
    factory: Callable[..., core.Application],
    kwargs: Mapping[str, Any],
) -> core.Application:
    """Invoke application factory passing only keyword arguments matching its signature."""

    parameters = inspect.signature(factory).parameters

    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values()):
        return factory(**kwargs)

    accepted_keywords = {
        name
        for name, param in parameters.items()
        if param.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }

    filtered_kwargs = {name: val for name, val in kwargs.items() if name in accepted_keywords}

    return factory(**filtered_kwargs)
