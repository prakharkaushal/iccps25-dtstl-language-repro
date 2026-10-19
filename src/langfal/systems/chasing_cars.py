"""Chasing Cars (CC) benchmark of ARCH-COMP, ported to Python from the canonical Simulink model.

Source (fetched for transcription only, not redistributed; see scripts/fetch_cc_model.sh):
  gitlab.com/goranf/ARCH-COMP, models/FALS/chasing-cars/cars.mdl, commit 8e11a799 (2021-05-07),
  sha256 3fe04206e40ac8b32203c49e494d5ae981873ef6dbd5d9f54c72c42de0d33520.
  The 2019 'falsify' copy (2019/FALS/falsify/benchmarks/chasing-cars/cars.mdl) has identical
  dynamics, transitions, initial values and wiring (checked; only variable names differ).

Dynamics transcribed from the Stateflow charts (positions decrease: cars "run toward -infinity"):
  Car 1 (lead), mode Run:   y1' = v1,  v1' = -Throttle - Brake * v1,      y1(0) = 0,  v1(0) = 0
  Car i = 2..5, input y_in = y_{i-1}, gap d = y_i - y_{i-1};  y_i(0) = 10 (i-1), v_i(0) = 0,
  initial mode Keeping:
    Keeping:  y' = +v (as in the model), v' = 0 (no v_dot assigned in this state, see A-CC1)
    Chasing:  y' = -v,  v' = 1
    Braking:  y' = -v,  v' = -v
    Keeping -> Chasing  if d >= 15   (execution order 1)
    Keeping -> Braking  if d <= 5    (execution order 2)
    Chasing -> Keeping  if d <= 10
    Braking -> Chasing  if d >= 20
  Outputs y1..y5. Inputs Throttle, Brake in [0, 1]; ARCH's run script interpolates inputs with
  'previous' (piecewise constant). Simulink solver: VariableStepAuto, RelTol 1e-3, AbsTol 1e-5.

Assumption A-CC1: Stateflow sets the derivative of a continuous local to 0 in a state that does not
assign it, so v is constant in Keeping. Confirmed against Simulink (MATLAB R2026b): with accurate
integration the official model and this port agree to 6.7e-7 m on 200 random inputs
(scripts/cc_matlab_compare.py, results/tables/cc_port_vs_simulink.md).

Simulation is event driven and exact up to floating point. With fixed modes and inputs every car
moves as  y(tau) = p0 + p1 tau + p2 tau^2 + sum_k c_k exp(-r_k tau)  (closed form per mode).
A follower's next transition is the first root of a guard g(tau) = +-(y_i - y_{i-1}) + const of the
same form. Roots are found by curvature-bound stepping: on [tau, inf) every exponential term's
second derivative is bounded by its value at tau, so U(s) = g + g' s + M s^2 / 2 bounds g from above;
stepping to U's first root never passes the true first crossing (exact in one step for pure
quadratics). Validated against a fixed-step simulation whose error decreases linearly with the step
(tests/test_chasing_cars.py).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

KEEP, CHASE, BRAKE = 0, 1, 2
MODE_NAMES = {KEEP: "Keeping", CHASE: "Chasing", BRAKE: "Braking"}
Y0 = (0.0, 10.0, 20.0, 30.0, 40.0)
INF = math.inf
_exp = math.exp


@dataclass(frozen=True)
class CCConfig:
    horizon: float = 100.0      # s (paper and ARCH)
    n_segments: int = 10        # control points per input (paper: 10 each, 20 in total)
    sample_dt: float = 10.0     # output sampling period, 0.1 Hz (paper); D1 -> 11 samples
    root_tol: float = 1e-12     # stop stepping when the step is below this (s)
    max_root_iter: int = 2000

    @property
    def n_samples(self) -> int:
        return int(round(self.horizon / self.sample_dt)) + 1

    @property
    def dim(self) -> int:
        return 2 * self.n_segments


def _first_quadratic_root(c0, b, a):
    """Smallest s > 0 with a s^2 + b s + c0 = 0, for c0 < 0 (INF if none)."""
    if a == 0.0 or abs(a) < 1e-300:
        return -c0 / b if b > 0.0 else INF
    disc = b * b - 4.0 * a * c0
    if disc < 0.0:
        return INF
    sq = math.sqrt(disc)
    q = -0.5 * (b + math.copysign(sq, b)) if b != 0.0 else -0.5 * sq
    r1 = q / a
    r2 = c0 / q if q != 0.0 else r1
    best = INF
    if r1 > 0.0:
        best = r1
    if 0.0 < r2 < best:
        best = r2
    return best


def _lead_traj(y0, v0, T, B):
    """Lead car: (p0, p1, p2, ((c, r), ...), sign) where v = sign * dy/dt."""
    if B > 1e-12:
        vinf = -T / B
        k = (v0 - vinf) / B
        return [y0 + k, vinf, 0.0, [(-k, B)] if k != 0.0 else [], 1.0]
    return [y0, v0, -0.5 * T, [], 1.0]


def _foll_traj(y0, v0, mode):
    if mode == KEEP:
        return [y0, v0, 0.0, [], 1.0]
    if mode == CHASE:
        return [y0, -v0, -0.5, [], -1.0]
    return [y0 - v0, 0.0, 0.0, [(v0, 1.0)] if v0 != 0.0 else [], -1.0]      # BRAKE


def _pos(tr, tau):
    val = tr[0] + tau * (tr[1] + tau * tr[2])
    for c, r in tr[3]:
        val += c * _exp(-r * tau)
    return val


def _vel(tr, tau):
    """Velocity state v (not dy/dt) at local time tau."""
    dy = tr[1] + 2.0 * tr[2] * tau
    for c, r in tr[3]:
        dy -= r * c * _exp(-r * tau)
    return tr[4] * dy


def _shift(tr, delta):
    """Re-express a trajectory in local time tau' = tau - delta (anchor moved forward by delta)."""
    p0, p1, p2, ex = tr[0], tr[1], tr[2], tr[3]
    return (p0 + delta * (p1 + delta * p2), p1 + 2.0 * p2 * delta, p2,
            [(c * _exp(-r * delta), r) for c, r in ex])


