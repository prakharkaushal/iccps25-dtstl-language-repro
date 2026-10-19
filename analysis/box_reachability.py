"""Which boxes of L(not phi) can the Chasing Cars system actually reach? (explains PROF's E2 behaviour)

For each requirement: number of boxes j of the exact language L(not phi); number of boxes entered by at
least one of the E1 signals (10,000 uniform inputs, results/raw/e1_monitoring/<e1-run>/signals.npz);
how often each box was the falsifying box of a PROF trial (results/raw/falsification/<run>) and how many
boxes were never falsified by modified PROF (results/raw/table4/<run>, if present).
Writes results/tables/box_reachability_<run>.md.

Usage: python analysis/box_reachability.py --e1 main --falsification main [--table4 pilot]
"""
import argparse
import collections
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from langfal.language import compile_negated_language  # noqa: E402
from langfal.runlog import read_records  # noqa: E402
from langfal.specs import cc_specs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", default="main")
    ap.add_argument("--falsification", default="main")
    ap.add_argument("--table4")
    a = ap.parse_args()
    X = np.load(ROOT / "results" / "raw" / "e1_monitoring" / a.e1 / "signals.npz")["x"]
    fal = read_records(ROOT / "results" / "raw" / "falsification" / a.falsification)
    t4 = read_records(ROOT / "results" / "raw" / "table4" / a.table4) if a.table4 else []
    lines = ["# Reachability of the boxes of L(¬φ) on the Chasing Cars model `[ours]`", "",
             f"Signals: {len(X)} uniform inputs from E1 run `{a.e1}`; PROF falsifiers from run `{a.falsification}`"
             + (f"; modified PROF from run `{a.table4}`" if a.table4 else "") + ".", "",
             "| Req | boxes j | boxes entered by ≥1 random signal | PROF falsified trials | distinct falsifying boxes (PROF) | "
             "falsifying box → trials | PBO-RTAMT falsified trials | never falsified by modified PROF (mean) |",
             "|---|---|---|---|---|---|---|---|"]
    for name, sp in cc_specs().items():
        neg = compile_negated_language(sp.formula, sp.n_samples)
        D = neg.signed_distance(X)                       # (N, j)
        entered = (D > 0).any(axis=0)
        prof = [r for r in fal if r["spec"] == name and r["method"] == "PROF"]
        pbo = [r for r in fal if r["spec"] == name and r["method"] == "PBO-RTAMT"]
        boxes = collections.Counter(r["falsifier_box"] for r in prof if r["falsified"])
        never = [len(r["never_falsified_boxes"]) for r in t4 if r["spec"] == name and r["method"] == "PROF-all"]
        lines.append(f"| {name} | {neg.j} | {int(entered.sum())} (indices {np.flatnonzero(entered).tolist()}) | "
                     f"{sum(r['falsified'] for r in prof)}/{len(prof)} | {len(boxes)} | "
                     f"{dict(sorted(boxes.items()))} | {sum(r['falsified'] for r in pbo)}/{len(pbo)} | "
                     f"{np.mean(never) if never else '—'} |")
    lines += ["", "Reading: a PROF process is tied to one box; processes on boxes that the system cannot enter "
              "(e.g. φ1's box 'x(0) > 40' while x(0) = 10 always) cannot succeed, whereas every PBO-RTAMT process "
              "optimises the full robustness. The paper's FindBox languages had different (fewer for φ1, φ2, φ4) boxes."]
    out = ROOT / "results" / "tables" / f"box_reachability_{a.falsification}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
