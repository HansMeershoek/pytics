# Progress

The project owner accepted the Slice 001 codebase on 2026-10-03 as the approved baseline for continued development. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, and TSK-015 are complete. They are foundation slices. No requirement below is completed. TSK-005 completes the planned strong-physical-type semantics phase. A documentation-only Semantic Foundation consolidation, recorded the same day, accepted the candidate-resolution architecture in DEC-064 through DEC-076. TSK-006 then strengthened the universal column-evidence family. TSK-007 then added exact frequency observations and no semantic reading. TSK-008 then added exact numeric-structure observations and no semantic reading. TSK-009 then added exact string-structure observations and no semantic reading. TSK-010 then added exact pattern observations and no semantic reading. TSK-011 then added an Identifier candidate assessment and does not select that reading. TSK-012 then added Numeric, Categorical, and Text candidate assessments and does not select those readings. TSK-013 then added exact string-content observations and does not select a reading. TSK-014 then resolves structural readings and already produced candidate assessments. It does not assign confidence to a candidate-derived selection and does not enter the precedence chain. TSK-015 then records the inferred state after that resolution. It preserves a structural interpretation and does not assign confidence to a candidate-derived selection. It does not enter the precedence chain. The next implementation slice has not been selected.

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

A completed task may name a requirement it only prepares or only partly covers. That requirement stays Not started until the requirement as written is implemented. TSK-001 is that case for REQ-S-01, REQ-S-02, and REQ-S-05. TSK-002 infers Empty and Constant only and collects four basic counts. TSK-003 infers Boolean only from a physical Boolean dtype, and only after Empty and Constant. TSK-004 infers Datetime only from a native or timezone-aware datetime dtype, and only after those three rules. TSK-005 infers Timedelta only from a physical timedelta dtype, and only after those four rules. TSK-006 does not add a semantic reading. It derives convenience facts from the four basic counts and keeps Empty and Constant on those facts. TSK-007 does not add a semantic reading. It records exact frequency observations for non-missing values and does not interpret them. TSK-008 does not add a semantic reading. It records exact numeric-structure observations for physically numeric columns and does not interpret them. TSK-009 does not add a semantic reading. It records exact string-structure observations for physical string columns, and for object columns whose non-missing values are Python strings, and does not interpret them. TSK-010 does not add a semantic reading. It records exact full-value pattern observations for populations that already have string-structure evidence, and does not interpret them. TSK-011 does not select a semantic reading. It assesses whether observations support an Identifier candidate. TSK-012 does not select a semantic reading. It assesses whether observations support Numeric, Categorical, and Text candidates. Physical integer or floating storage can support Numeric. Physical categorical storage can support Categorical. Current observations do not support Text. TSK-013 does not add a semantic reading. It records exact token and vocabulary observations for populations that already have string-structure evidence, and it does not interpret them. TSK-014 resolves an already produced structural reading, or exactly one supported candidate, and abstains or stays ambiguous otherwise. It does not build a confidence-bearing interpretation for a candidate-derived selection. TSK-015 records that resolution together with the observed physical dtype. A structural reading keeps its interpretation. A candidate-derived selection remains resolved at the type level and does not become a confidence-bearing interpretation. Abstention and ambiguity are inferred states. Do not read these task links as completion of semantic inference, Boolean/Binary analysis, datetime analysis, time-series analysis, timedelta duration analysis, downstream numeric analysis, text diagnostics, identifier detection, or missing-like literal reporting.

## Task log

| Task | Requirements | Scope | Acceptance criteria | State |
| --- | --- | --- | --- | --- |
| TSK-001 | REQ-S-01, REQ-S-02, REQ-S-05, foundation only | Slice 001. Physical dtype classification and typed semantic value models. No inference. | The 16 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-001). | Completed |
| TSK-002 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, Empty and Constant only. REQ-S-03 respected on this path. | Slice 002. Exact basic column evidence and Empty/Constant inference. No other semantic type. | The 24 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-002). | Completed |
| TSK-003 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, physical Boolean only. REQ-D-01 and REQ-D-03 only for a physical Boolean dtype. REQ-S-03 and REQ-D-02 respected on this path. | Slice 003. Empty, then Constant, then physical Boolean. No other Boolean representation. | The 30 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-003). | Completed |
| TSK-004 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, physical Datetime only. REQ-E-03 and REQ-E-04 respected on this path. REQ-S-03 respected on this path. | Slice 004. Empty, then Constant, then physical Boolean, then physical Datetime. No string parsing and no time-series analysis. | The 42 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-004). | Completed |
| TSK-005 | REQ-S-01, REQ-S-02, REQ-S-04, REQ-S-05, physical Timedelta only. REQ-S-07 respected on this path. REQ-S-03 respected on this path. | Slice 005. Empty, then Constant, then physical Boolean, then physical Datetime, then physical Timedelta. No duration parsing and no duration analysis. | The 45 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-005). | Completed |
| TSK-006 | REQ-S-03 and REQ-S-05, universal column evidence only. REQ-S-01 and REQ-S-04 respected because no new reading was added. | Slice 006. Stored primary counts and derived facts on `BasicColumnEvidence`. No new semantic type. | The 31 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-006). | Completed |
| TSK-007 | REQ-S-03 and REQ-S-05, frequency observations only. REQ-S-01 and REQ-S-04 respected because no new reading was added. | Slice 007. Exact non-missing frequency evidence composed with basic column evidence. No new semantic type. | The 33 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-007). | Completed |
| TSK-008 | REQ-S-03 and REQ-S-05, numeric-structure observations only. REQ-S-01 and REQ-S-04 respected because no new reading was added. | Slice 008. Exact numeric-structure evidence for physical integer and floating columns, composed with basic column evidence. No new semantic type. | The 31 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-008). | Completed |
| TSK-009 | REQ-S-03 and REQ-S-05, string-structure observations only. REQ-S-01 and REQ-S-04 respected because no new reading was added. REQ-F-02 and REQ-H-04 are not completed. | Slice 009. Exact string-structure evidence for physical string columns and eligible object columns, composed with basic column evidence. No new semantic type. | The 34 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-009). | Completed |
| TSK-010 | REQ-S-03 and REQ-S-05, pattern observations only. REQ-S-01 and REQ-S-04 respected because no new reading was added. REQ-F-02, REQ-G-01, and REQ-G-02 are not completed. | Slice 010. Exact full-value pattern evidence composed with string-structure evidence. No new semantic type. | The 30 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-010). | Completed |
| TSK-011 | REQ-S-04 and REQ-S-05, candidate assessment only. REQ-S-01 respected because no reading is selected. REQ-G-01 and REQ-G-02 are not completed. | Slice 011. Candidate assessment foundation and an Identifier candidate. No resolution and no selected reading. | The 24 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-011). | Completed |
| TSK-012 | REQ-S-04 and REQ-S-05, candidate assessment only. REQ-S-01 respected because no reading is selected. REQ-C-01, REQ-F-01, REQ-D-01, and REQ-D-02 are not completed. | Slice 012. Numeric, Categorical, and Text candidate assessments. No resolution and no selected reading. | The 19 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-012). | Completed |
| TSK-013 | REQ-S-03 and REQ-S-05, string-content observations only. REQ-S-01 and REQ-S-04 respected because no reading is selected. REQ-F-01, REQ-F-02, and REQ-C-01 are not completed. | Slice 013. Exact token and vocabulary evidence composed with string-structure evidence. No new semantic type and no selected reading. | The 15 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-013). | Completed |
| TSK-014 | REQ-S-04 and REQ-S-05, resolution only. REQ-S-01 is not completed: a structural reading is preserved, and exactly one supported candidate selects a type without a confidence-bearing interpretation. REQ-S-02 is not completed. | Slice 014. Resolution of structural readings and candidate assessments. No override, no eligibility, and no public result. | The 16 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-014). | Completed |
| TSK-015 | REQ-S-04 and REQ-S-05, inferred state only. REQ-S-01 is not completed: a structural reading is preserved, and a candidate-derived selection stays without a confidence-bearing interpretation. REQ-S-02 is not completed. | Slice 015. Inferred state after resolution. No override, no effective interpretation, no eligibility, and no public result. | The 16 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-015). | Completed |

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

### TSK-005 — Slice 005, physical Timedelta inference

The committed Slice 001, Slice 002, Slice 003, and Slice 004 code was the development baseline. `git status` was clean, and `main` matched `origin/main`, before this slice. Slice 001, Slice 002, Slice 003, and Slice 004 files were not rewritten.

Approved in the Slice 005 session on 2026-10-03. This record was written after verification in that same session.

No new `DEC-###`. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) stay open. This slice introduces no inference threshold and no numeric confidence score. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions). `SemanticType.TIMEDELTA` is the only duration semantic type. No second duration type was added.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/physical_timedelta.py` | Empty, then Constant, then physical Boolean, then physical Datetime, then physical Timedelta, or no interpretation. |

Not modified: `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001, Slice 002, Slice 003, and Slice 004 tests were not modified.

Tests: `tests/test_physical_timedelta.py`.

`interpret_series_precedence` in this module classifies the physical dtype once and collects `BasicColumnEvidence` once. `interpret_precedence_from_evidence` calls `physical_datetime.interpret_precedence_from_evidence`. Only when that returns no reading does it apply the timedelta rule. It does not call `isna` or `nunique` again, and it does not classify again. There is no rule class, registry, or priority manager.

