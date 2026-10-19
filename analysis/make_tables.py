"""Build the comparison tables (paper vs ours) from raw experiment records.

Every table carries a provenance header (run ids, number of trials/replications, whether the run is a
PILOT) and keeps three kinds of numbers apart:
  [paper]  values transcribed from the paper (analysis/target_paper/paper_reported_values.py),
  [ours]   values measured by our runs (results/raw/...),
  [derived] arithmetic on one of the two (ratios, geometric means), labelled as such.

Usage: python analysis/make_tables.py --e1 main --falsification main --table4 main --control main
       (any argument can be omitted; missing runs are skipped)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis" / "target_paper"))

from langfal.runlog import read_records  # noqa: E402
from langfal.stats import geometric_mean, mean_ci, paired_wilcoxon  # noqa: E402
import paper_reported_values as paper  # noqa: E402

RAW = ROOT / "results" / "raw"
OUT = ROOT / "results" / "tables"
REQS = ["phi1", "phi2", "phi3", "phi4", "phi5"]


def _meta(exp, run_id):
    p = RAW / exp / run_id / "meta.json"
    return json.loads(p.read_text()) if p.exists() else None


def _fmt(m, h=None, nd=2):
    if m is None or (isinstance(m, float) and math.isnan(m)):
        return "—"
    s = f"{m:.{nd}f}"
    if h is not None and not math.isnan(h):
        s += f" ± {h:.{nd}f}"
    return s


def _header(title, exp, run_id, expected_n=None, n=None, unit="trials", status=None):
    meta = _meta(exp, run_id)
    status = status or "FULL"
    if expected_n is not None and n is not None and n < expected_n:
        status = f"PILOT ({n} of {expected_n} {unit})"
    lines = [f"# {title}", "",
             f"- Status: **{status}**",
             f"- Source: `results/raw/{exp}/{run_id}/` (records.jsonl, meta.json)"]
    if meta:
        s = meta["sessions"][-1]
        env = s.get("environment", {})
        hashes = list(dict.fromkeys(x.get("source_sha256", "")[:12] for x in meta["sessions"]))
        lines.append(f"- Run created {meta.get('created')}; {len(meta['sessions'])} session(s), source sha256 "
                     f"{', '.join(f'`{h}`' for h in hashes)}; "
                     f"Python {env.get('python')}, numpy {env.get('numpy')}, scikit-learn {env.get('sklearn')}, "
                     f"RTAMT {env.get('rtamt')}; {env.get('cpu_count')} logical CPUs, {env.get('ram_gb')} GB RAM")
    lines += ["- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.",
              ""]
    return lines


# ------------------------------------------------------------------ Table 1
def table1(run_id):
    recs = {r["spec"]: r for r in read_records(RAW / "e1_monitoring" / run_id)}
    n = next(iter(recs.values()))["n"]
    L = _header("Table 1 — language monitor vs RTAMT (E1)", "e1_monitoring", run_id, 10000, n, "samples")
    T = paper.TABLE1
    rows = [
        ("Value agreement (%)", "value_agreement_pct", "value_agreement_pct", 2),
        ("Sign-only agreement (%)", "sign_only_agreement_pct", "sign_only_agreement_pct", 2),
        ("Complete disagreement (%)", "complete_disagreement_pct", "complete_disagreement_pct", 2),
        ("Mean RTAMT time (ms) — ours: discrete-time", "mean_rtamt_time_ms", "rtamt_discrete_ms", 4),
        ("Mean language monitor time (ms) — ours: all boxes", "mean_language_monitor_ms", "language_ms", 4),
        ("Satisfaction ratio (%) — ours: % violating (see note)", "satisfaction_ratio_pct", "violating_pct", 2),
        ("Number of boxes — ours: boxes of L(¬φ)", "number_of_boxes", "n_boxes_neg", 0),
    ]
    L += ["| Metric | " + " | ".join(f"{s} [paper] | {s} [ours]" for s in REQS) + " |",
          "|---|" + "---|---|" * len(REQS)]
    for label, pk, ok, nd in rows:
        cells = []
        for i, s in enumerate(REQS):
            pv = T[pk][i]
            ov = recs[s].get(ok) if s in recs else None
            cells += [f"{pv:.{nd}f}" if nd else f"{pv}", "—" if ov is None else (f"{ov:.{nd}f}" if nd else f"{int(ov)}")]
        L.append(f"| {label} | " + " | ".join(cells) + " |")
    L += ["", "Extra measurements (not in the paper) `[ours]`:", "",
          "| Metric | " + " | ".join(REQS) + " |", "|---|" + "---|" * len(REQS)]
    extras = [("% satisfying (ρ ≥ 0)", "satisfying_pct", 2), ("% with ρ exactly 0", "rho_zero_pct", 2),
              ("RTAMT dense-time (ms/call)", "rtamt_dense_ms", 4), ("one box (ms/call)", "one_box_ms", 4),
              ("RTAMT discrete on 1 s grid, 101 samples (ms/call)", "rtamt_discrete_1s_grid_ms", 4),
              ("RTAMT discrete on 0.1 s grid, 1001 samples (ms/call)", "rtamt_discrete_0.1s_grid_ms", 3),
              ("max |our robustness − RTAMT|", "ours_vs_rtamt_max_abs_diff", 2),
              ("exact language compilation, L(¬φ) (ms, once per formula)", "language_compile_ms", 2)]
    for label, k, nd in extras:
        L.append(f"| {label} | " + " | ".join(_fmt(recs[s].get(k), nd=nd) if s in recs else "—" for s in REQS) + " |")
    sp_p = [a / b for a, b in zip(T["mean_rtamt_time_ms"], T["mean_language_monitor_ms"])]
    sp_o = [recs[s]["rtamt_discrete_ms"] / recs[s]["language_ms"] for s in REQS]
    L += ["", "Per-call monitor speedup RTAMT / language monitor `[derived]`:", "",
          "| | " + " | ".join(REQS) + " | geomean |", "|---|" + "---|" * (len(REQS) + 1),
          "| from paper values | " + " | ".join(f"{v:.1f}" for v in sp_p) + f" | {geometric_mean(sp_p):.1f} |",
          "| from our values | " + " | ".join(f"{v:.1f}" for v in sp_o) + f" | {geometric_mean(sp_o):.1f} |",
          "", "Notes:",
          "1. Our language is exact (deviation L1), so the language monitor reproduces RTAMT's robustness value; the paper's "
          "42.6% value agreement for φ2/φ4 reflects FindBox's approximate language.",
          "2. The paper calls its row 'Satisfaction Ratios' and describes it as the share of trajectories inside the "
          "language and 'an indirect measure of the difficulty of falsification'; we report next to it the share of "
          "*violating* trajectories (inside L(¬φ)), which is our interpretation, and the satisfying share above.",
          "3. Absolute times depend on hardware (paper: not stated) and on the trace length RTAMT monitors (see the "
          "1 s / 0.1 s grid rows)."]
    return L


# ------------------------------------------------------------------ Tables 2/3
def _by(recs, method, spec):
    return sorted([r for r in recs if r["method"] == method and r["spec"] == spec], key=lambda r: r["trial"])


def tables23(run_id, expected_trials=20):
    recs = read_records(RAW / "falsification" / run_id)
    meta = _meta("falsification", run_id)
    cfg = (meta or {}).get("config", {})
    specs_cfg = cfg.get("specs", REQS)
    present = [s for s in specs_cfg if any(r["spec"] == s for r in recs)]
    missing = [s for s in specs_cfg if s not in present]
    counts = [len({r["trial"] for r in recs if r["spec"] == s and r["method"] == m})
              for s in present for m in cfg.get("methods", ["PROF", "PBO-RTAMT", "SMuRF", "SBO-RTAMT"])]
    lo, hi = (min(counts), max(counts)) if counts else (0, 0)
    status = None
    if lo < expected_trials:
        status = (f"PILOT ({lo} of {expected_trials} trials)" if lo == hi else
                  f"INCOMPLETE ({lo}–{hi} of {expected_trials} trials per requirement × method)")
    elif missing:
        status = f"FULL for {', '.join(present)}; not run: {', '.join(missing)}"
    L = _header("Tables 2 and 3 — falsification on Chasing Cars (E2/E3)", "falsification", run_id, status=status)
    lang = (meta or {}).get("config", {}).get("language", {"source": "exact"})
    L.insert(4, f"- Language of ¬φ: **{lang.get('source', 'exact')}**"
                + (f" (FindBox run `{lang.get('run')}`, variant `{lang.get('variant')}`)" if lang.get("source") == "findbox" else
                   " (compiled exactly, DEVIATIONS A1)"))
    na = [r for r in recs if str(r.get("stop_reason", "")).startswith("not-applicable")]
    if na:
        L.insert(5, f"- {len(na)} runs not applicable (empty language for: "
                    f"{', '.join(sorted({r['spec'] for r in na}))}); counted as not falsified.")
    if missing:
        note = RAW / "findbox" / str(lang.get("run")) / "INCOMPLETE.md"
        L.insert(5, f"- Not run: {', '.join(missing)} (no language of ¬φ available"
                    + (f"; see `results/raw/findbox/{lang.get('run')}/INCOMPLETE.md`" if note.exists() else "") + ").")
    L += ["Columns: FR = falsified trials / trials; S̄ = mean iterations over falsified trials (± 95% t-CI); "
          "T̄_T = mean total monitoring time per falsified trial in ms on the critical path (parallel methods: "
          "slowest process per round); T̄_M = mean time per monitoring call in ms (one box for PROF, all boxes for "
          "SMuRF, one RTAMT evaluation for the baselines). Extra columns are ours only.", ""]
    pairs = [("Table 2", paper.TABLE2, "PBO-RTAMT", "PROF"), ("Table 3", paper.TABLE3, "SBO-RTAMT", "SMuRF")]
    for name, ptab, base, ours in pairs:
        L += [f"## {name}: {base} vs {ours}", "",
              "| Req | Method | FR [paper] | FR [ours] | S̄ [paper] | S̄ [ours] | median S [ours] | T̄_T ms [paper] | "
              "T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | sims/trial [ours] | sim s/trial [ours] | "
              "GP s/trial [ours] | wall s/trial [ours] |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        ratios_tt, ratios_s, ratios_r, pvals = [], [], [], []
        for i, s in enumerate(REQS):
            stats = {}
            for meth in (base, ours):
                rs = _by(recs, meth, s)
                ok = [r for r in rs if r["falsified"]]
                S = mean_ci([r["iterations"] for r in ok])
                TT = mean_ci([r["T_T_ms"] for r in ok])
                TM = np.mean([r["T_M_ms"] for r in rs]) if rs else float("nan")
                stats[meth] = (rs, ok, S, TT)
                L.append(f"| {s} | {meth} | {ptab[meth]['FR'][i]}/20 | {len(ok)}/{len(rs)} | "
                         f"{ptab[meth]['S'][i]:.2f} | {_fmt(*S)} | "
                         f"{_fmt(float(np.median([r['iterations'] for r in ok])) if ok else None)} | "
                         f"{ptab[meth]['TT'][i]:.3f} | {_fmt(*TT, nd=3)} | {ptab[meth]['TM'][i]:.3f} | {_fmt(TM, nd=4)} | "
                         f"{_fmt(np.mean([r['n_sims'] for r in rs]) if rs else None, nd=0)} | "
                         f"{_fmt(np.mean([r['sim_ms'] for r in rs]) / 1e3 if rs else None)} | "
                         f"{_fmt(np.mean([r['gp_ms'] for r in rs]) / 1e3 if rs else None)} | "
                         f"{_fmt(np.mean([r['wall_s'] for r in rs]) if rs else None)} |")
            b, o = stats[base], stats[ours]
            ratios_tt.append(_ratio(b[3][0], o[3][0]))
            ratios_s.append(_ratio(b[2][0], o[2][0]))
            ratios_r.append(_ratio(_mean_all(b[0]), _mean_all(o[0])))
            paired = [(rb["iterations"], ro["iterations"]) for rb, ro in zip(b[0], o[0])
                      if rb["trial"] == ro["trial"] and rb["iterations"] is not None and ro["iterations"] is not None]
            pvals.append(paired_wilcoxon([p[0] for p in paired], [p[1] for p in paired]) if len(paired) >= 5 else float("nan"))
        pp_tt = [a / c for a, c in zip(ptab[base]["TT"], ptab[ours]["TT"])]
        pp_s = [a / c for a, c in zip(ptab[base]["S"], ptab[ours]["S"])]
        L += ["", f"Speedups {base} / {ours} `[derived]` (ratio of means; > 1 favours {ours}):", "",
              "| | " + " | ".join(REQS) + " | geomean |", "|---|" + "---|" * (len(REQS) + 1),
              "| T̄_T ratio, paper | " + " | ".join(f"{v:.1f}" for v in pp_tt) + f" | {geometric_mean(pp_tt):.1f} |",
              "| T̄_T ratio, ours | " + " | ".join(_fmt(v, nd=1) for v in ratios_tt) + f" | {_gm(ratios_tt, 1)} |",
              "| S̄ ratio, paper | " + " | ".join(f"{v:.2f}" for v in pp_s) + f" | {geometric_mean(pp_s):.2f} |",
              "| S̄ ratio, ours | " + " | ".join(_fmt(v) for v in ratios_s) + f" | {_gm(ratios_s, 2)} |",
              "| S̄ ratio, ours, failures counted at 200 | " + " | ".join(_fmt(v) for v in ratios_r)
              + f" | {_gm(ratios_r, 2)} |",
              "| paired Wilcoxon p (iterations), ours | " + " | ".join(_fmt(p, nd=3) for p in pvals) + " | |", ""]
    L += ["Notes on the ratio rows:",
          "- S̄ follows the paper: it averages falsified trials only. That is harmless at the paper's 20/20 success "
          "rates, but with unequal success rates it favours the method that fails more often.",
          "- 'Failures counted at 200' averages all trials, with unfalsified trials at the 200-iteration cap "
          "(a restricted mean, a lower bound for a method that fails).",
          "- Wilcoxon: two-sided signed-rank test on paired per-trial iteration counts, unfalsified trials at 200.", ""]
    if any(None in r for r in (ratios_tt, ratios_s, ratios_r)):
        L += ["'—' = no ratio (a method falsified no trial of that requirement); the geometric mean then covers only "
              "the requirements shown.", ""]
    if lang.get("source", "exact") != "exact":
        L += _rechecks(recs)
    return L


def _mean_all(rs):
    """Mean iterations over all applicable trials (unfalsified trials are stored at the cap); None if none."""
    v = [r["iterations"] for r in rs if r["iterations"] is not None]
    return float(np.mean(v)) if v else None


def _ratio(a, c):
    """a / c, or None when a mean is missing (no falsified trial) or not positive."""
    def ok(v):
        return v is not None and not math.isnan(v) and v > 0
    return a / c if ok(a) and ok(c) else None


def _gm(vals, nd):
    v = [x for x in vals if x is not None]
    g = _fmt(geometric_mean(v), nd=nd) if v else "—"
    return g if len(v) == len(vals) else f"{g} ({len(v)} of {len(vals)} req.)"


def _rechecks(recs):
    """D9 re-checks with an approximate (FindBox) language: language claims (Dist > 0) that RTAMT rejected."""
    L = ["## RTAMT re-checks of language claims (D9) `[ours]`", "",
         "A language method claims a falsifier when the signal lies in a box of the given L(¬φ) (Dist > 0); the claim "
         "is accepted only if RTAMT gives ρ < 0. A rejected claim is a satisfying signal that the approximate language "
         "puts in L(¬φ). Records written before the `validation_rejections` counter existed give the count exactly "
         "for SMuRF (re-checks − 1 per falsified trial) and as bounds for PROF (1 to j boxes can succeed in the final "
         "round).", "",
         "| Req | Method | trials | re-checks per trial (mean) | rejected claims, total | trials with a rejected claim |",
         "|---|---|---|---|---|---|"]
    for s in REQS:
        for meth in ("PROF", "SMuRF"):
            rs = [r for r in _by(recs, meth, s) if not str(r.get("stop_reason", "")).startswith("not-applicable")]
            if not rs:
                L.append(f"| {s} | {meth} | 0 | — | — | — |")
                continue
            lo = hi = 0
            n_lo = n_hi = 0
            for r in rs:
                v, f = r["validation_calls"], int(r["falsified"])
                if "validation_rejections" in r:
                    a = b = r["validation_rejections"]
                elif meth == "SMuRF" or not f:
                    a = b = v - f
                else:
                    a, b = max(v - r["n_boxes"], 0), v - 1
                lo, hi, n_lo, n_hi = lo + a, hi + b, n_lo + (a > 0), n_hi + (b > 0)
            rng = (lambda x, y: f"{x}" if x == y else f"{x}–{y}")
            L.append(f"| {s} | {meth} | {len(rs)} | {np.mean([r['validation_calls'] for r in rs]):.1f} | "
                     f"{rng(lo, hi)} | {rng(n_lo, n_hi)} |")
    return L + [""]


# ------------------------------------------------------------------ Table 4
def table4(run_id, expected_trials=20, falsification_run=None):
    recs = read_records(RAW / "table4" / run_id)
    n = len({r["trial"] for r in recs})
    L = _header("Table 4 — box difficulty (E4)", "table4", run_id, expected_trials, n)
    L += ["S̄_min / S̄_max: modified PROF (runs until every box of L(¬φ) is falsified or 200 rounds), averaged over "
          "**all** trials: S_min counts 200 when no box was falsified, S_max counts 200 when at least one box never was "
          "(so S̄_min differs from Table 2's PROF S̄, which averages falsified trials only). FR, S̄, T̄_T, T̄_M: "
          "sequential single-box BO (random box order, fresh BO per box, ≤ 200 iterations per box); S̄ and T̄_T over "
          "falsified trials.", "",
          "| Req | FR [paper] | FR [ours] | S̄_min [paper] | S̄_min [ours] | S̄_max [paper] | S̄_max [ours] | S̄ [paper] | "
          "S̄ [ours] | T̄_T ms [paper] | T̄_T ms [ours] | T̄_M ms [paper] | T̄_M ms [ours] | boxes never falsified (mean) [ours] |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    P = paper.TABLE4
    for i, s in enumerate(REQS):
        pa = _by(recs, "PROF-all", s)
        sq = _by(recs, "SEQ-BO", s)
        ok = [r for r in sq if r["falsified"]]
        L.append(f"| {s} | {P['FR'][i]}/20 | {len(ok)}/{len(sq)} | {P['S_min'][i]} | {_fmt(*mean_ci([r['S_min'] for r in pa]))} | "
                 f"{P['S_max'][i]} | {_fmt(*mean_ci([r['S_max'] for r in pa]))} | {P['S'][i]} | "
                 f"{_fmt(*mean_ci([r['iterations'] for r in ok]))} | {P['TT'][i]} | {_fmt(*mean_ci([r['T_T_ms'] for r in ok]), nd=3)} | "
                 f"{P['TM'][i]} | {_fmt(np.mean([r['T_M_ms'] for r in sq]) if sq else None, nd=4)} | "
                 f"{_fmt(np.mean([len(r['never_falsified_boxes']) for r in pa]) if pa else None)} |")
    if falsification_run and (RAW / "falsification" / falsification_run).exists():
        fr = read_records(RAW / "falsification" / falsification_run)
        prof = {(r["spec"], r["trial"]): r["iterations"] for r in fr if r["method"] == "PROF" and r["falsified"]}
        pairs = [(prof[(r["spec"], r["trial"])], r["S_min"]) for r in recs
                 if r["method"] == "PROF-all" and (r["spec"], r["trial"]) in prof]
        same = sum(a == b for a, b in pairs)
        L += ["", f"Consistency `[ours]`: S_min (modified PROF) equals PROF's iteration count in {same}/{len(pairs)} "
              f"matched (spec, trial) pairs of run `{falsification_run}` (same seeds; the paper's Table 4 S̄_min also "
              f"equals its Table 2 PROF S̄)."]
    return L


# ------------------------------------------------------------------ Table 5
def table5(run_id):
    recs = read_records(RAW / "control" / run_id)
    meta = _meta("control", run_id)
    reps = recs[0]["reps"] if recs else 0
    L = _header("Table 5 — LangControl on the UAV model (E5)", "control", run_id, 1000, reps, "replications")
    L += ["P̄ = mean number of iterations until a feasible signal over successful replications (one iteration = one "
          "Track call for LCW, one lock-step round of all processes for LCP). Our tracker, UAV parameters, sampling, "
          "projection and limits are our own choices (the paper gives none), so this is a re-implementation (L3), "
          "not a reproduction of the paper's numbers.", "",
          "| Formula | P̄ LCW [paper] | P̄ LCW [ours] | failures LCW [ours] | P̄ LCP [paper] | P̄ LCP [ours] | "
          "failures LCP [ours] | LCP processes [ours] | Track calls per replication LCW / LCP [ours] | "
          "boxes in L(φ) [ours] | M, K [ours] |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    by = {(r["spec"], r["variant"]): r for r in recs}
    more = 0
    for i in range(8):
        s = f"phi{i + 1}"
        w, p = by.get((s, "LCW")), by.get((s, "LCP"))
        tw = w["n_tracks"] / w["reps"] if w else None
        tp = p["n_tracks"] / p["reps"] if p else None
        more += bool(tw and tp and tp > tw)
        L.append(f"| {s} | {paper.TABLE5['LCW'][i]} | {_fmt(w['P_bar_success']) if w else '—'} | "
                 f"{f'{w['failures']}/{w['reps']}' if w else '—'} | {paper.TABLE5['LCP'][i]} | "
                 f"{_fmt(p['P_bar_success']) if p else '—'} | {f'{p['failures']}/{p['reps']}' if p else '—'} | "
                 f"{p['n_processes'] if p else '—'} | {_fmt(tw, nd=1)} / {_fmt(tp, nd=1)} | "
                 f"{(w or p or {}).get('n_boxes_language', '—')} | "
                 f"{(w or p or {}).get('M', '—')}, {(w or p or {}).get('K', '—')} |")
    L += ["", f"P̄ counts iterations (LCP: parallel rounds), as in the paper. In total tracking effort (all Track calls, "
          f"failed replications included), LCP uses more than LCW on {more} of 8 formulas: its advantage is wall-clock "
          "time given enough processors, not total computation."]
    return L


# ------------------------------------------------------------------ E6 (paper Sec. 4.3 text)
def table6(run_id, control_run):
    recs = read_records(RAW / "control_bo" / run_id)
    reps = len({r["rep"] for r in recs})
    meta = _meta("control_bo", run_id)
    budget = None
    if meta:
        b = meta["config"].get("bo", {})
        budget = int(b.get("n_init", 5)) + int(b.get("max_iter", 200))
    L = _header("E6 — robustness-BO control baseline vs LangControl (paper Sec. 4.3, no table in the paper)",
                "control_bo", run_id, status=f"complete at reduced scale ({reps} replications per objective, D24) — "
                "new evidence for a claim the paper states without data")
    L += [f"Paper claim (text only): 'Compared to LCW, we observe that BO consistently requires 3-7x the number of "
          f"iterations.' `[paper]`. BO: {reps} replications per objective, ≤ {budget} Track calls (initial samples "
          "included); LCW: E5 records (one iteration = one Track call). Because BO is capped, both methods are compared "
          f"within the same budget of {budget} Track calls.", "",
          f"| Formula | BO success ≤ {budget} [ours] | LCW success ≤ {budget} [ours] | BO mean iterations given success [ours] | "
          f"LCW mean iterations given success ≤ {budget} [ours] | ratio BO/LCW `[derived]` | LCW P̄ (all, E5) [ours] | "
          "BO median best ρ when failing [ours] |",
          "|---|---|---|---|---|---|---|---|"]
    lcw = {}
    if control_run and (RAW / "control" / control_run).exists():
        lcw = {r["spec"]: r for r in read_records(RAW / "control" / control_run) if r["variant"] == "LCW"}
    ratios, ratios_5 = [], []
    for i in range(8):
        s = f"phi{i + 1}"
        rs = [r for r in recs if r["spec"] == s]
        ok = [r["iterations"] for r in rs if r["success"]]
        fail_rho = [r["best_rho"] for r in rs if not r["success"]]
        w = lcw.get(s)
        n_within = 0
        if w:
            it = np.array(w["iterations"])
            within = it[(it > 0) & (it <= budget)]
            n_within = len(within)
            lcw_rate = f"{100 * len(within) / len(it):.1f} %"
            lcw_mean = float(within.mean()) if len(within) else float("nan")
            lcw_all = w["P_bar_success"]
        else:
            lcw_rate, lcw_mean, lcw_all = "—", float("nan"), None
        bo_mean = float(np.mean(ok)) if ok else float("nan")
        ratio = bo_mean / lcw_mean if ok and not math.isnan(lcw_mean) else float("nan")
        if not math.isnan(ratio):
            ratios.append(ratio)
            if len(ok) >= 5 and n_within >= 5:
                ratios_5.append(ratio)
        L.append(f"| {s} | {len(ok)}/{len(rs)} ({100 * len(ok) / max(1, len(rs)):.0f} %) | {lcw_rate} | {_fmt(bo_mean)} | "
                 f"{_fmt(lcw_mean)} | {_fmt(ratio)} | {_fmt(lcw_all)} | {_fmt(float(np.median(fail_rho)) if fail_rho else None)} |")
    L += ["", f"Geometric mean of the BO/LCW iteration ratio over formulas where both succeed `[derived]`: "
          f"{_fmt(geometric_mean(ratios))} ({len(ratios)} formulas); over formulas where both have ≥ 5 successes "
          f"within the budget: {_fmt(geometric_mean(ratios_5))} ({len(ratios_5)} formulas). Paper claim: 3–7 "
          "(BO needs 3–7× the iterations of LCW). Values < 1 mean BO needed fewer iterations."]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1")
    ap.add_argument("--falsification")
    ap.add_argument("--table4")
    ap.add_argument("--control")
    ap.add_argument("--control-bo")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [("table1", args.e1, lambda r: table1(r)),
            ("table2_3", args.falsification, lambda r: tables23(r)),
            ("table4", args.table4, lambda r: table4(r, falsification_run=args.falsification)),
            ("table5", args.control, lambda r: table5(r)),
            ("e6_control_bo", args.control_bo, lambda r: table6(r, args.control))]
    for name, run_id, fn in jobs:
        if not run_id:
            continue
        lines = fn(run_id)
        path = OUT / f"{name}_{run_id}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
