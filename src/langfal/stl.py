"""Discrete-time STL (DT-STL) over a scalar signal: AST, robustness, NNF, RTAMT rendering.

Scope follows the paper's setting (Def. 2.1, Cor. 2.4): one-dimensional signals and atoms
``x <= c``, ``x < c``, ``x >= c``, ``x > c``. Robustness is the usual space robustness
(min/max over time windows), which is what RTAMT's discrete-time offline interpreter computes.
Time windows are truncated at the end of the trace, exactly like RTAMT (checked against
RTAMT in tests/test_stl.py); an *empty* window yields the identity of the operator
(+inf for always, -inf for eventually). Specifications used in experiments always have a
horizon that fits inside the trace, so empty windows never influence robustness at t = 0.

``b = None`` in Always/Eventually means "until the end of the trace" (unbounded operator).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np

_LE_OPS = ("<=", "<")
_GE_OPS = (">=", ">")
_FLIP = {"<=": ">", "<": ">=", ">=": "<", ">": "<="}


@dataclass(frozen=True)
class Atom:
    op: str
    c: float

    def __post_init__(self):
        if self.op not in _FLIP:
            raise ValueError(f"unsupported comparison {self.op!r}")


@dataclass(frozen=True)
class Not:
    f: "Formula"


@dataclass(frozen=True)
class And:
    fs: Tuple["Formula", ...]


@dataclass(frozen=True)
class Or:
    fs: Tuple["Formula", ...]


@dataclass(frozen=True)
class Always:
    a: int
    b: Optional[int]
    f: "Formula"


@dataclass(frozen=True)
class Eventually:
    a: int
    b: Optional[int]
    f: "Formula"


Formula = Union[Atom, Not, And, Or, Always, Eventually]


# ---------------------------------------------------------------- constructors
def le(c): return Atom("<=", float(c))
def lt(c): return Atom("<", float(c))
def ge(c): return Atom(">=", float(c))
def gt(c): return Atom(">", float(c))
def conj(*fs): return And(tuple(fs))
def disj(*fs): return Or(tuple(fs))
def always(a, b, f): return Always(int(a), None if b is None else int(b), f)
def eventually(a, b, f): return Eventually(int(a), None if b is None else int(b), f)
def between(lo, hi): return conj(ge(lo), le(hi))


# ---------------------------------------------------------------- structure
def horizon(f: Formula) -> float:
    """Number of future samples (beyond t) the formula needs; inf for unbounded operators."""
    if isinstance(f, Atom):
        return 0
    if isinstance(f, Not):
        return horizon(f.f)
    if isinstance(f, (And, Or)):
        return max(horizon(g) for g in f.fs)
    if isinstance(f, (Always, Eventually)):
        return math.inf if f.b is None else f.b + horizon(f.f)
    raise TypeError(f)


def nnf(f: Formula, negate: bool = False) -> Formula:
    """Negation normal form (no Not nodes). Robustness is preserved exactly: rho(nnf(f)) == rho(f)."""
    if isinstance(f, Atom):
        return Atom(_FLIP[f.op], f.c) if negate else f
    if isinstance(f, Not):
        return nnf(f.f, not negate)
    if isinstance(f, And):
        kids = tuple(nnf(g, negate) for g in f.fs)
        return Or(kids) if negate else And(kids)
    if isinstance(f, Or):
        kids = tuple(nnf(g, negate) for g in f.fs)
        return And(kids) if negate else Or(kids)
    if isinstance(f, Always):
        return Eventually(f.a, f.b, nnf(f.f, negate)) if negate else Always(f.a, f.b, nnf(f.f))
    if isinstance(f, Eventually):
        return Always(f.a, f.b, nnf(f.f, negate)) if negate else Eventually(f.a, f.b, nnf(f.f))
    raise TypeError(f)


def negation(f: Formula) -> Formula:
    return nnf(f, negate=True)


# ---------------------------------------------------------------- robustness
def _window(t: int, a: int, b: Optional[int], n: int):
    lo = t + a
    hi = n - 1 if b is None else min(t + b, n - 1)
    return lo, hi


def robustness_trace(f: Formula, X: np.ndarray) -> np.ndarray:
    """Robustness of ``f`` at every time index. ``X`` has shape (m, n) (m signals of length n)."""
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[None, :]
    if isinstance(f, Atom):
        return (f.c - X) if f.op in _LE_OPS else (X - f.c)
    if isinstance(f, Not):
        return -robustness_trace(f.f, X)
    if isinstance(f, And):
        return np.minimum.reduce([robustness_trace(g, X) for g in f.fs])
    if isinstance(f, Or):
        return np.maximum.reduce([robustness_trace(g, X) for g in f.fs])
    if isinstance(f, (Always, Eventually)):
        child = robustness_trace(f.f, X)
        m, n = child.shape
        out = np.empty_like(child)
        reduce = np.min if isinstance(f, Always) else np.max
        empty = np.inf if isinstance(f, Always) else -np.inf
        for t in range(n):
            lo, hi = _window(t, f.a, f.b, n)
            out[:, t] = reduce(child[:, lo:hi + 1], axis=1) if lo <= hi else empty
        return out
    raise TypeError(f)


def robustness(f: Formula, X: np.ndarray) -> np.ndarray:
    """Robustness at t = 0 for each signal in ``X`` (shape (m, n) or (n,)). Returns shape (m,)."""
    return robustness_trace(f, X)[:, 0]


def robustness_scalar(f: Formula, xs) -> float:
    """Robustness at t = 0 of one signal (pure Python, memoised): same semantics as ``robustness``.
    Much faster than the vectorised version or RTAMT for single short signals (used as FindBox's
    oracle, which is called millions of times); equality is checked in tests/test_stl.py."""
    x = [float(v) for v in xs]
    n = len(x)
    memo = {}

    def rho(g, t):
        key = (id(g), t)
        if key in memo:
            return memo[key]
        if isinstance(g, Atom):
            r = (g.c - x[t]) if g.op in _LE_OPS else (x[t] - g.c)
        elif isinstance(g, Not):
            r = -rho(g.f, t)
        elif isinstance(g, And):
            r = min(rho(h, t) for h in g.fs)
        elif isinstance(g, Or):
            r = max(rho(h, t) for h in g.fs)
        else:
            lo, hi = _window(t, g.a, g.b, n)
            if lo > hi:
                r = math.inf if isinstance(g, Always) else -math.inf
            elif isinstance(g, Always):
                r = min(rho(g.f, s) for s in range(lo, hi + 1))
            else:
                r = max(rho(g.f, s) for s in range(lo, hi + 1))
        memo[key] = r
        return r

    return rho(f, 0)


# ---------------------------------------------------------------- rendering
def _num(c: float) -> str:
    return str(int(c)) if float(c).is_integer() else repr(float(c))


def to_rtamt(f: Formula, var: str = "x") -> str:
    """Render in RTAMT's STL syntax (discrete-time, intervals in samples with period 1)."""
    if isinstance(f, Atom):
        return f"({var} {f.op} {_num(f.c)})"
    if isinstance(f, Not):
        return f"(not {to_rtamt(f.f, var)})"
    if isinstance(f, And):
        return "(" + " and ".join(to_rtamt(g, var) for g in f.fs) + ")"
    if isinstance(f, Or):
        return "(" + " or ".join(to_rtamt(g, var) for g in f.fs) + ")"
    if isinstance(f, (Always, Eventually)):
        op = "always" if isinstance(f, Always) else "eventually"
        iv = "" if f.b is None else f"[{f.a},{f.b}]"
        if f.b is None and f.a != 0:
            raise ValueError("unbounded operators with a > 0 are not used")
        return f"({op}{iv}({to_rtamt(f.f, var)}))"
    raise TypeError(f)


def to_text(f: Formula, var: str = "x") -> str:
    """Human-readable rendering with step intervals (used in logs and tables)."""
    if isinstance(f, Atom):
        return f"{var}{f.op}{_num(f.c)}"
    if isinstance(f, Not):
        return f"¬({to_text(f.f, var)})"
    if isinstance(f, And):
        return "(" + " ∧ ".join(to_text(g, var) for g in f.fs) + ")"
    if isinstance(f, Or):
        return "(" + " ∨ ".join(to_text(g, var) for g in f.fs) + ")"
    if isinstance(f, (Always, Eventually)):
        sym = "□" if isinstance(f, Always) else "◇"
        iv = "" if f.b is None else f"[{f.a},{f.b}]"
        return f"{sym}{iv}{to_text(f.f, var)}"
    raise TypeError(f)
