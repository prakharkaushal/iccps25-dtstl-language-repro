"""LangControl (paper Alg. 3): control with the language. LCW = whole language, LCP = one box per process.

Algorithm 3 (as printed):  m <- 0; while m <= M: x_ref <- Sample(B);
  for count = 0..K: x, u <- Track(x_ref); if x in B: return x, u; else x_ref <- Projection(x, B)
  m <- m + 1.   Return failure.
"LCW": B = L(phi) (no parallelism). "LCP": B = a single box per process, boxes distributed over
processes; "each tracking result is checked for whether it entered any box" of L(phi).
P_bar = average number of iterations until a feasible signal (paper Table 5). We count one
iteration per Track call; for LCP an iteration is one lock-step round of all processes.

Our decisions (paper silent): D16 Sample = uniform box, then uniform point (unconstrained coordinates
from the domain D19); Projection = Euclidean projection onto the nearest box (L2); M = 500, K = 10;
D21 LCP uses at most ``max_processes`` boxes (a seeded random subset when the language has more).
Runs are batched over replications (and processes) so that one vectorised Track call advances all of
them by one iteration; this does not change the algorithm.

Languages whose formula is a conjunction of unbounded "always" over atom-only formulas (control
phi1, phi5) are represented exactly as a product of per-sample interval unions (ProductLanguage):
their DNF has 2^11 and 2^30 boxes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from . import stl
from .language import BoxUnion, compile_language


# ------------------------------------------------------------------ product languages
def _intervals(g):
    """Union of closed intervals satisfying a temporal-free formula (NNF) at one sample."""
    if isinstance(g, stl.Atom):
        return [(-np.inf, g.c)] if g.op in ("<=", "<") else [(g.c, np.inf)]
    if isinstance(g, stl.Or):
        out = [iv for h in g.fs for iv in _intervals(h)]
        return _merge(out)
    if isinstance(g, stl.And):
        acc = [(-np.inf, np.inf)]
        for h in g.fs:
            acc = _merge([(max(a, c), min(b, d)) for a, b in acc for c, d in _intervals(h) if max(a, c) <= min(b, d)])
        return acc
    raise TypeError("temporal operator inside a product language")


def _merge(ivs):
    ivs = sorted(ivs)
    out = []
    for a, b in ivs:
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


@dataclass
class ProductLanguage:
    intervals: list           # per sample: list of (lo, hi), clipped to the domain

    @property
    def n(self):
        return len(self.intervals)

    @property
    def n_boxes(self) -> int:
        k = 1
        for ivs in self.intervals:
            k *= len(ivs)
        return k

    def contains(self, X) -> np.ndarray:
        X = np.atleast_2d(X)
        ok = np.ones(len(X), dtype=bool)
        for t, ivs in enumerate(self.intervals):
            ok &= np.any([(X[:, t] >= a) & (X[:, t] <= b) for a, b in ivs], axis=0)
        return ok

    def project_batch(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        P = np.empty_like(X)
        for t, ivs in enumerate(self.intervals):
            cand = np.stack([np.clip(X[:, t], a, b) for a, b in ivs], axis=1)
            P[:, t] = cand[np.arange(len(X)), np.argmin(np.abs(cand - X[:, t:t + 1]), axis=1)]
        return P

    def sample_batch(self, rng, k):
        S = np.empty((k, self.n))
        for t, ivs in enumerate(self.intervals):
            lens = np.array([b - a for a, b in ivs])
            idx = rng.choice(len(ivs), size=k, p=lens / lens.sum())
            lo = np.array([ivs[i][0] for i in idx]); hi = np.array([ivs[i][1] for i in idx])
            S[:, t] = rng.uniform(lo, hi)
        return S

    def random_boxes(self, rng, count) -> BoxUnion:
        """`count` distinct boxes (one interval per sample), uniformly at random (seeded)."""
        count = min(count, self.n_boxes)
        seen, lo, hi = set(), [], []
        while len(lo) < count:
            choice = tuple(int(rng.integers(len(ivs))) for ivs in self.intervals)
            if choice in seen:
                continue
            seen.add(choice)
            lo.append([self.intervals[t][c][0] for t, c in enumerate(choice)])
            hi.append([self.intervals[t][c][1] for t, c in enumerate(choice)])
        return BoxUnion(np.array(lo), np.array(hi))


def product_language(f, n, domain):
    """ProductLanguage if f (in NNF) is a conjunction of unbounded always(0) over atom-only formulas."""
    g = stl.nnf(f)
    parts = g.fs if isinstance(g, stl.And) else (g,)
    per = [(-np.inf, np.inf)]
    for p in parts:
        if not (isinstance(p, stl.Always) and p.a == 0 and p.b is None):
            return None
        try:
            ivs = _intervals(p.f)
        except TypeError:
            return None
        per = _merge([(max(a, c), min(b, d)) for a, b in per for c, d in ivs if max(a, c) <= min(b, d)])
    lo_d, hi_d = domain
    per = [(max(a, lo_d), min(b, hi_d)) for a, b in per if max(a, lo_d) <= min(b, hi_d)]
    return ProductLanguage([list(per) for _ in range(n)])


class UnionLanguage:
    """Adapter giving a BoxUnion the batch interface used by LangControl (clipped to the domain)."""

    def __init__(self, boxes: BoxUnion, domain):
        self.boxes = boxes.clipped(domain)
        self.n_boxes = self.boxes.j

    def contains(self, X):
        return self.boxes.contains(X)

    def project_batch(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        lo, hi = self.boxes.lo, self.boxes.hi
        out = np.empty_like(X)
        for s in range(0, len(X), 256):                 # chunk to bound memory (rows x boxes x n)
            P = np.clip(X[s:s + 256, None, :], lo[None], hi[None])
            k = np.argmin(((P - X[s:s + 256, None, :]) ** 2).sum(axis=2), axis=1)
            out[s:s + 256] = P[np.arange(len(k)), k]
        return out

    def sample_batch(self, rng, k):
        idx = rng.integers(self.boxes.j, size=k)
        return rng.uniform(self.boxes.lo[idx], self.boxes.hi[idx])

    def random_boxes(self, rng, count) -> BoxUnion:
        if count >= self.boxes.j:
            return self.boxes
        idx = np.sort(rng.choice(self.boxes.j, size=count, replace=False))
        return BoxUnion(self.boxes.lo[idx], self.boxes.hi[idx])


def control_language(spec, max_boxes: int = 5000):
    """Exact language of a control objective, in the cheapest exact representation."""
    pl = product_language(spec.formula, spec.n_samples, spec.domain)
    if pl is not None:
        return pl
    return UnionLanguage(compile_language(spec.formula, spec.n_samples, max_boxes=max_boxes), spec.domain)


# ------------------------------------------------------------------ LangControl
@dataclass
class LCConfig:
    M: int = 500                 # outer restarts (D16)
    K: int = 10                  # projections per reference (D16)
    max_processes: int = 64      # LCP cap (D21)


@dataclass
class LCResult:
    iterations: np.ndarray       # per replication; -1 if no feasible signal within the limits
    n_tracks: int                # total Track calls (all processes)
    n_processes: int = 1
    extra: dict = field(default_factory=dict)


def langcontrol_lcw(lang, track, rng, reps: int, cfg: LCConfig) -> LCResult:
    """LCW for `reps` independent replications, advanced together one Track call at a time."""
    xref = lang.sample_batch(rng, reps)
    iters = np.zeros(reps, dtype=int)
    count = np.zeros(reps, dtype=int)
    m = np.zeros(reps, dtype=int)
    result = np.full(reps, -1)
    active = np.arange(reps)
    n_tracks = 0
    while active.size:
        X = track(xref[active])
        n_tracks += active.size
        iters[active] += 1
        ok = lang.contains(X)
        result[active[ok]] = iters[active[ok]]
        keep = ~ok
        act, Xk = active[keep], X[keep]
        count[act] += 1
        proj = count[act] <= cfg.K                     # inner loop continues: project
        if proj.any():
            xref[act[proj]] = lang.project_batch(Xk[proj])
        new = act[~proj]                               # inner loop exhausted: restart
        if new.size:
            m[new] += 1
            count[new] = 0
            alive = new[m[new] <= cfg.M]
            if alive.size:
                xref[alive] = lang.sample_batch(rng, alive.size)
            act = np.setdiff1d(act, new[m[new] > cfg.M])
        active = act
    return LCResult(result, n_tracks, 1)


def robustness_bo_control(track, rho, n: int, domain, bcfg, rng) -> dict:
    """E6 baseline (paper Sec. 4.3, text only): BO on RTAMT robustness instead of the language.

    The decision variable is the reference signal x_ref in domain^n (the same variable LangControl
    manipulates), normalised to [0, 1]^n; the objective is ``rho`` of Track(x_ref); success when
    rho >= 0. The runner passes the RTAMT robustness of (phi AND always(x in domain)), whose sign test
    equals LangControl's membership test in the domain-bounded language (experiments/run_control_bo.py).
    One iteration = one Track call, initial samples included (as P_bar counts every Track call of LCW).
    Our decisions D22-D24 (DEVIATIONS.md); GP/EI settings are the falsification ones (D6).
    """
    from . import bo
    lo, hi = domain
    to_ref = lambda z: lo + (hi - lo) * np.asarray(z)
    t0 = time.perf_counter()
    Z, Y = [], []
    track_ms = gp_ms = 0.0
    sur = bo.Surrogate(bcfg, rng)
    for it in range(1, bcfg.n_init + bcfg.max_iter + 1):
        if it <= bcfg.n_init:
            z = rng.uniform(size=n)
        else:
            f0 = sur.fit_ms
            sur.fit(np.asarray(Z), np.asarray(Y))
            gp_ms += sur.fit_ms - f0
            z, _ = bo.propose(sur, np.asarray(Z), np.asarray(Y), n, bcfg, rng)
        ts = time.perf_counter_ns()
        x = track(to_ref(z)[None, :])[0]
        track_ms += (time.perf_counter_ns() - ts) / 1e6
        r = float(rho(x))
        Z.append(np.asarray(z))
        Y.append(r)
        if r >= 0.0:
            return {"success": True, "iterations": it, "best_rho": r, "track_ms": track_ms,
                    "gp_ms": gp_ms, "wall_s": time.perf_counter() - t0}
    return {"success": False, "iterations": bcfg.n_init + bcfg.max_iter, "best_rho": float(max(Y)),
            "track_ms": track_ms, "gp_ms": gp_ms, "wall_s": time.perf_counter() - t0}


def langcontrol_lcp(lang, track, rng, reps: int, cfg: LCConfig) -> LCResult:
    """LCP: P processes, each running Alg. 3 on its own box; success when any process enters L(phi)."""
    boxes = lang.random_boxes(rng, cfg.max_processes)
    P, n = boxes.j, boxes.n
    lo = np.broadcast_to(boxes.lo, (reps, P, n)).reshape(-1, n)
    hi = np.broadcast_to(boxes.hi, (reps, P, n)).reshape(-1, n)
    xref = rng.uniform(lo, hi)
    rounds = np.zeros(reps, dtype=int)
    count = np.zeros(reps * P, dtype=int)
    m = np.zeros(reps * P, dtype=int)
    result = np.full(reps, -1)
    alive_proc = np.ones(reps * P, dtype=bool)
    active_reps = np.arange(reps)
    n_tracks = 0
    while active_reps.size:
        rows = (active_reps[:, None] * P + np.arange(P)[None, :]).ravel()
        rows = rows[alive_proc[rows]]
        if rows.size == 0:
            break
        X = track(xref[rows])
        n_tracks += rows.size
        rounds[active_reps] += 1
        ok = lang.contains(X)
        rep_of = rows // P
        done_reps = np.unique(rep_of[ok])
        result[done_reps] = rounds[done_reps]
        cont = ~np.isin(rep_of, done_reps)
        r_rows, Xc = rows[cont], X[cont]
        count[r_rows] += 1
        proj = count[r_rows] <= cfg.K
        pr = r_rows[proj]
        xref[pr] = np.clip(Xc[proj], lo[pr], hi[pr])   # projection onto the process's own box
        rs = r_rows[~proj]
        if rs.size:
            m[rs] += 1
            count[rs] = 0
            dead = rs[m[rs] > cfg.M]
            alive_proc[dead] = False
            ok_rs = rs[m[rs] <= cfg.M]
            xref[ok_rs] = rng.uniform(lo[ok_rs], hi[ok_rs])
        still = np.setdiff1d(active_reps, done_reps)
        has_alive = alive_proc.reshape(reps, P)[still].any(axis=1)
        active_reps = still[has_alive]
    return LCResult(result, n_tracks, P)
