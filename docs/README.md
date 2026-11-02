# Declusor Documentation

Reference guides for the protocol and runtime concepts used by Declusor.

## Guides

- [Channel Types](channel-type.md): logical lanes in multiplexed sessions.
- [Execution Modes](execution-mode.md): interfaces exposed by the session engine.
- [Framing Modes](framing-mode.md): boundaries and wire formats for command responses.
- [Launcher Delivery](launcher-delivery.md): staged, stageless, and output delivery options.
- [Plugin Assets](plugin-asset.md): target-side launchers, ACL helper libraries, and module hierarchies.
- [Transport Layers](transport-layer.md): composable obfuscation, authentication, and encryption layers.

## Status Vocabulary

- **Available**: supported by the built-in CLI and runtime.
- **Programmatic**: available through the Python API but not exposed as a default CLI option.
- **Upcoming**: planned, but not implemented yet.
- **Extensible**: reserved for custom implementations.

Protocol documents describe the current built-in behavior. Planned features are
marked explicitly and should not be treated as available security guarantees.
