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

Target-specific behavior sits on top of that layer: target distribution, imbalance, the diagnostic model, and potential leakage ([DEC-059](DECISIONS.md#dec-059)).

The exact internal API is [OPEN-038](DECISIONS.md#open-questions).

## Method registry

The registry concept is accepted ([DEC-038](DECISIONS.md#dec-038)). Its purpose is a central, inspectable description of methods and their applicability. An entry may eventually carry a stable identifier, name, purpose, applicable semantic types, assumptions, parameters, limitations, computational characteristics, references, and the modes in which the method is available. That list is not a schema.

Do not implement the registry until the schema and API are decided (`REQ-T-03`, [OPEN-039](DECISIONS.md#open-questions)).

## Core value models

Accepted ([DEC-062](DECISIONS.md#dec-062)). Core analytical result and value models use frozen dataclasses, enums, and explicit type hints where those objects are analytical facts. Pydantic is not required. Dictionaries and TypedDict-only structures are not the preferred representation for those facts. Do not freeze mutable orchestration or configuration objects before they exist. This does not freeze public result-class names ([OPEN-004](DECISIONS.md#open-questions)).

TSK-001 placed the first of these objects under `src/pytics/semantics/`. TSK-002 added `BasicColumnEvidence` there, as an exact observed-characteristic fact, and Empty/Constant interpretations that reuse the Slice 001 physical classifier. TSK-003 composes those rules with one further reading: semantic Boolean when the physical family is Boolean and the column is neither Empty nor Constant. That Boolean reading uses the physical dtype as its source. Object, categorical, numeric, and string values are not read as Boolean. TSK-004 calls that chain and then reads semantic Datetime when the physical family is native datetime or timezone-aware datetime. Both families stay distinct on the physical dtype. The composition is one successor function, not a rule registry. String, object, integer, categorical, timedelta, and period values are not read as Datetime. Those modules are internal. That location does not resolve [OPEN-045](DECISIONS.md#open-questions). The physical classifier names storage families only. Ordinal storage remains [OPEN-016](DECISIONS.md#open-questions). The subtype taxonomy remains [OPEN-014](DECISIONS.md#open-questions). Inference thresholds remain [OPEN-044](DECISIONS.md#open-questions).

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
