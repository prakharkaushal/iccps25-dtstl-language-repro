# Table 1 — language monitor vs RTAMT (E1)

- Status: **FULL**
- Source: `results/raw/e1_monitoring/main/` (records.jsonl, meta.json)
- Run created 2026-10-18T15:55:40; 1 session(s), source sha256 `43806dbaefab`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

| Metric | phi1 [paper] | phi1 [ours] | phi2 [paper] | phi2 [ours] | phi3 [paper] | phi3 [ours] | phi4 [paper] | phi4 [ours] | phi5 [paper] | phi5 [ours] |
|---|---|---|---|---|---|---|---|---|---|---|
| Value agreement (%) | 100.00 | 100.00 | 42.60 | 100.00 | 100.00 | 100.00 | 42.61 | 100.00 | 100.00 | 100.00 |
| Sign-only agreement (%) | 0.00 | 0.00 | 57.40 | 0.00 | 0.00 | 0.00 | 57.38 | 0.00 | 0.00 | 0.00 |
| Complete disagreement (%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| Mean RTAMT time (ms) — ours: discrete-time | 0.8690 | 0.0875 | 0.6720 | 0.1687 | 1.3800 | 0.1927 | 1.3700 | 0.2045 | 1.0500 | 0.1670 |
| Mean language monitor time (ms) — ours: all boxes | 0.0364 | 0.0775 | 0.0151 | 0.1099 | 0.3510 | 0.0943 | 0.0133 | 0.1003 | 0.0368 | 0.0932 |
| Satisfaction ratio (%) — ours: % violating (see note) | 7.08 | 0.70 | 1.82 | 0.84 | 3.84 | 4.23 | 0.87 | 0.85 | 7.08 | 0.52 |
| Number of boxes — ours: boxes of L(¬φ) | 7 | 11 | 3 | 8 | 85 | 27 | 2 | 27 | 7 | 7 |

Extra measurements (not in the paper) `[ours]`:

| Metric | phi1 | phi2 | phi3 | phi4 | phi5 |
|---|---|---|---|---|---|
| % satisfying (ρ ≥ 0) | 99.30 | 99.16 | 95.77 | 99.15 | 99.48 |
| % with ρ exactly 0 | 0.00 | 2.65 | 0.00 | 0.00 | 2.65 |
| RTAMT dense-time (ms/call) | 0.1022 | 0.1786 | 0.2339 | 0.2476 | 0.1831 |
| one box (ms/call) | 0.0230 | 0.0309 | 0.0241 | 0.0253 | 0.0261 |
| RTAMT discrete on 1 s grid, 101 samples (ms/call) | 0.5329 | 0.8609 | 0.9476 | 1.0009 | 0.8587 |
| RTAMT discrete on 0.1 s grid, 1001 samples (ms/call) | 17.689 | 22.492 | 29.313 | 26.144 | 26.223 |
| max |our robustness − RTAMT| | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| exact language compilation, L(¬φ) (ms, once per formula) | 1.13 | 2.37 | 12.99 | 11.88 | 2.79 |

Per-call monitor speedup RTAMT / language monitor `[derived]`:

| | phi1 | phi2 | phi3 | phi4 | phi5 | geomean |
|---|---|---|---|---|---|---|
| from paper values | 23.9 | 44.5 | 3.9 | 103.0 | 28.5 | 26.2 |
| from our values | 1.1 | 1.5 | 2.0 | 2.0 | 1.8 | 1.7 |

Notes:
1. Our language is exact (deviation L1), so the language monitor reproduces RTAMT's robustness value; the paper's 42.6% value agreement for φ2/φ4 reflects FindBox's approximate language.
2. The paper calls its row 'Satisfaction Ratios' and describes it as the share of trajectories inside the language and 'an indirect measure of the difficulty of falsification'; we report next to it the share of *violating* trajectories (inside L(¬φ)), which is our interpretation, and the satisfying share above.
3. Absolute times depend on hardware (paper: not stated) and on the trace length RTAMT monitors (see the 1 s / 0.1 s grid rows).
