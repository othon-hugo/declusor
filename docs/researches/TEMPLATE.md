# Technical Research Template

This document defines the standard structure for writing atomic technical researches.

## Purpose

A research records a technical learning that can be reused beyond the original implementation context. It explains a mechanism, the evidence used to understand it, the limits of the conclusion, and the practical decision that follows.

Researches are investigative documents. They are not normative specifications, changelogs, complete tutorials, or collections of unrelated notes.

## Atomicity Rule

Each research must answer one central technical question.

A research is atomic when it has:

1. one primary mechanism or boundary;
2. one falsifiable hypothesis;
3. one coherent set of experiments or observations;
4. one direct practical conclusion;
5. explicit non-goals separating adjacent topics.

Do not combine topics merely because they appear in the same delivery pipeline. Source transformation, compression, framing, authentication, and compatibility should be separate researches when each requires a different question or experiment.

## Research Categories

| Category           | Focus                                                                      |
| :----------------- | :------------------------------------------------------------------------- |
| **Execution**      | How code or commands are interpreted and which runtime state they require. |
| **Representation** | How source, binary data, or structured values are transformed.             |
| **Framing**        | How a byte stream is divided into complete messages.                       |
| **Transport**      | How bytes move, are buffered, and preserve ordering or lifecycle.          |
| **Security**       | How authenticity, integrity, isolation, or boundary enforcement works.     |
| **Performance**    | How size, latency, CPU, memory, or throughput should be measured.          |
| **Compatibility**  | Which runtime, format, or version assumptions must hold.                   |
| **Testing**        | How a behavior or contract can be verified independently.                  |

A document may mention adjacent categories, but it should not investigate them in depth. Link to a separate research when necessary.

## Standard Structure

Every research should use the following reasoning structure whenever applicable:

1. `Central Question`
2. `Scope`
3. `Hypothesis`
4. Mechanism or observation
5. Minimal experiment
6. Failure modes and limits
7. Verification strategy
8. Practical conclusion

The exact section names may be adapted for readability, but the reasoning structure must remain visible.

## Standard Template

````markdown
# <Atomic Research Title>

## Central Question

<One question that can be answered through technical reasoning or experiment.>

## Scope

This research covers:

- <mechanism included>;
- <boundary included>;
- <behavior included>.

It does not cover <adjacent topic>, <separate mechanism>, or <unrelated concern>.

## Hypothesis

<State the expected behavior and the conditions under which it should hold.>

## <Mechanism or Observation>

<Explain the smallest mechanism necessary to answer the central question.>

```text
<small conceptual diagram or data flow>
```

## Minimal Experiment

<Provide a small reproducible experiment that can confirm or refute the hypothesis.>

```python
# or another appropriate language
```

Expected observation:

- <observable result>;
- <relevant invariant>;
- <condition that would falsify the hypothesis>.

## Failure Modes and Limits

Document cases where the mechanism does not work or where the conclusion no longer applies:

- <failure mode>;
- <boundary condition>;
- <resource or compatibility limit>.

Do not imply stronger guarantees than the experiment supports.

## Verification Strategy

List focused checks that another person can reproduce:

1. <normal case>;
2. <partial or boundary case>;
3. <invalid or adversarial case>;
4. <compatibility or lifecycle case>.

## Practical Conclusion

<State the decision or reusable lesson in a short paragraph.>

The central design rule is:

> <One concise rule derived from the research.>
````

## Writing Guidelines

### Keep the Question Narrow

Prefer:

> How does a length prefix preserve message boundaries when reads are partial?

Avoid:

> How does the entire communication system work?

The first question can be tested with a focused parser experiment. The second contains many independent topics.

### Separate Mechanisms From Properties

A mechanism explains how something works. A property explains what it guarantees.

For example:

- a delimiter is a framing mechanism;
- resistance to accidental collision is a property;
- confidentiality is a separate security property.

Do not claim a property merely because a mechanism appears to support it.

### Distinguish Facts From Assumptions

Mark whether a statement comes from:

- an experiment;
- a language or protocol definition;
- an implementation observation;
- a measured benchmark;
- an assumption that still needs validation.

### Include Negative Results

Document trade-offs, incompatible conditions, resource limits, and cases where a seemingly simpler solution is unsafe.

### Keep Examples Reproducible

Examples should be minimal, state their runtime assumptions, produce an observable result, and avoid relying on timing or environment accidents when possible.

### Avoid Coupling

Researches should remain useful outside the codebase that motivated them. Prefer generic terminology, standard-library examples, conceptual diagrams, and public references.

Do not make a conclusion depend on an internal module name or private implementation detail.

### Avoid Scope Creep

Create a separate research when a new topic introduces a different:

- central question;
- threat model;
- measurement method;
- compatibility boundary;
- lifecycle model;
- failure policy.

## Review Checklist

Before accepting a research, verify:

- [ ] The title describes one technical topic.
- [ ] There is exactly one central question.
- [ ] Scope and non-scope are explicit.
- [ ] The hypothesis is falsifiable.
- [ ] The mechanism is explained without unrelated implementation detail.
- [ ] At least one reproducible experiment is included.
- [ ] Failure modes and limits are documented.
- [ ] Security claims are no stronger than the evidence.
- [ ] The conclusion is practical and reusable.
- [ ] The document does not duplicate a specification or another research.
- [ ] Examples do not depend on private paths or names.
- [ ] The file contains no credentials, secrets, or environment-specific data.
