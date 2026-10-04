# Product contract

Status: **Accepted** product direction, with the qualifications recorded here and in [DECISIONS.md](DECISIONS.md).

Requirement IDs in this file are tracked in [PROGRESS.md](PROGRESS.md). Analytical detail is in [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md). Report structure is in [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md).

## Identity

Pytics is an extremely good analytical microscope for datasets.

Primary audience: professional data scientists and professional data analysts.

Primary purpose:

- understand a dataset;
- understand relationships inside a dataset;
- understand data-quality characteristics;
- understand a target where one is supplied;
- compare two datasets;
- understand changes and drift between datasets.

Pytics is about understanding. It is not about optimizing predictive performance. Where a target is supplied, TSK-032 records that column's semantic state, its own missingness, and the relationships already calculated with the other columns ([DEC-103](DECISIONS.md#dec-103)). TSK-033 adds the exact observed distribution of a Categorical target from the shared descriptive layer ([DEC-104](DECISIONS.md#dec-104)). It does not infer a target, a problem type, or an imbalance verdict, and it does not fit a diagnostic model. The public `profile` call is not yet that analysis.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-01 | Serve the six purposes above for a professional audience. | Accepted |
| REQ-P-02 | Treat understanding as the goal. Do not optimize predictive performance. | Accepted |

## Non-goals

Pytics is not intended to become:

- an AutoML platform;
- a BI dashboard;
- a data-cleaning framework;
- a notebook replacement;
- an AI-insights gimmick;
- an automatic prescriptive system.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-03 | Stay outside the non-goals listed above. | Out of scope for those product types. The exclusion is Accepted. |

## Philosophy

Report and observe; do not prescribe.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-04 | Report observations and evidence. Do not prescribe actions. | Accepted |

## Audience

Design for professionals. Do not add educational clutter merely to accommodate beginners. Methods and assumptions must nevertheless remain inspectable and transparent.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-05 | Design for professionals, without beginner clutter, and keep methods and assumptions inspectable. | Accepted |

## Pandas first, DataFrame only

Pytics 2.0 is Pandas Perfect. Excellent pandas support matters more than premature support for multiple dataframe engines.

