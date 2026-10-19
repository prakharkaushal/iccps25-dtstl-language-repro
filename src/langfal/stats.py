"""Summary statistics.

``mean_ci`` and ``geometric_mean`` follow the reference project's evaluation code
(reference_project/CS637_SPGA/spga/generate_table_2.py:20-37, generate_table_3.py:13-26),
re-implemented here because the reference repository declares no license. Unlike the reference,
ratios are NOT rounded before the geometric mean (see docs/REFERENCE_ANALYSIS.md, Sec. 6/7).
"""
from __future__ import annotations

import math

import numpy as np
import scipy.stats


def mean_ci(data, confidence: float = 0.95):
    """Mean and half-width of the t-based confidence interval (nan half-width if n < 2)."""
    a = np.asarray([v for v in data if v is not None and not (isinstance(v, float) and math.isnan(v))], dtype=float)
    n = len(a)
    if n == 0:
        return float("nan"), float("nan")
    m = float(a.mean())
    if n < 2:
        return m, float("nan")
    h = float(scipy.stats.sem(a) * scipy.stats.t.ppf((1 + confidence) / 2.0, n - 1))
    return m, h


def geometric_mean(values) -> float:
    a = np.asarray(values, dtype=float)
    if a.size == 0 or np.any(a <= 0):
        return float("nan")
    return float(np.exp(np.log(a).mean()))


def paired_wilcoxon(a, b):
    """Two-sided Wilcoxon signed-rank test on paired samples (p-value; nan if not computable)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.size < 2 or np.allclose(a, b):
        return float("nan")
    try:
        return float(scipy.stats.wilcoxon(a, b).pvalue)
    except ValueError:
        return float("nan")
