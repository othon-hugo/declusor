# Domain Invariants Specification

This document specifies the domain invariants and validation rules governing CLI configuration, command modeling, routing, and transport parameters using Lean BDD.

### DOM-01: Port Number Range Validation

Network port numbers supplied via CLI or configuration must be valid integers in the closed range $[0, 65535]$; invalid or out-of-bounds inputs raise `ParserError` to prevent unhandled operating system socket errors.

```gherkin
Scenario: Reject out-of-bounds port numbers
  Given an input port value outside the range 0 to 65535 (such as -1 or 70000)
  When the CLI arguments are parsed
  Then parsing fails with ParserError("Port must be between 0 and 65535.")
```

### DOM-02: Positive Connection Timeout Validation

Socket connection timeouts must be strictly positive floating-point numbers ($> 0.0$); non-positive or invalid values raise `ParserError` to prevent instant timeouts or infinite terminal hangs.

```gherkin
Scenario: Reject non-positive timeout values
  Given a timeout parameter less than or equal to 0 (such as 0.0 or -2.5)
  When the CLI arguments are parsed
  Then parsing fails with ParserError("Timeout must be positive.")
```

### DOM-03: Launcher Delivery Target Syntax Validation

Launcher delivery targets must conform to the syntax `terminal`, `silent`, or `file:<path>` with a non-empty destination path; malformed targets raise `ParserError` to prevent stager generation failures during startup.

```gherkin
Scenario: Reject malformed launcher output syntax
  Given a launcher output parameter with an empty file path (such as "file:") or unknown mode
  When the CLI arguments are parsed
  Then parsing fails with ParserError
```

### DOM-04: Transport Layer Registry Membership Validation

All transport decorator names supplied via configuration must be registered in the transport registry; unknown decorator names raise `ParserError` to catch unsupported wrappers prior to socket initialization.

```gherkin
Scenario: Reject unknown transport layer decorators
  Given a transport layer argument specifying an unregistered decorator name
  When the CLI arguments are parsed
  Then parsing fails with ParserError("Unknown transport layer: '...'.")
```

### DOM-05: Plugin Name Registration Validation in CLI Parser

Client plugin names requested via `--plugin` must exist within the plugin registry; unrecognized plugin names raise `ParserError` to prevent bootstrap crashes on unmapped runtimes.

```gherkin
Scenario: Reject unrecognized plugin names
  Given a CLI argument requesting a plugin name not registered in the system
  When the CLI arguments are parsed
  Then parsing fails with ParserError("Unknown plugin: '...'.")
```

### DOM-06: Route Registration Collision Rejection in Router

The router rejects duplicate names passed directly to `connect` with `DuplicateRouteError`. During application composition, a plugin registration may replace an official registration before connecting; collisions with names already present in the injected router are still rejected.

```gherkin
Scenario: Reject duplicate direct router registration
  Given a router that already has a controller registered for command "exec"
  When another controller attempts to register under command "exec"
  Then registration fails with DuplicateRouteError
```

### DOM-07: Empty Command Dispatch Rejection in Router

The command router must reject dispatching requests with empty or whitespace-only command names; blank requests raise `RouterError` to maintain input hygiene.

```gherkin
Scenario: Reject dispatching empty command requests
  Given an operator request with an empty or whitespace-only command name
  When the request is dispatched to the router
  Then dispatching fails with RouterError("Command name cannot be empty.")
```

### DOM-08: Unregistered Command Dispatch Rejection in Router

Dispatching a request for a command identifier not present in the route table raises `RouterError` to allow presentation layers to display user-friendly diagnostics rather than crashing.

```gherkin
Scenario: Reject dispatching unregistered command names
  Given an incoming request for a command name not present in the route table
  When the request is dispatched to the router
  Then dispatching fails with RouterError("Command '...' is not registered.")
```

### DOM-09: Command Invariant Validation Prior to Execution

Command objects must validate their domain parameters before initiating execution against a session; invalid parameters raise `CommandValidationError` to protect active network streams from corrupt payloads.

```gherkin
Scenario: Validate command parameters before execution
  Given a command instantiated with invalid or corrupted parameters
  When the command is executed against an active session
  Then validation fails with CommandValidationError before any network I/O occurs
```

### DOM-10: Non-Empty Command String Invariant in Execute Command

Execute-command requests must contain a non-empty, non-whitespace command string; empty strings raise `CommandValidationError` to prevent sending blank payloads that stall remote processes.

```gherkin
Scenario: Reject empty execute command strings
  Given an execute-command request with an empty or whitespace-only command string
  When the command parameters are validated
  Then validation fails with CommandValidationError("Command line cannot be empty.")
```

### DOM-11: Non-Empty Code String Invariant in Execute Code

Execute-code requests must contain a non-empty, non-whitespace code string; empty strings raise `CommandValidationError` to prevent transmitting blank evaluation payloads.

```gherkin
Scenario: Reject empty execute code strings
  Given an execute-code request with an empty or whitespace-only code string
  When the command parameters are validated
  Then validation fails with CommandValidationError("Code cannot be empty.")
```

### DOM-12: Script File Existence and Regular File Invariant in Execute File

