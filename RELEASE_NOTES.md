# Development note

The HTML reports and PDF export described in the 1.0.0 notes below were removed from the working tree during Pytics 2.0 development (TSK-046). The package version is still 1.1.5. Those notes are the historical release record. They are not the current feature list. The current result API is `pytics.results.profile_result` and `pytics.results.comparison_result`.

# pytics v1.0.0 Release Notes 🎉

We're excited to announce the first stable release of pytics, an interactive data profiling library designed for Python notebooks with rich reporting capabilities.

## Key Features

### 📊 Interactive HTML Reports
- Dynamic profiling reports with interactive visualizations
- Responsive layout for better readability and navigation
- Collapsible sections for detailed analysis
- Cross-browser compatibility

### 📑 PDF Export Support
- High-quality PDF report generation
- Consistent formatting and styling
- Suitable for sharing and documentation
- Professional-grade output for stakeholders

### 📈 Comprehensive Data Analysis
- Detailed statistical summaries for numeric columns
- Distribution analysis and outlier detection
- Missing value analysis and patterns
- Correlation matrices and relationship insights

### 🎯 Target Variable Analysis
- In-depth analysis of target variables
- Relationship exploration between features and target
- Feature importance indicators
- Distribution comparisons across target categories

### 📉 Rich Visualizations
- Distribution plots (histograms, box plots)
- Correlation heatmaps
- Missing value patterns
- Interactive Plotly-based charts

### ⚡ Performance Features
- Efficient handling of large datasets
- Configurable analysis thresholds
- Memory-optimized processing
- Progress tracking for long operations

### 🛠️ Technical Details
- Python 3.8+ compatibility
- Built on robust data science stack (pandas, numpy, plotly)
- Jupyter notebook integration
- Customizable theming options

## Dependencies
- pandas >= 1.3.0
- numpy >= 1.20.0
- plotly >= 5.0.0
- jinja2 >= 3.0.0
- xhtml2pdf >= 0.2.8
- scipy >= 1.7.0
- IPython >= 7.0.0

## Installation
```bash
pip install pytics
```

## Quick Start
```python
import pandas as pd
from pytics import Profile

# Create and generate a profile
df = pd.read_csv('your_data.csv')
profile = Profile(df)
profile.generate_report()

# Export to PDF
profile.to_pdf('report.pdf')
```

## Breaking Changes
- Initial stable release, no breaking changes to note

## Future Plans
- Enhanced visualization options
- Additional export formats
- Custom analysis plugins
- Performance optimizations

## Feedback and Contributions
We welcome feedback, bug reports, and contributions! Please visit our [GitHub repository](https://github.com/HansMeershoek/pytics) to:
- Report issues
- Submit feature requests
- Contribute to the codebase

---
Thank you to all contributors and early adopters who helped make this release possible! 🙏 