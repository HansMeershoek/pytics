# Technical architecture

This file records accepted architectural direction and the constraints that already bind.

No production code is authorized by this document. See [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md).

The diagram is direction. It is not a class hierarchy, a module map, or a file layout ([DEC-036](DECISIONS.md#dec-036), [OPEN-045](DECISIONS.md#open-questions)).

## Accepted constraints

| ID | Constraint | Status |
| --- | --- | --- |
| REQ-T-01 | Analytical code must not directly generate HTML. An analyzer takes inputs such as a series, semantic schema, and configuration, and returns a structured result. | Accepted |
| REQ-T-02 | HTML and PDF renderers consume structured result models. They are not the place where statistics are defined. | Accepted |
| REQ-T-03 | The method-registry concept is accepted. Do not implement the registry until its schema and API are decided. | Accepted as a hold |
| REQ-T-04 | Do not install or pin a Pytics 2.0 dependency lock. Candidate directions from the ecosystem review are not that lock. | Accepted as a hold |
| REQ-T-05 | Reuse one statistical layer for general relationships, target analysis, missingness relationships, dataset comparison, and drift wherever analytically appropriate. Do not implement separate statistical truths for those uses. The exact internal API is not frozen. | Accepted |

These restate product rules that also bind the architecture:

- pandas DataFrames only (`REQ-P-06`, [DEC-040](DECISIONS.md#dec-040));
- semantic-first, without silent coercion or mutation (`REQ-S-01` through `REQ-S-09`);
- structured results rather than rendered strings as the analytical output (`REQ-P-14`, `REQ-T-01`);
- evidence-based findings (`REQ-N-01`);
- reproducibility and visible sampling (`REQ-P-12`, `REQ-IA-15`, [DEC-054](DECISIONS.md#dec-054)).

Structured results are Accepted. A specific type system, class hierarchy, or attribute spelling is not ([OPEN-004](DECISIONS.md#open-questions)).

## Architectural direction

Status: **Accepted** as direction ([DEC-036](DECISIONS.md#dec-036)). This replaces the bootstrap sketch. That sketch is not a second active proposal.

```text
                         PUBLIC API
                   profile() / compare()
                              |
                              v
                    INPUT VALIDATION
                              |
                              v
                     SEMANTIC ENGINE
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
       DATA ANALYSIS      RELATIONSHIPS    DATA QUALITY
             |                |                |
             +----------------+----------------+
                              |
                              v
                    STATISTICAL ENGINE
                              |
                +-------------+-------------+
                |                           |
                v                           v
          Frequentist                   Bayesian
                |                           |
                +-------------+-------------+
                              |
                              v
                     SPECIAL ANALYSES
                Target / Anomaly / Drift /
                     temporal analysis
                              |
                              v
                       FINDINGS ENGINE
                              |
                              v
                        RESULT MODEL
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
         Python API          HTML             PDF
```

`compare()` is a public entry point. Drift is a special analysis that compare can use. It is not a second statistical implementation (`REQ-T-05`).

The same diagram is recorded in [DEC-036](DECISIONS.md#dec-036). If the two copies diverge, that is a documentation defect. The decision is the ruling. This file is the architecture description.

| Principle | Classification |
| --- | --- |
| Pandas-native, DataFrame-only | Accepted (`REQ-P-06`, [DEC-040](DECISIONS.md#dec-040)) |
| Semantic-first | Accepted (`REQ-S-*`) |
| Analysis/render separation | Accepted (`REQ-T-01`, `REQ-T-02`) |
| Structured results | Accepted. Concrete types not finalized ([OPEN-004](DECISIONS.md#open-questions)). |
| Shared statistical capabilities | Accepted (`REQ-T-05`, [DEC-037](DECISIONS.md#dec-037)). Internal API not finalized ([OPEN-038](DECISIONS.md#open-questions)). |
| Evidence-based findings | Accepted (`REQ-N-*`) |
| Analysis modes | Accepted as a concept ([DEC-058](DECISIONS.md#dec-058)). Contents not finalized ([OPEN-010](DECISIONS.md#open-questions)). |
| Reproducibility and transparency | Accepted (`REQ-P-12`, `REQ-IA-14`, `REQ-IA-15`) |

The bootstrap sketch listed "progressive computation" as a proposed principle. That phrase is not part of the accepted direction. Analysis modes are the accepted depth concept. No separate progressive-computation design is accepted.

## Semantic inference

The semantic engine in the diagram above follows the conceptual pipeline in [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) ([DEC-064](DECISIONS.md#dec-064)). That pipeline is not a module map. [OPEN-045](DECISIONS.md#open-questions) stays open. The labels are not class names. If this file and [DEC-064](DECISIONS.md#dec-064) diverge on the pipeline, the decision is the ruling.

```text
PHYSICAL DTYPE
      ↓
OBSERVATIONS / EVIDENCE
      ↓
CANDIDATE ASSESSMENTS
      ↓
RESOLUTION
      ↓
INFERRED INTERPRETATION
      ↓
OPTIONAL USER OVERRIDE
      ↓
EFFECTIVE INTERPRETATION
      ↓
DOWNSTREAM ANALYSIS
```

Observations and candidate assessments are distinct ([DEC-065](DECISIONS.md#dec-065)). Absence of a supporting observation is not contradicting evidence. Candidate Resolution v0.1 does not use a numeric total-score ([DEC-066](DECISIONS.md#dec-066)). User-facing confidence remains High, Medium, or Low. The resolution foundation does not derive those words from how many candidates are supported ([DEC-085](DECISIONS.md#dec-085)). The inferred result does not derive them either ([DEC-086](DECISIONS.md#dec-086)). One internal function now runs that column path from a Series through the inferred result ([DEC-087](DECISIONS.md#dec-087)). A DataFrame analysis calls that same path once per physical column and retains the evidence ([DEC-088](DECISIONS.md#dec-088)). Both stop before the optional override, the effective interpretation, and downstream analysis. They do not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

Evidence is collected once and then interpreted ([DEC-076](DECISIONS.md#dec-076)). The levels below are conceptual cost, not a cache API and not a file layout. If this list and that decision diverge, the decision is the ruling.

```text
LEVEL 0 — physical metadata
LEVEL 1 — cheap universal evidence
LEVEL 2 — type-family evidence
LEVEL 3 — candidate-specific evidence
LEVEL 4 — expensive/deep evidence
```

Shared observations, including missingness, value counts, string lengths, patterns, and monotonicity, should be reusable across candidate assessments. Procedure provenance belongs with the evidence. Fields for exact versus sampled collection, sample size, population size, seed, and method are not frozen. Sampling can affect confidence. It does not decide whether an interpretation is true. Sample sizes remain [OPEN-010](DECISIONS.md#open-questions). The universal counts `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing` are exact, full-column, and unsampled ([DEC-077](DECISIONS.md#dec-077)). Frequency evidence, numeric-structure evidence, string-structure evidence, pattern evidence, and string-content evidence are also exact, full-column, and unsampled, and each is collected only when requested ([DEC-078](DECISIONS.md#dec-078), [DEC-079](DECISIONS.md#dec-079), [DEC-080](DECISIONS.md#dec-080), [DEC-081](DECISIONS.md#dec-081), [DEC-084](DECISIONS.md#dec-084)). None of those procedures carries a provenance object. A reusable provenance model waits until a procedure can vary, such as sampled evidence.

The current `SemanticAlternative` value is thinner than the material-alternative requirement in [DEC-067](DECISIONS.md#dec-067). The consolidation did not redesign it. `None` from the implemented precedence chain is control flow, not an ambiguity state. User override is direction only ([DEC-075](DECISIONS.md#dec-075)). The renderer does not choose a second semantic reading ([DEC-025](DECISIONS.md#dec-025)). Heuristic Binary inference waits until a binary-not-Boolean reading can be represented ([DEC-074](DECISIONS.md#dec-074), [OPEN-014](DECISIONS.md#open-questions)). Some roles need dataset context the column does not contain ([DEC-073](DECISIONS.md#dec-073)). That reservation is not permission to implement cross-column inference.

## Illustrative result shapes

Status: **not accepted**. Do not implement these classes or attribute names as if they were frozen ([OPEN-004](DECISIONS.md#open-questions)).

```text
ProfileReport
  dataset
  schema
  variables
  missing
  duplicates
  anomalies
  relationships
  target
  time_series
  findings
  methods
  metadata
```

```text
ComparisonReport
  left
  right
  schema_changes
  variable_changes
  missing_changes
  distribution_changes
  relationship_changes
  target_changes
  drift
  findings
  methods
  metadata
```

The profile shape and the compare information architecture are related but not the same list. Compare navigation also has duplicates. The sketch above has no `duplicate_changes` field. That mismatch inside the illustration is unresolved ([OPEN-004](DECISIONS.md#open-questions)).

## Shared statistics

General relationships, target analysis, missingness relationships, dataset comparison, and drift reuse one statistical layer wherever that is analytically appropriate ([DEC-037](DECISIONS.md#dec-037), `REQ-T-05`).

Target-specific behavior sits on top of that layer: target distribution, imbalance, the diagnostic model, and potential leakage ([DEC-059](DECISIONS.md#dec-059)). TSK-032 is the first of that behavior. It projects an explicit target onto retained descriptive facts and retained relationship records. It does not add the diagnostic model ([DEC-103](DECISIONS.md#dec-103)). TSK-033 adds the exact observed Categorical distribution to that descriptive layer and has the projection reuse it ([DEC-104](DECISIONS.md#dec-104)). It does not add an imbalance verdict or the diagnostic model. TSK-034 adds the diagnostic model ([DEC-105](DECISIONS.md#dec-105)). It is target-specific and is not part of the shared relationship layer. It does not read or recompute relationship records, and the relationship layer does not read it.

The exact internal API is [OPEN-038](DECISIONS.md#open-questions).

## Method registry

The registry concept is accepted ([DEC-038](DECISIONS.md#dec-038)). Its purpose is a central, inspectable description of methods and their applicability. An entry may eventually carry a stable identifier, name, purpose, applicable semantic types, assumptions, parameters, limitations, computational characteristics, references, and the modes in which the method is available. That list is not a schema.

Do not implement the registry until the schema and API are decided (`REQ-T-03`, [OPEN-039](DECISIONS.md#open-questions)).

## Core value models

Accepted ([DEC-062](DECISIONS.md#dec-062)). Core analytical result and value models use frozen dataclasses, enums, and explicit type hints where those objects are analytical facts. Pydantic is not required. Dictionaries and TypedDict-only structures are not the preferred representation for those facts. Do not freeze mutable orchestration or configuration objects before they exist. This does not freeze public result-class names ([OPEN-004](DECISIONS.md#open-questions)).

TSK-001 placed the first of these objects under `src/pytics/semantics/`. TSK-002 added `BasicColumnEvidence` there, as an exact observed-characteristic fact, and Empty/Constant interpretations that reuse the Slice 001 physical classifier. TSK-003 composes those rules with one further reading: semantic Boolean when the physical family is Boolean and the column is neither Empty nor Constant. That Boolean reading uses the physical dtype as its source. Object, categorical, numeric, and string values are not read as Boolean. TSK-004 calls that chain and then reads semantic Datetime when the physical family is native datetime or timezone-aware datetime. Both families stay distinct on the physical dtype. The composition is one successor function, not a rule registry. String, object, integer, categorical, timedelta, and period values are not read as Datetime. TSK-005 calls that precedence and then reads semantic Timedelta when the physical family is timedelta. Datetime stays a point in time. Timedelta stays a duration. String, object, numeric, categorical, and period values are not read as Timedelta. That step is one further successor call plus one explicit branch, not a rule registry. Those modules are internal. That location does not resolve [OPEN-045](DECISIONS.md#open-questions). The physical classifier names storage families only. Ordinal storage remains [OPEN-016](DECISIONS.md#open-questions). The subtype taxonomy remains [OPEN-014](DECISIONS.md#open-questions). Inference thresholds remain [OPEN-044](DECISIONS.md#open-questions).

The semantic-foundation consolidation did not change these modules. `SemanticAlternative` still records a type, an optional subtype label, and an optional confidence. It does not carry the alternative's evidence. `None` still means the implemented precedence chain produced no interpretation. TSK-014 adds resolution beside that chain ([DEC-085](DECISIONS.md#dec-085)). The chain does not call it. A binary-not-Boolean reading is not implemented. User overrides are not implemented. `categorical_ordered` remains physical metadata when Empty or Constant wins.

TSK-006 keeps `BasicColumnEvidence` as the universal family ([DEC-077](DECISIONS.md#dec-077)). The four counts stay the stored fields. `missing_ratio`, `unique_ratio_non_missing`, `has_missing`, `is_empty`, and `is_constant` are computed from them and are not stored. Empty and Constant read `is_empty` and `is_constant`. The composed chain still classifies the physical dtype once and collects the four counts once. That location still does not resolve [OPEN-045](DECISIONS.md#open-questions). `unique_ratio_non_missing` does not close Identifier thresholds ([OPEN-044](DECISIONS.md#open-questions)).

TSK-007 adds `FrequencyEvidence` in the same internal package ([DEC-078](DECISIONS.md#dec-078)). It is composed with `BasicColumnEvidence` and is not a subclass. Frequency facts cover non-missing values only. Ratios use the basic counts as denominators. The exact distinct values are retained only up to an operational storage limit of 32. That limit is not a semantic threshold. The precedence chain does not collect this family. Collecting an observation once, when it is needed, is not the same as computing every observation eagerly. No semantic reading was added.

TSK-008 adds `NumericStructureEvidence` in the same internal package ([DEC-079](DECISIONS.md#dec-079)). It is composed with `BasicColumnEvidence` and is not a subclass. It applies only to physical integer and floating storage. Boolean storage is excluded. The counts describe finite values, signs, infinities, and exact integer-like values. Monotonicity is recorded only when every non-missing value is finite. Ratios use those counts and the basic non-missing count as denominators. The family is exact, full-column, and unsampled. The precedence chain does not collect it. No descriptive numeric summary and no semantic reading were added.

TSK-009 adds `StringStructureEvidence` in the same internal package ([DEC-080](DECISIONS.md#dec-080)). It is composed with `BasicColumnEvidence` and is not a subclass. A physical string dtype is eligible, including an all-missing string column. An object column is eligible only when every non-missing value is a Python `str`. An all-missing object column is not eligible. Categorical storage is not eligible. The counts describe empty strings, whitespace, and alphabetic, digit, and other characters, using Python's Unicode string methods. Length bounds use `len` of the original string and are undefined when there is no non-missing string. Ratios use `n_non_missing` as the denominator. The family is exact, full-column, and unsampled. The precedence chain does not collect it. No word count, pattern name, or semantic reading was added.

TSK-010 adds `PatternEvidence` in the same internal package ([DEC-081](DECISIONS.md#dec-081)). It is composed with `StringStructureEvidence` and is not a subclass. Eligibility comes from that prior evidence. The collector checks population consistency and does not recollect string structure. Counts describe full-value UUID, IPv4, IPv6, and ASCII hexadecimal tokens of widths 32, 40, 64, and 128. A compact UUID may increment both the UUID count and the 32-character count. Ratios use `n_non_missing` as the denominator. The family is exact, full-column, and unsampled. The precedence chain does not collect it, and string-structure collection does not collect it either. No semantic reading was added.

TSK-011 adds `CandidateAssessment` in the same internal package ([DEC-082](DECISIONS.md#dec-082)). It names one `SemanticType`, a disposition of supported, not supported, or contradicted, and separate supporting and contradicting statements. It is not a `SemanticInterpretation`. It has no score and no High, Medium, or Low confidence. The first assessor reads an Identifier candidate from evidence already collected. A full non-missing population of UUID syntax, or of one supported hexadecimal width, can support that candidate. Uniqueness, missingness, partial patterns, IP syntax, and numeric monotonicity cannot. Empty and Constant stay unsupported for the candidate. The precedence chain does not call the assessor. No reading is selected. That location still does not resolve [OPEN-045](DECISIONS.md#open-questions).

TSK-012 adds Numeric, Categorical, and Text assessors on that same value ([DEC-083](DECISIONS.md#dec-083)). It does not add a specialized assessment type. Non-empty, non-constant physical integer or floating storage can support Numeric. Non-empty, non-constant physical categorical storage can support Categorical. Ordered metadata stays on the physical dtype. Current observations do not support Text. Empty and Constant stay unsupported for each candidate, without a contradiction. The assessors do not force one reading to exclude another. They consume evidence already collected and are not called by the precedence chain. No reading is selected. No cardinality, length, or whitespace threshold was added. That location still does not resolve [OPEN-045](DECISIONS.md#open-questions).

TSK-013 adds `StringContentEvidence` in the same internal package ([DEC-084](DECISIONS.md#dec-084)). It is composed with `StringStructureEvidence` and is not a subclass. Eligibility comes from that prior evidence. The collector checks population consistency and does not recollect string structure or whole-value frequency. A token is a maximal Unicode alphanumeric run. Stored facts are the token partition of non-missing strings, the total token count, the total character count, and aggregate distinct, singleton, and most-frequent token counts. No raw vocabulary is retained. Ratios use the denominators in that decision. The family is exact, full-column, and unsampled. The precedence chain does not collect it. Those facts do not support Text or ordinary-string Categorical. No token-count or vocabulary threshold was added. No semantic reading was added. That location still does not resolve [OPEN-045](DECISIONS.md#open-questions).

TSK-014 adds `SemanticResolution` in the same internal package ([DEC-085](DECISIONS.md#dec-085)). It is a frozen resolution result, not a semantic type and not a `SemanticInterpretation` for a candidate-derived selection. `resolve_semantics` takes an optional structural interpretation and candidate assessments already produced. Empty, Constant, Boolean, Datetime, and Timedelta resolve before those candidates. Exactly one supported candidate selects that semantic type without assigning confidence. No supported candidate is insufficient evidence. More than one supported candidate is ambiguous. A contradicted candidate does not veto another supported candidate. Duplicate semantic types are rejected. Input order does not change the result. The function does not collect observations and does not import pandas. `interpret_series_precedence` does not call it. No override, eligibility rule, threshold, or numeric total was added. That location still does not resolve [OPEN-045](DECISIONS.md#open-questions).

TSK-015 adds `InferredSemanticResult` in the same internal package ([DEC-086](DECISIONS.md#dec-086)). It stores the observed physical dtype and the resolution already produced. A structural resolution keeps that interpretation, including its confidence and source. The supplied physical dtype must match it. A candidate-derived resolution stays resolved at the selected type and does not receive a `SemanticInterpretation`, because no High, Medium, or Low confidence is justified. Insufficient evidence and ambiguity are inferred states with no interpretation and no selected type. The constructor does not collect observations, assess candidates, or call the resolver. The precedence chain does not call it. No override, effective interpretation, eligibility rule, or public result was added. That location still does not resolve [OPEN-045](DECISIONS.md#open-questions).

TSK-016 connects those components for one Series ([DEC-087](DECISIONS.md#dec-087)). TSK-017 keeps one column orchestration, `analyze_series`, and returns the existing inferred result from `infer_series_semantics` ([DEC-088](DECISIONS.md#dec-088)). The column record retains physical dtype, the evidence that path collected, and the inferred result. It does not enlarge `InferredSemanticResult`. A DataFrame analysis stores row, column, and cell counts and one column record per physical column, in source order, including duplicate and non-string labels. Missing-cell totals are derived from retained basic evidence. String-content evidence is not collected. Frequency evidence was not collected in that slice. [DEC-090](DECISIONS.md#dec-090) later retains it for a non-structural physical categorical column. The DataFrame and its Series are not stored. `profile` and `compare` are unchanged. `pytics.semantics` owns semantic inference. `pytics.analysis` owns these records and the DataFrame traversal. That split narrows [OPEN-045](DECISIONS.md#open-questions) and does not freeze the rest of the layout.

TSK-018 adds `build_dataset_overview` in `pytics.analysis` ([DEC-089](DECISIONS.md#dec-089)). It accepts the dataset analysis already produced and returns a frozen overview. It copies row, column, and cell counts and the missing-cell totals. It counts each resolved selected semantic type, and it names Empty, Constant, Identifier, insufficient-evidence, and ambiguous columns by position and original label. It does not import pandas, rescan values, or choose a semantic type. Candidate-derived selections count without a confidence-bearing interpretation. Cell completeness and semantic-resolution coverage are separate ratios, each undefined when its denominator is zero. Memory usage and duplicate rows are not defined here and are not computed. The overview is not rendered and is not exported from top-level `pytics`. `profile` and `compare` are unchanged. `overview.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-019 adds `build_variables_summary` in `pytics.analysis` ([DEC-090](DECISIONS.md#dec-090)). It accepts the dataset analysis already produced and returns one frozen variable summary per physical column, in source order. Common counts come from retained basic evidence. Specialized detail follows the selected semantic type: numeric-structure counts for Numeric, frequency counts for Categorical, and pattern counts for Identifier. Other selected types had no specialized detail in that slice. [DEC-092](DECISIONS.md#dec-092) later adds Boolean true and false counts. Unresolved and ambiguous columns still have no specialized detail. The builder does not import pandas and does not rescan values. Frequency evidence stays an observation in `pytics.semantics` and is now collected for non-structural physical categorical columns. The variables summary is not rendered and is not exported from top-level `pytics`. `profile` and `compare` are unchanged. `variables.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-020 adds `NumericDescriptiveAnalysis` in `pytics.analysis` ([DEC-091](DECISIONS.md#dec-091)). It is not semantic evidence and not a field of the inferred result. `analyze_series` collects it only after resolution, and only when the selected semantic type is Numeric. The population is the finite non-missing values. Sample standard deviation uses `ddof=1`. Q1, the median, and Q3 share one linear interpolation. The variables builder copies the frozen result onto Numeric detail and does not calculate it. Constant numeric columns are not described. No semantic rule changed. TSK-025 resolves the two float64 limits of this pass ([DEC-096](DECISIONS.md#dec-096)). A non-representable mean, sample standard deviation, range, or interquartile range is `None` and does not raise. Integer extrema stay exact. A large-integer sample deviation is centered before the float64 cast, so distinct integers do not become a false zero deviation solely because of their magnitude. `numeric.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-021 adds `BooleanDescriptiveAnalysis` in `pytics.analysis` ([DEC-092](DECISIONS.md#dec-092)). It is not semantic evidence and not a field of the inferred result. `analyze_series` collects it only after resolution, and only when the selected semantic type is Boolean. `True` and `False` are counted separately. Missing values are excluded. The ratios use the non-missing count. The variables builder copies the counts onto Boolean detail and does not calculate them. Constant and Empty boolean columns are not counted. `{0, 1}` stays Numeric. No semantic rule changed. `boolean_analysis` stays a separate field beside `numeric_analysis`. `boolean.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-022 adds exact missingness structure in `pytics.analysis` ([DEC-093](DECISIONS.md#dec-093)). It is not semantic evidence. `analyze_dataframe` collects it after the per-column analyses, from one boolean mask that is not retained. `DatasetAnalysis.missing_analysis` stores the row distribution and the exact position patterns. `build_missing_summary` reads that retained analysis and the basic-evidence counts. It does not rescan. Pattern identity is physical position. The empty pattern is a complete row. There is no mechanism classification and no co-missingness coefficient. `missing.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-023 adds exact duplicate-row groups in `pytics.analysis` ([DEC-094](DECISIONS.md#dec-094)). It is not semantic evidence. `analyze_dataframe` collects it after the missingness pass. The two passes do not call each other. `DatasetAnalysis.duplicate_analysis` stores repeated physical row positions only. `build_duplicate_summary` reads that retained analysis and does not rescan. `build_dataset_overview` copies unique-row and excess-duplicate counts from the same derivations and does not store the groups. Row equality is pandas factorize equality, including one code for pandas-missing values in a column. There is no near-duplicate normalization and no Finding. `duplicate.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-024 adds Numeric × Numeric relationships in `pytics.analysis` ([DEC-095](DECISIONS.md#dec-095)). It is not semantic evidence. `analyze_dataframe` collects it after the duplicate pass. The missing, duplicate, and relationship passes do not call each other. `DatasetAnalysis.relationship_analysis` stores supported pairs and coverage counts. Unsupported pairs are not retained one by one. `build_relationships_summary` reads that retained analysis and does not recompute. Spearman is the primary descriptive association. Pearson is complementary. The population is pairwise finite values. There is no method registry and no Finding. TSK-025 keeps those statistical rules and moves the implementation into `pytics.analysis.relationships` ([DEC-096](DECISIONS.md#dec-096)). `relationship.py` remains a re-export. TSK-026 adds Numeric × Categorical in `relationships/numeric_categorical.py` ([DEC-097](DECISIONS.md#dec-097)). The collector still chooses pairs. The family module owns the sums of squares and the ANOVA call. Group descriptions reuse the Numeric descriptive calculator. TSK-027 keeps both families in one `relationship_analysis` field and removes dataset-level method, population, computation, and confidence-level claims ([DEC-098](DECISIONS.md#dec-098)). Family records stay in `models.py`. The collector does not become a registry. TSK-028 adds Boolean × Boolean in `relationships/boolean_boolean.py` without a new `DatasetAnalysis` field ([DEC-099](DECISIONS.md#dec-099)). The family module owns the 2×2 counts, the effect formulas, and the Fisher call. The collector prepares each needed Boolean column once and does not contain those formulas. The retained records then moved from one `models.py` file into `relationships/models/`: shared vocabulary in `common.py`, one module per calculated family, and coverage records in `coverage.py`. That package re-exports the previous names. TSK-029 adds Numeric × Boolean as `relationships/numeric_boolean.py` with records in `relationships/models/numeric_boolean.py` ([DEC-100](DECISIONS.md#dec-100)). The family module owns the group moments, Hedges' g, the Welch interval, and the Welch test. Group descriptions reuse the Numeric descriptive calculator. `BooleanLevel` moved into `common.py` because two families use it. The collector reuses the existing Numeric and Boolean preparations, prepares each needed column once, and adds one direct branch. TSK-030 adds Categorical × Categorical as `relationships/categorical_categorical.py` with records in `relationships/models/categorical_categorical.py` ([DEC-101](DECISIONS.md#dec-101)). The family module owns the contingency counts, classical Cramér's V, the expected-count diagnostics, and the uncorrected Pearson chi-square. It reuses the existing categorical preparation. `_require_category_scalar` moved into `common.py` because two families retain category scalars. Boolean's 2×2 table was not generalized. The collector adds one direct branch and was not split. TSK-031 adds `relationships/adjustment.py` ([DEC-102](DECISIONS.md#dec-102)). Pair calculators still store raw p-values. The collector calls that module once after the records exist, and `build_relationships_summary` copies the adjusted values without recomputing them. Categorical × Boolean is counted as one unimplemented family. There is no method registry. It does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-032 adds `target.py` in `pytics.analysis` ([DEC-103](DECISIONS.md#dec-103)). `analyze_dataframe` accepts an optional explicit target. `DatasetAnalysis.target_analysis` is `None` when none was requested. The projection reads the selected column's inferred state, the descriptive object that column already stores, and the relationship records that already involve that column. It attaches those records by identity. `build_target_summary` copies them and does not calculate. Pair coverage uses the same `classify_selected_pair` decision as the relationship collector. Legacy `profile` is unchanged. `target.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-033 adds `categorical.py` in `pytics.analysis` ([DEC-104](DECISIONS.md#dec-104)). `CategoricalDescriptiveAnalysis` is not semantic evidence. `analyze_series` collects it only after a Categorical selection. The population is the non-missing observations. Levels follow the physical vocabulary, without unused levels. `ordered` is the dtype flag. The variables builder copies the frozen result onto Categorical detail and does not recount. A Categorical target reuses the column object by identity. `target.py` stays one module: it was 969 lines and is 901 after the aggregate frequency copy was removed. It was not split. Frequency evidence remains a separate observation with its retention limit of 32. No cardinality cutoff was added. `categorical.py` does not freeze the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)).

TSK-034 adds two modules in `pytics.analysis` ([DEC-105](DECISIONS.md#dec-105)). `target_diagnostic.py` holds the frozen diagnostic result and its consistency rules, and does not import scikit-learn. `target_diagnostic_fit.py` is the only module that imports scikit-learn. It reads the frame through the relationship package's Numeric, Boolean, and Categorical column readers, so each semantic type has one source-value representation. The pass order is semantic and descriptive column analysis, relationships, the target projection, then the diagnostic. `analyze_dataframe` stores the result as `DatasetAnalysis.target_diagnostic`, present exactly when a target was requested. It is a sibling of `target_analysis`, not a field of it, so the DEC-103 projection still reads no source values. `DatasetAnalysis` checks the attachment against the target and column records without refitting. `TargetSummary.diagnostic` is a rebuilt copy. The diagnostic retains no estimator, pipeline, frame, array, sparse matrix, generator, or row index. Modeling logic is not in the renderer or the relationship engine. There is no estimator registry and no generic modeling interface.

The TSK-034b hardening pass encodes the validation rows once for permutation importance. Before, each permuted scoring re-encoded every input through the `ColumnTransformer`; that was about 96% of the importance cost. `_owned_columns` reads the fixed layout `_preprocessor` builds. The numeric block is each scaled value in input order, then one missing indicator per input that had missing training values. The one-hot block is each input's training levels in input order. Every encoded column must belong to exactly one input, or the function raises. `_block_mover` moves one input's columns by a row order and keeps the others. A sparse matrix stays sparse: the moved and kept parts are column masks of the same matrix, so their sum is exact. A dense matrix occurs only when no one-hot block exists, and it is copied once per scoring. `_validation_permutations` generates the five row orders with NumPy `RandomState`, reproducing the orders scikit-learn's `permutation_importance` drew in TSK-034. Only one permuted matrix and one input's two masked parts exist at a time. None of them is retained. This mapping depends on the fixed preprocessing. A new transformer in `_preprocessor` must keep each encoded column computed from one input of the same row, or the block permutation is no longer equivalent.

## Package end state

Pytics 2.0 replaces the implementation inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). The final product does not keep a permanent second package under another name. Build that replacement in place ([DEC-063](DECISIONS.md#dec-063)). Keep each 1.1.5 component until its replacement has been specified, implemented, tested, and verified. This document does not authorize deleting or moving the 1.1.5 tree outside that rule.

## Performance and configuration

Performance is an architectural concern. That goal is accepted as intent.

`quick`, `standard`, and `deep` are accepted mode names. Standard is the intended default. Exact contents and thresholds are not frozen ([DEC-058](DECISIONS.md#dec-058), [OPEN-010](DECISIONS.md#open-questions), `REQ-P-16`).

Zero-config by default, and no large public keyword surface, are accepted (`REQ-P-15`). A configuration object is likely and not frozen ([OPEN-009](DECISIONS.md#open-questions)). The signature that selects a mode is not frozen.

## HTML and PDF

Direction, not a final library lock ([DEC-061](DECISIONS.md#dec-061)):

```text
Structured Pytics results
        |
        v
HTML renderer
    /       \
 Jinja     Plotly
    \       /
     HTML/CSS/JS
        |
        v
standalone interactive report
```

Ordinary report generation does not require Dash, a web server, React, Vue, or a JavaScript build chain unless later evidence creates a compelling reason.

Plotly is a rendering engine. It is not the visual design system. The report's restrained grammar is [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md).

xhtml2pdf is not the 2.0 PDF architecture. WeasyPrint is the leading candidate for HTML and CSS PDF layout and is not a final dependency ([OPEN-035](DECISIONS.md#open-questions)).

HTML and PDF share a design language. They are not required to use identical markup.

How Plotly figures become reliable static PDF graphics, without fragile system dependencies, is [OPEN-041](DECISIONS.md#open-questions). Kaleido is neither selected nor rejected.

## What 1.1.5 does instead

`src/pytics/profiler.py` computes statistics and emits HTML or PDF in the same functions. That conflicts with `REQ-T-01`. It is recorded as baseline fact, not as a pattern to extend. See [BASELINE_1_1_5.md](BASELINE_1_1_5.md).
