# Pytics 2.0 project memory

This directory is the durable source of truth for Pytics 2.0.

Chat context is not a substitute. When an approved decision changes, update the relevant document and the decision log in the same change.

These documents record product and architecture direction. They do not by themselves authorize implementation. No Pytics 2.0 production code is to be written until a slice is explicitly approved under [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md). TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, and TSK-024 are approved for their recorded scopes only.

The released codebase remains Pytics 1.1.5. It is a functional and historical reference. It is not the 2.0 specification, and it is not inherited automatically. See [BASELINE_1_1_5.md](BASELINE_1_1_5.md).

Established: 2026-10-03, from the Pytics 2.0 bootstrap briefing. Architecture and methodology update: 2026-10-03, recorded as DEC-036 through DEC-061. Slice 001, recorded the same day as DEC-062, DEC-063, and TSK-001, was accepted by the project owner as the development baseline. TSK-002, basic column evidence and Empty/Constant inference, was completed the same day on that baseline. TSK-003, physical Boolean inference after Empty and Constant, was completed the same day. TSK-004, physical Datetime inference after that chain, was completed the same day. TSK-005, physical Timedelta inference after that chain, was completed the same day. That completes the planned strong-physical-type semantics phase. The Semantic Foundation Review was then consolidated into these documents the same day, as DEC-064 through DEC-076. That consolidation is documentation only. It does not authorize heuristic semantic inference. TSK-006, the universal column-evidence foundation, was completed the same day after that consolidation and is recorded as [DEC-077](DECISIONS.md#dec-077). It does not add a semantic reading and does not authorize a later slice. TSK-007, frequency and cardinality evidence, was completed the same day and is recorded as [DEC-078](DECISIONS.md#dec-078). It adds observations only and does not authorize a later slice. TSK-008, numeric-structure evidence, was completed the same day and is recorded as [DEC-079](DECISIONS.md#dec-079). It adds observations only and does not authorize a later slice. TSK-009, string-structure evidence, was completed the same day and is recorded as [DEC-080](DECISIONS.md#dec-080). It adds observations only and does not authorize a later slice. TSK-010, pattern evidence, was completed the same day and is recorded as [DEC-081](DECISIONS.md#dec-081). It adds observations only and does not authorize a later slice. TSK-011, the candidate-assessment foundation and the Identifier candidate, was completed the same day and is recorded as [DEC-082](DECISIONS.md#dec-082). It does not select a semantic reading and does not authorize a later slice. TSK-012, Numeric, Categorical, and Text candidate assessments, was completed the same day and is recorded as [DEC-083](DECISIONS.md#dec-083). It does not select a semantic reading and does not authorize a later slice. TSK-013, string vocabulary and text-structure evidence, was completed the same day and is recorded as [DEC-084](DECISIONS.md#dec-084). It adds observations only, does not select a semantic reading, and does not authorize a later slice. TSK-014, the semantic resolution foundation, was completed the same day and is recorded as [DEC-085](DECISIONS.md#dec-085). It resolves structural readings and already produced candidate assessments. It does not assign confidence to a candidate-derived selection, does not integrate that resolver into the precedence chain, and does not authorize a later slice. TSK-015, the inferred interpretation foundation, was completed the same day and is recorded as [DEC-086](DECISIONS.md#dec-086). It records the post-resolution inferred state, including abstention and ambiguity. It preserves a structural interpretation and does not assign confidence to a candidate-derived selection. It does not enter the precedence chain, and it does not authorize a later slice. TSK-016, column-level semantic pipeline integration, was completed the same day and is recorded as [DEC-087](DECISIONS.md#dec-087). It composes the existing semantic components for one Series and returns the existing inferred result. It does not assign confidence to a candidate-derived selection, does not change `profile` or `compare`, and does not authorize a later slice. TSK-017, dataset observation and column-analysis retention, was completed the same day and is recorded as [DEC-088](DECISIONS.md#dec-088). It analyzes one DataFrame by retaining one column analysis per physical column. It does not add a semantic rule, does not change `profile` or `compare`, and does not authorize a later slice. TSK-018, the dataset overview foundation, was completed the same day and is recorded as [DEC-089](DECISIONS.md#dec-089). It summarizes an existing dataset analysis. It does not rescan the DataFrame, does not change `profile` or `compare`, and does not authorize a later slice. TSK-019, the variables and column-summary foundation, was completed the same day and is recorded as [DEC-090](DECISIONS.md#dec-090). It summarizes each column of that analysis. It does not rescan the DataFrame, does not change `profile` or `compare`, and does not authorize a later slice. TSK-020, the numeric descriptive-analysis foundation, was completed the same day and is recorded as [DEC-091](DECISIONS.md#dec-091). It describes a column only after that column is selected as Numeric. It does not change semantic inference, does not change `profile` or `compare`, and does not authorize a later slice. TSK-021, the Boolean descriptive-analysis foundation, was completed the same day and is recorded as [DEC-092](DECISIONS.md#dec-092). It counts true and false values only after that column is selected as Boolean. It does not change semantic inference, does not change `profile` or `compare`, and does not authorize a later slice. TSK-022, the missing-data analysis foundation, was completed on 2026-10-04 and is recorded as [DEC-093](DECISIONS.md#dec-093). It records exact missingness structure for one DataFrame. It does not infer a missingness mechanism, does not change `profile` or `compare`, and does not authorize a later slice. TSK-023, the duplicate-data analysis foundation, was completed on 2026-10-04 and is recorded as [DEC-094](DECISIONS.md#dec-094). It records exact duplicate rows for one DataFrame. It does not treat duplication as an error, does not change `profile` or `compare`, and does not authorize a later slice. TSK-024, the numeric relationship-analysis foundation, was completed on 2026-10-04 and is recorded as [DEC-095](DECISIONS.md#dec-095). It describes selected Numeric × selected Numeric pairs with Spearman and Pearson. It does not implement other relationship families, does not change `profile` or `compare`, and does not authorize a later slice. The next implementation slice has not been selected. None of TSK-001 through TSK-024 authorizes a later slice.

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
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | How slices are opened. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, and TSK-024 are complete. No later slice is approved. The semantic-foundation architecture is consolidated. TSK-016 connects that foundation for one Series. TSK-017 retains that column analysis on a DataFrame. TSK-018 summarizes that analysis as a dataset overview. TSK-019 summarizes each column as a variable. TSK-020 adds finite-population descriptive statistics for a selected Numeric column. TSK-021 adds true and false counts for a selected Boolean column. TSK-022 records exact missingness structure. TSK-023 records exact duplicate rows. TSK-024 describes selected Numeric × selected Numeric pairs. The next implementation slice is not selected. |
| [DECISIONS.md](DECISIONS.md) | Accepted decisions (`DEC-###`) and open questions (`OPEN-###`). |
| [PROGRESS.md](PROGRESS.md) | Requirement → task → files → tests → verification → completion. |
| [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md) | Required procedure for every implementation slice. |
| [BASELINE_1_1_5.md](BASELINE_1_1_5.md) | What 1.1.5 actually is. Not a claim that it meets this specification. |

## Requirement and decision IDs

- `DEC-###` — an accepted decision. Defined only in [DECISIONS.md](DECISIONS.md).
- `OPEN-###` — a question that still needs a product or architecture decision. Not a decision.
- `REQ-###` — an accepted requirement, defined in the specification files and tracked in [PROGRESS.md](PROGRESS.md).
- `TSK-###` — an implementation task. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, and TSK-024 exist. None completes a requirement row.

## What not to do with this directory

- Do not treat class names, function signatures, or the engine diagram as a frozen file layout. The diagram is accepted direction ([DEC-036](DECISIONS.md#dec-036)).
- Do not install or pin the 2.0 dependency stack from the candidate directions.
- Do not invent About-page narrative, motivation, or contact details.
- Do not mark implementation work complete in [PROGRESS.md](PROGRESS.md) until the protocol's verification step has been recorded.
- Do not "correct" 1.1.5 so that it appears to satisfy 2.0.
