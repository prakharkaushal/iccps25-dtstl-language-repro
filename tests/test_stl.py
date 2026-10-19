import numpy as np
import pytest

from langfal import stl
from langfal.monitors import RtamtMonitor
from langfal.specs import cc_specs, seconds_to_steps, uav_specs


def _random_signals(rng, n, lo, hi, m=150):
    X = rng.uniform(lo, hi, size=(m, n))
    X[: m // 3] = np.round(X[: m // 3])          # include ties / boundary values
    return X


@pytest.mark.parametrize("name", list(cc_specs()))
def test_cc_robustness_matches_rtamt(name):
    sp = cc_specs()[name]
    mon = RtamtMonitor(sp.formula)
    X = _random_signals(np.random.default_rng(0), sp.n_samples, 0.0, 50.0)
    ours = stl.robustness(sp.formula, X)
    ref = np.array([mon(x) for x in X])
    np.testing.assert_allclose(ours, ref, atol=1e-9)


@pytest.mark.parametrize("name", list(uav_specs()))
def test_uav_robustness_matches_rtamt(name):
    sp = uav_specs()[name]
    mon = RtamtMonitor(sp.formula)
    X = _random_signals(np.random.default_rng(1), sp.n_samples, *sp.domain)
    ours = stl.robustness(sp.formula, X)
    ref = np.array([mon(x) for x in X])
    np.testing.assert_allclose(ours, ref, atol=1e-9)


def test_trace_end_truncation_matches_rtamt():
    f = stl.eventually(0, 3, stl.ge(10))
    x = np.array([10, 12, 9, 15, 41, 8, 7, 11, 30, 33, 36], dtype=float)
    mon = RtamtMonitor(f)
    s = mon.spec.evaluate({"time": list(range(len(x))), "x": list(x)})
    np.testing.assert_allclose(stl.robustness_trace(f, x)[0], [r for _, r in s])


def _random_formula(rng, depth=3):
    if depth == 0 or rng.random() < 0.3:
        return stl.Atom(rng.choice(["<=", "<", ">=", ">"]), float(rng.integers(0, 20)))
    k = rng.integers(0, 5)
    if k == 0:
        return stl.Not(_random_formula(rng, depth - 1))
    if k == 1:
        return stl.conj(_random_formula(rng, depth - 1), _random_formula(rng, depth - 1))
    if k == 2:
        return stl.disj(_random_formula(rng, depth - 1), _random_formula(rng, depth - 1))
    a = int(rng.integers(0, 2)); b = a + int(rng.integers(0, 3))
    op = stl.always if k == 3 else stl.eventually
    return op(a, b, _random_formula(rng, depth - 1))


def test_nnf_preserves_robustness_and_negation():
    rng = np.random.default_rng(2)
    X = rng.uniform(0, 20, size=(40, 12))
    for _ in range(200):
        f = _random_formula(rng)
        if stl.horizon(f) > 11:
            continue
        r = stl.robustness(f, X)
        np.testing.assert_allclose(stl.robustness(stl.nnf(f), X), r)
        np.testing.assert_allclose(stl.robustness(stl.negation(f), X), -r)


def test_seconds_to_steps_decision_D2():
    assert seconds_to_steps(0, 100) == (0, 10)
    assert seconds_to_steps(0, 30) == (0, 3)
    assert seconds_to_steps(0, 5) == (0, 0)
    assert seconds_to_steps(0, 65) == (0, 6)
    sp = cc_specs()
    assert stl.horizon(sp["phi2"].formula) == 10
    assert stl.horizon(sp["phi5"].formula) == 9
    assert all(s.n_samples == 11 for s in sp.values())
