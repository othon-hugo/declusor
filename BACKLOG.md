# Declusor Engineering Roadmap & Backlog

This document outlines high-level capabilities, architectural milestones, and the product evolution roadmap based on operational field experience.

## 1. Multi-Session & Reconnect Architecture

Manage multiple concurrent targets, reconnect workflows, and privilege transitions from a single control point.

- [x] **Autonomous Plugin Architecture**
  - Modular, self-contained client plugins discovered dynamically across workspace, user, and system locations.
  - Automated contract conformance verification across all built-in and external plugins.
- [ ] **Multi-Session Management**
  - Concurrent connection handling and queuing on a single listener endpoint.
  - Granular session lifecycle states to track active, backgrounded, connecting, and closed sessions.
  - Interactive session switching to navigate between connected targets without dropping sessions.
  - Seamless backgrounding to return to the management console during active operations.
- [ ] **Correlated Session Reconnect**
  - Grouping and lineage tracking to associate secondary or elevated sessions with their original access point.
  - Seamless hand-off when compromised processes restart or dial back.
- [ ] **Privilege Elevation Spawning**
  - Triggering secondary payload execution directly from an unprivileged session into elevated target contexts.
  - Automated elevation leveraging available target credentials or administrative roles.

## 2. Process Contexts, Subsessions & Structured Concurrency

Provide flexible execution contexts, asynchronous tasks, interactive terminal allocation, and timeout protection.

- [x] **In-Memory Remote Execution**
  - Pure in-memory payload staging and execution avoiding target disk forensics.
  - Deterministic stream synchronization to eliminate command output collisions.
  - Signal isolation protecting persistent reverse connections from accidental terminal interrupt cancellations.
- [x] **Pluggable Execution Interfaces**
  - Clean separation between core session engine and presentation layers.
  - Extensible engine architecture accommodating interactive consoles, automated daemons, and agent interfaces.
- [ ] **Background Task Management**
  - Asynchronous task dispatching on the target returning managed job identifiers.
  - Monitoring, status querying, and resource inspection for long-running remote tasks.
  - On-demand retrieval of buffered standard output and error streams.
  - Safe termination of running remote background tasks.
- [ ] **Interactive Pseudo-Terminal Support**
  - Full terminal emulation with window resize handling for interactive text editors, monitors, and administrative shells.
- [ ] **Bounded Execution Timeouts**
  - Configurable execution deadlines for commands and automated operations.
  - Graceful cancellation and cleanup when operations exceed execution bounds without dropping the underlying session.

## 3. Lateral Pivoting, Tunnels & Proxying

Route network traffic through compromised targets and automate multi-step network pivoting workflows.

- [x] **Target Network Reconnaissance**
  - Target-side network socket probing and local interface enumeration.
  - Host availability sweeps, service port scanning, and host pivoting evaluation modules.
- [ ] **Port Forwarding Tunnels**
  - **Local Port Forwarding**: Exposing remote internal network services directly on the operator host through the active session stream.
  - **Remote Port Forwarding**: Exposing operator services on remote target network interfaces.
- [ ] **Integrated Dynamic Proxying**
  - Built-in dynamic proxy server on the operator host routing tool traffic through target agents.
- [ ] **Automated Pivoting Workflows**
  - Composite multi-step routines for network mapping, automated tunnel setup, and bulk data collection.

## 4. Transport, Protocol & Architecture Hardening

Maintain robust architectural boundaries, authenticated communication channels, and rigorous verification standards.

- [x] **Contract-First Core Architecture**
  - Rigorous type safety and static contract boundaries eliminating duck-typing and dynamic reflection.
  - Centralized domain models, immutable transfer objects, and strict downward-only layer dependencies.
- [x] **Transport Layer Composition & Capability Validation**
  - Composable transport pipelines providing stream obfuscation and data integrity protection.
  - Fail-fast capability negotiation preventing protocol mismatches before establishing connections.
- [x] **Multiplexed Binary Framing**
  - Binary framing isolating standard output, standard error, input, control signals, and process exit codes.
  - Protective payload bounds guarding against resource exhaustion.
- [x] **Deterministic Testing SDK & Challenge Labs**
  - Comprehensive, mock-free test double framework for deterministic integration and unit verification.
  - Multi-stage, containerized challenge labs validating practical post-exploitation workflows.
- [ ] **Authenticated Encryption Transport**
  - Cryptographically authenticated transport layer featuring ephemeral key exchange and data confidentiality.
- [ ] **Remote Signal Propagation**
  - Propagating cancellation and interrupt signals directly to target subprocesses over dedicated control channels.
- [ ] **Configurable Frame Boundaries**
  - Operator-configurable payload size boundaries across binary protocol streams.

## 5. Target Assets, Delivery & Usability

Minimize target footprints, eliminate telemetry noise, provide flexible delivery options, and streamline engagements.

- [x] **Single-Socket Stager Micro-Framework**
  - Ultra-compact initial loaders retrieving full runtime payloads in-memory over the initial socket without connection teardown.
  - Configurable delivery formats supporting both micro-loaders and self-contained standalone payloads.
  - Silent clipboard delivery utilizing terminal escape protocols alongside terminal and file output modes.
- [x] **Execution Wrapper Templating**
  - Custom execution wrappers enabling tailored command invocation across staging and standalone payloads.
- [x] **Target Anti-Corruption Libraries & Noise Filtering**
  - Multi-tool fallback chains for encoding, compression, archiving, network retrieval, and system inspection.
  - Target-side error suppression ensuring missing utilities and permission denials never pollute operator output.
  - Vendor-agnostic capability hierarchy organizing modules by operational domain.
  - Custom asset tree overrides with development artifact filtering in interactive completions.
- [ ] **Session Transcript Recording**
  - Comprehensive logging capturing inputs, outputs, module runs, and forensic metadata into structured audit records.
- [ ] **In-Session Payload Re-Inspection**
  - On-demand inspection and copying of the active deployment payload during an active session for secondary pivots.

## 6. Operator Infrastructure & Resource Development

Maintain operator-side state, persistent intelligence, shared assets, and multi-operator collaboration independently of individual target sessions.

- [ ] **Centralized Loot & Intelligence Store**
  - Persistent, structured repository for harvested artifacts, credentials, keys, network maps, and host snapshots.
  - Cross-session aggregation providing queryable engagement data rather than scattered console output.
- [ ] **Typed Credential Registry**
  - Deduplicated credential catalog tracking capture origin, source process, verification state, and access level.
  - Direct integration into lateral movement planning and credential-reuse workflows.
- [ ] **Target Knowledge Base**
  - Dynamic host profiles recording network topology, reached privilege boundaries, and active session lineage.
  - Automated state updates as sessions are established, elevated, migrated, or closed.
- [ ] **Listener Profiles & Staging Automation**
  - Named, reusable listener profiles defining transport, port, encoding, and timing specifications.
  - Persistent payload catalog categorized by target platform, delivery mode, and operational tier.
  - Integrated staging services delivering runtime payloads on demand with request-level audit tracking.
  - Operator-controlled relay and redirection infrastructure decoupling listeners from observed network addresses.
- [ ] **Multi-Operator Collaboration & Auditability**
  - Concurrent multi-operator session access supporting real-time observation, review, and dual-operator workflows.
  - Append-only event journals recording all operator commands, file transfers, and lifecycle state changes.
  - Non-intrusive annotation layer attaching contextual notes and tags to sessions, findings, and targets.
