"""Phase 4 reproducibility audit: every check is recomputed from raw outputs, independently of make_tables.py.

  A. claims    every headline number quoted in README.md / PROGRESS.md, recomputed from results/raw/ and
               results/matlab/ with fresh code, compared with the quoted (rounded) value
  B. data      falsifiers re-simulated (they must reproduce falsifier_x and violate phi); E1 signals re-simulated
               and E1 metrics recomputed from the stored signals; internal consistency of control records
  C. configs   config stored in each run's meta.json vs the current configs/*.yaml
  D. reruns    audit re-runs (run id `audit_rerun`, current code) vs the stored runs, field by field
  E. tables    tables regenerated from the raw records vs the stored results/tables/*.md
  F. censoring success-conditional means (paper's S-bar, P-bar) vs restricted means that count failures at the cap

Writes results/tables/audit.md. Usage: python analysis/audit.py
"""
import difflib
import json
import sys
from pathlib import Path

import numpy as np
import scipy.stats
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))
from langfal import stl  # noqa: E402
from langfal.language import compile_negated_language  # noqa: E402
from langfal.runlog import read_records  # noqa: E402
from langfal.specs import cc_specs  # noqa: E402
from langfal.systems.chasing_cars import ChasingCars  # noqa: E402

RAW = ROOT / "results" / "raw"
MAT = ROOT / "results" / "matlab"
REQS = ["phi1", "phi2", "phi3", "phi4", "phi5"]
CHECKS = []          # (section, id, what, claimed, recomputed, ok, source)


def check(sec, cid, what, claimed, value, ok, source):
    CHECKS.append((sec, cid, what, claimed, value, bool(ok), source))


def recs(exp, run):
    return read_records(RAW / exp / run)


def gmean(v):
    v = [x for x in v if x is not None]
    return float(np.exp(np.mean(np.log(v)))) if v else float("nan")


def r(x, nd):
    return round(float(x), nd)


# ------------------------------------------------------------------ A. claims
def claims_e1():
    E = {x["spec"]: x for x in recs("e1_monitoring", "main")}
    src = "results/raw/e1_monitoring/main"
    check("A", "E1-1", "value agreement language monitor vs RTAMT, all φ", "100 %",
          [E[s]["value_agreement_pct"] for s in REQS], all(E[s]["value_agreement_pct"] == 100 for s in REQS), src)
    sp = [E[s]["rtamt_discrete_ms"] / E[s]["language_ms"] for s in REQS]
    check("A", "E1-2", "per-call speedup RTAMT/language, range", "1.1–2.0×", f"{min(sp):.2f}–{max(sp):.2f}",
          r(min(sp), 1) == 1.1 and r(max(sp), 1) == 2.0, src)
    t11 = [E[s]["rtamt_discrete_ms"] for s in REQS]
    check("A", "E1-3", "RTAMT ms/call, 11-sample traces, range", "0.09–0.20", f"{min(t11):.3f}–{max(t11):.3f}",
          r(min(t11), 2) == 0.09 and r(max(t11), 2) == 0.20, src)
    t101 = [E[s]["rtamt_discrete_1s_grid_ms"] for s in REQS]
    check("A", "E1-4", "RTAMT ms/call, 101-sample traces, range (corrected in Phase 5; was 0.41–1.08)", "0.53–1.00",
          f"{min(t101):.3f}–{max(t101):.3f}", r(min(t101), 2) == 0.53 and r(max(t101), 2) == 1.00, src)
    v = [E[s]["violating_pct"] for s in REQS]
    check("A", "E1-5", "violation rate %, φ1–φ5", "0.70/0.84/4.23/0.85/0.52", "/".join(f"{x:.2f}" for x in v),
          [r(x, 2) for x in v] == [0.70, 0.84, 4.23, 0.85, 0.52], src)


def _by(R, m, s):
    return sorted([x for x in R if x["method"] == m and x["spec"] == s], key=lambda x: x["trial"])


def _fals_ratios(R, base, ours, key):
    out = []
    for s in REQS:
        a = [x[key] for x in _by(R, base, s) if x["falsified"]]
        b = [x[key] for x in _by(R, ours, s) if x["falsified"]]
        out.append(np.mean(a) / np.mean(b) if a and b and np.mean(b) > 0 and np.mean(a) > 0 else None)
    return out


def _wilcoxon(R, base, ours, s):
    a = [x["iterations"] for x in _by(R, base, s)]
    b = [x["iterations"] for x in _by(R, ours, s)]
    if np.allclose(a, b):
        return float("nan")
    return float(scipy.stats.wilcoxon(a, b).pvalue)


