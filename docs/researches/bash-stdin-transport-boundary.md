# Bash Standard Input and Transport Boundaries

## Central Question

Where should the boundary exist between transporting Bash source bytes and interpreting those bytes as shell commands?

## Scope

This research covers the separation between source delivery, byte transport, input decoding, and Bash interpretation.

It does not cover a specific framing protocol, obfuscation, encryption, interpreter selection, or sandboxing.

## Separate the Layers

A reliable design separates these concerns:

```text
source generation
    -> encoding
    -> byte transport
    -> input reconstruction
    -> Bash interpreter
    -> command execution
```

The transport layer should move bytes without interpreting shell syntax. The interpreter should receive only the source and input contract it is expected to process.

## Encoding

The sender and receiver must agree on the encoding used for source text:

```bash
printf '%s' "$source"
```

The absence of an explicit encoding contract can corrupt non-ASCII text or cause different bytes to be interpreted as different commands.

For predictable delivery, define:

- character encoding;
- newline representation;
- handling of invalid byte sequences;
- whether a terminal or locale can rewrite bytes.

## Input Ownership

When Bash reads a script from standard input, that stream is also the default input source for commands executed by the script.

For example:

```bash
printf '%s\n' 'read value' 'printf "%s\n" "$value"' | bash
```

The `read` command may consume bytes intended to be script source rather than an independent user input stream.

A design that needs both script delivery and command input must allocate separate channels or define explicit multiplexing rules.

## Transport Must Preserve Order

The byte transport must preserve ordering and report truncation. It may split or combine writes, but it must not silently reorder, duplicate, or drop bytes.

A transport boundary should define behavior for:

- partial writes;
- partial reads;
- premature EOF;
- timeouts;
- invalid encoding;
- extra bytes after the script;
- stream closure.

## Framing Is Separate

If multiple scripts or messages share one byte stream, the receiver needs framing before it can identify where one script ends and another begins.

The interpreter should not be responsible for discovering transport message boundaries. It should receive a complete source unit or an explicitly defined input stream.

## Verification Strategy

Test with:

1. ASCII source;
2. non-ASCII source;
3. source split at every byte boundary;
4. premature EOF;
5. extra bytes after a complete source unit;
6. commands that read standard input;
7. different newline representations;
8. invalid byte sequences.

## Conclusion

Bash execution from standard input is reliable only when byte transport, source encoding, stream ownership, and message boundaries are explicit.

The central design rule is:

> The transport moves bytes; the interpreter assigns shell meaning only after the input boundary has been established.
