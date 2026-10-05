"""Notebook HTML for public profile and comparison results.

Internal. Callers display a result object. They do not import this
package to obtain a profile or a comparison.
"""

from pytics.presentation.notebook.comparison import render_comparison
from pytics.presentation.notebook.profile import render_profile

__all__ = ["render_comparison", "render_profile"]
