# App Package

The **app** package provides concrete application implementations and target flavors for Declusor.

> [!NOTE]
> Base application lifecycle and protocol interfaces live in `core.application`. Dedicated application flavors (such as terminal REPL or future API/MCP targets) are encapsulated within this package.

## Modules

| Module     | Responsibility                                                                 |
| ---------- | ------------------------------------------------------------------------------ |
| `terminal` | Specialized interactive terminal application, prompt runner wiring, and factories |

## Design Principles

1. **Concrete Target Isolation** — encapsulates specific runtime presentation and input dependencies away from generic core services.
2. **Pre-Wired Bootstrap** — provides ergonomic factory functions (`create_terminal_application`, `create_application`) with sensible defaults and automated plugin discovery.
3. **Extensible Topology** — designed for modular growth where new application targets (e.g. MCP, headless scripts, API daemons) can be introduced as sibling modules without modifying existing application workflows.
