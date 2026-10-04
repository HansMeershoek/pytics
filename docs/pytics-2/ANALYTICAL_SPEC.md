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

An interpretation must be able to retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source. Sources are: inferred; directly supported by physical dtype; explicitly configured by the user. Exact object names are [OPEN-004](DECISIONS.md#open-questions). The implemented interpretation has one source. `InferenceSource.USER_CONFIGURED` exists on that value. Keeping an inferred reading beside a separate effective reading is accepted direction ([DEC-075](DECISIONS.md#dec-075)). The effective reading is not implemented. The internal inferred result after resolution is [DEC-086](DECISIONS.md#dec-086). One Series can reach that result through the internal column pipeline ([DEC-087](DECISIONS.md#dec-087)). A DataFrame analysis calls that same path once per physical column and retains the evidence ([DEC-088](DECISIONS.md#dec-088)). Neither is the effective interpretation, and neither is the public result. Relevance of a competing reading is materiality ([DEC-067](DECISIONS.md#dec-067)).

### Observations and candidate assessments

Observations are objective facts about the source data or the procedure used to inspect it ([DEC-065](DECISIONS.md#dec-065)). Examples, not a closed catalog: physical dtype, missing count, unique count, cardinality, an observed small value set, frequency information, string lengths, pattern matches, monotonicity, sequence regularity, ordered categorical metadata, column name metadata, and sampling provenance. Observations do not decide semantic meaning by themselves.

Candidate assessments interpret observations in support of possible semantic readings. The architecture must eventually distinguish supporting evidence, contradicting evidence, and evidence that does not bear on the candidate. `CandidateAssessment` keeps the first two as separate tuples of `SemanticEvidence` ([DEC-082](DECISIONS.md#dec-082)). Evidence that does not bear on the candidate is omitted. That split is not an evidence-role enum ([OPEN-048](DECISIONS.md#open-048)). The statement itself remains one concrete fact. A candidate assessment does not assign High, Medium, or Low, and it does not select the column's interpretation. The implemented assessors are Identifier, Numeric, Categorical, and Text ([DEC-082](DECISIONS.md#dec-082), [DEC-083](DECISIONS.md#dec-083)). None is called by the precedence chain. When that chain does not apply, the internal column pipeline calls them and then the existing resolver and inferred-result constructor ([DEC-087](DECISIONS.md#dec-087)). The assessors do not force mutual exclusivity. Current positive rules do not yet overlap. A column may also have no supported candidate. Resolution of those assessments is a separate step ([DEC-085](DECISIONS.md#dec-085)).

Absence of support is not contradiction. No UUID pattern means Identifier did not receive UUID-pattern support. It does not mean Identifier has been contradicted. No repetition does not by itself contradict Categorical. No prose structure does not by itself contradict Text. A contradicting observation is positive evidence that conflicts with a specific claim of a candidate. Do not count every absent signal against a candidate.

### Universal column evidence

`BasicColumnEvidence` is the universal typed evidence family ([DEC-077](DECISIONS.md#dec-077)). Analytical observations use typed families, composed as needed. The core model is not a generic observation property bag. Frequency evidence, numeric-structure evidence, string-structure evidence, and pattern evidence are the further families authorized so far ([DEC-078](DECISIONS.md#dec-078), [DEC-079](DECISIONS.md#dec-079), [DEC-080](DECISIONS.md#dec-080), [DEC-081](DECISIONS.md#dec-081)). Candidate assessment is not another evidence family ([DEC-082](DECISIONS.md#dec-082), [DEC-083](DECISIONS.md#dec-083)). This specification does not authorize another family, and it does not establish inheritance among families.

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

These observations are exact, full-column, and unsampled. They are collected when requested. The implemented precedence chain does not collect them. TSK-019 requests them from `analyze_series` for a non-structural physical categorical column and retains that object ([DEC-090](DECISIONS.md#dec-090)). Numeric, string, object, and structural columns still do not collect them. They do not select a semantic type. No confidence and no evidence role are attached. The class name is not a public schema ([OPEN-004](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions)).

### Numeric structure evidence

`NumericStructureEvidence` is a typed observation family composed with `BasicColumnEvidence` ([DEC-079](DECISIONS.md#dec-079)). It is not a subclass of that universal family. It applies only to a physical integer or floating dtype. Physical Boolean is excluded. Strings are not parsed into numbers. Datetime, Timedelta, and the other non-numeric families are not coerced.

The population is non-missing observations. `n_total`, `n_missing`, and `n_non_missing` stay on the universal family. Stored observations are the finite count, the finite sign counts, the two infinity counts, the integer-like and non-integer-like counts, and two monotonicity flags. Ratios are read-only:

- `finite_ratio` is `finite_count / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`.
- `positive_ratio`, `negative_ratio`, and `zero_ratio` divide those counts by `finite_count` when `finite_count > 0`, and are `None` when `finite_count == 0`.
- `integer_like_ratio` is `integer_like_count / finite_count` when `finite_count > 0`, and `None` when `finite_count == 0`.

An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. None of these ratios is a semantic threshold ([OPEN-044](DECISIONS.md#open-questions)).

Finite values and the two infinities partition the non-missing observations. Sign counts partition finite values only. `0` and `-0.0` are both zero. Infinities are not sign counts and are neither integer-like nor non-integer-like. Integer-like means a finite value equals its truncation. There is no tolerance. Integer-like counts do not decide Continuous or Discrete ([OPEN-014](DECISIONS.md#open-questions)).

Monotonicity is defined only when every non-missing value is finite. Otherwise both flags are undefined. Missing values are ignored, and the remaining values keep their original order. No non-missing values, one finite value, and a finite constant series are both non-decreasing and non-increasing. That is not Identifier evidence. A step size or regular sequence is not part of this family.

These observations are exact, full-column, and unsampled. They are collected when requested. The implemented precedence chain does not collect them. They do not select Numeric, Identifier, Boolean, or Binary. `{0.0, 1.0}` remains open as binary evidence ([OPEN-046](DECISIONS.md#open-046)). No confidence and no evidence role are attached. Mean, quantiles, and the other numeric summaries in section B are not this family. The class name is not a public schema ([OPEN-004](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions)).

### String structure evidence

`StringStructureEvidence` is a typed observation family composed with `BasicColumnEvidence` ([DEC-080](DECISIONS.md#dec-080)). It is not a subclass of that universal family. It applies to a physical string dtype, including an all-missing string column. An object column is eligible only when every non-missing value is a Python `str`. An empty or all-missing object column is not eligible. Physical categorical storage is not eligible, even when its labels are strings. Other physical families are not coerced into strings. Numpy byte-string values are not decoded.

The population is non-missing strings. Pandas missingness decides what is missing. `""`, whitespace, and literals such as `"NA"` remain ordinary strings. `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing` stay on the universal family. Stored observations are the empty-string count, the whitespace-only count, the contains-whitespace count, the alphabetic, digit, and other character counts, and the minimum and maximum lengths. Ratios are read-only:

- `empty_string_ratio`, `whitespace_only_ratio`, `contains_whitespace_ratio`, `contains_alpha_ratio`, `contains_digit_ratio`, and `contains_other_ratio` each divide the named count by `n_non_missing` when `n_non_missing > 0`, and are `None` when `n_non_missing == 0`.

An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. None of these ratios is a semantic threshold ([OPEN-044](DECISIONS.md#open-questions)).

An empty string is exactly `""`. It is not whitespace-only, and its length is 0. Whitespace-only uses Python `str.isspace`. A string contains whitespace when one of its characters does, so a whitespace-only string also contains whitespace. Alphabetic uses `str.isalpha`. Digit uses `str.isdigit`. Other means a character that is not alphabetic, not a digit, and not whitespace. Those content counts may overlap. They are not a partition of the non-missing strings. The definitions use Python's Unicode string methods. Strings are not normalized, case-folded, or stripped.

Length is `len` of the original string. `min_length` and `max_length` are `None` when there is no non-missing string. They are integers when there is at least one. An observed empty string can make `min_length` 0. That 0 is not used for the case with no observations.

These observations are exact, full-column, and unsampled. They are collected when requested. The implemented precedence chain does not collect them. They do not select Text, Categorical, Identifier, Boolean, Binary, Datetime, or Numeric. They do not count words or tokens, and they do not name patterns such as UUID, email, or URL. No confidence and no evidence role are attached. The class name is not a public schema ([OPEN-004](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions)). Word counts, pattern semantics, and the missing-like literal list remain open ([OPEN-019](DECISIONS.md#open-questions), [OPEN-014](DECISIONS.md#open-questions), [OPEN-018](DECISIONS.md#open-questions)).

### Pattern evidence

`PatternEvidence` is a typed observation family composed with `StringStructureEvidence` ([DEC-081](DECISIONS.md#dec-081)). It is not a subclass of that family or of `BasicColumnEvidence`. The supplied string-structure evidence is what establishes that the column population is string-applicable. Pattern collection does not make that decision again. It checks that the Series, the physical dtype, and the non-missing population still agree, and it rejects a value that is not a Python `str`.

The population is non-missing strings. `""`, whitespace, and literals such as `"NA"` remain ordinary strings. The original string is tested. Nothing is stripped, case-folded, Unicode-normalized, stringified, or decoded. Every pattern is a full-value match. Surrounding text does not match.

The initial catalog is UUID, IPv4, IPv6, and fixed-width ASCII hexadecimal tokens of lengths 32, 40, 64, and 128. UUID syntax is the 36-character hyphenated form or the 32-character compact form. Braces, a `urn:uuid:` prefix, and misplaced hyphens do not match, even where `uuid.UUID` would accept them. No UUID version is required. IPv4 and IPv6 use the standard-library address constructors on the entire original string. CIDR syntax does not match, and address properties are not classified. The hexadecimal alphabet is `0123456789abcdefABCDEF`. It is not the Unicode character-class definition used by string-structure evidence. Those widths are not hash-algorithm names. A `0x` prefix, whitespace, and separators do not match.

Counts may overlap. A compact UUID increments both the UUID count and the 32-character hexadecimal count. There is no best pattern. Each ratio divides the named count by `n_non_missing` when `n_non_missing` is greater than 0, and is `None` when `n_non_missing` is 0. A zero numerator with a positive denominator is `0.0`. The denominator is the full non-missing string population. An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. None of these ratios is a semantic threshold ([OPEN-044](DECISIONS.md#open-questions)).

Email, URL, path, phone, postal code, MAC address, date-like text, and the other families named in [DEC-081](DECISIONS.md#dec-081) are not recognized. These observations are exact, full-column, and unsampled. They are collected when requested. The implemented precedence chain does not collect them, and string-structure collection does not collect them either. They do not select Identifier, Text, Categorical, Datetime, or any other semantic type. A separate Identifier candidate assessment may treat a full non-missing population of UUID syntax, or of one supported hexadecimal width, as support for that candidate ([DEC-082](DECISIONS.md#dec-082)). That assessment is not a selected reading. A partial ratio is not that support. No confidence and no evidence role are attached to the pattern observation. The class name is not a public schema ([OPEN-004](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions)).

### String content evidence

`StringContentEvidence` is a typed observation family composed with `StringStructureEvidence` ([DEC-084](DECISIONS.md#dec-084)). It is not a subclass of that family or of `BasicColumnEvidence`. The supplied string-structure evidence is what establishes that the column population is string-applicable. String-content collection does not make that decision again. It checks that the Series, the physical dtype, and the non-missing population still agree, and it rejects a value that is not a Python `str`.

The population is non-missing strings. `""`, whitespace, and literals such as `"NA"` remain ordinary strings. The original string is observed. Nothing is stripped, case-folded, Unicode-normalized, stringified, or decoded. A token is a maximal contiguous run of characters for which Python `str.isalnum` is true. Punctuation and whitespace separate tokens. `"hello-world"` is two tokens. `"abc123"` is one. `"Apple"` and `"apple"` stay distinct. Accents are not rewritten. An emoji is not a token. `""` and a whitespace-only string have no token and are still observed strings.

Stored observations are the total token count, the counts of strings with zero tokens, one token, and multiple tokens, the total character count, the number of distinct tokens, the number of singleton tokens, and the occurrence count of the most frequent token. Minimum and maximum length stay on string-structure evidence. Whole-value frequency stays on frequency evidence. `"red car"` and `"blue car"` can be two distinct whole values and still repeat a token. No raw string or vocabulary is retained.

`zero_token_ratio`, `one_token_ratio`, `multiple_token_ratio`, `mean_tokens_per_non_missing`, and `mean_characters_per_non_missing` divide by `n_non_missing` when that count is greater than 0, and are `None` when it is 0. `token_singleton_ratio` divides singleton tokens by distinct tokens. `most_frequent_token_ratio` divides the most frequent token's occurrences by all token occurrences. An undefined ratio or mean is `None`. A zero numerator with a positive denominator is `0.0`. None of these ratios is a semantic threshold ([OPEN-044](DECISIONS.md#open-questions)).

These observations are exact, full-column, and unsampled. They are collected when requested. The implemented precedence chain does not collect them, and string-structure collection does not collect them either. They do not select Text, Categorical, Identifier, or any other semantic type. One token in every string does not support Categorical or Text. Several tokens in a string do not support Text. Token repetition does not support Categorical. No candidate rule was added from these facts. The class name is not a public schema ([OPEN-004](DECISIONS.md#open-questions), [OPEN-045](DECISIONS.md#open-questions)). Downstream common-token diagnostics and trimmed mean remain [OPEN-019](DECISIONS.md#open-questions).

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

Resolution consumes a structural interpretation and candidate assessments that were already produced. It does not collect observations and it does not call the candidate assessors ([DEC-085](DECISIONS.md#dec-085)). Resolution status is not a semantic type. `SemanticType` has no unknown, ambiguous, or unresolved member.

`RESOLVED` means one justified reading was selected. A supplied Empty, Constant, Boolean, Datetime, or Timedelta interpretation resolves to that reading. Candidate assessments do not replace it. The confidence already on that interpretation is kept. With no structural reading, exactly one `SUPPORTED` candidate resolves to that semantic type. That selection does not construct a `SemanticInterpretation`. The interpretation requires a confidence, and a candidate assessment does not carry a justified High, Medium, or Low value. The inferred result supplies the observed physical dtype separately and still does not construct that interpretation ([DEC-086](DECISIONS.md#dec-086)).

`INSUFFICIENT_EVIDENCE` means there is no structural reading and no supported candidate. An empty candidate collection is the same outcome. There is no fallback semantic type. This is abstention at the resolution layer. It is distinct from `None`.

`AMBIGUOUS` means more than one candidate is `SUPPORTED` and no reviewed rule selects between them. The result does not select a semantic type. Input order, enum order, and the number of supporting statements are not used. A `CONTRADICTED` candidate is not selected and does not block a different supported candidate. Two assessments for the same semantic type are rejected rather than merged.

The inferred result carries the observed physical dtype and the resolution already produced ([DEC-086](DECISIONS.md#dec-086)). It does not collect observations, assess candidates, or resolve them again. It does not add a second status. The selected type, when resolution has one, stays on the resolution. A structural resolution keeps that `SemanticInterpretation` object, including its confidence and source. The supplied physical dtype must match the interpretation. A candidate-derived `RESOLVED` result keeps the selected semantic type and has no `SemanticInterpretation`, because current candidate rules do not justify High, Medium, or Low. A dataset overview counts that selected type. It does not require the interpretation ([DEC-089](DECISIONS.md#dec-089)). `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` are complete inferred states. Each has a physical dtype, no interpretation, and no selected type.

The earlier direction remains for a later case in which one reading is selected while another plausible reading is retained ([DEC-043](DECISIONS.md#dec-043), [DEC-067](DECISIONS.md#dec-067)). It is not how unresolved ambiguity is represented:

```text
selected interpretation
+ resolution confidence
+ material alternative(s)
```

A material alternative is a competing interpretation that has its own positive evidence, survives the observations without requiring coercion, and remains plausible beside the selected interpretation. Theoretical compatibility is not enough. Every possible type is not an alternative. An unsupported candidate is not a material alternative. Downstream analytical impact may explain why an alternative is worth showing. It does not define whether the alternative is material. The architecture must eventually preserve the rationale and evidence for a material alternative. The current `SemanticAlternative` value records a type, an optional subtype label, and an optional confidence. It does not record that rationale. Resolution does not fill it. The inferred result does not fill it either.

The accepted illustration remains: values `1, 2, 3, 4, 5` in a column named `score` may be selected as numeric discrete with medium confidence, with ordinal categorical as the alternative, because no explicit order was supplied. That illustration does not resolve [OPEN-016](DECISIONS.md#open-questions). It does not mean that every unimplemented type is an alternative, and it does not mean that absence of order evidence by itself creates one. It is not a rule the resolver applies.

`None`, as returned by `interpret_series_precedence`, means that chain produced no interpretation. The chain does not call the resolver. `None` is control flow. It is not a semantic type, and it is not `INSUFFICIENT_EVIDENCE` or `AMBIGUOUS`.

The inferred result now represents abstention and ambiguity without an interpretation ([DEC-086](DECISIONS.md#dec-086), [OPEN-047](DECISIONS.md#open-047)). Candidate-derived confidence, material alternatives on a selected reading, and the public result representation remain open. User overrides and downstream eligibility are not part of this result ([OPEN-009](DECISIONS.md#open-questions), [OPEN-043](DECISIONS.md#open-questions), [OPEN-049](DECISIONS.md#open-049)).

A column name may support an inference. It must not determine semantic type by itself.

### Empty, Constant, and implemented physical readings

Empty and Constant are semantic interpretations and dataset facts ([DEC-046](DECISIONS.md#dec-046)):

- an all-missing column is semantic interpretation Empty, and a dataset fact that the column is empty;
- a column with exactly one distinct non-missing value is semantic interpretation Constant, and a dataset fact that the column is constant.

Those dataset facts are `is_empty` and `is_constant` on the universal evidence value ([DEC-077](DECISIONS.md#dec-077)). A zero-length column is empty, not constant. Empty and Constant interpretation uses those facts.

Empty precedes Constant. In the current semantic system those two readings win over competing type readings, including the physical Boolean, Datetime, and Timedelta rules already implemented, and over a Numeric or Identifier reading of the same column. That sentence is not an exhaustive precedence law for every future semantic reading. The physical dtype remains inspectable when Empty or Constant wins. Ordered categorical metadata (`categorical_ordered`) remains inspectable in that case. Semantic interpretation and physical or source facts stay distinct. Do not duplicate the underlying computation unnecessarily.

TSK-002 through TSK-005 implement the readings below. TSK-006 adds no semantic reading. TSK-007 adds frequency observations and no semantic reading. TSK-008 adds numeric-structure observations and no semantic reading. TSK-009 adds string-structure observations and no semantic reading. TSK-010 adds pattern observations and no semantic reading. TSK-011 assesses an Identifier candidate and does not select it. TSK-012 assesses Numeric, Categorical, and Text candidates and does not select them. Those slices do not implement candidate resolution, user overrides, or the separate effective interpretation. TSK-014 resolves already produced facts beside that chain. TSK-015 records the inferred state from an observed physical dtype and that resolution. Neither enters the precedence chain. Selecting a heuristic semantic reading is not authorized.

- A non-empty, non-constant physical Boolean column is Boolean, with High confidence and physical-dtype provenance. A physical pandas Boolean is very strong direct Boolean/Binary evidence ([DEC-047](DECISIONS.md#dec-047)). That phrase does not rank physical Boolean as the strongest evidence of every kind.
- A non-empty, non-constant physical Datetime column is Datetime, with High confidence and physical-dtype provenance. A non-empty, non-constant timezone-aware Datetime column is the same semantic type, with its own physical family and its own evidence statement. Native and timezone-aware datetime dtypes are strong evidence of Datetime semantics ([DEC-050](DECISIONS.md#dec-050)). Timezone-aware storage is not a second semantic type.
- A non-empty, non-constant physical Timedelta column is Timedelta, with High confidence and physical-dtype provenance, because the procedure reads the physical dtype directly. Timedelta stays a duration ([DEC-051](DECISIONS.md#dec-051)).

High on these readings is the three-level confidence used for a direct, exact procedure. It is not a numeric score. Boolean versus Binary representation is not resolved ([OPEN-014](DECISIONS.md#open-questions)).

### Ordinal reservation

Ordinal order is not inferred from labels ([DEC-052](DECISIONS.md#dec-052)). Order may come only from explicit user configuration or from explicit source order. An ordered pandas categorical dtype, such as `pd.Categorical(..., ordered=True)`, is source evidence. A Categorical candidate for that dtype does not add an Ordinal semantic type ([DEC-083](DECISIONS.md#dec-083)). Label text must never invent order. `categorical_ordered` remains on the physical dtype. A later Categorical interpretation must not erase that fact. Empty or Constant does not erase it. Ordinal is not in the minimum semantic vocabulary. When ordinal semantics are accepted, storage remains [OPEN-016](DECISIONS.md#open-questions). Do not use the optional subtype string to pretend that question is resolved. Do not add an Ordinal semantic type in order to close it.

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

Cheap evidence uses the full column where practical. Expensive evidence, particularly string and pattern analysis on very large data, may use controlled sampling ([DEC-054](DECISIONS.md#dec-054)). The implemented pattern collector is exact, full-column, and unsampled ([DEC-081](DECISIONS.md#dec-081)). That choice does not withdraw the permission to sample a later expensive pattern procedure, and it does not set mode sample sizes. Evidence should eventually preserve procedure provenance. That provenance may include whether collection was exact and full-column or sampled, the sample size, the population size, the seed, and the method ([DEC-076](DECISIONS.md#dec-076)). Those fields are not frozen. Exact versus sampled belongs to provenance. Sampling can affect resolution confidence. Sampling does not itself make an interpretation true or false. Thresholds and sample sizes are [OPEN-010](DECISIONS.md#open-questions). Exact inference cutoffs are [OPEN-044](DECISIONS.md#open-questions).

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

TSK-017 stores `n_rows`, `n_columns`, and `n_cells` on an internal dataset analysis, with missing-cell totals derived from retained basic column evidence ([DEC-088](DECISIONS.md#dec-088)). TSK-018 builds an internal dataset overview from that analysis and does not scan the DataFrame again ([DEC-089](DECISIONS.md#dec-089)). The overview copies those three counts and the missing-cell totals. Cell completeness is the non-missing share of cells, and it is undefined when there are no cells. It is not a complete-row ratio. Resolved columns are counted by the semantic type resolution selected, including a candidate-derived selection that has no confidence-bearing interpretation. Insufficient evidence and ambiguity stay separate and are not semantic types. Semantic-resolution coverage is resolved columns divided by columns, and it is undefined when there are no columns. Empty, Constant, and Identifier columns are the columns with that selected type. The overview keeps position and the original label. Memory usage, duplicate rows, physical dtype composition, near-constant columns, high-cardinality columns, and a rendered overview are not that slice. There is no composite quality score. TSK-022 defines complete and incomplete rows on the Missing summary ([DEC-093](DECISIONS.md#dec-093)). Those row facts are not copied onto this overview. Cell completeness here stays the non-missing share of cells. TSK-023 copies `n_unique_rows` and `n_excess_duplicate_rows` from the retained duplicate analysis ([DEC-094](DECISIONS.md#dec-094)). Duplicate groups stay off this overview. Those counts are not a quality score.

## B — Numeric analysis

Statistically rich numeric profiling, where meaningful.

A physically numeric column that is not better interpreted as Empty, Constant, Boolean/Binary, or Identifier may be interpreted as Numeric ([DEC-049](DECISIONS.md#dec-049)). Physical numeric dtype is meaningful evidence for that reading. A numeric dtype does not need a further positive heuristic before Numeric is available merely because the storage is numeric ([DEC-069](DECISIONS.md#dec-069)). Identifier displaces that generic Numeric reading only when Identifier has positive evidence of its own. Uniqueness alone is not that evidence. When the selected reading remains uncertain, the direction is to preserve a material competing interpretation and an appropriate confidence ([DEC-067](DECISIONS.md#dec-067)). The resolution foundation does not yet apply Identifier-over-Numeric displacement and does not assign that confidence. Two supported candidates stay ambiguous. No supported candidate is insufficient evidence rather than a fallback Numeric reading ([DEC-085](DECISIONS.md#dec-085), [OPEN-047](DECISIONS.md#open-047)). Subtypes may include Continuous and Discrete. Do not treat integer dtype as discrete, or float dtype as continuous, without the observed values. Subtype inference stays conservative.

Statistics in this section, including mean, skewness, kurtosis, and histogram shape, are downstream numeric analysis. The semantic engine precedes that analysis. Do not recycle those outputs as ad hoc Identifier detectors. If semantic evidence legitimately needs a descriptive numeric observation, that use has to be an explicit semantic-inference decision. This boundary does not close the identifier detector catalog ([DEC-048](DECISIONS.md#dec-048), [OPEN-044](DECISIONS.md#open-questions)).

Numeric-structure evidence is a separate observation family ([DEC-079](DECISIONS.md#dec-079)). It counts finite values, signs, infinities, and integer-like values, and it records monotonicity when every non-missing value is finite. It does not compute the summaries in this section, and it does not select a Numeric subtype.

A Numeric variable detail copies those structural counts when the selected semantic type is Numeric ([DEC-090](DECISIONS.md#dec-090)). `{0, 1}` and `{0.0, 1.0}` receive that Numeric detail. They do not receive Boolean detail.

Descriptive statistics are a later analysis fact ([DEC-091](DECISIONS.md#dec-091)). They are not added to `NumericStructureEvidence`, and they are not collected before the selected semantic type is known. After resolution, a column selected as Numeric receives a finite-population profile: minimum, maximum, range, mean, median, sample standard deviation, Q1, Q3, and interquartile range. Missing values are excluded. Positive and negative infinity are excluded. An empty finite population leaves those statistics undefined. The sample standard deviation divides by `n - 1` (`ddof=1`). One finite value has no standard deviation. Q1, the median, and Q3 use one linear interpolation: the position is `(n - 1) * q`, which is Hyndman-Fan type 7. The method is not configurable. Integer minimum and maximum stay exact. Mean and sample standard deviation are float64 when that result is finite ([DEC-096](DECISIONS.md#dec-096)). A mean, sample standard deviation, range, or interquartile range that is not a finite supported number is `None`. `None` is not zero and not NaN. It does not reject the other statistics and it does not reject the column. Integer populations outside the exact float64 integer range are centered by their minimum in integer arithmetic before the mean and the deviation are calculated, so a difference of 1 is not stored as a zero deviation. Differences larger than `2**53` can still round. This is not arbitrary-precision arithmetic. Q1, the median, and Q3 stay on the type-7 linear rule. A non-integral quantile of integer data stays exact when float64 would move it outside the integer extrema. `-0.0` is recorded as `0.0`. Constant numeric columns stay Constant and are not described. An unavailable descriptive statistic does not change the selected Numeric type. This does not change semantic inference.

Still not delivered for Numeric: sum; mode; a stored variance; MAD; coefficient of variation; skewness; kurtosis; distribution visualization; distribution fitting; normality tests; outlier or anomaly signals; confidence intervals; robust estimators; and Findings. Numeric analysis is not complete.

A Numeric candidate assessment may be supported for a non-empty, non-constant physical integer or floating column ([DEC-083](DECISIONS.md#dec-083)). That storage is the positive evidence. Numeric-structure facts do not add a distribution cutoff and are not required. Complex storage is not that support. Numeric-looking strings are not parsed. `{0, 1}` and `{0.0, 1.0}` on numeric storage may support the Numeric candidate and are not Boolean or Binary. Empty and Constant are not supported for the candidate. The assessment does not select Numeric. The precedence chain does not call it. Resolution may select that candidate when it is the only one supported. The inferred result keeps that selection and the observed physical dtype, and it does not assign confidence ([DEC-085](DECISIONS.md#dec-085), [DEC-086](DECISIONS.md#dec-086)).

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

A Categorical candidate assessment may be supported for a non-empty, non-constant physical categorical dtype ([DEC-083](DECISIONS.md#dec-083)). That storage is the positive evidence. Ordered metadata stays on the physical dtype and does not create an Ordinal type. Unused levels do not change the rule. Repetition and low cardinality are not an operational rule: no cardinality threshold is approved, so an ordinary string, object, or numeric column is not supported as Categorical from those facts alone. Exactly two labels are not sufficient. The product meaning of an arbitrary two-category variable remains categorical rather than Boolean. The candidate assessor does not yet have an approved vocabulary rule that would support that reading from the labels alone. The assessment does not select Categorical. The precedence chain does not call it.

A Categorical variable detail copies most-frequent and singleton counts from frequency evidence when the selected semantic type is Categorical ([DEC-090](DECISIONS.md#dec-090)). It does not retain the most frequent value or the per-value frequency table. Ordered storage stays physical metadata. Ordinary repeated strings are not given this detail, because repetition still does not select Categorical.

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
- `{0, 1}` may support a binary interpretation and is not automatically Boolean. `{0.0, 1.0}` is not accepted as that evidence ([OPEN-046](DECISIONS.md#open-046)). Physical numeric storage of either pair may support a Numeric candidate ([DEC-083](DECISIONS.md#dec-083)). That candidate is not Boolean and not Binary.
- Conservative true/false recognition may support binary semantics. Conservative yes/no recognition may also be considered, more cautiously. String or token recognition never coerces or mutates the Series.
- An arbitrary two-category variable stays categorical, including as a binary category, and is not described as Boolean.
- A column name may support a binary reading and must never decide it. Do not grow a large language or domain dictionary of binary token pairs in core.

The contract allows a binary interpretation that is not necessarily Boolean. The current `SemanticType.BOOLEAN` family cannot fully express that distinction. Heuristic `{0, 1}` inference and string-token Binary inference must not be implemented until a binary-not-Boolean reading can be represented without mislabeling it ([DEC-074](DECISIONS.md#dec-074)). That hold does not resolve the representation question, and it does not add a semantic type. Whether Binary becomes a semantic type, a subtype, a semantic property, or another representation remains [OPEN-014](DECISIONS.md#open-questions).

A selected Boolean column receives true and false counts after semantic resolution ([DEC-092](DECISIONS.md#dec-092)). The counts live in `pytics.analysis`. They are not semantic evidence, and they do not change inference. `True` increments `true_count` only. `False` increments `false_count` only. Missing values increment neither. The ratios divide by the non-missing count, so they are not proportions of all rows. Empty and Constant still precede Boolean, so a one-valued physical Boolean column stays Constant and is not counted. `{0, 1}`, `{0.0, 1.0}`, true/false strings, yes/no strings, and arbitrary two-category labels do not receive these counts. A categorical column whose stored values are boolean stays Categorical. The pass is exact, full-column, and unsampled. Entropy, confidence intervals, hypothesis tests, and a Binary type are not delivered. `REQ-D-01`, `REQ-D-02`, and `REQ-D-03` stay not completed: this does not infer binary-like strings or `{0, 1}`, and it does not add a new confidence statement.

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

`StringStructureEvidence` records empty strings, whitespace, alphabetic, digit, and other characters, and minimum and maximum length ([DEC-080](DECISIONS.md#dec-080)). Those facts are observations. They are not word counts, pattern names, or a Text, Categorical, or Identifier reading.

`PatternEvidence` records full-value UUID, IPv4, IPv6, and fixed-width ASCII hexadecimal token counts ([DEC-081](DECISIONS.md#dec-081)). A compact UUID may increment both the UUID count and the 32-character hexadecimal count. Those counts are observations. They do not select Identifier, Text, Categorical, or Datetime. The hexadecimal counts are not hash-algorithm names. Email-like, URL-like, path-like, and datetime-like strings are not patterns in this family. No pattern-agreement threshold is introduced. A full-population UUID or same-width hexadecimal count may support an Identifier candidate ([DEC-082](DECISIONS.md#dec-082)). That support is not the selected semantic type. Those pattern counts do not support Text or Categorical ([DEC-083](DECISIONS.md#dec-083)).

A Text candidate assessment is not supported from current observations ([DEC-083](DECISIONS.md#dec-083), [DEC-084](DECISIONS.md#dec-084)). String dtype, length bounds, whitespace, character classes, alphanumeric token runs, token repetition, long values, and prose-like appearance are not an approved positive rule. No length, whitespace, or token-count threshold is chosen. The permission that long, multi-word, or prose-like structure may support Text remains ([DEC-071](DECISIONS.md#dec-071)). The candidate may stay unsupported beside Categorical and Identifier. That is not a contradiction and not a selected generic-string type. Downstream common-token diagnostics and trimmed mean remain [OPEN-019](DECISIONS.md#open-questions).

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

`unique_ratio == 1` alone is not sufficient. Perfect uniqueness is not a definitional requirement. Zero missingness is not sufficient and is not a definitional requirement. Their weight remains future evidence and thresholds. The universal property `unique_ratio_non_missing` uses the non-missing count as its denominator ([DEC-077](DECISIONS.md#dec-077)). That does not decide an Identifier threshold, and it does not create a `unique_ratio` alias. Duplicates do not automatically disqualify Identifier. Duplicate identifiers may later be a quality finding under section I. A column name may support Identifier and must never decide it alone. Positive Identifier evidence is required before Identifier displaces a generic Numeric reading ([DEC-069](DECISIONS.md#dec-069)). UUID-like and hash-like structure are stronger Identifier evidence than generic uniqueness ([DEC-072](DECISIONS.md#dec-072)). `PatternEvidence` can count UUID syntax and fixed-width hexadecimal tokens ([DEC-081](DECISIONS.md#dec-081)). Those counts are not an Identifier reading, and the hexadecimal counts are not hash-algorithm names.

The first Identifier candidate assessment may be `SUPPORTED` when every non-missing value matches UUID syntax, or when every non-missing value matches one ASCII hexadecimal width of 32, 40, 64, or 128 ([DEC-082](DECISIONS.md#dec-082)). That is a candidate assessment, not a selected Identifier interpretation. A compact UUID may contribute both facts. That is not a score. A partial pattern ratio does not support the candidate. A mixture of patterns does not support it. IPv4 and IPv6 do not support it and do not contradict it. Uniqueness and missingness do not support it. Duplicates do not contradict it. Empty and Constant remain `NOT_SUPPORTED` for this candidate, including a constant UUID, because those readings already have precedence. Numeric sequences are not Identifier candidates in this assessment. Regular-step evidence is not an observation, and the assessor does not reconstruct it. The same sequences may support a Numeric candidate ([DEC-083](DECISIONS.md#dec-083)). That support does not select Numeric and does not change the Identifier result. The full-population rule is the conservative initial candidate rule for the current evidence foundation. It is not a universal threshold. Partial-pattern thresholds, numeric sequence evidence, column-name evidence, dataset context, resolution, and final confidence remain open ([OPEN-044](DECISIONS.md#open-questions)).

An Identifier variable detail copies the retained pattern counts when the selected semantic type is Identifier ([DEC-090](DECISIONS.md#dec-090)). Overlapping UUID and hexadecimal counts stay separate facts. They are not a score. Duplicate UUID values stay Identifier. A repeated UUID stays Constant and does not receive Identifier detail. The constant value itself is not retained.

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

TSK-022 records observed missingness structure in `pytics.analysis` ([DEC-093](DECISIONS.md#dec-093)). It is not semantic inference. One DataFrame pass counts exact row missingness and exact patterns of physical column positions, then drops the mask. Column missing counts stay the basic-evidence counts. Pandas missingness is the rule. Missing-like literals stay observed. The empty pattern is a complete row. Patterns do not use labels as identity. The pass is exact and has no cutoff. It does not classify MCAR, MAR, or MNAR, and it does not compute a co-missingness coefficient. The rendered Missing view is not this summary.

## I — Duplicate analysis

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-I-01 | Report exact duplicate rows and duplicate groups. | Accepted |
| REQ-I-02 | Report duplicate identifiers. | Accepted |
| REQ-I-03 | Report conflicting duplicates. | Accepted |
| REQ-I-04 | Support controlled partial-duplicate analysis. | Accepted as a named capability. "Controlled" is not defined ([OPEN-018](DECISIONS.md#open-questions)). |
| REQ-I-05 | Do not run uncontrolled combinatorial searches over all possible column combinations. | Accepted |
| REQ-I-06 | Fuzzy or near-duplicate analysis is not a default core operation. | Accepted as a boundary. |

TSK-023 records exact duplicate rows in `pytics.analysis` ([DEC-094](DECISIONS.md#dec-094)). A duplicate group is one complete row value that occurs more than once. Membership is physical row position. The index and the column labels are not part of the row. Pandas factorize equality is the rule, including one shared code for pandas-missing values in a column. `n_unique_rows` and `n_excess_duplicate_rows` are separate counts. Excess rows are occurrences beyond one of each distinct row value. The pass does not decide that a repeated row is an error. It does not normalize case, whitespace, or close numbers. Identifier duplicates, conflicting duplicates, and partial duplicates are not this pass. The rendered Duplicates view is not this summary. The dataset overview copies the unique-row and excess-row counts only.

Fuzzy or near-duplicate analysis may eventually become optional or deep functionality. That capability is **Future investigation** ([OPEN-020](DECISIONS.md#open-questions)). TSK-023 does not define it.

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

TSK-024 calculates one family in `pytics.analysis` ([DEC-095](DECISIONS.md#dec-095)). TSK-025 moves that implementation into `pytics.analysis.relationships` and leaves the statistical rules unchanged ([DEC-096](DECISIONS.md#dec-096)). A Numeric column whose descriptive mean or standard deviation is unavailable stays Numeric, and a relationship that uses it is not dropped for that reason. Both columns must be selected as Numeric. The pair is identified by physical position. Spearman rank correlation is the primary descriptive association. Pearson product-moment correlation is complementary. The population is the pairwise finite rows. The estimate, a Pearson Fisher z interval at 95% when defined, and the raw p-value are separate components. Spearman has no interval in that slice. Adjusted p-values are not calculated. No normality test chooses the method. No strength label or Finding is added.

TSK-026 calculates selected Numeric × selected Categorical in the same package ([DEC-097](DECISIONS.md#dec-097)). Physical position is still the pair identity. The numeric and categorical roles do not depend on which side is numeric. The population is a finite Numeric value paired with a non-missing category. Only observed groups are described, using the same Numeric descriptive definitions. The effect is eta squared. The omnibus test is classical one-way ANOVA. The effect and the raw p-value are separate. There is no post-hoc test, no assumption gate, no strength label, and no adjusted p-value. Other accepted pair directions are counted and not calculated. This does not complete the Relationships contract.

TSK-027 does not add a family and does not change those calculations ([DEC-098](DECISIONS.md#dec-098)). The dataset relationship container stores coverage and family records. It does not store one method, one population rule, one computational image, or one confidence level for every pair. Pair counts stay on the pair. The eligibility rule stays on the family record. A 95% level is stored only on an available Pearson interval.

TSK-028 calculates selected Boolean × selected Boolean in the same package ([DEC-099](DECISIONS.md#dec-099)). Physical position is still the pair identity. The conditioning role is the left column and the outcome role is the right column. Those names are conditional-probability roles, not causes. The population is pairwise non-missing Boolean values. The four logical cells are retained, including zeros. The probability difference, the probability ratio, and phi are separate from the raw two-sided Fisher exact p-value. An absent conditioning level is not a zero probability. An exact infinite ratio is not stored as a number. There is no confidence interval, no continuity correction, and no strength label. `{0, 1}`, `{0.0, 1.0}`, Boolean-like strings, and a categorical column whose values are Boolean do not enter this family unless semantic selection already says Boolean. No semantic rule changed. Categorical × Categorical is still not calculated. This does not complete the Relationships contract.

TSK-029 calculates selected Numeric × selected Boolean in the same package ([DEC-100](DECISIONS.md#dec-100)). Physical position is still the pair identity. The Numeric and Boolean roles do not depend on which side is Boolean. Every signed component is True minus False. That orientation is not causal, and unlike Boolean × Boolean it does not follow the physical column order. The population is a finite Numeric value paired with a non-missing Boolean value. Both groups are retained in False, True order, each with the Numeric descriptive definitions. An absent level is an unavailable group, not a zero-size group, and the Boolean column is not reclassified. The mean difference in original units, Hedges' g, the 95% Welch–Satterthwaite interval for the mean difference, and Welch's t-test with its raw two-sided p-value are separate components. Large integer offsets do not erase a between-group difference or a within-group spread. Zero within-group variation does not become a finite standardized effect, an infinite t, or a zero-width interval. There is no assumption gate, no strength label, and no adjusted p-value. `{0, 1}` and `{0.0, 1.0}` keep the Numeric role. Categorical × Boolean has no accepted direction and is not calculated. This does not complete the Relationships contract.

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

Feature-target relationships reuse the shared relationship layer (`REQ-T-05`, [DEC-059](DECISIONS.md#dec-059)). Target-specific behavior adds distribution, imbalance, the diagnostic model, and potential leakage. The Numeric × Boolean relationship family ([DEC-100](DECISIONS.md#dec-100)) may later serve a Boolean target with Numeric predictors. It is symmetric dataset analysis with Numeric and Boolean roles. It has no target, predictor, importance, or leakage field, and it does not advance `REQ-L-01` through `REQ-L-07`. Do not select Random Forest, Extra Trees, gradient boosting, or another estimator in place of [OPEN-013](DECISIONS.md#open-questions).

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