The core analytical API is DataFrame-first and DataFrame-only ([DEC-040](DECISIONS.md#dec-040)):

```python
pytics.profile(df)
pytics.compare(df_a, df_b)
```

Core does not take responsibility for CSV parsing, separators, encodings, Parquet engines, remote file loading, or generic path detection. The user loads data with pandas and passes a DataFrame.

Exact public signatures are not frozen ([OPEN-004](DECISIONS.md#open-questions)).

Do not design a Polars or Arrow abstraction at this stage merely for theoretical future compatibility.

The architecture should avoid unnecessary decisions that make future expansion impossible. What counts as an unnecessary blocking decision is [OPEN-002](DECISIONS.md#open-questions).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-06 | Implement the core analytical API against pandas DataFrames only. Do not load files or parse CSV, Parquet, encodings, or remote paths in core. Do not add a multi-engine dataframe abstraction at this stage. | Accepted |

## Semantic-first analysis

Physical pandas dtype is not sufficient. Pytics must infer semantic meaning.

The semantic rules, including confidence, overrides, and the prohibition on silent coercion, are specified in [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) (`REQ-S-01` through `REQ-S-09`). The conceptual pipeline, from observations through an optional override to the effective interpretation, is [DEC-064](DECISIONS.md#dec-064) through [DEC-076](DECISIONS.md#dec-076). Candidate Resolution v0.1 does not use a numeric total-score ([DEC-066](DECISIONS.md#dec-066)). The resolution foundation selects a structural reading or exactly one supported candidate, and otherwise abstains or stays ambiguous, without assigning confidence from candidate counts ([DEC-085](DECISIONS.md#dec-085)). That limit does not withdraw the separate prohibition on a composite data-quality score.

## No arbitrary quality score

Do not create an overall score in the style of 82/100. Report concrete evidence and findings.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-07 | Do not produce a composite data-quality score. | Accepted |

## Statistical depth

Pytics should be statistically rich rather than merely wrapping `DataFrame.describe()`.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-08 | Provide statistical depth beyond a `DataFrame.describe()` wrapper. | Accepted |

Methodological direction is accepted in [STATISTICAL_METHODS.md](STATISTICAL_METHODS.md). The catalog is not frozen ([OPEN-006](DECISIONS.md#open-questions), `REQ-K-03`).

## Evidence before decoration

Every chart should answer an analytical question. No chart should exist merely because a plotting library makes it easy to create.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-09 | Every chart must answer an analytical question. | Accepted |

## Effect size first

For inferential statistics: effect size first, statistical significance second.

P-values should not be presented as the primary interpretation of an analysis.

Where appropriate, analyses should consider:

- effect size;
- uncertainty;
- confidence or credible intervals;
- p-values;
- assumptions;
- sample size;
- missing observations;
- multiple-testing correction.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-10 | Lead inferential presentation with effect size, uncertainty, and context. Do not lead with the p-value, use significance stars, or treat a tiny p-value as inherent importance. Where correction applies, distinguish raw and adjusted p-values. | Accepted |

"Where appropriate" is unresolved at the level of individual methods ([OPEN-006](DECISIONS.md#open-questions)). False-discovery-rate control is the preferred screening direction, with Benjamini-Hochberg as the leading candidate. The test family is not defined ([OPEN-007](DECISIONS.md#open-questions), [DEC-056](DECISIONS.md#dec-056)). TSK-024 stores a Numeric × Numeric estimate before its raw p-value and does not adjust that p-value ([DEC-095](DECISIONS.md#dec-095)). TSK-025 does not change that presentation ([DEC-096](DECISIONS.md#dec-096)). TSK-026 stores eta squared before the raw one-way ANOVA p-value for a Numeric × Categorical pair and does not adjust that p-value ([DEC-097](DECISIONS.md#dec-097)). TSK-027 does not add a dataset-wide method or a dataset-wide adjustment. Adjustment stays on each frequentist result and is still not applied ([DEC-098](DECISIONS.md#dec-098)). TSK-028 stores the Boolean probability difference, probability ratio, and phi before the raw Fisher exact p-value and does not adjust that p-value ([DEC-099](DECISIONS.md#dec-099)). It does not add a confidence interval or a strength label. TSK-029 stores the Numeric × Boolean mean difference, Hedges' g, and a 95% Welch–Satterthwaite interval for the mean difference before the raw Welch p-value, and does not adjust that p-value ([DEC-100](DECISIONS.md#dec-100)). It does not add a strength label. TSK-030 stores the contingency table and classical Cramér's V before the raw Pearson chi-square p-value for a Categorical × Categorical pair, with expected-count diagnostics beside them, and does not adjust that p-value ([DEC-101](DECISIONS.md#dec-101)). It does not add a strength label. Five calculated families do not complete relationship analysis. TSK-031 keeps that order and stores a Benjamini–Hochberg adjusted p-value beside the available primary raw p-value ([DEC-102](DECISIONS.md#dec-102)). Pearson's correlation p-value stays raw. The adjusted value is not a significance flag. The test family for other analyses remains open ([OPEN-007](DECISIONS.md#open-questions)).

## Bayesian inference

Bayesian inference is in scope when it helps understand data. It complements frequentist inference. It is not Bayesian predictive optimization.

Bayesian analyses must be transparent about:

- method;
- prior;
- posterior;
- credible interval;
- relevant probability statements;
- approximation or sampling where applicable;
- limitations.

Do not promise a Bayesian counterpart for every statistical analysis.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-11 | Allow Bayesian analyses that help understanding, under the transparency rules above, without promising universal Bayesian coverage and without Bayesian predictive optimization. | Accepted |

Bayesian analysis is selective and lightweight ([DEC-057](DECISIONS.md#dec-057)). The catalog remains [OPEN-008](DECISIONS.md#open-questions). NumPy and SciPy are the current calculation direction, not a pin. PyMC is not intended as a core dependency at present.

## Reproducibility

Where reasonably possible, the same data, configuration, Pytics version, and random seed should produce the same analytical result.

Sampling, stochastic models, and other nondeterministic methods must record relevant metadata. Sampling must never be hidden. Report Info requirements are `REQ-IA-15`.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-12 | Reproduce results for the same data, configuration, version, and seed where reasonably possible, and record metadata for nondeterministic methods. | Accepted |

The seed's place in the public configuration is [OPEN-009](DECISIONS.md#open-questions). Controlled sampling for expensive semantic evidence is accepted ([DEC-054](DECISIONS.md#dec-054)). Other sampling rules, and sample sizes, are [OPEN-010](DECISIONS.md#open-questions).

## How a result is used

Intended direction, not a frozen API:

```python
report = pytics.profile(df)
```

That call performs analysis. It should not dump charts into the notebook. A plain notebook representation of `report` should stay compact.

Explicit rendering may eventually look approximately like:

```python
report.show()
report.to_html("report.html")
report.to_pdf("report.pdf")
```

The result should expose structured analytical results programmatically. Conceptual access looks like `report.variables["income"]`, `report.missing`, `report.relationships`, and `report.findings`. Those attribute names are not frozen.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-13 | `profile` performs analysis without dumping charts into the notebook, and a plain notebook representation stays compact. | Accepted |
| REQ-P-14 | Expose structured results programmatically, and render HTML and PDF through explicit presentation entry points. | Accepted as behavior. Method and attribute names are Proposed / not yet finalized. |

HTML is the canonical interactive report. PDF is a professional static, shareable representation. Visual and navigation rules are in [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md).

## Configuration

Goal: zero-config by default, deeply configurable when needed.

Avoid a public function with dozens of individual keyword arguments. A structured configuration object is likely. Its shape is not frozen.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-15 | Default to zero configuration, and avoid a large public keyword-argument surface. | Accepted as a goal. The configuration object is Proposed / not yet finalized. |

## Performance modes

`quick`, `standard`, and `deep` are accepted. Standard is the intended default ([DEC-058](DECISIONS.md#dec-058)). Exact contents, thresholds, and the signature that selects a mode are not frozen ([OPEN-010](DECISIONS.md#open-questions), [OPEN-004](DECISIONS.md#open-questions)). The current direction is in [STATISTICAL_METHODS.md](STATISTICAL_METHODS.md). Those lists are not a closed catalog. Any sampling that does occur must be recorded transparently (`REQ-P-12`, `REQ-IA-15`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-P-16 | Provide quick, standard, and deep analysis modes. Standard is the intended default. Exact contents and thresholds are not frozen. | Accepted as a concept |

## Redesign boundary

Pytics 2.0 is a clean redesign, not a blind incremental refactor of the 1.1.5 architecture. Useful algorithms, tests, behavior, and ideas from 1.1.5 may be reused deliberately. Nothing is inherited automatically.

Do not treat the current PDF failure, documentation mismatches, or monolithic structure as work to patch in place. The end state is replacement of the implementation inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). In-place coexistence until each replacement is verified is [DEC-063](DECISIONS.md#dec-063). See [BASELINE_1_1_5.md](BASELINE_1_1_5.md).
