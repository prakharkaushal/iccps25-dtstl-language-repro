"""Falsification algorithms of the paper (Sec. 3) and the RTAMT baselines.

  PROF       Alg. 1: one BO process per box of L(not phi), maximising Dist(x, b_k); stop when any
             process finds a falsifier. ``until="all"`` gives Table 4's *modified PROF* (continue until
             every box is falsified or the iteration cap is hit).
  PBO-RTAMT  j BO processes (j = number of boxes) maximising -rho (RTAMT robustness).
  SMuRF      Alg. 2: one GP per box, MinBO EI with the global incumbent (Eq. 7); one simulation per
             iteration evaluated against all boxes.
  SBO-RTAMT  single BO process maximising -rho.
  SEQ-BO     Table 4 (b): boxes in random order, <= max_iter iterations per box, data reused.

Parallel methods are emulated in lock step (one "round" = one iteration of every active process);
this preserves iteration counts, and monitoring time is reported both on the critical path
(sum over rounds of the slowest process, i.e. what a truly parallel run would see) and in total.

Our decisions (see DEVIATIONS.md): D7 shared starting points, D8 iteration counting (iterations
after the n_init initial samples; 0 if an initial sample already falsifies), D9 a language-based
candidate needs Dist > 0 (Eq. 4) and is re-checked with RTAMT (rho < 0); D10 PBO-RTAMT processes
share the initial data and differ by their random streams; D11 timing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

import numpy as np

from . import bo
from .language import BoxUnion
from .monitors import RtamtMonitor


@dataclass
class FalsificationProblem:
    name: str
    simulate: Callable[[np.ndarray], np.ndarray]     # u in [0,1]^dim -> sampled signal x
    neg_boxes: BoxUnion                               # boxes of L(not phi)
    rtamt: RtamtMonitor                               # ground-truth DT-STL robustness of phi
    dim: int


@dataclass
class Meter:
    """Costs of one run. Times in milliseconds."""
    n_sims: int = 0
    sim_ms: float = 0.0
    monitor_calls: int = 0
    monitor_ms_total: float = 0.0
    monitor_ms_critical: float = 0.0
    validation_calls: int = 0
    validation_rejections: int = 0        # language claimed a falsifier (Dist > 0) but RTAMT rho >= 0
    validation_ms: float = 0.0
    gp_ms: float = 0.0
    acq_ms: float = 0.0
    n_gp_fits: int = 0

    def summary(self) -> dict:
        d = dict(self.__dict__)
        d["T_T_ms"] = self.monitor_ms_critical
        d["T_M_ms"] = self.monitor_ms_total / self.monitor_calls if self.monitor_calls else float("nan")
        return d


def _ns_ms(t0):
    return (time.perf_counter_ns() - t0) / 1e6


class _Run:
    """Shared bookkeeping for one falsification run."""

    def __init__(self, prob: FalsificationProblem, cfg: bo.BOConfig):
        self.prob = prob
        self.cfg = cfg
        self.m = Meter()
        self.t_wall = time.perf_counter()
        self.falsifier = None

    def simulate(self, u):
        t0 = time.perf_counter_ns()
        x = self.prob.simulate(u)
        self.m.sim_ms += _ns_ms(t0)
        self.m.n_sims += 1
        return x

    def monitor(self, fn, *args):
        """A monitoring call (one 'component'): returns (value, elapsed ms)."""
        t0 = time.perf_counter_ns()
        val = fn(*args)
        ms = _ns_ms(t0)
        self.m.monitor_calls += 1
        self.m.monitor_ms_total += ms
        return val, ms

    def validate(self, x) -> float:
        t0 = time.perf_counter_ns()
        rho = self.prob.rtamt(x)
        self.m.validation_ms += _ns_ms(t0)
        self.m.validation_calls += 1
        self.m.validation_rejections += int(rho >= 0.0)
        return rho

    def propose(self, sur: bo.Surrogate, X, y, rng, best=None):
        fit0 = sur.fit_ms
        sur.fit(X, y)
        self.m.gp_ms += sur.fit_ms - fit0
        self.m.n_gp_fits += 1
        t0 = time.perf_counter_ns()
        u, ei = bo.propose(sur, X, y, self.prob.dim, self.cfg, rng, best=best)
        self.m.acq_ms += _ns_ms(t0)
        return u, ei

    def record(self, method, falsified, iterations, stop_reason, **extra):
        rec = {"method": method, "falsified": bool(falsified), "iterations": iterations,
               "stop_reason": stop_reason, "wall_s": time.perf_counter() - self.t_wall,
               "n_boxes": self.prob.neg_boxes.j}
        rec.update(self.m.summary())
        if self.falsifier is not None:
            u, x, rho, k = self.falsifier
            rec.update(falsifier_u=[float(v) for v in u], falsifier_x=[float(v) for v in x],
                       falsifier_rho=float(rho), falsifier_box=k)
        rec.update(extra)
        return rec


def _streams(rng: np.random.Generator, n: int):
    return [np.random.default_rng(s) for s in rng.bit_generator.seed_seq.spawn(n)] \
        if hasattr(rng.bit_generator, "seed_seq") and rng.bit_generator.seed_seq is not None \
        else [np.random.default_rng(rng.integers(2**63)) for _ in range(n)]


# ---------------------------------------------------------------------------------- PROF
def run_prof(prob, X0, cfg: bo.BOConfig, rng, until: str = "first"):
    """Alg. 1. until='first' -> PROF (Table 2); until='all' -> modified PROF (Table 4)."""
    run = _Run(prob, cfg)
    boxes = prob.neg_boxes
    j = boxes.j
    S0 = [run.simulate(u) for u in X0]
    Xs = [list(map(np.asarray, X0)) for _ in range(j)]
    Ys, success, init_ms = [], [None] * j, []
    for k in range(j):
        vals, ms_k = [], 0.0
        for x in S0:
            d, ms = run.monitor(boxes.signed_distance_one, x, k)
            vals.append(d)
            ms_k += ms
        Ys.append(vals)
        init_ms.append(ms_k)
    run.m.monitor_ms_critical += max(init_ms) if init_ms else 0.0
    for k in range(j):
        i = int(np.argmax(Ys[k]))
        if Ys[k][i] > 0.0:
            rho = run.validate(S0[i])
            if rho < 0.0:
                success[k] = 0
                if run.falsifier is None:
                    run.falsifier = (X0[i], S0[i], rho, k)
    rngs = _streams(rng, j)
    surs = [bo.Surrogate(cfg, rngs[k]) for k in range(j)]
    first = 0 if any(s is not None for s in success) else None
    it = 0
    if not (until == "first" and first is not None):
        active = [k for k in range(j) if success[k] is None] if until == "all" else list(range(j))
        for it in range(1, cfg.max_iter + 1):
            round_ms = []
            for k in active:
                u, _ = run.propose(surs[k], Xs[k], Ys[k], rngs[k])
                x = run.simulate(u)
                d, ms = run.monitor(boxes.signed_distance_one, x, k)
                round_ms.append(ms)
                Xs[k].append(u)
                Ys[k].append(d)
                if d > 0.0 and success[k] is None:
                    rho = run.validate(x)
                    if rho < 0.0:
                        success[k] = it
                        if run.falsifier is None:
                            run.falsifier = (u, x, rho, k)
            run.m.monitor_ms_critical += max(round_ms) if round_ms else 0.0
            if first is None and any(s is not None for s in success):
                first = it
            if until == "first" and first is not None:
                break
            if until == "all":
                active = [k for k in active if success[k] is None]
                if not active:
                    break
    if until == "first":
        return run.record("PROF", first is not None, first if first is not None else cfg.max_iter,
                          "falsified" if first is not None else "cap",
                          best_dist_per_box=[float(max(y)) for y in Ys])
    capped = [k for k in range(j) if success[k] is None]
    iters = [s if s is not None else cfg.max_iter for s in success]
    return run.record("PROF-all", first is not None, first if first is not None else cfg.max_iter,
                      "all-falsified" if not capped else "cap",
                      S_min=int(min(iters)), S_max=int(max(iters)), per_box_iterations=iters,
                      never_falsified_boxes=capped, best_dist_per_box=[float(max(y)) for y in Ys])


# ---------------------------------------------------------------------------------- PBO-RTAMT
def run_pbo_rtamt(prob, X0, cfg: bo.BOConfig, rng):
    """j parallel BO processes on -rho (RTAMT), lock-step (D10)."""
    run = _Run(prob, cfg)
    j = prob.neg_boxes.j
    S0 = [run.simulate(u) for u in X0]
    Ys, init_ms = [], []
    for _ in range(j):              # every process monitors its own initial data
        vals, ms_p = [], 0.0
        for x in S0:
            r, ms = run.monitor(prob.rtamt, x)
            vals.append(-r)
            ms_p += ms
        Ys.append(vals)
        init_ms.append(ms_p)
    run.m.monitor_ms_critical += max(init_ms)
    i = int(np.argmax(Ys[0]))
    if Ys[0][i] > 0.0:
        run.falsifier = (X0[i], S0[i], -Ys[0][i], None)
        return run.record("PBO-RTAMT", True, 0, "falsified")
    Xs = [list(map(np.asarray, X0)) for _ in range(j)]
    rngs = _streams(rng, j)
    surs = [bo.Surrogate(cfg, rngs[p]) for p in range(j)]
    for it in range(1, cfg.max_iter + 1):
        round_ms, found = [], False
        for p in range(j):
            u, _ = run.propose(surs[p], Xs[p], Ys[p], rngs[p])
            x = run.simulate(u)
            r, ms = run.monitor(prob.rtamt, x)
            round_ms.append(ms)
            Xs[p].append(u)
            Ys[p].append(-r)
            if r < 0.0 and run.falsifier is None:
                run.falsifier = (u, x, r, None)
                found = True
        run.m.monitor_ms_critical += max(round_ms)
        if found:
            return run.record("PBO-RTAMT", True, it, "falsified")
    return run.record("PBO-RTAMT", False, cfg.max_iter, "cap")


# ---------------------------------------------------------------------------------- SMuRF
def run_smurf(prob, X0, cfg: bo.BOConfig, rng):
    """Alg. 2 with MinBO EI (Eq. 7): per-box GPs, global incumbent, one simulation per iteration."""
    run = _Run(prob, cfg)
    boxes = prob.neg_boxes
    j = boxes.j
    X = list(map(np.asarray, X0))
    Y = []
    for u in X0:
        x = run.simulate(u)
        dists, ms = run.monitor(lambda s: boxes.signed_distance(s[None, :])[0], x)
        run.m.monitor_ms_critical += ms
        Y.append(dists)
        if dists.max() > 0.0 and run.falsifier is None:
            rho = run.validate(x)
            if rho < 0.0:
                run.falsifier = (u, x, rho, int(np.argmax(dists)))
    if run.falsifier is not None:
        return run.record("SMuRF", True, 0, "falsified")
    rngs = _streams(rng, j + 1)
    surs = [bo.Surrogate(cfg, rngs[k]) for k in range(j)]
    for it in range(1, cfg.max_iter + 1):
        Ymat = np.asarray(Y)
        ystar = float(Ymat.max())
        best_u, best_ei, best_k = None, -np.inf, None
        for k in range(j):
            u_k, ei_k = run.propose(surs[k], X, Ymat[:, k], rngs[k], best=ystar)
            if ei_k > best_ei:
                best_u, best_ei, best_k = u_k, ei_k, k
        x = run.simulate(best_u)
        dists, ms = run.monitor(lambda s: boxes.signed_distance(s[None, :])[0], x)
        run.m.monitor_ms_critical += ms
        X.append(best_u)
        Y.append(dists)
        if dists.max() > 0.0:
            rho = run.validate(x)
            if rho < 0.0:
                run.falsifier = (best_u, x, rho, int(np.argmax(dists)))
                return run.record("SMuRF", True, it, "falsified")
    return run.record("SMuRF", False, cfg.max_iter, "cap")


# ---------------------------------------------------------------------------------- SBO-RTAMT
def run_sbo_rtamt(prob, X0, cfg: bo.BOConfig, rng):
    run = _Run(prob, cfg)
    X, Y = list(map(np.asarray, X0)), []
    for u in X0:
        x = run.simulate(u)
        r, ms = run.monitor(prob.rtamt, x)
        run.m.monitor_ms_critical += ms
        Y.append(-r)
        if r < 0.0 and run.falsifier is None:
            run.falsifier = (u, x, r, None)
    if run.falsifier is not None:
        return run.record("SBO-RTAMT", True, 0, "falsified")
    sur = bo.Surrogate(cfg, rng)
    for it in range(1, cfg.max_iter + 1):
        u, _ = run.propose(sur, X, Y, rng)
        x = run.simulate(u)
        r, ms = run.monitor(prob.rtamt, x)
        run.m.monitor_ms_critical += ms
        X.append(u)
        Y.append(-r)
        if r < 0.0:
            run.falsifier = (u, x, r, None)
            return run.record("SBO-RTAMT", True, it, "falsified")
    return run.record("SBO-RTAMT", False, cfg.max_iter, "cap")


# ---------------------------------------------------------------------------------- SEQ-BO (Table 4b)
def run_sequential_bo(prob, X0, cfg: bo.BOConfig, rng):
    """Random box order; a fresh BO on one box for <= max_iter iterations, then switch (D13).

    Every box restarts from the trial's n_init initial signals (simulated once, re-monitored for
    the new box); data gathered for earlier boxes is not reused, which keeps each GP <= n_init +
    max_iter points (the paper does not say whether data is reused)."""
    run = _Run(prob, cfg)
    boxes = prob.neg_boxes
    order = [int(k) for k in rng.permutation(boxes.j)]
    S0 = [run.simulate(u) for u in X0]
    total = 0
    for pos, k in enumerate(order):
        X, sigs, y = list(map(np.asarray, X0)), list(S0), []
        for x in sigs:
            d, ms = run.monitor(boxes.signed_distance_one, x, k)
            run.m.monitor_ms_critical += ms
            y.append(d)
        i = int(np.argmax(y))
        if y[i] > 0.0:
            rho = run.validate(sigs[i])
            if rho < 0.0:
                run.falsifier = (X[i], sigs[i], rho, k)
                return run.record("SEQ-BO", True, total, "falsified", boxes_tried=pos + 1, box_order=order)
        sur = bo.Surrogate(cfg, rng)
        for _ in range(cfg.max_iter):
            u, _ = run.propose(sur, X, y, rng)
            x = run.simulate(u)
            d, ms = run.monitor(boxes.signed_distance_one, x, k)
            run.m.monitor_ms_critical += ms
            X.append(u)
            sigs.append(x)
            y.append(d)
            total += 1
            if d > 0.0:
                rho = run.validate(x)
                if rho < 0.0:
                    run.falsifier = (u, x, rho, k)
                    return run.record("SEQ-BO", True, total, "falsified", boxes_tried=pos + 1, box_order=order)
    return run.record("SEQ-BO", False, total, "all-boxes-exhausted", boxes_tried=len(order), box_order=order)


METHODS = {
    "PROF": lambda p, X0, c, r: run_prof(p, X0, c, r, until="first"),
    "PBO-RTAMT": run_pbo_rtamt,
    "SMuRF": run_smurf,
    "SBO-RTAMT": run_sbo_rtamt,
    "PROF-all": lambda p, X0, c, r: run_prof(p, X0, c, r, until="all"),
    "SEQ-BO": run_sequential_bo,
}
