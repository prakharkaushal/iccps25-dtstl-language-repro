"""Robustness monitors: RTAMT (the paper's baseline monitor, ref. [37]) and the language monitor.

Compatibility: RTAMT 0.3.5 pins antlr4-python3-runtime 4.7, whose Lexer.py/Parser.py do
``from typing.io import TextIO``; ``typing.io`` was removed in Python 3.13. ``ensure_typing_io``
registers a tiny alias module before RTAMT is imported (no third-party file is modified).
"""
from __future__ import annotations

import sys
import time
import types
import typing

import numpy as np

from . import stl
from .language import BoxUnion


def ensure_typing_io() -> None:
    if "typing.io" not in sys.modules:
        shim = types.ModuleType("typing.io")
        shim.IO, shim.TextIO, shim.BinaryIO = typing.IO, typing.TextIO, typing.BinaryIO
        sys.modules["typing.io"] = shim


def import_rtamt():
    ensure_typing_io()
    import rtamt  # noqa: E402
    return rtamt


class RtamtMonitor:
    """Offline RTAMT monitor for a scalar signal sampled at integer steps 0..n-1.

    ``mode='discrete'`` uses StlDiscreteTimeOfflineSpecification (DT-STL semantics, our ground
    truth). ``mode='dense'`` uses StlDenseTimeOfflineSpecification on the same samples (piecewise
    linear interpolation); it is only used as a timing sensitivity check because the paper does
    not say which RTAMT interpreter it timed.
    """

    def __init__(self, formula: stl.Formula, mode: str = "discrete", var: str = "x"):
        rtamt = import_rtamt()
        self.mode = mode
        self.var = var
        self.text = stl.to_rtamt(formula, var)
        if mode == "discrete":
            spec = rtamt.StlDiscreteTimeOfflineSpecification()
        elif mode == "dense":
            spec = rtamt.StlDenseTimeOfflineSpecification()
        else:
            raise ValueError(mode)
        spec.declare_var(var, "float")
        spec.spec = self.text
        spec.parse()
        self.spec = spec

    def __call__(self, x) -> float:
        x = [float(v) for v in np.asarray(x, dtype=float).ravel()]
        t = list(range(len(x)))
        if self.mode == "discrete":
            out = self.spec.evaluate({"time": t, self.var: x})
        else:
            out = self.spec.evaluate([self.var, [[ti, xi] for ti, xi in zip(t, x)]])
        return float(out[0][1])


class LanguageMonitor:
    """Language-based estimate of the robustness of phi: -max_k Dist(x, b_k^{not phi})."""

    def __init__(self, neg_boxes: BoxUnion):
        self.boxes = neg_boxes

    def __call__(self, x) -> float:
        return float(-self.boxes.max_signed_distance(np.asarray(x, dtype=float)[None, :])[0])


def timed(fn, *args, **kwargs):
    """Call fn and return (result, elapsed_ms) measured with perf_counter_ns."""
    t0 = time.perf_counter_ns()
    out = fn(*args, **kwargs)
    return out, (time.perf_counter_ns() - t0) / 1e6
