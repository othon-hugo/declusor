# Data Directory

The **data** directory contains the static shell scripts deployed to or executed on remote targets.

## Structure

```
data/
├── clients/          # Reverse-shell client scripts (connection initiators)
│   └── shell_socket.sh
├── library/          # Functions auto-loaded on session init
│   └── *.sh
└── modules/          # On-demand payloads organised by category
    ├── discovery/
    ├── escalation/
    └── ...
```

### `clients/`

Reverse-shell client scripts that establish the initial TCP connection back to Declusor. Scripts are formatted at runtime with `$HOST`, `$PORT`, and `$ACKNOWLEDGE` placeholders.

### `library/`

Utility functions automatically transmitted during `ShellSocketConnection.initialize()`. These persist in the target's memory and are available to all subsequent payloads (e.g. file storage, encoding helpers).

### `modules/`

Categorised payload scripts executed on demand via the `load` command. Each script runs once and its output is streamed back to the console.

## Security Considerations

- **Extension whitelist** — only `.sh` files can be loaded.
- **Path-traversal guard** — `validate_file_relative` prevents loading files outside the designated directory.
- Scripts are transmitted to remote systems — review content for unintended side effects.

## Adding New Payloads

1. Place the `.sh` script in the appropriate subdirectory.
2. Follow the established ACK protocol conventions.
3. Test in a controlled environment before deployment.
