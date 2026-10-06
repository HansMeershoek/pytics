# Progress

The project owner accepted the Slice 001 codebase on 2026-10-03 as the approved baseline for continued development. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, TSK-024, TSK-025, TSK-026, TSK-027, TSK-028, TSK-029, TSK-030, TSK-031, TSK-032, TSK-033, TSK-034, TSK-035, TSK-036, TSK-037, TSK-038, TSK-039, TSK-040, TSK-041, TSK-042, TSK-043, TSK-044, TSK-045, TSK-046, and TSK-047 are complete. TSK-001 through TSK-017 are foundation slices. TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, TSK-024, TSK-025, TSK-026, TSK-027, TSK-028, TSK-029, TSK-030, TSK-031, TSK-032, TSK-033, TSK-034, TSK-035, TSK-036, TSK-037, TSK-038, and TSK-039 are analytical product slices. REQ-L-04 and REQ-L-05 are Implemented. No requirement row is Completed. TSK-005 completes the planned strong-physical-type semantics phase. A documentation-only Semantic Foundation consolidation, recorded the same day, accepted the candidate-resolution architecture in DEC-064 through DEC-076. TSK-006 then strengthened the universal column-evidence family. TSK-007 then added exact frequency observations and no semantic reading. TSK-008 then added exact numeric-structure observations and no semantic reading. TSK-009 then added exact string-structure observations and no semantic reading. TSK-010 then added exact pattern observations and no semantic reading. TSK-011 then added an Identifier candidate assessment and does not select that reading. TSK-012 then added Numeric, Categorical, and Text candidate assessments and does not select those readings. TSK-013 then added exact string-content observations and does not select a reading. TSK-014 then resolves structural readings and already produced candidate assessments. It does not assign confidence to a candidate-derived selection and does not enter the precedence chain. TSK-015 then records the inferred state after that resolution. It preserves a structural interpretation and does not assign confidence to a candidate-derived selection. It does not enter the precedence chain. TSK-016 then connects those components for one Series. It returns the existing inferred result, preserves structural readings, and does not assign confidence to a candidate-derived selection. It does not change `profile` or `compare`. TSK-017 then retains that column analysis for one DataFrame. It keeps physical dtype, collected evidence, and the inferred result, and it stores row, column, and cell counts. It does not add a semantic rule, and it does not change `profile` or `compare`. TSK-018 then summarizes that analysis as an internal dataset overview. It copies the dimension and missing-cell facts, counts resolved selected semantic types, and names Empty, Constant, Identifier, and unresolved columns. It does not rescan the DataFrame, and it does not change `profile` or `compare`. TSK-019 then summarizes each column of that analysis as an internal variable. It copies universal counts and adds Numeric, Categorical, and Identifier detail from retained evidence. It does not rescan the DataFrame, and it does not change `profile` or `compare`. TSK-020 then adds finite-population descriptive statistics for a column whose selected semantic type is Numeric. It does not change semantic inference, and it does not change `profile` or `compare`. TSK-021 then adds true and false counts for a column whose selected semantic type is Boolean. It does not change semantic inference, and it does not change `profile` or `compare`. TSK-022 then adds exact dataset missingness structure: cell facts already retained, column missingness, the row distribution, and recurring missingness patterns. It does not infer a missingness mechanism, and it does not change `profile` or `compare`. TSK-023 then records exact duplicate rows: unique-row and excess-row counts, and the physical positions of each repeated row value. It does not treat duplication as an error, and it does not change `profile` or `compare`. TSK-024 then describes selected Numeric × selected Numeric pairs with Spearman and Pearson. It does not implement other relationship families, and it does not change `profile` or `compare`. TSK-025 then keeps dataset analysis alive when a Numeric mean, sample standard deviation, range, or interquartile range cannot be represented as a finite float64, and it moves the relationship implementation into a package. It does not add a relationship family, and it does not change `profile` or `compare`. TSK-026 then describes selected Numeric × selected Categorical pairs with group summaries, eta squared, and classical one-way ANOVA. It does not add post-hoc tests, and it does not change `profile` or `compare`. TSK-027 then moves relationship metadata onto the family or component that owns it. It does not add a family, and it does not change `profile` or `compare`. TSK-028 then describes selected Boolean × selected Boolean pairs with a 2×2 table, probability effects, phi, and Fisher exact. It does not change `profile` or `compare`. TSK-029 then describes selected Numeric × selected Boolean pairs with a True − False mean difference, Hedges' g, a Welch interval, and Welch's t-test. It does not change `profile` or `compare`. TSK-030 then describes selected Categorical × selected Categorical pairs with an observed contingency table, classical Cramér's V, expected-count diagnostics, and uncorrected Pearson chi-square. It does not change `profile` or `compare`. TSK-031 then adjusts the available primary relationship p-values with Benjamini–Hochberg and classifies Categorical × Boolean as unimplemented. It does not add a relationship family, and it does not change `profile` or `compare`. TSK-032 then projects an explicit target onto that column's inferred state, its retained descriptive facts, and the relationship records that already involve it. It does not fit a diagnostic model, and it does not change `profile` or `compare`. TSK-033 then retains the exact observed distribution of a selected Categorical column and reuses that result for a Categorical target. It does not add an imbalance verdict, a problem type, or a diagnostic model, and it does not change `profile` or `compare`. TSK-034 then adds one untuned diagnostic model for an explicit target, scored on a held-out split against a naive baseline, with held-out permutation importance of the original columns. It does not tune or compare models, it does not change target analysis or relationships, and it does not change `profile` or `compare`. TSK-035 then records exact-duplicate and repeated deterministic-mapping evidence for that target. It does not decide that a column leaks the target, it does not change relationship records, and it does not change `profile` or `compare`. TSK-036 then records finite numeric values outside retained Tukey fences. It does not treat those values as errors, it does not add a multivariate detector, and it does not change `profile` or `compare`. TSK-037 then compares a reference dataset with a comparison dataset using those retained analyses. It aligns columns, records schema and semantic transitions, and compares Numeric, Categorical, and Boolean descriptive facts. It does not score drift, and it does not change `profile` or `compare`. TSK-038 then adds univariate distribution drift for matched Numeric, Categorical, and Boolean columns: distances first, one test per column, and one Benjamini–Hochberg family per comparison. It splits the comparison module into a package. It does not add relationship or target drift, a score, or a threshold, and it does not change `profile` or `compare`. TSK-039 then compares retained relationship effects and projects target change for an explicit target. It adds no drift score and does not change `profile` or `compare`. TSK-040 then adds the Findings Engine foundation: a threshold-free v0.1 catalog that selects retained Profile and Compare facts for attention, with typed evidence, a label-based identity, an explicit severity policy, deterministic order, and inspectable suppression. It computes no statistic, reads no DataFrame or p-value, emits no recommendation or prose, and does not change `profile` or `compare`. TSK-041 then makes the column-label match key and occurrence count the one identity primitive in `column_label.py`, and uses that key wherever a stored column label is compared, so a Numeric column whose label is float `NaN` completes analysis. It does not change a statistical method, the findings catalog, or `profile` or `compare`. TSK-042 then adds the public result contract in `pytics.results`: a frozen facade over a finished profile or comparison, with variables, relationships, findings, and target views that reference the canonical records. It does not serialize or change `pytics.profile` or `pytics.compare`. TSK-043 then adds the notebook Observe landing view of that facade. Displaying the result renders namespaced HTML. The renderer does not recompute a statistic, add a chart, or replace legacy `profile` and `compare`. TSK-044 then supports Categorical for a reused vocabulary of unpunctuated letter-bearing labels on string or object storage. It does not assign High, Medium, or Low to that selection, it does not parse mixed representations, and it does not change `profile` or `compare`. TSK-045 then retains a partition of representation families for string columns that reach candidate assessment, distinguishes an empty representation picture from a conflicting one, and supports Categorical for a reused short-label vocabulary. It does not coerce the source, select Datetime or Numeric from those families, assign High, Medium, or Low, or change `profile` or `compare`. TSK-046 then removes the 1.1.5 renderer and makes `profile` and `compare` return the 2.0 results. TSK-047 then keeps eta squared and classical Cramér's V, adds epsilon squared and Bergsma's bias-corrected V, and withholds Benjamini–Hochberg from a chi-square tail that fails Cochran's expected-count convention. It does not add a cardinality cutoff or another inferential test. TSK-048 then abstains when an exact distinct count is unavailable. TSK-049 then removes six parallel product summaries. TSK-050 then classifies a repeated string once and rejects impossible IP text before standard parsing. The next implementation slice has not been selected.

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
| Implemented | Code and tests exist for the whole requirement as written. Verification against the spec is not recorded as a completed row. First used for REQ-L-04 and REQ-L-05 in the TSK-034b audit. |
| Verified | Behavior was checked against the specification and the evidence is recorded in Verification. Not used yet. |
| Completed | Verified, and the progress row is filled in. Do not use this state on a requirement row without that evidence. Not used on a requirement row yet. The task log may mark a finished slice Completed. |

`In force` is reserved for exclusions and holds: REQ-P-03, REQ-F-03, REQ-I-05, REQ-I-06, REQ-K-03, REQ-L-06, REQ-N-04, REQ-T-03, REQ-T-04. REQ-L-04 and REQ-L-05 are Implemented. Every other requirement row is Not started, including rows a task has partly delivered.

A completed task may name a requirement it only prepares or only partly covers. That requirement stays Not started until the requirement as written is implemented. TSK-001 is that case for REQ-S-01, REQ-S-02, and REQ-S-05. TSK-002 infers Empty and Constant only and collects four basic counts. TSK-003 infers Boolean only from a physical Boolean dtype, and only after Empty and Constant. TSK-004 infers Datetime only from a native or timezone-aware datetime dtype, and only after those three rules. TSK-005 infers Timedelta only from a physical timedelta dtype, and only after those four rules. TSK-006 does not add a semantic reading. It derives convenience facts from the four basic counts and keeps Empty and Constant on those facts. TSK-007 does not add a semantic reading. It records exact frequency observations for non-missing values and does not interpret them. TSK-008 does not add a semantic reading. It records exact numeric-structure observations for physically numeric columns and does not interpret them. TSK-009 does not add a semantic reading. It records exact string-structure observations for physical string columns, and for object columns whose non-missing values are Python strings, and does not interpret them. TSK-010 does not add a semantic reading. It records exact full-value pattern observations for populations that already have string-structure evidence, and does not interpret them. TSK-011 does not select a semantic reading. It assesses whether observations support an Identifier candidate. TSK-012 does not select a semantic reading. It assesses whether observations support Numeric, Categorical, and Text candidates. Physical integer or floating storage can support Numeric. Physical categorical storage can support Categorical. Current observations do not support Text. TSK-013 does not add a semantic reading. It records exact token and vocabulary observations for populations that already have string-structure evidence, and it does not interpret them. TSK-014 resolves an already produced structural reading, or exactly one supported candidate, and abstains or stays ambiguous otherwise. It does not build a confidence-bearing interpretation for a candidate-derived selection. TSK-015 records that resolution together with the observed physical dtype. A structural reading keeps its interpretation. A candidate-derived selection remains resolved at the type level and does not become a confidence-bearing interpretation. Abstention and ambiguity are inferred states. TSK-016 does not add a semantic reading. It runs the existing structural rules and the existing candidate rules for one Series, and it leaves candidate-derived confidence unset. TSK-017 does not add a semantic reading. It retains the column analysis and dataset dimensions already justified by that path. TSK-018 does not add a semantic reading. It aggregates the dataset analysis into an internal overview and does not render that overview. TSK-019 does not add a semantic reading. It aggregates each column analysis into an internal variable summary and does not render that summary. TSK-020 does not add a semantic reading. It adds a partial numeric descriptive profile for a selected Numeric column and does not complete numeric analysis. TSK-021 does not add a semantic reading. It adds true and false counts for a selected Boolean column and does not complete Boolean/Binary inference. TSK-022 does not add a semantic reading. It records exact observed missingness structure and does not complete missing-data analysis. Do not read these task links as completion of semantic inference, Boolean/Binary analysis, datetime analysis, time-series analysis, timedelta duration analysis, downstream numeric analysis, text diagnostics, identifier detection, missing-like literal reporting, missingness mechanisms, co-missingness coefficients, memory usage, duplicate-row analysis, the rendered Dataset Overview, the rendered Variables table, or the rendered Missing view.

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
| TSK-016 | REQ-S-03, REQ-S-04, and REQ-S-05, column orchestration only. REQ-S-01 is not completed: existing readings are reached and none is added. REQ-S-02 is not completed. | Slice 016. One internal Series pipeline returning the existing inferred result. No override, no confidence policy, and no public profiler integration. | The 18 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-016). | Completed |
| TSK-017 | REQ-A-01 for row, column, and cell counts only. REQ-S-03 and REQ-S-05 for retained column evidence on a DataFrame path. REQ-A-01, REQ-A-02, REQ-A-03, REQ-S-01, and REQ-S-02 are not completed. | Slice 017. One internal DataFrame analysis. One column analysis per physical column. No overview, no memory contract, and no public profiler integration. | The 15 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-017). | Completed |
| TSK-018 | REQ-A-01 for exposing those counts on an overview. REQ-A-03 for cell completeness only. REQ-A-05 for resolved semantic-type counts only. REQ-A-06 for Empty, Constant, and Identifier columns only. REQ-IA-05 for the analytical facts only. None of those requirement rows is completed. | Slice 018. One internal overview built from `DatasetAnalysis`. No DataFrame rescan, no memory contract, no duplicate-row contract, and no public profiler integration. | The 13 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-018). | Completed |
| TSK-019 | REQ-B-01 for structural numeric counts only. REQ-C-01, REQ-C-02, and REQ-C-04 for the universal counts and the frequency counts that evidence already retains. REQ-G-01 and REQ-G-02 for Identifier pattern facts only. REQ-IA-07 for the analytical rows only. None of those requirement rows is completed. | Slice 019. One internal variables summary built from `DatasetAnalysis`. Frequency evidence is collected for non-structural physical categorical columns. No descriptive-statistics collector, no DataFrame rescan from the product builder, and no public profiler integration. | The 14 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-019). | Completed |
| TSK-020 | REQ-B-01 for minimum, maximum, and range only. REQ-B-02 for mean, median, sample standard deviation, Q1, Q3, and interquartile range only. Neither requirement row is completed. | Slice 020. Finite-population descriptive statistics for a column whose selected semantic type is Numeric. Collected in `pytics.analysis` after resolution. No skewness, kurtosis, histogram, outlier rule, or Findings. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-020). | Completed |
| TSK-021 | REQ-D-02 respected for the descriptive pass only. REQ-D-01 and REQ-D-03 are not advanced. None of those rows is completed. | Slice 021. True and false counts for a column whose selected semantic type is Boolean. Collected in `pytics.analysis` after resolution. No Binary type, no string Boolean parsing, and no `{0, 1}` inference. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-021). | Completed |
| TSK-022 | REQ-H-01 for dataset, column, and row missingness facts only. REQ-H-02 for exact missingness patterns only. REQ-A-03 for complete and incomplete rows on the Missing summary only. REQ-IA-08 for the analytical surface only. REQ-H-04 and REQ-H-05 are respected and not completed. None of those rows is completed. | Slice 022. Exact missingness structure for one DataFrame: retained patterns and a product summary. No mechanism classification, no co-missingness coefficient, and no rendered Missing view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-022). | Completed |
| TSK-023 | REQ-I-01 for exact duplicate rows and duplicate groups only. REQ-A-04 for unique rows and excess duplicate rows on the overview only. REQ-IA-09 and REQ-IA-05 for those analytical facts only. REQ-I-05 and REQ-I-06 are respected and not completed. REQ-I-02, REQ-I-03, and REQ-I-04 are not advanced. None of those rows is completed. | Slice 023. Exact duplicate-row groups for one DataFrame, retained positions, and a product summary. No near-duplicate matching, no Findings, and no rendered Duplicates view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-023). | Completed |
| TSK-024 | REQ-K-01, REQ-K-02, and REQ-K-04 for selected Numeric × Numeric only. REQ-K-03 and REQ-K-05 are respected and not completed as a catalog or a diagnostic layer. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are advanced only as the verification says. None of those rows is completed. | Slice 024. Pair eligibility, Spearman and Pearson for selected Numeric pairs, and a product summary. No other relationship family, no Findings, and no rendered Relationships view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-024). | Completed |
| TSK-025 | REQ-B-01 for minimum, maximum, and range only, including an explicit unavailable range. REQ-B-02 for mean, median, sample standard deviation, Q1, Q3, and interquartile range only, including an explicit unavailable mean, deviation, or interquartile range. Neither requirement row is completed. REQ-K-01 through REQ-K-05 are unchanged. | Slice 025. Numeric descriptive robustness and a relationship-package split. No new relationship family, no Findings, and no rendered view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-025). | Completed |
| TSK-026 | REQ-K-01, REQ-K-02, and REQ-K-04 for selected Numeric × Categorical in addition to Numeric × Numeric. REQ-K-03 and REQ-K-05 are respected and not completed as a catalog or a diagnostic layer. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are advanced only as the verification says. None of those rows is completed. | Slice 026. Group summaries, eta squared, and classical one-way ANOVA for selected Numeric × Categorical pairs. No post-hoc tests, no Findings, and no rendered Relationships view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-026). | Completed |
| TSK-027 | REQ-K-01, REQ-K-02, and REQ-K-04 are unchanged. REQ-K-03 and REQ-K-05 are respected. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are not completed. None of those rows is completed. | Slice 027. Heterogeneous relationship metadata. No new family, no statistical-calculation change, no Findings, and no rendered Relationships view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-027). | Completed |
| TSK-028 | REQ-K-01, REQ-K-02, and REQ-K-04 for selected Boolean × Boolean in addition to the two earlier families. REQ-K-03 and REQ-K-05 are respected and not completed as a catalog or a diagnostic layer. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are advanced only as the verification says. None of those rows is completed. | Slice 028. A 2×2 table, probability difference, probability ratio, phi, and a raw two-sided Fisher exact p-value for selected Boolean × Boolean pairs. No confidence interval, no odds ratio, no generic contingency framework, no Findings, and no rendered Relationships view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-028). | Completed |
| TSK-029 | REQ-K-01, REQ-K-02, and REQ-K-04 for selected Numeric × Boolean in addition to the three earlier families. REQ-K-03 and REQ-K-05 are respected and not completed as a catalog or a diagnostic layer. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are advanced only as the verification says. REQ-L-01 through REQ-L-07 are not advanced. None of those rows is completed. | Slice 029. False and True group summaries, a True − False mean difference, Hedges' g, a 95% Welch–Satterthwaite interval, and Welch's t-test with a raw p-value for selected Numeric × Boolean pairs. No rank test, no target analysis, no Findings, and no rendered Relationships view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-029). | Completed |
| TSK-030 | REQ-K-01, REQ-K-02, and REQ-K-04 for selected Categorical × Categorical in addition to the four earlier families. REQ-K-03 and REQ-K-05 are respected and not completed as a catalog or a diagnostic layer. REQ-P-10, REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are advanced only as the verification says. REQ-L-01 through REQ-L-07 are not advanced. None of those rows is completed. | Slice 030. Observed contingency table, classical Cramér's V, expected-count diagnostics, and uncorrected Pearson chi-square with a raw p-value for selected Categorical × Categorical pairs. No Yates correction, no Fisher fallback, no target analysis, no Findings, and no rendered Relationships view. | The 10 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-030). | Completed |
| TSK-031 | REQ-K-01, REQ-K-02, and REQ-K-04 for the five calculated families, plus dataset-level correction of their primary tests. REQ-K-03 and REQ-K-05 are respected and not completed as a catalog or a diagnostic layer. REQ-P-10 is advanced because raw and adjusted p-values are now distinct stored evidence. REQ-G-03, REQ-IA-11, REQ-T-03, and REQ-T-05 are advanced only as the verification says. REQ-L-01 through REQ-L-07 are not advanced. None of those rows is completed. | Slice 031. Benjamini–Hochberg adjustment of one available primary p-value per calculated relationship, and a coverage classification for Categorical × Boolean. No new relationship calculator, no target analysis, no Findings, and no rendered Relationships view. | The 9 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-031). | Completed |
| TSK-032 | REQ-L-01 and REQ-L-02 for the selected semantic state, the target's own missingness, and reused Numeric and Boolean facts. REQ-L-06 is respected. REQ-G-03, REQ-T-05, and REQ-IA-12 are advanced only as the verification says. REQ-L-03, REQ-L-04, REQ-L-05, REQ-L-07, and REQ-P-14 are not advanced. None of those rows is completed. | Slice 032. Explicit target resolution by label or physical position, the target status matrix, the target population, reused descriptive facts, and relationship links with orientation, projected from retained records. No diagnostic model, ranking, problem type, or rendered Target view. | The 9 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-032). | Completed |
| TSK-033 | REQ-C-02, REQ-C-04, and REQ-C-05 for the exact observed distribution of a selected Categorical column. REQ-L-01 and REQ-L-02 for its reuse on a Categorical target and for Boolean class structure. None of those rows is completed. | Slice 033. Exact observed level counts, vocabulary order, the physical `ordered` flag, and derived proportions, reused by identity for a Categorical target. No imbalance verdict, problem type, diagnostic model, or rendered view. | The 9 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-033). | Completed |
| TSK-034 | REQ-L-04, REQ-L-05, and REQ-L-07 for one diagnostic model of a Numeric, Boolean, or Categorical target. REQ-L-01 is advanced by a predictive task kept separate from the semantic type. REQ-L-06, REQ-P-02, and REQ-T-04 are respected. REQ-G-03 and REQ-P-12 are advanced only as the verification says. REQ-L-03 is not delivered. None of those rows is completed. | Slice 034. One untuned logistic or ridge model, one 25% holdout, a prior or mean baseline, three held-out metrics per task, and held-out permutation importance of original columns. No tuning, comparison, leakage analysis, metric uncertainty, or rendered Target view. | The 11 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-034). | Completed |
| TSK-035 | REQ-L-03 for exact-duplicate evidence and repeated deterministic classification mappings only. The rest of that requirement is not delivered. REQ-L-06 is respected. REQ-G-03 is unchanged. None of those rows is completed. | Slice 035. Evidence of exact target copies and of repeated conflict-free mappings onto classification classes. No leakage score, no association threshold, no temporal leakage, and no rendered Target view. | The 10 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-035). | Completed |
| TSK-036 | REQ-J-01 and REQ-J-02 for Tukey fences on a selected Numeric column only. REQ-B-06 for that same signal only. REQ-J-03, REQ-J-04, and REQ-IA-10 are not delivered. REQ-G-03 and REQ-P-04 are respected on this path. None of those rows is completed. | Slice 036. One univariate numeric anomaly method, physical row identity, and coverage. No multivariate detector, no severity, and no rendered Anomalies view. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-036). | Completed |
| TSK-037 | REQ-M-01 through REQ-M-04 for column alignment, schema and semantic transitions, and Numeric, Categorical, and Boolean descriptive comparison only. Distribution drift, relationship drift, and target drift are not delivered. REQ-P-07 and REQ-T-05 are respected on this path. None of those rows is completed. | Slice 037. Reference and comparison orientation, occurrence-aware column identity, and descriptive change from retained analyses. No drift score, no severity, and no rendered Compare view. | The 11 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-037). | Completed |
| TSK-038 | REQ-M-01 through REQ-M-04 for univariate distribution drift of matched Numeric, Categorical, and Boolean columns, in addition to TSK-037. Relationship drift, target drift, public `compare()`, and the rendered Compare view are not delivered. REQ-M-03 and REQ-P-07 are respected on this path. REQ-P-10 and REQ-T-05 are advanced only as the verification says. None of those rows is completed. | Slice 038. KS and Wasserstein distances, total variation distance, a True-share difference, one primary test per column, expected-count diagnostics, one comparison-level Benjamini–Hochberg family, and a compare package split by ownership. No drift score, no severity, no threshold, and no Findings. | The 12 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-038). | Completed |
| TSK-039 | REQ-M-01 through REQ-M-04 for relationship effect changes and an explicit-target projection, in addition to TSK-037 and TSK-038. Public `compare()`, Findings, and the rendered Compare view are not delivered. Formal change tests other than a complementary Pearson Fisher z test are not delivered. REQ-M-03, REQ-P-07, and REQ-P-10 are respected on this path. REQ-T-05 is advanced only as the verification says. None of those rows is completed. | Slice 039. Signed or directional effect changes for the five calculated relationship families, pair alignment by column identity, explicit family and availability transitions, one unadjusted Pearson change test, and target projections of distribution drift, relationship drift, diagnostic metrics, and leakage statuses. No drift score and no Findings. | The 10 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-039). | Completed |
| TSK-040 | REQ-N-01 through REQ-N-03 for a threshold-free v0.1 catalog over retained Profile and Compare results. REQ-N-04 is respected. REQ-IA-06 is prepared and not delivered. REQ-P-04, REQ-P-07, REQ-P-10, REQ-M-03, REQ-L-03, and REQ-T-05 are respected on this path. None of those rows is completed. | Slice 040. Findings Epistemic Contract v0.1, typed codes, scopes, subjects, and evidence, label-based identity, an explicit severity and order policy, root-condition suppression, coverage, and policy metadata. Five Profile codes and six Compare codes. No threshold, no score, no recommendation, no prose, and no renderer. | The 10 checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-040). | Completed |
| TSK-041 | No requirement row is advanced. The column identity already used by Compare and Findings is one implementation. REQ-M-01 through REQ-M-04 and REQ-N-01 through REQ-N-03 stay Not started. | Slice 041. Match key and occurrence owned by `column_label.py`. Float `NaN` labels compare under that key. No statistical, findings-policy, drift, or public-API change. | The checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-041). | Completed |
| TSK-042 | REQ-T-01 and REQ-T-02 are advanced and not completed: the analytical return is a structured result, and no renderer consumes it yet. REQ-P-07 is respected. REQ-P-14 is advanced only as this object. REQ-IA-06 is not delivered. None of those rows is completed. | Slice 042. Public result contract v0.1. `ProfileResult` and `ComparisonResult` reference canonical analysis and findings. No notebook, HTML, Markdown, PDF, JSON file, plugin, or change to legacy `profile` and `compare`. | The checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-042). | Completed |
| TSK-043 | REQ-P-13 is advanced for the 2.0 result only. REQ-P-14 and REQ-IA-17 are advanced and not completed. REQ-IA-06 is not delivered. REQ-P-07 is respected. None of those rows is completed. | Slice 043. Notebook Observe landing view of `ProfileResult` and `ComparisonResult`. No chart, no standalone HTML, PDF, Markdown, or JSON, and no change to legacy `profile` and `compare`. | The checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-043). | Completed |
| TSK-044 | REQ-S-01 and REQ-C-01 are advanced and not completed. REQ-C-05 and REQ-F-01 are advanced only for the letter-label rule. REQ-D-01 is not completed. None of those rows is completed. | Slice 044. Categorical support for a reused vocabulary of unpunctuated letter-bearing labels. No cleaning, no mixed-representation parser, and no notebook redesign. | The checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-044). | Completed |
| TSK-045 | REQ-S-01, REQ-C-01, and REQ-F-01 are advanced and not completed. REQ-S-03 is respected. REQ-D-01 is not completed. None of those rows is completed. | Slice 045. Representation-family evidence, mixture of that evidence, and Categorical support for reused short labels. No cleaning, no Datetime or Numeric coercion, and no notebook redesign. | The checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-045). | Completed |
| TSK-047 | REQ-K-02, REQ-K-04, REQ-P-10, and REQ-T-05 are advanced and not completed. REQ-K-05, REQ-M-03, and REQ-P-07 are respected. None of those rows is completed. | Slice 047. Epsilon squared, Bergsma's bias-corrected Cramér's V, and Cochran's chi-square validity gate for relationship and distribution-drift tails. No cardinality cutoff and no replacement test. | The checks in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#tsk-047). | Completed |
| TSK-050 | No requirement row is completed. REQ-S-03 is respected: source values are not cleaned or coerced. | Slice 050. Local weighted string evidence for a repetitive population, and cheap IP impossibility checks before `ipaddress`. No cache, no shared classifier, and no semantic change. | Exact evidence equality with the row-wise collectors, and the Phase-A timing gates. | Completed |

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

### TSK-016 — Slice 016, column-level semantic pipeline integration

The committed Slice 001 through Slice 015 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `98bf3d5`, before this slice.

