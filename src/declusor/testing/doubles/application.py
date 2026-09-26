from declusor import contract, core
from declusor.testing.doubles.plugins import DummyPlugin


class DummyApplication:
    """Fully-typed test double for Application lifecycle in CLI and integration tests."""

    def __init__(
        self,
        manager: core.PluginManager | None = None,
        run_error: BaseException | None = None,
    ) -> None:
        if manager is None:
            self.manager: core.PluginManager = core.PluginManager()
            self.manager.register(DummyPlugin)
        else:
            self.manager = manager

        self.run_error: BaseException | None = run_error
        self.run_calls: list[contract.PluginConfig] = []

    def register_plugin(self, plugin: type[contract.IPlugin], /) -> None:
        """Register a client plugin in the manager."""

        self.manager.register(plugin)

    def run(self, config: contract.PluginConfig, /) -> None:
        """Simulate running the application lifecycle."""

        self.run_calls.append(config)

        if self.run_error is not None:
            raise self.run_error
