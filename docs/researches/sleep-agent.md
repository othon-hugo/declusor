# Agent Sleep, Dormancy, and Survivability Lifecycle

## Central Question

How can an autonomous agent transition between active communication and dormancy to balance state preservation, host and network observability, and operational survivability across pause boundaries?

## Scope

This research covers:

- control loop pause, sleep conditions, and state transitions;
- wake condition validation, stale trigger rejection, and idempotent re-entry;
- taxonomy of operational dormancy modes:
  1. Active Polling with Stochastic Jitter;
  2. Bounded Retry and Self-Termination (Deadman Switch / Bounded Teardown);
  3. Disk-Staged Cold Hibernation (0-RAM footprint, process eviction, scheduled revival);
  4. In-Memory Hot Sleep Masking (socket teardown, ephemeral scope obfuscation);
  5. Out-of-Band Remote Re-Activation (passive listening, trigger signals, external dispatch);
- mathematical modeling of interval jitter against network flow periodicity analysis (FFT/autocorrelation);
- multi-dimensional trade-offs between resident RAM footprint, disk forensic exposure, and network telemetry;
- platform constraints and failure boundaries (OS file locking, interpreter memory arenas, NAT state expiration).

It does not cover general distributed task scheduling engines, cryptographic key exchange protocols, framing specifications, or stream cipher implementations.

## Hypothesis

An autonomous agent maintains correctness, operational survivability, and minimal observability when:

1. Pause and wake transitions are governed by an explicit state machine with reason validation;
2. Dormancy modes are tailored to the threat model, balancing resident memory footprint against disk persistence and network traffic telemetry;
3. Repetitive connection failures are bounded by deterministic retry budgets that trigger defensive self-teardown before detection occurs.

The mechanism fails when wake conditions are evaluated without freshness checks, when sleep loops generate rigid periodic network signatures, or when unhandled errors leave persistent orphaned processes in host memory.

## Sleep and Wake State Machine

A comprehensive agent dormancy lifecycle extends beyond a simple sleep timer into a coordinated state machine:

```text
RUNNING
  │
  ├─► IDLE ──► SLEEP_EVALUATION
  │              │
  │              ├─► ACTIVE_JITTER_SLEEP  ──(timer)───────► WAKE_VALIDATION ──► RUNNING
  │              ├─► HOT_MEMORY_MASK      ──(timer/signal)► DECRYPT_SCOPE    ──► WAKE_VALIDATION ──► RUNNING
  │              ├─► COLD_DISK_HIBERNATE  ──► SNAPSHOT ──► PROCESS_EXIT ──(os_scheduler)──► REHYDRATE ──► RUNNING
  │              ├─► PASSIVE_DORMANT      ──(inbound_trig)► WAKE_VALIDATION  ──► RUNNING
  │              └─► RETRY_EXHAUSTION     ──► SCRUB_STATE ──► UNLINK_LAUNCHER ──► TERMINATE_CLEAN
  │
  └── WAKING ──► VALIDATION_FAILED ──► IDLE / TERMINATE
```

The key invariant is that pausing execution requires explicit boundary management. Waiting in memory, hibernating to disk, and listening for remote wakeups each present distinct failure domains that must converge on validated re-entry or deterministic termination.

## The Sleep Condition Must Be Explicit

A sleep agent should define the exact condition that governs its pause:

- scheduled wake timestamp;
- arrival of an authentic trigger token;
- completion of an external dependency;
- expiration of a bounded retry budget;
- administrative cancellation signal.

If the sleep condition is implicit, the agent risks waking spuriously or failing to wake at all. An explicit dormancy policy distinguishes:

- scheduled timer expiration;
- authentic remote wake trigger;
- administrative cancellation;
- network disconnect timeout;
- stale or replayed delivery.

## State Preservation Across Dormancy Boundaries

Before entering dormancy, the agent must persist or snapshot all context necessary to resume correctly:

- current operational phase and task identifier;
- execution cursor, command queue offset, or session token;
- consecutive failure counter and retry budget limit;
- ephemeral session keys or encryption context;
- absolute deadline or expiration timestamp.

In hot in-memory dormancy, state remains in volatile memory under defensive protection. In cold hibernation, state is serialized to a protected checkpoint on disk, allowing the host process to terminate completely.

## Wake-Up Validation and Stale Trigger Rejection

