"""Generate FindBox approximations of the falsification languages L(not phi) (paper Sec. 3.2: "For
generating the language, we used the code from [5]").

FindBox is external, unlicensed code used locally at the user's request (src/langfal/findbox_adapter.py).
One task per (spec, variant); outputs results/raw/findbox/<run-id>/<variant>_<spec>.json (boxes) and a
record per task in records.jsonl (box count, sample/inside counts, oracle calls, timings, FindBox's own
over/under-approximation check).

Example: python experiments/run_findbox.py --config configs/findbox.yaml --run-id main --workers 6
"""
from __future__ import annotations

import argparse
import time

import common  # noqa: F401
from common import load_config, run_parallel, utf8_stdout
from langfal import stl
from langfal.findbox_adapter import run_findbox
from langfal.runlog import RunDir
from langfal.specs import cc_specs


def _task(args):
    out_dir, variant, v, spec_name = args
    sp = cc_specs()[spec_name]
    res = run_findbox(stl.Not(sp.formula), sp.n_samples, v["bounds"][0], v["bounds"][1],
                      n_samples=v["n_samples"], seed=v["seed"], sampler=v["sampler"],
                      oracle_impl=v.get("oracle_impl", "scalar"))
    boxes = res.pop("boxes")
    name = f"{variant}_{spec_name}.json"
    boxes.save(f"{out_dir}/{name}")
    res.update(spec=spec_name, variant=variant, boxes_file=name)     # relative to the run directory
    return res


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--variants", nargs="*")
    ap.add_argument("--specs", nargs="*")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    cfg = load_config(args.config)
    run = RunDir(cfg["experiment"], args.run_id, cfg)
    done = run.done_keys(("variant", "spec"))
    variants = args.variants or list(cfg["variants"])
    specs = args.specs or cfg["specs"]
    tasks = [(str(run.path), var, cfg["variants"][var], s) for var in variants for s in specs if (var, s) not in done]
    print(f"{len(tasks)} FindBox runs -> {run.path}")
    t0 = time.time()

    def on_result(task, rec):
        run.append(rec)
        print(f"[{time.time() - t0:7.1f}s] {rec['variant']} {rec['spec']}: boxes={rec['n_boxes']} "
              f"inside={rec['samples_inside_language']}/{rec['n_samples']} oracle_calls={rec['oracle_calls_build']} "
              f"time={rec['total_s']:.0f}s over_bad={rec['check_over_bad_points']}/{rec['check_box_points']} "
              f"under_bad={rec['check_under_bad_points']}/{rec['check_language_points']}", flush=True)

    run_parallel(_task, tasks, args.workers, on_result)
    run.finish(elapsed_s=round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
