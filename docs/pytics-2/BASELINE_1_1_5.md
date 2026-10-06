# Pytics 1.1.5 baseline

Status of this document: historical record.

Pytics 1.1.5 is the released codebase this record describes. Nothing in this file is a 2.0 requirement. Nothing here is rewritten to look like the 2.0 contract. TSK-046 later removed the HTML and PDF renderer described below. This file stays the record of that 1.1.5 behavior.

This record was made by inspecting the repository on 2026-10-03. The test-run figures below come from the bootstrap briefing. They were **not** re-executed while this memory was written.

## Briefing baseline

Recorded as given. Not re-measured here.

| Item | Recorded baseline |
| --- | --- |
| Released version | 1.1.5 |
| Local development environment named in the briefing | Python 3.14.8 |
| Tests | 20 |
| Passing | 19 |
| Failing | 1 |
| Coverage | 92% |
| HTML profiling | Works |
| PDF export | Fails under the tested Python 3.14.8 environment |
| Shape of the implementation | Relatively monolithic |
| Public API | `profile` and `compare` |
| Docs versus code | Several mismatches |
| Role for 2.0 | Functional and historical reference |

The pytest suite that matches the count of 20 is `tests/test_profiler.py` (`testpaths = ["tests"]` in `pyproject.toml`). The briefing attributes the failure to PDF export. The test that generates a PDF file is `test_pdf_export`. This document does not claim that failure was reproduced during the inspection.

## What the repository actually contains

Package version `1.1.5` is set in both `pyproject.toml` and `src/pytics/__init__.py`.

Public exports are `profile` and `compare` only.

Production code:

| Path | Role observed |
| --- | --- |
| `src/pytics/profiler.py` | `profile`, `compare`, overview stats, per-column analysis, duplicate summary, and Jinja rendering in one module. |
| `src/pytics/visualizations.py` | Plotly figure conversion and comparison distribution plots. |
| `src/pytics/templates/base_template.html.j2` | Shared HTML shell, including a fixed left sidebar. |
| `src/pytics/templates/report_template.html.j2` | Profile report. |
| `src/pytics/templates/compare_report_template.html.j2` | Comparison report. |
| `tests/test_profiler.py` | 20 test functions. |

`profile()` analyzes a `pandas.DataFrame` and renders immediately. It can return an HTML string, return a template context when `return_context=True`, or write HTML or PDF. Numeric and categorical results are stored largely as preformatted strings, and plots are stored as HTML fragments or static-image placeholders. That couples analysis to presentation.

`compare()` builds a result dictionary and, when `output_file` is set, renders HTML inside the same function. The returned dictionary includes the original DataFrames.

Other tracked items that are not the library:

| Path | Observed fact |
| --- | --- |
| `Prompt` | Earlier notebook-profiler brief. It was present in the baseline repository. It is not the 2.0 contract, and it is not tracked on current `main`. |
| `README.md` | User documentation for the released package. |
| `RELEASE_NOTES.md` | Title still says v1.0.0. The sample API is `Profile(...).generate_report()` / `to_pdf()`. |
| `CONTRIBUTING.md` | The baseline text told contributors to run `pre-commit install`. No pre-commit config was tracked. That instruction is no longer in the current file. |
| `examples/generate_screenshots.py` | Imports `pandas_profiler`, and calls `include_sections`. |
| `test_install.py` | Imports `pandas_profiler`. |
| `test_import.py`, `test_kaleido.py`, `test_pdf_gen.py` | Standalone scripts. They are outside `tests/` and are not part of the pytest path. `test_pdf_gen.py` comments that it expects v1.1.4. |
| `test_report.html`, `test_report.pdf` | Generated report artifacts. They were tracked in the baseline repository. They are not tracked on current `main`. |
| `pyproject.toml.bak` | Backup of the packaging file. It was tracked in the baseline repository. It is not tracked on current `main`. |
| `.venv-py311/` | A Python 3.11.6 virtual environment. It was tracked in the baseline repository. Its `pyvenv.cfg` pointed at a machine path under `C:\Users\hnsmr\...`. The baseline `.gitignore` ignored `venv/`, `env/`, and `ENV/`, not `.venv-py311/`. It is not tracked on current `main`. |

CI (`.github/workflows/python-test.yml`) tests Python 3.9, 3.10, and 3.11. `requires-python` is `>=3.8`. Classifiers stop at 3.11. The briefing's local environment is Python 3.14.8. Those facts are recorded together and are not reconciled here.

## Behavior that is actually implemented

Overview stats include rows, columns, memory, duplicate rows, missing cells, and average record size.

Per-column analysis branches on physical dtype. The numeric branch treats `int64` and `float64` only. It records count-style fields plus mean, standard deviation, min, quartiles, median, and max, and it builds a histogram/box figure. Other dtypes are treated as categorical: mode, and a bar chart of the top 20 values.

Date, boolean, text, identifier, constant, and empty are not semantic types. Datetime columns are counted in the template context with `select_dtypes`, but they do not have a separate time analysis.

Duplicates are exact row duplicates, summarized as up to 10 groups.

Correlations are a numeric correlation heatmap inside summary plots. There is no effect-size layer, interval, hypothesis-test record, or multiple-testing correction.

