# Cross-Cutting Business Rules Specification

This document specifies system-wide cross-cutting business rules, dependency injection conventions, and process execution standards governing Declusor composition roots and runners using Lean BDD.

### XCT-01: Dynamic Application Factory Signature Introspection

When composing application targets, factories must be invoked using dynamic signature introspection to supply optional dependencies only when declared, avoiding speculative exception catching that masks internal errors.

```gherkin
Scenario: Supply dependencies dynamically based on factory parameter signature
  Given an application factory declaring specific dependency parameters (such as listener factory)
  When the application is composed
  Then matching dependencies are provided and undeclared optional arguments are omitted
```

### XCT-02: Deterministic Process Exit Code Mapping

The main composition root must catch all domain and unhandled exceptions, translating execution outcomes into deterministic operating system exit codes: `0` for clean exit or help display, `1` for operational or domain failures, and `2` for configuration or argument parsing errors.

```gherkin
Scenario: Map CLI execution outcomes to deterministic exit codes
  Given a CLI invocation encountering an argument parsing error
  When the process terminates
  Then the process exit code is strictly 2
```

### XCT-03: Dual-Stream Standard Output / Error Channel Isolation

Terminal output streams must maintain strict channel hygiene: operational errors and diagnostic traces must be directed exclusively to standard error (`stderr`), while interactive prompts, banner rendering, and command outputs must be directed to standard output (`stdout`).

```gherkin
Scenario: Isolate diagnostic error messages from standard output
  Given an error condition occurring during command-line execution
  When error diagnostic messages are emitted
  Then messages are written exclusively to standard error without contaminating standard output
```

### XCT-04: Command-Aware Readline Input Completion & Asset Scoping

Terminal input autocompletion must scope file searches dynamically based on command semantics and plugin assets: `load` autocompletes from the active plugin's `assets/modules/` directory when available, while `upload` and `execute` default to the host working directory, and explicit host paths (`./...`, `/...`) resolve against the local filesystem. `Application.run` supplies the active plugin assets directory via dynamic signature introspection. Non-essential artifacts and caches (such as `__pycache__`, `.git`, `.venv`, `.pyc`, and editor swap files) are excluded from candidate completion via configurable blocklists.

```gherkin
Scenario: Scope load command autocomplete to plugin payload modules
  Given an active session with a plugin defining an assets/modules repository
  When the operator presses tab after typing "load "
  Then autocomplete candidates are discovered from the plugin's modules directory rather than repository root

Scenario: Exclude noise artifacts and caches from autocomplete candidates
  Given a target directory containing standard cache and metadata artifacts (such as __pycache__ or .pyc)
  When the operator triggers filename autocomplete
  Then candidate results omit blocked paths and extensions matching the active blocklist
```
