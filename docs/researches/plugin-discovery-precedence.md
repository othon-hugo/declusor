# Plugin Discovery Precedence

## Central Question

How can independently distributed extensions be discovered from multiple sources without making selection ambiguous?

## Scope

This research covers discovery sources, deterministic precedence, duplicate names, invalid candidates, and origin reporting.

It does not cover plugin lifecycle, plugin implementation contracts, asset loading, command dispatch, or package management.

## Discovery Sources

A system may discover extensions from sources such as:

- built-in registrations;
- installed distribution metadata;
- user drop-in directories;
- explicitly configured search directories.

Each source should be identified separately so that selection can be explained after discovery.

## Deterministic Precedence

When two sources provide the same name, a deterministic precedence rule is required:

```text
source A > source B > source C
```

The rule should be documented and applied consistently. Discovery order based on filesystem traversal or package iteration is not a sufficient policy.

## Duplicate Names

A duplicate can be handled by:

- rejecting the configuration;
- selecting the highest-precedence candidate;
- requiring an explicit source selector;
- merging only when the extension contract permits composition.

Silent replacement is difficult to diagnose and should be avoided unless precedence is intentional and observable.

## Invalid Candidates

Discovery should distinguish:

- source not found;
- source found but metadata invalid;
- source valid but implementation fails to load;
- source loads but violates the extension contract;
- source is shadowed by a higher-precedence candidate.

These outcomes should not collapse into a generic "not found" message.

## Origin Reporting

A selected extension should expose or log its origin:

```text
name: example
source: user-directory
location: /path/to/extension
```

Origin reporting is useful for diagnosing unexpected overrides and supply-chain changes.

## Verification Strategy

Test:

1. one valid candidate per source;
2. duplicate names across sources;
3. invalid metadata;
4. import failure;
5. contract failure;
6. explicit source selection;
7. deterministic results across repeated discovery;
8. origin reporting.

## Conclusion

Discovery is a selection algorithm, not merely a filesystem search. Its correctness depends on explicit sources, deterministic precedence, observable origins, and defined handling of invalid candidates.

The central design rule is:

> If multiple sources can provide the same extension, precedence is part of the public contract.
