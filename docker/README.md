# Declusor Labs — Enterprise Security & Breakout Labs

Welcome to **Declusor Labs**, a semi-realistic, multi-tiered security training platform designed for **Red Teamers, Blue Teamers, Software Developers, DevOps Engineers, SREs, and CTF players**.

Instead of abstract puzzles, these four progressive Alpine-based labs simulate a fictional shipping logistics organization. Each environment combines misconfigured services, exposed developer artifacts, vulnerable code patterns, and infrastructure integration flaws.

## Challenge Matrix

| Directory       | Lab Name      | Difficulty | SSH Port | Web/API Port | Primary Focus & Attack Vector                                             | Target Flag & Scope            |
| :-------------- | :------------ | :--------: | :------: | :----------: | :------------------------------------------------------------------------ | :----------------------------- |
| `01-skiff/`     | **Skiff**     |  **Easy**  |  `2201`  |    `8081`    | Web hygiene, exposed `.env`/`.git`, SUID, Sudo, Writable Cron             | `/root/flag.txt` _(Container)_ |
| `02-draftsman/` | **Draftsman** | **Medium** |  `2202`  |    `8082`    | Runtime `/proc` leaks, Redis/SQLite dumps, SUID PATH hijacking            | `/root/flag.txt` _(Container)_ |
| `03-dockside/`  | **Dockside**  |  **Hard**  |  `2203`  |    _N/A_     | IaC state leakage (`terraform.tfstate`), CI/CD secrets, `docker.sock`     | Host `/root/flag.txt` _(Host)_ |
| `04-leviathan/` | **Leviathan** | **Expert** |  `2204`  |    _N/A_     | Linux capabilities (`cap_dac_read_search`), core dumps, Privileged Escape | Host `/root/flag.txt` _(Host)_ |

## Global Credentials

| Parameter         | Value       |
| :---------------- | :---------- |
| **Username**      | `player`    |
| **Password**      | `declusor`  |
| **Default Shell** | `/bin/bash` |
| **Target Host**   | `127.0.0.1` |

> [!WARNING]
> **Security Note:** Direct SSH root login is strictly disabled (`PermitRootLogin no`). Competitors must authenticate as the low-privileged `player` account and leverage local enumeration to escalate.

## Quick Start & Management

The repository is fully managed via a modular `Makefile` at the root:

```bash
# Build all 4 challenge Docker images
make build-labs

# Start all containers in the background
make run-labs

# Check container status and mapped ports
make status-labs

# Connect directly to a specific lab (e.g., Skiff)
make ssh-01

# Stop and clean up all resources
make clean-labs
```
