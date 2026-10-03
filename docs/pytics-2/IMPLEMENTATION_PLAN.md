# Implementation plan

Status: **TSK-001 and TSK-002 are complete. No later slice is approved.**

Pytics 2.0 implementation has started only for Slice 001 and Slice 002. This file does not sequence the rest of the analytical contract, and it does not assign priority. Sequencing beyond those slices is [OPEN-037](DECISIONS.md#open-questions).

## Authorization

An accepted requirement is not permission to code. A slice starts only when [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md) steps 1–3 are written down and the slice is approved, and only for the requirement IDs named in that scope.

Outside an approved slice:

- do not add a package or module for 2.0;
- do not modify 1.1.5 production code;
- do not change `pyproject.toml` dependencies;
- do not implement the engine, result classes, or method registry;
- do not install or pin the candidate stack in [DEPENDENCIES.md](DEPENDENCIES.md).

Accepting architectural direction is not approval of a slice. The end state is replacement inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). In-place migration is [DEC-063](DECISIONS.md#dec-063). TSK-001 and TSK-002 are the only slices approved under that rule.

## How a future slice is opened

1. Name the `REQ-###` IDs from [PROGRESS.md](PROGRESS.md).
2. Write the scope, including what is deliberately excluded.
3. Write acceptance criteria that can be checked against the specification.
4. Assign `TSK-###` in [PROGRESS.md](PROGRESS.md) and set those requirements to Scoped.
5. Only then implement, and only that slice.
6. Stop at protocol step 12.

If the slice needs a decision that is still `OPEN-###`, stop and record the question. Do not resolve it in code.

## Holds that block related work

| Hold | Effect |
| --- | --- |
| `REQ-T-04`, [DEC-027](DECISIONS.md#dec-027), [DEC-060](DECISIONS.md#dec-060) | No installation and no version pins. Candidate directions are not a lock. |
| `REQ-K-03`, `REQ-T-03` | No frozen method catalog. The registry concept is accepted. Do not implement it until [OPEN-039](DECISIONS.md#open-questions) is decided. |
| `REQ-L-06`, `REQ-P-03` | No AutoML, tuning, leaderboards, cleaning framework, or prescriptive product. |
| [OPEN-004](DECISIONS.md#open-questions) | No commitment to function signatures or illustrative `ProfileReport` / `ComparisonReport` attribute names. |
| [OPEN-013](DECISIONS.md#open-questions) | No selection of a diagnostic estimator. |
| [OPEN-041](DECISIONS.md#open-questions) | No silent choice of a Plotly static-export mechanism for PDF. |

## Traceability

[PROGRESS.md](PROGRESS.md) is the register that must stay able to show:

```text
requirement → implementation task → source files → tests → verification → completion
```

No requirement row in that register is completed. TSK-001 and TSK-002 are completed tasks. They do not complete REQ-S-01, REQ-S-02, REQ-S-04, or REQ-S-05.

## Reuse of 1.1.5

Reuse of a 1.1.5 algorithm, test, threshold, or template is a deliberate choice inside an approved slice, recorded as a decision if it sets or changes architecture. It is not the default, and it is not scheduled here. See [BASELINE_1_1_5.md](BASELINE_1_1_5.md) and [DEC-001](DECISIONS.md#dec-001). TSK-001 did not reuse a 1.1.5 algorithm.

## TSK-001

Slice 001, core semantic foundation. Approved 2026-10-03. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-01, REQ-S-02, and REQ-S-05, as foundation only. The slice does not implement semantic inference, so those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- A typed physical dtype vocabulary and an objective classifier for pandas dtypes, using pandas dtype predicates and dtype classes rather than exact dtype-string equality.
- Families: boolean, integer, floating, complex, string, object, categorical, datetime, timezone-aware datetime, timedelta, period, interval, and an other/extension fallback. Ordered categoricals stay categorical. `categorical_ordered` records the physical ordered flag and is not an ordinal inference.
- The minimum semantic vocabulary: Numeric, Categorical, Boolean/Binary, Text/String, Datetime, Timedelta, Identifier, Constant, and Empty. Ordinal is not a member. Subtype is an optional string and is not a taxonomy.
- User-facing confidence: High, Medium, Low. No numeric score.
- Inference source: inferred; directly supported by physical dtype; explicitly configured by the user.
- A small immutable evidence value and a small immutable interpretation value carrying type, optional subtype label, confidence, evidence, alternatives, source, and physical dtype.
- Internal modules under `src/pytics/semantics/`. That path does not freeze [OPEN-045](DECISIONS.md#open-questions) and does not freeze public names ([OPEN-004](DECISIONS.md#open-questions)).
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063).

### Exclusions

Do not implement identifier detection, uniqueness thresholds, high cardinality, near-constant detection, string-versus-category inference, URL, email, or path detection, datetime parsing from strings, binary token dictionaries, numeric continuous/discrete inference, missing-like literals, ordinal inference, confidence scoring, semantic sampling, target eligibility, or anomaly eligibility.

Do not change `pytics.profile` or `pytics.compare`. Do not export the new types from top-level `pytics`. Do not add a second package. Do not delete 1.1.5 code. Do not add a dependency. Do not implement statistics, findings, or rendering.

### Acceptance criteria

1. Existing `profile()` and `compare()` public behavior is unchanged.
2. No second Pytics package was created.
3. A typed physical dtype vocabulary exists.
4. Objective pandas physical dtype classification exists.
5. The classifier uses modern pandas dtype APIs rather than the old int64/float64-only approach.
6. The accepted semantic-type vocabulary can be represented without implementing semantic heuristics.
7. High, Medium, and Low confidence is represented.
8. Inference source is represented.
9. Semantic evidence has a small typed representation.
10. Semantic interpretation has a small immutable typed representation.
11. No semantic thresholds or heuristic inference rules were introduced.
12. No new runtime dependency was introduced.
13. Focused tests pass.
14. Existing regression tests remain at least at their documented baseline.
15. Project memory accurately records what was and was not implemented.
16. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 16 passed for TSK-001.

## TSK-002

Slice 002, basic column evidence and Empty/Constant inference. Approved 2026-10-03 after the project owner accepted the Slice 001 codebase as the development baseline. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-01, REQ-S-02, REQ-S-04, and REQ-S-05, only for basic counts and the Empty/Constant rules. REQ-S-03 is respected on this path and is not completed. Those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- A frozen `BasicColumnEvidence` value with `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing`.
- Exact full-column collection from a pandas Series, using pandas missingness. No sampling. No mutation. No conversion of missing-like strings.
- Empty when `n_non_missing == 0`. Constant when the column is not empty and `n_unique_non_missing == 1`. Empty is tested first.
- A Slice 001 `SemanticInterpretation` for those two results, with physical dtype from `classify_physical_dtype`, source inferred, confidence High, and one evidence statement derived from the counts.
- `None` when neither rule applies. No unknown semantic type.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The definitions follow [DEC-046](DECISIONS.md#dec-046). This slice does not resolve [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not implement Boolean/Binary, Numeric, Continuous/Discrete, Identifier, Categorical, Text, string patterns, datetime inference from strings, Timedelta analysis, Ordinal, cardinality thresholds, near-constant, high cardinality, missing-like literal reporting, sampling, relationships, findings, target analysis, anomalies, compare/drift, HTML, PDF, a configuration API, or a public result API.

Do not store the constant value. Do not report Empty or Constant as dataset-level facts. Do not change `pytics.profile` or `pytics.compare`. Do not export the new types from top-level `pytics`. Do not add a dependency. Do not rewrite Slice 001.

### Acceptance criteria

1. Accepted Slice 001 behavior remains intact.
2. Basic column evidence has a typed representation.
3. `n_total` is computed exactly.
4. `n_missing` is computed exactly.
5. `n_non_missing` is computed exactly.
6. `n_unique_non_missing` is computed exactly.
7. No sampling is used for these counts.
8. Empty is inferred exactly when there are zero non-missing observations.
9. Constant is inferred exactly when there is one unique non-missing observation and the column is non-empty.
10. Empty takes precedence over Constant.
11. Columns that are neither empty nor constant receive no semantic interpretation from this slice.
12. Physical dtype information is reused from Slice 001.
13. No Boolean, Numeric, Categorical, Text, Identifier, or Ordinal heuristic was added.
14. Missing-like strings are not silently treated as missing.
15. The input Series is not mutated.
16. Semantic evidence is attached to Empty and Constant interpretations.
17. Inference source is represented as inferred.
18. No numeric confidence score was introduced.
19. No new dependency was added.
20. Existing `profile()` and `compare()` behavior is unchanged.
21. Focused tests pass.
22. Existing regression tests remain at least at their documented baseline.
23. Project memory records the slice without overstating requirement completion.
24. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 24 passed for TSK-002.
