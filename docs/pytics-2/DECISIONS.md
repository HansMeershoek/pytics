# Decision log

Accepted decisions from the Pytics 2.0 bootstrap briefing, recorded 2026-10-03, from the architecture and methodology update recorded the same day, from Slice 001 recorded the same day, from the semantic-foundation consolidation recorded the same day, from TSK-006 recorded the same day, from TSK-007 recorded the same day, from TSK-008 recorded the same day, from TSK-009 recorded the same day, from TSK-010 recorded the same day, from TSK-011 recorded the same day, from TSK-012 recorded the same day, and from TSK-013 recorded the same day.

IDs are stable. Do not renumber them. A change of mind is a new decision that supersedes an old one, not an edit that hides the old text.

Status values: **Accepted**. Where a later decision narrows an earlier one, the earlier entry stays in place and gains a later-update note. The superseded part is listed under [Superseded decisions](#superseded-decisions). Items that are not decisions are listed under [Open questions](#open-questions) and are not accepted. Resolved questions stay in the log.

## DEC-001

| | |
| --- | --- |
| Title | Pytics 2.0 is a clean redesign |
| Status | Accepted |
| Decision | 2.0 is a clean redesign of the product, not a blind incremental refactor of the 1.1.5 architecture. The 1.1.5 codebase is a functional and historical reference. Algorithms, tests, behavior, and ideas may be reused only deliberately. Nothing is inherited automatically. |
| Rationale | The briefing states that the current implementation is relatively monolithic and that 2.0 must not treat 1.1.5 as the architecture to extend in place. |
| Implications | Do not start 2.0 by refactoring `profiler.py`. Do not describe 1.1.5 behavior as if it already met this contract. Reuse inside a later slice must be an explicit choice. See [BASELINE_1_1_5.md](BASELINE_1_1_5.md). |

## DEC-002

| | |
| --- | --- |
| Title | Product identity |
| Status | Accepted |
| Decision | Pytics is an analytical microscope for datasets, for professional data scientists and data analysts. Its purpose is to understand a dataset, relationships, data-quality characteristics, a supplied target, the comparison of two datasets, and changes and drift. The goal is understanding, not optimizing predictive performance. |
| Rationale | Stated as the core concept and primary purpose in the bootstrap briefing. |
| Implications | `REQ-P-01`, `REQ-P-02`. Features that exist to raise a model's score are outside the product. |

## DEC-003

| | |
| --- | --- |
| Title | Explicit non-goals |
| Status | Accepted |
| Decision | Pytics is not to become an AutoML platform, a BI dashboard, a data-cleaning framework, a notebook replacement, an AI-insights gimmick, or an automatic prescriptive system. |
| Rationale | The briefing lists these as products Pytics is not intended to become. |
| Implications | `REQ-P-03`. The older `Prompt` file's interest in Great Expectations or Pandera, PowerPoint export, and an interactive wizard is not carried forward by this decision. |

## DEC-004

| | |
| --- | --- |
| Title | Report and observe; do not prescribe |
| Status | Accepted |
| Decision | The general philosophy is to report and observe, and not to prescribe. |
| Rationale | Stated as the general philosophy. It is also why leakage, drift, outliers, and missingness mechanisms are framed as evidence rather than instructions. |
| Implications | `REQ-P-04`, `REQ-J-01`, `REQ-M-03`, `REQ-L-03`, `REQ-H-05`. Findings describe evidence. They do not tell the user to delete rows, impute values, or ship a model. |

## DEC-005

| | |
| --- | --- |
| Title | Professional audience, inspectable methods |
| Status | Accepted |
| Decision | Design for professionals. Do not add educational clutter merely for beginners. Methods and assumptions remain inspectable and transparent. |
| Rationale | Stated audience principle. |
| Implications | `REQ-P-05`, `REQ-IA-14`, `REQ-IA-17`. Depth belongs in the verify level, not in beginner exposition. |

## DEC-006

| | |
| --- | --- |
| Title | Pandas Perfect |
| Status | Accepted |
| Decision | Excellent pandas support comes before multiple dataframe engines. Do not design a Polars or Arrow abstraction at this stage merely for theoretical future compatibility. Avoid unnecessary decisions that would make later expansion impossible. |
| Rationale | Stated data-model principle. |
| Implications | `REQ-P-06`. What "unnecessary blocking decision" means is [OPEN-002](#open-questions). Polars and PyArrow are not rejected forever; they are not a reason to add an engine abstraction now. |
| Later update | [DEC-040](#dec-040) limits the core API to pandas DataFrames. [DEC-060](#dec-060) says Polars is not a core dependency and PyArrow is not required merely for that API. Neither note reverses the "not rejected forever" sentence, and neither authorizes an engine abstraction. |

## DEC-007

| | |
| --- | --- |
| Title | Semantic-first inference |
| Status | Accepted |
| Decision | Physical dtype is not sufficient. Infer semantic meaning. The minimum concepts are Numeric, Categorical, Boolean/Binary, Text/String, Datetime, Timedelta, Identifier, Constant, and Empty. Subtypes may exist where useful. Inference retains type, confidence, evidence or reasoning, and relevant metadata. Inference must not mutate the original DataFrame. Inference should be intelligent and transparent. |
| Rationale | Stated semantic-first principle, including the minimum concept list and the non-mutation rule. |
| Implications | `REQ-S-01` through `REQ-S-09`. Boolean conservatism is [DEC-014](#dec-014) via section D, refined by [DEC-047](#dec-047). |
| Later update | [DEC-041](#dec-041) through [DEC-054](#dec-054) refine inference, confidence, overrides, coercion, Empty/Constant, identifiers, numeric and string meaning, datetime and timedelta, ordinal policy, eligibility, and sampling. Subtype taxonomy remains [OPEN-014](#open-questions). The ordinal storage question remains [OPEN-016](#open-questions). |
| Later update | [DEC-064](#dec-064) through [DEC-076](#dec-076) record the semantic-foundation consolidation. They refine the inference pipeline, evidence roles, v0.1 scoring scope, material alternatives, Identifier and string meanings, binary representation pressure, overrides, and evidence reuse. They do not close the open questions named in those decisions. |
| Later update | [DEC-077](#dec-077) specifies the stored counts and derived facts of the universal column-evidence family. It does not add a semantic type. |

## DEC-008

| | |
| --- | --- |
| Title | No composite quality score |
| Status | Accepted |
| Decision | Do not create an overall data-quality score. Report concrete evidence and findings. |
| Rationale | The briefing rejects an 82/100-style score. |
| Implications | `REQ-P-07`, `REQ-IA-05`. Dataset-level analysis surfaces factual findings. |

## DEC-009

| | |
| --- | --- |
| Title | Statistical depth |
| Status | Accepted |
| Decision | Analysis should be statistically rich rather than a wrapper of `DataFrame.describe()`. |
| Rationale | Stated statistical-depth principle. |
| Implications | `REQ-P-08`. This does not select libraries or a method list. See [STATISTICAL_METHODS.md](STATISTICAL_METHODS.md). |

## DEC-010

| | |
| --- | --- |
| Title | Evidence before decoration |
| Status | Accepted |
| Decision | Every chart should answer an analytical question. No chart should exist only because a plotting library makes it easy. |
| Rationale | Stated evidence-before-decoration principle. |
| Implications | `REQ-P-09`, `REQ-C-07`. |

## DEC-011

| | |
| --- | --- |
| Title | Effect size first |
| Status | Accepted |
| Decision | For inferential statistics, effect size comes first and statistical significance second. P-values are not the primary interpretation. Where appropriate, also consider uncertainty, confidence or credible intervals, p-values, assumptions, sample size, missing observations, and multiple-testing correction. |
| Rationale | Stated inferential principle. |
| Implications | `REQ-P-10`. Per-method applicability is [OPEN-006](#open-questions). |
| Later update | [DEC-056](#dec-056) sets the multiple-testing direction and rejects significance stars. The test-family definition remains [OPEN-007](#open-questions). |

## DEC-012

| | |
| --- | --- |
| Title | Bayesian inference is in scope for understanding |
| Status | Accepted |
| Decision | Bayesian inference is in scope when it helps understand data. It complements frequentist inference. It is not Bayesian predictive optimization. Analyses must disclose method, prior, posterior, credible interval, relevant probability statements, approximation or sampling where applicable, and limitations. A Bayesian counterpart is not promised for every analysis. |
| Rationale | The briefing places Bayesian understanding inside the product and sets transparency limits. |
| Implications | `REQ-P-11`. |
| Later update | [DEC-057](#dec-057) makes Bayesian analysis selective and lightweight. The method catalog remains [OPEN-008](#open-questions). |

## DEC-013

| | |
| --- | --- |
| Title | Reproducibility |
| Status | Accepted |
| Decision | Where reasonably possible, the same data, configuration, Pytics version, and random seed produce the same analytical result. Sampling, stochastic models, and other nondeterministic methods record relevant metadata. |
| Rationale | Stated reproducibility principle. |
| Implications | `REQ-P-12`. Seed configuration is [OPEN-009](#open-questions). |
| Later update | [DEC-054](#dec-054) accepts controlled sampling for expensive semantic evidence. Mode contents, thresholds, and other sampling rules remain [OPEN-010](#open-questions). |

## DEC-014

| | |
| --- | --- |
| Title | Analytical areas A–N are in scope |
| Status | Accepted |
| Decision | Dataset-level analysis, numeric, categorical, boolean/binary, datetime and time, text/string, identifier detection, missing data, duplicates, outliers and multivariate anomalies, relationships and statistical inference, target analysis, dataset comparison and drift, and structured findings are accepted parts of the analytical design. The binding write-up, including preserved qualifiers, is [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md). |
| Rationale | The briefing presents contract A–N as accepted design, and separately marks method catalogs and several APIs as not finalized. |
| Implications | Requirements `REQ-A-*` through `REQ-N-*`, plus the semantic requirements. Qualified lists are not silently turned into closed mandatory catalogs ([OPEN-001](#open-questions)). Named methods in section K are not part of this acceptance. |
| Later update | [DEC-055](#dec-055) accepts methodological direction for named pair types. That direction is not a closed catalog, and it does not retire `REQ-K-03`. |

## DEC-015

| | |
| --- | --- |
| Title | Missingness is reported conservatively |
| Status | Accepted |
| Decision | Missing-like literals are reported and are not silently rewritten as missing. MCAR, MAR, and MNAR diagnostics stay methodologically conservative and must not claim a definitive mechanism the observed data cannot support. |
| Rationale | Stated missing-data rules. |
| Implications | `REQ-H-04`, `REQ-H-05`. The literal dictionary is not closed ([OPEN-018](#open-questions)). |

## DEC-016

| | |
| --- | --- |
| Title | Identifiers are first-class and usually excluded from meaningless analyses |
| Status | Accepted |
| Decision | Identifier is a first-class semantic concept. Detection exposes evidence and reasoning. Identifiers are normally excluded from analyses where inclusion would be meaningless, such as ordinary correlation or target modeling, unless explicitly justified or configured. |
| Rationale | Stated identifier rules. |
| Implications | `REQ-G-01` through `REQ-G-03`. |
| Later update | [DEC-048](#dec-048) resolves the evidence list as admissible signals, not a closed detector, and rejects uniqueness alone. Thresholds remain [OPEN-044](#open-questions). |

## DEC-017

| | |
| --- | --- |
| Title | Outliers and anomalies are not automatic errors |
| Status | Accepted |
| Decision | Outlier does not mean error. Anomaly does not mean bad data. Support robust univariate analysis and multivariate anomaly detection. Do not automatically recommend deleting anomalous observations. Multivariate analysis should eventually provide explainability or context where possible. |
| Rationale | Stated anomaly principles. |
| Implications | `REQ-J-01` through `REQ-J-04`. Univariate techniques and multivariate algorithms are [OPEN-022](#open-questions). Explainability is a goal whose design is not finalized. |

## DEC-018

| | |
| --- | --- |
| Title | One diagnostic model, for understanding only |
| Status | Accepted |
| Decision | Target analysis may use one lightweight, untuned diagnostic model to expose multivariate feature-target relationships. The model is for understanding data architecture, not predictive optimization. Validation must be methodologically responsible rather than training and judging on exactly the same observations. Do not add hyperparameter search, leaderboards, competitions, automated tuning, or deployment. Leakage is surfaced as evidence, not asserted without basis. |
| Rationale | Stated target-model boundary. |
| Implications | `REQ-L-03` through `REQ-L-07`. |
| Later update | The statement that permutation importance was only a discussion is superseded by [DEC-059](#dec-059). Estimator family remains [OPEN-013](#open-questions). |

## DEC-019

| | |
| --- | --- |
| Title | Findings are structured and do not require an LLM |
| Status | Accepted |
| Decision | Findings are structured analytical objects traceable to metric, value, threshold where relevant, method, variables, and source analysis. Rendered text presents that object. Core findings must be producible without an LLM. Labels must not be gamified or sensational. |
| Rationale | Stated findings principle, including independence from an LLM. |
| Implications | `REQ-N-01` through `REQ-N-04`. The level names information, notable, and warning are [OPEN-025](#open-questions). |

## DEC-020

| | |
| --- | --- |
| Title | Analysis is separate from notebook dumping |
| Status | Accepted |
| Decision | `profile` performs analysis and must not dump charts into the notebook. A plain notebook representation stays compact. Structured results are available programmatically. HTML and PDF are explicit rendering steps. The exact methods and attribute names are not frozen. |
| Rationale | The briefing gives this usage direction and then says the exact API is not frozen. |
| Implications | `REQ-P-13`, `REQ-P-14`. Illustrative names such as `show`, `to_html`, `to_pdf`, `variables`, `missing`, `relationships`, and `findings` are not accepted as the API. See [OPEN-004](#open-questions). |
| Later update | [DEC-040](#dec-040) accepts DataFrame-only `profile` and `compare` as the core conceptual API. Signatures and result-object names remain open. |

## DEC-021

| | |
| --- | --- |
| Title | HTML is canonical; PDF is the static representation |
| Status | Accepted |
| Decision | HTML is the canonical interactive report. PDF is a professional static, shareable representation. |
| Rationale | Stated report-format roles. |
| Implications | `REQ-IA-19`. The 1.1.5 PDF failure is not a 2.0 design input beyond the baseline record. |
| Later update | [DEC-061](#dec-061) sets the HTML and PDF direction. Final libraries remain [OPEN-035](#open-questions). Static chart export for PDF is [OPEN-041](#open-questions). |

## DEC-022

| | |
| --- | --- |
| Title | Visual philosophy |
| Status | Accepted |
| Decision | The report should feel like a scientific instrument meeting a modern financial report: modern, restrained, professional, clean, typographically strong, spacious, and analytical. Color is sparse and semantic. Avoid dopamine dashboards, rainbow charts, unnecessary cards, excessive rounded containers, gradients, gratuitous shadows, icon overload, and animation without an analytical purpose. Light theme is the primary reference. Dark mode may exist. |
| Rationale | Stated visual philosophy and the avoid list. |
| Implications | `REQ-IA-18`, `REQ-IA-19`. Whether dark mode ships is [OPEN-026](#open-questions). |

## DEC-023

| | |
| --- | --- |
| Title | Information architecture v1 |
| Status | Accepted |
| Decision | Profile and Compare use the navigation structures and section rules in [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md). The sidebar is persistent on desktop and is navigation, not a mini-dashboard. Irrelevant or empty items are omitted. Target and Time Series appear only when applicable. About does not invent an author story. |
| Rationale | The briefing specifies information architecture v1 for both modes. |
| Implications | `REQ-IA-01` through `REQ-IA-16` and `REQ-IA-20`. Internal Target subsections are not frozen. Responsive layout is [OPEN-028](#open-questions). |

## DEC-024

| | |
| --- | --- |
| Title | Three disclosure levels |
| Status | Accepted |
| Decision | Presentation uses three levels: Observe (what deserves attention), Investigate (what is happening), and Verify (method, assumptions, parameters, and data). |
| Rationale | Stated UX principle, so the product can be mathematically deep and visually calm. |
| Implications | `REQ-IA-17`. |

## DEC-025

| | |
| --- | --- |
| Title | Analysis and render stay separate |
| Status | Accepted |
| Decision | This is a hard architectural rule. Analytical code must not directly generate HTML. Analyzers return structured results. HTML and PDF renderers consume those results. |
| Rationale | The briefing marks analysis/render separation as a hard principle, distinct from the then-unadopted pipeline sketch. |
| Implications | `REQ-T-01`, `REQ-T-02`. The 1.1.5 module that renders inside `profile` and `compare` is not a template for 2.0. |
| Later update | [DEC-036](#dec-036) accepts the refined pipeline as architectural direction. That supersedes the "unadopted sketch" clause. Analysis/render separation is unchanged. |

## DEC-026

| | |
| --- | --- |
| Title | Sampling must be visible |
| Status | Accepted |
| Decision | Sampling must never be hidden. Report Info includes sampling, and nondeterministic methods record relevant metadata. |
| Rationale | Stated both as a reproducibility rule and as a Report Info rule. |
| Implications | `REQ-P-12`, `REQ-IA-15`. |
| Later update | Controlled semantic-inference sampling is [DEC-054](#dec-054). Broader sampling rules remain [OPEN-010](#open-questions). |

## DEC-027

| | |
| --- | --- |
| Title | The 2.0 dependency stack is not chosen |
| Status | Accepted, superseded in part by [DEC-060](#dec-060) |
| Decision | No 2.0 dependency decision is made. Do not assume 1.1.5 dependencies remain. Do not choose or install the stack until a separate ecosystem review is decided. The undecided names are listed in [DEPENDENCIES.md](DEPENDENCIES.md). |
| Rationale | The briefing withholds dependency decisions and requires a later ecosystem review. |
| Implications | `REQ-T-04`. |
| Later update | [DEC-060](#dec-060) records the review outcome as candidate directions, not a lock. The prohibition on installing or pinning the stack remains. The statement that the review had not been done, and that the named libraries carried no direction, is superseded. |

## DEC-028

| | |
| --- | --- |
| Title | Implementation slices follow a fixed protocol |
| Status | Accepted |
| Decision | Every future implementation slice follows [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md): identify the requirement, define scope and acceptance criteria, implement only that slice, test, verify against the specification, update progress, record architectural changes, report what changed, and stop. No silent scope expansion, no unregistered architectural change, and no unapproved drive-by refactor. If an accepted specification is technically problematic, stop and report it. |
| Rationale | The briefing records this as the development protocol for all future 2.0 work. |
| Implications | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). No slice is approved by the existence of this log. |

## DEC-029

| | |
| --- | --- |
| Title | Planning documents are the source of truth |
| Status | Accepted |
| Decision | From the bootstrap onward, the approved documents under `docs/pytics-2/` are the durable source of truth for Pytics 2.0. Chat context is not a substitute. Approved decisions stay synchronized in these documents. |
| Rationale | Stated source-of-truth rule. |
| Implications | A later decision that is not written here is not approved. Historical files do not override this directory. See [DEC-035](#dec-035). |

## DEC-030

| | |
| --- | --- |
| Title | Compare explains change, and drift is neutral |
| Status | Accepted |
| Decision | `compare()` is first-class. It uses the same visual and product language as profile. It explains what changed rather than only placing two reports side by side. Drift is reported as observed or material change, not automatically as something bad. The destination coverage list is section M of [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md). |
| Rationale | Stated compare and drift principles. |
| Implications | `REQ-M-01` through `REQ-M-04`, `REQ-IA-03`, `REQ-IA-04`, `REQ-IA-20`. Sequencing of that coverage is [OPEN-024](#open-questions). |

## DEC-031

| | |
| --- | --- |
| Title | Fuzzy duplicates and deep time-series passes are not default |
| Status | Accepted |
| Decision | Fuzzy or near-duplicate analysis is not a default core operation. Deeper time-series diagnostics such as trend, seasonality, and autocorrelation are optional or deep, and are not run on every datetime column. A date column is not the same thing as a time-series structure. |
| Rationale | The briefing sets these boundaries explicitly. |
| Implications | `REQ-I-06`, `REQ-E-03`, `REQ-E-04`, `REQ-IA-13`. Building the deferred capabilities is [OPEN-020](#open-questions). |
| Later update | [DEC-055](#dec-055) says datetime relationships study temporal structure when justified, and must not be ordinary correlation on timestamps. That does not make trend, seasonality, or autocorrelation a default pass on every datetime column. |

## DEC-032

| | |
| --- | --- |
| Title | Zero-config by default |
| Status | Accepted |
| Decision | The configuration goal is zero-config by default and deep configuration when needed. Avoid a public function with dozens of individual keyword arguments. |
| Rationale | Stated configuration goal. |
| Implications | `REQ-P-15`. A configuration object is likely and is not accepted as an API ([OPEN-009](#open-questions)). |

## DEC-033

| | |
| --- | --- |
| Title | About content is supplied later |
| Status | Accepted |
| Decision | About will eventually hold the author's story and motivation, why Pytics exists, project principles, author and contact details, project links, license, and version. Do not invent the story or the contact details. |
| Rationale | The briefing defers that material and forbids inventing it. |
| Implications | `REQ-IA-16`. Existing 1.1.5 About copy is not a substitute ([OPEN-029](#open-questions)). |

## DEC-034

| | |
| --- | --- |
| Title | Core is not an NLP platform |
| Status | Accepted |
| Decision | Text analysis distinguishes string roles and reports the diagnostics in section F. Pytics core is not a full NLP platform. |
| Rationale | Stated limit on text analysis. |
| Implications | `REQ-F-01` through `REQ-F-03`. Common-token analysis is [OPEN-019](#open-questions). |

## DEC-035

| | |
| --- | --- |
| Title | Older briefs do not override this directory |
| Status | Accepted |
| Decision | `Prompt`, `README.md`, `RELEASE_NOTES.md`, and the 1.1.5 templates describe history or the released package. They are not the Pytics 2.0 contract. Where they disagree with `docs/pytics-2/`, these planning documents win for 2.0 work. |
| Rationale | [DEC-029](#dec-029) makes this directory the source of truth. The inspection found an earlier product brief and public docs that specify a different product. Leaving that implicit would let the next session follow the wrong file. |
| Implications | Do not implement path inputs, `include_sections`, an interactive yes/no wizard, or the `Profile` class from those older texts unless a new decision accepts them. Public README text is unchanged by this decision; it still documents 1.1.5. |
| Later update | [DEC-040](#dec-040) rejects core responsibility for paths, CSV, and Parquet. `include_sections`, the wizard, and the `Profile` class remain unaccepted. |

## DEC-036

| | |
| --- | --- |
| Title | High-level engine direction |
| Status | Accepted |
| Decision | The pipeline below is the architectural direction for Pytics 2.0. It is not a frozen class, module, or file layout. The bootstrap sketch is replaced by this diagram. Compare stays a public entry point. Drift and temporal analysis are special analyses, not a second statistical implementation. |
| Rationale | The bootstrap left the engine diagram unadopted. This update accepts the refined direction and withholds the file layout. |
| Implications | `REQ-T-01` and `REQ-T-02` still separate analysis from rendering. Exact layout is [OPEN-045](#open-questions). Result names remain [OPEN-004](#open-questions). |

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

## DEC-037

| | |
| --- | --- |
| Title | One shared statistical layer |
| Status | Accepted |
| Decision | General relationships, target analysis, missingness relationships, dataset comparison, and drift reuse one statistical and methodological layer wherever that reuse is analytically appropriate. Pytics must not keep a separate statistical truth for each of those uses. Target-specific behavior is layered on top of that shared capability. The exact internal API is not accepted. |
| Rationale | Parallel implementations would let the same relationship mean different things in different reports. |
| Implications | `REQ-T-05`. The API and the boundary of "analytically appropriate" are [OPEN-038](#open-questions). |

## DEC-038

| | |
| --- | --- |
| Title | Method registry concept |
| Status | Accepted |
| Decision | A method registry is accepted as the central, inspectable description of analytical methods and their applicability. A method may eventually expose a stable identifier, name, analytical purpose, applicable semantic types, assumptions, parameters, limitations, computational characteristics, references, and the analysis modes in which it is available. That list is illustrative. The implementation, schema, and API are not accepted. Do not implement the registry. |
| Rationale | Methods and assumptions must stay inspectable. Accepting the concept does not freeze a schema. |
| Implications | `REQ-T-03` now holds implementation until the schema and API exist, not until the concept is accepted. Those remain [OPEN-039](#open-questions). `REQ-K-03` still forbids a hard-coded final catalog. |

## DEC-039

| | |
| --- | --- |
| Title | Pytics 2.0 replaces `src/pytics` |
| Status | Accepted |
| Decision | The intended end state is that Pytics 2.0 replaces the implementation inside the normal `src/pytics` package. The final product does not keep a permanent `pytics_v2`, `pytics2`, `legacy`, `old_profiler`, or `new_profiler` package. Pytics 1.1.5 may remain temporarily available during migration as a reference. Git history is the long-term archive. Migration mechanics and temporary coexistence stay open. This decision does not delete or move current code. |
| Rationale | A permanent second package would become the product. The end state is one package. How to get there is a planning question. |
| Implications | [OPEN-040](#open-040). [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) still forbids an unapproved slice from adding that tree. |
| Later update | [DEC-063](#dec-063) accepts the migration mechanics. The end state in this decision is unchanged. |

## DEC-040

| | |
| --- | --- |
| Title | Core API is DataFrame-only |
| Status | Accepted |
| Decision | The core analytical API is pandas DataFrame-first and DataFrame-only. Conceptually, `pytics.profile(df)` and `pytics.compare(df_a, df_b)`. Core does not take responsibility for CSV parsing, separators, encodings, Parquet engines, remote file loading, or generic path detection. Users load data through pandas and pass a DataFrame. Exact public signatures and result-object names are not accepted. |
| Rationale | File loading is a pandas responsibility. The 1.1.5 documentation claimed path inputs the code did not implement. 2.0 does not take that responsibility back. |
| Implications | `REQ-P-06`. Signatures and result names remain [OPEN-004](#open-questions). This rejects the path-input claim in the public 1.1.5 README for 2.0 work. It does not edit that README. |

## DEC-041

| | |
| --- | --- |
| Title | Semantic inference system v0.1 |
| Status | Accepted |
| Decision | Physical dtype, observed characteristics, and semantic interpretation are distinct. Physical pandas dtype is evidence, not the final analytical meaning, and the original physical dtype stays inspectable. Inference is evidence-driven, through conceptual stages of physical classification, basic evidence, pattern and structural evidence, candidate semantic types, conflict resolution, and semantic interpretation. Those stages are not a frozen function decomposition. An interpretation must be able to retain semantic type, subtype where relevant, confidence, supporting evidence, alternative interpretations where relevant, and source. Sources include inferred, directly supported by physical dtype, and explicitly configured by the user. Exact object names are not accepted. |
| Rationale | A dtype branch cannot express identifiers, empty columns, datetime-like strings, or conflicting readings. |
| Implications | `REQ-S-02`, `REQ-S-04`, `REQ-S-05`. Object names remain [OPEN-004](#open-questions). Subtype taxonomy remains [OPEN-014](#open-questions). |
| Later update | [DEC-064](#dec-064) refines the stage list in this decision into the current conceptual pipeline, including observations, candidate assessments, resolution, an inferred interpretation, an optional override, and an effective interpretation. The distinction between physical dtype, observed characteristics, and semantic interpretation stands. Retained fields and sources stand. The pipeline is still not a frozen decomposition. The superseded part is the stage list as the current description. |

## DEC-042

| | |
| --- | --- |
| Title | User-facing confidence is High, Medium, or Low |
| Status | Accepted |
| Decision | User-facing confidence is High, Medium, or Low, together with concrete evidence. Do not expose pseudo-precise confidence such as `0.87321` unless a future statistically justified reason exists. Internal scores may help conflict resolution. They must not become unexplained user-facing precision. |
| Rationale | A long decimal implies a measurement the inference procedure does not have. |
| Implications | `REQ-S-02`. |
| Later update | [DEC-066](#dec-066) leaves the internal-score permission unused for Candidate Resolution v0.1. It does not delete that permission, and it does not ban a future statistically justified numeric confidence. High, Medium, and Low remain the user-facing resolution confidence. They are not a probability and not a candidate score. |

## DEC-043

| | |
| --- | --- |
| Title | Ambiguity stays visible |
| Status | Accepted |
| Decision | Pytics does not have to treat every semantic inference as certain. Uncertainty is exposed. A selected interpretation may carry medium or low confidence and a relevant alternative. The example of a `score` column read as numeric discrete, with ordinal categorical as an alternative because no order was supplied, is accepted product behavior. |
| Rationale | Hiding a plausible alternative presents a guess as a fact. |
| Implications | `REQ-S-02`, `REQ-S-04`. Ordinal policy is [DEC-052](#dec-052). |
| Later update | [DEC-067](#dec-067) defines a material alternative and represents current ambiguity as the selected interpretation, resolution confidence, and any material alternatives. The score-column illustration in this decision remains accepted product behavior. It does not resolve [OPEN-016](#open-questions), and it does not mean every compatible type is an alternative. Abstention is not introduced. `None` from the implemented rule chain stays control flow. |

## DEC-044

| | |
| --- | --- |
| Title | User semantic overrides |
| Status | Accepted as a capability. The API is not accepted. |
| Decision | Explicit semantic configuration for individual variables is a first-class capability. Explicit user intent normally takes precedence over inference. If the configured interpretation cannot be meaningfully applied to the observed data, Pytics reports the conflict. It does not silently coerce or repair the data. The exact API is not accepted. |
| Rationale | Professionals need to correct inference. A configuration that the data cannot support is itself a finding. |
| Implications | `REQ-S-06`. API shape remains [OPEN-004](#open-questions) and [OPEN-009](#open-questions). |
| Later update | [DEC-075](#dec-075) accepts inferred interpretation, then optional override, then effective interpretation, as direction. The API remains unaccepted. [OPEN-043](#open-questions) stays open. Exact Empty or Constant override behavior is [OPEN-049](#open-049). |

## DEC-045

| | |
| --- | --- |
| Title | No mutation or silent coercion |
| Status | Accepted |
| Decision | Pytics observes. It does not silently clean, repair, coerce, or mutate the user's original DataFrame. A mostly numeric string column that contains `"?"` must not have `"?"` rewritten as missing and then be presented as if the original column were clean numeric data. Pytics may detect numeric-like values, missing-like literals, and possible semantic interpretations. It preserves the distinction between source representation and analytical interpretation. |
| Rationale | Silent repair would make the report describe a dataset the user does not have. |
| Implications | `REQ-S-03`, `REQ-H-04`. This strengthens [DEC-007](#dec-007) and [DEC-015](#dec-015). It does not supersede them. |

## DEC-046

| | |
| --- | --- |
| Title | Empty and Constant are both interpretations and dataset facts |
| Status | Accepted |
| Decision | Empty and Constant are semantic interpretations and dataset or data-quality facts. All values missing means semantic interpretation Empty and a dataset fact that the column is empty. One unique non-missing value means semantic interpretation Constant and a dataset fact that the column is constant. Those two definitions take precedence over a Boolean, Numeric, or Identifier reading of the same column. The physical dtype remains inspectable. The architecture avoids duplicating the underlying computation unnecessarily. |
| Rationale | The two representations describe one observation. They should not be computed as unrelated truths. |
| Implications | `REQ-S-01`, `REQ-A-06`. |
| Later update | The current semantic system applies Empty, then Constant, before the implemented physical Boolean, Datetime, and Timedelta rules, as well as before a Numeric or Identifier reading. Physical dtype remains inspectable when Empty or Constant wins, including ordered categorical metadata. This note does not legislate an exhaustive precedence list for every future semantic reading. |
| Later update | [DEC-077](#dec-077) expresses those two dataset facts as `is_empty` and `is_constant` on the universal evidence value. The definitions are unchanged. A zero-length column and an all-missing column are empty and are not constant. |

## DEC-047

| | |
| --- | --- |
| Title | Boolean meaning is not binary cardinality |
| Status | Accepted |
| Decision | Boolean/Binary is a first-class analytical family. Binary cardinality does not automatically imply Boolean meaning. A physical pandas boolean is very strong Boolean/Binary evidence. `{0, 1}` may be a binary interpretation and is not automatically Boolean. Yes/no or true/false strings may be a binary interpretation under conservative token recognition. An arbitrary two-category variable stays categorical, including as a binary category, and is not described as Boolean. A column name may be weak supporting evidence and must never determine semantic type by itself. The exact subtype taxonomy is not accepted. |
| Rationale | Two distinct values are a cardinality fact. Boolean meaning needs stronger evidence. |
| Implications | `REQ-D-01`, `REQ-D-02`, `REQ-S-04`. Subtypes remain [OPEN-014](#open-questions). |
| Later update | [DEC-074](#dec-074) holds heuristic `{0, 1}` and string-token Binary inference until a binary-not-Boolean reading can be represented. That hold does not withdraw the permission in this decision, and it does not resolve [OPEN-014](#open-questions). `{0.0, 1.0}` is not accepted as binary evidence ([OPEN-046](#open-046)). Conservative true/false recognition may support a binary reading. Conservative yes/no recognition may be considered, more cautiously than true/false. Neither recognition may coerce or mutate the Series. Physical Boolean is very strong direct evidence. This note does not call it the strongest evidence of every kind. |

## DEC-048

| | |
| --- | --- |
| Title | Identifier evidence is a set of signals |
| Status | Accepted |
| Decision | Identifier is a first-class semantic type. Inference may use uniqueness ratio, duplicate count, missing count, UUID or GUID-like structure, hash-like structure, sequential integer patterns, fixed-width codes, alphanumeric code patterns, prefixes and suffixes, monotonic or sequential behavior, and column name as a weak supporting signal. That list is admissible evidence, not a closed detector. `unique_ratio == 1` alone is not sufficient. Identifiers are normally excluded from ordinary correlation, diagnostic target modeling, and ordinary multivariate anomaly modeling, unless explicitly configured otherwise. |
| Rationale | Uniqueness is common in small samples and in continuous measurements. Identifier treatment changes which analyses are meaningful. |
| Implications | `REQ-G-01` through `REQ-G-03`. Thresholds remain [OPEN-044](#open-questions). Exact eligibility rules remain [OPEN-043](#open-questions). |
| Later update | [DEC-068](#dec-068) states that Identifier is not a relational candidate-key definition, that perfect uniqueness and zero missingness are not definitional requirements, and that duplicates do not automatically disqualify Identifier. [DEC-069](#dec-069) requires positive Identifier evidence before a generic Numeric reading is displaced. [DEC-072](#dec-072) treats UUID-like and hash-like structure as evidence that is not automatically sufficient. The admissible-evidence list in this decision is unchanged and is not closed. |
| Later update | The phrase `unique_ratio == 1` in this decision is not a property name. The universal derived property is `unique_ratio_non_missing` ([DEC-077](#dec-077)). That property is not an Identifier rule. Thresholds remain [OPEN-044](#open-questions). |

## DEC-049

| | |
| --- | --- |
| Title | Numeric, categorical, and string semantics |
| Status | Accepted |
| Decision | A physically numeric column that is not better read as Empty, Constant, Boolean/Binary, or Identifier may be interpreted as Numeric. Numeric subtypes may include Continuous and Discrete. Integer dtype is not discrete, and float dtype is not continuous, without looking at the observed values. Subtype inference stays conservative. Categorical is a semantic interpretation, not a synonym for pandas `object`. A categorical variable may physically be a categorical dtype, a string, an object, or numeric codes. Low-cardinality numeric values are not assumed to be category codes without sufficient evidence or explicit configuration. Where evidence supports it, strings are distinguished as categorical-like, free text, identifier-like, URL-like, email-like, path-like, datetime-like, or generic string. Cardinality alone is insufficient. String evidence may include uniqueness, repetition, character-length distribution, word counts, token or pattern consistency, and structural patterns. |
| Rationale | Storage type and cardinality are evidence. They are not the semantic type. |
| Implications | `REQ-S-01`, `REQ-B-*`, `REQ-C-*`, `REQ-F-01`. The full subtype taxonomy remains [OPEN-014](#open-questions). Common-token diagnostics remain [OPEN-019](#open-questions). |
| Later update | [DEC-070](#dec-070) defines Categorical as a classification vocabulary. [DEC-071](#dec-071) defines Text as textual content and does not collapse generic string into Text. [DEC-069](#dec-069) keeps physical numeric dtype as meaningful Numeric evidence. [DEC-072](#dec-072) keeps detected pattern names as observations. |
| Later update | [DEC-081](#dec-081) records full-value UUID, IPv4, IPv6, and fixed-width hexadecimal token counts as pattern observations. Those counts do not assign the string roles listed in this decision. Email-like, URL-like, path-like, and datetime-like patterns are not part of that catalog. |
| Later update | [DEC-083](#dec-083) records candidate assessments for Numeric, Categorical, and Text. Physical integer or floating storage can support a Numeric candidate. Physical categorical storage can support a Categorical candidate. Current observations do not support a Text candidate. None of those assessments selects a reading. |

## DEC-050

| | |
| --- | --- |
| Title | Pattern detection does not convert the series |
| Status | Accepted |
| Decision | Pytics may detect strings that appear URL-like, email-like, UUID-like, path-like, datetime-like, or another well-defined structural form. Detection does not silently rewrite the source Series. For datetime-like strings, the physical source type remains string even when a semantic datetime interpretation is selected. Native pandas datetime and timezone-aware datetime dtypes are strong evidence of Datetime semantics. String-to-datetime inference is conservative and considers parse success, representation and format consistency, plausible ranges, ambiguity, and sampling or full-column verification. Arbitrary numeric-looking strings are not blindly read as dates. A datetime variable does not automatically imply a time series. |
| Rationale | A successful parse is an interpretation. The column the user holds is still strings until they change it. |
| Implications | `REQ-S-03`, `REQ-E-03`, `REQ-F-01`. Sampling thresholds remain [OPEN-010](#open-questions). |
| Later update | [DEC-072](#dec-072) records that a detected pattern name is an observation or role and does not automatically become the semantic type. Datetime-like strings still do not change the physical dtype, and no Series is rewritten. |

## DEC-051

| | |
| --- | --- |
| Title | Timedelta has dedicated duration analysis |
| Status | Accepted |
| Decision | Timedelta is a first-class semantic type with dedicated duration analysis. Analysis may reuse numeric concepts where appropriate and must preserve duration semantics and readable units. In-scope concepts include count, missing, min, max, range, mean, median, quantiles, distribution, zero durations, and negative durations. Those names are not a closed mandatory catalog. User-facing timedelta results are not reduced to raw nanoseconds. |
| Rationale | A duration is not an ordinary float, and a nanosecond integer is not a readable duration. |
| Implications | `REQ-S-07`. Whether each named statistic is always emitted stays with [OPEN-001](#open-questions). |

## DEC-052

| | |
| --- | --- |
| Title | Ordinal order must be explicit |
| Status | Accepted |
| Decision | Pytics does not freely infer ordinal ordering from arbitrary category labels. Ordinal semantics may be accepted when the user explicitly configures them, or when ordering is explicitly represented in the source data, for example an ordered pandas categorical dtype. Without that explicit ordering, values such as Low, Medium, and High remain categorical. Pytics does not invent semantic ordering. |
| Rationale | A human guess about label order is not metadata the dataset supplied. |
| Implications | `REQ-S-08`. When ordinal semantics are accepted, whether they are stored as their own type, a categorical subtype, or only a relationship case remains [OPEN-016](#open-questions). |
| Later update | `categorical_ordered` stays on the physical dtype. A later Categorical interpretation must not erase it. Empty or Constant does not erase it. The optional subtype string must not be used as if [OPEN-016](#open-questions) were resolved. The semantic-foundation consolidation does not add an Ordinal semantic type. |
| Later update | [DEC-083](#dec-083) may support a Categorical candidate for non-empty, non-constant physical categorical storage, including ordered storage. That candidate does not add an Ordinal semantic type, and it does not infer order from labels. [OPEN-016](#open-questions) stays open. |

## DEC-053

| | |
| --- | --- |
| Title | Semantic type guides eligibility |
| Status | Accepted as direction |
| Decision | Semantic interpretation guides which analyses are analytically meaningful. The examples below are direction, not a closed eligibility matrix. Identifier is typically eligible for a variable profile, missingness, and duplicate or identifier-quality analysis, and is normally excluded from ordinary correlation, target predictor modeling, and ordinary multivariate anomaly modeling. Numeric is normally eligible for distribution analysis, relationships, target relationships, and anomaly analysis. Text is eligible for text profiling and relevant quality or pattern analysis. Ordinary statistical relationships and target modeling for text are limited by default unless a meaningful method exists. Datetime is eligible for datetime profiling and for temporal analysis when genuine temporal structure exists. Timestamps are not converted to numbers and then treated as ordinary measurements. Exact eligibility rules belong to later method design. |
| Rationale | Running every method on every storage type produces results that are numerically defined and analytically meaningless. |
| Implications | `REQ-S-09`, `REQ-G-03`, `REQ-K-01`. Exact rules are [OPEN-043](#open-questions). |
| Later update | Where an override exists, downstream eligibility uses the effective interpretation where applicable ([DEC-075](#dec-075)). Physical facts still limit what can run without coercion. This note does not close [OPEN-043](#open-questions). |

## DEC-054

| | |
| --- | --- |
| Title | Semantic-inference sampling |
| Status | Accepted |
| Decision | Cheap evidence uses the full column where practical. Expensive evidence, particularly string and pattern analysis on very large data, may use controlled sampling. That sampling must be transparent, reproducible where possible, recorded, tied to the configured analysis mode, and considered when inference confidence is expressed. Exact thresholds and sample sizes are not accepted. |
| Rationale | Hidden sampling would make a semantic type look more certain than the evidence procedure was. |
| Implications | `REQ-P-12`, `REQ-IA-15`. Thresholds and sample sizes are [OPEN-010](#open-questions). |
| Later update | [DEC-076](#dec-076) adds procedure provenance and observe-once evidence collection. It does not choose sample sizes, and it does not close [OPEN-010](#open-questions) or [OPEN-044](#open-questions). |

## DEC-055

| | |
| --- | --- |
| Title | Relationship result and pair-type direction |
| Status | Accepted as direction. Not a closed method catalog. |
| Decision | A relationship separates description, effect, uncertainty, frequentist inference, Bayesian inference where appropriate, diagnostics, and method metadata. A relationship is not reduced to a p-value. Exact Python objects are not accepted. Accepted pair-type direction, still subject to validation during implementation design: numeric with numeric uses Spearman as a monotonic or rank perspective and Pearson as a linear perspective where applicable, plus uncertainty where methodologically appropriate, sample size, and missing-pair information. Pearson and Spearman are not treated as the same phenomenon. Deep analysis may add Kendall, bootstrap confidence intervals, permutation or resampling inference, and further robust or nonlinear diagnostics where justified. Numeric with binary includes per-group sample sizes, group descriptive statistics, observed group differences, an appropriate standardized effect, uncertainty, and frequentist evidence. Welch-family inference is currently preferred over blindly assuming equal variances. Robust or rank-based evidence may complement it. Numeric with categorical, for more than two groups, prioritizes group descriptive statistics, an overall relationship or effect, and an appropriate omnibus test. Every pairwise comparison is not dumped automatically. Post-hoc pairwise analysis belongs primarily in deeper analysis and uses appropriate multiple-testing control. Binary with binary is not reduced to chi-square significance. Relevant concepts include contingency counts, observed proportions, absolute proportion or risk difference, relative measures where meaningful, association strength, uncertainty, and frequentist evidence. This pair is a strong candidate for lightweight Bayesian analysis. Categorical with categorical uses contingency information, observed proportions, Cramér's V or another appropriate association-strength measure, and appropriate inferential evidence. Sparse or small tables may require exact or resampling alternatives. Extreme high-cardinality pairs are protected from meaningless or computationally explosive analysis. Identifiers are excluded by default. Datetime is not converted to integer timestamps and passed through ordinary correlation. Datetime with numeric focuses on meaningful temporal structure when justified, such as trend, change over time, temporal association, and periodic or seasonal structure where justified. Datetime with categorical may examine changes in category distribution or temporal patterns. A datetime column by itself does not establish a time-series context. Ordinal relationships apply only where [DEC-052](#dec-052) accepts ordinal semantics. |
| Rationale | Effect, uncertainty, and method are the interpretation. Pair type changes which of those quantities are meaningful. |
| Implications | `REQ-K-01`, `REQ-K-04`. This does not retire `REQ-K-03`. Exact formulas, selection rules, default binary-binary measures, datetime methods, and unlisted pair types remain [OPEN-006](#open-questions). [DEC-031](#dec-031) still keeps trend, seasonality, and autocorrelation off the default pass for every datetime column. Their scope remains [OPEN-020](#open-questions). |

## DEC-056

| | |
| --- | --- |
| Title | Multiple testing, no stars, assumptions as diagnostics |
| Status | Accepted as direction |
| Decision | Where multiple-testing correction applies, raw and adjusted p-values are distinct. False-discovery-rate control is the preferred default direction for broad relationship screening. Benjamini-Hochberg is the leading candidate. It is not an unconditional universal rule. The definition of a statistical test family inside Pytics is not accepted and must be designed before correction behavior is finalized. Pytics does not use significance-star conventions and does not label a tiny p-value as inherently highly important. Presentation prefers effect, uncertainty, adjusted or raw p-value where relevant, sample size, and context. Statistical assumptions are diagnostic context, not a gate. A normality test below a cutoff does not by itself invalidate a method, especially on large data. Where useful, Pytics may expose skew or distribution diagnostics, variance characteristics, robust or rank alternatives, method agreement or disagreement, and relevant limitations. Method selection stays explainable. |
| Rationale | Stars and assumption gates collapse effect, dependence among tests, and sample size into a label. |
| Implications | `REQ-P-10`, `REQ-K-05`. The test family remains [OPEN-007](#open-questions). |

## DEC-057

| | |
| --- | --- |
| Title | Bayesian analysis stays selective and lightweight |
| Status | Accepted |
| Decision | Bayesian analysis remains in scope and is selective. Prefer lightweight analytical or numerical Bayesian methods where they answer a data-understanding question, without a full probabilistic-programming framework. Useful outputs may include a posterior effect estimate, a credible interval, a directional probability such as `P(A > B)`, and the probability that an effect exceeds a meaningful threshold. Pytics does not invent a domain-specific meaningful threshold. Such a threshold comes from a defensible established convention or from explicit user configuration. Bayesian inference is not Bayesian predictive optimization. Binary-with-binary association is a strong candidate for a lightweight Bayesian analysis. The exact Bayesian catalog is not accepted. |
| Rationale | A probabilistic-programming stack would change the product's dependency and runtime shape in order to cover questions that do not all need it. |
| Implications | `REQ-P-11`. Catalog, which further analyses qualify, and the final library choice remain [OPEN-008](#open-questions). NumPy and SciPy are the current calculation direction in [DEC-060](#dec-060), not a pin. PyMC is not intended as a core dependency at present. |

## DEC-058

| | |
| --- | --- |
| Title | Analysis modes |
| Status | Accepted as a concept. Contents are not frozen. |
| Decision | The modes quick, standard, and deep are accepted. Standard is the intended default. Exact contents and thresholds are not frozen. Current direction: quick prioritizes inexpensive descriptive profiling, cheap associations, and important data-quality checks. Standard likely includes descriptive statistics, effect sizes, primary relationships, confidence intervals where appropriate, appropriate frequentist inference, multiple-testing correction, missing analysis, duplicate analysis, univariate outlier analysis, and controlled multivariate anomaly analysis. Deep may add further bootstrap or resampling, further robust alternatives, broader Bayesian inference, post-hoc analysis, deeper temporal analysis, more expensive anomaly analysis, and deeper drift inference. Those lists are not a closed catalog. The call signature that selects a mode is not accepted. |
| Rationale | One computation depth cannot serve both a quick look and a careful inferential pass. Naming the modes does not invent their budgets. |
| Implications | `REQ-P-16`, `REQ-IA-15`. Contents, thresholds, and sample sizes are [OPEN-010](#open-questions). Multiple-testing inside standard still depends on [OPEN-007](#open-questions). |

## DEC-059

| | |
| --- | --- |
| Title | Target analysis reuses relationships; diagnostic importance is permutational |
| Status | Accepted as direction. The estimator is not accepted. |
| Decision | Target analysis reuses the semantic interpretation and the shared relationship layer used elsewhere. A binary target's associations with other variables reuse that layer rather than a second statistical implementation. Target-specific behavior adds target distribution, imbalance, one diagnostic multivariate model, and potential leakage analysis. The diagnostic model is lightweight and untuned. Validation uses responsible holdout or cross-validation, not evaluation only on the training observations. Model output is for data understanding, not optimization. Held-out permutation importance is the primary feature-importance direction. Where applicable, uncertainty or spread across permutations is reported. Correlated predictors can share or obscure permutation importance, and the report says so. Model importance is never presented as causal importance. The model family for classification or regression is not accepted. Random Forest, Extra Trees, gradient boosting, and any other named estimator are not selected by this decision. |
| Rationale | A second relationship implementation would fork the statistical result. Impurity importance answers a different question from held-out permutation importance and is easier to over-read. |
| Implications | `REQ-L-02`, `REQ-L-04`, `REQ-L-05`, `REQ-L-07`, `REQ-T-05`. This supersedes the [DEC-018](#dec-018) implication that permutation importance was only a discussion. Estimator family remains [OPEN-013](#open-questions). Problem types beyond classification or regression remain [OPEN-023](#open-questions). |

## DEC-060

| | |
| --- | --- |
| Title | Dependency research produced candidates, not a lock |
| Status | Accepted |
| Decision | The ecosystem review's outcome is a candidate stack, not a dependency lock and not a set of version pins. Do not install those candidates from this decision. Do not edit `pyproject.toml` from this decision. Pandas is the DataFrame foundation required by [DEC-006](#dec-006) and [DEC-040](#dec-040); that is not a version pin. Current directions, none of which are pins: NumPy as the numeric foundation; SciPy as statistical primitives; statsmodels for advanced inference and diagnostics; NumPy and SciPy for lightweight Bayesian calculations; scikit-learn for the diagnostic model and as the candidate home for multivariate anomaly methods; Plotly as the interactive visualization engine; Jinja2 as the HTML templating engine; restrained custom JavaScript for HTML interactivity. PyMC is not intended as a core dependency at present. LightGBM is not currently intended as a core dependency. Polars is not core. PyArrow is not required merely for the core DataFrame API. IPython is likely not core and stays unresolved until a packaging review. Final versions remain open. |
| Rationale | Recording the review without labeling it a lock avoids both an empty dependency file and an accidental pin set. |
| Implications | `REQ-T-04`. This supersedes the part of [DEC-027](#dec-027) that said the review had not been done and that the named libraries carried no direction. The install-and-pin hold remains. Final versions are [OPEN-042](#open-questions). Rendering consequences are [DEC-061](#dec-061). Anomaly and diagnostic estimators remain [OPEN-022](#open-questions) and [OPEN-013](#open-questions). |

## DEC-061

| | |
| --- | --- |
| Title | HTML and PDF rendering direction |
| Status | Accepted as direction. Not a final dependency decision. |
| Decision | HTML rendering is structured results, then an HTML renderer using Jinja2 and Plotly, producing standalone HTML, CSS, and restrained JavaScript. Ordinary report generation does not require Dash, a web server, React, Vue, or a JavaScript build chain unless later evidence creates a compelling reason. Plotly is a rendering engine, not Pytics' visual design system. Pytics defines its own restrained visual grammar. The 1.1.5 xhtml2pdf path is not the Pytics 2.0 architecture. WeasyPrint is the leading candidate for professional HTML and CSS PDF layout and is not a final dependency. HTML and PDF share a design language and are not required to use identical markup. How interactive Plotly figures become reliable static PDF graphics, without fragile system dependencies, is unresolved. |
| Rationale | The report can be interactive HTML and a static PDF without becoming a web application. The static-chart bridge is a real packaging risk and is not solved by naming WeasyPrint. |
| Implications | `REQ-IA-18`, `REQ-IA-19`, `REQ-T-02`. Final libraries remain [OPEN-035](#open-questions). The Plotly static bridge is [OPEN-041](#open-questions). Kaleido is neither selected nor rejected. |

## DEC-062

| | |
| --- | --- |
| Title | Core analytical value models use frozen dataclasses |
| Status | Accepted |
| Decision | Pytics 2.0 core analytical result and value models use standard-library Python frozen dataclasses, enums, and explicit type hints where appropriate. Pydantic is not required for core analytical models. Loose dictionaries and TypedDict-only structures are not the preferred representation for core analytical facts. This does not mean every future Pytics object must be a frozen dataclass. Use frozen dataclasses where they represent value objects or analytical facts. Do not prematurely freeze mutable orchestration or configuration objects that do not yet exist. Do not add Pydantic for this purpose. |
| Rationale | The representation should be lightweight, explicit, inspectable, and friendly to IDEs and type checkers. Analytical facts should be immutable where that matches the fact. The analytical core should not take a framework dependency for its value objects. |
| Implications | TSK-001 uses this representation for physical dtype facts and semantic interpretation values. TSK-002 uses it for basic column evidence. TSK-003 reuses those values for the physical Boolean reading and does not add a value type. TSK-004 reuses those values for the physical Datetime reading and does not add a value type or timezone metadata on `PhysicalDtype`. TSK-005 reuses those values for the physical Timedelta reading and does not add a value type or duration-unit metadata on `PhysicalDtype`. TSK-006 keeps that basic-evidence value and does not add a value type. TSK-007 uses a frozen dataclass for frequency observations composed with basic column evidence. It does not add a semantic type or a public result type. Public result names remain [OPEN-004](#open-questions). Module layout remains [OPEN-045](#open-questions). `REQ-T-04` is unchanged: do not add a dependency for this choice. |
| Later update | The semantic-foundation consolidation did not add a value type and did not redesign `SemanticAlternative`. That value remains thinner than the material-alternative rationale in [DEC-067](#dec-067). |
| Later update | TSK-006 keeps `BasicColumnEvidence` as the frozen universal evidence value. Derived ratios and boolean facts are properties, not fields ([DEC-077](#dec-077)). No provenance value and no further evidence family were added. |
| Later update | TSK-007 adds `FrequencyEvidence` as a frozen observation value composed with `BasicColumnEvidence` ([DEC-078](#dec-078)). It is not a public result type. |
| Later update | TSK-008 adds `NumericStructureEvidence` as a frozen observation value composed with `BasicColumnEvidence` ([DEC-079](#dec-079)). It is not a public result type and not a semantic type. |
| Later update | TSK-009 adds `StringStructureEvidence` as a frozen observation value composed with `BasicColumnEvidence` ([DEC-080](#dec-080)). It is not a public result type and not a semantic type. |

## DEC-063

| | |
| --- | --- |
| Title | Build Pytics 2.0 in place inside `src/pytics` |
| Status | Accepted |
| Decision | Pytics 2.0 is built incrementally in place inside the existing `src/pytics` package. Existing Pytics 1.1.5 components remain temporarily intact until their Pytics 2.0 replacement has been specified, implemented, tested, and verified against the Pytics 2.0 specification. Temporary internal coexistence inside `src/pytics` is allowed. The final product must not contain a permanent second public package such as `pytics_v2`, `pytics2`, `legacy`, `old_pytics`, or `new_pytics`. Do not redirect the existing public `profile` / `compare` API except in a slice that explicitly requires that change. |
| Rationale | [DEC-039](#dec-039) already fixed the end state as one package. The missing piece was how 1.1.5 and 2.0 share that package during the work. A second public package would become the product. Deleting 1.1.5 before its replacement is verified would remove the baseline without a successor. |
| Implications | Resolves [OPEN-040](#open-040). TSK-001 adds internal modules under `src/pytics/semantics/` and does not delete or rewrite `profiler.py` or `visualizations.py`. TSK-002 adds basic column evidence and Empty/Constant inference in that same internal package, without changing `profile` or `compare`. TSK-003 adds physical Boolean inference there, still without changing `profile` or `compare`. TSK-004 adds physical Datetime inference in that same internal package, still without changing `profile` or `compare`. TSK-005 adds physical Timedelta inference in that same internal package, still without changing `profile` or `compare`. TSK-006 strengthens basic column evidence in that same internal package, still without changing `profile` or `compare`. TSK-007 adds frequency evidence in that same internal package, still without changing `profile` or `compare`. TSK-008 adds numeric-structure evidence in that same internal package, still without changing `profile` or `compare`. TSK-009 adds string-structure evidence in that same internal package, still without changing `profile` or `compare`. That directory is not a resolution of [OPEN-045](#open-questions). Unapproved slices still follow [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md). |

## DEC-064

| | |
| --- | --- |
| Title | Semantic inference follows a conceptual pipeline |
| Status | Accepted |
| Decision | The conceptual analytical pipeline is physical dtype, then observations and evidence, then candidate assessments, then resolution, then an inferred interpretation, then an optional user override, then an effective interpretation, then downstream analysis. This is not a frozen package, module, class, or function decomposition. The labels are not class names. It does not resolve [OPEN-045](#open-questions). It refines the stage list in [DEC-041](#dec-041). Physical metadata, basic observations, and pattern observations remain distinguishable inside the observations stage. Analysis still produces structured results before rendering ([DEC-025](#dec-025)). The diagram below is the ruling copy. The copies in [ANALYTICAL_SPEC.md](ANALYTICAL_SPEC.md) and [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) must match it. |
| Rationale | The earlier stage list stopped at semantic interpretation and did not separate observations from candidate assessments, or the inferred reading from the effective reading used downstream. |
| Implications | `REQ-S-04`, `REQ-S-05`, `REQ-T-01`. Object names remain [OPEN-004](#open-questions). This decision does not authorize a heuristic-inference slice. |
| Later update | [DEC-085](#dec-085) implements the resolution stage for facts already produced. It does not implement the inferred interpretation for a candidate-derived selection, the optional override, the effective interpretation, or downstream analysis. |
| Later update | [DEC-086](#dec-086) implements the inferred-result stage for a physical dtype and a resolution already produced. A structural resolution keeps its interpretation. A candidate-derived resolution does not receive a confidence-bearing interpretation. Insufficient evidence and ambiguity are inferred states. The optional override, the effective interpretation, and downstream analysis are not implemented. |
| Later update | [DEC-087](#dec-087) connects those stages for one Series, through the inferred result. The optional override, the effective interpretation, and downstream analysis remain unimplemented. The function and module are not a layout decision. |

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

## DEC-065

| | |
| --- | --- |
| Title | Observations are facts; absence of support is not contradiction |
| Status | Accepted |
| Decision | Observations are objective facts about the source data or the procedure used to inspect it. Examples, not a closed catalog, include physical dtype, missing count, unique count, cardinality, an observed small value set, frequency information, string lengths, pattern matches, monotonicity, sequence regularity, ordered categorical metadata, column name metadata, and sampling provenance. Observations do not decide semantic meaning by themselves. Candidate assessments interpret observations in support of possible semantic readings. The architecture must eventually distinguish supporting evidence, contradicting evidence, and evidence that does not bear on the candidate. This decision does not create an evidence-role enum and does not freeze an evidence object shape. Absence of support is not contradiction. No UUID pattern means Identifier lacked that support; it does not contradict Identifier. No repetition does not by itself contradict Categorical. No prose structure does not by itself contradict Text. A contradicting observation is positive evidence that conflicts with a specific claim of a candidate. Do not build a hidden negative-score system in which every absent signal counts against a candidate. |
| Rationale | Treating a missing signal as a vote against a candidate would turn an incomplete observation into a refutation. |
| Implications | `REQ-S-04`, `REQ-S-05`. The implemented evidence value remains one statement ([DEC-062](#dec-062)). Whether an evidence-strength enum is ever needed is [OPEN-048](#open-048). |
| Later update | [DEC-077](#dec-077) specifies the stored counts and derived facts of `BasicColumnEvidence`. It does not freeze other evidence shapes, create an evidence-role enum, or introduce a generic observation bag. |
| Later update | [DEC-079](#dec-079) records monotonicity of physically numeric columns as an observation. Sequence regularity is still not an observation. Neither fact decides a semantic type. |
| Later update | [DEC-080](#dec-080) records minimum and maximum string length, and character-class counts, as observations. Pattern matches are still not an implemented observation. None of these facts decides a semantic type. |
| Later update | [DEC-082](#dec-082) keeps supporting evidence and contradicting evidence as separate tuples of `SemanticEvidence` on a candidate assessment. Evidence that does not bear on the candidate is omitted. That split is not an evidence-role enum. [OPEN-048](#open-048) stays open. Absence of support remains not contradiction. |

## DEC-066

| | |
| --- | --- |
| Title | Candidate Resolution v0.1 does not use a numeric total-score |
| Status | Accepted. Narrows use of [DEC-042](#dec-042) for v0.1. Does not withdraw it. |
| Decision | Candidate Resolution v0.1 will not use an arbitrary numeric total-score such as Identifier = 82, Numeric = 54, Categorical = 31. It will not introduce an evidence-strength enum or pseudo-probabilities. User-facing resolution confidence remains High, Medium, and Low. Those words are not a displayed probability and not a candidate score. Evidence role, evidence strength, and resolution confidence are distinct. [DEC-042](#dec-042) still permits an internal score, and still permits a future statistically justified numeric confidence. That permission stays intact and unused. Reconsider scoring only if future concrete conflict cases show that explicit observations, candidate evidence roles, and resolution rules are insufficient. Implemented physical rules may continue to produce High because their procedure is direct and exact. A strong heuristic or a sampled observation does not automatically imply High. |
| Rationale | A total-score would look like a measurement the v0.1 procedure does not have, and it would hide the separate questions of role, strength, and resolution confidence. |
| Implications | `REQ-S-02`. This is a v0.1 scope limit, not a permanent ban. [OPEN-048](#open-048) stays open. [OPEN-044](#open-questions) stays open. |
| Later update | [DEC-082](#dec-082) does not assign High, Medium, or Low on a candidate assessment and does not introduce a numeric score. Those confidence words remain resolution confidence. |
| Later update | [DEC-085](#dec-085) does not assign High, Medium, or Low from the number of supported candidates, and it does not add a numeric total. A structural interpretation keeps the confidence it already carries. |
| Later update | [DEC-086](#dec-086) does not assign High, Medium, or Low from candidate support, from the number of supporting statements, or from the absence of contradiction. A structural interpretation keeps the confidence it already carries. No evidence-strength enum is added. |

## DEC-067

| | |
| --- | --- |
| Title | Ambiguity is a selected reading, confidence, and material alternatives |
| Status | Accepted |
| Decision | A material alternative is a competing interpretation that has its own positive evidence, survives the observations without requiring coercion, and remains plausible beside the selected interpretation. Theoretical compatibility is not enough. Every possible type is not an alternative. Downstream analytical impact may explain why an alternative is important to show. It does not define whether the alternative is material. The architecture must eventually preserve the rationale and evidence for material alternatives. The current `SemanticAlternative` value records type, an optional subtype label, and optional confidence, and does not record that rationale. This decision does not redesign that value. Current ambiguity is the selected interpretation, plus resolution confidence, plus any material alternatives. Do not introduce abstention now. Do not redefine `None`. In the implemented rule chain, `None` means that chain produced no interpretation. It must not silently become ambiguous, unknown, unsupported, conflicted, or abstained. A future abstention state may be reconsidered if concrete cases justify it. |
| Rationale | A list of every compatible type hides which competitors actually have evidence. A control-flow `None` is not an analytical conclusion that the column is ambiguous. |
| Implications | `REQ-S-02`, `REQ-S-04`. This refines [DEC-043](#dec-043) and does not withdraw its score-column illustration. That illustration does not resolve [OPEN-016](#open-questions). Abstention remains [OPEN-047](#open-047). |
| Later update | [DEC-085](#dec-085) represents insufficient evidence and unresolved competition as resolution statuses, without selecting a semantic type and without redefining `None` from the precedence chain. The direction in this decision, a selected interpretation plus confidence plus material alternatives, remains the later inferred-interpretation step. That step is not this resolution result. `SemanticAlternative` is not redesigned. |
| Later update | [DEC-086](#dec-086) keeps insufficient evidence and ambiguity as inferred states. Those states have no selected interpretation, no confidence, and no material alternatives. The direction in this decision remains the policy for a later case in which one reading is selected while another plausible reading is retained. It is not the representation of an unresolved result. Explicit unresolved states stay because current candidate evidence does not justify a confidence, and choosing one supported candidate in order to attach Low confidence would undo the abstention in [DEC-085](#dec-085). `SemanticAlternative` is still not redesigned. `None` from the precedence chain is still not redefined. |

## DEC-068

| | |
| --- | --- |
| Title | Identifier is not defined by uniqueness or completeness |
| Status | Accepted |
| Decision | Identifier is a semantic type, not a relational candidate-key definition. Perfect uniqueness is not sufficient and is not a definitional requirement. Zero missingness is not sufficient and is not a definitional requirement. Their weight remains future inference evidence and thresholds. Duplicates do not automatically disqualify Identifier. Duplicate identifiers may later become a quality finding. A column name may support Identifier and must never decide it alone. |
| Rationale | Uniqueness and completeness are observations. An identifier can repeat, and a unique measurement is not an identifier. |
| Implications | `REQ-G-01`, `REQ-G-02`, `REQ-S-04`. This narrows how the signals in [DEC-048](#dec-048) may be read. It does not remove them from the admissible list and does not close that list. Positive-evidence checklists and thresholds remain [OPEN-044](#open-questions). |
| Later update | [DEC-077](#dec-077) decides the denominator of the universal derived property `unique_ratio_non_missing`. Identifier uniqueness thresholds, and any other use of uniqueness, remain [OPEN-044](#open-questions). |
| Later update | [DEC-082](#dec-082) does not treat uniqueness or zero missingness as Identifier candidate support, and does not treat duplicates as contradiction of that candidate. |

## DEC-069

| | |
| --- | --- |
| Title | Identifier needs positive evidence to displace Numeric |
| Status | Accepted |
| Decision | A physically numeric column may be interpreted as Numeric when it is not better read as Empty, Constant, Boolean/Binary, or Identifier, as [DEC-049](#dec-049) already says. Physical numeric dtype is meaningful evidence. Do not require an additional positive heuristic before Numeric is available merely because the dtype is numeric. Identifier requires positive Identifier evidence before it displaces that generic Numeric reading. Uniqueness alone is not enough. When the selected reading remains uncertain, preserve a material competing interpretation and an appropriate confidence. Do not introduce abstention. The semantic engine precedes downstream statistical analysis. Do not casually recycle downstream Numeric outputs such as mean, skewness, kurtosis, or histogram shape as ad hoc Identifier detectors. If future semantic evidence legitimately requires a descriptive numeric observation, that use must be an explicit semantic-inference decision rather than accidental reuse of downstream analysis. |
| Rationale | A numeric column is already numeric evidence. Identifier should displace it only with its own positive case, not with a downstream statistic borrowed for a different purpose. |
| Implications | `REQ-S-01`, `REQ-G-01`. The detector catalog in [DEC-048](#dec-048) stays open. Thresholds remain [OPEN-044](#open-questions). |
| Later update | [DEC-079](#dec-079) adds numeric-structure observations for physically numeric columns. Those observations do not by themselves select Numeric, and they do not supply the positive Identifier evidence this decision requires. |
| Later update | [DEC-082](#dec-082) does not treat uniqueness, integer-like values, or monotonicity as positive Identifier evidence. It does not reconstruct regular-step evidence. |
| Later update | [DEC-083](#dec-083) may support a Numeric candidate from non-empty, non-constant physical integer or floating storage, including a sequence such as `1, 2, 3, 4, 5`. That support does not select Numeric and does not supply the positive Identifier evidence this decision requires. Regular-step evidence is still not reconstructed. |
| Later update | [DEC-085](#dec-085) does not implement the displacement in this decision as a resolver rule. When Numeric and Identifier are both supported, the result stays ambiguous. The requirement for positive Identifier evidence is unchanged. |

## DEC-070

| | |
| --- | --- |
| Title | Categorical means a classification vocabulary |
| Status | Accepted |
| Decision | Categorical means that values function as a classification vocabulary. It is not synonymous with pandas `object` or with pandas `category`. Storage may be category, string, object, numeric code, or another compatible representation. Repetition supports a categorical reading and is not required. Cardinality alone does not establish Categorical. Low cardinality alone does not establish it. High cardinality does not remove Categorical meaning. Singleton categories remain possible. Charting and contingency cost limits do not redefine the semantic type. Arbitrary two-category label variables are Categorical rather than Boolean. Do not define Categorical as recurring values. |
| Rationale | Recurrence and low cardinality are observations about a vocabulary. They are not the vocabulary's semantic role. |
| Implications | `REQ-C-01`, `REQ-S-01`. This clarifies [DEC-049](#dec-049). Distinctions from Text and Identifier are [DEC-071](#dec-071) and [DEC-072](#dec-072). Subtype taxonomy remains [OPEN-014](#open-questions). No cardinality threshold is set ([OPEN-044](#open-questions), [OPEN-018](#open-questions)). |
| Later update | [DEC-083](#dec-083) supports a Categorical candidate from non-empty, non-constant physical categorical storage. Repetition remains support that is not sufficient. No cardinality threshold is approved, so untyped string repetition and low-cardinality numeric values do not support that candidate. |
| Later update | [DEC-084](#dec-084) records token-vocabulary counts. Repetition of a token inside string values remains support that is not sufficient. It does not support a Categorical candidate for ordinary strings. |

## DEC-071

| | |
| --- | --- |
| Title | Text means textual content |
| Status | Accepted |
| Decision | Text means that values primarily function as textual content. Text is not defined by string dtype. Possible inference evidence includes length structure, word counts, whitespace, line breaks, lexical or textual structure, pattern regularity, and repetition, where the contract already allows that evidence. Semantic inference evidence stays separate from downstream text-profile diagnostics. Do not introduce NLP models, embeddings, language models, or language detection into core semantic inference. Do not collapse every generic string role into Text. Cardinality alone never distinguishes Categorical from Text. Repetition supports Categorical and is not sufficient. Long, multi-word, or prose-like structure may support Text. High uniqueness alone does not imply Text. High cardinality alone does not imply Text. A pandas categorical dtype is physical and source evidence and does not automatically override contradictory semantic evidence. High-cardinality Categorical remains possible. Text inference does not require NLP. This decision does not choose length, word-count, repetition, or cardinality thresholds. |
| Rationale | String storage, cardinality, and repetition each fail to identify textual content, and a language model would change what core inference is. |
| Implications | `REQ-F-01`, `REQ-F-03`. Generic string, and where it sits beside other string roles, remains [OPEN-014](#open-questions). Common-token diagnostics remain [OPEN-019](#open-questions). Thresholds remain [OPEN-044](#open-questions). |
| Later update | [DEC-080](#dec-080) records length bounds, whitespace, and character classes as string-structure observations. Those observations do not by themselves select Text. Word counts and length thresholds remain undecided. |
| Later update | [DEC-083](#dec-083) does not support a Text candidate from those observations, from string dtype, or from prose-like appearance. The permission that long, multi-word, or prose-like structure may support Text remains, and no threshold is chosen. [OPEN-019](#open-questions) and [OPEN-044](#open-questions) stay open. |
| Later update | [DEC-084](#dec-084) records alphanumeric token runs, a zero/one/multiple-token partition, total character count, and aggregate token-vocabulary counts. Those observations do not support a Text candidate. One token in every string, and several tokens in a string, are not that support. No length or token-count threshold is chosen. [OPEN-019](#open-questions) and [OPEN-044](#open-questions) stay open. |

## DEC-072

| | |
| --- | --- |
| Title | A structural pattern name is not the semantic type |
| Status | Accepted |
| Decision | Structural pattern detection produces observations first. The detected pattern name does not automatically become the final semantic type. UUID-like, hash-like, email-like, URL-like, path-like, and datetime-like are observations or roles. UUID-like and hash-like structure are accepted Identifier evidence and are not automatically sufficient for Identifier. Email-like, URL-like, and path-like structure do not automatically imply Identifier. Datetime-like string detection does not change the physical dtype. No Series is rewritten. Uniqueness alone does not distinguish Text from Identifier. Stable structural regularity may support Identifier. Prose-like structure supports Text and may contradict a specific code-like Identifier claim. It does not make every Identifier role impossible. Fixed width is evidence only. Repeated identifier-like strings may remain Identifier. All-unique free text may remain Text. Repeated entity keys can remain Identifier, and repeated labels can be Categorical, so repetition alone cannot distinguish them. Identifier needs evidence of an identity, key, or code role, not merely high cardinality. Categorical needs evidence of a label or classification role, not merely low cardinality. The same code can have different semantic roles in different datasets. A country code or an SKU may be a classification attribute in one dataset and an entity key in another. That illustration is not a detection rule. This decision does not choose pattern-agreement thresholds. |
| Rationale | A pattern match is evidence about form. The semantic role still has to be resolved, and the source Series stays what the user holds. |
| Implications | `REQ-S-03`, `REQ-F-01`, `REQ-G-02`. This clarifies [DEC-050](#dec-050) and [DEC-048](#dec-048). Where URL-like, email-like, path-like, and generic string live in the subtype taxonomy remains [OPEN-014](#open-questions). Whether UUID-like or hash-like structure can ever be sufficient alone remains [OPEN-044](#open-questions). |
| Later update | [DEC-080](#dec-080) does not detect structural patterns. A character such as `@` or `/` may increment an other-character count. That count is not a pattern name and does not select Identifier. |
| Later update | [DEC-081](#dec-081) records separate full-value counts for UUID syntax, IPv4, IPv6, and fixed-width ASCII hexadecimal tokens. A compact UUID may increment both the UUID count and the 32-character hexadecimal count. Those counts are observations. They do not select Identifier. The hexadecimal counts are not hash-algorithm names. Email, URL, path, and datetime-like patterns are not in that catalog. Whether UUID-like or hash-like structure can be sufficient alone remains [OPEN-044](#open-questions). |
| Later update | [DEC-082](#dec-082) accepts a full non-missing population of UUID syntax, or of one supported fixed-width ASCII hexadecimal width, as sufficient for an Identifier candidate assessment of SUPPORTED. That assessment is not a selected Identifier interpretation. A partial population, a mixture of patterns, and IP syntax are not that support. Whether a partial pattern can support a candidate, and whether any of these facts can select Identifier, remains [OPEN-044](#open-questions). |

## DEC-073

| | |
| --- | --- |
| Title | Some roles cannot be resolved from one Series |
| Status | Accepted |
| Decision | Some semantic roles cannot be reliably resolved from one Series alone. Column-local observations may make more than one interpretation plausible and cannot always observe dataset role. Examples of that limit, not detection rules: `customer_id` on transaction rows versus `customer_id` as an entity key; a country code as an attribute versus as the entity; an SKU on order lines versus in a product master; an email as a contact attribute versus as an account identity. The architecture must leave room for future dataset-context evidence beside column-local evidence. This decision does not implement cross-column inference, functional-dependency discovery, candidate-key mining, or schema-graph inference. User configuration remains the accepted current mechanism for context the column cannot justify. |
| Rationale | The same values can be an attribute in one table and an entity key in another. One Series does not contain that distinction. |
| Implications | `REQ-S-04`, `REQ-S-06`. Configuration shape remains [OPEN-009](#open-questions). This does not authorize a cross-column slice. |

## DEC-074

| | |
| --- | --- |
| Title | Heuristic binary inference waits on a binary-not-Boolean representation |
| Status | Accepted. Does not resolve [OPEN-014](#open-questions). |
| Decision | The contract allows a binary interpretation that is not necessarily Boolean ([DEC-047](#dec-047)). The current `SemanticType.BOOLEAN` cannot fully express that distinction. Heuristic `{0, 1}` or string-token Binary inference must not be implemented until the architecture can represent a binary-not-Boolean reading without mislabeling it. This decision does not choose whether Binary becomes a semantic type, a subtype, a semantic property, or another representation, and it does not add a `SemanticType` member. Physical pandas Boolean, when the column is not Empty and not Constant, remains the implemented Boolean reading at High confidence with physical-dtype provenance. That is very strong direct evidence. It is not a claim that physical Boolean is the strongest evidence of every kind. `{0.0, 1.0}` is not accepted as binary evidence. Two unique values alone do not establish Boolean meaning. Conservative true/false recognition may support binary semantics. Conservative yes/no recognition may be considered, more cautiously. String or token recognition never coerces or mutates the Series. A column name may support binary semantics and must never decide it. Do not grow a large language or domain dictionary of binary token pairs in core. |
| Rationale | Implementing a binary heuristic into `SemanticType.BOOLEAN` would report a binary-not-Boolean column as Boolean. |
| Implications | `REQ-D-01`, `REQ-D-02`. The permission in [DEC-047](#dec-047) remains. The hold is about when a heuristic may be implemented. `{0.0, 1.0}` remains [OPEN-046](#open-046). Representation remains [OPEN-014](#open-questions). |
| Later update | [DEC-083](#dec-083) may support a Numeric candidate for non-empty, non-constant `{0, 1}` integer storage and for `{0.0, 1.0}` floating storage. It does not infer Boolean or Binary from those values, and it does not infer Categorical from two string labels. [OPEN-014](#open-questions) and [OPEN-046](#open-046) stay open. |

## DEC-075

| | |
| --- | --- |
| Title | An override yields an effective interpretation and keeps the inferred one |
| Status | Accepted as architectural direction. The API is not accepted. |
| Decision | The direction is inferred interpretation, then an optional user override, then effective interpretation. A future override architecture must preserve the original inferred interpretation rather than silently rewriting history. User intent normally takes precedence where the requested interpretation is meaningfully applicable ([DEC-044](#dec-044)). Downstream analysis uses the effective interpretation where applicable. An override never erases physical or source facts. An override never authorizes coercion or mutation ([DEC-045](#dec-045)). Conflicts must be reportable. Removing an override should conceptually restore the inferred interpretation. An interactive renderer must not become a second analytical engine ([DEC-025](#dec-025)). Changing the semantic interpretation may require re-analysis because eligibility can change. Future reproducible configuration should be able to carry semantic overrides. Effective interpretation expresses the requested or active semantic reading. Physical applicability and immutable dataset facts still determine which analyses can actually run without coercion. A numeric Identifier overridden toward Numeric can enable Numeric analysis when the values are already physically numeric. UUID strings overridden toward Numeric cannot create valid Numeric analysis without coercion. Empty overridden toward Text cannot create textual content. A physical Boolean overridden toward Categorical may permit categorical frequency analysis without mutating values. |
| Rationale | If the override replaces the inferred reading in place, the report can no longer show what Pytics concluded or restore it. If the override ignores physical facts, analysis would require coercion. |
| Implications | `REQ-S-06`, `REQ-S-03`, `REQ-S-09`. These principles are accepted direction. The result object remains [OPEN-004](#open-questions). The configuration object remains [OPEN-009](#open-questions). The eligibility matrix remains [OPEN-043](#open-questions). Exact error and warning behavior is not frozen. Exact Empty or Constant override behavior is [OPEN-049](#open-049). This decision does not design an API or an HTML control. |

## DEC-076

| | |
| --- | --- |
| Title | Evidence keeps procedure provenance and is observed once |
| Status | Accepted |
| Decision | Evidence should eventually preserve procedure provenance. Conceptually this may include whether the procedure was exact and full-column or sampled, the sample size, the population size, the seed, and the method. This decision does not freeze those fields. Exact versus sampled belongs to provenance. Sampling can affect resolution confidence. Sampling does not itself make an interpretation true or false. Conceptual cost layering, not a module layout, is: level 0, physical metadata; level 1, cheap universal evidence; level 2, type-family evidence; level 3, candidate-specific evidence; level 4, expensive or deep evidence. Observe once, interpret many. Shared observations should be reusable by multiple candidate assessments. Avoid an architecture in which every candidate independently rescans the Series for missingness, value counts, string lengths, patterns, or monotonicity. This decision does not design a cache API. |
| Rationale | Hidden or repeated scans would make confidence depend on an unstated procedure and would redo the same facts for every candidate. |
| Implications | `REQ-P-12`, `REQ-S-05`, `REQ-IA-15`. This extends [DEC-054](#dec-054) and does not change its sampling permission. Sample sizes remain [OPEN-010](#open-questions). Thresholds remain [OPEN-044](#open-questions). Module layout remains [OPEN-045](#open-questions). The same cost list is described in [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md). If the copies diverge, this decision is the ruling. |
| Later update | The four universal counts are definitionally exact, full-column, and unsampled ([DEC-077](#dec-077)). They do not carry a provenance object. A reusable provenance model still waits for a second procedure, such as sampled evidence. This note does not freeze provenance fields and does not close [OPEN-010](#open-questions). |
| Later update | Frequency evidence is also exact, full-column, and unsampled, and it is collected only when requested ([DEC-078](#dec-078)). It does not add a provenance object. Observe once means a needed observation is computed once and shared. It does not mean every observation is computed eagerly. A reusable provenance model still waits for a procedure that can vary, such as sampled evidence. |
| Later update | Numeric-structure evidence is also exact, full-column, and unsampled, and it is collected only when requested ([DEC-079](#dec-079)). It does not add a provenance object. The same observe-once rule applies: compute the observation when a consumer needs it, and do not compute it eagerly from the current precedence chain. |
| Later update | String-structure evidence is also exact, full-column, and unsampled, and it is collected only when requested ([DEC-080](#dec-080)). It does not add a provenance object. The same observe-once rule applies. |
| Later update | Pattern evidence is also exact, full-column, and unsampled, and it is collected only when requested ([DEC-081](#dec-081)). It does not add a provenance object. Collecting string-structure evidence does not collect pattern evidence. The same observe-once rule applies. |
| Later update | The Identifier candidate assessor in [DEC-082](#dec-082) consumes observations already collected. It does not rescan the Series for missingness, frequencies, numeric structure, string structure, or patterns, and it does not classify the physical dtype again. The precedence chain does not call it. |
| Later update | The Numeric, Categorical, and Text candidate assessors in [DEC-083](#dec-083) also consume observations already collected. They use the same bundle identity checks. They do not rescan the Series, and the precedence chain does not call them. |
| Later update | String-content evidence is also exact, full-column, and unsampled, and it is collected only when requested ([DEC-084](#dec-084)). It does not add a provenance object. Collecting string-structure evidence does not collect it. The candidate assessors do not collect it. The same observe-once rule applies. |
| Later update | The resolver in [DEC-085](#dec-085) consumes a structural interpretation and candidate assessments already produced. It does not recollect observations and it does not call the assessors. |
| Later update | The inferred-result constructor in [DEC-086](#dec-086) consumes a physical dtype and a resolution already produced. It does not recollect observations, call the assessors, or call the resolver. |
| Later update | [DEC-087](#dec-087) classifies physical dtype once and collects basic evidence once, then reuses those objects. Structural readings do not collect frequency, numeric-structure, string-structure, pattern, or string-content evidence. Frequency evidence is still not collected on the candidate path, because no current assessor reads it. Eligible string populations collect string structure once and pass that same object to pattern evidence and string-content evidence. |
| Later update | [DEC-088](#dec-088) keeps that single column path and retains the evidence it collects. Frequency evidence and string-content evidence are still not collected. Eligible string populations still share one string-structure object with pattern evidence. Observe once still does not mean every evidence family is computed before a consumer needs it. |

## DEC-077

| | |
| --- | --- |
| Title | Universal column evidence stores primary counts and derives the rest |
| Status | Accepted |
| Decision | Analytical observations use typed evidence families, composed as needed. The core model is not a generic observation property bag. `BasicColumnEvidence` is the universal family. Later families, when a slice authorizes them, are separate typed values. This decision does not name those families, does not create them, and does not establish inheritance among them. The universal family stores four primary counts: `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing`. Each count is retained even when another count is mathematically related. The four counts are exact, full-column, and unsampled. Derived convenience facts are read-only computations from those counts and are not a second stored source of truth. `missing_ratio` is `n_missing / n_total` when `n_total > 0`, and `None` when `n_total == 0`. `unique_ratio_non_missing` is `n_unique_non_missing / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`. An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. There is no `unique_ratio` alias. `has_missing` is `n_missing > 0`. `is_empty` is `n_non_missing == 0`. `is_constant` is `n_non_missing > 0` and `n_unique_non_missing == 1`. A zero-length column and an all-missing column are empty and are not constant. One repeated non-missing value is constant, including when missing observations are also present, and including a one-row non-missing column. Empty and Constant interpretation uses `is_empty` and `is_constant`. This decision does not add a semantic type, a provenance object, or a semantic-inference threshold. |
| Rationale | The four counts are the observed facts. A ratio with a zero denominator is undefined, and storing a second copy of a derived fact would let it drift from the counts. A property bag would erase the distinction between evidence families. A provenance object has nothing to vary until a second procedure exists. |
| Implications | `REQ-S-03`, `REQ-S-05`. Empty and Constant definitions in [DEC-046](#dec-046) are unchanged. This decision sets only the denominator of `unique_ratio_non_missing`. Identifier thresholds remain [OPEN-044](#open-questions). Procedure provenance remains [DEC-076](#dec-076) and is not implemented here. Module layout remains [OPEN-045](#open-questions). No later evidence family is authorized. |
| Later update | TSK-007 adds `FrequencyEvidence` as one composed family ([DEC-078](#dec-078)). This decision still does not establish inheritance or a property bag. TSK-007 itself authorized no family beyond that one. |
| Later update | TSK-008 adds `NumericStructureEvidence` as one further composed family ([DEC-079](#dec-079)). This decision still does not establish inheritance or a property bag. No family beyond basic evidence, frequency evidence, and numeric-structure evidence is authorized. |
| Later update | TSK-009 adds `StringStructureEvidence` as one further composed family ([DEC-080](#dec-080)). This decision still does not establish inheritance or a property bag. No family beyond basic evidence, frequency evidence, numeric-structure evidence, and string-structure evidence is authorized. |
| Later update | TSK-010 adds `PatternEvidence` as one further family, composed with `StringStructureEvidence` rather than copied from `BasicColumnEvidence` ([DEC-081](#dec-081)). This decision still does not establish inheritance or a property bag. No family beyond basic evidence, frequency evidence, numeric-structure evidence, string-structure evidence, and pattern evidence is authorized. |
| Later update | TSK-011 adds a candidate assessment ([DEC-082](#dec-082)). It is not an evidence family and does not change the stored universal counts. |
| Later update | TSK-012 adds Numeric, Categorical, and Text candidate assessments ([DEC-083](#dec-083)). They are not evidence families and do not change the stored universal counts. |
| Later update | TSK-013 adds `StringContentEvidence` as one further family, composed with `StringStructureEvidence` rather than copied from `BasicColumnEvidence` ([DEC-084](#dec-084)). This decision still does not establish inheritance or a property bag. No family beyond basic evidence, frequency evidence, numeric-structure evidence, string-structure evidence, pattern evidence, and string-content evidence is authorized. |

## DEC-078

| | |
| --- | --- |
| Title | Frequency evidence observes non-missing values and does not interpret them |
| Status | Accepted |
| Decision | `FrequencyEvidence` is a typed observation family composed with `BasicColumnEvidence`. It is not a subclass of that family and not a generic property bag. No further evidence family is named or authorized. The frequency population is non-missing observations only. Missing values are not frequency keys. Unobserved categorical levels, which a count table can list at zero, are not frequency keys either. `n_missing`, `missing_ratio`, and `has_missing` stay on the universal family and are not copied. The collector uses `n_non_missing` and `n_unique_non_missing` from the composed basic evidence and does not define those counts again. Stored frequency observations are `most_frequent_count`, `singleton_count`, and a bounded exact set of distinct non-missing values. `most_frequent_count` is an integer. It is `0` when there is no non-missing observation, and otherwise the largest occurrence count, at least `1`. `singleton_count` is an integer. It is `0` when there is no non-missing observation, and otherwise the number of distinct non-missing values that occur once. Neither count is `None`. `most_frequent_ratio` is `most_frequent_count / n_non_missing` when `n_non_missing > 0`, and `None` when `n_non_missing == 0`. `singleton_ratio` is `singleton_count / n_unique_non_missing` when `n_unique_non_missing > 0`, and `None` when `n_unique_non_missing == 0`. The denominator of `singleton_ratio` is the number of distinct non-missing values, not the number of rows. There is no second singleton ratio. An undefined ratio is `None`. It is not `0.0`, `1.0`, NaN, or infinity. The v0.1 representation retains that exact distinct-value set only when `n_unique_non_missing` is at most 32. The empty population retains an empty immutable set because that set is known. Above 32 distinct non-missing values, the exact set is absent, represented by `None`, and the full frequency mapping is not retained. Computation may inspect exact frequencies temporarily. The stored result stays bounded apart from the scalar counts. The value 32 is one named storage limit, `EXACT_DISTINCT_VALUE_RETENTION_LIMIT`. It is not a semantic threshold. It does not mean categorical, binary, identifier, text, low cardinality, high cardinality, or suitability for a chart or a contingency table. The retained values are not sorted and are not stringified. Values that Python treats as equal, including `True` and `1`, remain one frequency key as pandas groups them. Unhashable non-missing values still fail. A frequency pass does not stringify, freeze, or omit them in order to succeed where basic evidence fails. These observations are exact, full-column, and unsampled. There is no sketch, reservoir, or approximate cardinality. There is no provenance object: this procedure does not vary. The family is collected when requested. The implemented Empty, Constant, and physical-type chain does not collect it. Observe once means a needed observation is computed once and shared. It does not mean every observation is computed before a candidate needs it. These facts do not select Categorical, Identifier, Text, Numeric, Boolean, or Binary. They carry no High, Medium, or Low confidence and no evidence role. |
| Rationale | Candidate assessment needs compact frequency facts that cannot drift from the universal counts. A complete high-cardinality table would make the evidence object unbounded. A semantic label on the same object would collapse observation into interpretation. Eager collection would make every current reading pay for a fact it does not use. |
| Implications | `REQ-S-03`, `REQ-S-05`. Empty and Constant definitions in [DEC-046](#dec-046) and [DEC-077](#dec-077) are unchanged. This decision does not close [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), or [OPEN-049](#open-049). The retention limit does not answer high cardinality, near-constant, or any inference cutoff. No later slice is approved. |
| Later update | TSK-008 adds `NumericStructureEvidence` as a separate composed family ([DEC-079](#dec-079)). The sentence above, that no further family is authorized, is the TSK-007 scope. It does not forbid that later family. [DEC-090](#dec-090) requests this family from `analyze_series` for a non-structural physical categorical column and retains the collector's object. The collector contract, including the 32-value retention bound, is unchanged. Structural columns, numeric columns, and ordinary strings still do not collect it. The facts still do not select a semantic type. |

## DEC-079

| | |
| --- | --- |
| Title | Numeric structure evidence observes real numeric columns and does not interpret them |
| Status | Accepted |
| Decision | `NumericStructureEvidence` is a typed observation family composed with `BasicColumnEvidence`. It is not a subclass of that family and not a generic property bag. No further evidence family is named or authorized. It applies only when the physical family is integer or floating, including the nullable integer and floating dtypes the physical classifier already places in those families. Physical Boolean is excluded, including when a numeric predicate would accept `bool`. Datetime, timezone-aware Datetime, Timedelta, categorical, string, object, Period, complex, and any other family are excluded. Calling the collector on an excluded family raises `TypeError`. The collector does not coerce the Series and does not parse numeric-looking strings. `n_total`, `n_missing`, and `n_non_missing` stay on the universal family and are not copied. Stored observations are `finite_count`, `positive_count`, `negative_count`, `zero_count`, `positive_infinity_count`, `negative_infinity_count`, `integer_like_count`, `non_integer_like_count`, `is_non_decreasing`, and `is_non_increasing`. Counts are integers and are never `None`. They cover non-missing observations only. A missing NaN or `pd.NA` is missing, not non-finite numeric evidence. Finite values and the two infinities partition `n_non_missing`. Sign counts partition finite values only: positive means `x > 0`, negative means `x < 0`, and zero means `x == 0`, with `0` and `-0.0` both zero. Infinities are not sign counts. A finite value is integer-like exactly when it equals its truncation. There is no tolerance and no rounding. Infinities are neither integer-like nor non-integer-like. Those two counts partition `finite_count`. `finite_ratio` is `finite_count / n_non_missing` when `n_non_missing > 0`, and `None` otherwise. `positive_ratio`, `negative_ratio`, `zero_ratio`, and `integer_like_ratio` each divide the named count by `finite_count` when `finite_count > 0`, and are `None` when `finite_count` is zero. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. A zero numerator with a positive denominator is `0.0`. Monotonicity is a bool only when every non-missing value is finite. If any non-missing value is infinite, both flags are `None`, including a constant infinity. Missing values are not positions in the sequence. The remaining finite values keep their original row order. Zero non-missing values, one finite value, and a finite constant series are both non-decreasing and non-increasing. Those degenerate cases are structural facts only. This decision does not record a step size, a gap, or a sequence role. It does not add min, max, mean, median, mode, variance, a quantile, or any other downstream numeric summary. The observations are exact, full-column, and unsampled. There is no provenance object. The family is collected when requested. The implemented Empty, Constant, and physical-type chain does not collect it. These facts do not select Numeric, Identifier, Boolean, Binary, Categorical, discrete, or ordinal. They carry no High, Medium, or Low confidence and no evidence role. |
| Rationale | Candidate assessment needs structural facts about a physically numeric column that cannot drift from the universal counts. Sign facts must not mix ordinary measurements with infinities. An integer-like float is an observation about the value, not a decision that the column is discrete, binary, or an identifier. Eager collection would make every current reading pay for a fact it does not use. Downstream numeric summaries answer a different question and stay outside this family. |
| Implications | `REQ-S-03`, `REQ-S-05`. Empty and Constant definitions in [DEC-046](#dec-046) and [DEC-077](#dec-077) are unchanged. This decision does not complete `REQ-B-01` or `REQ-A-07`. It does not close [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), or [OPEN-049](#open-049). Integer-like counts do not decide Continuous or Discrete. `{0.0, 1.0}` is not accepted as binary evidence. Monotonicity is not a sequential-identifier rule. Regular-step semantics, including gaps, duplicates, descending sequences, floating precision, missing observations, and irregular sampling, are not decided. No later slice is approved. |
| Later update | TSK-009 adds `StringStructureEvidence` as a separate composed family ([DEC-080](#dec-080)). The sentence above, that no further family is authorized, is the TSK-008 scope. It does not forbid that later family. |
| Later update | [DEC-083](#dec-083) may read physical integer or floating storage as support for a Numeric candidate. Numeric-structure counts remain context. They do not add a finite, sign, integer-like, or monotonicity cutoff, and they do not select Numeric. Complex storage stays outside that candidate. |

## DEC-080

| | |
| --- | --- |
| Title | String structure evidence observes string shape and does not interpret it |
| Status | Accepted |
| Decision | `StringStructureEvidence` is a typed observation family composed with `BasicColumnEvidence`. It is not a subclass of that family and not a generic property bag. No further evidence family is named or authorized. Pattern evidence is not this family. It applies to a physical string dtype, including the pandas string storage variants the physical classifier already places in that family. Python-backed and Arrow-backed string storage are not given different semantic treatment. An all-missing or zero-length physical string column remains eligible, because the dtype is positive evidence that the values are strings. Its counts are then zero, its ratios are undefined, and both length bounds are undefined. An object column is eligible only when every non-missing value is a Python `str`. The test is `isinstance(value, str)`, so a subclass of `str` is eligible. Eligibility inspects every non-missing value. An object column with no non-missing value is not eligible: absence of a non-string is not positive evidence of strings. Physical categorical storage is not eligible, even when every category label is a string. Labels are not converted and are not inspected by this collector. Boolean, integer, floating, Datetime, timezone-aware Datetime, Timedelta, Period, complex, Interval, and any other family are excluded. A non-missing value that is not a Python `str` is excluded even when the physical family is string. Numpy byte-string storage is classified as string by the existing classifier and is not eligible, because the values are `bytes` and this decision does not decode them. Calling the collector on an excluded Series raises `TypeError`. The collector does not stringify, strip, case-fold, or Unicode-normalize the Series, and it does not change physical classification. `n_total`, `n_missing`, `n_non_missing`, and `n_unique_non_missing` stay on the universal family and are not copied. The population is non-missing strings. Pandas missingness is the missingness already used by basic evidence. `""`, whitespace, and literals such as `"NA"`, `"N/A"`, `"null"`, `"None"`, and `"?"` remain ordinary strings. Stored observations are `empty_string_count`, `whitespace_only_count`, `contains_whitespace_count`, `contains_alpha_count`, `contains_digit_count`, `contains_other_count`, `min_length`, and `max_length`. Counts are non-negative integers and are never `None`. Each count is at most `n_non_missing`. An empty string is a non-missing value equal to `""`. It is not whitespace-only, and it contains neither whitespace nor an alphabetic, digit, or other character. Its length is 0. A non-empty string is whitespace-only when `str.isspace` is true. That is Python's Unicode definition, not an ASCII-only list. A string contains whitespace when at least one character has `str.isspace` true, so a whitespace-only string also contains whitespace. Alphabetic uses `str.isalpha`. Digit uses `str.isdigit`. Other means a character that is not alphabetic, not a digit, and not whitespace. A string may increment more than one of those content counts. They are not a partition of `n_non_missing`. Length is `len` of the original string: Python's code-point length, not UTF-8 bytes, display width, grapheme clusters, or tokens. `min_length` and `max_length` are `None` when `n_non_missing` is 0. They are non-negative integers when `n_non_missing` is greater than 0, and the minimum does not exceed the maximum. An empty-string count above zero requires `min_length == 0`. A minimum of 0 requires an empty string, because only `""` has length 0. A whitespace-only count cannot exceed the contains-whitespace count. The empty-string count and the whitespace-only count cannot together exceed `n_non_missing`. `empty_string_ratio`, `whitespace_only_ratio`, `contains_whitespace_ratio`, `contains_alpha_ratio`, `contains_digit_ratio`, and `contains_other_ratio` each divide the named count by `n_non_missing` when that count is greater than 0, and are `None` when it is 0. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. A zero numerator with a positive denominator is `0.0`. There is no second denominator. The observations are exact, full-column, and unsampled. There is no provenance object. The family is collected when requested. The implemented Empty, Constant, and physical-type chain does not collect it. These facts do not select Text, Categorical, Identifier, Boolean, Binary, Datetime, or Numeric. They carry no High, Medium, or Low confidence and no evidence role. They do not count words or tokens. They do not recognize UUID, email, URL, path, hash, phone, postal code, date-like, numeric-like, JSON, XML, HTML, or similar patterns. Characters such as `@`, `:`, `/`, `-`, `_`, and `.` may contribute only to the other-character count. |
| Rationale | Candidate assessment needs structural facts about strings that cannot drift from the universal counts. String storage is not a semantic role, and an empty object column does not show that its missing values would have been strings. Pattern names and word counts answer later questions and stay outside this family. Eager collection would make every current reading pay for a fact it does not use. |
| Implications | `REQ-S-03`, `REQ-S-05`. Empty and Constant definitions in [DEC-046](#dec-046) and [DEC-077](#dec-077) are unchanged. This decision does not complete `REQ-F-01`, `REQ-F-02`, or `REQ-H-04`. It does not close [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), or [OPEN-049](#open-049). Character-class counts and length bounds do not decide Text, Categorical, Identifier, or a string subtype. The ratios are not inference thresholds. Word and token definitions, pattern semantics, and the missing-like literal list remain open. Numpy byte-string storage stays in the physical string family; this decision only refuses to treat `bytes` as Python string observations. No later slice is approved. |
| Later update | TSK-010 adds `PatternEvidence` as a separate family composed with this one ([DEC-081](#dec-081)). The sentence above, that no further family is authorized, is the TSK-009 scope. It does not forbid that later family. This family still does not recognize UUID, email, URL, path, or any other pattern. Pattern counts are not string-structure fields. |
| Later update | [DEC-083](#dec-083) does not treat these observations as support for a Text or Categorical candidate. Length bounds and character-class counts remain observations. They are not inference thresholds. |
| Later update | TSK-013 adds `StringContentEvidence` as a separate family composed with this one ([DEC-084](#dec-084)). The sentence above, that no further family is authorized, is the TSK-009 scope. It does not forbid that later family. This family still does not count tokens. Token counts are not string-structure fields. Minimum and maximum length stay here and are not copied. |

## DEC-081

| | |
| --- | --- |
| Title | Pattern evidence observes full-value syntax and does not interpret it |
| Status | Accepted |
| Decision | `PatternEvidence` is a typed observation family composed with `StringStructureEvidence`. It is not a subclass of that family or of `BasicColumnEvidence`, and it is not a generic property bag. No further evidence family is named or authorized. The supplied `StringStructureEvidence` is the evidence that the column population already satisfied the string-structure applicability contract. The collector does not recollect string structure, does not recollect basic evidence, and does not classify the physical dtype again. It still rejects a Series whose length or non-missing count disagrees with the composed basic evidence, a physical dtype name that disagrees with the Series, a physical family other than string or object, an all-missing object population, and a non-missing value that is not a Python `str`. Those checks do not rebuild character-class or length observations. `bytes` are not decoded. Values are not stringified. The population is the non-missing strings. Pandas missingness stays missing. `""`, whitespace-only strings, and literals such as `"NA"` remain ordinary strings and do not match any pattern in this family. The original string is tested. The collector does not strip, case-fold, or Unicode-normalize it. Every pattern is a full-value syntactic match. A pattern embedded in surrounding text does not match. Leading or trailing whitespace does not match. The catalog is UUID, IPv4, IPv6, and fixed-width hexadecimal tokens of widths 32, 40, 64, and 128. Email, URL, URI, filesystem path, phone number, postal code, credit-card-like values, date-like strings, datetime-like strings, time-like strings, numeric-like strings, JSON, XML, HTML, MAC address, hostname, base64, and a generic identifier pattern are not recognized. UUID syntax is exactly two textual forms. The canonical form is 36 characters, eight hexadecimal characters, a hyphen, four, a hyphen, four, a hyphen, four, a hyphen, and twelve. The compact form is 32 hexadecimal characters. Upper and lower case are both accepted. Brace-wrapped forms, a `urn:uuid:` prefix, misplaced hyphens, and any other shape are not accepted, including shapes that `uuid.UUID` would parse. A parser call may confirm the hexadecimal body after the shape has matched. It must not widen the shape. No UUID version and no RFC variant is required. `uuid_count` is the number of non-missing strings that match. Matched values are not retained. IPv4 uses `ipaddress.IPv4Address` on the entire original string. IPv6 uses `ipaddress.IPv6Address` on the entire original string, including compressed and expanded spellings that constructor accepts. CIDR and other network syntax do not match. The collector does not classify private, public, loopback, link-local, multicast, or any other address property, and it does not store a canonicalized address. `ipv4_count` and `ipv6_count` are separate. There is no stored generic IP count. A fixed-width hexadecimal token is a string whose every character is in `0123456789abcdefABCDEF` and whose length is exactly 32, 40, 64, or 128. That alphabet is ASCII. It is not Python's Unicode digit or alphabetic definition, which remains the definition used by string-structure character classes. A `0x` prefix, whitespace, and separators such as `-`, `:`, and `_` do not match. The counts are `hex_32_count`, `hex_40_count`, `hex_64_count`, and `hex_128_count`. They are not named as MD5, SHA-1, SHA-256, or SHA-512. A 32-character token may also be a compact UUID. The observation is only the width and the alphabet. The counts are independent. They may overlap. A compact UUID increments both `uuid_count` and `hex_32_count`. There is no precedence, no best pattern, and no winner. Validation does not require the counts to be mutually exclusive and does not require their sum to be at most `n_non_missing`. Each count is a non-negative integer and is at most `string_structure.basic.n_non_missing`. Ratios are read-only. `uuid_ratio`, `ipv4_ratio`, `ipv6_ratio`, `hex_32_ratio`, `hex_40_ratio`, `hex_64_ratio`, and `hex_128_ratio` each divide the named count by `string_structure.basic.n_non_missing` when `n_non_missing` is greater than 0, and are `None` when `n_non_missing` is 0. An undefined ratio is `None`, not `0.0`, `1.0`, NaN, or infinity. A zero numerator with a positive denominator is `0.0`. The denominator is the full non-missing string population. It is not the non-empty strings, the unique strings, or the matched strings. An all-missing or zero-length physical string column may already have string-structure evidence. Pattern evidence collected from it has every count at 0 and every ratio `None`. A constant string column may have pattern evidence for every row. Neither fact changes Empty or Constant precedence. The observations are exact, full-column, and unsampled. There is no provenance object. The family is collected when requested. The implemented Empty, Constant, and physical-type chain does not collect it. Collecting string-structure evidence does not collect it. These facts do not select Identifier, Text, Categorical, Boolean, Binary, Datetime, or Numeric. They carry no High, Medium, or Low confidence, no evidence role, and no column-level threshold. A ratio of 1.0 is an observed proportion. It is not a semantic conclusion. Absence of a match is not positive evidence for another semantic type. |
| Rationale | Candidate assessment needs syntactic facts that cannot drift from the string population already observed. A permissive parser, a substring hit, or a semantic label on the same object would collapse observation into interpretation. Overlap is a fact about the strings, not a conflict to be solved here. Eager collection would make every current reading pay for a fact it does not use. |
| Implications | `REQ-S-03`, `REQ-S-05`. Empty and Constant definitions in [DEC-046](#dec-046) and [DEC-077](#dec-077) are unchanged. String-structure applicability in [DEC-080](#dec-080) is unchanged. This decision does not complete `REQ-F-01`, `REQ-F-02`, `REQ-G-01`, or `REQ-G-02`. It does not close [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), or [OPEN-049](#open-049). The ratios are not inference thresholds. UUID syntax and fixed-width hexadecimal counts do not decide whether UUID-like or hash-like structure can be sufficient for Identifier. Email-like, URL-like, path-like, and datetime-like patterns are not selected and are not rejected as future observations. No later slice is approved. |
| Later update | [DEC-082](#dec-082) may read a full-population UUID count, or a full-population count at one supported hexadecimal width, as support for an Identifier candidate assessment. The pattern observation still does not select Identifier. A ratio of 1.0 on this object remains an observed proportion. The precedence chain still does not collect or read this family. A partial ratio, a mixture of patterns, IPv4, and IPv6 are not that support. |
| Later update | [DEC-083](#dec-083) does not treat UUID, hexadecimal, IPv4, or IPv6 counts as support for Text or Categorical. Absence of a pattern match remains not positive evidence for Text. |
| Later update | [DEC-084](#dec-084) counts maximal Unicode alphanumeric runs. Those runs are not the fixed-width hexadecimal tokens in this family. A hyphenated UUID can be several alphanumeric runs and still one UUID pattern match. Neither observation selects a semantic type. |

## DEC-082

| | |
| --- | --- |
| Title | Candidate assessment records support and contradiction without selecting a reading |
| Status | Accepted |
| Decision | A candidate assessment asks whether observed evidence supports one plausible semantic reading. Resolution decides which reading wins. `CandidateAssessment` is a frozen value for one candidate. It is not a `SemanticInterpretation`, not a selected reading, and not a material alternative. Its fields are `semantic_type`, `disposition`, `supporting_evidence`, and `contradicting_evidence`. `semantic_type` is a `SemanticType`. There is no second candidate-type enum. `disposition` is `CandidateDisposition`: `SUPPORTED`, `NOT_SUPPORTED`, or `CONTRADICTED`. `SUPPORTED` means the candidate's current explicit rules found sufficient positive evidence to keep the reading available for later resolution. It does not mean the candidate wins. `NOT_SUPPORTED` means those rules did not find sufficient positive evidence. It is the result when positive support is absent. It is not contradiction. `CONTRADICTED` means an explicit observed fact is incompatible with the candidate under a stated rule. Absence of support is not contradiction. Supporting and contradicting evidence are separate tuples of `SemanticEvidence`. That statement type is reused. There is no second evidence-item class and no evidence-role enum. Evidence that does not bear on the candidate is omitted. `SUPPORTED` requires at least one supporting statement. `CONTRADICTED` requires at least one contradicting statement. Both sequences may be non-empty. The value has no score, points, weight, probability, confidence percentage, High, Medium, or Low confidence, winner, rank, or priority. Final confidence remains a resolution concern. The first concrete assessor is Identifier. `assess_identifier_candidate` consumes already collected evidence. It does not recollect basic counts, frequency, numeric structure, string structure, or patterns, and it does not classify the physical dtype again. It does not take a Series or a column name. Supplied frequency, numeric-structure, and string-structure evidence must be the objects composed with the supplied `BasicColumnEvidence`. Pattern evidence must be the object composed with the supplied `StringStructureEvidence`. Equal counts from another column are not the same bundle. A physical family that cannot carry the supplied family evidence is rejected. The precedence chain does not call the assessor. Ordinary calls do not start returning Identifier. Identifier means values primarily function to distinguish, reference, or key entities or records, rather than measure a quantity or represent a classification vocabulary. It is not a primary key. For this slice the rules are: an empty column is `NOT_SUPPORTED`; a constant column is `NOT_SUPPORTED`, including a constant UUID; otherwise the candidate is `SUPPORTED` when every non-missing value matches UUID syntax, or every non-missing value matches one ASCII hexadecimal width of 32, 40, 64, or 128; otherwise it is `NOT_SUPPORTED`. The full population is the pattern count equal to `n_non_missing`. That is the same fact as an observed ratio of 1.0, compared on the integers. It is the conservative initial Identifier candidate rule for the current evidence foundation. It is not a universal threshold and does not forbid a future partial-pattern rule. A compact UUID may record both the UUID fact and the 32-character hexadecimal fact. Two statements are not a stronger disposition and are not a score. The hexadecimal statement names the width and the ASCII alphabet. It does not name a hash algorithm. A ratio below the full population does not support. A mixture of different patterns does not support, even when every row matches some strong pattern. IPv4 and IPv6 do not support Identifier and do not contradict it. Uniqueness, zero missingness, singleton ratio, and other frequency facts do not support Identifier. Missing values do not contradict it. Duplicates do not contradict it and do not remove UUID or hexadecimal support. A column name is not read. Physical Boolean, Datetime, timezone-aware Datetime, Timedelta, and categorical storage are `NOT_SUPPORTED`, not `CONTRADICTED`. Numeric uniqueness, integer-like values, and monotonicity are not Identifier support. Regular-step evidence is not reconstructed. This slice emits no Identifier contradiction. The contradicting sequence stays available for a later candidate. No resolution function, material alternative, or final confidence is added. No public API is added. |
| Rationale | Support for a plausible reading and the choice of a reading are different stages. A numeric total would hide that difference, and treating a missing signal as contradiction would turn an incomplete observation into a refutation. UUID syntax and a stable hexadecimal token are role evidence. Uniqueness and completeness are not. |
| Implications | `REQ-S-04`, `REQ-S-05`, `REQ-G-01`, `REQ-G-02`. None of those rows is completed. The assessor does not select Identifier and does not displace Numeric. [OPEN-044](#open-questions) is narrowed only for this initial full-population candidate rule. Partial-pattern thresholds, numeric sequence Identifier evidence, column-name and schema evidence, dataset-context evidence, final candidate resolution, and final confidence assignment stay open. [OPEN-045](#open-questions) stays open: the module names are not a layout decision. [OPEN-048](#open-048) stays open. [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-043](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), and [OPEN-049](#open-049) stay open. No later slice is approved. |
| Later update | [DEC-083](#dec-083) reuses this candidate model for Numeric, Categorical, and Text. It does not change the Identifier rules, the disposition meanings, or the absence of a score and of final confidence. |
| Later update | [DEC-085](#dec-085) consumes candidate assessments, including Identifier. It does not change the Identifier rules, and a supported Identifier candidate is not by itself a selected interpretation. |
| Later update | [DEC-086](#dec-086) may record a resolved Identifier selection when that candidate is the only one supported. It does not assign High, Medium, or Low to that selection and does not build a `SemanticInterpretation` for it. |
| Later update | [DEC-087](#dec-087) calls this assessor from the column pipeline when structural precedence does not apply. The precedence chain still does not. The Identifier rules are unchanged. |

## DEC-083

| | |
| --- | --- |
| Title | Numeric, Categorical, and Text candidates record positive evidence without selecting a reading |
| Status | Accepted |
| Decision | TSK-012 adds Numeric, Categorical, and Text candidate assessments on the unchanged `CandidateAssessment` model from [DEC-082](#dec-082). It does not add a specialized assessment type for any of them. It does not resolve candidates, assign High, Medium, or Low, add a score, weight, probability, rank, or priority, or call any candidate assessor from the precedence chain. Identifier rules are unchanged. The three assessors consume an evidence bundle already collected. They use the Identifier assessor's bundle identity checks. They do not take a Series, read a column name, recollect observations, or classify a physical dtype again. Empty and Constant yield `NOT_SUPPORTED` for each candidate, including a constant integer, float, string, category label, or paragraph. That is stronger precedence already held by Empty or Constant, not a contradiction. None of these assessors emits `CONTRADICTED`. Absence of support is not contradiction. The assessors do not force mutual exclusivity. Zero, one, or more candidates may be supported for the same column. Numeric means values primarily function as quantities on which magnitude and arithmetic relationships are analytically meaningful. A non-empty, non-constant column whose physical family is integer or floating is `SUPPORTED`. That includes nullable integer and floating storage, and sparse storage the current physical classifier already places in those families. The supporting statement names the family and says that it supports a Numeric reading. It does not say that the column is Numeric. Numeric-structure evidence may be supplied with the bundle. Its finite, sign, zero, integer-like, and monotonicity facts are context. They do not add a cutoff, and they are not required. A column that contains infinities may still be supported. Physical Boolean is not in those families and is not supported. Complex storage is not supported: current decisions do not define complex values as Numeric semantics, and numeric-structure evidence excludes complex. Datetime, timezone-aware Datetime, Timedelta, categorical, string, and object storage are not supported as Numeric. Numeric-looking strings are not parsed. `{0, 1}` and `{0.0, 1.0}` on numeric storage may support Numeric. They are not inferred as Boolean or Binary. An integer sequence such as `1, 2, 3, 4, 5` is `SUPPORTED` as Numeric and remains `NOT_SUPPORTED` as Identifier, because regular-step evidence still does not exist. Categorical means values primarily function as a classification vocabulary. A non-empty, non-constant physical categorical dtype is `SUPPORTED`. The statement says that physical categorical storage supports a Categorical reading. Ordered metadata stays on the physical dtype. It is not an Ordinal semantic type. Unused levels do not change the rule. Labels are not recollected or parsed, and string-structure evidence is not collected for categorical storage. [DEC-070](#dec-070) and [DEC-071](#dec-071) treat repetition as support that is not sufficient, and no cardinality threshold is approved. Ordinary string and object columns, two labels, Boolean-like labels, UUID strings, IP strings, and low-cardinality numeric values therefore stay `NOT_SUPPORTED` as Categorical. Text means values primarily function as textual content. [DEC-071](#dec-071) allows length, whitespace, and prose-like structure as possible evidence and does not choose a threshold. [DEC-080](#dec-080) says the current string-structure facts do not by themselves select Text. No word or token counts exist. This slice therefore does not support Text from current observations. String dtype, length, whitespace, punctuation, long values, prose-like values, UUID syntax, hexadecimal tokens, IP syntax, email-like text, and URL-like text do not support Text. Absence of an Identifier pattern is not Text support. The Text assessor still validates the bundle and returns `NOT_SUPPORTED`. That is not a contradiction. No cardinality, uniqueness, length, or whitespace threshold is introduced. No regular-step collector, common-token diagnostic, NLP feature, user override, material alternative, or final confidence is added. |
| Rationale | A candidate should stay available only when current observations give positive evidence for that reading. Physical numeric storage and physical categorical storage are such evidence. Repetition, cardinality, length, and whitespace are not, until a threshold or a stronger observation is actually approved. Forcing a type onto every column would hide that gap. |
| Implications | `REQ-S-01`, `REQ-S-04`, and `REQ-S-05` are not completed. `REQ-C-01`, `REQ-F-01`, `REQ-D-01`, and `REQ-D-02` are not completed. A supported candidate is not the selected reading. [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-037](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), and [OPEN-049](#open-049) stay open. No later slice is approved. |
| Later update | [DEC-084](#dec-084) adds token and vocabulary observations. It does not change these candidate rules. The sentence in this decision that no token counts exist is the TSK-012 scope. Ordinary strings stay `NOT_SUPPORTED` as Categorical, and Text stays `NOT_SUPPORTED`. |
| Later update | [DEC-085](#dec-085) resolves these assessments and does not change the Numeric, Categorical, or Text rules. A supported candidate is still not, by itself, a confidence-bearing interpretation. |
| Later update | [DEC-086](#dec-086) may record a resolved Numeric or Categorical selection when that candidate is the only one supported. It does not assign High, Medium, or Low to either selection. A directly constructed Text candidate may resolve in a generic test. That fixture is not a production Text confidence. |
| Later update | [DEC-087](#dec-087) calls these assessors from the column pipeline when structural precedence does not apply. The precedence chain still does not. The Numeric, Categorical, and Text rules are unchanged. |

## DEC-084

| | |
| --- | --- |
| Title | String content evidence observes token structure and vocabulary counts and does not interpret them |
| Status | Accepted |
| Decision | `StringContentEvidence` is a typed observation family composed with `StringStructureEvidence`. It is not a subclass of that family or of `BasicColumnEvidence`, and it is not a generic property bag. No further evidence family is named or authorized. The supplied `StringStructureEvidence` is the evidence that the column population already satisfied the string-structure applicability contract. The collector does not recollect string structure, does not recollect basic evidence, does not recollect whole-value frequency, does not recollect pattern evidence, and does not classify the physical dtype again. It still rejects a Series whose length or non-missing count disagrees with the composed basic evidence, a physical dtype name that disagrees with the Series, a physical family other than string or object, an all-missing object population, and a non-missing value that is not a Python `str`. Those checks do not rebuild character-class or length observations. `bytes` are not decoded. Values are not stringified. Categorical labels are not inspected. The population is the non-missing strings. Pandas missingness stays missing. `""`, whitespace-only strings, and literals such as `"NA"`, `"nan"`, and `"None"` remain ordinary strings. The original string is observed. The collector does not strip, case-fold, or Unicode-normalize it. A token is a maximal contiguous run of characters for which Python `str.isalnum` is true. That is Unicode alphanumeric, the same character database Python already uses. Punctuation and whitespace end a run. Underscore, hyphen, and period are separators because they are not alphanumeric. `"hello world"`, `"hello-world"`, and `"hello_world"` are two tokens. `"abc123"` is one token, because letters and digits are both alphanumeric. `"één twee"` is two tokens. `"東京 データ"` is two tokens. An emoji is not alphanumeric, so `"🙂"` has no token and `"hello🙂world"` is two tokens. `""` and a whitespace-only string have no token. A combining accent is not rewritten into a precomposed character: `"café"` and `"cafe"` plus a combining acute are different token observations. `"Apple"` and `"apple"` stay distinct. Case-folding would be a transformation, and this decision does not add one. Stored observations are `total_token_count`, `strings_with_zero_tokens_count`, `strings_with_one_token_count`, `strings_with_multiple_tokens_count`, `total_character_count`, `n_distinct_tokens`, `singleton_token_count`, and `most_frequent_token_count`. Counts are non-negative integers and are never `None`. The three string classes partition `string_structure.basic.n_non_missing`. A one-token string contributes one token. A multiple-token string contributes at least two. A positive token total requires a string that contains a token. `total_character_count` is the sum of `len` of the original non-missing strings, the same length definition as [DEC-080](#dec-080). It is `0` when `n_non_missing` is `0`. Otherwise it is at least `total_token_count`, because each token occupies at least one character, and it lies between `min_length * n_non_missing` and `max_length * n_non_missing`. Minimum and maximum length are not copied. An empty string and a whitespace-only string contain no alphanumeric token, so `strings_with_zero_tokens_count` is at least the sum of those two string-structure counts. Other zero-token strings, including punctuation and emoji, may raise that count further. `n_distinct_tokens` is `0` exactly when `total_token_count` is `0`. Otherwise it is at least `1` and at most `total_token_count`. `singleton_token_count` counts distinct tokens that occur once. It does not exceed `n_distinct_tokens`. `most_frequent_token_count` is `0` when there is no token, and otherwise at least `1` and at most `total_token_count`. Those three vocabulary counts must be possible together for the token-occurrence total. The limits are the same kind already used for whole-value frequency, applied to tokens rather than to whole values. Whole-value `most_frequent_count`, `singleton_count`, and the retained distinct-value set stay on frequency evidence and are not copied. `"red car"` and `"blue car"` can be two distinct whole values and still repeat the token `"car"`. Ratios and means are read-only. `zero_token_ratio`, `one_token_ratio`, `multiple_token_ratio`, `mean_tokens_per_non_missing`, and `mean_characters_per_non_missing` each divide the named count by `n_non_missing` when `n_non_missing` is greater than `0`, and are `None` when it is `0`. `token_singleton_ratio` is `singleton_token_count / n_distinct_tokens` when `n_distinct_tokens` is greater than `0`, and `None` otherwise. The denominator is distinct tokens, not token occurrences and not non-missing strings. `most_frequent_token_ratio` is `most_frequent_token_count / total_token_count` when `total_token_count` is greater than `0`, and `None` otherwise. The denominator is token occurrences, not distinct tokens and not non-missing strings. An undefined ratio or mean is `None`, not `0.0`, `1.0`, NaN, or infinity. A zero numerator with a positive denominator is `0.0`. A column of punctuation therefore has mean tokens `0.0` and undefined vocabulary ratios. Means are not stored. No raw string, token, or vocabulary is retained. A temporary mapping may count occurrences during collection. It is not part of the returned value. The observations are exact, full-column, and unsampled. There is no provenance object. The family is collected when requested. The implemented Empty, Constant, and physical-type chain does not collect it. Collecting string-structure evidence does not collect it. Candidate assessors do not collect it. These facts do not select Text, Categorical, Identifier, Boolean, Binary, Datetime, or Numeric. They carry no High, Medium, or Low confidence and no evidence role. A ratio of `1.0` is an observed proportion. It is not a semantic conclusion. TSK-013 does not change `core_candidates.py`. Every non-missing string consisting of one token does not support Categorical or Text: city names and single-word text share that shape. At least one string containing several tokens does not support Text: `"New York"` and a sentence share that shape. Token repetition does not support Categorical: [DEC-070](#dec-070) already says repetition is not sufficient, and no cardinality or vocabulary threshold is approved. No threshold-free structural fact in this family separates a classification vocabulary from textual content without a high risk of confusing common labels with prose. Ordinary strings therefore stay `NOT_SUPPORTED` as Categorical, and Text stays `NOT_SUPPORTED`. Physical categorical storage, physical integer and floating storage, full-population UUID syntax, and full-population fixed-width hexadecimal syntax keep the candidate rules in [DEC-082](#dec-082) and [DEC-083](#dec-083). A hyphenated UUID may be several alphanumeric runs and still one UUID pattern match. Those are different observations. This decision does not add resolution, final confidence, a score, Binary inference, Ordinal inference, yes/no parsing, or regular-step numeric Identifier evidence. |
| Rationale | Candidate assessment needs structural facts about strings that frequency of whole values and character classes do not provide. Retaining the vocabulary would make the evidence unbounded and would keep raw text inside the semantic layer. Treating one token, several tokens, or a repeated token as a semantic type would turn an observation into an unapproved cutoff. |
| Implications | `REQ-S-03`, `REQ-S-05`. Empty and Constant definitions in [DEC-046](#dec-046) and [DEC-077](#dec-077) are unchanged. String-structure applicability in [DEC-080](#dec-080) is unchanged. This decision does not complete `REQ-F-01`, `REQ-F-02`, or `REQ-C-01`. It does not close [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), or [OPEN-049](#open-049). [OPEN-019](#open-questions) is narrowed only for the evidence-collection portion of token aggregates. Trimmed mean, downstream common-token diagnostics, and any rule that would support Text or Categorical from those aggregates stay open. The ratios are not inference thresholds. No later slice is approved. |
| Later update | [DEC-085](#dec-085) does not read these token observations again and does not turn them into a Text or Categorical rule. |
| Later update | [DEC-087](#dec-087) collects this family on an eligible non-structural string population, from the string-structure evidence already collected for that column. The candidate assessors still do not read it. Text and ordinary-string Categorical stay unsupported. |
| Later update | [DEC-088](#dec-088) stops that eager collection. No candidate assessor reads the family, and the dataset facts in that slice do not read it either. [OPEN-019](#open-questions) still leaves open whether the aggregates belong in a text profile. The collector remains. It is not called by column analysis until a consumer needs it. |

## DEC-085

| | |
| --- | --- |
| Title | Resolution selects a justified reading and can abstain |
| Status | Accepted |
| Decision | TSK-014 adds a resolution foundation beside the existing precedence chain. It consumes one optional structural interpretation and candidate assessments that were already produced. It does not collect observations, call collectors, call assessors, parse source values, or read a Series. Resolution status is not a `SemanticType`. No unknown, ambiguous, or unresolved member is added to that enum. `ResolutionStatus` is `RESOLVED`, `INSUFFICIENT_EVIDENCE`, or `AMBIGUOUS`. `SemanticResolution` is a frozen value. It stores the status, one diagnostic reason, the candidate assessments considered, the selected semantic type when the status is `RESOLVED`, and the structural `SemanticInterpretation` when a structural reading was selected. It does not store a Series, a DataFrame, a numeric total, or a second copy of the observations already held by a candidate assessment. A structural interpretation is accepted only for Empty, Constant, Boolean, Datetime, or Timedelta. Any other semantic type supplied as a structural reading is rejected, so a prebuilt Numeric interpretation cannot skip candidate resolution. When an accepted structural interpretation is supplied, the result is `RESOLVED` to that same object. Candidate assessments do not replace it. Constant UUID and constant integer storage stay Constant. Physical Boolean, Datetime, timezone-aware Datetime, and Timedelta stay those readings. The confidence already stored on that object is kept. The resolver does not assign a new one. With no structural interpretation, exactly one `SUPPORTED` candidate makes the result `RESOLVED` to that semantic type. No confidence and no `SemanticInterpretation` are produced for that selection. A candidate assessment does not carry a physical dtype or a justified High, Medium, or Low mapping, and `SemanticInterpretation` requires both. Inventing either would manufacture an interpretation. With no structural interpretation and no `SUPPORTED` candidate, including an empty candidate collection, the result is `INSUFFICIENT_EVIDENCE`. There is no fallback semantic type. That status is abstention at the resolution layer. It does not redefine `None` from `interpret_series_precedence`. With no structural interpretation and more than one `SUPPORTED` candidate, and no reviewed rule between those candidates, the result is `AMBIGUOUS`. It does not select a semantic type. Enum order, input order, and the number of supporting statements are not used. In particular, this slice does not give Identifier priority over Numeric. The displacement principle in [DEC-069](#dec-069) is not withdrawn and is not implemented here. A `CONTRADICTED` candidate is not supported and is not selected. It does not veto a different supported candidate. The number of contradictions is not a confidence measure. Two candidate assessments for the same `SemanticType` are invalid input. They are rejected rather than merged. The result does not depend on candidate input order. Stored assessments are ordered by semantic-type name, and an ambiguous reason lists supported types in that same order. That order does not choose a reading. `interpret_series_precedence` is unchanged and does not call the resolver. User overrides, effective interpretation, downstream eligibility, the public profile result, configuration, and inference thresholds are not added. Material alternatives are not constructed. An ambiguous result keeps the supported assessments. An unsupported candidate is not a material alternative. `SemanticAlternative` is not redesigned. The inferred `SemanticInterpretation` for a candidate-derived resolution is deferred. A structural resolution preserves the interpretation that already existed. |
| Rationale | `SemanticInterpretation` requires a selected type, a confidence, a source, and a physical dtype. It cannot say that the evidence was insufficient, or that competing candidates remain unresolved, without pretending that a type was selected. A separate status keeps those outcomes explicit. Counting supported candidates is not a measurement of confidence. |
| Implications | `REQ-S-01`, `REQ-S-02`, `REQ-S-04`, and `REQ-S-05` are not completed. The resolver is not on the public `pytics` API. [OPEN-047](#open-047) now records that abstention exists as `INSUFFICIENT_EVIDENCE`, distinct from `None`, and that the inferred-interpretation representation of abstention and ambiguity remains open. [OPEN-044](#open-questions) stays open for thresholds, partial patterns, numeric Identifier evidence, final confidence of a candidate-derived reading, and any future rule that would select between supported candidates. [OPEN-004](#open-questions), [OPEN-009](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-043](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-048](#open-048), and [OPEN-049](#open-049) stay open. No later slice is approved. |
| Later update | [DEC-086](#dec-086) consumes this resolution together with an observed physical dtype. It does not change the resolver. A structural resolution keeps the interpretation this decision already preserved. A candidate-derived resolution still does not receive a `SemanticInterpretation`. |
| Later update | [DEC-087](#dec-087) calls `resolve_semantics` from the column pipeline. `interpret_series_precedence` still does not. The resolver rules are unchanged. |

## DEC-086

| | |
| --- | --- |
| Title | The inferred result records resolution without inventing candidate confidence |
| Status | Accepted |
| Decision | TSK-015 adds the inferred semantic state after resolution. `InferredSemanticResult` is a frozen value. Its stored fields are the observed `PhysicalDtype` and the `SemanticResolution` already produced. It does not store a second status, a second selected type, the candidate assessments again, the resolution reason again, or a second copy of a structural interpretation. `interpretation` is that structural interpretation when the resolution has one, and `None` otherwise. `selected_type` is the resolution's selected type. Both are derived. `build_inferred_semantic_result` combines the two stored facts. It does not read a Series, collect observations, assess candidates, or call `resolve_semantics`. The physical dtype is supplied from the observation already made. It is not derived from the selected semantic type. Numeric storage may be integer or floating. Identifier storage may be string or object. Categorical storage keeps its ordered flag. A semantic type does not choose among those families. When the resolution carries a structural interpretation, the supplied physical dtype must equal that interpretation's physical dtype. A mismatch is invalid. The constructor does not replace either value. The interpretation object is kept. Its confidence, source, evidence, and physical dtype are not rewritten. Empty, Constant, Boolean, Datetime, timezone-aware Datetime, and Timedelta stay the readings they already were. A candidate-derived `RESOLVED` result keeps the selected semantic type and does not build a `SemanticInterpretation`. Current positive candidate rules justify that selection when the candidate is the only one supported. They do not justify High, Medium, or Low. Non-empty, non-constant physical integer or floating storage can select Numeric. That storage does not guarantee Numeric meaning. Numeric Identifier evidence is not implemented, so an integer value can still be an identifier. A full non-missing population of UUID syntax, or of one supported fixed-width hexadecimal form, can select Identifier. That is strong syntactic support for the candidate. It is not an approved confidence. Non-empty, non-constant physical categorical storage can select Categorical. Categorical storage is not synonymous with Categorical meaning. The Text assessor has no positive production rule. A directly constructed Text candidate may still resolve in a generic resolver test. That fixture is not a production confidence rule. No mapping from an evidence origin, a candidate count, a supporting-statement count, or the absence of contradiction to High, Medium, or Low is introduced. No evidence-strength enum is introduced. `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` are valid inferred states. Each carries the physical dtype and the resolution. Neither carries an interpretation or a selected type. Neither is an error, and neither is `None` from `interpret_series_precedence`. An ambiguous result does not become a selected reading, a low confidence, or material alternatives. The supported candidate assessments remain on the resolution. `SemanticInterpretation` remains a selected reading that already has a confidence, a source, and a physical dtype. It is not widened so that confidence can be absent. `Confidence`, `InferenceSource`, and `SemanticType` are unchanged. No `RESOLUTION` source is added. Resolution is a stage, and this slice builds no candidate-derived interpretation that would need a source. Structural interpretations keep the source they already have. `interpret_series_precedence` does not call this construction. User override, effective interpretation, downstream eligibility, the public profile result, and configuration are not added. |
| Rationale | `SemanticInterpretation` cannot record a selected type that has no justified confidence, and it cannot record that no reading was selected, without inventing one of those facts. A separate result can carry the resolution, including abstention and ambiguity, and can expose an interpretation only when one already exists. Counting support is not a measurement of confidence. |
| Implications | `REQ-S-01`, `REQ-S-02`, `REQ-S-04`, and `REQ-S-05` are not completed. The result is not on the public `pytics` API. [OPEN-047](#open-047) now records that the inferred result represents abstention and ambiguity without an interpretation. Candidate-derived confidence, material alternatives on a future selected reading, and the public result representation remain open. [OPEN-044](#open-questions) stays open for that confidence and for thresholds. [OPEN-004](#open-questions), [OPEN-009](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-043](#open-questions), [OPEN-045](#open-questions), [OPEN-046](#open-046), [OPEN-048](#open-048), and [OPEN-049](#open-049) stay open. No later slice is approved. |
| Later update | [DEC-087](#dec-087) calls `build_inferred_semantic_result` with the physical dtype observed for that Series and the resolution already produced. It does not assign High, Medium, or Low to a candidate-derived selection. |

## DEC-087

| | |
| --- | --- |
| Title | One column pipeline composes the existing semantic engine |
| Status | Accepted |
| Decision | TSK-016 adds one internal column pipeline, `infer_series_semantics`. It accepts one pandas Series and returns the existing `InferredSemanticResult`. It does not add a second result type. It classifies physical dtype once, with `classify_physical_dtype`, and collects `BasicColumnEvidence` once. Those two objects are the observations reused downstream. Structural precedence is the existing `interpret_precedence_from_evidence` in the Timedelta precedence module. That helper already accepts the physical dtype and the basic evidence and does not classify or collect again. No second copy of Empty, Constant, Boolean, Datetime, or Timedelta rules was added. `interpret_series_precedence` remains the Series wrapper: it classifies, collects basic evidence, and delegates to that helper. The pipeline does not call the wrapper. When the helper returns a structural interpretation, the pipeline calls `resolve_semantics` with that interpretation and no candidate assessments, then `build_inferred_semantic_result`. It does not collect frequency, numeric-structure, string-structure, pattern, or string-content evidence on that path, and it does not call the candidate assessors. A constant UUID therefore stays Constant. Physical Boolean, Datetime, timezone-aware Datetime, and Timedelta stay those readings, and the timezone-aware family stays on the physical dtype. When there is no structural interpretation, evidence follows the existing collector contracts. Integer and floating storage collect `NumericStructureEvidence` once, composed with the same basic evidence. Boolean, complex, datetime, timedelta, string, object, and categorical storage do not. String and object storage collect `StringStructureEvidence` only when that collector accepts the population. Pattern evidence and string-content evidence then receive that same string-structure object. An applicability `TypeError` from the string-structure collector means the population is not string evidence. Mixed object values and `bytes` are that case. They are not coerced, and they are not an inference error. All-missing object storage is already Empty, so it never reaches that collector. Physical categorical storage collects no string evidence and does not convert labels. Frequency evidence is not collected. No current Identifier, Numeric, Categorical, or Text rule reads it. The retention limit is unchanged. No cardinality threshold is added. The four assessors then run on one bundle: the basic evidence, the physical dtype, and only the optional evidence that applies. They do not receive the Series. Missing evidence stays absent. A zero-filled object is not invented for an inapplicable family. `resolve_semantics` is the only resolution step. The pipeline does not reimplement supported-count logic. `build_inferred_semantic_result` is the only inferred-result constructor. It receives the physical dtype that was classified and the resolution that was produced. A candidate-derived selection stays without a `SemanticInterpretation` and without High, Medium, or Low. `INSUFFICIENT_EVIDENCE` is a normal result for ordinary strings, prose, mixed objects, and physical families that have no supported candidate, including complex storage. It is not an exception. There is no sampling, no mode, no configuration, no user override, no target, no dataset context, and no use of the Series name or index. `pytics.profile` and `pytics.compare` are not routed through this function. It is not exported from top-level `pytics`. The module path is not a frozen layout. |
| Rationale | The semantic components already existed as separate, tested contracts. Connecting them with a second inference engine, or by letting each stage recollect the same facts, would hide which observation is the source of truth. A structural reading does not need candidate evidence. A candidate that no current rule reads does not need its evidence collected. |
| Implications | `REQ-S-01`, `REQ-S-02`, `REQ-S-03`, `REQ-S-04`, and `REQ-S-05` are not completed. The pipeline is not the public semantic API and not the effective interpretation. [OPEN-044](#open-questions) stays open for candidate-derived confidence, partial patterns, numeric Identifier evidence, and any future rule between supported candidates. [OPEN-047](#open-047) stays open for that confidence, material alternatives, and the public result. [OPEN-045](#open-questions) stays open: `pipeline.py` is not a module-layout decision. [OPEN-004](#open-questions), [OPEN-009](#open-questions), [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-037](#open-questions), [OPEN-043](#open-questions), [OPEN-046](#open-046), [OPEN-048](#open-048), and [OPEN-049](#open-049) stay open. No later slice is approved. |
| Later update | [DEC-088](#dec-088) moves this orchestration to `analyze_series` and keeps `infer_series_semantics` as the wrapper that returns that analysis's inferred result. String-content evidence is no longer collected on the path. Semantic results are unchanged. Frequency evidence remains uncollected. |

## DEC-088

| | |
| --- | --- |
| Title | Dataset analysis retains one column analysis per physical column |
| Status | Accepted |
| Decision | TSK-017 adds an internal DataFrame analysis above the column pipeline. It is not a public profile result, not `ProfileResult`, and not the Dataset Overview. `pytics.analysis` owns `ColumnEvidence`, `ColumnAnalysis`, `DatasetAnalysis`, and `analyze_dataframe`. `pytics.semantics` keeps semantic inference. `analyze_series` in `pytics.analysis.column` is the only column collection and semantic orchestration. `infer_series_semantics` returns `analyze_series(series).inferred` and does not collect again. This narrows [OPEN-045](#open-questions). It does not freeze the rest of the package layout, and it does not move the existing semantic modules. `ColumnEvidence` stores `basic` and, when that path collected them, `numeric_structure`, `string_structure`, and `pattern`. `None` means the family was not collected. It does not mean a count was zero. The stored objects are the objects the collectors returned. `numeric_structure.basic` is `basic`. `string_structure.basic` is `basic`. `pattern.string_structure` is `string_structure`. There is no evidence dictionary, registry, or generic cache. `FrequencyEvidence` is not collected. No current candidate rule reads it. [DEC-078](#dec-078) collects it only when requested. `REQ-C-02`, `REQ-C-04`, and `REQ-C-05` are later categorical analysis, and the retained exact set stops at 32 distinct values, so it is not that frequency distribution. The field is absent. `StringContentEvidence` is not collected. TSK-016 computed it and discarded it. No candidate assessor reads it. [DEC-084](#dec-084) says those token aggregates do not support Text or ordinary-string Categorical and are not downstream text-profile diagnostics. [OPEN-019](#open-questions) still leaves open whether they belong in a text profile. `REQ-F-02` word counts are not this observation. The field is absent. The collector remains for a later consumer. A structural reading still returns after physical dtype, basic evidence, and structural resolution. Empty, Constant, Boolean, Datetime, and Timedelta do not collect numeric-structure, string-structure, or pattern evidence. The dataset facts in this slice use basic missing counts, which that path already has. Column identity is `position` and `label`. `position` is the column's place on the column axis. `label` is the original label object, including a non-string label and a MultiIndex key. Labels are not stringified and are not joined. Duplicate labels are separate records. Column order is source order. Columns are not stored in a dictionary keyed by label. A Series analyzed alone uses position `0` and label `None` unless the caller passes identity. That label is not taken from `Series.name`, and neither the name nor the index is semantic evidence. `DatasetAnalysis` stores `n_rows`, `n_columns`, `n_cells`, and `columns`. `n_cells` is `n_rows * n_columns`. `columns` is a tuple with one `ColumnAnalysis` per physical column. `n_missing_cells`, `n_non_missing_cells`, and `missing_ratio` are derived from those dimensions and from retained basic evidence. They are not stored and they do not scan again. `missing_ratio` is `None` when `n_cells` is zero. A zero numerator with a positive cell count is `0.0`. `n_non_missing_cells` is the count `n_cells - n_missing_cells`, including zero when there are no cells. A zero-row frame still analyzes each defined column. Those columns follow the current Empty rule. A zero-column frame has no column records. The analysis does not store the DataFrame or any Series. It does not copy the DataFrame to protect it, and it does not mutate values, the index, columns, dtypes, categorical metadata, or timezone metadata. `analyze_dataframe` accepts a pandas DataFrame only. A Series, mapping, list, ndarray, or other input raises `TypeError` and is not passed to the DataFrame constructor. Each physical column is passed to `analyze_series` once, by position. The inferred result on that record is the result of that call. The DataFrame path does not also call `infer_series_semantics`. It does not read other columns, the index, or labels as semantic evidence, and it does not run a second semantic pass. It does not emit findings or warnings for empty frames, duplicate labels, unresolved columns, or constants. It does not count duplicate rows, memory usage, or semantic-type composition. It does not add configuration, sampling, parallelism, or a progress report. `pytics.profile` and `pytics.compare` are unchanged. Nothing in this slice is exported from top-level `pytics`. |
| Rationale | Column evidence was already computed during semantic inference and then discarded, so a later dataset analysis would have had to scan again or lose the distinction between applicable evidence and a zero count. The dataset layer is the place that can keep those objects. Collecting a family that still has no consumer would repeat the discard, only one level higher. |
| Implications | `REQ-A-01` is not completed. Rows, columns, and cells are stored. Dataset dimensions beyond those three counts remain [OPEN-018](#open-questions). `REQ-A-02` is not implemented. Memory-usage semantics are not chosen. `REQ-A-03` is not completed. Derived missing-cell totals are not complete rows, incomplete rows, missing patterns, or co-missingness. `REQ-A-04` and `REQ-I-01` are not implemented. `REQ-A-05` is not implemented. A semantic-type count needs a policy for candidate-derived selections, insufficient evidence, and ambiguity. `REQ-S-01`, `REQ-S-02`, `REQ-S-03`, `REQ-S-04`, and `REQ-S-05` are not completed. No semantic rule changed. [OPEN-004](#open-questions), [OPEN-009](#open-questions), [OPEN-010](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-037](#open-questions), [OPEN-043](#open-questions), [OPEN-044](#open-questions), and [OPEN-047](#open-047) stay open. [OPEN-045](#open-questions) is narrowed only for this package boundary. No later slice is approved. |
| Later update | [DEC-089](#dec-089) consumes this analysis and does not change it. The overview copies the stored dimensions and the derived missing-cell totals. It counts resolved selected semantic types, including candidate-derived selections, and keeps insufficient evidence separate from ambiguity. It does not scan the DataFrame again. [DEC-090](#dec-090) adds `frequency` to `ColumnEvidence` and collects it for a non-structural physical categorical column. `frequency.basic` is `basic`. String-content evidence stays uncollected. The variables summary consumes the retained analysis and does not scan again. |

## DEC-089

| | |
| --- | --- |
| Title | Dataset overview aggregates resolved semantic state |
| Status | Accepted |
| Decision | TSK-018 adds an internal dataset overview in `pytics.analysis`. `build_dataset_overview` accepts one `DatasetAnalysis` and returns a `DatasetOverview`. It does not accept a DataFrame. A DataFrame, Series, or other object raises `TypeError` and is not analyzed. The builder does not import pandas. It does not call `analyze_dataframe`, `analyze_series`, `infer_series_semantics`, physical classification, evidence collectors, candidate assessors, or `resolve_semantics`. It does not mutate the analysis and does not store it. `DatasetOverview` is a frozen value. It is not `ProfileReport`, not a rendered overview, and not part of `pytics.profile` or `pytics.compare`. Nothing in this slice is exported from top-level `pytics`. Stored facts are `n_rows`, `n_columns`, `n_cells`, `n_missing_cells`, `n_non_missing_cells`, `semantic_type_counts`, and five column-reference tuples: insufficient evidence, ambiguous, empty, constant, and identifier. The three dimension counts are copies of the stored analysis facts. The two cell counts are copies of the analysis properties that already derive them from retained basic evidence. The overview does not sum Series values and does not walk basic evidence to recompute missingness. `missing_ratio` is `n_missing_cells / n_cells` when `n_cells` is positive, and `None` when there are no cells. `completeness_ratio` is `n_non_missing_cells / n_cells` on the same rule. It is cell completeness. It is not a complete-row ratio, and it is not semantic-resolution coverage. For a positive cell count the two ratios sum to 1 within ordinary floating-point arithmetic. A zero numerator with a positive cell count is `0.0`. A selected semantic type is the resolution's `selected_type` when `resolution.status` is `RESOLVED`. Otherwise the column has no selected semantic type. `interpretation` is not that test. A candidate-derived Numeric, Identifier, Categorical, or Text selection counts while `interpretation` is `None`. No High, Medium, or Low confidence is required, and none is assigned. `semantic_type_counts` is a tuple of `SemanticTypeCount` values. Each entry is one `SemanticType` and a positive count. Types with a zero count are omitted. Order is `SemanticType` definition order. That order is the enum's neutral definition order. It is not an importance ranking, not alphabetical order, and not a renderer order. Counts are per physical column. Duplicate labels are not merged. The aggregation walks `SemanticType` rather than a fixed chain of the types production currently reaches, so a later selected type, including Text or a future enum member, is counted without a new overview rule. `INSUFFICIENT_EVIDENCE` and `AMBIGUOUS` are not semantic types and are not merged. Each is a tuple of `ColumnRef` in source position order. `resolved_column_count` is the sum of the semantic type counts. `insufficient_evidence_column_count` and `ambiguous_column_count` are the lengths of those tuples. Those three counts sum to `n_columns`. `semantic_resolution_ratio` is `resolved_column_count / n_columns` when `n_columns` is positive, and `None` when the schema has no columns. An empty schema is not treated as fully resolved. Empty, Constant, and Identifier groups are the columns whose resolved selected type is that `SemanticType`. They are not re-derived from `n_non_missing`, `n_unique_non_missing`, uniqueness, names, or pattern evidence. A repeated UUID stays Constant because that is the selected type. Group counts are the lengths of the tuples. Each `ColumnRef` stores `position` and the original label object. Labels are not stringified. Label alone is not identity. Positions inside one group are strictly increasing, and a position is not repeated across the five groups. Boolean, Datetime, Timedelta, Numeric, Categorical, Text, and any other resolved type are counts only. This slice does not also split resolved columns into structural and candidate-selected counts. Both are `RESOLVED`. Confidence remains on the column analysis when a structural interpretation has one. A zero-column dataset has no column references, a semantic-count total of zero, and `semantic_resolution_ratio` `None`. A zero-cell dataset also has `missing_ratio` and `completeness_ratio` `None`. A zero-row dataset with defined columns follows the current Empty rule already on the analysis: every column is resolved Empty, the resolution ratio is `1.0`, and the cell ratios stay `None`. An all-missing populated dataset has `missing_ratio` `1.0` and `completeness_ratio` `0.0`. Its Empty columns are the columns the analysis already resolved as Empty. The dataset missing ratio does not classify columns. A dataset with no missing cells has completeness `1.0` even when some columns are unresolved. No memory usage is recorded. Shallow versus deep, pandas-reported versus estimated, and whether the index is included are still not decided, and the overview does not hold the DataFrame that would be measured. No duplicate-row or unique-row fact is recorded. It is still undecided whether the first occurrence counts as a duplicate, whether missing values compare equal, whether the count is extra rows or every row in a duplicate group, how unhashable values behave, and what unique-row count means. `DataFrame.duplicated` is not called. Near-constant columns, high-cardinality columns, physical-dtype composition, missing-like literals, confidence totals, findings, severity, and a composite quality score are not added. Resolver reason strings and evidence statements are not parsed. There is no configuration and no threshold. |
| Rationale | The analysis layer already holds dimensions, missing-cell totals, and one resolved semantic state per physical column. A summary that scanned the frame again, or that counted only columns with a `SemanticInterpretation`, would either duplicate that work or drop Numeric, Identifier, and Categorical. Cell completeness and semantic-resolution coverage answer different questions and use different denominators. |
| Implications | `REQ-A-01` is not completed. The overview exposes the three stored dimension counts. Further dataset dimensions remain [OPEN-018](#open-questions). The rendered Overview is not implemented. `REQ-A-02` is not implemented. Memory semantics were not chosen. `REQ-A-03` is not completed. Cell completeness is defined. Complete rows, incomplete rows, missing patterns, and co-missingness are not. `REQ-A-04` and `REQ-I-01` are not implemented. `REQ-A-05` is not completed. Resolved selected semantic types are counted. Physical dtype composition is not. Insufficient evidence and ambiguity stay outside the semantic-type count. `REQ-A-06` is not completed. Empty, Constant, and Identifier columns are grouped from the selected type. Near-constant and high-cardinality thresholds remain [OPEN-018](#open-questions). `REQ-IA-05` is not completed. The analytical facts can answer size, which resolved semantic types are present, and which named columns are unresolved or structurally notable. They do not say what dataset this is, and they are not a rendered view. No composite quality score was added. `REQ-P-07` remains the prohibition. `REQ-N-01` through `REQ-N-04` are not implemented. [OPEN-018](#open-questions) is narrowed for those three dimension counts and for the cell-completeness ratio. [OPEN-037](#open-questions) records TSK-018 as the slice after TSK-017 and does not choose the next slice. [OPEN-044](#open-questions) and [OPEN-047](#open-047) stay open: a counted candidate selection still has no confidence. [OPEN-045](#open-questions) stays open. `overview.py` is not a further layout decision. [OPEN-004](#open-questions), [OPEN-009](#open-questions), [OPEN-010](#open-questions), [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-019](#open-questions), [OPEN-043](#open-questions), [OPEN-046](#open-046), [OPEN-048](#open-048), and [OPEN-049](#open-049) stay open. No later slice is approved. |
| Later update | [DEC-090](#dec-090) adds a separate variables summary. It does not change this overview. |

## DEC-090

| | |
| --- | --- |
| Title | Variables summary follows the selected semantic type |
| Status | Accepted |
| Decision | TSK-019 adds an internal variables summary in `pytics.analysis`. `build_variables_summary` accepts one `DatasetAnalysis` and returns a frozen `VariablesSummary`. It does not accept a DataFrame. A DataFrame, Series, or other object raises `TypeError` and is not analyzed. The builder does not import pandas. It does not call `analyze_dataframe`, `analyze_series`, `infer_series_semantics`, physical classification, evidence collectors, candidate assessors, or `resolve_semantics`. It does not mutate the analysis and does not store the analysis, a `ColumnAnalysis`, a DataFrame, or a Series. `VariablesSummary` stores `variables`, a tuple with one `VariableSummary` per physical column, in source order. `n_variables` is the length of that tuple. Positions are `0` through `n_variables - 1`. Duplicate labels stay distinct. Labels are the original objects, including a non-string label and a MultiIndex key. They are not stringified. The summary is not keyed by label. Every variable in one summary shares `n_total`. The summary does not copy dataset-overview facts. `VariableSummary` stores `position`, `label`, `physical`, `resolution_status`, `selected_type`, `n_total`, `n_missing`, `n_non_missing`, `n_unique_non_missing`, and an optional `detail`. `physical` is the existing `PhysicalDtype`, including `categorical_ordered` and a timezone-aware family. It is not a display string. `selected_type` is present only when `resolution_status` is `RESOLVED`. Otherwise it is absent. `interpretation is not None` is not that test. A candidate-derived Numeric, Identifier, or Categorical selection is resolved while its interpretation is absent. Confidence and `InferenceSource` are not copied. A candidate-derived selection has neither, and this result does not invent them. `None` is not mapped to Low. The four counts come from retained `BasicColumnEvidence`. `missing_ratio` is `n_missing / n_total` when `n_total` is positive, and `None` when the column has no rows. `unique_ratio_non_missing` is `n_unique_non_missing / n_non_missing` when `n_non_missing` is positive, and `None` otherwise. There is no competing ratio over all rows. The excess `n_non_missing - n_unique_non_missing` is not stored as a separate duplicate count and does not remove Identifier. `detail` follows the selected semantic type, not the physical dtype. `NumericVariableDetail` is copied from retained `NumericStructureEvidence` when the selected type is Numeric and that evidence is present. It stores the structural counts and the monotonicity flags. `infinity_count` is the sum of the two infinity counts. `finite_ratio` divides by non-missing values. The sign ratios, `zero_ratio`, and `integer_like_ratio` divide by finite values. An undefined ratio is `None`. Monotonicity `None` stays unknown. Minimum, maximum, mean, median, standard deviation, quantiles, skewness, kurtosis, and outlier signals are not added. `CategoricalVariableDetail` is copied from retained `FrequencyEvidence` when the selected type is Categorical and that evidence is present. It stores `most_frequent_count` and `singleton_count`. `most_frequent_ratio` divides by non-missing values. `singleton_ratio` divides by distinct non-missing values. The most frequent value is not retained. The exact value set and the per-value frequency table are not copied. Unobserved categorical levels stay out of the counts, as the collector already removes them. `categorical_ordered` stays on the physical dtype. It is not an ordinal reading. `IdentifierVariableDetail` is copied from retained `PatternEvidence` when the selected type is Identifier and that evidence is present. It stores the seven pattern counts. Each ratio divides by non-missing values. A compact UUID may increment both the UUID count and the 32-character hexadecimal count. Those counts are not scores and are not added together. No identifier confidence is stored. Duplicate UUID values stay Identifier. A repeated UUID stays Constant because that is the selected type, and it has no Identifier detail. Pattern evidence on a column that was not selected as Identifier, including IPv4 strings, does not create Identifier detail. Empty, Constant, Boolean, Datetime, Timedelta, Text, insufficient evidence, and ambiguity have no specialized detail. The constant value is not retained, because basic evidence does not store it and this slice does not rescan to recover it. Boolean true and false counts are not added. Datetime and timedelta descriptive facts are not added. String-structure evidence on an unresolved string does not become Text detail. Numeric-structure evidence on an unresolved or ambiguous column does not become Numeric detail. A selected type whose evidence was not collected has common facts and no detail. `analyze_series` now collects `FrequencyEvidence` for a non-structural physical categorical column and stores it on `ColumnEvidence.frequency`. `frequency.basic` is that column's `basic`. The collector contract is unchanged. Empty, Constant, Boolean, Datetime, Timedelta, numeric, string, and object columns do not collect it. The assessors do not receive it. `StringContentEvidence` stays uncollected. No new collector and no descriptive-statistics family were added. The product detail copies analytical counts. It does not store the evidence object. No finding, threshold, renderer string, chart, or public export was added. `pytics.profile` and `pytics.compare` are unchanged. |
| Rationale | A column summary that only renamed `ColumnAnalysis` would not be an analytical surface, and a summary that computed every Product Contract B–G statistic would invent methods and thresholds this evidence does not support. The retained structural, frequency, and pattern facts are enough to make Numeric, Categorical, and Identifier columns useful while the other selected types stay honest common facts. Specialized detail has to follow the selected semantic type, or a UUID string would be described as text and a repeated UUID as an identifier. |
| Implications | `REQ-B-01` is not completed. Count, missing, distinct, zeros, negatives, and infinities are available for a Numeric variable from basic evidence and numeric-structure evidence. Minimum, maximum, range, and sum are not. `REQ-B-02` through `REQ-B-06` are not implemented. `REQ-C-01` is not completed. Count, missing, distinct, and `unique_ratio_non_missing` are on every variable, including a Categorical one. The rendered categorical analysis is not. `REQ-C-02` is not completed. The most frequent count and ratio are available. The mode value, top categories, rare categories, and bottom categories are not. `REQ-C-04` is not completed. Singleton count and ratio are available. Rare-category percentage needs a threshold that remains [OPEN-018](#open-questions). `REQ-C-03`, `REQ-C-05`, `REQ-C-06`, and `REQ-C-07` are not implemented. The frequency distribution is not retained. `REQ-G-01` is not completed. Identifier is a selected type with pattern counts on the variable. Exclusion from later multivariate analysis is not this slice. `REQ-G-02` is not completed. The pattern counts are exposed as structured facts. The candidate's evidence statements are not copied, and no confidence is assigned. `REQ-IA-07` is not completed. The analytical variable rows and type-specific details exist. The searchable table and the rendered disclosure do not. `REQ-D-01` through `REQ-D-03`, `REQ-E-01`, `REQ-E-02`, and `REQ-S-07` are not advanced by new Boolean, Datetime, or Timedelta facts. [OPEN-043](#open-questions) is narrowed only for this detail rule: specialized detail follows the selected semantic type. That is not the downstream eligibility matrix. [OPEN-044](#open-questions) stays open. Collecting frequency evidence for a categorical variable is not an inference threshold, and candidate confidence is still unset. [OPEN-045](#open-questions) is narrowed only by placing the product summary in `pytics.analysis` and leaving `FrequencyEvidence` in `pytics.semantics`. `variables.py` is not a layout freeze. No descriptive-statistics collector was added under `pytics.semantics`. [OPEN-037](#open-questions) records TSK-019 as the slice after TSK-018 and does not choose the next slice. [OPEN-014](#open-questions), [OPEN-016](#open-questions), [OPEN-018](#open-questions), [OPEN-019](#open-questions), [OPEN-046](#open-046), [OPEN-047](#open-047), [OPEN-048](#open-048), and [OPEN-049](#open-049) stay open. No later slice is approved. |

## Open questions

These are not decisions. Do not implement an answer.

<a id="open-questions"></a>

### OPEN-001

Are the "such as" and "may include" concept lists a closed set of mandatory outputs, an open in-scope set, or illustrative examples? This memory treats the parent areas as accepted and preserves the qualifiers. It does not treat every named statistic as an always-on output.

### OPEN-002

Which decisions would count as "unnecessary" blockers to a future non-pandas engine, given that a Polars or Arrow abstraction is out of scope now? [DEC-040](#dec-040) and the "Polars is not core" direction in [DEC-060](#dec-060) do not answer this.

### OPEN-004

What are the public function signatures, result types, and attribute names? DataFrame-only `profile` and `compare` are accepted ([DEC-040](#dec-040)). The illustrative `ProfileReport` and `ComparisonReport` shapes are not frozen. The compare sketch also omits duplicate changes that compare navigation includes. The configuration object is [OPEN-009](#open-questions). The split between inferred interpretation and effective interpretation, and the result representation of a semantic override, are part of this question ([DEC-075](#dec-075)). Exact Empty or Constant override behavior is [OPEN-049](#open-049).

### OPEN-006

What is the exact method catalog, and which dependencies does it require? [DEC-055](#dec-055) accepts pair-type direction and does not close the catalog. Still unset: numeric-by-binary effect-size formula and fallback; ANOVA, Welch, or rank-based selection for numeric-by-categorical; default binary-by-binary measures; exact or resampling rules for sparse categorical tables; datetime relationship methods; ordinal relationship methods where [DEC-052](#dec-052) applies; pair types with no direction yet, including text and timedelta; which deep-mode robust methods are included; and the dependency that implements each method. `REQ-K-03` remains in force.

### OPEN-007

What is a statistical test family inside Pytics, and therefore when multiple-testing correction applies? [DEC-056](#dec-056) prefers false-discovery-rate control for broad relationship screening, with Benjamini-Hochberg as the leading candidate, and requires raw and adjusted p-values to stay distinct. Benjamini-Hochberg is not an unconditional rule. Correction behavior is not final until the family is defined.

### OPEN-008

Which analyses receive a Bayesian treatment, and what is the exact method catalog? [DEC-057](#dec-057) keeps Bayesian analysis selective and lightweight. NumPy and SciPy are the current calculation direction. PyMC is not intended as a core dependency at present. Binary-by-binary association is a strong candidate. No domain threshold has been selected. A threshold, if used, must come from an established convention or explicit user configuration. Final library choice beyond that direction is [OPEN-042](#open-questions).

### OPEN-009

What is the configuration-object shape, and where do random seed and other reproducibility controls live? Future reproducible configuration should be able to carry semantic overrides ([DEC-075](#dec-075)). That direction does not decide the shape.

### OPEN-010

What are the exact contents, cost thresholds, and sample sizes of `quick`, `standard`, and `deep`? The three names, and standard as the intended default, are accepted ([DEC-058](#dec-058)). The lists in that decision are not a closed catalog. Controlled sampling for expensive semantic evidence is accepted ([DEC-054](#dec-054)). Its thresholds and sample sizes, and sampling rules for other analyses, are part of this question. Procedure-provenance fields are not frozen ([DEC-076](#dec-076)). The mode-selection signature is not accepted. Frequency evidence in v0.1 is exact, full-column, and unsampled ([DEC-078](#dec-078)). Numeric-structure evidence is also exact, full-column, and unsampled ([DEC-079](#dec-079)). String-structure evidence is also exact, full-column, and unsampled ([DEC-080](#dec-080)). Pattern evidence is also exact, full-column, and unsampled ([DEC-081](#dec-081)). None of those choices sets the contents, thresholds, or sample sizes of the three modes. String-content evidence is also exact, full-column, and unsampled ([DEC-084](#dec-084)). That choice does not set them either.

### OPEN-013

Which estimator family is used for the diagnostic classification model, and which for regression? Holdout or cross-validation, and held-out permutation importance, are accepted direction ([DEC-059](#dec-059)). Do not select Random Forest, Extra Trees, gradient boosting, or another estimator as the answer to this question until a decision does so.

### OPEN-014

Which subtypes exist under the minimum semantic types? Continuous and Discrete are permitted numeric concepts, and that inference stays conservative ([DEC-049](#dec-049)). Boolean/Binary representation is not set ([DEC-047](#dec-047), [DEC-074](#dec-074)). The contract allows a binary interpretation that is not necessarily Boolean. `SemanticType.BOOLEAN` cannot fully express that distinction. Whether Binary is its own semantic type, a subtype, a semantic property, or another representation is this question. Where URL-like, email-like, path-like, and generic string sit is also this question. Integer dtype is not a discrete subtype, and float dtype is not a continuous subtype, without the observed values. Integer-like counts are observations ([DEC-079](#dec-079)). They do not decide Continuous or Discrete. String-structure counts and length bounds are observations ([DEC-080](#dec-080)). They do not place generic string, URL-like, email-like, or path-like roles. Pattern counts for UUID, IPv4, IPv6, and fixed-width hexadecimal tokens are also observations ([DEC-081](#dec-081)). They do not place those roles, and email-like, URL-like, and path-like patterns are not recognized by that family. Do not close this question by overloading the optional subtype string. Ordinal storage is [OPEN-016](#open-questions), not this question. `{0.0, 1.0}` as binary evidence is [OPEN-046](#open-046). A Numeric candidate for physical `{0, 1}` storage ([DEC-083](#dec-083)) is not a binary-not-Boolean representation. Two string labels are not given a Categorical candidate by that decision. Neither fact chooses Binary's representation. Alphanumeric token counts and token-vocabulary aggregates are observations ([DEC-084](#dec-084)). They do not place generic string, Text, or Categorical, and they do not choose Binary. A physical Boolean variable has no true/false counts in the variables summary ([DEC-090](#dec-090)). That absence does not choose Binary's representation. `{0, 1}` and `{0.0, 1.0}` stay Numeric variables.

### OPEN-016

When ordinal semantics are accepted under [DEC-052](#dec-052), is that interpretation its own semantic type, a categorical subtype, or only a relationship case? The rule against inventing order is decided. `categorical_ordered` remains physical metadata and stays inspectable under Empty, Constant, and a later Categorical reading. That preservation does not answer this question. Do not treat a free-string subtype as the answer. A Categorical candidate for an ordered pandas categorical dtype ([DEC-083](#dec-083)) does not choose this storage question. The variables summary keeps `categorical_ordered` on the physical dtype and attaches Categorical frequency detail, not an ordinal detail ([DEC-090](#dec-090)). This storage question is not decided.

### OPEN-018

Operational definitions are unset for: dataset dimensions beyond row, column, and cell counts, computational-analysis metadata, near-constant, high cardinality, rare category, cardinality band thresholds, the missing-like literal list, and "controlled" partial duplicates. TSK-018 copies `n_rows`, `n_columns`, and `n_cells` onto the dataset overview and defines cell completeness as `n_non_missing_cells / n_cells`, which is `None` when `n_cells` is zero ([DEC-089](#dec-089)). That ratio is not a complete-row ratio and does not add a further dimension. Memory-usage semantics and duplicate-row semantics are not part of this narrowing. Near-constant and high-cardinality thresholds remain unset. The v0.1 exact-value retention limit of 32 distinct non-missing values is an operational storage guard ([DEC-078](#dec-078)). It is not a near-constant threshold, a high-cardinality threshold, a cardinality band, or a missing-like literal rule. Empty-string and whitespace-only counts are string-structure observations ([DEC-080](#dec-080)). They do not define the missing-like literal list. Distinct-token and singleton-token counts are string-content observations ([DEC-084](#dec-084)). They do not define near-constant, high cardinality, rare category, or a cardinality band. Variable-level most-frequent and singleton ratios ([DEC-090](#dec-090)) are the frequency-evidence ratios. They do not define those bands.

### OPEN-019

Are trimmed mean and common-token text diagnostics in scope? Both were worded as potential. [DEC-084](#dec-084) collects exact token-occurrence counts, the zero-token, one-token, and multiple-token partition of non-missing strings, total character count, and aggregate token-vocabulary counts: distinct tokens, singleton tokens, and the occurrence count of the most frequent token. Those are structural observations. They do not retain the vocabulary, they are not downstream text-profile diagnostics, and they do not support a Text or Categorical candidate. The evidence-collection portion of a common-token observation is therefore recorded. Whether those aggregates belong in a text profile, and whether any token fact should support Text or Categorical, remain open. No token-count, length, or vocabulary threshold is approved. Trimmed mean remains open. String-structure evidence still does not count tokens ([DEC-080](#dec-080)). Pattern evidence still does not count them either ([DEC-081](#dec-081)). The variables summary does not collect string-content evidence and does not add a Text detail ([DEC-090](#dec-090)).

### OPEN-020

If fuzzy or near-duplicate analysis, or deep time-series diagnostics, are built later, what is their scope? [DEC-031](#dec-031) only says they are not default. [DEC-055](#dec-055) does not define that scope. Datetime relationships may ask about trend, change, association, or periodic structure when justified. That is not a default diagnostic pass on every datetime column.

### OPEN-022

Which univariate outlier methods and which multivariate anomaly methods are used, and what does explainability require? scikit-learn is the candidate home for multivariate anomaly methods ([DEC-060](#dec-060)). That does not select an estimator.

### OPEN-023

Which target problem types beyond a classification or regression interpretation must be recognized?

### OPEN-024

In what order is compare coverage delivered, and is comparison limited to exactly two datasets?

### OPEN-025

Are finding levels exactly information, notable, and warning, or a different restrained vocabulary?

### OPEN-026

Does dark mode ship, or is it only permitted?

### OPEN-027

Is a "Generated with Pytics" link required, optional, or absent?

### OPEN-028

How does navigation behave below desktop width? Only a desktop sidebar was specified.

### OPEN-029

What About narrative, motivation, and contact details should be shown? Do not invent them. Do not promote the 1.1.5 template blurb.

### OPEN-032

Do the 1.1.5 hard limits of 1,000,000 rows and 1,000 columns continue, change, or disappear? Mode names are accepted ([DEC-058](#dec-058)). Exact mode behavior is [OPEN-010](#open-questions). Neither decides these limits.

### OPEN-033

Repository hygiene, not a product decision: should the tracked `.venv-py311/` tree, `test_report.html`, `test_report.pdf`, `pyproject.toml.bak`, and similar artifacts remain? This planning task does not add, delete, or untrack them.

### OPEN-035

Which libraries are the final choice for interactive HTML and static PDF? [DEC-061](#dec-061) sets the direction: Jinja2, Plotly, and restrained custom JavaScript for standalone HTML; WeasyPrint as the leading PDF candidate; xhtml2pdf is not the 2.0 architecture. Versions are not pinned. The Plotly static-graphics problem is [OPEN-041](#open-questions).

### OPEN-036

Which Python versions does 2.0 support? Do not set `requires-python` until compatibility is checked across the dependency stack that is actually accepted. Python 3.14 compatibility matters because it is part of the known local development baseline. Do not require 3.14 if a broader modern range is supportable. The 1.1.5 floor (`>=3.8`) and CI range (3.9–3.11) are not this decision. Final dependency versions are [OPEN-042](#open-questions).

### OPEN-037

In what order are accepted requirements turned into approved slices? TSK-017 is the internal dataset-analysis foundation after the column pipeline ([DEC-088](#dec-088)). TSK-018 is the dataset-overview slice after that analysis ([DEC-089](#dec-089)). TSK-019 is the variables summary after that overview ([DEC-090](#dec-090)). It does not choose the slice after that.

### OPEN-038

What is the exact internal API of the shared statistical layer, and where is reuse analytically appropriate rather than target-specific? [DEC-037](#dec-037) accepts the layer and leaves this boundary open.

### OPEN-039

What are the method registry's schema and API? [DEC-038](#dec-038) accepts the concept. The metadata list there is illustrative, not a schema. Do not implement the registry.

### OPEN-041

How should interactive Plotly visualizations become reliable static graphics for PDF without imposing fragile system dependencies? [DEC-061](#dec-061) leaves this unresolved on purpose. Kaleido is neither selected nor rejected.

### OPEN-042

What are the final 2.0 dependency versions, and which candidate directions become a lock? [DEC-060](#dec-060) is not that lock. IPython remains unresolved until a packaging review. Do not pin versions and do not install the candidate stack from the planning documents.

### OPEN-043

What are the exact analysis-eligibility rules for each semantic type? [DEC-053](#dec-053) gives direction only. Downstream analysis uses the effective interpretation where applicable ([DEC-075](#dec-075)). Physical applicability still limits which analyses can run without coercion. Exact error and warning behavior is not decided. The Empty or Constant override case is [OPEN-049](#open-049). TSK-018 does not decide eligibility ([DEC-089](#dec-089)). TSK-019 attaches specialized variable detail only for the selected semantic type: numeric structure for Numeric, frequency counts for Categorical, and pattern counts for Identifier ([DEC-090](#dec-090)). Unresolved and ambiguous columns have no specialized detail. That applicability rule is not the downstream eligibility matrix.

### OPEN-044

What are the exact semantic-inference thresholds? [DEC-048](#dec-048) rejects uniqueness alone as an identifier rule and does not set numeric cutoffs. [DEC-068](#dec-068) also rejects perfect uniqueness and zero missingness as definitional requirements for Identifier. The universal derived property `unique_ratio_non_missing` divides distinct non-missing values by the non-missing count, and is undefined when that count is zero ([DEC-077](#dec-077)). That property is not an Identifier rule, and it does not create a `unique_ratio` alias. `most_frequent_ratio` and `singleton_ratio` are frequency observations with the denominators in [DEC-078](#dec-078). They are not inference thresholds. `finite_ratio`, the sign ratios, and `integer_like_ratio` are numeric-structure observations with the denominators in [DEC-079](#dec-079). They are not inference thresholds. The six string-structure ratios divide by `n_non_missing` and are undefined when that count is zero ([DEC-080](#dec-080)). They are not Text, Categorical, or Identifier thresholds. The seven pattern ratios also divide by `n_non_missing` and are undefined when that count is zero ([DEC-081](#dec-081)). They are not Identifier, Text, or pattern-agreement thresholds. UUID counts and fixed-width hexadecimal counts are observations. They do not decide whether UUID-like or hash-like structure can be sufficient alone. The hexadecimal counts are not hash-algorithm names. Minimum and maximum string length are not a Text cutoff. Monotonicity flags are not a sequential-identifier rule. Regular-step semantics are not decided. The 32-value retention limit is not an Identifier, Categorical, Text, or Binary cutoff. Identifier uniqueness thresholds, positive-evidence checklists, and any other use of uniqueness are not decided. UUID-like and hash-like structure remain accepted Identifier evidence ([DEC-072](#dec-072)). [DEC-082](#dec-082) accepts a full non-missing population of UUID syntax, or of one supported fixed-width ASCII hexadecimal width, as sufficient for an Identifier candidate assessment of SUPPORTED. That rule is the conservative initial candidate rule for the current evidence foundation. It is not a selected Identifier interpretation, not High, Medium, or Low confidence, and not a ban on a future partial-pattern rule. A smaller ratio, a union of different patterns, IPv4, IPv6, uniqueness, missingness, and numeric monotonicity do not support that candidate. Whether a partial pattern can support Identifier, whether numeric sequence evidence can support it, and whether any of these facts can select Identifier, remain part of this question. Column-name evidence, dataset-context evidence, and final confidence for a candidate-derived reading also remain open. How already supported candidates are resolved is [DEC-085](#dec-085). [DEC-083](#dec-083) does not set a cardinality, uniqueness, length, or whitespace threshold. Non-empty, non-constant physical integer or floating storage supports a Numeric candidate without a distribution cutoff. Non-empty, non-constant physical categorical storage supports a Categorical candidate. Repetition is not an operational Categorical rule for untyped strings or numeric codes. Current string-structure facts do not support a Text candidate. Whether a future vocabulary rule, length rule, or word-count observation should support those candidates remains part of this question. [DEC-084](#dec-084) records `zero_token_ratio`, `one_token_ratio`, `multiple_token_ratio`, `mean_tokens_per_non_missing`, and `mean_characters_per_non_missing`, each divided by `n_non_missing` and undefined when that count is zero. `token_singleton_ratio` divides singleton tokens by distinct tokens and is undefined when there is no distinct token. `most_frequent_token_ratio` divides the most frequent token's occurrences by all token occurrences and is undefined when there is no token. None of those is a Text, Categorical, or Identifier threshold. A column in which every non-missing string has one token, and a column in which a string has several tokens, do not by themselves support Categorical or Text. No token-count, vocabulary, or length threshold was added. Sampling sizes are [OPEN-010](#open-questions). Candidate Resolution v0.1 does not close these questions with a numeric score ([DEC-066](#dec-066)). [DEC-085](#dec-085) resolves a structural reading, or exactly one supported candidate, without a threshold and without a numeric total. No supported candidate is insufficient evidence. More than one supported candidate stays ambiguous. No Identifier-over-Numeric rule was added. Final confidence for a candidate-derived reading, partial-pattern thresholds, numeric sequence Identifier evidence, and any future rule that would select between supported candidates remain part of this question. [DEC-086](#dec-086) keeps a candidate-derived selection without a confidence-bearing interpretation. It does not close that confidence question. [DEC-087](#dec-087) reaches that selection from one Series and still does not close it. [DEC-088](#dec-088) reaches the same selection from each DataFrame column and still does not close it. [DEC-089](#dec-089) counts that selected type in the dataset overview without a `SemanticInterpretation` and without High, Medium, or Low. That count is not confidence. [DEC-090](#dec-090) collects frequency evidence for a non-structural physical categorical column and exposes most-frequent and singleton counts on a Categorical variable. No candidate rule reads those facts. They are not a new threshold. The variables summary does not assign High, Medium, or Low to a candidate-derived selection.

### OPEN-045

What is the module and file layout? [DEC-036](#dec-036) accepts the engine diagram as direction only. [DEC-064](#dec-064) accepts the semantic pipeline as a conceptual analytical pipeline only. [DEC-076](#dec-076) accepts evidence cost levels as conceptual layering only. None of those is a module layout. TSK-016 added `src/pytics/semantics/pipeline.py` as the Series wrapper. TSK-017 narrows the boundary ([DEC-088](#dec-088)): `pytics.semantics` owns semantic inference, and `pytics.analysis` owns the column and dataset analytical records, the single column orchestration in `analyze_series`, and the DataFrame traversal in `analyze_dataframe`. `infer_series_semantics` remains the Series wrapper. TSK-018 adds `overview.py` in that same analysis package ([DEC-089](#dec-089)). The file is not a further layout decision. TSK-019 adds `variables.py` in that same package ([DEC-090](#dec-090)). The product variable summary stays in `pytics.analysis`. `FrequencyEvidence` stays in `pytics.semantics`. No descriptive-statistics collector was added under `pytics.semantics`. That file is not a further layout decision. The rest of the package layout is not frozen. Public result names remain [OPEN-004](#open-questions).

### OPEN-046

Is `{0.0, 1.0}` binary-candidate evidence? [DEC-047](#dec-047) permits `{0, 1}` as a possible binary interpretation and does not decide the floating-point pair. [DEC-074](#dec-074) does not accept `{0.0, 1.0}`. Numeric-structure evidence can count that pair as two finite integer-like values ([DEC-079](#dec-079)). That observation does not accept the pair as binary evidence. Physical numeric `{0, 1}` and `{0.0, 1.0}` may support a Numeric candidate ([DEC-083](#dec-083)). That support is not binary evidence. The variables summary gives both pairs Numeric detail ([DEC-090](#dec-090)). Do not implement either pair as binary evidence while this question is open.

### OPEN-047

The inferred result represents post-resolution abstention and ambiguity. `InferredSemanticResult` carries the observed physical dtype and the `SemanticResolution` ([DEC-086](#dec-086)). `INSUFFICIENT_EVIDENCE` means no structural reading was supplied and no candidate is supported. `AMBIGUOUS` means more than one candidate is supported and no reviewed rule selects between them. Neither status is a `SemanticType`. On the inferred result, neither status has a `SemanticInterpretation` or a selected type. That is a valid inferred state. It is not an error, and it is not `None` from `interpret_series_precedence`. A structural `RESOLVED` result keeps the existing interpretation. A candidate-derived `RESOLVED` result keeps the selected semantic type and does not yet have a `SemanticInterpretation`, because no High, Medium, or Low confidence is assigned ([DEC-085](#dec-085), [DEC-086](#dec-086)). What remains open is candidate-derived confidence, material alternatives once one reading is selected while another stays plausible, and how a public result should represent these states. Do not treat candidate counts as confidence. Do not turn ambiguity into a low-confidence selected reading. TSK-016 now produces this inferred result from one Series ([DEC-087](#dec-087)). TSK-017 keeps that same inferred result on each column analysis ([DEC-088](#dec-088)). Neither orchestration assigns candidate-derived confidence. TSK-018 counts a resolved selected type, including a candidate-derived selection that has no `SemanticInterpretation` ([DEC-089](#dec-089)). That count does not assign confidence. TSK-019 represents insufficient evidence and ambiguity as variable states with no selected type and no specialized detail ([DEC-090](#dec-090)). It does not assign candidate-derived confidence, and it does not turn ambiguity into a selected reading.

### OPEN-048

Is an evidence-strength enum ever needed? [DEC-066](#dec-066) keeps evidence role, evidence strength, and resolution confidence distinct, and does not introduce an evidence-strength enum for Candidate Resolution v0.1. User-facing confidence remains High, Medium, and Low.

### OPEN-049

What is the exact behavior when a user override meets an Empty or Constant column? [DEC-075](#dec-075) accepts override direction and does not freeze this case. Exact error and warning behavior for other overrides is also unset. Result and configuration shapes remain [OPEN-004](#open-questions) and [OPEN-009](#open-questions).

## Resolved open questions

Resolved items stay here so the original question is not lost. They are not active decisions.

### OPEN-003

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-036](#dec-036) |
| Original question | Is the engine diagram in [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) adopted, modified, or discarded? |
| Resolution | Adopted as architectural direction, in the refined diagram. The bootstrap sketch is not a second active proposal. Class, module, and file layout remain [OPEN-045](#open-questions). |

### OPEN-005

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-055](#dec-055) |
| Original question | Which relationship pair types are actually supported? |
| Resolution | Accepted direction covers numeric–numeric, numeric–binary, numeric–categorical, binary–binary, categorical–categorical, datetime–numeric, and datetime–categorical. Ordinal pairs apply only where ordinal semantics are accepted. This is not a closed catalog. Exact methods remain [OPEN-006](#open-questions). Pair types with no direction yet are not rejected by omission. |

### OPEN-011

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-037](#dec-037) |
| Original question | Is there one shared statistical layer for relationships, target, missingness relationships, compare, and drift, and what is its boundary? |
| Resolution | Yes. Those uses share one layer wherever analytically appropriate. The exact API and that boundary continue as [OPEN-038](#open-questions). |

### OPEN-012

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-038](#dec-038) |
| Original question | Is a method registry adopted, and what metadata does an entry carry? It must not be built before that decision. |
| Resolution | The concept is adopted. The metadata list is illustrative, not an accepted schema. Schema and API continue as [OPEN-039](#open-questions). Do not implement it. |

### OPEN-015

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-051](#dec-051) |
| Original question | Timedelta is a semantic type. What analysis, if any, is required for it? No timedelta section was specified. |
| Resolution | Dedicated duration analysis is required, with duration semantics and readable units. The named measures are in-scope concepts, not proof that each is always emitted ([OPEN-001](#open-questions)). User-facing results are not raw nanoseconds. |

### OPEN-017

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-046](#dec-046) |
| Original question | How do the Constant and Empty semantic types relate to the same facts reported at dataset level? |
| Resolution | They are both the semantic interpretation and the dataset fact. Do not duplicate the underlying computation unnecessarily. |

### OPEN-021

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-048](#dec-048) |
| Original question | Is the identifier evidence list a closed detector specification or a set of admissible signals? |
| Resolution | Admissible signals, not a closed detector. `unique_ratio == 1` alone is not sufficient. Thresholds remain [OPEN-044](#open-questions). |

### OPEN-030

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-039](#dec-039) |
| Original question | How does 2.0 coexist with the 1.1.5 tree and the public `profile` / `compare` imports while it is built? In-place replacement is not decided. |
| Resolution | The end state is replacement inside `src/pytics`, with no permanent parallel package. Temporary coexistence was left as [OPEN-040](#open-040), later resolved by [DEC-063](#dec-063). |

### OPEN-031

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-040](#dec-040) |
| Original question | Which inputs besides a pandas DataFrame are in scope? The 1.1.5 README claims CSV and Parquet paths. The 2.0 API is not frozen, and pandas-first does not by itself accept or reject paths. |
| Resolution | Core is DataFrame-only. Core does not load CSV, Parquet, or other paths. Exact signatures remain [OPEN-004](#open-questions). |

### OPEN-034

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-060](#dec-060) |
| Original question | What is the outcome of the required current-ecosystem dependency review? |
| Resolution | The outcome is the candidate directions in [DEPENDENCIES.md](DEPENDENCIES.md). It is not a lock and not a set of pins. Final versions continue as [OPEN-042](#open-questions). |

### OPEN-040

| | |
| --- | --- |
| Status | Resolved |
| Resolved by | [DEC-063](#dec-063) |
| Original question | How does 2.0 temporarily coexist with the 1.1.5 tree and the public `profile` / `compare` imports during migration? [DEC-039](#dec-039) accepts the end state: replacement inside `src/pytics`, with no permanent second package. Git history is the long-term archive. This question is the mechanics only. Do not delete or move current code while it is open. |
| Resolution | Build incrementally in place inside `src/pytics`. Keep each 1.1.5 component until its replacement has been specified, implemented, tested, and verified. Temporary internal coexistence is allowed. Do not add a permanent second public package. TSK-001 did not delete 1.1.5 code and did not change `profile` or `compare`. |

## Superseded decisions

No decision is withdrawn in full.

| Decision | Superseded part | By |
| --- | --- | --- |
| [DEC-018](#dec-018) | The implication that permutation importance was only a discussion. The one-model boundary stands. | [DEC-059](#dec-059) |
| [DEC-025](#dec-025) | The rationale clause that the pipeline sketch is unadopted. Analysis/render separation stands. | [DEC-036](#dec-036) |
| [DEC-027](#dec-027) | The statement that the ecosystem review had not been done, and that the named libraries carried no direction. The prohibition on installing or pinning a stack stands. | [DEC-060](#dec-060) |
| [DEC-041](#dec-041) | The conceptual stage list as the current pipeline description. Physical dtype, observed characteristics, and semantic interpretation remain distinct. Retained fields and sources remain. The stages are still not a frozen function decomposition. | [DEC-064](#dec-064) |

