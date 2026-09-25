# Testing Support Package

The **testing** package provides reusable, fully-typed test infrastructure, doubles, and conformance suites for Declusor and plugin developers.

> [!NOTE]
> This package depends on `contract` and foundation layers to supply mock-free, deterministic test doubles and contract verification tools.

## Modules

| Module          | Responsibility                                                                       |
| --------------- | ------------------------------------------------------------------------------------ |
| `conformance`   | Conformance test harness and assertion suites for validating plugin contracts        |
| `doubles`       | Deterministic, fully-typed test doubles implementing all Declusor domain contracts   |
| `factories`     | Factory functions generating test sessions, configurations, and controller requests  |
| `pytest_plugin` | Pytest fixture definitions providing plug-and-play typed doubles for test suites     |

## Design Principles

1. **Deterministic Test Doubles** — eliminates fragile, untyped `MagicMock` setups in favor of predictable, contract-compliant doubles.
2. **Contract Conformance** — provides reusable test suites (`PluginConformanceTestSuite`) ensuring external plugins strictly satisfy host invariants.
3. **Strict Static Typing** — every fixture, double, and factory carries precise type annotations compatible with strict `mypy` checks.
4. **Isolated Test State** — doubles maintain explicit reset capabilities to prevent test contamination and state leakage across runs.
