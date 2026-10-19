"""E5 (paper Table 5): LangControl LCW vs LCP on the UAV model, objectives phi1-phi8.

For every objective and variant, `reps` independent replications run Algorithm 3 from different
random initial references (paper: 1000 replications). P_bar = mean number of iterations until a
feasible signal; failures (no feasible signal within M, K) are counted separately.

Example: python experiments/run_control.py --config configs/control.yaml --run-id main
"""
from __future__ import annotations

import argparse
import time

import numpy as np

import common  # noqa: F401
from common import load_config, method_rng, run_parallel, trial_seed, utf8_stdout
from langfal.control import LCConfig, control_language, langcontrol_lcp, langcontrol_lcw
from langfal.runlog import RunDir
from langfal.specs import uav_specs
from langfal.systems.uav import TrackerGains, UAVParams, UAVTracker


def _task(args):
    cfg, spec_name, variant, reps = args
    sp = uav_specs()[spec_name]
    lang = control_language(sp, max_boxes=int(cfg.get("max_boxes", 5000)))
    tracker = UAVTracker(UAVParams(**cfg.get("uav", {})), TrackerGains(**cfg.get("tracker", {})))
    lc = LCConfig(**cfg.get("langcontrol", {}))
    seed = trial_seed(cfg, 0)
    rng = method_rng(seed, variant, spec_name)
    t0 = time.perf_counter()
    fn = langcontrol_lcw if variant == "LCW" else langcontrol_lcp
    res = fn(lang, tracker.track, rng, reps, lc)
    it = res.iterations
    ok = it > 0
    return {"spec": spec_name, "variant": variant, "paper_text": sp.paper_text, "reps": reps,
            "n_boxes_language": int(lang.n_boxes), "n_processes": res.n_processes,
            "language_repr": type(lang).__name__, "successes": int(ok.sum()), "failures": int((~ok).sum()),
            "P_bar_success": float(it[ok].mean()) if ok.any() else None,
            "P_median_success": float(np.median(it[ok])) if ok.any() else None,
            "P_max_success": int(it[ok].max()) if ok.any() else None,
            "iterations": it.tolist(), "n_tracks": res.n_tracks, "wall_s": time.perf_counter() - t0,
            "M": lc.M, "K": lc.K, "max_processes": lc.max_processes, "seed": seed}


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--reps", type=int, help="override replications (pilot)")
    ap.add_argument("--specs", nargs="*")
    ap.add_argument("--variants", nargs="*", default=None)
    ap.add_argument("--M", type=int)
    ap.add_argument("--K", type=int)
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    cfg = load_config(args.config)
    lc = cfg.setdefault("langcontrol", {})
    if args.M is not None:
        lc["M"] = args.M
    if args.K is not None:
        lc["K"] = args.K
    reps = args.reps or cfg["reps"]
    run = RunDir(cfg["experiment"], args.run_id, {**cfg, "reps": reps})
    done = run.done_keys(("spec", "variant"))
    specs = args.specs or cfg["specs"]
    variants = args.variants or cfg["variants"]
    tasks = [(cfg, s, v, reps) for s in specs for v in variants if (s, v) not in done]
    print(f"{len(tasks)} (spec, variant) runs with {reps} replications each -> {run.path}")
    t0 = time.time()

    def on_result(task, rec):
        run.append(rec)
        print(f"[{time.time() - t0:7.1f}s] {rec['spec']} {rec['variant']}: P_bar={rec['P_bar_success']} "
              f"failures={rec['failures']}/{rec['reps']} boxes={rec['n_boxes_language']} procs={rec['n_processes']} "
              f"tracks={rec['n_tracks']} wall={rec['wall_s']:.1f}s", flush=True)

    run_parallel(_task, tasks, args.workers, on_result)
    run.finish(elapsed_s=round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
