import numpy as np
import pytest

from langfal import stl
from langfal.findbox_adapter import FINDBOX_DIR, bounded, run_findbox
from langfal.monitors import RtamtMonitor
from langfal.specs import cc_specs

pytestmark = pytest.mark.skipif(not (FINDBOX_DIR / "LanguageBoxGeneral.py").exists(),
                                reason="FindBox not downloaded (scripts/fetch_findbox.sh)")


@pytest.mark.parametrize("name", list(cc_specs()))
def test_scalar_oracle_equals_rtamt_dense(name):
    sp = cc_specs()[name]
    f = bounded(stl.Not(sp.formula), sp.n_samples, 0, 100)
    X = np.random.default_rng(5).uniform(-5, 105, size=(100, sp.n_samples))
    X[:40] = np.round(X[:40])
    dense = RtamtMonitor(f, "dense")
    np.testing.assert_allclose([stl.robustness_scalar(f, x) for x in X], [dense(x) for x in X], atol=1e-12)


def test_findbox_recovers_a_simple_box():
    """always[0,1](x <= 5) in [0, 10]^2 has the language [0, 5]^2."""
    res = run_findbox(stl.always(0, 1, stl.le(5)), 2, 0, 10, n_samples=20, seed=1)
    assert res["n_boxes"] >= 1
    B = res["boxes"]
    np.testing.assert_allclose(B.lo.min(axis=0), [0, 0], atol=1e-6)
    np.testing.assert_allclose(B.hi.max(axis=0), [5, 5], atol=1e-6)
    assert res["check_over_bad_points"] == 0
