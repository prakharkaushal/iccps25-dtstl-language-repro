import numpy as np
import pytest

from langfal import stl
from langfal.language import BoxUnion, LanguageTooLarge, compile_language, compile_negated_language
from langfal.specs import cc_specs, uav_specs


def _signals(n, rng, m=400):
    X = rng.uniform(5.0, 45.0, size=(m, n))
    X[:100] = np.round(X[:100] / 5.0) * 5.0     # many exact threshold values
    return X


@pytest.mark.parametrize("name", list(cc_specs()))
def test_negated_language_is_exact(name):
    sp = cc_specs()[name]
    neg = compile_negated_language(sp.formula, sp.n_samples)
    X = _signals(sp.n_samples, np.random.default_rng(3))
    rho = stl.robustness(sp.formula, X)
    md = neg.max_signed_distance(X)
    # language monitor value equals -rho exactly for these specs (no empty conjunctions)
    np.testing.assert_allclose(md, -rho, atol=1e-12)
    # membership: strictly violating signals are inside L(not phi); strictly satisfying are outside
    inside = neg.contains(X)
    assert np.all(inside[rho < 0])
    assert not np.any(inside[rho > 0])


def test_box_counts_of_negated_languages():
    counts = {k: compile_negated_language(s.formula, s.n_samples).j for k, s in cc_specs().items()}
    assert counts == {"phi1": 11, "phi2": 8, "phi3": 27, "phi4": 27, "phi5": 7}


def _naive_signed_distance(x, lo, hi):
    proj = np.clip(x, lo, hi)
    if np.all(proj == x):
        slack = np.concatenate([(x - lo)[np.isfinite(lo)], (hi - x)[np.isfinite(hi)]])
        return slack.min() if slack.size else np.inf
    return -np.abs(x - proj).max()


def test_signed_distance_matches_naive_definition():
    rng = np.random.default_rng(4)
    lo = rng.uniform(-5, 0, size=(6, 4)); hi = lo + rng.uniform(0.5, 5, size=(6, 4))
    lo[0, 1] = -np.inf; hi[2, 3] = np.inf
    U = BoxUnion(lo, hi)
    X = rng.uniform(-8, 8, size=(300, 4))
    D = U.signed_distance(X)
    for a in range(len(X)):
        for k in range(U.j):
            assert D[a, k] == pytest.approx(_naive_signed_distance(X[a], lo[k], hi[k]))
            assert U.signed_distance_one(X[a], k) == pytest.approx(D[a, k])


def test_projection_and_sampling_stay_in_boxes():
    rng = np.random.default_rng(5)
    sp = uav_specs()["phi4"]
    L = compile_language(sp.formula, sp.n_samples)
    assert L.j > 0
    for _ in range(50):
        x = rng.uniform(*sp.domain, size=sp.n_samples)
        p, k = L.project(x)
        assert L.contains(p[None, :])[0]
        s, b = L.sample(rng, sp.domain)
        assert L.contains(s[None, :])[0]
        assert stl.robustness(sp.formula, s[None, :])[0] >= 0


def test_control_language_sizes_and_blowup_guard():
    sizes = {}
    for name, sp in uav_specs().items():
        try:
            sizes[name] = compile_language(sp.formula, sp.n_samples, max_boxes=5000).j
        except LanguageTooLarge:
            sizes[name] = None
    assert sizes["phi5"] is None                       # 2^30 boxes: handled by the product form
    assert sizes["phi2"] == 8 and sizes["phi4"] == 36
