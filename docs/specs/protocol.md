# Protocol & Contract Invariants Specification

This document specifies the behavioral stream contracts, framing protocols, channel demultiplexing, and signal translation rules governing Declusor transports and client sessions using Lean BDD.

### PRO-01: Exact Byte Count Read Accumulation & Premature EOF Invariant

Byte stream transports reading an exact count of bytes must accumulate incoming chunks until the requested count is satisfied; reaching premature stream EOF raises `ConnectionClosed` to prevent corrupted message deserialization.

```gherkin
Scenario: Reject premature stream termination during exact read
  Given an open transport stream containing fewer bytes than requested
  When an exact byte read operation is executed
  Then reading fails with ConnectionClosed indicating the expected versus received byte counts
```

### PRO-02: Non-Negative Read Count Barrier

Exact byte read requests must enforce non-negative byte count requests; negative counts raise an invalid argument error, while zero bytes returns an empty byte sequence immediately without stream I/O.

```gherkin
Scenario: Enforce non-negative count bounds on exact reads
  Given a request to read a negative byte count (such as -1)
  When an exact byte read operation is attempted
  Then reading fails with an invalid argument error
```

### PRO-03: Transport and Listener Guaranteed Scoped Cleanup

Transport connections and network listeners must guarantee resource teardown upon exiting their execution scope; unhandled errors must propagate cleanly without leaking operating system socket descriptors.

```gherkin
Scenario: Guarantee resource teardown upon scope exit
  Given an active transport or listener within a managed execution scope
  When an error occurs during execution within the scope
  Then the network resource is closed upon scope exit and the original error propagates
```

### PRO-04: Unbuffered Direct Binary Output Invariant

Binary output streaming in presentation views must write raw bytes directly to the unbuffered binary standard output stream; bypassing text encoding layers prevents `UnicodeDecodeError` crashes during binary streaming.

```gherkin
Scenario: Stream raw binary payloads without text decoding
  Given a raw binary byte sequence containing non-UTF-8 characters
  When the payload is output through the presentation view
  Then bytes are written directly to the binary output buffer without decoding errors
```

### PRO-05: Input Source Signal Translation Invariant

Terminal input sources must catch terminal control signals (such as EOF and interrupt) and translate them into a clean termination indicator (`None`) to prevent unhandled control flow exceptions.

```gherkin
Scenario: Translate terminal interrupt and EOF signals
  Given an active terminal input source receiving an EOF signal (Ctrl+D)
  When a user command line is requested
  Then the input source returns None cleanly without raising an unhandled exception
```

### PRO-06: Python Agent TLV Framing Protocol Contract

Communication with Python socket agents must adhere to 5-byte Type-Length-Value (TLV) framing (1-byte channel, 4-byte big-endian length), streaming standard output and error chunks, and consuming any payload attached to an exit frame before stream termination.

```gherkin
Scenario: Demultiplex TLV framed packets and consume exit payload
  Given an incoming stream delivering standard output TLV frames followed by an exit frame with payload
  When response frames are read from the connection
  Then standard output chunks are yielded and the exit payload is consumed before stream termination
```

### PRO-07: POSIX Shell Dynamic Envelope Delimiter Contract

Commands executed against POSIX shell clients must prefix payloads with a dynamic nonce delimiter, and response streaming must demultiplex incoming chunks by stripping the trailing dynamic delimiter without truncating command output.

```gherkin
Scenario: Demultiplex response chunks across sliding delimiter window
  Given a shell command response ending with a dynamic delimiter split across two consecutive read chunks
  When chunks are read from the connection
  Then all command output is yielded intact and the delimiter token is excluded from output
```

### PRO-08: Active Command Nonce Prerequisite for Shell Reading

Reading from a POSIX shell connection requires an active command nonce to have been set by a preceding write or handshake; attempting to read without an active nonce raises `ConnectionError` to prevent unbounded stream listening.

```gherkin
Scenario: Reject reading without an active command nonce
  Given a newly initialized shell connection that has not performed a write or handshake
  When a stream read operation is initiated
  Then reading fails with ConnectionError("No active command nonce for read operation.")
```
