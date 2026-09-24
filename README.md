# Declusor: Remote Control and Payload Delivery Handler

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)

**Declusor** is a fast, flexible, and modular Python tool built for penetration testers, CTF players, and security professionals. It streamlines payload delivery and provides reliable remote control through an extensible, plugin-driven interactive CLI.

Its intelligent command-line interface boosts productivity with smart command and path completion, while supporting remote command execution, interactive sessions, payload management, and file transfers — all in one place.

![Capabilities Overview](https://i.imgur.com/Wsw2l90.gif)

> [!WARNING]
> **Legal Notice**: This software is intended solely for educational use and authorized security research. The developers assume no liability for any misuse or unlawful activity carried out with this tool. Executing this software on networks or systems without ownership or explicit, written authorization for any form of testing or operation is strictly prohibited.

## Features

- **Extensible Client Plugin Architecture**: Autonomous, self-contained plugins supporting different remote agents (e.g. native Bash `/dev/tcp`, Python agent with dual-mode execution).
- **Multi-Tier Runtime Discovery**: Dynamically discovers built-in plugins (`plugins/`), external Python packages via Entry Points (`declusor.plugins`), and drop-in directories (`--plugin-dir`).
- **Shell Management**: Establish, maintain, and manage reverse shell sessions with connected targets.
- **Interactive Shell**: Spawn a fully interactive shell on the remote host for real-time command execution.
- **Command Execution**: Execute arbitrary commands on the remote system and stream output back cleanly.
- **File Upload & Execution**: Transfer files or execute local scripts in memory / via temporary binaries on the target.
- **On-Demand Module Loading**: Execute reconnaissance and post-exploitation modules with tabular presentation.
- **Zero Heavy Dependencies**: Core engine depends exclusively on the Python standard library.

## Getting Started

### Prerequisites

- **Python 3.11+** installed on the local machine running Declusor.
- **Target environment**: Unix-like system for `shell_socket`, or any system with Python 3.6+ for `py_socket`.

### Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Starting the Listener

Start Declusor specifying the bind address and port:

```bash
# Default (shell_socket client)
declusor 0.0.0.0 4444

# Select client plugin explicitly
declusor 0.0.0.0 4444 --client py_socket

# Load external drop-in plugins
declusor 0.0.0.0 4444 --plugin-dir /path/to/custom_plugins --client my_custom_agent
```

On startup, Declusor prints the client launcher command to execute on the target system.

### Available Client Plugins

| Client            | Flag              | Target Compatibility                | Execution Method                                                       |
| ----------------- | ----------------- | ----------------------------------- | ---------------------------------------------------------------------- |
| **Shell Socket**  | `-c shell_socket` | Linux / Bash                        | Native `/dev/tcp` file descriptor                                      |
| **Python Socket** | `-c py_socket`    | Linux, macOS, Windows (Python 3.6+) | In-memory `exec()` with persistent session scope & subprocess fallback |

### Interacting with the Target

Once the target connects back to the listener, an interactive prompt is presented:

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

Example payload module execution:

```text
[declusor] load discovery/system_info.py

SYSTEM INFORMATION
------------------
OS: Linux 6.8.0-45-generic (#45-Ubuntu SMP PREEMPT_DYNAMIC)
Architecture: x86_64
Hostname: target-host
User: dev
```

## Developing Plugins

Declusor was built from the ground up to allow users to build and publish custom client transports:

- See the [Plugins Developer Guide](plugins/README.md) for full documentation, directory layout specifications, and step-by-step tutorials.
- See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete domain contract specifications and layer architecture.

## Contributing

Contributions are welcome! Please ensure that:

1. Code adheres to clean architecture principles and domain contracts in `src/declusor/contract/`.
2. All new components include unit tests (`pytest`).
3. Code passes linting (`ruff check src plugins tests`).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
