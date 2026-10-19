"""How good are FindBox's approximations of L(not phi)? (exact language = ground truth)

For every FindBox run/variant and requirement, on the bounded signal space D = [lo, hi]^11 FindBox used:
  * precision: share of FindBox's box volume that is truly in L(not phi) (points uniform in the FindBox
    union, exact membership via robustness < 0),
  * recall: share of L(not phi) within D covered by FindBox's boxes (points uniform in the exact union,
    clipped to D; overlap-corrected rejection sampling),
  * reachable recall: share of the E1 Chasing Cars signals that violate phi (reachable violations) that
    lie inside FindBox's boxes -- falsification by PROF/SMuRF needs these,
  * Table-1-style agreement of the FindBox language monitor (-max_k Dist(x, b_k)) with RTAMT on the 10,000
    E1 signals (the paper's Table 1 was computed with FindBox languages).
Writes results/tables/findbox_quality_<run>.md.

Usage: python analysis/findbox_quality.py --findbox main --e1 main
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis" / "target_paper"))
from langfal import stl  # noqa: E402
from langfal.language import BoxUnion, compile_negated_language  # noqa: E402
from langfal.runlog import read_records  # noqa: E402
from langfal.specs import cc_specs  # noqa: E402
import paper_reported_values as paper  # noqa: E402


def sample_union(U: BoxUnion, lo, hi, m, rng):
    """Uniform samples from the union of boxes clipped to [lo, hi] (volume-weighted + overlap rejection)."""
    C = U.clipped((lo, hi))
    vol = np.prod(np.maximum(C.hi - C.lo, 0), axis=1)
    if C.j == 0 or vol.sum() == 0:
        return np.empty((0, U.n))
    out = []
    while sum(len(o) for o in out) < m:
        k = rng.choice(C.j, size=m, p=vol / vol.sum())
        X = rng.uniform(C.lo[k], C.hi[k])
        cover = ((X[:, None, :] >= C.lo[None]) & (X[:, None, :] <= C.hi[None])).all(axis=2).sum(axis=1)
        out.append(X[rng.uniform(size=m) < 1.0 / np.maximum(cover, 1)])
    return np.vstack(out)[:m]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findbox", default="main")
    ap.add_argument("--e1", default="main")
    ap.add_argument("--m", type=int, default=20000)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    fb_dir = ROOT / "results" / "raw" / "findbox" / a.findbox
    recs = read_records(fb_dir)
    E1 = np.load(ROOT / "results" / "raw" / "e1_monitoring" / a.e1 / "signals.npz")["x"]
    specs = cc_specs()
    names = list(specs)
    L = ["# FindBox approximations of L(¬φ) vs the exact language `[ours]`", "",
         f"FindBox run `{a.findbox}` (results/raw/findbox/{a.findbox}/); E1 signals from run `{a.e1}`; "
         f"{a.m} sample points per estimate (seed 0). Box counts: FindBox [ours] vs paper Table 1 [paper] vs exact "
         "language [ours].", "",
         "| Variant | Req | boxes [ours, FindBox] | boxes [paper] | boxes exact [ours] | samples inside L(¬φ) during build | "
         "precision (volume) | recall in D (volume) | reachable recall (E1 violations covered) | reachable precision "
         "(E1 signals in boxes that violate) | FindBox time (s) | oracle calls |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    agree_rows = []
    for r in sorted(recs, key=lambda r: (r["variant"], r["spec"])):
        sp = specs[r["spec"]]
        lo, hi = r["bounds"]
        fb = BoxUnion.load(fb_dir / f"{r['variant']}_{r['spec']}.json")    # not r["boxes_file"]: absolute path
        ex = compile_negated_language(sp.formula, sp.n_samples)
        f_neg = stl.Not(sp.formula)
        Xfb = sample_union(fb, lo, hi, a.m, rng)
        prec = float(np.mean(stl.robustness(f_neg, Xfb) > 0)) if len(Xfb) else float("nan")
        Xex = sample_union(ex, lo, hi, a.m, rng)
        rec_d = float(np.mean(fb.contains(Xex))) if len(Xex) and fb.j else (0.0 if len(Xex) else float("nan"))
        rho = stl.robustness(sp.formula, E1)
        viol = E1[rho < 0]
        rr = float(np.mean(fb.contains(viol))) if len(viol) and fb.j else (0.0 if len(viol) else float("nan"))
        inside_e1 = fb.contains(E1) if fb.j else np.zeros(len(E1), dtype=bool)
        rp = f"{np.mean(rho[inside_e1] < 0):.3f} ({int(inside_e1.sum())} in boxes)" if inside_e1.any() else "— (0 in boxes)"
        i = names.index(r["spec"])
        L.append(f"| {r['variant']} | {r['spec']} | {fb.j} | {paper.TABLE1['number_of_boxes'][i]} | {ex.j} | "
                 f"{r['samples_inside_language']}/{r['n_samples']} | {prec:.3f} | {rec_d:.3f} | "
                 f"{rr:.3f} ({len(viol)} violations) | {rp} | {r['total_s']:.0f} | {r['oracle_calls_build']} |")
        if fb.j:
            lang = -fb.max_signed_distance(E1)
            same_val = np.abs(lang - rho) <= 1e-9 * (1 + np.abs(rho))
            same_cls = (lang < 0) == (rho < 0)
            agree_rows.append((r["variant"], r["spec"], 100 * same_val.mean(), 100 * (same_cls & ~same_val).mean(),
                               100 * (~same_cls).mean(), i))
        else:
            agree_rows.append((r["variant"], r["spec"], None, None, None, i))
    L += ["", "## Table 1 recomputed with FindBox languages (10,000 E1 signals) `[ours]` vs the paper `[paper]`", "",
          "| Variant | Req | value agreement % [ours] | [paper] | sign-only % [ours] | [paper] | complete disagreement % [ours] | [paper] |",
          "|---|---|---|---|---|---|---|---|"]
    T = paper.TABLE1
    for v, s, va, so, cd, i in agree_rows:
        f = (lambda x: "— (no boxes)" if x is None else f"{x:.2f}")
        L.append(f"| {v} | {s} | {f(va)} | {T['value_agreement_pct'][i]:.2f} | {f(so)} | {T['sign_only_agreement_pct'][i]:.2f} | "
                 f"{f(cd)} | {T['complete_disagreement_pct'][i]:.2f} |")
    L += ["", "Notes: 'complete disagreement' = the FindBox language monitor and RTAMT disagree on whether the signal violates "
          "φ. FindBox samples on the integer grid in the 'default' variant, so violation sets of width < 1 (φ4: 32 < x < 33) "
          "cannot be found there."]
    meta = json.loads((fb_dir / "meta.json").read_text())
    cfg = meta.get("config", {})
    done = {(r["variant"], r["spec"]) for r in recs}
    missing = [f"{v} {s}" for v in cfg.get("variants", {}) for s in cfg.get("specs", []) if (v, s) not in done]
    if missing:
        L.append(f"Missing languages: {', '.join(missing)}"
                 + (f" (see results/raw/findbox/{a.findbox}/INCOMPLETE.md)." if (fb_dir / "INCOMPLETE.md").exists() else "."))
    out = ROOT / "results" / "tables" / f"findbox_quality_{a.findbox}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