_GUARDS = {
    KEEP: ((1.0, -15.0, CHASE), (-1.0, 5.0, BRAKE)),   # d >= 15 (order 1), d <= 5 (order 2)
    CHASE: ((-1.0, 10.0, KEEP),),                       # d <= 10
    BRAKE: ((1.0, -20.0, CHASE),),                      # d >= 20
}


def _next_mode(mode, d):
    if mode == KEEP:
        if d >= 15.0:
            return CHASE
        if d <= 5.0:
            return BRAKE
        return KEEP
    if mode == CHASE:
        return KEEP if d <= 10.0 else CHASE
    return CHASE if d >= 20.0 else BRAKE


@dataclass
class CCResult:
    t_samples: np.ndarray        # (n_samples,)
    y: np.ndarray                # (5, n_samples) car positions at sample times
    n_events: int                # number of mode switches
    switch_log: list = field(default_factory=list)   # optional (time, car, from, to, gap)

    @property
    def x(self) -> np.ndarray:
        """Falsification signal x = y5 - y4 at the sample times (paper Sec. 3.2)."""
        return self.y[4] - self.y[3]


class ChasingCars:
    def __init__(self, config: CCConfig = CCConfig()):
        self.cfg = config

    def split_inputs(self, u):
        u = np.clip(np.asarray(u, dtype=float).ravel(), 0.0, 1.0)
        n = self.cfg.n_segments
        if u.size != 2 * n:
            raise ValueError(f"expected {2 * n} control points, got {u.size}")
        return u[:n], u[n:]           # DECISION D3: first half throttle, second half brake

    # ------------------------------------------------------------------ root finding
    def _first_crossing(self, p0, p1, p2, ex, horizon):
        """First s in [0, horizon] with g(s) >= 0 for g = p0 + p1 s + p2 s^2 + sum c e^{-r s}."""
        if not ex:
            if p0 >= 0.0:
                return 0.0
            r = _first_quadratic_root(p0, p1, p2)
            return r if r <= horizon else INF
        tau = 0.0
        tol = self.cfg.root_tol
        for _ in range(self.cfg.max_root_iter):
            g = p0 + tau * (p1 + tau * p2)
            dg = p1 + 2.0 * p2 * tau
            M = 2.0 * p2
            for c, r in ex:
                e = c * _exp(-r * tau)
                g += e
                dg -= r * e
                if e > 0.0:
                    M += r * r * e
            if g >= 0.0:
                return tau
            s = _first_quadratic_root(g, dg, 0.5 * M)
            if tau + s > horizon:
                return INF
            tau += s
            if s < tol:
                return tau
        return tau

    def _next_event(self, i, trs, anchors, modes, t_now, valid_until):
        """Absolute time and target mode of follower i's next transition before ``valid_until``
        (the time until which both trajectories involved stay valid); INF if none."""
        horizon = valid_until - t_now
        fi = _shift(trs[i], t_now - anchors[i])
        ff = _shift(trs[i - 1], t_now - anchors[i - 1])
        dp0, dp1, dp2 = fi[0] - ff[0], fi[1] - ff[1], fi[2] - ff[2]
        best, target = INF, None
        for scale, const, tgt in _GUARDS[modes[i]]:
            ex = [(scale * c, r) for c, r in fi[3]] + [(-scale * c, r) for c, r in ff[3]]
            s = self._first_crossing(scale * dp0 + const, scale * dp1, scale * dp2, ex, horizon)
            if s < best:
                best, target = s, tgt
        return t_now + best, target

    # ------------------------------------------------------------------ simulation
    def simulate(self, u, log_switches: bool = False) -> CCResult:
        cfg = self.cfg
        throttle, brake = self.split_inputs(u)
        seg_len = cfg.horizon / cfg.n_segments
        n_s = cfg.n_samples
        t_samples = np.arange(n_s) * cfg.sample_dt
        sample_set = {round(k * cfg.sample_dt, 9): k for k in range(1, n_s)}
        boundaries = {round(k * seg_len, 9): k for k in range(1, cfg.n_segments)}
        stops = sorted(set(sample_set) | set(boundaries) | {round(cfg.horizon, 9)})
        t_end = cfg.horizon

        modes = [None, KEEP, KEEP, KEEP, KEEP]
        trs = [_lead_traj(Y0[0], 0.0, float(throttle[0]), float(brake[0]))] + \
              [_foll_traj(Y0[i], 0.0, KEEP) for i in range(1, 5)]
        anchors = [0.0] * 5
        Y = np.empty((5, n_s))
        Y[:, 0] = Y0
        n_events = 0
        log = [] if log_switches else None
        lead_valid_until = boundaries and min(boundaries) or t_end
        nxt = [None] * 5
        for i in range(1, 5):
            hz = (lead_valid_until if i == 1 else t_end)
            nxt[i] = self._next_event(i, trs, anchors, modes, 0.0, hz)

        for stop in stops:
            while True:
                i_min, te = 1, nxt[1][0]
                for i in (2, 3, 4):
                    if nxt[i][0] < te:
                        i_min, te = i, nxt[i][0]
                if te >= stop:
                    break
                tgt = nxt[i_min][1]
                tr = trs[i_min]
                tau = te - anchors[i_min]
                y_i, v_i = _pos(tr, tau), _vel(tr, tau)
                if log is not None:
                    gap = y_i - _pos(trs[i_min - 1], te - anchors[i_min - 1])
                    log.append((te, i_min + 1, MODE_NAMES[modes[i_min]], MODE_NAMES[tgt], gap))
                modes[i_min] = tgt
                trs[i_min] = _foll_traj(y_i, v_i, tgt)
                anchors[i_min] = te
                n_events += 1
                for j in (i_min, i_min + 1):
                    if j <= 4:
                        hz = lead_valid_until if j == 1 else t_end
                        nxt[j] = self._next_event(j, trs, anchors, modes, te, hz)
            if stop in sample_set:
                k = sample_set[stop]
                Y[:, k] = [_pos(trs[i], stop - anchors[i]) for i in range(5)]
            if stop in boundaries:
                seg = boundaries[stop]
                tau = stop - anchors[0]
                y0, v0 = _pos(trs[0], tau), _vel(trs[0], tau)
                trs[0] = _lead_traj(y0, v0, float(throttle[seg]), float(brake[seg]))
                anchors[0] = stop
                later = [b for b in boundaries if b > stop]
                lead_valid_until = min(later) if later else t_end
                nxt[1] = self._next_event(1, trs, anchors, modes, stop, lead_valid_until)
        return CCResult(t_samples, Y, n_events, log or [])

    def __call__(self, u) -> np.ndarray:
        """Falsification signal x = y5 - y4 sampled at 0.1 Hz (11 samples by default)."""
        return self.simulate(u).x