def claims_e23():
    R = recs("falsification", "main")
    src = "results/raw/falsification/main"
    fr = {m: sum(x["falsified"] for x in R if x["method"] == m) for m in ("PROF", "PBO-RTAMT", "SMuRF", "SBO-RTAMT")}
    check("A", "E23-1", "falsified trials /100: PROF, PBO, SMuRF, SBO", "77/97/79/85",
          "/".join(str(fr[m]) for m in ("PROF", "PBO-RTAMT", "SMuRF", "SBO-RTAMT")),
          [fr[m] for m in ("PROF", "PBO-RTAMT", "SMuRF", "SBO-RTAMT")] == [77, 97, 79, 85], src)
    tt1, tt2 = gmean(_fals_ratios(R, "PBO-RTAMT", "PROF", "T_T_ms")), gmean(_fals_ratios(R, "SBO-RTAMT", "SMuRF", "T_T_ms"))
    check("A", "E23-2", "T̄_T geomean ratio PBO/PROF, SBO/SMuRF", "2.7 / 2.3", f"{tt1:.2f} / {tt2:.2f}",
          r(tt1, 1) == 2.7 and r(tt2, 1) == 2.3, src)
    s1, s2 = gmean(_fals_ratios(R, "PBO-RTAMT", "PROF", "iterations")), gmean(_fals_ratios(R, "SBO-RTAMT", "SMuRF", "iterations"))
    check("A", "E23-3", "S̄ geomean ratio PBO/PROF, SBO/SMuRF", "0.47 / 1.23", f"{s1:.3f} / {s2:.3f}",
          r(s1, 2) == 0.47 and r(s2, 2) == 1.23, src)
    p_sm = [_wilcoxon(R, "SBO-RTAMT", "SMuRF", s) for s in REQS]
    check("A", "E23-4", "Wilcoxon SBO vs SMuRF: only φ4 < 0.05, p = 0.017", "φ4 only, 0.017",
          "/".join(f"{p:.3f}" for p in p_sm), [p < 0.05 for p in p_sm] == [False, False, False, True, False]
          and r(p_sm[3], 3) == 0.017, src)
    p_pr = [_wilcoxon(R, "PBO-RTAMT", "PROF", s) for s in REQS]
    check("A", "E23-5", "Wilcoxon PBO vs PROF: < 0.05 for φ1, φ4, φ5", "φ1, φ4, φ5",
          "/".join(f"{p:.3f}" for p in p_pr), [p < 0.05 for p in p_pr] == [True, False, False, True, True], src)
    init = {m: {(x["spec"], x["trial"]) for x in R if x["method"] == m and x["falsified"] and x["iterations"] == 0}
            for m in ("PROF", "PBO-RTAMT", "SMuRF", "SBO-RTAMT")}
    same = len(set.intersection(*init.values()))
    check("A", "E23-6", "trials falsified by an initial sample, identical for all 4 methods", "9 (same 9)",
          f"{[len(v) for v in init.values()]}, common {same}",
          same == 9 and all(len(v) == 9 for v in init.values()), src)
    boxes = sorted({x["falsifier_box"] for x in _by(R, "PROF", "phi1") if x["falsified"]})
    n1 = sum(x["falsified"] for x in _by(R, "PROF", "phi1"))
    check("A", "E23-7", "PROF φ1: 9 falsifications, all in box index 3 (0-based: x(3) > 40)", "9, box 3",
          f"{n1}, boxes {boxes}", n1 == 9 and boxes == [3], src)
    E1 = np.load(RAW / "e1_monitoring" / "main" / "signals.npz")["x"]
    neg = compile_negated_language(cc_specs()["phi1"].formula, 11)
    inside = [int(((E1 >= neg.lo[k]) & (E1 <= neg.hi[k])).all(axis=1).sum()) for k in range(neg.j)]
    reach = sum(1 for c in inside if c > 0)
    check("A", "E23-8", "φ1: boxes of L(¬φ1) entered by the 10,000 E1 signals", "2 of 11", f"{reach} of {neg.j} {inside}",
          reach == 2 and neg.j == 11, "results/raw/e1_monitoring/main/signals.npz")
    rm = [gmean([np.mean([x["iterations"] for x in _by(R, b, s)]) / np.mean([x["iterations"] for x in _by(R, o, s)])
                 for s in REQS]) for b, o in (("PBO-RTAMT", "PROF"), ("SBO-RTAMT", "SMuRF"))]
    check("A", "E23-9", "S̄ ratio with unfalsified trials at 200: PBO/PROF, SBO/SMuRF", "0.34 / 1.03",
          f"{rm[0]:.3f} / {rm[1]:.3f}", r(rm[0], 2) == 0.34 and r(rm[1], 2) == 1.03, src)


