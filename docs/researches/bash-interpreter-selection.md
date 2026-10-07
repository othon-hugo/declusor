# Bash Interpreter Selection

## Central Question

When is Bash required instead of a generic `sh` interpreter, and how can shell-language assumptions be made explicit?

## Scope

This research covers interpreter selection, Bash-specific syntax, portability assumptions, and verification of the selected shell.

It does not cover input transport, framing, permissions, sandboxing, or command semantics.

## Bash and `sh` Are Different Contracts

`bash` names a specific shell implementation. `sh` names a shell-compatible interface and may point to another implementation.

A script that runs under Bash is not automatically portable to every `sh` implementation.

```bash
bash < script.sh
sh < script.sh
```

These commands may interpret the same bytes differently.

## Bash-Specific Features

Features commonly requiring Bash include:

- arrays;
- `[[ ... ]]` conditions;
- process substitution;
- Bash parameter expansion;
- `mapfile` and `readarray`;
- Bash-specific shell options;
- `/dev/tcp` support;
- behavior of exported functions.

A script that relies on such features must select Bash explicitly.

## Portability-Oriented Scripts

A script intended for multiple shells should use the smallest language subset required by all supported interpreters and avoid assuming Bash behavior.

Portability must be tested against the actual shell implementations rather than inferred from the `/bin/sh` path.

## Interpreter Verification

A process can inspect the selected shell version:

```bash
if [ -n "${BASH_VERSION:-}" ]; then
    printf '%s\n' "running under Bash"
else
    printf '%s\n' "Bash-specific features are unavailable"
fi
```

This check only verifies the current shell environment. It does not prove that every required feature is available or enabled.

## Failure Modes

Common failures include:

- Bash syntax sent to a non-Bash interpreter;
- assuming `/bin/sh` is Bash;
- relying on a feature unavailable in an older Bash version;
- interpreting a script under one shell during testing and another in production;
- confusing an interpreter failure with a script failure.

## Verification Strategy

Test scripts with:

1. the intended Bash version;
2. the intended `sh` implementation when portability is required;
3. Bash-only syntax;
4. strict mode settings;
5. unset variables and empty input;
6. command-not-found behavior;
7. exit status propagation.

## Conclusion

Interpreter choice is part of a shell script's execution contract. Selecting `bash` explicitly is necessary when the source depends on Bash-specific syntax or behavior.

The central design rule is:

> A shell script is portable only across interpreters whose language and runtime contracts it actually satisfies.
