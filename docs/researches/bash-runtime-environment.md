# Bash Runtime Environment

## Central Question

Which environmental values must be treated as part of a Bash script's execution contract?

## Scope

This research covers working directory, environment variables, `PATH`, identity, permissions, available commands, locale, and shell options.

It does not cover message framing, transport encoding, interpreter selection, sandboxing, or application-specific command behavior.

## Environment Is Input

A Bash script does not execute in isolation from its environment. The same source may produce different results when these values change:

- current working directory;
- environment variables;
- `PATH`;
- user and group identity;
- filesystem permissions;
- available commands;
- locale;
- shell options.

These values should be documented when reproducibility matters.

## Working Directory

Relative paths depend on the current directory:

```bash
printf '%s\n' "$(pwd)"
printf '%s\n' "./relative/path"
```

A script should not assume a directory unless the caller establishes it or the script resolves paths deliberately.

## `PATH` and Command Resolution

The same command name may resolve to different executables depending on `PATH`:

```bash
command -v tool
```

For critical operations, verify the resolved command or use an explicit path. Do not assume that a command available during development exists in the target environment.

## Identity and Permissions

The script executes with the identity and privileges of its Bash process:

```bash
id
```

Read, write, execute, and network permissions are environment properties, not properties of the script delivery mechanism.

## Locale and Text

Locale settings can affect:

- sorting;
- character classes;
- case conversion;
- command output;
- interpretation of non-ASCII text.

Scripts that process text should define their locale requirements or avoid depending on locale-sensitive behavior.

## Shell Options

Options such as `errexit`, `nounset`, and `pipefail` change failure behavior:

```bash
set -o pipefail
```

A script should establish the options it requires instead of relying on inherited shell state.

## Verification Strategy

Record or test:

1. current directory;
2. required environment variables;
3. resolved executable paths;
4. user and group identity;
5. required permissions;
6. locale;
7. shell options;
8. behavior when a dependency is unavailable.

## Conclusion

The runtime environment is part of a Bash script's effective input. Reproducible behavior requires explicit assumptions about paths, identity, commands, locale, and shell options.

The central design rule is:

> A script cannot be more portable or predictable than the environment contract it makes explicit.
