# Progress

The project owner accepted the Slice 001 codebase on 2026-10-03 as the approved baseline for continued development. TSK-001, TSK-002, TSK-003, and TSK-004 are complete. They are foundation slices. No requirement below is completed.

This register is the trace from requirement to proof:

```text
requirement -> implementation task -> source files -> tests -> verification -> completion
```

Update implementation status only as part of an approved slice under [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md). Requirement wording may also change when an accepted decision changes the contract. That wording change is not implementation, and it must not mark a row Implemented. Establishing this project memory on 2026-10-03, and the architecture update the same day, were not implementation slices.

## States

| State | Meaning |
| --- | --- |
| Not started | The requirement as written is not implemented. A preparatory task may still name the row. |
| In force | A prohibition or hold that already binds. It is not built product behavior, and it is not a completed slice. |
| Scoped | A `TSK-###` names this requirement, and the slice is approved. Not used yet. |
| In progress | Implementation of an approved slice has started. Not used yet. |
| Implemented | Code and tests exist. Verification against the spec is not recorded. Not used yet. |
| Verified | Behavior was checked against the specification and the evidence is recorded in Verification. Not used yet. |
| Completed | Verified, and the progress row is filled in. Do not use this state on a requirement row without that evidence. Not used on a requirement row yet. The task log may mark a finished slice Completed. |

`In force` is reserved for exclusions and holds: REQ-P-03, REQ-F-03, REQ-I-05, REQ-I-06, REQ-K-03, REQ-L-06, REQ-N-04, REQ-T-03, REQ-T-04. Every other requirement row is Not started.

A completed task may name a requirement it only prepares or only partly covers. That requirement stays Not started until the requirement as written is implemented. TSK-001 is that case for REQ-S-01, REQ-S-02, and REQ-S-05. TSK-002 infers Empty and Constant only and collects four basic counts. TSK-003 infers Boolean only from a physical Boolean dtype, and only after Empty and Constant. TSK-004 infers Datetime only from a native or timezone-aware datetime dtype, and only after those three rules. Do not read these task links as completion of semantic inference, Boolean/Binary analysis, datetime analysis, or time-series analysis.

## Task log

| Task | Requirements | Scope | Acceptance criteria | State |
| --- | --- | --- | --- | --- |
| TSK-001 | REQ-S-01, REQ-S-02, REQ-S-05, foundation only | Slice 001. Physical dtype classification and typed semantic value models. No inference. | The 16 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-001). | Completed |
| TSK-002 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, Empty and Constant only. REQ-S-03 respected on this path. | Slice 002. Exact basic column evidence and Empty/Constant inference. No other semantic type. | The 24 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-002). | Completed |
| TSK-003 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, physical Boolean only. REQ-D-01 and REQ-D-03 only for a physical Boolean dtype. REQ-S-03 and REQ-D-02 respected on this path. | Slice 003. Empty, then Constant, then physical Boolean. No other Boolean representation. | The 30 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-003). | Completed |
| TSK-004 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, physical Datetime only. REQ-E-03 and REQ-E-04 respected on this path. REQ-S-03 respected on this path. | Slice 004. Empty, then Constant, then physical Boolean, then physical Datetime. No string parsing and no time-series analysis. | The 42 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-004). | Completed |

### TSK-001 — Slice 001, core semantic foundation

Approved in the Slice 001 session on 2026-10-03, before the code was written. This record was written after verification in that same session.

