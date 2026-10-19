"""E2/E3 (paper Tables 2-3) and E4 (Table 4): falsification of phi1-phi5 on the Chasing Cars model.

Examples:
  python experiments/run_falsification.py --config configs/falsification.yaml --run-id pilot --trials 1
  python experiments/run_falsification.py --config configs/falsification.yaml --run-id main
  python experiments/run_falsification.py --config configs/table4.yaml --run-id main
Records are appended to results/raw/<experiment>/<run-id>/records.jsonl; finished
(spec, trial, method) triples are skipped, so interrupted runs can be resumed with the same command.
"""
from __future__ import annotations

import argparse
import time

import common  # noqa: F401  (sets up sys.path)
from common import (bo_config, cc_problem, initial_design, load_config, method_rng, run_parallel,
                    trial_seed, utf8_stdout)
from langfal.falsification import METHODS
from langfal.runlog import RunDir


def _task(args):
    cfg, spec, trial, method = args
    seed = trial_seed(cfg, trial)
    prob = cc_problem(cfg, spec)
    if prob.neg_boxes.j == 0 and method != "SBO-RTAMT":
        # e.g. FindBox found no box of L(not phi): language-based methods have nothing to work with, and
        # PBO-RTAMT would run j = 0 processes. SBO-RTAMT does not use the language and runs normally.
        # Recorded explicitly instead of silently skipped.
        return {"spec": spec, "trial": trial, "seed": seed, "method": method, "falsified": False,
                "iterations": None, "stop_reason": "not-applicable: empty language", "n_boxes": 0,
                "n_sims": 0, "T_T_ms": float("nan"), "T_M_ms": float("nan"), "wall_s": 0.0,
                "sim_ms": 0.0, "gp_ms": 0.0}
    bcfg = bo_config(cfg)
    X0 = initial_design(seed, bcfg.n_init, prob.dim)
    rec = METHODS[method](prob, X0, bcfg, method_rng(seed, method, spec))
    rec.update(spec=spec, trial=trial, seed=seed)
    return rec


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--trials", type=int, help="override n_trials (e.g. 1 for a pilot)")
    ap.add_argument("--trial-ids", type=int, nargs="*", help="run only these trial indices (e.g. audit re-runs)")
    ap.add_argument("--specs", nargs="*", help="subset of specs")
    ap.add_argument("--methods", nargs="*", help="subset of methods")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.trials is not None:
        cfg["n_trials"] = args.trials
    specs = args.specs or cfg["specs"]
    methods = args.methods or cfg["methods"]
    run = RunDir(cfg["experiment"], args.run_id, cfg)
    done = run.done_keys(("spec", "trial", "method"))
    trials = args.trial_ids if args.trial_ids is not None else range(cfg["n_trials"])
    tasks = [(cfg, s, t, m) for s in specs for t in trials for m in methods if (s, t, m) not in done]
    print(f"{len(tasks)} runs to do ({len(done)} already done) -> {run.path}")
    t0 = time.time()
    n = [0]

    def on_result(task, rec):
        run.append(rec)
        n[0] += 1
        print(f"[{n[0]}/{len(tasks)} {time.time() - t0:7.1f}s] {rec['spec']} trial {rec['trial']:2d} "
              f"{rec['method']:9s} falsified={rec['falsified']} S={rec['iterations']} sims={rec['n_sims']} "
              f"T_T={rec['T_T_ms']:.3f}ms wall={rec['wall_s']:.1f}s {rec['stop_reason']}", flush=True)

    run_parallel(_task, tasks, args.workers, on_result)
    run.finish(n_new_records=n[0], elapsed_s=round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
