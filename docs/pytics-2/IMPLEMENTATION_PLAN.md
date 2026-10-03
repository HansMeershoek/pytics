# Implementation plan

Status: **TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 are complete. No later slice is approved.** The strong-physical-type phase is complete. The Semantic Foundation Review has been consolidated into project memory. TSK-006 strengthens the universal column-evidence family and does not add a semantic reading. TSK-007 adds frequency observations and does not add a semantic reading. TSK-008 adds numeric-structure observations and does not add a semantic reading. TSK-009 adds string-structure observations and does not add a semantic reading. TSK-010 adds pattern observations and does not add a semantic reading. It does not select the next slice.

Pytics 2.0 implementation has started only for Slice 001, Slice 002, Slice 003, Slice 004, Slice 005, Slice 006, Slice 007, Slice 008, Slice 009, and Slice 010. This file does not sequence the rest of the analytical contract, and it does not assign priority. Sequencing beyond those slices is [OPEN-037](DECISIONS.md#open-questions). Evidence-based inference does not start from this file. The next implementation slice is not selected.

## Authorization

An accepted requirement is not permission to code. A slice starts only when [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md) steps 1–3 are written down and the slice is approved, and only for the requirement IDs named in that scope.

Outside an approved slice:

- do not add a package or module for 2.0;
- do not modify 1.1.5 production code;
- do not change `pyproject.toml` dependencies;
- do not implement the engine, result classes, or method registry;
- do not install or pin the candidate stack in [DEPENDENCIES.md](DEPENDENCIES.md).

Accepting architectural direction is not approval of a slice. The end state is replacement inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). In-place migration is [DEC-063](DECISIONS.md#dec-063). TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 are the only slices approved under that rule.

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
| [DEC-066](DECISIONS.md#dec-066) | Candidate Resolution v0.1 uses no numeric total-score. [DEC-042](DECISIONS.md#dec-042) still permits a future statistically justified numeric confidence. |
| [DEC-074](DECISIONS.md#dec-074), [OPEN-014](DECISIONS.md#open-questions) | No heuristic `{0, 1}` or string-token Binary inference until a binary-not-Boolean reading can be represented. |
| [DEC-064](DECISIONS.md#dec-064), [OPEN-045](DECISIONS.md#open-questions) | The semantic pipeline is not a module layout. |

## Traceability

[PROGRESS.md](PROGRESS.md) is the register that must stay able to show:

```text
requirement → implementation task → source files → tests → verification → completion
```

No requirement row in that register is completed. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 are completed tasks. They do not complete REQ-S-01, REQ-S-02, REQ-S-03, REQ-S-04, REQ-S-05, REQ-S-07, REQ-D-01, REQ-D-02, REQ-D-03, REQ-E-03, REQ-E-04, REQ-F-01, REQ-F-02, REQ-G-01, REQ-G-02, or REQ-H-04.

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

## TSK-003

Slice 003, physical Boolean inference and semantic precedence. Approved 2026-10-03 after the committed Slice 001 and Slice 002 baseline. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-01, REQ-S-02, REQ-S-04, and REQ-S-05, only for composing Empty, Constant, and physical Boolean. REQ-D-01 and REQ-D-03 are touched only for a physical pandas Boolean dtype. REQ-D-02 and REQ-S-03 are respected on this path and are not completed. Those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- Reuse `classify_physical_dtype` and `BasicColumnEvidence`. Classify the physical dtype once. Collect the four basic counts once.
- Reuse `interpret_empty_or_constant_from_evidence`. Do not recompute `isna` or `nunique`, and do not copy the Empty or Constant rules.
- Precedence: Empty, then Constant, then physical Boolean, then no interpretation. `None` means no interpretation. No unknown semantic type.
- Semantic Boolean only when the column is not Empty, not Constant, and `PhysicalDtypeFamily` is Boolean. Native `bool` and nullable pandas `boolean` both qualify. Confidence is High. Source is directly supported by the physical dtype. Evidence is the statement `physical dtype is boolean`. The physical dtype value is retained. Subtype is unset. Alternatives are empty.
- A small orchestration function. No rule engine, registry, or priority framework.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). Precedence over Boolean follows [DEC-046](DECISIONS.md#dec-046). The physical-dtype rule follows [DEC-047](DECISIONS.md#dec-047). This slice does not resolve [OPEN-044](DECISIONS.md#open-questions). It does not set Boolean subtypes ([OPEN-014](DECISIONS.md#open-questions)).

### Exclusions

Do not infer Boolean from `{0, 1}`, yes/no or true/false strings, object values that happen to be `True` and `False`, categorical values that happen to be `True` and `False`, an ordered categorical, or any other two-valued column. Binary cardinality is not Boolean meaning.

Do not implement Numeric, Continuous/Discrete, Identifier, Categorical, Text, datetime semantic inference, timedelta semantic inference, ordinal storage, thresholds, sampling, missing-like detection, near-constant, high cardinality, dataset findings, relationships, statistics, target analysis, anomalies, compare/drift, HTML, PDF, a configuration API, or a public semantic API.

Do not change `pytics.profile` or `pytics.compare`. Do not export the new function from top-level `pytics`. Do not add a dependency. Do not rewrite Slice 001 or Slice 002. Do not add `SemanticType` members.

### Acceptance criteria

1. The accepted checkpoint was clean before this slice, and Slice 001 tests still pass.
2. Slice 002 tests still pass.
3. Empty still takes precedence, including on a physical Boolean column.
4. Constant still takes precedence, including on a physical Boolean column.
5. A non-empty, non-constant physical Boolean column is semantic Boolean.
6. Native `bool` is supported.
7. Nullable pandas `boolean` is supported.
8. That Boolean result uses High confidence.
9. That Boolean result uses the physical-dtype inference source, not inferred.
10. That Boolean result retains the physical dtype.
11. That Boolean result has factual semantic evidence and no numeric score.
12. `{0, 1}` is not inferred Boolean.
13. Boolean-like strings are not inferred Boolean.
14. Object dtype holding Python `True` and `False` is not inferred Boolean.
15. Categorical `True`/`False` is not inferred Boolean.
16. An ordered categorical is not inferred Boolean or ordinal.
17. Other unsupported columns still produce no interpretation.
18. Basic evidence is reused rather than collected again inside the Boolean rule.
19. No semantic threshold was introduced.
20. The input Series is not mutated.
21. No new dependency was added.
22. `profile()` and `compare()` are unchanged, and the new names are not on the public API.
23. Focused tests pass.
24. Existing regression tests remain at least at their documented baseline.
25. Project memory records physical Boolean only, and leaves other Boolean representations open.
26. No unrelated production changes were made.
27. [OPEN-044](DECISIONS.md#open-questions) stays open.
28. No second semantic type was added for binary.
29. Slice 001 and Slice 002 tests were not edited.
30. No rule framework was added.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 30 passed for TSK-003.

## TSK-004

Slice 004, physical Datetime inference and scalable semantic composition. Approved 2026-10-03 after the committed Slice 001, Slice 002, and Slice 003 baseline. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-01, REQ-S-02, REQ-S-04, and REQ-S-05, only for composing Empty, Constant, physical Boolean, and physical Datetime. REQ-E-03 and REQ-E-04 are respected on this path because a Datetime reading is not a time series and no deeper temporal diagnostic is run. REQ-S-03 is respected on this path and is not completed. Those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- Reuse `classify_physical_dtype` and `BasicColumnEvidence`. Classify the physical dtype once. Collect the four basic counts once.
- Reuse `interpret_empty_constant_or_physical_boolean_from_evidence`. Do not recompute `isna` or `nunique`, and do not copy the Empty, Constant, or physical Boolean rules.
- Precedence: Empty, then Constant, then physical Boolean, then physical Datetime, then no interpretation. `None` means no interpretation. No unknown semantic type.
- Semantic Datetime only when the column is not Empty, not Constant, not physical Boolean, and `PhysicalDtypeFamily` is `DATETIME` or `DATETIME_TZ_AWARE`. Both families use `SemanticType.DATETIME`. Confidence is High. Source is directly supported by the physical dtype. Evidence is `physical dtype is datetime` or `physical dtype is timezone-aware datetime`. The physical dtype value is retained, including the timezone-aware family. Subtype is unset. Alternatives are empty. `PhysicalDtype` is not extended with timezone metadata.
- A successor function, `interpret_series_precedence`, calls the Slice 003 chain and then the datetime rule. The Slice 003 function is unchanged. The new name does not list every rule. No rule engine, registry, or priority framework.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). Precedence over later readings follows [DEC-046](DECISIONS.md#dec-046). Native and timezone-aware datetime as strong Datetime evidence follows [DEC-050](DECISIONS.md#dec-050). Confidence stays on the three-level scale in [DEC-042](DECISIONS.md#dec-042). This slice does not resolve [OPEN-044](DECISIONS.md#open-questions) or [OPEN-045](DECISIONS.md#open-questions). It does not set a subtype ([OPEN-014](DECISIONS.md#open-questions)).

### Exclusions

Do not infer Datetime from date-like strings, object values that happen to be Python datetimes or timestamps, integer or floating Unix-like values, categorical timestamps, period dtypes, or timedelta dtypes. Do not call `pd.to_datetime` on source data. Do not parse strings. Do not normalize timezones, convert timezone-aware values to naive values, or convert values to UTC for inference.

Do not implement `SemanticType.TIMEDELTA` inference. Do not treat period as Datetime. Do not infer a time series, frequency, regularity, monotonicity, gaps, calendar patterns, trend, seasonality, or autocorrelation from a Datetime column.

Do not implement Numeric, Continuous/Discrete, Identifier, Categorical, Text, ordinal storage, Boolean from `{0, 1}` or Boolean-like strings, thresholds, sampling, missing-like detection, relationships, statistics, target analysis, anomalies, compare/drift, HTML, PDF, a configuration API, or a public semantic API.

Do not change `pytics.profile` or `pytics.compare`. Do not export the new function from top-level `pytics`. Do not add a dependency. Do not rewrite Slice 001, Slice 002, or Slice 003. Do not add `SemanticType` members.

### Acceptance criteria

1. The accepted checkpoint was clean before this slice, and Slice 001 tests still pass.
2. Slice 002 tests still pass.
3. Slice 003 tests still pass.
4. Empty remains the highest precedence, including an all-missing or zero-length datetime Series.
5. Constant remains above the physical semantic rules, including a repeated timestamp and one timestamp plus missing values.
6. Physical Boolean still works, and it still precedes physical Datetime.
7. A non-empty, non-constant native datetime column is semantic Datetime.
8. A non-empty, non-constant timezone-aware datetime column is semantic Datetime.
9. Datetime with `NaT` is Datetime when the column is not empty and not constant.
10. That Datetime result uses High confidence.
11. That Datetime result uses the physical-dtype inference source.
12. That Datetime result retains the physical dtype.
13. The timezone-aware physical family remains distinguishable from native datetime.
14. That Datetime result has concise factual evidence and no numeric score.
15. Datetime-like strings are not inferred as Datetime.
16. Object dtype holding Python datetime or timestamp values is not inferred as Datetime.
17. Integer and floating Unix-like values are not inferred as Datetime.
18. Timedelta is not inferred as Datetime, and timedelta semantic inference is not implemented.
19. Period is not inferred as Datetime.
20. Categorical timestamps are not inferred as Datetime.
21. A Datetime reading is not treated as a time-series structure.
22. The input Series is not coerced or mutated. Index, name, timezone, and category metadata stay in place.
23. Basic evidence is collected once and reused.
24. Physical classification is performed once on the series path and reused.
25. No semantic threshold was introduced.
26. No numeric confidence score was introduced.
27. No broad inference framework was introduced.
28. Composition stays a direct call from one successor function to the existing Boolean chain, plus one datetime rule.
29. No new dependency was added.
30. `profile()` and `compare()` are unchanged, and the new names are not on the public API.
31. Slice 001, Slice 002, and Slice 003 tests were not edited.
32. Focused tests pass.
33. Existing regression tests remain at their documented baseline, apart from the known PDF failure.
34. Project memory records physical Datetime only, and does not mark datetime analysis or time-series analysis complete.
35. [OPEN-044](DECISIONS.md#open-questions) stays open.
36. [OPEN-045](DECISIONS.md#open-questions) stays open.
37. No unknown, other, or unclassified semantic type was added.
38. No second semantic type was added for timezone-aware datetime.
39. Empty and Constant keep their existing inferred source.
40. No unrelated production changes were made.
41. `PhysicalDtype` was not redesigned.
42. No commit or push was made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 42 passed for TSK-004.

## TSK-005

Slice 005, physical Timedelta inference and completion of the strong physical-type semantics phase. Approved 2026-10-03 after the committed Slice 001, Slice 002, Slice 003, and Slice 004 baseline. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-01, REQ-S-02, REQ-S-04, and REQ-S-05, only for composing Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta. REQ-S-07 is respected on this path because a Timedelta reading is not duration analysis and no unit or statistic is produced. REQ-S-03 is respected on this path and is not completed. Those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- Reuse `classify_physical_dtype` and `BasicColumnEvidence`. Classify the physical dtype once. Collect the four basic counts once.
- Reuse `interpret_precedence_from_evidence` from Slice 004. Do not recompute `isna` or `nunique`, and do not copy the Empty, Constant, physical Boolean, or physical Datetime rules.
- Precedence: Empty, then Constant, then physical Boolean, then physical Datetime, then physical Timedelta, then no interpretation. `None` means no interpretation. No unknown semantic type.
- Semantic Timedelta only when the column is not Empty, not Constant, not physical Boolean, not physical Datetime, and `PhysicalDtypeFamily` is `TIMEDELTA`. The semantic type is `SemanticType.TIMEDELTA`. Confidence is High. Source is directly supported by the physical dtype. Evidence is `physical dtype is timedelta`. The physical dtype value is retained. Subtype is unset. Alternatives are empty. `PhysicalDtype` is not extended with duration-unit or resolution metadata.
- A successor module calls the Slice 004 chain and then the timedelta rule. The Slice 004 function is unchanged. A physical timedelta Series is still `None` from that function. No rule engine, registry, or priority framework.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). Precedence over later readings follows [DEC-046](DECISIONS.md#dec-046). Timedelta stays a duration distinct from Datetime, which stays a point in time, following [DEC-051](DECISIONS.md#dec-051). Confidence stays on the three-level scale in [DEC-042](DECISIONS.md#dec-042). This slice does not implement the duration analysis in [DEC-051](DECISIONS.md#dec-051) or `REQ-S-07`. It does not resolve [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), or [OPEN-045](DECISIONS.md#open-questions).

### Exclusions

Do not infer Timedelta from duration-like strings, clock-like strings, integer or floating magnitudes, object values that happen to be Python `timedelta` or pandas `Timedelta` values, categorical timedeltas, period dtypes, or datetime dtypes. Do not call `pd.to_timedelta` on source data. Do not parse strings. Do not guess units. Do not convert values.

Do not read a physical timedelta as Datetime, or a physical datetime as Timedelta. Do not implement duration statistics, readable-unit presentation, or time-series analysis.

Do not implement Numeric, Continuous/Discrete, Identifier, Categorical, Text, ordinal storage, Boolean from `{0, 1}` or Boolean-like strings, thresholds, sampling, missing-like detection, relationships, statistics, target analysis, anomalies, compare/drift, HTML, PDF, a configuration API, or a public semantic API.

Do not change `pytics.profile` or `pytics.compare`. Do not export the new function from top-level `pytics`. Do not add a dependency. Do not rewrite Slice 001, Slice 002, Slice 003, or Slice 004. Do not add `SemanticType` members.

### Acceptance criteria

1. The accepted checkpoint was clean before this slice, and Slice 001 tests still pass.
2. Slice 002 tests still pass.
3. Slice 003 tests still pass.
4. Slice 004 tests still pass.
5. Slice 001, Slice 002, Slice 003, and Slice 004 tests were not edited.
6. Empty remains the highest precedence, including an all-missing or zero-length timedelta Series.
7. Constant remains above the physical semantic rules, including a repeated duration and one duration plus missing values.
8. Physical Boolean still works, and it still precedes physical Datetime and physical Timedelta.
9. A non-empty, non-constant native datetime column remains semantic Datetime.
10. A non-empty, non-constant timezone-aware datetime column remains semantic Datetime.
11. Neither Datetime reading becomes Timedelta.
12. A non-empty, non-constant physical timedelta column is semantic Timedelta.
13. Timedelta with `NaT` is Timedelta when the column is not empty and not constant.
14. That Timedelta result uses High confidence.
15. That Timedelta result uses the physical-dtype inference source.
16. That Timedelta result retains the physical dtype, and the family remains `TIMEDELTA`.
17. That Timedelta result has the evidence statement `physical dtype is timedelta` and no numeric score.
18. A physical Timedelta reading does not become Datetime.
19. Duration-like strings are not inferred as Timedelta.
20. Clock-like strings are not inferred as Timedelta.
21. Integer and floating duration-like values are not inferred as Timedelta.
22. Object dtype holding Python `timedelta` or pandas `Timedelta` values is not inferred as Timedelta.
23. Categorical timedeltas are not inferred as Timedelta.
24. Period is not inferred as Timedelta.
25. No units are guessed, and the engine does not parse or call `pd.to_timedelta` on source data.
26. The input Series is not coerced or mutated. Index, name, and categorical metadata stay in place.
27. Basic evidence is collected once and reused.
28. Physical classification is performed once on the series path and reused.
29. Empty, Constant, Boolean, and Datetime rules are not copied.
30. No semantic threshold was introduced.
31. No numeric confidence score was introduced.
32. No broad inference framework was introduced.
33. Composition stays a direct call to the Slice 004 precedence, plus one timedelta rule.
34. No new dependency was added.
35. `profile()` and `compare()` are unchanged, and the new names are not on the public API.
36. Focused tests pass.
37. Existing regression tests remain at their documented baseline, apart from the known PDF failure.
38. Project memory records physical Timedelta only, records completion of the strong-physical-type phase, and records a Semantic Foundation Review as the next step.
39. This section does not approve or implement a later slice.
40. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) stay open.
41. No unknown, other, unclassified, or second duration semantic type was added.
42. Empty and Constant keep their existing inferred source.
43. No unrelated production changes were made.
44. `PhysicalDtype` was not given duration-unit metadata.
45. No commit or push was made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 45 passed for TSK-005. Criterion 38 records the project memory at that verification. The status recorded for that verification is [After TSK-005](#after-tsk-005). The current status is [After TSK-010](#after-tsk-010).

## After TSK-005

The planned strong-physical-type semantics phase is complete. The Semantic Foundation Review was consolidated in documentation on 2026-10-03. [DEC-064](DECISIONS.md#dec-064) through [DEC-076](DECISIONS.md#dec-076) record that architecture. No heuristic semantic inference was authorized. No TSK-006 existed at that consolidation. TSK-006 was approved later and is recorded below. The next concrete implementation slice after TSK-006 remains subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)).

Future implementation planning must respect that consolidated architecture: observations kept distinct from candidate assessments; resolution; material alternatives; High, Medium, and Low resolution confidence without a v0.1 numeric total-score; override provenance that preserves the inferred interpretation; and compute-once evidence. Those constraints are not a task and not a module layout ([OPEN-045](DECISIONS.md#open-questions)).

The review agenda that TSK-005 named — precedence, result models, evidence, ambiguity, subtypes, overrides, configuration, thresholds, deterministic versus heuristic rules, interactions among Numeric, Categorical, Text, Identifier, and Binary, and temporary module boundaries — is no longer an open agenda. The accepted parts are the decisions above. The parts that stay open are the `OPEN-###` items those decisions name. That agenda was not a design and was not a slice.

## TSK-006

Slice 006, universal column evidence foundation. Approved 2026-10-03 after the semantic-foundation consolidation. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03 and REQ-S-05, for exact observed characteristics and the prohibition on coercion. REQ-S-01 and REQ-S-04 are respected because Empty and Constant keep their existing readings. Those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- Keep the frozen `BasicColumnEvidence` fields `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing` as the stored primary observations.
- Those four counts remain exact, full-column, and unsampled.
- Derived read-only facts, computed from the stored counts and not stored themselves: `missing_ratio`, `unique_ratio_non_missing`, `has_missing`, `is_empty`, and `is_constant`, with the definitions in [DEC-077](DECISIONS.md#dec-077).
- Undefined ratios are `None`. There is no `unique_ratio` alias.
- Empty and Constant interpretation uses `is_empty` and `is_constant`. Precedence, evidence statements, confidence, and inference source stay as they were.
- The composed chain still classifies the physical dtype once and collects basic evidence once.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The primary-versus-derived contract is [DEC-077](DECISIONS.md#dec-077). This slice narrows [OPEN-044](DECISIONS.md#open-questions) only for the denominator of `unique_ratio_non_missing`. It does not set an Identifier threshold.

### Exclusions

Do not implement a later evidence family. Do not implement value-frequency analysis, dominant-frequency analysis, singleton analysis, UUID, hash, email, URL, path, or datetime-string detection. Do not implement Numeric, Identifier, Categorical, Text, `{0, 1}` Binary, `{0.0, 1.0}` Binary, true/false, or yes/no inference. Do not implement candidate assessments, candidate resolution, material alternatives, new confidence rules, evidence-strength enums, scoring, abstention, user overrides, effective interpretation, ordinal representation, cross-column evidence, dataset-context inference, functional dependencies, downstream profiling statistics, or sampling.

Do not add a provenance object. Do not add an evidence-family inheritance hierarchy. Do not add a generic observation property bag. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). Do not close [OPEN-044](DECISIONS.md#open-questions) beyond the denominator of this one property.

Do not change `pytics.profile` or `pytics.compare`. Do not export the evidence type from top-level `pytics`. Do not add a dependency. Do not approve TSK-007.

### Acceptance criteria

1. The stored fields remain the four primary counts.
2. Those counts stay exact and full-column. No sampling is used for them.
3. `missing_ratio`, `unique_ratio_non_missing`, `has_missing`, `is_empty`, and `is_constant` are computed from the stored counts and are not stored fields.
4. `missing_ratio` is `n_missing / n_total` when `n_total > 0`, and `None` when `n_total == 0`.
5. `unique_ratio_non_missing` is `n_unique_non_missing / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`.
6. An undefined ratio is not `0.0`, `1.0`, NaN, or infinity.
7. There is no `unique_ratio` alias.
8. `has_missing` is `n_missing > 0`.
9. `is_empty` is `n_non_missing == 0`, for both a zero-length Series and an all-missing Series.
10. `is_constant` is `n_non_missing > 0` and `n_unique_non_missing == 1`.
11. A constant non-missing Series, a constant Series with missing observations, and a one-row non-missing Series are constant.
12. A zero-length Series and an all-missing Series are empty and are not constant.
13. A fully unique non-missing Series has `unique_ratio_non_missing == 1.0` and is not interpreted as Identifier.
14. Missing-like literals remain observed values.
15. Unhashable non-missing values still raise `TypeError` and are not normalized.
16. Empty and Constant interpretation uses `is_empty` and `is_constant`.
17. Precedence, evidence statements, confidence, and inferred source for Empty and Constant are unchanged.
18. Physical Boolean, Datetime, timezone-aware Datetime, and Timedelta inference is unchanged.
19. Normal collection obeys the count invariants.
20. The composed chain classifies the physical dtype once and collects basic evidence once.
21. Interpretation from already collected evidence does not scan the Series again.
22. No provenance object was added.
23. No later evidence family and no new semantic reading were added.
24. No public API change and no new dependency.
25. Focused tests pass.
26. The semantic tests for TSK-001 through TSK-006 pass.
27. The full suite stays at the documented baseline apart from the known PDF failure.
28. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) through [OPEN-049](DECISIONS.md#open-049) stay open.
29. [OPEN-044](DECISIONS.md#open-questions) stays open except for the denominator of `unique_ratio_non_missing`.
30. This section does not approve or implement a later slice.
31. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 31 passed for TSK-006.

## After TSK-006

TSK-006 strengthens the universal column-evidence family. It does not add a semantic reading. [DEC-077](DECISIONS.md#dec-077) records the primary-versus-derived contract and the denominator of `unique_ratio_non_missing`. No later evidence family was authorized at that point. TSK-007 was approved later and is recorded below. The next concrete implementation slice after TSK-007 remains subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)).

## TSK-007

Slice 007, frequency and cardinality evidence foundation. Approved 2026-10-03 after TSK-006. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03 and REQ-S-05, for exact observed characteristics and the prohibition on coercion. REQ-S-01 and REQ-S-04 are respected because no new semantic reading was added. Those requirement rows stay Not started. See [PROGRESS.md](PROGRESS.md).

### Scope

- A typed `FrequencyEvidence` value composed with `BasicColumnEvidence`. It is not a subclass and not a property bag.
- Stored observations: `most_frequent_count`, `singleton_count`, and a bounded exact set of distinct non-missing values.
- Derived read-only ratios: `most_frequent_ratio` and `singleton_ratio`, with the denominators in [DEC-078](DECISIONS.md#dec-078).
- The frequency population is non-missing observations. Missing counts stay on basic evidence.
- Exact, full-column, and unsampled collection, from one frequency pass that reuses the basic counts.
- Exact distinct values are retained only while `n_unique_non_missing` is at most 32. That number is a storage limit, not a semantic threshold.
- Above that limit the exact set is absent and the full frequency mapping is not retained.
- The collector is separate. The Empty, Constant, and physical-type chain does not call it.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The frequency contract is [DEC-078](DECISIONS.md#dec-078). This slice does not resolve [OPEN-018](DECISIONS.md#open-questions) or [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not implement Numeric, Identifier, Categorical, Text, Boolean, or Binary inference from frequency facts. Do not implement `{0, 1}` Binary, `{0.0, 1.0}` Binary, true/false, or yes/no inference. Do not implement candidate assessments, candidate resolution, material alternatives, confidence on frequency evidence, evidence roles, evidence-strength enums, scoring, abstention, user overrides, or effective interpretation. Do not implement numeric-structure, string-structure, or pattern evidence. Do not implement sampling, sketches, or approximate cardinality.

Do not add a provenance object. Do not add an evidence-family inheritance hierarchy. Do not add a generic observation property bag. Do not collect frequency evidence from the existing precedence chain. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049).

Do not change `pytics.profile` or `pytics.compare`. Do not export the evidence type from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `FrequencyEvidence` is a frozen dataclass composed with `BasicColumnEvidence`, not a subclass and not a property bag.
2. No placeholder evidence family was added.
3. The stored frequency fields are `most_frequent_count`, `singleton_count`, and `exact_distinct_non_missing_values`. The ratios are properties.
4. No semantic-conclusion field, confidence, or evidence role was added.
5. The frequency population is non-missing observations. Missing values are not keys.
6. `n_missing`, `missing_ratio`, and `has_missing` are not frequency fields.
7. `most_frequent_count` is an int. It is `0` when `n_non_missing` is `0`, and at least `1` otherwise. It is not `None`.
8. `singleton_count` is an int. It is `0` when there is no non-missing observation, and otherwise counts distinct non-missing values that occur once.
9. `most_frequent_ratio` is `most_frequent_count / n_non_missing` when `n_non_missing > 0`, and `None` otherwise. The denominator is the composed basic count.
10. `singleton_ratio` is `singleton_count / n_unique_non_missing` when `n_unique_non_missing > 0`, and `None` otherwise. The denominator is the distinct count. There is no second singleton ratio.
11. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity.
12. The collector does not recompute `n_non_missing` or `n_unique_non_missing`. One frequency pass produces the frequency facts.
13. The exact distinct values are a `frozenset` when `n_unique_non_missing <= 32`, including an empty `frozenset` when that count is `0`. They are `None` when the count is greater than 32.
14. `32` is one named retention constant. It is not used as a semantic threshold.
15. The retained set does not require values to be sortable, and values are not stringified.
16. A result above the limit does not retain the full frequency mapping or the full distinct-value collection.
17. Collection is exact, full-column, and unsampled. No sketch or approximate cardinality was added.
18. Empty frequency facts agree with empty universal evidence.
19. A constant non-missing column has `most_frequent_count == n_non_missing` and `most_frequent_ratio == 1.0`. `singleton_count` is `1` only when that one value occurs once.
20. Missing-like literals remain ordinary values.
21. Unhashable non-missing values still raise `TypeError` and are not normalized, including when a frequency pass can group them.
22. Frequency facts do not select Categorical, Identifier, Text, Boolean, or Binary.
23. The precedence chain does not collect frequency evidence.
24. Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta interpretations are unchanged.
25. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
26. Focused tests pass.
27. TSK-006 tests pass.
28. Semantic tests for TSK-001 through TSK-007 pass.
29. The legacy profiler stays at 19 passed and the known PDF failure.
30. The full suite adds only the new tests, with the same known PDF failure, and coverage remains about 97%.
31. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) through [OPEN-049](DECISIONS.md#open-049) stay open. The retention limit does not close [OPEN-018](DECISIONS.md#open-questions) or [OPEN-044](DECISIONS.md#open-questions).
32. This section does not approve or implement a later slice.
33. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 33 passed for TSK-007.

## After TSK-007

TSK-007 adds exact frequency observations. It does not add a semantic reading. [DEC-078](DECISIONS.md#dec-078) records the frequency contract, including the operational 32-value retention limit. That limit is not a semantic cardinality threshold. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-008 was approved later and is recorded below. This section does not create a later task.

## TSK-008

Slice 008, numeric structure evidence foundation. Approved 2026-10-03 after TSK-007. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03 and REQ-S-05, for exact observed characteristics and the prohibition on coercion. REQ-S-01 and REQ-S-04 are respected because no new semantic reading was added. Those requirement rows stay Not started. Zeros, negatives, and infinities recorded here do not complete REQ-B-01 or REQ-A-07. See [PROGRESS.md](PROGRESS.md).

### Scope

- A typed `NumericStructureEvidence` value composed with `BasicColumnEvidence`. It is not a subclass and not a property bag.
- Applicable only when the physical family is integer or floating, including nullable integer and floating dtypes the existing classifier already treats as those families. Boolean, datetime, timezone-aware datetime, timedelta, categorical, string, object, period, complex, and other non-numeric families raise `TypeError`.
- Stored observations: `finite_count`, `positive_count`, `negative_count`, `zero_count`, `positive_infinity_count`, `negative_infinity_count`, `integer_like_count`, `non_integer_like_count`, `is_non_decreasing`, and `is_non_increasing`.
- Derived read-only ratios: `finite_ratio`, `positive_ratio`, `negative_ratio`, `zero_ratio`, and `integer_like_ratio`, with the denominators in [DEC-079](DECISIONS.md#dec-079).
- Universal counts stay on basic evidence. The collector reuses that evidence and the already classified physical dtype.
- Exact, full-column, and unsampled collection, from one non-missing numeric pass.
- Integer-like classification is exact truncation equality. There is no tolerance.
- Monotonicity is defined only when every non-missing value is finite. Infinities make both flags undefined.
- The collector is separate. The Empty, Constant, and physical-type chain does not call it.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The numeric-structure contract is [DEC-079](DECISIONS.md#dec-079). This slice does not resolve [OPEN-044](DECISIONS.md#open-questions) or [OPEN-046](DECISIONS.md#open-046).

### Exclusions

Do not implement Numeric, Identifier, Categorical, Text, Boolean, or Binary inference from these facts. Do not implement `{0, 1}` Binary, `{0.0, 1.0}` Binary, discrete or continuous subtypes, or ordinal inference. Do not implement a regular step, constant step, step size, or sequential-identifier observation. Do not add min, max, mean, median, mode, variance, standard deviation, quantiles, or other downstream numeric summaries. Do not implement candidate assessments, candidate resolution, material alternatives, confidence on this evidence, evidence roles, scoring, abstention, user overrides, or effective interpretation. Do not coerce strings with `pd.to_numeric`. Do not sample.

Do not add a provenance object. Do not add an evidence-family inheritance hierarchy. Do not add a generic observation property bag. Do not collect this evidence from the existing precedence chain. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049).

Do not change `pytics.profile` or `pytics.compare`. Do not export the evidence type from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `NumericStructureEvidence` is a frozen dataclass composed with `BasicColumnEvidence`, not a subclass and not a property bag.
2. No placeholder evidence family was added.
3. The stored fields are the eight counts and the two monotonicity flags. The ratios are properties. `n_total`, `n_missing`, and `n_non_missing` are not copied.
4. No semantic-conclusion field, confidence, evidence role, or descriptive statistic was added.
5. The collector accepts physical integer and floating families, including nullable `Int64` and `Float64`, and raises `TypeError` for Boolean, string, object, Datetime, timezone-aware Datetime, Timedelta, categorical, period, and complex.
6. Numeric strings are not coerced, and `pd.to_numeric` is not used to make a Series eligible.
7. Counts use non-missing observations. Missing NaN and `pd.NA` are not counted as non-finite numeric evidence.
8. `finite_count + positive_infinity_count + negative_infinity_count == n_non_missing`.
9. `positive_count + negative_count + zero_count == finite_count`. Infinities are not sign counts. `0` and `-0.0` are zero.
10. A finite value is integer-like exactly when it equals its truncation. There is no tolerance. `1.0000000001` is not integer-like.
11. Infinities are neither integer-like nor non-integer-like. `integer_like_count + non_integer_like_count == finite_count`.
12. Ratios use the denominators in [DEC-079](DECISIONS.md#dec-079). An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. A zero numerator with a positive denominator is `0.0`.
13. Monotonicity is `bool` when every non-missing value is finite, and `None` when any infinity is present. Missing values are skipped. Remaining values keep their original row order.
14. Zero non-missing values, one finite value, and a finite constant series are both non-decreasing and non-increasing. A constant infinity leaves both flags `None`.
15. No regular-step, step-size, or sequence-role field was added.
16. The collector reuses the supplied basic evidence and physical dtype. It does not recompute basic counts, reclassify, or collect frequency evidence.
17. Collection is exact, full-column, and unsampled. No provenance object was added.
18. The precedence chain does not collect numeric-structure evidence.
19. Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta interpretations are unchanged.
20. A unique monotonic integer series is not Identifier. `{0, 1}` is not Boolean. `{0.0, 1.0}` is not Binary. Integer-like floats do not create a Numeric subtype.
21. The input Series is not mutated.
22. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
23. Focused tests pass.
24. TSK-007 tests pass.
25. TSK-006 tests pass.
26. Semantic tests for TSK-001 through TSK-008 pass.
27. The legacy profiler stays at 19 passed and the known PDF failure.
28. The full suite adds only the new tests, with the same known PDF failure.
29. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) through [OPEN-049](DECISIONS.md#open-049) stay open. `{0.0, 1.0}` does not close [OPEN-046](DECISIONS.md#open-046). Monotonicity and integer-like counts do not close [OPEN-044](DECISIONS.md#open-questions).
30. This section does not approve or implement a later slice.
31. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 31 passed for TSK-008.

## After TSK-008

TSK-008 adds exact numeric-structure observations for physically numeric columns. It does not add a semantic reading. [DEC-079](DECISIONS.md#dec-079) records the contract, including Boolean exclusion, exact integer-like classification, infinity-aware monotonicity, and on-demand collection. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-009 was approved later and is recorded below. This section does not create a later task.

## TSK-009

Slice 009, string structure evidence foundation. Approved 2026-10-03 after TSK-008. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03 and REQ-S-05, for exact observed characteristics and the prohibition on coercion. REQ-S-01 and REQ-S-04 are respected because no new semantic reading was added. Those requirement rows stay Not started. Empty-string, whitespace, and length observations recorded here do not complete REQ-F-02. Preserving missing-like literals as ordinary strings does not complete REQ-H-04. See [PROGRESS.md](PROGRESS.md).

### Scope

- A typed `StringStructureEvidence` value composed with `BasicColumnEvidence`. It is not a subclass and not a property bag.
- Applicable to a physical string dtype, including the pandas string storage the existing classifier already treats as string, and including an all-missing or zero-length string column.
- Applicable to an object column only when every non-missing value is a Python `str`, tested with `isinstance(value, str)`. An empty or all-missing object column is not eligible.
- Physical categorical storage is not eligible. Boolean, integer, floating, Datetime, timezone-aware Datetime, Timedelta, Period, complex, Interval, mixed object, non-string object, and byte strings raise `TypeError`. Byte strings are not decoded. Physical classification is not changed.
- Stored observations: `empty_string_count`, `whitespace_only_count`, `contains_whitespace_count`, `contains_alpha_count`, `contains_digit_count`, `contains_other_count`, `min_length`, and `max_length`.
- Derived read-only ratios with denominator `n_non_missing`, as in [DEC-080](DECISIONS.md#dec-080). Undefined ratios are `None`.
- Universal counts stay on basic evidence. The collector reuses that evidence and the already classified physical dtype.
- Exact, full-column, and unsampled collection, from one pass over non-missing values. Character classes use Python Unicode string methods. Length is `len` of the original string.
- The collector is separate. The Empty, Constant, and physical-type chain does not call it.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The string-structure contract is [DEC-080](DECISIONS.md#dec-080). This slice does not resolve [OPEN-014](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), or [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not implement Text, Categorical, Identifier, Boolean, Binary, Datetime, or Numeric inference from these facts. Do not implement word counts, token counts, or pattern recognition, including UUID, email, URL, path, hash, phone, date-like, or numeric-like strings. Do not add `PatternEvidence`. Do not coerce with `astype(str)` or an equivalent. Do not treat missing-like literals as missing. Do not sample. Do not add candidate assessments, candidate resolution, material alternatives, confidence on this evidence, evidence roles, scoring, abstention, user overrides, or effective interpretation.

Do not add a provenance object. Do not add an evidence-family inheritance hierarchy. Do not add a generic observation property bag. Do not collect this evidence from the existing precedence chain. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049).

Do not change `pytics.profile` or `pytics.compare`. Do not export the evidence type from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `StringStructureEvidence` is a frozen dataclass composed with `BasicColumnEvidence`, not a subclass and not a property bag.
2. No placeholder evidence family was added.
3. The stored fields are the six counts and the two length bounds. The ratios are properties. `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing` are not copied.
4. No semantic-conclusion field, confidence, evidence role, score, or threshold was added.
5. A physical string dtype is eligible, including nullable string storage and an all-missing or zero-length string Series. Python-backed and the project's `str` string storage are not treated as different semantic cases.
6. An object Series is eligible only when every non-missing value is a Python `str`. `isinstance(value, str)` accepts a `str` subclass. The check covers every non-missing value.
7. An empty object Series and an all-missing object Series raise `TypeError`.
8. A mixed object Series, a numeric object Series, and `bytes` raise `TypeError` and are not stringified.
9. Categorical storage raises `TypeError` even when the labels are strings. Labels are not converted.
10. Boolean, integer, floating, Datetime, timezone-aware Datetime, Timedelta, Period, complex, and Interval raise `TypeError`.
11. Numpy byte-string storage remains a physical string dtype and raises `TypeError` here. It is not decoded. Physical classification is unchanged.
12. Pandas missingness matches basic evidence. `""`, whitespace, `"NA"`, `"N/A"`, `"null"`, `"None"`, and `"?"` remain ordinary strings.
13. An empty string is `value == ""`. It is not whitespace-only. Whitespace-only uses `str.isspace`. Contains-whitespace uses `character.isspace`, so a whitespace-only string also contains whitespace.
14. Alphabetic, digit, and other use `str.isalpha`, `str.isdigit`, and the generic other definition. The same string may increment more than one content count. There is no ASCII-only substitute.
15. Strings are not Unicode-normalized, case-folded, or stripped.
16. Length is `len` of the original string. Both bounds are `None` when `n_non_missing` is 0. An observed empty string may make `min_length` 0.
17. Each ratio divides by `n_non_missing` and is `None` when that count is 0. A zero numerator with a positive denominator is `0.0`. There is no second denominator.
18. No word, token, or pattern observation was added.
19. The facts do not select Text, Categorical, Identifier, Boolean, Binary, Datetime, or Numeric.
20. The collector reuses the supplied basic evidence and physical dtype. It does not recompute basic counts, reclassify, or collect frequency evidence.
21. Collection is exact, full-column, and unsampled. No provenance object was added.
22. The precedence chain does not collect string-structure evidence. Empty and Constant precedence is unchanged.
23. The input Series is not mutated.
24. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
25. Focused tests pass.
26. TSK-008 tests pass.
27. TSK-007 tests pass.
28. TSK-006 tests pass.
29. Semantic tests for TSK-001 through TSK-009 pass.
30. The legacy profiler stays at 19 passed and the known PDF failure.
31. The full suite adds only the new tests, with the same known PDF failure.
32. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) through [OPEN-049](DECISIONS.md#open-049) stay open. Character-class counts and length bounds do not close [OPEN-014](DECISIONS.md#open-questions) or [OPEN-044](DECISIONS.md#open-questions). Empty-string and whitespace counts do not close [OPEN-018](DECISIONS.md#open-questions). The absence of word counts does not close [OPEN-019](DECISIONS.md#open-questions).
33. This section does not approve or implement a later slice.
34. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 34 passed for TSK-009.

## After TSK-009

TSK-009 adds exact string-structure observations for physical string columns and for object columns whose non-missing values are Python strings. It does not add a semantic reading. [DEC-080](DECISIONS.md#dec-080) records the contract, including conditional object applicability, categorical exclusion, Python Unicode character classes, length bounds, ratio denominators, and on-demand collection. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-010 was approved later and is recorded below. This section does not create a later task.

## TSK-010

Slice 010, pattern evidence foundation. Approved 2026-10-03 after TSK-009. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03 and REQ-S-05, for exact observed characteristics and the prohibition on coercion. REQ-S-01 and REQ-S-04 are respected because no new semantic reading was added. Those requirement rows stay Not started. UUID and hexadecimal counts recorded here do not complete REQ-F-02, REQ-G-01, or REQ-G-02. See [PROGRESS.md](PROGRESS.md).

### Scope

- A typed `PatternEvidence` value composed with `StringStructureEvidence`. It is not a subclass of that family or of `BasicColumnEvidence`, and it is not a property bag.
- The collector consumes the Series, the already collected string-structure evidence, and the already classified physical dtype. It does not recollect string structure and does not redefine string eligibility. It rejects inconsistent length, non-missing count, physical dtype name, non-string values, and populations outside the string-structure contract, including an all-missing object column.
- The population is non-missing strings. Empty strings, whitespace-only strings, and missing-like literals stay ordinary non-matches. Nothing is stripped, case-folded, Unicode-normalized, stringified, or decoded.
- Every pattern is a full-value match. The catalog is UUID, IPv4, IPv6, and ASCII hexadecimal tokens of widths 32, 40, 64, and 128.
- UUID accepts only the 36-character hyphenated form and the 32-character compact form. `uuid.UUID` must not widen that shape. No version is required.
- IPv4 and IPv6 use `ipaddress.IPv4Address` and `ipaddress.IPv6Address` on the original string. CIDR syntax does not match. Address properties are not classified.
- Hexadecimal tokens use `0123456789abcdefABCDEF`. They are not named as hash algorithms. Counts may overlap. A compact UUID increments both `uuid_count` and `hex_32_count`.
- Derived read-only ratios with denominator `n_non_missing`, as in [DEC-081](DECISIONS.md#dec-081). Undefined ratios are `None`.
- Universal counts stay on basic evidence, reached through the composed string-structure evidence.
- Exact, full-column, and unsampled collection, from one pass over non-missing strings.
- The collector is separate. The Empty, Constant, and physical-type chain does not call it. String-structure collection does not call it.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The pattern contract is [DEC-081](DECISIONS.md#dec-081). This slice does not resolve [OPEN-014](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), or [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not implement Identifier, Text, Categorical, Boolean, Binary, Datetime, or Numeric inference from these facts. Do not recognize email, URL, URI, path, phone, postal code, credit-card-like text, date-like text, datetime-like text, time-like text, numeric-like text, JSON, XML, HTML, MAC address, hostname, base64, or a generic identifier pattern. Do not name hexadecimal widths as hash algorithms. Do not add a pattern registry, a winner, a threshold, or a confidence. Do not coerce with `astype(str)` or an equivalent. Do not strip or Unicode-normalize before matching. Do not sample. Do not add candidate assessments, candidate resolution, material alternatives, evidence roles, scoring, abstention, user overrides, or effective interpretation.

Do not add a provenance object. Do not add an evidence-family inheritance hierarchy. Do not add a generic observation property bag. Do not collect this evidence from the existing precedence chain or from string-structure collection. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049).

Do not change `pytics.profile` or `pytics.compare`. Do not export the evidence type from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `PatternEvidence` is a frozen dataclass composed with `StringStructureEvidence`, not a subclass and not a property bag.
2. No generic pattern registry or observation bag was added.
3. The stored fields are `string_structure` and the seven counts. The ratios are properties. `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing` are not copied.
4. No semantic-conclusion field, confidence, evidence role, score, threshold, winner, or matched-value collection was added.
5. The collector reuses the supplied string-structure evidence and physical dtype. It does not recollect string structure, basic counts, or frequency evidence, and it does not reclassify the physical dtype.
6. It rejects inconsistent length, non-missing count, physical dtype name, non-string values, and populations outside the string-structure contract, including an all-missing object column and `bytes`.
7. The population is non-missing strings. `""`, whitespace, and missing-like literals remain ordinary non-matches. Nothing is stripped, case-folded, Unicode-normalized, stringified, or decoded.
8. Every pattern is a full-value match. Embedded syntax and surrounding whitespace do not match.
9. UUID accepts only the canonical 36-character form and the compact 32-character form, in either case. Braces, URN prefixes, misplaced hyphens, and non-hex characters do not match. No UUID version is required. `uuid.UUID` does not widen the shape.
10. IPv4 uses `ipaddress.IPv4Address` on the original string. IPv6 uses `ipaddress.IPv6Address`. CIDR, malformed, and embedded forms do not match. Address properties are not classified.
11. Fixed-width hexadecimal tokens use the ASCII alphabet at widths 32, 40, 64, and 128. Prefixes, separators, whitespace, and Unicode digits do not match. The widths are not hash-algorithm names.
12. Counts may overlap. A compact UUID increments `uuid_count` and `hex_32_count`. There is no mutual-exclusion validation and no precedence.
13. Each ratio divides by `n_non_missing` and is `None` when that count is 0. A zero numerator with a positive denominator is `0.0`.
14. An all-missing physical string column yields zero counts and undefined ratios. A constant pattern column keeps Constant precedence and still records the pattern count.
15. The facts do not select Identifier, Text, Categorical, Datetime, or Numeric. Date-like strings are not parsed. Email, URL, path, and MAC text are not recognized.
16. Collection is exact, full-column, and unsampled. No provenance object was added.
17. The precedence chain does not collect pattern evidence. String-structure collection does not collect it either.
18. The input Series is not mutated.
19. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
20. Focused tests pass.
21. TSK-009 tests pass.
22. TSK-008 tests pass.
23. TSK-007 tests pass.
24. TSK-006 tests pass.
25. Semantic tests for TSK-001 through TSK-010 pass.
26. The legacy profiler stays at 19 passed and the known PDF failure.
27. The full suite adds only the new tests, with the same known PDF failure.
28. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) through [OPEN-049](DECISIONS.md#open-049) stay open. Pattern ratios and syntax counts do not close [OPEN-014](DECISIONS.md#open-questions) or [OPEN-044](DECISIONS.md#open-questions). The absence of word counts does not close [OPEN-019](DECISIONS.md#open-questions).
29. This section does not approve or implement a later slice.
30. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 30 passed for TSK-010.

## After TSK-010

TSK-010 adds exact full-value pattern observations for populations that already have string-structure evidence. It does not add a semantic reading. [DEC-081](DECISIONS.md#dec-081) records the contract, including composition with string-structure evidence, the initial syntax catalog, ASCII hexadecimal tokens, allowed overlap, the non-missing denominator, and on-demand collection. The next concrete implementation slice remains subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). This section does not create a later task.