If `target` is passed and the column exists, the target column is run through the same variable analysis and excluded from the variable list. There is no diagnostic model, no feature-importance calculation, and no leakage analysis in `profiler.py`.

Missingness is counted and plotted with dtype composition. Missing-like literals are not a separate reported concept.

Hard limits: more than 1,000,000 rows or more than 1,000 columns raises `DataSizeError`.

Comparison covers column set differences, physical dtype differences, side-by-side descriptive stats, and distribution data. Numeric comparison is again limited to `int64` and `float64` on both sides. Kernel density in `compare()` uses pandas' matplotlib-backed `Series.plot.kde`. There is no semantic-type comparison, relationship comparison, target comparison, or drift section.

Profile navigation in the template is: Overview, DataFrame Summary, Variables, Correlations, Missing Values, Duplicates, About. Compare navigation in the template is: Overview & Schema, Variable Comparison, Unique Columns. The compare template also has correlations and missing sections that are not in that navigation list.

The About block in `report_template.html.j2` is a short product blurb, a feature list, the GitHub URL, and a developer credit. That text is 1.1.5 template copy. It is not the approved Pytics 2.0 About narrative. Do not carry it forward as author story or contact details.

## PDF, as the code and docs describe it

`visualizations.py` documents a known Kaleido `>=0.2.1` hang. For `format='pdf'`, `_convert_to_static_image` returns the placeholder `PLOT_OMITTED_FOR_PDF` instead of rendering the figure. `README.md` says PDF plots are omitted for that reason and that the rest of the PDF still works, and it points readers who need PDF plots to version 1.1.3.

`profile()` still sends the HTML through `xhtml2pdf` (`pisa.CreatePDF`) when the output format or filename is PDF. `test_pdf_export` expects both the placeholder and a file whose header is `%PDF-`.

The bootstrap briefing separately says PDF export fails on Python 3.14.8. This file does not decide whether that failure is the Kaleido issue, an `xhtml2pdf` failure, or something else.

## Declared dependencies versus a pinned file

`pyproject.toml` runtime dependencies:

- pandas >= 1.3.0
- numpy >= 1.20.0
- plotly >= 5.0.0
- jinja2 >= 3.0.0
- xhtml2pdf >= 0.2.8
- scipy >= 1.7.0
- IPython >= 7.0.0
- matplotlib >= 3.3.0
- kaleido >= 0.2.1

`requirements-pinned.txt` also pins `scikit-learn==1.3.0`. scikit-learn is not a `pyproject.toml` dependency, and `profiler.py` does not import it.

SciPy is declared. It is not used by the profile or compare functions inspected above.

These are 1.1.5 facts. They are not a decision to keep any of these libraries in 2.0. See [DEPENDENCIES.md](DEPENDENCIES.md).

## Documentation and API mismatches

Observed by comparing docs and scripts with `profile()` / `compare()` signatures. Not fixed.

| Claim | Where | Code |
| --- | --- | --- |
| `profile` accepts a CSV or Parquet path | `README.md`, and the older `Prompt` file | `profile` types `df` as a DataFrame. No path loading. |
| `include_sections` / `exclude_sections` | `README.md`, `examples/generate_screenshots.py`, `Prompt` | Not parameters of `profile`. |
| Target analysis includes feature importance and statistical tests | `README.md` | Target path reuses `_analyze_variable`. |
| Section `interactions` | `README.md` | No such analysis or navigation item. |
| `from pytics import Profile` and `generate_report()` / `to_pdf()` | `RELEASE_NOTES.md` | Not exported. Version heading is v1.0.0. |
| Import `pandas_profiler` | `examples/generate_screenshots.py`, `test_install.py` | Installed package name is `pytics`. |
| Interactive yes/no configuration mode | `Prompt` | Not implemented. |
| Outlier section in the report | `Prompt` | No outlier analysis in `profiler.py`. |
| `pre-commit install` | `CONTRIBUTING.md` | No pre-commit configuration file is tracked. |

`README.md` also describes a responsive report, configurable sections, and performance optimizations. The implementation is the module described above, with a hard row/column cap and no section-selection arguments.

## Relationship to the 2.0 contract

1.1.5 already has a profile function, a compare function, an HTML report, a PDF path, a sidebar, light/dark theme arguments, and some of the same topic names (overview, variables, missing, duplicates, target). That overlap is historical. It does not mean those implementations satisfy the 2.0 specification.

Concrete gaps relative to the 2.0 contract, stated so they are not mistaken for finished work:

- No semantic types, confidence, or evidence.
- No separation between analyzers and HTML.
- No structured finding objects.
- No effect-size-first inference, Bayesian analysis, or methods appendix.
- No identifier, text-role, missing-like-literal, anomaly, or time-structure analysis of the kind specified for 2.0.
- Comparison does not explain change across the accepted compare coverage list.
- The report information architecture is a different, smaller navigation.
- Notebook use returns or writes a full HTML report rather than a compact result object.

Reuse of a 1.1.5 algorithm, test, or idea requires a later explicit decision. It is not the default.

The 2.0 end state is replacement of the implementation inside `src/pytics` ([DEC-039](DECISIONS.md#dec-039)). This file remains the historical record of 1.1.5. It is not an instruction to delete or move that code. In-place coexistence until a replacement is verified is [DEC-063](DECISIONS.md#dec-063). Git history is the long-term archive.
