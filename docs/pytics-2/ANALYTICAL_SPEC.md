# Analytical specification

Status of areas A–N: **Accepted** as parts of the Pytics 2.0 analytical design ([DEC-014](DECISIONS.md#dec-014)).

This file is the analytical contract. It does not freeze algorithms, thresholds, or library choices.

Recording rules from [README.md](README.md#recording-convention) apply. In particular, "such as" and "may" are not rewritten into "always emit every named statistic". Confirming whether each named concept is mandatory output is [OPEN-001](DECISIONS.md#open-questions).

Cross-cutting product rules (`REQ-P-*`) are in [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md).

## Semantic model

Physical pandas dtype is not the semantic type ([DEC-041](DECISIONS.md#dec-041)).

Pytics observes ([DEC-045](DECISIONS.md#dec-045)). It does not silently clean, repair, coerce, or mutate the original DataFrame. It may detect numeric-like values, missing-like literals, and possible interpretations. It preserves the distinction between source representation and analytical interpretation. A mostly numeric string column containing `"?"` must not be rewritten into clean numeric data. Analysis produces structured analytical truth first. Rendering comes later ([DEC-025](DECISIONS.md#dec-025)).

Pytics distinguishes physical dtype, observed characteristics, and semantic interpretation. Physical dtype is evidence. The original physical dtype remains inspectable. Physical metadata, basic observations, and pattern observations remain distinguishable.

### Conceptual pipeline

The accepted conceptual pipeline is [DEC-064](DECISIONS.md#dec-064). It refines the earlier stage list in [DEC-041](DECISIONS.md#dec-041). It is an analytical description, not a package, module, class, or function layout, and it does not resolve [OPEN-045](DECISIONS.md#open-questions). The labels are not class names.

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

An interpretation must be able to retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source. Sources are: inferred; directly supported by physical dtype; explicitly configured by the user. Exact object names are [OPEN-004](DECISIONS.md#open-questions). The implemented interpretation has one source. `InferenceSource.USER_CONFIGURED` exists on that value. Keeping an inferred reading beside a separate effective reading is accepted direction ([DEC-075](DECISIONS.md#dec-075)) and is not implemented. Relevance of a competing reading is materiality ([DEC-067](DECISIONS.md#dec-067)).

### Observations and candidate assessments

Observations are objective facts about the source data or the procedure used to inspect it ([DEC-065](DECISIONS.md#dec-065)). Examples, not a closed catalog: physical dtype, missing count, unique count, cardinality, an observed small value set, frequency information, string lengths, pattern matches, monotonicity, sequence regularity, ordered categorical metadata, column name metadata, and sampling provenance. Observations do not decide semantic meaning by themselves.

Candidate assessments interpret observations in support of possible semantic readings. The architecture must eventually distinguish supporting evidence, contradicting evidence, and evidence that does not bear on the candidate. This specification does not create an evidence-role enum and does not freeze an evidence object shape. The implemented evidence value is one statement. That value is thinner than the future distinction.

Absence of support is not contradiction. No UUID pattern means Identifier did not receive UUID-pattern support. It does not mean Identifier has been contradicted. No repetition does not by itself contradict Categorical. No prose structure does not by itself contradict Text. A contradicting observation is positive evidence that conflicts with a specific claim of a candidate. Do not count every absent signal against a candidate.

### Universal column evidence

`BasicColumnEvidence` is the universal typed evidence family ([DEC-077](DECISIONS.md#dec-077)). Analytical observations use typed families, composed as needed. The core model is not a generic observation property bag. Frequency evidence is the one further family authorized so far ([DEC-078](DECISIONS.md#dec-078)). This specification does not authorize another family, and it does not establish inheritance among families.

The stored primary observations are exact, full-column, and unsampled:

- `n_total`
- `n_missing`
- `n_non_missing`
- `n_unique_non_missing`

Each count is retained even when another count is mathematically related. There is no sampling for these four values. Missing-like literals such as `""`, `"NA"`, `"N/A"`, `"null"`, and `"?"` remain observed values unless pandas already represents them as missing.

Derived convenience facts are read-only computations from those counts. They are not a second stored source of truth.

- `missing_ratio` is `n_missing / n_total` when `n_total > 0`, and `None` when `n_total == 0`.
- `unique_ratio_non_missing` is `n_unique_non_missing / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`.
- `has_missing` is `n_missing > 0`.
- `is_empty` is `n_non_missing == 0`.
- `is_constant` is `n_non_missing > 0` and `n_unique_non_missing == 1`.

An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. There is no `unique_ratio` alias. `unique_ratio_non_missing` decides the denominator of this property only. It is not an Identifier threshold ([OPEN-044](DECISIONS.md#open-questions)).

`is_empty` covers a zero-length Series and an all-missing Series. Both are empty, not constant. One repeated non-missing value is constant, including when missing observations are also present, and including a one-row non-missing Series.

These four counts do not carry a procedure-provenance object. They are definitionally exact. A reusable provenance model waits for a second procedure ([DEC-076](DECISIONS.md#dec-076)). Sample sizes remain [OPEN-010](DECISIONS.md#open-questions).

### Frequency evidence

`FrequencyEvidence` is a typed observation family composed with `BasicColumnEvidence` ([DEC-078](DECISIONS.md#dec-078)). It is not a subclass of that universal family. The frequency population is non-missing observations. Missing values are not frequency keys. Unobserved categorical levels, which a count table can list at zero, are not frequency keys either. `n_missing`, `missing_ratio`, and `has_missing` stay on the universal family.

Stored frequency observations are `most_frequent_count`, `singleton_count`, and a bounded exact set of distinct non-missing values. Ratios are read-only:

- `most_frequent_ratio` is `most_frequent_count / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`.
- `singleton_ratio` is `singleton_count / n_unique_non_missing` when `n_unique_non_missing > 0`, and `None` when `n_unique_non_missing == 0`. The denominator is the number of distinct non-missing values, not the number of rows.

An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. There is no second singleton ratio. Neither ratio is a semantic threshold ([OPEN-044](DECISIONS.md#open-questions)).

`most_frequent_count` is `0` when there is no non-missing observation, and otherwise the largest occurrence count. `singleton_count` is `0` in that empty case, and otherwise the number of distinct non-missing values that occur once. Neither count is `None`.

When the distinct count is within the v0.1 retention limit of 32, the exact distinct non-missing values are retained, including an empty collection when that count is zero. Above 32, the exact collection is absent. The limit is a storage guard. It does not define categorical, binary, identifier, text, or high cardinality ([OPEN-018](DECISIONS.md#open-questions), [OPEN-044](DECISIONS.md#open-questions)).

These observations are exact, full-column, and unsampled. They are collected when requested. The implemented precedence chain does not collect them. They do not select a semantic type. No confidence and no evidence role are attached. The class name is not a public schema ([OPEN-004](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions)).

### Confidence

User-facing resolution confidence is High, Medium, or Low, together with concrete evidence ([DEC-042](DECISIONS.md#dec-042)). Those three words are not a displayed probability and not a candidate score.

Evidence role, evidence strength, and resolution confidence are distinct ([DEC-066](DECISIONS.md#dec-066)). Candidate Resolution v0.1 does not use an arbitrary numeric total-score, does not introduce an evidence-strength enum, and does not introduce pseudo-probabilities such as `0.87321`. [DEC-042](DECISIONS.md#dec-042) still permits an internal score, and still permits a future statistically justified numeric confidence. That permission is unused. Reconsider scoring only if concrete conflict cases show that explicit observations, evidence roles, and resolution rules are insufficient. Whether an evidence-strength enum is ever needed is [OPEN-048](DECISIONS.md#open-048).

The implemented physical rules may use High because the procedure is direct and exact. A strong heuristic or a sampled observation does not automatically imply High.

The following block shows fields an interpretation can retain. It is not a detector, not a threshold, and not an assignment of High confidence. It does not define an Identifier uniqueness threshold ([OPEN-044](DECISIONS.md#open-questions)). The denominator of `unique_ratio_non_missing` is [DEC-077](DECISIONS.md#dec-077). That property is not this illustration.

```text
Semantic type
Identifier

Evidence
- uniqueness among the observed values
- integer values follow a near-sequential pattern
- column name contains an identifier token
```

### Resolution and ambiguity

Ambiguity stays visible ([DEC-043](DECISIONS.md#dec-043), [DEC-067](DECISIONS.md#dec-067)). The current architectural direction is:

```text
selected interpretation
+ resolution confidence
+ material alternative(s)
```

A material alternative is a competing interpretation that has its own positive evidence, survives the observations without requiring coercion, and remains plausible beside the selected interpretation. Theoretical compatibility is not enough. Every possible type is not an alternative. Downstream analytical impact may explain why an alternative is worth showing. It does not define whether the alternative is material. The architecture must eventually preserve the rationale and evidence for a material alternative. The current `SemanticAlternative` value records a type, an optional subtype label, and an optional confidence. It does not record that rationale. This consolidation does not redesign that value.

The accepted illustration remains: values `1, 2, 3, 4, 5` in a column named `score` may be selected as numeric discrete with medium confidence, with ordinal categorical as the alternative, because no explicit order was supplied. That illustration does not resolve [OPEN-016](DECISIONS.md#open-questions). It does not mean that every unimplemented type is an alternative, and it does not mean that absence of order evidence by itself creates one.

Do not introduce abstention now. A future abstention state may be reconsidered if concrete cases justify it ([OPEN-047](DECISIONS.md#open-047)).

`None`, as returned by the implemented rule chain, means that chain produced no interpretation. It is control flow. It is not a semantic type. It must not be read as ambiguous, unknown, unsupported, conflicted, or abstained. `SemanticType` has no member for those words.

A column name may support an inference. It must not determine semantic type by itself.

### Empty, Constant, and implemented physical readings

Empty and Constant are semantic interpretations and dataset facts ([DEC-046](DECISIONS.md#dec-046)):

- an all-missing column is semantic interpretation Empty, and a dataset fact that the column is empty;
- a column with exactly one distinct non-missing value is semantic interpretation Constant, and a dataset fact that the column is constant.

Those dataset facts are `is_empty` and `is_constant` on the universal evidence value ([DEC-077](DECISIONS.md#dec-077)). A zero-length column is empty, not constant. Empty and Constant interpretation uses those facts.

Empty precedes Constant. In the current semantic system those two readings win over competing type readings, including the physical Boolean, Datetime, and Timedelta rules already implemented, and over a Numeric or Identifier reading of the same column. That sentence is not an exhaustive precedence law for every future semantic reading. The physical dtype remains inspectable when Empty or Constant wins. Ordered categorical metadata (`categorical_ordered`) remains inspectable in that case. Semantic interpretation and physical or source facts stay distinct. Do not duplicate the underlying computation unnecessarily.

TSK-002 through TSK-005 implement the readings below. TSK-006 adds no semantic reading. TSK-007 adds frequency observations and no semantic reading. Those slices do not implement heuristic candidate resolution, user overrides, or the separate effective interpretation. Heuristic semantic inference is not authorized.

- A non-empty, non-constant physical Boolean column is Boolean, with High confidence and physical-dtype provenance. A physical pandas Boolean is very strong direct Boolean/Binary evidence ([DEC-047](DECISIONS.md#dec-047)). That phrase does not rank physical Boolean as the strongest evidence of every kind.
- A non-empty, non-constant physical Datetime column is Datetime, with High confidence and physical-dtype provenance. A non-empty, non-constant timezone-aware Datetime column is the same semantic type, with its own physical family and its own evidence statement. Native and timezone-aware datetime dtypes are strong evidence of Datetime semantics ([DEC-050](DECISIONS.md#dec-050)). Timezone-aware storage is not a second semantic type.
- A non-empty, non-constant physical Timedelta column is Timedelta, with High confidence and physical-dtype provenance, because the procedure reads the physical dtype directly. Timedelta stays a duration ([DEC-051](DECISIONS.md#dec-051)).

High on these readings is the three-level confidence used for a direct, exact procedure. It is not a numeric score. Boolean versus Binary representation is not resolved ([OPEN-014](DECISIONS.md#open-questions)).

### Ordinal reservation

Ordinal order is not inferred from labels ([DEC-052](DECISIONS.md#dec-052)). Order may come only from explicit user configuration or from explicit source order. An ordered pandas categorical dtype, such as `pd.Categorical(..., ordered=True)`, is source evidence. Label text must never invent order. `categorical_ordered` remains on the physical dtype. A later Categorical interpretation must not erase that fact. Empty or Constant does not erase it. Ordinal is not in the minimum semantic vocabulary. When ordinal semantics are accepted, storage remains [OPEN-016](DECISIONS.md#open-questions). Do not use the optional subtype string to pretend that question is resolved. Do not add an Ordinal semantic type in order to close it.

### Overrides

Explicit per-variable semantic configuration is a first-class capability ([DEC-044](DECISIONS.md#dec-044)). The accepted direction is inferred interpretation, then an optional user override, then the effective interpretation ([DEC-075](DECISIONS.md#dec-075)). The result object, the configuration object, and the public API are not accepted ([OPEN-004](DECISIONS.md#open-questions), [OPEN-009](DECISIONS.md#open-questions)). Eligibility rules remain [OPEN-043](DECISIONS.md#open-questions).

These points are accepted architectural direction. Their exact objects remain open under those questions:

- a future override preserves the inferred interpretation rather than silently rewriting it;
- user intent normally takes precedence where the requested interpretation is meaningfully applicable;
- downstream analysis uses the effective interpretation where applicable;
- an override never erases physical or source facts;
- an override never authorizes coercion or mutation;
- a conflict must be reportable;
- removing an override conceptually restores the inferred interpretation;
- an interactive renderer must not become a second analytical engine;
- changing the semantic interpretation may require re-analysis, because eligibility can change;
- future reproducible configuration should be able to carry semantic overrides.

Effective interpretation expresses the requested or active semantic reading. Physical applicability and immutable dataset facts still determine which analyses can run without coercion. Example, not a fixture and not an error-behavior specification: a numeric Identifier overridden toward Numeric can enable Numeric analysis when the values are already physically numeric; UUID strings overridden toward Numeric cannot create valid Numeric analysis without coercion; Empty overridden toward Text cannot create textual content; a physical Boolean overridden toward Categorical may permit categorical frequency analysis without mutating values. Exact error and warning behavior is not frozen. Exact Empty or Constant override behavior is [OPEN-049](DECISIONS.md#open-049).

### Sampling and reuse

Cheap evidence uses the full column where practical. Expensive evidence, particularly string and pattern analysis on very large data, may use controlled sampling ([DEC-054](DECISIONS.md#dec-054)). Evidence should eventually preserve procedure provenance. That provenance may include whether collection was exact and full-column or sampled, the sample size, the population size, the seed, and the method ([DEC-076](DECISIONS.md#dec-076)). Those fields are not frozen. Exact versus sampled belongs to provenance. Sampling can affect resolution confidence. Sampling does not itself make an interpretation true or false. Thresholds and sample sizes are [OPEN-010](DECISIONS.md#open-questions). Exact inference cutoffs are [OPEN-044](DECISIONS.md#open-questions).

Shared observations should be collected once and reused by candidate assessments. The cost layering is architectural ([TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md), [DEC-076](DECISIONS.md#dec-076)). It is not a cache API and not a module layout.

Semantic interpretation guides eligibility ([DEC-053](DECISIONS.md#dec-053)). The examples in that decision are direction, not a closed matrix ([OPEN-043](DECISIONS.md#open-questions)). Where an override exists, eligibility follows the effective interpretation where applicable, still without coercion. Some roles cannot be resolved from one Series. That limit is specified under Identifier detection.

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

A physically numeric column that is not better interpreted as Empty, Constant, Boolean/Binary, or Identifier may be interpreted as Numeric ([DEC-049](DECISIONS.md#dec-049)). Physical numeric dtype is meaningful evidence for that reading. A numeric dtype does not need a further positive heuristic before Numeric is available merely because the storage is numeric ([DEC-069](DECISIONS.md#dec-069)). Identifier displaces that generic Numeric reading only when Identifier has positive evidence of its own. Uniqueness alone is not that evidence. When the selected reading remains uncertain, preserve a material competing interpretation and an appropriate confidence. Do not introduce abstention ([DEC-067](DECISIONS.md#dec-067), [OPEN-047](DECISIONS.md#open-047)). Subtypes may include Continuous and Discrete. Do not treat integer dtype as discrete, or float dtype as continuous, without the observed values. Subtype inference stays conservative.

Statistics in this section, including mean, skewness, kurtosis, and histogram shape, are downstream numeric analysis. The semantic engine precedes that analysis. Do not recycle those outputs as ad hoc Identifier detectors. If semantic evidence legitimately needs a descriptive numeric observation, that use has to be an explicit semantic-inference decision. This boundary does not close the identifier detector catalog ([DEC-048](DECISIONS.md#dec-048), [OPEN-044](DECISIONS.md#open-questions)).

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

Categorical means that values function as a classification vocabulary ([DEC-070](DECISIONS.md#dec-070), [DEC-049](DECISIONS.md#dec-049)). It is not a synonym for pandas `object`, and it is not a synonym for pandas `category`. Storage may be a categorical dtype, a string, an object, a numeric code, or another compatible representation. Repetition supports a categorical reading and is not required. Cardinality alone does not establish Categorical. Low cardinality alone does not establish it. High cardinality does not remove Categorical meaning. Singleton categories remain possible. Do not assume low-cardinality numeric values are category codes without sufficient evidence or explicit configuration. Charting and contingency limits, including `REQ-C-07`, do not redefine the semantic type. Arbitrary two-category label variables stay categorical rather than Boolean. How Categorical differs from Text and from Identifier is specified in section F.

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

- A physical pandas boolean is very strong direct Boolean/Binary evidence. The implemented non-empty, non-constant physical Boolean reading is specified in the semantic model. That wording does not rank physical Boolean as the strongest evidence of every kind.
- Two unique values alone do not establish Boolean meaning.
- `{0, 1}` may support a binary interpretation and is not automatically Boolean. `{0.0, 1.0}` is not accepted as that evidence ([OPEN-046](DECISIONS.md#open-046)).
- Conservative true/false recognition may support binary semantics. Conservative yes/no recognition may also be considered, more cautiously. String or token recognition never coerces or mutates the Series.
- An arbitrary two-category variable stays categorical, including as a binary category, and is not described as Boolean.
- A column name may support a binary reading and must never decide it. Do not grow a large language or domain dictionary of binary token pairs in core.

The contract allows a binary interpretation that is not necessarily Boolean. The current `SemanticType.BOOLEAN` family cannot fully express that distinction. Heuristic `{0, 1}` inference and string-token Binary inference must not be implemented until a binary-not-Boolean reading can be represented without mislabeling it ([DEC-074](DECISIONS.md#dec-074)). That hold does not resolve the representation question, and it does not add a semantic type. Whether Binary becomes a semantic type, a subtype, a semantic property, or another representation remains [OPEN-014](DECISIONS.md#open-questions).

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

Text means that values primarily function as textual content ([DEC-071](DECISIONS.md#dec-071)). Text is not defined by string dtype. Inference evidence may include length structure, word counts, whitespace, line breaks, lexical or textual structure, pattern regularity, and repetition, where this contract already allows that evidence. That evidence is for semantic inference. The diagnostics in `REQ-F-02` are downstream text profiling. Do not introduce NLP models, embeddings, language models, or language detection into core semantic inference (`REQ-F-03`, [DEC-034](DECISIONS.md#dec-034)). Generic string remains a listed role. Collapsing every generic string into Text is not accepted. Where generic string, URL-like, email-like, and path-like sit in the subtype taxonomy is [OPEN-014](DECISIONS.md#open-questions).

Structural pattern detection produces observations first ([DEC-072](DECISIONS.md#dec-072), [DEC-050](DECISIONS.md#dec-050)). The detected pattern name does not automatically become the semantic type. UUID-like, hash-like, email-like, URL-like, path-like, and datetime-like are observations or roles. UUID-like and hash-like structure are Identifier evidence and are not automatically sufficient for Identifier. Whether either pattern can ever be sufficient alone is [OPEN-044](DECISIONS.md#open-questions). Email-like, URL-like, and path-like structure do not by themselves select Identifier. Datetime-like string detection does not change the physical dtype. No Series is rewritten.

Cardinality alone never distinguishes Categorical from Text. Repetition supports Categorical and is not sufficient for it. Long, multi-word, or prose-like textual structure may support Text. High uniqueness alone does not imply Text. High cardinality alone does not imply Text. A pandas categorical dtype is physical and source evidence. It does not automatically override contradictory semantic evidence. High-cardinality Categorical remains possible. Text inference does not require NLP. No length, word-count, repetition, or cardinality threshold is chosen here.

Uniqueness alone does not distinguish Text from Identifier. Stable structural regularity may support Identifier. Prose-like structure supports Text and may contradict a specific code-like Identifier claim. It does not make every Identifier role impossible. Fixed width is evidence only. Repeated identifier-like strings may remain Identifier. All-unique free text may remain Text. No pattern-agreement threshold is chosen here.

Repeated entity keys can remain Identifier. Repeated labels can be Categorical, so repetition alone cannot separate the two. Identifier needs evidence of an identity, key, or code role, not merely high cardinality. Categorical needs evidence of a label or classification role, not merely low cardinality. The same code can have different semantic roles in different datasets. The column-local limit on seeing that difference is specified in section G. No threshold in this section is a detection rule.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-F-01 | Distinguish the string roles listed above. | Accepted |
| REQ-F-02 | Text diagnostics covering count, missing, distinct, empty strings, whitespace-only values, length statistics and distribution, word counts, leading or trailing whitespace, line breaks, Unicode or non-ASCII characteristics, pattern consistency, and duplicate text. | Accepted |
| REQ-F-03 | Pytics core must not become a full NLP platform. | Out of scope. The exclusion is Accepted. |

Common tokens, "potentially" and "where appropriate", are **Proposed / not yet finalized** ([OPEN-019](DECISIONS.md#open-questions)).

## G — Identifier detection

Identifier is a first-class semantic concept (`REQ-S-01`). It is a semantic type, not a relational candidate-key definition ([DEC-068](DECISIONS.md#dec-068)).

Admissible evidence, not a closed detector ([DEC-048](DECISIONS.md#dec-048)): uniqueness ratio, duplicate count, missing count, UUID or GUID-like structure, hash-like structure, sequential integer patterns, fixed-width codes, alphanumeric code patterns, prefixes and suffixes, monotonic or sequential behavior, and column name as a weak supporting signal.

`unique_ratio == 1` alone is not sufficient. Perfect uniqueness is not a definitional requirement. Zero missingness is not sufficient and is not a definitional requirement. Their weight remains future evidence and thresholds. The universal property `unique_ratio_non_missing` uses the non-missing count as its denominator ([DEC-077](DECISIONS.md#dec-077)). That does not decide an Identifier threshold, and it does not create a `unique_ratio` alias. Duplicates do not automatically disqualify Identifier. Duplicate identifiers may later be a quality finding under section I. A column name may support Identifier and must never decide it alone. Positive Identifier evidence is required before Identifier displaces a generic Numeric reading ([DEC-069](DECISIONS.md#dec-069)). UUID-like and hash-like structure are stronger Identifier evidence than generic uniqueness and are not currently sufficient alone ([DEC-072](DECISIONS.md#dec-072)). Thresholds, checklists, and that sufficiency question are [OPEN-044](DECISIONS.md#open-questions).

Some semantic roles cannot be reliably resolved from one Series ([DEC-073](DECISIONS.md#dec-073)). Column-local observations may make more than one interpretation plausible. They cannot always observe dataset role. Example, not a fixture and not a detection rule: `customer_id` on transaction rows versus `customer_id` as an entity key; a country code as an attribute versus a country code as the entity; an SKU on order lines versus an SKU in a product master; an email as a contact attribute versus an email as an account identity.

The architecture leaves room for future dataset-context evidence beside column-local evidence. This specification does not adopt cross-column inference, functional-dependency discovery, candidate-key mining, or schema-graph inference. User configuration remains the accepted current way to supply context the column cannot justify ([DEC-044](DECISIONS.md#dec-044)).

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
