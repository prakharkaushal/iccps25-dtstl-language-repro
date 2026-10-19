import numpy as np
import pytest

from langfal import bo, stl
from langfal.falsification import METHODS, FalsificationProblem
from langfal.language import BoxUnion, compile_negated_language
from langfal.monitors import RtamtMonitor


def test_expected_improvement_matches_monte_carlo():
    rng = np.random.default_rng(9)
    mu, sd, best = np.array([0.3, -1.0, 2.0]), np.array([0.5, 2.0, 0.1]), 0.5
    ei = bo.expected_improvement(mu, sd, best)
    mc = np.maximum(mu + sd * rng.standard_normal((400_000, 3)) - best, 0).mean(axis=0)
    np.testing.assert_allclose(ei, mc, rtol=2e-2, atol=2e-3)


def _toy_problem():
    """x_t = 30 * u_t for t = 0..4 (5 samples); phi = always[0,4](x <= 25); falsifiable but small."""
    f = stl.always(0, 4, stl.le(25.0))
    return FalsificationProblem(
        name="toy", simulate=lambda u: 30.0 * np.asarray(u)[:5] * np.asarray(u)[5:10],
        neg_boxes=compile_negated_language(f, 5), rtamt=RtamtMonitor(f), dim=10)


CFG = bo.BOConfig(max_iter=60, n_uniform=300, n_local=300)


@pytest.mark.parametrize("method", list(METHODS))
def test_methods_falsify_toy_problem(method):
    prob = _toy_problem()
    X0 = np.random.default_rng(10).uniform(0, 0.5, size=(5, 10))   # initial points do not falsify
    rec = METHODS[method](prob, X0, CFG, np.random.default_rng(11))
    assert rec["falsified"], rec
    assert rec["falsifier_rho"] < 0
    assert rec["T_M_ms"] > 0 and rec["n_sims"] >= 5


def test_runs_are_deterministic_and_prof_all_prefix_equals_prof():
    prob = _toy_problem()
    X0 = np.random.default_rng(12).uniform(0, 0.5, size=(5, 10))
    a = METHODS["PROF"](prob, X0, CFG, np.random.default_rng(13))
    b = METHODS["PROF"](prob, X0, CFG, np.random.default_rng(13))
    c = METHODS["PROF-all"](prob, X0, CFG, np.random.default_rng(13))
    assert a["iterations"] == b["iterations"] and a["falsifier_u"] == b["falsifier_u"]
    assert c["S_min"] == a["iterations"]


def test_rtamt_rejects_claims_of_an_over_approximate_language():
    """D9: with the exact language a language claim is never rejected; a box containing every signal (like
    FindBox's x(0) <= 40 box for phi1) sends satisfying signals to RTAMT, which rejects and counts them."""
    exact = _toy_problem()
    X0 = np.random.default_rng(10).uniform(0, 0.5, size=(5, 10))   # x <= 7.5: every initial signal satisfies phi
    cfg = bo.BOConfig(max_iter=5, n_uniform=50, n_local=50)
    for method in ("PROF", "SMuRF"):
        assert METHODS[method](exact, X0, cfg, np.random.default_rng(11))["validation_rejections"] == 0
    over = FalsificationProblem(name="toy-over", simulate=exact.simulate,
                                neg_boxes=BoxUnion(np.full((1, 5), -1.0), np.full((1, 5), 100.0)),
                                rtamt=exact.rtamt, dim=10)
    for method in ("PROF", "SMuRF"):
        rec = METHODS[method](over, X0, cfg, np.random.default_rng(11))
        assert rec["validation_rejections"] >= 1
        assert rec["validation_rejections"] == rec["validation_calls"] - int(rec["falsified"])   # one box
        if rec["falsified"]:
            assert rec["falsifier_rho"] < 0
