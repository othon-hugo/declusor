from __future__ import annotations

from typing import TYPE_CHECKING

from declusor import contract, core

if TYPE_CHECKING:
    from declusor import transport


class DummyApplication(core.Application):
    """Fully-typed test double for Application lifecycle in CLI and integration tests."""

    def __init__(
        self,
        manager: core.PluginManager | None = None,
        run_error: BaseException | None = None,
        *,
        router: contract.IRouter | None = None,
        view: contract.IView | None = None,
        session_runner: contract.ISessionRunner | None = None,
        input_source: contract.IInputSource | None = None,
        transport_registry: transport.TransportLayerRegistry | None = None,
    ) -> None:
        from declusor import transport
        from declusor.testing.doubles.input_source import DummyInputSource
        from declusor.testing.doubles.router import DummyRouter
        from declusor.testing.doubles.runner import DummySessionRunner
        from declusor.testing.doubles.view import DummyView

        mgr = manager if manager is not None else core.PluginManager()
        super().__init__(
            router or DummyRouter(),
            view or DummyView(),
            plugin_manager=mgr,
            session_runner=session_runner or DummySessionRunner(),
            input_source=input_source or DummyInputSource(),
            transport_registry=transport_registry or transport.default_transport_registry(),
        )
        self.manager: core.PluginManager = mgr
        self.run_error: BaseException | None = run_error
        self.run_calls: list[contract.PluginConfig[contract.ParsedArguments]] = []

    @property
    def plugin_manager(self) -> core.PluginManager:
        """Return the plugin manager."""

        return self.manager

    @property
    def router(self) -> contract.IRouter:
        """Return the injected router."""

        return self._router

    @property
    def view(self) -> contract.IView:
        """Return the injected view."""

        return self._view

    @property
    def input_source(self) -> contract.IInputSource | None:
        """Return the injected input source."""

        return self._input_source

    @property
    def session_runner(self) -> contract.ISessionRunner:
        """Return the injected session runner."""

        return self._session_runner

    def register_plugin(self, plugin: type[contract.IPluginExtension[contract.ParsedArguments]], /) -> None:
        """Register a client plugin in the manager."""

        self.manager.register(plugin)

    def run(self, config: contract.PluginConfig[contract.ParsedArguments], /) -> None:
        """Simulate running the application lifecycle."""

        self.run_calls.append(config)

        if self.run_error is not None:
            raise self.run_error
