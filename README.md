# pytics

[![PyPI version](https://img.shields.io/pypi/v/pytics)](https://pypi.org/project/pytics/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytics)](https://pypi.org/project/pytics/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/HansMeershoek/pytics/actions/workflows/python-test.yml/badge.svg?branch=main)](https://github.com/HansMeershoek/pytics/actions/workflows/python-test.yml)

Data profiling for pandas DataFrames.

The released version number is still 1.1.5. The working tree is the Pytics 2.0 analytical system: semantic inference, dataset analysis, and a structured result. A notebook display of that result is a compact HTML view. Interactive HTML and PDF are not current export features.

## Installation

```bash
pip install pytics
```

Runtime dependencies are pandas, NumPy, SciPy, and scikit-learn. Plotly, Jinja2, xhtml2pdf, ReportLab, Kaleido, and Matplotlib are not installed with Pytics.

## Current use

Load a DataFrame yourself, then profile it:

```python
import pandas as pd
import pytics

df = pd.read_csv("your_data.csv")
report = pytics.profile(df)
report
comparison = pytics.compare(df, df)
```

`report` is a `ProfileResult`. `comparison` is a `ComparisonResult`. In Jupyter or Colab, displaying either object uses `_repr_html_()`. That view reads the result. It does not recompute the analysis, and it does not write a file.

`profile_result` and `comparison_result` remain in `pytics.results`. The top-level functions call them. A keyword-only `target` is passed through when one is supplied. File export arguments from the 1.1.5 renderer are not accepted.

The configuration object and semantic overrides are still open, recorded as OPEN-004 in `docs/pytics-2/DECISIONS.md`.

## What changed from the 1.1.5 report

Pytics 1.1.5 generated an HTML report, and it attempted a PDF report, from `profile()` and `compare()`. That renderer analyzed the DataFrame on its own, with Plotly charts, Jinja templates, and xhtml2pdf. It is not the 2.0 analysis. It has been removed, including its templates and its PDF test. There is no Markdown report exporter.

The durable 2.0 design notes are in `docs/pytics-2/`. They are documentation, not a report format.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the LICENSE file for details.