A wake event is only safe when validated against the agent's active state. Stale, expired, or duplicate triggers must be rejected before scheduling work:

```python
import time
from typing import Any

state: dict[str, Any] = {
    "task_id": "job-101",
    "phase": "waiting",
    "deadline": time.monotonic() + 30.0,
    "cancelled": False,
}


def validate_wake(reason: str, event_task_id: str | None = None) -> str:
    if state["cancelled"]:
        return "cancelled"

    if reason == "timer":
        if time.monotonic() >= state["deadline"]:
            return "resume"
        return "premature_wake"

    if reason == "event":
        if event_task_id == state["task_id"]:
            return "resume"
        return "ignored_stale_event"

    return "wait"
```

This validation barrier prevents the agent from replaying expired actions or reacting to obsolete network packets after state transitions.

## Taxonomy of Operational Dormancy Modes

### Mode 1: Active Polling with Stochastic Jitter

When an agent must periodically poll a coordinator while remaining resident in memory, deterministic sleep intervals create prominent periodic signatures in network telemetry (e.g., flow logs, NetFlow, Zeek beacon detection).

To suppress periodicity, the base sleep interval $T_{\text{base}}$ is randomized with a jitter ratio $j \in [0.0, 1.0]$:

$$T_{\text{sleep}} = T_{\text{base}} \times (1 + \mathcal{U}(-j, +j))$$

For example, with $T_{\text{base}} = 60\text{s}$ and $j = 0.3$, the actual sleep interval varies uniformly between $42\text{s}$ and $78\text{s}$. This variance disrupts autocorrelation algorithms and Fast Fourier Transform (FFT) frequency analysis used by network intrusion detection systems.

### Mode 2: Bounded Retry and Self-Termination (Deadman Switch)

Unbounded connection loops are a critical vulnerability: an agent that retries connection endlessly to an offline coordinator generates continuous, detectable network anomalies and leaves orphaned processes running indefinitely.

A bounded retry policy enforces:

1. **Failure Budget**: Maximum consecutive failed connection attempts (`max_retries`).
2. **Absolute Expiration**: A fixed wall-clock kill-date (`kill_date`).
3. **Defensive Self-Teardown**: Upon budget exhaustion or deadline expiration, the agent:
   - Scrubs sensitive variables and session keys from memory;
   - Flushes and closes all open transport sockets;
   - Unlinks the launcher/stager script from disk (`os.unlink`);
   - Terminates cleanly (`sys.exit(0)`).

### Mode 3: Disk-Staged Cold Hibernation (Process Eviction)

In environments subject to frequent memory inspection, process listing audits (`ps -ef`, Task Manager), or volatile memory acquisition, a resident agent process presents an ongoing footprint.

Cold hibernation eliminates the in-memory presence entirely:

1. The agent serializes its minimal session state and wake deadline into a local checkpoint file;
2. It registers an OS-level deferred execution trigger (e.g., user `cron` entry, `systemd --user` timer, `at` command, or an external loop runner);
3. The running agent process exits completely (`exit 0`), returning memory to the OS;
4. Upon timer trigger, a lightweight launcher re-executes, reads the checkpoint, verifies freshness, unlinks the state file, and resumes the session.

**Trade-off**: Memory presence drops to zero during sleep, but a temporary filesystem artifact is created, trading memory detection for forensic disk artifact risk.

### Mode 4: In-Memory Hot Sleep Masking

When writing to disk is unacceptable (fileless operational mandate), the agent remains resident in RAM but camouflages its state during dormancy:

1. **Socket Teardown**: Active TCP sockets are closed before entering sleep, removing visible `ESTABLISHED` or `CLOSE_WAIT` connections from `ss` and `netstat`;
2. **In-Place Scrambling**: In-memory session dictionaries, configuration strings, and code buffers are XOR-masked or encrypted with an ephemeral one-time key generated immediately prior to sleeping;
3. **Monotonic Wait**: The thread executes a sleep call using monotonic time;
4. **Rehydration**: Upon timer expiration, memory buffers are unmasked using the ephemeral key, the key is overwritten, and a fresh socket connection is established.

### Mode 5: Out-of-Band Remote Re-Activation (Passive Dormancy)

Rather than polling outbound, the agent generates zero egress network traffic while dormant:

