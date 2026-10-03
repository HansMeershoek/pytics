# Statistical methods

Status: rules and directions below that are marked Accepted are binding. The method catalog is not.

Do not implement a catalog, a method registry, or a Bayesian stack from this file. `REQ-K-03` remains in force. [DEC-055](DECISIONS.md#dec-055) does not retire it.

Numeric summaries in this file are downstream analysis. They are not semantic-inference detectors ([DEC-069](DECISIONS.md#dec-069)). Numeric-structure evidence counts finite values, signs, infinities, and integer-like values for later candidate assessment ([DEC-079](DECISIONS.md#dec-079)). It is not these summaries. String-structure evidence counts empty strings, whitespace, character classes, and length bounds for later candidate assessment ([DEC-080](DECISIONS.md#dec-080)). It is not text profiling and not a semantic reading. Pattern evidence counts full-value UUID, IPv4, IPv6, and fixed-width hexadecimal syntax for later candidate assessment ([DEC-081](DECISIONS.md#dec-081)). It is not an Identifier reading and not a semantic type. An Identifier candidate assessment may use a full-population UUID or same-width hexadecimal count as support for that candidate ([DEC-082](DECISIONS.md#dec-082)). That support is not a selected semantic type and not a downstream statistic.

## Accepted inferential rules

These are product rules. The contract detail sits in [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) and [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md).

| Topic | Rule | Status |
| --- | --- | --- |
| Depth | Statistically rich analysis, not a wrapper around `DataFrame.describe()` (`REQ-P-08`). | Accepted |
| Effect size | Effect, uncertainty, and context come before the p-value. No significance stars. A tiny p-value is not inherent importance (`REQ-P-10`, [DEC-056](DECISIONS.md#dec-056)). | Accepted |
| Relationship shape | A relationship separates description, effect, uncertainty, frequentist inference, Bayesian inference where appropriate, diagnostics, and method metadata. It is not a p-value (`REQ-K-04`). | Accepted. Object design is [OPEN-004](DECISIONS.md#open-questions). |
| Context | Where appropriate, consider effect size, uncertainty, confidence or credible intervals, p-values, assumptions, sample size, missing observations, and multiple-testing correction. | Accepted as considerations. Per-method formulas are [OPEN-006](DECISIONS.md#open-questions). |
| Raw and adjusted p-values | Where correction applies, the raw p-value and the adjusted p-value stay distinct. | Accepted |
| Multiple testing | False-discovery-rate control is the preferred direction for broad relationship screening. Benjamini-Hochberg is the leading candidate. It is not a universal rule. | Accepted as direction. The test family is [OPEN-007](DECISIONS.md#open-questions). |
| Assumptions | Assumptions are diagnostic context. A significant normality test does not by itself invalidate a method. Method selection stays explainable (`REQ-K-05`). | Accepted |
| Distributional claims | Normality and other distribution diagnostics are signals, not declarations (`REQ-B-05`). | Accepted |
| Missingness mechanisms | Do not claim definitive MAR or MNAR without support from the observed data (`REQ-H-05`). | Accepted |
| One statistical layer | Relationships, target analysis, missingness relationships, compare, and drift share one layer wherever analytically appropriate (`REQ-T-05`). | Accepted. API is [OPEN-038](DECISIONS.md#open-questions). |
| Bayesian role | Selective, lightweight, and for understanding. Not predictive optimization. Not promised for every analysis (`REQ-P-11`, [DEC-057](DECISIONS.md#dec-057)). | Accepted |
| Bayesian transparency | State method, prior, posterior, credible interval, relevant probability statements, approximation or sampling where applicable, and limitations. | Accepted |
| Meaningful thresholds | A Bayesian "meaningful effect" threshold comes from an established convention or from explicit user configuration. Pytics does not invent one. | Accepted. No convention is selected ([OPEN-008](DECISIONS.md#open-questions)). |
| Reproducibility | Same data, configuration, version, and seed should agree where reasonably possible. Record nondeterministic metadata (`REQ-P-12`). | Accepted |
| Catalog freeze | Do not hard-code a final method catalog (`REQ-K-03`). | In force |

## Relationship direction

Status: **Accepted as direction** ([DEC-055](DECISIONS.md#dec-055)). Not a closed catalog. Exact formulas and fallbacks are [OPEN-006](DECISIONS.md#open-questions).

### Numeric × numeric

Standard analysis uses Spearman as a monotonic or rank perspective and Pearson as a linear perspective where applicable. Include uncertainty where methodologically appropriate, plus sample size and missing-pair information. Pearson and Spearman are not the same phenomenon.

Deep analysis may add Kendall, bootstrap confidence intervals, permutation or resampling inference, and further robust or nonlinear diagnostics where justified.

### Numeric × binary

Include per-group sample sizes, group descriptive statistics, observed group differences, an appropriate standardized effect, uncertainty, and frequentist evidence.

Welch-family inference is currently preferred over blindly assuming equal variances. Robust or rank-based evidence may complement it. The effect-size formula and the fallback are [OPEN-006](DECISIONS.md#open-questions).

### Numeric × categorical

For more than two groups, prioritize group descriptive statistics, an overall relationship or effect, and an appropriate omnibus inference. Do not automatically emit every pairwise comparison.

Post-hoc pairwise analysis belongs primarily in deeper analysis and uses appropriate multiple-testing control. ANOVA, Welch, or rank-based selection is [OPEN-006](DECISIONS.md#open-questions).

### Binary × binary

Do not reduce the analysis to chi-square significance. Relevant concepts: contingency counts, observed proportions, absolute proportion or risk difference, relative measures where meaningful, association strength, uncertainty, and frequentist evidence.

This pair is a strong candidate for lightweight Bayesian analysis ([DEC-057](DECISIONS.md#dec-057)). Default measures are [OPEN-006](DECISIONS.md#open-questions).

### Categorical × categorical

Include contingency information, observed proportions, Cramér's V or another appropriate association-strength measure, and appropriate inferential evidence.

Sparse or small tables may require exact or resampling alternatives. Protect extreme high-cardinality pairs from meaningless or computationally explosive analysis. Identifiers are excluded by default (`REQ-G-03`).

### Datetime

Do not convert timestamps to integers and pass them through ordinary correlation.

Datetime × numeric focuses on meaningful temporal structure when justified, such as trend, change over time, temporal association, and periodic or seasonal structure where justified.

Datetime × categorical may examine change in category distribution or temporal patterns.

A datetime column by itself does not establish a time-series context (`REQ-E-03`). [DEC-031](DECISIONS.md#dec-031) still withholds trend, seasonality, and autocorrelation as a default pass on every datetime column. The scope of those deep diagnostics is [OPEN-020](DECISIONS.md#open-questions).

### Ordinal

Ordinal relationship methods apply only where [DEC-052](DECISIONS.md#dec-052) accepts ordinal semantics. No ordinal method is selected.

### Not given a direction

Text and timedelta relationship methods are not specified. Omission is not a rejection. They remain inside [OPEN-006](DECISIONS.md#open-questions).

## Modes

`quick`, `standard`, and `deep` are accepted names. Standard is the intended default ([DEC-058](DECISIONS.md#dec-058), `REQ-P-16`).

| Mode | Current direction | Status |
| --- | --- | --- |
| Quick | Inexpensive descriptive profiling, cheap associations, and important data-quality checks. | Direction, not a closed list |
| Standard | Likely: descriptive statistics, effect sizes, primary relationships, confidence intervals where appropriate, appropriate frequentist inference, multiple-testing correction, missing analysis, duplicate analysis, univariate outliers, and controlled multivariate anomaly analysis. | Intended default. Not a closed list. Correction still depends on [OPEN-007](DECISIONS.md#open-questions). |
| Deep | May add further bootstrap or resampling, further robust alternatives, broader Bayesian inference, post-hoc analysis, deeper temporal analysis, more expensive anomaly analysis, and deeper drift inference. | Direction, not a closed list |

Exact contents and thresholds are [OPEN-010](DECISIONS.md#open-questions).

## Bayesian work

No analysis is pre-assigned a Bayesian counterpart except the candidate status of binary × binary. Lightweight analytical or numerical methods are preferred. NumPy and SciPy are the current calculation direction, not a pin. PyMC is not intended as a core dependency at present.

Useful outputs may include a posterior effect estimate, a credible interval, a directional probability such as `P(A > B)`, and the probability that an effect exceeds a meaningful threshold.

The catalog remains [OPEN-008](DECISIONS.md#open-questions).

## Method registry

The concept is accepted ([DEC-038](DECISIONS.md#dec-038)), including as a possible source for the Methods section (`REQ-IA-14`).

Do not implement it. Schema and API are [OPEN-039](DECISIONS.md#open-questions).

## Target-model statistics

Target associations reuse this relationship layer (`REQ-T-05`, [DEC-059](DECISIONS.md#dec-059)).

One lightweight untuned diagnostic model is allowed, for understanding (`REQ-L-04`). Validation is holdout or cross-validation, not training-set evaluation (`REQ-L-05`). Held-out permutation importance is the primary importance direction. Report spread across permutations where applicable. Warn that correlated predictors can share or obscure that importance. Do not present it as causal importance (`REQ-L-07`).

The estimator family is not selected ([OPEN-013](DECISIONS.md#open-questions)).
