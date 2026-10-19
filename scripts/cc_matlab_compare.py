"""Compare the Python Chasing Cars port with the official Simulink model (needs MATLAB + Simulink, see below).

Step 1 (Python):  python scripts/cc_matlab_compare.py export [--n 200] [--seed 99]
    writes results/matlab/cc_inputs.csv (N x 20) and our outputs results/matlab/cc_outputs_python.csv
          python scripts/cc_matlab_compare.py export-falsifiers [--run main]
    writes the falsifying inputs of results/raw/falsification/<run>/ to results/matlab/falsifiers_<run>_inputs.csv
    (+ _index.csv: spec, trial, method, robustness on the port)
Step 2 (MATLAB, after scripts/fetch_cc_model.sh), from target_project/:
    matlab -batch "run('scripts/matlab/run_cc_reference.m')"                                       (ARCH inputs, model tolerances)
    matlab -batch "input_mode='step'; reltol='1e-6'; abstol='1e-6'; out_csv='cc_outputs_simulink_step_tol1e-6.csv'; run('scripts/matlab/run_cc_reference.m')"
    matlab -batch "in_csv='falsifiers_main_inputs.csv'; out_csv='falsifiers_main_simulink.csv'; run('scripts/matlab/run_cc_reference.m')"
    matlab -batch "in_csv='falsifiers_main_inputs.csv'; out_csv='falsifiers_main_simulink_step_tol1e-6.csv'; input_mode='step'; reltol='1e-6'; abstol='1e-6'; run('scripts/matlab/run_cc_reference.m')"
    (setting (c): the same two with reltol='1e-10'; abstol='1e-10'; minstep='auto' and out_csv ..._step_tol1e-10.csv)
Step 3 (Python):  python scripts/cc_matlab_compare.py compare [--run main]
    writes results/tables/cc_port_vs_simulink.md from whichever Simulink outputs exist: position differences per
    car, verdict agreement of phi1..phi5 on x = y5 - y4, an attribution of the lead car's difference (it never
    switches mode, so high-accuracy references can be computed here), and whether the port's falsifiers also
    falsify the Simulink model.

Simulink's variable-step solver uses the model's RelTol 1e-3, and ARCH's input convention turns every input switch
into a 0.01 s ramp; because the follower cars chatter between modes, small differences can grow over 100 s, so
distributions are reported, not only maxima.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from langfal import stl  # noqa: E402
from langfal.runlog import read_records  # noqa: E402
from langfal.specs import cc_specs  # noqa: E402
from langfal.systems.chasing_cars import ChasingCars  # noqa: E402

OUT = ROOT / "results" / "matlab"
TS = np.arange(0, 101, 10.0)
TOL = 1e-6       # robustness within +-TOL of 0 is a boundary case (e.g. gap exactly 10), not a sign flip
# Simulink settings compared with the port: label, description, output file (200 inputs), falsifier output file
SETTINGS = [
    ("a", "ARCH input convention (a 0.01 s ramp at every input switch) and the model's own solver settings "
          "(VariableStepAuto, RelTol 1e-3, AbsTol 1e-5, MinStep 0.01 s): the benchmark as usually run",
     "cc_outputs_simulink.csv", "falsifiers_{run}_simulink.csv"),
    ("b", "exactly piecewise-constant inputs (as the port) and RelTol = AbsTol = 1e-6 requested; the model's MinStep "
          "of 0.01 s limits the accuracy reached at the input switches (Simulink warns; effective tolerances in "
          "results/logs/cc_simulink_*step_tol1e-6.log)",
     "cc_outputs_simulink_step_tol1e-6.csv", "falsifiers_{run}_simulink_step_tol1e-6.csv"),
    ("c", "exactly piecewise-constant inputs, RelTol = AbsTol = 1e-10 and MinStep auto (overriding the model's 0.01 s)",
     "cc_outputs_simulink_step_tol1e-10.csv", "falsifiers_{run}_simulink_step_tol1e-10.csv"),
]


def export(n, seed):
    OUT.mkdir(parents=True, exist_ok=True)
    U = np.random.default_rng(seed).uniform(size=(n, 20))
    sim = ChasingCars()
    Y = np.array([sim.simulate(u).y for u in U])                  # (n, 5, 11)
    np.savetxt(OUT / "cc_inputs.csv", U, delimiter=",", fmt="%.17g")
    np.savetxt(OUT / "cc_outputs_python.csv", Y.reshape(n, -1), delimiter=",", fmt="%.17g")
    print(f"wrote {n} inputs and Python outputs to {OUT.relative_to(ROOT)}")


def export_falsifiers(run_id):
    OUT.mkdir(parents=True, exist_ok=True)
    recs = [r for r in read_records(ROOT / "results" / "raw" / "falsification" / run_id) if r["falsified"]]
    recs.sort(key=lambda r: (r["spec"], r["method"], r["trial"]))
    U = np.array([r["falsifier_u"] for r in recs])
    np.savetxt(OUT / f"falsifiers_{run_id}_inputs.csv", U, delimiter=",", fmt="%.17g")
    with open(OUT / f"falsifiers_{run_id}_index.csv", "w", encoding="utf-8") as f:
        f.write("spec,trial,method,rho_port\n")
        for r in recs:
            f.write(f"{r['spec']},{r['trial']},{r['method']},{r['falsifier_rho']!r}\n")
    print(f"wrote {len(recs)} falsifying inputs of run {run_id} to {OUT.relative_to(ROOT)}")


def _load(name):
    return np.loadtxt(OUT / name, delimiter=",", ndmin=2).reshape(-1, 5, 11)


def _section(title, yp, ys):
    d = np.abs(yp - ys)
    L = [f"## {title}", "", "| car | max abs diff (m) | median | 95th percentile |", "|---|---|---|---|"]
    for c in range(5):
        L.append(f"| {c + 1} | {d[:, c].max():.4g} | {np.median(d[:, c]):.4g} | {np.percentile(d[:, c], 95):.4g} |")
    xp, xs = yp[:, 4] - yp[:, 3], ys[:, 4] - ys[:, 3]
    L += ["", f"| requirement | verdict agreement (violated iff ρ < −{TOL:g}) | boundary cases |ρ| ≤ {TOL:g} "
          "(Python / Simulink) | max abs robustness diff | median |", "|---|---|---|---|---|"]
    for name, sp in cc_specs().items():
        rp, rs = stl.robustness(sp.formula, xp), stl.robustness(sp.formula, xs)
        L.append(f"| {name} | {100 * np.mean((rp < -TOL) == (rs < -TOL)):.2f} % | "
                 f"{int((np.abs(rp) <= TOL).sum())} / {int((np.abs(rs) <= TOL).sum())} | "
                 f"{np.abs(rp - rs).max():.4g} | {np.median(np.abs(rp - rs)):.3g} |")
    return L + [""]


def _lead_reference(u, ramp):
    """High-accuracy y1(t = 0..100) of the lead car (y1' = v1, v1' = -throttle - brake * v1); ramp=True applies
    ARCH's convention ('previous' on a 0.01 s grid, linear in between: a 0.01 s ramp before every switch)."""
    from scipy.integrate import solve_ivp
    th, br = u[:10], u[10:]

    def inp(t, vals):
        k = min(int(np.floor(t / 10 + 1e-12)), 9)
        if ramp and k < 9 and t > 10.0 * (k + 1) - 0.01:
            a = (t - (10.0 * (k + 1) - 0.01)) / 0.01
            return (1 - a) * vals[k] + a * vals[k + 1]
        return vals[k]

    breaks = sorted({0.0, 100.0, *(10.0 * k for k in range(1, 10)),
                     *((10.0 * k - 0.01 for k in range(1, 10)) if ramp else ())})
    z, out = np.zeros(2), {0.0: 0.0}
    for a, b in zip(breaks[:-1], breaks[1:]):
        sol = solve_ivp(lambda t, s: [s[1], -inp(t, th) - inp(t, br) * s[1]], (a, b), z, method="DOP853",
                        rtol=1e-12, atol=1e-12, dense_output=True)
        out.update({float(t): float(sol.sol(t)[0]) for t in TS if a < t <= b})
        z = sol.y[:, -1]
    return np.array([out[float(t)] for t in TS])


