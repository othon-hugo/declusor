# Bash Execution from Standard Input

## Central Question

How can Bash execute script content received through standard input without requiring the script to exist as a file?

## Scope

This research covers:

- execution with `bash < input`;
- execution through a pipe;
- relationship between standard input and script source;
- process and filesystem implications;
- prerequisites for reliable execution.

It does not cover network framing, shell protocol design, sandboxing, privilege reduction, interpreter compatibility in depth, or transport encryption.

## Basic Model

Bash can read commands from standard input:

```bash
bash < script.sh
```

The shell process reads the contents of `script.sh` through file descriptor `stdin` and interprets them as commands.

The source is consumed as a byte stream rather than opened by Bash through a script path.

Conceptually:

```text
script source -> stdin -> Bash interpreter -> command execution
```

## Pipe-Based Execution

The same model can be expressed with a pipeline:

```bash
cat script.sh | bash
```

The producer writes the script content to standard output. The Bash process reads that content from standard input.

A producer does not need to be `cat`:

```bash
printf '%s\n' 'printf "hello\n"' | bash
```

The important property is that Bash receives commands through its input stream.

## No Script File on the Receiver

When the source is sent through standard input, the receiving environment does not need to create a `.sh` file before execution:

```bash
printf '%s\n' \
  'value=41' \
  'printf "%s\n" "$((value + 1))"' |
bash
```

This avoids one temporary script file, but it does not mean that execution is isolated from the filesystem. Bash and the commands it invokes still use normal operating-system resources.

## Interpreter Selection

Bash syntax should be interpreted by Bash explicitly:

```bash
bash < script.sh
```

Using `sh` is not equivalent:

```bash
sh < script.sh
```

On many systems, `/bin/sh` points to an interpreter with different syntax and behavior. A script that uses Bash-specific features may fail or behave differently when passed to `sh`.

Examples of Bash-specific features include:

- arrays;
- `[[ ... ]]`;
- process substitution;
- Bash parameter expansion;
- `mapfile`;
- `/dev/tcp`;
- shell functions with Bash-specific behavior.

## Standard Input Has Two Roles

When a script is executed from standard input, the same stream is used to supply source commands.

This affects commands that also expect interactive input:

```bash
read value
```

Depending on how the input stream is provided, `read` may consume remaining script content rather than input intended for the executed command.

A script that needs a separate input channel must explicitly arrange one, for example by using another file descriptor or an external source.

## Process Lifetime

The Bash process remains active while it reads and executes the input stream.

A process exits when:

- the input stream reaches EOF;
- the script executes `exit`;
- an unrecoverable error terminates the process;
- a command or signal causes termination.

EOF in the input stream is not the same as a successful result. The exit status must be checked separately:

```bash
bash < script.sh
status=$?

if [ "$status" -eq 0 ]; then
    printf '%s\n' "success"
else
    printf '%s\n' "failure: $status"
fi
```

## Exit Status

The resulting status depends on Bash's execution mode and the commands in the script.

A pipeline may obscure the status of the process that performed the execution:

```bash
producer | bash
```

When status precision matters, capture the correct process status explicitly and configure pipeline behavior according to the calling environment.

A script that prints an error message may still exit with status zero. Output and exit status must therefore be treated as separate signals.

## Environment

Execution still depends on the receiving process environment:

- current working directory;
- environment variables;
- `PATH`;
- user identity;
- filesystem permissions;
- available commands;
- shell options;
- locale;
- Bash version.

The absence of a script file does not remove these dependencies.

For reproducibility, record or control the environment that the script expects.

## Error Handling

Bash may continue after a command fails unless configured otherwise:

```bash
set -e
```

However, `set -e` has detailed behavior and should not be treated as a universal failure policy.

A robust script should define its own error policy and report meaningful status. For example:

```bash
set -u

if ! command_that_may_fail; then
    printf '%s\n' "command failed" >&2
    exit 1
fi
```

The method of delivering the script does not automatically improve its error handling.

## Encoding

The sender and receiver must agree on how script bytes are interpreted.

Shell source commonly uses a locale-dependent text environment. Non-ASCII content can behave differently when the sender and receiver use different encodings or locales.

For portable scripts:

- prefer predictable character sets;
- avoid unnecessary non-ASCII syntax;
- define the expected locale when required;
- test the script in the target environment.

The shell's input stream is a byte stream. Correct interpretation depends on the interpreter and environment.

## When This Approach Is Useful

Executing Bash from standard input is useful when:

- the script is short-lived;
- creating a temporary script file is undesirable;
- a producer already has a byte stream;
- the receiving environment provides Bash;
- the execution environment is controlled.

It is not automatically better than a file-based script. A file may be preferable when:

- repeated execution is required;
- debugging and inspection are important;
- restartability matters;
- the script must be referenced by another process;
- auditability is a requirement.

## Verification Strategy

A minimal verification set should test:

1. Commands arrive through standard input.
2. Variables and functions persist during one Bash process.
3. EOF terminates the input stream.
4. Exit status is observable.
5. Errors are reported through the expected stream.
6. Bash-specific syntax behaves under Bash.
7. The same input behaves differently under `sh` when the syntax is not portable.
8. Commands that read stdin do not consume unintended script content.
9. The required environment is available.

Example:

```bash
result="$(
    printf '%s\n' \
        'value=41' \
        'printf "%s\n" "$((value + 1))"' |
    bash
)"

test "$result" = "42"
```

## Limitations

Execution through standard input does not provide:

- sandboxing;
- filesystem isolation;
- privilege separation;
- process isolation;
- memory isolation;
- protection from destructive commands;
- a guarantee that no files will be created by executed commands.

Only the script file itself is avoided. The script may still create files, start processes, access the network, or modify the environment according to its privileges.

## Conclusion

Bash can execute source received through standard input without first creating a script file. This is a delivery technique, not a security boundary or an execution sandbox.

The central design rule is:

> Removing the script file changes how source is delivered, not what the resulting Bash process is allowed to do.