Approved in the Slice 016 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-087](DECISIONS.md#dec-087). `infer_series_semantics` accepts one pandas Series and returns the existing `InferredSemanticResult`. It classifies physical dtype once and collects `BasicColumnEvidence` once. Structural precedence is the existing `interpret_precedence_from_evidence`. `interpret_series_precedence` remains the Series wrapper and was not given a second implementation. A structural reading returns through `resolve_semantics` and `build_inferred_semantic_result` without candidate-family evidence or candidate assessment. Otherwise integer and floating storage collect numeric-structure evidence once; eligible string and object populations collect string structure once, then pattern and string content from that same object; categorical storage and other non-structural families collect nothing further. An ineligible object population is insufficient evidence, not an error and not a coercion. Frequency evidence is not collected, because no current assessor reads it. The four existing assessors run on that bundle and do not receive the Series. Candidate-derived selections stay without a `SemanticInterpretation` and without High, Medium, or Low. [OPEN-047](DECISIONS.md#open-047) records that this pipeline produces the inferred result and leaves candidate-derived confidence, material alternatives, and the public result open. [OPEN-044](DECISIONS.md#open-questions) stays open for that confidence. [OPEN-045](DECISIONS.md#open-questions) stays open: the module is not a layout decision. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/semantics/pipeline.py` | Column-level orchestration from one Series to the existing inferred result. Not called by `interpret_series_precedence` or by `profile`. |

Not modified: `src/pytics/semantics/inferred.py`, `src/pytics/semantics/resolution.py`, `src/pytics/semantics/core_candidates.py`, `src/pytics/semantics/candidate.py`, `src/pytics/semantics/identifier_candidate.py`, `src/pytics/semantics/column_evidence.py`, `src/pytics/semantics/empty_constant.py`, `src/pytics/semantics/frequency_evidence.py`, `src/pytics/semantics/numeric_structure_evidence.py`, `src/pytics/semantics/string_structure_evidence.py`, `src/pytics/semantics/string_content_evidence.py`, `src/pytics/semantics/pattern_evidence.py`, `src/pytics/semantics/physical.py`, `src/pytics/semantics/interpretation.py`, `src/pytics/semantics/physical_boolean.py`, `src/pytics/semantics/physical_datetime.py`, `src/pytics/semantics/physical_timedelta.py`, `src/pytics/semantics/__init__.py`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, `pyproject.toml`. Slice 001 through Slice 015 tests were not modified.

Tests: `tests/test_semantic_pipeline.py`.

`infer_series_semantics` does not mutate the Series and does not read its name or index. Empty, Constant, physical Boolean, nullable Boolean, physical Datetime, timezone-aware Datetime, and physical Timedelta keep the interpretation the precedence wrapper already produces. A constant UUID stays Constant. Integer and floating columns, including `{0, 1}`, resolve to Numeric with no interpretation. Canonical UUID strings, compact UUID strings, supported hexadecimal strings, and object-stored UUID strings resolve to Identifier with no interpretation, except where Constant precedence applies. Physical categorical storage, including the ordered flag, resolves to Categorical and is not Ordinal. City names, prose, ordinary object strings, mixed objects, `bytes`, and complex or period storage are `INSUFFICIENT_EVIDENCE`. Missing-like literals stay ordinary strings. Physical classification and basic-evidence collection each happen once. String structure is shared by identity with pattern evidence and string-content evidence. Numeric-structure evidence shares the basic evidence by identity. Structural columns do not run candidate collectors or assessors. Resolution and inferred-result construction are the existing functions.

What was not implemented: High, Medium, or Low confidence for a candidate-derived selection; a `SemanticInterpretation` for that selection; material alternatives; frequency collection; a Text or ordinary-string Categorical rule; Binary or Ordinal inference; numeric Identifier evidence; a user override; effective interpretation; downstream eligibility; dataset context; sampling; a public result; a threshold; a change to `profile` or `compare`.

Left open, and not decided in this slice: candidate-derived confidence ([OPEN-044](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047)); material alternatives ([OPEN-047](DECISIONS.md#open-047)); Text and ordinary-string Categorical inference ([OPEN-044](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions)); Binary representation ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); numeric Identifier evidence ([OPEN-044](DECISIONS.md#open-questions)); user overrides and effective interpretation ([OPEN-009](DECISIONS.md#open-questions), [OPEN-049](DECISIONS.md#open-049), [OPEN-004](DECISIONS.md#open-questions)); downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); dataset-context evidence; sampling and modes ([OPEN-010](DECISIONS.md#open-questions)); the public result shape ([OPEN-004](DECISIONS.md#open-questions)); the module layout ([OPEN-045](DECISIONS.md#open-questions)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-S-01, REQ-S-02, REQ-S-03, REQ-S-04, or REQ-S-05. An inferred result reached through the column pipeline is still not the public semantic interpretation and not the effective interpretation.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `98bf3d5532b6d822907bfec4a39ba7f394429351`. The pre-slice semantic baseline recorded under TSK-015 was 920 passed. The pre-slice full-suite baseline was 939 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_semantic_pipeline.py -q` | 70 passed |
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
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py -q` | 143 passed |
| `pytest tests/test_semantic_foundation.py tests/test_empty_constant.py tests/test_physical_boolean.py tests/test_physical_datetime.py tests/test_physical_timedelta.py tests/test_column_evidence.py tests/test_frequency_evidence.py tests/test_numeric_structure_evidence.py tests/test_string_structure_evidence.py tests/test_pattern_evidence.py tests/test_candidate_assessment.py tests/test_identifier_candidate.py tests/test_core_candidates.py tests/test_string_content_evidence.py tests/test_semantic_resolution.py tests/test_inferred_semantics.py tests/test_semantic_pipeline.py -q` | 990 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 1009 passed, 1 failed |

`tests/test_semantic_pipeline.py` is 70 Slice 016 tests. The combined semantic run was 990 passed, which is the previous 920 plus these 70. The structural run for TSK-001 through TSK-005 was 143 passed. The full suite was 1009 passed and 1 failed, which is the previous 939 plus these 70. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Semantic modules, including the pipeline, were fully covered on the full run. Total coverage on that run was 99%. `pipeline.py` had no missed statements. The uncovered lines remain in the profiler and visualizations.

All 18 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-017 — Slice 017, dataset observation and column-analysis retention

The committed Slice 001 through Slice 016 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `5996e34`, before this slice.

Approved in the Slice 017 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-088](DECISIONS.md#dec-088). `analyze_series` is the only column collection and semantic orchestration. It returns a `ColumnAnalysis` that keeps position, the original label, the physical dtype, a typed `ColumnEvidence` value, and the existing `InferredSemanticResult`. `infer_series_semantics` returns that analysis's inferred result. `analyze_dataframe` accepts a pandas DataFrame only and returns a `DatasetAnalysis` with `n_rows`, `n_columns`, `n_cells`, and one column analysis per physical column. Missing-cell totals and `missing_ratio` are derived from retained basic evidence. `missing_ratio` is `None` when there are no cells. Duplicate labels stay distinct because identity is position plus label. Labels are not stringified. Frequency evidence and string-content evidence are not collected: no current candidate reads them, and this slice's dataset facts do not either. Structural columns still stop after basic evidence. The DataFrame and its Series are not stored and are not mutated. `pytics.semantics` owns semantic inference. `pytics.analysis` owns these records, `analyze_series`, and `analyze_dataframe`. [OPEN-045](DECISIONS.md#open-questions) records that boundary and stays open for the rest of the layout. [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-047](DECISIONS.md#open-047) stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/__init__.py` | Internal package marker. Not part of the public profiler API. |
| `src/pytics/analysis/column.py` | Column evidence, column analysis, and the only column orchestration. |
| `src/pytics/analysis/dataset.py` | Dataset analysis and the DataFrame traversal. |
| `src/pytics/semantics/pipeline.py` | Series wrapper. Returns the inferred result of `analyze_series`. |

Not modified: the semantic evidence modules, candidate assessors, resolution, the inferred-result model, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_dataset_analysis.py`. `tests/test_semantic_pipeline.py` now spies on the column-analysis module. Ordinary strings no longer collect string-content evidence. Semantic expectations are otherwise unchanged.

`analyze_dataframe` does not read column labels as semantic evidence, does not call `infer_series_semantics`, and does not run a second pass. Zero-row columns follow the current Empty rule and do not collect string structure. A zero-column frame has no column records. A completely empty frame has zero cells and an undefined missing ratio.

What was not implemented: memory usage; duplicate rows; semantic-type counts; missing patterns; frequency collection; string-content collection on the column path; dataset-context semantic inference; candidate-derived confidence; a public result; a change to `profile` or `compare`.

Left open, and not decided in this slice: public result naming ([OPEN-004](DECISIONS.md#open-questions)); configuration ([OPEN-009](DECISIONS.md#open-questions)); modes and sampling ([OPEN-010](DECISIONS.md#open-questions)); dataset dimensions beyond row, column, and cell counts, and cardinality thresholds ([OPEN-018](DECISIONS.md#open-questions)); whether token aggregates belong in a text profile ([OPEN-019](DECISIONS.md#open-questions)); downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); candidate-derived confidence ([OPEN-044](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047)); the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)); memory-usage semantics; duplicate-row semantics; and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-A-01, REQ-A-02, REQ-A-03, REQ-S-01, REQ-S-02, REQ-S-03, or REQ-S-05.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `5996e34236373a3a4dcbdea1c7a621ad7346b90d`. The pre-slice TSK-016 baseline was 70 passed. The pre-slice full-suite baseline was 1009 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_dataset_analysis.py -q` | 31 passed |
| `pytest tests/test_semantic_pipeline.py -q` | 70 passed |
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
| structural TSK-001 through TSK-005 | 143 passed |
| combined semantic, without the new dataset tests | 990 passed |
| `pytest tests/test_dataset_analysis.py -q` again, as the analysis/dataset run | 31 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 1040 passed, 1 failed |

`tests/test_dataset_analysis.py` is 31 Slice 017 tests. The combined semantic run stayed 990 passed. The full suite was 1040 passed and 1 failed, which is the previous 1009 plus these 31. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/column.py` and `analysis/dataset.py` had no missed statements. Total coverage on the full run was 99%.

All 15 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-018 — Slice 018, dataset overview foundation

The committed Slice 001 through Slice 017 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `93faa29`, before this slice.

Approved in the Slice 018 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-089](DECISIONS.md#dec-089). `build_dataset_overview` accepts a `DatasetAnalysis` and returns a frozen `DatasetOverview`. It does not accept a DataFrame. Stored facts are the three dimension counts, the two cell counts, a sparse tuple of semantic type counts in `SemanticType` definition order, and column references for insufficient evidence, ambiguity, Empty, Constant, and Identifier. A resolved column is counted by `selected_type`. A candidate-derived Numeric, Identifier, Categorical, or synthetic Text selection counts while `interpretation` is `None`. `completeness_ratio` is non-missing cells divided by cells, and `None` when there are no cells. `semantic_resolution_ratio` is resolved columns divided by columns, and `None` when there are no columns. Those ratios are not a quality score. A constant UUID stays Constant. Column references keep position and the original label, so duplicate labels stay distinct. A zero-row schema is resolved Empty. A zero-column schema does not claim full resolution. The overview module does not import pandas and does not call analysis, collection, or resolution. Memory usage stays deferred because shallow versus deep, pandas-reported versus estimated, and index inclusion are not decided. Duplicate rows stay deferred because first-occurrence, missing equality, group membership, unhashable values, and unique-row meaning are not decided. Near-constant and high-cardinality thresholds stay open. No finding, severity, or composite score was added. `profile` and `compare` are unchanged. [OPEN-018](DECISIONS.md#open-questions) records the dimension and cell-completeness narrowing. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-047](DECISIONS.md#open-047) stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/overview.py` | Dataset overview aggregation. No pandas import and no semantic inference. |
| `src/pytics/analysis/__init__.py` | Package description now includes the overview. |

Not modified: `DatasetAnalysis`, `ColumnAnalysis`, the semantic modules, candidate rules, evidence collectors, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_dataset_overview.py`.

What was not implemented: memory usage; duplicate rows; complete rows and incomplete rows; physical dtype composition; near-constant columns; high-cardinality columns; confidence aggregation; Findings; a rendered overview; a public result; a change to `profile` or `compare`.

Left open, and not decided in this slice: public result naming ([OPEN-004](DECISIONS.md#open-questions)); configuration ([OPEN-009](DECISIONS.md#open-questions)); modes and sampling ([OPEN-010](DECISIONS.md#open-questions)); near-constant and high-cardinality thresholds, and dataset dimensions beyond the three counts ([OPEN-018](DECISIONS.md#open-questions)); downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); candidate-derived confidence ([OPEN-044](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047)); the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)); memory-usage semantics; duplicate-row semantics; and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-A-01, REQ-A-02, REQ-A-03, REQ-A-04, REQ-A-05, REQ-A-06, or REQ-IA-05. The analytical overview supplies rows, columns, cells, cell completeness, resolved semantic-type counts, and Empty, Constant, and Identifier identity. The rendered Overview, complete and incomplete rows, physical dtype composition, near-constant columns, high-cardinality columns, memory, and duplicate rows are not delivered.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `93faa29343da25e39e10e478e16dd4bbfd48576d`. The pre-slice TSK-017 baseline was 31 passed. The pre-slice full-suite baseline was 1040 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_dataset_overview.py -q` | 28 passed |
| `pytest tests/test_dataset_analysis.py -q` | 31 passed |
| `pytest tests/test_semantic_pipeline.py -q` | 70 passed |
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
| structural TSK-001 through TSK-005 | 143 passed |
| combined semantic, without the dataset and overview tests | 990 passed |
| `pytest tests/test_dataset_analysis.py -q` again, as the analysis/dataset run | 31 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 1068 passed, 1 failed |

`tests/test_dataset_overview.py` is 28 Slice 018 tests. The combined semantic run stayed 990 passed. The full suite was 1068 passed and 1 failed, which is the previous 1040 plus these 28. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/overview.py` had no missed statements. Total coverage on the full run was 99%.

All 13 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-019 — Slice 019, variables and column-summary foundation

The committed Slice 001 through Slice 018 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `384ebbc`, before this slice.

Approved in the Slice 019 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-090](DECISIONS.md#dec-090). `build_variables_summary` accepts a `DatasetAnalysis` and returns a frozen `VariablesSummary`. It does not accept a DataFrame. Each physical column becomes one `VariableSummary` in source order. Common facts are position, the original label, the physical dtype, resolution status, selected semantic type, and the four basic counts. `unique_ratio_non_missing` uses the non-missing denominator. A candidate-derived Numeric, Identifier, or Categorical selection is resolved while `interpretation` is `None`. Confidence and inference source are not copied. Numeric detail copies retained numeric-structure counts. Monotonicity `None` stays unknown. Mean, median, and the other descriptive summaries are not added. `analyze_series` collects existing `FrequencyEvidence` for a non-structural physical categorical column. Categorical detail copies the most frequent count and the singleton count, not the most frequent value. Identifier detail copies pattern counts. Overlap is not a score. A constant UUID stays Constant. Empty, Constant, Boolean, Datetime, Timedelta, Text, insufficient evidence, and ambiguity have no specialized detail. The constant value is not retained. Ordinary strings do not collect frequency evidence and do not become Categorical or Text. `StringContentEvidence` stays uncollected. The variables module does not import pandas and does not rescan. [OPEN-043](DECISIONS.md#open-questions) records the detail-applicability narrowing. [OPEN-045](DECISIONS.md#open-questions) records the product-summary location. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049) stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/variables.py` | Variables summary. No pandas import and no semantic inference. |
| `src/pytics/analysis/column.py` | Retains frequency evidence for a non-structural physical categorical column. |
| `src/pytics/analysis/__init__.py` | Package description now includes the variables summary. |

Not modified: semantic candidate rules, evidence collector contracts, `DatasetAnalysis`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `ColumnEvidence` gained the optional `frequency` field. `StringContentEvidence` stays uncollected.

Tests: `tests/test_variables.py`. `tests/test_dataset_analysis.py` and `tests/test_semantic_pipeline.py` record that frequency evidence is now collected on that categorical path and still is not a semantic rule.

What was not implemented: mean, median, standard deviation, quantiles, skewness, kurtosis, and outlier signals; the most frequent category value and the frequency distribution; Boolean true/false counts; datetime span and calendar structure; timedelta duration statistics; Text detail; the constant value; candidate confidence; Findings; a rendered Variables table; a public result; a change to `profile` or `compare`.

Left open, and not decided in this slice: Binary representation ([OPEN-014](DECISIONS.md#open-questions)); ordinal storage ([OPEN-016](DECISIONS.md#open-questions)); near-constant and high-cardinality thresholds ([OPEN-018](DECISIONS.md#open-questions)); string-content profile role ([OPEN-019](DECISIONS.md#open-questions)); the rest of downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); candidate confidence ([OPEN-044](DECISIONS.md#open-questions), [OPEN-047](DECISIONS.md#open-047)); the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); evidence strength ([OPEN-048](DECISIONS.md#open-048)); override behavior ([OPEN-049](DECISIONS.md#open-049)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-B-01, REQ-B-02, REQ-C-01, REQ-C-02, REQ-C-04, REQ-G-01, REQ-G-02, or REQ-IA-07. The analytical variables summary supplies universal column facts and the first Numeric, Categorical, and Identifier details. Descriptive numeric statistics, the frequency distribution, Boolean counts, datetime analysis, duration analysis, Text detail, and the rendered table are not delivered.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `384ebbcb5b82ff21e9995d5f3a860a7ce58303d0`. The pre-slice full-suite baseline was 1068 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_variables.py -q` | 44 passed |
| `pytest tests/test_dataset_overview.py -q` | 28 passed |
| `pytest tests/test_dataset_analysis.py -q` | 31 passed |
| `pytest tests/test_semantic_pipeline.py -q` | 70 passed |
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
| structural TSK-001 through TSK-005 | 143 passed |
| combined semantic, without the dataset, overview, and variables tests | 990 passed |
| `pytest tests/test_dataset_analysis.py -q` again, as the analysis/dataset run | 31 passed |
| `pytest tests/test_dataset_overview.py -q` again, as the overview run | 28 passed |
| `pytest tests/test_profiler.py -q` | 19 passed, 1 failed |
| `pytest tests -q` | 1112 passed, 1 failed |

`tests/test_variables.py` is 44 Slice 019 tests. The combined semantic run stayed 990 passed. The full suite was 1112 passed and 1 failed, which is the previous 1068 plus these 44. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/variables.py` and `analysis/column.py` had no missed statements. Total coverage on the full run was 99%.

All 14 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-020 — Slice 020, numeric descriptive analysis foundation

The committed Slice 001 through Slice 019 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `c84d73c`, before this slice.

Approved in the Slice 020 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-091](DECISIONS.md#dec-091). Descriptive statistics for a Numeric column live in `pytics.analysis`, not in `pytics.semantics`. `analyze_series` resolves the semantic type first. Only a selected `SemanticType.NUMERIC` then receives `NumericDescriptiveAnalysis`, retained on `ColumnAnalysis.numeric_analysis`. `ColumnEvidence` and `InferredSemanticResult` do not gain those fields. The population is finite and non-missing. Missing values and both infinities are excluded. An empty finite population leaves every statistic `None`. Minimum and maximum of integer storage stay exact Python integers. Mean and sample standard deviation are float64, with `ddof=1`. Q1, the median, and Q3 use one linear interpolation, Hyndman-Fan type 7. A non-integral integer quantile stays a `Fraction` when float64 would leave the exact extrema. `-0.0` is stored as `0.0`. Range and interquartile range are derived. `NumericVariableDetail` keeps the TSK-019 structural counts and copies the frozen descriptive result. The variables builder does not calculate and does not rescan. Constant numeric columns stay Constant and are not described. No semantic rule changed. [OPEN-010](DECISIONS.md#open-questions) records that this pass is exact and full-column. [OPEN-043](DECISIONS.md#open-questions) records that the pass follows the selected Numeric type. [OPEN-044](DECISIONS.md#open-questions) records that the statistics are not inference thresholds. [OPEN-045](DECISIONS.md#open-questions) records `numeric.py` in the analysis package. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-018](DECISIONS.md#open-questions) is not narrowed. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/numeric.py` | Finite-population descriptive model and calculation. |
| `src/pytics/analysis/column.py` | Collects that result after a Numeric selection and retains it on the column analysis. |
| `src/pytics/analysis/variables.py` | Copies the frozen result onto Numeric detail. No statistical calculation. |
| `src/pytics/analysis/__init__.py` | Package description now names the post-resolution descriptive pass. |

Not modified: semantic candidate rules, evidence collector contracts, `DatasetAnalysis`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `variables.py` grew from 683 lines to 725. The added lines copy and validate the composed result. They do not calculate it.

Tests: `tests/test_numeric_descriptive.py`. `tests/test_variables.py` and `tests/test_dataset_analysis.py` record that the builder still does not rescan and that structural columns do not retain descriptive analysis.

What was not implemented: sum; mode; stored variance; MAD; coefficient of variation; skewness; kurtosis; histograms; distribution fitting; normality tests; outlier or anomaly detection; confidence intervals; robust estimators; Findings; the constant numeric value; Boolean counts; datetime or timedelta description; Text detail; a rendered table; a public result; a change to `profile` or `compare`.

Left open, and not decided in this slice: mode contents and sampling ([OPEN-010](DECISIONS.md#open-questions)); near-constant and high-cardinality thresholds ([OPEN-018](DECISIONS.md#open-questions)); the rest of downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); candidate confidence and inference thresholds ([OPEN-044](DECISIONS.md#open-questions)); the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

Two float64 limits remained open at the end of this slice. Distinct integers above float64 precision could produce an incorrect sample standard deviation of `0.0`. An extreme finite float range could make the sample standard deviation non-representable, and collection raised `ValueError`. TSK-025 later resolves both. See that record and [DEC-096](DECISIONS.md#dec-096).

This slice does not approve a later slice. It does not complete REQ-B-01 or REQ-B-02. Numeric analysis is not complete.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `c84d73cfd378dbcae6e6f1dec987ba14d49067f0`. The pre-slice full-suite baseline was 1112 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_numeric_descriptive.py -q` | 22 passed |
| semantic, analysis, overview, and variables regression, without `tests/test_profiler.py` | 1115 passed |
| `pytest tests -q` | 1134 passed, 1 failed |

The focused file is 22 Slice 020 tests. The regression without the profiler is the previous non-profiler total plus these 22. The full suite is the previous 1112 passed plus these 22. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/numeric.py`, `analysis/column.py`, and `analysis/variables.py` had no missed statements on the full run. Total coverage on the full run was 99%.

On a 200,000-row frame, collecting the descriptive result for one float64 column took about 26 ms and for one int64 column about 17 ms. `analyze_dataframe` on a five-column frame of that size stayed about 2.1 s; skipping the descriptive pass changed that time by roughly 50 ms, inside the noise of the rest of the analysis. `build_variables_summary` on that analysis took about 0.1 ms. The descriptive collector ran for the selected Numeric columns and did not run for string, Boolean, or constant numeric columns. Peak traced memory during one 1.6 MB float64 collection was about 6.4 MB and was released with the result. The source Series is scanned again only for a selected Numeric column: missing values are dropped, floating values are filtered to finite numbers, and the finite population is sorted once. Q1, the median, and Q3 are read from that sorted copy. Mean and sample standard deviation scan it again. Non-Numeric columns are not scanned for this result.

All 12 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-021 — Slice 021, Boolean descriptive analysis foundation

The committed Slice 001 through Slice 020 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `5515a99`, before this slice.

Approved in the Slice 021 session on 2026-10-03. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-092](DECISIONS.md#dec-092). True and false counts for a Boolean column live in `pytics.analysis`, not in `pytics.semantics`. `analyze_series` resolves the semantic type first. Only a selected `SemanticType.BOOLEAN` then receives `BooleanDescriptiveAnalysis`, retained on `ColumnAnalysis.boolean_analysis`. `ColumnEvidence` and `InferredSemanticResult` do not gain those fields. `True` increments `true_count` only. `False` increments `false_count` only. Missing values increment neither. `n_non_missing` is the sum of those counts and is not stored. The ratios divide by that non-missing count and are not stored. A zero sum leaves both ratios `None`. Empty still precedes Constant, and Constant still precedes Boolean. `{0, 1}` and `{0.0, 1.0}` stay Numeric. Two-valued strings and categorical boolean values are not counted. `BooleanVariableDetail` copies the counts. The variables builder does not count and does not rescan. `numeric_analysis` and `boolean_analysis` stay separate fields. No registry was added. No semantic rule changed. [OPEN-010](DECISIONS.md#open-questions) records that this pass is exact and full-column. [OPEN-043](DECISIONS.md#open-questions) records that the pass follows the selected Boolean type. [OPEN-044](DECISIONS.md#open-questions) records that the ratios are not inference thresholds. [OPEN-045](DECISIONS.md#open-questions) records `boolean.py` in the analysis package. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-014](DECISIONS.md#open-questions) and [OPEN-046](DECISIONS.md#open-046) stay open. The TSK-020 float64 limits stay open: distinct integers above float64 precision can produce an incorrect sample standard deviation of `0.0`, and an extreme finite float range can make that deviation non-representable and raise `ValueError`. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/boolean.py` | True/false descriptive model and calculation. |
| `src/pytics/analysis/column.py` | Collects that result after a Boolean selection and retains it on the column analysis. |
| `src/pytics/analysis/variables.py` | Copies the counts onto Boolean detail. No counting. |
| `src/pytics/analysis/__init__.py` | Package description now names the Boolean pass. |

Not modified: semantic modules, Numeric descriptive calculation, `DatasetAnalysis`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `variables.py` grew from 725 lines to 790. The added lines copy and validate the counts. They do not calculate them.

Tests: `tests/test_boolean_descriptive.py`. `tests/test_variables.py`, `tests/test_numeric_descriptive.py`, and `tests/test_dataset_analysis.py` record that a selected Boolean variable now has Boolean detail, that the builder still does not rescan, and that the new field is not a retained Series.

What was not implemented: a Binary semantic type; inference from `{0, 1}`, `{0.0, 1.0}`, true/false strings, or yes/no strings; categorical Boolean reinterpretation; entropy; confidence intervals; hypothesis tests; target relationships; Findings; charts; a rendered table; a public result; a change to `profile` or `compare`; the TSK-020 numeric precision limits.

Left open, and not decided in this slice: Boolean versus Binary representation ([OPEN-014](DECISIONS.md#open-questions)); `{0.0, 1.0}` as binary evidence ([OPEN-046](DECISIONS.md#open-046)); mode contents and sampling ([OPEN-010](DECISIONS.md#open-questions)); the rest of downstream eligibility ([OPEN-043](DECISIONS.md#open-questions)); the rest of the module layout ([OPEN-045](DECISIONS.md#open-questions)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-D-01, REQ-D-02, or REQ-D-03. Boolean/Binary analysis is not complete.

Verification, 2026-10-03, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `5515a991da3cb8f44dbf9bf8eece80c5d9b64907`. The pre-slice full-suite baseline was 1134 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_boolean_descriptive.py -q` | 14 passed |
| semantic, analysis, overview, and variables regression, without `tests/test_profiler.py` | 1129 passed |
| `pytest tests -q` | 1148 passed, 1 failed |

The focused file is 14 Slice 021 tests. The regression without the profiler is the previous non-profiler total plus these 14. The full suite is the previous 1134 passed plus these 14. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/boolean.py`, `analysis/column.py`, and `analysis/variables.py` had no missed statements on the full run. Total coverage on the full run was 99%.

On a 200,000-row Series, collecting the Boolean result for dense `bool` storage took about 0.1 ms. The same length of nullable `boolean` storage, with every tenth value missing, took about 3 ms. `analyze_dataframe` on a six-column frame of that size stayed about 2.2 s. `build_variables_summary` on that analysis took about 0.2 ms. The Boolean collector ran for the selected Boolean columns and did not run for integer `{0, 1}`, floating values, strings, or a constant Boolean column. The collector drops missing values, then counts `True` in the remaining boolean array. `False` is the remainder. Dense `bool` storage did not allocate a second copy of the values. Nullable storage allocated a temporary boolean array of the non-missing values; peak traced memory for that collection was about 3.4 MB and was released with the result. The pass is exact, full-column, and unsampled.

All 12 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-022 — Slice 022, missing-data analysis foundation

The committed Slice 001 through Slice 021 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `f1feb79`, before this slice.

Approved in the Slice 022 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-093](DECISIONS.md#dec-093). Missingness structure lives in `pytics.analysis`, not in `pytics.semantics`. `analyze_dataframe` still analyzes each physical column once. It then counts exact row missingness and exact missingness patterns from one `DataFrame.isna` pass and retains that result on `DatasetAnalysis.missing_analysis`. The boolean mask is not retained. `build_missing_summary` accepts that analysis and returns a frozen `MissingSummary`. It copies cell facts and basic-evidence column counts. It does not rescan. Patterns are tuples of physical positions, ordered by descending row count and then by ascending positions. The empty pattern is the complete-row pattern. A zero-row frame has no buckets and no patterns. A frame with rows and no columns has one empty pattern, cell ratios `None`, and row ratios `1.0` and `0.0`. Pandas missingness is the only missingness. Empty strings, whitespace, and `"NA"` stay observed. There is no mechanism classification, no imputation, and no pairwise coefficient. [OPEN-010](DECISIONS.md#open-questions) records that this pass is exact and unsampled, with no pattern cutoff. [OPEN-018](DECISIONS.md#open-questions) records the complete-row definition and leaves the missing-like literal list open. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-044](DECISIONS.md#open-questions) records that the ratios are not inference thresholds. [OPEN-045](DECISIONS.md#open-questions) records `missing.py` in the analysis package. The TSK-020 float64 limits stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/missing.py` | Retained missingness aggregates, the DataFrame pattern pass, and the product summary. |
| `src/pytics/analysis/dataset.py` | Retains `missing_analysis` and collects it after the column analyses. |
| `src/pytics/analysis/__init__.py` | Package description now names the missingness pass. |

Not modified: `src/pytics/analysis/variables.py`, `src/pytics/analysis/overview.py`, `src/pytics/analysis/column.py`, semantic modules, Numeric descriptive calculation, Boolean counting, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `variables.py` stays 790 lines. `missing.py` is 506 lines and 235 statements.

Tests: `tests/test_missing_analysis.py`. `tests/missing_margins.py` builds a fixture pattern set for manual `DatasetAnalysis` values. `tests/test_dataset_analysis.py`, `tests/test_dataset_overview.py`, `tests/test_variables.py`, `tests/test_boolean_descriptive.py`, and `tests/test_numeric_descriptive.py` pass `missing_analysis` explicitly.

What was not implemented: missing-like literal diagnostics; imputation; cleaning; MCAR, MAR, or MNAR classification; Little's MCAR test; pairwise co-missingness coefficients; a missingness correlation matrix; clustering; heatmaps; Findings; a renderer; target-conditioned missingness; compare or drift missingness; sampling or mode cutoffs; a public `profile` change; a pattern-count threshold.

Left open, and not decided in this slice: mode contents and any future sample of wide missingness ([OPEN-010](DECISIONS.md#open-questions)); the missing-like literal list ([OPEN-018](DECISIONS.md#open-questions)); relationships between missingness and observed values of other variables; co-missingness coefficients; the rendered Missing view; and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-H-01, REQ-H-02, REQ-H-03, REQ-H-04, REQ-H-05, REQ-A-03, or REQ-IA-08. Missing analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `f1feb79f669eb63089c0cbf2cd5316af7462512b`. The pre-slice full-suite baseline was 1148 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_missing_analysis.py -q` | 16 passed |
| `pytest tests -q` | 1164 passed, 1 failed |

The focused file is 16 Slice 022 tests. The full suite is the previous 1148 passed plus these 16. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/missing.py` and `analysis/dataset.py` had no missed statements on the full run. `analysis/variables.py`, `analysis/overview.py`, `analysis/column.py`, `analysis/numeric.py`, and `analysis/boolean.py` had no missed statements either. Total coverage on the full run was 99%.

On representative float64 frames, seeded with NumPy generator 22, the missingness collection median of three calls and the surrounding `analyze_dataframe` time were:

| Shape | Missingness | Collection | `analyze_dataframe` | Summary builder | Patterns | Traced peak | Retained aggregates |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100,000 × 10 | mostly complete, NaNs confined to a prefix of the first column | 35 ms | 282 ms | 0.05 ms | 2 | 2.9 MiB | 0.7 KiB |
| 100,000 × 10 | independent 15% missing cells | 48 ms | 257 ms | 2.0 ms | 734 | 2.9 MiB | 69 KiB |
| 100,000 × 10 | five repeated position patterns | 36 ms | 206 ms | 0.07 ms | 5 | 2.9 MiB | 1.2 KiB |
| 10,000 × 100 | mostly complete, same prefix construction | 13 ms | 313 ms | 0.4 ms | 2 | 2.0 MiB | 3.8 KiB |
| 10,000 × 100 | independent 15% missing cells | 169 ms | 482 ms | 49 ms | 10,000 | 4.7 MiB | 1.7 MiB |
| 10,000 × 100 | five repeated position patterns | 13 ms | 262 ms | 0.4 ms | 5 | 2.0 MiB | 4.6 KiB |

`analyze_dataframe` includes the column analyses and the missingness pass. The collection column is that pass alone. Pandas `DataFrame.isna` materializes a boolean mask. On these frames the mask was column-major, so the collector made one temporary C-contiguous copy and did not keep either array. The new raw pass is that one `DataFrame.isna` call. Existing per-column evidence scans are unchanged. Retained patterns cannot exceed the row count, because only observed rows are counted. The 10,000 × 100 random frame reached that bound: every row had its own pattern. The power set of columns is not enumerated. There is no top-k cutoff.

All 12 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-023 — Slice 023, duplicate-data analysis foundation

The committed Slice 001 through Slice 022 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `58c8a8e`, before this slice.

Approved in the Slice 023 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-094](DECISIONS.md#dec-094). Exact duplicate rows live in `pytics.analysis`, not in `pytics.semantics`. `analyze_dataframe` still analyzes each physical column once, then collects missingness, then collects duplicate groups. The two dataset passes do not call each other. `DatasetAnalysis.duplicate_analysis` retains one `DuplicateGroup` per repeated row value. A group stores strictly increasing physical positions. `size` and `excess_count` are derived. Singleton positions are not stored. Row values are not stored. Order is descending size, then ascending first position, then the position tuple. Row equality is `pandas.factorize` on each physical column, with the default missing sentinel, compared as an exact int64 code tuple. `None`, `np.nan`, and `pd.NA` share a column's missing code. `"NA"`, case, whitespace, and unequal floats do not. `-0.0` matches `0.0` under that equality. The index and column labels are not part of the row. Unhashable `list`, `dict`, and `set` cells raise `TypeError` when comparison is required. A `0 × 0` or `0 × N` frame has no groups. A `1 × 0` frame has one unique empty row. An `N × 0` frame with `N >= 2` has one group of every position, which is not what pandas `drop_duplicates` returns. `DuplicateSummary` stores `n_rows` and copied groups. `DatasetOverview` copies `n_unique_rows` and `n_excess_duplicate_rows` and does not store groups. There is no quality score and no Finding. [OPEN-010](DECISIONS.md#open-questions) records that this pass is exact and unsampled, with no group cutoff. [OPEN-018](DECISIONS.md#open-questions) records the exact full-row definitions and leaves controlled partial duplicates open. [OPEN-020](DECISIONS.md#open-questions) records that fuzzy scope stays open. [OPEN-037](DECISIONS.md#open-questions) records this slice and does not choose the next one. [OPEN-044](DECISIONS.md#open-questions) records that the ratios are not inference thresholds. [OPEN-045](DECISIONS.md#open-questions) records `duplicate.py` in the analysis package. The TSK-020 float64 limits and the TSK-022 missingness limits stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/duplicate.py` | Retained duplicate groups, the factorize pass, and the product summary. |
| `src/pytics/analysis/dataset.py` | Retains `duplicate_analysis` and collects it after missingness. |
| `src/pytics/analysis/overview.py` | Copies unique-row and excess-duplicate counts from that analysis. |
| `src/pytics/analysis/__init__.py` | Package description now names the duplicate pass. |

Not modified: `src/pytics/analysis/variables.py`, `src/pytics/analysis/missing.py`, `src/pytics/analysis/column.py`, semantic modules, Numeric descriptive calculation, Boolean counting, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `variables.py` stays 790 lines. `missing.py` stays 506 lines. `duplicate.py` is 389 lines and 183 statements.

Tests: `tests/test_duplicate_analysis.py` (35 tests). `tests/test_dataset_overview.py` adds the duplicate-count rejection checks and the zero-size overview assertions. Manual `DatasetAnalysis` constructors in the existing analysis tests pass an explicit `duplicate_analysis`.

What was not implemented: identifier duplicates; conflicting duplicates; partial duplicates; near-duplicate normalization or scoring; duplicate-column detection; Findings; a renderer; sampling or a group cutoff; a public `profile` change.

Left open, and not decided in this slice: mode contents and any future sample or cap on stored positions ([OPEN-010](DECISIONS.md#open-questions)); controlled partial duplicates ([OPEN-018](DECISIONS.md#open-questions)); fuzzy or near-duplicate scope ([OPEN-020](DECISIONS.md#open-questions)); the rendered Duplicates view; and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-I-01, REQ-I-02, REQ-I-03, REQ-I-04, REQ-A-04, REQ-IA-05, or REQ-IA-09. Duplicate analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6. Before this slice the working tree was clean and `main` matched `origin/main` at `58c8a8ea49dc7aa5848c6407064c4d691e2db64b`. The pre-slice full-suite baseline was 1164 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_duplicate_analysis.py tests/test_dataset_overview.py tests/test_dataset_analysis.py tests/test_missing_analysis.py tests/test_variables.py tests/test_boolean_descriptive.py tests/test_numeric_descriptive.py -q` | 191 passed |
| `pytest tests -q` | 1200 passed, 1 failed |

The focused duplicate file is 35 tests. The full suite is the previous 1164 passed plus these 35 and one overview rejection test. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/duplicate.py`, `analysis/dataset.py`, and `analysis/overview.py` had no missed statements on the full run. `analysis/variables.py`, `analysis/missing.py`, `analysis/numeric.py`, and `analysis/boolean.py` had no missed statements either. Total coverage on the full run was 99%.

On representative int64 frames, seeded with NumPy generator 23, the duplicate collection median of three calls and the surrounding `analyze_dataframe` time were:

| Shape | Rows | Collection | `analyze_dataframe` | Summary builder | Missing collection | Groups | Rows in groups | Traced collection peak | Retained groups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100,000 × 10 | all unique | 128 ms | 317 ms | 0.01 ms | 31 ms | 0 | 0 | 34 MiB | 96 B |
| 100,000 × 10 | 1,000 repeated values | 169 ms | 322 ms | 29 ms | 32 ms | 1,000 | 100,000 | 25 MiB | 3.5 MiB |
| 10,000 × 100 | all unique | 92 ms | 322 ms | 0.01 ms | 12 ms | 0 | 0 | 31 MiB | 96 B |
| 100,000 × 10 | 5 repeated values | 136 ms | 254 ms | 26 ms | 34 ms | 5 | 100,000 | 25 MiB | 3.4 MiB |

`analyze_dataframe` includes the column analyses, the missingness pass, and the duplicate pass. The collection column is the duplicate pass alone. The missing column is `collect_missing_analysis` on the same frame. The duplicate pass is several times the missing pass and still a minority of `analyze_dataframe` on these numeric frames. A separate 20,000 × 5 unique-string frame spent 29 ms in duplicate collection and 1,125 ms in `analyze_dataframe`, because the string column analyses dominate. Collector-only medians at 100,000 rows were 127 ms for int64 × 10, 170 ms for float64 × 10, 172 ms for bool × 10, 117 ms for datetime × 4, and 150 ms for string × 4. The source-value read is one `factorize` per physical column. The temporary int64 code matrix is then grouped once and discarded. Source values are not read again. Retained positions are bounded by the rows that belong to a duplicate group. The all-unique frames retain no positions.

All 12 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-024 — Slice 024, numeric relationship-analysis foundation

The committed Slice 001 through Slice 023 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `37a5d8a`, before this slice.

Approved in the Slice 024 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-095](DECISIONS.md#dec-095). Relationships live in `pytics.analysis`, not in `pytics.semantics`. `analyze_dataframe` still analyzes each physical column once, then collects missingness, then duplicate groups, then relationships. The three dataset passes do not call each other. `DatasetAnalysis.relationship_analysis` is an explicit field beside `missing_analysis` and `duplicate_analysis`. No registry was added. A pair is two physical positions with the left position smaller. Labels are not identity. The only calculated family is selected `SemanticType.NUMERIC` × selected `SemanticType.NUMERIC`. Recognized but unimplemented families are counts. Ineligible pairs, including Identifier, Constant, Empty, Text, Timedelta, and unresolved columns, are one count. Unsupported pairs do not retain a record and do not read raw values. Each selected Numeric column is converted once inside the collector. Those arrays are discarded before return. The statistical population is the rows where both source values are finite. Missing values and infinities are excluded. Spearman is the primary descriptive association, from `scipy.stats.spearmanr(x, y)`. Pearson is complementary, from `scipy.stats.pearsonr(x, y)`. The Pearson interval is classical Fisher z at 95%, implemented in this package because a library interval would exceed the SciPy 1.7 floor. Spearman has no interval. Raw two-sided p-values are stored when `n_paired >= 3`. Adjusted p-values are not calculated. There is no normality gate, no significance flag, no strength label, and no Finding. Float64 is the computational image. Integers that vary but collapse in that image make both methods unavailable. `RelationshipsSummary` copies the retained records and does not recompute. [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings in this slice and stay open. The TSK-020 float64 limits, the TSK-022 missingness limits, and the TSK-023 duplicate limits stay open. Internal names below are not a public schema.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/relationship.py` | Pair eligibility, Spearman and Pearson, and the product summary. |
| `src/pytics/analysis/dataset.py` | Retains `relationship_analysis` and collects it after duplicates. |
| `src/pytics/analysis/__init__.py` | Package description now names the relationship pass. |

Not modified: semantic modules, Numeric descriptive calculation, Boolean counting, missingness, duplicate grouping, the overview builder, the variables builder, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `relationship.py` is 1456 lines and 690 statements. `ColumnRef` in `overview.py` was not reused, because the relationship engine would then import the overview builder. The pair stores position and the original label directly.

Tests: `tests/test_relationship_analysis.py` (25 tests). Manual `DatasetAnalysis` constructors in the existing analysis tests pass an explicit `relationship_analysis`.

What was not implemented: Numeric × Boolean, Numeric × Categorical, Boolean × Boolean, Categorical × Categorical, datetime relationships, ordinal relationships, Spearman intervals, multiple-testing adjustment, assumption tests, Findings, charts, and a rendered Relationships view.

Left open, and not decided in this slice: the test family for multiple-testing correction ([OPEN-007](DECISIONS.md#open-questions)); the rest of the method catalog ([OPEN-006](DECISIONS.md#open-questions)); mode contents ([OPEN-010](DECISIONS.md#open-questions)); the shared statistical API ([OPEN-038](DECISIONS.md#open-questions)); the rendered Relationships view; and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, REQ-P-10, REQ-G-03, REQ-IA-11, or REQ-T-05. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, SciPy 1.18.1. The declared floor remains `scipy>=1.7.0`. Before this slice the working tree was clean and `main` matched `origin/main` at `37a5d8a2a5821813191ddfdfe72c7f592b12ddac`. The pre-slice full-suite baseline was 1200 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_relationship_analysis.py tests/test_dataset_analysis.py tests/test_dataset_overview.py tests/test_missing_analysis.py tests/test_duplicate_analysis.py tests/test_variables.py tests/test_numeric_descriptive.py tests/test_boolean_descriptive.py -q` | 216 passed |
| `pytest tests -q` | 1225 passed, 1 failed |

The focused relationship file is 25 tests. The full suite is the previous 1200 passed plus these 25. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. `analysis/relationship.py` and `analysis/dataset.py` had no missed statements on the full run. `analysis/numeric.py`, `analysis/boolean.py`, `analysis/missing.py`, `analysis/duplicate.py`, `analysis/overview.py`, and `analysis/variables.py` had no missed statements either. Total coverage on the full run was 99%.

On seeded NumPy generator 24, the relationship-collection median of three calls, without tracing inside the timed call, was:

| Frame | Eligible / total pairs | Collection | `analyze_dataframe` | Builder | Traced peak | Retained |
| --- | --- | --- | --- | --- | --- | --- |
| 100,000 × 5 int64 | 10 / 10 | 460 ms | 616 ms | 0.26 ms | 16 MiB | 7.7 KiB |
| 20,000 × 20 float64 | 190 / 190 | 1,895 ms | 2,035 ms | 4.45 ms | 6.1 MiB | 132 KiB |
| 20,000 × 50 mixed | 3 / 1,225 | 33 ms | 197 ms | 0.10 ms | 3.0 MiB | 3.5 KiB |
| 20,000 × 3 with pairwise missing | 3 / 3 | 26 ms | 53 ms | 0.09 ms | 2.5 MiB | 2.9 KiB |

`analyze_dataframe` includes column analyses, missingness, duplicates, and relationships. The collection column is `collect_relationship_analysis` alone. The mixed frame has 3 selected Numeric columns, 30 Boolean columns, and 17 Categorical columns. Its 1,222 unsupported pairs are counts only. The collector reads each selected Numeric column once and does not read unsupported columns for correlation. SciPy is then called once per method per eligible pair. That statistical work dominates the 190-pair frame. A full numeric-matrix cache was not added. Temporary arrays do not survive the collector. Retained memory follows the number of analyzed pairs, not the number of unsupported pairs.

All 12 acceptance criteria in the implementation plan passed. Dependency files were not changed.

### TSK-025 — Slice 025, numeric robustness and relationship architecture

The committed Slice 001 through Slice 024 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `cd4d700`, before this slice.

Approved in the Slice 025 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-096](DECISIONS.md#dec-096). A selected Numeric column with valid finite observations is not rejected because a derived statistic is not a finite float64. `None` means unavailable. It is not zero and not NaN. Minimum, maximum, and the type-7 quartiles stay when the finite population defines them. Integer extrema stay exact. Sample standard deviation stays `ddof=1`. Integer values outside `[-2**53, 2**53]` are centered by their minimum in integer arithmetic before the float64 mean and deviation. A difference of 1 does not become a false zero deviation. Differences above `2**53` can still round. There is no arbitrary-precision statistic. The ordinary float mean uses NumPy. An overflowing sum uses a scaled `math.fsum`. Float quantiles use a weighted average so `right - left` overflow does not invent an infinite quantile. Range and interquartile range are `None` when the difference is not finite, and an integer difference stays exact. The selected type stays Numeric. Relationship rules from [DEC-095](DECISIONS.md#dec-095) are unchanged, including float64 precision collapse. The implementation now lives in `pytics.analysis.relationships`: `models.py`, `numeric_numeric.py`, and `collector.py`. `pytics.analysis.relationship` re-exports it. No registry and no new family were added. [OPEN-006](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings and stay open. The TSK-022 missingness limits, the TSK-023 duplicate limits, and the TSK-024 float64 relationship precision collapse stay open.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/numeric.py` | Finite-population descriptive statistics, with independent unavailability. |
| `src/pytics/analysis/relationships/models.py` | Shared relationship records. No SciPy import. |
| `src/pytics/analysis/relationships/numeric_numeric.py` | Spearman, Pearson, and the Fisher z interval. |
| `src/pytics/analysis/relationships/collector.py` | Pair eligibility, collection, and the product summary. |
| `src/pytics/analysis/relationships/__init__.py` | Package exports. |
| `src/pytics/analysis/relationship.py` | Re-export used by dataset analysis and existing tests. |

Not modified: semantic modules, Boolean counting, missingness, duplicate grouping, the overview builder, the variables builder's calculations, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. The variables builder still copies the retained descriptive object.

Tests: new cases live in `tests/test_numeric_descriptive.py`. `tests/test_relationship_analysis.py` still has 25 tests. Monkeypatch targets that follow the moved functions now point at the module that defines them.

What was not implemented: any new relationship family, multiple-testing correction, bootstrap or permutation intervals, Bayesian methods, Findings, visualizations, mode selection, and arbitrary-precision statistics.

Left open, and not decided in this slice: float64 relationship precision collapse; relationship pair scaling; the rest of the method catalog ([OPEN-006](DECISIONS.md#open-questions)); mode contents ([OPEN-010](DECISIONS.md#open-questions)); the shared statistical API ([OPEN-038](DECISIONS.md#open-questions)); and the order of later slices ([OPEN-037](DECISIONS.md#open-questions)).

This slice does not approve a later slice. It does not complete REQ-B-01 or REQ-B-02. Numeric analysis is not complete. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8. Before this slice the working tree was clean and `main` matched `origin/main` at `cd4d700401c3d7bd4abe577b8e1c4be3fe622239`. The pre-slice full-suite baseline was 1225 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_relationship_analysis.py -q` | 25 passed |
| `pytest tests/test_numeric_descriptive.py -q` | 36 passed |
| `pytest tests -q` | 1239 passed, 1 failed |

The full suite is the previous 1225 passed plus 14 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%. The 17 missed statements are in `profiler.py` and `visualizations.py`. `numeric.py` and the relationship package had no missed statements.

On this machine, the descriptive-collector minimum of repeated calls was about 24 ms for 200,000 float64 rows and about 16 ms for 200,000 ordinary int64 rows. Before the change, the same script recorded about 23 ms and about 15 ms. A 50,000 × 4 mixed frame stayed about 260 ms in `analyze_dataframe`, matching the pre-change timing. A 200,000-row int64 series offset by `2**60` took about 18 ms and did not report a false zero deviation. A four-value series at the float64 extreme finished in under 1 ms, with a finite mean and an undefined sample deviation and range. The large-integer path allocates one temporary unsigned offset array and one float64 array. Those arrays are not retained. The ordinary path still uses one float64 image.

All 12 acceptance criteria in the implementation plan passed. Dependency files were not changed except for a note that the floor was not raised.

### TSK-026 — Slice 026, Numeric × Categorical relationship foundation

The committed Slice 001 through Slice 025 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `1c76264`, before this slice.

Approved in the Slice 026 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-097](DECISIONS.md#dec-097). Selected Numeric × selected Categorical is calculated in `pytics.analysis.relationships.numeric_categorical`. Physical position remains pair identity. Numeric and categorical roles do not follow left and right. The population is a finite Numeric value paired with a non-missing category. Only observed groups are retained, in physical categorical vocabulary order. That order is not an ordinal score. Each group reuses `NumericDescriptiveAnalysis`. The effect is eta squared, `SS_between / SS_total`. The omnibus test is classical one-way ANOVA from `scipy.stats.f_oneway` with no keyword arguments. The null hypothesis is equal group means. The p-value is the raw upper tail. When within-group variation is zero and between-group variation is positive, eta squared may be `1.0` and both the F statistic and the p-value are unavailable. Adjustment is not applied. There is no post-hoc test, no assumption gate, no strength label, and no category cutoff. Boolean is not treated as Categorical. Numeric × Numeric rules are unchanged. [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings and stay open.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/relationships/numeric_categorical.py` | Group summaries, eta squared, and classical one-way ANOVA. |
| `src/pytics/analysis/relationships/models.py` | Shared records plus the Numeric × Categorical result. |
| `src/pytics/analysis/relationships/collector.py` | Pair eligibility, one read per needed column, and the product summary. |
| `src/pytics/analysis/relationship.py` | Re-exports the new records. |

Not modified: semantic modules, Numeric × Numeric formulas, Boolean counting, missingness, duplicate grouping, the overview builder, the variables builder, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. Group descriptions call the existing Numeric calculator. `numeric.py` was not rewritten.

Tests: `tests/test_numeric_categorical_relationship.py`. `tests/test_relationship_analysis.py` now expects Numeric × Categorical pairs to be analyzed.

What was not implemented: Welch ANOVA, Kruskal–Wallis, omega squared, post-hoc tests, multiple-testing correction, assumption diagnostics, Findings, and a high-cardinality cutoff.

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, REQ-P-10, REQ-G-03, REQ-IA-11, or REQ-T-05. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, SciPy 1.18.1. Before this slice the working tree was clean and `main` matched `origin/main` at `1c76264a05bfa67a8b4bfe3f4d5f16fa06c966b3`. The pre-slice full-suite baseline was 1239 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_numeric_categorical_relationship.py tests/test_relationship_analysis.py -q` | 46 passed |
| `pytest tests -q` | 1260 passed, 1 failed |

The full suite is the previous 1239 passed plus 21 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%.

On this machine, seeded with NumPy generator 26, relationship collection and the surrounding `analyze_dataframe` time were:

| Case | Rows | Groups | Collection | `analyze_dataframe` | Builder | Peak traced | Retained relationships | Column reads |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 groups, one numeric | 100,000 | 5 | 19 ms | 132 ms | 0.3 ms | 10.0 MiB | 2.4 KiB | 1 numeric, 1 categorical |
| 100 groups | 100,000 | 100 | 38 ms | 180 ms | 0.7 ms | 10.0 MiB | 33 KiB | 1 numeric, 1 categorical |
| 8,000 groups | 80,000 | 8,000 | 1,555 ms | 5,520 ms | 52 ms | 12.7 MiB | 2.3 MiB | 1 numeric, 1 categorical |
| 4 numeric × 3 categorical | 100,000 | 5 each | 543 ms | 844 ms | 0.8 ms | 25.3 MiB | 27 KiB | 4 numeric, 3 categorical |
| 10% missing | 100,000 | 5 | 16 ms | 134 ms | 0.1 ms | 9.7 MiB | 2.4 KiB | 1 numeric, 1 categorical |
| integers at `2**60` | 100,000 | 5 | 17 ms | 281 ms | 0.1 ms | 11.4 MiB | 2.7 KiB | 1 centered integer image |

The 8,000-group collection is the expensive case because every observed group keeps a descriptive record. The full `analyze_dataframe` time on that frame is larger still because the categorical column analysis is included. Twelve Numeric × Categorical pairs in the mixed frame used four numeric reads and three categorical reads, not one read per pair. The ordinary float path did not center integers. The `2**60` path centered once. No category cutoff was applied.

All 12 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-027 — Slice 027, heterogeneous relationship metadata

The committed Slice 001 through Slice 026 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `ac3fd09`, before this slice.

Approved in the Slice 027 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-098](DECISIONS.md#dec-098). `RelationshipAnalysis` and `RelationshipsSummary` store pair coverage and family records. They do not store one primary method, one population rule, one computational image, one confidence level, one adjustment status, or an implemented-family list. Pair counts stay on each pair. Numeric × Numeric population is pairwise finite values, and its computation property is the float64 correlation image. Numeric × Categorical population is a finite numeric value with a non-missing category. That record has no confidence level and no correlation computation property. An available Pearson interval stores its own 95% Fisher-z level. Spearman remains the named primary component of a Numeric × Numeric record. Eta squared and one-way ANOVA stay separate components. Adjustment stays on each frequentist result and is not applied. `RelationshipFamily` names the families this version calculates. Records name the families present in one dataset. Coverage invariants are unchanged. `DatasetAnalysis` keeps one `relationship_analysis` field. The summary copies retained records and does not recompute. Family models stay in `models.py`. The collector does not become a registry. Statistical calculations from TSK-024 through TSK-026 are unchanged. [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings and stay open.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/relationships/models.py` | Shared records, family records, and the coverage containers. Dataset-level method claims removed. |
| `src/pytics/analysis/relationships/collector.py` | Same pair selection and copy. The record union is named `RelationshipRecord`. |
| `src/pytics/analysis/relationship.py` | Internal re-export. Not a public result schema. |
| `src/pytics/analysis/dataset.py` | Still one `relationship_analysis` field. |

Not modified: family statistical formulas, semantic modules, Numeric descriptive calculation, Boolean counting, missingness, duplicate grouping, the overview builder, the variables builder, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `models.py` was not split.

Tests: `tests/test_relationship_metadata.py`. Existing relationship tests now expect the removed dataset claims to be absent.

What was not implemented: a new relationship family, multiple-testing correction, a sampled execution mode, a method registry, a generic statistics schema, Findings, and a rendered Relationships view.

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, REQ-P-10, REQ-G-03, REQ-IA-11, or REQ-T-05. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, SciPy 1.18.1. Before this slice the working tree was clean and `main` matched `origin/main` at `ac3fd0925efd635bed32fd8137043d4dfaca73f9`. The pre-slice full-suite baseline was 1260 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_relationship_metadata.py -o addopts= -q` | 8 passed |
| `pytest tests/test_relationship_analysis.py tests/test_numeric_categorical_relationship.py tests/test_dataset_analysis.py -o addopts= -q` | 77 passed |
| `pytest tests -q` | 1268 passed, 1 failed |

The full suite is the previous 1260 passed plus 8 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%.

On this machine, seeded with NumPy generator 26, the representative mixed frame of 4 Numeric columns, 3 low-cardinality Categorical columns, and 100,000 rows was timed before and after the metadata move. Medians of three calls:

| | Collection | `analyze_dataframe` | Builder | Peak traced | Retained relationships |
| --- | --- | --- | --- | --- | --- |
| Before | 556 ms | 796 ms | 0.78 ms | 16.1 MiB | 27,797 bytes |
| After | 570 ms | 811 ms | 0.83 ms | 16.1 MiB | 27,797 bytes |

The after frame retained 18 records: 6 Numeric × Numeric and 12 Numeric × Categorical. Retained size was 27,797 bytes both times. Traced peak was 16,436 KiB before and 16,438 KiB after. A 200-row mixed frame stayed in the same few-millisecond band. The differences are run-to-run noise. Moving metadata did not change the statistical work or the retained record size.

All 12 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-028 — Slice 028, Boolean × Boolean relationships

The committed Slice 001 through Slice 027 code was the development baseline. `git status` was clean, `main` matched `origin/main`, and both were `8c8a7b1`, before this slice.

Approved in the Slice 028 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-099](DECISIONS.md#dec-099). A selected Boolean × selected Boolean pair keeps a 2×2 table, two conditional outcome-True probabilities, a probability difference, a probability ratio, phi, and a raw two-sided Fisher exact p-value. The conditioning variable is the left physical column. The outcome variable is the right physical column. Those roles are not causes. The population is pairwise non-missing Boolean values. An absent conditioning level is not stored as probability zero. An exact infinite probability ratio is unavailable. No continuity correction and no confidence interval are added. SciPy's odds ratio is not stored. A constant paired margin does not store Fisher's degenerate p-value of `1.0`. Adjustment stays unapplied. `RelationshipFamily` now includes Boolean × Boolean. Dataset-level relationship fields are unchanged. Boolean descriptive counts are not reused as pairwise counts. No semantic rule changed. [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-008](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), and [OPEN-045](DECISIONS.md#open-questions) record the narrowings and stay open.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/relationships/boolean_boolean.py` | 2×2 counts, probability effects, phi, and the Fisher call. |
| `src/pytics/analysis/relationships/models/` | Shared vocabulary, one module per calculated family, and the coverage container. Re-exports the previous names. |
| `src/pytics/analysis/relationships/collector.py` | Boolean eligibility, one preparation per Boolean column, and the summary copy. |
| `src/pytics/analysis/relationship.py` | Internal re-export. Not a public result schema. |

Not modified: semantic inference, Boolean descriptive counting, Numeric × Numeric formulas, Numeric × Categorical formulas, `DatasetAnalysis` fields, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_boolean_boolean_relationship.py`. Existing relationship tests now treat Boolean × Boolean as calculated.

What was not implemented: an odds ratio, Cramér's V, a Boolean confidence interval, Pearson chi-square, Barnard's test, Boschloo's test, Categorical × Categorical, a generic RxC table, a multiple-testing correction, Findings, and a rendered Relationships view.

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, REQ-P-10, REQ-G-03, REQ-IA-11, or REQ-T-05. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, SciPy 1.18.1. Before this slice the working tree was clean and `main` matched `origin/main` at `8c8a7b1cfe5e0675fc7d5a751c5d04c2eef32447`. The pre-slice full-suite baseline was 1268 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_boolean_boolean_relationship.py -o addopts= -q` | 36 passed |
| `pytest tests -q` | 1304 passed, 1 failed |

The full suite is the previous 1268 passed plus 36 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%.

Boolean × Boolean collection was timed as the median of three calls. NumPy generator seeds were 28 and 29. Peak traced memory is a separate collection call and is not process RSS. A fake Fisher call isolates the exact-test cost. Preparations are one per Boolean column.

| Case | Rows | Boolean columns | Pairs | Preparations | Collection | `analyze_dataframe` | Builder | Fisher portion | Peak traced |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| One pair, 1% missing | 1,000,000 | 2 | 1 | 2 | 35 ms | 1,376 ms | 0.16 ms | 2.5 ms | 13.5 MiB |
| Ten columns, 1% missing | 100,000 | 10 | 45 | 10 | 678 ms | 1,028 ms | 2.1 ms | 600 ms | 3.0 MiB |
| Thirty columns, 1% missing | 50,000 | 30 | 435 | 30 | 4,142 ms | 4,382 ms | 16 ms | 3,841 ms | 4.0 MiB |
| Ten columns, 10% missing | 100,000 | 10 | 45 | 10 | 628 ms | 1,034 ms | 1.5 ms | 531 ms | 2.8 MiB |

Counting and preparation without Fisher were about 300 ms for the 435-pair frame. Fisher is the dominant cost once there are many Boolean pairs. Exactly balanced or perfectly separated tables returned in about a millisecond or less in a separate SciPy probe, including million-scale counts. The slower tables are large near-null random tables, about 9 ms each at 50,000 rows on SciPy 1.18.1. The `method` keyword was not passed. The test was not replaced. The pair count remains `b * (b - 1) / 2`.

All 12 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-029 — Slice 029, Numeric × Boolean relationships

The committed Slice 001 through Slice 028 code was the development baseline. `main` matched `origin/main`, and both were `f185ab6`, before this slice. The working tree was not clean when the session started: `src/pytics/analysis/relationships/models/coverage.py` held two uncommitted hunks from an interrupted earlier attempt. They referenced a record type that did not exist and left the package unimportable. That file was restored to `f185ab6` before work began. No other tracked file differed.

Approved in the Slice 029 session on 2026-10-04. This record was written after verification in that same session.

Decision recorded with the slice: [DEC-100](DECISIONS.md#dec-100). A selected Numeric × selected Boolean pair keeps the Numeric and Boolean roles, a False group and a True group, the True − False mean difference, Hedges' g, a 95% Welch–Satterthwaite interval for the mean difference, and Welch's two-sample t-test with its degrees of freedom and raw two-sided p-value. The orientation is True minus False whichever physical side is Boolean, and it is not causal. The population is a finite Numeric value with a non-missing Boolean value. Each observed group uses the Numeric descriptive calculator. An absent level is an unavailable group. Group moments for the effects and the test are taken on offsets from each group's own exact minimum, and the two means are combined exactly. A large common integer magnitude therefore does not create a false zero difference or a false zero spread. Hedges' g uses the exact gamma correction and needs two pooled degrees of freedom. Zero pooled variation is undefined or unbounded, not a number. The Welch interval and test use `scipy.stats.t` on the declared floor. They are unavailable for one-value groups and for two constant groups, and SciPy's infinite statistic is not stored. No assumption test selects the method. Adjustment stays unapplied. `RelationshipFamily` now includes Numeric × Boolean. `BooleanLevel` moved to the shared model module. No semantic rule changed. [OPEN-004](DECISIONS.md#open-questions), [OPEN-006](DECISIONS.md#open-questions), [OPEN-007](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-037](DECISIONS.md#open-questions), [OPEN-038](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), and [OPEN-046](DECISIONS.md#open-046) record the narrowings and stay open.

Production files:

| Path | Purpose |
| --- | --- |
| `src/pytics/analysis/relationships/numeric_boolean.py` | Group values, group moments, the mean difference, Hedges' g, the Welch interval, and the Welch test. |
| `src/pytics/analysis/relationships/models/numeric_boolean.py` | Numeric × Boolean records and their consistency rules. |
| `src/pytics/analysis/relationships/models/common.py` | `RelationshipFamily.NUMERIC_BOOLEAN`, plus `BooleanLevel` and one validator moved from the Boolean × Boolean model module. |
| `src/pytics/analysis/relationships/models/boolean_boolean.py` | Imports the moved names. No Boolean × Boolean rule changed. |
| `src/pytics/analysis/relationships/models/coverage.py` | Fourth `RelationshipRecord` variant. Numeric × Boolean removed from the unimplemented families. |
| `src/pytics/analysis/relationships/models/__init__.py` | Re-exports the new records. |
| `src/pytics/analysis/relationships/collector.py` | Numeric × Boolean eligibility, one direct branch, reuse of the Numeric and Boolean preparations, the record check, and the summary copy. |
| `src/pytics/analysis/relationships/__init__.py`, `src/pytics/analysis/relationship.py` | Internal re-exports. Not a public result schema. |
| `src/pytics/analysis/dataset.py` | Docstring only. The relationship pass describes every calculated family. |

Not modified: semantic inference, Numeric descriptive calculation, Boolean descriptive counting, the Numeric × Numeric, Numeric × Categorical, and Boolean × Boolean formulas, `DatasetAnalysis` fields, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_numeric_boolean_relationship.py`. `tests/test_relationship_analysis.py`, `tests/test_relationship_metadata.py`, `tests/test_boolean_boolean_relationship.py`, and `tests/test_numeric_categorical_relationship.py` now count Numeric × Boolean pairs as calculated. Their statistical expectations for the earlier families are unchanged.

What was not implemented: Categorical × Boolean, Categorical × Categorical, target analysis, Student's pooled t-test, Mann–Whitney U, Brunner–Munzel, a permutation test, Cohen's d, Glass's delta, a median-difference component, an interval for Hedges' g, a multiple-testing correction, Findings, and a rendered Relationships view.

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, REQ-P-10, REQ-G-03, REQ-IA-11, or REQ-T-05, and it does not advance the REQ-L rows. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1. Before this slice `main` matched `origin/main` at `f185ab69ae6ebfbcd78473b27f05b076514fdb57`. The pre-slice full-suite baseline was 1304 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_numeric_boolean_relationship.py -o addopts= -q` | 39 passed |
| `pytest tests/test_relationship_analysis.py tests/test_relationship_metadata.py tests/test_boolean_boolean_relationship.py tests/test_numeric_categorical_relationship.py tests/test_dataset_analysis.py -o addopts= -q` | 121 passed |
| `pytest tests -q` | 1343 passed, 1 failed |

The full suite is the previous 1304 passed plus 39 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%. The new calculator and record modules are fully covered.

Numeric × Boolean collection was timed on frames from NumPy generator seed 29, with 1% missing values in every column. Collection, `analyze_dataframe`, and the builder are medians of three calls. Component times come from one instrumented collection call. Peak traced memory is a separate collection call and is not process RSS. Retained size is the sum of `sys.getsizeof` over the unique objects reachable from the retained records, excluding enum members. Preparations are one per Numeric column and one per Boolean column.

| Case | Rows | Pairs, of which Numeric × Boolean | Preparations | Collection | `analyze_dataframe` | Builder | Numeric × Boolean family | Group description | Group moments | SciPy `t` | Peak traced | Retained relationships |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Numeric, 1 Boolean | 1,000,000 | 1, 1 | 1 + 1 | 171 ms | 1,531 ms | 0.09 ms | 166 ms | 36 ms | 21 ms | 0.4 ms | 33.7 MiB | 1,318 bytes |
| 5 Numeric, 5 Boolean | 100,000 | 45, 25 | 5 + 5 | 963 ms | 1,241 ms | 1.7 ms | 333 ms | 58 ms | 37 ms | 12 ms | 17.4 MiB | 42,014 bytes |
| 15 Numeric, 15 Boolean | 50,000 | 435, 225 | 15 + 15 | 4,827 ms | 5,207 ms | 15 ms | 1,555 ms | 277 ms | 194 ms | 93 ms | 14.4 MiB | 394,304 bytes |
| 1 Int64 column near `2**60`, 1 Boolean | 1,000,000 | 1, 1 | 1 + 1 | 139 ms | 1,897 ms | 0.06 ms | 135 ms | 43 ms | 27 ms | 0.5 ms | 38.9 MiB | 1,438 bytes |

Masking, indexing, and sorting each pair's group values took 59% to 64% of the family time in the one-pair and fifteen-by-fifteen frames. Profiling the one-pair frame put most of that in the first sort of each group, which is the order the group quartiles need. The descriptive calculator then sorts its already sorted input again, at about 14 ms per million values. The Hedges and Welch arithmetic is negligible. Each `scipy.stats.t` call costs about 0.2 ms. The rest of collection in the mixed frames is Numeric × Numeric and Boolean × Boolean work, which this slice did not change. Pair-local masks and group arrays are discarded after each pair. No sample, pair cutoff, or quartile shortcut was added. The pair count is `n_numeric * n_boolean`.

Before acceptance, a focused statistical audit checked Hedges' g. The correction matched an independent sixty-digit evaluation of the gamma recurrence `Γ(x + 1) = x Γ(x)`, with a maximum relative error of 6.3e-16 from 2 to 4,000 degrees of freedom and about 4e-17 at 10^4, 10^5, and 10^6. The truncation error of the asymptotic series converged to its next coefficient, which confirms the coefficients used. End-to-end g matched an exact rational reference to 5.0e-15 at group sizes from (2, 2) to (1000, 1000). The closed form `(345/32) √(2π/365)` matched to 1.6e-16. The audit corrected the one-degree-of-freedom wording in [DEC-100](DECISIONS.md#dec-100) and in two docstrings: the correction is undefined there, and only its limit is zero. It recorded the normal, equal-variance condition behind the unbiasedness and the naming convention. It made the existing correction test independent of `math.gamma`, extended the Hedges reference to those group sizes, and added a closed-form test and a test that the correction is not evaluated below two degrees of freedom. No formula, availability rule, or stored value changed.

All 12 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-030 — Slice 030, Categorical × Categorical relationships

Completed 2026-10-04. The slice calculates selected Categorical × selected Categorical association. It does not change semantic inference. It does not render a relationship, and it does not add target analysis.

What was implemented:

| File | Role |
| --- | --- |
| `src/pytics/analysis/relationships/categorical_categorical.py` | Pairwise non-missing population, sparse observed contingency counts, classical Cramér's V, expected-count diagnostics, and uncorrected Pearson chi-square. |
| `src/pytics/analysis/relationships/models/categorical_categorical.py` | Frozen contingency table, association, diagnostics, chi-square evidence, and the pair record. |
| `src/pytics/analysis/relationships/models/common.py` | `RelationshipFamily.CATEGORICAL_CATEGORICAL`. `_require_category_scalar` moved here because two families retain category scalars. |
| `src/pytics/analysis/relationships/models/coverage.py` | Fifth `RelationshipRecord` variant. Categorical × Categorical removed from the unimplemented families. |
| `src/pytics/analysis/relationships/models/numeric_categorical.py` | Imports the shared category-scalar check. No statistical change. |
| `src/pytics/analysis/relationships/collector.py` | Categorical × Categorical eligibility, one direct branch, reuse of the categorical preparation, the record check, and the summary copy. |
| `src/pytics/analysis/relationships/models/__init__.py`, `src/pytics/analysis/relationships/__init__.py`, `src/pytics/analysis/relationship.py` | Internal re-exports. Not a public result schema. |

Not modified: semantic inference, Numeric descriptive calculation, Boolean descriptive counting, the Numeric × Numeric, Numeric × Categorical, Boolean × Boolean, and Numeric × Boolean formulas, `DatasetAnalysis` fields, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_categorical_categorical_relationship.py`. `tests/test_relationship_analysis.py`, `tests/test_relationship_metadata.py`, `tests/test_boolean_boolean_relationship.py`, `tests/test_numeric_categorical_relationship.py`, and `tests/test_numeric_boolean_relationship.py` now count Categorical × Categorical pairs as calculated. Their statistical expectations for the earlier families are unchanged.

What was not implemented: bias-corrected Cramér's V, a confidence interval, Theil's U, mutual information, the G-test, Fisher exact, the Fisher–Freeman–Halton test, Monte Carlo inference, Categorical × Boolean, datetime relationships, target analysis, a multiple-testing correction, Findings, and a rendered Relationships view.

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, REQ-P-10, REQ-G-03, REQ-IA-11, or REQ-T-05, and it does not advance the REQ-L rows. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1. Before this slice `main` matched `origin/main` at `52f6939588bedfb284c282c60eecd236fc872a2e`. The pre-slice full-suite baseline was 1343 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_categorical_categorical_relationship.py -o addopts= -q` | 22 passed |
| `pytest tests/test_relationship_analysis.py tests/test_relationship_metadata.py tests/test_boolean_boolean_relationship.py tests/test_numeric_categorical_relationship.py tests/test_numeric_boolean_relationship.py tests/test_dataset_analysis.py -o addopts= -q` | 180 passed |
| `pytest tests -q` | 1365 passed, 1 failed |

The full suite is the previous 1343 passed plus 22 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%.

Categorical × Categorical collection was timed on frames from NumPy generator seed 30, with about 1% missing values. Collection, `analyze_dataframe`, and the builder are medians of three calls. Component times come from one instrumented `analyze_dataframe` call. Peak traced memory is a separate collection call and is not process RSS. Retained size is the sum of `sys.getsizeof` over the unique objects reachable from the retained records, excluding enum members.

| Case | Rows | Categorical columns | Pairs | Observed cells | Possible cells | Preparation | Contingency | Chi-square and V | Collection | `analyze_dataframe` | Builder | Peak traced | Retained relationships |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 × 10 | 1,000,000 | 2 | 1 | 100 | 100 | 2.0 ms | 54 ms | 0.5 ms | 66 ms | 1,729 ms | 0.3 ms | 27.2 MiB | 13,715 bytes |
| 100 × 100 | 250,000 | 2 | 1 | 10,000 | 10,000 | 0.8 ms | 27 ms | 6.6 ms | 35 ms | 531 ms | 6.9 ms | 7.9 MiB | 821,275 bytes |
| 1,000 × 1,000 diagonal | 100,000 | 2 | 1 | 1,000 | 1,000,000 | 2.8 ms | 19 ms | 0.8 ms | 29 ms | 167 ms | 1.8 ms | 10.9 MiB | 251,535 bytes |
| 10 columns, about 20 levels | 100,000 | 10 | 45 | 18,000 | 18,000 | 2.7 ms | 251 ms | 27 ms | 298 ms | 484 ms | 17 ms | 5.0 MiB | 1,674,486 bytes |

The million-row pass spends almost all of its family time building the contingency, not evaluating chi-square. `analyze_dataframe` on that frame is dominated by the rest of the dataset pass. The 1,000 by 1,000 case retains 1,000 positive cells against 1,000,000 possible cells. Its traced peak is about 11 MiB, which includes the temporary histogram of at most `2**20` bins, not a Python object per possible cell. Ten columns are prepared once. Each of the 45 pairs then builds its own contingency. No sample and no pair cutoff were added.

All 10 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-031 — Slice 031, relationship statistical consolidation

Completed 2026-10-04. The slice treats the five calculated relationship families as one statistical subsystem. It applies Benjamini–Hochberg to the available primary test of each calculated pair and classifies Categorical × Boolean as unimplemented. It does not add a calculator, and it does not change `profile` or `compare`.

What was implemented:

| File | Role |
| --- | --- |
| `src/pytics/analysis/relationships/adjustment.py` | Dataset-level Benjamini–Hochberg adjustment of the available primary p-value, and frozen replacement of that frequentist component. |
| `src/pytics/analysis/relationships/collector.py` | Calls the adjustment after pair records exist. Classifies Categorical × Boolean as unimplemented in either physical order. |
| `src/pytics/analysis/relationships/models/common.py` | `BENJAMINI_HOCHBERG`, and frequentist invariants for an adjusted p-value. |
| `src/pytics/analysis/relationships/models/coverage.py` | `CATEGORICAL_BOOLEAN`, and the calculated, unimplemented, and ineligible meanings. |
| `src/pytics/analysis/relationships/models/numeric_numeric.py` | Pearson stays outside the correction family. |
| Family calculators and the other family models | Raw evidence remains the calculator output. Primary components may later carry the adjusted value. No formula changed. |

Not modified: semantic inference, the five statistical formulas, `DatasetAnalysis` fields, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_relationship_adjustment.py`. Existing relationship tests now expect primary adjustment on analyzed pairs and count Categorical × Boolean as unimplemented.

What was not implemented: Categorical × Boolean calculation, datetime relationship methods, robust or rank alternatives, exact or resampling tests, a method registry, target analysis, Findings, and a rendered Relationships view.

This slice does not approve a later slice. It does not complete REQ-K-01, REQ-K-02, REQ-K-04, or REQ-P-10, and it does not advance the REQ-L rows. Relationship analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1. Statsmodels is not installed and is not required. Before this slice `main` matched `origin/main` at `520e4f8860b1dbc71041b9bd63822f14cefbbfab`. The pre-slice full-suite baseline was 1365 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests -q` | 1394 passed, 1 failed |

The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. Total coverage on the full run was 99%.

On this machine, correction of 100, 1,000, 10,000, and 100,000 synthetic p-values took about 0.25 ms, 2.8 ms, 41 ms, and 416 ms. Additional traced memory was about 6 KiB, 131 KiB, 1.2 MiB, and 12.1 MiB. A 4,000-row frame with 6 Numeric, 3 Categorical, and 3 Boolean columns had 66 physical pairs, 57 calculated pairs, and 57 corrected hypotheses. Pair analysis took about 143 ms, adjustment about 1.9 ms, relationship collection about 145 ms, and the summary builder about 4.3 ms.

All 9 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-032 — Slice 032, target analysis foundation

Completed 2026-10-04. The slice projects an explicitly requested target from semantic state, descriptive facts, and relationship records that dataset analysis already retained. It does not fit a diagnostic model, and it does not change `profile` or `compare`.

What was implemented:

| File | Role |
| --- | --- |
| `src/pytics/analysis/target.py` | Explicit target resolution, the eligibility matrix, population, reused descriptive facts, relationship links with orientation, and the source-free summary. |
| `src/pytics/analysis/dataset.py` | Optional `target` argument and `DatasetAnalysis.target_analysis`. `None` when no target is requested. |
| `src/pytics/analysis/relationships/models/coverage.py` | `classify_selected_pair`, shared by the relationship collector and the target projection. |
| `src/pytics/analysis/relationships/collector.py` | Pair classification calls that shared decision. No formula changed. |

Not modified: semantic inference, descriptive calculators, the five relationship formulas, Benjamini–Hochberg, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`.

Tests: `tests/test_target_analysis.py`. `tests/test_dataset_analysis.py` and `tests/test_relationship_metadata.py` record `target_analysis` on the dataset field list and expect `None` when no target is requested.

What was not implemented: a diagnostic model, train/test split, cross-validation, permutation importance, predictive performance, leakage detection, feature ranking, target encoding, preprocessing, class weights, threshold optimization, a problem-type label, a target-only multiple-testing correction, per-level categorical counts, and a rendered Target view.

This slice does not approve a later slice. It does not complete REQ-L-01, REQ-L-02, REQ-L-03, REQ-L-04, REQ-L-05, REQ-L-07, REQ-T-05, REQ-IA-12, or REQ-P-14. REQ-L-06 stays in force. Target analysis is not complete. Predictive target analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1. Before this slice `main` matched `origin/main` at `4f78d21d39e21c88e6e0099ed84f783c354df225`. The pre-slice full-suite baseline was 1394 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_target_analysis.py -o addopts= -q` | 29 passed |
| `pytest tests/test_relationship_analysis.py tests/test_relationship_metadata.py tests/test_relationship_adjustment.py tests/test_boolean_boolean_relationship.py tests/test_numeric_boolean_relationship.py tests/test_numeric_categorical_relationship.py tests/test_categorical_categorical_relationship.py tests/test_dataset_analysis.py tests/test_dataset_overview.py tests/test_variables.py tests/test_boolean_descriptive.py tests/test_numeric_descriptive.py tests/test_semantic_pipeline.py tests/test_inferred_semantics.py -o addopts= -q` | 473 passed |
| `pytest tests -q` | 1423 passed, 1 failed |

The full suite is the previous 1394 passed plus 29 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%.

On this machine, NumPy generator seed 32, a 20,000-row frame with 8 Numeric, 4 Boolean, and 4 Categorical columns had 120 physical pairs, 104 calculated pairs, and 16 unimplemented Categorical × Boolean pairs. Medians of three calls: `analyze_dataframe` about 725 ms, the same call with an explicit Boolean target about 713 ms, relationship collection about 626 ms, target projection about 0.7 ms, and target summary construction about 0.6 ms. The projection indexes retained records. It does not scan rows.

All 9 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-033 — Slice 033, target statistical analysis

Completed 2026-10-04. The slice adds the exact observed distribution of a selected Categorical column and reuses that result for a Categorical target. It does not fit a diagnostic model, and it does not change `profile` or `compare`.

What was implemented:

| File | Role |
| --- | --- |
| `src/pytics/analysis/categorical.py` | Exact observed level counts, vocabulary order, the physical `ordered` flag, and derived proportions. |
| `src/pytics/analysis/column.py` | Collects that result after a Categorical selection, whether or not the column is the target. |
| `src/pytics/analysis/variables.py` | Copies the frozen distribution onto Categorical detail. Aggregate frequency counts stay. |
| `src/pytics/analysis/boolean.py` | Derives observed-class and largest/smallest class facts from the existing true and false counts. |
| `src/pytics/analysis/target.py` | Reuses the categorical descriptive object by identity. Removes the aggregate-only categorical workaround. |

Not modified: semantic inference, `FrequencyEvidence` and its retention limit of 32, Numeric descriptive calculation, the five relationship formulas, Benjamini–Hochberg, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `pyproject.toml`. `target.py` was not split. It went from 969 lines to 901.

Tests: `tests/test_categorical_descriptive.py`. `tests/test_target_analysis.py`, `tests/test_boolean_descriptive.py`, `tests/test_variables.py`, and `tests/test_numeric_descriptive.py` record the reuse, the Boolean class facts, and the variables copy.

What was not implemented: a diagnostic model, a problem type, an imbalance verdict, a target-only test, feature ranking, entropy, a cardinality band, and a rendered Target or Variables view.

This slice does not approve a later slice. It does not complete REQ-C-02, REQ-C-04, REQ-C-05, REQ-L-01, or REQ-L-02. REQ-L-06 stays in force. Target analysis is not complete. Predictive target analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1. Before this slice `main` matched `origin/main` at `dfb59a4`. The pre-slice full-suite baseline was 1423 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests -q` | 1440 passed, 1 failed |

The full suite is the previous 1423 passed plus 17 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%.

On this machine, categorical descriptive collection was exact and unsampled. 1,000,000 rows and 10 levels took about 9 ms and retained about 1.4 KiB. The traced peak was about 9.8 MiB of temporary codes, not the result. 250,000 rows and 100 levels took about 3 ms and retained about 13 KiB. 100,000 rows and 1,000 levels took about 10 ms and retained about 100 KiB. 100,000 rows and 100,000 observed levels took about 0.4–0.6 s and retained about 10 MiB, with a traced peak around 16 MiB. That cost is one record per observed level. The code array is not retained, and the distribution was not sampled. Column analysis still also collects frequency evidence, which is a separate `value_counts` pass with the retention limit of 32. The target projection does not scan. NumPy generator seed 32, a 20,000-row frame with 8 Numeric, 4 Boolean, and 4 Categorical columns still had 104 calculated pairs. Medians of three calls: `analyze_dataframe` about 707 ms, the same call with an explicit Boolean target about 709 ms, relationship collection about 616 ms, categorical target projection about 0.3 ms, and categorical target summary construction about 1.4 ms.

All 9 acceptance criteria in the implementation plan passed. No dependency was added and the SciPy floor was not raised.

### TSK-034 — Slice 034, lightweight target diagnostic model

Completed 2026-10-04. The slice adds one untuned diagnostic model for an explicit target, scored on a held-out split against a naive baseline, with held-out permutation importance of original input columns. It does not tune, compare, or select models, it does not change target analysis or relationships, and it does not change `profile` or `compare`.

What was implemented:

| File | Role |
| --- | --- |
| `src/pytics/analysis/target_diagnostic.py` | Frozen diagnostic result, the task mapping, predictor decisions, metric and importance records, consistency rules, the dataset attachment check, and the copy used by the summary. No scikit-learn import. |
| `src/pytics/analysis/target_diagnostic_fit.py` | The only scikit-learn importer. Target-side eligibility from retained facts, predictor screening, the holdout split, the training-only pipeline, the baseline, held-out metrics, and permutation importance. |
| `src/pytics/analysis/dataset.py` | `DatasetAnalysis.target_diagnostic`, present exactly when a target was requested, and its attachment check. |
| `src/pytics/analysis/target.py` | `TargetSummary.diagnostic`, a copied diagnostic. `TargetAnalysis` and the projection are unchanged. |
| `pyproject.toml` | `scikit-learn>=1.3` runtime dependency. |

Not modified: semantic inference, descriptive calculators, the five relationship formulas, Benjamini–Hochberg, `TargetAnalysis`, `src/pytics/__init__.py`, `src/pytics/profiler.py`, `src/pytics/visualizations.py`, and `requirements-pinned.txt`. `target.py` went from 901 to 911 lines and was not split.

Tests: `tests/test_target_diagnostic.py`, 35 tests. `tests/test_target_analysis.py`, `tests/test_dataset_analysis.py`, and `tests/test_relationship_metadata.py` record the new dataset field and its absence without a target.

What was not implemented: hyperparameter search, a second estimator, cross-validation, calibration, threshold choice, class weights, SHAP, model export, a prediction API, leakage analysis beyond the exact-copy guard, confidence intervals for held-out metrics, a predictability label, a public seed, sampling, and a rendered Target view.

This slice does not approve a later slice. It does not complete REQ-L-01, REQ-L-03, REQ-L-04, REQ-L-05, REQ-L-07, REQ-G-03, REQ-P-12, REQ-IA-12, or REQ-P-14. REQ-L-06 stays in force. Target analysis is not complete.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1. Before this slice `main` matched `origin/main` at `6682416`. The pre-slice full-suite baseline was 1440 passed and 1 failed. scikit-learn was not installed in `.venv` before this slice and was installed for it.

| Command | Result |
| --- | --- |
| `pytest tests/test_target_diagnostic.py -o addopts= -q` | 35 passed |
| `pytest tests/test_target_analysis.py -o addopts= -q` | 29 passed |
| `pytest tests/test_relationship_analysis.py tests/test_relationship_metadata.py tests/test_relationship_adjustment.py tests/test_boolean_boolean_relationship.py tests/test_numeric_boolean_relationship.py tests/test_numeric_categorical_relationship.py tests/test_categorical_categorical_relationship.py -o addopts= -q` | 180 passed |
| `pytest tests/test_dataset_analysis.py tests/test_dataset_overview.py tests/test_variables.py tests/test_boolean_descriptive.py tests/test_numeric_descriptive.py tests/test_categorical_descriptive.py tests/test_semantic_pipeline.py tests/test_inferred_semantics.py -o addopts= -q` | 281 passed |
| `pytest tests -q` | 1475 passed, 1 failed |

The full suite is the previous 1440 passed plus 35 tests. The only failure is `tests/test_profiler.py::test_pdf_export`: `TypeError: '<' not supported between instances of 'float' and 'str'` in `xhtml2pdf`. That is the documented baseline PDF failure. No previously passing test failed. Total coverage on the full run was 99%. `target_diagnostic.py` was fully covered. `target_diagnostic_fit.py` missed two internal invariant raises. The 12 warnings come from legacy `profiler.py`.

The training-only test was checked against two deliberate mutations of the fitting code: imputing medians on all modeling rows before the split, and fitting the whole preprocessor on all modeling rows and freezing it. Both made the test fail. The mutations were removed.

Independent checks: stratified split sizes against `ceil(n_class / 4)` clipped to `[1, n_class - 1]`, and the regression split against `ceil(n / 4)`; ROC AUC, macro one-versus-rest ROC AUC, balanced accuracy, and log loss against `sklearn.metrics` on predictions rebuilt from the source frame; R², MAE, and RMSE against `sklearn.metrics`; baselines against training proportions and the training mean computed in the test; and permutation importance of a known signal against pure noise.

On this machine, NumPy generator seed 32, a 20,000-row frame with 8 Numeric, 4 Boolean, and 4 Categorical columns and 16 included predictors, medians of three calls:

| Target | Base `analyze_dataframe` | Relationships | Preprocess and fit | Baseline | Validation scoring | Permutation importance | Diagnostic total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Boolean, binary | 876 ms | 754 ms | 108 ms | 1 ms | 26 ms | 1,805 ms | 1,975 ms |
| Categorical, 5 classes | 854 ms | 745 ms | 197 ms | 1 ms | 33 ms | 1,976 ms | 2,245 ms |
| Numeric | 945 ms | 826 ms | 92 ms | 1 ms | 20 ms | 1,840 ms | 1,989 ms |

At 100,000 rows the same shapes took 3.5–4.0 s for the base analysis and 4.9–6.2 s for the diagnostic, of which permutation importance was 4.4–5.1 s. One rescoring of 5,000 validation rows took about 17.6 ms, of which the model's own probability calculation was about 0.6 ms. The rest re-encodes unchanged columns. A 100-level and a 900-level Categorical predictor were included, adding up to about 0.06 s to fitting. A 5,000-level predictor had 4,728 training levels and was excluded as `TOO_MANY_LEVELS`. The diagnostic runs only for an explicit target. Nothing is sampled.

All 11 acceptance criteria in the implementation plan passed.

### TSK-034b — hardening of Slice 034

Completed 2026-10-04, before TSK-034 was committed. This is a hardening pass, not a new slice and not a new decision. It makes held-out permutation importance faster without changing its meaning or its values, corrects requirement states, and repairs the task log. The performance figures in the TSK-034 record above are the pre-hardening measurements.

Root cause. In TSK-034, each of the 80 permuted scorings at 20,000 rows called the full pipeline, so the `ColumnTransformer` re-encoded every input to permute one. Under a profiler, 3.43 s of 3.83 s of importance time was `ColumnTransformer.transform`, of which 1.52 s was `OneHotEncoder`. The model's own probability calculation was a small part.

Change. `_permutation_importance` encodes the validation rows once. `_owned_columns` maps each included input to its encoded columns from the fixed preprocessing layout. `_block_mover` moves those columns together by one row order and keeps the others. `_validation_permutations` generates the five row orders in Pytics with NumPy `RandomState`, reproducing the orders TSK-034 drew through scikit-learn. `sklearn.inspection.permutation_importance` is no longer called. Every fitted transformation — median imputation, missing indicator, standardization, and one-hot encoding with an all-zero row for an unseen level — computes each encoded value from one input value of the same row. Moving an input's encoded rows therefore gives the same matrix as permuting the source column and encoding it. The retained result, seed, repeat count, scorers, and validation population are unchanged.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/target_diagnostic_fit.py` | Encode-once permutation importance: `_owned_columns`, `_validation_permutations`, and `_block_mover`. 808 to 899 lines, 359 to 412 statements. |
| `tests/test_target_diagnostic.py` | Equivalence tests against a source-column-permutation reference and against `sklearn.inspection.permutation_importance` for seven fixtures, a controlled-order test of block movement, and a row-order test. Three existing tests now spy on or patch the new functions instead of `permutation_importance`. |

Not modified: `target_diagnostic.py`, the result model, the task mapping, the split, the preprocessing, the estimators, the baselines, the metrics, predictor eligibility, `pyproject.toml`, target analysis, relationships, and Benjamini–Hochberg.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1. HEAD was `6682416` with TSK-034 uncommitted. The pre-hardening full suite was 1475 passed and 1 failed.

| Command | Result |
| --- | --- |
| `pytest tests/test_target_diagnostic.py -o addopts= -q -k "block_permutation or controlled_order or validation_permutations"` | 9 passed |
| `pytest tests/test_target_diagnostic.py -o addopts= -q` | 44 passed |
| `pytest tests/test_target_analysis.py -o addopts= -q` | 29 passed |
| The relationship command in the TSK-034 record | 180 passed |
| The descriptive and semantic command in the TSK-034 record | 281 passed |
| `pytest tests -q` | 1484 passed, 1 failed |

The full suite is the previous 1475 passed plus 9 test cases. The only failure is `tests/test_profiler.py::test_pdf_export`, the documented legacy PDF failure. Total coverage was 99%. `target_diagnostic.py` was fully covered. `target_diagnostic_fit.py` missed two internal invariant raises: every class in the training rows, and every encoded column owned by exactly one input.

Equivalence. Seven fixtures cover a Numeric input with a dense design, a Numeric input with missing values, infinities, and a missing indicator, a Boolean input with missing values, a Categorical input with a missing level and validation-only levels, and mixed binary, multiclass, and regression frames. Every repeat of every input, the mean, and the standard deviation agree with a source-column-permutation reference within `1e-12`. Every repeat also agrees with `sklearn.inspection.permutation_importance` on the fitted pipeline within `1e-12`. A controlled-order test replaces the row orders and checks that each scored matrix exactly equals encoding after the source permutation, that every moved column moves by the same order, and that no other column moves. The scaled value and missing indicator moved as two columns. A Boolean input with missing values moved as three columns. A Categorical input moved all five levels present on the validation rows. Strong-signal, negative-importance, held-out, ordering, scorer, determinism, relationship, and Benjamini–Hochberg tests are unchanged and pass.

On this machine, the TSK-034 benchmark frames, NumPy generator seed 32, 8 Numeric, 4 Boolean, and 4 Categorical columns. The 20,000-row figures are medians of three calls and the 100,000-row figures are one call. Before is the TSK-034 importance path and after is the hardened path, measured in the same session:

| Frame | Base | Fit | Baseline | Scoring | Permutation before → after | Diagnostic total before → after | Importance peak before → after | Largest value difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20,000 rows, binary | 779 ms | 101 ms | 1 ms | 22 ms | 1,699 → 220 ms | 1,858 → 373 ms | 4.4 → 3.4 MiB | 1.1e-16 |
| 20,000 rows, 5 classes | 775 ms | 177 ms | 1 ms | 30 ms | 1,734 → 343 ms | 1,994 → 589 ms | 4.4 → 3.7 MiB | 2.2e-16 |
| 20,000 rows, Numeric | 849 ms | 90 ms | 1 ms | 19 ms | 1,610 → 211 ms | 1,746 → 392 ms | 4.4 → 3.3 MiB | 2.2e-16 |
| 100,000 rows, binary | 3,390 ms | 394 ms | 6 ms | 66 ms | 4,817 → 998 ms | 5,435 → 1,591 ms | 19.6 → 16.9 MiB | 5.6e-17 |
| 100,000 rows, 5 classes | 3,354 ms | 858 ms | 5 ms | 95 ms | 5,095 → 1,600 ms | 6,218 → 2,703 ms | 19.6 → 17.9 MiB | 2.2e-16 |
| 100,000 rows, Numeric | 3,768 ms | 321 ms | 1 ms | 52 ms | 4,363 → 913 ms | 4,888 → 1,423 ms | 19.6 → 16.6 MiB | 1.1e-16 |
| 20,000 rows, binary, 900-level input | 2,534 ms | 162 ms | 1 ms | 25 ms | 1,839 → 239 ms | 2,063 → 460 ms | 4.6 → 3.6 MiB | 1.1e-16 |
| 100,000 rows, binary, 900-level input | 5,197 ms | 517 ms | 4 ms | 65 ms | 5,071 → 1,175 ms | 5,779 → 1,899 ms | 20.8 → 17.8 MiB | 1.1e-16 |

The peak is the traced allocation during the importance call. The encoded validation matrix stays sparse whenever a one-hot block exists. For one input at a time the path holds that input's moved part, the kept part, and one permuted matrix. They are released before the next input, and none is retained.

Requirement states. REQ-L-04 and REQ-L-05 are fully delivered as written and are now Implemented. That is the first use of that state. REQ-L-01, REQ-L-02, REQ-L-03, REQ-L-07, REQ-G-03, REQ-P-02, and REQ-P-12 stay Not started because each is only partly delivered or is a broader principle. REQ-L-07 still lacks a rendered correlated-predictor warning, and REQ-L-03 leakage evidence is not delivered. REQ-L-06 and REQ-T-04 stay In force. No row is Completed.

### TSK-035 — target leakage evidence

Completed 2026-10-04. Decision: [DEC-106](DECISIONS.md#dec-106).

The layer records two mechanical facts for an explicit target. An exact duplicate is a same-type Numeric, Boolean, or Categorical predictor equal to the target on every applicable row. Applicable rows are the finite Numeric rows or the non-missing Boolean or Categorical rows, the same rows the diagnostic models. A missing or non-finite predictor value, a disagreement, an empty joint population, and a different semantic type are separate statuses. A repeated deterministic mapping is collected for a Boolean or Categorical target when observed predictor values determine at least two observed classes, at least one predictor value repeats, and no group conflicts. Pure uniqueness, including a unique Identifier, is not that status. A missing target value is not a class. A missing predictor value is not a group. Counts are retained. Values are not. There is no score, probability, severity, association threshold, near-deterministic percentage, affine search, missingness-indicator rule, or temporal rule. The diagnostic excludes an exact duplicate by reading that result and does not compare the column again. A deterministic relabeling can still enter the model. Identifier columns stay excluded because of their semantic type.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/target_leakage.py` | Frozen evidence and the collector. 1,187 lines, 565 statements, 5 retained dataclasses, 3 enums. |
| `src/pytics/analysis/dataset.py` | `target_leakage` beside the projection and the diagnostic. 224 to 253 lines. |
| `src/pytics/analysis/target.py` | The summary copies the leakage result. 911 to 923 lines. |
| `src/pytics/analysis/target_diagnostic_fit.py` | Consumes exact-duplicate positions. The local comparison was removed. 899 to 879 lines, 430 to 421 statements. |
| `src/pytics/analysis/target_diagnostic.py` | The duplicate exclusion is described as consumption of leakage evidence. 929 to 938 lines. Statement count unchanged. |
| `tests/test_target_leakage.py` | Exact copies, mappings, uniqueness, Identifier, the strong-association probe, summary independence, and record guards. |

Not modified: relationship formulas, Benjamini–Hochberg, Identifier inference thresholds, the diagnostic metrics, the split, the estimators, and `pyproject.toml`.

Ownership. Exact duplication lives in the leakage result. Predictor eligibility reads it. The two passes do not both compare the column. Leakage does not call the model, and the model does not build the leakage result.

Order. Column analysis, then relationships, then target projection, leakage evidence, and the diagnostic. Missingness and duplicate-row collection run when the dataset result is built and do not feed leakage. The graph does not read back.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1. HEAD remained `2234c4d`. Nothing was committed.

| Command | Result |
| --- | --- |
| `pytest tests/test_target_leakage.py -o addopts= -q` | 24 passed |
| `pytest tests -q` | 1508 passed, 1 failed |

Functional-dependency counts were compared with an independent pandas group-size calculation: joint rows, distinct groups, repeated groups, conflicting groups, and rows covered by repeated groups. Exact copies of Boolean, Categorical, and Numeric targets stay out of the diagnostic. A relabeled deterministic mapping stays in the model and is `DETERMINISTIC_REPEATED` in the leakage result. A unique Identifier is `TRIVIAL_UNIQUENESS` and is still excluded as Identifier. A categorical predictor with a large Cramér's V, a tiny chi-square p-value, and positive held-out importance is `CONFLICTING`, not a repeated mapping. `y = 2x + 1` on a Numeric target is `NOT_EQUAL`.

On this machine, NumPy generator seed 32, component calls timed separately:

| Frame | Base | Relationships | Leakage | Diagnostic | Full `analyze_dataframe` with target | Traced leakage peak | Retained leakage result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20,000 rows, mixed, Boolean target | 691 ms | 800 ms | 59 ms | 312 ms | 1,064 ms | 2.0 MiB | 3.2 KiB |
| 100,000 rows, mixed, Boolean target | 3,432 ms | 2,898 ms | 368 ms | 1,796 ms | 7,059 ms | 9.7 MiB | 3.3 KiB |
| 100,000 rows, unique Identifier | 5,672 ms | 3,040 ms | 381 ms | 1,360 ms | 7,790 ms | 9.7 MiB | 3.5 KiB |
| 100,000 rows, six deterministic groups | 412 ms | 235 ms | 125 ms | 471 ms | 955 ms | 9.7 MiB | 2.1 KiB |

The 20,000-row relationship call is a separate median and can sit above one base sample. Leakage stayed well below relationships and the diagnostic on the mixed frames. The unique Identifier did not retain a per-row map. The six grouped predictors were `DETERMINISTIC_REPEATED`. Nothing is sampled.

The full suite is the previous 1484 passed plus 24 leakage tests. The only failure is `tests/test_profiler.py::test_pdf_export`, the documented legacy PDF failure. Total coverage was 98%. `target_diagnostic.py` was fully covered. `target_leakage.py` was 95%. The missed lines are defensive raises: an internal copy that cannot change type, a category code outside its vocabulary, and attachment checks that the other attachment checks already make unreachable. `target_diagnostic_fit.py` missed four internal raises. The 12 warnings come from legacy `profiler.py`.

Requirement states. REQ-L-03 stays Not started. The delivered part is exact-duplicate evidence and repeated deterministic classification mappings. Contextual, temporal, near-deterministic, transform, and missingness-indicator leakage remain. REQ-L-04 and REQ-L-05 stay Implemented. REQ-L-06 stays In force. No row is Completed.

All 10 acceptance criteria in the implementation plan passed.

History. The task log above had no TSK-032 or TSK-033 row although both slices were complete and recorded. Those rows were added from their records and from the implementation plan. No date or state was invented. The implementation-plan list of started slices now includes Slice 033 and Slice 034. The implementation-plan traceability sentence that lists TSK-001 through TSK-029, and the approval list in `DEVELOPMENT_PROTOCOL.md` that stops at TSK-024, are not updated by this pass.

### TSK-036 — univariate numeric anomaly analysis

Completed 2026-10-04. Decision: [DEC-107](DECISIONS.md#dec-107).

The question is which finite observations are unusual under Tukey's inner fence, and what evidence shows that. An unusual value is not an error. The fences are `Q1 - (3/2) × IQR` and `Q3 + (3/2) × IQR`, using the quartiles already retained for a selected Numeric column. The coefficient is fixed. A value on the fence is not an anomaly. Missing values stay in the missingness result. Infinities are counted and are not IQR observations. A zero interquartile range does not classify the values that differ from the quartile. There is no minimum sample size. A float64 fence that is not finite is unavailable. Integer fences stay exact. Row identity is the physical position. Every crossing is retained, with direction. Boolean minority classes, rare categories, identifiers, datetimes, durations, and text are not this method. Multivariate detection was not added. There is no score and no severity.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/anomaly.py` | Frozen result, collector, and summary. 1,164 lines, 626 statements, 4 enums, 7 frozen dataclasses. |
| `src/pytics/analysis/dataset.py` | `anomaly_analysis` beside the other dataset results. 253 to 270 lines. |
| `src/pytics/analysis/variables.py` | The numeric detail comment points at the separate anomaly result. |
| `tests/test_anomaly_analysis.py` | Fences, population edges, semantic exclusions, precision, row identity, summary independence, and record guards. |

Not modified: numeric quartile formulas, semantic inference, relationship formulas, the diagnostic model, leakage evidence, and `pyproject.toml`.

Ownership. Quartiles stay on the numeric descriptive result. The anomaly pass reads them and locates rows. It does not calculate a second quantile. Missingness and duplicate analysis are not reread as anomaly evidence.

Order. Column analysis, then relationships, then anomaly location, then, when a target was named, the target projection, leakage evidence, and the diagnostic. Missingness and duplicate-row collection run when the dataset result is built and do not feed the anomaly pass. Naming a target does not change the anomaly result.

Verification, 2026-10-04, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1. HEAD remained `a113e19`. Nothing was committed.

| Command | Result |
| --- | --- |
| `pytest tests/test_anomaly_analysis.py -o addopts= -q` | 34 passed |
| `pytest tests -q` | 1542 passed, 1 failed |

Independent checks used the retained Q1, Q3, and interquartile range, then computed fences and physical positions without calling the anomaly collector. Integer fixtures also recomputed the type-7 quartiles. Large integers above `2**53`, including `2**63 + 1000` stored as `uint64`, stayed exact Python ints and were classified from those ints. A normal float column is fenced in float64. A float population whose upper fence overflows float64 is `NUMERIC_PRECISION_UNSAFE` and has no observations. `+inf` and `-inf` are counts, not fence crossings. A Boolean minority and a singleton category do not receive a numeric anomaly record.

On this machine, NumPy generator seed 32, component calls timed separately:

| Frame | Column analysis | Numeric descriptive | Anomaly location | Full `analyze_dataframe` | Traced anomaly peak | Retained anomaly result | Observations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20,000 rows, mixed | 20 ms | 5 ms | 23 ms | 89 ms | 256 KiB | 30 KiB | 272 |
| 100,000 rows, mixed | 76 ms | 21 ms | 143 ms | 448 ms | 1.3 MiB | 155 KiB | 1,455 |
| 1,000,000 rows, four Numeric columns | 1.6 s | 579 ms | 2.3 s | 9.1 s | 15 MiB | 2.9 MiB | 27,767 |
| 100,000 rows, about 24,000 crossings | 34 ms | 17 ms | 1.2 s | 1.0 s | 5.0 MiB | 2.6 MiB | 24,692 |

The location cost is the scan plus one retained observation per crossing. At the high anomaly rate the retained result is about 2.6 MiB. Nothing is sampled and nothing is dropped. Full analysis of the million-row frame is larger than the location pass because the relationship pass is still in that total.

The full suite is the previous 1508 passed plus 34 anomaly tests. The only failure is `tests/test_profiler.py::test_pdf_export`, the documented legacy PDF failure. Total coverage was 98%. `anomaly.py` was 85%. The missed lines are defensive raises: malformed records, a non-numeric series handed to the locator, and attachment checks the production path does not hit. The 12 warnings come from legacy `profiler.py`.

Requirement states. REQ-J-01, REQ-J-02, and REQ-B-06 stay Not started. The delivered part is Tukey fences for a selected Numeric column. Other univariate methods, multivariate detection, and the rendered view remain. REQ-J-03 and REQ-J-04 stay Not started because no multivariate method was added. REQ-IA-10 stays Not started because the view is not rendered. REQ-G-03 and REQ-P-04 stay Not started. No row is Completed.

All 12 acceptance criteria in the implementation plan passed.

### TSK-037 — compare and drift foundation

Completed 2026-10-05. Decision: [DEC-108](DECISIONS.md#dec-108).

The question is what changed between a reference dataset and a comparison dataset. A difference is not drift, and drift is not a verdict that one dataset is worse. The two sides are analyzed independently. Compare reads those results. It does not build a second profile.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/column_label.py` | Cross-dataset label identity and source-independent retention. 318 lines, 228 statements, 1 enum, 1 frozen dataclass. |
| `src/pytics/analysis/compare.py` | Frozen comparison result and the comparison pass. 1,758 lines, 813 statements, 4 enums, 19 public frozen dataclasses. |
| `src/pytics/analysis/__init__.py` | Package docstring names the comparison layer. |
| `tests/test_compare_foundation.py` | Alignment, schema, descriptive comparison, row independence, and source purity. |
| `tests/test_compare_guards.py` | Record guards for labels, alignment, and descriptive payloads. |

Not modified: `dataset.py`, semantic inference, numeric and categorical formulas, relationship modules, anomaly analysis, target analysis, and `pytics.compare`.

Ownership. Each `DatasetAnalysis` stays the single-dataset truth. Compare copies counts and descriptive landmarks from those results. It does not rescan values to subtract two retained numbers. Column labels use a match key that keeps booleans distinct from integers. Occurrence, starting at 1 in physical order, distinguishes duplicate labels.

Order. `compare_dataframes` calls `analyze_dataframe` on each frame with no target, then `compare_dataset_analyses`. The second function does not read target, relationship, or anomaly results. A directional change is comparison minus reference.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `10dcb2b`. Nothing was committed.

| Command | Result |
| --- | --- |
| `pytest tests/test_compare_foundation.py tests/test_compare_guards.py -o addopts= -q` | 41 passed |
| Dataset, overview, variables, descriptive, semantic, anomaly, relationship, and target tests | 627 passed |
| `pytest tests -q` | 1583 passed, 1 failed |

Independent checks used the column lists, retained numeric landmarks, and observed category counts without calling the comparison collector. `1` matched `1.0` and did not match `True`. Duplicate labels matched by occurrence. Integer minima above `2**53`, including `uint64` near `2**64`, kept exact Python-int changes. A float mean difference that overflows float64 is `None`, with both means retained. Categorical shared, reference-only, and comparison-only levels matched a set partition of the fixture. Unused declared categories were absent. Reindexing a frame did not change the comparison.

On this machine, NumPy generator seed 32, after one warmup. Analysis and cross times are wall clock. Peaks are tracemalloc. The comparison frame in the mixed cases drops one column and adds another, so its analysis time is not the same shape as the reference.

| Frame | Reference analysis | Comparison analysis | Cross-comparison | Full compare | Traced cross peak | Traced full peak | Retained result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20,000 rows, mixed | 269 ms | 79 ms | 1 ms | 348 ms | 27 KiB | 4.6 MiB | 13 KiB |
| 100,000 rows, mixed | 1.81 s | 0.85 s | 1 ms | 2.65 s | 23 KiB | 22.5 MiB | 13 KiB |
| 1,000,000 rows, four Numeric columns | 8.67 s | 8.68 s | 1 ms | 17.3 s | 17 KiB | 170 MiB | 10 KiB |
| 1,000 categorical levels, 20,000 rows | 35 ms | 38 ms | 6 ms | 72 ms | 246 KiB | 4.7 MiB | 150 KiB |
| 100,000 categorical levels | 635 ms | 796 ms | 552 ms | 2.33 s | 18.7 MiB | 42 MiB | 13.0 MiB |
| About 200 columns, reordered | 1.17 s | 1.20 s | 9 ms | 2.35 s | 379 KiB | 3.3 MiB | 156 KiB |

The cross pass stays near 1 ms from 20,000 rows through one million rows. It does not rescan values. One hundred thousand category levels took about 92 times the one-thousand-level cross time. Alignment of about 200 columns took 9 ms.

The full suite is the previous 1542 passed plus 41 comparison tests. The only failure is `tests/test_profiler.py::test_pdf_export`, the documented legacy PDF failure. Total coverage was 97%. `compare.py` was 92%. `column_label.py` was 92%. The missed lines are defensive raises. The 12 warnings come from legacy `profiler.py`.

Requirement states. REQ-M-01 through REQ-M-04 stay Not started. The delivered part is alignment, schema and semantic transition, and descriptive comparison for Numeric, Categorical, and Boolean. Distribution drift, relationship drift, target drift, and the rendered Compare view remain. REQ-P-07 and REQ-T-05 stay Not started. No row is Completed.

All 11 acceptance criteria in the implementation plan passed.

### TSK-038 — distribution drift and compare consolidation

Completed 2026-10-05. Decision: [DEC-109](DECISIONS.md#dec-109).

The question is how a matched variable's distribution differs from reference to comparison, how large that difference is, and what evidence supports it. A drift record holds distances first and one test second. It has no score, severity, threshold, or significance flag.

Method matrix v0.1, derived before implementation:

| | Numeric | Categorical | Boolean |
| --- | --- | --- | --- |
| Population | Finite non-missing | Non-missing observed levels | Non-missing |
| Effects | KS distance with location; Wasserstein-1 in column units | Total variation distance; one-sided observations | True-share difference |
| Test | Two-sample KS, exact up to 10,000 on the larger side | Chi-square homogeneity, no Yates | Fisher exact |
| Diagnostics | Distinct pooled values (ties) | Cochran expected-count checkpoints | None |
| Standard mode | Yes, `O(n log n)` | Yes, `O(k log k)` | Yes, `O(1)` |

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/compare.py` | Removed. Replaced by the package below, with the same import path. |
| `src/pytics/analysis/compare/__init__.py` | Package map and re-exports. 84 lines. |
| `src/pytics/analysis/compare/values.py` | Directional count, proportion, and number records. 213 lines, 126 statements. |
| `src/pytics/analysis/compare/alignment.py` | Column identity and the aligned sequence. 222 lines, 107 statements. |
| `src/pytics/analysis/compare/schema.py` | Physical and semantic snapshots. 203 lines, 97 statements. |
| `src/pytics/analysis/compare/overview.py` | Dataset-level counts. 194 lines, 65 statements. |
| `src/pytics/analysis/compare/descriptive.py` | Missingness, typed descriptive change, and eligibility. 633 lines, 256 statements. |
| `src/pytics/analysis/compare/distribution_models.py` | Frozen drift records. 573 lines, 288 statements, 6 enums, 7 frozen dataclasses. |
| `src/pytics/analysis/compare/distribution.py` | Drift calculation and the only source read. 705 lines, 283 statements. |
| `src/pytics/analysis/compare/models.py` | Column, coverage, and dataset records with cross-checks. 548 lines, 293 statements. |
| `src/pytics/analysis/compare/collector.py` | Entry points and pass order. 205 lines, 82 statements. |
| `src/pytics/analysis/relationships/categorical_categorical.py` | Chi-square and expected-count kernels take margins and positive cells; the table functions delegate. Same arithmetic. |
| `src/pytics/analysis/relationships/models/common.py` | `MultipleTestingAdjustment` names both correction families. Docstring only. |
| `tests/test_compare_distribution_drift.py` | Statistical verification, eligibility, sources, and the effect-size-first tests. 31 tests. |
| `tests/test_compare_distribution_guards.py` | Record contracts and calculator edge states. 7 tests. |
| `tests/test_compare_foundation.py` | The analyze patch target moved to `collector`. The TSK-037 "no distribution test" check now checks that no score, severity, PSI, Jensen–Shannon, or Hellinger exists. |

Not modified: `dataset.py`, `column_label.py`, semantic inference, numeric, categorical, and Boolean descriptive formulas, relationship results, anomaly and target analysis, and `pytics.compare`.

Ownership. The descriptive layer owns eligibility. Drift reads it. Categorical and Boolean drift read retained counts. Numeric drift reads each side's finite values once, through `numeric._finite_values`, and checks the retained finite count. Without both source frames, `compare_dataset_analyses` reads no value and every eligible column is `SOURCE_VALUES_NOT_SUPPLIED`. Chi-square, expected counts, Fisher, and Benjamini–Hochberg are the relationship package's.

Verification, 2026-10-05, local `.venv`, Python 3.14, SciPy 1.18.1, NumPy 2.5.3, pandas 3.0.6. HEAD remained `a4ba3d2`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_compare_distribution_drift.py tests/test_compare_distribution_guards.py -o addopts= -q` | 38 passed |
| `pytest tests/test_compare_foundation.py tests/test_compare_guards.py -o addopts= -q` | 41 passed |
| Numeric, Categorical, and Boolean descriptive tests | 67 passed |
| Relationship and adjustment tests | 180 passed |
| Semantic tests | 422 passed |
| Anomaly tests | 34 passed |
| Target, leakage, and diagnostic tests | 97 passed |
| `pytest tests -q` | 1621 passed, 1 failed |

TSK-037 regression. The previous `compare.py` from HEAD was run beside the package over five frame pairs, 48 columns, with reordered, added, removed, duplicate, boolean-labelled, large-integer, `uint64`, categorical, Boolean, text, datetime, constant, and empty columns. Overview, alignment, schema, missingness, descriptive status, reason, payload, and the TSK-037 coverage counts were identical.

Independent checks did not call the drift calculators. KS distances matched an exact Fraction ECDF, and Wasserstein distances matched an exact Fraction integral and `scipy.stats.wasserstein_distance`. KS p-values matched `scipy.stats.ks_2samp` in both regimes and equalled a full permutation enumeration without ties. With ties they were never below it. TVD, the chi-square statistic, every expected count, and the Cochran counts matched hand-built tables. Fisher matched a hypergeometric sum. Benjamini–Hochberg matched the definitional minimum over later ranks, with ties and with original column order. Integers at `2**60` that share one float64 image, `uint64` near `2**64`, signed and unsigned samples that share no NumPy dtype, and integers beyond `2**53` against floats all kept exact distances. A distance beyond float64 was unavailable while KS stayed available. A subnormal distance of `5e-324` was kept.

Sample-size sensitivity. One million values a side shifted by 1%: KS distance 0.01, Wasserstein 10,000 units, p below `1e-30`. Three against three disjoint values: KS distance 1.0, p 0.1. Categorical and Boolean at 200,000 rows and a 1-point shift: TVD and difference 0.01, p below `1e-8`. Small Categorical and Boolean samples with large effects kept p above 0.3. No record has a significance field.

On this machine, NumPy generator seed 38, after one warmup. Times are wall clock. Peaks are tracemalloc. Retained sizes are the recursive size of the frozen result.

| Frame | Reference analysis | Comparison analysis | Descriptive cross | Drift pass | BH | Total | Cross and drift peak | Retained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20,000 rows, 4 Numeric | 115 ms | 137 ms | 0.8 ms | 159 ms | 0.16 ms | 411 ms | 3.1 MiB | 9.5 → 11.5 KiB |
| 100,000 rows, 4 Numeric | 667 ms | 627 ms | 0.7 ms | 764 ms | 0.15 ms | 2.06 s | 15.5 MiB | 9.5 → 11.6 KiB |
| 1,000,000 rows, 4 Numeric | 8.92 s | 8.89 s | 0.7 ms | 3.25 s | 0.17 ms | 21.1 s | 154.5 MiB | 9.5 → 11.4 KiB |
| 20,000 rows, mixed | 662 ms | 535 ms | 1.5 ms | 116 ms | 0.23 ms | 1.31 s | 3.1 MiB | 24.8 → 27.7 KiB |
| 100,000 rows, mixed | 3.00 s | 2.51 s | 2.0 ms | 465 ms | 0.22 ms | 5.97 s | 15.5 MiB | 24.8 → 27.8 KiB |

Per Numeric column, values a side: pooled sort 8, 40, and 742 ms at 20,000, 100,000, and one million; ECDF weights 1, 5, and 29 ms; Wasserstein 1, 3, and 32 ms. The asymptotic KS tail took 33 and 153 ms at the first two sizes and near zero at one million, where it underflowed. Its cost peaks for moderate tails, up to 1.7 s at an effective `n` of 500,000.

| Categorical | Analyses | Alignment | Partition | Drift | Chi-square | Diagnostics | BH | Drift peak | Retained drift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,000 levels, 20,000 rows | 34 / 35 ms | 0.09 ms | 4.4 ms | 3.8 ms | 1.4 ms | 0.2 ms | 0.3 ms | 0.27 MiB | 516 B |
| 100,000 levels, 200,000 rows | 1.28 / 1.44 s | 0.10 ms | 551 ms | 193 ms | 92 ms | 13 ms | 0.3 ms | 25 MiB | 600 B |

The drift record does not grow with levels. The TSK-037 partition it reads is 14.4 MiB at 100,000 levels.

The full suite is the previous 1583 passed plus 38 drift tests. The only failure is `tests/test_profiler.py::test_pdf_export`, the documented legacy PDF failure. Total coverage stayed at 97%. `distribution.py` was 95%, `distribution_models.py` 95%, `models.py` 92%, and `collector.py` 99%. Their missed lines are defensive: SciPy exceptions, non-finite library tails, counts beyond `int64`, an `object` input, and record guards that the calculators cannot reach. The 12 warnings come from legacy `profiler.py`.

Requirement states. REQ-M-01 through REQ-M-04 stay Not started. Descriptive comparison and univariate distribution drift are delivered. Relationship drift, target drift, public `compare()`, and the Compare renderer remain. REQ-P-07, REQ-P-10, and REQ-T-05 stay Not started. No row is Completed.

All 12 acceptance criteria in the implementation plan passed.

### TSK-039 — relationship drift and target drift

Completed 2026-10-05. Decision: [DEC-110](DECISIONS.md#dec-110).

The questions are whether a relationship effect changed between the reference and comparison datasets, and whether target-related structure changed. A difference of significance is not an answer to either question. There is no relationship-drift score and no target-drift score.

Method matrix v0.1, derived before implementation:

| Family | Primary change | Complementary | Formal change test |
| --- | --- | --- | --- |
| Numeric × Numeric | Signed Spearman rho | Signed Pearson r, plus absolute-magnitude change | Complementary Fisher z test of equal Pearson correlations. Not a Spearman test. Not adjusted. |
| Numeric × Categorical | Eta squared | None | None. Group vocabulary is same or changed. |
| Numeric × Boolean | Signed Hedges' g, True minus False | Signed mean difference | None |
| Boolean × Boolean | Signed phi | Probability difference only when the conditioning column is the same logical column | None |
| Categorical × Categorical | Cramér's V | None | None. Level sets and shape are diagnostics. |
| Categorical × Boolean, datetime relationships | None | None | Unimplemented |

Target drift, only when a target is requested, projects the column's distribution drift, the relationship-drift records that include the target, descriptive held-out metric changes for a comparable diagnostic task, and mechanical leakage-status transitions. Permutation importance is not compared. "Concept drift" is not a result.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/compare/relationship_models.py` | Relationship-drift records and their checks. |
| `src/pytics/analysis/compare/relationships.py` | Cross-dataset effect pass. No source read. |
| `src/pytics/analysis/compare/target_models.py` | Target-drift records. |
| `src/pytics/analysis/compare/target.py` | Projection of distribution, relationship, diagnostic, and leakage evidence. |
| `src/pytics/analysis/compare/collector.py` | Optional target request. Relationship drift always. Target drift only when requested. |
| `src/pytics/analysis/compare/models.py` | Relationship and target records on `DatasetComparison`. Relationship and target drift leave the deferred-family list. |
| `src/pytics/analysis/relationships/numeric_numeric.py` | `independent_pearson_equality`, beside the existing Fisher z interval. |
| `tests/test_compare_relationship_drift.py` | Independent family checks and the two significance fixtures. |
| `tests/test_compare_target_drift.py` | Projection, comparability, leakage transitions, and target absence. |

Not modified: legacy `pytics.compare`, semantic inference, the relationship calculators other than the Pearson equality helper, and the distribution-drift methods.

Verification, 2026-10-05, local `.venv`, Python 3.14. HEAD remained `e24536c`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_compare_relationship_drift.py tests/test_compare_target_drift.py -o addopts= -q` | 25 passed |
| `pytest tests/test_compare_foundation.py tests/test_compare_guards.py tests/test_compare_distribution_drift.py tests/test_compare_distribution_guards.py -o addopts= -q` | 79 passed |
| `pytest tests -q` | 1660 passed, 1 failed |

The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage is 97% (432 statements missed of 12,546). The new modules are `relationship_models.py` 96%, `relationships.py` 94%, `target_models.py` 94%, and `target.py` 91%. The remaining misses are defensive rejects for corrupt inputs the constructors and upstream records already make unreachable, or duplicate checks owned by `RelationshipSide`. Normal analytical paths and the meaningful result-model invariants are covered.

On this machine, after the analyses already existed. The cross-pass does not reread rows. Reversing columns does not change the pair count. Fisher z replay is arithmetic on the retained correlations.

| Frame | Reference analysis | Comparison analysis | Relationship cross-pass | Formal Fisher replay | Cross-pass peak | Retained pickle |
| --- | --- | --- | --- | --- | --- | --- |
| 80 rows, 8 numeric columns, 28 pairs | 69 ms | 67 ms | 8 ms | included | 64 KiB | 14 KiB |
| 120 rows, 25 numeric columns, 300 pairs | 574 ms | 602 ms | 70 ms | included | 549 KiB | 135 KiB |
| 80 rows, 60 numeric columns, 1,770 pairs | 3.79 s | 3.23 s | 422 ms | 188 ms on a separate 1,770-call replay | 3.2 MiB | 791 KiB |

The same 1,770 pairs took 403 ms at 20 rows and 502 ms at 200 rows. The cross-pass tracks the pair count, not the row count. A 20-column target projection over an existing comparison took 1.2 ms, peak 10 KiB, retained pickle 3.8 KiB. Building both analyses, including the diagnostic, took about 1.0 s.

Requirement states. REQ-M-01 through REQ-M-04 stay Not started. Descriptive comparison, univariate distribution drift, relationship effect changes, and an explicit-target projection are delivered. Public `compare()`, Findings, and the Compare renderer remain. REQ-P-07, REQ-P-10, and REQ-T-05 stay Not started. No row is Completed.

All 10 acceptance criteria in the implementation plan passed.

### TSK-040 — Findings Engine foundation

Completed 2026-10-05. Decision: [DEC-111](DECISIONS.md#dec-111).

The question is which already established analytical facts deserve the reader's attention. It is not which further conclusions can be drawn from them. Analysis establishes truth, findings select and structure attention, and a later renderer communicates it.

Findings Epistemic Contract v0.1, derived before implementation and recorded in DEC-111 before the first production file:

| Term | Meaning |
| --- | --- |
| Fact | A value an analysis retained. |
| Evidence | The retained facts that make one finding true. |
| Finding | A structured attention selection: code, subject, severity, evidence. |
| Severity | The policy's attention level for a code: `INFO`, `NOTABLE`, or `WARNING`, defined by the consequence for reading other results. Not significance, confidence, or effect size. |
| Priority | Severity, then code rank, then subject order. Not severity alone, and not a score. |
| Interpretation | What a reader concludes. Not produced. |
| Verdict | A judgement that something is wrong. Not produced. |
| Recommendation | An instruction to act. Not produced. |

The catalog, the deferred catalog, and the rejected candidates are in [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md#findings-v01). Implementation found one evidence semantics problem. `DETERMINISTIC_REPEATED` needs only one repeated predictor value, and exact duplicate rows give a nearly unique predictor such a value. The profile mapping finding therefore also needs no singleton predictor value. The comparison keeps only mapping statuses, so a mapping transition is deferred.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/findings/__init__.py` | Package exports and module map. Not exported from top-level `pytics`. |
| `src/pytics/analysis/findings/models.py` | Codes, scopes, severities, subjects, evidence, identity, suppression, and the code contracts. |
| `src/pytics/analysis/findings/result.py` | Policy type, coverage, and `FindingsAnalysis` with its checks. |
| `src/pytics/analysis/findings/policy.py` | The v0.1 severity and order table and result assembly. |
| `src/pytics/analysis/findings/profile.py` | Profile rules and `collect_profile_findings`. |
| `src/pytics/analysis/findings/compare.py` | Compare rules and `collect_compare_findings`. |
| `src/pytics/analysis/__init__.py` | Docstring names the findings package. |
| `tests/findings_support.py` | Exact-label frame builder and source-independence walker. |
| `tests/test_findings_models.py` | Policy, contracts, identity, ordering, suppression, coverage, invalid combinations, and the no-source, no-significance import check. |
| `tests/test_findings_profile.py` | Structural findings, root conditions, aggregation, target leakage deduplication, duplicate and adversarial labels, identity stability, determinism, and significance independence. |
| `tests/test_findings_compare.py` | One-sided columns, semantic-change roots, target task and class-set changes, exact-duplicate transitions, suppression, target absence, drift significance independence, labels, and determinism. |

Not modified: semantic inference, every analysis and comparison module, legacy `pytics.profile` and `pytics.compare`, and `pyproject.toml`.

Verification, 2026-10-05, local `.venv`, Python 3.14. HEAD remained `7d2a2ef`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_findings_models.py tests/test_findings_profile.py tests/test_findings_compare.py -q --cov-branch` | 50 passed. Every findings module has 100% statement and branch coverage. |
| `pytest tests -q` | 1710 passed, 1 failed |
| `black --check` and `mypy` on the findings package | Clean |

The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage is 97% (432 statements missed of 13,172). The missed count did not change.

On this machine, after the analysis or comparison already existed. Findings time is the fastest of seven runs after one warmup. Peak is tracemalloc during one findings pass. Retained is the pickled findings result. Each frame has an explicit Boolean target and an exact copy, about 2% duplicated rows, and one Empty or Constant column in six.

| Input | Analysis | Findings | Findings ÷ analysis | Peak | Retained | Findings | Suppressed | Codes evaluated | Relationship records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Profile, 1,000 rows, 10 columns | 0.25 s | 0.26 ms | 1.0e-3 | 6.8 KiB | 2.6 KiB | 3 | 1 | 5 | 33 |
| Profile, 20,000 rows, 30 columns | 2.79 s | 0.56 ms | 2.0e-4 | 11.7 KiB | 2.9 KiB | 6 | 1 | 5 | 295 |
| Profile, 2,000 rows, 100 columns | 8.21 s | 1.38 ms | 1.7e-4 | 30.2 KiB | 4.0 KiB | 18 | 1 | 5 | 3,198 |
| Compare, 1,000 rows, 10 columns | 0.36 s | 0.16 ms | 4.5e-4 | 4.8 KiB | 2.9 KiB | 4 | 0 | 6 | 28 |
| Compare, 2,000 rows, 100 columns | 17.21 s | 0.87 ms | 5.1e-5 | 7.5 KiB | 2.9 KiB | 4 | 0 | 6 | 3,403 |

The pass is linear in columns, predictors, and relationship records, and it does not grow with row count. The Compare pass reads relationship records only to count transitions.

Size: the package is 1,332 lines and 626 statements in six modules, with 6 enums and 13 frozen dataclasses, one of them a private contract record. `models.py` is the largest module at 621 lines. Eleven codes, two suppression rules.

Requirement states. REQ-N-01, REQ-N-02, and REQ-N-03 stay Not started: the v0.1 findings are structured, traceable, prose-free, and LLM-free, and the catalog is not the product's findings scope. REQ-N-04 stays In force and is respected. REQ-IA-06 stays Not started. REQ-P-04, REQ-P-07, REQ-P-10, REQ-M-03, REQ-L-03, and REQ-T-05 stay Not started and are respected on this path. No row is Completed.

All 10 acceptance criteria in the implementation plan passed.

### TSK-041 — Canonical column identity

Completed 2026-10-05. Decision: [DEC-112](DECISIONS.md#dec-112).

The question is which implementation owns "same column label", and why a Numeric column named float `NaN` aborted `analyze_dataframe`. It is not a new statistical method.

Before the edit, `column_label.py` already defined the match key. Compare alignment counted occurrences privately, and Findings imported that private helper and the private `_match_key`. Anomaly, relationship, and target records compared a raw label with Python `==`. `float("nan") == float("nan")` is false even for one object, so the rebuilt anomaly record did not match. On pandas 3.0.6 the relationship frame check did not raise, because a repeated Index lookup returns the same object and the old helper treated identity as a match. A distinct float `NaN` failed that helper. A freshly constructed float `NaN` did not resolve as a target.

What was changed:

| File | Role |
| --- | --- |
| `src/pytics/analysis/column_label.py` | Match key, occurrence count, observed-label equality, and record equality for column-label fields. |
| `src/pytics/analysis/compare/alignment.py` | Occurrence counting calls `identify_column_labels`. Alignment still pairs occurrences. |
| `src/pytics/analysis/compare/collector.py` | Source-frame label check uses `observed_labels_equal`. |
| `src/pytics/analysis/findings/models.py` | Subject key uses `retained_column_label_match_key`. |
| `src/pytics/analysis/findings/profile.py` | Subjects use `identify_column_labels`. No import from Compare alignment. |
| `src/pytics/analysis/anomaly.py` | Anomaly-record equality uses the match key for the label. |
| `src/pytics/analysis/relationships/collector.py` | `_labels_match` delegates to `observed_labels_equal`. |
| `src/pytics/analysis/relationships/models/*.py` | The five calculated relationship records compare labels by the match key. |
| `src/pytics/analysis/target.py` | Target resolution uses the same equivalence. Target records compare labels by the match key. |
| `src/pytics/analysis/target_leakage.py` | The type-strict check treats float `NaN` as equal to float `NaN`. |
| `src/pytics/analysis/target_diagnostic.py` | The same NaN case for labels and class values. `1` and `1.0` stay different types. |
| `tests/test_column_identity.py` | NaN Numeric analysis, relationships, target, duplicates, adversarial labels, and reorder. |

Not modified: semantic inference, statistical methods, drift, the findings catalog and policy, legacy `pytics.profile` and `pytics.compare`, and `pyproject.toml`.

Verification, 2026-10-05, local `.venv`, Python 3.14.8, pandas 3.0.6, NumPy 2.5.3. HEAD remained `ce87404`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest` on identity, anomaly, relationship, target, compare, and findings modules | 465 passed |
| `pytest tests -q` | 1717 passed, 1 failed. The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage 97% (432 missed of 13,261). `column_label.py` is 94%. The missed lines there are the pre-existing retention guards. |

Indexing, after one warmup, quiet machine. The previous `_index_columns` times on the same machine were 0.830 ms, 3.960 ms, and 4.162 ms.

| Schema | `identify_column_labels` | Alignment adapter |
| --- | --- | --- |
| 100 distinct labels | 0.621 ms | 0.701 ms |
| 500 distinct labels | 3.257 ms | 4.289 ms |
| 500 labels, two names | 3.274 ms | 4.040 ms |

Five times the columns takes about five times the identification time. The adapter stays near the previous indexer. It does not scan column values.

Requirement states. No row is advanced. `REQ-M-01` through `REQ-M-04` and `REQ-N-01` through `REQ-N-03` stay Not started. No row is Completed.

### TSK-042 — Public result contract

Completed 2026-10-05. Decision: [DEC-113](DECISIONS.md#dec-113).

The question is which object a caller should hold after analysis, and which boundary a later notebook, serializer, or integration should read. It is not a renderer.

`pytics.profile` still returns the legacy HTML renderer output. `pytics.compare` still returns the legacy comparison dictionary and can still render HTML. Both still hold rendering concerns, and `compare` still keeps the DataFrames. The canonical `DatasetAnalysis` and `DatasetComparison` already drop the DataFrame. Findings already select retained facts. Publishing those internal dataclasses unchanged would freeze collector structure as the API. Copying them would make a second analysis.

What was added:

| File | Role |
| --- | --- |
| `src/pytics/results/profile.py` | `ProfileResult`, variable and relationship indexes, target view, coverage. |
| `src/pytics/results/comparison.py` | `ComparisonResult`, aligned columns, relationship drift, target drift. |
| `src/pytics/results/common.py` | Kind, target request, metadata, findings view, ambiguous-label error. |
| `src/pytics/results/equality.py` | Label-aware content equality. Does not change internal `==`. |
| `src/pytics/results/__init__.py` | Public exports. Not added to top-level `pytics.__all__`. |
| `tests/test_public_result.py` | Construction, identity, equality, immutability, and source independence. |

Not added: notebook representation, Rich, HTML, Markdown, PDF, `to_dict`, `to_json`, plugins, Polars, Spark, MLflow, W&B, FastAPI, a CI verdict, annotations, and Python 3.15 changes. Legacy `profile` and `compare` are unchanged.

On this machine, after the analysis already existed, wrapping retained the same objects. Traced memory was started after that analysis. A 10-column profile took 0.9 ms, retained 7 KiB, and peaked at 9 KiB, against 0.29 s of analysis. A 100-column profile with 4,851 relationship records took 6.4 ms, retained 22 KiB, and peaked at 31 KiB, against 29 s. A 10-column comparison took 0.4 ms, retained 3 KiB, and peaked at 3 KiB, against 0.68 s. A 100-column comparison took 4.7 ms, retained 3 KiB, and peaked at 3 KiB, against 67 s.

Requirement states. `REQ-T-01`, `REQ-T-02`, and `REQ-P-14` are advanced and not completed. `REQ-P-07` and `REQ-IA-06` are respected and not completed. No row is Completed.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `89ee030`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_public_result.py -q` | 20 passed |
| `pytest tests -q` | 1737 passed, 1 failed. The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage 97% (432 missed of 13,908). `pytics.results` is fully covered. |

### TSK-043 — Notebook landing view

Completed 2026-10-05. Decision: [DEC-114](DECISIONS.md#dec-114).

The question is what a reader sees when a `ProfileResult` or `ComparisonResult` is displayed in a notebook. It is not a second analysis and not a dashboard.

`pytics.profile` and `pytics.compare` remain the legacy 1.1.5 renderers. The temporary 2.0 path is `profile_result` and `comparison_result`. Displaying the returned object calls `_repr_html_`, which delegates to `pytics.presentation.notebook`. The HTML is not stored on the result. `repr` and `str` stay one line.

What was added:

| File | Role |
| --- | --- |
| `src/pytics/presentation/notebook/text.py` | Escaping, counts, label display, finding prose. |
| `src/pytics/presentation/notebook/style.py` | Namespaced CSS. No external asset. |
| `src/pytics/presentation/notebook/document.py` | HTML structure shared by both landing views. |
| `src/pytics/presentation/notebook/profile.py` | Profile Observe landing view. |
| `src/pytics/presentation/notebook/comparison.py` | Compare Observe landing view. |
| `tests/test_notebook_presentation.py` | Protocol, identity, escaping, privacy, scale, and edges. |

`ProfileResult._repr_html_` and `ComparisonResult._repr_html_` are the only hooks on the public result. Nothing was added to `pytics.__all__`.

The landing view shows at most five findings, in canonical order. It counts retained semantic types, missing cells, and duplicate groups. It does not list relationship records, category labels, or anomaly values. A comparison uses Reference and Comparison, not old and new. Warning is an attention label, not a red failure state.

Visual inspection of local HTML at about 700px and 1000px changed three things: the missing-column label was shortened so it stays on one line, a zero missing share no longer adds `(0%)`, and the compare distribution section dropped a descriptive-count row that repeated the drift-record line. Long Unicode labels wrap inside the finding. A `<b>` in a label renders as text.

Not added: Investigate or Verify interaction, charts, tabs, standalone HTML, PDF, Markdown, JSON, plugins, and Python 3.15 changes. Legacy `profile` and `compare` are unchanged.

Requirement states. `REQ-P-13`, `REQ-P-14`, and `REQ-IA-17` are advanced and not completed. `REQ-IA-06` is not delivered. `REQ-P-07` is respected. No row is Completed.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `5e8def3`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_notebook_presentation.py -q -k "not wide"` | 22 passed |
| `pytest tests -q` | 1761 passed, 1 failed. The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage 97% (437 missed of 14,443). |

On this machine, rendering was measured after the analysis and the wrap already existed. A 10-column profile rendered in 0.73 ms and produced 6,151 bytes, against 0.12 s of analysis. A 100-column profile with 4,950 relationship records rendered in 0.89 ms and produced 6,161 bytes, against 8.8 s of analysis. A 10-column comparison rendered in 0.50 ms and produced 7,800 bytes, against 0.22 s of analysis. A 100-column comparison with 4,950 aligned pairs rendered in 0.46 ms and produced 7,821 bytes, against 18.2 s of analysis. After the HTML string was dropped, traced memory above the pre-render baseline was about 108 bytes. Cold imports of `pytics` and of `pytics.results` did not load `pytics.presentation`.

### TSK-044 — Core semantic inference hardening

Completed 2026-10-05. Decision: [DEC-115](DECISIONS.md#dec-115).

A clean mixed table, with three repeated object or string label columns and five numeric columns, previously resolved only the numeric columns. The three label columns were `INSUFFICIENT_EVIDENCE`, so relationships were only the ten numeric pairs. The cause was the Categorical assessor: it supported a pandas categorical dtype and had no rule for a reused string vocabulary. Resolution then abstained. The notebook renderer was not the cause.

The new rule supports Categorical only when string structure and pattern evidence describe the same column, every non-missing string is an unpunctuated letter-bearing label, at least one value is reused, and the distinct count is at most `max(12, n_non_missing // 4)`. Full-population UUID or hexadecimal syntax stays Identifier. Two letter labels stay Categorical, not Boolean. Low-cardinality numeric columns stay Numeric. Multi-word text, punctuation, pure digits, and mixed date or currency strings stay unresolved. A repeated long letter token with no separator can still be a label, because this slice does not add a Text rule.

String and object columns selected as Categorical keep frequency evidence and a first-appearance level table. `ordered` is unset. Relationship code uses `factorize` and does not replace the source dtype. The statistical methods are unchanged.

Not solved: mixed representations, category normalization, notebook information density, charts, and candidate-derived confidence. A later slice is expected for mixed representations and explainable uncertainty. Important analytical phases need a real-world acceptance check in addition to unit and statistical regression tests.

Requirement states. `REQ-S-01`, `REQ-C-01`, `REQ-C-05`, and `REQ-F-01` are advanced and not completed. `REQ-D-01` is not completed. No row is Completed.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `fe086d3`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_string_vocabulary.py tests/test_core_candidates.py -q` | Passed before the full suite. |
| `pytest tests -q` | 1786 passed, 1 failed. The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage 97% (440 missed of 14,539). |

The baseline before this slice was 1761 passed and the same PDF failure, at 97% coverage. The local acceptance fixture is a constructed 344-row table with the same physical pattern as the reported penguin extract: three repeated object labels, four continuous floats, and one low-cardinality integer. It is not a download of that dataset. Before the change that fixture had 10 calculated relationships and 18 ineligible pairs. After the change the three labels are Categorical, the integer and the floats stay Numeric, and all 28 column pairs are calculated: 10 numeric, 15 numeric-categorical, and 3 categorical-categorical. Ineligible pairs are 0. A 12-row mixed country, stage, date, revenue, and score table stays unresolved except for its numeric column: 0 calculated and 15 ineligible. The source frame is unchanged.

Column-only inference, median of three runs, before to after: the 344-row mixed table moved from 0.018 s to 0.019 s; a 10,000-row, 17-column label table moved from 1.239 s to 1.320 s; a 5,000-row, 6-column high-cardinality string table moved from 0.293 s to 0.301 s. The high-cardinality strings stayed unresolved. Full `analyze_dataframe` on the wide label table moved from 1.343 s with 0 calculated pairs to 1.595 s with 136 calculated pairs. That increase is the existing relationship calculators running on columns that are now eligible. The Colab rerun of the original extract remains for review after this slice.

### TSK-045 — Mixed representation and explainable semantic evidence

Completed 2026-10-05. Decision: [DEC-116](DECISIONS.md#dec-116).

String structure and pattern evidence were already collected for string columns that reached candidate assessment. Pattern evidence named only UUID, IP, and hexadecimal syntax. Token evidence existed and was not collected on this path. Every other shape was discarded. Resolution then used one reason, `No candidate is supported.`, for a column with no signal and for a column full of conflicting shapes.

`RepresentationEvidence` now partitions those strings. The column keeps counts and ratios, not raw values. `mixture` is `none`, `observed`, or `conflicting`. It is not a new resolution status. The unpunctuated letter-label rule is unchanged. A short-label rule can also support Categorical when every non-missing string is label-like, a value is reused, and the distinct count stays within the same vocabulary bound. Prose, at 6 or more tokens, is not that family. Date-like and currency-like strings are observed and are not converted. Missing-like literals stay literals. Email-like and URL-like strings are not Identifier. A pure digit string is numeric-like, not an Excel date.

Requirement states. `REQ-S-01`, `REQ-C-01`, and `REQ-F-01` are advanced and not completed. `REQ-S-03` is respected. `REQ-D-01` is not completed. No row is Completed.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `87fa804`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests/test_representation_evidence.py tests/test_representation_acceptance.py tests/test_string_vocabulary.py tests/test_core_candidates.py -q` | Passed before the full suite. |
| `pytest tests -q` | 1908 passed, 1 failed. The only failure is `tests/test_profiler.py::test_pdf_export`. Total coverage 97% (440 missed of 14,981). |

The baseline before this slice was 1786 passed and the same PDF failure, at 97% coverage. A constructed 344-row table with three repeated letter-label columns, four continuous numeric columns, and one low-cardinality integer stays 3 Categorical, 5 Numeric, 28 calculated relationships, and 0 ineligible. A real Palmer Penguins file was not on this machine. The 10,000 × 17 messy company CSV at `Downloads/messy-company-data-10000.csv` was read with `pandas.read_csv` and no preprocessing. Physical dtypes were unchanged. Missing cells stayed 13,387 of 170,000. The frame compared equal after analysis. Semantic counts moved from 1 Numeric and 16 unresolved to 1 Numeric, 4 Categorical, and 12 unresolved. Country, Source System, Lifecycle Stage, and Raw Company Name are Categorical. Padding on Country and Raw Company Name, and missing-like literals on Source System, stay on the evidence and stay distinct observed levels. They are not stripped and they are not semantic conflicts. Company Description and CRM Notes are prose-like and not Categorical. The three date columns stay unresolved with conflicting temporal, quarter-year, numeric-like, and label-like evidence. Annual Revenue, Lead Score, Open Opportunities, Website, and Account Owner stay unresolved because two core groups are material. Employee Count stays unresolved with one numeric core group, a missing-like modifier, and an other count. Row ID is label-like and unique, so it is observed and not Categorical. Relationships moved from 0 calculated and 136 ineligible to 10 calculated and 126 ineligible. Those pairs are the existing readers among Index and the four Categorical columns. No relationship method changed.

Column-only inference, median of three runs, before to after, on constructed frames: the 344-row mixed table's one string column moved from 0.009 s to 0.009 s; a 10,000-row, 17-column short-string table moved from 2.072 s to 2.698 s; a 5,000-row, 6-column high-cardinality string table moved from 0.416 s to 0.717 s; a 10,000-row prose column moved from 0.199 s to 0.255 s; a 10,000-row mixed-representation column moved from 0.122 s to 0.164 s. Full nalyze_dataframe on the real messy file took 3.715 s, of which column inference was 3.386 s. That file was not timed before the change.

### TSK-046 — Legacy surface, export, and dependency cleanup

Completed 2026-10-05. Decision: [DEC-117](DECISIONS.md#dec-117).

`import pytics` imported the 1.1.5 renderer, and that renderer imported Plotly, Jinja2, and xhtml2pdf. xhtml2pdf imported ReportLab. The same stack loaded for `from pytics.results import profile_result`, because the package init imported the renderer. Kaleido was used only to rasterize Plotly figures. Matplotlib was used only by the legacy `compare()` density plot. IPython was declared and was not imported by runtime code. The three Jinja templates belonged only to that renderer. There was no Markdown report exporter. The analytical engine does not call this path.

The renderer, `visualizations.py`, the templates, `profiler.py`, and the tests and root scripts that only exercised them were removed. `pytics.profile(frame, *, target=None)` returns `ProfileResult`. `pytics.compare(reference, comparison, *, target=None)` returns `ComparisonResult`. Both delegate to `profile_result` and `comparison_result`, which remain. The analysis stack loads when those functions are called. `import pytics` does not load it. [OPEN-004](DECISIONS.md#open-questions) is narrowed to the configuration object, semantic-override representation, further public parameters, and the later status of the transitional helpers. Plotly, Jinja2, xhtml2pdf, Matplotlib, and Kaleido left the runtime dependencies. IPython moved to the development extra for the notebook formatter test. SciPy and scikit-learn stay. The notebook landing view was not redesigned. No analytical threshold or statistic changed.

Requirement states. `REQ-T-01` is advanced and not completed. `REQ-P-13` and `REQ-P-14` are not completed. No row is Completed.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `d026566`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests -q` | 1894 passed. Total coverage 97% (423 missed of 14,772). |

The baseline before this slice was 1908 passed and 1 failed, at 97% coverage (440 missed of 14,981). The failed test was `tests/test_profiler.py::test_pdf_export`. That file was removed because it tested the retired renderer. The failure was not skipped. A clean virtual environment installed from this tree pulled pandas, NumPy, SciPy, and scikit-learn, and did not pull Plotly, Jinja2, xhtml2pdf, ReportLab, Kaleido, Matplotlib, or IPython. After the top-level facade correction, `import pytics` took 0.027 s and loaded 55 modules. It did not load the result package, the analysis package, pandas, SciPy, or the retired export stack. `pytics.profile` on the penguins-shaped control matched `profile_result`: 5 Numeric, 3 Categorical, 28 calculated relationships, and 0 ineligible. The same call on the real messy-company file matched `profile_result`: 1 Numeric, 4 Categorical, 12 unresolved, 10 calculated relationships, 126 ineligible, and 13,387 missing cells, with the source frame unchanged. `pytics.compare` on a two-column pair matched `comparison_result`. The notebook landing view of the object returned by `pytics.profile` still contains the profile heading.

### TSK-047 — Statistical validity hardening

Completed 2026-10-05. Decision: [DEC-118](DECISIONS.md#dec-118).

On HEAD `4f7da2a`, eta squared and classical Cramér's V were the only stored association effects for their families, and any computable Pearson chi-square tail entered its Benjamini–Hochberg family. Under independent noise those effects follow their null expectations. A seed-0 categorical pair with 1,000 rows and about 240 levels had Cramér's V about 0.49, a chi-square p-value about 0.00045, and a minimum expected count of 0.001, and that p-value was adjusted. The expected-count diagnostics were already stored. They did not decide validity.

Eta squared remains `SS_between / SS_total`. Epsilon squared is Kelley's correction of that ratio, `(SS_between - (k - 1) * MS_within) / SS_total`. A negative value is kept. It is unavailable when `N = k`. Bergsma's bias-corrected Cramér's V is stored beside classical V. A negative phi-squared adjustment is floored at zero and marked `numerator_floored`. A corrected denominator that is not positive is `BIAS_CORRECTION_UNDEFINED`, not zero. Cochran's convention is the chi-square gate: no expected count below 1, and at most 20 percent of expected counts below 5, with the share checked as `5 * n_below_5 <= n_cells`. A failing tail stays computed, is `INVALID` with reason `CHI_SQUARE_EXPECTED_COUNTS`, and has no adjusted p-value. The relationship family and the drift family stay separate. Categorical distribution drift uses the same gate. Total variation distance is unchanged. Relationship drift keeps eta squared and classical V as primary changes and copies the corrected effects beside them. Target links still reuse the dataset record, so an invalid tail does not regain an adjusted p-value there. No semantic threshold, cardinality cutoff, category collapse, exact test, or predictive-model change was made.

Requirement states. `REQ-K-02`, `REQ-K-04`, `REQ-P-10`, and `REQ-T-05` are advanced and not completed. `REQ-K-05`, `REQ-M-03`, and `REQ-P-07` are respected. No row is Completed.

Verification, 2026-10-05, local `.venv`, Python 3.14.8. HEAD remained `4f7da2a`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests -q` | 1904 passed. Total coverage 97% (503 missed of 15,136). |

The baseline before this slice was 1894 passed, at 97% coverage (423 missed of 14,772). The penguins-shaped control stayed 5 Numeric, 3 Categorical, 28 calculated relationships, and 0 ineligible. Its chi-square tails met Cochran's convention, so they stayed in the relationship family. Epsilon squared is now stored beside eta squared, including small negative values where the naive eta squared is near zero. `Downloads/messy-company-data-10000.csv` stayed 10,000 × 17, 1 Numeric, 4 Categorical, 12 unresolved, 10 calculated relationships, 126 ineligible, and 13,387 missing cells, with the source frame unchanged. Three of its categorical pairs fail Cochran's convention, keep their computed p-values, and no longer have adjusted p-values. The other three stay valid and adjusted. Naive Cramér's V on Raw Company Name × Country stayed about 0.40; the corrected companion is about 0.37. Ordinary profile and compare timings, median of three runs after one warmup, before to after: penguins-shaped profile 0.082 s to 0.087 s, a 4,000 × 7 mixed frame 0.069 s to 0.068 s, penguins-shaped compare 0.188 s to 0.189 s, and the mixed compare 0.164 s to 0.166 s.

### TSK-048 — Minimal core graceful abstention

Completed 2026-10-06. Decision: [DEC-119](DECISIONS.md#dec-119).

On HEAD `0abfb62`, one unhashable object column aborted `profile` in `collect_basic_column_evidence` because `Series.nunique` raised `TypeError`. The same cells made `pd.factorize` fail inside exact duplicate analysis when the frame had at least two rows. String-structure applicability and that duplicate failure both inspected the text of a `TypeError`.

`n_unique_non_missing` is now `None` when that distinct count cannot be hashed. `0` is still a known empty distinct count. The column stays in the result with its physical dtype and missing counts, is not Empty or Constant, and resolves as `INSUFFICIENT_EVIDENCE` with the reason `Exact distinct values are unavailable.` No candidate evidence is collected. Relationships, anomaly, target, and compare descriptive eligibility follow that existing state. Duplicate analysis sets `available` false for two or more rows with an unhashable cell. Its counts are `None`, not zero, and no duplicate-row finding is emitted. A frame with fewer than two rows stays an available empty duplicate result. A one-row list column is not treated as Constant. `AnalyticalInapplicability` is the string-structure signal. Duplicate unhashability is confirmed with `hash` after `TypeError`, not by reading the message. An unexpected `TypeError` on hashable values still propagates. The notebook count formatter prints `Unavailable` for a missing count.

Value-aware method eligibility is deferred. A physical categorical `Decimal` column beside a numeric column still raises when the relationship retainer rejects `Decimal`.

Requirement states. `REQ-I-01` and `REQ-A-04` are advanced and not completed. No semantic threshold or relationship method changed. No row is Completed.

Verification, 2026-10-06, local `.venv`, Python 3.14.8. HEAD remained `0abfb62`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests -q` | 1918 passed. Total coverage 97% (517 missed of 15,209). |

The baseline before this slice was 1905 passed, at 97% coverage. The penguins-shaped control stayed 5 Numeric, 3 Categorical, 28 calculated relationships, and 0 ineligible. `Downloads/messy-company-data-10000.csv` stayed 10,000 × 17, 1 Numeric, 4 Categorical, 12 unresolved, 10 calculated relationships, 126 ineligible, and 13,387 missing cells, with the source frame unchanged. Three categorical pairs still fail Cochran's convention, keep their computed p-values, and have no adjusted p-value. The other three stay valid and adjusted. A 344-row penguins-shaped profile completed in about 0.08 s. A 1,000-row frame with an unhashable column, which previously aborted, completed in about 0.013 s. That second figure is a completion time, not a before/after ratio.

### TSK-050 — String evidence performance hardening

Completed 2026-10-06. Decision: [DEC-121](DECISIONS.md#dec-121).

On HEAD `7a7ee5f`, string structure, pattern evidence, and representation evidence each walked every non-missing string. Equal values were classified again. Every string was also passed to `ipaddress`, including ordinary labels. A 100,000-row column of four labels took about 1.19 s. A 500,000-row column of those labels took about 6.03 s. An all-distinct 100,000-row string column took about 1.46 s.

When the retained distinct count is a known int and at most half the non-missing count, each collector now counts exact strings locally, after its existing string check, and classifies each string once. The count table is discarded. It does not order categorical levels. Otherwise the per-value walk remains. IPv4 parsing is skipped unless the string contains exactly three dots. IPv6 parsing is skipped unless it contains at least two colons. Strings that pass those checks still use `ipaddress`. The collectors stay separate. They still do not call `Series.value_counts` or `Series.nunique`. A non-string still raises the collector's existing exception, and it is not hashed first.

Requirement states. No requirement row is completed. `REQ-S-03` is respected.

Verification, 2026-10-06, local `.venv`, Python 3.14.8. HEAD remained `7a7ee5f`. Nothing was committed or staged.

| Command | Result |
| --- | --- |
| `pytest tests -q` | 1910 passed. Total coverage 97% (504 missed of 14,548). Duration 81 s. |

`analyze_series` medians, before to after: 100,000 rows and four object labels, 1.193 s to 0.128 s; 100,000 distinct object strings, 1.464 s to 0.828 s; 100,000 rows of nine mixed shapes, 1.987 s to 0.101 s; 500,000 rows and four labels, 6.025 s to 0.613 s; 100,000 rows and four pandas string labels, 1.696 s to 0.228 s. A 100,000-row constant label stayed 0.011 s to 0.012 s. A 100,000-row int64 column stayed 0.011 s to 0.012 s. A 344-row label column stayed 0.006 s to 0.002 s. The penguins-shaped control stayed 5 Numeric, 3 Categorical, 28 calculated relationships, and 0 ineligible. `Downloads/messy-company-data-10000.csv` stayed 10,000 × 17, 1 Numeric, 4 Categorical, 12 unresolved, 10 calculated relationships, 126 ineligible, and 13,387 missing cells, with the source frame unchanged. Raw Company Name paired with Country, Source System, and Lifecycle Stage still fail Cochran's convention, keep their computed p-values, and have no adjusted p-value. The other three categorical pairs stay valid and adjusted.

## Documentation record — semantic foundation consolidation

Recorded 2026-10-03, after TSK-005. Documentation only. No production file was changed. No test was changed. No dependency file was changed. No `TSK-###` was created. Nothing in this record marks a requirement Implemented.

Decisions recorded: [DEC-064](DECISIONS.md#dec-064) through [DEC-076](DECISIONS.md#dec-076). Later-update notes on earlier decisions state the relationship. [DEC-041](DECISIONS.md#dec-041)'s stage list is no longer the current pipeline description. [DEC-042](DECISIONS.md#dec-042)'s permission for an internal score, and for a future statistically justified numeric confidence, remains and is unused for Candidate Resolution v0.1.

The Strong Physical Type phase remains complete. At consolidation, TSK-001 through TSK-005 were the only completed implementation slices. The consolidated architecture covers observations, candidate assessments, resolution, material alternatives, High / Medium / Low confidence, inferred versus effective interpretation, and compute-once evidence. Heuristic semantic inference is not authorized. The next implementation slice was not selected at that point ([OPEN-037](DECISIONS.md#open-questions)). TSK-006 was approved later. TSK-007 was approved after that. TSK-008 was approved after that. TSK-009 was approved after that. TSK-010 was approved after that. TSK-011 was approved after that. TSK-012 was approved after that. TSK-013 was approved after that. TSK-014 was approved after that. TSK-015 was approved after that. TSK-016 was approved after that. TSK-017 was approved after that. TSK-018 was approved after that. TSK-019 was approved after that. TSK-020 was approved after that. TSK-021 was approved after that. TSK-022 was approved after that. TSK-023 was approved after that. TSK-024 was approved after that. TSK-025 was approved after that. TSK-026 was approved after that. TSK-027 was approved after that. See those records in the task log.

Still open, among others: [OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions), [OPEN-010](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-016](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions), [OPEN-019](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions), [OPEN-046](DECISIONS.md#open-046), [OPEN-047](DECISIONS.md#open-047), [OPEN-048](DECISIONS.md#open-048), and [OPEN-049](DECISIONS.md#open-049). TSK-014 later narrowed [OPEN-047](DECISIONS.md#open-047): resolution can abstain, and the inferred-interpretation representation of that status remained open. TSK-015 then recorded that representation. TSK-016 produces that inferred result from one Series. TSK-017 retains it on each column of a DataFrame analysis. TSK-018 counts a resolved selected type from that analysis, including a candidate-derived selection that has no interpretation. TSK-019 exposes that same selected type on a variable summary and still does not assign candidate-derived confidence. Candidate-derived confidence, material alternatives, and the public result remain open.

## Requirement register

Source files and tests stay empty on a requirement row until that requirement is implemented. A preparatory note may appear in Verification. Do not point these columns at `src/pytics/` merely because 1.1.5 happens to touch a similar topic.

| ID | Requirement | State | Task | Source files | Tests | Verification | Spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-P-01 | Serve the six purposes above for a professional audience. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-02 | Treat understanding as the goal. Do not optimize predictive performance. | Not started | TSK-034 | — | — | Respected by TSK-034. The diagnostic model is untuned, single, and compared only with a naive baseline. It carries no predictability label. | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-03 | Stay outside the non-goals listed above. | In force | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-04 | Report observations and evidence. Do not prescribe actions. | Not started | TSK-036 | — | — | Respected by TSK-036. Anomaly evidence names the method, the fences, the direction, and the physical row. It does not recommend deletion or repair. TSK-040 findings store no recommendation and no instruction to act. The requirement is broader than anomaly analysis. | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-05 | Design for professionals, without beginner clutter, and keep methods and assumptions inspectable. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-06 | Implement the core analytical API against pandas DataFrames only. Do not load files or parse CSV, Parquet, encodings, or remote paths in core. Do not add a multi-engine dataframe abstraction at this stage. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-07 | Do not produce a composite data-quality score. | Not started | TSK-037, TSK-038 | — | — | Respected by TSK-037 and TSK-038. The comparison result has no composite score, no drift score, and no severity. TSK-040 orders findings lexicographically and adds no interestingness, finding, or quality score. The requirement is broader than comparison. | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-08 | Provide statistical depth beyond a `DataFrame.describe()` wrapper. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-09 | Every chart must answer an analytical question. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-10 | Lead inferential presentation with effect size, uncertainty, and context. Do not lead with the p-value, use significance stars, or treat a tiny p-value as inherent importance. Where correction applies, distinguish raw and adjusted p-values. | Not started | TSK-024 | — | — | Not completed. TSK-024 stores the estimate before the raw p-value. TSK-026 stores eta squared before the raw ANOVA p-value. TSK-028 stores the Boolean effects before the raw Fisher p-value and does not add a Boolean confidence interval. TSK-029 stores the Numeric × Boolean mean difference, Hedges' g, and the 95% Welch interval before the raw Welch p-value. TSK-030 stores the contingency table and classical Cramér's V before the raw Pearson chi-square p-value. None of those slices adds a significance star. TSK-031 stores the Benjamini–Hochberg value beside the available primary raw p-value and still does not add a significance star. TSK-038 stores drift distances before the raw drift p-value and its comparison-level Benjamini–Hochberg value, with no significance flag. TSK-040 findings do not read a p-value, and no severity follows from significance. The rendered presentation is not delivered. | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-11 | Allow Bayesian analyses that help understanding, under the transparency rules above, without promising universal Bayesian coverage and without Bayesian predictive optimization. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-12 | Reproduce results for the same data, configuration, version, and seed where reasonably possible, and record metadata for nondeterministic methods. | Not started | TSK-034 | `src/pytics/analysis/target_diagnostic.py` | `tests/test_target_diagnostic.py` | Not completed. TSK-034 retains the diagnostic seed, validation design, estimator parameters, importance repeats, and scikit-learn version, and repeated runs are equal. The seed is not configurable ([OPEN-009](DECISIONS.md#open-questions)). | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-13 | `profile` performs analysis without dumping charts into the notebook, and a plain notebook representation stays compact. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-14 | Expose structured results programmatically, and render HTML and PDF through explicit presentation entry points. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-15 | Default to zero configuration, and avoid a large public keyword-argument surface. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-P-16 | Provide quick, standard, and deep analysis modes. Standard is the intended default. Exact contents and thresholds are not frozen. | Not started | — | — | — | — | [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) |
| REQ-S-01 | Infer a semantic type. The minimum concepts are Numeric, Categorical, Boolean/Binary, Text/String, Datetime, Timedelta, Identifier, Constant, and Empty. Empty and Constant are also dataset facts. | Not started | TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-014, TSK-015, TSK-016, TSK-044, TSK-045 | — | — | Not completed. TSK-001 can represent the minimum types. TSK-002 infers Empty and Constant only. TSK-003 also infers Boolean from a physical Boolean dtype after those two rules. TSK-004 also infers Datetime from a native or timezone-aware datetime dtype after those three rules. TSK-005 also infers Timedelta from a physical timedelta dtype after those four rules. It does not infer Timedelta from strings, numbers, objects, categoricals, or periods. It does not infer Datetime from strings or other storage, the other minimum types, other Boolean representations, duration analysis, or dataset facts. TSK-006 adds no semantic reading. TSK-007 adds no semantic reading. TSK-008 adds no semantic reading. TSK-009 adds no semantic reading. TSK-010 adds no semantic reading. TSK-011 assesses an Identifier candidate and does not select Identifier or any other reading. TSK-012 assesses Numeric, Categorical, and Text candidates and does not select any of them. TSK-013 adds token and vocabulary observations and does not select a reading. TSK-014 resolves a structural reading or exactly one supported candidate. It does not build a confidence-bearing interpretation for that candidate, and the precedence chain does not call it. TSK-015 records the inferred state for that resolution and the observed physical dtype. It keeps a structural interpretation and does not build a confidence-bearing interpretation for a candidate-derived selection. The precedence chain does not build that state. TSK-016 reaches those existing readings from one Series and does not add a reading or a public result. TSK-044 supports Categorical for a reused vocabulary of unpunctuated letter-bearing labels and still does not assign High, Medium, or Low to that selection. TSK-045 also supports Categorical for a reused short-label vocabulary and still does not assign High, Medium, or Low. Representation evidence does not select Datetime, Numeric, or Text. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-02 | Retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source of interpretation. User-facing confidence is High, Medium, or Low, with concrete evidence. Do not present pseudo-precise confidence. | Not started | TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-014, TSK-015, TSK-016 | — | — | Not completed. TSK-001 can store a reading. TSK-002 stores type, High confidence, one evidence statement, inferred source, and physical dtype for Empty and Constant only. TSK-003 does the same for physical Boolean, with source physical dtype. TSK-004 does the same for physical Datetime. Timezone-aware storage keeps its own evidence statement and its physical family. TSK-005 does the same for physical Timedelta. Its evidence statement is `physical dtype is timedelta`. TSK-014 keeps that confidence when a structural interpretation resolves, and does not assign High, Medium, or Low to a candidate-derived selection. TSK-015 keeps that same structural confidence and still does not assign High, Medium, or Low to a candidate-derived selection. TSK-016 keeps that boundary when the column pipeline produces the inferred result. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-03 | Do not silently clean, repair, coerce, or mutate the original DataFrame. Preserve the distinction between source representation and analytical interpretation. Pattern detection must not rewrite the source Series. | Not started | TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-013, TSK-016, TSK-017 | — | — | Not completed. TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, and TSK-010 do not mutate the Series they read. TSK-002, TSK-006, and TSK-007 do not treat missing-like strings as missing. TSK-004 does not parse strings or coerce them to datetime. TSK-005 does not parse strings or coerce them to timedelta. TSK-008 does not parse numeric strings or coerce them with `pd.to_numeric`. TSK-009 does not stringify, strip, or Unicode-normalize strings, and it does not decode byte strings. TSK-010 does not strip, case-fold, Unicode-normalize, stringify, or decode strings before a full-value pattern match. TSK-013 does not strip, case-fold, Unicode-normalize, or decode strings before counting alphanumeric runs. TSK-016 does not mutate, coerce, normalize, or clean the Series it reads. TSK-017 does not mutate the DataFrame or its Series, and it does not coerce a non-DataFrame into a DataFrame. TSK-045 does not strip, case-fold, or parse source strings. A missing-like literal is not added to the pandas missing count. A date-like or currency-like string is not converted. The requirement covers the product, not only these paths. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-04 | Make inference evidence-driven and transparent, and expose uncertainty. A column name may support an inference and must not determine semantic type by itself. | Not started | TSK-002, TSK-003, TSK-004, TSK-005, TSK-014, TSK-015, TSK-016, TSK-017 | — | — | Not completed. TSK-002 decides Empty and Constant from basic counts and does not use the column name. TSK-003 decides physical Boolean from the dtype family after those counts, and does not use the column name or cardinality. TSK-004 decides physical Datetime from the dtype family after those rules, and does not use the column name or parse values. TSK-005 decides physical Timedelta from the dtype family after those rules, and does not use the column name, parse values, or guess units. TSK-006 does not add a reading. TSK-007 records frequency observations and does not add a reading. TSK-008 records numeric-structure observations and does not add a reading. TSK-009 records string-structure observations and does not add a reading. TSK-010 records pattern observations and does not add a reading. TSK-011 assesses an Identifier candidate from observations already collected. It does not resolve a reading, assign High, Medium, or Low, or use the column name. It does not implement the rest of evidence-driven inference. TSK-012 assesses Numeric, Categorical, and Text candidates from observations already collected. It does not resolve a reading, assign High, Medium, or Low, invent a cardinality or length threshold, or use the column name. TSK-013 records token and vocabulary observations and does not invent a token-count, vocabulary, or length threshold, and does not use the column name. TSK-014 resolves assessments already produced. It does not invent a threshold, assign High, Medium, or Low to a candidate-derived selection, or use a column name. TSK-015 records abstention and ambiguity as inferred states and does not invent confidence from candidate counts or evidence quantity. TSK-016 orchestrates those stages for one Series and does not use the column name or invent that confidence. TSK-017 keeps column labels out of semantic evidence. TSK-045 keeps column names and Series names out of representation evidence and out of the short-label rule. Mixture is retained evidence. It is not High, Medium, or Low confidence. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-05 | Distinguish physical dtype, observed characteristics, and semantic interpretation. Keep the original physical dtype inspectable. | Not started | TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017 | — | — | Not completed. TSK-001 classifies physical dtype. TSK-002 collects four exact basic counts and keeps that physical dtype on Empty and Constant interpretations. TSK-003 keeps it on physical Boolean interpretations. TSK-004 keeps it on physical Datetime interpretations, including the timezone-aware family. TSK-005 keeps it on physical Timedelta interpretations and does not add duration-unit metadata. TSK-006 keeps those four counts as stored primary observations and adds derived ratios and boolean facts computed from them. TSK-007 adds exact frequency observations composed with those counts. TSK-008 adds exact numeric-structure observations for physical integer and floating columns, composed with those counts. TSK-009 adds exact string-structure observations for physical string columns and for eligible object columns, composed with those counts. TSK-010 adds exact full-value pattern observations composed with that string-structure evidence. TSK-011 adds an Identifier candidate assessment that consumes those observations and does not select a reading. It does not collect the rest of the observed characteristics. TSK-012 adds Numeric, Categorical, and Text candidate assessments that consume those observations and do not select a reading. TSK-013 adds exact string-content observations composed with string-structure evidence and does not select a reading. TSK-014 keeps resolution distinct from those observations and from a confidence-bearing interpretation. TSK-015 keeps the supplied physical dtype on the inferred result and does not derive it from the semantic type. TSK-016 classifies that physical dtype once and keeps the same object on the inferred result. TSK-017 keeps that physical dtype, the evidence collected for it, and the inferred result on one column analysis, and it does not store the Series. TSK-045 adds representation counts on that same column analysis for a string population that reaches candidate assessment. The counts are not a semantic type. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-06 | Treat explicit per-variable semantic configuration as a first-class capability. User intent normally takes precedence. If a configured interpretation cannot be meaningfully applied, report the conflict instead of silently coercing. The exact API is not frozen. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-07 | Give Timedelta dedicated duration analysis that preserves duration semantics and readable units. Do not present user-facing timedelta results as raw nanoseconds. | Not started | TSK-005 | — | — | Not completed. TSK-005 can read a physical timedelta dtype as Timedelta. It does not analyze durations, choose display units, or present statistics. The requirement covers duration analysis, not only this reading. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-08 | Do not infer ordinal ordering from category labels. Accept ordinal semantics only when the user configures them or the source explicitly represents order. | Not started | TSK-012 | — | — | Not completed. TSK-012 does not infer order from labels. An ordered pandas categorical dtype can support a Categorical candidate and keeps `categorical_ordered` on the physical dtype. No Ordinal type was added. Ordinal storage stays open. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-S-09 | Let semantic interpretation guide which analyses are meaningful. The specification examples are direction, not a closed eligibility matrix. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-01 | Rows, columns, cells, and dataset dimensions. | Not started | TSK-017, TSK-018 | — | — | Not completed. TSK-017 stores `n_rows`, `n_columns`, and `n_cells` on an internal dataset analysis. TSK-018 copies those three counts onto an internal dataset overview. Dataset dimensions beyond those three counts remain open. The overview is not a rendered report. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-02 | Memory usage and memory per row. | Not started | — | — | — | Not completed. TSK-017 and TSK-018 do not record memory usage. Shallow versus deep, pandas-reported versus estimated, and whether the index is included are not decided. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-03 | Missingness, complete rows, and incomplete rows. | Not started | TSK-017, TSK-018, TSK-022 | — | — | Not completed. TSK-017 derives missing-cell, non-missing-cell, and missing-ratio facts from retained basic evidence. TSK-018 copies those counts and defines cell completeness as the non-missing share of cells, undefined when there are no cells. TSK-022 reports complete rows, incomplete rows, and exact missingness patterns on the Missing summary. The overview still does not report complete or incomplete rows. Co-missingness coefficients are not reported. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-04 | Duplicate rows and unique rows. | Not started | TSK-023 | — | — | Not completed. TSK-023 exposes `n_unique_rows` and `n_excess_duplicate_rows` on an internal overview and on the duplicate summary. The rendered Overview is not delivered. Identifier duplicates and partial duplicates are not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-05 | Physical dtype composition and semantic type composition. | Not started | TSK-018 | — | — | Not completed. TSK-018 counts resolved selected semantic types, including candidate-derived selections that have no confidence-bearing interpretation. Insufficient evidence and ambiguity are separate column states, not semantic types. Physical dtype composition is not aggregated. The counts are not rendered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-06 | Constant columns, near-constant columns, empty columns, identifier candidates, and high-cardinality columns. | Not started | TSK-018 | — | — | Not completed. TSK-018 groups columns whose selected semantic type is Empty, Constant, or Identifier, and keeps position plus the original label. Near-constant columns and high-cardinality columns are not classified. No threshold was added. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-07 | Infinities. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-A-08 | Relevant computational-analysis metadata. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-01 | Count, missing, distinct, zeros, negatives, infinities, min, max, range, and sum. | Not started | TSK-019, TSK-020 | — | — | Not completed. TSK-019 exposes count, missing, and distinct on every variable, and zeros, negatives, and infinities on a Numeric detail copied from retained numeric-structure evidence. TSK-020 adds minimum, maximum, and range for a selected Numeric column. TSK-025 keeps an exact integer range and leaves a non-finite float range undefined. Sum is not implemented. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-02 | Mean, median, mode where meaningful, variance, standard deviation, IQR, MAD, coefficient of variation, and quantiles or percentiles. | Not started | TSK-020 | — | — | Not completed. TSK-020 adds mean, median, sample standard deviation, Q1, Q3, and interquartile range for a selected Numeric column. TSK-025 leaves a mean, sample standard deviation, or interquartile range undefined when it is not a finite supported number. `None` is not zero. Mode, a stored variance, MAD, and coefficient of variation are not implemented. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-03 | Skewness and kurtosis. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-04 | Robust statistics. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-05 | Distribution analysis, and normality or other distribution diagnostics where responsible. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-B-06 | Univariate outlier signals. | Not started | TSK-036 | — | — | Not completed. TSK-036 delivers Tukey inner fences for a selected Numeric column, reusing the retained quartiles. Other univariate methods are not implemented. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-01 | Count, missing, distinct, and cardinality ratio. | Not started | TSK-019, TSK-044, TSK-045 | — | — | Not completed. TSK-019 exposes count, missing, distinct, and `unique_ratio_non_missing` on every variable, including a Categorical one. The ratio uses the non-missing denominator. The rendered categorical analysis is not delivered. TSK-044 also selects Categorical for a reused unpunctuated letter-bearing vocabulary. TSK-045 also selects Categorical for a reused short-label vocabulary, including ordinary spaces and a small punctuation set. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-02 | Mode, mode frequency, top categories, rare categories, and bottom categories where useful. | Not started | TSK-019, TSK-033 | — | — | Not completed. TSK-019 exposes the most frequent count and its ratio for a Categorical variable. TSK-033 retains every observed level and every value that ties for the largest or smallest count. A separate top, rare, or bottom category view is not added. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-03 | Entropy, normalized entropy, and concentration. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-04 | Singleton categories and rare-category percentage. | Not started | TSK-019, TSK-033 | — | — | Not completed. TSK-019 exposes singleton count and singleton ratio for a Categorical variable. TSK-033 derives the singleton count from the observed level table. Rare-category percentage is not defined. The threshold remains open. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-05 | Frequency distribution. | Not started | TSK-033, TSK-044 | — | — | Not completed. TSK-033 retains the exact observed non-missing distribution for a selected Categorical column. TSK-044 retains that distribution for a string or object column selected as Categorical, in first-appearance order, with `ordered` unset. Entropy and concentration are not delivered. The rendered categorical analysis is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-06 | Low, medium, and high cardinality characteristics. Thresholds should ultimately be configurable. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-C-07 | Do not produce meaningless charts of thousands of categories. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-01 | Support conservative inference of binary-like values where the evidence justifies it. Examples may include true/false, and possibly 0/1 or yes/no. | Not started | TSK-003 | — | — | Not completed. TSK-003 interprets a non-empty, non-constant physical pandas Boolean dtype as Boolean. It does not infer Boolean from true/false strings, `{0, 1}`, or yes/no. TSK-021 counts true and false values only after Boolean is already selected. It does not infer those other representations. TSK-044 reads repeated yes/no and true/false strings as Categorical, not Boolean. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-02 | Do not treat binary cardinality as Boolean meaning. Do not treat every {0, 1} column as Boolean. Keep arbitrary two-category variables categorical. | Not started | TSK-003 | — | — | Not completed. TSK-003 does not treat two distinct values, `{0, 1}`, Boolean-like strings, or categorical booleans as Boolean. TSK-012 does not treat `{0, 1}` numeric storage as Boolean. It may support a Numeric candidate for that storage. It does not yet support two string labels as Categorical, because no vocabulary rule is approved. TSK-013 records token evidence and still does not approve that rule. The requirement covers the product, not only this path. TSK-021 describes only a selected Boolean column. `{0, 1}`, `{0.0, 1.0}`, two-label strings, and categorical boolean values do not receive Boolean counts. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-D-03 | Record confidence and reason for a boolean or binary inference. | Not started | TSK-003 | — | — | Not completed. TSK-003 records High confidence and one factual evidence statement for a physical Boolean reading. It does not cover other boolean or binary readings. TSK-021 does not add a confidence statement. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-01 | Earliest, latest, range or span, missingness, distinct values, duplicate timestamps, timezone, and inferred resolution. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-02 | Monotonicity, gaps, irregular intervals, frequency, relevant calendar distributions, and time-structure signals. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-03 | Distinguish a column that contains dates from an actual time-series structure. | Not started | TSK-004 | — | — | Not completed. TSK-004 can read a physical datetime dtype as Datetime and does not treat that reading as a time series. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-E-04 | Do not indiscriminately run deeper time-series diagnostics on every datetime column. | Not started | TSK-004 | — | — | Not completed. TSK-004 does not run monotonicity, frequency, gap, calendar, trend, seasonality, or autocorrelation analysis. The requirement covers the product, not only this path. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-01 | Distinguish the string roles listed above. | Not started | TSK-012, TSK-013, TSK-044, TSK-045 | — | — | Not completed. TSK-012 does not support a Text candidate from current observations, and it does not support Categorical for ordinary strings. TSK-013 adds token and vocabulary observations and still does not support either candidate for ordinary strings. TSK-044 distinguishes a reused unpunctuated letter-bearing vocabulary as Categorical. TSK-045 also distinguishes short labels from prose-like strings and records email-like and URL-like shapes as representation evidence. Text is still not selected. Email-like and URL-like shapes are not semantic types. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-02 | Text diagnostics covering count, missing, distinct, empty strings, whitespace-only values, length statistics and distribution, word counts, leading or trailing whitespace, line breaks, Unicode or non-ASCII characteristics, pattern consistency, and duplicate text. | Not started | — | — | — | Not completed. TSK-009 records empty-string counts, whitespace counts, character-class counts, and minimum and maximum length. TSK-010 records full-value UUID, IPv4, IPv6, and fixed-width hexadecimal counts. Neither records a length distribution, word counts, leading or trailing whitespace as a separate fact, line-break diagnostics, pattern consistency, or duplicate text. TSK-012 does not add those diagnostics and does not treat the current string facts as a Text candidate. TSK-013 records alphanumeric token counts, total character count, and aggregate token-vocabulary counts. It does not record a length distribution, leading or trailing whitespace as a separate fact, line breaks, downstream common-token diagnostics, or a Text candidate. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-F-03 | Pytics core must not become a full NLP platform. | In force | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-01 | Treat Identifier as a first-class semantic concept. | Not started | TSK-019 | — | — | Not completed. TSK-011 can record an Identifier candidate. It does not select Identifier. TSK-019 exposes a resolved Identifier variable and copies its pattern counts. Exclusion from later multivariate analysis is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-02 | Expose the evidence and reasoning for identifier detection. | Not started | TSK-019 | — | — | Not completed. TSK-011 preserves a concrete syntax statement when an Identifier candidate is supported. TSK-019 copies the structured pattern counts onto an Identifier variable. It does not copy those statements, and it does not assign confidence. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-G-03 | Normally exclude identifiers from ordinary correlation, diagnostic target modeling, and ordinary multivariate anomaly modeling, unless explicitly configured otherwise. | Not started | TSK-024, TSK-032, TSK-034, TSK-036 | — | — | Not completed. TSK-024 excludes a selected Identifier from Numeric × Numeric pairs. TSK-029 does not group by or compare a selected Identifier either. TSK-030 does not put a selected Identifier in a categorical pair. TSK-032 treats an Identifier target as ineligible. TSK-034 excludes a selected Identifier from the diagnostic model, with no configuration to include it. An integer row-number column that resolves as Numeric is not an Identifier and is not excluded. Anomaly modeling is not delivered as a multivariate method. TSK-036 excludes a selected Identifier from univariate numeric fences, with no configuration to include it. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-01 | Report dataset-level, variable-level, and row-level missingness. | Not started | TSK-022 | — | — | Not completed. TSK-022 exposes dataset cell facts, one column missingness record per physical column, and the row missingness distribution on an internal Missing summary. Variable rows already expose a missing count. The rendered Missing view is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-02 | Report missingness patterns and co-missingness. | Not started | TSK-022 | — | — | Not completed. TSK-022 retains exact recurring patterns of physical column positions, including the complete-row pattern. Pairwise co-missingness coefficients, conditional matrices, and clustering are not delivered. The pattern aggregates can support a later co-missingness count. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-03 | Report relationships between missingness and other variables. | Not started | — | — | — | — | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-04 | Report missing-like literals such as `""`, whitespace, `"N/A"`, `"null"`, and `"?"`. Do not silently rewrite them as missing data. | Not started | TSK-022 | — | — | Not completed. TSK-009 keeps those literals as ordinary strings and can count an empty string or a whitespace-only string as structure. TSK-022 also leaves them observed under pandas missingness. It does not report a missing-like literal diagnostic and does not define the literal list. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-H-05 | Keep MCAR, MAR, and MNAR diagnostics methodologically conservative. Do not claim that missingness is definitively MAR or MNAR when the observed data cannot support that conclusion. | Not started | TSK-022 | — | — | Not completed. TSK-022 records observed missingness structure and does not classify MCAR, MAR, or MNAR. It does not add Little's MCAR test or a mechanism finding. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-01 | Report exact duplicate rows and duplicate groups. | Not started | TSK-023 | — | — | Not completed. TSK-023 retains exact duplicate groups and the row counts on an internal summary. The rendered Duplicates view is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-02 | Report duplicate identifiers. | Not started | — | — | — | Not completed. TSK-023 does not report duplicate identifiers. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-03 | Report conflicting duplicates. | Not started | — | — | — | Not completed. TSK-023 does not report conflicting duplicates. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-04 | Support controlled partial-duplicate analysis. | Not started | — | — | — | Not completed. TSK-023 does not compare row subsets. "Controlled" remains unset. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-05 | Do not run uncontrolled combinatorial searches over all possible column combinations. | In force | TSK-023 | — | — | Respected. TSK-023 compares full rows only. It does not search column combinations. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-I-06 | Fuzzy or near-duplicate analysis is not a default core operation. | In force | TSK-023 | — | — | Respected. TSK-023 does not normalize or score near-duplicates. The deferred capability remains open. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-01 | Treat outliers and anomalies as observations to understand, not as errors to delete, and do not automatically recommend deletion. | Not started | TSK-036 | — | — | Not completed. TSK-036 keeps Tukey evidence as observations: value, direction, fence, and physical row. It does not delete, repair, or assign severity. Multivariate analysis and a rendered treatment remain. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-02 | Support robust univariate outlier analysis. | Not started | TSK-036 | — | — | Not completed. TSK-036 delivers Tukey inner fences for a selected Numeric column. MAD, z-score, and other univariate families are not implemented. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-03 | Support multivariate anomaly detection. | Not started | TSK-036 | — | — | Not delivered. TSK-036 considered IsolationForest and did not implement a multivariate method. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-J-04 | Multivariate anomaly analysis should eventually provide explainability or context where possible. | Not started | TSK-036 | — | — | Not delivered. The univariate record keeps the row, value, direction, and fence. Multivariate explainability was not designed because no multivariate method was selected. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-01 | Relationship analysis must be type-aware. | Not started | TSK-024 | — | — | Not completed. TSK-024, TSK-026, TSK-028, TSK-029, and TSK-030 use the selected semantic type. Numeric × Numeric, Numeric × Categorical, Boolean × Boolean, Numeric × Boolean, and Categorical × Categorical are calculated. Boolean is not treated as Categorical. Integer `{0, 1}` is not treated as Boolean; it takes the Numeric role in Numeric × Boolean. TSK-031 classifies Categorical × Boolean as unimplemented rather than ineligible, and does not calculate it. Datetime directions stay unimplemented. Other selected pairs are not treated as those families. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-02 | The capability categories listed above are in scope, under `REQ-P-10` and `REQ-P-11`. | Not started | TSK-024 | — | — | Not completed. TSK-024 adds Spearman, Pearson, a Pearson interval, and raw p-values for Numeric × Numeric. TSK-026 adds eta squared and a raw one-way ANOVA p-value for Numeric × Categorical. TSK-028 adds a probability difference, a probability ratio, phi, and a raw Fisher exact p-value for Boolean × Boolean. TSK-029 adds a mean difference, Hedges' g, a 95% Welch–Satterthwaite interval, and a raw Welch p-value for Numeric × Boolean. TSK-030 adds classical Cramér's V, expected-count diagnostics, and a raw uncorrected Pearson chi-square p-value for Categorical × Categorical. TSK-031 adds Benjamini–Hochberg adjustment of the available primary p-value for each calculated pair. Pearson correlation stays raw. Robust and rank-based alternatives, exact categorical tests, and the other categories are not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-03 | Do not hard-code a final method catalog before that catalog is decided. | In force | TSK-024 | — | — | Respected. TSK-026 does not close the catalog. TSK-028 does not close it either. TSK-029 does not close it either. TSK-030 does not close it either. TSK-031 does not close it either. Odds ratios, Boolean confidence intervals, bias-corrected Cramér's V, exact categorical tests, datetime relationships, Categorical × Boolean, and robust or rank-based Numeric × Boolean complements remain open. Five calculated families do not complete the catalog. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-04 | Separate a relationship into description, effect, uncertainty, frequentist inference, Bayesian inference where appropriate, diagnostics, and method metadata. Do not reduce a relationship to a p-value. | Not started | TSK-024 | — | — | Not completed. TSK-024 keeps the estimate, the interval, and the raw test as separate components for Numeric × Numeric. TSK-026 keeps group description, eta squared, and the raw ANOVA p-value separate. TSK-028 keeps the 2×2 table, the conditional probabilities, the directional effects, phi, and the raw Fisher p-value separate. A Boolean confidence interval is not delivered. TSK-029 keeps group description, the mean difference, Hedges' g, the Welch interval, and the raw Welch p-value separate, each with its own availability. TSK-030 keeps the contingency table, Cramér's V, the expected-count diagnostics, and the raw chi-square p-value separate. TSK-031 keeps the adjusted p-value on that same frequentist component and does not replace the effect. Bayesian inference and the rendered view are not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-K-05 | Treat statistical assumptions as diagnostic context. Do not invalidate a method solely because an assumption test is significant. Keep method selection explainable. | Not started | TSK-024 | — | — | Respected and not completed. TSK-024 does not run a normality test and does not use one to choose Pearson or Spearman. TSK-026 does not run Levene or Shapiro and does not use one to choose ANOVA. TSK-028 does not switch between chi-square and Fisher using an expected-count rule. TSK-029 does not run Shapiro or Levene and does not switch from Welch to a rank test. TSK-030 does not switch from Pearson chi-square to Fisher when an expected count is small. TSK-031 does not remove a sparse chi-square p-value from correction because an expected count is small. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-01 | Where a target is supplied, recognize target semantics and problem type where possible. | Not started | TSK-032, TSK-033, TSK-034 | `src/pytics/analysis/target_diagnostic.py` | `tests/test_target_diagnostic.py` | Not completed. TSK-032 retains the selected semantic type, resolution status, and structural confidence for an explicit target. TSK-033 does not assign classification or regression either. Numeric `{0, 1}` stays Numeric. TSK-034 assigns a predictive task to the diagnostic model only, separate from the semantic type: Boolean binary, Categorical binary or multiclass, Numeric regression, including `{0, 1}`. Other problem types remain [OPEN-023](DECISIONS.md#open-questions). | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-02 | Target analysis may cover distribution, imbalance, feature-target relationships, effect sizes, and inference. | Not started | TSK-032, TSK-033 | — | — | Not completed. TSK-032 retains the target's own missingness and reuses Numeric and Boolean descriptive facts. TSK-033 reuses the exact observed Categorical distribution and derives Boolean class structure from the existing true and false counts. Relationship effects and tests are the retained records. An imbalance verdict is not added. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-03 | Surface potential target leakage as evidence or signals. Do not assert leakage without a sufficient basis. | Not started | TSK-034, TSK-035 | `src/pytics/analysis/target_leakage.py` | `tests/test_target_leakage.py` | Not completed. TSK-035 retains exact-duplicate evidence and repeated deterministic mappings for Boolean and Categorical targets ([DEC-106](DECISIONS.md#dec-106)). A unique Identifier is not promoted. No column is asserted to be leakage. Contextual leakage, temporal leakage, near-deterministic rules, numeric transforms, and missingness-indicator rules are not delivered. TSK-040 surfaces exact-duplicate evidence and complete repeated mappings as findings named evidence, not leakage. The rendered surface is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-04 | Pytics may fit one lightweight, untuned diagnostic model to expose multivariate feature-target relationships. The model is for understanding data architecture, not for predictive optimization. | Implemented | TSK-034 | `src/pytics/analysis/target_diagnostic.py`, `src/pytics/analysis/target_diagnostic_fit.py` | `tests/test_target_diagnostic.py` | Implemented by TSK-034 for Numeric, Boolean, and Categorical targets: one untuned logistic or ridge model compared with a prior or mean baseline, with held-out multivariate signal and per-input importance ([DEC-105](DECISIONS.md#dec-105)). The requirement permits the model and bounds it. It does not require a rendered view, which belongs to REQ-IA-12. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-05 | Validate the diagnostic model with responsible holdout or cross-validation. Do not evaluate it only on the observations used to fit it. | Implemented | TSK-034 | `src/pytics/analysis/target_diagnostic_fit.py` | `tests/test_target_diagnostic.py` | Implemented by TSK-034: one 25% holdout, stratified per class for classification, with every learned preprocessing step fitted on training rows only, and importance computed on validation rows only. No in-sample metric is stored. Held-out metric uncertainty is not part of this requirement and is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-06 | Do not add hyperparameter search, model leaderboards, model competitions, automated tuning, or deployment workflows. | In force | TSK-032, TSK-034 | — | — | Respected. TSK-032 adds none of those workflows. TSK-034 fits one fixed estimator per task with fixed parameters and retains no fitted estimator. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-L-07 | Use held-out permutation importance as the primary feature-importance direction. Report spread across permutations where applicable. Warn that correlated predictors can share or obscure that importance. Do not present it as causal importance. The estimator family is not chosen. | Not started | TSK-034 | `src/pytics/analysis/target_diagnostic_fit.py` | `tests/test_target_diagnostic.py` | Not completed. TSK-034 computes held-out permutation importance of original input columns with five repeats and keeps every repeat, so the spread is available. Negative values are kept. The correlated-predictor warning and the non-causal reading are in the contract and the result docstrings. No rendered warning exists. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-01 | `compare()` is a first-class capability and uses the same product language as profile. | Not started | TSK-037, TSK-038 | — | — | Not completed. TSK-037 adds an internal comparison result. TSK-038 adds univariate distribution drift to it. TSK-039 adds relationship effect changes and, when requested, a target projection. Public `compare()` is still the legacy function, and the rendered product language is not delivered. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-02 | Explain what changed. Do not merely place two profile reports side by side. | Not started | TSK-037, TSK-038 | — | — | Not completed. TSK-037 records directional schema and descriptive change from two analyses. TSK-038 adds distribution distances and tests. TSK-039 adds relationship effect changes and a target projection. It is not a rendered explanation, and it does not yet cover every change type. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-03 | Report drift neutrally as observed or material change. Do not automatically label it bad. | Not started | TSK-037, TSK-038 | — | — | Not completed. TSK-037 records observed difference and assigns no degradation label. TSK-038 adds univariate drift methods with no degradation label, score, or severity. No material-change rule exists. Relationship effect changes and an explicit-target projection are delivered without a degradation label. TSK-040 Compare findings name change by side and add no degradation label or drift finding. Public comparison and the remaining change types are not. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-M-04 | The change types listed above are the destination scope of comparison. | Not started | TSK-037, TSK-038 | — | — | Not completed. TSK-037 delivers schema, semantic, missing-count, duplicate-count, and Numeric, Categorical, and Boolean descriptive change. TSK-038 delivers numeric and categorical distribution change for Numeric, Categorical, and Boolean columns. TSK-039 delivers relationship effect changes for the five calculated families and a target projection. Public `compare()` and the rendered Compare view remain. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-01 | Findings are structured objects traceable to metric, value, threshold where relevant, method, variables, and source analysis. | Not started | TSK-040 | — | — | Not completed. TSK-040 findings carry a code, a scope, a typed subject with physical positions and retained labels, and typed evidence that is the canonical record by reference or an exact count snapshot. Each code names its source analysis. No v0.1 rule uses a threshold. The v0.1 catalog is not the product's findings scope. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-02 | Rendered finding text presents the structured finding. It is not the source of the finding. | Not started | TSK-040 | — | — | Not completed. TSK-040 findings have no prose field, and identity does not depend on text. No rendered text exists. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-03 | Core findings must be producible without an LLM. | Not started | TSK-040 | — | — | Not completed. TSK-040 rules are deterministic functions of retained results, with no LLM, service, sampling, or randomness. The catalog is not complete. | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-N-04 | Do not use gamified or sensational finding labels. | In force | TSK-040 | — | — | Respected. TSK-040 codes name conditions neutrally and name reference and comparison sides rather than added, removed, or degraded. User-facing labels remain [OPEN-025](DECISIONS.md#open-questions). | [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) |
| REQ-IA-01 | Use a persistent left sidebar on desktop, as navigation only. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-02 | Profile navigation follows the structure above, omitting items that do not apply. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-03 | Compare navigation follows the structure above, omitting items that do not apply. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-04 | Profile and Compare should feel like two modes of the same product. | Not started | — | — | — | — | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-05 | Overview answers those four questions and does not show a composite quality score. | Not started | TSK-018, TSK-023 | — | — | Not completed. TSK-018 provides an internal analytical overview of size, cell completeness, resolved semantic types, semantic-resolution coverage, and Empty, Constant, Identifier, and unresolved column identity. TSK-023 adds unique-row and excess-duplicate counts to that overview. It does not render the Overview view, name the dataset, list duplicate groups, or add a composite quality score. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-06 | The Findings view links each finding back to its evidence. | Not started | TSK-040 | — | — | Not completed. TSK-040 subjects keep the positions, labels, and scope a view needs to link a finding to its evidence. No Findings view is rendered. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-07 | Variables begin as a searchable, sortable table, with type-aware detail under progressive disclosure. | Not started | TSK-019, TSK-021 | — | — | Not completed. TSK-019 provides ordered analytical variable rows and type-specific detail for Numeric, Categorical, and Identifier. TSK-021 adds Boolean true and false counts to that detail. It does not render a searchable or sortable table. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-08 | Missing is its own view for the missing-data contract. | Not started | TSK-022 | — | — | Not completed. TSK-022 provides an internal Missing summary, separate from the dataset overview and the variables summary. It does not render the Missing view. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-09 | Duplicates is its own view for the duplicate contract. | Not started | TSK-023 | — | — | Not completed. TSK-023 provides an internal duplicate summary, separate from the dataset overview and the variables summary. It does not render the Duplicates view. Identifier, partial, and conflicting duplicates are not delivered. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-10 | Anomalies keeps univariate and multivariate perspectives separate. | Not started | TSK-036 | — | — | Not completed. The internal anomaly result contains only the univariate numeric family. There is no multivariate result to mix with it. The rendered Anomalies view is not delivered. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-11 | Relationships are explored primarily as a table, with detail for statistics, uncertainty, inference, visualization, and methods as appropriate. A matrix is an additional view, not a replacement for the table. | Not started | TSK-024 | — | — | Not completed. TSK-024 provides an internal relationship summary. TSK-026, TSK-027, TSK-028, TSK-029, and TSK-030 keep that summary able to hold the implemented families without one dataset-level method. A Categorical × Categorical record carries the table, V, the expected-count diagnostics, and the raw chi-square result a later view needs without recomputation. It does not render the Relationships view, a matrix, or a chart. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
| REQ-IA-12 | Show Target only when target analysis exists. | Not started | TSK-032 | — | — | Not completed. TSK-032 leaves `target_analysis` as `None` when no target was requested, and the summary is absent in that case. The Target view is not rendered. | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) |
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
| REQ-T-03 | The method-registry concept is accepted. Do not implement the registry until its schema and API are decided. | In force | TSK-024 | — | — | Respected. TSK-024 does not add a method registry. Methods are explicit fields on the pair result. TSK-028 does not add a registry either. TSK-029 does not add a method registry, a test registry, or a generic two-group framework. TSK-030 does not add a method registry, a generic contingency record, or a relationship superclass. | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |
| REQ-T-04 | Do not install or pin a Pytics 2.0 dependency lock. Candidate directions from the ecosystem review are not that lock. | In force | TSK-034 | `pyproject.toml` | — | Respected. TSK-034 declares `scikit-learn>=1.3` under its brief ([DEC-105](DECISIONS.md#dec-105)). That is a floor, not a lock or a pin. | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |
| REQ-T-05 | Reuse one statistical layer for general relationships, target analysis, missingness relationships, dataset comparison, and drift wherever analytically appropriate. Do not implement separate statistical truths for those uses. The exact internal API is not frozen. | Not started | TSK-024, TSK-032, TSK-037, TSK-038 | — | — | Not completed. TSK-024 places Numeric × Numeric methods in `pytics.analysis`. TSK-028 places Boolean × Boolean methods in the same relationship package. TSK-029 places Numeric × Boolean methods there too. TSK-030 places Categorical × Categorical methods there too. TSK-032 reads those retained records for an explicit target and does not recalculate them. TSK-037 compares retained descriptive facts and does not add a second test. TSK-038 distribution drift reuses the relationship chi-square and expected-count kernels, the Fisher helper, and Benjamini–Hochberg, and reads Numeric values through the Numeric profile's reader. Missingness relationships do not call the relationship package yet. TSK-039 relationship drift reads retained relationship effects and does not calculate them again. Its Pearson change test lives in the Numeric × Numeric calculator. Target drift projects those records. | [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) |

Total rows: 119. Not started: 108. In force: 9. Implemented: 2 (REQ-L-04 and REQ-L-05). Verified and completed requirement rows: 0. Completed tasks: TSK-001 through TSK-041. REQ-L-04 and REQ-L-05 are Implemented. No other requirement row is completed.

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
- the multivariate anomaly estimator ([OPEN-022](DECISIONS.md#open-questions)). The univariate method is Tukey fences ([DEC-107](DECISIONS.md#dec-107)). The diagnostic estimator family is decided by [DEC-105](DECISIONS.md#dec-105);
- user-facing finding level labels ([OPEN-025](DECISIONS.md#open-questions)). The internal v0.1 levels are defined by [DEC-111](DECISIONS.md#dec-111);
- findings configuration: severity overrides, enabled families, practical thresholds, and example retention ([OPEN-009](DECISIONS.md#open-questions));
- dark mode as a committed feature ([OPEN-026](DECISIONS.md#open-questions));
- a 2.0 dependency lock or version pins ([OPEN-042](DECISIONS.md#open-questions)).

Migration mechanics are decided ([DEC-063](DECISIONS.md#dec-063)). They are not a requirement row. The denominator of `unique_ratio_non_missing` is decided ([DEC-077](DECISIONS.md#dec-077)). The frequency-observation contract, including its ratio denominators and the operational 32-value retention limit, is decided ([DEC-078](DECISIONS.md#dec-078)). The numeric-structure contract, including its ratio denominators and its integer-like and monotonicity rules, is decided ([DEC-079](DECISIONS.md#dec-079)). The string-structure contract, including native string applicability, conditional object applicability, character classes, length bounds, and ratio denominators, is decided ([DEC-080](DECISIONS.md#dec-080)). The pattern contract, including full-value UUID, IPv4, IPv6, and fixed-width ASCII hexadecimal counts, allowed overlap, and the non-missing denominator, is decided ([DEC-081](DECISIONS.md#dec-081)). The candidate-assessment contract, including support versus contradiction and the initial full-population Identifier candidate rule, is decided ([DEC-082](DECISIONS.md#dec-082)). The Numeric, Categorical, and Text candidate rules are decided ([DEC-083](DECISIONS.md#dec-083)). None of those is an open item above. The retention limit is not a semantic cardinality threshold. Integer-like counts and monotonicity flags are not Identifier, Discrete, or Binary rules. String-structure counts and length bounds are not Text, Categorical, or Identifier rules. Pattern counts are not a selected Identifier, Text, or Categorical reading. A full-population UUID or same-width hexadecimal count may support an Identifier candidate and does not select Identifier. Physical integer or floating storage may support a Numeric candidate and does not select Numeric. Physical categorical storage may support a Categorical candidate and does not select Categorical. Current string observations do not support a Text candidate. The resolution contract is decided ([DEC-085](DECISIONS.md#dec-085)). The inferred-result contract is decided ([DEC-086](DECISIONS.md#dec-086)). The column pipeline that reaches that result from one Series is decided ([DEC-087](DECISIONS.md#dec-087)). The dataset analysis that retains that column path is decided ([DEC-088](DECISIONS.md#dec-088)). The dataset overview that aggregates that analysis is decided ([DEC-089](DECISIONS.md#dec-089)). It counts a resolved selected type, including a candidate-derived selection, and it does not assign High, Medium, or Low. Cell completeness and semantic-resolution coverage use the denominators in that decision. Memory-usage semantics are not decided. Exact duplicate-row semantics are decided ([DEC-094](DECISIONS.md#dec-094)). The variables summary that reads the same analysis is decided ([DEC-090](DECISIONS.md#dec-090)). Specialized detail follows the selected semantic type. Numeric detail is structural, and [DEC-091](DECISIONS.md#dec-091) adds a finite-population descriptive result to that detail. Categorical detail uses frequency counts. Identifier detail uses pattern counts. Sum, mode, skewness, kurtosis, datetime span, timedelta duration statistics, and Text detail are not that summary. [DEC-092](DECISIONS.md#dec-092) adds true and false counts to a selected Boolean variable. Those counts are not a Binary reading. Resolution may select Identifier, Numeric, or Categorical when that candidate is the only one supported. The inferred result keeps that selection and the observed physical dtype, and it does not assign High, Medium, or Low. Partial-pattern thresholds, Categorical vocabulary thresholds, Text length thresholds, and candidate-derived confidence remain open.

The engine diagram, the three mode names, the shared statistical layer, the method-registry concept, DataFrame-only input, held-out permutation importance, the candidate dependency directions, and the semantic-foundation pipeline in DEC-064 through DEC-076 are accepted. Acceptance is not a task and not an implementation. TSK-001, TSK-002, TSK-003, TSK-004, TSK-005, TSK-006, TSK-007, TSK-008, TSK-009, TSK-010, TSK-011, TSK-012, TSK-013, TSK-014, TSK-015, TSK-016, TSK-017, TSK-018, TSK-019, TSK-020, TSK-021, TSK-022, TSK-023, TSK-024, TSK-025, TSK-026, TSK-027, TSK-028, TSK-029, TSK-030, TSK-031, TSK-032, TSK-033, TSK-034, and TSK-035 are the only implementation tasks. TSK-016 connects one Series to the inferred result. TSK-017 retains that analysis for each physical column of a DataFrame. TSK-018 summarizes that analysis and does not render it. TSK-019 summarizes each column and does not render it. TSK-020 describes a selected Numeric column and does not render it. TSK-021 counts a selected Boolean column and does not render it. TSK-022 records exact missingness structure and does not render it. TSK-023 records exact duplicate rows and does not render them. TSK-024 describes selected Numeric × Numeric pairs and does not render them. TSK-025 makes a non-representable Numeric statistic unavailable without aborting dataset analysis, and it does not render that fact. TSK-026 describes selected Numeric × Categorical pairs and does not render them. TSK-027 moves relationship metadata onto the record that owns it and does not render that fact. None of them implements a user override, an effective interpretation, or the downstream engines. TSK-033 retains an exact Categorical distribution and does not render it. TSK-034 fits one diagnostic model for an explicit target and does not render it. TSK-035 records exact-duplicate and repeated deterministic-mapping evidence for an explicit target and does not render it. The next implementation slice has not been selected.
