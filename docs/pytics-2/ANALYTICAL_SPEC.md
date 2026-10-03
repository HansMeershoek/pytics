# Analytical specification

Status of areas A–N: **Accepted** as parts of the Pytics 2.0 analytical design ([DEC-014](DECISIONS.md#dec-014)).

This file is the analytical contract. It does not freeze algorithms, thresholds, or library choices.

Recording rules from [README.md](README.md#recording-convention) apply. In particular, "such as" and "may" are not rewritten into "always emit every named statistic". Confirming whether each named concept is mandatory output is [OPEN-001](DECISIONS.md#open-questions).

Cross-cutting product rules (`REQ-P-*`) are in [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md).

## Semantic model

Physical pandas dtype is not the semantic type ([DEC-041](DECISIONS.md#dec-041)).

Pytics distinguishes physical dtype, observed characteristics, and semantic interpretation. Physical dtype is evidence. The original physical dtype remains inspectable.

Inference is evidence-driven. The accepted conceptual stages, not a frozen function decomposition, are:

```text
Physical classification
        |
        v
Basic evidence collection
        |
        v
Pattern / structural evidence
        |
        v
Candidate semantic types
        |
        v
Conflict resolution
        |
        v
Semantic interpretation
```

An interpretation must be able to retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source. Sources are: inferred; directly supported by physical dtype; explicitly configured by the user. Exact object names are [OPEN-004](DECISIONS.md#open-questions).

User-facing confidence is High, Medium, or Low, together with concrete evidence ([DEC-042](DECISIONS.md#dec-042)). Do not expose a pseudo-precise figure such as `0.87321` unless a future statistically justified reason exists. An internal score may help conflict resolution. It must not become unexplained user-facing precision.

Example, not a fixture:

```text
Semantic type
Identifier

Confidence
High

Evidence
- 100% unique among non-missing observations
- integer values follow a near-sequential pattern
- column name contains an identifier token
```

Ambiguity stays visible ([DEC-043](DECISIONS.md#dec-043)). A selected reading may carry an alternative. Example, not a fixture: values `1, 2, 3, 4, 5` in a column named `score` may be selected as numeric discrete with medium confidence, with ordinal categorical as the alternative, because no explicit order was supplied.

A column name may support an inference. It must not determine semantic type by itself.

Explicit per-variable semantic configuration is a first-class capability ([DEC-044](DECISIONS.md#dec-044)). The API is not accepted. User intent normally takes precedence. If the configured interpretation cannot be meaningfully applied, report the conflict. Do not silently coerce or repair the data.

Pytics observes ([DEC-045](DECISIONS.md#dec-045)). It does not silently clean, repair, coerce, or mutate the original DataFrame. It may detect numeric-like values, missing-like literals, and possible interpretations. It preserves the distinction between source representation and analytical interpretation. A mostly numeric string column containing `"?"` must not be rewritten into clean numeric data.

Pattern detection does not rewrite the source Series ([DEC-050](DECISIONS.md#dec-050)). URL-like, email-like, UUID-like, path-like, datetime-like, and other well-defined structural forms may be detected. A datetime interpretation of strings still records that the physical source type was string.

Cheap evidence uses the full column where practical. Expensive evidence, particularly string and pattern analysis on very large data, may use controlled sampling ([DEC-054](DECISIONS.md#dec-054)). Sampling must be transparent, reproducible where possible, recorded, tied to the configured analysis mode, and considered when confidence is expressed. Thresholds and sample sizes are [OPEN-010](DECISIONS.md#open-questions). Exact inference cutoffs are [OPEN-044](DECISIONS.md#open-questions).

Empty and Constant are semantic interpretations and dataset facts ([DEC-046](DECISIONS.md#dec-046)):

- all values missing → semantic interpretation Empty, and a dataset fact that the column is empty;
- one unique non-missing value → semantic interpretation Constant, and a dataset fact that the column is constant.

Those two definitions take precedence over a Boolean, Numeric, or Identifier reading of the same column. The physical dtype remains inspectable. Do not duplicate the underlying computation unnecessarily.

Ordinal order is not inferred from labels ([DEC-052](DECISIONS.md#dec-052)). Ordinal semantics are accepted only when the user configures them, or when the source explicitly represents order, for example an ordered pandas categorical dtype. Without that, Low / Medium / High remains categorical. Pytics does not invent semantic ordering. Ordinal is not in the minimum list below. When ordinal semantics are accepted, the storage question remains [OPEN-016](DECISIONS.md#open-questions).

Semantic interpretation guides eligibility ([DEC-053](DECISIONS.md#dec-053)). The examples in that decision are direction, not a closed matrix ([OPEN-043](DECISIONS.md#open-questions)).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-S-01 | Infer a semantic type. The minimum concepts are Numeric, Categorical, Boolean/Binary, Text/String, Datetime, Timedelta, Identifier, Constant, and Empty. Empty and Constant are also dataset facts. | Accepted |
| REQ-S-02 | Retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source of interpretation. User-facing confidence is High, Medium, or Low, with concrete evidence. Do not present pseudo-precise confidence. | Accepted |
| REQ-S-03 | Do not silently clean, repair, coerce, or mutate the original DataFrame. Preserve the distinction between source representation and analytical interpretation. Pattern detection must not rewrite the source Series. | Accepted |
| REQ-S-04 | Make inference evidence-driven and transparent, and expose uncertainty. A column name may support an inference and must not determine semantic type by itself. | Accepted |
| REQ-S-05 | Distinguish physical dtype, observed characteristics, and semantic interpretation. Keep the original physical dtype inspectable. | Accepted |
| REQ-S-06 | Treat explicit per-variable semantic configuration as a first-class capability. User intent normally takes precedence. If a configured interpretation cannot be meaningfully applied, report the conflict instead of silently coercing. The exact API is not frozen. | Accepted. API not frozen. |
| REQ-S-07 | Give Timedelta dedicated duration analysis that preserves duration semantics and readable units. Do not present user-facing timedelta results as raw nanoseconds. | Accepted |
| REQ-S-08 | Do not infer ordinal ordering from category labels. Accept ordinal semantics only when the user configures them or the source explicitly represents order. | Accepted |
| REQ-S-09 | Let semantic interpretation guide which analyses are meaningful. The specification examples are direction, not a closed eligibility matrix. | Accepted as direction |

Subtypes may exist where useful. Continuous and Discrete are permitted numeric concepts. That permission is not a subtype taxonomy ([OPEN-014](DECISIONS.md#open-questions)).

## A — Dataset-level analysis

Surface factual findings. Do not produce a composite quality score (`REQ-P-07`).

| ID | In-scope concepts | Status |
| --- | --- | --- |
| REQ-A-01 | Rows, columns, cells, and dataset dimensions. | Accepted. "Dataset dimensions" is not otherwise defined ([OPEN-018](DECISIONS.md#open-questions)). |
| REQ-A-02 | Memory usage and memory per row. | Accepted |
| REQ-A-03 | Missingness, complete rows, and incomplete rows. | Accepted |
| REQ-A-04 | Duplicate rows and unique rows. | Accepted |
| REQ-A-05 | Physical dtype composition and semantic type composition. | Accepted |
| REQ-A-06 | Constant columns, near-constant columns, empty columns, identifier candidates, and high-cardinality columns. | Accepted as concepts. Thresholds for near-constant and high cardinality are not set ([OPEN-018](DECISIONS.md#open-questions)). |
| REQ-A-07 | Infinities. | Accepted |
| REQ-A-08 | Relevant computational-analysis metadata. | Accepted as a named concept. Contents are not defined ([OPEN-018](DECISIONS.md#open-questions)). |

## B — Numeric analysis

Statistically rich numeric profiling, where meaningful.

A physically numeric column that is not better interpreted as Empty, Constant, Boolean/Binary, or Identifier may be interpreted as Numeric ([DEC-049](DECISIONS.md#dec-049)). Subtypes may include Continuous and Discrete. Do not treat integer dtype as discrete, or float dtype as continuous, without the observed values. Subtype inference stays conservative.

| ID | In-scope concepts | Status |
| --- | --- | --- |
| REQ-B-01 | Count, missing, distinct, zeros, negatives, infinities, min, max, range, and sum. | Accepted, where meaningful. |
| REQ-B-02 | Mean, median, mode where meaningful, variance, standard deviation, IQR, MAD, coefficient of variation, and quantiles or percentiles. | Accepted, where meaningful. |
| REQ-B-03 | Skewness and kurtosis. | Accepted, where meaningful. |
| REQ-B-04 | Robust statistics. | Accepted as a category. Which robust measures beyond those named in `REQ-B-02` and section J are not finalized ([OPEN-006](DECISIONS.md#open-questions)). |
| REQ-B-05 | Distribution analysis, and normality or other distribution diagnostics where responsible. | Accepted. Diagnostics are evidence and signals, not overconfident declarations. |
| REQ-B-06 | Univariate outlier signals. | Accepted as signals. The method set is Proposed / not yet finalized (section J). |

Trimmed mean was named as "potentially trimmed mean". It is **Proposed / not yet finalized** and has no requirement ID ([OPEN-019](DECISIONS.md#open-questions)).

## C — Categorical analysis

Categorical is a semantic interpretation, not a synonym for pandas `object` ([DEC-049](DECISIONS.md#dec-049)). A categorical variable may physically be a categorical dtype, a string, an object, or numeric codes. Do not assume low-cardinality numeric values are category codes without sufficient evidence or explicit configuration.

| ID | In-scope concepts | Status |
| --- | --- | --- |
| REQ-C-01 | Count, missing, distinct, and cardinality ratio. | Accepted |
| REQ-C-02 | Mode, mode frequency, top categories, rare categories, and bottom categories where useful. | Accepted |
| REQ-C-03 | Entropy, normalized entropy, and concentration. | Accepted |
| REQ-C-04 | Singleton categories and rare-category percentage. | Accepted |
| REQ-C-05 | Frequency distribution. | Accepted |
| REQ-C-06 | Low, medium, and high cardinality characteristics. Thresholds should ultimately be configurable. | Accepted as behavior. Threshold values are not set ([OPEN-018](DECISIONS.md#open-questions)). |
| REQ-C-07 | Do not produce meaningless charts of thousands of categories. | Accepted |

## D — Boolean/Binary analysis

Boolean/Binary is a first-class analytical family (`REQ-S-01`, [DEC-047](DECISIONS.md#dec-047)). Binary cardinality does not imply Boolean meaning.

- A physical pandas boolean is very strong Boolean/Binary evidence.
- `{0, 1}` may be a binary interpretation and is not automatically Boolean.
- Yes/no or true/false strings may be a binary interpretation under conservative token recognition.
- An arbitrary two-category variable stays categorical, including as a binary category, and is not described as Boolean.

The subtype taxonomy is [OPEN-014](DECISIONS.md#open-questions).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-D-01 | Support conservative inference of binary-like values where the evidence justifies it. Examples may include true/false, and possibly 0/1 or yes/no. | Accepted |
| REQ-D-02 | Do not treat binary cardinality as Boolean meaning. Do not treat every {0, 1} column as Boolean. Keep arbitrary two-category variables categorical. | Accepted |
| REQ-D-03 | Record confidence and reason for a boolean or binary inference. | Accepted. This is also required generally by `REQ-S-02`. |

## E — Datetime and time analysis

Native pandas datetime and timezone-aware datetime dtypes are strong evidence of Datetime semantics ([DEC-050](DECISIONS.md#dec-050)).

String-to-datetime inference is conservative. It considers parse success, representation and format consistency, plausible ranges, ambiguity, and sampling or full-column verification. Do not read arbitrary numeric-looking strings as dates. When a string column receives a datetime interpretation, the physical source type remains string (`REQ-S-03`).

| ID | In-scope concepts | Status |
| --- | --- | --- |
| REQ-E-01 | Earliest, latest, range or span, missingness, distinct values, duplicate timestamps, timezone, and inferred resolution. | Accepted |
| REQ-E-02 | Monotonicity, gaps, irregular intervals, frequency, relevant calendar distributions, and time-structure signals. | Accepted |
| REQ-E-03 | Distinguish a column that contains dates from an actual time-series structure. | Accepted |
| REQ-E-04 | Do not indiscriminately run deeper time-series diagnostics on every datetime column. | Accepted |

Trend, seasonality, and autocorrelation are not a default pass on every datetime column ([DEC-031](DECISIONS.md#dec-031), `REQ-E-04`). When a datetime relationship is justified, section K directs that analysis toward temporal structure, including trend, change, association, and periodic or seasonal structure where justified ([DEC-055](DECISIONS.md#dec-055)). That is not a commitment to a closed time-series catalog. The scope of a deeper diagnostic pass remains [OPEN-020](DECISIONS.md#open-questions). Autocorrelation has no accepted method yet. The Time Series report section appears only when genuine time structure is inferred or explicitly configured (`REQ-IA-13`).

## Timedelta duration analysis

Timedelta is a first-class semantic type with dedicated duration analysis ([DEC-051](DECISIONS.md#dec-051), `REQ-S-07`).

Analysis may reuse numeric concepts where appropriate. It must preserve duration semantics and readable units. Do not present user-facing results as raw nanoseconds.

In-scope concepts, not a closed mandatory catalog ([OPEN-001](DECISIONS.md#open-questions)): count, missing, minimum, maximum, range, mean, median, quantiles, distribution, zero durations, and negative durations.

Results belong in type-aware variable detail. This section does not add a navigation destination.

## F — Text/String analysis

Distinguish, where evidence supports it ([DEC-049](DECISIONS.md#dec-049)):

- categorical-like string;
- free text;
- identifier-like string;
- URL-like;
- email-like;
- path-like;
- datetime-like;
- generic string.

Cardinality alone is insufficient. String evidence may include uniqueness, repetition, character-length distribution, word counts, token or pattern consistency, and structural patterns. Detection of a structural form does not rewrite the Series (`REQ-S-03`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-F-01 | Distinguish the string roles listed above. | Accepted |
| REQ-F-02 | Text diagnostics covering count, missing, distinct, empty strings, whitespace-only values, length statistics and distribution, word counts, leading or trailing whitespace, line breaks, Unicode or non-ASCII characteristics, pattern consistency, and duplicate text. | Accepted |
| REQ-F-03 | Pytics core must not become a full NLP platform. | Out of scope. The exclusion is Accepted. |

Common tokens, "potentially" and "where appropriate", are **Proposed / not yet finalized** ([OPEN-019](DECISIONS.md#open-questions)).

## G — Identifier detection

Identifier is a first-class semantic concept (`REQ-S-01`).

Admissible evidence, not a closed detector ([DEC-048](DECISIONS.md#dec-048)): uniqueness ratio, duplicate count, missing count, UUID or GUID-like structure, hash-like structure, sequential integer patterns, fixed-width codes, alphanumeric code patterns, prefixes and suffixes, monotonic or sequential behavior, and column name as a weak supporting signal.

`unique_ratio == 1` alone is not sufficient. Thresholds are [OPEN-044](DECISIONS.md#open-questions).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-G-01 | Treat Identifier as a first-class semantic concept. | Accepted |
| REQ-G-02 | Expose the evidence and reasoning for identifier detection. | Accepted |
| REQ-G-03 | Normally exclude identifiers from ordinary correlation, diagnostic target modeling, and ordinary multivariate anomaly modeling, unless explicitly configured otherwise. | Accepted |

## H — Missing-data analysis

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-H-01 | Report dataset-level, variable-level, and row-level missingness. | Accepted |
| REQ-H-02 | Report missingness patterns and co-missingness. | Accepted |
| REQ-H-03 | Report relationships between missingness and other variables. | Accepted. These relationships reuse the shared statistical layer (`REQ-T-05`). |
| REQ-H-04 | Report missing-like literals such as `""`, whitespace, `"N/A"`, `"null"`, and `"?"`. Do not silently rewrite them as missing data. | Accepted. The examples are not stated to be a closed dictionary ([OPEN-018](DECISIONS.md#open-questions)). |
| REQ-H-05 | Keep MCAR, MAR, and MNAR diagnostics methodologically conservative. Do not claim that missingness is definitively MAR or MNAR when the observed data cannot support that conclusion. | Accepted |

## I — Duplicate analysis

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-I-01 | Report exact duplicate rows and duplicate groups. | Accepted |
| REQ-I-02 | Report duplicate identifiers. | Accepted |
| REQ-I-03 | Report conflicting duplicates. | Accepted |
| REQ-I-04 | Support controlled partial-duplicate analysis. | Accepted as a named capability. "Controlled" is not defined ([OPEN-018](DECISIONS.md#open-questions)). |
| REQ-I-05 | Do not run uncontrolled combinatorial searches over all possible column combinations. | Accepted |
| REQ-I-06 | Fuzzy or near-duplicate analysis is not a default core operation. | Accepted as a boundary. |

Fuzzy or near-duplicate analysis may eventually become optional or deep functionality. That capability is **Future investigation** ([OPEN-020](DECISIONS.md#open-questions)).

## J — Outliers and multivariate anomalies

An outlier does not mean an error. An anomaly does not mean bad data. Do not automatically recommend deleting anomalous observations (`REQ-P-04`).

Identifiers are normally excluded from ordinary multivariate anomaly modeling (`REQ-G-03`). Exact eligibility rules are [OPEN-043](DECISIONS.md#open-questions).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-J-01 | Treat outliers and anomalies as observations to understand, not as errors to delete, and do not automatically recommend deletion. | Accepted |
| REQ-J-02 | Support robust univariate outlier analysis. | Accepted |
| REQ-J-03 | Support multivariate anomaly detection. | Accepted |
| REQ-J-04 | Multivariate anomaly analysis should eventually provide explainability or context where possible. | Accepted as a goal. The design is Proposed / not yet finalized. |

Potential univariate perspectives, not a finalized method set: IQR, robust MAD-based methods, classical z-score where appropriate, and extreme quantiles. **Proposed / not yet finalized** ([OPEN-022](DECISIONS.md#open-questions)).

## K — Relationships and statistical inference

Relationship analysis must be type-aware.

A relationship separates description, effect, uncertainty, frequentist inference, Bayesian inference where appropriate, diagnostics, and method metadata (`REQ-K-04`). It is not reduced to a p-value. Exact objects are [OPEN-004](DECISIONS.md#open-questions).

Relevant capability categories:

- association measures;
- correlation measures;
- effect sizes;
- confidence intervals;
- hypothesis tests;
- assumption handling;
- robust or non-parametric alternatives;
- multiple-testing correction;
- Bayesian inference.

Assumptions are diagnostic context, not a gate (`REQ-K-05`). Where correction applies, raw and adjusted p-values stay distinct. Significance stars are not used (`REQ-P-10`).

The shared statistical layer is accepted (`REQ-T-05`). The method-registry concept is accepted and must not be implemented yet (`REQ-T-03`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-K-01 | Relationship analysis must be type-aware. | Accepted |
| REQ-K-02 | The capability categories listed above are in scope, under `REQ-P-10` and `REQ-P-11`. | Accepted as categories. |
| REQ-K-03 | Do not hard-code a final method catalog before that catalog is decided. | Accepted. In force. [DEC-055](DECISIONS.md#dec-055) does not retire this. |
| REQ-K-04 | Separate a relationship into description, effect, uncertainty, frequentist inference, Bayesian inference where appropriate, diagnostics, and method metadata. Do not reduce a relationship to a p-value. | Accepted. Object design is not frozen. |
| REQ-K-05 | Treat statistical assumptions as diagnostic context. Do not invalidate a method solely because an assumption test is significant. Keep method selection explainable. | Accepted |

Pair-type direction is accepted in [STATISTICAL_METHODS.md](STATISTICAL_METHODS.md) ([DEC-055](DECISIONS.md#dec-055)). It covers numeric–numeric, numeric–binary, numeric–categorical, binary–binary, categorical–categorical, datetime–numeric, and datetime–categorical. Ordinal pairs apply only under `REQ-S-08`. That direction is not a closed catalog. Exact formulas, selection rules, and pair types with no direction yet are [OPEN-006](DECISIONS.md#open-questions).

Identifiers are excluded from ordinary correlation by default (`REQ-G-03`). Extreme high-cardinality categorical pairs are protected from meaningless or computationally explosive analysis. Datetime values are not converted to integers for ordinary correlation. A datetime column does not by itself establish a time-series context (`REQ-E-03`).

## L — Target analysis

`profile(df, target="...")` should recognize the target's semantics and problem type where possible. That call shape is the intended direction. The exact signature is not frozen (`REQ-P-14`).

Target analysis may include:

- classification or regression interpretation;
- target distribution;
- imbalance;
- feature-target relationships;
- effect sizes;
- inference;
- potential leakage signals.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-L-01 | Where a target is supplied, recognize target semantics and problem type where possible. | Accepted |
| REQ-L-02 | Target analysis may cover distribution, imbalance, feature-target relationships, effect sizes, and inference. | Accepted as conditional scope. |
| REQ-L-03 | Surface potential target leakage as evidence or signals. Do not assert leakage without a sufficient basis. | Accepted |
| REQ-L-04 | Pytics may fit one lightweight, untuned diagnostic model to expose multivariate feature-target relationships. The model is for understanding data architecture, not for predictive optimization. | Accepted as a bound. |
| REQ-L-05 | Validate the diagnostic model with responsible holdout or cross-validation. Do not evaluate it only on the observations used to fit it. | Accepted |
| REQ-L-06 | Do not add hyperparameter search, model leaderboards, model competitions, automated tuning, or deployment workflows. | Out of scope. The exclusion is Accepted. |
| REQ-L-07 | Use held-out permutation importance as the primary feature-importance direction. Report spread across permutations where applicable. Warn that correlated predictors can share or obscure that importance. Do not present it as causal importance. The estimator family is not chosen. | Accepted as direction. Family is [OPEN-013](DECISIONS.md#open-questions). |

Feature-target relationships reuse the shared relationship layer (`REQ-T-05`, [DEC-059](DECISIONS.md#dec-059)). Target-specific behavior adds distribution, imbalance, the diagnostic model, and potential leakage. Do not select Random Forest, Extra Trees, gradient boosting, or another estimator in place of [OPEN-013](DECISIONS.md#open-questions).

Problem types beyond a classification/regression interpretation are [OPEN-023](DECISIONS.md#open-questions).

Identifiers are normally excluded from diagnostic target modeling unless explicitly configured otherwise (`REQ-G-03`).

## M — Dataset comparison and drift

`compare()` is a first-class capability, not an afterthought.

Comparison should eventually cover:

- schema change;
- physical dtype change;
- semantic type change;
- missingness change;
- duplicate change;
- cardinality change;
- category change;
- numeric distribution change;
- categorical distribution change;
- relationship change;
- target change;
- drift analysis.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-M-01 | `compare()` is a first-class capability and uses the same product language as profile. | Accepted. Distribution, relationship, and drift comparisons reuse the shared statistical layer where analytically appropriate (`REQ-T-05`). |
| REQ-M-02 | Explain what changed. Do not merely place two profile reports side by side. | Accepted |
| REQ-M-03 | Report drift neutrally as observed or material change. Do not automatically label it bad. | Accepted |
| REQ-M-04 | The change types listed above are the destination scope of comparison. | Accepted as destination scope. |

"Eventually" means this list is not an approved first implementation slice. Sequencing is [OPEN-024](DECISIONS.md#open-questions). Comparison of more than two datasets was not specified ([OPEN-024](DECISIONS.md#open-questions)).

The illustrative `ComparisonReport` fields in [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) are not accepted ([OPEN-004](DECISIONS.md#open-questions)).

## N — Findings

Findings are structured analytical objects, not free-form AI-generated prose.

A finding should retain enough evidence to trace it back to:

- metric;
- value;
- threshold where relevant;
- method;
- variables;
- source analysis.

Rendered text is a presentation of a structured finding. Pytics core must be able to produce findings without an LLM.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-N-01 | Findings are structured objects traceable to metric, value, threshold where relevant, method, variables, and source analysis. | Accepted |
| REQ-N-02 | Rendered finding text presents the structured finding. It is not the source of the finding. | Accepted |
| REQ-N-03 | Core findings must be producible without an LLM. | Accepted |
| REQ-N-04 | Do not use gamified or sensational finding labels. | Accepted |

Possible restrained levels — information, notable, and warning — are **Proposed / not yet finalized** ([OPEN-025](DECISIONS.md#open-questions)).
