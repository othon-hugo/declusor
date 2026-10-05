# Plugin Conformance Invariants Specification

This document specifies the architectural invariants, conformance standards, and client handshake specifications enforced uniformly across all Declusor plugins using Lean BDD.

### PLG-01: Plugin Metadata Invariant

Every plugin extension must declare non-empty string properties for its human-readable name, unique kind identifier, and metadata documentation to guarantee unambiguous identification and auditability.

```gherkin
Scenario: Verify mandatory plugin metadata properties
  Given any registered plugin extension in the system
  When the plugin metadata properties are inspected
  Then name, kind, and metadata are non-empty strings
```

### PLG-02: Plugin Argument Parser Configuration Contract

Plugins must provide an argument parser configuration capability that registers plugin-specific command-line options without throwing errors or causing flag collisions.

```gherkin
Scenario: Configure central argument parser with plugin options
  Given a central argument parser instance
  When the plugin registers its options onto the parser
  Then plugin-specific command-line flags are added cleanly without error
```

### PLG-03: Plugin Configuration Builder & Validation Barrier

Plugins must build a validated configuration object from parsed command-line parameters, and reject invalid, contradictory, or out-of-bounds options by raising `PluginValidationError`.

```gherkin
Scenario: Intercept invalid plugin configuration options
  Given an invalid, incomplete, or contradictory set of plugin options
  When the plugin validates the configuration parameters
  Then validation fails with PluginValidationError before runtime initialization
```

### PLG-04: Plugin Runtime Creation Contract

Plugins must successfully instantiate an operational plugin runtime from a valid configuration, and the runtime must produce functional connection instances wrapping any compliant transport.

```gherkin
Scenario: Create connection instance from plugin runtime
  Given a valid plugin configuration and an open transport
  When the plugin runtime creates a client connection
  Then a functional connection adhering to the connection lifecycle contract is returned
```

### PLG-05: Plugin Asset Directory Structure Contract

Plugin asset directories must provide conforming `launchers`, `helpers`, and `modules` resource locations to ensure stagers and modular payloads can be resolved reliably without filesystem errors.

```gherkin
Scenario: Confirm presence of plugin asset directories
  Given a conforming plugin asset directory structure
  When the plugin filesystem paths are inspected
  Then launchers, helpers, and modules directories exist and are accessible
```

### PLG-06: POSIX Shell Handshake Helper Delivery Validation

Handshake with POSIX shell agents must transmit helper functions and wait for dynamic delimiter acknowledgement; network interruptions or timeouts during handshake raise `ConnectionHandshakeError`.

```gherkin
Scenario: Handle transport failure during shell helper handshake
  Given a shell client session where the network drops or times out during helper transmission
  When the connection handshake is executed
  Then initialization fails with ConnectionHandshakeError
```

### PLG-07: Python Agent Handshake SHA-256 ACK Verification

Handshake with Python socket agents must transmit helper scripts and verify that the remote agent responds with the exact SHA-256 hash of the client acknowledgement seed; mismatched tokens raise `ConnectionHandshakeError`.

```gherkin
Scenario: Reject mismatched client acknowledgement token
  Given a remote agent that responds with an invalid or corrupted acknowledgement token
  When the connection handshake is executed
  Then initialization fails with ConnectionHandshakeError("Invalid client ACK during session initialization.")
```

### PLG-08: Extensible Plugin Route Table Contract

Every plugin must declare `routes` as a mapping from non-empty, open-ended string names to `RouteRegistration` values. The application composes plugin registrations over the official core route table before connecting routes. Plugins may override official registrations, but `help` and `exit` are protected; duplicate normalized plugin names and collisions with routes already present in the injected router are rejected before any route is connected.

```gherkin
Scenario: Add a plugin-specific route
  Given a plugin route table containing a custom string name and RouteRegistration
  When the application composes the selected plugin's routes
  Then the custom route is available with the plugin's controller and help text

Scenario: Override an official route registration
  Given a plugin route table defining the name of an official route
  When the application composes the selected plugin's routes
  Then the plugin's RouteRegistration replaces the official registration for that name

Scenario: Protect application-owned routes
  Given a plugin route table containing "help" or "exit"
  When PluginManager validates the plugin
  Then validation fails with PluginValidationError

Scenario: Reject collisions before connecting routes
  Given a plugin route table with whitespace-equivalent duplicate names or a router containing a composed route
  When the application prepares route registration
  Then registration fails before adding any route from the composed table
```
