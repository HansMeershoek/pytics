# Implementation plan

Status: **TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, TSK-024, TSK-025, TSK-026, TSK-027, TSK-028, TSK-029, TSK-030, TSK-031, TSK-032, TSK-033, TSK-034, TSK-035, and TSK-036 are complete. No later slice is approved.** The strong-physical-type phase is complete. The Semantic Foundation Review has been consolidated into project memory. TSK-006 strengthens the universal column-evidence family and does not add a semantic reading. TSK-007 adds frequency observations and does not add a semantic reading. TSK-008 adds numeric-structure observations and does not add a semantic reading. TSK-009 adds string-structure observations and does not add a semantic reading. TSK-010 adds pattern observations and does not add a semantic reading. TSK-011 adds an Identifier candidate assessment and does not select a semantic reading. TSK-012 adds Numeric, Categorical, and Text candidate assessments and does not select a semantic reading. TSK-013 adds string-content observations and does not select a semantic reading. TSK-014 resolves structural readings and candidate assessments and does not assign candidate confidence. TSK-015 records the inferred state after that resolution and does not invent that confidence. TSK-016 connects those components for one Series and does not invent that confidence. TSK-017 retains that column analysis for one DataFrame and does not invent that confidence. TSK-018 summarizes that analysis as a dataset overview and does not invent that confidence. TSK-019 summarizes each column of that analysis as a variable and does not invent that confidence. TSK-020 adds finite-population descriptive statistics after a Numeric selection and does not change that confidence. TSK-021 adds true and false counts after a Boolean selection and does not change inference or that confidence. TSK-022 records exact missingness structure and does not infer a missingness mechanism. TSK-023 records exact duplicate rows and does not treat them as errors. TSK-024 describes selected Numeric × Numeric pairs with Spearman and Pearson and does not implement other relationship families. TSK-025 makes Numeric descriptive statistics robust when a derived value is not a finite float64, and it splits the relationship implementation into a small package. It does not add a relationship family and it does not select the next slice. TSK-026 adds selected Numeric × selected Categorical relationships: observed group summaries, eta squared, and classical one-way ANOVA. It does not add post-hoc tests and it does not select the slice after that. TSK-027 moves relationship metadata to the family or component that owns it. It does not add a family, change those calculations, or select the slice after that. TSK-028 adds selected Boolean × selected Boolean relationships: a 2×2 table, probability difference, probability ratio, phi, and a two-sided Fisher exact p-value. It does not add a confidence interval or select the slice after that. TSK-029 adds selected Numeric × selected Boolean relationships: False and True group summaries, the True − False mean difference, Hedges' g, a 95% Welch–Satterthwaite interval, and Welch's t-test. It does not add a rank test or target analysis, and it does not select the slice after that.

