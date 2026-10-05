"""Unit tests for public package exports in declusor.core.__init__."""

from declusor import config, contract, core


class TestCoreExports:
    """Tests verifying public symbols exported by declusor.core."""

    def test_core_all__contains_all_seventeen_public_symbols(self) -> None:
        """The core package exports its components, exceptions, and official routes."""

        expected = [
            "Application",
            "DeclusorParser",
            "DuplicateRouteError",
            "EXIT_ROUTE",
            "LauncherDeliveryError",
            "LauncherRenderer",
            "OFFICIAL_ROUTES",
            "ParserError",
            "PluginError",
            "PluginManager",
            "PluginNotFoundError",
            "PluginRegistry",
            "PluginType",
            "PluginValidationError",
            "Router",
            "RouterError",
            "create_help_route",
        ]

        assert core.__all__ == expected

    def test_core_exports__every_symbol_in_all__is_accessible_on_module(self) -> None:
        """Every symbol listed in __all__ is an accessible attribute of the core module."""

        for name in core.__all__:
            assert hasattr(core, name), f"declusor.core is missing expected export: {name}"

    def test_core_exports__exception_reexports__match_config_exceptions(self) -> None:
        """Exception symbols re-exported from core are identical to their config definitions."""

        assert core.DuplicateRouteError is config.DuplicateRouteError
        assert core.LauncherDeliveryError is config.LauncherDeliveryError
        assert core.ParserError is config.ParserError
        assert core.PluginError is config.PluginError
        assert core.PluginNotFoundError is config.PluginNotFoundError
        assert core.PluginValidationError is config.PluginValidationError
        assert core.RouterError is config.RouterError

    def test_core_exports__component_classes__match_submodule_classes(self) -> None:
        """Component classes exported from core match their respective submodule definitions."""

        from declusor.core.application import Application
        from declusor.core.launcher import LauncherRenderer
        from declusor.core.parser import DeclusorParser
        from declusor.core.plugin import PluginManager, PluginRegistry
        from declusor.core.router import Router
        from declusor.core.routes import EXIT_ROUTE, OFFICIAL_ROUTES, create_help_route

        assert core.Application is Application
        assert core.LauncherRenderer is LauncherRenderer
        assert core.DeclusorParser is DeclusorParser
        assert core.PluginManager is PluginManager
        assert core.PluginRegistry is PluginRegistry
        assert core.Router is Router
        assert core.EXIT_ROUTE is EXIT_ROUTE
        assert core.OFFICIAL_ROUTES is OFFICIAL_ROUTES
        assert core.create_help_route is create_help_route

    def test_core_official_routes__names_and_registrations__are_available_for_plugins(self) -> None:
        """Official plugin routes form an immutable reusable route table."""

        assert set(core.OFFICIAL_ROUTES) == {"load", "command", "eval", "shell", "upload", "execute"}
        assert all(isinstance(registration, contract.RouteRegistration) for registration in core.OFFICIAL_ROUTES.values())
