"""Internal column and dataset analysis for Pytics 2.0.

Not part of the public ``pytics.profile`` / ``pytics.compare`` API.
Import paths and type names here are not a frozen public schema.
Semantic inference stays in ``pytics.semantics``. This package owns the
broader column and dataset records, the DataFrame traversal, the dataset
overview, the variables summary, the missingness summary, the
duplicate-row summary, the relationships summary, and the target
summary aggregated from an existing dataset analysis. Numeric
descriptive statistics for a selected Numeric column, Boolean
true/false counts for a selected Boolean column, and the observed
level distribution for a selected Categorical column, are collected
in this package after semantic resolution. Dataset
missingness patterns, exact duplicate-row groups, and Numeric × Numeric
and Numeric × Categorical relationships are collected in this package
from the DataFrame. They are
not semantic evidence. The relationship implementation lives in
``relationships``. ``relationship`` re-exports it. For an explicit
target, ``target_leakage`` records exact-duplicate and deterministic
mapping evidence and does not score leakage. ``target_diagnostic_fit``
then fits one untuned diagnostic model and is the only scikit-learn
user. ``target_diagnostic`` holds its frozen result. An exact duplicate
recorded by leakage evidence is excluded from that model.
"""