def claims_e4():
    T = recs("table4", "main")
    F = {(x["spec"], x["trial"]): x for x in recs("falsification", "main") if x["method"] == "PROF"}
    src = "results/raw/table4/main"
    pa = [x for x in T if x["method"] == "PROF-all"]
    matched = [x for x in pa if F[(x["spec"], x["trial"])]["falsified"]]
    eq = sum(x["S_min"] == F[(x["spec"], x["trial"])]["iterations"] for x in matched)
    check("A", "E4-1", "modified PROF S_min = PROF S (matched falsified trials)", "77/77", f"{eq}/{len(matched)}",
          eq == len(matched) == 77, src + " + falsification/main")
    smax = [np.mean([x["S_max"] for x in pa if x["spec"] == s]) for s in REQS]
    check("A", "E4-2", "S̄_max, φ1–φ5", "200 everywhere", smax, all(v == 200 for v in smax), src)
    nf = [np.mean([len(x["never_falsified_boxes"]) for x in pa if x["spec"] == s]) for s in REQS]
    check("A", "E4-3", "mean never-falsified boxes", "10.5/6.7/22.5/22.4/5.75", "/".join(f"{v:.2f}" for v in nf),
          [r(nf[0], 1), r(nf[1], 1), r(nf[2], 1), r(nf[3], 1), r(nf[4], 2)] == [10.5, 6.7, 22.5, 22.4, 5.75], src)
    sq = [x for x in T if x["method"] == "SEQ-BO"]
    fr = [sum(x["falsified"] for x in sq if x["spec"] == s) for s in REQS]
    sb = [np.mean([x["iterations"] for x in sq if x["spec"] == s and x["falsified"]]) for s in REQS]
    check("A", "E4-4", "SEQ-BO falsified /20 and S̄ range", "8/17/20/20/14, 594–1,113",
          f"{'/'.join(map(str, fr))}, {min(sb):.0f}–{max(sb):.0f}",
          fr == [8, 17, 20, 20, 14] and round(min(sb)) == 594 and round(max(sb)) == 1113, src)


def claims_e5():
    C = {(x["spec"], x["variant"]): x for x in recs("control", "main")}
    src = "results/raw/control/main"
    pw = [np.mean([v for v in C[(f"phi{i}", "LCW")]["iterations"] if v > 0]) for i in range(1, 9)]
    pp = [np.mean([v for v in C[(f"phi{i}", "LCP")]["iterations"] if v > 0]) for i in range(1, 9)]
    rat = [a / b for a, b in zip(pw, pp)]
    check("A", "E5-1", "LCP P̄ < LCW P̄ on all 8 objectives", "8/8", f"{sum(b < a for a, b in zip(pw, pp))}/8",
          all(b < a for a, b in zip(pw, pp)), src)
    check("A", "E5-2", "LCW/LCP ratio range", "1.0–70", f"{min(rat):.2f}–{max(rat):.1f}",
          r(min(rat), 1) == 1.0 and round(max(rat)) == 70, src)
    fw = [C[(f"phi{i}", "LCW")]["failures"] for i in range(1, 9)]
    check("A", "E5-3", "LCW failures φ5, φ8 (others 0)", "786, 3", fw,
          fw[4] == 786 and fw[7] == 3 and sum(fw) == 789, src)
    check("A", "E5-4", "LCW P̄ φ1, φ8", "56.6, 950", f"{pw[0]:.2f}, {pw[7]:.1f}", r(pw[0], 1) == 56.6 and round(pw[7]) == 950, src)
    more = sum(C[(f"phi{i}", "LCP")]["n_tracks"] > C[(f"phi{i}", "LCW")]["n_tracks"] for i in range(1, 9))
    check("A", "E5-5", "LCP uses more total Track calls than LCW (same 1000 replications)", "5 of 8", f"{more} of 8",
          more == 5, src)
    for i in range(1, 9):     # internal consistency of the stored summary fields
        for v in ("LCW", "LCP"):
            x = C[(f"phi{i}", v)]
            it = np.array(x["iterations"])
            ok = (len(it) == x["reps"] == 1000 and int((it < 0).sum()) == x["failures"]
                  and int((it > 0).sum()) == x["successes"]
                  and (x["successes"] == 0 or np.isclose(it[it > 0].mean(), x["P_bar_success"])))
            if not ok:
                check("B", f"E5-c-{i}{v}", "control record consistency", "consistent", "inconsistent", False, src)
    check("B", "E5-c", "control records: failures/successes/P̄ match the per-replication iterations (16 records)",
          "consistent", "checked", all(c[5] for c in CHECKS if c[1].startswith("E5-c-")), src)


def claims_e6():
    B = recs("control_bo", "main")
    W = {x["spec"]: np.array(x["iterations"]) for x in recs("control", "main") if x["variant"] == "LCW"}
    budget = 205
    src = "results/raw/control_bo/main + control/main"
    ratios, ratios5, fewer, rows = [], [], 0, {}
    for i in range(1, 9):
        s = f"phi{i}"
        ok = [x["iterations"] for x in B if x["spec"] == s and x["success"]]
        w = W[s][(W[s] > 0) & (W[s] <= budget)]
        rat = np.mean(ok) / np.mean(w) if ok and len(w) else None
        rows[s] = (len(ok) / 50, len(w) / len(W[s]), rat)
        if rat is not None:
            ratios.append(rat)
            fewer += rat < 1
            if len(ok) >= 5 and len(w) >= 5:
                ratios5.append(rat)
    g, g5 = gmean(ratios), gmean(ratios5)
    check("A", "E6-1", "BO/LCW geomean ratio (all 8; ≥5 successes each)", "0.52 (8), 0.53 (7)",
          f"{g:.3f} ({len(ratios)}), {g5:.3f} ({len(ratios5)})",
          r(g, 2) == 0.52 and r(g5, 2) == 0.53 and len(ratios) == 8 and len(ratios5) == 7, src)
    check("A", "E6-2", "BO needs fewer iterations than LCW", "6 of 8", f"{fewer} of {len(ratios)}", fewer == 6, src)
    check("A", "E6-3", "φ1 ratio; φ6 success BO vs LCW (≤ 205 calls)", "1.21; 2 % vs 30.8 %",
          f"{rows['phi1'][2]:.2f}; {100 * rows['phi6'][0]:.0f} % vs {100 * rows['phi6'][1]:.1f} %",
          r(rows["phi1"][2], 2) == 1.21 and round(100 * rows["phi6"][0]) == 2 and r(100 * rows["phi6"][1], 1) == 30.8, src)
    return rows


