# Table 5 — LangControl on the UAV model (E5)

- Status: **FULL**
- Source: `results/raw/control/main/` (records.jsonl, meta.json)
- Run created 2026-10-18T18:05:54; 1 session(s), source sha256 `43806dbaefab`; Python 3.14.7, numpy 2.5.2, scikit-learn 1.9.1, RTAMT 0.3.5; 12 logical CPUs, 15.7 GB RAM
- `[paper]` = transcribed from Paper.pdf; `[ours]` = measured here; `[derived]` = arithmetic on one of them.

P̄ = mean number of iterations until a feasible signal over successful replications (one iteration = one Track call for LCW, one lock-step round of all processes for LCP). Our tracker, UAV parameters, sampling, projection and limits are our own choices (the paper gives none), so this is a re-implementation (L3), not a reproduction of the paper's numbers.

| Formula | P̄ LCW [paper] | P̄ LCW [ours] | failures LCW [ours] | P̄ LCP [paper] | P̄ LCP [ours] | failures LCP [ours] | LCP processes [ours] | Track calls per replication LCW / LCP [ours] | boxes in L(φ) [ours] | M, K [ours] |
|---|---|---|---|---|---|---|---|---|---|---|
| phi1 | 1.88423 | 56.60 | 0/1000 | 1 | 1.19 | 0/1000 | 64 | 56.6 / 76.0 | 2048 | 500, 10 |
| phi2 | 4.80769 | 59.29 | 0/1000 | 2.32152 | 5.06 | 0/1000 | 8 | 59.3 / 40.5 | 8 | 500, 10 |
| phi3 | 1.25672 | 10.63 | 0/1000 | 1 | 1.00 | 0/1000 | 64 | 10.6 / 64.0 | 110 | 500, 10 |
| phi4 | 135.036 | 30.73 | 0/1000 | 41.2362 | 1.23 | 0/1000 | 36 | 30.7 / 44.2 | 36 | 500, 10 |
| phi5 | 4.27235 | 2672.63 | 786/1000 | 2.37237 | 128.47 | 0/1000 | 64 | 4903.6 / 8221.8 | 1073741824 | 500, 10 |
| phi6 | 6.31527 | 580.87 | 0/1000 | 2.94731 | 571.23 | 0/1000 | 1 | 580.9 / 571.2 | 1 | 500, 10 |
| phi7 | 206.935 | 36.06 | 0/1000 | 89.7326 | 1.00 | 0/1000 | 64 | 36.1 / 64.0 | 870 | 500, 10 |
| phi8 | 1965 | 949.81 | 3/1000 | 488.345 | 13.66 | 0/1000 | 64 | 963.5 / 874.4 | 1000 | 500, 10 |

P̄ counts iterations (LCP: parallel rounds), as in the paper. In total tracking effort (all Track calls, failed replications included), LCP uses more than LCW on 5 of 8 formulas: its advantage is wall-clock time given enough processors, not total computation.
