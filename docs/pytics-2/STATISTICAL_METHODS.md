# Statistical methods

Status: rules and directions below that are marked Accepted are binding. The method catalog is not.

Do not implement a catalog, a method registry, or a Bayesian stack from this file. `REQ-K-03` remains in force. [DEC-055](DECISIONS.md#dec-055) does not retire it.

Numeric summaries in this file are downstream analysis. They are not semantic-inference detectors ([DEC-069](DECISIONS.md#dec-069)). Numeric-structure evidence counts finite values, signs, infinities, and integer-like values for later candidate assessment ([DEC-079](DECISIONS.md#dec-079)). It is not these summaries. String-structure evidence counts empty strings, whitespace, character classes, and length bounds for later candidate assessment ([DEC-080](DECISIONS.md#dec-080)). It is not text profiling and not a semantic reading. Pattern evidence counts full-value UUID, IPv4, IPv6, and fixed-width hexadecimal syntax for later candidate assessment ([DEC-081](DECISIONS.md#dec-081)). It is not an Identifier reading and not a semantic type. An Identifier candidate assessment may use a full-population UUID or same-width hexadecimal count as support for that candidate ([DEC-082](DECISIONS.md#dec-082)). That support is not a selected semantic type and not a downstream statistic. A Numeric candidate may be supported by non-empty, non-constant physical integer or floating storage ([DEC-083](DECISIONS.md#dec-083)). A Categorical candidate may be supported by non-empty, non-constant physical categorical storage. Current string-structure observations do not support a Text candidate. None of those assessments is a selected semantic type or a downstream statistic. String-content evidence counts alphanumeric token runs, the zero-token, one-token, and multiple-token partition, total characters, and aggregate token-vocabulary counts for later candidate assessment ([DEC-084](DECISIONS.md#dec-084)). It does not retain raw text. It is not a Text reading, and it does not support a Text or ordinary-string Categorical candidate.

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
| Missingness mechanisms | Do not claim definitive MAR or MNAR without support from the observed data (`REQ-H-05`). TSK-022 records observed missingness structure and does not add a mechanism test ([DEC-093](DECISIONS.md#dec-093)). | Accepted |
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

TSK-024 implements that standard pair for selected Numeric × selected Numeric only ([DEC-095](DECISIONS.md#dec-095)). Spearman is the primary descriptive association. Pearson is complementary. Both may exist together. The Pearson uncertainty in that slice is the classical Fisher z interval at 95%, without a bias correction, when `n >= 4` and the estimate is strictly inside `(-1, 1)`. Spearman has no interval there. The p-value is the raw two-sided SciPy p-value when `n >= 3`. Multiple-testing adjustment is not applied. This does not close the catalog, and it does not add Kendall, bootstrap, or a normality gate. TSK-025 does not change those rules ([DEC-096](DECISIONS.md#dec-096)). The correlation image remains float64. Integers that vary in the source and collapse in that image still make the correlation unavailable. A more robust Numeric sample standard deviation does not make that correlation exact.

Deep analysis may add Kendall, bootstrap confidence intervals, permutation or resampling inference, and further robust or nonlinear diagnostics where justified.

### Numeric × binary

Include per-group sample sizes, group descriptive statistics, observed group differences, an appropriate standardized effect, uncertainty, and frequentist evidence.

Welch-family inference is currently preferred over blindly assuming equal variances. Robust or rank-based evidence may complement it. The effect-size formula and the fallback are [OPEN-006](DECISIONS.md#open-questions).

TSK-029 implements that foundation for selected Numeric × selected Boolean only ([DEC-100](DECISIONS.md#dec-100)). The population is a finite Numeric value paired with a non-missing Boolean value. Every signed component is the True group minus the False group, whichever physical column is Boolean. That orientation is not causal. Each observed group keeps a Numeric descriptive summary with the same definitions as a Numeric column. An absent level is an unavailable group, not a zero-size group. The raw effect is the mean difference in Numeric units. Each group mean is its exact minimum plus the float64 mean of its offsets from that minimum. The two means are subtracted exactly and rounded once, so a large common magnitude does not create a false zero. The standardized effect is Hedges' g: the mean difference over the pooled sample standard deviation, times the exact correction `J(v) = Γ(v/2) / (sqrt(v/2) Γ((v - 1)/2))` with `v = N - 2`. The correction makes g unbiased when both groups are normal with a common variance, a condition Pytics does not test. It is not the `1 - 3/(4v - 1)` approximation. Below `v = 2` no unbiased correction exists, so g is not reported. Zero pooled variation leaves it unavailable: undefined when every paired value is equal, and unbounded when the group means differ. The pooled scale is a descriptive convention. It is not the Welch standard error. The interval is the 95% Welch–Satterthwaite interval for the mean difference, `difference ± t(0.975, df) * SE`, with the critical value from `scipy.stats.t.ppf`. The test is Welch's two-sample t-test: `t = difference / SE` and the raw two-sided p-value `2 * scipy.stats.t.sf(abs(t), df)`. That matches `scipy.stats.ttest_ind(true, false, equal_var=False)` on the same moments. The null hypothesis is equal population means. Each group needs two observations for its variance. Two constant groups leave the test and the interval unavailable. An infinite t, a p-value of zero, and a zero-width interval are not stored. No normality or variance test selects the method. Student's pooled t-test, Mann–Whitney U, Brunner–Munzel, permutation tests, Cohen's d, Glass's delta, the median difference as a component, and an interval for Hedges' g were evaluated and not retained. Robust or rank-based complements remain [OPEN-006](DECISIONS.md#open-questions), possibly for deep analysis. Multiple-testing adjustment is not applied. Numeric `{0, 1}` and `{0.0, 1.0}` stay Numeric. A binary reading that is not selected Boolean has no method here.

### Numeric × categorical

For more than two groups, prioritize group descriptive statistics, an overall relationship or effect, and an appropriate omnibus inference. Do not automatically emit every pairwise comparison.

Post-hoc pairwise analysis belongs primarily in deeper analysis and uses appropriate multiple-testing control.

TSK-026 implements the foundation for selected Numeric × selected Categorical ([DEC-097](DECISIONS.md#dec-097)). The population is finite Numeric values paired with a non-missing category. Only observed groups are retained. Each group uses the Numeric descriptive definitions: sample standard deviation with `ddof=1`, and Hyndman-Fan type 7 quartiles. The overall effect is eta squared, `SS_between / SS_total`. It is the proportion of observed numeric variation associated with between-group differences. It is not a causal share and it has no strength label. The omnibus test is classical one-way ANOVA, `scipy.stats.f_oneway` with no keyword arguments. The null hypothesis is equal group population means. The p-value is the raw upper tail of `F(k - 1, N - k)` when the F ratio is finite. When within-group variation is zero and between-group variation is positive, eta squared may be `1.0` and classical ANOVA inference is unavailable: the F statistic and the p-value are both absent. That case is not stored as an infinite F or as a p-value of `0.0`. Welch's ANOVA is not the default because `equal_var=False` requires SciPy 1.16 and the declared floor is 1.7.0. Kruskal–Wallis is not selected by a normality gate and is not calculated here. Ordered categorical metadata is not scored. Two groups stay on this ANOVA. Post-hoc tests are not calculated. The p-value is not adjusted. Welch, Kruskal–Wallis, omega squared, epsilon squared, and post-hoc selection remain [OPEN-006](DECISIONS.md#open-questions).

TSK-027 does not change those formulas ([DEC-098](DECISIONS.md#dec-098)). Dataset-level relationship metadata no longer names Spearman, the pairwise-finite population, the float64 correlation image, or a 95% confidence level for every pair. Spearman and Pearson stay components of a Numeric × Numeric record. The Pearson interval keeps its own 95% level. Eta squared and one-way ANOVA stay separate components of a Numeric × Categorical record. That record has no confidence interval. Adjustment stays on each frequentist result and is still not applied.

### Boolean × Boolean

Do not reduce the analysis to a p-value. The foundation keeps the observed 2×2 counts, the conditional outcome-True probabilities, an absolute directional effect, a relative directional effect, a signed symmetric association, and one inferential result.

TSK-028 implements that foundation for selected Boolean × selected Boolean only ([DEC-099](DECISIONS.md#dec-099)). The population is pairwise non-missing Boolean values. The conditioning variable is the left physical column and the outcome variable is the right physical column. That orientation is for conditional probabilities. It is not a cause. The absolute effect is the probability difference, `P(outcome True | conditioning True) - P(outcome True | conditioning False)`, on `[-1, 1]` when both conditioning levels are observed. The relative effect is the probability ratio of those same probabilities. An exact infinite ratio is unavailable, reason `MATHEMATICALLY_UNBOUNDED`. An exact `0/0` ratio is unavailable, reason `UNDEFINED_RATIO`. No continuity correction is added. Phi is the signed symmetric association under False = 0 and True = 1. It is unchanged when the two variables swap sides. It is unavailable when either paired margin is constant. The inferential result is `scipy.stats.fisher_exact(table, alternative="two-sided")`. The null is an odds ratio of 1 conditional on the observed margins. Only the raw p-value is stored. SciPy's odds-ratio statistic is not the Pytics effect. A constant margin does not store the library p-value of `1.0`. There is no confidence interval, no strength label, and no multiple-testing adjustment. Odds ratio, Cramér's V, Pearson chi-square, Barnard's test, and Boschloo's test were evaluated and not retained. Categorical × Categorical is not this family.

### Binary × binary

Do not reduce the analysis to chi-square significance. Relevant concepts: contingency counts, observed proportions, absolute proportion or risk difference, relative measures where meaningful, association strength, uncertainty, and frequentist evidence.

The selected-Boolean case is specified above ([DEC-099](DECISIONS.md#dec-099)). Numeric `{0, 1}`, `{0.0, 1.0}`, and Boolean-like strings are not that case. This pair remains a strong candidate for lightweight Bayesian analysis ([DEC-057](DECISIONS.md#dec-057)). A confidence interval, an odds ratio, and the measures for pairs that are not selected Boolean remain [OPEN-006](DECISIONS.md#open-questions).

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

Exact contents and thresholds are [OPEN-010](DECISIONS.md#open-questions). An internal exact duplicate-row pass now exists ([DEC-094](DECISIONS.md#dec-094)). It is full-frame and unsampled. It does not assign that pass to one mode, and it does not set mode contents. An internal Numeric × Numeric relationship pass now exists ([DEC-095](DECISIONS.md#dec-095)). It is full-frame and unsampled. It does not assign that pass to one mode, and it does not set mode contents. An internal Numeric × Categorical relationship pass now exists ([DEC-097](DECISIONS.md#dec-097)). It is full-frame and unsampled. It does not assign that pass to one mode, and it does not set mode contents. An internal Boolean × Boolean relationship pass now exists ([DEC-099](DECISIONS.md#dec-099)). It is full-frame and unsampled. It does not assign that pass to one mode, and it does not set mode contents. An internal Numeric × Boolean relationship pass now exists ([DEC-100](DECISIONS.md#dec-100)). It is full-frame and unsampled, and it keeps full group quartiles for every pair. Sorting for those quartiles is most of its measured cost. It does not assign that pass to one mode, and it does not set mode contents. Multiple-testing correction inside those passes is still not applied ([OPEN-007](DECISIONS.md#open-questions)).

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
