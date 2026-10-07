# Extension Conformance Testing

## Central Question

How can an independently implemented extension demonstrate compatibility with a host contract without relying on the host's concrete internals?

## Scope

This research covers contract-oriented tests, typed doubles, lifecycle checks, protocol behavior, and reusable conformance suites.

It does not cover discovery precedence, asset resolution, operation rendering, or general application integration testing.

## Contract Over Implementation

A conformance suite should test observable behavior defined by the contract:

- required metadata;
- parser registration;
- option extraction;
- validation;
- runtime construction;
- lifecycle transitions;
- connection behavior;
- asset boundaries.

It should not require a particular private class layout.

## Test Doubles

Typed in-memory doubles can make contract tests deterministic:

- memory transports;
- dummy connections;
- input sources;
- views;
- file stores;
- routers.

Doubles should expose recorded interactions and state transitions without pretending to be unrestricted mocks.

## Reusable Test Suite

A conformance suite can be parameterized with an extension instance:

```python
suite = ExtensionConformanceSuite(extension)
suite.test_metadata()
suite.test_parser_options()
suite.test_runtime_creation()
```

The suite should allow extension-specific tests in addition to shared contract tests.

## Required Invariants

A conformance suite should verify that:

- metadata is complete;
- required options have stable types;
- invalid input fails before resource allocation;
- runtime creation is deterministic;
- close is safe and repeatable;
- transport boundaries are respected;
- malformed input fails predictably;
- asset paths remain within permitted roots.

## Integration Boundary

Unit conformance tests should use doubles. A smaller number of integration tests should exercise real transports, subprocesses, or package discovery.

Keeping these categories separate makes failures easier to diagnose and avoids requiring network or operating-system resources for every contract assertion.

## Verification Strategy

For each extension, run:

1. shared conformance tests;
2. extension-specific unit tests;
3. transport integration tests;
4. asset and security tests;
5. package discovery tests;
6. type and style checks.

The suite should report which contract requirement failed, not only that a generic test failed.

## Limits

Conformance tests cannot prove:

- absence of all security defects;
- behavior on every operating system;
- compatibility with every interpreter version;
- performance under production load;
- correctness of undocumented behavior.

They prove compatibility with the tested contract and scenarios.

## Conclusion

Conformance testing provides a stable compatibility boundary for independently implemented extensions. Its value comes from testing observable guarantees with deterministic doubles and a focused set of real integration checks.

The central design rule is:

> Test the contract that consumers depend on, not the implementation details that happen to satisfy it today.
