"""Sensitivity of violation rates to the time-discretisation decision (D1/D2, paper inconsistency B1).

Simulates N uniform inputs once on a 1 s output grid and evaluates phi1..phi5 under three readings of
"100 s at 0.1 Hz": 11 samples t = 0..100 s (D1, used everywhere), 10 samples t = 0..90 s (windows
truncated at the trace end), and a 1 s grid (101 samples, intervals in seconds).
Writes results/tables/grid_sensitivity.md.

Usage: python analysis/grid_sensitivity.py [--n 2000] [--seed 12345] [--workers 10]
"""
import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from common import run_parallel  # noqa: E402
from langfal import stl  # noqa: E402
from langfal.specs import cc_specs  # noqa: E402
from langfal.systems.chasing_cars import CCConfig, ChasingCars  # noqa: E402

PAPER = [7.08, 1.82, 3.84, 0.87, 7.08]   # paper Table 1 "Satisfaction Ratios (%)"


def _sim(U):
    sim = ChasingCars(CCConfig(sample_dt=1.0))
    return np.array([sim(u) for u in U])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    U = np.random.default_rng(a.seed).uniform(size=(a.n, 20))
    chunks = np.array_split(U, max(1, a.workers * 4))
    out = {}
    run_parallel(_sim, chunks, a.workers, lambda t, r: out.__setitem__(id(t), r))
    Y = np.vstack([out[id(c)] for c in chunks])                 # x at t = 0, 1, ..., 100 s
    s11 = cc_specs(10.0, 11)
    rows = {
        "D1: 11 samples t=0..100 s (used)": [(stl.robustness(s.formula, Y[:, ::10]) < 0).mean() for s in s11.values()],
        "10 samples t=0..90 s (truncated windows)": [(stl.robustness(s.formula, Y[:, :91:10]) < 0).mean() for s in s11.values()],
        "1 s grid, 101 samples": [(stl.robustness(s.formula, Y) < 0).mean() for s in cc_specs(1.0, 101).values()],
    }
    lines = ["# Violation rate (% of uniform inputs with ρ < 0) under three time grids",
             "", f"`[ours]` N = {a.n} uniform inputs (seed {a.seed}); `[paper]` Table 1 'Satisfaction Ratios' "
             "(our interpretation: share inside L(¬φ), see DEVIATIONS.md B5).", "",
             "| Grid | φ1 | φ2 | φ3 | φ4 | φ5 |", "|---|---|---|---|---|---|",
             "| [paper] | " + " | ".join(f"{v:.2f}" for v in PAPER) + " |"]
    lines += [f"| {k} | " + " | ".join(f"{100 * v:.2f}" for v in vals) + " |" for k, vals in rows.items()]
    path = ROOT / "results" / "tables" / "grid_sensitivity.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