Pytics 2.0 implementation has started only for Slice 001, Slice 002, Slice 003, Slice 004, Slice 005, Slice 006, Slice 007, Slice 008, Slice 009, Slice 010, Slice 011, Slice 012, Slice 013, Slice 014, Slice 015, Slice 016, Slice 017, Slice 018, Slice 019, Slice 020, Slice 021, Slice 022, Slice 023, Slice 024, Slice 025, Slice 026, Slice 027, Slice 028, Slice 029, Slice 030, Slice 031, Slice 032, Slice 033, Slice 034, Slice 035, and Slice 036. This file does not sequence the rest of the analytical contract, and it does not assign priority. Sequencing beyond those slices is [OPEN-037](DECISIONS.md#open-questions). Selecting a semantic reading from a candidate assessment does not start from this file. The next implementation slice is not selected.

## Authorization

An accepted requirement is not permission to code. A slice starts only when [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md) steps 1–3 are written down and the slice is approved, and only for the requirement IDs named in that scope.

Outside an approved slice:

- do not add a package or module for 2.0;
- do not modify 1.1.5 production code;
- do not change `pyproject.toml` dependencies;
- do not implement the engine, result classes, or method registry;
- do not install or pin the candidate stack in [DEPENDENCIES.md](DEPENDENCIES.md).

Accepting architectural direction is not approval of a slice. The end state is replacement inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). In-place migration is [DEC-063](DECISIONS.md#dec-063). TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, TSK-024, TSK-025, TSK-026, TSK-027, TSK-028, TSK-029, TSK-030, TSK-031, TSK-032, TSK-033, TSK-034, and TSK-035 are the only slices approved under that rule.

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
| [OPEN-004](DECISIONS.md#open-questions) | Legacy `profile` / `compare` signatures are not the 2.0 result. The public result contract v0.1 is [DEC-113](DECISIONS.md#dec-113). The illustrative `ProfileReport` / `ComparisonReport` names were not adopted. |
| [DEC-105](DECISIONS.md#dec-105), formerly [OPEN-013](DECISIONS.md#open-013) | One untuned diagnostic estimator per task: logistic regression and ridge regression. No second estimator, search, or comparison. |
| [OPEN-041](DECISIONS.md#open-questions) | No silent choice of a Plotly static-export mechanism for PDF. |
| [DEC-066](DECISIONS.md#dec-066) | Candidate Resolution v0.1 uses no numeric total-score. [DEC-042](DECISIONS.md#dec-042) still permits a future statistically justified numeric confidence. |
| [DEC-074](DECISIONS.md#dec-074), [OPEN-014](DECISIONS.md#open-questions) | No heuristic `{0, 1}` or string-token Binary inference until a binary-not-Boolean reading can be represented. |
| [DEC-064](DECISIONS.md#dec-064), [OPEN-045](DECISIONS.md#open-questions) | The semantic pipeline is not a module layout. |

## Traceability

[PROGRESS.md](PROGRESS.md) is the register that must stay able to show:

```text
requirement → implementation task → source files → tests → verification → completion
```

No requirement row in that register is completed. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, TSK-024, TSK-025, TSK-026, TSK-027, TSK-028, and TSK-029 are completed tasks. They do not complete REQ-S-01, REQ-S-02, REQ-S-03, REQ-S-04, REQ-S-05, REQ-S-07, REQ-D-01, REQ-D-02, REQ-D-03, REQ-E-03, REQ-E-04, REQ-F-01, REQ-F-02, REQ-G-01, REQ-G-02, REQ-H-01, REQ-H-02, REQ-H-04, REQ-H-05, REQ-A-01, REQ-A-02, REQ-A-03, REQ-A-04, REQ-A-05, REQ-A-06, REQ-I-01, REQ-IA-05, REQ-IA-08, REQ-IA-09, REQ-B-01, or REQ-B-02.

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

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 45 passed for TSK-005. Criterion 38 records the project memory at that verification. The status recorded for that verification is [After TSK-005](#after-tsk-005). The current status is [After TSK-013](#after-tsk-013).

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

TSK-010 adds exact full-value pattern observations for populations that already have string-structure evidence. It does not add a semantic reading. [DEC-081](DECISIONS.md#dec-081) records the contract, including composition with string-structure evidence, the initial syntax catalog, ASCII hexadecimal tokens, allowed overlap, the non-missing denominator, and on-demand collection. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-011 was approved later and is recorded below. This section does not create a later task.

## TSK-011

Slice 011, candidate assessment foundation and the Identifier candidate. Approved 2026-10-03 after TSK-010. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-04 and REQ-S-05, for evidence-driven assessment kept distinct from observations and from a selected reading. REQ-S-01 is respected because no reading is selected. REQ-G-01 and REQ-G-02 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- A frozen `CandidateAssessment` for one `SemanticType`, with `CandidateDisposition` of `SUPPORTED`, `NOT_SUPPORTED`, or `CONTRADICTED`.
- Supporting and contradicting evidence are tuples of `SemanticEvidence`. No second evidence class. No score, confidence, winner, rank, or probability.
- `SUPPORTED` requires supporting evidence. `CONTRADICTED` requires contradicting evidence. Both sequences may be non-empty. `NOT_SUPPORTED` may be empty.
- `assess_identifier_candidate` consumes already collected evidence. It does not recollect observations, classify a dtype, or read a Series or column name.
- Supplied composed evidence must be the same objects, not merely equal counts. A physical family that cannot carry the supplied family evidence is rejected.
- Empty and Constant, including a constant UUID, are `NOT_SUPPORTED`. They are not contradictions.
- A full non-missing population of UUID syntax, or of one ASCII hexadecimal width 32, 40, 64, or 128, is `SUPPORTED`. A compact UUID may record both facts. That is not a score. The hexadecimal statement is not a hash-algorithm name.
- A partial ratio, a mixture of patterns, IPv4, IPv6, uniqueness, missingness, singleton ratio, and a column name do not support Identifier. Duplicates do not contradict it.
- Numeric sequences stay `NOT_SUPPORTED`. The assessor does not reconstruct a regular step.
- Boolean, Datetime, timezone-aware Datetime, Timedelta, and categorical storage stay `NOT_SUPPORTED`.
- No Identifier contradiction is emitted. No resolution function is added. The precedence chain does not call the assessor.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The candidate contract is [DEC-082](DECISIONS.md#dec-082). The full-population rule narrows [OPEN-044](DECISIONS.md#open-questions) only as an initial Identifier candidate rule. It does not close that question.

### Exclusions

Do not resolve candidates. Do not assign High, Medium, or Low. Do not add material alternatives, a score, or an evidence-strength enum. Do not add Numeric, Categorical, Text, or Boolean candidate assessors. Do not infer Identifier from uniqueness, missingness, cardinality, IP syntax, partial pattern ratios, column names, or numeric monotonicity. Do not reconstruct regular-step evidence. Do not call the assessor from `interpret_series_precedence`. Do not change `SemanticInterpretation`.

Do not add a candidate registry, a rule engine, or a resolver. Do not add a provenance object. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049).

Do not change `pytics.profile` or `pytics.compare`. Do not export the assessment from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `CandidateAssessment` is a frozen dataclass. It is not a `SemanticInterpretation`.
2. `semantic_type` is a `SemanticType`. `disposition` is `CandidateDisposition` with `SUPPORTED`, `NOT_SUPPORTED`, and `CONTRADICTED`.
3. Supporting and contradicting evidence are tuples of `SemanticEvidence`. No second evidence class was added.
4. `SUPPORTED` requires supporting evidence. `CONTRADICTED` requires contradicting evidence. `NOT_SUPPORTED` may be empty. Both sequences may be non-empty. The value has no Identifier-specific field.
5. No score, confidence, winner, rank, probability, or priority field was added.
6. `assess_identifier_candidate` consumes a consistent evidence bundle. It does not take a Series and does not recollect observations.
7. Equal counts from another column are rejected. Pattern evidence must be the supplied string-structure object. An inapplicable physical family is rejected.
8. Empty, all-missing string, zero-length string, constant ordinary string, and constant UUID are `NOT_SUPPORTED`. Contradicting evidence stays empty.
9. A full UUID population is `SUPPORTED`, including compact form, uppercase, duplicates, unique values, object storage, and missing values beside non-missing UUIDs. The statement describes the UUID syntax. Uniqueness is not the reason.
10. A full population at hexadecimal width 32, 40, 64, or 128 is `SUPPORTED`. Duplicate hexadecimal tokens stay supported. The statement names the width and ASCII hexadecimal tokens, not a hash algorithm. Compact UUID overlap records both facts and no score.
11. A partial UUID ratio, a partial hexadecimal ratio, full IPv4, full IPv6, a mixture of patterns, date-like strings, email-like strings, URL-like strings, ordinary labels, a column name, uniqueness, zero missingness, and a singleton ratio do not support Identifier.
12. Physical categorical, Boolean, Datetime, timezone-aware Datetime, and Timedelta are `NOT_SUPPORTED`.
13. Unique, complete, integer-like, monotonic numeric sequences are `NOT_SUPPORTED`. The assessor does not read a step or the monotonicity flags.
14. No Identifier assessment emits contradicting evidence.
15. `interpret_series_precedence` does not call the assessor. A UUID column still produces no Identifier interpretation.
16. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
17. Focused candidate-foundation tests pass. Focused Identifier tests pass.
18. TSK-010, TSK-009, TSK-008, TSK-007, and TSK-006 tests pass.
19. Semantic tests for TSK-001 through TSK-011 pass.
20. The legacy profiler stays at 19 passed and the known PDF failure.
21. The full suite adds only the new tests, with the same known PDF failure.
22. [OPEN-044](DECISIONS.md#open-questions) stays open beyond the initial full-population candidate rule. Partial-pattern thresholds, numeric sequence evidence, name and dataset context, resolution, and final confidence stay open. [OPEN-045](DECISIONS.md#open-questions) and [OPEN-048](DECISIONS.md#open-048) stay open.
23. This section does not approve or implement a later slice.
24. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 24 passed for TSK-011.

## After TSK-011

TSK-011 adds a candidate assessment and uses Identifier as the first concrete candidate. It does not select a semantic reading and does not enter the precedence chain. [DEC-082](DECISIONS.md#dec-082) records the contract, including support versus contradiction, the absence of a score and of final confidence, the initial full-population UUID and same-width hexadecimal rules, and the facts that do not support Identifier. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-012 was approved later and is recorded below. This section does not create a later task.

## TSK-012

Slice 012, Numeric, Categorical, and Text candidate assessments. Approved 2026-10-03 after TSK-011. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-04 and REQ-S-05, for evidence-driven assessment kept distinct from observations and from a selected reading. REQ-S-01 is respected because no reading is selected. REQ-C-01, REQ-F-01, REQ-D-01, and REQ-D-02 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Reuse `CandidateAssessment` and `CandidateDisposition`. Do not add a specialized assessment type.
- `assess_numeric_candidate`, `assess_categorical_candidate`, and `assess_text_candidate` consume an evidence bundle already collected. They use the Identifier bundle identity checks. They do not take a Series, read a column name, recollect observations, or classify a dtype again.
- Empty and Constant are `NOT_SUPPORTED` for each candidate. They are not contradictions. No candidate in this slice emits `CONTRADICTED`.
- Non-empty, non-constant physical integer or floating storage is `SUPPORTED` Numeric. The statement names that family and supports a reading. Nullable and sparse storage already classified in those families are included. Complex storage is not. Numeric-looking strings are not parsed.
- Numeric-structure facts may be supplied. They do not add a finite, sign, integer-like, or monotonicity cutoff, and they are not required.
- `{0, 1}` and `{0.0, 1.0}` numeric storage may support Numeric. They are not Boolean or Binary.
- Non-empty, non-constant physical categorical storage is `SUPPORTED` Categorical, including ordered storage and unused levels. Ordered metadata stays on the physical dtype. No Ordinal type is added.
- Repetition, two labels, and low cardinality do not support Categorical. No cardinality threshold is introduced.
- Text stays `NOT_SUPPORTED` from current observations. No length or whitespace threshold is introduced.
- Assessors are independent. A column may support one candidate, more than one, or none. Identifier rules are unchanged.
- The precedence chain does not call any candidate assessor. No resolver, score, or final confidence is added.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The candidate contract is [DEC-083](DECISIONS.md#dec-083). It reuses [DEC-082](DECISIONS.md#dec-082). It does not close [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not resolve candidates. Do not assign High, Medium, or Low. Do not add material alternatives, a score, or an evidence-strength enum. Do not change Identifier rules. Do not reconstruct regular-step evidence. Do not add word counts, token counts, or NLP. Do not infer Boolean or Binary from `{0, 1}` or from string labels. Do not infer Categorical from repetition or from two values. Do not infer Text from string dtype, length, or whitespace. Do not parse numeric-looking strings. Do not call the assessors from `interpret_series_precedence`. Do not change `SemanticInterpretation`.

Do not add a candidate registry, a rule engine, or a resolver. Do not add a user override. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049).

Do not change `pytics.profile` or `pytics.compare`. Do not export the assessors from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `CandidateAssessment` and `CandidateDisposition` are unchanged. No Numeric, Categorical, or Text assessment dataclass was added.
2. The three assessors consume a consistent evidence bundle. They do not take a Series and do not recollect observations.
3. Equal counts from another column are rejected. An inapplicable physical family for supplied family evidence is rejected.
4. Empty and Constant are `NOT_SUPPORTED` for Numeric, Categorical, and Text, including constant numeric storage, constant categorical storage, a constant paragraph, and a constant UUID. Contradicting evidence stays empty.
5. Non-empty, non-constant integer and floating storage is `SUPPORTED` Numeric, including signed, unsigned, nullable, and sparse storage the current classifier already accepts. The statement names the physical family and supports a Numeric reading.
6. Infinities, negatives, zeros, integer-like floats, non-integer floats, and both directions of an integer sequence stay `SUPPORTED` Numeric. Numeric-structure facts are not required and do not impose a cutoff.
7. Numeric-looking strings are not parsed. Complex, Boolean, Datetime, timezone-aware Datetime, Timedelta, and categorical storage are `NOT_SUPPORTED` Numeric.
8. `{0, 1}` and `{0.0, 1.0}` numeric storage may support Numeric and are not inferred as Boolean or Binary.
9. Non-empty, non-constant physical categorical storage is `SUPPORTED` Categorical, including ordered storage and an unused level. The statement does not claim Ordinal. `categorical_ordered` stays on the physical dtype.
10. Empty and Constant categorical storage are `NOT_SUPPORTED`. Ordinary strings, two labels, Boolean-like labels, label text that looks ordered, repeated integers, UUID strings, and IP strings are `NOT_SUPPORTED` Categorical. No cardinality threshold was added.
11. Text stays `NOT_SUPPORTED` for ordinary words, repeated labels, unique labels, whitespace, long strings, prose-like strings, punctuation, mixed alphanumeric text, UUID, hexadecimal, IPv4, IPv6, numeric-looking strings, email-like strings, URL-like strings, empty and all-missing string columns, a constant paragraph, categorical labels, numeric storage, Boolean, and Datetime. No length or whitespace threshold was added.
12. Assessors operate independently. An ordinary integer column supports Numeric only. Physical categorical storage supports Categorical. UUID strings support Identifier only. Ordinary strings support none. A constant UUID supports none. No resolver writes those results.
13. No score, confidence, rank, or `CONTRADICTED` result was added. `interpret_series_precedence` does not call any candidate assessor. Current Empty, Constant, Boolean, Datetime, timezone-aware Datetime, Timedelta, numeric, string, and UUID precedence results stay as they were.
14. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. Identifier tests stay green.
15. Focused TSK-012 tests pass. TSK-011 foundation and Identifier tests pass. TSK-010, TSK-009, TSK-008, TSK-007, and TSK-006 tests pass.
16. Semantic tests for TSK-001 through TSK-012 pass. The legacy profiler stays at 19 passed and the known PDF failure. The full suite adds only the new tests, with the same known PDF failure.
17. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open. Resolution, final confidence, numeric sequence Identifier evidence, and user overrides stay open.
18. This section does not approve or implement a later slice.
19. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 19 passed for TSK-012.

## After TSK-012

TSK-012 adds Numeric, Categorical, and Text candidate assessments on the candidate model from TSK-011. It does not select a semantic reading and does not enter the precedence chain. [DEC-083](DECISIONS.md#dec-083) records the contract, including physical integer and floating storage as Numeric support, physical categorical storage as Categorical support, the absence of an approved Text rule in the current observations, and the absence of a cardinality, length, or whitespace threshold. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-013 was approved later and is recorded below. This section does not create a later task.

## TSK-013

Slice 013, string vocabulary and text-structure evidence. Approved 2026-10-03 after TSK-012. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03 and REQ-S-05, for observations kept distinct from interpretation. REQ-S-01 and REQ-S-04 are respected because no reading is selected and no column name is used. REQ-F-01, REQ-F-02, and REQ-C-01 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add one typed evidence family, `StringContentEvidence`, composed with `StringStructureEvidence`. Do not copy basic counts, length bounds, character-class counts, or whole-value frequency counts.
- A token is a maximal contiguous run of characters for which `str.isalnum` is true. Case is preserved. Accents are not normalized. Empty strings and whitespace-only strings have no token and remain observed strings. Missing values stay missing.
- Store the zero/one/multiple-token partition, total token count, total character count, distinct-token count, singleton-token count, and most-frequent-token count. Derive ratios and means. Do not store means. Undefined ratios are `None`.
- `token_singleton_ratio` divides by distinct tokens. `most_frequent_token_ratio` divides by token occurrences. The string ratios and means divide by `n_non_missing`.
- Do not retain raw strings, tokens, or a vocabulary. A temporary occurrence map during collection is not part of the returned value.
- Collection is exact, full-column, and unsampled. The collector reuses supplied string-structure evidence and does not recollect basic, frequency, string-structure, or pattern evidence.
- Do not change Numeric, Categorical, Text, or Identifier candidate rules. One-token strings and multi-token strings do not by themselves support Categorical or Text. Token repetition does not support Categorical.
- The precedence chain does not collect this family. No resolver, score, or final confidence is added.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The evidence contract is [DEC-084](DECISIONS.md#dec-084). It does not close [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not resolve candidates. Do not assign High, Medium, or Low. Do not add a Text or ordinary-string Categorical rule. Do not add a cardinality, uniqueness, token-count, length, or whitespace threshold. Do not lowercase, case-fold, strip, or Unicode-normalize source values. Do not add language detection, stopwords, embeddings, or an NLP library. Do not expand the pattern catalog. Do not infer email, URL, or path. Do not use a column name. Do not add regular-step numeric Identifier evidence. Do not infer Binary or Ordinal. Do not call the collector from `interpret_series_precedence`. Do not change `SemanticInterpretation` or `core_candidates.py`.

Do not add a tokenizer package, a vocabulary store, or a resolver. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-019](DECISIONS.md#open-questions) may record only the evidence-collection portion that this slice actually solves.

Do not change `pytics.profile` or `pytics.compare`. Do not export the collector from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `StringContentEvidence` is a frozen dataclass composed with `StringStructureEvidence`. It is not a subclass. Basic counts, length bounds, and whole-value frequency counts are not copied.
2. Eligibility follows string-structure evidence. A physical string dtype is eligible, including an all-missing string column. An object column is eligible only when every non-missing value is a Python `str`. Categorical, numeric, Boolean, Datetime, Timedelta, and `bytes` values are not coerced into tokens.
3. The collector reuses the supplied string-structure evidence. It does not recollect basic, frequency, string-structure, or pattern evidence, and it does not classify the physical dtype again. The Series is not mutated.
4. A token is a maximal `str.isalnum` run. Case stays distinct. Accents are not normalized. `""` and whitespace-only strings are observed strings with zero tokens. Missing values are not treated as `""`, `"nan"`, or `"None"`.
5. Stored fields are the token partition, `total_token_count`, `total_character_count`, `n_distinct_tokens`, `singleton_token_count`, and `most_frequent_token_count`. Means and ratios are derived. An undefined ratio or mean is `None`. `token_singleton_ratio` uses distinct tokens as its denominator. `most_frequent_token_ratio` uses token occurrences.
6. The returned evidence retains no raw string and no vocabulary. Whole-value frequency and token vocabulary remain different observations.
7. Collection is exact, full-column, and unsampled. `interpret_series_precedence` does not collect it. String-structure collection does not collect it. Candidate assessors do not collect it.
8. `core_candidates.py` is unchanged. `["Amsterdam", "Berlin", "Paris"]` stays `NOT_SUPPORTED` for Categorical and Text. Multi-token sentences stay `NOT_SUPPORTED` for Text and Categorical. UUID Identifier support, physical categorical support, Numeric support, and `{0, 1}` Numeric behavior stay as they were.
9. No cardinality, uniqueness, token-count, length, or whitespace threshold was added. No resolution, final confidence, Binary inference, Ordinal inference, or numeric-sequence Identifier evidence was added.
10. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
11. Focused TSK-013 tests pass. TSK-012, TSK-011 foundation, TSK-011 Identifier, TSK-010, TSK-009, TSK-008, TSK-007, and TSK-006 tests pass.
12. Semantic tests for TSK-001 through TSK-013 pass. The legacy profiler stays at 19 passed and the known PDF failure. The full suite adds only the new tests, with the same known PDF failure.
13. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open. [OPEN-019](DECISIONS.md#open-questions) records the token-evidence collection and leaves diagnostics and inference rules open. Resolution, final confidence, numeric sequence Identifier evidence, and user overrides stay open.
14. This section does not approve or implement a later slice.
15. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 15 passed for TSK-013.

## After TSK-013

TSK-013 adds string-content observations composed with string-structure evidence. It does not select a semantic reading and does not enter the precedence chain. [DEC-084](DECISIONS.md#dec-084) records the contract, including the alphanumeric token definition, case-sensitive aggregate vocabulary counts, the separation from whole-value frequency, and the decision that those facts do not support Text or ordinary-string Categorical. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-014 was approved later and is recorded below. This section does not create a later task.

## TSK-014

Slice 014, semantic resolution foundation. Approved 2026-10-03 after TSK-013. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-04 and REQ-S-05, for resolution kept distinct from observation and from candidate assessment. REQ-S-01 is not completed: a structural reading is preserved, and exactly one supported candidate selects a semantic type without a confidence-bearing interpretation. REQ-S-02 is not completed because a candidate-derived selection does not receive High, Medium, or Low. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `ResolutionStatus` with `RESOLVED`, `INSUFFICIENT_EVIDENCE`, and `AMBIGUOUS`. Do not add those words to `SemanticType`.
- Add one frozen `SemanticResolution`: status, diagnostic reason, candidate assessments, selected semantic type when resolved, and the structural interpretation when that reading won.
- `resolve_semantics` consumes an optional structural interpretation and candidate assessments already produced. It does not collect observations, call assessors, or read a Series.
- Empty, Constant, Boolean, Datetime, and Timedelta resolve to that interpretation. Candidate assessments do not replace it. Any other semantic type supplied as a structural reading is rejected.
- Exactly one `SUPPORTED` candidate resolves to that semantic type and does not construct a `SemanticInterpretation` or a confidence.
- No `SUPPORTED` candidate, including an empty candidate collection, is `INSUFFICIENT_EVIDENCE`. There is no fallback type.
- More than one `SUPPORTED` candidate is `AMBIGUOUS`. No selected type. No Identifier-over-Numeric rule.
- A `CONTRADICTED` candidate is not selected and does not veto a different supported candidate.
- Two assessments for the same semantic type are rejected. Input order does not change the result. An ambiguous reason lists types in semantic-type name order.
- A structural interpretation keeps the confidence it already carries. Candidate-derived confidence is not invented. Material alternatives are not constructed.
- `interpret_series_precedence` does not call the resolver. No override, eligibility rule, public result, configuration, or threshold is added.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The resolution contract is [DEC-085](DECISIONS.md#dec-085). It narrows [OPEN-047](DECISIONS.md#open-047) to the remaining inferred-interpretation representation. It does not close [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not add `SemanticType.UNKNOWN`, `SemanticType.AMBIGUOUS`, or `SemanticType.UNRESOLVED`. Do not assign High, Medium, or Low from candidate counts. Do not build a `SemanticInterpretation` for a candidate-derived selection. Do not invent a priority between supported candidates. Do not merge duplicate candidate types. Do not treat a contradiction as a veto or as a confidence measure. Do not construct material alternatives. Do not call collectors or assessors from the resolver. Do not call the resolver from `interpret_series_precedence`. Do not add a user override, effective interpretation, downstream eligibility, or a public `profile()` result.

Do not add a rule registry, a strategy framework, or a numeric total. Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-047](DECISIONS.md#open-047) records the resolution statuses and leaves their inferred-interpretation representation open.

Do not change `pytics.profile` or `pytics.compare`. Do not export the resolver from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `SemanticResolution` is a frozen dataclass. `ResolutionStatus` is `RESOLVED`, `INSUFFICIENT_EVIDENCE`, or `AMBIGUOUS`. Those words are not `SemanticType` members.
2. `RESOLVED` has a selected semantic type. `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` do not. Impossible combinations are rejected. An invalid status is rejected.
3. Candidate assessments are stored as a tuple in semantic-type name order. Duplicate semantic types are rejected, including two identical assessments.
4. Empty, Constant, Boolean, Datetime, timezone-aware Datetime, and Timedelta structural readings resolve to that interpretation. A constant UUID and a constant integer stay Constant when Identifier or Numeric is supported. Candidates do not replace a structural reading. A Numeric, Identifier, Categorical, or Text object supplied as a structural reading is rejected.
5. Exactly one supported candidate resolves to that type for Numeric, Identifier, Categorical, and a directly constructed Text assessment. Current assessors produce that Numeric, Identifier, and Categorical result. No `SemanticInterpretation` and no confidence are created for that selection.
6. All unsupported candidates, a mixture of unsupported and contradicted candidates, an empty candidate collection, city-name strings, and prose-like strings are `INSUFFICIENT_EVIDENCE`. There is no fallback type.
7. Numeric with Identifier, Categorical with Text, and Identifier with Text stay `AMBIGUOUS` when both are supported. No semantic type is selected. Input order does not change the result or the reason.
8. A supported candidate remains resolved when a different candidate is contradicted. A contradicted candidate beside only unsupported candidates is insufficient evidence. The number of supporting statements does not select a candidate.
9. The resolver does not collect observations or call assessors. Its module does not import pandas or the collectors. `interpret_series_precedence` does not call it, and existing precedence results stay as they were.
10. A structural interpretation keeps its existing confidence. Candidate resolution does not assign High, Medium, or Low. Material alternatives are not constructed.
11. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
12. Focused TSK-014 tests pass. TSK-013, TSK-012, TSK-011 foundation, TSK-011 Identifier, TSK-010, TSK-009, TSK-008, TSK-007, and TSK-006 tests pass.
13. Semantic tests for TSK-001 through TSK-014 pass. The legacy profiler stays at 19 passed and the known PDF failure. The full suite adds only the new tests, with the same known PDF failure.
14. [OPEN-047](DECISIONS.md#open-047) records resolution abstention and ambiguity and leaves the inferred-interpretation representation open. [OPEN-044](DECISIONS.md#open-questions) stays open for thresholds, final candidate-derived confidence, and any future rule between supported candidates. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open.
15. This section does not approve or implement a later slice.
16. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 16 passed for TSK-014.

## After TSK-014

TSK-014 resolves structural readings and already produced candidate assessments. It does not assign confidence to a candidate-derived selection, does not build that selection's `SemanticInterpretation`, and does not enter the precedence chain. [DEC-085](DECISIONS.md#dec-085) records the contract, including structural precedence, exactly-one-supported resolution, abstention when nothing is supported, ambiguity when several candidates are supported, and the rejection of duplicate candidate types. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-015 was approved later and is recorded below. This section does not create a later task.

## TSK-015

Slice 015, inferred interpretation foundation. Approved 2026-10-03 after TSK-014. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-04 and REQ-S-05, for the inferred state kept distinct from resolution, from candidate assessment, and from observation. REQ-S-01 is not completed: a structural reading is preserved, and a candidate-derived selection remains a selected type without a confidence-bearing interpretation. REQ-S-02 is not completed because that selection does not receive High, Medium, or Low. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add one frozen `InferredSemanticResult`. Store the observed physical dtype and the `SemanticResolution` already produced. Do not store a second status, a second selected type, the candidates again, or a second structural interpretation.
- Derive `interpretation` from the resolution's structural interpretation. Derive `selected_type` from the resolution. Reuse `ResolutionStatus` through the contained resolution.
- `build_inferred_semantic_result` consumes those two facts. It does not read a Series, collect observations, assess candidates, or call `resolve_semantics`.
- The physical dtype is supplied. It is not derived from the selected semantic type.
- A structural resolution keeps that interpretation object. Its confidence, source, and physical dtype stay as they are. The supplied physical dtype must match. A mismatch is rejected.
- A candidate-derived `RESOLVED` result keeps the selected type and does not build a `SemanticInterpretation`. No High, Medium, or Low confidence is invented from candidate counts, evidence counts, or the absence of contradiction.
- `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` are valid inferred results. Neither has an interpretation or a selected type. Neither is an error or a bare `None`.
- Ambiguity does not become a selected reading, a low confidence, or material alternatives.
- `interpret_series_precedence` does not call the constructor. No override, effective interpretation, eligibility rule, public result, configuration, or threshold is added.
- Focused unit tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The inferred-result contract is [DEC-086](DECISIONS.md#dec-086). It narrows [OPEN-047](DECISIONS.md#open-047) to candidate-derived confidence, material alternatives on a future selected reading, and the public result. It does not close [OPEN-044](DECISIONS.md#open-questions).

### Exclusions

Do not widen `SemanticInterpretation` so that confidence is optional. Do not add `SemanticType.UNKNOWN`. Do not add a second status enum. Do not assign High, Medium, or Low from candidate counts or evidence quantity. Do not add an evidence-strength enum. Do not map a semantic type to a physical dtype family. Do not construct material alternatives. Do not turn ambiguity into a low-confidence selected reading. Do not call collectors, assessors, or the resolver from the constructor. Do not call the constructor from `interpret_series_precedence`. Do not add a user override, effective interpretation, downstream eligibility, or a public `profile()` result.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-047](DECISIONS.md#open-047) records the inferred representation of abstention and ambiguity and leaves confidence, material alternatives, and the public result open.

Do not change `pytics.profile` or `pytics.compare`. Do not export the inferred result from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `InferredSemanticResult` is a frozen dataclass. Its stored fields are the physical dtype and the resolution. Status, selected type, candidates, reason, and the structural interpretation are not stored again.
2. `interpretation` and `selected_type` are derived from the resolution. An unresolved result cannot carry an interpretation.
3. Empty, Constant, Boolean, Datetime, timezone-aware Datetime, and Timedelta structural readings are preserved by identity. Confidence, source, and the interpretation's physical dtype are unchanged. The supplied physical dtype matches.
4. A supplied physical dtype that differs from the structural interpretation is rejected. Neither value is replaced. An ordered-flag mismatch on categorical storage is rejected.
5. A candidate-derived resolved result keeps the selected type and has no `SemanticInterpretation`. Integer and floating Numeric storage, string and object Identifier storage, and categorical storage, including the ordered flag, stay as observed. No confidence is created.
6. City-name strings and prose-like strings are `INSUFFICIENT_EVIDENCE`. The inferred result retains the physical dtype, has no interpretation and no selected type, and is not `None`.
7. An ambiguous resolution of supported Numeric and Identifier candidates is a valid inferred result. No interpretation, no selected type, no confidence, and no material alternative. Both supported candidates remain on the resolution.
8. The constructor preserves a supplied physical dtype for Numeric, Identifier, Categorical, and Text selections. It does not contain a semantic-type-to-physical-family mapping.
9. One supporting statement, two supporting statements, no contradiction, and a contradicted neighbor do not create an interpretation or a confidence.
10. Construction does not collect observations, assess candidates, or call the resolver. `interpret_series_precedence` does not call the constructor, and existing precedence results stay as they were.
11. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. `SemanticInterpretation`, `SemanticResolution`, `Confidence`, and `SemanticType` are unchanged.
12. Focused TSK-015 tests pass. TSK-014, TSK-013, TSK-012, TSK-011 foundation, TSK-011 Identifier, TSK-010, TSK-009, TSK-008, TSK-007, and TSK-006 tests pass.
13. Semantic tests for TSK-001 through TSK-015 pass. The legacy profiler stays at 19 passed and the known PDF failure. The full suite adds only the new tests, with the same known PDF failure.
14. [OPEN-047](DECISIONS.md#open-047) records the inferred representation of abstention and ambiguity and leaves candidate-derived confidence, material alternatives, and the public result open. [OPEN-044](DECISIONS.md#open-questions) stays open for that confidence. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open.
15. This section does not approve or implement a later slice.
16. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 16 passed for TSK-015.

## After TSK-015

TSK-015 records the inferred state for a physical dtype and a resolution already produced. It preserves a structural interpretation and does not assign confidence to a candidate-derived selection. It does not enter the precedence chain. [DEC-086](DECISIONS.md#dec-086) records the contract, including physical-dtype provenance, deferred candidate confidence, and abstention and ambiguity as ordinary inferred states. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-016 was approved later and is recorded below. This section does not create a later task.

## TSK-016

Slice 016, column-level semantic pipeline integration. Approved 2026-10-03 after TSK-015. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-S-03, REQ-S-04, and REQ-S-05, for one Series path that reuses physical dtype, basic evidence, and the existing interpretation objects without mutation. REQ-S-01 is not completed: the pipeline reaches the readings that already exist and does not add one. REQ-S-02 is not completed because a candidate-derived selection still does not receive High, Medium, or Low. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add one internal function, `infer_series_semantics`, in `src/pytics/semantics/pipeline.py`. It accepts a pandas Series and returns `InferredSemanticResult`. Do not add a second result type.
- Classify physical dtype once. Collect `BasicColumnEvidence` once. Reuse those objects.
- Structural precedence is the existing `interpret_precedence_from_evidence`. Do not copy Empty, Constant, Boolean, Datetime, or Timedelta rules. Leave `interpret_series_precedence` as the Series wrapper.
- A structural reading returns through `resolve_semantics` and `build_inferred_semantic_result` without frequency, numeric-structure, string-structure, pattern, or string-content collection, and without candidate assessment.
- Otherwise collect only applicable evidence. Integer and floating storage collect numeric-structure evidence. Eligible string and object populations collect string structure once, then pattern and string content from that same object. An ineligible object population is not an error and is not coerced. Categorical storage and other non-structural families collect no further evidence.
- Do not collect frequency evidence. No current candidate rule reads it. Do not change the retention limit. Do not invent zero-filled evidence for an inapplicable family.
- Call the existing Identifier, Numeric, Categorical, and Text assessors with that bundle. They do not receive the Series.
- Delegate resolution and inferred-result construction. Do not assign candidate confidence. Do not read the Series name, index, or any other column.
- No configuration, sampling, override, dataset context, or public `profile()` integration. Do not export the function from top-level `pytics`.
- Focused integration tests, plus the existing suite as a regression check.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The integration contract is [DEC-087](DECISIONS.md#dec-087). It does not close [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), or [OPEN-047](DECISIONS.md#open-047).

### Exclusions

Do not add a semantic type, an evidence family, a candidate rule, a threshold, or a confidence policy. Do not infer Text or Categorical from ordinary strings. Do not infer Boolean or Binary from `{0, 1}`. Do not infer Ordinal from ordered categorical metadata. Do not infer Identifier from a numeric sequence, a partial pattern, an IP address, uniqueness, or a column name. Do not normalize, strip, case-fold, or coerce values. Do not sample. Do not add a registry, a planner, or a plugin system. Do not change `interpret_series_precedence` results. Do not route `pytics.profile` or `pytics.compare` through the pipeline.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-047](DECISIONS.md#open-047) records that the column pipeline produces the inferred result and leaves candidate-derived confidence, material alternatives, and the public result open.

Do not change `pytics.profile` or `pytics.compare`. Do not export the pipeline from top-level `pytics`. Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `infer_series_semantics` accepts a Series and returns `InferredSemanticResult`. A non-Series is rejected. A valid Series with no supported candidate is not an exception.
2. Physical dtype is classified once. That object is the inferred result's physical dtype, including `categorical_ordered` and the timezone-aware datetime family.
3. Basic evidence is collected once. Downstream evidence that composes with it uses that same object.
4. Structural precedence is the existing evidence-level helper. `interpret_series_precedence` remains the Series wrapper, and its results stay the same. No second structural implementation was added.
5. Empty, Constant, Boolean, nullable Boolean, Datetime, timezone-aware Datetime, and Timedelta resolve with their existing interpretation. Candidate-family collectors and assessors do not run. A constant UUID stays Constant.
6. Non-empty, non-constant integer and floating storage, including `{0, 1}`, resolves to Numeric. There is no interpretation, no Boolean reading, and no Binary reading. The observed physical family is kept.
7. A full non-missing population of canonical UUIDs, compact UUIDs, or one supported hexadecimal width resolves to Identifier. There is no interpretation. Partial patterns, IPv4, and a numeric sequence do not. String and object storage stay as observed. Duplicates do not remove Identifier when the column is not Constant.
8. Non-empty, non-constant physical categorical storage resolves to Categorical. The ordered flag stays on the physical dtype. It is not Ordinal. String evidence is not collected for categorical storage.
9. City names, prose, eligible object strings that are not Identifier, mixed object values, `bytes`, and unsupported families such as complex and period are `INSUFFICIENT_EVIDENCE`. Text is not a fallback. Missing-like literals stay ordinary strings.
10. Eligible string columns collect string structure once. Pattern evidence and string-content evidence receive that same object. Frequency evidence is not collected. No zero-filled stand-in is created for an inapplicable family.
11. The four current assessors run on the candidate path and do not receive the Series. `resolve_semantics` and `build_inferred_semantic_result` are the resolution and construction boundaries.
12. A candidate-derived result has no `SemanticInterpretation` and no High, Medium, or Low confidence. The input Series is not mutated.
13. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. No semantic type, evidence family, threshold, or candidate rule was added.
14. Focused TSK-016 tests pass. TSK-015, TSK-014, TSK-013, TSK-012, TSK-011 foundation, TSK-011 Identifier, TSK-010, TSK-009, TSK-008, TSK-007, and TSK-006 tests pass.
15. Semantic tests for TSK-001 through TSK-016 pass. The legacy profiler stays at 19 passed and the known PDF failure. The full suite adds only the new tests, with the same known PDF failure.
16. [OPEN-047](DECISIONS.md#open-047) records that the column pipeline produces the inferred result and leaves candidate-derived confidence, material alternatives, and the public result open. [OPEN-044](DECISIONS.md#open-questions) stays open for that confidence. [OPEN-045](DECISIONS.md#open-questions) stays open. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open.
17. This section does not approve or implement a later slice.
18. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 18 passed for TSK-016.

## After TSK-016

TSK-016 connects the existing semantic components for one Series and returns the existing inferred result. It preserves structural readings, reaches the current candidate selections, and does not assign confidence to a candidate-derived selection. It does not enter `interpret_series_precedence`, and it does not change `profile` or `compare`. [DEC-087](DECISIONS.md#dec-087) records the contract, including single classification, single basic-evidence collection, structural early exit, applicability branching, and delegated resolution. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-017 was approved later and is recorded below. This section does not create a later task.

## TSK-017

Slice 017, dataset observation and column-analysis retention. Approved 2026-10-03 after TSK-016. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-A-01 for stored row, column, and cell counts only. Dataset dimensions beyond those counts stay open. REQ-S-03 and REQ-S-05 for a DataFrame path that does not mutate the source and keeps physical dtype, observed evidence, and the inferred result distinct. REQ-A-01, REQ-A-02, REQ-A-03, REQ-S-01, and REQ-S-02 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `ColumnEvidence`, `ColumnAnalysis`, and `analyze_series` in `src/pytics/analysis/column.py`. `analyze_series` is the only column collection and semantic orchestration. `infer_series_semantics` returns that analysis's inferred result.
- `ColumnEvidence` stores basic evidence and, when collected, numeric-structure, string-structure, and pattern evidence. `None` means the family was not collected. Composition identity is preserved. Frequency evidence and string-content evidence are not collected. Their fields are absent.
- Structural precedence still returns before candidate-family collection. Empty, Constant, Boolean, Datetime, and Timedelta keep basic evidence only.
- Add `DatasetAnalysis` and `analyze_dataframe` in `src/pytics/analysis/dataset.py`. Stored facts are `n_rows`, `n_columns`, `n_cells`, and one column analysis per physical column. `n_cells` is `n_rows * n_columns`. Missing-cell totals and `missing_ratio` are derived. `missing_ratio` is `None` when there are no cells.
- Column identity is position plus the original label. Duplicate labels stay distinct. Order is source order. Non-string labels and MultiIndex keys are not stringified.
- The DataFrame path calls `analyze_series` once per column and does not also call `infer_series_semantics`. It accepts a DataFrame only. It does not store or mutate the DataFrame or its Series.
- No dataset-context semantic inference, no second pass, no findings, no warnings, no memory-usage contract, no duplicate-row analysis, no semantic-type counts, no configuration, no sampling, and no public `profile()` integration.
- `pytics.semantics` owns semantic inference. `pytics.analysis` owns these records and the DataFrame traversal. That narrows [OPEN-045](DECISIONS.md#open-questions) and does not freeze the rest of the layout.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063). The dataset-analysis contract is [DEC-088](DECISIONS.md#dec-088). It does not close [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), or [OPEN-047](DECISIONS.md#open-047).

### Exclusions

Do not add a semantic type, an evidence family, a candidate rule, a threshold, or a confidence policy. Do not collect frequency evidence or string-content evidence without a consumer. Do not enlarge `InferredSemanticResult`. Do not infer from column labels, the index, or other columns. Do not implement Dataset Overview, Missing patterns, duplicate rows, memory usage, or semantic-type composition. Do not route `pytics.profile` or `pytics.compare` through the analysis. Do not export it from top-level `pytics`.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-045](DECISIONS.md#open-questions) records only the semantics/analysis boundary above. [OPEN-047](DECISIONS.md#open-047) stays open for candidate-derived confidence, material alternatives, and the public result.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `analyze_dataframe` accepts a DataFrame and returns `DatasetAnalysis`. A Series, dict, list, ndarray, or `None` is rejected and is not converted.
2. `analyze_series` accepts a Series. A non-Series is rejected. `infer_series_semantics` returns the inferred result of that same analysis.
3. Each physical column is analyzed once. Physical classification and basic evidence are not collected again for the same column. The DataFrame path does not call `infer_series_semantics`.
4. Column identity keeps position and the original label. Duplicate labels remain distinct records. Source order is preserved. Non-string labels and MultiIndex keys are not stringified or flattened.
5. Retained evidence keeps collector identity. Numeric structure composes with the same basic evidence. Pattern evidence composes with the same string structure. `None` means the family was not collected.
6. Frequency evidence and string-content evidence are not collected. Structural columns retain basic evidence only. Semantic results match the TSK-016 rules.
7. Stored dataset facts are `n_rows`, `n_columns`, and `n_cells`, with `n_cells = n_rows * n_columns`. Derived missing-cell totals use retained basic evidence. A zero cell count makes `missing_ratio` `None`.
8. Zero-row, zero-column, and empty frames follow those facts. Zero-row columns follow the current Empty rule.
9. The DataFrame is not mutated and is not stored. Series values are not stored. No unbounded vocabulary or token list is retained.
10. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. No semantic rule was added.
11. Focused TSK-017 tests pass. TSK-016 tests pass with the same semantic expectations, aside from string-content collection no longer running.
12. The semantic regression and the legacy profiler stay at the previous results, plus the new tests on the full suite, with the known PDF failure unchanged.
13. [OPEN-045](DECISIONS.md#open-questions) records the semantics/analysis boundary and stays open for the rest of the layout. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-047](DECISIONS.md#open-047) stay open.
14. This section does not approve or implement a later slice.
15. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 15 passed for TSK-017.

## After TSK-017

TSK-017 keeps one column analysis per physical DataFrame column and derives missing-cell totals from basic evidence already retained. It does not add a semantic rule, collect frequency or string-content evidence, or change `profile` or `compare`. [DEC-088](DECISIONS.md#dec-088) records the contract, including column position and original label, evidence applicability, and the semantics/analysis package boundary. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-018 was approved later and is recorded below. This section does not create a later task.

## TSK-018

Slice 018, dataset overview foundation. Approved 2026-10-03 after TSK-017. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-A-01 for exposing the stored row, column, and cell counts on an internal overview. REQ-A-03 only for cell completeness, not complete or incomplete rows. REQ-A-05 only for counts of resolved selected semantic types, not physical dtype composition. REQ-A-06 only for Empty, Constant, and Identifier columns already selected, not near-constant or high-cardinality columns. REQ-IA-05 only for the analytical facts behind size, semantic composition, and notable or unresolved columns, not a rendered Overview and not a dataset identity. REQ-A-01, REQ-A-02, REQ-A-03, REQ-A-04, REQ-A-05, REQ-A-06, and REQ-IA-05 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `ColumnRef`, `SemanticTypeCount`, `DatasetOverview`, and `build_dataset_overview` in `src/pytics/analysis/overview.py`.
- The builder accepts `DatasetAnalysis` only. It copies `n_rows`, `n_columns`, and `n_cells`, and it copies the analysis missing-cell totals. It does not scan a DataFrame or a Series.
- `completeness_ratio` is cell completeness: non-missing cells divided by cells, `None` when there are no cells. `missing_ratio` uses the same denominator. Semantic-resolution coverage is resolved columns divided by columns, `None` when there are no columns.
- A resolved column contributes its `selected_type`. A candidate-derived selection counts while `interpretation` is `None`. Semantic type counts omit zeros and follow `SemanticType` definition order.
- `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` are separate column-reference groups. They are not semantic types. Resolved, insufficient, and ambiguous counts sum to the column count. The sum of semantic type counts equals the resolved count.
- Empty, Constant, and Identifier groups are the columns with that selected type. A constant UUID stays Constant. Each reference stores position and the original label. Duplicate labels stay distinct.
- A zero-row schema follows the current Empty rule. Its cell ratios stay undefined and its semantic-resolution ratio is `1.0`. A zero-column schema does not claim full resolution.
- No memory usage, duplicate rows, near-constant rule, high-cardinality rule, physical-dtype histogram, confidence summary, finding, severity, or quality score. No pandas import. The analysis is not retained. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063) and the analysis package in [DEC-088](DECISIONS.md#dec-088). The overview contract is [DEC-089](DECISIONS.md#dec-089). It narrows [OPEN-018](DECISIONS.md#open-questions) for the three dimension counts and the cell-completeness ratio, and it records this slice in [OPEN-037](DECISIONS.md#open-questions). It does not close [OPEN-004](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), or [OPEN-047](DECISIONS.md#open-047).

### Exclusions

Do not rescan values or re-run semantic inference. Do not accept a DataFrame. Do not add memory usage or duplicate-row analysis while their semantics are undecided. Do not add near-constant or high-cardinality thresholds. Do not parse resolver reasons or evidence statements. Do not aggregate confidence. Do not emit Findings or a quality score. Do not render HTML. Do not route `pytics.profile` or `pytics.compare` through the overview. Do not export it from top-level `pytics`. Do not add a dependency.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-018](DECISIONS.md#open-questions) records the dimension and cell-completeness narrowing and stays open for near-constant, high cardinality, and the other unset definitions. [OPEN-045](DECISIONS.md#open-questions) records `overview.py` only as a file in the existing analysis package.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `build_dataset_overview` accepts a `DatasetAnalysis`. A DataFrame, Series, mapping, or `None` raises `TypeError` and is not analyzed.
2. The overview copies `n_rows`, `n_columns`, `n_cells`, `n_missing_cells`, and `n_non_missing_cells`. It does not recompute them from a frame.
3. `completeness_ratio` is non-missing cells divided by cells, and `None` when there are no cells. For a positive cell count it and `missing_ratio` sum to 1 within ordinary floating-point arithmetic. Completeness is not semantic-resolution coverage.
4. Every resolved `selected_type` is counted, including Numeric, Identifier, and Categorical when `interpretation` is `None`, and including a synthetic Text selection. Zero counts are omitted. Order is `SemanticType` definition order. The sum of those counts equals the resolved column count.
5. Insufficient evidence and ambiguity are separate groups. They are not merged and they are not semantic types. Resolved, insufficient, and ambiguous counts sum to `n_columns`. `semantic_resolution_ratio` is `None` when there are no columns.
6. Empty, Constant, and Identifier membership is the selected semantic type. A repeated UUID is Constant. Group counts are the lengths of the reference tuples. References keep position and the original label, including duplicate labels and non-string labels.
7. A zero-row schema is resolved Empty, with semantic-resolution ratio `1.0` and undefined cell ratios. An all-missing populated dataset has missing ratio `1.0` and completeness `0.0`, and its Empty columns come from column semantics.
8. The overview module does not import pandas or call analysis, collection, or resolution functions. It does not retain the analysis. It adds no memory fact, duplicate-row fact, near-constant rule, high-cardinality rule, confidence summary, finding, severity, or quality score.
9. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. No semantic rule was added.
10. Focused TSK-018 tests pass. TSK-017 and the semantic regression stay at the previous results. The full suite adds only the new tests, with the known PDF failure unchanged.
11. [OPEN-018](DECISIONS.md#open-questions) records the dimension and cell-completeness narrowing and stays open for near-constant and high cardinality. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-047](DECISIONS.md#open-047) stay open.
12. This section does not approve or implement a later slice.
13. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 13 passed for TSK-018.

## After TSK-018

TSK-018 summarizes one `DatasetAnalysis` as a frozen overview. It copies dimensions and missing-cell totals, counts resolved selected semantic types, and names Empty, Constant, Identifier, insufficient-evidence, and ambiguous columns by position and original label. It does not rescan the DataFrame, assign candidate confidence, or change `profile` or `compare`. [DEC-089](DECISIONS.md#dec-089) records the contract, including sparse semantic counts, separate cell-completeness and semantic-resolution ratios, and the deferred memory and duplicate-row definitions. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-019 was approved later and is recorded below. This section does not create a later task.

## TSK-019

Slice 019, variables and column-summary foundation. Approved 2026-10-03 after TSK-018. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-B-01 only for count, missing, distinct, zeros, negatives, and infinities already available from basic evidence and numeric-structure evidence. REQ-C-01 only for those universal counts and `unique_ratio_non_missing` on a categorical variable. REQ-C-02 only for the most frequent count and ratio, not the mode value. REQ-C-04 only for singleton count and ratio, not a rare-category percentage. REQ-G-01 only for Identifier as a selected variable type with pattern counts. REQ-G-02 only for those structured pattern counts, not copied evidence statements or confidence. REQ-IA-07 only for the analytical rows and type-specific details, not a rendered table. REQ-B-01, REQ-B-02, REQ-C-01, REQ-C-02, REQ-C-04, REQ-G-01, REQ-G-02, and REQ-IA-07 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `NumericVariableDetail`, `CategoricalVariableDetail`, `IdentifierVariableDetail`, `VariableSummary`, `VariablesSummary`, and `build_variables_summary` in `src/pytics/analysis/variables.py`.
- The builder accepts `DatasetAnalysis` only. It copies identity, physical dtype, resolution status, selected semantic type, and basic counts. It does not scan a DataFrame or a Series.
- `selected_type` is present only for `RESOLVED`. A candidate-derived Numeric, Identifier, or Categorical selection is resolved while `interpretation` is `None`. Confidence and inference source are not copied.
- `unique_ratio_non_missing` divides distinct non-missing values by non-missing values, and is `None` when that count is zero.
- Numeric detail copies retained numeric-structure counts. Monotonicity `None` stays unknown. Mean, median, and the other descriptive summaries are not added.
- `analyze_series` collects existing `FrequencyEvidence` for a non-structural physical categorical column and retains it on `ColumnEvidence`. The collector contract is unchanged. Categorical detail copies the most frequent count and the singleton count. It does not copy the most frequent value. Ordinary strings do not collect frequency evidence.
- Identifier detail copies retained pattern counts. Overlap is not a score. A constant UUID stays Constant and has no Identifier detail.
- Empty, Constant, Boolean, Datetime, Timedelta, Text, insufficient evidence, and ambiguity have common facts and no specialized detail. The constant value is not retained.
- Variables stay in source order. Duplicate labels stay distinct. Labels are not stringified. A zero-row column is Empty with undefined ratios. A zero-column schema has an empty tuple.
- No pandas import in the variables module. The analysis is not retained. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows [DEC-063](DECISIONS.md#dec-063) and the analysis package in [DEC-088](DECISIONS.md#dec-088). The variables contract is [DEC-090](DECISIONS.md#dec-090). It narrows [OPEN-043](DECISIONS.md#open-questions) for detail applicability, [OPEN-045](DECISIONS.md#open-questions) for the product-summary location, and records this slice in [OPEN-037](DECISIONS.md#open-questions). It does not close [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), or [OPEN-047](DECISIONS.md#open-047).

### Exclusions

Do not rescan values from the variables builder. Do not accept a DataFrame. Do not add mean, median, standard deviation, quantiles, skewness, kurtosis, or outlier signals. Do not add Boolean true/false counts, datetime span, timedelta duration statistics, or a Text detail. Do not collect string-content evidence. Do not collect frequency evidence for ordinary strings or structural columns. Do not retain the constant value by a new scan. Do not invent candidate confidence. Do not add Binary or Ordinal. Do not add thresholds, Findings, or renderer text. Do not route `pytics.profile` or `pytics.compare` through the summary. Do not export it from top-level `pytics`. Do not add a dependency.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-043](DECISIONS.md#open-questions) records the detail-applicability narrowing and stays open for the rest of eligibility. [OPEN-045](DECISIONS.md#open-questions) records `variables.py` only as a file in the existing analysis package.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `build_variables_summary` accepts a `DatasetAnalysis`. A DataFrame, Series, mapping, or `None` raises `TypeError` and is not analyzed.
2. Every physical column has one summary in source order, with position, the original label, the physical dtype, resolution status, and the basic counts. `unique_ratio_non_missing` uses the non-missing denominator and is `None` when that count is zero.
3. Numeric, Identifier, and Categorical summaries are `RESOLVED` with that selected type while `interpretation` is `None`. Insufficient evidence and ambiguity have no selected type and no specialized detail.
4. Numeric detail copies retained numeric-structure counts, including infinities and monotonicity. `None` monotonicity is not false. `{0, 1}` and `{0.0, 1.0}` stay Numeric. Mean and the other descriptive summaries are absent.
5. Physical categorical columns that are not Empty or Constant retain `FrequencyEvidence`. Categorical detail exposes most-frequent and singleton counts and ratios, not the top value. Ordered storage stays on the physical dtype. Unused levels follow the existing collector. Ordinary strings do not collect frequency evidence and are not Categorical.
6. Identifier detail copies pattern counts. Compact UUID overlap is not a score. Duplicate UUIDs stay Identifier. A constant UUID is Constant and has no Identifier detail.
7. Empty, Constant, Boolean, Datetime, timezone-aware Datetime, and Timedelta have common summaries and no specialized detail.
8. Duplicate labels stay distinct. Non-string and MultiIndex labels are preserved. A zero-row schema is resolved Empty with undefined ratios. A zero-column schema has an empty tuple.
9. The variables module does not import pandas or call analysis, collection, or resolution functions. It does not retain the analysis. It adds no finding, threshold, confidence, or renderer field.
10. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. No semantic rule was added. `StringContentEvidence` stays uncollected.
11. Focused TSK-019 tests pass. The semantic regression stays at the previous results except for the frequency-collection assertions that this slice changes. The full suite adds only the new tests, with the known PDF failure unchanged.
12. [OPEN-043](DECISIONS.md#open-questions) records the detail-applicability narrowing and stays open. [OPEN-045](DECISIONS.md#open-questions) records the file location and stays open. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-047](DECISIONS.md#open-047) stay open.
13. This section does not approve or implement a later slice.
14. No unrelated production changes were made.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 14 passed for TSK-019.

## After TSK-019

TSK-019 summarizes one `DatasetAnalysis` as ordered variable facts. Every column has common counts. Numeric, Categorical, and Identifier columns can carry a typed detail copied from retained evidence. The other semantic states do not. Frequency evidence is collected only for non-structural physical categorical columns. The variables builder does not rescan the DataFrame, assign candidate confidence, or change `profile` or `compare`. [DEC-090](DECISIONS.md#dec-090) records the contract, including semantic-first detail, the deferred descriptive statistics, and the constant-value gap. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-020 was approved later and is recorded below. TSK-021 was approved after that and is recorded after TSK-020. This section does not create a later task.

## TSK-020

Slice 020, numeric descriptive analysis foundation. Approved 2026-10-03 after TSK-019. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-B-01 only for minimum, maximum, and range on a selected Numeric column. REQ-B-02 only for mean, median, sample standard deviation, Q1, Q3, and interquartile range. Sum, mode, stored variance, MAD, coefficient of variation, skewness, kurtosis, and outlier signals are not this slice. REQ-B-01 and REQ-B-02 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `NumericDescriptiveAnalysis` and `collect_numeric_descriptive_analysis` in `src/pytics/analysis/numeric.py`.
- Collect that result inside `analyze_series` only after resolution, and only when the selected semantic type is Numeric. Retain it on `ColumnAnalysis.numeric_analysis`. Do not put it on `ColumnEvidence` or `InferredSemanticResult`.
- The descriptive population is the finite non-missing values. Missing values and positive and negative infinity are excluded. `finite_count == 0` leaves every statistic `None`.
- Sample standard deviation uses `ddof=1`. One finite value has no standard deviation. Two or more use the sample convention. Do not inherit NumPy's population default.
- Q1, the median, and Q3 use one linear interpolation, the Hyndman-Fan type 7 position `(n - 1) * q`. The method is not configurable.
- Integer minimum and maximum stay exact. Mean and standard deviation are float64. A non-integral integer quantile may be a `Fraction` when float64 would leave the exact extrema. `-0.0` is stored as `0.0`.
- `NumericVariableDetail` keeps the structural counts from TSK-019 and copies the frozen descriptive result. The variables builder does not calculate statistics and does not receive a Series.
- Constant numeric, Empty numeric, Boolean, Identifier, unresolved, and ambiguous columns do not receive the descriptive result. `{0, 1}` and `{0.0, 1.0}` stay Numeric and do receive it.
- No semantic-rule change. No sampling. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The descriptive contract is [DEC-091](DECISIONS.md#dec-091). It narrows [OPEN-010](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says, and records this slice in [OPEN-037](DECISIONS.md#open-questions). It does not close [OPEN-018](DECISIONS.md#open-questions).

### Exclusions

Do not add skewness, kurtosis, histograms, distribution fitting, normality tests, outlier detection, confidence intervals, robust estimators, or Findings. Do not add sum, mode, MAD, or coefficient of variation. Do not store variance as its own field. Do not collect descriptive statistics before the selected semantic type is known. Do not describe a Constant numeric column. Do not change Identifier or Categorical behavior. Do not parse numeric strings, coerce complex values, or mutate the source dtype. Do not put the calculator in `variables.py` or in `pytics.semantics`. Do not add a registry or a plugin framework. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not add a dependency.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-010](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in [DEC-091](DECISIONS.md#dec-091) and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `NumericDescriptiveAnalysis` is a frozen analysis-layer value. It is not semantic evidence, not a field of `InferredSemanticResult`, and not a field of `ColumnEvidence`.
2. `analyze_series` collects it only when the selected semantic type is Numeric. Constant numeric, Empty numeric, Boolean, Identifier, unresolved, and ambiguous columns do not collect it. `{0, 1}` and `{0.0, 1.0}` do.
3. Missing values and both infinities are excluded. A Numeric column with no finite observation keeps its semantic type and stores `None` for every descriptive statistic. Minimum and maximum are never infinite.
4. Standard deviation is the sample convention, `ddof=1`. It is `None` for fewer than two finite values and a non-negative float otherwise.
5. Q1, the median, and Q3 come from one linear-interpolation path. Odd counts, even counts, and interpolation between two values agree with that path.
6. Integer extrema stay exact, including values above `2**53`. Mean and standard deviation may lose integer precision through float64. `-0.0` is stored as `0.0`. The source Series and its dtype are not mutated.
7. `NumericVariableDetail` still exposes the TSK-019 structural counts and also exposes the copied descriptive result. Categorical, Identifier, Boolean, and Constant details are unchanged. The variables builder does not rescan.
8. The retained values enforce finite-count consistency, landmark order, and the one-value and empty-population rules. Representative models are frozen. No Series, DataFrame, or value array is retained.
9. No semantic rule was added. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
10. Focused TSK-020 tests pass. The semantic, analysis, overview, and variables regression stays at the previous results plus the new tests. The full suite adds only the new tests, with the known PDF failure unchanged.
11. [OPEN-010](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-037](DECISIONS.md#open-questions) record the narrowings in this slice and stay open. [OPEN-018](DECISIONS.md#open-questions) stays open without a new threshold.
12. This section does not approve or implement a later slice.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-020.

## After TSK-020

TSK-020 adds finite-population descriptive statistics for a column whose selected semantic type is Numeric. The statistics are analysis facts, collected after resolution, and copied onto the Numeric variable detail. Structural numeric counts from TSK-019 remain. Sum, mode, skewness, kurtosis, distribution shape, outlier signals, and Findings are not delivered. No semantic rule changed. [DEC-091](DECISIONS.md#dec-091) records the contract, including the sample standard deviation, the linear quantile method, and the remaining Numeric gaps. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-021 was approved later and is recorded below. This section does not create a later task.

## TSK-021

Slice 021, Boolean descriptive analysis foundation. Approved 2026-10-03 after TSK-020. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-D-02 is respected because true and false counts follow a selected Boolean type and are not collected for `{0, 1}`, `{0.0, 1.0}`, or two-valued strings. REQ-D-01 and REQ-D-03 are not advanced. Inference is unchanged. REQ-D-01, REQ-D-02, and REQ-D-03 are not completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `BooleanDescriptiveAnalysis` and `collect_boolean_descriptive_analysis` in `src/pytics/analysis/boolean.py`.
- Collect that result inside `analyze_series` only after resolution, and only when the selected semantic type is Boolean. Retain it on `ColumnAnalysis.boolean_analysis`. Do not put it on `ColumnEvidence` or `InferredSemanticResult`.
- Stored fields are `true_count` and `false_count`. `n_non_missing` is their sum and is not stored. `true_ratio` and `false_ratio` divide by that non-missing count and are not stored. A zero sum leaves both ratios `None`.
- `True` contributes only to `true_count`. `False` contributes only to `false_count`. Missing values contribute to neither. `true_count + false_count` equals `n_non_missing`. The ratios are not proportions of all rows.
- The collector accepts boolean storage, including NumPy `bool`, nullable pandas `boolean`, and sparse boolean storage the physical classifier already calls boolean. It rejects a categorical dtype even when the values are boolean. It rejects integers, floats, strings, and objects. It does not treat `1` as `True` or `0` as `False`, and it does not parse strings.
- Empty still precedes Constant, and Constant still precedes Boolean. An all-true, all-false, or all-missing physical Boolean column is not counted.
- `BooleanVariableDetail` copies the two counts. The variables builder does not count and does not receive a Series. A selected Numeric `{0, 1}` column keeps Numeric detail.
- `numeric_analysis` and `boolean_analysis` stay separate optional fields. No analysis registry is added.
- No semantic-rule change. No sampling. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The Boolean descriptive contract is [DEC-092](DECISIONS.md#dec-092). It narrows [OPEN-010](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says, and records this slice in [OPEN-037](DECISIONS.md#open-questions). It does not close [OPEN-014](DECISIONS.md#open-questions) or [OPEN-046](DECISIONS.md#open-046).

### Exclusions

Do not add a Binary semantic type. Do not infer Boolean from `{0, 1}`, `{0.0, 1.0}`, true/false strings, yes/no strings, or arbitrary two-category labels. Do not reinterpret a categorical column whose values are boolean. Do not add entropy, a confidence interval, a hypothesis test, a target relationship, a Finding, or a chart. Do not collect the counts before the selected semantic type is known. Do not count a Constant or Empty boolean column. Do not change Numeric descriptive behavior, including the float64 standard-deviation limits recorded with TSK-020. Do not put the calculator in `variables.py` or in `pytics.semantics`. Do not add a registry, a plugin framework, or an `Any` payload. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not add a dependency.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-010](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in [DEC-092](DECISIONS.md#dec-092) and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `BooleanDescriptiveAnalysis` is a frozen analysis-layer value. It is not semantic evidence, not a field of `InferredSemanticResult`, and not a field of `ColumnEvidence`.
2. `analyze_series` collects it only when the selected semantic type is Boolean, and only after resolution. Constant boolean, Empty boolean, Numeric, Identifier, unresolved, and ambiguous columns do not collect it.
3. `True` and `False` are counted separately. Missing values are in neither count. The ratios use the non-missing denominator. They are derived. A directly constructed zero sum leaves both ratios `None`.
4. Empty still precedes Constant, and Constant still precedes Boolean. All `True`, all `False`, and all missing stay structural and have no Boolean descriptive result.
5. `{0, 1}` and `{0.0, 1.0}` stay Numeric and keep Numeric detail. `"true"`/`"false"`, `"yes"`/`"no"`, and other two-label strings do not receive Boolean analysis. Categorical boolean values stay Categorical. Object storage of Python booleans is not Boolean.
6. `BooleanVariableDetail` copies the counts. The variables builder does not rescan. A selected Boolean variable has no Numeric detail. Constant and Empty boolean columns have common facts only.
7. The retained values reject a negative count, a non-int count, Boolean analysis on a non-Boolean selection, and a count sum that disagrees with `n_non_missing`. The denominator is not stored. No Series, DataFrame, or value array is retained.
8. No semantic rule was added. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added. Numeric descriptive behavior is unchanged.
9. Focused TSK-021 tests pass. The semantic, analysis, overview, and variables regression stays at the previous results plus the new tests. The full suite adds only the new tests, with the known PDF failure unchanged.
10. [OPEN-010](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-037](DECISIONS.md#open-questions) record the narrowings in this slice and stay open. [OPEN-014](DECISIONS.md#open-questions) and [OPEN-046](DECISIONS.md#open-046) stay open.
11. The two float64 limits of TSK-020 remain recorded: distinct integers above float64 precision can produce an incorrect sample standard deviation of `0.0`, and an extreme finite float range can make that deviation non-representable and raise `ValueError`.
12. This section does not approve or implement a later slice.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-021.

## After TSK-021

TSK-021 adds true and false counts for a column whose selected semantic type is Boolean. The counts are analysis facts, collected after resolution, and copied onto a Boolean variable detail. Empty and Constant still precede Boolean. `{0, 1}` and `{0.0, 1.0}` stay Numeric. No semantic rule changed. [DEC-092](DECISIONS.md#dec-092) records the contract, including the non-missing denominator and the unresolved Boolean/Binary boundary. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-022 was approved later and is recorded below. This section does not create a later task.

## TSK-022

Slice 022, missing-data analysis foundation. Approved 2026-10-04 after TSK-021. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-H-01 for dataset, column, and row missingness facts only. REQ-H-02 for exact missingness patterns only, not co-missingness coefficients. REQ-A-03 for complete and incomplete rows on the Missing summary only. REQ-IA-08 for that analytical surface only. REQ-H-04 is respected because missing-like literals stay observed. REQ-H-05 is respected because no mechanism is classified. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `MissingAnalysis`, `collect_missing_analysis`, `MissingSummary`, and `build_missing_summary` in `src/pytics/analysis/missing.py`.
- Retain `missing_analysis` on `DatasetAnalysis`. Collect it inside `analyze_dataframe` after the per-column analyses, from one `DataFrame.isna` pass. Do not retain the DataFrame or the mask.
- Dataset cell facts and column missing counts come from retained analysis. Do not rescan columns to reproduce them.
- Row distribution is an ordered tuple of buckets. Exact patterns use physical positions, include the empty complete-row pattern when complete rows exist, and use the documented order: descending row count, then ascending positions.
- Zero-row frames have no buckets and no patterns. A frame with rows and no columns has one empty pattern. Cell ratios stay `None` when there are no cells. Row ratios are `None` only when there are no rows.
- The product builder consumes `DatasetAnalysis` only. It does not scan the DataFrame and does not depend on the overview or variables builders.
- No semantic-rule change. No sampling and no pattern cutoff. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The missingness contract is [DEC-093](DECISIONS.md#dec-093). It narrows [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says. It does not close the missing-like literal list.

### Exclusions

Do not add missing-like literal detection beyond the existing decision to leave those literals observed. Do not impute, clean, or recommend fills. Do not classify MCAR, MAR, or MNAR. Do not add Little's MCAR test, a pairwise co-missingness coefficient, a correlation matrix, clustering, a heatmap, a Finding, or a chart. Do not add target-conditioned missingness, compare or drift missingness, or a sampling mode. Do not put dataset-level missingness in `pytics.semantics`. Do not change Numeric descriptive behavior, including the float64 standard-deviation limits recorded with TSK-020. Do not change Boolean counting. Do not grow the variables or overview builders with this surface. Do not add a registry. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not add a dependency.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in [DEC-093](DECISIONS.md#dec-093) and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `MissingAnalysis` is retained on `DatasetAnalysis`. It stores the row distribution and exact patterns. It does not store the DataFrame, a row index, or the boolean mask.
2. `build_missing_summary` accepts only a `DatasetAnalysis`. It copies cell facts and basic-evidence column counts. It does not call pandas missingness or the collector.
3. Column records keep source order, original labels, duplicate labels, and physical position as pattern identity. A zero-row column has counts of zero and `missing_ratio` `None`.
4. Patterns include `()` when complete rows exist. Order is descending row count, then ascending positions. The row distribution omits empty buckets and matches pattern widths.
5. Pandas missingness is the rule. `""`, whitespace, and `"NA"` stay observed. `None`, `NaN`, `pd.NA`, and `NaT` are missing where pandas already says so.
6. `0 × 0` and `0 × N` have no buckets, no patterns, and undefined cell and row ratios. `N × 0` has N complete rows, one empty pattern, undefined cell ratios, and row ratios `1.0` and `0.0`.
7. The cross-layer count invariants hold, including pattern margins against column `n_missing` and pattern width times row count against `n_missing_cells`.
8. The overview and the variables summary are not rewritten. They agree with the Missing summary on the shared cell and column missing counts, and neither product calls the other.
9. The source DataFrame is unchanged. After analysis exists, the summary builder still succeeds when collection and pandas missingness are patched to fail. No mechanism label, coefficient, imputation, Finding, or chart was added.
10. The pass is exact. There is no undocumented pattern cutoff. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
11. Focused TSK-022 tests pass. The full suite adds only the new tests, with the known PDF failure unchanged. Numeric and Boolean behavior is unchanged.
12. [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in this slice and stay open. The two float64 limits of TSK-020 remain recorded.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-022.

## After TSK-022

TSK-022 records where values are missing and which physical positions are missing together. It does not say why they are missing. Complete and incomplete rows live on the Missing summary. The dataset overview, at the end of TSK-022, still reported cell completeness only. TSK-023 later copies unique-row and excess-duplicate counts onto it. Pairwise co-missingness coefficients, missing-like literal diagnostics, and mechanism classification are not delivered. [DEC-093](DECISIONS.md#dec-093) records the contract, including positional pattern identity, the empty complete-row pattern, and the exact full-frame pass. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-023 was approved later and is recorded below. This section does not create a later task.

## TSK-023

Slice 023, duplicate-data analysis foundation. Approved 2026-10-04 after TSK-022. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-I-01 for exact duplicate rows and duplicate groups only. REQ-A-04 for unique rows and excess duplicate rows on the overview only. REQ-IA-09 and REQ-IA-05 for those analytical facts only. REQ-I-05 is respected because no column-combination search is added. REQ-I-06 is respected because near-duplicates are not analyzed. REQ-I-02, REQ-I-03, and REQ-I-04 are not advanced. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add `DuplicateAnalysis`, `DuplicateGroup`, `collect_duplicate_analysis`, `DuplicateSummary`, and `build_duplicate_summary` in `src/pytics/analysis/duplicate.py`.
- Retain `duplicate_analysis` on `DatasetAnalysis`. Collect it inside `analyze_dataframe` after the missingness pass. Do not make either pass depend on the other. Do not retain the DataFrame or the row values.
- A duplicate group stores strictly increasing physical row positions. `size` and `excess_count` are derived. Singleton rows are not stored.
- Group order is descending size, then ascending first physical position, then the position tuple.
- Row equality is pandas `factorize` equality for every physical column, including one shared code for pandas-missing values in that column. The index and the column labels are not part of the row.
- `0 × 0` and `0 × N` have no groups and undefined row ratios. `1 × 0` has one unique empty row and no group. `N × 0` with `N >= 2` has one group of every physical position.
- `DuplicateSummary` copies `n_rows` and the groups. It does not rescan. `DatasetOverview` copies `n_unique_rows` and `n_excess_duplicate_rows` from the same derivations and does not store groups.
- No semantic-rule change. No sampling and no group cutoff. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The duplicate contract is [DEC-094](DECISIONS.md#dec-094). It narrows [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-020](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says. It does not close controlled partial duplicates or fuzzy scope.

### Exclusions

Do not add approximate string matching, fuzzy row matching, whitespace or case normalization, numeric or datetime tolerance, Unicode normalization, entity resolution, or record linkage. Do not add duplicate-column detection, identifier-duplicate reporting, conflicting duplicates, or partial-duplicate search. Do not add a Finding, severity, or quality score. Do not decide that a duplicate row is an error. Do not put dataset-level duplication in `pytics.semantics`. Do not add duplicate fields to `VariableSummary`. Do not infer duplicate groups from missingness patterns. Do not change Numeric descriptive behavior, including the float64 standard-deviation limits recorded with TSK-020. Do not change Boolean counting. Do not change the missingness contract, including its scalability limits. Do not add a registry. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not add a dependency.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-020](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in [DEC-094](DECISIONS.md#dec-094) and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `DuplicateAnalysis` is retained on `DatasetAnalysis`. It stores duplicate groups of physical positions. It does not store the DataFrame, the index, row values, or singleton positions.
2. `build_duplicate_summary` accepts only a `DatasetAnalysis`. It copies groups. It does not call factorize, `duplicated`, or the collector.
3. Counts distinguish `n_unique_rows`, `n_duplicate_groups`, `n_rows_in_duplicate_groups`, and `n_excess_duplicate_rows`. There is no undefined `duplicate_count`. Row ratios use `n_rows` and are `None` when there are no rows.
4. Group order is descending size, then ascending first physical position. Positions are physical positions, not index labels. Duplicate labels stay separate columns.
5. Pandas factorize equality is the rule. Missing values in the same physical positions can share a group. `"NA"`, case, whitespace, and unequal floats stay distinct. `-0.0` matches `0.0` under that equality.
6. Unhashable `list`, `dict`, and `set` cells raise `TypeError` when rows must be compared. No custom serializer is added.
7. `0 × 0` and `0 × N` have no groups and undefined ratios. `1 × 0` has one unique row and no group. `N × 0` with `N >= 2` has one group of every row. That zero-column result is not pandas `drop_duplicates`.
8. The stated count invariants hold, including `n_excess_duplicate_rows == n_rows - n_unique_rows` and the group sums.
9. The overview copies `n_unique_rows` and `n_excess_duplicate_rows` from the duplicate analysis and agrees with the summary. It does not store groups. The variables summary is unchanged.
10. The source DataFrame is unchanged. After analysis exists, the summary builder still succeeds when collection and pandas factorize are patched to fail. No Finding or near-duplicate rule was added.
11. The pass is exact. There is no undocumented group cutoff. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
12. Focused TSK-023 tests pass. The full suite adds only the new tests, with the known PDF failure unchanged. Numeric, Boolean, and Missing behavior is unchanged. [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-020](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in this slice and stay open. The TSK-020 float64 limits and the TSK-022 missingness limits remain recorded.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-023.

## After TSK-023

TSK-023 records which rows are exactly equal, how many distinct row values exist, and how many occurrences are beyond one of each value. It does not say whether those repetitions are errors. Identifier duplicates, conflicting duplicates, partial duplicates, and near-duplicates are not delivered. [DEC-094](DECISIONS.md#dec-094) records the contract, including factorize equality, physical positions, and the zero-column empty row. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-024 was approved later and is recorded below. This section does not create a later task.

## TSK-024

Slice 024, numeric relationship-analysis foundation. Approved 2026-10-04 after TSK-023. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-K-01, REQ-K-02, and REQ-K-04 for selected Numeric × Numeric only. REQ-K-03 remains in force and is respected. REQ-K-05 is respected because no assumption test gates a method. REQ-P-10 is respected for this result and is not completed as a rendered presentation. REQ-G-03 is respected for identifiers in this pass. REQ-IA-11 is not completed because the view is not rendered. REQ-T-03 is respected because no method registry is added. REQ-T-05 is not completed. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Add relationship analysis in `src/pytics/analysis/relationship.py`.
- Retain `relationship_analysis` on `DatasetAnalysis`. Collect it inside `analyze_dataframe` after the duplicate pass. Do not make the missing, duplicate, and relationship passes call each other.
- Identify pairs by physical position, with the left position smaller. Do not use labels as identity.
- Calculate only selected Numeric × selected Numeric. Count recognized unimplemented families. Count other pairs as ineligible. Do not retain one record per unsupported pair, and do not read raw values for those pairs.
- Use pairwise finite observations. Exclude missing values and infinities. Do not impute.
- Spearman is the primary descriptive association. Pearson is complementary. Keep the estimate, the frequentist test, and the confidence interval as separate availability states.
- Pearson's interval is the classical Fisher z interval at 95%. Spearman has no interval in this slice.
- Store raw p-values. Do not apply a multiple-testing adjustment while the test family is undefined.
- Do not add a normality gate, a significance flag, a strength label, a Finding, or a chart.
- `build_relationships_summary` reads the retained analysis and does not recompute.
- The pass is exact and full-frame. There is no sampling and no hidden pair cutoff.
- No semantic-rule change. `profile` and `compare` are unchanged.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The relationship contract is [DEC-095](DECISIONS.md#dec-095). It narrows [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says. It does not close the method catalog or the multiple-testing family.

### Exclusions

Do not add Numeric × Boolean, Numeric × Categorical, Boolean × Boolean, Categorical × Categorical, datetime, timedelta, text, or ordinal relationship methods. Do not add Kendall, bootstrap, or permutation intervals. Do not add Shapiro-Wilk or any other assumption test. Do not add Benjamini-Hochberg or another adjustment. Do not add significance stars, strength labels, or Findings. Do not add charts. Do not coerce non-Numeric selected types. Do not claim exact correlation for integers above `2**53`. Do not change Numeric descriptive behavior, including the float64 standard-deviation limits recorded with TSK-020. Do not change Boolean counting, missingness, or duplicate grouping. Do not add a registry. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not add a dependency or raise the SciPy floor.

Do not resolve [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). The open questions named in [DEC-095](DECISIONS.md#dec-095) record the narrowings and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `RelationshipAnalysis` is retained on `DatasetAnalysis`. It stores Numeric × Numeric records and coverage counts. It does not store the DataFrame, paired arrays, or a record for every unsupported pair.
2. Pair identity is physical position, ordered so the left position is smaller. Duplicate labels stay distinct pairs.
3. Eligibility follows the selected semantic type. Constant, Empty, Identifier, and unresolved columns are not Numeric × Numeric pairs. Recognized unimplemented families are counted and not calculated.
4. The statistical population is pairwise finite. `n_paired` is that count. Missing values and infinities are excluded. There is no imputation.
5. Spearman and Pearson are both retained when the pair is eligible. Spearman is the primary descriptive method. A normality test does not choose between them.
6. An estimate, a p-value, and a confidence interval can be unavailable separately. Unavailable results are not stored as `0.0` or NaN. The dataset analysis does not fail because one method is unavailable.
7. The Pearson interval is classical Fisher z at 95% where it is defined. Spearman has no interval. Raw p-values are stored. Adjusted p-values are not calculated.
8. Integers that remain distinct but collapse in float64 make the methods unavailable. The result does not claim exact integer correlation above `2**53`.
9. `build_relationships_summary` accepts only a `DatasetAnalysis`. After analysis exists, it still succeeds when SciPy and the raw collector are patched to fail.
10. `0 × 0`, `N × 0`, and `N × 1` have no pairs. `0 × N` follows the selected semantic types and does not override Empty.
11. The source DataFrame is unchanged. No DataFrame, Series, Index, ndarray, or SciPy result is retained. `pytics.profile`, `pytics.compare`, and `pytics.__all__` are unchanged. No dependency was added.
12. Focused TSK-024 tests pass. The full suite adds only the new tests, with the known PDF failure unchanged. Numeric, Boolean, Missing, and Duplicate behavior is unchanged. [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in this slice and stay open. The TSK-020, TSK-022, and TSK-023 limits remain recorded.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-024.

## After TSK-024

TSK-024 records how selected Numeric variables are associated, how large that association is, and what frequentist evidence is available. It does not say that an association is important, and it does not analyze other pair families. [DEC-095](DECISIONS.md#dec-095) records the contract, including positional pair identity, pairwise finite observations, Spearman as the primary method, and the decision not to adjust p-values yet. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-025 was approved later and is recorded below. This section does not create a later task.

## TSK-025

Slice 025, numeric robustness and relationship-package consolidation. Approved 2026-10-04 after TSK-024. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-B-01 for minimum, maximum, and range on a selected Numeric column, including a range that is undefined when the difference is not finite. REQ-B-02 for mean, median, sample standard deviation, Q1, Q3, and interquartile range, including a mean, sample standard deviation, or interquartile range that is undefined when it is not a finite supported number. Neither requirement row is completed. REQ-K-01 through REQ-K-05 are unchanged. See [PROGRESS.md](PROGRESS.md).

### Scope

- Keep a valid finite Numeric population when one derived statistic cannot be stored as a finite float64. Store that statistic as `None`. Do not store NaN, infinity, or a fabricated zero.
- Preserve exact integer extrema. Center large integers before the float64 sample standard deviation so a difference of 1 is not erased by magnitude.
- Keep sample standard deviation at `ddof=1`, and keep Hyndman-Fan type 7 quantiles.
- Leave range and interquartile range undefined when the difference is not finite. Keep exact integer differences.
- Do not change semantic inference. An unavailable descriptive statistic does not change the selected Numeric type and does not drop relationship analysis.
- Do not change TSK-024 statistical rules. Float64 precision collapse of a correlation stays.
- Move the relationship implementation into `pytics.analysis.relationships` (`models.py`, `numeric_numeric.py`, `collector.py`). Keep `pytics.analysis.relationship` as a re-export. Do not add a registry or another relationship family.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The contract is [DEC-096](DECISIONS.md#dec-096). It narrows [OPEN-006](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says.

### Exclusions

Do not add Numeric × Boolean, Numeric × Categorical, Boolean × Boolean, Categorical × Categorical, multiple-testing correction, bootstrap intervals, permutation tests, Bayesian methods, Findings, visualizations, Quick/Standard/Deep, target analysis, anomaly analysis, or compare/drift. Do not redesign the public API or the renderer. Do not change semantic inference. Do not add a dependency or raise a dependency floor. Do not claim arbitrary-precision statistics.

Do not resolve [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). The TSK-022 missingness limits and the TSK-023 duplicate limits remain. Float64 relationship precision collapse remains.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. Distinct large integers do not produce a sample standard deviation of `0.0` solely because float64 cannot represent their absolute values. A true constant remains `0.0`.
2. Extreme finite Numeric observations do not abort `analyze_series` or `analyze_dataframe` when a derived statistic is not a finite float64.
3. `None` is distinguishable from numeric zero and from NaN. An available float statistic is finite.
4. Extrema, and quantiles that follow the existing population rules, stay available when only the mean, deviation, range, or interquartile range fails.
5. Integer minimum and maximum stay exact, including values above `2**53`.
6. Ordinary Numeric results do not materially regress. Sample deviation stays `ddof=1`. Quartiles stay type 7.
7. Semantic interpretation is unchanged. The column stays Numeric when a descriptive statistic is unavailable.
8. Relationship analysis still runs in that case. Spearman can remain available when the descriptive deviation or Pearson is not.
9. TSK-024 statistical behavior is unchanged. Float64 precision collapse of a correlation remains.
10. The relationship package separates shared models, Numeric × Numeric calculation, and dataset collection. No generic registry was added. No new family was added.
11. Retained results do not keep the source DataFrame, Series, or calculation arrays. The variables builder does not recompute a statistic.
12. The full suite has only the known legacy PDF failure. [OPEN-006](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings and stay open.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-025.

## After TSK-025

TSK-025 keeps a valid Numeric column when a derived statistic does not fit in float64, and it separates relationship models from the one implemented family. It does not add a family and it does not say which family comes next. [DEC-096](DECISIONS.md#dec-096) records the numerical guarantee and the package boundary. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-026 was approved later and is recorded below. This section does not create a later task.

## TSK-026

Slice 026, Numeric × Categorical relationship foundation. Approved 2026-10-04 after TSK-025. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-K-01, REQ-K-02, and REQ-K-04 for selected Numeric × selected Categorical only, in addition to the Numeric × Numeric coverage from TSK-024. REQ-K-03 remains in force and is respected. REQ-K-05 is respected because no assumption test gates the omnibus method. REQ-P-10 is respected for this result and is not completed as a rendered presentation. REQ-G-03 is respected for identifiers in this pass. REQ-IA-11 is not completed because the view is not rendered. REQ-T-03 is respected because no method registry is added. REQ-T-05 is not completed. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Calculate selected Numeric × selected Categorical in `relationships/numeric_categorical.py`.
- Keep physical position as pair identity. Record numeric and categorical roles separately from left and right.
- Use finite Numeric values paired with a non-missing category. Keep only observed groups.
- Reuse Numeric descriptive statistics for each group.
- Store eta squared, `SS_between / SS_total`, as the overall effect.
- Store classical one-way ANOVA from `scipy.stats.f_oneway` with no keyword arguments as the omnibus test.
- Keep the effect and the raw p-value separate. Do not adjust the p-value.
- Do not add a post-hoc test, an assumption gate, a strength label, a category cutoff, or a Finding.
- `build_relationships_summary` copies both family records and does not recompute.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The contract is [DEC-097](DECISIONS.md#dec-097). It narrows [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says. It does not close the method catalog, ordinal storage, high cardinality, or the multiple-testing family.

### Exclusions

Do not add Welch ANOVA, Kruskal–Wallis, omega squared, epsilon squared, Tukey, Games–Howell, Dunn, pairwise t-tests, or pairwise rank tests. Do not add Shapiro, Levene, or Bartlett. Do not add Benjamini-Hochberg. Do not treat Boolean as Categorical. Do not score ordered categories. Do not add a high-cardinality cutoff or a sample. Do not change Numeric × Numeric statistical rules. Do not change semantic inference. Do not add a dependency or raise the SciPy floor. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`.

Do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). The open questions named in [DEC-097](DECISIONS.md#dec-097) record the narrowings and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. Selected Numeric × selected Categorical is a supported relationship family. Boolean is not treated as Categorical.
2. Analytical roles do not depend on which physical side is numeric. Pair identity remains the two physical positions.
3. The population is finite Numeric values paired with a non-missing category. Only observed groups participate.
4. Group summaries use the Numeric descriptive definitions, including `ddof=1` and type-7 quartiles.
5. Eta squared is stored separately from the raw one-way ANOVA p-value. There is no strength label and no significance flag.
6. Degenerate cases are explicit. They do not fail dataset analysis. Zero within-group variation keeps eta squared at `1.0` when the effect is defined and leaves both the F statistic and the p-value unavailable.
7. Large integer offsets do not collapse a real between-group difference into a zero effect.
8. Category identity is not display-string coercion. There is no hidden cardinality cutoff or sample.
9. No post-hoc test and no assumption gate are implemented. Multiple-testing adjustment is not applied.
10. `build_relationships_summary` copies retained records and does not recompute.
11. Numeric × Numeric behavior is unchanged. The second family uses the existing package without a method registry.
12. The full suite has only the known legacy PDF failure. Documentation states the formula, the ANOVA call, and the limitations.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-026.

## After TSK-026

TSK-026 records whether the location of a selected Numeric variable differs across the observed groups of a selected Categorical variable, how large that overall association is, and what omnibus evidence accompanies it. It does not say which category pairs differ. [DEC-097](DECISIONS.md#dec-097) records the contract, including eta squared, classical one-way ANOVA, observed groups, and the decision not to adjust p-values. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-027 was approved later and is recorded below. This section does not create a later task.

## TSK-027

Slice 027, heterogeneous relationship result model and statistical metadata. Approved 2026-10-04 after TSK-026. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-K-01, REQ-K-02, and REQ-K-04 are unchanged. REQ-K-03 remains in force. REQ-K-05 is respected because no assumption test was added. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are not completed. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Keep `RelationshipAnalysis` and `RelationshipsSummary` as coverage containers for family-specific records.
- Remove dataset-level `primary_method`, `population`, `computation`, `confidence_level`, `multiple_testing`, and `implemented_families`.
- Keep pair counts on each pair. Keep the Numeric × Numeric and Numeric × Categorical eligibility rules on those records.
- Keep the 95% Fisher-z level on an available Pearson interval. Do not put a confidence level on a Numeric × Categorical record.
- Keep Spearman as the named primary component of a Numeric × Numeric record. Do not add a shared primary-method field.
- Keep adjustment on each frequentist result. Do not apply a correction.
- Keep `RelationshipFamily` as the families this version calculates. Presence in a dataset is the retained records.
- Keep physical pair identity and Numeric × Categorical roles. Do not add a universal pair record or a registry.
- Do not change Numeric × Numeric or Numeric × Categorical statistical outputs.
- `build_relationships_summary` copies retained records and does not recompute.
- Keep one `relationship_analysis` field on `DatasetAnalysis`.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the analysis package in [DEC-088](DECISIONS.md#dec-088). The contract is [DEC-098](DECISIONS.md#dec-098). It narrows [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says. It does not close the method catalog, the public result, or the multiple-testing family.

### Exclusions

Do not add Boolean × Boolean, Categorical × Categorical, or any other relationship family. Do not change Spearman, Pearson, the Fisher z interval, eta squared, or classical one-way ANOVA. Do not add Welch, Kruskal–Wallis, post-hoc tests, or a multiple-testing correction. Do not add a plugin, registry, or generic statistics schema. Do not split `models.py` only to move classes. Do not change semantic inference, Numeric descriptive behavior, Boolean counting, missingness, or duplicate grouping. Do not add a dependency or raise the SciPy floor. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not freeze the internal dataclasses as a public schema.

Do not resolve [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). The open questions named in [DEC-098](DECISIONS.md#dec-098) record the narrowings and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. `RelationshipAnalysis` and `RelationshipsSummary` do not claim one primary method, one population rule, one computation, or one confidence level for every pair.
2. Pair population counts stay on the pair. The two implemented eligibility rules stay distinguishable.
3. An available Pearson interval records 95% Fisher z. A Numeric × Categorical record has no confidence level.
4. A Numeric × Numeric record exposes Spearman and Pearson without a dataset `primary_method`. Eta squared and ANOVA stay separate.
5. Adjustment status stays on frequentist evidence. No correction is applied, and no dataset-wide adjustment is stored.
6. `RelationshipFamily` names families this version calculates. Retained records name families present in a dataset. Coverage invariants are unchanged.
7. Physical pair identity and Numeric × Categorical roles are unchanged. There is no universal pair record and no registry.
8. Numeric × Numeric and Numeric × Categorical statistical outputs are unchanged, including zero within-group ANOVA.
9. `build_relationships_summary` copies retained records and does not recompute or read the DataFrame.
10. `DatasetAnalysis` keeps one `relationship_analysis` field. A later family can be another record type without changing that field list.
11. No dependency was added and the SciPy floor was not raised. `profile` and `compare` are unchanged. Internal names are not a public schema.
12. The full suite has only the known legacy PDF failure. Documentation records ownership and the remaining debt.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-027.

## TSK-028

Slice 028, Boolean × Boolean relationship analysis. Approved 2026-10-04 after TSK-027. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-K-01, REQ-K-02, and REQ-K-04 for selected Boolean × Boolean in addition to Numeric × Numeric and Numeric × Categorical. REQ-K-03 remains in force. REQ-K-05 is respected because no assumption test was added. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are not completed. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Calculate selected Boolean × selected Boolean only. Do not infer Boolean from `{0, 1}`, `{0.0, 1.0}`, Boolean-like strings, or a categorical column.
- Keep canonical physical pair identity. Name the left column the conditioning variable and the right column the outcome variable. Those roles are conditional probabilities, not causes.
- Use the pairwise non-missing Boolean population. Retain all four 2×2 cells.
- Store the probability difference, the probability ratio, and phi separately from a raw two-sided Fisher exact p-value.
- Leave an exact infinite ratio unavailable. Do not add a continuity correction or a confidence interval.
- Add `BOOLEAN_BOOLEAN` to `RelationshipFamily` and remove it from the unimplemented families. Keep coverage identities.
- Copy the record in `build_relationships_summary` without recomputing.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the relationship package in [DEC-096](DECISIONS.md#dec-096). The contract is [DEC-099](DECISIONS.md#dec-099). It narrows [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-008](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) only as that decision says. It does not close the method catalog, the public result, or the multiple-testing family.

### Exclusions

Do not add Categorical × Categorical, Numeric × Boolean, or a generic RxC contingency framework. Do not add an odds ratio, Cramér's V, Pearson chi-square, Barnard's test, Boschloo's test, or a Boolean confidence interval. Do not add a continuity correction. Do not change Spearman, Pearson, the Fisher z interval, eta squared, or classical one-way ANOVA. Do not change semantic inference or Boolean descriptive counting. Do not add a multiple-testing correction, a plugin, or a registry. Do not split `models.py` only because it grew. Do not add a dependency or raise the SciPy floor. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not freeze the internal dataclasses as a public schema.

Do not resolve [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). The open questions named in [DEC-099](DECISIONS.md#dec-099) record the narrowings and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. Selected Boolean × Boolean is calculated. Integer `{0, 1}`, Boolean-like strings, and categorical Boolean values are not.
2. Canonical physical pair identity stays. Conditioning is the left column and outcome is the right column. That orientation is not causal.
3. Pairwise non-missing rows are exact. The four cells sum to `n_paired`. A zero event count is distinct from an absent conditioning level.
4. The probability difference, the probability ratio, and phi have explicit formulas. An exact infinite ratio is unavailable. No continuity correction is applied.
5. Two-sided Fisher exact supplies the raw p-value only. SciPy's odds ratio is not stored. A constant margin does not store a p-value of `1.0`.
6. Adjustment stays unapplied. No strength label and no confidence interval are added.
7. `RelationshipFamily` includes Boolean × Boolean. Coverage reconciles. A degenerate pair still retains a record when the table can be stored.
8. The product summary copies the record and does not reread the DataFrame or call Fisher.
9. The record does not retain a DataFrame, Series, Index, ndarray, BooleanArray, or SciPy result.
10. Repeated analysis is equal. Previous Numeric families are unchanged. No generic RxC framework or registry is added.
11. No dependency was added and the SciPy floor was not raised. `profile` and `compare` are unchanged.
12. The full suite has only the known legacy PDF failure. [DEC-099](DECISIONS.md#dec-099) records the statistical contract, including the measured Fisher cost.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-028.

## After TSK-028

TSK-028 calculates selected Boolean × Boolean and leaves Categorical × Categorical, Boolean confidence intervals, and the odds ratio unselected. [DEC-099](DECISIONS.md#dec-099) records the 2×2 contract. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-029 was approved later and is recorded below. This section does not create a later task.

## TSK-029

Slice 029, Numeric × Boolean relationship analysis. Approved 2026-10-04 after TSK-028. Completed the same day. No later slice is approved by this section.

Linked requirements: REQ-K-01, REQ-K-02, and REQ-K-04 for selected Numeric × selected Boolean in addition to the three earlier families. REQ-K-03 remains in force. REQ-K-05 is respected because no assumption test selects or replaces the method. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are not completed. REQ-L-01 through REQ-L-07 are not advanced. None of those requirement rows is completed. See [PROGRESS.md](PROGRESS.md).

### Scope

- Calculate selected Numeric × selected Boolean in either physical order. Do not infer Boolean from `{0, 1}`, `{0.0, 1.0}`, Boolean-like strings, or a categorical column.
- Keep canonical physical pair identity. Record `numeric_position` and `boolean_position`. Orient every signed component as True minus False, whichever side is Boolean. That orientation is not causal.
- Use finite Numeric values paired with non-missing Boolean values. Exclude each missing or infinite row once. Do not impute.
- Keep a False group and a True group in logical order. Describe each observed group with the Numeric descriptive calculator. Keep an absent level as an unavailable group.
- Store the mean difference in Numeric units, Hedges' g with the exact correction, the 95% Welch–Satterthwaite interval, and Welch's t-test with a raw two-sided p-value as separate components.
- Use one set of stable group moments: each group offset from its own exact minimum, with the two means combined exactly and rounded once.
- Leave zero within-group variation, one-value groups, and non-finite results unavailable with explicit reasons. Do not store infinity, NaN, a p-value of zero for a degenerate test, or a zero-width interval.
- Add `NUMERIC_BOOLEAN` to `RelationshipFamily` and remove it from the unimplemented families. Keep coverage identities.
- Copy the record in `build_relationships_summary` without recomputing.

Representation follows [DEC-062](DECISIONS.md#dec-062). Placement follows the relationship package in [DEC-096](DECISIONS.md#dec-096) and the model package recorded with [DEC-099](DECISIONS.md#dec-099). The contract is [DEC-100](DECISIONS.md#dec-100). It narrows [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) only as that decision says. It does not close the method catalog, the public result, Binary's representation, or the multiple-testing family.

### Exclusions

Do not add Categorical × Boolean, Categorical × Categorical, target analysis, binary subtype inference, or `{0, 1}` to Boolean inference. Do not add a generic two-group framework, a test registry, post-hoc analysis, or a multiple-testing correction. Do not add Student's pooled t-test, Mann–Whitney U, Brunner–Munzel, a permutation test, Cohen's d, Glass's delta, a median-difference component, or an interval for Hedges' g. Do not select a method with Shapiro, Levene, or another assumption test. Do not add strength or significance labels. Do not change semantic inference, Numeric descriptive behavior, Boolean counting, or the Numeric × Numeric, Numeric × Categorical, and Boolean × Boolean calculations. Do not add a dependency or raise the SciPy floor. Do not route `pytics.profile` or `pytics.compare` through this result. Do not export it from top-level `pytics`. Do not freeze the internal dataclasses as a public schema. Do not render it.

Do not resolve [OPEN-009](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), or [OPEN-049](DECISIONS.md#open-049). The open questions named in [DEC-100](DECISIONS.md#dec-100) record the narrowings and stay open.

Do not add a dependency. Do not approve a later slice.

### Acceptance criteria

1. Selected Numeric × selected Boolean is calculated in both physical orders. Integer `{0, 1}`, `{0.0, 1.0}`, Boolean-like strings, and categorical Boolean values do not take the Boolean role. No semantic rule changes.
2. Canonical physical pair identity stays. `numeric_position` and `boolean_position` are explicit. Every signed component is True minus False.
3. The population is finite Numeric with non-missing Boolean. Missing and infinite rows are excluded once. Group sizes sum to `n_paired`.
4. Each observed group uses the Numeric descriptive definitions. An absent level is an unavailable group. The Boolean column is not reclassified.
5. The mean difference is stored in Numeric units. Large integer offsets do not create a false zero difference or a false zero spread.
6. Hedges' g uses the pooled sample deviation and the exact correction, needs two pooled degrees of freedom, and is unavailable rather than finite when pooled variation is zero.
7. Welch's t-test stores t, the Welch–Satterthwaite degrees of freedom, and the raw two-sided p-value, and matches SciPy on ordinary data. No assumption test selects it.
8. The 95% Welch–Satterthwaite interval comes from the same moments as the test. Constant and one-value groups leave the interval and the test unavailable with explicit reasons.
9. Non-finite results are not stored as estimates. Adjustment stays unapplied. No strength label or significance flag is added.
10. `RelationshipFamily` includes Numeric × Boolean. Coverage reconciles. `RelationshipRecord` has a fourth typed variant. There is no universal record and no registry.
11. The product summary copies records without rereading the DataFrame or calling SciPy. No DataFrame, Series, Index, ndarray, BooleanArray, or SciPy result is retained. Repeated and row-reordered analysis is equal. The three earlier families are unchanged. No dependency was added.
12. The full suite has only the known legacy PDF failure. [DEC-100](DECISIONS.md#dec-100) records the statistical contract, and the measured cost is recorded.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md). All 12 passed for TSK-029.

## After TSK-029

TSK-029 calculates selected Numeric × Boolean and leaves robust and rank-based complements, Categorical × Boolean, Categorical × Categorical, and target analysis unselected. [DEC-100](DECISIONS.md#dec-100) records the two-group contract. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-030 was approved later and is recorded below. This section does not create a later task.

## TSK-030

Slice 030, Categorical × Categorical relationship analysis. Approved 2026-10-04 after TSK-029. Completed the same day. No later slice is approved by this section.

Calculate selected Categorical × selected Categorical only. Keep canonical physical pair identity. Use the pairwise non-missing categorical population. Retain the observed contingency table, classical Cramér's V, expected-count diagnostics, and uncorrected Pearson chi-square with a raw p-value. Do not apply Yates's correction. Do not switch sparse tables to Fisher's exact test. Do not add a bias correction, an interval, ordinal association, mutual information, Theil's U, a G-test, a Monte Carlo test, multiple-testing correction, findings, or a renderer. Do not change semantic inference. Do not merge this family with Boolean × Boolean. Do not add target semantics. Do not add a generic contingency framework, a superclass, or a registry.

Acceptance checks:

1. Selected Categorical × Categorical is calculated. Semantic inference is unchanged. Canonical physical pair identity is unchanged.
2. Both axes follow the physical categorical vocabulary with unused levels removed. The population is pairwise non-missing. Exclusions reconcile. The source frame is unchanged.
3. The observed contingency table and its margins are retained as Python integers. Invariants are enforced. Category values are not stringified.
4. A high-cardinality pair cannot allocate an uncontrolled Cartesian matrix. The `2**20` histogram bound is an algorithm switch, not a statistical cutoff, and the pair remains calculated above it.
5. Classical Cramér's V is the symmetric effect. Its formula is frozen. It is unsigned and lies on `[0, 1]`. Degenerate tables have explicit availability.
6. Pearson's chi-square of independence is the frequentist result. Yates's correction is off, including for 2×2. Degrees of freedom are `(r - 1) * (c - 1)`. Expected-count diagnostics do not gate the test. Sparse tables are not reclassified as exact or as absent.
7. Adjustment stays unapplied. No strength label or significance flag is added. Non-finite results are not stored as estimates. A p-value of `0.0` from underflow may be stored.
8. `RelationshipFamily` includes Categorical × Categorical. Coverage reconciles. `RelationshipRecord` has a fifth typed variant. There is no universal record and no registry.
9. The product summary copies records without rereading the DataFrame or calling SciPy. No DataFrame, Series, Index, ndarray, Categorical, or SciPy result is retained. The four earlier families are unchanged. Boolean × Boolean stays specialized.
10. The full suite has only the known legacy PDF failure. [DEC-101](DECISIONS.md#dec-101) records the statistical contract, and the measured cost is recorded.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-030

TSK-030 calculates selected Categorical × Categorical and leaves bias-corrected association, exact and resampling tests, Categorical × Boolean, datetime relationships, multiple testing, and target analysis unselected. [DEC-101](DECISIONS.md#dec-101) records the contingency contract. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-031 was approved later and is recorded below. This section does not create a later task.

## TSK-031

Slice 031, relationship statistical consolidation. Approved 2026-10-04 after TSK-030. Completed the same day. No later slice is approved by this section.

Inspect the five calculated families as one statistical subsystem. Decide and apply the dataset-level multiple-testing policy. Audit availability and coverage. Do not add a relationship family, a target analysis, a renderer, a method registry, or a generic relationship superclass.

Acceptance checks:

1. The five calculated formulas, effects, intervals, and raw p-values stay intact. Family calculators do not run the dataset correction.
2. Benjamini–Hochberg adjusts one available primary p-value per calculated pair: Spearman, ANOVA, Welch, Fisher, or chi-square. Pearson stays raw. Unavailable p-values do not enter `m`.
3. Adjusted values are stored on the retained frequentist component before `RelationshipAnalysis` is frozen. The summary copies them and does not recompute them.
4. Adjustment is deterministic, including ties, zero, and one. Adjusted values stay on `[0, 1]` and are not below the raw value. There is no significance verdict.
5. Adding an eligible tested relationship can change adjusted p-values and does not change raw p-values or effects. An ineligible column does not change the correction family.
6. Calculated, unimplemented, and ineligible have the meanings in [DEC-102](DECISIONS.md#dec-102). Categorical × Boolean is one unimplemented family in either physical order. Datetime × Numeric and Datetime × Categorical stay unimplemented.
7. Pair counts still reconcile. `RelationshipFamily` still names only calculated families. No unavailability reason is renamed without a semantic error.
8. Records stay frozen. No source object is retained. Correction memory is linear in `m`, and 100,000 hypotheses are safe.
9. The full suite has only the known legacy PDF failure. [DEC-102](DECISIONS.md#dec-102) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-031

TSK-031 corrects the available primary relationship tests and classifies Categorical × Boolean as unimplemented. It leaves datetime methods, exact and resampling tests, robust alternatives, target analysis, and the rendered Relationships view unselected. [DEC-102](DECISIONS.md#dec-102) records the correction and coverage contract. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-032 was approved later and is recorded below. This section does not create a later task.

## TSK-032

Slice 032, target analysis foundation. Approved 2026-10-04 after TSK-031. Completed the same day. No later slice is approved by this section.

Project an explicitly requested target from analytical facts Pytics already computed. Do not fit a diagnostic model, rank columns, or recalculate relationships.

Acceptance checks:

1. Target analysis runs only for an explicit request. No request leaves `target_analysis` as `None`, and existing no-target results stay the same aside from that absence.
2. Identity is physical position. A unique label selects one column, including non-string and tuple labels. Duplicate labels raise. `TargetPosition` selects one of them. A missing label raises. Boolean labels are not integer labels. A bad selector does not return a dataset with target analysis disabled.
3. Semantic inference is reused unchanged. Structural confidence is kept. Candidate-derived selections do not gain confidence. Numeric `{0, 1}` stays Numeric.
4. Supported targets are Numeric, Categorical, and Boolean. Datetime, Timedelta, and Text are unsupported. Empty, Constant, and Identifier are ineligible. Unresolved columns stay unresolved.
5. Target population counts reconcile. Missing target rows are not dropped. Relationship populations stay on their records.
6. Numeric and Boolean descriptive facts are the retained objects. Categorical facts are the retained frequency counts. There is no imbalance verdict and no second descriptive scan.
7. Target links are the retained relationship records, in physical order, including raw and adjusted p-values. Unimplemented and ineligible pairs stay visible. Calculators and Benjamini–Hochberg are not run again. Orientation is recorded and statistics are not reversed.
8. The summary copies those facts and can be built after the calculators are patched to fail. It retains no source object. `profile` is not rewired.
9. The full suite has only the known legacy PDF failure. [DEC-103](DECISIONS.md#dec-103) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-032

TSK-032 projects an explicit target onto retained semantics, descriptive facts, and relationship records. It leaves the diagnostic model, leakage, problem types, a target-only multiple-testing family, class-level categorical counts, and the rendered Target view unselected. [DEC-103](DECISIONS.md#dec-103) records that boundary. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-033 was approved later and is recorded below. This section does not create a later task.

## TSK-033

Slice 033, target statistical analysis. Approved 2026-10-04 after TSK-032. Completed the same day. No later slice is approved by this section.

Give a supported target enough canonical descriptive truth to show what the target itself looks like. Put a missing generic categorical fact in the descriptive layer, then project it. Do not add a diagnostic model.

Acceptance checks:

1. A selected Categorical column receives an exact observed distribution whether or not it is the target. The collector lives with Numeric and Boolean descriptive analysis. There is no target-only categorical calculator.
2. Observed category values stay their own values. Pandas categorical vocabulary order is preserved, unused levels are omitted, and `ordered` is the physical dtype flag. Missing values are not levels. Counts sum to the non-missing population. Proportions use that population.
3. Category identity is the identity pandas already used. `1`, `True`, and `1.0` may already be one level. This slice does not invent a stronger equality universe. There is no cardinality cutoff. High-cardinality cost is measured.
4. A Categorical target reuses that descriptive object by identity. Numeric still reuses `NumericDescriptiveAnalysis`. Boolean still reuses `BooleanDescriptiveAnalysis`. The summary copies the frozen distribution and does not rescan.
5. Boolean and Categorical targets expose class counts and proportions, including ties. There is no balanced or imbalanced verdict and no imbalance threshold.
6. No classification or regression problem type is inferred. Numeric `{0, 1}` stays Numeric. No predictive model, feature ranking, or target-only test is added.
7. Relationship records and Benjamini–Hochberg adjusted p-values are unchanged. The projection does not recalculate them.
8. `target.py` stays one module. The aggregate categorical workaround is removed. The file is shorter, and a package split is not justified by this slice.
9. No DataFrame, Series, Index, ndarray, or callable is retained. The full suite has only the known legacy PDF failure. [DEC-104](DECISIONS.md#dec-104) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-033

TSK-033 retains the exact observed Categorical distribution and reuses it for an explicit Categorical target. It leaves the diagnostic model, leakage, problem types, imbalance verdicts, a target-only multiple-testing family, and the rendered Target view unselected. [DEC-104](DECISIONS.md#dec-104) records that boundary. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-034 was approved later and is recorded below. This section does not create a later task.

## TSK-034

Slice 034, lightweight target diagnostic model. Approved 2026-10-04 after TSK-033. Completed the same day. No later slice is approved by this section.

Add one simple untuned diagnostic model for an explicit target, evaluated out of sample against a naive baseline, with held-out permutation importance at original-column level. Do not tune, compare, select, or deploy models.

Acceptance checks:

1. Exactly one untuned estimator exists per predictive task: logistic regression for classification and ridge regression for regression. There is no search, leaderboard, model selection, ensemble, calibration, threshold choice, SHAP, export, prediction API, or AutoML vocabulary.
2. The semantic target type and the predictive task are separate. Boolean is binary classification. Categorical is binary or multiclass by observed class count. Numeric, including `{0, 1}`, is regression. Datetime, Timedelta, Text, Empty, Constant, Identifier, and unresolved targets have no task.
3. Model unavailability is a typed status: unsupported target, fewer than two classes, too many classes, too few modeling rows, no target variation, impossible stratified split, no eligible predictors, or a numerical failure. Arbitrary exceptions are not converted into a status.
4. Predictor eligibility is explicit for every other column. The target, Identifier, Empty, Constant, Datetime, Timedelta, Text, and unresolved columns are excluded with a reason. A same-type exact copy of the target is excluded. Training-row variation, one-hot width, and Numeric scale exclusions are recorded.
5. Evaluation is out of sample. One 25% holdout with an explicit retained seed is stratified per class for classification, with every class in both parts, and random for regression. Validation rows are never fitted.
6. Imputation, missing indicators, scaling, and one-hot vocabularies are fitted inside one pipeline on training rows only, and a test fails if they are fitted before the split. Unseen validation levels are handled. The source frame is not modified.
7. The model and its naive baseline use the same split. Classification reports ROC AUC or macro one-versus-rest ROC AUC, balanced accuracy, and log loss. Regression reports R², MAE, and RMSE. R² can be negative. An undefined metric is absent, not replaced. There is no predictability label.
8. Permutation importance uses validation rows only, permutes original input columns, keeps every repeat, keeps negative values, follows physical order, and is not described as causal, significant, or an effect.
9. Target analysis, relationship records, Benjamini–Hochberg adjusted p-values, and descriptive facts are unchanged, including when the model is unavailable. No-target analysis has no diagnostic.
10. No estimator, pipeline, frame, array, sparse matrix, callable, generator, or row index is retained. The summary can be built after fitting and source access are patched to fail. Results repeat for the same seed.
11. The full suite has only the known legacy PDF failure. scikit-learn is declared in `pyproject.toml`. [DEC-105](DECISIONS.md#dec-105) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-034

TSK-034 adds the lightweight target diagnostic model. The TSK-034b hardening pass then encodes the validation rows once for permutation importance and moves each input's encoded columns together, with the same values ([DEC-105](DECISIONS.md#dec-105), later update). It leaves leakage analysis, metric uncertainty, a public seed, sampling for very large frames, problem types beyond classification and regression, and the rendered Target view unselected. [DEC-105](DECISIONS.md#dec-105) records that boundary. The next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-035 was approved later and is recorded below. This section does not create a later task.

## TSK-035

Slice 035, target leakage evidence. Approved 2026-10-04 after TSK-034. Completed the same day. No later slice is approved by this section.

Record mechanical evidence of possible target duplication. Do not decide that a column leaks the target. Do not treat association as leakage.

Acceptance checks:

1. Leakage evidence is a separate target-level result. It does not fit a model, read relationship records, or assign a score, probability, or severity.
2. No target request does not run the pass. An unsupported, ineligible, or unresolved target returns that applicability and does not read predictor values.
3. An exact duplicate is a same-type Numeric, Boolean, or Categorical predictor equal to the target on every applicable row. Applicable rows are the finite Numeric rows or the non-missing Boolean or Categorical rows. Missing and non-finite predictor values, empty joint populations, disagreements, and different semantic types are distinct statuses. `1` and `True` are not duplicates across semantic types. Categorical value equality can treat `1`, `True`, and `1.0` as equal.
4. A Boolean or Categorical target records whether observed predictor values determine the observed classes. A missing predictor value is not a group. A missing target value is not a class. Conflicting groups, a constant joint target, and pure uniqueness are distinct from a repeated conflict-free mapping onto at least two classes. No percentage cutoff is used. The value map is not retained.
5. A unique Identifier is not promoted. The diagnostic still excludes it as Identifier. A repeated Identifier group that determines the classes keeps that mapping evidence and stays excluded from the model.
6. A Numeric target has exact-duplicate evidence only. An exact affine copy such as `y = 2x` is not a detected transform. A strong non-deterministic predictor, including one with a large effect, a tiny p-value, and positive diagnostic importance, is not given the repeated-mapping status.
7. Datetime columns are not read as temporal leakage. No missingness-indicator rule is added.
8. The diagnostic still excludes an exact copy, by consuming the leakage result, and does not recompute that comparison. A deterministic relabeling can still enter the model. Diagnostic metrics for a non-copy frame stay on the TSK-034 contract.
9. Target analysis, relationship records, and Benjamini–Hochberg values are unchanged. The summary copies the leakage result after source access is patched to fail. No DataFrame, Series, Index, ndarray, mapping, or callable is retained.
10. Functional-dependency counts are checked against an independent group-size calculation. The full suite has only the known legacy PDF failure. [DEC-106](DECISIONS.md#dec-106) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-035

TSK-035 records exact-duplicate and repeated deterministic-mapping evidence. It leaves contextual and temporal leakage, near-deterministic rules, numeric transforms, missingness-indicator rules, metric uncertainty, a public seed, sampling for very large frames, problem types beyond classification and regression, and the rendered Target view unselected. [DEC-106](DECISIONS.md#dec-106) records that boundary. At that point the next concrete implementation slice remained subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-036 was approved later and is recorded below. This section does not create a later task.

## TSK-036

Slice 036, univariate numeric anomaly analysis. Approved 2026-10-04 after TSK-035. Completed the same day. No later slice is approved by this section.

Record which finite numeric observations are unusual under Tukey's inner fence. Do not treat an unusual value as an error. Do not add a multivariate detector.

Acceptance checks:

1. An anomaly record is evidence under a stated method. It does not delete, repair, cap, impute, or label a value as wrong. There is no severity and no anomaly score.
2. The only method is Tukey's inner fence on a selected Numeric column. The fences use the retained Q1, Q3, and interquartile range. The coefficient is the fixed rational `3/2`. A value on the fence is not an anomaly.
3. Missing values are not anomalies. Positive and negative infinity are counted separately and are not IQR observations. A zero interquartile range does not classify differing values. There is no minimum sample size. A float fence that is not finite is unavailable. Integer fences are not classified through a collapsed float64 image.
4. Boolean, Categorical, Datetime, Timedelta, Identifier, Text, Empty, Constant, unresolved, and ambiguous columns are not fenced. A physical integer column selected as Identifier is not fenced. A Boolean minority class and a rare category are not relabeled as anomalies.
5. Row identity is the physical position. Duplicate and non-monotonic index labels do not change it. The same unusual value on several rows keeps one observation per row, with direction.
6. Every crossing is retained. Coverage separates eligible, analyzed, unavailable, ineligible, and profile-absent columns. A zero analyzed count is not a claim of zero anomalies.
7. `analyze_dataframe` produces the result with or without a target, and the two anomaly results are equal. The summary copies the retained result after source access and the collector are patched to fail.
8. No DataFrame, Series, Index, ndarray, NumPy scalar, or callable is retained. The source frame is unchanged.
9. Fence arithmetic and row positions agree with an independent calculation that uses the retained quartiles and does not call the anomaly collector.
10. Multivariate detection is not implemented. There is no detector registry and no scikit-learn import in the anomaly module.
11. Performance of the location pass, the retained size, and a high anomaly rate are measured. Nothing is silently truncated.
12. The full suite has only the known legacy PDF failure. [DEC-107](DECISIONS.md#dec-107) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-036

TSK-036 records Tukey fences for selected Numeric columns. It leaves multivariate anomaly detection, other univariate methods, categorical rarity as an anomaly method, datetime gaps, text-length anomalies, mode-dependent retention, and the rendered Anomalies view unselected. [DEC-107](DECISIONS.md#dec-107) records that boundary. The next concrete implementation slice remains subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-037 was approved later and is recorded below. This section does not create a later task.

## TSK-037

Slice 037, compare and drift foundation. Approved 2026-10-05 after TSK-036. Completed the same day. No later slice is approved by this section.

Record what changed between a reference DataFrame and a comparison DataFrame. Do not score drift or degradation. Do not add distribution, relationship, or target drift.

Acceptance checks:

1. The sides are reference and comparison. A directional change is comparison minus reference. There is no drift score, quality score, or severity.
2. `compare_dataframes` analyzes each frame independently and then compares those results. `compare_dataset_analyses` does not scan either frame. Public `pytics.compare` is unchanged.
3. Columns align by label identity and occurrence. Reordered columns stay matched. Both physical positions are retained. `1` does not match `True`. Duplicate labels are deterministic.
4. Physical dtype transitions and semantic transitions are separate. Confidence transitions are categorical.
5. Matched Numeric, Categorical, and Boolean columns compare retained descriptive facts. Identifier, Datetime, Timedelta, Text, Empty, Constant, unresolved columns, and semantic mismatches do not receive those specialized comparisons. The reason is visible.
6. Numeric differences do not collapse exact integers or store a non-finite float as a change. Categorical level partitions follow the existing category equality and are not quadratic. Boolean comparison is descriptive.
7. Rows are not paired by index. Duplicate groups are not matched across datasets. Missingness patterns, anomaly counts, relationship drift, and target drift are not compared.
8. A missing descriptive payload is an explicit status. It does not mean the column was unchanged. The retained result holds no DataFrame, Series, Index, or ndarray. The source frames are unchanged.
9. Alignment, schema transitions, numeric deltas, and categorical partitions agree with independent fixture calculations.
10. Naming a target does not change the comparison. High-cardinality category comparison and a wide reordered schema are measured. The cross pass does not rescan row values.
11. The full suite has only the known legacy PDF failure. [DEC-108](DECISIONS.md#dec-108) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-037

TSK-037 records column alignment and descriptive change for exactly two datasets. It leaves distribution drift, relationship drift, target drift, a rendered Compare view, and the public `compare()` replacement unselected. [DEC-108](DECISIONS.md#dec-108) records that boundary. The next concrete implementation slice remains subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). TSK-038 was approved later and is recorded below. This section does not create a later task.

## TSK-038

Slice 038, statistical distribution drift and compare architecture consolidation. Approved 2026-10-05 after TSK-037. Completed the same day. No later slice is approved by this section.

Add univariate distribution drift for matched Numeric, Categorical, and Boolean columns, effect first. Split the comparison module by ownership before adding it. Do not add relationship drift, target drift, Findings, or public `compare()`.

Acceptance checks:

1. A drift statistical method matrix is derived before implementation. Drift is not framed as degradation. There is no drift score, severity, threshold, or significance flag. Sides stay reference and comparison.
2. `compare.py` becomes a package with one direction of imports. TSK-037 values are unchanged, verified against the previous module.
3. Eligibility is the descriptive comparison's. Semantic mismatches, Identifier, Datetime, Timedelta, Text, Empty, and Constant are not coerced. Constant behavior is explicit.
4. Numeric drift uses finite non-missing values, keeps the KS distance with its location, the Wasserstein distance in column units, and the two-sample KS test with its exact or asymptotic computation. Ties are visible and the conservative p-value is documented.
5. Large integers, `uint64`, mixed integer and float storage, extreme floats, subnormals, and signed zero keep exact order. No NaN or infinity is stored as an effect.
6. Categorical drift uses the descriptive partition, total variation distance, chi-square homogeneity, and expected-count diagnostics. New and disappeared levels are evidence. Memory stays linear in the number of levels.
7. Boolean drift has a signed True-share difference and a Fisher exact test, with no redundant effect.
8. Missingness change stays separate from value drift. Components are independently available.
9. One available primary p-value per tested column enters one Benjamini–Hochberg family per comparison. Raw and adjusted values are distinct. Unavailable p-values do not enter.
10. Independent calculations verify KS, Wasserstein, the permutation p-value, TVD, the chi-square statistic, expected counts, Fisher, and Benjamini–Hochberg. Tiny effects with huge samples and large effects with small samples keep both facts.
11. Results are deterministic and source-independent after collection. Numeric, high-cardinality, and mixed-frame costs are measured separately from descriptive compare.
12. The full suite has only the known legacy PDF failure. [DEC-109](DECISIONS.md#dec-109) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-038

TSK-038 records univariate distribution drift between two datasets. It leaves relationship drift, target drift, constant-value comparison, mode-dependent drift inference, Findings, a rendered Compare view, and the public `compare()` replacement unselected. [DEC-109](DECISIONS.md#dec-109) records that boundary. TSK-039 was approved later and is recorded below. This section does not create a later task.

## TSK-039

Slice 039, relationship drift and target drift. Approved 2026-10-05 after TSK-038. Completed the same day. No later slice is approved by this section.

Compare retained relationship effects between two datasets, and project target change when a target is requested. Do not infer either change from significance transitions. Do not add Findings or public `compare()`.

Acceptance checks:

1. A relationship-drift method matrix and a target-drift decomposition are derived before implementation. Effect size stays ahead of any test. A significance transition is not an effect change.
2. Pairs align by the TSK-037 column identity. Duplicate labels and reordered columns keep one logical pair. A semantic-family change is not coerced onto one statistic.
3. Primary changes are Spearman rho, eta squared, Hedges' g, phi, and Cramér's V. Signed changes keep direction. Sign reversal is mechanical. An unavailable effect is not stored as zero change.
4. The only formal change test is a complementary Fisher z test of equal Pearson correlations, with an explicit null and assumptions. It is not a Spearman test and it is not adjusted. Distribution-drift Benjamini–Hochberg stays a separate family.
5. Categorical × Boolean and datetime relationships stay unimplemented. Category vocabulary and contingency shape are diagnostics, not gates and not proof of relationship change.
6. Target drift runs only for an explicit target. Distribution drift and relationship drift are projections. Diagnostic metric changes are descriptive and stop at a task or class-set change. Leakage transitions are mechanical statuses. Permutation-importance drift is not implemented.
7. A comparison without a target is unchanged by adding target support. No target, relationship, or concept-drift score is stored. No Findings and no renderer work are added. Legacy `pytics.compare` is unchanged.
8. Results are source-independent. The relationship cross-pass does not reread rows. Alignment is not quadratic in the number of relationship records.
9. Independent calculations verify each implemented family, including a significance transition with a nearly unchanged effect and a large effect change whose within-dataset p-values agree.
10. The full suite has only the known legacy PDF failure. [DEC-110](DECISIONS.md#dec-110) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-039

TSK-039 records relationship effect changes and a target projection for an explicit target. It leaves formal Spearman, eta-squared, Hedges' g, phi, and Cramér's V change tests, permutation-importance drift, temporal drift, Findings, a rendered Compare view, and the public `compare()` replacement unselected. [DEC-110](DECISIONS.md#dec-110) records that boundary. TSK-040 was approved later and is recorded below. This section does not create a later task.

## TSK-040

Slice 040, Findings Engine foundation. Approved 2026-10-05 after TSK-039. Completed the same day. No later slice is approved by this section.

Define what a Finding is before writing rules, then build a small, threshold-free v0.1 catalog over retained Profile and Compare results. Do not add a second statistical engine, recommendations, prose, a renderer, or public API changes.

Acceptance checks:

1. A Findings Epistemic Contract separates fact, evidence, finding, severity, priority, interpretation, verdict, and recommendation before implementation. Severity is not significance. Priority is not severity.
2. Findings read finished `DatasetAnalysis` and `DatasetComparison` values only. They do not read a DataFrame, compute a statistic, or read a p-value.
3. Identity is the code and a structured subject key, deterministic, independent of prose and severity, distinct for duplicate labels, and stable under column reordering and unrelated insertion.
4. Scopes, subjects, and evidence are typed. Each code has one scope, one subject type, and one evidence type. Invalid combinations are rejected.
5. Severity semantics and a per-code severity table are explicit. No severity follows from a p-value or an effect size. No practical threshold is introduced.
6. Ordering is lexicographic and deterministic: severity, code rank, subject order. There is no score.
7. The v0.1 catalog, the deferred catalog, and rejected candidates are explicit, each with a rationale.
8. Root conditions suppress derivative candidates deterministically, and suppressed candidates are inspectable. Empty never also produces Constant. No finding is emitted per row.
9. Tests cover identity, ordering, duplicate and adversarial labels, root conditions, target leakage deduplication, Compare suppression, significance independence, coverage arithmetic, source independence, and invalid frozen combinations.
10. The findings pass is benchmarked separately from analysis. The full suite has only the known legacy PDF failure, total coverage stays at least 97%, and [DEC-111](DECISIONS.md#dec-111) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-040

TSK-040 records the Findings Engine foundation and a threshold-free v0.1 catalog. It leaves threshold-based and effect-first findings for missingness, cardinality, anomalies, non-finite values, relationships, relationship change, distribution drift, and target predictability unselected, together with repeated-mapping transitions, findings configuration, user-facing level labels, renderer wording, a rendered Findings view, and the public result. [DEC-111](DECISIONS.md#dec-111) records that boundary. TSK-041 was approved later and is recorded below. This section does not create a later task.

## TSK-041

Slice 041, canonical column identity. Approved 2026-10-05 after TSK-040. Completed the same day. No later slice is approved by this section.

Make the existing label match key and occurrence count the one identity primitive, and use that key where a stored column label is compared. Do not change a statistical method, the findings catalog, drift, or the public API.

Acceptance checks:

1. A Numeric column whose label is float `NaN` completes `analyze_dataframe`, including anomaly location and a relationship with another eligible column.
2. Duplicate labels stay distinct by occurrence through analysis, relationships, Compare alignment, and Findings subjects.
3. `True` does not match `1`. `1` matches `1.0` by match key and keeps a separate occurrence. `None` does not match float `NaN`. `2**53 + 1` does not match `float(2**53 + 1)`.
4. Reordered columns stay aligned by match key plus occurrence.
5. Findings no longer imports private Compare identity helpers. The 11 codes, 2 suppression rules, and `pytics.findings/0.1` are unchanged.
6. The full suite has only the known legacy PDF failure, total coverage stays at least 97%, and [DEC-112](DECISIONS.md#dec-112) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## TSK-042

Slice 042, public result contract. Approved 2026-10-05 after TSK-041. Completed the same day. No later slice is approved by this section.

Add a read-only public facade over a finished profile or comparison. Do not render a notebook, terminal theme, HTML, Markdown, or PDF. Do not serialize a file. Do not change `pytics.profile` or `pytics.compare`. Do not migrate to Python 3.15.

Acceptance checks:

1. `profile_result` and `comparison_result` return `ProfileResult` and `ComparisonResult`.
2. The facade references the canonical analysis and does not recompute it or keep the DataFrame.
3. Variables, findings, relationships, and target are navigable, including duplicate, `NaN`, `True`/`1`, and `1`/`1.0` labels.
4. Target-not-requested is distinct from a requested target that is unsupported, unavailable, or unaligned.
5. Public equality is label-aware and has no timestamp or random id. Results are frozen.
6. The full suite has only the known legacy PDF failure, total coverage stays at least 97%, and [DEC-113](DECISIONS.md#dec-113) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## TSK-043

Slice 043, notebook landing view. Approved 2026-10-05 after TSK-042. Completed the same day. No later slice is approved by this section.

Render a compact notebook view of `ProfileResult` and `ComparisonResult`. Do not recompute statistics. Do not replace legacy `profile()` or `compare()`. Do not add charts, standalone HTML, PDF, Markdown, JSON, or a Python 3.15 migration.

Acceptance checks:

1. Displaying a profile or comparison result returns namespaced HTML through `_repr_html_`.
2. The renderer reads the public result and does not recompute analytical truth or create findings.
3. Profile and Compare landing views are different, bounded, and ordered by the canonical finding order.
4. User-controlled labels are escaped. Duplicate, `NaN`, `True`/`1`, and `1`/`1.0` labels stay distinguishable. Raw anomaly and category values are not on the landing view.
5. The view needs no JavaScript, CDN, notebook extension, or separate package. `import pytics` does not import it.
6. The full suite has only the known legacy PDF failure, total coverage stays at least 97%, and [DEC-114](DECISIONS.md#dec-114) records the contract.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## TSK-044

Slice 044, core semantic inference hardening. Approved 2026-10-05 after TSK-043. Completed the same day. No later slice is approved by this section.

Make ordinary, unambiguous string and object columns eligible for Categorical when the evidence supports a reused label vocabulary. Do not special-case a dataset. Do not clean, coerce, or mutate the source. Do not redesign the notebook. Do not parse mixed dates, currencies, or other dirty representations.

Acceptance checks:

1. A clean low-cardinality object or string column of repeated letter labels resolves as Categorical, including when some values are missing.
2. Two letter labels such as yes/no stay Categorical and do not become Boolean.
3. Continuous numeric columns stay Numeric. Low-cardinality integers, including `{0, 1}` and a three-valued year, stay Numeric.
4. Unique strings, near-unique strings, full-population UUID or hexadecimal syntax, prose, multi-word labels, and mixed date or currency text do not resolve as high-confidence Categorical.
5. Constant and Empty stay structural. The source Series and DataFrame are unchanged.
6. A mixed frame of numeric columns and newly categorical labels activates the existing Numeric × Categorical and Categorical × Categorical readers.
7. The full suite has only the known legacy PDF failure, total coverage stays at least 97%, and [DEC-115](DECISIONS.md#dec-115) records the rule.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## TSK-045

Slice 045, mixed representation and explainable semantic evidence. Approved 2026-10-05 after TSK-044. Completed the same day. No later slice is approved by this section.

Retain bounded representation evidence for heterogeneous string columns, distinguish absence of evidence from conflicting evidence, and support Categorical for reused short labels that include ordinary spaces and punctuation. Do not clean, coerce, or mutate the source. Do not select Datetime or Numeric from string shapes. Do not redesign the notebook. Do not change relationship methods.

Acceptance checks:

1. Reused short labels with internal spaces or a small punctuation set can resolve Categorical. The unpunctuated letter-label rule still applies to clean single-token labels.
2. Repeated long prose, unique strings, emails, URLs, UUIDs, and empty strings do not resolve Categorical. Padding and missing-like literals beside a label vocabulary are retained and do not by themselves block Categorical or count as semantic conflict. The original strings stay the category levels.
3. Date-like, quarter-year, numeric-like, currency-like, range, score, and unit-count strings are counted without conversion. A pure digit string is not an Excel date.
4. Missing-like literals stay literals and do not change pandas missing counts.
5. A column with no informative representation family and a column with conflicting families can both stay unresolved, and the retained mixture distinguishes them.
6. The source Series and DataFrame are unchanged. Column names are not evidence.
7. A penguins-shaped table stays 5 Numeric, 3 Categorical, 28 calculated relationships, and 0 ineligible.
8. The full suite has only the known legacy PDF failure, total coverage stays at least 97%, and [DEC-116](DECISIONS.md#dec-116) records the rule.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## TSK-046

Slice 046, legacy presentation and export cleanup. Approved 2026-10-05 after TSK-045. Completed the same day. No later slice is approved by this section.

Remove the 1.1.5 HTML and PDF renderer where ownership is limited to that renderer. Make `pytics.profile` and `pytics.compare` delegate to the existing result constructors. Do not build a replacement presentation. Do not change analytical behavior.

Acceptance checks:

1. `import pytics` and `from pytics.results import profile_result, comparison_result` do not import Plotly, Jinja2, xhtml2pdf, ReportLab, Kaleido, or Matplotlib.
2. `pytics.profile` and `pytics.compare` remain the only names in `pytics.__all__`. `profile(frame, *, target=None)` returns `ProfileResult`. `compare(reference, comparison, *, target=None)` returns `ComparisonResult`. Both match `profile_result` and `comparison_result`. `import pytics` does not load the analysis stack.
3. The notebook landing view, findings, and result objects are unchanged.
4. The penguins-shaped control and the messy-company control stay at their accepted counts.
5. The known `test_pdf_export` failure is gone because that test and the renderer were removed, not because the test was skipped.
6. [DEC-117](DECISIONS.md#dec-117) records the removal and the minimal top-level facade. [OPEN-004](DECISIONS.md#open-questions) stays open for configuration, semantic override, further parameters, and the transitional helpers.

Verification of these checks is recorded in [PROGRESS.md](PROGRESS.md).

## After TSK-046

TSK-046 removes the 1.1.5 HTML and PDF renderer and the dependencies that only it imported, and makes `profile()` and `compare()` the minimal top-level facade over the existing results. It leaves notebook redesign, charts, standalone HTML, Markdown export, PDF, JSON serialization, the configuration object, semantic-override representation, Text selection, and Python 3.15 migration unselected. [DEC-117](DECISIONS.md#dec-117) records that boundary. The next concrete implementation slice remains subject to a later human decision ([OPEN-037](DECISIONS.md#open-questions)). This section does not create a later task.
