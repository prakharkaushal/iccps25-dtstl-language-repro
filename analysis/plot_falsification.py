"""Figure for E2/E3: per-trial iterations and monitoring time (critical path) per method and requirement.

Usage: python analysis/plot_falsification.py --run-id main   -> results/tables/falsification_<run-id>.png
Each point is one trial ([ours]); unfalsified trials are drawn at the 200-iteration cap with an open marker.
The paper's means ([paper], Tables 2-3) are drawn as short black bars for reference.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis" / "target_paper"))
from langfal.runlog import read_records  # noqa: E402
import paper_reported_values as paper  # noqa: E402

METHODS = ["PROF", "PBO-RTAMT", "SMuRF", "SBO-RTAMT"]
COLORS = {"PROF": "#1f77b4", "PBO-RTAMT": "#aec7e8", "SMuRF": "#d62728", "SBO-RTAMT": "#ff9896"}
PAPER = {**paper.TABLE2, **paper.TABLE3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="main")
    a = ap.parse_args()
    recs = read_records(ROOT / "results" / "raw" / "falsification" / a.run_id)
    specs = sorted({r["spec"] for r in recs})
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    rng = np.random.default_rng(0)
    for ax, key, plabel, title in ((axes[0], "iterations", "S", "Iterations to falsify (log)"),
                                   (axes[1], "T_T_ms", "TT", "Monitoring time per trial, ms (log)")):
        for si, s in enumerate(specs):
            for mi, m in enumerate(METHODS):
                x0 = si * (len(METHODS) + 1) + mi
                rs = [r for r in recs if r["spec"] == s and r["method"] == m]
                if any(str(r.get("stop_reason", "")).startswith("not-applicable") for r in rs):
                    ax.text(x0, 1.0, "n/a", ha="center", va="bottom", fontsize=7, color=COLORS[m], rotation=90)
                rs = [r for r in rs if not str(r.get("stop_reason", "")).startswith("not-applicable")]
                vals = np.array([max(r[key], 0.5) for r in rs])
                ok = np.array([r["falsified"] for r in rs], dtype=bool)
                jit = x0 + rng.uniform(-0.25, 0.25, size=len(vals))
                ax.scatter(jit[ok], vals[ok], s=10, color=COLORS[m], label=m if si == 0 else None)
                ax.scatter(jit[~ok], vals[~ok], s=14, facecolors="none", edgecolors=COLORS[m])
                pv = PAPER[m][plabel][int(s[-1]) - 1]
                ax.hlines(pv, x0 - 0.35, x0 + 0.35, color="black", lw=1.5,
                          label="paper mean" if (si == 0 and mi == 0) else None)
        ax.set_yscale("log")
        ax.set_xticks([si * (len(METHODS) + 1) + 1.5 for si in range(len(specs))])
        ax.set_xticklabels(specs)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=9, frameon=False)
    n = len({r["trial"] for r in recs})
    meta = json.loads((ROOT / "results" / "raw" / "falsification" / a.run_id / "meta.json").read_text())
    lang = meta.get("config", {}).get("language", {"source": "exact"})
    lang_s = "exact L(¬φ)" if lang.get("source", "exact") == "exact" else f"FindBox L(¬φ), variant {lang.get('variant')}"
    fig.suptitle(f"E2/E3 falsification on Chasing Cars ({lang_s}) — ours: {n} trials per cell (run '{a.run_id}')\n"
                 "open markers = not falsified within 200 iterations; S = 0 drawn at 0.5; n/a = empty language",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.07, 1, 0.97))
    out = ROOT / "results" / "tables" / f"falsification_{a.run_id}.png"
    fig.savefig(out, dpi=130)
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
