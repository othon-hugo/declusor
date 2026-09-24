# Declusor

A fast, modular, and extensible reverse-shell framework and payload delivery handler for security professionals and CTF players.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![PyPI version](https://img.shields.io/pypi/v/declusor.svg)](https://pypi.org/project/declusor/)
[![Typing: Strict](https://img.shields.io/badge/typing-strict-brightgreen.svg)](https://mypy.readthedocs.io/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://docs.astral.sh/ruff/)

## The Problem & Why I Built Declusor

If you have spent any time in capture-the-flag (CTF) competitions or authorized penetration testing engagements, you already know the frustration:

- **The Netcat Fragility Trap**: You finally achieve remote code execution, catch the reverse shell with `nc -lvnp 4444`, instinctively press `Up-Arrow` to recall a command or hit `Ctrl+C` to stop a running binary — and your entire session instantly evaporates. You scramble through cheat sheets to spawn a pseudo-terminal with Python `pty.spawn()`, struggle with raw terminal dimensions, and resort to messy base64 copy-paste gymnastics just to push an enumeration script.
- **The Heavyweight C2 Overkill**: You consider reaching for a full-scale Command & Control (C2) framework, only to realize you have to configure multi-container Docker compose stacks, spin up background databases, and manage team servers. It is excessive overhead when all you need is a fast, rock-solid, and interactive handler for an engagement.
- **The Brittle One-Off Scripts**: Custom listener scripts often lack rigorous error handling, have hardcoded protocol assumptions, and crash as soon as they encounter unexpected binary bytes or a closed socket.

I built **Declusor** because I wanted to end that compromise once and for all.

Declusor bridges the gap: it delivers the **zero-overhead, single-command simplicity** of netcat combined with the **ergonomics of a modern interactive CLI**. You get full readline history, intelligent tab-completion for remote and local paths, in-memory script staging, and modular, swappable client transports — all built on a strict, typed architecture that will not crash when you need it most.

## Visual Overview & Interactive Demo

<!--
  ASSET PLACEHOLDER:
  Replace the image below with your high-resolution terminal screenshot at 'docs/assets/overview.png'.
  See docs/assets/README.md for instructions and recommended dimensions.
-->
<p align="center">
  <img src="docs/assets/overview.png" alt="Declusor Overview" width="900" onerror="this.style.display='none'"/>
</p>

<!--
  ASSET PLACEHOLDER:
  Replace the GIF below with your custom recording at 'docs/assets/demo.gif'.
  Follow the VHS tape script in docs/assets/README.md to record an animated terminal walkthrough.
-->
<p align="center">
  <img src="docs/assets/demo.gif" alt="Declusor Interactive Demo" width="900" onerror="this.onerror=null;this.src='https://i.imgur.com/Wsw2l90.gif';"/>
  <br>
  <em>Declusor in action: Catching an incoming reverse shell, using tab-completion, streaming command output, and loading on-demand reconnaissance modules.</em>
</p>

> [!WARNING]
> **Legal Disclaimer**: Declusor is intended solely for educational purposes and authorized security research. The authors assume no liability for misuse. Executing this software against systems without explicit, prior written authorization is strictly prohibited.

## Key Capabilities

### 🎮 Operator Experience

- **Smart Interactive REPL**: Built-in tab-completion for commands, target arguments, and local files.
- **Persistent Command History**: Maintains command recall across operations, eliminating accidental disconnections from `Up-Arrow` or unhandled key sequences.
- **Clean Stream Presentation**: Real-time output streaming with dedicated diagnostic reporting and structured tabular formatting.

### ⚡ Tactical Operations

- **Single Command Execution**: Execute arbitrary commands on the remote target with framed stream delivery.
- **In-Memory Script Execution**: Stream local scripts directly into remote execution memory without writing forensic artifacts to disk.
- **Binary File Transfers**: Upload reconnaissance and privilege-escalation binaries through framed chunking.
- **Modular Post-Exploitation**: Execute modular payloads from local directories with clean parameter isolation.
- **Interactive Shell Spawning**: Drop into an interactive shell session whenever you need unrestricted access.

### 🧩 Autonomous Plugin Architecture

- **Multi-Tier Discovery**: Seamlessly loads built-in plugins, pip-installed packages (`declusor.plugins` entry points), and on-demand drop-in directories (`--plugin-dir`).
- **Completely Decoupled Transports**: Shipped with native Linux `/dev/tcp` (`shell_socket`) and cross-platform Python (`py_socket`) clients with zero coupling to core engine code.
- **First-Class Testing SDK**: Ships with `declusor.testing`, providing mock-free, contract-compliant test doubles and automated plugin conformance test suites.

## Getting Started

### Prerequisites

- **Python 3.11+** installed on the host operator machine.
- **Target environment**:
  - Unix-like system with Bash for `shell_socket`.
  - Any system with Python 3.6+ (Linux, macOS, Windows) for `py_socket`.

### Installation

#### Option A: Install from PyPI

```bash
pip install declusor
```

#### Option B: Fast Setup with `uv` (Recommended for Development)

Clone the repository and run `make install`:

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor

# Sync dependencies and install native plugins automatically
make install
```

#### Option C: Manual Setup with `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,testing]"
make install-plugins
```

## Real-World Workflow & Usage

### 1. Start the Listener

Start Declusor by specifying your local listening IP and port:

```bash
# Default listener (uses native shell_socket client)
declusor 0.0.0.0 4444

# Select the cross-platform Python client
declusor 0.0.0.0 4444 --client py_socket

# Load external custom plugins from an operator directory
declusor 0.0.0.0 4444 --plugin-dir ~/custom_plugins --client my_agent
```

On startup, Declusor initializes the listener and **prints the exact one-liner launcher command** to run on your target.

### 2. Built-in Client Transports

| Client Plugin     | Flag              | Target OS             | Execution Mechanism                                                    |
| :---------------- | :---------------- | :-------------------- | :--------------------------------------------------------------------- |
| **Shell Socket**  | `-c shell_socket` | Linux / POSIX         | Native `/dev/tcp` file descriptor; zero external dependencies          |
| **Python Socket** | `-c py_socket`    | Linux, macOS, Windows | In-memory `exec()` with persistent session scope & subprocess fallback |

### 3. Interact with the Session

Once your target connects back, Declusor drops you into an interactive session:

```text
[declusor] help
help    : Display detailed information about available commands or a specific command.
load    : Load a payload module from your local system and execute it on the remote system.
command : Execute a single command on the remote system.
shell   : Initiate an interactive shell session on the remote system.
upload  : Upload a file from the local system to the remote system.
execute : Execute a program or script from the local system on the remote system.
exit    : Terminate the session and exit the program.
```

#### Example: Running Commands

```text
[declusor] command id && uname -a
uid=1000(dev) gid=1000(dev) groups=1000(dev),27(sudo)
Linux target-node 6.8.0-45-generic #45-Ubuntu SMP PREEMPT_DYNAMIC x86_64 GNU/Linux
```

#### Example: In-Memory Module Loading

```text
[declusor] load discovery/system_info.py

SYSTEM INFORMATION
------------------
OS: Linux 6.8.0-45-generic (#45-Ubuntu SMP PREEMPT_DYNAMIC)
Architecture: x86_64
Hostname: target-host
User: dev
```

## Extensible Plugin Ecosystem

Declusor was architected from day one as an extensible engine. Transport plugins are fully autonomous packages with their own manifests, assets, and tests:

```text
plugins/my_plugin/
├── pyproject.toml         # Declares entry point under [project.entry-points."declusor.plugins"]
├── README.md              # Documentation with ## Modules and ## Design Principles
├── src/my_plugin/         # Implements IClientPlugin, IClientRuntime, and IConnection
├── assets/                # Launchers, initialization helpers, and post-exploitation modules
└── tests/                 # Unit and contract conformance tests
```

### Verifying Conformance in Seconds

Every plugin can verify its compliance against Declusor's contracts using the built-in testing SDK:

```python
from declusor import testing
from declusor_plugin import DeclusorPlugin


class TestDeclusorPluginConformance(testing.PluginConformanceTestSuite):
    plugin_class = DeclusorPlugin
```

For complete packaging tutorials, asset overlay mechanics, and step-by-step guides, check out the [Plugins Developer Guide](plugins/README.md).

## Architectural Highlights

Declusor adheres to strict **Clean Architecture** and **Dependency Inversion** principles:

- **Unidirectional Layer Boundaries**: Dependencies flow downward into pure domain contracts (`declusor.contract`). Core framework code never imports concrete plugins.
- **Fail-Fast Invariants**: Immutable Command DTOs validate parameters at the boundary, preventing invalid operations from propagating into transports.
- **Deterministic Flow Control**: Controllers return explicit lifecycle signals (`CONTINUE`, `TERMINATE`) rather than relying on control-flow exceptions.
- **100% Strict Static Typing**: Fully typed with strict mypy enforcement across core, native plugins, and tests.

Read the complete architectural specification in [ARCHITECTURE.md](ARCHITECTURE.md).

## Contributing & Quality Gates

Contributions from both humans and autonomous agents are warmly welcomed! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide before opening a pull request.

Before committing, ensure that all quality gates pass:

```bash
# Run full test suite, linter, formatter, and strict type-checks
make check

# Run all plugin test suites
make test-plugins

# Check a specific plugin
make check-plugin PLUGIN=py_socket
```

## License

This project is open-source software licensed under the [MIT License](LICENSE).
