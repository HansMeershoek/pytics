"""Internal column and dataset analysis for Pytics 2.0.

Not part of the public ``pytics.profile`` / ``pytics.compare`` API.
Import paths and type names here are not a frozen public schema.
Semantic inference stays in ``pytics.semantics``. This package owns the
broader column and dataset records, the DataFrame traversal, the dataset
overview, and the variables summary aggregated from an existing dataset
analysis. Numeric descriptive statistics for a selected Numeric column,
and Boolean true/false counts for a selected Boolean column, are
collected in this package after semantic resolution.
"""