1. The agent binds to a local listening socket or listens passively for an external wakeup signal (e.g., specific packet knocking sequence, ICMP payload token, or query to a public dead-drop channel);
2. Upon receiving and authenticating the wake signal, the agent initiates an outbound connection back to the coordinator;
3. **Trade-off**: Eliminates outbound beacon traffic entirely, but passive listening sockets are visible in local network tables (`LISTEN` status), and firewalls/NATs block inbound packets without port forwarding or hole punching.

## Comparative Decision Matrix

| Dormancy Mode                    | RAM Footprint      | Disk Forensics        | Egress Telemetry     | Ingress Exposure     | Operator Responsiveness           | Privilege Required |
| :------------------------------- | :----------------- | :-------------------- | :------------------- | :------------------- | :-------------------------------- | :----------------- |
| **Active Jitter Polling**        | Continuous (low)   | None (fileless)       | Periodic (jittered)  | None                 | Medium ($T_{\text{interval}}$)    | Standard user      |
| **Bounded Retry Self-Teardown**  | Zero on failure    | Cleaned / unlinked    | Bounded, then zero   | None                 | N/A (terminal)                    | Standard user      |
| **Disk-Staged Cold Hibernation** | Zero while asleep  | Staging file artifact | None during sleep    | None                 | High latency ($T_{\text{sched}}$) | User / Cron        |
| **In-Memory Hot Sleep Masking**  | Masked / disguised | None (fileless)       | None during sleep    | None                 | Medium ($T_{\text{interval}}$)    | Standard user      |
| **Out-of-Band Remote Trigger**   | Continuous (idle)  | None (fileless)       | Zero until triggered | Listening port / raw | Immediate on trigger              | Port bind / Raw    |

## Minimal Reproducible Experiments

### Experiment 1: Jitter Interval Dispersion

Demonstrates how uniform jitter disperses inter-arrival intervals across a range, eliminating rigid periodic beaconing:

```python
import random
import statistics


def calculate_jittered_intervals(base: float, jitter: float, count: int) -> list[float]:
    intervals = []
    for _ in range(count):
        delta = random.uniform(-jitter, jitter) * base
        intervals.append(round(base + delta, 2))
    return intervals


base_interval = 60.0
jitter_ratio = 0.30  # +/- 30%
samples = calculate_jittered_intervals(base_interval, jitter_ratio, 1000)

assert min(samples) >= base_interval * (1 - jitter_ratio)
assert max(samples) <= base_interval * (1 + jitter_ratio)
assert round(statistics.mean(samples)) == 60
# Variance proves non-periodicity
assert statistics.variance(samples) > 50.0
```

### Experiment 2: Bounded Retry and Self-Deletion

Demonstrates bounded retry budget exhaustion, file self-unlinking, and clean exit handling:

```python
import os
import tempfile


def simulate_agent_retry_budget(max_retries: int, should_succeed: bool) -> str:
    # Create temporary launcher artifact to simulate self-deletion
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"#!/bin/sh\n# declusor launcher")
        launcher_path = f.name

    retries = 0
    connected = False

    while retries < max_retries and not connected:
        if should_succeed and retries == 1:
            connected = True
            break
        retries += 1

    if not connected:
        # Self-teardown barrier: wipe state and unlink binary
        if os.path.exists(launcher_path):
            os.unlink(launcher_path)
        return f"terminated_deadman: unlinked={not os.path.exists(launcher_path)}"

    # Clean up on success
    if os.path.exists(launcher_path):
        os.unlink(launcher_path)
    return "connected"


assert "terminated_deadman: unlinked=True" in simulate_agent_retry_budget(3, False)
assert simulate_agent_retry_budget(3, True) == "connected"
```

### Experiment 3: Cold Hibernation Serialization and Rehydration

Demonstrates state snapshotting to disk, process termination simulation, and state rehydration:

```python
import json
import os
import tempfile
import time


def cold_hibernate(state: dict[str, object], path: str) -> None:
    serialized = json.dumps(state)
    with open(path, "w", encoding="utf-8") as f:
        f.write(serialized)


def cold_rehydrate(path: str) -> dict[str, object] | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
    os.unlink(path)  # Defensively wipe staging file upon wake
    return data


with tempfile.NamedTemporaryFile(delete=False) as tmp:
    checkpoint_file = tmp.name

initial_state = {"session_token": "tok_xyz", "counter": 42, "deadline": time.time() + 300}
cold_hibernate(initial_state, checkpoint_file)

# Process terminates here; new process launches and rehydrates
resumed_state = cold_rehydrate(checkpoint_file)

assert resumed_state == initial_state
assert not os.path.exists(checkpoint_file)  # Checkpoint must be wiped
```

