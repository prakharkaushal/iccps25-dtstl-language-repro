"""E1 (paper Table 1): accuracy and cost of the language monitor vs RTAMT on the Chasing Cars model.

For N uniformly sampled inputs u in [0,1]^20 we simulate x = y5 - y4 (11 samples, D1) and compare
for each requirement phi1..phi5:
  * RTAMT discrete-time robustness rho (ground truth, DT-STL semantics),
  * language monitor  -max_k Dist(x, b_k^{not phi})  (exact language, deviation L1),
  * agreement: same value (|diff| <= 1e-9 (1+|rho|)), same sign class only (both violate / both
    satisfy, value differs), or complete disagreement,
  * mean time per call (ms) of: RTAMT discrete, RTAMT dense-time, language monitor (all boxes),
    one box ("single component"), and -- extra, not in the paper -- RTAMT discrete on finer grids
    (1 s and 0.1 s sampling, formulas re-discretised) to show how RTAMT cost grows with trace length,
  * satisfying / violating percentages and the number of boxes of L(not phi).

Example:  python experiments/run_e1_monitoring.py --config configs/e1_monitoring.yaml --run-id main --workers 10
"""
from __future__ import annotations

import argparse
import time

import numpy as np

import common  # noqa: F401
from common import cc_config, load_config, run_parallel, utf8_stdout
from langfal import stl
from langfal.language import compile_negated_language
from langfal.monitors import LanguageMonitor, RtamtMonitor
from langfal.runlog import RunDir
from langfal.specs import cc_specs
from langfal.systems.chasing_cars import CCConfig, ChasingCars


def _simulate_chunk(args):
    ccfg_dict, U, fine_dt = args
    sim = ChasingCars(CCConfig(**ccfg_dict))
    xs = np.array([sim(u) for u in U])
    fine = None
    if fine_dt:
        fsim = ChasingCars(CCConfig(**{**ccfg_dict, "sample_dt": fine_dt}))
        fine = np.array([fsim(u) for u in U])
    return xs, fine


def _time_calls(fn, X):
    out = np.empty(len(X))
    fn(X[0])                                   # warm-up (not timed)
    t0 = time.perf_counter_ns()
    for a, x in enumerate(X):
        out[a] = fn(x)
    return out, (time.perf_counter_ns() - t0) / len(X) / 1e6


def _time_interleaved(fns: dict, X):
    """Time several monitors on the same signals in rotating order, so that slow drifts of the
    machine (frequency scaling, background load) affect every monitor equally. Returns
    (values per monitor, mean ms per call per monitor)."""
    names = list(fns)
    vals = {k: np.empty(len(X)) for k in names}
    tot = {k: 0 for k in names}
    for k in names:
        fns[k](X[0])                           # warm-up (not timed)
    for a, x in enumerate(X):
        r = a % len(names)
        for k in names[r:] + names[:r]:
            t0 = time.perf_counter_ns()
            vals[k][a] = fns[k](x)
            tot[k] += time.perf_counter_ns() - t0
    return vals, {k: tot[k] / len(X) / 1e6 for k in names}


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--n", type=int, help="override number of samples")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    cfg = load_config(args.config)
    n = args.n or cfg["n_samples"]
    run = RunDir(cfg["experiment"], args.run_id, {**cfg, "n_samples": n})
    ccfg = cc_config(cfg)
    rng = np.random.default_rng(cfg["seed"])
    U = rng.uniform(size=(n, ccfg.dim))

    t0 = time.time()
    chunks = np.array_split(U, max(1, args.workers * 4))
    timing_n = int(cfg.get("fine_grid_timing_samples", 0))
    results = {}
    tasks = [(cfg.get("cc", {}), c, (1.0 if (i == 0 and timing_n) else None)) for i, c in enumerate(chunks)]
    run_parallel(_simulate_chunk, tasks, args.workers, lambda t, r: results.__setitem__(id(t[1]), r))
    X = np.vstack([results[id(t[1])][0] for t in tasks])
    fine1 = results[id(tasks[0][1])][1]
    sim_s = time.time() - t0
    print(f"simulated {n} inputs in {sim_s:.1f}s; x range [{X.min():.2f}, {X.max():.2f}]")
    np.savez_compressed(run.path / "signals.npz", inputs=U, x=X)

    specs = cc_specs(ccfg.sample_dt, ccfg.n_samples)
    specs_1s = cc_specs(1.0, 101)
    specs_01s = cc_specs(0.1, 1001)
    for name, sp in specs.items():
        tc = time.perf_counter_ns()
        neg = compile_negated_language(sp.formula, sp.n_samples)
        compile_ms = (time.perf_counter_ns() - tc) / 1e6
        rt_d, rt_c = RtamtMonitor(sp.formula, "discrete"), RtamtMonitor(sp.formula, "dense")
        lang = LanguageMonitor(neg)
        vals, ms = _time_interleaved({"rtamt_discrete": rt_d, "rtamt_dense": rt_c, "language": lang,
                                      "one_box": lambda x: neg.signed_distance_one(x, 0)}, X)
        rho, rho_c, lval = vals["rtamt_discrete"], vals["rtamt_dense"], vals["language"]
        t_rd, t_rc, t_l, t_box = ms["rtamt_discrete"], ms["rtamt_dense"], ms["language"], ms["one_box"]
        ours = stl.robustness(sp.formula, X)
        same_value = np.abs(lval - rho) <= 1e-9 * (1.0 + np.abs(rho))
        same_class = (lval < 0) == (rho < 0)
        rec = {
            "spec": name, "paper_text": sp.paper_text, "formula_steps": sp.text, "n": n,
            "n_boxes_neg": neg.j, "language_compile_ms": compile_ms,
            "value_agreement_pct": 100 * same_value.mean(),
            "sign_only_agreement_pct": 100 * (same_class & ~same_value).mean(),
            "complete_disagreement_pct": 100 * (~same_class).mean(),
            "satisfying_pct": 100 * (rho >= 0).mean(), "violating_pct": 100 * (rho < 0).mean(),
            "rho_zero_pct": 100 * (rho == 0).mean(),
            "rtamt_discrete_ms": t_rd, "rtamt_dense_ms": t_rc, "language_ms": t_l, "one_box_ms": t_box,
            "rtamt_dense_vs_discrete_max_abs_diff": float(np.abs(rho_c - rho).max()),
            "ours_vs_rtamt_max_abs_diff": float(np.abs(ours - rho).max()),
        }
        if fine1 is not None:          # extra: RTAMT cost on longer traces (same inputs, subset)
            m1 = RtamtMonitor(specs_1s[name].formula, "discrete")
            _, rec["rtamt_discrete_1s_grid_ms"] = _time_calls(m1, fine1[:timing_n])
            m01 = RtamtMonitor(specs_01s[name].formula, "discrete")
            sim01 = ChasingCars(CCConfig(**{**cfg.get("cc", {}), "sample_dt": 0.1}))
            X01 = np.array([sim01(u) for u in U[: min(timing_n, 50)]])
            _, rec["rtamt_discrete_0.1s_grid_ms"] = _time_calls(m01, X01)
        run.append(rec)
        print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in rec.items() if k != "paper_text"})
    run.finish(elapsed_s=round(time.time() - t0, 1), simulation_s=round(sim_s, 1))


if __name__ == "__main__":
    main()
