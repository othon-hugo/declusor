# Plugin Conformance Invariants Specification

This document specifies the architectural invariants, conformance standards, and client handshake specifications enforced uniformly across all Declusor plugins using Lean BDD.

### PLG-01: Plugin Identifier Invariant

Every plugin extension must declare a non-empty string `name`, which serves as its plugin kind identifier. Registration rejects duplicate names by default; an explicit override may replace an existing plugin during discovery precedence handling. Descriptive metadata such as `description`, `version`, and `author` is optional and may be empty.

```gherkin
Scenario: Verify mandatory plugin metadata properties
  Given any registered plugin extension in the system
  When the plugin metadata properties are inspected
  Then the name is a non-empty string
  And registering a second plugin with the same name is rejected unless explicit override is enabled
```

### PLG-02: Plugin Argument Parser Configuration Contract

Plugins must register plugin-specific options on the shared argument parser and use option strings that do not conflict with common options. The parser raises `argparse.ArgumentError` during configuration if a plugin attempts to reuse an option string.

```gherkin
Scenario: Configure central argument parser with plugin options
  Given a central argument parser instance
  When the plugin registers its options onto the parser
  Then the plugin options are registered before command-line parsing

Scenario: Reject a plugin option that conflicts with a common option
  Given a plugin that registers an option string already used by the common parser
  When the plugin configures the parser
  Then configuration fails with argparse.ArgumentError before arguments are parsed
```

### PLG-03: Plugin Configuration Builder & Validation Barrier

Plugins must validate configuration options before runtime creation and reject invalid, contradictory, or out-of-bounds values with `ParserError`. `PluginValidationError` is reserved for invalid plugin declarations and contract violations.

```gherkin
Scenario: Intercept invalid plugin configuration options
  Given an invalid, incomplete, or contradictory set of plugin options
  When the plugin validates the configuration parameters
  Then validation fails with ParserError before runtime initialization
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

Plugin filesystem configuration derives `launchers`, `helpers`, and `modules` paths beneath its assets directory. The plugin validates its required launcher before runtime creation; helpers and modules may be absent when that plugin does not require bundled assets from those directories.

```gherkin
Scenario: Resolve plugin asset subdirectories from the configured root
  Given an existing plugin root or assets directory
  When the plugin filesystem is constructed
  Then launchers, helpers, and modules paths are derived beneath the assets directory

Scenario: Reject a missing required launcher
  Given a plugin configuration whose required launcher file is absent
  When the plugin validates its configuration
  Then validation fails with ParserError before runtime creation
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

### PLG-09: Plugin Discovery Precedence

When plugins with the same name are discovered from multiple sources, later tiers override earlier tiers in this order: built-in repository plugins, installed entry points, the user drop-in directory, and explicit CLI search directories. Within explicit search directories, later directories override earlier ones.

```gherkin
Scenario: User drop-in plugin overrides an installed entry point
  Given a built-in, entry-point, and user drop-in plugin with the same name
  When plugin discovery completes
  Then the user drop-in plugin is registered

Scenario: Later explicit search directory overrides an earlier one
  Given two explicit search directories containing plugins with the same name
  When plugin discovery processes the directories in order
  Then the plugin from the later directory is registered
```
