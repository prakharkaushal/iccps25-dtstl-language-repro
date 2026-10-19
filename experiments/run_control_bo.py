"""E6 (paper Sec. 4.3, text only): robustness-based BO baseline for control vs LangControl (LCW).

The paper reports, without data, that "employing BO as the sampling strategy to maximize robustness"
(RTAMT) "consistently requires 3-7x the number of iterations" of LCW. For every objective phi1..phi8 we run
`reps` independent BO replications that search the reference signal maximising RTAMT robustness of the
tracked UAV trajectory (same tracker, domains and iteration unit as E5). Compare with E5's LCW records in
analysis/make_tables.py.

Example: python experiments/run_control_bo.py --config configs/control_bo.yaml --run-id main --workers 10
"""
from __future__ import annotations

import argparse
import time

import common  # noqa: F401
from common import bo_config, load_config, method_rng, run_parallel, trial_seed, utf8_stdout
from langfal import stl
from langfal.control import robustness_bo_control
from langfal.monitors import RtamtMonitor
from langfal.runlog import RunDir
from langfal.specs import uav_specs
from langfal.systems.uav import TrackerGains, UAVParams, UAVTracker

_CACHE = {}


def bounded_formula(sp):
    """phi AND always(x within the signal domain): its robustness is >= 0 exactly when the tracked signal is
    in the domain-bounded language that LangControl's success test uses (checked in tests/test_control.py).
    Plain rho_phi >= 0 would accept trajectories that leave the domain, which LangControl rejects."""
    return stl.conj(sp.formula, stl.always(0, None, stl.between(*sp.domain)))


def _task(args):
    cfg, spec_name, rep = args
    sp = uav_specs()[spec_name]
    if spec_name not in _CACHE:
        _CACHE[spec_name] = RtamtMonitor(bounded_formula(sp))
    tracker = UAVTracker(UAVParams(**cfg.get("uav", {})), TrackerGains(**cfg.get("tracker", {})))
    seed = trial_seed(cfg, rep)
    rec = robustness_bo_control(tracker.track, _CACHE[spec_name], sp.n_samples, sp.domain, bo_config(cfg),
                                method_rng(seed, "BO-CTRL", spec_name))
    rec.update(spec=spec_name, rep=rep, seed=seed, n=sp.n_samples, domain=list(sp.domain))
    return rec


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--reps", type=int)
    ap.add_argument("--specs", nargs="*")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    cfg = load_config(args.config)
    reps = args.reps or cfg["reps"]
    run = RunDir(cfg["experiment"], args.run_id, {**cfg, "reps": reps})
    done = run.done_keys(("spec", "rep"))
    specs = args.specs or cfg["specs"]
    tasks = [(cfg, s, r) for s in specs for r in range(reps) if (s, r) not in done]
    print(f"{len(tasks)} BO replications to do ({len(done)} done) -> {run.path}")
    t0 = time.time()
    n = [0]

    def on_result(task, rec):
        run.append(rec)
        n[0] += 1
        print(f"[{n[0]}/{len(tasks)} {time.time() - t0:7.1f}s] {rec['spec']} rep {rec['rep']:3d} success={rec['success']} "
              f"iterations={rec['iterations']} best_rho={rec['best_rho']:.3f} wall={rec['wall_s']:.1f}s", flush=True)

    run_parallel(_task, tasks, args.workers, on_result)
    run.finish(n_new_records=n[0], elapsed_s=round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
