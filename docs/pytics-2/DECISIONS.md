# Decision log

Accepted decisions from the Pytics 2.0 bootstrap briefing, recorded 2026-10-03, from the architecture and methodology update recorded the same day, and from Slice 001 recorded the same day.

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

## DEC-042

| | |
| --- | --- |
| Title | User-facing confidence is High, Medium, or Low |
| Status | Accepted |
| Decision | User-facing confidence is High, Medium, or Low, together with concrete evidence. Do not expose pseudo-precise confidence such as `0.87321` unless a future statistically justified reason exists. Internal scores may help conflict resolution. They must not become unexplained user-facing precision. |
| Rationale | A long decimal implies a measurement the inference procedure does not have. |
| Implications | `REQ-S-02`. |

## DEC-043

| | |
| --- | --- |
| Title | Ambiguity stays visible |
| Status | Accepted |
| Decision | Pytics does not have to treat every semantic inference as certain. Uncertainty is exposed. A selected interpretation may carry medium or low confidence and a relevant alternative. The example of a `score` column read as numeric discrete, with ordinal categorical as an alternative because no order was supplied, is accepted product behavior. |
| Rationale | Hiding a plausible alternative presents a guess as a fact. |
| Implications | `REQ-S-02`, `REQ-S-04`. Ordinal policy is [DEC-052](#dec-052). |

## DEC-044

| | |
| --- | --- |
| Title | User semantic overrides |
| Status | Accepted as a capability. The API is not accepted. |
| Decision | Explicit semantic configuration for individual variables is a first-class capability. Explicit user intent normally takes precedence over inference. If the configured interpretation cannot be meaningfully applied to the observed data, Pytics reports the conflict. It does not silently coerce or repair the data. The exact API is not accepted. |
| Rationale | Professionals need to correct inference. A configuration that the data cannot support is itself a finding. |
| Implications | `REQ-S-06`. API shape remains [OPEN-004](#open-questions) and [OPEN-009](#open-questions). |

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

## DEC-047

| | |
| --- | --- |
| Title | Boolean meaning is not binary cardinality |
| Status | Accepted |
| Decision | Boolean/Binary is a first-class analytical family. Binary cardinality does not automatically imply Boolean meaning. A physical pandas boolean is very strong Boolean/Binary evidence. `{0, 1}` may be a binary interpretation and is not automatically Boolean. Yes/no or true/false strings may be a binary interpretation under conservative token recognition. An arbitrary two-category variable stays categorical, including as a binary category, and is not described as Boolean. A column name may be weak supporting evidence and must never determine semantic type by itself. The exact subtype taxonomy is not accepted. |
| Rationale | Two distinct values are a cardinality fact. Boolean meaning needs stronger evidence. |
| Implications | `REQ-D-01`, `REQ-D-02`, `REQ-S-04`. Subtypes remain [OPEN-014](#open-questions). |

## DEC-048

| | |
| --- | --- |
| Title | Identifier evidence is a set of signals |
| Status | Accepted |
| Decision | Identifier is a first-class semantic type. Inference may use uniqueness ratio, duplicate count, missing count, UUID or GUID-like structure, hash-like structure, sequential integer patterns, fixed-width codes, alphanumeric code patterns, prefixes and suffixes, monotonic or sequential behavior, and column name as a weak supporting signal. That list is admissible evidence, not a closed detector. `unique_ratio == 1` alone is not sufficient. Identifiers are normally excluded from ordinary correlation, diagnostic target modeling, and ordinary multivariate anomaly modeling, unless explicitly configured otherwise. |
| Rationale | Uniqueness is common in small samples and in continuous measurements. Identifier treatment changes which analyses are meaningful. |
| Implications | `REQ-G-01` through `REQ-G-03`. Thresholds remain [OPEN-044](#open-questions). Exact eligibility rules remain [OPEN-043](#open-questions). |

## DEC-049

| | |
| --- | --- |
| Title | Numeric, categorical, and string semantics |
| Status | Accepted |
| Decision | A physically numeric column that is not better read as Empty, Constant, Boolean/Binary, or Identifier may be interpreted as Numeric. Numeric subtypes may include Continuous and Discrete. Integer dtype is not discrete, and float dtype is not continuous, without looking at the observed values. Subtype inference stays conservative. Categorical is a semantic interpretation, not a synonym for pandas `object`. A categorical variable may physically be a categorical dtype, a string, an object, or numeric codes. Low-cardinality numeric values are not assumed to be category codes without sufficient evidence or explicit configuration. Where evidence supports it, strings are distinguished as categorical-like, free text, identifier-like, URL-like, email-like, path-like, datetime-like, or generic string. Cardinality alone is insufficient. String evidence may include uniqueness, repetition, character-length distribution, word counts, token or pattern consistency, and structural patterns. |
| Rationale | Storage type and cardinality are evidence. They are not the semantic type. |
| Implications | `REQ-S-01`, `REQ-B-*`, `REQ-C-*`, `REQ-F-01`. The full subtype taxonomy remains [OPEN-014](#open-questions). Common-token diagnostics remain [OPEN-019](#open-questions). |

## DEC-050

| | |
| --- | --- |
| Title | Pattern detection does not convert the series |
| Status | Accepted |
| Decision | Pytics may detect strings that appear URL-like, email-like, UUID-like, path-like, datetime-like, or another well-defined structural form. Detection does not silently rewrite the source Series. For datetime-like strings, the physical source type remains string even when a semantic datetime interpretation is selected. Native pandas datetime and timezone-aware datetime dtypes are strong evidence of Datetime semantics. String-to-datetime inference is conservative and considers parse success, representation and format consistency, plausible ranges, ambiguity, and sampling or full-column verification. Arbitrary numeric-looking strings are not blindly read as dates. A datetime variable does not automatically imply a time series. |
| Rationale | A successful parse is an interpretation. The column the user holds is still strings until they change it. |
| Implications | `REQ-S-03`, `REQ-E-03`, `REQ-F-01`. Sampling thresholds remain [OPEN-010](#open-questions). |

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

## DEC-053

| | |
| --- | --- |
| Title | Semantic type guides eligibility |
| Status | Accepted as direction |
| Decision | Semantic interpretation guides which analyses are analytically meaningful. The examples below are direction, not a closed eligibility matrix. Identifier is typically eligible for a variable profile, missingness, and duplicate or identifier-quality analysis, and is normally excluded from ordinary correlation, target predictor modeling, and ordinary multivariate anomaly modeling. Numeric is normally eligible for distribution analysis, relationships, target relationships, and anomaly analysis. Text is eligible for text profiling and relevant quality or pattern analysis. Ordinary statistical relationships and target modeling for text are limited by default unless a meaningful method exists. Datetime is eligible for datetime profiling and for temporal analysis when genuine temporal structure exists. Timestamps are not converted to numbers and then treated as ordinary measurements. Exact eligibility rules belong to later method design. |
| Rationale | Running every method on every storage type produces results that are numerically defined and analytically meaningless. |
| Implications | `REQ-S-09`, `REQ-G-03`, `REQ-K-01`. Exact rules are [OPEN-043](#open-questions). |

## DEC-054

| | |
| --- | --- |
| Title | Semantic-inference sampling |
| Status | Accepted |
| Decision | Cheap evidence uses the full column where practical. Expensive evidence, particularly string and pattern analysis on very large data, may use controlled sampling. That sampling must be transparent, reproducible where possible, recorded, tied to the configured analysis mode, and considered when inference confidence is expressed. Exact thresholds and sample sizes are not accepted. |
| Rationale | Hidden sampling would make a semantic type look more certain than the evidence procedure was. |
| Implications | `REQ-P-12`, `REQ-IA-15`. Thresholds and sample sizes are [OPEN-010](#open-questions). |

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
| Implications | TSK-001 uses this representation for physical dtype facts and semantic interpretation values. TSK-002 uses it for basic column evidence. TSK-003 reuses those values for the physical Boolean reading and does not add a value type. TSK-004 reuses those values for the physical Datetime reading and does not add a value type or timezone metadata on `PhysicalDtype`. Public result names remain [OPEN-004](#open-questions). Module layout remains [OPEN-045](#open-questions). `REQ-T-04` is unchanged: do not add a dependency for this choice. |

## DEC-063

| | |
| --- | --- |
| Title | Build Pytics 2.0 in place inside `src/pytics` |
| Status | Accepted |
| Decision | Pytics 2.0 is built incrementally in place inside the existing `src/pytics` package. Existing Pytics 1.1.5 components remain temporarily intact until their Pytics 2.0 replacement has been specified, implemented, tested, and verified against the Pytics 2.0 specification. Temporary internal coexistence inside `src/pytics` is allowed. The final product must not contain a permanent second public package such as `pytics_v2`, `pytics2`, `legacy`, `old_pytics`, or `new_pytics`. Do not redirect the existing public `profile` / `compare` API except in a slice that explicitly requires that change. |
| Rationale | [DEC-039](#dec-039) already fixed the end state as one package. The missing piece was how 1.1.5 and 2.0 share that package during the work. A second public package would become the product. Deleting 1.1.5 before its replacement is verified would remove the baseline without a successor. |
| Implications | Resolves [OPEN-040](#open-040). TSK-001 adds internal modules under `src/pytics/semantics/` and does not delete or rewrite `profiler.py` or `visualizations.py`. TSK-002 adds basic column evidence and Empty/Constant inference in that same internal package, without changing `profile` or `compare`. TSK-003 adds physical Boolean inference there, still without changing `profile` or `compare`. TSK-004 adds physical Datetime inference in that same internal package, still without changing `profile` or `compare`. That directory is not a resolution of [OPEN-045](#open-questions). Unapproved slices still follow [DEVELOPMENT_PROTOCOL.md](DEVELOPMENT_PROTOCOL.md). |

## Open questions

These are not decisions. Do not implement an answer.

<a id="open-questions"></a>

### OPEN-001

Are the "such as" and "may include" concept lists a closed set of mandatory outputs, an open in-scope set, or illustrative examples? This memory treats the parent areas as accepted and preserves the qualifiers. It does not treat every named statistic as an always-on output.

### OPEN-002

Which decisions would count as "unnecessary" blockers to a future non-pandas engine, given that a Polars or Arrow abstraction is out of scope now? [DEC-040](#dec-040) and the "Polars is not core" direction in [DEC-060](#dec-060) do not answer this.

### OPEN-004

What are the public function signatures, result types, and attribute names? DataFrame-only `profile` and `compare` are accepted ([DEC-040](#dec-040)). The illustrative `ProfileReport` and `ComparisonReport` shapes are not frozen. The compare sketch also omits duplicate changes that compare navigation includes. The configuration object is [OPEN-009](#open-questions).

### OPEN-006

What is the exact method catalog, and which dependencies does it require? [DEC-055](#dec-055) accepts pair-type direction and does not close the catalog. Still unset: numeric-by-binary effect-size formula and fallback; ANOVA, Welch, or rank-based selection for numeric-by-categorical; default binary-by-binary measures; exact or resampling rules for sparse categorical tables; datetime relationship methods; ordinal relationship methods where [DEC-052](#dec-052) applies; pair types with no direction yet, including text and timedelta; which deep-mode robust methods are included; and the dependency that implements each method. `REQ-K-03` remains in force.

### OPEN-007

What is a statistical test family inside Pytics, and therefore when multiple-testing correction applies? [DEC-056](#dec-056) prefers false-discovery-rate control for broad relationship screening, with Benjamini-Hochberg as the leading candidate, and requires raw and adjusted p-values to stay distinct. Benjamini-Hochberg is not an unconditional rule. Correction behavior is not final until the family is defined.

### OPEN-008

Which analyses receive a Bayesian treatment, and what is the exact method catalog? [DEC-057](#dec-057) keeps Bayesian analysis selective and lightweight. NumPy and SciPy are the current calculation direction. PyMC is not intended as a core dependency at present. Binary-by-binary association is a strong candidate. No domain threshold has been selected. A threshold, if used, must come from an established convention or explicit user configuration. Final library choice beyond that direction is [OPEN-042](#open-questions).

### OPEN-009

What is the configuration-object shape, and where do random seed and other reproducibility controls live?

### OPEN-010

What are the exact contents, cost thresholds, and sample sizes of `quick`, `standard`, and `deep`? The three names, and standard as the intended default, are accepted ([DEC-058](#dec-058)). The lists in that decision are not a closed catalog. Controlled sampling for expensive semantic evidence is accepted ([DEC-054](#dec-054)). Its thresholds and sample sizes, and sampling rules for other analyses, are part of this question. The mode-selection signature is not accepted.

### OPEN-013

Which estimator family is used for the diagnostic classification model, and which for regression? Holdout or cross-validation, and held-out permutation importance, are accepted direction ([DEC-059](#dec-059)). Do not select Random Forest, Extra Trees, gradient boosting, or another estimator as the answer to this question until a decision does so.

### OPEN-014

Which subtypes exist under the minimum semantic types? Continuous and Discrete are permitted numeric concepts, and that inference stays conservative ([DEC-049](#dec-049)). Boolean/Binary subtypes are not set ([DEC-047](#dec-047)). Integer dtype is not a discrete subtype, and float dtype is not a continuous subtype, without the observed values.

### OPEN-016

When ordinal semantics are accepted under [DEC-052](#dec-052), is that interpretation its own semantic type, a categorical subtype, or only a relationship case? The rule against inventing order is decided. This storage question is not.

### OPEN-018

Operational definitions are unset for: dataset dimensions, computational-analysis metadata, near-constant, high cardinality, rare category, cardinality band thresholds, the missing-like literal list, and "controlled" partial duplicates.

### OPEN-019

Are trimmed mean and common-token text diagnostics in scope? Both were worded as potential.

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

In what order are accepted requirements turned into approved slices?

### OPEN-038

What is the exact internal API of the shared statistical layer, and where is reuse analytically appropriate rather than target-specific? [DEC-037](#dec-037) accepts the layer and leaves this boundary open.

### OPEN-039

What are the method registry's schema and API? [DEC-038](#dec-038) accepts the concept. The metadata list there is illustrative, not a schema. Do not implement the registry.

### OPEN-041

How should interactive Plotly visualizations become reliable static graphics for PDF without imposing fragile system dependencies? [DEC-061](#dec-061) leaves this unresolved on purpose. Kaleido is neither selected nor rejected.

### OPEN-042

What are the final 2.0 dependency versions, and which candidate directions become a lock? [DEC-060](#dec-060) is not that lock. IPython remains unresolved until a packaging review. Do not pin versions and do not install the candidate stack from the planning documents.

### OPEN-043

What are the exact analysis-eligibility rules for each semantic type? [DEC-053](#dec-053) gives direction only.

### OPEN-044

What are the exact semantic-inference thresholds? [DEC-048](#dec-048) rejects uniqueness alone as an identifier rule and does not set numeric cutoffs. Sampling sizes are [OPEN-010](#open-questions).

### OPEN-045

What is the module and file layout? [DEC-036](#dec-036) accepts the engine diagram as direction only.

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

