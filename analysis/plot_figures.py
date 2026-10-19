"""Illustrations corresponding to the paper's Figures 1-4 (ours; the paper's exact projections are unknown).

Figs. 1, 2, 4 show "3D projections" of languages. FindBox's Box.plot3D draws the first three coordinates of each
box as voxels; we do the same with our exact languages (and optionally FindBox boxes): a voxel at integer
coordinates is filled if it lies in the projection of some box onto samples (0, 1, 2).
  fig1: control phi4 (Eq. 17)   fig2: falsification phi5 (Eq. 12), L(phi5) and L(not phi5)
  fig4: control phi1 (Eq. 14) and phi3 (Eq. 16)
Fig. 3 illustrates Algorithm 3 (LCW) on a 2-box language over the samples (x(1), x(2)) of a 3-sample signal
(x(0) = 0 fixed), with our tracker: initial reference (red), tracked points (blue), projections (orange),
final feasible point (green).
Writes results/figures/fig{1,2,3,4}_*.png.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from langfal import stl  # noqa: E402
from langfal.control import control_language  # noqa: E402
from langfal.language import BoxUnion, compile_language  # noqa: E402
from langfal.specs import cc_specs, uav_specs  # noqa: E402
from langfal.systems.uav import UAVTracker  # noqa: E402

OUT = ROOT / "results" / "figures"


def voxels(ax, boxes: BoxUnion, lo, hi, step=1.0, dims=(0, 1, 2), color=(0.1, 0.2, 0.9, 0.75)):
    g = np.arange(lo, hi, step)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    centers = np.stack([X, Y, Z], axis=-1) + step / 2
    filled = np.zeros(X.shape, dtype=bool)
    C = boxes.clipped((lo, hi))
    for k in range(C.j):
        inside = np.ones(X.shape, dtype=bool)
        for a, d in enumerate(dims):
            inside &= (centers[..., a] >= C.lo[k, d]) & (centers[..., a] <= C.hi[k, d])
        filled |= inside
    cols = np.empty(filled.shape + (4,))
    cols[filled] = color
    ax.voxels(filled, facecolors=cols, edgecolor=(0.5, 0.5, 0.5, 0.3), linewidth=0.2)
    ticks = np.linspace(0, len(g), 5)
    for setter in (ax.set_xticks, ax.set_yticks, ax.set_zticks):
        setter(ticks)
    labels = [f"{lo + t * step:.0f}" for t in ticks]
    ax.set_xticklabels(labels); ax.set_yticklabels(labels); ax.set_zticklabels(labels)
    ax.set_xlabel("x(0)"); ax.set_ylabel("x(1)"); ax.set_zlabel("x(2)")


def product_to_union(lang, cap=4096):
    """BoxUnion of (up to `cap`) boxes of a ProductLanguage (projection only needs samples 0..2)."""
    if isinstance(lang, BoxUnion):
        return lang
    if hasattr(lang, "boxes"):
        return lang.boxes
    import itertools
    ivs = lang.intervals
    lo, hi = [], []
    for combo in itertools.islice(itertools.product(*[range(len(i)) for i in ivs[:3]]), cap):
        lo.append([ivs[t][c][0] for t, c in enumerate(combo)] + [ivs[t][0][0] for t in range(3, lang.n)])
        hi.append([ivs[t][c][1] for t, c in enumerate(combo)] + [ivs[t][-1][1] for t in range(3, lang.n)])
    return BoxUnion(np.array(lo), np.array(hi))


def fig_language(name, boxes, lo, hi, title, step=1.0):
    fig = plt.figure(figsize=(5.2, 5))
    ax = fig.add_subplot(111, projection="3d")
    voxels(ax, boxes, lo, hi, step)
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=140)
    plt.close(fig)
    print("wrote", (OUT / name).relative_to(ROOT))


def fig3():
    tr = UAVTracker()
    # two boxes reachable from x(0) = 0 with our tracker (one sample per second)
    boxes = BoxUnion(np.array([[0.0, 1.5, 3.0], [0.0, 2.5, 6.5]]), np.array([[0.0, 3.5, 5.5], [0.0, 4.0, 9.0]]))
    def run(ref):
        pts, kinds = [ref[1:].copy()], ["ref"]
        for _ in range(10):
            x = tr.track(ref[None, :])[0]
            if boxes.contains(x[None, :])[0]:
                pts.append(x[1:]); kinds.append("final")
                break
            pts.append(x[1:]); kinds.append("track")
            ref, _ = boxes.project(x)
            pts.append(ref[1:].copy()); kinds.append("proj")
        return pts, kinds

    # illustration: first seeded random initial reference whose run needs >= 1 projection and then succeeds
    rng = np.random.default_rng(3)
    for _ in range(500):
        pts, kinds = run(np.r_[0.0, rng.uniform(0, 12, size=2)])
        if "proj" in kinds and kinds[-1] == "final":
            break
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    for k in range(boxes.j):
        ax.add_patch(Rectangle((boxes.lo[k, 1], boxes.lo[k, 2]), boxes.hi[k, 1] - boxes.lo[k, 1],
                               boxes.hi[k, 2] - boxes.lo[k, 2], fill=False, edgecolor="blue", lw=2))
    P = np.array(pts)
    ax.plot(P[:, 0], P[:, 1], color="grey", lw=0.8, zorder=1)
    col = {"ref": "red", "track": "royalblue", "proj": "orange", "final": "limegreen"}
    for p, k in zip(pts, kinds):
        ax.scatter(*p, color=col[k], s=55, zorder=2, edgecolor="black", linewidth=0.5)
    ax.set_xlim(0, 12); ax.set_ylim(0, 12); ax.set_xlabel("x(1)"); ax.set_ylabel("x(2)"); ax.grid(alpha=0.3)
    ax.set_title("Algorithm 3 (LCW) in a 2-box language, our tracker\nred: initial reference, blue: tracked, "
                 "orange: projected, green: feasible", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_langcontrol_run.png", dpi=140)
    plt.close(fig)
    print("wrote", (OUT / "fig3_langcontrol_run.png").relative_to(ROOT), "| path kinds:", kinds)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    u = uav_specs()
    fig_language("fig1_control_phi4.png", product_to_union(control_language(u["phi4"])), 0, 20,
                 "L(φ4), Eq. 17 (control), exact; samples 0-2")
    fig_language("fig4a_control_phi1.png", product_to_union(control_language(u["phi1"])), 0, 20,
                 "L(φ1), Eq. 14 (control), exact; samples 0-2")
    fig_language("fig4b_control_phi3.png", product_to_union(control_language(u["phi3"])), 0, 20,
                 "L(φ3), Eq. 16 (control), exact; samples 0-2")
    sp = cc_specs()["phi5"]
    fig_language("fig2_falsification_phi5.png", compile_language(sp.formula, sp.n_samples), 0, 70,
                 "L(φ5), Eq. 12 (falsification), exact; samples 0-2 (t = 0, 10, 20 s)", step=2.0)
    fig_language("fig2b_falsification_not_phi5.png", compile_language(stl.Not(sp.formula), sp.n_samples), 0, 70,
                 "L(¬φ5), Eq. 12 (falsification), exact; samples 0-2", step=2.0)
    fig3()


if __name__ == "__main__":
    main()
