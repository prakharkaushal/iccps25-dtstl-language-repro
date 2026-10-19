"""Languages of DT-STL formulas as unions of axis-aligned boxes (paper Sec. 2.2, Eq. 3).

DEVIATION (documented in DEVIATIONS.md, L1): the paper approximates the language with the
FindBox code of its ref. [5]. That code has no license and was not approved for use, so we
compile the *exact* language: for 1-D signals with atoms x<=c / x>=c the language of a
bounded-horizon formula is a finite union of boxes (paper Thm. 2.3/Cor. 2.4). We obtain it by
(i) negation normal form, (ii) unrolling temporal operators over the sample indices
(windows truncated at the trace end, like the robustness semantics in stl.py),
(iii) distributing conjunctions over disjunctions, (iv) dropping empty boxes and boxes contained
in another box. Boxes are closed; strict vs non-strict inequalities only differ on boundaries.

Distances use the paper's metric: ||x - y||_inf = max_t |x(t) - y(t)| (1-D signals), and the
signed distance of Eq. (1): depth to the boundary when inside, minus the distance when outside.
For a box with some infinite bounds, only finite faces count (the box is unbounded there).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import stl


class LanguageTooLarge(RuntimeError):
    pass


@dataclass
class BoxUnion:
    lo: np.ndarray   # (j, n) lower bounds (may be -inf)
    hi: np.ndarray   # (j, n) upper bounds (may be +inf)

    def __post_init__(self):
        self.lo = np.atleast_2d(np.asarray(self.lo, dtype=float))
        self.hi = np.atleast_2d(np.asarray(self.hi, dtype=float))
        if self.lo.shape != self.hi.shape:
            raise ValueError(f"lo/hi shape mismatch {self.lo.shape} vs {self.hi.shape}")

    @property
    def j(self) -> int:
        return self.lo.shape[0]

    @property
    def n(self) -> int:
        return self.lo.shape[1]

    # ------------------------------------------------------------ distances
    def signed_distance(self, X: np.ndarray, boxes=None) -> np.ndarray:
        """Eq. (1) for each signal and box: shape (m, j) (or (m, len(boxes)))."""
        X = np.atleast_2d(np.asarray(X, dtype=float))
        lo = self.lo if boxes is None else self.lo[boxes]
        hi = self.hi if boxes is None else self.hi[boxes]
        L = X[:, None, :] - lo[None, :, :]          # slack to lower faces (+inf if lo = -inf)
        U = hi[None, :, :] - X[:, None, :]          # slack to upper faces (+inf if hi = +inf)
        depth = np.minimum(L.min(axis=2), U.min(axis=2))
        outside = np.maximum(np.maximum((-L).max(axis=2), (-U).max(axis=2)), 0.0)
        return np.where(depth >= 0, depth, -outside)

    def signed_distance_one(self, x: np.ndarray, k: int) -> float:
        """Signed distance of one signal to box k (the 'single component' monitored by PROF)."""
        x = np.asarray(x, dtype=float)
        L = x - self.lo[k]
        U = self.hi[k] - x
        depth = min(L.min(), U.min())
        if depth >= 0:
            return float(depth)
        return -float(max((-L).max(), (-U).max()))

    def max_signed_distance(self, X: np.ndarray) -> np.ndarray:
        """Language monitor: max_k Dist(x, b_k). Exact signed distance to the union for signals
        outside it; inside, it is the largest single-box depth (a lower bound on the depth in the
        union, and equal to the robustness of the DNF formula)."""
        if self.j == 0:
            return np.full(np.atleast_2d(X).shape[0], -np.inf)
        return self.signed_distance(X).max(axis=1)

    def contains(self, X: np.ndarray) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, dtype=float))
        if self.j == 0:
            return np.zeros(X.shape[0], dtype=bool)
        inside = (X[:, None, :] >= self.lo[None]) & (X[:, None, :] <= self.hi[None])
        return inside.all(axis=2).any(axis=1)

    # ------------------------------------------------------------ geometry helpers
    def clipped(self, domain) -> "BoxUnion":
        lo_d, hi_d = domain
        return BoxUnion(np.clip(self.lo, lo_d, hi_d), np.clip(self.hi, lo_d, hi_d))

    def volumes(self, domain) -> np.ndarray:
        c = self.clipped(domain)
        return np.prod(np.maximum(c.hi - c.lo, 0.0), axis=1)

    def project(self, x: np.ndarray, boxes=None):
        """Euclidean projection of x onto the union (or onto a subset of boxes): per-box clipping,
        then the nearest box in the L2 sense. Returns (projected signal, box index)."""
        idx = np.arange(self.j) if boxes is None else np.asarray(boxes)
        P = np.clip(np.asarray(x, dtype=float)[None, :], self.lo[idx], self.hi[idx])
        d = np.linalg.norm(P - x[None, :], axis=1)
        k = int(np.argmin(d))
        return P[k], int(idx[k])

    def sample(self, rng: np.random.Generator, domain, box: int | None = None, weights="uniform"):
        """Uniform sample inside one box (random box if ``box`` is None) clipped to ``domain``."""
        c = self.clipped(domain)
        if box is None:
            if weights == "volume":
                v = c.volumes(domain)
                box = int(rng.choice(self.j, p=v / v.sum()))
            else:
                box = int(rng.integers(self.j))
        return rng.uniform(c.lo[box], c.hi[box]), box

    # ------------------------------------------------------------ persistence
    def to_json(self) -> dict:
        enc = lambda a: [[("inf" if v == np.inf else "-inf" if v == -np.inf else float(v)) for v in row] for row in a]
        return {"n": self.n, "j": self.j, "lo": enc(self.lo), "hi": enc(self.hi)}

    @classmethod
    def from_json(cls, d: dict) -> "BoxUnion":
        dec = lambda a: np.array([[float(v) for v in row] for row in a], dtype=float).reshape(-1, d["n"])
        return cls(dec(d["lo"]), dec(d["hi"]))

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_json(), indent=1))

    @classmethod
    def load(cls, path) -> "BoxUnion":
        return cls.from_json(json.loads(Path(path).read_text()))


# ---------------------------------------------------------------- compiler
def _full(n):
    return np.full((1, n), -np.inf), np.full((1, n), np.inf)


def _empty(n):
    return np.empty((0, n)), np.empty((0, n))


def _prune(lo, hi):
    """Drop empty boxes, duplicates and boxes contained in another box."""
    keep = (lo <= hi).all(axis=1)
    lo, hi = lo[keep], hi[keep]
    if lo.shape[0] <= 1:
        return lo, hi
    # unique rows first (cheap)
    key = np.concatenate([lo, hi], axis=1)
    _, first = np.unique(key, axis=0, return_index=True)
    first.sort()
    lo, hi = lo[first], hi[first]
    k = lo.shape[0]
    contained = np.zeros(k, dtype=bool)
    chunk = max(1, 4_000_000 // max(1, k * lo.shape[1]))
    for s in range(0, k, chunk):
        e = min(k, s + chunk)
        # inside[a, b] : box s+a is contained in box b
        inside = ((lo[None, :, :] <= lo[s:e, None, :]) & (hi[s:e, None, :] <= hi[None, :, :])).all(axis=2)
        inside[np.arange(e - s), np.arange(s, e)] = False
        contained[s:e] = inside.any(axis=1)
    return lo[~contained], hi[~contained]


def _and(A, B, max_boxes):
    (la, ha), (lb, hb) = A, B
    if la.shape[0] * lb.shape[0] > max_boxes * 50:
        raise LanguageTooLarge(f"conjunction of {la.shape[0]} x {lb.shape[0]} boxes")
    lo = np.maximum(la[:, None, :], lb[None, :, :]).reshape(-1, la.shape[1])
    hi = np.minimum(ha[:, None, :], hb[None, :, :]).reshape(-1, la.shape[1])
    lo, hi = _prune(lo, hi)
    if lo.shape[0] > max_boxes:
        raise LanguageTooLarge(f"{lo.shape[0]} boxes after conjunction")
    return lo, hi


def _or(parts, max_boxes):
    lo = np.concatenate([p[0] for p in parts], axis=0)
    hi = np.concatenate([p[1] for p in parts], axis=0)
    lo, hi = _prune(lo, hi)
    if lo.shape[0] > max_boxes:
        raise LanguageTooLarge(f"{lo.shape[0]} boxes after disjunction")
    return lo, hi


def _dnf(f, t, n, max_boxes):
    if isinstance(f, stl.Atom):
        lo, hi = _full(n)
        if f.op in ("<=", "<"):
            hi[0, t] = f.c
        else:
            lo[0, t] = f.c
        return lo, hi
    if isinstance(f, stl.And):
        acc = _full(n)
        for g in f.fs:
            acc = _and(acc, _dnf(g, t, n, max_boxes), max_boxes)
            if acc[0].shape[0] == 0:
                break
        return acc
    if isinstance(f, stl.Or):
        return _or([_dnf(g, t, n, max_boxes) for g in f.fs], max_boxes)
    if isinstance(f, (stl.Always, stl.Eventually)):
        lo_t = t + f.a
        hi_t = n - 1 if f.b is None else min(t + f.b, n - 1)
        if lo_t > hi_t:
            return _full(n) if isinstance(f, stl.Always) else _empty(n)
        parts = [_dnf(f.f, s, n, max_boxes) for s in range(lo_t, hi_t + 1)]
        if isinstance(f, stl.Eventually):
            return _or(parts, max_boxes)
        acc = _full(n)
        for p in parts:
            acc = _and(acc, p, max_boxes)
            if acc[0].shape[0] == 0:
                break
        return acc
    if isinstance(f, stl.Not):
        raise ValueError("formula must be in NNF")
    raise TypeError(f)


def compile_language(f: stl.Formula, n: int, max_boxes: int = 20000) -> BoxUnion:
    """Exact language {x in R^n : (x, 0) |= f} as a union of closed boxes."""
    if stl.horizon(f) > n - 1 and not math.isinf(stl.horizon(f)):
        raise ValueError(f"formula horizon {stl.horizon(f)} exceeds signal length {n}")
    lo, hi = _dnf(stl.nnf(f), 0, n, max_boxes)
    return BoxUnion(lo, hi)


def compile_negated_language(f: stl.Formula, n: int, max_boxes: int = 20000) -> BoxUnion:
    """Boxes b_k^{not phi} used for falsification (paper Eq. 3-4)."""
    return compile_language(stl.Not(f), n, max_boxes)