def claims_findbox():
    D, Bf, M = recs("falsification", "findbox_default"), recs("falsification", "findbox_besteffort"), recs("falsification", "main")
    def frs(R, m, ss):
        return [sum(x["falsified"] for x in _by(R, m, s)) for s in ss]
    s4 = ["phi1", "phi2", "phi3", "phi5"]
    got = {m: frs(D, m, s4) for m in ("PROF", "SMuRF", "PBO-RTAMT", "SBO-RTAMT")}
    want = {"PROF": [0, 0, 20, 0], "SMuRF": [1, 0, 20, 0], "PBO-RTAMT": [19, 15, 20, 11], "SBO-RTAMT": [20, 15, 20, 11]}
    check("A", "FB-1", "FindBox default: falsified /20 on φ1, φ2, φ3, φ5", str(want), str(got), got == want,
          "results/raw/falsification/findbox_default")
    na = sum(1 for x in D if x["spec"] == "phi4" and str(x["stop_reason"]).startswith("not-applicable"))
    sbo4 = sum(x["falsified"] for x in _by(D, "SBO-RTAMT", "phi4"))
    check("A", "FB-2", "FindBox default φ4: language methods n/a (60 runs), SBO 19/20", "60, 19", f"{na}, {sbo4}",
          na == 60 and sbo4 == 19, "results/raw/falsification/findbox_default")
    rej = {m: sum(x["validation_calls"] - (1 if x["falsified"] else 0) for x in _by(D, m, "phi1")) for m in ("PROF", "SMuRF")}
    check("A", "FB-3", "FindBox default φ1: RTAMT-rejected claims PROF, SMuRF", "4020, 4040",
          f"{rej['PROF']}, {rej['SMuRF']} (PROF: 0 falsified → exact)", rej == {"PROF": 4020, "SMuRF": 4040},
          "results/raw/falsification/findbox_default")
    s3 = ["phi2", "phi3", "phi4", "phi5"]
    got = {m: frs(Bf, m, s3) for m in ("PROF", "SMuRF", "PBO-RTAMT", "SBO-RTAMT")}
    want = {"PROF": [14, 15, 20, 13], "SMuRF": [6, 9, 20, 8], "PBO-RTAMT": [19, 20, 20, 17], "SBO-RTAMT": [15, 20, 19, 11]}
    rj = sum(x.get("validation_rejections", 0) for x in Bf if x["spec"] in s3)
    check("A", "FB-4", "FindBox best-effort: falsified /20 on φ2, φ3, φ4, φ5; rejected claims", f"{want}; 0",
          f"{got}; {rj}", got == want and rj == 0, "results/raw/falsification/findbox_besteffort")
    mm = {(x["spec"], x["trial"]): x for x in M if x["method"] == "SBO-RTAMT"}
    for name, R, n in (("default", D, 100), ("best-effort", Bf, None)):
        sb = [x for x in R if x["method"] == "SBO-RTAMT"]
        same = sum(x["iterations"] == mm[(x["spec"], x["trial"])]["iterations"]
                   and x.get("falsifier_u") == mm[(x["spec"], x["trial"])].get("falsifier_u") for x in sb)
        check("A", f"FB-5{name[0]}", f"SBO-RTAMT ({name}) identical to falsification/main", f"all {len(sb)}",
              f"{same}/{len(sb)}", same == len(sb) and (n is None or len(sb) == n), "falsification runs")
    FB = {(x["variant"], x["spec"]): x["n_boxes"] for x in recs("findbox", "main")}
    got = [FB.get(("default", s)) for s in REQS]
    check("A", "FB-6", "FindBox default box counts φ1–φ5", "3/1/54/0/1", got, got == [3, 1, 54, 0, 1],
          "results/raw/findbox/main")
    got = [FB.get(("besteffort", s)) for s in REQS]
    check("A", "FB-7", "FindBox best-effort box counts φ1–φ5 (φ1 stopped, INCOMPLETE.md)", "—/5/108/53/5", got,
          got == [None, 5, 108, 53, 5],
          "results/raw/findbox/main")


