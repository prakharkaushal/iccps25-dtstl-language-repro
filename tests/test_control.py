import numpy as np
import pytest

from langfal import stl
from langfal.control import (LCConfig, ProductLanguage, control_language, langcontrol_lcp,
                             langcontrol_lcw, product_language)
from langfal.language import compile_language
from langfal.specs import uav_specs
from langfal.systems.uav import UAVTracker


def test_product_language_matches_dnf_on_short_signals():
    f = stl.conj(stl.always(0, None, stl.between(0, 10)), stl.always(0, None, stl.Not(stl.conj(stl.gt(3), stl.lt(5)))))
    n = 5
    pl = product_language(f, n, (0.0, 20.0))
    dnf = compile_language(f, n)
    assert isinstance(pl, ProductLanguage) and pl.n_boxes == dnf.j == 2 ** n
    rng = np.random.default_rng(0)
    X = rng.uniform(-2, 12, size=(2000, n))
    np.testing.assert_array_equal(pl.contains(X), dnf.contains(X))
    P = pl.project_batch(X[:200])
    for x, p in zip(X[:200], P):
        q, _ = dnf.project(x)
        assert np.linalg.norm(p - x) == pytest.approx(np.linalg.norm(q - x))
    S = pl.sample_batch(rng, 500)
    assert pl.contains(S).all() and (stl.robustness(f, S) >= 0).all()


def test_planar_tracker_is_exact():
    X = np.random.default_rng(1).uniform(0, 20, size=(20, 11))
    np.testing.assert_allclose(UAVTracker(planar=True).track(X), UAVTracker(planar=False).track(X), atol=1e-9)


def test_tracker_follows_slow_references():
    ref = np.linspace(0, 5, 11)[None, :]
    out = UAVTracker().track(ref)
    assert np.abs(out - ref).max() < 0.6


@pytest.mark.parametrize("name", list(uav_specs()))
def test_domain_bounded_robustness_matches_language_membership(name):
    """E6 fairness: BO's success test (rho of phi AND always-in-domain >= 0) must equal LangControl's test."""
    sp = uav_specs()[name]
    lo, hi = sp.domain
    X = UAVTracker().track(np.random.default_rng(4).uniform(lo, hi, size=(200, sp.n_samples)))
    bounded = stl.conj(sp.formula, stl.always(0, None, stl.between(lo, hi)))
    np.testing.assert_array_equal(stl.robustness(bounded, X) >= 0, control_language(sp).contains(X))


def test_robustness_bo_control_baseline_on_easy_objective():
    from langfal.bo import BOConfig
    from langfal.control import robustness_bo_control
    from langfal.monitors import RtamtMonitor
    sp = uav_specs()["phi3"]
    cfg = BOConfig(n_init=5, max_iter=20, n_uniform=200, n_local=200)
    res = robustness_bo_control(UAVTracker().track, RtamtMonitor(sp.formula), sp.n_samples, sp.domain, cfg,
                                np.random.default_rng(3))
    assert res["success"] and res["best_rho"] >= 0 and 1 <= res["iterations"] <= 25
    again = robustness_bo_control(UAVTracker().track, RtamtMonitor(sp.formula), sp.n_samples, sp.domain, cfg,
                                  np.random.default_rng(3))
    assert again["iterations"] == res["iterations"]           # deterministic given the seed


@pytest.mark.parametrize("variant", ["LCW", "LCP"])
def test_langcontrol_finds_feasible_signal_for_easy_objective(variant):
    sp = uav_specs()["phi3"]                      # reach [0,3] and [7,10] within 10 s
    lang = control_language(sp)
    fn = langcontrol_lcw if variant == "LCW" else langcontrol_lcp
    res = fn(lang, UAVTracker().track, np.random.default_rng(2), reps=5, cfg=LCConfig(M=20, K=5, max_processes=8))
    assert (res.iterations > 0).all()
    assert res.n_tracks >= 5
