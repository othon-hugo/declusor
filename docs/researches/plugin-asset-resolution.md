# Extension Asset Resolution

## Central Question

How can an extension resolve launchers, helpers, and modules while preventing paths from escaping its allowed asset roots?

## Scope

This research covers asset categories, relative paths, canonicalization, traversal, symlinks, and resolution consistency.

It does not cover extension discovery, runtime lifecycle, command dispatch, framing, or transport security.

## Asset Roots

An extension may expose separate roots for:

- launchers;
- helper libraries;
- modules;
- templates;
- other static resources.

Each asset category should have an explicit root and a defined set of allowed file types.

## Relative Resolution

A user-supplied asset name should be interpreted relative to its designated root, not relative to the process working directory:

```python
candidate = root / requested_name
```

The candidate must be normalized before it is accepted.

## Traversal Defense

Names such as these must not escape the asset root:

```text
../outside
nested/../../outside
absolute/path
```

A containment check should compare canonical paths, not only raw strings:

```python
root = root.resolve()
candidate = (root / requested_name).resolve()

if candidate != root and root not in candidate.parents:
    raise ValueError("asset outside permitted root")
```

The exact policy for symlinks must be explicit.

## Symlink Policy

Resolving symlinks before containment checking prevents a path inside the root from pointing outside it. A system may instead forbid symlinks entirely, but the choice must be documented.

Checking only the lexical path is insufficient when links are allowed.

## Name Normalization

Convenience prefixes such as `modules/` should be normalized once, before resolution. The normalized name must then pass the same containment checks as every other name.

Normalization must not turn an invalid path into an accepted path accidentally.

## Consistent Consumers

Asset resolution used by:

- command execution;
- autocomplete;
- launcher generation;
- module loading;
- tests;

should follow the same root and validation rules. Different resolution paths create policy gaps.

## Verification Strategy

Test:

1. a valid direct asset;
2. a nested asset;
3. missing extensions;
4. absolute paths;
5. `..` traversal;
6. repeated separators;
7. symlinks to files inside the root;
8. symlinks outside the root;
9. normalized prefixes;
10. autocomplete results versus actual loading.

## Conclusion

Asset resolution is a security-sensitive boundary. It must combine explicit roots, canonical paths, consistent normalization, and a documented symlink policy.

The central design rule is:

> Validate the canonical destination, not merely the input string.
