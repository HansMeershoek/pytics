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
| Diagnostic model | scikit-learn | Current direction. Estimator family is [OPEN-013](DECISIONS.md#open-questions). |
| Multivariate anomaly methods | scikit-learn candidate methods | Current direction. Estimator is [OPEN-022](DECISIONS.md#open-questions). |
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
- the diagnostic estimator ([OPEN-013](DECISIONS.md#open-questions));
- the anomaly estimator ([OPEN-022](DECISIONS.md#open-questions));
- Python versions ([OPEN-036](DECISIONS.md#open-questions)). Choose the range only after checking the dependency stack that is actually accepted. Python 3.14 compatibility matters because it is the known local baseline. Do not require 3.14 if a broader modern range is supportable.

## Historical 1.1.5 inventory

This is what the released project declares today. It is not a shortlist and not the candidate stack.

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

`requirements-pinned.txt` additionally pins `scikit-learn==1.3.0`, which is not a `pyproject.toml` dependency. SciPy is declared and is not used by the profile or compare implementation inspected for [BASELINE_1_1_5.md](BASELINE_1_1_5.md). Matplotlib is used indirectly by `Series.plot.kde` inside `compare()`.

Those usage notes describe 1.1.5 only. `requires-python` is `>=3.8`. CI tests 3.9–3.11. The local baseline named in the briefing is Python 3.14.8. None of that is a 2.0 support decision.