def claims_findbox_quality():
    from langfal.language import BoxUnion
    E1 = np.load(RAW / "e1_monitoring" / "main" / "signals.npz")["x"]
    f = cc_specs()["phi3"].formula
    viol = E1[stl.robustness(f, E1) < 0]
    B = BoxUnion.load(RAW / "findbox" / "main" / "besteffort_phi3.json")
    rec = float(np.mean(B.contains(viol)))
    check("A", "FB-8", "best-effort φ3 FindBox boxes cover this share of the reachable (E1) violations", "17 %",
          f"{100 * rec:.1f} % ({int(B.contains(viol).sum())} of {len(viol)})", round(100 * rec) == 17,
          "results/raw/findbox/main + e1_monitoring/main")


def claims_cc():
    def load(n):
        return np.loadtxt(MAT / n, delimiter=",", ndmin=2).reshape(-1, 5, 11)
    yp = load("cc_outputs_python.csv")
    sp = cc_specs()
    src = "results/matlab/*.csv"
    for lab, f, claim_pos, claim_rho in (("a", "cc_outputs_simulink.csv", 1.5, 1.04),
                                         ("c", "cc_outputs_simulink_step_tol1e-10.csv", 6.7e-7, 1.1e-6)):
        ys = load(f)
        d = np.abs(yp - ys)
        xp, xs = yp[:, 4] - yp[:, 3], ys[:, 4] - ys[:, 3]
        agree, rho_d = [], []
        for s in REQS:
            a, b = stl.robustness(sp[s].formula, xp), stl.robustness(sp[s].formula, xs)
            agree.append(np.mean((a < -1e-6) == (b < -1e-6)))
            rho_d.append(np.abs(a - b).max())
        check("A", f"CC-{lab}", f"Simulink setting ({lab}): verdict agreement; max |Δy|; max |Δρ|",
              f"100 %; ≤ {claim_pos:g}; ≤ {claim_rho:g}", f"{100 * min(agree):.1f} %; {d.max():.3g}; {max(rho_d):.3g}",
              min(agree) == 1.0 and float(f"{d.max():.2g}") <= claim_pos * 1.02 and float(f"{max(rho_d):.2g}") <= claim_rho * 1.02,
              src)
    idx = np.genfromtxt(MAT / "falsifiers_main_index.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    counts, maxd = {}, None
    for lab, f in (("a", "falsifiers_main_simulink.csv"), ("b", "falsifiers_main_simulink_step_tol1e-6.csv"),
                   ("c", "falsifiers_main_simulink_step_tol1e-10.csv")):
        ys = load(f)
        rs = np.array([stl.robustness(sp[str(s)].formula, (ys[i, 4] - ys[i, 3])[None])[0] for i, s in enumerate(idx["spec"])])
        counts[lab] = int((rs < 0).sum())
        if lab == "c":
            maxd = float(np.abs(rs - idx["rho_port"]).max())
    check("A", "CC-f", "falsifiers that falsify Simulink (a)/(b)/(c); max |Δρ| (c)", "322/337/338 of 338; ≤ 7.2e-7",
          f"{counts['a']}/{counts['b']}/{counts['c']} of {len(idx)}; {maxd:.2g}",
          counts == {"a": 322, "b": 337, "c": 338} and len(idx) == 338 and maxd <= 7.2e-7 * 1.02, src)


# ------------------------------------------------------------------ B. data integrity
def data_checks():
    sim = ChasingCars()
    sp = cc_specs()
    for exp, run in (("falsification", "main"), ("table4", "main"), ("falsification", "findbox_default"),
                     ("falsification", "findbox_besteffort")):
        R = [x for x in recs(exp, run) if x["falsified"]]
        bad_x = bad_rho = 0
        for x in R:
            sig = sim.simulate(np.array(x["falsifier_u"])).x
            bad_x += not np.allclose(sig, x["falsifier_x"], atol=1e-9)
            rho = stl.robustness(sp[x["spec"]].formula, sig[None])[0]
            bad_rho += not (rho < 0 and abs(rho - x["falsifier_rho"]) < 1e-9)
        check("B", f"D-{exp}-{run}", f"{exp}/{run}: every stored falsifier re-simulated reproduces falsifier_x and "
              "violates φ with the stored ρ", f"{len(R)} falsifiers", f"{bad_x} x-mismatches, {bad_rho} ρ-mismatches",
              bad_x == 0 and bad_rho == 0, f"results/raw/{exp}/{run}")
    Z = np.load(RAW / "e1_monitoring" / "main" / "signals.npz")
    U, X = Z["inputs"], Z["x"]
    pick = np.random.default_rng(0).choice(len(U), 300, replace=False)
    err = max(np.abs(sim.simulate(U[i]).x - X[i]).max() for i in pick)
    U7 = np.random.default_rng(7).uniform(size=U.shape)
    check("B", "D-e1-sig", "E1 signals: stored inputs = seed-7 uniform draws; 300 random rows re-simulated",
          "identical", f"inputs equal: {np.array_equal(U7, U)}; max |Δx| = {err:.2g}", np.array_equal(U7, U) and err < 1e-9,
          "results/raw/e1_monitoring/main/signals.npz")
    E = {x["spec"]: x for x in recs("e1_monitoring", "main")}
    worst = 0.0
    for s in REQS:
        rho = stl.robustness(sp[s].formula, X)
        neg = compile_negated_language(sp[s].formula, 11)
        lang = -neg.max_signed_distance(X)
        same = np.abs(lang - rho) <= 1e-9 * (1 + np.abs(rho))
        worst = max(worst, abs(100 * (rho < 0).mean() - E[s]["violating_pct"]), abs(100 * same.mean() - E[s]["value_agreement_pct"]))
    check("B", "D-e1-met", "E1 violation and agreement percentages recomputed from the stored signals",
          "equal to records", f"max abs difference {worst:.2g} percentage points", worst < 1e-9,
          "results/raw/e1_monitoring/main")


# ------------------------------------------------------------------ C. configs
def config_checks():
    pairs = [("e1_monitoring", "main", "e1_monitoring.yaml"), ("falsification", "main", "falsification.yaml"),
             ("table4", "main", "table4.yaml"), ("control", "main", "control.yaml"),
             ("control_bo", "main", "control_bo.yaml"), ("findbox", "main", "findbox.yaml"),
             ("falsification", "findbox_default", "falsification_findbox_default.yaml"),
             ("falsification", "findbox_besteffort", "falsification_findbox_besteffort.yaml")]
    for exp, run, yml in pairs:
        stored = json.loads((RAW / exp / run / "meta.json").read_text())["config"]
        cur = yaml.safe_load((ROOT / "configs" / yml).read_text(encoding="utf-8"))
        diff = sorted(k for k in set(stored) | set(cur) if stored.get(k) != cur.get(k))
        check("C", f"CFG-{exp}-{run}", f"meta.json config of {exp}/{run} = configs/{yml}", "identical",
              "identical" if not diff else f"differs in {diff}", not diff, f"results/raw/{exp}/{run}/meta.json")


# ------------------------------------------------------------------ D. re-runs
def rerun_checks():
    def cmp_fals(exp, keys):
        A = {(x["spec"], x["trial"], x["method"]): x for x in recs(exp, "audit_rerun")}
        Mn = {(x["spec"], x["trial"], x["method"]): x for x in recs(exp, "main")}
        bad = [k for k, x in A.items() if any(x.get(f) != Mn[k].get(f) for f in keys)]
        check("D", f"RR-{exp}", f"{exp}: audit re-run (current code) vs main, fields {keys}",
              "identical", f"{len(A) - len(bad)}/{len(A)} identical" + (f"; differ: {bad[:4]}" if bad else ""),
              not bad and len(A) > 0, f"results/raw/{exp}/audit_rerun")
    if (RAW / "falsification" / "audit_rerun" / "records.jsonl").exists():
        cmp_fals("falsification", ["falsified", "iterations", "n_sims", "falsifier_u", "falsifier_rho", "stop_reason",
                                   "validation_calls"])
    if (RAW / "table4" / "audit_rerun" / "records.jsonl").exists():
        cmp_fals("table4", ["falsified", "iterations", "n_sims", "falsifier_u", "box_order", "boxes_tried",
                            "per_box_iterations", "S_min", "S_max"])
    P = {(x["spec"], x["trial"], x["method"]): x for x in recs("falsification", "pilot")}
    Mn = {(x["spec"], x["trial"], x["method"]): x for x in recs("falsification", "main")}
    same = sum(all(P[k][f] == Mn[k][f] for f in ("falsified", "iterations", "n_sims")) for k in P)
    check("D", "RR-pilot", "falsification pilot (older code, hash 437ea1b) vs main trial 0 (hash 43806db)",
          "identical", f"{same}/{len(P)}", same == len(P), "results/raw/falsification/pilot")
    if (RAW / "falsification" / "final_check" / "records.jsonl").exists():
        A = {(x["spec"], x["trial"], x["method"]): x for x in recs("falsification", "final_check")}
        keys = ["falsified", "iterations", "n_sims", "falsifier_u", "falsifier_rho", "stop_reason", "validation_calls"]
        bad = [k for k, x in A.items() if any(x.get(f) != Mn[k].get(f) for f in keys)]
        check("D", "RR-final", "after the Phase 5 refactor (current src hash): falsification re-run vs main",
              "identical", f"{len(A) - len(bad)}/{len(A)} identical", not bad and len(A) > 0,
              "results/raw/falsification/final_check")
    if (RAW / "control" / "final_check" / "records.jsonl").exists():
        A = {(x["spec"], x["variant"]): x for x in recs("control", "final_check")}
        Cm = {(x["spec"], x["variant"]): x for x in recs("control", "main")}
        bad = [k for k in A if A[k]["iterations"] != Cm[k]["iterations"]]
        check("D", "RR-final-control", "after the Phase 5 refactor: control re-run vs main", "identical",
              f"{len(A) - len(bad)}/{len(A)} identical", not bad and len(A) > 0, "results/raw/control/final_check")
    if (RAW / "e1_monitoring" / "audit_rerun" / "records.jsonl").exists():
        A = {x["spec"]: x for x in recs("e1_monitoring", "audit_rerun")}
        E = {x["spec"]: x for x in recs("e1_monitoring", "main")}
        keys = ["n_boxes_neg", "value_agreement_pct", "sign_only_agreement_pct", "complete_disagreement_pct",
                "satisfying_pct", "violating_pct", "rho_zero_pct", "ours_vs_rtamt_max_abs_diff"]
        bad = [(s, k) for s in A for k in keys if A[s][k] != E[s][k]]
        Zr = np.load(RAW / "e1_monitoring" / "audit_rerun" / "signals.npz")
        Zm = np.load(RAW / "e1_monitoring" / "main" / "signals.npz")
        sig = np.array_equal(Zr["x"], Zm["x"])
        tr = [A[s]["rtamt_discrete_ms"] / A[s]["language_ms"] for s in A]
        check("D", "RR-e1", "E1 re-run vs main: all non-timing metrics and the 10,000 signals", "identical (5 φ)",
              f"{len(A)} φ: {'identical' if not bad else bad}; signals equal: {sig}; re-run speedup "
              f"{min(tr):.2f}–{max(tr):.2f}×", not bad and sig and len(A) == 5, "results/raw/e1_monitoring/audit_rerun")
    if (RAW / "control" / "audit_rerun" / "records.jsonl").exists():
        A = {(x["spec"], x["variant"]): x for x in recs("control", "audit_rerun")}
        C = {(x["spec"], x["variant"]): x for x in recs("control", "main")}
        bad = [k for k in A if A[k]["iterations"] != C[k]["iterations"] or A[k]["n_tracks"] != C[k]["n_tracks"]]
        check("D", "RR-control", "control re-run (φ3, φ4 × LCW, LCP; 1000 reps each) vs main: per-replication "
              "iterations and Track calls", "identical", f"{len(A) - len(bad)}/{len(A)} identical", not bad and len(A) == 4,
              "results/raw/control/audit_rerun")
    if (RAW / "control_bo" / "audit_rerun" / "records.jsonl").exists():
        A = {(x["spec"], x["rep"]): x for x in recs("control_bo", "audit_rerun")}
        B = {(x["spec"], x["rep"]): x for x in recs("control_bo", "main")}
        bad = [k for k in A if (A[k]["success"], A[k]["iterations"], A[k]["best_rho"]) !=
               (B[k]["success"], B[k]["iterations"], B[k]["best_rho"])]
        check("D", "RR-control_bo", "E6 re-run (φ1, φ3 × reps 0–4) vs main", "identical",
              f"{len(A) - len(bad)}/{len(A)} identical", not bad and len(A) == 10, "results/raw/control_bo/audit_rerun")
    if (RAW / "findbox" / "audit_rerun" / "records.jsonl").exists():
        out = []
        for x in recs("findbox", "audit_rerun"):
            a = json.loads((RAW / "findbox" / "audit_rerun" / f"{x['variant']}_{x['spec']}.json").read_text())
            b = json.loads((RAW / "findbox" / "main" / f"{x['variant']}_{x['spec']}.json").read_text())
            out.append(a == b)
        check("D", "RR-findbox", "FindBox re-run (default φ2, φ4, φ5; best-effort φ2) vs main: box files", "identical",
              f"{sum(out)}/{len(out)} identical", all(out) and len(out) == 4, "results/raw/findbox/audit_rerun")


# ------------------------------------------------------------------ E. tables
def table_checks():
    import make_tables as mt
    jobs = [("table1_main.md", lambda: mt.table1("main")), ("table2_3_main.md", lambda: mt.tables23("main")),
            ("table2_3_pilot.md", lambda: mt.tables23("pilot")),
            ("table2_3_findbox_default.md", lambda: mt.tables23("findbox_default")),
            ("table2_3_findbox_besteffort.md", lambda: mt.tables23("findbox_besteffort")),
            ("table4_main.md", lambda: mt.table4("main", falsification_run="main")),
            ("table5_main.md", lambda: mt.table5("main")), ("table5_pilot.md", lambda: mt.table5("pilot")),
            ("e6_control_bo_main.md", lambda: mt.table6("main", "main"))]
    for name, fn in jobs:
        new = "\n".join(fn()) + "\n"
        old = (ROOT / "results" / "tables" / name).read_text(encoding="utf-8")
        d = [ln for ln in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
             if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        body = [ln for ln in d if not ln[1:].startswith(("- Run created", "- Language of ¬φ"))]
        check("E", f"T-{name}", f"results/tables/{name} regenerated from raw records",
              "identical (except header lines)", "identical" if not d else
              (f"only header lines differ ({len(d)})" if not body else f"{len(body)} body lines differ: {body[:2]}"),
              not body, "analysis/make_tables.py")


# ------------------------------------------------------------------ F. censoring
def censoring():
    L = ["## F. Success-conditional vs restricted means (censoring)", "",
         "The paper's S̄ and P̄ average over successful runs only; with its 100 % success rates this is harmless. Ours "
         "has unequal success rates, so conditional means can favour the method that fails more. The restricted mean "
         "counts every unsuccessful run at the cap (200 iterations for falsification; 205 Track calls for E6; "
         "(M+1)(K+1) = 5,511 Track calls for E5 LCW).", ""]
    R = recs("falsification", "main")
    L += ["| Comparison | ratio of conditional means, geomean (as reported) | ratio of restricted means, geomean |",
          "|---|---|---|"]
    out = {}
    for base, ours in (("PBO-RTAMT", "PROF"), ("SBO-RTAMT", "SMuRF")):
        cond = gmean(_fals_ratios(R, base, ours, "iterations"))
        rm = gmean([np.mean([x["iterations"] for x in _by(R, base, s)]) / np.mean([x["iterations"] for x in _by(R, ours, s)])
                    for s in REQS])
        per = [np.mean([x["iterations"] for x in _by(R, base, s)]) / np.mean([x["iterations"] for x in _by(R, ours, s)])
               for s in REQS]
        out[(base, ours)] = (cond, rm, per)
        L.append(f"| E2/E3 S̄ {base}/{ours} (>1 favours {ours}) | {cond:.2f} | {rm:.2f} (per φ: "
                 f"{', '.join(f'{v:.2f}' for v in per)}) |")
    B = recs("control_bo", "main")
    W = {x["spec"]: np.array(x["iterations"]) for x in recs("control", "main") if x["variant"] == "LCW"}
    rat_c, rat_r = [], []
    for i in range(1, 9):
        s = f"phi{i}"
        bo = np.array([x["iterations"] if x["success"] else 205 for x in B if x["spec"] == s])
        ok = [x["iterations"] for x in B if x["spec"] == s and x["success"]]
        w = W[s]
        wr = np.where((w > 0) & (w <= 205), w, 205)
        wc = w[(w > 0) & (w <= 205)]
        if ok and len(wc):
            rat_c.append(np.mean(ok) / wc.mean())
        rat_r.append(bo.mean() / wr.mean())
    L.append(f"| E6 BO/LCW iterations within 205 Track calls (<1 favours BO) | {gmean(rat_c):.2f} | {gmean(rat_r):.2f} "
             f"(per φ: {', '.join(f'{v:.2f}' for v in rat_r)}) |")
    C = {(x["spec"], x["variant"]): np.array(x["iterations"]) for x in recs("control", "main")}
    cap = 501 * 11
    w5, p5 = C[("phi5", "LCW")], C[("phi5", "LCP")]
    L.append(f"| E5 φ5 LCW/LCP P̄ (LCW fails 786/1000) | {w5[w5 > 0].mean() / p5[p5 > 0].mean():.1f} | "
             f"≥ {np.where(w5 > 0, w5, cap).mean() / np.where(p5 > 0, p5, cap).mean():.1f} (failures counted at 5,511) |")
    L += ["", "Reading: a restricted mean is a lower bound for the true mean of a method that fails within the cap.", ""]
    tot = {}
    for base, ours in (("PBO-RTAMT", "PROF"), ("SBO-RTAMT", "SMuRF")):
        tot[(base, ours)] = (gmean(_fals_ratios(R, base, ours, "T_T_ms")),
                             gmean(_fals_ratios(R, base, ours, "monitor_ms_total")))
    L += ["## G. T̄_T definition: critical path (D11, used) vs sum over all processes", "",
          "| Comparison | T̄_T ratio, critical path (reported) | ratio of total monitoring time over all processes |",
          "|---|---|---|"] + [f"| {b}/{o} | {a:.2f} | {c:.2f} |" for (b, o), (a, c) in tot.items()] + [
          "", "Sequential methods have one process, so both definitions coincide for SBO-RTAMT/SMuRF.", ""]
    return L, out, rat_r


def main():
    claims_e1(); claims_e23(); claims_e4(); claims_e5(); claims_e6(); claims_findbox(); claims_findbox_quality()
    claims_cc()
    data_checks(); config_checks(); rerun_checks(); table_checks()
    cens, _, _ = censoring()
    names = {"A": "Headline claims (README/PROGRESS) recomputed from raw outputs",
             "B": "Data integrity", "C": "Configuration provenance", "D": "Re-runs with the current code",
             "E": "Tables regenerated from raw records"}
    L = ["# Reproducibility audit — automated checks `[ours]`", "",
         "Generated by `analysis/audit.py` (independent recomputation; it does not reuse make_tables.py except in "
         "section E). PASS = recomputed value equals the quoted value at the quoted precision.", ""]
    for sec, title in names.items():
        rows = [c for c in CHECKS if c[0] == sec and not c[1].startswith("E5-c-")]
        L += [f"## {sec}. {title}", "", "| ID | Check | Quoted / expected | Recomputed | Result | Source |",
              "|---|---|---|---|---|---|"]
        for _, cid, what, claimed, value, ok, source in rows:
            L.append(f"| {cid} | {what} | {claimed} | {value} | {'PASS' if ok else '**FAIL**'} | `{source}` |")
        L.append("")
    L += cens
    n_fail = sum(1 for c in CHECKS if not c[5] and not c[1].startswith("E5-c-"))
    L.insert(4, f"**{len([c for c in CHECKS if not c[1].startswith('E5-c-')]) - n_fail} PASS, {n_fail} FAIL.**\n")
    out = ROOT / "results" / "tables" / "audit.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
