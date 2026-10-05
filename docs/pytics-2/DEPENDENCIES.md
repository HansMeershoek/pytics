# Dependencies

Status: the ecosystem review has an outcome. That outcome is a **candidate stack**, not a dependency lock ([DEC-060](DECISIONS.md#dec-060)).

Do not install these candidates from this file. Do not pin versions. Do not edit `pyproject.toml` from this file. Do not treat a 1.1.5 dependency as automatically retained ([DEC-027](DECISIONS.md#dec-027)).

`REQ-T-04` holds installation and version pins. Final versions are [OPEN-042](DECISIONS.md#open-questions). Python support is [OPEN-036](DECISIONS.md#open-questions).

## How to read the directions

| Kind | Meaning |
| --- | --- |
| Accepted constraint | Follows from an accepted product or architecture decision. Still not a version pin. |
| Current direction | What the review currently points to. Not a lock. A later decision can change it. |
| Unresolved | No selection. |

## Current directions

| Capability | Direction | Kind |
| --- | --- | --- |
| DataFrame foundation | pandas | Accepted constraint for the API ([DEC-006](DECISIONS.md#dec-006), [DEC-040](DECISIONS.md#dec-040)). Version not pinned. |
| Numeric foundation | NumPy | Current direction |
| Statistical primitives | SciPy | Current direction |
| Advanced inference and diagnostics | statsmodels | Current direction |
| Lightweight Bayesian calculations | NumPy and SciPy | Current direction ([DEC-057](DECISIONS.md#dec-057)) |
| General probabilistic programming | PyMC is not intended as a core dependency at present | Current direction |
| Diagnostic model | scikit-learn | Declared runtime dependency, `scikit-learn>=1.3`, by TSK-034 ([DEC-105](DECISIONS.md#dec-105)). Not a lock. The estimators are logistic and ridge regression, resolving [OPEN-013](DECISIONS.md#open-013). |
| Multivariate anomaly methods | scikit-learn candidate methods | Current direction. The univariate method is Tukey fences and does not use scikit-learn ([DEC-107](DECISIONS.md#dec-107)). The multivariate estimator remains [OPEN-022](DECISIONS.md#open-questions). |
| LightGBM | Not currently intended as a core dependency | Current direction |
| Interactive visualization | Plotly | Current direction. Plotly is a rendering engine, not the visual design system ([DEC-061](DECISIONS.md#dec-061)). |
| HTML templating | Jinja2 | Current direction |
| HTML interactivity | Restrained custom JavaScript | Current direction |
| PDF layout | WeasyPrint is the leading candidate | Current direction, not a final choice ([OPEN-035](DECISIONS.md#open-questions)) |
| xhtml2pdf | Not the 2.0 architecture | Accepted direction ([DEC-061](DECISIONS.md#dec-061)) |
| Plotly static image or PDF bridge | Unresolved | [OPEN-041](DECISIONS.md#open-questions). Kaleido is neither selected nor rejected. |
| IPython | Likely not core | Unresolved until a packaging review |
| Polars | Not core | Current direction. A Polars or Arrow dataframe abstraction remains out of scope (`REQ-P-06`). Polars is not rejected forever ([DEC-006](DECISIONS.md#dec-006)). |
| PyArrow | Not required merely for the core DataFrame API | Current direction. Not a ban on every future use. |

Ordinary HTML reports are not to depend on Dash, a web server, React, Vue, or a JavaScript build chain unless later evidence creates a compelling reason ([DEC-061](DECISIONS.md#dec-061)).

Matplotlib appears in the 1.1.5 inventory below. It is not part of the candidate directions. That absence is not a rejection.

## What is still open

- final versions and which directions become a lock ([OPEN-042](DECISIONS.md#open-questions));
- which statistical methods justify which libraries, inside the unfinished catalog ([OPEN-006](DECISIONS.md#open-questions));
- the Bayesian catalog ([OPEN-008](DECISIONS.md#open-questions));
- the final HTML and PDF libraries ([OPEN-035](DECISIONS.md#open-questions));
- the Plotly-to-static-PDF mechanism ([OPEN-041](DECISIONS.md#open-questions));
- the multivariate anomaly estimator ([OPEN-022](DECISIONS.md#open-questions)). The univariate method is Tukey fences and does not add a dependency ([DEC-107](DECISIONS.md#dec-107));
- Python versions ([OPEN-036](DECISIONS.md#open-questions)). Choose the range only after checking the dependency stack that is actually accepted. Python 3.14 compatibility matters because it is the known local baseline. Do not require 3.14 if a broader modern range is supportable.

## Historical 1.1.5 inventory

This is what release 1.1.5 declared before TSK-046. It is not a shortlist and not the candidate stack. TSK-046 changed the working-tree declarations ([DEC-117](DECISIONS.md#dec-117)). The table below stays the pre-cleanup inventory.

From `pyproject.toml`:

| Package | Declared floor |
| --- | --- |
| pandas | >= 1.3.0 |
| numpy | >= 1.20.0 |
| plotly | >= 5.0.0 |
| jinja2 | >= 3.0.0 |
| xhtml2pdf | >= 0.2.8 |
| scipy | >= 1.7.0 |
| IPython | >= 7.0.0 |
| matplotlib | >= 3.3.0 |
| kaleido | >= 0.2.1 |

Development extras: pytest, black, mypy, pytest-cov.

`requirements-pinned.txt` additionally pins `scikit-learn==1.3.0`, which is not a `pyproject.toml` dependency. SciPy is declared and is not used by the profile or compare implementation inspected for [BASELINE_1_1_5.md](BASELINE_1_1_5.md). Matplotlib is used indirectly by `Series.plot.kde` inside `compare()`. TSK-024 calls `scipy.stats.spearmanr`, `scipy.stats.pearsonr`, and `scipy.stats.norm.ppf` ([DEC-095](DECISIONS.md#dec-095)). Those calls use the declared `scipy>=1.7.0` floor. The Pearson interval is implemented in Pytics rather than through a newer SciPy confidence-interval API. The floor was not raised. TSK-025 does not add a dependency and does not raise that floor ([DEC-096](DECISIONS.md#dec-096)). TSK-026 calls `scipy.stats.f_oneway` with no keyword arguments ([DEC-097](DECISIONS.md#dec-097)). Welch's `equal_var=False` argument is not used, because it requires SciPy 1.16. The floor was not raised. TSK-027 does not add a dependency and does not raise that floor ([DEC-098](DECISIONS.md#dec-098)). TSK-028 calls `scipy.stats.fisher_exact(table, alternative="two-sided")` and does not pass `method`, which was added in SciPy 1.15 ([DEC-099](DECISIONS.md#dec-099)). The floor was not raised. Barnard's test and Boschloo's test were not selected. No statsmodels dependency was added. TSK-029 calls `scipy.stats.t.sf` and `scipy.stats.t.ppf` for the Welch p-value and interval, which exist on the declared floor ([DEC-100](DECISIONS.md#dec-100)). `scipy.stats.ttest_ind` is not called: its degrees-of-freedom attribute and interval method came after `scipy>=1.7.0`, and it would cast large integers to float64. The Hedges correction uses `math.gamma`, not `scipy.special`. The floor was not raised and no dependency was added. TSK-030 calls `scipy.stats.chi2.sf` for the Pearson chi-square tail ([DEC-101](DECISIONS.md#dec-101)). That survival function exists on the declared floor. `scipy.stats.chi2_contingency` is not called: its default applies Yates's correction to a 2×2 table, and its `method` argument is newer than `scipy>=1.7.0`. The floor was not raised and no dependency was added. TSK-031 implements Benjamini–Hochberg in Pytics ([DEC-102](DECISIONS.md#dec-102)). It does not call SciPy or statsmodels for that adjustment, and it does not add a dependency or raise the SciPy floor. Statsmodels remains a candidate direction, not a requirement of this correction. TSK-034 adds `scikit-learn>=1.3` to `pyproject.toml` as a runtime dependency ([DEC-105](DECISIONS.md#dec-105)). It calls `Pipeline`, `ColumnTransformer`, `SimpleImputer`, `StandardScaler`, `OneHotEncoder`, `LogisticRegression`, `Ridge`, `DummyClassifier`, `DummyRegressor`, and `ConvergenceWarning`, all present in 1.3, the version `requirements-pinned.txt` already pins. After the TSK-034b hardening it no longer calls `permutation_importance`. It reads `ColumnTransformer.output_indices_` (1.0), `named_transformers_`, `SimpleImputer.indicator_.features_`, and `OneHotEncoder.categories_`, all present in 1.3, and uses `scipy.sparse.diags`, sparse row indexing, and `numpy.random.RandomState`, all present on the declared SciPy and NumPy floors. It does not pass `penalty` or `multi_class`, and it computes its metrics in Pytics, so it does not depend on scikit-learn metric defaults that changed between releases. It also calls `scipy.stats.rankdata`, present on the declared SciPy floor. Only scikit-learn 1.9.1 was tested. Its install in `.venv` also brought joblib 1.6.0, threadpoolctl 3.7.0, and cloudpickle 3.1.2 as transitive packages. They are not declared by Pytics. No other machine-learning dependency was added. The SciPy floor was not raised.

Those usage notes describe 1.1.5 only. `requires-python` is `>=3.8`. CI tests 3.9–3.11. The local baseline named in the briefing is Python 3.14.8. None of that is a 2.0 support decision.

## Working tree after TSK-046

[DEC-117](DECISIONS.md#dec-117) removed dependencies that only the retired renderer imported. This is the working-tree declaration. It is not a version lock ([OPEN-042](DECISIONS.md#open-questions)).

| Package | Declared floor | Role |
| --- | --- | --- |
| pandas | >= 1.3.0 | DataFrame API |
| numpy | >= 1.20.0 | Numeric foundation |
| scipy | >= 1.7.0 | Statistical primitives used by the analytical engine |
| scikit-learn | >= 1.3 | Target diagnostic fit |

Removed from runtime dependencies: Plotly, Jinja2, xhtml2pdf, Matplotlib, and Kaleido. IPython is no longer a runtime dependency. It is a development extra because `tests/test_notebook_presentation.py` asks IPython's `HTMLFormatter` whether a result's `_repr_html_` is used. The notebook renderer itself does not import IPython.

Plotly and Jinja2 remain candidate directions for a future interactive HTML report. They are not installed by the package. WeasyPrint is still not selected. Kaleido is still neither selected nor rejected for a future static-PDF bridge.