Execute-file operations require the local script file to exist and be a regular file; non-existent files or directories raise `StorageValidationError` to halt execution before network transfer.

```gherkin
Scenario: Reject non-existent or directory script targets
  Given an execute-file target path that does not exist or points to a directory
  When the execute-file command is executed
  Then execution fails with StorageValidationError
```

### DOM-13: Source and Destination Path Invariant in Upload File

File upload operations require a valid, existing local source file and a non-empty remote destination path; missing sources or empty targets raise validation errors to prevent partial file uploads.

```gherkin
Scenario: Reject upload with missing source or empty destination
  Given an upload request with a non-existent local file or an empty destination path
  When the upload command is validated or executed
  Then execution fails with CommandValidationError or StorageValidationError
```

### DOM-14: Module Extension Restriction Invariant in Load Module

Modules loaded via module-loading commands must strictly bear approved executable script extensions (`.py` or `.sh`); unapproved extensions raise `InvalidOperation` to prevent loading arbitrary binary files.

```gherkin
Scenario: Reject module files with unapproved extensions
  Given a module name bearing an unapproved extension (such as "payload.bin" or "module.so")
  When the module loading command is validated
  Then validation fails with InvalidOperation because the selected plugin does not support that module extension
```

### DOM-15: Active Input Source Invariant in Launch Shell

Interactive shell sessions require an active, operational input source attached to the session; missing input sources raise `InvalidOperation` to prevent deadlocks in headless environments.

```gherkin
Scenario: Reject interactive shell execution without input source
  Given a session context configured without an active input source
  When interactive shell execution is launched
  Then execution fails with InvalidOperation("Interactive shell requires an active input source.")
```

### DOM-16: Operation Renderer Opcode Support Validation

Commands must verify that the connection profile supports the requested operation code; attempting unsupported operations raises `InvalidOperation` to prevent sending incompatible commands to remote agents.

```gherkin
Scenario: Reject operation codes unsupported by connection profile
  Given a connection profile that does not support code execution
  When an execute-code operation is dispatched against the session
  Then execution fails with InvalidOperation("Connection profile does not support code execution.")
```

### DOM-17: Launcher Delivery Mode and Path Coherence Invariant

Launcher delivery configurations must maintain consistency between mode and destination path: `file` mode requires a path, while non-file modes prohibit paths; contradictory settings raise `LauncherDeliveryError`.

```gherkin
Scenario: Reject inconsistent launcher delivery settings
  Given a launcher delivery configuration specifying "file" mode without a path, or "terminal" mode with a path
  When the delivery configuration is initialized
  Then initialization fails with LauncherDeliveryError
```

### DOM-18: Application Bootstrap Plugin Resolution Invariant

Application bootstrap must verify that the configured plugin kind exists in the plugin registry before allocating network listeners; missing plugins raise `PluginNotFoundError` to halt startup cleanly.

```gherkin
Scenario: Reject bootstrap with unregistered plugin kind
  Given an application configuration specifying an unknown plugin kind
  When the application startup sequence begins
  Then execution fails with PluginNotFoundError before any network socket is opened
```

### DOM-19: Positive Socket Read Limit Invariant

Socket byte transports must enforce that each read limit is a strictly positive integer ($> 0$); non-positive limits raise `ValueError` before socket I/O to prevent invalid or zero-byte reads.

```gherkin
Scenario: Reject non-positive socket read limit
  Given a socket read operation requested with a maximum byte count of 0 or less
  When the transport read is attempted
  Then it fails with ValueError before reading from the socket
```

### DOM-20: Stream Cipher Non-Empty Encryption Key Invariant

The XOR transport decorator must enforce a non-empty key; an empty key raises `ValueError` before any transport I/O because XOR key cycling requires at least one byte.

```gherkin
Scenario: Reject empty stream cipher encryption keys
  Given a stream cipher transport configured with an empty key
  When the transport is initialized
  Then initialization fails with ValueError
```

### DOM-21: Network Listener Port Range and Positive Backlog Invariant

Network listeners must validate that the bind port is within $[0, 65535]$ and the connection backlog is strictly positive ($> 0$); invalid parameters raise `ValueError` before opening or binding a socket.

```gherkin
Scenario: Reject out-of-range listener port or non-positive backlog
  Given a listener configuration with a port outside 0 to 65535, or a backlog of 0 or less
  When the network listener is initialized
  Then initialization fails with ValueError before a socket is opened
```

### DOM-22: Plugin Module Name Normalization Invariant

Plugin file stores resolving on-demand modules must normalize module identifiers by stripping redundant leading `modules/` prefixes (`module_name.removeprefix("modules/").removeprefix(f"modules{os.sep}")`); this guarantees that both direct identifiers (`discovery/sysinfo`) and autocompleted asset paths (`modules/discovery/sysinfo.py`) resolve to valid module files within the plugin repository while strictly enforcing containment inside `filesystem.modules`.

```gherkin
Scenario: Normalize autocompleted module path prefix
  Given a module load request specifying "modules/discovery/sysinfo.py"
  When the plugin file store resolves the module
  Then the module is resolved cleanly within the plugin's modules directory
```