Decisions recorded with the slice: [DEC-062](DECISIONS.md#dec-062), [DEC-063](DECISIONS.md#dec-063). DEC-063 resolves [OPEN-040](DECISIONS.md#open-040).

The slice does not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), or [OPEN-045](DECISIONS.md#open-questions). `SemanticType` has no ordinal member. `subtype` is an optional string label, not a taxonomy. The internal package path below is not a frozen layout.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/__init__.py` | Marks the internal package. Does not export it from top-level `pytics`. |
| `src/pytics/semantics/physical.py` | Physical dtype families, the inspectable `PhysicalDtype` value, and objective classification. |
| `src/pytics/semantics/interpretation.py` | Semantic type, confidence, inference source, evidence, alternatives, and interpretation values. |

Not modified: `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`.

Tests: `tests/test_semantic_foundation.py`.

What was implemented:

- objective physical families for boolean, integer, floating, complex, string, object, categorical, datetime, timezone-aware datetime, timedelta, period, interval, and an other/extension fallback;
- the minimum semantic vocabulary, without inferring it from values;
- confidence limited to High, Medium, and Low;
- inference source for inferred, directly supported by physical dtype, and explicitly configured;
- a one-statement evidence value and an immutable interpretation value that can carry type, an open subtype label, confidence, evidence, alternatives, source, and physical dtype;
- `PhysicalDtype.categorical_ordered`, which copies `CategoricalDtype.ordered`. That flag is physical metadata. It is not an ordinal semantic type.

Internal names, not a public schema: `PhysicalDtypeFamily`, `PhysicalDtype`, `classify_physical_dtype`, `SemanticType`, `Confidence`, `InferenceSource`, `SemanticEvidence`, `SemanticAlternative`, and `SemanticInterpretation`. `InferenceSource` members are `INFERRED`, `PHYSICAL_DTYPE`, and `USER_CONFIGURED`. `SemanticType.BOOLEAN` is the Boolean/Binary family. `SemanticType.TEXT` is the Text/String family. `PhysicalDtypeFamily.DATETIME_TZ_AWARE` is timezone-aware datetime storage.

The classifier accepts a Series, a dtype, or a dtype alias. On a Series it reads `.dtype` only. Family checks use `CategoricalDtype`, `PeriodDtype`, `IntervalDtype`, and `DatetimeTZDtype`, then `is_datetime64_any_dtype`, `is_timedelta64_dtype`, `is_bool_dtype`, `is_complex_dtype`, `is_integer_dtype`, `is_float_dtype`, `StringDtype`, `is_object_dtype`, and `is_string_dtype`. Object dtype stays object even when pandas reports it as a string dtype. A dtype alias is resolved with `pandas_dtype`. An unrecognized extension dtype is `OTHER`. Recognized extension dtypes, such as nullable integers and sparse floats, keep the family pandas assigns them. The classifier does not look at values, uniqueness, missingness, or column names.

What was not implemented: semantic inference, thresholds, observed-characteristic collection, ordinal storage, a subtype taxonomy, statistics, findings, rendering, the method registry, and any change to `profile()` or `compare()`.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3:

| Command | Result |
| --- | --- |
| `pytest tests/test_semantic_foundation.py -q` | 43 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 62 passed, 1 failed |

The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. The other 19 tests in `tests/test_profiler.py` passed. No previously passing test failed. New semantic modules were fully covered on the full run. Total coverage on that run was 96%. The briefing baseline of 92% was the 1.1.5 suite and was not treated as a regression.

All 16 acceptance criteria in the implementation plan passed. See that list for the checks. Dependency files were not changed.

### TSK-002 — Slice 002, basic column evidence and Empty/Constant inference

The project owner accepted the current Slice 001 code under `src/pytics/semantics/` and `tests/test_semantic_foundation.py` as the development baseline before this slice. Those files were not rewritten.

Approved in the Slice 002 session on 2026-10-03. This record was written after verification in that same session.

No new `DEC-###`. [OPEN-044](DECISIONS.md#open-questions) stays open. This slice introduces no inference threshold. Internal names below are not a public schema. They do not resolve [OPEN-045](DECISIONS.md#open-questions) or [OPEN-004](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/column_evidence.py` | Frozen basic counts and exact collection from one Series. |
| `src/pytics/semantics/empty_constant.py` | Empty, then Constant, or no interpretation. |

Not modified: `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`.

Tests: `tests/test_empty_constant.py`. `tests/test_semantic_foundation.py` was not changed.

Evidence collection is separate from interpretation. `interpret_empty_or_constant` reuses `classify_physical_dtype`, collects `BasicColumnEvidence` once, and applies precedence. There is no rule class, registry, or general inference function with branches for later semantic types.

`BasicColumnEvidence` is a frozen dataclass. Fields are `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing`, stored as Python `int`. Invariants are `n_total >= 0`, `0 <= n_missing <= n_total`, `n_non_missing == n_total - n_missing`, and `0 <= n_unique_non_missing <= n_non_missing`. The object does not store a semantic type, confidence, threshold, the constant value, or anything for rendering. The four counts are exact. There is no sampling.

Collection uses `len(series)`, `Series.isna().sum()`, and `Series.nunique(dropna=True)`. It does not copy, mutate, or convert the Series. `"?"`, `"N/A"`, `""`, `"null"`, and `"NA"` remain observed values unless pandas already treats them as missing. `None`, `numpy.nan`, `pandas.NA`, and `pandas.NaT` count as missing because pandas does. Unhashable non-missing values have no pandas distinct-count. Collection raises `TypeError` and does not stringify them.

Precedence is: if `n_non_missing == 0`, Empty; else if `n_unique_non_missing == 1`, Constant; else `None`. `None` means these rules produced no interpretation. `SemanticType` has no unknown member, and this slice did not add one. The count invariant already makes the two positive conditions mutually exclusive. Empty is still tested first.

An Empty or Constant result is a Slice 001 `SemanticInterpretation`. Source is `InferenceSource.INFERRED`. Confidence is `Confidence.HIGH`. [DEC-042](DECISIONS.md#dec-042) allows only High, Medium, and Low. [DEC-043](DECISIONS.md#dec-043) uses Medium or Low when a reading is uncertain. These two rules are the [DEC-046](DECISIONS.md#dec-046) definitions applied to exact full-column counts, with no sampling and no competing candidate from this slice, so the existing High level is used. That is not a numeric score and not a new scoring policy. Evidence is one statement: `0 non-missing observations out of {n_total}`, or `1 distinct non-missing value among {n_non_missing} non-missing observations out of {n_total}`. Subtype is unset. Alternatives are empty, so a constant boolean is not also offered as Boolean. Physical dtype is the Slice 001 value, including `categorical_ordered`. An ordered categorical is not inferred as ordinal.

Empty and Constant are not yet emitted as dataset-level facts. REQ-A-06 stays Not started.

Left open, and not decided in this slice: inference thresholds ([OPEN-044](DECISIONS.md#open-questions)); the subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); missing-like literal reporting (REQ-H-04); dataset-level empty and constant facts (REQ-A-06); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

What was not implemented: Boolean/Binary, Numeric, Continuous/Discrete, Identifier, Categorical, Text, string patterns, datetime-from-strings, Timedelta analysis, Ordinal, cardinality or near-constant or identifier thresholds, missing-like literal reporting, sampling, relationships, findings, target analysis, anomalies, compare/drift, HTML, PDF, configuration, and a public result API.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice, `pytest tests/test_semantic_foundation.py -q` was 43 passed and `pytest tests/test_profiler.py -q` was 19 passed, 1 failed. The repository had no tracked modifications. Untracked items were `docs/pytics-2/`, `src/pytics/semantics/`, and `tests/test_semantic_foundation.py`.

| Command | Result |
| --- | --- |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py -q` | 72 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 91 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is 29 Slice 002 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules were fully covered on the full run. Total coverage on that run was 96%.

All 24 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-003 — Slice 003, physical Boolean inference and semantic precedence

The committed Slice 001 and Slice 002 code was the development baseline. `git status` was clean before this slice. Slice 001 and Slice 002 files were not rewritten.

Approved in the Slice 003 session on 2026-10-03. This record was written after verification in that same session.

No new `DEC-###`. [OPEN-044](DECISIONS.md#open-questions) stays open. This slice introduces no inference threshold and no numeric confidence score. Internal names below are not a public schema. They do not resolve [OPEN-045](DECISIONS.md#open-questions), [OPEN-004](DECISIONS.md#open-questions), or [OPEN-014](DECISIONS.md#open-questions). `SemanticType.BOOLEAN` remains the Boolean/Binary family. No binary member was added.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/physical_boolean.py` | Empty, then Constant, then physical Boolean, or no interpretation. |

Not modified: `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 and Slice 002 tests were not modified.

Tests: `tests/test_physical_boolean.py`.

`interpret_empty_constant_or_physical_boolean` classifies the physical dtype once and collects `BasicColumnEvidence` once. `interpret_empty_constant_or_physical_boolean_from_evidence` then calls `interpret_empty_or_constant_from_evidence`. It does not call `isna` or `nunique` again. There is no rule class, registry, or priority manager. `interpret_empty_or_constant` is unchanged: a non-constant `bool` Series is still `None` from that function.

Precedence is Empty, then Constant, then physical Boolean, then no interpretation. `None` means this chain produced no interpretation. `SemanticType` has no unknown member, and this slice did not add one.

A Boolean result requires all three of: not Empty, not Constant, and `PhysicalDtypeFamily.BOOLEAN`. Native `bool` and nullable pandas `boolean` are that family. Confidence is `Confidence.HIGH`, because the physical dtype is direct evidence ([DEC-047](DECISIONS.md#dec-047)), not because a score was introduced. Source is `InferenceSource.PHYSICAL_DTYPE`. Empty and Constant stay `InferenceSource.INFERRED`, including when the physical family is Boolean. Evidence is one statement: `physical dtype is boolean`. Subtype is unset. Alternatives are empty, so Boolean is not also offered on a constant or empty Boolean column. The Slice 001 physical dtype is retained, including `dtype_name`.

Object storage of Python `True` and `False` stays object and gets no interpretation. A categorical of `True` and `False` stays categorical and gets no interpretation, including when `categorical_ordered` is true. That flag is not an ordinal semantic type. `{0, 1}`, `yes`/`no`, and `true`/`false` strings get no interpretation. A column name is not used.

The Series is not copied, coerced, or otherwise modified.

Boolean is not yet emitted as a dataset-level fact. REQ-A-06 stays Not started. REQ-D-01 stays Not started because `{0, 1}` and Boolean-like strings are not implemented.

Left open, and not decided in this slice: inference thresholds ([OPEN-044](DECISIONS.md#open-questions)); Boolean subtypes and the rest of the subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); numeric `{0, 1}`, Boolean-like strings, binary categoricals, and other two-valued representations; the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

What was not implemented: Boolean inference from `{0, 1}`, from Boolean-like strings, from binary categoricals, or from any other two-valued representation; Numeric, Continuous/Discrete, Identifier, Categorical, Text, datetime semantic inference, timedelta semantic inference, ordinal storage, thresholds, sampling, missing-like literal reporting, near-constant, high cardinality, relationships, findings, target analysis, anomalies, compare/drift, HTML, PDF, configuration, and a public result API.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean. `pytest tests/test_semantic_foundation.py -q` was 43 passed, `pytest tests/test_empty_constant.py -q` was 29 passed, and `pytest tests/test_profiler.py -q` was 19 passed, 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_physical_boolean.py -q` | 22 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py -q` | 94 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 113 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is 22 Slice 003 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules were fully covered on the full run. Total coverage on that run was 96%.

All 30 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-004 — Slice 004, physical Datetime inference and scalable semantic composition

The committed Slice 001, Slice 002, and Slice 003 code was the development baseline. `git status` was clean, and `main` matched `origin/main`, before this slice. Slice 001, Slice 002, and Slice 003 files were not rewritten.

Approved in the Slice 004 session on 2026-10-03. This record was written after verification in that same session.

No new `DEC-###`. [OPEN-044](DECISIONS.md#open-questions) stays open. [OPEN-045](DECISIONS.md#open-questions) stays open. This slice introduces no inference threshold and no numeric confidence score. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), or [OPEN-037](DECISIONS.md#open-questions). `SemanticType.DATETIME` is the only datetime semantic type. Timezone-aware storage is not a second semantic type.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/physical_datetime.py` | Empty, then Constant, then physical Boolean, then physical Datetime, or no interpretation. |

Not modified: `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001, Slice 002, and Slice 003 tests were not modified.

Tests: `tests/test_physical_datetime.py`.

`interpret_series_precedence` classifies the physical dtype once and collects `BasicColumnEvidence` once. `interpret_precedence_from_evidence` calls `interpret_empty_constant_or_physical_boolean_from_evidence`. Only when that returns no reading does it apply the datetime rule. It does not call `isna` or `nunique` again, and it does not classify again. There is no rule class, registry, or priority manager.

The Slice 003 function is unchanged. A non-empty, non-constant datetime Series is still `None` from `interpret_empty_constant_or_physical_boolean`. The new entry point is not named by listing every rule. Extending the Boolean function's name would have produced a longer chain name, and putting Datetime inside that function would have made its name false. One successor function is the smaller composition. It is not a framework, and the file location does not resolve [OPEN-045](DECISIONS.md#open-questions).

Precedence is Empty, then Constant, then physical Boolean, then physical Datetime, then no interpretation. `None` means this chain produced no interpretation. `SemanticType` has no unknown member, and this slice did not add one.

A Datetime result requires all of: not Empty, not Constant, not the physical Boolean rule, and `PhysicalDtypeFamily.DATETIME` or `PhysicalDtypeFamily.DATETIME_TZ_AWARE`. Both families use `SemanticType.DATETIME`. Confidence is `Confidence.HIGH`, because the physical dtype is direct evidence ([DEC-050](DECISIONS.md#dec-050)), not because a score was introduced. Source is `InferenceSource.PHYSICAL_DTYPE`. Empty and Constant stay `InferenceSource.INFERRED`, including when the physical family is datetime. Evidence is one statement: `physical dtype is datetime`, or `physical dtype is timezone-aware datetime`. Subtype is unset. Alternatives are empty. The Slice 001 physical dtype is retained, including `dtype_name` and the timezone-aware family. `PhysicalDtype` was not given timezone metadata. Inference does not remove timezone information, convert timezone-aware values to naive values, normalize timezones, or convert values to UTC. It does not call `pd.to_datetime` on source data. It does not depend on a particular resolution such as nanoseconds.

An all-`NaT` datetime Series and a zero-length datetime Series stay Empty. A repeated timestamp, including one distinct timestamp plus `NaT`, stays Constant. The physical family remains datetime on those readings.

Date-like strings stay strings and get no Datetime reading. A one-value datetime-like string stays Constant. An object Series of Python `datetime` or `Timestamp` values stays object and gets no interpretation. Integer and floating Unix-like values get no interpretation. A categorical of timestamps stays categorical and gets no interpretation. `PhysicalDtypeFamily.TIMEDELTA` gets no interpretation, and `SemanticType.TIMEDELTA` is not inferred. `PhysicalDtypeFamily.PERIOD` gets no interpretation. A column name is not used. A Datetime reading does not record frequency, regularity, monotonicity, gaps, calendar pattern, trend, seasonality, or autocorrelation, and it is not a time-series structure.

The Series is not copied, coerced, or otherwise modified.

Datetime is not yet emitted as a dataset-level fact. REQ-A-06 stays Not started. REQ-E-01 and REQ-E-02 stay Not started. REQ-S-07 stays Not started. String-to-datetime recognition stays Not started.

Left open, and not decided in this slice: inference thresholds ([OPEN-044](DECISIONS.md#open-questions)); the subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); the order of later slices ([OPEN-037](DECISIONS.md#open-questions)); string-to-datetime inference; object-datetime heuristics; Unix-timestamp detection; period semantics; timedelta semantic inference; and time-series analysis ([OPEN-020](DECISIONS.md#open-questions)).

What was not implemented: Timedelta semantic inference; period semantic inference; datetime string parsing; object datetime heuristics; Unix timestamp detection; date-format detection; timezone normalization; datetime resolution analysis; time-series inference; frequency detection; temporal gaps; calendar patterns; trend; seasonality; autocorrelation; Numeric; Continuous/Discrete; Identifier; Categorical; Text; ordinal semantics; `{0, 1}` Boolean; Boolean-like strings; binary categorical semantics; thresholds; sampling; findings; relationships; target; anomalies; compare/drift; HTML; PDF; and a public result API.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main`. `pytest tests/test_semantic_foundation.py -q` was 43 passed, `pytest tests/test_empty_constant.py -q` was 29 passed, `pytest tests/test_physical_boolean.py -q` was 22 passed, and `pytest tests/test_profiler.py -q` was 19 passed, 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_physical_datetime.py -q` | 24 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py -q` | 118 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 137 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is 24 Slice 004 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules were fully covered on the full run. Total coverage on that run was 97%.

All 42 acceptance criteria in the implementation plan passed. Dependency files were not changed.

## Requirement register

Source files and tests stay empty on a requirement row until that requirement is implemented. A preparatory note may appear in Verification. Do not point these columns at `src/pytics/` merely because 1.1.5 happens to touch a similar topic.

| ID | Requirement | State | Task | Source files | Tests | Verification | Spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-P-01 | Serve the six purposes above for a professional audience. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-02 | Treat understanding as the goal. Do not optimize predictive performance. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-03 | Stay outside the non-goals listed above. | In force | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-04 | Report observations and evidence. Do not prescribe actions. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-05 | Design for professionals, without beginner clutter, and keep methods and assumptions inspectable. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-06 | Implement the core analytical API against pandas DataFrames only. Do not load files or parse CSV, Parquet, encodings, or remote paths in core. Do not add a multi-engine dataframe abstraction at this stage. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-07 | Do not produce a composite data-quality score. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-08 | Provide statistical depth beyond a `DataFrame.describe()` wrapper. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-09 | Every chart must answer an analytical question. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-10 | Lead inferential presentation with effect size, uncertainty, and context. Do not lead with the p-value, use significance stars, or treat a tiny p-value as inherent importance. Where correction applies, distinguish raw and adjusted p-values. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-11 | Allow Bayesian analyses that help understanding, under the transparency rules above, without promising universal Bayesian coverage and without Bayesian predictive optimization. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-12 | Reproduce results for the same data, configuration, version, and seed where reasonably possible, and record metadata for nondeterministic methods. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-13 | `profile` performs analysis without dumping charts into the notebook, and a plain notebook representation stays compact. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-14 | Expose structured results programmatically, and render HTML and PDF through explicit presentation entry points. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-15 | Default to zero configuration, and avoid a large public keyword-argument surface. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-16 | Provide quick, standard, and deep analysis modes. Standard is the intended default. Exact contents and thresholds are not frozen. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-S-01 | Infer a semantic type. The minimum concepts are Numeric, Categorical, Boolean/Binary, Text/String, Datetime, Timedelta, Identifier, Constant, and Empty. Empty and Constant are also dataset facts. | Not started | TSK-001, TSK-002, TSK-003, TSK-004 | — | — | Not completed. TSK-001 can represent the minimum types. TSK-002 infers Empty and Constant only. TSK-003 also infers Boolean from a physical Boolean dtype after those two rules. TSK-004 also infers Datetime from a native or timezone-aware datetime dtype after those three rules. It does not infer Datetime from strings or other storage, Timedelta, the other minimum types, other Boolean representations, or dataset facts. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-02 | Retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source of interpretation. User-facing confidence is High, Medium, or Low, with concrete evidence. Do not present pseudo-precise confidence. | Not started | TSK-001, TSK-002, TSK-003, TSK-004 | — | — | Not completed. TSK-001 can store a reading. TSK-002 stores type, High confidence, one evidence statement, inferred source, and physical dtype for Empty and Constant only. TSK-003 does the same for physical Boolean, with source physical dtype. TSK-004 does the same for physical Datetime. Timezone-aware storage keeps its own evidence statement and its physical family. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-03 | Do not silently clean, repair, coerce, or mutate the original DataFrame. Preserve the distinction between source representation and analytical interpretation. Pattern detection must not rewrite the source Series. | Not started | TSK-002, TSK-003, TSK-004 | — | — | Not completed. TSK-002, TSK-003, and TSK-004 do not mutate the Series they read. TSK-002 does not treat missing-like strings as missing. TSK-004 does not parse strings or coerce them to datetime. The requirement covers the product, not only these paths. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-04 | Make inference evidence-driven and transparent, and expose uncertainty. A column name may support an inference and must not determine semantic type by itself. | Not started | TSK-002, TSK-003, TSK-004 | — | — | Not completed. TSK-002 decides Empty and Constant from basic counts and does not use the column name. TSK-003 decides physical Boolean from the dtype family after those counts, and does not use the column name or cardinality. TSK-004 decides physical Datetime from the dtype family after those rules, and does not use the column name or parse values. It does not implement the rest of evidence-driven inference. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-05 | Distinguish physical dtype, observed characteristics, and semantic interpretation. Keep the original physical dtype inspectable. | Not started | TSK-001, TSK-002, TSK-003, TSK-004 | — | — | Not completed. TSK-001 classifies physical dtype. TSK-002 collects four exact basic counts and keeps that physical dtype on Empty and Constant interpretations. TSK-003 keeps it on physical Boolean interpretations. TSK-004 keeps it on physical Datetime interpretations, including the timezone-aware family. It does not collect the rest of the observed characteristics. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-06 | Treat explicit per-variable semantic configuration as a first-class capability. User intent normally takes precedence. If a configured interpretation cannot be meaningfully applied, report the conflict instead of silently coercing. The exact API is not frozen. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-07 | Give Timedelta dedicated duration analysis that preserves duration semantics and readable units. Do not present user-facing timedelta results as raw nanoseconds. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-08 | Do not infer ordinal ordering from category labels. Accept ordinal semantics only when the user configures them or the source explicitly represents order. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-09 | Let semantic interpretation guide which analyses are meaningful. The specification examples are direction, not a closed eligibility matrix. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-01 | Rows, columns, cells, and dataset dimensions. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-02 | Memory usage and memory per row. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-03 | Missingness, complete rows, and incomplete rows. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-04 | Duplicate rows and unique rows. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-05 | Physical dtype composition and semantic type composition. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-06 | Constant columns, near-constant columns, empty columns, identifier candidates, and high-cardinality columns. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-07 | Infinities. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-08 | Relevant computational-analysis metadata. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-01 | Count, missing, distinct, zeros, negatives, infinities, min, max, range, and sum. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-02 | Mean, median, mode where meaningful, variance, standard deviation, IQR, MAD, coefficient of variation, and quantiles or percentiles. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-03 | Skewness and kurtosis. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-04 | Robust statistics. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-05 | Distribution analysis, and normality or other distribution diagnostics where responsible. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-06 | Univariate outlier signals. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-01 | Count, missing, distinct, and cardinality ratio. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-02 | Mode, mode frequency, top categories, rare categories, and bottom categories where useful. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-03 | Entropy, normalized entropy, and concentration. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-04 | Singleton categories and rare-category percentage. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-05 | Frequency distribution. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-06 | Low, medium, and high cardinality characteristics. Thresholds should ultimately be configurable. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-07 | Do not produce meaningless charts of thousands of categories. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-01 | Support conservative inference of binary-like values where the evidence justifies it. Examples may include true/false, and possibly 0/1 or yes/no. | Not started | TSK-003 | — | — | Not completed. TSK-003 interprets a non-empty, non-constant physical pandas Boolean dtype as Boolean. It does not infer Boolean from true/false strings, `{0, 1}`, or yes/no. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-02 | Do not treat binary cardinality as Boolean meaning. Do not treat every {0, 1} column as Boolean. Keep arbitrary two-category variables categorical. | Not started | TSK-003 | — | — | Not completed. TSK-003 does not treat two distinct values, `{0, 1}`, Boolean-like strings, or categorical booleans as Boolean. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-03 | Record confidence and reason for a boolean or binary inference. | Not started | TSK-003 | — | — | Not completed. TSK-003 records High confidence and one factual evidence statement for a physical Boolean reading. It does not cover other boolean or binary readings. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-01 | Earliest, latest, range or span, missingness, distinct values, duplicate timestamps, timezone, and inferred resolution. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-02 | Monotonicity, gaps, irregular intervals, frequency, relevant calendar distributions, and time-structure signals. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-03 | Distinguish a column that contains dates from an actual time-series structure. | Not started | TSK-004 | — | — | Not completed. TSK-004 can read a physical datetime dtype as Datetime and does not treat that reading as a time series. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-04 | Do not indiscriminately run deeper time-series diagnostics on every datetime column. | Not started | TSK-004 | — | — | Not completed. TSK-004 does not run monotonicity, frequency, gap, calendar, trend, seasonality, or autocorrelation analysis. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-01 | Distinguish the string roles listed above. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-02 | Text diagnostics covering count, missing, distinct, empty strings, whitespace-only values, length statistics and distribution, word counts, leading or trailing whitespace, line breaks, Unicode or non-ASCII characteristics, pattern consistency, and duplicate text. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-03 | Pytics core must not become a full NLP platform. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-01 | Treat Identifier as a first-class semantic concept. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-02 | Expose the evidence and reasoning for identifier detection. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-03 | Normally exclude identifiers from ordinary correlation, diagnostic target modeling, and ordinary multivariate anomaly modeling, unless explicitly configured otherwise. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-01 | Report dataset-level, variable-level, and row-level missingness. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-02 | Report missingness patterns and co-missingness. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-03 | Report relationships between missingness and other variables. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-04 | Report missing-like literals such as `""`, whitespace, `"N/A"`, `"null"`, and `"?"`. Do not silently rewrite them as missing data. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-05 | Keep MCAR, MAR, and MNAR diagnostics methodologically conservative. Do not claim that missingness is definitively MAR or MNAR when the observed data cannot support that conclusion. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-01 | Report exact duplicate rows and duplicate groups. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-02 | Report duplicate identifiers. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-03 | Report conflicting duplicates. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-04 | Support controlled partial-duplicate analysis. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-05 | Do not run uncontrolled combinatorial searches over all possible column combinations. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-06 | Fuzzy or near-duplicate analysis is not a default core operation. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-01 | Treat outliers and anomalies as observations to understand, not as errors to delete, and do not automatically recommend deletion. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-02 | Support robust univariate outlier analysis. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-03 | Support multivariate anomaly detection. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-04 | Multivariate anomaly analysis should eventually provide explainability or context where possible. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-01 | Relationship analysis must be type-aware. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-02 | The capability categories listed above are in scope, under `REQ-P-10` and `REQ-P-11`. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-03 | Do not hard-code a final method catalog before that catalog is decided. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-04 | Separate a relationship into description, effect, uncertainty, frequentist inference, Bayesian inference where appropriate, diagnostics, and method metadata. Do not reduce a relationship to a p-value. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-05 | Treat statistical assumptions as diagnostic context. Do not invalidate a method solely because an assumption test is significant. Keep method selection explainable. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-01 | Where a target is supplied, recognize target semantics and problem type where possible. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-02 | Target analysis may cover distribution, imbalance, feature-target relationships, effect sizes, and inference. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-03 | Surface potential target leakage as evidence or signals. Do not assert leakage without a sufficient basis. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-04 | Pytics may fit one lightweight, untuned diagnostic model to expose multivariate feature-target relationships. The model is for understanding data architecture, not for predictive optimization. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-05 | Validate the diagnostic model with responsible holdout or cross-validation. Do not evaluate it only on the observations used to fit it. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-06 | Do not add hyperparameter search, model leaderboards, model competitions, automated tuning, or deployment workflows. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-07 | Use held-out permutation importance as the primary feature-importance direction. Report spread across permutations where applicable. Warn that correlated predictors can share or obscure that importance. Do not present it as causal importance. The estimator family is not chosen. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-01 | `compare()` is a first-class capability and uses the same product language as profile. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-02 | Explain what changed. Do not merely place two profile reports side by side. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-03 | Report drift neutrally as observed or material change. Do not automatically label it bad. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-04 | The change types listed above are the destination scope of comparison. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-01 | Findings are structured objects traceable to metric, value, threshold where relevant, method, variables, and source analysis. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-02 | Rendered finding text presents the structured finding. It is not the source of the finding. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-03 | Core findings must be producible without an LLM. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-04 | Do not use gamified or sensational finding labels. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-IA-01 | Use a persistent left sidebar on desktop, as navigation only. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-02 | Profile navigation follows the structure above, omitting items that do not apply. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-03 | Compare navigation follows the structure above, omitting items that do not apply. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-04 | Profile and Compare should feel like two modes of the same product. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-05 | Overview answers those four questions and does not show a composite quality score. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-06 | The Findings view links each finding back to its evidence. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-07 | Variables begin as a searchable, sortable table, with type-aware detail under progressive disclosure. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-08 | Missing is its own view for the missing-data contract. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-09 | Duplicates is its own view for the duplicate contract. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-10 | Anomalies keeps univariate and multivariate perspectives separate. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-11 | Relationships are explored primarily as a table, with detail for statistics, uncertainty, inference, visualization, and methods as appropriate. A matrix is an additional view, not a replacement for the table. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-12 | Show Target only when target analysis exists. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-13 | Show Time Series only when genuine time structure is inferred or explicitly configured. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-14 | Methods is a technical appendix for methods, assumptions, parameters, priors, sampling, and related detail. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-15 | Report Info shows the metadata listed above. Sampling must never be hidden. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-16 | Provide an About destination. Leave narrative, motivation, and contact details empty until they are supplied. License and version may be taken from project metadata that already exists. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-17 | Structure the report so a reader can observe, then investigate, then verify. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-18 | The report should feel modern, restrained, professional, clean, typographically strong, spacious, and analytical. Use color sparingly and semantically. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-19 | HTML is the canonical interactive report. PDF is the professional static, shareable representation. Light theme is the primary design reference. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-20 | The comparison overview emphasizes what changed. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-T-01 | Analytical code must not directly generate HTML. An analyzer takes inputs such as a series, semantic schema, and configuration, and returns a structured result. | Not started | — | — | — | — | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |
| REQ-T-02 | HTML and PDF renderers consume structured result models. They are not the place where statistics are defined. | Not started | — | — | — | — | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |
| REQ-T-03 | The method-registry concept is accepted. Do not implement the registry until its schema and API are decided. | In force | — | — | — | — | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |
| REQ-T-04 | Do not install or pin a Pytics 2.0 dependency lock. Candidate directions from the ecosystem review are not that lock. | In force | — | — | — | — | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |
| REQ-T-05 | Reuse one statistical layer for general relationships, target analysis, missingness relationships, dataset comparison, and drift wherever analytically appropriate. Do not implement separate statistical truths for those uses. The exact internal API is not frozen. | Not started | — | — | — | — | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |

Total rows: 119. Not started: 110. In force: 9. Implemented, verified, and completed: 0. Completed tasks: TSK-001, TSK-002, TSK-003, TSK-004. Those tasks do not complete a requirement row.

## Items deliberately absent from this register

The following are not requirements and must not be given tasks until a decision accepts them:

- module and file layout, and concrete result-class or signature names ([OPEN-045](DECISIONS.md#open-questions), [OPEN-004](DECISIONS.md#open-questions));
- exact `quick` / `standard` / `deep` contents, thresholds, and sample sizes ([OPEN-010](DECISIONS.md#open-questions));
- the configuration-object shape ([OPEN-009](DECISIONS.md#open-questions));
- the closed statistical method catalog, effect-size formulas, and the multiple-testing family ([OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions));
- the method-registry schema and API ([OPEN-039](DECISIONS.md#open-questions));
- semantic-inference thresholds and the subtype taxonomy ([OPEN-044](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions));
- trimmed mean and common-token diagnostics ([OPEN-019](DECISIONS.md#open-questions));
- fuzzy or near-duplicate analysis, and the scope of deep time-series diagnostics ([OPEN-020](DECISIONS.md#open-questions));
- the diagnostic estimator family and the anomaly estimator ([OPEN-013](DECISIONS.md#open-questions), [OPEN-022](DECISIONS.md#open-questions));
- finding level names ([OPEN-025](DECISIONS.md#open-questions));
- dark mode as a committed feature ([OPEN-026](DECISIONS.md#open-questions));
- a 2.0 dependency lock or version pins ([OPEN-042](DECISIONS.md#open-questions)).

Migration mechanics are decided ([DEC-063](DECISIONS.md#dec-063)). They are not a requirement row.

The engine diagram, the three mode names, the shared statistical layer, the method-registry concept, DataFrame-only input, held-out permutation importance, and the candidate dependency directions are accepted. Acceptance is not a task and not an implementation. TSK-001, TSK-002, TSK-003, and TSK-004 are the only implementation tasks, and they do not implement those engines.
