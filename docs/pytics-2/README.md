# Pytics 2.0 project memory

This directory is the durable source of truth for Pytics 2.0.

Chat context is not a substitute. When an approved decision changes, update the relevant document and the decision log in the same change.

These documents record product and architecture direction. They do not by themselves authorize implementation. No Pytics 2.0 production code is to be written until a slice is explicitly approved under [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md). TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 are approved for their recorded scopes only.

The released codebase remains Pytics 1.1.5. It is a functional and historical reference. It is not the 2.0 specification, and it is not inherited automatically. See [BASELINE_1_1_5.md](BASELINE_1_1_5.md).

Established: 2026-10-03, from the Pytics 2.0 bootstrap briefing. Architecture and methodology update: 2026-10-03, recorded as DEC-036 through DEC-061. Slice 001, recorded the same day as DEC-062, DEC-063, and TSK-001, was accepted by the project owner as the development baseline. TSK-002, basic column evidence and Empty/Constant inference, was completed the same day on that baseline. TSK-003, physical Boolean inference after Empty and Constant, was completed the same day. TSK-004, physical Datetime inference after that chain, was completed the same day. TSK-005, physical Timedelta inference after that chain, was completed the same day. That completes the planned strong-physical-type semantics phase. The Semantic Foundation Review was then consolidated into these documents the same day, as DEC-064 through DEC-076. That consolidation is documentation only. It does not authorize heuristic semantic inference. TSK-006, the universal column-evidence foundation, was completed the same day after that consolidation and is recorded as [DEC-077](DECISIONS.md#dec-077). It does not add a semantic reading and does not authorize a later slice. TSK-007, frequency and cardinality evidence, was completed the same day and is recorded as [DEC-078](DECISIONS.md#dec-078). It adds observations only and does not authorize a later slice. TSK-008, numeric-structure evidence, was completed the same day and is recorded as [DEC-079](DECISIONS.md#dec-079). It adds observations only and does not authorize a later slice. TSK-009, string-structure evidence, was completed the same day and is recorded as [DEC-080](DECISIONS.md#dec-080). It adds observations only and does not authorize a later slice. TSK-010, pattern evidence, was completed the same day and is recorded as [DEC-081](DECISIONS.md#dec-081). It adds observations only and does not authorize a later slice. The next implementation slice has not been selected. None of TSK-001 through TSK-010 authorizes a later slice.

## Status labels

Use these labels exactly. Do not upgrade a label without a new decision.

| Label | Meaning |
| --- | --- |
| Accepted | Approved product, architecture, or process rule. |
| Proposed / not yet finalized | Under consideration. Named in the briefing, but not approved as a decision. |
| Future investigation | Deferred on purpose. Not a commitment to build it. |
| Out of scope | Explicitly excluded. |

## Recording convention

The briefing mixes binding rules with qualified lists.

- A rule stated as a decision, a hard principle, or an accepted part of the design is **Accepted**.
- A named concept under an accepted area is recorded as **in scope**. Words such as "such as", "may", "where meaningful", "where useful", and "where possible" are preserved. They are not rewritten into "always compute every item".
- Wording such as "proposed", "being considered", "potential", "not yet finalized", or "exact API is not frozen" stays **Proposed / not yet finalized**.
- "Should be investigated", and capabilities the briefing places outside the default core, stay **Future investigation** unless the briefing also sets a binding boundary. The boundary itself is Accepted. The deferred capability is not.
- "Is not" and "do not add" are **Out of scope**.

This convention is a documentation rule so the briefing is not silently tightened or loosened. If a qualified list was meant to be a closed mandatory catalog, or only a set of examples, that confirmation is [OPEN-001](DECISIONS.md#open-questions).

## How the files fit together

| File | Role |
| --- | --- |
| [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) | Identity, audience, principles, and product behavior. |
| [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) | Analytical contract A–N and the semantic model. Requirement IDs live here. |
| [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) | Report structure, navigation, and the three disclosure levels. |
| [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) | Accepted architectural direction and constraints. Not a frozen module layout. |
| [STATISTICAL_METHODS.md](STATISTICAL_METHODS.md) | Inferential rules and accepted methodological direction. The method catalog is not finalized. |
| [DEPENDENCIES.md](DEPENDENCIES.md) | 1.1.5 dependency inventory and 2.0 candidate directions. Not a lock. |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | How slices are opened. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 are complete. No later slice is approved. The semantic-foundation architecture is consolidated. The next implementation slice is not selected. |
| [DECISIONS.md](DECISIONS.md) | Accepted decisions (`DEC-###`) and open questions (`OPEN-###`). |
| [PROGRESS.md](PROGRESS.md) | Requirement → task → files → tests → verification → completion. |
| [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md) | Required procedure for every implementation slice. |
| [BASELINE_1_1_5.md](BASELINE_1_1_5.md) | What 1.1.5 actually is. Not a claim that it meets this specification. |

## Requirement and decision IDs

- `DEC-###` — an accepted decision. Defined only in [DECISIONS.md](DECISIONS.md).
- `OPEN-###` — a question that still needs a product or architecture decision. Not a decision.
- `REQ-###` — an accepted requirement, defined in the specification files and tracked in [PROGRESS.md](PROGRESS.md).
- `TSK-###` — an implementation task. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 exist. None completes a requirement row.

## What not to do with this directory

- Do not treat class names, function signatures, or the engine diagram as a frozen file layout. The diagram is accepted direction ([DEC-036](DECISIONS.md#dec-036)).
- Do not install or pin the 2.0 dependency stack from the candidate directions.
- Do not invent About-page narrative, motivation, or contact details.
- Do not mark implementation work complete in [PROGRESS.md](PROGRESS.md) until the protocol's verification step has been recorded.
- Do not "correct" 1.1.5 so that it appears to satisfy 2.0.
