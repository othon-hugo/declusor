# In-Memory Execution Is Not Sandboxing

## Central Question

Why does avoiding a file or temporary artifact fail to provide a security boundary for executed code?

## Scope

This research distinguishes delivery location from isolation and covers process privileges, filesystem access, network access, subprocesses, memory, and resource limits.

It does not cover a particular interpreter, framing protocol, encryption scheme, or operating-system sandbox implementation.

## Storage Is Not Authority

Executing code from memory may avoid creating a source file, but the code still runs inside a process with existing privileges.

The process may still:

- read and write files;
- open network connections;
- create subprocesses;
- inspect environment variables;
- access inherited file descriptors;
- consume CPU and memory;
- terminate or affect the host process.

Avoiding a filesystem artifact changes storage behavior, not authority.

## Process Isolation

A namespace, virtual machine, container, or separate process can provide an isolation boundary only when its policy and implementation actually restrict access.

A new interpreter namespace alone is not process isolation:

```python
first: dict[str, object] = {}
second: dict[str, object] = {}
```

Separate dictionaries do not prevent both executions from accessing the same process resources.

## Filesystem Access

Memory-resident code can still use normal filesystem APIs. A script may create files even when its own source was never stored.

A file-free delivery policy must not be described as a file-access restriction.

## Resource Exhaustion

A process may be denied a file while still consuming unbounded:

- memory;
- CPU time;
- subprocesses;
- descriptors;
- output buffers;
- network bandwidth.

Isolation requires explicit resource limits and enforcement.

## Verification Strategy

Test the actual boundary rather than the delivery mechanism:

1. attempt filesystem access;
2. attempt network access;
3. inspect inherited environment;
4. create a subprocess;
5. allocate memory;
6. consume CPU;
7. attempt process termination;
8. verify configured restrictions independently.

## Conclusion

In-memory execution can reduce artifacts and change delivery, but it does not sandbox code. Security claims must name the concrete authority and isolation mechanism that enforces them.

The central design rule is:

> A lack of files is not evidence of a lack of privileges.
