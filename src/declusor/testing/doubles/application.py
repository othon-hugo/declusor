from declusor import contract, core


class DummyApplication(core.Application):
    """Fully-typed test double for Application lifecycle in CLI and integration tests."""

    def __init__(
        self,
        manager: core.PluginManager | None = None,
        run_error: BaseException | None = None,
    ) -> None:
        self.manager: core.PluginManager = manager if manager is not None else core.PluginManager()
        self.run_error: BaseException | None = run_error
        self.run_calls: list[contract.PluginConfig[contract.ParsedArguments]] = []

    @property
    def plugin_manager(self) -> core.PluginManager:
        """Return the plugin manager."""

        return self.manager

    def register_plugin(self, plugin: type[contract.IPluginExtension[contract.ParsedArguments]], /) -> None:
        """Register a client plugin in the manager."""

        self.manager.register(plugin)

    def run(self, config: contract.PluginConfig[contract.ParsedArguments], /) -> None:
        """Simulate running the application lifecycle."""

        self.run_calls.append(config)

        if self.run_error is not None:
            raise self.run_error
