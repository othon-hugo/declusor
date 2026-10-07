# Extension Lifecycle Contracts

## Central Question

What are the distinct stages between selecting an extension and creating an operational runtime?

## Scope

This research covers configuration, parser setup, option extraction, validation, runtime creation, and connection creation.

It does not cover discovery precedence, asset resolution, operation rendering, transport internals, or conformance test design.

## Lifecycle Stages

A typical lifecycle is:

```text
select
  -> configure
  -> parse
  -> extract
  -> validate
  -> build runtime
  -> create connection
```

Each stage should have one responsibility and a clear failure boundary.

## Configuration

Configuration should represent validated, immutable choices rather than raw command-line strings whenever possible.

Raw input should not reach the runtime without normalization and validation.

## Parser Configuration

An extension may contribute options to a shared parser. Option names, defaults, and conflicts must be validated while the parser is configured, not only after arguments are parsed.

This prevents two extensions from silently claiming the same option.

## Option Extraction

Parsed values should be converted into the extension's own typed configuration:

```python
options = extension.extract_options(raw_values)
```

The extraction boundary is where untyped input becomes a domain-specific value.

## Validation

Validation should occur before opening listeners, allocating expensive resources, or creating a session.

It should cover:

- required values;
- incompatible combinations;
- bounds;
- paths;
- supported modes;
- security-sensitive defaults.

## Runtime Creation

A runtime contains behavior and resources needed after configuration. It should not silently re-read raw command-line arguments or discover unrelated global state.

Runtime creation should make dependencies explicit.

## Connection Creation

Connection creation is a later lifecycle stage because it may allocate sockets, processes, or other external resources. Failures here should be distinguishable from configuration failures.

## Verification Strategy

Test each boundary independently:

1. parser option registration;
2. conflicting options;
3. raw value extraction;
4. invalid configuration;
5. valid runtime creation;
6. connection failure;
7. cleanup after partial initialization;
8. repeated shutdown.

## Conclusion

A lifecycle contract makes extension behavior predictable by separating input parsing, validation, runtime construction, and external resource allocation.

The central design rule is:

> Validate configuration before creating resources, and make every lifecycle transition observable.
