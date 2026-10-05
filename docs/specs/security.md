# Security Invariants Specification

This document specifies the security boundaries, path confinement barriers, encryption guarantees, injection protections, and entropy standards enforced by Declusor using Lean BDD.

### SEC-01: Canonical Path Confinement Barrier

Target paths must resolve strictly within the designated canonical base directory; parent directory traversals (`../`), escaping symlinks, and absolute paths outside the base are rejected to prevent arbitrary filesystem disclosure.

```gherkin
Scenario: Reject paths escaping the designated base directory
  Given a target path containing parent directory traversal (such as "sandbox/../../etc/passwd") or escaping symlink
  When the path is validated against the base directory
  Then path confinement validation fails
```

### SEC-02: Module Directory Traversal Prevention

Module loading operations must strictly reject attempts to load modules located outside the plugin's designated modules directory; directory traversal attempts raise `InvalidOperation`.

```gherkin
Scenario: Reject module loading with path traversal sequences
  Given a module name containing directory traversal sequences (such as "../outside.py")
  When the module loading request is validated
  Then validation fails with InvalidOperation("Path traversal detected: module '...' is outside permitted directory.")
```

### SEC-03: Plugin Asset Confinement Barrier

Plugin asset processors must validate both relative and absolute paths against permitted helper and module directories before reading or transmitting files; unauthorized paths raise `InvalidOperation`.

```gherkin
Scenario: Reject asset loading targeting unauthorized absolute paths
  Given an asset loading request targeting an absolute host path (such as "/etc/passwd")
  When the asset path is verified by the plugin processor
  Then execution fails with InvalidOperation
```

### SEC-04: XOR Obfuscation and Continuous Key Offset Synchronization

The XOR transport decorator must reversibly transform data and preserve its key offset across arbitrary stream chunk boundaries. Repeating-key XOR provides obfuscation only; it does not provide authenticated encryption or cryptographic confidentiality.

```gherkin
Scenario: Preserve XOR key alignment across fragmented reads
  Given XOR-transformed payload bytes received across multiple stream chunks
  When chunks are transformed sequentially through the transport decorator
  Then the running key offset is preserved and the output matches the original payload
```

### SEC-05: Shell Command Quoting & Injection Neutralization

All command tokens interpolated into shell execution scripts must be safely quoted using standard POSIX shell escaping to eliminate command injection vulnerabilities.

```gherkin
Scenario: Neutralize shell command injection metacharacters
  Given a command argument containing shell metacharacters (such as "a; rm -rf /" or "$(whoami)")
  When the argument is quoted for shell interpolation
  Then metacharacters are safely escaped and treated as a single literal string argument
```

### SEC-06: Cryptographic Nonce Generation Entropy & Formatting

Nonces used for command envelopes and session identification must be generated using an operating system cryptographically secure pseudorandom number generator (CSPRNG) formatted strictly as lowercase hexadecimal strings.

```gherkin
Scenario: Generate cryptographically secure hexadecimal nonces
  Given a request to generate an N-byte session nonce
  When the nonce generation routine is invoked
  Then the output is a 2N-character string matching lowercase hexadecimal characters and successive calls produce distinct values
```

### SEC-07: Filesystem Storage Sanitization & Null-Byte Rejection

Filesystem storage operations must reject empty paths, whitespace-only paths, and paths containing null bytes (`\0`) to protect lower-level operating system APIs from null-byte poisoning attacks.

```gherkin
Scenario: Reject filesystem paths containing null bytes
  Given a filesystem path string containing null bytes (such as "/tmp/file\0.txt")
  When the storage path is validated
  Then validation fails with StorageValidationError
```