### Experiment 4: In-Memory Hot Scope Scrambling

Demonstrates ephemeral XOR obfuscation of session dictionaries during in-memory sleep:

```python
import os


def mask_payload(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


plain_payload = b"SECRET_SESSION_TOKEN_AND_DISPATCH_QUEUE"
ephemeral_key = os.urandom(16)

# Before entering sleep: mask buffer
masked = mask_payload(plain_payload, ephemeral_key)
assert masked != plain_payload

# Waking from sleep: unmask buffer with key, then erase key
recovered = mask_payload(masked, ephemeral_key)
assert recovered == plain_payload
del ephemeral_key
```

## Failure Modes and Limits

1. **OS File Locking on Self-Deletion**:
   On Windows systems, attempting to `os.unlink()` a currently running executable fails with a sharing violation (`ERROR_ACCESS_DENIED` / `PermissionError`). Self-deletion on Windows requires spawning a detached helper process (or batch script) that waits for parent process termination before deleting the binary.
2. **CPython Heap Memory Allocation Retention**:
   In Python runtimes, deleting variables (`del obj`) or running garbage collection (`gc.collect()`) releases objects to the interpreter's internal arena pool, but CPython rarely returns freed virtual memory back to the operating system heap (`brk`/`mmap`). Sensitive plaintext strings previously allocated may remain visible in `/proc/<pid>/mem` or core dumps unless overwritten in-place using mutable `bytearray` buffers.
3. **NAT and Stateful Firewall Session Timeouts**:
   In passive or long-delay dormancy modes, intermediate NAT routers drop connection tracking states after typical idle timeouts (e.g., 30–300 seconds). Agents attempting to reuse persistent sockets across long sleep intervals experience silent packet drops or RST packets upon wake.
4. **Clock Skew and NTP Stepping**:
   Using wall-clock time (`time.time()`) for sleep calculations is vulnerable to NTP synchronization steps and daylight saving adjustments. A backward clock adjustment can cause an agent to sleep indefinitely; a forward jump can cause premature kill-date self-termination. Monotonic clocks (`time.monotonic()`) must be used for all relative sleep intervals.
5. **Transient Network Partition False-Positives**:
   A retry budget set too aggressively (e.g., $N=2$ with short intervals) can trigger self-teardown during temporary network glitches, prematurely killing the agent.

## Verification Strategy

1. **Jitter Statistical Bound Check**:
   Verify that 10,000 generated sleep intervals strictly satisfy $[T_{\text{base}}(1-j), T_{\text{base}}(1+j)]$ with no cluster spikes.
2. **Retry Exhaustion Barrier Check**:
   Simulate coordinator unavailability; verify that retry counter reaches limit, launcher file is deleted from disk, and process exits cleanly with code 0.
3. **Kill-Date Expiration Check**:
   Set an expired deadline; verify that the agent refuses to initiate network connections and executes defensive teardown immediately.
4. **Cold Hibernation Round-Trip Check**:
   Serialize state, confirm process exit, relaunch bootstrap, verify state rehydration, and confirm state file removal.
5. **In-Memory Masking Integrity Check**:
   Confirm that session payloads are scrambled during wait periods and recovered without byte corruption.
6. **Cancellation Resilience Check**:
   Trigger an administrative cancel signal during sleep; verify that the sleep aborts cleanly without re-entering the work queue.

## Practical Conclusion

Dormancy is not a uniform delay loop; it is a multi-dimensional engineering trade-off balancing resident memory footprint, disk forensic exposure, and network traffic periodicity. Operational survivability requires matching the dormancy strategy to the environment's monitoring posture, mitigating traffic detection with stochastic jitter, and establishing bounded retry budgets with deterministic self-teardown to prevent persistent orphaned processes.

The central design rules are:

> 1. Pausing execution requires explicit wake validation; stale triggers, replayed packets, and unverified timeouts must never initiate work.
> 2. Periodic operations must incorporate stochastic jitter, and connection attempts must be strictly bounded by retry budgets and clean self-teardown barriers.