def _attribution(U, yp, ys):
    A = np.array([_lead_reference(u, ramp=False) for u in U])
    B = np.array([_lead_reference(u, ramp=True) for u in U])
    L = ["## Lead car: where does the difference come from? `[ours]`", "",
         "Car 1 never switches mode, so its exact trajectory can be computed to high accuracy here (DOP853, "
         "rtol = atol = 1e-12) under both input conventions.", "",
         "| comparison (car 1, all samples) | max abs diff (m) | median | 95th percentile |", "|---|---|---|---|"]
    for name, d in [("port vs exact-step reference (accuracy of the port)", yp[:, 0] - A),
                    ("Simulink (a) vs ARCH-ramp reference (Simulink's integration error at the model's tolerances)",
                     ys[:, 0] - B),
                    ("exact-step vs ARCH-ramp reference (effect of the input convention)", A - B),
                    ("Simulink (a) vs port (observed)", ys[:, 0] - yp[:, 0])]:
        d = np.abs(d)
        L.append(f"| {name} | {d.max():.3g} | {np.median(d):.3g} | {np.percentile(d, 95):.3g} |")
    return L + [""]


def _falsifiers(run_id):
    idx = np.genfromtxt(OUT / f"falsifiers_{run_id}_index.csv", delimiter=",", names=True, dtype=None,
                        encoding="utf-8")
    U = np.loadtxt(OUT / f"falsifiers_{run_id}_inputs.csv", delimiter=",", ndmin=2)
    avail = [(lab, _load(ff.format(run=run_id))) for lab, _, _, ff in SETTINGS if (OUT / ff.format(run=run_id)).exists()]
    sim = ChasingCars()
    specs = cc_specs()
    labs = [lab for lab, _ in avail]
    L = [f"## Do the port's falsifiers falsify the Simulink model? (run `{run_id}`) `[ours]`", "",
         f"Every falsifying input found on the port in `results/raw/falsification/{run_id}/` (Tables 2–3, exact "
         f"language), simulated on Simulink with settings {', '.join(f'({x})' for x in labs)} (defined above); "
         "ρ = robustness of φ on x = y5 − y4 (equals RTAMT).", "",
         "| Req | Method | falsifiers | " + " | ".join(f"also falsify Simulink ({x})" for x in labs) +
         " | median ρ port | " + " | ".join(f"max abs ρ diff ({x})" for x in labs) + " |",
         "|---|---|---|" + "---|" * (2 * len(labs) + 1)]
    rows, tot, ok_tot, misses = {}, 0, {x: 0 for x in labs}, {x: [] for x in labs}
    for i, row in enumerate(idx):
        rows.setdefault((str(row["spec"]), str(row["method"])), []).append(i)
    for (s, m), ii in sorted(rows.items()):
        f = specs[s].formula
        xp = np.array([sim.simulate(U[i]).x for i in ii])
        rp = stl.robustness(f, xp)
        assert np.allclose(rp, idx["rho_port"][ii], atol=1e-9), "port no longer reproduces the stored falsifiers"
        tot += len(ii)
        oks, diffs = [], []
        for x, ys in avail:
            rs = stl.robustness(f, ys[ii, 4] - ys[ii, 3])
            ok = int((rs < 0).sum())
            ok_tot[x] += ok
            misses[x] += [(s, m, int(idx["trial"][i]), float(a), float(b)) for i, a, b in zip(ii, rp, rs) if b >= 0]
            oks.append(f"{ok} ({100 * ok / len(ii):.0f} %)")
            diffs.append(f"{np.abs(rp - rs).max():.3g}")
        L.append(f"| {s} | {m} | {len(ii)} | {' | '.join(oks)} | {np.median(rp):.3g} | {' | '.join(diffs)} |")
    L += ["", "Overall, falsifiers that also falsify the Simulink model: " +
          "; ".join(f"({x}) {ok_tot[x]} of {tot} ({100 * ok_tot[x] / tot:.1f} %)" for x in labs) + "."]
    for x in labs:
        ms = misses[x]
        detail = "".join(f" {s} {m} trial {t}: ρ port {a:.5f}, Simulink {b:.5f}." for s, m, t, a, b in ms)
        if len(ms) == 1:
            L.append(f"- ({x}): 1 falsifier does not carry over.{detail}")
        elif ms:
            rng = [a for *_, a, _ in ms]
            L.append(f"- ({x}): {len(ms)} do not carry over; their robustness on the port is between "
                     f"{min(rng):.3g} and {max(rng):.3g}." + (detail if len(ms) <= 3 else ""))
    return L + [""]


