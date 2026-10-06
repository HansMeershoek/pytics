"""Internal column and dataset analysis for Pytics 2.0.

Not part of the public ``pytics.profile`` / ``pytics.compare`` API.
Import paths and type names here are not a frozen public schema.
Semantic inference stays in ``pytics.semantics``. This package owns the
broader column and dataset records, the DataFrame traversal, and the
dataset overview. Those records are the analytical truth. Profile and
compare read them. They are not copied into a second summary. Numeric
descriptive statistics for a selected Numeric column, Boolean
true/false counts for a selected Boolean column, and the observed
level distribution for a selected Categorical column, are collected
in this package after semantic resolution. Dataset
missingness patterns, exact duplicate-row groups, and Numeric × Numeric
and Numeric × Categorical relationships are collected in this package
from the DataFrame. Univariate numeric anomalies reuse the retained
numeric quartiles and do not treat an unusual value as an error. They
are not semantic evidence. The relationship implementation lives in
``relationships``. ``relationship`` re-exports it. For an explicit
target, ``target_leakage`` records exact-duplicate and deterministic
mapping evidence and does not score leakage. ``target_diagnostic_fit``
then fits one untuned diagnostic model and is the only scikit-learn
user. ``target_diagnostic`` holds its frozen result. An exact duplicate
recorded by leakage evidence is excluded from that model.
``compare`` reads two finished dataset analyses and describes column
alignment, schema transitions, descriptive change, and, when both source
frames are supplied, univariate distribution drift. It does not profile
either dataset again, and it is not ``pytics.compare``.
``findings`` selects retained facts from a finished analysis or
comparison for attention. It does not read a DataFrame or compute a
statistic. ``pytics.results`` is the public result boundary over those
finished records. This package remains internal.
"""
