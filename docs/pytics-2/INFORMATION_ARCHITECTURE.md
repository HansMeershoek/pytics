# Information architecture

Status: **Accepted** as information architecture v1, except where a row below says otherwise ([DEC-023](DECISIONS.md#dec-023)).

Visual and structural direction. Not an HTML specification, and not a frozen component API.

## Report roles

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-19 | HTML is the canonical interactive report. PDF is the professional static, shareable representation. Light theme is the primary design reference. | Accepted |
| REQ-IA-18 | The report should feel modern, restrained, professional, clean, typographically strong, spacious, and analytical. Use color sparingly and semantically. | Accepted |

The stated visual philosophy is: scientific instrument meets modern financial report.

Rendering direction ([DEC-061](DECISIONS.md#dec-061)): standalone HTML through Jinja2, Plotly, and restrained custom JavaScript. Ordinary reports do not require Dash, a web server, React, Vue, or a JavaScript build chain. Plotly is a rendering engine, not this visual grammar. WeasyPrint is the leading PDF candidate and is not a final dependency. HTML and PDF share a design language and need not use identical markup. Static Plotly graphics for PDF are [OPEN-041](DECISIONS.md#open-questions). Do not use significance stars (`REQ-P-10`).

Avoid:

- dopamine dashboards;
- rainbow charts;
- unnecessary cards;
- excessive rounded containers;
- gradients;
- gratuitous shadows;
- icon overload;
- animation without analytical purpose.

Dark mode may exist. Shipping it is **Proposed / not yet finalized**, not a commitment ([OPEN-026](DECISIONS.md#open-questions)).

A restrained "Generated with Pytics" reference may link to About. That is permission, not a requirement that the link exist ([OPEN-027](DECISIONS.md#open-questions)).

## Three levels

Pytics uses progressive disclosure so it can be mathematically deep and visually calm.

| Level | Question |
| --- | --- |
| 1 — Observe | What deserves attention? |
| 2 — Investigate | What exactly is happening? |
| 3 — Verify | How was it calculated, with what method, assumptions, parameters, and data? |

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-17 | Structure the report so a reader can observe, then investigate, then verify. | Accepted |

## Navigation shell

On desktop, the report uses a persistent left-hand navigation sidebar. The sidebar is navigation, not a mini-dashboard.

Do not show irrelevant or empty navigation items.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-01 | Use a persistent left sidebar on desktop, as navigation only. | Accepted |
| REQ-IA-04 | Profile and Compare should feel like two modes of the same product. | Accepted |

Responsive behavior below desktop width was not specified ([OPEN-028](DECISIONS.md#open-questions)).

## Profile navigation

```text
PYTICS
DATA PROFILE

OVERVIEW
  Overview
  Findings

DATA
  Variables
  Missing
  Duplicates
  Anomalies

ANALYSIS
  Relationships
  Target          # only when applicable
  Time Series     # only when applicable

DETAILS
  Methods
  Report Info

----------------
  About Pytics
```

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-02 | Profile navigation follows the structure above, omitting items that do not apply. | Accepted |

### Overview

Rapidly answer:

- what dataset is this?
- how large is it?
- what semantic types exist?
- what deserves attention?

No arbitrary quality score (`REQ-P-07`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-05 | Overview answers those four questions and does not show a composite quality score. | Accepted |

An internal analytical overview now exposes size, cell completeness, the resolved semantic types that are present, semantic-resolution coverage, and the columns that are Empty, Constant, Identifier, insufficient, or ambiguous ([DEC-089](DECISIONS.md#dec-089)). It also copies unique-row and excess-duplicate counts from the duplicate analysis ([DEC-094](DECISIONS.md#dec-094)). It does not list duplicate groups, render this view, name the dataset, or add a composite quality score. "What deserves attention" is not yet a Finding.

### Findings

Findings link back to their analytical evidence (`REQ-N-01`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-06 | The Findings view links each finding back to its evidence. | Accepted |

### Variables

Start with a searchable, sortable, professional variable table. Variable detail is type-aware. Use progressive disclosure rather than rendering every statistic and graph at once (`REQ-IA-17`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-07 | Variables begin as a searchable, sortable table, with type-aware detail under progressive disclosure. | Accepted |

An internal variables summary now exposes one ordered row per physical column, with universal counts and type-specific detail for Numeric, Categorical, Identifier, and Boolean ([DEC-090](DECISIONS.md#dec-090), [DEC-092](DECISIONS.md#dec-092)). A selected Numeric row also carries finite-population descriptive statistics ([DEC-091](DECISIONS.md#dec-091)). A selected Boolean row carries true and false counts. The summary does not render the table, add sort controls, or disclose Datetime, Timedelta, Text, Empty, or Constant statistics beyond the common facts and the selected type.

### Missing

Dedicated analysis for missingness, patterns, co-missingness, and related diagnostics (`REQ-H-01` through `REQ-H-05`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-08 | Missing is its own view for the missing-data contract. | Accepted |

An internal missingness summary now exposes dataset cell facts, one column missingness record per physical column, the row missingness distribution, and exact patterns of physical positions ([DEC-093](DECISIONS.md#dec-093)). It is separate from the dataset overview and from the variables summary. It does not render this view, classify a missingness mechanism, or recommend an imputation.

### Duplicates

Dedicated exact, identifier, partial, and conflict analysis (`REQ-I-01` through `REQ-I-06`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-09 | Duplicates is its own view for the duplicate contract. | Accepted |

An internal duplicate summary now exposes exact duplicate groups and the dataset counts of unique rows, rows in those groups, and excess duplicate rows ([DEC-094](DECISIONS.md#dec-094)). Group membership is physical row position. The summary does not render this view, decide that a duplicate is an error, or match near-duplicates. Identifier duplicates, conflicting duplicates, and partial duplicates are not this summary.

### Anomalies

Separate univariate and multivariate perspectives (`REQ-J-02`, `REQ-J-03`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-10 | Anomalies keeps univariate and multivariate perspectives separate. | Accepted |

### Relationships

Professional relationship exploration. A table-oriented view is important. A matrix may be an additional view. Relationship detail should expose the relationship structure in `REQ-K-04`: description, effect, uncertainty, inference, diagnostics, and method metadata, plus visualization as appropriate (`REQ-K-01`, `REQ-K-02`, `REQ-P-10`). Do not use significance stars.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-11 | Relationships are explored primarily as a table, with detail for statistics, uncertainty, inference, visualization, and methods as appropriate. A matrix is an additional view, not a replacement for the table. | Accepted. "May" for the matrix is preserved: the matrix is allowed, not mandated. |

An internal relationships summary now exposes pair coverage and family records ([DEC-095](DECISIONS.md#dec-095), [DEC-097](DECISIONS.md#dec-097), [DEC-098](DECISIONS.md#dec-098), [DEC-099](DECISIONS.md#dec-099)). A Numeric × Numeric record exposes Spearman and Pearson. Spearman is the primary descriptive association of that record. Pearson is complementary. A Numeric × Categorical record exposes group summaries, eta squared, and a raw one-way ANOVA p-value. A Boolean × Boolean record exposes the 2×2 counts, the conditional outcome-True probabilities, the probability difference, the probability ratio, phi, and a raw two-sided Fisher exact p-value. The summary does not name one method for every pair. It does not render this view, draw a matrix or a chart, or mark a result significant. Other relationship families are not calculated.

### Target

Shown only when target analysis exists.

Potential internal sections, **Proposed / not yet finalized** as a fixed internal outline: overview, relationships, diagnostic model, leakage, methods. The existence of the Target destination is Accepted.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-12 | Show Target only when target analysis exists. | Accepted |

### Time Series

Shown only when genuine time structure is inferred or explicitly configured (`REQ-E-03`, `REQ-E-04`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-13 | Show Time Series only when genuine time structure is inferred or explicitly configured. | Accepted |

### Methods

A technical and reproducibility appendix: methods, assumptions, parameters, priors, sampling, and other relevant details (`REQ-P-05`, `REQ-P-11`, `REQ-P-12`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-14 | Methods is a technical appendix for methods, assumptions, parameters, priors, sampling, and related detail. | Accepted |

### Report Info

Metadata such as:

- Pytics version;
- generation timestamp;
- dataset shape;
- analysis duration;
- mode;
- sampling;
- random seed where relevant.

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-15 | Report Info shows the metadata listed above. Sampling must never be hidden. | Accepted. "Such as" is preserved: this is the named metadata set, not proof that no other metadata field can exist. Mode names are accepted ([DEC-058](DECISIONS.md#dec-058)). Exact mode behavior is [OPEN-010](DECISIONS.md#open-questions). |

### About Pytics

A dedicated About page or section. It will eventually contain:

- the author's story and motivation;
- why Pytics exists;
- project principles;
- author and contact details;
- project links;
- license;
- version information.

Do not invent the author's story or contact details. Those will be supplied separately ([OPEN-029](DECISIONS.md#open-questions)).

The 1.1.5 template blurb is not that material. See [BASELINE_1_1_5.md](BASELINE_1_1_5.md).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-16 | Provide an About destination. Leave narrative, motivation, and contact details empty until they are supplied. License and version may be taken from project metadata that already exists. | Accepted |

Known metadata that already exists, and is not a story: the author name Hans Meershoek in `pyproject.toml`, copyright 2025 Hans Meershoek in `LICENSE`, MIT license, and the repository URL `https://github.com/HansMeershoek/pytics`.

## Compare navigation

```text
PYTICS
DATA COMPARE

OVERVIEW
  Overview
  Findings

DATA
  Schema
  Variables
  Missing
  Duplicates

CHANGE
  Distributions
  Relationships
  Drift

ANALYSIS
  Target          # if applicable
  Time Series     # if applicable

DETAILS
  Methods
  Report Info

----------------
  About Pytics
```

The comparison overview should emphasize what changed (`REQ-M-02`).

| ID | Requirement | Status |
| --- | --- | --- |
| REQ-IA-03 | Compare navigation follows the structure above, omitting items that do not apply. | Accepted |
| REQ-IA-20 | The comparison overview emphasizes what changed. | Accepted |

## What this architecture does not include

No composite score tile. No model leaderboard. No prescribed cleaning actions. No chart whose only reason is that it was easy to draw (`REQ-P-03`, `REQ-P-04`, `REQ-P-07`, `REQ-P-09`).