def compare(run_id="main", table_path=None):
    yp = _load("cc_outputs_python.csv")
    U = np.loadtxt(OUT / "cc_inputs.csv", delimiter=",", ndmin=2)
    meta = sorted(p.name for p in OUT.glob("*_meta.txt"))
    L = ["# Python Chasing Cars port vs the official Simulink model `[ours]`", "",
         f"{len(yp)} random inputs (results/matlab/cc_inputs.csv, seed 99), positions y1..y5 at t = 0, 10, …, 100 s. "
         f"MATLAB run details: {', '.join(f'results/matlab/{m}' for m in meta) or '—'}.", "",
         "Simulink settings:"] + [f"- ({lab}) {desc}" for lab, desc, _, _ in SETTINGS] + [""]
    for lab, _, f200, _ in SETTINGS:
        if (OUT / f200).exists():
            L += _section(f"Random inputs, Simulink setting ({lab})", yp, _load(f200))
    L += _attribution(U, yp, _load("cc_outputs_simulink.csv"))
    if (OUT / f"falsifiers_{run_id}_simulink.csv").exists():
        L += _falsifiers(run_id)
    path = table_path or ROOT / "results" / "tables" / "cc_port_vs_simulink.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["export", "export-falsifiers", "compare"])
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=99)
    ap.add_argument("--run", default="main", help="falsification run whose falsifiers are checked")
    a = ap.parse_args()
    if a.step == "export":
        export(a.n, a.seed)
    elif a.step == "export-falsifiers":
        export_falsifiers(a.run)
    else:
        compare(a.run)
