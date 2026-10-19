# Declusor CTF — Challenge Labs

A progressive 4-tier Linux post-exploitation and container breakout environment built on Alpine Linux.

> [!WARNING]
> **Security Notice** Labs `03-dockside` and `04-leviathan` are explicitly designed to escape into the host environment. Run these challenges only inside an isolated disposable virtual machine (VM) or dedicated sandbox host. Never expose ports `2203` or `2204` to untrusted public networks.

## Challenge Matrix

| Directory       | Container Name          | Level      | Port   | Primary Attack Vector                                 | Target Flag                    |
| --------------- | ----------------------- | ---------- | ------ | ----------------------------------------------------- | ------------------------------ |
| `01-skiff/`     | `declusor-01-skiff`     | **Easy**   | `2201` | Multi-path Local PrivEsc (Sudo, SUID, Cron, Passwd)   | `/root/flag.txt` _(Container)_ |
| `02-draftsman/` | `declusor-02-draftsman` | **Medium** | `2202` | Custom SUID binary PATH hijacking (`healthcheck`)     | `/root/flag.txt` _(Container)_ |
| `03-dockside/`  | `declusor-03-dockside`  | **Hard**   | `2203` | Exposed Docker daemon socket (`/var/run/docker.sock`) | Host `/root/flag.txt` _(Host)_ |
| `04-leviathan/` | `declusor-04-leviathan` | **Expert** | `2204` | Full container breakout via `--privileged` mode       | Host `/root/flag.txt` _(Host)_ |

## Global Credentials

| Parameter         | Value       |
| ----------------- | ----------- |
| **Username**      | `player`    |
| **Password**      | `declusor`  |
| **Default Shell** | `/bin/bash` |
| **Target Host**   | `127.0.0.1` |

> Direct SSH root login is disabled on all instances (`PermitRootLogin no`). Competitors must authenticate as `player` and escalate privileges.

## Quick Start

All operations can be driven from the repository root via the master `Makefile`:

````bash
# Build all challenge images
make build-all

# Start all containers in the background
make run-all

# Inspect container status and mapped ports
make status

# Connect to a target container (e.g., Lab 01)
make ssh-01

# Stop and wipe everything
make clean

### Direct SSH Connections

```bash
ssh player@127.0.0.1 -p 2201   # 01-skiff
ssh player@127.0.0.1 -p 2202   # 02-draftsman
ssh player@127.0.0.1 -p 2203   # 03-dockside
ssh player@127.0.0.1 -p 2204   # 04-leviathan

````

## Lab Descriptions

### `01-skiff` (Easy)

Designed for beginners to practice standard Linux local enumeration. Contains 5 intentional flaws:

- Overly permissive `sudoers` rules (`find`, `less`, `awk`, `tar`).
- SUID bit on `/bin/cat`.
- World-writable periodic maintenance script (`/opt/backup.sh`).
- Leaked administrator credentials in `/var/backups/.maintenance.txt`.
- Write permissions on `/etc/passwd`.

### `02-draftsman` (Medium)

Focuses on binary inspection and environment variable abuse. Features a compiled C utility (`/usr/local/bin/healthcheck`) with the SUID bit set that invokes an unqualified system command (`system("uptime")`).

### `03-dockside` (Hard)

Simulates a classic container orchestration misconfiguration. The container has `/var/run/docker.sock` mounted from the host, and the `player` user belongs to the Docker socket group, enabling host filesystem takeover via sibling containers.

### `04-leviathan` (Expert)

Runs with `--privileged` enabled and unconfined capabilities (`CAP_SYS_ADMIN`). Competitors must achieve a direct breakout into the host operating system through device node access or cgroup notification vectors.
