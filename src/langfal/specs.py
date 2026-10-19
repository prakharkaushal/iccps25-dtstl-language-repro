"""Specifications used in the paper, with our documented discretisation choices.

Falsification (paper Eqs. 8-12, signal x := y5 - y4 of the Chasing Cars model). The paper states
a 100 s horizon sampled at 0.1 Hz ("10 time steps", language in R^10) but phi2 needs samples up
to t = 100 s. DECISION D1: we sample at t = 0, 10, ..., 100 s (11 samples). DECISION D2: an
interval [a, b] in seconds maps to steps [ceil(a/10), floor(b/10)]; phi5's [0,5] s becomes [0,0].
Alternative grids can be built with ``cc_specs(dt=..., n_samples=...)``.

Control (paper Eqs. 14-21, signal x1 = x-position of the UAV). DECISION D17: "length 10"
formulas reference index 10 (e.g. G[8,10]), so they are evaluated on 11 samples (indices 0..10);
"length 30" formulas use indices 0..29 (30 samples), as printed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import stl
from .stl import always, between, conj, disj, eventually, ge, gt, le, lt

CC_DT_SECONDS = 10.0          # 0.1 Hz output sampling (paper)
CC_HORIZON_SECONDS = 100.0    # paper


@dataclass(frozen=True)
class Spec:
    name: str
    paper_text: str            # as printed in the paper
    formula: stl.Formula       # discretised, in sample steps
    n_samples: int             # signal length the formula is evaluated on
    domain: tuple = (-math.inf, math.inf)   # bounds of the signal space (used for sampling/volumes)
    notes: str = ""

    @property
    def text(self) -> str:
        return stl.to_text(self.formula)

    @property
    def rtamt(self) -> str:
        return stl.to_rtamt(self.formula)


def seconds_to_steps(a: float, b: float, dt: float = CC_DT_SECONDS):
    """DECISION D2: [a, b] seconds -> [ceil(a/dt), floor(b/dt)] samples."""
    lo, hi = math.ceil(a / dt - 1e-9), math.floor(b / dt + 1e-9)
    if lo > hi:
        raise ValueError(f"interval [{a},{b}] s contains no sample at dt={dt}")
    return lo, hi


def _G(a, b, f, dt):
    return always(*seconds_to_steps(a, b, dt), f)


def _F(a, b, f, dt):
    return eventually(*seconds_to_steps(a, b, dt), f)


def cc_specs(dt: float = CC_DT_SECONDS, n_samples: int | None = None) -> dict[str, Spec]:
    """Falsification requirements phi1-phi5 (paper Eqs. 8-12) on x = y5 - y4."""
    if n_samples is None:
        n_samples = int(round(CC_HORIZON_SECONDS / dt)) + 1      # D1: 11 samples for dt = 10 s
    raw = {
        "phi1": ("□[0,100](y5−y4 ≤ 40)",
                 lambda: _G(0, 100, le(40), dt)),
        "phi2": ("□[0,70](◇[0,30](y5−y4 ≥ 10))",
                 lambda: _G(0, 70, _F(0, 30, ge(10), dt), dt)),
        "phi3": ("□[0,80]((□[0,20](y5−y4 ≤ 30)) ∨ (◇[0,20](y5−y4 ≥ 35)))",
                 lambda: _G(0, 80, disj(_G(0, 20, le(30), dt), _F(0, 20, ge(35), dt)), dt)),
        "phi4": ("□[0,80]((□[0,20](y5−y4 ≤ 32)) ∨ (◇[0,20](y5−y4 ≥ 33)))",
                 lambda: _G(0, 80, disj(_G(0, 20, le(32), dt), _F(0, 20, ge(33), dt)), dt)),
        "phi5": ("□[0,65](◇[0,30](□[0,5](y5−y4 ≥ 10)))",
                 lambda: _G(0, 65, _F(0, 30, _G(0, 5, ge(10), dt), dt), dt)),
    }
    out = {}
    for name, (text, build) in raw.items():
        f = build()
        h = stl.horizon(f)
        if h > n_samples - 1:
            raise ValueError(f"{name}: horizon {h} does not fit in {n_samples} samples")
        out[name] = Spec(name, text, f, n_samples,
                         notes=f"dt={dt}s, n={n_samples}, horizon={h} steps")
    return out


def uav_specs() -> dict[str, Spec]:
    """Control objectives phi1-phi8 (paper Eqs. 14-21) on x1; D17 for signal lengths.

    DECISION D19: signal domain [0, 20] for the length-10 formulas and [0, 100] for the
    length-30 formulas (needed to sample references and to bound unconstrained coordinates).
    """
    n10, n30 = 11, 30
    d10, d30 = (0.0, 20.0), (0.0, 100.0)
    specs = {
        "phi1": ("□(0 ≤ x1 ≤ 10) ∧ □¬(3 < x1 < 5)",
                 conj(always(0, None, between(0, 10)), always(0, None, stl.Not(conj(gt(3), lt(5))))), n10, d10),
        "phi2": ("◇[0,7](0 ≤ x1 ≤ 3) ∧ □[8,10](0 ≤ x1 ≤ 3)",
                 conj(eventually(0, 7, between(0, 3)), always(8, 10, between(0, 3))), n10, d10),
        "phi3": ("◇[0,10](0 ≤ x1 ≤ 3) ∧ ◇[0,10](7 ≤ x1 ≤ 10)",
                 conj(eventually(0, 10, between(0, 3)), eventually(0, 10, between(7, 10))), n10, d10),
        "phi4": ("◇[0,2](0 ≤ x1 ≤ 2) ∧ ◇[3,5](4 ≤ x1 ≤ 6) ∧ ◇[6,9](15 ≤ x1 ≤ 17)",
                 conj(eventually(0, 2, between(0, 2)), eventually(3, 5, between(4, 6)),
                      eventually(6, 9, between(15, 17))), n10, d10),
        "phi5": ("□(0 ≤ x1 ≤ 100) ∧ □¬(30 < x1 < 50)",
                 conj(always(0, None, between(0, 100)), always(0, None, stl.Not(conj(gt(30), lt(50))))), n30, d30),
        "phi6": ("◇[0,20](40 ≤ x1 ≤ 45) ∧ □[20,29](40 ≤ x1 ≤ 45)",
                 conj(eventually(0, 20, between(40, 45)), always(20, 29, between(40, 45))), n30, d30),
        "phi7": ("◇[0,29](30 ≤ x1 ≤ 35) ∧ ◇[0,29](75 ≤ x1 ≤ 80)",
                 conj(eventually(0, 29, between(30, 35)), eventually(0, 29, between(75, 80))), n30, d30),
        "phi8": ("◇[0,9](x1 ≥ 0 ∧ x1 ≤ 5) ∧ ◇[10,19](x1 ≥ 95 ∧ x1 ≤ 100) ∧ ◇[20,29](x1 ≥ 0 ∧ x1 ≤ 5)",
                 conj(eventually(0, 9, between(0, 5)), eventually(10, 19, between(95, 100)),
                      eventually(20, 29, between(0, 5))), n30, d30),
    }
    return {k: Spec(k, text, f, n, domain=dom, notes=f"n={n}, domain={dom}")
            for k, (text, f, n, dom) in specs.items()}
