import math

import numpy as np
from scipy.integrate import solve_ivp

from langfal.systems.chasing_cars import CHASE, KEEP, ChasingCars, _next_mode


def test_zero_input_keeps_initial_gaps():
    r = ChasingCars().simulate(np.zeros(20))
    np.testing.assert_allclose(r.y[:, -1], [0, 10, 20, 30, 40])
    np.testing.assert_allclose(r.x, 10.0)
    assert r.n_events == 0


def test_lead_car_matches_numerical_integration():
    rng = np.random.default_rng(6)
    u = rng.uniform(size=20)
    r = ChasingCars().simulate(u)
    th, br = u[:10], u[10:]
    y, v = 0.0, 0.0
    for k in range(10):
        sol = solve_ivp(lambda t, s: [s[1], -th[k] - br[k] * s[1]], (0, 10), [y, v], rtol=1e-11, atol=1e-11)
        y, v = sol.y[0, -1], sol.y[1, -1]
        assert abs(y - r.y[0, k + 1]) < 1e-6


def _fixed_step(u, dt, t_end):
    th, br = u[:10], u[10:]
    y = [0., 10, 20, 30, 40]; v = [0.] * 5; mode = [None] + [KEEP] * 4
    out = [list(y)]; per = int(round(10 / dt)); e1 = math.exp(-dt)
    for k in range(int(round(t_end / dt))):
        seg = min(k // per, 9); T, B = th[seg], br[seg]
        if B > 1e-12:
            vinf = -T / B; e = math.exp(-B * dt)
            ny, nv = [y[0] + vinf * dt + (v[0] - vinf) * (1 - e) / B], [vinf + (v[0] - vinf) * e]
        else:
            ny, nv = [y[0] + v[0] * dt - 0.5 * T * dt * dt], [v[0] - T * dt]
        for i in range(1, 5):
            if mode[i] == KEEP: ny.append(y[i] + v[i] * dt); nv.append(v[i])
            elif mode[i] == CHASE: ny.append(y[i] - v[i] * dt - 0.5 * dt * dt); nv.append(v[i] + dt)
            else: ny.append(y[i] - v[i] * (1 - e1)); nv.append(v[i] * e1)
        y, v = ny, nv
        for i in range(1, 5):
            mode[i] = _next_mode(mode[i], y[i] - y[i - 1])
        if (k + 1) % per == 0:
            out.append(list(y))
    return np.array(out).T


def test_converges_to_fixed_step_reference():
    """A fixed-step simulation (exact per-step closed forms, guards checked every step) must
    approach the event-driven solution as its step shrinks (first-order event-time error)."""
    u = np.random.default_rng(1).uniform(size=20)
    ev = ChasingCars().simulate(u).y[:, :3]
    e1 = np.abs(_fixed_step(u, 4e-4, 20.0) - ev).max()
    e2 = np.abs(_fixed_step(u, 2e-4, 20.0) - ev).max()
    assert e2 < e1 and e2 < 0.2
    assert 1.5 < e1 / max(e2, 1e-12) < 2.7          # roughly halves with the step


def test_switches_happen_at_guard_thresholds():
    u = np.random.default_rng(7).uniform(size=20)
    sim = ChasingCars()
    r = sim.simulate(u, log_switches=True)
    assert r.n_events == len(r.switch_log) > 10
    expected = {("Keeping", "Chasing"): 15.0, ("Keeping", "Braking"): 5.0,
                ("Chasing", "Keeping"): 10.0, ("Braking", "Chasing"): 20.0}
    times = [s[0] for s in r.switch_log]
    assert times == sorted(times)
    for t, car, a, b, gap in r.switch_log:
        assert 2 <= car <= 5
        assert abs(gap - expected[(a, b)]) < 1e-6, (t, car, a, b, gap)


def test_deterministic():
    u = np.random.default_rng(8).uniform(size=20)
    a, b = ChasingCars().simulate(u), ChasingCars().simulate(u)
    np.testing.assert_array_equal(a.y, b.y)
