"""Dump every stored SPGA training-result and expected-return pickle (read-only)."""
import sys
import warnings
from pathlib import Path

import numpy as np
import scipy.stats

from safe_pickle import DEFAULT_SPGA_ROOT, load

warnings.filterwarnings("ignore")
root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SPGA_ROOT


def ci95(a):
    a = np.asarray(a, dtype=float)
    if len(a) < 2:
        return float(np.mean(a)), float("nan")
    return float(np.mean(a)), float(scipy.stats.sem(a) * scipy.stats.t.ppf(0.975, len(a) - 1))


for p in sorted(root.rglob("results/*.pkl")):
    d = load(p)
    tt = d["train_time"]
    seqs = {k: len(v) for k, v in d.items() if k != "train_time" and np.ndim(v) > 0}
    scal = {k: round(float(v), 3) for k, v in d.items() if np.ndim(v) == 0}
    print(p.relative_to(root).as_posix())
    print(f"   keys={sorted(d)}")
    print(f"   n_trials={len(tt)} train_time={[round(float(x), 1) for x in tt]}")
    print(f"   scalars={scal}  seq_lens={seqs}")

print("\n=== expected return pickles (mean, 95% t-CI half-width, n, min, max) ===")
for p in sorted(root.rglob("results/expected_return/*.pkl")):
    a = np.asarray(load(p), dtype=float)
    m, h = ci95(a)
    print(f"{p.relative_to(root).as_posix():85s} mean={m:8.3f} ci={h:7.3f} n={len(a)} min={a.min():.2f} max={a.max():.2f}")