The Slice 004 function is unchanged. A non-empty, non-constant timedelta Series is still `None` from `physical_datetime.interpret_series_precedence`. The new module uses the same function names for its own entry point. The module path distinguishes the two. The new function calls the earlier chain and then one timedelta rule. It is not a framework, and the file location does not resolve [OPEN-045](DECISIONS.md#open-questions).

Precedence on the Slice 005 entry point is Empty, then Constant, then physical Boolean, then physical Datetime, then physical Timedelta, then no interpretation. `None` means this chain produced no interpretation. `SemanticType` has no unknown member, and this slice did not add one.

A Timedelta result requires all of: not Empty, not Constant, not the physical Boolean rule, not the physical Datetime rule, and `PhysicalDtypeFamily.TIMEDELTA`. The semantic type is `SemanticType.TIMEDELTA`. Confidence is `Confidence.HIGH`, because this slice treats the physical timedelta dtype as direct evidence, using the same High and physical-dtype pattern as Boolean and Datetime. That is not a score. Source is `InferenceSource.PHYSICAL_DTYPE`. Empty and Constant stay `InferenceSource.INFERRED`, including when the physical family is timedelta. Evidence is one statement: `physical dtype is timedelta`. Subtype is unset. Alternatives are empty. The Slice 001 physical dtype is retained, including `dtype_name`. `PhysicalDtype` was not given duration-unit or resolution metadata. Inference does not call `pd.to_timedelta` on source data. It does not parse strings, guess units, or depend on a particular resolution such as nanoseconds.

An all-`NaT` timedelta Series and a zero-length timedelta Series stay Empty. A repeated duration, including one distinct duration plus `NaT`, stays Constant. The physical family remains timedelta on those readings.

A physical timedelta Series does not become Datetime. A native datetime Series and a timezone-aware datetime Series stay Datetime and do not become Timedelta. [DEC-051](DECISIONS.md#dec-051) keeps Timedelta as its own semantic type. This slice does not implement the duration analysis that decision describes.

Duration-like strings stay strings and get no Timedelta reading. A one-value duration-like string stays Constant. Clock-like strings get no Timedelta reading. Integer and floating duration-like values get no Timedelta reading. An object Series of Python `timedelta` or pandas `Timedelta` values stays object and gets no interpretation. A categorical of timedeltas stays categorical and gets no interpretation. `PhysicalDtypeFamily.PERIOD` gets no interpretation. `PhysicalDtypeFamily.DATETIME` and `PhysicalDtypeFamily.DATETIME_TZ_AWARE` stay Datetime. A column name is not used. A Timedelta reading does not record duration statistics, readable units, zero durations, or negative durations. REQ-S-07 stays Not started.

The Series is not copied, coerced, or otherwise modified.

Timedelta is not yet emitted as a dataset-level fact. REQ-A-06 stays Not started. Numeric, Categorical, Text, and Identifier inference are not started.

This slice completes the planned sequence of semantic interpretations supported directly by a strong physical pandas dtype: Empty, Constant, Boolean, Datetime, timezone-aware Datetime, and Timedelta. It does not complete semantic inference.

At the time of this slice, the next step was a Semantic Foundation Review, not automatic implementation of another semantic type. This slice does not approve TSK-006. The review agenda was the current precedence composition, result models, evidence representation, ambiguity representation, subtype strategy, user overrides, configuration boundaries, inference thresholds, deterministic versus heuristic rules, likely interactions among Numeric, Categorical, Text, Identifier, and Binary candidates, and whether the current module boundaries should remain temporary. That list was an agenda. It was not a design. The review was later consolidated in documentation. See the documentation record below. This slice still does not approve a later implementation task.

Left open, and not decided in this slice: inference thresholds ([OPEN-044](DECISIONS.md#open-questions)); the subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); the order of later slices ([OPEN-037](DECISIONS.md#open-questions)); duration-like string inference; numeric duration inference; unit guessing; object-timedelta heuristics; period semantics; timedelta duration analysis; and time-series analysis ([OPEN-020](DECISIONS.md#open-questions)).

What was not implemented: Numeric semantic inference; continuous or discrete numeric subtype; `{0, 1}` Boolean inference; Boolean-like strings; binary categorical semantics; Categorical inference; Text inference; Identifier inference; datetime-like string inference; duration-like string inference; numeric duration inference; unit guessing; Period semantics; Ordinal semantics; thresholds; sampling; missing-like literal detection; near-constant detection; high-cardinality detection; dataset findings; relationships; statistical inference; target analysis; anomalies; compare/drift; HTML; PDF; time-series analysis; and duration analysis under REQ-S-07.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main`. `pytest tests/test_semantic_foundation.py -q` was 43 passed, `pytest tests/test_empty_constant.py -q` was 29 passed, `pytest tests/test_physical_boolean.py -q` was 22 passed, `pytest tests/test_physical_datetime.py -q` was 24 passed, and `pytest tests/test_profiler.py -q` was 19 passed, 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_physical_timedelta.py -q` | 25 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py -q` | 143 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 162 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is 25 Slice 005 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules were fully covered on the full run. Total coverage on that run was 97%.

All 45 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-006 — Slice 006, universal column evidence foundation

The committed Slice 001 through Slice 005 code, including the semantic-foundation consolidation, was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `ca5e99c`, before this slice.

Approved in the Slice 006 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-077](DECISIONS.md#dec-077). It sets the primary-versus-derived contract and the denominator of `unique_ratio_non_missing`. [OPEN-044](DECISIONS.md#open-questions) stays open for Identifier thresholds and every other use of uniqueness. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. This slice introduces no inference threshold, no numeric confidence score, and no new semantic type. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/column_evidence.py` | Stored primary counts, and derived ratios and boolean facts computed from them. |
| `src/pytics/semantics/empty_constant.py` | Empty, then Constant, using `is_empty` and `is_constant`. |

Not modified: `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 005 tests were not modified.

Tests: `tests/test_column_evidence.py`.

`BasicColumnEvidence` remains a frozen dataclass. The stored fields remain `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing`, as Python `int`. They are the primary observations. They are exact, full-column, and unsampled. Each is retained even though `n_non_missing` equals `n_total - n_missing`. Invariants on construction stay `n_total >= 0`, `0 <= n_missing <= n_total`, `n_non_missing == n_total - n_missing`, and `0 <= n_unique_non_missing <= n_non_missing`. The object still does not store a semantic type, confidence, threshold, provenance record, or the constant value.

`missing_ratio`, `unique_ratio_non_missing`, `has_missing`, `is_empty`, and `is_constant` are read-only properties. They are not dataclass fields. They are computed from the stored counts and do not scan the Series. `missing_ratio` is `n_missing / n_total` when `n_total > 0`, and `None` when `n_total == 0`. `unique_ratio_non_missing` is `n_unique_non_missing / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. There is no `unique_ratio` alias. `has_missing` is `n_missing > 0`. `is_empty` is `n_non_missing == 0`. `is_constant` is `n_non_missing > 0` and `n_unique_non_missing == 1`. A zero-length Series and an all-missing Series are empty and are not constant. One repeated non-missing value is constant, including beside missing observations, and including a one-row non-missing Series.

Collection is unchanged: `len(series)`, `Series.isna().sum()`, and `Series.nunique(dropna=True)`. It does not copy, mutate, stringify, parse, coerce, or repair the Series. `""`, `"NA"`, `"N/A"`, `"null"`, and `"?"` remain observed values unless pandas already treats them as missing. Unhashable non-missing values still raise `TypeError` and are not normalized. On pandas 3.0.6, a Series of lists is that case. No fallback count was added.

`interpret_empty_or_constant_from_evidence` tests `is_empty`, then `is_constant`. Evidence statements, confidence, inferred source, subtype, alternatives, and physical dtype are unchanged. Precedence on the Slice 005 entry point remains Empty, then Constant, then physical Boolean, then physical Datetime, then physical Timedelta, then no interpretation. No semantic type was added.

`interpret_series_precedence` in `physical_timedelta` still classifies the physical dtype once and collects `BasicColumnEvidence` once, then passes those results through the existing chain. `interpret_precedence_from_evidence` does not call `isna` or `nunique`. There is no cache framework and no provenance object. The four counts are definitionally exact. [DEC-076](DECISIONS.md#dec-076) still waits for a second procedure before a reusable provenance model.

What was not implemented: any later evidence family; value-frequency, dominant-frequency, or singleton analysis; UUID, hash, email, URL, path, or datetime-string detection; Numeric, Identifier, Categorical, Text, or Binary inference; `{0, 1}`, `{0.0, 1.0}`, true/false, or yes/no inference; candidate assessments; resolution; material alternatives; confidence rules; evidence-strength enums; scoring; abstention; user overrides; effective interpretation; ordinal representation; cross-column evidence; sampling; and a public API change.

Left open, and not decided in this slice: Identifier uniqueness thresholds and other uses of uniqueness ([OPEN-044](DECISIONS.md#open-questions)); sampling sizes ([OPEN-010](DECISIONS.md#open-questions)); the subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); the missing-like literal list ([OPEN-018](DECISIONS.md#open-questions)); eligibility ([OPEN-043](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); abstention ([OPEN-047](DECISIONS.md#open-047)); an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048)); Empty or Constant override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve TSK-007.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `ca5e99c6df50daad578960b4f68371e15d4354c3`. The pre-slice semantic baseline recorded under TSK-005 was 143 passed. The pre-slice full-suite baseline was 162 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py -q` | 159 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 178 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is 16 Slice 006 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules were fully covered on the full run. Total coverage on that run was 97%.

All 31 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-007 — Slice 007, frequency and cardinality evidence foundation

The committed Slice 001 through Slice 006 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `748eae0`, before this slice.

Approved in the Slice 007 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-078](DECISIONS.md#dec-078). It sets the frequency-observation contract, the ratio denominators, the on-demand collection rule, and the operational retention limit of 32 distinct non-missing values. That limit is a storage guard. It is not a semantic cardinality threshold. [OPEN-018](DECISIONS.md#open-questions) and [OPEN-044](DECISIONS.md#open-questions) stay open. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. This slice introduces no inference threshold, no numeric confidence score, and no new semantic type. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/frequency_evidence.py` | Exact non-missing frequency observations, composed with `BasicColumnEvidence`, collected only when requested. |

Not modified: `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 006 tests were not modified.

Tests: `tests/test_frequency_evidence.py`.

`FrequencyEvidence` is a frozen dataclass. It holds the already collected `BasicColumnEvidence` rather than copying `n_non_missing` or `n_unique_non_missing` into new fields. The stored frequency fields are `most_frequent_count`, `singleton_count`, and `exact_distinct_non_missing_values`. `most_frequent_ratio` and `singleton_ratio` are properties. `most_frequent_ratio` divides by `n_non_missing` and is `None` when that count is zero. `singleton_ratio` divides by `n_unique_non_missing`, not by the row count, and is `None` when that count is zero. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity.

The frequency population is non-missing values. Missing values are not keys. `n_missing`, `missing_ratio`, and `has_missing` stay on basic evidence. `""`, `"NA"`, `"N/A"`, `"null"`, and `"?"` remain observed values unless pandas already treats them as missing. An empty population has `most_frequent_count == 0`, `singleton_count == 0`, both ratios `None`, and an empty `frozenset`. A constant non-missing population has `most_frequent_count == n_non_missing` and `most_frequent_ratio == 1.0`. `singleton_count` is `1` only when that one value occurs once.

`EXACT_DISTINCT_VALUE_RETENTION_LIMIT` is 32. At or below that distinct count, the exact non-missing values are a `frozenset`. Above it, the field is `None` and the count mapping is not stored. The limit is not a semantic class. Values are not sorted and are not stringified. Python-equal values, including `True` and `1`, stay one key as pandas groups them. Unhashable non-missing values still raise `TypeError`. `value_counts` can group some of those values, and frequency collection still refuses them instead of stringifying, freezing, or dropping them.

Collection calls `value_counts` once with missing values excluded and does not call `nunique` or `isna`. Unobserved categorical levels at count zero are dropped from that count table before the facts are read. It checks the temporary counts against the supplied basic evidence and does not replace those counts. There is no sampling and no approximate cardinality. There is no provenance object. The Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta chain does not collect frequency evidence. Observe once, for this slice, means the observation is computed when requested and then shared. It does not mean the chain computes it eagerly.

What was not implemented: any further evidence family; Numeric, Identifier, Categorical, Text, or Binary inference; `{0, 1}`, `{0.0, 1.0}`, true/false, or yes/no inference; candidate assessments; resolution; material alternatives; confidence on frequency evidence; evidence roles; scoring; abstention; user overrides; effective interpretation; sampling; and a public API change.

Left open, and not decided in this slice: high cardinality, near-constant, and cardinality bands ([OPEN-018](DECISIONS.md#open-questions)); Identifier uniqueness thresholds and other inference cutoffs ([OPEN-044](DECISIONS.md#open-questions)); sampling sizes ([OPEN-010](DECISIONS.md#open-questions)); the subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); eligibility ([OPEN-043](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); abstention ([OPEN-047](DECISIONS.md#open-047)); an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048)); Empty or Constant override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `748eae0a9ff54c11ccf3321598a648787ff49015`. The pre-slice semantic baseline recorded under TSK-006 was 159 passed. The pre-slice full-suite baseline was 178 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py -q` | 203 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 222 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is 44 Slice 007 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules were fully covered on the full run. Total coverage on that run was 97%.

All 33 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-008 — Slice 008, numeric structure evidence foundation

The committed Slice 001 through Slice 007 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `27be007`, before this slice.

Approved in the Slice 008 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-079](DECISIONS.md#dec-079). It sets the numeric-structure contract: physical integer and floating applicability, Boolean exclusion, finite and infinity partition, finite-only sign counts, exact integer-like classification, ratio denominators, infinity-aware monotonicity, and on-demand collection. [OPEN-044](DECISIONS.md#open-questions) and [OPEN-046](DECISIONS.md#open-046) stay open. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. This slice introduces no inference threshold, no numeric confidence score, and no new semantic type. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/numeric_structure_evidence.py` | Exact numeric-structure observations for physical integer and floating columns, composed with `BasicColumnEvidence`, collected only when requested. |

Not modified: `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 007 tests were not modified.

Tests: `tests/test_numeric_structure_evidence.py`.

`NumericStructureEvidence` is a frozen dataclass. It holds the already collected `BasicColumnEvidence` rather than copying `n_total`, `n_missing`, or `n_non_missing` into new fields. The stored fields are the eight counts and `is_non_decreasing` and `is_non_increasing`. The five ratios are properties. `finite_ratio` divides by `n_non_missing` and is `None` when that count is zero. The sign ratios and `integer_like_ratio` divide by `finite_count` and are `None` when that count is zero. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. When the denominator is positive and the numerator is zero, the ratio is `0.0`.

The collector accepts `PhysicalDtypeFamily.INTEGER` and `PhysicalDtypeFamily.FLOATING` only. That includes nullable `Int64` and `Float64`, and a sparse floating dtype the classifier already calls floating. Physical Boolean raises `TypeError`, including a Boolean Series labeled as integer. String, object, Datetime, timezone-aware Datetime, Timedelta, categorical, period, and complex also raise `TypeError`. The collector does not call `pd.to_numeric`. `["1", "2", "3"]` is not numeric evidence.

Counts use one drop of pandas-missing values, then one numeric array in the original row order. The array keeps its integer or floating dtype. Integer values are not cast through float64. Missing NaN and `pd.NA` are not non-finite evidence. Finite values and the two infinities partition `n_non_missing`. Sign counts partition finite values. `0` and `-0.0` are both zero. Infinities are not sign counts. Integer-like means a finite value equals `np.trunc` of itself. There is no tolerance. `1.0` is integer-like and `1.0000000001` is not. Infinities are in neither integer-like count.

Monotonicity is a bool when every non-missing value is finite. Both flags are `None` when any infinity is present, including a constant infinity and a finite run that would have been monotonic beside an infinity. Missing values are skipped. The remaining values keep row order, not index-sorted order. A zero-length numeric Series, an all-missing numeric Series, one finite value, and a finite constant Series are both non-decreasing and non-increasing. Those cases stay Empty or Constant in the precedence chain. No step size is stored.

The collector checks `n_total` and `n_non_missing` against the supplied basic evidence and does not replace those counts. It does not call `nunique`, `value_counts`, or frequency collection, and it does not classify the physical dtype again. There is no sampling and no provenance object. The Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta chain does not collect numeric-structure evidence. A unique increasing integer series, `{0, 1}`, `{0.0, 1.0}`, and integer-like floats still receive no interpretation from that chain.

What was not implemented: Numeric, Identifier, Boolean, Binary, discrete, continuous, or ordinal inference; regular-step or sequence evidence; min, max, mean, median, quantiles, or other downstream numeric summaries; candidate assessment; resolution; sampling; and a public API change.

Left open, and not decided in this slice: Identifier thresholds and regular-step semantics ([OPEN-044](DECISIONS.md#open-questions)); Continuous and Discrete subtypes ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); sampling sizes ([OPEN-010](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); high cardinality and near-constant ([OPEN-018](DECISIONS.md#open-questions)); trimmed mean and common-token diagnostics ([OPEN-019](DECISIONS.md#open-questions)); eligibility ([OPEN-043](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); abstention ([OPEN-047](DECISIONS.md#open-047)); an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048)); Empty or Constant override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-B-01 or REQ-A-07. Zeros, negatives, and infinities here are structural observations, not the downstream numeric profile.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `27be0077d71015f7e7d1ca60b610168c6c801390`. The pre-slice semantic baseline recorded under TSK-007 was 203 passed. The pre-slice full-suite baseline was 222 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py -q` | 266 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 285 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is 63 Slice 008 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including numeric-structure evidence, were fully covered on the full run. Total coverage on that run was 98%. The previous full-suite figure was 97%. The rise is the new covered module. The uncovered profiler and visualization lines are unchanged.

All 31 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-009 — Slice 009, string structure evidence foundation

The committed Slice 001 through Slice 008 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `8ceb103`, before this slice.

Approved in the Slice 009 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-080](DECISIONS.md#dec-080). It sets the string-structure contract: physical string applicability, conditional object applicability, all-missing object exclusion, categorical exclusion, Python Unicode character classes, empty versus whitespace-only, length bounds, ratio denominators, and on-demand collection. [OPEN-014](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), and [OPEN-044](DECISIONS.md#open-questions) stay open. [OPEN-010](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. This slice introduces no inference threshold, no numeric confidence score, and no new semantic type. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/string_structure_evidence.py` | Exact string-structure observations for physical string columns and eligible object columns, composed with `BasicColumnEvidence`, collected only when requested. |

Not modified: `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 008 tests were not modified.

Tests: `tests/test_string_structure_evidence.py`.

`StringStructureEvidence` is a frozen dataclass. It holds the already collected `BasicColumnEvidence` rather than copying `n_total`, `n_missing`, `n_non_missing`, or `n_unique_non_missing` into new fields. The stored fields are the six counts and `min_length` and `max_length`. The six ratios are properties. Each divides by `n_non_missing` and is `None` when that count is zero. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. When the denominator is positive and the numerator is zero, the ratio is `0.0`.

The collector accepts `PhysicalDtypeFamily.STRING` for every storage variant the existing classifier already calls string, including an all-missing or zero-length string Series. It accepts `PhysicalDtypeFamily.OBJECT` only after every non-missing value passes `isinstance(value, str)`. That includes a subclass of `str`. An object Series with no non-missing value raises `TypeError`. Mixed objects, numeric objects, and `bytes` raise `TypeError` and are not stringified. Categorical storage raises `TypeError` even when the labels are strings. Boolean, integer, floating, Datetime, timezone-aware Datetime, Timedelta, Period, complex, and Interval also raise `TypeError`. Numpy byte-string storage stays in the physical string family and raises `TypeError` here, because the values are `bytes`. They are not decoded. Physical classification was not changed.

Counts use one drop of pandas-missing values, then one pass over the remaining values. `""` is an empty string. It is not whitespace-only, and its length is 0. Whitespace-only uses `str.isspace`. A string contains whitespace when one character does, so a whitespace-only string is included in that count. Alphabetic uses `str.isalpha`. Digit uses `str.isdigit`. Other means a character that is not alphabetic, not a digit, and not whitespace. Those content counts may overlap. The original string is not stripped, case-folded, or Unicode-normalized. Length is `len` of that string. Both bounds are `None` when there is no non-missing string. An observed empty string can make the minimum 0.

The collector checks `n_total` and `n_non_missing` against the supplied basic evidence and does not replace those counts. It does not call `nunique`, `value_counts`, or frequency collection, and it does not classify the physical dtype again. There is no sampling and no provenance object. The Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta chain does not collect string-structure evidence. A long string, a repeated short string, a fully unique string, `"0"` and `"1"`, a date-looking string, a numeric-looking string, and strings that contain `@`, `:`, or `/` still receive no interpretation from that chain beyond Empty or Constant when those rules already apply.

What was not implemented: Text, Categorical, Identifier, Boolean, Binary, Datetime, or Numeric inference; word or token counts; pattern evidence; candidate assessment; resolution; sampling; and a public API change.

Left open, and not decided in this slice: string subtypes, including generic string, URL-like, email-like, and path-like ([OPEN-014](DECISIONS.md#open-questions)); the missing-like literal list ([OPEN-018](DECISIONS.md#open-questions)); trimmed mean and common-token diagnostics ([OPEN-019](DECISIONS.md#open-questions)); Text, Categorical, and Identifier thresholds ([OPEN-044](DECISIONS.md#open-questions)); sampling sizes ([OPEN-010](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); eligibility ([OPEN-043](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); abstention ([OPEN-047](DECISIONS.md#open-047)); an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048)); Empty or Constant override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-F-02 or REQ-H-04. Empty strings, whitespace, and length bounds here are structural observations, not the downstream text profile and not a missing-like literal report.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `8ceb1031e9a3ed6969735063ed1485b850bc7df5`. The pre-slice semantic baseline recorded under TSK-008 was 266 passed. The pre-slice full-suite baseline was 285 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py -q` | 340 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 359 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is the unchanged 63 Slice 008 tests. `tests/test_string_structure_evidence.py` is 74 Slice 009 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including string-structure evidence, were fully covered on the full run. Total coverage on that run was 98%. The string-structure module had no missed statements. The uncovered profiler and visualization lines are unchanged.

All 34 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-010 — Slice 010, pattern evidence foundation

The committed Slice 001 through Slice 009 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `8644529`, before this slice.

Approved in the Slice 010 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-081](DECISIONS.md#dec-081). It sets the pattern contract: composition with prior string-structure evidence, full-value matching, the UUID, IPv4, IPv6, and fixed-width ASCII hexadecimal catalog, allowed overlap, the non-missing denominator, bounded counts, and on-demand collection. [OPEN-014](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), and [OPEN-044](DECISIONS.md#open-questions) stay open. [OPEN-010](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. This slice introduces no inference threshold, no numeric confidence score, and no new semantic type. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/pattern_evidence.py` | Exact full-value pattern observations composed with `StringStructureEvidence`, collected only when requested. |

Not modified: `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 009 tests were not modified.

Tests: `tests/test_pattern_evidence.py`.

`PatternEvidence` is a frozen dataclass. It holds the already collected `StringStructureEvidence` rather than copying `n_total`, `n_missing`, `n_non_missing`, or `n_unique_non_missing` into new fields. The stored fields are that object and the seven pattern counts. The seven ratios are properties. Each divides by `string_structure.basic.n_non_missing` and is `None` when that count is zero. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. When the denominator is positive and the numerator is zero, the ratio is `0.0`.

The collector does not decide string eligibility again. It uses the supplied string-structure evidence as that decision, then checks that the Series length and non-missing count agree, that the physical dtype name agrees, and that every non-missing value is a Python `str`. A physical family other than string or object is rejected. An all-missing object population is rejected. `bytes` are not decoded. Categorical labels are not inspected. An all-missing or zero-length physical string column is accepted and yields zero counts and undefined ratios.

Counts use one drop of pandas-missing values, then one pass over the remaining strings. The original string is not stripped, case-folded, or Unicode-normalized. UUID syntax is the 36-character hyphenated form or the 32-character compact form. `uuid.UUID` is consulted only after that shape matches, so braces, a `urn:uuid:` prefix, and misplaced hyphens do not match. No UUID version is required. IPv4 and IPv6 use `ipaddress.IPv4Address` and `ipaddress.IPv6Address` on the entire original string. A successful IPv6 parse is not compared with a canonical spelling. CIDR text does not match. Fixed-width tokens use the ASCII alphabet `0123456789abcdefABCDEF` at widths 32, 40, 64, and 128. That alphabet is not the Unicode character-class definition used by string structure. The widths are not hash-algorithm names. A compact UUID increments both `uuid_count` and `hex_32_count`. The counts are not mutually exclusive, and their sum may exceed `n_non_missing`. No matched strings are stored.

The collector does not call `nunique`, `value_counts`, frequency collection, string-structure collection, or physical classification. There is no sampling and no provenance object. The Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta chain does not collect pattern evidence. Collecting string structure alone does not collect it either. A column of UUIDs, a column of IP addresses, and a column of hexadecimal tokens still receive no Identifier reading. A pattern-free string column still receives no Text or Categorical reading. A constant pattern column remains Constant. Empty precedence is unchanged.

What was not implemented: Identifier, Text, Categorical, Boolean, Binary, Datetime, or Numeric inference; email, URL, path, phone, postal code, MAC, date-like, or other pattern families; candidate assessment; resolution; sampling; and a public API change.

Left open, and not decided in this slice: string subtypes, including generic string, URL-like, email-like, and path-like ([OPEN-014](DECISIONS.md#open-questions)); trimmed mean and common-token diagnostics ([OPEN-019](DECISIONS.md#open-questions)); Identifier thresholds and whether UUID-like or hash-like structure can be sufficient alone ([OPEN-044](DECISIONS.md#open-questions)); the missing-like literal list ([OPEN-018](DECISIONS.md#open-questions)); sampling sizes ([OPEN-010](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); eligibility ([OPEN-043](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); abstention ([OPEN-047](DECISIONS.md#open-047)); an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048)); Empty or Constant override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-F-02, REQ-G-01, or REQ-G-02. UUID, IP, and hexadecimal counts here are syntactic observations, not an Identifier reading and not a text-diagnostic pattern-consistency report.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `8644529adbc73049dbecd6a901e8a28a546fb5b4`. The pre-slice semantic baseline recorded under TSK-009 was 340 passed. The pre-slice full-suite baseline was 359 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_pattern_evidence.py -q` | 172 passed |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py -q` | 512 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 531 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is the unchanged 63 Slice 008 tests. `tests/test_string_structure_evidence.py` is the unchanged 74 Slice 009 tests. `tests/test_pattern_evidence.py` is 172 Slice 010 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including pattern evidence, were fully covered on the full run. Total coverage on that run was 98%. The pattern module had no missed statements. The uncovered profiler and visualization lines are unchanged.

All 30 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-011 — Slice 011, candidate assessment foundation and Identifier candidate

The committed Slice 001 through Slice 010 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `2a66f59`, before this slice.

Approved in the Slice 011 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-082](DECISIONS.md#dec-082). It sets the candidate-assessment contract: one `SemanticType`, a disposition of supported, not supported, or contradicted, separate supporting and contradicting statements, and no score or final confidence. It also sets the first Identifier rules. A full non-missing population of UUID syntax, or of one ASCII hexadecimal width 32, 40, 64, or 128, supports the Identifier candidate. That rule is the conservative initial candidate rule for the current evidence foundation. It is not a universal threshold. Uniqueness, missingness, partial ratios, mixed patterns, IP syntax, column names, and numeric monotonicity do not support the candidate. Duplicates do not contradict it. Empty and Constant, including a constant UUID, are not supported and are not contradictions. [OPEN-044](DECISIONS.md#open-questions) stays open for partial-pattern thresholds, numeric sequence Identifier evidence, name and dataset context, final resolution, and final confidence. [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/candidate.py` | Frozen candidate assessment and disposition. Not a selected interpretation. |
| `src/pytics/semantics/identifier_candidate.py` | Identifier candidate assessment from evidence already collected. Not called by the precedence chain. |

Not modified: `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/pattern_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 010 tests were not modified.

Tests: `tests/test_candidate_assessment.py`, `tests/test_identifier_candidate.py`.

`CandidateAssessment` is a frozen dataclass. `semantic_type` is a `SemanticType`. `disposition` is `CandidateDisposition`: `SUPPORTED`, `NOT_SUPPORTED`, or `CONTRADICTED`. Supporting and contradicting evidence are tuples of `SemanticEvidence`. There is no second evidence class. `SUPPORTED` requires at least one supporting statement. `CONTRADICTED` requires at least one contradicting statement. Both sequences may be non-empty. `NOT_SUPPORTED` may carry none. The value has no score, confidence, winner, rank, or priority. It is not a `SemanticInterpretation`.

`assess_identifier_candidate` always returns an Identifier candidate assessment. It accepts `BasicColumnEvidence`, `PhysicalDtype`, and optional frequency, numeric-structure, string-structure, and pattern evidence. When one of those objects is supplied, it must be the object composed with that basic evidence. Pattern evidence must be the supplied string-structure object. Equal counts from another object are rejected. A physical family that cannot carry numeric-structure or string-structure evidence is rejected. The function does not take a Series, does not read a column name, and does not call the collectors or the physical classifier.

Empty and Constant are `NOT_SUPPORTED`, including a constant UUID whose pattern ratio is 1.0. An all-missing string column and a zero-length string column are `NOT_SUPPORTED`. Those results are not contradictions. A full non-missing UUID population is `SUPPORTED`, including compact form, uppercase, duplicates, unique values, object storage, and missing values beside the UUIDs. The statement says that all non-missing values match the UUID syntax. A full population at hexadecimal width 32, 40, 64, or 128 is `SUPPORTED`. The statement names that width and ASCII hexadecimal tokens. It does not name a hash algorithm. A compact UUID records both the UUID statement and the 32-character statement. The disposition stays `SUPPORTED`. There is no second degree of support. A ratio below the full population, a mixture of UUID, IP, and hexadecimal values, full IPv4, full IPv6, date-like strings, email-like strings, URL-like strings, ordinary labels, uniqueness, zero missingness, and a singleton ratio stay `NOT_SUPPORTED`. Physical categorical, Boolean, Datetime, timezone-aware Datetime, and Timedelta stay `NOT_SUPPORTED`.

Unique complete integer sequences, including `1, 2, 3, 4, 5`, `1001, 1002, 1003, 1004`, `10, 20, 30, 40`, and `5, 4, 3, 2, 1`, stay `NOT_SUPPORTED` even when they are integer-like and monotonic. The assessor does not read those flags and does not reconstruct a step. No Identifier assessment in this slice emits contradicting evidence.

`interpret_series_precedence` does not call the assessor. Empty, Constant, physical Boolean, physical Datetime, and physical Timedelta keep their current readings. An ordinary numeric column, an ordinary string column, and a UUID string column still receive the current chain result. The UUID column is not Identifier there.

What was not implemented: resolution; final confidence; material alternatives; Numeric, Categorical, Text, or Boolean candidate assessors; Identifier support from uniqueness, missingness, cardinality, IP syntax, partial patterns, column names, or numeric sequences; regular-step evidence; a public API change.

Left open, and not decided in this slice: partial-pattern Identifier thresholds and numeric sequence Identifier evidence ([OPEN-044](DECISIONS.md#open-questions)); column-name, schema, and dataset-context evidence ([OPEN-044](DECISIONS.md#open-questions), [DEC-073](DECISIONS.md#dec-073)); final candidate resolution and final confidence; string subtypes ([OPEN-014](DECISIONS.md#open-questions)); sampling sizes ([OPEN-010](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); high cardinality and near-constant ([OPEN-018](DECISIONS.md#open-questions)); eligibility ([OPEN-043](DECISIONS.md#open-questions)); module layout ([OPEN-045](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); abstention ([OPEN-047](DECISIONS.md#open-047)); an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048)); Empty or Constant override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-S-01, REQ-G-01, or REQ-G-02. A supported Identifier candidate is not the semantic reading of the column.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `2a66f5939e5742cf4c07ba26b8a0225d7fb1f725`. The pre-slice semantic baseline recorded under TSK-010 was 512 passed. The pre-slice full-suite baseline was 531 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_candidate_assessment.py -q` | 24 passed |
| `pytest tests/test_identifier_candidate.py -q` | 61 passed |
| `pytest tests/test_pattern_evidence.py -q` | 172 passed |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py tests/test_candidate_assessment.py tests/test_identifier_candidate.py -q` | 597 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 616 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is the unchanged 63 Slice 008 tests. `tests/test_string_structure_evidence.py` is the unchanged 74 Slice 009 tests. `tests/test_pattern_evidence.py` is the unchanged 172 Slice 010 tests. `tests/test_candidate_assessment.py` is 24 Slice 011 foundation tests. `tests/test_identifier_candidate.py` is 61 Slice 011 Identifier tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including candidate assessment and the Identifier assessor, were fully covered on the full run. Total coverage on that run was 99%. Both new modules had no missed statements. The uncovered lines remain in the profiler and visualizations.

All 24 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-012 — Slice 012, Numeric, Categorical, and Text candidates

The committed Slice 001 through Slice 011 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `c469d9b`, before this slice.

Approved in the Slice 012 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-083](DECISIONS.md#dec-083). It reuses the candidate model from [DEC-082](DECISIONS.md#dec-082). A non-empty, non-constant physical integer or floating column supports a Numeric candidate. A non-empty, non-constant physical categorical column supports a Categorical candidate. Current observations do not support a Text candidate. Empty and Constant are not supported for any of the three, and they are not contradictions. No cardinality, uniqueness, length, or whitespace threshold is set. `{0, 1}` numeric storage may support Numeric and is not Boolean or Binary. Ordered categorical metadata stays on the physical dtype and does not become Ordinal. Identifier rules are unchanged. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open, as do resolution, final confidence, and user overrides. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/core_candidates.py` | Numeric, Categorical, and Text candidate assessments from evidence already collected. Not called by the precedence chain. |

Not modified: `src/pytics/semantics/candidate.py`, `src/pytics/semantics/identifier_candidate.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/pattern_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 011 tests were not modified. The new assessors call the existing Identifier bundle-identity check. They do not change it.

Tests: `tests/test_core_candidates.py`.

`assess_numeric_candidate`, `assess_categorical_candidate`, and `assess_text_candidate` each return one candidate assessment. They accept `BasicColumnEvidence`, `PhysicalDtype`, and optional frequency, numeric-structure, string-structure, and pattern evidence. When one of those objects is supplied, it must be the object composed with that basic evidence. Pattern evidence must be the supplied string-structure object. The functions do not take a Series, do not read a column name, and do not call the collectors or the physical classifier.

Empty and Constant are `NOT_SUPPORTED` for all three candidates. A supported Numeric statement names the physical family, `INTEGER` or `FLOATING`, and says that family supports a Numeric reading. A supported Categorical statement says that physical categorical storage supports a Categorical reading. Text supporting evidence stays empty. No assessment in this slice has contradicting evidence. None assigns High, Medium, or Low. None is a `SemanticInterpretation`.

`interpret_series_precedence` does not call the assessors. Empty, Constant, physical Boolean, physical Datetime, timezone-aware Datetime, and physical Timedelta keep their current readings. An ordinary numeric column, an ordinary string column, and a UUID string column still receive the current chain result.

What was not implemented: resolution; final confidence; material alternatives; a score; a Text support rule; a Categorical rule for untyped strings or numeric codes; Boolean or Binary inference from `{0, 1}` or from string labels; an Ordinal type; regular-step Identifier evidence; word or token counts; a user override; a public API change.

Left open, and not decided in this slice: cardinality and vocabulary rules for Categorical ([OPEN-044](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions)); length, whitespace, and word-count rules for Text ([OPEN-044](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions)); Binary representation ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); partial-pattern Identifier thresholds and numeric sequence Identifier evidence ([OPEN-044](DECISIONS.md#open-questions)); final candidate resolution and final confidence; user overrides ([OPEN-009](DECISIONS.md#open-questions), [OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-S-01, REQ-C-01, REQ-F-01, REQ-D-01, or REQ-D-02. A supported Numeric or Categorical candidate is not the semantic reading of the column. An unsupported Text candidate is not a finding that the column is not text.

Verification, 2026-10-03, local `.venv`, Python 3.14.8, pandas 3.0.6, numpy 2.5.3. Before this slice the working tree was clean and `main` matched `origin/main` at `c469d9baf34ed1e0d43fc9af07f04f2aa9feeff4`. The pre-slice semantic baseline recorded under TSK-011 was 597 passed. The pre-slice full-suite baseline was 616 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_core_candidates.py -q` | 97 passed |
| `pytest tests/test_candidate_assessment.py -q` | 24 passed |
| `pytest tests/test_identifier_candidate.py -q` | 61 passed |
| `pytest tests/test_pattern_evidence.py -q` | 172 passed |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py tests/test_candidate_assessment.py tests/test_identifier_candidate.py tests/test_core_candidates.py -q` | 694 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 713 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is the unchanged 63 Slice 008 tests. `tests/test_string_structure_evidence.py` is the unchanged 74 Slice 009 tests. `tests/test_pattern_evidence.py` is the unchanged 172 Slice 010 tests. `tests/test_candidate_assessment.py` is the unchanged 24 Slice 011 foundation tests. `tests/test_identifier_candidate.py` is the unchanged 61 Slice 011 Identifier tests. `tests/test_core_candidates.py` is 97 Slice 012 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including the new candidate assessors, were fully covered on the full run. Total coverage on that run was 99%. `core_candidates.py` had no missed statements. The uncovered lines remain in the profiler and visualizations.

All 19 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-013 — Slice 013, string vocabulary and text-structure evidence

The committed Slice 001 through Slice 012 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `f2393c7`, before this slice.

Approved in the Slice 013 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-084](DECISIONS.md#dec-084). `StringContentEvidence` is composed with `StringStructureEvidence`. A token is a maximal contiguous run of characters for which `str.isalnum` is true. Case is preserved. Accents are not normalized. Empty strings and whitespace-only strings stay observed strings with no token. Missing values stay missing. Stored facts are the zero-token, one-token, and multiple-token partition, the total token count, the total character count, and aggregate distinct-token, singleton-token, and most-frequent-token counts. `token_singleton_ratio` divides by distinct tokens. `most_frequent_token_ratio` divides by token occurrences. No raw string or vocabulary is retained. Whole-value frequency stays a separate observation. The family is exact, full-column, and unsampled. The precedence chain does not collect it. No token-count, vocabulary, or length threshold was added. `core_candidates.py` is unchanged: ordinary one-token labels and multi-token sentences stay unsupported for Categorical and Text. [OPEN-019](DECISIONS.md#open-questions) records the evidence collection and leaves diagnostics and inference rules open. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) stay open, as do resolution, final confidence, and user overrides. Internal names below are not a public schema. They do not resolve [OPEN-004](DECISIONS.md#open-questions) or [OPEN-009](DECISIONS.md#open-questions).

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/string_content_evidence.py` | Exact token and vocabulary observations composed with string-structure evidence. Not called by the precedence chain. |

Not modified: `src/pytics/semantics/core_candidates.py`, `src/pytics/semantics/candidate.py`, `src/pytics/semantics/identifier_candidate.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/pattern_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 012 tests were not modified.

Tests: `tests/test_string_content_evidence.py`.

`collect_string_content_evidence` returns one frozen `StringContentEvidence`. It accepts a Series, the string-structure evidence already collected for that Series, and the physical dtype already classified for that Series. `string_structure` on the result is that same object. Basic counts stay on it. The collector does not take a column name.

`total_token_count` counts alphanumeric runs. `strings_with_zero_tokens_count`, `strings_with_one_token_count`, and `strings_with_multiple_tokens_count` partition `n_non_missing`. `total_character_count` is the sum of `len` of the original non-missing strings. `n_distinct_tokens`, `singleton_token_count`, and `most_frequent_token_count` describe the temporary token tally and are the only vocabulary facts retained. `"Apple"` and `"apple"` stay distinct. `"red car"` and `"blue car"` can repeat a token while remaining two distinct whole values. A hyphenated UUID can be several alphanumeric runs and still one UUID pattern match.

`interpret_series_precedence` does not collect this family. Empty, Constant, physical Boolean, physical Datetime, timezone-aware Datetime, and physical Timedelta keep their current readings. An ordinary numeric column, an ordinary string column, and a UUID string column still receive the current chain result. Candidate assessors do not collect the new evidence. Numeric, physical Categorical, and full-population UUID Identifier support stay as they were. `{0, 1}` stays a Numeric candidate and not Boolean or Binary.

What was not implemented: a Text support rule; a Categorical rule for ordinary strings; resolution; final confidence; material alternatives; a score; Binary or Ordinal inference; regular-step Identifier evidence; language detection; a retained vocabulary; a user override; a public API change.

Left open, and not decided in this slice: whether token facts should support Text or Categorical ([OPEN-044](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions)); downstream common-token diagnostics and trimmed mean ([OPEN-019](DECISIONS.md#open-questions)); operational cardinality thresholds ([OPEN-018](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions)); Binary representation ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); partial-pattern Identifier thresholds and numeric sequence Identifier evidence ([OPEN-044](DECISIONS.md#open-questions)); final candidate resolution and final confidence; user overrides ([OPEN-009](DECISIONS.md#open-questions), [OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-S-01, REQ-F-01, REQ-F-02, or REQ-C-01. An observation of one token or of several tokens is not a semantic reading.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `f2393c74f14a720a87a9369519e8a3405349eb9f`. The pre-slice semantic baseline recorded under TSK-012 was 694 passed. The pre-slice full-suite baseline was 713 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_string_content_evidence.py -q` | 83 passed |
| `pytest tests/test_core_candidates.py -q` | 97 passed |
| `pytest tests/test_candidate_assessment.py -q` | 24 passed |
| `pytest tests/test_identifier_candidate.py -q` | 61 passed |
| `pytest tests/test_pattern_evidence.py -q` | 172 passed |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py tests/test_candidate_assessment.py tests/test_identifier_candidate.py tests/test_core_candidates.py tests/test_string_content_evidence.py -q` | 777 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 796 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is the unchanged 63 Slice 008 tests. `tests/test_string_structure_evidence.py` is the unchanged 74 Slice 009 tests. `tests/test_pattern_evidence.py` is the unchanged 172 Slice 010 tests. `tests/test_candidate_assessment.py` is the unchanged 24 Slice 011 foundation tests. `tests/test_identifier_candidate.py` is the unchanged 61 Slice 011 Identifier tests. `tests/test_core_candidates.py` is the unchanged 97 Slice 012 tests. `tests/test_string_content_evidence.py` is 83 Slice 013 tests. The combined semantic run was 777 passed, which is the previous 694 plus these 83. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including string-content evidence, were fully covered on the full run. Total coverage on that run was 99%. `string_content_evidence.py` had no missed statements. The uncovered lines remain in the profiler and visualizations.

All 15 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-014 — Slice 014, semantic resolution foundation

The committed Slice 001 through Slice 013 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `32366bd`, before this slice.

Approved in the Slice 014 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-085](DECISIONS.md#dec-085). Resolution status is not a semantic type. `resolve_semantics` consumes an optional structural interpretation and candidate assessments already produced. Empty, Constant, Boolean, Datetime, and Timedelta resolve to the interpretation already produced, and candidates do not replace them. Exactly one supported candidate selects that semantic type and does not receive High, Medium, or Low, and does not become a `SemanticInterpretation`. No supported candidate is `INSUFFICIENT_EVIDENCE`, with no fallback type. More than one supported candidate is `AMBIGUOUS`, with no selected type. A contradicted candidate does not veto a different supported candidate. Duplicate semantic types are rejected. Input order does not change the result. The precedence chain does not call the resolver. [OPEN-047](DECISIONS.md#open-047) records those statuses and leaves the inferred-interpretation representation open. [OPEN-044](DECISIONS.md#open-questions) stays open for thresholds, candidate-derived confidence, and any future rule between supported candidates. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/resolution.py` | Resolve structural readings and candidate assessments. Not called by the precedence chain. |

Not modified: `src/pytics/semantics/core_candidates.py`, `src/pytics/semantics/candidate.py`, `src/pytics/semantics/identifier_candidate.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/string_content_evidence.py`, `src/pytics/semantics/pattern_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 013 tests were not modified.

Tests: `tests/test_semantic_resolution.py`.

`SemanticResolution` is frozen. `RESOLVED` requires a selected semantic type. `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` must not have one. A structural result also keeps the supplied `SemanticInterpretation`, including its existing confidence. A candidate-derived result records only the selected semantic type. Stored candidates are a tuple ordered by semantic-type name. That order is not a selection rule.

`resolve_semantics` does not import pandas, does not collect observations, and does not call candidate assessors. `interpret_series_precedence` does not call it. Empty, Constant, physical Boolean, physical Datetime, timezone-aware Datetime, and physical Timedelta keep their current chain results. An ordinary numeric column, an ordinary string column, and a UUID string column still receive the current chain result.

What was not implemented: a confidence for a candidate-derived selection; the `SemanticInterpretation` for that selection; material alternatives; an Identifier-over-Numeric rule; a user override; effective interpretation; downstream eligibility; a public result; a threshold; a numeric total.

Left open, and not decided in this slice: how an inferred interpretation should represent abstention, ambiguity, candidate-derived confidence, and material alternatives ([OPEN-047](DECISIONS.md#open-047)); inference thresholds and any future rule between supported candidates ([OPEN-044](DECISIONS.md#open-questions)); Text and ordinary-string Categorical inference ([OPEN-044](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions)); Binary representation ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); numeric Identifier evidence ([OPEN-044](DECISIONS.md#open-questions)); user overrides ([OPEN-009](DECISIONS.md#open-questions), [OPEN-049](DECISIONS.md#open-049)); downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); the public result shape ([OPEN-004](DECISIONS.md#open-questions)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-S-01, REQ-S-02, REQ-S-04, or REQ-S-05. A resolution status is not the public semantic interpretation.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `32366bd9b6b1d63d2e82dd8ab3c4db7647a07e15`. The pre-slice semantic baseline recorded under TSK-013 was 777 passed. The pre-slice full-suite baseline was 796 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_semantic_resolution.py -q` | 103 passed |
| `pytest tests/test_string_content_evidence.py -q` | 83 passed |
| `pytest tests/test_core_candidates.py -q` | 97 passed |
| `pytest tests/test_candidate_assessment.py -q` | 24 passed |
| `pytest tests/test_identifier_candidate.py -q` | 61 passed |
| `pytest tests/test_pattern_evidence.py -q` | 172 passed |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py tests/test_candidate_assessment.py tests/test_identifier_candidate.py tests/test_core_candidates.py tests/test_string_content_evidence.py tests/test_semantic_resolution.py -q` | 880 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 899 passed, 1 failed |

`tests/test_semantic_foundation.py` is the unchanged 43 Slice 001 tests. `tests/test_empty_constant.py` is the unchanged 29 Slice 002 tests. `tests/test_physical_boolean.py` is the unchanged 22 Slice 003 tests. `tests/test_physical_datetime.py` is the unchanged 24 Slice 004 tests. `tests/test_physical_timedelta.py` is the unchanged 25 Slice 005 tests. `tests/test_column_evidence.py` is the unchanged 16 Slice 006 tests. `tests/test_frequency_evidence.py` is the unchanged 44 Slice 007 tests. `tests/test_numeric_structure_evidence.py` is the unchanged 63 Slice 008 tests. `tests/test_string_structure_evidence.py` is the unchanged 74 Slice 009 tests. `tests/test_pattern_evidence.py` is the unchanged 172 Slice 010 tests. `tests/test_candidate_assessment.py` is the unchanged 24 Slice 011 foundation tests. `tests/test_identifier_candidate.py` is the unchanged 61 Slice 011 Identifier tests. `tests/test_core_candidates.py` is the unchanged 97 Slice 012 tests. `tests/test_string_content_evidence.py` is the unchanged 83 Slice 013 tests. `tests/test_semantic_resolution.py` is 103 Slice 014 tests. The combined semantic run was 880 passed, which is the previous 777 plus these 103. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including resolution, were fully covered on the full run. Total coverage on that run was 99%. `resolution.py` had no missed statements. The uncovered lines remain in the profiler and visualizations.

All 16 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-015 — Slice 015, inferred interpretation foundation

The committed Slice 001 through Slice 014 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `d979f9c`, before this slice.

Approved in the Slice 015 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-086](DECISIONS.md#dec-086). `InferredSemanticResult` stores the observed physical dtype and the `SemanticResolution` already produced. It does not store a second status or a second selected type. `interpretation` is the structural interpretation when resolution has one, and `None` otherwise. `selected_type` is read from the resolution. `build_inferred_semantic_result` combines those two facts and does not collect observations, assess candidates, or call the resolver. A structural resolution keeps that interpretation object, including its confidence and source. The supplied physical dtype must match it. A candidate-derived `RESOLVED` result keeps the selected semantic type and does not receive a `SemanticInterpretation`, because current Numeric, Identifier, and Categorical support does not justify High, Medium, or Low. A constructed Text candidate is not a production confidence rule. `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` are valid inferred states with no interpretation and no selected type. Ambiguity does not become a selected reading plus low confidence plus material alternatives. The precedence chain does not call the constructor. [OPEN-047](DECISIONS.md#open-047) records that representation and leaves candidate-derived confidence, material alternatives on a future selected reading, and the public result open. [OPEN-044](DECISIONS.md#open-questions) stays open for that confidence. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/inferred.py` | Inferred semantic state after a resolution already produced. Not called by the precedence chain. |

Not modified: `src/pytics/semantics/resolution.py`, `src/pytics/semantics/core_candidates.py`, `src/pytics/semantics/candidate.py`, `src/pytics/semantics/identifier_candidate.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/string_content_evidence.py`, `src/pytics/semantics/pattern_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 014 tests were not modified.

Tests: `tests/test_inferred_semantics.py`.

`InferredSemanticResult` is frozen. The stored fields are `physical` and `resolution`. `interpretation` and `selected_type` are derived, so they cannot disagree with the resolution. Empty, Constant, physical Boolean, physical Datetime, timezone-aware Datetime, and physical Timedelta keep the interpretation object the precedence chain already produced. A different supplied physical dtype, including a categorical ordered-flag mismatch, is rejected. Integer and floating Numeric selections, string and object Identifier selections, and categorical selections keep the observed physical dtype and have no interpretation. City names and prose-like strings are insufficient evidence. A Numeric-plus-Identifier fixture is ambiguous. Neither outcome is `None`. Construction does not recollect evidence or call `resolve_semantics`. `interpret_series_precedence` does not call the constructor.

What was not implemented: High, Medium, or Low confidence for a candidate-derived selection; a `SemanticInterpretation` for that selection; material alternatives; an evidence-strength enum; a semantic-type-to-physical-dtype mapping; a user override; effective interpretation; downstream eligibility; a public result; orchestration from a Series through the whole pipeline; a threshold; a numeric total.

Left open, and not decided in this slice: candidate-derived confidence ([OPEN-044](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047)); material alternatives once a reading is selected while another stays plausible ([OPEN-047](DECISIONS.md#open-047)); Text and ordinary-string Categorical inference ([OPEN-044](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions)); Binary representation ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); numeric Identifier evidence ([OPEN-044](DECISIONS.md#open-questions)); user overrides and effective interpretation ([OPEN-009](DECISIONS.md#open-questions), [OPEN-049](DECISIONS.md#open-049), [OPEN-004](DECISIONS.md#open-questions)); downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); the public result shape ([OPEN-004](DECISIONS.md#open-questions)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-S-01, REQ-S-02, REQ-S-04, or REQ-S-05. An inferred result is not the public semantic interpretation and not the effective interpretation.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `d979f9cc4a3050a276513caa269c2a704589fc4f`. The pre-slice semantic baseline recorded under TSK-014 was 880 passed. The pre-slice full-suite baseline was 899 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_inferred_semantics.py -q` | 40 passed |
| `pytest tests/test_semantic_resolution.py -q` | 103 passed |
| `pytest tests/test_string_content_evidence.py -q` | 83 passed |
| `pytest tests/test_core_candidates.py -q` | 97 passed |
| `pytest tests/test_candidate_assessment.py -q` | 24 passed |
| `pytest tests/test_identifier_candidate.py -q` | 61 passed |
| `pytest tests/test_pattern_evidence.py -q` | 172 passed |
| `pytest tests/test_string_structure_evidence.py -q` | 74 passed |
| `pytest tests/test_numeric_structure_evidence.py -q` | 63 passed |
| `pytest tests/test_frequency_evidence.py -q` | 44 passed |
| `pytest tests/test_column_evidence.py -q` | 16 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py tests/test_candidate_assessment.py tests/test_identifier_candidate.py tests/test_core_candidates.py tests/test_string_content_evidence.py tests/test_semantic_resolution.py tests/test_inferred_semantics.py -q` | 920 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 939 passed, 1 failed |

`tests/test_inferred_semantics.py` is 40 Slice 015 tests. The combined semantic run was 920 passed, which is the previous 880 plus these 40. The full suite was 939 passed and 1 failed, which is the previous 899 plus these 40. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including inferred results, were fully covered on the full run. Total coverage on that run was 99%. `inferred.py` had no missed statements. The uncovered lines remain in the profiler and visualizations.

All 16 acceptance criteria in the implementation plan passed. Dependency files were not changed.

## Documentation record — semantic foundation consolidation

Recorded 2026-10-03, after TSK-005. Documentation only. No production file was changed. No test was changed. No dependency file was changed. No `TSK-###` was created. Nothing in this record marks a requirement Implemented.

Decisions recorded: [DEC-064](DECISIONS.md#dec-064) through [DEC-076](DECISIONS.md#dec-076). Later-update notes on earlier decisions state the relationship. [DEC-041](DECISIONS.md#dec-041)'s stage list is no longer the current pipeline description. [DEC-042](DECISIONS.md#dec-042)'s permission for an internal score, and for a future statistically justified numeric confidence, remains and is unused for Candidate Resolution v0.1.

The Strong Physical Type phase remains complete. At consolidation, TSK-001 through TSK-005 were the only completed implementation slices. The consolidated architecture covers observations, candidate assessments, resolution, material alternatives, High / Medium / Low confidence, inferred versus effective interpretation, and compute-once evidence. Heuristic semantic inference is not authorized. The next implementation slice was not selected at that point ([OPEN-037](DECISIONS.md#open-questions)). TSK-006 was approved later. TSK-007 was approved after that. TSK-008 was approved after that. TSK-009 was approved after that. TSK-010 was approved after that. TSK-011 was approved after that. TSK-012 was approved after that. TSK-013 was approved after that. TSK-014 was approved after that. TSK-015 was approved after that. See those records in the task log.

Still open, among others: [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049). TSK-014 later narrowed [OPEN-047](DECISIONS.md#open-047): resolution can abstain, and the inferred-interpretation representation of that status remained open. TSK-015 then recorded that representation. Candidate-derived confidence, material alternatives, and the public result remain open.

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
| REQ-S-01 | Infer a semantic type. The minimum concepts are Numeric, Categorical, Boolean/Binary, Text/String, Datetime, Timedelta, Identifier, Constant, and Empty. Empty and Constant are also dataset facts. | Not started | TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-014, TSK-015 | — | — | Not completed. TSK-001 can represent the minimum types. TSK-002 infers Empty and Constant only. TSK-003 also infers Boolean from a physical Boolean dtype after those two rules. TSK-004 also infers Datetime from a native or timezone-aware datetime dtype after those three rules. TSK-005 also infers Timedelta from a physical timedelta dtype after those four rules. It does not infer Timedelta from strings, numbers, objects, categoricals, or periods. It does not infer Datetime from strings or other storage, the other minimum types, other Boolean representations, duration analysis, or dataset facts. TSK-006 adds no semantic reading. TSK-007 adds no semantic reading. TSK-008 adds no semantic reading. TSK-009 adds no semantic reading. TSK-010 adds no semantic reading. TSK-011 assesses an Identifier candidate and does not select Identifier or any other reading. TSK-012 assesses Numeric, Categorical, and Text candidates and does not select any of them. TSK-013 adds token and vocabulary observations and does not select a reading. TSK-014 resolves a structural reading or exactly one supported candidate. It does not build a confidence-bearing interpretation for that candidate, and the precedence chain does not call it. TSK-015 records the inferred state for that resolution and the observed physical dtype. It keeps a structural interpretation and does not build a confidence-bearing interpretation for a candidate-derived selection. The precedence chain does not build that state. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-02 | Retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source of interpretation. User-facing confidence is High, Medium, or Low, with concrete evidence. Do not present pseudo-precise confidence. | Not started | TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-014, TSK-015 | — | — | Not completed. TSK-001 can store a reading. TSK-002 stores type, High confidence, one evidence statement, inferred source, and physical dtype for Empty and Constant only. TSK-003 does the same for physical Boolean, with source physical dtype. TSK-004 does the same for physical Datetime. Timezone-aware storage keeps its own evidence statement and its physical family. TSK-005 does the same for physical Timedelta. Its evidence statement is `physical dtype is timedelta`. TSK-014 keeps that confidence when a structural interpretation resolves, and does not assign High, Medium, or Low to a candidate-derived selection. TSK-015 keeps that same structural confidence and still does not assign High, Medium, or Low to a candidate-derived selection. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-03 | Do not silently clean, repair, coerce, or mutate the original DataFrame. Preserve the distinction between source representation and analytical interpretation. Pattern detection must not rewrite the source Series. | Not started | TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-013 | — | — | Not completed. TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 do not mutate the Series they read. TSK-002, TSK-006, and TSK-007 do not treat missing-like strings as missing. TSK-004 does not parse strings or coerce them to datetime. TSK-005 does not parse strings or coerce them to timedelta. TSK-008 does not parse numeric strings or coerce them with `pd.to_numeric`. TSK-009 does not stringify, strip, or Unicode-normalize strings, and it does not decode byte strings. TSK-010 does not strip, case-fold, Unicode-normalize, stringify, or decode strings before a full-value pattern match. TSK-013 does not strip, case-fold, Unicode-normalize, or decode strings before counting alphanumeric runs. The requirement covers the product, not only these paths. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-04 | Make inference evidence-driven and transparent, and expose uncertainty. A column name may support an inference and must not determine semantic type by itself. | Not started | TSK-002, TSK-003, TSK-004, TSK-005, TSK-014, TSK-015 | — | — | Not completed. TSK-002 decides Empty and Constant from basic counts and does not use the column name. TSK-003 decides physical Boolean from the dtype family after those counts, and does not use the column name or cardinality. TSK-004 decides physical Datetime from the dtype family after those rules, and does not use the column name or parse values. TSK-005 decides physical Timedelta from the dtype family after those rules, and does not use the column name, parse values, or guess units. TSK-006 does not add a reading. TSK-007 records frequency observations and does not add a reading. TSK-008 records numeric-structure observations and does not add a reading. TSK-009 records string-structure observations and does not add a reading. TSK-010 records pattern observations and does not add a reading. TSK-011 assesses an Identifier candidate from observations already collected. It does not resolve a reading, assign High, Medium, or Low, or use the column name. It does not implement the rest of evidence-driven inference. TSK-012 assesses Numeric, Categorical, and Text candidates from observations already collected. It does not resolve a reading, assign High, Medium, or Low, invent a cardinality or length threshold, or use the column name. TSK-013 records token and vocabulary observations and does not invent a token-count, vocabulary, or length threshold, and does not use the column name. TSK-014 resolves assessments already produced. It does not invent a threshold, assign High, Medium, or Low to a candidate-derived selection, or use a column name. TSK-015 records abstention and ambiguity as inferred states and does not invent confidence from candidate counts or evidence quantity. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-05 | Distinguish physical dtype, observed characteristics, and semantic interpretation. Keep the original physical dtype inspectable. | Not started | TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015 | — | — | Not completed. TSK-001 classifies physical dtype. TSK-002 collects four exact basic counts and keeps that physical dtype on Empty and Constant interpretations. TSK-003 keeps it on physical Boolean interpretations. TSK-004 keeps it on physical Datetime interpretations, including the timezone-aware family. TSK-005 keeps it on physical Timedelta interpretations and does not add duration-unit metadata. TSK-006 keeps those four counts as stored primary observations and adds derived ratios and boolean facts computed from them. TSK-007 adds exact frequency observations composed with those counts. TSK-008 adds exact numeric-structure observations for physical integer and floating columns, composed with those counts. TSK-009 adds exact string-structure observations for physical string columns and for eligible object columns, composed with those counts. TSK-010 adds exact full-value pattern observations composed with that string-structure evidence. TSK-011 adds an Identifier candidate assessment that consumes those observations and does not select a reading. It does not collect the rest of the observed characteristics. TSK-012 adds Numeric, Categorical, and Text candidate assessments that consume those observations and do not select a reading. TSK-013 adds exact string-content observations composed with string-structure evidence and does not select a reading. TSK-014 keeps resolution distinct from those observations and from a confidence-bearing interpretation. TSK-015 keeps the supplied physical dtype on the inferred result and does not derive it from the semantic type. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-06 | Treat explicit per-variable semantic configuration as a first-class capability. User intent normally takes precedence. If a configured interpretation cannot be meaningfully applied, report the conflict instead of silently coercing. The exact API is not frozen. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-07 | Give Timedelta dedicated duration analysis that preserves duration semantics and readable units. Do not present user-facing timedelta results as raw nanoseconds. | Not started | TSK-005 | — | — | Not completed. TSK-005 can read a physical timedelta dtype as Timedelta. It does not analyze durations, choose display units, or present statistics. The requirement covers duration analysis, not only this reading. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-08 | Do not infer ordinal ordering from category labels. Accept ordinal semantics only when the user configures them or the source explicitly represents order. | Not started | TSK-012 | — | — | Not completed. TSK-012 does not infer order from labels. An ordered pandas categorical dtype can support a Categorical candidate and keeps `categorical_ordered` on the physical dtype. No Ordinal type was added. Ordinal storage stays open. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
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
| REQ-D-02 | Do not treat binary cardinality as Boolean meaning. Do not treat every {0, 1} column as Boolean. Keep arbitrary two-category variables categorical. | Not started | TSK-003 | — | — | Not completed. TSK-003 does not treat two distinct values, `{0, 1}`, Boolean-like strings, or categorical booleans as Boolean. TSK-012 does not treat `{0, 1}` numeric storage as Boolean. It may support a Numeric candidate for that storage. It does not yet support two string labels as Categorical, because no vocabulary rule is approved. TSK-013 records token evidence and still does not approve that rule. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-03 | Record confidence and reason for a boolean or binary inference. | Not started | TSK-003 | — | — | Not completed. TSK-003 records High confidence and one factual evidence statement for a physical Boolean reading. It does not cover other boolean or binary readings. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-01 | Earliest, latest, range or span, missingness, distinct values, duplicate timestamps, timezone, and inferred resolution. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-02 | Monotonicity, gaps, irregular intervals, frequency, relevant calendar distributions, and time-structure signals. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-03 | Distinguish a column that contains dates from an actual time-series structure. | Not started | TSK-004 | — | — | Not completed. TSK-004 can read a physical datetime dtype as Datetime and does not treat that reading as a time series. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-04 | Do not indiscriminately run deeper time-series diagnostics on every datetime column. | Not started | TSK-004 | — | — | Not completed. TSK-004 does not run monotonicity, frequency, gap, calendar, trend, seasonality, or autocorrelation analysis. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-01 | Distinguish the string roles listed above. | Not started | TSK-012, TSK-013 | — | — | Not completed. TSK-012 does not support a Text candidate from current observations, and it does not support Categorical for ordinary strings. TSK-013 adds token and vocabulary observations and still does not support either candidate for ordinary strings. String roles are not distinguished. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-02 | Text diagnostics covering count, missing, distinct, empty strings, whitespace-only values, length statistics and distribution, word counts, leading or trailing whitespace, line breaks, Unicode or non-ASCII characteristics, pattern consistency, and duplicate text. | Not started | — | — | — | Not completed. TSK-009 records empty-string counts, whitespace counts, character-class counts, and minimum and maximum length. TSK-010 records full-value UUID, IPv4, IPv6, and fixed-width hexadecimal counts. Neither records a length distribution, word counts, leading or trailing whitespace as a separate fact, line-break diagnostics, pattern consistency, or duplicate text. TSK-012 does not add those diagnostics and does not treat the current string facts as a Text candidate. TSK-013 records alphanumeric token counts, total character count, and aggregate token-vocabulary counts. It does not record a length distribution, leading or trailing whitespace as a separate fact, line breaks, downstream common-token diagnostics, or a Text candidate. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-03 | Pytics core must not become a full NLP platform. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-01 | Treat Identifier as a first-class semantic concept. | Not started | — | — | — | Not completed. TSK-011 can record an Identifier candidate. It does not select Identifier and does not complete this requirement. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-02 | Expose the evidence and reasoning for identifier detection. | Not started | — | — | — | Not completed. TSK-011 preserves a concrete syntax statement when an Identifier candidate is supported. It does not resolve detection and does not complete this requirement. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-03 | Normally exclude identifiers from ordinary correlation, diagnostic target modeling, and ordinary multivariate anomaly modeling, unless explicitly configured otherwise. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-01 | Report dataset-level, variable-level, and row-level missingness. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-02 | Report missingness patterns and co-missingness. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-03 | Report relationships between missingness and other variables. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-04 | Report missing-like literals such as `""`, whitespace, `"N/A"`, `"null"`, and `"?"`. Do not silently rewrite them as missing data. | Not started | — | — | — | Not completed. TSK-009 keeps those literals as ordinary strings and can count an empty string or a whitespace-only string as structure. It does not report a missing-like literal diagnostic and does not define the literal list. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
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

Total rows: 119. Not started: 110. In force: 9. Implemented, verified, and completed: 0. Completed tasks: TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, and TSK-015. Those tasks do not complete a requirement row.

## Items deliberately absent from this register

The following are not requirements and must not be given tasks until a decision accepts them:

- module and file layout, and concrete result-class or signature names ([OPEN-045](DECISIONS.md#open-questions), [OPEN-004](DECISIONS.md#open-questions));
- exact `quick` / `standard` / `deep` contents, thresholds, and sample sizes ([OPEN-010](DECISIONS.md#open-questions));
- the configuration-object shape ([OPEN-009](DECISIONS.md#open-questions));
- the closed statistical method catalog, effect-size formulas, and the multiple-testing family ([OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions));
- the method-registry schema and API ([OPEN-039](DECISIONS.md#open-questions));
- semantic-inference thresholds beyond the initial full-population Identifier candidate rule ([DEC-082](DECISIONS.md#dec-082)) and beyond the physical-storage Numeric and Categorical candidate rules ([DEC-083](DECISIONS.md#dec-083)), including Categorical vocabulary thresholds, Text length and whitespace thresholds, positive-evidence checklists, Identifier uniqueness thresholds, partial-pattern thresholds, numeric sequence Identifier evidence, and whether any pattern fact can select Identifier ([OPEN-044](DECISIONS.md#open-questions));
- the subtype taxonomy, Binary representation, and unresolved string roles ([OPEN-014](DECISIONS.md#open-questions));
- `{0.0, 1.0}` as binary-candidate evidence ([OPEN-046](DECISIONS.md#open-046));
- candidate-derived confidence, material alternatives on a selected reading, and the public representation of abstention and ambiguity ([OPEN-047](DECISIONS.md#open-047), [OPEN-044](DECISIONS.md#open-questions));
- an evidence-strength enum ([OPEN-048](DECISIONS.md#open-048));
- exact Empty or Constant override behavior, and the override result and configuration representation ([OPEN-049](DECISIONS.md#open-049), [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions));
- trimmed mean and common-token diagnostics ([OPEN-019](DECISIONS.md#open-questions));
- fuzzy or near-duplicate analysis, and the scope of deep time-series diagnostics ([OPEN-020](DECISIONS.md#open-questions));
- the diagnostic estimator family and the anomaly estimator ([OPEN-013](DECISIONS.md#open-questions), [OPEN-022](DECISIONS.md#open-questions));
- finding level names ([OPEN-025](DECISIONS.md#open-questions));
- dark mode as a committed feature ([OPEN-026](DECISIONS.md#open-questions));
- a 2.0 dependency lock or version pins ([OPEN-042](DECISIONS.md#open-questions)).

Migration mechanics are decided ([DEC-063](DECISIONS.md#dec-063)). They are not a requirement row. The denominator of `unique_ratio_non_missing` is decided ([DEC-077](DECISIONS.md#dec-077)). The frequency-observation contract, including its ratio denominators and the operational 32-value retention limit, is decided ([DEC-078](DECISIONS.md#dec-078)). The numeric-structure contract, including its ratio denominators and its integer-like and monotonicity rules, is decided ([DEC-079](DECISIONS.md#dec-079)). The string-structure contract, including native string applicability, conditional object applicability, character classes, length bounds, and ratio denominators, is decided ([DEC-080](DECISIONS.md#dec-080)). The pattern contract, including full-value UUID, IPv4, IPv6, and fixed-width ASCII hexadecimal counts, allowed overlap, and the non-missing denominator, is decided ([DEC-081](DECISIONS.md#dec-081)). The candidate-assessment contract, including support versus contradiction and the initial full-population Identifier candidate rule, is decided ([DEC-082](DECISIONS.md#dec-082)). The Numeric, Categorical, and Text candidate rules are decided ([DEC-083](DECISIONS.md#dec-083)). None of those is an open item above. The retention limit is not a semantic cardinality threshold. Integer-like counts and monotonicity flags are not Identifier, Discrete, or Binary rules. String-structure counts and length bounds are not Text, Categorical, or Identifier rules. Pattern counts are not a selected Identifier, Text, or Categorical reading. A full-population UUID or same-width hexadecimal count may support an Identifier candidate and does not select Identifier. Physical integer or floating storage may support a Numeric candidate and does not select Numeric. Physical categorical storage may support a Categorical candidate and does not select Categorical. Current string observations do not support a Text candidate. The resolution contract is decided ([DEC-085](DECISIONS.md#dec-085)). The inferred-result contract is decided ([DEC-086](DECISIONS.md#dec-086)). Resolution may select Identifier, Numeric, or Categorical when that candidate is the only one supported. The inferred result keeps that selection and the observed physical dtype, and it does not assign High, Medium, or Low. Partial-pattern thresholds, Categorical vocabulary thresholds, Text length thresholds, and candidate-derived confidence remain open.

The engine diagram, the three mode names, the shared statistical layer, the method-registry concept, DataFrame-only input, held-out permutation importance, the candidate dependency directions, and the semantic-foundation pipeline in DEC-064 through DEC-076 are accepted. Acceptance is not a task and not an implementation. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, and TSK-015 are the only implementation tasks. TSK-015 records an inferred result after resolution. It does not implement those engines, a user override, or an effective interpretation. The next implementation slice has not been selected.
